import pytest
from little_world.factory.teaching import TeachingBook, TaughtPosition


def test_positions_roundtrip_replace_and_validation():
    a=TaughtPosition('Above product',(.4,0,1.0))
    book=TeachingBook().saved(a).saved(TaughtPosition('Drop here',(.3,.25,1.1)))
    assert TeachingBook.from_json(book.to_json())==book
    assert len(book.saved(TaughtPosition(a.name,(.5,0,1.0))).positions)==2
    assert len(book.removed(a.name).positions)==1
    for name,point in [('',(0,0,1)),('Bad',(0,0,float('nan'))),('Bad',(0,1))]:
        with pytest.raises(ValueError):TaughtPosition(name,point)
    with pytest.raises(ValueError):TeachingBook.from_json('{"version": 99, "positions": []}')


def test_teaching_plans_without_teleport_and_moves_with_servos():
    pytest.importorskip('mujoco')
    import numpy as np
    from little_world.factory.teaching_native import TeachingMotion
    from little_world.factory.scene import factory_scene
    from little_world.physics.mujoco_backend import MujocoBackend
    b=MujocoBackend();b.compile(factory_scene(),.002)
    try:
        motion=TeachingMotion(b);before=b.data.qpos.copy();ctrl=b.data.ctrl.copy()
        target=(.4,0,1.02);motion.preview(target)
        assert np.array_equal(b.data.qpos,before) and np.array_equal(b.data.ctrl,ctrl)
        motion.start()
        for _ in range(6000):
            b.step(motion.commands(.002))
            if motion.state!='moving':break
        assert motion.state=='reached',motion.message
        assert np.linalg.norm(motion.ik.tool(b.data)-target)<.012
        with pytest.raises(ValueError):motion.preview((4,0,1))
        assert motion.target is None
        with pytest.raises(ValueError):motion.start()
    finally:b.close()

import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires native window')
def test_teaching_window_drag_save_recall_and_robot_guard(tmp_path,monkeypatch):
    import glfw
    import numpy as np
    from little_world.ui.factory_workspace import FactoryWorkshop
    app=FactoryWorkshop(tmp_path/'cell.json');draw=app.draw;done=False
    def use():
        nonlocal done
        draw()
        if done:return
        app.select_experiment('Teach positions');draw()
        assert not app.control_panel
        assert any(b.label=='Move to target' and not b.enabled for b in app.buttons)
        before=app.data.qpos.copy();pixel=app.project_table(app.teach_point)
        monkeypatch.setattr(glfw,'get_cursor_pos',lambda window:pixel)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        assert app.teach_drag
        original=app.teach_point.copy();app.mouse_move(app.window,pixel[0]+12,pixel[1])
        assert not np.array_equal(app.teach_point,original)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        assert not app.teach_drag
        app.preview_teaching();assert app.teach_motion.target is not None
        assert np.array_equal(app.data.qpos,before)
        app.save_taught('Above product');assert app.teaching_path.exists()
        app.change_target((4,0,1));app.preview_teaching();assert app.teach_motion.state=='unreachable'
        app.recall_teaching();app.dialog['apply']('Above product');app.dialog=None
        assert app.teach_motion.target is not None
        app.move_teaching()
        for _ in range(6000):
            app.tick_program();app.state=app.world.step(app.joint_commands())
            if app.paused:break
        assert app.teach_motion.state=='reached'
        app.reset_cell();assert app.teach_book.positions
        app.select_robot('ur5e')
        with pytest.raises(ValueError,match='Panda'):app.select_experiment('Teach positions')
        app.select_robot('franka_panda');app.select_experiment('Teach positions');draw()
        glfw.set_window_size(app.window,1040,740);draw()
        for i,a in enumerate(app.buttons):
            for b in app.buttons[i+1:]:
                assert not(a.x<b.x+b.width and b.x<a.x+a.width and a.y<b.y+b.height and b.y<a.y+a.height),(a.label,b.label)
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(30);assert done
