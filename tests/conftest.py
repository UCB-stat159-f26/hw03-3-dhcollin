"""Local career data shared by the tests."""

from pathlib import Path
from email.message import Message
from io import BytesIO

import pytest

from tennisage._players import _player_index


_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def female_js():
    """Read the women's career sample from disk."""
    return (_FIXTURES / "FemalePlayerCareer.js").read_text(encoding="utf-8")


@pytest.fixture
def male_js():
    """Read the men's career sample from disk."""
    return (_FIXTURES / "MalePlayerCareer.js").read_text(encoding="utf-8")


@pytest.fixture
def mock_http(monkeypatch):
    """Replace HTTP responses with local payloads and record each request."""
    responses, calls = {}, []
    def open_response(request, *, timeout):
        calls.append((request.full_url, timeout, request.get_header("User-agent")))
        payload = responses[request.full_url]
        if isinstance(payload, Exception):
            raise payload
        response = BytesIO(payload.encode("utf-8") if isinstance(payload, str) else payload)
        response.headers = Message()
        return response
    monkeypatch.setattr("tennisage._download.urlopen", open_response)
    _player_index.cache_clear()
    yield responses, calls
    _player_index.cache_clear()
