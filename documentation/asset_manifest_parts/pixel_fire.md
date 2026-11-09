# Pixel fire kit (round 13)

Owner: cinematics stream. One fire for the whole game: flames, smoke, sparks and fire light authored on the pixel
grid by `tools/pixelgen/pixel_fire.py` (deterministic, original, painted in code) and played pixel-snapped by
`scripts/render/pixel_fire.gd` (+ `pixel_fire_reveal.gdshader`). First users: LS_C3_Fire and LS_C3_Escape.
Rules: 1 texel = 1 world pixel, alpha 0 or 255 only, no blur, no runtime scaling or rotation, whole-pixel positions;
things grow by switching to a bigger sheet and fade through the dither drawn into their frames; every instance
has its own phase (golden-ratio sequence) and mirror, so neighbours never pulse in sync.

## Art — `assets/fx/pixel_fire/` (sheet table: `kit.json`; all sheets are frames side by side)
| File | Use |
|---|---|
| `flame_xs` (8, 10x16), `flame_s` (8, 20x30), `flame_m` (8, 36x54), `flame_l` (10, 56x92), `flame_xl` (12, 80x144), `flame_xxl` (12, 112x212) | looping flames, bottom-centre anchored: tongues that rise, lean into a travelling sway, pinch at the neck and let their tip go as a flamelet that climbs on and cools; one merged hot core; a fire grows by stepping up these sizes |
| `lick` (10, 48x80) | flames out of an opening and up the wall above it, leaning with the draught |
| `window` (8, 48x32), `ground` (8, 64x26), `low_a`, `low_b` (10, 96x60), `wall_a`, `wall_b` (12, 128x136) | tiles (wrap in x; a / b join in any order): fire filling an opening, a low ground fire, a low and a tall wall of fire |
| `puff_s/m/l/xl` (+ `_grey`) (8-12 frames, 16x16 .. 104x84) | one puff's life: a tight ball swells into a cauliflower of pixel discs (dark / body / lit, 2x2 checker between the tones) and breaks up through the ordered dither; warm = lit by the fire below, grey = away from it |
| `bank_a`, `bank_b`, `veil_a`, `veil_b` (+ `_grey`) (8, 160x48) | tiles: a rolling bank of smoke under a ceiling, its underside frayed by dither; the veil is the same billows with dither holes (the thin leading stretch of a bank) |
| `sparks_s` (12, 24x40), `sparks_m` (12, 56x80) | looping fields of single-pixel sparks on arcs, cooling down the spark ramp |
| `glow_s/m/l` (4, 48 / 96 / 176 px), `pool_s/m/l` (4, 64x24 / 120x40 / 200x64) | fire light for additive drawing: three flat bands dithered into each other and into nothing, four frames that breathe; glow = on a wall, pool = on a floor or on snow |

Colours: `#A8381A` `#D8662A` `#F2A044` `#FCE0A0` `#FFF6DC` (rim .. white-hot core) + `#6E1E0C` (cooling), smoke
`#1A1412` `#4C3020` `#844E2A` (warm) / `#14161A` `#2B2E33` `#4C4C4E` (grey) — all from the scenes' own ramps.
Other palettes and sizes: import `pixel_fire` in a generator and call `flame_frames` / `puff_frames` / `bank_frames`
/ `pool_frames` (see `env_c3p2_cine_fire.build_fx_fire`), then `PF.register()` the sheet at runtime.

## Rollout: every other fire of the game (round 13)
`tools/pixelgen/pixel_fire_bake.py` bakes the kit's parts for cells of any size and loop length (`flames` over a
fuel line, `hot` = the emission twin of the hot core, `column` / `wisp` = looping columns of puffs, `ceiling` = a
still bank under a ceiling, `drift` = a rolling stretch of it, `halo` = flat light bands, `recolor` / `bands` for a
scene's own palette). The scene generators call it where they used noise flames and soft veils; file names, cell
sizes, frame counts and `scene.json` are unchanged, every other output of the generators is byte-identical.

| Where | Files (generator) | Now |
|---|---|---|
| L_C3_Registry (looks C / D) | `veltrava_registry/fx/flames_*.png` + `_e` (14 strips), `smoke_c|d.png`, `fx/roll_*`, `fx/plume_*`, `fx/heat_*` (`env_c3p2_archive_fx.py`) | designed tongues with merged bands, emission = hot core only; the smoke under the vaults is a hard-pixel bank with billows and a dithered veil, the rolls are stretches of the kit's bank, the plumes columns of puffs, the heat shimmer became sparks; kit colours (the film LS_C3_Fire plays in this room) |
| L_C3_Quay | `veltrava_quay/life/fire_win_1..5.png` + `_e`, `fx/smoke_1..3.png`, `fx/smoke_ladder.png`, the fire's halos in `glow_air.png` (`env_c3p2_quay_life.py`, `_near.py`) | tongues filling the souterrain windows and standing on the lintels, columns of puffs, halos as flat dithered bands — in the Veltrava palette (red rim, lamp ramp; the palette has no fire ramp) |
| LS_C3_Halves (h3) | no files: the film plays kit sheets (`ch3_halves.gd`); `halves/flame_s.png`, `halves/smoke.png`, `halves/h3_plume.png` removed | flames in the wing's windows and on its roof, a plume per fire, the big column as puffs, sparks; glow steps instead of ramping |
| LS_C3_Fire | `c3p2/fire/f2_glow.png`, `f4_lit.png`, `f4_lit_table.png` (`env_c3p2_cine_registry.py`) | palette differences (lit minus unlit, both quantised with the background's dither): background + layer is the palette picture of the lit place; the wall of fire is drawn as one mass (`scripts/render/pixel_fire_mass.gdshader`) |
| L_M1_Parade avenue | flame cells of `great_hall/avenue/avenue_figures.png` (`gen_great_hall_avenue.py`) | the kit's tongues per LOD cell in the avenue's warm ramp (exact Berlin palette) |
| Karsk depot (L_C4P2_Karsk) | `karsk_c4p2/fx/barrel_flames.png` + `_e`, every wisp of `plume()` (hood / dispatch / brazier / cabin / sandhouse smoke, kasha / samovar / express steam, coal dust) (`env_c4p2_karsk_fx.py`) | barrel fire as tongues in the depot's colours; wisps as hard-pixel puffs in three tones of their ramp |
| Karsk railyard (L_A1_Railyard) | `karsk_railyard/fx/barrel_flames.png` + `_e` (`env_karsk_fx.py`) | tongues in the copper ramp |
| Karsk tunnels (L_C4_Tunnels) | `karsk_tunnels/fx/booth_smoke.png`, `samovar_steam.png`, `steam_flange.png` (`env_c4_tunnels_fx.py`) | hard-pixel puffs |
| Plaza (L_M1_Plaza) | `hall_plaza/props/barrel_guard.png` (+ `_e`, `_n`) (`env_plaza_sprites.py`) | the still flame is one frame of the kit's tongues |
| LS_C4P2_Depot | `c4p2/depot/flame.png` (`env_c3p2_cine_kit.flame_sheet`); `depot/embers.png` removed (sparks: `PF.sparks`) | tongues; sparks cool down the spark ramp; the glow steps |
| LS_C4P2_Clock | — (`ch4p2_clock.gd`) | the candle's light steps (`light_step`) instead of ramping |
| Berlin courtyard (L_C4P2_Berlin) | `berlin_c4p2/fx/smoke_0..3.png`, `fx/smoke_chimney.png` (`env_c4p2_berlin_life.plume_strip`, base < 3) | chimney smoke as hard-pixel puffs in three tones of its ramp (steam keeps its veil) |
| Berlin archive (L_M1_Archive) | `berlin_archive/actors/smoke_curl.png` (`env_berlin_fx.smoke_curl_strip`) | the cigarette's thread in hard pixels: it thins out instead of fading |

All of it is original, deterministic work of the scripts named above (no downloads).

## Checks
`tests/test_pixel_fire_kit.gd`: every sheet exists and fits kit.json, hard pixels only, the limited ramp, tiles
join in any order, neighbours out of phase, light under 3 Hz, the films (LS_C3_Fire, LS_C3_Escape, LS_C3_Halves)
draw no scaled or faded fire any more; rollout: the baked level strips are hard pixels in a limited ramp, the
mass passes exist, the light layers of LS_C3_Fire add up to a palette picture, the soft assets are gone.
