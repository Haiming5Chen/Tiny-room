# Little World development rules

Read docs/VISION.md and docs/ARCHITECTURE.md before architectural changes.
Core must remain standard-library-only and independent of MuJoCo and UI.
Objects and robots share Entity/Blueprint. All construction emits versioned,
serializable Blueprint data. No task assumptions in Scene or native handles in core.
Keep geometry, materials, design, runtime state, controllers and solvers separate.
Unsupported behavior must fail explicitly; do not imply future physics exists.
Preserve build → simulate → reset → redesign and immutable saved designs.

Before a new system, document: Does an existing simulator solve it? Can we wrap it?
Is it our unique contribution? Does it preserve Blueprint construction, decoupled
UI/world/backend, and the future builder? Reuse solvers and license-tracked assets.

Add contract tests before significant new behavior, then relevant integration
checks. Run `python -m pytest`; no graphics required for the default suite. Camera
and viewer checks are explicit. Do not implement thermal, fluids, chemistry, AI,
or a graphical builder in milestone one. Do not add dependencies for future phases.
