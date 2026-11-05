# Career match fixtures

These local files contain the three-row examples supplied in the
[STAT 159 HW3 instructions](https://stat159.berkeley.edu/fall-2026/hws/hw03/hw03.html).
Their data values are unchanged; each array declaration ends with a semicolon.
Tests read these files directly and do not download data.

| File | Player | Opponent information at index 16 |
| --- | --- | --- |
| `FemalePlayerCareer.js` | Serena Williams | Birth date as `YYYYMMDD` text. |
| `MalePlayerCareer.js` | Rafael Nadal | Age in years as decimal text. |

The shared fields used for the age comparison have the following zero-based
positions:

| Index | Field |
| --- | --- |
| 0 | Source tournament date, `YYYYMMDD`. |
| 1 | Tournament name. |
| 2 | Surface. |
| 3 | Tournament level code. |
| 4 | Match result, `W` or `L`, from the player's perspective. |
| 8 | Round. |
| 9 | Score. |
| 11 | Opponent name. |
| 16 | Opponent birth date or age, depending on the source format. |

The parser preserves every field and its original position, including blank
optional fields. It accepts different row widths and requires at least 17
fields. Match results come from index 4; the level code at index 3 can also
contain `W` and must not be interpreted as a result.
