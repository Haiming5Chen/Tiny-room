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
                            # 'factory': Real's cell; 'conveyor': beside the roller conveyor;
                            # 'curbs': the kit cart driven at the Curb run's curbs (FR-040)
    tab: str = ''           # the left panel shown while it runs ('Edit': the drive panel); '' the Guide's
    heavier: float = 1.     # the Fetch cube made this many times as heavy for the run (FR-036)
    after: str = ''         # when set, the run stops as its program ends - its report on the left,
                            # as Stop shows it - and the status line says this (ADR 0063, 0064)
    product: str = 'Small block'    # what Real's cell makes in a 'factory' demonstration
    feeder: str = 'hand'            # how Real's cell is fed in a 'factory' demonstration: 'conveyor' (ADR 0068)
    sensing: str = 'known'          # how Real's cell finds its parts in a 'factory' demonstration: 'camera' (ADR 0069)
    squeeze: float = 0.             # the Fetch's jaws squeezing this many newtons by current, 0: as solved (FR-037)


# Newest first; the first four, the sweeps' disturbances, as ADR 0055 made them.
DEMOS = (
    Demo('nowhere', 'Energy from nowhere',
         'Every run now checks its contacts: one gives back what two bodies put into it as they press '
         'together, never more. On the Curb run one does - the kit cart pushes a caster against the '
         '10 mm curb, and their contact gives the cart energy it never took, enough to lift it 4.6 mm.',
         'at about 6 s the drive panel\'s physics check turns orange: the curb and a caster\'s wheel',
         '', 'ADR 0074', where='curbs', tab='Edit'),
    Demo('felt', 'It feels the cube under its jaw',
         'The cube is moved 5 cm just after the camera looked, and a jaw comes down on it. The arm\'s '
         'servos feel the shoulder fall behind where it was sent, and the arm rises at once - it used '
         'to press the cube into the table for 2 s - then looks again and fetches it.',
         'about 16 s in the cube jumps; a second later the Program panel says "Felt something reaching down"',
         'cube moved 5 cm sideways, 2 s later', 'ADR 0071'),
    Demo('seen', 'The cell finds its parts',
         "In Real mode the Panda's cell looks for each part with its overhead depth camera, a "
         "RealSense D435's pixels and noise, instead of reading where it is from the simulation. The "
         "arm first moves out of the camera's view; in the corner the depth picture shows the part "
         "in green, and where it was seen.",
         'the depth picture in the corner: each part in green, and how far from its place it was seen',
         '', 'ADR 0069', where='factory', feeder='conveyor', sensing='camera'),
    Demo('fed', 'The cell fed by a conveyor',
         'In Real mode a roller conveyor feeds the Panda: pallets carry the parts to its stop, the '
         'Panda picks each off its pallet into its slot, and the empty pallet goes back to the '
         'line\'s start with the next part on it. The rollers under a held pallet stand still, as '
         'friction rollers do.',
         'each part arrives at the stop on its pallet; the line under the cell says how far from its place',
         '', 'ADR 0068', where='factory', feeder='conveyor'),
    Demo('conveyor', 'A roller conveyor',
         "A new test field: nine powered steel rollers carry two pallets at 0.1 m/s, the kit's cube on "
         "each, to a stop plate. The first comes to rest against the stop, the second queues behind "
         "it, and the rollers under both stand still while their drives turn on (ADR 0068).",
         'the pallets ride to the stop and queue; on the left, their goals met by 2 s',
         '', 'ADR 0067', where='conveyor', tab='Edit'),
    Demo('squeeze', 'A squeeze set in newtons',
         "The Fetch program with its jaws set to squeeze 7 N at each pad, as a ROBOTIS servo sets it by "
         "its current: in the Program panel the close block says \"squeeze 7 N\". On the left, under "
         "\"holding\", the grip's friction in use peaks near 60 %, where the squeeze the closing ramp "
         "leaves peaks near 80 %.",
         'the close block says "squeeze 7 N"; on the left, the grip in use stays near 60 % at most',
         '', 'ADR 0066', tab='Edit', squeeze=7.),
    Demo('panda', 'The Panda holds itself up',
         'In Real mode the Panda puts six tall blocks in their slots. Its joints are now held up against '
         'gravity, as its own controller holds the real arm, and its hand squeezes 70 N, as its '
         'datasheet gives: each part lands within a millimetre of its slot, where they landed 2 to 6 mm '
         'out.',
         'the line under the cell: every part within its room, the worst under a millimetre off',
         '', 'ADR 0065', where='factory', product='Tall block'),
    Demo('repeats', 'Where repeats fail',
         'The Fetch runs once, as designed, and stops when the cube is in the bin. Under each Repeat '
         'button its report says what the repeats can show before they run. Repeated with '
         'disturbances, each that cost runs says which goal they missed and what the program was '
         'doing when it gave up.',
         'when the run stops, the lines under the Repeat buttons; then press Repeat with disturbances',
         '', 'ADR 0063, 0064',
         after='under each Repeat button, what its runs can show. Press Repeat with disturbances: '
               'when its runs are done, each disturbance says where they failed'),
    Demo('slip', 'How close to slipping',
         'The cube is made 16 times as heavy: 260 g, as if it were silver. On the left, under "holding", '
         "a line says how much of the grip's friction is in use. It climbs as the arm lifts, reaches "
         '100 % and the cube slides out of the jaws. The ordinary cube uses about 38 %.',
         'on the left, under "holding": the friction in use climbs to 100 % and the cube slides out',
         '', 'ADR 0061', heavier=16., tab='Edit'),
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
         'The cube is moved 5 cm just after the camera looked. A jaw comes down on it; the arm rises, '
         'looks again and fetches it from where it went.',
         'about 16 s in, the cube jumps 5 cm; at 17 s the arm rises and the camera looks again',
         'cube moved 5 cm sideways, 2 s later', 'ADR 0033, 0037, 0051, 0071'),
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

# The Guide's What's new page, top to bottom: the list from LIST_TOP, a ROW for each
# demonstration; under it what the one picked shows - at most SHOWN high, with its eight lines
# of what it shows and four of what to watch for - and the Guide's own button, whose top is FOOT
# above the window's foot (px).
LIST_TOP, ROW, SHOWN, FOOT = 146, 28, 257, 122


def demo_pages(wh):
    """How the list is paged in a window `wh` high: (demonstrations a page, pages). All on one
    page when they fit above what the one picked shows; else a row of them goes to the pager."""
    room = (wh - FOOT - SHOWN - LIST_TOP) // ROW
    if room >= len(DEMOS):
        return len(DEMOS), 1
    rows = max(1, room - 1)
    return rows, -(-len(DEMOS) // rows)

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
        self.demo_report_due = False
        if demo.where == 'factory':
            self.start_factory_demo(demo)
            return
        if demo.where in ('tilt', 'conveyor'):
            self.start_tilt_demo(demo)
            return
        if demo.where == 'curbs':
            self.start_curb_demo(demo)
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
        if demo.squeeze:
            from little_world.control.tool_motion import squeezed
            self.program_edit(squeezed(self.program, demo.squeeze))     # its jaws by current (FR-037)
        if demo.heavier != 1.:
            self.backend.scale_mass('objects/fetch_cube', demo.heavier)     # until the world is reset (FR-036)
        self.show_program()
        self.start_program()
        self.watch_the_table()
        if demo.tab:
            self.active_tab = demo.tab      # the drive panel: its motors (ADR 0058)
        self.demo = demo.id
        self.demo_report_due = bool(demo.after)
        self.status = f'{demo.title}: {demo.watch}.'

    def poll_demo(self):
        """A demonstration that ends on its run's report stops the run as its program ends -
        done, or given up - as a press of Stop would, once (ADR 0063, 0064)."""
        if not getattr(self, 'demo_report_due', False):
            return
        if self.building:
            self.demo_report_due = False        # stopped by hand first
            return
        if self.runner.state in ('completed', 'failed'):
            self.demo_report_due = False
            self.events.append(self.end_demo_run)

    def end_demo_run(self):
        demo = BY_ID[self.demo]
        if not self.building:
            self.simulate()             # back to build, the run's report on the left
        self.status = f'{demo.title}: {demo.after}.'

    def start_tilt_demo(self, demo):
        """The arm on its cart on a field that moves by itself - the tilt table (ADR 0059), the
        roller conveyor (ADR 0067) - run, the drive panel open."""
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        if not self.building:
            self.simulate()
        self.close_bench()
        self.stop_program()
        self.edit(lambda: self.editor.load(mobile_manipulator_blueprint()))
        self.program_edit(type(self.program)())
        self.set_field(demo.where)
        self.arm_disturbance(None)
        self.simulate()
        self.home(True)
        self.active_tab = 'Edit'            # the drive panel: speed, stance, degrees from tipping
        self.demo = demo.id
        self.status = f'{demo.title}: {demo.watch}.'

    def start_curb_demo(self, demo):
        """The kit cart driven straight at the Curb run's curbs by a one-block program, the drive
        panel open, where the physics check says what each contact did (FR-040)."""
        from little_world.programming.program import Block, Program
        from little_world.robots.mobile_platform import mobile_platform_blueprint
        if not self.building:
            self.simulate()
        self.close_bench()
        self.stop_program()
        self.edit(lambda: self.editor.load(mobile_platform_blueprint()))
        self.set_field('curbs')
        self.arm_disturbance(None)
        self.program_edit(Program((Block('drive', value=12., secondary=12., duration=13.),)))
        self.start_program()
        self.active_tab = 'Edit'
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
        if real.feeder != demo.feeder:
            real.select_feeder(demo.feeder)
        if real.sensing != demo.sensing:
            real.select_sensing(demo.sensing)
        if real.product != demo.product:
            real.select_product(demo.product)
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
        y = LIST_TOP
        rows, pages = demo_pages(wh)
        picked = getattr(self, 'demo', None)
        if picked != getattr(self, 'demo_paged', None):
            # A demonstration just started - from the command line too: the list opens on its page.
            self.demo_paged = picked
            if picked in BY_ID:
                self.demo_page = DEMOS.index(BY_ID[picked]) // rows
        page = min(max(getattr(self, 'demo_page', 0), 0), pages - 1)
        for demo in DEMOS[page * rows:(page + 1) * rows]:
            button(demo.title, 12, y, 264, lambda n=demo.id: self.start_demo(n), h=ROW - 4,
                   active=getattr(self, 'demo', None) == demo.id)
            y += ROW
        if pages > 1:
            # Fifteen and more do not fit a window 780 high above what the one shown is: pages of
            # them, newest first.
            button('< Newer', 12, y, 80, lambda: setattr(self, 'demo_page', page - 1), enabled=page > 0, h=ROW - 4)
            text(f'{page + 1} of {pages}', 122, y + (ROW - 4 - 16) / 2, 12, MUTED, 56)
            button('Older >', 196, y, 80, lambda: setattr(self, 'demo_page', page + 1), enabled=page < pages - 1, h=ROW - 4)
            y += ROW
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
