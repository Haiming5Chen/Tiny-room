# Servo damping the solver integrates

**Problem.** A joint's position controller commands bias + kp x error - kd x speed,
once per 2 ms step, from the speed at the start of the step; the solver then holds
that torque constant for the step. Measured at the ADR 0013 commit, the mobile
manipulator could not stand still: with the drive holding zero and every arm target
unchanged, its arm motors sat at their torque limits 70 % of the time, the elbow sagged
17 degrees, the base rocked 5.4 degrees between its front and rear casters, and the
machine crept 12 cm in 3 s. Anchored arms looked fine only because they start exactly
at equilibrium - the gravity feed-forward cancels the model's bias to the last bit, so
nothing excites them. A 0.2 rad/s nudge on every joint left the compact arm kit
chattering at its limits for good (75 % of steps, 21 degrees off target) and the arm
lab's standard arm at 21 % (7 degrees off).

**Why.** Damping applied late over-corrects. For one joint alone the sampled damping is
stable while kd x timestep / inertia stays below 2; in a chain the inertia that matters
is what a joint moves when its neighbours move too, and the compact arm's elbow and
wrist see about 1.5e-4 kg m^2. The step-to-step damping map, v <- (1 - dt M^-1 Kd) v,
has a spectral radius of 44 for the compact arm kit, 25 for the mobile manipulator, 5.0
for the standard arm and 1.00 for the long-reach arm (below 1 decays); the torque limit
is the only thing that bounds the result, as a limit cycle. A real servo does not
behave like this: its damping comes from the motor's back-EMF and an inner loop running
far faster than 500 Hz, so it acts on the speed as it is.

**Does an existing simulator solve it? Can we wrap it?** Yes: MuJoCo's implicitfast
integrator differentiates an actuator's force with respect to velocity when the force
is an affine bias, which is how ADR 0011 made the gearmotor's speed-torque line stable.
MuJoCo's own position actuator could not replace the controller - it has no gravity
feed-forward, and the controller must stay portable (`control/keyboard.py` knows no
solver). MuJoCo also keeps that velocity derivative when a force range clamps the
force (a pendulum with a -1000 N m s/rad bias clamped to 0.01 N m fell 5 degrees in
0.5 s where free fall gives 178), so a saturated servo must not carry a slope at all.

**Unique contribution.**
- *A command that says how it changes with speed.* `core/command.py` adds `Torque`, a
  float with a `slope` (N m s/rad, never positive, finite). Every backend can apply it
  as a torque; arithmetic on it returns a plain float, so a command that has been
  changed loses a slope that no longer describes it, while a clamp that does not bind
  keeps it.
- *The controller reports its damping.* The keyboard/program position controller
  returns `Torque(command, -kd)` below its limit and the plain limit at it.
- *The adapter integrates it.* Every kit motor compiles with an affine bias that is zero
  unless a step gives it a slope. Force = command + slope x (v - v0): exactly the
  command at the speed it was computed for (`actuator_force` equals it), and the slope
  for the implicit step. Where a sourced motor's speed-torque line binds, the line's
  slope wins; a command the line cut short carries none. A slope on a model's own
  position servo (the Panda) is refused.

**Blueprint and builder.** Nothing saved changes: gains, limits and designs load as
before, and a plain float command behaves exactly as it did. The Program, the
keyboard, the jog buttons, the inventory's trials and the test drive all use the same
controller, so all of them get the fix without a change at the call site.

**Result.** Same gains, same designs:

| Case | Before | After |
| --- | --- | --- |
| Mobile manipulator standing, arm held (last 1.5 s of 3) | arm at its limits 70 % of steps; rocks 5.4 deg; creeps 12 cm | 0 %; 0.00 deg; no creep |
| Compact arm kit, 0.2 rad/s nudge | 75 % at limits, 21 deg off | 0 %, 0.0 deg |
| Standard arm (arm lab), same nudge | 21 %, 7.0 deg | 0 %, 0.0 deg |
| Arm lab keyboard pickup: cube lifted | 12.1 cm | 14.4 cm |

The long-reach arm, whose damping map was already at 1.00, is unchanged (0.23 degrees of
steady sag in both). Cost: arm lab step 164 -> 170 us; the mobile manipulator's fell
1215 -> 1156 us because it no longer chatters.

**Boundaries.** The slope covers the controller's damping only: its stiffness (kp) and
the model-bias feed-forward are still sampled once per step. Stiffness is stable while
the joint's natural frequency times the step stays below 2 (the compact arm's elbow is
at about 0.7). Rotor inertia, which through a servo's gearbox would dominate these
link inertias, is still not modelled (ADR 0011). A backend without an implicit
integrator may ignore slopes; it then has the old behaviour.
