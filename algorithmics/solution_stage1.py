from itertools import combinations
from typing import List, Tuple

import networkx as nx

from algorithmics.enemy.asteroids_zone import AsteroidsZone
from algorithmics.enemy.enemy import Enemy
from algorithmics.enemy.observation_post import ObservationPost
from algorithmics.utils.coordinate import Coordinate


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
        if isinstance(enemy, ObservationPost):
            graph.add_nodes_from(enemy.approximate_boundary())


def is_legal_leg(start: Coordinate, end: Coordinate, enemies: List[Enemy]) -> bool:
    """Assert that the movement from start to end is legal, regarding all enemies

    :param start: start of the movement
    :param end: destination of the movement
    :param enemies: enemies to be considered
    :return: True if the leg is legal, False otherwise
    """
    return all(enemy.is_legal_leg(start, end) for enemy in enemies)


def calculate_path(source: Coordinate, target: Coordinate, enemies: List[Enemy]) -> Tuple[List[Coordinate], nx.Graph]:
    """Calculates a path from source to target without any detection

    Note: The path must start at the source coordinate and end at the target coordinate!

    :param source: source coordinate of the spaceship
    :param target: target coordinate of the spaceship
    :param enemies: list of enemies along the way
    :return: list of calculated pathway points and the graph constructed
    """

    # We use a method called "Visibility Graph" in order to solve the problem.
    #
    # Using this method we build a graph containing all the corners of the no-entrance zones (where circles are
    # approximated as polygons) and connect with an edge every pair of nodes that are legal (i.e. have no detection).
    # Lastly, we use a shortest-path algorithm (such as dijkstra) to find the shortest path.

    # Initialize the graph
    graph = nx.Graph()
    graph.add_node(source)
    graph.add_node(target)

    # Add corners of no-entrance zones to the graph
    add_enemies_to_graph(graph, enemies)

    # For every pair of nodes, try to connect them
    for node1, node2 in combinations(graph.nodes, 2):
        # If the connection is legal, add the edge to the graph
        if is_legal_leg(node1, node2, enemies):
            graph.add_edge(node1, node2, dist=node1.distance_to(node2))

    # Try computing the shortest path
    try:
        print('Computing path')
        path = nx.shortest_path(graph, source, target, weight='dist')
    # If no such path exists, return an empty path
    except nx.NetworkXNoPath:
        path = []

    print('Returning path')
    return path, graph
