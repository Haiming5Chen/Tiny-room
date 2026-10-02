"""Variations of a run (ADR 0024): the machine set down off its mark, carrying a steel block,
on surfaces anywhere in their published friction range.

A test field runs its scenario once, exactly as designed. A test in a lab is repeated, and no
two repeats are alike: the machine is put down a little off its mark and heading, it carries
something, and the floor is not the surface a handbook measured. A result is worth defending
when its spread over such repeats is known, and when each repeat says which change moved it.

Each variation is ordinary data. The start pose and the payload are Blueprint edits, so a
varied design can be saved and looked at; the friction is a table of pair coefficients the
backend uses for that run - a condition of the run, as a damp floor would be, not part of the
design. Standard library only.
"""
from dataclasses import dataclass, replace
from math import cos, isfinite, radians, sin
import random

from little_world.construction.connections import conjugate, multiply, rotate
from little_world.construction.docking import body_bounds, poses
from little_world.core.component import Body, Geometry, Hinge, Transform
from little_world.core.material import Material
from little_world.materials import contact_pairs

STEEL = 7850.       # kg/m3: a payload is a steel block of its mass - a 4 cm cube at 0.5 kg
GAP = .001          # m: the block is set down this far above what carries it
PAYLOAD = 'payload'


@dataclass(frozen=True)
class Variation:
    """One repeat of a run: metres, degrees and kilograms."""
    label: str = 'as designed'
    x: float = 0.           # set down this far off its mark along the field's X ...
    y: float = 0.           # ... and its Y
    yaw: float = 0.         # turned this far off its heading about its mark, anticlockwise
    payload: float = 0.     # a steel block of this mass carried on the machine
    at: tuple = (0., 0.)    # where the block sits, in plan, from the payload site
    friction: float = 0.    # every sourced pair along its spread: -1 low end, +1 high end

    def __post_init__(self):
        object.__setattr__(self, 'at', tuple(float(v) for v in self.at))
        values = (self.x, self.y, self.yaw, self.payload, self.friction, *self.at)
        if len(self.at) != 2 or not all(isfinite(v) for v in values):
            raise ValueError('a variation needs finite numbers and a plan offset (x, y)')
        if self.payload < 0 or not -1. <= self.friction <= 1.:
            raise ValueError('a payload is a mass of zero or more; friction runs from -1 to +1')

    @property
    def nominal(self):
        return self == Variation(self.label)

    def describe(self):
        """What is varied, in short: 'x +1.2 cm, turned -2.6 deg, 0.31 kg 2 cm left, friction -0.40'."""
        parts = []
        if self.x:
            parts.append(f'x {100 * self.x:+.1f} cm')
        if self.y:
            parts.append(f'y {100 * self.y:+.1f} cm')
        if self.yaw:
            parts.append(f'turned {self.yaw:+.1f} deg')
        if self.payload:
            side = self.at[1]
            parts.append(f'{self.payload:.2f} kg' + (f' {100 * abs(side):.0f} cm {"left" if side > 0 else "right"}'
                                                       if round(100 * side) else ''))
        if self.friction:
            parts.append(f'friction {self.friction:+.2f}')
        return ', '.join(parts) or 'as designed'


@dataclass(frozen=True)
class Ranges:
    """How far the variations go, each way. The defaults are stated assumptions, not
    measurements: a machine set down by hand on a marked spot lands within 2 cm and 3
    degrees of it; a kit machine's load is up to 0.5 kg (a 4 cm steel block, a can of
    drink); friction anywhere in each pair's published range."""
    place: float = .02
    turn: float = 3.
    payload: float = .5
    shift: float = .05      # the payload this far to either side of its site (along Y)
    friction: float = 1.

    def __post_init__(self):
        if not all(isfinite(v) and v >= 0 for v in (self.place, self.turn, self.payload, self.shift)) \
                or not 0 <= self.friction <= 1:
            raise ValueError('ranges are finite and not negative; friction at most 1')


def plan(ranges=Ranges(), samples=8, seed=1):
    """The run as designed; each variation alone at both ends of its range, so its own
    effect can be read; then `samples` repeats with every variation drawn at random within
    its range - seeded, so a plan is the same every time it is made."""
    r = ranges
    out = [Variation()]
    if r.place:
        cm = f'{100 * r.place:g} cm'
        out += [Variation(f'set down {cm} ahead', x=r.place), Variation(f'set down {cm} behind', x=-r.place),
                Variation(f'set down {cm} to the left', y=r.place), Variation(f'set down {cm} to the right', y=-r.place)]
    if r.turn:
        out += [Variation(f'turned {r.turn:g} deg left', yaw=r.turn), Variation(f'turned {r.turn:g} deg right', yaw=-r.turn)]
    if r.payload:
        kg = f'{r.payload:g} kg'
        out.append(Variation(f'carrying {kg}', payload=r.payload))
        if r.shift:
            cm = f'{100 * r.shift:g} cm'
            out += [Variation(f'carrying {kg}, {cm} left', payload=r.payload, at=(0., r.shift)),
                    Variation(f'carrying {kg}, {cm} right', payload=r.payload, at=(0., -r.shift))]
    if r.friction:
        out += [Variation('friction at its low end', friction=-r.friction),
                Variation('friction at its high end', friction=r.friction)]
    draw = random.Random(seed)

    def either(size):
        return draw.uniform(-size, size)
    for i in range(samples):
        out.append(Variation(f'repeat {i + 1}', x=either(r.place), y=either(r.place), yaw=either(r.turn),
                             payload=draw.uniform(0., r.payload), at=(0., either(r.shift)),
                             friction=either(r.friction)))
    return tuple(out)


def moved(blueprint, x=0., y=0., yaw=0.):
    """The design set down (x, y) off its mark and turned `yaw` degrees about it."""
    if not (x or y or yaw):
        return blueprint
    half = radians(yaw) / 2
    turn = (cos(half), 0., 0., sin(half))
    out = []
    for c in blueprint.components:
        if isinstance(c, Body) and c.parent is None:
            px, py, pz = rotate(turn, c.transform.position)
            c = replace(c, transform=Transform((px + x, py + y, pz), multiply(turn, c.transform.quaternion)))
        out.append(c)
    return replace(blueprint, components=tuple(out))


def _jointed(blueprint):
    """Bodies that move against the machine's base: those below a hinge (wheels, arms)."""
    bodies = {b.id: b for b in blueprint.components if isinstance(b, Body)}
    hinged = {h.body for h in blueprint.components if isinstance(h, Hinge)}
    out = set()
    for b in bodies.values():
        walk = b
        while walk is not None:
            if walk.id in hinged:
                out.add(b.id)
                break
            walk = bodies.get(walk.parent)
    return out


def _block(mass):
    return (mass / STEEL) ** (1 / 3)


def carrier(blueprint, point, mass):
    """What would carry a steel block of `mass` set down at `point` (x, y) on the machine:
    (body, z of its top). It rests on the highest body under that point that does not move
    against the base, and nothing else may reach into the block - an arm overhead, a wheel
    alongside. Raises ValueError, naming what is in the way."""
    side = _block(mass)
    places = poses(blueprint)
    bodies = [b for b in blueprint.components if isinstance(b, Body)]
    bounds = {b.id: body_bounds(b, places[b.id]) for b in bodies}
    under = [(hi[2], b.id) for b in bodies for lo, hi in [bounds[b.id]]
             if lo[0] <= point[0] <= hi[0] and lo[1] <= point[1] <= hi[1]]
    if not under:
        raise ValueError(f'nothing on the machine at ({point[0]:.3f}, {point[1]:.3f}) to carry a payload')
    top, body = max(under)
    if body in _jointed(blueprint):
        raise ValueError(f'a moving part, {body}, is the highest thing at ({point[0]:.3f}, {point[1]:.3f})')
    lo = (point[0] - side / 2, point[1] - side / 2, top + GAP)
    hi = (point[0] + side / 2, point[1] + side / 2, top + GAP + side)
    for other, (a, b) in bounds.items():
        if other != body and all(a[i] < hi[i] and lo[i] < b[i] for i in range(3)):
            raise ValueError(f'{other} reaches into a payload at ({point[0]:.3f}, {point[1]:.3f})')
    return body, top


def payload_site(blueprint, mass=.5):
    """Where a payload goes by default, in plan: over the machine's centre of mass, if
    nothing that moves - an arm, a wheel - reaches above what would carry it there, as
    designed; else wholly on the largest top of its base, as far back as it will go in the
    middle - the machine faces +X, where fields put its work, so for an arm on a cart that
    is its deck behind the arm."""
    from little_world.construction.structure import centre_of_mass
    _, com = centre_of_mass(blueprint)
    places = poses(blueprint)
    moving = _jointed(blueprint)
    side = _block(mass)
    sweeps, tops = [], []
    for b in blueprint.components:
        if isinstance(b, Body):
            lo, hi = body_bounds(b, places[b.id])
            if b.id in moving:
                sweeps.append((lo, hi))
            else:
                tops.append(((hi[0] - lo[0]) * (hi[1] - lo[1]), lo, hi))

    def usable(point):
        try:
            _, top = carrier(blueprint, point, mass)
        except ValueError:
            return False
        return not any(hi[2] > top and lo[0] < point[0] + side / 2 and point[0] - side / 2 < hi[0] and
                       lo[1] < point[1] + side / 2 and point[1] - side / 2 < hi[1] for lo, hi in sweeps)

    if usable(com[:2]):
        return (com[0], com[1])
    if not tops:
        raise ValueError('the machine has no base to carry a payload')
    _, lo, hi = max(tops)
    back = (lo[0] + side / 2, (lo[1] + hi[1]) / 2)
    step, best = .005, None
    for i in range(int((hi[0] - lo[0] - side) / step) + 1):          # wholly on that top
        for j in range(int((hi[1] - lo[1] - side) / step) + 1):
            point = (lo[0] + side / 2 + i * step, lo[1] + side / 2 + j * step)
            gap = (point[0] - back[0]) ** 2 + (point[1] - back[1]) ** 2
            if (best is None or gap < best[0]) and usable(point):
                best = (gap, point)
    if best is None:
        raise ValueError('no place on the machine clear of its moving parts for a payload')
    return best[1]


def loaded(blueprint, mass, point):
    """The design carrying a steel block of `mass` kg set down at `point` (x, y), fixed to
    what it rests on. Its mass and inertia follow from its size and steel's density, as
    every body's do."""
    if mass <= 0:
        return blueprint
    if any(c.id == PAYLOAD for c in blueprint.components):
        raise ValueError('the design already has a body called payload')
    body, top = carrier(blueprint, point, mass)
    side = _block(mass)
    held = poses(blueprint)[body]
    centre = (point[0], point[1], top + GAP + side / 2)
    local = rotate(conjugate(held.quaternion), tuple(c - p for c, p in zip(centre, held.position)))
    block = Body(PAYLOAD, Geometry('box', (side, side, side)), PAYLOAD,
                 Transform(local, conjugate(held.quaternion)), parent=body)
    steel = Material(PAYLOAD, STEEL, .5, (.42, .44, .47, 1.), surface='steel')
    materials = tuple(m for m in blueprint.materials if m.id != PAYLOAD) + (steel,)
    return replace(blueprint, components=(*blueprint.components, block), materials=materials)


def varied(blueprint, variation, site=None):
    """The design as a variation runs it: loaded, then set down off its mark. `site` is
    where its payload goes, in plan, before the variation's own shift (default:
    `payload_site`)."""
    bp = blueprint
    if variation.payload > 0:
        site = site if site is not None else payload_site(blueprint, variation.payload)
        bp = loaded(bp, variation.payload, (site[0] + variation.at[0], site[1] + variation.at[1]))
    return moved(bp, variation.x, variation.y, variation.yaw)


def friction(variation):
    """The pair coefficients a variation runs on, or None as sourced."""
    return contact_pairs.varied(variation.friction) if variation.friction else None
