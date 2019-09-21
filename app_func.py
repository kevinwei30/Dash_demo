import plotly.graph_objs as go
import pandas as pd
import numpy as np


def create_scatter_figure(datas, x_min, x_max):
    return {
        'data': datas,
        'layout': go.Layout(
            title={
                'text': '<b>模內壓峰值變化</b>',
                'font': {'size': 20, 'color': 'green'},
                'x': 0.05
            },
            xaxis_range=[x_min, x_max],
            xaxis={
                'title': 'Molding Time',
                'rangeselector': {'buttons': list([{'count': 1, 'label': '1h', 'step': 'hour', 'stepmode': 'backward'},
                                                   {'count': 6, 'label': '6h', 'step': 'hour', 'stepmode': 'backward'},
                                                   {'step': 'all'}])},
                'rangeslider': {'visible': True},
                'type': 'date'
            },
            yaxis={'title': '模內壓峰值', 'type': 'linear'},
            showlegend=False,
            margin={'l': 50, 'b': 40, 't': 100, 'r': 20},
            height=600,
            hovermode='closest'
        )
    }


def create_cl(x, cl, cl_type):
    type_dict = {'ucl': 0, 'lcl': 1}
    return go.Scatter(
        x=x.iloc[[0, -1]],
        y=[cl[type_dict[cl_type]], cl[type_dict[cl_type]]],
        text=[cl_type.upper()],
        mode='text+lines',
        textposition='top left',
        textfont={'size': 15, 'color': 'red'},
        line={'color': 'red', 'width': 2, 'dash': 'dot'}
    )


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


def get_Time(t):
    t = str(t)
    t_str = t[:2] + '/' + t[2:4] + '/' + t[4:6] + ' ' + t[6:8] + ':' + t[8:10] + ':' + t[10:]
    return t_str


def update_log(file, new_df):
    df = pd.read_csv(file)
    for new_row in new_df.values:
        origin_row = df[(df['Date'] == new_row[1]) & (df['time'] == new_row[2])]
        idx = origin_row.index
        df.loc[idx, ['label', 'record']] = new_row[-2], new_row[-1]

    df.to_csv(file, index=False)
    return
