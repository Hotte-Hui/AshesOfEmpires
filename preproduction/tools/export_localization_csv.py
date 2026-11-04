#!/usr/bin/env python3
"""Export human-reviewable string table CSV. Unreal DataTable import still needs matching struct."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
loc=json.loads((ROOT/'data/v3/locale_de.json').read_text(encoding='utf-8'))['strings']
dest=ROOT/'exports'/'localization_de.csv';dest.parent.mkdir(exist_ok=True)
with dest.open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.writer(f);writer.writerow(['Key','SourceString'])
    for key,text in sorted(loc.items()):writer.writerow([key,text])
print('Wrote',dest.relative_to(ROOT),len(loc),'strings')
