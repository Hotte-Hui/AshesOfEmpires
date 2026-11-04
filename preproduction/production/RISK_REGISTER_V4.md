# Risk register v0.4

| Risk | Likelihood | Impact | Detection | Response |
|---|---|---|---|---|
| Pure 3D cannot reproduce deliberate pixel clustering | High | High | side-by-side style scorecard | hybrid stages, hand-corrected sprites |
| Temporal AA/TSR causes crawling/ghosting | High | High | recorded motion at fixed camera | compare FXAA/no AA, render targets, depth-aware stylization |
| Feature scope expands from slice to 8–12 h game | High | Very high | backlog and milestone reviews | lock demo scope until packaged/playtested |
| Seed C++ fails to compile against installed UE5 | Medium | High | first clean compile | treat seed as reference, fix API/build scripts, preserve logs |
| Story softlock after saving at a transition | Medium | High | save/load and skip matrix | atomic quest events, gated scene director, restore checks |
| Source references cannot legally be shipped | High | High | provenance audit | reference-only, create original assets, obtain rights as needed |
| Ambiguous alternate-history framing trivializes crimes | Medium | High | narrative review | explicit critical treatment, historically informed sensitivity review |
| RTX 4090 cannot maintain targeted 4K/60 | Unknown | Medium | frame-time captures in actual packaged build | graphical budget and per-scene tuning |
| Work/Claude handoff loses decisions | Medium | Medium | audit README/CLAUDE/status | single source of truth, stable IDs, acceptance logs |
| Assistant mistakes prototype for completed game | Medium | High | evidence-based status matrix | distinguish authored, tested offline, compiled, packaged, player verified |
