"""cine_finale_build -- builds every asset of the X1 finale montage and its timeline (owner: trans-finale).

Run:  py -3 -P tools/pixelgen/cine_finale_build.py [--preview DIR]
Writes assets/cinematics/finale/<set>/*.png and assets/cinematics/finale/finale.json (sets, shots, events),
the data file read by scripts/cinematics/finale/finale_montage.gd.  Deterministic (seeds from crc32 of
names), original procedural pixel art; see documentation/asset_manifest_parts/trans_finale.md.

Timeline (seconds, 47.5 s):
   0.0  b_wide    Berlin, night.  Konrad at the drafting table, dome and snow in the east window
   4.6  b_close   branch m1_choose (request: typing / evidence: copy into the coat lining)
  12.6  b_window  snow against the glass, the floodlit dome ... the snow thickens (veil)
  14.3  k_window  ... and becomes the snow over the Karsk yard (dithered dissolve)
  16.2  k_wide    the signal box: Alexei at the desk, facing west
  20.4  k_close   branch a1_choose (share: Irina's note / keep: ledger locked away)
  28.4  rhyme     same framing, mirrored: Berlin desk / Karsk desk / both halves side by side
  33.6  map       both lamps over one border map; C-17 draws itself from Karsk west to Berlin;
                  the Karsk lamp goes out, then the Berlin lamp; the red line is the last light
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_finale_kit as kit          # noqa: E402
import cine_finale_berlin as b         # noqa: E402
import cine_finale_berlin_anim as ba   # noqa: E402
import cine_finale_karsk as k          # noqa: E402
import cine_finale_karsk_anim as ka    # noqa: E402
import cine_finale_figure as fig       # noqa: E402
import pg                              # noqa: E402

OUT = kit.OUT
HOME = [b.OX, b.OY]

# ------------------------------------------------------------------------------------------- timeline
T = {
    'b_wide': (0.0, 4.6),
    'b_close': (4.6, 12.6),
    'b_window': (12.6, 14.9),
    'veil': (13.95, 15.25),
    'k_window': (14.35, 16.6),
    'k_wide': (16.2, 20.4),
    'k_close': (20.4, 28.4),
    'r1_b': (28.4, 29.6),
    'r2_k': (29.6, 30.8),
    'r3_b': (30.8, 31.6),
    'r4_k': (31.6, 32.4),
    'split': (32.4, 34.4),
    'map': (33.6, 47.5),
}
DURATION = 47.5
# split screen: Konrad's head (x 272 request / 236 evidence) around the middle of the left half (view x 160),
# Alexei's (x 360) in the middle of the right half (view x 480)
SPLIT_SHIFT_B = -70
SPLIT_SHIFT_K = 140


def rel(path: str) -> str:
    return os.path.relpath(path, OUT).replace('\\', '/')


def save(arr: np.ndarray, name: str) -> str:
    path = os.path.join(OUT, name)
    kit.save_rgba(arr, path)
    return name


def shift_keys(nodes: list, dt: float) -> list:
    for n in nodes:
        if 'keys' in n:
            n['keys'] = [[round(kk[0] + dt, 3)] + list(kk[1:]) for kk in n['keys']]
        if 'pos_keys' in n:
            n['pos_keys'] = [[round(kk[0] + dt, 3)] + list(kk[1:]) for kk in n['pos_keys']]
    return nodes


def loop_node(nid: str, atlas_rel: str, rects: list, frames: list, fps: float, z: int, t0: float = 0.0) -> dict:
    return {'id': nid, 'type': 'anim', 'atlas': atlas_rel, 'frames': rects, 'z': z,
            'loop': {'fps': fps, 'seq': frames, 't0': t0}}


# ------------------------------------------------------------------------------------------- sets
def build_b_close(ext_b) -> dict:
    t0 = T['b_close'][0]
    base = b.b_close_base(ext_b)
    nodes = []
    nodes.append({'id': 'ext', 'type': 'sprite', 'file': save(b.ext_layer(ext_b, b.EXT_OFF_CLOSE), 'b_close/ext.png'),
                  'z': 0, 'parallax': 0.55})
    x0, y0, x1, y1 = b.WIN_B
    nodes.append({'id': 'snow', 'type': 'snow', 'rect': [x0 - 30, 0, x1 - x0 + 60, y1 + 4], 'count': 130,
                  'seed': kit.seed_of('b_close_snow'), 'speed': [10, 22], 'sway': 3, 'wind': -4, 'near': 0.35,
                  'colors': ['#8F8A92', '#D2CCCB'], 'z': 1, 'parallax': 0.8})
    nodes.append({'id': 'base', 'type': 'sprite', 'file': save(base['base'], 'b_close/base.png'), 'z': 2})
    nodes.append({'id': 'glass', 'type': 'sprite', 'file': save(base['glass'], 'b_close/glass.png'), 'z': 3})
    save(b.stamp_overlay(base['plan_q'], b.LAMP_B, False), 'b_close/stamp.png')
    save(b.stamp_overlay(base['plan_q'], b.LAMP_B, True), 'b_close/stamp_hist.png')
    nodes.append({'id': 'stamp', 'type': 'sprite', 'file': 'b_close/stamp.png', 'hist': 'b_close/stamp_hist.png', 'z': 4})
    # carriage (static in the evidence branch) and the copy lying on the plan (request branch)
    nodes.append({'id': 'carriage_static', 'type': 'sprite', 'file': save(b.carriage(b.W, b.H, b.LAMP_B), 'b_close/carriage_static.png'),
                  'z': 13, 'when': {'m1_choose': 'preserve_evidence'}})
    nodes.append({'id': 'copy_static', 'type': 'sprite', 'file': save(b.copy_sheet(b.LAMP_B, ba.COPY_Q0, 'flat'), 'b_close/copy_static.png'),
                  'z': 11, 'when': {'m1_choose': 'request_explanation'}})
    # cigarette smoke (loop)
    at = kit.Atlas('b_smoke')
    tip = base['tip']
    fr = ka.wisp_frames(at, (tip[0], tip[1] - 1), 10, kit.BR['smoke'], b.LAMP_B, 'b_smoke', height=58, spread=4.0,
                        draft=-6.0, count=6, rmax=3.0, density=0.7, ribbon=True)
    nodes.append(loop_node('smoke', 'b_close/smoke.png', at.save(os.path.join(OUT, 'b_close/smoke.png')), fr, 7.0, 18))
    # steam over the coffee cup (thin, it has gone half cold)
    at = kit.Atlas('b_cup')
    cup = base['cup']
    fr = ka.wisp_frames(at, (cup[0], cup[1] - 2), 10, kit.BR['smoke'], b.LAMP_B, 'b_cup', height=30, spread=2.0,
                        draft=-3.0, count=5, rmax=2.5, density=0.55)
    nodes.append(loop_node('cup_steam', 'b_close/cup_steam.png', at.save(os.path.join(OUT, 'b_close/cup_steam.png')), fr, 6.0, 18))
    # lamp (on / off frames; the map reuses the same heads at the same screen position)
    at = kit.Atlas('b_lamp')
    on, _ = b.lamp_architect(b.W, b.H, b.V(112, 70), True)
    off, _ = b.lamp_architect(b.W, b.H, b.V(112, 70), False)
    lf = [at.add(on), at.add(off)]
    lrects = at.save(os.path.join(OUT, 'b_close/lamp.png'))
    nodes.append({'id': 'lamp', 'type': 'anim', 'atlas': 'b_close/lamp.png', 'frames': lrects, 'z': 30,
                  'keys': [[0.0, lf[0]]]})
    # branches
    req = shift_keys(ba.branch_request(OUT), t0)
    ev = shift_keys(ba.branch_evidence(OUT), t0)
    nodes += req + ev
    # rhyme: the right hand taps once (index lifts) in its final pose
    add_tap(nodes, 'b_arm_r', T['r1_b'][0] + 0.45, 'b_close')
    return {'nodes': nodes, 'flicker': {'amp': 0.012, 'dips': [[t0 + 4.9, 0.10, 0.18], [t0 + 5.15, 0.06, 0.12],
                                                               [T['r1_b'][0] + 0.2, 0.05, 0.12]]}}


def build_k_close(ext_k) -> dict:
    t0 = T['k_close'][0]
    base = k.k_close_base(ext_k)
    nodes = []
    nodes.append({'id': 'ext', 'type': 'sprite', 'file': save(b.ext_layer(ext_k, k.EXT_OFF_CLOSE), 'k_close/ext.png'),
                  'z': 0, 'parallax': 0.55})
    x0, y0, x1, y1 = k.WIN_K
    nodes.append({'id': 'snow', 'type': 'snow', 'rect': [0, 0, x1 + 30, y1 + 4], 'count': 130,
                  'seed': kit.seed_of('k_close_snow'), 'speed': [10, 22], 'sway': 3, 'wind': 4, 'near': 0.35,
                  'colors': ['#7E8E8C', '#DEE5DC'], 'z': 1, 'parallax': 0.8})
    nodes.append({'id': 'base', 'type': 'sprite', 'file': save(base['base'], 'k_close/base.png'), 'z': 2})
    nodes.append({'id': 'glass', 'type': 'sprite', 'file': save(base['glass'], 'k_close/glass.png'), 'z': 3})
    save(k.plaque(False, k.LAMP_K), 'k_close/plaque.png')
    save(k.plaque(True, k.LAMP_K), 'k_close/plaque_hist.png')
    nodes.append({'id': 'plaque', 'type': 'sprite', 'file': 'k_close/plaque.png', 'hist': 'k_close/plaque_hist.png', 'z': 4})
    led = k.ledger_layer()
    nodes.append({'id': 'ledger_static', 'type': 'sprite', 'file': save(led, 'k_close/ledger.png'), 'z': 11,
                  'when': {'a1_choose': 'share_with_irina'}})
    save(k.ledger_stamp(False, k.LAMP_K), 'k_close/stamp.png')
    save(k.ledger_stamp(True, k.LAMP_K), 'k_close/stamp_hist.png')
    nodes.append({'id': 'stamp_a', 'type': 'sprite', 'file': 'k_close/stamp.png', 'hist': 'k_close/stamp_hist.png', 'z': 11,
                  'when': {'a1_choose': 'share_with_irina'}})
    nodes.append({'id': 'stamp_b', 'type': 'sprite', 'file': 'k_close/stamp.png', 'hist': 'k_close/stamp_hist.png', 'z': 11,
                  'when': {'a1_choose': 'keep_private'}, 'vis': [[0.0, 1], [t0 + ka.T_TURN[0] + 0.07, 0]]})
    # tea steam (two loops: still air / draught while the door is open in the share branch)
    at = kit.Atlas('k_steam')
    still = ka.wisp_frames(at, (k.GLASS_C[0], k.GLASS_C[1] - 9), 10, kit.KR['steam'], k.LAMP_K, 'k_steam', height=54,
                           spread=3.0, count=8, rmax=5.0, density=0.95)
    draft = ka.wisp_frames(at, (k.GLASS_C[0], k.GLASS_C[1] - 9), 10, kit.KR['steam'], k.LAMP_K, 'k_steam_d', height=40,
                           spread=2.0, draft=-34.0, count=8, rmax=4.5, density=0.9)
    rects = at.save(os.path.join(OUT, 'k_close/steam.png'))
    nodes.append(dict(loop_node('steam', 'k_close/steam.png', rects, still, 7.0, 18), when={'a1_choose': 'keep_private'}))
    # share branch: still -> draught -> still, expressed as explicit keys over the loop
    keys = []
    tt = 0.0
    i = 0
    while tt < DURATION:
        in_draft = (t0 + 1.6) <= tt < (t0 + 5.4)
        seq = draft if in_draft else still
        keys.append([round(tt, 3), seq[i % len(seq)]])
        tt += 1.0 / 7.0
        i += 1
    nodes.append({'id': 'steam_share', 'type': 'anim', 'atlas': 'k_close/steam.png', 'frames': rects, 'z': 18,
                  'keys': keys, 'when': {'a1_choose': 'share_with_irina'}})
    at = kit.Atlas('k_lamp')
    on, _ = k.lamp_enamel(b.W, b.H, b.V(528, 70), True)
    off, _ = k.lamp_enamel(b.W, b.H, b.V(528, 70), False)
    lf = [at.add(on), at.add(off)]
    lrects = at.save(os.path.join(OUT, 'k_close/lamp.png'))
    nodes.append({'id': 'lamp', 'type': 'anim', 'atlas': 'k_close/lamp.png', 'frames': lrects, 'z': 30,
                  'keys': [[0.0, lf[0]]]})
    static = b.composite([(base['base'], 0, 0), (led, 0, 0), (k.ledger_stamp(True, k.LAMP_K), 0, 0)])
    share = shift_keys(ka.branch_share(OUT, static), t0)
    keep = shift_keys(ka.branch_keep(OUT), t0)
    nodes += share + keep
    add_tap(nodes, 'k_arm_r', T['r2_k'][0] + 0.45, 'k_close')
    add_tap(nodes, 'k_arm_l', T['r2_k'][0] + 0.45, 'k_close')
    return {'nodes': nodes, 'flicker': {'amp': 0.012, 'dips': [[t0 + 0.75, 0.06, 0.12], [T['r2_k'][0] + 0.2, 0.05, 0.12]]}}


TAP_CACHE = {}


def add_tap(nodes: list, arm_id: str, t_tap: float, set_dir: str, only_if_missing=None):
    """Rhyme beat: every branch version of arm_id lifts its index finger once (0.22 s) at t_tap, in sync
    with the clock tick (Berlin) / the telegraph click (Karsk).  The tap frame is rendered from the arm's
    final pose (kit.render_tap) and appended to its atlas."""
    for n in nodes:
        if n.get('id') != arm_id or n.get('type') != 'anim' or '_atlas' not in n:
            continue
        last = n['keys'][-1][1]
        if last < 0:
            continue
        if '_rig' in n:
            f = fig.render_tap(n['_rig'], n['_side'], n['_atlas'], extra=n.get('_extra'))
        else:
            f = kit.render_tap(n['_atlas'])
        if f < 0:
            continue
        n['frames'] = n['_atlas'].save(n['_path'])
        n['keys'].append([round(t_tap, 3), f])
        n['keys'].append([round(t_tap + 0.22, 3), last])


def strip_private(obj):
    if isinstance(obj, dict):
        return {k_: strip_private(v) for k_, v in obj.items() if not str(k_).startswith('_')}
    if isinstance(obj, list):
        return [strip_private(v) for v in obj]
    return obj


# ------------------------------------------------------------------------------------------- assemble
def main(preview_dir=None):
    t_start = time.time()
    os.makedirs(OUT, exist_ok=True)
    for d in ('b_close', 'k_close', 'b_wide', 'k_wide', 'b_window', 'k_window', 'map'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    ext_b = b.exterior()
    ext_k = k.exterior()
    sets = {}
    sets['b_close'] = build_b_close(ext_b)
    print('b_close', round(time.time() - t_start, 1))
    sets['k_close'] = build_k_close(ext_k)
    print('k_close', round(time.time() - t_start, 1))
    extra_sets, extra_shots, extra_events = build_rest(ext_b, ext_k)
    sets.update(extra_sets)
    shots = make_shots()
    events = make_events()
    data = {'version': 1, 'duration': DURATION, 'view': [640, 360], 'set_size': [b.W, b.H], 'home': HOME,
            'sets': sets, 'shots': sorted(shots + extra_shots, key=lambda x: x['t0']),
            'events': sorted(events + extra_events, key=lambda e: e['t'])}
    with open(os.path.join(OUT, 'finale.json'), 'w', encoding='utf-8') as f:
        json.dump(strip_private(data), f, ensure_ascii=False, separators=(',', ':'))
    print('finale.json', round(time.time() - t_start, 1), 's')


def cam(t0, t1, a, bxy):
    return [[t0, a[0], a[1]], [t1, bxy[0], bxy[1]]]


def make_shots() -> list:
    sh = []
    t0, t1 = T['b_close']
    sh.append({'set': 'b_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (20, 12), (26, 9)),
               'when': {'m1_choose': 'preserve_evidence'}})
    # request: the camera tilts up with his hand to the sheet in the platen, follows the sheet down into the
    # AUSGANG tray (the reach is framed on forearm, hand and sheet, not on an upright arm)
    sh.append({'set': 'b_close', 't0': t0, 't1': t1, 'home': HOME, 'when': {'m1_choose': 'request_explanation'},
               'cam': [[t0, 20, 12], [t0 + ba.T_REACH[0] - 0.1, 23, 10], [t0 + ba.T_REACH[1], 25, -22],
                       [t0 + ba.T_SWING[1], 26, -14], [t0 + ba.T_CARRY[1], 27, 6], [t1, 26, 9]]})
    t0, t1 = T['k_close']
    sh.append({'set': 'k_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (20, 12), (14, 9)),
               'when': {'a1_choose': 'share_with_irina'}})
    # keep_private: the camera tilts down with Alexei's hand to the wide-open pedestal drawer and back up
    sh.append({'set': 'k_close', 't0': t0, 't1': t1, 'home': HOME, 'when': {'a1_choose': 'keep_private'},
               'cam': [[t0, 20, 12], [t0 + 2.2, 19, 12], [t0 + 3.1, 18, 66], [t0 + 5.3, 17, 66], [t0 + 6.4, 15, 14],
                       [t1, 14, 9]]})
    t0, t1 = T['r1_b']
    sh.append({'set': 'b_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (24, 10), (25, 10))})
    t0, t1 = T['r2_k']
    sh.append({'set': 'k_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (16, 10), (15, 10))})
    t0, t1 = T['split']
    # each half is framed on its sitter (the set is shifted inside its fixed half): Konrad and Alexei both sit
    # in the middle of their half, heads clear of the divider
    sh.append({'set': 'b_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (20, 10), (20, 10)),
               'clip': [0, 0, 319, 360], 'shift': [SPLIT_SHIFT_B, 0]})
    sh.append({'set': 'k_close', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (20, 10), (20, 10)),
               'clip': [321, 0, 319, 360], 'shift': [SPLIT_SHIFT_K, 0]})
    return sh


def make_events() -> list:
    return []


def build_rest(ext_b, ext_k):
    """Wide shots, window inserts and the map (cine_finale_build_rest).  Returns (sets, shots, events)."""
    try:
        import cine_finale_rest as rest
    except ImportError:
        return {}, [], []
    return rest.build(ext_b, ext_k, T, DURATION, OUT, HOME)


if __name__ == '__main__':
    main()
