"""The first hour, checked by the app: five short lessons (ADR 0046, FR-033).

A newcomer learns a tool faster by doing guided tasks than by watching: 79 novices taught an
arm's block language by an interactive tutorial made their program in 9 min 59 s and scored
12.1 of 15, against 13 min 38 s and 9.4 taught by a video (ABB's CoBlox study; the focused
reading of 21 October). Little World taught with a guide tab and documents. Here a lesson is
data - what to do, a few steps, a set-up the window can make, and a check - and the window
watches for the check while the user works, in any order, and keeps who finished what outside
the repository.

Standard library only: a check reads `Facts`, which the window gathers each frame.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path

ENVIRONMENT = 'LITTLE_WORLD_PROGRESS'
MOVED = 5.          # degrees (or mm): a joint moved this far from home was moved on purpose


@dataclass(frozen=True)
class Facts:
    """What the window can tell a lesson about the work so far."""
    field: str = ''             # the field the machine is on
    goals: tuple = ()           # (goal id, status) of that field's goals now: met, kept, failed, missed, open
    tool_off: float = None      # m: the tool point from the field's object, once the tool has been away from it
    blocks: tuple = ()          # the program's block kinds
    ran: str = ''               # the program runner's state: stopped, running, completed, failed ...
    robot: str = ''             # the Joint lab's robot
    moved: float = 0.           # degrees (or mm): the most one of its joints has gone from home
    swept: str = ''             # the field of the last repeats with variations that finished


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    goal: str           # what to do, in a sentence
    steps: tuple        # how, a few short lines
    setup: str          # what "Start" makes ready - the window knows each

    def check(self, facts):
        """(done, what is still missing - '' once done)."""
        return CHECKS[self.id](facts)


def _drive(facts):
    if facts.field != 'doorway':
        return False, 'Start the lesson: the cart on the Doorway field.'
    status = dict(facts.goals)
    if status.get('frame') == 'failed':
        return False, 'The door frame was touched: press Stop, then try again.'
    if status.get('upright') == 'failed':
        return False, 'The cart tipped over: press Stop, then try again.'
    if status.get('through') != 'met':
        return False, 'Not through the doorway yet.'
    if status.get('parked') != 'met':
        return False, 'Through: now park in the bay beyond.'
    return True, ''


def _tool(facts):
    if facts.field != 'pick_place' or facts.tool_off is None:
        return False, 'Start the lesson: the arm lab at the Pick and place table, in Tool mode, drawn back.'
    if facts.tool_off > .015:
        return False, f'The jaws are {100 * facts.tool_off:.0f} cm from the cube.'
    return True, ''


def _program(facts):
    if facts.field != 'pick_place':
        return False, 'Start the lesson: the arm lab at the Pick and place table.'
    if 'grasp' not in facts.blocks:
        return False, 'The program has no grasp step: load the Pick and place template.'
    if facts.ran != 'completed':
        return False, 'Run the program to its end.'
    if dict(facts.goals).get('lifted') != 'met':
        return False, 'The program ran, but the cube was not lifted.'
    return True, ''


def _import(facts):
    if not facts.robot.startswith('user:'):
        return False, 'Import a robot: the sample arm, or drop your own URDF on the window.'
    if facts.moved < MOVED:
        return False, 'Imported. Now move one of its joints: hold its keys, or run the joint example.'
    return True, ''


def _sweep(facts):
    if not facts.swept:
        return False, 'Run the sprint, stop, and press Repeat with variations in the run report.'
    return True, ''


CHECKS = {'drive': _drive, 'tool': _tool, 'program': _program, 'import': _import, 'sweep': _sweep}

LESSONS = (
    Lesson('drive', 'Drive through the doorway',
           'Drive the cart through the doorway without touching its frame, and park beyond.',
           ('Press SIMULATE, then hold W to go and A or D to turn.',
            'The door is off to the left; the bay is behind the wall.',
            'Touch the frame and the lesson starts again.'),
           'cart'),
    Lesson('tool', 'Move the gripper to the cube',
           'Bring the open jaws around the cube, moving the tool rather than single joints.',
           ('Start draws the arm back; Tool mode is open on the right.',
            'Hold the arrow keys to move the tool; Page Up and Down to raise and lower it.',
            'It travels straight; at the edge of its reach it stops and says so.'),
           'arm'),
    Lesson('program', 'Program the arm to pick the cube up',
           'Make a block program that lifts the cube, and run it.',
           ('In Program, load the Pick and place template.',
            'Read its steps: poses, grasp, release - each is one block.',
            'Press Run and watch the run report.'),
           'program'),
    Lesson('import', 'Bring in a robot from its file',
           'Import a robot from its URDF file and move one of its joints.',
           ('Start opens the import with the sample arm, or drop your own file on the window.',
            'Read what the import added and what it says to check.',
            'Then hold a joint\'s keys, or load the joint motion example and run it.'),
           'import'),
    Lesson('sweep', 'Ask how sure a result is',
           'Repeat a run with variations and read how much its result spreads.',
           ('Drive the cart down the 5 m sprint lane, then press Stop.',
            'In the run report, press Repeat with variations.',
            'Read the spread: how much each change moved the time.'),
           'sweep'),
)
BY_ID = {lesson.id: lesson for lesson in LESSONS}


def path():
    """Where progress is kept: $LITTLE_WORLD_PROGRESS, else beside the robot library in the
    platform's place for an application's own data."""
    if os.environ.get(ENVIRONMENT):
        return Path(os.environ[ENVIRONMENT]).expanduser()
    home = Path.home()
    if sys.platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'Little World' / 'lessons.json'
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA') or home) / 'Little World' / 'lessons.json'
    return Path(os.environ.get('XDG_DATA_HOME') or home / '.local' / 'share') / 'little-world' / 'lessons.json'


class Progress:
    """Which lessons this user has finished, and when; and the one they are on."""

    def __init__(self, where=None):
        self.where = Path(where) if where is not None else path()
        self.done, self.current = {}, LESSONS[0].id
        try:
            data = json.loads(self.where.read_text(encoding='utf-8'))
            self.done = {k: v for k, v in data.get('done', {}).items() if k in BY_ID}
            if data.get('current') in BY_ID:
                self.current = data['current']
        except (OSError, ValueError, AttributeError):
            pass

    def lesson(self):
        return BY_ID[self.current]

    def choose(self, lesson_id):
        if lesson_id not in BY_ID:
            raise ValueError(f'No lesson called {lesson_id!r}')
        self.current = lesson_id
        self.save()

    def finish(self, lesson_id):
        """Mark a lesson done; the current one moves to the next not yet done. True if new."""
        if lesson_id in self.done:
            return False
        self.done[lesson_id] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        if lesson_id == self.current:
            left = [x.id for x in LESSONS if x.id not in self.done]
            self.current = left[0] if left else lesson_id
        self.save()
        return True

    def save(self):
        try:
            self.where.parent.mkdir(parents=True, exist_ok=True)
            self.where.write_text(json.dumps(dict(done=self.done, current=self.current), indent=1), encoding='utf-8')
        except OSError:
            pass    # progress is a convenience: a read-only home folder does not stop the lessons


def check_all(progress, facts):
    """Finish every lesson whose check passes now; the ids newly finished, in order."""
    return [x.id for x in LESSONS if x.id not in progress.done and x.check(facts)[0] and progress.finish(x.id)]
