import click
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, callback, clientside_callback
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly
cols = plotly.colors.DEFAULT_PLOTLY_COLORS
from pathlib import Path
import json 

from .parsing import read_log, Snapshot




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
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True

    app.layout = dbc.Container([
        html.H1('blossom simulation'),
        html.Div(f'Run logs: {data_dir.resolve()}'),
        html.Hr(),
        dcc.Graph(
            id='multiplot-graph'
        ), 
        # dcc.Graph(
        #     id='alive-graph'
        # ), 
        # dcc.Graph(
        #     id='dead-graph'
        # ), 
        # dcc.Graph(
        #     id='ratio-graph'
        # ), 
        dcc.Interval(
            id="interval-component", 
            interval=5000
        )
    ])

    @app.callback(
        Output('multiplot-graph', 'figure'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_multiplot_data(n_intervals):
        fns = sorted(data_dir.glob("log_ds*"))
        species = list(read_log(fns[0])['species'].keys())
        x = []
        y = []
        for fn in fns:
            log_dict = read_log(fn)
            x.append(log_dict['world']['time'])
            y.append(log_dict['species'])
        y_alive = {s: [d[s]['alive'] for d in y] for s in species}
        y_dead= {s: [d[s]['dead'] for d in y] for s in species}
        y_ratio = [d[species[1]]['alive']/d[species[0]]['alive'] for d in y]

        fig = make_subplots(rows=3, cols=1,
                            vertical_spacing=0.1,
                            subplot_titles=('Alive', 'Dead', 'Ratio'))
        for i, s in enumerate(species):
            fig.add_trace(row=1, col=1,
                          trace=go.Scatter(x=x, 
                                           y=y_alive[s],
                                           line=dict(color=cols[i]),
                                           name=s, 
                                           legendgroup=s))
        for i, s in enumerate(species):
            fig.add_trace(row=2, col=1,
                          trace=go.Scatter(x=x, 
                                           y=y_dead[s],
                                           line=dict(color=cols[i]),
                                           name=s, 
                                           legendgroup=s,
                                           showlegend=False))
        fig.add_trace(row=3, col=1,
                      trace=go.Scatter(x=x, 
                                       y=y_ratio, 
                                       line=dict(color='black'),
                                       name='ratio',
                                       showlegend=False))
        fig.update_layout(height=750)
        return fig
    
    app.run(port=port, debug=True)


if __name__ == '__main__':
    dashboard()