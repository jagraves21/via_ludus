"""Optional dependencies (matplotlib, pandas, tqdm) must stay optional.

Every scenario runs in a fresh Python subprocess. In that process an import
hook makes ``import <name>`` fail with a real ``ModuleNotFoundError`` for the
blocked libraries (and all of their submodules), exactly as if they were not
installed. The hook is checked by the tests themselves, so a scenario can
never pass merely because blocking silently did nothing.

Scenarios that need a library to be genuinely installed are skipped when it
is not; the scenarios in which libraries are missing always run.
"""

import functools
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

import via_ludus
from via_ludus.utils import OptionalDependencyError, requires_extra


SOURCE_ROOT = Path(via_ludus.__file__).resolve().parents[1]

PRELUDE = """
import importlib.abc
import json
import sys

blocked = [name for name in sys.argv[1].split(",") if name]


class Blocker(importlib.abc.MetaPathFinder):
	def find_spec(self, fullname, path=None, target=None):
		for name in blocked:
			if fullname == name or fullname.startswith(name + "."):
				raise ModuleNotFoundError(
					f"No module named {fullname!r}",
					name=fullname,
				)

		return None


for loaded in list(sys.modules):
	if any(loaded == name or loaded.startswith(name + ".") for name in blocked):
		del sys.modules[loaded]

sys.meta_path.insert(0, Blocker())

report = {}
"""

FEATURES_SCRIPT = PRELUDE + """
import via_ludus
from via_ludus.board import Cell, PlayerColor, SearchBoard, UnionFindBoard
from via_ludus.tournament import TournamentResults
from via_ludus.utils import OptionalDependencyError
from via_ludus.visualizations import plot_board

OPTIONAL = ("matplotlib", "pandas")

report["loaded_after_import"] = sorted(
	name for name in OPTIONAL if name in sys.modules
)

report["blocked_imports"] = {}
for name in blocked:
	try:
		__import__(name)
	except ModuleNotFoundError as exc:
		report["blocked_imports"][name] = exc.name


def attempt(function):
	try:
		value = function()
	except OptionalDependencyError as exc:
		return {
			"available": False,
			"message": str(exc),
			"cause": type(exc.__cause__).__name__,
			"is_import_error": isinstance(exc, ImportError),
		}

	return {"available": True, "value": value}


# Core functionality: no optional dependency involved.
core = {}

for board_type in (SearchBoard, UnionFindBoard):
	board = board_type(size=3)
	board.set(1, 1, Cell.RED)
	core[board_type.__name__] = board.winner.name

results = TournamentResults(["a", "b"])
results.add_matchup_result("a", "b", PlayerColor.RED, 5, True)
results.add_matchup_result("b", "a", PlayerColor.BLUE, 7, True)

core["total_games"] = results.total_games
core["summary_rows"] = len(results.summary())
core["head_to_head_rows"] = len(results.head_to_head_summary())
core["win_matrix_type"] = type(results.win_matrix()).__name__
report["core"] = core


def check_summary_df():
	frame = results.summary_df()
	return [type(frame).__name__, len(frame)]


def check_win_matrix_df():
	frame = results.win_matrix_df()
	return [type(frame).__name__, list(frame.shape)]


def check_plot_board():
	_, fig, ax = plot_board(
		UnionFindBoard(size=5),
		show=False,
		close=True,
		return_fig=True,
	)
	return [type(fig).__name__, len(ax.patches)]


def check_board_plot_method():
	UnionFindBoard(size=5).plot(show=False, close=True)
	return "plotted"


def check_plot_win_matrix():
	_, fig, _ = results.plot_win_matrix(
		show=False,
		close=True,
		return_fig=True,
	)
	return type(fig).__name__


report["pandas"] = {
	"summary_df": attempt(check_summary_df),
	"win_matrix_df": attempt(check_win_matrix_df),
}
report["matplotlib"] = {
	"plot_board": attempt(check_plot_board),
	"board_plot": attempt(check_board_plot_method),
	"plot_win_matrix": attempt(check_plot_win_matrix),
}

print("RESULT=" + json.dumps(report))
"""

TQDM_SCRIPT = PRELUDE + """
import warnings

with warnings.catch_warnings(record=True) as caught:
	warnings.simplefilter("always")

	import via_ludus
	from via_ludus.utils import tqdm

report["warnings_on_import"] = [
	str(warning.message)
	for warning in caught
	if issubclass(warning.category, RuntimeWarning)
]

report["blocked_imports"] = {}
for name in blocked:
	try:
		__import__(name)
	except ModuleNotFoundError as exc:
		report["blocked_imports"][name] = exc.name

report["is_fallback"] = tqdm.__module__.startswith("via_ludus")

with warnings.catch_warnings(record=True) as caught:
	warnings.simplefilter("always")

	report["items"] = list(tqdm(range(3)))
	report["items_again"] = list(tqdm(range(2)))

	with tqdm(total=4) as bar:
		bar.update(3)
		report["bar_n"] = bar.n

	if report["is_fallback"]:
		report["empty"] = list(tqdm())

report["warnings_on_use"] = [
	str(warning.message)
	for warning in caught
	if issubclass(warning.category, RuntimeWarning)
]

print("RESULT=" + json.dumps(report))
"""


def _is_installed(name):
	return importlib.util.find_spec(name) is not None


@functools.lru_cache(maxsize=None)
def _config_dir():
	return tempfile.mkdtemp(prefix="via-ludus-mpl-")


@functools.lru_cache(maxsize=None)
def _run_in_subprocess(script, blocked):
	env = dict(os.environ)
	env["PYTHONPATH"] = os.pathsep.join(
		part for part in (str(SOURCE_ROOT), env.get("PYTHONPATH")) if part
	)
	env["MPLBACKEND"] = "Agg"
	env["MPLCONFIGDIR"] = _config_dir()

	completed = subprocess.run(
		[sys.executable, "-c", script, ",".join(blocked)],
		capture_output=True,
		text=True,
		env=env,
		timeout=180,
	)

	assert completed.returncode == 0, (
		f"subprocess failed\n--- stdout ---\n{completed.stdout}"
		f"\n--- stderr ---\n{completed.stderr}"
	)

	lines = [
		line
		for line in completed.stdout.splitlines()
		if line.startswith("RESULT=")
	]

	assert len(lines) == 1, completed.stdout

	return json.loads(lines[0][len("RESULT="):])


@dataclass(frozen=True)
class Scenario:
	name: str
	blocked: frozenset
	has_matplotlib: bool
	has_pandas: bool


SCENARIOS = {
	"both-installed": frozenset(),
	"matplotlib-only": frozenset({"pandas"}),
	"pandas-only": frozenset({"matplotlib"}),
	"neither-installed": frozenset({"matplotlib", "pandas"}),
}


@pytest.fixture(params=list(SCENARIOS))
def scenario(request):
	blocked = SCENARIOS[request.param]
	available = {"matplotlib", "pandas"} - blocked

	for name in sorted(available):
		if not _is_installed(name):
			pytest.skip(
				f"scenario {request.param!r} needs {name} to be installed"
			)

	return Scenario(
		name=request.param,
		blocked=blocked,
		has_matplotlib="matplotlib" in available,
		has_pandas="pandas" in available,
	)


@pytest.fixture
def report(scenario):
	return _run_in_subprocess(FEATURES_SCRIPT, tuple(sorted(scenario.blocked)))


def _assert_missing_dependency_error(outcome, module_name, extra_name, function_name):
	assert outcome["available"] is False
	assert outcome["is_import_error"] is True
	assert outcome["cause"] == "ModuleNotFoundError"
	assert f"requires {module_name!r}" in outcome["message"]
	assert f'pip install -e ".[{extra_name}]"' in outcome["message"]
	assert function_name in outcome["message"]


class TestMatplotlibAndPandasScenarios:
	def test_blocked_libraries_really_fail_to_import(self, scenario, report):
		assert report["blocked_imports"] == {
			name: name for name in scenario.blocked
		}

	def test_importing_via_ludus_does_not_load_optional_libraries(self, report):
		assert report["loaded_after_import"] == []

	def test_core_functionality_works(self, report):
		assert report["core"] == {
			"SearchBoard": "RED",
			"UnionFindBoard": "RED",
			"total_games": 2,
			"summary_rows": 2,
			"head_to_head_rows": 2,
			"win_matrix_type": "dict",
		}

	def test_pandas_features(self, scenario, report):
		summary = report["pandas"]["summary_df"]
		win_matrix = report["pandas"]["win_matrix_df"]

		if scenario.has_pandas:
			assert summary == {"available": True, "value": ["DataFrame", 2]}
			assert win_matrix == {"available": True, "value": ["DataFrame", [2, 2]]}
		else:
			_assert_missing_dependency_error(
				summary, "pandas", "dataframe", "TournamentResults.summary_df",
			)
			_assert_missing_dependency_error(
				win_matrix, "pandas", "dataframe", "TournamentResults.win_matrix_df",
			)

	def test_matplotlib_features(self, scenario, report):
		plotted = report["matplotlib"]

		if scenario.has_matplotlib:
			assert plotted["plot_board"] == {"available": True, "value": ["Figure", 25]}
			assert plotted["board_plot"] == {"available": True, "value": "plotted"}
			assert plotted["plot_win_matrix"] == {"available": True, "value": "Figure"}
		else:
			for name in ("plot_board", "board_plot", "plot_win_matrix"):
				assert plotted[name]["available"] is False
				assert plotted[name]["is_import_error"] is True
				assert plotted[name]["cause"] == "ModuleNotFoundError"
				assert "'matplotlib" in plotted[name]["message"]
				assert 'pip install -e ".[visualization]"' in plotted[name]["message"]

	def test_each_library_works_without_the_other(self, scenario, report):
		# A working feature must not depend on the other optional library.
		if scenario.has_pandas and not scenario.has_matplotlib:
			assert report["pandas"]["summary_df"]["available"] is True

		if scenario.has_matplotlib and not scenario.has_pandas:
			assert report["matplotlib"]["plot_board"]["available"] is True

		# A missing library only disables its own features.
		assert (report["pandas"]["summary_df"]["available"]) is scenario.has_pandas
		assert (report["matplotlib"]["plot_board"]["available"]) is scenario.has_matplotlib


class TestTqdm:
	def test_tqdm_fallback_when_tqdm_is_missing(self):
		report = _run_in_subprocess(TQDM_SCRIPT, ("tqdm",))

		assert report["blocked_imports"] == {"tqdm": "tqdm"}
		assert report["is_fallback"] is True
		assert report["items"] == [0, 1, 2]
		assert report["items_again"] == [0, 1]
		assert report["bar_n"] == 3
		assert report["empty"] == []

	def test_tqdm_fallback_warns_once_on_first_use_not_on_import(self):
		report = _run_in_subprocess(TQDM_SCRIPT, ("tqdm",))

		assert report["warnings_on_import"] == []
		assert len(report["warnings_on_use"]) == 1
		assert "tqdm is not installed" in report["warnings_on_use"][0]
		assert "via-ludus[progress]" in report["warnings_on_use"][0]

	@pytest.mark.skipif(not _is_installed("tqdm"), reason="tqdm is not installed")
	def test_real_tqdm_is_used_when_installed(self):
		report = _run_in_subprocess(TQDM_SCRIPT, ())

		assert report["is_fallback"] is False
		assert report["items"] == [0, 1, 2]
		assert report["warnings_on_use"] == []


class TestRequiresExtra:
	def test_optional_dependency_error_is_an_import_error(self):
		assert issubclass(OptionalDependencyError, ImportError)

	def test_requires_extra_calls_the_function_when_the_module_exists(self):
		@requires_extra("json", "example")
		def add(first, second=0):
			return first + second

		assert add(1, second=2) == 3

	def test_requires_extra_preserves_function_metadata(self):
		@requires_extra("json", "example")
		def documented():
			"""Docstring."""

		assert documented.__name__ == "documented"
		assert documented.__doc__ == "Docstring."

	def test_requires_extra_raises_a_helpful_error_for_a_missing_module(self):
		@requires_extra("via_ludus_missing_module", "example")
		def feature():
			raise AssertionError("must not be called")

		with pytest.raises(OptionalDependencyError) as excinfo:
			feature()

		message = str(excinfo.value)

		assert "requires 'via_ludus_missing_module'" in message
		assert "feature()" in message
		assert 'pip install -e ".[example]"' in message
		assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)

	def test_requires_extra_handles_a_missing_submodule_of_a_missing_package(self):
		@requires_extra("via_ludus_missing_package.sub", "example")
		def feature():
			raise AssertionError("must not be called")

		with pytest.raises(OptionalDependencyError, match="via_ludus_missing_package.sub"):
			feature()

	def test_requires_extra_does_not_hide_a_missing_inner_dependency(self, tmp_path, monkeypatch):
		# The requested module exists but fails to import one of its own
		# dependencies. That is a different problem and must not be reported as
		# the optional extra being missing.
		(tmp_path / "via_ludus_outer_module.py").write_text(
			"import via_ludus_inner_missing_module\n"
		)
		monkeypatch.syspath_prepend(str(tmp_path))
		monkeypatch.delitem(sys.modules, "via_ludus_outer_module", raising=False)

		@requires_extra("via_ludus_outer_module", "example")
		def feature():
			raise AssertionError("must not be called")

		with pytest.raises(ModuleNotFoundError) as excinfo:
			feature()

		assert not isinstance(excinfo.value, OptionalDependencyError)
		assert excinfo.value.name == "via_ludus_inner_missing_module"
