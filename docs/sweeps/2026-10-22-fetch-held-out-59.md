Measured for ADR 0049 (tuning draws and held-out draws) on 2026-10-22: the Fetch field as of ADR 0048, 59 set-ups drawn with seed 20261022 - entered in `docs/sweeps/seeds.jsonl` before the sweep ran - read beside the same design's sweep on seed 1 (`docs/sweeps/2026-10-22-fetch-feel-71.md`), on which ADR 0041, 0042 and 0048 were tuned and judged.

# fetch: tuning draws and held-out draws

Tuning: 59 set-ups drawn with seed 1; held out: 59 drawn with seed 20261022. Design: arm on a cart. Rates with their two-sided 95 % Clopper-Pearson intervals (ADR 0028); handling over the drawn runs, median and range (ADR 0040).

| Goal | Tuning | Held out |
| --- | --- | --- |
| every goal | 59 of 59 (94-100 %) | 59 of 59 (94-100 %) |
| Reached the table | 59 of 59 (94-100 %) | 59 of 59 (94-100 %) |
| Cube lifted 5 cm | 59 of 59 (94-100 %) | 59 of 59 (94-100 %) |
| Cube resting in the bin | 59 of 59 (94-100 %) | 59 of 59 (94-100 %) |
| Stayed upright | 59 of 59 (94-100 %) | 59 of 59 (94-100 %) |

| Part | Measure | Tuning: median (least - most) | Held out | |
| --- | --- | --- | --- | --- |
| fetch_cube | force from the machine, in a step | 4.02 N (3.47 N - 5.13 N) | 4.05 N (3.58 N - 5.07 N) | within |
| fetch_cube | force from the machine, over 50 ms | 3.66 N (3.22 N - 5.00 N) | 3.71 N (3.22 N - 4.97 N) | within |
| fetch_cube | force from the bin, in a step | 0.51 N (0.45 N - 0.83 N) | 0.54 N (0.44 N - 0.77 N) | outside |
| fetch_cube | force from the bin, over 50 ms | 0.26 N (0.23 N - 0.30 N) | 0.26 N (0.24 N - 0.30 N) | within |
| fetch_cube | force from the table, in a step | 0.43 N (0.22 N - 0.62 N) | 0.46 N (0.24 N - 0.77 N) | outside |
| fetch_cube | force from the table, over 50 ms | 0.19 N (0.17 N - 0.23 N) | 0.18 N (0.17 N - 0.23 N) | within |
| fetch_cube | leaned from how it stood | 26.6 deg (26.2 deg - 27.5 deg) | 26.5 deg (26.0 deg - 27.5 deg) | outside |
| fetch_cube | leaned before it was held | 0.0 deg (0.0 deg - 0.1 deg) | 0.0 deg (0.0 deg - 0.1 deg) | within |
| fetch_cube | leaning when it came to rest | 0.0 deg (0.0 deg - 0.0 deg) | 0.0 deg (0.0 deg - 0.0 deg) | within |
| fetch_cube | fell when let go | 0.4 cm (0.1 cm - 1.1 cm) | 0.4 cm (0.2 cm - 0.9 cm) | within |

Outside the tuning range - reported as found, not tuned away:
- fetch_cube, force from the bin, in a step: least 0.44 N under the tuning's least, 0.45 N.
- fetch_cube, force from the table, in a step: most 0.77 N over the tuning's most, 0.62 N.
- fetch_cube, leaned from how it stood: least 26.0 deg under the tuning's least, 26.2 deg.

## The held-out sweep: Fetch, varied: arm on a cart

71 runs, running the field's program, solved once for the design on its mark. Set-ups drawn with seed 20261022.
Payload site: (-0.105, -0.000) m in plan, a steel block of the payload's mass.

| Goal | Met | Drawn at random | Times (fastest / median / slowest) | Not met in |
| --- | --- | --- | --- | --- |
| Reached the table | 71 of 71 | 59 of 59, at least 95 % | 10.3 s / 10.5 s / 10.7 s | - |
| Cube lifted 5 cm | 71 of 71 | 59 of 59, at least 95 % | 19.2 s / 19.5 s / 19.9 s | - |
| Cube resting in the bin | 71 of 71 | 59 of 59, at least 95 % | 36.9 s / 37.4 s / 38.1 s | - |
| Stayed upright | 71 of 71 | 59 of 59, at least 95 % | - | - |

The program looked for its object with the field's camera (ADR 0032) in 71 runs and saw it 1.0 mm from where it was planned (median; 0.7 to 1.9 mm), each time within 1.9 mm of where it really was.

How sure: the 59 runs drawn at random within the ranges are the sample. Every goal was met in 59 of them, so at least 95 % of runs set up at random within these ranges would meet every goal (95 % confidence, one-sided, Clopper-Pearson). The other 12 runs were chosen, not drawn - the design as designed and each variation alone at either end of its range: they check the corners and measure no rate. To show failures below 5 % at 95 % takes 59 drawn runs without one (`--samples 59`).

How fetch_cube was handled, over 71 runs (ADR 0040): the force on it from each thing that touched it, largest in any one step and averaged over 50 ms; how far it leaned, before it was held and as it came to rest; how far it fell when the machine let go.

| | Median | Least | Most |
| --- | --- | --- | --- |
| force from the machine, in a step | 4.01 N | 3.58 N | 5.07 N |
| force from the machine, over 50 ms | 3.69 N | 3.22 N | 4.97 N |
| force from the bin, in a step | 0.54 N | 0.44 N | 0.77 N |
| force from the bin, over 50 ms | 0.26 N | 0.24 N | 0.30 N |
| force from the table, in a step | 0.47 N | 0.24 N | 0.77 N |
| force from the table, over 50 ms | 0.18 N | 0.17 N | 0.23 N |
| leaned from how it stood | 26.5 deg | 26.0 deg | 27.5 deg |
| leaned before it was held | 0.0 deg | 0.0 deg | 0.1 deg |
| leaning when it came to rest | 0.0 deg | 0.0 deg | 0.0 deg |
| fell when let go | 0.4 cm | 0.2 cm | 0.9 cm |

The program felt its grasps with its jaw servos - where each jaw stopped against where it was sent, how fast it moved and the current it drew (ADR 0048) - at 71 grasp checks in 71 runs: it felt a hold where the contacts showed one 71 times; it was never wrong.

## Each run

| Variation | Goals | Changed from as designed |
| --- | --- | --- |
| as designed | 4 of 4 |  |
| set down 2 cm ahead | 4 of 4 |  |
| set down 2 cm behind | 4 of 4 |  |
| set down 2 cm to the left | 4 of 4 |  |
| set down 2 cm to the right | 4 of 4 |  |
| turned 3 deg left | 4 of 4 |  |
| turned 3 deg right | 4 of 4 |  |
| carrying 0.5 kg | 4 of 4 | cube resting in the bin +0.8 s |
| carrying 0.5 kg, 5 cm left | 4 of 4 | cube resting in the bin +0.9 s |
| carrying 0.5 kg, 5 cm right | 4 of 4 | cube resting in the bin +1.1 s |
| friction at its low end | 4 of 4 |  |
| friction at its high end | 4 of 4 |  |
| repeat 1: x +0.7 cm, y +0.3 cm, turned +2.1 deg, 0.02 kg 3 cm left, friction -0.54 | 4 of 4 |  |
| repeat 2: x -2.0 cm, y +1.3 cm, turned -2.2 deg, 0.10 kg 2 cm right, friction +0.40 | 4 of 4 |  |
| repeat 3: x +0.6 cm, y -1.6 cm, turned -1.8 deg, 0.08 kg 4 cm right, friction +0.18 | 4 of 4 |  |
| repeat 4: x -2.0 cm, y -1.5 cm, turned -2.2 deg, 0.17 kg 4 cm right, friction +0.67 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 5: x -1.4 cm, y -0.2 cm, turned +2.5 deg, 0.28 kg, friction +0.03 | 4 of 4 | cube resting in the bin +1.1 s |
| repeat 6: x -1.6 cm, y -1.3 cm, turned +0.7 deg, 0.21 kg 4 cm right, friction -0.09 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 7: x +1.1 cm, y -1.8 cm, turned +2.1 deg, 0.46 kg 3 cm right, friction -0.88 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 8: x -1.7 cm, y -1.6 cm, turned +0.0 deg, 0.00 kg 4 cm right, friction -0.56 | 4 of 4 |  |
| repeat 9: x +2.0 cm, y -0.1 cm, turned -2.6 deg, 0.27 kg 3 cm left, friction -0.27 | 4 of 4 |  |
| repeat 10: x +1.1 cm, y +0.4 cm, turned +2.9 deg, 0.00 kg, friction -0.52 | 4 of 4 |  |
| repeat 11: x -1.9 cm, y +0.8 cm, turned -1.2 deg, 0.26 kg 2 cm left, friction +0.33 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 12: x +0.9 cm, y +1.4 cm, turned -0.2 deg, 0.42 kg 4 cm right, friction +0.80 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 13: x +0.3 cm, y -1.8 cm, turned -2.7 deg, 0.25 kg 5 cm right, friction +0.03 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 14: x -0.3 cm, y -0.2 cm, turned -1.0 deg, 0.10 kg 5 cm left, friction +0.28 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 15: x +0.4 cm, y +1.6 cm, turned +1.0 deg, 0.36 kg 4 cm left, friction -0.44 | 4 of 4 |  |
| repeat 16: x +0.7 cm, y -1.0 cm, turned +0.1 deg, 0.20 kg 3 cm left, friction +0.64 | 4 of 4 |  |
| repeat 17: x -0.6 cm, y +0.9 cm, turned +2.0 deg, 0.09 kg, friction -0.07 | 4 of 4 |  |
| repeat 18: x -0.8 cm, y -1.4 cm, turned +3.0 deg, 0.02 kg 1 cm left, friction +0.91 | 4 of 4 |  |
| repeat 19: x +1.4 cm, y +0.8 cm, turned -1.4 deg, 0.49 kg 3 cm left, friction +0.02 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 20: x +1.3 cm, y -1.5 cm, turned +1.5 deg, 0.47 kg 1 cm right, friction +0.85 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 21: x +0.2 cm, y -1.4 cm, turned -1.5 deg, 0.28 kg 5 cm right, friction -0.14 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 22: x +0.3 cm, y -1.6 cm, turned -0.6 deg, 0.40 kg 2 cm right, friction +0.75 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 23: x +0.4 cm, y -1.2 cm, turned +1.4 deg, 0.36 kg 1 cm right, friction +0.06 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 24: x -1.7 cm, y +0.4 cm, turned -2.1 deg, 0.25 kg 3 cm right, friction -0.19 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 25: x -1.7 cm, y +1.8 cm, turned -0.2 deg, 0.46 kg 4 cm left, friction -0.19 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 26: x -0.3 cm, y -1.3 cm, turned +1.4 deg, 0.17 kg 5 cm left, friction +0.62 | 4 of 4 |  |
| repeat 27: x -1.8 cm, y +0.6 cm, turned -0.3 deg, 0.11 kg 4 cm right, friction -0.43 | 4 of 4 |  |
| repeat 28: x -1.3 cm, y -0.1 cm, turned -0.4 deg, 0.20 kg 4 cm right, friction -0.55 | 4 of 4 |  |
| repeat 29: x -1.4 cm, y +1.9 cm, turned -1.7 deg, 0.26 kg, friction -0.86 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 30: x +0.0 cm, y +0.3 cm, turned +2.3 deg, 0.47 kg 3 cm left, friction -0.85 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 31: x +0.7 cm, y +1.7 cm, turned -2.8 deg, 0.38 kg 1 cm left, friction +0.32 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 32: x +0.7 cm, y -1.4 cm, turned -1.0 deg, 0.41 kg, friction +0.29 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 33: x +1.8 cm, y +1.9 cm, turned -2.8 deg, 0.28 kg 2 cm right, friction -0.39 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 34: x -0.9 cm, y -0.6 cm, turned -2.6 deg, 0.07 kg 1 cm left, friction +0.76 | 4 of 4 |  |
| repeat 35: x -0.3 cm, y -1.3 cm, turned -0.3 deg, 0.44 kg 2 cm right, friction -0.60 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 36: x +1.9 cm, y +1.5 cm, turned -2.8 deg, 0.34 kg 4 cm right, friction -0.31 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 37: x -0.6 cm, y -0.6 cm, turned +1.9 deg, 0.17 kg 3 cm right, friction -0.03 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 38: x +0.3 cm, y +0.4 cm, turned +2.9 deg, 0.06 kg 1 cm left, friction +0.26 | 4 of 4 |  |
| repeat 39: x +1.0 cm, y -1.9 cm, turned +1.7 deg, 0.06 kg 2 cm right, friction -0.44 | 4 of 4 |  |
| repeat 40: x -0.3 cm, y +0.7 cm, turned -0.7 deg, 0.02 kg 4 cm right, friction +0.05 | 4 of 4 |  |
| repeat 41: x +0.7 cm, y +0.4 cm, turned -2.1 deg, 0.38 kg 2 cm right, friction -0.44 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 42: x -1.0 cm, y +1.0 cm, turned +0.4 deg, 0.29 kg 1 cm left, friction +0.94 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 43: x +1.1 cm, y -1.9 cm, turned -2.4 deg, 0.43 kg 5 cm right, friction +0.42 | 4 of 4 | cube resting in the bin +1.3 s |
| repeat 44: x -0.8 cm, y -0.7 cm, turned -0.8 deg, 0.03 kg 3 cm left, friction +0.76 | 4 of 4 |  |
| repeat 45: x -1.8 cm, y -0.6 cm, turned +1.2 deg, 0.33 kg 1 cm right, friction +0.32 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 46: x +0.9 cm, y -1.9 cm, turned +0.6 deg, 0.14 kg 3 cm right, friction +0.56 | 4 of 4 |  |
| repeat 47: x -0.8 cm, y -1.8 cm, turned -0.6 deg, 0.03 kg 4 cm left, friction -0.67 | 4 of 4 |  |
| repeat 48: x +1.6 cm, y +1.6 cm, turned +1.4 deg, 0.12 kg 4 cm left, friction +0.76 | 4 of 4 |  |
| repeat 49: x +1.0 cm, y +0.0 cm, turned -2.6 deg, 0.32 kg 2 cm right, friction -0.33 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 50: x -0.6 cm, y -1.3 cm, turned +2.5 deg, 0.29 kg 3 cm right, friction +0.58 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 51: x -0.2 cm, y +1.9 cm, turned +0.7 deg, 0.49 kg 1 cm right, friction -0.38 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 52: x -0.5 cm, y -1.0 cm, turned -2.8 deg, 0.37 kg 4 cm right, friction +0.55 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 53: x +1.4 cm, y -1.7 cm, turned +1.4 deg, 0.45 kg 3 cm left, friction -0.55 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 54: x -1.8 cm, y -1.8 cm, turned -2.9 deg, 0.37 kg 5 cm right, friction +0.41 | 4 of 4 | cube resting in the bin +1.2 s |
| repeat 55: x +1.2 cm, y -0.9 cm, turned +2.1 deg, 0.41 kg 2 cm left, friction +0.18 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 56: x +1.8 cm, y -1.4 cm, turned -0.3 deg, 0.19 kg 2 cm left, friction +0.48 | 4 of 4 |  |
| repeat 57: x -1.5 cm, y +1.7 cm, turned -2.5 deg, 0.32 kg 3 cm left, friction -0.21 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 58: x -0.8 cm, y -1.3 cm, turned -2.0 deg, 0.08 kg 3 cm left, friction +0.99 | 4 of 4 |  |
| repeat 59: x -1.0 cm, y -0.5 cm, turned -0.1 deg, 0.02 kg 3 cm right, friction -0.47 | 4 of 4 |  |

Variations: set down up to 2 cm and 3 deg off its mark; up to 0.5 kg carried, up to 5 cm either side of its site; friction across each surface pair's published range (contact_pairs.SPREADS; a factor of two where a source gives none). The placement and payload ranges are assumptions, stated; the friction ranges are the sources'.
