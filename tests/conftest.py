"""Native regression windows stay hidden and cannot consume desktop input."""
import os
import pytest

@pytest.fixture(autouse=True)
def hidden_native_windows(monkeypatch):
    if os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1':return
    glfw=pytest.importorskip('glfw')
    create=glfw.create_window
    def hidden(*args,**kwargs):
        glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
        return create(*args,**kwargs)
    monkeypatch.setattr(glfw,'create_window',hidden)
    # GLFW cannot warp a cursor into an invisible window on macOS. Keep a
    # synthetic cursor for tests that explicitly set it; no OS pointer movement.
    cursor=[(0.,0.)]
    monkeypatch.setattr(glfw,'set_cursor_pos',lambda window,x,y:cursor.__setitem__(0,(x,y)))
    monkeypatch.setattr(glfw,'get_cursor_pos',lambda window:cursor[0])
    swap_interval=glfw.swap_interval
    monkeypatch.setattr(glfw,'swap_interval',lambda interval:swap_interval(0))


@pytest.fixture(autouse=True)
def own_robot_library(tmp_path_factory, monkeypatch):
    """No test reads or writes the user's robot library (ADR 0044): each gets an empty one."""
    monkeypatch.setenv('LITTLE_WORLD_ROBOTS', str(tmp_path_factory.mktemp('robots')))
    from little_world.assets import robot_library
    robot_library.forget()
    yield
    robot_library.forget()


@pytest.fixture(autouse=True)
def own_lesson_progress(tmp_path_factory, monkeypatch):
    """No test reads or writes the user's lesson progress (ADR 0046)."""
    monkeypatch.setenv('LITTLE_WORLD_PROGRESS', str(tmp_path_factory.mktemp('lessons') / 'lessons.json'))


def _slow_list():
    """tests/slow.txt as {'test_file.py::test_name[param]': seconds} (scripts/test_times.py writes it)."""
    path = os.path.join(os.path.dirname(__file__), 'slow.txt')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as lines:
        rows = [line.split(None, 1) for line in lines if line.strip() and not line.startswith('#')]
    return {name.strip(): float(seconds) for seconds, name in rows}


def pytest_collection_modifyitems(config, items):
    """The quick tier (ADR 0073): tests listed in tests/slow.txt, and every window test, are marked
    `slow`, so that `pytest -m "not slow"` answers in a couple of minutes; with no `-m` everything
    runs, as before. Window tests are also marked `window`."""
    listed = _slow_list()
    for item in items:
        name = f'{os.path.basename(str(item.fspath))}::{item.name}'
        window = any('LITTLE_WORLD_TEST_RENDER' in str(m.args) or str(m.kwargs.get('reason', '')).startswith('requires')
                     for m in item.iter_markers('skipif'))
        if window:
            item.add_marker(pytest.mark.window)
        if window or name in listed:
            item.add_marker(pytest.mark.slow)
