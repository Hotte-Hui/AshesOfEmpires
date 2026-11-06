shader_type spatial;
// AVENUE FIGURES (Mode C) — owner: hall (great_hall_3d).  MultiMesh billboards for the avenue staging layer
// (scripts/levels/hall/hall_avenue.gd): cordon guards, waiting and marching infantry, work crews, civilians held
// back at the barriers, crows and vapour.  Atlas assets/architecture/great_hall/avenue/avenue_figures.png
// (+ .json, tools/pixelgen/gen_great_hall_avenue.py).  Same pixel-lock model as the parade's figure shader
// (kept as an independent copy so both layers can evolve separately):
// Per instance (MultiMesh, translation = feet position): INSTANCE_CUSTOM = (first slot, frame count,
// frame phase, flip > 0.5).
// Pixel lock: the feet are projected, snapped to a whole viewport pixel and the quad is rebuilt in view space so
// every texel covers exactly k x k screen pixels.  The LOD strip closest to the true projected height is chosen
// per instance (log error); only the largest strip may be enlarged by an integer k.
// Vapour mode (rise_h > 0): every instance runs a loop of `period` seconds (offset = phase): it rises by rise_h,
// drifts by drift (m) and steps through its frames once per loop (the puff grows and dissolves).
// Band lock (`snap_band` > 0): a figure is snapped relative to the anchor of its depth band (z cells of snap_band
// metres, measured from `snap_origin`, the current offset of a moving node such as the marching column): anchor ->
// whole pixel, offset to the anchor -> whole pixel, so a band of figures steps one pixel at once while the camera
// cranes (no crawling static) and a moving block slides as one body.
// Calm (`calm` > 0): figures smaller than `calm_px` become flat silhouettes in `calm_col` (far civilians and troops
// read as dark coats, not as coloured gravel that boils while the camera moves).
// ROUGHNESS = flag 0.55 -> "people" band of pixel3d_post (no post outline: the atlas carries its own).
render_mode skip_vertex_transform, cull_disabled, specular_disabled;

uniform sampler2D atlas : source_color, filter_nearest, repeat_disable;
uniform vec2 atlas_size = vec2(1.0, 1.0);
uniform vec4 lods[16];               // (strip_y, cell_w, cell_h, figure_h) in atlas pixels
uniform int lod_count = 1;
uniform float height_m = 1.8;        // world height that maps to figure_h
uniform float time = 0.0;
uniform float fps = 2.0;
uniform float max_scale = 3.0;
uniform float flag = 0.55;
uniform float self_light = 0.0;
uniform float rise_h = 0.0;
uniform float period = 3.0;
uniform vec3 drift = vec3(0.0);
uniform float toon_steps = 5.0;
uniform float toon_max = 1.6;
uniform float toon_seam = 0.16;
uniform float snap_band = 0.0;       // m; > 0 = band lock (see above)
uniform vec3 snap_origin = vec3(0.0);
uniform float calm = 0.0;
uniform float calm_px = 7.0;
uniform vec3 calm_col = vec3(0.032, 0.03, 0.036);

varying flat float v_calm;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

void vertex() {
	vec3 feet = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float frames = max(INSTANCE_CUSTOM.g, 1.0);
	float frame = mod(floor(time * fps + INSTANCE_CUSTOM.b), frames);
	if (rise_h > 0.0) {
		float u = fract((time + INSTANCE_CUSTOM.b) / max(period, 0.01));
		feet += vec3(0.0, u * rise_h, 0.0) + drift * u;
		frame = min(floor(u * frames), frames - 1.0);
	}
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
	float slot = INSTANCE_CUSTOM.r + frame;
	vec4 clip = PROJECTION_MATRIX * vec4(fv, 1.0);
	vec2 ndc = clip.xy / clip.w;
	vec2 pf = (ndc * 0.5 + 0.5) * VIEWPORT_SIZE;
	vec2 base = floor(pf + 0.5);
	if (snap_band > 0.0 && rise_h <= 0.0) {
		float zl = feet.z - snap_origin.z;
		vec3 an = vec3(feet.x, feet.y, snap_origin.z + (floor(zl / snap_band) + 0.5) * snap_band);
		vec4 ca = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(an, 1.0));
		if (ca.w > 0.05) {
			vec2 pa = (ca.xy / ca.w * 0.5 + 0.5) * VIEWPORT_SIZE;
			base = floor(pa + 0.5) + floor(pf - pa + 0.5);
		}
	}
	float ax = floor(L.y * 0.5);
	float ay = L.w + 1.0;
	vec2 cp = vec2(UV.x * L.y - ax, (ay - UV.y * L.z) * sy) * bk;
	vec2 ndc2 = (base + cp) / VIEWPORT_SIZE * 2.0 - 1.0;
	vec4 v = INV_PROJECTION_MATRIX * vec4(ndc2, clip.z / clip.w, 1.0);
	VERTEX = v.xyz / v.w;
	if (depth < 0.06) {
		VERTEX = vec3(0.0, 0.0, 1.0);        // behind the camera -> clipped
	}
	NORMAL = vec3(0.0, 0.0, 1.0);
	float u = INSTANCE_CUSTOM.a > 0.5 ? 1.0 - UV.x : UV.x;
	v_calm = calm > 0.0 ? calm * (1.0 - smoothstep(calm_px * 0.6, calm_px, ph)) : 0.0;
	UV = vec2((slot + u) * L.y, L.x + UV.y * L.z) / atlas_size;
}

void fragment() {
	vec4 t = texture(atlas, UV);
	vec3 a = t.rgb;
	a = mix(a, calm_col, v_calm);
	ALBEDO = a;
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
