import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import os
import json
import pickle
from datetime import datetime as dt
from .app_func import anomaly_figure
from .db_connectors import RecordDBConnector as recordDB
from app import app



labels = ['毛邊', '不飽模', '翹曲變形', '表面髒污', '其它']
init_columns = [{'name': 'init', 'id': 'init'}]


# page layout
layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.P(
                    '實時模內壓異常狀態監控',
                    style={'fontSize': '18px', 'fontWeight': '800', 'marginLeft': '20px'}
                ),
                dcc.Graph(
                    id='anomaly-realtime-graph',
                    style={'height': '380px'}
                )
            ], style={'display': 'inline-block', 'width': '50%', 'float': 'left',
                      'borderRight': '2px solid #CCE5FF'}),
            html.Div([
                html.P(
                    '異常相似度判別',
                    style={'fontSize': '18px', 'fontWeight': '800', 'marginLeft': '20px'}
                ),
                dcc.Graph(
                    id='anomaly-radar-graph',
                    figure={
                        'data': [
                            go.Scatterpolar(
                                r=[1, 5, 2, 2, 3],
                                theta=labels,
                                fill='toself',
                                name='@@'
                            ),
                            go.Scatterpolar(
                                r=[2, 3, 0, 3, 1],
                                theta=labels,
                                fill='toself',
                                name='##'
                            ),
                        ],
                        'layout': go.Layout(
                            height=380
                        )
                    }
                )
            ], style={'display': 'inline-block', 'width': '48%', 'float': 'right'})
        ], style={'height': '420px', 'margin': '5px 5px', 'borderBottom': '2px solid #CCE5FF'}),

        html.Div([
            html.Div([
                html.P(
                    '異常指標變化',
                    style={'fontSize': '18px', 'fontWeight': '800', 'display': 'inline-block', 'margin': '0px 20px'}
                ),
                html.P(
                    '2019-01-01',
                    id='anomaly-date-selected',
                    style={'display': 'inline-block', 'margin': '0px 20px'}
                ),
                dcc.Dropdown(
                    id='anomaly-main-sensors',
                    value=[],
                    multi=True,
                    style={'display': 'inline-block', 'width': '500px', 'verticalAlign': 'middle'}
                ),
                dcc.Loading(
                    id='anomaly-loading-1',
                    children=[html.Div(id='anomaly-loading-output-1')],
                    style={'display': 'inline-block', 'marginLeft': '20px'}
                ),
            ]),
            dcc.Graph(
                id='anomaly-main-graph',
                clickData={'points': [{'customdata': 0}]}
            )
        ], style={'padding': '5px 5px'})
    ], style={'width': '95%', 'display': 'inline-block', 'marginLeft': '20px', 'float': 'left'}),

    html.Div(id='anomaly-date-init', style={'display': 'none'}),
    html.Div(id='anomaly-temp-value', style={'display': 'none'})
])


# callbacks
@app.callback(
    [Output('anomaly-temp-value', 'children'),
     Output('anomaly-main-sensors', 'options'),
     Output('anomaly-main-sensors', 'value'),
     Output('anomaly-date-selected', 'children'),
     Output('anomaly-loading-output-0', 'children')],
    [Input('anomaly-date-picker-single', 'date'),
     Input('anomaly-machine-id', 'value')]
)
def fetch_anomaly_data(date_time, machine_id):
    date = date_time.split(' ')[0]
    start_time = dt.strptime('{} 000000'.format(date), '%Y-%m-%d %H%M%S')
    end_time = dt.strptime('{} 235959'.format(date), '%Y-%m-%d %H%M%S')

    DB = recordDB()
    df = DB.get_data('anomalylog' + machine_id, start_time, end_time)
    df['Molding Time'] = df['Molding Time'].apply(lambda t: t.strftime('%Y-%m-%d %H:%M:%S'))

    if len(df) <= 0:
        options = []
        value = []
        date_str = '({} 無數據)'.format(date)
    else:
        cols = df.columns.tolist()
        sensors = []
        for col in  cols:
            if 'sensor' in col:
                sensors.append(col)
        options = [{'label': s, 'value': s} for s in sensors]
        value = sensors[:1]
        date_str = '({} 共{}筆數據)'.format(date, len(df))

    return df.to_json(), options, value, date_str, None


@app.callback(
    [Output('anomaly-main-graph', 'figure'),
     Output('anomaly-loading-output-1', 'children')],
     # Output('anomaly-table', 'columns'),
     # Output('anomaly-table', 'data')],
    [Input('anomaly-main-sensors', 'value')],
    [State('anomaly-temp-value', 'children')]
)
def update_anomaly_graph_and_table(sensors, json_data):
    if json_data == None:
        # return anomaly_figure([], []), None, init_columns, []
        return anomaly_figure([], []), None

    log_df = pd.read_json(json_data).round(3)
    log_df['time'] = log_df['Molding Time'].apply(lambda t: t.split(' ')[1])
    table_df = log_df[['time'] + log_df.columns.tolist()[1:-1]]

    table_cols = [{'name': i, 'id': i} for i in table_df.columns]
    table_data = table_df.to_dict('records')

    t = log_df['Molding Time']

    datas = []
    for sensor in sensors:
        datas.append(go.Scatter(
            x=t,
            y=log_df[sensor],
            mode='lines+markers',
            # customdata=t,
            marker={'size': 8, 'opacity': 0.5},
            line={'width': 1.5},
            name=sensor
        ))

    # highlight regions
    shapes=[]
    # shapes = [go.layout.Shape(
    #     type="rect",
    #     xref="x",
    #     yref="paper",
    #     x0="2019-11-02 01:00:00",
    #     y0=0,
    #     x1="2019-11-02 02:30:00",
    #     y1=1,
    #     fillcolor="LightSalmon",
    #     opacity=0.5,
    #     layer="below",
    #     line_width=0,
    # )]
    
    # return anomaly_figure(datas, shapes), None, table_cols, table_data
    return anomaly_figure(datas, shapes), None



if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
