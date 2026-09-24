"""A catalog arm bolted to a driven cart; one articulated dynamic assembly."""
from dataclasses import replace
from little_world.construction.editor import AssemblyEditor
from little_world.robots.mobile_platform import mobile_platform_blueprint
from little_world.robots.arm_lab import attach_arm
from little_world.core.component import Body,Geometry,Transform,Attachment


def mobile_manipulator_blueprint():
    editor=AssemblyEditor(mobile_platform_blueprint())
    # A mounting deck spans the chassis rails, leaving the driven shafts independent.
    deck=Body('arm_deck',Geometry('box',(.18,.18,.012)),'metal',
              Transform((-.035,.1025,.022)),parent='root',
              attachments=(Attachment('arm_mount',Transform((0,0,.006))),))
    editor.load(replace(editor.blueprint,components=(*editor.blueprint.components,deck)))
    editor.select('arm_deck')
    return attach_arm(editor,'robot_arm_compact')
