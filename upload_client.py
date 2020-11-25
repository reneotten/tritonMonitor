# -*- coding: utf-8 -*-

import logging
import load_triton_log
from time import sleep
import json
import socket
import argparse


# TODO Optimize Colors
# TODO Catch if sensor on top is disabled, switch between 2 MC Sensors?


parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='settings.json')
parser.add_argument('--port', type=int, default=8080)

args = parser.parse_args()

config_file = args.filename
port = args.port

logger = logging.getLogger('tritonMonitor.app')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

host = socket.gethostbyname(socket.gethostname())
logger.debug(host)

with open(config_file,'r') as file:
    logger.debug(f'Loading settings file {file}')
    settings=json.load(file)

Log = load_triton_log.TritonLogReader(settings['log_file'],
                                        sql=settings['SQL_DATABASE_URL'],
                                        dataframe_rows=settings['dataframe_rows'],
                                        sql_table_length=settings['SQL_Table_Length'])
Log.logger = logger
print("Press Ctrl-C to terminate while statement")
try:
    while True:
        logger.debug(f'Sleeping for 60s')
        sleep(60)
        logger.debug(f'Refreshing log file')
        Log.refresh()

except KeyboardInterrupt:
    print("Press Ctrl-C to terminate while statement")
    pass