import pytest
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor,starter_blueprint
from little_world.core.component import Motor,Camera


def test_simple_library_keeps_raw_hardware_in_advanced():
    from little_world.assets.ready_assemblies import is_ready
    assert not is_ready(BY_ID['gearmotor_37'])
    assert not is_ready(BY_ID['bolt_m4'])
    assert not is_ready(BY_ID['shaft_coupler'])
    assert is_ready(BY_ID['drive_left'])
    assert is_ready(BY_ID['ready_rover_4'])


@pytest.mark.parametrize('item,count',[('ready_rover_4',4),('ready_rover_6',6),('ready_delivery_base',2)])
def test_complete_base_installs_with_all_drive_controls_and_undo(item,count):
    e=AssemblyEditor(starter_blueprint());before=e.blueprint
    e.add_catalog(item,'Floor')
    assert sum(len(c.actuators) for c in e.blueprint.controllers if c.kind=='differential_torque')==count
    assert len(e.past)==1
    e.undo();assert e.blueprint==before


@pytest.mark.parametrize('item',['ready_pick_arm_compact','ready_pick_arm_standard','ready_pick_arm_long'])
def test_pick_arm_includes_gripper_and_default_controls(item):
    e=AssemblyEditor(starter_blueprint());e.add_catalog(item)
    assert len([c for c in e.blueprint.components if isinstance(c,Motor)])==6
    assert len(e.blueprint.controllers)==5
    assert any(c.positive_key=='G' for c in e.blueprint.controllers)


@pytest.mark.parametrize('item',['ready_fork','ready_scoop','ready_cargo_tray','ready_pan_tilt'])
def test_complete_attachment_has_editable_motor_and_defaults(item):
    e=AssemblyEditor(starter_blueprint());e.add_catalog(item)
    assert e.blueprint.controllers
    if item=='ready_pan_tilt':assert any(isinstance(c,Camera) for c in e.blueprint.components)


@pytest.mark.parametrize('item',['ready_fork','ready_scoop','ready_cargo_tray','ready_pan_tilt'])
def test_attachment_motor_actually_moves_in_native_physics(item):
    pytest.importorskip('mujoco')
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    e=AssemblyEditor(starter_blueprint());e.add_catalog(item)
    backend=MujocoBackend()
    with World(backend,Scene((Entity('machine',e.blueprint),))) as world:
        world.start();control=MujocoKeyboardControl(backend,e.blueprint)
        control.press(control.specs[0].positive_key)
        for _ in range(400):world.step(control.step_commands(world.timestep))
        motor=control.specs[0].actuators[0]
        assert backend.data.qpos[control.channels[motor][0]]>.05


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_ready_library_scope_and_drop_complete_base(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'ready.json',starter_blueprint());app.open_bench()
    draw=app.draw;tick=0;before=app.editor.blueprint
    def mouse(x,y,action):
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(x,y))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,action,0)
    def exercise():
        nonlocal tick
        draw();tick+=1
        if tick==1:
            assert 'gearmotor_37' not in {p.id for p in app.parts_items()}
            row=next(r for r in app.catalog_rows if r[0]=='ready_rover_4')
            mouse(row[1]+40,row[2]+60,glfw.PRESS)
            app.mouse_move(app.window,600,350)
            mouse(600,350,glfw.RELEASE)
        elif tick==2:
            assert len(app.channels)==4
            assert app.editor.selected.catalog_part=='ready_rover_4'
            app.edit(app.editor.undo);assert app.editor.blueprint==before
            b=next(b for b in app.buttons if b.label=='Advanced')
            mouse(b.x+20,b.y+12,glfw.PRESS)
        elif tick==3:
            assert not app.bench_hardware
            app.parts_input('gearmotor')
            assert any(p.id=='gearmotor_37' for p in app.parts_items())
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==3
