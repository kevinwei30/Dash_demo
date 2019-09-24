import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from datetime import datetime as dt
import math
import json
import os
from .data_process import DataProcess
from app import app



# pre-defined variable
df_cols = ['index', 'Date', 'time', 'max', 'region', 'label', 'record']
page_size_ = 300
origin_title = '模內壓SPC管制 log紀錄'
init_date = '2019-08-21'

col_zh = ['index', '日期', '時間', '該模壓力峰值', '管制區間(n倍標準差)', '產品標註', '額外紀錄(可編輯)']
col_zh2 = ['index', '日期', '時間', '壓力峰值', '管制區間', '產品標註', '額外紀錄']

init_sdc = [
    {
        'if': {
            'column_id': 'region',
            'filter_query': '{region} eq "< 1.5"'
        },
        'backgroundColor': '#32CD32',
        'color': 'white',
    },
    {
        'if': {
            'column_id': 'region',
            'filter_query': '{region} eq "1.5 ~ 3"'
        },
        'backgroundColor': '#FFFF66'
    },
    {   
        'if': {
            'column_id': 'region',
            'filter_query': '{region} contains "4.5"'
        },
        'backgroundColor': '#FF0000',
        'color': 'white',
    },
]

table_columns = []
table_columns2 = []
scc = []
for i, col in enumerate(df_cols):
    if col == 'label':
        table_columns.append({'name': col_zh[i], 'id': col, 'presentation': 'dropdown'})
        table_columns2.append({'name': col_zh2[i], 'id': col})
        scc.append({'if': {'column_id': col}, 'width': '15%'})
    elif col == 'record':
        table_columns.append({'name': col_zh[i], 'id': col, 'editable': True})
        table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})
        scc.append({'if': {'column_id': col}, 'width': '30%'})
    elif col == 'index' or col == 'Date':
        continue
        # table_columns.append({'name': col_zh[i], 'id': col, 'hideable': True})
    else:
        table_columns.append({'name': col_zh[i], 'id': col, 'editable': False})
        table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})
        col_width = '20%' if col == 'region' else '15%'
        scc.append({'if': {'column_id': col}, 'width': col_width})

label_options = ['毛邊', '不飽模', '翹曲變形', '表面髒污']


# init Dash app
# app = dash.Dash(__name__)
# server = app.server


# page layout
layout = html.Div([
    html.Div([
        html.Div([
            html.H5(
                origin_title,
                id='title',
                style={'color': '#00008B', 'display': 'inline-block'}
            ),
            html.P(
                init_date,
                id='log_date',
                style={'display': 'inline-block', 'margin-left': '20px',
                       'padding': '8px', 'backgroundColor': '#ADD8E6'}
            ),
            dcc.Loading(
                id='loading-log-1',
                children=[html.Div(id='loading-output-log-1')],
                style={'display': 'inline-block', 'margin-left': '20px'}
            )
        ], style={'margin-bottom': '10px'}),
        html.Div([
            dash_table.DataTable(
                id='datatable-interactivity',
                columns=table_columns,
                style_cell_conditional=scc,
                style_cell={'minWidth': '100px'},
                style_data_conditional=init_sdc,
                # data=df.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi",
                selected_rows=[],
                page_size= page_size_,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '750px', 'maxHeight': '750px', 'border': '1px solid #CCE5FF'},
                style_header={'backgroundColor': '#F0F0F0', 'fontWeight': '600'},
                export_format='xlsx',
                export_headers='display',
            )
        ]),
        html.Div([
            html.P('00', id='total-page', style={'display': 'none'}),
            html.P(
                '頁數 : 0/00',
                id='page-number',
                style={'font-size': 12, 'display': 'inline-block', 'margin-right': '20px'}
            ),
            html.P(
                '(每頁最多{:d}筆紀錄)'.format(page_size_),
                style={'font-size': 8, 'display': 'inline-block'}
            ),
            html.Div([
                # html.Button(
                #     'log重整',
                #     id='refresh_button',
                #     className='button-primary',
                #     style={'margin-right': '20px', 'display': 'inline-block',
                #            'background-color': 'transparent', 'color': '#33C3F0'}
                # ),
                html.Button(
                    '人為紀錄提交',
                    id='submit_button',
                    className='button-primary',
                    style={'display': 'inline-block'}
                )
            ], style={'float': 'right', 'display': 'inline-block'})
        ], style={'margin-top': '10px'})
    ], style={'width': '50%', 'display': 'inline-block', 'margin': '10px 10px', 'vertical-align': 'top'}
    ),
    html.Div([
        html.Div([
            html.Div([
                html.H4(
                    '警報',
                    style={'font-size': 18, 'color': '#DC143C'}
                ),
                dcc.Loading(
                    id='loading-log-2',
                    children=[html.Div(id='loading-output-log-2')],
                    style={'display': 'inline-block', 'margin-left': '20px'}
                )
            ]),
            dash_table.DataTable(
                id='alarm-section',
                columns=table_columns2,
                # data=alarm_df.to_dict('records'),
                style_cell_conditional=scc,
                style_cell={'minWidth': '60px'},
                style_data_conditional=init_sdc,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size= 100,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '360px', 'maxHeight': '360px', 'border': '1px solid #FFCCCC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            )
        ], style={'height': '450px', 'margin-bottom': '20px', 'margin-top': '10px'}),
        html.Div([
            html.Div([
                html.H4(
                    '標註 & 紀錄',
                    style={'font-size': 18, 'color': '#FF8C00'}
                ),
                dcc.Loading(
                    id='loading-log-3',
                    children=[html.Div(id='loading-output-log-3')],
                    style={'display': 'inline-block', 'margin-left': '20px'}
                )
            ]),
            dash_table.DataTable(
                id='label-section',
                columns=table_columns2,
                # data=label_df.to_dict('records'),
                style_cell_conditional=scc,
                style_cell={'minWidth': '60px'},
                style_data_conditional=init_sdc,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size= 20,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '360px', 'maxHeight': '360px', 'border': '1px solid #FFE5CC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            ),
        ], style={'height': '450px', 'margin-top': '20px'}),
    ], style={'width': '35%', 'display': 'inline-block', 'margin-left': '20px', 'vertical-align': 'top'}
    ),
    html.Div([
        html.Div([
            html.H4(
                '選擇日期',
                style={'font-size': 18, 'color': 'black'}
            ),
            dcc.DatePickerSingle(
                id='date-picker-log',
                min_date_allowed=dt(2000, 1, 1),
                max_date_allowed=dt(2030, 12, 31),
                initial_visible_month=dt(2019, 8, 21),
                date=str(dt(2019, 8, 21, 23, 59, 59)),
                display_format='YYYY-MM-DD',
                style={'display': 'inline-block', 'margin-top': '10px'}
            ),
            dcc.Loading(
                id='loading-log-0',
                children=[html.Div(id='loading-output-log-0')],
                type='circle',
                style={'display': 'inline-block', 'margin-left': '20px', 'height': '30px'}
            )
        ], style={'margin-top': '20px'}),
    ], style={'width': '10%', 'display': 'inline-block', 'margin-left': '40px', 'vertical-align': 'top'}
    ),
    html.Div(id='temp-value', style={'display': 'none'}),
    html.Div(id='origin_label_index', style={'display': 'none'}),
    dcc.ConfirmDialog(
        id='confirm',
        message='確定提交標註與紀錄嗎?',
    ),
])



# callback functions
@app.callback(
    [Output('datatable-interactivity', 'data'),
     Output('log_date', 'children'),
     Output('datatable-interactivity', 'selected_rows'),
     Output('origin_label_index', 'children'),
     Output('loading-output-log-0', 'children')],
    [Input('date-picker-log', 'date')]
    # [State('refresh_button', 'n_clicks')]
)
def fetch_data(date):
    print('fetch log!!!')

    DP = DataProcess()
    df = DP.get_log(date[:10], '1:9738-1-T')

    label_df = df[(df['label'].notnull()) | ((df['record'] != '') & (df['record'].notnull()))]
    origin_label_index = label_df.index.values.tolist()

    return df.to_dict('records'), date[:10], [], origin_label_index, None


@app.callback(
    Output('temp-value', 'children'),
    [Input('datatable-interactivity', 'data')]
)
def temp_value_update(data):
    if data == None:
        print('no data...')
        return None
    
    new_df = pd.DataFrame(data)
    if len(new_df) == 0:
        print('empty df...')
        return None

    new_alarm_df = new_df[new_df['region'].str.contains('4.5')]
    new_label_df = new_df[(new_df['label'].notnull()) | ((new_df['record'] != '') & (new_df['record'].notnull()))]

    datasets = {
        'df': new_df.to_json(),
        'alarm_df': new_alarm_df.to_json(),
        'label_df': new_label_df.to_json(),
    }
    return json.dumps(datasets)


@app.callback(
    [Output('datatable-interactivity', 'style_data_conditional'),
     Output('datatable-interactivity', 'dropdown_conditional'),
     Output('loading-output-log-1', 'children')],
    [Input('datatable-interactivity', 'selected_rows')]
)
def update_sdc(selected_rows):
    # print(selected_rows)
    row_str = ','
    for row in selected_rows:
        row_str += '{:05d},'.format(row)
    filter_str = '"' + row_str + '"'
    # print(filter_str)

    new_sdc =  [{
        'if': { 'filter_query': filter_str + ' contains {index}' },
        'background_color': '#87CEFA'
    } for i in selected_rows]

    dc = [{
        'if': {'column_id': 'label', 'filter_query': filter_str + ' contains {index}'},
        'options': [{'label': i, 'value': i}
                    for i in label_options]
    }]

    return new_sdc + init_sdc, dc, None


@app.callback(
    [Output('alarm-section', 'data'),
     Output('loading-output-log-2', 'children')],
    [Input('temp-value', 'children')]
)
def update_alarm_section(jsonified_data):
    if jsonified_data == None:
        return [], None
    
    datasets = json.loads(jsonified_data)
    alarm_df = pd.read_json(datasets['alarm_df'], dtype={'Date': str})
    
    return alarm_df.to_dict('records'), None


@app.callback(
    [Output('label-section', 'data'),
     Output('loading-output-log-3', 'children')],
    [Input('temp-value', 'children')]
)
def update_label_section(jsonified_data):
    if jsonified_data == None:
        return [], None
    
    datasets = json.loads(jsonified_data)
    label_df = pd.read_json(datasets['label_df'], dtype={'Date': str})
    
    return label_df.to_dict('records'), None


@app.callback(
    Output('page-number', 'children'),
    [Input('datatable-interactivity', 'page_current'),
     Input('datatable-interactivity', 'derived_virtual_row_ids')],
    [State('total-page', 'children')]
)
def update_page_number(page_n, row_ids, total_page):
    if row_ids != None:
        total_page_n = math.ceil(len(row_ids)/page_size_)
    else:
        total_page_n = int(total_page)
    if page_n == None:
        page_n = 0
    page_str = '頁數 : {:d}/{:d}'.format(int(page_n)+1, total_page_n)
    return page_str


@app.callback(
    Output('confirm', 'displayed'),
    [Input('submit_button', 'n_clicks')]
)
def display_confirm(n_clicks):
    return True if n_clicks != None else False


@app.callback(
    Output('confirm', 'message'),
     # Output('date-picker-log', 'date')],
    [Input('confirm', 'submit_n_clicks')],
    [State('temp-value', 'children'),
     State('log_date', 'children'),
     State('origin_label_index', 'children')]
)
def submit_confirm(submit_n_clicks, jsonified_data, date, origin_label_index):
    if submit_n_clicks == None:
        return '確定提交標註與紀錄嗎?'
    else:
        datasets = json.loads(jsonified_data)
        label_df = pd.read_json(datasets['label_df'], dtype={'Date': str})
        df = pd.read_json(datasets['df'], dtype={'Date': str})

        diff_index = set(label_df.index.values.tolist()).symmetric_difference(set(origin_label_index))

        DP = DataProcess()
        DP.update_log(df, list(diff_index))

        return '確定要再次提交標註與紀錄嗎?'



# run app server
if __name__ == '__main__':
    app.run_server(debug=True)
