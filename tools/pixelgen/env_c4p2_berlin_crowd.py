"""env_c4p2_berlin_crowd -- the people of the Corridor platform as ambient walkers (C4P2_DESIGN §4.2: travellers
with Corridor permits, a railway policeman, porters, a family with a grandmother boarding, the buffet woman).

Each figure is an anonymous colour variant of an EXISTING character, re-rendered through the character pipeline
(tools/pixelgen/walkers_r8.build_rig, imported read-only: same rows, frames and silhouette as the source, with its
own normal map and the appended front/back walk rows) -- full-quality people, never the twin of a speaking
character, no insignia (the railway policeman's armband and emblem are painted over in his coat colour).
Written to assets/environments/berlin_c4p2/crowd/ (this generator's own folder -- walkers/ stays walkers_r8's);
assets/environments/berlin_c4p2/walkers_a.json drives scripts/actors/ambient_walker.gd.  Who stands where follows
the platform's story: the policeman walks the buffet, the family with the sleeping boy waits by the buffet, a man
reads the departure board, two porters wait by their carts, the conductor and a family with the grandmother at
the sleeping car's door, the buffet woman behind her counter, two travellers walk the platform.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GREY_HAIR = ['#2E2E30', '#55575A', '#7C7E80', '#A2A3A2', '#C4C4BE', '#E0DFD8']
DARK_HAIR = ['#140E0C', '#2A1C16', '#3E2A20', '#563C2C', '#6E503A', '#88664A']
FAIR_HAIR = ['#3A2E1C', '#5E4C2E', '#82693E', '#A08A5A', '#BCA674', '#D6C494']
LANE = 295.5

# (name, source, material overrides, walker spec)
CROWD = [
    ('ost_police', 'guard', {
        'coat': '#2E3A3A', 'trouser': '#262E2E', 'hat': '#2E3A3A', 'band': '#3A4646', 'collar': '#3A4848',
        'armband': '#2E3A3A', 'emblem': '#2E3A3A', 'belt': '#16181A', 'metal': '#8A8F91', 'hair': DARK_HAIR},
     {'path': [[186, LANE], [262, LANE], [356, LANE]], 'speed': 13, 'start': 0.2, 'pauses': {'1': [2.0, 4.0]},
      'end_pause': [3.0, 6.0], 'pause_rows': ['look_side', 'idle_front'],
      'note': 'a railway policeman walks the buffet and watches the travellers (no insignia)'}),
    ('ost_attendant', 'vendor', {
        'coat': '#4A3E3E', 'skirt': '#2E2A2E', 'apron': '#D8CFB2', 'hat': '#E9DFC4', 'band': '#B3A98D',
        'hair': GREY_HAIR},
     {'path': [[256, 281.0], [286, 281.0]], 'speed': 7, 'start': 0.6, 'end_pause': [4.0, 9.0],
      'pause_rows': ['work_side', 'look_side', 'idle_front'],
      'note': 'the buffet woman behind her counter (feet hidden by the counter prop, base_y 292), pouring tea'}),
    ('ost_mother', 'berlin_mother', {
        'coat': '#8E6E4A', 'hat': '#5A2E2E', 'band': '#2A2A30', 'hair': '#2A2224', 'scarf': '#A8382E',
        'case': '#4E3E34'},
     {'path': [[210, LANE], [214, LANE]], 'speed': 5, 'start': 0.0, 'end_pause': [7.0, 14.0],
      'pause_rows': ['look_side', 'idle_front'],
      'note': 'exp_corridor_permit: the mother waits by her sleeping boy, the permits in cellophane'}),
    ('ost_father', 'berlin_father', {
        'coat': '#5E5A50', 'hat': '#2E2E34', 'band': '#1E1E22', 'scarf': '#5E3B24', 'hair': '#3A3230',
        'crate': '#5E4A3A'},
     {'path': [[188, LANE], [192, LANE]], 'speed': 5, 'start': 0.5, 'end_pause': [8.0, 15.0],
      'pause_rows': ['look_side', 'idle_front'], 'note': 'the father with the family\'s second case'}),
    ('ost_reader', 'clerk', {
        'coat': '#7A7870', 'sleeve': '#7A7870', 'protector': '#7A7870', 'trouser': '#3A3836', 'hair': GREY_HAIR,
        'tie': '#3A2A2A', 'hat': '#3A3834', 'band': '#16161A'},
     {'path': [[94, LANE], [100, LANE]], 'speed': 5, 'start': 0.3, 'end_pause': [6.0, 12.0],
      'pause_rows': ['look_side'], 'note': 'an older man reads the departure board twice'}),
    ('ost_porter_a', 'porter', {
        'coat': '#2A3346', 'hat': '#2A3346', 'band': '#7A2218', 'collar': '#1E2430', 'trouser': '#232838',
        'brass': ['#26282A', '#5E4A1E', '#8E6E2A', '#B49A58', '#D4BA72', '#EAD48E'], 'hair': DARK_HAIR},
     {'path': [[600, LANE], [606, LANE]], 'speed': 5, 'start': 0.0, 'end_pause': [5.0, 11.0],
      'pause_rows': ['work_side', 'look_side', 'idle_front'], 'note': 'exp_porters: a porter by his cart'}),
    ('ost_porter_b', 'worker_a', {
        'coat': '#56627C', 'trouser': '#2A2E38', 'hat': '#2A3346', 'band': '#8E6E2A', 'hair': GREY_HAIR,
        'boot': ('#1E1A18', {'texture': 'felt'}), 'mitten': '#4A3E32', 'patch': '#434E64', 'button': '#B49A58'},
     {'path': [[634, LANE], [638, LANE]], 'speed': 5, 'start': 0.7, 'end_pause': [6.0, 12.0],
      'pause_rows': ['work_side', 'look_side', 'idle_front'],
      'note': 'exp_porters: the older porter in his short blue work jacket and felt boots, the brass badge on his '
              'cap, waiting for a fare (another build than the young one in the long coat)'}),
    ('ost_conductor', 'conductor', {
        'coat': ('#1E2A44', {'bias': 0.04}), 'trouser': '#1A2236', 'hat': '#1E2A44', 'bag': '#2A1E14',
        'strap': '#2A1E14', 'hair': DARK_HAIR},
     {'path': [[810, LANE], [815, LANE]], 'speed': 5, 'start': 0.2, 'end_pause': [5.0, 10.0],
      'pause_rows': ['look_side', 'idle_front'], 'note': 'the sleeping-car conductor at his door'}),
    ('ost_grandmother', 'babushka', {
        'coat': '#3A3036', 'skirt': '#2E2A30', 'hat': '#8E7A9A', 'band': '#B3A98D', 'cloth': '#8A96A0',
        'fur': ('#4A3E36', {'texture': 'fur'}), 'hair': GREY_HAIR},
     {'path': [[828, LANE], [831, LANE]], 'speed': 4, 'start': 0.5, 'end_pause': [6.0, 12.0],
      'pause_rows': ['look_side', 'idle_front'],
      'note': 'the grandmother who is helped up into the sleeping car (once a year to Karsk)'}),
    ('ost_son', 'berlin_father', {
        'coat': '#6A4A3A', 'hat': '#3A3A40', 'band': '#1E1E22', 'scarf': '#7A2218', 'hair': '#2A2220',
        'crate': '#4E3E34'},
     {'path': [[856, LANE], [861, LANE]], 'speed': 5, 'start': 0.1, 'end_pause': [5.0, 9.0],
      'pause_rows': ['look_side', 'idle_front'], 'note': 'her son with the parcel for Karsk'}),
    ('ost_walker_a', 'clerk', {
        'coat': '#9A8A68', 'sleeve': '#9A8A68', 'protector': '#9A8A68', 'trouser': '#3E3A34', 'hair': DARK_HAIR,
        'tie': '#5A2A26', 'hat': '#4A4238', 'band': '#2A2A2E'},
     {'path': [[452, LANE], [828, LANE]], 'speed': 19, 'start': 0.35, 'end_pause': [2.0, 5.0],
      'pauses': {}, 'note': 'a traveller walks down the train looking for his car'}),
    ('ost_walker_b', 'berlin_mother', {
        'coat': '#2E5444', 'hat': '#6A2E36', 'band': '#16161A', 'hair': FAIR_HAIR, 'scarf': '#D8CFB2',
        'case': '#3E2A20'},
     {'path': [[124, LANE], [364, LANE]], 'speed': 16, 'start': 0.92, 'end_pause': [2.0, 4.0],
      'note': 'a woman with a small case walks to the buffet and back (starts at x 345, clear of Marta at 318)'}),
    ('ost_worker', 'worker_a', {
        'coat': '#3E4434', 'trouser': '#2E3228', 'hat': '#2E3228', 'band': '#1E2018', 'hair': DARK_HAIR},
     {'path': [[283, LANE], [288, LANE]], 'speed': 5, 'start': 0.4, 'end_pause': [7.0, 13.0],
      'pause_rows': ['look_side', 'idle_front'], 'note': 'a railway worker drinks his coffee at the counter'}),
]


def build(env_dir: str, gen: str, write: bool = True) -> tuple[list, dict]:
    """Writes crowd/<name>_rig.png / _rig_n.png / _rig.json; returns (produced rows, walkers json)."""
    import walkers_r8 as W
    W.CC3.install()
    produced = []
    walkers = []
    d = os.path.join(env_dir, 'crowd')
    os.makedirs(d, exist_ok=True)
    for (name, src, ov, spec) in CROWD:
        sheet, nsheet, meta = W.build_rig('berlin_c4p2', name, src, ov, write=False)
        meta['id'] = name
        if write:
            Image.fromarray(sheet, 'RGBA').save(os.path.join(d, name + '_rig.png'))
            Image.fromarray(nsheet, 'RGBA').save(os.path.join(d, name + '_rig_n.png'))
            with open(os.path.join(d, name + '_rig.json'), 'w', encoding='utf-8', newline='\n') as f:
                json.dump(meta, f, indent=1)
        rel = 'assets/environments/berlin_c4p2/crowd/' + name
        desc = 'ambient walker rig: %s (colour variant of %s through the character pipeline)' % (spec['note'], src)
        produced += [(rel + '_rig.png', gen, desc), (rel + '_rig_n.png', gen, desc + ' -- normal map'),
                     (rel + '_rig.json', gen, desc + ' -- sheet json')]
        w = {'id': name, 'char': src, 'rig': 'crowd/%s_rig.json' % name}
        w.update({k: v for k, v in spec.items() if k != 'note'})
        w.setdefault('give_way', 0)
        w['note'] = spec['note']
        walkers.append(w)
    data = {'doc': 'Ambient walkers of L_C4P2_BerlinA (Ostbahnhof, Korridorbahnsteig K): scripts/actors/ambient_walker.gd, '
                   'instanced by the scene.json actor res://scenes/actors/AmbientWalkers.tscn (scene_id L_C4P2_BerlinA). '
                   'Rigs in crowd/ from tools/pixelgen/env_c4p2_berlin_crowd.py (colour variants of existing characters, '
                   'same silhouettes, no insignia). Lane y 295.5 = in front of the platform furniture (base_y <= 294), '
                   'behind the walk band (>= 296): the player and the story NPCs are always drawn in front; the buffet '
                   'woman stands behind her counter (y 281 < the counter prop\'s base_y 292).',
            'walkers': walkers}
    return produced, data
