from enum import StrEnum


class Endpoint(StrEnum):
	SOURCE = "S"
	TARGET = "T"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"Endpoint.{self.name}"

