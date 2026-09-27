# Frontier radar: what is new elsewhere, filed under what this project decided

**Problem.** The field this project stands in moves faster than one person reads. arXiv's
robotics category took 1,149 new papers in August 2026, against 750 a year before; open
robot models and repositories arrive weekly; and MuJoCo, the simulator every physical
result here rests on, has released eleven minor versions since the 3.3.7 this project
pins - among them a PID actuator, a DC-motor model, actuator delays, conveyor surfaces,
an integrator made for stiff servos and a system identification toolbox, each bearing on
a decision recorded here. Nothing connected the two: what reached the project was what its
builder happened to read.

**Does an existing tool solve it? Can we wrap it?** Personal paper filters exist and
work: arxiv-sanity-lite ranks by tf-idf with an SVM per tag trained on the reader's own
tags; zotero-arxiv-daily by embedding similarity to the reader's library; Scholar Inbox
by embeddings and a per-user classifier trained on thumbs up and down; gpt_paper_assistant
and ArxivDigest by asking a language model to score each abstract against a written list
of interests; Semantic Scholar recommends from positive and negative seed papers. They
answer "what would this reader like to read". None answers "which of this project's
decisions does this change", and none reads the changelog of the library a project is
built on. Their scoring can be borrowed - this is arxiv-sanity's tf-idf - but not their
question.

**Unique contribution.**
- *The decisions are the query.* Every decision record is a topic on its own: its title
  and its opening, the problem it solved. A short profile (docs/radar/profile.md) adds the
  words papers use for what a record says in its own words, the roadmap's next steps
  (`Next: ...`) and what the builder wants to learn (`Learn: ...`). As records are added,
  the radar's interests follow.
- *Filed with a reason.* Each item is scored against every topic - tf-idf over word stems
  and adjacent pairs, compared by cosine - and filed under its best, with the words that
  matched most and the runner-up when close. One shared phrase is not enough: an item
  needs two separate pieces of evidence, so "language models" alone does not put a protein
  paper under robot programming. Scores are explained word by word and are the same on
  every machine; a semantic embedding model can replace the vectors in one function.
- *The simulator's own changes.* MuJoCo's changelog is a source: one item per entry of
  every version newer than the pinned one, tagged by section and "breaking" when it sits
  under a Breaking API changes admonition, and filed under the decisions it touches.
- *What is loud but unasked.* Items with much attention elsewhere (upvotes, stars, likes)
  and no topic here are listed apart: a gap in the profile, or noise, for a person to say.
- *A triage, kept.* The digest ends in a list to judge - adopt (change the project), learn
  (study it), watch (look again later), skip - and verdicts are kept with the item, so the
  next digest shows what was already judged and a decision record can cite what it
  adopted.

**Sources and limits** (`python -m little_world.radar fetch`, standard library only):
arXiv's daily cs.RO listing (new submissions and cross-lists; empty at weekends),
Hugging Face's daily papers with their upvotes, its robotics and LeRobot models with their
likes, GitHub's search for MuJoCo repositories and new robotics ones with their stars,
releases of watched repositories, and MuJoCo's changelog. Requests are named, spaced
(arXiv asks for one every three seconds; GitHub's search allows ten a minute without a
token) and a GitHub token, if set, goes to GitHub only. A feed that fails is reported and
the rest go on. Items gathered by hand - or by an assistant with a browser - come in as
JSON lines (`ingest`), which is how the first run below was gathered.

**Blueprint and builder.** Untouched: the radar reads the documents, never the designs.

**Result** (docs/RADAR.md has the run and its triage). The first run, 27 September 2026:
302 items - a day of arXiv cs.RO and of Hugging Face's daily papers, trending robotics
models and repositories, nine notable releases of the year and MuJoCo's 198 changelog
entries since 3.3.7 - of which 48 were filed under a topic: 7 of 38 arXiv papers, 13 of the
198 changes (the PID and DC-motor actuators under the servo and motor records, conveyor
surfaces under the planned feeder, the system identification toolbox under calibration).
Judged: 6 adopt, 8 learn, 4 watch, 5 skip. Acting on the first adopt - the upgrade every
other one needs - the headless suite on MuJoCo 3.14.0 passed 565 of 568: three results
involving a cylinder wheel in contact moved, two of them partly or wholly through the
multiccd default the radar had filed as breaking, one through a change it missed.
tests/test_radar.py (13): every parser on invented documents in the feeds' shapes,
including the changelog's admonitions, commit roles and directives; stems; filing by
topic with the words that matched and refusing single-phrase matches; the profile's
headings; merging one paper from two feeds; the digest's sections and triage; fetching
with one feed failing; a token sent to GitHub only; and the command line end to end.

**Boundaries.** Lexical: 'grip' does not meet 'grasp' unless the profile says so. The
radar ranks and files; it does not read papers, and it never decides - a verdict is a
person's, or an assistant's that a person can overrule. The fetcher's parsers are tested
on documents shaped like the feeds, not against the live services, which change; the first
run's items were gathered through a browsing tool whose summaries are condensed, not
verbatim abstracts.
