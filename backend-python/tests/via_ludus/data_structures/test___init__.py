import pytest

import via_ludus.data_structures as data_structures_package
from via_ludus.data_structures import union_find


EXPORTS = [
	("UnionFind", union_find, "UnionFind"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(data_structures_package, name) for name in data_structures_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(data_structures_package.__all__) == len(set(data_structures_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in data_structures_package.__all__
		assert getattr(data_structures_package, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(data_structures_package.__all__) == {name for name, _, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.data_structures import *", namespace)

		assert set(data_structures_package.__all__) <= set(namespace)
