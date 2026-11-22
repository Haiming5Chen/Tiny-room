"""The grasp bench (FR-043, ADR 0077): its grid, its objects, how it judges a run, its report -
and, through MuJoCo, the arm lab's gripper on the lying block and the cube."""
from math import cos, radians, sin

import pytest

from little_world.inventory import graspbench as gb


def test_the_grid_is_three_by_three_places_at_four_turns():
    poses = gb.poses()
    assert len(poses) == 36 == len(set(poses))
    assert {p[:2] for p in poses} == {(dx, dy) for dx in gb.SHIFTS for dy in gb.SHIFTS}
    assert {p[2] for p in poses} == set(gb.TURNS) == {0., 30., 60., 90.}
    assert poses[:4] == tuple((-.02, -.02, t) for t in gb.TURNS)     # places first, each at every turn


def test_each_object_stands_as_tall_as_its_shape_says():
    assert [gb.height(n) for n in gb.OBJECTS] == [.025, .040, .025, .040, .006]
    assert gb.OBJECTS['block'][1] == (.025, .025, .040)               # the kit cube of the arm lab and the Fetch
    assert sorted(gb.OBJECTS['block lying'][1]) == sorted(gb.OBJECTS['block'][1])


def test_held_is_lifted_carried_and_still_in_the_jaws():
    held = gb.Outcome('cube', (0., 0., 0.), lifted=.097, carried=.195, slip=.0008, message='Completed', skew=74.)
    assert held.held and held.reason == ''
    assert not gb.Outcome('cube', (0., 0., 0.), lifted=.079, carried=.195, slip=.0008, skew=74.).held
    assert not gb.Outcome('cube', (0., 0., 0.), lifted=.097, carried=.179, slip=.0008, skew=74.).held
    slipped = gb.Outcome('cube', (0., 0., 0.), lifted=.097, carried=.195, slip=.002, skew=74.)
    assert not slipped.held and slipped.reason == 'slipped in the jaws'
    dropped = gb.Outcome('block lying', (0., 0., 90.), lifted=-.187, carried=.227, slip=.0001, message='Completed', skew=16.)
    assert dropped.reason == 'not lifted'
    assert gb.Outcome('cube', (0., 0., 0.), lifted=.05, carried=.195, slip=.0001, skew=74.).reason == 'slid down in the jaws'
    assert gb.Outcome('cube', (0., 0., 0.), lifted=.097, carried=.10, slip=.0001, skew=74.).reason == 'not carried'
    # a run the arm could not reach, or that could not be set up, is a failure that says why
    missing = gb.Outcome('plate', (.02, .02, 0.), message='the arm cannot reach the at point: 1.0 cm short')
    assert not missing.held and missing.reason == 'the arm cannot reach the at point: 1.0 cm short'
    stopped = gb.Outcome('cube', (0., 0., 0.), message='Timed out: pose did not settle')
    assert stopped.reason == 'Timed out: pose did not settle'        # it never came to its grasp


def test_the_jaws_angle_is_folded_between_along_and_across():
    assert gb.skew((1., 0.), 0.) == pytest.approx(0.)
    assert gb.skew((0., 1.), 0.) == pytest.approx(90.)
    assert gb.skew((1., 1.), 0.) == pytest.approx(45.)
    assert gb.skew((-1., 0.), 0.) == pytest.approx(0.)                 # a line has no direction
    assert gb.skew((1., 0.), 170.) == pytest.approx(10.)
    closing = (cos(radians(74.5)), sin(radians(74.5)))                  # the arm lab's at the grid's middle
    assert [round(gb.skew(closing, t), 1) for t in gb.TURNS] == [74.5, 44.5, 14.5, 15.5]


def _outcomes():
    o = gb.Outcome
    return (o('cube', (0., 0., 0.), .097, .195, .0008, 'Completed', True, True, 74.5),
            o('cube', (.02, 0., 0.), .097, .195, .0006, 'Completed', True, True, 74.),
            o('cube', (0., 0., 30.), .098, .199, .0001, 'Completed', False, True, 44.5),
            o('block lying', (0., 0., 90.), -.187, .227, .0001, 'Completed', True, True, 15.5),
            o('block lying', (0., 0., 0.), .096, .194, .0011, 'Completed', True, True, 74.5),
            o('plate', (0., 0., 0.), 0., 0., 0., 'Completed', False, False, 74.5),
            o('plate', (.02, .02, 90.), message='the arm cannot reach the at point: 0.4 cm short'))


def test_the_report_counts_by_object_and_turn_with_an_exact_interval():
    found = _outcomes()
    by_turn, total = gb.table(found)
    assert total == {'cube': (3, 3), 'block lying': (1, 2), 'plate': (0, 2)}
    assert by_turn['block lying'] == {90.: (0, 1), 0.: (1, 1)}
    text = gb.markdown(found, 'arm_lab')
    assert text.startswith('# Grasp bench: arm_lab\n')
    assert '| cube | 2 of 2 | 1 of 1 | 0 of 0 | 0 of 0 | 3 of 3 | 29 to 100 % |' in text
    assert '| plate | 0 of 1 | 0 of 0 | 0 of 0 | 0 of 1 | 0 of 2 | 0 to 84 % |' in text
    assert '- block lying: not lifted (1)' in text
    assert '- plate: not lifted (1); the arm cannot reach the at point: 0.4 cm short (1)' in text
    assert 'At the 0, 30, 90 deg turns the object\'s x axis lay 74, 44, 16 deg from the line the jaws close along' in text
    assert 'Held runs slipped 0.10 to 1.10 mm in their last 2 s.' in text


def test_the_report_says_what_the_grasp_check_felt_against_the_outcome():
    found = _outcomes()
    assert gb.check(found) == ((3, 4), (1, 2))          # felt 3 of 4 held, 1 of 2 not held; one never checked
    text = gb.markdown(found, 'arm_lab')
    assert '| cube | 2 | 1 | 0 | 0 |' in text
    assert '| block lying | 1 | 0 | 1 | 0 |' in text
    assert '| plate | 0 | 0 | 0 | 1 |' in text
    assert 'It felt 3 of the 4 held runs held, and 1 of the 2 others.' in text
    assert gb.jaw_angles(found) == {0.: 74.5, 30.: 44.5, 90.: 15.5}


def test_the_bench_field_sets_the_object_where_the_grid_says():
    field = gb.bench_field('block lying', (.02, -.02, 30.))
    assert field.id == 'grasp_bench' and [g.target for g in field.goals] == ['objects/part']
    entities = {e.id: e for e in field.build()}
    part = entities['objects'].blueprint.components[0]
    x, y, z = part.transform.position
    assert (x, y) == pytest.approx((gb.CENTRE[0] + .02, gb.CENTRE[1] - .02))
    assert z == pytest.approx(gb.TOP + .0125 + .0005)                   # on the bench, half a millimetre up
    assert part.transform.quaternion == pytest.approx((cos(radians(15.)), 0., 0., sin(radians(15.))))
    assert part.geometry.size == (.040, .025, .025) and part.dynamic
    bench = next(b for b in entities['field'].blueprint.components if b.id == 'bench')
    assert bench.transform.position[2] * 2 == pytest.approx(gb.TOP)
    from little_world.fields import find_field
    assert find_field('grasp_bench') is field, "the window finds the last one made by its id"
    with pytest.raises(ValueError, match='no bench object called'):
        gb.bench_field('sphere', (0., 0., 0.))


def test_the_lying_block_is_held_across_the_jaws_and_falls_along_them():
    # OPEN LW-034 on the bench: the arm lab's jaws, which have no wrist to turn them, close 74 deg
    # from the block's length at turn 0 - across it, on its 25 mm sides - and 16 deg from it at
    # turn 90, on its ends: there it is felt held, and falls as it is carried.
    across = gb.run('arm_lab', 'block lying', (0., 0., 0.))
    along = gb.run('arm_lab', 'block lying', (0., 0., 90.))
    assert across.skew == pytest.approx(74.5, abs=1.) and along.skew == pytest.approx(15.5, abs=1.)
    assert across.held and across.slip < .0018                     # it creeps: 1.6 mm in the hold's 2 s
    assert not along.held and along.felt and along.lifted < -.1      # off the bench, on the floor


def test_a_cube_turned_against_the_jaws_is_held_and_felt_held(monkeypatch):
    # ADR 0078 (OPEN LW-056): the template closes for 1 s, squeezes 0.6 deg more, then checks. Turned
    # 30 deg (its faces 44 deg from the jaws), the cube is turned square in them before the check; at
    # rest each jaw stops 6 pulses short pushing with 10 counts of current, over the 6 the feel needs
    # (ADR 0048) - checked straight after the 1 s close it pushed with 4 and the check felt nothing.
    from little_world.control import feel
    read, last = feel.read, {}

    def kept(*args, **kwargs):
        last['jaws'] = read(*args, **kwargs)
        return last['jaws']
    monkeypatch.setattr(feel, 'read', kept)
    turned = gb.run('arm_lab', 'cube', (0., 0., 30.))
    assert turned.held and turned.felt and turned.between
    jaws = last['jaws']                                             # in the hold, resting on the cube
    assert feel.holding(jaws) and min(j.current for j in jaws) >= 8 and min(j.short for j in jaws) >= 4, jaws


def test_the_plate_is_out_of_the_tall_pads_reach():
    # The pads stand 35 mm tall about the tool point; kept 5 mm over the bench they cannot close
    # on a 6 mm plate lying flat, and the bench says so rather than run.
    plate = gb.run('arm_lab', 'plate', (0., 0., 0.))
    assert not plate.held and plate.felt is None and plate.lifted == 0.
    assert plate.reason == 'the arm cannot close its jaws on it without striking the bench'
