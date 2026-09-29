"""Contracts for servo damping the solver integrates (ADR 0014).

The defect: a joint's position controller commanded bias + kp * error - kd * speed once
per 2 ms step, so its damping acted on the speed of the step before. That sampled
damping is unstable at these gains: an anchored arm nudged at 0.2 rad/s chattered
between its torque limits for good, and the mobile manipulator - kicked by settling
onto the floor - could not stand still: arm motors at their limit 70 % of the time,
the base rocking between its casters and creeping 12 cm in 3 s.
"""
from dataclasses import replace
from math import degrees
import pytest

from little_world.core.blueprint import ControllerSpec
from little_world.core.command import Torque, slope_of


# -- the command: a torque that says how it changes with speed ---------------------------

def test_a_torque_command_is_a_float_with_a_slope():
    t = Torque(1.25, -.4)
    assert isinstance(t, float) and t == 1.25 and t.slope == -.4
    assert slope_of(t) == -.4 and slope_of(1.25) == 0.
    assert slope_of(-t) == 0. and slope_of(t * 2) == 0., "arithmetic makes a plain torque"
    assert slope_of(max(-2., min(2., t))) == -.4, "a clamp that does not bind keeps it"
    assert slope_of(max(-1., min(1., t))) == 0., "one that binds replaces it with the limit"


@pytest.mark.parametrize("slope", [.1, float("inf"), float("nan")])
def test_a_slope_that_would_feed_energy_in_is_refused(slope):
    with pytest.raises(ValueError):
        Torque(1., slope)
    with pytest.raises(ValueError):
        Torque(float("nan"), -.1)


def test_the_position_controller_reports_its_damping_unless_it_is_saturated():
    from little_world.control.keyboard import KeyboardPositionControl
    spec = ControllerSpec('lift', 'keyboard_position', ('a', 'b'), positive_key='R', negative_key='V',
                          speed=30, kp=8, kd=.4)
    control = KeyboardPositionControl((spec,))
    control.targets.update(a=.1, b=1.)
    out = control.commands({'a': (0., .5, -2., 2., 3.), 'b': (0., 0., -2., 2., 3.)}, .002)
    assert out['a'] == pytest.approx(8 * .1 - .4 * .5) and out['a'].slope == -.4
    assert out['b'] == 3. and slope_of(out['b']) == 0., "at its limit the torque no longer follows speed"


# -- the solver: the slope is integrated, the command is exact ----------------------------

mujoco = pytest.importorskip("mujoco")
import numpy as np  # noqa: E402
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_drive import MujocoDrive  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.fields import field_scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.arm_family import arm_family_blueprint  # noqa: E402
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint  # noqa: E402


def open_world(bp):
    backend = MujocoBackend()
    world = World(backend, field_scene('sprint', Entity('machine', bp)))
    world.start()
    return world, backend


def saturated(backend, commands):
    m = backend.model
    return any(abs(v) >= .98 * m.actuator_ctrlrange[m.actuator(k).id, 1] for k, v in commands.items())


def test_the_command_is_the_torque_at_the_current_speed():
    """The slope only shapes the step; at the speed the controller saw, the actuator
    delivers exactly what it was told."""
    bp = arm_family_blueprint('Compact arm kit')
    world, backend = open_world(bp)
    with world:
        name = 'machine/robot_arm_compact_1_elbow_joint_motor'
        idx = backend.model.actuator(name).id
        dof = backend.model.jnt_dofadr[backend.model.actuator_trnid[idx, 0]]
        backend.data.qvel[dof] = .3
        world.step({name: Torque(.25, -.8)})
        assert backend.data.actuator_force[idx] == pytest.approx(.25, abs=1e-12)
        world.step({name: .25})
        assert backend.model.actuator_biasprm[idx, 2] == 0., "a plain torque leaves no slope behind"
        assert backend.data.actuator_force[idx] == pytest.approx(.25, abs=1e-12)


def test_a_nudged_arm_settles_back_onto_its_targets():
    """Anchored, the explicit damping only looked stable because the arm started
    exactly at rest; 0.2 rad/s on every joint set it chattering at its limits."""
    bp = arm_family_blueprint('Compact arm kit')
    world, backend = open_world(bp)
    with world:
        arm = MujocoKeyboardControl(backend, bp)
        late = []
        for step in range(1000):
            if step == 100:
                for _, dof, *_ in arm.channels.values():
                    backend.data.qvel[dof] += .2
            commands = arm.step_commands(world.timestep)
            world.step(commands)
            if step >= 600:
                late.append(saturated(backend, commands))
        assert not any(late), f"{100 * sum(late) / len(late):.0f} % of late steps at a torque limit"
        for name, (q, *_) in arm.channels.items():
            assert abs(degrees(backend.data.qpos[q] - arm.targets[name])) < .5, name


def test_the_mobile_manipulator_stands_still_with_its_arm_held():
    bp = mobile_manipulator_blueprint()
    world, backend = open_world(bp)
    with world:
        arm = MujocoKeyboardControl(backend, bp)
        drive = MujocoDrive(backend, bp)
        root = backend.model.body('machine/root').id
        pitch, busy, start = [], 0, None
        for step in range(1500):
            commands = dict(drive.step_commands((0., 0.), world.timestep))
            joints = arm.step_commands(world.timestep)
            commands.update(joints)
            world.step(commands)
            if step == 750:
                start = backend.data.xpos[root].copy()
            if step >= 750:
                w, x, y, z = backend.data.xquat[root]
                pitch.append(degrees(np.arcsin(2 * (w * y - z * x))))
                busy += saturated(backend, joints)
        assert max(pitch) - min(pitch) < .1, (min(pitch), max(pitch))
        assert np.linalg.norm(backend.data.xpos[root][:2] - start[:2]) < .002, "no creeping"
        assert busy == 0
        for name, (q, *_) in arm.channels.items():
            assert abs(degrees(backend.data.qpos[q] - arm.targets[name])) < .5, name


def test_a_saturated_servo_is_not_damped_by_a_slope_it_no_longer_has():
    """MuJoCo keeps an actuator's velocity derivative in its implicit step even when a
    force range clamps the force, which would brake a joint its motor cannot hold.
    Here a command at its limit is a plain torque: the arm falls as fast as the limit
    lets it, not slower."""
    bp = arm_family_blueprint('Compact arm kit')
    weak = replace(bp, components=tuple(replace(c, max_torque=.05) if hasattr(c, 'max_torque') else c
                                        for c in bp.components))
    world, backend = open_world(weak)
    with world:
        arm = MujocoKeyboardControl(backend, weak)
        name = 'machine/robot_arm_compact_1_shoulder_joint_motor'
        idx = backend.model.actuator(name).id
        for _ in range(100):
            commands = arm.step_commands(world.timestep)
            world.step(commands)
        assert abs(commands[name]) == .05, "it cannot hold the arm up"
        assert slope_of(commands[name]) == 0. and backend.model.actuator_biasprm[idx, 2] == 0.


def test_a_sourced_motor_line_takes_precedence_over_the_controller_slope():
    """Where the speed-torque line limits a gearmotor, the line is what the torque
    follows (ADR 0011), whatever the controller asked for."""
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    from little_world.assets.real_motors import KIT_GEARMOTOR, PROFILES
    bp = mobile_platform_blueprint()
    world, backend = open_world(bp)
    with world:
        name = 'machine/' + bp.controllers[0].actuators[0]
        idx = backend.model.actuator(name).id
        dof = backend.model.jnt_dofadr[backend.model.actuator_trnid[idx, 0]]
        stall, free = PROFILES[KIT_GEARMOTOR].line()
        backend.data.qvel[dof] = .95 * free
        high = backend.model.actuator_ctrlrange[idx, 1]
        world.step({name: Torque(float(high), -.01)})
        assert backend.model.actuator_biasprm[idx, 2] == pytest.approx(-stall / free)
