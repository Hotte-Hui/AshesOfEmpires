# Art direction — anchored to supplied images

## Non-negotiable
The user's uploaded BUNKER-style references define the intended artistic character. Treat them as **style references**, not as assets to redistribute or copy. Build original compositions.

## Observations from visible references
1. Dark ceremonial interior: very deep navy/teal blacks; dense small-pixel masonry and mural detail; isolated warm copper lighting; crowds as small silhouettes; near-symmetrical composition.
2. Orange monumental facade: dusty terracotta/ochre sky and architecture; strongly simplified silhouettes at distance; dark smoke ribbons; stacked city layers; tiny people and vehicles for scale.
3. Pale industrial wasteland: desaturated sage-green sky; flat side-on perspective; partially ruined factories; vintage vehicle at foreground edge; sparse vegetation and road rubble.
4. Cropped facade/street layer: foreground elevated infrastructure with deep shadows; small people, tram/vehicle silhouettes; backlit architecture.

## Pixel-art production rules
- Define a reference pixel grid and camera scale per scene; do not allow inconsistent sprite texel density.
- Favor deliberate clusters, selective outlines and restrained dithering; avoid indiscriminate noise.
- Use nearest-neighbor for intended pixel layers and test temporal stability under camera movement.
- Pixelation must be authored or controlled in a coherent pipeline; 4K display output does not imply native 4K pixel detail.
- Use restrained color palettes per location with shared shadow hues and controlled warm highlights.
- Layer silhouettes into foreground, midground and background to convey depth.
- Keep readable interaction hotspots even in dark scenes.

## Palette proposals (starting points, not sampled measurements)
Soviet dusk: #071720 #203638 #53665B #91A68C #BA775B #DCA16E
Berlin sunset: #1A2530 #443B43 #805A52 #B67A57 #E6A36A #F5C18A
Interior: #06151D #14272B #354448 #805C4E #B57B59

## UE5 look-dev experiments
A. Native sprite + Paper2D 2D composition.
B. Orthographic 3D architecture with stylized low-frequency material shading.
C. Pixel-grid postprocess at fixed internal resolution and integer scaling.
D. Compare temporal stability with TAA/TSR, motion blur, Lumen and hardware RT enabled/disabled; reject features that break pixel clarity.
E. Test lighting fidelity in static screenshots **and** moving-camera capture.

## Screenshot approval gates
- Soviet street: matching atmosphere, strong depth, clear pixel clusters, no shimmering, legible character.
- Berlin Great Hall: overwhelming scale without ideological glorification; consistent pixels, convincing interior/exterior lighting, no 3D style mismatch.
- Character switch: coherent transition from 2.5D to side-on/3D without a sudden change in visual language.
