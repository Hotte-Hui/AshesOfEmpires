# Asset manifest part — splash (boot sequence + demo notice, round 11)

Date: 2026-11-07. Owner: splash. Contract: TECHNICAL_ARCHITECTURE §12.13. Everything is original and generated
deterministically by the scripts below (re-running reproduces the files byte for byte); no image, sound or logo of
any third party is used — the engine card only names the engine in the game's own pixel capitals.

| Item | Path | Origin / generator | Licence |
|---|---|---|---|
| Title picture | `assets/ui/splash/title_scene.png` (640×420, shown ×3; final view = rows 0–359, the card starts on rows 60–419 and tilts up) | `tools/pixelgen/gen_title_splash.py` — Karsk railyard at dusk (water tower, depot, silos, slab blocks, chimneys whose smoke drifts east, crane, semaphore signal, snowed-in sidings) and the domed Great Hall of Berlin (fictional, no insignia) in the afterglow, divided by ONE railway line running to the horizon; telegraph poles and a snow fence on the Berlin side; stars, stratus clouds lit from below | Project art |
| Train lamp | `assets/ui/splash/title_lamp.png` (640×420, binary alpha) | same generator — headlamp, glittering halo, horizontal flare, light running down the rails; faded / pulsed at runtime | Project art |
| Title lettering | `assets/ui/splash/title_logo.png` (ASHES OF EMPIRES), `assets/ui/splash/title_sub.png` (◆── THE LAST WINTER ──◆) | same generator — own 7×9 capitals → Scale3x → bold verticals, forged-copper ramp, bevel, snow lying on the letters, ash flecks, outline + drop shadow; subtitle in snow tones at 1× | Project art |
| Studio emblem | `assets/ui/splash/studio_mark.png`, `studio_glow.png` (40×40, shown ×4) | same generator — broken ring of ash around a glowing ember with a small flame; dithered glow pulsed at runtime | Project art |
| Pixel capitals | runtime, `scripts/ui/pixel_font.gd` (5×7, umlaut dots above the cap line as in `pixfont_umlauts.py`, Scale2x option) | hand-made glyph table; letters the studio name and „Erstellt mit / Godot Engine“ from locale keys | Project code |
| Glint | `assets/shaders/splash_glint.gdshader` | hand-written canvas shader, quantised to art pixels | Project code |
| Title sting | `assets/audio/music/mus_title_sting.wav` (9.2 s, 44.1 kHz/16-bit stereo) | `tools/audiogen/title_audio.py` — snow wind, low D drone, far locomotive horn, the K head (piano) answered by the B head (celesta) from `music.py`, one stroke at 2.40 s (timpani + sub, low brass, strings on D minor add9) when the title appears, open D/A ringing into the menu theme | Project audio |
| Ember crackle | `assets/audio/sfx/splash_ember.wav` (3.0 s) | same script — warm breath, crackling embers, faint glassy shimmer | Project audio |
| Fonts | `assets/fonts/fv_serif_italic.tres` („präsentiert“, signature), theme fonts of the letter | reused | SIL OFL 1.1 |
| UI kit art | `assets/ui/icons/ornament_diamond.png`, `icons/stamp_evidence.png`, `frames/paper.png` (PaperPanel) | reused | see `ui.md` |
| Text | `data/locale/de_splash.json` (`splash.*`, `ui.demo.*`; studio name `splash.studio`) | written for this round | Project text |

Run: `py -3 -P tools/pixelgen/gen_title_splash.py [--preview=DIR]`, `py -3 -P tools/audiogen/title_audio.py`.

Verification: `tests/test_splash.gd` (12 cases); windowed check run of the real boot
`godot --path . -- --splash-shots=DIR` (frames of every card, the main menu and the letter; the letter is not
confirmed, the settings flag is not written) — frames reviewed outside the project (scratchpad).
