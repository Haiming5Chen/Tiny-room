"""A cell judged as a factory judges one: where each part landed and how long it took (ADR 0056, FR-029).

A production run (ADR 0019) counted the parts placed. A line asks two more things of a cell: that
each part lands within its fixture's tolerance zone, and that none takes longer than the takt - the
available production time divided by the demand (Lean Enterprise Institute, Lean Lexicon, "takt
time"). How capable a process is of a zone is its Cpk = min(USL - mean, mean - LSL) / (3 sigma), at
least 1 wanted; its approximate 95 % interval, z * sqrt(1 / 9n + Cpk^2 / 2(n - 1)), is valid from
about 25 values (NIST/SEMATECH e-Handbook of Statistical Methods, 6.1.6).

Here the zone is the room a part has in its slot of the destination tray: the slots' pitch less the
part's width, half each way - closer to a neighbouring slot than that and two parts touch. A cell's
own repeatability is the Franka Panda's datasheet's, +-0.1 mm (ISO 9283).

Standard library only.
"""
from dataclasses import dataclass
from math import hypot, inf, sqrt
from statistics import NormalDist, mean, stdev

REPEATABILITY = .1      # mm: the Franka Panda's pose repeatability, ISO 9283 (its datasheet)
VALID = 25              # values from which the e-Handbook's interval for Cpk is valid
AXES = ('x', 'y', 'yaw')


@dataclass(frozen=True)
class Placement:
    """One part as it was left: from the centre of its slot (mm, along the table's x and y), turned
    from square to the tray (degrees; a square part, within +-45), and its cycle (s): from its
    plan's start to its placement checked."""
    part: int
    dx: float
    dy: float
    yaw: float
    seconds: float

    @property
    def off(self):
        """mm from the centre of its slot."""
        return hypot(self.dx, self.dy)

    def value(self, axis):
        return {'x': self.dx, 'y': self.dy, 'yaw': self.yaw}[axis]


def room(pitch, width):
    """mm a part may stray from its slot's centre before it touches the next slot's part, given
    the slots' pitch and the part's width along the same axis (mm)."""
    if width >= pitch:
        raise ValueError(f'a part {width:g} mm wide does not fit slots {pitch:g} mm apart')
    return (pitch - width) / 2


def turn_room(pitch, width):
    """Degrees a square part `width` mm across, centred in its slot, may turn before a corner
    reaches the next slot's part (`pitch` mm away): its half-width grows as cos + sin of the turn;
    45 if no turn reaches it."""
    from math import asin, degrees, sqrt as root
    reach = pitch / (width * root(2))
    return 45. if reach >= 1 else degrees(asin(reach)) - 45.


def slot_room(slots, width):
    """(x, y, turn): the room a square part `width` mm across has in a tray's slots, `slots` the
    slots' centres (m, from the tray's centre): along each axis half the pitch less the part's
    width (inf for a single row), and the turn that reaches the nearer neighbour."""
    def pitch(values):
        values = sorted({round(1000 * v, 3) for v in values})
        return min(b - a for a, b in zip(values, values[1:])) if len(values) > 1 else inf
    px, py = pitch(x for x, _ in slots), pitch(y for _, y in slots)
    return (room(px, width) if px < inf else inf, room(py, width) if py < inf else inf,
            turn_room(min(px, py), width))


def capability(values, half):
    """Cpk of `values` against a zone of +-`half` round 0 and its approximate 95 % interval, None
    below VALID values; inf for values that do not vary."""
    values = tuple(values)
    if len(values) < 2:
        raise ValueError('Cpk needs at least two values')
    m, s = mean(values), stdev(values)
    if s == 0:
        return (inf if abs(m) < half else 0.), None
    cpk = min(half - m, m + half) / (3 * s)
    if len(values) < VALID:
        return cpk, None
    n = len(values)
    w = NormalDist().inv_cdf(.975) * sqrt(1 / (9 * n) + cpk * cpk / (2 * (n - 1)))
    return cpk, (cpk - w, cpk + w)


@dataclass(frozen=True)
class Window:
    """What placements say against a zone (mm each way along x and y; degrees each way turned) and
    a takt (s)."""
    n: int
    inside: int             # parts inside the zone on every axis
    worst: float            # mm, the farthest a part landed from its slot's centre
    worst_turn: float       # deg
    slowest: float          # s, the longest cycle
    late: int               # cycles longer than the takt
    cpk: tuple              # (axis, Cpk, interval or None) for x, y and yaw
    bias: tuple             # mm: the mean placement along x and y

    def capable(self):
        """Whether every axis's Cpk is at least 1, the e-Handbook's 'at least' (inf counts)."""
        return all(c >= 1 for _, c, _ in self.cpk)


def judge(placements, zone, turn, takt=inf):
    """A run's or a study's placements against a zone of +-zone (x, y; mm, a pair) and +-turn
    (deg), and a takt (s)."""
    placements = tuple(placements)
    if not placements:
        raise ValueError('no placements to judge')
    zx, zy = zone
    halves = {'x': zx, 'y': zy, 'yaw': turn}
    inside = sum(abs(p.dx) <= zx and abs(p.dy) <= zy and abs(p.yaw) <= turn for p in placements)
    cpk = tuple((a, *capability([p.value(a) for p in placements], halves[a])) for a in AXES) \
        if len(placements) > 1 else ()
    return Window(len(placements), inside, max(p.off for p in placements), max(abs(p.yaw) for p in placements),
                  max(p.seconds for p in placements), sum(p.seconds > takt for p in placements), cpk,
                  (mean(p.dx for p in placements), mean(p.dy for p in placements)))


def tightest(placements, zones, share=.99):
    """The tightest of `zones` (mm, each way, on x and y alike) that at least `share` of the
    placements land inside, with a Clopper-Pearson lower bound on the share at 95 % (one-sided),
    as (zone, inside, n, lower) - or None if none does."""
    placements = tuple(placements)
    n = len(placements)
    for zone in sorted(zones):
        k = sum(abs(p.dx) <= zone and abs(p.dy) <= zone for p in placements)
        if k / n >= share:
            return zone, k, n, lower_bound(k, n)
    return None


def lower_bound(k, n, confidence=.95):
    """The one-sided Clopper-Pearson lower bound on a share seen as k of n: the share p at which k
    or more of n would come up with probability 1 - confidence (bisection on the binomial tail)."""
    if not 0 <= k <= n or n < 1:
        raise ValueError('k of n with 0 <= k <= n')
    if k == 0:
        return 0.
    from math import comb
    tail = lambda p: sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    lo, hi = 0., 1.
    for _ in range(60):
        mid = (lo + hi) / 2
        if tail(mid) < 1 - confidence:
            lo = mid
        else:
            hi = mid
    return lo


def line(window, zone):
    """The factory panel's line for a run: how many landed with room to spare, how far off the
    worst was against the room it had, and the slowest part."""
    zx, zy = zone
    return (f'{window.inside} of {window.n} placed within their room  /  worst {window.worst:.1f} mm off '
            f'(room {min(zx, zy):.1f} mm)  /  slowest part {window.slowest:.1f} s')
