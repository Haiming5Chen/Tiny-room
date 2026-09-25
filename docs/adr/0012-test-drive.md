# Test drive: chase view, live telemetry and a run report

**Problem.** The builder is where the design happens; the test is where it succeeds or
fails, and the test was the weakest part of the loop. Measured on the default mobile
platform: SIMULATE showed the robot from 5.4 m, where the box around it covered 0.4 %
of the 3D view; the left panel kept the edit controls, all disabled while physics ran;
nothing on screen said how fast the robot went, what limited it or how hard its motors
worked; and Stop discarded the run without a trace, so the next design could not be
compared with this one. Follow (F) kept the robot centred but at the same distance,
and did not turn with it.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo's free camera and
renderer do the drawing; `mjCAMERA_TRACKING` follows a body's position but not its
heading. The chase view sets the same free camera's look-at point, azimuth, elevation
and distance each frame from the machine's pose, eased in the UI; `mj_ray` keeps it in
front of walls. The onboard-camera inset is a second `mjr_render` of the same scene
from the machine's own camera. Every number shown is MuJoCo state the physics already
computed - body pose and velocity, joint velocity, actuator force, contacts - read
through one adapter-side module. Nothing is estimated or animated for effect.

**Unique contribution.** The test is tied to the design and to the sources:
- *Telemetry* (`control/drive_telemetry.py`): forward speed and position of the
  machine's centre of mass (a base whose origin is a chassis rail would otherwise
  "travel" while turning on the spot), tilt, and for each drive motor its speed
  against its sourced no-load speed, its torque against what is available at that
  speed (the operating cap, or the speed-torque line of ADR 0007 / 0011), and its
  wheel slip - tread speed beyond the ground speed under that wheel, as the drive
  assist measures it. The panel names what sets the top speed, the drive assist's
  setting or the motors themselves, so a slow robot says why it is slow.
- *Run log* (`control/run_log.py`, standard library only): time, path length, top
  speed, maximum tilt, the share of time a motor was at its limit or a wheel slipped,
  and what the machine touched. Stop turns it into a run report with the difference
  from the previous run and three ways on: back to the Build stage, run again, or
  adjust the drive assist when that is what limited the speed. The Build stage keeps
  a one-line reminder of the last run.
- *Seeing the run*: a chase view behind the machine that turns with it (drag orbits,
  scroll zooms, both relative to the machine; right-drag pans and leaves the chase; F
  or the Chase button switches to the room and back), the path it drove drawn on the
  floor and kept after Stop, and for a machine with a camera, what that camera sees.

**Blueprint and builder.** Nothing is written to the Blueprint or the saved design.
Run reports and the path live in the session, like undo history, and an edit clears
them. The chase view is used for a machine that can drive (a differential drive and a
free base); arms and fixed machines keep the current camera. While physics runs the
first tab becomes Drive and shows the test instead of disabled edit controls; the
Connect tab keeps its motor pulse test.

**Boundaries.** Ideal sensors: exact simulator state, no noise, no latency, no sensor
model - the panel says so. Distance is the centre of mass's path over the floor,
sampled once per displayed frame, ignoring movements under 5 mm. Touch lists bodies in
contact with the machine, not forces or damage. Reports are not saved and are not the
inventory's controlled trials (ADR 0009), which remain the way to compare saved
versions under identical conditions. The chase view assumes the base's +X is forward,
as the drive assist does.

**Result.** The box around the platform covers 6.4 % of the 3D view in the chase view,
against 0.4 % before. The trail costs 0.6 ms a frame for 30 m of driving with turns
(straight runs merge into one segment); telemetry and the log cost well under 1 ms.

**Tests.** Run-log arithmetic, the chase camera's easing and angle wrap-around and the
trail's merging without MuJoCo; telemetry against the drive assist, a wheel-speed
closed form, a spin on the spot and a push against a fixed stand on the real
platform; and window tests that build, drive, stop, read the report, return to the
Build stage and show an onboard camera, through the real input callbacks.
