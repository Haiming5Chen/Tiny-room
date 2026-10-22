"""Contracts for robots brought in from their own description files (ADR 0044, FR-031).

The defect: Little World drove four Menagerie arms, each registered by hand. A robot that
does not exist yet - one a student designs in CAD and exports as a URDF - could not be
tried. MuJoCo reads a URDF itself, but it comes in with no motors, its root link fused into
the ground, its `package://` meshes not found and a misspelt attribute silently dropped.

The robots here are made in the tests: a two-link arm with a mesh in a ROS package, a
parallel gripper whose second finger mimics the first, and the shipped UR5e's own file.
Each test has an empty robot library of its own (tests/conftest.py).
"""
import struct

import numpy as np
import pytest

from little_world.assets import robot_library
from little_world.physics.importer import ImportFailed, import_robot, main

STEP = .002


def stl(path, sx, sy, sz):
    """A binary STL box, sx by sy by sz metres, centred on its origin."""
    x, y, z = sx / 2, sy / 2, sz / 2
    v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    with open(path, 'wb') as out:
        out.write(b'\0' * 80 + struct.pack('<I', len(faces)))
        for face in faces:
            out.write(struct.pack('<3f', 0, 0, 0))
            for i in face:
                out.write(struct.pack('<3f', *v[i]))
            out.write(b'\0\0')


def inertial(mass, centre, ixx, izz):
    return (f'<inertial><origin xyz="0 0 {centre}"/><mass value="{mass}"/>'
            f'<inertia ixx="{ixx}" iyy="{ixx}" izz="{izz}" ixy="0" ixz="0" iyz="0"/></inertial>')


def arm(effort=12, upper=inertial(1.5, .15, .012, .001), limit='limit', forearm_mesh='package://my_arm/meshes/forearm.stl'):
    """A 4.3 kg two-link arm: a shoulder and an elbow about y, no motors, a mesh forearm."""
    return f'''<robot name="my_arm">
  <link name="base_link">{inertial(2., .025, .003, .004)}
    <visual><origin xyz="0 0 0.025"/><geometry><cylinder radius="0.08" length="0.05"/></geometry></visual>
    <collision><origin xyz="0 0 0.025"/><geometry><cylinder radius="0.08" length="0.05"/></geometry></collision></link>
  <link name="upper_arm">{upper}
    <visual><origin xyz="0 0 0.15"/><geometry><box size="0.05 0.05 0.3"/></geometry></visual>
    <collision><origin xyz="0 0 0.15"/><geometry><box size="0.05 0.05 0.3"/></geometry></collision></link>
  <link name="forearm">{inertial(.8, .125, .004, .0005)}
    <visual><origin xyz="0 0 0.125"/><geometry><mesh filename="{forearm_mesh}"/></geometry></visual>
    <collision><origin xyz="0 0 0.125"/><geometry><mesh filename="package://my_arm/meshes/forearm.stl"/></geometry></collision></link>
  <link name="tool0"/>
  <joint name="shoulder" type="revolute"><parent link="base_link"/><child link="upper_arm"/>
    <origin xyz="0 0 0.05"/><axis xyz="0 1 0"/><{limit} lower="-2.0" upper="2.0" effort="{effort}" velocity="2.0"/></joint>
  <joint name="elbow" type="revolute"><parent link="upper_arm"/><child link="forearm"/>
    <origin xyz="0 0 0.3"/><axis xyz="0 1 0"/><limit lower="-2.5" upper="2.5" effort="6" velocity="2.0"/></joint>
  <joint name="tool_joint" type="fixed"><parent link="forearm"/><child link="tool0"/><origin xyz="0 0 0.25"/></joint>
</robot>'''


def package(tmp_path, text):
    """The arm as a ROS package: src/my_arm/{package.xml, urdf/, meshes/}."""
    root = tmp_path / 'src' / 'my_arm'
    (root / 'urdf').mkdir(parents=True, exist_ok=True)
    (root / 'meshes').mkdir(exist_ok=True)
    (root / 'package.xml').write_text('<package format="2"><name>my_arm</name><version>0.1.0</version></package>')
    stl(root / 'meshes' / 'forearm.stl', .04, .04, .25)
    path = root / 'urdf' / 'my_arm.urdf'
    path.write_text(text)
    return path


GRIPPER = '''<robot name="Two-finger gripper">
  <link name="palm"><inertial><mass value="0.4"/><inertia ixx="1e-4" iyy="1e-4" izz="1e-4" ixy="0" ixz="0" iyz="0"/></inertial>
    <collision><geometry><box size="0.1 0.04 0.02"/></geometry></collision></link>
  <link name="left"><inertial><mass value="0.05"/><inertia ixx="1e-5" iyy="1e-5" izz="1e-5" ixy="0" ixz="0" iyz="0"/></inertial>
    <collision><origin xyz="0 0 0.03"/><geometry><box size="0.01 0.02 0.04"/></geometry></collision></link>
  <link name="right"><inertial><mass value="0.05"/><inertia ixx="1e-5" iyy="1e-5" izz="1e-5" ixy="0" ixz="0" iyz="0"/></inertial>
    <collision><origin xyz="0 0 0.03"/><geometry><box size="0.01 0.02 0.04"/></geometry></collision></link>
  <joint name="left_finger_joint" type="prismatic"><parent link="palm"/><child link="left"/>
    <origin xyz="-0.045 0 0.01"/><axis xyz="1 0 0"/><limit lower="0" upper="0.04" effort="20" velocity="0.1"/></joint>
  <joint name="right_finger_joint" type="prismatic"><parent link="palm"/><child link="right"/>
    <origin xyz="0.045 0 0.01"/><axis xyz="-1 0 0"/><limit lower="0" upper="0.04" effort="20" velocity="0.1"/>
    <mimic joint="left_finger_joint" multiplier="1" offset="0"/></joint>
</robot>'''


def scene(asset):
    """The robot on the Joint lab's table: (blueprint, backend, its keyboard control)."""
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.factory.scene import robot_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    bp = robot_blueprint(asset)
    backend = MujocoBackend()
    backend.compile(Scene((Entity('machine', bp),)), STEP)
    return bp, backend, MujocoKeyboardControl(backend, bp)


def run(backend, control, seconds):
    for _ in range(round(seconds / STEP)):
        backend.step(control.step_commands(STEP))


# -- a robot without motors becomes one to drive ----------------------------------------


def test_a_urdf_without_motors_gets_a_servo_on_each_joint_that_holds_a_pose_against_its_weight(tmp_path):
    from little_world.assets.robot_models import metadata
    asset, report = import_robot(package(tmp_path, arm()))
    assert asset == 'user:my_arm'
    meta = metadata(asset)
    assert meta['actuators'] == ['servo_shoulder', 'servo_elbow'] and meta['units'] == ['deg', 'deg']
    assert meta['root'] == 'base_link', "the root link is the robot's base, not fused into the ground"
    assert meta['mass'] == pytest.approx(4.3) and meta['tool'][0] == 'tool0'
    assert any('a position servo on each of its 2 driven joints' in t.lower() for t in report.of('added'))
    assert (robot_library.folder(asset) / 'assets').iterdir(), "the mesh is copied with the model"
    _, backend, control = scene(asset)
    goal = {'servo_1': 60., 'servo_2': -40.}
    for name, angle in goal.items():
        control.set_position_target(name, angle)
    within = None
    for k in range(1000):
        backend.step(control.step_commands(STEP))
        off = max(abs(control.display_position(n)[0] - a) for n, a in goal.items())
        if within is None and off < 1.:
            within = (k + 1) * STEP
    # Held out at 60 degrees, the arm's weight pulls on both joints; each servo was made
    # stiff enough to hold within half a degree of where it is sent.
    assert off < .5 and within is not None and within < 1.


def test_the_files_effort_limit_is_its_servos_strength(tmp_path):
    asset, report = import_robot(package(tmp_path, arm(effort=3)))
    assert any("'shoulder' can push at most 3 N m" in t and 'it will sag there' in t for t in report.of('warning'))
    _, backend, control = scene(asset)
    control.set_position_target('servo_1', 90.)
    run(backend, control, 2.)
    m, d = backend.model, backend.data
    dof = m.jnt_dofadr[m.joint(backend.servo_joint_names['machine/servo_1']).id]
    assert abs(d.qfrc_actuator[dof]) <= 3 + 1e-6, "the servo pushes no harder than the file allows"
    assert control.display_position('servo_1')[0] > 100, "too weak to hold the arm out, it sags past"


def test_a_mimic_slide_follows_its_leader_and_a_slide_is_driven_in_millimetres(tmp_path):
    from little_world.assets.robot_models import metadata
    from little_world.programming.program import Block, Program
    path = tmp_path / 'stage.urdf'
    # The gripper's two slides, named as a double stage's rather than as fingers (a gripper
    # is driven by how closed it is: ADR 0047, below).
    path.write_text(GRIPPER.replace('_finger_joint', '_slide').replace('Two-finger gripper', 'Double stage'))
    asset, report = import_robot(path)
    assert asset == 'user:double-stage'
    meta = metadata(asset)
    assert meta['servo_joints'] == ['left_slide'] and meta['units'] == ['mm'] and meta['gripper'] is None
    assert any("'right_slide' follows 'left_slide'" in t for t in report.of('added'))
    bp, backend, control = scene(asset)
    control.set_position_target('servo_1', 30.)
    run(backend, control, 1.)
    right = backend.model.joint('machine/root__robot_right_slide').id
    assert control.display_position('servo_1') == (pytest.approx(30., abs=.5), 'mm')
    assert 1000 * backend.data.qpos[backend.model.jnt_qposadr[right]] == pytest.approx(30., abs=.5)
    Program((Block('move', 'joint_1', 30., 1.),)).validate(bp)
    with pytest.raises(ValueError, match='limits'):
        Program((Block('move', 'joint_1', 50., 1.),)).validate(bp)   # 40 mm is all it opens


def test_a_menagerie_arm_imported_from_its_own_file_keeps_its_servos_and_moves_as_the_shipped_one():
    from little_world.assets.robot_models import metadata, model_path
    asset, report = import_robot(model_path('ur5e'), 'UR5e copy')
    assert asset == 'user:ur5e-copy'
    assert not report.of('added') or not any('servo on each' in t for t in report.of('added'))
    assert any('6 actuators of its own' in t for t in report.of('found'))
    assert metadata(asset)['actuators'] == metadata('ur5e')['actuators']
    assert np.allclose(metadata(asset)['home'], metadata('ur5e')['home'])
    paths = []
    for robot in ('ur5e', asset):
        _, backend, control = scene(robot)
        for i, angle in enumerate((-60., -80., 70., -100., -80., 20.)):
            control.set_position_target(f'servo_{i + 1}', angle)
        path = []
        for _ in range(500):
            backend.step(control.step_commands(STEP))
            path.append([control.display_position(f'servo_{i + 1}')[0] for i in range(6)])
        paths.append(np.array(path))
    assert np.abs(paths[0] - paths[1]).max() < .5, "the importer added nothing to a model with actuators"


def test_an_imported_arm_runs_a_block_program(tmp_path):
    from little_world.programming.execution import apply, joint_angles
    from little_world.programming.program import Block, Program, Runner
    asset, _ = import_robot(package(tmp_path, arm()))
    bp, backend, control = scene(asset)
    assert [c.label for c in bp.controllers] == ['Shoulder', 'Elbow'], "named after the file's joints"
    program = Program((Block('pose', value=30., duration=4., angles=(('joint_1', (45.,)), ('joint_2', (-30.,)))),
                       Block('move', 'joint_2', 20., 2.), Block(duration=.3)))
    program.validate(bp)
    runner = Runner()
    runner.start(program)
    for _ in range(round(10 / STEP)):
        apply(runner.tick(STEP, joint_angles(control)), control)
        backend.step(control.step_commands(STEP))
        if runner.state != 'running':
            break
    assert runner.state == 'completed', runner.message
    assert control.display_position('servo_1')[0] == pytest.approx(45., abs=.5)
    assert control.display_position('servo_2')[0] == pytest.approx(20., abs=.5)


def test_an_imported_arms_tool_goes_where_it_is_sent(tmp_path):
    from little_world.control.tool_motion import ToolMotion
    asset, _ = import_robot(package(tmp_path, arm()))
    bp, backend, control = scene(asset)
    control.set_position_target('servo_1', 30.)
    control.set_position_target('servo_2', 60.)
    run(backend, control, 1.)
    motion = ToolMotion(backend, bp, control)
    assert backend.model.body(motion.body).name.endswith('tool0'), "the link named like a tool"
    start = motion.tool()[0].copy()
    short = motion.jog(forward=.03, up=-.02, hold_angle=False)
    assert short <= .002
    path = []
    for _ in range(round(1. / STEP)):
        backend.step(control.step_commands(STEP))
        path.append(motion.tool()[0].copy())
    forward, left, up = motion.frame()
    moved = path[-1] - start
    assert (moved @ forward, moved @ left, moved @ up) == pytest.approx((.03, 0., -.02), abs=.002)
    # Not along a straight line: each servo takes its joint to its new angle at its own pace,
    # and the tool bows some 10 mm off the line on the way (moving the tool itself is FR-032).


def test_links_that_already_overlap_at_home_are_kept_from_colliding(tmp_path):
    from little_world.assets.robot_models import metadata
    post = ('<link name="post">' + inertial(.1, 0, 1e-5, 1e-5) + '<collision><origin xyz="0 0 0.45"/>'
            '<geometry><box size="0.02 0.02 0.02"/></geometry></collision></link>'
            '<joint name="post_joint" type="fixed"><parent link="base_link"/><child link="post"/></joint></robot>')
    asset, report = import_robot(package(tmp_path, arm().replace('</robot>', post)))
    assert metadata(asset)['exclude'] == [['forearm', 'post']]
    assert any("'forearm' and 'post' already touch at the home pose" in t for t in report.of('added'))
    _, backend, control = scene(asset)
    run(backend, control, .5)
    assert abs(control.display_position('servo_2')[0]) < .1, "the forearm is not pushed off the post"


# -- what the import says -------------------------------------------------------------


def test_what_a_file_leaves_unsaid_is_reported_in_plain_words(tmp_path):
    text = arm(upper='', limit='limit').replace('effort="12"', 'efort="12"')
    text = text.replace('package://my_arm/meshes/forearm.stl"/></geometry></visual>',
                        'package://my_arm/meshes/forearm.dae"/></geometry></visual>')
    path = package(tmp_path, text)
    (path.parent.parent / 'meshes' / 'forearm.dae').write_text('<COLLADA/>')
    asset, report = import_robot(path)
    warnings = '\n'.join(report.of('warning'))
    assert "limit in joint 'shoulder': 'efort' is not a URDF attribute of <limit>" in warnings
    assert "'shoulder' has no effort limit in the file" in warnings
    assert "Link 'upper_arm' has no mass in the file" in warnings and '0.75 kg' in warnings
    assert "Link 'forearm': its visual mesh forearm.dae is a .dae file" in warnings
    assert asset == 'user:my_arm', "each of these is a warning; the robot still imports"


@pytest.mark.parametrize('name, text, words', [
    ('arm.urdf.xacro', '<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="a"/>', 'xacro'),
    ('page.urdf', '<html><body/></html>', 'neither a URDF'),
    ('broken.urdf', '<robot name="a"><link name="b">', 'not readable XML'),
    ('float.urdf', '<robot name="a"><link name="b"/><link name="c"/><joint name="j" type="floating">'
                   '<parent link="b"/><child link="c"/></joint></robot>', "'j' is floating"),
    ('still.urdf', '<robot name="a"><link name="b"><collision><geometry><box size="1 1 1"/></geometry>'
                   '</collision></link></robot>', 'no joints'),
    ('motors.xml', '<mujoco><worldbody><body name="b"><joint name="j" axis="0 1 0"/><geom size=".1" mass="1"/>'
                   '</body></worldbody><actuator><motor joint="j"/></actuator></mujoco>', 'not a position servo'),
])
def test_a_file_that_cannot_be_imported_says_why_and_leaves_nothing_behind(tmp_path, name, text, words):
    path = tmp_path / name
    path.write_text(text)
    with pytest.raises(ImportFailed, match=words):
        import_robot(path)
    assert robot_library.entries() == () and not any(robot_library.root().iterdir())


def test_a_missing_mesh_is_named(tmp_path):
    path = package(tmp_path, arm())
    (path.parent.parent / 'meshes' / 'forearm.stl').unlink()
    with pytest.raises(ImportFailed, match=r"Link 'forearm': its visual mesh 'package://my_arm/meshes/forearm.stl' is not there"):
        import_robot(path)


# -- the library ----------------------------------------------------------------------


def test_the_library_names_each_robot_never_overwrites_one_and_says_which_is_gone(tmp_path):
    from little_world.core.component import Body, Geometry
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.factory.scene import robot_blueprint
    from little_world.physics.mujoco_backend import MujocoBackend
    path = package(tmp_path, arm())
    first, _ = import_robot(path)
    second, _ = import_robot(path)
    assert (first, second) == ('user:my_arm', 'user:my_arm-2') and robot_library.entries() == (first, second)
    design = robot_blueprint(first)
    robot_library.remove(first)
    assert robot_library.entries() == (second,)
    with pytest.raises(ValueError, match="The robot 'my_arm' is not in your robot library"):
        MujocoBackend().compile(Scene((Entity('machine', design),)), STEP)
    for bad in ('user:../x', 'user:My Arm', 'user:', 'user:a/b', '/tmp/robot.urdf'):
        with pytest.raises(ValueError):
            Body('root', Geometry('box', (1, 1, 1)), 'metal', robot_asset=bad)
    Body('root', Geometry('box', (1, 1, 1)), 'metal', robot_asset='user:my_arm')   # a name, not a path


def test_library_robots_are_parts_and_the_command_line_imports_lists_and_removes(tmp_path, capsys):
    from little_world.assets.catalog import BY_ID, items
    path = package(tmp_path, arm())
    assert main(['--check', str(path)]) == 0 and robot_library.entries() == ()
    assert 'A position servo on each of its 2 driven joints' in capsys.readouterr().out
    assert main([str(path), '--name', 'Bench arm']) == 0
    assert robot_library.entries() == ('user:bench-arm',)
    assert BY_ID['user:bench-arm'].variant == 'real_robot' and 'user:bench-arm' in BY_ID
    assert items()[-1].id == 'user:bench-arm' and BY_ID['user:bench-arm'].blueprint().controllers
    main(['--list'])
    assert 'bench-arm' in capsys.readouterr().out
    assert main(['--remove', 'bench-arm']) == 0 and robot_library.entries() == ()
    assert main([str(tmp_path / 'nothing.urdf')]) == 1


# -- in the app -----------------------------------------------------------------------


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires native window')
def test_the_joint_lab_imports_a_robot_from_its_file_and_runs_it(tmp_path):
    import glfw
    from little_world.construction.editor import starter_blueprint
    from little_world.ui.workshop import Workshop
    path = package(tmp_path, arm())
    app = Workshop(tmp_path / 'kit.json', starter_blueprint())
    app.factory_recipe_path = tmp_path / 'cell.json'
    original_draw, finished = app.draw, False

    def use():
        nonlocal finished
        original_draw()
        if finished:
            return
        app.switch_workspace('Real')
        real = app.active_workspace
        real.reset_cell()
        real.choose_robot()
        assert real.IMPORT in real.dialog['query']
        real.dialog = None
        real.import_robot_form()
        real.dialog['fields'][0][1] = str(tmp_path / 'missing.urdf')
        real.apply_form()
        assert 'There is no file' in real.dialog['error'], "a failed import says why, in the form"
        real.dialog['fields'][0][1] = str(path)
        real.apply_form()
        assert real.dialog is None and real.robot_asset == 'user:my_arm' and real.joint_lab
        assert 'Imported my_arm' in real.status
        real.draw()
        assert any(b.label == 'Robot: my_arm' for b in real.buttons)
        real.choose_robot()
        assert 'my_arm (yours: my_arm)' in real.dialog['query']
        real.dialog = None
        app.switch_workspace('Anime')
        app.active_workspace.files_dropped([str(tmp_path / 'notes.txt')])
        assert 'Drop a robot' in app.active_workspace.status and app.app_mode == 'Anime'
        app.active_workspace.files_dropped([str(path)])   # dropped on the window: imported again
        real = app.active_workspace
        assert real.app_mode == 'Real' and real.robot_asset == 'user:my_arm-2'
        real.joint_example()
        real.start_program()
        for _ in range(400):
            real.tick_program()
            real.state = real.world.step(real.joint_commands())
        assert real.runner.state in ('running', 'completed')
        assert real.program_path.name == 'user-my_arm-2.program.json', 'a name the file system takes'
        real.reset_cell()
        finished = True
        glfw.set_window_should_close(app.window, True)
    app.draw = use
    app.run(60)
    assert finished


# -- a gripper in the file (ADR 0047) --------------------------------------------------

# A parallel gripper at the arm's end: two fingers sliding across the palm, the right one
# mimicking the left, closing along the elbow's axis (y) so that the elbow can turn what they
# hold over.
HAND = '''<link name="palm">{palm}<collision><geometry><box size="0.03 0.09 0.02"/></geometry></collision></link>
  <link name="left_finger">{finger}<collision><origin xyz="0 0 0.035"/><geometry><box size="0.02 0.01 0.05"/></geometry></collision></link>
  <link name="right_finger">{finger}<collision><origin xyz="0 0 0.035"/><geometry><box size="0.02 0.01 0.05"/></geometry></collision></link>
  <joint name="wrist_mount" type="fixed"><parent link="forearm"/><child link="palm"/><origin xyz="0 0 0.26"/></joint>
  <joint name="left_finger_joint" type="prismatic"><parent link="palm"/><child link="left_finger"/>
    <origin xyz="0 -0.035 0.01"/><axis xyz="0 1 0"/><limit lower="0" upper="0.03" effort="20" velocity="0.1"/></joint>
  <joint name="right_finger_joint" type="prismatic"><parent link="palm"/><child link="right_finger"/>
    <origin xyz="0 0.035 0.01"/><axis xyz="0 -1 0"/><limit lower="0" upper="0.03" effort="20" velocity="0.1"/>
    <mimic joint="left_finger_joint" multiplier="1" offset="0"/></joint>
</robot>'''.format(palm=inertial(.2, 0, 2e-4, 2e-4), finger=inertial(.03, .025, 1e-5, 1e-5))


def jaw_force(backend, jaw, other):
    """The force pressing `jaw` (a body) on `other`, summed over their contacts (N)."""
    import mujoco as mj
    m, d = backend.model, backend.data
    a, b = m.body(jaw).id, m.body(other).id
    total, f = 0., np.zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        if {int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])} == {a, b}:
            mj.mj_contactForce(m, d, i, f)
            total += f[0]
    return total


def test_a_gripper_in_the_file_is_found_and_its_grasp_blocks_hold_what_it_closes_on(tmp_path):
    """The arm with a parallel gripper at its end: the finger joint is found as a gripper,
    closing at the end of its travel where the fingers meet. A block program closes it on a box
    and checks the grasp as the pick-and-place programs do; the elbow then turns the box over a
    right angle, where only the jaws' grip holds it, and the box stays where it was held."""
    from little_world.assets.robot_models import blueprint, metadata
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.control.tool_motion import ToolMotion
    from little_world.core.blueprint import Blueprint
    from little_world.core.component import Body, Geometry, Transform
    from little_world.core.entity import Entity
    from little_world.core.scene import Scene
    from little_world.materials import WOOD
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.programming.execution import apply, joint_angles
    from little_world.programming.observations import Observations
    from little_world.programming.program import Block, Program, Runner
    asset, report = import_robot(package(tmp_path, arm().replace('</robot>', HAND)))
    meta = metadata(asset)
    assert meta['units'] == ['deg', 'deg', '%'] and meta['gripper']['channel'] == 2
    assert (meta['gripper']['open'], meta['gripper']['closed']) == (0., .03), "closed where the fingers meet"
    assert meta['gripper']['jaws'] == ['left_finger', 'right_finger'] and meta['tool'][0] == 'palm'
    assert meta['tool'][1] == pytest.approx([0., 0., .045]), "the tool point: between the jaws, above the palm"
    assert any("'left_finger_joint' closes a gripper - its fingers 60 mm apart open, 0 mm closed" in t
               and 'up to 10 N at each jaw (its effort in the file, 20 N)' in t for t in report.of('added'))
    bp = blueprint(asset)
    assert [c.label for c in bp.controllers][2] == 'Gripper close / open'
    # A 3 cm box on the palm between the open jaws, the arm upright at home.
    probe = MujocoBackend()
    probe.compile(Scene((Entity('machine', bp),)), STEP)
    x, y, z = (float(v) for v in sum(probe.data.xpos[probe.model.body(f'machine/root__robot_{side}_finger').id]
                                     for side in ('left', 'right')) / 2)
    objects = Blueprint((Body('box', Geometry('box', (.02, .03, .03)), 'wood', Transform((x, y, z + .016)),
                              dynamic=True),), (WOOD,))
    backend = MujocoBackend()
    backend.compile(Scene((Entity('machine', bp), Entity('objects', objects))), STEP)
    m, d = backend.model, backend.data
    control = MujocoKeyboardControl(backend, bp)
    seen = Observations(m, d, backend.robot_jaws)
    assert backend.robot_jaws == (('machine/root__robot_left_finger', 'machine/root__robot_right_finger'),)
    motion = ToolMotion(backend, bp, control)
    assert motion.jaws == ('servo_3',), "Tool mode's Open and Close drive the gripper"
    fingers = [d.geom_xpos[g] for g in range(m.ngeom) if m.body(int(m.geom_bodyid[g])).name.endswith('_finger')]
    assert np.linalg.norm(motion.tool()[0] - sum(fingers) / 2) < .001, "the tool point is between the jaws"
    run(backend, control, .3)
    assert control.display_position('servo_3') == (pytest.approx(0., abs=1.), '% closed')
    assert seen.grasped() == frozenset()
    palm, box = m.body('machine/root__robot_palm').id, m.body('objects/box').id
    held_at = lambda: d.xmat[palm].reshape(3, 3).T @ (d.xpos[box] - d.xpos[palm])
    program = Program((Block('action', 'joint_3', 1, 1.), Block('grasp', 'objects/box', duration=.5),
                       Block('pose', value=30., duration=5., angles=(('joint_2', (90.,)),)), Block(duration=1.)))
    program.validate(bp, ('objects/box',))
    runner, grasped_at = Runner(), None
    runner.start(program)
    while runner.state == 'running' and d.time < 15.:
        out = runner.tick(STEP, joint_angles(control), held=seen.grasped())
        if runner.index == 2 and grasped_at is None:      # the grasp is checked: the box is held
            grasped_at, closure = held_at(), control.display_position('servo_3')[0]
        control.clear()
        for key in apply(out, control):
            control.press(key)
        backend.step(control.step_commands(STEP))
    assert runner.state == 'completed', runner.message
    assert 45 < closure < 55, "stopped by the 3 cm box: half closed"
    assert control.display_position('servo_2')[0] == pytest.approx(90., abs=1.)
    assert seen.grasped() == {'objects/box'}
    assert all(palm not in (int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])) for c in d.contact[:d.ncon]), \
        "turned over, the box is off the palm: the jaws alone hold it"
    assert np.linalg.norm(held_at() - grasped_at) < .001, "and it stays where it was held"
    # The program's close went to 60 %: squeezing, short of its whole force. Sent fully closed,
    # the joint pushes with the file's 20 N, which the two jaws share (averaged over 0.2 s: the
    # held box rocks a milliradian between its eight contacts).

    def jaws():
        total = np.zeros(2)
        for _ in range(100):
            backend.step(control.step_commands(STEP))
            total += [jaw_force(backend, f'machine/root__robot_{side}_finger', 'objects/box') for side in ('left', 'right')]
        return tuple(total / 100)
    assert all(5. < f < 10. for f in jaws())
    control.set_position_target('servo_3', 100.)
    run(backend, control, .3)
    assert jaws() == (pytest.approx(10., abs=.2), pytest.approx(10., abs=.2))
    assert 45 < control.display_position('servo_3')[0] < 55, "and the jaws do not sink into the box"
    control.set_position_target('servo_3', 0.)
    run(backend, control, 1.)
    assert seen.grasped() == frozenset() and control.display_position('servo_3')[0] < 1.


CLAW = '''<robot name="Claw">
  <link name="palm">{heavy}<collision><geometry><box size="0.06 0.04 0.02"/></geometry></collision></link>
  <link name="fixed_jaw">{light}<collision><origin xyz="0 0 0.04"/><geometry><box size="0.01 0.03 0.06"/></geometry></collision></link>
  <link name="claw">{light}<collision><origin xyz="0 0 0.04"/><geometry><box size="0.01 0.03 0.06"/></geometry></collision></link>
  <joint name="jaw_mount" type="fixed"><parent link="palm"/><child link="fixed_jaw"/><origin xyz="0.025 0 0.01"/></joint>
  <joint name="claw_joint" type="revolute"><parent link="palm"/><child link="claw"/>
    <origin xyz="-0.025 0 0.01"/><axis xyz="0 1 0"/><limit lower="-0.3" upper="0.9" velocity="1"/></joint>
</robot>'''.format(heavy=inertial(.3, 0, 1e-4, 1e-4), light=inertial(.02, .04, 1e-5, 1e-5))


def test_a_claw_closing_on_a_fixed_jaw_squeezes_as_the_kit_gripper_when_its_file_gives_no_effort(tmp_path):
    """One hinged finger closing on a jaw fixed to the palm, with no effort in the file: the
    gripper is still found - the fixed jaw is the other jaw - and squeezes as the kit gripper
    does, 12 N at its jaw: a torque of that force times the finger's lever."""
    from little_world.assets.robot_models import metadata
    path = tmp_path / 'claw.urdf'
    path.write_text(CLAW)
    asset, report = import_robot(path)
    meta = metadata(asset)
    assert meta['units'] == ['%'] and meta['gripper']['jaws'] == ['claw', 'fixed_jaw']
    assert (meta['gripper']['open'], meta['gripper']['closed']) == (pytest.approx(-.3), pytest.approx(.9))
    line = next(t for t in report.of('added') if 'closes a gripper' in t)
    assert "up to 12 N at each jaw (the file gives no effort: the kit gripper's)" in line
    assert not any("'claw_joint' has no effort limit" in t for t in report.of('warning')), "said once, as the gripper's"
    bp, backend, control = scene(asset)
    servo = backend.model.actuator('machine/root__robot_servo_claw_joint').id
    assert backend.model.actuator_forcerange[servo][1] == pytest.approx(12. * .04, rel=.05), \
        "12 N at a jaw 4 cm from the hinge"
    control.set_position_target('servo_1', 100.)
    run(backend, control, 1.)
    # Its file lets the claw turn on past the fixed jaw: closing on nothing, it stops where the
    # jaws meet, 0.62 rad - 77 % of its travel - and presses them together.
    assert control.display_position('servo_1')[0] == pytest.approx(77., abs=1.)
    assert jaw_force(backend, 'machine/root__robot_claw', 'machine/root__robot_fixed_jaw') > 5.
