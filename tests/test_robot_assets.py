"""Contracts for registered, preserved real robot models."""
from dataclasses import replace
import pytest
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor


def panda():return BY_ID['franka_panda'].blueprint()


def test_robot_asset_roundtrip_and_lifecycle():
    bp=panda();assert Blueprint.from_json(bp.to_json())==bp
    ed=AssemblyEditor(bp);ed.duplicate();assert len(ed.blueprint.controllers)==16
    ed.delete();assert len(ed.blueprint.controllers)==8
    ed.undo();assert len(ed.blueprint.controllers)==16
    with pytest.raises(ValueError,match='fixed'):ed.scale(1.2)


def test_unknown_robot_asset_rejected():
    bp=panda();root=next(c for c in bp.components if isinstance(c,Body))
    with pytest.raises(ValueError,match='robot asset'):
        replace(root,robot_asset='../../untrusted.xml')


def test_panda_native_constraints_and_controls():
    mj=pytest.importorskip('mujoco')
    import numpy as np
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.assets.robot_models import model_path
    source=mj.MjModel.from_xml_path(str(model_path('franka_panda')))
    backend=MujocoBackend();backend.compile(Scene((Entity('machine',panda()),)),.002)
    m,d=backend.model,backend.data
    assert m.nmesh==source.nmesh and m.neq==source.neq and m.ntendon==source.ntendon
    assert m.body_mass.sum()==pytest.approx(source.body_mass.sum())
    assert np.allclose(m.jnt_range,source.jnt_range)
    assert np.allclose(m.actuator_forcerange,source.actuator_forcerange)
    original=d.qpos.copy()
    control=MujocoKeyboardControl(backend,panda())
    for _ in range(200):backend.step(control.step_commands(.002))
    assert np.max(np.abs(d.qpos-original))<.04
    control.press('Q')
    for _ in range(250):backend.step(control.step_commands(.002))
    assert d.qpos[0]>original[0]+.08
    control.clear();control.press('G')
    for _ in range(1000):backend.step(control.step_commands(.002))
    assert d.qpos[-1]<.015 and abs(d.qpos[-1]-d.qpos[-2])<.002
    assert np.isfinite(d.qpos).all()
    backend.reset();assert np.allclose(d.qpos,original)
    backend.close()


def test_mount_real_arm_and_save():
    ed=AssemblyEditor(BY_ID['ready_rover_4'].blueprint())
    from little_world.construction.docking import dock
    dock(ed,'franka_panda','root','Top')
    assert len([c for c in ed.blueprint.controllers if c.kind=='keyboard_position'])==8
    assert Blueprint.from_json(ed.blueprint.to_json())==ed.blueprint
    ed.undo();assert not any(b.robot_asset for b in ed.bodies)


def test_two_registered_robots_have_independent_controls():
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.materials import METAL
    ed=AssemblyEditor(Blueprint((),(METAL,)))
    ed.add_catalog('franka_panda','Floor');ed.add_catalog('franka_panda','Floor')
    assert len(ed.blueprint.controllers)==14  # all available non-reserved key pairs are used
    keys=[k for s in ed.blueprint.controllers for k in (s.positive_key,s.negative_key)]
    assert len(keys)==len(set(keys))
    backend=MujocoBackend();backend.compile(Scene((Entity('machine',ed.blueprint),)),.002)
    assert backend.model.nu==16 and backend.model.neq==2
    assert backend.model.body_mass.sum()==pytest.approx(2*17.451901)
    control=MujocoKeyboardControl(backend,ed.blueprint)
    control.press('Q')
    for _ in range(250):backend.step(control.step_commands(.002))
    roots=[b for b in ed.bodies if b.robot_asset]
    q0=backend.model.jnt_qposadr[backend.model.joint('machine/'+roots[0].id+'__robot_joint1').id]
    q1=backend.model.jnt_qposadr[backend.model.joint('machine/'+roots[1].id+'__robot_joint1').id]
    assert backend.data.qpos[q0]>.08 and abs(backend.data.qpos[q1])<.02
    backend.close()


def test_panda_program_units_and_inventory_mass():
    pytest.importorskip('mujoco')
    from little_world.programming.program import Program,Block
    from little_world.inventory.analysis import analyze
    from little_world.inventory.benchmark import trial
    bp=panda();report=analyze(bp)
    assert report['mass_kg']==pytest.approx(17.451901)
    assert report['motors']==8
    program=Program((Block('move','panda_1',10,2),Block('move','panda_8',100,3)))
    program.validate(bp)
    with pytest.raises(ValueError,match='limits'):Program((Block('move','panda_8',110),)).validate(bp)
    result=trial(bp,program,'program',5,.002)
    assert result['program_state']=='completed'
    assert result['absolute_mechanical_work_J']>=0


import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_robot_ui_mesh_resources_save_undo_and_controls(tmp_path):
    import glfw
    import mujoco as mj
    import numpy as np
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'panda.json');app.open_bench();original_draw=app.draw
    tick=0;old_context=None;canvas=None
    def draw():
        nonlocal tick,old_context,canvas
        original_draw();tick+=1
        if tick==1:
            old_context=app.context;canvas=app.canvas
            app.edit(lambda:app.editor.load(panda()))
            app.catalog_selection='franka_panda';app.frame_assembly()
        elif tick==2:
            assert app.context is not old_context and app.canvas is canvas
            app.wheel_position_form()
            assert app.dialog['title']=='Choose a socket / kit compatibility'
            app.dialog=None
            assert app.model.nmesh==67 and len(app.joint_control.specs)==8
            # A real mesh preview must have its own uploaded resources.
            ww,wh=glfw.get_window_size(app.window);fw,fh=glfw.get_framebuffer_size(app.window)
            app.render_catalog_preview(ww,wh,fw,fh)
            assert app.preview_cache['franka_panda'][4] is not None
            app.inventory_preview(app.editor.blueprint,(300,200,250,220),ww,wh,fw,fh)
            assert next(iter(app.inventory_previews.values()))[0]._preview_context is not None
            app.path.write_text(app.editor.blueprint.to_json())
            app.edit(app.editor.delete)
        elif tick==3:
            assert app.model.nmesh==0
            app.edit(app.editor.undo)
        elif tick==4:
            assert app.editor.blueprint==Blueprint.from_json(app.path.read_text())
            app.close_bench();app.control_panel=True;app.panel_mode='keys'
            app.simulate();app.joint_control.press('Q')
            for _ in range(250):app.world.step(app.joint_control.step_commands(.002))
            assert app.data.qpos[0]>.08
        elif tick==5:
            snapshot=app.test_snapshot()
            assert len(snapshot['joints'])==8
            assert snapshot['joints'][-1]['unit']=='% closed'
            app.show_test();original_draw()
            glfw.set_window_should_close(app.window,True)
    app.draw=draw;app.run(10)
    assert tick==5
