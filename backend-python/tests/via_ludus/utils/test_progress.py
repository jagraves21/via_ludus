"""The tqdm progress bar (or its fallback when tqdm is not installed).

The fallback is exercised in-process: ``block_imports`` makes tqdm look
missing and ``via_ludus/utils/progress.py`` is executed afresh, so the tests
behave the same whether or not tqdm is installed on the developer's machine.
The same module is also tested in a separate process in
``tests/via_ludus/test_optional_dependencies.py``.
"""

import importlib.util
import sys
import warnings
from pathlib import Path

import pytest

import via_ludus.utils.progress as progress_module


PROGRESS_PATH = Path(progress_module.__file__)


def _load_progress_module():
	spec = importlib.util.spec_from_file_location(
		"via_ludus_progress_under_test",
		PROGRESS_PATH,
	)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)

	return module


@pytest.fixture
def isolated_tqdm_modules():
	"""Hide any imported tqdm and discard whatever the test imports as tqdm."""
	def is_tqdm(name):
		return name == "tqdm" or name.startswith("tqdm.")

	saved = {name: module for name, module in sys.modules.items() if is_tqdm(name)}

	for name in saved:
		del sys.modules[name]

	yield

	for name in [name for name in sys.modules if is_tqdm(name)]:
		del sys.modules[name]

	sys.modules.update(saved)


@pytest.fixture
def fallback_module(block_imports):
	block_imports("tqdm")

	with warnings.catch_warnings():
		warnings.simplefilter("ignore")

		return _load_progress_module()


@pytest.fixture
def fallback_tqdm(fallback_module):
	return fallback_module.tqdm


@pytest.fixture
def quiet_fallback_tqdm(fallback_tqdm):
	"""The fallback class, with its one-time warning already used up."""
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		fallback_tqdm()

	return fallback_tqdm


class TestFallbackSelection:
	def test_a_fresh_class_is_defined_when_tqdm_is_missing(self, fallback_module):
		assert fallback_module.tqdm.__module__ == "via_ludus_progress_under_test"
		assert not hasattr(fallback_module.tqdm, "auto")

	def test_an_installation_without_tqdm_auto_is_not_hidden(self, tmp_path, monkeypatch, isolated_tqdm_modules):
		# Only a missing top-level "tqdm" selects the fallback. A tqdm that is
		# importable but lacks its "auto" module is a broken installation.
		package = tmp_path / "tqdm"
		package.mkdir()
		(package / "__init__.py").write_text("")
		monkeypatch.syspath_prepend(str(tmp_path))

		with pytest.raises(ModuleNotFoundError) as excinfo:
			_load_progress_module()

		assert excinfo.value.name == "tqdm.auto"

	def test_a_missing_dependency_inside_tqdm_is_not_hidden(self, tmp_path, monkeypatch, isolated_tqdm_modules):
		# tqdm itself is importable but one of its own dependencies is not.
		# That is a broken installation, not a missing optional package.
		package = tmp_path / "tqdm"
		package.mkdir()
		(package / "__init__.py").write_text("")
		(package / "auto.py").write_text("import via_ludus_missing_tqdm_dependency\n")
		monkeypatch.syspath_prepend(str(tmp_path))

		with pytest.raises(ModuleNotFoundError) as excinfo:
			_load_progress_module()

		assert excinfo.value.name == "via_ludus_missing_tqdm_dependency"

	def test_the_real_tqdm_is_used_when_it_is_installed(self):
		tqdm_auto = pytest.importorskip("tqdm.auto")

		assert _load_progress_module().tqdm is tqdm_auto.tqdm

	def test_the_package_exposes_the_same_class(self):
		import via_ludus.utils as utils

		assert utils.tqdm is progress_module.tqdm


class TestFallbackWarning:
	def test_warns_on_first_use(self, fallback_tqdm):
		with pytest.warns(RuntimeWarning, match="tqdm is not installed"):
			fallback_tqdm()

	def test_warning_explains_how_to_install_tqdm(self, fallback_tqdm):
		with pytest.warns(RuntimeWarning) as caught:
			fallback_tqdm()

		message = str(caught[0].message)

		assert "Progress bars are disabled" in message
		assert 'pip install "via-ludus[progress]"' in message

	def test_warns_only_once(self, fallback_tqdm):
		with warnings.catch_warnings(record=True) as caught:
			warnings.simplefilter("always")

			fallback_tqdm()
			fallback_tqdm(range(3))
			fallback_tqdm(total=5)

		assert len(caught) == 1

	def test_no_warning_when_the_module_is_imported(self, block_imports):
		block_imports("tqdm")

		with warnings.catch_warnings():
			warnings.simplefilter("error")
			_load_progress_module()

	def test_the_warning_points_at_the_calling_code(self, fallback_tqdm):
		with pytest.warns(RuntimeWarning) as caught:
			fallback_tqdm()

		assert caught[0].filename == __file__

	def test_each_fresh_module_warns_again(self, block_imports):
		block_imports("tqdm")

		for _ in range(2):
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				module = _load_progress_module()

			with pytest.warns(RuntimeWarning):
				module.tqdm()


class TestFallbackIteration:
	def test_yields_every_item_unchanged(self, quiet_fallback_tqdm):
		assert list(quiet_fallback_tqdm(range(4))) == [0, 1, 2, 3]
		assert list(quiet_fallback_tqdm(["a", "b"])) == ["a", "b"]

	def test_accepts_any_iterable(self, quiet_fallback_tqdm):
		assert list(quiet_fallback_tqdm(item * 2 for item in range(3))) == [0, 2, 4]
		assert list(quiet_fallback_tqdm({"x": 1, "y": 2})) == ["x", "y"]

	def test_counts_the_items_as_they_are_consumed(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(range(5))
		iterator = iter(bar)

		next(iterator)
		next(iterator)

		assert bar.n == 2

		list(iterator)

		assert bar.n == 5

	def test_items_are_pulled_lazily(self, quiet_fallback_tqdm):
		pulled = []

		def source():
			for item in range(3):
				pulled.append(item)
				yield item

		iterator = iter(quiet_fallback_tqdm(source()))

		assert pulled == []

		next(iterator)

		assert pulled == [0]

	def test_without_an_iterable_nothing_is_yielded(self, quiet_fallback_tqdm):
		assert list(quiet_fallback_tqdm()) == []
		assert list(quiet_fallback_tqdm(total=10)) == []

	def test_an_empty_iterable_yields_nothing(self, quiet_fallback_tqdm):
		assert list(quiet_fallback_tqdm([])) == []

	def test_errors_from_the_iterable_propagate(self, quiet_fallback_tqdm):
		def failing():
			yield 1
			raise RuntimeError("source failed")

		with pytest.raises(RuntimeError, match="source failed"):
			list(quiet_fallback_tqdm(failing()))


class TestFallbackProgress:
	def test_initial_state(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(range(3), total=3)

		assert bar.n == 0
		assert bar.total == 3
		assert bar.iterable is not None

	def test_total_defaults_to_none(self, quiet_fallback_tqdm):
		assert quiet_fallback_tqdm().total is None

	def test_update_defaults_to_one(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(total=10)

		bar.update()
		bar.update()

		assert bar.n == 2

	def test_update_with_an_amount(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(total=10)

		bar.update(3)
		bar.update(4)

		assert bar.n == 7

	def test_accepts_the_usual_tqdm_arguments(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(
			range(3),
			"description",
			total=3,
			desc="Matchup",
			unit="game",
			leave=False,
			ncols=80,
		)

		assert list(bar) == [0, 1, 2]

	@pytest.mark.parametrize(
		"method, arguments, keyword_arguments",
		[
			("set_postfix", (), {"red": "a", "blue": "b"}),
			("set_postfix", ({"red": "a"},), {}),
			("set_postfix_str", ("text",), {}),
			("set_description", ("text",), {"refresh": False}),
			("refresh", (), {}),
			("close", (), {}),
		],
	)
	def test_display_methods_do_nothing(self, quiet_fallback_tqdm, method, arguments, keyword_arguments):
		bar = quiet_fallback_tqdm(total=3)

		assert getattr(bar, method)(*arguments, **keyword_arguments) is None
		assert bar.n == 0

	def test_context_manager_returns_the_bar(self, quiet_fallback_tqdm):
		with quiet_fallback_tqdm(total=2) as bar:
			bar.update(2)

		assert bar.n == 2

	def test_context_manager_returns_the_same_object(self, quiet_fallback_tqdm):
		bar = quiet_fallback_tqdm(total=2)

		with bar as entered:
			pass

		assert entered is bar

	def test_context_manager_does_not_swallow_exceptions(self, quiet_fallback_tqdm):
		with pytest.raises(ValueError, match="bad"):
			with quiet_fallback_tqdm(total=2):
				raise ValueError("bad")

	def test_context_manager_closes_the_bar(self, quiet_fallback_tqdm):
		closed = []

		class RecordingBar(quiet_fallback_tqdm):
			def close(self):
				closed.append(True)

		with RecordingBar(total=1):
			assert closed == []

		assert closed == [True]

	def test_context_manager_closes_the_bar_on_errors(self, quiet_fallback_tqdm):
		closed = []

		class RecordingBar(quiet_fallback_tqdm):
			def close(self):
				closed.append(True)

		with pytest.raises(RuntimeError):
			with RecordingBar(total=1):
				raise RuntimeError("boom")

		assert closed == [True]

	def test_tournament_code_can_use_the_fallback_like_a_real_bar(self, quiet_fallback_tqdm):
		with quiet_fallback_tqdm(total=3, desc="Round-Robin Tournament", unit="game") as bar:
			for _ in range(3):
				bar.set_postfix(red="a", blue="b")
				bar.update(1)

		assert bar.n == 3
