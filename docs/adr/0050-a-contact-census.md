# A contact census: what multiccd decides, and what it does not

**Problem.** ADR 0027 turned MuJoCo's multiple-contact search (multiccd) off everywhere: on a
cylinder wheel its extra contacts added a rolling loss of the engine's own, measured. MuJoCo
collides most pairs of shapes with a collider of their own, which finds several points where two
faces meet; a pair it has no collider for goes to its general one, which finds a single point
unless multiccd is on. Since then decisions have rested on contacts no one had counted: the jaw
pads' squeeze and creep (ADR 0017, 0042), the cube's presses on the table (ADR 0040, 0041), its
landing in the bin (ADR 0042), the casters (ADR 0041). If a face held or stood on one point, its
resistance to turning came from that point alone, and the numbers would carry it (FR-030, the
weekly reading of 21 October: contact, not reasoning, is the limit, HexaShell).

**Does an existing simulator solve it? Can we wrap it?** MuJoCo finds the contacts; it says how
many, not what a project's results rest on. The census counts MuJoCo's own contacts on copies of
an instant, once as the model is set and once with multiccd on - no new physics.

**Unique contribution.**
- *The census of an instant* (`MujocoBackend.contact_census`): for each pair of bodies in contact,
  the kinds of shape that touch, the contact points as the model is set, and the points with
  multiccd on - both counted on copies of the instant, so a run goes on untouched.
- *At the moments a result is decided* (`inventory/census.py`, `python -m
  little_world.inventory.census`): the Fetch field run once as designed, a sweep run's new `probe`
  counting every 20 ms; the counts read at the cart standing at its start and at the table, the
  cube held on the table, carried, and resting in the bin - for the cube's pairs and the cart's
  wheels and casters on the floor, summed over each part's bodies.

**Blueprint and builder.** Untouched.

**Result.** Every face-on-face pair a decision rests on is box on box, which MuJoCo collides with
its own collider, and multiccd would not change one count: the cube on the table 4 points (1 to
2 as the jaws lift it), the jaw pads on the cube 1 to 4 each (the left pad 1 to 2 - the rotary
jaws meet the cube at an edge, OPEN LW-028), the palm stop 1 to 2, the cube in the bin 3 to 4,
each tread wheel's tread on the floor 2 to 6. So the squeeze, creep, presses and landing of ADR
0017, 0040, 0041 and 0042 do not rest on the setting, and no sweep was repeated with it on - a
valid negative result. The one pair the setting decides is each caster's wheel on the floor -
a cylinder on a box, the general collider - 1 point as set, 4 to 5 with multiccd on. A caster is
a narrow wheel rolling on a line, not a face on a face, so FR-030's rule repeats no sweep for it;
measured beside it, the casters' loads say how the cart stands: one carries 2.2 to 8.2 N through
the run, the other 0.4 to 2.5 N while the cart stands at its start and at the table, and nothing
at the bin, where its wheel is 0.2 mm above the floor (and up to 0.34 mm at times while the cube
is carried) - "on all four" (ADR 0041) holds at the table; at the bin the cart stands on three. The report: `docs/sweeps/2026-10-22-fetch-contact-census.md`.

Held by `tests/test_census.py` (3): a box standing on its face against a lying cylinder on one
point that multiccd would make several, counted on copies; a census row's part, moment and
summed points; a sweep run handing its probe every step. Suites on MuJoCo 3.10.0: 1052 passed with a display, 1000 headless.

**Boundaries.** One run, as designed: a drawn set-up could touch other faces, and the census
says how many points, not where they are or what they carry. The counts are MuJoCo 3.10.0's. The
general collider's other pairs in the scene - the jaws' pivot caps, bolts, hubs - touched none of
the counted parts at these moments. Multiccd stays off (ADR 0027).
