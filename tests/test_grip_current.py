"""Contracts for the jaws squeezing by current (FR-037).

The kit jaws are position servos, and their squeeze was a by-product: when the closing ramp ended
past the part (ADR 0042). A ROBOTIS XH430 in current-based position control (its Operating Mode 5)
runs its position loop with the current capped at its Goal Current, so a squeeze becomes a setting.
Here an action block's `secondary` is its jaws' squeeze in newtons at each pad's centre - the cap
on each jaw's torque its lever gives - kept until an action on those jaws sets another.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from little_world.programming.execution import apply
from little_world.programming.program import Block, Program, Runner


def test_an_action_block_carries_its_squeeze_to_the_controller():
    with pytest.raises(ValueError, match='squeeze'):
        Block('action', 'jaws', 1, 1., secondary=-1.)
    with pytest.raises(ValueError, match='squeeze'):
        Block('action', 'jaws', 1, 1., secondary=101.)
    runner = Runner()
    runner.start(Program((Block('action', 'jaws', 1, .1, secondary=4.), Block('action', 'jaws', -1, .1))))
    calls = []
    control = SimpleNamespace(specs=(SimpleNamespace(id='jaws', positive_key='G', negative_key='H', actuators=('a', 'b')),),
                              limits={}, squeeze=lambda name, newtons: calls.append((name, newtons)))
    out = runner.tick(.05, {})
    assert out['squeeze'] == ('jaws', 4.) and apply(out, control) == {'G'} and calls == [('jaws', 4.)]
    for _ in range(3):
        out = runner.tick(.05, {})
    assert out['squeeze'] == ('jaws', 0.) and out['action'] == ('jaws', -1)
    control.limits = {'a': .2}
    apply(out, control)
    assert calls[-1] == ('jaws', 0.), "an action without a squeeze gives the jaws their full torque back"


def lab(newtons, long=.004, width=.056, seconds=2.5):
    """The arm lab's kit gripper closing on a fixed box between its pads - `long` along them, `width`
    across, its centre at theirs - with `newtons` of squeeze: (each pad's push on the box, N; the
    controller; the jaws' registers at the end)."""
    import mujoco as mj
    from little_world.control import feel
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.arm_lab import arm_lab_blueprint
    bp = arm_lab_blueprint()
    jaws = next(s for s in bp.controllers if s.id == 'control_jaws')
    b = MujocoBackend()
    b.compile(Scene((Entity('machine', bp),)), .002)
    m, d = b.model, b.data
    control = MujocoKeyboardControl(b, bp)
    for _ in range(250):
        b.step(control.step_commands(.002))
    pads = [int(m.body_geomadr[i]) for i in range(m.nbody) if m.body(i).name.endswith('_pad')]
    centre = (d.geom_xpos[pads[0]] + d.geom_xpos[pads[1]]) / 2
    turn = np.zeros(4)
    mj.mju_mat2Quat(turn, d.geom_xmat[pads[0]])
    b.close()
    box = field_entities([fixed('block', (long, width, .02), 'plywood', tuple(centre), tuple(turn))])
    b = MujocoBackend()
    b.compile(Scene((Entity('machine', bp),) + box), .002)
    m, d = b.model, b.data
    control = MujocoKeyboardControl(b, bp)
    for _ in range(250):
        b.step(control.step_commands(.002))
    control.squeeze(jaws.id, newtons)
    control.press(jaws.positive_key)
    for _ in range(round(seconds / .002)):
        b.step(control.step_commands(.002))
    block, force, pushed = m.body('field/block').id, np.zeros(6), {}
    for i in range(d.ncon):
        c = d.contact[i]
        pair = {int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])}
        if block in pair:
            mj.mj_contactForce(m, d, i, force)
            pad = (pair - {block}).pop()
            pushed[pad] = pushed.get(pad, 0.) + force[0]
    pushed = list(pushed.values())
    registers = feel.read(b, control, jaws.actuators)
    b.close()
    return pushed, control, registers


@pytest.mark.parametrize('newtons', (1., 2., 4., 6.))
def test_a_squeeze_in_newtons_is_what_each_pad_pushes_with_at_its_centre(newtons):
    pytest.importorskip('mujoco')
    pushed, control, registers = lab(newtons)
    assert len(pushed) == 2 and all(abs(p - newtons) < .05 * newtons for p in pushed), (newtons, pushed)
    assert len(control.levers) == 2 and all(v == pytest.approx(.0525, abs=1e-4) for v in control.levers.values()), \
        "the pad's centre, 52.5 mm from the pivot"
    from little_world.control import feel
    goal = round(newtons * .0525 / feel.TORQUE_PER_AMP / feel.CURRENT_UNIT)
    assert feel.holding(registers) and all(abs(j.current - goal) <= 1 for j in registers), \
        "Present Current at its Goal Current while it holds, as the servo reads it"


def test_rotary_jaws_push_less_where_a_part_reaches_out_past_the_pads_centre():
    """A squeeze is a torque: a box as long as most of the pad touches first at its outer edge,
    15 mm past the pad's centre, and is pushed with 52.5 / 67.5 of the setting."""
    pytest.importorskip('mujoco')
    pushed, _, _ = lab(4., long=.03)
    assert all(abs(p - 4. * 52.5 / 67.5) < .1 for p in pushed), pushed
    full, _, _ = lab(0.)
    assert all(p > 8. for p in full), "no squeeze set: the motors' full 0.6 N m"
