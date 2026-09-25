"""Contracts for friction that holds (ADR 0017).

The defect: MuJoCo's contact friction is soft - below its limit a contact still creeps.
A 16 g cube squeezed at about 12 N per jaw slid out of the kit gripper at 2 mm/s and
fell out of a carried grasp within 30 s; the same creep let the platform's 40 mm casters
ride up a 20 mm curb, level with their axles, where a pushed wheel has nothing lifting
it. Separately, the Kinova Gen3's shoulder touched its base 12 mm deep at every pose -
MuJoCo does not filter a child against a parent welded to the world - and its first
joint ground against that contact at its 105 N m limit.
"""
import pytest

mujoco = pytest.importorskip('mujoco')
import numpy as np  # noqa: E402
from little_world import Entity, World  # noqa: E402
from little_world.control.mujoco_keyboard import MujocoKeyboardControl  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend, NOSLIP_ITERATIONS  # noqa: E402


def test_a_held_cube_stays_in_the_grip():
    from little_world.control.tool_motion import ToolMotion
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.scenes.workshop import workshop_scene
    bp = arm_lab_blueprint()
    backend = MujocoBackend()
    with World(backend, workshop_scene(Entity('machine', bp))) as world:
        world.start()
        assert backend.model.opt.noslip_iterations == NOSLIP_ITERATIONS >= 2
        control = MujocoKeyboardControl(backend, bp)
        motion = ToolMotion(backend, bp, control)

        def advance(seconds):
            for _ in range(round(seconds / world.timestep)):
                world.step(control.step_commands(world.timestep))
        advance(.5)
        control.press('G'); advance(1.); control.release('G'); advance(.3)
        control.press('R'); advance(.6); control.release('R'); advance(.5)
        offset = lambda: backend.data.body('objects/grasp_cube').xpos - motion.tool()[0]
        before = offset().copy()
        advance(10.)
        assert np.linalg.norm(offset() - before) < .001, "held for 10 s without sliding out"


def test_what_slides_still_slides():
    """Noslip removes creep below the friction limit, not sliding above it: a box on a
    tilted plane steeper than its friction angle accelerates at g (sin a - mu cos a)."""
    xml = '''<mujoco><option timestep="0.002" integrator="implicitfast" noslip_iterations="%d"/>
    <worldbody><geom type="plane" size="2 2 .1" euler="0 20 0" friction=".2 .005 .0001"/>
    <body pos="0 0 .06" euler="0 20 0"><freejoint/><geom type="box" size=".05 .05 .05" mass="1" friction=".2 .005 .0001"/></body>
    </worldbody></mujoco>'''
    expected = 9.81 * (np.sin(np.radians(20)) - .2 * np.cos(np.radians(20)))
    for noslip in (0, NOSLIP_ITERATIONS):
        m = mujoco.MjModel.from_xml_string(xml % noslip)
        d = mujoco.MjData(m)
        for _ in range(250):
            mujoco.mj_step(m, d)
        speed = np.linalg.norm(d.qvel[:3])
        assert speed / .5 == pytest.approx(expected, rel=.05), (noslip, speed / .5, expected)


def test_adjacent_links_of_a_registered_robot_do_not_collide():
    from little_world.assets.robot_models import blueprint
    from little_world.core.scene import Scene
    bp = blueprint('kinova_gen3')
    backend = MujocoBackend()
    backend.compile(Scene((Entity('machine', bp),)), .002)
    m, d = backend.model, backend.data
    touching = [(m.body(m.geom_bodyid[d.contact[i].geom1]).name, m.body(m.geom_bodyid[d.contact[i].geom2]).name)
                for i in range(d.ncon)]
    assert not touching, touching
    control = MujocoKeyboardControl(backend, bp)
    control.press('Q')
    start = float(d.qpos[0])
    for _ in range(250):
        backend.step(control.step_commands(.002))
    assert d.qpos[0] > start + .06
    assert abs(d.actuator_force[0]) < 105., "turning its first joint no longer takes all it has"
    backend.close()
