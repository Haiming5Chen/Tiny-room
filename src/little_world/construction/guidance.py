"""Construction suggestions and missing-input checks, not mechanical certification."""
from little_world.core.component import Body,Motor,RobotServo


def build_checks(blueprint):
    motors=[c for c in blueprint.components if isinstance(c,Motor)]
    controlled={a for c in blueprint.controllers for a in c.actuators}
    checks=[]
    if not motors and not any(isinstance(c,RobotServo) for c in blueprint.components):checks.append('No powered joints yet.')
    unbound=[m.id for m in blueprint.components if isinstance(m,(Motor,RobotServo)) and m.id not in controlled]
    if unbound:checks.append(f'{len(unbound)} motors have no keyboard/program action.')
    free=[c for c in blueprint.components if isinstance(c,Body) and c.dynamic]
    if len(free)>1:checks.append(f'{len(free)} separate moving roots; check attachments.')
    if any(m.profile for m in motors):checks.append('Motor models assigned; physical fit still unverified.')
    if any(not m.profile for m in motors):checks.append('Some motor capabilities are ideal estimates.')
    return tuple(checks or ('Structure references and controls are connected.',))


def suggestions(editor):
    b=editor.selected
    if b is None or b.robot_asset:return ()
    frames={a.id for a in b.attachments}
    occupied=any(child.parent==b.id and any(a.id=='assembly_top' for a in child.attachments) for child in editor.bodies)
    if occupied:return ()
    if 'tool' in frames:return (('two_finger_gripper','Attach a gripper to this tool frame'),)
    if 'output' in frames:return (('tread_wheel','Attach a wheel to this output'),)
    if editor.gripper_root():return ()
    if b.geometry.shape=='box' and b.geometry.size[0]>=.14 and b.geometry.size[1]>=.1:
        return (('robot_arm_compact','Add compact arm on this deck'),('robot_arm','Add standard arm on this deck'))
    return (('chassis_plate','Add a mounting plate'),)


def add_suggested(editor,item_id):
    from .editor import AssemblyEditor
    from little_world.robots.arm_lab import attach_arm
    trial=AssemblyEditor(editor.blueprint);trial.select(editor.selection)
    target=trial.selection
    if item_id in ('robot_arm_compact','robot_arm','robot_arm_long'):
        attach_arm(trial,item_id)
    else:
        trial.add_catalog(item_id)
        if item_id=='two_finger_gripper':
            trial.snap(target,'tool_mount','tool')
            trial.bind_keys('Gripper close / open','G','H',30,8,.25)
        elif item_id=='tread_wheel':
            trial.snap(target,'Bottom','output');trial.make_fixed()
    editor._commit(trial.blueprint,trial.selection)
