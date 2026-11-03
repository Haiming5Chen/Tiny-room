"""Where runs fail: a stage profile for every sweep (FR-038).

A sweep reports how many set-ups met every goal, with its interval (ADR 0028), and - paired with
the same set-ups undisturbed - how many a disturbance broke and how many it mended (ADR 0036). Two
disturbances can cost the same and fail in different places, and a rate can stay put while pairs
flip both ways (RoboCasa-Shift, arXiv 2610.27861). The goals of a field are its stages, in the order
a run meets them - the Fetch's: reached the table, lifted the cube, set it in the bin - and a program
that gives up says at which of its blocks: looking, driving, moving the arm, checking the grasp.
Here, for a group of runs, how many got how far, and where those that did not stopped.
Standard library only.
"""
from collections import Counter

DONE = ('met', 'kept')

# What a program was doing at a block of each kind, said plainly.
DOING = {'goto': 'driving', 'drive': 'driving', 'look': 'looking', 'pose': 'moving the arm',
         'move': 'moving a joint', 'grasp': 'checking the grasp', 'action': 'working the jaws',
         'contact': 'waiting for a touch', 'if_contact': 'waiting for a touch',
         'distance': 'closing in', 'wait': 'waiting'}


HELD = ('kept', 'failed')    # a goal held all along - staying upright - or broken: not a stage


def staged(results):
    """The goals that mark how far a run got, in the field's order: the ones met at a moment
    ('met', 'missed', 'open'), not those held all along, such as staying upright."""
    return [r for r in results if r.status not in HELD]


def first_missed(run, by='label'):
    """The first of a run's goals, in the field's order, it did not meet: its label (or its id,
    `by='id'`), or None."""
    for r in run.results:
        if r.status not in DONE:
            return getattr(r, by)
    return None


def funnel(runs):
    """[(goal label, runs that met it and every goal before it)], in the field's order: how
    far the runs got. Runs that could not run are left out."""
    runs = [r for r in runs if not r.error and r.results]
    if not runs:
        return []
    labels = [r.label for r in staged(runs[0].results)]
    out = []
    for k, label in enumerate(labels):
        out.append((label, sum(1 for r in runs if all(x.status in DONE for x in staged(r.results)[:k + 1]))))
    return out


def stopped(runs):
    """[(what the program was doing, runs)] for the runs whose program gave up, most first:
    from the block it stopped at (`Run.stopped`)."""
    said = Counter(DOING.get(r.stopped[1], r.stopped[1]) for r in runs if getattr(r, 'stopped', ()))
    return sorted(said.items(), key=lambda kv: (-kv[1], kv[0]))


def missed_at(runs, by='label'):
    """[(the first goal missed, runs)] for the runs that missed one, most first."""
    said = Counter(first_missed(r, by) for r in runs if not r.error and r.results and first_missed(r) is not None)
    return sorted(said.items(), key=lambda kv: (-kv[1], kv[0]))


# What a program was doing, in a word, for a narrow panel.
BRIEF = {'driving': 'driving', 'looking': 'looking', 'moving the arm': 'reaching', 'moving a joint': 'reaching',
         'checking the grasp': 'grasping', 'working the jaws': 'grasping'}


def lines(runs):
    """At most two short lines on where a group's runs failed, for a panel: 'missed: lifted 3,
    reached 1' - each goal by its id - and 'gave up: looking 2, grasping 1'; none when every run
    met every goal."""
    missed = missed_at(runs, 'id')
    if not missed:
        return ()
    out = ['missed: ' + ', '.join(f'{goal} {n}' for goal, n in missed)]
    gave_up = Counter()
    for doing, n in stopped(runs):
        gave_up[BRIEF.get(doing, doing)] += n
    if gave_up:
        out.append('gave up: ' + ', '.join(f'{doing} {n}' for doing, n in sorted(gave_up.items(), key=lambda kv: (-kv[1], kv[0]))))
    return tuple(out)


def markdown(groups):
    """A sweep's stage profile as a table: per group of runs - (label, runs) - how many met each
    goal in turn, and where those that missed stopped."""
    groups = [(label, [r for r in runs if not r.error]) for label, runs in groups]
    groups = [(label, runs) for label, runs in groups if runs]
    if not groups:
        return []
    goals = [label for label, _ in funnel(groups[0][1])]
    lines = ['', 'Where the runs got to (FR-038): how many met each goal and every goal before it, and what '
             'the program was doing where it gave up.', '',
             '| Runs | ' + ' | '.join(goals) + ' | Gave up |',
             '| --- |' + ' --- |' * (len(goals) + 1)]
    for label, runs in groups:
        counts = dict(funnel(runs))
        gave_up = ', '.join(f'{doing} {n}' for doing, n in stopped(runs)) or '-'
        lines.append(f'| {label} ({len(runs)}) | ' + ' | '.join(str(counts.get(g, 0)) for g in goals) + f' | {gave_up} |')
    return lines
