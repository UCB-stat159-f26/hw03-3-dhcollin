"""Test career array parsing with local data and malformed inputs."""

import json

import pytest

from tennisage._parsing import _parse_career_js


def _script(records):
    """Wrap JSON data in a JavaScript variable declaration."""
    return "var morematchmx = " + json.dumps(records) + ";"


def test_female_sample_preserves_dates_and_results(female_js):
    records = _parse_career_js(female_js)
    assert len(records) == 3
    assert records[0][0] == "19951030"
    assert records[0][3:5] == ["W", "L"]
    assert records[0][11] == "Anne Miller"
    assert records[0][16] == "19770119"
    assert records[2][11] == "Magui Serna"


def test_male_sample_preserves_opponent_ages(male_js):
    records = _parse_career_js(male_js)
    assert len(records) == 3
    assert records[0][0] == "20010910"
    assert records[0][11] == "Guillermo Platel"
    assert records[0][16] == "22.264202601"
    assert records[2][16] == "18.7597535934"
    assert [row[4] for row in records] == ["L", "L", "W"]


@pytest.mark.parametrize("prefix", ["\ufeff \tvar", "let", "const"])
def test_accepts_declarations_and_whitespace(female_js, prefix):
    source = female_js.replace("var morematchmx =", prefix + "\tmorematchmx\n=\r\n", 1)
    assert _parse_career_js(source)[0][11] == "Anne Miller"


def test_ignores_surrounding_javascript(female_js):
    source = "var player = 'Serena Williams';\n" + female_js
    source += "\nthrow new Error('Do not execute this script');"
    assert len(_parse_career_js(source)) == 3


def test_preserves_text_and_blank_fields():
    row = [""] * 17
    row[11] = 'Zoë "Ace" O\'Brien ] \\ Court'
    row[16] = "22.264202601"
    assert _parse_career_js(_script([row])) == [row]


@pytest.mark.parametrize("width", [17, 27, 47])
def test_accepts_different_row_widths(width):
    row = [""] * width
    assert _parse_career_js(_script([row])) == [row]


@pytest.mark.parametrize("source", [
    "", "<html>Not found</html>", "var other = [];",
    "// var morematchmx = [];", 'var label = "var morematchmx = [];";',
])
def test_rejects_missing_match_array(source):
    with pytest.raises(ValueError, match="morematchmx declaration"):
        _parse_career_js(source)


@pytest.mark.parametrize("value", ["[[", "undefined", "loadMatches()", "[['x']]"])
def test_rejects_malformed_json(value):
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_career_js("var morematchmx = " + value)


@pytest.mark.parametrize("records", [None, {}, "matches"])
def test_rejects_nonarray_match_data(records):
    with pytest.raises(ValueError, match="must be an array of match rows"):
        _parse_career_js(_script(records))


def test_rejects_empty_match_array():
    with pytest.raises(ValueError, match="contains no matches"):
        _parse_career_js(_script([]))


@pytest.mark.parametrize("row", [None, {}, "match"])
def test_rejects_nonarray_rows(row):
    with pytest.raises(ValueError, match="Match row 1 must be an array"):
        _parse_career_js(_script([row]))


@pytest.mark.parametrize("width", [0, 16])
def test_rejects_short_rows(width):
    with pytest.raises(ValueError, match="at least 17 fields"):
        _parse_career_js(_script([[""] * width]))


@pytest.mark.parametrize("value", [None, 22.5, True, {"age": "22.5"}])
def test_rejects_nontext_fields(value):
    row = [""] * 17
    row[16] = value
    with pytest.raises(ValueError, match="Match row 1 must contain only text fields"):
        _parse_career_js(_script([row]))


def test_error_identifies_the_invalid_row():
    records = [[""] * 17, [""] * 16]
    with pytest.raises(ValueError, match="Match row 2"):
        _parse_career_js(_script(records))


@pytest.mark.parametrize("source", [None, 123, b"var morematchmx = [];"])
def test_rejects_nontext_source(source):
    with pytest.raises(TypeError, match="must be supplied as text"):
        _parse_career_js(source)
