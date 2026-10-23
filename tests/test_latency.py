"""Time passes while the program looks and moves (FR-028): the latencies of its camera and its servo
bus, from their sources, and what they do to a run.

A picture reaches the program a frame interval and the finder's time after it was exposed; a
command or a reading crosses a ROBOTIS Dynamixel bus - Protocol 2.0 packets at the X series'
default 57,600 bps, each servo answering after its 500 us return delay. `Lag` holds commands and
readings back step by step; `Late` shows the camera the world as it was; a sweep run takes a
latency, and with none it is the run it always was.
"""
import pytest

from little_world.control.latency import (BAUD, FINDER, Lag, Latency, RETURN_DELAY, sourced, sync_read,
                                          sync_write, wire)


def test_the_bus_takes_what_its_packets_take_at_the_e_manuals_defaults():
    assert (BAUD, RETURN_DELAY) == (57600, 500e-6)
    assert wire(576) == pytest.approx(.1), 'ten bits a byte'
    # A Sync Read of 4 bytes from two servos: a 16-byte instruction, then a 15-byte status packet
    # from each, each after its return delay (e-Manual, Protocol 2.0).
    assert sync_read(2, 4) == pytest.approx(wire(16 + 2 * 15) + 2 * RETURN_DELAY)
    # The kit's six servos: their goal positions written in 44 bytes, 7.6 ms; the registers a grasp
    # is felt by - Moving to Present Position, 14 bytes - read back in 170 bytes and six delays.
    assert sync_write(6, 4) == pytest.approx(44 * 10 / 57600)
    assert sync_read(6, 14) == pytest.approx(170 * 10 / 57600 + 6 * 500e-6)
    late = sourced()
    assert late.picture == pytest.approx(1 / 30 + FINDER) and late.command == pytest.approx(.00764, abs=1e-5)
    assert late.reading == pytest.approx(.0325, abs=1e-4)
    with pytest.raises(ValueError):
        sourced(frame_rate=0.)


def test_a_latency_is_a_time_on_each_path():
    assert Latency().zero and not Latency(command=.01).zero
    assert Latency.every(.3) == Latency(.3, .3, .3)
    assert Latency(.0333, .0076, .0325).steps(.002) == (17, 4, 16)
    for bad in (-.1, float('nan'), float('inf')):
        with pytest.raises(ValueError, match='finite time'):
            Latency(reading=bad)


def test_the_lag_holds_the_servos_commands_and_readings_back_and_drives_the_wheels_at_once():
    lag = Lag(Latency(command=.006, reading=.004), .002)        # 3 steps and 2
    sent, read = [], []
    for k in range(6):
        out = lag.command({'pose': {'arm': (k,)}, 'action': ('jaws', 1) if k == 1 else None, 'move': None,
                           'drive': (k, k), 'base': None})
        sent.append((out['pose'], out['action'], out['drive']))
        read.append(lag.reading(k))
    assert [p for p, _, _ in sent] == [None, None, None, {'arm': (0,)}, {'arm': (1,)}, {'arm': (2,)}]
    assert [a for _, a, _ in sent] == [None, None, None, None, ('jaws', 1), None]
    assert [d for _, _, d in sent] == [(k, k) for k in range(6)], 'the wheels are not on the bus'
    assert read == [0, 0, 0, 1, 2, 3], 'the first reading until one that old has come'


def test_a_late_camera_sees_the_cube_where_it_was():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import _hold, _rigs, design, eye
    from little_world.perception.eye import Late
    from little_world.physics.mujoco_backend import MujocoBackend
    bp, field, backend = design('mobile_manipulator'), FIELDS['fetch'], MujocoBackend()
    scene = field.scene(Entity('machine', bp))
    with World(backend, scene) as world:
        state = world.start()
        drive, control, _ = _rigs(backend, bp)
        for _ in range(50):
            state = _hold(world, drive, control, field, state)
        camera = eye(backend, field, scene, ideal=True)
        late = Late(camera, backend, 3)
        for _ in range(4):
            late.keep()
        planned, cube = (1.84, 0., .14), 'objects/fetch_cube'
        backend.shift(cube, (0., .05))
        now = backend.data.qpos.copy()
        late.keep()
        then = late(cube, planned, .25)
        assert then.centre[1] == pytest.approx(0., abs=.003), 'the picture is of three steps ago'
        assert (backend.data.qpos == now).all() and backend.sight is backend.data, 'the world is untouched'
        assert camera(cube, planned, .25).centre[1] == pytest.approx(.05, abs=.003)
        for _ in range(3):
            late.keep()
        assert late(cube, planned, .25).centre[1] == pytest.approx(.05, abs=.003)
        assert late.last is camera.last and late.place(cube, then.centre) in ('empty', 'there', 'hidden')


def made_up(latency, late_met, shove_met):
    from test_disturbance import made_up as shaped
    from dataclasses import replace
    result = shaped((('none', '', (33., 33., 34., 33.), None),
                     ('cube moved 5 cm sideways, 2 s later', 'moved', tuple(40. + (latency or Latency()).command if ok
                                                                             else None for ok in late_met), None),
                     ('shoved 6 N s at the table', 'a push', tuple(41. if ok else None for ok in shove_met), .08)))
    return replace(result, latency=latency)


def test_the_margin_is_read_against_the_same_set_ups_without_latency():
    from little_world.inventory import margin
    base = made_up(None, (True,) * 4, (True,) * 4)
    results = [('sourced', made_up(sourced(), (True,) * 4, (True,) * 4)),
               ('0.3 s', made_up(Latency.every(.3), (True,) * 4, (True,) * 4)),
               ('0.5 s', made_up(Latency.every(.5), (True, False, True, False), (True,) * 4))]
    table = margin.rows(base, results)
    assert dict(table[2][2])['cube moved 5 cm sideways, 2 s later'] == (2, 4, 2, 0, pytest.approx(.5))
    assert margin.margin(table) == ('0.3 s', '0.5 s')
    page = margin.markdown(base, results)
    assert '| Latency: pictures / commands / readings, ms | none | cube moved 5 cm sideways, 2 s later | shoved 6 N s at the table |' in page
    assert '| sourced: 139 / 7.6 / 33 | 4 of 4; +0.0 s | 4 of 4; +0.0 s | 4 of 4; +0.0 s |' in page
    assert '| 0.5 s: 500 / 500 / 500 | 4 of 4; +0.0 s | 2 of 4, 2 broken; +0.5 s | 4 of 4; +0.0 s |' in page
    assert 'Every set-up held at 0.3 s; at 0.5 s the latency broke some.' in page
    assert margin.parse('sourced, 0.2') == (('sourced', sourced()), ('0.2 s', Latency.every(.2)))
    with pytest.raises(ValueError, match="seconds or 'sourced'"):
        margin.parse('fast')


def test_a_sweep_records_its_latency_and_says_it(capsys):
    from dataclasses import replace
    from little_world.inventory.sweep import (disturbed_from_json, disturbed_markdown, from_json, main, markdown,
                                              to_json, Sweep)
    from little_world.fields.variation import Ranges
    result = made_up(sourced(), (True,) * 4, (True,) * 4)
    assert disturbed_from_json(to_json(result)).latency == sourced()
    assert ('its pictures showed the world as it was 139 ms before, its commands reached the servos 7.6 ms late and '
            'its readings of them came 33 ms late') in disturbed_markdown(result)
    assert 'Time passed' not in disturbed_markdown(replace(result, latency=None))
    plain = Sweep('fetch', 'arm on a cart', 'program', 60., None, Ranges(), result.groups[0][2], latency=Latency.every(.2))
    assert from_json(to_json(plain)).latency == Latency.every(.2)
    assert 'as it was 200 ms before' in markdown(plain)
    with pytest.raises(SystemExit):
        main(['fetch', '--latency', 'soon'])
    assert "--latency takes seconds, 0 or more, or 'sourced', not 'soon'" in capsys.readouterr().err


def test_a_bus_slower_than_the_grasp_check_leaves_a_held_cube_unfelt():
    """Every path half a second late: the jaws close on the cube, but the program's grasp check -
    0.5 s from when it asked them to close - is over before the hold has crossed the bus, and it
    takes the grasp to have missed. Pictures that late alone change nothing for a cube that stands
    still (the measured sweep, docs/sweeps)."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run
    late = run('fetch', design('mobile_manipulator'), latency=Latency.every(.5))
    assert late.felt and late.felt[0][1:] == (False, True), late.felt
    assert late.result('lifted').status == 'missed'
