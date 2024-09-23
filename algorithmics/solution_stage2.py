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

            # Connect edge in both directions
            dist = node.distance_to(other)
            if is_legal_leg(other, node, enemies):
                graph.add_edge(other, node, dist=dist)
            if is_legal_leg(node, other, enemies):
                graph.add_edge(node, other, dist=dist)


# Navigator


def calculate_path(source: Coordinate, target: Coordinate, enemies: List[Enemy]) -> Tuple[List[Coordinate], nx.Graph]:
    """Calculates a path from source to target without any detection

    Note: The path must start at the source coordinate and end at the target coordinate!

    :param source: source coordinate of the spaceship
    :param target: target coordinate of the spaceship
    :param enemies: list of enemies along the way
    :return: list of calculated pathway points and the graph constructed
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
        # If the connection is legal, add the edge to the graph
        if is_legal_leg(node1, node2, enemies):
            dist = node1.distance_to(node2)
            graph.add_edge(node1, node2, dist=dist)
            graph.add_edge(node2, node1, dist=dist)

    # To deal with the added problem of radars, it is not enough to just circle the threat because there may be a
    # shorter route that requires delicate maneuvering. The solution in this case is a "Probabilistic Roadmap" (PRM),
    # which is a group of motion planning algorithms. In the most basic case, we sample random coordinates in the graph
    # and try to connect them to all existing nodes within a given radius.
    print('Sampling inside radars')
    add_nodes_inside_radars(graph, enemies)

    # Try computing the shortest path
    try:
        print('Computing path')
        path = nx.shortest_path(graph, source, target, weight='dist')
    # If not path exists, return an empty path
    except nx.NetworkXNoPath:
        path = []

    print('Returning path')
    return path, graph
