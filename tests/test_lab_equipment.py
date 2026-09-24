import pytest
from little_world.assets.catalog import BY_ID,CATALOG
from little_world.core.component import Body,Motor,Hinge,Camera
from little_world.core.blueprint import Blueprint
from little_world.construction.editor import AssemblyEditor
from little_world.materials import METAL


@pytest.mark.parametrize('item',[p.id for p in CATALOG if p.variant.startswith('lab_')])
def test_lab_equipment_portable_floor_and_undo(item):
    bp=BY_ID[item].blueprint();assert bp==Blueprint.from_json(bp.to_json())
    ed=AssemblyEditor(Blueprint((),(METAL,)));ed.add_catalog(item,'Floor')
    root=ed.selected
    assert root.dynamic==next(c.dynamic for c in bp.components if isinstance(c,Body) and c.parent is None)
    ed.undo();assert not ed.bodies


def test_real_arm_mounts_to_generic_platform_and_table():
    from little_world.construction.docking import dock
    for part in ('lab_mobile_base','lab_workbench','lab_pedestal'):
        ed=AssemblyEditor(BY_ID[part].blueprint());dock(ed,'franka_panda','root','Top')
        assert len([c for c in ed.blueprint.controllers if c.kind=='keyboard_position'])==8
        assert ed.selected.parent=='root'


def test_roller_table_is_passive_and_camera_is_real():
    rollers=BY_ID['lab_roller_table'].blueprint()
    assert len([c for c in rollers.components if isinstance(c,Hinge)])==12
    assert not any(isinstance(c,Motor) for c in rollers.components)
    assert any(isinstance(c,Camera) for c in BY_ID['lab_camera_gantry'].blueprint().components)


@pytest.mark.parametrize('item,wheels',[('lab_mobile_base',4),('lab_research_rover',6),('lab_panda_mobile',4)])
def test_mobile_lab_base_moves(item,wheels):
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    from little_world.scenes.room import room_entity
    from little_world.control.mujoco_drive import MujocoDrive
    from little_world.construction.docking import grounded
    bp=BY_ID[item].blueprint()
    backend=MujocoBackend();backend.compile(Scene((room_entity(),Entity('machine',bp))),.002)
    drive=MujocoDrive(backend,bp);assert len(drive.channels)==wheels
    start=backend.data.xpos[backend.model.body('machine/root').id].copy()
    for _ in range(1000):backend.step(drive.step_commands((5,5),.002))
    assert backend.data.xpos[backend.model.body('machine/root').id,0]>start[0]+.1
    backend.close()


@pytest.mark.parametrize('item',['lab_panda_mobile','lab_panda_station','lab_index_table'])
def test_inserted_assemblies_keep_default_controls(item):
    ed=AssemblyEditor(Blueprint((),(METAL,)));ed.add_catalog(item,'Floor')
    controls=[c for c in ed.blueprint.controllers if c.kind=='keyboard_position']
    assert len(controls)==(1 if item=='lab_index_table' else 8)
    keys=[k for c in controls for k in (c.positive_key,c.negative_key)]
    assert len(keys)==len(set(keys))


def test_fixed_workcell_and_rotary_actuation():
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    ed=AssemblyEditor(BY_ID['lab_workbench'].blueprint())
    from little_world.construction.docking import dock
    dock(ed,'lab_index_table','root','Top')
    bp=ed.blueprint;backend=MujocoBackend();backend.compile(Scene((Entity('machine',bp),)),.002)
    control=MujocoKeyboardControl(backend,bp);control.press('Q')
    assert backend.model.nq==1  # anchored support, only the rotary joint moves
    for _ in range(300):backend.step(control.step_commands(.002))
    assert backend.data.qpos[0]>.10
    backend.close()
