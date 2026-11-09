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

## Checks
`tests/test_pixel_fire_kit.gd`: every sheet exists and fits kit.json, hard pixels only, the limited ramp, tiles
join in any order, neighbours out of phase, light under 3 Hz, the two films draw no scaled or faded fire any more.
