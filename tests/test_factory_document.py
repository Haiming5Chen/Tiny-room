from dataclasses import replace
import json
import pytest
from little_world.construction.editor import starter_blueprint
from little_world.core.component import Transform
from little_world.factory.document import FactoryDocument,MachineAsset,Station,ProcessLink
from little_world.factory.document_editor import FactoryEditor


def document():
    return FactoryDocument((MachineAsset('custom',starter_blueprint()),),
        (Station('feed','custom','Feed',Transform((0,0,0))),Station('inspect','custom','Inspect',Transform((1,0,0)))),
        (ProcessLink('transfer','feed','inspect'),))


def test_portable_shared_assets_and_scene_compile():
    doc=document();loaded=FactoryDocument.from_json(doc.to_json())
    assert loaded==doc
    scene=loaded.to_scene()
    assert [e.id for e in scene.entities]==['feed','inspect']
    assert scene.entities[0].blueprint is scene.entities[1].blueprint
    assert scene.entities[1].transform.position==(1,0,0)
    changed=loaded.move_station('feed',Transform((.5,.2,0)))
    assert changed.assets==doc.assets and doc.stations[0].transform.position==(0,0,0)
    assert changed.links==doc.links


def test_connections_make_deletion_explicit_and_atomic():
    doc=document()
    with pytest.raises(ValueError,match='links'):doc.remove_station('feed')
    changed=doc.remove_station('feed',remove_links=True)
    assert len(changed.stations)==1 and changed.links==() and doc.links
    with pytest.raises(ValueError,match='used'):doc.remove_asset('custom')
    with pytest.raises(ValueError):doc.move_station('unknown',Transform())
    with pytest.raises(ValueError):doc.with_link(ProcessLink('bad','feed','missing'))
    with pytest.raises(ValueError):doc.with_link(ProcessLink('self','feed','feed'))


def test_revision_conflicts_undo_redo_and_shared_asset_impact():
    doc=document();editor=FactoryEditor(doc)
    proposal=editor.preview(doc.move_station('feed',Transform((.2,0,0))))
    assert editor.document==doc
    assert proposal.changes[0]['id']=='feed'
    editor.apply(proposal);assert editor.revision==1
    editor.undo();assert editor.document==doc and editor.revision==2
    with pytest.raises(ValueError,match='changed'):editor.apply(proposal)
    editor.redo();assert editor.document==proposal.after
    replacement=replace(doc.assets[0],blueprint=replace(starter_blueprint(),controllers=()))
    # Change actual machine geometry rather than just the station pose.
    from little_world.construction.editor import AssemblyEditor
    machine=AssemblyEditor(replacement.blueprint);machine.move((.1,0,0))
    candidate=editor.document.with_asset(MachineAsset('custom',machine.blueprint))
    edit=editor.preview(candidate)
    assert edit.affected_stations==('feed','inspect')
    editor.apply(edit);assert editor.document.assets[0].blueprint==machine.blueprint
    editor.undo();assert editor.document==proposal.after
    editor.apply(editor.preview(editor.document.move_station('inspect',Transform((2,0,0)))))
    assert not editor.can_redo


def test_request_roundtrip_and_noop_history():
    doc=document();editor=FactoryEditor(doc)
    proposal=editor.preview(doc.move_station('feed',Transform((.25,0,0))))
    restored=type(proposal).from_json(proposal.to_json())
    assert restored==proposal
    editor.apply(restored)
    revision=editor.revision
    editor.apply(editor.preview(editor.document));assert editor.revision==revision
    with pytest.raises(ValueError):editor.apply(restored)

@pytest.mark.parametrize('mutation',[
    lambda d:d.update(version=True),lambda d:d.update(units='cm'),lambda d:d.update(frame='camera'),
    lambda d:d.update(extra=1),lambda d:d['stations'][0].update(asset='missing'),
    lambda d:d['stations'].append(d['stations'][0]),lambda d:d['assets'][0].update(extra='bad'),
    lambda d:d['stations'][0]['transform'].update(position=[True,0,0]),
    lambda d:d['stations'][0]['transform'].update(position=[10**500,0,0]),
])
def test_strict_document_validation(mutation):
    wire=json.loads(document().to_json());mutation(wire)
    with pytest.raises(ValueError):FactoryDocument.from_json(json.dumps(wire))


def test_native_scene_preserves_entity_names_and_authored_pose():
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    doc=document();backend=MujocoBackend();backend.compile(doc.to_scene(),.002)
    try:
        assert backend.model.body('feed/base').id!=backend.model.body('inspect/base').id
        a=backend.data.xpos[backend.model.body('feed/base').id]
        b=backend.data.xpos[backend.model.body('inspect/base').id]
        assert tuple(b-a)==pytest.approx((1,0,0))
        before=doc.to_json()
        for _ in range(20):backend.step({})
        assert doc.to_json()==before
    finally:backend.close()


def test_reordering_does_not_create_a_spurious_edit():
    doc=document();editor=FactoryEditor(doc)
    reordered=replace(doc,stations=tuple(reversed(doc.stations)))
    proposal=editor.preview(reordered)
    assert not proposal.changes
    editor.apply(proposal);assert editor.revision==0 and not editor.can_undo


def test_link_edit_preserves_identity_and_reports_affected_stations():
    doc=document();editor=FactoryEditor(doc)
    proposal=editor.preview(doc.with_link(ProcessLink('transfer','inspect','feed')))
    assert proposal.affected_stations==('feed','inspect')
    assert proposal.changes[0]['collection']=='links'
    assert 'process execution' in proposal.report()['not_checked']
    editor.apply(proposal);editor.undo();assert editor.document==doc
    assert doc.remove_link('transfer').links==()


def test_saved_custom_machine_example_exports_and_compiles_without_a_window(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    source=tmp_path/'machine.json';source.write_text(starter_blueprint().to_json(), encoding='utf-8')
    output=tmp_path/'factory.json'
    command=[sys.executable,str(Path(__file__).parents[1]/'examples/factory_layout.py'),'--machine',str(source),'--output',str(output),'--check-physics']
    result=subprocess.run(command,capture_output=True,text=True,check=True, encoding='utf-8')
    report=json.loads(result.stdout)
    assert report['physics_compiled'] and report['process_links'].startswith('layout intent')
    loaded=FactoryDocument.from_json(output.read_text(encoding='utf-8'))
    assert next(a.blueprint for a in loaded.assets if a.id=='custom_machine')==starter_blueprint()
    assert len([s for s in loaded.stations if s.asset=='custom_machine'])==2
    before=output.read_bytes()
    repeated=subprocess.run(command,capture_output=True,text=True, encoding='utf-8')
    assert repeated.returncode!=0 and output.read_bytes()==before


def test_mutating_a_diff_does_not_mutate_the_reviewed_scene():
    doc=document();editor=FactoryEditor(doc)
    proposal=editor.preview(doc.move_station('feed',Transform((.2,0,0))))
    view=proposal.changes;view[0]['after']['label']='wrong'
    editor.apply(proposal)
    assert editor.document.stations[0].label=='Feed'


def test_editor_clone_keeps_history_independent():
    doc=document();editor=FactoryEditor(doc)
    editor.apply(editor.preview(doc.move_station('feed',Transform((.2,0,0)))))
    copy=editor.clone();copy.undo()
    assert copy.document==doc and copy.can_redo
    assert editor.document!=doc and editor.can_undo and not editor.can_redo
    copy.apply(copy.preview(doc.move_station('inspect',Transform((3,0,0)))))
    assert not copy.can_redo and editor.revision==1
