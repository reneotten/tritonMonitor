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

# Log = load_triton_log.TritonLogReader(r"//janeway/user ag bluhm/Common/GaAs/Otten/log 190522 110546.vcl")

Log = load_triton_log.TritonLogReader(r"\\OI-PC\\LogFiles\\60555 Bluhm\\log 190609 120150.vcl")
Log.logger = logger
df=Log.df
# Hack for correct timezone
LOCAL_TIMEZONE_DIFF = datetime.now()-datetime.utcnow()
print(LOCAL_TIMEZONE_DIFF)

layout = {
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],                
                'font': {
                    'color': colors['text']
                },
                'height': 800
            }

lakeshore_sensors=['PT1 Head', 
                'PT1 Plate', 
                'PT2 Head', 
                'PT2 Plate', 
                'Magnet', 
                'Still Plate',
                'Cold Plate', 
                'MC Plate',
                'MC Plate Cernox']
def make_static_figure(df):
    temp_traces = [go.Scatter(
                            x=df['PT1 Head t(s)'],
                            y=df['PT1 Head T(K)'],
                            legendgroup='group',
                            name='PT1 Head (mBar)'),
                    go.Scatter(
                            x=df['PT1 Plate t(s)'],
                            y=df['PT1 Plate T(K)'],
                            legendgroup='group',
                            name='PT1 Plate (mBar)'),
                    go.Scatter(
                            x=df['PT2 Head t(s)'],
                            y=df['PT2 Head T(K)'],
                            legendgroup='group',
                            name='PT2 Head T(K)'),
                    go.Scatter(
                            x=df['PT2 Plate t(s)'],
                            y=df['PT2 Plate T(K)'],
                            legendgroup='group',
                            name='PT2 Plate T(K)'),
                    go.Scatter(
                            x=df['Magnet t(s)'],
                            y=df['Magnet T(K)'],
                             legendgroup='group',
                            name='Magnet T(K)'),
                    go.Scatter(
                            x=df['Still Plate t(s)'],
                            y=df['Still Plate T(K)'],
                            legendgroup='group',
                            name='Still Plate T(K)'),
                    go.Scatter(
                            x=df['Cold Plate t(s)'],
                            y=df['Cold Plate T(K)'],
                            legendgroup='group',
                            name='Cold Plate T(K)'),
                    go.Scatter(
                            x=df['MC Plate t(s)'],
                            y=df['MC Plate T(K)'],
                            legendgroup='group',
                            name='MC Plate T(K)'),
                    go.Scatter(
                            x=df['MC Plate Cernox t(s)'],
                            y=df['MC Plate Cernox T(K)'],
                            legendgroup='group',
                            name='MC Plate Cernox T(K)')
                    ]
    
    preasure_traces = [go.Scatter(
                            x=df['Time'],
                            y=df['P1 Tank (Bar)'],
                            legendgroup='group2',
                            name='P1 Tank (Bar)'),
                    go.Scatter(
                            x=df['Time'],
                            y=df['P2 Condense (Bar)'],
                            legendgroup='group2',
                            name='P2 Condense (Bar)'),
                    go.Scatter(
                            x=df['Time'],
                            y=df['P3 Still (mBar)'],
                            legendgroup='group2',
                            name='P3 Still (mBar)'),
                    go.Scatter(
                            x=df['Time'],
                            y=df['P4 TurboBack (mBar)'],
                            legendgroup='group2',
                            name='P4 TurboBack (mBar)'),
                    go.Scatter(
                            x=df['Time'],
                            y=df['P5 ForepumpBack (Bar)'],
                            legendgroup='group2',
                            name='P5 ForepumpBack (Bar)'),
                    go.Scatter(
                            x=df['Time'],
                            y=df['Dewar (mBar)'],
                            legendgroup='group2',
                            name='Dewar (mBar)')
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

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.title='Fridge Monitor'

logger.debug('Creating Layout')

page_fridge_1 = [html.Div(#Live Dashboard Part
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
            # TODO Add option for log scale
            dcc.Graph(id='static_plot'),
            html.Label('MISC Channels', 
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
            dcc.Graph(id='misc_plot')
            ]
    
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1( #Header
        children='Triton 200', 
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding': 25
        }
    )]
    +   page_fridge_1
    )
    
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