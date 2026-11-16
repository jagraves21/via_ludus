import pytest

import via_ludus.ai.via_ludus_agents as agents_package
from via_ludus.ai import AgentBase
from via_ludus.ai.via_ludus_agents import random_agent


GRAPH_REGISTRIES = (
	"GRAPH_AGENTS",
	"DISTANCE_AGENTS",
	"PATH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
)


class TestPackageExports:
	def test_all_lists_only_existing_names(self):
		assert all(hasattr(agents_package, name) for name in agents_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(agents_package.__all__) == len(set(agents_package.__all__))

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.ai.via_ludus_agents import *", namespace)

		assert set(agents_package.__all__) <= set(namespace)

	def test_the_registry_is_exported(self):
		assert "VIA_LUDUS_AGENTS" in agents_package.__all__

	def test_the_random_agent_is_exported(self):
		assert "RandomAgent" in agents_package.__all__
		assert agents_package.RandomAgent is random_agent.RandomAgent

	@pytest.mark.parametrize("name", GRAPH_REGISTRIES)
	def test_graph_registries_are_exported_only_with_the_graph_agents(self, name):
		assert (name in agents_package.__all__) == hasattr(agents_package, name)


class TestViaLudusAgents:
	def test_contains_the_random_agent(self):
		name = agents_package.RandomAgent.get_agent_name()

		assert agents_package.VIA_LUDUS_AGENTS[name] is agents_package.RandomAgent

	def test_maps_agent_names_to_registered_agent_classes(self):
		registered = AgentBase.get_agents()

		for name, agent_class in agents_package.VIA_LUDUS_AGENTS.items():
			assert agent_class.get_agent_name() == name
			assert registered[name] is agent_class

	def test_values_are_distinct_classes(self):
		classes = list(agents_package.VIA_LUDUS_AGENTS.values())

		assert len(classes) == len(set(classes))
		assert all(isinstance(cls, type) for cls in classes)

	@pytest.mark.parametrize("name", GRAPH_REGISTRIES)
	def test_graph_agents_are_registered_when_available(self, name):
		if not hasattr(agents_package, name):
			pytest.skip("graph agents are not available")

		registry = getattr(agents_package, name)

		assert registry
		for agent_name, agent_class in registry.items():
			assert agents_package.VIA_LUDUS_AGENTS[agent_name] is agent_class
