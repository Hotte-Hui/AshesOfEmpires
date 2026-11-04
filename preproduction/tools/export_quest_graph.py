#!/usr/bin/env python3
"""Produce Graphviz DOT for offline review; Graphviz itself not required."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
q=json.loads((ROOT/'data/v3/quests.json').read_text(encoding='utf-8'))
lines=['digraph AshesQuest {','  rankdir=LR;','  node [shape=box,fontname="Arial"];']
for quest in q['quests']:
    lines.append('  subgraph cluster_'+quest['id']+' {')
    lines.append('    label="'+quest['id']+'";')
    for o in quest['objectives']:
        lines.append('    "'+o['id']+'";')
        for dep in o.get('requires',[]):lines.append('    "'+dep+'" -> "'+o['id']+'";')
    lines.append('  }')
lines.append('  "a1_choose" -> "m1_inspect_plan_a" [style=dashed,label="a1_completed"];')
lines.append('  "a1_choose" -> "m1_inspect_plan_b" [style=dashed];')
lines.append('}')
dest=ROOT/'exports/quest_graph.dot';dest.parent.mkdir(exist_ok=True)
dest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Wrote',dest.relative_to(ROOT))
