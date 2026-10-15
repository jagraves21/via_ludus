from pydantic import BaseModel


class GetAgentsRequest(BaseModel):
	pass


class GetAgentsResponse(BaseModel):
	agents: list[str]


class GetMoveRequest(BaseModel):
	rows: int
	cols: int
	board: str
	color: str


class GetMoveResponse(BaseModel):
	row: int
	col: int

