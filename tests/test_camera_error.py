"""How well must the camera be mounted? The table camera off its believed pose (ADR 0039,
FR-021).

The program reads its pictures by where it believes the camera stands. A stand set up by
hand is off by millimetres, a bumped one by degrees, and every point is then read off by as
much: a camera shifted by d sees the cube -d away; turned by a small angle, it sees it swung
about the camera by that angle times its distance, 0.88 m here. First the error and the
closed form, then the camera moved in MuJoCo and read as believed, then the runs on either
side of where fetching stops.
"""
import numpy as np
import pytest

from little_world.fields.variation import CameraError
from little_world.perception.calibration import seen, turned


def test_a_camera_error_is_millimetres_and_degrees_and_says_what_it_is():
    assert CameraError().nominal and CameraError().describe() == 'where it is believed to be'
    error = CameraError((-.01, 0., .005), (1.5, -.5, 0.))
    assert not error.nominal
    assert error.describe() == '-10 mm along X, +5 mm along Z, panned +1.5 deg, tilted -0.5 deg'
    for bad in (dict(shift=(0., 0.)), dict(turn=(0., float('nan'), 0.))):
        with pytest.raises(ValueError):
            CameraError(**bad)


def test_the_closed_form_shifts_by_minus_d_and_swings_by_angle_times_distance():
    """A camera 0.88 m from the cube, looking 60 degrees down: a degree of pan moves the
    seen cube 15.3 mm sideways; a degree of tilt, 13.1 mm along and 7.8 mm down."""
    c = np.array((2.2938, 0., .8892))
    back = np.array((.5, 0., np.sqrt(.75)))            # the camera looks along -z: 60 degrees down, towards -X
    right = np.array((0., 1., 0.))
    rotation = np.stack((right, np.cross(back, right), back), axis=1)      # columns: x right, y up, z back
    cube = np.array((1.84, 0., .14))
    assert np.allclose(seen(cube, c, rotation, shift=(.01, -.02, .003)), cube - (.01, -.02, .003))
    assert np.allclose(seen(cube, c, rotation), cube)
    pan = seen(cube, c, rotation, turn=(1., 0., 0.)) - cube
    tilt = seen(cube, c, rotation, turn=(0., 1., 0.)) - cube
    assert abs(pan[1]) == pytest.approx(.0153, abs=.0002) and abs(pan[0]) < .0003
    assert abs(tilt[0]) == pytest.approx(.0131, abs=.0002) and abs(tilt[2]) == pytest.approx(.0078, abs=.0002)
    assert np.allclose(turned(rotation, (0., 0., 0.)), rotation)
    assert np.allclose(turned(rotation, (90., 0., 0.))[:, 1], rotation[:, 1])      # pan keeps the up axis


def test_the_camera_moved_in_the_world_is_read_where_it_was_believed_and_the_closed_form_holds():
    """Ideal pictures: the sighting moves as the closed form says, within about a millimetre
    (the finder's own error); believed where it stands, nothing changes."""
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.inventory.sweep import design, eye
    from little_world.physics.mujoco_backend import MujocoBackend
    field = FIELDS['fetch']
    for shift, turn in (((-.01, 0., 0.), (0., 0., 0.)), ((0., 0., 0.), (1., 0., 0.)), ((0., 0., 0.), (0., 1., 0.))):
        backend = MujocoBackend()
        scene = field.scene(Entity('machine', design('mobile_manipulator')))
        with World(backend, scene) as world:
            world.start()
            camera = 'field/table_camera'
            believed = backend.camera_pose(camera)
            before = np.array(eye(backend, field, scene, ideal=True)('objects/fetch_cube', (1.84, 0., .14)).centre)
            same = eye(backend, field, scene, ideal=True, believed=believed)('objects/fetch_cube', (1.84, 0., .14))
            assert np.allclose(same.centre, before)
            backend.move_camera(camera, shift, turn)
            position, rotation = backend.camera_pose(camera)
            assert np.allclose(position, believed[0] + shift) and np.allclose(rotation, turned(believed[1], turn))
            after = np.array(eye(backend, field, scene, ideal=True, believed=believed)('objects/fetch_cube',
                                                                                       (1.84, 0., .14)).centre)
            truth = backend.data.xpos[backend.model.body('objects/fetch_cube').id].copy()
            assert np.linalg.norm((after - before) - (seen(truth, *believed, shift, turn) - truth)) < .0015
            with pytest.raises(ValueError):
                backend.move_camera('field/nowhere', shift, turn)
            with pytest.raises(ValueError):
                backend.move_camera(camera, (0., 0.), turn)


def test_fetching_holds_with_the_camera_panned_one_and_a_half_degrees_and_not_two():
    """The onset as designed: panned 1.5 degrees the cube is seen 23 mm sideways and still
    fetched; 2 degrees, 30 mm - past the jaws' reach across - and it is not."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run, solve
    bp = design('mobile_manipulator')
    program = solve('fetch', bp)
    held = run('fetch', bp, program=program, camera_error=CameraError(turn=(1.5, 0., 0.)))
    assert all(r.status in ('met', 'kept') for r in held.results), held.message
    lost = run('fetch', bp, program=program, camera_error=CameraError(turn=(2., 0., 0.)))
    assert lost.result('delivered').status == 'missed'
    assert abs(held.seen[-1][2][1] - held.seen[-1][3][1]) == pytest.approx(.0225, abs=.002)
