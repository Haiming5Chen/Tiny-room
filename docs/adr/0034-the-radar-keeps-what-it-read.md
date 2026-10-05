# The radar keeps what it read: a collection in the repository, and a search over it

**Problem.** The radar's store is one SQLite file outside the repository (ADR 0021). The
first run, on 27 September, read 302 items and judged 23; the store went with the session
that wrote it, and what is left are two digests - `docs/RADAR.md` and the brief in
`docs/agents/FRONTIER.md` - naming 30 items. The weekly reading the owner chose (ADR 0026)
runs in a fresh session every Monday: on 5 October it read about sixty items, judged 51 by
name and wrote five proposals, into a project document outside the repository, where no
command could read it and the next week's run could learn what was already read only by
reading prose. Two agents now work in two checkouts and log to one file (the shared log);
both need the same memory of what was read, and nothing could answer "what have we read
about calibrating a camera?" short of reading every digest.

**Does an existing tool solve it? Can we wrap it?** A reference manager (Zotero) keeps
papers, but not this project's verdicts or the decisions they are filed under, and not in
the repository the agents share. Vector databases (FAISS, Chroma, sqlite-vec) and embedding
models (sentence-transformers) search by meaning, but need a model download and, mostly,
PyTorch, whose builds for the owner's Intel Mac stopped at 2.2; and at a few hundred entries
an exact cosine over every entry takes well under a millisecond, so an index structure buys
nothing. Latent semantic analysis (Deerwester et al., 1990) needs only numpy and text the
project already has. Wrapped: the radar's `Item`, its store and its lexical vectors.

**Unique contribution.**
- *The collection* (`radar/collection.py`): `docs/radar/collection.jsonl` holds every item
  filed under one of the project's topics or judged - its `Item` fields and what was made of
  it: first seen, the topics it was filed under, how much was read (`title`, `abstract`,
  `full`), the verdict, its note and date. One line an entry, sorted by id, empty fields left
  out, so a change is one line of a diff. Two agents adding the same paper merge line by line
  (`.gitattributes`: merge=union), and reading merges entries with one id: the longer
  summary, the larger attention, sources, topics and tags joined, the earliest sighting, the
  newest verdict. The repository is public: a journal's abstract is never kept, and a
  summary is arXiv's own (its metadata is CC0) or a few lines written while reading.
- *In and out of the store.* `collect` keeps what the store has filed or judged, and merges
  entries gathered by hand in the same shape (`--add found.jsonl`), filing them on the way
  in; `recall` reads the collection back into a store, verdicts included, so a fresh session
  - the weekly one - starts from what was judged before.
- *Search* (`radar/search.py`). `search WORDS` and `related TOPIC` (a decision as `topics`
  names it, or a proposal, `FR-016`) rank entries by the radar's own tf-idf cosine over stems
  and word pairs and say which words matched; `--verdict` keeps adopt, learn, watch, skip or
  not yet judged. `--latent SHARE` mixes in a latent cosine: the stems' tf-idf weights over
  the collection and the project's own paragraphs (its decision records, proposals, profile,
  roadmap and vision), cut to 64 directions by a truncated singular value decomposition
  (randomized, two power iterations, seeded); a hit found that way shows the words that
  brought it close. `search --check` measures the search on 20 questions whose answers were
  written down before the first search (`docs/radar/queries.jsonl`).
- *First contents.* 81 entries: the 30 the first run's digests name (18 judged) and the 51
  the weekly reading of 5 October judged; its five proposals are FR-017 to FR-021, and its
  evidence is a dated note under eight older ones.

**Blueprint and builder.** Untouched: the radar reads documents, never designs.

**Result.**

| 20 questions, 81 entries | an answer in the top three | mean reciprocal rank |
| --- | --- | --- |
| words alone (the default) | 17 | 0.794 |
| words and the latent cosine, half each | 18 | 0.823 |
| the latent cosine alone | 17 | 0.813 |

Those are the numbers with this record written. Measured first, before it and the new
proposals were part of the project's writing, the same mix found 16 (0.782), and varied
after that - 16 to 128 directions, the background widened to every document - it found
between 15 and 19, while words found 17 every time. The latent half moves with every
paragraph the project adds, by one or two questions in twenty either way: too little to
change what a search returns by default. So words rank, the latent cosine is asked for by
name, and `--check` repeats the measurement as the collection grows by fifty or sixty
entries a week. That the mechanism works where the writing supports it is held by a test:
'grip' finds a 'grasp' entry they share no word with, when the latent space has as many
directions as the writing has subjects - and loses it with one direction more, spent on
telling grip from grasp. Building the latent space over the collection and 264 paragraphs
takes 0.2 s; a search by words, under 10 ms.

Held by `tests/test_radar_collection.py` (11): the file round trip and the merge of two
sightings, refused lines named by number, no journal abstract and long summaries cut,
`collect` and `recall` through a store, entries gathered by hand merged and filed, the search
by words with its matched words and its verdict filter, the latent test above, the check, a
proposal or a topic as the question, the repository's collection sorted, public and written
as `dumps` writes it, and the 20 questions answerable, words putting an answer in the top
three for at least 15.

**Boundaries.** The collection is what agents read, not what was published; most entries
of the weekly reading were read by title only (`read: title`; 43 of 81), and a verdict is an
agent's reading of its source. The first run's 302 items are not recovered: only the 30 its
digests name. Latent semantic analysis is not an embedding model: it relates words only as
far as the project's writing pairs them, and here that did not beat the words. A trained
embedding model would relate words unasked (OPEN LW-012, the owner's decision); a static one
such as Model2Vec runs on numpy after a download of about 30 MB - not tried. MuJoCo changelog
entries taken from the digests carry ids written by hand (`mujoco:3.7.0#dcmotor`); a later
`fetch` files the same changes under the parser's numbered ids, as separate entries.
