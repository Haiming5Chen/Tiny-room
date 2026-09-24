# From motor profiles to a reproducible physical robot

Current status: manufacturer endpoint specifications plus estimated simulation.
No real-device measurements have been collected. Neither the demo arm geometry
nor its mounting interfaces claim compatibility with the candidate actuators.

The next validation unit is one motor and one measured link. Before treating the
model as a build guide, capture the exact servo variant/interface, firmware and
operating mode; supply voltage; complete link/tool mass; centre of mass; pivot and
mounting dimensions; controller settings; and command/measurement timestamps.
Record unloaded motion, response at several known loads, and position holding.
Repeat trials and reserve some loads/trajectories for validation rather than fitting.
Compare measured and simulated angle, speed, settling time and holding error.
Report residuals and the tested voltage/load/speed ranges; do not extrapolate a
continuous torque rating from a short lift or a stall specification.

A useful measurement CSV contains:

```csv
time_s,command_angle_rad,measured_angle_rad,measured_velocity_rad_s,supply_voltage_V,load_mass_kg,load_com_distance_m
```

These are physical measurements, never values synthesized from our own simulator.
A later fitting tool can estimate response delay, damping and actuator response;
accepted parameters must retain the dataset reference and validation error.

Only after that should we compose the measured link into a complete arm/cart kit,
validate gripping and wheel traction with the actual contact materials, and produce
a checked bill of materials, mounting drawings and hardware control configuration.
The current parts export intentionally identifies those missing build requirements.
