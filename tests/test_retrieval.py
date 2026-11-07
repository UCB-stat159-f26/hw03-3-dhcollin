"""Exercise the public career-data API with local HTTP responses."""

from copy import deepcopy
import json
from urllib.error import HTTPError, URLError

import pandas as pd
import pytest

from tennisage import get_career_data
from tennisage._parsing import _parse_career_js
from tennisage._players import _resolve_player

_ROOT = "https://www.tennisabstract.com"
_INDEX = f"{_ROOT}/mwplayerlist.js"
_WOMAN = f"{_ROOT}/cgi-bin/wplayer-classic.cgi?p=SerenaWilliams&f=ACareerqq"
_MAN = f"{_ROOT}/cgi-bin/player-classic.cgi?p=RafaelNadal&f=ACareerqq"
_CURRENT = f"{_ROOT}/jsmatches/SerenaWilliams.js"
_ARCHIVE = f"{_ROOT}/jsmatches/SerenaWilliamsCareer.js"
_PLAYERS = 'var playerlist=["(W) Serena Williams", "(M) Rafael Nadal", "(M) Roger Federer"];'


def _profile(name, birth_date, archive, rows):
    """Build a small profile using the site's metadata and table declarations."""
    return (
        f"var fullname = {json.dumps(name)};\n"
        f"var dob = {birth_date};\n"
        f"var careerjs = {int(archive)};\n"
        f"var matchmx = {json.dumps(rows)};\n"
    )


@pytest.fixture
def female_responses(mock_http, female_js):
    """Provide a legacy profile with an empty current table and three archive rows."""
    responses, calls = mock_http
    responses.update({
        _INDEX: _PLAYERS,
        _WOMAN: '<html><script src="/jsmatches/SerenaWilliams.js"></script></html>',
        _CURRENT: _profile("Serena Williams", "19810926", True, []),
        _ARCHIVE: female_js,
    })
    return responses, calls


@pytest.mark.parametrize("name", ["serena williams", "Serena Williams", "SerenaWilliams", "SERENAWILLIAMS", " Serena\t Williams ", "(W) Serena Williams"])
def test_flexible_names_retrieve_womens_career(female_responses, name):
    responses, calls = female_responses
    frame = get_career_data(name)
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 3
    assert frame["player_name"].eq("Serena Williams").all()
    assert frame.loc[0, "player_age"] == pytest.approx(5147 / 365.25)
    assert frame.loc[0, "age_difference"] == pytest.approx(-1711 / 365.25)
    assert frame["included_in_plot"].all()
    assert [url for url, _, _ in calls] == [_INDEX, _WOMAN, _CURRENT, _ARCHIVE]


@pytest.mark.parametrize("name", ["rafael nadal", "RafaelNadal", "RAFAEL NADAL"])
def test_inline_mens_reported_ages(mock_http, male_js, name):
    responses, calls = mock_http
    rows = _parse_career_js(male_js)
    responses.update({_INDEX: _PLAYERS, _MAN: _profile("Rafael Nadal", "19860603", False, rows)})
    frame = get_career_data(name)
    assert len(frame) == 3
    assert frame.loc[0, "opponent_age"] == pytest.approx(22.264202601, rel=0, abs=1e-12)
    assert frame["opponent_dob"].isna().all()
    assert frame["included_in_plot"].all()
    assert [url for url, _, _ in calls] == [_INDEX, _MAN]


def test_current_mens_birth_dates_and_missing_values(mock_http, male_js):
    responses, calls = mock_http
    rows = _parse_career_js(male_js)
    rows[0][16], rows[1][16], rows[2][16] = "19790101", "19800101", ""
    responses.update({_INDEX: _PLAYERS, _MAN: _profile("Rafael Nadal", "19860603", False, rows)})
    frame = get_career_data("Rafael Nadal")
    assert frame.loc[0, "opponent_dob"] == pd.Timestamp("1979-01-01")
    assert frame.loc[0, "opponent_age"] == pytest.approx(8288 / 365.25)
    assert frame.loc[:1, "included_in_plot"].all()
    assert not frame.loc[2, "included_in_plot"]
    assert frame.loc[2, "exclusion_reason"] == "missing_opponent_age"


def test_mixed_mens_age_formats(mock_http, male_js):
    responses, calls = mock_http
    rows = _parse_career_js(male_js)
    rows[0][16] = "19790101"
    responses.update({_INDEX: _PLAYERS, _MAN: _profile("Rafael Nadal", "19860603", False, rows)})
    frame = get_career_data("Rafael Nadal")
    assert frame.loc[0, "opponent_dob"] == pd.Timestamp("1979-01-01")
    assert pd.isna(frame.loc[1, "opponent_dob"])
    assert frame.loc[1, "opponent_age"] == pytest.approx(24.2902121834, rel=0, abs=1e-12)
    assert frame["included_in_plot"].all()


def test_other_indexed_player_uses_supplied_identity(mock_http, male_js):
    responses, calls = mock_http
    url = f"{_ROOT}/cgi-bin/player-classic.cgi?p=RogerFederer&f=ACareerqq"
    source = _profile("Roger Federer", "19810808", False, _parse_career_js(male_js))
    responses.update({_INDEX: _PLAYERS, url: source})
    frame = get_career_data("rogerfederer")
    assert frame["player_name"].eq("Roger Federer").all()
    assert frame["player_dob"].eq(pd.Timestamp("1981-08-08")).all()
    assert [request[0] for request in calls] == [_INDEX, url]


def test_current_record_replaces_archive_overlap(female_responses, female_js):
    responses, calls = female_responses
    current = deepcopy(_parse_career_js(female_js)[0])
    current[4], current[9] = "W", "6-0 6-0"
    responses[_CURRENT] = _profile("Serena Williams", "19810926", True, [current])
    frame = get_career_data("Serena Williams")
    assert len(frame) == 3
    assert frame.loc[0, "result"] == "W"
    assert frame.loc[0, "score"] == "6-0 6-0"
    assert frame["source_row"].tolist() == [3, 1, 2]


def test_current_matches_extend_the_archive(female_responses, female_js):
    responses, calls = female_responses
    current = deepcopy(_parse_career_js(female_js)[0])
    current[0] = "20220902"
    responses[_CURRENT] = _profile("Serena Williams", "19810926", True, [current])
    frame = get_career_data("Serena Williams")
    assert len(frame) == 4
    assert frame.iloc[-1]["tournament_date"] == pd.Timestamp("2022-09-02")
    assert frame.iloc[-1]["included_in_plot"]


def test_legacy_mens_split_files(mock_http, male_js):
    responses, calls = mock_http
    current_url = f"{_ROOT}/jsmatches/RafaelNadal.js"
    archive_url = f"{_ROOT}/jsmatches/RafaelNadalCareer.js"
    responses.update({_INDEX: _PLAYERS, _MAN: "<html></html>", archive_url: male_js})
    responses[current_url] = _profile("Rafael Nadal", "19860603", True, [])
    frame = get_career_data("Rafael Nadal")
    assert len(frame) == 3
    assert frame.loc[0, "opponent_age"] == pytest.approx(22.264202601, rel=0, abs=1e-12)
    assert [url for url, _, _ in calls] == [_INDEX, _MAN, current_url, archive_url]


def test_profile_identity_mismatch_is_rejected(female_responses):
    responses, calls = female_responses
    responses[_CURRENT] = _profile("Another Player", "19810926", True, [])
    with pytest.raises(ValueError, match="different player"):
        get_career_data("Serena Williams")
    assert _ARCHIVE not in [url for url, _, _ in calls]


def test_empty_career_has_a_meaningful_error(mock_http):
    responses, calls = mock_http
    responses.update({_INDEX: _PLAYERS, _MAN: _profile("Rafael Nadal", "19860603", False, [])})
    with pytest.raises(ValueError, match="No career matches are available for Rafael Nadal"):
        get_career_data("Rafael Nadal")


def test_archive_failure_never_returns_partial_data(female_responses, female_js):
    responses, calls = female_responses
    rows = _parse_career_js(female_js)
    responses[_CURRENT] = _profile("Serena Williams", "19810926", True, rows[:1])
    responses[_ARCHIVE] = HTTPError(_ARCHIVE, 503, "Unavailable", None, None)
    with pytest.raises(ConnectionError, match="503"):
        get_career_data("Serena Williams")


def test_malformed_archive_is_rejected(female_responses):
    responses, calls = female_responses
    responses[_ARCHIVE] = "<html>Service temporarily unavailable</html>"
    with pytest.raises(ValueError, match="morematchmx"):
        get_career_data("Serena Williams")


@pytest.mark.parametrize("declaration", ["dob", "fullname", "careerjs"])
def test_missing_metadata_is_rejected(female_responses, declaration):
    responses, calls = female_responses
    responses[_CURRENT] = responses[_CURRENT].replace(f"var {declaration} =", f"var other_{declaration} =")
    with pytest.raises(ValueError, match=declaration):
        get_career_data("Serena Williams")


def test_invalid_birth_date_is_rejected(female_responses):
    responses, calls = female_responses
    responses[_CURRENT] = responses[_CURRENT].replace("19810926", "19810230")
    with pytest.raises(ValueError, match="player_dob"):
        get_career_data("Serena Williams")


def test_invalid_archive_flag_is_rejected(female_responses):
    responses, calls = female_responses
    responses[_CURRENT] = responses[_CURRENT].replace("careerjs = 1", "careerjs = 2")
    with pytest.raises(ValueError, match="archive flag"):
        get_career_data("Serena Williams")


@pytest.mark.parametrize("name", ["GastonSanchez", "Gaston Sanchez"])
def test_unknown_player_is_rejected_before_profile_download(mock_http, name):
    responses, calls = mock_http
    responses[_INDEX] = _PLAYERS
    with pytest.raises(ValueError, match="No player named"):
        get_career_data(name)
    assert [url for url, _, _ in calls] == [_INDEX]


@pytest.mark.parametrize("name, exception", [(None, TypeError), (123, TypeError), ([], TypeError), ("", ValueError), (" \t ", ValueError), ("---", ValueError)])
def test_invalid_names_make_no_requests(mock_http, name, exception):
    responses, calls = mock_http
    with pytest.raises(exception, match="player_name"):
        get_career_data(name)
    assert calls == []


def test_ambiguous_name_can_be_disambiguated(mock_http):
    responses, calls = mock_http
    responses[_INDEX] = 'var playerlist=["(W) Alex Smith", "(M) Alex Smith"];'
    with pytest.raises(ValueError, match="Ambiguous player name"):
        get_career_data("Alex Smith")
    assert _resolve_player("(W) Alex Smith", 20.0) == ("Alex Smith", "W")


def test_accents_and_punctuation_match_index_names(mock_http):
    responses, calls = mock_http
    responses[_INDEX] = 'var playerlist=["(W) Iga Swiatek", "(M) Jo-Wilfried Tsonga"];'
    assert _resolve_player("Íga Świątek", 20.0) == ("Iga Swiatek", "W")
    assert _resolve_player("jo wilfried tsonga", 20.0) == ("Jo-Wilfried Tsonga", "M")


def test_timeout_header_and_index_cache(female_responses):
    responses, calls = female_responses
    get_career_data("Serena Williams", timeout=7)
    get_career_data("serenawilliams", timeout=7)
    assert [url for url, _, _ in calls].count(_INDEX) == 1
    assert [url for url, _, _ in calls].count(_CURRENT) == 2
    assert all(timeout == 7 and agent == "tennisage/0.1.0" for _, timeout, agent in calls)


@pytest.mark.parametrize("timeout, exception", [(0, ValueError), (-1, ValueError), (float("nan"), ValueError), (float("inf"), ValueError), (True, TypeError), ("20", TypeError)])
def test_invalid_timeouts_make_no_requests(mock_http, timeout, exception):
    responses, calls = mock_http
    with pytest.raises(exception, match="timeout"):
        get_career_data("Serena Williams", timeout=timeout)
    assert calls == []


@pytest.mark.parametrize("error", [URLError("DNS failure"), TimeoutError("timed out"), HTTPError(_INDEX, 429, "Too many requests", None, None)])
def test_network_failure_is_not_an_unknown_player(mock_http, error):
    responses, calls = mock_http
    responses[_INDEX] = error
    with pytest.raises(ConnectionError, match="Tennis Abstract request failed") as caught:
        get_career_data("Serena Williams")
    assert caught.value.__cause__ is error
