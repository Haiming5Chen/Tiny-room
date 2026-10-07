from dataclasses import replace
import json
import pytest
from little_world.factory.recipe import CellRecipe
from little_world.factory.changes import CellRequest,CellChange,preview_changes


def test_request_roundtrip_preview_and_exact_diff():
    recipe=CellRecipe()
    request=CellRequest(recipe,3,(CellChange('tray','input',(.4,.01)),CellChange('product','product','Tall block')))
    assert CellRequest.from_json(request.to_json())==request
    preview=preview_changes(recipe,3,request)
    assert preview.before==recipe and recipe.point('input')==(.45,0)
    assert preview.after.point('input')==(.4,.01)
    assert preview.after.product=='Tall block'
    assert len(preview.summary)==2
    assert 'input' in preview.summary[0] and '0.45' in preview.summary[0]
    assert preview.apply(recipe,3)==preview.after


def test_stale_manual_edits_and_undo_revision_cannot_be_overwritten():
    recipe=CellRecipe();request=CellRequest(recipe,0,(CellChange('product','product','Tall block'),))
    preview=preview_changes(recipe,0,request)
    with pytest.raises(ValueError,match='changed'):preview.apply(recipe.moved('input',(.4,0)),0)
    with pytest.raises(ValueError,match='changed'):preview.apply(recipe,2)
    with pytest.raises(ValueError,match='changed'):preview_changes(recipe,1,request)


def test_complete_batch_validated_atomically_and_unknowns_rejected():
    recipe=CellRecipe()
    swap=CellRequest(recipe,0,(CellChange('tray','Blue',recipe.point('Amber')),CellChange('tray','Amber',recipe.point('Blue'))))
    assert preview_changes(recipe,0,swap).after.point('Blue')==recipe.point('Amber')
    bad=CellRequest(recipe,0,(CellChange('product','product','Tall block'),CellChange('tray','Blue',(0,0))))
    with pytest.raises(ValueError):preview_changes(recipe,0,bad)
    assert recipe.product=='Small block'
    for c in [CellChange('delete','input',None),CellChange('tray','typo',(.4,0)),CellChange('product','product','Car door')]:
        with pytest.raises(ValueError):preview_changes(recipe,0,CellRequest(recipe,0,(c,)))
    duplicate=CellRequest(recipe,0,(CellChange('product','product','Tall block'),)*2)
    with pytest.raises(ValueError,match='Duplicate'):preview_changes(recipe,0,duplicate)


def test_wire_format_strict_units_fields_and_numbers():
    recipe=CellRecipe();request=CellRequest(recipe,0,(CellChange('tray','input',(.4,0)),))
    wire=json.loads(request.to_json())
    for key,value in [('units','mm'),('frame','robot'),('version',True),('revision',-1),('surprise',4)]:
        bad=dict(wire);bad[key]=value
        with pytest.raises(ValueError):CellRequest.from_json(json.dumps(bad))
    for point in [(float('nan'),0),(True,0),(1,),('0.4',0)]:
        with pytest.raises(ValueError):preview_changes(recipe,0,CellRequest(recipe,0,(CellChange('tray','input',point),)))
    for text in ['[]','null','{"version":1,"version":1}']:
        with pytest.raises(ValueError):CellRequest.from_json(text)


def test_noop_has_no_changes_and_snapshot_is_portable():
    recipe=CellRecipe();p=preview_changes(recipe,0,CellRequest(recipe,0,()))
    assert p.after==recipe and p.summary==()

import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires native window')
def test_change_review_form_import_manual_conflict_undo_redo(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.factory_workspace import FactoryWorkshop
    app=FactoryWorkshop(tmp_path/'cell.json');draw=app.draw;done=False
    def exercise():
        nonlocal done
        draw()
        if done:return
        before=app.recipe
        app.open_cell_changes();app.dialog['apply']('Move a tray precisely')
        app.dialog['apply']('input');app.dialog['fields'][0][1]='0.4, 0.01'
        app.apply_form()
        assert app.dialog.get('cell_review') and app.recipe==before
        draw();assert {b.label for b in app.buttons}=={'Dismiss','Apply changes'}
        app.apply_cell_proposal();assert app.dialog is None
        assert app.recipe.point('input')==(.4,.01) and len(app.recipe_history)==1
        app.undo_recipe();assert app.recipe==before
        app.redo_recipe();assert app.recipe.point('input')==(.4,.01)
        file=tmp_path/'draft.json';app.export_cell_request(file)
        with pytest.raises(FileExistsError):app.export_cell_request(file)
        exported=CellRequest.from_json(file.read_text())
        assert preview_changes(app.recipe,app.recipe_revision,exported).summary==()
        request=app.change_request((CellChange('product','product','Tall block'),))
        file.write_text(request.to_json())
        app.open_cell_changes();app.dialog['apply']('Import JSON proposal')
        app.dialog['fields'][0][1]=str(file);app.apply_form()
        assert app.dialog.get('cell_review')
        app.apply_recipe(app.recipe.moved('input',(.38,.01)))
        edited=app.recipe
        app.apply_cell_proposal();assert app.recipe==edited and 'changed' in app.dialog['error']
        draw();assert not next(b for b in app.buttons if b.label=='Apply changes').enabled
        app.dismiss_cell_proposal();assert app.recipe==edited
        app.review_cell_request(app.change_request((CellChange('product','product','Tall block'),)))
        original_rebuild=app.rebuild;calls=0
        def fail_once():
            nonlocal calls
            calls+=1
            if calls==1:raise ValueError('Compilation rejected')
            original_rebuild()
        monkeypatch.setattr(app,'rebuild',fail_once)
        revision=app.recipe_revision;history=list(app.recipe_history)
        app.apply_cell_proposal()
        assert app.recipe==edited and app.recipe_revision==revision and app.recipe_history==history
        assert 'Compilation rejected' in app.dialog['error']
        monkeypatch.setattr(app,'rebuild',original_rebuild)
        app.apply_cell_proposal();assert app.recipe.product=='Tall block'
        app.undo_recipe();assert app.recipe==edited
        # Existing direct task/product edits still use the same undo mechanism.
        app.select_product('Tall block');assert not app.recipe_future
        app.undo_recipe();assert app.recipe==edited
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=exercise;app.run(60);assert done
