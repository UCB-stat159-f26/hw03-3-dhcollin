"""Decode Tennis Abstract career match arrays without executing JavaScript."""

import json
import re


_MATCH_ARRAY = re.compile(
    r"^[ \t]*(?:var|let|const)\s+morematchmx\s*=\s*", re.MULTILINE
)
_MIN_FIELDS = 17


def _parse_career_js(source: str) -> list[list[str]]:
    """Return match rows with their original field positions and text values."""
    if not isinstance(source, str):
        raise TypeError("Career data must be supplied as text.")
    records = _decode_records(source.lstrip("\ufeff"))
    _validate_records(records)
    return records


def _decode_records(source: str):
    """Extract the JSON value assigned to the morematchmx variable."""
    match = _MATCH_ARRAY.search(source)
    if match is None:
        raise ValueError("Career data do not contain a morematchmx declaration.")
    try:
        return json.JSONDecoder().raw_decode(source[match.end():])[0]
    except json.JSONDecodeError as exc:
        raise ValueError("The morematchmx value is not valid JSON.") from exc


def _validate_records(records) -> None:
    """Require a nonempty array and validate every match row."""
    if not isinstance(records, list):
        raise ValueError("The morematchmx value must be an array of match rows.")
    if not records:
        raise ValueError("The morematchmx array contains no matches.")
    for number, row in enumerate(records, start=1):
        _validate_row(row, number)


def _validate_row(row, number: int) -> None:
    """Check row width and text fields, including opponent information at index 16."""
    if not isinstance(row, list) or len(row) < _MIN_FIELDS:
        raise ValueError(f"Match row {number} must be an array with at least 17 fields.")
    if any(not isinstance(value, str) for value in row):
        raise ValueError(f"Match row {number} must contain only text fields.")
