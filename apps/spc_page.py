import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import os
import json
from datetime import datetime as dt
from datetime import timedelta
from .app_func import realtime_figure, create_scatter_figure, create_cl, create_time_series, update_models
from .db_connectors import RawDBConnector as rawDB
from .db_connectors import PreprocessedDBConnector as preDB
from .model_operations import SPCModel
from app import app


range_options = [10, 20, 30]


# app page layout
layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.P(
                    '實時模內壓峰值監控',
                    style={'fontSize': '18px', 'fontWeight': '800', 'display': 'inline-block', 'margin': '0px 20px'}
                ),
                dcc.Dropdown(
                    id='spc-realtime-sensor',
                    value='sensor1',
                    style={'display': 'inline-block', 'width': '120px', 'verticalAlign': 'middle', 'marginRight': '15px'}
                ),
                html.P(
                    '監控長度(分鐘):',
                    style={'fontSize': '15px', 'display': 'inline-block', 'marginRight': '5px'}
                ),
                dcc.Dropdown(
                    id='spc-realtime-range',
                    value=20,
                    options = [{'label': i, 'value': i} for i in range_options],
                    style={'display': 'inline-block', 'width': '50px', 'verticalAlign': 'middle'}
                )
            ]),
            dcc.Graph(
                id='spc-realtime-graph',
                clickData={'points': [{'customdata': 0}]},
                style={'height': '400px'}
            ),
        ], style={'display': 'inline-block', 'width': '50%', 'borderRight': '2px solid #CCE5FF'}),
        html.Div([
            html.Div([
                html.P(
                    '單模模內壓曲線',
                    style={'fontSize': '18px', 'fontWeight': '800', 'display': 'inline-block', 'margin': '0px 20px'}
                ),
                dcc.Dropdown(
                    id='spc-onemold-sensor',
                    value=[],
                    multi=True,
                    style={'display': 'inline-block', 'width': '420px', 'verticalAlign': 'middle'}
                ),
                dcc.Loading(
                    id='spc-loading-2',
                    children=[html.Div(id='spc-loading-output-2')],
                    style={'display': 'inline-block', 'marginLeft': '20px'}
                )
            ]),
            dcc.Graph(id='spc-onemold-graph')
        ], style={'display': 'inline-block', 'width': '48%', 'float': 'right'})
    ], style={'margin': '5px 5px'}),

    html.Div([
        html.Div([
            html.P(
                '模內壓峰值變化',
                style={'fontSize': '18px', 'fontWeight': '800', 'display': 'inline-block', 'marginLeft': '20px'}
            ),
            html.P(
                '2019-01-01',
                id='spc-date-selected',
                style={'display': 'inline-block', 'margin': '0px 20px'}
            ),
            dcc.Dropdown(
                id='spc-max-sensor',
                style={'display': 'inline-block', 'width': '150px', 'verticalAlign': 'middle'}
            ),
            dcc.Checklist(
                id='spc-checklist',
                options=[
                    {'label': '管制線(1.5)', 'value': 'cl_1.5'},
                    {'label': '管制線(3)', 'value': 'cl_3'},
                    {'label': '管制線(4.5)', 'value': 'cl_4.5'}
                ],
                value=[],
                labelStyle={'display': 'inline-block', 'marginLeft': '20px'},
                style={'display': 'inline-block', 'margin': '0px 20px'}
            ),
            dcc.Loading(
                id='spc-loading-1',
                children=[html.Div(id='spc-loading-output-1')],
                style={'display': 'inline-block'}
            )
        ]),
        dcc.Graph(
            id='spc-max-graph',
            clickData={'points': [{'customdata': 0}]}
        ),
    ], style={'padding': '5px 5px', 'borderTop': '2px solid #CCE5FF'}),

    dcc.Interval(
        id='interval-component',
        interval=5*1000, # in milliseconds, now update every 5 seconds
        n_intervals=0
    ),

    html.Div(id='spc-temp-value-a', style={'display': 'none'}),
    html.Div(id='spc-temp-value-b', style={'display': 'none'}),
    html.Div(id='spc-temp-value-c', style={'display': 'none'}),

    dcc.ConfirmDialog(
        id='retrain-confirm',
        message='確定變更工況嗎?'
    )
])



# callback functions
@app.callback(
    Output('spc-realtime-graph', 'figure'),
    [Input('interval-component', 'n_intervals')],
    [State('spc-realtime-range', 'value'),
     State('spc-realtime-sensor', 'value'),
     State('spc-machine-id', 'value'),
     State('spc-temp-value-b', 'children')]
)
def spc_realtime_graph(n, range_min, main_sensor, machine_id, cl_data):
    end_time = dt.now()
    # end_time = dt.now() - timedelta(days=27)
    start_time = end_time - timedelta(minutes=range_min)

    DB = preDB()
    df = DB.get_data('max' + machine_id, start_time, end_time)

    if len(df) <= 0:
        return {}
    else:
        cols = df.columns.tolist()
        sensors = cols[1:]
        t = df['Molding Time']
        x_min, x_max = t.values[0], t.values[-1]

        datas = []
        for sensor in sensors:
            x = t
            y = df[sensor]
            if sensor == main_sensor:
                datas.append(go.Scatter(
                    x=x,
                    y=y,
                    customdata=df['Molding Time'],
                    mode='lines+markers',
                    marker={'size': 8, 'opacity': 0.8},
                    line={'width': 1.5},
                    name=sensor
                ))
            else:
                datas.append(go.Scatter(
                    x=x,
                    y=y,
                    customdata=df['Molding Time'],
                    mode='lines+markers',
                    marker={'size': 3, 'opacity': 0.2},
                    line={'width': 0.5},
                    name=sensor
                ))

        return realtime_figure(datas, x_min, x_max, cl_data, main_sensor)


@app.callback(
    Output('retrain-confirm', 'message'),
    [Input('spc-realtime-range', 'value')]
)
def change_realtime_range(range_min):
    retrain_message = '確定變更工況嗎?\n系統將會收集前{}分鐘的數據進行模型更新。'\
                      .format(range_min)
    return retrain_message


@app.callback(
    [Output('spc-temp-value-a', 'children'),
     Output('spc-temp-value-b', 'children'),
     Output('spc-max-sensor', 'options'),
     Output('spc-max-sensor', 'value'),
     Output('spc-onemold-sensor', 'options'),
     Output('spc-onemold-sensor', 'value'),
     Output('spc-realtime-sensor', 'options'),
     Output('spc-realtime-sensor', 'value'),
     Output('spc-date-selected', 'children'),
     Output('spc-loading-output-0', 'children')],
    [Input('spc-date-picker-single', 'date'),
     Input('spc-machine-id', 'value')]
)
def fetch_data(date_time, machine_id):
    date = date_time.split(' ')[0]
    start_time = dt.strptime('{} 000000'.format(date), '%Y-%m-%d %H%M%S')
    end_time = dt.strptime('{} 235959'.format(date), '%Y-%m-%d %H%M%S')

    DB = preDB()
    dff = DB.get_data('max' + machine_id, start_time, end_time)

    available_sensors = dff.columns.tolist()
    available_sensors.remove('Molding Time')
    
    options = [{'label': i, 'value': i} for i in available_sensors]

    init_sensor = available_sensors[0]
    init_sensors = available_sensors[:1]

    if len(dff) <= 0:
        date_str = '({} 無數據)'.format(date)
    else:
        date_str = '({} 共{}筆數據)'.format(date, len(dff))

    dff['Molding Time'] = dff['Molding Time'].astype(str)

    spc = SPCModel()
    cl_df = spc.get_model(machine_id)
    cl_df.index = cl_df['cl_type']

    return dff.to_json(), cl_df.to_json(), options, init_sensor, options, init_sensors, \
           options, init_sensor, date_str, None


@app.callback(
    [Output('spc-max-graph', 'figure'),
     Output('spc-loading-output-1', 'children')],
    [Input('spc-max-sensor', 'value'),
     Input('spc-checklist', 'value')],
    [State('spc-temp-value-a', 'children'),
     State('spc-temp-value-b', 'children')]
)
def update_main_graph(yaxis, cl_check, jsonified_data, cl_data):
    # print('update_main_graph!')
    if jsonified_data == None:
        # print('no data...')
        return create_scatter_figure([], None, None), None

    dff = pd.read_json(jsonified_data)
    if len(dff) == 0:
        return create_scatter_figure([], None, None), None

    x = dff['Molding Time']
    y = dff[yaxis]
    x_min, x_max = x.values[0], x.values[-1]

    datas = []
    datas.append(go.Scatter(
        x=x,
        y=y,
        customdata=dff['Molding Time'],
        mode='lines+markers',
        marker={'size': 8, 'opacity': 0.5},
        line={'width': 1.5}
    ))

    if len(cl_check) > 0:
        cl_df = pd.read_json(cl_data)
        color_dict = {'cl_1.5': 'green', 'cl_3': 'orange', 'cl_4.5': 'red'}
        for check in cl_check:
            cl = cl_df.loc[['u'+check, 'l'+check], yaxis].values.round(3)
            ucl = create_cl(x, cl, 'ucl', color_dict[check])
            lcl = create_cl(x, cl, 'lcl', color_dict[check])
            datas += [ucl, lcl]

    return create_scatter_figure(datas, x_min, x_max), None


@app.callback(
    [Output('spc-temp-value-c', 'children'),
     Output('spc-loading-output-2', 'children')],
    [Input('spc-max-graph', 'clickData')],
    [State('spc-machine-id', 'value')]
)
def update_x_timeseries(click_data, machine_id):
    t = click_data['points'][0]['customdata']
    if t == 0:
        return None, None
    else:
        DB = rawDB()
        mold_time = dt.strptime(str(t), '%Y-%m-%d %H:%M:%S')
        m_df = DB.get_data('sensor' + machine_id, mold_time, mold_time)
        return m_df.to_json(), None


@app.callback(
    Output('spc-onemold-graph', 'figure'),
    [Input('spc-onemold-sensor', 'value'),
     Input('spc-temp-value-c', 'children')],
    [State('spc-max-graph', 'clickData'),]
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
            marker={'size': 6, 'opacity': 0.5},
            line={'width': 1.2},
            name=sensor.strip()
        )
        datas.append(scatter)

    t = click_data['points'][0]['customdata']
    t_str = ' Time: ' + t
    
    return create_time_series(datas, 'Linear', t_str)


@app.callback(
    Output('retrain-confirm', 'displayed'),
    [Input('retrain-button', 'n_clicks')]
)
def display_confirm(n_clicks):
    return True if n_clicks != None else False


@app.callback(
    [Output('retrain-loading-output', 'children'),
     Output('spc-date-picker-single', 'date')],
    [Input('retrain-confirm', 'submit_n_clicks')],
    [State('spc-machine-id', 'value'),
     State('spc-realtime-range', 'value')]
)
def retrain_models(n_clicks, machine_id, range_min):
    if n_clicks != None:
        update_models(machine_id, range_min)
    return None, str(dt.now())



if __name__ == '__main__':
    app.run_server(debug=True)
