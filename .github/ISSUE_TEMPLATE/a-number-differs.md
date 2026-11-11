---
name: A number differs on my machine
about: little-world evidence printed DIFFERS, or a test fails here that passes in the workflows
title: "differs: "
labels: evidence
---

**What differs** (the lines `little-world evidence` printed, or the failing test's name):

**Where** (the first two lines `little-world evidence` prints - "Here: ..."):

**The file** `little-world evidence --json mine.json` wrote: attach `mine.json`.

A different MuJoCo release than 3.10.0 is expected to move results (`little-world doctor` says
which you have); another operating system or processor may move times a little and should not
flip a goal. Either way it is worth knowing: docs/EVALUATION.md, "One machine, one release".
