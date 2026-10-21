# Fetch, varied: arm on a cart

71 runs, running the field's program, solved once for the design on its mark.
Payload site: (-0.105, -0.000) m in plan, a steel block of the payload's mass.

| Goal | Met | Drawn at random | Times (fastest / median / slowest) | Not met in |
| --- | --- | --- | --- | --- |
| Reached the table | 71 of 71 | 59 of 59, at least 95 % | 10.3 s / 10.5 s / 10.7 s | - |
| Cube lifted 5 cm | 71 of 71 | 59 of 59, at least 95 % | 19.2 s / 19.4 s / 19.9 s | - |
| Cube resting in the bin | 71 of 71 | 59 of 59, at least 95 % | 36.7 s / 37.3 s / 38.1 s | - |
| Stayed upright | 71 of 71 | 59 of 59, at least 95 % | - | - |

The program looked for its object with the field's camera (ADR 0032) in 71 runs and saw it 1.0 mm from where it was planned (median; 0.7 to 1.9 mm), each time within 1.9 mm of where it really was.

How sure: the 59 runs drawn at random within the ranges are the sample. Every goal was met in 59 of them, so at least 95 % of runs set up at random within these ranges would meet every goal (95 % confidence, one-sided, Clopper-Pearson). The other 12 runs were chosen, not drawn - the design as designed and each variation alone at either end of its range: they check the corners and measure no rate. To show failures below 5 % at 95 % takes 59 drawn runs without one (`--samples 59`).

How fetch_cube was handled, over 71 runs (ADR 0040): the force on it from each thing that touched it, largest in any one step and averaged over 50 ms; how far it leaned, before it was held and as it came to rest; how far it fell when the machine let go.

| | Median | Least | Most |
| --- | --- | --- | --- |
| force from the machine, in a step | 4.05 N | 3.50 N | 5.08 N |
| force from the machine, over 50 ms | 3.89 N | 3.35 N | 4.98 N |
| force from the bin, in a step | 0.52 N | 0.42 N | 0.78 N |
| force from the bin, over 50 ms | 0.26 N | 0.23 N | 0.30 N |
| force from the table, in a step | 0.48 N | 0.22 N | 0.85 N |
| force from the table, over 50 ms | 0.18 N | 0.16 N | 0.23 N |
| leaned from how it stood | 26.7 deg | 26.1 deg | 27.6 deg |
| leaned before it was held | 0.0 deg | 0.0 deg | 0.1 deg |
| leaning when it came to rest | 0.0 deg | 0.0 deg | 0.0 deg |
| fell when let go | 0.3 cm | 0.1 cm | 1.1 cm |

## Under a micrometre (ADR 0043)

Each of the 59 set-ups drawn at random run 5 times more, the machine set down within 1 micrometre of where it was and turned within 0.00057 degrees - the same set-up to any lab, and the same camera noise. The outcome changed in none of the 59.

How far each measure spread among a set-up's 6 runs (the median over set-ups, and the most), against how far it spread across the 59 set-ups: under 0.1 of it, a measure is the design's; above, partly chance. And how many set-ups spread further than that under a micrometre: each one is a knife edge for that measure.

| Measure | Under a micrometre (median) | Most, and where | Across set-ups | Share | Set-ups past a tenth | |
| --- | --- | --- | --- | --- | --- | --- |
| last goal met, s | 0.098 | 0.48 (repeat 6) | 1.2 | 0.08 | 25 of 59 | the design's |
| squeeze over 50 ms, N | 0.0623 | 0.586 (repeat 27) | 1.64 | 0.04 | 14 of 59 | the design's |
| table over 50 ms, N | 0.013 | 0.0504 (repeat 38) | 0.0637 | 0.20 | 46 of 59 | partly chance |
| bin in a step, N | 0.0678 | 0.308 (repeat 10) | 0.354 | 0.19 | 52 of 59 | partly chance |
| bin over 50 ms, N | 0.0206 | 0.0446 (repeat 4) | 0.062 | 0.33 | 58 of 59 | partly chance |
| fell when let go, cm | 0.288 | 0.898 (repeat 10) | 0.996 | 0.29 | 55 of 59 | partly chance |
| leaned at most, deg | 0.115 | 1.29 (repeat 43) | 1.42 | 0.08 | 26 of 59 | the design's |

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
| carrying 0.5 kg, 5 cm left | 4 of 4 | cube resting in the bin +1.0 s |
| carrying 0.5 kg, 5 cm right | 4 of 4 | cube resting in the bin +1.1 s |
| friction at its low end | 4 of 4 |  |
| friction at its high end | 4 of 4 |  |
| repeat 1: x -1.5 cm, y +1.4 cm, turned +1.6 deg, 0.13 kg, friction -0.10 | 4 of 4 |  |
| repeat 2: x +0.6 cm, y +1.2 cm, turned -2.4 deg, 0.01 kg 3 cm left, friction -0.13 | 4 of 4 |  |
| repeat 3: x +1.0 cm, y -2.0 cm, turned -0.3 deg, 0.36 kg 3 cm right, friction +0.89 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 4: x +1.6 cm, y -1.9 cm, turned -2.8 deg, 0.27 kg 4 cm left, friction -0.24 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 5: x -1.1 cm, y -0.3 cm, turned -2.8 deg, 0.11 kg 1 cm right, friction -0.01 | 4 of 4 |  |
| repeat 6: x -1.1 cm, y -1.1 cm, turned -1.7 deg, 0.23 kg 2 cm right, friction -0.96 | 4 of 4 |  |
| repeat 7: x +1.4 cm, y +0.2 cm, turned +0.9 deg, 0.09 kg 5 cm left, friction +0.72 | 4 of 4 |  |
| repeat 8: x -1.5 cm, y -0.7 cm, turned +1.3 deg, 0.36 kg 4 cm left, friction -0.16 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 9: x +1.3 cm, y +0.7 cm, turned -1.2 deg, 0.29 kg 4 cm left, friction +0.69 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 10: x +0.0 cm, y +0.4 cm, turned -2.8 deg, 0.12 kg 3 cm left, friction -0.17 | 4 of 4 |  |
| repeat 11: x -1.3 cm, y +0.2 cm, turned +1.2 deg, 0.34 kg 1 cm right, friction -0.12 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 12: x +0.0 cm, y +1.1 cm, turned +0.1 deg, 0.20 kg, friction -0.94 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 13: x -1.8 cm, y +0.8 cm, turned +2.9 deg, 0.30 kg 1 cm right, friction -0.66 | 4 of 4 | cube resting in the bin +1.1 s |
| repeat 14: x +0.0 cm, y +1.9 cm, turned +1.6 deg, 0.27 kg 4 cm left, friction -0.54 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 15: x +0.1 cm, y +1.8 cm, turned +0.5 deg, 0.23 kg 2 cm right, friction +0.10 | 4 of 4 |  |
| repeat 16: x +1.8 cm, y -2.0 cm, turned +1.7 deg, 0.41 kg 4 cm left, friction +0.48 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 17: x +1.2 cm, y +0.1 cm, turned +0.4 deg, 0.21 kg 4 cm right, friction +0.74 | 4 of 4 |  |
| repeat 18: x +0.3 cm, y -1.2 cm, turned +0.0 deg, 0.24 kg 1 cm right, friction -0.31 | 4 of 4 |  |
| repeat 19: x +0.2 cm, y +0.5 cm, turned +0.7 deg, 0.23 kg 5 cm right, friction -0.54 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 20: x -1.3 cm, y +0.3 cm, turned +2.2 deg, 0.40 kg 3 cm left, friction +0.63 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 21: x -1.0 cm, y +1.4 cm, turned +1.0 deg, 0.04 kg 5 cm right, friction -0.97 | 4 of 4 |  |
| repeat 22: x +1.0 cm, y -1.0 cm, turned -2.3 deg, 0.31 kg 2 cm right, friction -0.86 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 23: x -1.4 cm, y +0.1 cm, turned -2.0 deg, 0.14 kg 2 cm left, friction -0.09 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 24: x -0.7 cm, y -0.1 cm, turned -2.9 deg, 0.19 kg 1 cm right, friction -0.62 | 4 of 4 |  |
| repeat 25: x -1.6 cm, y +1.6 cm, turned +0.1 deg, 0.10 kg 1 cm left, friction +0.63 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 26: x -1.9 cm, y -1.9 cm, turned -2.1 deg, 0.36 kg 3 cm right, friction +0.41 | 4 of 4 | cube lifted 5 cm +0.5 s; cube resting in the bin +1.3 s |
| repeat 27: x +0.7 cm, y +0.2 cm, turned -1.7 deg, 0.49 kg 3 cm left, friction +0.03 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 28: x -1.1 cm, y +0.6 cm, turned -0.6 deg, 0.29 kg 2 cm right, friction +0.26 | 4 of 4 |  |
| repeat 29: x -1.8 cm, y -0.8 cm, turned +2.8 deg, 0.44 kg 2 cm right, friction +0.72 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 30: x -0.8 cm, y +1.8 cm, turned +1.5 deg, 0.21 kg 2 cm right, friction -0.98 | 4 of 4 |  |
| repeat 31: x +1.5 cm, y -1.8 cm, turned +1.9 deg, 0.48 kg 1 cm left, friction -0.66 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 32: x +1.5 cm, y +1.9 cm, turned +1.2 deg, 0.25 kg 1 cm right, friction -0.31 | 4 of 4 |  |
| repeat 33: x -1.2 cm, y +0.7 cm, turned -0.4 deg, 0.10 kg 4 cm right, friction +0.33 | 4 of 4 |  |
| repeat 34: x -0.8 cm, y -0.0 cm, turned -1.0 deg, 0.44 kg 4 cm left, friction -0.96 | 4 of 4 | cube resting in the bin +0.5 s |
| repeat 35: x -1.2 cm, y -0.7 cm, turned +2.9 deg, 0.39 kg 2 cm right, friction -0.57 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 36: x +0.7 cm, y +1.4 cm, turned +2.6 deg, 0.17 kg 4 cm left, friction +0.37 | 4 of 4 |  |
| repeat 37: x -0.1 cm, y +1.9 cm, turned -1.6 deg, 0.36 kg 4 cm right, friction -0.66 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 38: x +1.6 cm, y -1.1 cm, turned +1.6 deg, 0.30 kg 3 cm left, friction -0.26 | 4 of 4 |  |
| repeat 39: x -0.6 cm, y -0.8 cm, turned +2.2 deg, 0.30 kg 5 cm left, friction +0.77 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 40: x -1.5 cm, y +0.2 cm, turned -2.4 deg, 0.02 kg 4 cm right, friction +0.73 | 4 of 4 |  |
| repeat 41: x +1.2 cm, y +1.3 cm, turned -1.0 deg, 0.31 kg 3 cm left, friction -0.24 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 42: x +0.3 cm, y -1.1 cm, turned -2.5 deg, 0.13 kg 4 cm left, friction +0.13 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 43: x +1.7 cm, y -0.2 cm, turned -1.3 deg, 0.39 kg 3 cm left, friction -0.98 | 4 of 4 |  |
| repeat 44: x +0.7 cm, y -1.6 cm, turned -2.3 deg, 0.44 kg 5 cm right, friction -0.52 | 4 of 4 | cube resting in the bin +0.9 s |
| repeat 45: x +2.0 cm, y -0.3 cm, turned -2.3 deg, 0.08 kg 3 cm right, friction +0.49 | 4 of 4 |  |
| repeat 46: x -1.6 cm, y +1.6 cm, turned -0.7 deg, 0.49 kg 4 cm left, friction -0.41 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 47: x -1.0 cm, y -0.1 cm, turned -2.4 deg, 0.33 kg 5 cm right, friction -0.98 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 48: x +1.9 cm, y -0.8 cm, turned +0.6 deg, 0.22 kg 2 cm right, friction -0.87 | 4 of 4 |  |
| repeat 49: x +1.7 cm, y +1.9 cm, turned +2.8 deg, 0.06 kg 3 cm right, friction +0.24 | 4 of 4 |  |
| repeat 50: x +1.9 cm, y +0.2 cm, turned +1.1 deg, 0.33 kg 2 cm right, friction +0.08 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 51: x -0.8 cm, y -1.0 cm, turned -2.5 deg, 0.14 kg 5 cm left, friction -0.10 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 52: x +0.6 cm, y +0.6 cm, turned +2.6 deg, 0.20 kg 2 cm right, friction -0.35 | 4 of 4 |  |
| repeat 53: x -0.7 cm, y +1.4 cm, turned +2.4 deg, 0.15 kg 2 cm right, friction +0.09 | 4 of 4 |  |
| repeat 54: x +0.3 cm, y +0.4 cm, turned -1.5 deg, 0.01 kg 3 cm right, friction -0.86 | 4 of 4 |  |
| repeat 55: x +0.2 cm, y -1.7 cm, turned -2.5 deg, 0.32 kg 2 cm right, friction +0.58 | 4 of 4 | cube resting in the bin +1.0 s |
| repeat 56: x -0.0 cm, y +1.5 cm, turned -2.1 deg, 0.25 kg 3 cm left, friction -0.85 | 4 of 4 | cube resting in the bin +0.7 s |
| repeat 57: x +1.8 cm, y -1.3 cm, turned +1.7 deg, 0.49 kg 3 cm left, friction -0.36 | 4 of 4 | cube resting in the bin +0.8 s |
| repeat 58: x -1.6 cm, y +0.1 cm, turned +2.5 deg, 0.15 kg 4 cm left, friction -0.72 | 4 of 4 |  |
| repeat 59: x +1.6 cm, y -1.9 cm, turned -1.1 deg, 0.45 kg 3 cm left, friction +0.81 | 4 of 4 | cube resting in the bin +0.6 s |

Variations: set down up to 2 cm and 3 deg off its mark; up to 0.5 kg carried, up to 5 cm either side of its site; friction across each surface pair's published range (contact_pairs.SPREADS; a factor of two where a source gives none). The placement and payload ranges are assumptions, stated; the friction ranges are the sources'.
