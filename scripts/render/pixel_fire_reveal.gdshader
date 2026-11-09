shader_type canvas_item;
render_mode blend_add;
// Pixel fire kit (scripts/render/pixel_fire.gd): shows an ADDITIVE fire-light layer (a baked "lit minus unlit"
// image, a light pool) as a hard-pixel, ordered-dithered shape on the texture's own texel grid -- a pool that
// grows and breathes around `origin`, or a wipe.  No alpha ramps: a texel is either drawn or not.
//   d = length(max(abs(texel - origin) - core, 0) / reach)      0 inside the core box .. 1 at the rim
// core  = half extents of the fully lit box (0, 0 = a point, the pool is an ellipse of radii `reach`)
// reach = width of the falloff outside the core; soft = share of that falloff which is dithered (4x4 Bayer)
uniform vec2 origin = vec2(0.0, 0.0);
uniform vec2 core = vec2(0.0, 0.0);
uniform vec2 reach = vec2(64.0, 64.0);
uniform float soft : hint_range(0.0, 1.0) = 0.5;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void fragment() {
	vec2 px = floor(UV / TEXTURE_PIXEL_SIZE);
	vec2 q = max(abs(px + 0.5 - origin) - core, vec2(0.0)) / max(reach, vec2(0.001));
	ivec2 b = ivec2(mod(px, 4.0));
	float th = (BAYER[b.y * 4 + b.x] + 0.5) / 16.0;
	if (length(q) >= 1.0 - soft * th) {
		discard;
	}
}
