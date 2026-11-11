# Watch it work: recent work run in the window, one press each

**Problem.** The owner, 26 October: "over the past 2 weeks, no updates that I can see from the
app". It was so. Of the eleven decisions since 21 October, the last six - ADR 0049 to 0054 -
changed nothing the window shows: each ran in a sweep's processes and ended as counts in a report.
The five before them changed the window in corners: an import in Real mode (ADR 0044), held keys in
Tool mode (ADR 0045), lessons behind the Guide button (ADR 0046), an imported gripper (ADR 0047)
and five lines of how the program feels its grasp (ADR 0048). What the sweeps measured - the cube
moved after the program looked, a camera that freezes, a shove at the table, an alarm from outside
- could not be seen happening, and the alarm of ADR 0052 had no control at all. The owner on 21
October: "complex inside, operation easy".

**Does an existing simulator solve it? Can we wrap it?** No simulator shows this app's own sweeps.
They are wrapped as they are: the disturbance in the window is the sweeps' own `Disturbing` (ADR
0030), with the same trigger; Look again is the runner's own `alarm` (ADR 0052); the demonstrations
load the same kit, field and solved program a user would.

**Unique contribution.**
- *What's new* (`ui/whats_new.py`): a button in the top bar, beside the field, opens the Guide on
  four demonstrations, each a title, what happens in two sentences and the decisions it comes from.
  One press loads the arm on its cart, puts it on the Fetch field, solves the Fetch program for it,
  arms the demonstration's disturbance, runs it and turns the view to the table, from the cart's
  left - from behind the cart its arm hides the cube; F brings the chase view back. The status line
  says what to watch for and when.
  - *Watch it look again*: the cube moved 5 cm sideways 2 s after the program looked (ADR 0033, 0037,
    0051).
  - *A camera that freezes*: the camera stops sending new pictures as the cube is moved (ADR 0038).
  - *Shove the cart off its stop*: 6 N s from the side as the cart stops at the table (ADR 0031).
  - *Tell it to look again yourself*: the Fetch program undisturbed, for the next button (ADR 0052).
- *A disturbance in the window* (`ui/live_disturbance.py`): armed by its label from the field's own
  list (`fields.disturbance.DEFAULTS`), it happens during each run on the sweeps' trigger - after a
  goal is met, once the machine has stood still that long, after its delay - on the goals' clock;
  a camera fault fails the program's own camera. It happens once a run, stays armed until cleared,
  and the window says when it happened. Only the field's own disturbances can be armed.
- *Look again* in the Program panel: enabled while the runner listens - running, at a stop where it
  looked, with a regrasp left - and pressed, the program opens its jaws by as much as they closed,
  rises if the arm reached down, goes back to its stop and looks again, once a run (ADR 0052).
- *What it has to go on*: while a program runs, two lines in the Program panel say what its camera
  last saw ("saw the fetch_cube 4.8 cm from the plan"), or what is wrong with its pictures ("its
  picture is not new"), and what its jaw servos' registers say: moving, nothing between them, or
  holding - stopped short and pushing, with the current they draw (ADR 0048).

**Blueprint and builder.** Untouched: a demonstration loads the kit's mobile manipulator as the
Build tab's "Arm on moving cart" does, and the user's design is replaced as by any kit button.

**Result.** Each demonstration was run in the window (Xvfb, MuJoCo 3.10.0) and does what its
button says; times on the run's clock:
- *Watch it look again*: the cart stopped at the table at 11.2 s and looked at 14.2 s; the cube was
  moved at 16.5 s; at 19.9 s the program found the cube was not where it was reaching ("Blocked
  reaching down: looking again"), rose, looked again at 22.3 s, lifted the cube at 27.1 s and set it
  in the bin; done at 45.8 s, all four goals met.
- *A camera that freezes*: frozen at 14.5 s as the cube was moved; at 14.8 s the program stopped -
  "Looked for fetch_cube: the camera's picture is not new" - and reached for nothing.
- *Shove the cart off its stop*: shoved at 14.5 s; at 16.3 s "Pushed 6 cm off its stop: going back";
  it drove in again, looked, lifted the cube at 31.3 s; done at 50.7 s, all goals met.
- *Tell it to look again yourself*: Look again became pressable at 15.2 s, as the arm reached for the
  cube; pressed at 16.2 s, the program went back and looked again, lifted the cube at 23.5 s; done
  at 42.4 s, all goals met.

Held by `tests/test_whats_new.py` (9, three of them window tests): the demonstrations each arm one of the Fetch field's own
disturbances; a disturbance armed by its label and cleared, and refused for another field's; it
happens on its trigger, once a run, and the window says when; a camera fault fails the program's
camera; Look again asks the runner and says why when it cannot; what the program sees and feels;
and in the window - the top bar's button, the cube moved and fetched from where it went; a frozen
camera that stops the program, then Look again pressed while the arm reaches and the cube fetched;
the shove, going back and the cube fetched. Suites on MuJoCo 3.10.0: 1092 passed with a display, 1037 headless.

**Boundaries.** Four fixed set-ups on one field and one machine; the window shows the sweeps'
disturbances, it does not measure them - the counts stay the sweeps'. The goals are checked once a
frame, so a disturbance after a goal comes up to a frame later than in a sweep: its time, and so the
run, can differ by a frame's simulated time (at most 0.1 s) from run to run. Look again acts only
at a stop where the program looked, once a run. The jaws are read as the kit's XH430 servos; a
robot model's own gripper servo is not read ("no servos to read"). The top bar's button needs a
window at least 1168 pixels wide; narrower, What's new is in the Guide. The list is written by hand:
later work is added to it when it can be watched.

**2026-11-06: in pages.** Fifteen demonstrations and what the picked one shows no longer fitted the
window as it opens, 1200 by 780: the last lines ran under the Guide's own button at its foot and off
the window. The list is now paged when it does not fit above what the picked one shows - eight to a
page at 780, under them "< Newer", "1 of 2" and "Older >" - and on one page in a window tall enough
(`ui/whats_new.demo_pages`). A demonstration just started, from its button or from
`little-world demo NAME`, is shown on its own page. `tests/test_whats_new.py` draws every page with every demonstration
picked: every word and button is above the Guide's button, and the pages hold each demonstration
once, newest first. Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.
