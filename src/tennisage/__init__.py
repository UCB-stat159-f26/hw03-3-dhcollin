"""Career match data and age comparisons from Tennis Abstract."""

from importlib.metadata import version as _version

from .data import get_career_data
from .plotting import plot_age_difference

__version__ = _version("tennisage")

__all__ = ["get_career_data", "plot_age_difference"]
