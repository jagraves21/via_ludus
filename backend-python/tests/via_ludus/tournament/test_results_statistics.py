import math

import pytest

from via_ludus.board import PlayerColor
from via_ludus.tournament import TournamentResults


R = PlayerColor.RED
B = PlayerColor.BLUE
NAN = float("nan")


def _is_nan(value):
	return isinstance(value, float) and math.isnan(value)


def _same(left, right):
	return (_is_nan(left) and _is_nan(right)) or left == right


def _assert_matrix(matrix, expected):
	"""``expected`` maps (row, column) to a value; every other cell is NaN."""
	players = list(matrix)

	assert list(matrix) == players
	for row in players:
		assert list(matrix[row]) == players

		for col in players:
			if (row, col) in expected:
				assert matrix[row][col] == pytest.approx(expected[(row, col)]), (row, col)
			else:
				assert _is_nan(matrix[row][col]), (row, col)


class TestSummary:
	def test_players_are_sorted_by_total_win_rate(self, sample_results):
		assert [row["player"] for row in sample_results.summary()] == ["gamma", "alpha", "beta"]

	def test_alpha(self, sample_results):
		row = {row["player"]: row for row in sample_results.summary()}["alpha"]

		assert row["total_games"] == 9
		assert row["total_wins"] == 5
		assert row["total_win_rate"] == pytest.approx(5 / 9)
		assert row["deterministic_games"] == 5
		assert row["deterministic_game_rate"] == pytest.approx(5 / 9)
		assert row["red_games"] == 6
		assert row["red_wins"] == 3
		assert row["red_win_rate"] == pytest.approx(0.5)
		assert row["red_deterministic_games"] == 4
		assert row["blue_games"] == 3
		assert row["blue_wins"] == 2
		assert row["blue_win_rate"] == pytest.approx(2 / 3)
		assert row["blue_deterministic_games"] == 1

	def test_beta(self, sample_results):
		row = {row["player"]: row for row in sample_results.summary()}["beta"]

		assert row["total_games"] == 8
		assert row["total_wins"] == 2
		assert row["total_win_rate"] == pytest.approx(0.25)
		assert row["deterministic_games"] == 4
		assert row["deterministic_game_rate"] == pytest.approx(0.5)
		assert row["red_games"] == 3
		assert row["red_wins"] == 1
		assert row["blue_games"] == 5
		assert row["blue_wins"] == 1
		assert row["blue_deterministic_games"] == 3

	def test_gamma(self, sample_results):
		row = {row["player"]: row for row in sample_results.summary()}["gamma"]

		assert row["total_games"] == 3
		assert row["total_wins"] == 3
		assert row["total_win_rate"] == pytest.approx(1.0)
		assert row["red_games"] == 1
		assert row["blue_games"] == 2
		assert row["deterministic_game_rate"] == pytest.approx(1.0)

	def test_every_game_is_counted_for_both_players(self, sample_results):
		rows = sample_results.summary()

		assert sum(row["total_games"] for row in rows) == 2 * sample_results.total_games

	def test_every_game_has_exactly_one_winner(self, sample_results):
		rows = sample_results.summary()

		assert sum(row["total_wins"] for row in rows) == sample_results.total_games

	def test_total_games_split_by_color(self, sample_results):
		for row in sample_results.summary():
			assert row["total_games"] == row["red_games"] + row["blue_games"]
			assert row["total_wins"] == row["red_wins"] + row["blue_wins"]
			assert row["deterministic_games"] == row["red_deterministic_games"] + row["blue_deterministic_games"]

	def test_rows_have_the_expected_columns(self, sample_results):
		assert list(sample_results.summary()[0]) == [
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

	def test_players_without_games_have_zero_rates(self):
		rows = TournamentResults(["a", "b"]).summary()

		assert [row["player"] for row in rows] == ["a", "b"]
		for row in rows:
			assert row["total_games"] == 0
			assert row["total_win_rate"] == 0.0
			assert row["deterministic_game_rate"] == 0.0
			assert row["red_win_rate"] == 0.0
			assert row["blue_win_rate"] == 0.0

	def test_a_player_without_games_in_a_color_has_a_zero_rate(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("a", "b", R, 5, True)

		rows = {row["player"]: row for row in results.summary()}

		assert rows["a"]["blue_games"] == 0
		assert rows["a"]["blue_win_rate"] == 0.0
		assert rows["b"]["red_games"] == 0
		assert rows["b"]["red_win_rate"] == 0.0

	def test_ties_keep_the_player_order(self):
		results = TournamentResults(["a", "b", "c"])

		assert [row["player"] for row in results.summary()] == ["a", "b", "c"]

	def test_games_against_oneself_count_once_for_each_color(self):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", [R, B, R], [5, 6, 7], [True, True, True])

		row = results.summary()[0]

		assert row["total_games"] == 6
		assert row["red_games"] == 3
		assert row["red_wins"] == 2
		assert row["red_win_rate"] == pytest.approx(2 / 3)
		assert row["blue_games"] == 3
		assert row["blue_wins"] == 1
		assert row["blue_win_rate"] == pytest.approx(1 / 3)
		assert row["total_wins"] == 3

	@pytest.mark.parametrize("outcomes", [[R, R, R], [B, B, B], [R, B, R, B]])
	def test_games_against_oneself_do_not_change_the_total_win_rate(self, outcomes):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", outcomes, [5] * len(outcomes), [True] * len(outcomes))

		row = results.summary()[0]

		assert row["total_win_rate"] == pytest.approx(0.5)
		assert row["total_games"] == 2 * len(outcomes)

	def test_games_against_oneself_do_not_dilute_results_against_others(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_data("a", "b", [R, R], [5, 5], [True, True])
		results.add_matchup_data("a", "a", [R, B], [5, 5], [True, True])

		row = {row["player"]: row for row in results.summary()}["a"]

		# 2 wins in 2 games against b, plus 2 wins in the 4 counted self-play
		# games (the 2 games count once as red and once as blue)
		assert row["total_games"] == 6
		assert row["total_wins"] == 4

	def test_each_game_still_has_exactly_one_winner_with_self_play(self, full_results):
		rows = full_results.summary()

		assert sum(row["total_wins"] for row in rows) == full_results.total_games
		assert sum(row["total_games"] for row in rows) == 2 * full_results.total_games

	def test_every_player_has_the_same_number_of_games_with_self_play(self, full_results):
		assert {row["total_games"] for row in full_results.summary()} == {12}

	def test_summary_does_not_create_matchups(self, sample_results):
		sample_results.summary()

		assert len(list(sample_results)) == 4


class TestHeadToHeadSummary:
	def test_one_row_per_recorded_matchup(self, sample_results):
		rows = sample_results.head_to_head_summary()

		assert [(row["red_player"], row["blue_player"]) for row in rows] == [
			("alpha", "beta"),
			("alpha", "gamma"),
			("beta", "alpha"),
			("gamma", "beta"),
		]

	def test_rows_follow_the_player_order_not_the_insertion_order(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("b", "a", R, 5, True)
		results.add_matchup_result("a", "b", B, 6, True)

		rows = results.head_to_head_summary()

		assert [(row["red_player"], row["blue_player"]) for row in rows] == [("a", "b"), ("b", "a")]

	def test_alpha_against_beta(self, sample_results):
		row = sample_results.head_to_head_summary()[0]

		assert row["num_games"] == 4
		assert row["deterministic_games"] == 2
		assert row["deterministic_game_rate"] == pytest.approx(0.5)
		assert row["red_wins"] == 3
		assert row["red_win_rate"] == pytest.approx(0.75)
		assert row["red_avg_moves_to_win"] == pytest.approx(12.0)
		assert row["red_std_moves_to_win"] == pytest.approx(2.0)
		assert row["blue_wins"] == 1
		assert row["blue_win_rate"] == pytest.approx(0.25)
		assert row["blue_avg_moves_to_win"] == pytest.approx(9.0)
		assert _is_nan(row["blue_std_moves_to_win"])

	def test_beta_against_alpha(self, sample_results):
		row = sample_results.head_to_head_summary()[2]

		assert row["num_games"] == 3
		assert row["deterministic_games"] == 1
		assert row["deterministic_game_rate"] == pytest.approx(1 / 3)
		assert row["red_wins"] == 1
		assert row["red_win_rate"] == pytest.approx(1 / 3)
		assert row["red_avg_moves_to_win"] == pytest.approx(13.0)
		assert _is_nan(row["red_std_moves_to_win"])
		assert row["blue_wins"] == 2
		assert row["blue_win_rate"] == pytest.approx(2 / 3)
		assert row["blue_avg_moves_to_win"] == pytest.approx(13.0)
		assert row["blue_std_moves_to_win"] == pytest.approx(math.sqrt(8))

	def test_a_color_that_never_wins_has_undefined_move_statistics(self, sample_results):
		row = sample_results.head_to_head_summary()[1]

		assert row["red_wins"] == 0
		assert row["red_win_rate"] == 0.0
		assert _is_nan(row["red_avg_moves_to_win"])
		assert _is_nan(row["red_std_moves_to_win"])
		assert row["blue_avg_moves_to_win"] == pytest.approx(21.0)
		assert row["blue_std_moves_to_win"] == pytest.approx(math.sqrt(2))

	def test_a_single_win_has_an_undefined_standard_deviation(self, sample_results):
		row = sample_results.head_to_head_summary()[3]

		assert row["red_avg_moves_to_win"] == pytest.approx(8.0)
		assert _is_nan(row["red_std_moves_to_win"])
		assert row["blue_wins"] == 0
		assert _is_nan(row["blue_avg_moves_to_win"])

	def test_the_standard_deviation_is_the_sample_standard_deviation(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_data("a", "b", [R, R], [10, 20], [False, False])

		row = results.head_to_head_summary()[0]

		assert row["red_std_moves_to_win"] == pytest.approx(math.sqrt(50))

	def test_wins_add_up_to_the_number_of_games(self, sample_results):
		for row in sample_results.head_to_head_summary():
			assert row["red_wins"] + row["blue_wins"] == row["num_games"]
			assert row["red_win_rate"] + row["blue_win_rate"] == pytest.approx(1.0)

	def test_matchups_without_games_have_undefined_rates(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_data("a", "b", [], [], [])

		row = results.head_to_head_summary()[0]

		assert row["num_games"] == 0
		assert _is_nan(row["red_win_rate"])
		assert _is_nan(row["blue_win_rate"])
		assert _is_nan(row["deterministic_game_rate"])

	def test_no_games_gives_no_rows(self):
		assert TournamentResults(["a", "b"]).head_to_head_summary() == []

	def test_rows_have_the_expected_columns(self, sample_results):
		assert list(sample_results.head_to_head_summary()[0]) == [
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

class TestFirstMoveAdvantage:
	def test_one_row_per_player_with_self_play(self, full_results):
		rows = full_results.first_move_advantage()

		assert [row["player"] for row in rows] == ["a", "b"]

	def test_values(self, full_results):
		rows = {row["player"]: row for row in full_results.first_move_advantage()}

		# a against a: R, R, B     b against b: B, R, R
		for player in ("a", "b"):
			assert rows[player]["num_games"] == 3
			assert rows[player]["red_wins"] == 2
			assert rows[player]["red_win_rate"] == pytest.approx(2 / 3)
			assert rows[player]["blue_wins"] == 1
			assert rows[player]["blue_win_rate"] == pytest.approx(1 / 3)

	def test_the_two_rates_add_up_to_one(self, full_results):
		for row in full_results.first_move_advantage():
			assert row["red_win_rate"] + row["blue_win_rate"] == pytest.approx(1.0)
			assert row["red_wins"] + row["blue_wins"] == row["num_games"]

	@pytest.mark.parametrize("outcomes, red_rate", [([R, R, R], 1.0), ([B, B], 0.0), ([R, B], 0.5)])
	def test_a_player_that_always_wins_when_moving_first(self, outcomes, red_rate):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", outcomes, [5] * len(outcomes), [True] * len(outcomes))

		assert results.first_move_advantage()[0]["red_win_rate"] == pytest.approx(red_rate)

	def test_results_against_other_players_are_ignored(self, sample_results):
		assert sample_results.first_move_advantage() == []

	def test_only_players_with_self_play_games_are_listed(self):
		results = TournamentResults(["a", "b", "c"])
		results.add_matchup_data("a", "b", [R], [5], [True])
		results.add_matchup_data("b", "b", [B, B], [5, 5], [True, True])

		rows = results.first_move_advantage()

		assert [row["player"] for row in rows] == ["b"]
		assert rows[0]["blue_win_rate"] == 1.0

	def test_matchups_without_games_are_skipped(self):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", [], [], [])

		assert results.first_move_advantage() == []

	def test_without_results(self):
		assert TournamentResults(["a", "b"]).first_move_advantage() == []

	def test_players_are_listed_in_player_order(self):
		results = TournamentResults(["c", "a", "b"])
		for name in ("b", "c", "a"):
			results.add_matchup_data(name, name, [R], [5], [True])

		assert [row["player"] for row in results.first_move_advantage()] == ["c", "a", "b"]

	def test_rows_have_the_expected_columns(self, full_results):
		assert list(full_results.first_move_advantage()[0]) == [
			"player",
			"num_games",
			"red_wins",
			"red_win_rate",
			"blue_wins",
			"blue_win_rate",
		]

	def test_it_matches_the_head_to_head_row_of_the_player_against_itself(self, full_results):
		head_to_head = {
			(row["red_player"], row["blue_player"]): row
			for row in full_results.head_to_head_summary()
		}

		for row in full_results.first_move_advantage():
			expected = head_to_head[(row["player"], row["player"])]

			assert row["red_win_rate"] == pytest.approx(expected["red_win_rate"])
			assert row["blue_win_rate"] == pytest.approx(expected["blue_win_rate"])
			assert row["num_games"] == expected["num_games"]


class TestRedAndBlueWinMatrices:
	def test_red_win_rates(self, sample_results):
		_assert_matrix(sample_results.red_win_matrix(), {
			("alpha", "beta"): 0.75,
			("alpha", "gamma"): 0.0,
			("beta", "alpha"): 1 / 3,
			("gamma", "beta"): 1.0,
		})

	def test_red_win_counts(self, sample_results):
		_assert_matrix(sample_results.red_win_matrix(rates=False), {
			("alpha", "beta"): 3,
			("alpha", "gamma"): 0,
			("beta", "alpha"): 1,
			("gamma", "beta"): 1,
		})

	def test_blue_win_rates_are_indexed_by_the_blue_player(self, sample_results):
		_assert_matrix(sample_results.blue_win_matrix(), {
			("beta", "alpha"): 0.25,
			("alpha", "beta"): 2 / 3,
			("gamma", "alpha"): 1.0,
			("beta", "gamma"): 0.0,
		})

	def test_blue_win_counts(self, sample_results):
		_assert_matrix(sample_results.blue_win_matrix(rates=False), {
			("beta", "alpha"): 1,
			("alpha", "beta"): 2,
			("gamma", "alpha"): 2,
			("beta", "gamma"): 0,
		})

	def test_matrices_cover_every_player_pair(self, sample_results):
		matrix = sample_results.red_win_matrix()

		assert list(matrix) == ["alpha", "beta", "gamma"]
		assert all(list(row) == ["alpha", "beta", "gamma"] for row in matrix.values())

	def test_matrices_without_games_are_undefined(self):
		results = TournamentResults(["a", "b"])

		_assert_matrix(results.red_win_matrix(), {})
		_assert_matrix(results.blue_win_matrix(), {})
		_assert_matrix(results.win_matrix(), {})


class TestOverallWinMatrix:
	def test_win_rates(self, sample_results):
		_assert_matrix(sample_results.win_matrix(), {
			("alpha", "beta"): 5 / 7,
			("beta", "alpha"): 2 / 7,
			("alpha", "gamma"): 0.0,
			("gamma", "alpha"): 1.0,
			("beta", "gamma"): 0.0,
			("gamma", "beta"): 1.0,
		})

	def test_win_counts(self, sample_results):
		_assert_matrix(sample_results.win_matrix(rates=False), {
			("alpha", "beta"): 5,
			("beta", "alpha"): 2,
			("alpha", "gamma"): 0,
			("gamma", "alpha"): 2,
			("beta", "gamma"): 0,
			("gamma", "beta"): 1,
		})

	def test_rates_default_to_true(self, sample_results):
		default = sample_results.win_matrix()
		explicit = sample_results.win_matrix(rates=True)

		for row in default:
			for col in default:
				assert _same(default[row][col], explicit[row][col])

	def test_opponents_win_rates_are_complementary(self, sample_results):
		matrix = sample_results.win_matrix()

		for row, col in [("alpha", "beta"), ("alpha", "gamma"), ("beta", "gamma")]:
			assert matrix[row][col] + matrix[col][row] == pytest.approx(1.0)

	def test_win_counts_add_up_to_the_games_between_two_players(self, sample_results):
		matrix = sample_results.win_matrix(rates=False)

		assert matrix["alpha"]["beta"] + matrix["beta"]["alpha"] == 4 + 3
		assert matrix["alpha"]["gamma"] + matrix["gamma"]["alpha"] == 2
		assert matrix["beta"]["gamma"] + matrix["gamma"]["beta"] == 1


class TestSelfPlayMatrices:
	def test_the_red_matrix_diagonal_is_the_first_mover_win_rate(self, full_results):
		matrix = full_results.red_win_matrix()

		assert matrix["a"]["a"] == pytest.approx(2 / 3)
		assert matrix["b"]["b"] == pytest.approx(2 / 3)

	def test_the_blue_matrix_diagonal_is_the_second_mover_win_rate(self, full_results):
		matrix = full_results.blue_win_matrix()

		assert matrix["a"]["a"] == pytest.approx(1 / 3)
		assert matrix["b"]["b"] == pytest.approx(1 / 3)

	def test_the_diagonals_of_the_two_matrices_add_up_to_one(self, full_results):
		red = full_results.red_win_matrix()
		blue = full_results.blue_win_matrix()

		for player in ("a", "b"):
			assert red[player][player] + blue[player][player] == pytest.approx(1.0)

	@pytest.mark.parametrize("outcomes", [[R, R, R], [B, B], [R, B, B, R, R]])
	def test_a_player_wins_exactly_half_of_its_games_against_itself(self, outcomes):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", outcomes, [5] * len(outcomes), [True] * len(outcomes))

		assert results.win_matrix()["a"]["a"] == pytest.approx(0.5)

	def test_the_win_count_on_the_diagonal_is_the_number_of_games(self, full_results):
		matrix = full_results.win_matrix(rates=False)

		assert matrix["a"]["a"] == 3
		assert matrix["b"]["b"] == 3

	def test_the_overall_matrix_against_other_players_is_unaffected(self, full_results):
		matrix = full_results.win_matrix()

		# a (red) vs b (blue): R, B, B; b (red) vs a (blue): B, B, R
		# a wins 1 + 2 of 6 games
		assert matrix["a"]["b"] == pytest.approx(0.5)
		assert matrix["b"]["a"] == pytest.approx(0.5)


class TestWinMatrices:
	def test_returns_the_three_matrices(self, sample_results):
		red, blue, overall = sample_results.win_matrices()

		_assert_matrix(red, {
			("alpha", "beta"): 0.75,
			("alpha", "gamma"): 0.0,
			("beta", "alpha"): 1 / 3,
			("gamma", "beta"): 1.0,
		})
		_assert_matrix(blue, {
			("beta", "alpha"): 0.25,
			("alpha", "beta"): 2 / 3,
			("gamma", "alpha"): 1.0,
			("beta", "gamma"): 0.0,
		})
		_assert_matrix(overall, {
			("alpha", "beta"): 5 / 7,
			("beta", "alpha"): 2 / 7,
			("alpha", "gamma"): 0.0,
			("gamma", "alpha"): 1.0,
			("beta", "gamma"): 0.0,
			("gamma", "beta"): 1.0,
		})

	def test_counts(self, sample_results):
		red, blue, overall = sample_results.win_matrices(rates=False)

		_assert_matrix(red, {
			("alpha", "beta"): 3,
			("alpha", "gamma"): 0,
			("beta", "alpha"): 1,
			("gamma", "beta"): 1,
		})
		_assert_matrix(blue, {
			("beta", "alpha"): 1,
			("alpha", "beta"): 2,
			("gamma", "alpha"): 2,
			("beta", "gamma"): 0,
		})
		_assert_matrix(overall, {
			("alpha", "beta"): 5,
			("beta", "alpha"): 2,
			("alpha", "gamma"): 0,
			("gamma", "alpha"): 2,
			("beta", "gamma"): 0,
			("gamma", "beta"): 1,
		})

	def test_individual_matrices_match_the_win_matrices(self, sample_results):
		for rates in (True, False):
			red, blue, overall = sample_results.win_matrices(rates=rates)

			for row in red:
				for col in red:
					for left, right in (
						(red[row][col], sample_results.red_win_matrix(rates=rates)[row][col]),
						(blue[row][col], sample_results.blue_win_matrix(rates=rates)[row][col]),
						(overall[row][col], sample_results.win_matrix(rates=rates)[row][col]),
					):
						assert _same(left, right)


class TestEloRatings:
	def test_one_decisive_game(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("a", "b", R, 5, True)

		ratings = {row["player"]: row["elo"] for row in results.elo_ratings()}

		assert ratings == {"a": pytest.approx(1516.0), "b": pytest.approx(1484.0)}

	def test_blue_win(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("a", "b", B, 5, True)

		ratings = {row["player"]: row["elo"] for row in results.elo_ratings()}

		assert ratings == {"a": pytest.approx(1484.0), "b": pytest.approx(1516.0)}

	def test_initial_rating(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("a", "b", R, 5, True)

		ratings = {row["player"]: row["elo"] for row in results.elo_ratings(initial_rating=1000)}

		assert ratings == {"a": pytest.approx(1016.0), "b": pytest.approx(984.0)}

	def test_k_factor(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_result("a", "b", R, 5, True)

		ratings = {row["player"]: row["elo"] for row in results.elo_ratings(k_factor=16)}

		assert ratings == {"a": pytest.approx(1508.0), "b": pytest.approx(1492.0)}

	@pytest.mark.parametrize("k_factor", [0, -1, -32.0])
	def test_invalid_k_factors_are_rejected(self, sample_results, k_factor):
		with pytest.raises(ValueError, match="k_factor must be positive"):
			sample_results.elo_ratings(k_factor=k_factor)

	def test_players_are_sorted_by_rating(self, sample_results):
		ratings = [row["elo"] for row in sample_results.elo_ratings()]

		assert ratings == sorted(ratings, reverse=True)

	def test_games_played(self, sample_results):
		games = {row["player"]: row["games_played"] for row in sample_results.elo_ratings()}

		assert games == {"alpha": 9, "beta": 8, "gamma": 3}

	def test_rows_have_the_expected_columns(self, sample_results):
		assert list(sample_results.elo_ratings()[0]) == ["player", "elo", "games_played"]

	def test_ratings_are_conserved(self, sample_results):
		total = sum(row["elo"] for row in sample_results.elo_ratings())

		assert total == pytest.approx(3 * 1500.0)

	def test_ratings_are_reproducible_for_a_seed(self, sample_results):
		assert sample_results.elo_ratings(seed=7) == sample_results.elo_ratings(seed=7)

	def test_default_seed_is_fixed(self, sample_results):
		assert sample_results.elo_ratings() == sample_results.elo_ratings(seed=42)

	def test_the_player_who_always_wins_has_the_highest_rating(self):
		results = TournamentResults(["strong", "weak"])
		results.add_matchup_data("strong", "weak", [R] * 5, [5] * 5, [True] * 5)
		results.add_matchup_data("weak", "strong", [B] * 5, [5] * 5, [True] * 5)

		ratings = results.elo_ratings()

		assert [row["player"] for row in ratings] == ["strong", "weak"]
		assert ratings[0]["elo"] > 1500 > ratings[1]["elo"]

	@pytest.mark.parametrize("outcomes", [[R] * 5, [B] * 5, [R, B, R, B, R]])
	def test_games_against_oneself_never_change_a_rating(self, outcomes):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", outcomes, [5] * 5, [True] * 5)

		row = results.elo_ratings()[0]

		assert row["elo"] == pytest.approx(1500.0)

	def test_games_against_oneself_count_twice_as_games_played(self):
		results = TournamentResults(["a"])
		results.add_matchup_data("a", "a", [R, B, R], [5, 6, 7], [True] * 3)

		assert results.elo_ratings()[0]["games_played"] == 6

	def test_games_against_oneself_do_not_change_ratings_earned_against_others(self):
		without = TournamentResults(["a", "b"])
		without.add_matchup_result("a", "b", R, 5, True)

		with_self_play = TournamentResults(["a", "b"])
		with_self_play.add_matchup_result("a", "b", R, 5, True)
		with_self_play.add_matchup_result("a", "a", R, 5, True)
		with_self_play.add_matchup_result("b", "b", R, 5, True)

		expected = {row["player"]: row["elo"] for row in without.elo_ratings()}
		actual = {row["player"]: row["elo"] for row in with_self_play.elo_ratings()}

		assert actual == {"a": pytest.approx(expected["a"]), "b": pytest.approx(expected["b"])}

	def test_games_against_oneself_do_not_shift_the_rating_of_the_other_players(self):
		results = TournamentResults(["a", "b"])
		results.add_matchup_data("a", "a", [R] * 6, [5] * 6, [True] * 6)
		results.add_matchup_data("b", "b", [R] * 6, [5] * 6, [True] * 6)

		assert {row["elo"] for row in results.elo_ratings()} == {1500.0}

	def test_ratings_are_conserved_with_self_play(self, full_results):
		total = sum(row["elo"] for row in full_results.elo_ratings())

		assert total == pytest.approx(2 * 1500.0)

	def test_without_games_everyone_keeps_the_initial_rating(self):
		ratings = TournamentResults(["a", "b"]).elo_ratings(initial_rating=1200)

		assert [row["player"] for row in ratings] == ["a", "b"]
		assert all(row["elo"] == 1200.0 and row["games_played"] == 0 for row in ratings)
