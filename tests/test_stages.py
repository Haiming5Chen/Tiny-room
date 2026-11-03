"""Contracts for where runs fail: a stage profile in every sweep report (FR-038).

A rate says how many runs met every goal; it does not say where the others failed, and two
disturbances can cost the same and fail in different places (RoboCasa-Shift, arXiv 2610.27861).
The field's goals are its stages, in the order a run meets them; a program that gives up says at
which block, and what it was doing there.
"""
import json
from dataclasses import asdict

import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Variation
from little_world.inventory.stages import first_missed, funnel, lines, markdown, missed_at, stopped
from little_world.inventory.sweep import Run, _run

FETCH = ('reached', 'Reached the table'), ('lifted', 'Cube lifted 5 cm'), ('delivered', 'Cube resting in the bin')


def fetch(label, got, kept=True, stop=()):
    """A Fetch run that met its first `got` goals and missed the rest."""
    results = tuple(Result(i, text, 'met' if k < got else 'missed', 10. * k if k < got else None)
                    for k, (i, text) in enumerate(FETCH))
    return Run(Variation(label), results + (Result('upright', 'Stayed upright', 'kept' if kept else 'failed'),),
               program='failed' if stop else 'completed', stopped=stop)


def test_how_far_runs_got_and_where_they_stopped():
    runs = [fetch('as designed', 3), fetch('repeat 1', 3), fetch('repeat 2', 1, stop=(8, 'grasp')),
            fetch('repeat 3', 1, stop=(4, 'look')), fetch('repeat 4', 1, stop=(4, 'look')), fetch('repeat 5', 0)]
    assert funnel(runs) == [('Reached the table', 5), ('Cube lifted 5 cm', 2), ('Cube resting in the bin', 2)]
    assert missed_at(runs) == [('Cube lifted 5 cm', 3), ('Reached the table', 1)]
    assert stopped(runs) == [('looking', 2), ('checking the grasp', 1)]
    assert lines(runs) == ('missed: lifted 3, reached 1', 'gave up: looking 2, grasping 1')
    assert lines(runs[:2]) == (), 'every goal met: nothing to say'
    assert first_missed(fetch('tipped', 3, kept=False)) == 'Stayed upright', "a held goal broken counts, not as a stage"
    assert funnel([fetch('tipped', 3, kept=False)]) == [('Reached the table', 1), ('Cube lifted 5 cm', 1),
                                                        ('Cube resting in the bin', 1)]
    table = markdown([('undisturbed', runs[:2]), ('camera frozen', runs[2:])])
    assert '| Runs | Reached the table | Cube lifted 5 cm | Cube resting in the bin | Gave up |' in table
    assert '| undisturbed (2) | 2 | 2 | 2 | - |' in table
    assert '| camera frozen (4) | 3 | 0 | 0 | looking 2, checking the grasp 1 |' in table


def test_where_a_program_stopped_survives_the_report_file():
    run = fetch('repeat 2', 1, stop=(8, 'grasp'))
    back = _run(json.loads(json.dumps(asdict(run))))
    assert back.stopped == (8, 'grasp') and _run(json.loads(json.dumps(asdict(fetch('x', 3))))).stopped == ()


def test_a_frozen_camera_stops_the_fetch_while_it_looks():
    """On the field: the camera freezes as the cube is moved (ADR 0038); the program sees its
    pictures are old and gives up at its look, having reached the table."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import run
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    frozen = next(d for d in DEFAULTS['fetch'] if d.label == 'camera frozen as the cube is moved 5 cm')
    r = run('fetch', mobile_manipulator_blueprint(), disturbance=frozen)
    assert r.program == 'failed' and r.stopped[1] == 'look', (r.program, r.stopped, r.message)
    assert lines([r]) == ('missed: lifted 1', 'gave up: looking 1')
