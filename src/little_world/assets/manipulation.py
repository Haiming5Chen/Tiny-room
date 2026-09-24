"""Articulated arm and contact gripper, built from ordinary Blueprint components."""
from dataclasses import replace
from math import sqrt
from little_world.core.component import Body,Geometry,Transform,Attachment,Hinge,Motor
from little_world.core.blueprint import Blueprint
from .hardware import PALETTE,QY


def make_manipulation(item):
    parts=[]
    def body(name,shape,size,pos=(0,0,0),parent='root',material='metal',q=(1,0,0,0)):
        parts.append(Body(name,Geometry(shape,size),material,Transform(pos,q),parent,dynamic=parent is None))
    def box(name,size,pos=(0,0,0),parent='root',material='metal'):
        body(name,'box',size,pos,parent,material)
    def cylinder(name,r,length,pos=(0,0,0),parent='root',material='steel',q=(1,0,0,0)):
        body(name,'cylinder',(r,length),pos,parent,material,q)
    def joint(name,body,axis=(0,-1,0),pivot=(0,0,0),limits=(-80,100),torque=3.):
        parts.extend((Hinge(name,body,axis,.08,pivot,limits),Motor(name+'_motor',name,torque)))
    def attach(name,label,pos,q=(1,0,0,0)):
        for i,p in enumerate(parts):
            if p.id==name:
                parts[i]=replace(p,attachments=(*p.attachments,Attachment(label,Transform(pos,q))))
                return
    variant=item.variant[3:]
    if variant in ('arm','arm_compact','arm_long'):
        box('root',(.10,.10,.012),parent=None,material='anodized')
        cylinder('yaw',.033,.026,(0,0,.019))
        joint('yaw_joint','yaw',(0,0,1),limits=(-160,160),torque=3.)
        for side in (-1,1):
            box('shoulder_fork_'+str(side+1),(.040,.008,.060),(0,side*.026,.040),'yaw')
        # Each link has its origin at its centre; hinges pivot at the proximal end.
        box('upper_arm',(.18,.022,.024),(.09,0,.060),'yaw','anodized')
        joint('shoulder_joint','upper_arm',pivot=(-.09,0,0),limits=(-65,110),torque=5.)
        cylinder('shoulder_cap',.024,.006,(-.09,.0295,0),'upper_arm','metal',QY)
        cylinder('shoulder_back',.024,.006,(-.09,-.0295,0),'upper_arm','metal',QY)
        box('forearm',(.16,.020,.022),(.17,0,0),'upper_arm','anodized')
        joint('elbow_joint','forearm',pivot=(-.08,0,0),limits=(-100,120),torque=3.)
        cylinder('elbow_cap',.021,.006,(-.08,.0245,0),'forearm','metal',QY)
        cylinder('elbow_back',.021,.006,(-.08,-.0245,0),'forearm','metal',QY)
        box('wrist',(.035,.045,.025),(.0975,0,0),'forearm')
        joint('wrist_joint','wrist',pivot=(-.0175,0,0),limits=(-90,90),torque=1.5)
        attach('wrist','tool',(.0175,0,0),(sqrt(.5),0,sqrt(.5),0))
        for name,length in (('upper_arm',.18),('forearm',.16)):
            for side in (-1,1):
                box(name+'_rail_'+str(side+1),(length-.045,.004,.006),(0,side*.014,.008),name)
    elif variant in ('gripper','gripper_compact','gripper_wide'):
        box('root',(.030,.085,.025),parent=None,material='anodized')
        box('palm_stop',(.020,.060,.025),(.025,0,0),material='rubber')
        for side in (-1,1):
            name='finger_'+('left' if side==1 else 'right')
            box(name,(.090,.010,.026),(.055,side*.040,0),material='metal')
            joint(name+'_joint',name,(0,0,-side),(-.045,0,0),limits=(-12,30),torque=.6)
            box(name+'_pad',(.075,.008,.035),(.0075,-side*.007,0),name,'rubber')
            cylinder(name+'_pivot_cap',.009,.032,(-.045,0,0),name)
        attach('root','tool_mount',(-.015,0,0),(sqrt(.5),0,-sqrt(.5),0))
    elif variant=='arm_deck':
        box('root',(.18,.18,.012),parent=None)
        attach('root','arm_mount',(0,0,.006))
    elif variant=='arm_link':
        box('root',(.16,.008,.008),parent=None,material='anodized')
        for side in (-1,1):
            box('side_'+str(side+1),(.16,.005,.030),(0,side*.014,0))
        for side in (-1,1):
            cylinder('end_'+str(side+1),.019,.036,(side*.07,0,0),q=QY)
        attach('root','proximal',(-.07,0,0),QY)
        attach('root','distal',(.07,0,0),QY)
    elif variant=='wrist':
        box('root',(.055,.055,.012),parent=None,material='anodized')
        cylinder('output',.025,.010,(0,0,.011))
        joint('rotation_joint','output',(0,0,1),limits=(-160,160),torque=1.5)
        attach('output','tool',(0,0,.005))
    attach('root','mount',(0,0,-parts[0].geometry.size[2]/2),(0,1,0,0))
    attach('root','assembly_top',(0,0,parts[0].geometry.size[2]/2))
    scale={'arm_compact':.65,'arm_long':1.4,'gripper_compact':.7,'gripper_wide':1.3}.get(variant,1.)
    if variant=='arm':scale=item.dimensions[0]/.38
    if scale!=1:
        def pose(t):return replace(t,position=tuple(v*scale for v in t.position))
        parts=[replace(p,geometry=replace(p.geometry,size=tuple(v*scale for v in p.geometry.size)),
                       transform=pose(p.transform),attachments=tuple(replace(a,transform=pose(a.transform)) for a in p.attachments)) if isinstance(p,Body)
               else replace(p,position=tuple(v*scale for v in p.position)) if isinstance(p,Hinge)
               else replace(p,max_torque=p.max_torque*max(scale,scale**4)) if isinstance(p,Motor) else p for p in parts]
    return Blueprint(tuple(parts),PALETTE)
