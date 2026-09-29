"""Kit docking rules and initial ground placement; independent of native physics."""
from dataclasses import dataclass, replace
from math import sqrt
from little_world.core.component import Body, Transform, Hinge, Motor, Geometry, Attachment
from .connections import frames, mate, multiply, rotate, module_bounds, conjugate

FACES=('Top','Bottom','Left','Right','Front','Back')
WHEELS=('wheel','drive','hw_tread')
SIDE_MOUNTS=('Left front','Right front','Left rear','Right rear')
SHAFT_LOADS=('wheel','hw_tread','shaft_load','hw_hub','hw_coupler','hw_arm_link')


def poses(blueprint):
    bodies={b.id:b for b in blueprint.components if isinstance(b,Body)}
    result={}
    def visit(b):
        t=b.transform
        if b.parent:
            p=visit(bodies[b.parent]) if b.parent not in result else result[b.parent]
            t=Transform(tuple(a+c for a,c in zip(p.position,rotate(p.quaternion,t.position))),multiply(p.quaternion,t.quaternion))
        result[b.id]=t
        return t
    for b in bodies.values():
        if b.id not in result:visit(b)
    return result


def world_bounds(blueprint, names=None):
    transforms=poses(blueprint);lo=[float('inf')]*3;hi=[-float('inf')]*3
    for b in blueprint.components:
        if not isinstance(b,Body) or names is not None and b.id not in names:continue
        t=transforms[b.id];g=b.geometry
        basis=[rotate(t.quaternion,tuple(float(i==j) for i in range(3))) for j in range(3)]
        for axis in range(3):
            if g.shape=='sphere':extent=g.size[0]
            elif g.shape=='cylinder':extent=g.size[0]*sqrt(basis[0][axis]**2+basis[1][axis]**2)+g.size[1]/2*abs(basis[2][axis])
            else:extent=sum(abs(basis[j][axis])*g.size[j]/2 for j in range(3))
            lo[axis]=min(lo[axis],t.position[axis]-extent);hi[axis]=max(hi[axis],t.position[axis]+extent)
    return tuple(lo),tuple(hi)


def subtree(blueprint,name):
    names={name}
    while True:
        new=names|{b.id for b in blueprint.components if isinstance(b,Body) and b.parent in names}
        if new==names:return names
        names=new


def grounded(blueprint,name,mobile=True,raise_only=False):
    bodies={b.id:b for b in blueprint.components if isinstance(b,Body)}
    root=bodies[name]
    while root.parent:root=bodies[root.parent]
    low,_=world_bounds(blueprint,subtree(blueprint,root.id))
    dz=.002-low[2]
    if raise_only:dz=max(0,dz)
    root=replace(root,dynamic=mobile,transform=replace(root.transform,position=tuple(v+(dz if i==2 else 0) for i,v in enumerate(root.transform.position))))
    return replace(blueprint,components=tuple(root if c.id==root.id else c for c in blueprint.components))


def wheel_motor_sides(blueprint):
    """Find the actual powered axle upstream of each wheel, not its name."""
    from little_world.assets.catalog import BY_ID
    bodies={b.id:b for b in blueprint.components if isinstance(b,Body)}
    hinges={h.body:h for h in blueprint.components if isinstance(h,Hinge)}
    motors={m.joint:m for m in blueprint.components if isinstance(m,Motor)}
    transforms=poses(blueprint);result={}
    for wheel in bodies.values():
        item=BY_ID.get(catalog_id(wheel.id,blueprint))
        if item is None or item.variant not in WHEELS:continue
        ancestor=wheel;joint=None
        while True:
            if ancestor.id in hinges:joint=hinges[ancestor.id];break
            if ancestor.parent is None:break
            ancestor=bodies[ancestor.parent]
        if joint is None or joint.id not in motors or joint.limits is not None:continue
        base=wheel
        while base.parent:base=bodies[base.parent]
        iq=conjugate(transforms[base.id].quaternion)
        axis=rotate(iq,rotate(transforms[ancestor.id].quaternion,joint.axis))
        if axis[1]<.9:continue
        point=rotate(iq,tuple(a-b for a,b in zip(transforms[wheel.id].position,transforms[base.id].position)))
        result[motors[joint.id].id]=(base.id,0 if point[1]>0 else 1)
    return result


def drive_controls(blueprint):
    """Repair legacy drive-module pairs without replacing arm/user bindings."""
    from little_world.core.blueprint import ControllerSpec
    candidates=wheel_motor_sides(blueprint)
    controls=[]
    for c in blueprint.controllers:
        if c.kind=='differential_torque' and all(a in candidates for a in c.actuators):
            if len(c.actuators)==1 and c.drive_sides:continue
            if len(c.actuators)==2:
                first,second=(candidates[a] for a in c.actuators)
                if first[0]!=second[0] or first[1]==second[1]:continue
                if first[1]==1:c=replace(c,actuators=tuple(reversed(c.actuators)))
        controls.append(c)
    used={a for c in controls for a in c.actuators};groups={}
    for motor,(root,side) in candidates.items():
        if motor not in used:groups.setdefault(root,([],[]))[side].append(motor)
    ids={c.id for c in (*blueprint.components,*controls)}
    for root,(left,right) in groups.items():
        pairs=[((a,b),()) for a,b in zip(left,right)]
        if {side for base,side in candidates.values() if base==root}=={0,1}:
            count=min(len(left),len(right))
            pairs.extend(((a,),(side,)) for side,remaining in enumerate((left[count:],right[count:])) for a in remaining)
        for actuators,sides in pairs:
            i=1
            while 'drive_'+str(i) in ids:i+=1
            name='drive_'+str(i);ids.add(name)
            template=next((c.drive_settings for c in controls if c.kind=='differential_torque'),None)
            kwargs={'drive_settings':template} if template is not None else {}
            controls.append(ControllerSpec(name,'differential_torque',actuators,drive_sides=sides,**kwargs))
    return replace(blueprint,controllers=tuple(controls))


def prepare_base(editor,name,mobile):
    editor._commit(drive_controls(grounded(editor.blueprint,name,mobile)),editor.selection)


def catalog_id(name,blueprint=None):
    from little_world.assets.catalog import BY_ID
    if blueprint is not None:
        body=next((b for b in blueprint.components if isinstance(b,Body) and b.id==name),None)
        if body and body.catalog_part in BY_ID:return body.catalog_part
    if name.startswith(('left_wheel_','right_wheel_')):return 'drive_left' if name.startswith('left') else 'drive_right'
    return next((k for k in sorted(BY_ID,key=len,reverse=True) if name.startswith(k+'_') and name.endswith('_root')),None)


def mounting_body(parent):
    """Use the full open frame's envelope, not its one narrow root rail."""
    from little_world.assets.catalog import BY_ID
    item=BY_ID.get(parent.catalog_part)
    if item is None or item.variant!='hw_chassis':return parent
    module=item.blueprint()
    module=replace(module,components=tuple(replace(c,transform=Transform()) if isinstance(c,Body) and c.parent is None else c for c in module.components))
    lo,hi=module_bounds(module);centre=tuple((a+b)/2 for a,b in zip(lo,hi))
    proxy=replace(parent,geometry=Geometry('box',tuple(b-a for a,b in zip(lo,hi))),attachments=())
    mounts=tuple(Attachment(n,replace(t,position=tuple(a+b for a,b in zip(t.position,centre)))) for n,t in frames(proxy).items())
    return replace(proxy,attachments=tuple(a for a in parent.attachments if a.id not in FACES)+mounts)


def placement(item,parent,face,module=None):
    parent=mounting_body(parent)
    module=module or item.blueprint()
    root=next(c for c in module.components if isinstance(c,Body) and c.parent is None)
    if face in ('tool','arm_mount','output'):
        source='mount' if item.variant=='real_robot' else 'tool_mount' if face=='tool' else 'shaft_mount' if 'shaft_mount' in frames(root) else 'proximal' if item.variant=='hw_arm_link' else 'Bottom'
        return mate(frames(root)[source],frames(parent)[face],.002)
    base_face=face.split(' ')[0]
    q=root.transform.quaternion
    if item.variant in WHEELS:
        # Local +Z is the decorative outside; right wheels must face outward.
        q=(sqrt(.5),sqrt(.5) if base_face=='Right' else -sqrt(.5),0,0)
        module=replace(module,components=tuple(replace(c,transform=replace(c.transform,quaternion=q)) if c.id==root.id else c for c in module.components))
    if item.variant in ('hw_gearmotor','hw_motor') and base_face in ('Left','Right'):
        yaw=(sqrt(.5),0,0,sqrt(.5) if base_face=='Left' else -sqrt(.5))
        q=multiply(yaw,q)
        module=replace(module,components=tuple(replace(c,transform=replace(c.transform,quaternion=q)) if c.id==root.id else c for c in module.components))
    if item.variant=='real_robot':
        return mate(frames(root)['mount'],frames(parent)[face],.002)
    lower,upper=module_bounds(module)
    axis,sign={'Top':(2,1),'Bottom':(2,-1),'Left':(1,1),'Right':(1,-1),'Front':(0,1),'Back':(0,-1)}[base_face]
    point=frames(parent)[base_face].position
    pos=[0.,0.,0.];pos[axis]=point[axis]+sign*.002-(lower[axis] if sign>0 else upper[axis])
    if item.variant in WHEELS and axis==1:
        pos[2]=-.035
        if face in SIDE_MOUNTS:pos[0]=parent.geometry.size[0]*.32*(1 if face.endswith('front') else -1)
    return Transform(tuple(pos),q)


@dataclass(frozen=True)
class Socket:
    body: str
    face: str
    point: tuple
    transform: Transform
    valid: bool
    reason: str


def sockets(blueprint,item_id,target,moving=None):
    from little_world.assets.catalog import BY_ID
    item=BY_ID[item_id];bodies={b.id:b for b in blueprint.components if isinstance(b,Body)}
    parent=bodies[target]
    if item.variant in SHAFT_LOADS and not any(a.id=='output' for a in parent.attachments):
        # Find the moving shaft inside the selected motor, stopping at separately
        # added catalog modules. The user need not select a tiny internal shaft.
        candidates=[];pending=[target]
        while pending:
            name=pending.pop()
            for b in bodies.values():
                if b.parent==name and b.catalog_part is None:
                    if any(a.id=='output' for a in b.attachments):candidates.append(b)
                    pending.append(b.id)
        if len(candidates)==1:parent=candidates[0];target=parent.id
    parent=mounting_body(parent)
    named={a.id for a in parent.attachments};result={}
    descendants=subtree(blueprint,moving) if moving else set()
    # Cache one module construction across all faces in this query.
    module=item.blueprint()
    extra=SIDE_MOUNTS if item.variant in WHEELS and parent.geometry.shape=='box' and min(parent.geometry.size[:2])>=.05 else ()
    for face in (*FACES,*extra,*(n for n in ('tool','arm_mount','output') if n in named)):
        reason='Compatible mount'
        if item.variant in ('ready_base','lab_mobile','lab_table','lab_pedestal','lab_rollers','lab_mobile_cell','lab_fixed_cell','lab_delivery','lab_rack','lab_ramp','lab_inspection','lab_ur_cell','lab_gen3_cell'):reason='Place this complete assembly on the floor'
        elif parent.robot_asset:reason='This is a complete robot model; mount accessories on its supporting deck'
        elif target in descendants:reason='Cannot attach to self or a descendant'
        elif item.variant in WHEELS:
            if face not in ('Left','Right','output',*SIDE_MOUNTS):reason='Wheels need a side mount or an output shaft'
            elif face=='output' and item.variant=='drive':reason='Powered wheel module needs a chassis side'
            elif face!='output' and (parent.geometry.shape!='box' or min(parent.geometry.size[:2])<.05):reason='Use a chassis side or a driven output shaft'
        elif item.variant in ('shaft_load','hw_hub','hw_coupler') and face!='output':reason='Attach this component to a motor output shaft'
        elif 'gripper' in item.variant and face!='tool':reason='Gripper requires an arm tool socket'
        elif item.variant in ('hw_arm','hw_arm_compact','hw_arm_long','ready_arm','real_robot') and (face not in ('Top','arm_mount') or parent.geometry.shape!='box' or min(parent.geometry.size[:2])<.08):reason='Arm requires a top deck or arm mount'
        elif item.variant=='hw_caster' and face!='Bottom':reason='Caster requires a bottom mount'
        elif face in ('tool','output') and not (face=='tool' and 'gripper' in item.variant or face=='output' and item.variant in SHAFT_LOADS):reason='This socket requires a matching tool or wheel'
        elif face=='arm_mount' and item.variant not in ('hw_arm','hw_arm_compact','hw_arm_long','ready_arm','real_robot'):reason='Arm mount requires an arm module'
        elif parent.geometry.shape!='box' and face in FACES:reason='Use a structural face or a named socket'
        elif parent.geometry.shape=='box' and max(parent.geometry.size)<.02:reason='This detail is too small for a module mount'
        transform=placement(item,parent,face,module) if not (face=='tool' and 'gripper' not in item.variant) else Transform()
        if reason=='Compatible mount':
            for child in bodies.values():
                if child.parent!=target or child.id==moving:continue
                child_item=catalog_id(child.id,blueprint)
                if not child_item:continue
                overlaps=False
                if item.variant in WHEELS and BY_ID[child_item].variant in WHEELS and face in ('Left','Right',*SIDE_MOUNTS):
                    side=1 if face.startswith('Left') else -1
                    spacing=abs(child.transform.position[0]-transform.position[0])
                    overlaps=child.transform.position[1]*side>0 and spacing<(item.dimensions[0]+BY_ID[child_item].dimensions[0])/2+.005
                if overlaps or face in ('tool','output','arm_mount') or sum((a-b)**2 for a,b in zip(child.transform.position,placement(BY_ID[child_item],parent,face).position))<.0004:
                    reason='Mount occupied by '+child.id;break
        point=frames(parent)[face.split(' ')[0]].position
        if face in SIDE_MOUNTS:point=(transform.position[0],point[1],point[2])
        result[face]=Socket(target,face,point,transform,reason=='Compatible mount',reason)
    return result


def dock(editor,item_id,target,face,moving=None):
    """Validate and insert/reparent once; invalid drops leave history untouched."""
    from .editor import AssemblyEditor
    from little_world.assets.catalog import BY_ID
    choice=sockets(editor.blueprint,item_id,target,moving)[face]
    if not choice.valid:raise ValueError(choice.reason)
    target=choice.body
    trial=AssemblyEditor(editor.blueprint)
    if moving:
        trial.select(moving)
        trial._replace(replace(trial.selected,parent=target,dynamic=False,transform=choice.transform))
    else:
        trial.select(target)
        trial.add_catalog(item_id,face.split(' ')[0] if face in (*FACES,*SIDE_MOUNTS) else 'Top')
        trial._replace(replace(trial.selected,transform=choice.transform))
    if face=='output':
        trial.make_fixed()
        if BY_ID[item_id].variant in WHEELS:
            # The shaft is already the powered joint. Orient its positive axis
            # consistently when the motor is mounted on the opposite side.
            bodies={b.id:b for b in trial.bodies};ancestor=bodies[target]
            hinges={h.body:h for h in trial.blueprint.components if isinstance(h,Hinge)}
            while ancestor.id not in hinges and ancestor.parent:ancestor=bodies[ancestor.parent]
            joint=hinges.get(ancestor.id)
            if joint and joint.limits is None:
                transforms=poses(trial.blueprint);base=ancestor
                while base.parent:base=bodies[base.parent]
                axis=rotate(conjugate(transforms[base.id].quaternion),rotate(transforms[ancestor.id].quaternion,joint.axis))
                if axis[1]<-.9:
                    trial.blueprint=replace(trial.blueprint,components=tuple(replace(c,axis=tuple(-v for v in c.axis)) if c.id==joint.id else c for c in trial.blueprint.components))
    elif BY_ID[item_id].variant in WHEELS and trial.selected_hinge() is None:
        trial.configure_hinge(axis=(0,0,1))
    if BY_ID[item_id].variant in WHEELS and face!='output':
        hinge=trial.selected_hinge()
        if hinge is not None:
            trial.blueprint=replace(trial.blueprint,components=tuple(replace(c,axis=(0,0,-1 if face.startswith('Right') else 1)) if c.id==hinge.id else c for c in trial.blueprint.components))
    if BY_ID[item_id].variant in WHEELS:
        trial.blueprint=grounded(trial.blueprint,target,True,raise_only=True)
    editor._commit(drive_controls(trial.blueprint),trial.selection)


def wheel_at(editor,item_id,target,side,x,moving=None,clearance=.005):
    """Continuous longitudinal mounting; presets are only suggested positions."""
    from math import isfinite
    from .editor import AssemblyEditor
    from little_world.assets.catalog import BY_ID
    item=BY_ID[item_id]
    if item.variant not in WHEELS or side not in ('Left','Right'):raise ValueError('Choose a wheel and Left or Right side')
    if not isfinite(clearance) or not 0<=clearance<=.05:raise ValueError('Clearance must be between 0 and 0.05 m')
    bodies={b.id:b for b in editor.bodies};parent=mounting_body(bodies[target])
    if parent.geometry.shape!='box' or min(parent.geometry.size[:2])<.05:raise ValueError('Choose a chassis or structural deck')
    lo,hi=frames(parent)['Back'].position[0],frames(parent)['Front'].position[0]
    if not isfinite(x) or not lo<=x<=hi:raise ValueError(f'Wheel center must be between {lo:g} and {hi:g} m along this frame')
    if moving and target in subtree(editor.blueprint,moving):raise ValueError('Cannot attach a wheel to its own descendant')
    sign=1 if side=='Left' else -1
    for child in editor.bodies:
        other=catalog_id(child.id,editor.blueprint)
        if child.parent==target and child.id!=moving and other and BY_ID[other].variant in WHEELS and child.transform.position[1]*sign>0:
            if abs(child.transform.position[0]-x)<(item.dimensions[0]+BY_ID[other].dimensions[0])/2+clearance:
                raise ValueError('Wheels overlap: move the center farther away, use smaller wheels, or lengthen the chassis')
    pose=placement(item,parent,side);pose=replace(pose,position=(x,pose.position[1],pose.position[2]))
    trial=AssemblyEditor(editor.blueprint)
    if moving:trial.select(moving)
    else:trial.select(target);trial.add_catalog(item_id,side)
    trial._replace(replace(trial.selected,parent=target,dynamic=False,transform=pose))
    hinge=trial.selected_hinge()
    if hinge:
        trial.blueprint=replace(trial.blueprint,components=tuple(replace(c,axis=(0,0,sign)) if c.id==hinge.id else c for c in trial.blueprint.components))
    trial.blueprint=drive_controls(grounded(trial.blueprint,target,True,raise_only=True))
    editor._commit(trial.blueprint,trial.selection)
