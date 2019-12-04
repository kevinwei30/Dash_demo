import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
from .model_operations import SPCModel, AnomalyModel


def cl_shapes(cl_data, main_sensor):
    shapes = []
    if cl_data != None:
        cl_df = pd.read_json(cl_data)
        color_dict = {'cl_4.5': 'Red', 'cl_3': 'Yellow', 'cl_1.5': 'LightGreen'}
        for check in color_dict.keys():
            cl = cl_df.loc[['u'+check, 'l'+check], main_sensor].values.round(3)
            shapes += [go.layout.Shape(
                type="rect",
                xref="paper",
                yref="y",
                x0=0,
                y0=cl[1],
                x1=1,
                y1=cl[0],
                fillcolor=color_dict[check],
                opacity=0.5,
                layer="below",
                line_width=0
            )]
    return shapes


def realtime_figure(datas, x_min, x_max, cl_data, main_sensor):
    return {
        'data': datas,
        'layout': go.Layout(
            xaxis_range=[x_min, x_max],
            xaxis={
                'title': 'Molding Time',
                'type': 'date'
            },
            yaxis={'title': '模內壓峰值', 'type': 'linear'},
            legend={'x': 0, 'y': 1.1, 'orientation': 'h'},
            margin={'l': 50, 'b': 40, 't': 40, 'r': 50},
            height=380,
            hovermode='closest',
            shapes=cl_shapes(cl_data, main_sensor)
        )
    }


def create_scatter_figure(datas, x_min, x_max):
    return {
        'data': datas,
        'layout': go.Layout(
            xaxis_range=[x_min, x_max],
            xaxis={
                'title': 'Molding Time',
                'type': 'date'
            },
            yaxis={'title': '模內壓峰值', 'type': 'linear'},
            showlegend=False,
            margin={'l': 50, 'b': 50, 't': 10, 'r': 50},
            height=380,
            hovermode='closest'
        )
    }


def create_cl(x, cl, cl_type, color):
    type_dict = {'ucl': 0, 'lcl': 1}
    return go.Scatter(
        x=x.iloc[[0, -1]],
        y=[cl[type_dict[cl_type]], cl[type_dict[cl_type]]],
        mode='lines',
        textposition='top left',
        textfont={'size': 15, 'color': color},
        line={'color': color, 'width': 1, 'dash': 'dot'}
    )


def create_time_series(datas, axis_type, title):
    return {
        'data': datas,
        'layout': go.Layout(
            height=400,
            margin={'l': 50, 'b': 40, 'r': 20, 't': 60},
            annotations=[{
                'x': 0, 'y': 1.1, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'right', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            yaxis={'type': 'linear' if axis_type == 'Linear' else 'log', 'title': '模內壓'},
            xaxis={'showgrid': False, 'title': 'Elapsed Time (s)'},
            legend={'x': 0.3, 'y': 1.1, 'orientation': 'h', 'bordercolor': 'black', 'borderwidth': 1}
        )
    }


def data_table_var(log_df):
    sensor_n = log_df.shape[1] - 3

    # pre-defined variable
    df_cols = ['index', 'Date', 'time']
    df_cols += ['sensor' + str(i+1) for i in range(sensor_n)]
    df_cols += ['label', 'record']

    col_zh = ['index', '日期', '時間']
    col_zh += ['管制區間' + str(i+1) for i in range(sensor_n)]
    col_zh1 = col_zh + ['不良標註', '備註(可編輯)']
    col_zh2 = col_zh + ['不良標註', '備註']

    sdc = []
    for i in range(sensor_n):
        s = 'sensor' + str(i+1)
        sdc += [
            {
                'if': {
                    'column_id': s,
                    'filter_query': '{' + s + '} eq "< 1.5"'
                },
                'backgroundColor': '#32CD32',
                'color': 'white',
            },
            {
                'if': {
                    'column_id': s,
                    'filter_query': '{' + s + '} eq "1.5 ~ 3"'
                },
                'backgroundColor': '#FFFF66'
            },
            {   
                'if': {
                    'column_id': s,
                    'filter_query': '{' + s + '} contains "4.5"'
                },
                'backgroundColor': '#FF0000',
                'color': 'white',
            },
        ]

    table_columns1 = []
    table_columns2 = []
    tmp_width = '{:d}%'.format(50 // sensor_n)
    for i, col in enumerate(df_cols):
        if col == 'label':
            table_columns1.append({'name': col_zh1[i], 'id': col, 'presentation': 'dropdown'})
            table_columns2.append({'name': col_zh2[i], 'id': col})
        elif col == 'record':
            table_columns1.append({'name': col_zh1[i], 'id': col, 'editable': True})
            table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})
        elif col == 'index' or col == 'Date':
            continue
        else:
            table_columns1.append({'name': col_zh1[i], 'id': col, 'editable': False})
            table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})

    scc = [
        {'if': {'column_id': 'time'}, 'width': '10%'},
        {'if': {'column_id': 'label'}, 'width': '15%'},
        {'if': {'column_id': 'record'}, 'width': '30%'}
    ]

    return sdc, scc, table_columns1, table_columns2


def anomaly_figure(datas, shapes):
    return {
        'data': datas,
        'layout': go.Layout(
            xaxis={
                'title': 'Molding Time',
                'type': 'date'
            },
            yaxis={'title': '異常指標 (超過0為異常)', 'type': 'linear'},
            legend={'x': 0.2, 'y': 1.1, 'orientation': 'h'},
            margin={'l': 50, 'b': 40, 't': 10, 'r': 10},
            height=400,
            hovermode='closest',
            shapes=shapes
        )
    }


def update_models(machine_id, minutes):
    # get time
    end_t = dt.now()
    # end_t = dt.strptime('20191102130000', '%Y%m%d%H%M%S')
    start_t = end_t - timedelta(minutes=minutes)
    print('Model Update: use data from {} to {}'.format(start_t, end_t))

    # # update SPC model
    spc = SPCModel()
    spc.update_model(machine_id, start_t, end_t)

    # # update anomaly detection model
    ad_model = AnomalyModel()
    ad_model.update_model(machine_id, start_t, end_t)
