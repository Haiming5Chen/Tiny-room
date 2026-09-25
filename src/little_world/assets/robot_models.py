"""Pinned real assemblies. Registry paths are never supplied by saved designs."""
from functools import lru_cache
from pathlib import Path
import json

ROOT=Path(__file__).parent/'robots'/'panda'
MODELS={
 'franka_panda':('panda','panda.xml','Franka Panda + gripper'),
 'franka_fr3':('franka_fr3','fr3.xml','Franka Research 3 arm'),
 'kinova_gen3':('kinova_gen3','gen3.xml','Kinova Gen3 arm'),
 'ur5e':('universal_robots_ur5e','ur5e.xml','UR5e industrial arm'),
}


# Where a registered model's tool point is: a body and an offset in its frame. The Panda's
# is between its fingertips (as the factory cell grasps); an arm-only model's is the
# origin of the link its last joint turns, its flange.
TOOLS={'franka_panda':('hand',(0.,0.,.103))}


def asset_root(asset):
    if asset not in MODELS:raise ValueError('Unknown registered robot asset')
    return ROOT.parent/MODELS[asset][0]


def model_path(asset):
    return asset_root(asset)/MODELS[asset][1]


@lru_cache(maxsize=4)
def metadata(asset='franka_panda'):
    model_path(asset)
    return json.loads((asset_root(asset)/'metadata.json').read_text())


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
    if asset!='franka_panda':labels=tuple('Joint '+str(i+1) for i in range(len(meta['actuators'])))
    controls=tuple(ControllerSpec(('panda_' if asset=='franka_panda' else 'joint_')+str(i+1),'keyboard_position',(parts[i+1].id,),label,*keys[i],60 if i==7 else 20) for i,label in enumerate(labels[:len(meta['actuators'])]))
    return Blueprint(parts,(METAL,),controls)
