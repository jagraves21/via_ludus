from enum import StrEnum


class Endpoint(StrEnum):
	SOURCE = "S"
	TARGET = "T"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"Endpoint.{self.name}"


def is_endpoint(endpoint):
	return isinstance(endpoint, Endpoint)


def validate_endpoint(endpoint):
	if not is_endpoint(endpoint):
		raise TypeError(
			f"Expected an Endpoint, got {type(endpoint).__name__}"
		)

