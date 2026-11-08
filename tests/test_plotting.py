"""Check scatter-plot behavior using local data and a noninteractive backend."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
import pandas as pd
import pytest

import tennisage
from tennisage import plot_age_difference
from tennisage._cleaning import _clean_mens_records, _clean_womens_records
from tennisage._parsing import _parse_career_js


@pytest.fixture(autouse=True)
def close_figures():
    """Release figures even when a plotting assertion fails."""
    yield
    plt.close("all")


@pytest.fixture
def matches():
    """Include both results, both age-gap signs, and a missing excluded age."""
    return pd.DataFrame({
        "player_name": ["Sample Player"] * 4,
        "player_age": [18.0, 27.5, 40.0, 41.0],
        "age_difference": [-4.5, 0.0, 12.25, float("nan")],
        "result": ["W", "L", "W", "L"],
        "included_in_plot": [True, True, True, False],
    }, index=[7, 3, 10, 22])


def test_public_functions_are_exported():
    assert tennisage.__all__ == ["get_career_data", "plot_age_difference"]
    assert callable(tennisage.get_career_data)
    assert callable(tennisage.plot_age_difference)


def test_coordinates_colors_and_input_preservation(matches):
    original = matches.copy(deep=True)
    ax = plot_age_difference(matches)
    assert isinstance(ax, Axes)
    won, lost = ax.collections
    assert won.get_offsets().tolist() == [[18.0, -4.5], [40.0, 12.25]]
    assert lost.get_offsets().tolist() == [[27.5, 0.0]]
    assert won.get_facecolors()[0] == pytest.approx(to_rgba("#36C4E5", alpha=0.86))
    assert lost.get_facecolors()[0] == pytest.approx(to_rgba("#95349A", alpha=0.86))
    assert [text.get_text() for text in ax.get_legend().get_texts()] == ["Won", "Lost"]
    pd.testing.assert_frame_equal(matches, original)


def test_labels_same_age_line_and_no_match_annotations(matches):
    ax = plot_age_difference(matches)
    assert ax.get_title(loc="left") == "Sample Player: career matches"
    assert ax.get_xlabel() == "Player age (years)"
    assert ax.get_ylabel() == "Player age − opponent age (years)"
    assert ax.xaxis.get_label_position() == "top"
    assert list(ax.lines[0].get_ydata()) == [0, 0]
    assert len(ax.texts) == 0
    formatter = ax.yaxis.get_major_formatter()
    assert [formatter(value) for value in [-10, 0, 10]] == ["-10", "Same age", "+10"]


def test_limits_include_full_career_and_zero(matches):
    matches.loc[7, ["player_age", "age_difference"]] = [12.0, -30.0]
    matches.loc[10, ["player_age", "age_difference"]] = [46.0, 32.0]
    ax = plot_age_difference(matches)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    assert 0 <= xmin < 12 < 46 < xmax
    assert ymin < -30 < 0 < 32 < ymax


@pytest.mark.parametrize("gap", [-7.0, 0.0, 9.0])
@pytest.mark.parametrize("result", ["W", "L"])
def test_single_match_and_one_result(matches, gap, result):
    single = matches.iloc[[0]].copy()
    single["age_difference"], single["result"] = gap, result
    ax = plot_age_difference(single)
    counts = [len(group.get_offsets()) for group in ax.collections]
    assert counts == ([1, 0] if result == "W" else [0, 1])
    assert ax.get_xlim()[0] < 18 < ax.get_xlim()[1]
    assert ax.get_ylim()[0] < min(0, gap) <= max(0, gap) < ax.get_ylim()[1]


def test_existing_axes_is_reused(matches):
    fig, ax = plt.subplots()
    line, = ax.plot([10, 12], [1, 2], label="Reference")
    figures_before = plt.get_fignums()
    returned = plot_age_difference(matches, ax=ax)
    assert returned is ax
    assert returned.figure is fig
    assert line in ax.lines
    assert plt.get_fignums() == figures_before


def test_no_implicit_display_or_global_style_change(matches, monkeypatch):
    def forbid_show(*args, **kwargs):
        pytest.fail("plot_age_difference must not call show().")
    monkeypatch.setattr(plt, "show", forbid_show)
    with plt.rc_context({"font.size": 9, "font.family": "serif"}):
        before = plt.rcParams.copy()
        plot_age_difference(matches)
        assert dict(plt.rcParams) == dict(before)


@pytest.mark.parametrize("extension, signature", [("png", b"\x89PNG\r\n\x1a\n"), ("pdf", b"%PDF")])
def test_figure_can_be_saved(matches, tmp_path, extension, signature):
    ax = plot_age_difference(matches)
    path = tmp_path / f"career.{extension}"
    ax.figure.savefig(path, bbox_inches="tight")
    assert path.read_bytes().startswith(signature)
    assert path.stat().st_size > 1000


@pytest.mark.parametrize("tour", ["women", "men"])
def test_cleaned_fixture_plots_without_network(female_js, male_js, tour):
    if tour == "women":
        frame = _clean_womens_records(_parse_career_js(female_js), "Serena Williams", "19810926")
    else:
        frame = _clean_mens_records(_parse_career_js(male_js), "Rafael Nadal", "19860603")
    ax = plot_age_difference(frame)
    assert sum(len(group.get_offsets()) for group in ax.collections) == 3
    for result, group in zip(["W", "L"], ax.collections):
        expected = frame.loc[frame["result"].eq(result), ["player_age", "age_difference"]]
        assert group.get_offsets().tolist() == expected.to_numpy().tolist()


@pytest.mark.parametrize("value", [None, [], {}, "Serena Williams"])
def test_reject_non_dataframe(value):
    with pytest.raises(TypeError, match="pandas DataFrame"):
        plot_age_difference(value)


@pytest.mark.parametrize("column", ["player_name", "player_age", "age_difference", "result", "included_in_plot"])
def test_reject_missing_columns(matches, column):
    with pytest.raises(ValueError, match=column):
        plot_age_difference(matches.drop(columns=column))


def test_reject_duplicate_columns(matches):
    frame = pd.concat([matches, matches[["result"]]], axis=1)
    with pytest.raises(ValueError, match="unique column"):
        plot_age_difference(frame)


@pytest.mark.parametrize("flags", [[1, 1, 1, 0], ["True"] * 4, [True, None, True, False]])
def test_reject_invalid_inclusion_flags(matches, flags):
    matches["included_in_plot"] = flags
    with pytest.raises(ValueError, match="boolean"):
        plot_age_difference(matches)


def test_nullable_boolean_and_numeric_columns(matches):
    matches["included_in_plot"] = matches["included_in_plot"].astype("boolean")
    matches["player_age"] = matches["player_age"].astype("Float64")
    matches["age_difference"] = matches["age_difference"].astype("Float64")
    ax = plot_age_difference(matches)
    assert sum(len(group.get_offsets()) for group in ax.collections) == 3


@pytest.mark.parametrize("empty_frame", [True, False])
def test_reject_no_eligible_matches(matches, empty_frame):
    matches["included_in_plot"] = False
    frame = matches.iloc[:0] if empty_frame else matches
    with pytest.raises(ValueError, match="No matches are eligible"):
        plot_age_difference(frame)


@pytest.mark.parametrize("column", ["player_age", "age_difference"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_reject_nonfinite_eligible_coordinates(matches, column, value):
    matches.loc[7, column] = value
    with pytest.raises(ValueError, match="finite"):
        plot_age_difference(matches)


@pytest.mark.parametrize("column", ["player_age", "age_difference"])
@pytest.mark.parametrize("value", ["18.0", True, 18 + 1j])
def test_reject_nonreal_coordinate_dtypes(matches, column, value):
    matches[column] = value
    with pytest.raises(ValueError, match="real numeric"):
        plot_age_difference(matches)


def test_reject_negative_player_age(matches):
    matches.loc[7, "player_age"] = -1.0
    with pytest.raises(ValueError, match="nonnegative"):
        plot_age_difference(matches)


@pytest.mark.parametrize("result", [None, "win", "", "D"])
def test_reject_invalid_result(matches, result):
    matches.loc[7, "result"] = result
    with pytest.raises(ValueError, match="result 'W' or 'L'"):
        plot_age_difference(matches)


@pytest.mark.parametrize("name", [None, "", "   ", 42])
def test_reject_invalid_player_name(matches, name):
    matches.loc[7, "player_name"] = name
    with pytest.raises(ValueError, match="nonempty player_name"):
        plot_age_difference(matches)


def test_reject_multiple_players(matches):
    matches.loc[7, "player_name"] = "Another Player"
    with pytest.raises(ValueError, match="one player at a time"):
        plot_age_difference(matches)


@pytest.mark.parametrize("ax", ["axes", [], 1])
def test_reject_invalid_axes_type(matches, ax):
    with pytest.raises(TypeError, match="Matplotlib Axes"):
        plot_age_difference(matches, ax=ax)


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_reject_noncartesian_axes(matches, projection):
    ax = plt.figure().add_subplot(projection=projection)
    with pytest.raises(ValueError, match="Cartesian"):
        plot_age_difference(matches, ax=ax)


def test_invalid_input_does_not_create_figure(matches):
    figures_before = plt.get_fignums()
    with pytest.raises(ValueError):
        plot_age_difference(matches.drop(columns="player_age"))
    assert plt.get_fignums() == figures_before
