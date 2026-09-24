from dataclasses import replace
import pytest
from little_world.factory.recipe import CellRecipe

def test_recipe_roundtrip_and_immutable_move():
    recipe=CellRecipe();changed=recipe.moved('input',(.40,.01))
    assert CellRecipe.from_json(changed.to_json())==changed
    assert recipe.point('input')==(.45,0)

@pytest.mark.parametrize('point,reason',[((2,0),'worktable'),((.1,0),'robot base'),((.44,-.24),'overlap'),((.70,.4),'camera support')])
def test_recipe_explains_bad_placements(point,reason):
    with pytest.raises(ValueError,match=reason):CellRecipe().moved('input',point)

def test_source_and_destination_must_differ():
    with pytest.raises(ValueError,match='different'):replace(CellRecipe(),source='Blue')

@pytest.mark.parametrize('source,destination',[('input','Amber'),('Amber','Blue')])
def test_authored_recipe_physical_cycle(source,destination):
    pytest.importorskip('mujoco')
    from little_world.factory.scene import factory_scene
    from little_world.factory.controller import FactoryCycle
    from little_world.physics.mujoco_backend import MujocoBackend
    recipe=replace(CellRecipe().moved('input',(.40,.01)),source=source,destination=destination)
    backend=MujocoBackend();backend.compile(factory_scene(recipe=recipe),.002)
    try:
        cycle=FactoryCycle(backend,source=source);cycle.plan(destination);cycle.start()
        for _ in range(18000):
            backend.step(cycle.commands(.002))
            if cycle.state in ('completed','failed'):break
        assert cycle.state=='completed',cycle.message
    finally:backend.close()

import os
@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires OpenGL')
def test_native_drag_task_guide_and_save(tmp_path):
    import glfw
    from little_world.ui.factory_workspace import FactoryWorkshop
    from little_world.factory.scene import TABLE
    app=FactoryWorkshop(tmp_path/'cell.json');draw=app.draw;done=False
    def click(name):
        x,y=app.project_table((*app.recipe.point(name),TABLE+.025))
        glfw.set_cursor_pos(app.window,x,y)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        while app.events:app.events.pop(0)()
    def drag(name,target):
        x,y=app.project_table((*app.recipe.point(name),TABLE+.025))
        glfw.set_cursor_pos(app.window,x,y)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        assert app.tray_drag is not None
        x,y=app.project_table((*target,TABLE+.025))
        glfw.set_cursor_pos(app.window,x,y);app.mouse_move(app.window,x,y)
        app.mouse(app.window,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        while app.events:app.events.pop(0)()
    def use():
        nonlocal done
        draw()
        if done:return
        original=app.recipe
        drag('input',(.40,.01));assert app.recipe.point('input')==(.4,.01)
        valid=app.recipe
        drag('input',(.95,0));assert app.recipe==valid
        assert 'worktable' in app.authoring_note
        app.choose_mode('Set task');click('Amber');assert app.pending_source=='Amber'
        click('Blue');assert app.recipe.source=='Amber' and app.destination=='Blue'
        app.save_cell();saved=CellRecipe.from_json(app.recipe_path.read_text());assert saved==app.recipe
        app.undo_recipe();assert app.recipe==valid
        app.enter_guide();assert app.guided
        app.start_cycle(True)
        for _ in range(6000):
            app.tick_program();app.state=app.world.step(app.joint_commands())
            if app.paused:break
        assert app.paused and app.cycle.index==1 and app.guide_caption()[0]=='Lower'
        app.try_yourself();assert app.building and not app.guided and app.recipe==valid
        loaded=FactoryWorkshop(app.recipe_path);assert loaded.recipe==saved;loaded.world.close()
        app.undo_recipe();assert app.recipe==original
        done=True;glfw.set_window_should_close(app.window,True)
    app.draw=use;app.run(30);assert done
