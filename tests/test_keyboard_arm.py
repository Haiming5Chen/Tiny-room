from dataclasses import replace
import pytest
from little_world.core.blueprint import Blueprint,ControllerSpec
from little_world.construction.editor import AssemblyEditor,starter_blueprint


def test_keyboard_binding_roundtrip_and_validation():
    editor=AssemblyEditor(starter_blueprint())
    editor.add_catalog('servo_module')
    defaults=editor.blueprint
    editor.bind_keys('Lift','R','V',30,8,.4)
    spec=editor.blueprint.controllers[-1]
    assert spec.kind=='keyboard_position' and spec.positive_key=='R'
    assert Blueprint.from_json(editor.blueprint.to_json())==editor.blueprint
    before=editor.blueprint
    for pos,neg in [('W','V'),('R','R'),('ENTER','V')]:
        with pytest.raises(ValueError): editor.bind_keys('Lift',pos,neg)
    assert editor.blueprint==before
    editor.undo(); assert editor.blueprint==defaults


def test_keyboard_control_targets_hold_clamp_and_clear():
    from little_world.control.keyboard import KeyboardPositionControl
    spec=ControllerSpec('lift','keyboard_position',('motor',),positive_key='R',negative_key='V',speed=30,kp=8,kd=.4)
    control=KeyboardPositionControl((spec,))
    observations={'motor':(0.,0.,-.5,.5,1.)}
    control.press('R')
    command=control.commands(observations,1.)
    assert command['motor']==1.
    assert control.targets['motor']==.5
    control.release('R')
    assert control.commands(observations,.1)['motor']==1.
    control.press('V');control.clear()
    assert not control.held and control.targets['motor']==.5
    control.reset()
    assert not control.targets


def test_arm_grasps_lifts_holds_and_releases_by_contact():
    pytest.importorskip('mujoco')
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.scenes.workshop import workshop_scene
    from little_world.core.entity import Entity
    from little_world.core.world import World
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    bp=arm_lab_blueprint()
    backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',bp))) as world:
        world.start()
        control=MujocoKeyboardControl(backend,bp)
        def advance(seconds):
            for _ in range(round(seconds/world.timestep)):
                world.step(control.step_commands(world.timestep))
            return float(backend.data.body('objects/grasp_cube').xpos[2])
        initial=advance(.5)
        control.press('G');advance(.9);control.release('G');advance(.2)
        control.press('R');advance(.8);control.release('R')
        lifted=advance(.6)
        assert lifted>initial+.09
        assert advance(.4)>initial+.09
        control.press('H');advance(1.);control.release('H')
        assert advance(.8)<.05
        assert backend.model.neq==0  # No hidden grasp constraints.
        world.reset();control.reset()
        assert not control.targets and not control.held
        assert world.scene.entities[-1].blueprint==bp


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display and OpenGL')
def test_keyboard_panel_edit_and_runtime_callbacks(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.robots.arm_lab import arm_lab_blueprint
    app=Workshop(tmp_path/'arm.json',arm_lab_blueprint())
    app.control_panel=True
    app.library_open=False
    original=app.draw
    tick=0
    def click(label):
        item=next(b for b in app.buttons if b.label==label)
        assert item.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(item.x+item.width/2,item.y+item.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        while app.events: app.events.pop(0)()
    def draw():
        nonlocal tick
        original();tick+=1
        if tick==1:
            click('R / V   Shoulder');original();click('Edit action')
            for i,value in enumerate(('Lift shoulder','U','J','20','18, 1')):
                app.dialog['focus']=i;app.dialog['replace']=True
                for c in value: app.character(app.window,ord(c))
            app.key(app.window,glfw.KEY_ENTER,0,glfw.PRESS,0)
            while app.events: app.events.pop(0)()
            assert app.dialog is None
            app.save()
            saved=Blueprint.from_json(app.path.read_text())
            assert next(c for c in saved.controllers if c.label=='Lift shoulder').positive_key=='U'
            original();click('Start simulation')
            app.key(app.window,glfw.KEY_U,0,glfw.PRESS,0)
            assert 'U' in app.joint_control.held
            app.key(app.window,glfw.KEY_U,0,glfw.RELEASE,0)
            assert not app.joint_control.held
            app.key(app.window,glfw.KEY_G,0,glfw.PRESS,0)
            app.key(app.window,glfw.KEY_P,0,glfw.PRESS,0)
            assert app.paused and not app.joint_control.held
            app.simulate()
            assert app.building and not app.joint_control.targets
            glfw.set_window_should_close(app.window,True)
    app.draw=draw
    app.run(seconds=3)
    assert tick==1
