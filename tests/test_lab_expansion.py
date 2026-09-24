import pytest
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor
from little_world.core.component import Body,Camera
from little_world.core.blueprint import Blueprint
from little_world.materials import METAL

@pytest.mark.parametrize('item,count', [('lab_ur_station',6),('lab_gen3_mobile',7),('lab_tilt_table',1)])
def test_expanded_assembly_controls(item,count):
    ed=AssemblyEditor(Blueprint((),(METAL,)));ed.add_catalog(item,'Floor')
    assert len([c for c in ed.blueprint.controllers if c.kind=='keyboard_position'])==count
    assert Blueprint.from_json(ed.blueprint.to_json())==ed.blueprint

def test_inspection_camera_and_loose_objects():
    assert any(isinstance(c,Camera) for c in BY_ID['lab_inspection_station'].blueprint().components)
    for item in ('lab_test_cylinder','lab_test_ball','lab_sorting_tray'):
        bp=BY_ID[item].blueprint()
        assert next(c for c in bp.components if isinstance(c,Body) and c.parent is None).dynamic

@pytest.mark.parametrize('item,wheels',[('lab_wide_base',6),('lab_delivery_platform',4),('lab_gen3_mobile',4)])
def test_new_platforms_drive(item,wheels):
    from test_lab_equipment import test_mobile_lab_base_moves
    test_mobile_lab_base_moves(item,wheels)

def test_powered_tilting_table_moves():
    pytest.importorskip('mujoco')
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.scene import Scene
    from little_world.core.entity import Entity
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    ed=AssemblyEditor(Blueprint((),(METAL,)));ed.add_catalog('lab_tilt_table','Floor')
    backend=MujocoBackend();backend.compile(Scene((Entity('machine',ed.blueprint),)),.002)
    try:
        control=MujocoKeyboardControl(backend,ed.blueprint);control.press('R')
        for _ in range(300):backend.step(control.step_commands(.002))
        assert backend.data.qpos[0]>.1
    finally:backend.close()
