"""How far a design can go: where its success crosses one half along one factor (FR-042).

A field answers whether a design passed, and how often, at the field's own settings: the Curb run's
three curbs, the tilt table's angle. A boundary answers how far it can go: the factor stepped along a
grid - a curb's height, a table's angle - each level run on the same draws of the other varied things
(ADR 0024's box, one seed), and the level at which the rate of success falls through one half, with
an interval. A study of driving agents read failure this way, one measured factor a family, and found
where agents stop trying apart from where they stop succeeding (arXiv 2611.06453); a field whose
machine has no choice - driven at a curb, it drives - has only the second.

- Each level: the runs that met the field's goals of `tried`, with an exact 95 % interval (ADR 0028).
- The rates fitted to fall monotonically with the factor - pooled where a higher level did better than
  a lower one (pool-adjacent-violators, weighted by runs) - and the crossing of one half found between
  the two levels it falls between, linearly; None when it is not crossed within the grid.
- The crossing's interval from resampling each level's draws with replacement (a bootstrap of `REPEATS`
  with a seed of its own, recorded), the 2.5th and 97.5th percentiles; resamples that do not cross
  within the grid are counted, not dropped.

Standard library only; the runs come from `inventory.sweep` (`boundary_runs`).
"""
import random
from dataclasses import dataclass

from little_world.inventory.confidence import interval as rate_interval

AT = .5
REPEATS = 2000


@dataclass(frozen=True)
class Level:
    """One step of the factor: its value, and each draw's outcome there (label, met)."""
    value: float
    outcomes: tuple = ()

    @property
    def met(self):
        return sum(1 for _, ok in self.outcomes if ok)

    @property
    def tried(self):
        return len(self.outcomes)

    @property
    def rate(self):
        return self.met / self.tried if self.tried else float('nan')


def monotone(levels, falling=True):
    """The rates fitted to fall (or rise) with the factor: pool-adjacent-violators, weighted by runs.
    One fitted rate a level, in the levels' order."""
    blocks = []                                     # [rate, weight, count]
    for level in levels:
        blocks.append([level.rate, level.tried, 1])
        while len(blocks) > 1 and ((blocks[-2][0] < blocks[-1][0]) if falling else (blocks[-2][0] > blocks[-1][0])):
            r2, w2, n2 = blocks.pop()
            r1, w1, n1 = blocks.pop()
            w = w1 + w2
            blocks.append([(r1 * w1 + r2 * w2) / w if w else 0., w, n1 + n2])
    fitted = []
    for rate, _, count in blocks:
        fitted += [rate] * count
    return tuple(fitted)


def crossing(values, fitted, at=AT):
    """Where the fitted rate falls through `at`, by straight lines between levels; None if it does not
    within the grid (above it all the way, or below it from the first level)."""
    for (v1, r1), (v2, r2) in zip(zip(values, fitted), zip(values[1:], fitted[1:])):
        if r1 >= at > r2:
            return v1 + (v2 - v1) * (r1 - at) / (r1 - r2)
    return None


@dataclass(frozen=True)
class Profile:
    """A design's boundary along one factor."""
    field: str
    factor: str
    unit: str
    levels: tuple
    fitted: tuple
    at: float | None                # where success falls through one half; None if not within the grid
    low: float | None               # its 95 % interval, from the bootstrap
    high: float | None
    beyond: int = 0                 # bootstrap resamples that did not cross within the grid
    repeats: int = REPEATS
    seed: int = 1                   # the bootstrap's
    draws_seed: int | None = None   # the draws' (ADR 0049)

    def pooled(self):
        """Where the fit had to pool: (first value, last value) of each run of levels in which a higher one
        did better than a lower one - success not falling with the factor there."""
        out, i = [], 0
        while i < len(self.levels):
            j = i
            while j + 1 < len(self.levels) and self.fitted[j + 1] == self.fitted[i]:
                j += 1
            if j > i and any(self.levels[k].rate < self.levels[k + 1].rate for k in range(i, j)):
                out.append((self.levels[i].value, self.levels[j].value))
            i = j + 1
        return tuple(out)

    def line(self):
        """'Curb height: 50 % at 19.3 mm, 95 % between 17.6 and 21.0 mm.'"""
        name = self.factor[:1].upper() + self.factor[1:]
        pooled = ''.join(f' From {_n(a)} to {_n(b)} {self.unit} a higher level did better than a lower one: pooled.'
                         for a, b in self.pooled())
        if self.at is None:
            above = all(r >= AT for r in self.fitted)
            return (f'{name}: {"above" if above else "below"} one half over the whole grid, '
                    f'{_n(self.levels[0].value)} to {_n(self.levels[-1].value)} {self.unit}.' + pooled)
        spread = ('' if self.low is None or self.high is None else
                  f', 95 % between {_n(self.low)} and {_n(self.high)} {self.unit}')
        beyond = f' ({self.beyond} of {self.repeats} resamples did not cross within the grid)' if self.beyond else ''
        return f'{name}: 50 % at {_n(self.at)} {self.unit}{spread}{beyond}.' + pooled


def _n(x):
    return f'{x:.1f}' if abs(x) < 100 else f'{x:.0f}'


def profile(field, factor, unit, levels, seed=1, repeats=REPEATS, draws_seed=None):
    """The boundary from the levels' outcomes, its interval by resampling each level's draws."""
    levels = tuple(sorted(levels, key=lambda level: level.value))
    values = [level.value for level in levels]
    fitted = monotone(levels)
    at = crossing(values, fitted)
    rng = random.Random(seed)
    found, beyond = [], 0
    for _ in range(repeats):
        resampled = [Level(level.value, tuple(rng.choice(level.outcomes) for _ in level.outcomes)) for level in levels]
        x = crossing(values, monotone(resampled))
        if x is None:
            beyond += 1
        else:
            found.append(x)
    found.sort()
    low = found[int(.025 * len(found))] if found and at is not None else None
    high = found[min(len(found) - 1, int(.975 * len(found)))] if found and at is not None else None
    return Profile(field, factor, unit, levels, fitted, at, low, high, beyond, repeats, seed, draws_seed)


def markdown(p, title=''):
    """A profile as a short report: one row a level."""
    lines = [f'# {title or p.field}: {p.factor}', '', p.line(), '',
             f'| {p.factor[:1].upper() + p.factor[1:]}, {p.unit} | Met every goal | 95 % interval | Fitted |',
             '| --- | --- | --- | --- |']
    for level, f in zip(p.levels, p.fitted):
        lo, hi = rate_interval(level.met, level.tried) if level.tried else (0., 1.)
        lines.append(f'| {_n(level.value)} | {level.met} of {level.tried} | {100 * lo:.0f} to {100 * hi:.0f} % | {100 * f:.0f} % |')
    lines += ['', f'Each level on the same {p.levels[0].tried} draws' + (f' (seed {p.draws_seed})' if p.draws_seed is not None else '')
              + f'; the interval from {p.repeats} resamples of each level\'s draws (seed {p.seed}).']
    return '\n'.join(lines) + '\n'


# -- the runs --------------------------------------------------------------------------------------

def _curb(value):
    from little_world.fields import curb_run
    return curb_run((value / 1000.,))


# factor: (the field whose protocol and ranges it uses, its unit, the field at a value, what it is called)
FACTORS = {'curb': ('curbs', 'mm', _curb, 'curb height')}


def _one(job):
    factor, value, design, variation, site, duration, multiccd = job
    from little_world.inventory import sweep
    from little_world.physics import mujoco_backend
    mujoco_backend.MULTICCD = multiccd          # a study's one setting changed (LW-047); off as everywhere else
    field_id, _, build, _ = FACTORS[factor]
    run = sweep.run(field_id, sweep.design(design), variation, site=site, field=build(value), duration=duration)
    return value, variation.label, not run.error and all(x.status in ('met', 'kept') for x in run.results)


def levels(factor, values, design, samples=8, seed=1, duration=None, jobs=1, progress=None, multiccd=False):
    """Each value of the factor run on the same draws - the design as designed and `samples` drawn
    within the field's ranges with `seed` - for `duration` seconds of the field's protocol; one Level a
    value, each draw met when every goal of the varied field was. `multiccd` runs them with MuJoCo's
    multiccd on, the one setting a study of LW-047 changes; the project's own runs have it off (ADR 0027)."""
    from little_world.fields.variation import plan
    from little_world.inventory import sweep
    field_id = FACTORS[factor][0]
    drawn = [v for v in plan(sweep.ranges_for(field_id), samples, seed) if v.nominal or v.label.startswith('repeat')]
    site = sweep.shared_site(sweep.design(design), drawn)
    work = [(factor, value, design, v, site, duration, multiccd) for value in values for v in drawn]
    outcomes = {value: [] for value in values}
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            for i, (value, label, ok) in enumerate(pool.map(_one, work)):
                outcomes[value].append((label, ok))
                if progress:
                    progress(i + 1, len(work), value, label, ok)
    else:
        for i, job in enumerate(work):
            value, label, ok = _one(job)
            outcomes[value].append((label, ok))
            if progress:
                progress(i + 1, len(work), value, label, ok)
    return tuple(Level(value, tuple(outcomes[value])) for value in values)


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.boundary',
                                     description="Where a design's success crosses one half along one factor (FR-042).")
    parser.add_argument('factor', choices=sorted(FACTORS))
    parser.add_argument('first', type=float)
    parser.add_argument('last', type=float)
    parser.add_argument('step', type=float)
    parser.add_argument('--design', default='mobile_platform')
    parser.add_argument('--samples', type=int, default=8, help='draws besides the design as designed (default 8)')
    parser.add_argument('--seed', type=int, default=1, help="the draws' seed (default 1, the tuning draws)")
    parser.add_argument('--seconds', type=float, default=None, help="how long each run lasts (default: the field's own)")
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--multiccd', action='store_true', help="MuJoCo's multiccd on, for a study (off everywhere else, ADR 0027)")
    parser.add_argument('--out', help='write the report here, and its outcomes beside it as .json')
    args = parser.parse_args(argv)
    count = int(round((args.last - args.first) / args.step)) + 1
    values = [round(args.first + i * args.step, 6) for i in range(count)]
    field_id, unit, _, name = FACTORS[args.factor]
    found = levels(args.factor, values, args.design, args.samples, args.seed, args.seconds, args.jobs,
                   lambda i, n, value, label, ok: print(f'{i}/{n} {value:g} {unit} {label}: {"met" if ok else "missed"}', flush=True),
                   args.multiccd)
    p = profile(field_id, name, unit, found, draws_seed=args.seed)
    text = markdown(p, f'{args.design} on the {field_id} field' + (', multiccd on' if args.multiccd else ''))
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        Path(args.out).with_suffix('.json').write_text(json.dumps([[level.value, level.outcomes] for level in found]),
                                                       encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
