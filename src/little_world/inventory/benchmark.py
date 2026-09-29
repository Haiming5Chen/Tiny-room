"""Isolated reproducible trials; never touches the interactive world."""
from dataclasses import asdict
from datetime import datetime,timezone
from math import degrees,acos,hypot
import hashlib,json
from .store import fingerprint


def environment_fingerprint():
    # The room and the contact table together: changing a sourced friction pair changes
    # every trial, so a stored comparison made under the old table must read as historical.
    from little_world.scenes.workshop import workshop_entities
    from little_world.materials import contact_pairs
    room=json.dumps([asdict(e) for e in workshop_entities()],sort_keys=True)
    return hashlib.sha256((room+contact_pairs.fingerprint()).encode()).hexdigest()


def compare_trials(left,right,program,mode='hold_drive',seconds=5.,dt=.002):
    import mujoco
    if mode not in ('hold_drive','program'):raise ValueError('Unknown trial')
    if not 0<seconds<=10 or dt!=.002:raise ValueError('Trial requires at most 10 seconds and 0.002s steps')
    if mode=='program' and not program.blocks:raise ValueError('The current program is empty')
    protocol=dict(mode=mode,seconds=seconds,timestep=dt,solver=mujoco.__version__,environment=environment_fingerprint(),program=fingerprint(program) if mode=='program' else None,revision=1)
    return dict(version=1,created=datetime.now(timezone.utc).isoformat(),left_hash=fingerprint(left),right_hash=fingerprint(right),protocol=protocol,
                left=trial(left,program,mode,seconds,dt),right=trial(right,program,mode,seconds,dt),
                evidence='Simulated under identical conditions; mechanical work is not electrical energy; no physical validation')


def trial(bp,program,mode,seconds,dt):
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.core.world import World
    from little_world.core.entity import Entity
    from little_world.core.component import Body
    from little_world.scenes.workshop import workshop_scene
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.programming.program import Runner
    from little_world.programming.observations import Observations
    backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',bp)),dt) as world:
        world.start();model,data=backend.model,backend.data;control=MujocoKeyboardControl(backend,bp);obs=Observations(model,data)
        runner=Runner()
        if mode=='program':program.validate(bp,tuple(obs.indices));runner.start(program)
        from little_world.control.mujoco_drive import MujocoDrive
        drive_control=MujocoDrive(backend,bp)
        from little_world.control.navigation import BasePose
        try:base=BasePose(backend,drive_control,bp)
        except ValueError:base=None
        motor_channels={}
        for i in range(model.nu):motor_channels[i]=i
        root=next(b.id for b in bp.components if isinstance(b,Body) and b.parent is None)
        root_id=model.body('machine/'+root).id;start=data.xpos[root_id].copy()
        peak_tilt=peak_error=work=0.;limited=0;trace=[]
        for step in range(round(seconds/dt)):
            drive=(3.,3.) if mode=='hold_drive' and step*dt<2 else (0.,0.)
            control.clear()
            if mode=='program' and runner.state=='running':
                from little_world.programming.execution import apply,base_targets,joint_angles,needs_grasp
                contacts,distances=obs.program_inputs(program)
                held=obs.grasped() if needs_grasp(program) else frozenset()
                output=runner.tick(dt,joint_angles(control),contacts,distances,held,base.pose() if base else None)
                drive=base_targets(output,base) if output['base'] else output['drive']
                for key in apply(output,control):control.press(key)
            commands=control.step_commands(dt)
            commands.update(drive_control.step_commands(drive,dt,angular=mode=='program'))
            velocities={i:float(data.actuator_velocity[i]) for i in motor_channels}
            world.step(commands)
            work+=sum(abs(float(data.actuator_force[i])*v)*dt for i,v in velocities.items())
            peak_tilt=max(peak_tilt,degrees(acos(max(-1,min(1,float(data.xmat[root_id,8]))))))
            error=max((abs(degrees(control.targets[n]-data.qpos[c[0]])) for n,c in control.channels.items() if n not in control.servos or control.servos[n][1]<7),default=0.)
            peak_error=max(peak_error,error)
            if any(abs(float(data.actuator_force[i]))>=max(abs(float(v)) for v in model.actuator_forcerange[i])*.95 if model.actuator_forcelimited[i] else abs(float(data.ctrl[i]))>=float(model.actuator_ctrlrange[i,1])*.95 for i in motor_channels):limited+=1
            if step%50==0:trace.append(dict(time_s=round(float(data.time),3),distance_m=hypot(*(data.xpos[root_id,:2]-start[:2])),joint_error_deg=error))
        return dict(elapsed_s=float(data.time),displacement_m=hypot(*(data.xpos[root_id,:2]-start[:2])),peak_tilt_deg=peak_tilt,
                    peak_joint_error_deg=peak_error,absolute_mechanical_work_J=work,cap_fraction=limited/(step+1),
                    program_state=runner.state if mode=='program' else 'not used',message=runner.message if mode=='program' else 'Drive at 60% of configured speed for 2s, then hold; fixed bases hold throughout',trace=trace)
