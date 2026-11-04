# QA matrix v3

| ID | Level | Test | Evidence |
|---|---|---|---|
| D01 | Python | v3 JSON parse, references and DAGs valid | validate_v3 output |
| D02 | Python | A1 and M1 all four branch combinations | unittest |
| D03 | Python | objective cannot advance before prerequisites | unittest |
| D04 | Python | duplicate input cannot apply choice twice | unittest |
| D05 | Python | save JSON round trip and v1->2 migration | unittest |
| D06 | Python | cinematic skip vs play same end-state | unittest |
| U01 | UE5 | Paper2D plugin and selected camera types render | editor screenshots |
| U02 | UE5 | A1 quest runs fully using mouse/keyboard | recorded test, log |
| U03 | UE5 | puzzle wrong input/retry/hint/reset works | gameplay test |
| U04 | UE5 | M1 detective loop and two plan overlays | gameplay test |
| U05 | UE5 | transitions happen once, Skip equivalent | gameplay test |
| U06 | UE5 | Save/load across scene switch and after choice | packaged Windows test |
| V01 | UE5 | no pixel crawl in 10s slow pan, 1080p and 4K | videos |
| V02 | UE5 | not photorealism, coherent palette 2D/2.5D/3D | images + manual score |
| V03 | UE5 | monumental architecture is critically framed | narrative/art review |
| P01 | UE5 | 60FPS aspiration on RTX 4090 | FPS and frame times measured |
| A01 | UE5 | fonts and quest markers accessible | QA log |
| L01 | Rights | only clearly licensed final media in build | provenance sheet |

**D-series tests can be performed outside the engine and are not evidence that any U/P/V/A/L test passed.**
