"""The knife-edge check (ADR 0043, FR-024): does a run's result survive a micrometre?

In MuJoCo one drawn set-up has exactly one outcome, so a sweep alone cannot tell a result the
design earns from one it happened on - a contact that does or does not open, a part that creeps
one way or the other. Each drawn set-up is run again, a few times, with the machine set down
within a micrometre and a hundred-thousandth of a radian of where it was: far below anything a
lab could place a machine to, and four orders of magnitude below the ranges a sweep draws from
(2 cm and 3 degrees, ADR 0024). A measure whose spread over those repeats is small against its
spread over the drawn set-ups is the design's; one that spreads as far under a micrometre as
across the set-ups is partly chance, and a report says so.

The repeats keep their set-up's label, so a program that looks draws the same camera noise
(ADR 0032): only the placement moves. Standard library only.
"""
from dataclasses import dataclass, replace
from math import degrees, inf
import random
from statistics import median

PLACE = 1e-6        # m: a repeat is set down up to this far off its set-up's own place, along X and along Y
TURN = 1e-5         # rad: and turned up to this far off its heading (0.00057 degrees)
REPEATS = 5         # repeats of each drawn set-up, besides its own run
ROBUST = .1         # a measure whose spread under a micrometre stays under this share of its spread
                    # across the drawn set-ups is taken as the design's (FR-024)


def jittered(variation, k, seed=1):
    """Repeat `k` (1, 2, ...) of a set-up: the same set-up under the same label, set down within
    PLACE and turned within TURN of it - drawn from `seed`, the label and `k`, so a repeat is the
    same every time it is made."""
    draw = random.Random(f'{seed}:{variation.label}:{k}')
    return replace(variation, x=variation.x + draw.uniform(-PLACE, PLACE),
                   y=variation.y + draw.uniform(-PLACE, PLACE),
                   yaw=variation.yaw + degrees(draw.uniform(-TURN, TURN)))


def measures(run):
    """What a run measured, by name: whether it met every goal (1 or 0), the time of its last
    goal, where a static test tipped, and how the part its goals carry was handled (ADR 0040,
    0042). Empty when it could not run."""
    if run.error:
        return {}
    out = {'every goal met': float(all(r.status in ('met', 'kept') for r in run.results))}
    times = [r.time for r in run.results if r.time is not None and r.status in ('met', 'kept')]
    if times:
        out['last goal met, s'] = max(times)
    if run.tipped is not None:
        out['tipped at, deg'] = run.tipped
    for h in run.handled[:1]:
        out['squeeze over 50 ms, N'] = h.of('steady', 'machine')
        out['table over 50 ms, N'] = h.of('steady', 'table')
        out['bin in a step, N'] = h.of('peak', 'bin')
        out['bin over 50 ms, N'] = h.of('steady', 'bin')
        if h.dropped is not None:
            out['fell when let go, cm'] = 100 * h.dropped
        out['leaned at most, deg'] = h.tilt
    return out


@dataclass(frozen=True)
class Edge:
    """One measure under jitter: how far a set-up's own run and its repeats spread (the median
    over the set-ups, and the most, with where), against how far the set-ups' own runs spread;
    and how many set-ups spread further than ROBUST of that under a micrometre."""
    measure: str
    within: float       # median over set-ups of (highest - lowest) among a set-up's runs
    most: float         # the largest of those ...
    where: str          # ... in this set-up
    across: float       # highest - lowest of the set-ups' own runs
    edges: int = 0      # set-ups whose runs spread further than ROBUST * across
    sets: int = 0       # set-ups measured

    @property
    def ratio(self):
        return self.within / self.across if self.across > 0 else (inf if self.within > 0 else 0.)

    @property
    def robust(self):
        return self.ratio < ROBUST


def groups(runs, repeats):
    """Each set-up's own run with its repeats: [(label, [own, repeat, ...])], in the order of
    `runs`; set-ups without a repeat are left out."""
    by = {}
    for r in repeats:
        by.setdefault(r.variation.label, []).append(r)
    return [(r.variation.label, [r, *by[r.variation.label]]) for r in runs if r.variation.label in by]


def edges(runs, repeats):
    """Every measure the runs share, as an Edge."""
    sets = groups(runs, repeats)
    out = []
    names = []
    for _, group in sets:
        for name in measures(group[0]):
            if name not in names:
                names.append(name)
    for name in names:
        spreads = []
        own = []
        for label, group in sets:
            values = [m[name] for m in map(measures, group) if name in m]
            if len(values) == len(group):
                spreads.append((max(values) - min(values), label))
                own.append(values[0])
        if not spreads:
            continue
        most = max(spreads, key=lambda s: s[0])
        across = max(own) - min(own)
        out.append(Edge(name, median(s for s, _ in spreads), most[0], most[1], across,
                        sum(1 for s, _ in spreads if s > ROBUST * across), len(spreads)))
    return out


def flips(runs, repeats):
    """The set-ups whose repeats did not all meet every goal or all miss one, as their own run did."""
    return [label for label, group in groups(runs, repeats)
            if len({measures(r).get('every goal met') for r in group}) > 1]


def lines(runs, repeats):
    """The report's section on the knife-edge check, as Markdown lines; [] without repeats."""
    sets = groups(runs, repeats)
    if not sets:
        return []
    n, k = len(sets), max(len(g) for _, g in sets) - 1
    flipped = flips(runs, repeats)
    looked = any(r.seen for _, g in sets for r in g)
    out = ['', '## Under a micrometre (ADR 0043)', '',
           f'Each of the {n} set-ups drawn at random run {k} times more, the machine set down within '
           f'{1e6 * PLACE:g} micrometre of where it was and turned within {degrees(TURN):.5f} degrees - the same '
           'set-up to any lab' + (', and the same camera noise. ' if looked else '. ')
           + (f'The outcome changed in {len(flipped)} of {n}: {", ".join(flipped)}.' if flipped else
              f'The outcome changed in none of the {n}.'),
           '', f'How far each measure spread among a set-up\'s {k + 1} runs (the median over set-ups, and the most), '
           f'against how far it spread across the {n} set-ups: under {ROBUST:g} of it, a measure is the design\'s; '
           'above, partly chance. And how many set-ups spread further than that under a micrometre: each one '
           'is a knife edge for that measure.', '',
           '| Measure | Under a micrometre (median) | Most, and where | Across set-ups | Share | Set-ups past a tenth | |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for e in edges(runs, repeats):
        if e.measure == 'every goal met':
            continue
        share = '-' if e.ratio == inf else f'{e.ratio:.2f}'
        verdict = 'the design\'s' if e.robust else 'partly chance'
        out.append(f'| {e.measure} | {_g(e.within)} | {_g(e.most)} ({e.where}) | {_g(e.across)} | {share} | '
                   f'{e.edges} of {e.sets} | {verdict} |')
    return out


def _g(v):
    return f'{v:.3g}'
