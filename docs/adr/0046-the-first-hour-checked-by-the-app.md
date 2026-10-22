# The first hour, checked by the app: five lessons in the Guide

**Problem.** Little World taught a newcomer with a Guide tab of starter kits and with
documents: nothing said what to try first, and nothing noticed when it was done. The owner asked
on 21 October for "controlling and learning cost as low as possible". What helps novices learn an
arm's block language is doing guided tasks, not watching: 79 technical novices taught CoBlox by an
interactive tutorial made their pick-and-place program in 9 min 59 s and scored 12.1 of 15,
against 13 min 38 s and 9.4 taught by a video, and the eight who scored nothing had all watched
([ABB, Training end-users to program industrial robots](https://new.abb.com/news/detail/26823/training-end-users-to-program-industrial-robots);
the focused reading of 21 October, FR-033).

**Does an existing simulator solve it? Can we wrap it?** No simulator teaches this app's own
work. The lessons drive what the app already has - its kits, fields, goals, Tool mode (ADR
0045), block programs, the robot import (ADR 0044) and repeats with variations (ADR 0024) -
through the same actions a user has.

**Unique contribution.**
- *Lessons as data* (`lessons.py`, standard library): five, each a goal, two or three steps, a
  set-up and a check - drive the cart through the doorway and park; bring the gripper's open jaws
  to the cube by moving the tool; program the arm to lift the cube; bring in a robot from its file
  and move one of its joints; repeat a run with variations and read its spread. A check reads
  `Facts` - the field and its goals, how far the tool is from the cube once it has been away from
  it, the program's blocks and how its run ended, the Joint lab's robot and how far its joints
  moved, the last repeats that finished - and says what is still missing in a line.
- *Checked as the user works* (`ui/lessons_panel.py`): each frame the active workspace - the
  workshop or the Joint lab - gathers its facts, and every lesson whose check passes is finished,
  in any order, and said above the view for six seconds (not in the status line, which stays the
  work's own). Progress is kept per user outside the repository, beside the robot library
  (`$LITTLE_WORLD_PROGRESS`); tests get their own.
- *The Guide opens on them*: the five with what is done, the chosen lesson's goal, steps and what
  is missing, and "Start this lesson", which sets up its machine, field and panel - the cart at the
  doorway; the arm lab at the pick-and-place table in Tool mode, drawn back from the cube along a
  line that never passes it; the program panel; the Joint lab's import with a sample arm
  (`assets/samples/sample_arm.urdf`, made here); the cart at the sprint lane. The starter kits and
  build checks are a click away.

**Blueprint and builder.** Untouched; a lesson loads the same kits a user would.

**Result.** Each lesson is finished in the window through a user's actions: the tool lesson by
holding arrow and page keys towards the cube as a user watching it would; the program lesson by
the Pick and place template and Run; the import lesson by the prefilled form and the joint motion
example (the sample arm imports with a servo on each of its three joints and nothing to check);
the drive lesson by a two-stop drive-to program through the door into the bay; the sweep lesson
by the sprint, Stop and Repeat with variations.

Held by `tests/test_lessons.py` (7, three of them window tests). Suites on MuJoCo 3.10.0: 1035 passed with a display, 983 headless.

**Boundaries.** Five lessons, an hour at most; the checks see what the simulator shows, not what
the user understood. The sweep lesson is done when any repeats finish. Progress is per user on one
machine. No study of how much the lessons shorten anyone's first hour has been made here - the
CoBlox result is the reason to try, not a measurement of this.
