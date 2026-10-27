"""Contracts for the factory cell's straight descents and narrow release (ADR 0057, OPEN LW-037).

The defect, found by judging the cell by its process window (ADR 0056): tall blocks failed every
production run. The cell moved its joints from pose to pose, so lowering a part into the
destination tray swung the tool up to 15 mm off its slot's vertical halfway down, and a tall part's
bottom caught the top edge of the part beside it; and the hand opened fully, 80 mm, to let a part
go, and a finger reached the next tall part.
"""
import numpy as np
import pytest

mj = pytest.importorskip('mujoco')

from little_world.factory.controller import CLEAR, HAND_OPEN, LINES, SLOTS, STEP, FactoryCycle  # noqa: E402
from little_world.factory.process import judge, slot_room  # noqa: E402
from little_world.factory.scene import factory_scene, stock_name  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402


def cell(product='Small block', stock=0):
    b = MujocoBackend()
    b.compile(factory_scene(product=product, stock=stock), .002)
    return b, FactoryCycle(b)


def test_the_moves_up_and_down_are_solved_a_centimetre_at_a_time_along_their_line():
    b, cycle = cell()
    try:
        cycle.plan('Amber')
        lines = [s for s in cycle.stages if s.label in LINES]
        assert [s.label for s in lines] == list(LINES) and all(s.path is None for s in cycle.stages if s not in lines)
        scratch = mj.MjData(b.model)
        for stage in lines:
            start = cycle.stages[cycle.stages.index(stage) - 1].point
            assert len(stage.path) - 1 == round(np.linalg.norm(stage.point - start) / STEP) == 16
            assert np.array_equal(stage.path[-1], stage.target), "the line ends where the stage does"
            for x in np.linspace(0, 1, 49):
                scratch.qpos[:] = b.data.qpos
                scratch.qpos[cycle.qids] = cycle.along(stage, cycle.stages[cycle.stages.index(stage) - 1].target, x)
                mj.mj_forward(b.model, scratch)
                assert np.allclose(start[:2], stage.point[:2]), "each is straight up or down"
                off = np.linalg.norm(cycle.tool(scratch)[:2] - stage.point[:2])
                assert off < .001, (stage.label, x, off)
    finally:
        b.close()


def test_the_hand_opens_only_a_little_past_the_part_to_let_it_go():
    b, cycle = cell()
    try:
        cycle.plan('Blue')
        grips = {s.label: s.grip for s in cycle.stages}
        assert grips['Approach product'] == 255 and grips['Close gripper'] == 0
        assert grips['Release product'] == grips['Retract'] == pytest.approx((.016 + CLEAR) / HAND_OPEN * 255)
        assert 2 * HAND_OPEN * grips['Release product'] / 255 == pytest.approx(.048), "48 mm, not 80"
    finally:
        b.close()


def test_tall_blocks_now_go_into_their_slots_and_the_tool_keeps_to_the_vertical():
    b, cycle = cell('Tall block', stock=5)
    try:
        parts = ['objects/' + stock_name(i) for i in range(6)]
        cycle.production(parts, 'Amber')
        stray = 0.
        for _ in range(int(90 / .002)):
            b.step(cycle.commands(.002))
            if cycle.state == 'running' and cycle.stages[cycle.index].label == 'Lower into bin':
                stage = cycle.stages[cycle.index]
                stray = max(stray, float(np.linalg.norm(cycle.tool(b.data)[:2] - stage.point[:2])))
            if cycle.state == 'failed' or (cycle.state == 'completed' and cycle.run['done'] == 6):
                break
        assert cycle.state == 'completed' and cycle.run['done'] == 6, cycle.message
        zx, zy, turn = slot_room(SLOTS, 32.)
        window = judge(cycle.run['placements'], (zx, zy), turn)
        assert window.inside == 6 and window.worst < 6., window
        assert stray < .0055, f'the tool strayed {1000 * stray:.1f} mm from the vertical: the arm sags, it does not swing'
    finally:
        b.close()
