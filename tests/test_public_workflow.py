"""Exercise retrieval and plotting together using local HTTP responses."""

import json

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from tennisage import get_career_data, plot_age_difference
from tennisage._parsing import _parse_career_js


_ROOT = "https://www.tennisabstract.com"
_INDEX = f"{_ROOT}/mwplayerlist.js"
_WOMAN = f"{_ROOT}/cgi-bin/wplayer-classic.cgi?p=SerenaWilliams&f=ACareerqq"
_MAN = f"{_ROOT}/cgi-bin/player-classic.cgi?p=RafaelNadal&f=ACareerqq"
_CURRENT = f"{_ROOT}/jsmatches/SerenaWilliams.js"
_ARCHIVE = f"{_ROOT}/jsmatches/SerenaWilliamsCareer.js"


def _profile_source(name, birth_date, rows, archive=False):
    """Construct profile metadata and a current match table."""
    return (
        f"var fullname={json.dumps(name)};\n"
        f"var dob={birth_date};\n"
        f"var careerjs={int(archive)};\n"
        f"var matchmx={json.dumps(rows)};\n"
    )


@pytest.fixture
def career_responses(mock_http, female_js, male_js):
    """Provide one archive-based career and one career embedded in its profile."""
    responses, calls = mock_http
    responses[_INDEX] = 'var playerlist=["(W) Serena Williams", "(M) Rafael Nadal"];'
    responses[_WOMAN] = '<html><script src="/jsmatches/SerenaWilliams.js"></script></html>'
    responses[_CURRENT] = _profile_source("Serena Williams", "19810926", [], archive=True)
    responses[_ARCHIVE] = female_js
    responses[_MAN] = _profile_source("Rafael Nadal", "19860603", _parse_career_js(male_js))
    return responses, calls


@pytest.fixture(autouse=True)
def close_figures():
    """Close every figure created by a public-workflow test."""
    yield
    plt.close("all")


@pytest.mark.parametrize("name, wins, age, gap", [
    ("serena williams", 0, 5147 / 365.25, -1711 / 365.25),
    ("RafaelNadal", 1, 5578 / 365.25, 5578 / 365.25 - 22.264202601),
])
def test_retrieved_frame_can_be_plotted_directly(career_responses, name, wins, age, gap):
    frame = get_career_data(name)
    ax = plot_age_difference(frame)
    won, lost = ax.collections
    assert len(won.get_offsets()) == wins
    assert len(lost.get_offsets()) == 3 - wins
    assert lost.get_offsets()[0].tolist() == pytest.approx([age, gap])
    assert ax.get_title(loc="left") == f"{frame['player_name'].iloc[0]}: career matches"


@pytest.mark.parametrize("name, url, old, new, reason", [
    ("SerenaWilliams", _ARCHIVE, '"6-1 6-1"', '"W/O"', "walkover_or_default"),
    ("Rafael Nadal", _MAN, '"22.264202601"', '""', "missing_opponent_age"),
])
def test_exclusion_flags_survive_the_public_workflow(career_responses, name, url, old, new, reason):
    responses, calls = career_responses
    responses[url] = responses[url].replace(old, new, 1)
    frame = get_career_data(name)
    ax = plot_age_difference(frame)
    assert len(frame) == 3
    assert frame["included_in_plot"].sum() == 2
    assert frame.loc[0, "exclusion_reason"] == reason
    assert sum(len(group.get_offsets()) for group in ax.collections) == 2


def test_successive_players_and_unknown_name(career_responses):
    responses, calls = career_responses
    serena = get_career_data("Serena Williams")
    rafa = get_career_data("rafael nadal")
    serena_ax, rafa_ax = plot_age_difference(serena), plot_age_difference(rafa)
    requests_before = len(calls)
    with pytest.raises(ValueError, match="No player named 'GastonSanchez'"):
        get_career_data("GastonSanchez")
    assert serena_ax.figure is not rafa_ax.figure
    assert len(calls) == requests_before
    assert sum(url == _INDEX for url, _, _ in calls) == 1
