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
from little_world.inventory.sweep import PROTOCOLS, from_json, headline, markdown, moved_most, spread

MUTED = (.49, .57, .63)
ACCENT = (.37, .83, .69)
WARN = (.96, .72, .38)
LIGHT = (.86, .90, .93)
JOBS = 2            # worker processes: most laptops have at least two cores to spare


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
        # Its own process group, so stopping it stops its worker processes too.
        process = subprocess.Popen(self.vary_command(record.field, design, out, name), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, start_new_session=os.name == 'posix')
        state = dict(field=record.field, run=record.number, blueprint=self.editor.blueprint, process=process,
                     done=0, total=len(plan()), out=out, result=None, error='', lines=[])

        def read():
            for line in process.stdout:
                state['lines'].append(line.rstrip())
                count = re.match(r'\s*(\d+)/(\d+) ', line)
                if count:
                    state['done'], state['total'] = int(count[1]), int(count[2])
        threading.Thread(target=read, daemon=True).start()
        self.varied = state
        self.status = f'Repeating run {record.number} with {state["total"]} variations in the background.'

    def stop_variations(self):
        process = self.varied['process'] if self.varied is not None else None
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL) if os.name == 'posix' else process.kill()
            except ProcessLookupError:
                pass
        self.varied = None

    def poll_variations(self):
        v = self.varied
        if v is None or v['result'] is not None or v['error'] or v['process'].poll() is None:
            return
        try:
            if v['process'].returncode != 0:
                raise ValueError(next((line for line in reversed(v['lines']) if line.strip()), 'the repeats stopped'))
            v['result'] = from_json(v['out'].read_text(encoding='utf-8'))
            self.status = f'Repeated run {v["run"]}: ' + headline(v['result'])[0].lower() + '.'
        except (OSError, ValueError, KeyError, TypeError) as error:
            v['error'] = str(error) or 'the repeats stopped'

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
            button(f'Repeat with variations ({len(plan())} runs)', 12, y, 264, self.start_variations, h=28)
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
        text(words, 16, y, 13, WARN if tone == 'warn' else ACCENT if tone == 'ok' else LIGHT, 256)
        y += 22
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
        most = moved_most(s)
        if most:
            text('moved it most:', 16, y + 2, 10, MUTED)
            y += 18
            for label, change in most:
                text(f'{label}: {change}', 16, y, 11, LIGHT, 256)
                y += 17
        skipped = sum(1 for r in s.runs if r.error)
        if skipped:
            text(f'{skipped} could not run', 16, y, 11, WARN, 256)
            y += 17
        button('Copy the full report', 12, y + 4, 264, self.copy_variations_report, h=26)
        return y + 38
