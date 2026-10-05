import os
import pytest
pytestmark=pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires hidden OpenGL window')


def test_layout_drag_builder_import_history_and_same_window(tmp_path,monkeypatch):
    import glfw
    import numpy as np
    from little_world.ui.workshop import Workshop
    from little_world.construction.editor import starter_blueprint
    from little_world.factory.document import FactoryDocument,ProcessLink,Station,MachineAsset
    from little_world.core.component import Transform
    opened=[];create=glfw.create_window
    def tracked(*a,**kw):
        window=create(*a,**kw);opened.append(window);return window
    monkeypatch.setattr(glfw,'create_window',tracked)
    host=Workshop(tmp_path/'machine.json',starter_blueprint());host.factory_recipe_path=tmp_path/'cell.json'
    draw=host.draw;done=False
    def use():
        nonlocal done
        draw()
        if done:return
        original=host.editor.blueprint
        host.switch_workspace('Real');lab=host.active_workspace
        lab.switch_real_view('Layout');layout=host.active_workspace
        assert layout.window is host.window and layout.app_mode=='Real'
        layout.draw();assert any(b.label=='Use current Anime machine' and b.enabled for b in layout.buttons)
        before=layout.layout.document;revision=layout.layout.revision
        # Locate a real rendered station through MuJoCo picking, not a mocked hit.
        def project(point):
            w,h=glfw.get_window_size(layout.window);a,b=layout.render_scene.camera
            origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
            p=np.asarray(point)-origin;scale=(h-88)/2/((a.frustum_top-a.frustum_bottom)/(2*a.frustum_near)*float(p@forward))
            return (layout.PANEL+(w-layout.PANEL)/2+float(p@np.cross(forward,up))*scale,56+(h-88)/2-float(p@up)*scale)
        points=[project(layout.data.geom_xpos[g]) for g in range(layout.model.ngeom) if layout.model.body(layout.model.geom_bodyid[g]).name.startswith('work/')]
        x,y=next(p for p in points if layout.station_at(*p)=='work')
        pointer=[(x,y)];monkeypatch.setattr(glfw,'get_cursor_pos',lambda window:pointer[0])
        layout.mouse(layout.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0);assert layout.station_drag
        layout.mouse_move(layout.window,x+45,y+15);layout.draw()
        assert layout.layout.document==before
        old_drag=dict(layout.station_drag)
        target=tuple(layout.station_drag['point']);assert target!=before.stations[-1].transform.position
        pointer[0]=(x+45,y+15);layout.mouse(layout.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        while layout.events:layout.events.pop(0)()
        assert layout.station.transform.position==target and layout.layout.revision==revision+1
        with pytest.raises(ValueError,match='changed during drag'):layout.finish_drag(old_drag)
        layout.undo_layout();assert layout.layout.document==before
        layout.redo_layout();assert layout.station.transform.position==target
        layout.apply_document(layout.layout.document.with_asset(MachineAsset('station_1_asset',original)))
        layout.use_builder();assert host.editor.blueprint==original
        assert layout.station.asset!='station_1_asset'
        imported=layout.station
        assert next(a.blueprint for a in layout.layout.document.assets if a.id==imported.asset)==original
        layout.apply_document(layout.layout.document.with_link(ProcessLink('to_custom','work',imported.id)))
        old=layout.layout.document
        layout.delete_station();assert layout.dialog is not None and layout.layout.document==old
        label=layout.dialog['query'][0];layout.dialog['apply'](label);layout.dialog=None
        assert all(s.id!=imported.id for s in layout.layout.document.stations)
        assert not layout.layout.document.links
        layout.undo_layout();assert layout.layout.document==old
        layout.select_station(imported.id);layout.delete_station();stale_delete=layout.dialog['apply'];layout.dialog=None
        layout.apply_document(old.move_station('work',Transform((3,0,0))))
        with pytest.raises(ValueError,match='review station deletion'):stale_delete('')
        layout.undo_layout();assert layout.layout.document==old
        layout.save();assert FactoryDocument.from_json(layout.path.read_text())==old
        # Compilation failure must preserve document, selection and history.
        original_rebuild=layout.rebuild;calls=0
        def fail_once():
            nonlocal calls
            calls+=1
            if calls==1:raise ValueError('Rejected layout')
            original_rebuild()
        monkeypatch.setattr(layout,'rebuild',fail_once)
        r=layout.layout.revision
        with pytest.raises(ValueError,match='Rejected'):layout.apply_document(old.move_station('work',Transform((3,0,0))))
        assert layout.layout.document==old and layout.layout.revision==r
        monkeypatch.setattr(layout,'rebuild',original_rebuild)
        layout.switch_real_view('Real');assert host.active_workspace is lab
        lab.switch_real_view('Layout');assert host.active_workspace is layout
        layout.switch_workspace('Anime');assert host.active_workspace is host and host.editor.blueprint==original
        host.switch_workspace('Real');assert host.active_workspace is layout
        assert layout.layout.document==old and len(opened)==1
        glfw.set_window_size(host.window,1040,740);layout.draw()
        for i,a in enumerate(layout.buttons):
            for b in layout.buttons[i+1:]:
                assert not(a.x<b.x+b.width and b.x<a.x+a.width and a.y<b.y+b.height and b.y<a.y+a.height),(a.label,b.label)
        done=True;glfw.set_window_should_close(host.window,True)
    host.draw=use;host.run(60,visible=False);assert done
