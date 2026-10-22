"""Tuning draws and held-out draws (FR-027).

A design shaped while looking at the very set-ups that then certify it looks better than it
is: the first cohort of a study of frozen robot policies showed an effect that an independent
replication did not (arXiv 2610.24573). Every sweep here was drawn with seed 1, and the
decisions of October were tuned on those draws - ADR 0042's squeeze was added after repeat 44
crept out of the jaws, ADR 0041 was judged on the draws where its four presses had been found.

So every sweep records the seed its set-ups were drawn with, and a ledger in the repository
(`docs/sweeps/seeds.jsonl`) lists the seeds decisions were tuned on, field by field. A held-out
sweep is drawn with a seed the ledger has not seen for its field, reserved in the ledger before
it runs, and read beside its tuning sweep: each goal's rate with its two-sided Clopper-Pearson
interval (ADR 0028), each handling measure's median and range (ADR 0040), and every held-out
value outside its tuning range named. A held-out value outside is reported as found; anything
changed after seeing it is certified again on a new seed.

Standard library only.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

LEDGER = Path('docs') / 'sweeps' / 'seeds.jsonl'
EVERY = '*'         # a ledger entry for every field
ROLES = ('tuning', 'holdout')


class SeedUsed(ValueError):
    """A held-out sweep asked for draws a decision was already tuned or judged on."""


@dataclass(frozen=True)
class Entry:
    """One line of the ledger: a seed, the field it drew set-ups for, and for what."""
    seed: int
    field: str          # a field's id, or EVERY
    role: str           # 'tuning' or 'holdout'
    decisions: str      # which decision records it served, in words: 'ADR 0049'
    date: str           # when it was entered, ISO
    note: str = ''

    def covers(self, field):
        return self.field in (field, EVERY)


def read(path=LEDGER):
    """The ledger's entries, oldest first; a ledger that is not there has none."""
    path = Path(path)
    if not path.is_file():
        return ()
    entries = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            entry = Entry(int(d['seed']), str(d['field']), str(d['role']), str(d['decisions']), str(d['date']),
                          str(d.get('note', '')))
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f'{path}, line {number}: not a ledger entry ({error})') from None
        if entry.role not in ROLES:
            raise ValueError(f"{path}, line {number}: the role is 'tuning' or 'holdout', not {entry.role!r}")
        entries.append(entry)
    return tuple(entries)


def used(entries, field):
    """The seeds whose draws of `field` something was already tuned or judged on."""
    return {e.seed for e in entries if e.covers(field)}


def reserve(seed, field, decisions, path=LEDGER, today=None):
    """Enter `seed` in the ledger as `field`'s held-out draws for `decisions` - before the
    sweep runs, so that its draws are never mistaken for fresh ones again. Refuses a seed the
    ledger already has for the field (SeedUsed). The entry."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f'a seed is a whole number, not {seed!r}')
    path = Path(path)
    entries = read(path)
    if seed in used(entries, field):
        served = '; '.join(f'{e.role} for {e.decisions}' for e in entries if e.covers(field) and e.seed == seed)
        raise SeedUsed(f'seed {seed} already drew the {field} field\'s set-ups ({served}): held-out draws '
                       f'are ones no decision has seen - choose a seed not in {path}')
    entry = Entry(seed, field, 'holdout', decisions,
                  (today or datetime.now(timezone.utc).date()).isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as out:
        out.write(json.dumps(asdict(entry)) + '\n')
    return entry


# -- reading a held-out sweep beside its tuning sweep ------------------------------------------

def _rates(sweep):
    from little_world.inventory.sweep import rates
    return {r.label: r for r in rates(sweep)}


def _measures(sweep):
    """(part, label) -> (median, least, most) of the handling summary over the drawn runs."""
    from little_world.inventory.handling import summary
    from little_world.inventory.sweep import drawn
    sample = drawn(sweep)
    parts = []
    for r in sample:
        parts += [h.part for h in r.handled if h.part not in parts]
    out = {}
    for part in parts:
        for label, mid, low, high in summary([next((h for h in r.handled if h.part == part), None) for r in sample]):
            out[(part, label)] = (mid, low, high)
    return out


def _unit(label, v):
    if label.startswith('force'):
        return f'{v:.2f} N'
    if label.startswith('lean'):
        return f'{v:.1f} deg'
    return f'{100 * v:.1f} cm'


def _shown(label, v):
    """A measure as the report shows it: forces to 0.01 N, leans to 0.1 degree, falls to a mm."""
    return round(v, 2) if label.startswith('force') else round(v, 1) if label.startswith('lean') else round(v, 3)


def outside(tuning, holdout):
    """Each measure whose held-out values leave its tuning range as the report shows them:
    ((part, label), what) - the held-out least below the tuning's least, its most above the
    tuning's most."""
    a, b = _measures(tuning), _measures(holdout)
    found = []
    for key in a:
        if key not in b:
            continue
        label = key[1]
        (_, low, high), (_, low2, high2) = ((_shown(label, v) for v in a[key]), (_shown(label, v) for v in b[key]))
        said = []
        if high2 > high:
            said.append(f'most {_unit(label, high2)} over the tuning\'s most, {_unit(label, high)}')
        if low2 < low:
            said.append(f'least {_unit(label, low2)} under the tuning\'s least, {_unit(label, low)}')
        if said:
            found.append((key, '; '.join(said)))
    return tuple(found)


def compare(tuning, holdout):
    """The held-out sweep beside its tuning sweep, as a short Markdown report."""
    from little_world.inventory.confidence import interval
    from little_world.inventory.sweep import drawn
    if tuning.field != holdout.field:
        raise ValueError(f'a held-out sweep is read beside a tuning sweep of the same field, not '
                         f'{holdout.field} beside {tuning.field}')
    seeds = getattr(tuning, 'seed', None), getattr(holdout, 'seed', None)
    if None not in seeds and seeds[0] == seeds[1]:
        raise ValueError(f'both sweeps were drawn with seed {seeds[0]}: the held-out draws must be other draws')
    n, m = len(drawn(tuning)), len(drawn(holdout))
    name = lambda s: f'seed {s}' if s is not None else 'seed not recorded'
    lines = [f'# {tuning.field}: tuning draws and held-out draws', '',
             f'Tuning: {n} set-ups drawn with {name(seeds[0])}; held out: {m} drawn with {name(seeds[1])}. '
             f'Design: {holdout.design}. Rates with their two-sided 95 % Clopper-Pearson intervals (ADR 0028); '
             'handling over the drawn runs, median and range (ADR 0040).', '',
             '| Goal | Tuning | Held out |', '| --- | --- | --- |']
    a, b = _rates(tuning), _rates(holdout)
    for label in a:
        if label not in b:
            continue
        cells = []
        for rate in (a[label], b[label]):
            low, high = interval(rate.met, rate.runs)
            cells.append(f'{rate.met} of {rate.runs} ({100 * low:.0f}-{100 * high:.0f} %)')
        lines.append(f'| {label} | {cells[0]} | {cells[1]} |')
    ma, mb = _measures(tuning), _measures(holdout)
    flagged = dict(outside(tuning, holdout))
    rows = [key for key in ma if key in mb]
    if rows:
        lines += ['', '| Part | Measure | Tuning: median (least - most) | Held out | |', '| --- | --- | --- | --- | --- |']
        for key in rows:
            part, label = key
            cell = lambda v: f'{_unit(label, v[0])} ({_unit(label, v[1])} - {_unit(label, v[2])})'
            lines.append(f'| {part.split("/")[-1]} | {label} | {cell(ma[key])} | {cell(mb[key])} | '
                         f'{"outside" if key in flagged else "within"} |')
    lines += ['']
    if flagged:
        lines.append('Outside the tuning range - reported as found, not tuned away:')
        lines += [f'- {key[0].split("/")[-1]}, {key[1]}: {what}.' for key, what in flagged.items()]
    else:
        lines.append('Every held-out measure is within its tuning range.')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    import argparse
    from little_world.inventory.sweep import from_json
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.holdout',
                                     description='Read a held-out sweep beside its tuning sweep (FR-027).')
    parser.add_argument('tuning', help="the tuning sweep's JSON (sweep --json)")
    parser.add_argument('holdout', help="the held-out sweep's JSON")
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    try:
        text = compare(from_json(Path(args.tuning).read_text(encoding='utf-8')),
                       from_json(Path(args.holdout).read_text(encoding='utf-8')))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
