"""Search for the failure, not only sample it: a falsifier over the sourced ranges (FR-025).

Drawn set-ups certify a rate (ADR 0028, 0049) but do not say where failures live; a search that
follows a run's margin towards zero can find one in fewer runs (arXiv 2610.06862: a guided search
found failures more often than an unguided one, and they transferred to the real robot). The box
searched is the variation ranges' own (ADR 0024): where the machine is set down (x, y), how far it
is turned, the payload it carries and where across its deck, the friction of every sourced pair.

A run's margin says how far it stayed from failing, 0 at the edge, below it a failure:

- Fetch: what the tuning draws certified (ADR 0049) - each measure of how the cube was handled
  (ADR 0040) that does harm when it grows, at most as large as any tuning draw had it: the table's
  and the bin's push on the cube, in a step and over 50 ms, how far it leaned and how far it fell,
  and the squeeze within its range either way - as a share of that measure's spread over the
  draws (at least its report's precision); and a goal missed is a failure outright.
- the tilt table: how many degrees past its last hold (50 degrees) the machine tipped.

The search is a compass search, deterministic: from the design as designed - known before any
draw, as a random sampler knows nothing either - each coordinate a step either way, two runs at a
time, a move kept when it lowers the margin, the step halved when no move along any coordinate
does, until a failure is found, the budget is spent or the step is a sixteenth of the range. (Not
from the worst tuning draw: against what the tuning draws certified, the worst of them stands on
the edge by construction.)

The reading is standard library; running is MuJoCo-bound, through the sweep's run.
`python -m little_world.inventory.falsify`.
"""
from dataclasses import dataclass

from little_world.fields.variation import Ranges, Variation

NAMES = ('x', 'y', 'yaw', 'payload', 'at', 'friction')
LAST_HOLD = 50.         # degrees: the tilt table's last hold a machine can meet before 60 (fields.tilt_goals)
LEAST = 1 / 16          # the smallest step, as a share of each coordinate's half-range
HARM = ('force from the table, in a step', 'force from the table, over 50 ms', 'force from the bin, in a step',
        'force from the bin, over 50 ms', 'leaned from how it stood', 'leaned before it was held',
        'leaning when it came to rest', 'fell when let go')
SQUEEZE = 'force from the machine, over 50 ms'


def box(ranges=Ranges()):
    """The searched box: (name, least, most) per coordinate, in the variation's own units."""
    return (('x', -ranges.place, ranges.place), ('y', -ranges.place, ranges.place), ('yaw', -ranges.turn, ranges.turn),
            ('payload', 0., ranges.payload), ('at', -ranges.shift, ranges.shift),
            ('friction', -ranges.friction, ranges.friction))


def point(variation):
    """A variation as a point of the box: (x, y, yaw, payload, at, friction)."""
    return (variation.x, variation.y, variation.yaw, variation.payload, variation.at[1], variation.friction)


def variation(at, label='searched'):
    """The variation at a point of the box."""
    x, y, yaw, payload, side, friction = at
    return Variation(label, x=x, y=y, yaw=yaw, payload=payload, at=(0., side), friction=friction)


def _resolution(label):
    return .01 if label.startswith('force') else .1 if label.startswith('lean') else .001


def envelope(runs):
    """What the tuning draws certified, from their runs: {measure: (least, most)} over the handled
    part's measures (ADR 0040), as ADR 0049 reads a held-out sweep against them."""
    from little_world.inventory.handling import summary
    handled = [r.handled[0] for r in runs if r.handled]
    return {label: (low, high) for label, _, low, high in summary(handled)}


def fetch_margin(run, certified, only=None):
    """(margin, the measure that set it) for a Fetch run against what the tuning draws certified;
    `only`, one measure's label, to read that one alone."""
    if run.error or not all(x.status in ('met', 'kept') for x in run.results):
        return -1., 'a goal missed'
    if not run.handled:
        return -1., 'nothing handled'
    from little_world.inventory.handling import summary
    values = {label: mid for label, mid, _, _ in summary([run.handled[0]])}
    found = []
    for label in HARM + (SQUEEZE,):
        if label not in values or label not in certified or only not in (None, label):
            continue
        low, high = certified[label]
        step = _resolution(label)
        width = max(high - low, step)
        # The edge is where ADR 0049 calls a value outside: beyond the certified one at the
        # report's precision - half a step past it, rounded.
        top = round(high / step) * step + step / 2
        found.append(((top - values[label]) / width, label))
        if label == SQUEEZE:
            found.append(((values[label] - (round(low / step) * step - step / 2)) / width, label + ', the least'))
    return min(found) if found else (1., 'nothing to measure')


def tilt_margin(run, certified=None):
    """(margin, why) for a tilt-table run: degrees past its last hold that it tipped."""
    if run.error or run.tipped is None:
        return -1., 'did not tip' if not run.error else run.error
    return run.tipped - LAST_HOLD, 'tipped'


MARGINS = {'fetch': fetch_margin, 'tilt': tilt_margin}


@dataclass(frozen=True)
class Tried:
    """One set-up the search ran."""
    at: tuple
    margin: float
    why: str
    step: float         # the step it was tried at; 0 for the start


def _clip(value, low, high):
    return min(high, max(low, value))


def inert(at, i):
    """Whether moving coordinate `i` of the box at point `at` changes nothing: where a payload sits
    when there is none."""
    return NAMES[i] == 'at' and not at[NAMES.index('payload')]


def search(measure, start, limits, budget=40, step=.5, stop=True, jobs=2, still=lambda at, i: False):
    """The compass search: `measure(points)` -> [(margin, why), ...] runs a batch of points, `start`
    the point to begin from, `limits` the box; `still(point, i)`, whether moving coordinate i there
    changes nothing (`inert` for the variation box), so is not tried. Returns the set-ups tried, in
    order."""
    tried = []

    def ask(points):
        out = measure(points)
        tried.extend(Tried(p, m, w, s) for p, (m, w), s in zip(points, out, [size] * len(points)))
        return out
    size = 0.
    best = tuple(start)
    (low_margin, _), = ask([best])
    size = step
    while len(tried) < budget and size >= LEAST - 1e-12 and not (stop and low_margin < 0):
        moved = False
        for i, (_, low, high) in enumerate(limits):
            if len(tried) >= budget or (stop and low_margin < 0):
                break
            half = (high - low) / 2
            if not half or still(best, i):
                continue
            candidates = []
            for sign in (-1, 1):
                p = list(best)
                p[i] = _clip(best[i] + sign * size * half, low, high)
                if tuple(p) != best and tuple(p) not in [t.at for t in tried]:
                    candidates.append(tuple(p))
            candidates = candidates[:max(0, budget - len(tried))]
            if not candidates:
                continue
            for p, (m, _) in zip(candidates, ask(candidates)):
                if m < low_margin - 1e-9:
                    best, low_margin, moved = p, m, True
        if not moved:
            size /= 2
    return tuple(tried)


def drawn_margins(runs, margin, certified=None):
    """Random draws read as the search's runs are: (draws, the draw - counted from 1 - that first
    failed or None, the lowest margin)."""
    margins = [margin(r, certified)[0] for r in runs]
    failed = next((k + 1 for k, m in enumerate(margins) if m < 0), None)
    return len(margins), failed, min(margins)


def first_failure(tried):
    """The run (counted from 1) at which the search first found a failure, or None."""
    return next((k + 1 for k, t in enumerate(tried) if t.margin < 0), None)


def describe(at):
    """A point of the box as a report says it."""
    x, y, yaw, payload, side, friction = at
    return (f'x {100 * x:+.1f} cm, y {100 * y:+.1f} cm, turned {yaw:+.1f} deg, {payload:.2f} kg '
            f'{100 * side:+.1f} cm across, friction {friction:+.2f}')


def markdown(field, tried, baseline=None, title=None):
    """A search as a short report; `baseline`, (draws, the draw that first failed or None, the lowest
    margin among the draws)."""
    best = min(tried, key=lambda t: t.margin)
    found = first_failure(tried)
    lines = [f'## {title or field}: searching for the failure', '',
             f'{len(tried)} runs of the compass search, from the start below; a margin under 0 is a failure.', '',
             '| Run | Step | Set-up | Margin | Set by |', '| --- | --- | --- | --- | --- |']
    for k, t in enumerate(tried):
        mark = ' **failure**' if t.margin < 0 else ''
        lines.append(f'| {k + 1} | {t.step:g} | {describe(t.at)} | {t.margin:+.2f}{mark} | {t.why} |')
    lines += ['', f'The lowest margin: {best.margin:+.2f} ({best.why}), at {describe(best.at)}.']
    lines.append(f'The first failure: run {found}.' if found else f'No failure in {len(tried)} runs.')
    if baseline is not None:
        draws, failed, lowest = baseline
        lines.append(f'Drawn at random instead: {draws} draws, ' +
                     (f'the first failure at draw {failed}' if failed else 'no failure') +
                     f'; their lowest margin {lowest:+.2f}.')
    return '\n'.join(lines) + '\n'


# -- running (MuJoCo) --------------------------------------------------------------------------------

def _one(args):
    from little_world.inventory.sweep import run
    field_id, bp, at, program, site = args
    return run(field_id, bp, variation(at), program, site)


def runner(field_id, bp, certified=None, jobs=2, keep=None):
    """`measure` for `search`: each point run in the field, `jobs` at a time, and its margin; every run
    appended to `keep`, a list, if given."""
    from little_world.inventory.sweep import PROTOCOLS, shared_site, solve
    program = solve(field_id, bp) if PROTOCOLS[field_id][0] == 'program' else None
    margin = MARGINS[field_id]

    def measure(points):
        site = shared_site(bp, [Variation(payload=Ranges().payload)])
        work = [(field_id, bp, p, program, site) for p in points]
        if jobs > 1 and len(work) > 1:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(min(jobs, len(work))) as pool:
                runs = list(pool.map(_one, work))
        else:
            runs = [_one(w) for w in work]
        if keep is not None:
            keep.extend(runs)
        return [margin(r, certified) for r in runs]
    return measure


def main(argv=None):
    import argparse
    from pathlib import Path
    from little_world.inventory.sweep import design, drawn, from_json
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.falsify',
                                     description='Search the variation box for the failure (FR-025).')
    parser.add_argument('field', choices=sorted(MARGINS))
    parser.add_argument('--tuning', required=True, help="the field's tuning sweep's JSON (`sweep --json`): for Fetch, "
                                                         'what its draws certified')
    parser.add_argument('--draws', help='a sweep of random draws to read beside the search (a held-out sweep\'s JSON)')
    parser.add_argument('--design', default='mobile_manipulator')
    parser.add_argument('--budget', type=int, default=40)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    if args.budget < 1:
        parser.error('--budget is a number of runs, 1 or more')
    try:
        tuning = from_json(Path(args.tuning).read_text(encoding='utf-8'))
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    if tuning.field != args.field:
        parser.error(f'the tuning sweep is of {tuning.field}, not {args.field}')
    certified = envelope(drawn(tuning)) if args.field == 'fetch' else None
    margin = MARGINS[args.field]
    baseline = None
    if args.draws:
        try:
            baseline = drawn_margins(drawn(from_json(Path(args.draws).read_text(encoding='utf-8'))), margin, certified)
        except (OSError, ValueError, KeyError) as error:
            parser.error(str(error))
    tried = search(runner(args.field, design(args.design), certified, args.jobs), point(Variation()),
                   box(tuning.ranges), args.budget, still=inert)
    text = markdown(args.field, tried, baseline, title=f'{args.field}, from the design as designed')
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
