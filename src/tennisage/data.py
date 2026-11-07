"""Public career-data retrieval."""

import pandas as pd

from ._cleaning import _clean_downloaded_records
from ._download import _download_text, _validate_timeout
from ._parsing import _find_assignment, _parse_career_js
from ._players import _match_url, _player_url, _profile_metadata, _resolve_player


def get_career_data(player_name: str, *, timeout: float = 20.0) -> pd.DataFrame:
    """Download and clean a player's full available singles career.

    Accept spaced or compact names, ignoring case and accents. Each request
    uses the supplied timeout in seconds. Return chronologically sorted
    records with ages, signed age differences, and explicit plot flags.
    Raise TypeError for incorrect argument types, ValueError for unknown or
    ambiguous names or invalid data, and ConnectionError for request failures.
    """
    _validate_timeout(timeout)
    name, tour = _resolve_player(player_name, timeout)
    source = _load_profile(name, tour, timeout)
    name, birth_date, archive = _profile_metadata(source, name)
    records = _career_records(source, name, archive, timeout)
    return _clean_downloaded_records(records, name, birth_date, tour)


def _load_profile(name: str, tour: str, timeout: float) -> str:
    """Use an embedded profile table or load the profile's legacy JavaScript."""
    page = _download_text(_player_url(name, tour), timeout)
    if _find_assignment(page, "matchmx") is not None:
        return page
    return _download_text(_match_url(name), timeout)


def _career_records(source: str, name: str, archive: bool, timeout: float):
    """Assemble current and archive rows without counting their overlap twice."""
    recent = _parse_career_js(source, "matchmx", allow_empty=True)
    older = []
    if archive:
        older = _parse_career_js(_download_text(_match_url(name, archive=True), timeout))
    rows = _merge_records(older, recent)
    if not rows:
        raise ValueError(f"No career matches are available for {name}.")
    return rows


def _merge_records(older, recent):
    """Prefer a current record when both files contain the same match."""
    recent_keys = {_match_key(row) for row in recent}
    return [row for row in older if _match_key(row) not in recent_keys] + recent


def _match_key(row):
    """Identify a match by date, tournament, round, and opponent."""
    return tuple(row[index].strip() for index in (0, 1, 8, 11))
