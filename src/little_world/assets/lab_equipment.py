"""Generic lab/workcell assemblies, inspired by common equipment categories.

Original geometry and estimated parameters; no vendor specifications are implied.
"""
from dataclasses import replace
from math import sqrt
from little_world.core.component import Body,Geometry,Transform,Hinge,Motor,Camera
from little_world.core.blueprint import Blueprint
from little_world.materials import METAL,RUBBER,PLASTIC,WOOD

BLUE=replace(PLASTIC,id='lab_blue',rgba=(.07,.26,.48,1),roughness=.5)
DARK=replace(METAL,id='lab_dark',rgba=(.12,.15,.18,1))
# Cardboard, not wood: no sourced pairs, so it keeps its illustrative coefficient.
CARTON=replace(WOOD,id='lab_carton',density=150,rgba=(.64,.43,.22,1),surface=None)
PALETTE=(METAL,RUBBER,PLASTIC,WOOD,BLUE,DARK,CARTON)


def entries(Part):
    rows=(
        ('lab_mobile_base','Mobile manipulation platform','Platforms','Wide four-wheel base with motors and a clear deck for an arm.','4 drives / 12 Nm each',(.8,.65,.25),'lab_mobile','Floor'),
        ('lab_research_rover','Six-wheel research platform','Platforms','Long six-wheel differential-drive base for indoor experiments.','6 drives / 12 Nm each',(1.0,.7,.25),'lab_mobile','Floor'),
        ('lab_workbench','Robot workbench','Workcells','Anchored table with a mounting grid and open space underneath.','1200 x 800 mm worktop',(1.2,.8,.78),'lab_table','Floor'),
        ('lab_compact_bench','Compact experiment table','Workcells','Small anchored workbench for tabletop manipulation.','800 x 600 mm worktop',(.8,.6,.65),'lab_table','Floor'),
        ('lab_pedestal','Robot mounting pedestal','Workcells','Anchored column with a wide foot and an arm mounting plate.','Fixed arm support',(.48,.48,.60),'lab_pedestal','Floor'),
        ('lab_index_table','Powered indexing table','Positioning','Motorized rotary table for presenting objects at different angles.','Q/E rotates / +/-180 deg',(.36,.36,.07),'lab_index','Top'),
        ('lab_roller_table','Passive roller conveyor','Handling','Twelve freely rotating rollers and a supporting frame. Objects move when pushed.','Passive / no belt drive',(.95,.38,.55),'lab_rollers','Floor'),
        ('lab_parts_bin','Open parts bin','Handling','Open container for sorting and pick-and-place experiments.','Rigid open container',(.30,.22,.14),'lab_bin','Floor'),
        ('lab_pallet','Small logistics pallet','Handling','Slatted wooden pallet with open fork entries.','Rigid cargo support',(.60,.40,.09),'lab_pallet','Floor'),
        ('lab_payload_box','Small handling box','Test objects','Small rigid carton-shaped payload for stacking and grasp tests.','Estimated 0.45 kg',(.20,.15,.10),'lab_box','Floor'),
        ('lab_v_fixture','V-block workholding fixture','Fixtures','Fixed angled supports for cradling a cylindrical workpiece.','Passive V-shaped cradle',(.18,.16,.065),'lab_fixture','Top'),
        ('lab_camera_gantry','Overhead camera gantry','Sensors','Bench-mountable frame with a real downward-looking RGB camera.','RGB view / fixed frame',(.65,.15,.65),'lab_gantry','Top'),
        ('lab_panda_mobile','Panda mobile manipulator','Assembled robots','Panda arm and gripper already mounted on the generic powered platform.','WASD + arm + gripper',(1.0,.65,1.05),'lab_mobile_cell','Floor'),
        ('lab_panda_station','Panda tabletop workcell','Assembled robots','Panda arm and gripper installed on an anchored experiment bench.','Anchored arm + gripper',(1.2,.8,1.6),'lab_fixed_cell','Floor'),
    )
    from .lab_expansion import entries as more_entries
    return tuple(Part(*r) for r in rows)+more_entries(Part)


def make_equipment(item):
    from .lab_expansion import entries as more_entries,make_equipment as make_extra
    if item.id in {p.id for p in more_entries(type(item))} and item.variant!='lab_mobile':return make_extra(item)
    if item.variant in ('lab_mobile_cell','lab_fixed_cell'):
        from .catalog import BY_ID
        from little_world.construction.editor import AssemblyEditor
        from little_world.construction.docking import dock
        base='lab_mobile_base' if item.variant=='lab_mobile_cell' else 'lab_workbench'
        editor=AssemblyEditor(BY_ID[base].blueprint());dock(editor,'franka_panda','root','Top')
        return editor.blueprint
    if item.variant=='lab_mobile':return mobile_base(item)
    parts=[]
    def box(name,size,pos=(0,0,0),mat='metal',parent='root',q=(1,0,0,0)):
        parts.append(Body(name,Geometry('box',size),mat,Transform(pos,q),parent))
    def cyl(name,r,h,pos,mat='metal',parent='root',q=(1,0,0,0)):
        parts.append(Body(name,Geometry('cylinder',(r,h)),mat,Transform(pos,q),parent))
    v=item.variant;x,y,z=item.dimensions
    if v=='lab_table':
        box('root',(x,y,.04),parent=None)
        for i,(a,b) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
            pos=(a*(x/2-.065),b*(y/2-.065),-z/2)
            box('leg_'+str(i),(.045,.045,z-.02),pos,'lab_dark')
            cyl('foot_'+str(i),.040,.018,(pos[0],pos[1],-z+.019),'rubber')
        for i,side in enumerate((-1,1)):
            box('rail_'+str(i),(x-.08,.025,.04),(0,side*(y/2-.065),-.15),'lab_dark')
        for i in range(7):
            for j in range(5):cyl(f'grid_{i}_{j}',.003,.001,((i-3)*x/8,(j-2)*y/6,.0205),'lab_dark')
    elif v=='lab_pedestal':
        box('root',(.28,.28,.025),parent=None)
        box('column',(.13,.13,z-.06),(0,0,-z/2),'lab_dark')
        box('foot',(.48,.48,.025),(0,0,-z+.025))
        for i,(a,b) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):cyl('bolt_'+str(i),.008,.006,(a*.19,b*.19,-z+.04),'lab_dark')
    elif v=='lab_index':
        box('root',(.25,.25,.035),parent=None)
        cyl('platter',.18,.015,(0,0,.029),'lab_dark')
        parts.extend((Hinge('rotation','platter',damping=.4,limits=(-180,180)),Motor('rotation_motor','rotation',12)))
        for i in range(5):
            for j in range(5):
                if (i-2)**2+(j-2)**2<=5:cyl(f'mark_{i}_{j}',.003,.001,((i-2)*.055,(j-2)*.055,.008),'metal','platter')
    elif v=='lab_rollers':
        box('root',(x,y,.025),parent=None)
        for i,side in enumerate((-1,1)):
            box('side_'+str(i),(x,.018,.08),(0,side*(y/2-.009),.03),'lab_blue')
            for j,end in enumerate((-1,1)):box(f'leg_{i}_{j}',(.04,.04,z-.04),(end*(x/2-.08),side*(y/2-.04),-z/2+.02),'lab_dark')
        for i in range(12):
            name='roller_'+str(i);cyl(name,.029,y-.05,((i-5.5)*.075,0,.045),'metal',q=(sqrt(.5),-sqrt(.5),0,0))
            parts.append(Hinge(name+'_joint',name,damping=.002))
    elif v=='lab_bin':
        box('root',(x,y,.008),mat='lab_blue',parent=None)
        for i,side in enumerate((-1,1)):
            box('long_wall_'+str(i),(x,.008,z),(0,side*(y/2-.004),z/2),'lab_blue')
            box('short_wall_'+str(i),(.008,y,z),(side*(x/2-.004),0,z/2),'lab_blue')
    elif v=='lab_pallet':
        box('root',(x,.055,.018),mat='wood',parent=None)
        for i,side in enumerate((-1,1)):
            box('deck_'+str(i),(x,.09,.018),(0,side*.15,0),'wood')
            box('runner_'+str(i),(.065,y,.06),(side*.23,0,-.04),'wood')
            box('bottom_'+str(i),(.08,y,.012),(side*.23,0,-.076),'wood')
    elif v=='lab_box':box('root',(x,y,z),mat='lab_carton',parent=None)
    elif v=='lab_fixture':
        from little_world.construction.connections import euler_quaternion
        box('root',(x,y,.012),parent=None)
        for i,side in enumerate((-1,1)):
            box('jaw_'+str(i),(.15,.018,.055),(0,side*.036,.024),'lab_dark',q=euler_quaternion((side*-40,0,0)))
    elif v=='lab_gantry':
        box('root',(.65,.035,.015),mat='lab_dark',parent=None)
        box('first_foot',(.10,.15,.015),(-.3,0,0),'lab_dark')
        box('second_foot',(.10,.15,.015),(.3,0,0),'lab_dark')
        for i,a in enumerate((-.3,.3)):box('post_'+str(i),(.035,.035,z),(a,0,z/2),'lab_dark')
        box('beam',(.64,.035,.035),(0,0,z),'lab_dark')
        box('camera',(.07,.07,.045),(0,0,z-.035),'lab_blue')
        cyl('lens',.018,.012,(0,0,-.03),'lab_dark','camera')
        parts.append(Camera('overhead_rgb','camera',Transform((0,0,-.04)),fovy=60))
    else:raise ValueError('Unknown lab equipment')
    from little_world.construction.docking import grounded
    mobile=v in ('lab_bin','lab_pallet','lab_box')
    bp=Blueprint(tuple(parts),PALETTE)
    return grounded(bp,'root',mobile) if item.mount=='Floor' else bp


def mobile_base(item):
    from little_world.scripting import RobotBuilder
    from little_world.construction.editor import AssemblyEditor
    from little_world.construction.docking import wheel_at,grounded
    long=item.id in ('lab_research_rover','lab_wide_base');wide=item.id=='lab_wide_base'
    length,width=(1.15,.64) if wide else (1.,.56) if long else (.80,.50)
    bp=RobotBuilder.chassis(length,width,.024).blueprint
    bp=replace(bp,components=tuple(replace(c,id='root') if c.id=='chassis' else c for c in bp.components),materials=PALETTE)
    editor=AssemblyEditor(bp)
    for side in ('Left','Right'):
        for x in ((-.40,0,.40) if wide else (-.34,0,.34) if long else (-.27,.27)):wheel_at(editor,'drive_220','root',side,x)
    extra=(Body('undertray',Geometry('box',(length-.10,width-.08,.045)),'lab_dark',Transform((0,0,-.045)),'root'),
           Body('front_bumper',Geometry('box',(.035,width,.065)),'rubber',Transform((length/2,0,-.015)),'root'),
           Body('rear_bumper',Geometry('box',(.035,width,.065)),'rubber',Transform((-length/2,0,-.015)),'root'))
    bp=replace(editor.blueprint,components=tuple(replace(c,max_torque=18 if wide else 12) if isinstance(c,Motor) else c for c in editor.blueprint.components)+extra)
    return grounded(bp,'root',True)
