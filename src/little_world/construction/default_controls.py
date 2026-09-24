"""Editable semantic defaults for articulated kit modules, independent of UI."""
from dataclasses import replace
from little_world.core.blueprint import ControllerSpec,BINDABLE_KEYS
from little_world.core.component import Body,Hinge,Motor,RobotServo


def default_controls(bp,module_roots=None):
    from little_world.assets.catalog import BY_ID
    controls=list(bp.controllers);bound={a for c in controls for a in c.actuators}
    used={k for c in controls for k in (c.positive_key,c.negative_key) if k}
    ids={c.id for c in (*bp.components,*controls)}
    joints={c.id:c for c in bp.components if isinstance(c,Hinge)}
    motors=[c for c in bp.components if isinstance(c,Motor)]
    for root in bp.components:
        if not isinstance(root,Body) or root.catalog_part not in BY_ID:continue
        if module_roots is not None and root.id not in module_roots:continue
        item=BY_ID[root.catalog_part]
        prefix=root.id[:-4] if root.id.endswith('_root') else '' if root.id=='root' else root.id+'_'
        if item.variant=='real_robot':
            from little_world.assets.robot_models import blueprint
            for spec in blueprint(root.robot_asset).controllers:
                channel=int(spec.actuators[0].rsplit('_',1)[1])-1
                names=tuple(c.id for c in bp.components if isinstance(c,RobotServo) and c.body==root.id and c.channel==channel and c.id not in bound)
                if not names:continue
                pos,neg=spec.positive_key,spec.negative_key
                if pos in used or neg in used:
                    free=[k for k in 'UIOJKLZX0123456789QERTYGHVBNM' if k in BINDABLE_KEYS and k not in used]
                    if len(free)<2:continue
                    pos,neg=free[:2]
                name=prefix+spec.id
                controls.append(replace(spec,id=name,actuators=names,positive_key=pos,negative_key=neg))
                ids.add(name);bound.update(names);used.update((pos,neg))
            continue
        if item.variant in ('hw_arm','hw_arm_compact','hw_arm_long','ready_arm'):
            roles=(('yaw','Base yaw','Q','E',25,18,1.),('upper_arm','Shoulder','R','V',25,18,1.),
                   ('forearm','Elbow','T','B',25,18,1.),('wrist','Wrist','Y','N',25,18,1.))
        elif item.variant=='lab_tilt':
            roles=(('tilt_deck','Table tilt','R','V',20,24,1.5),)
        elif item.variant=='lab_index':
            roles=(('platter','Indexing table','Q','E',25,18,1.),)
        elif item.variant=='ready_camera':
            roles=(('pan','Camera pan','Q','E',25,12,.8),('tilt','Camera tilt','R','V',25,12,.8))
        elif item.variant in ('ready_fork','ready_scoop','ready_tray'):
            roles=(('moving','Attachment tilt','R','V',25,18,1.),)
        elif item.variant=='hw_servo':
            roles=(('horn','Servo','R','V',30,12,.8),)
        elif item.variant=='hw_wrist':
            roles=(('output','Wrist turntable','Y','N',25,12,.8),)
        elif 'gripper' in item.variant:
            roles=(('jaws','Gripper close / open','G','H',30,8,.25),)
        else:continue
        for body,label,pos,neg,speed,kp,kd in roles:
            names=tuple(m.id for m in motors if m.id not in bound and joints[m.joint].limits is not None and
                        (joints[m.joint].body in (prefix+'finger_left',prefix+'finger_right') if body=='jaws' else joints[m.joint].body==prefix+body))
            if not names:continue
            if pos in used or neg in used:
                free=[k for k in 'UIOJKLZX0123456789QERTYGHVBNM' if k in BINDABLE_KEYS and k not in used]
                if len(free)<2:continue
                pos,neg=free[:2]
            name='control_'+body;i=2
            while name in ids:name='control_'+body+'_'+str(i);i+=1
            controls.append(ControllerSpec(name,'keyboard_position',names,label,pos,neg,speed,kp,kd))
            ids.add(name);bound.update(names);used.update((pos,neg))
    return replace(bp,controllers=tuple(controls))
