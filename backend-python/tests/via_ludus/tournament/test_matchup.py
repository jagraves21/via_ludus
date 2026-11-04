import pytest

from via_ludus.board import PlayerColor, SearchBoard, UnionFindBoard
from via_ludus.tournament import (
	Game,
	TournamentResults,
	play_head_to_head,
	play_matchup,
)


R = PlayerColor.RED
B = PlayerColor.BLUE


def _expected_game(red, blue, **kwargs):
	game = Game(red, blue, **kwargs)
	winner = game.play()

	return winner, game.move_count


class TestPlayMatchup:
	def test_returns_tournament_results(self, deterministic_first_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert isinstance(results, TournamentResults)

	def test_players_are_named_after_their_classes(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			2,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert results.players == ("DeterministicFirstMovePlayer", "DeterministicLastMovePlayer")
		assert results.get_matchup_count("DeterministicFirstMovePlayer", "DeterministicLastMovePlayer") == 2

	def test_custom_names(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			2,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="first",
			blue_name="last",
		)

		assert results.players == ("first", "last")
		assert results.get_matchup_count("first", "last") == 2
		assert results.get_matchup_count("last", "first") == 0

	@pytest.mark.parametrize("num_games", [1, 2, 7])
	def test_plays_the_requested_number_of_games(self, random_move_player_class, recording_progress, num_games):
		results = play_matchup(
			random_move_player_class,
			random_move_player_class,
			num_games,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.total_games == num_games
		assert results.get_matchup_count("red", "blue") == num_games

	def test_zero_games_are_rejected(self, random_move_player_class, recording_progress):
		with pytest.raises(ValueError, match="num_games must be a positive integer"):
			play_matchup(
				random_move_player_class,
				random_move_player_class,
				0,
				board=SearchBoard(size=5),
				progress=recording_progress,
			)

		assert recording_progress.updates == 0
		assert recording_progress.postfixes == []

	@pytest.mark.parametrize("num_games", [0, -1, -3, 1.5, "2", None, True, False])
	def test_the_number_of_games_must_be_a_positive_integer(self, random_move_player_class, recording_progress, num_games):
		with pytest.raises(ValueError, match="num_games must be a positive integer"):
			play_matchup(
				random_move_player_class,
				random_move_player_class,
				num_games,
				board=SearchBoard(size=5),
				progress=recording_progress,
			)

		assert recording_progress.updates == 0

	def test_no_progress_bar_is_created_for_an_invalid_number_of_games(self, random_move_player_class, patched_tqdm):
		with pytest.raises(ValueError):
			play_matchup(random_move_player_class, random_move_player_class, -3, board=SearchBoard(size=5))

		assert patched_tqdm == []

	def test_numpy_integers_are_accepted(self, random_move_player_class, recording_progress):
		import numpy as np

		results = play_matchup(
			random_move_player_class,
			random_move_player_class,
			np.int64(3),
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_count("red", "blue") == 3

	def test_results_match_an_independent_game(self, deterministic_first_move_player_class, deterministic_last_move_player_class, board_type, recording_progress):
		expected_winner, expected_moves = _expected_game(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			board=board_type(size=7),
		)

		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			3,
			board=board_type(size=7),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_results("red", "blue") == (expected_winner,) * 3
		assert results.get_matchup_moves("red", "blue") == (expected_moves,) * 3

	def test_starting_color_is_used(self, deterministic_first_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=3),
			starting_color=B,
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_results("red", "blue") == (B, B)

	def test_red_starts_by_default(self, deterministic_first_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=3),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_results("red", "blue") == (R, R)

	def test_default_board_is_an_11x11_board(self, deterministic_first_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			1,
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)
		_, expected_moves = _expected_game(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
		)

		assert results.get_matchup_moves("red", "blue") == (expected_moves,)

	def test_the_given_board_is_not_modified(self, random_move_player_class, board_type, recording_progress):
		board = board_type(size=5)
		before = board.serialize()

		play_matchup(
			random_move_player_class,
			random_move_player_class,
			3,
			board=board,
			progress=recording_progress,
		)

		assert board.serialize() == before

	def test_games_can_start_from_a_position_in_progress(self, deterministic_first_move_player_class, board_type, red_winning_moves, make_board_from_moves, recording_progress):
		board = make_board_from_moves(red_winning_moves[:-1], board_type=board_type)
		expected_winner, expected_moves = _expected_game(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			board=board,
		)

		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=board,
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_results("red", "blue") == (expected_winner,) * 2
		assert results.get_matchup_moves("red", "blue") == (expected_moves,) * 2

	@pytest.mark.parametrize("which", ["red", "blue"])
	def test_player_instances_are_rejected(self, deterministic_first_move_player_class, recording_progress, which):
		instance = deterministic_first_move_player_class(R)
		arguments = {
			"red": (instance, deterministic_first_move_player_class),
			"blue": (deterministic_first_move_player_class, instance),
		}[which]

		with pytest.raises(TypeError):
			play_matchup(*arguments, 1, progress=recording_progress)


class TestMatchupDeterminism:
	def test_deterministic_players_are_flagged_as_deterministic(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			5,
			board=SearchBoard(size=7),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_determinism("red", "blue") == (True,) * 5
		assert results.deterministic_game_rate == 1.0

	def test_deterministic_matchup_is_played_only_once(self, deterministic_first_move_player_class, recording_progress):
		calls = []

		class CountingPlayer(deterministic_first_move_player_class):
			def choose_move(self, board):
				calls.append(self.color)

				return super().choose_move(board)

		expected_winner, expected_moves = _expected_game(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			board=SearchBoard(size=7),
		)

		results = play_matchup(
			CountingPlayer,
			CountingPlayer,
			10,
			board=SearchBoard(size=7),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert len(calls) == expected_moves
		assert results.total_games == 10
		assert set(results.get_matchup_results("red", "blue")) == {expected_winner}

	def test_non_deterministic_players_play_every_game(self, random_move_player_class, recording_progress):
		calls = []

		class CountingPlayer(random_move_player_class):
			def choose_move(self, board):
				calls.append(self.color)

				return super().choose_move(board)

		results = play_matchup(
			CountingPlayer,
			CountingPlayer,
			6,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert sum(results.get_matchup_moves("red", "blue")) == len(calls)
		assert results.get_matchup_determinism("red", "blue") == (False,) * 6

	def test_one_random_player_makes_every_game_non_deterministic(self, deterministic_first_move_player_class, random_move_player_class, recording_progress):
		results = play_matchup(
			deterministic_first_move_player_class,
			random_move_player_class,
			4,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_determinism("red", "blue") == (False,) * 4

	def test_scoring_players_with_non_deterministic_scores(self, index_scoring_player_class, recording_progress):
		results = play_matchup(
			index_scoring_player_class,
			index_scoring_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_determinism("red", "blue") == (False,) * 3

	def test_per_move_determinism_is_enough_for_a_deterministic_game(self, unique_best_random_scoring_player_class, recording_progress):
		results = play_matchup(
			unique_best_random_scoring_player_class,
			unique_best_random_scoring_player_class,
			4,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert results.get_matchup_determinism("red", "blue") == (True,) * 4
		assert len(set(results.get_matchup_results("red", "blue"))) == 1

	def test_recorded_moves_are_valid_game_lengths(self, random_move_player_class, board_type, recording_progress):
		results = play_matchup(
			random_move_player_class,
			random_move_player_class,
			10,
			board=board_type(size=5),
			progress=recording_progress,
			red_name="red",
			blue_name="blue",
		)

		assert all(1 <= moves <= 5 for moves in results.get_matchup_moves("red", "blue"))
		assert set(results.get_matchup_results("red", "blue")) <= {R, B}


class TestMatchupProgress:
	@pytest.mark.parametrize("num_games", [1, 5])
	def test_every_game_updates_the_given_progress(self, random_move_player_class, recording_progress, num_games):
		play_matchup(
			random_move_player_class,
			random_move_player_class,
			num_games,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert recording_progress.updates == num_games

	def test_deterministic_matchups_still_report_every_game(self, deterministic_first_move_player_class, recording_progress):
		play_matchup(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			8,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert recording_progress.updates == 8

	def test_postfix_shows_the_player_names(self, random_move_player_class, recording_progress):
		play_matchup(
			random_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			red_name="alice",
			blue_name="bob",
		)

		assert recording_progress.postfixes == [{"red": "alice", "blue": "bob"}] * 3

	def test_a_given_progress_is_not_closed(self, random_move_player_class, recording_progress):
		play_matchup(
			random_move_player_class,
			random_move_player_class,
			2,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert recording_progress.closed is False

	def test_a_given_progress_is_not_closed_when_a_game_fails(self, first_move_player_class, recording_progress):
		class BrokenPlayer(first_move_player_class):
			def choose_move(self, board):
				raise RuntimeError("broken")

		with pytest.raises(RuntimeError, match="broken"):
			play_matchup(
				BrokenPlayer,
				BrokenPlayer,
				2,
				board=SearchBoard(size=5),
				progress=recording_progress,
			)

		assert recording_progress.closed is False

	def test_creates_its_own_progress_when_none_is_given(self, random_move_player_class, patched_tqdm):
		play_matchup(
			random_move_player_class,
			random_move_player_class,
			4,
			board=SearchBoard(size=5),
		)

		assert len(patched_tqdm) == 1

		progress = patched_tqdm[0]

		assert progress.init_kwargs == {
			"total": 4,
			"desc": "Matchup",
			"unit": "game",
			"leave": False,
		}
		assert progress.updates == 4
		assert progress.closed is True

	def test_closes_its_own_progress_when_a_game_fails(self, first_move_player_class, patched_tqdm):
		class BrokenPlayer(first_move_player_class):
			def choose_move(self, board):
				raise RuntimeError("broken")

		with pytest.raises(RuntimeError, match="broken"):
			play_matchup(BrokenPlayer, BrokenPlayer, 2, board=SearchBoard(size=5))

		assert patched_tqdm[0].closed is True


class TestPlayHeadToHead:
	def test_plays_both_orientations(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			3,
			board=SearchBoard(size=7),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert results.players == ("a", "b")
		assert results.get_matchup_count("a", "b") == 3
		assert results.get_matchup_count("b", "a") == 3
		assert results.get_matchup_count("a", "a") == 0
		assert results.get_matchup_count("b", "b") == 0
		assert results.total_games == 6

	def test_default_names_come_from_the_classes(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			1,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert results.players == ("DeterministicFirstMovePlayer", "DeterministicLastMovePlayer")

	def test_each_player_plays_each_color(self, deterministic_first_move_player_class, deterministic_last_move_player_class, recording_progress):
		expected_ab = _expected_game(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			board=SearchBoard(size=7),
		)
		expected_ba = _expected_game(
			deterministic_last_move_player_class,
			deterministic_first_move_player_class,
			board=SearchBoard(size=7),
		)

		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_last_move_player_class,
			2,
			board=SearchBoard(size=7),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert results.get_matchup_results("a", "b") == (expected_ab[0],) * 2
		assert results.get_matchup_moves("a", "b") == (expected_ab[1],) * 2
		assert results.get_matchup_results("b", "a") == (expected_ba[0],) * 2
		assert results.get_matchup_moves("b", "a") == (expected_ba[1],) * 2

	def test_the_first_player_always_wins_when_red_wins_every_game(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=3),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		# On the smallest board the player who moves first wins.
		assert results.get_matchup_results("a", "b") == (R, R)
		assert results.get_matchup_results("b", "a") == (R, R)

	def test_starting_color_is_used_for_both_orientations(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=3),
			starting_color=B,
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert results.get_matchup_results("a", "b") == (B, B)
		assert results.get_matchup_results("b", "a") == (B, B)

	def test_determinism_is_recorded_for_both_orientations(self, deterministic_first_move_player_class, random_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert results.deterministic_games == 0

	def test_board_is_not_modified(self, random_move_player_class, board_type, recording_progress):
		board = board_type(size=5)
		before = board.serialize()

		play_head_to_head(
			random_move_player_class,
			random_move_player_class,
			2,
			board=board,
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert board.serialize() == before

	@pytest.mark.parametrize("num_games", [0, -2, 1.5, "2", None, True])
	def test_the_number_of_games_per_color_must_be_a_positive_integer(self, random_move_player_class, recording_progress, num_games):
		with pytest.raises(ValueError, match="num_games_per_color must be a positive integer"):
			play_head_to_head(
				random_move_player_class,
				random_move_player_class,
				num_games,
				board=SearchBoard(size=5),
				progress=recording_progress,
			)

		assert recording_progress.updates == 0

	def test_no_progress_bar_is_created_for_an_invalid_number_of_games(self, random_move_player_class, patched_tqdm):
		with pytest.raises(ValueError):
			play_head_to_head(random_move_player_class, random_move_player_class, -2, board=SearchBoard(size=5))

		assert patched_tqdm == []

	def test_the_same_player_only_plays_one_orientation(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="a",
		)

		assert results.players == ("a",)
		assert results.get_matchup_count("a", "a") == 3
		assert results.total_games == 3

	def test_the_same_class_with_the_default_name_is_the_same_player(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=5),
			progress=recording_progress,
		)

		assert results.players == ("DeterministicFirstMovePlayer",)
		assert results.total_games == 2

	def test_the_same_class_with_different_names_is_two_players(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			2,
			board=SearchBoard(size=5),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert results.get_matchup_count("a", "b") == 2
		assert results.get_matchup_count("b", "a") == 2
		assert results.total_games == 4

	def test_progress_counts_only_the_games_played_against_oneself(self, random_move_player_class, recording_progress):
		play_head_to_head(
			random_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="a",
		)

		assert recording_progress.updates == 3

	def test_the_progress_bar_total_for_the_same_player(self, random_move_player_class, patched_tqdm):
		play_head_to_head(
			random_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			player_a_name="a",
			player_b_name="a",
		)

		assert patched_tqdm[0].init_kwargs["total"] == 3
		assert patched_tqdm[0].updates == 3
		assert patched_tqdm[0].closed is True

	def test_the_first_mover_wins_every_game_on_the_smallest_board(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			4,
			board=SearchBoard(size=3),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="a",
		)

		assert results.get_matchup_results("a", "a") == (R,) * 4
		assert results.first_move_advantage()[0]["red_win_rate"] == 1.0


	def test_a_given_progress_is_shared_and_counts_every_game(self, random_move_player_class, recording_progress):
		play_head_to_head(
			random_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)

		assert recording_progress.updates == 6
		assert recording_progress.closed is False

	def test_creates_one_progress_bar_for_both_orientations(self, random_move_player_class, patched_tqdm):
		play_head_to_head(
			random_move_player_class,
			random_move_player_class,
			3,
			board=SearchBoard(size=5),
			player_a_name="a",
			player_b_name="b",
		)

		assert len(patched_tqdm) == 1

		progress = patched_tqdm[0]

		assert progress.init_kwargs == {
			"total": 6,
			"desc": "Head-to-head",
			"unit": "game",
			"leave": False,
		}
		assert progress.updates == 6
		assert progress.closed is True

	def test_closes_its_own_progress_when_a_game_fails(self, first_move_player_class, patched_tqdm):
		class BrokenPlayer(first_move_player_class):
			def choose_move(self, board):
				raise RuntimeError("broken")

		with pytest.raises(RuntimeError, match="broken"):
			play_head_to_head(BrokenPlayer, BrokenPlayer, 1, board=SearchBoard(size=5))

		assert patched_tqdm[0].closed is True

	def test_default_board_is_an_11x11_board(self, deterministic_first_move_player_class, recording_progress):
		results = play_head_to_head(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			1,
			progress=recording_progress,
			player_a_name="a",
			player_b_name="b",
		)
		_, expected_moves = _expected_game(
			deterministic_first_move_player_class,
			deterministic_first_move_player_class,
			board=UnionFindBoard(size=11),
		)

		assert results.get_matchup_moves("a", "b") == (expected_moves,)
