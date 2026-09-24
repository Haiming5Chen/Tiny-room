"""Explanations from authored parts; no physical calibration or payload guarantee."""
from dataclasses import asdict
from math import pi
from little_world.core.component import Body,Hinge,Motor,RobotServo,Transform
from little_world.construction.connections import rotate,multiply


def mass(body,materials):
    if body.robot_asset:
        from little_world.assets.robot_models import metadata
        return metadata(body.robot_asset)['mass']
    g=body.geometry
    volume=g.size[0]*g.size[1]*g.size[2] if g.shape=='box' else pi*g.size[0]**2*g.size[1] if g.shape=='cylinder' else 4*pi*g.size[0]**3/3
    return volume*materials[body.material].density


def analyze(blueprint):
    bodies={c.id:c for c in blueprint.components if isinstance(c,Body)}
    materials={m.id:m for m in blueprint.materials}
    hinges=[c for c in blueprint.components if isinstance(c,Hinge)]
    motors=[c for c in blueprint.components if isinstance(c,Motor)]
    masses={b.id:mass(b,materials) for b in bodies.values()};poses={}
    def pose(name):
        if name in poses:return poses[name]
        b=bodies[name];t=b.transform
        if b.parent:
            p=pose(b.parent);v=rotate(p.quaternion,t.position)
            t=Transform(tuple(a+c for a,c in zip(p.position,v)),multiply(p.quaternion,t.quaternion))
        poses[name]=t;return t
    for name in bodies:pose(name)
    children={}
    for b in bodies.values():children.setdefault(b.parent,[]).append(b.id)
    def subtree(name):
        result={name}
        for child in children.get(name,[]):result.update(subtree(child))
        return result
    controlled={a for c in blueprint.controllers for a in c.actuators}
    moving=set()
    for b in bodies.values():
        if b.dynamic:moving.update(subtree(b.id))
    for h in hinges:moving.update(subtree(h.body))
    loads=[]
    for h in hinges:
        t=poses[h.body];v=rotate(t.quaternion,h.position);pivot=tuple(a+b for a,b in zip(t.position,v));axis=rotate(t.quaternion,h.axis)
        torque=0.
        for name in subtree(h.body):
            r=tuple(a-b for a,b in zip(poses[name].position,pivot));torque+=9.81*masses[name]*(-r[1]*axis[0]+r[0]*axis[1])
        available=sum(m.max_torque for m in motors if m.joint==h.id)
        if available:loads.append(dict(joint=h.id,gravity_Nm=abs(torque),cap_Nm=available,margin_Nm=available-abs(torque)))
    servos=[c for c in blueprint.components if isinstance(c,RobotServo)]
    pros=[];cons=[]
    if servos:
        pros.append("Real robot assemblies retain upstream meshes, inertias, limits and position servos.")
        cons.append("Imported robot models are approximations, not validated digital twins; internal dimensions are fixed.")
    if any(c.kind=='differential_torque' for c in blueprint.controllers):pros.append('Drive controller present: the base can receive coordinated wheel commands.')
    if motors and len(controlled)==len(motors):pros.append(f'All {len(motors)} motors have assigned control actions.')
    if any(h.limits is not None for h in hinges):pros.append('Limited joints provide explicit angle bounds in simulation.')
    profiles=sum(m.profile is not None for m in motors)
    if profiles:pros.append(f'{profiles} motors use sourced endpoints with estimated speed-dependent limits.')
    if loads and any(l['gravity_Nm']>.05 for l in loads) and all(l['margin_Nm']>=0 for l in loads):
        pros.append('Motor caps cover the gravity-only starting-pose estimate; dynamic and payload loads remain untested.')
    pads=[b for b in bodies.values() if '_finger_' in b.id and b.id.endswith('_pad')]
    if pads:
        friction=min(materials[b.material].sliding_friction for b in pads)
        pros.append(f'Jaw contact pads are modeled with sliding friction {friction:g}; the contacted material also matters.')
    unbound=len([m for m in motors if m.id not in controlled])
    if unbound:cons.append(f'{unbound} motors are not bound to a control action.')
    unbound+=sum(c.id not in controlled for c in servos)
    if any(c.id not in controlled for c in servos):cons.append('Some real-robot servos have no key pair; they hold their home target.')
    if not motors and not servos:cons.append('No motors: this is a passive assembly.')
    if not any(b.dynamic for b in bodies.values()):cons.append('Base is fixed to the world; this design cannot drive as assembled.')
    weak=sorted((l for l in loads if l['margin_Nm']<0),key=lambda l:l['margin_Nm'])
    for l in weak[:3]:cons.append(f'{l["joint"]}: {l["gravity_Nm"]:.2f} Nm estimated gravity load exceeds {l["cap_Nm"]:.2f} Nm cap at the starting pose.')
    if len(motors)>profiles:cons.append(f'{len(motors)-profiles} motor limits are ideal estimates, without a sourced model.')
    cons.append('Payload, grasp reliability and stability require task tests; parts alone cannot establish them.')
    from little_world.assets.robot_models import metadata
    robot_joints=sum(len(metadata(b.robot_asset)['joints']) for b in bodies.values() if b.robot_asset)
    internal_moving=sum(metadata(b.robot_asset)['moving_mass'] for b in bodies.values() if b.robot_asset and b.id not in moving)
    return dict(parts=len(bodies),motors=len(motors)+len(servos),joints=len(hinges)+robot_joints,mass_kg=sum(masses.values()),moving_mass_kg=sum(masses[n] for n in moving)+internal_moving,
                profiled_motors=profiles,unbound_motors=unbound,gravity_loads=loads,pros=pros,cons=cons,
                basis='Source-model mass for registered robots; geometry/density for kit parts; gravity-only starting pose; ignores support contacts, acceleration and payload; not physical validation')


def differences(left,right):
    result={}
    for field in ('components','materials','controllers'):
        a={c.id:c for c in getattr(left,field)};b={c.id:c for c in getattr(right,field)}
        result[field]=dict(added=sorted(a.keys()-b.keys()),removed=sorted(b.keys()-a.keys()),changed=sorted(k for k in a.keys() & b.keys() if a[k]!=b[k]))
    return result


def changed_fields(left,right):
    """Saved -> current field values, including geometry and material parameters."""
    lines=[]
    def walk(a,b,prefix):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(a.keys() | b.keys()):walk(a.get(key),b.get(key),prefix+'.'+key)
        elif a!=b:lines.append(prefix+': '+str(b)+' -> '+str(a))
    for kind in ('components','materials','controllers'):
        current={c.id:c for c in getattr(left,kind)};saved={c.id:c for c in getattr(right,kind)}
        for name in sorted(current.keys() & saved.keys()):
            if current[name]!=saved[name]:walk(asdict(current[name]),asdict(saved[name]),kind+'/'+name)
    return lines
