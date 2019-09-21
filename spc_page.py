import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
import os
import json
from datetime import datetime as dt
from data_process import DataProcess
from app_func import *


app = dash.Dash(__name__)
server = app.server

# app page layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.H5('日期選擇', style={'display': 'inline-block'}),
            dcc.DatePickerSingle(
                id='date-picker-single',
                min_date_allowed=dt(2000, 1, 1),
                max_date_allowed=dt(2030, 12, 31),
                initial_visible_month=dt(2019, 8, 21),
                date=str(dt(2019, 8, 21, 23, 59, 59)),
                display_format='YYYY-MM-DD',
                style={'display': 'inline-block', 'margin-left': '20px'}
            ),
            dcc.Loading(
                id='loading-0',
                children=[html.Div(id='loading-output-0')],
                type='circle',
                style={'display': 'inline-block', 'margin-left': '20px', 'height': '30px'}
            )
        ], style={'display': 'inline-block', 'margin': ' 2px 20px'}),
        html.Div([
            html.P('管制時間段 :', style={'display': 'inline-block', 'margin': '0px 10px'}),
            html.P('2019-08-21', id='date-selected', style={'display': 'inline-block', 'margin-right': '20px'}),
            dcc.Input(id='cl_input1', placeholder='HH:MM:SS', style={'width': '100px'}),
            html.P('~', style={'display': 'inline-block', 'margin': '0px 10px'}),
            dcc.Input(id='cl_input2', placeholder='HH:MM:SS', style={'width': '100px'}),
            html.Button('重設管制線', id='cl_submit', className='button-primary', style={'margin': '0px 10px'})
        ], style={'display': 'inline-block', 'padding': '8px', 'float':'right',
                  'vertical-align': 'middle', 'backgroundColor': '#FFFACD'}
        )
    ], style={'margin-bottom': '20px'}),
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.P('壓力傳感器(for模內壓峰值變化)')
                ], style={'height': '30px', 'color': 'green'}), 
                dcc.Dropdown(
                    id='max-yaxis-column'
                ),
                dcc.Checklist(
                    id='cl_check',
                    options=[
                        {'label': '管制線', 'value': 'CL'}
                    ],
                    value=[],
                    labelStyle={'display': 'inline-block'}
                )
            ], style={'margin': '5px 20px'}),
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.Div([
                html.P('壓力傳感器(for模內壓曲線)')
            ], style={'height': '30px', 'color': 'blue'}), 
            dcc.Dropdown(
                id='sensor-yaxis-column',
                value=[],
                multi=True
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'float': 'right', 'margin-top': '5px'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(240, 240, 240)',
        'padding': '5px 5px',
    }),

    html.Div([
        dcc.Loading(id='loading-1', children=[html.Div(id='loading-output-1')]),
        dcc.Graph(
            id='main-indicator-scatter',
            clickData={'points': [{'customdata': 0}]}
        ),
    ], style={'width': '50%', 'display': 'inline-block', 'margin': '20px 5px', 'paddingLeft': '20px', 'float': 'left'}),
    
    html.Div([
        dcc.Loading(id='loading-2', children=[html.Div(id='loading-output-2')]),
        dcc.Graph(id='y-time-series'),
    ], style={'display': 'inline-block', 'width': '45%', 'float': 'right', 'margin': '20px 5px'}),

    # dcc.Interval(
    #     id='Interval-component',
    #     interval=60*1000, # in milliseconds, now update every 60 seconds
    #     n_intervals=60
    # ),

    html.Div(id='temp-value-a', style={'display': 'none'}),
    html.Div(id='temp-value-b', style={'display': 'none'}),
    html.Div(id='temp-value-c', style={'display': 'none'})
])



# callback functions
@app.callback(
    [Output('temp-value-a', 'children'),
     Output('temp-value-b', 'children'),
     Output('max-yaxis-column', 'options'),
     Output('max-yaxis-column', 'value'),
     Output('sensor-yaxis-column', 'options'),
     Output('sensor-yaxis-column', 'value'),
     Output('date-selected', 'children'),
     Output('loading-output-0', 'children')],
    [Input('date-picker-single', 'date')]
)
def update_fetch_data(date):
    # print(date)
    start_t = int('{}000000'.format(date.replace('-', '')[2:8]))
    end_t = int('{}235959'.format(date.replace('-', '')[2:8]))

    DP = DataProcess()
    dff = DP.processA(start_t, end_t)

    if len(dff) <= 0:
        options = []
        max_value = None
        sensor_value = []
    else:
        available_sensors = dff.columns.tolist()
        available_sensors.remove('Molding Time')
        
        options = [{'label': i, 'value': i} for i in available_sensors]

        max_value = available_sensors[0]
        sensor_value = available_sensors[:1]

    dff['Date'] = dff['Molding Time'].apply(lambda t: int(str(t)[:6]))

    cl_df = DP.get_max_cl()

    return dff.to_json(), cl_df.to_json(), options, max_value, options, sensor_value, date[:10], None


@app.callback(
    [Output('main-indicator-scatter', 'figure'),
     Output('loading-output-1', 'children')],
    [Input('max-yaxis-column', 'value'),
     Input('cl_check', 'value')],
    [State('temp-value-a', 'children'),
     State('temp-value-b', 'children')]
)
def update_main_graph(yaxis, cl_check, jsonified_data, cl_data):
    # print('update_main_graph!')
    if jsonified_data == None:
        # print('no data...')
        return create_scatter_figure([], None, None), None

    dff = pd.read_json(jsonified_data)
    if len(dff) == 0:
        return create_scatter_figure([], None, None), None

    x = dff['Molding Time'].apply(lambda t: datetime.strptime(str(t), '%y%m%d%H%M%S'))
    y = dff[yaxis]
    x_min, x_max = x.values[0], x.values[-1]

    datas = []
    datas.append(go.Scatter(
        x=x,
        y=y,
        customdata=dff['Molding Time'],
        mode='lines+markers',
        marker={'size': 8, 'opacity': 0.5},
        line={'width': 2}
    ))

    if 'CL' in cl_check:
        cl_df = pd.read_json(cl_data)
        cl = cl_df.loc[['ucl_3', 'lcl_3'], yaxis].values.round(3)
        ucl = create_cl(x, cl, 'ucl')
        lcl = create_cl(x, cl, 'lcl')
        datas += [ucl, lcl]

    return create_scatter_figure(datas, x_min, x_max), None


@app.callback(
    [Output('temp-value-c', 'children'),
     Output('loading-output-2', 'children')],
    [Input('main-indicator-scatter', 'clickData')]
)
def update_x_timeseries(click_data):
    t = click_data['points'][0]['customdata']
    if t == 0:
        return None, None
    else:
        DP = DataProcess()
        m_df = DP.processA(t, t, 'one mold')
        return m_df.to_json(), None
    
    # except:
    #     t = 0
    #     return None, None


@app.callback(
    Output('y-time-series', 'figure'),
    [Input('sensor-yaxis-column', 'value'),
     Input('temp-value-c', 'children')],
    [State('main-indicator-scatter', 'clickData'),]
)
def sensor_select_update(sensors, mold_data, click_data):
    # print('update timeseries!')
    if mold_data == None:
        # print('no data...')
        return create_time_series([], 'Linear', '')

    m_df = pd.read_json(mold_data)
    datas = []
    for sensor in sensors:
        scatter = go.Scatter(
            x=m_df['Elapsed Time'],
            y=m_df[sensor],
            mode='lines+markers',
            marker={'size': 4},
            line={'width': 2},
            name=sensor.strip()
        )
        datas.append(scatter)

    t = click_data['points'][0]['customdata']
    t_str = ' Time: ' + get_Time(t)
    
    return create_time_series(datas, 'Linear', t_str)


@app.callback(
    Output('date-picker-single', 'date'),
    [Input('cl_submit', 'n_clicks')],
    [State('date-selected', 'children'),
     State('cl_input1', 'value'),
     State('cl_input2', 'value')]
)
def update_cl(cl_clicks, date, t_start, t_end):
    if t_start != None and t_end != None:
        DP = DataProcess()
        start_t = int((date + t_start).replace('-', '').replace(':', '')[2:])
        end_t = int((date + t_end).replace('-', '').replace(':', '')[2:])
        DP.update_cl(start_t, end_t)

    return date + ' 23:59:59'



if __name__ == '__main__':
    app.run_server(debug=True)
