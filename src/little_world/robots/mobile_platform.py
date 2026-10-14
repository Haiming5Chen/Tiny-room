"""Example mobile base assembled from the same catalog hardware as the UI."""
from dataclasses import replace
from little_world.assets.catalog import BY_ID
from little_world.construction.docking import grounded, subtree, world_bounds
from little_world.construction.editor import AssemblyEditor
from little_world.core.component import Body, Transform
from little_world.core.blueprint import ControllerSpec

CASTER_GAP=0.   # m each swivel caster's wheel stands above the floor the drive wheels stand on (ADR 0041)
ROCKING_GAP=.0065   # m: where the casters stood before ADR 0041 - the cart then teetered between them


def mobile_platform_blueprint(caster_gap=CASTER_GAP):
    """The kit cart: two driven tread wheels across its middle and a swivel caster ahead of
    and behind them, each caster `caster_gap` above the floor the drive wheels stand on."""
    bp=BY_ID['open_chassis'].blueprint()
    # Chassis root is its left rail; centre the complete frame over the origin. It is
    # assembled high and set down at the end, so it stands on its wheels when a run starts.
    bp=replace(bp,components=tuple(replace(c,transform=Transform((0,-.1025,.13))) if isinstance(c,Body) and c.parent is None else c for c in bp.components))
    editor=AssemblyEditor(bp)
    actuators,wheels,casters=[],[],[]
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
        wheels.append(editor.selection)
        editor.snap(shaft,'Bottom','output')
        editor.make_fixed()  # wheel is fastened to the driven output, not free on it
    for xx in (-.12,.12):
        editor.select('root')
        editor.add_catalog('swivel_caster')
        editor.set_pose((xx,.1025,-.020))
        casters.append(editor.selection)
    # Each caster reaches the floor the drive wheels stand on, so the cart stands on all four
    # and its load cannot rock it from one caster onto the other. Mounted 6.5 mm higher
    # (ROCKING_GAP), it teetered on its drive wheels between them: loaded behind its axle, 6
    # degrees as its arm reached over the Fetch cube, carrying the open jaws down onto it - but
    # that freedom to pitch is what let it climb curbs: on all four it climbs none (ADR 0041).
    floor=min(world_bounds(editor.blueprint,subtree(editor.blueprint,w))[0][2] for w in wheels)
    for caster in casters:
        low=world_bounds(editor.blueprint,subtree(editor.blueprint,caster))[0][2]
        editor.select(caster)
        x,y,z=editor.selected.transform.position
        editor.set_pose((x,y,z-(low-floor)+caster_gap))
    return grounded(replace(editor.blueprint,controllers=(ControllerSpec('drive','differential_torque',tuple(actuators)),)),'root')
