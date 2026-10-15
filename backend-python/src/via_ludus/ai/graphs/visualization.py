import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from ...utils import with_ax
from ...board import PlayerColor

from .graph import (
	Endpoint,
	board_to_player_graph,
	board_to_move_graph,
)


@with_ax
def plot_graph(
	graph,
	color,
	rows,
	cols,
	edge_labels="cost",
	ax=None,
):
	if not isinstance(color, PlayerColor):
		raise ValueError(f"Invalid player color: {color}")

	pos = {}

	grid_nodes = [
		node
		for node in graph
		if isinstance(node, tuple)
		and len(node) == 2
	]

	for row, col in grid_nodes:
		pos[(row, col)] = (col, row)

	if color == PlayerColor.RED:
		pos[Endpoint.SOURCE] = (
			(cols - 1) / 2,
			-1,
		)

		pos[Endpoint.TARGET] = (
			(cols - 1) / 2,
			rows,
		)

	elif color == PlayerColor.BLUE:
		pos[Endpoint.SOURCE] = (
			-1,
			(rows - 1) / 2,
		)

		pos[Endpoint.TARGET] = (
			cols,
			(rows - 1) / 2,
		)

	nx.draw_networkx_edges(
		graph,
		pos=pos,
		ax=ax,
	)

	node_edgecolors = [
		"red"
		if graph.nodes[node]["cell"] == PlayerColor.RED.cell
		else "blue"
		if graph.nodes[node]["cell"] == PlayerColor.BLUE.cell
		else "black"
		for node in grid_nodes
	]

	nx.draw_networkx_nodes(
		graph,
		pos=pos,
		nodelist=grid_nodes,
		ax=ax,
		node_color="white",
		edgecolors=node_edgecolors,
		node_size=500,
	)

	endpoint_nodes = [
		node
		for node in (
			Endpoint.SOURCE,
			Endpoint.TARGET,
		)
		if node in graph
	]

	nx.draw_networkx_nodes(
		graph,
		pos=pos,
		nodelist=endpoint_nodes,
		ax=ax,
		node_color=color.cell.color,
		edgecolors=color.cell.color,
		node_size=700,
	)

	labels = {
		node: f"{node[0]},{node[1]}"
		for node in grid_nodes
	}

	labels.update({
		Endpoint.SOURCE: str(Endpoint.SOURCE),
		Endpoint.TARGET: str(Endpoint.TARGET),
	})

	nx.draw_networkx_labels(
		graph,
		pos=pos,
		labels=labels,
		ax=ax,
		font_color="black",
		font_size=10,
	)

	nx.draw_networkx_edge_labels(
		graph,
		pos=pos,
		edge_labels=nx.get_edge_attributes(
			graph,
			edge_labels,
		),
		ax=ax,
		rotate=False,
	)

	ax.set_aspect("equal")
	ax.invert_yaxis()


@with_ax
def plot_player_graph(
	board,
	color,
	edge_labels="cost",
	ax=None,
):
	if not isinstance(color, PlayerColor):
		raise ValueError(f"Invalid player color: {color}")

	graph = board_to_player_graph(board, color)

	plot_graph(
		graph,
		color,
		board.rows,
		board.cols,
		edge_labels=edge_labels,
		ax=ax,
	)


@with_ax
def plot_move_graph(
	board,
	color,
	edge_labels="cost",
	ax=None,
):
	if not isinstance(color, PlayerColor):
		raise ValueError(f"Invalid player color: {color}")

	graph = board_to_move_graph(board, color)

	plot_graph(
		graph,
		color,
		board.rows,
		board.cols,
		edge_labels=edge_labels,
		ax=ax,
	)

