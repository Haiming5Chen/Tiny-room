import pytest
from little_world.assets.catalog import CATALOG, BY_ID
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.core.component import Body,Hinge,Motor


def test_hardware_modules_preserve_materials_outputs_and_internal_joints():
    editor=AssemblyEditor(starter_blueprint())
    editor.add_catalog('gearmotor_37')
    materials={m.id for m in editor.blueprint.materials}
    assert {'anodized','steel','copper'} <= materials
    shaft=next(b for b in editor.bodies if b.id.endswith('output_shaft'))
    assert 'output' in {a.id for a in shaft.attachments}
    editor.select(shaft.id)
    assert len(editor.selected_motors())==1
    assert editor.selected_hinge() is not None
    editor.add_catalog('flange_hub')
    editor.snap(shaft.id,'Back','output')
    assert editor.selected.parent==shaft.id


def test_swivel_caster_has_independent_joint_axes():
    bp=BY_ID['swivel_caster'].blueprint()
    assert len([c for c in bp.components if isinstance(c,Hinge)])==2
    assert not any(isinstance(c,Motor) for c in bp.components)
    wheel=next(c for c in bp.components if isinstance(c,Body) and c.id=='wheel')
    assert wheel.parent=='swivel'
    from little_world.construction.connections import rotate
    assert rotate(wheel.transform.quaternion,(0,0,1))==pytest.approx((0,1,0))


def test_compound_catalog_mount_uses_full_geometry_envelope():
    from little_world.construction.connections import module_bounds
    for item in (p for p in CATALOG if p.variant.startswith('hw_')):
        editor=AssemblyEditor(starter_blueprint())
        lower,upper=module_bounds(item.blueprint())
        editor.add_catalog(item.id,mount='Top')
        assert editor.selected.transform.position[2]+lower[2]==pytest.approx(.045+.002)


def test_hardware_mobile_platform_moves_with_output_shafts():
    pytest.importorskip('mujoco')
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.scenes.room import room_entity
    from little_world.physics.mujoco_backend import MujocoBackend
    bp=mobile_platform_blueprint()
    motors=bp.controllers[0].actuators
    assert len(motors)==2
    with World(MujocoBackend(),Scene((room_entity(),Entity('mobile',bp)))) as world:
        first=world.start()
        # Mirrored motor axes use a common forward command sign.
        for _ in range(1000):
            last=world.step({'mobile/'+motors[0]:.4,'mobile/'+motors[1]:.4})
        delta=last.bodies['mobile/root'].pose.position[0]-first.bodies['mobile/root'].pose.position[0]
        assert abs(delta)>.03
