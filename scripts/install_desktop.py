"""Install the Tiny-room builder under a name distinct from the SyRoom app."""
from pathlib import Path
import plistlib
import shlex
import shutil
import subprocess

repo=Path(__file__).resolve().parents[1]
app=Path.home()/'Applications'/'Little World Builder.app'
identifier='org.littleworld.tinyroom.builder'
info=app/'Contents'/'Info.plist'
if app.exists():
    if not info.exists() or plistlib.loads(info.read_bytes()).get('CFBundleIdentifier')!=identifier:
        raise SystemExit('Existing app has a different identity; left it untouched: '+str(app))
executable=app/'Contents'/'MacOS'/'LittleWorldBuilder'
executable.parent.mkdir(parents=True,exist_ok=True)
resources=app/'Contents'/'Resources';resources.mkdir(exist_ok=True)
log=Path.home()/'Library'/'Logs'/'Little World Builder.log'
log.parent.mkdir(parents=True,exist_ok=True)
executable.write_text('#!/bin/sh\ncd '+shlex.quote(str(repo))+' || exit 1\nexec '+shlex.quote(str(repo/'.venv/bin/python'))+' '+shlex.quote(str(repo/'examples/launch_desktop.py'))+' "$@" >> '+shlex.quote(str(log))+' 2>&1\n')
executable.chmod(0o755)
plist=dict(CFBundleExecutable='LittleWorldBuilder',CFBundleIdentifier=identifier,CFBundleName='Little World Builder',CFBundleDisplayName='Little World Builder',CFBundlePackageType='APPL',CFBundleVersion='1',CFBundleShortVersionString='0.1',NSHighResolutionCapable=True)
info.write_bytes(plistlib.dumps(plist))
shortcut=Path.home()/'Desktop'/'Little World Builder.app'
if not shortcut.exists() and not shortcut.is_symlink():shortcut.symlink_to(app)
subprocess.run(['/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister','-f',str(app)],check=True)
print(app)
print('Desktop shortcut:',shortcut)
