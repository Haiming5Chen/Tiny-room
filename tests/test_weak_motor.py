"""Contracts for a weakened motor among the disturbances (ADR 0058, FR-019).

A lab's robot does not only get bumped: its motors run hot. A winding's copper gains resistance
with its temperature, so at the same voltage it draws less current at stall and makes less
torque, at the same free speed; a sagging supply takes torque and speed alike. The disturbance
says which motor, from when and how much it keeps; the motor's own speed-torque line is scaled
and its friction kept.
"""
from types import SimpleNamespace

import pytest

from little_world.fields.disturbance import COPPER, LEFT, WEAK, Disturbance, Disturbing, hot


def kit_motor():
    from little_world.core.component import Motor
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    return next(c.profile for c in mobile_platform_blueprint().components if isinstance(c, Motor) and c.profile)


def test_a_hot_winding_keeps_its_free_speed_and_loses_stall_torque_as_copper_says():
    assert COPPER == .00393 and hot(50.) == pytest.approx(1 / 1.1965) and hot(0.) == 1.
    motor = kit_motor()
    stall, free = motor.line()
    warm = motor.weakened(hot(50.))
    assert warm.line() == pytest.approx((stall * hot(50.), free)), "the line pivots about its free speed"
    assert warm.friction_torque == pytest.approx(motor.friction_torque), "the gearbox's friction is the same"
    assert warm.stall_torque == pytest.approx(stall * hot(50.) - motor.friction_torque)
    assert warm.no_load_rpm < motor.no_load_rpm, "past the same friction, a little slower with no load"
    sagging = motor.weakened(.9, .9)
    assert sagging.line() == pytest.approx((stall * .9, free * .9)), "a supply 10 % low: both ends"
    assert motor.weakened() == motor
    for bad in ((0., 1.), (1.2, 1.), (1., float('nan'))):
        with pytest.raises(ValueError):
            motor.weakened(*bad)
    with pytest.raises(ValueError, match='friction'):
        motor.weakened(.03)


def test_the_backend_weakens_a_motor_until_the_world_resets():
    pytest.importorskip('mujoco')
    from little_world.core.entity import Entity
    from little_world.fields import field_scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    b = MujocoBackend()
    b.compile(field_scene('sprint', Entity('machine', mobile_manipulator_blueprint())), .002)
    try:
        idx = b._motor_ids['machine/' + LEFT]
        before = b._motor_profiles[idx][0]
        b.weaken('machine/' + LEFT, .5)
        b.weaken('machine/' + LEFT, .6)
        assert b._motor_profiles[idx][0] == before.weakened(.6), "weakened from the motor as it was, not again"
        with pytest.raises(ValueError, match='no motor'):
            b.weaken('machine/no_such_motor', .5)
        with pytest.raises(ValueError, match='no sourced profile'):
            b.weaken('machine/robot_arm_compact_1_yaw_joint_motor', .5)
        b.reset()
        assert b._motor_profiles[idx][0] == before, "a reset world's motor is itself again"
    finally:
        b.close()


def test_a_motor_disturbance_weakens_its_motor_on_its_trigger_and_says_so():
    d = WEAK['sprint'][0]
    assert (d.kind, d.motor, d.after, d.delay) == ('motor', LEFT, '', 0.) and d.torque == pytest.approx(hot())
    assert d.describe() == 'the left drive motor at 84 % of its torque, from the start'
    weakened = []
    backend = SimpleNamespace(weaken=lambda motor, torque, speed: weakened.append((motor, torque, speed)))
    state = SimpleNamespace(bodies={})
    kick = Disturbing(d, 'machine/root')
    kick.tick(backend, state, 0., {})
    kick.tick(backend, state, 1., {})
    assert weakened == [('machine/' + LEFT, d.torque, 1.)] and kick.note() == 'left motor 50 K hot at 0.0 s'
    with pytest.raises(ValueError):
        Disturbance('nothing weaker', 'motor', motor=LEFT)
    with pytest.raises(ValueError):
        Disturbance('stronger', 'motor', motor=LEFT, torque=1.5)


def test_the_kit_cart_does_not_notice_its_left_motor_run_hot():
    """The drive asks each motor for at most its operating cap, half its stall, and on the flat a
    third of its line: a motor keeping 84 % of its torque changes nothing, run for run."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import run
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    bp = mobile_platform_blueprint()
    plain, warm = [], []
    as_designed = run('sprint', bp, trace=plain)
    hot_run = run('sprint', bp, disturbance=WEAK['sprint'][0], trace=warm)
    assert hot_run.disturbed == 'left motor 50 K hot at 0.0 s'
    assert [r.status for r in hot_run.results] == [r.status for r in as_designed.results] == ['met', 'met', 'kept']
    assert warm == plain, "the same run, step for step"
