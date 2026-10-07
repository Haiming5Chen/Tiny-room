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
