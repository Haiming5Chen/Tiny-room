# The research collection's search mixes words and meaning by default

**Problem.** OPEN LW-027. The research collection (ADR 0034) is searched before anything is read
again, and `search --check` measures it on 20 questions written down with their answers before the
first search. Words alone put an answer in the top three for 17 of them at 81 entries, 16 at 134, 15
at 177 - the test's floor - and, with the weekly reading of 2 November's 55 sources, 14 at 238 entries,
the mean reciprocal rank 0.60 where it was 0.79. New entries share the questions' common words without
answering them; the questions that lost their answers ask in other words than the answers use: "how far
can a mobile arm lean before it falls over" for a tip-over stability criterion, where "lean" now finds
the Lean Lexicon's takt time.

**Does an existing simulator solve it? Can we wrap it?** Not a simulator's question. Reweighting words
does not reach answers that share none: Okapi BM25 over the same stems and pairs (k1 from 0.9
to 2.0, b from 0.5 to 0.9) put an answer in the top three for 14 to 15 of
the 20, its mean reciprocal rank 0.60 to 0.66. The collection already has what does: ADR 0034's latent
space - latent semantic analysis of the entries and the project's own writing - which at 81 entries
did no better than words, and was left for when asked.

**Unique contribution.** The command line's `search` and `related` mix words and meaning equally by
default (`--latent` 0.5, ADR 0034's own share and 64 directions: nothing tuned to these questions);
`--latent 0` is words alone. `search --check` and the test measure the default.

**Blueprint and builder.** Untouched.

**Result.** The 20 questions, the top three and the mean reciprocal rank:

| entries | words alone | words and meaning, equally | meaning alone |
| --- | --- | --- | --- |
| 81 (ADR 0034) | 17 | 15 to 19 | |
| 183 (27 October) | 15, 0.69 | 17, 0.76 | 16, 0.74 |
| 238 (2 November) | 14, 0.60 | 16, 0.69 | 15, 0.63 |

With the reading of 2 November's 55 sources the collection holds 238 entries. Held by
`tests/test_radar_collection.py`: the default search answers at least 15 of the 20, its mean
reciprocal rank at least 0.65. Suites on MuJoCo 3.10.0: 1122 passed with a display, 1063 headless.

**Boundaries.** Twenty questions are few: one answer more or less moves the count by 5 points. The mix
also loses ground as the collection grows (17 to 16 here); `search --check` says when. The latent
space is rebuilt from the files at each search - well under a second at this size.
