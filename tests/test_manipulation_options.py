from dataclasses import replace
import pytest
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body,Motor


def test_gripper_configuration_is_atomic_and_local():
    from little_world.robots.arm_lab import arm_lab_blueprint
    editor=AssemblyEditor(arm_lab_blueprint())
    editor.select('two_finger_gripper_1_finger_left_pad')
    original=editor.blueprint
    editor.configure_gripper('round','plastic',.25,.3,.06)
    changed=editor.blueprint
    assert Blueprint.from_json(changed.to_json())==changed
    pads=[c for c in changed.components if isinstance(c,Body) and c.id.endswith('_pad')]
    assert len(pads)==2 and all(c.geometry.shape=='cylinder' for c in pads)
    material=next(m for m in changed.materials if m.id==pads[0].material)
    assert material.sliding_friction==.25
    assert next(m for m in changed.materials if m.id=='rubber').sliding_friction==1.2
    assert all(c.max_torque==.3 for c in changed.components if isinstance(c,Motor) and 'finger_' in c.id)
    for args in [('bad','rubber',1,.6,.075),('flat','rubber',-1,.6,.075),('flat','rubber',1,0,.075)]:
        with pytest.raises(ValueError):editor.configure_gripper(*args)
    assert editor.blueprint==changed
    editor.undo();assert editor.blueprint==original


@pytest.mark.parametrize('name,scale',[('robot_arm_compact',.65),('robot_arm',1),('robot_arm_long',1.4)])
def test_arm_sizes_compile_with_scaled_reach(name,scale):
    bp=BY_ID[name].blueprint()
    upper=next(c for c in bp.components if c.id=='upper_arm')
    assert upper.geometry.size[0]==pytest.approx(.18*scale)
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    backend=MujocoBackend()
    backend.compile(Scene((Entity('arm',bp),)),.002)
    backend.step({});backend.close()


def test_mobile_arm_drives_and_moves_joint_without_changing_design():
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.entity import Entity
    from little_world.core.world import World
    from little_world.scenes.workshop import workshop_scene
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    bp=mobile_manipulator_blueprint()
    assert Blueprint.from_json(bp.to_json())==bp
    backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',bp))) as world:
        world.start();control=MujocoKeyboardControl(backend,bp)
        drive=next(c for c in bp.controllers if c.kind=='differential_torque')
        import numpy as np
        start=backend.data.body('machine/root').xpos.copy()
        control.press('R')
        for _ in range(500):
            commands=control.step_commands(world.timestep)
            for name in drive.actuators:
                actuator=backend.model.actuator('machine/'+name).id
                joint=backend.model.actuator_trnid[actuator,0]
                velocity=backend.data.qvel[backend.model.jnt_dofadr[joint]]
                limit=backend.model.actuator_ctrlrange[actuator,1]
                commands['machine/'+name]=max(-limit,min(limit,.3*(4-velocity)))
            world.step(commands)
        root=backend.data.body('machine/root')
        assert np.linalg.norm(root.xpos[:2]-start[:2])>.02
        assert root.xmat.reshape(3,3)[2,2]>.9
        shoulder=next(v for n,v in control.channels.items() if 'shoulder' in n)
        assert backend.data.qpos[shoulder[0]]>.15
        assert world.scene.entities[-1].blueprint==bp
        world.reset()
        assert backend.data.body('machine/root').xpos==pytest.approx(start)


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display')
def test_gripper_setup_ui_chain(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.robots.arm_lab import arm_lab_blueprint
    app=Workshop(tmp_path/'grip.json',arm_lab_blueprint())
    app.editor.select('two_finger_gripper_1_root')
    original=app.draw
    complete=False
    def click(label):
        original()
        button=next(b for b in app.buttons if b.label==label)
        assert button.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(button.x+button.width/2,button.y+button.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        while app.events:app.events.pop(0)()
    def draw():
        nonlocal complete
        click('Configure gripper');click('round');click('plastic')
        assert app.dialog['fields'][0][1]=='0.5'
        app.dialog['fields'][0][1]='0.35'
        app.dialog['fields'][1][1]='0.2'
        click('Apply')
        assert app.dialog is None
        app.save()
        bp=Blueprint.from_json(app.path.read_text())
        assert next(m for m in bp.materials if m.id.endswith('_contact')).sliding_friction==.35
        complete=True
        glfw.set_window_should_close(app.window,True)
    app.draw=draw
    app.run(seconds=3)
    assert complete


@pytest.mark.parametrize('shape',['flat','round','narrow'])
def test_gripper_contact_parameters_reach_solver(shape):
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    editor=AssemblyEditor(arm_lab_blueprint());editor.select('two_finger_gripper_1_root')
    editor.configure_gripper(shape,'rubber',1.7,.15,.06)
    backend=MujocoBackend()
    backend.compile(Scene((Entity('machine',editor.blueprint),)),.002)
    for side in ('left','right'):
        geom=backend.model.geom('machine/two_finger_gripper_1_finger_'+side+'_pad_geom')
        assert geom.friction[0]==pytest.approx(1.7)
        actuator=backend.model.actuator('machine/two_finger_gripper_1_finger_'+side+'_joint_motor')
        assert actuator.ctrlrange==pytest.approx((-.15,.15))
    backend.step({});backend.close()
