# tennisage

**David H. Collin | STAT 159 | UC Berkeley | Fall 2026**

`tennisage` is the Python package for the STAT 159 tennis career analysis.
The analysis compares a player's age with the difference between that player's
age and their opponent's age, using match records from
[Tennis Abstract](https://www.tennisabstract.com/).

The package exposes two public functions:

| Function | Input | Output |
| --- | --- | --- |
| `get_career_data(player_name, *, timeout=20.0)` | A player name and an optional request timeout. | A cleaned pandas data frame containing the available career records. |
| `plot_age_difference(matches, *, ax=None)` | The cleaned data frame and an optional Matplotlib axes. | A Matplotlib axes containing the age-difference scatter plot. |

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

## Plot age differences

```python
import matplotlib.pyplot as plt
from tennisage import get_career_data, plot_age_difference

serena = get_career_data("serena williams")
ax = plot_age_difference(serena)
ax.figure.savefig("serena_age_difference.png", dpi=300, bbox_inches="tight")
plt.show()

rafa = get_career_data("Rafael Nadal")
plot_age_difference(rafa)
plt.show()
```

`plot_age_difference(matches, *, ax=None)` returns a Matplotlib `Axes`.
It plots only rows marked `included_in_plot=True`, with player age on the
horizontal axis and player age minus opponent age on the vertical axis.
Positive differences mean the player was older; negative differences mean
the opponent was older. Wins are cyan and losses are purple. The gray line
marks equal ages. Axis limits adapt to the eligible matches, and individual
matches are not annotated.

The function works offline with an already retrieved data frame. It does not
change that frame or automatically display or save a figure. Pass an existing
ordinary Matplotlib axes through `ax` to use a subplot; the function adds
points, sets labels and limits, and returns that same axes:

```python
fig, ax = plt.subplots(figsize=(11, 7), layout="constrained")
plot_age_difference(serena, ax=ax)
```

The required columns are `player_name`, `player_age`, `age_difference`,
`result`, and `included_in_plot`. Inclusion flags must be boolean and complete.
Eligible rows must describe one named player, have a `W` or `L` result, and
contain finite real numeric coordinates with nonnegative player ages.
Missing ages on excluded rows are allowed. An empty selection or invalid data
raises `ValueError`; a non-data-frame input or an invalid axes type raises
`TypeError`. Polar and three-dimensional axes are not supported.

## Example notebook

[Career examples](examples/career_examples.ipynb) demonstrates retrieval and
plotting for Serena Williams and Rafael Nadal, summarizes retained and excluded
matches, and displays the error for an unknown player. The notebook includes
executed outputs and records the retrieval time and package versions.

To open it locally, run these commands from the repository's top-level directory
with the virtual environment activated:

```bash
python -m pip install -e ".[dev,notebook]"
python -m jupyter lab examples/career_examples.ipynb
```

Select the Python kernel from this environment, then restart the kernel and
run all cells. The notebook may run with its working directory set to either
the repository root or `examples/`. It imports the installed package without
changing Python's module search path.

Running the notebook downloads current records from Tennis Abstract and
overwrites these figures:

- [Serena Williams age differences](examples/figures/serena_age_difference.png).
- [Rafael Nadal age differences](examples/figures/rafael_age_difference.png).

Viewing the saved outputs requires no download. Rerunning the retrieval cells
requires internet access, and upstream changes may alter the match counts and
figures. To refresh the notebook from the terminal:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace examples/career_examples.ipynb --ExecutePreprocessor.timeout=180
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
Plotting tests use a noninteractive backend and local data to check coordinates,
win/loss colors, inclusion flags, adaptive limits, axes reuse, input validation,
unchanged input data, and PNG/PDF output.
Public-workflow tests pass retrieved data directly to the plotting function
for both tours, including excluded rows and successive calls for different
players. These tests use local HTTP responses. The notebook is a live-data
example and is not executed by pytest.

## Build the package

With the `dev` dependencies installed, create a source distribution and wheel:

```bash
python -m build
```

The files are written to `dist/`. The wheel contains the importable package;
the source distribution also includes the tests, local fixtures, data dictionary,
example notebook, and saved figures. These build outputs are excluded from Git.
The package uses the `src/` layout so that tests and examples exercise an
installed package instead of depending on imports from the current directory.

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

## Scope and limitations

- Career coverage depends on the records available from Tennis Abstract.
  The package combines the required current and archive tables, but cannot
  establish whether the upstream database contains every historical match.
- Retrieval depends on Tennis Abstract's player index, profile metadata, and
  JavaScript table structure. A website redesign, unavailable file, or malformed
  required record can prevent retrieval. Local tests check the supported formats;
  they do not establish the current availability of the website.
- Ages calculated from birth dates use the source tournament date, which may
  differ from the date of an individual round. Dividing elapsed days by 365.25
  gives an approximate age in years. Legacy reported opponent ages retain the
  source's precision and may use a different dating convention.
- Exclusion rules recognize the documented stand-alone walkover and default
  markers. Other score text is not a complete classification of match status.
  Missing opponent ages remain visible in the returned data through explicit
  flags and reasons.
- Repeating a download can produce different records after an upstream update.
  The notebook preserves example outputs and retrieval metadata, but the package
  does not save a permanent raw-data snapshot. To reproduce a particular analysis
  exactly, retain its raw inputs and record the dependency versions as well.
- The figure describes age differences and observed match outcomes. It does
  not estimate a causal effect of age or adjust for opponent strength, tournament
  selection, or other differences across a player's career.

## Repository organization

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Package metadata, dependencies, build configuration, and pytest settings. |
| `src/tennisage/` | Importable Python package. |
| `src/tennisage/data.py` | Public career-data retrieval and current/archive assembly. |
| `src/tennisage/plotting.py` | Public age-difference scatter plot and input validation. |
| `src/tennisage/_download.py` | HTTP requests, timeouts, and text decoding. |
| `src/tennisage/_players.py` | Player-name lookup, profile URLs, and metadata validation. |
| `src/tennisage/_parsing.py` | Private match-array parser and structural validation. |
| `src/tennisage/_cleaning.py` | Women's and men's career cleaning, age calculations, and inclusion flags. |
| `tests/` | Automated tests. |
| `tests/fixtures/` | Local career samples and their field documentation. |
| `examples/career_examples.ipynb` | Executed examples of both public functions and the invalid-name error. |
| `examples/figures/` | PNG plots saved by the example notebook. |
| `docs/data_dictionary.md` | Cleaned columns, age definitions, and validation rules. |
| `MANIFEST.in` | Include tests, fixtures, documentation, and examples in the source distribution. |
| `README.md` | Installation, testing, and project documentation. |
| `instructions.md` | Assignment instructions supplied with the repository. |
| `.gitignore` | Exclusions for local environments, caches, and build outputs. |

## Personal reflection

Turning the HW2 analysis into `tennisage` helped me understand the difference
between completing one analysis and designing code that someone else can reuse.
For a plot centered on Serena Williams, the player's identity and the structure
of her data could remain implicit. A package has to make those assumptions
explicit. It needs to accept different spellings of a name, retrieve the correct
career, return a consistent data frame, and explain why a request fails. Keeping
retrieval and plotting as separate public functions also makes the cleaned data
available for inspection before any points appear on a figure.

The most instructive data issue was the difference between the women's and
men's records. The same field position can contain an opponent's birth date or
a reported age. Treating both as ordinary numbers would produce incorrect
comparisons even if the program ran without an exception. The cleaning logic
therefore has to interpret the field before calculating an age difference.
Handling birth dates in current men's records also showed me why examples are
useful starting points but should not be mistaken for a complete description
of a changing data source. The shared output columns let the plotting function
work without needing to know which representation appeared upstream.

This assignment also made data inclusion a more deliberate part of my workflow.
Walkovers, defaults, and missing opponent ages require decisions about what a
point represents. Retaining those records with an inclusion flag and an
explanation makes the decisions inspectable. I can compare the number of
retrieved records with the number plotted instead of assuming that every
downloaded row should appear. Documenting the tournament-date convention and
the sign of the age difference serves a similar purpose: it makes the meaning
of the coordinates explicit, rather than leaving a reader to infer it from
the picture.

Offline testing changed how I thought about evidence that the package works.
A successful download shows that a request worked at that moment, but it does
not isolate whether the cleaning rules are correct. Small local examples make
it possible to check known ages, missing values, duplicate matches, and invalid
inputs against specific expectations. Mocked responses extend those checks to
name lookup and career assembly while keeping network availability out of the
test results. Passing the retrieved frames directly into the plotting function
then checks that the pieces agree on their shared data format. The live notebook
and the automated suite serve different purposes, and both are useful.

Keeping functions short encouraged me to separate parsing, validation, cleaning,
retrieval, and plotting into named operations. That separation makes failures
easier to locate, although too many small helpers can make the overall flow
harder to follow. Clear names and a small public interface help balance those
concerns. The sequence of contributions also reinforced the value of finishing
one coherent change at a time, with tests and documentation tied to the behavior
being added. This gives each step a purpose that is easier to review and explain.

Finally, I learned to distinguish repeatable processing from a frozen data
source. The package can apply the same rules again, but a later download may
contain different records. Recording versions and retrieval times helps explain
the saved examples; preserving the raw inputs would be the next improvement
for reproducing an exact historical result. I would also expand the fixtures
when new source formats appear and check installation across the supported
Python and dependency versions. Overall, the assignment connected reproducibility
to practical design decisions: a documented interface, explicit data conventions,
meaningful errors, and tests that check more than whether a plot is produced.

## References

- [STAT 159 HW3 assignment](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
- [Tennis Abstract](https://www.tennisabstract.com/), by Jeff Sackmann.
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
- [Python JSON decoder documentation](https://docs.python.org/3/library/json.html).
- [pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
- [pytest-socket documentation](https://github.com/miketheman/pytest-socket).
