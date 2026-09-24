"""Undoable Blueprint edits, independent of rendering and physics handles."""
from dataclasses import replace
from math import cos, sin, pi, sqrt
from little_world.core.blueprint import Blueprint, ControllerSpec
from little_world.core.component import Body, Geometry, Transform, Hinge, Motor, RobotServo, Camera, vector
from .connections import frames, mate, euler_quaternion, module_bounds
from little_world.materials import METAL, RUBBER, SKID, WOOD, PLASTIC


def starter_blueprint():
    return Blueprint((Body('base', Geometry('box', (.32, .24, .09)), 'metal',
                           Transform((0, 0, .13)), dynamic=True),), (METAL, RUBBER, SKID, WOOD, PLASTIC))


def multiply(a, b):
    w, x, y, z = a
    v, i, j, k = b
    return (w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v)


class AssemblyEditor:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.selection = next((c.id for c in blueprint.components if isinstance(c, Body)), None)
        self.past = []
        self.future = []

    @property
    def bodies(self):
        return tuple(c for c in self.blueprint.components if isinstance(c, Body))

    @property
    def selected(self):
        return next((c for c in self.bodies if c.id == self.selection), None)

    def select(self, name):
        if name is not None and not any(b.id == name for b in self.bodies):
            raise ValueError('Select a part in the editable assembly')
        self.selection = name

    def _commit(self, bp, selection=None):
        bp.validate()
        self.past.append((self.blueprint, self.selection))
        self.future.clear()
        self.blueprint = bp
        if selection is not None:
            self.selection = selection
        if self.selected is None:
            self.selection = next((b.id for b in self.bodies), None)

    def load(self, blueprint):
        self._commit(blueprint)

    def undo(self):
        if self.past:
            self.future.append((self.blueprint, self.selection))
            self.blueprint, self.selection = self.past.pop()

    def redo(self):
        if self.future:
            self.past.append((self.blueprint, self.selection))
            self.blueprint, self.selection = self.future.pop()

    def _part(self):
        if self.selected is None:
            raise ValueError('Select a part first')
        return self.selected

    def _replace(self, body):
        self._commit(replace(self.blueprint, components=tuple(body if c.id == body.id else c
                                                            for c in self.blueprint.components)))

    def move(self, delta):
        b = self._part()
        self._replace(replace(b, transform=replace(b.transform,
            position=tuple(x+d for x, d in zip(b.transform.position, delta)))))

    def rotate(self, degrees):
        b = self._part()
        half = degrees * pi / 360
        self._replace(replace(b, transform=replace(b.transform,
            quaternion=multiply((cos(half), 0, 0, sin(half)), b.transform.quaternion))))

    def scale(self, factor):
        b = self._part()
        if b.robot_asset:raise ValueError('Real robot dimensions are fixed; move or replace the complete assembly')
        dims = tuple(x * factor for x in b.geometry.size)
        if any(x < .005 or x > 3 for x in dims):
            raise ValueError('Part dimensions must stay between 0.005 and 3 metres')
        self._replace(replace(b, geometry=Geometry(b.geometry.shape, dims)))

    def set_pose(self, position, rotation=None):
        body = self._part()
        q = body.transform.quaternion if rotation is None else euler_quaternion(vector(rotation, 3, 'rotation'))
        self._replace(replace(body, transform=Transform(position, q)))

    def set_parameters(self, position, rotation, dimensions):
        body = self._part()
        if body.robot_asset:raise ValueError('Real robot dimensions are fixed; use the placement controls')
        geometry = Geometry(body.geometry.shape, dimensions)
        if any(v < .001 or v > 3 for v in geometry.size):
            raise ValueError("Dimensions must stay between 0.001 and 3 metres")
        pose = Transform(position, euler_quaternion(vector(rotation, 3, "rotation")))
        self._replace(replace(body, geometry=geometry, transform=pose))

    def set_dimensions(self, dimensions):
        body = self._part()
        if body.robot_asset:raise ValueError('Real robot dimensions are fixed; use the placement controls')
        geometry = Geometry(body.geometry.shape, dimensions)
        if any(v < .001 or v > 3 for v in geometry.size):
            raise ValueError('Dimensions must stay between 0.001 and 3 metres')
        self._replace(replace(body, geometry=geometry))

    def connection_targets(self):
        removed = {self._part().id}
        while True:
            expanded = removed | {b.id for b in self.bodies if b.parent in removed}
            if expanded == removed:
                return tuple(b for b in self.bodies if b.id not in removed)
            removed = expanded

    def snap(self, parent_id, source_face, target_face, gap=0.):
        body = self._part()
        parent = next((b for b in self.connection_targets() if b.id == parent_id), None)
        if parent is None:
            raise ValueError('Cannot connect to self or a descendant; select another parent')
        gap = vector((gap,), 1, 'gap')[0]
        if not 0 <= gap <= 1:
            raise ValueError('Gap must be between 0 and 1 metre')
        pose = mate(frames(body)[source_face], frames(parent)[target_face], gap)
        self._replace(replace(body, parent=parent.id, dynamic=False, transform=pose))

    def selected_hinge(self):
        body = self._part()
        return next((c for c in self.blueprint.components if isinstance(c, Hinge) and c.body == body.id), None)

    def configure_hinge(self, axis=None, pivot=None, damping=None, limits='unchanged'):
        body = self._part()
        if body.parent is None:
            raise ValueError('Connect this part to a parent before adding a hinge')
        old = self.selected_hinge()
        hinge = old or Hinge(self._id('hinge'), body.id)
        hinge = replace(hinge, axis=hinge.axis if axis is None else axis,
                        position=hinge.position if pivot is None else pivot,
                        damping=hinge.damping if damping is None else damping,
                        limits=hinge.limits if limits == 'unchanged' else limits)
        if old:
            self._replace(hinge)
        else:
            self._add((hinge,), body.id)

    def set_motor_profile(self,profile,operating_cap):
        motors=self.selected_motors()
        if not motors:raise ValueError('Select a joint with a motor')
        replacements={m.id:replace(m,profile=profile,max_torque=operating_cap) for m in motors}
        self._commit(replace(self.blueprint,components=tuple(replacements.get(c.id,c) for c in self.blueprint.components)))

    def set_motor(self, torque):
        hinge = self.selected_hinge()
        if hinge is None:
            raise ValueError('Add a hinge before adding a motor')
        motors = self.selected_motors()
        if torque is None:
            removed = {m.id for m in motors}
            self._commit(replace(self.blueprint,
                components=tuple(c for c in self.blueprint.components if c.id not in removed),
                controllers=tuple(c for c in self.blueprint.controllers if not set(c.actuators) & removed)))
        elif motors:
            replacements = {m.id: replace(m, max_torque=torque) for m in motors}
            self._commit(replace(self.blueprint, components=tuple(replacements.get(c.id,c) for c in self.blueprint.components)))
        else:
            self._add((Motor(self._id('motor'), hinge.id, torque),), self.selection)

    def make_fixed(self):
        hinge = self.selected_hinge()
        if hinge is None:
            return
        removed = {hinge.id, *(m.id for m in self.selected_motors())}
        self._commit(replace(self.blueprint,
            components=tuple(c for c in self.blueprint.components if c.id not in removed),
            controllers=tuple(c for c in self.blueprint.controllers if not set(c.actuators) & removed)))

    def material(self, name):
        b = self._part()
        if b.robot_asset:raise ValueError('Real robot appearance and physical properties are fixed by its source model')
        palette = {m.id: m for m in (METAL, RUBBER, SKID, WOOD, PLASTIC)}
        if name not in palette:
            raise ValueError('Unknown material')
        mats = self.blueprint.materials
        if name not in {m.id for m in mats}:
            mats = (*mats, palette[name])
        else:
            # Reapplying a library surface upgrades legacy color-only materials,
            # preserving their saved density and friction measurements.
            visual=palette[name]
            mats=tuple(replace(m,texture=visual.texture,roughness=visual.roughness,rgba=visual.rgba)
                       if m.id==name else m for m in mats)
        self._commit(replace(self.blueprint, materials=mats,
            components=tuple(replace(b, material=name) if c.id == b.id else c for c in self.blueprint.components)))

    def _id(self, stem):
        used = {c.id for c in (*self.blueprint.components, *self.blueprint.controllers)}
        i = 1
        while any(n == f'{stem}_{i}' or n.startswith(f'{stem}_{i}_') for n in used):
            i += 1
        return f'{stem}_{i}'

    def _add(self, parts, selection, materials=(), mobilize=None):
        mats = {m.id: m for m in self.blueprint.materials}
        for m in (*materials, METAL, RUBBER, SKID, WOOD, PLASTIC):
            mats.setdefault(m.id, m)
        components = (*self.blueprint.components, *parts)
        from .docking import drive_controls
        bp=drive_controls(replace(self.blueprint,components=components,materials=tuple(mats.values())))
        from .default_controls import default_controls
        bp=default_controls(bp,{c.id for c in parts if isinstance(c,Body) and c.catalog_part})
        if mobilize is not None:
            from .docking import grounded
            bp=grounded(bp,mobilize,True,raise_only=True)
        self._commit(bp,selection)

    def add_catalog(self, item_id, mount=None):
        from little_world.assets.catalog import BY_ID
        item=BY_ID[item_id]
        mount=mount or item.mount
        if mount=='output':
            raise ValueError('Use a motor output socket to attach this driven component')
        if mount not in ('Top','Bottom','Left','Right','Front','Back','Floor'):
            raise ValueError('Unsupported mounting face')
        parent=self._part() if mount!='Floor' else None
        if parent is not None and parent.robot_asset:raise ValueError('Mount accessories on the supporting deck; the real robot internals are fixed')
        module=item.blueprint()
        lower,upper=module_bounds(module)
        prefix=self._id(item_id)
        names={c.id:prefix+'_'+c.id for c in module.components}
        # Keep the wheel side in the actuator ID for the existing differential
        # controller resolver. Every inserted part remains ordinary Blueprint data.
        if item.variant=='drive':
            side='left' if mount=='Left' else 'right'
            prefix=self._id(side+'_wheel')
            names={c.id:prefix+'_'+c.id for c in module.components}
        if parent is None:
            position=(.6,0,-lower[2]+.02)
            if item.variant in ('ready_base','real_robot') or item.variant.startswith('lab_'):
                from .docking import world_bounds
                right=world_bounds(self.blueprint)[1][0] if self.bodies else -.15+lower[0]
                position=(right+.15-lower[0],0,-lower[2]+.002)
        else:
            g=parent.geometry
            half=tuple(v/2 for v in g.size) if g.shape=='box' else ((g.size[0],)*3 if g.shape=='sphere'
                   else (g.size[0],g.size[0],g.size[1]/2))
            axis,sign={'Top':(2,1),'Bottom':(2,-1),'Left':(1,1),'Right':(1,-1),
                       'Front':(0,1),'Back':(0,-1)}[mount]
            pos=[0.,0.,0.]
            pos[axis]=sign*(half[axis]+.002)-(lower[axis] if sign>0 else upper[axis])
            if item.variant in ('wheel','drive','hw_tread') and axis==1:
                pos[2]=-.035
            position=tuple(pos)
        from .docking import placement
        pose=placement(item,parent,mount,module) if parent is not None else None
        parts=[]
        for part in module.components:
            if isinstance(part,Body):
                part=replace(part,id=names[part.id],parent=(parent.id if parent else None) if part.parent is None else names[part.parent],
                             dynamic=parent is None and part.parent is None and not part.robot_asset and (not item.variant.startswith('lab_') or part.dynamic),
                             transform=(pose or replace(part.transform,position=position)) if part.parent is None else part.transform)
            elif isinstance(part,(Hinge,Camera,RobotServo)):
                part=replace(part,id=names[part.id],body=names[part.body])
            elif isinstance(part,Motor):
                part=replace(part,id=names[part.id],joint=names[part.joint])
            parts.append(part)
        if item.variant in ('wheel','drive','hw_tread') and parent is not None:
            joint=prefix+'_hinge'
            parts.append(Hinge(joint,names['root'],axis=(0,0,-1 if mount=='Right' else 1)))
            if item.variant=='drive':
                if mount not in ('Left','Right'):
                    raise ValueError('Drive modules mount on Left or Right faces')
                parts.append(Motor(prefix+'_motor',joint,1.))
        elif item.variant=='drive':
            raise ValueError('Select a chassis and attach the drive module to its side')
        self._add(tuple(parts),names['root'],module.materials,parent.id if parent is not None and item.variant in ('wheel','drive','hw_tread') else None)

    def add_box(self):
        name = self._id('box')
        self._add((Body(name, Geometry('box', (.2, .2, .2)), 'wood',
                       Transform((.6, 0, .11)), dynamic=True),), name)

    def attach_beam(self):
        parent = self._part()
        if parent.geometry.shape != 'box':
            raise ValueError('Select a box or beam as the mounting part')
        name = self._id('beam')
        self._add((Body(name, Geometry('box', (.35, .07, .07)), parent.material,
                       Transform((0, 0, parent.geometry.size[2]/2 + .035)), parent=parent.id),), name)

    def attach_wheel(self, side):
        parent = self._part()
        if parent.geometry.shape != 'box':
            raise ValueError('Select a box or beam as the mounting part')
        if side not in (-1, 1):
            raise ValueError('Wheel side must be -1 or +1')
        name = self._id('left_wheel' if side == 1 else 'right_wheel')
        joint, motor = name + '_hinge', name + '_motor'
        self._add((Body(name, Geometry('cylinder', (.085, .035)), 'rubber',
                      Transform((0, side*(parent.geometry.size[1]/2 + .025), -.035),
                                (sqrt(.5), -sqrt(.5), 0, 0)), parent=parent.id),
                   Hinge(joint, name), Motor(motor, joint, 1.)), name)

    def attach_camera(self):
        parent = self._part()
        name = self._id('camera')
        self._add((Camera(name, parent.id, Transform((.18, 0, .08), (.5, .5, -.5, -.5))),), parent.id)

    def selected_motors(self):
        body = self._part()
        joints = {c.id for c in self.blueprint.components if isinstance(c, Hinge) and c.body == body.id}
        return tuple(c for c in self.blueprint.components if isinstance(c, Motor) and c.joint in joints)

    def motor_strength(self, factor):
        motors = self.selected_motors()
        if not motors:
            raise ValueError('Select a powered wheel first')
        replacements = {m.id: replace(m, max_torque=m.max_torque*factor) for m in motors}
        if any(not .05 <= m.max_torque <= 5 for m in replacements.values()):
            raise ValueError('Motor strength must stay between 0.05 and 5 Nm')
        self._commit(replace(self.blueprint, components=tuple(replacements.get(c.id,c)
                                                             for c in self.blueprint.components)))

    def gripper_root(self):
        from .manipulation import gripper_root
        return gripper_root(self)

    def configure_gripper(self,shape,material,friction,torque,pad_length):
        from .manipulation import configure_gripper
        configure_gripper(self,shape,material,friction,torque,pad_length)

    def bind_keys(self, label, positive, negative, speed=30., kp=12., kd=.8, controller_id=None):
        included=self.subtree_ids()
        own=self.selected_motors()
        motors=tuple(c.id for c in own) if own else tuple(c.id for c in self.blueprint.components if isinstance(c,(Motor,RobotServo)) and c.id in included)
        if controller_id is not None:
            old=next(c for c in self.blueprint.controllers if c.id==controller_id and c.kind=='keyboard_position')
            motors=old.actuators
        if not motors:
            raise ValueError('Select a powered arm, gripper, or motor first')
        if controller_id is None:
            existing=next((c for c in self.blueprint.controllers if c.kind=='keyboard_position' and set(c.actuators)==set(motors)),None)
            if existing:controller_id=existing.id
        spec=ControllerSpec(controller_id or self._id('keyboard'),'keyboard_position',motors,
                            label,positive.upper().strip(),negative.upper().strip(),speed,kp,kd)
        controllers=tuple(c for c in self.blueprint.controllers if c.id!=controller_id)
        self._commit(replace(self.blueprint,controllers=(*controllers,spec)))

    def remove_binding(self, controller_id):
        self._commit(replace(self.blueprint,controllers=tuple(c for c in self.blueprint.controllers
                             if c.id!=controller_id or c.kind!='keyboard_position')))

    def subtree_ids(self):
        removed = {self._part().id}
        while True:
            expanded = set(removed)
            for c in self.blueprint.components:
                target = (c.parent if isinstance(c, Body) else
                          c.body if isinstance(c, (Hinge, Camera, RobotServo)) else
                          c.joint if isinstance(c, Motor) else None)
                if target in removed:
                    expanded.add(c.id)
            if expanded == removed:
                return removed
            removed = expanded

    def duplicate(self, offset=(.05, 0., 0.)):
        root = self._part()
        offset = vector(offset, 3, 'duplicate offset')
        included = self.subtree_ids()
        prefix = self._id(root.id + '_copy')
        names = {name: prefix if name == root.id else prefix + '_' + name for name in included}
        copies = []
        for c in self.blueprint.components:
            if c.id not in included:
                continue
            if isinstance(c, Body):
                pose = c.transform
                if c.id == root.id:
                    pose = replace(pose, position=tuple(a+b for a,b in zip(pose.position,offset)))
                copies.append(replace(c,id=names[c.id],parent=names.get(c.parent,c.parent),transform=pose))
            elif isinstance(c, (Hinge, Camera, RobotServo)):
                copies.append(replace(c,id=names[c.id],body=names[c.body]))
            elif isinstance(c, Motor):
                copies.append(replace(c,id=names[c.id],joint=names[c.joint]))
        controllers = tuple(replace(c,id=prefix+'_'+c.id,actuators=tuple(names[a] for a in c.actuators))
                            for c in self.blueprint.controllers if c.actuators and set(c.actuators)<=included)
        self._commit(replace(self.blueprint,components=(*self.blueprint.components,*copies),
                             controllers=(*self.blueprint.controllers,*controllers)),prefix)

    def delete(self):
        removed = self.subtree_ids()
        controllers = tuple(c for c in self.blueprint.controllers if not set(c.actuators) & removed)
        self._commit(replace(self.blueprint, components=tuple(c for c in self.blueprint.components if c.id not in removed),
                             controllers=controllers))
