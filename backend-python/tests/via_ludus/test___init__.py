import importlib

import pytest

import via_ludus
from via_ludus import ai, board, player


GRAPH_REGISTRIES = (
	"GRAPH_AGENTS",
	"DISTANCE_AGENTS",
	"PATH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
)

EXPORTS = [
	("Cell", board, "Cell"),
	("PlayerColor", board, "PlayerColor"),
	("Board", board, "Board"),
	("SearchBoard", board, "SearchBoard"),
	("UnionFindBoard", board, "UnionFindBoard"),
	("Player", player, "Player"),
	("DeterministicMoveSelectionMixin", player, "DeterministicMoveSelectionMixin"),
	("ScoringPlayer", player, "ScoringPlayer"),
	("DeterministicScoringMixin", player, "DeterministicScoringMixin"),
	("MoveSelector", player, "MoveSelector"),
	("BestSelector", player, "BestSelector"),
	("MaxSelector", player, "MaxSelector"),
	("MinSelector", player, "MinSelector"),
	("RandomBestSelector", player, "RandomBestSelector"),
	("RandomMaxSelector", player, "RandomMaxSelector"),
	("RandomMinSelector", player, "RandomMinSelector"),
	("SoftmaxSelector", player, "SoftmaxSelector"),
	("SoftminSelector", player, "SoftminSelector"),
	("MaxSelectorMixin", player, "MaxSelectorMixin"),
	("MinSelectorMixin", player, "MinSelectorMixin"),
	("RandomMaxSelectorMixin", player, "RandomMaxSelectorMixin"),
	("RandomMinSelectorMixin", player, "RandomMinSelectorMixin"),
	("SoftmaxSelectorMixin", player, "SoftmaxSelectorMixin"),
	("SoftminSelectorMixin", player, "SoftminSelectorMixin"),
	("AI_AGENTS", ai, "AI_AGENTS"),
	("VIA_LUDUS_AGENTS", ai, "VIA_LUDUS_AGENTS"),
]


def _expected_names():
	return {name for name, _, _ in EXPORTS} | {
		name for name in GRAPH_REGISTRIES if hasattr(ai, name)
	}


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(via_ludus, name) for name in via_ludus.__all__)

	def test_all_has_no_duplicates(self):
		assert len(via_ludus.__all__) == len(set(via_ludus.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in via_ludus.__all__
		assert getattr(via_ludus, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(via_ludus.__all__) == _expected_names()

	@pytest.mark.parametrize("name", GRAPH_REGISTRIES)
	def test_graph_registries_are_exported_when_the_graph_agents_are_available(self, name):
		if hasattr(ai, name):
			assert name in via_ludus.__all__
			assert getattr(via_ludus, name) is getattr(ai, name)
		else:
			assert name not in via_ludus.__all__
			assert not hasattr(via_ludus, name)

	@pytest.mark.parametrize(
		"name",
		["board", "player", "validation", "tournament", "ai", "utils"],
	)
	def test_subpackages_are_available_as_attributes(self, name):
		assert getattr(via_ludus, name) is importlib.import_module(f"via_ludus.{name}")

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus import *", namespace)

		assert set(via_ludus.__all__) <= set(namespace)
