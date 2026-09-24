import pytest
from little_world.assets.catalog import CATALOG
from little_world.construction.editor import AssemblyEditor,starter_blueprint


@pytest.mark.parametrize('item',[p.id for p in CATALOG if p.variant in ('hw_arm','hw_arm_compact','hw_arm_long')])
def test_every_arm_size_has_editable_default_controls(item):
    e=AssemblyEditor(starter_blueprint());before=e.blueprint;e.add_catalog(item)
    controls=[c for c in e.blueprint.controllers if c.kind=='keyboard_position']
    assert {(c.positive_key,c.negative_key) for c in controls}=={('Q','E'),('R','V'),('T','B'),('Y','N')}
    assert len({a for c in controls for a in c.actuators})==4
    e.undo();assert e.blueprint==before


def test_continuous_mounting_six_wheels_and_collision_feedback():
    from little_world.scripting import RobotBuilder
    robot=RobotBuilder.chassis(length=.65,width=.24,height=.04)
    for side in ('Left','Right'):
        for x in (-.21,0,.21):robot.wheel('drive_100',side=side,x=x)
    assert sum(len(c.actuators) for c in robot.blueprint.controllers)==6
    before=robot.blueprint
    with pytest.raises(ValueError,match='overlap'):robot.wheel('drive_100',side='Left',x=.03)
    assert robot.blueprint==before


def test_drive_assist_ramps_and_respects_each_torque_limit():
    from little_world.control.drive_assist import DriveAssist
    from little_world.core.drive_settings import DriveSettings
    drive=DriveAssist()
    observations={'a':(0.,.05,.2,0.),'b':(0.,.1,2.,0.)}
    targets={'a':.5,'b':.5}
    settings=DriveSettings(acceleration=.5,torque_fraction=.5)
    commands=drive.commands(targets,observations,.1,settings)
    assert drive.targets['a']==pytest.approx(.05)
    assert 0<commands['a']<=.1 and 0<commands['b']<=1.
    for _ in range(20):drive.commands(targets,observations,.1,settings)
    assert drive.targets['a']==pytest.approx(.5)


def test_python_build_success_error_and_timeout(tmp_path):
    from little_world.scripting.runner import run_script
    source='from little_world.scripting import RobotBuilder\nr = RobotBuilder.chassis(length=.6)\nr.wheel("drive_100", side="Left", x=.2)\nblueprint = r.blueprint'
    result=run_script(source,starter_blueprint(),timeout=5)
    assert result.components
    with pytest.raises(ValueError,match='SyntaxError'):run_script('if :',starter_blueprint(),timeout=5)
    with pytest.raises(TimeoutError):run_script('while True: pass',starter_blueprint(),timeout=.2)


def test_passive_wheels_on_separate_side_motors_get_automatic_drive():
    from little_world.construction.docking import dock
    e=AssemblyEditor(starter_blueprint())
    for side in ('Left','Right'):
        dock(e,'gearmotor_37','base',side)
        dock(e,'wheel_100',e.selection,'output')
    drives=[c for c in e.blueprint.controllers if c.kind=='differential_torque']
    assert len(drives)==1 and len(drives[0].actuators)==2
    assert all('gearmotor' in a for a in drives[0].actuators)


def test_unmatched_extra_motor_is_controlled_and_settings_roundtrip():
    from little_world.scripting import RobotBuilder
    from little_world.core.blueprint import Blueprint
    robot=RobotBuilder.chassis(length=.65)
    for side,x in (('Left',-.2),('Right',-.2),('Left',.2)):
        robot.wheel('drive_100',side=side,x=x)
    robot.drive(max_speed=.3,torque_fraction=.6)
    specs=robot.blueprint.controllers
    assert sum(len(c.actuators) for c in specs)==3
    assert all(c.drive_settings.max_speed==.3 for c in specs)
    assert Blueprint.from_json(robot.blueprint.to_json())==robot.blueprint


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_python_window_build_error_undo_and_drive_settings(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'python.json',starter_blueprint())
    draw=app.draw;phase=0;original=app.editor.blueprint;built=None
    def click(label):
        b=next(b for b in app.buttons if b.label==label);assert b.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(b.x+b.width/2,b.y+b.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
    def exercise():
        nonlocal phase,built
        if phase==0:glfw.set_window_size(app.window,1040,740)
        draw()
        if phase==0:click('Python');phase=1
        elif phase==1:
            assert app.script_open
            click('Run build');phase=2
        elif phase==2 and app.script_future is None:
            assert 'Applied' in app.script_output,app.script_output
            assert len(app.channels)==6
            built=app.editor.blueprint
            click('Save script');phase=3
        elif phase==3:
            assert app.script_path.exists()
            app.key(app.window,glfw.KEY_A,0,glfw.PRESS,glfw.MOD_SUPER)
            monkeypatch.setattr(glfw,'get_clipboard_string',lambda w:b'blueprint = None')
            app.key(app.window,glfw.KEY_V,0,glfw.PRESS,glfw.MOD_SUPER)
            assert app.script_text=='blueprint = None'
            click('Run build');phase=4
        elif phase==4 and app.script_future is None:
            assert 'Assign the finished design' in app.script_output
            assert app.editor.blueprint==built
            click('Undo build');phase=5
        elif phase==5:
            assert app.editor.blueprint==original
            app.edit(app.editor.redo)
            click('View build');phase=6
        elif phase==6:
            assert app.bench_open and not app.script_open
            click('Drive assist');phase=7
        elif phase==7:click('Gentle');phase=8
        elif phase==8:
            assert all(c.drive_settings.torque_fraction==.5 for c in app.editor.blueprint.controllers)
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=15)
    assert phase==8


def test_removed_default_binding_stays_removed_when_adding_unrelated_part():
    e=AssemblyEditor(starter_blueprint());e.add_catalog('robot_arm_compact')
    spec=e.blueprint.controllers[0];e.remove_binding(spec.id)
    e.select('base');e.add_catalog('camera_module')
    assert all(c.id!=spec.id for c in e.blueprint.controllers)


def test_clearance_is_adjustable_without_allowing_overlapping_tires():
    from little_world.scripting import RobotBuilder
    robot=RobotBuilder.chassis(length=.65)
    robot.wheel('wheel_100',side='Left',x=0)
    robot.wheel('wheel_100',side='Left',x=.101,clearance=0)
    with pytest.raises(ValueError,match='overlap'):robot.wheel('wheel_100',side='Left',x=-.099,clearance=0)


def test_drive_assist_traction_only_limits_accelerating_overspeed():
    from little_world.control.drive_assist import DriveAssist
    from little_world.core.drive_settings import DriveSettings
    assisted=DriveAssist();raw=DriveAssist()
    settings=DriveSettings(acceleration=10,gain=2)
    observations={'wheel':(20.,.05,1.,0.)}
    aided=assisted.commands({'wheel':2.},observations,1.,settings)['wheel']
    unlimited=raw.commands({'wheel':2.},observations,1.,DriveSettings(acceleration=10,gain=2,traction=False))['wheel']
    assert 0<aided<unlimited
    braking=assisted.commands({'wheel':0.},observations,1.,settings)['wheel']
    assert braking==-1.


def test_native_assisted_drive_runs_all_five_motors_with_individual_caps():
    pytest.importorskip('mujoco')
    from little_world.scripting import RobotBuilder
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.scenes.room import room_entity
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_drive import MujocoDrive
    robot=RobotBuilder.chassis(length=.65)
    for side,positions in (('Left',(-.21,0,.21)),('Right',(-.21,.21))):
        for x in positions:robot.wheel('drive_100',side=side,x=x)
    robot.drive(max_speed=.3,acceleration=.5,torque_fraction=.6)
    backend=MujocoBackend()
    with World(backend,Scene((room_entity(),Entity('machine',robot.blueprint)))) as world:
        start=world.start();control=MujocoDrive(backend,robot.blueprint)
        assert len(control.channels)==5
        for _ in range(1000):
            commands=control.step_commands((5,5),world.timestep)
            assert len(commands)==5 and all(abs(v)<=.6 for v in commands.values())
            end=world.step(commands)
        assert end.bodies['machine/chassis'].pose.position[0]>start.bodies['machine/chassis'].pose.position[0]+.1
        assert all(backend.data.qvel[c[1]]>1 for c in control.channels)


def test_native_drive_caps_turn_speed_and_preserves_program_angular_units():
    pytest.importorskip('mujoco')
    from little_world.scripting import RobotBuilder
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.control.mujoco_drive import MujocoDrive
    robot=RobotBuilder.chassis()
    for side in ('Left','Right'):robot.wheel('drive_100',side=side)
    robot.drive(max_speed=.5,acceleration=10)
    backend=MujocoBackend()
    with World(backend,Scene((Entity('machine',robot.blueprint),))) as world:
        world.start();control=MujocoDrive(backend,robot.blueprint)
        control.step_commands((7.5,7.5),1.)
        assert all(v==pytest.approx(.5) for v in control.assist.targets.values())
        control.step_commands((3,3),1.,angular=True)
        assert all(v==pytest.approx(.15) for v in control.assist.targets.values())
