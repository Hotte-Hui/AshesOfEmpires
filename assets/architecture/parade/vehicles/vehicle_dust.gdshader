shader_type spatial;
// VEHICLE DUST (Mode C) — owner: parade.  Powder snow thrown off the tracks and cold exhaust vapour behind the
// armoured column of L_M1_Parade (scripts/levels/parade/parade_vehicles.gd, MultiMesh of 1 x 1 quads).
// Per instance: translation = ground point under the puff (world), INSTANCE_CUSTOM = (width m, height m,
// density 0..1, seed + 100 * kind) with kind 0 = snow dust (hugs the ground), 1 = exhaust vapour (a lifted wisp).
// The quad is rebuilt as a camera-facing billboard standing on that point.  Coverage is not blended: a value-noise
// density field is cut by a 4x4 Bayer matrix in screen pixels (the world renders at 640 x 360, 1 fragment =
// 1 game pixel), so a thin veil reads as a sparse dither the running gear shows through, a dense core as a
// solid clot -- the same idiom as the dithered fog and ground haze of pixel3d_post.
// ROUGHNESS = flag 0.95 -> "wires" band of pixel3d_post: the scattered dust pixels are never outlined and never
// cause outlines on what is behind them.  Lit by the scene with the quantised toon model of parade_figures.
render_mode skip_vertex_transform, cull_disabled, specular_disabled;

uniform vec4 dust_color : source_color = vec4(0.74, 0.72, 0.74, 1.0);
uniform vec4 dust_shade : source_color = vec4(0.54, 0.52, 0.57, 1.0);
uniform vec4 vapour_color : source_color = vec4(0.55, 0.55, 0.61, 1.0);
uniform float self_light = 0.4;
uniform float flag = 0.95;
uniform float toon_steps = 4.0;
uniform float toon_max = 1.6;
uniform float toon_seam = 0.16;

varying flat vec4 v_cd;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
		f.y);
}

void vertex() {
	v_cd = INSTANCE_CUSTOM;
	vec3 base = (VIEW_MATRIX * (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0))).xyz;
	vec3 up = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	up = normalize(vec3(0.0, up.y, 0.0) + vec3(up.x, 0.0, 0.0));
	vec3 right = vec3(up.y, -up.x, 0.0);
	VERTEX = base + right * ((UV.x - 0.5) * v_cd.x) + up * ((1.0 - UV.y) * v_cd.y);
	if (v_cd.z <= 0.0 || base.z > -0.1) {
		VERTEX = vec3(0.0, 0.0, 1.0);          // unborn / spent puff, or behind the camera -> clipped
	}
	NORMAL = vec3(0.0, 0.0, 1.0);
}

void fragment() {
	float kind = step(99.5, v_cd.w);
	float seed = v_cd.w - 100.0 * kind;
	vec2 p = vec2(UV.x * 2.0 - 1.0, 1.0 - UV.y);                  // x -1..1, y 0 (base) .. 1 (top)
	vec2 m = vec2(UV.x * v_cd.x, (1.0 - UV.y) * v_cd.y);          // metres on the billboard
	vec2 q = m * 3.2 + vec2(seed * 7.13, seed * 3.71);
	float n = 0.62 * vnoise(q) + 0.38 * vnoise(q * 2.3 + 11.0);
	// dust: a plume thrown up behind the sprocket, densest a third of the way up, settling onto the snow;
	// vapour: an ellipse lifted off its base point
	vec2 e = kind > 0.5 ? vec2(p.x, (p.y - 0.5) * 2.0) : vec2(p.x, (p.y - 0.32) * 1.5);
	float r = length(e) + (n - 0.5) * 0.85;
	float shape = 1.0 - smoothstep(0.15, 0.85, r);
	// no lone sparkles at the thin rim: coverage starts at a small floor and is re-stretched above it
	float d = (v_cd.z * shape * (0.5 + 0.9 * n) - 0.08) * 1.2;
	if (d < bayer4(FRAGCOORD.xy)) {
		discard;
	}
	vec3 col = kind > 0.5 ? vapour_color.rgb : mix(dust_shade.rgb, dust_color.rgb, clamp(p.y * 1.4 + n * 0.5, 0.0, 1.0));
	ALBEDO = col;
	ROUGHNESS = flag;
	METALLIC = 0.0;
	SPECULAR = 0.0;
	EMISSION = col * self_light;
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
