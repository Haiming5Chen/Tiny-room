"""Matched procedural modules, not vendor-certified assemblies."""
from little_world.assets.catalog import BY_ID
from little_world.construction.editor import AssemblyEditor
from little_world.robots.arm_lab import attach_arm
from dataclasses import replace
from little_world.core.component import Body,Transform

FAMILIES={
    'Compact arm kit':('robot_arm_compact','gripper_compact'),
    'Standard arm kit':('robot_arm','two_finger_gripper'),
    'Long reach arm kit':('robot_arm_long','gripper_wide'),
}


def arm_family_blueprint(name):
    arm,gripper=FAMILIES[name]
    bp=BY_ID['arm_mount_deck'].blueprint()
    bp=replace(bp,components=tuple(replace(c,dynamic=False,transform=Transform((0,0,.006))) if isinstance(c,Body) and c.parent is None else c for c in bp.components))
    editor=AssemblyEditor(bp)
    return attach_arm(editor,arm,gripper)
