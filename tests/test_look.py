"""A program looks for its object with the field's camera and aims where it was seen
(ADR 0032, FR-011).

The runner's rules first, with a camera the test stands in for: a look watches for a while,
a picture every tenth of a second, and ends once three in a row agree; the poses at that
stop aimed near the object are then aimed where it was seen, solved before they move; a new
stop forgets it. Then the Fetch table's own camera, through MuJoCo's rays, and a full run in
which the cube is moved 5 cm while the cart stands at the table - the run of ADR 0030 that
no set-up had passed.
"""
from types import SimpleNamespace

import pytest

from little_world.programming.program import NEAR, PICTURE, Block, Program, Runner

CUBE = 'objects/cube'
PLANNED = (1.84, 0., .14)
LOOK = Block('look', CUBE, value=1., duration=5., point=PLANNED)
ABOVE = Block('pose', value=40., duration=2., angles=(('arm', (10.,)),), point=(1.84, 0., .20))
AT = Block('pose', value=40., duration=2., angles=(('arm', (20.,)),), point=(1.84, 0., .14))
AWAY = Block('pose', value=40., duration=2., angles=(('arm', (30.,)),), point=(1.84, .40, .14))
STOP = Block('goto', value=.01, duration=60., point=(1.0, 0., 0.))


class Camera:
    """Sees the object at `where(time)`, or not at all where that is None."""

    def __init__(self, where):
        self.where, self.time, self.asked = where, 0., []

    def __call__(self, target, planned):
        self.asked.append((round(self.time, 2), target, planned))
        at = self.where(self.time)
        return None if at is None else SimpleNamespace(centre=at)


def run(program, camera, ticks=2000, base=(1.6, 0., 0.)):
    """Joints that arrive at once; `aim` returns a pose named after the point it was given."""
    runner, angles, aimed = Runner(), {'arm': (0.,)}, []

    def aim(point, pose):
        aimed.append(tuple(round(v, 3) for v in point))
        return (('arm', (100. + 1000 * point[1],)),)
    runner.start(program)
    for _ in range(ticks):
        out = runner.tick(.01, angles, base=base, aim=aim, see=camera)
        camera.time += .01
        if out['pose']:
            angles = dict(out['pose'])
        if runner.state != 'running':
            break
    return runner, aimed


def test_a_look_waits_until_three_pictures_agree_then_its_poses_aim_where_it_was_seen():
    camera = Camera(lambda t: (1.84, .05, .14))                       # 5 cm to the left of the plan
    runner, aimed = run(Program((LOOK, ABOVE, AT, AWAY)), camera)
    assert runner.state == 'completed'
    looks = [t for t, *_ in camera.asked]
    assert len(looks) == 12 and looks[10] - looks[0] == pytest.approx(10 * PICTURE, abs=.02)  # a second's watch,
    assert looks[11] > looks[10] + .1                     # then one more as the jaws reach down for it (ADR 0033)
    assert runner.seen == [(CUBE, PLANNED, (1.84, .05, .14))]
    # Both poses near the cube were solved for where it was seen before they moved; the
    # pose 40 cm away from it was not moved.
    assert aimed[0] == (1.84, .05, .20) and (1.84, .05, .14) in aimed
    assert (1.84, .45, .14) not in aimed and (1.84, .40, .14) in aimed
    assert NEAR < .40


def test_a_cube_moved_while_it_looks_is_seen_where_it_came_to_rest():
    camera = Camera(lambda t: (1.84, 0., .14) if t < .32 else (1.84, .05, .14))
    runner, _ = run(Program((LOOK, AT)), camera)
    assert runner.state == 'completed' and runner.seen[0][2] == (1.84, .05, .14)


def test_a_look_that_never_sees_it_still_fails_and_says_why():
    runner, _ = run(Program((LOOK, AT)), Camera(lambda t: None))
    assert runner.state == 'failed' and runner.message == 'Looked for cube: not found'
    pictures = []
    jitter = Camera(lambda t: pictures.append(t) or (1.84, .01 * (len(pictures) % 2), .14))   # still being moved
    runner, _ = run(Program((LOOK, AT)), jitter)
    assert runner.state == 'failed' and runner.message == 'Looked for cube: it would not keep still'
    runner = Runner()
    runner.start(Program((LOOK,)))
    runner.tick(.01, {})
    assert runner.state == 'failed' and runner.message == 'No camera to look with'


def test_a_new_stop_forgets_what_was_seen():
    camera = Camera(lambda t: (1.84, .05, .14))
    runner, aimed = run(Program((LOOK, STOP, AT)), camera, base=(1.0, 0., 0.))
    assert runner.state == 'completed' and runner.offset is None
    assert set(aimed) == {(1.84, 0., .14)}                # the plan's point, checked after it moved


def test_a_look_is_written_as_version_3_and_says_what_it_needs():
    program = Program((LOOK, AT))
    assert program.version == 3 and Program.from_json(program.to_json()) == program
    assert Program((AT,)).version == 2
    for bad in (dict(target=''), dict(point=()), dict(duration=1.)):
        with pytest.raises(ValueError):
            Block('look', **{**dict(target=CUBE, value=1., duration=5., point=PLANNED), **bad})


def test_reports_say_how_far_from_the_plan_the_camera_saw_it():
    from little_world.fields.goals import Result
    from little_world.fields.variation import Ranges, Variation
    from little_world.inventory.sweep import Disturbed, Run, disturbed_from_json, disturbed_markdown, to_json

    def runs(dy):
        met = (Result('delivered', 'Cube resting in the bin', 'met', 35.),)
        return tuple(Run(Variation(label), met, seen=((CUBE, PLANNED, (1.841, dy + .001 * i, .14), (1.84, dy, .14)),))
                     for i, label in enumerate(('as designed', 'repeat 1', 'repeat 2')))
    result = Disturbed('fetch', 'arm on a cart', 'program', 60., None, Ranges(), None,
                       (('none', '', runs(0.)), ('cube moved 5 cm sideways', 'a move', runs(.05))))
    page = disturbed_markdown(result)
    assert '| Camera saw it moved |' in page and '| 5.1 cm (5.0 to 5.2) |' in page
    assert 'within 2.2 mm of where the cube really was' in page
    assert disturbed_from_json(to_json(result)) == result


def test_the_fetch_tables_camera_sees_its_cube_within_5_mm():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS, FETCH_CUBE, TABLE
    from little_world.inventory.sweep import design, eye
    from little_world.physics.mujoco_backend import MujocoBackend
    field = FIELDS['fetch']
    backend = MujocoBackend()
    scene = field.scene(Entity('machine', design('mobile_manipulator')))
    with World(backend, scene) as world:
        world.start()
        # Where the camera is, and that it does not see its own head: the middle of its
        # picture is the cube's far face, 0.883 m along its axis.
        position, rotation = backend.camera_pose('field/table_camera')
        assert sum((a - b) ** 2 for a, b in zip(position, (2.294, 0., .889))) ** .5 < .002
        assert backend.cast('field/table_camera', [(0., 0., -1.)])[0] == pytest.approx(.883, abs=.002)
        planned = (FETCH_CUBE[0], FETCH_CUBE[1], TABLE[4] + .02)
        camera = eye(backend, field, scene)
        for shift in ((0., 0.), (0., .05), (.03, -.04)):
            if any(shift):
                backend.shift('objects/fetch_cube', shift)
            truth = backend.data.xpos[backend.model.body('objects/fetch_cube').id].copy()
            seen = camera('objects/fetch_cube', planned)
            assert sum((a - b) ** 2 for a, b in zip(seen.centre, truth)) ** .5 < .005, (shift, seen.centre, truth)
            assert abs(seen.yaw) < 5 and seen.up == 2


def test_the_cube_moved_5_cm_as_the_cart_stands_at_the_table_is_fetched():
    """ADR 0030's disturbance: none of 9 set-ups fetched the cube moved 5 cm (ADR 0031)."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, run as field_run
    moved = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways')
    result = field_run('fetch', design('mobile_manipulator'), disturbance=moved)
    assert all(r.status in ('met', 'kept') for r in result.results), (result.results, result.program)
    (_, planned, seen, actual), = result.seen
    assert abs(seen[1] - planned[1] - .05) < .005 and sum((a - b) ** 2 for a, b in zip(seen, actual)) ** .5 < .005


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_the_program_shows_what_the_table_camera_saw(monkeypatch, tmp_path):
    """The Fetch program's button writes the look in; once a look has a picture, the
    window shows it in the corner - the cube's pixels green - and the block says how far
    from the plan the cube was seen."""
    import glfw
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'look.json', mobile_manipulator_blueprint())
    draw = app.draw
    step = {'n': 0}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.set_field('fetch')
            app.show_program()
        elif n == 1:
            app.events.append(next(b for b in app.buttons if b.label == 'Fetch program').action)
        elif n == 2:
            kinds = [b.kind for b in app.program.blocks]
            assert app.program.version == 3 and kinds.index('look') == kinds.index('goto') + 1
            look = app.program.blocks[kinds.index('look')]
            app.eye = app.program_eye()
            app.backend.shift('objects/fetch_cube', (0., .05))
            app.runner.seen = [(look.target, look.point, app.eye(look.target, look.point).centre)]
        elif n == 3:
            assert app.look_rect is not None and app.eye.last.box is not None and len(app.eye.last.box) > 50
            assert abs(app.runner.seen[0][2][1] - .05) < .005
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=60)
    assert step['n'] == 4
