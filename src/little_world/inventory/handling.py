"""How a handled part was treated during a run, beside whether the goals were met (ADR 0040).

A Fetch that meets its goals after knocking the cube over, or dropping it into the bin from a
height, is not the success a lab wants: in a lab the cube is a vial. The goals say where a part
ended; this says how it got there - for each thing that touched it (the machine, the table,
the bin), the hardest push on it from any one of its bodies, so that two jaws squeezing from
either side count as the squeeze and do not cancel; how far it leaned from upright - the most
over the run, the most before the machine first held it, and at the end (ADR 0042); and how far
it fell when the machine let it go. Read from the forces the contact solver applied each step
(`MujocoBackend.contact_forces`) and the part's pose.

A force in one step of a soft contact depends on the step: a knock lasts a few steps, and the
solver spreads it over them. The force averaged over 50 ms - what a force sensor that reads
20 times a second would show - is the steadier number, and both are kept (ADR 0040).
Standard library only.
"""
from collections import deque
from dataclasses import dataclass
from math import acos, degrees, sqrt

WINDOW = .05    # s: forces are also averaged over this long
HELD = .05      # N: two of the machine's bodies pushing a part this hard from opposite sides hold it



def grip_use(backend, part, machine='machine/'):
    """The share of its grip's friction the machine uses on `part` now, held in the air: the
    friction its contacts use over what their cones allow, summed (`MujocoBackend.friction_use`) -
    0 with nothing pulling it along the jaws, 1 when every contact is at its edge and it slides.
    None when anything else touches it, or nothing does (FR-036)."""
    rows = backend.friction_use(part) if part else ()
    if not rows or any(not other.startswith(machine) for other, _, _ in rows):
        return None
    normal = sum(n for _, n, _ in rows)
    return sum(u for _, _, u in rows) / normal if normal > 1e-9 else None

def partner(name, machine='machine/'):
    """What a body touching the part is called in a report: the machine; a part of the field by
    the first word of its name - 'field/bin_wall_2' is the bin, 'field/table' the table; any
    other part by its own name."""
    if name.startswith(machine):
        return 'machine'
    entity, _, rest = name.partition('/')
    return rest.split('_', 1)[0] if entity == 'field' else (rest or name)


def _up(quaternion):
    """The part's own z axis in the world, from its (w, x, y, z) turn."""
    w, x, y, z = quaternion
    return (2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y))


@dataclass(frozen=True)
class Handled:
    """One part's treatment over a run."""
    part: str
    peak: tuple = ()        # ((partner, newtons), ...): the hardest push on it from one of each partner's bodies, in any one step
    steady: tuple = ()      # ((partner, newtons), ...): the largest force on it from each, averaged over WINDOW
    tilt: float = 0.        # degrees: the most it leaned from how it stood at the start
    dropped: float | None = None   # m: the most it fell after the machine let go of it, before the
                                   # machine touched it again; None if never touched (ADR 0042)
    before: float = 0.      # degrees: the most it leaned before the machine first held it (ADR 0042)
    rest: float = 0.        # degrees: how far it leaned when the run ended - how it came to rest

    def of(self, what, partner_name):
        """`what`, 'peak' or 'steady', from `partner_name` - 0 if it never touched the part."""
        return dict(getattr(self, what)).get(partner_name, 0.)


class Watching:
    """Follows one part through a run: call `update` after each step."""

    def __init__(self, part, machine='machine/'):
        self.part, self.machine = part, machine
        self.peak, self.steady = {}, {}
        self.recent = {}            # partner -> deque of (dt, force) over the last WINDOW
        self.sums = {}
        self.start = None           # the part's up axis at the start
        self.tilt = 0.
        self.before = 0.            # the most it leaned until the machine first held it
        self.gripped = False
        self.lean = 0.              # how far it leans now
        self.released = None        # its height when the machine last touched it
        self.height = None          # its height now
        self.lowest = None          # its lowest since the machine let go of it, while it is let go
        self.fell = 0.              # the most it fell after the machine let go, before it touched it again

    def update(self, backend, state, dt):
        body = state.bodies.get(self.part) if state is not None else None
        if body is None:
            return
        up = _up(body.pose.quaternion)
        if self.start is None:
            self.start = up
        cos = max(-1., min(1., sum(a * b for a, b in zip(up, self.start))))
        lean = degrees(acos(cos))
        self.tilt = max(self.tilt, lean)
        self.height = body.pose.position[2]
        # Each body's push on the part, then the hardest of each partner's bodies: two jaws
        # squeezing from either side cancel in a sum, and each still presses.
        pushes = {}
        for name, force in backend.contact_forces(self.part):
            f = pushes.get(name, (0., 0., 0.))
            pushes[name] = tuple(a + b for a, b in zip(f, force))
        self.lean = lean
        if not self.gripped:
            self.gripped = _held(f for name, f in pushes.items() if name.startswith(self.machine))
            if not self.gripped:
                self.before = max(self.before, lean)
        totals = {}
        for name, f in pushes.items():
            who = partner(name, self.machine)
            totals[who] = max(totals.get(who, 0.), sqrt(sum(v * v for v in f)))
        for who in set(totals) | set(self.recent):
            size = totals.get(who, 0.)
            if who in totals:
                self.peak[who] = max(self.peak.get(who, 0.), size)
            window = self.recent.setdefault(who, deque())
            window.append((dt, size))
            self.sums[who] = self.sums.get(who, 0.) + dt * size
            span = sum(t for t, _ in window)
            while window and span - window[0][0] >= WINDOW - 1e-12:
                t, f = window.popleft()
                span -= t
                self.sums[who] -= t * f
            if span >= WINDOW - 1e-12:
                self.steady[who] = max(self.steady.get(who, 0.), self.sums[who] / span)
        # A fall is from where the machine let go to the lowest it then came to before the
        # machine touched it again: a part that slips out of the jaws and is then pressed by
        # them has fallen as far, though they touched it last (ADR 0042).
        if 'machine' in totals:
            self.released, self.lowest = self.height, None
        elif self.released is not None:
            self.lowest = self.height if self.lowest is None else min(self.lowest, self.height)
            self.fell = max(self.fell, self.released - self.lowest)

    def result(self):
        """What was watched; a partner that touched the part without pushing it is left out."""
        order = sorted((k for k, v in self.peak.items() if v > 1e-9), key=lambda k: (k != 'machine', k))
        return Handled(self.part, tuple((k, self.peak[k]) for k in order),
                       tuple((k, self.steady.get(k, 0.)) for k in order), self.tilt,
                       None if self.released is None else self.fell, self.before, self.lean)


def _held(forces):
    """Whether two of these pushes, each at least HELD, come from opposite sides: a part
    squeezed between them is held."""
    strong = [f for f in forces if sqrt(sum(v * v for v in f)) >= HELD]
    return any(sum(a * b for a, b in zip(f, g)) < 0 for i, f in enumerate(strong) for g in strong[i + 1:])


def summary(handled):
    """Over runs (one Handled each, of the same part): for each partner, the medians and
    largest of its peak and steady forces; the median and range of its lean - over the run,
    before it was held and at rest - and of the fall when let go. Rows of (label, median, low,
    high), forces in newtons, the lean in degrees, the fall in metres - for a report."""
    from statistics import median
    handled = [h for h in handled if h is not None]
    if not handled:
        return ()
    partners = []
    for h in handled:
        partners += [k for k, _ in h.peak if k not in partners]
    rows = []
    for who in sorted(partners, key=lambda k: (k != 'machine', k)):
        for what, said in (('peak', 'in a step'), ('steady', f'over {1000 * WINDOW:.0f} ms')):
            values = [h.of(what, who) for h in handled if who in dict(h.peak)]
            rows.append((f'force from the {who}, {said}', median(values), min(values), max(values)))
    tilts = [h.tilt for h in handled]
    rows.append(('leaned from how it stood', median(tilts), min(tilts), max(tilts)))
    before = [h.before for h in handled]
    rows.append(('leaned before it was held', median(before), min(before), max(before)))
    rest = [h.rest for h in handled]
    rows.append(('leaning when it came to rest', median(rest), min(rest), max(rest)))
    falls = [h.dropped for h in handled if h.dropped is not None]
    if falls:
        rows.append(('fell when let go', median(falls), min(falls), max(falls)))
    return tuple(rows)


def table(rows):
    """Summary rows as a Markdown table: forces in newtons, the lean in degrees, the fall in cm."""
    def unit(label, v):
        if label.startswith('force'):
            return f'{v:.2f} N'
        if label.startswith('lean'):
            return f'{v:.1f} deg'
        return f'{100 * v:.1f} cm'
    lines = ['| | Median | Least | Most |', '| --- | --- | --- | --- |']
    lines += [f'| {label} | {unit(label, mid)} | {unit(label, low)} | {unit(label, high)} |' for label, mid, low, high in rows]
    return lines
