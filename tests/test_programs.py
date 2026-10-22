import pytest
from little_world.programming.program import Program,Block,Runner


def test_program_roundtrip_timing_repeat_step():
    p=Program((Block('action','lift',1,.1),Block(duration=.1)),2)
    assert Program.from_json(p.to_json())==p
    r=Runner();r.start(p,single=True)
    assert r.tick(.1)['action']==('lift',1)
    assert r.state=='paused' and r.index==1
    r.state='running';r.single=False
    r.tick(.1);assert r.cycle==1 and r.index==0
    r.tick(.1);r.tick(.1);assert r.state=='completed'
    assert r.tick(.1)['action'] is None
    with pytest.raises(ValueError):Block(duration=float('nan'))


def test_program_stale_action_rejected():
    from little_world.robots.arm_lab import arm_lab_blueprint
    with pytest.raises(ValueError):Program((Block('action','missing',1),)).validate(arm_lab_blueprint())


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display')
def test_program_workspace_pickup_save_step_and_drag(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.robots.arm_lab import arm_lab_blueprint
    app=Workshop(tmp_path/'robot.json',arm_lab_blueprint());app.show_program();app.pickup_program()
    draw_original=app.draw;done=False
    def draw():
        nonlocal done
        draw_original()
        original=app.program
        a,b=app.program_rows[0],app.program_rows[1]
        app.program_mouse(a[1]+5,a[2]+5,glfw.PRESS)
        app.program_mouse(b[1]+5,b[2]+5,glfw.RELEASE)
        while app.events:app.events.pop(0)()
        assert app.program.blocks[0]==original.blocks[1]
        app.program_undo();assert app.program==original
        app.save_program();assert Program.from_json(app.program_path.read_text())==original
        app.start_program(True)
        for _ in range(250):app.tick_program();app.state=app.world.step(app.joint_commands())
        assert app.runner.state=='paused' and app.runner.index==1 and app.paused
        app.stop_program();app.simulate();app.start_program()
        start=float(app.data.body('objects/grasp_cube').xpos[2])
        peak=0
        for _ in range(2500):
            app.tick_program();app.state=app.world.step(app.joint_commands())
            peak=max(peak,float(app.data.body('objects/grasp_cube').xpos[2]))
        assert app.runner.state=='completed' and peak>.30
        # Released and back down, wherever it lands: back on the stand or beside it is a
        # millimetre-scale coin toss that differs between platforms (test_keyboard_arm).
        assert app.data.body('objects/grasp_cube').xpos[2]<start+.01
        assert not app.program_keys
        app.simulate();assert app.building
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=draw;app.run(seconds=5);assert done


def test_guided_arm_is_atomic_and_keeps_wheel_controls():
    from little_world.construction.editor import AssemblyEditor,starter_blueprint
    from little_world.construction.guidance import add_suggested,build_checks
    e=AssemblyEditor(starter_blueprint());original=e.blueprint
    add_suggested(e,'robot_arm_compact')
    assert len(e.blueprint.controllers)==5
    assert len(e.past)==1
    assert not any('no keyboard' in c for c in build_checks(e.blueprint))
    e.undo();assert e.blueprint==original


def test_conditions_branch_move_and_timeout():
    p=Program((Block('if_contact','a',other='b'),Block('action','lift',1),Block('distance','a',.1,.2,'b')))
    r=Runner();r.start(p);r.tick(.01,contacts=());assert r.index==2
    r.tick(.1,distances={('a','b'):.2});r.tick(.1,distances={('a','b'):.2})
    assert r.state=='failed'
    r.start(Program((Block('contact','a',other='b'),Block('move','lift',20))))
    r.tick(.01,contacts={frozenset(('a','b'))});assert r.index==1
    r.tick(.01,angles={'lift':(19.,20.)});assert r.state=='completed'


def test_native_contact_distance_and_bilateral_observations():
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.entity import Entity
    from little_world.core.world import World
    from little_world.scenes.workshop import workshop_scene
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.programming.observations import Observations
    bp=arm_lab_blueprint();backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',bp))) as world:
        world.start();control=MujocoKeyboardControl(backend,bp);obs=Observations(backend.model,backend.data)
        for _ in range(250):world.step(control.step_commands(world.timestep))
        control.press('G')
        for _ in range(450):world.step(control.step_commands(world.timestep))
        assert 'objects/grasp_cube' in obs.grasped()
        a='machine/two_finger_gripper_1_finger_left_pad';b='objects/grasp_cube'
        assert frozenset((a,b)) in obs.contact_pairs()
        assert 0<obs.distance(a,b)<.1


@pytest.mark.parametrize('family',['Compact arm kit','Standard arm kit','Long reach arm kit'])
def test_matched_arm_family_mounts_and_controls(family):
    from little_world.robots.arm_family import arm_family_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.core.blueprint import Blueprint
    bp=arm_family_blueprint(family)
    assert Blueprint.from_json(bp.to_json())==bp and len(bp.controllers)==5
    backend=MujocoBackend();backend.compile(Scene((Entity('kit',bp),)),.002)
    import numpy as np
    bodies=[c for c in bp.components if hasattr(c,'attachments')]
    wrist=next(c for c in bodies if c.id.endswith('_wrist'))
    gripper=next(c for c in bodies if c.id.endswith('_root') and ('gripper' in c.id))
    def frame_position(body,label):
        frame=next(a for a in body.attachments if a.id==label)
        native=backend.data.body('kit/'+body.id)
        return native.xpos+native.xmat.reshape(3,3)@np.array(frame.transform.position)
    assert frame_position(wrist,'tool')==pytest.approx(frame_position(gripper,'tool_mount'))
    backend.step({});backend.close()


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display')
def test_guided_test_workspace_and_sensor_block_editor(tmp_path,monkeypatch):
    import glfw,json
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'flow.json');draw_original=app.draw;done=False
    def click(label):
        draw_original()
        b=next(b for b in reversed(app.buttons) if b.label==label)
        assert b.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(b.x+b.width/2,b.y+b.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        while app.events:app.events.pop(0)()
    def draw():
        nonlocal done
        # The Guide opens on the first hour's lessons (ADR 0046); the starter kits are a click away.
        app.show_guide();click('Build help: starter kits and checks');click('Tabletop pickup')
        app.show_program();click('Add');click('contact')
        # Choose through native modal buttons, exercising chained sensor forms.
        a='machine/two_finger_gripper_1_finger_left_pad';b='objects/grasp_cube'
        app.dialog['fields'][0][1]=a;click(a)
        app.dialog['fields'][0][1]=b;click(b);click('Apply')
        assert app.program.blocks[0].kind=='contact'
        app.show_test();draw_original();click('Export test snapshot')
        report=json.loads(app.path.with_suffix('.test.json').read_text())
        assert len(report['joints'])==6 and report['root_tilt_deg']==0
        app.show_guide();click('Matched arm families');click('Compact arm kit')
        assert any(c.id.startswith('gripper_compact') for c in app.editor.blueprint.components)
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=draw;app.run(seconds=5);assert done
