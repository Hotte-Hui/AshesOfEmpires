# NEXT STEPS — Ashes of Empires: The Last Winter

State at the time of writing: the vertical slice (Chapter 1 opening in Karsk + Chapter 2 opening in Berlin, with
the Great Hall reveal and the X1 finale montage) is integrated, playable end to end and tested (see
`TEST_REPORT.md`). Everything below is **not done yet**, in priority order.

## 1. Human playtest of the slice (highest value, cannot be automated)
- Play the exported build start to finish with keyboard, then with a controller.
- Judge what the automated tests cannot: pacing, readability of hints, puzzle difficulty, walking speed
  (45 px/s walk / 90 px/s run), camera feel during pans, dialogue text speed.
- **Listen**: no human has heard the synthesized music, ambience and SFX yet. Expect level tweaks per stem
  (`tools/audiogen/music.py`, `ambience.py`) and a mix pass against dialogue.
- Rate A1, M1, the Hall and the stills with `preproduction/docs/ART_QA_SCORECARD.md` (needs a human reviewer).

## 2a. Bring the slice to its 20–30 minute target (content, not systems)
The systems are complete; the slice currently plays in an estimated 10–15 minutes because the canonical script
has only 14 dialogue lines. Add, in `data/v3` (+ regenerate the parity fixture) and the locale files:
- optional conversations: the tea-stall vendor, the fire-barrel workers, the waiting family (Karsk); the clerk
  and a second Emil scene (Berlin), each revealing world context without new mandatory gates;
- more observation hotspots (both levels already have unused prop silhouettes and signage to hang them on);
- two or three additional documents per level (ledger history, a transfer order, an archive memo);
- a short walk-and-talk with Irina before the signal box and a phone call for Konrad after the hall reveal.

## 2. Polish items found during integration (small, known)
- X1 desk tableaux (`x1_alexei_desk.png`, `x1_konrad_desk.png`): hands and sleeves are simplified shapes.
- Civilians only have `idle_side` / `walk_side` rows; Emil has no walk; front/back views are stiffer than side views.
- Irina's sprite headscarf reads a little helmet-like; portraits have no talking-mouth frames.
- `berlin_archive/shafts.png` is designed for additive blending; `layer_stack.gd` ignores the `blend` hint.
- Engine prints "N resources still in use at exit" / "ObjectDB instances leaked" on quit (harmless, but should be
  tracked down with `--verbose`, probably static texture caches in `layer_stack.gd`).
- Toast column can briefly overlap the chapter-card band when many toasts fire at level start.
- Platform lamps in Karsk are cold white on purpose (one warm focal light per screen); revisit after playtest.

## 3. Build size and platforms
- Audio ships as lossless WAV (~120 MB). Switch music/ambience imports to QOA or Ogg Vorbis after a listening
  check (expected ~5× smaller build).
- Test on a mid-range GPU and on integrated graphics (only an RTX 4090 was used so far).
- 1440p check (1080p and 4K were verified visually).

## 4. Features still missing for the full game
- **Localisation:** German only. Add English (`data/locale/en_*.json`, `Loc` already supports multiple sources).
- **Mouse in the world:** UI is fully mouse-capable; world movement is keyboard/controller only (no click-to-walk).
- **Chapters 3–6** (8–12 h total, multiple endings): designed in `STORY_BIBLE.md` and `QUEST_DATABASE.md`
  (Chapter-3 callbacks `C3_IRINA_WITNESS`, `C3_ALEXEI_SILENCE`, `C3_KONRAD_COPY`, `C3_ARCHIVE_ALERTED`, …);
  not implemented. The production pipeline is ready: new environments via `tools/pixelgen/env_*.py` +
  `scene.json`, characters via `tools/pixelgen/characters.py`, story data in `data/v3/*.json` (regenerate the
  parity fixture with `tests/reference/make_python_reference.py` after edits).
- The `civilian_welfare` meter is reserved and unused in the slice.
- Voice acting: none planned for the slice; subtitles carry all speech.

## 5. Process
- Keep running all three test layers after every change: `tests/run_all.gd`, `--autoplay` (4 routes × play/skip),
  `--inputplay` (real key presses). Re-export and smoke-test the build before calling anything done.
