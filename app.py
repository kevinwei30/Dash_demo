import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from datetime import datetime
import math


# customed functions
def date_process(t):
    t = str(t)
    return '20%s-%s-%s' % (t[:2], t[2:4], t[4:6])

def time_process(t):
    t = str(t)
    return '%s:%s:%s' % (t[6:8], t[8:10], t[10:12])

def cl_region(x):
    if x <= max_cl['ucl_1.5'] and x >= max_cl['lcl_1.5']:
        return '< 1.5'
    elif x <= max_cl['ucl_3'] and x >= max_cl['lcl_3']:
        return '1.5 ~ 3'
    elif x <= max_cl['ucl_4.5'] and x >= max_cl['lcl_4.5']:
        return '3 ~ 4.5'
    else:
        return '> 4.5'


# data preprocess
df = pd.read_csv('0821_max.csv')

df['Date'] = df['Time'].apply(date_process)
df['time'] = df['Time'].apply(time_process)
df = df.drop('Time', axis=1)
df = df[['Date', 'time', 'max']]

cl_df = pd.read_csv('cl.csv', index_col=0)
max_cl = cl_df.loc[:, 'max']

df['region'] = df['max'].apply(cl_region)
df['label'] = [None for i in range(len(df))]
df['record'] = ['' for i in range(len(df))]
df['select_'] = ['N' for i in range(len(df))]
selected_rows_ = []


# pre-defined variable
col_zh = ['日期', '時間', '該模壓力峰值', '管制區間(n倍標準差)', '產品標註', '額外紀錄(可編輯)']
col_zh2 = ['日期', '時間', '壓力峰值', '管制區間', '產品標註', '額外紀錄']

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

page_size_ = 300
total_page_ = math.ceil(len(df)/page_size_)
origin_title = '模內壓SPC管制log紀錄'

table_columns = []
table_columns2 = []
scc = []
for i, col in enumerate(df.columns):
    if col == 'label':
        table_columns.append({'name': col_zh[i], 'id': col, 'presentation': 'dropdown'})
        table_columns2.append({'name': col_zh2[i], 'id': col})
        scc.append({'if': {'column_id': col}, 'width': '15%'})
    elif col == 'record':
        table_columns.append({'name': col_zh[i], 'id': col, 'editable': True})
        table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})
        scc.append({'if': {'column_id': col}, 'width': '20%'})
    elif col == 'select_':
        continue
        # table_columns.append({'name': '勾選', 'id': col, 'hideable': True})
    else:
        table_columns.append({'name': col_zh[i], 'id': col, 'editable': False})
        table_columns2.append({'name': col_zh2[i], 'id': col, 'editable': False})
        col_width = '20%' if col == 'region' else '15%'
        scc.append({'if': {'column_id': col}, 'width': col_width})

dc = [{
    'if': {'column_id': 'label', 'filter_query': '{select_} eq "Y"'},
    'options': [{'label': i, 'value': i}
                for i in ['毛邊', '不飽模']]
}]

alarm_df = df[df['region'].str.contains('4.5')]
label_df = df[df['label'].notnull()]


# init Dash app
app = dash.Dash(__name__)
server = app.server

# page layout
app.layout = html.Div([
    html.Div([
        # html.Button('Submit', id='button'),
        html.Div([
            html.H4(
                origin_title,
                id='title',
                style={'font-size': 20, 'color': '#00008B', 'margin-top': '5px'}
            )
        ], style={'margin-bottom': '10px'}), 
        html.Div([
            dash_table.DataTable(
                id='datatable-interactivity',
                columns=table_columns,
                style_cell_conditional=scc,
                style_cell={'minWidth': '100px'},
                dropdown_conditional=dc,
                style_data_conditional=init_sdc,
                data=df.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                # column_selectable="single",
                row_selectable="multi",
                # row_deletable=True,
                # selected_columns=[],
                selected_rows=[],
                # page_action="native",
                # page_current= 0,
                page_size= page_size_,
                # fixed_columns={'headers': True, 'data': 4},
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '750px', 'maxHeight': '750px', 'border': '1px solid #CCE5FF'},
                style_header={'backgroundColor': '#F0F0F0', 'fontWeight': '600'},
                export_format='xlsx',
                export_headers='display',
            )
        ]),
        html.Div([
            html.P(
                '頁數 : {:d}/{:d}'.format(0, total_page_),
                id='page-number',
                style={'font-size': 12}
            ),
            html.P(
                '(每頁最多{:d}筆紀錄)'.format(page_size_),
                style={'font-size': 8}
            )
        ])
    ], style={'width': '45%', 'display': 'inline-block', 'margin': '10px 10px', 'vertical-align': 'top'}
    ),
    html.Div([
        html.Div([
            html.H4(
                'Alarm Table',
                style={'font-size': 18, 'color': '#DC143C'}
            ),
            dash_table.DataTable(
                id='alarm-section',
                columns=table_columns2,
                data=alarm_df.to_dict('records'),
                style_cell_conditional=scc,
                style_cell={'minWidth': '60px'},
                style_data_conditional=init_sdc,
                filter_action="native",
                page_size= 100,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '360px', 'maxHeight': '360px', 'border': '1px solid #FFCCCC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            )
        ], style={'height': '450px', 'margin-bottom': '20px', 'margin-top': '10px'}),
        html.Div([
            html.H4(
                'Labeled & Recorded Table',
                style={'font-size': 18, 'color': '#FF8C00'}
            ),
            dash_table.DataTable(
                id='label-section',
                columns=table_columns2,
                data=label_df.to_dict('records'),
                style_cell_conditional=scc,
                style_cell={'minWidth': '60px'},
                style_data_conditional=init_sdc,
                filter_action="native",
                page_size= 20,
                fixed_rows={'headers': True, 'data': 0 },
                style_table={'minHeight': '360px', 'maxHeight': '360px', 'border': '1px solid #FFE5CC'},
                style_header={'backgroundColor': '#F0F0F0'},
                export_format='xlsx',
                export_headers='display',
            )
        ], style={'height': '450px', 'margin-top': '20px'}),
    ], style={'width': '30%', 'display': 'inline-block', 'margin-left': '20px', 'vertical-align': 'top'}
    )
])


# callback functions

@app.callback(
    [Output('datatable-interactivity', 'style_data_conditional'),
     Output('datatable-interactivity', 'data')],
    [Input('datatable-interactivity', 'selected_rows')]
)
def update_styles(selected_rows):
    new_sdc =  [{
        'if': { 'row_index': i },
        'background_color': '#87CEFA'
    } for i in selected_rows]
    global df, selected_rows_
    if len(selected_rows) > len(selected_rows_):
        diff = list(set(selected_rows) - set(selected_rows_))
        df.iloc[diff, -1] = 'Y'
    else:
        diff = list(set(selected_rows_) - set(selected_rows))
        df.iloc[diff, -1] = 'N'
    selected_rows_ = selected_rows
    return new_sdc + init_sdc, df.to_dict('records')


@app.callback(
    Output('page-number', 'children'),
    [Input('datatable-interactivity', 'page_current'),
     Input('datatable-interactivity', 'derived_virtual_row_ids')]
)
def update_page_number(page_n, row_ids):
    if row_ids != None:
        total_page = math.ceil(len(row_ids)/page_size_)
    else:
        total_page = total_page_
    if page_n == None:
        page_n = 0
    page_str = '頁數 : {:d}/{:d}'.format(int(page_n)+1, total_page)
    return page_str


@app.callback(
    [Output('label-section', 'data'),
     Output('alarm-section', 'data')],
    [Input('datatable-interactivity', 'data')]
)
def update_label_section(data):
    global df
    df = pd.DataFrame(data)
    alarm_df = df[df['region'].str.contains('4.5')]
    label_df = df[(df['label'].notnull()) | (df['record'] != '')]
    return label_df.to_dict('records'), alarm_df.to_dict('records')


# run app server
if __name__ == '__main__':
    app.run_server()
