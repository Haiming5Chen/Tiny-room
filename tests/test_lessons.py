"""Contracts for the first hour's lessons, checked by the app (ADR 0046, FR-033).

The defect: Little World taught by a guide tab of starter kits and by documents; nothing said
what to try first, or noticed when it was done. A tutorial that is done, not watched, is what
helped novices learn an arm's blocks (the CoBlox study, FR-033). Each lesson is data and a
check; each can be finished in the window through the actions a user has - the test for each
does exactly that.
"""
import json
import os

import pytest

from little_world import lessons
from little_world.lessons import BY_ID, LESSONS, Facts, Progress, check_all


def test_five_lessons_each_with_a_goal_steps_a_setup_and_a_check_that_says_what_is_missing():
    assert [x.id for x in LESSONS] == ['drive', 'tool', 'program', 'import', 'sweep']
    for lesson in LESSONS:
        assert lesson.goal and 1 <= len(lesson.steps) <= 4 and lesson.setup
        done, missing = lesson.check(Facts())
        assert not done and missing, "with nothing done, each says what to do first"


def test_each_check_reads_the_work_as_the_window_reports_it():
    doorway = dict(through='met', parked='met', frame='kept', upright='kept')
    assert BY_ID['drive'].check(Facts(field='doorway', goals=tuple(doorway.items())))[0]
    touched = Facts(field='doorway', goals=tuple({**doorway, 'frame': 'failed'}.items()))
    assert BY_ID['drive'].check(touched) == (False, 'The door frame was touched: press Stop, then try again.')
    assert not BY_ID['drive'].check(Facts(field='doorway', goals=(('through', 'met'),)))[0]
    assert BY_ID['tool'].check(Facts(field='pick_place', tool_off=.01))[0]
    assert BY_ID['tool'].check(Facts(field='pick_place', tool_off=.1)) == (False, 'The jaws are 10 cm from the cube.')
    assert not BY_ID['tool'].check(Facts(field='pick_place'))[0], "not before the tool has been away"

    picked = Facts(field='pick_place', blocks=('pose', 'grasp'), ran='completed', goals=(('lifted', 'met'),))
    assert BY_ID['program'].check(picked)[0]
    assert not BY_ID['program'].check(Facts(field='pick_place', blocks=('pose',), ran='completed', goals=(('lifted', 'met'),)))[0]
    assert BY_ID['import'].check(Facts(robot='user:sample-arm', moved=12.))[0]
    assert not BY_ID['import'].check(Facts(robot='ur5e', moved=40.))[0], "a robot of one's own"
    assert BY_ID['sweep'].check(Facts(swept='sprint'))[0]


def test_progress_is_kept_outside_the_repository_and_moves_on_to_the_next_lesson(tmp_path, monkeypatch):
    where = tmp_path / 'progress' / 'lessons.json'
    monkeypatch.setenv(lessons.ENVIRONMENT, str(where))
    progress = Progress()
    assert progress.current == 'drive' and not progress.done
    assert check_all(progress, Facts(swept='sprint')) == ['sweep']
    assert progress.current == 'drive', "finishing another lesson leaves the current one"
    assert check_all(progress, Facts(swept='sprint')) == [], "once"
    progress.choose('tool')
    assert progress.finish('tool') and progress.current == 'drive'
    again = Progress()
    assert set(again.done) == {'sweep', 'tool'} and again.current == 'drive'
    assert json.loads(where.read_text(encoding='utf-8'))['current'] == 'drive'
    where.write_text('{not json', encoding='utf-8')
    assert Progress().done == {}, "a spoilt file starts afresh"
    with pytest.raises(ValueError):
        progress.choose('flying')


def test_the_sample_arm_imports_with_a_servo_on_each_joint_and_nothing_to_check():
    from little_world.physics.importer import import_robot
    from little_world.ui.lessons_panel import SAMPLE
    asset, report = import_robot(SAMPLE)
    assert asset == 'user:sample-arm' and not report.of('warning')
    assert 'each of its 3 driven joints' in report.of('added')[0]


# -- in the window: each lesson finished through the actions a user has -------------------

WINDOW = pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')


def window(tmp_path):
    from little_world.construction.editor import starter_blueprint
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'design.json', starter_blueprint())
    app.factory_recipe_path = tmp_path / 'cell.json'
    return app


def click(app, label):
    b = next(b for b in app.active_workspace.buttons if b.label.startswith(label))
    assert b.enabled, label
    app.active_workspace.events.append(b.action)


@WINDOW
def test_the_tool_and_program_lessons_are_done_in_the_window(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_guide()
        elif n == 1:
            assert app.lesson_progress.current == 'drive', "the first lesson first"
            click(app, '2.  Move the gripper to the cube')
        elif n == 2:
            assert app.lesson_progress.current == 'tool'
            click(app, 'Start this lesson')
        elif n == 3:
            assert app.control_mode == 'Tool' and not app.building and app.field_id == 'pick_place'
            facts = app.lesson_facts()
            if 'tool' in app.lesson_progress.done:
                for key in list(app.tool_keys):
                    app.key(app.window, key, 0, glfw.RELEASE, 0)
                step['n'] += 1
                return
            if app.tool_motion.gliding is not None or facts.tool_off is None:
                return      # still being drawn back by the lesson's start
            # Like a user watching the tool: steer it towards the cube along each axis.
            f, l, u = app.tool_motion.frame()
            cube = app.data.xpos[app.model.body('objects/grasp_cube').id]
            off = cube - app.tool_motion.tool()[0]
            want = set()
            for axis, ahead, back in ((f, glfw.KEY_UP, glfw.KEY_DOWN), (l, glfw.KEY_LEFT, glfw.KEY_RIGHT),
                                      (u, glfw.KEY_PAGE_UP, glfw.KEY_PAGE_DOWN)):
                if off @ axis > .004: want.add(ahead)
                if off @ axis < -.004: want.add(back)
            for key in app.tool_keys - want:
                app.key(app.window, key, 0, glfw.RELEASE, 0)
            for key in want - app.tool_keys:
                app.key(app.window, key, 0, glfw.PRESS, 0)
            assert app.state.time < 30, 'the tool should be over the cube by now'
            return
        elif n == 4:
            assert 'tool' in app.lesson_progress.done and app.lesson_progress.current == 'drive'
            app.show_guide()
            click(app, '3.  Program the arm')
        elif n == 5:
            click(app, 'Start this lesson')
        elif n == 6:
            assert app.building and app.field_id == 'pick_place'
            click(app, 'Pick and place')
        elif n == 7:
            assert 'grasp' in [b.kind for b in app.program.blocks]
            click(app, 'Run')
        elif n == 8:
            if 'program' not in app.lesson_progress.done:
                assert app.runner.state == 'running' or app.runner.state == 'completed', app.runner.message
                return
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=150)
    assert step['n'] == 9


@WINDOW
def test_the_import_lesson_is_done_in_the_joint_lab(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}

    def in_the_joint_lab():
        real = app.active_workspace
        real_draw()
        n = step['n']
        if n == 2:
            assert real.app_mode == 'Real' and real.dialog['fields'][0][1].endswith('sample_arm.urdf')
            real.apply_form()
        elif n == 3:
            assert real.dialog is None and real.robot_asset == 'user:sample-arm'
            real.joint_example()
            real.start_program()
        elif n == 4:
            if 'import' not in app.lesson_progress.done:
                assert real.state.time < 20, ('a joint should have moved 5 degrees by now', real.lesson_facts())
                return
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    def exercise():
        nonlocal real_draw
        draw()
        n = step['n']
        if n == 0:
            app.show_guide()
            app.lesson_progress.choose('import')
        elif n == 1:
            button = next(b for b in app.buttons if b.label == 'Start this lesson')
            button.action()                  # the Real workspace draws from here on
            real = app.active_workspace
            real_draw = real.draw
            monkeypatch.setattr(real, 'draw', in_the_joint_lab)
        step['n'] += 1

    real_draw = None
    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=90)
    assert step['n'] == 5


@WINDOW
def test_the_drive_and_sweep_lessons_are_done_in_the_window(tmp_path, monkeypatch):
    import sys
    import glfw
    from little_world.inventory.sweep import to_json
    from little_world.programming.program import Block, Program
    from test_variation import made_up_sweep
    app = window(tmp_path)
    made = to_json(made_up_sweep())
    monkeypatch.setattr(app, 'vary_command', lambda field, design, out, name: [
        sys.executable, '-c', f'import pathlib; pathlib.Path({str(out)!r}).write_text({made!r})'])
    draw = app.draw
    step = {'n': 0}
    # Through the door (its centre 0.5 m to the left of the start line, the wall at 2 m) and
    # into the bay: what a user might hold the keys for, as a program a user might write.
    route = Program((Block('goto', value=.03, duration=40., point=(1.3, .5, 0.)),
                     Block('goto', value=.05, duration=40., point=(3.1, .5, 0.))))

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_guide()
        elif n == 1:
            click(app, 'Start this lesson')
        elif n == 2:
            assert app.field_id == 'doorway' and app.building
            app.program_edit(route)
            click(app, 'SIMULATE')
        elif n == 3:
            app.start_program()
        elif n == 4:
            if 'drive' not in app.lesson_progress.done:
                assert app.runner.state == 'running', app.runner.message
                return
            assert app.lesson_progress.current == 'tool'
            app.show_guide()
            click(app, '5.  Ask how sure')
        elif n == 5:
            click(app, 'Start this lesson')
        elif n == 6:
            assert app.field_id == 'sprint' and app.building
            click(app, 'SIMULATE')
        elif n == 7:
            app.key(app.window, glfw.KEY_W, 0, glfw.PRESS, 0)
        elif n == 8:
            if app.state.time < .5:
                return
            app.key(app.window, glfw.KEY_W, 0, glfw.RELEASE, 0)
            click(app, 'STOP / RETURN TO BUILD')
        elif n == 9:
            click(app, 'Repeat with variations')
        elif n == 10:
            if 'sweep' not in app.lesson_progress.done:
                return
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=150)
    assert step['n'] == 11
