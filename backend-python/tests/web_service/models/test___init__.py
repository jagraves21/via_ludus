import pytest

import web_service.models as models
from web_service.models import agents


EXPORTS = [
	("GetAgentsRequest", agents),
	("GetAgentsResponse", agents),
	("GetMoveRequest", agents),
	("GetMoveResponse", agents),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(models, name) for name in models.__all__)

	def test_all_has_no_duplicates(self):
		assert len(models.__all__) == len(set(models.__all__))

	@pytest.mark.parametrize(
		"name, module",
		EXPORTS,
		ids=[name for name, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module):
		assert name in models.__all__
		assert getattr(models, name) is getattr(module, name)

	def test_all_matches_the_expected_api(self):
		assert set(models.__all__) == {name for name, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from web_service.models import *", namespace)

		assert set(models.__all__) <= set(namespace)
