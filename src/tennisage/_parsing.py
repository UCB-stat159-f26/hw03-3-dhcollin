"""Decode Tennis Abstract career match arrays without executing JavaScript."""

import ast
import json
import re


_DECLARATION = r"^[ \t]*(?:var|let|const)\s+{}\s*=\s*"
_SCALAR = re.compile(r'''('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|-?[0-9]+)\s*;''')
_MIN_FIELDS = 17


def _parse_career_js(source: str, variable="morematchmx", allow_empty=False) -> list[list[str]]:
    """Return match rows with their original field positions and text values."""
    if not isinstance(source, str):
        raise TypeError("Career data must be supplied as text.")
    records = _decode_records(source.lstrip("\ufeff"), variable)
    if allow_empty and records == []:
        return records
    _validate_records(records)
    return records


def _decode_records(source: str, variable="morematchmx"):
    """Extract a JSON value assigned to a named JavaScript variable."""
    match = _find_assignment(source, variable)
    if match is None:
        raise ValueError(f"Career data do not contain a {variable} declaration.")
    try:
        return json.JSONDecoder().raw_decode(source[match.end():])[0]
    except json.JSONDecodeError as exc:
        raise ValueError(f"The {variable} value is not valid JSON.") from exc


def _find_assignment(source: str, variable: str):
    """Find a declaration at the beginning of a JavaScript source line."""
    return re.search(_DECLARATION.format(re.escape(variable)), source, re.MULTILINE)


def _parse_scalar(source: str, variable: str):
    """Read a quoted string or integer without executing JavaScript."""
    source = source.lstrip("\ufeff")
    assignment = _find_assignment(source, variable)
    match = _SCALAR.match(source, assignment.end()) if assignment else None
    if match is None:
        raise ValueError(f"Player metadata lack a valid {variable} declaration.")
    return _literal_value(match.group(1))


def _literal_value(literal: str):
    """Convert a scalar literal and report malformed quoting consistently."""
    try:
        return ast.literal_eval(literal)
    except (ValueError, SyntaxError) as exc:
        raise ValueError("Player metadata contain an invalid string or integer.") from exc


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
