# Sourced motor profiles and build reports

Reuse MuJoCo's existing torque actuators. Our contribution is portable component
provenance and explicit assumptions, not a new electromechanical solver. Optional
MotorProfile snapshots live in Blueprint; old motors retain ideal torque behavior.
The backend applies a speed-dependent envelope to every command path, including
Python, keyboard and pulse tests. No global callback or UI-only enforcement.

Initial profiles use manufacturer stall/no-load endpoints at a fixed 12 V. Linear
interpolation between endpoints is an unvalidated estimate, not a digitized measured
performance curve. Forward torque falls to zero at no-load speed; reverse/braking
commands retain the selected torque cap (also an approximation). max_torque is a
user-assumed operating cap, never labeled continuous torque. Continuous capability,
heating, battery sag, current, latency, backlash and firmware control are unknown or
unmodeled. No automated hardware control or fabricated physical validation.

Selecting a profile changes actuation only. Existing geometry, inertia and mounting
remain custom; an export must not imply the motor physically fits. Report assigned
candidate actuators separately from custom geometry and unresolved build requirements.
Freeze source URL, verification date and endpoint values in the design so later
registry revisions cannot silently change saved simulation behavior. Support
selection, removal, undo, old JSON, validation and actual native command tests.
