# NEXT STEPS — Ashes of Empires: The Last Winter

State after round 7 (2026-11-06): Chapters 1–3 (opening) playable, memories (§12.10), side tasks (§12.9), 9 optional
mini-games (§12.8), 91 finds, 24 chats, 19 history cards. Main path ≈ 24 min, everything ≈ 2 h for a completionist
(estimates from `tools/docs/estimate_playtime.py`; no human playtest yet). Open work, in priority order.

## 1. Round 8 (planned and started on 2026-11-06): Chapter 3, part 2
Canon: STORY_BIBLE §6 row 3 and `preproduction/narrative/FUTURE_CHAPTER_ARCS.md` — Elena Weiss vanishes with notes;
the radio broadcast heard in both hotel rooms; the joint evidence check that shows the contract partner is not simply
"the other country"; a fire in the commission's registry forces both men to save the same file together — the first
scene where both act (authored in-level protagonist switches, never a menu); outside in the snow each keeps half.
Contract: `documentation/C3P2_DESIGN.md` (written in round 8). Build streams: registry level with fire states, night
locations, cinematics, the joint evidence-check puzzle UI, cast and sound, exploration (finds, a side task, a mini-game).
In parallel a feel pass: walking ambient figures (Palais, station, reading room), the thawed car 3 after the heating
task, desynchronised decor loops, portraits for the evicted Berlin family, MemoryView fixes, toasts held while a
modal is open, journal tab row, Voronova's hat edge, a richer Soviet compartment shot in LS_C3_Trains.

## 2. Human playtest and listening pass (cannot be automated)
- Play the exported build with keyboard and a physical controller (pad mapping exists, never tried on hardware).
- Judge camera feel, walk speed, pacing of the cinematics, readability of hidden finds, puzzle and mini-game
  difficulty (Relaispult round 3 may be hectic; knobs in `relay_logic.gd`), text speed.
- **Listen**: all music, ambience and ~200 SFX are synthesized and were only checked numerically (levels, loops,
  onsets) — mix against dialogue; the relay desk's synthetic voices may sound buzzy.

## 3. Known polish items (from the round-7 reports)
- Characters: faces share one lighting setup; women's faces still a little angular; `talk_back` only for the two
  protagonists; Kessler's rimless glasses are drawn with thin rims.
- Station: island walkers are simple procedural figures; pigeons vanish under the canopy.
- Palais: life figures are fixed loops (walkers come in round 8); clocks have baked hour/minute hands.
- Mini-games: Morse/Rohrpost switch to ×2 pixel art at 125/150 % text; the cloakroom rack shows five coats, the
  hall counter six.
- 3D hall: near objects can still crawl during the crane/push; parade tribune officials are tiny (~14 px).
- Small pixel fonts: Ä/Ö in close-ups read almost like A/O.
- Only 1920×1080 captures for the round-7 art; check 1440p and 4K.

## 4. Content for the full game (STORY_BIBLE §6)
- **Chapter 4 „Stimmen unter Beton“** (alternating): Alexei traces sealed wagons through tunnels to a transfer siding;
  Konrad maps the registry annex under the Hall; testimony of evicted families (Marta Vogel) and returned exiles;
  choice: reveal a witness's identity to obtain records — or protect them. Switch moments on shared objects (the same
  wagon number, the same registry card). Uses the round-8 in-level switch.
- Chapters 5–6 and the assembled endings (§8: Öffentliche Akte, Stille Sicherungen, Brüchige Reform, Getrennte Wege,
  Gebrochenes Vertrauen) with epilogues.
- English localisation (Loc supports more files; add a language setting); mouse click-to-walk.
- Story hook to carry forward: the "Hanna" thread in Berlin (house number 14, the porter's message) sets up the
  Chapter-5 decision about the neighbours' file.

## 5. Process
- Keep all test layers green after every change: `tests/run_all.gd`, `--autoplay` (routes × play/skip,
  `--autoplay-explore`, `--autoplay-memories`), `--inputplay` (`--inputplay-explore`, `--inputplay-memories`).
  Re-export and run the exe before calling anything done. E2E runs write to the game's user:// folder — back it up
  first and restore it afterwards (the user plays the same build).
- Token budget: fresh session per big round, 6–10 agents with tight briefs, filtered output (see memory notes).
