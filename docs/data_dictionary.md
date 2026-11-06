# Clean career data

The women's and men's cleaners read parsed match records and accept the
player's name and birth date as arguments. Player birth dates may use
`YYYYMMDD` or `YYYY-MM-DD`. Tournament dates and women's opponent birth dates
use the source's `YYYYMMDD` format. Men's records instead supply numeric
opponent ages. Surrounding whitespace is removed from selected source fields,
and repeated whitespace in the player name is collapsed.

Both cleaners return the same pandas columns and data types, retaining every
valid source row. Rows are sorted by tournament date, with their original order
preserved for tied dates.

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
| `opponent_dob` | Date or `NaT` | Opponent birth date from field 16 in women's records; always `NaT` in men's records. |
| `player_age` | Float | Elapsed days from player birth to tournament date, divided by 365.25. |
| `opponent_age` | Float or `NaN` | Women's age derived from birth date, or men's reported age from field 16. |
| `age_difference` | Float or `NaN` | `player_age - opponent_age`; positive means the player is older. |
| `included_in_plot` | Boolean | Whether the row has the ages and match status needed for plotting. |
| `exclusion_reason` | Text | Empty for included rows; otherwise the reason or reasons described below. |

## Age calculations

Dates are timezone-naive pandas datetime columns. The source's tournament date
is a proxy for the day of a match; multiple rounds may share that date.
The player's age and women's opponent ages use elapsed days divided by 365.25,
including actual leap days in the elapsed-day count. Men's opponent ages are
converted from source strings to floating-point numbers without rounding or
recalculation. Opponent birth dates are not inferred from reported ages.

For women's records, both ages use the same tournament date. For men's records,
the player's age at the tournament date is compared with the opponent's reported
age. A positive difference means the player is older, zero means equal ages,
and a negative difference means the player is younger.

## Inclusion rules

The cleaner applies no article publication date or career-end cutoff.
All valid career records remain in the data frame, including excluded rows.
Consumers should select rows where `included_in_plot` is `True` when plotting.

- Stand-alone scores `W/O`, `WO`, `WALKOVER`, `DEF`, and `DEFAULT` are excluded
  as `walkover_or_default`. Recognition ignores case and whitespace.
- A blank women's opponent birth date produces `NaT` for `opponent_dob` and
  `NaN` for `opponent_age` and `age_difference`. A blank men's reported age
  also produces `NaN` for `opponent_age` and `age_difference`. Either case
  excludes the row as `missing_opponent_age`.
- Men's records with valid reported opponent ages can be included even though
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
tournament, round, and opponent; duplicate combinations raise `ValueError`
instead of silently removing rows. The input record lists are not modified.

## Sources

- [Tennis Abstract](https://www.tennisabstract.com/).
- [STAT 159 HW3 field examples](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
- [Local sample field positions](../tests/fixtures/README.md).
