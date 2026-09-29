"""Contracts for guided docking and wheel-ready chassis edits."""
from dataclasses import replace
import pytest
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.robots.arm_lab import arm_lab_blueprint


def test_wheels_release_raise_pedestal_and_preserve_arm_controls():
    from little_world.construction.docking import world_bounds
    editor=AssemblyEditor(arm_lab_blueprint())
    original=editor.blueprint
    editor.select('pedestal');editor.add_catalog('drive_left')
    editor.select('pedestal');editor.add_catalog('drive_right')
    base=next(b for b in editor.bodies if b.id=='pedestal')
    assert base.dynamic and base.transform.position[2]>.11
    assert world_bounds(editor.blueprint)[0][2]>=.0019
    assert all(c in editor.blueprint.controllers for c in original.controllers)
    drive=[c for c in editor.blueprint.controllers if c.kind=='differential_torque']
    assert len(drive)==1 and drive[0].actuators[0].startswith('left_wheel')
    editor.undo();editor.undo()
    assert editor.blueprint==original


def test_docking_rejects_incompatible_and_occupied_slots_atomically():
    from little_world.construction.docking import dock, sockets
    editor=AssemblyEditor(starter_blueprint())
    original=editor.blueprint
    choices=sockets(original,'drive_left','base')
    assert choices['Left'].valid
    assert not choices['Top'].valid
    with pytest.raises(ValueError,match='side'):
        dock(editor,'drive_left','base','Top')
    assert editor.blueprint==original and not editor.past
    dock(editor,'drive_left','base','Left')
    assert not sockets(editor.blueprint,'drive_left','base')['Left'].valid
    assert sockets(editor.blueprint,'drive_right','base')['Right'].valid
    with pytest.raises(ValueError,match='occupied'):
        dock(editor,'drive_left','base','Left')


def test_existing_part_drag_moves_subtree_in_one_undo():
    from little_world.construction.docking import dock, sockets
    editor=AssemblyEditor(starter_blueprint())
    dock(editor,'drive_left','base','Left')
    name=editor.selection;before=editor.blueprint;history=len(editor.past)
    dock(editor,'drive_left','base','Right',moving=name)
    moved=editor.selected
    assert moved.id==name and moved.transform.position[1]<0
    assert len(editor.past)==history+1
    assert not sockets(editor.blueprint,'drive_left',name,moving=name)['Left'].valid
    editor.undo();assert editor.blueprint==before


def test_passive_wheels_are_not_given_motors():
    from little_world.core.component import Motor
    editor=AssemblyEditor(starter_blueprint())
    editor.add_catalog('wheel_small')
    assert not any(isinstance(c,Motor) for c in editor.blueprint.components)


def test_ground_clearance_respects_rotated_shapes():
    from little_world.construction.docking import world_bounds, prepare_base
    from little_world.construction.connections import euler_quaternion
    bp=starter_blueprint()
    b=bp.components[0]
    bp=replace(bp,components=(replace(b,transform=replace(b.transform,quaternion=euler_quaternion((20,35,0)))),))
    editor=AssemblyEditor(bp);prepare_base(editor,'base',True)
    assert world_bounds(editor.blueprint)[0][2]==pytest.approx(.002)
    assert editor.selected.dynamic
    editor.undo();assert editor.blueprint==bp


def test_powered_wheels_on_arm_pedestal_move_without_deep_floor_penetration():
    mj=pytest.importorskip('mujoco')
    from little_world import World, Entity
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.scenes.workshop import workshop_scene
    editor=AssemblyEditor(arm_lab_blueprint())
    for side in ('drive_left','drive_right'):
        editor.select('pedestal');editor.add_catalog(side)
    # Fore/aft support stabilizes a tall, front-heavy robot on a two-wheel axle.
    for x in (-.07,.07):
        editor.select('pedestal');editor.add_catalog('skid_foot');editor.move((x,0,0))
    drive=next(c for c in editor.blueprint.controllers if c.kind=='differential_torque')
    backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',editor.blueprint))) as world:
        first=world.start();start=first.bodies['machine/pedestal'].pose.position
        deepest=0
        for _ in range(750):
            commands={'machine/'+name:.45 for name in drive.actuators}
            last=world.step(commands)
            for c in backend.data.contact[:backend.data.ncon]:
                names=[backend.model.geom(i).name for i in (c.geom1,c.geom2)]
                if any('floor' in n for n in names) and any('wheel' in n for n in names):deepest=min(deepest,c.dist)
        assert abs(last.bodies['machine/pedestal'].pose.position[0]-start[0])>.02
        assert deepest>-.005


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_drag_drop_valid_invalid_and_existing_part(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'drag.json',starter_blueprint());app.open_bench()
    app.catalog_selection='drive_left';app.bench_hardware=False;app.bench_offset=10
    draw=app.draw;tick=0;added=None
    def mouse(x,y,action):
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(x,y))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,action,0)
    def drop(face):
        draw()  # sockets appear contextually once a drag starts
        s,x,y,w,h=next(r for r in app.socket_regions if r[0].face==face)
        app.mouse_move(app.window,x+w/2,y+h/2)
        draw()  # translucent preview is rendered before release
        mouse(x+w/2,y+h/2,glfw.RELEASE)
    def exercise():
        nonlocal tick,added
        draw();tick+=1
        if tick==1:
            row=next(r for r in app.catalog_rows if r[0]=='drive_left')
            mouse(row[1]+10,row[2]+10,glfw.PRESS)
            drop('Top')
            assert not app.editor.past and 'side' in app.status
        elif tick==2:
            row=next(r for r in app.catalog_rows if r[0]=='drive_left')
            mouse(row[1]+10,row[2]+10,glfw.PRESS);drop('Left')
        elif tick==3:
            added=app.editor.blueprint
            assert len(app.editor.past)==1 and app.editor.selected.parent=='base'
            name=app.editor.selection
            # The actual picking result determines which existing module is dragged.
            monkeypatch.setattr(app,'pick_bench_body',lambda x,y:name)
            mouse(500,350,glfw.PRESS);drop('Right')
        elif tick==4:
            assert len(app.editor.past)==2 and app.editor.selected.transform.position[1]<0
            app.edit(app.editor.undo)
            assert app.editor.blueprint==added
            app.save();app.load();assert app.editor.blueprint==added
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==4


def test_prepare_base_repairs_legacy_unbound_drive_pair():
    from little_world.construction.docking import prepare_base
    editor=AssemblyEditor(arm_lab_blueprint())
    for part in ('drive_left','drive_right'):
        editor.select('pedestal');editor.add_catalog(part)
    editor.blueprint=replace(editor.blueprint,controllers=tuple(c for c in editor.blueprint.controllers if c.kind!='differential_torque'))
    before=editor.blueprint
    prepare_base(editor,'pedestal',True)
    assert len(editor.blueprint.controllers)==len(before.controllers)+1
    assert all(c in editor.blueprint.controllers for c in before.controllers)
    editor.undo();assert editor.blueprint==before


def test_tool_socket_and_output_wheel_coupling():
    from little_world.construction.docking import dock, sockets
    from little_world.core.component import Hinge
    editor=AssemblyEditor(arm_lab_blueprint())
    gripper=next(b.id for b in editor.bodies if b.id.startswith('two_finger_gripper') and b.id.endswith('_root'))
    editor.select(gripper);editor.delete()
    wrist='robot_arm_1_wrist'
    assert sockets(editor.blueprint,'two_finger_gripper',wrist)['tool'].valid
    dock(editor,'two_finger_gripper',wrist,'tool')
    assert not sockets(editor.blueprint,'two_finger_gripper',wrist)['tool'].valid
    editor=AssemblyEditor(starter_blueprint())
    dock(editor,'gearmotor_37','base','Top')
    shaft=editor.selection.removesuffix('_root')+'_output_shaft'
    dock(editor,'tread_wheel',shaft,'output')
    wheel=editor.selection
    assert not any(isinstance(c,Hinge) and c.body==wheel for c in editor.blueprint.components)
    dock(editor,'tread_wheel','base','Left',moving=wheel)
    assert any(isinstance(c,Hinge) and c.body==wheel for c in editor.blueprint.components)


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_immersive_stage_panels_and_contextual_sockets(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'immersive.json',starter_blueprint());app.open_bench()
    draw=app.draw;tick=0;wide=None;original=app.editor.blueprint
    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        app.events.append(b.action)
    def exercise():
        nonlocal tick,wide
        if tick==0:glfw.set_window_size(app.window,1040,740)
        draw();tick+=1
        w,h=glfw.get_window_size(app.window)
        assert all(0<=b.x and b.x+b.width<=w and b.y+b.height<=h-32 for b in app.buttons)
        for i,a in enumerate(app.buttons):
            for b in app.buttons[i+1:]:
                assert not (a.x<b.x+b.width and b.x<a.x+a.width and a.y<b.y+b.height and b.y<a.y+a.height),(a.label,b.label)
        if tick==1:
            assert not app.bench_details and not app.socket_regions
            wide=app.bench_rect[2]
            click('Hide parts')
        elif tick==2:
            assert app.bench_rect[2]>wide and not app.catalog_rows
            click('Details')
        elif tick==3:
            assert app.bench_details and app.bench_part_rect
            click('Hide details')
        elif tick==4:
            assert not app.bench_details
            click('Sockets')
        elif tick==5:
            assert app.socket_regions
            click('Frame all')
        elif tick==6:
            assert app.editor.blueprint==original
            assert not app.editor.past
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==6


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_drag_both_wheels_from_cards_without_inspector(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'two-sides.json',starter_blueprint());app.open_bench();app.parts_input('drive')
    draw=app.draw;tick=0;before=app.editor.blueprint
    def pointer(x,y,action):
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(x,y))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,action,0)
    def start():
        _,x,y,w,h=next(r for r in app.catalog_rows if r[0]=='drive_left')
        assert h>=100  # the illustration and parameters belong to the drag target
        pointer(x+40,y+65,glfw.PRESS)
        draw()
    def drop(face):
        _,x,y,w,h=next(r for r in app.socket_regions if r[0].face==face)
        app.mouse_move(app.window,x+w/2,y+h/2);draw()
        pointer(x+w/2,y+h/2,glfw.RELEASE)
    def exercise():
        nonlocal tick
        draw();tick+=1
        assert not app.bench_details
        if tick==1:start();drop('Left')
        elif tick==2:
            assert app.bench_target=='base' and app.catalog_mount=='Right'
            start()
            # Crossing the newly installed wheel must not replace the chassis
            # target with a wheel which has no compatible side sockets.
            name=app.editor.selection
            center=app.data.body('machine/'+name).xpos
            crossing=None
            cx,cy=app.project_socket(center)
            for dx in range(-100,101,8):
                for dy in range(-110,111,8):
                    point=(cx+dx,cy+dy)
                    if app.socket_at(*point) is None and (app.pick_bench_body(*point) or '').startswith('left_wheel'):
                        crossing=point;break
                if crossing:break
            assert crossing is not None, 'Find a real visible wheel surface outside socket labels'
            app.mouse_move(app.window,*crossing)
            assert app.bench_target=='base'
            draw();drop('Right')
        elif tick==3:
            wheels=[b for b in app.editor.bodies if b.id.startswith(('left_wheel','right_wheel')) and b.id.endswith('_root')]
            assert len(wheels)==2
            assert {1 if b.transform.position[1]>0 else -1 for b in wheels}=={-1,1}
            assert len(app.channels)==2
            app.edit(app.editor.undo);app.edit(app.editor.undo)
            assert app.editor.blueprint==before
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==3


def test_part_cards_cover_catalog_and_distinguish_passive_wheels():
    from little_world.assets.catalog import CATALOG
    from little_world.ui.part_cards import card_data
    for item in CATALOG:
        shapes,lo,hi,labels=card_data(item.id)
        assert shapes and all(hi>lo) and len(labels)==3
    assert 'Powered' in card_data('drive_left')[3][-1]
    assert 'Passive' in card_data('wheel_small')[3][-1]
    assert '120 mm' in card_data('wheel_small')[3][0]


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_live_parts_search_fractional_scroll_and_component_actions(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'browser.json',starter_blueprint());app.open_bench()
    draw=app.draw;tick=0;before=app.editor.blueprint
    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(b.x+b.width/2,b.y+b.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
    def exercise():
        nonlocal tick
        draw();tick+=1
        if tick==1:
            monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(100,300))
            app.scroll(app.window,0,-.25)
            assert app.parts_scroll==pytest.approx(9.5)
            tx,ty,tw,th,hy,hh=app.parts_track
            assert app.parts_mouse(tx+5,hy+5,glfw.PRESS)
            app.mouse_move(app.window,tx+5,ty+th)
            app.parts_mouse(tx+5,ty+th,glfw.RELEASE)
            assert app.parts_scroll==app.parts_max_scroll
            click('Search parts')
            for c in 'wheel':app.character(app.window,ord(c))
        elif tick==2:
            assert app.dialog is None and app.parts_query=='wheel'
            assert app.parts_scroll==0 and app.catalog_rows
            assert all('wheel' in (p.title+' '+p.id+' '+p.category+' '+p.capability).lower() for p in app.parts_items())
            app.key(app.window,glfw.KEY_A,0,glfw.PRESS,glfw.MOD_SUPER)
            for c in 'zzzz':app.character(app.window,ord(c))
        elif tick==3:
            assert not app.catalog_rows
            app.key(app.window,glfw.KEY_ESCAPE,0,glfw.PRESS,0)
            assert app.bench_open and not app.parts_focus
            click('X');click('Replace')
        elif tick==4:
            assert app.dialog and 'Replace' in app.dialog['title']
            value=next(v for v in app.dialog['query'] if 'Wide' in v or 'wide' in v)
            app.dialog['apply'](value);app.dialog=None
            assert app.editor.selected.catalog_part=='chassis_wide'
            app.edit(app.editor.undo);assert app.editor.blueprint==before
            draw();click('Delete')
        elif tick==5:
            assert not app.editor.bodies
            app.edit(app.editor.undo);assert app.editor.blueprint==before
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==5


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_connected_delete_review_and_undo(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.robots.arm_lab import arm_lab_blueprint
    app=Workshop(tmp_path/'branch.json',arm_lab_blueprint());app.open_bench()
    app.editor.select('robot_arm_1_root');before=app.editor.blueprint
    draw=app.draw;tick=0
    def exercise():
        nonlocal tick
        draw();tick+=1
        if tick==1:
            app.delete_selected()
            assert app.editor.blueprint==before
            assert app.dialog['query'][0]=='Keep assembly'
            app.dialog['apply']('Keep assembly');app.dialog=None
            assert app.editor.blueprint==before
        elif tick==2:
            app.delete_selected()
            action=app.dialog['query'][1]
            assert 'bodies' in action and 'bindings' in action
            app.dialog['apply'](action);app.dialog=None
            assert [b.id for b in app.editor.bodies]==['pedestal']
            assert not app.editor.blueprint.controllers
        elif tick==3:
            app.edit(app.editor.undo)
            assert app.editor.blueprint==before
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==3
