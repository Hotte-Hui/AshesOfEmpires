# NEXT STEPS — Ashes of Empires: The Last Winter

State: vertical slice after expansion round 2 (see DEVELOPMENT_STATUS.md, TEST_REPORT.md). Main path ≈ 12–15 min,
with all 43 optional finds and chats ≈ 25–30 min (estimates; no human playtest yet). Open work, in priority order.

## 1. Human playtest and listening pass (cannot be automated)
- Play the exported build with keyboard and with a physical controller (pad mapping exists, never tried on hardware).
- Judge: camera feel (spring 5.2/s, look-ahead 40 px, dead zone 6×4 px in `scripts/render/world_camera.gd`), walk
  speed, pacing of the two transitions (40 s / 47 s), readability of hidden finds (glint period in scene.json), puzzle
  difficulty, text speed.
- **Listen**: all music, ambience and ~70 SFX are synthesized and were only checked numerically; mix against dialogue.
- Rate scenes with `preproduction/docs/ART_QA_SCORECARD.md`.

## 2. Known polish items (from the specialists' reports)
- Characters: bodies/torsos still rig-rendered (heads and faces were redone); front/back walk feet 1–2 px off the
  origin mid-stride; no `talk_front`; the player turns instantly (NPCs turn softly via `rig.turn_to()`).
- Portraits share one sculpted head base — individualise noses/chins/eyes further; Babushka's scarf reads hood-like.
- Cinematics: hands in the stamp/desk shots are procedural; the Berlin far roof layer of the A1→M1 sequence is plain;
  Karsk shots inside the transition are hard cuts.
- 3D hall: near objects can still crawl during the crane/push (geometry renders at 640×360); kiosk only visible in h1.
- Rendering: translucent overlays (fog, smoke, shafts) have no own dither code — small threshold shifts when layers
  slide; odd window sizes (1366×768, 1600×900) fall back to uneven texel widths.
- Karsk: the distant train is hidden behind buildings from camera ~900–1150; tiny emblems (newspaper, plaques) are
  only hints at 1×.
- Small pixel fonts: Ä/Ö in close-ups read almost like A/O.
- Engine prints "resources still in use at exit" (audio streams at quit) — harmless.

## 3. Build size and platforms
- ~120 MB lossless WAV in the pack; switch music/ambience to QOA or Ogg after the listening pass (~5× smaller).
- Test on a mid-range and an integrated GPU (only an RTX 4090 so far); 1440p display check.

## 3b. Requested by the user, not done yet
- Plaza polish: a mini-game or small task on the plaza (user wished for "Aufgaben und Minigames" there), more easter
  eggs (only one so far), a portrait for the press photographer, close-up brightness vs. the evening art.
- Parade: tribune officials are tiny (~14 px); possible pipeline-compile hitch on first play.
- **Merge branch `kapitel-3`** (cloud session: Chapter-3 story data, level shells without art, Veltrava finds,
  E2E drivers) — follow `documentation/MERGE_NOTES_C3.md` on that branch, then build the Veltrava art.
- `data/v3/cinematics.json` still lists the hall shots as 3/5/3 s (now 5.5/9/9.5 s) — informational only; update
  together with the next data/v3 change (the parity fixture must be regenerated then).

## 4. Content and features for the full game
- **Chapter 3 "Der eiserne Frieden"** — a prompt for a parallel cloud session (branch `kapitel-3`) was prepared; merge
  it here, then verify in-engine.
- **English localisation** (Loc supports more files; add a language setting).
- Mouse click-to-walk in the world; voice acting not planned for the slice.
- Story hooks from round 2 to carry forward: the "Hanna" thread in Berlin (house number 14 after the eviction list,
  the porter's message) sets up the Chapter 5 decision about her neighbours' file — note it in STORY_BIBLE.

## 5. Process
- Keep all test layers green after every change: `tests/run_all.gd`, `--autoplay` (4 routes × play/skip,
  `--autoplay-explore`), `--inputplay` (`--inputplay-explore`). Re-export and run the exe before calling anything done.
- Re-running `tools/pixelgen/env_karsk.py` keeps the round-2 skyline (it merges `assets/environments/karsk_skyline/skyline.json`).
