import via_ludus.ai.via_ludus_agents.utils as utils_package
from via_ludus.ai.via_ludus_agents.utils import agent_utils


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(utils_package, name) for name in utils_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(utils_package.__all__) == len(set(utils_package.__all__))

	def test_get_concrete_subclasses_is_exported(self):
		assert "get_concrete_subclasses" in utils_package.__all__
		assert utils_package.get_concrete_subclasses is agent_utils.get_concrete_subclasses

	def test_all_matches_the_expected_api(self):
		assert set(utils_package.__all__) == {"get_concrete_subclasses"}

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.ai.via_ludus_agents.utils import *", namespace)

		assert set(utils_package.__all__) <= set(namespace)
