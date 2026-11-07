"""Validate player indexes, metadata literals, and response decoding offline."""

from email.message import Message
from io import BytesIO
from unittest.mock import Mock

import pytest

from tennisage._download import _decode_text, _download_text
from tennisage._parsing import _parse_career_js, _parse_scalar
from tennisage._players import _parse_player_index


@pytest.mark.parametrize("source", ["var playerlist=[];", "var playerlist={};", 'var playerlist=["Serena Williams"];', 'var playerlist=["(X) Someone"];', 'var playerlist=["(M) "];', "var playerlist=[12];"])
def test_invalid_player_indexes_raise(source):
    with pytest.raises(ValueError, match="player index"):
        _parse_player_index(source)


def test_exact_index_repetitions_are_removed():
    source = 'var playerlist=["(W) Serena Williams", "(W) Serena Williams"];'
    assert _parse_player_index(source) == ("(W) Serena Williams",)


def test_historical_index_spacing_is_normalized():
    source = 'var playerlist=["(W)  Fehlmann", "(W)  Serena   Williams ", "(W) Serena Williams"];'
    assert _parse_player_index(source) == ("(W) Fehlmann", "(W) Serena Williams")


@pytest.mark.parametrize("literal, expected", [("19810926", 19810926), ("'Serena Williams'", "Serena Williams"), ('"Serena Williams"', "Serena Williams"), ("'D\\'Arcy'", "D'Arcy")])
def test_metadata_scalar_literals(literal, expected):
    assert _parse_scalar(f"var example = {literal};", "example") == expected


@pytest.mark.parametrize("source", ["var dob = run_code();", "var dob = 19810926 + 1;", "// var dob = 19810926;", "var dob = 'unterminated;", "var dob = 'line\nbreak';"])
def test_metadata_expressions_and_malformed_literals_raise(source):
    with pytest.raises(ValueError):
        _parse_scalar(source, "dob")


def test_main_match_array_uses_the_same_parser(male_js):
    expected = _parse_career_js(male_js)
    current = male_js.replace("var morematchmx", "var matchmx")
    assert _parse_career_js(current, "matchmx") == expected
    assert _parse_career_js("var matchmx=[];", "matchmx", allow_empty=True) == []


def test_current_array_does_not_match_archive_name(male_js):
    with pytest.raises(ValueError, match="matchmx declaration"):
        _parse_career_js(male_js, "matchmx")


def test_http_response_is_closed_and_encoding_is_honored(monkeypatch):
    response = BytesIO("André".encode("iso-8859-1"))
    response.headers = Message()
    response.headers["Content-Type"] = "text/javascript; charset=iso-8859-1"
    opener = Mock(return_value=response)
    monkeypatch.setattr("tennisage._download.urlopen", opener)
    assert _download_text("https://www.tennisabstract.com/example.js", 5) == "André"
    assert response.closed
    assert opener.call_args.kwargs["timeout"] == 5


def test_byte_order_mark_is_removed():
    assert _decode_text(b"\xef\xbb\xbfvar dob=19810926;", "utf-8") == "var dob=19810926;"


@pytest.mark.parametrize("content, encoding", [(b"\xff", "utf-8"), (b"text", "not-a-real-codec")])
def test_invalid_response_encoding_raises(content, encoding):
    with pytest.raises(ValueError, match="invalid encoding"):
        _decode_text(content, encoding)
