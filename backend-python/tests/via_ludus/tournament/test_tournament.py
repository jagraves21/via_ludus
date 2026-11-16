import gzip
import itertools
import warnings

import pytest

from via_ludus.board import PlayerColor, SearchBoard, UnionFindBoard
from via_ludus.tournament import (
	Game,
	RoundRobinTournament,
	TournamentResults,
)


R = PlayerColor.RED
B = PlayerColor.BLUE
NAMES = ("first", "last")


@pytest.fixture(autouse=True)
def quiet_progress(patched_tqdm):
	"""Never draw real progress bars in these tests."""
	return patched_tqdm


@pytest.fixture
def players(deterministic_first_move_player_class, deterministic_last_move_player_class):
	return {
		"first": deterministic_first_move_player_class,
		"last": deterministic_last_move_player_class,
	}


@pytest.fixture
def make_tournament(players):
	def _make_tournament(num_games_per_color=3, **kwargs):
		kwargs.setdefault("board", SearchBoard(size=5))

		return RoundRobinTournament(players, num_games_per_color, **kwargs)

	return _make_tournament


@pytest.fixture
def partial_results():
	"""Two games of 'first' (red) against 'last' (blue)."""
	results = TournamentResults(NAMES)
	results.add_matchup_data("first", "last", [R, B], [5, 6], [True, True])

	return results


class TestConstruction:
	def test_properties(self, make_tournament, players):
		tournament = make_tournament(4)

		assert tournament.players == players
		assert tournament.num_games_per_color == 4
		assert isinstance(tournament.results, TournamentResults)
		assert tournament.results.players == NAMES
		assert tournament.results.total_games == 0

	def test_players_property_returns_a_copy(self, make_tournament):
		tournament = make_tournament()

		tournament.players.clear()

		assert set(tournament.players) == set(NAMES)

	def test_the_given_players_are_copied(self, players):
		tournament = RoundRobinTournament(players, 1, board=SearchBoard(size=5))

		players["extra"] = players["first"]

		assert set(tournament.players) == set(NAMES)

	@pytest.mark.parametrize("value", [None, [], "players", {}, [("a", object)], 1])
	def test_players_must_be_a_non_empty_dictionary(self, value):
		with pytest.raises(TypeError, match="players must be a non-empty dictionary"):
			RoundRobinTournament(value, 1)

	@pytest.mark.parametrize("name", ["", 1, None, ("a",)])
	def test_player_names_must_be_non_empty_strings(self, first_move_player_class, name):
		with pytest.raises(ValueError, match="non-empty string"):
			RoundRobinTournament({name: first_move_player_class}, 1)

	@pytest.mark.parametrize("value", [int, "player", None, 1])
	def test_players_must_be_player_classes(self, first_move_player_class, value):
		with pytest.raises(TypeError):
			RoundRobinTournament({"a": first_move_player_class, "b": value}, 1)

	def test_player_instances_are_rejected(self, first_move_player_class):
		instance = first_move_player_class(R)

		with pytest.raises(TypeError, match="Expected a Player subclass"):
			RoundRobinTournament({"a": instance}, 1)

	@pytest.mark.parametrize("value", [0, -1, 1.5, "2", None, True, False])
	def test_games_per_color_must_be_a_positive_integer(self, players, value):
		with pytest.raises(ValueError, match="num_games_per_color must be a positive integer"):
			RoundRobinTournament(players, value)

	def test_numpy_integers_are_accepted_as_the_number_of_games(self, players):
		import numpy as np

		tournament = RoundRobinTournament(players, np.int64(2), board=SearchBoard(size=5))

		assert tournament.total_expected_games == 8

	@pytest.mark.parametrize("results", ["results", 1, {"players": []}, [], TournamentResults, object()])
	def test_loaded_results_must_be_tournament_results(self, players, results):
		with pytest.raises(TypeError, match="Expected a TournamentResults"):
			RoundRobinTournament(players, 1, board=SearchBoard(size=5), results=results)

	def test_invalid_results_are_reported_before_anything_else_is_done(self, players):
		with pytest.raises(TypeError, match="got str"):
			RoundRobinTournament(players, 1, results="results")

	def test_invalid_starting_color_is_rejected(self, players):
		with pytest.raises(TypeError):
			RoundRobinTournament(players, 1, starting_color="red")

	def test_invalid_board_is_rejected(self, players):
		with pytest.raises(TypeError):
			RoundRobinTournament(players, 1, board="board")

	def test_a_single_player_is_enough(self, deterministic_first_move_player_class):
		tournament = RoundRobinTournament(
			{"only": deterministic_first_move_player_class},
			2,
			board=SearchBoard(size=5),
		)

		assert list(tournament.expected_matchups) == [("only", "only")]
		assert tournament.total_expected_games == 2


class TestMatchupBookkeeping:
	def test_expected_matchups_are_all_ordered_pairs(self, make_tournament):
		assert list(make_tournament().expected_matchups) == list(itertools.product(NAMES, repeat=2))

	def test_total_expected_games(self, make_tournament):
		assert make_tournament(3).total_expected_games == 12
		assert make_tournament(5).total_expected_games == 20

	def test_a_new_tournament_has_nothing_completed(self, make_tournament):
		tournament = make_tournament(3)

		assert tournament.total_completed_games == 0
		assert tournament.total_remaining_games == 12
		assert tournament.is_complete is False
		assert list(tournament.completed_matchups) == []
		assert list(tournament.incomplete_matchups) == list(tournament.expected_matchups)

	def test_games_played_and_remaining(self, make_tournament, partial_results):
		tournament = make_tournament(3, results=partial_results)

		assert tournament.get_matchup_games_played("first", "last") == 2
		assert tournament.get_matchup_games_remaining("first", "last") == 1
		assert tournament.is_matchup_complete("first", "last") is False
		assert tournament.get_matchup_games_played("last", "first") == 0
		assert tournament.get_matchup_games_remaining("last", "first") == 3

	def test_loaded_results_count_towards_the_totals(self, make_tournament, partial_results):
		tournament = make_tournament(3, results=partial_results)

		assert tournament.total_completed_games == 2
		assert tournament.total_remaining_games == 10

	def test_a_matchup_is_complete_when_it_has_enough_games(self, make_tournament, partial_results):
		tournament = make_tournament(2, results=partial_results)

		assert tournament.is_matchup_complete("first", "last") is True
		assert list(tournament.completed_matchups) == [("first", "last")]
		assert ("first", "last") not in list(tournament.incomplete_matchups)

	def test_surplus_games_leave_nothing_remaining(self, make_tournament, partial_results):
		with pytest.warns(UserWarning):
			tournament = make_tournament(1, results=partial_results)

		assert tournament.get_matchup_games_remaining("first", "last") == 0
		assert tournament.is_matchup_complete("first", "last") is True

	def test_matchup_methods_reject_unknown_players(self, make_tournament):
		tournament = make_tournament()

		with pytest.raises(ValueError, match="is not in the list of agents"):
			tournament.get_matchup_games_played("first", "unknown")


class TestLoadedResults:
	def test_loaded_results_are_copied(self, make_tournament, partial_results):
		before = partial_results.to_json()
		tournament = make_tournament(3, results=partial_results)

		assert tournament.results is not partial_results

		tournament.run()

		assert partial_results.to_json() == before

	def test_results_for_unknown_players_trigger_a_warning(self, make_tournament):
		loaded = TournamentResults(["first", "ghost", "phantom"])

		with pytest.warns(UserWarning, match="not provided to this tournament: ghost, phantom"):
			make_tournament(3, results=loaded)

	def test_matchups_beyond_the_configured_games_trigger_a_warning(self, make_tournament, partial_results):
		with pytest.warns(UserWarning) as caught:
			make_tournament(1, results=partial_results)

		message = str(caught[0].message)

		assert "more games than the configured limit of 1" in message
		assert "first (red) vs last (blue): 2 games" in message

	def test_no_warning_for_matching_results(self, make_tournament, partial_results):
		with warnings.catch_warnings():
			warnings.simplefilter("error")
			make_tournament(3, results=partial_results)


class TestRun:
	def test_plays_every_matchup(self, make_tournament):
		tournament = make_tournament(3)

		tournament.run()

		for red, blue in itertools.product(NAMES, repeat=2):
			assert tournament.results.get_matchup_count(red, blue) == 3
		assert tournament.results.total_games == 12

	def test_the_tournament_is_complete_afterwards(self, make_tournament):
		tournament = make_tournament(3)

		tournament.run()

		assert tournament.is_complete is True
		assert tournament.total_remaining_games == 0
		assert tournament.total_completed_games == 12
		assert list(tournament.incomplete_matchups) == []
		assert list(tournament.completed_matchups) == list(tournament.expected_matchups)

	def test_returns_the_results(self, make_tournament):
		tournament = make_tournament(1)

		assert tournament.run() is tournament.results

	def test_results_use_the_dictionary_names(self, make_tournament):
		results = make_tournament(1).run()

		assert results.players == NAMES

	def test_results_match_independent_games(self, make_tournament, players):
		results = make_tournament(2).run()

		for red, blue in itertools.product(NAMES, repeat=2):
			game = Game(players[red], players[blue], board=SearchBoard(size=5))
			winner = game.play()

			assert results.get_matchup_results(red, blue) == (winner,) * 2
			assert results.get_matchup_moves(red, blue) == (game.move_count,) * 2

	def test_deterministic_players_give_deterministic_games(self, make_tournament):
		results = make_tournament(3).run()

		assert results.deterministic_games == 12
		assert results.deterministic_game_rate == 1.0

	def test_random_players_give_non_deterministic_games(self, random_move_player_class):
		tournament = RoundRobinTournament(
			{"x": random_move_player_class, "y": random_move_player_class},
			3,
			board=SearchBoard(size=5),
		)

		results = tournament.run()

		assert results.total_games == 12
		assert results.deterministic_games == 0

	def test_every_game_has_a_winner(self, make_tournament):
		results = make_tournament(3).run()

		for _, _, outcomes, moves, _ in results:
			assert set(outcomes) <= {R, B}
			assert all(move >= 1 for move in moves)

	def test_the_starting_color_is_used(self, deterministic_first_move_player_class):
		players = {"a": deterministic_first_move_player_class, "b": deterministic_first_move_player_class}
		tournament = RoundRobinTournament(players, 2, board=SearchBoard(size=3), starting_color=B)

		results = tournament.run()

		assert all(set(outcomes) == {B} for _, _, outcomes, _, _ in results)

	def test_red_starts_by_default(self, deterministic_first_move_player_class):
		players = {"a": deterministic_first_move_player_class, "b": deterministic_first_move_player_class}
		tournament = RoundRobinTournament(players, 2, board=SearchBoard(size=3))

		results = tournament.run()

		assert all(set(outcomes) == {R} for _, _, outcomes, _, _ in results)

	def test_the_given_board_is_used(self, make_tournament, players):
		results = make_tournament(1, board=UnionFindBoard(size=3)).run()

		assert all(moves == (1,) for _, _, _, moves, _ in results)

	def test_the_default_board_is_11x11(self, players):
		tournament = RoundRobinTournament(players, 1)
		game = Game(players["first"], players["last"])
		game.play()

		results = tournament.run()

		assert results.get_matchup_moves("first", "last") == (game.move_count,)

	def test_the_given_board_is_not_modified(self, players):
		board = SearchBoard(size=5)
		before = board.serialize()

		RoundRobinTournament(players, 2, board=board).run()

		assert board.serialize() == before

	def test_running_again_plays_nothing_more(self, make_tournament):
		tournament = make_tournament(2)
		tournament.run()
		before = tournament.results.to_json()

		tournament.run()

		assert tournament.results.to_json() == before

	def test_a_complete_tournament_plays_no_games(self, make_tournament, patched_tqdm):
		tournament = make_tournament(2)
		tournament.run()
		patched_tqdm.clear()

		tournament.run()

		assert patched_tqdm[0].init_kwargs["total"] == 0
		assert patched_tqdm[0].updates == 0

class TestSelfPlay:
	def test_a_player_plays_itself_in_a_single_matchup(self, make_tournament):
		matchups = list(make_tournament().expected_matchups)

		assert matchups.count(("first", "first")) == 1
		assert matchups.count(("last", "last")) == 1

	def test_self_play_gets_the_same_number_of_games_as_every_other_matchup(self, make_tournament):
		tournament = make_tournament(3)

		tournament.run()

		assert tournament.results.get_matchup_count("first", "first") == 3
		assert tournament.results.get_matchup_count("first", "last") == 3

	def test_every_player_has_the_same_number_of_games(self, make_tournament):
		results = make_tournament(3).run()

		# 2 players x 3 games per color x 2 colors against each of 2 opponents (including itself)
		assert {row["total_games"] for row in results.summary()} == {12}

	def test_every_player_has_the_same_number_of_games_per_color(self, make_tournament):
		results = make_tournament(3).run()

		assert {(row["red_games"], row["blue_games"]) for row in results.summary()} == {(6, 6)}

	def test_the_first_mover_advantage_is_reported_for_every_player(self, players):
		tournament = RoundRobinTournament(players, 3, board=SearchBoard(size=3))

		rows = tournament.run().first_move_advantage()

		# on the smallest board the player who moves first always wins
		assert [row["player"] for row in rows] == ["first", "last"]
		assert all(row["red_win_rate"] == 1.0 and row["num_games"] == 3 for row in rows)

	def test_ratings_are_conserved_with_self_play_included(self, make_tournament):
		ratings = make_tournament(3).run().elo_ratings()

		assert sum(row["elo"] for row in ratings) == pytest.approx(2 * 1500.0)
		assert {row["games_played"] for row in ratings} == {12}


class TestResume:
	def test_only_the_missing_games_are_played(self, make_tournament, partial_results, patched_tqdm):
		tournament = make_tournament(3, results=partial_results)

		tournament.run()

		assert patched_tqdm[0].init_kwargs["total"] == 10
		assert patched_tqdm[0].updates == 10
		assert tournament.results.total_games == 12

	def test_existing_games_are_kept_unchanged(self, make_tournament, partial_results):
		tournament = make_tournament(3, results=partial_results)

		tournament.run()

		assert tournament.results.get_matchup_results("first", "last")[:2] == (R, B)
		assert tournament.results.get_matchup_moves("first", "last")[:2] == (5, 6)
		assert tournament.results.get_matchup_count("first", "last") == 3

	def test_a_loaded_complete_tournament_has_nothing_to_play(self, make_tournament, patched_tqdm):
		complete = make_tournament(2).run()
		tournament = make_tournament(2, results=complete)

		tournament.run()

		assert tournament.is_complete is True
		assert patched_tqdm[-1].init_kwargs["total"] == 0

	def test_matchups_beyond_the_limit_are_not_extended(self, make_tournament, partial_results):
		with pytest.warns(UserWarning):
			tournament = make_tournament(1, results=partial_results)

		tournament.run()

		assert tournament.results.get_matchup_count("first", "last") == 2
		assert tournament.results.get_matchup_count("last", "first") == 1


class TestRunProgress:
	def test_progress_bar_settings(self, make_tournament, patched_tqdm):
		make_tournament(3).run()

		assert len(patched_tqdm) == 1
		assert patched_tqdm[0].init_kwargs == {
			"total": 12,
			"desc": "Round-Robin Tournament",
			"unit": "game",
		}

	def test_every_game_updates_the_progress(self, make_tournament, patched_tqdm):
		make_tournament(3).run()

		assert patched_tqdm[0].updates == 12

	def test_the_progress_bar_is_shared_by_all_matchups(self, make_tournament, patched_tqdm):
		make_tournament(2).run()

		assert len(patched_tqdm) == 1
		assert patched_tqdm[0].entered is True
		assert patched_tqdm[0].closed is True

	def test_the_progress_bar_is_closed_when_a_game_fails(self, players, first_move_player_class, patched_tqdm):
		class BrokenPlayer(first_move_player_class):
			def choose_move(self, board):
				raise RuntimeError("broken")

		tournament = RoundRobinTournament(
			{"first": players["first"], "boom": BrokenPlayer},
			1,
			board=SearchBoard(size=5),
		)

		with pytest.raises(RuntimeError, match="broken"):
			tournament.run()

		assert patched_tqdm[0].closed is True


class TestCheckpoints:
	def test_nothing_is_written_without_a_checkpoint_file(self, make_tournament, tmp_path):
		make_tournament(1).run()

		assert list(tmp_path.iterdir()) == []

	def test_the_final_checkpoint_holds_all_results(self, make_tournament, tmp_path):
		path = tmp_path / "checkpoint.json"
		tournament = make_tournament(2)

		tournament.run(checkpoint_file=path)

		assert TournamentResults.load(path).to_json() == tournament.results.to_json()

	@pytest.mark.parametrize("as_string", [False, True])
	def test_paths_and_strings_are_accepted(self, make_tournament, tmp_path, as_string):
		path = tmp_path / "checkpoint.json"

		make_tournament(1).run(checkpoint_file=str(path) if as_string else path)

		assert path.exists()

	def test_gz_checkpoints_are_compressed(self, make_tournament, tmp_path):
		path = tmp_path / "checkpoint.json.gz"
		tournament = make_tournament(1)

		tournament.run(checkpoint_file=path)

		assert path.read_bytes()[:2] == b"\x1f\x8b"
		with gzip.open(path, "rt", encoding="utf-8") as handle:
			assert handle.read().startswith("{")
		assert TournamentResults.load(path).total_games == 4

	def test_a_checkpoint_is_saved_before_playing_and_after_every_matchup(self, make_tournament, tmp_path, monkeypatch):
		tournament = make_tournament(2)
		saved = []
		monkeypatch.setattr(
			tournament.results,
			"save",
			lambda filename: saved.append((filename, tournament.results.total_games)),
		)

		tournament.run(checkpoint_file=tmp_path / "checkpoint.json")

		assert [games for _, games in saved] == [0, 2, 4, 6, 8]
		assert {filename for filename, _ in saved} == {tmp_path / "checkpoint.json"}

	def test_only_pending_matchups_are_saved_after_the_initial_checkpoint(self, make_tournament, partial_results, tmp_path, monkeypatch):
		tournament = make_tournament(2, results=partial_results)
		saved = []
		monkeypatch.setattr(tournament.results, "save", lambda filename: saved.append(filename))

		tournament.run(checkpoint_file=tmp_path / "checkpoint.json")

		# the initial checkpoint plus the three matchups that still had games to play
		assert len(saved) == 1 + 3

	def test_the_initial_checkpoint_is_written_even_when_there_is_nothing_to_play(self, make_tournament, tmp_path):
		complete = make_tournament(1).run()
		path = tmp_path / "checkpoint.json"

		make_tournament(1, results=complete).run(checkpoint_file=path)

		assert TournamentResults.load(path).total_games == 4

	def test_progress_survives_a_crash_and_can_be_resumed(self, players, first_move_player_class, tmp_path):
		class BrokenPlayer(first_move_player_class):
			def choose_move(self, board):
				raise RuntimeError("broken")

		path = tmp_path / "checkpoint.json"
		crashing = RoundRobinTournament(
			{"first": players["first"], "boom": BrokenPlayer},
			2,
			board=SearchBoard(size=5),
		)

		with pytest.raises(RuntimeError, match="broken"):
			crashing.run(checkpoint_file=path)

		# "boom" crashed before finishing any matchup, so the checkpoint has
		# no games for it and loading it warns.
		with pytest.warns(UserWarning, match="no recorded matchups: boom"):
			saved = TournamentResults.load(path)

		assert saved.get_matchup_count("first", "first") == 2
		assert saved.get_matchup_count("first", "boom") == 0

		resumed = RoundRobinTournament(
			{"first": players["first"], "boom": players["last"]},
			2,
			board=SearchBoard(size=5),
			results=saved,
		)
		resumed.run(checkpoint_file=path)

		assert resumed.is_complete is True
		assert resumed.results.get_matchup_results("first", "first") == saved.get_matchup_results("first", "first")
		assert TournamentResults.load(path).total_games == 8
