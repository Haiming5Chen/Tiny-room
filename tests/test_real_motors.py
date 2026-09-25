from dataclasses import replace
from math import pi
import pytest
from little_world.assets.real_motors import PROFILES
from little_world.core.blueprint import Blueprint
from little_world.core.component import Motor


def test_envelope_direction_speed_and_braking():
    p=next(iter(PROFILES.values()));w=p.no_load_rpm*2*pi/60
    assert p.constrain(2.,0,2.)==2.
    assert p.constrain(2.,w*.5,2.)==pytest.approx(1.25)
    assert p.constrain(2.,w,2.)==0
    assert p.constrain(-2.,-w*.5,2.)==pytest.approx(-1.25)
    assert p.constrain(-2.,w,2.)==-2.
    assert p.constrain(2.,0,.5)==.5
    with pytest.raises(ValueError):replace(p,no_load_rpm=float('nan'))


def test_profile_edit_roundtrip_undo_and_old_json():
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.construction.editor import AssemblyEditor
    import json
    editor=AssemblyEditor(arm_lab_blueprint());editor.select('robot_arm_1_upper_arm')
    original=editor.blueprint
    profile=next(iter(PROFILES.values()))
    editor.set_motor_profile(profile,.75)
    assert editor.selected_motors()[0].profile==profile
    assert Blueprint.from_json(editor.blueprint.to_json())==editor.blueprint
    with pytest.raises(ValueError):editor.set_motor(3.)
    editor.undo();assert editor.blueprint==original
    raw=json.loads(original.to_json())
    for c in raw['components']:
        if c['kind']=='motor':c.pop('profile',None)
    assert Blueprint.from_json(json.dumps(raw))==original


def test_backend_enforces_envelope_for_direct_commands():
    from little_world.core.component import Body,Geometry,Hinge
    from little_world.materials import METAL
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    p=next(iter(PROFILES.values()))
    bp=Blueprint((Body('body',Geometry('box',(.1,.1,.1)),'metal'),Hinge('joint','body'),Motor('motor','joint',2.,p)),(METAL,))
    backend=MujocoBackend();backend.compile(Scene((Entity('robot',bp),)),.002)
    backend.data.qvel[0]=p.no_load_rpm*2*pi/60*.5
    backend.step({'robot/motor':2.})
    assert backend.data.ctrl[0]==pytest.approx(1.25)
    backend.reset();assert backend.data.qvel[0]==0
    backend.step({'robot/motor':2.});assert backend.data.ctrl[0]==2.
    backend.close()


def test_report_separates_candidates_from_custom_parts():
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.construction.editor import AssemblyEditor
    from little_world.construction.build_report import build_report
    import csv,io
    editor=AssemblyEditor(arm_lab_blueprint());editor.select('robot_arm_1_upper_arm')
    editor.set_motor_profile(next(iter(PROFILES.values())),.75)
    rows=list(csv.DictReader(io.StringIO(build_report(editor.blueprint))))
    assigned=[r for r in rows if r['candidate_model'].startswith('ROBOTIS')]
    assert len(assigned)==1 and assigned[0]['source'].startswith('https://emanual.robotis.com/')
    assert 'not measured' in assigned[0]['evidence']
    assert any(r['candidate_model']=='Unassigned' for r in rows)
    assert all(r['candidate_model']=='Custom / no vendor part' for r in rows if r['type']=='custom geometry')


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display')
def test_motor_profile_ui_and_export(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.robots.arm_lab import arm_lab_blueprint
    app=Workshop(tmp_path/'robot.json',arm_lab_blueprint())
    app.editor.select('robot_arm_1_upper_arm');app.active_tab='Connect'
    original=app.draw
    done=False
    def click(label):
        original()
        item=next(b for b in app.buttons if b.label==label)
        assert item.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(item.x+item.width/2,item.y+item.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        while app.events:app.events.pop(0)()
    def draw():
        nonlocal done
        click('Choose motor model');click('XH430-W210 / 12 V');click('Apply')
        assert app.editor.selected_motors()[0].profile.model=='ROBOTIS XH430-W210'
        app.save();app.active_tab='Files';click('Export parts / assumptions')
        assert app.path.with_suffix('.parts.csv').exists()
        app.simulate();app.key(app.window,glfw.KEY_R,0,glfw.PRESS,0)
        for _ in range(10):app.state=app.world.step(app.joint_commands())
        app.simulate()
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=draw;app.run(seconds=3)
    assert done


def test_real_profiles_produce_different_native_speed_limits():
    from little_world.core.component import Body,Geometry,Hinge
    from little_world.materials import METAL
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    speeds=[]
    # The two ROBOTIS servos this was written for. The Pololu gearmotors (ADR 0011) spin
    # 30x faster and are checked against their own free speed in test_drivetrain.
    for profile in (PROFILES['XH430-W210 / 12 V'],PROFILES['XH430-W350 / 12 V']):
        cap=profile.stall_torque*.3
        bp=Blueprint((Body('rotor',Geometry('box',(.1,.1,.1)),'metal'),
                      Hinge('joint','rotor',damping=0),Motor('motor','joint',cap,profile)),(METAL,))
        backend=MujocoBackend();backend.compile(Scene((Entity('test',bp),)),.0001)
        for _ in range(2000):backend.step({'test/motor':cap})
        speeds.append(float(backend.data.qvel[0]))
        assert backend.data.qvel[0]==pytest.approx(profile.no_load_rpm*2*pi/60,rel=.01)
        backend.close()
    assert speeds[0]>speeds[1]*1.5
