import glob
import json
import re
from typing import List, Tuple

import dash
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

from algorithmics.enemy.asteroids_zone import AsteroidsZone
from algorithmics.enemy.enemy import Enemy
from algorithmics.enemy.observation_post import ObservationPost
from algorithmics.enemy.radar import Radar
from algorithmics.solution_stage2 import calculate_path
from algorithmics.utils.coordinate import Coordinate
from algorithmics.assets.generate_scatter import generate_path_scatter, generate_graph_scatter, \
    generate_all_scenario_scatters, \
    generate_graph_layout


def _extract_scenario_number_from_path(path: str) -> int:
    """Extract the number of a scenario given its name in the file system

    For example, the file
        ../resources/scenarios/scenario_5.json

    Will be converted into the integer 5.

    :param path: path to scenario's JSON in the file system
    :return: scenario's number
    """
    return int(re.match(r'.*scenario_(\d+)\.json', path).group(1))


scenario_files = glob.glob('../resources/scenarios/scenario_*.json')
scenario_files = ['../resources/scenarios\\scenario_1.json']

print('--------------------------')
print(len(scenario_files))
print('--------------------------')

scenario_files = sorted(scenario_files, key=lambda name: _extract_scenario_number_from_path(name))

colors = {
    'background': '#111111',
    'h1': '#7FDBFF',
    'text': '#0099FF'
}

app = dash.Dash(__name__, external_stylesheets=[r'./assets/bWLwgP.css'])
server = app.server

app.layout = html.Div([
    html.H1('The Most Best Application Ever', style={'text-align': 'center', 'font-family': 'Courier New',
                                                     'font-weight': 'bold', 'font-size': '30px',
                                                     'color': colors['h1']}),
    html.Div(children=[
        dcc.Dropdown(id='scenario-dropdown',
                     options=[{'label': f'Scenario #{_extract_scenario_number_from_path(filename)}',
                               'value': filename}
                              for filename in scenario_files],
                     value=scenario_files[0],
                     clearable=False,
                     style={'font-family': 'Courier New', 'font-weight': 'bold', 'color': colors['text'],
                            'margin-bottom': '10px', 'margin-right': '10px', 'font-size': '16px',
                            'width': '100%'}),
        html.Button('Run Algorithm!', id='run-button',
                    style={'color': colors['h1'], 'background-color': 'black'},
                    )
    ], style={'display': 'flex'}, className='1 row'),
    dcc.Graph(
        id='graph',
        config={'scrollZoom': True},
        style={'height': '60vh', 'margin-bottom': '10px'}
    ),
    dcc.Checklist(id='graph-toggle',
                  options=[{'label': 'Show Graph', 'value': 'Toggle'}],
                  value=[],
                  style={'font-family': 'Courier New', 'font-weight': 'bold', 'margin-top': '5px',
                         'margin-bottom': '5px', 'color': '#ffffff'}),
    html.Div('Calculated path:',
             style={'font-family': 'Courier New', 'font-weight': 'bold', 'margin-top': '5px',
                    'margin-bottom': '5px', 'color': '#ffffff'}),
    dcc.Textarea(id='calculated-path',
                 readOnly=True,
                 style={'font-family': 'Courier New', 'font-weight': 'bold', 'background-color': 'black',
                        'color': 'white', 'width': '100%'}),
    dcc.Store(id='store-path', data=[]),
    dcc.Store(id='store-edges', data=[])
], style={'margin-top': '20px', 'margin-left': '10px', 'margin-right': '10px'})


@app.callback(Output('calculated-path', 'value'),
              Input('store-path', 'data'),
              prevent_initial_call=True)
def update_path_text(path: List[Tuple[float, float]]) -> str:
    if not path:
        return 'No path returned, error occured in calculation'
    coordinates = [f'({coordinate[0]}, {coordinate[1]})' for coordinate in path]
    return ', '.join(coordinates)


def _load_scenario(scenario_path: str) -> Tuple[Coordinate, Coordinate, List[Enemy]]:
    with open(scenario_path, 'r') as f:
        raw_scenario = json.load(f)

    # Parse scenario JSON
    source = Coordinate(raw_scenario['source'][0], raw_scenario['source'][1])
    target = Coordinate(raw_scenario['target'][0], raw_scenario['target'][1])
    enemies: List[Enemy] = []
    enemies += [ObservationPost(Coordinate(raw_post['center'][0], raw_post['center'][1]), raw_post['radius'])
                for raw_post in raw_scenario['observation_posts']]
    enemies += [AsteroidsZone([Coordinate(c[0], c[1]) for c in raw_zone['boundary']])
                for raw_zone in raw_scenario['asteroids_zones']]
    enemies += [Radar(Coordinate(raw_radar['center'][0], raw_radar['center'][1]), raw_radar['radius'])
                for raw_radar in raw_scenario['radars']]

    return source, target, enemies


@app.callback(Output('graph', 'figure'),
              Input('scenario-dropdown', 'value'),
              Input('store-path', 'data'),
              Input('store-edges', 'data'),
              Input('graph-toggle', 'value'))
def update_map(scenario_path: str, path: List[Tuple[float, float]],
               edges: List[Tuple[float, float, float, float]], graph_on: str) -> go.Figure:
    source, target, enemies = _load_scenario(scenario_path)

    # If only scenario was changed, path and graph are empty
    if dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'scenario-dropdown':
        draw_path, edges_scatter = [], []

    # Otherwise, parse path and graph
    else:
        draw_path = [Coordinate(c[0], c[1]) for c in path]
        edges_scatter = [generate_graph_scatter(edges)] if len(graph_on) > 0 else []

    data = generate_all_scenario_scatters(source, target, enemies) + \
           [generate_path_scatter(draw_path, color='#cccccc')] + edges_scatter
    return go.Figure(data=data,
                     layout=generate_graph_layout())


@app.callback(Output('store-path', 'data'),
              Output('store-edges', 'data'),
              Input('run-button', 'n_clicks'),
              State('scenario-dropdown', 'value'),
              prevent_initial_call=True)
def run_button_n_clicks_changed(n_clicks: int, scenario_path: str) -> \
        Tuple[List[Tuple[float, float]], List[Tuple[float, ...]]]:
    source, target, enemies = _load_scenario(scenario_path)

    # Dash doesn't support custom return types from callbacks, so we convert the path into a list of tuples
    path, graph = calculate_path(source, target, enemies)
    return [(c.x, c.y) for c in path], [(edge[0].x, edge[0].y, edge[1].x, edge[1].y) for edge in graph.edges]


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=7324, dev_tools_silence_routes_logging=False, debug=False)
