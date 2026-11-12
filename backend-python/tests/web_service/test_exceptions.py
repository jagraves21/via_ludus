import pytest

from web_service.exceptions import AgentComputationError


class TestAgentComputationError:
	def test_is_an_exception(self):
		assert issubclass(AgentComputationError, Exception)

	@pytest.mark.parametrize(
		"builtin",
		[KeyError, ValueError],
		ids=lambda builtin: builtin.__name__,
	)
	def test_is_not_a_key_error_or_value_error(self, builtin):
		# The agents endpoint maps KeyError to 404 and ValueError to 422,
		# and handles both before AgentComputationError. Subclassing either
		# would send agent failures to the wrong status code.
		assert not issubclass(AgentComputationError, builtin)

	def test_message_is_preserved(self):
		assert str(AgentComputationError("no move")) == "no move"

	def test_can_be_raised_and_caught(self):
		with pytest.raises(AgentComputationError, match="boom"):
			raise AgentComputationError("boom")

	def test_chains_the_original_error(self):
		original = RuntimeError("root cause")

		with pytest.raises(AgentComputationError) as excinfo:
			try:
				raise original
			except RuntimeError as exc:
				raise AgentComputationError("wrapped") from exc

		assert excinfo.value.__cause__ is original
