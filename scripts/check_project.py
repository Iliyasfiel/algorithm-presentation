"""Portable project checks. No third-party Python or npm packages required.

Run from any directory: python scripts/check_project.py [--build]
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slides = []
        self.codes = []
        self.scripts = []
        self.external = []
        self.code = None
        self.script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and 'slide' in attrs.get('class', '').split():
            self.slides.append(attrs)
        if tag == 'code' and attrs.get('class') == 'language-python':
            self.code = []
        if tag == 'script':
            self.script = []
            if attrs.get('src'):
                self.external.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.external.append(attrs.get('href'))

    def handle_endtag(self, tag):
        if tag == 'code' and self.code is not None:
            self.codes.append(''.join(self.code))
            self.code = None
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script))
            self.script = None

    def handle_data(self, data):
        if self.code is not None:
            self.code.append(data)
        if self.script is not None:
            self.script.append(data)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args, *, source=None):
    result = subprocess.run(args, cwd=ROOT, input=source, encoding='utf-8',
                            errors='replace', capture_output=True)
    if result.returncode:
        raise RuntimeError(f'Command failed: {" ".join(map(str, args))}\n'
                           f'{result.stdout}{result.stderr}')
    return result.stdout


def check_deck(node):
    html = (ROOT/'ppt/index.html').read_text(encoding='utf-8')
    parsed = DeckParser()
    parsed.feed(html)
    require(len(parsed.slides) == 18, 'Expected 18 PPT slides.')
    ids = [slide.get('data-slide-id') for slide in parsed.slides]
    require(all(ids) and len(set(ids)) == 18, 'Slide IDs must be unique and nonempty.')
    require(all('light' in slide['class'].split() and
                'dark' not in slide['class'].split() for slide in parsed.slides),
            'All slides must use the white/light theme.')
    require(not parsed.external, f'External runtime assets: {parsed.external}')
    require(len(parsed.codes) == 4, 'Expected build + report/count/nearest code blocks.')
    for code in parsed.codes:
        compile(code, 'PPT Python snippet', 'exec')
    teaching = (ROOT/'demo/teaching.py').read_text(encoding='utf-8')
    for name, code in zip(('report', 'count', 'nearest'), parsed.codes[1:]):
        snippet = re.search(r'# PPT:'+name+r':start\n([\s\S]*?)\n# PPT:'+name+r':end', teaching)
        require(snippet and snippet.group(1) == code, f'Stale teaching code: {name}')
    require('tok-keyword' in html, 'Python syntax highlighting is missing.')
    for source in parsed.scripts:
        run([node, '--check', '-'], source=source)
    for filename in ('ppt/content.js', 'ppt/viz.js'):
        run([node, '--check', filename])

    notes_match = re.search(r'const SPEAKER_NOTES = (\[[\s\S]*?\]);\s*window.__SPEAKER_NOTES__', html)
    require(notes_match is not None, 'Speaker notes not found.')
    notes = json.loads(notes_match.group(1))
    require([n['id'] for n in notes] == ids, 'Speaker note IDs do not match slides.')
    require(all(n.get('talk') and n.get('purpose') and n.get('transition') for n in notes),
            'Incomplete speaker notes.')
    plan = json.loads((ROOT/'ppt/slide-plan.json').read_text(encoding='utf-8'))
    require([n['id'] for n in plan] == ids, 'Slide plan does not match HTML.')
    require([n['title'] for n in plan] == [n['title'] for n in notes],
            'Slide titles differ between notes and plan.')
    require(all(abs(n['minutes']*60-p['duration']) < .01 for n, p in zip(notes, plan)),
            'Speaker timing differs from plan.')
    sections = re.findall(r'<section class="slide[\s\S]*?</section>', html)
    require("data-demo='insertion'" in sections[12] and
            "data-demo='dynamic'" not in sections[12], 'Slide 13 must show plain insertion only.')
    require("data-demo='dynamic'" in sections[13], 'Slide 14 must contain rebuilding demo.')

    for path, pattern in [
        ('docs/kdtree-report.md', r'^## (\d+)｜'),
        ('docs/kdtree-speaker-script.md', r'^## 第 (\d+) 页｜'),
    ]:
        text = (ROOT/path).read_text(encoding='utf-8')
        require([int(n) for n in re.findall(pattern, text, re.M)] == list(range(1, 19)),
                f'Expected 18 sequential page chapters in {path}.')
    script_text = (ROOT/'docs/kdtree-speaker-script.md').read_text(encoding='utf-8')
    titles = re.findall(r'^## 第 \d+ 页｜(.+)$', script_text, re.M)
    require(titles == [p['title'] for p in plan], 'Spoken script titles differ from PPT.')
    print(f'[PASS] HTML: 18 white slides, 4 Python code blocks, {len(parsed.scripts)} valid inline scripts; notes and docs aligned.')


def check_data():
    path = ROOT/'demo/output'
    raw = (path/'data.json').read_text(encoding='utf-8')
    data = json.loads(raw)
    wrapped = (path/'data.js').read_text(encoding='utf-8')
    match = re.fullmatch(r'window\.KD_DATA\s*=\s*([\s\S]*);\s*', wrapped)
    require(match and json.loads(match.group(1)) == data, 'data.js differs from data.json.')
    require(wrapped.strip() in (ROOT/'ppt/index.html').read_text(encoding='utf-8'),
            'PPT embeds stale data; run python ppt/build_deck.py.')
    require(data['range']['result'] == ['B', 'C', 'F', 'H'], 'Fixed range result differs.')
    require(data['nearest']['result'] == 'B' and data['nearest']['distanceSquared'] == 3,
            'Fixed nearest result differs.')
    require(not data['benchmarks']['metadata']['quick_mode'],
            'Quick data is active. Run python demo/generate.py, then rebuild PPT.')
    for row in data['benchmarks']['bySize'] + data['benchmarks']['byDimension']:
        require(all(row[k] for k in ('range_results_match_brute', 'count_results_match_brute',
                                     'nearest_results_match_brute', 'tree_metadata_valid')),
                'Benchmark correctness validation failed.')
    steps = data['dynamic']['steps']
    require(len(steps) == 31, 'Expected 31 insertion snapshots.')
    for step in steps:
        node, count = step['plainTree'], 0
        while node:
            require(node['left'] is None and node['point'] == [count+1]*3,
                    'Plain insertion snapshot is not the expected right chain.')
            count += 1
            node = node['right']
        require(count == step['n'] == step['heightPlain'], 'Insertion snapshot size differs.')
    last = steps[-1]
    require((last['heightPlain'], last['heightBalanced'], last['rebuilds']) == (31, 6, 9),
            'Fixed rebuilding result changed; update expectations and documentation deliberately.')
    print('[PASS] Export: JSON/JS/HTML data aligned; full benchmark data and fixed examples valid.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='rebuild PPT before checking; no benchmark rerun')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10 or newer is required.')
    node = shutil.which('node')
    if not node:
        parser.error('Node.js is required for building/syntax checks. Install it and reopen your terminal.')
    try:
        if args.build:
            print(run([sys.executable, 'ppt/build_deck.py']).strip())
        run([sys.executable, '-m', 'unittest', 'demo/test_kdtree.py', 'demo/test_teaching.py', '-v'])
        # unittest writes its summary to stderr; success is defined by its exit code.
        print('[PASS] Python core and teaching query unit tests.')
        check_deck(node)
        check_data()
    except (ValueError, RuntimeError, OSError, SyntaxError, KeyError, json.JSONDecodeError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr)
        return 1
    print('Project checks passed. Browser layout and presenter/audience interaction still require manual review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
