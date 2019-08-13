import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

external_stylesheets = ['bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('20190808_200.csv')

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
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            html.Div([
                html.P('壓力傳感器(for模內壓曲線)')
            ], style={'height': '30px'}), 
            dcc.Dropdown(
                id='sensor-yaxis-column',
                options=[{'label': i, 'value': i} for i in available_sensors],
                value='1:9738-1-T'
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
        )
    ], style={'width': '49%', 'display': 'inline-block', 'margin': '20px 5px', 'float': 'left'}),
    
    html.Div([
        dcc.Graph(id='y-time-series'),
    ], style={'display': 'inline-block', 'width': '49%', 'float': 'right', 'margin': '20px 5px'})
])


def get_Time(t):
    t = str(t)
    t_str = t[:2] + '/' + t[2:4] + '/' + t[4:6] + ' ' + t[6:8] + ':' + t[8:10] + ':' + t[10:]
    return t_str


@app.callback(
    dash.dependencies.Output('main-indicator-scatter', 'figure'),
    [dash.dependencies.Input('max-yaxis-column', 'value'),])
     # dash.dependencies.Input('crossfilter-yaxis-column', 'value'),])
def update_graph(yaxis_column_name):
    dff = df[df['variable'] == yaxis_column_name]
    # t = dff[dff['Elapsed Time'] == 0.6]['Molding Time'].apply(get_Time)
    x = dff[dff['Elapsed Time'] == 0.6]['Molding Time'].apply(lambda t: datetime.strptime(str(t), '%y%m%d%H%M%S'))
    y = dff[dff['Elapsed Time'] == 0.6]['value']

    return {
        'data': [
            go.Scatter(
                x=x,
                y=y,
                # text=dff[dff['Elapsed Time'] == 0.6]['Molding Time'].apply(get_Time),
                customdata=dff[dff['Elapsed Time'] == 0.6]['Molding Time'],
                mode='lines+markers',
                marker={
                    'size': 10,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'}
                }
            ),
            go.Scatter(
                x=x.iloc[[0, -1]],
                y=[9, 9],
                text=['UCL'],
                mode='text+lines',
                textposition='top left',
                textfont={
                    'size': 15,
                    'color': 'red'
                },
                line={
                    'color': 'red',
                    'width': 2,
                    'dash': 'dot'
                }
            ),
            go.Scatter(
                x=x.iloc[[0, -1]],
                y=[8, 8],
                text=['LCL'],
                mode='text, lines',
                textposition='bottom left',
                textfont={
                    'size': 15,
                    'color': 'red'
                },
                line={
                    'color': 'red',
                    'width': 2,
                    'dash': 'dot'
                }
            )
        ],
        'layout': go.Layout(
            title={
                'text': '<b>模內壓峰值變化</b>',
                'font': {'size': 20, 'color': 'green'},
                'x': 0.1
            },
            xaxis_range=[
                x.values[0], x.values[-1]
            ],
            xaxis={
                'title': 'Molding Time'
            },
            yaxis={
                # 'title': yaxis_column_name,
                'title': '模內壓峰值',
                'type': 'linear'
            },
            showlegend=False,
            margin={'l': 50, 'b': 40, 't': 50, 'r': 20},
            height=600,
            hovermode='closest'
        )
    }


def create_time_series(dff, axis_type, title):
    return {
        'data': [go.Scatter(
            x=dff['Elapsed Time'],
            y=dff['value'],
            mode='lines+markers',
            marker={
                'size': 5,
            }
        )],
        'layout': {
            'title': {
                'text': '<b>單模模內壓曲線</b>',
                'font': {'size': 20, 'color': 'blue'},
                'x': 0.1
            },
            'height': 600,
            'margin': {'l': 50, 'b': 40, 'r': 20, 't': 50},
            'annotations': [{
                'x': 0, 'y': 0.99, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'right', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            'yaxis': {'type': 'linear' if axis_type == 'Linear' else 'log', 'title': '模內壓'},
            'xaxis': {'showgrid': False, 'title': 'Elapsed Time (s)'}
        }
    }


@app.callback(
    dash.dependencies.Output('y-time-series', 'figure'),
    [dash.dependencies.Input('main-indicator-scatter', 'hoverData'),
     dash.dependencies.Input('sensor-yaxis-column', 'value')])
def update_x_timeseries(hoverData, yaxis_column_name):
    dff = df[df['variable'] == yaxis_column_name]
    try:
        t = hoverData['points'][0]['customdata']
    except:
        t = 0
    dff = dff[dff['Molding Time'] == t]
    if t == 0:
        t_str = ''
    else:
        t_str = ' Time: ' + get_Time(t)
    return create_time_series(dff, 'Linear', t_str)


if __name__ == '__main__':
    app.run_server(debug=True)
