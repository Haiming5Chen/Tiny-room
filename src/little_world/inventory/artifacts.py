"""Energy from nowhere: a contact that gave back more than it took (FR-040).

Every result here assumes the engine behaved as physics does, and nothing checked that it did.
A contact is a spring and a damper: while two bodies touch it takes energy as they press into
each other and gives some of it back as they part - never more than it took. One that gives more
is the engine making energy: a part started inside another, or found sunk in by a bad collision,
is pushed out with energy nothing put in. A simulated benchmark audited for this had 12 of 100
episodes flung by such contacts, the policy blamed for each (arXiv 2610.41857).

This watch adds up, for each pair of bodies, the work their contacts did on them from the moment
they touched (`MujocoBackend.contact_work`) - what the contacts gave back less what they took - and
flags the pair if that ever came to more than lifting the lighter of the two bodies GIVE takes. A
block dropped 5 cm onto a slab gives the slab all 40 mJ it fell, and is never given any back;
started 5 mm inside the slab, it is lifted 5 mm by nothing, and flagged. Whether the two bodies
are driven - a jaw, a roller - does not matter: their motors work on the bodies, not on the contact
between them. The watch reads the step and changes nothing. Standard library only.

GIVE is a judgment, set above what most runs show: the kit jaws' contacts give the cube back 1.3
mm's worth more than they took in the Fetch as designed - with no noslip pass, none (ADR 0074) -
and a part set 0.5 mm into what it rests on is pushed out with half a millimetre's.
"""
from dataclasses import dataclass

GIVE = .002     # m: contacts giving back more than lifting the lighter body this high takes are not physics
G = 9.81        # m/s^2


@dataclass(frozen=True)
class Artifact:
    """One time two bodies touched and their contacts gave back more than they took."""
    bodies: tuple           # the two bodies' names
    began: float            # s, when they came to touch
    at: float               # s, when their contacts had given back the most
    gave: float             # J, the most their contacts gave back beyond what they took
    allowed: float          # J, what lifting the lighter body GIVE takes
    deepest: float          # m, how far the pair's deepest contact point sank in while they touched
    lighter: str = ''       # what the energy is weighed against: the lighter of the two, as a report names it

    @property
    def lifted(self):
        """What was given, as the height it would lift the lighter body to, m."""
        return GIVE * self.gave / self.allowed

    def said(self):
        """The artifact in words, for a report."""
        return (f'the contact between the {_name(self.bodies[0])} and the {_name(self.bodies[1])} gave back '
                f'{1000 * self.gave:.2f} mJ more than it took - enough to lift {self.lighter or "the lighter"} '
                f'{1000 * self.lifted:.1f} mm - by {self.at:.1f} s')


@dataclass(frozen=True)
class Checked:
    """A run's physics check: how its contacts' work came out."""
    touches: int = 0        # times two bodies came into contact
    pairs: int = 0          # pairs of bodies that touched
    worst: float = 0.       # the most any contacts gave back beyond what they took, as a share of what was allowed
    flagged: tuple = ()     # Artifact, the most given first
    deepest: tuple = ()     # (the two bodies, metres): the pair that sank deepest into each other, () if none touched

    @property
    def clean(self):
        return not self.flagged

    def brief(self):
        """The check in two short lines at most, for the window's narrow panel; () before anything touched."""
        if not self.touches:
            return ()
        if self.clean:
            return ('physics check: nothing from nowhere',)
        a = self.flagged[0]
        short = [b.split('/', 1)[-1].replace('_', ' ') for b in a.bodies]
        return (f'energy from nowhere at {a.at:.1f} s: {1000 * a.gave:.1f} mJ', f'{short[0]} / {short[1]}')

    def line(self):
        """The check in one line, for a run report."""
        if not self.touches:
            return 'Physics check: nothing touched'
        if self.clean:
            return f'Physics check: no contact gave back more than it took ({_touches(self.touches)})'
        more = f' (and {len(self.flagged) - 1} more)' if len(self.flagged) > 1 else ''
        return f'Physics check: energy from nowhere - {self.flagged[0].said()}{more}'


def _touches(n):
    return f'{n} touch' + ('' if n == 1 else 'es')


def _name(body):
    """A body as a report names it: 'objects/fetch_cube' -> 'fetch cube', 'field/curb_10mm' -> 'curb 10mm',
    'machine/swivel_caster_2_wheel' -> 'machine's swivel caster 2 wheel'."""
    entity, _, rest = body.partition('/')
    if entity == 'machine' and rest:
        return "machine's " + rest.replace('_', ' ')
    return (rest or body).replace('_', ' ')


def _whole(body):
    """What a push on `body` lifts, as a report names it: the machine for any of its parts."""
    return 'the machine' if body.startswith('machine/') else 'the ' + _name(body)


class Watch:
    """Follows every contact through a run: call `update` after each step."""

    def __init__(self):
        self.live = {}          # (body, body) -> [began, work, most, when, deepest, allowed, lighter]
        self.touches = 0
        self.pairs = set()
        self.masses = {}        # body -> kg it sets moving, None if fixed
        self.flagged = []
        self.worst = 0.
        self.deepest = ((), 0.)

    def allowed(self, backend, pair):
        """What lifting the lighter of the pair GIVE takes, J, and what that lighter one is called."""
        masses = []
        for body in pair:
            if body not in self.masses:
                self.masses[body] = backend.moving_mass(body)
            if self.masses[body]:
                masses.append((self.masses[body], body))
        if not masses:
            return float('inf'), ''
        mass, body = min(masses)
        return mass * G * GIVE, _whole(body)

    def update(self, backend, time):
        seen = set()
        for first, second, joules, depth in backend.contact_work():
            pair = (first, second)
            seen.add(pair)
            touch = self.live.get(pair)
            if touch is None:
                touch = self.live[pair] = [time, 0., 0., time, 0., *self.allowed(backend, pair)]
                self.touches += 1
                self.pairs.add(pair)
            touch[1] += joules
            if touch[1] > touch[2]:
                touch[2], touch[3] = touch[1], time
            if depth > touch[4]:
                touch[4] = depth
                if depth > self.deepest[1]:
                    self.deepest = (pair, depth)
        for pair in [p for p in self.live if p not in seen]:
            self._parted(pair)

    def _parted(self, pair):
        touch = self.live.pop(pair)
        self.worst = max(self.worst, touch[2] / touch[5])
        if touch[2] > touch[5]:
            self.flagged.append(_artifact(pair, touch))

    def result(self):
        """The check so far; touches still going are judged as they stand."""
        worst, flagged = self.worst, list(self.flagged)
        for pair, touch in self.live.items():
            worst = max(worst, touch[2] / touch[5])
            if touch[2] > touch[5]:
                flagged.append(_artifact(pair, touch))
        return Checked(self.touches, len(self.pairs), worst, tuple(sorted(flagged, key=lambda a: -a.gave / a.allowed)),
                       self.deepest if self.deepest[0] else ())


def _artifact(pair, touch):
    began, _, most, when, deepest, allowed, lighter = touch
    return Artifact(pair, began, when, most, allowed, deepest, lighter)


def summary(checks):
    """Over runs (one Checked each): (runs checked, runs flagged, the worst share, the artifacts)."""
    checks = [c for c in checks if c is not None]
    flagged = [c for c in checks if not c.clean]
    return (len(checks), len(flagged), max((c.worst for c in checks), default=0.),
            tuple(a for c in flagged for a in c.flagged))


def lines(checks):
    """A report's lines on its runs' physics check (FR-040)."""
    n, k, worst, artifacts = summary(checks)
    if not n:
        return []
    if not k:
        return ['', f'Physics check (FR-040): in {n} of {n} runs no contact gave back more energy than it took - '
                    f'the most any came to was {worst:.0%} of lifting the lighter body {1000 * GIVE:.0f} mm.']
    out = ['', f'Physics check (FR-040): in {k} of {n} runs a contact gave back more energy than it took - the '
               'engine making energy, not physics. Read those runs\' results with that in mind:']
    for a in sorted(artifacts, key=lambda a: -a.gave / a.allowed)[:5]:
        out.append(f'- {a.said()}; their deepest contact sank {1000 * a.deepest:.1f} mm in')
    return out
