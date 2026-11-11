"""Where Little World keeps what a user makes, when it is not told a place.

A checkout run from its own folder writes `designs/` beside the code (examples/workshop.py);
an installed copy has no such folder, so the command line keeps designs in the platform's place
for an application's own data - where the robot library and the lessons' progress already are
(ADR 0044, 0046). Standard library only.
"""
import os
import sys
from pathlib import Path

ENVIRONMENT = 'LITTLE_WORLD_HOME'


def home():
    """$LITTLE_WORLD_HOME if set, else the platform's place for an application's own data."""
    if os.environ.get(ENVIRONMENT):
        return Path(os.environ[ENVIRONMENT]).expanduser()
    user = Path.home()
    if sys.platform == 'darwin':
        return user / 'Library' / 'Application Support' / 'Little World'
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA') or user) / 'Little World'
    return Path(os.environ.get('XDG_DATA_HOME') or user / '.local' / 'share') / 'little-world'


def design_path():
    """The design the window saves to and opens again: designs/my_machine.json under `home()`."""
    return home() / 'designs' / 'my_machine.json'
