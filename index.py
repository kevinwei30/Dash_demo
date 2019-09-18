import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
from apps import spc_page, log_page


server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


# 目錄頁
index_page = html.Div([
    html.H2(children='Molding App', id='title'),
    html.Ul([
        html.Li(html.A('SPC-page', href='SPC')),
        html.Li(html.A('log-page', href='log')),
    ]),
])


# Update the index
@app.callback(
    Output('page-content', 'children'), 
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return index_page
    elif pathname == '/SPC':
        return spc_page.layout
    elif pathname == '/log':
        return log_page.layout
    else:
        return 'URL not found'


if __name__ == '__main__':
    app.run_server(debug=True)
