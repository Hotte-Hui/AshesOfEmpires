# Rendering acceptance plan v0.4 — UE5 lookdev, **not yet executed in UE5**

## Target is the visual *language*, not maximum feature toggles
The four supplied references use deliberate pixel clusters, broad tonal grouping, readable dark silhouettes, compressed color palettes, extreme monumental scale, atmospheric haze, selective highlights and hand-composed architecture. They are **third-party artworks of unknown license status**; production content must be original. UE5 is chosen for flexibility in 3D lighting, camera composition and scene construction, not because an RTX 4090 automatically yields better pixel art.

## Technical decision record
- **Pipeline A, foreground/characters:** author low-resolution sprite sheets or 3D-to-sprite renders with hand correction. Test nearest-neighbor at exact pixel multiples and camera-space snap.
- **Pipeline B, middle-ground:** modular 3D masses with large stylized light groups and selectively textured sprites. Test orthographic/low-FOV perspective cameras for side views and 2.5D traversal.
- **Pipeline C, background/landmarks:** physically modeled monumental forms with custom shading or depth-aware pixel treatment. For 3D movement, avoid a naive screen-space pixelation pass that shimmers under movement.
- **UI:** native-resolution UMG typography and vector/SDF icons; **never** downsample accessible text along with world imagery.
- Treat Lumen, Nanite and RT as **AB test candidates**, not unconditional requirements. The winning method is measured visual quality **with temporal stability**.

## Fixed test matrix (capture at 3840×2160 **output**, log actual rendering resolution)
Use **one** reference camera in `L_A1_Railyard` and **one** in `L_M1_Archive`; set deterministic day phase and scene time. Same composition under all variants.

| ID | Scene | Internal logical pixel grid | Anti-aliasing | Geometry lighting | Gate |
|---|---|---|---|---|---|
| A0 | Karsk | 320×180 | none | unlit + fixed baked palette | crisp sprite baseline |
| A1 | Karsk | 640×360 | none / FXAA | hybrid 3D + manual shade | parallax and legible outlines |
| A2 | Karsk | 960×540 | TAA / TSR separately | hybrid 3D + Lumen candidate | evaluate thin detail, smoke and ghosting |
| B0 | Berlin | 640×360 | none | stage-painted 3D | foreground characters readable |
| B1 | Berlin | 960×540 | TSR candidate | 3D + GI candidate | building looks imposed, not celebrated |
| B2 | Berlin | native UHD reference | TSR / off | architecture 3D + pixel-filter candidate | prove intentional stylization |

Logical grid is **not** the same as Screen Percentage; preserve a screenshot of each render path for comparison. 4K=3840×2160 gives integer upscale multiples of 12 for 320×180, 6 for 640×360, 4 for 960×540. At 2560×1440 re-evaluate the target grid; use aspect-ratio safe bars if necessary.

## Temporal testing (mandatory before scene approval)
1. Capture a still and a 10-second slow pan plus a 10-second fast pan at every tested setting; note camera FOV, exposure, AA, temporal history reset and exact engine build.
2. Use same character silhouette, smokestack plume, thin railing and illuminated window patterns in both scenes.
3. **Fail** a variant for repeated one-pixel crawling, ghost silhouettes during movement, unreadable task markers, color clipping, or scene changes that reset exposure visibly. Fix cause before increasing sharpening.
4. Record `stat unit`, `stat gpu`, Unreal Insights/GPU Visualizer where supported; export uncropped frame-time samples. A screenshot **does not** demonstrate 60 fps.
5. Test from a fresh Windows package, not only editor. Hardware RTX 4090 target: 60 fps at UHD is **aspirational** and not verified. Report P50/P95/P99 frame times and 1% lows once tested; set a budget only after baseline.
6. Separate benchmark captures from approved production visuals in `evidence/`, labelled `scene_variant_engineversion_camera_date`, with `README` metadata.

## Explicit handoff constraints
- Reference pixel dimensions and palette sizes are **observations**, not permission to reuse their imagery. No copying composition-specific propaganda artwork.
- Graybox two scenes before city-scale assets. Approval = reference similarity + readability + stability, not highest polycount.
- If camera and world pixel scale cannot be reconciled, reduce movement freedom locally or hand-author key frames rather than forcing a global post-process effect.
- Distinguish `tested in Python`, `tested in browser`, `UE5 code compiled`, `UE5 PIE`, `packaged build` and `playtested by user` in reports.

## Official reading (verify installed UE version)
- Paper2D: https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-overview-in-unreal-engine
- TSR and temporal upscalers: https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-upscalers-in-unreal-engine
- TSR FAQs and ghosting/post-process limitations: https://dev.epicgames.com/documentation/unreal-engine/temporal-super-resolution-frequently-asked-questions-for-unreal-engine
- Lumen details: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine
