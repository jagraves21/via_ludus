import pytest

from via_ludus.utils import OptionalDependencyError
from via_ludus.visualizations import with_ax


@pytest.fixture
def drawn():
	"""A decorated function that records what it was called with."""
	calls = []

	@with_ax
	def draw(*args, ax, **kwargs):
		"""Draw something."""
		calls.append((args, kwargs, ax))

		return "result"

	draw.calls = calls

	return draw


@pytest.fixture
def show_calls(plt, monkeypatch):
	"""Replace plt.show and record each call (and whether the figure was open)."""
	calls = []

	def fake_show(*args, **kwargs):
		calls.append(list(plt.get_fignums()))

	monkeypatch.setattr(plt, "show", fake_show)

	return calls


class TestCreatedFigure:
	def test_the_function_receives_an_axes(self, plt, drawn, show_calls):
		drawn(show=False)

		(_, _, ax), = drawn.calls

		assert ax.figure is not None
		assert ax in ax.figure.axes

	def test_returns_the_functions_result(self, plt, drawn, show_calls):
		assert drawn(show=False) == "result"

	def test_positional_and_keyword_arguments_are_passed_through(self, plt, drawn, show_calls):
		drawn(1, "two", show=False, option=3)

		(args, kwargs, _), = drawn.calls

		assert args == (1, "two")
		assert kwargs == {"option": 3}

	def test_default_figure_size(self, plt, drawn, show_calls):
		_, fig, _ = drawn(show=False, return_fig=True)

		assert tuple(fig.get_size_inches()) == (2.0, 2.0)

	def test_custom_figure_size(self, plt, drawn, show_calls):
		_, fig, _ = drawn(figsize=(5, 3), show=False, return_fig=True)

		assert tuple(fig.get_size_inches()) == (5.0, 3.0)

	def test_each_call_creates_a_new_figure(self, plt, drawn, show_calls):
		_, first, _ = drawn(show=False, return_fig=True)
		_, second, _ = drawn(show=False, return_fig=True)

		assert first is not second

	def test_return_fig_returns_result_figure_and_axes(self, plt, drawn, show_calls):
		result, fig, ax = drawn(show=False, return_fig=True)

		assert result == "result"
		assert ax.figure is fig
		assert drawn.calls[0][2] is ax


class TestShow:
	def test_shows_by_default(self, plt, drawn, show_calls):
		drawn()

		assert len(show_calls) == 1

	def test_show_can_be_disabled(self, plt, drawn, show_calls):
		drawn(show=False)

		assert show_calls == []

	def test_the_figure_is_still_open_when_shown(self, plt, drawn, show_calls):
		_, fig, _ = drawn(close=True, return_fig=True)

		assert show_calls == [[fig.number]]

	def test_a_given_axes_is_not_shown(self, plt, drawn, show_calls):
		_, ax = plt.subplots()

		drawn(ax=ax, show=True)

		assert show_calls == []


class TestClose:
	def test_the_figure_stays_open_by_default(self, plt, drawn, show_calls):
		_, fig, _ = drawn(show=False, return_fig=True)

		assert plt.fignum_exists(fig.number)

	def test_the_figure_is_closed_on_request(self, plt, drawn, show_calls):
		_, fig, _ = drawn(show=False, close=True, return_fig=True)

		assert not plt.fignum_exists(fig.number)

	def test_the_closed_figure_can_still_be_used(self, plt, drawn, show_calls):
		_, fig, ax = drawn(show=False, close=True, return_fig=True)

		assert ax.figure is fig
		assert tuple(fig.get_size_inches()) == (2.0, 2.0)


class TestGivenAxes:
	def test_the_function_draws_on_the_given_axes(self, plt, drawn, show_calls):
		fig, ax = plt.subplots()

		drawn(ax=ax, show=False)

		assert drawn.calls[0][2] is ax

	def test_no_new_figure_is_created(self, plt, drawn, show_calls):
		fig, ax = plt.subplots()

		drawn(ax=ax, show=False)

		assert plt.get_fignums() == [fig.number]

	def test_the_figure_size_is_ignored(self, plt, drawn, show_calls):
		fig, ax = plt.subplots(figsize=(4, 4))

		drawn(ax=ax, figsize=(9, 9), show=False)

		assert tuple(fig.get_size_inches()) == (4.0, 4.0)

	def test_the_figure_is_never_closed(self, plt, drawn, show_calls):
		fig, ax = plt.subplots()

		drawn(ax=ax, show=False, close=True)

		assert plt.fignum_exists(fig.number)

	def test_return_fig_returns_the_axes_figure(self, plt, drawn, show_calls):
		fig, ax = plt.subplots()

		result, returned_fig, returned_ax = drawn(ax=ax, show=False, return_fig=True)

		assert result == "result"
		assert returned_fig is fig
		assert returned_ax is ax


class TestDecorator:
	def test_preserves_function_metadata(self, drawn):
		assert drawn.__name__ == "draw"
		assert drawn.__doc__ == "Draw something."

	def test_can_decorate_methods(self, plt, show_calls):
		class Plotter:
			@with_ax
			def plot(self, value, ax):
				return (self, value, ax)

		plotter = Plotter()

		result, _, ax = plotter.plot(7, show=False, return_fig=True)

		assert result == (plotter, 7, ax)

	def test_errors_from_the_function_propagate(self, plt, show_calls):
		@with_ax
		def failing(ax):
			raise RuntimeError("drawing failed")

		with pytest.raises(RuntimeError, match="drawing failed"):
			failing(show=False)

		assert show_calls == []


class TestWithoutMatplotlib:
	"""These tests run whether or not matplotlib is installed."""

	def test_a_helpful_error_is_raised(self, block_imports):
		block_imports("matplotlib")

		@with_ax
		def draw(ax):
			raise AssertionError("must not be called")

		with pytest.raises(OptionalDependencyError) as excinfo:
			draw(show=False)

		message = str(excinfo.value)

		assert "matplotlib" in message
		assert 'pip install -e ".[visualization]"' in message
		assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)

	def test_decorating_does_not_require_matplotlib(self, block_imports):
		block_imports("matplotlib")

		@with_ax
		def draw(ax):
			pass

		assert callable(draw)
