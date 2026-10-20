# Fetch, disturbed: arm on a cart

Each disturbance tried on the same 9 set-ups - the design as designed and 8 drawn at random within the ranges of ADR 0024 - running the field's program, solved once for the design on its mark.

| Disturbance | Every goal met | Drawn at random | Broken by it | Last goal, median change | Pushed | Went back | Looked again | Camera saw it moved | Missed in |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 8 of 8, at least 69 % | - | - | - | - | - | 0.1 cm (0.1 to 0.1) | - |
| shoved 4 N s at the table | 9 of 9 | 8 of 8, at least 69 % | 0 of 8, at most 31 % | +1.1 s | 1.6 cm (1.0 to 3.3) | 2 | - | 0.1 cm (0.1 to 0.1) | - |
| shoved 6 N s at the table | 9 of 9 | 8 of 8, at least 69 % | 0 of 8, at most 31 % | +11.1 s | 5.7 cm (3.6 to 11.1) | 9 | - | 0.1 cm (0.1 to 0.1) | - |
| cube moved 3 cm sideways | 9 of 9 | 8 of 8, at least 69 % | 0 of 8, at most 31 % | -1.3 s | - | - | - | 3.0 cm (3.0 to 3.0) | - |
| cube moved 5 cm sideways | 9 of 9 | 8 of 8, at least 69 % | 0 of 8, at most 31 % | -1.6 s | - | - | - | 5.0 cm (5.0 to 5.0) | - |
| cube moved 5 cm sideways, 2 s later | 9 of 9 | 8 of 8, at least 69 % | 0 of 8, at most 31 % | +6.3 s | - | - | 9 | 5.0 cm (4.9 to 5.1) | - |
| camera frozen as the cube is moved 5 cm | 0 of 9 | 0 of 8, at least 0 % | 8 of 8, at least 69 %; p = 0.0078 | - | - | - | - | 0.1 cm (0.1 to 0.1) | every set-up: "Looked for fetch_cube: the camera's picture is not new" |
| camera dark at the table | 0 of 9 | 0 of 8, at least 0 % | 8 of 8, at least 69 %; p = 0.0078 | - | - | - | - | 0.1 cm (0.1 to 0.1) | every set-up: "Looked for fetch_cube: the camera's picture has no depth" |

How fetch_cube was handled (ADR 0040), the median over the set-ups and, in brackets, the most: the force on it from the machine and from anything else, averaged over 50 ms; how far it leaned, before it was held and as it came to rest; how far it fell when the machine let go.

| Disturbance | From the machine | From anything else | Leaned | Before it was held | At rest | Fell when let go |
| --- | --- | --- | --- | --- | --- | --- |
| none | 3.95 N (4.81) | 0.26 N (0.29) | 26 deg (27) | 0 deg (0) | 0 deg (0) | 0.5 cm |
| shoved 4 N s at the table | 3.39 N (4.14) | 0.26 N (0.27) | 27 deg (28) | 0 deg (0) | 0 deg (0) | 0.2 cm |
| shoved 6 N s at the table | 3.60 N (4.08) | 0.26 N (0.27) | 27 deg (27) | 0 deg (0) | 0 deg (0) | 0.3 cm |
| cube moved 3 cm sideways | 3.91 N (4.52) | 0.29 N (0.30) | 26 deg (27) | 0 deg (0) | 0 deg (0) | 0.8 cm |
| cube moved 5 cm sideways | 4.30 N (5.10) | 0.28 N (0.29) | 26 deg (27) | 0 deg (0) | 0 deg (0) | 0.7 cm |
| cube moved 5 cm sideways, 2 s later | 3.97 N (4.99) | 3.28 N (3.33) | 26 deg (27) | 4 deg (5) | 0 deg (0) | 0.5 cm |
| camera frozen as the cube is moved 5 cm | 0.00 N (0.00) | 0.16 N (0.16) | 0 deg (0) | 0 deg (0) | 0 deg (0) | - |
| camera dark at the table | 0.00 N (0.00) | 0.16 N (0.16) | 0 deg (0) | 0 deg (0) | 0 deg (0) | - |

What each disturbance does:

- **shoved 4 N s at the table**: 4 N s over 0.1 s, 90 deg left of its heading, after "reached", once still for 0.2 s, 0.1 s later.
- **shoved 6 N s at the table**: 6 N s over 0.1 s, 90 deg left of its heading, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 3 cm sideways**: fetch_cube moved +0.0 cm, +3.0 cm, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 5 cm sideways**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 5 cm sideways, 2 s later**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 2.1 s later.
- **camera frozen as the cube is moved 5 cm**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 0.1 s later; the camera frozen on its last picture just before.
- **camera dark at the table**: the camera dark, after "reached", once still for 0.2 s, 0.1 s later.

A run counts when it meets every goal (reached the table, cube lifted 5 cm, cube resting in the bin, stayed upright). "Last goal, median change" compares each set-up with itself undisturbed. "Pushed" is how far the machine's base went the way it was pushed, a second after the push; "Went back", in how many set-ups the program drove back to a stop it had been pushed off (ADR 0031). "Broken by it" pairs each drawn set-up with itself undisturbed - the two are one run until the event, step for step (ADR 0036) - and counts those that met every goal undisturbed and missed one with it, with the share of successes it breaks (95 % confidence); "rescued" counts the set-ups it turned the other way, and p is the exact McNemar test on the set-ups whose outcomes differ. "Looked again", in how many the program, its grasp missed, opened its jaws, looked and reached again (ADR 0033). "Camera saw it moved" is how far from where it was planned the table camera last saw the cube (ADR 0032); every sighting was within 2.6 mm of where the cube really was. The rate is over the set-ups drawn at random (ADR 0028); the design as designed is a chosen run.
