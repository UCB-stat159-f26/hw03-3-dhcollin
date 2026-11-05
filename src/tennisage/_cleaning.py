"""Clean career records and calculate ages from player birth dates."""

import re

import pandas as pd

from ._parsing import _validate_records

_RAW_FIELDS = {
    "tournament_date": 0,
    "tournament": 1,
    "surface": 2,
    "level_code": 3,
    "result": 4,
    "round": 8,
    "score": 9,
    "opponent": 11,
    "opponent_info": 16,
}
_REQUIRED_TEXT = ["tournament", "opponent", "round", "score"]
_MATCH_KEY = ["tournament_date", "tournament", "round", "opponent"]
_UNPLAYED_SCORES = {"W/O", "WO", "WALKOVER", "DEF", "DEFAULT"}
_OUTPUT_COLUMNS = [
    "source_row", "player_name", "player_dob", "tournament_date",
    "tournament", "surface", "level_code", "result", "round", "score",
    "opponent", "opponent_dob", "player_age", "opponent_age",
    "age_difference", "included_in_plot", "exclusion_reason",
]


def _clean_womens_records(records, player_name: str, player_dob: str) -> pd.DataFrame:
    """Return women's career records with ages, age differences, and plot flags."""
    frame = _match_frame(records)
    births = frame.pop("opponent_info")
    frame["opponent_dob"] = _parse_dates(births, "opponent_dob", allow_missing=True)
    frame = _add_player(frame, player_name, player_dob)
    frame["opponent_age"] = _years_between(frame["tournament_date"], frame["opponent_dob"])
    return _finish_frame(frame)


def _match_frame(records) -> pd.DataFrame:
    """Select shared fields, trim surrounding spaces, and preserve source positions."""
    _validate_records(records)
    data = [{name: row[index].strip() for name, index in _RAW_FIELDS.items()} for row in records]
    frame = pd.DataFrame(data)
    frame.insert(0, "source_row", range(1, len(frame) + 1))
    frame["tournament_date"] = _parse_dates(frame["tournament_date"], "tournament_date")
    _validate_match_fields(frame)
    return frame


def _validate_match_fields(frame: pd.DataFrame) -> None:
    """Require valid results, match identifiers, scores, and unique match keys."""
    if not frame["result"].isin(["W", "L"]).all():
        raise ValueError("Match results must be W or L.")
    if frame[_REQUIRED_TEXT].eq("").any().any():
        raise ValueError("Tournament, opponent, round, and score must not be blank.")
    if frame.duplicated(_MATCH_KEY).any():
        raise ValueError("Duplicate matches have the same date, tournament, round, and opponent.")


def _parse_dates(values: pd.Series, column: str, allow_missing: bool = False) -> pd.Series:
    """Parse compact calendar dates, allowing blanks only when explicitly requested."""
    missing = values.eq("")
    formed = values.str.fullmatch(r"[0-9]{8}")
    if not (formed | (missing & allow_missing)).all():
        raise ValueError(f"{column} must contain dates in YYYYMMDD format.")
    dates = pd.to_datetime(values.mask(missing), format="%Y%m%d", errors="coerce")
    if (dates.isna() & ~missing).any():
        raise ValueError(f"{column} contains an invalid calendar date.")
    return dates


def _parse_player_birth_date(player_dob: str) -> pd.Timestamp:
    """Accept a player birth date written as YYYYMMDD or YYYY-MM-DD."""
    if not isinstance(player_dob, str):
        raise TypeError("player_dob must be a date string.")
    value = player_dob.strip()
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        value = value.replace("-", "")
    return _parse_dates(pd.Series([value]), "player_dob").iloc[0]


def _add_player(frame: pd.DataFrame, player_name: str, player_dob: str) -> pd.DataFrame:
    """Add the player's name, birth date, and age at each tournament."""
    if not isinstance(player_name, str) or not player_name.strip():
        raise ValueError("player_name must be a nonempty string.")
    frame["player_name"] = " ".join(player_name.split())
    frame["player_dob"] = _parse_player_birth_date(player_dob)
    frame["player_age"] = _years_between(frame["tournament_date"], frame["player_dob"])
    return frame


def _years_between(later: pd.Series, earlier: pd.Series) -> pd.Series:
    """Express elapsed calendar days in years using 365.25 days per year."""
    return (later - earlier).dt.days / 365.25


def _validate_ages(frame: pd.DataFrame) -> None:
    """Reject negative ages and ages of 100 years or more."""
    for column in ["player_age", "opponent_age"]:
        ages = frame[column].dropna()
        if not ages.between(0, 100, inclusive="left").all():
            raise ValueError(f"{column} must be at least 0 and less than 100 years.")


def _unplayed_scores(scores: pd.Series) -> pd.Series:
    """Recognize stand-alone walkover and default markers without case or spaces."""
    normalized = scores.str.upper().str.replace(r"\s+", "", regex=True)
    return normalized.isin(_UNPLAYED_SCORES)


def _add_inclusion_flags(frame: pd.DataFrame) -> pd.DataFrame:
    """Retain every row and record why a match cannot appear in the age plot."""
    reasons = pd.Series("", index=frame.index)
    reasons.loc[_unplayed_scores(frame["score"])] = "walkover_or_default"
    reasons.loc[frame["opponent_age"].isna()] += ";missing_opponent_age"
    frame["exclusion_reason"] = reasons.str.strip(";")
    frame["included_in_plot"] = frame["exclusion_reason"].eq("")
    return frame


def _finish_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate signed age differences and return rows in chronological order."""
    _validate_ages(frame)
    frame["age_difference"] = frame["player_age"] - frame["opponent_age"]
    frame = _add_inclusion_flags(frame)
    frame = frame[_OUTPUT_COLUMNS].sort_values(["tournament_date", "source_row"], kind="stable")
    return frame.reset_index(drop=True)
