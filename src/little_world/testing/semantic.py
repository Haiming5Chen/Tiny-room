"""Machine-readable inspection and bounded actions against the actual factory UI."""
import json
import math
from pathlib import Path
import tempfile


def snapshot(app):
    """Only detached JSON values; no private file contents or solver handles."""
    import glfw
    from little_world.factory.recipe import TRAYS
    controls=[dict(label=b.label,enabled=bool(b.enabled),bounds=[b.x,b.y,b.width,b.height]) for b in app.buttons]
    dialog=app.dialog
    view=None if dialog is None else dict(title=dialog.get('title','Review cell changes'),
        fields={name:value for name,value in dialog.get('fields',[])},error=dialog.get('error',''),
        choices=list(dialog.get('query') or ()))
    if getattr(app,'layout_mode',False):
        document=json.loads(app.layout.document.to_json())
        return dict(window_visible=bool(glfw.get_window_attrib(app.window,glfw.VISIBLE)),workspace='Real',view='Layout',
                    revision=app.layout.revision,stations={s['id']:s for s in document['stations']},links=document['links'],
                    selected=app.selected_station,can_undo=app.layout.can_undo,can_redo=app.layout.can_redo,
                    controls=controls,dialog=view,status=app.status)
    if app.app_mode=='Anime':
        return dict(window_visible=bool(glfw.get_window_attrib(app.window,glfw.VISIBLE)),workspace='Anime',
                    blueprint=json.loads(app.editor.blueprint.to_json()),controls=controls,dialog=view,status=app.status)
    result=dict(window_visible=bool(glfw.get_window_attrib(app.window,glfw.VISIBLE)),workspace=app.app_mode,experiment=app.experiment,robot=app.robot_asset,
        building=app.building,paused=app.paused,revision=app.recipe_revision,
        recipe=json.loads(app.recipe.to_json()),trays={n:list(app.recipe.point(n)) for n in TRAYS},
        undo_depth=len(app.recipe_history),redo_depth=len(app.recipe_future),
        status=app.status,note=app.authoring_note,controls=controls,dialog=view,
        simulation_time=float(app.data.time))
    proposal=app.cell_proposal
    result['proposal']=None if proposal is None else dict(summary=list(proposal.summary),
        fresh=proposal.revision==app.recipe_revision and proposal.before==app.recipe,
        after=json.loads(proposal.after.to_json()))
    cycle=app.cycle
    result['cycle']=None if cycle is None else dict(state=cycle.state,message=cycle.message,lift_verified=cycle.lift_verified,stage=cycle.index)
    product=app.model.body('objects/product').id
    result['product_position']=[float(x) for x in app.data.xpos[product]]
    motion=app.teach_motion
    result['teaching']=None if motion is None else dict(state=motion.state,message=motion.message,
        target=[float(x) for x in app.teach_point],saved=[p.name for p in app.teach_book.positions])
    return result


def value_at(state,path):
    value=state
    for key in path.split('.'):
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value


class SemanticDriver:
    """Uses real UI callbacks; does not emulate hit testing or OS event delivery."""
    def __init__(self,app,draw):self.app=app;self.draw=draw

    def observe(self):
        active=self.app.active_workspace
        self.draw() if active is self.app else active.draw()
        return snapshot(active)

    def execute(self,action):
        from little_world.factory.changes import CellRequest
        app=self.app.active_workspace;op=action['op']
        if op=='click':
            self.observe();matches=[b for b in app.buttons if b.label==action['label']]
            if len(matches)!=1:raise ValueError('Control label must match exactly one visible button: '+action['label'])
            if not matches[0].enabled:raise ValueError('Control is disabled: '+action['label'])
            matches[0].action()
        elif op=='fill':
            dialog=app.dialog
            if not dialog or 'fields' not in dialog:raise ValueError('No editable form is open.')
            matches=[i for i,f in enumerate(dialog['fields']) if f[0]==action['field']]
            if len(matches)!=1:raise ValueError('Field label must match exactly one field.')
            dialog['focus']=matches[0];dialog['replace']=True
            value=action['value']
            if not isinstance(value,str):raise ValueError('Form input must be text.')
            if not value:dialog['fields'][matches[0]][1]=''
            for character in value:app.character(app.window,ord(character))
            if dialog['fields'][matches[0]][1]!=value:raise ValueError('The form did not accept the requested text.')
        elif op=='propose':
            if not hasattr(app,'change_request'):raise ValueError('Cell proposals require the robot lab view.')
            # Full requests can be stale/malformed. A short changes list uses the current snapshot.
            request=action.get('request')
            if request is None:
                request=json.loads(app.change_request().to_json());request['changes']=action['changes']
                if 'revision' in action:request['revision']=action['revision']
            app.review_cell_request(CellRequest.from_json(json.dumps(request)))
        elif op=='advance':
            seconds=action['seconds']
            if type(seconds) not in (float,int) or not math.isfinite(seconds) or not 0<seconds<=60:
                raise ValueError('Advance requires 0 < seconds <= 60.')
            if app.building or app.paused:raise ValueError('Start or resume simulation before advancing.')
            for _ in range(math.ceil(seconds/app.world.timestep)):
                app.tick_program()
                commands=app.drive_control.step_commands(app.program_drive if app.program_drive is not None else app.controls.targets(),app.world.timestep,angular=app.program_drive is not None)
                commands.update(app.joint_commands());app.state=app.world.step(commands)
                if app.paused:break
        elif op=='expect':
            state=self.observe()
            for path,expected in action.get('equals',{}).items():
                actual=value_at(state,path)
                if actual!=expected:raise AssertionError(f'{path}: expected {expected!r}, got {actual!r}')
            for path,bounds in action.get('between',{}).items():
                actual=value_at(state,path)
                if not bounds[0]<=actual<=bounds[1]:raise AssertionError(f'{path}: {actual!r} outside {bounds!r}')
        elif op=='observe':pass
        else:raise ValueError('Unknown semantic action: '+str(op))
        return self.observe()


def run_scenario(scenario):
    """Run in a disposable native app; return a replayable trace including failures."""
    import glfw
    from little_world.ui.factory_workspace import FactoryWorkshop
    if not isinstance(scenario,dict) or not isinstance(scenario.get('actions'),list) or len(scenario['actions'])>500:
        raise ValueError('Scenario requires at most 500 actions.')
    report=dict(name=scenario.get('name','unnamed'),passed=False,steps=[],scope='native UI callbacks and physics; no language-model evaluation')
    with tempfile.TemporaryDirectory(prefix='little-world-test-') as directory:
        app=FactoryWorkshop(Path(directory)/'cell.json');draw=app.draw;finished=False
        driver=SemanticDriver(app,draw)
        def exercise():
            nonlocal finished
            if finished:return
            finished=True
            try:
                report['initial']=driver.observe()
                for index,action in enumerate(scenario['actions']):
                    before=driver.observe();error=None
                    try:after=driver.execute(action)
                    except Exception as failure:
                        error=dict(type=type(failure).__name__,message=str(failure));after=driver.observe()
                    expected=action.get('error_contains')
                    passed=(error is None) if expected is None else (error is not None and expected in error['message'])
                    report['steps'].append(dict(index=index,action=action,before=before,after=after,error=error,passed=passed))
                    if not passed:break
                report['passed']=len(report['steps'])==len(scenario['actions']) and all(s['passed'] for s in report['steps'])
                report['final']=driver.observe()
            except Exception as failure:report['fatal']=dict(type=type(failure).__name__,message=str(failure))
            finally:glfw.set_window_should_close(app.window,True)
        app.draw=exercise
        try:app.run(120,visible=False)
        except Exception as failure:report['fatal']=dict(type=type(failure).__name__,message=str(failure));report['passed']=False
    return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Replay agent-authored scenarios in an isolated, hidden Little World test window.')
    parser.add_argument('scenario',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    report=run_scenario(json.loads(args.scenario.read_text()))
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(dict(passed=report['passed'],steps=len(report['steps']),report=str(args.report))))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
