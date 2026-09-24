from dataclasses import replace
import json
import pytest
from little_world.core.material import Material
from little_world.core.blueprint import Blueprint
from little_world.robots.two_wheel import two_wheel_blueprint


def test_surface_roundtrip_and_old_blueprints():
    original=two_wheel_blueprint()
    assert Blueprint.from_json(original.to_json()) == original
    data=json.loads(original.to_json())
    for material in data['materials']:
        material.pop('texture');material.pop('roughness')
    legacy=Blueprint.from_json(json.dumps(data))
    assert all(m.texture is None for m in legacy.materials)
    with pytest.raises(ValueError):
        Material('bad',1000,roughness=2)


def test_unknown_surface_rejected_by_backend():
    pytest.importorskip('mujoco')
    from little_world import Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    bp=two_wheel_blueprint()
    bp=replace(bp,materials=tuple(replace(m,texture='missing') for m in bp.materials))
    with pytest.raises(ValueError,match='Unsupported texture'):
        MujocoBackend().compile(Scene((Entity('test',bp),)),.002)


def test_surface_texture_changes_native_material():
    pytest.importorskip('mujoco')
    from little_world import Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.construction.editor import AssemblyEditor
    editor=AssemblyEditor(two_wheel_blueprint())
    backend=MujocoBackend()
    ids=[]
    for material in ('metal','wood','rubber','plastic'):
        editor.material(material)
        backend.compile(Scene((Entity('machine',editor.blueprint),)),.002)
        geom=backend.model.geom('machine/chassis_geom').id
        mat=backend.model.geom_matid[geom]
        ids.append(int(backend.model.mat_texid[mat,1]))
        assert backend.model.ntex==5
    assert len(set(ids))==4
    backend.close()


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_rgb_surface_patterns_reach_rendered_pixels():
    mj=pytest.importorskip('mujoco')
    import numpy as np
    from little_world import Entity
    from little_world.core.scene import Scene
    from little_world.core.component import Body,Geometry
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.materials import WOOD,METAL,RUBBER,PLASTIC
    images=[]
    for material in (WOOD,METAL,RUBBER,PLASTIC):
        bp=Blueprint((Body('sample',Geometry('box',(.3,.3,.08)),material.id),),(material,))
        backend=MujocoBackend();backend.compile(Scene((Entity('test',bp),)),.002)
        camera=mj.MjvCamera();camera.distance=.7;camera.azimuth=110;camera.elevation=-55
        with mj.Renderer(backend.model,width=160,height=120) as renderer:
            renderer.update_scene(backend.data,camera=camera)
            rgb=renderer.render().copy();images.append(rgb)
            assert rgb.max()>rgb.min()
        backend.close()
    for a,b in zip(images,images[1:]):
        assert np.abs(a.astype(float)-b.astype(float)).mean()>3


def test_reapplying_library_material_upgrades_legacy_visual_only():
    from little_world.construction.editor import AssemblyEditor
    bp=two_wheel_blueprint()
    bp=replace(bp,materials=tuple(replace(m,texture=None,density=1234) for m in bp.materials))
    editor=AssemblyEditor(bp);editor.material('metal')
    metal=next(m for m in editor.blueprint.materials if m.id=='metal')
    assert metal.texture=='brushed_metal'
    assert metal.density==1234
