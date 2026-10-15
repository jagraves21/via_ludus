class UnionFind:
	def __init__(self, elements=()):
		self._parent = {}
		self._size = {}

		for element in elements:
			self.add(element)

	def __contains__(self, element):
		return element in self._parent

	def add(self, element):
		if element not in self._parent:
			self._parent[element] = element
			self._size[element] = 1

	def find(self, element):
		if element not in self._parent:
			raise KeyError(f"Unknown element: {element}")

		if self._parent[element] != element:
			self._parent[element] = self.find(
				self._parent[element]
			)

		return self._parent[element]

	def union(self, first, second):
		first_root = self.find(first)
		second_root = self.find(second)

		if first_root == second_root:
			return

		if self._size[first_root] < self._size[second_root]:
			first_root, second_root = second_root, first_root

		self._parent[second_root] = first_root
		self._size[first_root] += self._size[second_root]

	def connected(self, first, second):
		return self.find(first) == self.find(second)

	def copy(self):
		union_find = self.__class__.__new__(self.__class__)
		union_find._parent = self._parent.copy()
		union_find._size = self._size.copy()
		return union_find

	def __str__(self):
		sets = dict() 

		for element in self._parent:
			root = self.find(element)
			sets.setdefault(root, list()).append(element)

		return "\n".join(
			f"{root}: {sorted(elements, key=repr)}"
			for root, elements in sorted(
				sets.items(), key=lambda item: repr(item[0])
			)
		)

	def __repr__(self):
		return f"{self.__class__.__name__}({str(self)!r})"

