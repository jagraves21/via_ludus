from collections import defaultdict
import itertools
import json
from pathlib import Path
import warnings

from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandas as pd

from ..utils import with_ax

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

	def add_matchup_result(self, red_player, blue_player, result, move):
		self._validate_players(red_player, blue_player)
		self._validate_result(result, move)

		self.add_matchup_data(
			red_player,
			blue_player,
			[result],
			[move],
		)

	def add_matchup_data(self, red_player, blue_player, results, moves):
		self._validate_players(red_player, blue_player)
		self._validate_results(results, moves)

		matchups = self._results[(red_player, blue_player)]
		matchups["results"].extend(results)
		matchups["moves"].extend(moves)

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
			)

	def get_matchup_results(self, red_player, blue_player):
		return self.get_matchup_data(red_player, blue_player)["results"]

	def get_matchup_moves(self, red_player, blue_player):
		return self.get_matchup_data(red_player, blue_player)["moves"]

	def get_matchup_data(self, red_player, blue_player):
		self._validate_players(red_player, blue_player)

		matchup = self._results.get((red_player, blue_player))

		if matchup is None:
			return {
				"results": (),
				"moves": (),
			}

		return {
			"results": tuple(matchup["results"]),
			"moves": tuple(matchup["moves"]),
		}

	def get_matchup_count(self, red_player, blue_player):
		return len( self.get_matchup_results(red_player, blue_player) )
		
	def summary(self):
		data = []

		for player in self._players:
			red_results = list(itertools.chain.from_iterable(
				matchup["results"]
				for (red_player, _), matchup in self._results.items()
				if red_player == player
			))

			blue_results = list(itertools.chain.from_iterable(
				matchup["results"]
				for (red_player, blue_player), matchup in self._results.items()
				if blue_player == player and red_player != blue_player
			))

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

			data.append({
				"player": player,
				"total_games": total_games,
				"total_wins": total_wins,
				"total_win_rate": total_wins / total_games if total_games else 0.0,
				"red_games": red_games,
				"red_wins": red_wins,
				"red_win_rate": red_wins / red_games if red_games else 0.0,
				"blue_games": blue_games,
				"blue_wins": blue_wins,
				"blue_win_rate": blue_wins / blue_games if blue_games else 0.0,
			})

		return (
			pd.DataFrame(
				data,
				columns=[
					"player",
					"total_games",
					"total_wins",
					"total_win_rate",
					"red_games",
					"red_wins",
					"red_win_rate",
					"blue_games",
					"blue_wins",
					"blue_win_rate",
				],
			)
			.sort_values("total_win_rate", ascending=False)
			.reset_index(drop=True)
		)

	def head_to_head_summary(self):
		data = []

		for (red_player, blue_player), matchup in self._results.items():
			results = matchup["results"]
			moves = matchup["moves"]
			num_games = len(results)

			red_wins = sum(
				result == PlayerColor.RED
				for result in results
			)
			blue_wins = sum(
				result == PlayerColor.BLUE
				for result in results
			)

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
				"red_wins": red_wins,
				"red_win_rate": (
					red_wins / num_games
					if num_games
					else float("nan")
				),
				"red_avg_moves_to_win": (
					sum(red_moves) / len(red_moves)
					if red_moves
					else float("nan")
				),
				"red_std_moves_to_win": (
					pd.Series(red_moves).std()
					if len(red_moves) > 1
					else float("nan")
				),
				"blue_wins": blue_wins,
				"blue_win_rate": (
					blue_wins / num_games
					if num_games
					else float("nan")
				),
				"blue_avg_moves_to_win": (
					sum(blue_moves) / len(blue_moves)
					if blue_moves
					else float("nan")
				),
				"blue_std_moves_to_win": (
					pd.Series(blue_moves).std()
					if len(blue_moves) > 1
					else float("nan")
				),
			})

		columns = [
			"red_player",
			"blue_player",
			"num_games",
			"red_wins",
			"red_win_rate",
			"red_avg_moves_to_win",
			"red_std_moves_to_win",
			"blue_wins",
			"blue_win_rate",
			"blue_avg_moves_to_win",
			"blue_std_moves_to_win",
		]

		df = pd.DataFrame(data, columns=columns)

		player_order = self._players

		df["red_player"] = pd.Categorical(
			df["red_player"],
			categories=player_order,
			ordered=True,
		)
		df["blue_player"] = pd.Categorical(
			df["blue_player"],
			categories=player_order,
			ordered=True,
		)

		return df.sort_values(
			["red_player", "blue_player"],
		).reset_index(drop=True)

	def _build_matrix(self, matchup_df, index, columns, column):
		return matchup_df.pivot(
			index=index,
			columns=columns,
			values=column,
		)

	def red_win_matrix(self, rates=True):
		matchup_df = self.head_to_head_summary()
		column = "red_win_rate" if rates else "red_wins"

		return self._build_matrix(
			matchup_df,
			index="red_player",
			columns="blue_player",
			column=column,
		)

	def blue_win_matrix(self, rates=True):
		matchup_df = self.head_to_head_summary()
		column = "blue_win_rate" if rates else "blue_wins"

		return self._build_matrix(
			matchup_df,
			index="blue_player",
			columns="red_player",
			column=column,
		)

	def win_matrix(self, rates=True):
		_, _, win_matrix_df = self.win_matrices(rates=rates)
		return win_matrix_df

	def win_matrices(self, rates=True):
		matchup_df = self.head_to_head_summary()

		red_matrix_df = self._build_matrix(
			matchup_df,
			index="red_player",
			columns="blue_player",
			column="red_wins",
		)
		blue_matrix_df = self._build_matrix(
			matchup_df,
			index="blue_player",
			columns="red_player",
			column="blue_wins",
		)

		win_matrix_df = red_matrix_df.add(
			blue_matrix_df,
			fill_value=0,
		)

		if rates:
			num_games_df = self._build_matrix(
				matchup_df,
				index="red_player",
				columns="blue_player",
				column="num_games",
			)
			total_games_df = num_games_df.add(
				num_games_df.T,
				fill_value=0,
			)
			win_matrix_df = win_matrix_df / total_games_df

			red_matrix_df = self._build_matrix(
				matchup_df,
				index="red_player",
				columns="blue_player",
				column="red_win_rate",
			)
			blue_matrix_df = self._build_matrix(
				matchup_df,
				index="blue_player",
				columns="red_player",
				column="blue_win_rate",
			)

		return red_matrix_df, blue_matrix_df, win_matrix_df

	@with_ax
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

				if pd.isna(value):
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

	@with_ax
	def plot_red_win_matrix(self, cmap="Reds", ax=None):
		matrix = self.red_win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			matrix.to_numpy(dtype=float),
			row_labels=matrix.index,
			column_labels=matrix.columns,
			title="Red Win Rate",
			xlabel="Blue Player",
			ylabel="Red Player",
			ax=ax,
			cmap=cmap,
		)

	@with_ax
	def plot_blue_win_matrix(self, cmap="Blues", ax=None):
		matrix = self.blue_win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			matrix.to_numpy(dtype=float),
			row_labels=matrix.index,
			column_labels=matrix.columns,
			title="Blue Win Rate",
			xlabel="Red Player",
			ylabel="Blue Player",
			ax=ax,
			cmap=cmap,
		)

	@with_ax
	def plot_win_matrix(self, cmap="RdYlGn", ax=None):
		matrix = self.win_matrix(rates=True)

		return self._plot_win_rate_matrix(
			matrix.to_numpy(dtype=float),
			row_labels=matrix.index,
			column_labels=matrix.columns,
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

		if not isinstance(num_games, int) or isinstance(num_games, bool) or num_games < 1:
			raise ValueError("num_games must be a positive integer.")

		required_pairs = list( itertools.product(players, repeat=2) )

		missing_pairs = [
			pair
			for pair in required_pairs
			if pair not in self._results
		]

		if missing_pairs:
			raise ValueError(
				f"Missing results for player pairings: {missing_pairs}"
			)

		for pair in required_pairs:
			# every pair is in _results so we can
			# do this without modifying _results
			matchup = self._results[pair]
			results = matchup["results"]
			moves = matchup["moves"]

			if len(results) < num_games:
				raise ValueError(
					f"Pairing {pair} has {len(results)} games; "
					f"at least {num_games} are required."
				)

			if len(moves) != len(results):
				raise ValueError(
					f"Pairing {pair} has {len(results)} results "
					f"but {len(moves)} move records."
				)
		
		new_tournament = TournamentResults(players)
		for pair in required_pairs:
			# every pair is in _results so we can
			# do this without modifying _results
			matchup = self._results[pair]
			results = matchup["results"]
			moves = matchup["moves"]

			new_tournament.add_matchup_data(
				*pair, results[:num_games], moves[:num_games]
			)

		return new_tournament

	def save(self, filename):
		filename = Path(filename)

		with filename.open("w", encoding="utf-8") as fp:
			json.dump(self._results_to_json(), fp, indent=4)

	@classmethod
	def load(cls, filename):
		filename = Path(filename)

		with filename.open("r", encoding="utf-8") as fp:
			data = json.load(fp)

		instance = cls(data["players"])
		reported_players = set(instance.players)
		found_players = set()

		for matchup in data["matchups"]:
			red_player = matchup["red_player"]
			blue_player = matchup["blue_player"]

			found_players.update( (red_player,blue_player) )

			instance.add_matchup_data(
				red_player,
				blue_player,
				[
					PlayerColor(result)
					for result in matchup["results"]
				],
				matchup["moves"],
			)
		
		unknown_players = found_players - reported_players
		if len(unknown_players) > 0:
			raise ValueError(
				"Matchup contains players not listed in 'players': "
				+ ", ".join(sorted(unknown_players))
			)

		missing_players = reported_players - found_players
		if len(missing_players) > 0:
			warnings.warn(
				"The following players have no recorded matchups: "
				+ ", ".join(sorted(missing_players)),
				UserWarning,
				stacklevel=2,
			)

		return instance

	def _results_to_json(self):
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
				}
				for (red_player, blue_player), matchup in self._results.items()
			],
		}

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

	def __iter__(self):
		for (red_player, blue_player), matchup in self._results.items():
			yield (
				red_player,
				blue_player,
				tuple(matchup["results"]),
				tuple(matchup["moves"]),
			)

	def __str__(self):
		lines = [
			"Tournament Results",
			f"Players: {', '.join(map(str, self._players))}",
			f"Matchups: {len(self._results)}",
		]

		for (red_player, blue_player), matchup in self._results.items():
			results = matchup["results"]
			red_wins = sum(
				result == PlayerColor.RED
				for result in results
			)
			blue_wins = sum(
				result == PlayerColor.BLUE
				for result in results
			)

			lines.append(
				f"  {red_player} vs {blue_player}: "
				f"{len(results)} games "
				f"(Red wins: {red_wins}, Blue wins: {blue_wins})"
			)

		return "\n".join(lines)

	def __repr__(self):
		return (
			f"{type(self).__name__}("
			f"players={self._players!r}, "
			f"matchups={len(self._results)}"
			")"
		)

