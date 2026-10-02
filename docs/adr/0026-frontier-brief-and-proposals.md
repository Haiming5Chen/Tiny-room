# Frontier brief and proposals: from what the field publishes to what the owner decides

**Problem.** The radar (ADR 0021) files what is new under the decisions it could change,
and a person judges each item: adopt, learn, watch or skip. Between a verdict and a change
nothing was written down. Of the 23 verdicts of 27 September, 14 were adopt or learn; five
days later two had led to decision records (the multiccd default to ADR 0022, LIBERO-plus to
ADR 0024) and the other twelve existed as one sentence each in the radar's store. Two kinds
of agent work on this project - Codex and Claude sessions - neither reads the other's
conversations, and the owner decides what they do: an idea from a paper had nowhere to wait
for that decision, and nothing said how it would be adapted to this app, how we would know
it worked or what it would cost. And the radar read no journals: preprints, Hugging Face,
GitHub and MuJoCo's changelog, but not what reaches print in Science Robotics, IEEE Robotics
and Automation Letters or IEEE Transactions on Robotics.

**Does an existing tool solve it? Can we wrap it?** The paper filters of ADR 0021 rank
what to read; none turns an item into a change to a particular project. Software projects
settle that step with numbered proposals - Python's PEPs, Rust's RFCs: a motivation, a
design, its drawbacks, and a status that only the deciders change. That format is borrowed
here, cut to six fields. Journal tables of contents are RSS (2.0 from IEEE Xplore, 1.0 in
RDF from Science), which the radar's XML parsing already reads.

**Unique contribution.**
- *One file both agents read.* `docs/agents/FRONTIER.md` holds the rules, the proposals
  and, at its end, the radar's brief. Codex reads `AGENTS.md` and Claude Code reads
  `CLAUDE.md`, which imports it; both point there. Agents meet in the repository, not in a
  conversation.
- *Proposals shaped for a decision.* `### FR-nnn · title` and six fields: Status, From (the
  items it rests on, linked, with their radar ids), Idea, In Little World (where it would
  go), How we would know (a measurement, with numbers) and Cost and needs (work,
  dependencies, hardware, MuJoCo version, the owner's time). Only the owner moves a
  proposal to accepted or declined; agents mark it doing and done, with the decision record.
  An agent that disagrees adds a dated note under another's proposal and never edits it.
- *The brief.* `python -m little_world.radar brief` writes, between two markers, what was
  filed in the last two weeks: judged items first, topic by topic, each with the proposals
  that cite it - by its radar id, matched whole (`3.7.0#1` is not `3.7.0#13`), or by its
  link unless other items share it (every MuJoCo changelog entry points at one page) - and
  then the items judged worth adopting or learning that no proposal cites yet: where
  thinking is wanted next. Everything outside the markers belongs to the agents. Feed text
  is made inert (no HTML), so no title can close the markers.
- *Journals.* Science Robotics, IEEE RA-L and IEEE T-RO join the feeds, spaced like arXiv;
  an article is keyed by its DOI (from its own element, its identifier or its address,
  without the query), markup in titles is dropped and the journal is the item's tag.
- *A weekly reading.* The owner chose a weekly run (2026-10-02, OPEN LW-012). A scheduled
  session searches the same sources with web search - from the cloud workspace the journal
  feeds refuse automated requests (IEEE Xplore answered 418, Science 403, on 2026-10-02) -
  and writes proposals in this format outside the repository; the next agent session
  copies them here under new numbers.

**Blueprint and builder.** Untouched: the brief reads documents and writes one.

**Result.** The first brief, 2 October 2026, from the radar's store of 27 September: 302
items read, 51 filed, 23 judged. Fourteen proposals were written against it: FR-001 done
(ADR 0024), FR-002 accepted by the owner (MuJoCo 3.10.0 on every machine), and twelve
waiting for the owner, one of them (FR-014, the PID actuator and moving surfaces) blocked
because MuJoCo publishes no Intel-Mac wheels after 3.10.0. Every adopt and learn verdict is
cited by at least one proposal, so the brief's waiting list is empty. Checks:
`tests/test_radar.py` (21, six new): both journal feed shapes, with DOIs from elements and
addresses, escaped and nested markup and an item without a link; the journals among the
sources, spaced; proposals read with their status and ending at the next section;
citations by whole id and by unshared link; the brief's order, its inert feed text and its
waiting list; writing only between the markers, the same twice; the command line end to
end. `tests/test_agent_docs.py` (6, two new): the frontier file's proposals have their six
fields in order and a known status, a done one names its decision record, the markers come
once and after the proposals; the status script lists the proposals that wait on the owner.

**Boundaries.** The brief files and links; it reads no papers. A proposal is an agent's
reading of a source, often of an abstract, and says "title only, not yet read" where that
is all there was. Whether the journal feeds answer the owner's Mac is not known (LW-011):
they refused this workspace. Web search varies from week to week and can miss an article a
feed would list. Nothing in a proposal is a result until a decision record measures it.
