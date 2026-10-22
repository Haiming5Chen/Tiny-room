"""Contracts for the contact census (FR-030).

The question: ADR 0027 turned MuJoCo's multiple-contact search off everywhere, so a pair of
shapes that MuJoCo collides with its general collider gets a single contact point - a flat
face could be held, or stand, on one point. The census counts, at an instant, the points of
each pair of parts in contact as the model is set and again with multiccd on; a sweep run's
probe takes it at the moments a field's results are decided.
"""
from math import sqrt

from little_world.fields.goals import Result
from little_world.fields.variation import Variation
from little_world.inventory import census
from little_world.inventory.sweep import Run

QX = (sqrt(.5), sqrt(.5), 0., 0.)      # a quarter turn about x: a cylinder lying on its side


def test_a_box_stands_on_its_face_but_a_lying_cylinder_on_one_point_unless_multiccd():
    from little_world.core.blueprint import Blueprint
    from little_world.core.component import Body, Geometry, Transform
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.materials import METAL, WOOD
    from little_world.physics.mujoco_backend import MujocoBackend
    parts = Blueprint((Body('floor', Geometry('box', (1., 1., .1)), 'metal', Transform((0., 0., -.05))),
                       Body('block', Geometry('box', (.1, .1, .05)), 'wood', Transform((-.2, 0., .025)), dynamic=True),
                       Body('roller', Geometry('cylinder', (.03, .1)), 'wood', Transform((.2, 0., .03), QX), dynamic=True)),
                      (METAL, WOOD))
    backend = MujocoBackend()
    backend.compile(Scene((Entity('bench', parts),)), .002)
    for _ in range(100):
        backend.step({})
    found = backend.contact_census()
    block, roller = found[('bench/block', 'bench/floor')], found[('bench/floor', 'bench/roller')]
    assert block[0] == ('box-box',) and block[1] >= 3 and block[2] == block[1], "box on box: its own collider"
    assert roller[0] == ('box-cylinder',) and roller[1] == 1 and roller[2] > 1, "the general one: one point"
    assert backend.contact_census(('bench/block',)).keys() == {('bench/block', 'bench/floor')}
    again = backend.contact_census()
    assert again == found, "counted on copies: the run itself is untouched"


def test_a_census_row_is_a_part_at_a_moment_its_points_summed_over_its_bodies():
    assert census.part('machine/tread_wheel_1_tyre_13') == 'machine/tread_wheel_1_tyre'
    assert census.part('machine/two_finger_gripper_1_finger_left_pad') == 'machine/two_finger_gripper_1_finger_left_pad'
    assert census.part('objects/fetch_cube') == 'objects/fetch_cube'
    run = Run(Variation(), (Result('reached', 'Reached the table', 'met', 10.), Result('lifted', 'Lifted', 'met', 19.),
                            Result('delivered', 'In the bin', 'met', 37.)), felt=((19.,  True, True),))
    start = .6
    assert [m[0] for m in census.moments(run, start)] == [
        'standing at the start', 'standing at the table, reaching', 'held on the table', 'carried',
        'resting where it was set down']
    assert census.moments(run, start)[3][1:] == (19.6, 21.6), "goal times count from when the goals were first watched"
    tyre = lambda k, n, m: {(f'machine/tread_wheel_1_tyre_{k}', 'field/floor'): (('box-box',), n, m)}
    counts = [(.7, {**tyre(1, 2, 2), **tyre(2, 2, 2), ('field/floor', 'machine/swivel_caster_1_wheel'): (('box-cylinder',), 1, 5)}),
              (.8, {**tyre(1, 1, 1), **tyre(2, 2, 2), ('field/floor', 'machine/swivel_caster_1_wheel'): (('box-cylinder',), 1, 4)})]
    rows = census.table(run, counts, start)
    assert ('standing at the start', ('field/floor', 'machine/tread_wheel_1_tyre'), ('box-box',), (3, 4), (3, 4), 2, 2) in rows
    text = census.markdown(run, counts, start)
    assert '| standing at the start | floor - swivel_caster_1_wheel | box-cylinder | 1 | 4-5 | 2 of 2 |' in text
    assert 'Pairs whose count multiccd would change: floor - swivel_caster_1_wheel.' in text


def test_a_sweep_run_hands_its_probe_every_step():
    from little_world.inventory.sweep import design, run
    from little_world.physics.mujoco_backend import MujocoBackend
    seen = []
    result = run('push', design('mobile_platform'), probe=lambda state, backend: seen.append((state.time, backend)))
    assert not result.error and len(seen) >= round(12. / .002)
    assert all(isinstance(b, MujocoBackend) for _, b in seen[:3]) and seen[1][0] > seen[0][0]
