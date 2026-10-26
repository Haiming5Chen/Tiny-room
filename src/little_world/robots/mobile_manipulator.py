"""A catalog arm bolted to a driven cart; one articulated dynamic assembly."""
from dataclasses import replace
from little_world.construction.editor import AssemblyEditor
from little_world.robots.mobile_platform import CASTER_GAP, mobile_platform_blueprint
from little_world.robots.arm_lab import attach_arm
from little_world.core.component import Body,Geometry,Transform,Attachment


def mobile_manipulator_blueprint(caster_gap=CASTER_GAP):
    """The kit arm on the cart; `caster_gap`, how far its casters stand above the floor its drive
    wheels stand on (ADR 0041: ROCKING_GAP is the cart as it was, teetering between them)."""
    editor=AssemblyEditor(mobile_platform_blueprint(caster_gap))
    # A mounting deck spans the chassis rails, leaving the driven shafts independent.
    deck=Body('arm_deck',Geometry('box',(.18,.18,.012)),'metal',
              Transform((-.035,.1025,.022)),parent='root',
              attachments=(Attachment('arm_mount',Transform((0,0,.006))),))
    editor.load(replace(editor.blueprint,components=(*editor.blueprint.components,deck)))
    editor.select('arm_deck')
    return attach_arm(editor,'robot_arm_compact')
