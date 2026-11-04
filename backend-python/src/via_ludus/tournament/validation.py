from .results import TournamentResults


def is_tournament_results(results):
	return isinstance(results, TournamentResults)


def validate_tournament_results(results):
	if not is_tournament_results(results):
		raise TypeError(
			f"Expected a TournamentResults, got {type(results).__name__}"
		)
