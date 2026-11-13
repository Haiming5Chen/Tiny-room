"""Does a recovery earn its complexity? Recoveries read pair by pair (FR-023).

When its reach goes wrong at a stop where it looked, the program looks again and reaches where
it now sees the object (ADR 0033, 0037). That was measured against no recovery at all. A
study of learned correctors for robot policies found a scripted return to an earlier pose as
good as the learned pipeline (arXiv 2610.06921), and a study of retrieval-triggered corrections
could not tell its corrections from random ones of the same size (arXiv 2610.24573). So the
program's own recovery is read beside baselines run on the same set-ups under the same
disturbances (`sweep --disturb --recovery`): reaching again where it saw the object
('retreat'), looking again but reaching as far off in a random direction ('guess'), and
stopping ('none').

The simulator is deterministic, so each set-up under each disturbance is one run per recovery,
and the two recoveries' runs are the same run until the reach first goes wrong: a pair whose
outcomes differ was changed by the recovery alone, and the exact McNemar test on those pairs
says how sure that is (ADR 0036). Standard library only.
"""
from pathlib import Path


def _met(run):
    return not run.error and all(x.status in ('met', 'kept') for x in run.results)


def rows(own, baseline):
    """Per disturbance in both: (label, own met, baseline met, runs, rescued - the set-ups the
    own recovery met and the baseline did not - and the other way, p)."""
    from little_world.inventory.confidence import mcnemar
    theirs = {label: {r.variation.label: r for r in runs} for label, _, runs in baseline.groups}
    out = []
    for label, _, runs in own.groups:
        if label not in theirs:
            continue
        pairs = [(r, theirs[label][r.variation.label]) for r in runs if r.variation.label in theirs[label]]
        rescued = sum(1 for a, b in pairs if _met(a) and not _met(b))
        other = sum(1 for a, b in pairs if _met(b) and not _met(a))
        out.append((label, sum(_met(a) for a, _ in pairs), sum(_met(b) for _, b in pairs), len(pairs),
                    rescued, other, mcnemar(rescued, other)))
    return tuple(out)


def verified(own, baseline):
    """Whether each pair began from the same start (FR-041): a recovery is a runner's setting, not the set-up's."""
    from little_world.inventory.identity import check
    theirs = {label: {r.variation.label: r for r in runs} for label, _, runs in baseline.groups}
    return check((r.variation.label, r.fingerprint, theirs[label][r.variation.label].fingerprint)
                 for label, _, runs in own.groups if label in theirs
                 for r in runs if r.variation.label in theirs[label])


def markdown(own, baselines):
    """The program's own recovery beside each baseline, as a short report."""
    from little_world.inventory.sweep import RECOVERED
    lines = [f'# {own.field}: does looking again earn its complexity?', '',
             'Each disturbance tried on the same set-ups with the program\'s own recovery - looking again and '
             'reaching where it now sees the object (ADR 0033) - and with each baseline (FR-023). Every goal met, '
             'per set-up; a pair whose outcomes differ was changed by the recovery alone (exact McNemar, ADR 0036).']
    called = 'Looking again' if own.recovery in (None, 'look') else own.recovery.capitalize()
    for baseline in baselines:
        name = baseline.recovery or 'look'
        lines += ['', f'## Against "{name}": {RECOVERED.get(name, "looked again")}', '', verified(own, baseline).line(), '',
                  f'| Disturbance | {called} | {name.capitalize()} | Rescued by {called.lower()}, beyond it | The other way | p |',
                  '| --- | --- | --- | --- | --- | --- |']
        for label, mine, theirs, n, rescued, other, p in rows(own, baseline):
            lines.append(f'| {label} | {mine} of {n} | {theirs} of {n} | {rescued} | {other} | '
                         + ('-' if not rescued and not other else f'{p:.2g}') + ' |')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    import argparse
    from little_world.inventory.sweep import disturbed_from_json
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.recovery',
                                     description="Read the program's own recovery beside its baselines (FR-023).")
    parser.add_argument('own', help="a disturbed sweep's JSON with the program's own recovery")
    parser.add_argument('baselines', nargs='+', help='disturbed sweeps of the same set-ups with --recovery')
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    try:
        own = disturbed_from_json(Path(args.own).read_text(encoding='utf-8'))
        baselines = [disturbed_from_json(Path(p).read_text(encoding='utf-8')) for p in args.baselines]
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    text = markdown(own, baselines)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
