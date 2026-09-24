"""Atomic, connection-aware module changes without native simulator dependencies."""
from dataclasses import replace
from little_world.assets.catalog import BY_ID,CATALOG
from little_world.core.component import Body,Hinge,Motor,Camera
from .docking import catalog_id,subtree,grounded,placement,SIDE_MOUNTS,WHEELS,sockets
from .connections import frames,mate,rotate


def family(item):
    v=item.variant
    if v=='drive':return 'powered wheels'
    if v in ('wheel','hw_tread'):return 'passive wheels'
    if v in ('hw_arm','hw_arm_compact','hw_arm_long'):return 'arms'
    if 'gripper' in v:return 'grippers'
    if v in ('plate','hw_chassis','cross'):return 'chassis'
    if v in ('beam','hw_extrusion'):return 'beams'
    return v


def module_info(editor):
    root=editor._part();item_id=catalog_id(root.id,editor.blueprint)
    if item_id:
        prototype=BY_ID[item_id].blueprint()
        prefix=root.id[:-4] if root.id.endswith('_root') else '' if root.id=='root' else root.id+'_'
        names={c.id:(root.id if c.id=='root' else prefix+c.id) for c in prototype.components}
        owned={n for n in names.values() if any(c.id==n for c in editor.blueprint.components)}
    else:
        prototype=None;names={'root':root.id};owned={root.id}
    # Root mounting hinge/motor is inserted by the editor, outside the prototype.
    for c in editor.blueprint.components:
        if isinstance(c,Hinge) and c.body in owned:owned.add(c.id)
        if isinstance(c,Motor) and c.joint in owned:owned.add(c.id)
    attached=[b.id for b in editor.bodies if b.id not in owned and b.parent in owned]
    return root,item_id,names,owned,attached


def deletion_impact(editor):
    root,item_id,names,owned,attached=module_info(editor)
    all_ids=editor.subtree_ids()
    controls=[c.id for c in editor.blueprint.controllers if set(c.actuators)&all_ids]
    return dict(name=BY_ID[item_id].title if item_id else root.id,attachments=attached,
                bodies=sum(b.id in all_ids for b in editor.bodies),controls=controls,ids=all_ids)


def delete_component(editor,include_attached=False):
    impact=deletion_impact(editor)
    if impact['attachments'] and not include_attached:
        raise ValueError('Other components are attached. Remove them first or delete the reviewed branch.')
    editor.delete()


def replacement_options(editor):
    root,item_id,names,owned,attached=module_info(editor)
    group=family(BY_ID[item_id]) if item_id else 'chassis' if root.geometry.shape=='box' else None
    return tuple(p for p in CATALOG if family(p)==group and p.id!=item_id)


def replace_component(editor,item_id):
    if item_id not in {p.id for p in replacement_options(editor)}:
        raise ValueError('Choose a compatible component from the same family')
    root,old_id,names,owned,attached=module_info(editor)
    item=BY_ID[item_id];module=item.blueprint()
    old_parts={c.id:c for c in editor.blueprint.components}
    prefix=root.id[:-4] if root.id.endswith('_root') else '' if root.id=='root' else root.id+'_'
    new_names={c.id:root.id if c.id=='root' else prefix+c.id for c in module.components}
    if any(name in old_parts and name not in owned for name in new_names.values()):
        raise ValueError('Replacement IDs conflict with attached parts')
    fresh={}
    for c in module.components:
        if isinstance(c,Body):
            c=replace(c,id=new_names[c.id],parent=root.parent if c.parent is None else new_names[c.parent],
                dynamic=root.dynamic if c.parent is None else False,
                transform=root.transform if c.parent is None else c.transform)
        elif isinstance(c,(Hinge,Camera)):c=replace(c,id=new_names[c.id],body=new_names[c.body])
        elif isinstance(c,Motor):c=replace(c,id=new_names[c.id],joint=new_names[c.joint])
        fresh[c.id]=c
    # Resize at the existing mating face, rather than pushing a wider wheel
    # into its chassis. Preserve the user's small placement offsets.
    wheel_face=None
    if root.parent and old_id:
        parent=old_parts[root.parent]
        candidates=[]
        for face in (*frames(parent),*(SIDE_MOUNTS if item.variant in WHEELS else ())):
            if face not in ('Top','Bottom','Left','Right','Front','Back','tool','output','arm_mount',*SIDE_MOUNTS):continue
            if face=='tool' and 'gripper' not in BY_ID[old_id].variant:continue
            old_pose=placement(BY_ID[old_id],parent,face)
            distance=sum((a-b)**2 for a,b in zip(old_pose.position,root.transform.position))
            candidates.append((distance,face,old_pose))
        if candidates:
            distance,face,old_pose=min(candidates,key=lambda c:c[0])
            if distance<.0004:
                new_pose=placement(item,parent,face,module)
                position=tuple(p+n-o for p,n,o in zip(root.transform.position,new_pose.position,old_pose.position))
                q=root.transform.quaternion
                if item.variant in WHEELS and face in ('Left','Right',*SIDE_MOUNTS):
                    choice=sockets(editor.blueprint,item_id,root.parent,root.id).get(face)
                    if choice is not None and not choice.valid:raise ValueError(choice.reason)
                    wheel_face=face;q=new_pose.quaternion
                fresh[root.id]=replace(fresh[root.id],transform=replace(root.transform,position=position,quaternion=q))
    # Preserve the external wheel axle and motor, including its tuned motor profile.
    intrinsic=set(names.values())
    for name in sorted(owned-intrinsic,key=lambda n:0 if isinstance(old_parts[n],Hinge) else 1):
        c=old_parts[name]
        if isinstance(c,Hinge) and c.body in fresh:
            fresh[name]=replace(c,axis=(0,0,-1 if wheel_face.startswith('Right') else 1)) if wheel_face and c.body==root.id else c
        elif isinstance(c,Motor) and c.joint in fresh:fresh[name]=c
    referenced={a for control in editor.blueprint.controllers for a in control.actuators}
    if referenced & (owned-set(fresh)):
        raise ValueError('Replacement would remove a controlled joint; remove its binding first')
    parts=[]
    for c in editor.blueprint.components:
        if c.id in owned:continue
        if isinstance(c,Body) and c.parent in owned:
            old_parent=old_parts[c.parent];new_parent=fresh.get(c.parent)
            if not isinstance(new_parent,Body):raise ValueError('Replacement has no matching mount for '+c.id)
            old_frames=frames(old_parent);new_frames=frames(new_parent);child_frames=frames(c)
            named=next((n for n in ('tool','output','arm_mount') if n in old_frames),None)
            if named:
                if named not in new_frames:raise ValueError('Replacement lacks the '+named+' socket')
                source='tool_mount' if named=='tool' and 'tool_mount' in child_frames else 'Bottom'
                expected=mate(child_frames[source],old_frames[named])
                if sum((a-b)**2 for a,b in zip(expected.position,c.transform.position))<.0001:
                    # Keep the original intentional mounting offset/gap.
                    pose=mate(child_frames[source],new_frames[named])
                    delta=tuple(a-b for a,b in zip(c.transform.position,expected.position))
                    c=replace(c,transform=replace(pose,position=tuple(a+b for a,b in zip(pose.position,delta))))
                else:raise ValueError('Custom attachment on '+c.id+' needs manual remounting')
            else:
                half=[abs(old_frames[n].position[i]) for i,n in enumerate(('Front','Left','Top'))]
                axis=max(range(3),key=lambda i:abs(c.transform.position[i])/max(.001,half[i]))
                face=(('Back','Front'),('Right','Left'),('Bottom','Top'))[axis][c.transform.position[axis]>=0]
                delta=tuple(a-b for a,b in zip(new_frames[face].position,old_frames[face].position))
                c=replace(c,transform=replace(c.transform,position=tuple(a+b for a,b in zip(c.transform.position,delta))))
        parts.append(c)
    materials={m.id:m for m in editor.blueprint.materials}
    materials.update({m.id:m for m in module.materials if m.id not in materials})
    bp=replace(editor.blueprint,components=(*parts,*fresh.values()),materials=tuple(materials.values()))
    bodies={b.id:b for b in bp.components if isinstance(b,Body)};base=bodies[root.id]
    while base.parent:base=bodies[base.parent]
    bp=grounded(bp,root.id,base.dynamic,raise_only=True)
    editor._commit(bp,root.id)
