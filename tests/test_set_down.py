"""The cube set down in the bin, not dropped into it (ADR 0042; OPEN LW-024).

ADR 0040 found the Fetch program letting the cube go about 6 cm over the bin's floor. The kit
arm cannot bring its jaws lower there while they stay level: any lower and it hits its own
cart. So the jaws carry the cube level and, over the bin, tilt down by whatever angle lets the
arm lower it furthest - 25 degrees for the kit cart - and they close on the cube's upper half,
so its lower half hangs below them and meets the floor first. The cube comes down on an edge
2 mm over the floor and settles flat.
"""
import numpy as np
import pytest

CENTRE = (1.84, 0., .14)    # the Fetch cube on the table (m)
FLOOR = .006                # the top of the bin's floor (m)


def planned(**changes):
    """The Fetch program solved for the kit cart as designed, with the motion it was solved
    with and where the base stood - what `sweep.solve` does, keeping its parts; `changes` set
    constants of `tool_motion` while it is solved."""
    pytest.importorskip('mujoco')
    import little_world.control.tool_motion as tool_motion
    import little_world.fields as fields
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.inventory import sweep
    from little_world.physics.mujoco_backend import MujocoBackend
    old = {k: getattr(tool_motion, k) for k in changes}
    bp = sweep.design('mobile_manipulator')
    field, backend = FIELDS['fetch'], MujocoBackend()
    world = World(backend, field.scene(Entity('machine', bp)))
    world.__enter__()
    try:
        for k, v in changes.items():
            setattr(tool_motion, k, v)
        state = world.start()
        drive, control, base = sweep._rigs(backend, bp)
        for _ in range(sweep.SETTLE):
            state = sweep._hold(world, drive, control, field, state)
        motion = tool_motion.ToolMotion(backend, bp, control)
        jaws = next(s.id for s in control.specs if s.actuators and set(s.actuators) <= set(motion.jaws))
        program = tool_motion.fetch(motion, base, jaws, 'objects/fetch_cube', (*fields.BIN, FLOOR),
                                    reach_in=fields.BIN_SIZE / 2 - .045, look=True)
        return program, motion, base.pose(), backend, world
    finally:
        for k, v in old.items():
            setattr(tool_motion, k, v)


def poses(program):
    """The program's poses in the order they come: ready, above, at, lift, over, down, retract."""
    labels = ('ready', 'above', 'at', 'lift', 'over', 'down', 'retract')
    return dict(zip(labels, (b for b in program.blocks if b.kind == 'pose')))


def lowest_corner(program, motion, now, backend, label):
    """The cube's lowest corner (m) with the arm at pose `label`, held as the jaws close on it."""
    from little_world.control.tool_motion import _held_corners
    stop = next(b for b in program.blocks if b.kind == 'goto').point
    p = poses(program)
    corners = _held_corners(motion, now, (stop[0], stop[1], np.radians(stop[2])),
                            backend.model.body('objects/fetch_cube').id, motion.angles(p['at'].angles))
    d = motion._pose(motion.angles(p[label].angles))
    return float(np.min((corners @ d.xmat[motion.body].reshape(3, 3).T + d.xpos[motion.body])[:, 2]))


def tilt(motion, pose):
    """How far the jaws point down at a pose (degrees)."""
    return float(np.degrees(np.arcsin(-motion.tool(angles=motion.angles(pose.angles))[1][2])))


def test_the_jaws_close_on_the_upper_half_and_over_the_bin_tilt_to_set_the_cube_down():
    """Planned for the cart as designed: level at the table, the jaws' lower edge at the cube's
    middle, 20 mm over the table; over the bin, tilted 25 degrees - the least, in 5 degree
    steps, that lowers the cube furthest - its lowest corner 2.5 mm over the floor, the jaws
    10.8 mm over it."""
    from little_world.control.tool_motion import JAWS_CLEAR, SET_GAP, _jaws_low
    program, motion, now, backend, world = planned()
    try:
        p = poses(program)
        assert abs(tilt(motion, p['at'])) < 1. and abs(tilt(motion, p['lift'])) < 1.
        assert _jaws_low(motion, motion.angles(p['at'].angles)) == pytest.approx(CENTRE[2], abs=.001)
        assert tilt(motion, p['down']) == pytest.approx(25., abs=.5) and tilt(motion, p['over']) == pytest.approx(25., abs=.5)
        corner = lowest_corner(program, motion, now, backend, 'down') - FLOOR
        assert SET_GAP <= corner < SET_GAP + .0025 and corner == pytest.approx(.0025, abs=.0005)
        assert _jaws_low(motion, motion.angles(p['down'].angles)) - FLOOR >= JAWS_CLEAR
    finally:
        world.__exit__(None, None, None)


def test_allowed_no_tilt_the_arm_lets_the_cube_go_as_low_as_it_reaches_level():
    """With the jaws kept as they point, the kit arm stops over the bin with the cube's lowest
    corner 4.9 cm over the floor - any lower and it hits its own cart: the tilt is what sets it
    down."""
    program, motion, now, backend, world = planned(TILT_MOST=0.)
    try:
        p = poses(program)
        assert abs(tilt(motion, p['down'])) < 1.
        assert lowest_corner(program, motion, now, backend, 'down') - FLOOR == pytest.approx(.049, abs=.001)
    finally:
        world.__exit__(None, None, None)


@pytest.mark.parametrize('payload', (0., .5))
def test_the_cube_is_set_down_without_a_fall_and_comes_to_rest_upright(payload):
    """As designed and carrying 0.5 kg: every goal met; let go with its corner a few
    millimetres over the floor, it falls under a centimetre (6.8 cm before) and lands at under
    1 N in any step (2.2 N before); it leaned 25 degrees in the tilted jaws, did not lean before
    they held it, and comes to rest upright."""
    pytest.importorskip('mujoco')
    from little_world.fields.variation import Variation, payload_site
    from little_world.inventory.sweep import design, run, solve
    bp = design('mobile_manipulator')
    result = run('fetch', bp, Variation(payload=payload), solve('fetch', bp), payload_site(bp))
    assert all(r.status in ('met', 'kept') for r in result.results), result.message
    h = result.handled[0]
    assert h.dropped is not None and h.dropped < .01 and h.of('peak', 'bin') < 1.
    assert h.tilt == pytest.approx(26., abs=2.) and h.before < 2. and h.rest < 2.


def test_held_firmly_the_cube_that_crept_out_of_the_jaws_is_set_down():
    """Repeat 44 of the 59 drawn set-ups - the pads' friction low in its range, 0.44 kg on
    the deck: held at what the jaws' closing gave, about 0.5 N a pad, the cube crept 10 mm
    down the pads as the cart drove, turned in the tilted jaws, slipped out 3 cm over the
    bin's floor and was pressed there by the jaws at 1.65 N. Squeezed 0.6 degrees more once
    it is felt held (`SQUEEZE`), it is set down: it falls under a centimetre and the bin's push
    on it stays under 0.5 N over 50 ms."""
    pytest.importorskip('mujoco')
    from little_world.fields.variation import payload_site, plan
    from little_world.inventory.sweep import design, ranges_for, run, solve
    bp = design('mobile_manipulator')
    drawn = plan(ranges_for('fetch'), 59, 1)
    setup = next(v for v in drawn if v.label == 'repeat 44')
    result = run('fetch', bp, setup, solve('fetch', bp), payload_site(bp, max(v.payload for v in drawn)))
    assert all(r.status in ('met', 'kept') for r in result.results), result.message
    h = result.handled[0]
    assert h.dropped < .01 and h.of('steady', 'bin') < .5 and h.rest < 2.
