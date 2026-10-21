from .graph_utils import (
	board_to_move_graph,
	board_to_player_graph,
)


class UndirectedPlayerGraphMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_player_graph(
				board,
				color,
				directed=False,
				remove_unreachable=False,
			)

		return build_graph


class UndirectedPlayerGraphFilteredMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_player_graph(
				board,
				color,
				directed=False,
				remove_unreachable=True,
			)

		return build_graph


class DirectedPlayerGraphMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_player_graph(
				board,
				color,
				directed=True,
				remove_unreachable=False,
			)

		return build_graph


class DirectedPlayerGraphFilteredMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_player_graph(
				board,
				color,
				directed=True,
				remove_unreachable=True,
			)

		return build_graph


class UndirectedMoveGraphMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_move_graph(
				board,
				color,
				directed=False,
			)

		return build_graph


class DirectedMoveGraphMixin:
	@property
	def graph_builder(self):
		def build_graph(board, color):
			return board_to_move_graph(
				board,
				color,
				directed=True,
			)

		return build_graph

