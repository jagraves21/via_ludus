import pytest

import via_ludus.ai as ai_package
from via_ludus.ai import agent, via_ludus_agents


EXPORTS = [
	("AgentBase", agent, "AgentBase"),
	("Agent", agent, "Agent"),
	("ScoringAgent", agent, "ScoringAgent"),
	("VIA_LUDUS_AGENTS", via_ludus_agents, "VIA_LUDUS_AGENTS"),
]

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
		assert all(hasattr(ai_package, name) for name in ai_package.__all__)

	def test_all_has_no_duplicates(self):
		assert len(ai_package.__all__) == len(set(ai_package.__all__))

	@pytest.mark.parametrize(
		"name, module, attribute",
		EXPORTS,
		ids=[name for name, _, _ in EXPORTS],
	)
	def test_public_api_is_exported(self, name, module, attribute):
		assert name in ai_package.__all__
		assert getattr(ai_package, name) is getattr(module, attribute)

	def test_ai_agents_is_exported(self):
		assert "AI_AGENTS" in ai_package.__all__

	@pytest.mark.parametrize("name", GRAPH_REGISTRIES)
	def test_graph_registries_follow_the_graph_agents_package(self, name):
		if hasattr(via_ludus_agents, name):
			assert name in ai_package.__all__
			assert getattr(ai_package, name) is getattr(via_ludus_agents, name)
		else:
			assert name not in ai_package.__all__

	def test_star_import_exposes_the_public_api(self):
		namespace = {}

		exec("from via_ludus.ai import *", namespace)

		assert set(ai_package.__all__) <= set(namespace)


class TestAiAgents:
	def test_is_a_dictionary_of_agent_classes_by_name(self):
		assert isinstance(ai_package.AI_AGENTS, dict)
		assert ai_package.AI_AGENTS

		for name, agent_class in ai_package.AI_AGENTS.items():
			assert isinstance(agent_class, type)
			assert issubclass(agent_class, ai_package.AgentBase)
			assert agent_class.get_agent_name() == name

	def test_every_via_ludus_agent_is_listed(self):
		missing = set(ai_package.VIA_LUDUS_AGENTS) - set(ai_package.AI_AGENTS)

		assert not missing, f"agents missing from agent_order: {sorted(missing)}"

	def test_agents_are_the_registered_classes(self):
		registered = ai_package.AgentBase.get_agents()

		for name, agent_class in ai_package.AI_AGENTS.items():
			assert registered[name] is agent_class

	def test_agents_follow_agent_order(self):
		order = ai_package.agent_order

		assert list(ai_package.AI_AGENTS) == [
			name for name in order if name in ai_package.AI_AGENTS
		]

	def test_agent_order_has_no_duplicates(self):
		order = ai_package.agent_order

		assert len(order) == len(set(order))

	def test_agent_order_has_no_unknown_agents(self):
		pytest.importorskip("networkx")
		pytest.importorskip("scipy")

		unknown = set(ai_package.agent_order) - set(ai_package.AI_AGENTS)

		assert not unknown, f"agent_order names no registered agent: {sorted(unknown)}"
