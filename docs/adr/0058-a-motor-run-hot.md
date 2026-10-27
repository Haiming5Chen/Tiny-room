# A motor run hot: a weakened motor among the disturbances, and a cart that does not notice

**Problem.** The disturbances a run can be given (ADR 0030, 0038) act on the machine's body, its
parts and its camera; none on its actuators. A lab's motors run hot: a winding's copper gains
resistance with its temperature - 0.393 % per kelvin at 20 C (NBS Circular 31, the copper wire
tables) - so at the same voltage a winding 50 K over 20 C draws 16 % less current at stall and makes
84 % of its stall torque, at the same free speed; a supply that sags takes torque and speed alike.
FR-019 (the weekly reading of 5 October) predicted that one weak wheel would make a differential
drive curve - the textbook reason robots need heading feedback - and asked how far.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo's actuators have fixed gains; its
`dcmotor` (3.7 on) models a motor's electrical side, heating included, but the kit's gearmotor is
modelled by its sourced speed-torque line (ADR 0011), and the pin's question is open (FR-004). The
line is the project's own, so a weakened motor is that line scaled.

**Unique contribution.**
- *A motor weakened as physics says* (`MotorProfile.weakened`, core): its own speed-torque line
  scaled - stall torque by one share, free speed by another - with its friction as it was, so the
  net endpoints are what the motor then delivers past its unchanged gearbox.
- *In a run* (`MujocoBackend.weaken`): from a moment on, a motor with a sourced profile follows the
  weakened line; a reset world's motor is itself again. A motor without one fails, explicitly.
- *A disturbance kind* (`fields/disturbance.py`): 'motor', with the motor and the shares it keeps,
  on the same triggers as the others; `hot(kelvin)` from copper's coefficient; `WEAK`, the kit cart's
  left drive motor 50 K hot from the start, for the Sprint and the Fetch - apart from the fields'
  own disturbances (ADR 0030), which come once a goal is met. The window offers it among the
  disturbances a run can be given (ADR 0055).

**Blueprint and builder.** Untouched: no design changes; the motor is weakened during a run only.

**Result.** The kit cart does not notice a hot motor:
- *Every drive field, run for run the same.* The Sprint, the ramps, the push and the curb run, each
  with the left motor 50 K hot from the start, gave exactly its undisturbed run: the drive never asks
  a motor for more than the operating cap the kit's gearmotors are given, 0.5 N m - 36 % of their
  stall torque, an assumption of the build report - which is at most 48 % of the line at the speed it
  turns; on the flat lane 23 to 34 %.
- *The margin, on the Sprint.* The left motor kept 84, 70, 60, 50, 45, 40, 35 and 30 % of its torque
  and the run was bit for bit the same; at 25 % it finished 6 ms sooner, its drift to the right 17 mm
  less (338 mm as designed); at 15 %, 2 ms sooner and 11 mm less. The speed control holds both wheels
  at the speed asked, and on the flat that takes little torque: one weak wheel curves the cart only
  once its motor cannot turn it at that speed - none of the weakenings a motor runs into.
- *The Fetch*: with the left motor 50 K hot, and with it keeping only 25 % of its torque, the run was
  bit for bit the one undisturbed - the cube in the bin at 36.9 s: its drives to a point ask still less.

Held by `tests/test_weak_motor.py` (4): the hot winding's line, pivoting about its free speed,
its friction kept, a supply's sag taking both ends, impossible shares refused; a backend that
weakens a motor until it is reset, and refuses a motor without a profile; the disturbance on its
trigger, said as it happened; and the Sprint run for run the same with the left motor hot. Suites on
MuJoCo 3.10.0: 1105 passed with a display, 1049 headless.

**Boundaries.** Copper's coefficient is sourced; the 50 K is assumed - Pololu gives no winding
temperature - and the magnets' own weakening with heat is not modelled. Only motors with a sourced
line can be weakened. The operating cap, 0.5 N m, is the build report's assumption, not a datasheet's; a
machine built closer to its motors' limits would notice a hot one, which these fields do not show.
FR-019's predicted curve was not seen: the closed form for a cart whose wheels turn at different
speeds was not compared, because they did not.
