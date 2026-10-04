# Fetch, disturbed: arm on a cart

Each disturbance tried on the same 9 set-ups - the design as designed and 8 drawn at random within the ranges of ADR 0024 - running the field's program, solved once for the design on its mark. The program ran without its looks (`--blind`, ADR 0032).

| Disturbance | Every goal met | Drawn at random | Last goal, median change | Pushed | Went back | Missed in |
| --- | --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 8 of 8, at least 69 % | - | - | - | - |
| shoved 4 N s at the table | 8 of 9 | 7 of 8, at least 53 % | +5.0 s | 1.7 cm (0.9 to 3.8) | 5 | repeat 6 |
| shoved 6 N s at the table | 8 of 9 | 7 of 8, at least 53 % | +10.1 s | 6.3 cm (3.7 to 11.8) | 9 | repeat 7 |
| cube moved 3 cm sideways | 7 of 9 | 6 of 8, at least 40 % | +0.0 s | - | - | repeat 1, repeat 7 |
| cube moved 5 cm sideways | 0 of 9 | 0 of 8, at least 0 % | - | - | - | every set-up |
| cube moved 5 cm sideways, 2 s later | 0 of 9 | 0 of 8, at least 0 % | - | - | - | every set-up |

What each disturbance does:

- **shoved 4 N s at the table**: 4 N s over 0.1 s, 90 deg left of its heading, after "reached", once still for 0.2 s, 0.1 s later.
- **shoved 6 N s at the table**: 6 N s over 0.1 s, 90 deg left of its heading, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 3 cm sideways**: fetch_cube moved +0.0 cm, +3.0 cm, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 5 cm sideways**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 0.1 s later.
- **cube moved 5 cm sideways, 2 s later**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 2.1 s later.

A run counts when it meets every goal (reached the table, cube lifted 5 cm, cube resting in the bin, stayed upright). "Last goal, median change" compares each set-up with itself undisturbed. "Pushed" is how far the machine's base went the way it was pushed, a second after the push; "Went back", in how many set-ups the program drove back to a stop it had been pushed off (ADR 0031). The rate is over the set-ups drawn at random (ADR 0028); the design as designed is a chosen run.
