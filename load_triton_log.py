# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 14:32:40 2019

@author: otten
"""
#TODO stitch logs (For reader)
import ctypes
import numpy as np
import re
import pandas as pd
import logging
from datetime import datetime
import csv
from io import StringIO
from sqlalchemy import create_engine
import glob
import os

logger = logging.getLogger('tritonMonitor.load_triton_log')
logger.setLevel(logging.DEBUG)

LOCAL_TIMEZONE_DIFF = datetime.now()-datetime.utcnow()

def parse_cstr(cstr: bytes) -> str:
    return ctypes.create_string_buffer(cstr).value.decode()

def split_at_idx(buf, idx):
    return buf[:idx], buf[idx:]

def parse_triton_log(bin_data) -> pd.DataFrame:
    header_size = 1024
    comments_size = 5120
    name_block_size = 5120
    name_len = 32
    unknown_block_size = 1024

    header = parse_cstr(bin_data[:header_size])
    rest = bin_data[header_size:]

    comments = parse_cstr(rest[:comments_size])
    rest = rest[comments_size:]

    name_block = rest[:name_block_size]
    rest = rest[name_block_size:]

    names = []
    for idx in range(0, name_block_size, name_len):
        name = parse_cstr(name_block[idx:idx+name_len])
        if name:
            names.append(name)
        else:
            break

    unknown_block, rest = split_at_idx(rest, unknown_block_size)

    data = np.frombuffer(rest, dtype=float)
    data = data.reshape((-1, len(names)))
    df = pd.DataFrame(columns=names, data=data)
    return df

def cat_columns(columns):
    drop_columns=[]
    time_columns=[]
    # temperature_sensors=[]
    for column in columns:
        # print(column)
        if re.match('^chan\[\d+\]',column):
            # print('Match: Empty channel')
            drop_columns.append(column)

        elif re.match('.+t\(s\)$',column):
            # print('Match: Temperature Sensor time channel')
            # group_name = re.split(' t\(s\)',column)[0]
            # temperature_sensors.append(group_name)
            time_columns.append(column)
    return drop_columns, time_columns

def cleanup_log(df, drop_columns, time_columns):
    dt = pd.to_datetime(df['Time(secs)'], unit='s')+LOCAL_TIMEZONE_DIFF
    df.insert(0, 'Time', dt)

    for column in time_columns:
        df[column] = pd.to_datetime(df[column], unit='s')+LOCAL_TIMEZONE_DIFF
        val_columns = [re.split('t\(s\)$',column)[0] + 'T(K)', re.split('t\(s\)$',column)[0] + 'R(Ohm)']
        df.loc[df[column]<='1971-01-01 00:00:00',val_columns]=None
        df.loc[df[column]<='1971-01-01 00:00:00',column]=df.loc[0,'Time']

    df = df.drop(columns=drop_columns)
    df = df.drop(columns=['LineSize(bytes)', 'LineNumber', 'Time(secs)'])
    return df

def psql_insert_copy(table, conn, keys, data_iter):
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)

class TritonLogReader:
    def __init__(self, fullpath=None, sql=None, dataframe_rows=None, sql_table_length=None):
        # If both are set, load local file and mirror to sql, if not, load from sql
        self.logger = logging.getLogger('tritonMonitor.load_triton_log.TritonLogReader')
        self.logger.setLevel(logging.DEBUG)
        self.fullpath = fullpath
        self.sql = sql
        self.sql_table_length = sql_table_length
        self.dataframe_rows = dataframe_rows
        self.logger.debug(f'Opening Log File {self.fullpath}')
        self.LOCAL_TIMEZONE_DIFF = LOCAL_TIMEZONE_DIFF
        self.last_refresh = datetime.now()

        if self.sql =='DATABASE_URL':
            DATABASE_URL = os.environ['DATABASE_URL']
            print(DATABASE_URL)
            self.logger.debug(f'Database URL is {DATABASE_URL}')
        elif self.fullpath:
            if not os.path.isfile(self.fullpath):
                self.fullpath = max(glob.glob(os.path.join(self.fullpath,'*.vcl')), key=os.path.getctime)

        if self.fullpath:
            with open(self.fullpath, 'rb') as file:
                self.logger.debug(f'Opening Log file {file}')
                self.df = parse_triton_log(file.read())
                self.current_fpos = file.tell()
                self.last_refresh = datetime.now()
                self.logger.debug(f'Dataframe with {len(self.df.index)} rows created')

            self.names = self.df.columns
            self.drop_columns, self.time_columns = cat_columns(self.df.columns)

            self.logger.debug('Cleaning up Log file')
            self.df = cleanup_log(self.df, self.drop_columns, self.time_columns)

            if self.dataframe_rows:
                 self.df =  self.df.iloc[-self.dataframe_rows:]

            if self.sql:
                self.mode = 'upstream'
                self.engine = create_engine(self.sql)
                self.df.iloc[-self.sql_table_length:].to_sql('triton200', self.engine, method=psql_insert_copy, if_exists='replace')
            else:
                self.mode = 'local'

        else:
                self.mode = 'downstream'
                self.engine = create_engine(self.sql)
                self.df = pd.read_sql_query('select * from "triton200"',con=self.engine)
                self.names = self.df.columns
                self.drop_columns, self.time_columns = cat_columns(self.df.columns)


    def refresh(self):
        self.last_refresh = datetime.now()
        if self.mode == 'upstream' or self.mode == 'local':
            self.logger.debug(f'Refresh: Opening Log File {self.fullpath}')
            with open(self.fullpath, 'rb') as file:
                file.seek(self.current_fpos)
                bin_data = file.read()
                self.current_fpos = file.tell()
            data = np.frombuffer(bin_data, dtype=float)
            data = data.reshape((-1, len(self.names)))

        #TODO if no ew lines skip append
            self.logger.debug(f'Found {data.shape[0]} new lines')
            if len(data):
                self.logger.debug(f'Creating Dataframe')
                updated_df = pd.DataFrame(columns=self.names, data=data)
                self.logger.debug('Refresh: Cleaning up Log file')
                updated_df = cleanup_log(updated_df, self.drop_columns, self.time_columns)
                self.df = self.df.append(updated_df)

                if self.mode == 'upstream':
                    self.df.iloc[-1000:].to_sql('triton200', self.engine, method=psql_insert_copy, if_exists='replace')
                    self.logger.debug(f'Updated SQL Table')

                return updated_df.shape[0]
            else:
                return 0

        else: #downstream
            self.logger.debug(f'Updated DF fromSQL')
            self.df = pd.read_sql_query('select * from "triton200"',con=self.engine)
            return 0

