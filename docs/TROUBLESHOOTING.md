# When it does not start

Run this first. It checks what the window needs, one line each, and for anything missing prints
the line that mends it:

```sh
.venv/bin/little-world doctor            # or: python -m little_world doctor
```

```
Little World 0.3.0 on Linux x86_64, Python 3.13.16
  ok    Python        3.13.16
  ok    MuJoCo        3.10.0
  ok    NumPy         2.5.3
  ok    Pillow        12.3.0
  ok    PyOpenGL      3.1.10
  ok    Assets        4 robot models, 2 textures
  ok    Physics       a block dropped 10 cm rests at 5.0 cm; 500 steps in 126 ms
  ok    Your designs  /home/you/.local/share/little-world
  ok    Window        an OpenGL window opens

Ready: run  little-world  to open the window, or  little-world demo --list  for what to watch.
```

What has been run where, so you know what is tried and what is a guess: the test suites and
everything on this page marked *seen* on Linux (x86_64, Python 3.11 and 3.13); the window on an
Intel Mac (Python 3.13). Apple silicon and Windows have MuJoCo 3.10.0 wheels and nothing here
has been run on them yet; items marked *expected* are what the tools' own documents say.

## Installing

**`little-world: command not found`** (*seen*). The command is installed into the virtual
environment: run `.venv/bin/little-world` (Windows: `.venv\Scripts\little-world`), or activate
the environment first, or use `python -m little_world`, which is the same command.

**`No module named 'mujoco'`, or the doctor says MuJoCo is not importable** (*seen*). The
package's core has no dependencies on purpose - a design can be read and written without a
simulator - so the window's needs are an extra. Install with it:
`python -m pip install -e '.[workshop]'` (add `dev` for the tests: `'.[workshop,dev]'`).

**pip starts compiling MuJoCo, or fails to on an Intel Mac** (*expected*). No MuJoCo after 3.10.0
has a wheel for Intel Macs (3.11 to 3.17 have none; 4.0.0's engine, `mujoco-core`, has none
either); this project pins 3.10.0, which has one for macOS (Intel and Apple
silicon), Linux (x86_64 and arm64, glibc 2.28 or newer) and Windows, for Python 3.10 to 3.14.
If pip is building from source, something asked for another release: install through the extra
above rather than `pip install mujoco`.

**Python older than 3.11** (*seen*: pip refuses). Make the environment with a newer one:
`python3.13 -m venv .venv`, or `uv venv --python 3.13 .venv`.

## Opening the window

**The doctor's last line is a note: no OpenGL window** (*seen* on a machine without a display).
Everything but the window still works there - the tests, the sweeps, `little-world evidence`. For
the window you need a desktop session. On a Linux server a virtual display is enough to check that
it opens: `xvfb-run -a .venv/bin/little-world --seconds 5` (Debian and Ubuntu: `sudo apt install
xvfb libgl1`).

**Linux under Wayland** (*expected*). The window is made by GLFW through X11, which Wayland
desktops provide as XWayland; nothing needs setting on GNOME or KDE.

**The window opens and the physics is slow.** Each step is 2 ms of simulated time and the window
runs them in real time; a machine that cannot keep up runs slow rather than skipping physics. The
factory cell fed by its conveyor costs 0.86 ms a step on a cloud Xeon core, the Fetch field less.
A virtual machine rendering in software will be slower at drawing, not at physics.

**macOS says the app cannot be opened** applies to the Dock launcher made by
`scripts/install_desktop.py`, which runs this checkout's own environment: keep the checkout where
it was when the launcher was made, or run the script again after moving it.

## Where your work is kept

| What | Where |
| --- | --- |
| Designs saved from `little-world` | `designs/my_machine.json` in your Little World folder: `~/Library/Application Support/Little World` (macOS), `%APPDATA%\Little World` (Windows), `~/.local/share/little-world` (Linux). `LITTLE_WORLD_HOME` moves the folder; `--design PATH` names one file |
| Designs saved from `examples/workshop.py` | `designs/` in the folder it was run from |
| Robots you imported | `robots/` in the same Little World folder (`LITTLE_WORLD_ROBOTS` moves it) |
| The lessons' ticks | `lessons.json` there (`LITTLE_WORLD_PROGRESS`) |

Removing the checkout and that folder removes everything.

## Tests

**`pytest` takes a long time** (*seen*: 37 minutes of test time, about 25 on two cores). 64 of
the 1,100 tests run the whole Fetch or the factory cell and take all but two of those minutes.
`python -m pytest -q -m "not slow"` leaves them out and answers in a minute or two;
`tests/slow.txt` lists them with what each took.

**Many tests are skipped** (*seen*). The window tests run only when asked, on a display:
`LITTLE_WORLD_TEST_RENDER=1 python -m pytest -q` (Linux without a display: put
`xvfb-run -a -s "-screen 0 1600x1000x24"` in front). Their windows stay hidden.

## A number that differs

`little-world evidence` prints DIFFERS when a measurement on your machine is outside the tolerance
recorded for it. A physics engine repeats itself exactly on one machine and build
(`little-world evidence --only twice` checks that it does on yours) and not across processors,
operating systems or releases, so:

- with another MuJoCo release than 3.10.0 (the doctor says which you have), differences are
  expected: results move between releases (ADR 0027);
- on another operating system or processor, small differences in times are expected and a goal
  that flips is not. Measured here, on the same machine with NumPy's AVX-512 paths switched off:
  the Fetch's cube is in the bin 4 ms earlier in a 37 s run, and 29 of the 31 measurements are
  the same to the last digit. One flip is already known: on an Intel Mac the kit cart stalls for
  good at an 18 mm curb that on Linux it clears after 11.6 s, with the same MuJoCo release
  ([OPEN LW-026](agents/OPEN.md));
- on Linux x86_64 with MuJoCo 3.10.0, every number should hold: if one does not, please open an
  issue with the file `little-world evidence --json mine.json` writes.

**The drive panel or a report says "energy from nowhere"** (*seen*, on the Curb run). A contact in
the run gave back more energy than it took - as much as lifting the lighter body 2 mm or more - which
physics does not do: the simulator made it. The line names the two bodies and when. Read that run's
result with it in mind; it is not a fault in your design. Known: a caster's wheel against a curb's
edge, one contact point with MuJoCo's multiccd off ([ADR 0074](adr/0074-energy-from-nowhere.md),
[OPEN LW-047](agents/OPEN.md)); and, in about one Fetch set-up in six, a jaw's pad as the jaws close on the cube or the palm stop holding it - at most 1.8 mJ: a contact that comes on with the pad already in the cube within one 2 ms step.
