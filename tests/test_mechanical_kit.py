from dataclasses import replace
import pytest
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor,starter_blueprint
from little_world.construction.docking import dock,sockets,poses
from little_world.construction.connections import rotate
from little_world.core.component import Body,Hinge,Motor


def test_four_wheel_mounts_orientation_and_drive_pairs():
    e=AssemblyEditor(starter_blueprint())
    for face in ('Left front','Right front','Left rear','Right rear'):
        assert sockets(e.blueprint,'drive_left','base')[face].valid
        dock(e,'drive_left','base',face)
        b=e.selected
        normal=rotate(b.transform.quaternion,(0,0,1))
        assert normal[1]*(1 if face.startswith('Left') else -1)>.99
        joint=e.selected_hinge()
        assert rotate(b.transform.quaternion,joint.axis)[1]>.99
    assert len([c for c in e.blueprint.controllers if c.kind=='differential_torque'])==2
    assert not sockets(e.blueprint,'drive_left','base')['Left front'].valid
    assert not sockets(e.blueprint,'drive_left','base')['Left'].valid # middle would overlap


def test_motor_output_is_discoverable_and_drives_load_without_extra_joint():
    e=AssemblyEditor(starter_blueprint());dock(e,'gearmotor_37','base','Top');motor=e.selection
    choices=sockets(e.blueprint,'drive_roller_60',motor)
    assert choices['output'].valid and choices['output'].body.endswith('output_shaft')
    before=len([c for c in e.blueprint.components if isinstance(c,Hinge)])
    dock(e,'drive_roller_60',motor,'output')
    assert e.selected.parent.endswith('output_shaft')
    assert len([c for c in e.blueprint.components if isinstance(c,Hinge)])==before
    assert not sockets(e.blueprint,'drive_roller_60',motor)['output'].valid


def test_big_wheels_cannot_overlap_adjacent_mounts():
    e=AssemblyEditor(starter_blueprint());dock(e,'drive_280','base','Left front')
    assert not sockets(e.blueprint,'drive_280','base')['Left rear'].valid


def test_open_chassis_uses_full_frame_for_wheel_mounts():
    e=AssemblyEditor(BY_ID['open_chassis'].blueprint())
    for face in ('Left front','Right front','Left rear','Right rear'):
        assert sockets(e.blueprint,'drive_100','root')[face].valid
        dock(e,'drive_100','root',face)
    wheels=[b for b in e.bodies if b.catalog_part=='drive_100']
    assert len(wheels)==4
    assert max(b.transform.position[1] for b in wheels)>.22
    assert min(b.transform.position[1] for b in wheels)<0


def test_four_wheel_drive_moves_with_all_motors_in_native_physics():
    pytest.importorskip('mujoco')
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.scenes.room import room_entity
    e=AssemblyEditor(starter_blueprint())
    for face in ('Left front','Right front','Left rear','Right rear'):dock(e,'drive_left','base',face)
    names=[a for c in e.blueprint.controllers for a in c.actuators]
    backend=MujocoBackend()
    with World(backend,Scene((room_entity(),Entity('machine',e.blueprint)))) as world:
        first=world.start();channels=[]
        for name in names:
            idx=backend.model.actuator('machine/'+name).id
            joint=backend.model.actuator_trnid[idx,0]
            channels.append((name,backend.model.jnt_dofadr[joint]))
        for _ in range(1000):
            last=world.step({'machine/'+name:max(-1,min(1,.3*(3-backend.data.qvel[dof]))) for name,dof in channels})
        assert last.bodies['machine/base'].pose.position[0]>first.bodies['machine/base'].pose.position[0]+.1
        assert all(backend.data.qvel[dof]>1 for name,dof in channels)


def test_motor_hub_load_chain_uses_one_actuator_joint():
    e=AssemblyEditor(starter_blueprint());dock(e,'gearmotor_37','base','Top')
    dock(e,'flange_hub',e.selection,'output')
    dock(e,'flywheel_80',e.selection,'output')
    assert e.selected.parent.startswith('flange_hub')
    assert len([c for c in e.blueprint.components if isinstance(c,Hinge)])==1
    assert len([c for c in e.blueprint.components if isinstance(c,Motor)])==1
    pytest.importorskip('mujoco')
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    motor=next(c.id for c in e.blueprint.components if isinstance(c,Motor))
    backend=MujocoBackend()
    with World(backend,Scene((Entity('machine',e.blueprint),))) as world:
        world.start()
        for _ in range(200):world.step({'machine/'+motor:.1})
        assert abs(backend.data.qpos[-1])>.1


def test_replacing_four_wheel_component_checks_spacing():
    from little_world.construction.component_changes import replace_component
    e=AssemblyEditor(starter_blueprint())
    dock(e,'drive_left','base','Left front');front=e.selection
    dock(e,'drive_left','base','Left rear')
    e.select(front);before=e.blueprint
    with pytest.raises(ValueError,match='occupied'):replace_component(e,'drive_280')
    assert e.blueprint==before


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_kit_guide_and_all_four_runtime_channels(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    e=AssemblyEditor(starter_blueprint())
    for face in ('Left front','Right front','Left rear','Right rear'):dock(e,'drive_left','base',face)
    app=Workshop(tmp_path/'four.json',e.blueprint);app.open_bench()
    app.catalog_selection='gearmotor_37'
    draw=app.draw;tick=0
    def exercise():
        nonlocal tick
        if tick==0:glfw.set_window_size(app.window,1040,740)
        draw();tick+=1
        assert len(app.channels)==4
        if tick==1:
            app.events.append(next(b.action for b in app.buttons if b.label=='Part guide'))
        elif tick==2:
            assert app.dialog['part_info']=='gearmotor_37'
            app.character(app.window,ord('a')) # informational forms ignore typing
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            app.events.append(next(b.action for b in app.buttons if b.label=='Find matching parts'))
        elif tick==3:
            assert app.dialog is None
            assert len(app.parts_items())==10 and app.parts_query=='shaft-driven'
            app.simulate();assert len(app.channels)==4
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==3


def test_moving_a_paired_wheel_to_same_side_removes_invalid_drive_pair():
    e=AssemblyEditor(starter_blueprint())
    dock(e,'drive_left','base','Left front');name=e.selection
    dock(e,'drive_left','base','Right rear')
    assert len(e.blueprint.controllers)==1
    dock(e,'drive_left','base','Right front',moving=name)
    assert not e.blueprint.controllers
    dock(e,'drive_left','base','Left front',moving=name)
    assert len(e.blueprint.controllers)==1
