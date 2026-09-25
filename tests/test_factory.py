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


# -- production runs (ADR 0019) -------------------------------------------------------------

def test_a_stocked_cell_is_portable_and_its_parts_wait_on_the_shelf():
    pytest.importorskip('mujoco')
    from little_world.factory.scene import stock_name, STOCK_SHELF
    from little_world.physics.mujoco_backend import MujocoBackend
    scene = factory_scene(stock=5)
    for entity in scene.entities:
        assert Blueprint.from_json(entity.blueprint.to_json()) == entity.blueprint
    assert scene.backdrop == 'sky', "no black void round the floor"
    b = MujocoBackend(); b.compile(scene, .002)
    try:
        for _ in range(500):
            b.step({})
        for i in range(1, 6):
            x, y, z = b.data.xpos[b.model.body('objects/' + stock_name(i)).id]
            assert abs(y - STOCK_SHELF[1]) < .01 and abs(z - (TABLE + .02)) < .003, "resting on the shelf"
    finally:
        b.close()


def test_a_production_run_places_part_after_part_in_its_own_slot():
    pytest.importorskip('mujoco')
    import numpy as np
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.factory.controller import FactoryCycle, SLOTS
    from little_world.factory.scene import stock_name
    b = MujocoBackend(); b.compile(factory_scene(stock=2), .002)
    try:
        cycle = FactoryCycle(b)
        with pytest.raises(ValueError, match='input tray'):
            cycle.production(['objects/product_2'], 'Amber')
        parts = ['objects/' + stock_name(i) for i in range(3)]
        cycle.production(parts, 'Amber')
        with pytest.raises(ValueError, match='Pause or reset'):
            cycle.production(parts, 'Amber')
        for _ in range(int(60 / .002)):
            b.step(cycle.commands(.002))
            if cycle.state in ('completed', 'failed'):
                break
        assert cycle.state == 'completed' and 'Run complete: 3 parts' in cycle.message, cycle.message
        placed, failed, per_part, rate = cycle.run_summary()
        assert (placed, failed) == (3, 0) and 10. < per_part < 15. and rate > 3.
        x, y = BINS['Amber']
        where = [b.data.xpos[b.model.body(p).id] for p in parts]
        for position, (dx, dy) in zip(where, SLOTS):
            assert abs(position[0] - x - dx) < .02 and abs(position[1] - y - dy) < .02, "each in its own slot"
            assert TABLE < position[2] < TABLE + .06, "resting in the tray, not on another part"
    finally:
        b.close()


def test_a_part_the_feeder_cannot_find_stops_the_run_with_the_reason():
    pytest.importorskip('mujoco')
    import mujoco as mj
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.factory.controller import FactoryCycle
    from little_world.factory.scene import stock_name
    b = MujocoBackend(); b.compile(factory_scene(stock=1), .002)
    try:
        cycle = FactoryCycle(b)
        cycle.production(['objects/' + stock_name(i) for i in range(2)], 'Blue')
        jid = b.model.body('objects/product').jntadr[0]
        adr = b.model.jnt_qposadr[jid]
        b.data.qpos[adr:adr + 2] = (.65, .45)   # the first part is taken off the input tray
        mj.mj_forward(b.model, b.data)
        for _ in range(8000):
            b.step(cycle.commands(.002))
            if cycle.state == 'failed':
                break
        assert cycle.state == 'failed' and 'Grasp failed' in cycle.message
        assert cycle.run_summary()[0] == 0 and cycle.run['failure'] == cycle.message
    finally:
        b.close()


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_the_production_run_button_counts_parts_and_reset_clears_it(tmp_path):
    import glfw
    from little_world.ui.factory_workspace import FactoryWorkshop
    app = FactoryWorkshop(tmp_path / 'factory.json'); draw = app.draw; done = False

    def use():
        nonlocal done
        draw()
        if done:
            return
        button = next(b for b in app.buttons if b.label == 'Run 6 parts')
        assert button.enabled
        button.action()
        assert app.cycle.run is not None and not app.building
        for _ in range(12000):
            app.tick_program(); app.state = app.world.step(app.joint_commands())
            if app.cycle.run_summary()[0] >= 1:
                break
        placed, failed, per_part, _ = app.cycle.run_summary()
        assert placed == 1 and failed == 0 and app.cycle.state == 'running', "on to the second part"
        app.reset_cell()
        assert app.building and app.cycle.state == 'idle' and app.cycle.run is None
        done = True; glfw.set_window_should_close(app.window, True)
    app.draw = use; app.run(60); assert done
