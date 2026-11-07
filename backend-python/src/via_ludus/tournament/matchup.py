from ..utils import tqdm
from ..validation import validate_positive_integer

from .game import Game
from .results import TournamentResults


def play_matchup(
	red_player,
	blue_player,
	num_games,
	board=None,
	starting_color=None,
	progress=None,
	red_name=None,
	blue_name=None,
):
	validate_positive_integer(num_games, "num_games")

	game = Game(
		red_player=red_player,
		blue_player=blue_player,
		board=board,
		starting_color=starting_color,
	)

	red_name = red_player.__name__ if red_name is None else red_name
	blue_name = blue_player.__name__ if blue_name is None else blue_name
	results = TournamentResults([red_name, blue_name])

	owns_progress = progress is None

	if owns_progress:
		progress = tqdm(
			total=num_games,
			desc="Matchup",
			unit="game",
			leave=False,
		)

	try:
		for game_index in range(num_games):
			progress.set_postfix(
				red=red_name,
				blue=blue_name,
			)

			if game_index == 0:
				game.reset()
				winner, deterministic = game.play_with_determinism()
				moves = game.move_count

				results.add_matchup_result(
					red_name,
					blue_name,
					winner,
					moves,
					deterministic,
				)

				progress.update(1)

				if deterministic:
					for _ in range(1, num_games):
						results.add_matchup_result(
							red_name,
							blue_name,
							winner,
							moves,
							True,
						)
						progress.update(1)

					break

			else:
				game.reset()
				winner = game.play()

				results.add_matchup_result(
					red_name,
					blue_name,
					winner,
					game.move_count,
					False,
				)

				progress.update(1)
	finally:
		if owns_progress:
			progress.close()

	return results


def play_head_to_head(
	player_a,
	player_b,
	num_games_per_color,
	board=None,
	starting_color=None,
	progress=None,
	player_a_name=None,
	player_b_name=None,
):
	validate_positive_integer(num_games_per_color, "num_games_per_color")

	player_a_name = (
		player_a.__name__ if player_a_name is None else player_a_name
	)
	player_b_name = (
		player_b.__name__ if player_b_name is None else player_b_name
	)

	results = TournamentResults([player_a_name, player_b_name])

	# a player facing a copy of itself has a single matchup: playing it in
	# both orientations would just repeat the same games
	same_player = player_a_name == player_b_name
	num_matchups = 1 if same_player else 2

	owns_progress = progress is None

	if owns_progress:
		progress = tqdm(
			total=num_matchups * num_games_per_color,
			desc="Head-to-head",
			unit="game",
			leave=False,
		)

	try:
		results.add_tournament_data(
			play_matchup(
				red_player=player_a,
				blue_player=player_b,
				num_games=num_games_per_color,
				board=board,
				starting_color=starting_color,
				progress=progress,
				red_name=player_a_name,
				blue_name=player_b_name,
			)
		)

		if not same_player:
			results.add_tournament_data(
				play_matchup(
					red_player=player_b,
					blue_player=player_a,
					num_games=num_games_per_color,
					board=board,
					starting_color=starting_color,
					progress=progress,
					red_name=player_b_name,
					blue_name=player_a_name,
				)
			)
	finally:
		if owns_progress:
			progress.close()

	return results

