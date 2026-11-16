import pytest

import via_ludus.visualizations as visualizations_package
from via_ludus.visualizations import (
	board_visualizations,
	plotting,
	score_visualizations,
)


EXPORTS = [
	("with_ax", plotting, "with_ax"),
	("plot_board", board_visualizations, "plot_board"),
	("plot_agent_scores", score_visualizations, "plot_agent_scores"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(visualizations_package, name) for name in visualizations_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(visualizations_package.__all__) == len(set(visualizations_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in visualizations_package.__all__
		assert getattr(visualizations_package, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(visualizations_package.__all__) == {name for name, _, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.visualizations import *", namespace)

		assert set(visualizations_package.__all__) <= set(namespace)
