"""Win-rate heat maps (need the optional matplotlib library).

These tests are skipped one by one when matplotlib is not installed. How the
package behaves *without* matplotlib is covered in
``tests/via_ludus/test_optional_dependencies.py``.
"""

import pytest


PLOTS = [
	pytest.param(
		("plot_red_win_matrix", "Red Win Rate", "Blue Player", "Red Player", {"75%", "0%", "33%", "100%"}, "Reds"),
		id="red",
	),
	pytest.param(
		("plot_blue_win_matrix", "Blue Win Rate", "Red Player", "Blue Player", {"25%", "67%", "100%", "0%"}, "Blues"),
		id="blue",
	),
	pytest.param(
		("plot_win_matrix", "Overall Win Rate", "Opponent", "Player", {"71%", "29%", "0%", "100%"}, "RdYlGn"),
		id="overall",
	),
]


@pytest.fixture(params=PLOTS)
def plot(request):
	return request.param


class TestWinMatrixPlots:
	def test_labels_and_title(self, plt, sample_results, plot):
		method, title, xlabel, ylabel, _, _ = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.get_title() == title
		assert ax.get_xlabel() == xlabel
		assert ax.get_ylabel() == ylabel

	def test_axes_are_labelled_with_the_players(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert [label.get_text() for label in ax.get_xticklabels()] == ["alpha", "beta", "gamma"]
		assert [label.get_text() for label in ax.get_yticklabels()] == ["alpha", "beta", "gamma"]

	def test_every_cell_with_games_is_annotated(self, plt, sample_results, plot):
		method, _, _, _, labels, _ = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert {text.get_text() for text in ax.texts} == labels

	def test_cells_without_games_are_not_annotated(self, plt, sample_results):
		_, _, ax = sample_results.plot_red_win_matrix(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 4

		_, _, ax = sample_results.plot_win_matrix(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 6

	def test_color_scale_is_fixed_to_zero_and_one(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.images[0].get_clim() == (0.0, 1.0)

	def test_image_holds_the_win_rates(self, plt, sample_results):
		_, _, ax = sample_results.plot_red_win_matrix(show=False, close=True, return_fig=True)
		data = ax.images[0].get_array()

		assert data.shape == (3, 3)
		assert data[0][1] == pytest.approx(0.75)
		assert data[2][1] == pytest.approx(1.0)

	def test_has_a_colorbar(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert len(fig.axes) == 2
		assert fig.axes[1].get_ylabel() == "Win rate"
		assert [label.get_text() for label in fig.axes[1].get_yticklabels()] == ["0%", "25%", "50%", "75%", "100%"]

	def test_default_color_maps(self, plt, sample_results, plot):
		method, _, _, _, _, cmap = plot

		_, _, ax = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert ax.images[0].get_cmap().name == cmap

	def test_custom_color_map(self, plt, sample_results, plot):
		method = plot[0]

		_, _, ax = getattr(sample_results, method)(cmap="viridis", show=False, close=True, return_fig=True)

		assert ax.images[0].get_cmap().name == "viridis"

	def test_draws_on_a_given_axes(self, plt, sample_results, plot):
		method, title, *_ = plot
		fig, ax = plt.subplots()

		result = getattr(sample_results, method)(ax=ax)

		assert result is None
		assert ax.get_title() == title
		assert len(ax.images) == 1
		assert plt.fignum_exists(fig.number)

	def test_a_given_axes_is_not_closed(self, plt, sample_results, plot):
		method = plot[0]
		fig, ax = plt.subplots()

		getattr(sample_results, method)(ax=ax, show=True, close=True)

		assert plt.fignum_exists(fig.number)

	def test_the_created_figure_is_closed_on_request(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, close=True, return_fig=True)

		assert not plt.fignum_exists(fig.number)

	def test_the_created_figure_stays_open_by_default(self, plt, sample_results, plot):
		method = plot[0]

		_, fig, _ = getattr(sample_results, method)(show=False, return_fig=True)

		assert plt.fignum_exists(fig.number)

	def test_plots_results_without_games(self, plt, plot):
		from via_ludus.tournament import TournamentResults

		method = plot[0]

		_, _, ax = getattr(TournamentResults(["a", "b"]), method)(show=False, close=True, return_fig=True)

		assert len(ax.texts) == 0
