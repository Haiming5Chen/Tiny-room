"""Contracts for poses aimed at a point (ADR 0025).

The defect: a program's arm poses were joint angles solved for the machine as it stood when
the program was planned. With 0.5 kg on its deck behind the arm, the arm on a cart rides on
its rear caster and rocks 5 degrees onto the front one as the arm lifts: the same angles left
the cube 12 mm short of the Fetch field's 5 cm line until the cart rocked back on its way to
the bin (ADR 0024, OPEN LW-016).
"""
import math
import pytest

from little_world.programming.program import CORRECTIONS, Block, Program, Runner

AIMED = Block('pose', value=30., duration=2., angles=(('shoulder', (40.,)),), point=(.5, 0., .3))


def follow(runner, aim, steps=600, stuck=lambda: False):
    """Joints that go exactly where they are sent, until `stuck()` says they stop."""
    angles = {'shoulder': (0.,)}
    for _ in range(steps):
        out = runner.tick(.01, angles, aim=aim)
        if out['pose'] and not stuck():
            angles = dict(out['pose'])
        if runner.state != 'running':
            break
    return angles


def test_an_aimed_pose_is_version_2_data_that_round_trips():
    p = Program((AIMED,))
    assert p.version == 2 and Program.from_json(p.to_json()) == p
    for bad in ((.5, 0.), (.5, 0., math.nan), (500., 0., 0.)):
        with pytest.raises(ValueError):
            Block('pose', value=30., angles=(('a', (1.,)),), point=bad)
    with pytest.raises(ValueError):
        Block('wait', point=(1., 2., 3.))


def test_where_the_tool_got_to_is_checked_and_the_pose_solved_again_until_it_is_there():
    asked = []

    def aim(point, pose):
        asked.append((point, pose))
        return (('shoulder', (44.,)),) if len(asked) == 1 else None
    r = Runner()
    r.start(Program((AIMED,)))
    angles = follow(r, aim)
    assert r.state == 'completed' and angles == {'shoulder': (44.,)}
    assert asked == [((.5, 0., .3), (('shoulder', (40.,)),)), ((.5, 0., .3), (('shoulder', (44.,)),))]


def test_corrections_are_few_and_one_that_cannot_settle_does_not_fail_the_program():
    asked = []

    def never_there(point, pose):
        asked.append(pose)
        return (('shoulder', (pose[0][1][0] + 3.,)),)
    r = Runner()
    r.start(Program((AIMED, Block(duration=.1))))
    follow(r, never_there, steps=2000)
    assert r.state == 'completed' and len(asked) == CORRECTIONS
    asked.clear()
    r.start(Program((AIMED,)))
    angles = follow(r, never_there, steps=2000, stuck=lambda: bool(asked))   # stuck once asked again
    assert r.state == 'completed' and len(asked) == 1, 'the pose itself had settled'
    assert angles['shoulder'][0] == pytest.approx(40., abs=.01)


def test_a_pose_without_a_point_or_a_runner_without_an_aim_is_the_angles_alone():
    def aim(point, pose):
        raise AssertionError('not asked')
    plain = Block('pose', value=30., duration=2., angles=(('shoulder', (40.,)),))
    for program, given in ((Program((plain,)), aim), (Program((AIMED,)), None)):
        r = Runner()
        r.start(program)
        assert follow(r, given) == {'shoulder': (40.,)} and r.state == 'completed'


# -- in the simulator ------------------------------------------------------------------------

mujoco = pytest.importorskip('mujoco')
import numpy as np  # noqa: E402
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.control.tool_motion import AIMED as NEAR, ToolMotion  # noqa: E402
from little_world.fields import field_scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint  # noqa: E402


def test_an_arm_aims_a_pose_from_where_its_machine_stands_now():
    bp = mobile_manipulator_blueprint()
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', bp))) as world:
        world.start()
        motion = ToolMotion(backend, bp, MujocoKeyboardControl(backend, bp))
        here = motion.teach()
        assert np.allclose(motion.angles(here), motion.targets()), 'a pose read back is the same angles'
        tool, _ = motion.tool()
        assert motion.aim(tuple(tool), here) is None, 'the tool is already there'
        lower = tool - (0., 0., .02)
        better = motion.aim(tuple(lower), here)
        reached, _ = motion.tool(angles=motion.angles(better))
        assert np.linalg.norm(reached - lower) < NEAR / 2
        assert motion.aim((5., 0., .3), here) is None, 'out of reach: the pose stands'


def test_a_loaded_cart_lifts_the_cube_clear_when_its_poses_are_aimed():
    """0.5 kg behind the arm: the cart rides on its rear caster, so the jaws met the cube
    28 mm from where they were aimed and the lift left it 12 mm short of the 5 cm line
    until the cart rocked back on its way to the bin (lifted at 23.7 s). Aimed, the jaws
    meet it within 4 mm and the lift clears the line: lifted at 18.2 s, 16.7 as designed."""
    from little_world.fields.variation import Variation, payload_site
    from little_world.inventory.sweep import run, solve
    bp = mobile_manipulator_blueprint()
    loaded = run('fetch', bp, Variation(payload=.5), solve('fetch', bp), payload_site(bp))
    goals = {r.id: r for r in loaded.results}
    assert loaded.program == 'completed' and all(r.status in ('met', 'kept') for r in goals.values())
    assert goals['lifted'].time < 19.
