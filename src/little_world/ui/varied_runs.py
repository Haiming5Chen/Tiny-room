"""Repeat a field run with variations, from its run report (ADR 0024).

A workshop mixin. The repeats run in another Python process (`little_world.inventory.sweep`),
so the window stays live; the report shows how far they have got and then the spread: the
range a static test's machine tipped over in, against the design's prediction, or each goal
over the runs, and the changes that moved the result most. The design is copied into the
other process; nothing here edits it.
"""
from pathlib import Path
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading

from little_world.fields.variation import plan
from little_world.inventory.sweep import (PROTOCOLS, assurance, from_json, headline, markdown, moved_most,
                                          ranges_for, spread, strip)

MUTED = (.49, .57, .63)
ACCENT = (.37, .83, .69)
WARN = (.96, .72, .38)
LIGHT = (.86, .90, .93)
JOBS = 2            # worker processes: most laptops have at least two cores to spare


def launch(command, total):
    """Start a sweep command in its own process group - so stopping it stops its workers too -
    and return its state: the process, how far it has got (its 'done/total' lines), the
    lines it printed. A thread reads its output; the window polls the state."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               start_new_session=os.name == 'posix')
    state = dict(process=process, done=0, total=total, result=None, error='', lines=[])

    def read():
        for line in process.stdout:
            state['lines'].append(line.rstrip())
            count = re.match(r'\s*(\d+)/(\d+) ', line)
            if count:
                state['done'], state['total'] = int(count[1]), int(count[2])
    threading.Thread(target=read, daemon=True).start()
    return state


def halt(state):
    """Stop a launched sweep and its workers, if it is still running."""
    process = state['process'] if state is not None else None
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL) if os.name == 'posix' else process.kill()
        except ProcessLookupError:
            pass


def finished(state, read, what):
    """Once a launched sweep's process has ended: its result read back with `read`, or why
    it stopped; True the first time it has a result."""
    if state is None or state['result'] is not None or state['error'] or state['process'].poll() is None:
        return False
    try:
        if state['process'].returncode != 0:
            raise ValueError(next((line for line in reversed(state['lines']) if line.strip()), f'the {what} stopped'))
        state['result'] = read(state['out'].read_text(encoding='utf-8'))
        return True
    except (OSError, ValueError, KeyError, TypeError) as error:
        state['error'] = str(error) or f'the {what} stopped'
        return False


class VariedRuns:
    def init_varied_runs(self):
        # The variations of one run: field, the design they were made from, the process and
        # its progress, then the sweep it wrote - or why it stopped.
        self.varied = None

    def variable(self, field):
        return field in PROTOCOLS

    def vary_command(self, field, design, out, name):
        return [sys.executable, '-m', 'little_world.inventory.sweep', field, '--design', str(design),
                '--json', str(out), '--name', name, '--jobs', str(JOBS)]

    def start_variations(self):
        record = self.run_report
        if record is None or not self.variable(record.field):
            raise ValueError('This field has no protocol a machine can follow alone')
        self.stop_variations()          # one set of repeats at a time
        folder = Path(tempfile.mkdtemp(prefix='little-world-varied-'))
        design = folder / 'design.json'
        design.write_text(self.editor.blueprint.to_json(), encoding='utf-8')
        out = folder / 'sweep.json'
        name = self.path.stem if getattr(self, 'path', None) else 'design'
        state = launch(self.vary_command(record.field, design, out, name), len(plan(ranges_for(record.field))))
        state.update(field=record.field, run=record.number, blueprint=self.editor.blueprint, out=out)
        self.varied = state
        self.status = f'Repeating run {record.number} with {state["total"]} variations in the background.'

    def stop_variations(self):
        halt(self.varied)
        self.varied = None

    def poll_variations(self):
        v = self.varied
        if finished(v, from_json, 'repeats'):
            self.status = f'Repeated run {v["run"]}: ' + headline(v['result'])[0].lower() + '.'

    def copy_variations_report(self):
        import glfw
        glfw.set_clipboard_string(None, markdown(self.varied['result']))
        self.status = 'The full report of the repeats is on the clipboard (Markdown).'

    def draw_variations(self, ui, button, text, section, y, wh):
        """Below a run report's actions: the button, then progress, then the spread."""
        record = self.run_report
        v = self.varied
        if not self.variable(record.field):
            return y
        if v is None or v['field'] != record.field or v['blueprint'] is not self.editor.blueprint:
            button(f'Repeat with variations ({len(plan(ranges_for(record.field)))} runs)', 12, y, 264,
                   self.start_variations, h=28)
            text('off its mark, turned, loaded, other floors', 16, y + 34, 10, MUTED, 256)
            return y + 54
        section(f'RUN {v["run"]} REPEATED  /  varied', y)
        y += 22
        if v['error']:
            text('Could not repeat: ' + v['error'], 16, y, 11, WARN, 256)
            button('Try again', 12, y + 18, 264, self.start_variations, h=26)
            return y + 52
        if v['result'] is None:
            done, total = v['done'], max(1, v['total'])
            text(f'{done} of {total} runs', 16, y, 12, LIGHT, 256)
            ui.rect(16, y + 20, 256, 6, (.14, .19, .23))
            ui.rect(16, y + 20, 256 * done / total, 6, ACCENT)
            button('Stop repeating', 12, y + 34, 264, self.stop_variations, h=26, tone='danger')
            return y + 70
        s = v['result']
        words, tone = headline(s)
        text(words, 16, y, 12, WARN if tone == 'warn' else ACCENT if tone == 'ok' else LIGHT, 256)
        y += 22
        sure = assurance(s)
        for line in sure:          # what the runs drawn at random show, and how sure (ADR 0028)
            text(line, 16, y - 4, 10, MUTED, 256)
            y += 13
        y += 5 if sure else 0
        ran = [r for r in s.runs if not r.error and r.tipped is not None and r.predicted is not None]
        if ran:
            errors = [r.tipped - r.predicted for r in ran]
            text(f'{min(errors):+.1f} to {max(errors):+.1f} deg from each prediction', 16, y, 11, MUTED, 256)
            y += 18
        else:
            for label, good, total, times, _ in spread(s):
                if y > wh - 160:
                    break
                span = '' if not times else f'  {times[0]:.1f}-{times[-1]:.1f} s' if times[-1] - times[0] >= .1 else f'  {times[0]:.1f} s'
                text(f'{good}/{total}', 16, y, 11, ACCENT if good == total else WARN)
                text(label + span, 52, y, 11, LIGHT, 220)
                y += 17
        y = self.draw_strip(ui, text, strip(s), y)
        most = moved_most(s)
        if most and y < wh - 150:
            text('moved it most:', 16, y + 2, 10, MUTED)
            y += 18
            for label, change in most:
                if y > wh - 110:
                    break
                # The first change it made; the full report has the rest.
                text(f'{label}: {change.split("; ")[0]}', 16, y, 11, LIGHT, 256)
                y += 17
        skipped = sum(1 for r in s.runs if r.error)
        if skipped:
            text(f'{skipped} could not run', 16, y, 11, WARN, 256)
            y += 17
        button('Copy the full report', 12, y + 4, 264, self.copy_variations_report, h=26)
        return y + 38

    def draw_strip(self, ui, text, line, y):
        """The runs as ticks on a line drawn just wide enough for them: the run as designed
        taller and light, the design's prediction as a warm mark."""
        if line is None:
            return y
        marks = [*line.values, *(v for v in (line.nominal, line.predicted) if v is not None)]
        lo, hi = min(marks), max(marks)
        step = 1. if line.unit == 'deg' else .5
        lo, hi = step * (lo // step) - step, step * (hi // step) + 2 * step
        x0, width = 16, 256

        def at(v):
            return x0 + width * (v - lo) / (hi - lo)
        ui.rect(x0, y + 10, width, 2, (.20, .26, .31))
        ui.rect(at(min(line.values)), y + 7, max(2., at(max(line.values)) - at(min(line.values))), 8, (.14, .32, .28))
        for v in line.values:
            ui.rect(at(v) - .5, y + 5, 1, 12, ACCENT)
        if line.nominal is not None:
            ui.rect(at(line.nominal) - 1, y + 1, 2, 20, LIGHT)
        if line.predicted is not None:
            ui.rect(at(line.predicted) - 3, y, 6, 4, WARN)
        unit = ' deg' if line.unit == 'deg' else ' s'
        text(f'{lo:g}', x0, y + 22, 10, MUTED)
        end = f'{hi:g}{unit}'
        text(end, x0 + width - ui.width(end, 10), y + 22, 10, MUTED)
        # A key in the marks' own colours: each run, the run as designed, the prediction.
        key = [(line.label, ACCENT), ('as designed', LIGHT)] + ([('predicted', WARN)] if line.predicted is not None else [])
        gap = 8
        x = x0 + (width - sum(ui.width(w, 10) for w, _ in key) - gap * (len(key) - 1)) / 2
        for words, colour in key:
            text(words, x, y + 22, 10, colour)
            x += ui.width(words, 10) + gap
        return y + 40
