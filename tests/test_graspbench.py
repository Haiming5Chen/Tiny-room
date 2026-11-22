"""The grasp bench (FR-043, ADR 0077): its grid, its objects, how it judges a run, its report -
and, through MuJoCo, the arm lab's gripper on the lying block and the cube."""
from math import cos, radians, sin
from pathlib import Path

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


def test_the_arm_labs_record_is_its_report_and_a_runs_lines_fill_the_table():
    # The Inventory's Grasp bench tab (ADR 0077): the arm lab's record, as designed, is what its report says;
    # a run's progress lines fill the table as they come in, and its outcomes are read back.
    import json
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    name, by_turn, report, note = gb.recorded(arm_lab_blueprint())
    assert name == 'arm_lab' and gb.recorded(mobile_manipulator_blueprint()) is None
    page = (Path(__file__).resolve().parents[1] / report).read_text(encoding='utf-8')
    for obj, row in by_turn.items():
        cells = ' | '.join('{} of {}'.format(*row[turn]) for turn in gb.TURNS)
        assert f'| {obj} | {cells} |' in page, obj
    assert 'It felt 97 of the 97 held runs held' in page and 'felt all 97 held' in note
    lines = ['1/180 cube (-0.02, -0.02, 0.0): held', '2/180 cube (-0.02, -0.02, 30.0): not lifted', 'Traceback',
             '3/180 sphere (0.0, 0.0, 0.0): held']
    found = [p for p in map(gb.progress, lines) if p]
    assert found == [('cube', (-.02, -.02, 0.), True), ('cube', (-.02, -.02, 30.), False)]
    assert gb.counts(found) == {'cube': {0.: (1, 1), 30.: (0, 1)}}
    outcomes = _outcomes()
    written = json.dumps([[o.name, list(o.pose), o.lifted, o.carried, o.slip, o.message, o.felt, o.between, o.skew]
                          for o in outcomes])
    assert gb.from_json(written) == outcomes
    assert gb.summary(outcomes) == ["The jaws close 74, 44, 16 deg from the object's length at the 0, 30, 90 deg turns "
                                    "(the median over the places).", 'The grasp check felt 3 of the 4 held runs held.']


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
    assert across.grip < .5 and along.grip == pytest.approx(1.)     # by its ends it used all its friction


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


def test_the_bench_with_its_camera_looks_for_the_object_and_aims_its_poses():
    # FR-043's second mode: a depth camera beyond the bench, as the Fetch's at its table, and a program
    # that looks for the object where it is planned and reaches where it was seen (ADR 0032, 0025).
    from little_world.inventory import sweep
    field = gb.bench_field('cube', (0., 0., 0.), camera=True)
    assert field.id == 'grasp_bench_camera' and field.camera == ('bench_camera', 'realsense_d435')
    names = {c.id for c in next(e for e in field.build() if e.id == 'field').blueprint.components}
    assert {'camera_post', 'camera_bracket', 'camera_head', 'bench_camera'} <= names
    program, _ = gb.program(field, sweep.design('arm_lab'), top=gb.height('cube') / 2, look=True)
    look = next(b for b in program.blocks if b.kind == 'look')
    assert look.target == 'objects/part' and look.secondary == gb.SEARCH
    assert look.point == pytest.approx((gb.CENTRE[0], gb.CENTRE[1], gb.TOP + .0125 + .0005), abs=.002)
    assert all(b.point for b in program.blocks if b.kind == 'pose'), "every pose aimed at its point"
    known, _ = gb.program(gb.bench_field('cube', (0., 0., 0.)), sweep.design('arm_lab'), top=gb.height('cube') / 2)
    assert not any(b.kind == 'look' or b.point for b in known.blocks), "known pose: no look, no aim"
    assert gb.run('arm_lab', 'cylinder', (0., 0., 0.), look=True).reason == \
        'not looked for: the camera finds boxes (ADR 0032)'


def test_a_cube_off_the_benchs_middle_is_found_by_the_camera_and_picked():
    # Solved for the bench's middle, the program finds the cube 2.8 cm away with the camera, reaches it
    # there and carries it to the place 20 cm from the middle (ADR 0077).
    found = gb.run('arm_lab', 'cube', (.02, .02, 30.), look=True)
    assert found.held and found.felt and found.message == 'Completed'
    assert found.carried == pytest.approx(.195, abs=.005)


def test_the_report_says_how_close_each_grip_came_to_slipping():
    # FR-036's friction in use, while the object was in the air: the held runs' median and most, and
    # the others' each (ADR 0077).
    o = gb.Outcome
    found = (o('cube', (0., 0., 0.), .097, .195, .0008, 'Completed', True, True, 74.5, .55),
             o('cube', (.02, 0., 0.), .097, .195, .0006, 'Completed', True, True, 74., .45),
             o('block lying', (0., 0., 90.), -.187, .22, .0003, 'Completed', True, True, 15.5, 1.),
             o('block lying', (0., 0., 0.), .095, .194, .0015, 'Completed', True, True, 74.5, .41),
             o('plate', (0., 0., 0.), message='the arm cannot close its jaws on it without striking the bench'))
    assert gb.grips(found) == {'cube': ([.55, .45], []), 'block lying': ([.41], [1.])}
    text = gb.markdown(found, 'arm_lab')
    assert '## How close to slipping' in text
    assert '| cube | 50 % | 55 % | - |' in text and '| block lying | 41 % | 41 % | 100 % |' in text
    assert '| plate |' not in text.split('## How close to slipping')[1].split('\n## ')[0], "never in the air"
