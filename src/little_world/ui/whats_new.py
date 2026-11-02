"""The Guide's What's new: recent work, each a button that sets it up and runs it (ADR 0055).

What the sweeps measured happened in another process and ended as counts in a report; the
owner could not see it in the window (26 Oct: "no updates that I can see from the app"). Here
each recent piece of work is a demonstration: one press loads the machine and its field, solves
its program, arms the disturbance the sweeps tried and starts the run, and the status line says
what to watch for. A workshop mixin.
"""
from dataclasses import dataclass
import textwrap

MUTED = (.6, .74, .77)
ACCENT = (.37, .83, .69)


@dataclass(frozen=True)
class Demo:
    id: str
    title: str
    shows: str          # what happens, in a sentence
    watch: str          # what the status line says to watch for
    disturbance: str    # the Fetch field's disturbance armed for the run, '' for none
    adr: str
    where: str = 'fetch'    # 'fetch': the arm on its cart at the Fetch field; 'tilt': on the tilt table;
                            # 'factory': Real's cell
    tab: str = ''           # the left panel shown while it runs ('Edit': the drive panel); '' the Guide's


# Newest first; the first four, the sweeps' disturbances, as ADR 0055 made them.
DEMOS = (
    Demo('tipping', 'How near it is to tipping',
         'The arm on its cart stands on a table that tilts 2 degrees a second. On the left, under the '
         "table's angle, a line counts the degrees it has left before it tips - its weight and its "
         'accelerations both - down to nothing as it goes over, at about 54.',
         "on the left, under the table's angle, the degrees left before it tips count down; at about 54 it tips",
         '', 'ADR 0059', where='tilt'),
    Demo('hot_motor', 'A motor run hot',
         'The left drive motor runs 50 degrees hot from the start, so it makes 84 % of its torque. The '
         'arm on its cart fetches the cube just as it does cool: its drive never asks a motor for more '
         'than about half of what it could give.',
         'on the left, under MOTORS, the left motor is marked weakened; the cube is in the bin at '
         'about 37 s, as cool',
         'left motor 50 K hot', 'ADR 0058', tab='Edit'),
    Demo('factory', 'Six parts, measured',
         'In Real mode the Panda in the factory cell puts six parts in their slots, one after another. '
         'Under the cell a line says how far from its slot each part landed, against the room it had '
         'before it would touch the next, and how long each took.',
         'the line under the cell says how far from its slot each part landed and how long it took',
         '', 'ADR 0019, 0056', where='factory'),
    Demo('look_again', 'Watch it look again',
         'The cube is moved 5 cm just after the camera looked. The jaws come down beside it, rise, '
         'look again and fetch it from where it went.',
         'about 16 s in, the cube jumps 5 cm; at 20 s the arm rises and the camera looks again',
         'cube moved 5 cm sideways, 2 s later', 'ADR 0033, 0037, 0051'),
    Demo('frozen', 'A camera that freezes',
         'The camera stops sending new pictures as the cube is moved. The program sees its pictures '
         'are old and stops before it reaches for a cube that is not there.',
         'at the table the program stops: "the camera\'s picture is not new"',
         'camera frozen as the cube is moved 5 cm', 'ADR 0038'),
    Demo('shove', 'Shove the cart off its stop',
         'A 6 N s push from the side as the cart reaches the table. It notices it is off its stop, '
         'backs up, drives in again and goes on.',
         'at the table the cart is pushed aside; it drives back to its stop',
         'shoved 6 N s at the table', 'ADR 0031'),
    Demo('alarm', 'Tell it to look again yourself',
         'The Fetch program, undisturbed. While it reaches for the cube, press Look again in the '
         'Program panel: it opens its jaws, rises, looks again and carries on. Once it holds the cube '
         'the button greys out: looking again then would drop it.',
         'press Look again in the Program panel while the arm reaches for the cube',
         '', 'ADR 0052'),
)
BY_ID = {d.id: d for d in DEMOS}

# Where a demonstration is watched from: the Fetch table, from the cart's left and above - what
# happens there is the point, and from behind the cart its arm hides the cube. (lookat, distance,
# azimuth, elevation); F turns the chase view back on.
TABLE_VIEW = ((1.75, .03, .17), 1.35, -50., -22.)


class WhatsNew:
    def show_whats_new(self):
        """The Guide, open on What's new: the top bar's button, one click from anywhere."""
        self.show_guide()
        self.guide_view = 'New'

    def start_demo(self, demo_id):
        """Load the arm on its cart, put it on the Fetch field, solve the Fetch program, arm the
        demonstration's disturbance and run it - or, for the factory's, start Real's cell."""
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        demo = BY_ID[demo_id]
        if demo.where == 'factory':
            self.start_factory_demo(demo)
            return
        if demo.where == 'tilt':
            self.start_tilt_demo(demo)
            return
        if not self.building:
            self.simulate()             # back to build: the demonstration sets up its own machine
        self.close_bench()
        self.stop_program()
        self.edit(lambda: self.editor.load(mobile_manipulator_blueprint()))
        self.program_edit(type(self.program)())
        self.set_field('fetch')
        self.arm_disturbance(demo.disturbance or None)
        self.fetch_program()            # solved for the machine as it stands: leaves the run paused
        self.show_program()
        self.start_program()
        self.watch_the_table()
        if demo.tab:
            self.active_tab = demo.tab      # the drive panel: its motors (ADR 0058)
        self.demo = demo.id
        self.status = f'{demo.title}: {demo.watch}.'

    def start_tilt_demo(self, demo):
        """The arm on its cart on the tilt table, run, the drive panel open (ADR 0059)."""
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        if not self.building:
            self.simulate()
        self.close_bench()
        self.stop_program()
        self.edit(lambda: self.editor.load(mobile_manipulator_blueprint()))
        self.program_edit(type(self.program)())
        self.set_field('tilt')
        self.arm_disturbance(None)
        self.simulate()
        self.home(True)
        self.active_tab = 'Edit'            # the drive panel: speed, stance, degrees from tipping
        self.demo = demo.id
        self.status = f'{demo.title}: {demo.watch}.'

    def start_factory_demo(self, demo):
        """Over to Real: the Panda's pick-and-place cell, reset, and a production run started
        (ADR 0019); the factory panel's lines say how it went (ADR 0056)."""
        self.demo = demo.id
        self._switch_view('Real')
        real = self.workspace_host.active_workspace
        if real.robot_asset != 'franka_panda':
            real.select_robot('franka_panda')
        if real.experiment != 'Pick and place':
            real.select_experiment('Pick and place')
        real.reset_cell()
        if real.product != 'Small block':
            real.select_product('Small block')     # the cell's own part: a tall one tips in the hand (ADR 0056)
        real.start_run()
        real.status = f'{demo.title}: {demo.watch}.'

    def watch_the_table(self):
        """Look at the table where the demonstration happens (TABLE_VIEW), in a free view."""
        self.home()                     # a free camera, which the chase view leaves alone
        lookat, distance, azimuth, elevation = TABLE_VIEW
        self.camera.lookat[:] = lookat
        self.camera.distance, self.camera.azimuth, self.camera.elevation = distance, azimuth, elevation

    def draw_whats_new(self, ui, button, text, section, ww, wh):
        section('WHAT\'S NEW  /  one press runs it', 122)
        y = 146
        for demo in DEMOS:
            button(demo.title, 12, y, 264, lambda n=demo.id: self.start_demo(n), h=28,
                   active=getattr(self, 'demo', None) == demo.id)
            y += 32
        shown = BY_ID.get(getattr(self, 'demo', None), DEMOS[0])
        section('WHAT IT SHOWS', y + 10)
        y += 34
        text(shown.title, 16, y, 13, ACCENT, 256)
        y += 21
        for line in textwrap.wrap(shown.shows, 40)[:8]:
            text(line, 16, y, 11, MUTED, 256)
            y += 15
        y += 6
        for line in textwrap.wrap('Watch for: ' + shown.watch, 40)[:4]:
            text(line, 16, y, 11, (.8, .87, .9), 256)
            y += 15
        text(shown.adr, 16, y + 4, 10, ACCENT, 256)
        y += 26
        armed = getattr(self, 'live_disturbance', None)
        if armed is not None and y + 40 < wh - 160:
            text('Every run now: ' + armed.label, 16, y, 11, ACCENT, 256)
            button('Stop disturbing the runs', 12, y + 18, 264, lambda: self.arm_disturbance(None), h=26)
        button('Lessons: the first hour', 12, wh - 118, 264, lambda: setattr(self, 'guide_view', 'Lessons'), h=30)
