"""Looking again without dragging the cube or doubting it (ADR 0037, OPEN LW-022 and LW-023).

Two faults the paired runs of ADR 0036 showed in looking again (ADR 0033). A reach stopped on
the cube went straight back to the stop's approach with a jaw still on the cube and dragged it
off the table; now the arm first rises back to the pose it reached down from. And the one
picture before the jaws go down found nothing when the open jaws hid the cube's top face, so
the program looked again though nothing had moved; now what the picture shows where the cube
was seen decides - its surface, something nearer over it, or the table beyond it. First the
place on made-up pictures, then the runner's rules with joints the test moves, then the runs
that had the faults.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from little_world.perception.boxes import _enter, find_box, place
from little_world.programming.program import Block, Program, Runner

SIZE = (.025, .025, .04)                # the Fetch cube
CUBE_AT = np.array((0., 0., .02))       # standing on the table, z = 0
CAMERA = np.array((.6, 0., .45))        # on a stand beyond the table, looking down at it


def picture(cube=CUBE_AT, cover=None):
    """A depth camera's points over the table round the cube: each ray's first hit among the
    table, the cube standing at `cube` (None: no cube) and a box `cover` = (centre, size)."""
    u, v = np.meshgrid(np.linspace(-.12, .12, 121), np.linspace(-.10, .10, 101))     # 2 mm apart
    target = np.stack((u.ravel(), v.ravel(), np.zeros(u.size)), axis=1)
    rays = target - CAMERA                                    # the table point is at s = 1
    s = np.ones(len(rays))
    for centre, size in ((cube, SIZE), cover or (None, None)):
        if centre is not None:
            s = np.minimum(s, _enter(CAMERA, rays, np.asarray(centre), np.asarray(size) / 2))
    return CAMERA + s[:, None] * rays


def test_the_place_says_there_empty_or_hidden_from_what_the_rays_meet():
    assert place(picture(), CAMERA, CUBE_AT, SIZE, .005) == 'there'
    assert place(picture(cube=None), CAMERA, CUBE_AT, SIZE, .005) == 'empty'
    # Moved 5 cm sideways: where it was, the rays reach the table; where it is, its surface.
    moved = picture(cube=CUBE_AT + (0., .05, 0.))
    assert place(moved, CAMERA, CUBE_AT, SIZE, .005) == 'empty'
    assert place(moved, CAMERA, CUBE_AT + (0., .05, 0.), SIZE, .005) == 'there'
    # The open jaws' palm between the camera and the cube, hiding most of it.
    palm = ((.08, 0., .07), (.03, .08, .06))
    assert place(picture(cover=palm), CAMERA, CUBE_AT, SIZE, .005) == 'hidden'
    # Its top face covered and its front plain: the finder, which needs the top face, finds
    # nothing; the place shows the cube there - LW-022 in one picture.
    lid = picture(cover=((0., 0., .06), (.03, .08, .02)))
    assert find_box(picture(), CUBE_AT, SIZE, .002, np.random.default_rng(1), CAMERA) is not None
    assert find_box(lid, CUBE_AT, SIZE, .002, np.random.default_rng(1), CAMERA) is None
    assert place(lid, CAMERA, CUBE_AT, SIZE, .005) == 'there'
    assert place(picture(), CAMERA, CUBE_AT + (5., 0., 0.), SIZE, .005) == 'hidden'      # not in the picture: no answer


CUBE = 'objects/cube'
OPEN = Block('action', 'jaws', -1, .5)
READY = Block('pose', value=40., duration=2., angles=(('arm', (5., 50.)),))
STOP = Block('goto', value=.01, duration=60., point=(1.6, 0., 0.))
LOOK = Block('look', CUBE, value=.3, duration=5., point=(1.84, 0., .14))
ABOVE = Block('pose', value=40., duration=2., angles=(('arm', (10., 10.)),), point=(1.84, 0., .20))
AT = Block('pose', value=40., duration=2., angles=(('arm', (20., 0.)),), point=(1.84, 0., .14))
CLOSE = Block('action', 'jaws', 1, .8)
CHECK = Block('grasp', CUBE, duration=.5)
LIFT = Block('pose', value=40., duration=2., angles=(('arm', (10., 10.)),), point=(1.84, 0., .20))
FETCH = Program((OPEN, READY, STOP, LOOK, ABOVE, AT, CLOSE, CHECK, LIFT))


class Camera:
    """Sees the cube at `cube(t)`; before the jaws go down (`low`), finds nothing and says
    what the place shows, when `shows` is given."""

    def __init__(self, cube, low=None, shows=None):
        self.cube, self.low, self.shows, self.asked, self.t = cube, low, shows, [], 0.

    def __call__(self, target, planned, search=None):
        if self.low is not None and self.low(self.t):
            return None
        return SimpleNamespace(centre=self.cube(self.t))


def run(camera, holds=lambda: True, stuck=None, ticks=4000, runner=None):
    """Tick a runner with an arm that goes where it is sent, except that while `stuck(runner,
    angles)` it stays put - a jaw resting on something. Returns the runner, its log, and every
    arm command after the program first said it would look again."""
    runner = runner or Runner()
    angles, log, after = {'arm': (0., 0.)}, [], []
    runner.start(FETCH)
    for _ in range(ticks):
        block = runner.program.blocks[runner.index]
        held = frozenset({CUBE}) if block.kind == 'grasp' and holds() else frozenset()
        out = runner.tick(.01, angles, held=held, base=(1.6, 0., 0.), see=camera)
        camera.t += .01
        if out['pose'] and not (stuck and runner.state == 'running' and stuck(runner, out['pose']['arm'])):
            angles = dict(out['pose'])
        if runner.message not in log:
            log.append(runner.message)
        if runner.regrasps and out['pose']:
            after.append(tuple(round(v, 3) for v in out['pose']['arm']))
        if runner.state != 'running':
            break
    return runner, log, after


def test_a_reach_blocked_on_the_cube_rises_the_way_it_came_before_going_back():
    """The jaws come down on the cube and stop halfway: the arm goes back up to the pose it
    reached down from - (10, 10) - before it turns for the stop's approach, (5, 50)."""
    def stuck(runner, sent):                        # the first reach down stops at (15, 5)
        return runner.program.blocks[runner.index] is AT and not runner.regrasps and sent[0] > 15.
    runner, log, after = run(Camera(lambda t: (1.84, 0., .14)), stuck=stuck)
    assert 'Blocked reaching down: looking again' in log and runner.state == 'completed', log
    up = after.index((10., 10.))                    # back where it reached down from
    assert all(elbow <= 10. + 1e-9 for _, elbow in after[:up])         # not swung out on the way
    assert after[up + 1:] and max(elbow for _, elbow in after[up:]) == 50.   # then to the approach


def test_a_missed_grasp_opens_the_jaws_then_rises_before_going_back():
    tries = {'n': 0}

    def holds():
        tries['n'] += 1
        return tries['n'] > 60                     # nothing held the first time round
    runner, log, after = run(Camera(lambda t: (1.84, 0., .14)), holds=holds)
    assert 'Nothing held: looking again' in log and runner.state == 'completed', log
    up = after.index((10., 10.))
    assert all(elbow <= 10. + 1e-9 for _, elbow in after[:up])


def test_seen_moved_before_the_reach_it_goes_straight_back_without_rising():
    """The arm has not gone down: nothing to rise from."""
    runner, log, after = run(Camera(lambda t: (1.84, 0., .14) if t < 2.5 else (1.84, .05, .14)))
    assert 'Moved since the look: looking again' in log and runner.state == 'completed'
    assert after[0] != (10., 10.) and after[0][1] > 10.       # the first command heads for the approach


def lows(shows):
    """A camera that finds nothing once the jaws are over the cube, and says `shows` there."""
    camera = Camera(lambda t: (1.84, 0., .14), low=lambda t: t > 2.5)    # once the look is done
    if shows is not None:
        camera.place = lambda target, where: camera.asked.append(where) or shows
    return camera


@pytest.mark.parametrize('shows, again', [('there', False), ('hidden', False), ('empty', True), (None, True)])
def test_found_nowhere_before_the_reach_the_place_decides(shows, again):
    """Its surface where it was seen, or something nearer over it: it has not gone, the jaws
    go down. The table beyond where it was - or a camera that cannot say - and it looks again."""
    camera = lows(shows)
    runner, log, _ = run(camera, runner=Runner(regrasps=1))
    assert ('Moved since the look: looking again' in log) is again, log
    if shows is not None:
        assert camera.asked and camera.asked[0] == (1.84, 0., .14)       # where the look saw it


def test_the_cube_hidden_under_the_jaws_is_fetched_without_looking_again():
    """LW-022: a drawn set-up (repeat 35 of ADR 0035's sweep) whose picture before the jaws
    went down found nothing - the palm hid the cube's top face - and looked again, 4 s lost."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, ranges_for, run as field_run, setups
    bp = design('mobile_manipulator')
    drawn = next(v for v in setups(ranges_for('fetch'), 59, 1) if v.label == 'repeat 35')
    result = field_run('fetch', bp, drawn)
    assert result.regrasped == 0 and all(r.status in ('met', 'kept') for r in result.results), result.message
    assert result.result('delivered').time < 37.


def test_a_reach_stopped_on_the_moved_cube_no_longer_drags_it_off_the_table():
    """LW-023: the pair ADR 0036 found broken (repeat 9, the cube moved 5 cm sideways 2 s
    after the look): it moved just after the picture before the jaws went down, a jaw came down
    on it, and rising to look again the arm dragged it over the table's edge."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, ranges_for, run as field_run, setups
    late = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    drawn = next(v for v in setups(ranges_for('fetch'), 59, 1) if v.label == 'repeat 9')
    result = field_run('fetch', design('mobile_manipulator'), drawn, disturbance=late)
    assert result.regrasped == 1
    assert all(r.status in ('met', 'kept') for r in result.results), (result.message, result.results)
