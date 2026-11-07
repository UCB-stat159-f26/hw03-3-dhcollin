"""Retrieve text from Tennis Abstract with bounded request times."""

import math
from numbers import Real
from urllib.error import URLError
from urllib.request import Request, urlopen


def _validate_timeout(timeout) -> None:
    """Require a positive, finite timeout in seconds."""
    if isinstance(timeout, bool) or not isinstance(timeout, Real):
        raise TypeError("timeout must be a positive number of seconds.")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive, finite number of seconds.")


def _download_text(url: str, timeout: float) -> str:
    """Report network and HTTP failures separately from invalid source data."""
    try:
        content, encoding = _read_response(url, timeout)
    except (URLError, OSError) as exc:
        raise ConnectionError(f"Tennis Abstract request failed for {url}: {exc}") from exc
    return _decode_text(content, encoding)


def _read_response(url: str, timeout: float):
    """Read and close one HTTP response while respecting its declared encoding."""
    request = Request(url, headers={"User-Agent": "tennisage/0.1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get_content_charset() or "utf-8"


def _decode_text(content: bytes, encoding: str) -> str:
    """Decode a response strictly and remove a leading byte-order mark."""
    try:
        return content.decode(encoding).lstrip("\ufeff")
    except (LookupError, UnicodeError) as exc:
        raise ValueError("Tennis Abstract returned text with an invalid encoding.") from exc
