#!/usr/bin/env python3
"""Build one self-contained offline HTML story lab from v3 canonical authoring JSON."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEMS=['flags','quests','items','scenes','dialogue','puzzles','cinematics','locale_de']
payload={k:json.loads((ROOT/'data'/'v3'/f'{k}.json').read_text('utf-8')) for k in STEMS}
encoded=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
template=(ROOT/'preview'/'v4_template.html').read_text('utf-8')
assert template.count('/*__GAME_DATA__*/')==1
result=template.replace('/*__GAME_DATA__*/',encoded)
out=ROOT/'preview'/'ashes_story_lab_v0.4.html'
out.write_text(result,'utf-8')
print(f'Built {out.relative_to(ROOT)}: {len(result):,} chars / {len(payload)} data sets')
