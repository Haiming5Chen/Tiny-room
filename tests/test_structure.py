"""Contracts for a machine's structure: modules, roles, mass and stance (ADR 0015).

The defect: the Assembly tab listed a mobile manipulator as 300-odd bodies in a tree,
so nothing said "this is a base with two drives, two casters, an arm and a gripper",
which keys move which module, or what each weighs; and nothing said whether the
machine stands - an arm reaching over the side of a light cart can tip it, and the
first sign was the tipped run.
"""
from math import atan2, cos, degrees, sin
import pytest

from little_world.construction.structure import area, hull, margin, modules, standing, centre_of_mass
from little_world.robots.arm_lab import arm_lab_blueprint
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
from little_world.robots.mobile_platform import mobile_platform_blueprint


# -- plane geometry -------------------------------------------------------------------

def test_hull_keeps_corners_and_drops_what_is_inside_or_on_a_line():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert hull(square + [(.5, .5), (.2, .7), (.5, 0.)]) == square
    assert hull([(0, 0), (1, 0), (2, 0)]) == [(0, 0), (2, 0)], "collinear points span a line, not an area"
    assert area(square) == 1.


def test_margin_is_positive_inside_negative_outside_and_measured_to_the_nearest_edge():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert margin(square, (.5, .5)) == pytest.approx(.5)
    assert margin(square, (.9, .5)) == pytest.approx(.1)
    assert margin(square, (1.3, .5)) == pytest.approx(-.3)
    assert margin([(0, 0), (1, 0)], (.5, .2)) < 0, "two contacts hold nothing up"
    assert margin([], (0, 0)) == float('-inf')


# -- modules ----------------------------------------------------------------------------

def roles(bp):
    return [m.role for m in modules(bp)]


def test_a_mobile_manipulator_reads_as_its_modules():
    found = modules(mobile_manipulator_blueprint())
    assert [m.role for m in found] == ['base', 'drive', 'wheel', 'drive', 'wheel', 'arm', 'tool', 'support', 'support']
    by_role = {}
    for m in found:
        by_role.setdefault(m.role, []).append(m)
    base = by_role['base'][0]
    assert base.depth == 0 and base.parent is None
    assert all(w.parent in {d.root for d in by_role['drive']} for w in by_role['wheel']), "wheels ride on the drives"
    arm, tool = by_role['arm'][0], by_role['tool'][0]
    assert tool.parent == arm.root and arm.parent == base.root
    assert [k[1:] for k in arm.keys] == [('Q', 'E'), ('R', 'V'), ('T', 'B'), ('Y', 'N')]
    assert [k[1:] for k in tool.keys] == [('G', 'H')]
    assert all(len(d.actuators) == 1 for d in by_role['drive'])
    assert sum(len(m.bodies) for m in found) == sum(1 for c in mobile_manipulator_blueprint().components
                                                    if type(c).__name__ == 'Body'), "every body in one module"


def test_an_arm_on_a_pedestal_and_a_bare_cart():
    assert roles(arm_lab_blueprint()) == ['base', 'arm', 'tool']
    assert roles(mobile_platform_blueprint()) == ['base', 'drive', 'wheel', 'drive', 'wheel', 'support', 'support']


def test_the_example_designs_start_on_the_floor_and_one_built_in_the_air_reads_how_high():
    """A run starts a design where it was built (ADR 0023). The examples rest on their
    lowest point, 2 mm up; the same platform lifted 4 cm reads 4 cm higher; an arm bolted
    to its pedestal has nothing standing free."""
    from dataclasses import replace
    from little_world.construction.editor import starter_blueprint
    from little_world.construction.structure import AIRBORNE, clearance
    from little_world.core.component import Body
    from little_world.robots.two_wheel import two_wheel_blueprint
    for factory in (starter_blueprint, two_wheel_blueprint, mobile_platform_blueprint, mobile_manipulator_blueprint):
        assert 0 < clearance(factory()) <= AIRBORNE, factory.__name__
    bp = mobile_platform_blueprint()
    lifted = replace(bp, components=tuple(
        replace(c, transform=replace(c.transform, position=(*c.transform.position[:2], c.transform.position[2] + .04)))
        if isinstance(c, Body) and c.parent is None else c for c in bp.components))
    assert clearance(lifted) == pytest.approx(clearance(bp) + .04)
    assert clearance(arm_lab_blueprint()) is None


# -- mass and stance against the simulator ------------------------------------------------

mujoco = pytest.importorskip('mujoco')
from little_world import Entity, World  # noqa: E402
from little_world.fields import field_scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402


@pytest.mark.parametrize('factory', [arm_lab_blueprint, mobile_platform_blueprint, mobile_manipulator_blueprint])
def test_module_masses_add_up_to_what_the_simulator_weighs(factory):
    bp = factory()
    found = modules(bp)
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', bp))) as world:
        world.start()
        m, d = backend.model, backend.data
        roots = [i for i in range(1, m.nbody) if m.body(i).name.startswith('machine/')
                 and not m.body(int(m.body_parentid[i])).name.startswith('machine/')]
        weighed = sum(float(m.body_subtreemass[i]) for i in roots)
        assert sum(x.mass for x in found) == pytest.approx(weighed, rel=1e-9)
        total, com = centre_of_mass(bp)
        simulated = sum(float(m.body_subtreemass[i]) * d.subtree_com[i] for i in roots) / weighed
        assert total == pytest.approx(weighed, rel=1e-9)
        assert com == pytest.approx(tuple(simulated), abs=1e-9)


@pytest.mark.parametrize('factory', [mobile_platform_blueprint, mobile_manipulator_blueprint])
def test_a_run_starts_the_platforms_on_their_wheels(factory):
    """Built with its wheels 4.3 cm up, the platform fell as every run began (OPEN LW-014),
    and a field that drives from the first step landed it with its wheels already turning.
    Now it starts on them and settles less than 3 mm."""
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', factory()))) as world:
        world.start()
        start = float(backend.data.body('machine/root').xpos[2])
        for _ in range(250):
            world.step({})
        assert start - float(backend.data.body('machine/root').xpos[2]) < .003


def test_a_box_stands_flat_and_a_tall_leaning_one_tips_over():
    from little_world.construction.structure import settle
    cube = [(x, y, z) for x in (0., .1) for y in (0., .1) for z in (0., .1)]
    s = settle(cube, (.05, .05, .05))
    assert s.tilt == 0. and s.margin == pytest.approx(.05) and not s.tips_over
    s = settle(cube, (.13, .05, .05))
    assert s.tips_over, "centre of mass beyond the edge: it rolls onto its side and past"


def test_a_rocker_settles_onto_the_side_its_centre_of_mass_is_on():
    """Two wheels on a line with a caster 6.5 mm up at each end: the machine cannot
    stand on the line, so it tips forward until the front caster meets the floor."""
    from little_world.construction.structure import settle
    wheels = [(0., y, 0.) for y in (-.15, .15)]
    casters = [(.12, 0., .0065), (-.12, 0., .0065)]
    tall = [(0., 0., .3)]
    s = settle(wheels + casters + tall, (.025, 0., .14), owners=['L', 'R', 'front', 'rear', 'top'])
    assert s.touching == ('L', 'R', 'front')
    tilt = atan2(.0065, .12)
    assert s.tilt == pytest.approx(degrees(tilt), abs=1e-6)
    # Nose down, the centre of mass sits further ahead of the wheel line than it was.
    assert s.margin == pytest.approx(.025 * cos(tilt) + .14 * sin(tilt), abs=1e-9)


def test_the_rigid_stance_matches_where_the_simulator_settles():
    """Asked of the design before it runs, and answered by the physics after it has
    settled: the mobile manipulator rests on both wheels and both casters, level (ADR 0041;
    with its casters 6.5 mm up it rested on its front caster, 2.8 degrees nose down)."""
    from little_world.construction.structure import module_roots
    from little_world.control.drive_telemetry import DriveTelemetry
    from little_world.control.mujoco_drive import MujocoDrive
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    bp = mobile_manipulator_blueprint()
    predicted = standing(bp)
    owner = module_roots(bp)
    assert sorted({owner[b] for b in predicted.touching}) == ['swivel_caster_1_root', 'swivel_caster_2_root',
                                                             'tread_wheel_1_root', 'tread_wheel_2_root']
    assert predicted.tilt == 0.
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', bp))) as world:
        world.start()
        drive, arm = MujocoDrive(backend, bp), MujocoKeyboardControl(backend, bp)
        telemetry = DriveTelemetry(backend, bp, drive)
        for _ in range(750):
            commands = dict(drive.step_commands((0., 0.), world.timestep))
            commands.update(arm.step_commands(world.timestep))
            world.step(commands)
        settled = telemetry.sample()
        assert settled.tilt == pytest.approx(predicted.tilt, abs=.3)
        assert settled.margin == pytest.approx(predicted.margin, abs=.003)


def test_the_bare_cart_stands_on_all_four_and_with_its_casters_up_was_a_rocker():
    """The bare cart's centre of mass is 0.7 mm ahead of its axle. With its casters on the
    floor it stands level on all four, 9.4 cm inside their outline (ADR 0041). With them
    6.5 mm up, as it was built before, it balanced on its two tread patches with 3 mm to
    spare, and the drop onto the floor at the start of a run was enough to rock it onto a
    caster."""
    from little_world.robots.mobile_platform import ROCKING_GAP
    four = standing(mobile_platform_blueprint())
    assert four.tilt == 0. and four.margin == pytest.approx(.094, abs=.001)
    rocker = standing(mobile_platform_blueprint(ROCKING_GAP))
    assert rocker.margin < .005 and rocker.tilt == 0.


# -- the window: the Assembly tab reads as modules ---------------------------------------

@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_the_assembly_tab_lists_modules_and_selects_them(monkeypatch, tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'modules.json', mobile_manipulator_blueprint())
    app.open_bench()
    draw = app.draw
    tick = 0

    def click(label):
        b = next(b for b in app.buttons if b.label == label)
        assert b.enabled, label
        app.events.append(b.action)

    def exercise():
        nonlocal tick
        draw()
        tick += 1
        if tick == 1:
            click('Assembly')
        elif tick == 2:
            assert app.assembly_view == 'Modules'
            labels = [b.label for b in app.buttons]
            assert 'Compact arm / 240 mm' in labels and 'Two-finger gripper' in labels
            assert labels.count('100 mm tread wheel') == 2
            found, stance, mass = app.machine_modules()
            assert app.structure_line().startswith('base + 2 drives + arm + tool + 2 supports')
            assert app.stance_words(found, stance).startswith('rests on 2 wheels and 2 supports; centre of mass 9.0 cm inside')
            click('Compact arm / 240 mm')
        elif tick == 3:
            assert app.editor.selection == 'robot_arm_compact_1_root'
            click('Parts')
        elif tick == 4:
            assert app.assembly_view == 'Parts' and any(b.label == 'Find in assembly' for b in app.buttons)
            glfw.set_window_should_close(app.window, True)
    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=10)
    assert tick >= 4
