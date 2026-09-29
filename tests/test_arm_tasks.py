"""Contracts for arm tasks: taught poses, grasp checks, tool moves (ADR 0016).

The defect: an arm could only be moved one joint at a time, by key or by a program
block per joint, so a pick-and-place meant hand-tuning shoulder, elbow and wrist in
turn while the tool swept an arc, and a program had no way to notice that the
gripper had closed on nothing. The Pick and place field's goals had no program
that met them.
"""
import pytest

from little_world.programming.program import Block, Program, Runner, smoothstep


# -- poses and grasp checks in a program: plain data ------------------------------------

POSE = Block('pose', value=30., duration=2., angles=(('shoulder', (40.,)), ('elbow', (-20.,)), ('grip', (5., 5.))))


def test_a_pose_is_data_that_round_trips_and_marks_its_program_version_2():
    p = Program((Block('action', 'grip', 1, .5), POSE, Block('grasp', duration=1.)))
    assert p.version == 2, "a version-1 reader must refuse it rather than misread it"
    assert Program.from_json(p.to_json()) == p
    old = Program((Block('action', 'grip', 1, .5),))
    assert old.version == 1 and '"angles"' not in old.to_json(), "version-1 files are unchanged"


@pytest.mark.parametrize('bad', [
    dict(angles=()),                                    # a pose of nothing
    dict(angles=(('a', (1.,)), ('a', (2.,)))),          # one action twice
    dict(angles=(('a', (float('nan'),)),)),
    dict(angles=(('a', (1.,)),), value=0.),             # no speed
])
def test_malformed_poses_are_refused(bad):
    with pytest.raises(ValueError):
        Block('pose', **{'value': 30., **bad})
    with pytest.raises(ValueError):
        Block('wait', angles=(('a', (1.,)),))


def test_pose_joints_move_together_and_arrive_together():
    r = Runner()
    r.start(Program((POSE,)))
    start = {'shoulder': (0.,), 'elbow': (0.,), 'grip': (5., 5.)}
    halfway = None
    for i in range(1, 400):
        out = r.tick(.01, start)
        if i == 67:
            halfway = out['pose']
    # The slowest joint (the shoulder, 40 deg at 30 deg/s) takes 1.33 s; at the halfway
    # time every joint is halfway along, so the tool moves along one smooth path.
    assert halfway['shoulder'][0] == pytest.approx(40 * smoothstep(.67 / (40 / 30)), abs=1e-6)
    assert halfway['elbow'][0] / -20 == pytest.approx(halfway['shoulder'][0] / 40, abs=1e-9)
    assert r.state == 'failed' and 'settle' in r.message, "the joints never got there"
    r.start(Program((POSE,)))
    r.tick(.01, start)
    for _ in range(140):
        r.tick(.01, {'shoulder': (40.,), 'elbow': (-19.,), 'grip': (5., 4.)})
    assert r.state == 'completed'


def test_a_grasp_check_fails_the_program_when_the_gripper_holds_nothing():
    r = Runner()
    r.start(Program((Block('grasp', duration=.5), Block(duration=.1))))
    for _ in range(60):
        r.tick(.01, held=frozenset())
    assert r.state == 'failed' and 'Nothing held' in r.message
    r.start(Program((Block('grasp', 'objects/grasp_cube', duration=.5),)))
    r.tick(.01, held=frozenset({'objects/other'}))
    assert r.state == 'running', "holding something else is not this grasp"
    r.tick(.01, held=frozenset({'objects/grasp_cube'}))
    assert r.state == 'completed'


def test_pose_validation_against_the_design():
    from little_world.robots.arm_lab import arm_lab_blueprint
    bp = arm_lab_blueprint()
    ok = Program((Block('pose', value=30., angles=(('control_upper_arm', (20.,)),)),))
    ok.validate(bp)
    with pytest.raises(ValueError, match='limits'):
        Program((Block('pose', value=30., angles=(('control_upper_arm', (170.,)),)),)).validate(bp)
    with pytest.raises(ValueError, match='angles for'):
        Program((Block('pose', value=30., angles=(('control_upper_arm', (1., 2.)),)),)).validate(bp)
    with pytest.raises(ValueError, match='Missing'):
        Program((Block('pose', value=30., angles=(('nothing', (1.,)),)),)).validate(bp)


# -- the arm in the simulator: tool moves, teaching, the whole task ------------------------

mujoco = pytest.importorskip('mujoco')
import numpy as np  # noqa: E402
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.control.tool_motion import ToolMotion, pick_and_place  # noqa: E402
from little_world.fields import FIELDS, TRAY, field_scene  # noqa: E402
from little_world.fields.goals import GoalTracker  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.programming.execution import apply, joint_angles, needs_grasp  # noqa: E402
from little_world.programming.observations import Observations  # noqa: E402
from little_world.robots.arm_lab import arm_lab_blueprint  # noqa: E402


def arm_in(field='pick_place', bp=None):
    bp = bp or arm_lab_blueprint()
    backend = MujocoBackend()
    world = World(backend, field_scene(field, Entity('machine', bp)))
    state = world.start()
    control = MujocoKeyboardControl(backend, bp)
    return world, backend, control, ToolMotion(backend, bp, control), state


def settle(world, control, seconds):
    state = None
    for _ in range(round(seconds / world.timestep)):
        state = world.step(control.step_commands(world.timestep))
    return state


def test_the_tool_is_found_and_so_are_the_joints_that_move_it():
    world, backend, control, motion, _ = arm_in()
    with world:
        assert [a for a, *_ in motion.joints] == ['control_yaw', 'control_upper_arm', 'control_forearm', 'control_wrist']
        point, pointing = motion.tool()
        pads = [backend.data.body(f'machine/two_finger_gripper_1_finger_{s}_pad').xpos for s in ('left', 'right')]
        assert point == pytest.approx((pads[0] + pads[1]) / 2, abs=1e-9), "midway between the pads"
        assert pointing == pytest.approx((1., 0., 0.), abs=1e-9)


@pytest.mark.parametrize('move', [dict(forward=-.05), dict(left=.05), dict(up=-.05), dict(forward=-.03, left=-.04, up=.02)])
def test_a_tool_move_goes_in_a_straight_step_and_keeps_the_tool_angle(move):
    world, backend, control, motion, _ = arm_in('sprint')   # nothing in the way of the arm
    with world:
        # The arm lab's design pose is fully stretched: from there nothing sideways or up
        # keeps the reach (5 cm to the left is 2.8 mm further out). Start drawn back.
        assert motion.jog(forward=-.06) <= .002
        before, pointing = motion.tool(angles=motion.targets())
        assert motion.jog(**move) <= .002
        after, turned = motion.tool(angles=motion.targets())
        f, l, u = motion.frame()
        expected = before + move.get('forward', 0.) * f + move.get('left', 0.) * l + move.get('up', 0.) * u
        assert after == pytest.approx(expected, abs=1e-4)
        assert turned[2] == pytest.approx(pointing[2], abs=1e-3), "the tool stays level"
        settle(world, control, 1.5)
        assert motion.tool()[0] == pytest.approx(expected, abs=.004), "and the servos take it there"


def test_out_of_reach_leaves_the_arm_where_it_was():
    world, backend, control, motion, _ = arm_in()
    with world:
        before = motion.targets().copy()
        short = motion.jog(forward=.20)
        assert short > .05 and motion.targets() == pytest.approx(before)


def test_a_taught_pose_is_the_arms_targets():
    world, backend, control, motion, _ = arm_in()
    with world:
        motion.jog(up=-.04)
        taught = dict(motion.teach())
        for (action, name, *_), value in zip(motion.joints, motion.targets()):
            assert taught[action] == pytest.approx((np.degrees(value),), abs=1e-3)


def run_program(world, backend, control, program, seconds=20.):
    obs = Observations(backend.model, backend.data)
    tracker = GoalTracker(FIELDS['pick_place'].goals, 'machine/pedestal')
    from little_world.programming.program import Runner
    runner = Runner()
    runner.start(program)
    for _ in range(round(seconds / world.timestep)):
        contacts, distances = obs.program_inputs(program)
        held = obs.grasped() if needs_grasp(program) else frozenset()
        control.held = apply(runner.tick(world.timestep, joint_angles(control), contacts, distances, held), control)
        tracker.update(world.step(control.step_commands(world.timestep)))
        if runner.state != 'running':
            break
    control.held = set()
    for _ in range(round(1.5 / world.timestep)):
        tracker.update(world.step(control.step_commands(world.timestep)))
    return runner, {r.id: r for r in tracker.results(finished=True)}


def test_the_pick_and_place_template_meets_the_fields_goals():
    """Solved for this arm from where the cube and the tray are, then run by the physics:
    the jaws close by contact, the cube is carried by friction and let go above the tray."""
    world, backend, control, motion, _ = arm_in()
    with world:
        program = pick_and_place(motion, 'control_jaws', (TRAY[0], TRAY[1], .006))
        assert program.version == 2 and any(b.kind == 'grasp' for b in program.blocks)
        runner, goals = run_program(world, backend, control, program)
        assert runner.state == 'completed', runner.message
        assert goals['lifted'].status == 'met' and goals['placed'].status == 'met'
        cube = backend.data.body('objects/grasp_cube').xpos
        assert np.linalg.norm(cube[:2] - np.array(TRAY)) < .04


def test_a_missed_grasp_stops_the_program_instead_of_carrying_air():
    world, backend, control, motion, _ = arm_in()
    with world:
        program = pick_and_place(motion, 'control_jaws', (TRAY[0], TRAY[1], .006))
        cube = backend.model.body('objects/grasp_cube')
        joint = backend.model.jnt_qposadr[cube.jntadr[0]]
        backend.data.qpos[joint:joint + 3] = (.46, -.3, .02)    # someone took the cube
        runner, goals = run_program(world, backend, control, program)
        assert runner.state == 'failed' and 'Nothing held' in runner.message
        assert goals['placed'].status == 'missed'


# -- the window: move the tool, teach, run the template in the field -----------------------

@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_tool_mode_teach_and_the_pick_and_place_template_in_the_window(monkeypatch, tmp_path):
    import time
    import glfw
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'pick.json', arm_lab_blueprint())
    draw = app.draw
    step = {'n': 0, 't': 0.}

    def click(label):
        b = next(b for b in app.buttons if b.label == label)
        assert b.enabled, label
        app.events.append(b.action)

    def exercise():
        draw()
        n, now = step['n'], time.monotonic()
        if n == 0:
            app.set_field('pick_place')
            app.operate_robot()
        elif n == 1:
            click('Tool')
        elif n == 2:
            assert app.control_mode == 'Tool' and app.tool_motion is not None
            forward, left, up = app.tool_readout()
            step['before'] = forward
            click('Back')
        elif n == 3:
            assert not app.building and app.tool_result == 'Target moved'
            assert app.tool_readout()[0] == pytest.approx(step['before'] - 2., abs=.05)
            click('Teach pose  ->  program step')
        elif n == 4:
            assert [b.kind for b in app.program.blocks] == ['pose']
            click('Stop simulation')
        elif n == 5:
            assert app.building
            app.show_program()
        elif n == 6:
            click('Pick and place')
        elif n == 7:
            kinds = [b.kind for b in app.program.blocks]
            assert 'grasp' in kinds and kinds.count('pose') >= 4
            click('Run')
            step['t'] = now
        elif n == 8:
            if app.runner.state == 'running':
                assert now - step['t'] < 60, 'the program should finish'
                return
            assert app.runner.state == 'completed', app.runner.message
            step['t'] = now
        elif n == 9:
            if now - step['t'] < 1.5:
                return
            results = {r.id: r.status for r in app.goal_tracker.results()}
            assert results == {'lifted': 'met', 'placed': 'met'}, results
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=90)
    assert step['n'] == 10


@pytest.mark.parametrize('asset', ['franka_panda', 'ur5e'])
def test_registered_robots_move_their_tool_too(asset):
    """A Menagerie arm has no kit tool module: its tool point is given (the Panda's between
    its fingertips) or is its flange, and its joints are its own position servos."""
    from little_world.factory.scene import factory_scene, robot_blueprint
    bp = robot_blueprint(asset)
    backend = MujocoBackend()
    with World(backend, factory_scene(Entity('machine', bp))) as world:
        world.start()
        control = MujocoKeyboardControl(backend, bp)
        motion = ToolMotion(backend, bp, control)
        assert len(motion.joints) == (7 if asset == 'franka_panda' else 6)
        assert motion.jaws == (('servo_8',) if asset == 'franka_panda' else ())
        start = motion.tool(angles=motion.targets())[0]
        assert motion.jog(up=-.05) <= .002
        settle(world, control, 3.)
        assert motion.tool()[0] == pytest.approx(start - (0., 0., .05), abs=.012)
