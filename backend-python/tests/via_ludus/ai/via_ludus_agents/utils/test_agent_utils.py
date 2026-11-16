from abc import ABC, abstractmethod

import pytest

from via_ludus.ai import AgentBase
from via_ludus.ai.via_ludus_agents import VIA_LUDUS_AGENTS
from via_ludus.ai.via_ludus_agents.utils import agent_utils
from via_ludus.ai.via_ludus_agents.utils.agent_utils import get_concrete_subclasses


@pytest.fixture
def base():
	"""A fresh abstract base class, so tests never share subclasses."""

	class Base(ABC):
		@classmethod
		def get_agent_name(cls):
			return cls.__dict__.get("name", cls.__name__)

	return Base


class TestGetAllSubclasses:
	def test_no_subclasses(self, base):
		assert agent_utils._get_all_subclasses(base) == []

	def test_direct_subclasses_in_definition_order(self, base):
		class A(base):
			pass

		class B(base):
			pass

		assert agent_utils._get_all_subclasses(base) == [A, B]

	def test_indirect_subclasses_follow_their_parent(self, base):
		class A(base):
			pass

		class A1(A):
			pass

		class A2(A1):
			pass

		class B(base):
			pass

		assert agent_utils._get_all_subclasses(base) == [A, A1, A2, B]

	def test_the_class_itself_is_not_included(self, base):
		class A(base):
			pass

		assert base not in agent_utils._get_all_subclasses(base)
		assert A not in agent_utils._get_all_subclasses(A)


class TestGetConcreteSubclasses:
	def test_empty_when_there_are_no_subclasses(self, base):
		assert get_concrete_subclasses(base) == {}

	def test_maps_agent_names_to_classes(self, base):
		class A(base):
			pass

		class B(base):
			pass

		assert get_concrete_subclasses(base) == {"A": A, "B": B}

	def test_uses_get_agent_name_for_the_keys(self, base):
		class A(base):
			name = "Custom"

		assert get_concrete_subclasses(base) == {"Custom": A}

	def test_the_base_class_is_not_included(self, base):
		class A(base):
			pass

		assert base not in get_concrete_subclasses(base).values()
		assert "Base" not in get_concrete_subclasses(base)

	def test_abstract_subclasses_are_excluded(self, base):
		class Abstract(base):
			@abstractmethod
			def play(self):
				pass

		class Concrete(base):
			pass

		assert get_concrete_subclasses(base) == {"Concrete": Concrete}

	def test_concrete_descendants_of_abstract_classes_are_found(self, base):
		class Abstract(base):
			@abstractmethod
			def play(self):
				pass

		class Concrete(Abstract):
			def play(self):
				pass

		class Deeper(Concrete):
			pass

		assert get_concrete_subclasses(base) == {"Concrete": Concrete, "Deeper": Deeper}

	def test_indirect_subclasses_are_included(self, base):
		class A(base):
			pass

		class B(A):
			pass

		class C(B):
			pass

		assert get_concrete_subclasses(base) == {"A": A, "B": B, "C": C}

	def test_diamond_inheritance_lists_a_class_once(self, base):
		class B(base):
			pass

		class C(base):
			pass

		class D(B, C):
			pass

		result = get_concrete_subclasses(base)

		assert result == {"B": B, "C": C, "D": D}
		assert len(result) == 3

	def test_starting_from_a_subclass_only_returns_its_descendants(self, base):
		class A(base):
			pass

		class A1(A):
			pass

		class B(base):
			pass

		assert get_concrete_subclasses(A) == {"A1": A1}

	def test_unrelated_hierarchies_are_not_mixed(self, base):
		class Other(ABC):
			@classmethod
			def get_agent_name(cls):
				return cls.__name__

		class A(base):
			pass

		class X(Other):
			pass

		assert get_concrete_subclasses(base) == {"A": A}
		assert get_concrete_subclasses(Other) == {"X": X}

	def test_returns_a_new_dictionary_each_time(self, base):
		class A(base):
			pass

		first = get_concrete_subclasses(base)
		first.clear()

		assert get_concrete_subclasses(base) == {"A": A}

	@pytest.mark.filterwarnings("ignore::UserWarning")
	def test_finds_every_registered_via_ludus_agent(self):
		found = get_concrete_subclasses(AgentBase)

		assert VIA_LUDUS_AGENTS
		for name, agent_class in VIA_LUDUS_AGENTS.items():
			assert found[name] is agent_class
