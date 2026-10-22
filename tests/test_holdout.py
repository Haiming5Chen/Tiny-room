"""Contracts for tuning draws and held-out draws (FR-027).

The defect: every sweep drew its set-ups with seed 1, and the decisions of October were tuned
on those very draws and then certified on them. A design tuned on its own test set looks
better than it is (an effect a study of frozen robot policies saw in its first cohort vanished
on an independent replication, arXiv 2610.24573). Each sweep now records its seed, a ledger
in the repository lists the seeds decisions were tuned on, and a held-out sweep is refused
draws a decision has already seen and read beside its tuning sweep.
"""
import json
from pathlib import Path

import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation
from little_world.inventory import holdout
from little_world.inventory.handling import Handled
from little_world.inventory.sweep import Run, Sweep, from_json, main, markdown, to_json

ROOT = Path(__file__).resolve().parents[1]


def fetch_sweep(seed, squeezes, falls, missed=0):
    """A Fetch sweep's shape without running it: the design as designed and drawn set-ups,
    each with the cube's squeeze and fall."""
    def results(ok):
        return (Result('lifted', 'Cube lifted 5 cm', 'met' if ok else 'missed', 20.),
                Result('in_bin', 'Cube in the bin', 'met' if ok else 'missed', 36. if ok else None))

    def handled(squeeze, fall):
        return (Handled('objects/fetch_cube', (('machine', squeeze), ('table', .2)), (('machine', squeeze - .1), ('table', .2)),
                        5., fall, 1., 2.),)
    runs = [Run(Variation(), results(True), program='completed', handled=handled(3.9, .003))]
    for i, (squeeze, fall) in enumerate(zip(squeezes, falls)):
        runs.append(Run(Variation(f'repeat {i + 1}', x=.001 * i), results(i >= missed), program='completed',
                        handled=handled(squeeze, fall)))
    return Sweep('fetch', 'arm on a cart', 'program', 60., None, Ranges(), tuple(runs), seed=seed)


def test_a_sweep_records_the_seed_its_setups_were_drawn_with():
    sweep = fetch_sweep(7, (3.8, 4.0), (.002, .004))
    again = from_json(to_json(sweep))
    assert again.seed == 7 and 'Set-ups drawn with seed 7.' in markdown(again)
    old = json.loads(to_json(sweep))
    del old['seed']
    assert from_json(json.dumps(old)).seed is None, "a sweep written before seeds were recorded reads back"


def test_the_ledger_lists_seed_1_as_the_tuning_draws_of_every_field():
    entries = holdout.read(ROOT / holdout.LEDGER)
    assert entries[0].seed == 1 and entries[0].role == 'tuning' and entries[0].field == holdout.EVERY
    for field in ('fetch', 'sprint', 'tilt'):
        assert 1 in holdout.used(entries, field)
    assert 20261022 in holdout.used(entries, 'fetch'), "ADR 0049's held-out draws, entered before they ran"


def test_a_held_out_seed_is_reserved_once_and_never_given_again(tmp_path):
    from datetime import date
    ledger = tmp_path / 'seeds.jsonl'
    ledger.write_text((ROOT / holdout.LEDGER).read_text())
    with pytest.raises(holdout.SeedUsed, match='seed 1 already drew'):
        holdout.reserve(1, 'fetch', 'ADR 0049', ledger)
    fresh = 987654321          # a seed no decision of this project has used
    entry = holdout.reserve(fresh, 'fetch', 'ADR 0099', ledger, today=date(2026, 10, 22))
    assert entry.role == 'holdout' and holdout.read(ledger)[-1] == entry
    with pytest.raises(holdout.SeedUsed, match='holdout for ADR 0099'):
        holdout.reserve(fresh, 'fetch', 'ADR 0100', ledger)
    assert holdout.reserve(fresh, 'sprint', 'ADR 0100', ledger).field == 'sprint', "another field's draws"
    lines = len(ledger.read_text().splitlines())
    ledger.write_text(ledger.read_text() + '{"seed": 3}\n')
    with pytest.raises(ValueError, match=f'line {lines + 1}'):
        holdout.read(ledger)


def test_the_command_line_refuses_a_held_out_sweep_on_draws_already_seen(tmp_path, capsys):
    ledger = tmp_path / 'seeds.jsonl'
    ledger.write_text((ROOT / holdout.LEDGER).read_text())
    entries = len(holdout.read(ledger))
    with pytest.raises(SystemExit):
        main(['fetch', '--holdout', 'ADR 0049', '--seed', '1', '--ledger', str(ledger)])
    assert 'seed 1 already drew' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(['fetch', '--holdout', 'ADR 0049', '--ledger', str(ledger)])
    assert '--holdout needs --seed' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(['fetch', '--holdout', 'ADR 0049', '--seed', '5', '--ledger', str(tmp_path / 'none.jsonl')])
    assert 'no ledger of seeds' in capsys.readouterr().err
    assert len(holdout.read(ledger)) == entries, "nothing reserved by a refused sweep"


def test_a_held_out_sweep_reads_beside_its_tuning_sweep_and_names_what_left_its_range():
    tuning = fetch_sweep(1, (3.6, 3.9, 4.2, 4.0), (.001, .004, .011, .003))
    held = fetch_sweep(20261022, (3.7, 4.1, 3.8, 4.6), (.002, .005, .003, .001), missed=1)
    text = holdout.compare(tuning, held)
    assert 'Tuning: 4 set-ups drawn with seed 1; held out: 4 drawn with seed 20261022.' in text
    assert '| Every goal | 4 of 4 (40-100 %) | 3 of 4 (19-99 %) |' in text.replace('every goal', 'Every goal')
    flagged = dict(holdout.outside(tuning, held))
    assert list(flagged) == [('objects/fetch_cube', 'force from the machine, in a step'),
                             ('objects/fetch_cube', 'force from the machine, over 50 ms')]
    assert 'most 4.60 N over the tuning\'s most, 4.20 N' in flagged[('objects/fetch_cube', 'force from the machine, in a step')]
    assert 'reported as found, not tuned away' in text and '| fetch_cube | fell when let go |' in text
    with pytest.raises(ValueError, match='both sweeps were drawn with seed 1'):
        holdout.compare(tuning, fetch_sweep(1, (4.,), (.002,)))
