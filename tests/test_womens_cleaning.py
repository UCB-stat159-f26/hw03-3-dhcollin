"""Check women's career cleaning using local match records."""

from copy import deepcopy

import pandas as pd
import pytest

from tennisage._cleaning import _clean_womens_records
from tennisage._parsing import _parse_career_js


@pytest.fixture
def womens_records(female_js):
    """Parse the local sample into independent records for each test."""
    return _parse_career_js(female_js)


def test_known_ages_and_gap(womens_records):
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    first = frame.iloc[0]
    assert first["player_age"] == pytest.approx(5147 / 365.25)
    assert first["opponent_age"] == pytest.approx(6858 / 365.25)
    assert first["age_difference"] == pytest.approx(-1711 / 365.25)
    assert first["tournament_date"] == pd.Timestamp("1995-10-30")
    assert first["opponent_dob"] == pd.Timestamp("1977-01-19")
    assert frame["included_in_plot"].all()
    assert frame["exclusion_reason"].eq("").all()
    assert frame["result"].tolist() == ["L", "L", "L"]


def test_output_schema_and_types(womens_records):
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame.columns.tolist() == [
        "source_row", "player_name", "player_dob", "tournament_date",
        "tournament", "surface", "level_code", "result", "round", "score",
        "opponent", "opponent_dob", "player_age", "opponent_age",
        "age_difference", "included_in_plot", "exclusion_reason",
    ]
    for name in ["player_dob", "tournament_date", "opponent_dob"]:
        assert pd.api.types.is_datetime64_any_dtype(frame[name])
    for name in ["player_age", "opponent_age", "age_difference"]:
        assert pd.api.types.is_float_dtype(frame[name])
    assert pd.api.types.is_integer_dtype(frame["source_row"])
    assert pd.api.types.is_bool_dtype(frame["included_in_plot"])
    assert frame["source_row"].tolist() == [1, 2, 3]


@pytest.mark.parametrize("birth_date", ["19810926", "1981-09-26", " 1981-09-26 "])
def test_player_birth_date_formats(womens_records, birth_date):
    frame = _clean_womens_records(womens_records, "Serena Williams", birth_date)
    assert frame["player_dob"].eq(pd.Timestamp("1981-09-26")).all()


def test_player_identity_is_not_fixed(womens_records):
    frame = _clean_womens_records(womens_records, "  Example   Player ", "19800926")
    assert frame["player_name"].eq("Example Player").all()
    assert frame["player_dob"].eq(pd.Timestamp("1980-09-26")).all()
    assert frame.loc[0, "player_age"] == pytest.approx(5512 / 365.25)


def test_source_fields_are_preserved_without_mutating_input(womens_records):
    womens_records[0][1] = "  Canadian Open "
    original = deepcopy(womens_records)
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert womens_records == original
    assert frame.loc[0, "tournament"] == "Canadian Open"
    assert frame.loc[0, "surface"] == "Carpet"
    assert frame.loc[0, "level_code"] == "W"
    assert frame.loc[0, "round"] == "Q1"
    assert frame.loc[0, "score"] == "6-1 6-1"
    assert frame.loc[0, "opponent"] == "Anne Miller"


def test_chronological_order_preserves_source_positions(womens_records):
    frame = _clean_womens_records(womens_records[::-1], "Serena Williams", "19810926")
    assert frame["tournament_date"].is_monotonic_increasing
    assert frame["source_row"].tolist() == [3, 2, 1]
    assert frame.index.tolist() == [0, 1, 2]


def test_tied_dates_retain_source_order(womens_records):
    womens_records[1][0] = womens_records[0][0]
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame["source_row"].tolist() == [1, 2, 3]


def test_full_career_has_no_article_date_cutoff(womens_records):
    womens_records[0][0] = "20220902"
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert len(frame) == 3
    assert frame.iloc[-1]["tournament_date"] == pd.Timestamp("2022-09-02")
    assert frame.iloc[-1]["included_in_plot"]


@pytest.mark.parametrize("opponent_dob, expected_days", [
    ("19800926", -365), ("19810926", 0), ("19820926", 365),
])
def test_gap_sign_means_player_age_minus_opponent_age(womens_records, opponent_dob, expected_days):
    womens_records[0][16] = opponent_dob
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame.loc[0, "age_difference"] == pytest.approx(expected_days / 365.25)


@pytest.mark.parametrize("score", ["W/O", " wo ", "Walkover", "DEF", "default", "W / O"])
def test_unplayed_matches_are_retained_but_excluded(womens_records, score):
    womens_records[0][9] = score
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert len(frame) == 3
    assert not frame.loc[0, "included_in_plot"]
    assert frame.loc[0, "exclusion_reason"] == "walkover_or_default"
    assert frame.loc[0, "score"] == score.strip()
    assert frame.loc[1:, "included_in_plot"].all()


@pytest.mark.parametrize("score", ["6-2 1-0 RET", "RET", "6-2 2-0 DEF", "6-1 6-1"])
def test_played_matches_and_retirements_are_included(womens_records, score):
    womens_records[0][9] = score
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame.loc[0, "included_in_plot"]
    assert frame.loc[0, "exclusion_reason"] == ""


def test_missing_opponent_birth_date_keeps_row(womens_records):
    womens_records[0][16] = " "
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert len(frame) == 3
    assert pd.isna(frame.loc[0, "opponent_dob"])
    assert pd.isna(frame.loc[0, "opponent_age"])
    assert pd.isna(frame.loc[0, "age_difference"])
    assert not frame.loc[0, "included_in_plot"]
    assert frame.loc[0, "exclusion_reason"] == "missing_opponent_age"
    assert frame.loc[1:, "included_in_plot"].all()


def test_all_missing_opponent_birth_dates(womens_records):
    for row in womens_records:
        row[16] = ""
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame["opponent_dob"].isna().all()
    assert frame["opponent_age"].isna().all()
    assert not frame["included_in_plot"].any()


def test_multiple_exclusion_reasons(womens_records):
    womens_records[0][16] = ""
    womens_records[0][9] = "W/O"
    frame = _clean_womens_records(womens_records, "Serena Williams", "19810926")
    assert frame.loc[0, "exclusion_reason"] == "walkover_or_default;missing_opponent_age"
    assert not frame.loc[0, "included_in_plot"]


@pytest.mark.parametrize("index, value, field", [
    (0, "", "tournament_date"), (0, "1995-10-30", "tournament_date"),
    (0, "19950230", "tournament_date"), (16, "1977-01-19", "opponent_dob"),
    (16, "19770229", "opponent_dob"), (16, "22.264202601", "opponent_dob"),
])
def test_invalid_source_dates_raise(womens_records, index, value, field):
    womens_records[0][index] = value
    with pytest.raises(ValueError, match=field):
        _clean_womens_records(womens_records, "Serena Williams", "19810926")


@pytest.mark.parametrize("birth_date", ["", "19810229", "09/26/1981", "1981-9-26"])
def test_invalid_player_birth_dates_raise(womens_records, birth_date):
    with pytest.raises(ValueError, match="player_dob"):
        _clean_womens_records(womens_records, "Serena Williams", birth_date)


@pytest.mark.parametrize("birth_date", [None, 19810926])
def test_nontext_player_birth_dates_raise(womens_records, birth_date):
    with pytest.raises(TypeError, match="player_dob"):
        _clean_womens_records(womens_records, "Serena Williams", birth_date)


@pytest.mark.parametrize("name", ["", "  ", None, 123])
def test_invalid_player_names_raise(womens_records, name):
    with pytest.raises(ValueError, match="player_name"):
        _clean_womens_records(womens_records, name, "19810926")


@pytest.mark.parametrize("result", ["", "win", "Q", "w"])
def test_invalid_results_raise(womens_records, result):
    womens_records[0][4] = result
    with pytest.raises(ValueError, match="results must be W or L"):
        _clean_womens_records(womens_records, "Serena Williams", "19810926")


@pytest.mark.parametrize("index", [1, 8, 9, 11])
def test_blank_required_text_raises(womens_records, index):
    womens_records[0][index] = " "
    with pytest.raises(ValueError, match="must not be blank"):
        _clean_womens_records(womens_records, "Serena Williams", "19810926")


def test_duplicate_matches_raise(womens_records):
    womens_records.append(deepcopy(womens_records[0]))
    with pytest.raises(ValueError, match="Duplicate matches"):
        _clean_womens_records(womens_records, "Serena Williams", "19810926")


@pytest.mark.parametrize("index, birth_date, field", [
    (16, "20000101", "opponent_age"), (16, "18000101", "opponent_age"),
    (None, "20000101", "player_age"), (None, "18000101", "player_age"),
])
def test_impossible_ages_raise(womens_records, index, birth_date, field):
    player_dob = birth_date if index is None else "19810926"
    if index is not None:
        womens_records[0][index] = birth_date
    with pytest.raises(ValueError, match=field):
        _clean_womens_records(womens_records, "Serena Williams", player_dob)


def test_leap_day_age_uses_elapsed_days(womens_records):
    row = womens_records[0]
    row[0], row[16] = "20200229", "20000228"
    frame = _clean_womens_records([row], "Example Player", "20000229")
    assert frame.loc[0, "player_age"] == pytest.approx(20.0)
    assert frame.loc[0, "opponent_age"] == pytest.approx(20.0 + 1 / 365.25)
    assert frame.loc[0, "age_difference"] == pytest.approx(-1 / 365.25)
