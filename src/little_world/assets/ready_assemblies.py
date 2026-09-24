"""Useful complete mechanisms composed of the same editable kit components."""
from dataclasses import replace
from math import sqrt
from little_world.core.component import Body,Geometry,Transform,Attachment,Hinge,Motor,Camera
from little_world.core.blueprint import Blueprint
from little_world.materials import METAL,RUBBER,PLASTIC


def entries(Part):
    rows=(
        ('ready_rover_4','Four-wheel rover base','Bases','A complete chassis, four powered wheels and drive controls.','4 motors included',(.50,.40,.17),'ready_base','Floor'),
        ('ready_rover_6','Six-wheel rover base','Bases','A longer chassis with six powered wheels and drive controls.','6 motors included',(.72,.44,.17),'ready_base','Floor'),
        ('ready_delivery_base','Delivery cart base','Bases','Two drive wheels and two swivel supports, assembled and wired for control.','2 motors + casters',(.36,.34,.17),'ready_base','Floor'),
        ('ready_pick_arm_compact','Compact picking arm','Arms','Compact four-axis arm with a contact gripper already fitted.','Arm + gripper + controls',(.32,.10,.12),'ready_arm','Top'),
        ('ready_pick_arm_standard','General-purpose picking arm','Arms','Four-axis arm with a contact gripper already fitted.','Arm + gripper + controls',(.49,.14,.16),'ready_arm','Top'),
        ('ready_pick_arm_long','Long-reach picking arm','Arms','Long four-axis arm with a wide contact gripper already fitted.','Arm + gripper + controls',(.68,.19,.23),'ready_arm','Top'),
        ('ready_fork','Powered tilting forks','Tools','A motorized fork attachment for scooping underneath and tilting cargo.','Motor + lift controls',(.22,.16,.10),'ready_fork','Front'),
        ('ready_scoop','Powered scoop bucket','Tools','A rigid bucket with a powered tilt joint for pushing and tipping objects.','Motor + tilt controls',(.20,.22,.11),'ready_scoop','Front'),
        ('ready_cargo_tray','Powered tipping tray','Tools','A cargo tray with its hinge and motor built in.','Motor + tip controls',(.28,.22,.08),'ready_tray','Top'),
        ('ready_pan_tilt','Pan-tilt camera head','Sensors','An RGB camera on two powered axes with default controls.','Camera + 2 motors',(.09,.09,.13),'ready_camera','Top'),
    )
    return tuple(Part(*row) for row in rows)


def is_ready(item):
    return item.variant.startswith('lab_') or item.variant=='real_robot' or item.variant.startswith('ready_') or item.variant in (
        'drive','wheel','hw_tread','hw_arm','hw_arm_compact','hw_arm_long','hw_gripper','hw_gripper_compact',
        'hw_gripper_wide','hw_caster','hw_chassis','hw_arm_deck','hw_wrist','camera','mast','bumper') or item.id in (
        'chassis_plate','long_plate','chassis_compact','chassis_wide','chassis_heavy','chassis_micro','cross_frame')


def make_ready(item):
    if item.variant=='ready_base':
        from little_world.scripting import RobotBuilder
        if item.id=='ready_rover_4':length,width,positions=.50,.28,(-.16,.16)
        elif item.id=='ready_rover_6':length,width,positions=.72,.32,(-.25,0,.25)
        else:length,width,positions=.36,.24,(0,)
        robot=RobotBuilder.chassis(length,width,.025)
        # Keep the module root convention used by insertion and replacement.
        bp=robot.blueprint
        bp=replace(bp,components=tuple(replace(c,id='root') if c.id=='chassis' else c for c in bp.components))
        from little_world.construction.editor import AssemblyEditor
        editor=AssemblyEditor(bp)
        from little_world.construction.docking import wheel_at,grounded
        for side in ('Left','Right'):
            for x in positions:wheel_at(editor,'drive_130','root',side,x)
        if item.id=='ready_delivery_base':
            for x in (-.14,.14):
                editor.select('root');editor.add_catalog('swivel_caster','Bottom');editor.set_pose((x,0,-.04))
        return grounded(editor.blueprint,'root',True)
    if item.variant=='ready_arm':
        from .catalog import BY_ID
        from little_world.construction.editor import AssemblyEditor
        arm,grip={'ready_pick_arm_compact':('robot_arm_compact','gripper_compact'),
                  'ready_pick_arm_standard':('robot_arm','two_finger_gripper'),
                  'ready_pick_arm_long':('robot_arm_long','gripper_wide')}[item.id]
        editor=AssemblyEditor(BY_ID[arm].blueprint());editor.select('wrist')
        editor.add_catalog(grip);editor.snap('wrist','tool_mount','tool')
        return editor.blueprint
    parts=[]
    def box(name,size,pos=(0,0,0),parent='root',material='metal'):
        parts.append(Body(name,Geometry('box',size),material,Transform(pos),parent,dynamic=parent is None))
    def joint(name,body,axis,limits,torque,pivot=(0,0,0)):
        parts.extend((Hinge(name,body,axis,.08,pivot,limits),Motor(name+'_motor',name,torque)))
    if item.variant=='ready_camera':
        box('root',(.07,.07,.012),parent=None)
        box('pan',(.045,.045,.016),(0,0,.016),material='plastic')
        joint('pan_joint','pan',(0,0,1),(-160,160),1.)
        for i,side in enumerate((-1,1)):box('fork_'+str(i),(.02,.008,.065),(0,side*.029,.035),'pan')
        box('tilt',(.050,.050,.034),(0,0,.066),'pan','plastic')
        joint('tilt_joint','tilt',(0,-1,0),(-70,70),.7)
        parts.append(Body('lens',Geometry('cylinder',(.013,.020)),'metal',Transform((.032,0,0),(sqrt(.5),0,sqrt(.5),0)),'tilt'))
        parts.append(Camera('rgb','tilt',Transform((.046,0,0),(.5,.5,-.5,-.5))))
    else:
        tray=item.variant=='ready_tray'
        box('root',(.10,.18,.014) if tray else (.018,.16,.08),parent=None)
        box('moving',(.24,.20,.009) if tray else (.035,.16,.012),(.08,0,.025) if tray else (.035,0,-.025))
        joint('tilt_joint','moving',(0,-1,0),(-5,65),18. if tray else 12.,(-.1,0,0) if tray else (0,0,0))
        if item.variant=='ready_fork':
            for i,side in enumerate((-1,1)):box('tine_'+str(i),(.18,.022,.010),(.075,side*.06,0),'moving')
        else:
            length,width=(.24,.20) if tray else (.18,.21)
            if not tray:box('bucket_floor',(length,width,.009),(.07,0,0),'moving')
            cx=0 if tray else .07
            for i,side in enumerate((-1,1)):box('side_'+str(i),(length,.008,.05),(cx,side*width/2,.022),'moving')
            box('back_wall',(.008,width,.06),(cx-length/2,0,.025),'moving')
        for i,side in enumerate((-1,1)):box('motor_cover_'+str(i),(.038,.020,.045),(-.014,side*.088,0),material='plastic')
    root=parts[0]
    parts[0]=replace(root,attachments=(Attachment('mount',Transform((0,0,-root.geometry.size[2]/2),(0,1,0,0))),))
    return Blueprint(tuple(parts),(METAL,RUBBER,PLASTIC))
