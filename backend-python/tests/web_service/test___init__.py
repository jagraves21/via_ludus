import importlib

import pytest

import web_service


class TestPackage:
	def test_is_a_package(self):
		assert hasattr(web_service, "__path__")

	def test_defines_no_public_api_of_its_own(self):
		assert not hasattr(web_service, "__all__")

	@pytest.mark.parametrize(
		"name",
		["api", "models", "services", "exceptions", "main", "openapi"],
	)
	def test_modules_are_importable_from_the_package(self, name):
		module = importlib.import_module(f"web_service.{name}")

		assert module.__name__ == f"web_service.{name}"
