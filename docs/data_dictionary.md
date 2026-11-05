# Clean career data

The women's cleaner reads parsed match records and accepts the player's name
and birth date as arguments. Player birth dates may use `YYYYMMDD` or
`YYYY-MM-DD`. Tournament dates and opponent birth dates use the source's
`YYYYMMDD` format. Surrounding whitespace is removed from selected source
fields, and repeated whitespace in the player name is collapsed.

The returned pandas data frame retains every valid source row. Rows are sorted
by tournament date, with their original order preserved for tied dates.

| Column | Type | Meaning |
| --- | --- | --- |
| `source_row` | Integer | One-based row position in the parsed career array. |
| `player_name` | Text | Name supplied for the player. |
| `player_dob` | Date | Player's supplied date of birth. |
| `tournament_date` | Date | Tournament date from source field 0. |
| `tournament` | Text | Tournament name from field 1. |
| `surface` | Text | Court surface from field 2; may be blank. |
| `level_code` | Text | Tournament classification from field 3; may be blank. |
| `result` | Text | Player's result, `W` or `L`, from field 4. |
| `round` | Text | Match round from field 8. |
| `score` | Text | Score or match-status text from field 9. |
| `opponent` | Text | Opponent's name from field 11. |
| `opponent_dob` | Date or `NaT` | Opponent birth date from field 16 in women's records. |
| `player_age` | Float | Elapsed days from player birth to tournament date, divided by 365.25. |
| `opponent_age` | Float or `NaN` | Elapsed days from opponent birth to tournament date, divided by 365.25. |
| `age_difference` | Float or `NaN` | `player_age - opponent_age`; positive means the player is older. |
| `included_in_plot` | Boolean | Whether the row has the ages and match status needed for plotting. |
| `exclusion_reason` | Text | Empty for included rows; otherwise the reason or reasons described below. |

## Age calculations

Dates are timezone-naive pandas datetime columns. The source's tournament date
is a proxy for the day of a match; multiple rounds may share that date.
Fractional ages use elapsed days divided by 365.25, including actual leap days
in the elapsed-day count. Ages are not rounded to whole years.

The age difference uses the same tournament date for both players. A positive
value means the player is older than the opponent, zero means equal ages, and
a negative value means the player is younger.

## Inclusion rules

The cleaner applies no article publication date or career-end cutoff.
All valid career records remain in the data frame, including excluded rows.
Consumers should select rows where `included_in_plot` is `True` when plotting.

- Stand-alone scores `W/O`, `WO`, `WALKOVER`, `DEF`, and `DEFAULT` are excluded
  as `walkover_or_default`. Recognition ignores case and whitespace.
- A blank opponent birth date produces `NaT` for `opponent_dob` and `NaN` for
  `opponent_age` and `age_difference`. The row is excluded as
  `missing_opponent_age`.
- If both conditions apply, the reason is
  `walkover_or_default;missing_opponent_age`.
- Retirements and scores with played sets or games followed by a default
  marker are retained when both ages are available.

## Validation

Malformed nonblank dates, invalid calendar dates, and missing required dates
raise `ValueError`. Ages below zero or at least 100 years also raise
`ValueError`. A missing opponent birth date is allowed; a missing player
birth date or tournament date is not.

Results must be `W` or `L`. Tournament, opponent, round, and score fields must
be nonblank. Matches must have unique combinations of tournament date,
tournament, round, and opponent; duplicate combinations raise `ValueError`
instead of silently removing rows. The input record lists are not modified.

## Sources

- [Tennis Abstract](https://www.tennisabstract.com/).
- [STAT 159 HW3 field examples](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
- [Local sample field positions](../tests/fixtures/README.md).
