"""Example mobile base assembled from the same catalog hardware as the UI."""
from dataclasses import replace
from little_world.assets.catalog import BY_ID
from little_world.construction.docking import grounded
from little_world.construction.editor import AssemblyEditor
from little_world.core.component import Body, Transform
from little_world.core.blueprint import ControllerSpec


def mobile_platform_blueprint():
    bp=BY_ID['open_chassis'].blueprint()
    # Chassis root is its left rail; centre the complete frame over the origin. It is
    # assembled high and set down at the end, so it stands on its wheels when a run starts.
    bp=replace(bp,components=tuple(replace(c,transform=Transform((0,-.1025,.13))) if isinstance(c,Body) and c.parent is None else c for c in bp.components))
    editor=AssemblyEditor(bp)
    actuators=[]
    for side in (1,-1):
        editor.select('root')
        editor.add_catalog('gearmotor_37')
        motor_root=editor.selection
        editor.set_pose((0,.1025+side*.072,-.035),(-90*side,0,0))
        shaft=motor_root.removesuffix('_root')+'_output_shaft'
        editor.select(shaft)
        editor.configure_hinge(axis=(0,0,side))  # common forward sign on mirrored motors
        actuators.append(editor.selected_motors()[0].id)
        editor.add_catalog('tread_wheel')
        editor.snap(shaft,'Bottom','output')
        editor.make_fixed()  # wheel is fastened to the driven output, not free on it
    for xx in (-.12,.12):
        editor.select('root')
        editor.add_catalog('swivel_caster')
        editor.set_pose((xx,.1025,-.020))
    return grounded(replace(editor.blueprint,controllers=(ControllerSpec('drive','differential_torque',tuple(actuators)),)),'root')
