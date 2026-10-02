"""Contracts for axle losses: rolling resistance and gearmotor friction (ADR 0011).

The defect: every wheel hinge carried a viscous damping of 0.01 N m s/rad, the only
loss in the drivetrain. At 1.75 m/s that is 0.875 N m on a 20 mm caster wheel - forty
times what its contact can transmit, so the caster skidded instead of rolling - and it
set the mobile platform's top speed and its 0.45 g coast-down, not any motor or tyre.
"""
from dataclasses import replace
from math import pi
import pytest

from little_world.core.component import Hinge, Motor
from little_world.core.motor_profile import MotorProfile
from little_world.assets.real_motors import KGCM, KIT_GEARMOTOR, POLOLU_37D, PROFILES
from little_world.materials import rolling


# -- data ----------------------------------------------------------------------------

def test_pololu_profiles_match_the_datasheet_table():
    table = {"6.3": (1600, 3.0), "10": (1000, 4.9), "19": (530, 8.5), "30": (330, 14.),
             "50": (200, 21.), "70": (150, 27.), "100": (100, 34.), "131": (76, 45.),
             "150": (67, 49.)}
    for ratio, (rpm, kgcm) in table.items():
        p = PROFILES[f"Pololu 37D {ratio}:1 / 12 V"]
        assert p.no_load_rpm == rpm and abs(p.stall_torque - kgcm * KGCM) < 1e-4
        assert (p.no_load_current, p.stall_current, p.voltage) == (.2, 5.5, 12.)
        assert p.envelope == "dc_friction_v1" and p.source == POLOLU_37D
    assert PROFILES[KIT_GEARMOTOR].no_load_rpm == 330


def test_friction_comes_from_the_no_load_current_and_endpoints_still_hold():
    p = PROFILES[KIT_GEARMOTOR]
    assert abs(p.friction_torque - p.stall_torque * .2 / 5.3) < 1e-12   # 0.0518 N m
    free = p.no_load_rpm * 2 * pi / 60
    # Net output = motor torque - friction: exactly the datasheet at both ends.
    assert abs(p.constrain(99, 0., 99) - p.friction_torque - p.stall_torque) < 1e-12
    assert abs(p.constrain(99, free, 99) - p.friction_torque) < 1e-12
    assert p.constrain(99, 2 * free, 99) == 0.
    assert p.constrain(-.3, free, .5) == -.3, "braking stays capped, not enveloped"


def test_old_profiles_and_invalid_currents():
    robotis = PROFILES["XH430-W210 / 12 V"]
    assert robotis.friction_torque == 0. and robotis.constrain(9, 0., 9) == robotis.stall_torque
    with pytest.raises(ValueError):
        MotorProfile("m", 12., 1., 100., "src", "2026-01-01", "dc_friction_v1", 1., .5)
    with pytest.raises(ValueError):
        MotorProfile("m", 12., 1., 100., "src", "2026-01-01", no_load_current=.1, stall_current=2.)
    from little_world.core.blueprint import Blueprint
    from little_world.robots.two_wheel import two_wheel_blueprint
    bp = two_wheel_blueprint()
    bp = replace(bp, components=tuple(
        replace(c, profile=PROFILES[KIT_GEARMOTOR], max_torque=.5) if isinstance(c, Motor) else c
        for c in bp.components))
    assert Blueprint.from_json(bp.to_json()) == bp


def test_rolling_table_is_in_metres_and_labelled():
    assert abs(rolling.lever_arm("rubber") - .047 * .0254) < 1e-12
    assert abs(rolling.lever_arm("steel") - .019 * .0254) < 1e-12
    assert rolling.lever_arm("wood") == 0.0 and rolling.lever_arm(None) == 0.0
    for loss in rolling.ROLLING.values():
        assert 0 < loss.lever_arm < .01 and loss.confidence in ("high", "medium", "low")
        assert loss.basis != "analogue" or loss.confidence == "low"


def test_kit_axles_lose_their_viscous_damping_and_the_gearmotor_gets_its_datasheet():
    from little_world.assets.catalog import BY_ID
    motor = BY_ID["gearmotor_37"].blueprint()
    shaft = next(c for c in motor.components if isinstance(c, Hinge))
    drive = next(c for c in motor.components if isinstance(c, Motor))
    assert shaft.damping == 0. and drive.profile == PROFILES[KIT_GEARMOTOR]
    caster = BY_ID["swivel_caster"].blueprint()
    joints = {c.id: c for c in caster.components if isinstance(c, Hinge)}
    assert joints["wheel_joint"].damping == 0.
    assert joints["swivel_joint"].damping == .01, "a swivel is not an axle"


def test_passive_wheels_mount_without_damping_and_ideal_drives_keep_theirs():
    from little_world.construction.editor import AssemblyEditor, starter_blueprint
    e = AssemblyEditor(starter_blueprint())
    base = e.blueprint.components[0].id
    for part, mount in (("wheel_small", "Left"), ("drive_right", "Right")):
        e.select(base)
        e.add_catalog(part, mount)
    hinges = {c.id: c for c in e.blueprint.components if isinstance(c, Hinge)}
    powered = {m.joint for m in e.blueprint.components if isinstance(m, Motor)}
    passive = [h for i, h in hinges.items() if i not in powered]
    ideal = [h for i, h in hinges.items() if i in powered]
    assert passive and all(h.damping == 0. for h in passive)
    assert ideal and all(h.damping == .01 for h in ideal), \
        "an ideal torque motor has no speed limit but its damping"


# -- the adapter ------------------------------------------------------------------------

mujoco = pytest.importorskip("mujoco")
from little_world import Blueprint, Entity, World  # noqa: E402
from little_world.components import box, wheel, Transform  # noqa: E402
from little_world.core.scene import Scene  # noqa: E402
from little_world.materials import METAL, RUBBER, SKID  # noqa: E402
from little_world.physics.mujoco_backend import (  # noqa: E402
    DRY_FRICTION_SOLIMP, MujocoBackend, dry_friction_solref)
from little_world.scenes.room import room_entity  # noqa: E402

AXLE = (.5 ** .5, -.5 ** .5, 0, 0)


def cart(radius=.05, wheel_material="rubber", mass_box=(.30, .20, .04)):
    """A box on four passive wheels: nothing but rolling and bearing losses."""
    parts = [box("chassis", mass_box, "metal", dynamic=True, transform=Transform((0, 0, radius + .03)))]
    for i, (x, y) in enumerate(((.12, .13), (.12, -.13), (-.12, .13), (-.12, -.13))):
        parts.append(wheel(f"w{i}", radius, .03, wheel_material, parent="chassis",
                           transform=Transform((x, y, -.03), AXLE)))
        parts.append(Hinge(f"h{i}", f"w{i}", damping=0.))
    return Blueprint(tuple(parts), (METAL, RUBBER, SKID))


def _normal(backend, dof_body):
    m, d = backend.model, backend.data
    total, f6 = 0., __import__("numpy").zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        if dof_body in (m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]):
            mujoco.mj_contactForce(m, d, i, f6)
            total += f6[0]
    return total


def test_rolling_resistance_is_the_lever_arm_times_the_load_on_that_wheel():
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("cart", cart())))) as world:
        world.start()
        for _ in range(300):
            world.step({})
        m = backend.model
        for i in range(4):
            body = m.body(f"cart/w{i}").id
            dof = m.jnt_dofadr[m.joint(f"cart/h{i}").id]
            assert abs(m.dof_frictionloss[dof] - rolling.lever_arm("rubber") * _normal(backend, body)) < 1e-9
            assert m.dof_frictionloss[dof] > 0
            assert tuple(m.dof_solref[dof]) == dry_friction_solref(m.opt.timestep)
        world.reset()
        assert (backend.model.dof_frictionloss == 0).all(), "reset restores the compiled losses"


def test_a_swivel_gets_no_rolling_torque_and_its_wheel_does():
    from little_world.assets.catalog import BY_ID
    caster = BY_ID["swivel_caster"].blueprint()
    caster = replace(caster, components=tuple(
        replace(c, dynamic=True, transform=Transform((0, 0, .08))) if getattr(c, "parent", 1) is None else c
        for c in caster.components))
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("c", caster)))) as world:
        world.start()
        for _ in range(400):
            world.step({})
        m = backend.model
        swivel = m.jnt_dofadr[m.joint("c/swivel_joint").id]
        wheel_dof = m.jnt_dofadr[m.joint("c/wheel_joint").id]
        assert m.dof_frictionloss[wheel_dof] > 0
        assert m.dof_frictionloss[swivel] == 0


def test_coast_down_matches_the_closed_form_prediction():
    """(M + sum I/r^2) a = sum b N / r = b M g / r, for equal wheels on a flat floor."""
    import numpy as np
    r = .05
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("cart", cart(r))))) as world:
        world.start()
        m, d = backend.model, backend.data
        for _ in range(200):
            world.step({})
        mass = sum(m.body_mass[i] for i in range(m.nbody) if m.body(i).name.startswith("cart/"))
        inertia = sum(m.body_inertia[m.body(f"cart/w{i}").id][2] for i in range(4))
        g = -m.opt.gravity[2]
        predicted = rolling.lever_arm("rubber") * mass * g / (r * (mass + inertia / r ** 2))
        v0 = .8
        root = m.body("cart/chassis").id
        d.qvel[m.jnt_dofadr[m.body_jntadr[root]]] = v0
        for i in range(4):
            d.qvel[m.jnt_dofadr[m.joint(f"cart/h{i}").id]] = v0 / r
        speeds = []
        for _ in range(600):
            world.step({})
            speeds.append(d.qvel[m.jnt_dofadr[m.body_jntadr[root]]])
        t = np.arange(1, len(speeds) + 1) * m.opt.timestep
        measured = -np.polyfit(t[50:], np.array(speeds[50:]), 1)[0]
    assert abs(measured - predicted) / predicted < .01, (measured, predicted)


def test_a_wheel_meets_the_floor_at_one_contact_so_the_engine_adds_no_rolling_loss():
    """MuJoCo 3.8 made multiccd the default: several contacts per convex pair. A cylinder
    wheel on the box floor got four, within 0.1 mm of each other, and the solver loaded the
    leading ones more as it rolled - a rolling loss of its own, 5 % of the sourced one at
    0.8 m/s. The adapter keeps one contact per convex pair (ADR 0027), so the coast-down
    above matches its closed form as it did on 3.3.7."""
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("cart", cart())))) as world:
        world.start()
        for _ in range(100):
            world.step({})
        m, d = backend.model, backend.data
        assert m.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_MULTICCD
        for i in range(4):
            wheel = m.body(f"cart/w{i}").id
            touching = [k for k in range(d.ncon) if wheel in (m.geom_bodyid[d.contact[k].geom1],
                                                               m.geom_bodyid[d.contact[k].geom2])]
            assert len(touching) == 1, (i, len(touching))


def test_gearbox_friction_sits_on_the_output_joint():
    from little_world.assets.catalog import BY_ID
    motor = BY_ID["gearmotor_37"].blueprint()
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("g", motor)))) as world:
        world.start()
        m = backend.model
        joint = next(m.joint(j).name for j in range(m.njnt) if m.joint(j).name.startswith("g/") and m.jnt_type[j] == 3)
        dof = m.jnt_dofadr[m.joint(joint).id]
        assert abs(m.dof_frictionloss[dof] - PROFILES[KIT_GEARMOTOR].friction_torque) < 1e-12
        assert m.dof_damping[dof] == 0.
        assert tuple(m.dof_solref[dof]) == dry_friction_solref(m.opt.timestep)
        assert tuple(m.dof_solimp[dof]) == DRY_FRICTION_SOLIMP


def _geared_disc(dt=.001):
    """A Pololu 37D output driving an aluminium disc the size of a kit wheel (radius
    40 mm, 20 mm thick: 2.2e-4 kg m^2)."""
    from little_world.core.component import Body, Geometry
    bp = Blueprint((Body("rotor", Geometry("cylinder", (.04, .02)), "metal"),
                    Hinge("joint", "rotor", damping=0.),
                    Motor("motor", "joint", .5, PROFILES[KIT_GEARMOTOR])), (METAL,))
    backend = MujocoBackend()
    backend.compile(Scene((Entity("t", bp),)), dt)
    return backend


def test_a_free_gearmotor_reaches_its_datasheet_speed_despite_its_friction():
    """Friction on the joint and the motor's larger own torque must cancel exactly at
    the no-load speed, or the gearmotor would run slower than its datasheet says."""
    backend = _geared_disc()
    for _ in range(3000):
        backend.step({"t/motor": .5})
    free = PROFILES[KIT_GEARMOTOR].no_load_rpm * 2 * pi / 60
    assert abs(backend.data.qvel[0] - free) / free < 1e-3
    backend.close()


def test_gearbox_friction_is_coulomb_friction_not_a_damper():
    """Below its friction torque a gearmotor holds; unpowered, it coasts to rest at the
    constant deceleration friction / inertia. MuJoCo's default soft friction crept 0.2
    rad in a second under 80 % of the friction and took 47 % longer to stop."""
    friction = PROFILES[KIT_GEARMOTOR].friction_torque
    backend = _geared_disc()
    inertia = 1 / backend.model.dof_invweight0[0]
    for _ in range(1000):
        backend.step({"t/motor": .8 * friction})
    assert abs(backend.data.qpos[0]) < 1e-3, "held for one second"
    backend.reset()
    free = PROFILES[KIT_GEARMOTOR].no_load_rpm * 2 * pi / 60
    backend.data.qvel[0] = free
    steps = 0
    while backend.data.qvel[0] > 1e-3:
        backend.step({"t/motor": 0.})
        steps += 1
    coulomb = free * inertia / friction
    assert abs(steps * backend.model.opt.timestep - coulomb) / coulomb < .02
    backend.close()


def test_a_tread_ring_rolls_on_its_axle():
    """The hardware tread wheel touches the floor with 24 separate rubber blocks, not a
    cylinder: together they are a tread, so the gearmotor output carries their load."""
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("r", mobile_platform_blueprint())))) as world:
        world.start()
        for _ in range(300):
            world.step({})
        m = backend.model
        outputs = [m.jnt_dofadr[j] for j in range(m.njnt) if m.joint(j).name.endswith("output_shaft_joint")]
        weight = m.body_subtreemass[m.body("r/root").id] * -m.opt.gravity[2]
        rolling_share = sum(m.dof_frictionloss[x] - PROFILES[KIT_GEARMOTOR].friction_torque for x in outputs)
        assert len(outputs) == 2
        # The platform rests almost entirely on its two drive wheels.
        assert .8 * weight < rolling_share / rolling.lever_arm("rubber") < 1.2 * weight


def test_a_rubber_pad_pressed_by_a_hinged_finger_is_not_a_tread():
    """Rubber, on a hinge, pressing on something - and still not rolling."""
    from little_world.materials import WOOD
    block = Blueprint((box("block", (.1, .1, .1), "wood", transform=Transform((.105, .07, .05))),), (WOOD,))
    finger = Blueprint((box("base", (.02, .02, .02), "metal", transform=Transform((0, 0, .05))),
                        box("finger", (.08, .01, .01), "metal", parent="base", transform=Transform((.06, 0, 0))),
                        box("pad", (.01, .03, .03), "rubber", parent="finger", transform=Transform((.045, 0, 0))),
                        Hinge("h", "finger", position=(-.05, 0, 0), damping=0.),
                        Motor("press", "h", 1.)), (METAL, RUBBER))
    backend = MujocoBackend()
    with World(backend, Scene((Entity("block", block), Entity("f", finger)))) as world:
        world.start()
        for _ in range(300):
            world.step({"f/press": .5})
        m = backend.model
        assert _normal(backend, m.body("f/pad").id) > 1., "the pad is pressing"
        assert m.dof_frictionloss[m.jnt_dofadr[m.joint("f/h").id]] == 0.


def test_a_bare_gearmotor_runs_at_its_datasheet_speed_without_a_limit_cycle():
    """The bare output shaft weighs 1.8e-8 kg m^2 - the rotor's inertia, which the
    datasheet does not give, is missing. Evaluated once per step, the speed-torque line
    let it reach 50,000 rad/s in one 2 ms step and sawtooth around 24,000 rad/s; the
    line is now integrated implicitly."""
    from little_world.assets.catalog import BY_ID
    motor = BY_ID["gearmotor_37"].blueprint()
    drive = next(c for c in motor.components if isinstance(c, Motor))
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("g", motor)))) as world:
        world.start()
        m = backend.model
        dof = m.jnt_dofadr[m.joint("g/" + drive.joint).id]
        speeds = []
        for _ in range(500):
            world.step({"g/" + drive.id: drive.max_torque})
            speeds.append(float(backend.data.qvel[dof]))
    free = PROFILES[KIT_GEARMOTOR].no_load_rpm * 2 * pi / 60
    tail = speeds[-250:]
    assert max(abs(v - free) for v in tail) / free < 1e-3, (min(tail), max(tail), free)


def test_the_line_is_implicit_only_where_it_limits_the_command():
    p = PROFILES[KIT_GEARMOTOR]
    stall, free = p.line()
    assert p.slope(.3, 0., .5) == 0., "below the line: the command itself"
    assert p.slope(.5, 0., .5, reach=1e6) == -stall / free, "one step could reach the line"
    assert p.slope(.5, .9 * free, .5) == -stall / free
    assert p.slope(.5, 1.1 * free, .5) == 0., "past free speed: no torque at all"
    assert p.slope(-.5, .5 * free, .5) == 0., "braking stays capped"
    assert p.slope(0., .5 * free, .5) == 0.
