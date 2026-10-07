"""How well an item matches a topic: tf-idf vectors over word stems and adjacent word
pairs, compared by cosine, with the words that matched most as the reason.

The vectors are lexical. 'friction' meets 'frictional' and 'slip' meets 'slipping'
through a small suffix stemmer, but 'grip' does not meet 'grasp': the profile's added
words close such gaps. A semantic embedding model would close them unasked, at the cost
of a model download and of scores no longer explained word by word; `match` takes the
vectors from `vectorise`, which is the one place to swap.
"""
from collections import Counter
from dataclasses import dataclass
from math import log, sqrt
import re

LEAST = .08             # cosine: below this an item matches no topic
CHANGE = .75            # a change to the simulator itself needs this share of LEAST: it is
                        # about the engine every result here runs on, and says it in few words
CLOSE = .8              # a runner-up topic scoring this share of the best is named too

STOP = frozenset('''
a about above across after again against all almost along also although among an and another any are
around as at be because been before being below between both but by can cannot could do does done
down due during each either else enough even ever every few for from further get gets given has have
having here how however i if in into is it its itself just less like made make makes many may might
more most much must near need needs neither new no nor not now of off often on once one only onto
or other others otherwise our out over own per rather same should show shown shows since so some such
than that the their them then there these they this those though through thus to too toward towards
two under until up upon us use used uses using very via was we well were what when where whether
which while who whom whose why will with within without would yet you your
paper propose proposed proposes present presents presented approach approaches method methods novel
result results demonstrate demonstrates demonstrated based work works et al e g i general improve improved
improves improvement improvements significant significantly various several better see details
'''.split())

SUFFIXES = (('ies', 'y'), ('izations', ''), ('ization', ''), ('ations', ''), ('ation', ''), ('ators', ''),
            ('ator', ''), ('ating', ''), ('ities', ''), ('ity', ''), ('izing', ''), ('ized', ''), ('izes', ''),
            ('ize', ''), ('ings', ''), ('ing', ''), ('ated', ''), ('ates', ''), ('ate', ''), ('ics', ''),
            ('ic', ''), ('al', ''), ('ed', ''), ('es', ''), ('s', ''))
_WORD = re.compile(r"[a-z][a-z0-9]*(?:[-'][a-z0-9]+)*")


def stem(word):
    """A word's stem by one suffix rule: 'manipulation', 'manipulators' -> 'manipul';
    'slipping' -> 'slip'; 'policies' -> 'policy'. Short words are left whole."""
    if word.endswith('ss'):
        return word
    for suffix, keep in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            root = word[:len(word) - len(suffix)] + keep
            if suffix in ('ing', 'ed', 'ings') and len(root) > 4 and root[-1] == root[-2] and root[-1] not in 'lsz':
                root = root[:-1]
            return root
    return word


def words(text):
    """[(stem, word)] of a text's meaningful words, in order."""
    out = []
    for raw in _WORD.findall((text or '').lower()):
        for word in raw.replace("'", '').split('-'):
            if len(word) > 1 and word not in STOP and not word.isdigit():
                out.append((stem(word), word))
    return out


def features(text):
    """(counts of stems and of adjacent stem pairs, the first word seen for each)."""
    found = words(text)
    counts, shown = Counter(), {}
    for (a, word_a), (b, word_b) in zip(found, found[1:]):
        if a != b:
            counts[f'{a} {b}'] += 1
            shown.setdefault(f'{a} {b}', f'{word_a} {word_b}')
    for s, word in found:
        counts[s] += 1
        shown.setdefault(s, word)
    return counts, shown


def vectorise(texts):
    """Unit tf-idf vectors {feature: weight}, the idf taken over these texts together, and
    each text's shown words. Term frequency is sublinear: a word said ten times is not ten
    times the evidence."""
    parsed = [features(t) for t in texts]
    frequency = Counter(f for counts, _ in parsed for f in counts)
    n = len(texts)
    out = []
    for counts, shown in parsed:
        vector = {f: (1. + log(c)) * (log((1 + n) / (1 + frequency[f])) + 1.) for f, c in counts.items()}
        norm = sqrt(sum(w * w for w in vector.values())) or 1.
        out.append(({f: w / norm for f, w in vector.items()}, shown))
    return out


@dataclass(frozen=True)
class Match:
    item: object
    topic: object       # the best topic, or None below LEAST
    score: float        # cosine with it, 0..1
    words: tuple        # the matched words that weighed most
    second: object = None   # a runner-up topic within CLOSE of the best


def _concepts(vector, topic_vector):
    """The features two vectors share, heaviest first, a word pair standing for its words:
    'language model' is one piece of evidence, not three - whichever of the three weighs
    most, since the weights move whenever a document joins the texts."""
    weights = sorted(((w * topic_vector[f], f) for f, w in vector.items() if f in topic_vector), reverse=True)
    paired = {word for _, f in weights if ' ' in f for word in f.split()}
    return [f for _, f in weights if ' ' in f or f not in paired]


def match(items, topics, least=LEAST, shown=4, evidence=2):
    """Every item's best topic, best first: the highest cosine among topics it shares at
    least `evidence` separate words or word pairs with. One shared phrase is not enough -
    'language models' alone does not make a protein paper about robot programming."""
    items, topics = list(items), list(topics)
    vectors = vectorise([t.text for t in topics] + [f'{i.title} {i.title} {i.summary}' for i in items])
    index = {}
    for k, (vector, _) in enumerate(vectors[:len(topics)]):
        for f, w in vector.items():
            index.setdefault(f, []).append((k, w))
    out = []
    for item, (vector, surface) in zip(items, vectors[len(topics):]):
        totals = Counter()
        for f, w in vector.items():
            for k, tw in index.get(f, ()):
                totals[k] += w * tw
        bar = least * (CHANGE if getattr(item, 'kind', '') == 'change' else 1.)
        found = []
        for k, score in totals.most_common():
            if score < bar or len(found) == 2:
                break
            concepts = _concepts(vector, vectors[k][0])
            if len(concepts) >= evidence:
                found.append((k, score, concepts))
        if not found:
            out.append(Match(item, None, round(totals.most_common(1)[0][1], 4) if totals else 0., ()))
            continue
        best, score, concepts = found[0]
        runner = topics[found[1][0]] if len(found) > 1 and found[1][1] >= CLOSE * score else None
        out.append(Match(item, topics[best], round(score, 4), tuple(surface[f] for f in concepts[:shown]), runner))
    out.sort(key=lambda m: (m.topic is None, -m.score))
    return out
