"""Run with Python for the drive window, or add --headless for batch simulation."""
import argparse
import math
from pathlib import Path
from little_world import Blueprint, Entity, World
from little_world.core.scene import Scene
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.robots.two_wheel import two_wheel_blueprint
from little_world.scenes.room import room_entity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seconds", type=float, help="simulation duration headless / viewer wall time")
    parser.add_argument("--left", type=float, default=.5, help="headless left motor torque, Nm")
    parser.add_argument("--right", type=float, default=.5, help="headless right motor torque, Nm")
    parser.add_argument("--save-blueprint", type=Path)
    parser.add_argument("--load-blueprint", type=Path)
    parser.add_argument("--camera", type=Path, help="headless RGB capture as binary PPM")
    args = parser.parse_args()
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error("--seconds must be finite and positive")
    bp = Blueprint.from_json(args.load_blueprint.read_text()) if args.load_blueprint else two_wheel_blueprint()
    if args.save_blueprint:
        args.save_blueprint.write_text(bp.to_json() + "\n")
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("robot", bp)))) as world:
        if args.headless:
            state = world.start()
            for _ in range(math.ceil((args.seconds or 2) / world.timestep)):
                state = world.step({"robot/left_motor": args.left, "robot/right_motor": args.right})
            print(f"time={state.time:.3f}s chassis={state.bodies['robot/chassis'].pose.position}")
            if args.camera:
                rgb = backend.capture("robot/camera")
                args.camera.write_bytes(f"P6\n{rgb.shape[1]} {rgb.shape[0]}\n255\n".encode() + rgb.tobytes())
                print(f"Camera written to {args.camera}")
        else:
            from little_world.ui.viewer import inspect
            while inspect(world, backend, left="robot/left_motor", right="robot/right_motor", seconds=args.seconds) == "reset":
                pass


if __name__ == "__main__":
    main()
