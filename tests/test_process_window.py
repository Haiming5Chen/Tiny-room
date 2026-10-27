"""Contracts for judging the factory cell by its process window (ADR 0056, FR-029).

The defect: a production run (ADR 0019) counted the parts placed and checked each was inside its
tray, 8 cm by 7 cm round its centre. Where in its slot a part landed, against the room it had before
it would touch its neighbour, and how long each took, were not measured: the cell's parts land
3 to 4 mm off their slots, the arm sagging under its servos and the part creeping in a hand that
squeezes 1.6 N.
"""
from math import cos, inf, isclose, radians, sin, sqrt

import pytest

from little_world.factory.process import (Placement, capability, judge, line, lower_bound, room,
                                          slot_room, tightest, turn_room)


def test_the_room_a_part_has_is_half_the_pitch_less_its_width_and_the_turn_that_reaches_the_next():
    assert room(45., 32.) == 6.5 and room(70., 32.) == 19.
    with pytest.raises(ValueError):
        room(32., 32.)
    t = radians(turn_room(45., 32.))
    assert isclose(16 * (cos(t) + sin(t)), 22.5), "a corner of the turned part reaches the next slot's half-pitch"
    assert turn_room(100., 32.) == 45., "no turn reaches a neighbour that far"
    from little_world.factory.controller import SLOTS
    x, y, turn = slot_room(SLOTS, 32.)
    assert (x, y) == (6.5, 19.) and 38.9 < turn < 39., "the destination tray's slots: 45 mm by 70 mm apart"
    assert slot_room(((0., 0.), (.05, 0.)), 30.)[1] == inf, "one row: no neighbour across it"


def test_cpk_and_its_interval_are_the_handbooks():
    values = [.1 * i for i in range(30)]              # mean 1.45, s 0.8803
    cpk, (low, high) = capability(values, 6.5)
    assert isclose(cpk, (6.5 - 1.45) / (3 * 0.880340), rel_tol=1e-5)
    w = 1.959964 * sqrt(1 / (9 * 30) + cpk ** 2 / (2 * 29))
    assert isclose(low, cpk - w, rel_tol=1e-5) and isclose(high, cpk + w, rel_tol=1e-5)
    assert capability(values[:24], 6.5)[1] is None, "below 25 values the approximation is not valid"
    assert capability([1., 1.], 2.) == (inf, None) and capability([3., 3.], 2.) == (0., None)
    with pytest.raises(ValueError):
        capability([1.], 2.)


def test_the_one_sided_clopper_pearson_bound():
    assert isclose(lower_bound(50, 50), .05 ** (1 / 50), rel_tol=1e-9), "all of n: alpha to the 1/n"
    assert lower_bound(0, 10) == 0.
    # 45 of 50: the binomial tail at the bound is 5 %
    from math import comb
    p = lower_bound(45, 50)
    assert isclose(sum(comb(50, i) * p ** i * (1 - p) ** (50 - i) for i in range(45, 51)), .05, rel_tol=1e-6)


def test_a_window_counts_what_landed_inside_the_worst_and_what_was_late():
    parts = [Placement(0, 3., -1., .2, 12.), Placement(1, 7., 0., 0., 13.9), Placement(2, -2., 18., -1., 12.5)]
    w = judge(parts, (6.5, 19.), 38.9, takt=13.)
    assert (w.n, w.inside, w.late) == (3, 2, 1) and isclose(w.worst, (4 + 18 * 18) ** .5)
    assert w.slowest == 13.9 and w.worst_turn == 1. and [a for a, *_ in w.cpk] == ['x', 'y', 'yaw']
    assert isclose(w.bias[0], 8 / 3) and not w.capable()
    assert line(w, (6.5, 19.)) == '2 of 3 placed within their room  /  worst 18.1 mm off (room 6.5 mm)  /  slowest part 13.9 s'
    many = [Placement(i, .5 * (-1) ** i, .1, 0., 12.) for i in range(30)]
    assert tightest(many, (5., 2., 1., .5)) == (.5, 30, 30, pytest.approx(.05 ** (1 / 30)))
    assert tightest(many, (.4,)) is None


def test_a_production_run_says_where_each_part_was_left_and_a_fed_part_off_centre_is_still_placed():
    pytest.importorskip('mujoco')
    from little_world.factory.controller import FactoryCycle
    from little_world.factory.scene import factory_scene, stock_name
    from little_world.physics.mujoco_backend import MujocoBackend
    b = MujocoBackend(); b.compile(factory_scene(stock=1), .002)
    try:
        cycle = FactoryCycle(b)
        fed = {0: (0., 0., 0.), 1: (.003, -.002, 10.)}       # the second part 3.6 mm off the centre, turned 10 deg
        cycle.feeder = fed.__getitem__
        parts = ['objects/' + stock_name(i) for i in range(2)]
        cycle.production(parts, 'Amber')
        for _ in range(int(40 / .002)):
            b.step(cycle.commands(.002))
            if cycle.state == 'failed' or (cycle.state == 'completed' and cycle.run['done'] == 2):
                break
        assert cycle.state == 'completed' and cycle.run['done'] == 2, cycle.message
        placed = cycle.run['placements']
        assert [p.part for p in placed] == [0, 1] and [p.seconds for p in placed] == cycle.run['times']
        assert cycle.placement is placed[-1]
        for p in placed:
            assert 1. < p.dx < 6.5 and -2.5 < p.dy < -.5, "out along the table, within its room, and short across it"
            assert abs(p.yaw) < 3., "the hand squares a part fed turned 10 deg, to within 2 (ADR 0057)"
    finally:
        b.close()
