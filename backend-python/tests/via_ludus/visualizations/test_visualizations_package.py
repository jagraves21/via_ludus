import os
import subprocess
import sys
from pathlib import Path

import pytest

import via_ludus.visualizations as visualizations
from via_ludus.visualizations import (
	board_visualizations,
	plotting,
	score_visualizations,
)


EXPORTS = [
	("with_ax", plotting),
	("plot_board", board_visualizations),
	("plot_agent_scores", score_visualizations),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(visualizations, name) for name in visualizations.__all__)

	def test_all_has_no_duplicates(self):
		assert len(visualizations.__all__) == len(set(visualizations.__all__))

	@pytest.mark.parametrize("name, module", EXPORTS, ids=[name for name, _ in EXPORTS])
	def test_public_api_is_exported(self, name, module):
		assert name in visualizations.__all__
		assert getattr(visualizations, name) is getattr(module, name)

	def test_all_matches_the_expected_api(self):
		assert set(visualizations.__all__) == {name for name, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.visualizations import *", namespace)

		assert set(visualizations.__all__) <= set(namespace)

	def test_importing_the_package_does_not_load_matplotlib(self):
		source_root = Path(visualizations.__file__).resolve().parents[2]
		environment = dict(os.environ, PYTHONPATH=str(source_root))

		completed = subprocess.run(
			[
				sys.executable,
				"-c",
				"import sys; import via_ludus.visualizations; "
				"print('matplotlib' in sys.modules)",
			],
			capture_output=True,
			text=True,
			env=environment,
		)

		assert completed.returncode == 0, completed.stderr
		assert completed.stdout.strip() == "False"
