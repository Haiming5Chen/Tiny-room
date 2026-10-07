"""Paired runs: each set-up run with and without the disturbance (ADR 0036, FR-017).

The simulator is deterministic, so a set-up's undisturbed run and its disturbed run are one
run until the event: whatever differs after it, the event did. The report pairs them - how
many successes the event broke, how many failures it turned round - and tests the pairs whose
outcomes differ exactly (McNemar). First the test itself, then the pairing on made-up runs,
then the two runs of a pair, step for step, on the Sprint and Fetch fields.
"""
import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation
from little_world.inventory.confidence import mcnemar
from little_world.inventory.sweep import Disturbed, Run, disturbed_markdown, summaries


def test_the_exact_mcnemar_test_counts_only_the_pairs_that_differ():
    assert mcnemar(9, 0) == 2 / 2 ** 9 == pytest.approx(.0039, abs=1e-4)      # nine broken, none rescued
    assert mcnemar(8, 0) == pytest.approx(.0078, abs=1e-4)
    assert mcnemar(10, 2) == pytest.approx(158 / 4096)                        # 2 (1 + 12 + 66) / 2^12
    assert mcnemar(0, 0) == mcnemar(3, 3) == mcnemar(1, 0) == 1.             # no evidence either way
    assert mcnemar(2, 7) == mcnemar(7, 2)
    for bad in ((-1, 0), (1.5, 0)):
        with pytest.raises(ValueError):
            mcnemar(*bad)


def outcome(label, met):
    goals = (Result('reached', 'Reached', 'met', 10.), Result('delivered', 'Delivered', 'met' if met else 'missed',
                                                              30. if met else None))
    return Run(Variation(label), goals, program='completed' if met else 'failed')


def result(undisturbed, disturbed):
    labels = ['as designed'] + [f'repeat {k}' for k in range(1, len(undisturbed))]
    runs = lambda oks: tuple(outcome(label, ok) for label, ok in zip(labels, oks))
    return Disturbed('fetch', 'cart', 'program', 60., None, Ranges(), None,
                     (('none', '', runs(undisturbed)), ('moved', 'moved, later', runs(disturbed))))


def test_each_drawn_set_up_is_paired_with_itself_undisturbed():
    """Eight drawn set-ups, every one fetched undisturbed and none disturbed: eight broken,
    p = 0.0078 - the as-designed run is chosen, not drawn, so it is not in the count."""
    none, moved = summaries(result([True] * 9, [False] * 9))
    assert (none.held, none.broke, none.rescued) == (8, 0, 0)
    assert (moved.held, moved.broke, moved.rescued) == (8, 8, 0) and moved.p == pytest.approx(.0078, abs=1e-4)
    assert moved.breaks_at_most == 1.
    text = disturbed_markdown(result([True] * 9, [False] * 9))
    assert '| Broken by it |' in text and '8 of 8, at least 69 %; p = 0.0078' in text


def test_a_disturbance_that_breaks_nothing_bounds_how_much_it_could():
    none, moved = summaries(result([True] * 9, [True] * 9))
    assert (moved.held, moved.broke, moved.rescued, moved.p) == (8, 0, 0, 1.)
    assert moved.breaks_at_most == pytest.approx(1 - .05 ** (1 / 8))        # 0 of 8: at most 31 %
    assert '0 of 8, at most 31 % |' in disturbed_markdown(result([True] * 9, [True] * 9))


def test_a_rescue_counts_the_other_way():
    oks = [True, True, False, True, True, True, True, True, False]
    _, moved = summaries(result(oks, [True, False, True, True, True, True, True, True, True]))
    assert (moved.held, moved.broke, moved.rescued) == (6, 1, 2) and moved.p == 1.
    text = disturbed_markdown(result(oks, [True, False, True] + [True] * 6))
    assert '1 of 6, 0 to 64 %; rescued 2; p = 1.0000' in text


def twins(field, disturbance, design):
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design as named, run
    bp = named(design)
    plain, moved = [], []
    calm = run(field, bp, trace=plain)
    shaken = run(field, bp, disturbance=disturbance, trace=moved)
    return calm, shaken, plain, moved


def first_difference(a, b):
    return next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), None)


def test_the_two_runs_of_a_sprint_pair_are_one_run_until_the_shove():
    from little_world.fields.disturbance import DEFAULTS
    shove = DEFAULTS['sprint'][0]
    calm, shaken, plain, moved = twins('sprint', shove, 'mobile_platform')
    assert calm.event is None and shaken.event is not None
    k = first_difference(plain, moved)
    assert k is not None and all(t == u for (t, _), (u, _) in zip(plain[:k + 1], moved[:k + 1]))
    # Identical, bit for bit, up to the step the push began; apart from the next step on.
    assert moved[k][0] == pytest.approx(shaken.event + 1e-3, abs=2e-3)
    assert plain[:k] == moved[:k]


def test_the_two_runs_of_a_fetch_pair_are_one_run_until_the_cube_is_moved():
    from little_world.fields.disturbance import DEFAULTS
    late = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    calm, shaken, plain, moved = twins('fetch', late, 'mobile_manipulator')
    k = first_difference(plain, moved)
    assert k is not None and plain[:k] == moved[:k]
    assert moved[k][0] == pytest.approx(shaken.event, abs=1e-9), 'the step the cube was moved is the first that differs'
    assert all(r.status in ('met', 'kept') for r in calm.results + shaken.results)
