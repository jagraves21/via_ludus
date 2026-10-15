from fastapi import APIRouter

from ..models import (
	GetAgentsResponse,
	GetMoveRequest,
	GetMoveResponse,
)
from ..services import get_agents, get_move


router = APIRouter(
	prefix="/agents",
	tags=["Agents"],
)


@router.get("", response_model=GetAgentsResponse)
def get_agents_endpoint() -> GetAgentsResponse:
	return GetAgentsResponse(
		agents=get_agents(),
	)


@router.post("/{agent_name}/move", response_model=GetMoveResponse)
def get_move_endpoint(
	agent_name: str,
	request: GetMoveRequest,
) -> GetMoveResponse:
	row, col = get_move(
		agent_name,
		request.rows,
		request.cols,
		request.board,
		request.color,
	)

	return GetMoveResponse(
		row=row,
		col=col,
	)
