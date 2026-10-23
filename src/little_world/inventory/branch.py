"""How late is too late: when an alarm can still put a run right, and what a false one costs (FR-022).

A check is worth having only if it fires while a recovery can still put things right, and only
if a false alarm costs little (RESCUE, arXiv 2610.13516: whether a failure can be recovered
depends on the state and the intervention together; an ideal detector there tolerated a false
alarm rate of only 2 to 3 %). The program's checks - the object moved since the look, a reach
blocked, a grasp holding nothing, a picture not new (ADR 0033, 0037, 0038) - fire at fixed
moments of its reach. Here an alarm is raised from outside at any moment (`Runner.alarm`), and
the program recovers as its own recovery does: it looks again.

The simulator is deterministic, so a run with an alarm at a moment is its unalarmed run - its
parent - until then, step for step (ADR 0036): branching a run at a checkpoint is running it
again with the alarm then, and needs no snapshot of the program's own state.

- `window`: a failing set-up, run with its checks ignored ('ignore': the program goes on as
  taught), and again with an alarm every EVERY seconds of the time it listens - at the stop where
  it looked, until it leaves: the alarms that rescue it, the earliest and the latest (the
  deadline), against when its own check began its recovery.
- `false_alarm`: a set-up that needed no recovery, run again with one alarm at a moment drawn
  from the time it listened: whether it still meets every goal, and how much later.

The reading is standard library; running the branches is MuJoCo-bound, through the sweep's run.
`python -m little_world.inventory.branch`.
"""
from dataclasses import dataclass
from math import floor
from statistics import median

EVERY = .5          # s between a window's alarms: FR-022's checkpoints
PHASES = ('reaching', 'closing', 'holding')


def met(run):
    """Whether a run met every goal."""
    return not run.error and bool(run.results) and all(x.status in ('met', 'kept') for x in run.results)


def last(run):
    """When a run that met every goal met its last, seconds from its start; None otherwise."""
    times = [x.time for x in run.results if x.time is not None]
    return max(times) if met(run) and times else None


def scan(listening, every=EVERY):
    """The moments a window raises its alarms: on every `every` seconds of world time inside the
    spans the parent listened (after a span's start, when the program is listening, up to its end)."""
    out = []
    for begin, end in listening:
        k = floor(begin / every + 1e-9) + 1
        while k * every <= end + 1e-9:
            out.append(round(k * every, 3))
            k += 1
    return tuple(out)


@dataclass(frozen=True)
class Window:
    """One failing set-up and its alarms."""
    setup: str
    event: float | None         # when the disturbance began, world seconds
    check: float | None         # when, with its own recovery, its own check began it; None: never
    own: bool                   # whether its own recovery met every goal
    listening: tuple            # the parent's spans in which an alarm acts
    alarms: tuple               # ((when, acted, met every goal), ...), in time order

    @property
    def rescued(self):
        return tuple(t for t, acted, ok in self.alarms if ok)

    @property
    def earliest(self):
        return min(self.rescued, default=None)

    @property
    def deadline(self):
        """The latest alarm that still rescued the run."""
        return max(self.rescued, default=None)

    @property
    def holes(self):
        """Alarms between the earliest and the deadline that did not rescue it."""
        if not self.rescued:
            return ()
        return tuple(t for t, _, ok in self.alarms if self.earliest < t < self.deadline and not ok)

    @property
    def slack(self):
        """How much later than its own check the alarm could have come and still rescued it."""
        return None if self.deadline is None or self.check is None else self.deadline - self.check


def window(parent, branches, own=None):
    """A set-up's window from its parent run (checks ignored), its branches (the parent with an
    alarm each) and, if given, its run with its own recovery."""
    alarms = sorted((b.alarm[0][0], bool(b.alarm[0][1]), met(b)) for b in branches if b.alarm)
    check = own.recovered[0] if own is not None and own.recovered else None
    return Window(parent.variation.label, parent.event, check, met(own) if own is not None else False,
                  parent.listening, tuple(alarms))


def false_alarm_at(run):
    """A moment drawn evenly from the time a run listened, from its set-up's name - so a set-up
    always draws the same - or None if it never listened."""
    from random import Random
    from zlib import crc32
    spans = [(a, b) for a, b in run.listening if b > a]
    total = sum(b - a for a, b in spans)
    if not total:
        return None
    u = Random(crc32(f'{run.variation.label} false alarm'.encode())).uniform(0., total)
    for a, b in spans:
        if u <= b - a:
            return round(a + u, 3)
        u -= b - a
    return round(spans[-1][1], 3)


def phase(program, index):
    """What the program was doing at its block `index`, after the look before it: 'reaching' -
    its jaws open, on the way to the object; 'closing' - closing on it, or checking the grasp;
    'holding' - past its grasp check, the object held."""
    blocks = program.blocks
    start = max((i for i in range(index + 1) if blocks[i].kind == 'look'), default=-1) + 1
    since = blocks[start:index + 1]
    if any(b.kind == 'grasp' for b in since[:-1]):
        return 'holding'
    if any(b.kind == 'action' and b.value > 0 for b in since) or since and since[-1].kind == 'grasp':
        return 'closing'
    return 'reaching'


@dataclass(frozen=True)
class FalseAlarm:
    """One set-up that needed no recovery, alarmed once."""
    setup: str
    when: float
    acted: bool
    phase: str
    parent: bool                # whether the unalarmed run met every goal
    alarmed: bool               # whether the alarmed run did
    cost: float | None          # how much later it met its last goal; None unless both met


def false_alarm(parent, alarmed, program):
    when, acted, index = alarmed.alarm[0]
    a, b = last(parent), last(alarmed)
    return FalseAlarm(parent.variation.label, when, bool(acted), phase(program, index), met(parent), met(alarmed),
                      None if a is None or b is None else b - a)


def _span(values):
    return f'{median(values):+.1f} s ({min(values):+.1f} to {max(values):+.1f})' if values else '-'


def windows_markdown(windows, disturbance, every=EVERY):
    lines = [f'## When an alarm can still rescue a run: {disturbance}', '',
             f'Each set-up run with the program\'s checks ignored - it goes on as taught - and missing a goal; then '
             f'again with an alarm every {every:g} s of the time the program listened, from the end of its look at '
             'the stop to leaving it, the alarm making it look again as its own recovery does. Each such run is the '
             'unalarmed one until the alarm, step for step (ADR 0036). "Its own check" is when, with its own '
             'recovery, the program\'s check began it (ADR 0033, 0037); the deadline is the latest alarm that still '
             'rescued the set-up, and the slack how much later than its own check that is. World seconds.', '',
             '| Set-up | Disturbed at | Listening | Its own check | Alarms that rescue | Earliest | Deadline | Slack |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for w in windows:
        listening = ', '.join(f'{a:.2f}-{b:.2f}' for a, b in w.listening)
        holes = f' (not {", ".join(f"{t:.1f}" for t in w.holes)})' if w.holes else ''
        lines.append(f'| {w.setup} | {"-" if w.event is None else f"{w.event:.2f}"} | {listening} | '
                     f'{"-" if w.check is None else f"{w.check:.2f}" + ("" if w.own else ", missed")} | '
                     f'{len(w.rescued)} of {len(w.alarms)}{holes} | '
                     f'{"-" if w.earliest is None else f"{w.earliest:.1f}"} | '
                     f'{"-" if w.deadline is None else f"{w.deadline:.1f}"} | '
                     f'{"-" if w.slack is None else f"{w.slack:+.1f} s"} |')
    return '\n'.join(lines) + '\n'


def false_alarms_markdown(alarms):
    from little_world.inventory.confidence import upper_bound
    lines = ['## What a false alarm costs', '',
             'Set-ups that needed no recovery, each run again with one alarm at a moment drawn evenly from the time '
             'its program listened (from the end of its look at the stop to leaving it): whether it still met every '
             'goal, and how much later it met its last than unalarmed - the same set-up, the same run until the alarm. '
             'An alarm recovers as the program\'s own recovery does, which never comes once a grasp is checked: '
             'while the object is held, it opens the jaws on it before looking again.', '',
             '| While | Alarms | Still met every goal | Broke a success | Later by: median (least to most) |',
             '| --- | --- | --- | --- | --- |']
    acted = [a for a in alarms if a.acted and a.parent]
    for name in (*PHASES, 'all'):
        group = [a for a in acted if name in ('all', a.phase)]
        if not group:
            continue
        broke = sum(1 for a in group if not a.alarmed)
        bound = upper_bound(broke, len(group))
        lines.append(f'| {name} | {len(group)} | {len(group) - broke} | {broke} of {len(group)}, at most '
                     f'{100 * bound:.0f} % | {_span([a.cost for a in group if a.cost is not None])} |')
    ignored = sum(1 for a in alarms if not a.acted)
    if ignored:
        lines += ['', f'{ignored} alarm{"s" if ignored != 1 else ""} came when the program was not listening and '
                      'changed nothing.']
    return '\n'.join(lines) + '\n'


# -- running the branches (MuJoCo) -----------------------------------------------------------------

def _work(args):
    from little_world.inventory.sweep import run
    return run(*args[:4], **args[4])


def _map(work, jobs):
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            return list(pool.map(_work, work))
    return [_work(w) for w in work]


def windows(disturbance, design='mobile_manipulator', field_id='fetch', samples=8, seed=1, every=EVERY, jobs=1):
    """Each set-up of a disturbed sweep under `disturbance` (a label of the field's own): its own
    recovery's run, its parent with the checks ignored and its branches. (windows, the set-ups'
    runs as {label: (own, parent, branches)})."""
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design as made, ranges_for, setups, shared_site, solve
    taken = next((d for d in DEFAULTS.get(field_id, ()) if d.label == disturbance), None)
    if taken is None:
        raise ValueError(f'the {field_id} field has no disturbance {disturbance!r}; it has: '
                         + ', '.join(repr(d.label) for d in DEFAULTS.get(field_id, ())))
    bp = made(design)
    program = solve(field_id, bp)
    variations = setups(ranges_for(field_id), samples, seed)
    site = shared_site(bp, variations)          # as the disturbed sweep loads them (ADR 0030)
    firsts = _map([(field_id, bp, v, program, {'site': site, 'disturbance': taken, 'recovery': r})
                   for v in variations for r in ('look', 'ignore')], jobs)
    own, parents = firsts[0::2], firsts[1::2]
    work = [(field_id, bp, v, program, {'site': site, 'disturbance': taken, 'recovery': 'ignore', 'alarm': t})
            for v, p in zip(variations, parents) for t in scan(p.listening, every)]
    done = _map(work, jobs)
    out, runs = [], {}
    for v, o, p in zip(variations, own, parents):
        mine = [b for b in done if b.variation.label == v.label]
        out.append(window(p, mine, o))
        runs[v.label] = (o, p, mine)
    return tuple(out), runs


def false_alarms(design='mobile_manipulator', field_id='fetch', samples=8, seed=1, jobs=1):
    """Every set-up of the field's sweep plan run as designed, then again with one false alarm."""
    from little_world.fields.variation import plan
    from little_world.inventory.sweep import design as made, ranges_for, shared_site, solve
    bp = made(design)
    program = solve(field_id, bp)
    variations = plan(ranges_for(field_id), samples, seed)
    site = shared_site(bp, variations)          # as the sweep loads them (ADR 0024)
    parents = _map([(field_id, bp, v, program, {'site': site}) for v in variations], jobs)
    chosen = [(v, p, false_alarm_at(p)) for v, p in zip(variations, parents)]
    chosen = [(v, p, t) for v, p, t in chosen if t is not None]
    alarmed = _map([(field_id, bp, v, program, {'site': site, 'alarm': t}) for v, _, t in chosen], jobs)
    return tuple(false_alarm(p, a, program) for (_, p, _), a in zip(chosen, alarmed))


def main(argv=None):
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.branch',
                                     description='When an alarm can still rescue a run, and what a false one costs (FR-022).')
    parser.add_argument('what', choices=('window', 'false-alarms'))
    parser.add_argument('--disturbance', default='cube moved 5 cm sideways, 2 s later',
                        help="for 'window': which of the Fetch field's disturbances")
    parser.add_argument('--every', type=float, default=EVERY, help="for 'window': seconds between alarms")
    parser.add_argument('--samples', type=int, default=8, help='set-ups drawn at random (seed 1)')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    if args.every <= 0:
        parser.error('--every is a time in seconds, more than 0')
    try:
        if args.what == 'window':
            found, _ = windows(args.disturbance, samples=args.samples, every=args.every, jobs=args.jobs)
            text = windows_markdown(found, args.disturbance, args.every)
        else:
            text = false_alarms_markdown(false_alarms(samples=args.samples, jobs=args.jobs))
    except ValueError as error:
        parser.error(str(error))
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
