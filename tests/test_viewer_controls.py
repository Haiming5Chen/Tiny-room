from little_world.ui.controls import DriveInput


def test_hold_release_and_opposed_keys():
    controls = DriveInput()
    controls.press('W')
    assert controls.targets() == (5., 5.)
    controls.press('D')
    assert controls.targets() == (7.5, 2.5)
    controls.release('W')
    assert controls.targets() == (2.5, -2.5)
    controls.clear()
    assert controls.targets() == (0., 0.)
    controls.press('W')
    controls.press('S')
    assert controls.targets() == (0., 0.)


def test_brake_blocks_held_keys_until_new_press():
    controls = DriveInput()
    controls.press('W')
    controls.clear()
    assert controls.targets() == (0., 0.)
    controls.release('W')
    controls.press('W')
    assert controls.targets() == (5., 5.)
