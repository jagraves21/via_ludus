from enum import Enum


class Endpoint(tuple, Enum):
	SOURCE = (-1, "S")
	TARGET = (-1, "T")

	def __str__(self):
		return self.value[1]

	def __repr__(self):
		return f"Endpoint.{self.name}"


def is_endpoint(endpoint):
	return isinstance(endpoint, Endpoint)


def validate_endpoint(endpoint):
	if not is_endpoint(endpoint):
		raise TypeError(
			f"Expected an Endpoint, got {type(endpoint).__name__}"
		)

