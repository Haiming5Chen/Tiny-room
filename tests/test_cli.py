"""`little-world`: one command for the window, its demonstrations and the project's own checks (ADR 0072).

Someone who has just cloned the repository should reach a running window, or a plain sentence
about what is missing, without reading the manual: the command opens the window with What's new
on the left, `doctor` says what an installation lacks and the line that mends it, and the tools
the documents use are reachable under the same name.
"""
import io
import os
import sys
import tomllib
import types
from pathlib import Path

import pytest

from little_world import cli, doctor, userdata

ROOT = Path(__file__).resolve().parents[1]
WINDOW = pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')


def test_the_package_installs_a_little_world_command_with_one_version():
    import little_world
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    assert project['project']['scripts'] == {'little-world': 'little_world.cli:main'}
    assert project['project']['dynamic'] == ['version'], "the version is the package's own, not written twice"
    assert project['tool']['setuptools']['dynamic']['version'] == {'attr': 'little_world.__version__'}
    assert little_world.__version__.count('.') == 2
    assert (ROOT / 'src' / 'little_world' / '__main__.py').exists(), "python -m little_world is the same command"


def test_the_version_and_the_help_name_every_command(capsys):
    import little_world
    with pytest.raises(SystemExit) as stop:
        cli.main(['--version'])
    assert stop.value.code == 0 and capsys.readouterr().out.strip() == f'little-world {little_world.__version__}'
    with pytest.raises(SystemExit):
        cli.main(['--help'])
    said = capsys.readouterr().out
    for command in ('app', 'build', 'demo', 'doctor', 'evidence', 'sweep', 'radar', 'import-robot', 'camera'):
        assert command in said, command
    assert 'With no command: open the window' in said


def test_demo_names_the_demonstrations_and_refuses_one_it_does_not_have(capsys):
    from little_world.ui.whats_new import DEMOS
    assert cli.main(['demo', '--list']) == 0
    said = capsys.readouterr().out
    assert all(d.id in said and d.title in said for d in DEMOS)
    assert cli.main(['demo']) == 0, "no name: the list"
    capsys.readouterr()
    assert cli.main(['demo', 'no-such-demo']) == 2
    assert 'no demonstration called' in capsys.readouterr().err


def test_a_window_that_cannot_import_its_needs_says_to_run_the_doctor(monkeypatch, capsys):
    def missing(design, blueprint=None):
        raise ImportError("No module named 'mujoco'")
    monkeypatch.setattr(cli, '_workshop', missing)
    for command in ([], ['build'], ['demo', 'felt']):
        assert cli.main(command) == 1, command
        said = capsys.readouterr().err
        assert "No module named 'mujoco'" in said and 'little-world doctor' in said, "what failed, and what to run"


def test_a_tool_is_handed_everything_after_its_name(monkeypatch):
    got = {}
    fake = types.ModuleType('fake_tool')
    fake.main = lambda argv: got.setdefault('argv', argv) and 0
    monkeypatch.setitem(sys.modules, 'fake_tool', fake)
    monkeypatch.setitem(cli.TOOLS, 'sweep', ('fake_tool', 'a stand-in'))
    assert cli.main(['sweep', '--field', 'fetch', '--design', 'mobile_manipulator', '--help']) == 0
    assert got['argv'] == ['--field', 'fetch', '--design', 'mobile_manipulator', '--help'], "its own --help and --design, untouched"
    for name, (module, about) in cli.TOOLS.items():
        assert about and (name == 'sweep' or __import__(module, fromlist=['main']).main), name


def test_designs_are_kept_in_the_users_own_folder_or_where_they_say(monkeypatch, tmp_path):
    monkeypatch.setenv('LITTLE_WORLD_HOME', str(tmp_path / 'mine'))
    assert userdata.home() == tmp_path / 'mine'
    assert userdata.design_path() == tmp_path / 'mine' / 'designs' / 'my_machine.json'
    monkeypatch.delenv('LITTLE_WORLD_HOME')
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    place = userdata.home()
    assert place.name in ('little-world', 'Little World'), "the platform's place for an application's own data"
    assert Path.cwd() not in (place, *place.parents) or place.is_relative_to(Path.home()), "not the folder it was run from"


def test_the_doctor_reads_each_need_and_says_the_line_that_mends_it():
    assert doctor.python_version((3, 13, 0)).ok and not doctor.python_version((3, 13, 0)).fix
    old = doctor.python_version((3, 10, 9))
    assert not old.ok and old.found == '3.10.9' and '3.11' in old.fix
    gone = doctor.module('no_such_module_here', 'Nothing', 'pip install nothing')
    assert not gone.ok and 'not importable' in gone.found and gone.fix == 'pip install nothing'
    assert doctor.module('json', 'JSON', '').ok
    assert doctor.PINNED == '3.10.0' and doctor.PINNED in (ROOT / 'pyproject.toml').read_text(encoding='utf-8')


def test_the_doctors_report_fails_only_on_what_the_window_needs():
    C = doctor.Check
    out = io.StringIO()
    ready = [C('Python', True, '3.13.1'), C('MuJoCo', True, '3.10.0')]
    assert doctor.report(ready, out) == 0 and 'Ready: run  little-world' in out.getvalue()
    out = io.StringIO()
    noted = ready + [C('Window', False, 'no display', 'use a desktop session', needed=False)]
    assert doctor.report(noted, out) == 0
    assert 'note  Window' in out.getvalue() and '-> use a desktop session' in out.getvalue() and 'with 1 note above' in out.getvalue()
    out = io.StringIO()
    broken = ready + [C('Pillow', False, 'not importable', "python -m pip install -e '.[workshop]'")]
    assert doctor.report(broken, out) == 1
    assert 'FAIL  Pillow' in out.getvalue() and '1 to fix before the window will open' in out.getvalue()


def test_the_doctor_finds_this_installation_ready_without_a_display(capsys, monkeypatch, tmp_path):
    pytest.importorskip('mujoco')
    monkeypatch.setenv('LITTLE_WORLD_HOME', str(tmp_path / 'home'))
    found = doctor.checks(display=False)
    assert [c.name for c in found] == ['Python', 'MuJoCo', 'NumPy', 'Pillow', 'PyOpenGL', 'Assets', 'Physics', 'Your designs']
    assert all(c.ok for c in found), [(c.name, c.found) for c in found if not c.ok]
    physics = next(c for c in found if c.name == 'Physics')
    assert 'rests at 5.0 cm' in physics.found, "a 10 cm block dropped on the floor: the simulator runs"
    assert cli.main(['doctor', '--no-window']) == 0 and 'Ready' in capsys.readouterr().out


@WINDOW
def test_the_bare_command_opens_the_window_on_whats_new_and_demo_starts_one(monkeypatch, tmp_path):
    from little_world.ui import workshop
    opened = []
    run = workshop.Workshop.run

    def spy(self, seconds=None, *a, **k):
        opened.append(self)
        return run(self, seconds, *a, **k)
    monkeypatch.setattr(workshop.Workshop, 'run', spy)
    design = str(tmp_path / 'designs' / 'mine.json')
    assert cli.main(['--design', design, '--seconds', '2']) == 0
    app = opened[-1]
    assert app.active_tab == 'Guide' and app.guide_view == 'New', "What's new on the left"
    assert cli.main(['demo', 'felt', '--design', design, '--seconds', '4']) == 0
    app = opened[-1]
    assert app.demo == 'felt' and app.field_id == 'fetch', "started as its button starts it"
    assert app.live_disturbance.label == 'cube moved 5 cm sideways, 2 s later'
    assert cli.main(['build', '--design', design, '--seconds', '2']) == 0
    assert Path(design).parent.is_dir() and not Path(design).exists(), "a design is written when it is saved, not when it is opened"
