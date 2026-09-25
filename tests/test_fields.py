"""Contracts for test fields and their goals (ADR 0013).

The defect: every test ran in one room whose pickup stand sat 0.46 m in front of the
machine, with nothing to time, climb, clear, push or place - a test could show that a
machine moved, not how well it did something.
"""
from dataclasses import replace
from math import cos, pi, sin
import os
import pytest

from little_world.components import Transform
from little_world.core.state import BodyState, State
from little_world.fields import FIELDS, field_scene
from little_world.fields.goals import GoalTracker, Line, Undisturbed, Upright, Zone, tilt


def body(x, y, z=.05, q=(1., 0., 0., 0.), v=(0., 0., 0.)):
    return BodyState(Transform((x, y, z), q), v, (0., 0., 0.))


def state(t, **bodies):
    return State(t, {name.replace('__', '/'): b for name, b in bodies.items()})


# -- goals: geometry on plain states -----------------------------------------------------

def test_a_line_is_crossed_forward_within_its_extent():
    line = Line('finish', 'Finish', (5., -.5), (5., .5))
    assert line.past((5.1, 0.)) and not line.past((4.9, 0.))
    assert not line.past((5.1, .8)), "beside the gate is not through it"


def test_gates_count_only_in_order_and_splits_are_timed():
    goals = (Line('a', 'Gate A', (1., -.5), (1., .5)),
             Line('b', 'Gate B', (2., -.5), (2., .5), after='a', since='a'))
    tracker = GoalTracker(goals, 'machine/base')
    tracker.update(state(0., machine__base=body(2.5, 1.)))       # past B's line, beside A
    tracker.update(state(1., machine__base=body(1.5, 0.)))       # through A
    tracker.update(state(3., machine__base=body(2.5, 0.)))       # through B
    results = {r.id: r for r in tracker.results(finished=True)}
    assert results['a'].status == 'met' and results['a'].time == 1.
    assert results['b'].status == 'met' and results['b'].time == 3.
    assert results['b'].detail.startswith('2.0 s after gate a')


def test_whole_means_every_body_is_over():
    curb = Line('c', 'Cleared curb', (1., -.5), (1., .5), whole=True)
    tracker = GoalTracker((curb,), 'machine/base')
    tracker.update(state(0., machine__base=body(1.2, 0.), machine__caster=body(.9, 0.)))
    assert tracker.results()[0].status == 'open', "the rear caster is still behind the curb"
    tracker.update(state(1., machine__base=body(1.4, 0.), machine__caster=body(1.1, 0.)))
    assert tracker.results()[0].status == 'met'


def test_an_object_delivered_to_a_zone_must_come_to_rest():
    zone = Zone('placed', 'Placed', (0., 0., 0.), (1., 1., 1.), target='objects/cube', rest=True)
    tracker = GoalTracker((zone,), 'machine/base')
    tracker.update(state(0., machine__base=body(0., 0.), objects__cube=body(.5, .5, v=(.3, 0., 0.))))
    assert tracker.results()[0].status == 'open', "still moving"
    tracker.update(state(1., machine__base=body(0., 0.), objects__cube=body(.5, .5)))
    assert tracker.results()[0].status == 'met'


def test_upright_and_undisturbed_are_kept_until_broken():
    goals = (Upright('up', 'Upright', 45.), Undisturbed('cones', 'Cones', ('objects/c0', 'objects/c1')))
    tracker = GoalTracker(goals, 'machine/base')
    lying = (cos(pi / 4), sin(pi / 4), 0., 0.)                    # 90 degrees about X
    assert tilt(lying) == pytest.approx(90.)
    tracker.update(state(0., machine__base=body(0., 0.), objects__c0=body(1., 0.), objects__c1=body(2., 0.)))
    tracker.update(state(1., machine__base=body(0., 0.), objects__c0=body(1.2, 0.), objects__c1=body(2., 0., q=lying)))
    tracker.update(state(2., machine__base=body(0., 0., q=lying), objects__c0=body(1., 0.), objects__c1=body(2., 0.)))
    up, cones = tracker.results(finished=True)
    assert up.status == 'failed' and up.time == 2.
    assert cones.status == 'failed' and cones.detail == '2 of 2 moved', "moved back is still disturbed"


def test_unmet_goals_are_open_while_running_and_missed_after():
    tracker = GoalTracker((Line('f', 'Finish', (5., -1.), (5., 1.)),), 'machine/base')
    tracker.update(state(0., machine__base=body(0., 0.)))
    assert tracker.results()[0].status == 'open'
    assert tracker.results(finished=True)[0].status == 'missed'


# -- fields: data -------------------------------------------------------------------------

def test_every_field_is_labelled_and_its_goals_name_real_bodies():
    from little_world import Entity
    from little_world.core.component import Body
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    assert 'workshop' in FIELDS and len(FIELDS) >= 7
    for field in FIELDS.values():
        assert field.title and len(field.summary) > 20
        scene = field.scene(Entity('machine', mobile_platform_blueprint()))
        names = {e.id + '/' + c.id for e in scene.entities for c in e.blueprint.components if isinstance(c, Body)}
        for goal in field.goals:
            for target in (getattr(goal, 'target', None), *getattr(goal, 'bodies', ())):
                assert target is None or target in names, (field.id, target)
        assert len({g.id for g in field.goals}) == len(field.goals)
    with pytest.raises(ValueError):
        field_scene('moon', Entity('machine', mobile_platform_blueprint()))


def test_fields_keep_clear_of_the_machine_at_the_start():
    """Every field is authored around the machine's start: nothing may overlap it."""
    from little_world import Entity
    from little_world.construction.docking import world_bounds
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    from little_world.assets.catalog import BY_ID
    machines = (mobile_platform_blueprint(), BY_ID['ready_rover_6'].blueprint())
    for field in FIELDS.values():
        for bp in machines:
            (mx0, my0, _), (mx1, my1, _) = world_bounds(bp)
            for entity in field.scene(Entity('machine', bp)).entities:
                if entity.id == 'machine':
                    continue
                for part in entity.blueprint.components:
                    if 'floor' in part.id:
                        continue
                    (x0, y0, z0), (x1, y1, _) = world_bounds(entity.blueprint, {part.id})
                    overlap = x0 < mx1 and mx0 < x1 and y0 < my1 and my0 < y1 and z0 < .5
                    assert not overlap, (field.id, part.id)


mujoco = pytest.importorskip('mujoco')
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_drive import MujocoDrive  # noqa: E402
from little_world.core.component import Body  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402


def run(field_id, bp, seconds, targets=(5., 5.), field=None):
    field = field or FIELDS[field_id]
    root = 'machine/' + next(b.id for b in bp.components if isinstance(b, Body) and b.parent is None)
    backend = MujocoBackend()
    with World(backend, field.scene(Entity('machine', bp))) as world:
        now = world.start()
        drive = MujocoDrive(backend, bp)
        tracker = GoalTracker(field.goals, root)
        tracker.update(now)
        for k in range(int(seconds / world.timestep)):
            now = world.step(drive.step_commands(targets, world.timestep))
            if k % 10 == 0:
                tracker.update(now)
        return {r.id: r for r in tracker.results(finished=True)}


def test_every_field_compiles_with_a_sky_and_the_machine_settles_where_it_would_at_home():
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    heights = {}
    for field in FIELDS.values():
        backend = MujocoBackend()
        with World(backend, field.scene(Entity('machine', mobile_platform_blueprint()))) as world:
            world.start()
            for _ in range(250):
                world.step({})
            heights[field.id] = float(backend.data.body('machine/root').xpos[2])
            sky = [i for i in range(backend.model.ntex) if backend.model.tex_type[i] == mujoco.mjtTexture.mjTEXTURE_SKYBOX]
            assert bool(sky) == (field.backdrop == 'sky'), field.id
    assert max(heights.values()) - min(heights.values()) < .002, heights


def test_the_sprint_is_timed_by_the_drive_assist_speed():
    """5 m at the drive assist's 0.425 m/s is 11.8 s; the platform's motors are not what limits it."""
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    results = run('sprint', mobile_platform_blueprint(), 15.)
    assert results['finish'].status == 'met' and results['upright'].status == 'kept'
    split = results['finish'].time - results['start'].time
    assert abs(split - 5 / .425) / (5 / .425) < .06, split


def test_small_casters_stop_at_a_curb_taller_than_themselves():
    """The platform's 20 mm swivel casters roll over 10 and 20 mm curbs, not 35 mm."""
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    results = run('curbs', mobile_platform_blueprint(), 13.)
    assert results['curb_10'].status == 'met' and results['curb_20'].status == 'met'
    assert results['curb_35'].status == 'missed'


def test_the_heavy_example_robot_cannot_climb_eight_degrees_and_a_lighter_one_can():
    """20.5 kg on 1 Nm per 85 mm wheel: m g sin(8 deg) = 28 N against 23.5 N of drive.
    The same robot with a plastic chassis weighs 9.1 kg and needs 12.4 N."""
    import little_world.fields as fields
    from little_world.materials import PLASTIC
    from little_world.robots.two_wheel import two_wheel_blueprint
    lanes = ((8., 0.),)   # the 8 degree ramp straight ahead
    eight = fields.Field('eight', 'Eight degrees', 'One plywood ramp of 8 degrees, straight ahead.',
                         lambda: fields.ramps_entities(lanes), goals=fields.ramps_goals(lanes))
    heavy = two_wheel_blueprint()
    assert 20.5 * 9.81 * sin(8 * pi / 180) > 2 * 1.0 / .085 > 9.1 * 9.81 * sin(8 * pi / 180)
    assert run('eight', heavy, 10., field=eight)['climb_8'].status == 'missed'
    light = replace(heavy, components=tuple(replace(c, material='plastic') if getattr(c, 'id', '') == 'chassis'
                                            else c for c in heavy.components),
                    materials=(*heavy.materials, PLASTIC))
    assert run('eight', light, 10., field=eight)['climb_8'].status == 'met'


def test_a_crate_needs_more_push_than_friction():
    """4 kg of wood on concrete takes 0.40 x 39 N = 15.7 N to slide; the two-wheel robot has 23.5 N."""
    from little_world.robots.two_wheel import two_wheel_blueprint
    results = run('push', two_wheel_blueprint(), 16.)
    assert results['delivered'].status == 'met'


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_choose_a_field_drive_it_and_read_the_goals(monkeypatch, tmp_path):
    import time
    import glfw
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'field.json', mobile_platform_blueprint())
    draw = app.draw
    step = {'n': 0, 't': 0.}
    design = app.editor.blueprint

    def exercise():
        draw()
        n, now = step['n'], time.monotonic()
        if n == 0:
            button = next(b for b in app.buttons if b.label.startswith('Field: '))
            assert button.label == 'Field: Workshop room'
            app.events.append(button.action)
        elif n == 1:
            assert app.dialog is not None and 'Sprint lane' in app.dialog['query']
            app.dialog = None
            app.set_field('sprint')
            assert app.model.body('field/floor') is not None and app.editor.blueprint == design
        elif n == 2:
            app.events.append(next(b for b in app.buttons if b.label == 'SIMULATE  >').action)
        elif n == 3:
            with pytest.raises(ValueError):
                app.set_field('ramps')
            app.key(app.window, glfw.KEY_W, 0, glfw.PRESS, 0)
            step['t'] = now
        elif n == 4:
            # On simulated progress, not the wall clock: the start line is 0.6 m out.
            met = {r.id: r.status for r in app.goal_tracker.results()}['start'] == 'met'
            if not met and now - step['t'] < 30.:
                return
            assert met
            app.key(app.window, glfw.KEY_W, 0, glfw.RELEASE, 0)
            app.events.append(next(b for b in app.buttons if b.label == 'STOP / RETURN TO BUILD').action)
        elif n == 5:
            record = app.run_report
            assert record.field == 'sprint' and {g.id for g in record.goals} == {'start', 'finish', 'upright'}
            assert app.last_goals and app.last_run_line().startswith('Last run in Sprint lane')
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=40)
    assert step['n'] == 6
