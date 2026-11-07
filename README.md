# tennisage

**David H. Collin | STAT 159 | UC Berkeley | Fall 2026**

`tennisage` is the Python package for the STAT 159 tennis career analysis.
The analysis compares a player's age with the difference between that player's
age and their opponent's age, using match records from
[Tennis Abstract](https://www.tennisabstract.com/).

## Installation

Use Python 3.10 or newer. From the repository's top-level directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The editable installation uses the source files in this checkout. The `dev`
extra installs pytest, pytest-socket, and the package build tool. Runtime
dependencies are pandas and Matplotlib; their supported version ranges are
declared in `pyproject.toml`.

Confirm the installation:

```bash
python -c "import tennisage; print(tennisage.__version__)"
```

The expected version is `0.1.0`.

## Retrieve career data

```python
from tennisage import get_career_data

serena = get_career_data("serena williams")
rafa = get_career_data("RafaelNadal")
serena.head()
```

`get_career_data(player_name, *, timeout=20.0)` returns a pandas data frame
with the player's full available singles career, ages, signed age differences,
and plot-inclusion flags. Names are matched against Tennis Abstract's player
index without regard to case, spacing, punctuation, or combining accents.
The index is cached within the Python process; profile and match data are
downloaded on each call. A positive, finite `timeout` limits each HTTP request
in seconds. Internet access is required for retrieval.

The function reads a full table embedded in the profile when available.
For profiles that use separate JavaScript files, it combines the current
`matchmx` table with the `morematchmx` archive when the profile indicates an
archive exists. Current rows replace overlapping archive rows identified by
date, tournament, round, and opponent. Missing or invalid required downloads
raise an error instead of returning a partial career.

Unknown names such as `"GastonSanchez"` raise `ValueError` with the requested
name. Ambiguous names raise `ValueError` listing the indexed choices; a label
such as `"(W) Alex Smith"` can distinguish otherwise identical names.
Invalid metadata or match data also raise `ValueError`. Network, timeout, and
HTTP failures raise `ConnectionError`; incorrect argument types raise
`TypeError`.

Direct installation from the GitHub repository is also supported:

```bash
python -m pip install git+https://github.com/UCB-stat159-f26/hw03-3-dhcollin.git
```

## Tests

Run the tests from the repository's top-level directory:

```bash
python -m pytest -q
```

The pytest configuration disables network sockets with pytest-socket. Tests
must use local data or mocked responses instead of contacting Tennis Abstract.
The tests verify package installation, the network restriction, and parsing
of the women's and men's local career samples. Invalid array declarations,
malformed JSON, empty arrays, and invalid rows produce explicit errors.
Women's cleaning tests check age calculations, leap days, match inclusion,
missing birth dates, invalid values, duplicate records, and source-row order.
Men's cleaning tests check reported ages, missing and invalid values, shared
inclusion rules, and compatibility with the women's output columns and types.
Retrieval tests replace HTTP responses with local payloads. They exercise
name lookup, both profile layouts, archive overlap, metadata validation,
request failures, and current men's records containing opponent birth dates.

## Raw match data

The private parser in `src/tennisage/_parsing.py` reads the JSON-compatible
arrays assigned to `morematchmx` or `matchmx`. It does not execute JavaScript.
Each match row retains its original column positions and text values,
including blank optional fields. Rows must contain at least 17 fields;
additional columns are retained.

Opponent information at index 16 is a birth date in the women's sample and
an age in the men's sample. Current men's profile tables can also supply
birth dates in that position. These values remain text during parsing. The
[fixture documentation](tests/fixtures/README.md) describes the shared field
positions and sample sources.

## Clean match data

The private cleaners in `src/tennisage/_cleaning.py` accept parsed records,
a player name, and a player birth date. Both return the same columns and
calculate the player's age from elapsed days divided by 365.25. The women's
cleaner derives opponent ages from birth dates. The men's cleaner uses the
legacy sample's reported opponent ages directly. The retrieval function also
recognizes eight-digit opponent birth dates in current men's records and
derives their ages. Birth dates remain unavailable for reported-age records.
The signed age difference is the player's age minus the opponent's age, so
positive values mean the player is older.

Every valid source row is retained in chronological order. Stand-alone
walkover and default records, and records without an opponent age, are marked
as excluded from plotting with explicit reasons. A missing opponent birth
date does not exclude a men's record when its reported age is available.
Retirements are retained when ages are available. The data are not restricted
to an article publication date. The [data dictionary](docs/data_dictionary.md)
describes all columns, validation rules, and inclusion rules.

## Repository organization

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Package metadata, dependencies, build configuration, and pytest settings. |
| `src/tennisage/` | Importable Python package. |
| `src/tennisage/data.py` | Public career-data retrieval and current/archive assembly. |
| `src/tennisage/_download.py` | HTTP requests, timeouts, and text decoding. |
| `src/tennisage/_players.py` | Player-name lookup, profile URLs, and metadata validation. |
| `src/tennisage/_parsing.py` | Private match-array parser and structural validation. |
| `src/tennisage/_cleaning.py` | Women's and men's career cleaning, age calculations, and inclusion flags. |
| `tests/` | Automated tests. |
| `tests/fixtures/` | Local career samples and their field documentation. |
| `docs/data_dictionary.md` | Cleaned columns, age definitions, and validation rules. |
| `MANIFEST.in` | Include tests, local fixtures, and documentation in the source distribution. |
| `README.md` | Installation, testing, and project documentation. |
| `instructions.md` | Assignment instructions supplied with the repository. |
| `.gitignore` | Exclusions for local environments, caches, and build outputs. |

## References

- [STAT 159 HW3 assignment](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
- [Tennis Abstract](https://www.tennisabstract.com/), by Jeff Sackmann.
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
- [Python JSON decoder documentation](https://docs.python.org/3/library/json.html).
- [pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
- [pytest-socket documentation](https://github.com/miketheman/pytest-socket).
