#!/usr/bin/env python3
"""Generate the Python-reference fixture for tests/test_reference_parity.gd.

    python3 -P tests/reference/make_python_reference.py        (Windows: py -3 -P tests/reference/make_python_reference.py)

Re-run it after ANY change to data/v3 (text edits included): the parity test compares the SHA-256 of every data
file with the hashes stored in the fixture and asks for a regeneration when they differ. The script reads all
data at run time; nothing in here depends on the German texts.

Runs the ORIGINAL, unmodified reference implementation of the preproduction package:
  * preproduction/tools/story_engine_v4.py runs DIRECTLY on this project's data/v3 (only its module-level DATA
    path is monkeypatched). The project data already uses the protagonist id `konrad`, so engine runs need no
    id mapping. This covers the whole chain L_A1_Railyard -> L_M1_Archive -> L_C3_Station -> L_C3_Hall ->
    L_X1_Montage (documentation/C3_DESIGN.md §1).
  * preproduction/tools/simulate_slice.py (the v0.3 runtime) runs twice: on preproduction/data/v3 (authentic
    save_version 2 files of the old slice, written with the pre-rename protagonist id and mapped to this
    project's id space exactly as before) and on the project data (byte reference for the GDScript port
    tests/support/legacy_runtime_v2.gd, which reads data/v3).
  * json.loads as seen by the engine keeps the nesting limit of CPython on Windows (see REFERENCE_MAX_NESTING),
    so the recorded verdicts are the same whichever OS generates the fixture.
Recorded sections (all in this project's id space):
  * routes      - save_json() of the full route for every slice combination (a1 x m1) x every Chapter-3 option
                  (c3a x c3b) x skip/play; the finale is only reachable after c3b
  * legacy      - v0.3 saves (authentic + port) and the reference VERDICT of StoryEngine.load_json() on them:
                  the migrated state, or the exact StoryError message (saves that claim the old demo end
                  directly after M1 are rejected now; saves taken before it still migrate)
  * traces      - scripted API call sequences (valid and invalid calls, into Chapter 3) with the result/error
                  and the full save_json() state after every call
  * corpus      - several thousand mutated / corrupted save texts with the reference verdict of load_json()
                  (accepted state, StoryError message, or exception type)
  * json_cases  - json.loads / json.dumps behaviour the GDScript port must match
  * preproduction_delta - how data/v3 differs from the (id-mapped) preproduction data: additions only, apart
                  from the documented chain re-link
Output: tests/reference/python_reference.json.gz (gzip, UTF-8 JSON, deterministic).
"""
import contextlib
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
PROJECT_DATA = ROOT / 'data' / 'v3'
PRE_DATA = PRE / 'data' / 'v3'
sys.path.insert(0, str(PRE))
import tools.story_engine_v4 as engine_mod  # noqa: E402
import tools.simulate_slice as legacy_mod  # noqa: E402
from tools.story_engine_v4 import StoryEngine, StoryError, FORMAT, VERSION  # noqa: E402

# The unmodified modules point at the preproduction data; the engine is redirected to this project's data.
assert engine_mod.DATA.resolve() == PRE_DATA.resolve(), engine_mod.DATA
assert legacy_mod.DATA.resolve() == PRE_DATA.resolve(), legacy_mod.DATA
engine_mod.DATA = PROJECT_DATA


# ------------------------------------------------------------------------------------- JSON nesting (platform pin)
# CPython's C json scanner raises RecursionError at a nesting depth that depends on the BUILD
# (Py_C_RECURSION_LIMIT in 3.13: 3000 on Windows, 10000 on Linux/macOS). The GDScript port mirrors the Windows
# build the game ships on (scripts/story/story_engine.gd Json.MAX_DEPTH = 2998 containers, measured there).
# So that the recorded verdicts do not depend on the OS that generates the fixture, json.loads as seen by the
# reference engine is pinned to that limit: a document whose nesting first exceeds 2998 before any syntax
# error raises RecursionError exactly like json.loads on Windows; every other call goes to the real
# json.loads unchanged. On Windows this is a no-op.
REFERENCE_MAX_NESTING = 2998


def _first_overflow(text, limit):
    """Index of the bracket that opens container number limit+1 (strings skipped), or None."""
    depth = 0
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == '[' or ch == '{':
            depth += 1
            if depth > limit:
                return i
        elif ch == ']' or ch == '}':
            depth -= 1
    return None


class _PinnedJson:
    """The json module with the reference platform's nesting limit for loads() (see above)."""

    def __getattr__(self, name):
        return getattr(json, name)

    @staticmethod
    def loads(s, *args, **kwargs):
        over = None
        if isinstance(s, str) and s.count('[') + s.count('{') > REFERENCE_MAX_NESTING:
            over = _first_overflow(s, REFERENCE_MAX_NESTING)
        if over is None:
            return json.loads(s, *args, **kwargs)
        try:
            json.loads(s, *args, **kwargs)
        except json.JSONDecodeError as e:
            if e.pos < over:       # the syntax error comes first, as in the scanner
                raise
        raise RecursionError('maximum recursion depth exceeded while decoding a JSON array from a unicode string')


_NATIVE_JSON = engine_mod.json
_PINNED_JSON = _PinnedJson()
engine_mod.json = _PINNED_JSON

DATA_FILES = ['flags', 'quests', 'items', 'scenes', 'dialogue', 'puzzles', 'cinematics', 'locale_de',
              'reference_manifest']
LEGACY_DATA_FILES = ['flags', 'quests', 'items', 'scenes']   # what simulate_slice.StoryRuntime reads
MAX_BYTES = 128 * 1024


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------- data (read at run time)
QUESTS = load(PROJECT_DATA / 'quests.json')['quests']
OBJECTIVES = {o['id']: o for q in QUESTS for o in q['objectives']}
PUZZLES = {p['id']: p for p in load(PROJECT_DATA / 'puzzles.json')['puzzles']}
SEQUENCES = [s['id'] for s in load(PROJECT_DATA / 'cinematics.json')['sequences']]


def options(objective_id):
    return [c['id'] for c in OBJECTIVES[objective_id]['choices']]


def solution(objective_id):
    return copy.deepcopy(PUZZLES[OBJECTIVES[objective_id]['puzzle_id']]['solution'])


def display(objective_id):
    return copy.deepcopy(PUZZLES[OBJECTIVES[objective_id]['puzzle_id']]['display_symbols'])


A1 = options('a1_choose')          # share_with_irina, keep_private
M1 = options('m1_choose')          # preserve_evidence, request_explanation
C3A = options('c3a_choose')        # ask_elena, note_alone
C3B = options('c3b_choose')        # share_protocol, search_elena, report_delegation
SYMBOLS = solution('a1_solve_signal')
OVERLAY = solution('m1_align_plans')
PROTOCOL = solution('c3b_solve_protocol')
PROTOCOL_SHOWN = display('c3b_solve_protocol')


# ------------------------------------------------------------------------------------- id mapping (legacy only)
def derive_rename():
    old = load(PRE_DATA / 'flags.json')['protagonists']
    new = load(PROJECT_DATA / 'flags.json')['protagonists']
    assert len(old) == len(new)
    pairs = [(o, n) for o, n in zip(old, new) if o != n]
    assert len(pairs) == 1, 'expected exactly one renamed protagonist'
    return pairs


RENAME = derive_rename()


def to_project(text):
    """Maps text written by simulate_slice on the PREPRODUCTION data (pre-rename id) to this project's ids."""
    for o, n in RENAME:
        text = text.replace(o, n).replace(o.capitalize(), n.capitalize())
    return text


@contextlib.contextmanager
def legacy_data(path):
    """Points the unmodified simulate_slice module at a data directory for the duration of the block."""
    old = legacy_mod.DATA
    legacy_mod.DATA = path
    try:
        yield
    finally:
        legacy_mod.DATA = old


# ------------------------------------------------------------------------------------- data delta
def _is_subsequence(a, b):
    it = iter(b)
    return all(any(x == y for y in it) for x in a)


def _diff(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            if k not in b:
                out['modified'].append('%s/%s: removed' % (path, k))
            else:
                _diff(a[k], b[k], '%s/%s' % (path, k), out)
        out['added'] += sum(1 for k in b if k not in a)
    elif isinstance(a, list) and isinstance(b, list) and all(isinstance(x, dict) and 'id' in x for x in a + b):
        ia = {x['id']: x for x in a}
        ib = {x['id']: x for x in b}
        for k in ia:
            if k not in ib:
                out['modified'].append('%s[%s]: removed' % (path, k))
            else:
                _diff(ia[k], ib[k], '%s[%s]' % (path, k), out)
        out['added'] += sum(1 for k in ib if k not in ia)
        if not _is_subsequence([x['id'] for x in a], [x['id'] for x in b]):
            out['modified'].append('%s: reordered' % path)
    elif isinstance(a, list) and isinstance(b, list):
        if not _is_subsequence(a, b):
            out['modified'].append('%s: %s -> %s' % (path, json.dumps(a), json.dumps(b)))
        else:
            out['added'] += len(b) - len(a)
    elif a != b or type(a) is not type(b):
        out['modified'].append('%s: %s -> %s' % (path, json.dumps(a, ensure_ascii=False), json.dumps(b, ensure_ascii=False)))


def preproduction_delta():
    """data/v3 compared with the id-mapped preproduction data: number of additions + every non-additive change."""
    out = {'added': 0, 'modified': []}
    for stem in DATA_FILES:
        old = json.loads(to_project(json.dumps(load(PRE_DATA / (stem + '.json')), ensure_ascii=False)))
        _diff(old, load(PROJECT_DATA / (stem + '.json')), stem, out)
    return out


# ------------------------------------------------------------------------------------- routes
def play_dialogue(g, oid):
    g.start_dialogue(oid)
    while oid in g.state['dialogue_progress']:
        g.advance_dialogue(oid)


def to_signal(g):
    play_dialogue(g, 'a1_talk_irina')
    g.inspect('a1_inspect_seal')
    g.inspect('a1_inspect_timetable')


def play_a1(g, a1):
    to_signal(g)
    g.solve_puzzle('a1_solve_signal', copy.deepcopy(SYMBOLS))
    g.inspect('a1_inspect_ledger')
    g.choose('a1_choose', a1)


def play_m1(g, m1):
    g.inspect('m1_inspect_plan_a')
    g.inspect('m1_inspect_plan_b')
    g.solve_puzzle('m1_align_plans', copy.deepcopy(OVERLAY))
    play_dialogue(g, 'm1_talk_emil')
    g.choose('m1_choose', m1)


def play_c3a(g, c3a):
    play_dialogue(g, 'c3a_talk_conductor')
    g.inspect('c3a_inspect_weighbill')
    g.inspect('c3a_inspect_departures')
    play_dialogue(g, 'c3a_pass_control')
    play_dialogue(g, 'c3a_talk_elena')
    g.choose('c3a_choose', c3a)


def play_c3b(g, c3b):
    play_dialogue(g, 'c3b_arrival')
    g.inspect('c3b_inspect_seating')
    g.inspect('c3b_inspect_log')
    g.solve_puzzle('c3b_solve_protocol', copy.deepcopy(PROTOCOL))
    g.inspect('c3b_inspect_booth')
    play_dialogue(g, 'c3b_talk_alexei')
    g.choose('c3b_choose', c3b)


def play_full_route(a1, m1, c3a, c3b, skip=False):
    """story_engine_v4.play_verified_route() extended to the whole chain (GDScript: Kit.play_verified_route):
    authentic dialogue and puzzle flows, every cinematic consumed at the end, then the finale."""
    g = StoryEngine()
    play_a1(g, a1)
    play_m1(g, m1)
    play_c3a(g, c3a)
    play_c3b(g, c3b)
    for seq in list(g.pending_cinematics()):
        g.consume_cinematic(seq, skipped=skip)
    g.finale(skipped=skip)
    return g


def route_key(a1, m1, c3a, c3b, skip):
    return '|'.join([a1, m1, c3a, c3b, 'skip' if skip else 'play'])


def routes():
    # The preproduction helper ends with finale() right after M1; on the new chain that is locked.
    try:
        engine_mod.play_verified_route()
        raise AssertionError('play_verified_route() should stop at the locked finale on the Chapter-3 chain')
    except StoryError as e:
        assert str(e) == 'Finale locked', e
    out = {}
    for a1, m1, c3a, c3b, skip in itertools.product(A1, M1, C3A, C3B, (False, True)):
        out[route_key(a1, m1, c3a, c3b, skip)] = play_full_route(a1, m1, c3a, c3b, skip).save_json()
    return out


# ------------------------------------------------------------------------------------- legacy (v0.3)
LEGACY_ORDER = ['a1_talk_irina', 'a1_inspect_seal', 'a1_inspect_timetable', 'a1_solve_signal', 'a1_inspect_ledger',
                'a1_choose', 'm1_inspect_plan_a', 'm1_inspect_plan_b', 'm1_align_plans', 'm1_talk_emil', 'm1_choose']


def legacy_runtime(steps, a1, m1, finale):
    """simulate_slice.StoryRuntime on the current legacy_mod.DATA: the first `steps` objectives of
    simulate_slice.play_route(), optionally followed by its finale() (steps=11 + finale == play_route)."""
    rt = legacy_mod.StoryRuntime()
    for o in LEGACY_ORDER[:steps]:
        rt.perform(o, {'a1_choose': a1, 'm1_choose': m1}.get(o))
    if finale:
        rt.finale()
    return rt


def verdict(raw):
    """Reference verdict of StoryEngine.load_json(raw) on the project data."""
    try:
        g = StoryEngine()
        g.load_json(raw)
        return {'accept': True, 'state': g.save_json()}
    except StoryError as e:
        return {'accept': False, 'error': str(e)}


def legacy_cases():
    cases = {}
    for a1, m1 in itertools.product(A1, M1):
        # the old demo end: simulate_slice.play_route() = all 11 objectives + finale (L_X1_Montage, slice_completed)
        cases['%s|%s' % (a1, m1)] = {'steps': 11, 'a1': a1, 'm1': m1, 'finale': True}
    # the montage of the old slice before its end card (m1_completed, scene L_X1_Montage, no slice_completed)
    cases['m1_end|keep_private|request_explanation'] = {'steps': 11, 'a1': 'keep_private', 'm1': 'request_explanation',
                                                        'finale': False}
    # the last v0.3 save before m1_choose, the protagonist boundary after A1 and the first objective
    cases['m1_talk|share_with_irina'] = {'steps': 10, 'a1': 'share_with_irina', 'm1': None, 'finale': False}
    cases['boundary|keep_private'] = {'steps': 6, 'a1': 'keep_private', 'm1': None, 'finale': False}
    cases['early'] = {'steps': 1, 'a1': None, 'm1': None, 'finale': False}
    return cases


def legacy():
    defaults = {k: v['default'] for k, v in load(PROJECT_DATA / 'flags.json')['flags'].items()}
    out = {}
    for key, spec in legacy_cases().items():
        with legacy_data(PRE_DATA):
            authentic = to_project(legacy_runtime(spec['steps'], spec['a1'], spec['m1'], spec['finale']).save_json())
        with legacy_data(PROJECT_DATA):
            port = to_project(legacy_runtime(spec['steps'], spec['a1'], spec['m1'], spec['finale']).save_json())
        # Same progress; the authentic file just lacks the flags added after the slice (they default on load).
        a, p = json.loads(authentic), json.loads(port)
        assert p == dict(a, flags={**defaults, **a['flags']}), key
        rec = dict(spec)
        rec.update({'v2': authentic, 'verdict': verdict(authentic), 'port': port, 'port_verdict': verdict(port)})
        out[key] = rec
    return out


# ------------------------------------------------------------------------------------- traces
def _dialogue(oid, advances):
    return [['start_dialogue', oid]] + [['advance_dialogue', oid]] * advances


def _slice_route(a1, m1):
    """Actions of the verified A1 + M1 route (dialogues node by node, no cinematic consumed)."""
    return (_dialogue('a1_talk_irina', 5) + [
        ['inspect', 'a1_inspect_seal'], ['inspect', 'a1_inspect_timetable'],
        ['solve_puzzle', 'a1_solve_signal', SYMBOLS], ['inspect', 'a1_inspect_ledger'], ['choose', 'a1_choose', a1],
        ['inspect', 'm1_inspect_plan_a'], ['inspect', 'm1_inspect_plan_b'],
        ['solve_puzzle', 'm1_align_plans', OVERLAY]] + _dialogue('m1_talk_emil', 5) + [['choose', 'm1_choose', m1]])


TRACES = {
    # The original slice trace, unchanged: after M1 the finale and the old end-card calls now hit the locked
    # finale (Chapter 3 pending) instead of succeeding.
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
    # The verified route, now through the whole chain, consuming each cinematic when it is queued (director).
    'verified_route_share_preserve': _dialogue('a1_talk_irina', 5) + [
        ['inspect', 'a1_inspect_seal'], ['inspect', 'a1_inspect_timetable'],
        ['solve_puzzle', 'a1_solve_signal', SYMBOLS], ['inspect', 'a1_inspect_ledger'],
        ['choose', 'a1_choose', 'share_with_irina'], ['consume', 'LS_A1_ToM1', False],
        ['inspect', 'm1_inspect_plan_a'], ['inspect', 'm1_inspect_plan_b'],
        ['solve_puzzle', 'm1_align_plans', OVERLAY], ['consume', 'LS_M1_Hall', False]] + _dialogue('m1_talk_emil', 5) + [
        ['choose', 'm1_choose', 'preserve_evidence'], ['consume', 'LS_X1_Final', False], ['finale', False],
        ['consume', 'LS_C3_Trains', False]] + _dialogue('c3a_talk_conductor', 7) + [
        ['inspect', 'c3a_inspect_weighbill'], ['inspect', 'c3a_inspect_departures']] + _dialogue('c3a_pass_control', 8) +
        _dialogue('c3a_talk_elena', 9) + [
        ['choose', 'c3a_choose', 'ask_elena'], ['consume', 'LS_C3_ToHall', False], ['finale', False]] +
        _dialogue('c3b_arrival', 9) + [
        ['inspect', 'c3b_inspect_seating'], ['inspect', 'c3b_inspect_log'],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL], ['inspect', 'c3b_inspect_booth']] +
        _dialogue('c3b_talk_alexei', 12) + [
        ['choose', 'c3b_choose', 'share_protocol'], ['consume', 'LS_C3_Close', False], ['finale', False],
        ['save_load'], ['available'], ['pending'],
    ],
    # Chapter 3 with noise: locked/foreign objectives, the finale before c3b, C3 cinematics out of order,
    # every kind of protocol-puzzle payload, invalid choice ids, resumes and reloads mid-chapter.
    'chapter3_with_noise': [
        ['start_dialogue', 'c3a_talk_conductor'], ['inspect', 'c3b_inspect_seating'],
        ['consume', 'LS_C3_Trains', False]] + _slice_route('keep_private', 'request_explanation')[:-1] + [
        ['inspect', 'c3a_inspect_weighbill'], ['choose', 'c3a_choose', 'ask_elena'],
        ['choose', 'm1_choose', 'request_explanation'],
        ['available'], ['pending'], ['finale', False], ['finale', True],
        ['inspect', 'c3a_inspect_weighbill'], ['inspect', 'c3a_inspect_departures'],
        ['start_dialogue', 'c3a_pass_control'], ['current_line', 'c3a_talk_conductor'],
        ['choose', 'c3a_choose', 'ask_elena'], ['inspect', 'c3b_inspect_seating'],
        ['start_dialogue', 'c3b_arrival'], ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL],
        ['hint', 'c3b_solve_protocol'], ['choose', 'c3b_choose', 'share_protocol'],
        ['consume', 'LS_C3_ToHall', False], ['consume', 'LS_C3_Close', True],
        ['consume', 'LS_X1_Final', True], ['consume', 'LS_C3_Trains', False], ['consume', 'LS_C3_Trains', False],
        ['pending'], ['save_load'],
        ['start_dialogue', 'c3a_talk_conductor'], ['advance_dialogue', 'c3a_talk_conductor'],
        ['advance_dialogue', 'c3a_talk_conductor'], ['save_load'], ['current_line', 'c3a_talk_conductor'],
        ['start_dialogue', 'c3a_talk_conductor']] + [['advance_dialogue', 'c3a_talk_conductor']] * 4 + [
        ['current_line', 'c3a_talk_conductor'], ['available'], ['advance_dialogue', 'c3a_talk_conductor'],
        ['advance_dialogue', 'c3a_talk_conductor'], ['start_dialogue', 'c3a_talk_conductor'],
        ['inspect', 'c3a_inspect_departures'], ['inspect', 'c3a_inspect_departures'],
        ['start_dialogue', 'c3a_pass_control'], ['inspect', 'c3a_talk_conductor'],
        ['start_dialogue', 'c3a_inspect_weighbill'], ['inspect', 'c3a_inspect_weighbill'], ['available'],
        ['start_dialogue', 'c3a_pass_control'], ['advance_dialogue', 'c3a_pass_control'],
        ['advance_dialogue', 'c3a_pass_control'], ['advance_dialogue', 'c3a_pass_control'], ['save_load'],
        ['current_line', 'c3a_pass_control'], ['start_dialogue', 'c3a_pass_control']] +
        [['advance_dialogue', 'c3a_pass_control']] * 5 + [
        ['start_dialogue', 'c3a_talk_elena'], ['advance_dialogue', 'c3a_talk_elena'],
        ['choose', 'c3a_choose', 'ask_elena']] + [['advance_dialogue', 'c3a_talk_elena']] * 8 + [
        ['choose', 'c3a_choose', 'nope'], ['choose', 'c3a_choose', 3], ['choose', 'c3a_choose', None],
        ['choose', 'c3a_choose', ['ask_elena']], ['choose', 'c3a_choose', 'share_protocol'],
        ['choose', 'c3a_choose', 'keep_private'], ['choose', 'c3a_talk_elena', 'ask_elena'],
        ['choose', 'c3a_inspect_weighbill', 'note_alone'], ['solve_puzzle', 'c3a_choose', PROTOCOL],
        ['choose', 'c3a_choose', 'note_alone'], ['choose', 'c3a_choose', 'ask_elena'],
        ['choose', 'c3a_choose', 'note_alone'], ['pending'], ['available'], ['finale', True], ['save_load'],
        ['inspect', 'c3b_inspect_log'], ['hint', 'c3b_solve_protocol'], ['consume', 'LS_C3_Close', False],
        ['start_dialogue', 'c3b_arrival'], ['advance_dialogue', 'c3b_arrival'], ['advance_dialogue', 'c3b_arrival'],
        ['save_load'], ['current_line', 'c3b_arrival']] + [['advance_dialogue', 'c3b_arrival']] * 7 + [
        ['available'], ['hint', 'c3b_solve_protocol'], ['inspect', 'c3b_inspect_log'],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL], ['inspect', 'c3b_inspect_booth'],
        ['inspect', 'c3b_inspect_seating'], ['available'], ['hint', 'c3b_solve_protocol'],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL_SHOWN], ['hint', 'c3b_solve_protocol'],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL[:3]], ['hint', 'c3b_solve_protocol'],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL + [PROTOCOL[-1]]],
        ['solve_puzzle', 'c3b_solve_protocol', [PROTOCOL[0], 1] + PROTOCOL[2:]],
        ['solve_puzzle', 'c3b_solve_protocol', [None] + PROTOCOL[1:]],
        ['solve_puzzle', 'c3b_solve_protocol', ','.join(PROTOCOL)],
        ['solve_puzzle', 'c3b_solve_protocol', {'0': PROTOCOL[0]}],
        ['solve_puzzle', 'c3b_solve_protocol', None], ['solve_puzzle', 'c3b_solve_protocol', 4],
        ['solve_puzzle', 'c3b_solve_protocol', [PROTOCOL]],
        ['solve_puzzle', 'c3b_solve_protocol', []], ['save_load'], ['hint', 'c3b_solve_protocol'],
        ['solve_puzzle', 'c3b_solve_protocol', [PROTOCOL[0].capitalize()] + PROTOCOL[1:]],
        ['solve_puzzle', 'c3b_solve_protocol', list(reversed(PROTOCOL))],
        ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL], ['solve_puzzle', 'c3b_solve_protocol', PROTOCOL],
        ['hint', 'c3b_solve_protocol'], ['start_dialogue', 'c3b_talk_alexei'], ['inspect', 'c3b_inspect_booth'],
        ['inspect', 'c3b_inspect_booth'], ['start_dialogue', 'c3b_talk_alexei']] +
        [['advance_dialogue', 'c3b_talk_alexei']] * 5 + [
        ['save_load'], ['current_line', 'c3b_talk_alexei'], ['choose', 'c3b_choose', 'search_elena'],
        ['start_dialogue', 'c3b_talk_alexei']] + [['advance_dialogue', 'c3b_talk_alexei']] * 7 + [
        ['choose', 'c3b_choose', 'note_alone'], ['choose', 'c3b_choose', ''], ['choose', 'c3b_choose', 'Search_Elena'],
        ['consume', 'LS_C3_ToHall', True], ['consume', 'LS_C3_Close', False], ['finale', False],
        ['choose', 'c3b_choose', 'search_elena'], ['choose', 'c3b_choose', 'report_delegation'],
        ['pending'], ['available'], ['save_load'], ['finale', True], ['finale', False],
        ['consume', 'LS_C3_Close', True], ['consume', 'LS_A1_ToM1', False], ['consume', 'LS_M1_Hall', True],
        ['consume', 'LS_C3_Close', True], ['pending'], ['save_load'], ['inspect', 'c3a_inspect_weighbill'],
        ['new_game'], ['available'], ['pending'],
    ],
}


def run_trace(actions):
    g = StoryEngine()
    out = []
    for act in actions:
        name = act[0]
        args = json.loads(json.dumps(act[1:]))   # exactly what the GDScript side reads back from the fixture
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
            entry = {'ok': True, 'result': json.loads(json.dumps(res))}
        except StoryError as e:
            entry = {'ok': False, 'error': str(e)}
        entry['state'] = g.save_json()
        out.append(entry)
    return out


# ------------------------------------------------------------------------------------- corpus
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
    # M1 done, every cinematic still queued: the save at the Chapter-3 entry (L_C3_Station).
    g = StoryEngine()
    play_a1(g, 'keep_private')
    play_m1(g, 'preserve_evidence')
    b['m1_done_unconsumed'] = g.save_json()
    # Chapter 3 checkpoints
    g.consume_cinematic('LS_X1_Final')
    play_dialogue(g, 'c3a_talk_conductor')
    g.inspect('c3a_inspect_departures')
    g.inspect('c3a_inspect_weighbill')
    g.start_dialogue('c3a_pass_control')
    for _ in range(3):
        g.advance_dialogue('c3a_pass_control')
    b['mid_c3a'] = g.save_json()
    while 'c3a_pass_control' in g.state['dialogue_progress']:
        g.advance_dialogue('c3a_pass_control')
    play_dialogue(g, 'c3a_talk_elena')
    g.choose('c3a_choose', 'note_alone')
    b['c3a_done'] = g.save_json()
    g.consume_cinematic('LS_C3_ToHall', True)
    play_dialogue(g, 'c3b_arrival')
    g.inspect('c3b_inspect_log')
    g.inspect('c3b_inspect_seating')
    g.solve_puzzle('c3b_solve_protocol', PROTOCOL_SHOWN)
    g.solve_puzzle('c3b_solve_protocol', PROTOCOL[:2])
    b['mid_c3b'] = g.save_json()
    g.solve_puzzle('c3b_solve_protocol', PROTOCOL)
    g.inspect('c3b_inspect_booth')
    play_dialogue(g, 'c3b_talk_alexei')
    g.choose('c3b_choose', 'report_delegation')
    b['c3b_done_unconsumed'] = g.save_json()
    g.finale()
    b['finished_unconsumed'] = g.save_json()
    b['finished'] = play_full_route('keep_private', 'request_explanation', 'ask_elena', 'search_elena').save_json()
    # authentic v0.3 saves (simulate_slice on the preproduction data, mapped to this project's ids)
    with legacy_data(PRE_DATA):
        b['legacy_v2_finished'] = to_project(legacy_mod.play_route('share_with_irina', 'preserve_evidence').save_json())
        b['legacy_v2_m1_end'] = to_project(legacy_runtime(11, 'share_with_irina', 'request_explanation', False).save_json())
        b['legacy_v2_boundary'] = to_project(legacy_runtime(6, 'keep_private', None, False).save_json())
        b['legacy_v2_early'] = to_project(legacy_runtime(1, None, None, False).save_json())
    return b


VALUES = [None, True, False, 0, 1, 1.5, 'x', [], {}]
# Dialogue node ids, read from data/v3 (objective -> node ids).
_CONV = {c['id']: [n['id'] for n in c['nodes']] for c in load(PROJECT_DATA / 'dialogue.json')['conversations']}
DIALOGUE_NODES = {o['id']: _CONV[o['dialogue_id']] for o in OBJECTIVES.values() if o['type'] == 'dialogue'}
PUZZLE_OBJECTIVES = [o['id'] for o in OBJECTIVES.values() if o['type'] == 'puzzle']
CHOICE_IDS = [c for o in OBJECTIVES.values() if o['type'] == 'choice' for c in options(o['id'])]
SCENES = [s['id'] for s in load(PROJECT_DATA / 'scenes.json')['scenes']]
RICH = {'after_fail', 'mid_m1', 'm1_done_unconsumed', 'mid_c3b', 'finished'}


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
        for i, v in enumerate(['bogus', 1, None, [], {}, 'a1_completed', 'ev_ledger', 'LS_X1_Final', 'a1_choose',
                               'c3a_completed', 'ev_c3_carbon', 'LS_C3_Close', 'c3b_choose']):
            if rich or i < 2:
                yield edit('append:%s=%d' % (k, i), lambda r, k=k, v=v: r[k].append(copy.deepcopy(v)))
    ch = d.get('choice_history')
    if isinstance(ch, dict):
        for obj in list(ch):
            own = options(obj) if obj in OBJECTIVES and OBJECTIVES[obj]['type'] == 'choice' else []
            foreign = [c for c in CHOICE_IDS if c not in own]
            for v in (CHOICE_IDS if rich else own + foreign[:1]) + ['fake', 1, None, []]:
                yield edit('choice:%s=%r' % (obj, v), lambda r, obj=obj, v=v: r['choice_history'].__setitem__(obj, copy.deepcopy(v)))
            yield edit('choicedel:' + obj, lambda r, obj=obj: r['choice_history'].pop(obj))
        yield edit('choice:extra_talk', lambda r: r['choice_history'].__setitem__('a1_talk_irina', 'share_with_irina'))
        yield edit('choice:future', lambda r: r['choice_history'].__setitem__('m1_choose', 'preserve_evidence'))
        yield edit('choice:future_c3', lambda r: r['choice_history'].__setitem__('c3b_choose', 'share_protocol'))
    if d.get('save_version') == 3 or rich:
        for obj, ns in DIALOGUE_NODES.items():
            for v in (ns + ['missing', 1, None]) if rich else [ns[0], ns[-1], 'missing']:
                yield edit('cursor:%s=%r' % (obj, v), lambda r, obj=obj, v=v: r.setdefault('dialogue_progress', {}).__setitem__(obj, v)
                           if isinstance(r.get('dialogue_progress', {}), dict) else None)
        yield edit('cursor:non_dialogue', lambda r: r.setdefault('dialogue_progress', {}).__setitem__('a1_inspect_seal', 'irina_01'))
        yield edit('cursor:foreign_node', lambda r: r.setdefault('dialogue_progress', {}).__setitem__('c3a_talk_elena', 'c3b_meet_01')
                   if isinstance(r.get('dialogue_progress', {}), dict) else None)
        for obj in PUZZLE_OBJECTIVES + ['a1_inspect_seal', 'unknown_objective']:
            for i, v in enumerate([-1, 0, 2, 100000, 100001, 1.0, True, '3', None] if rich else [-1, 0, 100001, True, None]):
                yield edit('attempts:%s=%d' % (obj, i), lambda r, obj=obj, v=v: r.setdefault('puzzle_attempts', {}).__setitem__(obj, v)
                           if isinstance(r.get('puzzle_attempts', {}), dict) else None)
        for v in [True, False, 'yes', 1, None]:
            yield edit('finale_viewed=%r' % (v,), lambda r, v=v: r.__setitem__('finale_viewed', v))
    for v in SCENES + ['bogus', None]:
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


def native_max_junk_depth():
    """measure_max_junk_depth() with this interpreter's own json limit (printed only: it differs per OS)."""
    engine_mod.json = _NATIVE_JSON
    try:
        return measure_max_junk_depth()
    finally:
        engine_mod.json = _PINNED_JSON


def measure_max_junk_depth():
    """Deepest ignored junk field StoryEngine.load_json() still parses (the C scanner limit, pinned above)."""
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


def corpus():
    max_junk_depth = measure_max_junk_depth()
    bases = base_saves()
    cases = []
    seen = set()
    results = []
    result_index = {}

    def judge(raw):
        try:
            g = StoryEngine()
            g.load_json(raw)
            text = g.save_json()
            if text not in result_index:
                result_index[text] = len(results)
                results.append(text)
            return {'accept': True, 'result': result_index[text]}
        except StoryError as e:
            return {'accept': False, 'error': str(e)}
        except Exception as e:  # noqa: BLE001 - the reference raised something else: still a rejection
            return {'accept': False, 'exception': type(e).__name__}

    for name, text in bases.items():
        for label, payload in mutations(name, text):
            raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            if raw in seen:
                continue
            seen.add(raw)
            case = {'base': name, 'label': label, 'raw': raw}
            case.update(judge(raw))
            cases.append(case)
        # Generated boundary cases (rebuilt from the base by tests/test_reference_parity.gd, not stored).
        for label, op in [('size:at_limit', {'op': 'pad_to', 'bytes': MAX_BYTES}),
                          ('size:over_limit', {'op': 'pad_to', 'bytes': MAX_BYTES + 1}),
                          ('size:umlaut_at_limit', {'op': 'junk_to', 'char': 'ä', 'bytes': MAX_BYTES}),
                          ('size:umlaut_over_limit', {'op': 'junk_to', 'char': 'ä', 'bytes': MAX_BYTES + 1}),
                          ('depth:max', {'op': 'junk_nest', 'depth': max_junk_depth}),
                          ('depth:max_plus_1', {'op': 'junk_nest', 'depth': max_junk_depth + 1})]:
            case = {'base': name, 'label': label, 'gen': op}
            if op['op'] != 'junk_nest':
                case['bytes'] = op['bytes']
            case.update(judge(gen_raw(text, op)))
            cases.append(case)
    plain = ['', '[]', '{}', '{"save_version":999}', '{' + 'x' * 200000 + '}', 'null', '3', '"str"',
             '{"save_version": 3}', '{"save_version": 2}', '{"save_version": 3, "format": "%s"}' % FORMAT,
             '{"save_version": 2, "completed_objectives": [], "choice_history": {}}']
    for raw in plain:
        case = {'base': '', 'label': 'plain', 'raw': raw}
        case.update(judge(raw))
        cases.append(case)
    return {'bases': bases, 'cases': cases, 'results': results, 'python_max_junk_depth': max_junk_depth}


# ------------------------------------------------------------------------------------- json
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
    values = [{}, [], {'b': 1, 'a': [1, 2, {}], 'c': {'x': None, 'y': True}}, 'ü"\\\n\u0001\u001f /\x7f',
              [1, -2, 0, 3.5, -2.25, 1.0, 100.0, 0.1, 1 / 3, 2.675, 123456.789], {'Z': 1, '_': 2, 'a': 3, 'ä': 4, 'A1': 5},
              [[[]], {}, [{}]], {'emoji': '\U0001F600', 'tab': '\t', 'cr': '\r'}]
    out_dumps = []
    for v in values:
        out_dumps.append({'value': json.dumps(v, ensure_ascii=False),
                          'pretty': json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2),
                          'compact': json.dumps(v, ensure_ascii=False, sort_keys=True)})
    return {'loads': out_loads, 'dumps': out_dumps}


def main():
    native_depth = native_max_junk_depth()
    assert native_depth + 1 >= REFERENCE_MAX_NESTING, 'this CPython build parses less nesting than the reference platform'
    fixture = {
        'generator': 'tests/reference/make_python_reference.py',
        'python': sys.version.split()[0],
        'reference_sha256': {
            'story_engine_v4.py': sha256(PRE / 'tools/story_engine_v4.py'),
            'simulate_slice.py': sha256(PRE / 'tools/simulate_slice.py'),
        },
        'format': FORMAT, 'version': VERSION,
        'engine_data': 'data/v3',
        'json_max_nesting': REFERENCE_MAX_NESTING,
        'data_sha256': {stem: sha256(PROJECT_DATA / (stem + '.json')) for stem in DATA_FILES},
        'legacy_data_sha256': {stem: sha256(PRE_DATA / (stem + '.json')) for stem in LEGACY_DATA_FILES},
        'preproduction_delta': preproduction_delta(),
        'choices': {'a1_choose': A1, 'm1_choose': M1, 'c3a_choose': C3A, 'c3b_choose': C3B},
        'routes': routes(),
        'legacy': legacy(),
        'traces': {k: {'actions': v, 'expected': run_trace(v)} for k, v in TRACES.items()},
        'corpus': corpus(),
        'json_cases': json_cases(),
    }
    raw = json.dumps(fixture, ensure_ascii=False, sort_keys=True).encode('utf-8')
    for o, _n in RENAME:   # every record is in this project's id space
        assert o.encode('utf-8') not in raw.lower(), 'pre-rename id leaked into the fixture'
    out = HERE / 'python_reference.json.gz'
    out.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    cases = fixture['corpus']['cases']
    accepted = sum(1 for c in cases if c['accept'])
    exc = sum(1 for c in cases if 'exception' in c)
    legacy_ok = sum(1 for v in fixture['legacy'].values() if v['verdict']['accept'])
    print('wrote %s (%d bytes gz, %d bytes json)' % (out.relative_to(ROOT), out.stat().st_size, len(raw)))
    print('engine data: data/v3; preproduction delta: %d additions, modified: %s' % (
        fixture['preproduction_delta']['added'], fixture['preproduction_delta']['modified']))
    print('json nesting: reference pinned to %d containers (junk depth %d); this interpreter natively parses junk '
          'depth %d' % (REFERENCE_MAX_NESTING, fixture['corpus']['python_max_junk_depth'], native_depth))
    print('routes %d, legacy %d (%d migrate, %d rejected), traces %d steps, corpus %d cases '
          '(%d accepted, %d StoryError, %d other exceptions)' % (
              len(fixture['routes']), len(fixture['legacy']), legacy_ok, len(fixture['legacy']) - legacy_ok,
              sum(len(t) for t in TRACES.values()), len(cases), accepted, len(cases) - accepted - exc, exc))
    for key, v in fixture['legacy'].items():
        print('  legacy %-42s %s' % (key, 'migrates' if v['verdict']['accept'] else 'rejected: ' + v['verdict']['error']))


if __name__ == '__main__':
    main()
