# Tilt table, varied: arm on a cart

18 runs, held still for 33 s.
Payload site: (-0.105, -0.000) m in plan, a steel block of the payload's mass.

| Goal | Met | Drawn at random | Times (fastest / median / slowest) | Not met in |
| --- | --- | --- | --- | --- |
| Held at 20 deg | 18 of 18 | 8 of 8, at least 69 % | 11.1 s / 11.1 s / 11.1 s | - |
| Held at 30 deg | 18 of 18 | 8 of 8, at least 69 % | 16.1 s / 16.1 s / 16.1 s | - |
| Held at 40 deg | 18 of 18 | 8 of 8, at least 69 % | 21.1 s / 21.1 s / 21.1 s | - |
| Held at 50 deg | 18 of 18 | 8 of 8, at least 69 % | 26.1 s / 26.1 s / 26.1 s | - |
| Held at 60 deg | 0 of 18 | 0 of 8, at least 0 % | - | every run |

Tipped over between 53.3 deg (friction at its high end) and 59.4 deg (carrying 0.5 kg, 5 cm left).
Against the design's prediction for each variation: -2.3 to +1.0 deg, the furthest friction at its high end.

How sure: the 8 runs drawn at random within the ranges tipped over between 55.0 and 58.7 deg. Another run drawn the same way lands between the lowest and highest of 8 with probability 7/9, whatever the spread's shape (order statistics). The other 10 runs were chosen, not drawn - the design as designed and each variation alone at either end of its range: they check the corners and measure no rate.

## Each run

| Variation | Tipped at | Predicted | Goals | Changed from as designed |
| --- | --- | --- | --- | --- |
| as designed | 54.6 | 55.6 | 4 of 5 |  |
| set down 2 cm ahead | 54.9 | 55.6 | 4 of 5 | tipped +0.3 deg |
| set down 2 cm behind | 54.6 | 55.6 | 4 of 5 |  |
| set down 2 cm to the left | 54.6 | 55.6 | 4 of 5 |  |
| set down 2 cm to the right | 54.5 | 55.6 | 4 of 5 |  |
| carrying 0.5 kg | 58.4 | 57.5 | 4 of 5 | tipped +3.7 deg |
| carrying 0.5 kg, 5 cm left | 59.4 | 58.5 | 4 of 5 | tipped +4.8 deg |
| carrying 0.5 kg, 5 cm right | 57.1 | 56.5 | 4 of 5 | tipped +2.5 deg |
| friction at its low end | 55.6 | 55.6 | 4 of 5 | tipped +1.0 deg |
| friction at its high end | 53.3 | 55.6 | 4 of 5 | tipped -1.3 deg |
| repeat 1: x -1.5 cm, y +1.4 cm, 0.13 kg, friction -0.10 | 56.2 | 56.2 | 4 of 5 | tipped +1.6 deg |
| repeat 2: x +0.6 cm, y +1.2 cm, 0.01 kg 3 cm left, friction -0.13 | 55.0 | 55.7 | 4 of 5 | tipped +0.4 deg |
| repeat 3: x +1.0 cm, y -2.0 cm, 0.36 kg 3 cm right, friction +0.89 | 56.6 | 56.7 | 4 of 5 | tipped +2.0 deg |
| repeat 4: x +1.6 cm, y -1.9 cm, 0.27 kg 4 cm left, friction -0.24 | 57.9 | 57.3 | 4 of 5 | tipped +3.3 deg |
| repeat 5: x -1.1 cm, y -0.3 cm, 0.11 kg 1 cm right, friction -0.01 | 55.8 | 56.1 | 4 of 5 | tipped +1.2 deg |
| repeat 6: x -1.1 cm, y -1.1 cm, 0.23 kg 2 cm right, friction -0.96 | 57.2 | 56.4 | 4 of 5 | tipped +2.6 deg |
| repeat 7: x +1.4 cm, y +0.2 cm, 0.09 kg 5 cm left, friction +0.72 | 55.1 | 56.3 | 4 of 5 | tipped +0.5 deg |
| repeat 8: x -1.5 cm, y -0.7 cm, 0.36 kg 4 cm left, friction -0.16 | 58.7 | 57.7 | 4 of 5 | tipped +4.1 deg |

Variations: set down up to 2 cm off its mark, then squared to the field; up to 0.5 kg carried, up to 5 cm either side of its site; friction across each surface pair's published range (contact_pairs.SPREADS; a factor of two where a source gives none). The placement and payload ranges are assumptions, stated; the friction ranges are the sources'.
