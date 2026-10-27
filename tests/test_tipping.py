"""Contracts for the force-angle measure of how near a machine is to tipping (ADR 0059, FR-005).

The defect: the static margin (ADR 0015, 0022) sees the centre of mass and the support polygon and
nothing of the machine's accelerations - "hard braking can tip a machine with margin left", as the
telemetry says of it. The force-angle measure (Papadopoulos and Rey) adds the inertial force and
moment to the weight and reads the angle each support edge has left.
"""
from math import atan, cos, degrees, radians, sin

import numpy as np
import pytest

from little_world.control.tipping import force_angles, measure, ordered

SQUARE = [(0., 0., 0.), (1., 0., 0.), (1., 1., 0.), (0., 1., 0.)]   # anticlockwise from above
CENTRE = (.5, .5, 1.)
WEIGHT = (0., 0., -9.81)


def test_at_rest_on_the_flat_each_edge_has_the_angle_its_reach_and_height_give():
    for angle in force_angles(SQUARE, CENTRE, WEIGHT):
        assert degrees(angle) == pytest.approx(degrees(atan(.5 / 1.)))
    assert measure(SQUARE, CENTRE, WEIGHT)[0] == pytest.approx(26.565, abs=1e-3)


def test_on_a_slope_the_downhill_edge_runs_out_at_the_static_tip_angle():
    for slope in (10., 26.565, 40.):
        s = radians(slope)
        tilt = lambda p: (p[0], p[1] * cos(s) - p[2] * sin(s), p[1] * sin(s) + p[2] * cos(s))   # rolled about x
        corners = [tilt(p) for p in SQUARE]
        angle, edge, _ = measure(corners, tilt(CENTRE), WEIGHT)
        assert edge == 0, "the downhill edge, y = 0"
        assert angle == pytest.approx(26.565 - slope, abs=1e-3), "the static tip angle: atan(reach / height)"


def test_braking_takes_atan_of_its_deceleration_over_g_from_the_front_edge():
    for decel in (2., 4.905, 9.81):
        force = np.array(WEIGHT) - np.array((-decel, 0., 0.))       # m (g - a), a decelerating along +x
        angles = force_angles(SQUARE, CENTRE, force)
        front = degrees(angles[1])                                   # the edge at x = 1
        assert front == pytest.approx(26.565 - degrees(atan(decel / 9.81)), abs=1e-3)
        assert degrees(angles[3]) == pytest.approx(26.565 + degrees(atan(decel / 9.81)), abs=1e-3), "the back gains"
    assert force_angles(SQUARE, CENTRE, (9.81, 0., -9.81))[1] < 0, "past the edge: negative, tipping"


def test_a_moment_tipping_the_machine_over_an_edge_takes_angle_from_it():
    still = force_angles(SQUARE, CENTRE, WEIGHT)[0]
    pitched = force_angles(SQUARE, CENTRE, WEIGHT, moment=(2., 0., 0.))[0]   # about +x: over the edge at y = 0
    assert pitched < still
    assert force_angles(SQUARE, CENTRE, WEIGHT, moment=(-2., 0., 0.))[0] > still


def test_the_support_is_ordered_anticlockwise_and_inner_points_dropped():
    points = [(1., 1., 0.), (0., 0., 0.), (.5, .5, 0.), (0., 1., 0.), (1., 0., 0.)]
    corners = ordered(points, (0., 0., 1.))
    assert len(corners) == 4
    signed = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, np.roll(corners, -1, axis=0)))
    assert signed > 0, "anticlockwise seen from above"
    turned = ordered([(p[0], -p[2], p[1]) for p in points], (0., -1., 0.))
    assert len(turned) == 4, "a support seen from its own side, whatever way up"


# -- on the solver's state ------------------------------------------------------------------

def tilted(make, every=10):
    """The tilt table run with a watch called every `every` steps: [(table degrees, angle left)], the run."""
    pytest.importorskip('mujoco')
    from little_world.control.tipping import Watch
    from little_world.fields import FIELDS, table_angle
    from little_world.inventory.sweep import run
    seen, watch, step = [], {}, [0]

    def probe(state, backend):
        step[0] += 1
        if step[0] % every:
            return
        if 'w' not in watch:
            watch['w'] = Watch(backend, backend.model.body('machine/root').id, ground=FIELDS['tilt'].ground)
        out = watch['w']()
        if out is not None:
            seen.append((table_angle(state), out[0]))
    return seen, run('tilt', make(), probe=probe)


def test_on_the_tilt_table_the_angle_runs_out_as_the_arm_cart_goes_over():
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    seen, r = tilted(mobile_manipulator_blueprint)
    assert seen[0][1] > 40, "standing on the level table, far from tipping"
    out = next(table for table, left in seen if left <= 0)
    assert 52.5 < out < r.tipped < r.predicted, (out, r.tipped, r.predicted)
    # As the table rises slowly the angle falls steadily with it - three quarters of a degree a
    # degree, its downhill edge not quite along the hinge: a static test.
    early = [(t, a) for t, a in seen if 30 < t < 40]
    slope = (early[-1][1] - early[0][1]) / (early[-1][0] - early[0][0])
    assert -.85 < slope < -.65, slope


def test_the_cart_without_its_arm_keeps_twelve_degrees_at_the_tables_top():
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    seen, r = tilted(mobile_platform_blueprint)
    assert r.tipped is None and seen[-1][0] == pytest.approx(60., abs=.1)
    assert 10. < seen[-1][1] < 14., "it would run out near 72 degrees, as its stance predicts with the rail"
    assert seen[-1][0] + seen[-1][1] == pytest.approx(r.predicted, abs=1.)


def test_a_hard_stop_takes_degrees_from_the_kit_cart_but_does_not_tip_it():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.control.tipping import Watch
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import AHEAD, _rigs, _root
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    bp = mobile_manipulator_blueprint()
    backend = MujocoBackend()
    with World(backend, FIELDS['sprint'].scene(Entity('machine', bp))) as world:
        state = world.start()
        drive, control, _ = _rigs(backend, bp)
        root = backend.model.body(_root(bp)).id
        watch = Watch(backend, root)
        cruising = braking = None
        stop = None
        for _ in range(int(9 / world.timestep)):
            x = float(backend.data.subtree_com[root][0])
            if stop is None and x >= 2.5:
                stop = state.time
            commands = dict(drive.step_commands(AHEAD if stop is None else (0., 0.), world.timestep))
            commands.update(control.step_commands(world.timestep))
            state = world.step(commands)
            out = watch()
            if out is None:
                continue
            if stop is None and x > 2.:
                cruising = out[0] if cruising is None else min(cruising, out[0])
            elif stop is not None and state.time - stop < 2.:
                braking = out[0] if braking is None else min(braking, out[0])
        assert stop is not None and cruising is not None and braking is not None
        assert 30. < braking < cruising - 2., (braking, cruising)
