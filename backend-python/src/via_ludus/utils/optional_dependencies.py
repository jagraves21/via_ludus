
from functools import wraps
from importlib import import_module


class OptionalDependencyError(ImportError):
	"""Optional dependency unavailable."""

def requires_extra(module_name, extra_name):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			try:
				import_module(module_name)
			except ModuleNotFoundError as exc:
				# Only handle the requested dependency being missing,
				# not a missing dependency inside that module.
				if exc.name != module_name and not (
					exc.name and module_name.startswith(exc.name + ".")
				):
					raise

				raise OptionalDependencyError(
					f"{func.__module__}.{func.__qualname__}() requires "
					f"{module_name!r}. From the via-ludus project root, run "
					f'`pip install -e ".[{extra_name}]"`.'
				) from exc

			return func(*args, **kwargs)

		return wrapper

	return decorator

