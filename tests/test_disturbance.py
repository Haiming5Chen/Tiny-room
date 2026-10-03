"""Disturbances during a run (ADR 0030): a shove, a part moved - when they happen, what the
adapter does with them, how a sweep reports them, and what the aimed poses of ADR 0025 do
about a cart shoved at the table."""
from types import SimpleNamespace

import pytest

from little_world.fields.disturbance import DEFAULTS, SETTLED, Disturbance, Disturbing
from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation


def test_a_disturbance_says_what_happens_and_refuses_what_cannot():
    push = Disturbance('shoved', 'push', after='reached', still=.2, delay=.1, impulse=4.)
    assert push.describe() == '4 N s over 0.1 s, 90 deg left of its heading, after "reached", once still for 0.2 s, 0.1 s later'
    move = Disturbance('cube moved', 'move', part='objects/fetch_cube', offset=(0, .03))
    assert move.describe() == 'fetch_cube moved +0.0 cm, +3.0 cm, from the start'
    for bad in (dict(kind='kick', impulse=1.), dict(kind='push'), dict(kind='move', part='objects/x'),
                dict(kind='push', impulse=1., delay=-1.), dict(kind='push', impulse=1., seconds=0.)):
        with pytest.raises(ValueError):
            Disturbance('bad', **bad)
    assert {d.after for d in DEFAULTS['fetch']} == {'reached'} and {d.after for d in DEFAULTS['sprint']} == {'start'}


class Recorder:
    def __init__(self):
        self.calls = []

    def push(self, body, force=(0., 0., 0.)):
        self.calls.append(('push', body, tuple(round(f, 9) for f in force)))

    def shift(self, body, offset):
        self.calls.append(('shift', body, tuple(offset)))


def state(x, y, speed=0., facing=90.):
    """The machine's base at (x, y), facing `facing` degrees, moving at `speed` along X."""
    from math import cos, radians, sin
    half = radians(facing) / 2
    pose = SimpleNamespace(position=(x, y, .1), quaternion=(cos(half), 0., 0., sin(half)))
    return SimpleNamespace(bodies={'machine/root': SimpleNamespace(pose=pose, linear_velocity=(speed, 0., 0.))})


def test_a_push_waits_for_its_goal_and_a_still_machine_then_shoves_it_to_its_left():
    backend = Recorder()
    kick = Disturbing(Disturbance('shoved', 'push', after='reached', still=.2, delay=.1, impulse=4., seconds=.1),
                      'machine/root')
    kick.tick(backend, state(0, 0, speed=.3), 1., {})                 # the goal is not met yet
    kick.tick(backend, state(0, 0, speed=.3), 2., {'reached': 1.5})   # met, but still moving
    kick.tick(backend, state(0, 0), 2.1, {'reached': 1.5})            # still from 2.1 s ...
    kick.tick(backend, state(0, 0), 2.35, {'reached': 1.5})           # ... still long enough: 0.1 s to go
    kick.tick(backend, state(0, 0), 2.4, {'reached': 1.5})
    assert backend.calls == []
    kick.tick(backend, state(0, 0), 2.45, {'reached': 1.5})
    # Facing +Y, its left is -X: 4 N s over 0.1 s is 40 N that way.
    assert backend.calls == [('push', 'machine/root', (-40., 0., 0.))] and kick.began == 2.45
    kick.tick(backend, state(-.005, 0), 2.5, {'reached': 1.5})
    kick.tick(backend, state(-.01, 0), 2.56, {'reached': 1.5})
    assert backend.calls[-1] == ('push', 'machine/root', (0., 0., 0.))
    kick.tick(backend, state(-.02, .03), 2.56 + SETTLED, {'reached': 1.5})
    assert kick.moved == pytest.approx(.02) and kick.done        # along the push only
    assert kick.note() == 'shoved at 2.5 s, the base went 2.0 cm the way it was pushed'


def test_a_move_shifts_its_part_once_and_a_disturbance_that_never_came_says_so():
    backend = Recorder()
    kick = Disturbing(Disturbance('cube moved', 'move', after='reached', part='objects/fetch_cube', offset=(0., .03)),
                      'machine/root')
    for t in (1., 2., 3.):
        kick.tick(backend, state(0, 0), t, {'reached': 1.5})
    assert backend.calls == [('shift', 'objects/fetch_cube', (0., .03))] and kick.note() == 'cube moved at 2.0 s'
    late = Disturbing(DEFAULTS['fetch'][0], 'machine/root')
    assert late.note() == 'shoved 4 N s at the table: never happened (reached not met)'


def test_the_adapter_pushes_a_body_and_moves_a_loose_one():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import field_scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    backend = MujocoBackend()
    with World(backend, field_scene('fetch', Entity('machine', mobile_platform_blueprint()))) as world:
        state0 = world.start()
        for _ in range(100):
            world.step({})
        before = world.step({}).bodies['machine/root'].pose.position
        backend.push('machine/root', (80., 0., 0.))
        for _ in range(50):
            world.step({})
        backend.push('machine/root')
        for _ in range(200):
            after = world.step({})
        assert after.bodies['machine/root'].pose.position[0] - before[0] > .01
        cube = after.bodies['objects/fetch_cube'].pose.position
        backend.shift('objects/fetch_cube', (0., .03))
        moved = backend.snapshot().bodies['objects/fetch_cube']
        assert moved.pose.position[1] - cube[1] == pytest.approx(.03) and moved.linear_velocity == pytest.approx((0, 0, 0))
        with pytest.raises(ValueError, match='not loose'):
            backend.shift('field/table', (0., .01))
        with pytest.raises(ValueError, match='no body'):
            backend.push('field/nothing', (1., 0., 0.))
        assert state0 is not None


def test_a_part_fixed_to_the_world_between_the_jaws_is_not_held():
    """Found by the first disturbance sweeps: shoved 6 N s, the cart's corrected pose closed
    the jaws on the table's edge, the grasp check counted the table as held, and the program
    went on to carry it (ADR 0030). Only something that can move is held."""
    from little_world.programming.observations import Observations
    names = {1: 'machine/arm_finger_left_pad', 2: 'machine/arm_finger_right_pad', 3: 'field/table', 4: 'objects/fetch_cube'}
    geom_body = [1, 2, 3, 4]

    def world(*pairs):
        contacts = [SimpleNamespace(geom1=a, geom2=b, dist=-.001) for a, b in pairs]
        model = SimpleNamespace(nbody=5, body=lambda i: SimpleNamespace(name=names.get(i, 'world')),
                                geom_bodyid=geom_body, body_weldid=[0, 1, 1, 0, 4])
        return Observations(model, SimpleNamespace(ncon=len(contacts), contact=contacts))
    assert world((0, 2), (1, 2)).grasped() == frozenset()                       # both pads on the table
    assert world((0, 3), (1, 3)).grasped() == frozenset({'objects/fetch_cube'})
    assert world((0, 3), (1, 2)).grasped() == frozenset()                       # one pad each


def made_up(groups):
    from little_world.inventory.sweep import Disturbed, Run

    def runs(times, pushed=None):
        out = []
        for i, t in enumerate(times):
            label = 'as designed' if i == 0 else f'repeat {i}'
            results = (Result('reached', 'Reached the table', 'met', 9.6),
                       Result('delivered', 'Cube resting in the bin', 'met' if t else 'missed', t))
            out.append(Run(Variation(label, x=.001 * i), results, pushed=pushed))
        return tuple(out)
    return Disturbed('fetch', 'arm on a cart', 'program', 60., None, Ranges(), None,
                     tuple((label, text, runs(times, pushed)) for label, text, times, pushed in groups))


def test_the_report_compares_each_set_up_with_itself_undisturbed():
    from little_world.inventory.sweep import disturbed_markdown
    result = made_up((('none', '', (33., 33., 34., 33.), None),
                      ('shoved 6 N s at the table', 'a push', (41., 40., 42., None), .081)))
    page = disturbed_markdown(result)
    assert page.startswith('# Fetch, disturbed: arm on a cart')
    assert 'the same 4 set-ups - the design as designed and 3 drawn at random' in page
    assert '| none | 4 of 4 | 3 of 3, at least 37 % | - | - | - |' in page
    assert '| shoved 6 N s at the table | 3 of 4 | 2 of 3, at least 14 % | +8.0 s | 8.1 cm (8.1 to 8.1) | repeat 3 |' in page
    assert '- **shoved 6 N s at the table**: a push.' in page


def test_aimed_poses_recover_a_cart_shoved_8_cm_at_the_table_and_poses_as_taught_miss():
    """FR-006's check, measured: shoved 6 N s to its left once stopped at the table, the
    cart slides about 8 cm. With ADR 0025's corrections the arm finds the cube where the
    cart now stands and the run meets every goal, later; run as taught it closes on air."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run
    shove = DEFAULTS['fetch'][1]
    corrected = run('fetch', design('mobile_manipulator'), disturbance=shove)
    assert all(x.status in ('met', 'kept') for x in corrected.results), corrected.results
    assert .05 < corrected.pushed < .12
    taught = run('fetch', design('mobile_manipulator'), disturbance=shove, corrections=0)
    assert {x.id: x.status for x in taught.results}['lifted'] == 'missed'
