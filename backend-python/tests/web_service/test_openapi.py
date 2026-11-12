import re
import tomllib
from pathlib import Path

import pytest

from web_service.api import agents_router
from web_service.openapi import (
	API_DESCRIPTION,
	API_VERSION,
	OPENAPI_TAGS,
)


PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


class TestApiVersion:
	def test_is_a_semantic_version(self):
		assert re.fullmatch(r"\d+\.\d+\.\d+", API_VERSION)

	def test_matches_the_version_declared_in_pyproject(self):
		with PYPROJECT.open("rb") as file:
			pyproject = tomllib.load(file)

		assert API_VERSION == pyproject["tool"]["via-ludus"]["api-version"]


class TestApiDescription:
	def test_is_not_blank(self):
		assert API_DESCRIPTION.strip()

	@pytest.mark.parametrize(
		"endpoint",
		[
			"GET /api/agents",
			"POST /api/agents/{agent_name}/move",
		],
	)
	def test_documents_every_endpoint(self, endpoint):
		assert endpoint in API_DESCRIPTION


class TestOpenapiTags:
	def test_every_tag_has_a_name_and_a_description(self):
		for tag in OPENAPI_TAGS:
			assert tag["name"].strip()
			assert tag["description"].strip()

	def test_tag_names_are_unique(self):
		names = [tag["name"] for tag in OPENAPI_TAGS]

		assert len(names) == len(set(names))

	def test_every_router_tag_is_declared(self):
		declared = {tag["name"] for tag in OPENAPI_TAGS}

		assert set(agents_router.tags) <= declared
