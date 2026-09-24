from dataclasses import replace
from math import sqrt
import pytest
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.core.component import Body, Geometry, Transform, Hinge, Attachment
from little_world.core.blueprint import Blueprint


def assembly():
    editor = AssemblyEditor(starter_blueprint())
    editor.add_box()
    return editor


def test_snap_faces_rotated_parent_and_undo():
    editor = assembly()
    before = editor.blueprint
    editor.snap('base', 'Bottom', 'Top', .003)
    assert editor.selected.parent == 'base'
    assert not editor.selected.dynamic
    assert editor.selected.transform.position == pytest.approx((0, 0, .148))
    assert editor.selected.transform.quaternion == pytest.approx((1, 0, 0, 0))
    assert Blueprint.from_json(editor.blueprint.to_json()) == editor.blueprint
    editor.undo()
    assert editor.blueprint == before
    editor.redo()
    editor.select('base')
    editor.set_pose((0, 0, .13), (90, 0, 0))
    # Resolved snapping stays relative to the rotated parent, not world axes.
    editor.select('box_1')
    editor.snap('base', 'Bottom', 'Top', 0)
    assert editor.selected.transform.position == pytest.approx((0, 0, .145))


def test_named_frames_and_cycle_rejection_are_atomic():
    from little_world.construction.connections import frames, rotate
    editor = assembly()
    base = editor.bodies[0]
    attachment = Attachment('socket', Transform((.1, .02, .04), (sqrt(.5), 0, sqrt(.5), 0)))
    editor._replace(replace(base, attachments=(attachment,)))
    editor.select('box_1')
    editor.snap('base', 'Bottom', 'socket', .002)
    source = frames(editor.selected)['Bottom']
    moved = rotate(editor.selected.transform.quaternion, source.position)
    assert tuple(a+b for a,b in zip(editor.selected.transform.position,moved)) == pytest.approx((.102,.02,.04))
    before = editor.blueprint
    editor.select('base')
    with pytest.raises(ValueError, match='descendant'):
        editor.snap('box_1', 'Bottom', 'Top')
    assert editor.blueprint == before


def test_exact_size_pose_and_joint_lifecycle():
    editor = assembly()
    editor.set_dimensions((.4, .02, .03))
    editor.snap('base', 'Back', 'Front')
    editor.configure_hinge(axis=(0, 2, 0), pivot=(-.2, 0, 0), damping=.07, limits=(-45,90))
    hinge = editor.selected_hinge()
    assert hinge.axis == (0,1,0)
    assert hinge.position == (-.2,0,0)
    assert hinge.limits == (-45,90)
    editor.set_motor(.6)
    assert editor.selected_motors()[0].max_torque == .6
    assert Blueprint.from_json(editor.blueprint.to_json()) == editor.blueprint
    before = editor.blueprint
    with pytest.raises(ValueError):
        editor.configure_hinge(limits=(90,-90))
    assert editor.blueprint == before
    editor.make_fixed()
    assert editor.selected_hinge() is None
    assert editor.selected_motors() == ()
    editor.undo()
    assert editor.blueprint == before


def test_hinge_legacy_defaults_and_invalid_values():
    editor = assembly()
    editor.snap('base','Bottom','Top')
    editor.configure_hinge()
    import json
    data=json.loads(editor.blueprint.to_json())
    for c in data['components']:
        if c['kind']=='hinge':
            c.pop('position'); c.pop('limits')
    assert Blueprint.from_json(json.dumps(data)) == editor.blueprint
    for limits in ((10,-10),(1,1),(0,float('inf'))):
        with pytest.raises(ValueError):
            Hinge('h','b',limits=limits)


def test_native_pivot_limits_and_motor_motion():
    mj = pytest.importorskip('mujoco')
    from little_world import World, Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.materials import METAL
    from math import radians
    base=Body('base',Geometry('box',(.1,.1,.1)),'metal')
    arm=Body('arm',Geometry('box',(.3,.02,.02)),'metal',Transform((.2,0,.1)),parent='base')
    editor=AssemblyEditor(Blueprint((base,arm),(METAL,)))
    editor.select('arm')
    editor.configure_hinge(pivot=(-.15,0,0), damping=.03, limits=(-30,30))
    editor.set_motor(.15)
    backend=MujocoBackend()
    with World(backend,Scene((Entity('test',editor.blueprint),))) as world:
        world.start()
        j=backend.model.joint('test/'+editor.selected_hinge().id)
        assert j.pos == pytest.approx((-.15,0,0))
        assert j.range == pytest.approx((-radians(30),radians(30)))
        assert j.limited[0]
        name='test/'+editor.selected_motors()[0].id
        for _ in range(1500):
            world.step({name:.15})
        angle=backend.data.qpos[j.qposadr[0]]
        assert radians(25) < angle < radians(33)
