"""Interactive Little World workshop: build a Blueprint, simulate, and redesign."""
import argparse
import math
from pathlib import Path
from little_world.ui.workshop import Workshop


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--design',type=Path,default=Path('designs/my_machine.json'))
    parser.add_argument('--seconds',type=float,help='bounded window smoke run')
    parser.add_argument('--screenshot',type=Path,help='save one window capture as PPM')
    parser.add_argument('--classic',action='store_true',help='open the original simple robot in the room')
    parser.add_argument('--program',action='store_true',help='open the visual pickup program')
    parser.add_argument('--motor-study',action='store_true',help='open an arm with an estimated sourced shoulder motor')
    parser.add_argument('--cart-arm',action='store_true',help='open the mobile cart with a compact arm')
    parser.add_argument('--arm',action='store_true',help='open the keyboard arm and gripper lab')
    args=parser.parse_args()
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds<=0):
        parser.error('--seconds must be finite and positive')
    if args.cart_arm:
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        app=Workshop(args.design,mobile_manipulator_blueprint())
        app.editor.select('two_finger_gripper_1_root')
        app.control_panel=True
        app.library_open=False
        app.initial_camera=((.12,0,.22),1.25)
    elif args.arm or args.motor_study or args.program:
        from little_world.robots.arm_lab import arm_lab_blueprint
        app=Workshop(args.design,arm_lab_blueprint())
        app.control_panel=True
        app.library_open=False
        app.initial_camera=((.22,0,.22),1.15)
        if args.program:
            app.show_program();app.pickup_program()
        if args.motor_study:
            from little_world.assets.real_motors import PROFILES
            app.editor.select('robot_arm_1_upper_arm')
            app.editor.set_motor_profile(PROFILES['XH430-W350 / 12 V'],1.02)
            app.active_tab='Connect'
    elif args.classic:
        app=Workshop(args.design)
    else:
        from little_world.robots.mobile_platform import mobile_platform_blueprint
        app=Workshop(args.design,mobile_platform_blueprint())
        app.open_bench()
    app.run(args.seconds,args.screenshot)


if __name__=='__main__':
    main()
