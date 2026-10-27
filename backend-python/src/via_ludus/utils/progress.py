import warnings

try:
	from tqdm.auto import tqdm
except ModuleNotFoundError as exc:
	if exc.name != "tqdm":
		raise

	class tqdm:
		_warned = False

		def __init__(
			self,
			iterable=None,
			*args,
			total=None,
			**kwargs,
		):
			if not tqdm._warned:
				warnings.warn(
					"tqdm is not installed. Progress bars are disabled. "
					"Install it with `pip install \"via-ludus[progress]\"` "
					"to enable them.",
					RuntimeWarning,
					stacklevel=2,
				)
				tqdm._warned = True

			self.iterable = iterable
			self.total = total
			self.n = 0

		def __iter__(self):
			if self.iterable is None:
				return iter(())

			return self._iterate()

		def _iterate(self):
			for item in self.iterable:
				self.update(1)
				yield item

		def update(self, n=1):
			self.n += n

		def set_postfix(self, *args, **kwargs):
			pass

		def set_postfix_str(self, *args, **kwargs):
			pass

		def set_description(self, *args, **kwargs):
			pass

		def refresh(self):
			pass

		def close(self):
			pass

		def __enter__(self):
			return self

		def __exit__(self, exc_type, exc_value, traceback):
			self.close()
			return False

