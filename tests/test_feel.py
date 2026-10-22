"""A grasp the program feels (ADR 0048, FR-026): from what the gripper's servos report - where
each jaw is, where it was sent, how fast it moves and the current it draws - and not from the
simulator's contacts, which no real robot has."""
from math import radians

import pytest

from little_world.control import feel
from little_world.control.feel import Jaw, counts, holding


def test_the_registers_count_as_the_xh430_counts_them():
    """The kit jaw's 0.6 N m is the XH430-W350's 229 mA at its stall point's 2.6 N m an ampere:
    85 counts of 2.69 mA. A degree is 11 pulses of 4096 a turn; the Moving Threshold's 10
    counts of 0.229 rev/min are 0.24 rad/s."""
    assert feel.TORQUE_PER_AMP == pytest.approx(2.615, abs=.001)
    assert counts(.6, 0., 0., 0.).current == 85 and counts(-.6, 0., 0., 0.).current == -85
    assert counts(0., radians(1.), radians(2.), 0.) == Jaw(11, 23, 0, 0)
    assert feel.MOVING * feel.VELOCITY_UNIT == pytest.approx(.24, abs=.001)


def test_holding_is_both_jaws_still_short_of_their_goal_and_pushing():
    held = Jaw(position=200, goal=207, velocity=0, current=12)
    assert holding((held, held))
    assert not holding((held, Jaw(200, 207, 22, 12)))        # still closing
    assert not holding((held, Jaw(207, 207, 0, 0)))          # at its goal: closed on air
    assert not holding((held, Jaw(205, 207, 0, 1)))          # short of it, but not pushing
    assert not holding(())


def test_jaws_closing_on_nothing_feel_nothing():
    """The Fetch program's open and close, 0.6 s and 1 s, with nothing between the jaws: they
    reach where they were sent, stop, and draw no current to speak of - at no step do they
    feel a hold."""
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.control.tool_motion import ToolMotion
    from little_world.fields import FIELDS
    from little_world.inventory import sweep
    from little_world.physics.mujoco_backend import MujocoBackend
    bp = sweep.design('mobile_manipulator')
    field, backend = FIELDS['fetch'], MujocoBackend()
    with World(backend, field.scene(Entity('machine', bp))) as world:
        state = world.start()
        drive, control, base = sweep._rigs(backend, bp)
        jaws = ToolMotion(backend, bp, control).jaws
        spec = next(s for s in control.specs if set(s.actuators) == set(jaws))
        readings = []
        for k in range(round(2.4 / world.timestep)):
            t = k * world.timestep
            control.held = {spec.negative_key} if t < .6 else {spec.positive_key} if t < 1.6 else set()
            state = sweep._hold(world, drive, control, field, state)
            readings.append(feel.read(backend, control, jaws))
    assert not any(holding(r) for r in readings)
    assert all(abs(j.short) <= 1 and not j.moving and abs(j.current) < feel.FELT for j in readings[-1])


@pytest.mark.parametrize('payload', (0., .5))
def test_the_fetch_program_feels_the_cube_where_the_contacts_say_it_is_held(payload):
    """As designed and carrying 0.5 kg: at the grasp check the jaws felt a hold, and the
    simulator's contacts say there was one. Told by the contacts instead, the program passes
    its check 52 ms sooner - the contacts are there at the touch, the servos feel the hold
    once the jaws have stopped - and meets every goal as well."""
    pytest.importorskip('mujoco')
    from little_world.fields.variation import Variation, payload_site
    from little_world.inventory.sweep import design, run, solve
    bp = design('mobile_manipulator')
    program, site, setup = solve('fetch', bp), payload_site(bp), Variation(payload=payload)
    felt = run('fetch', bp, setup, program, site)
    told = run('fetch', bp, setup, program, site, feel=False)
    for r in (felt, told):
        assert all(x.status in ('met', 'kept') for x in r.results), r.message
        assert len(r.felt) == 1 and r.felt[0][1] and r.felt[0][2]
    assert 0. < felt.felt[0][0] - told.felt[0][0] < .1


def test_jaws_closing_where_the_cube_was_taken_from_feel_nothing_held():
    """The cube taken 15 cm to the side as the jaws begin to close round it: they close on
    nothing, feel nothing, and the program looks again (ADR 0033), as the contacts made it do;
    it then fetches the cube where it now stands."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import Disturbance
    from little_world.inventory.sweep import design, run
    taken = Disturbance('cube taken from between the jaws', 'move', after='reached', still=.2, delay=4.,
                        part='objects/fetch_cube', offset=(0., .15))
    felt = run('fetch', design('mobile_manipulator'), disturbance=taken)
    assert felt.felt[0][1:] == (False, False) and felt.regrasped == 1
    assert not any(f != h for _, f, h in felt.felt), felt.felt
    assert all(x.status in ('met', 'kept') for x in felt.results), felt.message


def test_a_report_counts_what_the_jaws_felt_against_what_the_contacts_showed():
    from little_world.fields.variation import Ranges, Variation
    from little_world.inventory.sweep import Run, Sweep, from_json, markdown, to_json
    runs = (Run(Variation('as designed'), felt=((19.1, True, True),)),
            Run(Variation('repeat 1'), felt=((19.2, False, False), (25.3, True, True))))
    result = Sweep('fetch', 'arm on a cart', 'program', 60., None, Ranges(), runs)
    assert ('at 3 grasp checks in 2 runs: it felt a hold where the contacts showed one twice, and none where '
            'they showed none once; it was never wrong.') in markdown(result)
    assert from_json(to_json(result)) == result
