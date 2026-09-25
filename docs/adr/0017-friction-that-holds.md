# Friction that holds: no creep below the limit, no self-contact in robot models

**Problem.** Carrying a cube across the Fetch field (ADR 0018), the cube slid out of the
kit gripper on the way. Measured with the arm lab holding its 16 g, 25 mm wooden cube
still, the jaws squeezing at their 0.6 N m limit - about 12 N at each pad, against a
weight of 0.16 N - the cube slid out of the grip at 2 mm/s and accelerating: 18.5 mm in
10 s. Nothing physical does that. MuJoCo's contacts are soft constraints: below the
friction limit they still yield a little, and under a sustained load the yield adds up
to creep.

The same softness had flattered a validated result. The mobile platform "cleared" the
20 mm curb (ADR 0013), but its casters have 40 mm wheels: a free wheel pushed at its
axle against a step as tall as its radius meets the edge at the axle's own height, and
nothing lifts it. It crept up the edge.

**Does an existing simulator solve it? Can we wrap it?** Yes. MuJoCo has a noslip
post-processor for exactly this: after the main solve it removes the slip in friction
dimensions that the soft constraints allowed, and leaves sliding above the friction
limit alone. It is one option (`noslip_iterations`), set by the adapter.

**Measurements** (the cube held still for 10 s):

| noslip iterations | slide in 10 s |
| --- | --- |
| 0 (MuJoCo's default) | 18.5 mm, accelerating |
| 1 | 1.3 mm, still accelerating |
| 2 | 0.14 mm |
| 5 | 0.19 mm |

Elliptic cones alone reduced the slide to 7.2 mm and, with impratio 10, to 4 mm: less,
but still creep. Two iterations stop it; the adapter uses 2. Cost per step, best of
three interleaved runs: two-wheel robot 198 -> 251 us, arm lab 246 -> 308 us, mobile
platform 1096 -> 1211 us, mobile manipulator 1289 -> 1457 us.

**What else changed.** A box on a 20 degree plane with friction 0.2 still accelerates at
g (sin a - mu cos a) within 5 %, with and without noslip: real sliding is untouched. The
whole test-field matrix of ADR 0013 was re-run: every ramp and curb result is the same and
every sprint and crate time within 0.2 s, except the platform's 20 mm curb, now missed,
as a pushed caster of 20 mm radius should. The six-wheel rover still clears 10 mm only; the four-wheel rover,
driven through all its wheels, still clears 35 mm.

Turning noslip on also exposed a defect in a robot model: the Kinova Gen3's first joint
would not move at all. Its shoulder link overlaps its base by 12 mm at its home pose and
as its first joint turns, in MuJoCo Menagerie's own file as well. MuJoCo filters contacts between a body and its
parent, except when the parent is welded to the world - which a robot's base is - so the
two links touch, and the joint had been grinding against that contact at its 105 N m
limit just to turn. Soft friction let it creep round; noslip stopped it. The adapter now
excludes contacts between adjacent links of every registered robot model, which is what
MuJoCo's parent filter does for any other parent.

**Boundaries.** Noslip costs 10-27 % of a step here. It makes held contacts rigid in
their tangent directions; normal-direction softness (penetration, bounce) is unchanged,
and there is still no separate static coefficient (ADR 0010). Robot models keep their own
contacts otherwise, including non-adjacent self-collisions.
