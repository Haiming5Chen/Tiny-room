"""Contracts for the physics check: a contact gives back no more energy than it took (FR-040).

A contact is a spring and a damper. While two bodies touch, the work it does on them is what it
gives back less what it took, so from the moment they meet it can only be negative - unless the
engine made energy. First the bookkeeping on made-up steps, then the instrument against the bodies'
own energy, its positive and negative controls, that reading it changes nothing, and what it
found on the Curb run.
"""
from math import cos, pi, sin

import pytest

from little_world.inventory.artifacts import GIVE, Artifact, Checked, Watch, lines


class Backend:
    """Made-up steps: each `rows` is one step's (body, body, joules, metres sunk in)."""
    def __init__(self, masses):
        self.masses, self.rows = masses, ()

    def contact_work(self):
        return self.rows

    def moving_mass(self, body):
        return self.masses.get(body)


def test_a_touch_that_gives_back_more_than_it_took_is_flagged_and_one_that_gives_back_less_is_not():
    """A 16 g cube on a fixed table: pressed in, the contact takes 0.5 mJ and gives back 0.4 - it
    took more than it gave, as a spring and a damper do. They part; when they touch again the
    contact gives 0.6 mJ at once, more than lifting the cube GIVE takes: flagged, with when it began,
    when it gave the most and how deep it sank."""
    cube, table = 'objects/cube', 'field/table'
    allowed = .016 * 9.81 * GIVE
    backend, watch = Backend({cube: .016, table: None}), Watch()
    for t, rows in ((.002, ((table, cube, -.0005, .0004),)), (.004, ((table, cube, .0004, .0001),)), (.006, ()),
                    (.008, ((table, cube, .0006, .005),)), (.010, ((table, cube, -.0001, .001),)), (.012, ())):
        backend.rows = rows
        watch.update(backend, t)
    c = watch.result()
    assert c.touches == 2 and c.pairs == 1 and not c.clean
    (a,) = c.flagged
    assert a.bodies == (table, cube) and (a.began, a.at) == (.008, .008) and a.deepest == .005
    assert a.gave == pytest.approx(.0006) and a.allowed == pytest.approx(allowed) and a.lighter == 'the cube'
    assert a.lifted == pytest.approx(.0006 / (.016 * 9.81))
    assert c.worst == pytest.approx(.0006 / allowed) and c.deepest == ((table, cube), .005)
    assert c.line().startswith('Physics check: energy from nowhere - the contact between the table and the cube gave back 0.60 mJ')
    assert c.brief() == ('energy from nowhere at 0.0 s: 0.6 mJ', 'table / cube')
    quiet = Watch()
    backend.rows = ((table, cube, -.0005, .0004),)
    quiet.update(backend, .002)
    assert quiet.result().clean and quiet.result().brief() == ('physics check: nothing from nowhere',)
    assert Watch().result().brief() == () and Watch().result().line() == 'Physics check: nothing touched'


def test_a_touch_still_going_is_judged_as_it_stands_and_judged_again_when_it_ends():
    cube, table = 'objects/cube', 'field/table'
    backend, watch = Backend({cube: .016}), Watch()
    backend.rows = ((table, cube, .001, .002),)
    watch.update(backend, .1)
    assert len(watch.result().flagged) == 1 and len(watch.result().flagged) == 1, 'asking twice changes nothing'
    backend.rows = ()
    watch.update(backend, .2)
    assert len(watch.result().flagged) == 1 and not watch.live
    machine = Watch()
    backend.masses = {'machine/wheel': 1.7, 'field/curb': None}
    backend.rows = (('field/curb', 'machine/wheel', .05, .001),)
    machine.update(backend, 1.)
    assert machine.result().flagged[0].lighter == 'the machine', 'what a push on a wheel lifts is the whole machine'


def test_a_sweep_report_says_what_the_check_found_over_its_runs():
    clean = Checked(500, 40, .03)
    curb = Artifact(('field/curb_10mm', 'machine/swivel_caster_2_wheel'), 3.01, 7.74, .0782, .0171, .0011, 'the machine')
    flagged = Checked(1208, 98, 4.6, (curb,), (curb.bodies, .0011))
    assert lines([clean, clean]) == ['', 'Physics check (FR-040): in 2 of 2 runs no contact gave back more energy than it took - '
                                         f'the most any came to was 3% of lifting the lighter body {1000 * GIVE:.0f} mm.']
    said = lines([clean, flagged, None])
    assert said[1].startswith('Physics check (FR-040): in 1 of 2 runs a contact gave back more energy than it took')
    assert 'curb 10mm' in said[2] and "machine's swivel caster 2 wheel" in said[2] and '78.20 mJ' in said[2]
    assert lines([]) == lines([None]) == []


pytest.importorskip('mujoco')


def slab_and_block(lift=0., seconds=1.):
    """A 5 cm block over a fixed slab, its bottom `lift` metres above the slab's top (below it when
    negative), let go: (the block's mass, its energy change, the check, the slab's net work on it)."""
    from little_world import World
    from little_world.components import Transform, box
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.physics.mujoco_backend import MujocoBackend
    entities = field_entities([fixed('slab', (.6, .6, .04), 'slab', (0., 0., .3))],
                              [box('block', (.05, .05, .05), 'cube', dynamic=True, transform=Transform((0., 0., .345 + lift)))])
    backend, watch, net = MujocoBackend(), Watch(), 0.
    with World(backend, Scene(entities)) as world:
        state = world.start()
        mass = backend.moving_mass('objects/block')
        z0 = state.bodies['objects/block'].pose.position[2]
        for _ in range(round(seconds / world.timestep)):
            state = world.step({})
            watch.update(backend, state.time)
            net += sum(w for _, _, w, _ in backend.contact_work())
        body = state.bodies['objects/block']
        energy = mass * 9.81 * (body.pose.position[2] - z0) + .5 * mass * sum(v * v for v in body.linear_velocity)
    return mass, energy, watch.result(), net


def test_a_block_dropped_onto_a_slab_gives_it_all_it_fell_and_is_given_none_back():
    """The negative control. Dropped 5 cm, the block comes to rest on the slab: the slab's contact
    took the 40 mJ it fell - the block's own energy change, to 1 % - and gave none of it back."""
    mass, energy, check, net = slab_and_block(lift=.05, seconds=1.5)
    assert net == pytest.approx(energy, rel=.01) and energy == pytest.approx(-mass * 9.81 * .05, rel=.01)
    assert check.clean and check.worst == 0. and check.touches == 1


def test_a_block_started_inside_a_slab_is_pushed_out_with_energy_from_nowhere_and_flagged():
    """The positive control. Started 5 mm inside the slab, the block is pushed up out of it with
    nothing having pushed it in: the contact gives it as much as lifting it 5 mm takes, and the
    check says so. Started 0.5 mm in - under GIVE - it is not flagged."""
    mass, energy, check, net = slab_and_block(lift=-.005)
    (a,) = check.flagged
    assert a.lifted == pytest.approx(.005, abs=.0002) and net == pytest.approx(energy, rel=.01)
    assert a.bodies == ('field/slab', 'objects/block') and a.deepest == pytest.approx(.005, abs=1e-4)
    _, _, shallow, _ = slab_and_block(lift=-.0005)
    assert shallow.clean and .4 < shallow.worst * GIVE * 1000 < .5


def test_two_loose_boxes_started_one_inside_the_other_are_flagged():
    """A positive control between two bodies that both move: a box set 3 mm into the box under it,
    on a slab - the pair's contact gives them energy nothing put in, as much as lifting the upper
    box the 3 mm it was set in. Weighed against the lighter of the two, the 33 g lower box."""
    from little_world import World
    from little_world.components import Transform, box
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.physics.mujoco_backend import MujocoBackend
    entities = field_entities([fixed('slab', (.6, .6, .04), 'slab', (0., 0., .3))],
                              [box('under', (.08, .08, .04), 'crate', dynamic=True, transform=Transform((0., 0., .34))),
                               box('over', (.05, .05, .05), 'cube', dynamic=True, transform=Transform((0., 0., .382)))])
    backend, watch = MujocoBackend(), Watch()
    with World(backend, Scene(entities)) as world:
        state = world.start()
        for _ in range(500):
            state = world.step({})
            watch.update(backend, state.time)
    (a,) = watch.result().flagged
    assert a.bodies == ('objects/under', 'objects/over') and a.lighter == 'the under'
    assert a.gave == pytest.approx(.08125 * 9.81 * .003, rel=.05), 'as much as lifting the 81 g box the 3 mm it was set in'


def test_reading_the_contacts_work_changes_nothing_in_a_run():
    """The check reads the solver's forces and the step's speeds: the Curb run stepped with every
    step's contact work read is the same run, to the last bit."""
    import numpy as np
    from little_world import Entity, World
    from little_world.control.mujoco_drive import MujocoDrive
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import design
    from little_world.physics.mujoco_backend import MujocoBackend
    bp = design('mobile_platform')
    ends = []
    for read in (False, True):
        backend = MujocoBackend()
        with World(backend, FIELDS['curbs'].scene(Entity('machine', bp))) as world:
            world.start()
            drive = MujocoDrive(backend, bp)
            for _ in range(1500):
                world.step(drive.step_commands((5., 5.), world.timestep))
                if read:
                    backend.contact_work()
            ends.append((backend.data.qpos.copy(), backend.data.qvel.copy()))
    assert np.array_equal(ends[0][0], ends[1][0]) and np.array_equal(ends[0][1], ends[1][1])


def test_on_the_curb_run_the_casters_contact_with_the_curb_gives_the_cart_energy_it_never_took():
    """What the check found (ADR 0074, OPEN LW-047). Driven at the 10 mm curb, the kit cart pushes a
    swivel caster's wheel - a cylinder - against the curb's edge, one contact point between them
    (multiccd off, ADR 0027): from 3 s to 7.7 s that contact gives the cart 78 mJ more than it took,
    as much as lifting the 1.74 kg cart 4.6 mm, before it climbs over at 10.4 s. Nothing else in the
    run is flagged."""
    from little_world.inventory.sweep import design, run
    r = run('curbs', design('mobile_platform'))
    (a,) = r.physics.flagged
    assert a.bodies == ('field/curb_10mm', 'machine/swivel_caster_2_wheel') and a.lighter == 'the machine'
    assert a.gave == pytest.approx(.078, abs=.01) and a.at == pytest.approx(7.7, abs=.3)
    assert r.result('curb_10').status == 'met'
