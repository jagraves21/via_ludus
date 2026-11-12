import pytest
from fastapi import APIRouter

import web_service.api as api
from web_service.api import agents


EXPORTS = [
	("agents_router", agents, "router"),
]


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(api, name) for name in api.__all__)

	def test_all_has_no_duplicates(self):
		assert len(api.__all__) == len(set(api.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in api.__all__
		assert getattr(api, name) is getattr(module, attribute)

	def test_all_matches_the_expected_api(self):
		assert set(api.__all__) == {name for name, _, _ in EXPORTS}

	def test_agents_router_is_a_fastapi_router(self):
		assert isinstance(api.agents_router, APIRouter)

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from web_service.api import *", namespace)

		assert set(api.__all__) <= set(namespace)
