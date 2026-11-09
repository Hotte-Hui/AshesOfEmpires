# Asset manifest part — flashback (films of four real-history cards)

* **Date:** 2026-11-09 (round 13)
* **Area owner:** flashback stream
* **Contract:** `documentation/TECHNICAL_ARCHITECTURE.md` §12.15. Films `LS_FB_Nuremberg` (card
  `hist.reich.nuremberg_interpreters`), `LS_FB_Evictions` (`hist.reich.evictions`), `LS_FB_Settlement`
  (`hist.soviet.special_settlements`), `LS_FB_Kyshtym` (`hist.soviet.kyshtym`): 16–16.5 s, three painted shots each.
* **Provenance:** everything below is **original work** written by the project's own deterministic generators
  (fixed seeds; a re-run writes the same bytes). No downloads, no traced or sampled photographs or film frames, no AI
  image or audio models. The subjects are real events; the pictures are generic reconstructions that show only what
  the card states (places, rooms, documents, tools; people at a distance or from behind) — no faces, no uniforms, no
  flags, no insignia (no `*_hist` files, nothing for `Symbols.pick()`), no violence, no blast.
* **Scene / code:** `scenes/cinematics/flashback_common/flashback_film.gd` (+ four `Flashback<Name>.tscn`),
  `scripts/core/flashbacks.gd`, `scripts/ui/flashback_view.gd`, the button in `scripts/ui/discovery_view.gd`, three
  hooks in `scripts/core/game.gd` (`memory_films`, `_film_exists`, `rewatch_film`); sheet
  `data/flashbacks/flashbacks.json`; tests `tests/test_flashbacks.gd`, captures `tests/visual/flashback_shots.tscn`.

| Path | What | How it was made |
|---|---|---|
| `assets/cinematics/flashback/nuremberg/court.png` | the courtroom from the back rows: panelling, two draped windows, strip lights, the glazed, roofless booth with two rows of interpreters, listeners with headphones seen from behind (512 × 368; the film shows a 480 × 360 gate drifting across it) | `py -3 -P tools/pixelgen/env_flashback.py` (`env_flashback_reich.court`): one luminance painting resolved to the 13-step sepia ramp (`env_flashback_kit.resolve`: 4 × 4 ordered dither in the middle of a step, lens falloff, baked grain) |
| `assets/cinematics/flashback/nuremberg/booth.png` | three interpreters at their desk from behind (headphones, microphones, papers), the glass front with its one top rail, the room beyond | same (`booth`) |
| `assets/cinematics/flashback/nuremberg/desk.png` | headphones put down, the selector switch with four positions, the box with the two lamps (dark), typed sheets, a pencil | same (`desk`) |
| `assets/cinematics/flashback/nuremberg/desk_yellow.png`, `desk_red.png` | the two lamps lit (48 × 48, hard-edged, dithered halo): the only colours outside the ramp — a muted yellow and a muted red, because the card names them | same (`lamp_overlay`) |
| `assets/cinematics/flashback/evictions/street.png` | a Berlin street of tenements in summer: three open, empty windows, the open house door, things set on the pavement, a loaded handcart at the kerb; nobody in the street | same (`street`) |
| `assets/cinematics/flashback/evictions/chronicle.png` | a desk: a typed page headed „CHRONIK“ / „1941“ / „AUGUST“ (every other line unreadable dashes), a plan with hatched blocks along an axis, pen, ink, stamp | same (`chronicle`); pixel fonts of `env_veltrava_lib` |
| `assets/cinematics/flashback/evictions/room.png` | the cleared room: pale rectangles where a wardrobe and pictures were, a bare curtain rod, the darker floor where the carpet lay, the open door, a scrap of packing paper | same (`room`) |
| `assets/cinematics/flashback/settlement/steppe.png` | open country under a wide sky: barracks and earth huts with thin smoke, a rutted track, a telegraph line, three people far off | same (`env_flashback_soviet.steppe`) |
| `assets/cinematics/flashback/settlement/kommandantur.png` | the commandant's office (a log house, the board „КОМЕНДАТУРА“, a notice board) and seven people and a child waiting to report, all from behind | same (`kommandantur`) |
| `assets/cinematics/flashback/settlement/boundary.png` | the road out of the district at dusk: a hut, the striped barrier down, a board nobody can read, the telegraph line running on | same (`boundary`) |
| `assets/cinematics/flashback/kyshtym/plant.png` | the works across the water on a still day: halls, three stacks with thin plumes, low tank lids, a fence along the shore; reeds, birches and a boat in front. No blast, no cloud | same (`plant`) |
| `assets/cinematics/flashback/kyshtym/village.png` | a village left behind: three log houses with open doors and cold chimneys, open gates, a well with its bucket on the ground, a cart with the shafts down | same (`village`) |
| `assets/cinematics/flashback/kyshtym/fence.png` | a forest road ending at a chained mesh gate in a barbed-wire fence, an inner fence beyond, a barrier pole, a guard hut, an unlit lamp | same (`fence`) |
| `assets/cinematics/flashback/look/gate.png` | the film gate (480 × 360): rounded corners, a ragged edge, a hair | same (`gate_mask`) |
| `assets/cinematics/flashback/look/scratch_a.png`, `scratch_b.png`, `dust.png` | one light and one dark scratch (1 px wide), four dust specks (8 × 8 each) | same (`scratch`, `dust`) |
| `assets/cinematics/flashback/layout.json` | plates, drift anchors, overlay positions, the ramp and the accent colours | same |
| `assets/audio/sfx/fb_projector_bed.wav` | the films' only sound (19 s, 44.1 kHz, 16-bit, stereo, one-shot): a small projector in a quiet room — switch, motor run-up, a steady whirr with sixteen claw ticks a second, a low hum, the hiss and soft pops of an empty optical track, the run-down. No music | `py -3 -P tools/audiogen/flashback_audio.py` (numpy synthesis from one fixed seed) |
| `data/flashbacks/flashbacks.json` | the four film sheets (card, scene, bed, caption keys, shot lengths, lamp windows) | written by hand |
| `data/locale/de_flashback.json`, `data/locale/en_flashback.json` | button, hint, skip, the four place-and-date captions, eight lines, eight entries of the film page | written by hand; every caption restates facts of its card (`data/locale/*_history*.json`), checked by `tests/test_flashbacks.gd` |

Reproduce: `py -3 -P tools/pixelgen/env_flashback.py [--sheet <png>]`, `py -3 -P tools/audiogen/flashback_audio.py`,
then the shared import. Review captures: `"$GODOT" --path . res://tests/visual/flashback_shots.tscn -- --cinematic=none
--fb-mode=both --fb-out=<dir> [--fb-lang=en --fb-scale=1.5]`.
