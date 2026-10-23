Measured for ADR 0051 (what looking again earns) on 2026-10-23: the Fetch field as of ADR 0050, its 9 set-ups (seed 1: the design as designed and 8 drawn), undisturbed and under four of its disturbances, with the program's own recovery (ADR 0048's disturbed sweep, `docs/sweeps/2026-10-22-fetch-feel-disturbed-9.md`) and with each baseline (`sweep --disturb --recovery retreat|guess|none`).

# fetch: does looking again earn its complexity?

Each disturbance tried on the same set-ups with the program's own recovery - looking again and reaching where it now sees the object (ADR 0033) - and with each baseline (FR-023). Every goal met, per set-up; a pair whose outcomes differ was changed by the recovery alone (exact McNemar, ADR 0036).

## Against "retreat": reached again where it had seen the object

| Disturbance | Looking again | Retreat | Rescued by looking again, beyond it | The other way | p |
| --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 0 | 0 | - |
| shoved 6 N s at the table | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways, 2 s later | 9 of 9 | 0 of 9 | 9 | 0 | 0.0039 |
| camera frozen as the cube is moved 5 cm | 0 of 9 | 0 of 9 | 0 | 0 | - |

## Against "guess": looked again and reached as far off in a random direction

| Disturbance | Looking again | Guess | Rescued by looking again, beyond it | The other way | p |
| --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 0 | 0 | - |
| shoved 6 N s at the table | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways, 2 s later | 9 of 9 | 0 of 9 | 9 | 0 | 0.0039 |
| camera frozen as the cube is moved 5 cm | 0 of 9 | 0 of 9 | 0 | 0 | - |

## Against "none": stopped

| Disturbance | Looking again | None | Rescued by looking again, beyond it | The other way | p |
| --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 0 | 0 | - |
| shoved 6 N s at the table | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways | 9 of 9 | 9 of 9 | 0 | 0 | - |
| cube moved 5 cm sideways, 2 s later | 9 of 9 | 0 of 9 | 9 | 0 | 0.0039 |
| camera frozen as the cube is moved 5 cm | 0 of 9 | 0 of 9 | 0 | 0 | - |

## How each baseline ended where it failed

- retreat, cube moved 5 cm sideways, 2 s later: 9 "Timed out: pose did not settle".
- retreat, camera frozen as the cube is moved 5 cm: 9 "Looked for fetch_cube: the camera's picture is not new".
- guess, cube moved 5 cm sideways, 2 s later: 5 "Nothing held: the grasp missed"; 2 "Timed out: pose did not settle"; 2 "Seen 5 cm from where it was planned: out of the arm's reach from this stop".
- guess, camera frozen as the cube is moved 5 cm: 9 "Looked for fetch_cube: the camera's picture is not new".
- none, cube moved 5 cm sideways, 2 s later: 9 "Timed out: pose did not settle".
- none, camera frozen as the cube is moved 5 cm: 9 "Looked for fetch_cube: the camera's picture is not new".
