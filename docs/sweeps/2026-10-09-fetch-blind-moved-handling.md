# Fetch, disturbed: arm on a cart

Each disturbance tried on the same 9 set-ups - the design as designed and 8 drawn at random within the ranges of ADR 0024 - running the field's program, solved once for the design on its mark. The program ran without its looks (`--blind`, ADR 0032).

| Disturbance | Every goal met | Drawn at random | Broken by it | Last goal, median change | Pushed | Went back | Missed in |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 8 of 8, at least 69 % | - | - | - | - | - |
| cube moved 5 cm sideways | 0 of 9 | 0 of 8, at least 0 % | 8 of 8, at least 69 %; p = 0.0078 | - | - | - | every set-up: "Nothing held: the grasp missed" |

How fetch_cube was handled (ADR 0040), the median over the set-ups and, in brackets, the most: the force on it from the machine and from anything else, averaged over 50 ms; how far it leaned; how far it fell when the machine let go.

| Disturbance | From the machine | From anything else | Leaned | Fell when let go |
| --- | --- | --- | --- | --- |
| none | 4.84 N (5.02) | 0.56 N (0.57) | 9 deg (16) | 5.4 cm |
| cube moved 5 cm sideways | 4.96 N (5.18) | 5.12 N (5.34) | 13 deg (97) | 0.0 cm |

What each disturbance does:

- **cube moved 5 cm sideways**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 0.1 s later.

A run counts when it meets every goal (reached the table, cube lifted 5 cm, cube resting in the bin, stayed upright). "Last goal, median change" compares each set-up with itself undisturbed. "Pushed" is how far the machine's base went the way it was pushed, a second after the push; "Went back", in how many set-ups the program drove back to a stop it had been pushed off (ADR 0031). "Broken by it" pairs each drawn set-up with itself undisturbed - the two are one run until the event, step for step (ADR 0036) - and counts those that met every goal undisturbed and missed one with it, with the share of successes it breaks (95 % confidence); "rescued" counts the set-ups it turned the other way, and p is the exact McNemar test on the set-ups whose outcomes differ. The rate is over the set-ups drawn at random (ADR 0028); the design as designed is a chosen run.
