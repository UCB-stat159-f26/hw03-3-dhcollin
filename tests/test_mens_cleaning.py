"""Check reported opponent ages and the shared career data format offline."""

from copy import deepcopy

import pandas as pd
import pytest

from tennisage._cleaning import _clean_mens_records, _clean_womens_records
from tennisage._parsing import _parse_career_js


@pytest.fixture
def mens_records(male_js):
    """Parse the local men's sample into independent records for each test."""
    return _parse_career_js(male_js)


def test_reported_ages_and_player_age(mens_records):
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    expected = [22.264202601, 24.2902121834, 18.7597535934]
    assert frame["opponent_age"].tolist() == pytest.approx(expected, rel=0, abs=1e-12)
    assert frame.loc[0, "player_age"] == pytest.approx(5578 / 365.25)
    assert frame.loc[0, "age_difference"] == pytest.approx(5578 / 365.25 - expected[0])
    assert frame["result"].tolist() == ["L", "L", "W"]
    assert frame["player_name"].eq("Rafael Nadal").all()
    assert frame["player_dob"].eq(pd.Timestamp("1986-06-03")).all()


def test_missing_birth_dates_do_not_exclude_reported_ages(mens_records):
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert frame["opponent_dob"].isna().all()
    assert pd.api.types.is_datetime64_any_dtype(frame["opponent_dob"])
    assert frame["included_in_plot"].all()
    assert frame["exclusion_reason"].eq("").all()


def test_mens_and_womens_schemas_match(mens_records, female_js):
    men = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    women = _clean_womens_records(_parse_career_js(female_js), "Serena Williams", "19810926")
    assert men.columns.tolist() == women.columns.tolist()
    assert men.dtypes.equals(women.dtypes)
    combined = pd.concat([women, men], ignore_index=True)
    assert len(combined) == 6
    assert combined["included_in_plot"].all()
    assert combined[["player_age", "opponent_age", "age_difference"]].notna().all().all()


@pytest.mark.parametrize("value, expected", [(" 22.5 ", 22.5), ("22", 22.0), ("22.123456789", 22.123456789)])
def test_numeric_age_formats_preserve_precision(mens_records, value, expected):
    mens_records[0][16] = value
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert frame.loc[0, "opponent_age"] == pytest.approx(expected, rel=0, abs=1e-12)
    assert pd.api.types.is_float_dtype(frame["opponent_age"])


@pytest.mark.parametrize("age, gap", [(19.0, 1.0), (20.0, 0.0), (21.0, -1.0)])
def test_gap_sign_uses_reported_age(mens_records, age, gap):
    row = mens_records[0]
    row[0], row[16] = "20200229", str(age)
    frame = _clean_mens_records([row], "Example Player", "20000229")
    assert frame.loc[0, "player_age"] == pytest.approx(20.0)
    assert frame.loc[0, "age_difference"] == pytest.approx(gap)


def test_reported_age_is_not_recalculated_from_match_date(mens_records):
    mens_records[0][0] = "20240101"
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    first_source_row = frame.loc[frame["source_row"].eq(1)].iloc[0]
    assert first_source_row["opponent_age"] == pytest.approx(22.264202601, rel=0, abs=1e-12)
    assert first_source_row["included_in_plot"]
    assert len(frame) == 3


@pytest.mark.parametrize("value", ["", " \t "])
def test_missing_reported_age_keeps_row_but_excludes_plot(mens_records, value):
    mens_records[0][16] = value
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert len(frame) == 3
    assert pd.isna(frame.loc[0, "opponent_age"])
    assert pd.isna(frame.loc[0, "age_difference"])
    assert not frame.loc[0, "included_in_plot"]
    assert frame.loc[0, "exclusion_reason"] == "missing_opponent_age"
    assert frame.loc[1:, "included_in_plot"].all()


def test_all_reported_ages_missing(mens_records):
    for row in mens_records:
        row[16] = ""
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert len(frame) == 3
    assert pd.api.types.is_float_dtype(frame["opponent_age"])
    assert frame["opponent_age"].isna().all()
    assert not frame["included_in_plot"].any()
    assert frame["exclusion_reason"].eq("missing_opponent_age").all()


@pytest.mark.parametrize("value", ["unknown", "22 years", "22,5", "NaN", "null", "1977-01-19"])
def test_invalid_reported_ages_raise(mens_records, value):
    mens_records[0][16] = value
    with pytest.raises(ValueError, match="opponent_age must contain numeric ages"):
        _clean_mens_records(mens_records, "Rafael Nadal", "19860603")


@pytest.mark.parametrize("value", ["-0.1", "100", "19770119", "inf", "-inf", "Infinity", "1e309"])
def test_out_of_range_and_nonfinite_ages_raise(mens_records, value):
    mens_records[0][16] = value
    with pytest.raises(ValueError, match="opponent_age"):
        _clean_mens_records(mens_records, "Rafael Nadal", "19860603")


@pytest.mark.parametrize("score", ["W/O", " default "])
def test_mens_walkovers_and_defaults_are_excluded(mens_records, score):
    mens_records[0][9] = score
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert len(frame) == 3
    assert not frame.loc[0, "included_in_plot"]
    assert frame.loc[0, "exclusion_reason"] == "walkover_or_default"
    assert frame.loc[1:, "included_in_plot"].all()


@pytest.mark.parametrize("score", ["6-2 1-0 RET", "6-2 2-0 DEF"])
def test_mens_played_matches_remain_included(mens_records, score):
    mens_records[0][9] = score
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert frame["included_in_plot"].all()


def test_missing_age_and_walkover_record_both_reasons(mens_records):
    mens_records[0][9], mens_records[0][16] = "W/O", ""
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert frame.loc[0, "exclusion_reason"] == "walkover_or_default;missing_opponent_age"
    assert not frame.loc[0, "included_in_plot"]


def test_mens_cleaning_preserves_input_and_source_order(mens_records):
    mens_records.reverse()
    original = deepcopy(mens_records)
    frame = _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
    assert mens_records == original
    assert frame["source_row"].tolist() == [3, 1, 2]
    assert frame["tournament_date"].is_monotonic_increasing
    assert frame.index.tolist() == [0, 1, 2]
    assert frame.loc[0, "opponent"] == "Guillermo Platel"
    assert frame.loc[0, "round"] == "R32"


def test_mens_cleaner_accepts_supplied_player_identity(mens_records):
    frame = _clean_mens_records(mens_records, "  Example   Player ", "1985-06-03")
    assert frame["player_name"].eq("Example Player").all()
    assert frame["player_dob"].eq(pd.Timestamp("1985-06-03")).all()
    assert frame.loc[0, "player_age"] == pytest.approx(5943 / 365.25)


def test_mens_cleaner_reuses_match_validation(mens_records):
    mens_records.append(deepcopy(mens_records[0]))
    with pytest.raises(ValueError, match="Duplicate matches"):
        _clean_mens_records(mens_records, "Rafael Nadal", "19860603")
