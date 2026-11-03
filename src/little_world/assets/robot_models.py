"""Pinned real assemblies. Registry paths are never supplied by saved designs.

The four Menagerie arms ship with Little World; robots imported from their own description
files are in the user's robot library and named `user:<name>` (ADR 0044,
`robot_library.py`). Both are placed, driven and programmed the same way.
"""
from functools import lru_cache
from pathlib import Path
import json

from little_world.assets import robot_library

ROOT=Path(__file__).parent/'robots'/'panda'
MODELS={
 'franka_panda':('panda','panda.xml','Franka Panda + gripper'),
 'franka_fr3':('franka_fr3','fr3.xml','Franka Research 3 arm'),
 'kinova_gen3':('kinova_gen3','gen3.xml','Kinova Gen3 arm'),
 'ur5e':('universal_robots_ur5e','ur5e.xml','UR5e industrial arm'),
}


# Where a registered model's tool point is: a body and an offset in its frame. The Panda's
# is between its fingertips (as the factory cell grasps); an arm-only model's is the
# origin of the link its last joint turns, its flange. An imported robot's is in its
# metadata: a link named like a tool, else its last driven link.
TOOLS={'franka_panda':('hand',(0.,0.,.103))}

# What a real arm's controller does that its model's servos do not (OPEN LW-036). Franka's holds
# the arm against gravity - its joint torques include the arm's weight - so a commanded pose is
# reached, not sagged under; its hand squeezes with 70 N continuously, 140 N at most (Franka Hand
# datasheet), where Menagerie's hand is a 100 N/m spring on its fingers' tendon: 1.6 N on a 32 mm
# part; and its fingers move at 50 mm/s each, where Menagerie's close at 0.26 m/s. (hand actuator,
# the squeeze in newtons on each finger, the fingers' bodies, their speed in m/s)
CONTROLLERS={'franka_panda':dict(gravcomp=True,hand=('actuator8',70.,('left_finger','right_finger'),.05))}


def asset_root(asset):
    if robot_library.is_user(asset):return robot_library.folder(asset)
    if asset not in MODELS:raise ValueError('Unknown registered robot asset')
    return ROOT.parent/MODELS[asset][0]


def model_path(asset):
    return asset_root(asset)/('model.xml' if robot_library.is_user(asset) else MODELS[asset][1])


@lru_cache(maxsize=16)
def metadata(asset='franka_panda'):
    model_path(asset)
    return json.loads((asset_root(asset)/'metadata.json').read_text())


def title(asset):
    return metadata(asset)['title'] if robot_library.is_user(asset) else MODELS[asset][2]


def tool(asset):
    """(body, offset) of the tool point, or (None, origin) where the last arm joint's link is."""
    if asset in TOOLS:return TOOLS[asset]
    name,offset=metadata(asset).get('tool') or (None,(0.,0.,0.))
    return name,tuple(offset)


def units(asset):
    """What each servo channel is driven in: 'deg' (a hinge), 'mm' (a slide) or '%' (the Panda's
    gripper, closed by a fraction of its travel)."""
    meta=metadata(asset)
    if 'units' in meta:return tuple(meta['units'])
    return tuple('%' if asset=='franka_panda' and i==7 else 'deg' for i in range(len(meta['actuators'])))


def grip(asset, channel):
    """For a gripper servo: (its control when open, when closed, its joint's position open,
    closed); None for any other servo. The Panda's gripper takes 0 to 255 for 4 cm to closed; an
    imported gripper's control is its joint's position (ADR 0047)."""
    if asset=='franka_panda' and channel==7:return (255.,0.,.04,0.)
    g=metadata(asset).get('gripper')
    if g and g['channel']==channel:return (g['open'],g['closed'],g['open'],g['closed'])
    return None


def jaws(asset):
    """The two links an imported gripper holds between, or ()."""
    g=metadata(asset).get('gripper') if robot_library.is_user(asset) else None
    return tuple(g['jaws']) if g else ()


def blueprint(asset='franka_panda'):
    from little_world.core.component import Body,Geometry,Transform,Attachment,RobotServo
    from little_world.core.blueprint import Blueprint,ControllerSpec
    from little_world.materials import METAL
    meta=metadata(asset);center=tuple(meta['center'])
    root=Body('root',Geometry('box',meta['size']),'metal',Transform(center),
              attachments=(Attachment('mount',Transform(tuple(-x for x in center),(0,1,0,0))),),
              catalog_part=asset,robot_asset=asset)
    parts=(root,)+tuple(RobotServo('servo_'+str(i+1),'root',i) for i in range(len(meta['actuators'])))
    keys=(('Q','E'),('R','V'),('T','B'),('Y','N'),('U','J'),('I','K'),('O','L'),('G','H'))
    labels=('Base rotation','Shoulder','Upper-arm rotation','Elbow','Forearm rotation','Wrist bend','Wrist rotation','Gripper close / open')
    if asset!='franka_panda':labels=tuple(meta.get('labels') or ('Joint '+str(i+1) for i in range(len(meta['actuators']))))
    # A slide is jogged in mm/s, a hinge in degrees/s.
    speeds=tuple(60 if u=='%' else 50 if u=='mm' else 20 for u in units(asset))
    grips=metadata(asset).get('gripper')
    if asset!='franka_panda' and grips:labels=tuple('Gripper close / open' if i==grips['channel'] else l for i,l in enumerate(labels))
    controls=tuple(ControllerSpec(('panda_' if asset=='franka_panda' else 'joint_')+str(i+1),'keyboard_position',(parts[i+1].id,),label,*keys[i],speeds[i]) for i,label in enumerate(labels[:len(meta['actuators'])]))
    return Blueprint(parts,(METAL,),controls)
