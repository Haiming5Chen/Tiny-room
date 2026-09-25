"""Contracts for the test drive: chase view, live telemetry and the run report (ADR 0012).

The defect: SIMULATE showed the robot from 5.4 m, about 2 % of the viewport, beside a
panel of disabled edit buttons; nothing said how fast it went or what limited it, and
Stop threw the run away, so no design could be compared with the one before it.
"""
from math import pi
import os
import pytest

from little_world.control.run_log import DriveSample, MotorSample, RunLog, RunSummary
from little_world.ui.chase_camera import ChaseCamera, wrap


# -- the run log: plain arithmetic ------------------------------------------------------

def sample(t, x, y=0., speed=0., tilt=0., saturated=False):
    motor = MotorSample("left", 60., 330., .1, .1 if saturated else .5, saturated)
    return DriveSample(t, (x, y, .05), speed, tilt, (motor,))


def test_distance_is_the_path_driven_not_the_displacement():
    log = RunLog()
    for i, (x, y) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))):
        log.add(sample(i * .5, x, y, speed=2.))
    s = log.summary()
    assert s.distance == pytest.approx(4.) and s.displacement == pytest.approx(0.)
    assert s.duration == pytest.approx(2.) and s.top_speed == 2.
    assert s.average_speed == pytest.approx(2.)


def test_standing_still_does_not_add_up_to_a_journey():
    log = RunLog()
    for i in range(600):  # ten seconds of sub-millimetre shimmer at 60 frames a second
        log.add(sample(i / 60, .0004 * (-1) ** i, .0003 * (-1) ** (i // 2)))
    assert log.summary().distance < .005


def test_tilt_saturation_share_and_what_was_touched():
    log = RunLog()
    log.add(sample(0., 0., tilt=2.), touched={"pickup stand"})
    log.add(sample(.5, .1, tilt=12., saturated=True), touched={"red block"})
    log.add(sample(1., .2, tilt=3.))
    s = log.summary()
    assert s.max_tilt == 12. and not s.tipped
    assert s.saturated_share == pytest.approx(.5), "saturated from 0.5 s until the next sample"
    assert s.touched == ("pickup stand", "red block")
    assert RunSummary(max_tilt=75.).tipped


def test_slip_is_the_tread_outrunning_the_floor():
    spinning = MotorSample("left", 60., 330., .5, .5, True, .26)
    rolling = MotorSample("left", 60., 330., .1, .5, False, .01)
    assert spinning.slipping and not rolling.slipping
    log = RunLog()
    log.add(DriveSample(0., (0., 0., 0.), 0., 0., (rolling,)))
    log.add(DriveSample(1., (0., 0., 0.), 0., 0., (spinning,)))
    log.add(DriveSample(4., (0., 0., 0.), 0., 0., (rolling,)))
    assert log.summary().slip_share == pytest.approx(.75)


def test_paused_frames_add_nothing_and_time_cannot_run_backwards():
    log = RunLog()
    log.add(sample(1., 0.))
    log.add(sample(1., .3))            # same simulated time: a paused frame
    assert log.summary().distance == 0. and log.samples == 1
    with pytest.raises(ValueError):
        log.add(sample(.5, 0.))


def test_a_run_is_compared_with_the_one_before():
    first, second = RunSummary(duration=4., distance=1.2, top_speed=.40), RunSummary(duration=4., distance=1.5, top_speed=.43)
    delta = second.versus(first)
    assert delta["distance"] == pytest.approx(.3) and delta["top_speed"] == pytest.approx(.03)
    assert RunLog().summary() == RunSummary()


# -- the chase camera: smoothing without a renderer --------------------------------------

def test_angles_wrap_the_short_way():
    assert wrap(190.) == pytest.approx(-170.) and wrap(-181.) == pytest.approx(179.)


def test_the_chase_view_turns_the_short_way_and_settles_behind_the_machine():
    cam = ChaseCamera(distance=1.)
    cam.reset((0., 0., 0.), 179.)
    seen = []
    for _ in range(240):
        _, azimuth, _, _ = cam.update((0., 0., 0.), -179., 1 / 60)
        seen.append(azimuth)
    assert all(abs(wrap(a - 180.)) < 5. for a in seen), "2 degrees apart: never swing round through 0"
    assert abs(wrap(seen[-1] + 179.)) < .1


def test_the_users_orbit_stays_relative_to_the_heading():
    cam = ChaseCamera(distance=1.)
    cam.reset((0., 0., 0.), 0.)
    cam.orbit(30., -10.)
    for _ in range(300):
        _, azimuth, elevation, _ = cam.update((0., 0., 0.), 90., 1 / 60)
    assert abs(wrap(azimuth - 120.)) < .5 and elevation == pytest.approx(cam.elevation)
    cam.orbit(0., -200.)
    assert -85. <= cam.elevation <= -3.
    cam.zoom(100.)
    assert cam.distance <= 15.


def test_the_chase_view_follows_smoothly_and_catches_up():
    cam = ChaseCamera(distance=1.)
    cam.reset((0., 0., 0.), 0.)
    lookat, *_ = cam.update((1., 0., 0.), 0., 1 / 60)
    assert 0. < lookat[0] < .2, "a jump is eased, not snapped"
    for _ in range(60):
        lookat, *_ = cam.update((1., 0., 0.), 0., 1 / 60)
    assert lookat[0] > .99


def test_the_trail_keeps_corners_and_merges_straight_runs():
    from math import cos, sin, pi
    from little_world.ui.test_drive import TestDrive
    t = TestDrive()
    t.init_test_drive()
    for i in range(301):                      # 3 m straight, a point every centimetre
        t.extend_trail((i * .01, 0.))
    assert len(t.trail) == 2 and abs(t.trail[-1][0] - 3.) <= .02, "one segment, within a step of the end"
    for i in range(1, 48):                    # a quarter turn of radius 0.3 m
        a = i / 47 * pi / 2
        t.extend_trail((3. + .3 * sin(a), .3 - .3 * cos(a)))
    assert 4 < len(t.trail) < 20, len(t.trail)
    x, y = t.trail[-1]
    assert abs(x - 3.3) <= .02 and abs(y - .3) <= .02, "the trail keeps up with the machine"


# -- telemetry on the real platform -------------------------------------------------------

mujoco = pytest.importorskip("mujoco")
from little_world import Entity, World  # noqa: E402
from little_world.control.drive_telemetry import DriveTelemetry  # noqa: E402
from little_world.control.mujoco_drive import MujocoDrive  # noqa: E402
from little_world.core.drive_settings import DriveSettings  # noqa: E402
from little_world.core.scene import Scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.mobile_platform import mobile_platform_blueprint  # noqa: E402
from little_world.scenes.room import room_entity  # noqa: E402
from little_world.assets.real_motors import KIT_GEARMOTOR, PROFILES  # noqa: E402


def drive(scene_entities, seconds, targets=(5., 5.)):
    bp = mobile_platform_blueprint()
    backend = MujocoBackend()
    world = World(backend, Scene((*scene_entities, Entity("machine", bp))))
    world.start()
    control = MujocoDrive(backend, bp)
    telemetry = DriveTelemetry(backend, bp, control)
    log = RunLog()
    touched = set()
    for k in range(int(seconds / world.timestep)):
        world.step(control.step_commands(targets, world.timestep))
        if k % 8 == 0:
            s = telemetry.sample()
            now = telemetry.touched()
            touched |= now
            log.add(s, now)
    return world, telemetry, log, touched


def test_telemetry_reads_speed_motors_and_what_limits_the_top_speed():
    world, telemetry, log, _ = drive((room_entity(),), 2.5)
    with world:
        s = telemetry.sample()
        assist = DriveSettings().max_speed
        assert abs(s.speed - assist) / assist < .1, s.speed
        assert s.tilt < 10.
        assert len(s.motors) == 2 and {m.name for m in s.motors} == {"left", "right"}
        wheel = s.speed / .05 * 60 / (2 * pi)  # 100 mm tread wheels
        for m in s.motors:
            assert abs(abs(m.rpm) - wheel) / wheel < .15, (m.rpm, wheel)
            assert not m.slipping, m.slip
            assert m.no_load_rpm == PROFILES[KIT_GEARMOTOR].no_load_rpm
            assert abs(m.torque) <= m.available + 1e-9
        limit, source, motors_alone = telemetry.speed_limit()
        assert source == "drive assist" and limit == assist
        assert motors_alone == pytest.approx(330 * 2 * pi / 60 * .05, rel=1e-6)
        summary = log.summary()
        assert summary.displacement > .5, "driven, not jiggled"
        assert summary.distance == pytest.approx(summary.displacement, rel=.05), "a straight run"
        assert summary.top_speed <= assist * 1.1


def test_turning_on_the_spot_is_not_a_journey():
    """The platform's base origin is a chassis rail, 10 cm off-centre: tracking it would
    count a spin in place as distance. The machine's centre of mass barely moves."""
    world, telemetry, log, _ = drive((room_entity(),), 2., targets=(-2.5, 2.5))
    with world:
        assert abs(telemetry.heading()) > 30., "it did turn"
        assert log.summary().distance < .1, log.summary().distance


def test_touching_the_room_is_reported_by_name_and_the_floor_is_not():
    from little_world.scenes.workshop import workshop_scene
    room = [e for e in workshop_scene(Entity("machine", mobile_platform_blueprint())).entities if e.id != "machine"]
    world, telemetry, log, touched = drive(room, 3.)
    with world:
        assert "pickup stand" in touched, touched
        assert not any("floor" in name for name in touched)
        summary = log.summary()
        assert "pickup stand" in summary.touched
        assert summary.slip_share > .2 and summary.saturated_share > .2, \
            "pinned against the stand, the motors push flat out and the treads spin"


# -- the window: build, drive, stop, read, redesign ---------------------------------------

@pytest.mark.skipif(os.environ.get("LITTLE_WORLD_TEST_RENDER") != "1", reason="requires OpenGL")
def test_build_drive_stop_report_and_back_to_the_build_stage(monkeypatch, tmp_path):
    import time
    import glfw
    import numpy as np
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / "drive.json", mobile_platform_blueprint())
    app.open_bench()
    draw = app.draw
    step = {"n": 0, "t": 0.}
    build_view = {}

    def click(label):
        button = next(b for b in app.buttons if b.label == label)
        assert button.enabled, label
        app.events.append(button.action)

    def exercise():
        draw()
        n, now = step["n"], time.monotonic()
        if n == 0:
            build_view["lookat"] = tuple(app.camera.lookat)
            click("SIMULATE  >")
        elif n == 1:
            assert not app.building and app.drive_view == "chase"
            root = app.data.xpos[app.root_id]
            assert np.linalg.norm(np.array(app.camera.lookat) - root) < .3
            assert app.camera.distance < 2., "close enough to see the machine"
            assert not any(b.label == "Delete subtree" for b in app.buttons), "no disabled edit panel"
            app.key(app.window, glfw.KEY_W, 0, glfw.PRESS, 0)
            step["t"] = now
        elif n == 2:
            if now - step["t"] < 1.5:
                return
            assert app.drive_sample is not None and app.drive_sample.speed > .1
            app.key(app.window, glfw.KEY_W, 0, glfw.RELEASE, 0)
            click("STOP / RETURN TO BUILD")
        elif n == 3:
            assert app.building and app.drive_view is None
            assert app.run_report is not None and app.run_report.distance > .1
            assert tuple(app.camera.lookat) == pytest.approx(build_view["lookat"])
            click("Redesign in Build stage")
        elif n == 4:
            assert app.bench_open and len(app.runs) == 1
            glfw.set_window_should_close(app.window, True)
        step["n"] += 1

    monkeypatch.setattr(app, "draw", exercise)
    app.run(seconds=30)
    assert step["n"] == 5


@pytest.mark.skipif(os.environ.get("LITTLE_WORLD_TEST_RENDER") != "1", reason="requires OpenGL")
def test_a_machine_with_a_camera_shows_what_it_sees_while_driving(monkeypatch, tmp_path):
    import glfw
    from little_world.robots.two_wheel import two_wheel_blueprint
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / "eye.json", two_wheel_blueprint())
    draw = app.draw
    step = {"n": 0}

    def exercise():
        draw()
        n = step["n"]
        if n == 0:
            assert app.inset_rect is None, "not while building"
            app.key(app.window, glfw.KEY_ENTER, 0, glfw.PRESS, 0)
        elif n == 2:
            assert not app.building and app.onboard >= 0 and app.inset_rect is not None
            app.key(app.window, glfw.KEY_C, 0, glfw.PRESS, 0)
        elif n == 4:
            assert app.camera.type == __import__("mujoco").mjtCamera.mjCAMERA_FIXED
            assert app.inset_rect is None, "the main view already is the onboard camera"
            glfw.set_window_should_close(app.window, True)
        step["n"] += 1

    monkeypatch.setattr(app, "draw", exercise)
    app.run(seconds=20)
    assert step["n"] == 5
