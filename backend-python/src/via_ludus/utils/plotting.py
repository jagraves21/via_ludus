from functools import wraps

import matplotlib.pyplot as plt


def with_ax(func):
	@wraps(func)
	def wrapper(
		*args,
		ax=None,
		figsize=(2, 2),
		return_fig=False,
		show=True,
		close=False,
		**kwargs,
	):
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

