# Sourced contact-pair friction

**Problem.** Friction belongs to a pair of surfaces, but MuJoCo stores one coefficient
per geom and combines two of them with max() at equal priority. The kit's "skid"
material (0.01) therefore slid on the room floor at the floor's 0.8, and every rubber
contact ran at rubber's 1.2 whatever it touched. Measured on the two-wheel robot: at
0.2 Nm per wheel it moved 2 cm in four seconds, because a skid carrying 40% of its
weight dragged at 0.8. ARCHITECTURE.md had already recorded the defect and reserved
"an explicitly tested future adapter policy" for it. This is that policy.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo offers explicit
`<pair>` elements with their own friction. They were measured and rejected here: an
explicit pair is narrow-phased every step, and the mobile platform in the workshop
needs about 8,000 of them (+118 us per step), while `MjSpec.add_pair` costs 75 us per
call from Python - 450 ms added to every design edit in a builder whose edits take
100 ms. Geom priority cannot express a matrix either: the higher-priority geom's
coefficient wins against everything. What MuJoCo does support is reading and writing
`mjData.contact` between collision detection and constraint construction. The adapter
runs `mj_step` stage by stage in MuJoCo 3.3.7's order and, after `mj_collision`,
writes each contact's tangential coefficient from a pair table. MuJoCo still owns
collision, contact geometry, the solver and integration; the policy only chooses a
number MuJoCo was already choosing. With nothing sourced the staged step is
bit-identical to `mj_step`, and a test holds it to that.

**Unique contribution.** The sourced table (`materials/contact_pairs.py`): 26 pairs
over 8 real surfaces, each with a kinetic coefficient, a static one where the source
gives it, the conditions, a confidence and a citation that was opened and read.
Analogues - a pair with no measurement, borrowing a named similar pair - are
labelled and capped at low confidence. `docs/CONTACT_PAIRS.md` is generated from the
table and a test keeps them identical.

**Blueprint and builder.** `Material.surface` is an optional field naming the real
surface a material stands for; old JSON loads unchanged. Library materials saved
before this field existed are recognised by exact id, density and friction, so an
unedited saved design gets sourced friction and an edited one keeps its own numbers.
A friction coefficient the user types (gripper setup) is never replaced by the table.
Core stays standard-library only; the table is plain data; the adapter reads both.

**Boundaries.** MuJoCo receives the kinetic coefficient: there is still no stick-slip
distinction. Elastomer friction falls with contact pressure (rubber on rubber 1.2 at
35 kPa, 0.3 at 700 kPa) and MuJoCo's point contacts carry no contact area, so rubber
values are mid-range, not pressure-resolved. Torsional and rolling coefficients are
unchanged adapter defaults, and condim 4 ignores rolling friction entirely - rolling
resistance belongs to the wheel joint and is the next slice. Menagerie robot geoms
keep their upstream friction; the table applies only where both surfaces are named.
Pairs outside the table keep MuJoCo's combination and are reported as unsourced.

**Cost.** Compile time is unchanged. A step costs about 16 us more for the staging and
9 us for the policy; the rest of the measured difference comes from the physics itself
changing (things now slide that used to stick). The contact table is folded into the
inventory trial fingerprint, so comparisons stored under the old friction read as
historical instead of being silently reused.

**Next.** The same hook is where a causal chain enters the contact: a state field
(surface wetness, temperature) changing a pair's coefficient through an `Interaction`
that declares what it reads and writes. That is ROADMAP phase 4 and needs this
table's per-pair structure first.
