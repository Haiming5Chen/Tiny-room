"""A contact census: how many points carry each contact a result rests on (FR-030).

ADR 0027 turned MuJoCo's multiple-contact search (multiccd) off everywhere: on the kit's wheels
its extra contacts added a rolling loss of the engine's own, measured. MuJoCo collides most
pairs of shapes with a collider of their own - box on box, a sphere or a box on a plane - which
finds several points where two faces meet; a pair it has no collider for goes to its general
one (MPR), which finds one point unless multiccd is on. So a flat face could be held, or stand,
on a single point, its resistance to turning coming from that point alone - and the decisions
that rest on contact (the squeeze and creep of the jaws, ADR 0017 and 0042; the presses on the
table, ADR 0040 and 0041; the landing in the bin, ADR 0042; the casters, ADR 0041) would carry
that.

The census runs a field as designed and, at the moments its results are decided - the machine
standing at its start and at the table, the part held, carried and resting where it was set
down - counts for each pair of parts in contact the kinds of shape that touch and the points
between them, as the model is set and again with multiccd on (`MujocoBackend.contact_census`,
on copies of the instant). A pair whose count would change with multiccd is one the setting
decides; one whose count would not is not.

MuJoCo-bound, through the sweep's run; `python -m little_world.inventory.census`.
"""
import re

EVERY = 10          # steps between counts: 20 ms at the world's 2 ms step


def part(name):
    """What a census row calls a body: a machine's body without its numbered copies - each
    segment of a tread wheel's tyre is one 'tread_wheel_1_tyre' - and a field's or an
    object's by its own name."""
    entity, _, rest = name.partition('/')
    return f'{entity}/{re.sub(r"(_[0-9]+)+$", "", rest)}' if entity == 'machine' else name


def moments(run, start=0.):
    """The windows (label, from, to) of a Fetch run where its results are decided, from when
    its goals were met (seconds from `start`, when the run's goals began to be watched) and its
    grasp was checked; in the world's own time."""
    met = {r.id: start + r.time for r in run.results if r.time is not None}
    held = run.felt[0][0] if run.felt else None
    out = [('standing at the start', start, start + .4)]
    if 'reached' in met and held is not None:
        out.append(('standing at the table, reaching', met['reached'] + .5, held - .2))
    if held is not None:
        out.append(('held on the table', held, held + .3))
    if 'lifted' in met:
        out.append(('carried', met['lifted'], met['lifted'] + 2.))
    if 'delivered' in met:
        out.append(('resting where it was set down', met['delivered'], met['delivered'] + 1.))
    return tuple(out)


def take(field_id='fetch', design='mobile_manipulator'):
    """Run the field once as designed, counting contacts every EVERY steps: (the run, the
    counts [(time, {(a, b): (kinds, points, with multiccd)})], when its goals began to be
    watched)."""
    from little_world.inventory.sweep import design as made, run, solve
    bp = made(design)
    counts, step = [], [0]
    start = []

    def probe(state, backend):
        if not start:
            start.append(state.time)
        step[0] += 1
        if step[0] % EVERY == 0:
            counts.append((state.time, backend.contact_census()))
    result = run(field_id, bp, program=solve(field_id, bp), probe=probe)
    return result, counts, start[0]


def table(run, counts, start=0., keep=lambda a, b: True):
    """Rows (moment, pair, kinds, points as set (least, most), with multiccd (least, most)),
    the points summed over each pair of parts at each count, for the pairs `keep` passes."""
    rows = []
    for label, begin, end in moments(run, start):
        window = [c for t, c in counts if begin <= t <= end]
        if not window:
            continue
        pairs = {}
        for census in window:
            summed = {}
            for (a, b), (kinds, n, multi) in census.items():
                if not keep(a, b):
                    continue
                key = tuple(sorted((part(a), part(b))))
                k, n0, m0 = summed.get(key, (set(), 0, 0))
                summed[key] = (k | set(kinds), n0 + n, m0 + multi)
            for key, (kinds, n, multi) in summed.items():
                seen = pairs.setdefault(key, (set(), [], []))
                seen[0].update(kinds)
                seen[1].append(n)
                seen[2].append(multi)
        for key, (kinds, ns, ms) in sorted(pairs.items()):
            rows.append((label, key, tuple(sorted(kinds)), (min(ns), max(ns)), (min(ms), max(ms)), len(ns), len(window)))
    return rows


def carries(a, b):
    """The pairs the decisions rest on: the cube with anything, and the cart's wheels and casters
    on the floor."""
    names = a + ' ' + b
    return 'fetch_cube' in names or ('field/floor' in (a, b) and ('wheel' in names or 'caster' in names))


def markdown(run, counts, start=0.):
    rows = table(run, counts, start, carries)
    lines = ['# Contact census: Fetch, as designed', '',
             f'One run of the Fetch field as designed, its contacts counted every {EVERY} steps '
             f'({2 * EVERY} ms) at the moments its results are decided: for each pair of parts, the kinds of '
             'shape that touch, the contact points MuJoCo finds between them as the model is set (multiccd '
             'off, ADR 0027) and on a copy of the same instant with multiccd on - the least and most over the '
             'window, summed over the pair\'s bodies (a tread wheel\'s tyre segments are one tyre).', '',
             '| Moment | Pair | Shapes | Points | With multiccd | In contact |', '| --- | --- | --- | --- | --- | --- |']
    span = lambda lo_hi: f'{lo_hi[0]}' if lo_hi[0] == lo_hi[1] else f'{lo_hi[0]}-{lo_hi[1]}'
    for label, (a, b), kinds, ns, ms, seen, total in rows:
        lines.append(f'| {label} | {a.split("/", 1)[1]} - {b.split("/", 1)[1]} | {", ".join(kinds)} | {span(ns)} | '
                     f'{span(ms)} | {seen} of {total} |')
    decided = sorted({(a, b) for _, (a, b), _, ns, ms, _, _ in rows if ns != ms})
    lines += ['']
    if decided:
        lines.append('Pairs whose count multiccd would change: '
                     + '; '.join(f'{a.split("/", 1)[1]} - {b.split("/", 1)[1]}' for a, b in decided) + '.')
    else:
        lines.append('No pair here would have another count with multiccd on.')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.census',
                                     description="Count the contact points of the Fetch field's decisive contacts (FR-030).")
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    run, counts, start = take()
    text = markdown(run, counts, start)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
