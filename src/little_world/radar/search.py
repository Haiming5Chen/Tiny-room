"""Searching the collection by meaning as well as by words (ADR 0034).

Every entry is two vectors. The lexical one is the radar's own (score.py): tf-idf over word
stems and adjacent pairs, compared by cosine. It explains a hit by the words that matched,
and it misses a paper that says 'actuator' when the question says 'motor'. The latent one
closes some of those gaps: the stems' tf-idf weights over the collection and the project's
own writing - its decision records, proposals, profile and roadmap, a paragraph each - cut
down by a truncated singular value decomposition to the directions that carry most of it.
That is latent semantic analysis (Deerwester et al., 1990): stems that keep the same company
across those paragraphs land near each other, so a question finds an entry it shares no word
with, and the stems that brought it close are shown with it.

Measured on 20 questions written down before the first search (docs/radar/queries.jsonl,
81 entries; ADR 0034): words alone put an answer in the top three for 17, every time; the
latent half, mixed in equally, for 15 to 19 as the number of directions and the project's
writing changed. Too little to change what a search returns by default, so a search ranks
by words unless asked (`--latent`), and `search --check` repeats the measurement as the
collection grows. Built from the files when asked - well under a second - and searched
exhaustively: at this size an exact cosine over every entry costs less than an index would.
numpy only; no model to download; the same ranking on every machine, up to rounding.
"""
from collections import Counter
from dataclasses import dataclass
from math import log
from pathlib import Path
import re

import numpy as np

from .brief import BEGIN, proposals
from .profile import project_root, topics
from .score import _concepts, vectorise, words

DIMENSIONS = 64         # latent directions kept
LATENT = .5             # the latent cosine's share of a hit's score when it is asked for
PARAGRAPH = 12          # meaningful words a paragraph of the project's writing needs to count


@dataclass(frozen=True)
class Hit:
    entry: object       # collection.Entry
    score: float        # lexical, or (1 - share) * lexical + share * latent
    lexical: float      # cosine of the tf-idf vectors
    latent: float       # cosine in the latent space, 0 if negative or not asked for
    words: tuple        # the words both share, heaviest first
    near: tuple         # the entry's words that brought it closest in the latent space


def paragraphs(text):
    """A document's paragraphs with enough words to say something; code blocks left out."""
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    return [p for p in re.split(r'\n\s*\n', text) if len(words(p)) >= PARAGRAPH]


def background(root=None):
    """The project's own writing, a paragraph at a time: what teaches the latent space which
    words go together here. The radar's generated section of the frontier file is left out:
    it is made of the items themselves."""
    root = project_root(root)
    docs = Path(root) / 'docs'
    files = [*sorted((docs / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')), docs / 'radar' / 'profile.md',
             docs / 'ROADMAP.md', docs / 'VISION.md']
    out = []
    for path in files:
        if path.exists():
            out += paragraphs(path.read_text(encoding='utf-8'))
    frontier = docs / 'agents' / 'FRONTIER.md'
    if frontier.exists():
        out += paragraphs(frontier.read_text(encoding='utf-8').split(BEGIN)[0])
    return out


def _svd(matrix, k, seed):
    """The top k right singular vectors and values: a randomized range finder with two
    power iterations (Halko, Martinsson and Tropp, 2011), exact for the small sizes here."""
    rng = np.random.default_rng(seed)
    width = min(k + 16, min(matrix.shape))
    q = np.linalg.qr(matrix @ rng.standard_normal((matrix.shape[1], width)))[0]
    for _ in range(2):
        q = np.linalg.qr(matrix.T @ q)[0]
        q = np.linalg.qr(matrix @ q)[0]
    _, values, right = np.linalg.svd(q.T @ matrix, full_matrices=False)
    return values[:k], right[:k]


class Index:
    """The collection's entries as vectors, ready to be asked."""

    def __init__(self, entries, background=(), dimensions=DIMENSIONS, seed=0):
        self.entries = list(entries)
        self.texts = [e.text for e in self.entries]
        self._latent_inputs = (list(background), dimensions, seed)
        self.basis = None

    def _build(self):
        """The latent space, made the first time it is asked for."""
        background, dimensions, seed = self._latent_inputs
        corpus = self.texts + background
        counts = [Counter(s for s, _ in words(t)) for t in corpus]
        frequency = Counter(s for c in counts for s in c)
        n = len(corpus)
        vocabulary = sorted(s for s, d in frequency.items() if d >= 2)     # a stem seen once relates nothing
        self.column = {s: k for k, s in enumerate(vocabulary)}
        self.vocabulary = vocabulary
        self.idf = np.array([log((1 + n) / (1 + frequency[s])) + 1. for s in vocabulary])
        self.shown = {}
        for text in corpus:
            for s, word in words(text):
                self.shown.setdefault(s, word)
        matrix = np.array([self._weights(c) for c in counts]) if counts and vocabulary else np.zeros((n, 0))
        k = min(dimensions, min(matrix.shape) - 1) if matrix.size else 0
        if k > 0:
            self.values, self.basis = _svd(matrix, k, seed)
        else:
            self.values, self.basis = np.zeros(0), np.zeros((0, len(vocabulary)))
        self.weights = matrix[:len(self.entries)]
        self.latent = self._unit(self.weights @ self.basis.T)

    def _weights(self, counts):
        """A text's stems as a unit tf-idf row over the vocabulary (sublinear term frequency)."""
        row = np.zeros(len(self.vocabulary))
        for s, c in counts.items():
            k = self.column.get(s)
            if k is not None:
                row[k] = (1. + log(c)) * self.idf[k]
        norm = np.linalg.norm(row)
        return row / norm if norm else row

    @staticmethod
    def _unit(rows):
        norms = np.linalg.norm(rows, axis=-1, keepdims=True)
        return np.divide(rows, norms, out=np.zeros_like(rows), where=norms > 0)

    def ask(self, question, n=10, verdicts=None, least=.05, shown=4, latent=0.):
        """The entries closest to `question`, best first: at most `n`, scoring at least
        `least`, with one of `verdicts` ('' for not yet judged) when that is given. `latent`
        is the latent cosine's share of the score (0: words alone)."""
        if not self.entries:
            return []
        lexical = vectorise(self.texts + [question])
        asked, _ = lexical[-1]
        share = float(latent)
        if share > 0. and self.basis is None:
            self._build()
        if share > 0. and self.basis.size:
            row = self._weights(Counter(s for s, _ in words(question)))
            point = self._unit(row @ self.basis.T)
            closeness = np.clip(self.latent @ point, 0., 1.)
            toward = point @ self.basis
        else:
            share, closeness, toward = 0., np.zeros(len(self.entries)), None
        hits = []
        for k, e in enumerate(self.entries):
            if verdicts is not None and e.verdict not in verdicts:
                continue
            vector, surface = lexical[k]
            cosine = sum(w * asked.get(f, 0.) for f, w in vector.items())
            score = (1. - share) * cosine + share * float(closeness[k])
            if score < least:
                continue
            shared = _concepts(vector, asked)
            near = ()
            if toward is not None and closeness[k] > 0.:
                pull = self.weights[k] * toward
                said = {stem for f in shared for stem in f.split()}
                near = tuple(self.shown[self.vocabulary[j]] for j in np.argsort(-pull)[:shown + len(said)]
                             if pull[j] > 0. and self.vocabulary[j] not in said)[:shown]
            hits.append(Hit(e, round(score, 4), round(cosine, 4), round(float(closeness[k]), 4),
                            tuple(surface[f] for f in shared[:shown]), near))
        hits.sort(key=lambda h: (-h.score, h.entry.id))
        return hits[:n]


def about(subject, root=None):
    """The words a topic or a proposal is about: 'ADR 0032', 'Next: grasping from a camera'
    (as `python -m little_world.radar topics` names them) or 'FR-016'."""
    root = project_root(root)
    if re.fullmatch(r'FR-\d{3}', subject):
        path = Path(root) / 'docs' / 'agents' / 'FRONTIER.md'
        for pid, title, _, body in proposals(path.read_text(encoding='utf-8') if path.exists() else ''):
            if pid == subject:
                return f'{title} {title} {body}'
        raise KeyError(f'no proposal {subject} in {path}')
    for t in topics(root):
        if t.id == subject:
            return t.text
    raise KeyError(f'no topic {subject!r}: see python -m little_world.radar topics')


def check(index, questions, shares=(0., LATENT, 1.)):
    """How well the index answers questions with known answers: for each share of the
    latent cosine, how many questions have an expected entry in the top three, the mean
    reciprocal rank of the first expected entry, and each question's rank (None: absent)."""
    out = []
    for share in shares:
        ranks = []
        for q in questions:
            found = [h.entry.id for h in index.ask(q['question'], n=len(index.entries), least=-1., latent=share)]
            ranks.append(min((found.index(e) + 1 for e in q['expect'] if e in found), default=None))
        top = sum(1 for r in ranks if r is not None and r <= 3)
        out.append((share, top, round(sum(1. / r for r in ranks if r) / max(len(ranks), 1), 3), ranks))
    return out
