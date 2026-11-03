import pytest

from via_ludus.data_structures import UnionFind


class TestConstructionAndAdd:
	def test_empty_structure(self):
		union_find = UnionFind()

		assert "a" not in union_find

	def test_initial_elements_are_separate_sets(self):
		union_find = UnionFind(["a", "b", "c"])

		assert all(element in union_find for element in "abc")
		assert not union_find.connected("a", "b")
		assert not union_find.connected("b", "c")

	def test_an_element_is_connected_to_itself(self):
		union_find = UnionFind(["a"])

		assert union_find.connected("a", "a")
		assert union_find.find("a") == "a"

	def test_add_registers_new_elements(self):
		union_find = UnionFind()

		union_find.add((1, 2))

		assert (1, 2) in union_find

	def test_add_does_not_reset_an_existing_element(self):
		union_find = UnionFind(["a", "b"])
		union_find.union("a", "b")

		union_find.add("a")

		assert union_find.connected("a", "b")


class TestUnionAndFind:
	def test_union_connects_two_elements(self):
		union_find = UnionFind(["a", "b", "c"])

		union_find.union("a", "b")

		assert union_find.connected("a", "b")
		assert union_find.connected("b", "a")
		assert not union_find.connected("a", "c")

	def test_union_is_transitive(self):
		union_find = UnionFind(range(6))

		union_find.union(0, 1)
		union_find.union(2, 3)
		union_find.union(1, 2)

		assert union_find.connected(0, 3)
		assert not union_find.connected(0, 4)

	def test_union_is_idempotent(self):
		union_find = UnionFind(["a", "b"])

		union_find.union("a", "b")
		root = union_find.find("a")
		union_find.union("a", "b")
		union_find.union("b", "a")

		assert union_find.find("a") == root
		assert union_find.find("b") == root

	def test_find_returns_the_same_representative_for_a_set(self):
		union_find = UnionFind(range(10))

		for element in range(9):
			union_find.union(element, element + 1)

		assert len({union_find.find(element) for element in range(10)}) == 1

	def test_larger_set_keeps_its_representative(self):
		union_find = UnionFind(range(5))
		union_find.union(0, 1)
		union_find.union(0, 2)
		large_root = union_find.find(0)

		union_find.union(3, 0)

		assert union_find.find(3) == large_root

	def test_long_chain_can_be_resolved(self):
		union_find = UnionFind(range(2000))

		for element in range(1999):
			union_find.union(element, element + 1)

		assert union_find.connected(0, 1999)


class TestUnknownElements:
	def test_find_unknown_element(self):
		union_find = UnionFind(["a"])

		with pytest.raises(KeyError, match="Unknown element"):
			union_find.find("missing")

	def test_union_with_unknown_element(self):
		union_find = UnionFind(["a"])

		with pytest.raises(KeyError):
			union_find.union("a", "missing")

		with pytest.raises(KeyError):
			union_find.connected("missing", "a")


class TestCopy:
	def test_copy_is_independent(self):
		union_find = UnionFind(["a", "b", "c"])
		union_find.union("a", "b")
		clone = union_find.copy()

		clone.union("b", "c")
		clone.add("d")

		assert clone.connected("a", "c")
		assert not union_find.connected("a", "c")
		assert "d" not in union_find

	def test_copy_preserves_connectivity(self):
		union_find = UnionFind(["a", "b", "c"])
		union_find.union("a", "b")

		assert union_find.copy().equivalent(union_find)


class TestEquivalent:
	def test_equivalent_ignores_representatives(self):
		first = UnionFind(["a", "b", "c"])
		second = UnionFind(["a", "b", "c"])

		first.union("a", "b")
		first.union("b", "c")
		second.union("c", "b")
		second.union("b", "a")

		assert first.equivalent(second)
		assert second.equivalent(first)

	def test_equivalent_detects_different_connectivity(self):
		first = UnionFind(["a", "b", "c"])
		second = UnionFind(["a", "b", "c"])

		first.union("a", "b")
		second.union("b", "c")

		assert not first.equivalent(second)

	def test_equivalent_detects_different_elements(self):
		assert not UnionFind(["a", "b"]).equivalent(UnionFind(["a", "c"]))
		assert not UnionFind(["a"]).equivalent(UnionFind(["a", "b"]))

	def test_equivalent_with_other_types_is_not_implemented(self):
		assert UnionFind(["a"]).equivalent("a") is NotImplemented


class TestRepresentation:
	def test_str_lists_the_sets(self):
		union_find = UnionFind([1, 2, 3])
		union_find.union(1, 2)

		assert str(union_find) == "1: [1, 2]\n3: [3]"

	def test_repr_contains_the_class_name_and_sets(self):
		union_find = UnionFind([1])

		assert repr(union_find) == "UnionFind('1: [1]')"
