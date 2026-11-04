shader_type spatial;
// PIXEL-3D TOON SURFACE (Mode C) — owner: great_hall_3d.
// Quantised ("toon") lighting with a narrow Bayer-dithered seam between the 4–5 light steps, so dynamic
// light reads like hand-dithered pixel shading.  Everything is later palette-snapped by pixel3d_post.
//  * albedo  = uniform tint × vertex colour (linear; meshes are built with sRGB->linear colours)
//  * UV2.x   = per-vertex emission amount (lit windows, lamp lenses) — 0 for normal surfaces
//  * snow    = settles on up-facing surfaces (world normal), with dithered border
//  * course  = optional horizontal stone-course joints (world space, fades out before it can alias)
//  * flag    = written to ROUGHNESS -> material flag for the post process (see pixel3d_post)
render_mode cull_back, specular_disabled;

uniform vec4 albedo : source_color = vec4(1.0);
uniform bool use_vertex_color = true;
uniform sampler2D albedo_tex : source_color, filter_nearest_mipmap, repeat_enable, hint_default_white;
uniform bool use_tex = false;
uniform float alpha_scissor = 0.0;          // > 0: texture alpha below this is discarded
uniform vec4 emission_color : source_color = vec4(0.97, 0.82, 0.63, 1.0);
uniform float emission_energy = 1.0;
uniform bool emission_from_albedo = true;   // lit windows glow in their own (vertex) colour
uniform float snow = 0.0;
uniform vec4 snow_color : source_color = vec4(0.925, 0.902, 0.878, 1.0);
uniform float snow_threshold = 0.72;
uniform float course = 0.0;                  // metres between stone courses (0 = off)
uniform float course_dark = 0.82;
uniform float toon_steps = 5.0;             // number of lit levels (perceptual, sqrt-spaced)
uniform float toon_max = 1.6;               // light intensity (luminance) mapped to the top level
uniform float toon_seam = 0.16;              // fraction of a step that is dithered
uniform float light_wrap = 0.0;              // >0 softens the terminator (cloth, snow)
uniform float rim = 0.0;                     // back-light rim from directional lights
uniform float rim_threshold = 0.55;
uniform vec4 rim_color : source_color = vec4(1.0, 0.72, 0.45, 1.0);
uniform float flag = 0.0;

varying vec3 v_world_pos;
varying vec3 v_world_nrm;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

// Quantise a light INTENSITY (luminance incl. energy and attenuation) to a few levels.  The levels are
// spaced on a sqrt curve so dim fills and strong floods both land on visible steps; the seam between two
// levels is a narrow ordered-dither band.
float toon_q(float I, vec2 frag) {
	float x = sqrt(clamp(I / toon_max, 0.0, 1.0)) * toon_steps;
	float f = fract(x);
	float up = step(bayer4(frag), clamp((f - 0.5) / max(toon_seam, 0.001) + 0.5, 0.0, 1.0));
	float lv = min(floor(x) + up, toon_steps) / toon_steps;
	return lv * lv * toon_max;
}

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 c = albedo.rgb;
	if (use_vertex_color) {
		c *= COLOR.rgb;
	}
	if (use_tex) {
		vec4 t = texture(albedo_tex, UV);
		c *= t.rgb;
		if (alpha_scissor > 0.0) {
			ALPHA = t.a;
			ALPHA_SCISSOR_THRESHOLD = alpha_scissor;
		}
	}
	vec2 frag = FRAGCOORD.xy;
	if (course > 0.0) {
		float y = v_world_pos.y / course;
		float w = fwidth(y);
		if (w < 0.22 && fract(y) < w) {
			c *= course_dark;
		}
	}
	if (snow > 0.0) {
		float up = normalize(v_world_nrm).y;
		float s = smoothstep(snow_threshold, snow_threshold + 0.12, up) * snow;
		if (s > bayer4(frag)) {
			c = snow_color.rgb;
		}
	}
	ALBEDO = c;
	ROUGHNESS = flag;
	METALLIC = 0.0;
	SPECULAR = 0.0;
	float em = UV2.x;
	if (em > 0.0) {
		vec3 ec = emission_from_albedo ? c : emission_color.rgb;
		EMISSION = ec * em * emission_energy;
	}
}

void light() {
	vec3 lc = LIGHT_COLOR / PI;
	float lum = max(dot(lc, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
	float ndl = (dot(NORMAL, LIGHT) + light_wrap) / (1.0 + light_wrap);
	float I = clamp(ndl, 0.0, 1.0) * ATTENUATION * lum;
	DIFFUSE_LIGHT += lc * (toon_q(I, FRAGCOORD.xy) / lum);
	if (rim > 0.0 && LIGHT_IS_DIRECTIONAL) {
		float fres = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		float back = clamp(-dot(VIEW, LIGHT), 0.0, 1.0);
		float side = clamp(dot(NORMAL, LIGHT) + 0.35, 0.0, 1.0);
		float r = step(rim_threshold, fres * back * side);
		SPECULAR_LIGHT += r * rim * rim_color.rgb * LIGHT_COLOR / PI;
	}
}
