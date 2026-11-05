"""Local career data shared by the tests."""

from pathlib import Path

import pytest


_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def female_js():
    """Read the women's career sample from disk."""
    return (_FIXTURES / "FemalePlayerCareer.js").read_text(encoding="utf-8")


@pytest.fixture
def male_js():
    """Read the men's career sample from disk."""
    return (_FIXTURES / "MalePlayerCareer.js").read_text(encoding="utf-8")
