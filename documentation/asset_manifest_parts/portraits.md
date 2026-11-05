# Asset manifest — dialogue portraits (round 2: living close-ups)

Area owner: chars-portraits specialist · Date: **2026-11-04** · Engine target: Godot 4.7.2

## Provenance & licence (applies to every file below)
* **Original work, generated procedurally** by the project's own Python scripts (numpy + Pillow; no AI image
  models, no network, no third-party art, no image inputs). Facial features (eyes, lids, brows, mouths,
  ears, wrinkles) are hand-designed pixel stamps / parametric pixel strokes written in the generator source.
* The reference images in `documentation/references/` were used **only** as internal lighting study
  (`user_ref_1`: navy body + single warm key). Nothing was traced, sampled, copied or embedded.
* Licence: project-owned original asset (same licence as the game's own content). No third-party attribution.
* Deterministic: re-running the generator reproduces identical PNGs (all noise / hashes are integer-seeded,
  never Python `hash()`).

## Reproduce
```bash
py -3 -P tools/pixelgen/chargen_portrait2.py                    # all 9 speakers + previews (~7 min)
py -3 -P tools/pixelgen/chargen_portrait2.py konrad irina       # selected speakers
py -3 -P tools/pixelgen/chargen_portrait2.py --preview konrad   # previews only, no asset writes
# characters.py still calls chargen_portrait.main(); that module is now a shim that forwards here and
# skips speakers whose files are newer than the generator sources (--force rebuilds).
```

## Generator scripts
| File | Role |
|---|---|
| `tools/pixelgen/chargen_portrait2.py` | entry point: scene assembly per speaker / expression / jaw state, render pipeline, PNG + JSON writer, previews |
| `tools/pixelgen/chargen_portrait2_sdf.py` | signed-distance sculpting nodes (ellipsoids, round cones, boxes, elliptic cylinders, smooth union / subtraction, warps, displacement, bounding) + orthographic sphere tracer (3×3 super-sampling, soft key shadow, occlusion) and material-majority downsampling |
| `tools/pixelgen/chargen_portrait2_anat.py` | parametric head after the planes of the head (cranium, forehead / mid-face blocks, cheekbones, malar pads, brow ridge, sockets + lids, nose bridge / tip / alae, muzzle, lips, rotatable jaw group, box chin, ears, neck), landmarks, torso |
| `tools/pixelgen/chargen_portrait2_paint.py` | key / fill / ambient / rim light model, per-material hue-shifted ramps, material-aware smoothing of the light field, posterisation, cluster cleanup, selective outline, depth-break lines, painted background |
| `tools/pixelgen/chargen_portrait2_face.py` | eye stamps (near / far eye × neutral, concerned, determined, surprised, closed), parametric brows and mouths (rest, half, open; teeth, tongue) on a tone-relative canvas |
| `tools/pixelgen/chargen_portrait2_cast.py` | hats (fedora, ushanka flaps down / up, peaked cap without insignia), headscarves (nape knot / chin knot, hem, clip volumes), hair (short, fringe, bun), garments (coats with lapels, quilting, roll-necks, scarves, shawl, apron, layered cardigan + shirt + tie, buttons, straps), texture passes (knit ribs, felt grain, fur tufts, stitches, hair strands, cloth folds, polka dots, printed scarf borders), stubble, wrinkles, eye bags, spectacles, pencils, gold tooth; the nine speaker specs |
| `tools/pixelgen/chargen_portrait.py` | compatibility shim (old entry point, forwards to chargen_portrait2) |

## Files — `assets/characters/<id>/`
| File | Format |
|---|---|
| `portrait.png` | 448×112 strip, 4 frames of 112×112 = the REST frames in `expressions` order (contract of TECHNICAL_ARCHITECTURE §4, unchanged) |
| `portrait_anim.png` | 448×672 grid: **column = expression index** (same order as `expressions`), **row = state**: 0 `rest`, 1 `talk_half`, 2 `talk_open`, 3 `blink`, 4 `blink_talk_half`, 5 `blink_talk_open` (row = mouth + 3 × eyes_closed) |
| `portrait.json` | `{"size": [112,112], "expressions": [...], "anim": {"file", "layout", "rows", "talk_rows", "blink_offset": 3, "mouth_fps": 11, "blink_ms": 130, "blink_interval_s": [2.6, 5.2], "generator"}}` — readers that only know `size` + `expressions` keep working |

All frames are opaque (painted, scene-tinted background), 1 texel = 1 logical pixel, shown ×3 (nearest).

| id | look (bust, 3/4 view facing right, warm key front-right, cool rim back-left) | background |
|---|---|---|
| `alexei` | fur ushanka with hanging ear flaps + tie strings, grey ribbed roll-neck, quilted green padded coat, satchel strap, stubble, tired eyes | Karsk teal |
| `konrad` | felt fedora (tapered crown, pinch, ribbon band, snap brim), short dark hair, knitted sand scarf tucked into the dark-blue overcoat, lapels, drafting-tube strap | Berlin violet |
| `irina` | madder-red headscarf knotted at the nape (rolled hem, gathered folds, ochre printed border, hanging corner), auburn hair at the edge, mustard roll-neck, quilted slate dispatcher jacket | Karsk teal |
| `emil` | bald crown with grey fringe, round wire spectacles with glare, grey moustache, jowls, forehead lines, grey archive coat over a brown cardigan, shirt + green tie, pencils in the breast pocket, stoop | archive navy |
| `vendor` | off-white kerchief with a blue printed border, blush, teal quilted jacket, brown roll-neck, white apron bib; a gold tooth when she talks | Karsk teal |
| `worker_a` | ushanka with flaps tied up, heavy stubble, weathered lines, olive telogreika, dark roll-neck | Karsk teal |
| `babushka` | navy polka-dot headscarf knotted under the chin, deep wrinkles, grey knitted shawl, dark coat | Karsk teal |
| `librarian` | grey-streaked hair in a bun, half-moon reading glasses on a chain, high cream collar, bottle-green ribbed cardigan | archive navy |
| `porter` | doorman's peaked cap (cloth band, glossy visor, brass cord — **no badge, no insignia**), heavy jowls, navy uniform coat with brass buttons, shirt + dark tie | Berlin violet |

No regime insignia appear in any portrait (portraits are player-facing UI chrome, see TECHNICAL_ARCHITECTURE
§12.4), so no `_hist` variants are needed.

## Runtime (scripts/ui/dialogue_box.gd)
The DialogueBox reads the `anim` block: while the typewriter types, the mouth row follows the last revealed
letter (vowels open, labials / spaces / punctuation closed, other letters half; at most `mouth_fps` changes per
second; reduced motion halves the rate and never opens fully), rests during punctuation pauses and at the end
of the line; the eyes blink every `blink_interval_s` (sometimes twice) for `blink_ms`; the expression column
stays fixed per line. Without an `anim` block the strip stays static; without a portrait the silhouette
placeholder is shown.

## Verification harness
`tests/visual/portrait_harness.tscn` shows the real DialogueBox for all nine speakers × 4 expressions (+ talk
and blink poses) over in-engine level captures and checks: animation grid in use, mouth changes while typing,
mouth rests in punctuation pauses and at the end of the line, expression column constant per line, blink
closes and re-opens the eyes, 112×112 regions, silhouette placeholder for speakers without portrait, static
strips stay static, dock_top / toast suppression, choice guard. Never writes saves or settings.
```bash
godot --path . res://tests/visual/portrait_harness.tscn -- --out=<dir> [--bg-karsk=<png>] [--bg-berlin=<png>] [--only=id,id]
godot --headless --path . res://tests/visual/portrait_harness.tscn -- --out=<dir>     # checks only
```

## Review images (not shipped; `_preview/` has `.gdignore`)
`assets/characters/_preview/portraits_v2_<id>_3x.png` (4 expressions × 6 states per speaker),
`portraits_compare_old_new_2x.png` (old strips left, new right), `portraits_all_rest_2x.png` (= refreshed
`portraits_all_2x.png`), `portraits_states_2x.png`, `portraits_dialogue_ingame_all.png` (in-engine DialogueBox
panels, 9 speakers × neutral / concerned / determined / surprised / talk / blink) and single in-engine captures
`portraits_dialogue_{konrad,alexei,vendor_talk,placeholder,docktop_emil}.png`. The older
`<id>_portraits_3x.png` files show the first-generation portraits and are obsolete.
