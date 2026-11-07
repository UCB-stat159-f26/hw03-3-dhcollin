# Clean career data

`get_career_data()` retrieves the player's name, birth date, and match records
from Tennis Abstract. The underlying cleaners also accept parsed records and
player metadata directly. Player birth dates may use `YYYYMMDD` or
`YYYY-MM-DD`; source tournament and opponent birth dates use `YYYYMMDD`.
Legacy men's records supply numeric opponent ages, while current men's
profile tables can supply birth dates. The retrieval function recognizes
eight-digit birth dates and otherwise reads numeric ages for men's records.
Women's records use birth dates. Surrounding whitespace is removed from
selected source fields, and repeated whitespace in the player name is collapsed.

Both cleaners return the same pandas columns and data types, retaining every
valid source row. Rows are sorted by tournament date, with their original order
preserved for tied dates.

| Column | Type | Meaning |
| --- | --- | --- |
| `source_row` | Integer | One-based row position in the parsed or assembled career array before sorting. |
| `player_name` | Text | Player's canonical name from the profile. |
| `player_dob` | Date | Player's date of birth. |
| `tournament_date` | Date | Tournament date from source field 0. |
| `tournament` | Text | Tournament name from field 1. |
| `surface` | Text | Court surface from field 2; may be blank. |
| `level_code` | Text | Tournament classification from field 3; may be blank. |
| `result` | Text | Player's result, `W` or `L`, from field 4. |
| `round` | Text | Match round from field 8. |
| `score` | Text | Score or match-status text from field 9. |
| `opponent` | Text | Opponent's name from field 11. |
| `opponent_dob` | Date or `NaT` | Opponent birth date from field 16 when supplied; `NaT` for reported-age records. |
| `player_age` | Float | Elapsed days from player birth to tournament date, divided by 365.25. |
| `opponent_age` | Float or `NaN` | Age derived from an opponent birth date, or the reported numeric age from field 16. |
| `age_difference` | Float or `NaN` | `player_age - opponent_age`; positive means the player is older. |
| `included_in_plot` | Boolean | Whether the row has the ages and match status needed for plotting. |
| `exclusion_reason` | Text | Empty for included rows; otherwise the reason or reasons described below. |

## Age calculations

Dates are timezone-naive pandas datetime columns. The source's tournament date
is a proxy for the day of a match; multiple rounds may share that date.
The player's age and any opponent ages derived from birth dates use elapsed
days divided by 365.25, including actual leap days in the elapsed-day count.
Reported opponent ages are converted from source strings to floating-point
numbers without rounding or recalculation. Opponent birth dates are not
inferred from reported ages.

When both birth dates are available, both ages use the same tournament date.
Otherwise the player's age at the tournament date is compared with the
opponent's reported age. A positive difference means the player is older,
zero means equal ages, and a negative difference means the player is younger.

## Career assembly

The function uses the profile's embedded singles table when available.
Legacy profiles load a current JavaScript table and, when indicated by their
`careerjs` flag, a separate archive. On overlap, current records replace
archive records with the same date, tournament, round, and opponent.
Retained archive rows precede current rows before chronological sorting and
assignment of the displayed order. `source_row` records the position in that
assembled array before sorting; it is not a line number in a downloaded file.

## Inclusion rules

The cleaner applies no article publication date or career-end cutoff.
All valid career records remain in the data frame, including excluded rows.
Consumers should select rows where `included_in_plot` is `True` when plotting.

- Stand-alone scores `W/O`, `WO`, `WALKOVER`, `DEF`, and `DEFAULT` are excluded
  as `walkover_or_default`. Recognition ignores case and whitespace.
- A blank opponent birth date produces `NaT` for `opponent_dob` and
  `NaN` for `opponent_age` and `age_difference`. A blank men's reported age
  also produces `NaN` for `opponent_age` and `age_difference`. Either case
  excludes the row as `missing_opponent_age`.
- Records with valid reported opponent ages can be included even though
  `opponent_dob` is `NaT`.
- If both conditions apply, the reason is
  `walkover_or_default;missing_opponent_age`.
- Retirements and scores with played sets or games followed by a default
  marker are retained when both ages are available.

## Validation

Malformed nonblank dates, invalid calendar dates, and missing required dates
raise `ValueError`. Reported opponent ages must be numeric or blank; malformed
nonblank values, including text such as `NaN`, raise `ValueError`. Nonfinite
ages, ages below zero, and ages at least 100 years also raise `ValueError`.
Missing opponent birth dates or reported ages are allowed and flagged for
plot exclusion when no age is available. Missing player birth dates and
tournament dates are not allowed.

Results must be `W` or `L`. Tournament, opponent, round, and score fields must
be nonblank. Matches must have unique combinations of tournament date,
tournament, round, and opponent after archive/current overlap is resolved.
Other duplicate combinations raise `ValueError` instead of silently removing
rows. The input record lists are not modified.

## Sources

- [Tennis Abstract](https://www.tennisabstract.com/).
- [STAT 159 HW3 field examples](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
- [Local sample field positions](../tests/fixtures/README.md).
