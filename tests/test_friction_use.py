"""Contracts for how near a contact is to sliding: friction use (FR-036).

Results reported forces (ADR 0040), the squeeze (ADR 0042) and what the jaws feel (ADR 0048),
never how near a contact is to sliding. A contact's friction use is the friction it uses over
what its cone allows: 0 with no sideways load, 1 at the cone's edge, where it may slide. The
measure is MuJoCo's own cone, pyramidal in every scene here: the frictional forces, each over its
own coefficient, summed.
"""
from math import cos, radians, sin, tan

import pytest

pytest.importorskip('mujoco')


def incline(theta, seconds=.6):
    """A 5 cm block resting on a concrete slab tilted `theta` degrees about x, after `seconds`:
    (the block's friction use, its contacts' coefficient, its speed, m/s)."""
    from little_world import World
    from little_world.components import Transform, box
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.physics.mujoco_backend import MujocoBackend
    s = radians(theta)
    turn = (cos(s / 2), sin(s / 2), 0., 0.)
    up = (0., -sin(s), cos(s))
    centre = (0., 0., .3)
    at = tuple(c + .04 * u for c, u in zip(centre, up))       # the slab's 2 cm half thickness, the block's 2 cm
    entities = field_entities([fixed('ramp', (.6, .6, .04), 'slab', centre, turn)],
                              [box('block', (.05, .05, .04), 'cube', dynamic=True, transform=Transform(at, turn))])
    backend = MujocoBackend()
    with World(backend, Scene(entities)) as world:
        world.start()
        for _ in range(round(seconds / world.timestep)):
            state = world.step({})
        rows = backend.friction_use('objects/block')
        mu = {float(backend.data.contact[i].friction[0]) for i in range(backend.data.ncon)}
        speed = sum(v * v for v in state.bodies['objects/block'].linear_velocity) ** .5
    normal = sum(n for _, n, _ in rows)
    return sum(u for _, _, u in rows) / normal, mu, speed


def test_a_block_on_a_slope_uses_tan_theta_over_mu_of_its_friction_until_it_slides():
    """Concrete under wood, mu 0.4 (ADR 0010): its friction angle is 21.8 degrees. Inside its cone
    the block still creeps a few millimetres a second - MuJoCo's soft contacts, noslip on (OPEN
    LW-039) - where past it it slides off at a speed growing a hundred times faster."""
    for theta in (5., 15., 21.):
        use, mu, speed = incline(theta)
        (mu,) = mu
        assert abs(use - tan(radians(theta)) / mu) < .02, (theta, use, mu)
        assert speed < .005, "holding: creeping at most"
    use, mu, speed = incline(23.)
    (mu,) = mu
    assert tan(radians(23.)) > mu and use == pytest.approx(1., abs=1e-3) and speed > .05, "past its friction: at the edge, sliding"


def test_friction_use_is_the_cone_the_solver_keeps_and_the_backend_refuses_strangers():
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    backend = MujocoBackend()
    with World(backend, FIELDS['fetch'].scene(Entity('machine', mobile_manipulator_blueprint()))) as world:
        world.start()
        for _ in range(200):
            world.step({})
        rows = backend.friction_use('objects/fetch_cube')
        assert rows and all(other == 'field/table' for other, _, _ in rows), rows
        assert all(n > 0 and 0 <= used <= n * (1 + 1e-6) for _, n, used in rows), "inside the cone, at most at its edge"
        assert sum(n for _, n, _ in rows) == pytest.approx(.01625 * 9.81, rel=.02), "resting: the table carries its weight"
        with pytest.raises(ValueError, match='no body'):
            backend.friction_use('objects/nothing')
        mass = backend.model.body_mass[backend.model.body('objects/fetch_cube').id]
        backend.scale_mass('objects/fetch_cube', 4.)
        assert backend.model.body_mass[backend.model.body('objects/fetch_cube').id] == pytest.approx(4 * mass)
        for _ in range(200):
            world.step({})
        assert sum(n for _, n, _ in backend.friction_use('objects/fetch_cube')) == pytest.approx(4 * .01625 * 9.81, rel=.02)
        for bad in (0., -1., float('nan')):
            with pytest.raises(ValueError):
                backend.scale_mass('objects/fetch_cube', bad)


def test_a_run_follows_the_grip_while_it_carries_and_a_heavier_cube_uses_more_of_it():
    """The Fetch as designed: its grip uses a little over a third of its friction while it carries
    the cube; eight times as heavy, about three fifths, and sixteen times, it is lost on the lift."""
    from little_world.inventory.sweep import run
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    bp = mobile_manipulator_blueprint()
    plain = run('fetch', bp)
    start, end, most, when, median = plain.grip
    assert 18. < start < 20. < 36. < end < 38. and start <= when <= end
    assert .3 < median < .45 and median < most <= 1., plain.grip
    assert [r.status for r in plain.results] == ['met', 'met', 'met', 'kept']
    heavy = run('fetch', bp, masses={'objects/fetch_cube': 8.})
    assert .5 < heavy.grip[4] < .7 and heavy.result('delivered').status == 'met', heavy.grip
    lost = run('fetch', bp, masses={'objects/fetch_cube': 16.})
    assert lost.result('lifted').status == 'missed' and lost.grip[1] < 21., lost.grip


def test_reading_friction_use_changes_nothing_in_a_run():
    """mj_contactForce only reads the solver's forces: a Sprint whose every wheel contact is read at
    every step is the same run, step for step."""
    from little_world.inventory.sweep import run
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    bp = mobile_platform_blueprint()
    plain, read = [], []

    def every_wheel(state, backend):
        for name in state.bodies:
            if name.startswith('machine/'):
                backend.friction_use(name)
    run('sprint', bp, trace=plain)
    run('sprint', bp, trace=read, probe=every_wheel)
    assert plain and read == plain
