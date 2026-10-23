"""Baselines for the program's recovery (FR-023): does looking again earn its complexity?

ADR 0033's program, when its reach goes wrong at a stop where it looked, opens its jaws, goes
back and looks again, and reaches where it now sees the object. It was measured against doing
nothing. A recovery earns its complexity only if it beats the simplest thing that also moves the
robot back (a study of learned correctors found a scripted return as good, arXiv 2610.06921):
reaching again where it saw the object before ('retreat'), or looking again but reaching as far
off in a random direction ('guess', the control a study of retrieval-triggered corrections
lacked, arXiv 2610.24573). Here the runner's rules, with the stand-ins of
tests/test_look_again.py: joints that go where they are sent, a base at its stop and a camera.
"""
import pytest

from little_world.programming.program import Runner
from test_look_again import FETCH, run


def moved_once():
    """The cube moved 5 cm to the side as the jaws first go down, and seen there after."""
    moved = {'at': None}

    def cube(t):
        return (1.84, .05, .14) if moved['at'] is not None else (1.84, 0., .14)

    def holds(aimed):
        if moved['at'] is None and (1.84, 0., .14) in aimed:
            moved['at'] = len(aimed)
        return (1.84, .05, .14) in aimed[moved['at'] or 0:] if moved['at'] is not None else False
    return cube, holds


def test_a_recovery_is_one_of_the_four():
    assert Runner().recovery == 'look'
    with pytest.raises(ValueError, match='look, retreat, guess, none'):
        Runner(recovery='pray')


def test_looking_again_reaches_where_the_cube_was_moved_to():
    runner, aimed, _, log = run(FETCH, *moved_once(), Runner(recovery='look'))
    assert runner.state == 'completed' and runner.regrasps == 1, log
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14), (1.84, .05, .14)]


def test_a_retreat_reaches_again_where_it_saw_the_cube_without_a_new_picture():
    runner, aimed, actions, log = run(FETCH, *moved_once(), Runner(recovery='retreat'))
    assert runner.state == 'failed' and runner.message == 'Nothing held: the grasp missed', log
    assert runner.regrasps == 1 and 'Nothing held: looking again' in log
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14)], "no second look"
    assert not any(abs(p[1] - .05) < 1e-6 for p in aimed), "never aimed where the cube went"
    reopened = [t for t, a in actions if a == ('jaws', -1)]
    assert reopened and reopened[-1] > 2., "the jaws opened again before the second reach"


def test_a_guess_looks_again_but_reaches_as_far_off_in_another_direction():
    runner, aimed, _, log = run(FETCH, *moved_once(), Runner(recovery='guess'))
    assert runner.state == 'failed' and runner.regrasps == 1, log
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14), (1.84, .05, .14)], "it did look again"
    after = [p for p in aimed if abs(p[2] - .14) < 1e-6 and p != (1.84, 0., .14)]
    assert after, aimed
    x, y = after[-1][:2]
    off, miss = ((x - 1.84) ** 2 + y ** 2) ** .5, ((x - 1.84) ** 2 + (y - .05) ** 2) ** .5
    assert off == pytest.approx(.05, abs=1e-3), "as far from the first sighting as the cube went"
    assert miss > .01, "but not where it went"


def test_with_no_recovery_a_missed_grasp_ends_the_program():
    runner, _, _, log = run(FETCH, *moved_once(), Runner(recovery='none'))
    assert runner.state == 'failed' and runner.regrasps == 0 and runner.message == 'Nothing held: the grasp missed'


# -- the sweeps that compare them ----------------------------------------------------------

def made_up(recovery, late):
    """A Fetch disturbed sweep's shape: four set-ups, undisturbed and with the cube moved 2 s
    after the look; `late`, which of them meet every goal moved."""
    from dataclasses import replace
    from test_disturbance import made_up as shaped
    result = shaped((('none', '', (33., 33., 34., 33.), None),
                     ('cube moved 5 cm sideways, 2 s later', 'moved', tuple(40. if ok else None for ok in late), None)))
    return replace(result, recovery=recovery)


def test_a_disturbed_sweep_records_its_recovery_and_says_it():
    from little_world.inventory.sweep import disturbed_from_json, disturbed_markdown, to_json
    result = made_up('retreat', (True, False, False, True))
    assert disturbed_from_json(to_json(result)).recovery == 'retreat'
    assert ('When its reach went wrong the program did not look again but reached again where it had seen '
            'the object (`--recovery retreat`, FR-023).') in disturbed_markdown(result)
    assert 'did not look again' not in disturbed_markdown(made_up(None, (True,) * 4))


def test_recoveries_are_read_pair_by_pair():
    from little_world.inventory import recovery
    own, retreat = made_up(None, (True, True, True, True)), made_up('retreat', (True, False, False, False))
    assert recovery.rows(own, retreat) == (
        ('none', 4, 4, 4, 0, 0, 1.), ('cube moved 5 cm sideways, 2 s later', 4, 1, 4, 3, 0, .25))
    page = recovery.markdown(own, [retreat, made_up('none', (True, False, False, False))])
    assert '## Against "retreat": reached again where it had seen the object' in page
    assert '| Disturbance | Looking again | None | Rescued by looking again, beyond it | The other way | p |' in page
    assert '| cube moved 5 cm sideways, 2 s later | 4 of 4 | 1 of 4 | 3 | 0 | 0.25 |' in page
    assert '| none | 4 of 4 | 4 of 4 | 0 | 0 | - |' in page


def test_the_command_line_takes_a_recovery_for_a_disturbed_sweep_only(capsys):
    from little_world.inventory.sweep import main
    with pytest.raises(SystemExit):
        main(['fetch', '--recovery', 'retreat'])
    assert '--recovery is for --disturb' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(['fetch', '--disturb', '--recovery', 'pray'])
    assert "invalid choice: 'pray'" in capsys.readouterr().err
