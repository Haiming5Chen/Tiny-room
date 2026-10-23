# Time passes while the program looks: latencies from their sources, and the margin

**Problem.** A program in the simulator saw the world at the instant it asked, and its servo
commands and readings took no time: the camera's picture, the finder's work and the servo bus were
instantaneous. In a lab a depth frame reaches the program up to a frame interval after it was
exposed, the finder takes its time, and every command and reading crosses a serial bus while the
world moves on; a benchmark that let the world advance during each policy's measured latency found
every policy degraded as objects moved faster ([LIBERO-Dynamic, arXiv
2610.24579](https://arxiv.org/abs/2610.24579); FR-028, the weekly reading of 21 October). How late
may the Fetch program's pictures, commands and readings be before its results change?

**Does an existing simulator solve it? Can we wrap it?** MuJoCo keeps no history: it steps the
world now. What a camera sees is MuJoCo's own ray casting (ADR 0032) on the bodies' poses, so a
picture of the world as it was is the same ray casting on poses kept from then - laid out on an
MjData of its own, the world untouched. The delays themselves are not MuJoCo's: they are the
camera's frame rate (Intel), the finder's measured time and the bus's packets at its defaults
(ROBOTIS e-Manual).

**Unique contribution.**
- *Latencies from their sources* (`control/latency.py`, standard library): a picture is late by the
  D435's frame interval at 30 fps (33 ms) and the finder's time (106 ms searching 25 cm round the
  plan, measured); a command, by a Sync Write of the six servos' goal positions (44 bytes, 7.6 ms);
  a reading, by a Sync Read of the registers a grasp is felt by (170 bytes and six 500 us return
  delays, 33 ms) - Protocol 2.0 packets at the X series' default 57,600 bps, ten bits a byte.
  `Lag` holds commands and readings back step by step; the wheels, not on the bus, go at once.
- *A camera that sees the past* (`MujocoBackend.kept`, `as_it_was`, `sight`; `perception.eye.Late`):
  each picture shows the world as it was that many steps ago.
- *Sweeps with a latency* (`run`, `sweep`, `disturb`: `latency=`; `sweep --latency SECONDS|sourced`):
  recorded with the sweep and said in its report. None or zero, the run is the run it always was.
- *The margin* (`inventory/margin.py`, `python -m little_world.inventory.margin`): a disturbed sweep
  at each latency read beside the sweep without, pair by pair - set-ups met, broken, and how much
  later the last goal - and the largest latency at which none was broken.

**Blueprint and builder.** Untouched. The latency is the sweep's, not the machine's: the
interactive window runs without it.

**Result.** The Fetch field on the tuning draws (seed 1), beside ADR 0048's sweeps without latency
(`docs/sweeps/2026-10-23-fetch-latency-margin.md`, 207 runs):

| Latency: pictures / commands / readings | Undisturbed | Shoved 6 N s | Cube moved 2 s after the look |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 9 of 9 |
| **sourced: 139 / 7.6 / 33 ms** | 9 of 9, +0.0 s | 9 of 9, +0.0 s | 9 of 9, +0.1 s |
| 0.2 s on every path | 9 of 9, +3.9 s | 9 of 9, +3.8 s | 9 of 9, -0.6 s |
| 0.25 s on every path | 7 of 9 | 7 of 9 | 2 of 9 |
| 0.3 s on every path | 0 of 9 | 0 of 9 | 0 of 9 |

At the sourced latency the 71 set-ups of ADR 0048's sweep met every goal, 71 of 71, a median 0.03 s
later. One path at a time, 0.5 s late: the pictures changed nothing - 9 of 9, the last goal within
10 ms, since the program acts on a cube only once its pictures agree it stands still (ADR 0032) -
while the commands, or the readings, each broke 2 of 9. Every failure was one: the jaws held the
cube, and the program's grasp check - 0.5 s from the end of the closing ramp - was over before the
closing command had reached them and the hold had come back over the bus; it took the grasp to have
missed. So the margin is the grasp check's: 0.2 s each way held everywhere, 0.25 s broke 11 of 27,
and the sourced bus, 7.6 ms out and 33 ms back, is six times under it on its slower path - not
fragile by FR-028's threshold of three; nor are the pictures, at least 3.6 times under. The moved
cube breaks first at 0.25 s because looking again had used the program's one regrasp; at 0.2 s the
slower arm took its last picture before going down after the move, saw it, and looked again 2.3 s
sooner than without latency.

Held by `tests/test_latency.py` (7): the bus's times from its packets at the e-Manual's defaults
(a Sync Read of 4 bytes from two servos, 16 bytes and two status packets); a latency's paths and
steps; the lag holding the servos' commands and readings back while the wheels go at once; a late
camera seeing the cube where it was three steps ago while the world goes on untouched; the margin
read against the same set-ups without latency; a sweep recording its latency, saying it and refusing
one that is not a time; and a Fetch run with every path 0.5 s late, whose jaws hold the cube unfelt.
Suites on MuJoCo 3.10.0: 1077 passed with a display, 1025 headless.

**Boundaries.** The latencies are a model: a picture is the newest frame's age at most (a frame
interval) and the finder's median time on the cloud's CPU, not the owner's Mac's; the camera's own
pipeline beyond its frame interval, a USB adapter's latency timer and the program's own loop are not
in it; the bus is one Sync Write and one Sync Read, with no retries or lost packets. The arm's aimed
poses are checked against the arm as it stands (ADR 0025), not as last read, and the cart's pose is
the simulator's. One field, three conditions, the tuning draws: a study, not a certification (ADR
0049); the margin is known to the 0.05 s between the latencies tried.
