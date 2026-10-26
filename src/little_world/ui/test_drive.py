"""Test drive: chase view, live telemetry panel and run report (ADR 0012).

A workshop mixin. It reads state through `control/drive_telemetry.py` and keeps its
own session-only history; the Blueprint and the saved design are never touched.
"""
import time
from dataclasses import dataclass
from math import cos, radians, sin
import mujoco as mj
import numpy as np
from little_world.construction.structure import standing
from little_world.control.drive_telemetry import DriveTelemetry, display_name
from little_world.control.run_log import RunLog, RunSummary
from little_world.fields import FIELDS, railed
from little_world.fields.goals import GoalTracker, Line, TiltHold, Zone, between
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
_MARK = {'open': (.93, .93, .89, .85), 'met': (.37, .83, .69, 1.), 'kept': (.37, .83, .69, 1.),
         'missed': (.96, .50, .36, 1.), 'failed': (.96, .50, .36, 1.), 'lane': (.93, .93, .89, .45)}
_MARK = {k: np.array(v, dtype=np.float32) for k, v in _MARK.items()}
GOAL_WORDS = {'met': 'done', 'kept': 'kept', 'open': 'to do', 'missed': 'missed', 'failed': 'failed'}
LIGHT = (.86, .90, .93)


def static_verdict(peak, over, top):
    """A static test's result as a headline and a tone ('warn', 'ok' or 'muted'): where it
    went over, that it held to the top, or where the run was stopped."""
    if over is not None:
        return f'Tipped over at {over:.0f} deg', 'warn'
    if peak >= top - .5:
        return f'Held to {top:.0f} deg', 'ok'
    return f'Stopped at {peak:.0f} deg', 'muted'


def prediction_words(predicted, at_rail):
    """What the design predicted for a static test, in words."""
    if predicted is None:
        return 'No prediction: the design does not stand by itself'
    return f'Predicted {predicted:.0f} deg, {at_rail:.0f} at the rail'


@dataclass(frozen=True)
class RunRecord:
    """One finished run: where, what the log measured, and how the field's goals went."""
    number: int
    field: str
    summary: RunSummary
    goals: tuple = ()           # fields.goals.Result
    limit: tuple | None = None  # DriveTelemetry.speed_limit() at the end, for a vehicle
    anchored: bool = False      # bolted to the world: an arm's run, with no vehicle metrics
    # A static test (ADR 0020): (highest reading, where it went over or None, predicted,
    # predicted at the trip rail, the gauge's top), in degrees.
    static: tuple | None = None


class TestDrive:
    def init_test_drive(self):
        self.field_id = getattr(self, 'field_id', 'workshop')   # the test field (ADR 0013)
        self.drive_view = None      # 'chase', 'room' or 'free' while a machine is simulated
        self.chase = ChaseCamera()
        self.telemetry = None
        self.run_log = None
        self.drive_sample = None
        self.drive_touching = set()
        self.runs = []              # RunRecord, oldest first, this session only
        self.run_count = 0          # runs finished this session, including ones dropped from `runs`
        self.run_report = None      # the RunRecord shown after Stop until the user moves on
        self.goal_tracker = None
        self.last_goals = ()        # the last run's goal results, for the floor markings
        self.build_camera = None
        self.drive_clock = None
        self.trail = []             # the machine's path over the floor, kept after Stop
        self.trail_height = 0.
        self.onboard = -1           # the machine's first camera, shown as an inset while driving
        self.inset_camera = None
        self.inset_rect = None      # window coordinates of the inset, for its frame and label
        self.static = None          # a static test's live reading: [peak, predicted, at the rail]

    def drivable(self):
        """A machine the chase view suits: a drive to steer and a free base to move."""
        roots = [b for b in self.editor.bodies if b.parent is None]
        return bool(self.channels) and any(b.dynamic for b in roots)

    def start_test_drive(self):
        camera = self.camera
        self.build_camera = (camera.type, tuple(camera.lookat), camera.distance,
                             camera.azimuth, camera.elevation, self.follow)
        self.run_report = None
        field = FIELDS[self.field_id]
        self.telemetry = DriveTelemetry(self.backend, self.editor.blueprint, self.drive_control, ground=field.ground)
        self.static = None
        if field.reading is not None:
            stance = standing(self.editor.blueprint)
            tip = stance.tip(field.side) if stance is not None and field.side else None
            self.static = [0., tip, None if tip is None else railed(tip, stance.height)]
        self.run_log = RunLog()
        self.drive_sample = None
        self.drive_touching = set()
        self.drive_view = None
        self.trail = []
        self.trail_height = self.floor_top() + .003
        self.last_goals = ()
        root = next((b.id for b in self.editor.bodies if b.parent is None), None)
        self.goal_tracker = GoalTracker(field.goals, 'machine/' + root) if field.goals and root else None
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
            goals = self.goal_tracker.results(finished=True) if self.goal_tracker else ()
            self.run_count += 1
            static = None
            if self.static is not None:
                peak, predicted, at_rail = self.static
                over = self.goal_tracker.tipped_at if self.goal_tracker is not None else None
                static = (peak, over, predicted, at_rail, FIELDS[self.field_id].gauge_top)
            record = RunRecord(self.run_count, self.field_id, self.run_log.summary(), goals,
                               self.telemetry.speed_limit() if self.telemetry.channels else None,
                               anchored=self.telemetry.anchored, static=static)
            self.runs = (self.runs + [record])[-HISTORY:]
            self.run_report = record
            self.last_goals = goals
            self.active_tab = 'Edit'
        if self.build_camera is not None:
            kind, lookat, distance, azimuth, elevation, follow = self.build_camera
            self.camera.type = kind
            self.camera.lookat[:] = lookat
            self.camera.distance, self.camera.azimuth, self.camera.elevation = distance, azimuth, elevation
            self.follow = follow
        self.build_camera = None
        self.drive_view = None
        self.telemetry = self.run_log = self.goal_tracker = None
        if hasattr(self, 'end_live_disturbance'):
            self.end_live_disturbance()

    def sample_drive(self):
        if self.telemetry is None:
            return
        self.drive_sample = self.telemetry.sample()
        self.drive_touching = self.telemetry.touched()
        self.run_log.add(self.drive_sample, self.drive_touching)
        if self.goal_tracker is not None and self.state is not None:
            self.goal_tracker.update(self.state)
        if self.static is not None and self.state is not None:
            self.static[0] = max(self.static[0], FIELDS[self.field_id].reading(self.state))
        if self.telemetry.channels and self.static is None:
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

    def field_title(self):
        return FIELDS[self.field_id].title

    def field_commands(self):
        """The field's own motors, for a field that moves - a tilt table (ADR 0020) - and, each
        step of a run, a disturbance armed for it (ADR 0055)."""
        field = FIELDS.get(getattr(self, 'field_id', 'workshop'))
        if field is None or self.building:
            return {}
        if getattr(self, 'live_disturbance', None) is not None:
            self.tick_live_disturbance()
        return field.commands(self.state)

    def choose_field(self):
        if not self.building:
            self.status = 'Stop the run before changing the test field.'
            return
        titles = {f.title: f.id for f in FIELDS.values()}

        def apply(title):
            self.set_field(titles[title])
        self.choose('Test field', tuple(titles), apply)

    def set_field(self, field_id):
        """Rebuild the scene around the same design in another field (build mode only)."""
        if field_id not in FIELDS:
            raise ValueError(f'Unknown test field: {field_id}')
        if not self.building:
            raise ValueError('Stop the run before changing the test field')
        previous = self.field_id
        self.field_id = field_id
        try:
            self.rebuild()
        except Exception:
            self.field_id = previous
            self.rebuild()
            raise
        self.trail, self.last_goals, self.run_report = [], (), None
        self.home(True)
        field = FIELDS[field_id]
        self.status = field.title + ': ' + field.summary

    def goal_marks(self):
        """(goal, status) for what can be drawn on the floor: lines and small zones."""
        field = FIELDS[self.field_id]
        if self.goal_tracker is not None:
            results = {r.id: r.status for r in self.goal_tracker.results()}
        else:
            results = {r.id: r.status for r in self.last_goals}
        return [(g, results.get(g.id, 'open')) for g in field.goals if isinstance(g, (Line, Zone))]

    def draw_field_marks(self, scene=None):
        scene = self.render_scene if scene is None else scene
        field = FIELDS[self.field_id]
        if self.bench_open or not (field.goals or field.markings):
            return
        floor = self.floor_top() + .004
        segments = [(a, b, floor, _MARK['lane']) for a, b in field.markings]
        for goal, status in self.goal_marks():
            colour = _MARK[status]
            if isinstance(goal, Line):
                segments.append((goal.a, goal.b, floor, colour))
            else:
                (x0, y0, z0), (x1, y1, _) = goal.lo, goal.hi
                if x1 - x0 > 3. or y1 - y0 > 3.:
                    continue        # a half-plane, not a place: its line is a marking instead
                z = max(z0 + .024, floor) if z0 > floor else floor + .006
                corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
                for i in range(4):
                    segments.append((corners[i], corners[(i + 1) % 4], z, colour))
        start, end = np.zeros(3), np.zeros(3)
        for a, b, z, colour in segments:
            if scene.ngeom >= scene.maxgeom:
                return
            geom = scene.geoms[scene.ngeom]
            start[:] = a[0], a[1], z
            end[:] = b[0], b[1], z
            mj.mjv_initGeom(geom, mj.mjtGeom.mjGEOM_LINE, _ZERO, _ZERO, _EYE, colour)
            mj.mjv_connector(geom, mj.mjtGeom.mjGEOM_LINE, 4., start, end)
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
        """The Drive tab while physics runs, below the tab row. Sections are laid out
        top to bottom and a section that would not fit is left out, so a mobile
        manipulator in a field with goals still shows its goals and its arm."""
        if self.static is not None:
            self.draw_static_test_panel(ui, button, text, section, ww, wh)
            return
        s = self.drive_sample
        drive = bool(self.telemetry and self.telemetry.channels)
        anchored = bool(self.telemetry and self.telemetry.anchored)
        arm = tuple(self.joint_control.specs) if hasattr(self.joint_control, 'specs') else ()
        bottom = wh - 92
        top = 120
        section('TEST DRIVE' if drive else 'ARM RUN' if anchored else 'RUNNING', top)
        elapsed = 0. if s is None else s.time
        text(f'{elapsed:.1f} s  /  ideal sensors' + ('  /  paused' if self.paused else ''), 16, top + 18, 12, MUTED)
        speed = 0. if s is None else s.speed
        summary = self.run_log.summary() if self.run_log is not None else None
        if anchored:
            # Bolted to the world: speed, distance and stance say nothing about an arm.
            number = f'{elapsed:.1f}'
            text(number, 16, top + 36, 30)
            text('s', 22 + ui.width(number, 30), top + 50, 14, MUTED)
            text('anchored base', 16, top + 78, 12, MUTED)
            y = top + 98
            summary = None
        else:
            number = f'{abs(speed):.2f}'
            text(number, 16, top + 36, 30)
            text('m/s', 22 + ui.width(number, 30), top + 50, 14, MUTED)
            y = top + 78
        heading = 'forward' if speed > .05 else 'reverse' if speed < -.05 else 'standing'
        if summary is not None:
            tilt = 0. if s is None else s.tilt
            text(f'{heading}  /  top {summary.top_speed:.2f} m/s  /  tilt {tilt:.0f} deg', 16, y, 12,
                 WARN if tilt > 20 else (.86, .90, .93), 256)
            stance = None if s is None else s.margin
            stance_text = ('rocking on one support line' if stance is None else
                           f'stance margin {100 * stance:.1f} cm' + ('  (tipping)' if stance < 0 else ''))
            text(f'{summary.distance:.2f} m  /  ' + stance_text, 16, y + 20, 12,
                 WARN if stance is not None and stance < .01 else LIGHT, 256)
            y += 40
        # What the gripper holds is not a collision: name it apart from what is touched.
        observations = getattr(self, 'observations', None)
        held = {display_name(n) for n in observations.grasped()} if observations is not None and arm else set()
        touching = ', '.join(sorted(self.drive_touching - held))
        if held:
            text('holding: ' + ', '.join(sorted(held)), 16, y, 12, ACCENT, 256)
            y += 20
        # A vehicle touching things is news; an arm touching things is its job.
        text('touching: ' + touching if touching else 'touching nothing', 16, y, 12,
             WARN if touching and not anchored else (.86, .90, .93) if touching else MUTED, 256)
        y += 28
        if self.goal_tracker is not None:
            section('GOALS  /  ' + self.field_title(), y)
            y = self.draw_goal_lines(text, self.goal_tracker.results(), y + 20, bottom) + 8
        if drive and s is not None and y + 20 + 36 <= bottom:
            section('MOTORS  /  speed and torque', y)
            y += 20
            compact = len(s.motors) > 2 or bool(arm)
            for motor in s.motors:
                if y + (30 if compact else 36) > bottom:
                    break
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
            for warning, show in (('A motor is giving all it can.', any(m.saturated for m in s.motors)),
                                  ('Wheels slipping: the treads outrun the floor.', any(m.slipping for m in s.motors))):
                if show and y + 16 <= bottom:
                    text(warning, 16, y, 11, WARN, 256)
                    y += 16
            y += 8
        if arm and y + 20 + 18 <= bottom:
            section('ARM  /  keys and joint angles', y)
            y += 20
            for spec in arm:
                if y + 18 > bottom:
                    break
                values = []
                for name in spec.actuators[:2]:
                    try:
                        value, unit = self.joint_control.display_position(name)
                    except (KeyError, AttributeError):
                        continue
                    values.append(f'{round(value):d}' + (' deg' if unit == 'deg' else ' %'))  # no "-0"
                text(f'{spec.positive_key}/{spec.negative_key}', 16, y, 12, ACCENT)
                text(spec.label or spec.id, 58, y, 12, (.86, .90, .93), 140)
                reading = ' / '.join(values)
                text(reading, 272 - ui.width(reading, 11), y + 1, 11, MUTED)
                y += 18
            y += 8
        if drive and y + 58 <= bottom:
            limit, source, alone = self.telemetry.speed_limit()
            section('WHAT SETS THE TOP SPEED', y)
            if source == 'drive assist':
                text(f'Drive assist setting: {limit:.2f} m/s', 16, y + 20, 12)
                text(f'The motors alone could reach {alone:.2f} m/s' if alone else
                     'Ideal motors: no speed limit of their own', 16, y + 38, 11, MUTED, 256)
            else:
                text(f'Motor no-load speed: {limit:.2f} m/s', 16, y + 20, 12)
                text('Datasheet speed at the wheel; load lowers it', 16, y + 38, 11, MUTED, 256)
            y += 66
        if self.goal_tracker is None and y + 58 <= bottom:
            section('KEYS', y)
            if drive:
                text('W / S drive    A / D turn    P pause', 16, y + 20, 12, max_width=256)
                text('F chase or room view    Enter stop', 16, y + 38, 12, max_width=256)
            else:
                text('Operate or Program move the joints.', 16, y + 20, 12, max_width=256)
                text('P pause    Enter stop', 16, y + 38, 12, max_width=256)
        button('Stop and redesign', 12, wh - 78, 264, self.stop_and_redesign, tone='danger')

    def draw_goal_lines(self, text, results, y, bottom):
        """One line per goal: status word, label, time or detail. Stops before `bottom`."""
        for r in results:
            if y > bottom - 16:
                text('...', 16, y, 12, MUTED)
                return y + 18
            colour = ACCENT if r.status in ('met', 'kept') else WARN if r.status in ('missed', 'failed') else MUTED
            text(GOAL_WORDS[r.status], 16, y, 11, colour)
            detail = r.detail or ('' if r.time is None else f'{r.time:.1f} s')
            text(r.label + ('  /  ' + detail if detail else ''), 66, y, 12, (.86, .90, .93), 206)
            y += 18
        return y

    def draw_run_report(self, ui, button, text, section, ww, wh):
        record = self.run_report
        if record.static is not None:
            self.draw_static_report(ui, button, text, section, ww, wh)
            return
        r = record.summary
        title = FIELDS[record.field].title if record.field in FIELDS else record.field
        section(f'RUN {record.number} REPORT  /  {title}', 120)
        if record.anchored:
            met = sum(g.status in ('met', 'kept') for g in record.goals)
            text(f'{r.duration:.1f} s' + (f'  /  {met} of {len(record.goals)} goals' if record.goals else '  /  anchored arm'),
                 16, 140, 16, max_width=256)
            y = 166
        else:
            text(f'{r.duration:.1f} s  /  {r.distance:.2f} m driven', 16, 140, 16, max_width=256)
            text(f'top speed {r.top_speed:.2f} m/s  /  average {r.average_speed:.2f}', 16, 166, 12, max_width=256)
            text(f'max tilt {r.max_tilt:.0f} deg  /  motors at their limit {100 * r.saturated_share:.0f} %',
                 16, 186, 12, WARN if r.tipped else (.86, .90, .93), 256)
            text(f'wheels slipping {100 * r.slip_share:.0f} % of the time', 16, 206, 12,
                 WARN if r.slip_share > .1 else (.86, .90, .93), 256)
            y = 226
            if r.min_margin is not None:
                text(f'lowest stance margin {100 * r.min_margin:.1f} cm' + ('  (near tipping)' if r.min_margin < .01 else ''),
                     16, y, 12, WARN if r.min_margin < .01 else (.86, .90, .93), 256)
                y += 20
        touched = ', '.join(r.touched)
        text('touched: ' + touched if touched else 'touched nothing', 16, y, 12,
             WARN if touched and not record.anchored else (.86, .90, .93) if touched else MUTED, 256)
        y += 22
        if r.tipped:
            text('It tipped over.', 16, y, 12, WARN)
            y += 20
        if record.goals:
            y = self.draw_goal_lines(text, record.goals, y, wh - 250)
        earlier = [run for run in self.runs if run.field == record.field and run.number < record.number]
        if earlier:
            before = earlier[-1]
            delta = r.versus(before.summary)
            met = sum(g.status in ('met', 'kept') for g in record.goals)
            was = sum(g.status in ('met', 'kept') for g in before.goals)
            goals = f', goals {met - was:+d}' if record.goals else ''
            if record.anchored:
                line = f'vs run {before.number}: {delta["duration"]:+.1f} s{goals}'
            else:
                line = f'vs run {before.number}: {delta["distance"]:+.2f} m, top {delta["top_speed"]:+.2f} m/s{goals}'
            text(line, 16, y, 12, max_width=256)
            y += 20
        y = self.draw_report_actions(button, y + 8)
        y = self.draw_variations(ui, button, text, section, y, wh)
        y = self.draw_disturbances(ui, button, text, section, y, wh)
        # What set the top speed, while there is room above the status line for it.
        if record.limit is not None and record.limit[0] is not None and y + 54 <= wh - 40:
            limit, source, alone = record.limit
            text(f'Top speed set by the {source}: {limit:.2f} m/s', 16, y, 12, max_width=256)
            if source == 'drive assist':
                button('Adjust drive assist', 12, y + 20, 264, self.drive_settings_form, h=26)
                y += 28
            y += 26
        self.draw_session_runs(text, section, record, y, wh)

    def draw_report_actions(self, button, y):
        button('Redesign in Build stage', 12, y, 264, self.stop_and_redesign, h=36, tone='primary')
        button('Run again', 12, y + 44, 264, self.run_again, h=32)
        button('Back to editing', 12, y + 84, 264, lambda: setattr(self, 'run_report', None), h=28)
        return y + 122

    def draw_session_runs(self, text, section, record, y, wh):
        section('THIS SESSION', y)
        for i, run in enumerate(self.runs):
            if y + 20 + i * 19 > wh - 52:
                break
            text(self.run_line(run), 16, y + 20 + i * 19, 12, LIGHT if run is record else MUTED, 256)

    @staticmethod
    def run_line(run):
        """One run in the session list."""
        where = FIELDS[run.field].title if run.field in FIELDS else run.field
        if run.static is not None:
            peak, over, *_ = run.static
            return f'Run {run.number}  {where}  ' + (f'over at {over:.0f} deg' if over is not None else f'{peak:.0f} deg held')
        if run.anchored and run.goals:
            met = sum(g.status in ('met', 'kept') for g in run.goals)
            return f'Run {run.number}  {where}  {met}/{len(run.goals)} goals  {run.summary.duration:.1f} s'
        return f'Run {run.number}  {where}  {run.summary.distance:.2f} m  {run.summary.duration:.1f} s'

    # -- a static test: the machine holds still while the field moves (ADR 0020) --------

    def draw_gauge(self, ui, text, y, value, top, predicted=None, over=None):
        """A 0-to-top bar filled to `value`, a light tick where the design predicts the
        machine goes over and a warm one where it did; their labels on rows below."""
        x0, width = 16, 256
        ui.rect(x0, y, width, 8, (.14, .19, .23))
        ui.rect(x0, y, width * max(0., min(1., value / top)), 8, WARN if over is not None else ACCENT)
        row = y + 16
        for angle, colour, label in ((predicted, LIGHT, 'predicted {:.0f}'), (over, WARN, 'went over at {:.0f}')):
            if angle is None:
                continue
            px = x0 + width * max(0., min(1., angle / top))
            ui.rect(px - 1, y - 5, 2, 18, colour)
            words = label.format(angle)
            wide = ui.width(words, 11)
            text(words, max(x0, min(x0 + width - wide, px - wide / 2)), row, 11, colour)
            row += 16
        text(f'0 to {top:.0f} deg', x0, row, 10, MUTED)
        return row + 18

    def draw_hold_chips(self, ui, text, field, results, y):
        """A tilt test's goals as a row of chips, one per angle: held, missed or to come."""
        holds = [(g, r) for g, r in zip(field.goals, results) if isinstance(g, TiltHold)]
        if not holds:
            return y
        gap = 6
        w = (256 - gap * (len(holds) - 1)) / len(holds)
        for i, (goal, result) in enumerate(holds):
            x = 16 + i * (w + gap)
            colour = ACCENT if result.status == 'met' else WARN if result.status == 'missed' else (.30, .36, .41)
            ui.rect(x, y, w, 28, (.10, .14, .17))
            ui.rect(x, y + 25, w, 3, colour)
            label = f'{goal.angle:.0f}'
            text(label, x + (w - ui.width(label, 13)) / 2, y + 5, 13, LIGHT if result.status != 'open' else MUTED)
        text('held: still on its wheels as the table passed it', 16, y + 36, 11, MUTED, 256)
        return y + 56

    def draw_static_test_panel(self, ui, button, text, section, ww, wh):
        field = FIELDS[self.field_id]
        s = self.drive_sample
        peak, predicted, at_rail = self.static
        section(f'{field.title.upper()}  /  where it tips', 120)
        text(f'{0. if s is None else s.time:.1f} s  /  ideal sensors' + ('  /  paused' if self.paused else ''),
             16, 138, 12, MUTED)
        angle = field.reading(self.state) if self.state is not None else 0.
        number = f'{angle:.0f}'
        text(number, 16, 156, 30)
        text('deg, table angle', 22 + ui.width(number, 30), 170, 14, MUTED)
        over = self.goal_tracker.tipped_at if self.goal_tracker is not None else None
        y = self.draw_gauge(ui, text, 206, angle, field.gauge_top, at_rail, over)
        table = next((g.table for g in field.goals if isinstance(g, TiltHold)), None)
        root = self.telemetry.root if self.telemetry is not None else -1
        if table is not None and root >= 0 and self.state is not None:
            # Leaning off the table, not off the vertical: a machine on a 50 degree table
            # that still stands on all its wheels leans a few degrees at most.
            lean = between(tuple(float(v) for v in self.data.xquat[root]), self.state.bodies[table].pose.quaternion)
            text(f'leaning {lean:.0f} deg off the table', 16, y, 12, WARN if lean > 6. else LIGHT, 256)
            y += 20
        against = ', '.join(sorted(self.drive_touching))
        text('against: ' + against if against else 'against nothing but the table', 16, y, 12, MUTED, 256)
        y += 30
        if self.goal_tracker is not None:
            section('GOALS  /  held at each angle', y)
            y = self.draw_hold_chips(ui, text, field, self.goal_tracker.results(), y + 20)
        text('P pause    Enter stop', 16, y, 12, MUTED)
        button('Stop and redesign', 12, wh - 78, 264, self.stop_and_redesign, tone='danger')

    def draw_static_report(self, ui, button, text, section, ww, wh):
        record = self.run_report
        field = FIELDS[record.field]
        peak, over, predicted, at_rail, top = record.static
        section(f'RUN {record.number} REPORT  /  {field.title}', 120)
        headline, tone = static_verdict(peak, over, top)
        text(headline, 16, 140, 18, WARN if tone == 'warn' else ACCENT if tone == 'ok' else MUTED, 256)
        text(prediction_words(predicted, at_rail), 16, 168, 12, LIGHT, 256)
        y = 188
        if over is not None and at_rail is not None:
            text(f'{over - at_rail:+.1f} deg from the prediction at the rail', 16, y, 12, MUTED, 256)
            y += 18
        # The table goes on to its top after a machine has gone over: the gauge stops where it did.
        y = self.draw_gauge(ui, text, y + 14, peak if over is None else over, top, at_rail, over)
        y = self.draw_hold_chips(ui, text, field, record.goals, y + 4)
        earlier = [run for run in self.runs if run.field == record.field and run.number < record.number]
        if earlier:
            text('vs ' + self.run_line(earlier[-1]), 16, y, 12, MUTED, 256)
            y += 20
        y = self.draw_report_actions(button, y + 6)
        y = self.draw_variations(ui, button, text, section, y, wh)
        y = self.draw_disturbances(ui, button, text, section, y, wh)
        self.draw_session_runs(text, section, record, y, wh)

    def last_run_line(self):
        """One line for the Build stage, so the last result stays in view while redesigning."""
        if not self.runs:
            return None
        record = self.runs[-1]
        r = record.summary
        if record.static is not None:
            peak, over, predicted, at_rail, top = record.static
            where = FIELDS[record.field].title if record.field in FIELDS else record.field
            headline, _ = static_verdict(peak, over, top)
            return f'Last run on the {where.lower()}: {headline.lower()}' + (
                f', predicted {at_rail:.0f}' if at_rail is not None else '')
        if record.goals:
            met = sum(g.status in ('met', 'kept') for g in record.goals)
            where = FIELDS[record.field].title if record.field in FIELDS else record.field
            return f'Last run in {where}: {met} of {len(record.goals)} goals, {r.distance:.2f} m in {r.duration:.1f} s'
        touched = ', '.join(r.touched) if r.touched else 'nothing'
        return (f'Last run: {r.distance:.2f} m in {r.duration:.1f} s, top {r.top_speed:.2f} m/s, '
                f'touched {touched}')

    def last_run_troubled(self):
        if not self.runs:
            return False
        record = self.runs[-1]
        if record.static is not None:     # tipping is what a static test is for, not a trouble
            return False
        return bool(record.summary.touched) or record.summary.tipped or any(
            g.status in ('missed', 'failed') for g in record.goals)

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
