shader_type canvas_item;
// World post-process at logical pixel resolution (inside the 642x362 SubViewport).
// Grade (lift/gamma/gain, saturation, tint), dithered vignette, optional palette snap with 4x4 Bayer
// ordered dithering (keeps dynamic 2D light gradients looking hand-dithered), pixel-stable grain, fade.

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform vec3 lift = vec3(0.0);
uniform vec3 gamma = vec3(1.0);
uniform vec3 gain = vec3(1.0);
uniform float saturation = 1.0;
uniform vec3 tint = vec3(1.0);
uniform float vignette = 0.22;
uniform float grain = 0.0;          // 0..0.08 ; animated at low rate by `grain_seed`
uniform float grain_seed = 0.0;
uniform float palette_strength = 0.0;
uniform int palette_size = 0;
uniform vec3 palette[64];
uniform vec4 fade_color : source_color = vec4(0.0, 0.0, 0.0, 0.0);

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 frag) {
	ivec2 p = ivec2(mod(floor(frag), 4.0));
	return (BAYER[p.y * 4 + p.x] + 0.5) / 16.0;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233)) + grain_seed * 17.17) * 43758.5453);
}

void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float th = bayer4(FRAGCOORD.xy);
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
	// vignette (dithered so it stays pixel-art)
	vec2 q = SCREEN_UV - 0.5;
	float v = clamp(dot(q, q) * 2.2 * vignette, 0.0, 1.0);
	c *= 1.0 - v + (th - 0.5) * v * 0.35;
	// grain
	if (grain > 0.0) {
		c += (hash(floor(FRAGCOORD.xy)) - 0.5) * grain;
	}
	c = mix(c, fade_color.rgb, fade_color.a);
	COLOR = vec4(c, 1.0);
}
