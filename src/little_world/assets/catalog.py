"""Robot construction kit made from editable Blueprint primitives.

Procedural kits plus explicitly sourced registered robot assemblies. None are
claimed as calibrated commercial hardware.
Dimensions are metres. Module detail contributes ordinary rigid-body mass/inertia.
"""
from dataclasses import dataclass, replace
from math import pi, sin, cos, sqrt
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body, Geometry, Transform, Hinge, Motor, Camera, Attachment
from little_world.materials import METAL, RUBBER, WOOD, SKID, PLASTIC

PALETTE=(METAL,RUBBER,WOOD,SKID,PLASTIC)
AXLE=(sqrt(.5),-sqrt(.5),0,0)


@dataclass(frozen=True)
class CatalogPart:
    id: str
    title: str
    category: str
    description: str
    capability: str
    dimensions: tuple
    variant: str
    mount: str = 'Top'

    def blueprint(self):
        bp=make_part(self)
        return replace(bp,components=tuple(replace(c,catalog_part=self.id) if isinstance(c,Body) and c.parent is None else c for c in bp.components))


CATALOG=(
    CatalogPart('chassis_plate','Chassis plate','Structure','320 x 240 mm aluminium platform.','Rigid structure',(.32,.24,.018),'plate'),
    CatalogPart('long_plate','Long chassis plate','Structure','450 x 180 mm narrow platform.','Rigid structure',(.45,.18,.018),'plate'),
    CatalogPart('cross_frame','Cross frame','Structure','Two intersecting beams with raised deck.','Rigid structure',(.34,.28,.04),'cross'),
    CatalogPart('beam_short','Short beam','Structure','150 mm structural member.','Rigid structure',(.15,.035,.035),'beam'),
    CatalogPart('beam_long','Long beam','Structure','350 mm structural member.','Rigid structure',(.35,.035,.035),'beam'),
    CatalogPart('channel','U-channel beam','Structure','Open channel built from three walls.','Rigid structure',(.30,.055,.045),'channel'),
    CatalogPart('angle_bracket','L bracket','Structure','Right-angle mounting bracket.','Rigid structure',(.08,.07,.08),'angle'),
    CatalogPart('fork_bracket','Fork bracket','Structure','Open fork; no gripping actuator.','Rigid structure',(.12,.10,.06),'fork'),
    CatalogPart('standoff','Round standoff','Structure','Cylindrical 60 mm spacer.','Rigid structure',(.025,.025,.06),'standoff'),
    CatalogPart('axle','Axle shaft','Motion','180 mm crosswise shaft. Fixed mounting.','Rigid shaft',(.016,.18,.016),'axle'),
    CatalogPart('wheel_small','Small free wheel','Motion','120 mm wheel with a free hinge.','Passive wheel',(.12,.035,.12),'wheel','Left'),
    CatalogPart('wheel_large','Large free wheel','Motion','200 mm wheel with a free hinge.','Passive wheel',(.20,.045,.20),'wheel','Left'),
    CatalogPart('drive_left','Left drive module','Motion','170 mm wheel, hub and ideal torque motor.','Powered wheel',(.17,.045,.17),'drive','Left'),
    CatalogPart('drive_right','Right drive module','Motion','Right-side counterpart to left drive module.','Powered wheel',(.17,.045,.17),'drive','Right'),
    CatalogPart('skid_foot','Sliding support foot','Motion','Low-friction rigid foot; not a caster.','Passive contact',(.05,.05,.05),'skid','Bottom'),
    CatalogPart('hinge_arm','Hinged arm','Motion','Arm with a free Z-axis pivot.','Passive hinge',(.22,.045,.035),'hinge'),
    CatalogPart('camera_module','RGB camera module','Sensors','Rigid housing and live forward RGB camera.','RGB camera',(.065,.07,.05),'camera'),
    CatalogPart('camera_mast','Camera mast','Sensors','180 mm mast with a fixed RGB camera.','RGB camera',(.065,.07,.22),'mast'),
    CatalogPart('sensor_mount','Sensor mounting plate','Sensors','Small sensor shelf; includes no sensor.','Rigid mount',(.10,.08,.012),'plate'),
    CatalogPart('enclosure','Electronics enclosure','Housing','Rigid case and lid. No electronic simulation.','Rigid enclosure',(.12,.09,.05),'case'),
    CatalogPart('battery_tray','Battery tray','Housing','Open structural tray. No battery model.','Rigid enclosure',(.16,.08,.035),'tray'),
    CatalogPart('bumper','Rubber bumper','Housing','Solid rubber impact bar; no deformation.','Rigid contact',(.22,.03,.035),'bumper'),
)
from .hardware import entries
CATALOG=CATALOG+entries(CatalogPart)
# Explicit dimensional choices, all ordinary editable mechanical parts.
CATALOG=CATALOG+tuple(
    CatalogPart(f'wheel_{diameter}',f'{diameter} mm free wheel','Motion',f'{diameter} mm passive wheel with a free axle.','Passive wheel',(diameter/1000,width/1000,diameter/1000),'wheel','Left')
    for diameter,width in ((60,20),(80,25),(100,30),(150,40),(250,55),(300,65)))
CATALOG=CATALOG+tuple(
    CatalogPart(f'drive_{diameter}',f'{diameter} mm powered wheel','Motion',f'{diameter} mm wheel with an ideal 1 Nm motor; fits either side.','Powered wheel',(diameter/1000,width/1000,diameter/1000),'drive','Left')
    for diameter,width in ((100,30),(130,35),(220,50),(280,60)))
CATALOG=CATALOG+tuple(
    CatalogPart(id,title,'Structure','Structural platform; dimensions determine mass and mounting faces.','Rigid structure',size,'plate')
    for id,title,size in (('chassis_compact','Compact chassis / 220',(.22,.18,.018)),('chassis_wide','Wide chassis / 400',(.40,.36,.025)),('chassis_heavy','Thick chassis / 500',(.50,.32,.04)),('chassis_micro','Micro chassis / 140',(.14,.12,.012))))
CATALOG=CATALOG+tuple(
    CatalogPart(f'beam_{length}',f'{length} mm square beam','Structure','Square structural beam with face mounts.','Rigid structure',(length/1000,.04,.04),'beam')
    for length in (75,250,500))
CATALOG=CATALOG+tuple(
    CatalogPart(f'robot_arm_{label}',f'{label.title()} arm / {round(.38*scale*1000)} mm','Actuators','Four powered joints; dimensions and ideal torque caps scale with this family.','Articulated arm',(.38*scale,.10*scale,.11*scale),'hw_arm')
    for label,scale in (('micro',.45),('medium',.85),('xl',1.8)))
from .shaft_loads import entries as shaft_entries
CATALOG=CATALOG+shaft_entries(CatalogPart)
from .ready_assemblies import entries as ready_entries
CATALOG=CATALOG+ready_entries(CatalogPart)
CATALOG=CATALOG+(CatalogPart('franka_panda','Franka Panda + gripper','Real robots',
    'Menagerie model: seven-axis arm, coupled gripper, original meshes and inertias.',
    '7 axes + coupled gripper',(.809,.259,.813),'real_robot','Floor'),)
CATALOG=CATALOG+tuple(CatalogPart(id,title,'Real robots',
    'Sourced Menagerie arm with original meshes, inertias and position servos. No gripper included.',
    str(axes)+'-axis arm / no gripper',(.8,.3,.9),'real_robot','Floor')
    for id,title,axes in (('franka_fr3','Franka Research 3 arm',7),('kinova_gen3','Kinova Gen3 arm',7),('ur5e','UR5e industrial arm',6)))
from .lab_equipment import entries as lab_entries
CATALOG=CATALOG+lab_entries(CatalogPart)
BY_ID={item.id:item for item in CATALOG}


def make_part(item):
    if item.variant.startswith('lab_'):
        from .lab_equipment import make_equipment
        return make_equipment(item)
    if item.variant=='real_robot':
        from .robot_models import blueprint
        return blueprint(item.id)
    if item.variant.startswith('ready_'):
        from .ready_assemblies import make_ready
        return make_ready(item)
    if item.variant=='shaft_load':
        from .shaft_loads import make_load
        return make_load(item)
    if item.variant.startswith('hw_'):
        from .hardware import make_hardware
        return make_hardware(item)
    x,y,z=item.dimensions
    variant=item.variant
    parts=[]

    def body(name,shape,size,material='metal',position=(0,0,0),parent='root',quaternion=(1,0,0,0)):
        parts.append(Body(name,Geometry(shape,size),material,Transform(position,quaternion),parent,
                          dynamic=parent is None,
                          attachments=(Attachment('mount'),)))

    def box(name,size,position=(0,0,0),material='metal',parent='root'):
        body(name,'box',size,material,position,parent)

    if variant in ('plate','beam','bumper'):
        box('root',(x,y,z),material='rubber' if variant=='bumper' else 'metal',parent=None)
    elif variant=='standoff':
        body('root','cylinder',(x/2,z),parent=None)
    elif variant=='axle':
        body('root','cylinder',(x/2,y),parent=None,quaternion=AXLE)
    elif variant=='skid':
        body('root','sphere',(x/2,),material='skid',parent=None)
    elif variant=='cross':
        box('root',(x,.04,.02),parent=None)
        box('crossbar',(.04,y,.02),(0,0,.02))
        box('deck',(.12,.10,.012),(0,0,.036))
    elif variant in ('channel','angle','fork','tray'):
        # Each wall is actual editable collision geometry, not a filled box mesh.
        box('root',(x,y,.008),parent=None)
        if variant=='angle':
            box('upright',(.008,y,z),(-x/2+.004,0,z/2+.004))
        else:
            box('rail_left',(x,.008,z),(0,y/2-.004,z/2+.004))
            box('rail_right',(x,.008,z),(0,-y/2+.004,z/2+.004))
            if variant in ('fork','tray'):
                box('back',(.008,y,z),(-x/2+.004,0,z/2+.004))
    elif variant=='case':
        box('root',(x,y,z),material='plastic',parent=None)
        box('lid',(x+.004,y+.004,.005),(0,0,z/2+.0025))
    elif variant in ('wheel','drive'):
        body('root','cylinder',(x/2,y),material='rubber',parent=None,quaternion=AXLE)
        body('hub','cylinder',(x*.20,y+.008))
        body('rim_inner','cylinder',(x*.38,.004),position=(0,0,-y/2-.002))
        body('rim_outer','cylinder',(x*.38,.004),position=(0,0,y/2+.002))
        for i in range(6):
            a=i*pi/3
            body(f'bolt_{i}','cylinder',(.0025,.003),position=(x*.14*cos(a),x*.14*sin(a),y/2+.008))
        # Four hub spokes provide visible shape detail and rotate with the wheel.
        for i in range(4):
            q=(cos(i*pi/8),0,0,sin(i*pi/8))
            body(f'spoke_{i}','box',(x*.75,.009,.008),position=(0,0,y/2+.008),quaternion=q)
    elif variant=='hinge':
        box('root',(.045,.045,.012),parent=None)
        box('arm',(x,y,.015),(x/2-.02,0,.018))
        parts.append(Hinge('pivot','arm',position=(-x/2+.02,0,0)))
    elif variant in ('camera','mast'):
        if variant=='mast':
            box('root',(.02,.025,.18),parent=None)
            box('housing',(.055,.07,.04),(0,0,.11),'plastic')
            housing='housing'
        else:
            box('root',(.055,.07,.04),material='plastic',parent=None)
            housing='root'
        body('lens','cylinder',(.016,.022),'metal',(.033,0,0),housing,(sqrt(.5),0,sqrt(.5),0))
        parts.append(Camera('rgb',housing,Transform((.047,0,0),(.5,.5,-.5,-.5))))
    else:
        raise ValueError('Unsupported catalog variant')
    return Blueprint(tuple(parts),PALETTE)
