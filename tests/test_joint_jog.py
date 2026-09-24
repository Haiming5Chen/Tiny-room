import pytest
from little_world.assets.robot_models import blueprint
from little_world.core.scene import Scene
from little_world.core.entity import Entity

@pytest.mark.parametrize('asset',['franka_panda','franka_fr3','kinova_gen3','ur5e'])
def test_jog_accumulates_and_respects_limits(asset):
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    b=MujocoBackend();bp=blueprint(asset);b.compile(Scene((Entity('machine',bp),)),.002)
    try:
        c=MujocoKeyboardControl(b,bp);name=c.specs[0].actuators[0]
        start=c.display_position(name)[0]
        c.nudge(name,5);first=c.targets[name];c.nudge(name,5)
        from math import radians
        assert c.targets[name]==pytest.approx(first+radians(5))
        for _ in range(200):b.step(c.step_commands(.002))
        assert c.display_position(name)[0]>start+1
        c.nudge(name,10000);idx,_=c.servos[name]
        hi=b.model.actuator_ctrlrange[idx,1] if b.model.actuator_ctrllimited[idx] else 6.283185307
        assert c.targets[name]==pytest.approx(hi)
        if asset=='franka_panda':
            grip=c.specs[-1].actuators[0];c.nudge(grip,10)
            assert c.targets[grip]==pytest.approx(229.5)
            c.nudge(grip,1000);assert c.targets[grip]==0
            c.nudge(grip,-1000);assert c.targets[grip]==255
    finally:b.close()

import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_visible_jog_starts_physics_and_preserves_design(tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'robot.json',blueprint());original=app.editor.blueprint
    app.operate_robot();draw=app.draw;tick=0
    def use():
        nonlocal tick
        draw();tick+=1
        if tick==1:
            assert any(b.label=='Open' for b in app.buttons)
            next(b for b in app.buttons if b.label=='+').action()
            assert not app.building
            assert app.joint_control.targets
        elif tick==2:
            next(b for b in app.buttons if b.label=='Pause').action();assert app.paused
            app.simulate();assert app.building
            assert app.editor.blueprint==original
            next(b for b in app.buttons if b.label=='Gripper / 10%').action()
        elif tick==3:
            assert next(b for b in app.buttons if b.label=='Edit action').enabled
            glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(15);assert tick==3
