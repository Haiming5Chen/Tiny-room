"""A camera that can fail: frozen on its last picture, or dark (ADR 0038, FR-018).

A program that looks takes the camera's word for where its part is (ADR 0032). A camera
whose stream stops keeps sending its last frame: three pictures that agree, of a world that
has since moved, which is exactly what a look waits for. Each picture now carries its frame
number and how much of it has depth; a look that gets three in a row that are not new, or
have no depth, fails and names the camera, and nothing moves. First the disturbances, then
the camera, then the runner's rule with a camera the test stands in for, then the runs.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from little_world.fields.disturbance import DEFAULTS, Disturbance, Disturbing
from little_world.programming.program import Block, Program, Runner


def test_a_camera_fault_is_a_disturbance_of_its_own_or_comes_with_a_move():
    dark = Disturbance('dark', 'camera', after='reached', camera='dark')
    assert dark.describe() == 'the camera dark, after "reached"'
    frozen = Disturbance('frozen', 'move', part='objects/cube', offset=(0., .05), camera='freeze')
    assert frozen.describe().endswith('; the camera frozen on its last picture just before')
    for bad in (dict(kind='camera'), dict(kind='camera', camera='blurred'),
                dict(kind='move', part='objects/cube', offset=(0., .05), camera='off')):
        with pytest.raises(ValueError):
            Disturbance('bad', **bad)
    assert {'camera frozen as the cube is moved 5 cm', 'camera dark at the table'} <= {d.label for d in DEFAULTS['fetch']}


class Recorder:
    def __init__(self, calls):
        self.calls = calls

    def fail(self, fault):
        self.calls.append(('camera', fault))

    def shift(self, part, offset, turn=0.):
        self.calls.append(('shift', part))


def test_the_camera_fails_first_then_the_part_is_moved():
    """Frozen first: its last picture is of the cube before the move."""
    calls = []
    kick = Disturbing(Disturbance('frozen', 'move', part='objects/cube', offset=(0., .05), camera='freeze'), 'machine/root',
                      Recorder(calls))
    kick.tick(Recorder(calls), None, 0., {})
    assert calls == [('camera', 'freeze'), ('shift', 'objects/cube')] and kick.done
    calls.clear()
    alone = Disturbing(Disturbance('dark', 'camera', camera='dark'), 'machine/root', Recorder(calls))
    alone.tick(Recorder(calls), None, 0., {})
    assert calls == [('camera', 'dark')] and alone.note() == 'dark at 0.0 s'
    blind = Disturbing(Disturbance('dark', 'camera', camera='dark'), 'machine/root')
    blind.tick(Recorder([]), None, 0., {})
    assert blind.note() == 'dark at 0.0 s, with no camera to fail'


def test_a_frozen_camera_sends_its_last_picture_and_a_dark_one_new_pictures_without_depth():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import design, eye
    from little_world.physics.mujoco_backend import MujocoBackend
    field = FIELDS['fetch']
    backend = MujocoBackend()
    scene = field.scene(Entity('machine', design('mobile_manipulator')))
    with World(backend, scene) as world:
        world.start()
        camera = eye(backend, field, scene)
        cube = 'objects/fetch_cube'
        planned = (1.84, 0., .14)
        first = camera(cube, planned)
        assert first is not None and camera.last.frame == 1 and camera.last.valid > .9
        camera(cube, planned)
        assert camera.last.frame == 2
        camera.fail('freeze')                                # its last frame: the cube where it is
        backend.shift(cube, (0., .05))
        world.step({})
        again = [camera(cube, planned) for _ in range(3)]
        assert {camera.last.frame} == {3} and all(np.allclose(s.centre, first.centre, atol=.003) for s in again)
        assert camera(cube, (1.84, .05, .14)) is not None and camera.last.frame == 3     # moved, still seen where it was
        camera.fail('dark')
        assert camera(cube, planned) is None and camera.last.frame == 4 and camera.last.valid == 0.
        camera(cube, planned)
        assert camera.last.frame == 5
        camera.fail(None)
        seen = camera(cube, (1.84, .05, .14))
        assert camera.last.frame == 6 and seen is not None and seen.centre[1] == pytest.approx(.05, abs=.003)
        with pytest.raises(ValueError):
            camera.fail('smudged')


CUBE = 'objects/cube'
OPEN = Block('action', 'jaws', -1, .5)
READY = Block('pose', value=40., duration=2., angles=(('arm', (5.,)),))
STOP = Block('goto', value=.01, duration=60., point=(1.6, 0., 0.))
LOOK = Block('look', CUBE, value=.3, duration=5., point=(1.84, 0., .14))
ABOVE = Block('pose', value=40., duration=2., angles=(('arm', (10.,)),), point=(1.84, 0., .20))
AT = Block('pose', value=40., duration=2., angles=(('arm', (20.,)),), point=(1.84, 0., .14))
CLOSE = Block('action', 'jaws', 1, .8)
CHECK = Block('grasp', CUBE, duration=.5)
FETCH = Program((OPEN, READY, STOP, LOOK, ABOVE, AT, CLOSE, CHECK))


class Camera:
    """Sees the cube at (1.84, 0, .14) in pictures numbered as a stream would number them -
    until `stuck(t)`, when it sends its last picture again, or `dark(t)`, when its pictures
    have no depth."""

    def __init__(self, stuck=lambda t: False, dark=lambda t: False):
        self.stuck, self.dark, self.t, self.frames, self.last = stuck, dark, 0., 0, None

    def __call__(self, target, planned, search=None):
        if not (self.stuck(self.t) and self.last is not None):
            self.frames += 1
            self.last = SimpleNamespace(frame=self.frames, valid=0. if self.dark(self.t) else 1.)
        return None if self.last.valid == 0. else SimpleNamespace(centre=(1.84, 0., .14))


def run(camera, runner=None, ticks=3000):
    runner = runner or Runner()
    angles, sent, log = {'arm': (0.,)}, [], []
    runner.start(FETCH)
    for _ in range(ticks):
        out = runner.tick(.01, angles, held=frozenset({CUBE}), base=(1.6, 0., 0.), see=camera)
        if hasattr(camera, 't'):
            camera.t += .01
        if out['pose']:
            angles = dict(out['pose'])
            sent.append(angles['arm'][0])
        if runner.message not in log:
            log.append(runner.message)
        if runner.state != 'running':
            break
    return runner, sent, log


def test_a_look_at_a_camera_stuck_on_one_picture_names_it_and_moves_nothing():
    """Stuck from the start of the look: three pictures in a row that are not new."""
    runner, sent, _ = run(Camera(stuck=lambda t: t > .6))
    assert runner.state == 'failed' and runner.message == "Looked for cube: the camera's picture is not new"
    assert max(sent) <= 5.                              # never went past its approach pose
    # Taken on trust, the same picture three times is a steady look: the silent case.
    trusting, sent, _ = run(Camera(stuck=lambda t: t > .6), Runner(checks=False))
    assert trusting.state == 'completed' and max(sent) == 20.


def test_a_look_at_a_dark_camera_names_it():
    runner, sent, _ = run(Camera(dark=lambda t: t > .6))
    assert runner.state == 'failed' and runner.message == "Looked for cube: the camera's picture has no depth"
    assert max(sent) <= 5.


def test_stuck_before_the_reach_it_looks_again_and_then_names_the_camera():
    """The look done, the camera sticks: the picture before the jaws go down is not new, so the
    jaws do not go down; looking again finds the camera still stuck."""
    runner, sent, log = run(Camera(stuck=lambda t: t > 1.))
    assert "Reaching for cube: the camera's picture is not new: looking again" in log
    assert runner.state == 'failed' and runner.message == "Looked for cube: the camera's picture is not new"
    assert max(sent) <= 10.                             # above the cube at most, never at it
    no_second = Runner(regrasps=0)
    runner, _, _ = run(Camera(stuck=lambda t: t > 1.), no_second)
    assert runner.message == "Reaching for cube: the camera's picture is not new"


def test_a_camera_whose_pictures_carry_no_numbers_is_never_doubted():
    plain = lambda target, planned, search=None: SimpleNamespace(centre=(1.84, 0., .14))
    runner, sent, _ = run(plain)
    assert runner.state == 'completed'


def test_the_report_says_why_the_set_ups_missed_and_when_the_pictures_were_not_checked():
    from little_world.fields.goals import Result
    from little_world.fields.variation import Ranges, Variation
    from little_world.inventory.sweep import Disturbed, Run, disturbed_markdown

    def runs(ok, message):
        out = []
        for i in range(3):
            label = 'as designed' if i == 0 else f'repeat {i}'
            out.append(Run(Variation(label), (Result('delivered', 'Cube resting in the bin', 'met' if ok else 'missed',
                                                     30. if ok else None),),
                           program='completed' if ok else 'failed', message='Completed' if ok else message))
        return tuple(out)
    stuck = "Looked for fetch_cube: the camera's picture is not new"
    result = Disturbed('fetch', 'arm on a cart', 'program', 60., None, Ranges(), None,
                       (('none', '', runs(True, '')), ('frozen', 'frozen', runs(False, stuck))), checks=False)
    page = disturbed_markdown(result)
    assert f'| every set-up: "{stuck}" |' in page
    assert 'took every picture as new and lit' in page


def test_a_frozen_camera_is_named_before_any_grasp_and_on_trust_misses_twice():
    """FR-018's check on the design as designed: frozen as the cube is moved 5 cm at the table.
    On trust the program grasps where the frozen picture shows the cube, twice (ADR 0033's
    second try included), and misses; checked, it stops at the look, nothing grasped."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run as field_run
    frozen = next(d for d in DEFAULTS['fetch'] if d.label == 'camera frozen as the cube is moved 5 cm')
    bp = design('mobile_manipulator')
    checked = field_run('fetch', bp, disturbance=frozen)
    assert checked.message == "Looked for fetch_cube: the camera's picture is not new" and checked.regrasped == 0
    assert checked.result('reached').status == 'met' and checked.result('lifted').status == 'missed'
    trusting = field_run('fetch', bp, disturbance=frozen, checks=False)
    assert trusting.message == 'Nothing held: the grasp missed' and trusting.regrasped == 1


def test_a_dark_camera_is_named_at_the_look():
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run as field_run
    dark = next(d for d in DEFAULTS['fetch'] if d.label == 'camera dark at the table')
    result = field_run('fetch', design('mobile_manipulator'), disturbance=dark)
    assert result.message == "Looked for fetch_cube: the camera's picture has no depth" and result.regrasped == 0
