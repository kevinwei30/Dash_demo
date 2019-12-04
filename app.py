import dash

app = dash.Dash(__name__)
server = app.server
app.config.suppress_callback_exceptions = True
app.title = 'molding-web-app'
