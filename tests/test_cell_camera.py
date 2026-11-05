"""Contracts for the factory cell finding its parts with its camera (OPEN LW-010, ADR 0069).

The cell's overhead camera becomes a depth camera with a RealSense D435's pixels and noise (ADR
0032), cast from where it hangs; the box finder that the Fetch table uses finds each part round
the source's place, and the pick is planned from what it saw. The part's pose is never read for
the pick - only kept beside each sighting, for the record. The Panda's home pose hangs its wrist
under the camera: the arm first clears the view.
"""
import pytest

from little_world.factory.recipe import CellRecipe
from little_world.factory.scene import conveyor_line, factory_scene, stock_name


def _cell(feeder='hand', stock=1, product='Small block'):
    from little_world.factory.controller import FactoryCycle, camera_eye
    from little_world.physics.mujoco_backend import MujocoBackend
    recipe = CellRecipe(product=product)
    scene = factory_scene(recipe=recipe, stock=stock, feeder=feeder)
    b = MujocoBackend()
    b.compile(scene, .002)
    line = conveyor_line(recipe) if feeder == 'conveyor' else None
    return b, FactoryCycle(b, line=line, eye=camera_eye(b, scene, seed=1))


def _off(sighting):
    import numpy as np
    part, seen, true, yaw, turn = sighting
    return 1000 * float(np.linalg.norm(np.subtract(seen, true)[:2])), 1000 * abs(seen[2] - true[2]), abs(yaw - turn)


@pytest.mark.parametrize('feeder', ['hand', 'conveyor'])
def test_the_camera_sees_the_part_at_the_source_once_the_arm_is_out_of_its_view(feeder):
    pytest.importorskip('mujoco')
    b, cycle = _cell(feeder)
    try:
        assert not cycle.view_clear(), "at home the Panda's wrist hangs under the camera"
        cycle.plan('Amber')
        assert cycle.provisional and not cycle.sightings, "planned where the part should be, not seen"
        cycle.start()
        assert cycle.state == 'clearing'
        for _ in range(int(8 / .002)):
            b.step(cycle.commands(.002))
            if cycle.state == 'running':
                break
        assert cycle.state == 'running' and not cycle.provisional and cycle.view_clear(), cycle.message
        (part, *_), = cycle.sightings
        along, up, turn = _off(cycle.sightings[0])
        assert part == 'objects/product' and along < 1. and up < 2. and turn < 1., (along, up, turn)
    finally:
        b.close()


def test_a_run_found_by_the_camera_places_each_part_and_a_part_not_there_is_not_picked():
    pytest.importorskip('mujoco')
    b, cycle = _cell('hand', stock=1)
    try:
        fed = {0: (.002, -.002, 5.), 1: (-.003, .001, -10.)}         # off the tray's centre, turned
        cycle.feeder = fed.__getitem__
        parts = ['objects/' + stock_name(i) for i in range(2)]
        cycle.production(parts, 'Amber')
        for _ in range(int(40 / .002)):
            b.step(cycle.commands(.002))
            if cycle.state == 'failed' or (cycle.state == 'completed' and cycle.run['done'] == 2):
                break
        assert cycle.state == 'completed' and cycle.run['done'] == 2, cycle.message
        assert [s[0] for s in cycle.sightings] == parts, "each part looked for once, the first after clearing"
        for sighting in cycle.sightings:
            along, up, turn = _off(sighting)
            assert along < 2. and up < 2. and turn < 2., (sighting[0], along, up, turn)
        for p in cycle.run['placements']:
            assert abs(p.dx) < 1.5 and abs(p.dy) < 1. and abs(p.yaw) < 3., p
        # Both placed, the input tray is empty: asked for another, the cell says it sees no part
        # there and does not reach for one.
        assert cycle.view_clear() and cycle.product == 'objects/product_2'
        cycle.state = 'idle'
        with pytest.raises(ValueError, match='does not see the part'):
            cycle.plan('Amber')
    finally:
        b.close()
