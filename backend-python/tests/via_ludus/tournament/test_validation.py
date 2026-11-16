import pytest

from via_ludus.tournament import (
	TournamentResults,
	is_tournament_results,
	validate_tournament_results,
)


class _LookAlike:
	players = ()


class TestIsTournamentResults:
	def test_accepts_tournament_results(self):
		assert is_tournament_results(TournamentResults(["a", "b"])) is True

	def test_accepts_empty_tournament_results(self):
		assert is_tournament_results(TournamentResults([])) is True

	def test_accepts_subclass_instances(self):
		class Custom(TournamentResults):
			pass

		assert is_tournament_results(Custom(["a"])) is True

	@pytest.mark.parametrize(
		"value",
		[
			None,
			{},
			[],
			"results",
			1,
			object(),
			_LookAlike(),
			TournamentResults,
		],
		ids=["none", "dict", "list", "str", "int", "object", "look-alike", "class"],
	)
	def test_rejects_everything_else(self, value):
		assert is_tournament_results(value) is False

	def test_rejects_the_serialized_form(self):
		assert is_tournament_results(TournamentResults(["a"]).to_json()) is False


class TestValidateTournamentResults:
	def test_accepts_tournament_results(self):
		assert validate_tournament_results(TournamentResults(["a", "b"])) is None

	@pytest.mark.parametrize(
		"value, type_name",
		[
			(None, "NoneType"),
			({}, "dict"),
			("results", "str"),
			(3, "int"),
			(_LookAlike(), "_LookAlike"),
			(TournamentResults, "type"),
		],
		ids=["none", "dict", "str", "int", "look-alike", "class"],
	)
	def test_rejects_other_types_naming_the_offending_type(self, value, type_name):
		with pytest.raises(TypeError, match=f"Expected a TournamentResults, got {type_name}$"):
			validate_tournament_results(value)
