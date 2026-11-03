"""DataFrame views of TournamentResults (need the optional pandas library).

These tests are skipped one by one when pandas is not installed. How the
package behaves *without* pandas is covered in
``tests/via_ludus/test_optional_dependencies.py``.
"""

import math

import pytest

from via_ludus.tournament import TournamentResults


@pytest.fixture
def pd():
	return pytest.importorskip("pandas")


PLAYERS = ["alpha", "beta", "gamma"]


def _same(left, right):
	both_nan = (
		isinstance(left, float)
		and isinstance(right, float)
		and math.isnan(left)
		and math.isnan(right)
	)

	return both_nan or left == right


class TestSummaryDataFrame:
	def test_is_a_data_frame_with_the_summary_columns(self, pd, sample_results):
		frame = sample_results.summary_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == list(sample_results.summary()[0])

	def test_rows_match_the_summary(self, sample_results):
		frame = sample_results.summary_df()

		assert frame.to_dict("records") == sample_results.summary()

	def test_rows_are_sorted_by_win_rate(self, sample_results):
		assert sample_results.summary_df()["player"].tolist() == ["gamma", "alpha", "beta"]

	def test_without_games(self, pd):
		frame = TournamentResults(["a", "b"]).summary_df()

		assert frame["player"].tolist() == ["a", "b"]
		assert (frame["total_games"] == 0).all()


class TestHeadToHeadDataFrame:
	def test_columns(self, pd, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert list(frame.columns) == list(sample_results.head_to_head_summary()[0])

	def test_rows_follow_the_player_order(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert list(zip(frame["red_player"], frame["blue_player"])) == [
			("alpha", "beta"),
			("alpha", "gamma"),
			("beta", "alpha"),
			("gamma", "beta"),
		]

	def test_player_columns_are_ordered_categoricals(self, pd, sample_results):
		frame = sample_results.head_to_head_summary_df()

		for column in ("red_player", "blue_player"):
			assert isinstance(frame[column].dtype, pd.CategoricalDtype)
			assert frame[column].cat.ordered is True
			assert list(frame[column].cat.categories) == PLAYERS

	def test_index_is_reset(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		assert frame.index.tolist() == [0, 1, 2, 3]

	def test_values_match_the_summary(self, sample_results):
		frame = sample_results.head_to_head_summary_df()

		for row, expected in zip(frame.to_dict("records"), sample_results.head_to_head_summary()):
			assert row.keys() == expected.keys()
			for key in expected:
				assert _same(row[key], expected[key]), key

	def test_without_games(self, pd):
		frame = TournamentResults(["a", "b"]).head_to_head_summary_df()

		assert frame.empty
		assert "red_win_rate" in frame.columns

class TestFirstMoveAdvantageDataFrame:
	def test_columns_and_rows(self, pd, full_results):
		frame = full_results.first_move_advantage_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == [
			"player",
			"num_games",
			"red_wins",
			"red_win_rate",
			"blue_wins",
			"blue_win_rate",
		]
		assert frame.to_dict("records") == full_results.first_move_advantage()

	def test_without_self_play(self, pd, sample_results):
		frame = sample_results.first_move_advantage_df()

		assert frame.empty
		assert "red_win_rate" in frame.columns


class TestMatrixDataFrames:
	@pytest.mark.parametrize("method", ["red_win_matrix_df", "blue_win_matrix_df", "win_matrix_df"])
	@pytest.mark.parametrize("rates", [True, False])
	def test_shape_index_and_columns(self, pd, sample_results, method, rates):
		frame = getattr(sample_results, method)(rates=rates)

		assert isinstance(frame, pd.DataFrame)
		assert frame.index.tolist() == PLAYERS
		assert frame.columns.tolist() == PLAYERS

	@pytest.mark.parametrize(
		"method, matrix_method",
		[
			("red_win_matrix_df", "red_win_matrix"),
			("blue_win_matrix_df", "blue_win_matrix"),
			("win_matrix_df", "win_matrix"),
		],
	)
	@pytest.mark.parametrize("rates", [True, False])
	def test_values_match_the_dictionaries(self, sample_results, method, matrix_method, rates):
		frame = getattr(sample_results, method)(rates=rates)
		matrix = getattr(sample_results, matrix_method)(rates=rates)

		for row in PLAYERS:
			for col in PLAYERS:
				assert _same(float(frame.loc[row, col]), matrix[row][col]), (row, col)

	def test_rates_default_to_true(self, sample_results):
		assert sample_results.red_win_matrix_df().loc["alpha", "beta"] == pytest.approx(0.75)

	def test_cells_without_games_are_nan(self, pd, sample_results):
		frame = sample_results.red_win_matrix_df()

		assert pd.isna(frame.loc["alpha", "alpha"])
		assert pd.isna(frame.loc["beta", "gamma"])
		assert frame.loc["gamma", "beta"] == pytest.approx(1.0)

	def test_blue_matrix_rows_are_the_blue_players(self, sample_results):
		frame = sample_results.blue_win_matrix_df()

		assert frame.loc["beta", "alpha"] == pytest.approx(0.25)

	def test_overall_matrix(self, sample_results):
		frame = sample_results.win_matrix_df()

		assert frame.loc["alpha", "beta"] == pytest.approx(5 / 7)
		assert frame.loc["beta", "alpha"] == pytest.approx(2 / 7)

	def test_matrices_without_games_are_all_nan(self, pd):
		frame = TournamentResults(["a", "b"]).win_matrix_df()

		assert frame.isna().all().all()
		assert frame.index.tolist() == ["a", "b"]

	@pytest.mark.parametrize("rates", [True, False])
	def test_win_matrices_df(self, pd, sample_results, rates):
		frames = sample_results.win_matrices_df(rates=rates)

		assert len(frames) == 3
		assert all(isinstance(frame, pd.DataFrame) for frame in frames)
		red, blue, overall = frames
		for row in PLAYERS:
			for col in PLAYERS:
				assert _same(float(red.loc[row, col]), sample_results.win_matrices(rates=rates)[0][row][col])
				assert _same(float(blue.loc[row, col]), sample_results.win_matrices(rates=rates)[1][row][col])
				assert _same(float(overall.loc[row, col]), sample_results.win_matrices(rates=rates)[2][row][col])


class TestEloDataFrame:
	def test_columns(self, pd, sample_results):
		frame = sample_results.elo_ratings_df()

		assert isinstance(frame, pd.DataFrame)
		assert list(frame.columns) == ["player", "elo", "games_played"]

	def test_rows_match_the_ratings(self, sample_results):
		assert sample_results.elo_ratings_df().to_dict("records") == sample_results.elo_ratings()

	def test_parameters_are_forwarded(self, sample_results):
		frame = sample_results.elo_ratings_df(initial_rating=1000, k_factor=16, seed=3)

		assert frame.to_dict("records") == sample_results.elo_ratings(
			initial_rating=1000,
			k_factor=16,
			seed=3,
		)

	def test_invalid_k_factor_is_rejected(self, sample_results):
		with pytest.raises(ValueError, match="k_factor must be positive"):
			sample_results.elo_ratings_df(k_factor=0)


class TestWithoutPandas:
	"""These tests run whether or not pandas is installed."""

	@pytest.mark.parametrize(
		"method",
		[
			"summary_df",
			"head_to_head_summary_df",
			"red_win_matrix_df",
			"blue_win_matrix_df",
			"win_matrix_df",
			"win_matrices_df",
			"elo_ratings_df",
			"first_move_advantage_df",
		],
	)
	def test_every_data_frame_method_explains_the_missing_dependency(self, block_imports, sample_results, method):
		from via_ludus.utils import OptionalDependencyError

		block_imports("pandas")

		with pytest.raises(OptionalDependencyError) as excinfo:
			getattr(sample_results, method)()

		assert "pandas" in str(excinfo.value)
		assert 'pip install -e ".[dataframe]"' in str(excinfo.value)

	def test_the_plain_methods_work_without_pandas(self, block_imports, full_results):
		block_imports("pandas")

		assert full_results.first_move_advantage()
		assert full_results.summary()
