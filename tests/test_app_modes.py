import os
import pytest
pytestmark=pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires native window')


def test_one_window_retains_both_workspaces_and_supports_real_arms(tmp_path,monkeypatch):
    import glfw
    from dataclasses import replace
    from little_world.ui.workshop import Workshop
    from little_world.construction.editor import starter_blueprint
    from little_world.programming.program import Program,Block
    from little_world.core.component import RobotServo
    opened=[];create=glfw.create_window
    def tracked(*args,**kwargs):
        window=create(*args,**kwargs);opened.append(window);return window
    monkeypatch.setattr(glfw,'create_window',tracked)
    app=Workshop(tmp_path/'kit.json',starter_blueprint());app.factory_recipe_path=tmp_path/'cell.json'
    original=app.editor.blueprint;original_draw=app.draw;finished=False
    def use():
        nonlocal finished
        original_draw()
        if finished:return
        app.program=Program((Block(duration=.3),))
        app.switch_workspace('Real');real=app.active_workspace
        assert real.window is app.window and real.app_mode=='Real'
        real.apply_recipe(real.recipe.moved('input',(.4,.01)));recipe=real.recipe
        real.preview_cycle();real.start_cycle()
        real.tick_program();real.state=real.world.step(real.joint_commands())
        runtime=real.data.qpos.copy()
        real.switch_workspace('Anime')
        assert app.active_workspace is app and real.paused
        assert app.editor.blueprint==original and len(app.program.blocks)==1
        app.switch_workspace('Real');assert app.active_workspace is real
        assert real.recipe==recipe and (real.data.qpos==runtime).all() and real.paused
        real.reset_cell()
        glfw.set_window_size(app.window,1040,740);real.draw()
        for i,a in enumerate(real.buttons):
            for b in real.buttons[i+1:]:
                assert not (a.x<b.x+b.width and b.x<a.x+a.width and a.y<b.y+b.height and b.y<a.y+a.height),(a.label,b.label)
        for asset,axes in [('franka_fr3',7),('kinova_gen3',7),('ur5e',6),('franka_panda',8)]:
            real.select_robot(asset);assert real.joint_lab
            assert sum(isinstance(c,RobotServo) for c in real.editor.blueprint.components)==axes
            real.draw()
            assert any(b.label=='Program sequence' for b in real.buttons)
            real.joint_example();assert len(real.program.blocks)==3
            real.start_program()
            for _ in range(300):
                real.tick_program();real.state=real.world.step(real.joint_commands())
            assert real.runner.state in ('running','completed')
            real.reset_cell();assert real.runner.state!='running'
        real.select_experiment('Pick and place');assert not real.joint_lab
        assert real.recipe==recipe
        real.draw();assert any(b.label=='Anime' for b in real.buttons)
        real.choose_robot();real.draw();assert real.dialog is not None
        real.dialog=None
        real.switch_workspace('Anime');assert app.active_workspace is app
        assert len(opened)==1
        finished=True;glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(60);assert finished
