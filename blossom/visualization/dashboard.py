import click
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, callback, clientside_callback
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly
colors = plotly.colors.DEFAULT_PLOTLY_COLORS
from pathlib import Path
import json 
import humanfriendly

from .parsing import read_log


@click.command()
@click.argument('track_dir')
@click.option('-p', '--port', type=int, default=8888,
              help='Local port')
def dashboard(track_dir, port=8888):
    """
    Set up dashboard for tracking blossom runs
    """
    track_dir = Path(track_dir)

    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = Dash(__name__, 
               update_title=None, 
               external_stylesheets=external_stylesheets)  # remove "Updating..." from title
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True

    # Set dash layout
    button_style = {"display": "inline", "padding-left": "0.5rem", "padding-right": "0.5rem"}
    app.layout = dbc.Container([
        html.H1('blossom dashboard'),
        html.Div([
            html.Label('Location:', style={"padding-right": "0.5rem"}),
            dbc.Badge(str(track_dir.resolve()), color='info')
        ], style={'padding': 10, 'flex': 1}),
        # html.Hr(),
        html.Div([
            html.Div([
                html.Label('Dataset'),
                dcc.Dropdown(id='dataset-dropdown')
            ], style={'padding': 10, 'flex': 1}),
            html.Div([
                html.Label(f'Update period'),
                dcc.RadioItems(
                    id='interval-radio-buttons',
                    options=[
                        {'label': html.Div('1 sec', style=button_style), 'value': 1000},
                        {'label': html.Div('5 sec', style=button_style), 'value': 5000},
                        {'label': html.Div('1 min', style=button_style), 'value': 60000},
                    ],
                    value=1000,
                    style={'display': 'flex'}
                ),
            ], style={'padding': 10, 'flex': 1}),
        ], style={'display': 'flex', 'flexDirection': 'row'}),
        html.Div([
            html.Div([
                html.Label('Cumulative elapsed time:', style={"padding-right": "0.5rem"}),
                dbc.Badge(id='elapsed-badge', color='success')
            ], style={'padding': 10, 'flex': 1}),
            html.Div([
                html.Label('Data volume:', style={"padding-right": "0.5rem"}),
                dbc.Badge(id='size-badge', color='primary')
            ], style={'padding': 10, 'flex': 1}),
        ], style={'display': 'flex', 'flexDirection': 'row'}),
        dcc.Graph(
            id='multiplot-graph', 
            animate=True,
            style={'height': '60vh'}
        ),
        html.Div(id='dropdown-dummy-div'),
        dcc.Store(id='elapsed-store'),
        dcc.Store(id='size-store'),
        dcc.Store(id='dataset-filenames-store'),
        dcc.Interval(
            id='interval-component', 
            interval=1000
        )
    ])

    @callback(
        Output('interval-component', 'interval'),
        Input('interval-radio-buttons', 'value')
    )
    def update_interval_period(value):
        return value

    @callback(
        Output('dataset-dropdown', 'options'),
        Input('interval-component', 'n_intervals'),
    )
    def update_dropdown_options(n_intervals):
        run_dirs = [x for x in track_dir.glob('logs/*') if x.is_dir()]
        # if {track_dir / 'logs', track_dir / 'data'}.issubset(set(run_dirs)):
        #     run_dirs = [track_dir]
        return sorted([str(x.name) for x in run_dirs])
        
    @callback(
        Output('dataset-dropdown', 'value'),
        Input('dropdown-dummy-div', 'children')
    )
    def set_dropdown_value(children):
        run_dirs = [x for x in track_dir.glob('logs/*') if x.is_dir()]
        # if {track_dir / 'logs', track_dir / 'data'}.issubset(set(run_dirs)):
        #     return str(track_dir)
        if len(run_dirs) == 0:
            return None
        recent_idx = np.argmax([x.stat().st_mtime for x in run_dirs])
        return str(run_dirs[recent_idx].name)
    
    @callback(
        Output('elapsed-badge', 'children'),
        Input('elapsed-store', 'data')
    )
    def update_elapsed_label(elapsed_time):
        return humanfriendly.format_timespan(elapsed_time)
    
    @callback(
        Output('size-badge', 'children'),
        Input('size-store', 'data')
    )
    def update_size_label(size):
        return humanfriendly.format_size(size)

    @callback(
        Output('multiplot-graph', 'figure'),
        Output('dataset-filenames-store', 'data'),
        Output('elapsed-store', 'data'),
        Output('size-store', 'data'),
        Input('dataset-dropdown', 'value')
    )
    def update_figure_on_dropdown(run_name):
        figure = make_subplots(rows=3, cols=1,
                               shared_xaxes=True,
                               vertical_spacing=0.15,
                               subplot_titles=('Alive', 'Dead', 'Ratio'))
        figure.update_layout(uirevision=run_name, 
                             xaxis_showticklabels=True, 
                             xaxis2_showticklabels=True, 
                             margin=dict(t=50))
        for i in range(3):
            figure.update_yaxes(title_text='Count', autorange=True, 
                                row=i+1, col=1)
        figure.update_xaxes(title_text='Timestep', autorange=True, 
                            row=3, col=1)
        # figure.update_layout(height=600, uirevision=True, margin=dict(t=40))
        if run_name is not None:
            run_dir = track_dir / 'logs' / run_name
            all_fns = [str(x) for x in Path(run_dir).glob('*.log')]
            if all_fns != []:
                species = list(read_log(all_fns[0])['species'].keys())
                for i, s in enumerate(species):
                    figure.add_trace(row=1, col=1,
                                     trace=go.Scatter(x=[], 
                                                      y=[],
                                                      line=dict(color=colors[i]),
                                                      name=s, 
                                                      legendgroup=s))
                for i, s in enumerate(species):
                    figure.add_trace(row=2, col=1,
                                     trace=go.Scatter(x=[], 
                                                      y=[],
                                                      line=dict(color=colors[i]),
                                                      name=s, 
                                                      legendgroup=s,
                                                      showlegend=False))
                figure.add_trace(row=3, col=1,
                                 trace=go.Scatter(x=[], 
                                                  y=[], 
                                                  line=dict(color='black'),
                                                  name='ratio',
                                                  showlegend=False))
                return figure, {'analyzed_fns': []}, 0, 0
            
        figure.add_trace(row=1, col=1,
                         trace=go.Scatter(x=[], 
                                          y=[],))
        figure.add_trace(row=2, col=1,
                         trace=go.Scatter(x=[], 
                                          y=[],))
        figure.add_trace(row=3, col=1,
                         trace=go.Scatter(x=[], 
                                          y=[],))
        return figure, {'analyzed_fns': []}, 0, 0

    @callback(
        Output('multiplot-graph', 'extendData'),
        Output('dataset-filenames-store', 'data', allow_duplicate=True),
        Output('elapsed-store', 'data', allow_duplicate=True),
        Output('size-store', 'data', allow_duplicate=True),
        Input('interval-component', 'n_intervals'),
        State('dataset-dropdown', 'value'),
        State('multiplot-graph', 'figure'),
        State('dataset-filenames-store', 'data'),
        State('elapsed-store', 'data'),
        State('size-store', 'data'),
        prevent_initial_call=True
    )
    def update_multiplot_data(n_intervals, run_name, figure, dataset_fns, elapsed_time, size):
        if run_name is None:
            return None, dataset_fns, 0, 0
        run_dir = track_dir / 'logs' / run_name

        dataset_fns = dataset_fns or {'analyzed_fns': []}

        all_fns = [str(x) for x in Path(run_dir).glob('*.log')]
        fns = sorted(set(all_fns) - set(dataset_fns['analyzed_fns']))

        if len(all_fns) == 0:
            return None, dataset_fns, 0, 0
        species = list(read_log(all_fns[0])['species'].keys())

        x = []
        y = []
        for fn in fns:
            log_dict = read_log(fn)
            x.append(log_dict['world']['timestep'])
            y.append(log_dict['species'])
            elapsed_time += log_dict['world']['elapsed_time']
            size += log_dict['info']['size']
        y_alive = {s: [d[s]['alive'] for d in y] for s in species}
        y_dead = {s: [d[s]['dead'] for d in y] for s in species}
        y_ratio = [d[species[1]]['alive']/d[species[0]]['alive'] for d in y]

        extendData = [
            {
                'x': [x] * (2 * len(species) + 1),
                'y': [y_alive[s] for s in species] + [y_dead[s] for s in species] + [y_ratio]
            },
            list(range(2 * len(species) + 1))
        ]
        dataset_fns['analyzed_fns'].extend(fns)
        return extendData, dataset_fns, elapsed_time, size
    
    app.run(port=port, debug=True)


if __name__ == '__main__':
    dashboard()