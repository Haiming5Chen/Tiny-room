"""Keyboard manipulation example; object grasping is ordinary frictional contact."""
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body,Geometry,Transform
from little_world.materials import METAL
from little_world.construction.editor import AssemblyEditor


def arm_lab_blueprint():
    base=Body('pedestal',Geometry('box',(.16,.16,.12)),'metal',Transform((0,0,.06)))
    editor=AssemblyEditor(Blueprint((base,),(METAL,)))
    return attach_arm(editor)


def attach_arm(editor,item_id='robot_arm',gripper_id='two_finger_gripper'):
    editor.add_catalog(item_id)
    arm=editor.selection.removesuffix('_root')
    editor.select(arm+'_wrist')
    editor.add_catalog(gripper_id)
    editor.snap(arm+'_wrist','tool_mount','tool')
    return editor.blueprint
