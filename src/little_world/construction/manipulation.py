"""Module-level gripper edits expressed entirely as ordinary Blueprint data."""
from dataclasses import replace
from little_world.core.component import Body,Geometry,Transform,Motor,positive
from little_world.materials import RUBBER,METAL,PLASTIC,WOOD

MATERIALS={m.id:m for m in (RUBBER,METAL,PLASTIC,WOOD)}


def gripper_root(editor):
    bodies={b.id:b for b in editor.bodies}
    body=editor.selected
    while body:
        prefix=body.id.removesuffix('_root')
        if all(prefix+'_'+name in bodies for name in ('finger_left','finger_right','palm_stop')):
            return body.id
        body=bodies.get(body.parent)
    return None


def configure_gripper(editor,shape,material,friction,torque,pad_length):
    root=gripper_root(editor)
    if root is None:raise ValueError('Select a gripper or one of its parts')
    if shape not in ('flat','round','narrow'):raise ValueError('Shape must be flat, round or narrow')
    if material not in MATERIALS:raise ValueError('Unknown pad material')
    positive(torque,'torque')
    if torque>5:raise ValueError('Jaw torque must be at most 5 Nm')
    if not .02<=pad_length<=.09:raise ValueError('Pad length must be 20 to 90 mm')
    prefix=root.removesuffix('_root')
    mat=replace(MATERIALS[material],id=prefix+'_contact',sliding_friction=friction)
    parts=[]
    for c in editor.blueprint.components:
        if isinstance(c,Body) and c.id in (prefix+'_finger_left_pad',prefix+'_finger_right_pad'):
            # The pad stays centred along the jaw; all variants are actual collision geometry.
            geom=Geometry('cylinder',(.0075,pad_length)) if shape=='round' else Geometry('box',(pad_length,.008,.018 if shape=='narrow' else .035))
            q=(2**-.5,0,2**-.5,0) if shape=='round' else (1,0,0,0)
            c=replace(c,geometry=geom,material=mat.id,transform=replace(c.transform,quaternion=q))
        elif isinstance(c,Body) and c.id==prefix+'_palm_stop':
            c=replace(c,material=mat.id)
        elif isinstance(c,Motor) and c.id in (prefix+'_finger_left_joint_motor',prefix+'_finger_right_joint_motor'):
            c=replace(c,max_torque=torque)
        parts.append(c)
    materials=tuple(m for m in editor.blueprint.materials if m.id!=mat.id)+(mat,)
    editor._commit(replace(editor.blueprint,components=tuple(parts),materials=materials))
