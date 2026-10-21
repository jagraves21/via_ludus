from itertools import combinations
from math import exp

import networkx as nx

from .....board import (
	Cell,
	validate_player_color,
)

from .constants import Endpoint
from .utils import (
	neighbors,
	edge_cells,
)


def _edge_attributes(weight):
	connection_strength = 1 / (1 + weight)

	return {
		"weight": weight,
		"traversal_cost": weight,
		"connection_strength": connection_strength,
		"traversability": exp(-weight),
		"resistance": weight + 1e-6,
		"availability": connection_strength,
		"penalty": weight,
	}


def board_to_player_graph(
	board,
	color,
	directed=False,
	remove_unreachable=False,
):
	validate_player_color(color)

	graph = nx.DiGraph() if directed else nx.Graph()
	cell = color.cell

	# add empty cells and cells belonging to the player
	for row, col in board.empty_cells | board.positions_of(cell):
		graph.add_node(
			(row, col),
			cell=board.get(row, col),
		)

	# connect adjacent usable cells
	for vertex in list(graph.nodes):
		for neighbor in neighbors(board, *vertex):
			if neighbor not in graph:
				continue

			# undirected edges are processed once
			if not directed and vertex >= neighbor:
				continue

			vertex_cell = graph.nodes[vertex]["cell"]
			neighbor_cell = graph.nodes[neighbor]["cell"]

			if directed:
				# entering a white cell costs 1
				# entering an own cell costs 0
				graph.add_edge(
					vertex,
					neighbor,
					**_edge_attributes(
						int(neighbor_cell == Cell.WHITE)
					),
				)
				graph.add_edge(
					neighbor,
					vertex,
					**_edge_attributes(
						int(vertex_cell == Cell.WHITE)
					),
				)
			else:
				# an undirected connection costs 1 if either endpoint is white
				weight = int(
					vertex_cell == Cell.WHITE
					or neighbor_cell == Cell.WHITE
				)

				graph.add_edge(
					vertex,
					neighbor,
					**_edge_attributes(weight),
				)

	# add source and target endpoints
	graph.add_node(Endpoint.SOURCE, cell=cell)
	graph.add_node(Endpoint.TARGET, cell=cell)

	for endpoint in (Endpoint.SOURCE, Endpoint.TARGET):
		for row, col in edge_cells(board, color, endpoint):
			vertex = (row, col)

			if vertex not in graph:
				continue

			graph.add_edge(
				endpoint,
				vertex,
				**_edge_attributes(0),
			)

			if directed:
				graph.add_edge(
					vertex,
					endpoint,
					**_edge_attributes(0),
				)

	if remove_unreachable:
		if directed:
			reachable_nodes = (
				nx.descendants(graph, Endpoint.SOURCE)
				| nx.descendants(graph, Endpoint.TARGET)
				| {Endpoint.SOURCE, Endpoint.TARGET}
			)
		else:
			reachable_nodes = (
				nx.node_connected_component(graph, Endpoint.SOURCE)
				| nx.node_connected_component(graph, Endpoint.TARGET)
			)

		graph.remove_nodes_from(
			set(graph.nodes) - reachable_nodes
		)

	return graph


def board_to_move_graph(board, color, directed=False):
	graph = board_to_player_graph(
		board,
		color,
		directed=directed,
		remove_unreachable=True,
	)

	shortest_paths = dict(
		nx.all_pairs_dijkstra_path_length(
			graph,
			weight="weight",
		)
	)

	white_nodes = {
		node
		for node, data in graph.nodes(data=True)
		if data["cell"] == Cell.WHITE
	}

	move_graph = nx.DiGraph() if directed else nx.Graph()

	# add source and target endpoints
	for endpoint in (Endpoint.SOURCE, Endpoint.TARGET):
		move_graph.add_node(
			endpoint,
			**graph.nodes[endpoint],
		)

	# add all white nodes
	move_graph.add_nodes_from(
		(
			node,
			graph.nodes[node],
		)
		for node in white_nodes
	)

	# connect candidate moves separated by a path of
	# weight 1 in the player graph
	for u, v in combinations(white_nodes, 2):
		distance_uv = shortest_paths[u].get(v)
		distance_vu = shortest_paths[v].get(u)

		if distance_uv == 1:
			move_graph.add_edge(
				u,
				v,
				**_edge_attributes(1),
			)

		if directed and distance_vu == 1:
			move_graph.add_edge(
				v,
				u,
				**_edge_attributes(1),
			)

	# connect endpoints to white nodes with a shortest path
	# of weight 1 in the player graph
	for endpoint in (Endpoint.SOURCE, Endpoint.TARGET):
		for node in white_nodes:
			if shortest_paths[endpoint].get(node) in (0, 1):
				move_graph.add_edge(
					endpoint,
					node,
					**_edge_attributes(1),
				)

			if (
				directed
				and shortest_paths[node].get(endpoint) in (0, 1)
			):
				move_graph.add_edge(
					node,
					endpoint,
					**_edge_attributes(1),
				)

	return move_graph

