"""Original workcell fixtures and composed equipment; estimated generic parameters."""
from dataclasses import replace
from little_world.core.component import Body,Geometry,Transform,Hinge,Motor
from little_world.core.blueprint import Blueprint


def entries(Part):
    rows=(
        ('lab_wide_base','Wide six-wheel equipment base','Platforms','Broad powered deck for experiments needing more mounting space.','6 drives / 18 Nm each',(1.15,.78,.22),'lab_mobile','Floor'),
        ('lab_delivery_platform','Cargo delivery platform','Platforms','Powered platform with a shallow tray and retaining rails.','4 drives / open cargo deck',(.8,.65,.4),'lab_delivery','Floor'),
        ('lab_tilt_table','Powered tilting table','Positioning','Motorized cradle tilts a workpiece platform around one horizontal axis.','R/V tilt / +/-45 deg',(.4,.3,.22),'lab_tilt','Top'),
        ('lab_peg_fixture','Peg locating fixture','Fixtures','Four locating posts on a plate for positioning compatible workpieces.','Passive posts / no clamp',(.24,.20,.065),'lab_pegs','Top'),
        ('lab_sorting_tray','Four-compartment sorting tray','Handling','Open tray with four separate pockets for sorting small rigid objects.','Loose sorting container',(.36,.28,.08),'lab_sorting','Floor'),
        ('lab_storage_rack','Three-level storage rack','Workcells','Anchored open shelves for arranging rigid payloads.','3 shelves / fixed frame',(.8,.45,1.0),'lab_rack','Floor'),
        ('lab_test_ramp','Traction test ramp','Test equipment','Anchored inclined surface for driving and sliding experiments.','12 degree fixed incline',(.8,.6,.18),'lab_ramp','Floor'),
        ('lab_test_cylinder','Cylindrical grasp sample','Test objects','Loose plastic cylinder for testing grasps and V-block support.','60 mm diameter / 140 mm long',(.06,.06,.14),'lab_cylinder','Floor'),
        ('lab_test_ball','Rubber grasp ball','Test objects','Loose solid rubber sphere for rolling and contact experiments.','80 mm diameter',(.08,.08,.08),'lab_ball','Floor'),
        ('lab_inspection_station','Overhead inspection station','Assembled workcells','Workbench and downward RGB camera already assembled.','Camera + fixed workbench',(1.2,.8,1.45),'lab_inspection','Floor'),
        ('lab_ur_station','UR5e pedestal workcell','Assembled robots','Sourced six-axis UR5e mounted on an anchored pedestal.','6 axes / no gripper',(.9,.9,1.5),'lab_ur_cell','Floor'),
        ('lab_gen3_mobile','Kinova mobile manipulator','Assembled robots','Sourced Kinova Gen3 arm on a powered mobile platform.','7 axes + wrist camera / no gripper',(1.,.65,1.2),'lab_gen3_cell','Floor'),
    )
    return tuple(Part(*r) for r in rows)


COMPOSED={'lab_delivery_platform':('lab_mobile_base',None),
          'lab_inspection_station':('lab_workbench','lab_camera_gantry'),
          'lab_ur_station':('lab_pedestal','ur5e'),
          'lab_gen3_mobile':('lab_mobile_base','kinova_gen3')}


def make_equipment(item):
    from .lab_equipment import PALETTE
    from little_world.construction.docking import grounded,dock
    if item.id in COMPOSED:
        from .catalog import BY_ID
        from little_world.construction.editor import AssemblyEditor
        base,attachment=COMPOSED[item.id];ed=AssemblyEditor(BY_ID[base].blueprint())
        if attachment:dock(ed,attachment,'root','Top')
        bp=ed.blueprint
        if item.id=='lab_delivery_platform':
            rails=tuple(Body('cargo_rail_'+str(i),Geometry('box',size),'lab_blue',Transform(pos),'root') for i,(size,pos) in enumerate((
                ((.78,.018,.10),(0,.24,.075)),((.78,.018,.10),(0,-.24,.075)),((.018,.48,.10),(-.38,0,.075)))))
            bp=replace(bp,components=bp.components+rails)
        return bp
    parts=[]
    def box(name,size,pos=(0,0,0),mat='metal',parent='root',q=(1,0,0,0)):
        parts.append(Body(name,Geometry('box',size),mat,Transform(pos,q),parent))
    v=item.variant
    if v=='lab_tilt':
        box('root',(.4,.3,.02),parent=None)
        for i,y in enumerate((-.13,.13)):box('support_'+str(i),(.10,.025,.16),(0,y,.09),'lab_dark')
        box('tilt_deck',(.36,.22,.018),(0,0,.19))
        parts.extend((Hinge('tilt_joint','tilt_deck',axis=(0,1,0),limits=(-45,45),damping=.8),Motor('tilt_motor','tilt_joint',20)))
        for i,y in enumerate((-.10,.10)):box('lip_'+str(i),(.35,.012,.025),(0,y,.02),'lab_blue','tilt_deck')
    elif v=='lab_pegs':
        box('root',(.24,.20,.015),parent=None)
        for i,(x,y) in enumerate(((-.08,-.06),(-.08,.06),(.08,-.06),(.08,.06))):
            parts.append(Body('peg_'+str(i),Geometry('cylinder',(.009,.05)),'lab_dark',Transform((x,y,.0325)),'root'))
    elif v=='lab_sorting':
        box('root',(.36,.28,.008),mat='lab_blue',parent=None)
        for i,y in enumerate((-.136,0,.136)):box('long_wall_'+str(i),(.36,.008,.08),(0,y,.044),'lab_blue')
        for i,x in enumerate((-.176,0,.176)):box('cross_wall_'+str(i),(.008,.264,.08),(x,0,.044),'lab_blue')
    elif v=='lab_rack':
        box('root',(.8,.45,.025),parent=None)
        for i,z in enumerate((.45,.90)):box('shelf_'+str(i),(.8,.45,.025),(0,0,z))
        for i,(x,y) in enumerate(((-.38,-.205),(-.38,.205),(.38,-.205),(.38,.205))):box('post_'+str(i),(.035,.035,1.),(x,y,.48),'lab_dark')
    elif v=='lab_ramp':
        from little_world.construction.connections import euler_quaternion
        box('root',(.8,.6,.025),parent=None,q=euler_quaternion((0,-12,0)))
    elif v in ('lab_cylinder','lab_ball'):
        g=Geometry('cylinder',(.03,.14)) if v=='lab_cylinder' else Geometry('sphere',(.04,))
        parts.append(Body('root',g,'lab_blue' if v=='lab_cylinder' else 'rubber'))
    else:raise ValueError('Unknown lab expansion: '+item.id)
    bp=Blueprint(tuple(parts),PALETTE)
    return grounded(bp,'root',v in ('lab_sorting','lab_cylinder','lab_ball')) if item.mount=='Floor' else bp
