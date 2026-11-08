"""Scatter plots of player age and age difference from opponents."""

from math import isfinite

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter, MaxNLocator
import pandas as pd


_PLOT_COLUMNS = (
    "player_name", "player_age", "age_difference", "result", "included_in_plot"
)
_RESULT_STYLES = (("W", "Won", "#36C4E5"), ("L", "Lost", "#95349A"))


def plot_age_difference(matches: pd.DataFrame, *, ax: Axes | None = None) -> Axes:
    """Plot one player's eligible career matches and return a Matplotlib Axes.

    The x coordinate is player age; y is player age minus opponent age.
    Only rows with a true ``included_in_plot`` flag are drawn. The input
    is unchanged. A new figure is created when ``ax`` is omitted.
    """
    plotted, player = _plot_data(matches)
    _validate_axes(ax)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11}):
        if ax is None:
            _, ax = plt.subplots(figsize=(11, 7), facecolor="white", layout="constrained")
        _draw_matches(ax, plotted)
        _style_axes(ax)
        _label_axes(ax, player)
        _set_plot_limits(ax, plotted)
        ax.legend(loc="upper left", bbox_to_anchor=(0, -0.045), ncol=2, frameon=False)
    return ax


def _plot_data(matches):
    """Select eligible rows and validate the values needed for plotting."""
    _require_plot_columns(matches)
    flags = matches["included_in_plot"]
    if not pd.api.types.is_bool_dtype(flags) or flags.isna().any():
        raise ValueError("included_in_plot must contain boolean values without missing flags.")
    plotted = matches.loc[flags, list(_PLOT_COLUMNS)].copy()
    _validate_points(plotted)
    return plotted, _player_name(plotted)


def _require_plot_columns(matches):
    """Require a data frame with distinct columns and the plotting fields."""
    if not isinstance(matches, pd.DataFrame):
        raise TypeError("matches must be a pandas DataFrame returned by get_career_data().")
    if not matches.columns.is_unique:
        raise ValueError("matches must have unique column names.")
    missing = set(_PLOT_COLUMNS).difference(matches.columns)
    if missing:
        raise ValueError("Missing plotting columns: " + ", ".join(sorted(missing)))


def _validate_points(plotted):
    """Require at least one eligible match with a valid result and coordinates."""
    if plotted.empty:
        raise ValueError("No matches are eligible for plotting.")
    if not plotted["result"].isin(["W", "L"]).all():
        raise ValueError("Eligible matches must have result 'W' or 'L'.")
    _validate_coordinates(plotted[["player_age", "age_difference"]])


def _validate_coordinates(coordinates):
    """Reject missing, nonnumeric, infinite, or negative player ages."""
    if any(dtype.kind not in "iuf" for dtype in coordinates.dtypes):
        raise ValueError("player_age and age_difference must have real numeric dtypes.")
    if coordinates.isna().any().any() or not all(map(isfinite, coordinates.to_numpy().flat)):
        raise ValueError("Eligible player_age and age_difference values must be finite.")
    if (coordinates["player_age"] < 0).any():
        raise ValueError("Eligible player_age values must be nonnegative.")


def _player_name(plotted):
    """Require one nonempty player name among the eligible matches."""
    names = plotted["player_name"]
    if not names.map(lambda name: isinstance(name, str) and bool(name.strip())).all():
        raise ValueError("Eligible matches must have a nonempty player_name.")
    if names.nunique() != 1:
        raise ValueError("Plot one player at a time; player_name contains multiple names.")
    return names.iloc[0]


def _validate_axes(ax):
    """Accept an ordinary two-dimensional Matplotlib axes or None."""
    if ax is not None and not isinstance(ax, Axes):
        raise TypeError("ax must be a Matplotlib Axes or None.")
    if ax is not None and ax.name != "rectilinear":
        raise ValueError("ax must use ordinary two-dimensional Cartesian coordinates.")


def _draw_matches(ax, plotted):
    """Draw the same-age line, then wins followed by losses."""
    ax.axhline(0, color="#888888", linewidth=1.05, zorder=1)
    for result, label, color in _RESULT_STYLES:
        group = plotted.loc[plotted["result"].eq(result)]
        ax.scatter(
            group["player_age"], group["age_difference"], label=label,
            color=color, s=17, alpha=0.86, marker="o", edgecolors="none", zorder=3,
        )


def _style_axes(ax):
    """Use a white background, light grid, and unobtrusive axes."""
    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    ax.set_xscale("linear")
    ax.set_yscale("linear")
    ax.grid(True, color="#E7E7E7", linewidth=0.8)
    ax.tick_params(axis="both", which="both", length=0, labelsize=11, colors="#444444")
    for spine in ax.spines.values():
        spine.set_visible(False)


def _label_axes(ax, player):
    """Put age labels above the plot and show signed age differences."""
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Player age (years)", loc="left", labelpad=10)
    ax.set_ylabel("Player age − opponent age (years)", labelpad=12)
    ax.set_title(f"{player}: career matches", loc="left", fontsize=17, weight="bold", pad=58)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=12, integer=True, min_n_ticks=2))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_formatter(FuncFormatter(_age_difference_tick))


def _set_plot_limits(ax, plotted):
    """Pad the observed coordinates while keeping the same-age line visible."""
    ages, differences = plotted["player_age"], plotted["age_difference"]
    xmin, xmax = ages.min(), ages.max()
    ymin, ymax = min(0, differences.min()), max(0, differences.max())
    xpad, ypad = max((xmax - xmin) * 0.04, 0.5), max((ymax - ymin) * 0.05, 1.0)
    ax.set_xlim(max(0, xmin - xpad), xmax + xpad)
    ax.set_ylim(ymin - ypad, ymax + ypad)


def _age_difference_tick(value, position):
    """Label zero as the same age and include signs on other values."""
    return "Same age" if value == 0 else f"{value:+g}"
