import pytest

import via_ludus.tournament as tournament_package
from via_ludus.tournament import game, matchup, results, tournament, validation


EXPORTS = [
	("Game", game, "Game"),
	("play_head_to_head", matchup, "play_head_to_head"),
	("play_matchup", matchup, "play_matchup"),
	("TournamentResults", results, "TournamentResults"),
	("RoundRobinTournament", tournament, "RoundRobinTournament"),
	("is_tournament_results", validation, "is_tournament_results"),
	("validate_tournament_results", validation, "validate_tournament_results"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(tournament_package, name) for name in tournament_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(tournament_package.__all__) == len(set(tournament_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in tournament_package.__all__
		assert getattr(tournament_package, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(tournament_package.__all__) == {name for name, _, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.tournament import *", namespace)

		assert set(tournament_package.__all__) <= set(namespace)
