from .move_selector import (
	BestSelector,
	RandomMaxSelector,
	RandomMinSelector,
	SoftmaxSelector,
	SoftminSelector,
)


class BestSelectorMixin:
	def create_selector(self):
		return BestSelector()


class RandomMaxSelectorMixin:
	def create_selector(self):
		return RandomMaxSelector()


class RandomMinSelectorMixin:
	def create_selector(self):
		return RandomMinSelector()


class SoftmaxSelectorMixin:
	def create_selector(self):
		return SoftmaxSelector()


class SoftminSelectorMixin:
	def create_selector(self):
		return SoftminSelector()

