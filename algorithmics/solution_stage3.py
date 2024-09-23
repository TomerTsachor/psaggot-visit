import random
from itertools import combinations
from typing import List, Tuple

import networkx as nx
from shapely.geometry import Point, Polygon
from tqdm import tqdm

from algorithmics.enemy.asteroids_zone import AsteroidsZone
from algorithmics.enemy.enemy import Enemy
from algorithmics.enemy.observation_post import ObservationPost
from algorithmics.enemy.radar import Radar
from algorithmics.utils.coordinate import Coordinate

SAMPLES = 2000
EDGE_RADIUS = 5


# Stage 1 methods


def add_enemies_to_graph(graph: nx.Graph, enemies: List[Enemy]) -> None:
    """Add nodes to the graph, based on the enemies

    :param graph: graph to be extended
    :param enemies: enemies to be avoided
    :return: None
    """

    # For every enemy, add nodes to the graph
    for enemy in enemies:

        # If the enemy is an asteroid zone, add its corners
        if isinstance(enemy, AsteroidsZone):
            graph.add_nodes_from(enemy.boundary)

        # If the enemy is an observation post, add its approximation
        if isinstance(enemy, ObservationPost) or isinstance(enemy, Radar):
            graph.add_nodes_from(enemy.approximate_boundary())


def is_legal_leg(start: Coordinate, end: Coordinate, enemies: List[Enemy]) -> bool:
    """Assert that the movement from start to end is legal, regarding all enemies

    :param start: start of the movement
    :param end: destination of the movement
    :param enemies: enemies to be considered
    :return: True if the leg is legal, False otherwise
    """
    return all(enemy.is_legal_leg(start, end) for enemy in enemies)


# Stage 2 methods


def sample_in_polygon(polygon: Polygon) -> Coordinate:
    """Sample a coordinate uniformly inside a polygon

    :param polygon: polygon to be sampled inside
    :return: sampled <code>Coordinate</code>
    """

    # Note: this method of sampling is called `reject sampling`, where we sample uniformly in the bounding box of the
    # polygon and return the sampled point only if it happens to fall inside the polygon.
    # There are more advanced and efficient methods, you can take it as a thought exercise to think of one - but don't
    # put into it much time before you finish this stage.

    left, bottom, right, top = polygon.bounds
    while True:
        x = random.uniform(left, right)
        y = random.uniform(bottom, top)
        if polygon.contains(Point(x, y)):
            return Coordinate(x, y)


def add_nodes_inside_radars(graph: nx.DiGraph, enemies: List[Enemy]) -> None:
    """Add nodes and edges for movement inside radars

    :param graph: current graph
    :param enemies: list of enemies to be avoided
    :return: None
    """
    # Filter radars. If none exist, yield
    radars = [enemy for enemy in enemies if isinstance(enemy, Radar)]
    if len(radars) == 0:
        return

    # Add new nodes to graph
    new_nodes = []
    samples_per_radar = SAMPLES // len(radars)
    for radar in radars:
        new_nodes += [sample_in_polygon(radar.circle) for _ in range(samples_per_radar)]

    # Iteratively, sample nodes and try connecting them to the graph
    for node in tqdm(new_nodes):

        # Add node to the graph
        graph.add_node(node)
        for other in graph.nodes:

            # Skip current node and nodes further than EDGE_RADIUS from it
            if other == node or node.distance_to(other) > EDGE_RADIUS:
                continue

            # If leg crosses a no-entrance, skip it
            if not is_leg_legal_only_no_entrances(node, other, enemies):
                continue

            # Connect edge in both directions
            dist = node.distance_to(other)
            graph.add_edge(other, node, dist=dist, detected=not is_leg_legal_only_radars(other, node, enemies))
            graph.add_edge(node, other, dist=dist, detected=not is_leg_legal_only_radars(node, other, enemies))


# Stage 3 methods


def is_leg_legal_only_no_entrances(start: Coordinate, end: Coordinate, enemies: List[Enemy]) -> bool:
    """Assert that the movement from start to end is legal, regarding only no-entrances

    :param start: start of the movement
    :param end: destination of the movement
    :param enemies: enemies to be considered
    :return: True if the leg is legal, False otherwise
    """
    return all(enemy.is_legal_leg(start, end) for enemy in enemies if not isinstance(enemy, Radar))


def is_leg_legal_only_radars(start: Coordinate, end: Coordinate, enemies: List[Enemy]) -> bool:
    """Assert that the movement from start to end is legal, regarding only radars

    :param start: start of the movement
    :param end: destination of the movement
    :param enemies: enemies to be considered
    :return: True if the leg is legal, False otherwise
    """
    return all(enemy.is_legal_leg(start, end) for enemy in enemies if isinstance(enemy, Radar))


def add_legal_edge(graph: nx.DiGraph, max_detection: float, quanta: float, start: Coordinate, end: Coordinate,
                   dist: float) -> None:
    """Add a legal edge to layers graph

    :param graph: layers graph
    :param max_detection: maximum allowed detection in path
    :param quanta: quanta of detection
    :param start: start of the edge
    :param end: end of the edge
    :param dist: distance between start and end
    :return: None
    """
    layer = 0.0
    # For every layer in the graph, add the edge inside the layer
    while layer <= max_detection:
        graph.add_edge(f'{start}_{layer}', f'{end}_{layer}', dist=dist)
        layer += quanta


def add_detected_edge(graph: nx.DiGraph, max_detection: float, quanta: float, start: Coordinate, end: Coordinate,
                      dist: float) -> None:
    """Add an illegal edge to layers graph

    :param graph: layers graph
    :param max_detection: maximum allowed detection in path
    :param quanta: quanta of detection
    :param start: start of the edge
    :param end: end of the edge
    :param dist: distance between start and end
    :return: None
    """

    # Compute edge detection
    detection = dist
    # If detection is not a multiple of quanta, round up
    if detection % quanta > 0:
        detection = (detection // quanta + 1) * quanta

    layer = 0.0
    # Add edge between every layer to next fitting layer
    while layer + detection <= max_detection:
        graph.add_edge(f'{start}_{layer}', f'{end}_{layer + detection}', dist=dist)
        layer += quanta


def add_target_edges(graph: nx.DiGraph, layers: List[float], target: Coordinate) -> None:
    """Add edges connecting between targets in different layers to the layers graph

    :param graph: layers graph
    :param layers: list of layers' detection values
    :param target: target node in initial graph
    :return: None
    """
    for layer, next_layer in zip(layers, layers[1:]):
        graph.add_edge(f'{target}_{layer}', f'{target}_{next_layer}', dist=0)


def build_layers_graph(graph: nx.DiGraph, source: Coordinate, target: Coordinate, max_detection_percentage=0.1,
                       quanta: float = 0.5) -> Tuple[nx.DiGraph, str, str]:
    """Build a layers graph over initial graph

    :param graph: initial graph to build a layers graph from
    :param source: source of the path search
    :param target: target of the path search
    :param max_detection_percentage: allowed distance of detection as a percentage of distance between source to target
    :param quanta: quanta of detection (every detection value will be rounded up to a multiplication of quanta
    :return: Layers graph, its source (in the first layer) and target (in the last layer)
    """

    # Compute value of maximal detection distance
    max_detection = source.distance_to(target) * max_detection_percentage

    # Initialize layers graph and add its nodes
    layers_graph = nx.DiGraph()
    # We have layers from 0 to max_detection with deltas of quanta between consecutive layers
    layers = [quanta * i for i in range(int(max_detection // quanta) + 1)]
    for layer in layers:
        layers_graph.add_nodes_from([f'{node}_{layer}' for node in graph.nodes])

    # For every edge in the initial graph, add it to the layers graph
    for edge, attributes in tqdm(graph.edges.items()):

        start, end = edge
        distance = attributes['dist']

        # If the edge is detected, we add it as a connection between layers
        if attributes['detected']:
            add_detected_edge(layers_graph, max_detection, quanta, start, end, distance)

        # If the edge is legal, we add it as an inside edge in every level
        else:
            add_legal_edge(layers_graph, max_detection, quanta, start, end, distance)

    # Add target connecting edges to allow transformation to last-layer target
    add_target_edges(layers_graph, layers, target)

    # Return layers graph and its source and target
    return layers_graph, f'{source}_0.0', f'{target}_{layers[-1]}'


def retrieve_path_from_layered_path(path: List[str]) -> List[Coordinate]:
    """Retrieve a path in the original graph, given a grpah in the layers graph

    :param path: path in the layers graph
    :return: equivalent path in the original graph
    """

    # Remove layer value from every node
    path = [s.split('_')[0] for s in path]

    # Create coordinates from the nodes
    path = [Coordinate.from_str(s) for s in path]

    # Remove every duplication of target in the end of the path
    while path[-1] == path[-2]:
        path = path[:-1]

    return path


# Navigator


def calculate_path(source: Coordinate, target: Coordinate, enemies: List[Enemy]) -> Tuple[List[Coordinate], nx.Graph]:
    """Calculates a path from source to target without any detection

    Note: The path must start at the source coordinate and end at the target coordinate!

    :param source: source coordinate of the spaceship
    :param target: target coordinate of the spaceship
    :param enemies: list of enemies along the way
    :return: list of calculated path way points and the graph constructed
    """

    # Initialize the graph
    print('-' * 30)
    print('Initializing graph')
    graph = nx.DiGraph()
    graph.add_node(source)
    graph.add_node(target)

    # Add corners of no-entrance zones to the graph
    print('Adding corners to graph')
    add_enemies_to_graph(graph, enemies)

    # For every pair of nodes, try to connect them
    for node1, node2 in combinations(graph.nodes, 2):
        # If the connection is not legal, skip the pair
        if not is_legal_leg(node1, node2, enemies):
            continue

        # Otherwise, add the edge to the graph
        dist = node1.distance_to(node2)
        graph.add_edge(node1, node2, dist=dist, detected=False)
        graph.add_edge(node2, node1, dist=dist, detected=False)

    # To deal with the added problem of radars, it is not enough to just circle the threat because there maybe a shorter
    # route that requires delicate maneuvering. The solution in this case is a "Probabalistic Roadmap" (PRM). This is a
    # group of motion planning algorithms. In the most basic case, we sample random coordinates in the graph and try to
    # connect them to all existing nodes within a given radius.
    print('Sampling inside radars')
    add_nodes_inside_radars(graph, enemies)

    # Build a layers graph
    print('Building layers graph')
    layers_graph, source, target = build_layers_graph(graph, source, target)

    # Try computing the shortest path
    try:
        print('Computing path')
        path = nx.shortest_path(layers_graph, source, target, weight='dist')
        path = retrieve_path_from_layered_path(path)
    # If not path exists, return an empty path
    except nx.NetworkXNoPath:
        path = []

    print('Returning path')
    return path, graph
