"""Export a shared factory document, optionally reusing a saved builder machine.

No window is opened. Process connections represent intent, not running automation.
"""
import argparse
import json
from pathlib import Path
from little_world.assets.catalog import BY_ID
from little_world.core.blueprint import Blueprint
from little_world.core.component import Transform,Body,Geometry
from little_world.materials import METAL
from little_world.factory.document import FactoryDocument,MachineAsset,Station,ProcessLink
from little_world.factory.document_editor import FactoryEditor


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New factory JSON file; existing files are preserved')
    parser.add_argument('--machine',type=Path,help='Blueprint JSON saved by the existing builder')
    parser.add_argument('--check-physics',action='store_true',help='Compile the scene in MuJoCo without opening a window')
    args=parser.parse_args()
    machine=Blueprint.from_json(args.machine.read_text()) if args.machine else BY_ID['lab_index_table'].blueprint()
    ground=Blueprint((Body('floor',Geometry('box',(10,8,.1)),METAL.id,Transform((0,0,-.05))),),(METAL,))
    document=FactoryDocument(
        (MachineAsset('ground',ground),MachineAsset('roller',BY_ID['lab_roller_table'].blueprint()),MachineAsset('custom_machine',machine)),
        (Station('floor','ground','Floor'),Station('feed','roller','Passive feed rollers',Transform((-2,0,0))),
         Station('work','custom_machine','Custom work station'),Station('inspect','custom_machine','Second instance',Transform((2,0,0)))),
        (ProcessLink('feed_to_work','feed','work'),ProcessLink('work_to_inspect','work','inspect')))
    editor=FactoryEditor();proposal=editor.preview(document)
    report=proposal.report();report['physics_compiled']=False
    if args.check_physics:
        from little_world.physics.mujoco_backend import MujocoBackend
        backend=MujocoBackend()
        try:
            backend.compile(document.to_scene(),.002)
            report['physics_compiled']=True;report['native_bodies']=backend.model.nbody
        finally:backend.close()
    editor.apply(proposal)
    with args.output.open('x') as file:file.write(editor.document.to_json())
    report['output']=str(args.output)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
