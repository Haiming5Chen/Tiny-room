import os
import pytest
from little_world.assets.robot_models import blueprint,model_path
from little_world.assets.catalog import CATALOG
from little_world.core.scene import Scene
from little_world.core.entity import Entity


@pytest.mark.parametrize('asset',['franka_fr3','kinova_gen3','ur5e'])
def test_sourced_arm_keeps_mechanics_and_moves(asset):
    mj=pytest.importorskip('mujoco')
    import numpy as np
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.core.blueprint import Blueprint
    bp=blueprint(asset);assert Blueprint.from_json(bp.to_json())==bp
    source=mj.MjModel.from_xml_path(str(model_path(asset)))
    backend=MujocoBackend();backend.compile(Scene((Entity('machine',bp),)),.002)
    assert np.allclose(backend.model.jnt_range,source.jnt_range)
    assert np.allclose(backend.model.actuator_gainprm,source.actuator_gainprm)
    assert backend.model.body_mass.sum()==pytest.approx(source.body_mass.sum())
    assert backend.model.nmesh==source.nmesh
    control=MujocoKeyboardControl(backend,bp);control.press('Q');start=backend.data.qpos[0]
    for _ in range(250):backend.step(control.step_commands(.002))
    assert backend.data.qpos[0]>start+.06
    backend.reset();assert backend.data.qpos[0]==start
    backend.close()


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_mesh_ghost_follows_cursor_places_exactly_and_cancels(tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.construction.editor import starter_blueprint
    app=Workshop(tmp_path/'drag.json',starter_blueprint());app.open_bench();draw=app.draw
    before=app.editor.blueprint;tick=0;pose=None;model=None;point=None
    def use():
        nonlocal tick,pose,model,point
        draw();tick+=1
        if tick==1:
            app.set_library_style('Real robots')
            assert {p.id for p in app.parts_items()}=={p.id for p in CATALOG if p.variant=='real_robot' or p.variant.startswith('lab_')}
            app.set_real_filter('Lab');assert len(app.parts_items())==sum(p.variant.startswith('lab_') for p in CATALOG)
            app.parts_input('roller');assert [p.id for p in app.parts_items()]==['lab_roller_table']
            app.set_real_filter('Arms');assert len(app.parts_items())==4
            app.set_real_filter('All')
            assert app.editor.blueprint==before
            app.part_drag=dict(item='ur5e',moving=None,start=(100,300),moved=False)
            app.last_mouse=(750,460);app.docking_move(750,460)
            assert app.drag_preview and app.drag_preview['backend'].model.nmesh>0
            model=app.drag_preview['backend'].model
        elif tick==2:
            assert app.drag_preview['pose'] is not None
            original=app.drag_preview['pose']
            px,py,w,h=app.bench_rect
            point=next((x,y) for x in (px+w-25,px+w-65,px+35) for y in (py+h-25,py+h-65) if app.socket_at(x,y) is None and app.ground_cursor(x,y) is not None)
            app.last_mouse=point;app.docking_move(*point)
            assert app.drag_preview['backend'].model is model
            assert app.drag_preview['pose']!=original
            pose=app.drag_preview['pose'];assert app.drag_preview['valid']
            app.docking_mouse(*point,glfw.RELEASE)
            assert app.drag_preview is None
        elif tick==3:
            assert app.editor.selected.robot_asset=='ur5e',app.status
            assert app.editor.selected.transform==pose
            assert len(app.editor.past)==1
            app.edit(app.editor.undo);assert app.editor.blueprint==before
            app.part_drag=dict(item='franka_panda',moving=None,start=(100,300),moved=False)
            app.last_mouse=(750,460);app.docking_move(750,460)
            app.cancel_docking();assert app.editor.blueprint==before and app.drag_preview is None
            app.set_library_style('Anime / kit')
            assert not any(p.variant=='real_robot' for p in app.parts_items())
            assert app.editor.blueprint==before
            glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(15);assert tick==3
