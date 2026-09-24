"""Run the arm's saved keyboard actions from Python, without opening a window."""
from little_world.robots.arm_lab import arm_lab_blueprint
from little_world.scenes.workshop import workshop_scene
from little_world.core.entity import Entity
from little_world.core.world import World
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.control.mujoco_keyboard import MujocoKeyboardControl


def main():
    blueprint=arm_lab_blueprint()
    backend=MujocoBackend()
    with World(backend,workshop_scene(Entity('machine',blueprint))) as world:
        world.start()
        controller=MujocoKeyboardControl(backend,blueprint)
        def action(key,seconds):
            if key:
                controller.press(key)
            for _ in range(round(seconds/world.timestep)):
                world.step(controller.step_commands(world.timestep))
            if key:
                controller.release(key)
            height=backend.data.body('objects/grasp_cube').xpos[2]
            print(f'{key or "Hold":>4}: cube centre {height*100:.1f} cm above floor')
        action(None,.5)
        action('G',.9)   # Close both fingers.
        action(None,.2)
        action('R',.8)   # Raise shoulder; other joints hold their targets.
        action(None,.6)
        action('H',1.)   # Open fingers and release the cube.
        action(None,.8)


if __name__=='__main__':
    main()
