"""Contracts for the Panda as its own controller drives it (OPEN LW-036, ADR 0065).

Menagerie's Panda is the arm's mechanics with a position servo on each joint. The real arm's
controller also holds it against gravity, and the Franka Hand squeezes with 70 N continuously, 140 N
at most, its fingers moving at 50 mm/s each (its datasheet). Without them the cell's tool stopped 4 mm
short of every point and 4 mm low, the hand squeezed a 32 mm part with 1.6 N, and the part moved 3.3 mm
in the hand as it was carried.
"""
import numpy as np
import pytest

mj = pytest.importorskip('mujoco')


def test_its_links_are_held_against_gravity_on_a_fixed_base_and_not_on_a_cart():
    from little_world.assets.catalog import BY_ID
    from little_world.assets.robot_models import model_path
    from little_world.construction.docking import dock
    from little_world.construction.editor import AssemblyEditor
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.physics.importer import JAW_SOLIMP, JAW_SOLREF
    from little_world.physics.mujoco_backend import FINGER_SOLMIX, MujocoBackend
    source = mj.MjModel.from_xml_path(str(model_path('franka_panda')))
    backend = MujocoBackend()
    backend.compile(Scene((Entity('machine', BY_ID['franka_panda'].blueprint()),)), .002)
    m = backend.model
    links = [i for i in range(m.nbody) if m.body(i).name.startswith('machine/root__robot_')]
    assert len(links) == 11 and all(m.body_gravcomp[i] == 1. for i in links), "every link held up"
    assert m.body_gravcomp[m.body('machine/root').id] == 0.
    hand = m.actuator('machine/root__robot_actuator8').id
    assert tuple(m.actuator_forcerange[hand]) == (-140., 140.), "70 N on each finger, the tendon's force halved"
    assert np.allclose(np.delete(m.actuator_forcerange, hand, 0), np.delete(source.actuator_forcerange, 7, 0)), \
        "the arm's joints as Menagerie gives them"
    fingers = [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.endswith('finger')]
    assert fingers and all(np.allclose(m.geom_solref[g], JAW_SOLREF) and np.allclose(m.geom_solimp[g][:3], JAW_SOLIMP)
                           and m.geom_solmix[g] == FINGER_SOLMIX for g in fingers)
    backend.close()
    # On a cart the compensation would carry the cart's free joint too: no arm's controller does that.
    ed = AssemblyEditor(BY_ID['ready_rover_4'].blueprint())
    dock(ed, 'franka_panda', 'root', 'Top')
    rover = MujocoBackend()
    rover.compile(Scene((Entity('machine', ed.blueprint),)), .002)
    assert not rover.model.body_gravcomp.any(), "a robot on a free base is not held up"
    rover.close()


def test_the_cells_tool_reaches_each_point_and_the_hand_squeezes_seventy_newtons_and_holds_the_part_still():
    from little_world.factory.controller import FactoryCycle
    from little_world.factory.scene import factory_scene
    from little_world.physics.mujoco_backend import MujocoBackend
    b = MujocoBackend()
    b.compile(factory_scene(stock=0), .002)
    m, d = b.model, b.data
    cycle = FactoryCycle(b)
    cycle.plan('Amber')
    cycle.start()
    part = m.body('objects/product').id
    hand = next(i for i in range(m.nbody) if m.body(i).name.endswith('robot_hand'))
    fingers = {i for i in range(m.nbody) if m.body(i).name.endswith('finger')}
    finger_joints = [m.jnt_qposadr[m.body_jntadr[f]] for f in sorted(fingers)]
    finger_dofs = [m.jnt_dofadr[m.body_jntadr[f]] for f in sorted(fingers)]
    misses, squeezes, openings, in_hand, speeds = [], [], [], [], []
    force = np.zeros(6)
    for _ in range(int(30 / .002)):
        i = cycle.index
        b.step(cycle.commands(.002))
        if cycle.index != i or cycle.state != 'running':
            misses.append(float(np.linalg.norm(cycle.tool(d) - cycle.stages[i].point)))
        if cycle.state != 'running':
            break
        speeds.append(max(abs(float(d.qvel[k])) for k in finger_dofs))
        label = cycle.stages[cycle.index].label
        if label in ('Lift and check grasp', 'Transfer to Amber', 'Lower into bin') and cycle.elapsed > .1:
            per = {}
            for k in range(d.ncon):
                c = d.contact[k]
                pair = {int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])}
                if part in pair and pair & fingers:
                    mj.mj_contactForce(m, d, k, force)
                    finger = (pair & fingers).pop()
                    per[finger] = per.get(finger, 0.) + force[0]
            squeezes.append(sorted(per.values()))
            openings.append([float(d.qpos[q]) for q in finger_joints])
            in_hand.append(d.xmat[hand].reshape(3, 3).T @ (d.xpos[part] - cycle.tool(d)))
    assert cycle.state == 'completed', cycle.message
    assert len(misses) == len(cycle.stages) and max(misses) < .0006, \
        f'the tool {1000 * max(misses):.2f} mm from a point: held up, it does not sag (it was 5.7 to 6.7 mm)'
    assert .049 < max(speeds) < .0505, f'the fingers moved at up to {1000 * max(speeds):.0f} mm/s: their hand\'s 50 mm/s'
    assert all(len(s) == 2 and s[0] == pytest.approx(70., rel=.01) and s[1] == pytest.approx(70., rel=.01)
               for s in squeezes), "each finger presses 70 N, all through the carry"
    assert min(min(o) for o in openings) > .0158, "the fingers stop within 0.2 mm of the 32 mm part's faces"
    moved = max(np.linalg.norm(p - in_hand[0]) for p in in_hand)
    assert moved < .0015, f'the part moved {1000 * moved:.2f} mm in the hand as it was carried (3.3 mm before)'
    for _ in range(500):
        b.step({})
    x, y = cycle.trays['Amber']
    off = d.xpos[part][:2] - (x, y)
    assert np.linalg.norm(off) < .001, f'the part landed {1000 * np.linalg.norm(off):.2f} mm from its slot'
    b.close()
