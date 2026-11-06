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

## Raw match data

The private parser in `src/tennisage/_parsing.py` reads the JSON-compatible
array assigned to `morematchmx`. It does not execute the JavaScript file.
Each match row retains its original column positions and text values,
including blank optional fields. Rows must contain at least 17 fields;
additional columns are retained.

Opponent information at index 16 is a birth date in the women's sample and
an age in the men's sample. Both remain text during parsing. The
[fixture documentation](tests/fixtures/README.md) describes the shared field
positions and sample sources.

## Clean match data

The private cleaners in `src/tennisage/_cleaning.py` accept parsed records,
a player name, and a player birth date. Both return the same columns and
calculate the player's age from elapsed days divided by 365.25. The women's
cleaner derives opponent ages from birth dates. The men's cleaner uses the
reported opponent ages directly and leaves opponent birth dates unavailable.
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
