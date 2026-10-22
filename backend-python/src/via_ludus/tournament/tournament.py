import warnings
import itertools
from pathlib import Path

from tqdm.auto import tqdm

from ..board import (
	PlayerColor,
	UnionFindBoard as ViaLudusBoard,
)

from ..validation import (
	resolve_starting_player_color,
	resolve_board,
	validate_player_class,
)

from .matchup import play_matchup
from .results import TournamentResults


class RoundRobinTournament:
	def __init__(
		self,
		players,
		num_games_per_color,
		board=None,
		starting_color=None,
		results=None,
	):
		self._validate_players(players)
		self._validate_num_games_per_color(num_games_per_color)

		self._players = dict(players)
		self._board = resolve_board(board, default=ViaLudusBoard())
		self._starting_color = resolve_starting_player_color(starting_color)
		self._num_games_per_color = num_games_per_color

		self._results = TournamentResults(self._players.keys())
		if results is not None:
			self._validate_loaded_results(
				results,
				self._players,
				self._num_games_per_color,
			)

			self._results.add_tournament_data(results)

	@property
	def players(self):
		return self._players.copy()

	@property
	def num_games_per_color(self):
		return self._num_games_per_color

	@property
	def results(self):
		return self._results

	@property
	def expected_matchups(self):
		return itertools.product(self._players, repeat=2)

	@property
	def completed_matchups(self):
		return (
			(red_player, blue_player)
			for red_player, blue_player in self.expected_matchups
			if self.is_matchup_complete(red_player, blue_player)
		)

	@property
	def incomplete_matchups(self):
		return (
			(red_player, blue_player)
			for red_player, blue_player in self.expected_matchups
			if not self.is_matchup_complete(red_player, blue_player)
		)

	@property
	def total_expected_games(self):
		num_players = len(self._players)
		return num_players ** 2 * self._num_games_per_color

	@property
	def total_completed_games(self):
		return sum(
			self.get_matchup_games_played(red_player, blue_player)
			for red_player, blue_player in self.expected_matchups
		)

	@property
	def total_remaining_games(self):
		return self.total_expected_games - self.total_completed_games

	@property
	def is_complete(self):
		return self.total_remaining_games == 0

	def get_matchup_games_played(self, red_player, blue_player):
		return self._results.get_matchup_count(
			red_player,
			blue_player,
		)

	def get_matchup_games_remaining(self, red_player, blue_player):
		return max(
			0,
			self._num_games_per_color
			- self.get_matchup_games_played(red_player, blue_player),
		)

	def is_matchup_complete(self, red_player, blue_player):
		return self.get_matchup_games_remaining(red_player, blue_player) == 0

	def run(self, checkpoint_file=None):
		checkpoint_file = (
			Path(checkpoint_file)
			if checkpoint_file is not None
			else None
		)

		# Save the initial checkpoint.
		if checkpoint_file is not None:
			self._results.save(checkpoint_file)

		pending_matchups = [
			(red_name, blue_name, missing)
			for red_name, blue_name in self.expected_matchups
			if (
				missing := self.get_matchup_games_remaining(
					red_name,
					blue_name,
				)
			) > 0
		]

		total_games = sum(
			missing
			for _, _, missing in pending_matchups
		)

		with tqdm(
			total=total_games,
			desc="Round-Robin Tournament",
			unit="game",
		) as progress:
			for red_name, blue_name, missing in pending_matchups:
				matchup_results = play_matchup(
					red_player=self._players[red_name],
					blue_player=self._players[blue_name],
					num_games=missing,
					board=self._board,
					starting_color=self._starting_color,
					progress=progress,
					red_name=red_name,
					blue_name=blue_name,
				)

				self._results.add_tournament_data(matchup_results)

				if checkpoint_file is not None:
					self._results.save(checkpoint_file)

		return self._results

	@staticmethod
	def _validate_players(players):
		if not isinstance(players, dict) or not players:
			raise TypeError("players must be a non-empty dictionary")

		for name, player in players.items():
			if not isinstance(name, str) or not name:
				raise ValueError(
					"Every player name must be a non-empty string"
				)

			validate_player_class(player)

	@staticmethod
	def _validate_num_games_per_color(num_games_per_color):
		if (
			not isinstance(num_games_per_color, int)
			or isinstance(num_games_per_color, bool)
			or num_games_per_color < 1
		):
			raise ValueError(
				"num_games_per_color must be a positive integer"
			)

	@staticmethod
	def _validate_loaded_results(results, players, num_games_per_color):
		unknown_players = sorted(set(results.players) - set(players))

		if unknown_players:
			warnings.warn(
				"Loaded tournament results contain players not provided "
				"to this tournament: "
				+ ", ".join(unknown_players),
				UserWarning,
				stacklevel=2,
			)

		excess_matchups = []

		for (
			red_player,
			blue_player,
			matchup_results,
			moves,
			deterministic,
		) in results:
			num_games = len(matchup_results)

			if num_games > num_games_per_color:
				excess_matchups.append(
					(red_player, blue_player, num_games)
				)

		if excess_matchups:
			details = "\n".join(
				f"\t{red_player} (red) vs {blue_player} (blue): "
				f"{num_games} games"
				for red_player, blue_player, num_games in excess_matchups
			)

			warnings.warn(
				"The following matchups have more games than the "
				f"configured limit of {num_games_per_color}:\n{details}",
				UserWarning,
				stacklevel=2,
			)

