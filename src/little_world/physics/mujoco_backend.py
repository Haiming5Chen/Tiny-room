"""All native MuJoCo construction and runtime operations live in this adapter."""
from math import isfinite
import mujoco as mj
import numpy as np
from little_world.core.component import Body, Hinge, Motor, RobotServo, Camera, Transform, positive
from little_world.core.state import State, BodyState, DeferredBodyStates
from little_world.assets.textures import TEXTURES, SIZE, texture_bytes
from little_world.materials import surface_of
from little_world.materials import contact_pairs

_IMPLICIT = (mj.mjtIntegrator.mjINT_IMPLICIT, mj.mjtIntegrator.mjINT_IMPLICITFAST)


def _fwd_position(m, d, contact_hook):
    """mj_fwdPosition in MuJoCo 3.3.7's order, with one hook between collision detection
    and constraint construction - the only point at which a contact's friction can be
    set and still reach the solver. See ADR 0010; bit-identity with mj_step is tested."""
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


class MujocoBackend:
    def __init__(self):
        self.model = self.data = None
        self._renderer = None
        self._preview_context = None
        self._body_ids = {}
        self._motor_ids = {}
        self._camera_ids = {}
        self._static_states = {}
        self._motor_profiles = {}
        self._geom_surface = None
        self._pair_mu = None
        self._any_sourced = False
        self._energy_sensor = False

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
        spec.option.timestep = timestep
        spec.option.gravity = (0, 0, -9.81)
        spec.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
        spec.worldbody.add_light(pos=(0, 0, 4), dir=(0, 0, -1), diffuse=(.8, .8, .8))
        body_names, motor_names, camera_names = [], [], []
        geom_surfaces = {}  # native geom name -> sourced surface ID
        profiles={}
        robots=[]
        servo_names={}
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
                    texuniform=False, texrepeat=(3,2) if material.texture=='wood_floor' else (1,1))
                if material.texture:
                    appearance.textures[mj.mjtTextureRole.mjTEXROLE_RGB]=material.texture
            bodies = {b.id: b for b in bp.components if isinstance(b, Body)}
            native = {}

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
                    # Invisible bounds proxy exists only for editor selection/highlight.
                    nb.add_geom(name=prefix+name+'_geom',type=mj.mjtGeom.mjGEOM_BOX,
                                size=tuple(v/2 for v in b.geometry.size),rgba=(0,0,0,0),
                                contype=0,conaffinity=0,mass=0,group=5)
                    native_prefix=prefix+name+'__robot_'
                    for i,g in enumerate(child.geoms):
                        g.name='geom_'+str(i)
                        # Keep detailed appearance; hide collision-only hulls.
                        if g.group==3:g.rgba=(0,0,0,0)
                    frame=nb.add_frame(pos=tuple(-x for x in meta['center']))
                    frame.attach_body(child.body(meta.get('root','link0')),prefix=native_prefix)
                    robots.append((name,native_prefix,meta))
                    camera_names.extend(c.name for c in child.cameras)
                    return nb
                shape, size = b.geometry.shape, b.geometry.size
                if shape == "box":
                    kind, dims = mj.mjtGeom.mjGEOM_BOX, tuple(x / 2 for x in size)
                elif shape == "cylinder":
                    kind, dims = mj.mjtGeom.mjGEOM_CYLINDER, (size[0], size[1] / 2, 0)
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
                    native[c.body].add_joint(name=prefix + c.id, type=mj.mjtJoint.mjJNT_HINGE,
                                              axis=c.axis, pos=c.position, damping=c.damping,
                                              limited=c.limits is not None, range=c.limits or (0., 0.))
                elif isinstance(c, Camera):
                    native[c.body].add_camera(name=prefix + c.id, pos=c.transform.position,
                                              quat=c.transform.quaternion, fovy=c.fovy)
                    camera_names.append(prefix + c.id)
                elif isinstance(c, RobotServo):
                    from little_world.assets.robot_models import metadata
                    native_name=prefix+c.body+'__robot_'+metadata(bodies[c.body].robot_asset)['actuators'][c.channel]
                    servo_names[prefix+c.id]=(native_name,c.channel)
                elif isinstance(c, Motor):
                    spec.add_actuator(name=prefix + c.id, target=prefix + c.joint,
                                      trntype=mj.mjtTrn.mjTRN_JOINT, gear=(1, 0, 0, 0, 0, 0),
                                      ctrllimited=True, ctrlrange=(-c.max_torque, c.max_torque),
                                      gainprm=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0))
                    motor_names.append(prefix + c.id)
                    if c.profile is not None:profiles[prefix+c.id]=c.profile
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
        staged_forward(model, data, lambda m, d: apply_pair_friction(d, geom_surface, pair_mu),
                       energy_sensor)
        self.close()
        self._geom_surface, self._pair_mu, self._energy_sensor = geom_surface, pair_mu, energy_sensor
        self._any_sourced = bool(geom_surfaces)
        self.model, self.data = model, data
        self._body_ids = {n: model.body(n).id for n in body_names}
        self._motor_ids = {n: model.actuator(n).id for n in motor_names}
        self._camera_ids = {n: model.camera(n).id for n in camera_names}
        self.servo_info={}
        self.servo_joint_names={}
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
        self.robot_owners={}
        for name,native_prefix,_ in robots:
            for i in range(1,model.nbody):
                if model.body(i).name.startswith(native_prefix):
                    self.robot_owners[model.body(i).name]=native_prefix.split(name+'__robot_')[0]+name
        self._motor_profiles={self._motor_ids[n]:(p,int(model.jnt_dofadr[model.actuator_trnid[self._motor_ids[n],0]])) for n,p in profiles.items()}

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

    def step(self, commands):
        self._ready()
        unknown = commands.keys() - self._motor_ids.keys()
        if unknown:
            raise ValueError(f"unknown actuators: {sorted(unknown)}")
        controls = np.zeros(self.model.nu)
        controls[self._servo_ids]=self.data.ctrl[self._servo_ids]
        for name, value in commands.items():
            if not isfinite(value):
                raise ValueError("actuator command must be finite")
            idx = self._motor_ids[name]
            low, high = self.model.actuator_ctrlrange[idx]
            if self.model.actuator_ctrllimited[idx] and not low <= value <= high:
                raise ValueError(f"{name} command outside [{low}, {high}]")
            if idx in self._motor_profiles:
                profile,dof=self._motor_profiles[idx]
                value=profile.constrain(value,float(self.data.qvel[dof]),high)
            controls[idx] = value
        self.data.ctrl[:] = controls
        staged_step(self.model, self.data, self._contact_policy, self._energy_sensor)
        # Refresh the observed and rendered kinematics at post-integration time.
        # The next mj_step performs collision/dynamics itself; running a second
        # full constraint solve here doubled that work without advancing time.
        mj.mj_kinematics(self.model, self.data)
        mj.mj_comPos(self.model, self.data)
        mj.mj_camlight(self.model, self.data)
        mj.mj_comVel(self.model, self.data)
        return self.snapshot()

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
        mj.mj_resetData(self.model, self.data)
        self.data.qpos[:]=self._initial_qpos
        self.data.ctrl[:]=self._initial_ctrl
        staged_forward(self.model, self.data, self._contact_policy, self._energy_sensor)
        return self.snapshot()

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
