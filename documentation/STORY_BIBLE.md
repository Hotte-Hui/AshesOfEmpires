# STORY BIBLE — ASHES OF EMPIRES: THE LAST WINTER

Status: AUTHORED 2026-11-04. Builds on the locked preproduction canon (`preproduction/docs/STORY_BIBLE.md`,
`narrative/*`). Change log vs. canon: German protagonist renamed **Konrad Adler** (user request); the six-chapter
arc, the full C-17 truth, factions and the ending matrix are new and marked PROPOSED until the user accepts them.

## 1. Premise
Europe, winter 1964. A war that began in 1939 ended in 1953 without a victor; an exhausted armistice froze a
line through Eastern Europe. Two dictatorships survived: the Soviet Union and Nazi Germany. Ten years later both
sign the **Corridor Accord** — a reconstruction treaty that rebuilds railways and supply routes across the
armistice line. Alexei Morozov, a Soviet railway engineer, and Konrad Adler, a Berlin architectural draftsman,
each find one half of a secret buried in the Accord's paperwork: contract series **C-17**.

**Central question:** Can two people raised to distrust each other's countries recognise the truth behind their
governments' competing narratives — and act on it when acting has a price?

## 2. Tone and handling rules (binding)
* Serious, humane, specific. People first; slogans never.
* The Nazi regime is shown as a criminal racial dictatorship; its genocide is history inside this world, never a
  backdrop for spectacle, never "balanced". The Soviet system is shown with its own specific repression
  (deportations, camps, censorship, informants). **No false equivalence, no glamour, no collectible insignia.**
* Ordinary people in both countries are diverse: complicit, afraid, brave, tired, funny, kind.
* Monumental architecture is always framed against its human cost.
* The central conspiracy is fictional and never replaces or "explains" historical crimes.

## 3. The truth of C-17 (spoilers — the player assembles it over six chapters)
The Corridor Accord is genuinely useful: trains run again, grain and medicine move, towns like Karsk come back to
life. Annex series C is the "Logistics Integration" annex; **contract C-17** links the rail freight system with
the population registries of both states. On paper it standardises manifests. In practice it creates:
1. **A shared registry bridge** — card-index data (Germany: the *Zentrale Erfassungsstelle* under the Great Hall
   district; USSR: the transport department of State Security in the Karsk oblast) is exchanged via sealed
   courier wagons, so each regime can track people who crossed the armistice line.
2. **The Reciprocal Return Protocol** — a secret clause under which each side hands back "persons of interest"
   (defectors, refugees, dissidents, members of persecuted groups who fled) hidden as freight in sealed wagons
   on Accord trains. Returned people disappear into prisons and camps.
3. **Clearance zones** — in Berlin the corridor's registry annex requires "clearing" whole blocks around the
   Great Hall; families are evicted and their files flagged. In Karsk, "re-booked" wagons and workers who ask
   questions are reassigned.
No single mastermind exists: a German ministry wants trade and control, Soviet State Security wants its
defectors back, transport ministers want the trains running, a neutral commission wants the peace to hold and
looks away, and many clerks simply stamp what they are given.

## 4. Factions
| Faction | Wants | Face |
|---|---|---|
| Reich Ministry of Transport | Accord prestige, rail revenue, control | Ministerialdirektor **Gerhard Kessler** |
| German Staatspolizei | Registry data, returned exiles | Kommissar **Ludwig Wendt** |
| Soviet Ministry of Railways | Reconstruction, food, prestige | Deputy Minister **Lidia Voronova** (believes in the trains, half-blind to C-17) |
| Soviet State Security (transport dept.) | Defectors back, informant network | Colonel **Yuri Arkhipov** |
| Neutral Accord Commission, Veltrava | Peace holding at any price | Commissioner **Henrik Aalto** (Finnish) |
| Veltrava exile community | Survival, papers, family | **Pyotr Ilyin** (Alexei's childhood friend, defected 1957), the printer **Ada Kron** |

## 5. Protagonists (see CHARACTER_BIBLE.md)
* **Alexei Morozov (29)** — railway engineer, Karsk. Arc: from "I fix the line, politics is theirs" to taking
  responsibility for his silence; learns to separate people from states.
* **Konrad Adler (31)** — architect/draftsman, Berlin reconstruction office. Arc: from "drawings are neutral" to
  naming his own complicity; chooses people over career.

## 6. Six chapters (8–12 h)
| # | Title | Playable | Mode(s) | Core |
|---|---|---|---|---|
| 1 | **Die Heimkehr / The Homecoming** | Alexei | B oblique (yard, quarter), A side (signal box) | Restore the line; three wagons missing; C-17 in the ledger. Choice: tell Irina or keep it. |
| 2 | **Die Stadt aus Stein / City of Stone** | Konrad | A side (archive, office), C 3D (Great Hall), B (Hall district) | Contradicting plans; a corridor behind a wall; Emil: "C-17 is a contract series". Konrad's own office signed the revision. Choice: copy or official request. |
| 3 | **Der eiserne Frieden / The Iron Peace** | both, separate → meet | B (Veltrava streets, station), A (conference hall, train), C (conference hall reveal) | Both attend the Accord conference in neutral Veltrava. The interpreter **Elena Weiss** vanishes with notes. Distrustful first meeting; a fire in the archive forces them to save the same file together. Each keeps half. |
| 4 | **Stimmen unter Beton / Voices Beneath Concrete** | alternating | A (tunnels, archives), B (rail depot, Hall district) | Alexei traces sealed wagons through tunnels to a transfer siding; Konrad maps the registry annex under the Hall. Testimony of evicted families (Marta Vogel) and returned exiles. Choice: reveal a witness's identity to obtain records — or protect them. |
| 5 | **Der Preis des Friedens / The Price of Peace** | alternating | B (Karsk quarter, Berlin blocks), A (night train) | Factions close in; the archive is seized; earlier trust decides who helps. Reconstruction choice: keep repairing the civilian line Karsk needs, or sabotage it to stop a return train. Konrad must decide about his sister's neighbours' file. |
| 6 | **Asche und Morgen / Ashes and Dawn** | both, convergent | B (border interchange), C (commission chamber), A (epilogues) | The return train meets the commission's deadline. Both protagonists act in parallel scenes; outcome assembled from trust, evidence chain and protected people. |

### Character-switch moments (authored, never a menu)
Ch1→2 C-17 stamp → pencil note (match cut, metal → tram bell) · Ch2→3 Konrad's train window → Alexei's train
window (parallel railway journey) · Ch3 mid: radio broadcast heard in both hotel rooms · Ch4 alternates on
shared objects (the same wagon number, the same registry card) · Ch5 a phone line that connects both cities ·
Ch6 cross-cut finale on a single clock.

## 7. State variables (canonical + planned)
Canonical (slice): `irina_trust`, `alexei_secrecy`, `konrad_evidence`, `office_suspicion`, `civilian_welfare`,
`c17_confirmed`, `signal_restored`, `blueprint_match_confirmed`, `slice_finished`.
Planned: `alexei_konrad_trust` (0–5), `elena_trust`, `marta_trust`, `evidence_chain` (0–6 independently
verifiable documents), `witnesses_exposed`, `people_protected` (count), `line_repaired_ch5`, `kessler_alerted`,
`arkhipov_alerted`. No good/evil meter.

## 8. Endings (assembled, not picked from a menu)
| Ending | Requires (summary) | Outcome |
|---|---|---|
| **Öffentliche Akte** | evidence_chain ≥ 5, alexei_konrad_trust ≥ 3, witnesses_exposed = 0 | Neutral press and observers publish; the Return Protocol is suspended; some families protected; both regimes survive; Alexei must leave Karsk, Konrad loses his post. |
| **Stille Sicherungen** | people_protected ≥ 3, evidence_chain < 5, trust ≥ 2 | The registry bridge is quietly broken from inside; dozens escape the lists; nothing is public; the protagonists keep their lives and the secret. |
| **Brüchige Reform** | Voronova and Emil allies, trust ≥ 4, line_repaired_ch5 | The Accord is renegotiated with neutral oversight of manifests — fragile, reversible, real for some. |
| **Getrennte Wege** | trust ≤ 1 | Each saves only his own people; the corridor keeps running; a final letter that never arrives. |
| **Gebrochenes Vertrauen** | evidence fragmented and a witness exposed | The investigation is suppressed; a protagonist is arrested; epilogue from the other side of a fence. |
Every ending gets epilogues for Alexei, Konrad, Irina, Emil, Elena, Marta, Pyotr and the two towns.

## 9. Vertical slice (Chapter 1 opening + Chapter 2 opening, 20–30 min)
Exactly the canonical screenplay `preproduction/narrative/VERTICAL_SLICE_SCRIPT_V3.md`, with Konrad Adler as the
German protagonist (renamed from the preproduction package): A1 *Das letzte Signal* → match cut → M1 *Die falsche Zeichnung* → Great Hall reveal → X1 *Zwei Züge,
ein Eintrag* → demo end. Both protagonists have not met yet (they meet in Chapter 3).
