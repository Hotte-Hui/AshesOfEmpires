shader_type spatial;
// PARADE FIGURES (Mode C) — owner: parade.  MultiMesh billboards for the massed troops, the crowd, guards,
// officials and dust puffs of L_M1_Parade (scripts/levels/parade/parade_set.gd), generated atlas
// assets/architecture/parade/figures.png (+ figures.json, tools/pixelgen/gen_parade.py).
// Per instance (MultiMesh, translation = feet position): INSTANCE_CUSTOM = (first slot, frame count,
// frame phase, flip > 0.5).
// Pixel lock: the feet are projected, snapped to a whole viewport pixel and the quad is rebuilt in view space so
// every texel covers exactly k x k screen pixels.  The LOD strip (figure height 2..104 px) closest to the true
// projected height is chosen per instance (log error); only the largest strip may be enlarged by an integer k
// (foreground silhouettes).  Lit by the scene with the same quantised toon model as pixel3d_sprite.
// ROUGHNESS = flag 0.55 -> "people" band of pixel3d_post (no post outline: the atlas carries its own).
render_mode skip_vertex_transform, cull_disabled, specular_disabled;

uniform sampler2D atlas : source_color, filter_nearest, repeat_disable;
uniform vec2 atlas_size = vec2(1.0, 1.0);
uniform vec4 lods[16];               // (strip_y, cell_w, cell_h, figure_h) in atlas pixels
uniform int lod_count = 1;
uniform float height_m = 1.8;        // world height that maps to figure_h
uniform float time = 0.0;
uniform float fps = 2.0;
uniform float min_depth = 0.0;       // instances nearer than this (m) are hidden (camera inside the crowd)
uniform float max_scale = 3.0;
uniform float flag = 0.55;
uniform float self_light = 0.0;
uniform float toon_steps = 5.0;
uniform float toon_max = 1.6;
uniform float toon_seam = 0.16;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

void vertex() {
	vec3 feet = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 fv = (VIEW_MATRIX * vec4(feet, 1.0)).xyz;
	float depth = -fv.z;
	// render targets may be y-flipped (negative [1][1]): sizes use |f|, screen-up follows the sign
	float sy = PROJECTION_MATRIX[1][1] < 0.0 ? -1.0 : 1.0;
	float focal = 0.5 * VIEWPORT_SIZE.y * abs(PROJECTION_MATRIX[1][1]);
	float ph = height_m * focal / max(depth, 0.001);
	int best = 0;
	float bk = 1.0;
	float berr = 1e9;
	for (int i = 0; i < lod_count; i++) {
		float e = abs(log(lods[i].w / ph));
		if (e < berr) {
			berr = e;
			best = i;
		}
	}
	if (best == lod_count - 1) {
		for (float k = 2.0; k <= max_scale; k += 1.0) {
			float e = abs(log(lods[best].w * k / ph));
			if (e < berr) {
				berr = e;
				bk = k;
			}
		}
	}
	vec4 L = lods[best];
	float frames = max(INSTANCE_CUSTOM.g, 1.0);
	float slot = INSTANCE_CUSTOM.r + mod(floor(time * fps + INSTANCE_CUSTOM.b), frames);
	vec4 clip = PROJECTION_MATRIX * vec4(fv, 1.0);
	vec2 ndc = clip.xy / clip.w;
	vec2 base = floor((ndc * 0.5 + 0.5) * VIEWPORT_SIZE + 0.5);
	float ax = floor(L.y * 0.5);
	float ay = L.w + 1.0;
	vec2 cp = vec2(UV.x * L.y - ax, (ay - UV.y * L.z) * sy) * bk;
	vec2 ndc2 = (base + cp) / VIEWPORT_SIZE * 2.0 - 1.0;
	vec4 v = INV_PROJECTION_MATRIX * vec4(ndc2, clip.z / clip.w, 1.0);
	VERTEX = v.xyz / v.w;
	if (depth < max(min_depth, 0.06)) {
		VERTEX = vec3(0.0, 0.0, 1.0);        // behind the camera -> clipped
	}
	NORMAL = vec3(0.0, 0.0, 1.0);
	float u = INSTANCE_CUSTOM.a > 0.5 ? 1.0 - UV.x : UV.x;
	UV = vec2((slot + u) * L.y, L.x + UV.y * L.z) / atlas_size;
}

void fragment() {
	vec4 t = texture(atlas, UV);
	ALBEDO = t.rgb;
	ALPHA = t.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = flag;
	METALLIC = 0.0;
	SPECULAR = 0.0;
	if (self_light > 0.0) {
		EMISSION = ALBEDO * self_light;
	}
}

void light() {
	vec3 lc = LIGHT_COLOR / PI;
	float lum = max(dot(lc, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
	float I = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0) * ATTENUATION * lum;
	float x = sqrt(clamp(I / toon_max, 0.0, 1.0)) * toon_steps;
	float f = fract(x);
	float up = step(bayer4(FRAGCOORD.xy), clamp((f - 0.5) / toon_seam + 0.5, 0.0, 1.0));
	float lv = min(floor(x) + up, toon_steps) / toon_steps;
	DIFFUSE_LIGHT += lc * (lv * lv * toon_max / lum);
}
