# Fetch, disturbed: arm on a cart

Each disturbance tried on the same 9 set-ups - the design as designed and 8 drawn at random within the ranges of ADR 0024 - running the field's program, solved once for the design on its mark. The program took every picture as new and lit (`--unchecked-camera`, ADR 0038).

| Disturbance | Every goal met | Drawn at random | Broken by it | Last goal, median change | Pushed | Went back | Looked again | Camera saw it moved | Missed in |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 9 of 9 | 8 of 8, at least 69 % | - | - | - | - | - | 0.1 cm (0.1 to 0.1) | - |
| camera frozen as the cube is moved 5 cm | 0 of 9 | 0 of 8, at least 0 % | 8 of 8, at least 69 %; p = 0.0078 | - | - | - | 9 | 0.1 cm (0.1 to 0.2) | every set-up: "Timed out: pose did not settle" |
| camera dark at the table | 0 of 9 | 0 of 8, at least 0 % | 8 of 8, at least 69 %; p = 0.0078 | - | - | - | - | 0.1 cm (0.1 to 0.1) | every set-up: "Looked for fetch_cube: it would not keep still" |

What each disturbance does:

- **camera frozen as the cube is moved 5 cm**: fetch_cube moved +0.0 cm, +5.0 cm, after "reached", once still for 0.2 s, 0.1 s later; the camera frozen on its last picture just before.
- **camera dark at the table**: the camera dark, after "reached", once still for 0.2 s, 0.1 s later.

A run counts when it meets every goal (reached the table, cube lifted 5 cm, cube resting in the bin, stayed upright). "Last goal, median change" compares each set-up with itself undisturbed. "Pushed" is how far the machine's base went the way it was pushed, a second after the push; "Went back", in how many set-ups the program drove back to a stop it had been pushed off (ADR 0031). "Broken by it" pairs each drawn set-up with itself undisturbed - the two are one run until the event, step for step (ADR 0036) - and counts those that met every goal undisturbed and missed one with it, with the share of successes it breaks (95 % confidence); "rescued" counts the set-ups it turned the other way, and p is the exact McNemar test on the set-ups whose outcomes differ. "Looked again", in how many the program, its grasp missed, opened its jaws, looked and reached again (ADR 0033). "Camera saw it moved" is how far from where it was planned the table camera last saw the cube (ADR 0032); every sighting was within 101.7 mm of where the cube really was. The rate is over the set-ups drawn at random (ADR 0028); the design as designed is a chosen run.
