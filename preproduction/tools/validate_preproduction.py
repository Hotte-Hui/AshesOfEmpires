#!/usr/bin/env python3
"""Static preproduction data checks; no UE5 runtime required."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
q = json.loads((root/'data/quest_vertical_slice_v2.json').read_text(encoding='utf-8'))
s = json.loads((root/'data/story_flags_v2.json').read_text(encoding='utf-8'))
assert q['schema_version'] == 2 and s['schema_version'] == 2
flag_names = set(s['flags'])
quest_ids = [x['id'] for x in q['quests']]
assert len(quest_ids) == len(set(quest_ids))
all_events = {x['completion_event'] for x in q['quests']}
for quest in q['quests']:
    objectives = quest['objectives']
    ids = [o['id'] for o in objectives]
    assert len(ids) == len(set(ids)), quest['id']
    for obj in objectives:
        assert set(obj.get('requires', [])) <= set(ids), obj['id']
        for choice in obj.get('choices', []):
            assert set(choice.get('effects', {})) <= flag_names, choice['id']
    assert set(quest.get('requires_events', [])) <= all_events
assert set(q['slice_end_requires']) <= all_events
for key, meta in s['flags'].items():
    assert meta['type'] in ('integer', 'boolean'), key
    assert type(meta['default']) is (int if meta['type']=='integer' else bool), key
print('PASS: preproduction JSON consistency checks')
