# Little World

Little World is a compositional macroscopic physical-world simulator for robotics,
embodied AI, and physical experimentation. It models reality's observable interface,
not its microscopic implementation. Geometry plus measurable material parameters,
state, and physical laws determine behavior. Objects and robots use the same parts;
adding joints, motors, sensors, and a controller creates an embodiment.

The unique contribution is construction, shared world representation, materials,
state, and eventually causal coupling between solvers. Reuse established solvers.
A plausible generated observation is different from a causally simulated outcome.
Accuracy must be stated against observables (trajectory, stopping distance, slip,
temperature, volume), with domains and tolerances, never universal realism claims.

Python, a future graphical builder, and a future AI designer all produce the same
serializable Blueprint. The intended loop is build → simulate → observe failure →
reset → redesign. Physics owns runtime poses; the saved design remains independent.

Long term: wetness can change traction, radiation can heat surfaces, and temperature
can influence evaporation through shared state and explicit interaction rules.
These are research directions, not capabilities of the initial implementation.

The first milestone is deliberately mechanical: room, primitive parts, two-wheel
robot, two hinges, two motors, onboard camera, and MuJoCo inspection/control.
No thermal/fluid/chemical systems, AI agents, or construction editor yet.
