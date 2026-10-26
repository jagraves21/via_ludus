from matplotlib import pyplot as plt

from ..board.base import validate_board

from .plotting import with_ax


def _draw_board(board, ax, cell_colors=None):
	validate_board(board)

	if cell_colors is None:
		cell_colors = {}

	for row in range(board.rows):
		for col in range(board.cols):
			cell = board.get(row, col)

			ax.add_patch(
				plt.Rectangle(
					(col, board.rows - row - 1),
					1,
					1,
					facecolor=cell_colors.get(
						(row, col),
						cell.color,
					),
					edgecolor="black",
				)
			)

	ax.set_xlim(0, board.cols)
	ax.set_ylim(0, board.rows)
	ax.set_aspect("equal")
	ax.axis("off")

	return ax


@with_ax
def _plot_board(board, ax):
	return _draw_board(board, ax)


def plot_board(
	board,
	ax=None,
	figsize=None,
	return_fig=False,
	show=True,
	close=False,
):
	if figsize is None and ax is None:
		size = max(board.rows, board.cols)
		side = max(2, min(12, size * 0.2))
		figsize = (side, side)

	return _plot_board(
		board,
		ax=ax,
		figsize=figsize or (2, 2),
		return_fig=return_fig,
		show=show,
		close=close,
	)

