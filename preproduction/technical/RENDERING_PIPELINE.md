# UE5 rendering research plan — pixel art first

**Decision:** Unreal Engine 5 is the target. This is a look-development specification, not an assertion that shaders or assets already exist.

## Rendering tracks to compare
1. **2D native:** Paper2D sprites, orthographic camera, hand-authored parallax layers, unlit or carefully lit materials.
2. **2.5D hybrid:** 3D architecture and lighting with camera-constrained framing; pixel-art characters on camera-facing planes only where perspective remains convincing.
3. **Pixel-styled 3D:** modeled architectural masses with custom stylized materials, controlled color quantization, optional post-process pixelation, and deliberate pixel edge handling.

## Critical technical risks
- **Pixel shimmer:** camera motion + TAA/TSR jitter + subpixel sprite placement. Test integer-grid snapping for sprites, alternative antialiasing paths, fixed-camera resolutions, and camera smoothing separately.
- **Lumen / RT:** physically rich lighting may introduce unstable high-frequency noise or break deliberate pixel clusters. Evaluate against a simpler lighting baseline; do not enable every feature by default.
- **Nanite:** use for genuinely complex architectural meshes if beneficial, not as a blanket requirement for flat sprite layers.
- **Volumetric fog:** can wash out silhouette readability; use depth-aware and art-directed fog.
- **4K output:** test 1080p and 4K display targets with a chosen logical pixel scale; no promise of universal integer scaling at arbitrary aspect ratios.
- **Perspective changes:** define a consistent world scale, shared color grading, character size targets, UI scale, and shot-to-shot lighting continuity.

## Experiment matrix
| Test | Scene | Variant | Pass condition |
|---|---|---|---|
| P01 | Soviet street | Paper2D parallax | No crawl in a 10-second pan |
| P02 | Soviet street | Orthographic 3D | Characters remain readable while moving |
| P03 | Great Hall | Lumen on/off | Compare mood, stability and performance |
| P04 | Great Hall | Nanite on/off where supported | No needless complexity or regressions |
| P05 | Rain | Temporal methods on/off | No objectionable streaking or ghosting |
| P06 | Transition | 2D to 2.5D | Same palette, coherent pixel scale |
| P07 | Transition | 2.5D to 3D | No abrupt photorealistic mismatch |

## Captures required for each test
- Native resolution screenshot, same framing and exposure.
- 10-second moving-camera capture, same route.
- FPS, GPU frame time, VRAM estimate and UE version, measured not guessed.
- Short decision log: keep, revise, reject, with visual reason.

## Target vs. minimum
Target machine: RTX 4090, 32 GB RAM. Do not infer minimum requirements from this machine. Establish quality presets after profiling. Set 60 FPS as an *aspirational* performance target for the selected vertical-slice scene, not an unverified promise.
