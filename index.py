import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
from apps import spc_page, log_page, anomaly_page
from datetime import datetime as dt
from index_func import page_bar


server = app.server


# main layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    html.Div([
        html.Div([
            html.H4(
                id='title',
                style={'color': 'white', 'marginLeft': '20px'}
            )
        ], style={'display': 'inline-block', 'width': '25%'}),
        html.Div(
            id='machine-id-region',
            style={'display': 'inline-block', 'width': '15%'}),
        html.Div(
            id='date-picker-region',
            style={'display': 'inline-block', 'width': '20%'}),
        html.Div(
            id='retrain-region',
        style={'display': 'inline-block', 'width': '20%'}),
        html.Div(
            id='page-switch-region',
            style={'display': 'inline-block', 'width': '20%'})
    ], style={'backgroundColor': '#4169E1', 'height': '65px', 'marginBottom': '10px'}),

    html.Div(id='page-content')
])



# callback functions
@app.callback(
    [Output('title', 'children'),
     Output('machine-id-region', 'children'),
     Output('date-picker-region', 'children'),
     Output('retrain-region', 'children'),
     Output('page-switch-region', 'children'),
     Output('page-content', 'children')],
    [Input('url', 'pathname')]
)
def display_page(url):
    if url == '/':
        layout = spc_page.layout
        page = 'spc'
    elif url == '/spc':
        layout = spc_page.layout
        page = 'spc'
    elif url == '/log':
        layout = log_page.layout
        page = 'log'
    elif url == '/anomaly':
        layout = anomaly_page.layout
        page = 'anomaly'
    else:
        return '', [], [], [], [], 'Page Not Found'

    title, region1, region2, region3, region4 = page_bar(page)

    return title, region1, region2, region3, region4, layout



if __name__ == '__main__':
    app.run_server(debug=True)
