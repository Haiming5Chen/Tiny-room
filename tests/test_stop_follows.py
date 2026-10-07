"""A stop at an object follows where the camera saw it (ADR 0035, FR-016).

The Fetch program looks before it drives: the table's camera sees the cube from anywhere, so
the stop at the cube is placed where the cube is - sideways as far as it moved, towards it no
further than the cart keeps clear of the table. The runner's rules first, with a camera and a
base the test stands in for; then the program the Fetch field solves; then runs with the cube
set down 6 and 10 cm further along the table and 15 cm sideways before the run starts.
"""
from math import cos, radians, sin
from types import SimpleNamespace

import pytest

from little_world.programming.program import RUN_UP, Block, Program, Runner

CUBE = 'objects/cube'
PLANNED = (1.84, 0., .14)
LOOK = Block('look', CUBE, value=0., duration=5., point=PLANNED)
STOP = Block('goto', CUBE, value=.01, duration=60., secondary=.023, point=(1.61, 0., 0.))
AT = Block('pose', value=40., duration=2., angles=(('arm', (20.,)),), point=PLANNED)


class Base:
    """A base that drives where it is told, a centimetre a tick, and turns at once."""

    def __init__(self, at=(0., 0., 0.)):
        self.at = list(at)

    def move(self, runner):
        goal = runner.driver.goal if runner.driver is not None else None
        if goal is None:
            return
        dx, dy = goal[0] - self.at[0], goal[1] - self.at[1]
        far = (dx * dx + dy * dy) ** .5
        step = min(far, .01)
        if far:
            self.at[0] += step * dx / far
            self.at[1] += step * dy / far
        if far <= .01 and runner.driver.heading is not None:
            self.at[2] = runner.driver.heading


def run(program, seen, ticks=6000, aim=None, push=None):
    """The program with the cube seen at `seen`; `push(runner, base)` may move the base."""
    runner, base, angles = Runner(), Base(), {'arm': (0.,)}
    see = lambda target, planned: SimpleNamespace(centre=seen)
    runner.start(program)
    for _ in range(ticks):
        out = runner.tick(.01, angles, base=tuple(base.at), aim=aim, see=see)
        if out['pose']:
            angles = dict(out['pose'])
        base.move(runner)
        if push is not None:
            push(runner, base)
        if runner.state != 'running':
            break
    return runner, base


@pytest.mark.parametrize('seen, stop', [
    ((1.84, .15, .14), (1.61, .15)),         # 15 cm sideways: followed all the way
    ((1.90, 0., .14), (1.633, 0.)),          # 6 cm further along: 2.3 cm, as far as the table allows
    ((1.82, -.03, .14), (1.59, -.03)),       # nearer, and to the right: followed back freely
    ((1.84, 0., .14), (1.61, 0.)),           # where planned: where planned
])
def test_a_stop_at_an_object_follows_it_sideways_and_towards_it_only_as_far_as_allowed(seen, stop):
    runner, base = run(Program((LOOK, STOP)), seen)
    assert runner.state == 'completed'
    assert runner.goal[:2] == pytest.approx(stop, abs=1e-9) and runner.goal[2] == 0.
    assert runner.stop_at == pytest.approx(stop, abs=1e-9)
    assert base.at[:2] == pytest.approx(stop, abs=.011)


def test_the_limit_is_along_the_stops_own_heading():
    """Heading 90 degrees (towards +y): a cube seen 6 cm further in y moves the stop 2.3 cm,
    one seen 6 cm along x moves it all 6 cm."""
    turned = Block('goto', CUBE, value=.01, duration=60., secondary=.023, point=(1.84, -.23, 90.))
    runner, _ = run(Program((LOOK, turned)), (1.84, .06, .14))
    assert runner.goal[:2] == pytest.approx((1.84, -.207), abs=1e-9)
    runner, _ = run(Program((LOOK, turned)), (1.90, 0., .14))
    assert runner.goal[:2] == pytest.approx((1.90, -.23), abs=1e-9)


def test_a_stop_follows_only_its_own_object_and_a_plain_goto_none():
    plain = Block('goto', value=.01, duration=60., point=(1.61, 0., 0.))
    runner, _ = run(Program((LOOK, plain)), (1.84, .15, .14))
    assert runner.goal == (1.61, 0., 0.)
    other = Block('goto', 'objects/other', value=.01, duration=60., point=(1.61, 0., 0.))
    runner, _ = run(Program((LOOK, other)), (1.84, .15, .14))
    assert runner.goal == (1.61, 0., 0.)
    unlimited = Block('goto', CUBE, value=.01, duration=60., point=(1.61, 0., 0.))
    runner, _ = run(Program((LOOK, unlimited)), (1.90, .02, .14))
    assert runner.goal[:2] == pytest.approx((1.67, .02), abs=1e-9), 'secondary 0: no limit'


def test_going_back_to_a_stop_that_followed_goes_back_where_it_was_moved():
    """Pushed off the stop it followed the cube to (ADR 0031), the cart backs off behind that
    stop, not the planned one, and drives back in to it."""
    pushed = []

    def push(runner, base):
        if runner.index == 2 and not pushed:
            base.at[0] -= .08
            pushed.append(True)
    runner, base = run(Program((LOOK, STOP, AT)), (1.84, .15, .14), push=push,
                       aim=lambda point, pose: None)
    assert pushed and runner.retries == 1 and runner.state == 'completed'
    assert runner.stop_at == pytest.approx((1.61, .15), abs=1e-9)
    assert base.at[:2] == pytest.approx((1.61, .15), abs=.011)
    assert RUN_UP > .1


def test_a_pose_the_arm_cannot_reach_where_the_object_was_seen_fails_before_moving():
    """`aim` answers False when the point is out of reach from where the machine stands: a
    pose aimed where a look saw its object then fails at once, saying how far it was seen
    from its plan, instead of reaching for where it was planned (ADR 0035)."""
    look = Block('look', CUBE, value=0., duration=5., point=PLANNED)
    runner, base = run(Program((look, AT)), (1.94, 0., .14), aim=lambda point, pose: False)
    assert runner.state == 'failed'
    assert runner.message == "Seen 10 cm from where it was planned: out of the arm's reach from this stop"
    runner, _ = run(Program((look, AT)), (1.84, 0., .14), aim=lambda point, pose: False)
    assert runner.state == 'completed', 'not moved from its plan: nothing was re-aimed'


def test_a_goto_to_an_object_makes_a_version_4_program_and_keeps_its_fields():
    program = Program((LOOK, STOP))
    assert program.version == 4
    assert Program.from_json(program.to_json()) == program
    assert Program((Block('goto', value=.01, duration=60., point=(1., 0.)),)).version == 2
    with pytest.raises(ValueError, match='0 to 10 m'):
        Block('goto', CUBE, secondary=-.01, duration=60., point=(1., 0., 0.))
    with pytest.raises(ValueError, match='Missing object to drive to'):
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        Program((STOP,)).validate(mobile_manipulator_blueprint(), body_names=('objects/other',))
    assert cos(radians(90.)) == pytest.approx(0., abs=1e-12) and sin(radians(90.)) == 1.


def test_the_fetch_program_looks_before_it_drives_and_its_stops_follow_the_cube():
    """The Fetch field's program, looking: the first look comes before the drive and searches
    the table's width; the stop at the cube and the backing-off stop follow it, towards the
    table no further than the cart's front stays a centimetre clear of the table's edge."""
    pytest.importorskip('mujoco')
    from little_world.control.tool_motion import KEEP_CLEAR, SEARCH_WIDE
    from little_world.inventory.sweep import design, solve
    program = solve('fetch', design('mobile_manipulator'))
    kinds = [b.kind for b in program.blocks]
    assert program.version == 4 and kinds.index('look') < kinds.index('goto')
    first, at_stop = (b for b in program.blocks if b.kind == 'look')
    assert first.value == 0. and first.secondary == at_stop.secondary == SEARCH_WIDE
    stop, back, drop = (b for b in program.blocks if b.kind == 'goto')
    assert stop.target == back.target == 'objects/fetch_cube' and not drop.target
    # The cart's front - its caster, 15.7 cm ahead of the axle - stands 3.3 cm from the table.
    assert stop.secondary == back.secondary == pytest.approx(.033 - KEEP_CLEAR, abs=.002)


def test_a_cube_set_down_6_cm_further_and_15_cm_sideways_is_fetched():
    """Neither the 6 cm further along the table (out of reach from the planned stop, ADR 0032)
    nor 15 cm sideways (outside the camera's 12 cm search round the plan) was fetched."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import Disturbance
    from little_world.inventory.sweep import design, run as field_run
    moved = Disturbance('set down elsewhere', 'move', part='objects/fetch_cube', offset=(.06, .15))
    result = field_run('fetch', design('mobile_manipulator'), disturbance=moved)
    assert all(r.status in ('met', 'kept') for r in result.results), (result.results, result.message)
    (_, planned, seen, actual), *_ = result.seen
    assert seen[0] - planned[0] == pytest.approx(.06, abs=.005) and seen[1] - planned[1] == pytest.approx(.15, abs=.005)
    assert sum((a - b) ** 2 for a, b in zip(seen, actual)) ** .5 < .005


def test_a_cube_set_down_beyond_the_arms_reach_is_left_alone_with_the_reason():
    """10 cm further along: from a stop clear of the table the arm falls short. The program
    stops at the table and says so before the jaws move towards the cube."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import Disturbance
    from little_world.inventory.sweep import design, run as field_run
    moved = Disturbance('set down elsewhere', 'move', part='objects/fetch_cube', offset=(.10, 0.))
    result = field_run('fetch', design('mobile_manipulator'), disturbance=moved)
    assert result.program == 'failed'
    assert result.message == "Seen 10 cm from where it was planned: out of the arm's reach from this stop"
    assert result.result('reached').status == 'met' and result.result('lifted').status != 'met'


def test_leaving_a_stop_that_followed_the_next_stop_moves_as_it_did():
    """The backing-off stop moves as the stop at the cube did - the machine backs off from
    where it stood - not as the cube was seen to have moved once it was there (a cube moved
    as the cart stands at the table, ADR 0033)."""
    back = Block('goto', CUBE, value=.01, duration=60., secondary=.023, point=(1.36, 0., 0.))
    at_stop = Block('look', CUBE, value=0., duration=5., point=PLANNED)
    seen = {'at': (1.84, .02, .14)}
    runner, base = Runner(), Base()
    see = lambda target, planned: SimpleNamespace(centre=seen['at'])
    runner.start(Program((LOOK, STOP, at_stop, back)))
    for _ in range(6000):
        if runner.index == 2:
            seen['at'] = (1.84, .07, .14)        # moved 5 cm more once the cart stood there
        runner.tick(.01, {'arm': (0.,)}, base=tuple(base.at), see=see)
        base.move(runner)
        if runner.state != 'running':
            break
    assert runner.state == 'completed'
    assert runner.followed[1][:2] == pytest.approx((1.61, .02), abs=1e-9)
    assert runner.goal[:2] == pytest.approx((1.36, .02), abs=1e-9), 'as the stop moved, not 7 cm'
