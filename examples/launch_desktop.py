"""Desktop entry point: restore the saved design, otherwise open the pickup lab."""
import argparse
from pathlib import Path
from little_world.ui.workshop import Workshop
from little_world.core.blueprint import Blueprint
from little_world.programming.program import Program
from little_world.robots.arm_lab import arm_lab_blueprint


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seconds',type=float)
    parser.add_argument('--inventory',action='store_true')
    parser.add_argument('--mode',choices=('Real','Anime'),default='Real')
    args=parser.parse_args()
    path=Path(__file__).resolve().parents[1]/'designs'/'my_machine.json'
    saved=path.exists()
    app=Workshop(path,Blueprint.from_json(path.read_text()) if saved else arm_lab_blueprint())
    app.library_open=False
    app.initial_camera=((.2,0,.2),1.5)
    app.show_program()
    if app.program_path.exists():
        app.program=Program.from_json(app.program_path.read_text())
    elif not saved:
        app.pickup_program()
    app.start_mode='Anime' if args.inventory else args.mode
    if args.inventory:app.show_inventory()
    print('Opening Little World',flush=True)
    app.run(args.seconds)
    print('Little World closed normally',flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception:
        import traceback,subprocess
        traceback.print_exc()
        subprocess.run(['/usr/bin/osascript','-e','display alert "Little World could not open" message "Details are in Library/Logs/Little World.log. Your saved design has not been changed."'],check=False)
        raise SystemExit(1)
