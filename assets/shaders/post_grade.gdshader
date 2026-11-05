shader_type canvas_item;
// World post-process. Low-res path: full-viewport ColorRect on CanvasLayer 100 inside the World SubViewport
// (reads the screen). Hi-res path: TextureRect in the Graded SubViewport showing the raw World texture
// (from_texture = true, reads TEXTURE incl. the alpha dither codes - hint_screen_texture copies force alpha 1).
// Works at any render scale: `px_scale` = viewport pixels per world pixel (k = 3/4/6 in the high-resolution 2D
// path, 1 in the 642x362 path). Every pixel-art-scale effect stays on the 640x360 world grid:
//  * palette snap FIRST, with 4x4 Bayer ordered dither. The threshold is chosen per WORLD texel and anchored to
//    the playfield (`dither_origin` = camera top-left in viewport px, set every frame by PixelView), so the
//    dither of light gradients sticks to the world while the camera glides in single screen pixels and every
//    playfield texel stays one uniform k x k block (no 1-px slivers).
//    Painted pixels are already on-palette -> unchanged; dynamic light gradients get hand-dithered.
//  * grade (lift/gamma/gain, saturation, tint)
//  * dithered vignette and grain on the same playfield-anchored world-pixel cells (grain re-rolled at a low
//    rate via `grain_seed`), fade. In the 642x362 path px_scale = 1 and dither_origin = 0 (old behaviour).
// Uniform names lift..fade_color are the contract with Game._apply_grade(); px_scale/dither_origin/grain_seed
// belong to scripts/render/pixel_view.gd.

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform vec3 lift = vec3(0.0);
uniform vec3 gamma = vec3(1.0);
uniform vec3 gain = vec3(1.0);
uniform float saturation = 1.0;
uniform vec3 tint = vec3(1.0);
uniform float vignette = 0.22;
uniform float grain = 0.0;          // 0..0.08
uniform float grain_seed = 0.0;
uniform float palette_strength = 0.0;
uniform int palette_size = 0;
uniform vec3 palette[64];
uniform vec4 fade_color : source_color = vec4(0.0, 0.0, 0.0, 0.0);
uniform float px_scale = 1.0;       // viewport px per world px
uniform vec2 dither_origin = vec2(0.0);   // world-anchoring offset of the palette dither (viewport px)
uniform vec2 dither_shift = vec2(0.0);    // test hook: extra offset of the dither phase in world texels
uniform int debug_view = 0;               // 1: dither threshold used, 2: raw framebuffer alpha (codes)
uniform bool from_texture = false;        // true: post stage outside the world viewport, reads TEXTURE (the
                                          // raw world incl. alpha codes); false: in-viewport, reads the screen

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 cell) {
	ivec2 p = ivec2(mod(cell, 4.0));
	return (BAYER[p.y * 4 + p.x] + 0.5) / 16.0;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233)) + grain_seed * 17.17) * 43758.5453);
}

void fragment() {
	vec4 src = from_texture ? texture(TEXTURE, UV) : texture(screen_tex, SCREEN_UV);
	vec3 c = src.rgb;
	float k = max(px_scale, 1.0);
	vec2 world_cell = floor((FRAGCOORD.xy + dither_origin) / k);   // playfield texel under this pixel
	// Threshold: the texel-anchored code written by scripts/render/pixel_sprite.gdshader (0.02 < alpha < 0.97),
	// else (other materials, empty background) the playfield-anchored Bayer value.
	bool coded = src.a > 0.02 && src.a < 0.97;
	float th = coded ? clamp(src.a / 0.9, 0.0, 1.0) : bayer4(world_cell + dither_shift);

	// palette snap FIRST (painted pixels are already on-palette -> unchanged; light gradients get dithered)
	if (palette_strength > 0.0 && palette_size > 1) {
		float d1 = 1e9; float d2 = 1e9; vec3 c1 = c; vec3 c2 = c;
		for (int i = 0; i < 64; i++) {
			if (i >= palette_size) { break; }
			vec3 p = palette[i];
			vec3 dd = (c - p) * vec3(0.30, 0.59, 0.11) * 3.0;
			float d = dot(dd, dd) + dot(c - p, c - p) * 0.25;
			if (d < d1) { d2 = d1; c2 = c1; d1 = d; c1 = p; }
			else if (d < d2) { d2 = d; c2 = p; }
		}
		float t = sqrt(d1) / (sqrt(d1) + sqrt(d2) + 1e-5);
		vec3 snapped = (t > th * 0.5) ? c2 : c1;
		c = mix(c, snapped, palette_strength);
	}
	// grade
	c = c * gain + lift * (vec3(1.0) - c);
	c = pow(max(c, vec3(0.0)), vec3(1.0) / max(gamma, vec3(0.01)));
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(vec3(l), c, saturation) * tint;
	// vignette (evaluated at the texel centre and dithered per world texel so it stays pixel-art)
	vec2 q = ((world_cell + 0.5) * k - dither_origin) * SCREEN_PIXEL_SIZE - 0.5;   // same size in both stages
	float v = clamp(dot(q, q) * 2.2 * vignette, 0.0, 1.0);
	c *= 1.0 - v + (th - 0.5) * v * 0.35;
	// grain (one value per world texel; the hash cell index is kept small for float precision)
	if (grain > 0.0) {
		c += (hash(mod(world_cell, 1024.0)) - 0.5) * grain;
	}
	c = mix(c, fade_color.rgb, fade_color.a);
	if (debug_view == 1) {
		c = vec3(th);
	} else if (debug_view == 2) {
		c = vec3(src.a);
	}
	COLOR = vec4(c, 1.0);
}
