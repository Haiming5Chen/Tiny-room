# Fetch, varied: arm on a cart

20 runs, running the field's program, solved once for the design on its mark.
Payload site: (-0.105, -0.000) m in plan, a steel block of the payload's mass.

| Goal | Met | Drawn at random | Times (fastest / median / slowest) | Not met in |
| --- | --- | --- | --- | --- |
| Reached the table | 20 of 20 | 8 of 8, at least 69 % | 9.4 s / 9.6 s / 9.8 s | - |
| Cube lifted 5 cm | 20 of 20 | 8 of 8, at least 69 % | 16.2 s / 16.5 s / 17.7 s | - |
| Cube resting in the bin | 20 of 20 | 8 of 8, at least 69 % | 32.8 s / 33.2 s / 34.5 s | - |
| Stayed upright | 20 of 20 | 8 of 8, at least 69 % | - | - |

How sure: the 8 runs drawn at random within the ranges are the sample. Every goal was met in 8 of them, so at least 69 % of runs set up at random within these ranges would meet every goal (95 % confidence, one-sided, Clopper-Pearson). The other 12 runs were chosen, not drawn - the design as designed and each variation alone at either end of its range: they check the corners and measure no rate. To show failures below 5 % at 95 % takes 59 drawn runs without one (`--samples 59`).

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
| carrying 0.5 kg | 4 of 4 | cube lifted 5 cm +1.4 s; cube resting in the bin +1.4 s |
| carrying 0.5 kg, 5 cm left | 4 of 4 | cube lifted 5 cm +1.2 s; cube resting in the bin +0.9 s |
| carrying 0.5 kg, 5 cm right | 4 of 4 | cube lifted 5 cm +1.3 s; cube resting in the bin +1.5 s |
| friction at its low end | 4 of 4 |  |
| friction at its high end | 4 of 4 |  |
| repeat 1: x -1.5 cm, y +1.4 cm, turned +1.6 deg, 0.13 kg, friction -0.10 | 4 of 4 |  |
| repeat 2: x +0.6 cm, y +1.2 cm, turned -2.4 deg, 0.01 kg 3 cm left, friction -0.13 | 4 of 4 |  |
| repeat 3: x +1.0 cm, y -2.0 cm, turned -0.3 deg, 0.36 kg 3 cm right, friction +0.89 | 4 of 4 | cube resting in the bin +0.6 s |
| repeat 4: x +1.6 cm, y -1.9 cm, turned -2.8 deg, 0.27 kg 4 cm left, friction -0.24 | 4 of 4 |  |
| repeat 5: x -1.1 cm, y -0.3 cm, turned -2.8 deg, 0.11 kg 1 cm right, friction -0.01 | 4 of 4 |  |
| repeat 6: x -1.1 cm, y -1.1 cm, turned -1.7 deg, 0.23 kg 2 cm right, friction -0.96 | 4 of 4 |  |
| repeat 7: x +1.4 cm, y +0.2 cm, turned +0.9 deg, 0.09 kg 5 cm left, friction +0.72 | 4 of 4 |  |
| repeat 8: x -1.5 cm, y -0.7 cm, turned +1.3 deg, 0.36 kg 4 cm left, friction -0.16 | 4 of 4 |  |

Variations: set down up to 2 cm and 3 deg off its mark; up to 0.5 kg carried, up to 5 cm either side of its site; friction across each surface pair's published range (contact_pairs.SPREADS; a factor of two where a source gives none). The placement and payload ranges are assumptions, stated; the friction ranges are the sources'.
