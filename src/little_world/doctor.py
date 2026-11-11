"""`little-world doctor`: is this installation able to run, and if not, what is missing?

Each check is one line: what was looked at, what was found, and - when it is wrong - the one
thing to do about it. Nothing here needs a display except the last check, which says so.
Standard library only until a check imports what it checks.
"""
import importlib
import platform
import sys
from dataclasses import dataclass

PINNED = '3.10.0'                   # the MuJoCo release every number in the documents was measured on (ADR 0027)
INSTALL = 'python -m pip install "little-world[workshop] @ git+https://github.com/Haiming5Chen/Tiny-room"'
EXTRA = "python -m pip install -e '.[workshop]'"


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    found: str
    fix: str = ''
    needed: bool = True             # False: the window works without it; a note, not a failure


def python_version(version=None):
    v = tuple(version or sys.version_info[:3])
    ok = v >= (3, 11)
    return Check('Python', ok, '.'.join(str(n) for n in v), '' if ok else 'Little World needs Python 3.11 or newer')


def module(name, label, fix, needed=True):
    try:
        found = importlib.import_module(name)
    except Exception as error:                      # a broken install raises more than ImportError
        return Check(label, False, f'not importable ({type(error).__name__}: {error})'[:110], fix, needed)
    return Check(label, True, str(getattr(found, '__version__', 'present')), needed=needed)


def mujoco_release():
    try:
        import mujoco
    except Exception as error:
        return Check('MuJoCo', False, f'not importable ({type(error).__name__})',
                     f'install the simulator with the window\'s other needs: {EXTRA}  (from a checkout), or  {INSTALL}')
    if mujoco.__version__ != PINNED:
        return Check('MuJoCo', True, f'{mujoco.__version__} - the documents\' numbers were measured on {PINNED}',
                     f'runs, but physics results move between releases: for the recorded numbers, pip install mujoco=={PINNED}',
                     needed=False)
    return Check('MuJoCo', True, mujoco.__version__)


def assets():
    try:
        from importlib import resources
        root = resources.files('little_world.assets')
        robots = sum(1 for p in (root / 'robots').iterdir() if p.is_dir())
        textures = sum(1 for p in (root / 'data').iterdir() if p.name.endswith('.rgb.gz'))
    except Exception as error:
        return Check('Assets', False, f'not found ({type(error).__name__}: {error})'[:110],
                     'the package was installed without its data files: install it again from the repository')
    ok = robots >= 4 and textures >= 1
    return Check('Assets', ok, f'{robots} robot models, {textures} textures',
                 '' if ok else 'the package was installed without its data files: install it again from the repository')


def physics(steps=500):
    """Half a kilogram dropped 10 cm onto the floor: the simulator runs and the box comes to rest."""
    try:
        import time
        from little_world import Blueprint, Entity, World
        from little_world.components import Transform, box
        from little_world.core.material import Material
        from little_world.core.scene import Scene
        from little_world.physics.mujoco_backend import MujocoBackend
        wood = Material('wood', 600, .5, (.8, .6, .4, 1))
        design = Blueprint((box('block', (.1, .1, .1), 'wood', dynamic=True, transform=Transform((0, 0, .15))),), (wood,))
        floor = Blueprint((box('floor', (2, 2, .02), 'wood', transform=Transform((0, 0, -.01))),), (wood,))
        started = time.perf_counter()
        with World(MujocoBackend(), Scene((Entity('ground', floor), Entity('drop', design)))) as world:
            state = world.start()
            for _ in range(steps):
                state = world.step({})
            height = state.bodies['drop/block'].pose.position[2]
        took = time.perf_counter() - started
    except Exception as error:
        return Check('Physics', False, f'{type(error).__name__}: {error}'[:120],
                     'the simulator did not run a falling block: run  python -m pytest -q tests/test_contracts.py  for the detail')
    ok = abs(height - .05) < .005
    return Check('Physics', ok, f'a block dropped 10 cm rests at {100 * height:.1f} cm; {steps} steps in {1000 * took:.0f} ms',
                 '' if ok else 'a 10 cm block should rest with its centre 5 cm up: this MuJoCo build disagrees with the pinned one')


def window():
    """A hidden window with an OpenGL context: what the app needs to draw."""
    try:
        import glfw
    except Exception as error:
        return Check('Window', False, f'glfw not importable ({type(error).__name__})', f'{EXTRA}')
    try:
        if not glfw.init():
            raise RuntimeError('GLFW could not start')
        try:
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
            handle = glfw.create_window(64, 64, 'little-world doctor', None, None)
            if not handle:
                raise RuntimeError('no OpenGL window could be made')
            glfw.make_context_current(handle)
            import mujoco
            mujoco.MjrContext(mujoco.MjModel.from_xml_string('<mujoco/>'), mujoco.mjtFontScale.mjFONTSCALE_100)
            glfw.destroy_window(handle)
        finally:
            glfw.terminate()
    except Exception as error:
        linux = sys.platform.startswith('linux')
        return Check('Window', False, f'{type(error).__name__}: {error}'[:110],
                     'no display here: the tests, sweeps and `little-world evidence` still run; for the window use a '
                     'desktop session' + (', or  xvfb-run -a little-world' if linux else ''), needed=False)
    return Check('Window', True, 'an OpenGL window opens')


def data_folder():
    from little_world.userdata import home
    place = home()
    try:
        place.mkdir(parents=True, exist_ok=True)
        probe = place / '.write-test'
        probe.write_text('ok')
        probe.unlink()
    except OSError as error:
        return Check('Your designs', False, f'{place}: {error}'[:120],
                     'choose a folder you can write to: set LITTLE_WORLD_HOME, or open with  little-world --design PATH')
    return Check('Your designs', True, str(place))


def checks(display=True):
    found = [python_version(), mujoco_release(),
             module('numpy', 'NumPy', EXTRA), module('PIL', 'Pillow', EXTRA), module('OpenGL', 'PyOpenGL', EXTRA),
             assets(), physics(), data_folder()]
    if display:
        found.append(window())
    return found


def report(found, out=None):
    """Print the checks; 0 when everything the window needs is there."""
    out = out or sys.stdout
    import little_world
    version = getattr(little_world, '__version__', '?')
    print(f'Little World {version} on {platform.system()} {platform.machine()}, Python {platform.python_version()}', file=out)
    width = max(len(c.name) for c in found)
    for c in found:
        mark = 'ok  ' if c.ok and not c.fix else ('note' if c.ok or not c.needed else 'FAIL')
        print(f'  {mark}  {c.name:<{width}}  {c.found}', file=out)
        if c.fix:
            print(f'        {"":<{width}}  -> {c.fix}', file=out)
    failed = [c for c in found if not c.ok and c.needed]
    notes = [c for c in found if c.fix and c not in failed]
    if failed:
        print(f'\n{len(failed)} to fix before the window will open.', file=out)
        return 1
    print('\nReady' + (f', with {len(notes)} note{"s" if len(notes) != 1 else ""} above' if notes else '')
          + ': run  little-world  to open the window, or  little-world demo --list  for what to watch.', file=out)
    return 0
