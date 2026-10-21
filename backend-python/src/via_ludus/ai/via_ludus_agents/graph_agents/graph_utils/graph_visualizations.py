import matplotlib.pyplot as plt
import networkx as nx

from .....visualizations import with_ax

from .....board import (
	PlayerColor,
	validate_player_color,
)

from .constants import Endpoint

from .graph import (
	board_to_player_graph,
	board_to_move_graph,
)


def _edge_label_position(source_pos, target_pos, rad):
	x1, y1 = source_pos
	x2, y2 = target_pos

	dx = x2 - x1
	dy = y2 - y1
	length = (dx ** 2 + dy ** 2) ** 0.5

	if length == 0:
		return (
			(x1 + x2) / 2,
			(y1 + y2) / 2,
		)

	mid_x = (x1 + x2) / 2
	mid_y = (y1 + y2) / 2

	# Offset the label away from the straight line,
	# onto the outside of the curved edge.
	offset = rad * length * 0.8

	return (
		mid_x - dy / length * offset,
		mid_y + dx / length * offset,
	)


@with_ax
def plot_graph(
	graph,
	color,
	rows,
	cols,
	ax=None,
):
	validate_player_color(color)

	pos = {}

	grid_nodes = [
		node
		for node in graph
		if isinstance(node, tuple) and len(node) == 2
	]

	# Pin grid vertices to their board locations.
	for row, col in grid_nodes:
		pos[(row, col)] = (col, row)

	# Position source and target endpoints.
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

	# Draw edges and label them with weight only.
	if graph.is_directed():
		for source, target in graph.edges:
			has_reverse_edge = graph.has_edge(target, source)
			rad = 0.18 if has_reverse_edge else 0.0

			nx.draw_networkx_edges(
				graph,
				pos=pos,
				edgelist=[(source, target)],
				ax=ax,
				arrows=True,
				arrowstyle="-|>",
				arrowsize=18,
				width=1.5,
				connectionstyle=f"arc3,rad={rad}",
				min_source_margin=8,
				min_target_margin=12,
			)

			if "weight" in graph[source][target]:
				label = graph[source][target]["weight"]

				label_pos = _edge_label_position(
					pos[source],
					pos[target],
					rad,
				)

				ax.text(
					*label_pos,
					str(label),
					fontsize=9,
					color="black",
					horizontalalignment="center",
					verticalalignment="center",
					bbox={
						"facecolor": "white",
						"edgecolor": "none",
						"alpha": 0.8,
						"pad": 1,
					},
					zorder=5,
				)
	else:
		nx.draw_networkx_edges(
			graph,
			pos=pos,
			ax=ax,
			width=1.5,
		)

		nx.draw_networkx_edge_labels(
			graph,
			pos=pos,
			edge_labels=nx.get_edge_attributes(
				graph,
				"weight",
			),
			ax=ax,
			rotate=False,
			font_size=9,
			bbox={
				"facecolor": "white",
				"edgecolor": "none",
				"alpha": 0.8,
				"pad": 1,
			},
		)

	# Color grid-node borders according to cell ownership.
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

	# Draw source and target endpoints.
	endpoint_nodes = [
		node
		for node in (Endpoint.SOURCE, Endpoint.TARGET)
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

	ax.set_aspect("equal")
	ax.invert_yaxis()


@with_ax
def plot_player_graph(
	board,
	color,
	directed=False,
	remove_unreachable=False,
	ax=None,
):
	validate_player_color(color)

	graph = board_to_player_graph(
		board,
		color,
		directed=directed,
		remove_unreachable=remove_unreachable,
	)

	plot_graph(
		graph,
		color,
		board.rows,
		board.cols,
		ax=ax,
	)


@with_ax
def plot_move_graph(
	board,
	color,
	directed=False,
	ax=None,
):
	validate_player_color(color)

	graph = board_to_move_graph(board, color, directed=directed)

	plot_graph(
		graph,
		color,
		board.rows,
		board.cols,
		ax=ax,
	)

