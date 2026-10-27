from functools import wraps

from ..utils import requires_extra


def with_ax(func):
	@wraps(func)
	@requires_extra("matplotlib.pyplot", "visualization")
	def wrapper(
		*args,
		ax=None,
		figsize=(2, 2),
		return_fig=False,
		show=True,
		close=False,
		**kwargs,
	):
		import matplotlib.pyplot as plt

		created = ax is None

		if created:
			fig, ax = plt.subplots(figsize=figsize)
		else:
			fig = ax.figure

		result = func(*args, ax=ax, **kwargs)

		if created and show:
			plt.show()

		if created and close:
			plt.close(fig)

		if return_fig:
			return result, fig, ax

		return result

	return wrapper

