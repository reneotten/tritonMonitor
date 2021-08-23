# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly import subplots
import logging
import load_triton_log
from datetime import datetime, timedelta
import json
import socket
import argparse


# TODO Optimize Colors
# TODO Catch if sensor on top is disabled, switch between 2 MC Sensors?


parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='settings.json')
parser.add_argument('--port', type=int, default=8080)

args, unknown = parser.parse_known_args()

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
    logger.debug(f'Loading log file {file}')
    settings=json.load(file)

if settings['local_mode']:
    Log = load_triton_log.TritonLogReader(settings['log_file'],
                                        dataframe_rows=settings['dataframe_rows'],
                                        sql_table_length=settings['SQL_Table_Length'])
else:
    Log = load_triton_log.TritonLogReader(sql=settings['SQL_DATABASE_URL'],
                                        dataframe_rows=settings['dataframe_rows'],
                                        sql_table_length=settings['SQL_Table_Length'])

Log.logger = logger

# Create main plot for the dashboard view
def m_str(val, unit='K'):
    if val < 1:
        unit = 'm' + unit
        val *= 1e3
    return f"{val:.1f} {unit}"

def make_static_traces(df, duration=None):
    
    if duration is not None:
        start_time = df['Time'].iloc[-1] - timedelta(days=duration)
    else:
        start_time = df['Time'].iloc[0]
   
    temp_traces = [
        go.Scatter(
            x=df.loc[df[f'{trace} t(s)']>=start_time,f'{trace} t(s)'],
            y=df.loc[df[f'{trace} t(s)']>=start_time,f'{trace} T(K)'],
            legendgroup='temperature',
            name=f'{trace} T(K)',
            ) for trace in settings['lakeshore_sensors']
            ]

    pressure_traces = [
        go.Scatter(
            x=df.loc[df['Time']>=start_time,'Time'],
            y=df.loc[df['Time']>=start_time,f'{trace}'],
            legendgroup='pressure',
            name=f'{trace}',
            ) for trace in settings['pressure_sensors']
            ]
    
    return  temp_traces + pressure_traces, [1]*len(temp_traces) + [2]*len(pressure_traces)
    
def make_static_figure(df, duration=None, lightweight_mode=True):
  
    traces, subplot = make_static_traces(df, duration=duration)

    fig = subplots.make_subplots(
                        rows=2, 
                        cols=1, 
                        specs=[[{}], [{}]],
                        shared_xaxes=True,                        
                        vertical_spacing=0.07,
                        subplot_titles=('Temperature Sensors', 'Pressure Sensors'),
                        print_grid=False
                        )
    
    fig.add_traces(traces, rows=subplot, cols=[1]*len(traces))
    

    fig['layout'].update(**settings['layout'])
    val_RuOx = Log.df[settings['MC_RuOx']].iloc[-1]
    val_Cernox = Log.df[settings['MC_Cernox']].iloc[-1]

    if val_RuOx<3 or val_Cernox<3:
        scale = "log"
    else:
        scale = "linear"

    fig.update_layout(yaxis_type=scale)

    for row in range(1,3):
        fig.update_xaxes(gridcolor=settings['gridcolor'], zerolinecolor=settings['zerolinecolor'], row=row, col=1)
        fig.update_yaxes(gridcolor=settings['gridcolor'], zerolinecolor=settings['zerolinecolor'], row=row, col=1)
        

    return fig


# Create dash app, expose flask server (change localhost to expose server?)
app = dash.Dash(__name__, external_stylesheets=settings['external_stylesheets'],show_undo_redo=False)
server = app.server

app.title = settings['fridge_name'] + ' Fridge Monitor'

logger.debug('Creating Layout')

# Create Page Layout
dashboard = [html.Div(  # Live Dashboard Part
        style={
                'columnCount': 4,
                'textAlign': 'left',
                'color': settings['colors']['text'],
                'padding': 20
                },
        children=[
            html.H4('Last Log Read', id='log header'),
            html.H2('Last Log Read', id='update_time'),
            html.H4('MC Temperature'),
            html.H2('MC Temp', id='mc_temp_disp'),
            html.H4('P2 Condenser'),
            html.H2('P2', id='P2_disp'),
            html.H4('Magnet Temperature'),
            html.H2('Magnet Temp', id='magnet_temp_disp')
                ]
            ),
            dcc.Interval(
            id='interval-component',
            interval=60*1000, # in milliseconds
            n_intervals=0
            ),
            dcc.Graph(id='static_plot')]



page_fridge_1 = dashboard 


app.layout = html.Div( # Main Div
    style={'backgroundColor': settings['colors']['background']}, 
    children=[ 
    html.H1( #Header
        children=settings['fridge_name'], 
        style={
            'textAlign': 'center',
            'color': settings['colors']['text'],
            'padding': 15
        }
    ) 
    ]
    +   page_fridge_1 # Page Content
    )
    
# create callbacks
logger.debug('Creating callbacks')
@app.callback(
    Output('static_plot', 'figure'),
    [Input('interval-component', 'n_intervals')])
def update_static_figure(n_intervals):
    logger.debug(f"{datetime.now().strftime('%H:%M:%S - %d.%m.%Y')}:Refreshing log")
    Log.refresh()

    with open(config_file,'r') as file:
        settings=json.load(file)

    fig = make_static_figure(Log.df,duration=settings['duration'])
    fig.layout.uirevision = True
    return fig

@app.callback(
    Output('update_time', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_time_disp(n_intervals):  
    logger.debug('Refreshing update time disp')
   # return Log.last_refresh.strftime('%H:%M:%S     %d.%m.%Y')
    return Log.df['Time'].iloc[-1]

@app.callback(
    Output('update_time','style'),
    [Input('update_time', 'children')])
def color_text(n_intervals):
    if datetime.now()-Log.df['Time'].iloc[-1]>timedelta(minutes=settings['error_time_mins']):
        ret_style = {'color':'red'}
    else: 
        ret_style = {'color':'red'} 
    return ret_style

@app.callback(
    Output('mc_temp_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_mc_temp_disp(n_intervals):  
    logger.debug('Refreshing update MC Temp disp')
    val_RuOx = Log.df[settings['MC_RuOx']].iloc[-1]
    val_Cernox = Log.df[settings['MC_Cernox']].iloc[-1]

    if val_Cernox is None:
        val_ret = val_RuOx
    elif val_RuOx >= 70:
        val_ret = val_Cernox
    else:
        val_ret = val_RuOx

    return m_str(val_ret)

@app.callback(
    Output('P2_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_P2_disp(n_intervals):  
    logger.debug('Refreshing P2 disp')
    return m_str(Log.df['P2 Condense (Bar)'].iloc[-1], unit='bar') 

@app.callback(
    Output('magnet_temp_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_magnet_temp_disp(n_intervals):  
    logger.debug('Refreshing Magnet Temp disp')
    return m_str(Log.df[settings['Magnet']].iloc[-1])


if __name__ == '__main__':
    logger.debug('Starting app')
    app.run_server(debug=True)
