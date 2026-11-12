import logging

from typing import Annotated

from fastapi import (
	APIRouter,
	HTTPException,
	Path,
)

from ..exceptions import AgentComputationError

from ..models import (
	GetAgentsResponse,
	GetMoveRequest,
	GetMoveResponse,
)

from ..services import (
	get_agents,
	get_move,
)


logger = logging.getLogger(__name__)


router = APIRouter(
	prefix="/agents",
	tags=["Agents"],
)


@router.get(
	"",
	response_model=GetAgentsResponse,
	summary="List available agents",
	description=(
		"Returns the names of all AI agents currently available "
		"in the backend installation."
	),
	operation_id="get_agents",
	response_description="The available AI agent names.",
)
def get_agents_endpoint() -> GetAgentsResponse:
	return GetAgentsResponse(
		agents=get_agents(),
	)


@router.post(
	"/{agent_name}/move",
	response_model=GetMoveResponse,
	summary="Request an agent move",
	description=(
		"Requests a move from the specified AI agent. "
		"The agent must be one of the agents returned by "
		"GET /api/agents."
	),
	operation_id="get_agent_move",
	response_description="The selected move coordinates.",
	responses={
		404: {
			"description": "The specified agent does not exist.",
			"content": {
				"application/json": {
					"example": {
						"detail": (
							"Agent 'unknown-agent' not found. "
							"Available agents: Minimax, MCTS."
						),
					},
				},
			},
		},
		422: {
			"description": (
				"The request contains invalid board dimensions, board "
				"contents, or player color."
			),
			"content": {
				"application/json": {
					"example": {
						"detail": "Invalid player color 'green'. "
						"Valid colors: red, blue."
					},
				},
			},
		},
		500: {
			"description": (
				"The agent failed to compute a move, encountered "
				"an internal error, or returned invalid coordinates."
			),
			"content": {
				"application/json": {
					"example": {
						"detail": (
							"Agent 'Minimax' failed to compute a move: "
							"Iterative algorithm did not converge."
						),
					},
				},
			},
		},
	},
)
def get_move_endpoint(
	agent_name: Annotated[
		str,
		Path(
			description=(
				"Name of the AI agent. Must match a name "
				"returned by GET /api/agents."
			),
		),
	],
	request: GetMoveRequest,
) -> GetMoveResponse:
	try:
		result = get_move(
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
		)
	except KeyError as exc:
		logger.warning(
			"Unknown agent: agent=%s, rows=%d, cols=%d, "
			"board=%s, color=%s, error=%s",
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
			exc,
		)
		raise HTTPException(
			status_code=404,
			detail=exc.args[0],
		) from exc
	except ValueError as exc:
		logger.warning(
			"Invalid move request: agent=%s, rows=%d, cols=%d, "
			"board=%s, color=%s, error=%s",
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
			exc,
		)
		raise HTTPException(
			status_code=422,
			detail=str(exc),
		) from exc
	except AgentComputationError as exc:
		logger.exception(
			"Agent computation failed: agent=%s, rows=%d, cols=%d, "
			"board=%s, color=%s, error=%s",
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
			exc,
		)
		raise HTTPException(
			status_code=500,
			detail=str(exc),
		) from exc
	except Exception as exc:
		logger.exception(
			"Unexpected error computing move: agent=%s, rows=%d, "
			"cols=%d, board=%s, color=%s, error=%s",
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
			exc,
		)
		raise HTTPException(
			status_code=500,
			detail="An unexpected error occurred while computing the move.",
		) from exc

	try:
		row, col = result
	except (TypeError, ValueError) as exc:
		logger.error(
			"Agent returned a malformed move: agent=%s, result=%r",
			agent_name,
			result,
		)
		raise HTTPException(
			status_code=500,
			detail="Agent returned a malformed move.",
		) from exc

	if not (
		1 <= row < request.rows - 1
		and 1 <= col < request.cols - 1
	):
		logger.error(
			"Agent returned invalid coordinates: agent=%s, rows=%d, "
			"cols=%d, board=%s, color=%s, row=%s, col=%s",
			agent_name,
			request.rows,
			request.cols,
			request.board,
			request.color,
			row,
			col,
		)
		raise HTTPException(
			status_code=500,
			detail=(
				"Agent returned a move outside the valid "
				"interior board positions."
			),
		)

	return GetMoveResponse(
		row=row,
		col=col,
	)

