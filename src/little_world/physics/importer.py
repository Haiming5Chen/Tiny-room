"""Robots from their description files, made ready to drive (ADR 0044, FR-031).

A description file - a URDF, or a MuJoCo model (MJCF) - says what a robot is: its links,
their shapes and masses, and the joints between them. It does not say everything a
simulation needs to drive one. MuJoCo 3.10 reads both formats itself, but a URDF comes in
with no motors, its root link fused into the ground, its `package://` mesh paths unresolved
and its visual shapes dropped, and an attribute it does not know - a misspelt `efort` - is
ignored without a word. The importer reads the file, says what it found, adds what driving
the robot needs and nothing else, and writes the result into the robot library
(`assets/robot_library.py`), where the app places it like a Menagerie arm.

What it adds, to a model with no actuators of its own:
- a position servo on every hinge and slide: stiff enough to hold the robot within half a
  degree of where it is sent against its own weight at any pose (weighed at the home pose
  and 64 others), never softer than settling its joint in a quarter of a second, critically
  damped at the joint's own inertia, its force within the file's effort limit;
- a URDF `<mimic>` as a joint equality, the follower without a servo of its own, as stiff
  as MuJoCo takes at the 2 ms step;
- for a gripper - a limited joint named like a finger whose finger closes on another, or on a
  fixed jaw, at one end of its travel (ADR 0047): its closing direction and its two jaws, a
  servo driven by how closed it is that squeezes with the file's effort (or the kit gripper's
  12 N at each jaw) once the jaws are stopped, the jaws' contacts the stiffest MuJoCo takes,
  and the tool point between the jaws;
- one body per link (the root link kept as the robot's base), visual shapes kept and
  collision shapes hidden behind them;
- links that already touch at the home pose kept from touching each other, as neighbours
  are (the backend excludes neighbours itself).
A model that has actuators keeps them and gets nothing added; they must be position servos.

MuJoCo-bound, like the backend.
"""
from datetime import datetime, timezone
import hashlib
import json
from math import degrees, pi, radians, sqrt
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote
import xml.etree.ElementTree as ET

import mujoco as mj
import numpy as np

from little_world.assets import robot_library

SETTLE = .25            # s: an added servo is never slower than settling its joint in this
SLOWEST = 5.8 / SETTLE  # rad/s: the natural frequency that settles a critically damped joint to 2 % in SETTLE
FASTEST = 100.          # rad/s: the stiffest an added servo is made - a fifth of a radian a step at 2 ms
SAG = radians(.5)       # an added servo holds a hinge within this against the robot's own weight
SAG_SLIDE = .0005       # m: and a slide within this
POSES = 64              # poses the robot's weight is weighed at, besides the home pose
TURN = 2 * pi           # a hinge without limits is driven within one turn either way
TRAVEL = .5             # m: a slide without limits, within half a metre either way
MOST = 8                # servos a robot can have: a RobotServo's channels
MESHES = ('.stl', '.obj', '.msh')   # the mesh files MuJoCo 3.10 reads
FACES = 200_000         # a mesh with more faces is reported as slow (PickNik's MuJoCo guide decimates past it)
TOOL = re.compile(r'(tool|tcp|end_?effector|flange|ee_link|ee$|tip|grasp)', re.I)
FINGER = re.compile(r'(finger|gripper|jaw|claw|pinch)', re.I)
CLOSING = .003          # m: a gripper's fingers come at least this much closer at one end of its travel
SQUEEZE_AT = .1         # a gripper squeezes with all its force once its jaws are stopped this share of its travel short
GRIP = 12.              # N at each jaw: what a gripper whose file gives no effort squeezes with - the kit gripper's (ADR 0017)
JAW_SOLREF = (.004, 1.) # a jaw's contact: a time constant of twice the 2 ms step, the stiffest MuJoCo takes
JAW_SOLIMP = (.95, .99, .001)
VERSION = 1

# What a URDF may say (ROS urdf/XML, read 21 Oct 2026): anything else is reported, because
# MuJoCo ignores a word it does not know without a word of its own.
URDF = {
    'robot': {'name', 'version'},
    'link': {'name', 'type'},
    'joint': {'name', 'type'},
    'inertial': set(), 'visual': {'name'}, 'collision': {'name'}, 'geometry': set(),
    'origin': {'xyz', 'rpy'}, 'mass': {'value'},
    'inertia': {'ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz'},
    'box': {'size'}, 'cylinder': {'radius', 'length'}, 'sphere': {'radius'},
    'capsule': {'radius', 'length'}, 'mesh': {'filename', 'scale'},
    'material': {'name'}, 'color': {'rgba'}, 'texture': {'filename'},
    'parent': {'link'}, 'child': {'link'}, 'axis': {'xyz'},
    'calibration': {'rising', 'falling', 'reference_position'},
    'dynamics': {'damping', 'friction'},
    'limit': {'lower', 'upper', 'effort', 'velocity'},
    'mimic': {'joint', 'multiplier', 'offset'},
    'safety_controller': {'soft_lower_limit', 'soft_upper_limit', 'k_position', 'k_velocity'},
}
NOT_READ = {'transmission', 'gazebo', 'mujoco', 'sensor'}   # their contents are not checked
KINDS = {mj.mjtJoint.mjJNT_HINGE: 'hinge', mj.mjtJoint.mjJNT_SLIDE: 'slide'}


class ImportFailed(ValueError):
    """The file cannot be made into a robot; the message says why, in plain words."""


class Report:
    """What an import found, added and warns about, in plain words."""

    def __init__(self):
        self.lines = []

    def found(self, text):
        self.lines.append(('found', text))

    def added(self, text):
        self.lines.append(('added', text))

    def warn(self, text):
        self.lines.append(('warning', text))

    def of(self, kind):
        return [text for k, text in self.lines if k == kind]

    def text(self):
        heads = {'found': 'Found', 'added': 'Added', 'warning': 'Check'}
        out = []
        for kind in ('found', 'added', 'warning'):
            if self.of(kind):
                out.append(heads[kind] + ':')
                out.extend('- ' + t for t in self.of(kind))
        return '\n'.join(out)


# -- reading ----------------------------------------------------------------------------


def _local(tag):
    return tag.rsplit('}', 1)[-1].split(':')[-1]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _copy(source, assets, copied):
    """Copy a mesh or texture into `assets` under a flat name of its own; the name."""
    source = Path(source).resolve()
    if source not in copied:
        stem = re.sub(r'[^A-Za-z0-9_.-]+', '_', source.name)
        name = f'{len(copied):03d}_{stem}'
        shutil.copyfile(source, assets / name)
        copied[source] = name
    return copied[source]


def _package(name, start):
    """The folder of ROS package `name`: a folder of that name, or one whose package.xml
    names it, at or above the description file's folder or beside one of them."""
    for folder in [start, *start.parents]:
        try:
            beside = [p for p in folder.iterdir() if p.is_dir()]
        except OSError:
            beside = []
        for candidate in (folder, *beside):
            if candidate.name == name:
                return candidate
            manifest = candidate / 'package.xml'
            if manifest.is_file():
                try:
                    found = ET.parse(manifest).getroot().findtext('name')
                except ET.ParseError:
                    found = None
                if found and found.strip() == name:
                    return candidate
    return None


def _resolve(filename, file):
    """Where a URDF's mesh is: package://, file:// and paths relative to the file."""
    if filename.startswith('package://'):
        package, _, rest = filename[len('package://'):].partition('/')
        folder = _package(package, file.parent)
        return None if folder is None else folder / unquote(rest)
    if filename.startswith('file://'):
        return Path(unquote(filename[len('file://'):]))
    path = Path(unquote(filename))
    return path if path.is_absolute() else file.parent / path


def _words(element, report, where='robot'):
    """Report every element and attribute a URDF does not have."""
    for child in element:
        tag = _local(child.tag)
        if tag in NOT_READ:
            continue
        name = child.get('name')
        here = f"{tag} '{name}'" if name else f'{tag} in {where}'
        if tag not in URDF:
            report.warn(f'<{tag}> in {where} is not URDF: MuJoCo ignores it')
            continue
        for attribute in child.attrib:
            if _local(attribute) not in URDF[tag]:
                report.warn(f"{here}: '{_local(attribute)}' is not a URDF attribute of <{tag}> - "
                            'MuJoCo ignores it (a misspelling?)')
        _words(child, report, f"{tag} '{name}'" if name else where)


def _urdf(path, root, assets, report, copied):
    joints = root.findall('joint')
    for j in joints:
        kind = j.get('type')
        if kind == 'floating':
            raise ImportFailed(f"Joint '{j.get('name')}' is floating. Little World fixes a robot's base "
                               'where it is placed; a robot that floats or walks cannot be imported yet.')
        if kind == 'planar':
            raise ImportFailed(f"Joint '{j.get('name')}' is planar, which cannot be imported yet.")
    _words(root, report)
    mimic = {}
    for j in joints:
        m = j.find('mimic')
        if m is not None:
            mimic[j.get('name')] = (m.get('joint'), float(m.get('multiplier', 1)), float(m.get('offset', 0)))
    shapes = {}
    for link in root.findall('link'):
        name = link.get('name')
        for owner in ('visual', 'collision'):
            for element in list(link.findall(owner)):
                mesh = element.find('geometry/mesh')
                if mesh is None:
                    continue
                given = mesh.get('filename', '')
                source = _resolve(given, path)
                if source is None or not source.is_file():
                    raise ImportFailed(f"Link '{name}': its {owner} mesh '{given}' is not there"
                                       + ('' if source is None else f' (looked for {source})'))
                if source.suffix.lower() not in MESHES:
                    link.remove(element)
                    report.warn(f"Link '{name}': its {owner} mesh {source.name} is a {source.suffix} file; "
                                f'MuJoCo reads STL, OBJ and MSH only, so the {owner} shape was left out')
                    continue
                mesh.set('filename', _copy(source, assets, copied))
        shapes[name] = (link.find('visual') is not None, link.find('collision') is not None,
                        link.find('inertial') is not None)
    if root.find('transmission') is not None:
        report.found('Its <transmission> elements describe ROS controllers, which MuJoCo does not read')
    for block in root.findall('mujoco'):
        root.remove(block)
        report.found('Its own <mujoco> block was replaced by the importer\'s')
    block = ET.Element('mujoco')
    ET.SubElement(block, 'compiler', meshdir=str(assets), strippath='false', fusestatic='false',
                  discardvisual='false')
    root.insert(0, block)
    try:
        spec = mj.MjSpec.from_string(ET.tostring(root, encoding='unicode'))
    except Exception as error:
        raise ImportFailed(f'MuJoCo could not read {path.name}: {_plain(error)}') from None
    return spec, mimic, shapes


def _mjcf(path, assets, report, copied):
    try:
        spec = mj.MjSpec.from_file(str(path))
    except Exception as error:
        raise ImportFailed(f'MuJoCo could not read {path.name}: {_plain(error)}') from None
    base = path.parent
    for kind, items, folder in (('mesh', spec.meshes, spec.meshdir), ('texture', spec.textures, spec.texturedir)):
        for item in items:
            if not item.file:
                continue
            source = Path(item.file)
            if not source.is_absolute():
                source = base / (folder or '') / source
            if not source.is_file():
                raise ImportFailed(f"Its {kind} '{item.file}' is not there (looked for {source})")
            if not item.name:
                item.name = Path(item.file).stem   # the name MuJoCo gives it from its file, kept
            item.file = _copy(source, assets, copied)
    for kind, items in (('height field', spec.hfields), ('skin', spec.skins), ('flex', spec.flexes)):
        if len(items):
            raise ImportFailed(f'It has a {kind}, which a robot from the library cannot have yet.')
    spec.meshdir = spec.texturedir = str(assets)
    spec.compiler.meshdir = spec.compiler.texturedir = str(assets)
    return spec, {}, {}


def _plain(error):
    return ' '.join(str(error).replace('Error:', '').split())


def _read(path, assets, report):
    path = Path(path)
    if not path.is_file():
        raise ImportFailed(f'There is no file at {path}')
    if path.name.endswith('.xacro'):
        raise ImportFailed(f'{path.name} is a xacro file: make the URDF from it first '
                           f'(xacro {path.name} > robot.urdf) and import that')
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise ImportFailed(f'{path.name} is not readable XML: {error}') from None
    if any('xacro' in e.tag for e in root.iter()):
        raise ImportFailed(f'{path.name} still has xacro macros in it: make the URDF from it first '
                           f'(xacro {path.name} > robot.urdf) and import that')
    copied = {}
    tag = _local(root.tag)
    if tag == 'robot':
        spec, mimic, shapes = _urdf(path, root, assets, report, copied)
        return spec, mimic, shapes, 'URDF', root.get('name') or path.stem, copied
    if tag == 'mujoco':
        spec, mimic, shapes = _mjcf(path, assets, report, copied)
        return spec, mimic, shapes, 'MJCF', root.get('model') or path.stem, copied
    raise ImportFailed(f'{path.name} is neither a URDF (<robot>) nor a MuJoCo model (<mujoco>): '
                       f'it starts with <{tag}>')


# -- making it drivable -----------------------------------------------------------------


def _subtree(body):
    yield body
    for child in body.bodies:
        yield from _subtree(child)


def _label(name):
    text = re.sub(r'[_\-]+', ' ', re.sub(r'(_joint|joint_|_jnt)$', '', name, flags=re.I)).strip()
    return (text[:1].upper() + text[1:])[:48] or name[:48]


def _servos(spec, model, joints):
    """The model's own actuators, which must be position servos on joints: (actuator, joint)."""
    out = []
    for i, a in enumerate(spec.actuators):
        name = a.name or f'actuator_{i}'
        a.name = name
        gain, bias = model.actuator_gainprm[i], model.actuator_biasprm[i]
        position = (model.actuator_gaintype[i] == mj.mjtGain.mjGAIN_FIXED
                    and model.actuator_biastype[i] == mj.mjtBias.mjBIAS_AFFINE
                    and gain[0] > 0 and abs(bias[1] + gain[0]) <= 1e-9 * gain[0])
        if model.actuator_trntype[i] != mj.mjtTrn.mjTRN_JOINT or not position:
            raise ImportFailed(f"Its actuator '{name}' is not a position servo on a joint. Little World "
                               'drives a model\'s own actuators only when they are; remove the actuators '
                               'to have servos added instead.')
        joint = model.joint(int(model.actuator_trnid[i, 0])).name
        if joint not in joints:
            raise ImportFailed(f"Its actuator '{name}' drives joint '{joint}', which is not a hinge or a slide.")
        out.append((name, joint))
    return out


def _weight(model, joints, mimic, home, rng):
    """The most torque (or force) each joint needs to hold the robot up, over the home pose and
    POSES random ones: gravity's share at each joint, a mimic follower's added to its leader's."""
    data = mj.MjData(model)
    ids = {n: model.joint(n).id for n in joints}
    most = dict.fromkeys(joints, 0.)
    for k in range(POSES + 1):
        q = dict(home)
        if k:
            for n in joints:
                if n in mimic:
                    continue
                j = ids[n]
                lo, hi = (model.jnt_range[j] if model.jnt_limited[j]
                          else (-pi, pi) if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE else (-TRAVEL, TRAVEL))
                q[n] = float(rng.uniform(lo, hi))
        for n, (leader, k_, offset) in mimic.items():
            if leader in q:
                q[n] = offset + k_ * q[leader]
        for n in joints:
            data.qpos[model.jnt_qposadr[ids[n]]] = q[n]
        data.qvel[:] = 0
        mj.mj_forward(model, data)
        load = {n: float(data.qfrc_bias[model.jnt_dofadr[ids[n]]]) for n in joints}
        for n, (leader, k_, _) in mimic.items():
            if leader in load:
                load[leader] += k_ * load[n]
        for n in joints:
            most[n] = max(most[n], abs(load[n]))
    return most


def _box(model, data):
    """The robot's bounding box at its pose, in the frame the model places its root body in -
    the frame the backend attaches it by: (centre, size)."""
    points = []
    signs = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    for g in range(model.ngeom):
        if model.geom_bodyid[g] == 0:
            continue
        centre, half = model.geom_aabb[g, :3], model.geom_aabb[g, 3:]
        corners = centre + signs * half
        points.append(data.geom_xpos[g] + corners @ data.geom_xmat[g].reshape(3, 3).T)
    points = np.vstack(points)
    low, high = points.min(axis=0), points.max(axis=0)
    return (low + high) / 2, np.maximum(high - low, .01)


def prepare(path, assets, name=None):
    """Read a description file and make it drivable: (spec, metadata, report). Meshes are
    copied into `assets`; nothing else is written."""
    report = Report()
    spec, mimic, shapes, kind, title, copied = _read(path, Path(assets), report)
    title = name or title
    top = list(spec.worldbody.bodies)
    if not top:
        raise ImportFailed('The file has no bodies: there is no robot in it.')
    if len(top) > 1:
        raise ImportFailed(f'The file holds {len(top)} separate bodies at its top ('
                           + ', '.join(b.name or '?' for b in top[:5]) + '): import one robot at a time.')
    base = top[0]
    if not base.name:
        base.name = 'base'
    # A 'home' keyframe gives the home pose; read by joint before the model changes shape.
    keyed = {}
    key = next((k for k in spec.keys if k.name == 'home'), None)
    if key is not None:
        try:
            original = spec.compile()
        except Exception as error:
            raise ImportFailed(f'MuJoCo could not make a model of it: {_plain(error)}') from None
        if len(key.qpos) == original.nq:
            for j in range(original.njnt):
                if original.jnt_type[j] in KINDS and original.joint(j).name:
                    keyed[original.joint(j).name] = float(key.qpos[original.jnt_qposadr[j]])
    for k in list(spec.keys):
        spec.delete(k)
    for j in list(base.joints):
        if j.type == mj.mjtJoint.mjJNT_FREE:
            spec.delete(j)
            report.found('Its base had a free joint: removed, because Little World fixes a robot\'s base '
                         'where it is placed (on the floor, a bench or a cart)')
    worldly = len(spec.worldbody.geoms)
    for g in list(spec.worldbody.geoms):
        spec.delete(g)
    if worldly:
        report.found(f'{worldly} shape{"s" if worldly != 1 else ""} fixed to the world (a floor?) '
                     'left out: only the robot is imported')
    bodies = list(_subtree(base))
    names = set()
    for i, b in enumerate(bodies):
        if not b.name:
            b.name = f'link_{i}'
        names.add(b.name)
    joints = []
    for b in bodies:
        for j in b.joints:
            if j.type == mj.mjtJoint.mjJNT_BALL:
                raise ImportFailed(f"Joint '{j.name or '?'}' is a ball joint, which cannot be imported yet.")
            if j.type == mj.mjtJoint.mjJNT_FREE:
                raise ImportFailed(f"Link '{b.name}' floats free inside the robot, which cannot be imported.")
            if not j.name:
                j.name = f'joint_{len(joints)}'
            joints.append(j.name)
    if kind == 'URDF':
        for b in bodies:
            visual = [g.contype == 0 and g.conaffinity == 0 for g in b.geoms]
            for g, seen in zip(b.geoms, visual):
                g.group = 2 if seen else (3 if any(visual) else 0)
    for follower, (leader, k, offset) in mimic.items():
        if leader not in joints or follower not in joints:
            raise ImportFailed(f"Joint '{follower}' mimics '{leader}', which is not one of its joints.")
        e = spec.add_equality(type=mj.mjtEq.mjEQ_JOINT, name1=follower, name2=leader)
        e.data = np.array([offset, k, 0, 0, 0] + [0] * (len(e.data) - 5))
        # A mimic is a gear or a linkage: as stiff as MuJoCo takes at the 2 ms step. With
        # MuJoCo's default softness a follower finger gave 3.5 mm under a 20 N squeeze.
        e.solref[:] = JAW_SOLREF
        e.solimp[:3] = JAW_SOLIMP
        report.added(f"'{follower}' follows '{leader}'" + (f' ({k:g} times as far)' if k != 1 else '')
                     + ': a joint equality, as the file\'s <mimic> says')
    try:
        model = spec.compile()
    except Exception as error:
        raise ImportFailed(f'MuJoCo could not make a model of it: {_plain(error)}') from None
    if not joints:
        raise ImportFailed('It has no joints: nothing about it moves.')
    jid = {n: model.joint(n).id for n in joints}
    # The home pose: the file's 'home' keyframe, else its reference pose, within the limits.
    home = {}
    for n in joints:
        j = jid[n]
        q = keyed.get(n, float(model.qpos0[model.jnt_qposadr[j]]))
        if model.jnt_limited[j]:
            lo, hi = model.jnt_range[j]
            if not lo <= q <= hi:
                q = float(min(max(q, lo), hi))
                report.found(f"'{n}' starts at its nearest limit: its reference position is outside its range")
        home[n] = q
    for n, (leader, k, offset) in mimic.items():
        home[n] = offset + k * home[leader]
    own = len(spec.actuators) > 0
    if own:
        servos = _servos(spec, model, joints)
        report.found(f'{len(servos)} actuator{"s" if len(servos) != 1 else ""} of its own, '
                     'position servos: kept, and nothing added')
    else:
        driven = [n for n in joints if n not in mimic]
        if len(driven) > MOST:
            raise ImportFailed(f'It has {len(driven)} driven joints; Little World drives at most {MOST} '
                               'of one robot for now.')
        servos = []
        for n in driven:
            a = spec.add_actuator(name='servo_' + n, target=n, trntype=mj.mjtTrn.mjTRN_JOINT)
            a.set_to_position(kp=1., kv=0.)
            servos.append((a.name, n))
    if len(servos) > MOST:
        raise ImportFailed(f'It has {len(servos)} actuators; Little World drives at most {MOST} of one robot for now.')
    try:
        model = spec.compile()
    except Exception as error:
        raise ImportFailed(f'MuJoCo could not make a model of it: {_plain(error)}') from None
    weight = _weight(model, joints, mimic, home, np.random.default_rng(0))
    parent = {b.name: (b.parent.name if b.parent is not None else None) for b in bodies}
    grip = None if own else _gripper(model, servos, mimic, jid, home, parent)
    if not own:
        sags = []
        for channel, ((actuator, n), a) in enumerate(zip(servos, spec.actuators)):
            j = jid[n]
            inertia = float(model.dof_M0[model.jnt_dofadr[j]])
            hinge = model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
            if grip is not None and channel == grip['channel']:
                # A gripper squeezes what stops its jaws: with all its force once they are
                # stopped SQUEEZE_AT of its travel short of where they are sent. A servo that
                # stiff is stable at 2 ms only with the inertia of a geared drive behind the
                # finger - a gripper's motor and screw - which is added where the finger is lighter.
                given = bool(model.jnt_actfrclimited[j])
                squeeze = float(max(abs(model.jnt_actfrcrange[j]))) if given else GRIP * grip['lever'] * grip['share']
                kp = squeeze / (SQUEEZE_AT * abs(grip['closed'] - grip['open']))
                drive = kp / FASTEST ** 2
                if drive > inertia:
                    spec.joint(n).armature += drive - inertia
                    inertia = drive
                a.set_to_position(kp=kp, kv=2 * sqrt(kp * inertia))
                if not given:
                    a.forcelimited = mj.mjtLimited.mjLIMITED_TRUE
                    a.forcerange = (-squeeze, squeeze)
                grip.update(squeeze=squeeze, given=given, unit='N m' if hinge else 'N',
                            jaw=squeeze / (grip['lever'] * grip['share']))
                # MuJoCo's contacts are soft in proportion to the mass behind them: squeezed
                # with 20 N, a 10 g box let the jaws sink 7 mm into each side. The jaws'
                # contacts are made the stiffest MuJoCo takes at the 2 ms step, and decide
                # their own contacts (priority) with torsional friction, so that what they
                # hold does not turn about the line between them.
                for jaw in grip['jaws']:
                    for g in spec.body(jaw).geoms:
                        if g.contype or g.conaffinity:
                            g.priority, g.condim = 1, 4
                            g.solref[:] = JAW_SOLREF
                            g.solimp[:3] = JAW_SOLIMP
                a.ctrlrange = tuple(float(x) for x in model.jnt_range[j])
                a.ctrllimited = True
                continue
            stiff = max(inertia * SLOWEST ** 2, weight[n] / (SAG if hinge else SAG_SLIDE))
            kp = min(stiff, inertia * FASTEST ** 2)
            a.set_to_position(kp=kp, kv=2 * sqrt(kp * inertia))
            if model.jnt_limited[j]:
                a.ctrlrange = tuple(float(x) for x in model.jnt_range[j])
            else:
                a.ctrlrange = (-TURN, TURN) if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE else (-TRAVEL, TRAVEL)
                report.warn(f"'{n}' has no limits in the file: it is driven within "
                            + ('one turn' if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE else 'half a metre')
                            + ' either way')
            a.ctrllimited = True
            if kp < stiff:
                sags.append((n, weight[n] / kp))
        hinges = sum(model.jnt_type[jid[n]] == mj.mjtJoint.mjJNT_HINGE for _, n in servos)
        report.added(f'A position servo on each of its {len(servos)} driven joint{"s" if len(servos) != 1 else ""}'
                     ', because the file has no motors: each holds its joint within '
                     f'{degrees(SAG):g}°' + ('' if hinges == len(servos) else f' (a slide within {SAG_SLIDE * 1000:g} mm)')
                     + ' of where it is sent against the robot\'s own weight, '
                     f'and settles in at most {SETTLE:g} s')
        for n, sag in sags:
            report.warn(f"'{n}' carries a lot for its own inertia: its servo may let it sag "
                        + (f'{degrees(sag):.1f}°' if model.jnt_type[jid[n]] == mj.mjtJoint.mjJNT_HINGE else f'{sag * 1000:.1f} mm')
                        + ' at the worst pose')
    for _, n in servos:
        j = jid[n]
        unit = 'N m' if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE else 'N'
        if model.jnt_actfrclimited[j]:
            limit = float(max(abs(model.jnt_actfrcrange[j])))
            if weight[n] > limit:
                report.warn(f"'{n}' can push at most {limit:g} {unit}; holding the robot up takes up to "
                            f'{weight[n]:.3g} {unit} at some poses: it will sag there')
        elif not own and not (grip is not None and n == servos[grip['channel']][1]):
            report.warn(f"'{n}' has no effort limit in the file: its servo is as strong as it needs to be, "
                        'which a real motor is not')
    try:
        model = spec.compile()
    except Exception as error:
        raise ImportFailed(f'MuJoCo could not make a model of it: {_plain(error)}') from None
    data = mj.MjData(model)
    for n in joints:
        data.qpos[model.jnt_qposadr[jid[n]]] = home[n]
    mj.mj_forward(model, data)
    # Links that touch at the home pose, other than neighbours, are kept apart from each other.
    neighbours = {frozenset((a, p)) for a, p in parent.items() if p}
    touching = {}
    for c in data.contact[:data.ncon]:
        a, b = (model.body(int(model.geom_bodyid[g])).name for g in (c.geom1, c.geom2))
        if a != b and frozenset((a, b)) not in neighbours and a in names and b in names:
            touching[frozenset((a, b))] = max(touching.get(frozenset((a, b)), 0.), -float(c.dist))
    exclude = sorted(sorted(pair) for pair in touching)
    for a, b in exclude:
        report.added(f"'{a}' and '{b}' already touch at the home pose ({touching[frozenset((a, b))] * 1000:.1f} mm "
                     'deep): they are kept from colliding with each other')
    # Mass, size, links without mass or shape.
    root = model.body(base.name).id
    moving = [i for i in range(1, model.nbody) if _moves(model, i, root)]
    mass = float(sum(model.body_mass[i] for i in range(1, model.nbody)))
    for link, (visual, collision, inertial) in shapes.items():
        i = model.body(link).id
        if not inertial and i in moving and (visual or collision):
            report.warn(f"Link '{link}' has no mass in the file: MuJoCo worked it out from its shapes "
                        f'as if they were water, {model.body_mass[i]:.3g} kg')
        if not collision and (visual or inertial) and model.body_mass[i] > 0:
            report.warn(f"Link '{link}' has no collision shape: it passes through things")
    hulls = sum(model.geom_type[g] == mj.mjtGeom.mjGEOM_MESH and (model.geom_contype[g] or model.geom_conaffinity[g])
                for g in range(model.ngeom))
    if hulls:
        report.found(f'{hulls} collision mesh{"es" if hulls != 1 else ""}: MuJoCo collides each as its convex hull, '
                     'so a hollow or hooked link collides as if it were filled')
    for i in range(model.nmesh):
        if model.mesh_facenum[i] > FACES:
            report.warn(f"Mesh '{model.mesh(i).name}' has {int(model.mesh_facenum[i]):,} faces: drawing and "
                        'colliding with it will be slow; a simplified copy would do')
    centre, size = _box(model, data)
    # The tool point: a link named like a tool, deepest first; else the last driven link.
    depth = {base.name: 0}
    for b in bodies[1:]:
        depth[b.name] = depth[parent[b.name]] + 1
    tools = sorted((b.name for b in bodies if TOOL.search(b.name or '')), key=lambda n: -depth[n])
    last = max((model.body(int(model.jnt_bodyid[jid[n]])).name for _, n in servos), key=lambda n: depth[n])
    tool = tools[0] if tools and depth[tools[0]] >= depth[last] else last
    joint_kind = {n: KINDS[model.jnt_type[jid[n]]] for n in joints}
    units = ['deg' if joint_kind[n] == 'hinge' else 'mm' for _, n in servos]
    if grip is not None:
        units[grip['channel']] = '%'
        tool = [grip['palm'], grip['point']]
        report.added(f"'{servos[grip['channel']][1]}' closes a gripper - its fingers {1000 * grip['wide']:.0f} mm "
                     f"apart open, {1000 * grip['narrow']:.0f} mm closed: it is driven by how closed it is, 0 to 100 %, "
                     f"and presses what it closes on with up to {grip['jaw']:.3g} N at each jaw ("
                     + (f"its effort in the file, {grip['squeeze']:.3g} {grip['unit']}" if grip['given']
                        else "the file gives no effort: the kit gripper's")
                     + '); the tool point is between its fingers, and the grasp blocks hold with it')
    hinge_n = sum(k == 'hinge' for k in joint_kind.values())
    report.lines.insert(0, ('found', f'{title} ({kind}): {len(bodies)} links, {len(joints)} joints '
                            f'({hinge_n} hinge{"s" if hinge_n != 1 else ""}'
                            + (f', {len(joints) - hinge_n} slide{"s" if len(joints) - hinge_n != 1 else ""}' if len(joints) > hinge_n else '')
                            + f'), {mass:.3g} kg, {size[2]:.2f} m tall'))
    meta = dict(
        title=str(title)[:60], format=kind,
        center=[float(x) for x in centre], size=[float(x) for x in size],
        mass=mass, moving_mass=float(sum(model.body_mass[i] for i in moving)),
        home=[home[n] for n in joints],
        ctrl=[home[n] for _, n in servos],
        root=base.name, joints=joints,
        actuators=[a for a, _ in servos], servo_joints=[n for _, n in servos],
        limits=[_limits(model, a, jid[n]) for a, n in servos],
        units=units,
        labels=[_label(n) for _, n in servos],
        tool=tool if isinstance(tool, list) else [tool, [0., 0., 0.]], exclude=exclude,
        gripper=None if grip is None else dict(channel=grip['channel'], open=grip['open'], closed=grip['closed'],
                                               jaws=list(grip['jaws'])),
        report=report.lines,
    )
    return spec, meta, report, copied


def _gripper(model, servos, mimic, jid, home, parent):
    """A gripper the file describes, if any: a limited servo joint named like a finger (or its
    link), whose finger comes closer to the other finger - its mimic follower's link - or, with
    none, to a fixed jaw - the link it hangs from or a link fixed to that one - at one end of its
    travel than at the other. The end where they are nearest closes it. A dict - its servo channel, the open and closed joint positions,
    the two jaw links, the link carrying them and the point between the jaws in its frame,
    the fingers' gap open and closed, a hinged finger's lever (1 for a slide) and how many
    shares of the joint's force there are, one for each finger it closes - or None."""
    followers = {leader: follower for follower, (leader, _, _) in mimic.items()}
    data = mj.MjData(model)

    def gap(q, finger, other):
        pose = dict(home)
        pose[finger] = q
        for follower, (leader, k, offset) in mimic.items():
            pose[follower] = offset + k * pose[leader]
        for n, v in pose.items():
            data.qpos[model.jnt_qposadr[jid[n]]] = v
        mj.mj_forward(model, data)
        a, b = (model.body(name).id for name in other)
        geoms = lambda body: [g for g in range(model.ngeom) if model.geom_bodyid[g] == body
                              and (model.geom_contype[g] or model.geom_conaffinity[g])]
        pairs = [(g, h) for g in geoms(a) for h in geoms(b)]
        if not pairs:
            return None, None, None
        best = min(pairs, key=lambda gh: mj.mj_geomDistance(model, data, gh[0], gh[1], 1., None))
        middle = (data.geom_xpos[best[0]] + data.geom_xpos[best[1]]) / 2
        return max(0., float(mj.mj_geomDistance(model, data, best[0], best[1], 1., None))), middle, best[0]

    for channel, (_, n) in enumerate(servos):
        j = jid[n]
        finger = model.body(int(model.jnt_bodyid[j])).name
        if not (FINGER.search(n) or FINGER.search(finger)) or not model.jnt_limited[j]:
            continue
        other_joint = followers.get(n)
        if other_joint:
            others = [model.body(int(model.jnt_bodyid[jid[other_joint]])).name]
        elif parent[finger] is None:
            continue
        else:
            # A fixed jaw: the link the finger hangs from, or a link fixed to that one.
            hub = model.body(parent[finger]).id
            others = [parent[finger]] + [model.body(i).name for i in range(model.nbody)
                                         if model.body_parentid[i] == hub and i != hub
                                         and not model.body_jntnum[i] and model.body(i).name != finger]
        lo, hi = (float(x) for x in model.jnt_range[j])
        found = []
        for other in others:
            (a, _, _), (b, _, _) = gap(lo, n, (finger, other)), gap(hi, n, (finger, other))
            if a is not None and b is not None and abs(a - b) >= CLOSING:
                found.append((min(a, b), other, a, b))
        if not found:
            continue
        _, other, a, b = min(found)
        closed, opened = (lo, hi) if a < b else (hi, lo)
        _, middle, jaw = gap(closed, n, (finger, other))
        # A finger on a hinge squeezes with a torque: the force at its jaw times its lever.
        lever = 1.
        if model.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE:
            arm = data.geom_xpos[jaw] - data.xanchor[j]
            lever = float(np.linalg.norm(arm - (arm @ data.xaxis[j]) * data.xaxis[j])) or 1.
        # With a follower the joint's force closes both fingers: each jaw gets its share.
        share = 1. + abs(mimic[other_joint][1]) if other_joint else 1.
        palm = parent[finger]
        p = model.body(palm).id
        gap(home[n], n, (finger, other))     # the frame of the link carrying the jaws, at home
        point = data.xmat[p].reshape(3, 3).T @ (middle - data.xpos[p])
        return dict(channel=channel, open=opened, closed=closed, jaws=(finger, other), palm=palm,
                    point=[float(x) for x in point], wide=max(a, b), narrow=min(a, b), lever=lever, share=share)
    return None


def _limits(model, actuator, joint):
    """Where a servo can be sent: its control range, else its joint's, else a turn (or half a
    metre) either way."""
    a = model.actuator(actuator).id
    if model.actuator_ctrllimited[a]:
        return [float(x) for x in model.actuator_ctrlrange[a]]
    if model.jnt_limited[joint]:
        return [float(x) for x in model.jnt_range[joint]]
    far = TURN if model.jnt_type[joint] == mj.mjtJoint.mjJNT_HINGE else TRAVEL
    return [-far, far]


def _relative(xml):
    """The written model with its meshes and textures found beside it, in assets/."""
    root = ET.fromstring(xml)
    for compiler in root.iter('compiler'):
        for attribute in ('meshdir', 'texturedir', 'assetdir'):
            if attribute in compiler.attrib:
                compiler.set(attribute, 'assets')
    return ET.tostring(root, encoding='unicode')


def _moves(model, body, root):
    while body > 0 and body != root:
        if model.body_jntnum[body]:
            return True
        body = int(model.body_parentid[body])
    return False


# -- the library ------------------------------------------------------------------------


def import_robot(path, name=None):
    """Import a description file into the robot library: (its `user:` name, the report).
    Nothing is written if it fails."""
    path = Path(path)
    library = robot_library.root()
    library.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='.import-', dir=library))
    try:
        assets = work / 'assets'
        assets.mkdir()
        spec, meta, report, copied = prepare(path, assets, name)
        (work / 'model.xml').write_text(_relative(spec.to_xml()), encoding='utf-8')
        try:
            mj.MjSpec.from_file(str(work / 'model.xml')).compile()
        except Exception as error:
            raise ImportFailed(f'The model written for it could not be read back: {_plain(error)}') from None
        (work / 'source').mkdir()
        shutil.copyfile(path, work / 'source' / path.name)
        (work / 'metadata.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
        (work / 'REPORT.txt').write_text(report.text() + '\n', encoding='utf-8')
        files = {'source/' + path.name: _sha(path), **{'assets/' + n: _sha(assets / n) for n in sorted(copied.values())},
                 'model.xml': _sha(work / 'model.xml')}
        (work / 'SOURCE.json').write_text(json.dumps(dict(
            file=path.name, format=meta['format'], imported=datetime.now(timezone.utc).isoformat(timespec='seconds'),
            mujoco=mj.__version__, importer=VERSION, sha256=files), indent=1), encoding='utf-8')
        for _ in range(100):
            entry = robot_library.free_name(name or meta['title'])
            try:
                os.rename(work, library / entry)
                break
            except OSError:
                continue
        else:
            raise ImportFailed('No free name for it in the robot library.')
        robot_library.forget()
        return robot_library.PREFIX + entry, report
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog='python -m little_world.physics.importer',
                                     description='Bring a robot into your robot library from its URDF or MJCF file.')
    parser.add_argument('file', nargs='?', help='the robot\'s .urdf or MuJoCo .xml file')
    parser.add_argument('--name', help='what to call it (default: the name in the file)')
    parser.add_argument('--check', action='store_true', help='only say what importing it would do')
    parser.add_argument('--list', action='store_true', help='list the robots in your library')
    parser.add_argument('--remove', metavar='NAME', help='remove a robot from your library')
    args = parser.parse_args(argv)
    try:
        if args.list:
            print(f'Your robot library: {robot_library.root()}')
            for asset in robot_library.entries():
                meta = robot_library.metadata(asset)
                print(f'  {robot_library.name_of(asset):<24} {meta["title"]} ({len(meta["actuators"])} joints, {meta["mass"]:.3g} kg)')
            return 0
        if args.remove:
            robot_library.remove(robot_library.PREFIX + args.remove)
            print(f'Removed {args.remove}.')
            return 0
        if not args.file:
            parser.error('give a file to import, or --list')
        if args.check:
            with tempfile.TemporaryDirectory() as scratch:
                _, _, report, _ = prepare(args.file, scratch, args.name)
            print(report.text())
            return 0
        asset, report = import_robot(args.file, args.name)
        print(f'Imported as {robot_library.name_of(asset)}.')
        print(report.text())
        return 0
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
