import json

import pytest
from pydantic import ValidationError

from via_ludus import PlayerColor
from web_service.models import (
	GetAgentsRequest,
	GetAgentsResponse,
	GetMoveRequest,
	GetMoveResponse,
)


# Initial 7 x 7 board.
BOARD_7 = "XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"

# Initial 5 x 5 board.
BOARD_5 = "XRRRXBWBWBBRWRBBWBWBXRRRX"

# 5 x 6 board (rows x cols).
BOARD_5X6 = (
	"XRRRRX"
	"BWWWWB"
	"BWWWWB"
	"BWWWWB"
	"XRRRRX"
)


def move_request(**overrides):
	data = {
		"rows": 7,
		"cols": 7,
		"board": BOARD_7,
		"color": "red",
	}
	data.update(overrides)

	return data


def error_locations(excinfo):
	return {error["loc"] for error in excinfo.value.errors()}


class TestGetAgentsRequest:
	def test_takes_no_fields(self):
		assert GetAgentsRequest().model_dump() == {}

	def test_ignores_unknown_fields(self):
		assert GetAgentsRequest(unexpected=1).model_dump() == {}


class TestGetAgentsResponse:
	def test_stores_the_agent_names(self):
		response = GetAgentsResponse(agents=["Minimax", "MCTS"])

		assert response.agents == ["Minimax", "MCTS"]

	def test_preserves_order(self):
		names = ["Zeta", "Alpha", "Mu"]

		assert GetAgentsResponse(agents=names).agents == names

	def test_accepts_an_empty_list(self):
		assert GetAgentsResponse(agents=[]).agents == []

	def test_serializes_to_json(self):
		response = GetAgentsResponse(agents=["Minimax", "MCTS"])

		assert response.model_dump(mode="json") == {
			"agents": ["Minimax", "MCTS"],
		}

	def test_agents_is_required(self):
		with pytest.raises(ValidationError) as excinfo:
			GetAgentsResponse()

		assert error_locations(excinfo) == {("agents",)}

	@pytest.mark.parametrize(
		"agents",
		["Minimax", None, 3, [1, 2], [None], {"Minimax": 1}],
		ids=["string", "none", "int", "int-items", "none-item", "dict"],
	)
	def test_rejects_anything_but_a_list_of_strings(self, agents):
		with pytest.raises(ValidationError):
			GetAgentsResponse(agents=agents)

	def test_schema_documents_the_field(self):
		field = GetAgentsResponse.model_json_schema()["properties"]["agents"]

		assert field["description"]
		assert field["examples"] == [["Minimax", "MCTS"]]


class TestGetMoveRequest:
	def test_accepts_a_valid_request(self):
		request = GetMoveRequest(**move_request())

		assert request.rows == 7
		assert request.cols == 7
		assert request.board == BOARD_7
		assert request.color is PlayerColor.RED

	@pytest.mark.parametrize(
		"color, expected",
		[
			("red", PlayerColor.RED),
			("blue", PlayerColor.BLUE),
			(PlayerColor.RED, PlayerColor.RED),
			(PlayerColor.BLUE, PlayerColor.BLUE),
		],
		ids=["red", "blue", "red-enum", "blue-enum"],
	)
	def test_color_is_converted_to_a_player_color(self, color, expected):
		request = GetMoveRequest(**move_request(color=color))

		assert request.color is expected

	def test_accepts_the_smallest_board(self):
		request = GetMoveRequest(
			**move_request(rows=5, cols=5, board=BOARD_5),
		)

		assert (request.rows, request.cols) == (5, 5)

	def test_accepts_a_non_square_board(self):
		request = GetMoveRequest(
			**move_request(rows=5, cols=6, board=BOARD_5X6),
		)

		assert (request.rows, request.cols) == (5, 6)

	@pytest.mark.parametrize("rows", [4, 1, 0, -5])
	def test_rejects_too_few_rows(self, rows):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(rows=rows))

		assert error_locations(excinfo) == {("rows",)}

	@pytest.mark.parametrize("cols", [4, 1, 0, -5])
	def test_rejects_too_few_columns(self, cols):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(cols=cols))

		assert error_locations(excinfo) == {("cols",)}

	@pytest.mark.parametrize("field", ["rows", "cols"])
	@pytest.mark.parametrize("value", ["abc", 7.5, None])
	def test_rejects_non_integer_dimensions(self, field, value):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(**{field: value}))

		assert error_locations(excinfo) == {(field,)}

	@pytest.mark.parametrize("field", ["rows", "cols", "board", "color"])
	def test_every_field_is_required(self, field):
		data = move_request()
		del data[field]

		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**data)

		assert error_locations(excinfo) == {(field,)}

	@pytest.mark.parametrize("character", ["Z", "r", "w", " ", "1", "-", "."])
	def test_rejects_unknown_board_characters(self, character):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(board=BOARD_7[:-1] + character))

		assert error_locations(excinfo) == {("board",)}

	def test_rejects_an_empty_board(self):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(board=""))

		assert error_locations(excinfo) == {("board",)}

	@pytest.mark.parametrize(
		"board",
		[BOARD_7[:-1], BOARD_7 + "W", "W"],
		ids=["one-short", "one-long", "single-cell"],
	)
	def test_rejects_a_board_whose_length_is_not_rows_times_cols(self, board):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(board=board))

		assert "Board length must equal rows * cols." in str(excinfo.value)

	def test_length_is_checked_against_the_product_of_the_dimensions(self):
		# 7 * 7 = 49 cells, but this request claims 5 x 6 = 30.
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(rows=5, cols=6))

		assert "Board length must equal rows * cols." in str(excinfo.value)

	@pytest.mark.parametrize(
		"color",
		["green", "RED", "Red", "BLUE", "", None, 1],
		ids=["green", "RED", "Red", "BLUE", "empty", "none", "int"],
	)
	def test_rejects_unknown_colors(self, color):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveRequest(**move_request(color=color))

		assert error_locations(excinfo) == {("color",)}

	def test_ignores_unknown_fields(self):
		request = GetMoveRequest(**move_request(unexpected="value"))

		assert not hasattr(request, "unexpected")

	def test_parses_a_json_document(self):
		request = GetMoveRequest.model_validate_json(
			json.dumps(move_request(color="blue")),
		)

		assert request.color is PlayerColor.BLUE
		assert request.board == BOARD_7

	def test_serializes_the_color_as_its_value(self):
		request = GetMoveRequest(**move_request(color="blue"))

		assert request.model_dump(mode="json") == move_request(color="blue")

	def test_schema_requires_every_field(self):
		schema = GetMoveRequest.model_json_schema()

		assert set(schema["required"]) == {"rows", "cols", "board", "color"}

	def test_schema_documents_the_constraints(self):
		properties = GetMoveRequest.model_json_schema()["properties"]

		assert properties["rows"]["minimum"] == 5
		assert properties["cols"]["minimum"] == 5
		assert properties["board"]["pattern"] == r"^[RBWX]+$"

	def test_schema_describes_every_field(self):
		properties = GetMoveRequest.model_json_schema()["properties"]

		for name in ("rows", "cols", "board", "color"):
			assert properties[name]["description"]

	def test_schema_examples_form_a_valid_request(self):
		properties = GetMoveRequest.model_json_schema()["properties"]

		example = {
			name: properties[name]["examples"][0]
			for name in ("rows", "cols", "board", "color")
		}

		GetMoveRequest(**example)


class TestGetMoveResponse:
	def test_stores_the_coordinates(self):
		response = GetMoveResponse(row=4, col=3)

		assert (response.row, response.col) == (4, 3)

	def test_accepts_the_smallest_coordinates(self):
		response = GetMoveResponse(row=1, col=1)

		assert (response.row, response.col) == (1, 1)

	def test_serializes_to_json(self):
		response = GetMoveResponse(row=4, col=3)

		assert response.model_dump(mode="json") == {"row": 4, "col": 3}

	@pytest.mark.parametrize("value", [0, -1, -100])
	def test_rejects_a_row_on_the_first_row_or_above(self, value):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveResponse(row=value, col=3)

		assert error_locations(excinfo) == {("row",)}

	@pytest.mark.parametrize("value", [0, -1, -100])
	def test_rejects_a_column_on_the_first_column_or_left_of_it(self, value):
		with pytest.raises(ValidationError) as excinfo:
			GetMoveResponse(row=3, col=value)

		assert error_locations(excinfo) == {("col",)}

	def test_has_no_upper_bound_because_it_does_not_know_the_board(self):
		# The upper limit depends on the board size, so the endpoint checks
		# it rather than this model.
		response = GetMoveResponse(row=10_000, col=10_000)

		assert (response.row, response.col) == (10_000, 10_000)

	@pytest.mark.parametrize("field", ["row", "col"])
	def test_every_field_is_required(self, field):
		data = {"row": 3, "col": 3}
		del data[field]

		with pytest.raises(ValidationError) as excinfo:
			GetMoveResponse(**data)

		assert error_locations(excinfo) == {(field,)}

	@pytest.mark.parametrize("value", ["abc", 2.5, None])
	def test_rejects_non_integer_coordinates(self, value):
		with pytest.raises(ValidationError):
			GetMoveResponse(row=value, col=3)

		with pytest.raises(ValidationError):
			GetMoveResponse(row=3, col=value)

	def test_schema_documents_the_constraints(self):
		properties = GetMoveResponse.model_json_schema()["properties"]

		assert properties["row"]["minimum"] == 1
		assert properties["col"]["minimum"] == 1
		assert properties["row"]["description"]
		assert properties["col"]["description"]

	def test_schema_examples_are_interior_cells_of_the_example_board(self):
		properties = GetMoveResponse.model_json_schema()["properties"]
		request = GetMoveRequest.model_json_schema()["properties"]

		rows = request["rows"]["examples"][0]
		cols = request["cols"]["examples"][0]
		row = properties["row"]["examples"][0]
		col = properties["col"]["examples"][0]

		assert 1 <= row < rows - 1
		assert 1 <= col < cols - 1
