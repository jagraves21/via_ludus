import pytest

import via_ludus.utils as utils_package
from via_ludus.utils import optional_dependencies, progress, timing


EXPORTS = [
	("time_it", timing, "time_it"),
	("Timer", timing, "Timer"),
	("time_block", timing, "time_block"),
	("OptionalDependencyError", optional_dependencies, "OptionalDependencyError"),
	("requires_extra", optional_dependencies, "requires_extra"),
	("tqdm", progress, "tqdm"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(utils_package, name) for name in utils_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(utils_package.__all__) == len(set(utils_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in utils_package.__all__
		assert getattr(utils_package, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(utils_package.__all__) == {name for name, _, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.utils import *", namespace)

		assert set(utils_package.__all__) <= set(namespace)
