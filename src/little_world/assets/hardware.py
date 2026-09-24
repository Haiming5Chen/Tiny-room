"""Original engineering-style hardware, composed of editable rigid primitives.

These are approximate mechanical modules, not vendor CAD or electrical models.
"""
from dataclasses import replace
from math import pi, sin, cos, sqrt, tan
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body, Geometry, Transform, Attachment, Hinge, Motor
from little_world.materials import METAL, RUBBER, PLASTIC

DARK=replace(METAL,id='anodized',rgba=(.12,.15,.18,1),roughness=.42)
STEEL=replace(METAL,id='steel',density=7800,rgba=(.58,.62,.66,1),roughness=.22)
COPPER=replace(METAL,id='copper',density=8900,rgba=(.72,.37,.16,1),roughness=.35)
PALETTE=(METAL,RUBBER,PLASTIC,DARK,STEEL,COPPER)
QX=(sqrt(.5),0,sqrt(.5),0)  # cylinder Z -> X
QY=(sqrt(.5),-sqrt(.5),0,0)


def entries(Part):
    rows=(
        ('arm_mount_deck','Arm mounting deck','Structure','180 mm deck with a shared arm mounting frame.','Arm family mount',(.18,.18,.012),'arm_deck'),
        ('gripper_compact','Compact contact gripper','Actuators','70 percent size jaws with a tool frame for the compact arm.','Compact tool',(.0805,.07,.0245),'gripper_compact'),
        ('gripper_wide','Wide contact gripper','Actuators','130 percent size jaws with a tool frame for the long arm.','Wide tool',(.1495,.13,.0455),'gripper_wide'),
        ('robot_arm_compact','Compact arm / 240 mm','Actuators','Four powered joints, compact reach and tool frame.','Compact arm',(.247,.065,.0715),'arm_compact'),
        ('robot_arm_long','Long arm / 525 mm','Actuators','Four powered joints with larger links and higher torque limits.','Long reach arm',(.532,.14,.154),'arm_long'),
        ('robot_arm','4-axis robot arm','Actuators','Yaw, shoulder, elbow and wrist motors with a tool attachment.','Articulated arm',(.38,.10,.11),'arm'),
        ('two_finger_gripper','Two-finger gripper','Actuators','Two powered rotary jaws with rubber contact pads.','Contact gripper',(.115,.10,.035),'gripper'),
        ('arm_link_160','160 mm arm link','Structure','Side plates with proximal and distal hinge attachment frames.','Arm linkage',(.16,.04,.04),'arm_link'),
        ('wrist_turntable','Powered wrist turntable','Actuators','Limited rotary output with a tool mounting frame.','Wrist motor',(.055,.055,.026),'wrist'),
        ('gearmotor_37','37 mm gearmotor','Actuators','Metal gearbox, motor can, mounting flange and powered output shaft.','Torque motor',(.09,.037,.037),'gearmotor'),
        ('servo_module','Servo & horn','Actuators','Mounting ears, output horn and limited rotary joint. Ideal torque control.','Limited motor',(.055,.022,.049),'servo'),
        ('motor_42','42 mm motor','Actuators','Square motor stack, end plates and a powered shaft. No step electronics.','Torque motor',(.064,.042,.042),'motor'),
        ('extrusion_200','20 mm extrusion / 200','Structure','Four open T-slots, corner webs and a central spine.','Slotted profile',(.20,.02,.02),'extrusion'),
        ('extrusion_400','20 mm extrusion / 400','Structure','Long rail with exposed T-slot cross section.','Slotted profile',(.40,.02,.02),'extrusion'),
        ('open_chassis','Open robot chassis','Structure','Perimeter rails, cross members and four deck standoffs.','Chassis frame',(.30,.22,.035),'chassis'),
        ('motor_clamp','Motor mounting clamp','Hardware','Split circular clamp on a bolted mounting foot.','Motor mount',(.03,.058,.049),'clamp'),
        ('bearing_block','Pillow bearing block','Hardware','Raised bearing seat with a free inner race and open bore.','Passive bearing',(.026,.060,.042),'bearing'),
        ('flange_hub','Flanged shaft hub','Hardware','Open shaft bore, radial flange and four screw heads.','Shaft attachment',(.024,.044,.044),'hub'),
        ('shaft_coupler','Flexible-style coupler','Hardware','Segmented shaft coupling with end collars. Rigid approximation.','Rigid coupling',(.034,.025,.025),'coupler'),
        ('tread_wheel','100 mm tread wheel','Motion','Rubber tyre with raised tread, open spoke rim and bolted hub.','Passive wheel',(.10,.030,.10),'tread','Left'),
        ('swivel_caster','Swivel caster / 40','Motion','Mount plate, swivel bearing, fork and independently rolling wheel.','Two passive joints',(.06,.046,.075),'caster','Bottom'),
        ('mount_standoff','Hex-style standoff','Hardware','Six-sided spacer with threaded-hole approximation and end sockets.','Spacer',(.014,.014,.030),'standoff'),
        ('bolt_m4','Socket screw / M4','Hardware','4 mm shaft with socket-head recess. No thread contact model.','Fastener',(.007,.007,.020),'bolt'),
    )
    return tuple(Part(id,title,category,description,capability,dims,'hw_'+variant,*mount)
                 for id,title,category,description,capability,dims,variant,*mount in rows)


def make_hardware(item):
    if item.variant in ('hw_arm_deck','hw_gripper_compact','hw_gripper_wide','hw_arm','hw_arm_compact','hw_arm_long','hw_gripper','hw_arm_link','hw_wrist'):
        from .manipulation import make_manipulation
        return make_manipulation(item)
    parts=[]
    x,y,z=item.dimensions
    variant=item.variant[3:]

    def body(name,shape,size,pos=(0,0,0),material='metal',parent='root',q=(1,0,0,0),attachments=()):
        parts.append(Body(name,Geometry(shape,size),material,Transform(pos,q),parent,
                          dynamic=parent is None,attachments=tuple(attachments)))
    def box(name,size,pos=(0,0,0),material='metal',parent='root',q=(1,0,0,0)):
        body(name,'box',size,pos,material,parent,q)
    def cyl(name,r,length,pos=(0,0,0),material='metal',parent='root',q=(1,0,0,0)):
        body(name,'cylinder',(r,length),pos,material,parent,q)
    def sockets(name,values):
        for i,p in enumerate(parts):
            if p.id==name:
                parts[i]=replace(p,attachments=tuple(Attachment(k,Transform(pos,q)) for k,pos,q in values))
                return
    def ring(prefix,outer,inner,length,pos=(0,0,0),material='metal',parent='root',q=(1,0,0,0),n=16):
        # Ring segments leave a real bore rather than painting a hole onto a disc.
        from little_world.construction.connections import rotate,multiply
        radius=(outer+inner)/2
        for i in range(n):
            a=2*pi*i/n
            local=(radius*cos(a),radius*sin(a),0)
            offset=rotate(q,local)
            box(f'{prefix}_{i}',(outer-inner,2*outer*tan(pi/n)*1.001,length),
                tuple(v+w for v,w in zip(pos,offset)),material,parent,
                multiply(q,(cos(a/2),0,0,sin(a/2))))
    def screw(name,pos,parent='root',q=(1,0,0,0)):
        cyl(name,.0027,.003,pos,'steel',parent,q)
    def shaft_motor(name,pos,radius,length,q=QX,limit=None,torque=.5):
        cyl(name,radius,length,pos,'steel',q=q)
        parts.extend((Hinge(name+'_joint',name,limits=limit),Motor(name+'_motor',name+'_joint',torque)))
        sockets(name,(('output',(0,0,length/2),(1,0,0,0)),('axis',(0,0,0),(1,0,0,0))))

    if variant=='gearmotor':
        cyl('root',.0175,.032,(-.012,0,0),'metal',None,QX)
        cyl('rear_cap',.0177,.006,(-.031,0,0),'anodized',q=QX)
        cyl('gearbox',.0185,.023,(.0155,0,0),'metal',q=QX)
        cyl('flange',.019,.003,(.0285,0,0),'steel',q=QX)
        shaft_motor('output_shaft',(.0385,0,0),.003,.018)
        for i in range(6):
            a=i*pi/3
            screw('face_screw_'+str(i),(.031,.014*cos(a),.014*sin(a)),q=QX)
        for side in (-1,1):
            box('terminal_'+str(side).replace('-','n'),(.007,.002,.004),(-.037,side*.009,0),'copper')
        # Root geometry is already rotated: all fixed child positions below are
        # authored in the assembly frame, so unwrap root rotation at the end.
    elif variant=='motor':
        box('root',(.035,.042,.042),(-.003,0,0),'anodized',None)
        for side in (-1,1):
            box('endplate_'+str(side).replace('-','n'),(.005,.042,.042),(side*.020,0,0))
        cyl('boss',.011,.003,(.024,0,0),q=QX)
        shaft_motor('output_shaft',(.035,0,0),.0025,.018,torque=.4)
        for i in (-1,1):
            for j in (-1,1):
                screw(f'face_{i+1}_{j+1}',(.024,i*.0155,j*.0155),q=QX)
        box('connector',(.009,.018,.009),(-.023,0,.009),'plastic')
    elif variant=='servo':
        box('root',(.040,.020,.033),(0,0,0),'anodized',None)
        box('lid',(.040,.020,.005),(0,0,.019))
        for side in (-1,1):
            box('ear_'+str(side).replace('-','n'),(.009,.020,.003),(side*.024,0,.007))
            for yy in (-.006,.006):
                screw(f'ear_bolt_{side+1}_{int(yy*1000)+6}',(side*.024,yy,.010))
        cyl('horn',.007,.006,(.010,0,.025),'steel')
        box('horn_bar',(.034,.006,.003),(.008,0,.004),'metal','horn')
        for xx in (-.005,.014,.023):
            screw('horn_screw_'+str(int(xx*1000)+5),(xx,0,.006),'horn')
        parts.extend((Hinge('horn_joint','horn',limits=(-90,90)),Motor('horn_motor','horn_joint',.8)))
        sockets('horn',(('output',(0,0,.005),(1,0,0,0)),))
    elif variant=='extrusion':
        box('root',(x,.006,.006),material='anodized',parent=None)
        for a in (-1,1):
            for b in (-1,1):
                stem=f'corner_{a+1}_{b+1}'
                box(stem+'_outer',(x,.006,.002),(0,a*.007,b*.009))
                box(stem+'_side',(x,.002,.006),(0,a*.009,b*.005))
                box(stem+'_web',(x,.003,.003),(0,a*.0045,b*.0045))
    elif variant=='chassis':
        box('root',(x,.015,.005),(0,-y/2+.0075,0),'anodized',None)
        box('rail_right',(x,.015,.005),(0,y-.015,0),'anodized')
        for i,xx in enumerate((-x/2+.0075,0,x/2-.0075)):
            box('cross_'+str(i),(.015,y-.030,.005),(xx,(y-.015)/2,0))
        for i,xx in enumerate((-.12,.12)):
            for j,yy in enumerate((.010,y-.025)):
                cyl(f'standoff_{i}_{j}',.005,.028,(xx,yy,.0165),'steel')
                screw(f'deck_bolt_{i}_{j}',(xx,yy,.032))
    elif variant in ('clamp','bearing'):
        box('root',(.026,.060,.005),(0,0,0),'anodized',None)
        inner=.019 if variant=='clamp' else .011
        outer=.024 if variant=='clamp' else .018
        ring('seat',outer,inner,.018,(0,0,.024),q=QX)
        if variant=='bearing':
            # Small top segment is the root of the freely rotating inner race.
            box('race',(.020,.004,.003),(0,0,.024+.008),'steel')
            ring('race_ring',.010,.006,.020,(0,0,-.008),'steel','race',QX)
            parts.append(Hinge('bearing_joint','race',axis=(1,0,0),position=(0,0,-.008)))
            sockets('race',(('shaft',(0,0,-.008),QX),))
        for i,yy in enumerate((-.024,.024)):
            screw('foot_bolt_'+str(i),(0,yy,.004))
    elif variant in ('hub','coupler'):
        length=x
        outer=y/2
        height=outer if variant=='coupler' else .010
        # Root is one segment of the central sleeve; remaining segments weld to it.
        box('root',(length,.003,.004),(0,0,height-.002),'steel',None)
        ring('sleeve',outer if variant=='coupler' else .010,.0035,length,(0,0,-height+.002),q=QX)
        if variant=='hub':
            ring('flange',outer,.006,.004,(-length/2+.002,0,-height+.002),q=QX)
            for i in range(4):
                a=i*pi/2
                screw('flange_bolt_'+str(i),(-length/2-.001,.016*cos(a),.016*sin(a)-height+.002),q=QX)
        else:
            for i in (-1,1):
                ring('collar_'+str(i).replace('-','n'),outer+.001,.0035,.006,(i*.013,0,-height+.002),'anodized',q=QX)
    elif variant=='tread':
        cyl('root',.012,.027,material='steel',parent=None,q=QY)
        ring('tyre',.043,.033,.027,material='rubber',n=24)
        # Root local Z is wheel axle, so this branch is authored in wheel coordinates.
        for i in range(24):
            a=2*pi*i/24
            box('tread_'+str(i),(.011,.008,.030),(.046*cos(a),.046*sin(a),0),'rubber',q=(cos(a/2),0,0,sin(a/2)))
        for side in (-1,1):
            ring('rim_'+str(side).replace('-','n'),.034,.027,.003,(0,0,side*.015),'metal')
            for i in range(6):
                a=i*pi/3
                box(f'spoke_{side+1}_{i}',(.028,.005,.003),(.016*cos(a),.016*sin(a),side*.015),'anodized',q=(cos(a/2),0,0,sin(a/2)))
                screw(f'hub_bolt_{side+1}_{i}',(.009*cos(a),.009*sin(a),side*.018))
        cyl('hub',.012,.036,material='steel')
    elif variant=='caster':
        box('root',(.048,.040,.003),material='metal',parent=None)
        cyl('swivel',.013,.008,(0,0,-.006),'steel')
        parts.append(Hinge('swivel_joint','swivel'))
        for i,yy in enumerate((-.015,.015)):
            box('fork_'+str(i),(.012,.004,.028),(.009,yy,-.016),'metal','swivel')
        cyl('wheel',.020,.022,(.015,0,-.034),'rubber','swivel',QY)
        cyl('axle',.003,.039,(0,0,0),'steel','wheel')
        parts.append(Hinge('wheel_joint','wheel'))
        for i in (-1,1):
            for j in (-1,1):
                screw(f'mount_bolt_{i+1}_{j+1}',(i*.018,j*.014,.003))
    elif variant=='standoff':
        box('root',(.003,.004,z),(0,.005,0),'steel',None)
        ring('hex',.007,.0022,z,(0,-.005,0),n=6)
    elif variant=='bolt':
        cyl('root',.002,.016,(0,0,0),'steel',None)
        ring('head',.0035,.0015,.004,(0,0,.010),'steel',n=12)

    if variant=='gearmotor':
        # Authoring used world-like X for all positions. Keep cylinder geometry
        # rotated but transform child coordinates into its actual local frame.
        from little_world.construction.connections import conjugate,rotate,multiply
        root=parts[0]
        iq=conjugate(root.transform.quaternion)
        for i,p in enumerate(parts):
            if isinstance(p,Body) and p.parent=='root':
                parts[i]=replace(p,transform=Transform(rotate(iq,tuple(a-b for a,b in zip(p.transform.position,root.transform.position))),multiply(iq,p.transform.quaternion)))
    root=next(p for p in parts if isinstance(p,Body) and p.parent is None)
    # Frame names apply to the actual body-local geometry, with additional
    # functional output frames on independently moving bodies above.
    from little_world.construction.connections import module_bounds
    local_parts=tuple(replace(p,transform=Transform()) if p.id==root.id else p for p in parts)
    lower,upper=module_bounds(Blueprint(local_parts,PALETTE))
    centre=tuple((a+b)/2 for a,b in zip(lower,upper))
    sockets(root.id,(('mount',(centre[0],centre[1],lower[2]),(0,1,0,0)),
                     ('assembly_top',(centre[0],centre[1],upper[2]),(1,0,0,0))))
    if variant in ('hub','coupler'):
        # Through-shaft fittings carry rotation onward to the next rigid load.
        i=next(i for i,p in enumerate(parts) if p.id=='root')
        offset=-height+.002
        parts[i]=replace(parts[i],attachments=(*parts[i].attachments,
            Attachment('shaft_mount',Transform((-x/2,0,offset),(sqrt(.5),0,-sqrt(.5),0))),
            Attachment('output',Transform((x/2,0,offset),QX))))

    return Blueprint(tuple(parts),PALETTE)
