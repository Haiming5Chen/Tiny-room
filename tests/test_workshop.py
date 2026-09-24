import os
import pytest
pytest.importorskip('mujoco')


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires a display and OpenGL')
def test_workshop_build_save_simulate_and_return(monkeypatch, tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.core.component import Motor
    from little_world.core.blueprint import Blueprint
    from little_world.core.world import Mode
    app = Workshop(tmp_path/'design.json')
    app.library_open = False
    original_draw = app.draw
    original_cursor = glfw.get_cursor_pos
    tick = 0
    saved = None
    simulation_time = 0
    resources = None

    def click(label):
        item = next(b for b in app.buttons if b.label == label)
        assert item.enabled
        # Dispatch through the same hit-testing callback as a real mouse click.
        monkeypatch.setattr(glfw, 'get_cursor_pos', lambda w: (item.x+item.width/2,item.y+item.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        monkeypatch.setattr(glfw, 'get_cursor_pos', original_cursor)

    def draw_and_use():
        nonlocal tick, saved, simulation_time, resources
        original_draw()
        tick += 1
        # UI controls must fit the real window, including the lower inspector.
        width,height=glfw.get_window_size(app.window)
        assert all(0 <= b.x and b.x+b.width <= width and b.y+b.height <= height-32
                   for b in app.buttons)
        if tick == 1:
            resources=(app.context,app.canvas,app.render_scene)
            import mujoco as mj
            import numpy as np
            fw,fh=glfw.get_framebuffer_size(app.window)
            rgb=np.zeros((fh,fw,3),dtype=np.uint8)
            mj.mjr_readPixels(rgb,None,mj.MjrRect(0,0,fw,fh),app.context)
            sx,sy=fw/width,fh/height
            title=rgb[int(fh-42*sy):int(fh-12*sy),int(15*sx):int(150*sx)]
            assert (title.min(axis=2)>180).sum()>30  # actual font atlas is visible

        assert resources == (app.context,app.canvas,app.render_scene)
        if tick == 2:
            click('Size +10%')
        elif tick == 3:
            assert app.editor.selected.geometry.size[0] == pytest.approx(.352)
            assert app.model.geom('machine/chassis_geom').size[0] == pytest.approx(.176)
            click('Undo')
        elif tick == 4:
            assert app.editor.selected.geometry.size[0] == .32
            click('Files')
        elif tick == 5:
            click('Start with block')
        elif tick == 6:
            click('Add')
        elif tick == 7:
            click('Left wheel + motor')
        elif tick == 8:
            click('Edit')
        elif tick == 9:
            click('base')
        elif tick == 10:
            click('Add')
        elif tick == 11:
            click('Right wheel + motor')
        elif tick == 12:
            assert len([p for p in app.editor.blueprint.components if isinstance(p,Motor)]) == 2
            assert app.model.nu == 2
            click('Save')
        elif tick == 13:
            saved = app.editor.blueprint
            assert Blueprint.from_json(app.path.read_text()) == saved
            click('SIMULATE  >')
        elif tick == 14:
            assert app.world.mode == Mode.SIMULATE
            assert len(app.channels) == 2
            app.key(app.window,glfw.KEY_S,0,glfw.PRESS,glfw.MOD_CONTROL)
            assert app.controls.targets() == (0., 0.)  # Save is not reverse-drive
            app.key(app.window,glfw.KEY_S,0,glfw.RELEASE,glfw.MOD_CONTROL)
            app.key(app.window,glfw.KEY_W,0,glfw.PRESS,0)
        elif tick == 44:
            simulation_time=app.state.time
            assert simulation_time > 0
            app.key(app.window,glfw.KEY_W,0,glfw.RELEASE,0)
            click('STOP / RETURN TO BUILD')
        elif tick == 45:
            assert app.world.mode == Mode.BUILD
            assert app.state.time == 0
            assert app.editor.blueprint == saved
            click('Files')
        elif tick == 46:
            click('Load')
        elif tick == 47:
            assert app.editor.blueprint == saved
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',draw_and_use)
    app.run(seconds=10)
    assert tick >= 47 and simulation_time > 0


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_catalog_ui_preview_insert_and_selected_surface(monkeypatch,tmp_path):
    import glfw
    import numpy as np
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'design.json')
    draw=app.draw
    tick=0
    resources=None

    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        app.events.append(b.action)

    def exercise():
        nonlocal tick,resources
        draw();tick+=1
        if tick==1:
            resources=(app.context,app.canvas)
            click('Add')
        elif tick==2:
            click('Motion')
        elif tick==3:
            click('Left drive module')
        elif tick==4:
            assert 'drive_left' in app.preview_cache
            click('Add selected part')
        elif tick==5:
            assert app.model.nu==3
            assert len(app.editor.bodies)>5
            click('Edit')
        elif tick==6:
            click('Wood')
        elif tick==7:
            body=app.editor.selected
            material=next(m for m in app.editor.blueprint.materials if m.id==body.material)
            assert material.texture=='wood_grain'
            geom=app.model.geom('machine/'+body.id+'_geom').id
            assert np.allclose(app.model.geom_rgba[geom],material.rgba)  # selection doesn't repaint it
            assert app.model.ntex==5
            assert resources==(app.context,app.canvas)
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick>=7


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_precision_forms_snap_hinge_and_input_isolation(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    from little_world.construction.editor import starter_blueprint
    app=Workshop(tmp_path/'precision.json',starter_blueprint())
    draw=app.draw
    tick=0
    resources=None
    before=None

    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        app.events.append(b.action)

    def type_value(value):
        app.key(app.window,glfw.KEY_A,0,glfw.PRESS,glfw.MOD_CONTROL)
        for c in value:
            app.character(app.window,ord(c))

    def exercise():
        nonlocal tick,resources,before
        draw();tick+=1
        width,height=glfw.get_window_size(app.window)
        assert all(b.x>=0 and b.x+b.width<=width and b.y+b.height<=height-32 for b in app.buttons)
        if tick==1:
            resources=(app.context,app.canvas)
            click('Exact dimensions & pose')
        elif tick==2:
            assert app.dialog is not None
            # Shortcuts are swallowed while a field owns keyboard focus.
            app.key(app.window,glfw.KEY_W,0,glfw.PRESS,0)
            assert not app.held_codes and not app.events
            type_value('20, 0, 130')
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            type_value('0, 0, 30')
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            type_value('320, 240, 90')
            app.key(app.window,glfw.KEY_ENTER,0,glfw.PRESS,0)
        elif tick==3:
            assert app.dialog is None and app.building
            assert app.editor.selected.transform.position==pytest.approx((.02,0,.13))
            assert len(app.editor.past)==1
            app.edit(app.editor.add_box)
            click('Connect')
        elif tick==4:
            click('Snap faces')
        elif tick==5:
            assert app.editor.selected.parent=='base'
            assert app.editor.selected.transform.position==pytest.approx((0,0,.145))
            click('Hinge')
        elif tick==6:
            click('Axis, pivot & limits')
        elif tick==7:
            type_value('0, 0, 1')
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            type_value('-100, 0, 0')
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            type_value('0.04')
            app.key(app.window,glfw.KEY_TAB,0,glfw.PRESS,0)
            type_value('-30, 60')
            click('Apply')
        elif tick==8:
            assert app.editor.selected_hinge().position==(-.1,0,0)
            assert app.editor.selected_hinge().limits==(-30,60)
            click('Add motor')
        elif tick==9:
            type_value('0.7'); click('Apply')
        elif tick==10:
            before=app.editor.blueprint
            assert app.editor.selected_motors()[0].max_torque==.7
            click('SIMULATE  >')
        elif tick==11:
            assert not app.building
            click('Pulse +')
        elif tick==12:
            assert app.motor_test is not None
            app.key(app.window,glfw.KEY_SPACE,0,glfw.PRESS,0)
            assert app.motor_test is None
            click('STOP / RETURN TO BUILD')
        elif tick==13:
            assert app.editor.blueprint==before
            assert resources==(app.context,app.canvas)
            app.save()
            app.load()
            assert app.editor.blueprint==before
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick>=13


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_build_workspace_insert_search_and_keep_design(monkeypatch,tmp_path):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'hardware.json')
    app.bench_hardware=False;app.catalog_selection='gearmotor_37'
    app.bench_details=True
    draw=app.draw
    tick=0
    saved=None
    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        app.events.append(b.action)
    def exercise():
        nonlocal tick,saved
        draw();tick+=1
        width,height=glfw.get_window_size(app.window)
        assert all(b.x>=0 and b.x+b.width<=width and b.y+b.height<=height-32 for b in app.buttons)
        if tick==1:
            click('Build')
        elif tick==2:
            assert app.bench_open
            app.key(app.window,glfw.KEY_ENTER,0,glfw.PRESS,0)
            assert app.building and not app.events
            click('Add component')
        elif tick==3:
            assert app.editor.selected.id.startswith('gearmotor_37')
            assert app.model.nu==3
            assert app.bench_target=='chassis'
            assert app.bench_cache[0]==app.editor.blueprint
            click('Search parts')
        elif tick==4:
            for c in 'servo': app.character(app.window,ord(c))
        elif tick==5:
            click('Servo & horn')
        elif tick==6:
            assert app.catalog_selection=='servo_module'
            assert app.dialog is None  # Search results stay in the parts tray.
            assert app.catalog_mount!='Top'  # Select a free socket when Top is occupied.
            assert next(b for b in app.buttons if b.label=='Add component').enabled
            app.catalog_mount='Right'
            draw()
            click('Add component')
        elif tick==7:
            saved=app.editor.blueprint
            assert app.model.nu==4
            click('Save')
        elif tick==8:
            click('Back to room')
        elif tick==9:
            assert not app.bench_open and app.editor.blueprint==saved
            click('SIMULATE  >')
        elif tick==10:
            click('STOP / RETURN TO BUILD')
        elif tick==11:
            assert app.editor.blueprint==saved
            app.load()
            assert app.editor.blueprint==saved
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick>=11


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_workbench_assembly_browser_duplicate_and_focus(monkeypatch,tmp_path):
    import glfw
    import numpy as np
    from little_world.ui.workshop import Workshop
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    app=Workshop(tmp_path/'assembly.json',mobile_platform_blueprint())
    app.bench_details=True
    app.open_bench()
    draw=app.draw
    tick=0
    before=None
    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        app.events.append(b.action)
    def exercise():
        nonlocal tick,before
        draw();tick+=1
        w,h=glfw.get_window_size(app.window)
        assert all(b.x>=0 and b.x+b.width<=w and b.y+b.height<=h-32 for b in app.buttons)
        if tick==1:
            assert app.bench_module('gearmotor_37_1_face_screw_0')=='gearmotor_37_1_root'
            assert app.bench_module('tread_wheel_1_tread_0')=='tread_wheel_1_root'
            click('Assembly')
        elif tick==2:
            app.tree_select('gearmotor_37_1_root')
            app.reveal_in_tree(app.editor.selection)
        elif tick==3:
            before=app.editor.blueprint
            click('Duplicate')
        elif tick==4:
            for c in '120, 0, 0': app.character(app.window,ord(c))
            click('Apply')
        elif tick==5:
            assert app.bench_tab=='Assembly'
            assert app.editor.selected.id.startswith('gearmotor_37_1_root_copy')
            assert app.model.nu==3
            click('Focus selected')
        elif tick==6:
            assert np.linalg.norm(app.bench_camera.lookat)>0
            click('Delete subtree')
        elif tick==7:
            assert app.editor.blueprint==before
            click('Undo')
        elif tick==8:
            assert app.model.nu==3
            click('Pick: component')
        elif tick==9:
            assert not app.bench_module_pick
            app.save()
            saved=app.editor.blueprint
            app.load()
            assert app.editor.blueprint==saved
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick>=9


@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_workspace_navigation_at_minimum_size(monkeypatch, tmp_path):
    """The persistent workflow remains clickable across modes and simulation."""
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'navigation.json')
    draw=app.draw
    tick=0
    original=app.editor.blueprint
    cursor=glfw.get_cursor_pos

    def click(label):
        b=next(b for b in app.buttons if b.label==label)
        assert b.enabled
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(b.x+b.width/2,b.y+b.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        monkeypatch.setattr(glfw,'get_cursor_pos',cursor)

    def exercise():
        nonlocal tick
        if tick==0:glfw.set_window_size(app.window,1040,740)
        draw();tick+=1
        w,h=glfw.get_window_size(app.window)
        assert all(0<=b.x and b.x+b.width<=w and 0<=b.y and b.y+b.height<=h-32 for b in app.buttons)
        # No visible buttons may steal another button's hit area.
        for i,a in enumerate(app.buttons):
            for b in app.buttons[i+1:]:
                assert not (a.x<b.x+b.width and b.x<a.x+a.width and a.y<b.y+b.height and b.y<a.y+a.height), (a.label,b.label)
        assert all(any(b.label==label and b.y<56 for b in app.buttons)
                   for label in ('Real','Anime','Build','Program','Test','Inventory','Save'))
        if tick==1:click('Build')
        elif tick==2:
            assert app.bench_open
            click('Program')
        elif tick==3:
            assert not app.bench_open and app.panel_mode=='program'
            assert next(b for b in app.buttons if b.label=='Run').y<250
            click('Test')
        elif tick==4:
            assert app.panel_mode=='test'
            click('SIMULATE  >')
        elif tick==5:
            assert not app.building
            click('Inventory')
        elif tick==6:
            assert app.inventory_open and app.paused
            click('Build')
        elif tick==7:
            assert app.building and app.bench_open and not app.inventory_open
            assert not app.control_panel
            assert app.editor.blueprint==original
            click('Save')
        elif tick==8:
            assert app.path.exists() and app.program_path.exists()
            glfw.set_window_should_close(app.window,True)
    monkeypatch.setattr(app,'draw',exercise)
    app.run(seconds=10)
    assert tick==8
