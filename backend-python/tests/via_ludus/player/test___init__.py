import pytest

import via_ludus.player as player_package


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(player_package, name) for name in player_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(player_package.__all__) == len(set(player_package.__all__))

	@pytest.mark.parametrize(
		"name",
		[
			"MoveSelector",
			"BestSelector",
			"MaxSelector",
			"MinSelector",
			"RandomBestSelector",
			"RandomMaxSelector",
			"RandomMinSelector",
			"SoftmaxSelector",
			"SoftminSelector",
			"MaxSelectorMixin",
			"MinSelectorMixin",
			"RandomMaxSelectorMixin",
			"RandomMinSelectorMixin",
			"SoftmaxSelectorMixin",
			"SoftminSelectorMixin",
			"Player",
			"DeterministicMoveSelectionMixin",
			"ScoringPlayer",
			"DeterministicScoringMixin",
			"is_player",
			"is_player_class",
			"is_scoring_player",
			"is_scoring_player_class",
			"validate_player",
			"validate_player_class",
			"validate_scoring_player",
			"validate_scoring_player_class",
		],
	)
	def test_public_api_is_exported(self, name):
		assert name in player_package.__all__

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.player import *", namespace)

		assert set(player_package.__all__) <= set(namespace)
