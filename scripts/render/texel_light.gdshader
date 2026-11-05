shader_type canvas_item;
// Per-texel 2D lighting for (translucent) pixel-art sprites in the high-resolution world path
// (owner: render-camera). Normal alpha blending; see pixel_sprite.gdshader for opaque sprites.
#include "res://scripts/render/texel_light.gdshaderinc"

void fragment() {
	LIGHT_VERTEX.xy = texel_light_vertex(UV, TEXTURE_PIXEL_SIZE, VERTEX, LIGHT_VERTEX.xy);
}
