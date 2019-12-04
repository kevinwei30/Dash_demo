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
from .db_connectors import RecordDBConnector as recordDB
from .app_func import data_table_var
from app import app



page_size_ = 300
label_options = ['毛邊', '不飽模', '翹曲變形', '表面髒污', '其它']
sc = {'textOverflow': 'ellipsis', 'overflow': 'hidden', 'maxWidth': 0}
init_columns = [{'name': 'init', 'id': 'init'}]

# page layout
layout = html.Div([
    html.Div([
        html.Div([
            html.P(
                '2019-01-01',
                id='log-date',
                style={'display': 'inline-block'}
            ),
            dcc.Loading(
                id='log-loading-1',
                children=[html.Div(id='log-loading-output-1')],
                style={'display': 'inline-block', 'marginLeft': '20px'}
            )
        ]),
        html.Div([
            dash_table.DataTable(
                id='log-datatable',
                columns=init_columns,
                # style_cell_conditional=scc,
                # style_data_conditional=init_sdc,
                # data=df.to_dict('records'),
                style_cell=sc,
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi",
                selected_rows=[],
                page_size= page_size_,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '740px', 'maxHeight': '740px', 'border': '1px solid #CCE5FF'},
                style_header={'backgroundColor': '#F0F0F0', 'fontWeight': '600'},
                export_format='xlsx',
                export_headers='display',
            )
        ]),
        html.Div([
            html.P('00', id='log-total-page', style={'display': 'none'}),
            html.P(
                '頁數 : 0/00',
                id='log-page-number',
                style={'fontSize': 12, 'display': 'inline-block', 'marginRight': '20px'}
            ),
            html.P(
                '(每頁最多{:d}筆紀錄)'.format(page_size_),
                style={'fontSize': 8, 'display': 'inline-block'}
            ),
            html.Div([
                html.Button(
                    '人為紀錄提交',
                    id='log-submit-button',
                    className='button-primary',
                    style={'display': 'inline-block'}
                )
            ], style={'float': 'right', 'display': 'inline-block'})
        ], style={'marginTop': '5px'})
    ], style={'width': '55%', 'display': 'inline-block', 'margin': '0px 10px', 'verticalAlign': 'top'}),

    html.Div([
        html.Div([
            html.Div([
                html.H4(
                    '警報',
                    style={'fontSize': '18px', 'fontWeight': '800', 'color': '#DC143C'}
                ),
                dcc.Loading(
                    id='log-loading-2',
                    children=[html.Div(id='log-loading-output-2')],
                    style={'display': 'inline-block', 'marginLeft': '20px'}
                )
            ]),
            dash_table.DataTable(
                id='log-alarm-section',
                columns=init_columns,
                style_cell=sc,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size= 100,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '300px', 'maxHeight': '300px', 'border': '1px solid #FFCCCC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            )
        ], style={'height': '400px', 'marginBottom': '20px', 'marginTop': '10px'}),
        html.Div([
            html.Div([
                html.H4(
                    '標註 & 紀錄',
                    style={'fontSize': '18px', 'fontWeight': '800', 'color': '#FF8C00'}
                ),
                dcc.Loading(
                    id='log-loading-3',
                    children=[html.Div(id='log-loading-output-3')],
                    style={'display': 'inline-block', 'marginLeft': '20px'}
                )
            ]),
            dash_table.DataTable(
                id='log-label-section',
                columns=init_columns,
                style_cell=sc,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size= 20,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '300px', 'maxHeight': '300px', 'border': '1px solid #FFE5CC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            ),
        ], style={'height': '400px', 'marginTop': '20px'}),
    ], style={'width': '40%', 'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'top'}
    ),
    html.Div(id='log-temp-value', style={'display': 'none'}),
    html.Div(id='log-table-settings', style={'display': 'none'}),
    html.Div(id='log-label-index', style={'display': 'none'}),
    dcc.ConfirmDialog(
        id='log-confirm',
        message='確定提交標註與紀錄嗎?',
    ),
])



# callback functions
@app.callback(
    [Output('log-table-settings', 'children'),
     Output('log-datatable', 'data'),
     Output('log-date', 'children'),
     Output('log-datatable', 'selected_rows'),
     Output('log-label-index', 'children'),
     Output('log-loading-output-0', 'children')],
    [Input('log-date-picker-single', 'date'),
     Input('log-machine-id', 'value')]
)
def fetch_data(date_time, machine_id):
    date = date_time.split(' ')[0]
    start_time = dt.strptime('{} 000000'.format(date), '%Y-%m-%d %H%M%S')
    end_time = dt.strptime('{} 235959'.format(date), '%Y-%m-%d %H%M%S')

    DB = recordDB()
    df = DB.get_data('spclog' + machine_id, start_time, end_time)

    if len(df) == 0:
        return None, [], date + ' (無數據)', [], [], None
    else:
        date_str = '{} (共{}筆數據)'.format(date, len(df))

    base_sdc, scc, table_columns1, table_columns2 = data_table_var(df)
    table_settings = {
        'base_sdc': base_sdc,
        'scc': scc,
        'table_columns1': table_columns1,
        'table_columns2': table_columns2
    }
    settings = json.dumps(table_settings)

    df['index'] = df.index.to_series().apply(lambda i: str(i).zfill(5))
    df['date'] = df['Molding Time'].dt.date
    df['time'] = df['Molding Time'].dt.time

    df.drop('Molding Time', axis=1, inplace=True)
    cols = df.columns.tolist()
    df = df[cols[-3:] + cols[:-3]]

    label_df = df[(df['label'].notnull()) | ((df['record'] != '') & \
                  (df['record'].notnull()))]
    label_index = label_df.index.values.tolist()

    return settings, df.to_dict('records'), date_str, [], label_index, None


@app.callback(
    [Output('log-datatable', 'columns'),
     Output('log-datatable', 'style_cell_conditional'),
     Output('log-alarm-section', 'columns'),
     Output('log-alarm-section', 'style_cell_conditional'),
     Output('log-alarm-section', 'style_data_conditional'),
     Output('log-label-section', 'columns'),
     Output('log-label-section', 'style_cell_conditional'),
     Output('log-label-section', 'style_data_conditional')],
    [Input('log-table-settings', 'children')]
)
def set_table_format(jsonified_settings):
    if jsonified_settings == None:
        return init_columns, [], init_columns, [], [], init_columns, [], []
    
    settings = json.loads(jsonified_settings)
    columns1 = settings['table_columns1']
    columns2 = settings['table_columns2']
    scc = settings['scc']
    sdc = settings['base_sdc']

    return columns1, scc, columns2, scc, sdc, columns2, scc, sdc


@app.callback(
    Output('log-temp-value', 'children'),
    [Input('log-datatable', 'data')]
)
def temp_value_update(data):
    if data == None:
        # print('no data...')
        return None
    
    new_df = pd.DataFrame(data)
    if len(new_df) == 0:
        # print('empty df...')
        return None

    tmp_series = new_df.iloc[:, 1:-2].apply(lambda x: '/ '.join(x), axis=1)
    new_alarm_df = new_df[tmp_series.str.contains('4.5')]
    new_label_df = new_df[(new_df['label'].notnull()) | ((new_df['record'] != '') & (new_df['record'].notnull()))]

    datasets = {
        'df': new_df.to_json(),
        'alarm_df': new_alarm_df.to_json(),
        'label_df': new_label_df.to_json(),
    }
    share_datasets = json.dumps(datasets)

    return share_datasets


@app.callback(
    [Output('log-datatable', 'style_data_conditional'),
     Output('log-datatable', 'dropdown_conditional'),
     Output('log-loading-output-1', 'children')],
    [Input('log-datatable', 'selected_rows'),
     Input('log-table-settings', 'children')]
)
def update_sdc(selected_rows, jsonified_settings):
    if jsonified_settings == None:
        return [], [], None
    
    settings = json.loads(jsonified_settings)
    base_sdc = settings['base_sdc']
    if len(selected_rows) == 0:
        return base_sdc, [], None

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

    return new_sdc + base_sdc, dc, None


@app.callback(
    [Output('log-alarm-section', 'data'),
     Output('log-loading-output-2', 'children')],
    [Input('log-temp-value', 'children')]
)
def update_alarm_section(jsonified_data):
    if jsonified_data == None:
        return [], None
    
    datasets = json.loads(jsonified_data)
    alarm_df = pd.read_json(datasets['alarm_df'], dtype={'Date': str})
    
    return alarm_df.to_dict('records'), None


@app.callback(
    [Output('log-label-section', 'data'),
     Output('log-loading-output-3', 'children')],
    [Input('log-temp-value', 'children')]
)
def update_label_section(jsonified_data):
    if jsonified_data == None:
        return [], None
    
    datasets = json.loads(jsonified_data)
    label_df = pd.read_json(datasets['label_df'], dtype={'Date': str})
    
    return label_df.to_dict('records'), None


@app.callback(
    Output('log-page-number', 'children'),
    [Input('log-datatable', 'page_current'),
     Input('log-datatable', 'derived_virtual_row_ids')],
    [State('log-total-page', 'children')]
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
    Output('log-confirm', 'displayed'),
    [Input('log-submit-button', 'n_clicks')]
)
def display_confirm(n_clicks):
    return True if n_clicks != None else False


@app.callback(
    [Output('log-confirm', 'message'),
     Output('log-date-picker-single', 'date')],
    [Input('log-confirm', 'submit_n_clicks')],
    [State('log-temp-value', 'children'),
     State('log-date', 'children'),
     State('log-label-index', 'children'),
     State('log-machine-id', 'value')]
)
def submit_confirm(n_clicks, jsonified_data, date, origin_label_index, machine_id):
    # if n_clicks == None:
    #     date = time.strftime('%Y-%m-%d', time.gmtime())
    #     return '確定提交標註與紀錄嗎?', date + ' 23:59:59'

    datasets = json.loads(jsonified_data)
    label_df = pd.read_json(datasets['label_df'], dtype={'Date': str})
    df = pd.read_json(datasets['df'], dtype={'Date': str})

    diff_index = set(label_df.index.values.tolist() + origin_label_index)

    df = df.loc[diff_index, :]
    df['Molding Time'] = pd.to_datetime(df.loc[:, ['date', 'time']].astype(str).\
                         apply(lambda x: ' '.join(x), axis=1))
    df.drop(['index', 'date', 'time'], axis=1, inplace=True)
    cols = df.columns.tolist()
    diff_df = df[cols[-1:] + cols[:-1]]

    DB = recordDB()
    DB.update_data('spclog' + machine_id, diff_df)

    return '確定要再次提交標註與紀錄嗎?', date + ' 23:59:59'
    # return '確定要再次提交標註與紀錄嗎?', dt.now().date()



# run app server
if __name__ == '__main__':
    app.run_server(debug=True)
