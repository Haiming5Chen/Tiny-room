"""The Guide tab's lessons: the first hour, checked by the app (ADR 0046, FR-033).

A workshop mixin. Each frame the active workspace tells the lessons what it sees (`lesson_facts`)
and every lesson whose check passes is finished, wherever the user is - the Anime workshop or
the Joint lab. One `Progress` is shared by all the window's workspaces (it lives on the host).
"""
import textwrap
from math import degrees
from pathlib import Path

from little_world import lessons

SAMPLE = Path(__file__).resolve().parents[1] / 'assets' / 'samples' / 'sample_arm.urdf'
AWAY = .05          # m: how far the tool must have been from the cube before the tool lesson counts
MUTED = (.6, .74, .77)
ACCENT = (.37, .83, .69)
WARN = (.96, .72, .38)


class LessonsPanel:
    @property
    def lesson_progress(self):
        host = self.workspace_host
        if getattr(host, '_lessons', None) is None:
            host._lessons = lessons.Progress()
        return host._lessons

    # -- what the window sees ----------------------------------------------------------

    def lesson_facts(self):
        """A lesson's view of the work so far, from this workspace."""
        real = getattr(self, 'factory_mode', False)
        field = '' if real else getattr(self, 'field_id', '')
        tracker = getattr(self, 'goal_tracker', None)
        results = tracker.results() if tracker is not None else getattr(self, 'last_goals', ())
        tool_off = None
        motion = getattr(self, 'tool_motion', None)
        if motion is not None and not self.building and field == 'pick_place':
            try:
                point = motion.tool()[0]
                off = float(sum((a - b) ** 2 for a, b in zip(point, self.data.xpos[self.model.body('objects/grasp_cube').id])) ** .5)
            except (KeyError, IndexError, ValueError):
                off = None
            # The arm lab starts with its jaws round the cube: the tool has to have left it first.
            host = self.workspace_host
            if off is not None and off > AWAY:
                host._tool_left = True
            tool_off = off if getattr(host, '_tool_left', False) else None
        moved, robot = 0., ''
        if real and getattr(self, 'joint_lab', False):
            robot = getattr(self, 'robot_asset', '') or ''
            control = getattr(self, 'joint_control', None)
            start = getattr(getattr(self, 'backend', None), '_initial_qpos', None)
            if robot.startswith('user:') and control is not None and start is not None and not self.building:
                for name in getattr(control, 'servos', {}):
                    q = control.channels[name][0]
                    delta = abs(float(self.data.qpos[q] - start[q]))
                    moved = max(moved, 1000 * delta if control.unit(name) == 'mm' else degrees(delta))
        varied = getattr(self, 'varied', None)
        swept = varied['field'] if varied and varied.get('result') is not None else ''
        program = getattr(self, 'program', None)
        return lessons.Facts(field=field, goals=tuple((r.id, r.status) for r in results),
                             tool_off=tool_off,
                             blocks=tuple(b.kind for b in program.blocks) if program is not None else (),
                             ran=getattr(getattr(self, 'runner', None), 'state', ''),
                             robot=robot, moved=moved, swept=swept)

    def check_lessons(self):
        """Finish whatever lessons the work now satisfies, and say so for a few seconds above the
        view - not in the status line, which stays the work's own."""
        progress = self.lesson_progress
        newly = lessons.check_all(progress, self.lesson_facts())
        if newly:
            import time
            done = lessons.BY_ID[newly[-1]]
            left = len(lessons.LESSONS) - len(progress.done)
            self.workspace_host._lesson_note = (
                f'Lesson done: {done.title}. ' + (f'{left} to go - the Guide shows the next.' if left else 'All five lessons done.'),
                time.monotonic())
        return newly

    def draw_lesson_note(self, text, x, y, width):
        """The last lesson finished, for six seconds."""
        import time
        note = getattr(self.workspace_host, '_lesson_note', None)
        if note and time.monotonic() - note[1] < 6:
            text(note[0], x, y, 13, ACCENT, width)

    # -- starting a lesson ------------------------------------------------------------

    def start_lesson(self, lesson_id):
        """Make ready what a lesson needs: its machine, its field, the panel it is done in."""
        from little_world.robots.arm_lab import arm_lab_blueprint
        from little_world.robots.mobile_platform import mobile_platform_blueprint
        lesson = lessons.BY_ID[lesson_id]
        self.lesson_progress.choose(lesson_id)
        if lesson.setup == 'import':
            self.switch_workspace('Real')
            real = self.active_workspace
            real.import_robot_form()
            real.dialog['fields'][0][1] = str(SAMPLE)
            real.status = 'Lesson: ' + lesson.goal
            return
        if not self.building:
            self.simulate()     # back to build: the lesson sets up its own machine
        machine, field = {'cart': (mobile_platform_blueprint, 'doorway'), 'arm': (arm_lab_blueprint, 'pick_place'),
                          'program': (arm_lab_blueprint, 'pick_place'), 'sweep': (mobile_platform_blueprint, 'sprint')}[lesson.setup]
        self.close_bench()
        self.edit(lambda: self.editor.load(machine()))
        self.stop_program()
        self.program_edit(type(self.program)())
        self.set_field(field)
        if lesson.setup == 'arm':
            self.simulate()
            self.operate_robot()
            self.control_mode = 'Tool'
            self.workspace_host._tool_left = False
            if self.tool_motion is not None:    # drawn back from the cube, along a line that never passes it
                self.tool_motion.glide(forward=-.10, up=.08)
        elif lesson.setup == 'program':
            self.show_program()
        self.active_tab = 'Guide'
        self.status = 'Lesson: ' + lesson.goal

    # -- the panel ----------------------------------------------------------------------

    def draw_lessons(self, ui, button, text, section, ww, wh):
        progress = self.lesson_progress
        section(f'LEARN BY DOING  /  {len(progress.done)} of {len(lessons.LESSONS)} done', 122)
        for i, lesson in enumerate(lessons.LESSONS):
            mark = 'done  ' if lesson.id in progress.done else f'{i + 1}.  '
            button(mark + lesson.title, 12, 144 + i * 31, 264, lambda n=lesson.id: progress.choose(n),
                   active=lesson.id == progress.current, h=27)
        lesson = progress.lesson()
        y = 312
        text(lesson.title.upper(), 16, y, 11, ACCENT, 254)
        y += 22
        for line in textwrap.wrap(lesson.goal, 38):
            text(line, 16, y, 12, max_width=254)
            y += 18
        y += 6
        for i, step in enumerate(lesson.steps):
            for k, line in enumerate(textwrap.wrap(step, 36)):
                text((f'{i + 1}  ' if k == 0 else '   ') + line, 16, y, 11, MUTED, 254)
                y += 16
            y += 4
        done, missing = lesson.check(self.lesson_facts())
        y += 6
        if lesson.id in progress.done:
            text('Done. Pick another, or do it again.', 16, y, 12, ACCENT, 254)
        else:
            for line in textwrap.wrap(missing, 38)[:2]:
                text(line, 16, y, 11, WARN, 254)
                y += 16
        button('Start this lesson', 12, wh - 160, 264, lambda: self.start_lesson(lesson.id), h=34, tone='primary')
        button('Build help: starter kits and checks', 12, wh - 118, 264, lambda: setattr(self, 'guide_view', 'Build'), h=30)
