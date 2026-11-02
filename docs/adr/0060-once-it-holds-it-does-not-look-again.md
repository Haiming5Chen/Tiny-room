# Once it holds the cube, an alarm is not heard: Look again greys out

**Problem.** OPEN LW-033, found by ADR 0052. An alarm from outside the program - `Runner.alarm`, the
window's Look again - makes it recover as its own recovery does: open the jaws by as much as they
closed since the look, rise, go back and look again. Raised after its grasp check has found the cube
held, that opens the jaws on the cube in the air. ADR 0052's false alarms dropped it up to 6.6 cm
onto the table; 1 of 22 left it on its side and broke the run (LW-034), the 21 others cost 4.5 to
8.5 s. In the window What's new asks you to press Look again while the arm reaches for the cube;
pressed a moment late, it dropped it. Measured on the Fetch as designed: the program listened from
15.14 s to 20.62 s, 1.5 s past the grasp check at 19.11 s. An alarm 0.3 s after the check dropped the
cube; it was lifted again at 26.90 s and was in the bin at 44.24 s, not 36.87 s. An alarm at 20.61 s:
in the bin at 44.51 s.

**Does an existing simulator solve it? Can we wrap it?** No simulator's question: it is the program
runner's own rule (ADR 0052).

**Unique contribution.** `Runner.holding()`: the program is past a grasp check that found the object
held since it last looked (`Runner.felt`, that check's block). While it holds, `Runner.listening()` is
false: an alarm is not heard and changes nothing, and the window's Look again greys out. LW-033 named
two ways - set the object down before looking again, or do not act on an alarm once it is held - and
this is the second. What an alarm is for, a reach going wrong (FR-022), is over once the grasp is
felt; and looking again at the table cannot mend what goes wrong after it, a cube slipping in the hand.

**Blueprint and builder.** Untouched: a rule of the runner.

**Result.** The Fetch as designed now listens from 15.14 s to its grasp check at 19.11 s. An alarm
0.3 s and 1.5 s after the check is not heard: the run is its undisturbed run step for step, the cube
in the bin at 36.87 s (before: 44.24 s and 44.51 s, dropped onto the table and fetched again). What's
new's "Tell it to look again yourself" says the button greys out once the cube is held.

Held by `tests/test_branch.py`: an alarm while the program lifts the cube it holds is not heard, the
jaws stay shut and the program completes without looking again; checking the grasp, it is still
heard. Suites on MuJoCo 3.10.0: 1117 passed with a display, 1059 headless.

**Boundaries.** ADR 0052's false-alarm study is not run again: alarms drawn over the program's
listening spans no longer fall while it holds, so its 'holding' row would be empty. A cube that slips
from the hand after the check is not looked for again on an alarm; the program's own checks are as
they were. LW-034, a cube on its side, stays open: an alarm while the jaws close can still tip it.
