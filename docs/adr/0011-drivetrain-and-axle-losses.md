# Drivetrain and axle losses

**Problem.** Every hinge carried a viscous damping of 0.01 N m s/rad, and on wheels
it was the only loss. Measured at the ADR 0010 commit: the kit's 37 mm gearmotor, an
ideal 0.5 N m torque source, spun its bare shaft at 477 rpm where the Pololu 37D 30:1
it is modelled on is rated at 330; the mobile platform's drive wheels turned at 384 rpm
under load; its caster wheels did not turn at all (0.01 x 87 rad/s is 0.87 N m on a
20 mm wheel, far more than that contact transmits), so they skidded; and the platform
coasted down at 0.33 g. All of those numbers came from the damping constant, not from
a motor, a gearbox or a tyre.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo has every piece and
the adapter uses them: joint `frictionloss` (a dry-friction constraint) for gearbox
friction and rolling resistance, and affine actuator bias - which the implicitfast
integrator differentiates - for the motor's speed-torque line. What MuJoCo does not
supply is the numbers, or when a hinge is an axle. Its own rolling friction (condim 6)
was measured on a four-wheel test cart with the same lever arm: within 1.3 % of the
closed-form coast-down with elliptic friction cones, but 23-39 % short with the
pyramidal cones every scene here uses. Switching all contacts to elliptic cones would
change every grasp and skid validated so far, so it is a separate decision; until then
the loss is applied at the wheel's hinge, where it matches the closed form within 0.5 %.

**Unique contribution.**
- *Gearmotor data.* `assets/real_motors.py` carries all nine Pololu 37D ratios at
  12 V (stall torque, no-load speed, 5.5 A stall and 0.2 A no-load current; read on
  pololu.com 2026-09-25). A new envelope, `dc_friction_v1`, turns the currents into the
  motor's own friction: at no load the motor still draws current, and the torque that
  current makes is what the brushes, bearings and gears consume - referred to the
  output, stall_torque x I0 / (Is - I0), 0.052 N m for the 30:1. The motor's torque
  line is raised by that friction at both ends, so the net output (line minus friction)
  meets the datasheet exactly: stall torque at rest, zero at 330 rpm. The kit gearmotor
  now has this profile and no viscous damping.
- *Rolling resistance.* `materials/rolling.py`: the floor reaction sits a lever arm b
  ahead of the axle, giving a torque b x N against rolling. Rubber 1.19 mm (0.047 in,
  Hamilton Caster's 85A polyurethane on steel - no rubber value was found, so it is an
  analogue, low confidence), steel 0.48 mm (forged steel, measured, medium). For
  scale: 1.19 mm on an 85 mm wheel is a rolling coefficient of 0.014.
- *Which hinges are axles.* A tread geom must be rigidly part of a hinged body and be
  wheel-shaped about that hinge: a cylinder on the axis, a sphere centred on it, or one
  of a ring of same-surface blocks leaving no gap over 45 degrees (the 24 tread blocks
  of the hardware tread wheel). Each step, only contacts whose normal points at the
  axle (within 18 degrees) and that touch another machine count; N comes from the
  solver's contact force of the step just taken. A rubber gripper pad pressed by a
  hinged finger is not a tread; a caster's swivel is never charged its wheel's loss.
- *Coulomb, not a damper.* MuJoCo's dry friction is a soft constraint that behaves as
  a damper until it saturates, and how soon it saturates depends on the inertia behind
  it. Sourced friction gets the stiffest settings MuJoCo accepts (time constant two
  steps, impedance 0.9999). On a 37D driving a 2.2e-4 kg m^2 disc, against MuJoCo's
  defaults: coast-down 0.145 s, as Coulomb predicts (0.213 s); holding under 80 % of
  the friction torque, no creep (0.20 rad in a second).
- *An implicit speed-torque line.* Evaluated once per step, the line is unstable when
  timestep x slope / inertia exceeds about 2. A bare 37D output shaft is 1.8e-8 kg m^2
  (the rotor's own inertia, which Pololu does not publish, is absent): one 2 ms step
  took it to 50,000 rad/s and it sawtoothed around 24,000. Where the line limits a
  command, or one step could reach it, the adapter now writes the line's slope into the
  actuator's affine bias; `data.ctrl` and `actuator_force` still hold exactly the
  enveloped torque at the start of the step, and the integrator follows the line.

**Blueprint and builder.** `MotorProfile` gains an optional envelope name and two
optional currents; old profiles and JSON load unchanged and keep `linear_estimate_v1`.
Passive catalog axles and the caster's wheel lose their damping; ideal drive modules
keep theirs, because an ideal torque source has no no-load speed and that damping is
the only thing limiting how fast it spins. Swivels and user-created hinges keep the
default. The part guide and the motor-model form state the friction and its source.
For the 37 mm gearmotor this replaces ADR 0004's "internal motors model ideal torque
only"; the 42 mm motor and the servo horn remain ideal.

**Boundaries.** Friction is constant Coulomb friction at the no-load value: no
speed-dependent part, no load-dependent gear efficiency, and the same in both
directions (the 37D has a spur gearbox; a worm drive would behave very differently).
Pololu gives one no-load current for every ratio, so this is the motor's friction
referred through the gearbox; the gearbox's own drag is small by the table itself
(10,000 rpm / 30 is 333 rpm against the listed 330). Rotor inertia is not modelled:
through a 30:1 gearbox it counts 900 times over and can rival a kit wheel's, but
without a source it is left out rather than guessed. Tyres are rigid: no deformation,
no pressure dependence, and the 24-block tread wheel rolls as a polygon. N lags one
step. Loose rolling bodies (a ball on the floor) get no rolling resistance. The
caster swivel keeps an unsourced 0.01 N m s damping.

**Cost**, best of three interleaved runs against the ADR 0010 commit. Compile: 0.5 to
1.5 ms more (the tread tables). Step: two-wheel robot 86 -> 119 us, arm lab
124 -> 142 us, mobile platform 793 -> 849 us, mobile manipulator 1046 -> 1102 us. Most
of it is the per-step rolling-contact pass, which runs in Python over the few contacts
that qualify.

**Next.** Moving to elliptic cones would let MuJoCo's own rolling friction replace the
hinge policy and cover loose rolling bodies; it needs its own validation pass. A
measured rotor inertia (or a motor with a published one) would add the missing
armature.
