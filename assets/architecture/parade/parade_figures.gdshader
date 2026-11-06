shader_type spatial;
// PARADE FIGURES (Mode C) — owner: parade.  MultiMesh billboards for the massed troops, the crowd, guards,
// officials and dust puffs of L_M1_Parade (scripts/levels/parade/parade_set.gd), generated atlas
// assets/architecture/parade/figures.png (+ figures.json, tools/pixelgen/gen_parade.py).
// Per instance (MultiMesh, translation = feet position): INSTANCE_CUSTOM = (first slot, frame count,
// frame phase, flip + 2 * tone + 16 * group).  flip = mod(a, 2) > 0.5; tone 0..7 = albedo x TONE[tone] (variety in
// the crowd and inside a marching block), faded in only on figures >= ~16 px; group 0..7 = the colour a calmed far
// figure is pulled towards (CALM_COLS: 0 = a crowd of dark coats, the others = delegations in like coats).
// Pixel lock: the feet are projected, snapped to a whole viewport pixel and the quad is rebuilt in view space.
// The LOD strip (figure height 2..346 px, all drawn at 1 texel = 1 px) closest to the true projected height is
// chosen per instance (log error) among the strips that contain the instance's slots (lod_slots[i] = slots in
// strip i: the large strips only hold crowd, children and guards).
//   * figures below `smooth_min` px (and every figure while smooth_min is off, e.g. a pure sideways track where no
//     depth changes): every texel covers exactly k x k screen pixels, only the largest available strip may be
//     enlarged by an integer k;
//   * figures from `smooth_min` px up while the camera moves in depth: the chosen strip is scaled by
//     ph / strip height (0.87 .. 1.15, nearest texel), so a figure grows 1 px at a time instead of jumping
//     32 % when it crosses from one strip to the next.
// Band lock (`snap_band` > 0, shot p8 only): a figure is snapped relative to the anchor of its depth band (z cells of
// snap_band metres): anchor -> whole pixel, offset to the anchor -> whole pixel.  While the camera cranes, a whole
// band of a distant crowd then steps one pixel at once (it scrolls like a layer) instead of thousands of figures
// stepping one by one at their own moments (crawling static).
// Calm (`calm` > 0, shot p8 only): figures smaller than `calm_px` become flat silhouettes in the colour of their group
// (CALM_COLS[group], shaded per person by calm_shade x its tone); the top texel row -- the head -- is pale for the
// share `head_light` of them (a hat with snow on it, a light headscarf).  A far crowd, of which mostly heads are
// seen, then reads as a dark mass of like coats sprinkled with pale heads -- a block of a delegation as one patch --
// and not as coloured gravel that boils while the camera moves.
// Lit by the scene with the same quantised toon model as pixel3d_sprite.
// ROUGHNESS = flag 0.55 -> "people" band of pixel3d_post (no post outline: the atlas carries its own).
render_mode skip_vertex_transform, cull_disabled, specular_disabled;

uniform sampler2D atlas : source_color, filter_nearest, repeat_disable;
uniform vec2 atlas_size = vec2(1.0, 1.0);
uniform vec4 lods[24];               // (strip_y, cell_w, cell_h, figure_h) in atlas pixels
uniform float lod_slots[24];         // slots present in each strip (atlas order)
uniform int lod_count = 1;
uniform float height_m = 1.8;        // world height that maps to figure_h
uniform float time = 0.0;
uniform float fps = 2.0;
uniform float min_depth = 0.0;       // instances nearer than this (m) are hidden (camera inside the crowd)
uniform float max_scale = 3.0;
uniform float smooth_min = 1e9;      // px; figures at least this tall scale continuously (see above), 1e9 = off
uniform float flag = 0.55;
uniform float self_light = 0.0;
uniform float lift_slots = 0.0;      // instances whose slot is below this (the crowd) get `lift` extra self light:
uniform float lift = 0.0;            // the backs of the crowd face away from the floodlights
uniform float lift_far = 0.0;        // + lift * lift_far on small (far) crowd figures, so a distant crowd keeps coats
uniform float toon_steps = 5.0;
uniform float toon_max = 1.6;
uniform float toon_seam = 0.16;
uniform float snap_band = 0.0;       // m; > 0 = band lock (see above), 0 = every figure snaps on its own
uniform float calm = 0.0;            // 0..1 strength of the far calm (see above)
uniform float calm_px = 7.0;         // figures below this height (px) are calmed, fading in from 0.6 x calm_px down
uniform float calm_shade = 0.6;      // how much of the per-person tone survives in a calmed silhouette
uniform float head_light = 0.14;     // share of calmed figures with a pale head
uniform vec3 head_col = vec3(0.115, 0.11, 0.118);
// group colours of the far calm (linear): 0 dark coats, 1 grey-blue work coats, 2 brown, 3 black, 4 light coats
const vec3 CALM_COLS[8] = vec3[8](vec3(0.03, 0.027, 0.034), vec3(0.05, 0.068, 0.1), vec3(0.1, 0.055, 0.034),
	vec3(0.016, 0.013, 0.018), vec3(0.19, 0.18, 0.18), vec3(0.03, 0.027, 0.034), vec3(0.03, 0.027, 0.034),
	vec3(0.03, 0.027, 0.034));

const float TONE[8] = float[8](1.0, 0.74, 1.32, 0.56, 0.9, 1.12, 0.82, 1.2);    // linear albedo factors

varying flat float v_tone;
varying flat float v_lift;
varying flat float v_calm;
varying flat vec3 v_calm_col;
varying flat float v_strip_y;
varying flat float v_head;

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
	float last_slot = INSTANCE_CUSTOM.r + max(INSTANCE_CUSTOM.g, 1.0) - 1.0;
	int best = 0;
	int top = 0;
	float bk = 1.0;
	float berr = 1e9;
	for (int i = 0; i < lod_count; i++) {
		if (last_slot >= lod_slots[i] - 0.5) {
			continue;
		}
		top = i;
		float e = abs(log(lods[i].w / ph));
		if (e < berr) {
			berr = e;
			best = i;
		}
	}
	if (ph >= smooth_min) {
		bk = ph / lods[best].w;               // continuous: nearest texel, never more than ~15 % off 1:1
	} else if (best == top) {
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
	vec2 pf = (ndc * 0.5 + 0.5) * VIEWPORT_SIZE;
	vec2 base = floor(pf + 0.5);
	if (snap_band > 0.0) {
		vec3 an = vec3(feet.x, feet.y, (floor(feet.z / snap_band) + 0.5) * snap_band);
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
	if (depth < max(min_depth, 0.06)) {
		VERTEX = vec3(0.0, 0.0, 1.0);        // behind the camera -> clipped
	}
	NORMAL = vec3(0.0, 0.0, 1.0);
	float fl = mod(INSTANCE_CUSTOM.a + 0.25, 2.0) - 0.25;
	float u = fl > 0.5 ? 1.0 - UV.x : UV.x;
	int ti = int(mod(floor((INSTANCE_CUSTOM.a + 0.25) * 0.5), 8.0));
	v_tone = mix(1.0, TONE[ti], smoothstep(10.0, 22.0, ph));
	v_lift = INSTANCE_CUSTOM.r < lift_slots - 0.5 ? lift * (1.0 + lift_far * (1.0 - smoothstep(16.0, 44.0, ph))) : 0.0;
	v_calm = calm > 0.0 ? calm * (1.0 - smoothstep(calm_px * 0.6, calm_px, ph)) : 0.0;
	v_calm_col = CALM_COLS[clamp(int(floor((INSTANCE_CUSTOM.a + 0.25) / 16.0)), 0, 7)] * mix(1.0, TONE[ti], calm_shade);
	v_strip_y = L.x;
	v_head = fract(sin(dot(feet.xz, vec2(12.9898, 78.233))) * 43758.547) < head_light ? 1.0 : 0.0;
	UV = vec2((slot + u) * L.y, L.x + UV.y * L.z) / atlas_size;
}

void fragment() {
	vec4 t = texture(atlas, UV);
	vec3 a = t.rgb * v_tone;
	if (v_calm > 0.0) {
		vec3 cc = v_calm_col;
		if (v_head > 0.5 && UV.y * atlas_size.y - v_strip_y < 2.0) {
			cc = max(cc * 2.4, head_col);              // texel rows 0..1 of the cell: the head of a full-height figure
		}
		a = mix(a, cc, v_calm);
	}
	ALBEDO = a;
	ALPHA = t.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = flag;
	METALLIC = 0.0;
	SPECULAR = 0.0;
	if (self_light + v_lift > 0.0) {
		EMISSION = ALBEDO * (self_light + v_lift);
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
