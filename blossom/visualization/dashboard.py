import click
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, callback, clientside_callback
import dash_bootstrap_components as dbc
import plotly.express as px
from pathlib import Path
import json 

from .parsing import read_log


@click.command()
@click.argument('data_dir')
@click.option('-p', '--port', type=int, default=8888,
              help='Local port')
def dashboard(data_dir, port=8888):
    """
    Set up dashboard for tracking blossom runs
    """
    data_dir = Path(data_dir)

    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = Dash(__name__, 
               update_title=None, 
               external_stylesheets=external_stylesheets)  # remove "Updating..." from title
    
    # figure = dict(data=[{'x': [], 'y': []}, {'x': [], 'y': []}], 
    #               layout=dict(xaxis=dict(range=[0, 999]), 
    #                           yaxis=dict(range=[0, 200])))

    # app.layout = html.Div([
    #     html.H1('blossom simulation', style={'font-family': 'Open Sans'}),
    #     html.Div(f'Run logs: {data_dir.resolve()}'),
    #     dcc.Graph(
    #         id='live-update-graph'
    #     ), 
    #     dcc.Interval(
    #         id="interval-component", 
    #         interval=100
    #     )
    # ])
    app.layout = dbc.Container([
        html.H1('blossom simulation'),
        html.Div(f'Run logs: {data_dir.resolve()}'),
        html.Hr(),
        dcc.Graph(
            id='live-update-graph'
        ), 
        dcc.Interval(
            id="interval-component", 
            interval=1000
        )
    ])

    @app.callback(
        Output('live-update-graph', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_data(n_intervals):
        fns = sorted(data_dir.glob("log*"))
        x = []
        y = []
        species_list = []
        for fn in fns:
            log_dict = read_log(fn)
            for species in log_dict['species']:
                x.append(log_dict['world']['time'])
                y.append(log_dict['species'][species]['alive'])
                species_list.append(species)
        df = pd.DataFrame.from_dict(dict(x=x, y=y, species=species_list))
        fig = px.line(df, x='x', y='y', color='species',
                      labels={
                          'x': 'Timestep',
                          'y': 'Count'
                      })

        return fig
    
    app.run(port=port, debug=True)


if __name__ == '__main__':
    dashboard()