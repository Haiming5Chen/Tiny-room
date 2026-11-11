# From a clone to a running window: one command, a doctor, a README someone can read

**Problem.** The owner asked (10 Nov) that people be able to take this from GitHub and use it.
Looked at as a stranger would:
- *What GitHub has* (`git ls-remote`, 10 Nov): one branch, `main`, at the first import of 24 Sep -
  9 decision records, 163 test functions. The working branch is 89 commits ahead of it (62
  records, 617 test functions) and was never pushed: every "shipped" since then was a bundle
  copied into a folder on the owner's Mac, waiting on a double-click that the publish log
  shows happened once, on 24 Sep. Nothing here can push; what it can do is make what would be
  pushed worth having.
- *What the README asks of a reader*: 1,158 lines; the install lines come at line 367, after 58
  paragraphs of features; three ways to start the window (`examples/workshop.py`,
  `examples/launch_desktop.py`, a Dock launcher made for one Mac), none of them a command; a
  design saved to `designs/` in whatever folder it was run from.
- *What a broken installation says*: installed without its extra, the window's first word is a
  traceback ending in `No module named 'mujoco'`.
- *What does work*: from a clean clone into a new environment, `pip install '.[workshop]'` took
  26 s and the installed package opened its window from an empty folder - the package data is
  complete. Nothing said so, and nothing checked it.

**Does an existing simulator solve it? Can we wrap it?** Not a physics question. Python's own
packaging does what is needed: a console script, an extra, `python -m`.

**Unique contribution.**
- *One command* (`little_world/cli.py`, `[project.scripts]`, `python -m little_world`):
  `little-world` opens the window with What's new on the left - one press runs a demonstration;
  `little-world demo NAME` starts one (`--list` names the fifteen); `little-world build` opens
  the builder on the kit's mobile base; `--real` opens Real mode. The tools the documents use
  are under the same name and take their own options untouched: `sweep`, `radar`,
  `import-robot`, `camera`, `evidence` (ADR 0073). The package's version is its own
  (`little_world.__version__`, 0.2.0), read by the build.
- *A doctor* (`little_world/doctor.py`): `little-world doctor` checks Python, MuJoCo and whether
  it is the pinned release, NumPy, Pillow, PyOpenGL, the package's assets, half a second of
  physics (a 10 cm block dropped on a floor must rest 5 cm up), the user's folder and an OpenGL
  window, a line each; for anything missing it prints the line that mends it. No display is a
  note, not a failure: everything but the window still runs. A window command that cannot
  import its needs says to run the doctor instead of printing a traceback.
- *A place for a user's designs* (`little_world/userdata.py`): an installed copy has no
  `designs/` folder beside it, so the command keeps designs where the robot library and the
  lessons already are - the platform's place for an application's data; `LITTLE_WORLD_HOME`
  moves it, `--design` names a file. `examples/workshop.py` is unchanged.
- *A README someone can read*: 114 lines - what it is, three commands to a window, the first
  ten minutes, what is in it in five points, how to check it, where things are, what has been
  run where. Its 58 feature paragraphs are `docs/FEATURES.md` and its manual `docs/MANUAL.md`,
  moved whole with their links rewritten; `docs/TROUBLESHOOTING.md` is new, each item marked
  *seen* or *expected*. A test keeps the README under 200 lines and its quick start at three
  commands; new feature paragraphs go to `docs/FEATURES.md` (AGENTS.md's convention, changed).
  `CHANGELOG.md` says what changed for a user, version by version.

**Blueprint and builder.** Untouched. The core stays standard-library only: `cli`, `doctor` and
`userdata` import nothing else until a command runs.

**Result.** From a clean clone, the README's three commands: install 26 s, then the window, What's
new on the left, eight demonstrations a page (ADR 0055's amendment). `little-world doctor` on the
machine the suites run on: nine lines, all ok, "Ready"; without a display, eight ok and a note.
`little-world demo felt` starts the Fetch with its disturbance armed, as its button does.

Held by `tests/test_cli.py` (10, one a window test): the command and its one version; the help
names every command; `demo` lists and refuses; a window that cannot import says what failed and
to run the doctor; a tool gets everything after its name; designs go to the user's folder or
where they say; the doctor's checks, its report's three outcomes, and this installation found
ready without a display; in the window, the bare command opens on What's new, `demo felt` starts
it, and opening a design writes nothing. `tests/test_evidence.py` holds the README's length and
quick start. Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.

**Boundaries.** Nothing is published by this: the branch reaches GitHub when the owner pushes it,
and until then the README's `git clone` line fetches the import of 24 Sep. The command was run on
Linux only; macOS (where the window is used), Apple silicon and Windows have MuJoCo 3.10.0 wheels
and are untried - the doctor is how to find out. The `pipx` line was tried against a local copy
of the repository, not against GitHub. There is no installer and no application bundle; the Dock
launcher of `scripts/install_desktop.py` is still one Mac's. No licence has been chosen: people
may read this and may not yet use it - the owner's decision, and the first thing a user will ask.
