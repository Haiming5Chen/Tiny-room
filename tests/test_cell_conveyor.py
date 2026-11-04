"""Contracts for the factory cell fed by the roller conveyor (FR-007, ADR 0068).

The cell's parts ride pallets along a roller conveyor on its table to a stop at the source's place;
the Panda picks each off its pallet, and the emptied pallet goes back to the line's start with the
next part on it - the return and the loading are a person's, not simulated. The rollers are
friction rollers: their drives pass a twentieth of the load to them, so the rollers under a pallet
the stop holds stand still (Interroll, "Conveyor rollers: planning basics").
"""
import pytest

from little_world.factory.recipe import CellRecipe
from little_world.factory.scene import NEST, ON_LINE, conveyor_line, factory_scene, stock_name
from little_world.fields import conveyor as cv


def test_a_friction_rollers_drive_passes_a_twentieth_of_the_load_on_it():
    share = (cv.PALLET[0] * cv.PALLET[1] * cv.PALLET[2] * cv.DENSITY + .025) * cv.G * cv.PITCH / cv.PALLET[0]
    assert cv.Line(load=.025).clutch() == pytest.approx(.05 * share * cv.ROLLER[0]), "4 to 6 % of the load on a 50 mm roller"
    assert cv.Line(friction=False).clutch() == cv.DRIVE[1], "an ideal servo's own limit otherwise"
    assert cv.Line(load=.025).clutch() < .3 * share * cv.ROLLER[0], "less than HDPE on steel can hold: a held pallet stops them"


def test_the_conveyor_takes_the_sources_place_and_says_where_it_does_not_fit():
    line = conveyor_line(CellRecipe())
    assert line.heading == -1 and line.entity == 'factory' and line.at_stop(1) == pytest.approx(.45), "towards the robot"
    assert line.bed_bottom() == pytest.approx(.70), "its bed on the table"
    x0, y0, x1, y1 = line.footprint()
    assert x1 < .875 and x0 > .2 and y1 < .24 - .09 and y0 > -.24 + .09, "on the table, clear of the trays and the base"
    with pytest.raises(ValueError, match='off the table'):
        conveyor_line(CellRecipe().moved('input', (.6, 0.)))
    with pytest.raises(ValueError, match='Amber tray'):
        conveyor_line(CellRecipe().moved('Amber', (.44, .35)).moved('input', (.45, .14)))
    with pytest.raises(ValueError, match='Unknown feeder'):
        factory_scene(feeder='chute')
    scene = factory_scene(stock=5, feeder='conveyor')
    factory, objects = (next(e for e in scene.entities if e.id == n).blueprint for n in ('factory', 'objects'))
    names = {c.id for c in factory.components}
    assert 'input_base' not in names and {'conveyor_stop', 'roller_8_motor'} <= names, "the stop instead of the tray"
    bodies = {c.id: c for c in objects.components}
    assert [f'pallet_{k}' for k in range(1, ON_LINE + 1)] == [n for n in bodies if n.startswith('pallet_') and '_bar' not in n]
    for k in range(1, ON_LINE + 1):
        pallet, part = bodies[f'pallet_{k}'], bodies[stock_name(k - 1)]
        assert pallet.transform.position[:2] == pytest.approx(part.transform.position[:2]), "each part on a pallet"
        bars = [bodies[f'pallet_{k}_bar_{j}'] for j in (0, 1)]
        assert all(b.parent == f'pallet_{k}' for b in bars)
        gap = bars[1].transform.position[0] - bars[0].transform.position[0] - NEST[1]
        assert gap == pytest.approx(.032 + 2 * NEST[0]), "the nest: the part's width and its room"
    assert sum(1 for n in bodies if n.startswith('product')) == 6, "four more on the shelf"


def test_a_run_fed_by_the_conveyor_places_each_part_each_arriving_within_its_nest():
    pytest.importorskip('mujoco')
    from little_world.factory.controller import FactoryCycle
    from little_world.physics.mujoco_backend import MujocoBackend
    recipe = CellRecipe()
    b = MujocoBackend(); b.compile(factory_scene(recipe=recipe, stock=2, feeder='conveyor'), .002)
    try:
        cycle = FactoryCycle(b, line=conveyor_line(recipe))
        fed = {0: (0., 0., 0.), 1: (.001, -.003, 2.), 2: (-.0005, .002, -4.)}    # where the person puts each on its pallet
        cycle.feeder = fed.__getitem__
        parts = ['objects/' + stock_name(i) for i in range(3)]
        assert cycle.carrier == {'objects/product': 'objects/pallet_1', 'objects/product_2': 'objects/pallet_2'}
        cycle.production(parts, 'Amber')
        assert cycle.state == 'waiting', "the first picked once its pallet rests at the stop"
        machine = {i for i in range(b.model.nbody) if b.model.body(i).name.startswith('machine/')}
        touched = set()
        for _ in range(int(45 / .002)):
            b.step(cycle.commands(.002))
            for c in b.data.contact[:b.data.ncon]:
                pair = {b.model.geom_bodyid[c.geom1], b.model.geom_bodyid[c.geom2]}
                if pair & machine and not pair <= machine:
                    touched |= {b.model.body(i).name for i in pair - machine}
            if cycle.state == 'failed' or (cycle.state == 'completed' and cycle.run['done'] == 3):
                break
        assert cycle.state == 'completed' and cycle.run['done'] == 3, cycle.message
        assert touched <= set(parts), f"the arm touched only its parts: {touched}"
        arrivals = cycle.run['arrivals']
        assert len(arrivals) == 3 and all(w < .3 for *_, w in arrivals), "each pallet was there when the arm came back"
        for (x, y, _), (dx, dy, _) in zip(arrivals, (fed[i] for i in range(3))):
            # Forward along the line no further than its bar, across within a millimetre of where it was put.
            assert -1000 * NEST[0] - .5 < x < 1000 * dx + .5 and abs(y - 1000 * dy) < 1., (x, y)
        for p in cycle.run['placements']:
            assert 0. < p.dx < 1.5 and abs(p.dy) < 1. and abs(p.yaw) < 3., p
        # The emptied pallets went back: the third part's pallet at the stop, the other queued behind.
        at = [float(b.data.xpos[b.model.body(f'objects/pallet_{k}').id][0]) for k in (1, 2)]
        assert sorted(at) == pytest.approx([cycle.line.at_stop(1), cycle.line.at_stop(2)], abs=.001), at
        with pytest.raises(ValueError, match="does not fit between its pallet's bars"):
            cycle.feeder = lambda i: (.002, 0., 10.)
            cycle.carrier['objects/product'] = 'objects/pallet_1'
            cycle.feed('objects/product', 0)
    finally:
        b.close()
