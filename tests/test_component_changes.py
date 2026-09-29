import pytest
from little_world.construction.editor import AssemblyEditor,starter_blueprint
from little_world.robots.arm_lab import arm_lab_blueprint


def test_replace_powered_wheel_keeps_drive_and_undo():
    from little_world.construction.component_changes import replace_component
    e=AssemblyEditor(starter_blueprint())
    for item in ('drive_left','drive_right'):
        e.select('base');e.add_catalog(item)
    before=e.blueprint;controllers=before.controllers
    e.select('left_wheel_1_root');replace_component(e,'drive_220')
    assert e.selected.geometry.size[0]==pytest.approx(.11)
    assert e.blueprint.controllers==controllers
    assert e.selected.catalog_part=='drive_220'
    e.undo();assert e.blueprint==before


def test_replace_arm_keeps_gripper_controls_and_tool_connection():
    from little_world.construction.component_changes import replace_component
    from little_world.construction.connections import frames,mate
    e=AssemblyEditor(arm_lab_blueprint());before=e.blueprint
    e.select('robot_arm_1_root');replace_component(e,'robot_arm_long')
    assert e.blueprint.controllers==before.controllers
    parts={b.id:b for b in e.bodies}
    grip=parts['two_finger_gripper_1_root'];wrist=parts[grip.parent]
    assert grip.transform.position==pytest.approx(mate(frames(grip)['tool_mount'],frames(wrist)['tool']).position)
    assert parts['robot_arm_1_upper_arm'].geometry.size[0]>.18
    e.undo();assert e.blueprint==before


def test_replace_base_keeps_and_repositions_wheel_connections():
    from little_world.construction.component_changes import replace_component
    e=AssemblyEditor(starter_blueprint())
    for part in ('drive_left','drive_right'):
        e.select('base');e.add_catalog(part)
    before=e.blueprint
    e.select('base');replace_component(e,'chassis_wide')
    parts={b.id:b for b in e.bodies}
    assert parts['base'].geometry.size[1]==.36
    assert parts['left_wheel_1_root'].parent=='base'
    assert parts['left_wheel_1_root'].transform.position[1]>.18
    assert e.blueprint.controllers==before.controllers
    e.undo();assert e.blueprint==before


def test_smart_delete_blocks_intermediate_component_but_allows_reviewed_branch():
    from little_world.construction.component_changes import delete_component,deletion_impact
    e=AssemblyEditor(arm_lab_blueprint());e.select('robot_arm_1_root');before=e.blueprint
    impact=deletion_impact(e)
    assert 'two_finger_gripper_1_root' in impact['attachments']
    with pytest.raises(ValueError,match='attached'):delete_component(e)
    assert e.blueprint==before
    delete_component(e,include_attached=True)
    assert [b.id for b in e.bodies]==['pedestal']
    assert not e.blueprint.controllers
    e.undo();assert e.blueprint==before


def test_leaf_component_deletes_internal_details_in_one_edit():
    from little_world.construction.component_changes import delete_component,deletion_impact
    e=AssemblyEditor(starter_blueprint());e.add_catalog('drive_left');before=e.blueprint
    assert not deletion_impact(e)['attachments']
    delete_component(e)
    assert len(e.bodies)==1
    e.undo();assert e.blueprint==before


def test_incompatible_replace_rejected_without_changes():
    from little_world.construction.component_changes import replace_component
    e=AssemblyEditor(arm_lab_blueprint());e.select('robot_arm_1_root');before=e.blueprint
    with pytest.raises(ValueError):replace_component(e,'wheel_large')
    assert e.blueprint==before and not e.past


def test_wider_wheel_replacement_keeps_surface_clearance():
    from little_world.construction.component_changes import replace_component
    from little_world.construction.docking import dock,placement
    from little_world.assets.catalog import BY_ID
    e=AssemblyEditor(starter_blueprint())
    dock(e,'drive_left','base','Left')
    replace_component(e,'drive_280')
    base=next(b for b in e.bodies if b.id=='base')
    assert e.selected.transform.position==pytest.approx(placement(BY_ID['drive_280'],base,'Left').position)
