import pytest

import via_ludus.utils as utils
from via_ludus.utils import optional_dependencies, progress, timing


EXPORTS = [
	("time_it", timing),
	("Timer", timing),
	("time_block", timing),
	("OptionalDependencyError", optional_dependencies),
	("requires_extra", optional_dependencies),
	("tqdm", progress),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(utils, name) for name in utils.__all__)

	def test_all_has_no_duplicates(self):
		assert len(utils.__all__) == len(set(utils.__all__))

	@pytest.mark.parametrize("name, module", EXPORTS, ids=[name for name, _ in EXPORTS])
	def test_public_api_is_exported(self, name, module):
		assert name in utils.__all__
		assert getattr(utils, name) is getattr(module, name)

	def test_all_matches_the_expected_api(self):
		assert set(utils.__all__) == {name for name, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.utils import *", namespace)

		assert set(utils.__all__) <= set(namespace)
