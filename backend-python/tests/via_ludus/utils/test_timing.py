import pytest

from via_ludus.utils import Timer, time_block, time_it


@pytest.fixture
def clock(monkeypatch):
	"""A fake perf_counter whose time only moves when the test says so."""
	class Clock:
		def __init__(self):
			self.now = 100.0

		def __call__(self):
			return self.now

		def advance(self, seconds):
			self.now += seconds

	fake = Clock()
	monkeypatch.setattr("via_ludus.utils.timing.perf_counter", fake)

	return fake


class TestTimeIt:
	def test_returns_the_result_of_the_function(self, capsys):
		@time_it
		def add(first, second):
			return first + second

		assert add(2, 3) == 5

	def test_passes_positional_and_keyword_arguments(self, capsys):
		@time_it
		def describe(first, second, *, third):
			return (first, second, third)

		assert describe(1, 2, third=3) == (1, 2, 3)

	def test_preserves_function_metadata(self):
		@time_it
		def documented():
			"""Docstring."""

		assert documented.__name__ == "documented"
		assert documented.__doc__ == "Docstring."

	def test_prints_the_qualified_name_and_elapsed_time(self, clock, capsys):
		@time_it
		def work():
			clock.advance(90.25)

		work()

		assert capsys.readouterr().out == f"{work.__module__}.work 0:01:30.250000\n"

	def test_prints_a_zero_duration(self, clock, capsys):
		@time_it
		def instant():
			pass

		instant()

		assert capsys.readouterr().out == f"{instant.__module__}.instant 0:00:00\n"

	def test_prints_once_per_call(self, clock, capsys):
		@time_it
		def work():
			clock.advance(1)

		work()
		work()

		assert capsys.readouterr().out.count("work 0:00:01") == 2

	def test_prints_the_time_and_reraises_when_the_function_fails(self, clock, capsys):
		@time_it
		def failing():
			clock.advance(2.5)
			raise RuntimeError("boom")

		with pytest.raises(RuntimeError, match="boom"):
			failing()

		assert capsys.readouterr().out == f"{failing.__module__}.failing 0:00:02.500000\n"


class TestTimer:
	def test_default_name(self):
		assert Timer().name == "Block"

	def test_custom_name(self):
		assert Timer("plot").name == "plot"

	def test_empty_name_falls_back_to_the_default(self):
		assert Timer("").name == "Block"
		assert Timer(None).name == "Block"

	def test_elapsed_is_unknown_before_use(self):
		assert Timer().elapsed is None

	def test_enter_returns_the_timer(self, capsys):
		timer = Timer()

		with timer as entered:
			pass

		assert entered is timer

	def test_measures_the_block(self, clock, capsys):
		with Timer() as timer:
			clock.advance(2.5)

		assert timer.elapsed == 2.5

	def test_prints_the_name_and_elapsed_seconds(self, clock, capsys):
		with Timer("training"):
			clock.advance(2.5)

		assert capsys.readouterr().out == "training : 2.500000 s\n"

	def test_prints_the_default_name(self, clock, capsys):
		with Timer():
			clock.advance(0.000001)

		assert capsys.readouterr().out == "Block : 0.000001 s\n"

	def test_nothing_is_printed_before_the_block_ends(self, clock, capsys):
		with Timer("training"):
			clock.advance(1)

			assert capsys.readouterr().out == ""

	def test_elapsed_is_recorded_and_the_exception_propagates(self, clock, capsys):
		timer = Timer("failing")

		with pytest.raises(ValueError, match="bad"):
			with timer:
				clock.advance(1.5)
				raise ValueError("bad")

		assert timer.elapsed == 1.5
		assert capsys.readouterr().out == "failing : 1.500000 s\n"

	def test_a_timer_can_be_reused(self, clock, capsys):
		timer = Timer("again")

		with timer:
			clock.advance(1)
		with timer:
			clock.advance(3)

		assert timer.elapsed == 3
		assert capsys.readouterr().out == "again : 1.000000 s\nagain : 3.000000 s\n"

	def test_nested_timers_are_independent(self, clock, capsys):
		with Timer("outer") as outer:
			clock.advance(1)

			with Timer("inner") as inner:
				clock.advance(2)

			clock.advance(4)

		assert inner.elapsed == 2
		assert outer.elapsed == 7


class TestTimeBlock:
	def test_prints_the_name_and_elapsed_time(self, clock, capsys):
		with time_block("plot generation"):
			clock.advance(65.5)

		assert capsys.readouterr().out == "plot generation : 0:01:05.500000\n"

	def test_nothing_is_printed_before_the_block_ends(self, clock, capsys):
		with time_block("plot generation"):
			clock.advance(1)

			assert capsys.readouterr().out == ""

	def test_the_context_manager_yields_nothing(self, clock, capsys):
		with time_block("plot generation") as value:
			pass

		assert value is None

	def test_prints_the_time_and_reraises_when_the_block_fails(self, clock, capsys):
		with pytest.raises(RuntimeError, match="boom"):
			with time_block("failing"):
				clock.advance(2.5)
				raise RuntimeError("boom")

		assert capsys.readouterr().out == "failing : 0:00:02.500000\n"

	def test_blocks_can_be_nested(self, clock, capsys):
		with time_block("outer"):
			clock.advance(1)

			with time_block("inner"):
				clock.advance(2)

		assert capsys.readouterr().out == "inner : 0:00:02\nouter : 0:00:03\n"
