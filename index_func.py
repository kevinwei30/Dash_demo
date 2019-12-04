import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime as dt


# initial values
init_machine_id = '9738'
machine_ids = ['9738']
machine_options = [{'label': id_, 'value': id_} for id_ in machine_ids]

init_page = '模內壓SPC'
page_names = {'spc': '模內壓SPC', 'log': 'Log紀錄', 'anomaly': '異常監控'}
pages = {'模內壓SPC': 'spc', 'Log紀錄': 'log', '異常監控': 'anomaly'}
titles = {'spc': '模內壓SPC監控', 'log': '模內壓SPC管制 Log紀錄', 'anomaly': '模內壓異常狀態監控'}


def machine_id_div(page):
    return [
        html.P(
            '機台編號:',
            style={'display': 'inline-block', 'marginRight': '10px', 'color': 'white'}
        ),
        dcc.Dropdown(
            id='{}-machine-id'.format(page),
            value=init_machine_id,
            options=machine_options,
            style={'display': 'inline-block', 'minWidth': '100px', 'verticalAlign': 'middle'}
        ),
        dcc.Store(id='machine-id', storage_type='memory')
    ]

def date_picker_div(page):
    return [
        html.P(
            '日期:',
            style={'display': 'inline-block', 'marginRight': '10px', 'color': 'white'}
        ),
        dcc.DatePickerSingle(
            id='{}-date-picker-single'.format(page),
            min_date_allowed=dt(2000, 1, 1),
            max_date_allowed=dt(2030, 12, 31),
            initial_visible_month=dt.now().date(),
            date=str(dt.now()),
            display_format='YYYY-MM-DD',
            style={'display': 'inline-block', 'zIndex': '1000'}
        ),
        dcc.Loading(
            id='{}-loading-0'.format(page),
            children=[html.Div(id='{}-loading-output-0'.format(page))],
            type='circle',
            style={'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'middle'}
        )
    ]

def retrain_div(page):
    return [
        html.Button(
            '變更工況',
            id='retrain-button',
            className='button-primary'
        ),
        dcc.Loading(
            id='retrain-loading',
            children=[html.Div(id='retrain-loading-output')],
            type='circle',
            style={'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'middle'}
        )
    ]

def get_switch_link(page):
    style = {'fontSize': '20px', 'marginLeft': '20px', 'color': 'yellow'}
    href = '/' + page
    # return dcc.Link(page_names[page], href=href, style=style)
    return html.A(page_names[page], href=href, style=style)

def page_switch_div(page):
    switch_links = []
    for key in page_names.keys():
        if key != page:
            switch_links.append(get_switch_link(key))

    return [
        html.P(
            '頁面切換:',
            style={'display': 'inline-block', 'marginRight': '10px', 'color': 'white'}
        ),
    ] + switch_links

def page_bar(page):
    title = titles[page]
    region1 = machine_id_div(page)
    region2 = date_picker_div(page)
    if page == 'spc':
        region3 = retrain_div(page)
    else:
        region3 = []
    region4 = page_switch_div(page)

    return title, region1, region2, region3, region4
