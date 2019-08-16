import dash
import dash_core_components as dcc
import dash_html_components as html
# import dash_daq as daq
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

external_stylesheets = ['bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

datafile = 'data_50.csv'
df = pd.read_csv(datafile)

available_sensors = df['variable'].unique()

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.P('壓力傳感器(for模內壓峰值變化)')
            ], style={'height': '30px'}), 
            dcc.Dropdown(
                id='max-yaxis-column',
                options=[{'label': i, 'value': i} for i in available_sensors],
                value='1:9738-1-T'
            ),
            dcc.Checklist(
                id='cl_check',
                options=[
                    {'label': '管制線', 'value': 'CL'}
                ],
                value=[],
                labelStyle={'display': 'inline-block'}
            )  
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            html.Div([
                html.P('壓力傳感器(for模內壓曲線)')
            ], style={'height': '30px'}), 
            dcc.Dropdown(
                id='sensor-yaxis-column',
                options=[{'label': i, 'value': i} for i in available_sensors],
                value=['1:9738-1-T', ' 2:9738-1-W'],
                multi=True
            ),
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '5px 5px',
    }),

    html.Div([
        dcc.Graph(
            id='main-indicator-scatter',
            hoverData={'points': [{'customdata': 0}]}
        ),
        dcc.Slider(
            id='date_slider',
            min=df['Date'].min(),
            max=df['Date'].max(),
            value=df['Date'].max(),
            marks={str(date): '20' + str(date) for date in df['Date'].unique()},
        )
    ], style={'width': '50%', 'display': 'inline-block', 'margin': '20px 5px', 'padding-left': '20px', 'float': 'left'}),
    
    html.Div([
        dcc.Graph(id='y-time-series'),
    ], style={'display': 'inline-block', 'width': '45%', 'float': 'right', 'margin': '20px 5px'}),

    dcc.Interval(
        id='Interval-component',
        interval=60*1000, # in milliseconds, now update every 10 seconds
        n_intervals=60
    )
])


def get_Time(t):
    t = str(t)
    t_str = t[:2] + '/' + t[2:4] + '/' + t[4:6] + ' ' + t[6:8] + ':' + t[8:10] + ':' + t[10:]
    return t_str


@app.callback(
    dash.dependencies.Output('main-indicator-scatter', 'figure'),
    [dash.dependencies.Input('max-yaxis-column', 'value'),
     dash.dependencies.Input('cl_check', 'value'),
     dash.dependencies.Input('date_slider', 'value'),
     dash.dependencies.Input('Interval-component', 'n_intervals')])
def update_graph(yaxis_column_name, cl_check, date, n):
    df = pd.read_csv(datafile)
    ddf = df[df['Date'] == date]
    dff = ddf[ddf['variable'] == yaxis_column_name]
    x = dff[dff['Elapsed Time'] == 0.6]['Molding Time'].apply(lambda t: datetime.strptime(str(t), '%y%m%d%H%M%S'))
    # y = dff[dff['Elapsed Time'] == 0.6]['value']
    y = dff.groupby('Time')['value'].max()

    datas = []
    datas.append(go.Scatter(
        x=x,
        y=y,
        customdata=dff[dff['Elapsed Time'] == 0.6]['Molding Time'],
        mode='lines+markers',
        marker={'size': 8, 'opacity': 0.5},
        line={'width': 2}
    ))
    if 'CL' in cl_check:
        ucl = go.Scatter(
                x=x.iloc[[0, -1]],
                y=[14, 14],
                text=['UCL'],
                mode='text+lines',
                textposition='top left',
                textfont={'size': 15, 'color': 'red'},
                line={'color': 'red', 'width': 2, 'dash': 'dot'})
        lcl = go.Scatter(
                x=x.iloc[[0, -1]],
                y=[12, 12],
                text=['LCL'],
                mode='text+lines',
                textposition='top left',
                textfont={'size': 15, 'color': 'red'},
                line={'color': 'red', 'width': 2, 'dash': 'dot'})
        datas += [ucl, lcl]

    return {
        'data': datas,
        'layout': go.Layout(
            title={
                'text': '<b>模內壓峰值變化</b>',
                'font': {'size': 20, 'color': 'green'},
                'x': 0.05
            },
            xaxis_range=[
                x.values[0], x.values[-1]
            ],
            xaxis={
                'title': 'Molding Time',
                'rangeselector': {'buttons': list([{'count': 10, 'label': '10m', 'step': 'minute', 'stepmode': 'backward'},
                                                   {'count': 1, 'label': '1h', 'step': 'hour', 'stepmode': 'backward'},
                                                   {'step': 'all'}])},
                'rangeslider': {'visible': True},
                'type': 'date'
            },
            yaxis={
                # 'title': yaxis_column_name,
                'title': '模內壓峰值',
                'type': 'linear'
            },
            showlegend=False,
            margin={'l': 50, 'b': 40, 't': 100, 'r': 20},
            height=600,
            hovermode='closest'
        )
    }


def create_time_series(datas, axis_type, title):
    return {
        'data': datas,
        'layout': {
            'title': {
                'text': '<b>單模模內壓曲線</b>',
                'font': {'size': 20, 'color': 'blue'},
                'x': 0.05
            },
            'height': 600,
            'margin': {'l': 50, 'b': 40, 'r': 20, 't': 80},
            'annotations': [{
                'x': 0, 'y': 0.99, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'right', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            'yaxis': {'type': 'linear' if axis_type == 'Linear' else 'log', 'title': '模內壓'},
            'xaxis': {'showgrid': False, 'title': 'Elapsed Time (s)'},
            'legend': {'x': 0.3, 'y': 1.0, 'orientation': 'h', 'bordercolor': 'black', 'borderwidth': 1}
        }
    }


@app.callback(
    dash.dependencies.Output('y-time-series', 'figure'),
    [dash.dependencies.Input('main-indicator-scatter', 'hoverData'),
     dash.dependencies.Input('sensor-yaxis-column', 'value'),
     dash.dependencies.Input('date_slider', 'value'),])
     # dash.dependencies.Input('Interval-component', 'n_intervals')])
def update_x_timeseries(hoverData, sensors, date):
    try:
        t = hoverData['points'][0]['customdata']
    except:
        t = 0
    datas = []
    ddf = df[df['Date'] == date]
    for sensor in sensors:
        dff = ddf[ddf['variable'] == sensor]
        dff = dff[dff['Molding Time'] == t]
        scatter = go.Scatter(
            x=dff['Elapsed Time'],
            y=dff['value'],
            mode='lines+markers',
            marker={'size': 4},
            line={'width': 2},
            name=sensor.strip()
        )
        datas.append(scatter)    
    if t == 0:
        t_str = ''
    else:
        t_str = ' Time: ' + get_Time(t)
    return create_time_series(datas, 'Linear', t_str)


if __name__ == '__main__':
    app.run_server(debug=True)
