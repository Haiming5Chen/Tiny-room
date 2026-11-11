"""`little-world`: one command for the window, its demonstrations and the project's own checks.

    little-world                    open the window, What's new on the left: one press runs a demonstration
    little-world demo NAME          open the window and run that demonstration (demo --list names them)
    little-world build              open the builder on the kit's mobile base
    little-world doctor             check this installation and say what is missing
    little-world evidence           re-run the project's headline measurements here, against the recorded numbers
    little-world sweep|radar|import-robot|camera ...   the tools the documents use, as  python -m  runs them

Everything a sub-command needs is imported when it runs, so `doctor` can say what is missing
instead of failing on it. Standard library only at import (ADR 0072).
"""
import argparse
import sys

TOOLS = {'sweep': ('little_world.inventory.sweep', 'variation sweeps of a design on a test field (ADR 0024)'),
         'radar': ('little_world.radar.__main__', 'the frontier radar and its research collection (ADR 0021, 0034)'),
         'import-robot': ('little_world.physics.importer', 'a robot from its own URDF or MJCF file into the library (ADR 0044)'),
         'camera': ('little_world.perception.__main__', 'what the Fetch table\'s depth camera sees (ADR 0032)')}


def _version():
    import little_world
    return getattr(little_world, '__version__', '?')


def _missing(error):
    """Say what an import failure means for someone who just installed, and how to find out more."""
    print(f'little-world: {type(error).__name__}: {error}', file=sys.stderr)
    print('The window needs MuJoCo, Pillow and PyOpenGL (the "workshop" extra). Run  little-world doctor  '
          'to see what is missing and the line that installs it.', file=sys.stderr)
    return 1


def _after_open(app, *actions):
    """Run `actions`, one a frame, once the window is drawing."""
    draw, queue = app.draw, list(actions)

    def frame():
        draw()
        if queue:
            queue.pop(0)()
    app.draw = frame


def _workshop(design, blueprint=None):
    from pathlib import Path
    from little_world.core.blueprint import Blueprint
    from little_world.ui.workshop import Workshop
    from little_world.userdata import design_path
    path = Path(design) if design else design_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = Blueprint.from_json(path.read_text(encoding='utf-8')) if path.exists() and blueprint is None else blueprint
    if saved is None:
        from little_world.construction.editor import starter_blueprint
        saved = starter_blueprint()
    return Workshop(path, saved)


def app(args):
    """The window, What's new open: the saved design if there is one, else the starter machine."""
    try:
        window = _workshop(args.design)
    except ImportError as error:
        return _missing(error)
    window.library_open = False
    if args.real:
        window.start_mode = 'Real'
    else:
        _after_open(window, window.show_whats_new)
    window.run(args.seconds)
    return 0


def build(args):
    """The builder (Anime) on the kit's mobile base, as examples/workshop.py opens it."""
    try:
        from little_world.robots.mobile_platform import mobile_platform_blueprint
        window = _workshop(args.design, mobile_platform_blueprint())
    except ImportError as error:
        return _missing(error)
    window.open_bench()
    window.run(args.seconds)
    return 0


def demo(args):
    """One of What's new's demonstrations, started as its button starts it (ADR 0055)."""
    from little_world.ui.whats_new import BY_ID, DEMOS
    if args.list or not args.name:
        width = max(len(d.id) for d in DEMOS)
        for d in DEMOS:
            print(f'  {d.id:<{width}}  {d.title} - {d.adr}')
        print('\nRun one with  little-world demo NAME')
        return 0
    if args.name not in BY_ID:
        print(f'little-world: no demonstration called {args.name!r}; they are: {", ".join(d.id for d in DEMOS)}', file=sys.stderr)
        return 2
    try:
        window = _workshop(args.design)
    except ImportError as error:
        return _missing(error)
    window.library_open = False
    _after_open(window, window.show_whats_new, lambda: window.start_demo(args.name))
    window.run(args.seconds)
    return 0


def doctor(args):
    from little_world.doctor import checks, report
    return report(checks(display=not args.no_window))


def evidence(args):
    from little_world.evidence import main as run
    return run(args.rest)


def tool(name):
    def run(args):
        from importlib import import_module
        try:
            module = import_module(TOOLS[name][0])
        except ImportError as error:
            return _missing(error)
        return module.main(args.rest) or 0
    return run


def parser():
    p = argparse.ArgumentParser(prog='little-world', description='Build a robot from parts, run the physics, watch it '
                                'fail, change the design, try again. With no command: open the window.')
    p.add_argument('--version', action='version', version=f'little-world {_version()}')

    def opens(parser):
        parser.add_argument('--design', help='the design file to open and save to (default: in your Little World folder)')
        parser.add_argument('--seconds', type=float, help='close the window after this long (a smoke run)')
    window = argparse.ArgumentParser(add_help=False)
    opens(window)
    opens(p)                        # with no command, the window's own options
    p.add_argument('--real', action='store_true', help='open in Real mode: complete robots and the factory cell')
    p.set_defaults(run=app)
    sub = p.add_subparsers(metavar='command')
    s = sub.add_parser('app', parents=[window], help="open the window, What's new on the left (the default)")
    s.add_argument('--real', action='store_true', help='open in Real mode: complete robots and the factory cell')
    s.set_defaults(run=app)
    s = sub.add_parser('build', parents=[window], help="open the builder on the kit's mobile base")
    s.set_defaults(run=build)
    s = sub.add_parser('demo', parents=[window], help="run one of What's new's demonstrations in the window")
    s.add_argument('name', nargs='?', help='which one (see --list)')
    s.add_argument('--list', action='store_true', help='name them')
    s.set_defaults(run=demo)
    s = sub.add_parser('doctor', help='check this installation and say what is missing')
    s.add_argument('--no-window', action='store_true', help='skip the OpenGL window check (a server, CI)')
    s.set_defaults(run=doctor)
    s = sub.add_parser('evidence', add_help=False,
                       help="re-run the project's headline measurements here and compare them with the recorded numbers")
    s.add_argument('rest', nargs=argparse.REMAINDER)
    s.set_defaults(run=evidence)
    for name, (_, about) in TOOLS.items():
        s = sub.add_parser(name, add_help=False, help=about)
        s.add_argument('rest', nargs=argparse.REMAINDER)
        s.set_defaults(run=tool(name))
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # A tool's own options are the tool's: hand everything after its name on untouched.
    if argv and argv[0] in (*TOOLS, 'evidence'):
        args = argparse.Namespace(rest=argv[1:])
        return (evidence if argv[0] == 'evidence' else tool(argv[0]))(args)
    args = parser().parse_args(argv)
    return args.run(args)


if __name__ == '__main__':
    raise SystemExit(main())
