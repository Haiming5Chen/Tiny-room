from dataclasses import replace
import pytest
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.core.component import Body, Hinge, Motor
from little_world.core.blueprint import Blueprint
from little_world.robots.two_wheel import two_wheel_blueprint


def test_edit_undo_and_json_do_not_mutate_original():
    original = two_wheel_blueprint()
    editor = AssemblyEditor(original)
    editor.move((.1, 0, 0))
    assert editor.selected.transform.position[0] == .1
    assert original.components[0].transform.position[0] == 0
    editor.material('wood')
    assert editor.selected.material == 'wood'
    assert Blueprint.from_json(editor.blueprint.to_json()) == editor.blueprint
    editor.undo()
    assert editor.selected.material == 'metal'
    editor.undo()
    assert editor.blueprint == original
    editor.redo()
    assert editor.selected.transform.position[0] == .1


def test_block_can_become_motorized_assembly():
    editor = AssemblyEditor(starter_blueprint())
    editor.attach_wheel(1)
    editor.select('base')
    editor.attach_wheel(-1)
    parts = editor.blueprint.components
    assert len([p for p in parts if isinstance(p, Hinge)]) == 2
    assert len([p for p in parts if isinstance(p, Motor)]) == 2
    assert len(editor.blueprint.controllers[0].actuators) == 2
    editor.blueprint.validate()


def test_removal_cleans_joint_motor_and_controller_references():
    editor = AssemblyEditor(two_wheel_blueprint())
    editor.select('left_wheel')
    editor.delete()
    assert not any(p.id in ('left_wheel', 'left_hinge', 'left_motor') for p in editor.blueprint.components)
    assert not editor.blueprint.controllers
    editor.undo()
    assert editor.blueprint == two_wheel_blueprint()


def test_delete_root_removes_descendants_and_can_start_again():
    editor = AssemblyEditor(two_wheel_blueprint())
    editor.delete()
    assert editor.blueprint.components == ()
    editor.add_box()
    assert isinstance(editor.selected, Body)
    assert editor.selected.dynamic


def test_failed_edit_does_not_change_history():
    editor = AssemblyEditor(two_wheel_blueprint())
    with pytest.raises(ValueError):
        editor.scale(-1)
    assert editor.blueprint == two_wheel_blueprint()
    assert not editor.past


def test_build_preview_and_simulation_edit_boundary():
    from little_world import Entity, World
    from little_world.core.world import Mode
    from little_world.core.scene import Scene
    from test_contracts import FakeBackend
    world = World(FakeBackend(), Scene((Entity('machine', starter_blueprint()),)))
    assert world.preview().time == 0
    assert world.mode == Mode.BUILD
    world.start()
    with pytest.raises(RuntimeError):
        world.preview()
    world.reset()
    assert world.preview().time == 0
    world.close()


def test_right_wheel_first_preserves_steering_and_motor_configuration():
    editor = AssemblyEditor(starter_blueprint())
    editor.attach_wheel(-1)
    editor.select('base')
    editor.attach_wheel(1)
    assert editor.blueprint.controllers[0].actuators[0].startswith('left_wheel_')
    editor.motor_strength(.8)
    assert editor.selected_motors()[0].max_torque == .8
    editor.undo()
    assert editor.selected_motors()[0].max_torque == 1
