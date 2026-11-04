#!/usr/bin/env python3
"""Generate the Python-reference fixture for tests/test_reference_parity.gd.

    py -3 -P tests/reference/make_python_reference.py

Runs the ORIGINAL reference implementation from the preproduction package
(preproduction/tools/story_engine_v4.py and simulate_slice.py, unmodified, on preproduction/data/v3)
and records, in this project's id space:
  * routes      - save_json() of play_verified_route() for 4 branch combinations x skip
  * legacy      - v0.3 (save_version 2) saves of simulate_slice.play_route() and their v4 migration
  * traces      - scripted API call sequences (valid and invalid calls) with the result/error and the
                  full save_json() state after every call
  * corpus      - several thousand mutated / corrupted save texts with the reference verdict of
                  StoryEngine.load_json() (accepted state, StoryError message, or exception type)
  * json_cases  - json.loads / json.dumps behaviour the GDScript port must match
The preproduction package keeps the protagonist id from before the user's rename. The mapping
old -> new is DERIVED by comparing preproduction/data/v3/flags.json with data/v3/flags.json, and the script
asserts that the mapped preproduction data equals this project's data/v3 file by file.
Output: tests/reference/python_reference.json.gz (gzip, UTF-8 JSON).
"""
import copy
import gzip
import hashlib
import itertools
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRE = ROOT / 'preproduction'
sys.path.insert(0, str(PRE))
from tools.story_engine_v4 import StoryEngine, StoryError, play_verified_route, FORMAT, VERSION  # noqa: E402
from tools.simulate_slice import StoryRuntime, play_route as legacy_play  # noqa: E402

DATA_FILES = ['flags', 'quests', 'items', 'scenes', 'dialogue', 'puzzles', 'cinematics', 'locale_de',
              'reference_manifest']
A1 = ['share_with_irina', 'keep_private']
M1 = ['preserve_evidence', 'request_explanation']
SYMBOLS = ['square', 'circle', 'triangle']
OVERLAY = {'rotation_steps': 0, 'offset_x': 2, 'offset_y': -1}
MAX_BYTES = 128 * 1024


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def derive_rename():
    old = load(PRE / 'data/v3/flags.json')['protagonists']
    new = load(ROOT / 'data/v3/flags.json')['protagonists']
    assert len(old) == len(new)
    pairs = [(o, n) for o, n in zip(old, new) if o != n]
    assert len(pairs) == 1, 'expected exactly one renamed protagonist'
    return pairs


RENAME = derive_rename()


def to_project(text):
    for o, n in RENAME:
        text = text.replace(o, n).replace(o.capitalize(), n.capitalize())
    return text


def to_reference(text):
    for o, n in RENAME:
        text = text.replace(n, o).replace(n.capitalize(), o.capitalize())
    return text


def data_equivalence():
    report = {}
    for stem in DATA_FILES:
        mapped = json.loads(to_project(json.dumps(load(PRE / 'data/v3' / (stem + '.json')), ensure_ascii=False)))
        report[stem] = mapped == load(ROOT / 'data/v3' / (stem + '.json'))
    return report


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------------------------- routes
def play_dialogue(g, oid):
    g.start_dialogue(oid)
    while oid in g.state['dialogue_progress']:
        g.advance_dialogue(oid)


def to_signal(g):
    play_dialogue(g, 'a1_talk_irina')
    g.inspect('a1_inspect_seal')
    g.inspect('a1_inspect_timetable')


def routes():
    out = {}
    for a, m, skip in itertools.product(A1, M1, (False, True)):
        out['%s|%s|%s' % (a, m, 'skip' if skip else 'play')] = to_project(play_verified_route(a, m, skip).save_json())
    return out


def legacy():
    out = {}
    for a, m in itertools.product(A1, M1):
        old = legacy_play(a, m).save_json()
        g = StoryEngine()
        g.load_json(old)
        out['%s|%s' % (a, m)] = {'v2': to_project(old), 'migrated': to_project(g.save_json())}
    rt = StoryRuntime()
    for o in ['a1_talk_irina', 'a1_inspect_seal', 'a1_inspect_timetable', 'a1_solve_signal', 'a1_inspect_ledger']:
        rt.perform(o)
    rt.perform('a1_choose', 'keep_private')
    g = StoryEngine()
    g.load_json(rt.save_json())
    out['boundary|keep_private'] = {'v2': to_project(rt.save_json()), 'migrated': to_project(g.save_json())}
    return out


# --------------------------------------------------------------------------------------------- traces
TRACES = {
    'happy_path_with_noise': [
        ['available'], ['inspect', 'a1_inspect_seal'], ['start_dialogue', 'a1_inspect_seal'],
        ['current_line', 'a1_talk_irina'], ['advance_dialogue', 'a1_talk_irina'], ['inspect', 'bogus'],
        ['inspect', 123], ['start_dialogue', 'a1_talk_irina'], ['advance_dialogue', 'a1_talk_irina'],
        ['save_load'], ['current_line', 'a1_talk_irina'], ['start_dialogue', 'a1_talk_irina'],
        ['advance_dialogue', 'a1_talk_irina'], ['advance_dialogue', 'a1_talk_irina'],
        ['advance_dialogue', 'a1_talk_irina'], ['current_line', 'a1_talk_irina'],
        ['advance_dialogue', 'a1_talk_irina'], ['advance_dialogue', 'a1_talk_irina'],
        ['start_dialogue', 'a1_talk_irina'], ['hint', 'a1_solve_signal'], ['available'],
        ['inspect', 'a1_inspect_timetable'], ['solve_puzzle', 'a1_solve_signal', SYMBOLS],
        ['inspect', 'a1_inspect_seal'], ['inspect', 'a1_inspect_seal'], ['available'],
        ['solve_puzzle', 'a1_solve_signal', 'square'], ['solve_puzzle', 'a1_solve_signal', [False, 'circle']],
        ['solve_puzzle', 'a1_solve_signal', {'a': 0}], ['solve_puzzle', 'a1_solve_signal', 1],
        ['hint', 'a1_solve_signal'], ['solve_puzzle', 'a1_solve_signal', ['circle', 'square', 'triangle']],
        ['hint', 'a1_solve_signal'], ['solve_puzzle', 'a1_solve_signal', []], ['hint', 'a1_solve_signal'],
        ['save_load'], ['hint', 'a1_solve_signal'], ['solve_puzzle', 'a1_solve_signal', ['square', 'circle']],
        ['solve_puzzle', 'a1_solve_signal', SYMBOLS], ['solve_puzzle', 'a1_solve_signal', SYMBOLS],
        ['hint', 'a1_solve_signal'], ['consume', 'LS_A1_ToM1', False], ['inspect', 'a1_inspect_ledger'],
        ['choose', 'a1_choose', 'nope'], ['choose', 'a1_choose', 5], ['choose', 'a1_inspect_ledger', 'keep_private'],
        ['choose', 'a1_choose', 'keep_private'], ['choose', 'a1_choose', 'share_with_irina'], ['pending'],
        ['available'], ['finale', False], ['save_load'], ['consume', 'LS_A1_ToM1', True],
        ['consume', 'LS_A1_ToM1', False], ['consume', 'LS_M1_Hall', False],
        ['solve_puzzle', 'm1_align_plans', OVERLAY], ['inspect', 'm1_inspect_plan_b'],
        ['solve_puzzle', 'm1_align_plans', OVERLAY], ['inspect', 'm1_inspect_plan_a'],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': 0, 'offset_x': 2}],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': 0, 'offset_x': 2, 'offset_y': -1.0}],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': True, 'offset_x': 2, 'offset_y': -1}],
        ['solve_puzzle', 'm1_align_plans', [0, 2, -1]],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': 0, 'offset_x': 2, 'offset_y': -1, 'z': 1}],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': 1, 'offset_x': 2, 'offset_y': -1}],
        ['hint', 'm1_align_plans'], ['save_load'],
        ['solve_puzzle', 'm1_align_plans', {'rotation_steps': 0, 'offset_x': 3, 'offset_y': -1}],
        ['hint', 'm1_align_plans'], ['solve_puzzle', 'm1_align_plans', OVERLAY], ['pending'],
        ['start_dialogue', 'm1_talk_emil'], ['advance_dialogue', 'm1_talk_emil'], ['save_load'],
        ['current_line', 'm1_talk_emil'], ['choose', 'm1_choose', 'preserve_evidence'],
        ['advance_dialogue', 'm1_talk_emil'], ['advance_dialogue', 'm1_talk_emil'],
        ['advance_dialogue', 'm1_talk_emil'], ['advance_dialogue', 'm1_talk_emil'],
        ['advance_dialogue', 'm1_talk_emil'], ['available'], ['finale', True],
        ['choose', 'm1_choose', 'request_explanation'], ['pending'], ['available'], ['save_load'],
        ['finale', True], ['finale', False], ['save_load'], ['consume', 'LS_X1_Final', True],
        ['consume', 'LS_M1_Hall', True], ['pending'], ['consume', 'LS_M1_Hall', False],
        ['inspect', 'a1_inspect_seal'], ['new_game'], ['available'], ['pending'],
    ],
    'verified_route_share_preserve': [
        ['start_dialogue', 'a1_talk_irina']] + [['advance_dialogue', 'a1_talk_irina']] * 5 + [
        ['inspect', 'a1_inspect_seal'], ['inspect', 'a1_inspect_timetable'],
        ['solve_puzzle', 'a1_solve_signal', SYMBOLS], ['inspect', 'a1_inspect_ledger'],
        ['choose', 'a1_choose', 'share_with_irina'], ['consume', 'LS_A1_ToM1', False],
        ['inspect', 'm1_inspect_plan_a'], ['inspect', 'm1_inspect_plan_b'],
        ['solve_puzzle', 'm1_align_plans', OVERLAY], ['consume', 'LS_M1_Hall', False],
        ['start_dialogue', 'm1_talk_emil']] + [['advance_dialogue', 'm1_talk_emil']] * 5 + [
        ['choose', 'm1_choose', 'preserve_evidence'], ['consume', 'LS_X1_Final', False], ['finale', False],
        ['save_load'], ['available'], ['pending'],
    ],
}


def run_trace(actions):
    g = StoryEngine()
    out = []
    for act in actions:
        name = act[0]
        args = json.loads(to_reference(json.dumps(act[1:])))
        try:
            res = None
            if name == 'available':
                res = g.available()
            elif name == 'pending':
                res = g.pending_cinematics()
            elif name == 'hint':
                res = g.puzzle_hint_available(*args)
            elif name == 'start_dialogue':
                res = g.start_dialogue(*args)['id']
            elif name == 'current_line':
                res = g.current_dialogue_line(*args)['id']
            elif name == 'advance_dialogue':
                r = g.advance_dialogue(*args)
                res = None if r is None else r['id']
            elif name == 'inspect':
                g.inspect(*args)
            elif name == 'solve_puzzle':
                res = g.solve_puzzle(*args)
            elif name == 'choose':
                g.choose(*args)
            elif name == 'consume':
                g.consume_cinematic(*args)
            elif name == 'finale':
                g.finale(*args)
            elif name == 'save_load':
                text = g.save_json()
                g = StoryEngine()
                g.load_json(text)
            elif name == 'new_game':
                g.new_game()
            else:
                raise ValueError(name)
            entry = {'ok': True, 'result': json.loads(to_project(json.dumps(res)))}
        except StoryError as e:
            entry = {'ok': False, 'error': to_project(str(e))}
        entry['state'] = to_project(g.save_json())
        out.append(entry)
    return out


# --------------------------------------------------------------------------------------------- corpus
def base_saves():
    b = {}
    g = StoryEngine()
    b['fresh'] = g.save_json()
    g = StoryEngine()
    g.start_dialogue('a1_talk_irina')
    g.advance_dialogue('a1_talk_irina')
    g.advance_dialogue('a1_talk_irina')
    b['mid_dialogue'] = g.save_json()
    g = StoryEngine()
    to_signal(g)
    g.solve_puzzle('a1_solve_signal', ['circle', 'square', 'triangle'])
    g.solve_puzzle('a1_solve_signal', ['triangle', 'square', 'circle'])
    b['after_fail'] = g.save_json()
    g.solve_puzzle('a1_solve_signal', SYMBOLS)
    g.inspect('a1_inspect_ledger')
    g.choose('a1_choose', 'share_with_irina')
    b['a1_done'] = g.save_json()
    g.consume_cinematic('LS_A1_ToM1')
    g.inspect('m1_inspect_plan_b')
    g.inspect('m1_inspect_plan_a')
    g.solve_puzzle('m1_align_plans', {'rotation_steps': 1, 'offset_x': 2, 'offset_y': -1})
    g.solve_puzzle('m1_align_plans', OVERLAY)
    g.consume_cinematic('LS_M1_Hall', True)
    g.start_dialogue('m1_talk_emil')
    g.advance_dialogue('m1_talk_emil')
    b['mid_m1'] = g.save_json()
    b['finished'] = play_verified_route('keep_private', 'request_explanation').save_json()
    g = StoryEngine()
    to_signal(g)
    g.solve_puzzle('a1_solve_signal', SYMBOLS)
    g.inspect('a1_inspect_ledger')
    g.choose('a1_choose', 'keep_private')
    g.inspect('m1_inspect_plan_a')
    g.inspect('m1_inspect_plan_b')
    g.solve_puzzle('m1_align_plans', OVERLAY)
    play_dialogue(g, 'm1_talk_emil')
    g.choose('m1_choose', 'preserve_evidence')
    b['m1_done_unconsumed'] = g.save_json()
    g.finale()
    b['finished_unconsumed'] = g.save_json()
    b['legacy_v2_finished'] = legacy_play('share_with_irina', 'preserve_evidence').save_json()
    rt = StoryRuntime()
    for o in ['a1_talk_irina', 'a1_inspect_seal', 'a1_inspect_timetable', 'a1_solve_signal', 'a1_inspect_ledger']:
        rt.perform(o)
    rt.perform('a1_choose', 'keep_private')
    b['legacy_v2_boundary'] = rt.save_json()
    rt = StoryRuntime()
    rt.perform('a1_talk_irina')
    b['legacy_v2_early'] = rt.save_json()
    return {k: to_project(v) for k, v in b.items()}


VALUES = [None, True, False, 0, 1, 1.5, 'x', [], {}]
# Dialogue node ids in this project's id space, read from data/v3 (objective -> node ids).
_CONV = {c['id']: [n['id'] for n in c['nodes']] for c in load(ROOT / 'data/v3/dialogue.json')['conversations']}
DIALOGUE_NODES = {o['id']: _CONV[o['dialogue_id']] for q in load(ROOT / 'data/v3/quests.json')['quests']
                  for o in q['objectives'] if o['type'] == 'dialogue'}
RICH = {'mid_m1', 'finished', 'after_fail', 'legacy_v2_finished', 'm1_done_unconsumed'}


def mutations(name, text):
    """Yields (label, record or raw text). Records are dicts; raw strings are returned as str."""
    d = json.loads(text)
    keys = ['format', 'save_version', 'flags', 'completed_objectives', 'completed_events', 'inventory',
            'choice_history', 'current_scene', 'active_character', 'dialogue_progress', 'puzzle_attempts',
            'cinematics_seen', 'finale_viewed']
    rich = name in RICH

    def edit(label, fn):
        r = copy.deepcopy(d)
        fn(r)
        return label, r

    for k in keys:
        if k in d:
            yield edit('del:' + k, lambda r, k=k: r.pop(k))
        for i, v in enumerate(VALUES if rich or k in ('save_version', 'format', 'completed_objectives') else VALUES[:3]):
            yield edit('set:%s=%d' % (k, i), lambda r, k=k, v=v: r.__setitem__(k, copy.deepcopy(v)))
    for v in [1, 2, 3, 4, '3', 3.0, 2.0, True, None]:
        yield edit('version=%r' % (v,), lambda r, v=v: r.__setitem__('save_version', v))
    for v in ['other', None, 1, FORMAT.upper()]:
        yield edit('format=%r' % (v,), lambda r, v=v: r.__setitem__('format', v))
    flags = d.get('flags', {})
    for f in flags:
        for i, v in enumerate([True, False, 0, 1, 2, 3, 4, -1, 1.0, '1', None] if rich else [True, 1, 1.0, '1']):
            yield edit('flag:%s=%d' % (f, i), lambda r, f=f, v=v: r['flags'].__setitem__(f, v))
        if rich:
            yield edit('flagdel:' + f, lambda r, f=f: r['flags'].pop(f))
    yield edit('flag:unknown', lambda r: r['flags'].__setitem__('unknown_flag', 0))
    for k in ['completed_objectives', 'completed_events', 'inventory', 'cinematics_seen']:
        lst = d.get(k)
        if not isinstance(lst, list):
            continue
        if lst:
            yield edit('rev:' + k, lambda r, k=k: r[k].reverse())
            yield edit('dropfirst:' + k, lambda r, k=k: r[k].pop(0))
            yield edit('droplast:' + k, lambda r, k=k: r[k].pop())
            yield edit('dupfirst:' + k, lambda r, k=k: r[k].append(r[k][0]))
            yield edit('rot:' + k, lambda r, k=k: r.__setitem__(k, r[k][1:] + r[k][:1]))
            if len(lst) <= 3:
                for p in itertools.permutations(lst):
                    yield edit('perm:%s:%s' % (k, '/'.join(p)), lambda r, k=k, p=p: r.__setitem__(k, list(p)))
        for i, v in enumerate(['bogus', 1, None, [], {}, 'a1_completed', 'ev_ledger', 'LS_X1_Final', 'a1_choose']):
            if rich or i < 2:
                yield edit('append:%s=%d' % (k, i), lambda r, k=k, v=v: r[k].append(copy.deepcopy(v)))
    ch = d.get('choice_history')
    if isinstance(ch, dict):
        for obj in list(ch):
            for v in ['share_with_irina', 'keep_private', 'preserve_evidence', 'request_explanation', 'fake', 1, None, []]:
                yield edit('choice:%s=%r' % (obj, v), lambda r, obj=obj, v=v: r['choice_history'].__setitem__(obj, copy.deepcopy(v)))
            yield edit('choicedel:' + obj, lambda r, obj=obj: r['choice_history'].pop(obj))
        yield edit('choice:extra_talk', lambda r: r['choice_history'].__setitem__('a1_talk_irina', 'share_with_irina'))
        yield edit('choice:future', lambda r: r['choice_history'].__setitem__('m1_choose', 'preserve_evidence'))
    if d.get('save_version') == 3 or rich:
        for obj, ns in DIALOGUE_NODES.items():
            for v in ns + ['missing', 1, None]:
                yield edit('cursor:%s=%r' % (obj, v), lambda r, obj=obj, v=v: r.setdefault('dialogue_progress', {}).__setitem__(obj, v)
                           if isinstance(r.get('dialogue_progress', {}), dict) else None)
        yield edit('cursor:non_dialogue', lambda r: r.setdefault('dialogue_progress', {}).__setitem__('a1_inspect_seal', 'irina_01'))
        for obj in ['a1_solve_signal', 'm1_align_plans', 'a1_inspect_seal', 'unknown_objective']:
            for i, v in enumerate([-1, 0, 2, 100000, 100001, 1.0, True, '3', None]):
                yield edit('attempts:%s=%d' % (obj, i), lambda r, obj=obj, v=v: r.setdefault('puzzle_attempts', {}).__setitem__(obj, v)
                           if isinstance(r.get('puzzle_attempts', {}), dict) else None)
        for v in [True, False, 'yes', 1, None]:
            yield edit('finale_viewed=%r' % (v,), lambda r, v=v: r.__setitem__('finale_viewed', v))
    for v in ['L_A1_Railyard', 'L_M1_Archive', 'L_X1_Montage', 'bogus', None]:
        yield edit('scene=%r' % (v,), lambda r, v=v: r.__setitem__('current_scene', v))
    for v in ['alexei', RENAME[0][1], 'none', 'bogus', None]:
        yield edit('character=%r' % (v,), lambda r, v=v: r.__setitem__('active_character', v))
    yield edit('extra_key', lambda r: r.__setitem__('junk', {'nested': [1, 2, {'x': None}]}))
    # raw-level corruptions of the original text
    yield 'raw:truncated', text[:len(text) // 2]
    yield 'raw:trailing_garbage', text + 'x'
    yield 'raw:trailing_ws', '  \n' + text + '\n\t '
    yield 'raw:bom', '﻿' + text
    yield 'raw:crlf', text.replace('\n', '\r\n')
    yield 'raw:python_true', text.replace('true', 'True', 1) if 'true' in text else text + ' '
    yield 'raw:single_quotes', text.replace('"format"', "'format'")
    yield 'raw:trailing_comma', text[:text.rfind('}')].rstrip() + ',\n}'
    compact = json.dumps(d, ensure_ascii=False)
    yield 'raw:compact', compact
    yield 'raw:nan_field', compact[:-1] + ', "junk": NaN}'
    yield 'raw:inf_field', compact[:-1] + ', "junk": [Infinity, -Infinity, 1e400]}'
    yield 'raw:bigint_field', compact[:-1] + ', "junk": 123456789012345678901234567890}'
    yield 'raw:nested_150', compact[:-1] + ', "junk": ' + '[' * 150 + ']' * 150 + '}'
    yield 'raw:nested_1500', compact[:-1] + ', "junk": ' + '[' * 1500 + ']' * 1500 + '}'
    yield 'raw:control_char', compact[:-1] + ', "junk": "a\tb"}'.replace('\\t', '\t')
    yield 'raw:escaped_unicode', compact[:-1] + ', "junk": "\\u00e4\\ud83d\\ude00\\n"}'
    yield 'raw:dup_key_last_wins', compact[:-1] + ', "current_scene": "bogus"}'
    yield 'raw:dup_key_fix', compact[:-1] + ', "current_scene": ' + json.dumps(d.get('current_scene')) + '}'
    yield 'raw:leading_zero', compact.replace('"save_version": ' + str(d.get('save_version')),
                                              '"save_version": 0' + str(d.get('save_version')))
    yield 'raw:version_exp', compact.replace('"save_version": ' + str(d.get('save_version')),
                                             '"save_version": ' + str(d.get('save_version')) + 'e0')


def gen_raw(base_text, op):
    """Builds a generated case from a base save text (same algorithm in tests/test_reference_parity.gd)."""
    compact = json.dumps(json.loads(base_text), ensure_ascii=False)
    if op['op'] == 'pad_to':
        return compact + ' ' * (op['bytes'] - len(compact.encode('utf-8')))
    if op['op'] == 'junk_to':
        head, tail = compact[:-1] + ', "junk": "', '"}'
        room = op['bytes'] - len((head + tail).encode('utf-8'))
        return head + op['char'] * (room // 2) + 'a' * (room % 2) + tail
    if op['op'] == 'junk_nest':
        return compact[:-1] + ', "junk": ' + '[' * op['depth'] + ']' * op['depth'] + '}'
    raise ValueError(op)


def measure_max_junk_depth():
    """Deepest ignored junk field StoryEngine.load_json() still parses (CPython's C scanner limit)."""
    base = StoryEngine().save_json()
    lo, hi = 1, 20000
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        try:
            StoryEngine().load_json(gen_raw(base, {'op': 'junk_nest', 'depth': mid}))
            lo = mid
        except RecursionError:
            hi = mid
    return lo


MAX_JUNK_DEPTH = measure_max_junk_depth()


def corpus():
    bases = base_saves()
    cases = []
    seen = set()
    results = []
    result_index = {}

    def verdict(raw, mapped=True):
        try:
            g = StoryEngine()
            g.load_json(to_reference(raw) if mapped else raw)
            text = to_project(g.save_json())
            if text not in result_index:
                result_index[text] = len(results)
                results.append(text)
            return {'accept': True, 'result': result_index[text]}
        except StoryError as e:
            return {'accept': False, 'error': to_project(str(e))}
        except Exception as e:  # noqa: BLE001 - the reference raised something else: still a rejection
            return {'accept': False, 'exception': type(e).__name__}

    for name, text in bases.items():
        for label, payload in mutations(name, text):
            raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            if raw in seen:
                continue
            seen.add(raw)
            case = {'base': name, 'label': label, 'raw': raw}
            case.update(verdict(raw))
            cases.append(case)
        # Generated boundary cases. The same SEMANTIC case is built separately in each id space (the
        # renamed id is shorter than the pre-rename one, so a byte-exact copy would shift the size).
        for label, op in [('size:at_limit', {'op': 'pad_to', 'bytes': MAX_BYTES}),
                          ('size:over_limit', {'op': 'pad_to', 'bytes': MAX_BYTES + 1}),
                          ('size:umlaut_at_limit', {'op': 'junk_to', 'char': 'ä', 'bytes': MAX_BYTES}),
                          ('size:umlaut_over_limit', {'op': 'junk_to', 'char': 'ä', 'bytes': MAX_BYTES + 1}),
                          ('depth:max', {'op': 'junk_nest', 'depth': MAX_JUNK_DEPTH}),
                          ('depth:max_plus_1', {'op': 'junk_nest', 'depth': MAX_JUNK_DEPTH + 1})]:
            raw_ref = gen_raw(to_reference(text), op)
            case = {'base': name, 'label': label, 'gen': op}
            if op['op'] != 'junk_nest':
                case['bytes'] = op['bytes']
            case.update(verdict(raw_ref, mapped=False))
            cases.append(case)
    plain = ['', '[]', '{}', '{"save_version":999}', '{' + 'x' * 200000 + '}', 'null', '3', '"str"',
             '{"save_version": 3}', '{"save_version": 2}', '{"save_version": 3, "format": "%s"}' % FORMAT,
             '{"save_version": 2, "completed_objectives": [], "choice_history": {}}']
    for raw in plain:
        case = {'base': '', 'label': 'plain', 'raw': raw}
        case.update(verdict(raw))
        cases.append(case)
    return {'bases': bases, 'cases': cases, 'results': results, 'python_max_junk_depth': MAX_JUNK_DEPTH}


# --------------------------------------------------------------------------------------------- json
def json_cases():
    loads = ['1', '-0', '1.0', '1e2', '1E+2', '2.5e-3', '-12', '9223372036854775807', '[1, 2.0, true, null, "s"]',
             '{"a": 1, "a": 2}', '{"b": {"c": [1, {"d": 1.5}]}}', ' \n\t\r[1]\n', '"\\u00e4\\ud83d\\ude00\\/\\b\\f\\n\\r\\t"',
             'NaN', 'Infinity', '-Infinity', '[NaN]',
             '', ' ', '01', '1.', '.5', '+1', '-', '--1', '1e', '[1,]', '[,1]', '{"a":1,}', "{'a':1}", '{"a" 1}',
             '{1:2}', '"\\x41"', '"\\u12G4"', '"abc', 'nul', 'tru', '[1 2]', '{"a":1}x', '"a\tb"', '﻿[1]',
             '[' * 60 + ']' * 60]

    def typed(v):
        if isinstance(v, bool):
            return {'b': v}
        if isinstance(v, int):
            return {'i': str(v)}
        if isinstance(v, float):
            return {'f': repr(v)}
        if v is None:
            return {'n': 0}
        if isinstance(v, str):
            return {'s': v}
        if isinstance(v, list):
            return {'l': [typed(x) for x in v]}
        return {'d': [[k, typed(x)] for k, x in v.items()]}

    out_loads = []
    for t in loads:
        try:
            out_loads.append({'text': t, 'ok': True, 'typed': typed(json.loads(t))})
        except (ValueError, RecursionError):
            out_loads.append({'text': t, 'ok': False})
    values = [{}, [], {'b': 1, 'a': [1, 2, {}], 'c': {'x': None, 'y': True}}, 'ü"\\\n\u0001\u001f /\x7f',
              [1, -2, 0, 3.5, -2.25, 1.0, 100.0, 0.1, 1 / 3, 2.675, 123456.789], {'Z': 1, '_': 2, 'a': 3, 'ä': 4, 'A1': 5},
              [[[]], {}, [{}]], {'emoji': '\U0001F600', 'tab': '\t', 'cr': '\r'}]
    out_dumps = []
    for v in values:
        out_dumps.append({'value': json.dumps(v, ensure_ascii=False),
                          'pretty': json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2),
                          'compact': json.dumps(v, ensure_ascii=False, sort_keys=True)})
    return {'loads': out_loads, 'dumps': out_dumps}


def main():
    eq = data_equivalence()
    assert all(eq.values()), 'preproduction data (mapped) differs from data/v3: %r' % eq
    fixture = {
        'generator': 'tests/reference/make_python_reference.py',
        'python': sys.version.split()[0],
        'reference_sha256': {
            'story_engine_v4.py': sha256(PRE / 'tools/story_engine_v4.py'),
            'simulate_slice.py': sha256(PRE / 'tools/simulate_slice.py'),
        },
        'format': FORMAT, 'version': VERSION,
        'data_equivalent': eq,
        'data_sha256': {stem: sha256(ROOT / 'data/v3' / (stem + '.json')) for stem in DATA_FILES},
        'routes': routes(),
        'legacy': legacy(),
        'traces': {k: {'actions': v, 'expected': run_trace(v)} for k, v in TRACES.items()},
        'corpus': corpus(),
        'json_cases': json_cases(),
    }
    out = HERE / 'python_reference.json.gz'
    raw = json.dumps(fixture, ensure_ascii=False, sort_keys=True).encode('utf-8')
    out.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    cases = fixture['corpus']['cases']
    accepted = sum(1 for c in cases if c['accept'])
    exc = sum(1 for c in cases if 'exception' in c)
    print('wrote %s (%d bytes gz, %d bytes json)' % (out.relative_to(ROOT), out.stat().st_size, len(raw)))
    print('data equivalent after id mapping: %s' % all(eq.values()))
    print('routes %d, legacy %d, traces %d steps, corpus %d cases (%d accepted, %d StoryError, %d other exceptions)' % (
        len(fixture['routes']), len(fixture['legacy']), sum(len(t) for t in TRACES.values()),
        len(cases), accepted, len(cases) - accepted - exc, exc))


if __name__ == '__main__':
    main()
