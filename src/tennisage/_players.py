"""Resolve player names through the Tennis Abstract player index."""

from functools import lru_cache
import re
import unicodedata
from urllib.parse import quote

from ._download import _download_text
from ._parsing import _decode_records, _parse_scalar

_BASE_URL = "https://www.tennisabstract.com"
_INDEX_URL = f"{_BASE_URL}/mwplayerlist.js"


def _name_key(name: str) -> str:
    """Ignore case, spacing, punctuation, and combining accents when matching names."""
    if not isinstance(name, str):
        raise TypeError("player_name must be a string.")
    normalized = unicodedata.normalize("NFKD", name).casefold()
    key = "".join(character for character in normalized if character.isalnum())
    if not key:
        raise ValueError("player_name must contain a player's name.")
    return key


@lru_cache(maxsize=1)
def _player_index(timeout: float):
    """Cache the successfully parsed player index within this Python process."""
    return _parse_player_index(_download_text(_INDEX_URL, timeout))


def _parse_player_index(source: str):
    """Validate the index's labeled player names and remove exact repetitions."""
    entries = _decode_records(source, "playerlist")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Tennis Abstract returned an empty or invalid player index.")
    return tuple(dict.fromkeys(_clean_index_entry(item) for item in entries))


def _clean_index_entry(entry):
    """Normalize the extra whitespace present in some historical index entries."""
    match = re.fullmatch(r"\(([MW])\)\s+(.+)", entry) if isinstance(entry, str) else None
    if match is None or not match.group(2).strip():
        raise ValueError("Tennis Abstract returned an invalid player index entry.")
    return f"({match.group(1)}) {' '.join(match.group(2).split())}"


def _resolve_player(player_name: str, timeout: float):
    """Return one canonical player name and its M or W index label."""
    key = _name_key(player_name)
    matches = [item for item in _player_index(timeout) if key in (_name_key(item[4:]), _name_key(item))]
    if not matches:
        raise ValueError(f"No player named {player_name!r} was found in Tennis Abstract's player index.")
    if len(matches) > 1:
        raise ValueError(f"Ambiguous player name {player_name!r}; use one of: {', '.join(matches)}.")
    return matches[0][4:], matches[0][1]


def _player_url(player_name: str, tour: str) -> str:
    """Build the matching men's or women's classic profile URL."""
    prefix = "w" if tour == "W" else ""
    slug = quote("".join(player_name.split()), safe="")
    return f"{_BASE_URL}/cgi-bin/{prefix}player-classic.cgi?p={slug}&f=ACareerqq"


def _match_url(player_name: str, archive: bool = False) -> str:
    """Build a current or archive match file URL from the canonical name."""
    slug = quote("".join(player_name.split()), safe="")
    suffix = "Career" if archive else ""
    return f"{_BASE_URL}/jsmatches/{slug}{suffix}.js"


def _profile_metadata(source: str, expected_name: str):
    """Validate player identity and extract birth date and archive availability."""
    name = _parse_scalar(source, "fullname")
    birth_date = str(_parse_scalar(source, "dob"))
    archive = _parse_scalar(source, "careerjs")
    if not isinstance(name, str) or _name_key(name) != _name_key(expected_name):
        raise ValueError(f"Tennis Abstract returned a different player than {expected_name!r}.")
    if archive not in (0, 1):
        raise ValueError("Player metadata contain an invalid careerjs archive flag.")
    return name, birth_date, bool(archive)
