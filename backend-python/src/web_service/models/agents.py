from pydantic import (
	BaseModel,
	Field,
	model_validator,
)

from via_ludus import PlayerColor


class GetAgentsRequest(BaseModel):
	pass


class GetAgentsResponse(BaseModel):
	agents: list[str] = Field(
		description="Names of the AI agents currently available.",
		examples=[["Minimax", "MCTS"]],
	)


class GetMoveRequest(BaseModel):
	rows: int = Field(
		ge=5,
		description="Number of rows in the board. Must be at least 5.",
		examples=[7],
	)

	cols: int = Field(
		ge=5,
		description="Number of columns in the board. Must be at least 5.",
		examples=[7],
	)

	board: str = Field(
		pattern=r"^[RBWX]+$",
		description=(
			"Board contents encoded as a row-major string. "
			"Each character represents one cell: "
			"R (red), B (blue), W (white), or X (wall). "
			"The string must contain exactly rows * cols characters."
		),
		examples=["XRRRRRXBWBWBWBBRWRWRBBWBWBWBBRWRWRBBWBWBWBXRRRRRX"],
	)

	color: PlayerColor = Field(
		description="Player color for which the agent should select a move.",
		examples=["red"],
	)

	@model_validator(mode="after")
	def validate_board(self):
		if len(self.board) != self.rows * self.cols:
			raise ValueError(
				"Board length must equal rows * cols."
			)

		invalid_cells = set(self.board) - set("RBWX")

		if invalid_cells:
			raise ValueError(
				f"Invalid board cell values: {sorted(invalid_cells)}."
			)

		return self


class GetMoveResponse(BaseModel):
	row: int = Field(
		ge=1,
		description=(
			"Zero-based row index of the selected move. "
			"Must exclude the first and last rows."
		),
		examples=[4],
	)

	col: int = Field(
		ge=1,
		description=(
			"Zero-based column index of the selected move. "
			"Must exclude the first and last columns."
		),
		examples=[3],
	)

