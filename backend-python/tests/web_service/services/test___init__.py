import pytest

import web_service.services as services
from web_service.services import agents


EXPORTS = [
	("get_agents", agents),
	("get_move", agents),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(services, name) for name in services.__all__)

	def test_all_has_no_duplicates(self):
		assert len(services.__all__) == len(set(services.__all__))

	@pytest.mark.parametrize(
		"name, module",
		EXPORTS,
		ids=[name for name, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module):
		assert name in services.__all__
		assert getattr(services, name) is getattr(module, name)

	def test_all_matches_the_expected_api(self):
		assert set(services.__all__) == {name for name, _ in EXPORTS}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from web_service.services import *", namespace)

		assert set(services.__all__) <= set(namespace)
