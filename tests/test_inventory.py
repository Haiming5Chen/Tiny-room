from dataclasses import replace
import pytest
from little_world.inventory.store import Inventory,fingerprint
from little_world.inventory.analysis import analyze,differences
from little_world.programming.program import Program
from little_world.robots.arm_lab import arm_lab_blueprint


def test_inventory_roundtrip_metadata_and_snapshots(tmp_path):
    store=Inventory(tmp_path);bp=arm_lab_blueprint()
    a=store.save('My unfinished robot','draft','Needs a lighter arm',bp,Program())
    b=store.save('My unfinished robot','finished','Second version',bp,Program())
    assert a.id!=b.id and store.read(a.id)==a
    store.update(a.id,'Arm v1','finished','Reviewed')
    assert store.read(a.id).blueprint==bp
    assert store.read(b.id)==b
    with pytest.raises(ValueError):store.read('../escape')
    (tmp_path/'broken.json').write_text('{}')
    records,errors=store.list();assert len(records)==2 and len(errors)==1


def test_analysis_mass_and_gravity_warning():
    from little_world.core.blueprint import Blueprint
    from little_world.core.component import Body,Geometry,Hinge,Motor,Transform
    from little_world.core.material import Material
    # One kg cube centred one metre from a Y pivot: gravity moment = 9.81 Nm.
    bp=Blueprint((Body('link',Geometry('box',(.1,.1,.1)),'m',Transform((1,0,0))),
                  Hinge('joint','link',(0,1,0),position=(-1,0,0)),Motor('motor','joint',1)),(Material('m',1000),))
    report=analyze(bp)
    assert report['mass_kg']==pytest.approx(1)
    assert report['gravity_loads'][0]['gravity_Nm']==pytest.approx(9.81)
    assert any('exceeds' in c for c in report['cons'])
    changed=replace(bp,components=(*bp.components[:-1],replace(bp.components[-1],max_torque=12)))
    assert differences(changed,bp)['components']['changed']==['motor']
    assert fingerprint(changed)!=fingerprint(bp)


def test_comparison_is_reproducible_and_does_not_modify_design():
    from little_world.inventory.benchmark import compare_trials
    bp=arm_lab_blueprint();before=bp.to_json()
    result=compare_trials(bp,bp,Program(),seconds=.1)
    assert result['left']==result['right']
    assert result['left_hash']==fingerprint(bp)
    assert bp.to_json()==before
    assert result['protocol']['environment'] and result['protocol']['timestep']==.002
    with pytest.raises(ValueError):compare_trials(bp,bp,Program(),mode='program',seconds=.1)


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires display')
def test_inventory_ui_save_compare_and_recovery(tmp_path,monkeypatch):
    import glfw
    from little_world.ui.workshop import Workshop
    app=Workshop(tmp_path/'robot.json',arm_lab_blueprint());app.pickup_program()
    original_draw=app.draw;done=False
    def click(label):
        original_draw();b=next(b for b in app.buttons if b.label==label)
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda w:(b.x+b.width/2,b.y+b.height/2))
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        while app.events:app.events.pop(0)()
    def draw():
        nonlocal done
        app.show_inventory();click('Save current version')
        app.dialog['fields'][0][1]='Arm v1';click('Apply')
        saved=app.selected_design();assert saved.status=='draft'
        app.editor.select('robot_arm_1_upper_arm');app.edit(lambda:app.editor.set_motor(4))
        before=app.editor.blueprint
        app.inventory_tab='Performance';original_draw()
        app.start_comparison('hold_drive');app.comparison_future.result(timeout=30);app.poll_comparison()
        assert app.comparison and app.inventory.comparisons()
        assert app.editor.blueprint==before
        app.inventory_tab='Overview';click('Name / status / notes')
        app.dialog['fields'][1][1]='finished';click('Apply')
        assert app.selected_design().status=='finished'
        click('Load selected');assert app.editor.blueprint==saved.blueprint and app.program==saved.program
        records,errors=app.inventory.list();assert len(records)==2 and not errors
        assert any(r.blueprint==before and r.name.startswith('Recovery') for r in records)
        reopened=Inventory(tmp_path/'inventory');assert len(reopened.list()[0])==2
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=draw;app.run(seconds=15);assert done


def test_weaker_motor_has_larger_simulated_tracking_error():
    from little_world.inventory.benchmark import compare_trials
    from little_world.inventory.analysis import changed_fields
    from little_world.construction.editor import AssemblyEditor
    bp=arm_lab_blueprint();e=AssemblyEditor(bp);e.select('robot_arm_1_upper_arm');e.set_motor(.05)
    result=compare_trials(e.blueprint,bp,Program(),seconds=.5)
    assert result['left']['peak_joint_error_deg']>result['right']['peak_joint_error_deg']+1
    assert any('max_torque' in line and '0.05' in line for line in changed_fields(e.blueprint,bp))
