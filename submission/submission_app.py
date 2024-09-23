import glob
import json
import os
import re
import time
from typing import Dict, List, Tuple, Optional

import dash_auth
from dash_extensions.enrich import DashProxy, TriggerTransform, MultiplexerTransform
from flask import request
from dash.dependencies import State, Input, Output

from algorithmics.assets.generate_scatter import generate_all_scenario_scatters, generate_graph_layout, \
    generate_path_scatter
from algorithmics.enemy.enemy import Enemy

import dash
from dash import dcc, html, dash_table

from algorithmics.enemy.asteroids_zone import AsteroidsZone
from algorithmics.enemy.observation_post import ObservationPost
from algorithmics.enemy.radar import Radar
from algorithmics.utils.coordinate import Coordinate

import plotly.graph_objects as go


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _convert_string_to_path(path_str: str) -> List[Coordinate]:
    coordinates: List[Coordinate] = []
    path_stripped = path_str.replace(' ', ' ').replace('(', ' ').replace(')', ' ').replace(',', ' ')
    if not all(s.isnumeric() or s in [' ', '.', '-'] for s in path_stripped):
        raise ValueError('Path not in format')
    numbers = [float(s) for s in path_stripped.split() if _is_float(s)]
    if len(numbers) % 2 != 0:
        raise ValueError('Path not in format')
    for c1, c2 in zip(numbers[::2], numbers[1::2]):
        coordinates.append(Coordinate(float(c1), float(c2)))
    return coordinates


def extract_scenario_number_from_path(path: str) -> int:
    return int(re.match(r'.*scenario_(\d+)\.json', path).group(1))


scenario_files = glob.glob('../resources/scenarios/scenario_*.json')

with open('../resources/users.json', 'r') as f:
    users = json.load(f)
usernames = {user['username']: user['password'] for user in users.values()}

app = DashProxy(__name__, transforms=[TriggerTransform(), MultiplexerTransform()],
                external_stylesheets=[r'./assets/bWLwgP.css'])
server = app.server
auth = dash_auth.BasicAuth(
    app,
    usernames
)

app.layout = html.Div(
    [
        html.Div(
            [
                # Title
                html.H1('Submission App', style={'text-align': 'center', 'font-family': 'Courier New',
                                                 'font-weight': 'bold', 'font-size': '30px',
                                                 'background-color': '#D5D5D5'},
                        className='pt-2 pb-2'),

                # Scenario Dropdown
                dcc.Dropdown(id='scenario-dropdown',
                             options=[
                                 {'label': f'Scenario #{extract_scenario_number_from_path(filename)}',
                                  'value': filename}
                                 for filename in scenario_files
                             ],
                             value=scenario_files[0],
                             style={'font-family': 'Courier New', 'font-weight': 'bold', 'color': 'black',
                                    'background-color': 'black', 'margin-bottom': '10px', 'margin-right': '10',
                                    'font-size': '16px', 'width': '100%'}),

                # Tables and map
                html.Div(
                    children=[

                        # Tables
                        html.Div(
                            children=[
                                html.H1('Leaderboard', style={'text-align': 'center', 'font-family': 'Courier New',
                                                              'font-weight': 'bold', 'font-size': '30px',
                                                              'background-color': '#D5D5D5', 'margin': 0}),
                                html.Div(dash_table.DataTable(id='leaderboard-table',
                                                              editable=False,
                                                              columns=[{'name': '#', 'id': 'placement'},
                                                                       {'name': 'Path Length', 'id': 'path-length'},
                                                                       {'name': 'Submission Time',
                                                                        'id': 'submission-time'}],
                                                              data=[],
                                                              style_cell={'textAlign': 'left', 'padding': '10px',
                                                                          'font-size': 20, 'color': 'white',
                                                                          'backgroundColor': '#868686'},
                                                              style_cell_conditional=[
                                                                  {'if': {'column_id': 'placement'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'column_id': 'path-length'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'column_id': 'submission-time'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'row_index': 'odd'},
                                                                   'backgroundColor': '#3B3B3B'}
                                                              ],
                                                              style_as_list_view=True,
                                                              style_header={'font-weight': 'bold', 'color': 'white',
                                                                            'backgroundColor': '#3B3B3B'})),

                                html.H1('Personal Best', style={'text-align': 'center', 'font-family': 'Courier New',
                                                                'font-weight': 'bold', 'font-size': '30px',
                                                                'background-color': '#D5D5D5', 'margin': 0}),

                                html.Div(dash_table.DataTable(id='personal-table', editable=False,
                                                              columns=[{'name': '#', 'id': 'placement', 'hidden': True},
                                                                       {'name': 'Path Length', 'id': 'path-length',
                                                                        'hidden': True},
                                                                       {'name': 'Submission Time',
                                                                        'id': 'submission-time'}],
                                                              data=[],
                                                              style_cell={'textAlign': 'left', 'padding': '10px',
                                                                          'font-size': 20, 'color': 'white',
                                                                          'backgroundColor': '#868686'},
                                                              style_cell_conditional=[
                                                                  {'if': {'column_id': 'placement'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'column_id': 'path-length'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'column_id': 'submission-time'},
                                                                   'width': 'fit-content'},
                                                                  {'if': {'row_index': 'odd'},
                                                                   'backgroundColor': '#3B3B3B'}
                                                              ],
                                                              style_as_list_view=True,
                                                              style_header={'font-weight': 'bold', 'color': 'white',
                                                                            'backgroundColor': '#3B3B3B'})),
                            ],
                            style={'width': '30%', 'display': 'inline-block'}
                        ),

                        # Map
                        html.Div(dcc.Graph(id='scenario-graph'),
                                 style={'width': '70%', 'display': 'inline-block'})],
                    style={'display': 'flex'}
                ),

                html.Hr(style={'margin-bottom': 0}),

                # Submission Zone
                html.Div(
                    children=[

                        # Title
                        html.H1('Submission', style={'text-align': 'center', 'font-family': 'Courier New',
                                                     'font-weight': 'bold', 'font-size': '30px',
                                                     'background-color': '#D5D5D5', 'display': 'inline-block',
                                                     'width': '15%', 'height': 125},
                                className='pt-2 pb-2'),

                        # Data zone
                        html.Div(
                            children=[

                                # Insert path zone
                                html.Div(
                                    children=[
                                        html.Div('Insert path:',
                                                 style={'font-family': 'Courier New', 'font-weight': 'bold',
                                                        'font-size': 16, 'color': 'white', 'margin-left': 10,
                                                        'width': '10%', 'display': 'inline-block'}),
                                        dcc.Input(id='path-input',
                                                  style={'font-family': 'Courier New', 'font-weight': 'bold',
                                                         'width': '75%', 'display': 'inline-block',
                                                         'margin-right': 20}),
                                        html.Button('Submit!', id='submit-button',
                                                    style={'color': '#7FDBFF', 'background-color': 'black',
                                                           'margin-right': 10,
                                                           'width': '15%', 'display': 'inline-block'})
                                    ],
                                    style={'display': 'flex'}
                                ),

                                # Response zone
                                html.Div(id='submit-message')
                            ],
                            style={'width': '85%', 'display': 'inline-block', 'margin-top': 20}
                        )
                    ],
                    style={'display': 'flex'}
                )
            ],
            style={}, className='col-8'
        )
    ],
    style={'height': '100vh', 'background-color': '#111111'}, className='container-fluid row pt-5 pb-5'
)

ERROR_STYLE = {'font-family': 'Courier New', 'font-weight': 'bold', 'font-size': 16, 'color': 'red', 'margin-left': 10}
MEH_STYLE = {'font-family': 'Courier New', 'font-weight': 'bold', 'font-size': 16, 'color': 'orange', 'margin-left': 10}
OK_STYLE = {'font-family': 'Courier New', 'font-weight': 'bold', 'font-size': 16, 'color': 'green', 'margin-left': 10}


def load_scenario(scenario_path: str) -> Tuple[int, Coordinate, Coordinate, List[Enemy]]:
    scenario_number = extract_scenario_number_from_path(scenario_path)

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

    return scenario_number, source, target, enemies


def path_crosses_no_entrance(path: List[Coordinate], enemies: List[Enemy]) -> bool:
    """Verify if the path crosses any observation posts or asteroid zones

    :param path: path to be evaluated
    :param enemies: enemies to be avoided
    :return: True if the path does not cross any no-entrance zone, False otherwise
    """
    return any(any(not enemy.is_legal_leg(start, end) for enemy in enemies if not isinstance(enemy, Radar))
               for start, end in zip(path, path[1:]))


def compute_radar_detection_distance(path: List[Coordinate], enemies: List[Enemy]) -> float:
    """Compute accumulated distance of legs in radar detection

    :param path: path to be verified
    :param enemies: list of enemies to be avoided
    :return: accumulated distance of legs in radar detection
    """
    return sum(start.distance_to(end) for start, end in zip(path, path[1:])
               if any(not enemy.is_legal_leg(start, end) for enemy in enemies if isinstance(enemy, Radar)))


def compute_path_length(path: List[Coordinate]) -> float:
    """Compute distance of traversing a path

    :param path: path to measure length of
    :return: length of the path
    """
    total = 0.0
    for coord1, coord2 in zip(path, path[1:]):
        total += coord1.distance_to(coord2)
    return total


def get_submission_path(scenario_number: int) -> str:
    """Compute path of submission results of given scenario

    :param scenario_number: given scenario
    :return: path to submission data of the given scenario
    """
    return f'../resources/submissions/scenario_{scenario_number}_submission.json'


def load_submission_dict(scenario_number: int) -> Dict:
    """Load submission achievements for given scenario

    :param scenario_number: scenario to be loaded
    :return: submission for the given scenario
    """

    # Get submissions path
    submission_path = get_submission_path(scenario_number)

    # If path already exists, load the data
    if os.path.exists(submission_path):
        with open(submission_path, 'r') as f:
            submissions = json.load(f)

    # Otherwise, create a new data dict
    else:
        submissions = {}

    return submissions


def save_submission_dict(scenario_number: int, submissions: Dict) -> None:
    """Update the saved submissions file

    :param scenario_number: scenario to be updates
    :param submissions: updates json value
    :return: None
    """

    # Make sure submissions are sorted correctly
    submissions = dict(sorted(submissions.items(),
                              key=lambda item: (item[1]['path_length'], item[1]['submission_time'])))

    # Save updates submission file
    with open(get_submission_path(scenario_number), 'w') as f:
        json.dump(submissions, f)


def save_path(path: List[Coordinate], scenario_number: int) -> bool:
    """Save new path to submissions file if it is an improvement over previous submissions

    :param path: new path
    :param scenario_number: scenario to be regarded
    :return: True if this is the best path this user have submitted for this scenario, False otherwise
    """
    # Load existing submissions
    submissions = load_submission_dict(scenario_number)

    path_length = compute_path_length(path)
    username = request.authorization['username']
    # If user has already submitted a legal path, verify the new path is an improvement
    if username in submissions and path_length >= submissions[username]['path_length']:
        return False

    # Otherwise, update the path
    submissions[username] = {
        'path_length': path_length,
        'submission_time': time.time(),
        'path': [[c.x, c.y] for c in path]
    }

    save_submission_dict(scenario_number, submissions)

    return True


def generate_table_data_from_submissions_file(index: int, data: Dict) -> Dict:
    """Generate from data saved in the submission file, the data required for visualization in app tables

    :param index: index of the item in the table
    :param data: data as it appears in the submissions json
    :return: data as it appears in app tables
    """

    return {
        'placement': index,
        'path-length': round(data['path_length'], 6),
        'submission-time': time.strftime('%H:%M:%S', time.localtime(data['submission_time']))
    }


def extract_path_from_submissions_data(submission: Dict) -> List[Coordinate]:
    """Create path from a submission files and a desired index

    :param submission: dict representing a single submission
    :return: path
    """

    return [Coordinate(c[0], c[1]) for c in submission['path']]


@app.callback(Output('leaderboard-table', 'data'),
              Output('personal-table', 'data'),
              Input('scenario-dropdown', 'value'),
              Input('submit-message', 'children'))
def load_scenario_results(scenario_path: str, message: str) -> Tuple[List, List]:
    scenario_number = extract_scenario_number_from_path(scenario_path)
    submissions = load_submission_dict(scenario_number)

    # Load leaderboard table data
    leaderboard_table_data = [generate_table_data_from_submissions_file(idx + 1, data)
                              for idx, data in enumerate(list(submissions.values())[:5])]

    # Load personal table data
    username = request.authorization['username']
    personal_table_data = [] if username not in submissions else \
        [generate_table_data_from_submissions_file(1, submissions[username])]

    return leaderboard_table_data, personal_table_data


@app.callback(Output('scenario-graph', 'figure'),
              Input('scenario-dropdown', 'value'))
def draw_selected_scenario(scenario_path: str) -> go.Figure:
    scenario_number, source, target, enemies = load_scenario(scenario_path)

    return go.Figure(data=generate_all_scenario_scatters(source, target, enemies),
                     layout=generate_graph_layout())


@app.callback(Output('scenario-graph', 'figure'),
              Output('personal-table', 'active_cell'),
              Output('personal-table', 'selected_cells'),
              Input('leaderboard-table', 'active_cell'),
              Input('leaderboard-table', 'data'),
              State('scenario-dropdown', 'value'))
def draw_leaderboard_path(active_cell: Dict, table, scenario_path: str) -> \
        Tuple[go.Figure, Optional[Dict], List]:
    if active_cell is None:
        return dash.no_update, dash.no_update, dash.no_update

    scenario_number, source, target, enemies = load_scenario(scenario_path)
    submissions = load_submission_dict(scenario_number)

    try:
        chosen_submission_data = list(submissions.values())[int(active_cell['row'])]
        path = extract_path_from_submissions_data(chosen_submission_data)

        data, layout = generate_all_scenario_scatters(source, target, enemies), generate_graph_layout()
        data += [generate_path_scatter(path)]

        return go.Figure(data=data, layout=layout), None, []
    except IndexError:
        return dash.no_update, dash.no_update, dash.no_update


@app.callback(Output('scenario-graph', 'figure'),
              Output('leaderboard-table', 'active_cell'),
              Output('leaderboard-table', 'selected_cells'),
              Input('personal-table', 'active_cell'),
              Input('personal-table', 'data'),
              State('scenario-dropdown', 'value'))
def draw_personal_path(active_cell: Dict, table, scenario_path: str) -> \
        Tuple[go.Figure, Optional[Dict], List]:
    if active_cell is None:
        return dash.no_update, dash.no_update, dash.no_update

    scenario_number, source, target, enemies = load_scenario(scenario_path)
    submissions = load_submission_dict(scenario_number)

    try:
        username = request.authorization['username']
        chosen_submission_data = submissions[username]
        path = extract_path_from_submissions_data(chosen_submission_data)

        data, layout = generate_all_scenario_scatters(source, target, enemies), generate_graph_layout()
        data += [generate_path_scatter(path)]

        return go.Figure(data=data, layout=layout), None, []
    except KeyError:
        return dash.no_update, dash.no_update, dash.no_update


@app.callback(Output('submit-message', 'children'),
              Output('submit-message', 'style'),
              Input('submit-button', 'n_clicks'),
              State('scenario-dropdown', 'value'),
              State('path-input', 'value'),
              prevent_initial_call=True)
def submit_button_clicked(n_clicks: int, scenario_path: str, path: str) -> Tuple[str, dict]:
    # Make sure path and passcode were given
    if path is None or path == '':
        return 'You must enter a path to be submitted', ERROR_STYLE

    # Parse path into coordinates list
    try:
        path = _convert_string_to_path(path)
    except Exception as e:
        print('Error occurred while parsing path')
        print(e)
        return 'An error occurred while parsing the path, make sure you copied it correctly', ERROR_STYLE

    # Load scenario and assert fitting source and target
    scenario_number, source, target, enemies = load_scenario(scenario_path)
    if not source == path[0]:
        return f'First coordinate in the path must be the source coordinate (x={source.x}, y={source.y})', ERROR_STYLE
    if not target == path[-1]:
        return f'Last coordinate in the path must be the target coordinate (x={target.x}, y={target.y})', ERROR_STYLE

    # Verify path legality and respond accordingly
    if path_crosses_no_entrance(path, enemies):
        return f'Path is illegal! it crosses a non-entrance zone', ERROR_STYLE
    detection_distance = compute_radar_detection_distance(path, enemies)
    if detection_distance > 0:
        return f'Path is illegal! It has {round(detection_distance, 2)} miles under detection', ERROR_STYLE

    # Save path
    path_length = compute_path_length(path)
    path_improvement = save_path(path, scenario_number)
    if not path_improvement:
        return f'Path of length {path_length} is not an improvement regarding your previous attempts :(', MEH_STYLE

    # Report Success to user
    return f'Path was successfully submitted! Calculated path length is: {path_length}', OK_STYLE


if __name__ == '__main__':
    app.run_server(port=8324, debug=False, dev_tools_silence_routes_logging=True)
