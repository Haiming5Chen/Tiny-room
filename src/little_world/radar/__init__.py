"""A frontier radar: what is new elsewhere, filed under what this project decided (ADR 0021).

Every week brings a few hundred new robotics papers, new open models and repositories,
and releases of the libraries the project stands on. The radar scores each arrival
against what the project has already decided and plans next - its decision records,
the roadmap, and a short profile of what its builder wants to learn - so the arrivals
become a short list, each item filed under the decision it could change, with the words
that matched and how much attention it has elsewhere.

Nothing here decides. A digest ends in a triage - adopt, learn, watch or skip - that the
builder (or an assistant reading the digest) fills in; verdicts are kept, so the next
digest shows what was already judged and a decision record can cite what it adopted.

Standard library only: urllib to fetch, SQLite to keep, and a lexical vector model
(tf-idf over word stems and word pairs, compared by cosine) to score. A semantic
embedding model can replace the vectors later; the lexical one explains every score in
the words it matched, needs no download, and gives the same answer on every machine.

    python -m little_world.radar fetch            # the feeds in fetch.SOURCES
    python -m little_world.radar ingest items.jsonl
    python -m little_world.radar digest --days 7 --out digest.md
    python -m little_world.radar rate arxiv:2609.01234 adopt "ADR 0022 uses its model"
"""
from .items import Item
from .profile import Topic, topics
from .score import Match, match

__all__ = ('Item', 'Topic', 'topics', 'Match', 'match')
