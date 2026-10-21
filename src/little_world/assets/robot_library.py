"""Your robots: the robot library, kept outside the repository (ADR 0044, FR-031).

The four Menagerie arms ship with Little World (`robot_models.MODELS`). Robots imported
from their own description files (`physics/importer.py`) live in the user's robot library,
one folder each, and are named in designs as `user:<name>` - a name, never a path. An entry
is never changed once written: importing again makes a new entry, so a saved design keeps
meaning the robot it was built with. Removing an entry leaves designs that name it unable to
load, and they say which robot is missing.

Each entry holds `model.xml` (the MuJoCo model, its meshes in `assets/`), `metadata.json`
(what the app needs to place and drive it, and the import's report), `SOURCE.json` (where it
came from: the file's name and the SHA-256 of everything copied) and `source/` (the
description file as it was given).

Standard library only.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

PREFIX = 'user:'
NAME = re.compile(r'^[a-z0-9][a-z0-9_-]{0,39}$')
ENVIRONMENT = 'LITTLE_WORLD_ROBOTS'


def root():
    """Where the library is: $LITTLE_WORLD_ROBOTS if set, else the platform's place for an
    application's own data."""
    if os.environ.get(ENVIRONMENT):
        return Path(os.environ[ENVIRONMENT]).expanduser()
    home = Path.home()
    if sys.platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'Little World' / 'robots'
    if os.name == 'nt':
        return Path(os.environ.get('APPDATA') or home) / 'Little World' / 'robots'
    return Path(os.environ.get('XDG_DATA_HOME') or home / '.local' / 'share') / 'little-world' / 'robots'


def is_user(asset):
    return isinstance(asset, str) and asset.startswith(PREFIX)


def valid(asset):
    """Whether `asset` is a well-formed library name (`user:` and a lower-case name)."""
    return is_user(asset) and bool(NAME.match(asset[len(PREFIX):]))


def name_of(asset):
    if not valid(asset):
        raise ValueError(f'{asset!r} is not a robot library name')
    return asset[len(PREFIX):]


def slug(text):
    """A library name made from any text: lower case, letters, digits, '-' and '_'."""
    s = re.sub(r'[^a-z0-9_-]+', '-', str(text).lower()).strip('-_')[:40].strip('-_')
    return s or 'robot'


def folder(asset):
    """The entry's folder; a ValueError naming the robot if the library has no such entry."""
    path = root() / name_of(asset)
    if not (path / 'metadata.json').is_file():
        raise ValueError(f"The robot '{name_of(asset)}' is not in your robot library: "
                         'import it again, or choose another robot')
    return path


def entries():
    """The library's robots, as `user:` names, sorted."""
    base = root()
    if not base.is_dir():
        return ()
    return tuple(PREFIX + p.name for p in sorted(base.iterdir())
                 if NAME.match(p.name) and (p / 'metadata.json').is_file())


def free_name(text):
    """A name for a new entry: `slug(text)`, or with -2, -3 ... if that is taken."""
    base, taken = slug(text), {e[len(PREFIX):] for e in entries()}
    if base not in taken and not (root() / base).exists():
        return base
    n = 2
    while f'{base[:36]}-{n}' in taken or (root() / f'{base[:36]}-{n}').exists():
        n += 1
    return f'{base[:36]}-{n}'


def metadata(asset):
    return json.loads((folder(asset) / 'metadata.json').read_text())


def remove(asset):
    """Delete an entry. Designs that name it no longer load."""
    shutil.rmtree(folder(asset))
    forget()


def forget():
    """Drop what was read from the library, after it changed."""
    from little_world.assets import robot_models
    robot_models.metadata.cache_clear()
