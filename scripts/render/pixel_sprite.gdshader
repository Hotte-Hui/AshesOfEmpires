shader_type canvas_item;
// Opaque pixel-art sprite material for the high-resolution world path (owner: render-camera).
//  1. Per-texel 2D lighting (texel_light.gdshaderinc).
//  2. Texel-anchored dither code: drawn without blending (texels with alpha < 0.5 are discarded), the sprite
//     writes the 4x4 Bayer threshold of ITS OWN texel into the framebuffer alpha; post_grade.gdshader uses it,
//     so the palette-snap dither sticks to every layer's / actor's texels: no dither crawl on parallax layers
//     during pans, no 1-px slivers on actors between world pixels. Framebuffer alpha >= 0.97 = "no code"
//     (other materials) -> the post falls back to its playfield-anchored Bayer.
// Colour, texture, normal map and modulate RGB are untouched. Only for opaque sprites (TexelLight decides).
render_mode blend_disabled;
#include "res://scripts/render/texel_light.gdshaderinc"

instance uniform vec2 dither_anchor = vec2(0.0);  // world texel of texture (0, 0): same phase as the playfield
instance uniform vec2 dither_cell = vec2(0.0);    // sheet cell size in texels (0 = whole texture)

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void fragment() {
	if (COLOR.a < 0.5) {
		discard;
	}
	LIGHT_VERTEX.xy = texel_light_vertex(UV, TEXTURE_PIXEL_SIZE, VERTEX, LIGHT_VERTEX.xy);
	vec2 cell = floor(UV / TEXTURE_PIXEL_SIZE);
	if (dither_cell.x > 0.0) {
		cell = mod(cell, dither_cell);
	}
	ivec2 p = ivec2(mod(cell + dither_anchor, 4.0));
	COLOR.a = (BAYER[p.y * 4 + p.x] + 0.5) / 16.0 * 0.9;     // 16 levels in 0.03 .. 0.87
}
