import pytest
from little_world.factory.scene import factory_scene,robot_blueprint,BINS,TABLE
from little_world.core.blueprint import Blueprint

def test_factory_scene_is_portable():
    for entity in factory_scene().entities:
        assert Blueprint.from_json(entity.blueprint.to_json())==entity.blueprint

@pytest.mark.parametrize('product',['Small block','Tall block'])
@pytest.mark.parametrize('destination',['Blue','Amber'])
def test_factory_physically_places_product(product,destination):
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.factory.controller import FactoryCycle
    backend=MujocoBackend();backend.compile(factory_scene(product=product),.002)
    try:
        cycle=FactoryCycle(backend);before=backend.data.qpos.copy();cycle.plan(destination)
        assert (before==backend.data.qpos).all()  # planning cannot move the live world
        cycle.start()
        for _ in range(18000):
            backend.step(cycle.commands(.002))
            if cycle.state in ('completed','failed'):break
        assert cycle.state=='completed',cycle.message
        pos=backend.data.xpos[backend.model.body('objects/product').id]
        x,y=BINS[destination]
        assert abs(pos[0]-x)<.08 and abs(pos[1]-y)<.07 and TABLE<pos[2]<TABLE+.1
        assert cycle.lift_verified
    finally:backend.close()


def test_factory_rejects_unknown_destination_and_moved_input():
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.factory.controller import FactoryCycle
    import mujoco as mj
    b=MujocoBackend();b.compile(factory_scene(),.002)
    try:
        cycle=FactoryCycle(b)
        with pytest.raises(ValueError,match='Unknown'):cycle.plan('outside')
        jid=b.model.body('objects/product').jntadr[0]
        b.data.qpos[b.model.jnt_qposadr[jid]]+=.3;mj.mj_forward(b.model,b.data)
        with pytest.raises(ValueError,match='Reset'):cycle.plan('Blue')
    finally:b.close()


import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_factory_window_step_resume_reset(tmp_path):
    import glfw
    from little_world.ui.factory_workspace import FactoryWorkshop
    app=FactoryWorkshop(tmp_path/'factory.json');draw=app.draw;done=False
    def use():
        nonlocal done
        draw()
        if done:return
        before=app.editor.blueprint
        app.preview_cycle();app.start_cycle(True)
        for _ in range(6000):
            app.tick_program();app.state=app.world.step(app.joint_commands())
            if app.paused:break
        assert app.paused and app.cycle.index==1
        app.start_cycle()
        for _ in range(18000):
            app.tick_program();app.state=app.world.step(app.joint_commands())
            if app.paused:break
        assert app.cycle.state=='completed',app.cycle.message
        app.reset_cell();assert app.building and app.cycle.state=='idle'
        assert app.editor.blueprint==before
        app.select_product('Tall block');assert app.product=='Tall block'
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(30);assert done


def test_factory_reports_missed_grasp_without_fake_attachment():
    pytest.importorskip('mujoco')
    import mujoco as mj
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.factory.controller import FactoryCycle
    b=MujocoBackend();b.compile(factory_scene(),.002)
    try:
        cycle=FactoryCycle(b);cycle.plan('Blue')
        jid=b.model.body('objects/product').jntadr[0];adr=b.model.jnt_qposadr[jid]
        b.data.qpos[adr:adr+2]=(.65,.45);mj.mj_forward(b.model,b.data)
        cycle.start()
        for _ in range(8000):
            b.step(cycle.commands(.002))
            if cycle.state=='failed':break
        assert cycle.state=='failed' and 'Grasp failed' in cycle.message
        assert not cycle.lift_verified
    finally:b.close()
