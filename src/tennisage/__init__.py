"""Career match data and age comparisons from Tennis Abstract."""

from importlib.metadata import version as _version

from .data import get_career_data

__version__ = _version("tennisage")

__all__ = ["get_career_data"]
