from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from time import perf_counter


def time_it(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		start = perf_counter()

		try:
			return func(*args, **kwargs)
		finally:
			elapsed = perf_counter() - start

			print(
				f"{func.__module__}.{func.__name__} "
				f"{timedelta(seconds=elapsed)}"
			)

	return wrapper


class Timer:
	def __init__(self, name=None):
		self.name = name or "Block"
		self.elapsed = None

	def __enter__(self):
		self.start = perf_counter()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.elapsed = perf_counter() - self.start

		print(
			f"{self.name} : {self.elapsed:.6f} s"
		)


@contextmanager
def time_block(name):
	# with time_block("plot generation"):
	#	create_plot()
	start = perf_counter()

	try:
		yield
	finally:
		elapsed = perf_counter() - start

		print(
			f"{name} : {timedelta(seconds=elapsed)}"
		)

