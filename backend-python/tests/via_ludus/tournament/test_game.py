import pytest

from via_ludus.board import Cell, PlayerColor, SearchBoard, UnionFindBoard
from via_ludus.tournament import Game


@pytest.fixture
def make_game(first_move_player_class):
	def _make_game(red=None, blue=None, **kwargs):
		return Game(
			red or first_move_player_class,
			blue or first_move_player_class,
			**kwargs,
		)

	return _make_game


class TestGameConstruction:
	def test_initial_state(self, make_game):
		game = make_game()

		assert game.starting_color is PlayerColor.RED
		assert game.current_color is PlayerColor.RED
		assert game.moves == ()
		assert game.move_count == 0
		assert game.winner is None
		assert game.is_game_over is False

	def test_default_board_is_an_empty_11x11_union_find_board(self, make_game):
		board = make_game().board

		assert type(board) is UnionFindBoard
		assert board.shape == (11, 11)
		assert board.serialize() == UnionFindBoard(size=11).serialize()

	def test_available_moves_are_the_white_cells(self, make_game):
		game = make_game()

		assert game.available_moves == UnionFindBoard(size=11).available

	@pytest.mark.parametrize("starting_color", [PlayerColor.RED, PlayerColor.BLUE])
	def test_starting_color(self, make_game, starting_color):
		game = make_game(starting_color=starting_color)

		assert game.starting_color is starting_color
		assert game.current_color is starting_color
		assert game.starting_player is game.players[starting_color]
		assert game.current_player is game.players[starting_color]

	def test_invalid_starting_color_is_rejected(self, make_game):
		with pytest.raises(TypeError):
			make_game(starting_color="red")

	def test_players_are_created_from_the_classes(self, first_move_player_class, deterministic_last_move_player_class):
		game = Game(first_move_player_class, deterministic_last_move_player_class)

		assert type(game.players[PlayerColor.RED]) is first_move_player_class
		assert type(game.players[PlayerColor.BLUE]) is deterministic_last_move_player_class
		assert game.players[PlayerColor.RED].color is PlayerColor.RED
		assert game.players[PlayerColor.BLUE].color is PlayerColor.BLUE

	@pytest.mark.parametrize("which", ["red", "blue"])
	def test_player_instances_are_rejected(self, first_move_player_class, which):
		instance = first_move_player_class(PlayerColor.RED)
		arguments = {
			"red": (instance, first_move_player_class),
			"blue": (first_move_player_class, instance),
		}[which]

		with pytest.raises(TypeError, match="Expected a Player subclass"):
			Game(*arguments)

	@pytest.mark.parametrize("value", [int, "Player", None])
	def test_non_player_classes_are_rejected(self, first_move_player_class, value):
		with pytest.raises(TypeError):
			Game(value, first_move_player_class)

		with pytest.raises(TypeError):
			Game(first_move_player_class, value)

	def test_player_with_the_wrong_color_is_rejected(self, first_move_player_class):
		class AlwaysRedPlayer(first_move_player_class):
			def __init__(self, color):
				super().__init__(PlayerColor.RED)

		with pytest.raises(ValueError, match="Expected a blue player, got red"):
			Game(first_move_player_class, AlwaysRedPlayer)

	def test_board_argument_is_copied(self, make_game):
		board = SearchBoard(size=5)
		game = make_game(board=board)

		board.set(1, 1, Cell.RED)

		assert game.board.get(1, 1) is Cell.WHITE
		assert (1, 1) in game.available_moves

	def test_board_implementation_is_kept(self, make_game, board_type):
		game = make_game(board=board_type(size=5))

		assert type(game.board) is board_type

	def test_board_property_returns_a_copy(self, make_game):
		game = make_game()

		game.board.set(1, 1, Cell.RED)

		assert game.board.get(1, 1) is Cell.WHITE
		assert game.board is not game.board

	def test_players_property_returns_a_copy(self, make_game):
		game = make_game()

		game.players.clear()

		assert set(game.players) == {PlayerColor.RED, PlayerColor.BLUE}

	def test_game_can_start_from_a_won_position(self, make_game, board_type, red_winning_game):
		game = make_game(board=red_winning_game(board_type))

		assert game.winner is PlayerColor.RED
		assert game.is_game_over is True
		assert game.move_count == 0

	def test_game_can_start_from_a_position_in_progress(self, make_game, board_type, red_winning_moves, make_board_from_moves):
		board = make_board_from_moves(red_winning_moves[:-1], board_type=board_type)
		game = make_game(board=board)

		assert game.winner is None
		assert game.available_moves == board.available


class TestGameDeterminism:
	def test_is_deterministic_when_both_players_are(self, deterministic_first_move_player_class, deterministic_last_move_player_class):
		game = Game(deterministic_first_move_player_class, deterministic_last_move_player_class)

		assert game.is_deterministic is True

	@pytest.mark.parametrize("deterministic_color", [PlayerColor.RED, PlayerColor.BLUE])
	def test_is_not_deterministic_when_one_player_is_not(self, deterministic_first_move_player_class, random_move_player_class, deterministic_color):
		classes = {
			deterministic_color: deterministic_first_move_player_class,
			deterministic_color.opponent: random_move_player_class,
		}

		game = Game(classes[PlayerColor.RED], classes[PlayerColor.BLUE])

		assert game.is_deterministic is False

	def test_is_not_deterministic_when_neither_player_is(self, random_move_player_class):
		assert Game(random_move_player_class, random_move_player_class).is_deterministic is False


class TestMakeMove:
	def test_claims_the_cell_for_the_current_color(self, make_game):
		game = make_game()

		assert game.make_move((1, 1)) == (1, 1)
		assert game.board.get(1, 1) is Cell.RED

	def test_alternates_colors(self, make_game):
		game = make_game()

		game.make_move((1, 1))

		assert game.current_color is PlayerColor.BLUE
		assert game.current_player is game.players[PlayerColor.BLUE]

		game.make_move((3, 3))

		assert game.board.get(3, 3) is Cell.BLUE
		assert game.current_color is PlayerColor.RED

	def test_blue_can_start(self, make_game):
		game = make_game(starting_color=PlayerColor.BLUE)

		game.make_move((1, 1))

		assert game.board.get(1, 1) is Cell.BLUE
		assert game.current_color is PlayerColor.RED

	def test_records_the_moves(self, make_game):
		game = make_game()

		game.make_move((1, 1))
		game.make_move((3, 3))

		assert game.moves == ((1, 1), (3, 3))
		assert game.move_count == 2

	def test_moves_cannot_be_modified_through_the_property(self, make_game):
		game = make_game()
		game.make_move((1, 1))

		assert isinstance(game.moves, tuple)

	def test_removes_the_move_from_the_available_moves(self, make_game):
		game = make_game()
		before = game.available_moves

		game.make_move((1, 1))

		assert game.available_moves == before - {(1, 1)}

	@pytest.mark.parametrize(
		"move",
		[(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (11, 1), (-1, 1), (99, 99)],
		ids=["wall", "red-edge", "blue-edge", "prefilled-blue", "prefilled-red", "past-the-edge", "negative", "far-away"],
	)
	def test_rejects_moves_that_are_not_available(self, make_game, move):
		game = make_game()
		before = game.board.serialize()

		with pytest.raises(ValueError, match="Invalid move"):
			game.make_move(move)

		assert game.board.serialize() == before
		assert game.move_count == 0
		assert game.current_color is PlayerColor.RED

	def test_rejects_a_cell_that_was_already_claimed(self, make_game):
		game = make_game()
		game.make_move((1, 1))

		with pytest.raises(ValueError, match="Invalid move"):
			game.make_move((1, 1))

		assert game.current_color is PlayerColor.BLUE

	def test_the_winning_move_ends_the_game(self, make_game, board_type, red_winning_moves, make_board_from_moves):
		game = make_game(board=make_board_from_moves(red_winning_moves[:-1], board_type=board_type))

		move, _ = red_winning_moves[-1]
		game.make_move(move)

		assert game.winner is PlayerColor.RED
		assert game.is_game_over is True

	def test_the_turn_does_not_pass_after_the_winning_move(self, make_game, board_type, red_winning_moves, make_board_from_moves):
		game = make_game(board=make_board_from_moves(red_winning_moves[:-1], board_type=board_type))

		game.make_move(red_winning_moves[-1][0])

		assert game.current_color is PlayerColor.RED

	def test_no_moves_after_the_game_is_over(self, make_game, board_type, red_winning_game):
		game = make_game(board=red_winning_game(board_type))
		available = next(iter(game.available_moves))

		with pytest.raises(ValueError, match="already over"):
			game.make_move(available)

	def test_smallest_board_is_won_by_the_first_move(self, make_game, board_type):
		game = make_game(board=board_type(size=3))

		game.make_move((1, 1))

		assert game.winner is PlayerColor.RED
		assert game.available_moves == set()


class TestReset:
	def test_restores_the_initial_state(self, make_game):
		game = make_game()
		initial = game.board.serialize()
		game.make_move((1, 1))
		game.make_move((3, 3))

		game.reset()

		assert game.board.serialize() == initial
		assert game.moves == ()
		assert game.move_count == 0
		assert game.current_color is PlayerColor.RED
		assert game.winner is None

	def test_restores_the_starting_color(self, make_game):
		game = make_game(starting_color=PlayerColor.BLUE)
		game.make_move((1, 1))

		game.reset()

		assert game.current_color is PlayerColor.BLUE

	def test_reopens_a_finished_game(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		game.make_move((1, 1))

		game.reset()

		assert game.is_game_over is False
		game.make_move((1, 1))
		assert game.is_game_over is True

	def test_creates_new_player_instances(self, make_game):
		game = make_game()
		players = game.players

		game.reset()

		assert game.players[PlayerColor.RED] is not players[PlayerColor.RED]
		assert game.players[PlayerColor.BLUE] is not players[PlayerColor.BLUE]

	def test_resets_to_the_board_given_at_construction(self, make_game, board_type, red_winning_moves, make_board_from_moves):
		board = make_board_from_moves(red_winning_moves[:-1], board_type=board_type)
		game = make_game(board=board)
		game.make_move(red_winning_moves[-1][0])

		game.reset()

		assert game.board.serialize() == board.serialize()
		assert game.winner is None

	def test_a_game_can_be_played_again(self, make_game):
		game = make_game(board=SearchBoard(size=5))
		first = game.play()
		first_moves = game.moves

		game.reset()

		assert game.play() is first
		assert game.moves == first_moves


class TestMakePlayerMove:
	def test_asks_the_current_player_for_a_move(self, make_game, deterministic_last_move_player_class):
		game = make_game(red=deterministic_last_move_player_class)

		move = game.make_player_move()

		assert move == max(UnionFindBoard(size=11).available)
		assert game.board.get(*move) is Cell.RED

	def test_each_player_moves_in_turn(self, make_game, deterministic_last_move_player_class):
		game = make_game(blue=deterministic_last_move_player_class)

		first = game.make_player_move()
		second = game.make_player_move()

		assert first == min(UnionFindBoard(size=11).available)
		assert second == max(game.board.available | {second})
		assert game.board.get(*second) is Cell.BLUE

	def test_players_cannot_change_the_real_board(self, make_game, first_move_player_class):
		class CheatingPlayer(first_move_player_class):
			def choose_move(self, board):
				board.set(3, 3, self.cell)
				return (1, 1)

		game = make_game(red=CheatingPlayer)

		game.make_player_move()

		assert game.board.get(3, 3) is Cell.WHITE
		assert game.board.get(1, 1) is Cell.RED

	def test_an_illegal_choice_is_rejected(self, make_game, first_move_player_class):
		class EdgePlayer(first_move_player_class):
			def choose_move(self, board):
				return (0, 1)

		game = make_game(red=EdgePlayer)

		with pytest.raises(ValueError, match="Invalid move"):
			game.make_player_move()

		assert game.move_count == 0

	def test_no_player_moves_after_the_game_is_over(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		game.make_player_move()

		with pytest.raises(ValueError, match="already over"):
			game.make_player_move()


class TestMakePlayerMoveWithDeterminism:
	def test_deterministic_player(self, make_game, deterministic_first_move_player_class):
		game = make_game(red=deterministic_first_move_player_class)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move == min(UnionFindBoard(size=11).available)
		assert is_deterministic is True
		assert game.board.get(*move) is Cell.RED

	def test_scoring_player_with_non_deterministic_scores(self, make_game, index_scoring_player_class):
		game = make_game(red=index_scoring_player_class)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move == max(UnionFindBoard(size=11).available)
		assert is_deterministic is False

	def test_deterministic_scoring_player(self, make_game, deterministic_scoring_player_class):
		game = make_game(red=deterministic_scoring_player_class)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move == max(UnionFindBoard(size=11).available)
		assert is_deterministic is True

	def test_per_move_determinism_of_a_random_selector_with_a_unique_best_move(self, make_game, unique_best_random_scoring_player_class):
		game = make_game(red=unique_best_random_scoring_player_class)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move == max(UnionFindBoard(size=11).available)
		assert is_deterministic is True

	def test_per_move_determinism_with_tied_scores(self, make_game, tied_scoring_player_class):
		class TiedRandomPlayer(tied_scoring_player_class):
			def create_selector(self):
				from via_ludus.player import RandomMaxSelector

				return RandomMaxSelector(seed=0)

		game = make_game(red=TiedRandomPlayer)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move in UnionFindBoard(size=11).available
		assert is_deterministic is False

	def test_player_without_a_determinism_contract_is_not_deterministic(self, make_game, random_move_player_class):
		game = make_game(red=random_move_player_class)

		move, is_deterministic = game.make_player_move_with_determinism()

		assert move in UnionFindBoard(size=11).available
		assert is_deterministic is False

	def test_players_cannot_change_the_real_board(self, make_game, deterministic_first_move_player_class):
		class CheatingPlayer(deterministic_first_move_player_class):
			def choose_move(self, board):
				board.set(3, 3, self.cell)
				return (1, 1)

		game = make_game(red=CheatingPlayer)

		game.make_player_move_with_determinism()

		assert game.board.get(3, 3) is Cell.WHITE

	def test_no_player_moves_after_the_game_is_over(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		game.make_player_move_with_determinism()

		with pytest.raises(ValueError, match="already over"):
			game.make_player_move_with_determinism()


class TestPlay:
	@pytest.mark.parametrize("size", [3, 5, 7, 11])
	def test_plays_a_complete_legal_game(self, make_game, deterministic_first_move_player_class, board_type, size):
		game = make_game(
			red=deterministic_first_move_player_class,
			blue=deterministic_first_move_player_class,
			board=board_type(size=size),
		)

		winner = game.play()

		assert winner in (PlayerColor.RED, PlayerColor.BLUE)
		assert game.winner is winner
		assert game.is_game_over is True

	def test_the_winner_made_the_last_move(self, make_game, random_move_player_class, board_type):
		game = make_game(
			red=random_move_player_class,
			blue=random_move_player_class,
			board=board_type(size=7),
		)

		winner = game.play()

		assert game.current_color is winner
		assert game.board.get(*game.moves[-1]) is winner.cell

	def test_moves_are_distinct_and_alternate_between_the_players(self, make_game, random_move_player_class):
		game = make_game(red=random_move_player_class, blue=random_move_player_class)

		game.play()
		board = game.board

		assert len(set(game.moves)) == game.move_count
		for index, move in enumerate(game.moves):
			expected = PlayerColor.RED if index % 2 == 0 else PlayerColor.BLUE
			assert board.get(*move) is expected.cell

	def test_the_game_matches_the_board_winner(self, make_game, random_move_player_class):
		game = make_game(red=random_move_player_class, blue=random_move_player_class)

		winner = game.play()

		assert game.board.winner is winner

	def test_blue_can_move_first(self, make_game, board_type):
		game = make_game(board=board_type(size=3), starting_color=PlayerColor.BLUE)

		assert game.play() is PlayerColor.BLUE

	def test_deterministic_players_always_play_the_same_game(self, make_game, deterministic_first_move_player_class, deterministic_last_move_player_class):
		def play():
			game = make_game(
				red=deterministic_first_move_player_class,
				blue=deterministic_last_move_player_class,
				board=SearchBoard(size=7),
			)
			game.play()

			return game.winner, game.moves

		assert play() == play()

	def test_playing_a_finished_game_returns_the_winner(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		winner = game.play()
		moves = game.moves

		assert game.play() is winner
		assert game.moves == moves

	def test_play_resumes_from_a_position_in_progress(self, make_game, board_type, red_winning_moves, make_board_from_moves):
		board = make_board_from_moves(red_winning_moves[:-1], board_type=board_type)
		game = make_game(board=board)

		winner = game.play()

		assert winner in (PlayerColor.RED, PlayerColor.BLUE)
		assert game.move_count >= 1


class TestPlayWithDeterminism:
	def test_deterministic_players(self, make_game, deterministic_first_move_player_class, deterministic_last_move_player_class):
		game = make_game(
			red=deterministic_first_move_player_class,
			blue=deterministic_last_move_player_class,
			board=SearchBoard(size=7),
		)

		winner, was_deterministic = game.play_with_determinism()

		assert winner is game.winner
		assert was_deterministic is True

	def test_result_matches_play(self, make_game, deterministic_first_move_player_class, deterministic_last_move_player_class):
		kwargs = dict(
			red=deterministic_first_move_player_class,
			blue=deterministic_last_move_player_class,
			board=SearchBoard(size=7),
		)
		first = make_game(**kwargs)
		second = make_game(**kwargs)

		winner, _ = first.play_with_determinism()

		assert winner is second.play()
		assert first.moves == second.moves

	def test_random_players_are_not_deterministic(self, make_game, random_move_player_class):
		game = make_game(red=random_move_player_class, blue=random_move_player_class)

		winner, was_deterministic = game.play_with_determinism()

		assert winner is game.winner
		assert was_deterministic is False

	def test_one_random_player_makes_the_game_non_deterministic(self, make_game, deterministic_first_move_player_class, random_move_player_class):
		game = make_game(
			red=deterministic_first_move_player_class,
			blue=random_move_player_class,
		)

		_, was_deterministic = game.play_with_determinism()

		assert was_deterministic is False

	def test_scoring_players_with_non_deterministic_scores(self, make_game, index_scoring_player_class):
		game = make_game(
			red=index_scoring_player_class,
			blue=index_scoring_player_class,
			board=SearchBoard(size=5),
		)

		_, was_deterministic = game.play_with_determinism()

		assert was_deterministic is False

	def test_per_move_determinism_can_keep_a_game_deterministic(self, make_game, unique_best_random_scoring_player_class):
		game = make_game(
			red=unique_best_random_scoring_player_class,
			blue=unique_best_random_scoring_player_class,
			board=SearchBoard(size=7),
		)

		_, was_deterministic = game.play_with_determinism()

		# Neither player is deterministic as a whole, but every move had a
		# unique best score.
		assert game.is_deterministic is False
		assert was_deterministic is True

	def test_once_non_deterministic_the_rest_of_the_game_is_still_played(self, make_game, random_move_player_class, board_type):
		game = make_game(
			red=random_move_player_class,
			blue=random_move_player_class,
			board=board_type(size=7),
		)

		game.play_with_determinism()

		assert game.is_game_over is True
		assert game.board.winner is game.winner

	def test_a_finished_game_is_deterministic_by_default(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		game.play()

		assert game.play_with_determinism() == (game.winner, True)


class TestGameRepresentation:
	def test_str(self, make_game):
		assert str(make_game()) == (
			"Game(current_player=Red Player, current_color=Red, moves=0, winner=None)"
		)

	def test_str_after_a_move(self, make_game):
		game = make_game()
		game.make_move((1, 1))

		assert str(game) == (
			"Game(current_player=Blue Player, current_color=Blue, moves=1, winner=None)"
		)

	def test_str_after_the_game(self, make_game):
		game = make_game(board=SearchBoard(size=3))
		game.play()

		assert str(game).endswith("moves=1, winner=Red)")

	def test_repr(self, make_game):
		game = make_game(board=SearchBoard(size=5))

		assert repr(game) == (
			"Game(board=SearchBoard(shape=(5, 5)), "
			"current_player=FirstMovePlayer(color=PlayerColor.RED), "
			"current_color=Red, moves=0, winner=None)"
		)
