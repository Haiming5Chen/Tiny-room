"""How gently a part is handled, beside whether the goals were met (ADR 0040, FR-020).

The goals say where the cube ended; a lab also asks how it got there - pressed how hard, by
what, leaning how far, dropped from how high. First the bookkeeping on made-up steps, then the
instrument checked against the cube's weight, then the case the jaws used to come down on the
cube against the one where they did not.
"""
from types import SimpleNamespace

import pytest

from little_world.inventory.handling import WINDOW, Handled, Watching, partner, summary, table


def test_what_touched_the_part_is_named_as_a_report_names_it():
    assert partner('machine/arm__gripper__finger_left_pad') == 'machine'
    assert partner('field/bin_wall_2') == partner('field/bin_base') == 'bin'
    assert partner('field/table') == 'table' and partner('objects/other_cube') == 'other_cube'


class Backend:
    def __init__(self):
        self.forces = ()

    def contact_forces(self, body):
        return self.forces


def state(z=.14, quaternion=(1., 0., 0., 0.)):
    return SimpleNamespace(bodies={'objects/cube': SimpleNamespace(pose=SimpleNamespace(position=(1.8, 0., z),
                                                                                         quaternion=quaternion))})


def test_the_largest_force_in_a_step_and_over_fifty_milliseconds_the_lean_and_the_fall():
    """Resting on the table at 0.16 N; squeezed at 0.4 N by two jaws from either side - which
    cancel in a sum, so each jaw's push is what counts - with one 2 N knock of one step; lifted,
    let go 6 cm above where it then rests, leaning 20 degrees."""
    backend, watch, dt = Backend(), Watching('objects/cube'), .002
    backend.forces = (('field/table', (0., 0., .16)),)
    for _ in range(50):
        watch.update(backend, state(), dt)
    squeeze = (('machine/pad_left', (.4, 0., 0.)), ('machine/pad_right', (-.4, 0., 0.)))
    for k in range(50):
        backend.forces = (('machine/pad_left', (2., 0., 0.)),) if k == 10 else squeeze
        watch.update(backend, state(z=.20), dt)
    backend.forces = ()
    from math import cos, radians, sin
    for _ in range(25):
        watch.update(backend, state(z=.026, quaternion=(cos(radians(10)), sin(radians(10)), 0., 0.)), dt)
    h = watch.result()
    assert h.of('peak', 'machine') == pytest.approx(2.) and h.of('peak', 'table') == pytest.approx(.16)
    # Averaged over 50 ms, the one-step knock is a twenty-fifth of itself on top of the grip.
    assert h.of('steady', 'machine') == pytest.approx(.4 + (2. - .4) * dt / WINDOW, rel=.02)
    assert h.of('steady', 'table') == pytest.approx(.16)
    assert h.tilt == pytest.approx(20.) and h.dropped == pytest.approx(.20 - .026)
    assert [k for k, _ in h.peak] == ['machine', 'table'] and h.of('peak', 'bin') == 0.
    untouched = Watching('objects/cube')
    untouched.update(Backend(), state(), dt)
    assert untouched.result().dropped is None and untouched.result().peak == ()


def test_runs_are_summed_up_as_a_report_shows_them():
    gentle = Handled('objects/cube', (('machine', .35), ('bin', 1.9)), (('machine', .18), ('bin', .56)), 13., .06)
    rough = Handled('objects/cube', (('machine', 4.7), ('table', 4.8)), (('machine', 4.6), ('table', 4.8)), 12.6, None)
    rows = {label: (mid, low, high) for label, mid, low, high in summary([gentle, rough, None])}
    assert rows['force from the machine, over 50 ms'] == pytest.approx((2.39, .18, 4.6))
    assert rows['force from the bin, in a step'] == pytest.approx((1.9, 1.9, 1.9))
    assert rows['fell when let go'] == pytest.approx((.06, .06, .06))
    lines = table(summary([gentle]))
    assert '| force from the machine, in a step | 0.35 N | 0.35 N | 0.35 N |' in lines
    assert '| leaned from how it stood | 13.0 deg | 13.0 deg | 13.0 deg |' in lines and '| fell when let go | 6.0 cm |' in lines[-1]


def test_a_cube_resting_on_the_table_weighs_what_it_weighs():
    """The instrument: the forces the table puts on the resting cube add up to its weight."""
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import design
    from little_world.physics.mujoco_backend import MujocoBackend
    backend = MujocoBackend()
    field = FIELDS['fetch']
    with World(backend, field.scene(Entity('machine', design('mobile_manipulator')))) as world:
        state = world.start()
        watch = Watching('objects/fetch_cube')
        for _ in range(100):
            state = world.step({})
            watch.update(backend, state, world.timestep)
        weight = backend.model.body('objects/fetch_cube').mass[0] * 9.81
        forces = backend.contact_forces('objects/fetch_cube')
        assert {name for name, _ in forces} == {'field/table'}
        assert sum(f[2] for _, f in forces) == pytest.approx(weight, rel=.01)
        assert watch.result().of('steady', 'table') == pytest.approx(weight, rel=.01)
        with pytest.raises(ValueError):
            backend.contact_forces('objects/nothing')


def test_jaws_brought_down_on_the_moved_cube_press_it_into_the_table():
    """ADR 0032's rough case: the cube moved 5 cm as the cart stopped, the program blind - a
    jaw comes down where the cube had been, on its edge, and presses it into the table at
    thirty times its weight; looking, the same move is fetched and the table only ever carries
    the cube. From the machine's side the two look alike - a jaw pressing, a jaw squeezing, some
    4 N each - so it is the table that tells them apart."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, run, solve
    moved = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways')
    bp = design('mobile_manipulator')
    blind = run('fetch', bp, program=solve('fetch', bp, look=False), disturbance=moved).handled[0]
    looking = run('fetch', bp, program=solve('fetch', bp), disturbance=moved).handled[0]
    assert blind.of('steady', 'table') > 25 * .159 and looking.of('steady', 'table') < .5
    assert blind.of('steady', 'machine') > 2. and looking.of('steady', 'machine') > 2.
    assert looking.of('peak', 'bin') > 0. and blind.of('peak', 'bin') == 0.
