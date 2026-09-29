"""Contracts for driving to a point and the Fetch field (ADR 0018).

The defect: an arm on a wheeled base had no task that used both. Programs could drive
only by timed wheel speeds, so a program could not bring the base to a table, and no
field asked a machine to fetch anything: drive somewhere, pick something up, bring it
back and put it down.
"""
from math import degrees, radians
import pytest

from little_world.control.navigation import GoTo, wheel_targets
from little_world.programming.program import Block, Program, Runner


# -- driving to a point: plain arithmetic ---------------------------------------------------

def test_ahead_it_drives_off_the_bearing_it_turns_first_and_close_behind_it_backs_up():
    forward, turn, arrived = GoTo((2., 0.)).step((0., 0., 0.))
    assert forward > 0 and turn == 0 and not arrived
    forward, turn, _ = GoTo((0., 2.)).step((0., 0., 0.))
    assert forward == 0 and turn > 0, "90 degrees to the left: turn on the spot, left"
    forward, turn, _ = GoTo((-.3, 0.)).step((0., 0., 0.))
    assert forward < 0 and abs(turn) < 1e-9, "30 cm behind: back straight up, no turn round"
    forward, turn, _ = GoTo((-2., 0.)).step((0., 0., 0.))
    assert forward == 0 and turn != 0, "2 m behind: turn round and drive"


def test_it_slows_as_it_closes_but_never_to_a_stall():
    far, _, _ = GoTo((2., 0.)).step((0., 0., 0.))
    near, _, _ = GoTo((.02, 0.), tolerance=.01).step((0., 0., 0.))
    assert far > near > 0 and near >= .03


def test_once_there_it_turns_to_the_heading_and_does_not_chase_the_point_again():
    goto = GoTo((1., 0.), heading=radians(90.), tolerance=.01)
    forward, turn, arrived = goto.step((1., 0., 0.))
    assert forward == 0 and turn > 0 and not arrived
    # A turn on the spot drifts a little: within 4 tolerances it keeps turning.
    forward, turn, arrived = goto.step((1.015, .01, radians(45.)))
    assert forward == 0 and turn > 0 and not arrived
    assert goto.step((1., 0., radians(89.)))[2], "within 2 degrees: there"
    forward, turn, arrived = goto.step((1.2, 0., radians(90.)))
    assert not arrived and forward != 0 or turn != 0, "pushed 20 cm away, it goes back"


def test_wheel_speeds_from_a_forward_speed_and_a_turn_rate():
    left, right = wheel_targets(.2, 0., .05, .25)
    assert left == right == pytest.approx(4.)
    left, right = wheel_targets(0., 1., .05, .25)
    assert left == pytest.approx(-2.5) and right == pytest.approx(2.5), "turning left: right wheel forward"


def test_a_goto_block_is_version_2_data_and_the_runner_drives_until_it_arrives():
    block = Block('goto', value=.02, duration=10., point=(1., .5, 90.))
    p = Program((block,))
    assert p.version == 2 and Program.from_json(p.to_json()) == p
    for bad in (dict(point=(1.,)), dict(point=(1., 2., 3., 4.)), dict(point=(1., float('nan'))), dict(point=(1., 0.), value=2.)):
        with pytest.raises(ValueError):
            Block('goto', **bad)
    r = Runner()
    r.start(Program((Block('goto', duration=5., point=(1., 0.)),)))
    assert r.tick(.01)['base'] is None and r.state == 'failed', "no base to drive"
    r.start(Program((Block('goto', duration=5., point=(1., 0.)),)))
    out = r.tick(.01, base=(0., 0., 0.))
    assert out['base'][0] > 0 and r.state == 'running'
    r.tick(.01, base=(.995, 0., 0.))
    assert r.state == 'completed'


# -- in the simulator ---------------------------------------------------------------------

mujoco = pytest.importorskip('mujoco')
import numpy as np  # noqa: E402
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_drive import MujocoDrive  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.control.navigation import BasePose  # noqa: E402
from little_world.fields import BIN, BIN_SIZE, FIELDS, field_scene  # noqa: E402
from little_world.fields.goals import GoalTracker  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.programming.execution import apply, base_targets, joint_angles, needs_grasp  # noqa: E402
from little_world.programming.observations import Observations  # noqa: E402
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint  # noqa: E402
from little_world.robots.mobile_platform import mobile_platform_blueprint  # noqa: E402


def machine_in(field, bp):
    backend = MujocoBackend()
    world = World(backend, field_scene(field, Entity('machine', bp)))
    state = world.start()
    control = MujocoKeyboardControl(backend, bp)
    drive = MujocoDrive(backend, bp)
    return world, backend, control, drive, BasePose(backend, drive, bp), state


def run(world, backend, control, drive, base, program, goals, seconds, root='machine/root'):
    obs = Observations(backend.model, backend.data)
    tracker = GoalTracker(goals, root)
    runner = Runner()
    runner.start(program)
    for _ in range(round(seconds / world.timestep)):
        contacts, distances = obs.program_inputs(program)
        held = obs.grasped() if needs_grasp(program) else frozenset()
        out = runner.tick(world.timestep, joint_angles(control), contacts, distances, held, base.pose())
        control.held = apply(out, control)
        commands = dict(drive.step_commands(base_targets(out, base) if out['base'] else out['drive'], world.timestep, angular=True))
        commands.update(control.step_commands(world.timestep))
        tracker.update(world.step(commands))
        if runner.state != 'running':
            break
    control.held = set()
    for _ in range(round(1.5 / world.timestep)):
        commands = dict(drive.step_commands((0., 0.), world.timestep, angular=True))
        commands.update(control.step_commands(world.timestep))
        tracker.update(world.step(commands))
    return runner, {r.id: r for r in tracker.results(finished=True)}


def test_the_base_pose_is_the_drive_axle_midpoint_and_its_heading():
    world, backend, control, drive, base, _ = machine_in('sprint', mobile_platform_blueprint())
    with world:
        x, y, yaw = base.pose()
        assert abs(x) < .01 and abs(y) < .005 and abs(yaw) < 1e-3
        assert base.radius == pytest.approx(.05) and base.track == pytest.approx(.245, abs=.005)


def test_a_program_drives_the_platform_to_a_point_and_a_heading():
    world, backend, control, drive, base, _ = machine_in('sprint', mobile_platform_blueprint())
    with world:
        program = Program((Block('goto', value=.01, duration=30., point=(1., .5, 90.)),))
        runner, _ = run(world, backend, control, drive, base, program, (), 30.)
        assert runner.state == 'completed', runner.message
        x, y, yaw = base.pose()
        assert np.hypot(x - 1., y - .5) < .015 and abs(degrees(yaw) - 90.) < 2.5


def test_the_mobile_manipulator_fetches_the_cube_by_itself():
    """Drive 1.6 m to the table, pick the cube, back away, drive to the bin, let go:
    every stop and arm waypoint solved for this machine, and judged by the field."""
    from little_world.control.tool_motion import ToolMotion, fetch
    world, backend, control, drive, base, _ = machine_in('fetch', mobile_manipulator_blueprint())
    with world:
        motion = ToolMotion(backend, mobile_manipulator_blueprint(), control)
        # Planned from the machine as it stands: settled onto its front caster, 2.8 degrees
        # nose-down (ADR 0015), not level as designed.
        for _ in range(300):
            commands = dict(drive.step_commands((0., 0.), world.timestep, angular=True))
            commands.update(control.step_commands(world.timestep))
            world.step(commands)
        program = fetch(motion, base, 'control_jaws', 'objects/fetch_cube', (BIN[0], BIN[1], .006),
                        reach_in=BIN_SIZE / 2 - .045)
        assert [b.kind for b in program.blocks].count('goto') == 3
        runner, goals = run(world, backend, control, drive, base, program, FIELDS['fetch'].goals, 60.)
        assert runner.state == 'completed', runner.message
        assert {g: r.status for g, r in goals.items()} == {
            'reached': 'met', 'lifted': 'met', 'delivered': 'met', 'upright': 'kept'}
        assert goals['reached'].time < goals['lifted'].time < goals['delivered'].time < 45.


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_the_fetch_program_from_its_button_drives_off_towards_the_table(monkeypatch, tmp_path):
    import time
    import glfw
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'fetch.json', mobile_manipulator_blueprint())
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
            app.set_field('fetch')
            app.show_program()
        elif n == 1:
            click('Fetch program')
        elif n == 2:
            kinds = [b.kind for b in app.program.blocks]
            assert kinds.count('goto') == 3 and 'grasp' in kinds and kinds.count('pose') >= 5
            click('Run')
            step['t'] = now
        elif n == 3:
            x, y, _ = app.base_pose.pose()
            if x < .3:
                assert now - step['t'] < 40, 'the base should be driving to the table'
                return
            assert app.runner.state == 'running' and app.program.blocks[app.runner.index].kind == 'goto'
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=60)
    assert step['n'] == 4
