from little_world.construction.editor import AssemblyEditor
from little_world.robots.mobile_platform import mobile_platform_blueprint
from little_world.core.component import Body, Hinge, Motor, Camera, Transform
from little_world.core.blueprint import Blueprint
import pytest


def test_duplicate_motor_subtree_remaps_references_and_undo():
    editor=AssemblyEditor(mobile_platform_blueprint())
    editor.select('gearmotor_37_1_root')
    before=editor.blueprint
    old_ids=editor.subtree_ids()
    old=editor.selected
    editor.duplicate((.05,0,0))
    copied=editor.subtree_ids()
    assert not old_ids & copied
    assert editor.selected.parent==old.parent
    assert editor.selected.transform.position==pytest.approx(tuple(a+b for a,b in zip(old.transform.position,(.05,0,0))))
    assert len(old_ids)==len(copied)
    assert len(editor.blueprint.controllers)==len(before.controllers)
    new_motors=[c for c in editor.blueprint.components if isinstance(c,Motor) and c.id in copied]
    assert len(new_motors)==1
    assert new_motors[0].joint in copied
    assert Blueprint.from_json(editor.blueprint.to_json())==editor.blueprint
    editor.undo(); assert editor.blueprint==before
    editor.redo(); assert editor.subtree_ids()==copied
    editor.delete(); assert editor.blueprint==before


def test_duplicate_whole_robot_copies_controller_and_is_independent():
    editor=AssemblyEditor(mobile_platform_blueprint())
    original=editor.blueprint
    editor.duplicate((.6,0,0))
    copied=editor.subtree_ids()
    assert len(editor.blueprint.controllers)==2
    new_controller=editor.blueprint.controllers[-1]
    assert set(new_controller.actuators)<=copied
    assert new_controller.id!=original.controllers[0].id
    assert editor.selected.parent is None and editor.selected.dynamic
    editor.blueprint.validate()


def test_duplicate_camera_and_invalid_offset_are_atomic():
    from little_world.robots.two_wheel import two_wheel_blueprint
    editor=AssemblyEditor(two_wheel_blueprint())
    before=editor.blueprint
    with pytest.raises(ValueError): editor.duplicate((float('nan'),0,0))
    assert editor.blueprint==before and not editor.past
    editor.duplicate()
    copied=editor.subtree_ids()
    cameras=[c for c in editor.blueprint.components if isinstance(c,Camera) and c.id in copied]
    assert len(cameras)==1 and cameras[0].body in copied


def test_duplicate_motor_runs_as_an_independent_native_actuator():
    pytest.importorskip('mujoco')
    from little_world import World, Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    editor=AssemblyEditor(mobile_platform_blueprint())
    editor.select('gearmotor_37_1_root')
    editor.duplicate((.3,0,0))
    copied=editor.subtree_ids()
    motor=next(c for c in editor.blueprint.components if isinstance(c,Motor) and c.id in copied)
    backend=MujocoBackend()
    with World(backend,Scene((Entity('machine',editor.blueprint),))) as world:
        world.start()
        assert backend.model.nu==3
        joint=backend.model.joint('machine/'+motor.joint)
        for _ in range(30): world.step({'machine/'+motor.id:.2})
        assert abs(backend.data.qvel[joint.dofadr[0]])>.01
