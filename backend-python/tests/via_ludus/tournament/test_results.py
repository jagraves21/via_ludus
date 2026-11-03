import copy
import gzip
import io
import json
import warnings

import numpy as np
import pytest

from via_ludus.board import PlayerColor
from via_ludus.tournament import TournamentResults


R = PlayerColor.RED
B = PlayerColor.BLUE


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
