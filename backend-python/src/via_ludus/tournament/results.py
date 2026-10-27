from collections import defaultdict
import copy
import gzip
import itertools
import json
from pathlib import Path
import warnings

import numpy as np

from ..utils import requires_extra

from ..visualizations import with_ax
from ..board import (
	PlayerColor,
	validate_player_color,
)


class TournamentResults:
	def __init__(self, players):
		self._players = list(dict.fromkeys(players))
		self._results = defaultdict(lambda: {
			"results": [],
			"moves": [],
			"deterministic": [],
		})

	@property
	def players(self):
		return tuple(self._players)

	@property
	def total_games(self):
		return sum(
			len(matchup["results"])
			for matchup in self._results.values()
		)

	@property
	def deterministic_games(self):
		return sum(
			sum(matchup["deterministic"])
			for matchup in self._results.values()
		)

	@property
	def deterministic_game_rate(self):
		return (
			self.deterministic_games / self.total_games
			if self.total_games
			else 0.0
		)

	def add_matchup_result(
		self,
		red_player,
		blue_player,
		result,
		move,
		deterministic,
	):
		self._validate_players(red_player, blue_player)
		self._validate_result(result, move)
		self._validate_deterministic(deterministic)

		self.add_matchup_data(
			red_player,
			blue_player,
			[result],
			[move],
			[deterministic],
		)

	def add_matchup_data(
		self,
		red_player,
		blue_player,
		results,
		moves,
		deterministic,
	):
		self._validate_players(red_player, blue_player)
		self._validate_results(results, moves)
		self._validate_deterministic_data(
			results,
			moves,
			deterministic,
		)

		matchup = self._results[(red_player, blue_player)]
		matchup["results"].extend(results)
		matchup["moves"].extend(moves)
		matchup["deterministic"].extend(deterministic)

	def add_tournament_data(self, other):
		if not isinstance(other, TournamentResults):
			raise TypeError(
				"other must be a TournamentResults instance"
			)

		for player in other._players:
			if player not in self._players:
				self._players.append(player)

		for (red_player, blue_player), matchup in other._results.items():
			self.add_matchup_data(
				red_player,
				blue_player,
				matchup["results"],
				matchup["moves"],
				matchup["deterministic"],
			)

	def get_matchup_results(self, red_player, blue_player):
		return self.get_matchup_data(red_player, blue_player)["results"]

	def get_matchup_moves(self, red_player, blue_player):
		return self.get_matchup_data(red_player, blue_player)["moves"]

	def get_matchup_determinism(self, red_player, blue_player):
		return self.get_matchup_data(
			red_player,
			blue_player,
		)["deterministic"]

	def get_matchup_data(self, red_player, blue_player):
		self._validate_players(red_player, blue_player)

		matchup = self._results.get((red_player, blue_player))

		if matchup is None:
			return {
				"results": (),
				"moves": (),
				"deterministic": (),
			}

		return {
			"results": tuple(matchup["results"]),
			"moves": tuple(matchup["moves"]),
			"deterministic": tuple(matchup["deterministic"]),
		}

	def get_matchup_count(self, red_player, blue_player):
		return len(
			self.get_matchup_results(red_player, blue_player)
		)

	def summary(self):
		data = []

		for player in self._players:
			red_matchups = [
				matchup
				for (red_player, _), matchup in self._results.items()
				if red_player == player
			]
			blue_matchups = [
				matchup
				for (red_player, blue_player), matchup
				in self._results.items()
				if blue_player == player and red_player != player
			]

			red_results = list(itertools.chain.from_iterable(
				matchup["results"] for matchup in red_matchups
			))
			blue_results = list(itertools.chain.from_iterable(
				matchup["results"] for matchup in blue_matchups
			))

			red_deterministic = sum(
				sum(matchup["deterministic"])
				for matchup in red_matchups
			)
			blue_deterministic = sum(
				sum(matchup["deterministic"])
				for matchup in blue_matchups
			)

			red_games = len(red_results)
			blue_games = len(blue_results)
			total_games = red_games + blue_games

			red_wins = sum(
				result == PlayerColor.RED
				for result in red_results
			)
			blue_wins = sum(
				result == PlayerColor.BLUE
				for result in blue_results
			)
			total_wins = red_wins + blue_wins
			total_deterministic = (
				red_deterministic + blue_deterministic
			)

			data.append({
				"player": player,
				"total_games": total_games,
				"total_wins": total_wins,
				"total_win_rate": (
					total_wins / total_games if total_games else 0.0
				),
				"deterministic_games": total_deterministic,
				"deterministic_game_rate": (
					total_deterministic / total_games
					if total_games else 0.0
				),
				"red_games": red_games,
				"red_wins": red_wins,
				"red_win_rate": (
					red_wins / red_games if red_games else 0.0
				),
				"red_deterministic_games": red_deterministic,
				"blue_games": blue_games,
				"blue_wins": blue_wins,
				"blue_win_rate": (
					blue_wins / blue_games if blue_games else 0.0
				),
				"blue_deterministic_games": blue_deterministic,
			})

		return sorted(
			data,
			key=lambda row: row["total_win_rate"],
			reverse=True,
		)

	@requires_extra("pandas", "dataframe")
	def summary_df(self):
		import pandas as pd

		columns = [
			"player",
			"total_games",
			"total_wins",
			"total_win_rate",
			"deterministic_games",
			"deterministic_game_rate",
			"red_games",
			"red_wins",
			"red_win_rate",
			"red_deterministic_games",
			"blue_games",
			"blue_wins",
			"blue_win_rate",
			"blue_deterministic_games",
		]

		return pd.DataFrame(self.summary(), columns=columns)

	def head_to_head_summary(self):
		data = []

		for (red_player, blue_player), matchup in self._results.items():
			results = matchup["results"]
			moves = matchup["moves"]
			deterministic = matchup["deterministic"]
			num_games = len(results)

			red_wins = sum(
				result == PlayerColor.RED for result in results
			)
			blue_wins = sum(
				result == PlayerColor.BLUE for result in results
			)
			deterministic_games = sum(deterministic)

			red_moves = [
				move
				for result, move in zip(results, moves)
				if result == PlayerColor.RED
			]
			blue_moves = [
				move
				for result, move in zip(results, moves)
				if result == PlayerColor.BLUE
			]

			data.append({
				"red_player": red_player,
				"blue_player": blue_player,
				"num_games": num_games,
				"deterministic_games": deterministic_games,
				"deterministic_game_rate": (
					deterministic_games / num_games
					if num_games else float("nan")
				),
				"red_wins": red_wins,
				"red_win_rate": (
					red_wins / num_games
					if num_games else float("nan")
				),
				"red_avg_moves_to_win": (
					sum(red_moves) / len(red_moves)
					if red_moves else float("nan")
				),
				"red_std_moves_to_win": (
					float(np.std(red_moves, ddof=1))
					if len(red_moves) > 1 else float("nan")
				),
				"blue_wins": blue_wins,
				"blue_win_rate": (
					blue_wins / num_games
					if num_games else float("nan")
				),
				"blue_avg_moves_to_win": (
					sum(blue_moves) / len(blue_moves)
					if blue_moves else float("nan")
				),
				"blue_std_moves_to_win": (
					float(np.std(blue_moves, ddof=1))
					if len(blue_moves) > 1 else float("nan")
				),
			})

		player_order = {
			player: index
			for index, player in enumerate(self._players)
		}

		return sorted(
			data,
			key=lambda row: (
				player_order[row["red_player"]],
				player_order[row["blue_player"]],
			),
		)

	@requires_extra("pandas", "dataframe")
	def head_to_head_summary_df(self):
		import pandas as pd

		columns = [
			"red_player",
			"blue_player",
			"num_games",
			"deterministic_games",
			"deterministic_game_rate",
			"red_wins",
			"red_win_rate",
			"red_avg_moves_to_win",
			"red_std_moves_to_win",
			"blue_wins",
			"blue_win_rate",
			"blue_avg_moves_to_win",
			"blue_std_moves_to_win",
		]

		df = pd.DataFrame(
			self.head_to_head_summary(),
			columns=columns,
		)

		df["red_player"] = pd.Categorical(
			df["red_player"],
			categories=self._players,
			ordered=True,
		)
		df["blue_player"] = pd.Categorical(
			df["blue_player"],
			categories=self._players,
			ordered=True,
		)

		return df.sort_values(
			["red_player", "blue_player"],
		).reset_index(drop=True)

	def _build_matrix(self, matchup_data, index, columns, column):
		matrix = {
			row: {
				col: float("nan")
				for col in self._players
			}
			for row in self._players
		}

		for matchup in matchup_data:
			row = matchup[index]
			col = matchup[columns]
			matrix[row][col] = matchup[column]

		return matrix

	@requires_extra("pandas", "dataframe")
	def _matrix_to_df(self, matrix):
		import pandas as pd

		return pd.DataFrame.from_dict(
			matrix,
			orient="index",
		).reindex(
			index=self._players,
			columns=self._players,
		)

	def red_win_matrix(self, rates=True):
		matchup_data = self.head_to_head_summary()
		column = "red_win_rate" if rates else "red_wins"

		return self._build_matrix(
			matchup_data,
			index="red_player",
			columns="blue_player",
			column=column,
		)

	@requires_extra("pandas", "dataframe")
	def red_win_matrix_df(self, rates=True):
		return self._matrix_to_df(
			self.red_win_matrix(rates=rates)
		)

	def blue_win_matrix(self, rates=True):
		matchup_data = self.head_to_head_summary()
		column = "blue_win_rate" if rates else "blue_wins"

		return self._build_matrix(
			matchup_data,
			index="blue_player",
			columns="red_player",
			column=column,
		)

	@requires_extra("pandas", "dataframe")
	def blue_win_matrix_df(self, rates=True):
		return self._matrix_to_df(
			self.blue_win_matrix(rates=rates)
		)

	def win_matrix(self, rates=True):
		_, _, matrix = self.win_matrices(rates=rates)
		return matrix

	@requires_extra("pandas", "dataframe")
	def win_matrix_df(self, rates=True):
		return self._matrix_to_df(
			self.win_matrix(rates=rates)
		)

	def win_matrices(self, rates=True):
		matchup_data = self.head_to_head_summary()

		red_matrix = self._build_matrix(
			matchup_data,
			index="red_player",
			columns="blue_player",
			column="red_wins",
		)
		blue_matrix = self._build_matrix(
			matchup_data,
			index="blue_player",
			columns="red_player",
			column="blue_wins",
		)

		win_matrix = {
			row: {}
			for row in self._players
		}

		for row in self._players:
			for col in self._players:
				red_value = red_matrix[row][col]
				blue_value = blue_matrix[row][col]

				if (
					np.isnan(red_value)
					and np.isnan(blue_value)
				):
					win_matrix[row][col] = float("nan")
				else:
					win_matrix[row][col] = (
						(0 if np.isnan(red_value) else red_value)
						+ (0 if np.isnan(blue_value) else blue_value)
					)

		if rates:
			num_games_matrix = self._build_matrix(
				matchup_data,
				index="red_player",
				columns="blue_player",
				column="num_games",
			)

			rate_matrix = {
				row: {}
				for row in self._players
			}

			for row in self._players:
				for col in self._players:
					forward = num_games_matrix[row][col]
					reverse = num_games_matrix[col][row]

					if np.isnan(forward) and np.isnan(reverse):
						total_games = float("nan")
					else:
						total_games = (
							(0 if np.isnan(forward) else forward)
							+ (0 if np.isnan(reverse) else reverse)
						)

					wins = win_matrix[row][col]

					if np.isnan(wins) or np.isnan(total_games):
						rate_matrix[row][col] = float("nan")
					elif total_games == 0:
						rate_matrix[row][col] = float("nan")
					else:
						rate_matrix[row][col] = wins / total_games

			win_matrix = rate_matrix

			red_matrix = self._build_matrix(
				matchup_data,
				index="red_player",
				columns="blue_player",
				column="red_win_rate",
			)
			blue_matrix = self._build_matrix(
				matchup_data,
				index="blue_player",
				columns="red_player",
				column="blue_win_rate",
			)

		return red_matrix, blue_matrix, win_matrix

	@requires_extra("pandas", "dataframe")
	def win_matrices_df(self, rates=True):
		red_matrix, blue_matrix, win_matrix = self.win_matrices(
			rates=rates,
		)

		return (
			self._matrix_to_df(red_matrix),
			self._matrix_to_df(blue_matrix),
			self._matrix_to_df(win_matrix),
		)

	def elo_ratings(self, initial_rating=1500, k_factor=32, seed=42):
		if k_factor <= 0:
			raise ValueError("k_factor must be positive")

		rng = np.random.default_rng(seed)

		ratings = {
			player: float(initial_rating)
			for player in self._players
		}
		games_played = {
			player: 0
			for player in self._players
		}

		matchups = [
			(red_player, blue_player, matchup["results"])
			for (red_player, blue_player), matchup in self._results.items()
		]

		max_games = max(
			(len(results) for _, _, results in matchups),
			default=0,
		)

		for game_index in range(max_games):
			order = rng.permutation(len(matchups))

			for i in order:
				red_player, blue_player, results = matchups[i]

				if game_index >= len(results):
					continue

				result = results[game_index]

				red_rating = ratings[red_player]
				blue_rating = ratings[blue_player]

				red_expected = 1 / (
					1 + 10 ** ((blue_rating - red_rating) / 400)
				)

				red_score = (
					1.0 if result == PlayerColor.RED else 0.0
				)
				blue_score = 1.0 - red_score

				ratings[red_player] = (
					red_rating
					+ k_factor * (red_score - red_expected)
				)
				ratings[blue_player] = (
					blue_rating
					+ k_factor * (blue_score - (1 - red_expected))
				)

				games_played[red_player] += 1
				games_played[blue_player] += 1

		data = [
			{
				"player": player,
				"elo": ratings[player],
				"games_played": games_played[player],
			}
			for player in self._players
		]

		return sorted(
			data,
			key=lambda row: row["elo"],
			reverse=True,
		)

	@requires_extra("pandas", "dataframe")
	def elo_ratings_df(
		self,
		initial_rating=1500,
		k_factor=32,
		seed=42,
	):
		import pandas as pd

		return pd.DataFrame(
			self.elo_ratings(
				initial_rating=initial_rating,
				k_factor=k_factor,
				seed=seed,
			),
			columns=["player", "elo", "games_played"],
		)

	def _matrix_to_array(self, matrix):
		return np.array([
			[matrix[row][col] for col in self._players]
			for row in self._players
		], dtype=float)

	@requires_extra("matplotlib", "visualization")
	def _plot_win_rate_matrix(
		self,
		matrix,
		row_labels,
		column_labels,
		title,
		xlabel,
		ylabel,
		cmap=None,
		ax=None,
	):
		import matplotlib.pyplot as plt
		from mpl_toolkits.axes_grid1 import make_axes_locatable

		colormap = plt.get_cmap(cmap)

		image = ax.imshow(
			matrix,
			cmap=colormap,
			vmin=0.0,
			vmax=1.0,
			aspect="auto",
		)

		ax.set_xticks(range(len(column_labels)))
		ax.set_xticklabels(column_labels, rotation=45, ha="right")
		ax.set_yticks(range(len(row_labels)))
		ax.set_yticklabels(row_labels)

		ax.set_xlabel(xlabel)
		ax.set_ylabel(ylabel)
		ax.set_title(title)

		for row in range(matrix.shape[0]):
			for col in range(matrix.shape[1]):
				value = matrix[row, col]

				if np.isnan(value):
					continue

				red, green, blue, _ = colormap(value)
				luminance = (
					0.2126 * red
					+ 0.7152 * green
					+ 0.0722 * blue
				)

				ax.text(
					col,
					row,
					f"{value:.0%}",
					ha="center",
					va="center",
					color="black" if luminance > 0.5 else "white",
				)

		divider = make_axes_locatable(ax)
		colorbar_ax = divider.append_axes(
			"right",
			size="3%",
			pad=0.1,
		)

		colorbar = ax.figure.colorbar(image, cax=colorbar_ax)
		colorbar.set_label("Win rate")
		colorbar.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
		colorbar.set_ticklabels(["0%", "25%", "50%", "75%", "100%"])

	@requires_extra("matplotlib", "visualization")
	@with_ax
	def plot_red_win_matrix(self, cmap="Reds", ax=None):
		matrix = self.red_win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			self._matrix_to_array(matrix),
			row_labels=self._players,
			column_labels=self._players,
			title="Red Win Rate",
			xlabel="Blue Player",
			ylabel="Red Player",
			ax=ax,
			cmap=cmap,
		)

	@requires_extra("matplotlib", "visualization")
	@with_ax
	def plot_blue_win_matrix(self, cmap="Blues", ax=None):
		matrix = self.blue_win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			self._matrix_to_array(matrix),
			row_labels=self._players,
			column_labels=self._players,
			title="Blue Win Rate",
			xlabel="Red Player",
			ylabel="Blue Player",
			ax=ax,
			cmap=cmap,
		)

	@requires_extra("matplotlib", "visualization")
	@with_ax
	def plot_win_matrix(self, cmap="RdYlGn", ax=None):
		matrix = self.win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			self._matrix_to_array(matrix),
			row_labels=self._players,
			column_labels=self._players,
			title="Overall Win Rate",
			xlabel="Opponent",
			ylabel="Player",
			ax=ax,
			cmap=cmap,
		)

	def filter_and_truncate(self, players, num_games):
		players = list(players)

		if len(players) != len(set(players)):
			raise ValueError("Players must be unique.")

		if (
			not isinstance(num_games, int)
			or isinstance(num_games, bool)
			or num_games < 1
		):
			raise ValueError("num_games must be a positive integer.")

		required_pairs = list(itertools.product(players, repeat=2))

		missing_pairs = [
			pair for pair in required_pairs
			if pair not in self._results
		]

		if missing_pairs:
			raise ValueError(
				f"Missing results for player pairings: {missing_pairs}"
			)

		for pair in required_pairs:
			matchup = self._results[pair]
			results = matchup["results"]
			moves = matchup["moves"]
			deterministic = matchup["deterministic"]

			if len(results) < num_games:
				raise ValueError(
					f"Pairing {pair} has {len(results)} games; "
					f"at least {num_games} are required."
				)

			if not (
				len(results) == len(moves) == len(deterministic)
			):
				raise ValueError(
					f"Pairing {pair} has inconsistent record lengths."
				)

		new_tournament = TournamentResults(players)

		for pair in required_pairs:
			matchup = self._results[pair]

			new_tournament.add_matchup_data(
				*pair,
				matchup["results"][:num_games],
				matchup["moves"][:num_games],
				matchup["deterministic"][:num_games],
			)

		return new_tournament

	def _to_json(self):
		return {
			"players": self._players,
			"matchups": [
				{
					"red_player": red_player,
					"blue_player": blue_player,
					"results": [
						result.value
						for result in matchup["results"]
					],
					"moves": matchup["moves"],
					"deterministic": matchup["deterministic"],
				}
				for (red_player, blue_player), matchup
				in self._results.items()
			],
		}

	def to_json(self):
		return copy.deepcopy(self._to_json())

	@classmethod
	def from_json(cls, data):
		instance = cls(data["players"])
		reported_players = set(instance.players)
		found_players = set()

		for matchup in data["matchups"]:
			red_player = matchup["red_player"]
			blue_player = matchup["blue_player"]

			found_players.update((red_player, blue_player))

			instance.add_matchup_data(
				red_player,
				blue_player,
				[
					PlayerColor(result)
					for result in matchup["results"]
				],
				matchup["moves"],
				matchup["deterministic"],
			)

		unknown_players = found_players - reported_players
		if unknown_players:
			raise ValueError(
				"Matchup contains players not listed in 'players': "
				+ ", ".join(sorted(unknown_players))
			)

		missing_players = reported_players - found_players
		if missing_players:
			warnings.warn(
				"The following players have no recorded matchups: "
				+ ", ".join(sorted(missing_players)),
				UserWarning,
				stacklevel=2,
			)

		return instance

	def _save(self, fp):
		json.dump(self._to_json(), fp, indent=4)

	def save(self, filename, compressed=None):
		if hasattr(filename, "write"):
			self._save(filename)
			return

		filename = Path(filename)

		if compressed is None:
			compressed = filename.suffix == ".gz"

		opener = gzip.open if compressed else open

		with opener(filename, "wt", encoding="utf-8") as fp:
			self._save(fp)

	@classmethod
	def _load(cls, fp):
		return cls.from_json(json.load(fp))

	@classmethod
	def load(cls, filename, compressed=None):
		if hasattr(filename, "read"):
			return cls._load(filename)

		filename = Path(filename)

		if compressed is None:
			compressed = filename.suffix == ".gz"

		opener = gzip.open if compressed else open

		with opener(filename, "rt", encoding="utf-8") as fp:
			return cls._load(fp)

	def _validate_players(self, *players):
		for player in players:
			if player not in self._players:
				raise ValueError(
					f"player {player!r} is not in the list of agents"
				)

	@staticmethod
	def _validate_result(result, move):
		validate_player_color(result)

		if not isinstance(move, int) or isinstance(move, bool):
			raise TypeError("move must be an integer")

	@staticmethod
	def _validate_results(results, moves):
		if not isinstance(results, (list, tuple)):
			raise TypeError("results must be a list or tuple")

		if not isinstance(moves, (list, tuple)):
			raise TypeError("moves must be a list or tuple")

		for result in results:
			validate_player_color(result)

		if not all(
			isinstance(move, int) and not isinstance(move, bool)
			for move in moves
		):
			raise TypeError("every move must be an integer")

		if len(results) != len(moves):
			raise ValueError(
				"results and moves must have the same length"
			)

	@staticmethod
	def _validate_deterministic(deterministic):
		if not isinstance(deterministic, bool):
			raise TypeError("deterministic must be a bool")

	@classmethod
	def _validate_deterministic_data(
		cls,
		results,
		moves,
		deterministic,
	):
		if not isinstance(deterministic, (list, tuple)):
			raise TypeError(
				"deterministic must be a list or tuple"
			)

		for value in deterministic:
			cls._validate_deterministic(value)

		if not (
			len(results) == len(moves) == len(deterministic)
		):
			raise ValueError(
				"results, moves, and deterministic must have "
				"the same length"
			)

	def __iter__(self):
		for (red_player, blue_player), matchup in self._results.items():
			yield (
				red_player,
				blue_player,
				tuple(matchup["results"]),
				tuple(matchup["moves"]),
				tuple(matchup["deterministic"]),
			)

	def __str__(self):
		lines = [
			"Tournament Results",
			f"Players: {', '.join(map(str, self._players))}",
			f"Matchups: {len(self._results)}",
			f"Games: {self.total_games}",
			(
				f"Deterministic games: {self.deterministic_games} "
				f"({self.deterministic_game_rate:.1%})"
			),
		]

		for (red_player, blue_player), matchup in self._results.items():
			results = matchup["results"]
			red_wins = sum(
				result == PlayerColor.RED for result in results
			)
			blue_wins = sum(
				result == PlayerColor.BLUE for result in results
			)
			deterministic_games = sum(matchup["deterministic"])

			lines.append(
				f"  {red_player} vs {blue_player}: "
				f"{len(results)} games "
				f"(Red wins: {red_wins}, Blue wins: {blue_wins}, "
				f"Deterministic: {deterministic_games})"
			)

		return "\n".join(lines)

	def __repr__(self):
		return (
			f"{type(self).__name__}("
			f"players={self._players!r}, "
			f"matchups={len(self._results)}"
			")"
		)

