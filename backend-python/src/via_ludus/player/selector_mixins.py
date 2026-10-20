from .move_selector import (
	MaxSelector,
	MinSelector,
	RandomMaxSelector,
	RandomMinSelector,
	SoftmaxSelector,
	SoftminSelector,
)


class MaxSelectorMixin:
	def create_selector(self):
		return MaxSelector()


class MinSelectorMixin:
	def create_selector(self):
		return MinSelector()


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

