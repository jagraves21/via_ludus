from ..board import PlayerColor
from ..validation import (
	resolve_starting_player_color,
	resolve_board,
	is_scoring_player,
	validate_player,
	validate_player_class,
)


class Game:
	def __init__(
		self,
		red_player,
		blue_player,
		board=None,
		starting_color=None,
	):
		validate_player_class(red_player)
		validate_player_class(blue_player)

		self._player_classes = {
			PlayerColor.RED: red_player,
			PlayerColor.BLUE: blue_player,
		}
		self._initial_board = resolve_board(board).copy()
		self._starting_color = resolve_starting_player_color(
			starting_color
		)

		self.reset()

	@property
	def board(self):
		return self._board.copy()

	@property
	def players(self):
		return self._players.copy()

	@property
	def starting_color(self):
		return self._starting_color

	@property
	def current_color(self):
		return self._current_color

	@property
	def starting_player(self):
		return self._players[self._starting_color]

	@property
	def current_player(self):
		return self._players[self.current_color]

	@property
	def available_moves(self):
		return self._board.available

	@property
	def moves(self):
		return tuple(self._moves)

	@property
	def move_count(self):
		return len(self._moves)

	@property
	def winner(self):
		return self._winner

	@property
	def is_game_over(self):
		return self.winner is not None

	@property
	def is_deterministic(self):
		return all(
			player.is_deterministic
			for player in self._players.values()
		)

	def _validate_players(self):
		for color, player in self._players.items():
			validate_player(player)

			if player.color != color:
				raise ValueError(
					f"Expected a {color.name.lower()} player, "
					f"got {player.color.name.lower()}"
				)

	def _create_players(self):
		return {
			color: player_class(color)
			for color, player_class in self._player_classes.items()
		}

	def reset(self):
		self._board = self._initial_board.copy()
		self._players = self._create_players()
		self._validate_players()
		self._current_color = self._starting_color
		self._moves = []
		self._winner = self._board.winner

	def make_move(self, move):
		if self.is_game_over:
			raise ValueError("Game is already over")

		if move not in self.available_moves:
			raise ValueError(f"Invalid move: {move}")

		color = self.current_color
		row, col = move

		self._board.set(row, col, color.cell)
		self._moves.append(move)
		self._winner = self._board.winner

		if not self.is_game_over:
			self._current_color = color.opponent

		return move

	def make_player_move(self):
		if self.is_game_over:
			raise ValueError("Game is already over")

		# use the property so the player can't change the real board
		move = self.current_player.choose_move(self.board)
		return self.make_move(move)

	def make_player_move_with_determinism(self):
		if self.is_game_over:
			raise ValueError("Game is already over")

		# trust the player's explicit, whole-policy contract
		if self.current_player.is_deterministic:
			move = self.current_player.choose_move(self.board)
			move_is_deterministic = True
		elif is_scoring_player(self.current_player):
			move, move_is_deterministic = (
				self.current_player.choose_move_with_determinism(
					self.board
				)
			)
		else:
			# no contract or per-move assessment is available
			move = self.current_player.choose_move(self.board)
			move_is_deterministic = False

		move = self.make_move(move)
		return move, move_is_deterministic

	def play(self):
		while not self.is_game_over:
			self.make_player_move()

		return self.winner

	def play_with_determinism(self):
		was_deterministic = True

		while not self.is_game_over:
			if not was_deterministic:
				self.make_player_move()
				continue

			_, move_is_deterministic = (
				self.make_player_move_with_determinism()
			)

			if not move_is_deterministic:
				was_deterministic = False

		return self.winner, was_deterministic

	def __str__(self):
		return (
			f"Game("
			f"current_player={self.current_player}, "
			f"current_color={self.current_color}, "
			f"moves={self.move_count}, "
			f"winner={self.winner}"
			f")"
		)

	def __repr__(self):
		return (
			f"Game("
			f"board={self._board!r}, "
			f"current_player={self.current_player!r}, "
			f"current_color={self.current_color}, "
			f"moves={self.move_count}, "
			f"winner={self.winner!r}"
			f")"
		)

