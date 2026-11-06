# Asset manifest — dialogue portraits, round 7 (seventeen individual faces, Chapter-3 portraits alive)

Area owner: characters specialist · Date: **2026-11-06, round 7** · Engine target: Godot 4.7.2
Extends `portraits.md` (round 2; pipeline, file formats and runtime unchanged).

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** (numpy + Pillow; no AI image models, no network, no image inputs).
  Facial features are hand-designed pixel stamps / parametric strokes in the generator source.
* Licence: project-owned original asset. No regime insignia in any portrait (the officer's cap badge is the Free
  City's bridge, the conductor's the railway's winged wheel).
* Deterministic: verified 2026-11-06 (elena, babushka, porter rebuilt into a scratch directory: byte-identical).

## Reproduce
```bash
py -3 -P tools/pixelgen/chargen_portrait2.py --jobs=9          # all 17 speakers, one process each (~2.5 min)
py -3 -P tools/pixelgen/chargen_portrait2.py elena kessler     # some speakers
py -3 -P tools/pixelgen/chargen_portrait2.py --out=DIR         # review run into another assets/characters dir
```

## What changed
| Item | Before | Now |
|---|---|---|
| Chapter-3 portraits (elena, border_officer, conductor, voronova, kessler, typist, journalist) | first-generation ellipsoid busts from a module that no longer imported; static strips, no talking mouth, no blink; a flatter, different look | `chargen_portrait_c3.py` registers the seven in `chargen_portrait2_cast.CAST`: same SDF pipeline as the rest, 4 expressions x 6 states (`portrait_anim.png` + anim block), backgrounds `veltrava` (slate dawn) and `palais` (navy-teal) |
| Faces | every speaker on the same sculpted base: same nose, chin, eye stamps and brow stroke | per speaker: head proportions and 3/4 angle, nose (length, projection, width, bump / hook / button / drooping tip), chin and jaw (pointed, square, receding, cleft, double), eye shapes (`chargen_portrait2_face.eye_shapes`: hooded / narrow / round / droop / lift / deep), brow geometry (`features['brow_pts']`, thickness, arch), nostril style; softer planes for the women (`SOFT`) |
| Babushka | headscarf wrapped like a hood over forehead, ears and cheeks | `kerchief_chin`: front edge at the hairline with a plain rolled hem, open face framed down the cheeks to a knot with two tails under the chin, back corner over the nape |
| Peaked caps (porter, officer, conductor) | the head clip reached 1.4 px above the crown -> hair showed through the cap top as a pale patch | clip ends at the crown top |
| Porter | no moustache (his sprite has one) | white moustache, hooded eyes, bushy white brows |

Speaker notes (face, in one line each): **Alexei** broad Slavic face, high cheekbones, once-broken nose, tired
hooded eyes, heavy low brows · **Konrad** narrow long face, long straight nose, defined chin, fine brows, more in
profile · **Irina** shorter rounder face, short slightly upturned nose, strong straight brows, wide eyes · **Emil**
bulbous nose, jowls, kind drooping hooded eyes, bushy grey brows · **Vendor** broad round face, button nose, soft
double chin, crinkled warm eyes, a ready smile · **Worker** flat broad nose, squint, heavy low brows ·
**Babushka** long thin nose with a drooping tip, small pointed chin, deep-set kind eyes · **Librarian** thin long
nose, narrow chin, hooded reading eyes, fine high brows · **Porter** fleshy, white moustache · **Photographer**
hooked nose, wry squint · **Elena** slim oval face, fine nose, small chin, lifted eyes, fine arched brows ·
**Officer** broad jowly face, short wide nose, hooded narrow eyes, trimmed dark moustache · **Conductor** long
gaunt face, drooping nose, receding chin under a walrus moustache, droopy eyes · **Voronova** broad face, square
jaw, short broad nose, level brows, steady hooded eyes, grey waves under the karakul · **Kessler** narrow ascetic
face, aquiline nose, pointed chin, thin lips, narrow eyes behind thin rimless glasses · **Frau Brunner** round
face, upturned small nose, round eyes, raised arched brows, a smile · **Ekdahl** long Nordic face, strong straight
nose, cleft chin, almost invisible fair brows.

## Generator scripts (round 7)
| File | Change |
|---|---|
| `tools/pixelgen/chargen_portrait_c3.py` | rewritten: the seven Chapter-3 specs + builders (homburg, karakul pirozhok, swept hair with chignon, perm curls, tousled hair, karakul collar, temple wave) and passes (curls, cap badge, armband, pencil behind the ear, cheek hollows, chin cleft) |
| `tools/pixelgen/chargen_portrait2.py` | imports chargen_portrait_c3; `brow_pts` / `nostril` features; `set_out` / `--out`; `--jobs` (one process per speaker) |
| `tools/pixelgen/chargen_portrait2_face.py` | `eye_shapes(table, *kinds)` |
| `tools/pixelgen/chargen_portrait2_cast.py` | individual faces for the ten round-2 speakers, `kerchief_chin`, peaked-cap clip fix, porter moustache |
| `tools/pixelgen/chargen_portrait2_paint.py` | backgrounds `veltrava`, `palais` |
| `tools/pixelgen/chargen_portrait.py` | shim: the C3 module counts for the "up to date" check |

## Verification
`tests/visual/char_portraits.tscn` (real DialogueBox, all 17 speakers: animation grid in use, mouth moves while
typing and rests at the end, expression column follows the line; 102 screenshots, 0 failures);
`tests/test_characters_r7.gd` (portrait.json contract + anim block, grid size, talk / blink rows differ from rest).
