"""All native MuJoCo construction and runtime operations live in this adapter."""
from math import isfinite, sqrt
import mujoco as mj
import numpy as np
from little_world.core.command import slope_of
from little_world.core.component import Body, Hinge, Motor, RobotServo, Camera, Transform, positive
from little_world.core.state import State, BodyState, DeferredBodyStates
from little_world.assets.textures import TEXTURES, SIZE, texture_bytes
from little_world.materials import surface_of
from little_world.materials import contact_pairs
from little_world.materials import rolling

_IMPLICIT = (mj.mjtIntegrator.mjINT_IMPLICIT, mj.mjtIntegrator.mjINT_IMPLICITFAST)

# MuJoCo's dry friction (frictionloss) is a soft constraint. Until the damping it asks
# for reaches the friction bound it acts as a damper, so a joint loaded below its
# friction creeps and a coasting one stops late - by how much depends on the inertia
# behind it. Sourced friction (ADR 0011) gets the stiffest settings MuJoCo accepts: a
# reference time constant of two steps and impedance 0.9999 (mjMAXIMP). Measured on a
# Pololu 37D output driving a 2.2e-4 kg m^2 disc, against MuJoCo's defaults: coast-down
# from no-load speed 0.145 s, as Coulomb friction predicts (0.213 s); under 80 % of the
# friction torque it holds (crept 0.20 rad in 1 s); a bare output shaft runs at the
# datasheet's 330 rpm (3.7 % fast). Joints without sourced friction keep the defaults.
DRY_FRICTION_SOLIMP = (.9999, .9999, .001, .5, 2.)
NOSLIP_ITERATIONS = 2
# One contact per convex pair, as in every MuJoCo release before 3.8 made multiccd the
# default (ADR 0027). For a cylinder wheel on the box floor multiccd's extra contacts lie
# within 0.1 mm of each other and the solver loads the leading one more as the wheel rolls:
# a rolling loss of the engine's own on top of the sourced one (5 % of it at 0.8 m/s, 6 %
# at 1.6). Flip this only to compare.
MULTICCD = False
SHAPES = ('plane', 'height field', 'sphere', 'capsule', 'ellipsoid', 'cylinder', 'box', 'mesh', 'sdf')  # mjtGeom, in order
_CONTACT_ROWS = np.array([int(mj.mjtConstraint.mjCNSTR_CONTACT_FRICTIONLESS), int(mj.mjtConstraint.mjCNSTR_CONTACT_PYRAMIDAL),
                          int(mj.mjtConstraint.mjCNSTR_CONTACT_ELLIPTIC)])


def dry_friction_solref(timestep):
    return (2 * timestep, 1.)


def _fwd_position(m, d, contact_hook):
    """mj_fwdPosition in MuJoCo's order (written for 3.3.7, unchanged in 3.10.0), with one
    hook between collision detection and constraint construction - the only point at which
    a contact's friction can be set and still reach the solver. See ADR 0010; bit-identity
    with mj_step is tested, so a release that reorders the stage fails that test."""
    mj.mj_kinematics(m, d); mj.mj_comPos(m, d); mj.mj_camlight(m, d)
    mj.mj_flex(m, d); mj.mj_tendon(m, d)
    mj.mj_makeM(m, d); mj.mj_factorM(m, d)
    mj.mj_collision(m, d)
    contact_hook(m, d)
    mj.mj_makeConstraint(m, d); mj.mj_island(m, d)
    mj.mj_transmission(m, d); mj.mj_projectConstraint(m, d)


def _after_position(m, d, energy_sensor):
    """The rest of mj_forwardSkip once the position stage is done."""
    mj.mj_sensorPos(m, d)
    if not energy_sensor:
        if m.opt.enableflags & mj.mjtEnableBit.mjENBL_ENERGY:
            mj.mj_energyPos(m, d)
        else:
            d.energy[:2] = 0
    mj.mj_forwardSkip(m, d, mj.mjtStage.mjSTAGE_POS, 0)


def apply_pair_friction(d, geom_surface, pair_mu):
    """Overwrite the tangential friction of every contact whose surface pair is sourced.

    Only those contacts are written: an unsourced one keeps all five of MuJoCo's values,
    including a second tangent coefficient that an explicit <pair> may have made
    different from the first. One fancy assignment, a few microseconds per step."""
    if not d.ncon:
        return
    surface = geom_surface[d.contact.geom]
    mu = pair_mu[surface[:, 0], surface[:, 1]]
    sourced = np.flatnonzero(mu == mu)          # NaN marks an unsourced pair
    if sourced.size:
        d.contact.friction[sourced, :2] = mu[sourced, None]


_WHEEL_SHAPES = (mj.mjtGeom.mjGEOM_CYLINDER, mj.mjtGeom.mjGEOM_SPHERE)
_RING_GAP = np.pi / 4    # a tread ring leaves no gap wider than this around its axle
_RADIAL = .95            # a rolling contact's normal points at the axle, within 18 degrees


def _rolling_tables(model, pose, geom_surfaces):
    """Which geoms are wheel treads, and the hinge each one rolls on.

    A geom is a tread when its surface has a sourced rolling lever arm, it is rigidly
    part of a body whose only joint is a hinge, and it is shaped like a wheel about
    that hinge: a cylinder on the axis, a sphere centred on it, or one element of a
    ring of same-surface elements around it with no gap wider than 45 degrees (the
    tread blocks of a tread wheel). A rubber gripper pad on a hinged finger is not a
    tread, although it presses on things. `pose` is any MjData after kinematics: only
    positions relative to the hinge matter, and those are rigid. None when nothing in
    the scene has a tread - then no joint loss is ever written and the step is untouched.
    """
    b = np.zeros(model.ngeom)
    for name, surface in geom_surfaces.items():
        b[model.geom(name).id] = rolling.lever_arm(surface)
    g = np.flatnonzero(b)
    body = model.body_weldid[model.geom_bodyid[g]]
    j = model.body_jntadr[body]
    hinged = (body > 0) & (model.body_jntnum[body] == 1)
    hinged[hinged] = model.jnt_type[j[hinged]] == mj.mjtJoint.mjJNT_HINGE
    g, j = g[hinged], j[hinged]
    joint = np.full(model.ngeom, -1, dtype=np.intp)
    if g.size:
        axis = pose.xaxis[j]
        offset = pose.geom_xpos[g] - pose.xanchor[j]
        radial = offset - np.einsum("ij,ij->i", offset, axis)[:, None] * axis
        centred = np.linalg.norm(radial, axis=1) < 1e-3
        along = np.abs(np.einsum("ij,ij->i", pose.geom_xmat[g].reshape(-1, 3, 3)[:, :, 2], axis))
        kind = model.geom_type[g]
        wheel = centred & ((kind == mj.mjtGeom.mjGEOM_SPHERE) |
                           (np.isin(kind, _WHEEL_SHAPES) & (along > .996)))
        joint[g[wheel]] = j[wheel]
        rim = ~centred
        if rim.any():
            a, r = axis[rim], radial[rim]
            reference = np.where(np.abs(a[:, :1]) < .9, (1., 0., 0.), (0., 1., 0.))
            e1 = np.cross(a, reference)
            e1 /= np.linalg.norm(e1, axis=1)[:, None]
            angle = np.arctan2(np.einsum("ij,ij->i", np.cross(a, e1), r), np.einsum("ij,ij->i", e1, r))
            members, hinge, arm = g[rim], j[rim], b[g[rim]]
            for key in {(int(h), float(x)) for h, x in zip(hinge, arm)}:
                ring = (hinge == key[0]) & (arm == key[1])
                angles = np.sort(angle[ring])
                if np.diff(np.r_[angles, angles[0] + 2 * np.pi]).max() <= _RING_GAP:
                    joint[members[ring]] = key[0]
    rolls = joint >= 0
    if not rolls.any():
        return None
    dofs = np.unique(model.jnt_dofadr[joint[rolls]])
    return dict(b=np.where(rolls, b, 0.), tread=rolls, joint=joint, dofs=dofs,
                root=model.body_rootid[model.geom_bodyid], force=np.zeros(6))


def apply_rolling_resistance(m, d, tables, base):
    """Set each wheel hinge's dry friction to b * N for the step that follows.

    N is the normal force the solver has just found at that wheel's tread contacts
    with anything outside its own machine. Only rolling contacts count: the contact
    normal has to point at the axle (within 18 degrees), so a caster's swivel, a
    wheel's side face against a wall and a tread block's flank against a kerb are not
    charged. MuJoCo applies the loss as frictionloss, a constraint - a stopped wheel
    is held, not jittered - with the stiff parameters set at compile time. A handful
    of contacts qualify in any scene, so they are handled one by one in plain Python.
    """
    loss = base.copy()
    if d.ncon:
        tread, root = tables["tread"], tables["root"]
        con = d.contact
        geoms = con.geom
        hit = tread[geoms]
        rows = np.flatnonzero(hit[:, 0] | hit[:, 1])
        if rows.size:
            b, joint, dofadr, f6 = tables["b"], tables["joint"], m.jnt_dofadr, tables["force"]
            pos, frame, xaxis, xanchor = con.pos, con.frame, d.xaxis, d.xanchor
            for i in rows.tolist():
                pair = geoms[i].tolist()
                for side in (0, 1):
                    g, other = pair[side], pair[1 - side]
                    if not tread[g] or root[g] == root[other]:
                        continue
                    j = joint[g]
                    ax, ay, az = xaxis[j].tolist()
                    px, py, pz = (pos[i] - xanchor[j]).tolist()
                    along_axis = px * ax + py * ay + pz * az
                    rx, ry, rz = px - along_axis * ax, py - along_axis * ay, pz - along_axis * az
                    nx, ny, nz = frame[i, :3].tolist()
                    toward = nx * rx + ny * ry + nz * rz
                    if toward * toward < _RADIAL * _RADIAL * (rx * rx + ry * ry + rz * rz):
                        continue
                    mj.mj_contactForce(m, d, i, f6)
                    loss[dofadr[j]] += b[g] * max(f6[0], 0.)
    dofs = tables["dofs"]
    m.dof_frictionloss[dofs] = loss[dofs]


def staged_forward(m, d, contact_hook, energy_sensor=False):
    _fwd_position(m, d, contact_hook)
    _after_position(m, d, energy_sensor)


def staged_step(m, d, contact_hook, energy_sensor=False):
    """mj_step with a contact hook. Identical to mj_step when the hook changes nothing."""
    mj.mj_checkPos(m, d); mj.mj_checkVel(m, d)
    staged_forward(m, d, contact_hook, energy_sensor)
    mj.mj_checkAcc(m, d)
    if m.opt.enableflags & mj.mjtEnableBit.mjENBL_FWDINV:
        mj.mj_compareFwdInv(m, d)
    if m.opt.integrator in _IMPLICIT:
        mj.mj_implicit(m, d)
    elif m.opt.integrator == mj.mjtIntegrator.mjINT_RK4:
        mj.mj_RungeKutta(m, d, 4)
    else:
        mj.mj_Euler(m, d)


FINGER_SOLMIX = 1000.     # a held robot's fingers: their contacts take the fingers' stiffness (OPEN LW-036)


def held(child, asset, on_free_base):
    """A registered robot as its own controller drives it (OPEN LW-036; `robot_models.CONTROLLERS`):
    its links held against gravity - only on a fixed base: on a cart MuJoCo's compensation would
    lift the cart's free joint too - and its hand squeezing with its datasheet's force, the
    fingers' contacts as stiff as an imported gripper's jaws (ADR 0047). Returns the hand's
    actuator and how fast its control may change, per second, for its fingers to move at their
    datasheet's speed - or None."""
    from little_world.assets.robot_models import CONTROLLERS
    from little_world.physics.importer import JAW_SOLIMP, JAW_SOLREF
    controller = CONTROLLERS.get(asset)
    if not controller:
        return None
    if controller.get('gravcomp') and not on_free_base:
        for body in child.bodies:
            if body.name and body.name != 'world':
                body.gravcomp = 1.
    hand = controller.get('hand')
    if hand:
        name, squeeze, fingers, speed = hand
        rate = None
        for act in child.actuators:
            if act.name == name:
                # A stiff servo on the tendon, limited to the squeeze: each finger takes half the
                # tendon's force, so the limit is twice the squeeze.
                act.gainprm[0] *= 100.
                act.biasprm[1] *= 100.
                act.biasprm[2] = -100.
                act.forcerange[:] = (-2. * squeeze, 2. * squeeze)
                # Its control is where the fingers are sent, -biasprm[1] / gainprm[0] of it a metre.
                rate = speed * -act.biasprm[1] / act.gainprm[0]
        for body in child.bodies:
            if body.name in fingers:
                for g in body.geoms:
                    g.solref[:] = JAW_SOLREF
                    g.solimp[:3] = JAW_SOLIMP
                    # MuJoCo averages a contact's stiffness over its two geoms, weighted by solmix:
                    # weighted so, a finger's contact with a part is the finger's, not half the part's.
                    g.solmix = FINGER_SOLMIX
        return name, rate
    return None


class MujocoBackend:
    def __init__(self):
        self.model = self.data = None
        self._renderer = None
        self._preview_context = None
        self._body_ids = {}
        self._motor_ids = {}
        self._camera_ids = {}
        self._seen = None           # what the cameras see when not the world now: a past moment (FR-028)
        self._past = None           # the MjData that moment is laid out in, made once
        self._static_states = {}
        self._motor_profiles = {}
        self._motor_original = {}   # a weakened motor's profile as compiled (ADR 0058)
        self._mass_original = {}    # a body made heavier for a run: its mass and inertia as compiled (FR-036)
        self._hand_rates = {}       # a held robot's hand: how fast its control may change (OPEN LW-036)
        self._hand_goals = {}       # and where it was last sent
        self._geom_surface = None
        self._pair_mu = None
        self._any_sourced = False
        self._energy_sensor = False
        self._name_list = None       # every body's name by its id, made when first asked (FR-040)
        self._speeds_before = None   # every joint's speed when the last step began (FR-040)
        self._base_frictionloss = None
        self._roll = None  # rolling-resistance tables, or None when nothing rolls on a sourced tread
        self._affine = np.zeros(0, dtype=np.intp)  # kit motors: their slope, if any, is integrated implicitly
        self._motor_dofs = {}

    def compile(self, scene, timestep):
        positive(timestep, "timestep")
        spec = mj.MjSpec()
        spec.visual.quality.shadowsize = 1024
        spec.compiler.degree = True  # Blueprint hinge limits are in degrees
        # Stable asset order/content lets the workshop retain GPU resources
        # across primitive edits and material changes without re-upload stalls.
        for name in TEXTURES:
            tex=spec.add_texture(name=name, type=mj.mjtTexture.mjTEXTURE_2D,
                                 width=SIZE, height=SIZE, nchannel=3)
            tex.data=texture_bytes(name)
        if scene.backdrop == 'sky':
            # Appearance only: a gradient where MuJoCo would otherwise leave black.
            spec.add_texture(name='backdrop_sky', type=mj.mjtTexture.mjTEXTURE_SKYBOX,
                             builtin=mj.mjtBuiltin.mjBUILTIN_GRADIENT, rgb1=(.52, .60, .66),
                             rgb2=(.10, .12, .14), width=256, height=1536)
        spec.option.timestep = timestep
        spec.option.gravity = (0, 0, -9.81)
        spec.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
        # MuJoCo's soft friction lets a contact creep below its friction limit: a 16 g
        # cube squeezed at 12 N slid out of the kit gripper at 2 mm/s. The noslip pass
        # removes that creep and leaves real sliding alone (ADR 0017).
        spec.option.noslip_iterations = NOSLIP_ITERATIONS
        if not MULTICCD:
            spec.option.disableflags |= int(mj.mjtDisableBit.mjDSBL_MULTICCD)
        spec.worldbody.add_light(pos=(0, 0, 4), dir=(0, 0, -1), diffuse=(.8, .8, .8))
        if scene.backdrop == 'sky':
            # An open field is larger than the room light's cone: add a low sun as well.
            spec.worldbody.add_light(pos=(0, 0, 6), dir=(-.35, .25, -1), diffuse=(.55, .55, .52),
                                     specular=(.1, .1, .1), type=mj.mjtLightType.mjLIGHT_DIRECTIONAL, castshadow=False)
        body_names, motor_names, camera_names = [], [], []
        geom_surfaces = {}  # native geom name -> sourced surface ID
        spec_joints = {}  # native joint name -> MjSpec joint, for gearbox friction
        geared = []  # native joints carrying a gearmotor's sourced friction
        profiles={}
        robots=[]
        hands=[]    # (a held robot's hand actuator, how fast its control may change) - held()
        robot_jaws=[]   # an imported gripper's two jaw links, by their names here (ADR 0047)
        servo_names={}
        servo_units={}
        servo_grips={}
        for entity in scene.entities:
            bp = entity.blueprint
            bp.validate()
            prefix = entity.id + "/"
            materials = {m.id: m for m in bp.materials}
            for material in bp.materials:
                if material.texture is not None and material.texture not in TEXTURES:
                    raise ValueError(f"Unsupported texture asset: {material.texture}")
                appearance=spec.add_material(name=prefix+material.id, rgba=material.rgba,
                    specular=.1+.65*(1-material.roughness),
                    shininess=.1+.8*(1-material.roughness),
                    texuniform=material.texture=='concrete',
                    texrepeat=(3,2) if material.texture=='wood_floor' else (.5,.5) if material.texture=='concrete' else (1,1))
                if material.texture:
                    appearance.textures[mj.mjtTextureRole.mjTEXROLE_RGB]=material.texture
            bodies = {b.id: b for b in bp.components if isinstance(b, Body)}
            native = {}

            def free(name):
                """Whether a body moves with something on a free joint: a robot on a cart."""
                while name is not None:
                    if bodies[name].dynamic:
                        return True
                    name = bodies[name].parent
                return False

            def add_body(name):
                if name in native:
                    return native[name]
                b = bodies[name]
                parent = spec.worldbody if b.parent is None else add_body(b.parent)
                pos, quat = b.transform.position, b.transform.quaternion
                if b.parent is None:
                    pos, quat = np.zeros(3), np.zeros(4)
                    mj.mju_mulPose(pos, quat, np.array(entity.transform.position),
                                   np.array(entity.transform.quaternion),
                                   np.array(b.transform.position), np.array(b.transform.quaternion))
                nb = parent.add_body(name=prefix + name, pos=pos, quat=quat)
                native[name] = nb
                body_names.append(prefix + name)
                if b.dynamic:
                    nb.add_freejoint(name=prefix + name + "_free")
                if b.robot_asset:
                    from little_world.assets.robot_models import model_path,metadata
                    meta=metadata(b.robot_asset)
                    child=mj.MjSpec.from_file(str(model_path(b.robot_asset)))
                    for key in list(child.keys):child.delete(key)
                    hand=held(child,b.robot_asset,free(name))
                    # Invisible bounds proxy exists only for editor selection/highlight.
                    nb.add_geom(name=prefix+name+'_geom',type=mj.mjtGeom.mjGEOM_BOX,
                                size=tuple(v/2 for v in b.geometry.size),rgba=(0,0,0,0),
                                contype=0,conaffinity=0,mass=0,group=5)
                    native_prefix=prefix+name+'__robot_'
                    if hand and hand[1]:hands.append((native_prefix+hand[0],hand[1]))
                    for i,g in enumerate(child.geoms):
                        g.name='geom_'+str(i)
                        # Keep detailed appearance; hide collision-only hulls.
                        if g.group==3:g.rgba=(0,0,0,0)
                    # MuJoCo filters contacts between a body and its parent, except when the
                    # parent is welded to the world - which a robot's base is here. The
                    # Kinova Gen3's shoulder then touched its base 12 mm deep at every pose
                    # and its first joint ground against that contact at its 105 N m limit.
                    # Adjacent links of a registered model never collide (ADR 0017).
                    adjacent=[]
                    def links(body):
                        for c in body.bodies:
                            adjacent.append((body.name,c.name));links(c)
                    links(child.body(meta.get('root','link0')))
                    frame=nb.add_frame(pos=tuple(-x for x in meta['center']))
                    frame.attach_body(child.body(meta.get('root','link0')),prefix=native_prefix)
                    for a,c in adjacent:
                        spec.add_exclude(bodyname1=native_prefix+a,bodyname2=native_prefix+c)
                    # An imported robot's links that already touch at its home pose (ADR 0044).
                    for a,c in meta.get('exclude',()):
                        spec.add_exclude(bodyname1=native_prefix+a,bodyname2=native_prefix+c)
                    robots.append((name,native_prefix,meta))
                    from little_world.assets.robot_models import jaws
                    if jaws(b.robot_asset):robot_jaws.append(tuple(native_prefix+j for j in jaws(b.robot_asset)))
                    camera_names.extend(c.name for c in child.cameras)
                    return nb
                shape, size = b.geometry.shape, b.geometry.size
                if shape == "box":
                    kind, dims = mj.mjtGeom.mjGEOM_BOX, tuple(x / 2 for x in size)
                elif shape == "cylinder":
                    kind, dims = mj.mjtGeom.mjGEOM_CYLINDER, (size[0], size[1] / 2, 0)
                elif shape == "capsule":
                    kind, dims = mj.mjtGeom.mjGEOM_CAPSULE, (size[0], size[1] / 2, 0)
                else:
                    kind, dims = mj.mjtGeom.mjGEOM_SPHERE, (size[0], 0, 0)
                mat = materials[b.material]
                surface = surface_of(mat)
                if surface is not None:
                    geom_surfaces[prefix + name + "_geom"] = contact_pairs.validate_surface(surface)
                nb.add_geom(name=prefix + name + "_geom", type=kind, size=dims,
                            density=mat.density, friction=(mat.sliding_friction, .005, .0001),
                            rgba=mat.rgba, material=prefix+mat.id, condim=4)
                return nb

            for name in bodies:
                add_body(name)
            for c in bp.components:
                if isinstance(c, Hinge):
                    spec_joints[prefix + c.id] = native[c.body].add_joint(
                        name=prefix + c.id, type=mj.mjtJoint.mjJNT_HINGE,
                        axis=c.axis, pos=c.position, damping=c.damping,
                        limited=c.limits is not None, range=c.limits or (0., 0.))
                elif isinstance(c, Camera):
                    native[c.body].add_camera(name=prefix + c.id, pos=c.transform.position,
                                              quat=c.transform.quaternion, fovy=c.fovy)
                    camera_names.append(prefix + c.id)
                elif isinstance(c, RobotServo):
                    from little_world.assets.robot_models import metadata, units
                    asset=bodies[c.body].robot_asset
                    if c.channel>=len(metadata(asset)['actuators']):
                        raise ValueError(f"{c.id}: the robot {asset} has no servo channel {c.channel}")
                    native_name=prefix+c.body+'__robot_'+metadata(asset)['actuators'][c.channel]
                    servo_names[prefix+c.id]=(native_name,c.channel)
                    servo_units[prefix+c.id]=units(asset)[c.channel]
                    if servo_units[prefix+c.id]=='%':
                        from little_world.assets.robot_models import grip
                        servo_grips[prefix+c.id]=grip(asset,c.channel)
                elif isinstance(c, Motor):
                    # A motor's affine bias is zero unless a step gives it a slope: the
                    # sourced speed-torque line where it binds (ADR 0011), or the
                    # controller's own damping (ADR 0014). The integrator then lets the
                    # torque follow the joint's speed within the step, implicitly.
                    spec.add_actuator(name=prefix + c.id, target=prefix + c.joint,
                                      trntype=mj.mjtTrn.mjTRN_JOINT, gear=(1, 0, 0, 0, 0, 0),
                                      ctrllimited=True, ctrlrange=(-c.max_torque, c.max_torque),
                                      gainprm=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                                      biastype=mj.mjtBias.mjBIAS_AFFINE)
                    motor_names.append(prefix + c.id)
                    if c.profile is not None:profiles[prefix+c.id]=c.profile
            # A sourced gearmotor's own friction (brushes, bearings, gears), referred to
            # its output shaft from the datasheet's no-load current (ADR 0011). It is there
            # whether or not the motor is powered: back-driving a gearbox costs torque.
            for c in bp.components:
                if isinstance(c, Motor) and c.profile is not None and c.profile.friction_torque:
                    spec_joints[prefix + c.joint].frictionloss += c.profile.friction_torque
                    geared.append(prefix + c.joint)
        # Build before replacing a working runtime: failed compile is transactional.
        model = spec.compile()
        data = mj.MjData(model)
        for _,native_prefix,meta in robots:
            for name,value in zip(meta['joints'],meta['home']):
                data.qpos[model.jnt_qposadr[model.joint(native_prefix+name).id]]=value
            for name,value in zip(meta['actuators'],meta['ctrl']):
                data.ctrl[model.actuator(native_prefix+name).id]=value
        surfaces = sorted(contact_pairs.SURFACES)
        index = {name: i for i, name in enumerate(surfaces)}
        geom_surface = np.full(model.ngeom, len(surfaces), dtype=np.intp)
        for name, surface in geom_surfaces.items():
            geom_surface[model.geom(name).id] = index[surface]
        pair_mu = np.full((len(surfaces) + 1,) * 2, np.nan)
        for (a, b), pair in contact_pairs.PAIRS.items():
            pair_mu[index[a], index[b]] = pair_mu[index[b], index[a]] = pair.kinetic
        energy_sensor = bool(np.isin(model.sensor_type, (mj.mjtSensor.mjSENS_E_POTENTIAL,)).any())
        # Local tables until the swap below, so a failure here leaves the old runtime whole.
        geared_dofs = [int(model.jnt_dofadr[model.joint(name).id]) for name in geared]
        if geared_dofs:
            model.dof_solref[geared_dofs] = dry_friction_solref(timestep)
            model.dof_solimp[geared_dofs] = DRY_FRICTION_SOLIMP
        staged_forward(model, data, lambda m, d: apply_pair_friction(d, geom_surface, pair_mu),
                       energy_sensor)
        # Wheels carry no rolling loss yet, so their friction settings could not have
        # mattered to the forward pass above.
        roll = _rolling_tables(model, data, geom_surfaces)
        if roll is not None:
            model.dof_solref[roll["dofs"]] = dry_friction_solref(timestep)
            model.dof_solimp[roll["dofs"]] = DRY_FRICTION_SOLIMP
        self.close()
        self._geom_surface, self._pair_mu, self._energy_sensor = geom_surface, pair_mu, energy_sensor
        self._any_sourced = bool(geom_surfaces)
        self._base_frictionloss = model.dof_frictionloss.copy()
        self._roll = roll
        self.model, self.data = model, data
        self._name_list = self._speeds_before = None
        self._body_ids = {n: model.body(n).id for n in body_names}
        self._motor_ids = {n: model.actuator(n).id for n in motor_names}
        self._camera_ids = {n: model.camera(n).id for n in camera_names}
        self.servo_info={}
        self.servo_joint_names={}
        # What each robot servo is driven in: 'deg', 'mm' or '%' (robot_models.units); for a
        # gripper's, how its closure maps to its control and its joint (robot_models.grip).
        self.servo_units=dict(servo_units)
        self.servo_grips=dict(servo_grips)
        self.robot_jaws=tuple(robot_jaws)
        for name,(native_name,channel) in servo_names.items():
            idx=model.actuator(native_name).id
            self._motor_ids[name]=idx
            self.servo_info[name]=(idx,channel)
            native_prefix=native_name.rsplit('__robot_',1)[0]+'__robot_'
            meta=next(meta for _,p,meta in robots if p==native_prefix)
            self.servo_joint_names[name]=native_prefix+meta.get('servo_joints',meta['joints'])[channel]
        self._initial_qpos=data.qpos.copy()
        self._initial_ctrl=data.ctrl.copy()
        self._servo_ids=[idx for idx,_ in self.servo_info.values()]
        # A held robot's hand moves its fingers at its datasheet's speed: its control follows the
        # command no faster (OPEN LW-036). The command is kept until the next one.
        self._hand_rates={model.actuator(n).id:rate for n,rate in hands}
        self._hand_goals={}
        self.robot_owners={}
        for name,native_prefix,_ in robots:
            for i in range(1,model.nbody):
                if model.body(i).name.startswith(native_prefix):
                    self.robot_owners[model.body(i).name]=native_prefix.split(name+'__robot_')[0]+name
        self._motor_profiles={};self._motor_original={};self._mass_original={}
        for n,p in profiles.items():
            dof=int(model.jnt_dofadr[model.actuator_trnid[self._motor_ids[n],0]])
            # The most one step of this motor alone can add to its joint's speed, per
            # N m: timestep / inertia, with MuJoCo's inertia estimate at the design pose.
            self._motor_profiles[self._motor_ids[n]]=(p,dof,float(model.opt.timestep*model.dof_invweight0[dof]))
        # Every kit motor's joint speed, for the slope its command may carry.
        self._motor_dofs={self._motor_ids[n]:int(model.jnt_dofadr[model.actuator_trnid[self._motor_ids[n],0]])
                          for n in motor_names}
        self._affine=np.array(sorted(self._motor_dofs),dtype=np.intp)

    def _ready(self):
        if self.model is None:
            raise RuntimeError("backend is not compiled")

    def _contact_policy(self, m, d):
        """Sourced pair friction, written into each new contact before the solver sees it.

        MuJoCo gives a contact the larger of its two geoms' coefficients. Here any
        contact between two surfaces with a sourced pair (materials/contact_pairs.py)
        gets that pair's kinetic coefficient in both tangent directions instead.
        Contacts without a sourced pair are left exactly as MuJoCo made them.
        """
        if self._any_sourced:
            apply_pair_friction(d, self._geom_surface, self._pair_mu)

    def vary_pair_friction(self, table=None):
        """Run on other pair frictions than the sourced ones, from the next step on: `table`
        maps sourced surface pairs, such as ('concrete', 'rubber'), to the kinetic
        coefficient to use. A condition of the run, as a damp floor would be, not part of
        the design (ADR 0024). None restores the sourced values; so does a new compile."""
        self._ready()
        surfaces = sorted(contact_pairs.SURFACES)
        index = {name: i for i, name in enumerate(surfaces)}
        mu = np.full((len(surfaces) + 1,) * 2, np.nan)
        for (a, b), pair in contact_pairs.PAIRS.items():
            mu[index[a], index[b]] = mu[index[b], index[a]] = pair.kinetic
        for (a, b), value in (table or {}).items():
            if contact_pairs.lookup(a, b) is None:
                raise ValueError(f"no sourced pair {a}/{b} to vary")
            if not isfinite(value) or not 0. < value <= 2.:
                raise ValueError("a friction coefficient must be finite, above 0 and at most 2")
            mu[index[a], index[b]] = mu[index[b], index[a]] = value
        self._pair_mu = mu

    def scale_mass(self, body, factor):
        """Make `body` `factor` times as heavy as designed - its mass and its inertia alike, as
        if its material were that much denser - from now on: a condition of the run, as a payload
        is (FR-036). The model's constants that follow from its masses are recomputed and the
        world's state is kept; a reset world's body is as designed again."""
        self._ready()
        if body not in self._body_ids:
            raise ValueError(f'no body called {body!r}')
        if not isfinite(factor) or factor <= 0:
            raise ValueError('a body is made heavier or lighter by a finite factor above 0')
        m, d = self.model, self.data
        idx = self._body_ids[body]
        mass, inertia = self._mass_original.setdefault(idx, (float(m.body_mass[idx]), m.body_inertia[idx].copy()))
        m.body_mass[idx] = mass * factor
        m.body_inertia[idx] = inertia * factor
        kept = (d.time, d.qpos.copy(), d.qvel.copy(), d.act.copy(), d.ctrl.copy())
        mj.mj_setConst(m, d)              # subtree masses, the weights contacts are softened by
        d.time = kept[0]
        d.qpos[:], d.qvel[:], d.act[:], d.ctrl[:] = kept[1:]
        mj.mj_forward(m, d)

    def contact_report(self):
        """Current contacts: (geom, geom, coefficient in use, sourced pair or None)."""
        self._ready()
        surfaces = sorted(contact_pairs.SURFACES)
        out = []
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            a, b = (int(self._geom_surface[g]) for g in (c.geom1, c.geom2))
            pair = (contact_pairs.lookup(surfaces[a], surfaces[b])
                    if a < len(surfaces) and b < len(surfaces) else None)
            out.append((self.model.geom(c.geom1).name, self.model.geom(c.geom2).name,
                        float(c.friction[0]), pair))
        return out

    def contact_forces(self, body):
        """The forces on a body from everything touching it now: one (other body's name, force)
        per contact, the force (x, y, z) newtons in the world, as the solver found it this step
        (ADR 0040). MuJoCo gives a contact's force on its second geom, along the frame whose
        first axis points from the first geom to the second; on the first it is the opposite."""
        self._ready()
        if body not in self._body_ids:
            raise ValueError(f'no body called {body!r}')
        m, d = self.model, self.data
        idx = self._body_ids[body]
        if not d.ncon:
            return ()
        owners = m.geom_bodyid[d.contact.geom[:d.ncon]]
        out, force = [], np.zeros(6)
        for i in np.nonzero((owners == idx).any(axis=1))[0]:
            mj.mj_contactForce(m, d, int(i), force)
            on_second = d.contact.frame[i].reshape(3, 3).T @ force[:3]
            first, second = owners[i]
            other, sign = (first, 1.) if second == idx else (second, -1.)
            out.append((m.body(int(other)).name, tuple(float(v) for v in sign * on_second)))
        return tuple(out)

    def friction_use(self, body):
        """How near each of `body`'s contacts is to sliding (FR-036): one (other body's name,
        normal force N, friction used N) per contact now. The friction used is what the contact's
        cone measures - each frictional force (two along the surface, a torsional one where the
        contact has it) over its own coefficient, summed for the pyramidal cones the scenes use
        and taken as a length for elliptic ones - so it reaches the normal force exactly when the
        contact is at its cone's edge and may slide: its friction use, used / normal, is 0 to 1."""
        self._ready()
        if body not in self._body_ids:
            raise ValueError(f'no body called {body!r}')
        m, d = self.model, self.data
        idx = self._body_ids[body]
        if not d.ncon:
            return ()
        owners = m.geom_bodyid[d.contact.geom[:d.ncon]]
        elliptic = m.opt.cone == mj.mjtCone.mjCONE_ELLIPTIC
        out, force = [], np.zeros(6)
        for i in np.nonzero((owners == idx).any(axis=1))[0]:
            contact = d.contact[int(i)]
            dim = int(contact.dim)
            if dim < 3:
                continue                    # frictionless: nothing to slide against
            mj.mj_contactForce(m, d, int(i), force)
            parts = [abs(float(force[k])) / float(contact.friction[k - 1]) for k in range(1, dim)
                     if contact.friction[k - 1] > 0]
            used = sqrt(sum(p * p for p in parts)) if elliptic else sum(parts)
            first, second = owners[i]
            other = first if second == idx else second
            out.append((m.body(int(other)).name, max(0., float(force[0])), used))
        return tuple(out)

    def contact_census(self, bodies=()):
        """At this instant, each pair of bodies in contact - only those with a body in `bodies`,
        when given - with the kinds of shape that touch, how many contact points MuJoCo finds
        between them as this model is set (multiccd off, ADR 0027), and how many it finds with
        its multiple-contact search on: {(a, b): (kinds, points, with_multiccd)}, a and b in
        name order, kinds such as 'box-box' (FR-030). Both counts are made on copies of this
        instant, so the run goes on untouched."""
        self._ready()
        m, d = self.model, self.data
        wanted = set(bodies)

        def count(multiccd):
            copy = mj.MjData(m)
            copy.time = d.time
            copy.qpos[:], copy.qvel[:] = d.qpos, d.qvel
            if m.na:
                copy.act[:] = d.act
            if m.nmocap:
                copy.mocap_pos[:], copy.mocap_quat[:] = d.mocap_pos, d.mocap_quat
            flags = m.opt.disableflags
            off = int(mj.mjtDisableBit.mjDSBL_MULTICCD)
            try:
                m.opt.disableflags = (flags & ~off) if multiccd else flags
                mj.mj_fwdPosition(m, copy)
            finally:
                m.opt.disableflags = flags
            pairs = {}
            for c in copy.contact[:copy.ncon]:
                (a, ka), (b, kb) = sorted((m.body(int(m.geom_bodyid[g])).name, SHAPES[int(m.geom_type[g])])
                                          for g in (c.geom1, c.geom2))
                if wanted and a not in wanted and b not in wanted:
                    continue
                kinds, n = pairs.get((a, b), (frozenset(), 0))
                pairs[(a, b)] = (kinds | {f'{ka}-{kb}'}, n + 1)
            return pairs
        now, multi = count(False), count(True)
        return {pair: (tuple(sorted(kinds)), n, multi.get(pair, ((), 0))[1])
                for pair, (kinds, n) in sorted(now.items())}

    def contact_work(self):
        """The work the contacts between each pair of touching bodies did on them in the last step
        (FR-040): ((body, body, joules, deepest, metres), ...), one row a pair. A contact is a spring
        and a damper: it pushes two bodies apart as they press into each other, and while they touch
        the work it does on them is what it gives back less what it took - never more than nothing,
        unless the engine made energy. Each contact's forces as the solver found them, times how
        fast its two points moved apart along them over the step - the speeds the step left, which
        are the speeds it moved the bodies at - so it only reads the step and changes nothing.
        The speeds are the step's mean - the semi-implicit step moves a body by its new speed, and
        a force times that overstates its work by F^2 dt^2 / 2m a step: 6.3 of the 40 mJ a 81 g block
        dropped 5 cm gives a slab. With the mean, the work is what the bodies' energies show.
        `deepest` is how far the pair's deepest contact point sinks in, 0 at a touch."""
        self._ready()
        m, d = self.model, self.data
        ncon, nefc = d.ncon, d.nefc
        if not ncon or not nefc:
            return ()
        rows = np.nonzero(np.isin(d.efc_type[:nefc], _CONTACT_ROWS))[0]
        speeds = d.qvel if self._speeds_before is None or len(self._speeds_before) != m.nv else (self._speeds_before + d.qvel) / 2
        apart = np.zeros(nefc)
        mj.mj_mulJacVec(m, d, apart, speeds)
        power = np.bincount(d.efc_id[rows], weights=d.efc_force[rows] * apart[rows], minlength=ncon)[:ncon]
        active = d.contact.efc_address[:ncon] >= 0
        if not active.any():
            return ()
        pairs = np.sort(m.geom_bodyid[d.contact.geom[:ncon]], axis=1)[active]
        keys, which = np.unique(pairs[:, 0] * m.nbody + pairs[:, 1], return_inverse=True)
        joules = np.bincount(which, weights=power[active] * m.opt.timestep, minlength=len(keys))
        deepest = np.zeros(len(keys))
        np.maximum.at(deepest, which, -d.contact.dist[:ncon][active])
        names = self._names()
        return tuple((names[k // m.nbody], names[k % m.nbody], float(w), float(z))
                     for k, w, z in zip(keys.tolist(), joules.tolist(), deepest.tolist()))

    def _names(self):
        if self._name_list is None:
            self._name_list = [self.model.body(i).name for i in range(self.model.nbody)]
        return self._name_list

    def moving_mass(self, body):
        """How much a push on `body` sets moving, kg: the bodies from its highest ancestor that can
        move down - all of a cart from one of its wheels, a hinged roller alone - or None when it is
        fixed to the world (FR-040)."""
        self._ready()
        m = self.model
        idx = m.body(body).id
        if idx == 0 or m.body_weldid[idx] == 0:
            return None
        top = idx
        while m.body_parentid[top] and m.body_weldid[m.body_parentid[top]] != 0:
            top = int(m.body_parentid[top])
        return float(m.body_subtreemass[top])

    def step(self, commands):
        self._ready()
        unknown = commands.keys() - self._motor_ids.keys()
        if unknown:
            raise ValueError(f"unknown actuators: {sorted(unknown)}")
        controls = np.zeros(self.model.nu)
        bias = np.zeros((self.model.nu, 2))
        controls[self._servo_ids]=self.data.ctrl[self._servo_ids]
        for name, value in commands.items():
            if not isfinite(value):
                raise ValueError("actuator command must be finite")
            idx = self._motor_ids[name]
            low, high = self.model.actuator_ctrlrange[idx]
            if self.model.actuator_ctrllimited[idx] and not low <= value <= high:
                raise ValueError(f"{name} command outside [{low}, {high}]")
            slope = slope_of(value)   # the controller's own damping, ADR 0014
            if slope and idx not in self._motor_dofs:
                raise ValueError(f"{name} is a model's position servo: its command has no torque slope")
            if idx in self._motor_profiles:
                profile,dof,per_newton_metre=self._motor_profiles[idx]
                velocity=float(self.data.qvel[dof])
                line=profile.slope(value,velocity,high,reach=abs(high)*per_newton_metre)
                limited=profile.constrain(value,velocity,high)
                # Where the line limits the torque it is what the torque follows; a
                # command the line cut short no longer follows the controller either.
                slope=line if line else slope if limited==value else 0.
                value=limited
            if slope:
                # Force = value + slope * (v - velocity): exactly `value` at the speed
                # the command was computed for, and the slope for the implicit step.
                bias[idx]=-slope*float(self.data.qvel[self._motor_dofs[idx]]),slope
            controls[idx] = value
            if idx in self._hand_rates:
                self._hand_goals[idx] = value
        for idx, goal in self._hand_goals.items():
            now, most = float(self.data.ctrl[idx]), self._hand_rates[idx] * float(self.model.opt.timestep)
            controls[idx] = min(now + most, max(now - most, goal))
        self.data.ctrl[:] = controls
        if self._affine.size:
            self.model.actuator_biasprm[self._affine,0]=bias[self._affine,0]
            self.model.actuator_biasprm[self._affine,2]=bias[self._affine,1]
        self._speeds_before = self.data.qvel.copy()     # the step's work is read at its mean speeds (FR-040)
        staged_step(self.model, self.data, self._contact_policy, self._energy_sensor)
        if self._roll is not None:
            apply_rolling_resistance(self.model, self.data, self._roll, self._base_frictionloss)
        # Refresh the observed and rendered kinematics at post-integration time.
        # The next mj_step performs collision/dynamics itself; running a second
        # full constraint solve here doubled that work without advancing time.
        mj.mj_kinematics(self.model, self.data)
        mj.mj_comPos(self.model, self.data)
        mj.mj_camlight(self.model, self.data)
        mj.mj_comVel(self.model, self.data)
        return self.snapshot()

    def weaken(self, motor, torque=1., speed=1.):
        """From now on the motor called `motor` follows its speed-torque line scaled by these
        factors (`MotorProfile.weakened`): a winding grown hot, a sagging supply (ADR 0058). Only
        a motor with a sourced profile has a line to scale; any other fails, as does a name
        that is not a motor's."""
        self._ready()
        if motor not in self._motor_ids:
            raise ValueError(f'no motor called {motor!r}')
        idx = self._motor_ids[motor]
        if idx not in self._motor_profiles:
            raise ValueError(f'{motor} has no sourced profile to weaken')
        profile, dof, per_newton_metre = self._motor_profiles[idx]
        original = self._motor_original.setdefault(idx, profile)
        self._motor_profiles[idx] = (original.weakened(torque, speed), dof, per_newton_metre)

    def motor_line(self, actuator):
        """(the profile the motor at actuator index `actuator` follows now, the one it was
        compiled with) - the same twice unless it has been weakened (ADR 0058) - or None for a
        motor without a sourced profile: what a window says of it."""
        if self.model is None or actuator not in self._motor_profiles:
            return None
        now = self._motor_profiles[actuator][0]
        return now, self._motor_original.get(actuator, now)

    def push(self, body, force=(0., 0., 0.)):
        """Hold a force on a body's centre of mass, world frame, newtons, until pushed again
        (a zero force ends it): how a test field shoves a machine partway through a run (ADR
        0030). The solver integrates it like gravity; nothing else is touched."""
        self._ready()
        if body not in self._body_ids:
            raise ValueError(f'no body called {body!r}')
        force = tuple(float(f) for f in force)
        if len(force) != 3 or not all(isfinite(f) for f in force):
            raise ValueError('a push is three finite newtons')
        idx = self._body_ids[body]
        self.data.xfrc_applied[idx, :3] = force
        self.data.xfrc_applied[idx, 3:] = 0.

    def shift(self, body, offset, turn=0.):
        """Move a loose body - one on a free joint, such as a field's cube - by (dx, dy) metres
        in plan, turned `turn` degrees about the vertical through its centre, and leave it at
        rest: a part someone moved while the machine was busy (ADR 0030, 0032). A body that is
        not loose cannot be moved this way."""
        self._ready()
        if body not in self._body_ids:
            raise ValueError(f'no body called {body!r}')
        idx = self._body_ids[body]
        joint = self.model.body_jntadr[idx]
        if joint < 0 or self.model.jnt_type[joint] != mj.mjtJoint.mjJNT_FREE:
            raise ValueError(f'{body} is not loose: only a body on a free joint can be moved')
        dx, dy = (float(v) for v in offset)
        if not (isfinite(dx) and isfinite(dy) and isfinite(turn)):
            raise ValueError('an offset is two finite metres, a turn finite degrees')
        at, dof = self.model.jnt_qposadr[joint], self.model.jnt_dofadr[joint]
        self.data.qpos[at] += dx
        self.data.qpos[at + 1] += dy
        if turn:
            spin = np.array((np.cos(np.radians(turn) / 2), 0., 0., np.sin(np.radians(turn) / 2)))
            turned = np.zeros(4)
            mj.mju_mulQuat(turned, spin, self.data.qpos[at + 3:at + 7].copy())
            self.data.qpos[at + 3:at + 7] = turned
        self.data.qvel[dof:dof + 6] = 0.
        mj.mj_kinematics(self.model, self.data)
        mj.mj_comPos(self.model, self.data)
        mj.mj_camlight(self.model, self.data)
        mj.mj_comVel(self.model, self.data)

    def snapshot(self):
        self._ready()
        # Batch-detach poses before lazily constructing public BodyState objects.
        # Detailed hardware has hundreds of welded subparts: consumers usually
        # need only a few observations per frame, while native physics sees all.
        positions = self.data.xpos.tolist()
        quaternions = self.data.xquat.tolist()
        # mj_objectVelocity(mjOBJ_BODY, world orientation), batched. MuJoCo's
        # cvel is centred at the kinematic root's subtree COM; translate each
        # linear velocity to its own inertial origin, preserving the public API.
        angular = self.data.cvel[:, :3]
        offset = self.data.xipos - self.data.subtree_com[self.model.body_rootid]
        linear = self.data.cvel[:, 3:] + np.cross(angular, offset)
        angular_values = angular.tolist()
        linear_values = linear.tolist()
        welded = self.model.body_weldid
        records = {}
        for name, idx in self._body_ids.items():
            if name in self._static_states:
                records[name] = self._static_states[name]
                continue
            records[name] = (positions[idx], quaternions[idx], linear_values[idx], angular_values[idx])
            if welded[idx] == 0:
                records[name] = (positions[idx], quaternions[idx], (0.,0.,0.), (0.,0.,0.))
                state = BodyState(Transform(positions[idx], quaternions[idx]), records[name][2], records[name][3])
                self._static_states[name] = records[name] = state
        return State(float(self.data.time), DeferredBodyStates(records))

    def reset(self):
        self._ready()
        self._speeds_before = None
        mj.mj_resetData(self.model, self.data)
        self.data.qpos[:]=self._initial_qpos
        self.data.ctrl[:]=self._initial_ctrl
        self._hand_goals = {}
        self.model.dof_frictionloss[:] = self._base_frictionloss
        self.model.actuator_biasprm[self._affine] = 0.
        for idx, profile in self._motor_original.items():     # a weakened motor is itself again
            self._motor_profiles[idx] = (profile, *self._motor_profiles[idx][1:])
        self._motor_original = {}
        if self._mass_original:                                # a heavier body is as designed again
            for idx, (mass, inertia) in self._mass_original.items():
                self.model.body_mass[idx], self.model.body_inertia[idx] = mass, inertia
            self._mass_original = {}
            mj.mj_setConst(self.model, self.data)
            mj.mj_resetData(self.model, self.data)
            self.data.qpos[:]=self._initial_qpos
            self.data.ctrl[:]=self._initial_ctrl
        staged_forward(self.model, self.data, self._contact_policy, self._energy_sensor)
        return self.snapshot()

    def camera_pose(self, camera):
        """(position, rotation) of a camera now: its centre in the world, and its axes as the
        columns of a 3 x 3 matrix - x right, y up, looking along -z (ADR 0032)."""
        self._ready()
        if camera not in self._camera_ids:
            raise ValueError(f"unknown camera: {camera}")
        i = self._camera_ids[camera]
        d = self.sight
        return d.cam_xpos[i].copy(), d.cam_xmat[i].reshape(3, 3).copy()

    @property
    def sight(self):
        """The MjData the cameras see: the world now, or - inside `as_it_was` - a moment kept."""
        return self._seen if self._seen is not None else self.data

    def kept(self):
        """This moment, kept for a camera to see later (FR-028): its time, the joints' positions
        and the mocap bodies' poses - all that places what a camera sees."""
        self._ready()
        d = self.data
        return (float(d.time), d.qpos.copy(), d.mocap_pos.copy(), d.mocap_quat.copy())

    def as_it_was(self, moment):
        """Within it, the cameras - `camera_pose`, `cast` - see the world as it was at a moment
        `kept` earlier, laid out on an MjData of their own; the world itself is untouched."""
        from contextlib import contextmanager

        @contextmanager
        def seeing():
            self._ready()
            if self._past is None:
                self._past = mj.MjData(self.model)
            past = self._past
            past.time, past.qpos[:] = moment[0], moment[1]
            if self.model.nmocap:
                past.mocap_pos[:], past.mocap_quat[:] = moment[2], moment[3]
            mj.mj_kinematics(self.model, past)
            mj.mj_camlight(self.model, past)
            self._seen = past
            try:
                yield past
            finally:
                self._seen = None
        return seeing()

    def move_camera(self, camera, shift=(0., 0., 0.), turn=(0., 0., 0.)):
        """Set a camera off the pose it was built at: `shift` metres along the world's axes,
        then turned `turn` degrees about its own axes - pan about its up axis, tilt about its
        right axis, roll about its view - as a stand set up by hand, or bumped, puts it (ADR
        0039). Only the camera moves; what a program believes of its pose is the program's."""
        self._ready()
        if camera not in self._camera_ids:
            raise ValueError(f"unknown camera: {camera}")
        shift, turn = np.asarray(shift, dtype=float), np.asarray(turn, dtype=float)
        if shift.shape != (3,) or turn.shape != (3,) or not (np.isfinite(shift).all() and np.isfinite(turn).all()):
            raise ValueError('a camera is shifted by three finite metres and turned by three finite degrees')
        i = self._camera_ids[camera]
        body = self.model.cam_bodyid[i]
        self.model.cam_pos[i] += self.data.xmat[body].reshape(3, 3).T @ shift
        pan, tilt, roll = np.radians(turn) / 2
        quat = self.model.cam_quat[i].copy()
        for axis, half in ((1, pan), (0, tilt), (2, roll)):     # about y (up), then x (right), then z
            q = np.zeros(4)
            q[0], q[1 + axis] = np.cos(half), np.sin(half)
            out = np.zeros(4)
            mj.mju_mulQuat(out, quat, q)
            quat = out
        self.model.cam_quat[i] = quat / np.linalg.norm(quat)
        mj.mj_camlight(self.model, self.data)

    def cast(self, camera, directions, cutoff=10.):
        """Rays from a camera to the first visible surface (ADR 0032): `directions` (n x 3)
        in the camera's frame. Returns how far along each direction the surface is - the hit
        is at the camera plus that times the direction, so a direction scaled to z = -1
        gives depth along the camera's axis - and NaN where nothing is met; geoms further
        than `cutoff` metres are passed over. Visible geoms only (groups 0 to 2), not the
        camera's own body: what a camera there would see, from MuJoCo's own ray casting,
        without a GL context."""
        position, rotation = self.camera_pose(camera)
        local = np.asarray(directions, dtype=float).reshape(-1, 3)
        if not np.isfinite(local).all() or not np.isfinite(cutoff) or cutoff <= 0:
            raise ValueError("rays need finite directions and a positive cutoff")
        world = np.ascontiguousarray(local @ rotation.T)
        n = len(world)
        geoms, found = np.zeros(n, np.int32), np.zeros(n)
        if n:
            mj.mj_multiRay(self.model, self.sight, position, world.reshape(-1), np.array((1, 1, 1, 0, 0, 0), np.uint8),
                           1, int(self.model.cam_bodyid[self._camera_ids[camera]]), geoms, found, None, n, float(cutoff))
        return np.where(found >= 0, found, np.nan)

    def capture(self, camera, width=320, height=240):
        """Return a detached RGB uint8 array; creates GL resources only on demand."""
        self._ready()
        if camera not in self._camera_ids:
            raise ValueError(f"unknown camera: {camera}")
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise ValueError("image dimensions must be positive integers")
        if self._renderer is not None and (self._renderer.width, self._renderer.height) != (width, height):
            self._renderer.close()
            self._renderer = None
        if self._renderer is None:
            self.model.vis.global_.offwidth = max(width, self.model.vis.global_.offwidth)
            self.model.vis.global_.offheight = max(height, self.model.vis.global_.offheight)
            self._renderer = mj.Renderer(self.model, height=height, width=width)
        self._renderer.update_scene(self.data, camera=camera)
        return self._renderer.render().copy()

    def close(self):
        if self._preview_context is not None:
            self._preview_context.free();self._preview_context=None
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
        self.model = self.data = None
        self._body_ids, self._motor_ids, self._camera_ids = {}, {}, {}
        self._static_states = {}
        self._motor_profiles = {}
        self._motor_original = {}   # a weakened motor's profile as compiled (ADR 0058)
        self._mass_original = {}    # a body made heavier for a run: its mass and inertia as compiled (FR-036)
        self._hand_rates = {}       # a held robot's hand: how fast its control may change (OPEN LW-036)
        self._hand_goals = {}       # and where it was last sent
        self._motor_dofs = {}
        self._affine = np.zeros(0, dtype=np.intp)
