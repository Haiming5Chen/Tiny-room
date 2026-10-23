"""The latency margin: how late a program's pictures, commands and readings may be and its results
hold (FR-028).

In a lab time passes while a program looks and moves: a depth frame reaches it after it was
exposed, the finder takes its time, every servo command and reading crosses the bus
(`control/latency.py`). A sweep at each latency - the same set-ups, undisturbed and under the same
disturbances, every path that late - is read beside the sweep without: per latency and
disturbance, the set-ups meeting every goal, those broken by the latency (met without it, missed
with it: the two are one run until the first late picture, command or reading, ADR 0036), and how
much later the last goal was met. The margin is the largest latency tried at which none was broken.

MuJoCo-bound through the sweeps; the reading is standard library.
`python -m little_world.inventory.margin`.
"""
from statistics import median

from little_world.control.latency import Latency, sourced

LATENCIES = 'sourced,0.2,0.3,0.4,0.5'


def parse(text):
    """'sourced' or seconds on every path, comma separated: ((label, Latency), ...)."""
    out = []
    for item in (t.strip() for t in text.split(',') if t.strip()):
        if item == 'sourced':
            out.append(('sourced', sourced()))
            continue
        try:
            seconds = float(item)
        except ValueError:
            raise ValueError(f"a latency is seconds or 'sourced', not {item!r}") from None
        out.append((f'{seconds:g} s', Latency.every(seconds)))
    if not out:
        raise ValueError('name at least one latency')
    return tuple(out)


def _met(run):
    return not run.error and all(x.status in ('met', 'kept') for x in run.results)


def _last(run):
    times = [x.time for x in run.results if x.time is not None]
    return max(times) if _met(run) and times else None


def cell(own, baseline):
    """One latency's runs of one disturbance against the same set-ups without latency: (met, runs,
    broken - met without and missed with it -, rescued, the median change of the last goal over
    the set-ups that met every goal both ways, or None)."""
    theirs = {r.variation.label: r for r in baseline}
    pairs = [(r, theirs[r.variation.label]) for r in own if r.variation.label in theirs]
    broken = sum(1 for a, b in pairs if _met(b) and not _met(a))
    rescued = sum(1 for a, b in pairs if _met(a) and not _met(b))
    changes = [_last(a) - _last(b) for a, b in pairs if _last(a) is not None and _last(b) is not None]
    return sum(_met(a) for a, _ in pairs), len(pairs), broken, rescued, median(changes) if changes else None


def rows(baseline, results):
    """Per latency, its cells: ((label, latency, ((disturbance, cell), ...)), ...), the
    disturbances in the baseline's order. `baseline` and each of `results` (label, Disturbed) are
    disturbed sweeps of the same set-ups."""
    base = {label: runs for label, _, runs in baseline.groups}
    out = []
    for label, result in results:
        mine = {g: runs for g, _, runs in result.groups}
        out.append((label, result.latency or Latency(),
                    tuple((g, cell(mine[g], base[g])) for g in base if g in mine)))
    return tuple(out)


def margin(table):
    """The largest latency, by its slowest path, at which no set-up was broken - and every smaller
    one tried held too - and the smallest at which one was: (holds, breaks), each a label or None."""
    holds = breaks = None
    for label, latency, cells in sorted(table, key=lambda row: max(row[1].picture, row[1].command, row[1].reading)):
        if any(c[2] for _, c in cells):
            breaks = breaks or label
        elif breaks is None:
            holds = label
    return holds, breaks


def _ms(seconds):
    return f'{1000 * seconds:.0f}' if seconds >= .0095 else f'{1000 * seconds:.1f}'


def markdown(baseline, results, field='Fetch'):
    table = rows(baseline, results)
    groups = [g for g, _, _ in baseline.groups]
    lines = [f'## {field}: results against latency', '',
             'Each latency on the same set-ups, undisturbed and under each disturbance, beside the sweep '
             'without latency: the set-ups that met every goal, those the latency broke (met without it, missed '
             'with it), and the median change in when the last goal was met. A latency is how late the program\'s '
             'pictures show the world, its commands reach the servos and its readings of them reach it.', '',
             '| Latency: pictures / commands / readings, ms | ' + ' | '.join(groups) + ' |',
             '| --- |' + ' --- |' * len(groups)]
    n = len(baseline.groups[0][2])
    base_met = {g: sum(_met(r) for r in runs) for g, _, runs in baseline.groups}
    lines.append('| none | ' + ' | '.join(f'{base_met[g]} of {n}' for g in groups) + ' |')
    for label, latency, cells in table:
        shown = dict(cells)
        row = []
        for g in groups:
            if g not in shown:
                row.append('-')
                continue
            met, runs, broken, rescued, change = shown[g]
            text = f'{met} of {runs}' + (f', {broken} broken' if broken else '') + (f', {rescued} rescued' if rescued else '')
            row.append(text + ('' if change is None else f'; {change:+.1f} s'))
        name = f'{label}: {_ms(latency.picture)} / {_ms(latency.command)} / {_ms(latency.reading)}'
        lines.append(f'| {name} | ' + ' | '.join(row) + ' |')
    holds, breaks = margin(table)
    lines += ['']
    if holds and breaks:
        lines.append(f'Every set-up held at {holds}; at {breaks} the latency broke some.')
    elif holds:
        lines.append(f'Every set-up held at every latency tried, up to {holds}.')
    elif breaks:
        lines.append(f'The latency broke some set-ups already at {breaks}.')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    import argparse
    from pathlib import Path
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, disturb
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.margin',
                                     description="How late a program's pictures, commands and readings may be (FR-028).")
    parser.add_argument('--latencies', default=LATENCIES, help=f"'sourced' or seconds on every path (default {LATENCIES})")
    parser.add_argument('--only', action='append', default=None, metavar='LABEL',
                        help="the Fetch field's disturbances to try (default: the cube moved 2 s later and the 6 N s shove)")
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    try:
        latencies = parse(args.latencies)
    except ValueError as error:
        parser.error(str(error))
    wanted = args.only or ['cube moved 5 cm sideways, 2 s later', 'shoved 6 N s at the table']
    known = {d.label: d for d in DEFAULTS['fetch']}
    if any(w not in known for w in wanted):
        parser.error('the Fetch field\'s disturbances are: ' + '; '.join(known))
    chosen = tuple(known[w] for w in wanted)
    bp = design('mobile_manipulator')
    baseline = disturb('fetch', bp, chosen, samples=args.samples, jobs=args.jobs)
    results = [(label, disturb('fetch', bp, chosen, samples=args.samples, jobs=args.jobs, latency=latency))
               for label, latency in latencies]
    text = markdown(baseline, results)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
