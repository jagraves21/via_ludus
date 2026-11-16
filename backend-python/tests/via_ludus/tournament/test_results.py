"""Tests for ``TournamentResults``.

The file is organised in sections: construction and bookkeeping, JSON and
file persistence, statistics, DataFrame views and win-matrix plots.

The DataFrame tests need the optional pandas library and the plot tests need
the optional matplotlib library; they are skipped one by one when the library
is not installed. How the package behaves *without* those libraries is covered
in ``tests/via_ludus/utils/test_optional_dependencies.py``.
"""

import copy
import gzip
import io
import json
import math
import warnings

import numpy as np
import pytest

from via_ludus.board import PlayerColor
from via_ludus.tournament import TournamentResults


R = PlayerColor.RED
B = PlayerColor.BLUE
NAN = float("nan")


# ---------------------------------------------------------------------
# Construction, accumulation, filtering and persistence
# ---------------------------------------------------------------------


class TestResultsConstruction:
	def test_players_keep_their_order(self):
		assert TournamentResults(["b", "a", "c"]).players == ("b", "a", "c")

	def test_duplicate_players_are_dropped(self):
		assert TournamentResults(["a", "b", "a", "b", "c"]).players == ("a", "b", "c")

	def test_accepts_any_iterable(self):
		assert TournamentResults(iter(["a", "b"])).players == ("a", "b")
		assert TournamentResults({"a": 1, "b": 2}).players == ("a", "b")

	def test_players_are_immutable(self):
		assert isinstance(TournamentResults(["a"]).players, tuple)

	def test_starts_empty(self):
		results = TournamentResults(["a", "b"])

		assert results.total_games == 0
		assert results.deterministic_games == 0
		assert results.deterministic_game_rate == 0.0
		assert list(results) == []


class TestAddMatchupResult:
	def test_records_one_game(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_result("a", "b", R, 12, True)

		assert results.get_matchup_results("a", "b") == (R,)
		assert results.get_matchup_moves("a", "b") == (12,)
		assert results.get_matchup_determinism("a", "b") == (True,)

	def test_games_accumulate_in_order(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_result("a", "b", R, 12, True)
		results.add_matchup_result("a", "b", B, 9, False)

		assert results.get_matchup_results("a", "b") == (R, B)
		assert results.get_matchup_moves("a", "b") == (12, 9)
		assert results.get_matchup_determinism("a", "b") == (True, False)

	def test_orientations_are_separate_matchups(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_result("a", "b", R, 12, True)

		assert results.get_matchup_count("a", "b") == 1
		assert results.get_matchup_count("b", "a") == 0

	def test_a_player_can_play_itself(self):
		results = TournamentResults(["a"])

		results.add_matchup_result("a", "a", B, 7, True)

		assert results.get_matchup_count("a", "a") == 1

	@pytest.mark.parametrize("red, blue", [("x", "b"), ("a", "x"), ("x", "y")])
	def test_unknown_players_are_rejected(self, red, blue):
		results = TournamentResults(["a", "b"])

		with pytest.raises(ValueError, match="is not in the list of agents"):
			results.add_matchup_result(red, blue, R, 1, True)

		assert results.total_games == 0

	@pytest.mark.parametrize("result", ["red", None, 1, "Red"])
	def test_invalid_results_are_rejected(self, result):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError):
			results.add_matchup_result("a", "b", result, 1, True)

	@pytest.mark.parametrize("move", [1.5, "3", None, True, False])
	def test_invalid_move_counts_are_rejected(self, move):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="move must be an integer"):
			results.add_matchup_result("a", "b", R, move, True)

	@pytest.mark.parametrize("deterministic", [1, 0, "True", None, np.bool_(True)])
	def test_invalid_determinism_flags_are_rejected(self, deterministic):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="deterministic must be a bool"):
			results.add_matchup_result("a", "b", R, 1, deterministic)

	def test_nothing_is_recorded_when_validation_fails(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError):
			results.add_matchup_result("a", "b", R, 1, "yes")

		assert results.get_matchup_count("a", "b") == 0


class TestAddMatchupData:
	def test_records_many_games(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_data("a", "b", [R, B, R], [5, 6, 7], [True, False, True])

		assert results.get_matchup_results("a", "b") == (R, B, R)
		assert results.get_matchup_moves("a", "b") == (5, 6, 7)
		assert results.get_matchup_determinism("a", "b") == (True, False, True)

	def test_accepts_tuples(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_data("a", "b", (R, B), (5, 6), (True, False))

		assert results.get_matchup_count("a", "b") == 2

	def test_data_is_appended_to_existing_games(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_data("a", "b", [R], [5], [True])
		results.add_matchup_data("a", "b", [B, B], [6, 7], [False, False])

		assert results.get_matchup_results("a", "b") == (R, B, B)
		assert results.get_matchup_moves("a", "b") == (5, 6, 7)

	def test_empty_data_is_allowed(self):
		results = TournamentResults(["a", "b"])

		results.add_matchup_data("a", "b", [], [], [])

		assert results.total_games == 0

	def test_the_given_lists_are_not_kept(self):
		results = TournamentResults(["a", "b"])
		outcomes = [R]

		results.add_matchup_data("a", "b", outcomes, [5], [True])
		outcomes.append(B)

		assert results.get_matchup_results("a", "b") == (R,)

	def test_unknown_players_are_rejected(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(ValueError, match="is not in the list of agents"):
			results.add_matchup_data("a", "x", [R], [5], [True])

	@pytest.mark.parametrize("results_value", ["rr", None, {R}, R])
	def test_results_must_be_a_list_or_tuple(self, results_value):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="results must be a list or tuple"):
			results.add_matchup_data("a", "b", results_value, [5], [True])

	@pytest.mark.parametrize("moves", ["5", None, {5}, 5])
	def test_moves_must_be_a_list_or_tuple(self, moves):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="moves must be a list or tuple"):
			results.add_matchup_data("a", "b", [R], moves, [True])

	def test_every_result_must_be_a_player_color(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError):
			results.add_matchup_data("a", "b", [R, "blue"], [5, 6], [True, True])

	@pytest.mark.parametrize("moves", [[5, 6.0], [5, "6"], [5, True]])
	def test_every_move_count_must_be_an_integer(self, moves):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="every move must be an integer"):
			results.add_matchup_data("a", "b", [R, B], moves, [True, True])

	def test_results_and_moves_must_have_the_same_length(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(ValueError, match="results and moves must have the same length"):
			results.add_matchup_data("a", "b", [R, B], [5], [True, True])

	@pytest.mark.parametrize("deterministic", ["TT", None, True])
	def test_determinism_data_must_be_a_list_or_tuple(self, deterministic):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="deterministic must be a list or tuple"):
			results.add_matchup_data("a", "b", [R], [5], deterministic)

	def test_every_determinism_flag_must_be_a_bool(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(TypeError, match="deterministic must be a bool"):
			results.add_matchup_data("a", "b", [R, B], [5, 6], [True, 1])

	def test_determinism_data_must_have_the_same_length(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(ValueError, match="same length"):
			results.add_matchup_data("a", "b", [R, B], [5, 6], [True])

	def test_nothing_is_recorded_when_validation_fails(self):
		results = TournamentResults(["a", "b"])

		with pytest.raises(ValueError):
			results.add_matchup_data("a", "b", [R, B], [5, 6], [True])

		assert results.get_matchup_count("a", "b") == 0


class TestAddTournamentData:
	def test_merges_games(self):
		first = TournamentResults(["a", "b"])
		second = TournamentResults(["a", "b"])
		first.add_matchup_data("a", "b", [R], [5], [True])
		second.add_matchup_data("a", "b", [B], [6], [False])
		second.add_matchup_data("b", "a", [R], [7], [True])

		first.add_tournament_data(second)

		assert first.get_matchup_results("a", "b") == (R, B)
		assert first.get_matchup_moves("a", "b") == (5, 6)
		assert first.get_matchup_determinism("a", "b") == (True, False)
		assert first.get_matchup_results("b", "a") == (R,)
		assert first.total_games == 3

	def test_new_players_are_added_after_the_existing_ones(self):
		first = TournamentResults(["a", "b"])
		second = TournamentResults(["c", "a", "d"])

		first.add_tournament_data(second)

		assert first.players == ("a", "b", "c", "d")

	def test_other_results_are_not_modified(self, sample_results):
		other = copy.deepcopy(sample_results.to_json())
		target = TournamentResults(["alpha", "beta", "gamma"])

		target.add_tournament_data(sample_results)
		target.add_matchup_result("alpha", "beta", R, 1, True)

		assert sample_results.to_json() == other

	def test_later_changes_to_the_other_results_are_not_shared(self):
		target = TournamentResults(["a", "b"])
		other = TournamentResults(["a", "b"])
		other.add_matchup_result("a", "b", R, 5, True)

		target.add_tournament_data(other)
		other.add_matchup_result("a", "b", B, 6, True)

		assert target.get_matchup_count("a", "b") == 1

	def test_an_empty_tournament_can_be_merged(self):
		target = TournamentResults(["a"])

		target.add_tournament_data(TournamentResults(["a"]))

		assert target.total_games == 0

	@pytest.mark.parametrize("other", [None, "results", {"players": []}, [("a", "b")]])
	def test_other_must_be_tournament_results(self, other):
		with pytest.raises(TypeError, match="other must be a TournamentResults instance"):
			TournamentResults(["a"]).add_tournament_data(other)


class TestMatchupAccessors:
	def test_missing_matchup_is_empty(self):
		results = TournamentResults(["a", "b"])

		assert results.get_matchup_results("a", "b") == ()
		assert results.get_matchup_moves("a", "b") == ()
		assert results.get_matchup_determinism("a", "b") == ()
		assert results.get_matchup_count("a", "b") == 0

	def test_get_matchup_data(self, sample_results):
		assert sample_results.get_matchup_data("alpha", "gamma") == {
			"results": (B, B),
			"moves": (20, 22),
			"deterministic": (True, True),
		}

	def test_returned_data_is_immutable(self, sample_results):
		data = sample_results.get_matchup_data("alpha", "beta")

		assert all(isinstance(value, tuple) for value in data.values())

	def test_reading_a_missing_matchup_does_not_create_it(self):
		results = TournamentResults(["a", "b"])

		results.get_matchup_data("a", "b")

		assert list(results) == []

	def test_counts(self, sample_results):
		assert sample_results.get_matchup_count("alpha", "beta") == 4
		assert sample_results.get_matchup_count("beta", "alpha") == 3
		assert sample_results.get_matchup_count("beta", "gamma") == 0

	@pytest.mark.parametrize("method", ["get_matchup_results", "get_matchup_moves", "get_matchup_determinism", "get_matchup_data", "get_matchup_count"])
	def test_unknown_players_are_rejected(self, sample_results, method):
		with pytest.raises(ValueError, match="is not in the list of agents"):
			getattr(sample_results, method)("alpha", "unknown")


class TestTotals:
	def test_total_games(self, sample_results):
		assert sample_results.total_games == 10

	def test_deterministic_games(self, sample_results):
		assert sample_results.deterministic_games == 6

	def test_deterministic_game_rate(self, sample_results):
		assert sample_results.deterministic_game_rate == pytest.approx(0.6)

	def test_rate_is_zero_without_games(self):
		assert TournamentResults(["a"]).deterministic_game_rate == 0.0


class TestFilterAndTruncate:
	def test_keeps_the_requested_players_and_games(self, full_results):
		filtered = full_results.filter_and_truncate(["a", "b"], 2)

		assert filtered.players == ("a", "b")
		assert filtered.get_matchup_results("a", "b") == (R, B)
		assert filtered.get_matchup_moves("a", "b") == (9, 8)
		assert filtered.get_matchup_determinism("a", "b") == (True, False)
		assert filtered.get_matchup_results("b", "a") == (B, B)
		assert filtered.total_games == 8

	def test_keeps_all_games_when_the_limit_equals_the_count(self, full_results):
		filtered = full_results.filter_and_truncate(["a", "b"], 3)

		assert filtered.to_json()["matchups"] == full_results.to_json()["matchups"]

	def test_players_can_be_reordered_and_selected(self, full_results):
		filtered = full_results.filter_and_truncate(["b"], 1)

		assert filtered.players == ("b",)
		assert filtered.get_matchup_results("b", "b") == (B,)
		assert filtered.total_games == 1

	def test_player_order_is_taken_from_the_argument(self, full_results):
		assert full_results.filter_and_truncate(["b", "a"], 1).players == ("b", "a")

	def test_original_results_are_unchanged(self, full_results):
		before = copy.deepcopy(full_results.to_json())

		full_results.filter_and_truncate(["a", "b"], 1)

		assert full_results.to_json() == before

	def test_accepts_any_iterable_of_players(self, full_results):
		assert full_results.filter_and_truncate(iter(["a", "b"]), 1).players == ("a", "b")

	def test_duplicate_players_are_rejected(self, full_results):
		with pytest.raises(ValueError, match="Players must be unique"):
			full_results.filter_and_truncate(["a", "a"], 1)

	def test_numpy_integers_are_valid_game_limits(self, full_results):
		import numpy as np

		filtered = full_results.filter_and_truncate(["a", "b"], np.int64(2))

		assert filtered.total_games == 8

	@pytest.mark.parametrize("num_games", [0, -1, 1.5, "2", True, None])
	def test_invalid_game_limits_are_rejected(self, full_results, num_games):
		with pytest.raises(ValueError, match="num_games must be a positive integer"):
			full_results.filter_and_truncate(["a", "b"], num_games)

	def test_missing_pairings_are_rejected(self, sample_results):
		with pytest.raises(ValueError, match="Missing results for player pairings"):
			sample_results.filter_and_truncate(["alpha", "beta"], 1)

	def test_pairings_with_too_few_games_are_rejected(self, full_results):
		with pytest.raises(ValueError, match="has 3 games; at least 4 are required"):
			full_results.filter_and_truncate(["a", "b"], 4)

	def test_players_without_results_are_rejected(self, full_results):
		with pytest.raises(ValueError, match="Missing results"):
			full_results.filter_and_truncate(["a", "zzz"], 1)


class TestRemoveAndRetainPlayers:
	def test_remove_players_drops_the_players_and_their_matchups(self, sample_results):
		filtered = sample_results.remove_players(["gamma"])

		assert filtered.players == ("alpha", "beta")
		assert filtered.total_games == 7

		with pytest.raises(ValueError):
			filtered.get_matchup_results("alpha", "gamma")

	def test_retain_players_keeps_only_the_players_and_their_matchups(self, sample_results):
		filtered = sample_results.retain_players(["alpha", "beta"])

		assert filtered.players == ("alpha", "beta")
		assert filtered.total_games == 7

	def test_remove_and_retain_are_complementary(self, sample_results):
		removed = sample_results.remove_players(["gamma"])
		retained = sample_results.retain_players(["alpha", "beta"])

		assert removed.to_json() == retained.to_json()

	def test_matchup_data_is_preserved(self, sample_results):
		filtered = sample_results.retain_players(["alpha", "beta"])

		assert filtered.get_matchup_data("alpha", "beta") == sample_results.get_matchup_data("alpha", "beta")
		assert filtered.get_matchup_results("alpha", "beta") == (R, R, B, R)
		assert filtered.get_matchup_moves("alpha", "beta") == (10, 12, 9, 14)
		assert filtered.get_matchup_determinism("alpha", "beta") == (True, True, False, False)

	def test_matchups_between_two_retained_players_survive(self, sample_results):
		filtered = sample_results.retain_players(["alpha", "gamma"])

		assert filtered.players == ("alpha", "gamma")
		assert filtered.total_games == 2
		assert filtered.get_matchup_results("alpha", "gamma") == (B, B)

	def test_players_keep_their_original_order(self, sample_results):
		assert sample_results.retain_players(["gamma", "alpha"]).players == ("alpha", "gamma")
		assert sample_results.remove_players(["beta"]).players == ("alpha", "gamma")

	def test_a_new_results_object_is_returned(self, sample_results):
		for filtered in (
			sample_results.remove_players([]),
			sample_results.retain_players(["alpha", "beta", "gamma"]),
		):
			assert filtered is not sample_results
			assert filtered.to_json() == sample_results.to_json()

	def test_original_results_are_unchanged(self, sample_results):
		before = copy.deepcopy(sample_results.to_json())

		sample_results.remove_players(["gamma"])
		sample_results.retain_players(["alpha"])

		assert sample_results.to_json() == before

	def test_filtered_results_are_independent_of_the_original(self, sample_results):
		filtered = sample_results.retain_players(["alpha", "beta"])

		filtered.add_matchup_result("alpha", "beta", R, 5, True)

		assert sample_results.get_matchup_count("alpha", "beta") == 4
		assert filtered.get_matchup_count("alpha", "beta") == 5

	def test_accepts_any_iterable_of_players(self, sample_results):
		assert sample_results.remove_players(iter(["gamma"])).players == ("alpha", "beta")
		assert sample_results.retain_players(iter(["alpha"])).players == ("alpha",)
		assert sample_results.retain_players(("alpha", "beta")).players == ("alpha", "beta")

	def test_removing_every_player_leaves_nothing(self, sample_results):
		filtered = sample_results.remove_players(["alpha", "beta", "gamma"])

		assert filtered.players == ()
		assert filtered.total_games == 0

	def test_retaining_no_players_leaves_nothing(self, sample_results):
		filtered = sample_results.retain_players([])

		assert filtered.players == ()
		assert filtered.total_games == 0

	@pytest.mark.parametrize("method", ["remove_players", "retain_players"])
	def test_duplicate_players_are_rejected(self, sample_results, method):
		with pytest.raises(ValueError, match="Players must be unique"):
			getattr(sample_results, method)(["alpha", "alpha"])

	def test_retaining_unknown_players_is_an_error(self, sample_results):
		with pytest.raises(ValueError, match="Players not found: zzz"):
			sample_results.retain_players(["alpha", "zzz"])

	def test_unknown_players_are_listed_in_sorted_order(self, sample_results):
		with pytest.raises(ValueError, match="Players not found: x, y"):
			sample_results.retain_players(["y", "alpha", "x"])

	def test_removing_unknown_players_only_warns(self, sample_results):
		with pytest.warns(UserWarning, match="Players not found: zzz"):
			filtered = sample_results.remove_players(["gamma", "zzz"])

		assert filtered.players == ("alpha", "beta")

	def test_removing_only_unknown_players_keeps_everything(self, sample_results):
		with pytest.warns(UserWarning, match="Players not found: zzz"):
			filtered = sample_results.remove_players(["zzz"])

		assert filtered.to_json() == sample_results.to_json()

	def test_removing_known_players_does_not_warn(self, sample_results):
		with warnings.catch_warnings():
			warnings.simplefilter("error")

			sample_results.remove_players(["gamma"])


class TestJson:
	def test_structure(self, sample_results):
		data = sample_results.to_json()

		assert data["players"] == ["alpha", "beta", "gamma"]
		assert data["matchups"][0] == {
			"red_player": "alpha",
			"blue_player": "beta",
			"results": ["red", "red", "blue", "red"],
			"moves": [10, 12, 9, 14],
			"deterministic": [True, True, False, False],
		}
		assert len(data["matchups"]) == 4

	def test_results_are_plain_strings(self, sample_results):
		# PlayerColor is a str subclass that compares equal to "red", so the
		# exact type has to be checked to be sure the data is plain JSON.
		data = sample_results.to_json()

		assert all(
			type(value) is str
			for matchup in data["matchups"]
			for value in matchup["results"]
		)

	def test_is_json_serializable(self, sample_results):
		assert json.loads(json.dumps(sample_results.to_json())) == sample_results.to_json()

	def test_returns_a_copy(self, sample_results):
		data = sample_results.to_json()
		data["players"].append("intruder")
		data["matchups"][0]["moves"].append(999)

		assert sample_results.players == ("alpha", "beta", "gamma")
		assert sample_results.get_matchup_moves("alpha", "beta") == (10, 12, 9, 14)

	def test_empty_results(self):
		assert TournamentResults(["a", "b"]).to_json() == {
			"players": ["a", "b"],
			"matchups": [],
		}

	def test_round_trip(self, sample_results):
		restored = TournamentResults.from_json(sample_results.to_json())

		assert restored.to_json() == sample_results.to_json()
		assert restored.players == sample_results.players
		assert restored.total_games == sample_results.total_games

	def test_results_are_restored_as_player_colors(self, sample_results):
		restored = TournamentResults.from_json(sample_results.to_json())

		assert restored.get_matchup_results("alpha", "beta") == (R, R, B, R)
		assert all(isinstance(value, PlayerColor) for value in restored.get_matchup_results("alpha", "beta"))

	def test_matchup_order_is_preserved(self, sample_results):
		restored = TournamentResults.from_json(sample_results.to_json())

		assert [(red, blue) for red, blue, *_ in restored] == [
			("alpha", "beta"),
			("beta", "alpha"),
			("alpha", "gamma"),
			("gamma", "beta"),
		]

	def test_players_without_matchups_trigger_a_warning(self):
		data = {"players": ["a", "b", "c"], "matchups": []}

		with pytest.warns(UserWarning, match="no recorded matchups: a, b, c"):
			TournamentResults.from_json(data)

	def test_no_warning_when_every_player_has_a_matchup(self, sample_results):
		with warnings.catch_warnings():
			warnings.simplefilter("error")
			TournamentResults.from_json(sample_results.to_json())

	def test_matchups_with_unlisted_players_are_rejected(self):
		data = {
			"players": ["a"],
			"matchups": [{
				"red_player": "a",
				"blue_player": "ghost",
				"results": [],
				"moves": [],
				"deterministic": [],
			}],
		}

		with pytest.raises(ValueError, match="'ghost'"):
			TournamentResults.from_json(data)

	def test_invalid_result_values_are_rejected(self):
		data = {
			"players": ["a", "b"],
			"matchups": [{
				"red_player": "a",
				"blue_player": "b",
				"results": ["green"],
				"moves": [5],
				"deterministic": [True],
			}],
		}

		with pytest.raises(ValueError):
			TournamentResults.from_json(data)

	def test_inconsistent_lengths_are_rejected(self):
		data = {
			"players": ["a", "b"],
			"matchups": [{
				"red_player": "a",
				"blue_player": "b",
				"results": ["red", "blue"],
				"moves": [5],
				"deterministic": [True, True],
			}],
		}

		with pytest.raises(ValueError):
			TournamentResults.from_json(data)


class TestSaveAndLoad:
	def test_round_trip_through_a_json_file(self, sample_results, tmp_path):
		path = tmp_path / "results.json"

		sample_results.save(path)
		loaded = TournamentResults.load(path)

		assert loaded.to_json() == sample_results.to_json()

	def test_file_contents_are_plain_json(self, sample_results, tmp_path):
		path = tmp_path / "results.json"

		sample_results.save(path)

		assert json.loads(path.read_text(encoding="utf-8")) == sample_results.to_json()

	def test_paths_can_be_strings(self, sample_results, tmp_path):
		path = str(tmp_path / "results.json")

		sample_results.save(path)

		assert TournamentResults.load(path).to_json() == sample_results.to_json()

	def test_gz_files_are_compressed_automatically(self, sample_results, tmp_path):
		path = tmp_path / "results.json.gz"

		sample_results.save(path)

		assert path.read_bytes()[:2] == b"\x1f\x8b"
		with gzip.open(path, "rt", encoding="utf-8") as handle:
			assert json.load(handle) == sample_results.to_json()
		assert TournamentResults.load(path).to_json() == sample_results.to_json()

	def test_compression_can_be_forced(self, sample_results, tmp_path):
		path = tmp_path / "results.dat"

		sample_results.save(path, compressed=True)

		assert path.read_bytes()[:2] == b"\x1f\x8b"
		assert TournamentResults.load(path, compressed=True).to_json() == sample_results.to_json()

	def test_compression_can_be_disabled(self, sample_results, tmp_path):
		path = tmp_path / "results.json.gz"

		sample_results.save(path, compressed=False)

		assert json.loads(path.read_text(encoding="utf-8")) == sample_results.to_json()
		assert TournamentResults.load(path, compressed=False).to_json() == sample_results.to_json()

	def test_save_overwrites_an_existing_file(self, sample_results, tmp_path):
		path = tmp_path / "results.json"
		TournamentResults(["x"]).save(path)

		sample_results.save(path)

		assert TournamentResults.load(path).players == ("alpha", "beta", "gamma")

	def test_file_objects(self, sample_results):
		buffer = io.StringIO()

		sample_results.save(buffer)
		buffer.seek(0)
		loaded = TournamentResults.load(buffer)

		assert loaded.to_json() == sample_results.to_json()

	def test_loading_a_missing_file_fails(self, tmp_path):
		with pytest.raises(FileNotFoundError):
			TournamentResults.load(tmp_path / "missing.json")

	def test_loading_invalid_json_fails(self, tmp_path):
		path = tmp_path / "broken.json"
		path.write_text("{not json", encoding="utf-8")

		with pytest.raises(json.JSONDecodeError):
			TournamentResults.load(path)


class TestIterationAndRepresentation:
	def test_iteration_yields_matchups_in_insertion_order(self, sample_results):
		rows = list(sample_results)

		assert [(red, blue) for red, blue, *_ in rows] == [
			("alpha", "beta"),
			("beta", "alpha"),
			("alpha", "gamma"),
			("gamma", "beta"),
		]
		assert rows[0] == (
			"alpha",
			"beta",
			(R, R, B, R),
			(10, 12, 9, 14),
			(True, True, False, False),
		)

	def test_iteration_yields_immutable_data(self, sample_results):
		_, _, results, moves, deterministic = next(iter(sample_results))

		assert all(isinstance(value, tuple) for value in (results, moves, deterministic))

	def test_str(self, sample_results):
		assert str(sample_results) == "\n".join([
			"Tournament Results",
			"Players: alpha, beta, gamma",
			"Matchups: 4",
			"Games: 10",
			"Deterministic games: 6 (60.0%)",
			"  alpha vs beta: 4 games (Red wins: 3, Blue wins: 1, Deterministic: 2)",
			"  beta vs alpha: 3 games (Red wins: 1, Blue wins: 2, Deterministic: 1)",
			"  alpha vs gamma: 2 games (Red wins: 0, Blue wins: 2, Deterministic: 2)",
			"  gamma vs beta: 1 games (Red wins: 1, Blue wins: 0, Deterministic: 1)",
		])

	def test_str_without_games(self):
		assert str(TournamentResults(["a", "b"])) == "\n".join([
			"Tournament Results",
			"Players: a, b",
			"Matchups: 0",
			"Games: 0",
			"Deterministic games: 0 (0.0%)",
		])

	def test_repr(self, sample_results):
		assert repr(sample_results) == (
			"TournamentResults(players=['alpha', 'beta', 'gamma'], matchups=4)"
		)


# ---------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------


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


# ---------------------------------------------------------------------
# DataFrame views (optional pandas)
# ---------------------------------------------------------------------


@pytest.fixture
def pd():
	return pytest.importorskip("pandas")


PLAYERS = ["alpha", "beta", "gamma"]


class TestSummaryDataFrame:
	def test_is_a_data_frame_with_the_summary_columns(self, pd, sample_results):
		frame = sample_results.summary_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == list(sample_results.summary()[0])

	def test_rows_match_the_summary(self, sample_results):
		frame = sample_results.summary_df()

		assert frame.to_dict("records") == sample_results.summary()

	def test_rows_are_sorted_by_win_rate(self, sample_results):
		assert sample_results.summary_df()["player"].tolist() == ["gamma", "alpha", "beta"]

	def test_without_games(self, pd):
		frame = TournamentResults(["a", "b"]).summary_df()

		assert frame["player"].tolist() == ["a", "b"]
		assert (frame["total_games"] == 0).all()


class TestHeadToHeadDataFrame:
	def test_columns(self, pd, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert list(frame.columns) == list(sample_results.head_to_head_summary()[0])

	def test_rows_follow_the_player_order(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert list(zip(frame["red_player"], frame["blue_player"])) == [
			("alpha", "beta"),
			("alpha", "gamma"),
			("beta", "alpha"),
			("gamma", "beta"),
		]

	def test_player_columns_are_ordered_categoricals(self, pd, sample_results):
		frame = sample_results.head_to_head_summary_df()

		for column in ("red_player", "blue_player"):
			assert isinstance(frame[column].dtype, pd.CategoricalDtype)
			assert frame[column].cat.ordered is True
			assert list(frame[column].cat.categories) == PLAYERS

	def test_index_is_reset(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert frame.index.tolist() == [0, 1, 2, 3]

	def test_values_match_the_summary(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		for row, expected in zip(frame.to_dict("records"), sample_results.head_to_head_summary()):
			assert row.keys() == expected.keys()
			for key in expected:
				assert _same(row[key], expected[key]), key

	def test_without_games(self, pd):
		frame = TournamentResults(["a", "b"]).head_to_head_summary_df()

		assert frame.empty
		assert "red_win_rate" in frame.columns


class TestFirstMoveAdvantageDataFrame:
	def test_columns_and_rows(self, pd, full_results):
		frame = full_results.first_move_advantage_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == [
			"player",
			"num_games",
			"red_wins",
			"red_win_rate",
			"blue_wins",
			"blue_win_rate",
		]
		assert frame.to_dict("records") == full_results.first_move_advantage()

	def test_without_self_play(self, pd, sample_results):
		frame = sample_results.first_move_advantage_df()

		assert frame.empty
		assert "red_win_rate" in frame.columns


class TestMatrixDataFrames:
	@pytest.mark.parametrize("method", ["red_win_matrix_df", "blue_win_matrix_df", "win_matrix_df"])
	@pytest.mark.parametrize("rates", [True, False])
	def test_shape_index_and_columns(self, pd, sample_results, method, rates):
		frame = getattr(sample_results, method)(rates=rates)

		assert isinstance(frame, pd.DataFrame)
		assert frame.index.tolist() == PLAYERS
		assert frame.columns.tolist() == PLAYERS

	@pytest.mark.parametrize(
		"method, matrix_method",
		[
			("red_win_matrix_df", "red_win_matrix"),
			("blue_win_matrix_df", "blue_win_matrix"),
			("win_matrix_df", "win_matrix"),
		],
	)
	@pytest.mark.parametrize("rates", [True, False])
	def test_values_match_the_dictionaries(self, sample_results, method, matrix_method, rates):
		frame = getattr(sample_results, method)(rates=rates)
		matrix = getattr(sample_results, matrix_method)(rates=rates)

		for row in PLAYERS:
			for col in PLAYERS:
				assert _same(float(frame.loc[row, col]), matrix[row][col]), (row, col)

	def test_rates_default_to_true(self, sample_results):
		assert sample_results.red_win_matrix_df().loc["alpha", "beta"] == pytest.approx(0.75)

	def test_cells_without_games_are_nan(self, pd, sample_results):
		frame = sample_results.red_win_matrix_df()

		assert pd.isna(frame.loc["alpha", "alpha"])
		assert pd.isna(frame.loc["beta", "gamma"])
		assert frame.loc["gamma", "beta"] == pytest.approx(1.0)

	def test_blue_matrix_rows_are_the_blue_players(self, sample_results):
		frame = sample_results.blue_win_matrix_df()

		assert frame.loc["beta", "alpha"] == pytest.approx(0.25)

	def test_overall_matrix(self, sample_results):
		frame = sample_results.win_matrix_df()

		assert frame.loc["alpha", "beta"] == pytest.approx(5 / 7)
		assert frame.loc["beta", "alpha"] == pytest.approx(2 / 7)

	def test_matrices_without_games_are_all_nan(self, pd):
		frame = TournamentResults(["a", "b"]).win_matrix_df()

		assert frame.isna().all().all()
		assert frame.index.tolist() == ["a", "b"]

	@pytest.mark.parametrize("rates", [True, False])
	def test_win_matrices_df(self, pd, sample_results, rates):
		frames = sample_results.win_matrices_df(rates=rates)

		assert len(frames) == 3
		assert all(isinstance(frame, pd.DataFrame) for frame in frames)
		red, blue, overall = frames
		for row in PLAYERS:
			for col in PLAYERS:
				assert _same(float(red.loc[row, col]), sample_results.win_matrices(rates=rates)[0][row][col])
				assert _same(float(blue.loc[row, col]), sample_results.win_matrices(rates=rates)[1][row][col])
				assert _same(float(overall.loc[row, col]), sample_results.win_matrices(rates=rates)[2][row][col])


class TestEloDataFrame:
	def test_columns(self, pd, sample_results):
		frame = sample_results.elo_ratings_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == ["player", "elo", "games_played"]

	def test_rows_match_the_ratings(self, sample_results):
		assert sample_results.elo_ratings_df().to_dict("records") == sample_results.elo_ratings()

	def test_parameters_are_forwarded(self, sample_results):
		frame = sample_results.elo_ratings_df(initial_rating=1000, k_factor=16, seed=3)

		assert frame.to_dict("records") == sample_results.elo_ratings(
			initial_rating=1000,
			k_factor=16,
			seed=3,
		)

	def test_invalid_k_factor_is_rejected(self, sample_results):
		with pytest.raises(ValueError, match="k_factor must be positive"):
			sample_results.elo_ratings_df(k_factor=0)


class TestWithoutPandas:
	"""These tests run whether or not pandas is installed."""

	@pytest.mark.parametrize(
		"method",
		[
			"summary_df",
			"head_to_head_summary_df",
			"red_win_matrix_df",
			"blue_win_matrix_df",
			"win_matrix_df",
			"win_matrices_df",
			"elo_ratings_df",
			"first_move_advantage_df",
		],
	)
	def test_every_data_frame_method_explains_the_missing_dependency(self, block_imports, sample_results, method):
		from via_ludus.utils import OptionalDependencyError

		block_imports("pandas")

		with pytest.raises(OptionalDependencyError) as excinfo:
			getattr(sample_results, method)()

		assert "pandas" in str(excinfo.value)
		assert 'pip install -e ".[dataframe]"' in str(excinfo.value)

	def test_the_plain_methods_work_without_pandas(self, block_imports, full_results):
		block_imports("pandas")

		assert full_results.first_move_advantage()
		assert full_results.summary()


# ---------------------------------------------------------------------
# Win-matrix plots (optional matplotlib)
# ---------------------------------------------------------------------


PLOTS = [
	pytest.param(
		("plot_red_win_matrix", "Red Win Rate", "Blue Player", "Red Player", {"75%", "0%", "33%", "100%"}, "Reds"),
		id="red",
	),
	pytest.param(
		("plot_blue_win_matrix", "Blue Win Rate", "Red Player", "Blue Player", {"25%", "67%", "100%", "0%"}, "Blues"),
		id="blue",
	),
	pytest.param(
		("plot_win_matrix", "Overall Win Rate", "Opponent", "Player", {"71%", "29%", "0%", "100%"}, "RdYlGn"),
		id="overall",
	),
]


@pytest.fixture(params=PLOTS)
def plot(request):
	return request.param


class TestWinMatrixPlots:
	def test_labels_and_title(self, plt, sample_results, plot):
		method, title, xlabel, ylabel, _, _ = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.get_title() == title
		assert ax.get_xlabel() == xlabel
		assert ax.get_ylabel() == ylabel

	def test_axes_are_labelled_with_the_players(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert [label.get_text() for label in ax.get_xticklabels()] == ["alpha", "beta", "gamma"]
		assert [label.get_text() for label in ax.get_yticklabels()] == ["alpha", "beta", "gamma"]

	def test_every_cell_with_games_is_annotated(self, plt, sample_results, plot):
		method, _, _, _, labels, _ = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert {text.get_text() for text in ax.texts} == labels

	def test_cells_without_games_are_not_annotated(self, plt, sample_results):
		_, _, ax = sample_results.plot_red_win_matrix(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 4

		_, _, ax = sample_results.plot_win_matrix(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 6

	def test_color_scale_is_fixed_to_zero_and_one(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.images[0].get_clim() == (0.0, 1.0)

	def test_image_holds_the_win_rates(self, plt, sample_results):
		_, _, ax = sample_results.plot_red_win_matrix(show=False, close=True, return_fig=True)
		data = ax.images[0].get_array()

		assert data.shape == (3, 3)
		assert data[0][1] == pytest.approx(0.75)
		assert data[2][1] == pytest.approx(1.0)

	def test_has_a_colorbar(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert len(fig.axes) == 2
		assert fig.axes[1].get_ylabel() == "Win rate"
		assert [label.get_text() for label in fig.axes[1].get_yticklabels()] == ["0%", "25%", "50%", "75%", "100%"]

	def test_default_color_maps(self, plt, sample_results, plot):
		method, _, _, _, _, cmap = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.images[0].get_cmap().name == cmap

	def test_custom_color_map(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(cmap="viridis", show=False, close=True, return_fig=True)

		assert ax.images[0].get_cmap().name == "viridis"

	def test_draws_on_a_given_axes(self, plt, sample_results, plot):
		method, title, *_ = plot
		fig, ax = plt.subplots()

		result = getattr(sample_results, method)(ax=ax)

		assert result is None
		assert ax.get_title() == title
		assert len(ax.images) == 1
		assert plt.fignum_exists(fig.number)

	def test_a_given_axes_is_not_closed(self, plt, sample_results, plot):
		method = plot[0]
		fig, ax = plt.subplots()

		getattr(sample_results, method)(ax=ax, show=True, close=True)

		assert plt.fignum_exists(fig.number)

	def test_the_created_figure_is_closed_on_request(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert not plt.fignum_exists(fig.number)

	def test_the_created_figure_stays_open_by_default(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, return_fig=True)

		assert plt.fignum_exists(fig.number)

	def test_plots_results_without_games(self, plt, plot):
		from via_ludus.tournament import TournamentResults

		method = plot[0]

		_, _, ax = getattr(TournamentResults(["a", "b"]), method)(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 0
