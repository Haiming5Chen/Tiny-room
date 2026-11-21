# The kit cart's curb height: where it stops clearing (FR-042, ADR 0076)

Run with `python -m little_world.inventory.boundary curb 8 26 2 --samples 8 --seconds 25 --jobs 2` (and `--multiccd`), 15 November 2026, on 9874c9f's code with FR-042's module.

## mobile_platform on the curbs field: curb height

Curb height: 50 % at 14.3 mm, 95 % between 12.5 and 18.1 mm (522 of 2000 resamples did not cross within the grid). From 8.0 to 14.0 mm a higher level did better than a lower one: pooled. From 20.0 to 22.0 mm a higher level did better than a lower one: pooled.

| Curb height, mm | Met every goal | 95 % interval | Fitted |
| --- | --- | --- | --- |
| 8.0 | 2 of 9 | 3 to 60 % | 53 % |
| 10.0 | 5 of 9 | 21 to 86 % | 53 % |
| 12.0 | 6 of 9 | 30 to 93 % | 53 % |
| 14.0 | 6 of 9 | 30 to 93 % | 53 % |
| 16.0 | 3 of 9 | 7 to 70 % | 33 % |
| 18.0 | 3 of 9 | 7 to 70 % | 33 % |
| 20.0 | 0 of 9 | 0 to 34 % | 6 % |
| 22.0 | 1 of 9 | 0 to 48 % | 6 % |
| 24.0 | 0 of 9 | 0 to 34 % | 0 % |
| 26.0 | 0 of 9 | 0 to 34 % | 0 % |

Each level on the same 9 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).

## mobile_platform on the curbs field, multiccd on: curb height

Curb height: below one half over the whole grid, 8.0 to 26.0 mm. From 8.0 to 10.0 mm a higher level did better than a lower one: pooled.

| Curb height, mm | Met every goal | 95 % interval | Fitted |
| --- | --- | --- | --- |
| 8.0 | 0 of 9 | 0 to 34 % | 22 % |
| 10.0 | 4 of 9 | 14 to 79 % | 22 % |
| 12.0 | 1 of 9 | 0 to 48 % | 11 % |
| 14.0 | 0 of 9 | 0 to 34 % | 0 % |
| 16.0 | 0 of 9 | 0 to 34 % | 0 % |
| 18.0 | 0 of 9 | 0 to 34 % | 0 % |
| 20.0 | 0 of 9 | 0 to 34 % | 0 % |
| 22.0 | 0 of 9 | 0 to 34 % | 0 % |
| 24.0 | 0 of 9 | 0 to 34 % | 0 % |
| 26.0 | 0 of 9 | 0 to 34 % | 0 % |

Each level on the same 9 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).
