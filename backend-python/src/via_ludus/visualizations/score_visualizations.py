import numpy as np

from ..board import (
	Cell,
	validate_player_color,
)
from ..player import validate_scoring_player

from .board_visualizations import _draw_board
from .plotting import with_ax


def _blend_with_black(color, a=0.75):
	from matplotlib.colors import to_rgb, to_hex

	rgb = np.array(to_rgb(color))
	return to_hex((1 - a) * rgb)


def _board_figsize(board):
	size = max(board.rows, board.cols)
	side = max(2, min(12, size * 0.6))

	return side, side


@with_ax
def _plot_agent_scores(
	board,
	agent,
	color,
	cmap,
	ax,
):
	from matplotlib import colormaps
	from matplotlib.colors import Normalize
	from matplotlib.cm import ScalarMappable
	from mpl_toolkits.axes_grid1 import make_axes_locatable

	validate_player_color(color)

	scores = agent.score_moves(board, color)

	scores = {
		position: float(score)
		for position, score in scores.items()
		if position in board.available
	}

	finite_scores = [
		score
		for score in scores.values()
		if np.isfinite(score)
	]

	if finite_scores:
		vmin = min(finite_scores)
		vmax = max(finite_scores)

		if vmin == vmax:
			vmin -= 0.5
			vmax += 0.5

		norm = Normalize(vmin=vmin, vmax=vmax)
	else:
		norm = Normalize(vmin=0, vmax=1)

	colormap = colormaps[cmap]

	position_colors = {}

	for position, score in scores.items():
		if np.isfinite(score):
			position_colors[position] = colormap(norm(score))

	cell_colors = {
		Cell.RED: _blend_with_black("red"),
		Cell.BLUE: _blend_with_black("blue"),
		Cell.WALL: "black",
	}

	for row in range(board.rows):
		for col in range(board.cols):
			cell = board.get(row, col)

			if cell in cell_colors:
				position_colors[(row, col)] = cell_colors[cell]

	_draw_board(board, ax, cell_colors=position_colors)

	ax.set_title(
		f"{agent.get_agent_name()}\n"
		f"Player: {agent.color.name} | "
		f"Evaluating: {color.name}"
	)

	if finite_scores:
		mappable = ScalarMappable(
			norm=norm,
			cmap=colormap,
		)
		mappable.set_array([])

		divider = make_axes_locatable(ax)
		colorbar_ax = divider.append_axes(
			"right",
			size="5%",
			pad=0.1,
		)

		ax.figure.colorbar(
			mappable,
			cax=colorbar_ax,
			label=f"Move Score ({color.name})",
		)


def plot_agent_scores(
	board,
	agent,
	color,
	cmap="YlOrRd_r",
	ax=None,
	figsize=None,
	return_fig=False,
	show=True,
	close=False,
):
	validate_scoring_player(agent)

	if figsize is None and ax is None:
		figsize = _board_figsize(board)

	return _plot_agent_scores(
		board,
		agent,
		color,
		cmap=cmap,
		ax=ax,
		figsize=figsize or (2, 2),
		return_fig=return_fig,
		show=show,
		close=close,
	)

