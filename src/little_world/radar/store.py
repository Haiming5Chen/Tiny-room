"""Where the radar keeps what it has seen and what was made of it: one SQLite file.

An item seen again - a paper in arXiv's feed and then among Hugging Face's daily papers -
is merged: the longer summary, the larger attention, the sources joined, and the date it
was first seen kept, so each item turns up in one digest only. Verdicts are the triage:
'adopt' (change the project), 'learn' (study it), 'watch' (look again later), 'skip'.
"""
from dataclasses import astuple
from datetime import date
import json
from pathlib import Path
import sqlite3

from .items import Item

VERDICTS = ('adopt', 'learn', 'watch', 'skip')
DEFAULT = Path.home() / '.little_world' / 'radar.sqlite'

_SCHEMA = '''
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, summary TEXT, url TEXT,
    published TEXT, kind TEXT, attention REAL, tags TEXT, first_seen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS verdicts (
    id TEXT PRIMARY KEY, verdict TEXT NOT NULL, note TEXT, at TEXT NOT NULL);
'''


class Store:
    def __init__(self, path=DEFAULT):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(_SCHEMA)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def add(self, items, seen=None):
        """Keep items; returns how many were new."""
        seen = seen or date.today().isoformat()
        new = 0
        for item in items:
            row = self.db.execute('SELECT source, summary, attention, tags, first_seen FROM items WHERE id = ?',
                                  (item.id,)).fetchone()
            if row is None:
                values = list(astuple(item))
                values[-1] = json.dumps(list(item.tags))
                self.db.execute('INSERT INTO items (id, source, title, summary, url, published, kind, attention, '
                                'tags, first_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (*values, seen))
                new += 1
                continue
            sources = row[0].split('+')
            if item.source not in sources:
                sources.append(item.source)
            tags = list(dict.fromkeys([*json.loads(row[3] or '[]'), *item.tags]))
            summary = item.summary if len(item.summary) > len(row[1] or '') else row[1]
            self.db.execute('UPDATE items SET source = ?, summary = ?, attention = ?, tags = ? WHERE id = ?',
                            ('+'.join(sources), summary, max(row[2] or 0., item.attention), json.dumps(tags), item.id))
        self.db.commit()
        return new

    def items(self, since=''):
        """Items first seen on or after `since` ('YYYY-MM-DD'; '' for all)."""
        rows = self.db.execute('SELECT id, source, title, summary, url, published, kind, attention, tags '
                               'FROM items WHERE first_seen >= ? ORDER BY id', (since,)).fetchall()
        return [Item(*row[:8], tuple(json.loads(row[8] or '[]'))) for row in rows]

    def count(self):
        return self.db.execute('SELECT COUNT(*) FROM items').fetchone()[0]

    def rate(self, item_id, verdict, note='', when=None):
        if verdict not in VERDICTS:
            raise ValueError(f'verdict must be one of {VERDICTS}, not {verdict!r}')
        if self.db.execute('SELECT 1 FROM items WHERE id = ?', (item_id,)).fetchone() is None:
            raise KeyError(f'no item {item_id!r} in the radar')
        self.db.execute('INSERT OR REPLACE INTO verdicts (id, verdict, note, at) VALUES (?, ?, ?, ?)',
                        (item_id, verdict, note, when or date.today().isoformat()))
        self.db.commit()

    def verdicts(self):
        """{item id: (verdict, note, date)}."""
        return {row[0]: tuple(row[1:]) for row in self.db.execute('SELECT id, verdict, note, at FROM verdicts')}
