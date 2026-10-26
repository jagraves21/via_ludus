from abc import ABC, abstractmethod

from .graph_utils import (
	board_to_move_graph,
	board_to_player_graph,
)


class GraphBuilderMixin(ABC):
	@property
	def graph_builder(self):
		return self.build_graph

	@abstractmethod
	def build_graph(self, board, color):
		pass


# Undirected Graphs

class UndirectedPlayerGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color,
			directed=False,
			remove_unreachable=False,
		)


class UndirectedMoveGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_move_graph(
			board,
			color,
			directed=False,
		)


# Undirected Filtered Graphs

class UndirectedPlayerGraphFilteredMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color,
			directed=False,
			remove_unreachable=True,
		)


# Directed Graphs

class DirectedPlayerGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color,
			directed=True,
			remove_unreachable=False,
		)


class DirectedMoveGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_move_graph(
			board,
			color,
			directed=True,
		)


# Directed Filtered Graphs

class DirectedPlayerGraphFilteredMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color,
			directed=True,
			remove_unreachable=True,
		)


# Opponent Graphs

class UndirectedOpponentPlayerGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color.opponent,
			directed=False,
			remove_unreachable=False,
		)


class UndirectedOpponentPlayerGraphFilteredMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color.opponent,
			directed=False,
			remove_unreachable=True,
		)


class UndirectedOpponentMoveGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_move_graph(
			board,
			color.opponent,
			directed=False,
		)


class DirectedOpponentPlayerGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color.opponent,
			directed=True,
			remove_unreachable=False,
		)


class DirectedOpponentPlayerGraphFilteredMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_player_graph(
			board,
			color.opponent,
			directed=True,
			remove_unreachable=True,
		)


class DirectedOpponentMoveGraphMixin(GraphBuilderMixin):
	def build_graph(self, board, color):
		return board_to_move_graph(
			board,
			color.opponent,
			directed=True,
		)


# Player Graph Pairs

class PlayerGraphPairMixin(GraphBuilderMixin):
	@property
	def graph_builder(self):
		return self.build_graphs

	def build_graphs(self, board, color):
		return (
			self.build_graph(board, color),
			self.build_graph(board, color.opponent),
		)


class UndirectedPlayerGraphPairMixin(
	PlayerGraphPairMixin,
	UndirectedPlayerGraphMixin,
):
	pass


class UndirectedPlayerGraphFilteredPairMixin(
	PlayerGraphPairMixin,
	UndirectedPlayerGraphFilteredMixin,
):
	pass


class DirectedPlayerGraphPairMixin(
	PlayerGraphPairMixin,
	DirectedPlayerGraphMixin,
):
	pass


class DirectedPlayerGraphFilteredPairMixin(
	PlayerGraphPairMixin,
	DirectedPlayerGraphFilteredMixin,
):
	pass


class UndirectedMoveGraphPairMixin(
	PlayerGraphPairMixin,
	UndirectedMoveGraphMixin,
):
	pass


class DirectedMoveGraphPairMixin(
	PlayerGraphPairMixin,
	DirectedMoveGraphMixin,
):
	pass


# Opponent-First Graph Pairs

class OpponentFirstPlayerGraphPairMixin(PlayerGraphPairMixin):
	def build_graphs(self, board, color):
		return (
			self.build_graph(board, color.opponent),
			self.build_graph(board, color),
		)


class UndirectedOpponentPlayerGraphPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	UndirectedPlayerGraphMixin,
):
	pass


class UndirectedOpponentPlayerGraphFilteredPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	UndirectedPlayerGraphFilteredMixin,
):
	pass


class DirectedOpponentPlayerGraphPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	DirectedPlayerGraphMixin,
):
	pass


class DirectedOpponentPlayerGraphFilteredPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	DirectedPlayerGraphFilteredMixin,
):
	pass


class UndirectedOpponentMoveGraphPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	UndirectedMoveGraphMixin,
):
	pass


class DirectedOpponentMoveGraphPairMixin(
	OpponentFirstPlayerGraphPairMixin,
	DirectedMoveGraphMixin,
):
	pass

