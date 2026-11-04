#!/usr/bin/env python3
"""Produce production-friendly CSV manifests from a human-auditable source list."""
import csv
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ASSETS=[
('A001','L_A1_Railyard','ENV','Rail depot panorama', '3d+pixelpaint','P0','reference_02.jpeg','geometry, lighting, camera framing'),
('A002','L_A1_Railyard','ENV','Freight siding facade','modular3d','P0','reference_04.jpeg','large shadow grouping and haze'),
('A003','L_A1_Railyard','ENV','Freight wagon exterior','modular3d','P0','reference_03.jpeg','aged surface, readable silhouette'),
('A004','L_A1_Railyard','ENV','Depot office booth','2.5d','P0','reference_01.jpeg','windows and practical lamp'),
('A005','L_A1_Railyard','PROP','Damaged seal','sprite+inspectUI','P0','reference_03.jpeg','C-17 clue; no reference art reuse'),
('A006','L_A1_Railyard','PROP','Freight timetable','ui_document','P0','reference_03.jpeg','readable at 4K UI layer'),
('A007','L_A1_Railyard','PROP','Freight ledger','ui_document','P0','reference_01.jpeg','clear discrepancy in text'),
('A008','L_A1_Railyard','PUZZLE','Disconnected symbol board','sprite+ui','P0','reference_01.jpeg','fictional shapes, no rail signaling instructions'),
('A009','L_A1_Railyard','CHAR','Alexei hero','sprite_or_stylized3d','P0','reference_03.jpeg','5-direction idle/walk, inspect poses'),
('A010','L_A1_Railyard','CHAR','Irina dispatcher','sprite_or_stylized3d','P0','reference_01.jpeg','dialogue expressions and idle'),
('A011','L_A1_Railyard','FX','Factory exhaust haze','volumetric_or_sprites','P1','reference_02.jpeg','temporal stability benchmark'),
('A012','L_A1_Railyard','AUDIO','Depot environmental bed','original_audio','P1','reference_03.jpeg','no licensed recordings without provenance'),
('A013','L_M1_Archive','ENV','Berlin drafting archive','2.5d','P0','reference_01.jpeg','desk and soft overhead light'),
('A014','L_M1_Archive','ENV','Window onto fictional Great Hall','3d_silhouette','P0','reference_02.jpeg','institutional critical framing'),
('A015','L_M1_Archive','PROP','Plan A approved','ui_document','P0','reference_01.jpeg','distinct registration mark'),
('A016','L_M1_Archive','PROP','Plan B archived','ui_document','P0','reference_01.jpeg','alignment puzzle register'),
('A017','L_M1_Archive','PUZZLE','Architectural overlay tool','ui_canvas','P0','reference_01.jpeg','snap grid and free retry'),
('A018','L_M1_Archive','CHAR','Matthias hero','sprite_or_stylized3d','P0','reference_01.jpeg','humble technical dress, not uniform'),
('A019','L_M1_Archive','CHAR','Emil archivist','sprite_or_stylized3d','P0','reference_01.jpeg','dialogue poses and idle'),
('A020','L_M1_Archive','CHAR','Civilian silhouette group','silhouette','P1','reference_04.jpeg','foreground human-scale contrast'),
('A021','L_M1_Archive','PROP','Emil note','ui_document','P0','reference_03.jpeg','C-17 contract clarification'),
('A022','L_M1_Archive','FX','Sun shaft and haze','material_lighting','P1','reference_04.jpeg','no lighting flicker'),
('A023','GLOBAL','UI','Journal and inventory','umg','P0','reference_01.jpeg','display resolution; keyboard support'),
('A024','GLOBAL','UI','Dialogue text and choices','umg','P0','reference_01.jpeg','line-by-line, screenreader review'),
('A025','GLOBAL','TECH','Typed story state and saves','c++dataassets','P0','none','transactional validation and migration'),
('A026','GLOBAL','TECH','Quest trigger interaction','c++blueprints','P0','none','no public bypass'),
('A027','GLOBAL','CINEMATIC','C-17 match cut','sequencer','P0','reference_04.jpeg','skip-safe transition and protagonist swap'),
('A028','GLOBAL','CINEMATIC','Great Hall critical reveal','sequencer','P1','reference_02.jpeg','ordinary people foreground'),
('A029','GLOBAL','CINEMATIC','Final evidence montage','sequencer','P0','reference_03.jpeg','no repeat progress events'),
('A030','GLOBAL','QA','Two-scene render benchmark','test_assets','P0','none','screenshots and frame-time reports'),
]
PATH=ROOT/'assets'/'planned'/'asset_registry_v4.csv'
with PATH.open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.writer(h);w.writerow(('id','scene','category','description','implementation','priority','visual_reference','acceptance_criteria'));w.writerows(ASSETS)
refs=[]
for i,p in enumerate(sorted((ROOT/'references').glob('*.jpeg')),1):
 with Image.open(p) as src:
  im=src.convert('RGB'); sw=im.resize((200,200)).quantize(colors=10,method=Image.Quantize.MEDIANCUT).convert('RGB');count=sw.getcolors(40000) or []
  colors=sorted(count,reverse=True)[:10];pal=[{'hex':'#%02X%02X%02X'%rgb,'sampled_pixel_count':n} for n,rgb in colors]
  refs.append({'id':f'reference_{i:02d}','path':str(p.relative_to(ROOT)).replace('\\','/'),'width':im.width,'height':im.height,'palette_sampling_method':'200x200 median cut quantization (approximate, no human curation)','dominant_colors':pal})
(ROOT/'assets'/'planned'/'reference_palette_metrics_v4.json').write_text(json.dumps({'note':'Measured palette samples are diagnostic only; not a style license or final production palette.', 'references':refs},ensure_ascii=False,indent=2)+'\n','utf-8')
shots=[
('S001','A1','00:00','00:35','wide','Depot skyline; introduce civilian-scale rebuilding','A001','none'),
('S002','A1','00:35','01:10','tracking','Alexei arrives; steam and railcar silhouettes','A001 A009','skip to spawn'),
('S003','A1','01:10','03:10','medium','Irina handoff and relationship setup','A004 A010','complete dialogue 5 nodes'),
('S004','A1','03:10','05:50','insert','Siegel and timetable closeups','A005 A006','arbitrary order'),
('S005','A1','05:50','08:50','fixed','Fictional disconnected symbol board','A008','repeat/hint'),
('S006','A1','08:50','10:40','insert','Frachtbuch discrepancy','A007','C-17 clue'),
('S007','A1','10:40','12:10','face-to-face','Two choices with Irina','A010 A024','once-only effects'),
('S008','transition','12:10','12:20','match cut','C-17 stamp to Berlin handwritten note','A027','skip-safe'),
('S009','M1','12:20','13:40','side-on','Establish Matthias/office','A013 A018','scene spawn'),
('S010','M1','13:40','16:50','close','Plan overlay challenge','A015 A016 A017','repeat/hint'),
('S011','M1','16:50','17:05','exterior reveal','Fictional Great Hall + ordinary displaced people','A014 A020 A028','critical framing'),
('S012','M1','17:05','19:50','medium','Emil dialogue','A019 A024','complete dialogue 5 nodes'),
('S013','M1','19:50','21:20','close','Archive choice','A021 A024','once-only effects'),
('S014','finale','21:20','22:00','intercut','Two matched contract clues','A029','no premature meeting'),
('S015','finale','22:00','24:00','static','Journal epilogue and demo-complete','A023','safe resume and restart'),
]
with (ROOT/'production'/'shot_list_v4.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.writer(h);w.writerow(('shot_id','act','t_start','t_end','camera','on_screen_beat','asset_ids','gameplay_requirements'));w.writerows(shots)
print(f'Wrote {len(ASSETS)} asset rows, {len(shots)} shots and {len(refs)} measured reference palettes')
