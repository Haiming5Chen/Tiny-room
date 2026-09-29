"""Contracts for the doorway and the tilt table (ADR 0020).

The defect: the fields asked machines to go straight - a lane, a slope, a step, a
crate - so nothing tested turning where turning matters, or how steep a side slope a
machine stands on; and ADR 0015's stance, predicted from the design, was checked only
standing still on the level.
"""
from math import atan2, cos, degrees, radians, sin
import pytest

from little_world.components import Transform
from little_world.core.state import BodyState, State
from little_world.fields import FIELDS, tilt_target, TILT_MAX
from little_world.fields.goals import GoalTracker, TiltHold, between


def body(q=(1., 0., 0., 0.), x=0.):
    return BodyState(Transform((x, 0., 0.), q), (0., 0., 0.), (0., 0., 0.))


def roll(degrees_):
    a = radians(degrees_) / 2
    return (cos(a), sin(a), 0., 0.)


# -- the tilt table's goals: plain states ----------------------------------------------------

def test_held_means_the_table_got_there_with_the_machine_still_on_its_feet():
    goals = (TiltHold('h20', 'Held at 20', 'field/table', 20.), TiltHold('h30', 'Held at 30', 'field/table', 30.))
    tracker = GoalTracker(goals, 'machine/base')
    tracker.update(State(0., {'field/table': body(roll(10)), 'machine/base': body(roll(10))}))
    tracker.update(State(5., {'field/table': body(roll(21)), 'machine/base': body(roll(23))}))
    assert [r.status for r in tracker.results()] == ['met', 'open']
    tracker.update(State(9., {'field/table': body(roll(27)), 'machine/base': body(roll(60))}))
    h20, h30 = tracker.results(finished=True)
    assert h20.status == 'met' and h20.time == 5.
    assert h30.status == 'missed' and h30.detail == 'tipped over at 27 deg'
    assert between(roll(27), roll(60)) == pytest.approx(33.)


def test_the_table_follows_a_slow_schedule_to_its_top():
    assert tilt_target(0.) == 0. and tilt_target(1.) == 0.
    assert tilt_target(11.) == pytest.approx(20.) and tilt_target(100.) == TILT_MAX


# -- predicted from the design -----------------------------------------------------------------

def test_the_static_tip_angles_are_the_stability_factor_of_the_stance():
    """A box on a level floor: tipping sideways when tan(angle) = half its width over the
    height of its centre of mass."""
    from little_world.construction.structure import settle
    box = [(x, y, z) for x in (-.2, .2) for y in (-.1, .1) for z in (0., .3)]
    stance = settle(box, (0., 0., .15))
    assert stance.height == pytest.approx(.15)
    assert stance.tip('left') == pytest.approx(degrees(atan2(.1, .15)), abs=.02)
    assert stance.tip('forward') == pytest.approx(degrees(atan2(.2, .15)), abs=.02)


def test_rocking_onto_a_caster_is_not_tipping_over():
    """Two wheels on an axle and a caster 5 mm clear at each end: it rests on the axle and
    the front caster, 1 cm of margin behind the axle - yet tilted back it only rocks onto
    the back caster; it rolls over when its centre of mass passes that caster instead."""
    from little_world.construction.structure import settle
    points = [(0., -.1, 0.), (0., .1, 0.), (.2, 0., .005), (-.2, 0., .005)]
    points += [(x, y, .3) for x in (-.2, .2) for y in (-.1, .1)]
    stance = settle(points, (.01, 0., .1))
    assert not stance.tips_over
    assert stance.tip('back') > 55. and stance.tip('forward') > 55.
    assert stance.tip('left') == pytest.approx(degrees(atan2(.1, .1)), abs=3.)


# -- in the simulator ---------------------------------------------------------------------------

mujoco = pytest.importorskip('mujoco')
from little_world import Entity, World  # noqa: E402
from little_world.construction.structure import standing  # noqa: E402
from little_world.control.mujoco_drive import MujocoDrive  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.core.component import Body  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint  # noqa: E402
from little_world.robots.mobile_platform import mobile_platform_blueprint  # noqa: E402


def on_the_tilt_table(bp, seconds=33.):
    """Run the tilt table with the machine holding still; (goal results, table angle when
    the machine tipped or None)."""
    field = FIELDS['tilt']
    root = 'machine/' + next(b.id for b in bp.components if isinstance(b, Body) and b.parent is None)
    backend = MujocoBackend()
    with World(backend, field.scene(Entity('machine', bp))) as world:
        state = world.start()
        drive, arm = MujocoDrive(backend, bp), MujocoKeyboardControl(backend, bp)
        tracker = GoalTracker(field.goals, root)
        for _ in range(round(seconds / world.timestep)):
            commands = dict(drive.step_commands((0., 0.), world.timestep, angular=True))
            commands.update(arm.step_commands(world.timestep))
            commands.update(field.commands(state))
            state = world.step(commands)
            tracker.update(state)
        return {r.id: r for r in tracker.results(finished=True)}, getattr(tracker, 'tipped_at', None), state


def test_the_tilt_table_turns_on_schedule_under_a_machine():
    results, tipped, state = on_the_tilt_table(mobile_platform_blueprint(), 12.)
    from little_world.fields.goals import tilt
    assert tilt(state.bodies['field/tilt_table'].pose.quaternion) == pytest.approx(tilt_target(12.), abs=1.)


def test_the_mobile_manipulator_tips_where_its_stance_says_and_the_platform_holds():
    """Predicted from the rigid design: the arm lifts the manipulator's centre of mass to
    9.8 cm over the table with its wheels' outer edges 13.7 cm to the side of it, so it
    goes over near 54 degrees - 56 about the trip rail's edge. It goes at 54: one caster,
    loaded and pushed sideways, swivels 86 degrees as the table rises and its wheel's
    contact moves, which the rigid prediction does not know. The bare platform's centre
    of mass is 4 cm lower: past the table's 60 degrees. The rail keeps both from sliding."""
    from little_world.fields import railed
    manipulator = mobile_manipulator_blueprint()
    stance = standing(manipulator)
    predicted = railed(stance.tip('right'), stance.height)
    assert 1. < predicted - stance.tip('right') < 2.
    results, tipped, _ = on_the_tilt_table(manipulator)
    assert tipped is not None and abs(tipped - predicted) < 3., (tipped, predicted)
    assert results['held_50'].status == 'met' and results['held_60'].status == 'missed'
    platform = mobile_platform_blueprint()
    assert standing(platform).tip('right') > TILT_MAX
    results, tipped, _ = on_the_tilt_table(platform)
    assert tipped is None and all(r.status == 'met' for r in results.values()), results


def test_the_trip_rail_is_set_against_the_machine_on_the_table():
    from little_world.fields import RAIL, TILT_TABLE, trip_rail
    assert trip_rail(None) == pytest.approx(-(TILT_TABLE[1] / 2 - RAIL))
    assert trip_rail(mobile_platform_blueprint()) == pytest.approx(-.164, abs=.002)


def test_a_skid_steer_rover_cannot_turn_on_the_spot_on_concrete():
    """Four 1 N m wheels on a 13.45 kg rover give 4 x (1/0.065) x 0.164 = 10.1 N m to turn
    it; scrubbing the wheels sideways takes about 0.95 x 13.45 x 9.81 x 0.247 = 31 N m.
    The platform's swivel casters need no scrubbing."""
    from little_world.assets.catalog import BY_ID
    from little_world.control.navigation import BasePose, wheel_targets
    turned = {}
    for name, bp in (('rover', BY_ID['ready_rover_4'].blueprint()), ('platform', mobile_platform_blueprint())):
        backend = MujocoBackend()
        with World(backend, FIELDS['sprint'].scene(Entity('machine', bp))) as world:
            world.start()
            drive = MujocoDrive(backend, bp)
            base = BasePose(backend, drive, bp)
            left, right = wheel_targets(0., 1., base.radius, base.track)
            for _ in range(round(3. / world.timestep)):
                world.step(drive.step_commands((left, right), world.timestep, angular=True))
            turned[name] = degrees(base.pose()[2])
    assert abs(turned['rover']) < 15. and abs(turned['platform']) > 90., turned


def test_the_doorway_program_takes_the_platform_through_without_touching_the_frame():
    import sys
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    from test_fetch import machine_in, run
    from little_world.fields import DOOR_Y, WALL_X
    from little_world.programming.program import Block, Program
    world, backend, control, drive, base, _ = machine_in('doorway', mobile_platform_blueprint())
    with world:
        for _ in range(500):       # the frame's posts stand still with nothing touching them
            world.step({})
        for i in range(2):
            post = backend.data.body(f'objects/door_post_{i}')
            assert abs(post.xpos[1] - (DOOR_Y + (-1) ** (i + 1) * .27)) < .002
        stops = ((WALL_X - .7, DOOR_Y, 0.), (WALL_X + .6, DOOR_Y, 0.), (WALL_X + 1., DOOR_Y, 0.))
        program = Program(tuple(Block('goto', value=.02, duration=40., point=p) for p in stops))
        runner, goals = run(world, backend, control, drive, base, program, FIELDS['doorway'].goals, 60.)
        assert runner.state == 'completed', runner.message
        assert {g: r.status for g, r in goals.items()} == {
            'through': 'met', 'parked': 'met', 'frame': 'kept', 'upright': 'kept'}
