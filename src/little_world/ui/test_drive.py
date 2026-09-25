"""Test drive: chase view, live telemetry panel and run report (ADR 0012).

A workshop mixin. It reads state through `control/drive_telemetry.py` and keeps its
own session-only history; the Blueprint and the saved design are never touched.
"""
import time
from math import cos, radians, sin
import mujoco as mj
import numpy as np
from little_world.control.drive_telemetry import DriveTelemetry
from little_world.control.run_log import RunLog
from .chase_camera import ChaseCamera

MUTED = (.49, .57, .63)
ACCENT = (.37, .83, .69)
WARN = (.96, .72, .38)
HISTORY = 5
TRAIL_STEP = .02     # metres the machine moves before the trail takes a new point
TRAIL_BEND = .004    # a point closer than this to the straight line on is merged into it
TRAIL_POINTS = 600   # kept after merging: straight runs cost one segment, curves a few
_ZERO = np.zeros(3)
_EYE = np.eye(3).ravel()
_TRAIL_COLOUR = np.array((.37, .83, .69, .9), dtype=np.float32)


class TestDrive:
    def init_test_drive(self):
        self.drive_view = None      # 'chase', 'room' or 'free' while a machine is simulated
        self.chase = ChaseCamera()
        self.telemetry = None
        self.run_log = None
        self.drive_sample = None
        self.drive_touching = set()
        self.runs = []              # RunSummary, oldest first, this session only
        self.run_count = 0          # runs finished this session, including ones dropped from `runs`
        self.run_report = None      # shown after Stop until the user moves on
        self.build_camera = None
        self.drive_clock = None
        self.trail = []             # the machine's path over the floor, kept after Stop
        self.trail_height = 0.
        self.run_limit = None       # what set the top speed in the last run (see speed_limit)
        self.onboard = -1           # the machine's first camera, shown as an inset while driving
        self.inset_camera = None
        self.inset_rect = None      # window coordinates of the inset, for its frame and label

    def drivable(self):
        """A machine the chase view suits: a drive to steer and a free base to move."""
        roots = [b for b in self.editor.bodies if b.parent is None]
        return bool(self.channels) and any(b.dynamic for b in roots)

    def start_test_drive(self):
        camera = self.camera
        self.build_camera = (camera.type, tuple(camera.lookat), camera.distance,
                             camera.azimuth, camera.elevation, self.follow)
        self.run_report = None
        self.telemetry = DriveTelemetry(self.backend, self.editor.blueprint, self.drive_control)
        self.run_log = RunLog()
        self.drive_sample = None
        self.drive_touching = set()
        self.drive_view = None
        self.trail = []
        self.trail_height = self.floor_top() + .003
        self.onboard = next((i for i in range(self.model.ncam)
                             if self.model.camera(i).name.startswith('machine/')), -1)
        if self.drivable() and self.telemetry.root >= 0:
            from little_world.construction.docking import world_bounds
            lo, hi = world_bounds(self.editor.blueprint)
            size = max(hi[0] - lo[0], hi[1] - lo[1], .1)
            self.chase = ChaseCamera(distance=max(.7, min(4., 3.2 * size)), elevation=-22.)
            self.drive_view = 'chase'
            self.follow = False
            camera.type = mj.mjtCamera.mjCAMERA_FREE
            self.chase.reset(self.telemetry.centre(), self.telemetry.heading())
            self.drive_clock = None
            self.update_drive_camera()
        self.sample_drive()

    def stop_test_drive(self):
        if self.run_log is not None and self.run_log.samples > 1:
            self.run_limit = self.telemetry.speed_limit() if self.telemetry.channels else None
            summary = self.run_log.summary()
            self.runs = (self.runs + [summary])[-HISTORY:]
            self.run_count += 1
            self.run_report = summary
            self.active_tab = 'Edit'
        if self.build_camera is not None:
            kind, lookat, distance, azimuth, elevation, follow = self.build_camera
            self.camera.type = kind
            self.camera.lookat[:] = lookat
            self.camera.distance, self.camera.azimuth, self.camera.elevation = distance, azimuth, elevation
            self.follow = follow
        self.build_camera = None
        self.drive_view = None
        self.telemetry = self.run_log = None

    def sample_drive(self):
        if self.telemetry is None:
            return
        self.drive_sample = self.telemetry.sample()
        self.drive_touching = self.telemetry.touched()
        self.run_log.add(self.drive_sample, self.drive_touching)
        if self.telemetry.channels:
            self.extend_trail(self.drive_sample.position[:2])

    def extend_trail(self, point):
        """Add a point to the trail, merging it into a straight run when it stays on one."""
        x, y = float(point[0]), float(point[1])
        trail = self.trail
        if trail and (x - trail[-1][0]) ** 2 + (y - trail[-1][1]) ** 2 < TRAIL_STEP ** 2:
            return
        if len(trail) >= 2:
            (ax, ay), (bx, by) = trail[-2], trail[-1]
            dx, dy = x - ax, y - ay
            length = (dx * dx + dy * dy) ** .5
            along = ((bx - ax) * dx + (by - ay) * dy) / length if length else 0.
            off = abs((bx - ax) * dy - (by - ay) * dx) / length if length else 0.
            if 0. < along < length and off < TRAIL_BEND:
                trail[-1] = (x, y)
                return
        trail.append((x, y))
        if len(trail) > TRAIL_POINTS:
            del trail[0]

    def floor_top(self):
        """Height of the room's floor surface, where the trail is drawn."""
        m, d = self.model, self.data
        for i in range(m.ngeom):
            if m.geom(i).name.endswith('/floor_geom') and m.geom_type[i] == mj.mjtGeom.mjGEOM_BOX:
                return float(d.geom_xpos[i][2] + m.geom_size[i][2])
        return 0.

    def draw_trail(self, scene=None):
        """The path of the last run as a line on the floor, so a veer or a spin shows."""
        scene = self.render_scene if scene is None else scene
        if len(self.trail) < 2 or self.bench_open:
            return
        z = self.trail_height
        start, end = np.array((0., 0., z)), np.array((0., 0., z))
        for (x0, y0), (x1, y1) in zip(self.trail, self.trail[1:]):
            if scene.ngeom >= scene.maxgeom:
                return
            geom = scene.geoms[scene.ngeom]
            start[0], start[1], end[0], end[1] = x0, y0, x1, y1
            mj.mjv_initGeom(geom, mj.mjtGeom.mjGEOM_LINE, _ZERO, _ZERO, _EYE, _TRAIL_COLOUR)
            mj.mjv_connector(geom, mj.mjtGeom.mjGEOM_LINE, 3., start, end)
            geom.category = mj.mjtCatBit.mjCAT_DECOR
            scene.ngeom += 1

    def clear_view(self, lookat, azimuth, elevation, distance):
        """Bring the chase camera in front of a wall or shelf between it and the machine."""
        a, e = radians(azimuth), radians(elevation)
        back = -np.array((cos(e) * cos(a), cos(e) * sin(a), sin(e)))
        clearance = max(.15, .45 * self.chase.distance / 3.2)   # about half the machine's size
        start = np.asarray(lookat, dtype=float) + back * clearance
        geom = np.array([-1], dtype=np.int32)
        hit = mj.mj_ray(self.model, self.data, start, back, None, 1, -1, geom)
        if 0 <= hit < distance - clearance:
            return max(.25, clearance + hit - .05)
        return distance

    def update_drive_camera(self):
        now = time.monotonic()
        dt = 0. if self.drive_clock is None else min(.25, now - self.drive_clock)
        self.drive_clock = now
        if self.drive_view != 'chase' or self.camera.type == mj.mjtCamera.mjCAMERA_FIXED:
            return
        # Aim a little above the machine so it sits in the lower middle of the view.
        target = self.telemetry.centre() + (0., 0., .06 * self.chase.distance)
        lookat, azimuth, elevation, distance = self.chase.update(target, self.telemetry.heading(), dt)
        distance = self.clear_view(lookat, azimuth, elevation, distance)
        self.camera.lookat[:] = lookat
        self.camera.azimuth, self.camera.elevation, self.camera.distance = azimuth, elevation, distance

    def toggle_drive_view(self):
        """F and the Follow button while driving: chase view <-> the room."""
        if self.drive_view == 'chase':
            self.home(True)
            self.drive_view = 'room'
            self.follow = True
            self.status = 'Room view. F returns to the chase view.'
        else:
            self.drive_view = 'chase'
            self.follow = False
            self.camera.type = mj.mjtCamera.mjCAMERA_FREE
            self.chase.reset(self.telemetry.centre(), self.telemetry.heading())
            self.status = 'Chase view. Drag to look around, scroll to zoom, F for the room.'

    def chase_mouse(self, dx, dy, height, right):
        """Mouse in the viewport while chasing. Returns True when it was handled."""
        if self.drive_view != 'chase' or self.camera.type == mj.mjtCamera.mjCAMERA_FIXED:
            return False
        if right:
            self.drive_view = 'free'   # panning means looking elsewhere; F comes back
            self.status = 'Free view. F returns to the chase view.'
            return False
        self.chase.orbit(-dx / height * 180., -dy / height * 180.)
        return True

    def chase_scroll(self, yoffset):
        if self.drive_view != 'chase' or self.camera.type == mj.mjtCamera.mjCAMERA_FIXED:
            return False
        self.chase.zoom(.9 ** yoffset)
        return True

    def stop_and_redesign(self):
        if not self.building:
            self.simulate()
        self.run_report = None
        self.open_bench()

    def run_again(self):
        self.run_report = None
        if self.building:
            self.simulate()

    # -- drawing ----------------------------------------------------------------------

    def draw_test_drive_panel(self, ui, button, text, section, ww, wh):
        """The Drive tab while physics runs, below the tab row."""
        s = self.drive_sample
        drive = bool(self.telemetry and self.telemetry.channels)
        top = 120
        section('TEST DRIVE' if drive else 'RUNNING', top)
        elapsed = 0. if s is None else s.time
        text(f'{elapsed:.1f} s  /  ideal sensors' + ('  /  paused' if self.paused else ''), 16, top + 18, 12, MUTED)
        speed = 0. if s is None else s.speed
        number = f'{abs(speed):.2f}'
        text(number, 16, top + 36, 30)
        text('m/s', 22 + ui.width(number, 30), top + 50, 14, MUTED)
        summary = self.run_log.summary() if self.run_log is not None else None
        heading = 'forward' if speed > .05 else 'reverse' if speed < -.05 else 'standing'
        if summary is not None:
            text(f'{heading}  /  top {summary.top_speed:.2f} m/s', 16, top + 78, 12)
            tilt = 0. if s is None else s.tilt
            text(f'{summary.distance:.2f} m driven  /  tilt {tilt:.0f} deg', 16, top + 98, 12,
                 WARN if tilt > 20 else (.86, .90, .93))
        touching = ', '.join(sorted(self.drive_touching))
        text('touching: ' + touching if touching else 'touching nothing', 16, top + 118, 12,
             WARN if touching else MUTED, 256)
        y = top + 146
        if drive:
            section('MOTORS  /  speed and torque', y)
            y += 20
            compact = len(s.motors) > 2 if s else False
            for motor in (s.motors if s else ()):
                rpm = abs(motor.rpm)
                limit = f' of {motor.no_load_rpm:g}' if motor.no_load_rpm else ''
                text(f'{motor.name.title()}  {rpm:.0f}{limit} rpm', 16, y, 12 if compact else 13, max_width=150)
                torque = f'{abs(motor.torque):.2f} of {motor.available:.2f} Nm'
                text(torque, 272 - ui.width(torque, 11), y + 2, 11, WARN if motor.saturated else MUTED)
                share = min(1., rpm / motor.no_load_rpm) if motor.no_load_rpm else 0.
                load = min(1., abs(motor.torque) / motor.available) if motor.available > 0 else 0.
                bar_y = y + (17 if compact else 20)
                ui.rect(16, bar_y, 124, 5, (.14, .19, .23))
                ui.rect(16, bar_y, 124 * share, 5, ACCENT)
                ui.rect(148, bar_y, 124, 5, (.14, .19, .23))
                ui.rect(148, bar_y, 124 * load, 5, WARN if motor.saturated else (.55, .66, .72))
                y += 30 if compact else 36
            if s and any(m.saturated for m in s.motors):
                text('A motor is giving all it can.', 16, y, 11, WARN)
                y += 16
            if s and any(m.slipping for m in s.motors):
                worst = max(m.slip for m in s.motors)
                text(f'Wheels slipping: tread {worst:.2f} m/s faster than the floor.', 16, y, 11, WARN, 256)
                y += 16
            limit, source, alone = self.telemetry.speed_limit()
            y += 8
            section('WHAT SETS THE TOP SPEED', y)
            if source == 'drive assist':
                text(f'Drive assist setting: {limit:.2f} m/s', 16, y + 20, 12)
                text(f'The motors alone could reach {alone:.2f} m/s' if alone else
                     'Ideal motors: no speed limit of their own', 16, y + 38, 11, MUTED, 256)
            else:
                text(f'Motor no-load speed: {limit:.2f} m/s', 16, y + 20, 12)
                text('Datasheet speed at the wheel; load lowers it', 16, y + 38, 11, MUTED, 256)
            y += 66
            section('KEYS', y)
            text('W / S drive    A / D turn    P pause', 16, y + 20, 12, max_width=256)
            text('F chase or room view    Enter stop', 16, y + 38, 12, max_width=256)
        else:
            section('KEYS', y)
            text('Operate or Program move the joints.', 16, y + 20, 12, max_width=256)
            text('P pause    Enter stop', 16, y + 38, 12, max_width=256)
        button('Stop and redesign', 12, wh - 78, 264, self.stop_and_redesign, tone='danger')

    def draw_run_report(self, ui, button, text, section, ww, wh):
        r = self.run_report
        number = self.run_count
        section(f'RUN {number} REPORT  /  ideal sensors', 120)
        text(f'{r.duration:.1f} s  /  {r.distance:.2f} m driven', 16, 140, 16, max_width=256)
        text(f'top speed {r.top_speed:.2f} m/s  /  average {r.average_speed:.2f}', 16, 166, 12, max_width=256)
        text(f'max tilt {r.max_tilt:.0f} deg  /  motors at their limit {100 * r.saturated_share:.0f} %',
             16, 186, 12, WARN if r.tipped else (.86, .90, .93), 256)
        text(f'wheels slipping {100 * r.slip_share:.0f} % of the time', 16, 206, 12,
             WARN if r.slip_share > .1 else (.86, .90, .93), 256)
        touched = ', '.join(r.touched)
        text('touched: ' + touched if touched else 'touched nothing', 16, 226, 12,
             WARN if touched else MUTED, 256)
        y = 248
        if r.tipped:
            text('It tipped over.', 16, y, 12, WARN)
            y += 20
        if number > 1:
            delta = r.versus(self.runs[-2])
            text(f'vs run {number - 1}: {delta["distance"]:+.2f} m, top speed {delta["top_speed"]:+.2f} m/s',
                 16, y, 12, max_width=256)
        button('Redesign in Build stage', 12, 282, 264, self.stop_and_redesign, h=36, tone='primary')
        button('Run again', 12, 326, 264, self.run_again, h=32)
        button('Back to editing', 12, 366, 264, lambda: setattr(self, 'run_report', None), h=28)
        if self.run_limit is not None and self.run_limit[0] is not None:
            limit, source, alone = self.run_limit
            text(f'Top speed set by the {source}: {limit:.2f} m/s', 16, 404, 12, max_width=256)
            if source == 'drive assist':
                button('Adjust drive assist', 12, 424, 264, self.drive_settings_form, h=26)
        section('THIS SESSION', 466)
        first = number - len(self.runs) + 1
        for i, run in enumerate(self.runs):
            line = f'Run {first + i}   {run.distance:.2f} m   top {run.top_speed:.2f} m/s   {run.duration:.1f} s'
            text(line, 16, 486 + i * 19, 12, (.86, .90, .93) if run is r else MUTED, 256)

    def last_run_line(self):
        """One line for the Build stage, so the last result stays in view while redesigning."""
        if not self.runs:
            return None
        r = self.runs[-1]
        touched = ', '.join(r.touched) if r.touched else 'nothing'
        return (f'Last run: {r.distance:.2f} m in {r.duration:.1f} s, top {r.top_speed:.2f} m/s, '
                f'touched {touched}')

    def render_onboard_inset(self, viewport, sx, sy):
        """What the machine's own camera sees, in the corner of the driving view.

        The same renderer and scene as the main view, drawn a second time from the
        camera component; no image processing, no sensor model."""
        self.inset_rect = None
        if self.building or self.onboard < 0 or self.camera.type == mj.mjtCamera.mjCAMERA_FIXED:
            return
        if self.inset_camera is None:
            self.inset_camera = mj.MjvCamera()
            self.inset_camera.type = mj.mjtCamera.mjCAMERA_FIXED
        self.inset_camera.fixedcamid = self.onboard
        w, h = 240, 180
        right = (viewport.left + viewport.width) / sx
        x, bottom = right - w - 14, 74
        rect = mj.MjrRect(int(x * sx), int(bottom * sy), int(w * sx), int(h * sy))
        mj.mjv_updateScene(self.model, self.data, self.option, None, self.inset_camera,
                           mj.mjtCatBit.mjCAT_ALL, self.render_scene)
        mj.mjr_render(rect, self.render_scene, self.context)
        self.inset_rect = (x, bottom, w, h)

    def draw_inset_frame(self, ui, text, wh):
        if self.inset_rect is None:
            return
        x, bottom, w, h = self.inset_rect
        top = wh - bottom - h
        for rx, ry, rw, rh in ((x - 2, top - 2, w + 4, 2), (x - 2, top + h, w + 4, 2),
                               (x - 2, top, 2, h), (x + w, top, 2, h)):
            ui.rect(rx, ry, rw, rh, (.37, .83, .69))
        ui.rect(x, top - 20, 112, 18, (.045, .065, .085, .85))
        text('ONBOARD CAMERA', x + 6, top - 18, 10, (.68, .82, .84))
