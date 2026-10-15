from enum import StrEnum
from itertools import combinations

import networkx as nx
from networkx.algorithms.connectivity import minimum_st_node_cut

from ...board import (
	Cell,
	PlayerColor,
)


class Endpoint(StrEnum):
	SOURCE = "S"
	TARGET = "T"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"Endpoint.{self.name}"


def _edge_attributes(weight):
	return {
		"weight": weight,
		"cost": weight,
		"strength": 1 / (weight + 1),
	}


def board_to_player_graph(board, color):
	if not isinstance(color, PlayerColor):
		raise ValueError(f"Invalid player color: {color}")

	cell = color.cell
	graph = nx.Graph()

	# add cells that the player can use
	for row in range(board.rows):
		for col in range(board.cols):
			node_cell = board.get(row, col)

			if node_cell in (cell, Cell.WHITE):
				graph.add_node(
					(row, col),
					cell=node_cell,
				)

	# connect neighboring cells
	directions = (
		(-1, 0),
		(1, 0),
		(0, -1),
		(0, 1),
	)

	for row, col in graph.nodes:
		for row_offset, col_offset in directions:
			new_row = row + row_offset
			new_col = col + col_offset

			if not (
				0 <= new_row < board.rows
				and 0 <= new_col < board.cols
			):
				continue

			neighbor = (new_row, new_col)

			if neighbor not in graph:
				continue

			if (
				board.get(row, col) == cell
				and board.get(new_row, new_col) == cell
			):
				weight = 0
			else:
				weight = 1

			graph.add_edge(
				(row, col),
				neighbor,
				**_edge_attributes(weight),
			)

	# add source and target
	graph.add_node(
		Endpoint.SOURCE,
		cell=cell,
	)
	graph.add_node(
		Endpoint.TARGET,
		cell=cell,
	)

	if color == PlayerColor.RED:
		for col in range(board.cols):
			if (0, col) in graph:
				graph.add_edge(
					Endpoint.SOURCE,
					(0, col),
					**_edge_attributes(0),
				)

			if (board.rows - 1, col) in graph:
				graph.add_edge(
					Endpoint.TARGET,
					(board.rows - 1, col),
					**_edge_attributes(0),
				)

	elif color == PlayerColor.BLUE:
		for row in range(board.rows):
			if (row, 0) in graph:
				graph.add_edge(
					Endpoint.SOURCE,
					(row, 0),
					**_edge_attributes(0),
				)

			if (row, board.cols - 1) in graph:
				graph.add_edge(
					Endpoint.TARGET,
					(row, board.cols - 1),
					**_edge_attributes(0),
				)

	return graph


def board_to_move_graph(board, color):
	graph = board_to_player_graph(
		board,
		color,
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

	reachable_white_nodes = {
		node
		for node in white_nodes
		if (
			node in shortest_paths[Endpoint.SOURCE]
			or node in shortest_paths[Endpoint.TARGET]
		)
	}

	move_graph = nx.Graph()

	move_graph.add_node(
		Endpoint.SOURCE,
		**graph.nodes[Endpoint.SOURCE],
	)

	move_graph.add_node(
		Endpoint.TARGET,
		**graph.nodes[Endpoint.TARGET],
	)

	move_graph.add_nodes_from(
		(
			node,
			graph.nodes[node],
		)
		for node in reachable_white_nodes
	)

	for u in [Endpoint.SOURCE, Endpoint.TARGET]:
		for v, distance in shortest_paths[u].items():
			if distance == 1:
				move_graph.add_edge(
					u,
					v,
					**_edge_attributes(distance),
				)

	for u, v in combinations(
		reachable_white_nodes,
		2,
	):
		distance = shortest_paths[u].get(v)

		if distance in (1, 2):
			move_graph.add_edge(
				u,
				v,
				**_edge_attributes(distance),
			)

	return move_graph


def minimum_endpoint_cut(graph):
	return minimum_st_node_cut(
		graph,
		Endpoint.SOURCE,
		Endpoint.TARGET,
	)


def all_minimum_endpoint_cuts(graph):
	k = nx.node_connectivity(
		graph,
		Endpoint.SOURCE,
		Endpoint.TARGET,
	)

	nodes = set(graph) - {
		Endpoint.SOURCE,
		Endpoint.TARGET,
	}

	for cut in combinations(nodes, k):
		cut = set(cut)

		reduced_graph = graph.copy()
		reduced_graph.remove_nodes_from(cut)

		if not nx.has_path(
			reduced_graph,
			Endpoint.SOURCE,
			Endpoint.TARGET,
		):
			yield cut


