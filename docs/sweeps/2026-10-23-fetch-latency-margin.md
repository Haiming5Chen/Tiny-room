Measured for ADR 0053 (time passes while the program looks) on 2026-10-23: the Fetch field as of ADR
0052, on the tuning draws (seed 1) - the 9 set-ups of its disturbed sweeps, undisturbed, shoved 6 N s
and with the cube moved 5 cm 2 s after the look, at the sourced latency and at 0.2, 0.25 and 0.3 s on
every path; the 9 undisturbed with one path at a time 0.5 s late; and the 71 set-ups of ADR 0048's
sweep at the sourced latency. 207 runs, read beside ADR 0048's sweeps without latency
(`2026-10-22-fetch-feel-disturbed-9.md`, `2026-10-22-fetch-feel-71.md`) - which a run without latency
still is, bit for bit (checked on the design). Again: `python -m little_world.inventory.margin
--latencies sourced,0.2,0.25,0.3 --jobs 2` and `python -m little_world.inventory.sweep fetch --samples 59
--latency sourced`.

The sourced latency: a picture shows the world as it was 139 ms before - the D435's frame interval at
30 fps, 33 ms, and the finder's 106 ms searching 25 cm round the plan (measured on a 2.1 GHz Xeon); a
command reaches the servos 7.6 ms late - a Sync Write of the six servos' goal positions, 44 bytes; a
reading comes 33 ms late - a Sync Read of the 14 bytes a grasp is felt by from each, 170 bytes and six
500 us return delays - on a Dynamixel bus at the X series' default 57,600 bps (ROBOTIS e-Manual).

## Fetch: results against latency

Each latency on the same set-ups, undisturbed and under each disturbance, beside the sweep without latency: the set-ups that met every goal, those the latency broke (met without it, missed with it), and the median change in when the last goal was met. A latency is how late the program's pictures show the world, its commands reach the servos and its readings of them reach it.

| Latency: pictures / commands / readings, ms | none | shoved 6 N s at the table | cube moved 5 cm sideways, 2 s later |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 9 of 9 |
| sourced: 139 / 7.6 / 33 | 9 of 9; +0.0 s | 9 of 9; +0.0 s | 9 of 9; +0.1 s |
| 0.2 s: 200 / 200 / 200 | 9 of 9; +3.9 s | 9 of 9; +3.8 s | 9 of 9; -0.6 s |
| 0.25 s: 250 / 250 / 250 | 7 of 9, 2 broken; +5.1 s | 7 of 9, 2 broken; +4.9 s | 2 of 9, 7 broken; +0.6 s |
| 0.3 s: 300 / 300 / 300 | 0 of 9, 9 broken | 0 of 9, 9 broken | 0 of 9, 9 broken |

Every set-up held at 0.2 s; at 0.25 s the latency broke some.

## One path at a time

| 0.5 s late on one path only | Met every goal | Broken | Last goal, median change (least to most) |
| --- | --- | --- | --- |
| pictures | 9 of 9 | 0 | +0.00 s (+0.00 to +0.01) |
| commands | 7 of 9 | 2 | +5.35 s (+4.84 to +5.63) |
| readings | 7 of 9 | 2 | +4.81 s (+4.70 to +4.93) |

## The 71 set-ups at the sourced latency

71 of 71 met every goal, as without latency; the last goal a median 0.03 s later (-0.35 to +0.33 s),
the grasp felt a median 6 ms sooner (-0.22 to +0.11 s).

What it shows:

- **Late pictures alone change nothing here.** Half a second late, the pictures gave the same
  outcomes and the last goal within 10 ms: the program acts on a cube only once its pictures agree it
  stands still (ADR 0032), and a picture of a still cube is the same picture half a second on. What
  moved in the half second - the cart rocking, the arm - moved the sightings by less than a micrometre.
- **The bus is what counts, and the grasp check sets the margin.** Every failure, on every path and at
  every latency, was the same: the jaws held the cube, and the program, its grasp check over, took the
  grasp to have missed ("Nothing held"). The check waits 0.5 s from the end of the jaws' closing ramp;
  within it the closing command must reach the jaws and the hold must come back over the bus. With 0.2 s
  each way, every set-up held; with 0.25 s, 11 of 27 broke; with 0.3 s, all. The sourced bus takes
  7.6 ms out and 33 ms back - six times under the margin on the slower path.
- **The moved cube is the most fragile at 0.25 s** - 7 of 9 broken against 2 - because its looking
  again had used the program's one regrasp: a grasp check that then misses is final. At 0.2 s the slower
  arm reached the higher pose later, its last picture before going down came after the move, and the
  program saw it moved and looked again 2.3 s sooner than it did without latency - it finished 0.6 s
  sooner.
- **Slower, not wrong.** At 0.2 s the undisturbed and shoved set-ups met every goal about 4 s later: each pose waits for
  readings a fifth of a second old to show it has settled.
