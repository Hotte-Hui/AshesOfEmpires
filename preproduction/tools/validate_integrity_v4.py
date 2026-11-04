#!/usr/bin/env python3
"""Static second-line checks across canonical v3 data and generated production assets.

The canonical schema remains v3; v4 denotes the stronger toolchain, not a new
incompatible content format. Pure standard library, reproducible offline.
"""
from collections import defaultdict
from pathlib import Path
import csv
import json
try:
    from .validate_v3 import validate, load_data
except ImportError:
    from validate_v3 import validate, load_data

ROOT=Path(__file__).resolve().parents[1]


def require(test, msg):
    if not test: raise ValueError(msg)


def deep_validate(data=None, registry=None, shotlist=None):
    d=data if data is not None else load_data()
    validate(d)
    scenes={s['id']:s for s in d['scenes']['scenes']}
    quests={q['id']:q for q in d['quests']['quests']}
    items={i['id']:i for i in d['items']['items']}
    puzzles={p['id']:p for p in d['puzzles']['puzzles']}
    objectives={o['id']:o for q in quests.values() for o in q['objectives']}
    events={q['completion_event']:q['id'] for q in quests.values()}
    for scene in scenes.values():
        if scene['associated_quest'] is not None:
            q=quests[scene['associated_quest']]
            require(q['scene']==scene['id'],f'{scene["id"]}: quest scene mismatch')
            require(q['character']==scene['protagonist'], f'{scene["id"]}: quest protagonist mismatch')
            require(q['completion_event']==scene['exit_on_event'],f'{scene["id"]}: exit event mismatch')
            require(scene['next_scene'] in scenes, f'{scene["id"]}: missing next scene')
            require(scene['id']!=scene['next_scene'],f'{scene["id"]}: self scene loop')
        else:
            require(scene['protagonist']=='none' and scene['next_scene'] is None, 'Nonquest scene must be terminal montage')
    # All scene progression from start must reach the one terminal montage without loops.
    seen=[]; cur=d['scenes']['start_scene']
    while cur is not None:
        require(cur not in seen,'Scene graph cycle at '+cur)
        seen.append(cur);cur=scenes[cur]['next_scene']
    require(set(seen)==set(scenes),'Unreachable scene(s)')
    require(scenes[seen[-1]]['associated_quest'] is None,'Last scene must be montage')

    # Every quest-gating event has an emitting quest in an earlier scene.
    ix={s:i for i,s in enumerate(seen)}
    for q in quests.values():
        for event in q.get('requires_events', []):
            require(ix[quests[events[event]]['scene']]<ix[q['scene']],f'{q["id"]}: impossible event gate')
        for obj in q['objectives']:
            if obj.get('grant_item'):
                require(items[obj['grant_item']]['scene']==q['scene'],f'{obj["id"]}: item/quest scene mismatch')
            if obj['type']=='puzzle':
                p=puzzles[obj['puzzle_id']]
                require(p['scene']==q['scene'],f'{obj["id"]}: puzzle scene mismatch')
                # Inspect objective prereqs must actually give access to each clue.
                recursively=set()
                def visit(oid):
                    if oid in recursively:return
                    recursively.add(oid)
                    for need in objectives[oid].get('requires',[]): visit(need)
                for dep in obj.get('requires', []):visit(dep)
                available_items={objectives[i].get('grant_item') for i in recursively}
                require(set(p['clue_item_ids'])<=available_items,f'{obj["id"]}: inaccessible clue')
    for p in puzzles.values():
        if p['type']=='symbol_order':
            require(len(p['display_symbols'])==len(set(p['display_symbols'])),'Duplicate puzzle symbols')
            require(sorted(p['solution'])==sorted(p['display_symbols']), 'Puzzle display and solution differ')
        elif p['type']=='overlay_alignment':
            require(set(p['solution'])=={'rotation_steps','offset_x','offset_y'},'Overlay solution keys mismatch')
            require(all(type(v) is int for v in p['solution'].values()),'Overlay solution non-integer')
        else: raise ValueError('Unknown puzzle type: '+p['type'])
    for convo in d['dialogue']['conversations']:
        byid={n['id']:n for n in convo['nodes']}
        node=convo['entry_node']; visited=set()
        while True:
            require(node not in visited,f'{convo["id"]}: dialogue cycle')
            visited.add(node)
            if byid[node].get('end'):break
            node=byid[node]['next']
        require(visited==set(byid),f'{convo["id"]}: unused dialogue nodes')
    cinematic_ids=set()
    for s in d['cinematics']['sequences']:
        require(bool(s.get('trigger_event')) != bool(s.get('trigger_objective')),'Sequence needs exactly one trigger')
        cinematic_ids.add(s['id'])
        if 'trigger_event' in s:
            require(s['trigger_event'] in events,'Sequence event not emitted by a quest')
        if 'trigger_objective' in s:
            require(s['trigger_objective'] in objectives,'Sequence objective not present')
    require(cinematic_ids=={'LS_A1_ToM1','LS_M1_Hall','LS_X1_Final'},'Missing locked cinematic(s)')
    require(set(d['quests']['slice_end_requires'])==set(events),'Finale needs both quest events')

    if registry is None:
        with (ROOT/'assets'/'planned'/'asset_registry_v4.csv').open(encoding='utf-8-sig',newline='') as h:
            registry=list(csv.DictReader(h))
    if shotlist is None:
        with (ROOT/'production'/'shot_list_v4.csv').open(encoding='utf-8-sig',newline='') as h:
            shotlist=list(csv.DictReader(h))
    aids=[a['id'] for a in registry]
    require(len(set(aids))==len(aids),'Duplicate asset ID')
    for a in registry:
        require(a['scene'] in scenes or a['scene']=='GLOBAL','Unknown asset scene')
        require(a['priority'] in ('P0','P1','P2'),'Bad asset priority')
        require(a['visual_reference']=='none' or (ROOT/'references'/a['visual_reference']).is_file(),'Missing asset reference')
    ids=set(aids)
    require(len({s['shot_id'] for s in shotlist})==len(shotlist),'Duplicate shot ID')
    for shot in shotlist:
        require(set(shot['asset_ids'].split())<=ids,'Shot references missing assets')
        require(shot['t_start']<=shot['t_end'],'Nonmonotone shot timestamp')
    require(len(registry)>=25 and len(shotlist)>=12,'Insufficient production manifests')
    return dict(scenes=len(scenes),quests=len(quests),objectives=len(objectives),puzzles=len(puzzles),dialogues=len(d['dialogue']['conversations']),assets=len(registry),shots=len(shotlist),cinematics=len(cinematic_ids))


if __name__=='__main__':
    print('PASS deep cross-reference validation:',deep_validate())
