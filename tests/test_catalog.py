import pytest
from little_world.assets.catalog import CATALOG
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body, Camera, Hinge, Motor


@pytest.mark.parametrize('item',CATALOG,ids=lambda p:p.id)
def test_catalog_item_serializes_and_attaches_twice(item):
    bp=item.blueprint()
    assert Blueprint.from_json(bp.to_json())==bp
    editor=AssemblyEditor(starter_blueprint())
    for _ in range(2):
        editor.select('base')
        if item.mount=='output':
            editor.add_catalog('gearmotor_37')
            from little_world.construction.docking import dock
            dock(editor,item.id,editor.selection,'output')
        else:editor.add_catalog(item.id)
    editor.blueprint.validate()
    assert len({c.id for c in editor.blueprint.components})==len(editor.blueprint.components)


def test_drive_pair_camera_and_delete():
    editor=AssemblyEditor(starter_blueprint())
    editor.add_catalog('drive_right');editor.select('base');editor.add_catalog('drive_left')
    assert editor.blueprint.controllers[0].actuators[0].startswith('left_wheel')
    editor.select('base');editor.add_catalog('camera_module')
    assert len([c for c in editor.blueprint.components if isinstance(c,Camera)])==1
    editor.select('base');editor.delete()
    assert editor.blueprint.components==()


@pytest.mark.parametrize('item',CATALOG,ids=lambda p:p.id)
def test_catalog_compiles_and_steps(item):
    pytest.importorskip('mujoco')
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    editor=AssemblyEditor(starter_blueprint())
    if item.mount=='output':
        editor.add_catalog('gearmotor_37')
        from little_world.construction.docking import dock
        dock(editor,item.id,editor.selection,'output')
    else:editor.add_catalog(item.id)
    with World(MujocoBackend(),Scene((Entity('assembly',editor.blueprint),))) as world:
        world.start()
        for _ in range(10):
            state=world.step()
        assert state.time>0


def test_catalog_drive_pair_moves_through_mujoco():
    pytest.importorskip('mujoco')
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.scenes.room import room_entity
    editor=AssemblyEditor(starter_blueprint())
    editor.add_catalog('drive_left');editor.select('base');editor.add_catalog('drive_right')
    # Two driven wheels need fore/aft support to keep the chassis off the floor.
    for x in (-.12, .12):
        editor.select('base')
        editor.add_catalog('skid_foot')
        editor.move((x, 0, 0))
    names=editor.blueprint.controllers[0].actuators
    with World(MujocoBackend(),Scene((room_entity(),Entity('machine',editor.blueprint)))) as world:
        first=world.start()
        for _ in range(1000):
            last=world.step({'machine/'+name:.5 for name in names})
        assert last.bodies['machine/base'].pose.position[0] > first.bodies['machine/base'].pose.position[0]+.05
