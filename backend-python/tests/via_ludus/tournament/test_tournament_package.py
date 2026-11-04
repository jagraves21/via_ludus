import pytest

import via_ludus.tournament as tournament_package


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(tournament_package, name) for name in tournament_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(tournament_package.__all__) == len(set(tournament_package.__all__))

	@pytest.mark.parametrize(
		"name",
		[
			"Game",
			"play_head_to_head",
			"play_matchup",
			"TournamentResults",
			"RoundRobinTournament",
			"is_tournament_results",
			"validate_tournament_results",
		],
	)
	def test_public_api_is_exported(self, name):
		assert name in tournament_package.__all__

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.tournament import *", namespace)

		assert set(tournament_package.__all__) <= set(namespace)
