"""Contracts for the roller conveyor field (FR-007).

A belt needs MuJoCo 3.11's moving surfaces, past the pin (ADR 0027); powered rollers work on 3.10.
What a roller line carries must rest on three rollers at any time (Interroll's planning guide), so
the kit's cube rides on a pallet: 160 mm pallets on 50 mm rollers 55 mm apart, carried at the
rollers' surface speed to a stop plate, the next pallet queued behind the first.
"""
import pytest

from little_world.core.component import Geometry
from little_world.fields import FIELDS
from little_world.fields import conveyor as cv


def test_a_pallet_rests_on_three_rollers_and_a_capsule_is_a_shape():
    assert cv.PALLET[0] / cv.PITCH > 2.9 and cv.PITCH > 2 * cv.ROLLER[0], "three rollers under a pallet, gaps between them"
    assert cv.at_stop(1) == pytest.approx(cv.stop_x() - .08) and cv.at_stop(2) == pytest.approx(cv.at_stop(1) - .16)
    assert Geometry('capsule', (.025, .2)).size == (.025, .2)
    with pytest.raises(ValueError):
        Geometry('capsule', (.025,))
    from little_world.construction.docking import body_bounds
    from little_world.core.component import Body, Transform
    lo, hi = body_bounds(Body('r', Geometry('capsule', (.025, .2)), 'steel'), Transform((0., 0., 0.)))
    assert lo == pytest.approx((-.025, -.025, -.125)) and hi == pytest.approx((.025, .025, .125)), "its round ends counted"
    field = FIELDS['conveyor']
    assert [g.id for g in field.goals] == ['pallet_1', 'pallet_2', 'cube_1']


def test_a_box_laid_across_cylinders_sinks_into_them_and_across_capsules_does_not():
    """Why the rollers are capsules: MuJoCo 3.10 has no box-on-cylinder collider, and with multiccd off
    its general one gives one point - a 160 mm pallet laid across 50 mm cylinders sinks into them."""
    mj = pytest.importorskip('mujoco')

    def rest(shape):
        rollers = ''.join(f'<body pos="{.2 + .055 * i} 0 .095"><geom type="{shape}" size=".025 .1" euler="90 0 0"/></body>'
                          for i in range(5))
        m = mj.MjModel.from_xml_string(f'''<mujoco><option timestep=".002"><flag multiccd="disable"/></option>
            <worldbody><geom type="plane" size="1 1 .1"/>{rollers}
            <body pos=".31 0 .1280"><freejoint/><geom type="box" size=".08 .08 .0075" density="950"/></body></worldbody></mujoco>''')
        d = mj.MjData(m)
        for _ in range(1000):
            mj.mj_step(m, d)
        return float(d.xpos[-1][2]) - (.12 + .0075)
    assert rest('cylinder') < -.002, "across cylinders it sinks millimetres into them"
    assert abs(rest('capsule')) < .0005, "across capsules it rests on their tops"


def test_pallets_ride_at_the_rollers_speed_to_the_stop_and_queue():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields.goals import GoalTracker
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    field = FIELDS['conveyor']
    backend = MujocoBackend()
    with World(backend, field.scene(Entity('machine', mobile_manipulator_blueprint()))) as world:
        state = world.start()
        tracker = GoalTracker(field.goals, 'machine/root')
        carried, risen, on = [], 0., {}
        for k in range(round(4. / world.timestep)):
            state = world.step(field.commands(state))
            tracker.update(state)
            if .5 <= state.time <= 1.4:                  # both on their way, settled at speed
                carried += [state.bodies[f'objects/pallet_{p}'].linear_velocity[0] for p in (1, 2)]
            for p in (1, 2):
                risen = max(risen, state.bodies[f'objects/pallet_{p}'].pose.position[2] - cv.TOP - cv.PALLET[2] / 2)
            if round(state.time, 3) in (2.5, 4.):           # the cube on the held first pallet, along it
                on[round(state.time, 3)] = state.bodies['objects/cube_1'].pose.position[0] - state.bodies['objects/pallet_1'].pose.position[0]
        spins = cv.FIELD.spins(state)
        results = {r.id: r for r in tracker.results(finished=True)}
        rest = [state.bodies[f'objects/pallet_{p}'].pose.position for p in (1, 2)]
    under = {i for i in range(cv.ROLLERS) if any(abs(cv.roller_x(i) - cv.at_stop(p)) < cv.PALLET[0] / 2 for p in (1, 2))}
    free = [spins[i] * cv.ROLLER[0] for i in range(cv.ROLLERS) if i not in under]
    assert free and all(v == pytest.approx(cv.SPEED, rel=.01) for v in free), "the rollers nothing rests on turn at 0.1 m/s"
    assert all(abs(spins[i] * cv.ROLLER[0]) < .001 for i in under), "friction rollers: those under the held pallets stand still (ADR 0068)"
    assert abs(on[4.] - on[2.5]) < .0002, "so the cube on a held pallet stays put (OPEN LW-042)"
    assert carried and all(abs(v - cv.SPEED) < .03 * cv.SPEED for v in carried), (min(carried), max(carried))
    assert risen < .001, "they ride on the rollers, not over them, and do not climb the stop"
    for p, (x, y, _) in enumerate(rest, 1):
        assert abs(x - cv.at_stop(p)) < .001 and abs(y - cv.START[1]) < .005, (p, x, y)
    assert [results[g].status for g in ('pallet_1', 'pallet_2', 'cube_1')] == ['met'] * 3, results
    assert 1.4 < results['pallet_1'].time < 1.8 and results['pallet_1'].time < results['pallet_2'].time < 2.
