#!/usr/bin/env python3
"""Validate Ashes of Empires v3 authored design JSON. Python 3.10+ stdlib only."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'v3'
FILES = ['flags', 'quests', 'items', 'scenes', 'dialogue', 'puzzles', 'cinematics', 'locale_de', 'reference_manifest']


def load_data():
    return {stem: json.loads((DATA / (stem + '.json')).read_text(encoding='utf-8')) for stem in FILES}


def ensure(test, message):
    if not test:
        raise ValueError(message)


def unique(records, what):
    ids = [r['id'] for r in records]
    ensure(len(ids) == len(set(ids)), f'Duplicate IDs in {what}: {ids}')
    return set(ids)


def check_dag(records, label):
    ids = unique(records, label)
    deps = {r['id']: r.get('requires', []) for r in records}
    for key, needs in deps.items():
        ensure(set(needs) <= ids, f'{key}: unknown prerequisites')
        ensure(key not in needs, f'{key}: self dependency')
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            raise ValueError(f'{label}: cycle at {node}')
        if node in visited:
            return
        visiting.add(node)
        for need in deps[node]:
            visit(need)
        visiting.remove(node)
        visited.add(node)
    for key in ids:
        visit(key)


def validate(data=None):
    d = data or load_data()
    for n in FILES:
        ensure(d[n].get('schema_version') == 3, f'{n}: schema_version must be 3')
    ensure(d['flags']['save_version'] == 2, 'save_version should be 2')
    flag_defs = d['flags']['flags']
    for name, f in flag_defs.items():
        ensure(f['type'] in ('integer', 'boolean'), f'{name}: unsupported flag type')
        if f['type'] == 'integer':
            ensure(type(f['default']) is int, f'{name}: invalid integer default')
            ensure(type(f.get('min')) is int and type(f.get('max')) is int, f'{name}: bounds must be int')
            ensure(f['min'] <= f['default'] <= f['max'], f'{name}: default outside bounds')
        else:
            ensure(type(f['default']) is bool, f'{name}: invalid boolean default')

    loc = d['locale_de']['strings']
    def localized(key):
        ensure(key in loc and isinstance(loc[key], str) and loc[key].strip(), f'Missing German text: {key}')

    scenes = d['scenes']['scenes']; sceneids = unique(scenes, 'scenes')
    ensure(d['scenes']['start_scene'] in sceneids, 'start scene missing')
    events = d['flags']['events']
    ensure(len(events) == len(set(events)), 'duplicate events')
    eventids = set(events)
    items = d['items']['items']; itemids = unique(items, 'items')
    for item in items:
        ensure(item['scene'] in sceneids, f'Item {item["id"]}: unknown scene')
        localized(item['name_key']); localized(item['description_key'])
    puzzles = d['puzzles']['puzzles']; puzzleids = unique(puzzles, 'puzzles')
    for p in puzzles:
        ensure(p['scene'] in sceneids, f'Puzzle {p["id"]}: unknown scene')
        ensure(set(p['clue_item_ids']) <= itemids, f'Puzzle {p["id"]}: unknown clue')
        ensure(p['retry_unlimited'] and p['hint_after_attempts'] >= 0, f'Puzzle {p["id"]}: accessibility config')
        ensure(bool(p['solution']), f'Puzzle {p["id"]}: missing solution')

    dialogues = d['dialogue']['conversations']; dialogueids = unique(dialogues, 'dialogues')
    for dialog in dialogues:
        nodes = dialog['nodes']; nodeids = unique(nodes, dialog['id'])
        ensure(dialog['entry_node'] in nodeids, f'{dialog["id"]}: entry missing')
        edges = {}
        for node in nodes:
            localized(node['text_key'])
            edge = [node['next']] if 'next' in node else []
            edges[node['id']] = edge
            ensure(bool(node.get('end')) != bool(edge), f'{node["id"]}: must end or go to next')
            ensure(set(edge) <= nodeids, f'{node["id"]}: dangling link')
        seen = set(); stack = [dialog['entry_node']]
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node); stack.extend(edges[node])
        ensure(seen == nodeids, f'{dialog["id"]}: unreachable nodes: {nodeids-seen}')
        ensure(any(node.get('end') for node in nodes), f'{dialog["id"]}: no endpoint')

    def effects_valid(effects, context):
        for name, effect in effects.items():
            ensure(name in flag_defs, f'{context}: unknown flag {name}')
            kind = flag_defs[name]['type']
            ensure(isinstance(effect, dict), f'{context}: malformed effect')
            if kind == 'integer':
                ensure(set(effect) == {'delta'} and type(effect['delta']) is int, f'{context}: integer requires delta')
            else:
                ensure(set(effect) == {'set'} and type(effect['set']) is bool, f'{context}: boolean requires set')

    quests = d['quests']['quests']; questids = unique(quests, 'quests')
    completed_events = set()
    allobjectives = set()
    for q in quests:
        ensure(q['scene'] in sceneids, f'{q["id"]}: missing scene')
        ensure(q['character'] in ('alexei','matthias'), f'{q["id"]}: unknown character')
        localized(q['title_key'])
        ensure(q['completion_event'] in eventids, f'{q["id"]}: completion event missing')
        ensure(q['completion_event'] not in completed_events, 'duplicate completion event')
        completed_events.add(q['completion_event'])
        objectives = q['objectives']; check_dag(objectives, q['id'])
        for obj in objectives:
            ensure(obj['id'] not in allobjectives, f'Duplicate global objective: {obj["id"]}')
            allobjectives.add(obj['id']); localized(obj['text_key'])
            ensure(obj['type'] in ('inspect','dialogue','puzzle','choice'), f'{obj["id"]}: invalid type')
            if 'grant_item' in obj:
                ensure(obj['grant_item'] in itemids, f'{obj["id"]}: item missing')
            if 'effects' in obj:
                effects_valid(obj['effects'], obj['id'])
            if obj['type'] == 'dialogue':
                ensure(obj.get('dialogue_id') in dialogueids, f'{obj["id"]}: dialogue missing')
            if obj['type'] == 'puzzle':
                ensure(obj.get('puzzle_id') in puzzleids, f'{obj["id"]}: puzzle missing')
            if obj['type'] == 'choice':
                choices = obj.get('choices', [])
                ensure(len(choices) >= 2, f'{obj["id"]}: fewer than 2 choices')
                unique(choices, obj['id'] + ' choices')
                for choice in choices:
                    localized(choice['text_key']); effects_valid(choice.get('effects', {}), choice['id'])
        ensure(q['completion_event'] not in q.get('requires_events', []), f'{q["id"]}: self gated')
    for q in quests:
        ensure(set(q.get('requires_events', [])) <= completed_events, f'{q["id"]}: unknown quest event gate')
    ensure(set(d['quests']['slice_end_requires']) <= completed_events, 'slice end events missing')
    for scene in scenes:
        localized(scene['title_key'])
        ensure(scene['protagonist'] in ('alexei', 'matthias', 'none'), f'{scene["id"]}: protagonist invalid')
        if scene['associated_quest'] is not None:
            ensure(scene['associated_quest'] in questids, f'{scene["id"]}: quest invalid')
        if scene['next_scene'] is not None:
            ensure(scene['next_scene'] in sceneids, f'{scene["id"]}: next scene invalid')
        ensure(scene['exit_on_event'] in eventids, f'{scene["id"]}: unknown exit event')
    sequences = d['cinematics']['sequences']; unique(sequences, 'cinematics')
    for seq in sequences:
        ensure(seq.get('trigger_event') in eventids or seq.get('trigger_objective') in allobjectives, f'{seq["id"]}: invalid trigger')
        unique(seq['shots'], seq['id'] + ' shots')
        for shot in seq['shots']:
            ensure(shot['duration_s'] > 0 and shot['shot'], f'{seq["id"]}: empty shot')
    for asset in d['reference_manifest']['assets']:
        ensure((ROOT / asset['path']).is_file(), f'Reference file missing: {asset["path"]}')
        ensure(asset['license_status'] == 'reference_only', f'Artwork rights status unreviewed: {asset["id"]}')
    return {'quests':len(quests),'objectives':len(allobjectives),'dialogs':len(dialogues),'items':len(items),'puzzles':len(puzzles),'scenes':len(scenes),'locale_strings':len(loc)}


if __name__ == '__main__':
    try:
        result = validate()
        print('PASS: v3 JSON validated:', ', '.join(f'{k}={v}' for k,v in result.items()))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print(f'FAIL: {e}', file=sys.stderr)
        sys.exit(1)
