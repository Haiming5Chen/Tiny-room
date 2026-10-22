"""Contracts for moving the tool along its straight line (ADR 0045, FR-032).

The defect: a tool step set the arm's joint targets where the step ends, and each servo took
its joint there at its own pace, so the tool bowed off the line on the way - 7 to 13 mm on a
10 cm step of the kit arm, 10 mm on a 3.6 cm step of an imported arm (OPEN LW-031). And the
tool could only be stepped by clicking; holding a key moved single joints only.
"""
import numpy as np
import pytest

mujoco = pytest.importorskip('mujoco')
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.control.tool_motion import REACHED, SPEED, Glide, ToolMotion  # noqa: E402
from little_world.fields import field_scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.arm_lab import arm_lab_blueprint  # noqa: E402


def kit_arm():
    """The arm lab's kit arm in an empty field, drawn back from its stretched design pose."""
    bp = arm_lab_blueprint()
    backend = MujocoBackend()
    world = World(backend, field_scene('sprint', Entity('machine', bp)))
    world.start()
    control = MujocoKeyboardControl(backend, bp)
    motion = ToolMotion(backend, bp, control)
    motion.jog(forward=-.06)
    run(world, control, motion, 1.5)
    return world, control, motion


def run(world, control, motion, seconds, drive=None):
    """Step the world, the tool gliding (or driven along `drive`); the tool's path."""
    path = []
    for _ in range(round(seconds / world.timestep)):
        if drive is None:
            motion.advance(world.timestep)
        else:
            motion.drive(drive, world.timestep)
        world.step(control.step_commands(world.timestep))
        path.append(motion.tool()[0].copy())
    return np.array(path)


def off_line(path, start, goal):
    """How far the path strayed from the straight line from `start` to `goal`, metres."""
    line = (goal - start) / np.linalg.norm(goal - start)
    return max(np.linalg.norm((p - start) - ((p - start) @ line) * line) for p in path)


def test_a_glide_hands_out_the_line_from_rest_to_rest():
    line = [np.array((0., 0.)), np.array((1., 2.)), np.array((2., 4.))]
    glide = Glide(line, duration=1.)
    first = glide.at(.01)
    assert 0 < first[0] < .01, "it starts slowly"
    middle = glide.at(.49)
    assert middle == pytest.approx((1., 2.)) and not glide.done
    assert glide.at(.6) == pytest.approx((2., 4.)) and glide.done


@pytest.mark.parametrize('move', [dict(left=.1), dict(up=.1), dict(up=-.1)])
def test_the_kit_arm_tool_travels_its_straight_line_where_a_jump_bowed(move):
    bows = {}
    for kind in ('jog', 'glide'):
        world, control, motion = kit_arm()
        with world:
            start = motion.tool()[0].copy()
            f, l, u = motion.frame()
            goal = start + move.get('left', 0.) * l + move.get('up', 0.) * u
            assert getattr(motion, kind)(**move) <= REACHED
            path = run(world, control, motion, 3.)
            bows[kind] = off_line(path, start, goal)
            assert np.linalg.norm(path[-1] - goal) < .002
            if kind == 'glide':
                arrived = next(i for i, p in enumerate(path) if np.linalg.norm(p - goal) < .002) * world.timestep
                assert .1 / SPEED - .3 < arrived < .1 / SPEED + .3, "it travels at the tool speed"
    assert bows['jog'] > .005, "the joints' own paces bowed the tool (LW-031)"
    assert bows['glide'] < .001, f"{1000 * bows['glide']:.1f} mm off the line"


def test_a_line_out_of_reach_moves_nothing():
    world, control, motion = kit_arm()
    with world:
        before = motion.targets()
        short = motion.glide(forward=.3)
        assert short > REACHED and motion.gliding is None
        assert motion.targets() == pytest.approx(before)


def test_a_held_key_drives_the_tool_straight_and_stops_at_the_edge_of_its_reach():
    world, control, motion = kit_arm()
    with world:
        start = motion.tool()[0].copy()
        f, l, u = motion.frame()
        path = run(world, control, motion, 2., drive=(0, 0, 1))
        moved = path[-1] - start
        assert moved @ u == pytest.approx(2. * SPEED, abs=.01), "5 cm/s for 2 s"
        assert off_line(path, start, start + u) < .001
        # Forward until it can reach no further: it stops, holding the furthest it reached.
        shorts = []
        for _ in range(round(8. / world.timestep)):
            shorts.append(motion.drive((1, 0, 0), world.timestep))
            world.step(control.step_commands(world.timestep))
        assert shorts[-1] > REACHED, "at the edge of its reach the drive says so"
        held = motion.targets()
        motion.drive((0, 0, 0), 0.)
        run(world, control, motion, .5)
        assert motion.targets() == pytest.approx(held), "and it stays where it got to"


def test_an_imported_arm_glides_where_its_jump_bowed(tmp_path):
    from test_robot_library import arm, package, scene, STEP
    from little_world.physics.importer import import_robot
    asset, _ = import_robot(package(tmp_path, arm()))
    bows = []
    for kind in ('jog', 'glide'):
        bp, backend, control = scene(asset)
        control.set_position_target('servo_1', 30.)
        control.set_position_target('servo_2', 60.)
        for _ in range(round(1. / STEP)):
            backend.step(control.step_commands(STEP))
        motion = ToolMotion(backend, bp, control)
        start = motion.tool()[0].copy()
        f, l, u = motion.frame()
        goal = start + .03 * f - .02 * u
        assert getattr(motion, kind)(forward=.03, up=-.02, hold_angle=False) <= REACHED
        path = []
        for _ in range(round(1.5 / STEP)):
            motion.advance(STEP)
            backend.step(control.step_commands(STEP))
            path.append(motion.tool()[0].copy())
        bows.append(off_line(path, start, goal))
        assert np.linalg.norm(path[-1] - goal) < .002
    assert bows[0] > .008 and bows[1] < .001, [round(1000 * b, 1) for b in bows]


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_tool_mode_keys_in_the_window(monkeypatch, tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'arm.json', arm_lab_blueprint())
    draw = app.draw
    step = {'n': 0}

    def click(label):
        b = next(b for b in app.buttons if b.label == label)
        assert b.enabled, label
        app.events.append(b.action)

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.operate_robot()
        elif n == 1:
            click('Tool')
        elif n == 2:
            click('Back')   # drawn back from the stretched design pose first
        elif n == 3:
            if app.tool_motion.gliding is not None:
                return
            step['up'] = app.tool_readout()[2]
            step['t'] = app.state.time
            app.key(app.window, glfw.KEY_PAGE_UP, 0, glfw.PRESS, 0)
            assert app.tool_keys == {glfw.KEY_PAGE_UP}
        elif n == 4:
            if app.state.time - step['t'] < 1.:
                return
            app.key(app.window, glfw.KEY_PAGE_UP, 0, glfw.RELEASE, 0)
            assert not app.tool_keys
            rose = app.tool_readout()[2] - step['up']
            assert rose == pytest.approx(100 * SPEED * (app.state.time - step['t']), abs=1.), "cm, at 5 cm/s"
            step['held'] = app.tool_readout()
            step['t'] = app.state.time
        elif n == 5:
            if app.state.time - step['t'] < .3:
                return
            assert app.tool_readout() == pytest.approx(step['held'], abs=.05), "released, it stops"
            app.key(app.window, glfw.KEY_UP, 0, glfw.PRESS, 0)
            assert app.tool_keys == {glfw.KEY_UP} and not app.held_codes, \
                "in Tool mode an arrow moves the tool, not the base"
            app.key(app.window, glfw.KEY_UP, 0, glfw.RELEASE, 0)
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=60)
    assert step['n'] == 6
