# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly import tools
import ctypes
import numpy as np
import pandas as pd
import re
import logging
import load_triton_log
from datetime import datetime
from pytz import timezone


#TODO Add Pause button for Log viewing -> Make Log viewer seperate
#TODO Optimize Colors
logger = logging.getLogger('tritonMonitor.app')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


colors = {
    'background': '#333333',
    'text': '#7FDBFF'
}
    
external_stylesheets = ['./static/bWLwgP.css']

layout = {
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],                
                'font': {
                    'color': colors['text']
                },
                'height': 800
            }

# Hack for correct timezone
LOCAL_TIMEZONE_DIFF = datetime.now()-datetime.utcnow()
print(LOCAL_TIMEZONE_DIFF)

#Setup for Triton Fridge
# Log = load_triton_log.TritonLogReader(r"//janeway/user ag bluhm/Common/GaAs/Otten/log 190522 110546.vcl")
Log = load_triton_log.TritonLogReader(r"\\OI-PC\\LogFiles\\60555 Bluhm\\log 190609 120150.vcl")
Log.logger = logger
df=Log.df # Still nessesary?

# Standart Temp and Preasure Sensors for a Triton System
lakeshore_sensors=[
                'PT1 Head', 
                'PT1 Plate', 
                'PT2 Head', 
                'PT2 Plate', 
                'Magnet', 
                'Still Plate',
                'Cold Plate', 
                'MC Plate',
                'MC Plate Cernox'
                ]
preasure_sensors=[
    'P1 Tank (Bar)',
    'P2 Condense (Bar)',
    'P3 Still (mBar)',
    'P4 Turbo Back (mBar)',
    'P5 ForepumpBack (Bar)',
    'Dewar (mBar)' #Does it make sense to include the dewar or move it to misc?
]

misc_sensors=[
           'Input Water Temp', 
            'Output Water Temp' ,
            'Oil Temp', 
            'Helium Temp', 
            'Motor Current', 
            'Low Pressure', 
            'Low Pressure Avg', 
            'Still heater (W)', 
            'chamber heater (W)', 
            'IVC sorb heater (W)', 
            'turbo current(A)', 
            'turbo power(W)', 
            'turbo speed(Hz)', 
            'turbo motor(C)', 
            'turbo bottom(C)'
            ]

# Create main plot for the dashboard view
def make_static_figure(df):
    temp_traces = [
        go.Scatter(
            x=df[f'{trace} t(s)'],
            y=df[f'{trace} T(K)'],
            legendgroup='temperature',
            name=f'{trace} T(K)'
            ) for trace in lakeshore_sensors
            ]

    preasure_traces = [
        go.Scatter(
            x=df['Time'],
            y=df[f'{trace}'],
            legendgroup='preasure',
            name=f'{trace}'
            ) for trace in preasure_sensors
            ]

    fig = tools.make_subplots(rows=2, 
                        cols=1, 
                        specs=[[{}], [{}]],
                        shared_xaxes=True, 
                        shared_yaxes=False,
                        vertical_spacing=0.07,
                        subplot_titles=('Temperature Sensors', 'Preasure Sensors'),
                        print_grid=False
                        )

    fig.add_traces(
                    temp_traces + preasure_traces,
                    [1]*len(temp_traces)+[2]*len(preasure_traces),
                    [1]*len(temp_traces)+[1]*len(preasure_traces)
                   )

    fig['layout'].update(**layout)

    return fig

# Create dash app, expose flask server (change localhost to expose server?)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.title='Fridge Monitor'

logger.debug('Creating Layout')

# Create Page Layout
dashboard = [html.Div(#Live Dashboard Part
        style={'columnCount': 4,
            'textAlign': 'left',
            'color': colors['text'],
            'padding': 20}, 
        children=[
            html.H4('Last Log Read'),
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
            )]

log_reader = [html.Label('MISC Channels', 
               style={'textAlign': 'center',
                      'color': colors['text']}, ),
            dcc.Interval(
            id='interval-component',
            interval=60*1000, # in milliseconds
            n_intervals=0
            ),
            dcc.Dropdown( #Log Reader Part
        options=[
            {'label': 'Input Water Temp', 'value': 'Input Water Temp'},
            {'label': 'Output Water Temp', 'value': 'Output Water Temp'},
            {'label': 'Oil Temp', 'value': 'Oil Temp'},
            {'label': 'Helium Temp', 'value': 'Helium Temp'},
            {'label': 'Motor Current', 'value': 'Motor Current'},
            {'label': 'Low Pressure', 'value': 'Low Pressure'},
            {'label': 'Low Pressure Avg', 'value': 'Low Pressure Avg'},
            {'label': 'Still heater (W)', 'value': 'Still heater (W)'},
            {'label': 'chamber heater (W)', 'value': 'chamber heater (W)'},
            {'label': 'IVC sorb heater (W)', 'value': 'IVC sorb heater (W)'},
            {'label': 'turbo current(A)', 'value': 'turbo current(A)'},
            {'label': 'turbo power(W)', 'value': 'turbo power(W)'},
            {'label': 'turbo speed(Hz)', 'value': 'turbo speed(Hz)'},
            {'label': 'turbo motor(C)', 'value': 'turbo motor(C)'},
            {'label': 'turbo bottom(C)', 'value': 'turbo bottom(C)'}
            ],
            value=['turbo power(W)'],
            multi=True,
            style={
                'background': colors['background'],  
                'color': colors['text']
                },
            id='misc_dropdown'
            ),
            dcc.Graph(id='misc_plot')]


page_fridge_1 = dashboard + log_reader


app.layout = html.Div( # Main Div
    style={'backgroundColor': colors['background']}, 
    children=[ 
    html.H1( #Header
        children='Triton 200', 
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding': 25
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
    fig = make_static_figure(Log.df)
    return fig

@app.callback(
    Output('update_time', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_time_disp(n_intervals):  
    logger.debug('Refreshing update time disp')
    return Log.last_refresh.strftime('%H:%M:%S     %d.%m.%Y')

@app.callback(
    Output('mc_temp_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_mc_temp_disp(n_intervals):  
    logger.debug('Refreshing update MC Temp disp')
    return f"{df['MC Plate T(K)'].iloc[-1]*1000:.4} mK"

@app.callback(
    Output('P2_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_P2_disp(n_intervals):  
    logger.debug('Refreshing P2 disp')
    return f"{df['P2 Condense (Bar)'].iloc[-1]*1000:.4} mbar"

@app.callback(
    Output('magnet_temp_disp', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_magnet_temp_disp(n_intervals):  
    logger.debug('Refreshing Magnet Temp disp')
    return f"{df['Magnet T(K)'].iloc[-1]:.4} K"

@app.callback(
    Output('misc_plot', 'figure'),
    [Input('misc_dropdown', 'value')])
def update_misc_figure(plot_traces):    
    traces = []
    for plot_trace in plot_traces:
        traces.append(go.Scatter(
            x=Log.df['Time'],
            y=Log.df[plot_trace],
            name=plot_trace
        ))
    return {
        'data': traces,
        'layout': layout        
    }

if __name__ == '__main__':
    logger.debug('Starting app')
    app.run_server(debug=True)