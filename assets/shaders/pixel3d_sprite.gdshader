shader_type spatial;
// PIXEL-3D SPRITE (Mode C) — owner: great_hall_3d.
// Pixel-art people inside the 3D render: alpha-scissored, nearest-sampled, Y-billboarded quads lit by the
// same toon light model as the architecture (optional sprite normal map so lamps wrap around figures).
// The level script keeps every sprite at exactly 1 texel = 1 screen pixel and on whole screen pixels.
// flag 0.55 -> "people": the post process does not add outlines (sprites carry their own).
render_mode cull_disabled, specular_disabled;

uniform sampler2D sprite_tex : source_color, filter_nearest, repeat_disable;
uniform sampler2D sprite_normal : hint_normal, filter_nearest, repeat_disable;
uniform bool use_normal = false;
uniform bool flip = false;               // mirror the normal map x when the sprite is flipped
uniform vec4 tint : source_color = vec4(1.0);
uniform float toon_steps = 5.0;
uniform float toon_max = 1.6;
uniform float toon_seam = 0.16;
uniform float billboard = 1.0;           // 1 = Y-billboard, 0 = use node rotation
uniform float self_light = 0.0;          // flat lift (keeps silhouettes readable against dark ground)
uniform float flag = 0.55;
uniform float unshaded = 0.0;            // 1 = shows its own palette colours (smoke, steam, birds far away)
uniform float dissolve = 0.0;            // 0..1 ordered-dither fade (appear / disappear without alpha blending)

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

void vertex() {
	if (billboard > 0.5) {
		// Y-billboard (same construction as BaseMaterial3D BILLBOARD_FIXED_Y), keeps node scale.
		vec3 sx = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), length(MODEL_MATRIX[2].xyz));
		mat4 bb = mat4(
			vec4(normalize(cross(vec3(0.0, 1.0, 0.0), INV_VIEW_MATRIX[2].xyz)) * sx.x, 0.0),
			vec4(0.0, sx.y, 0.0, 0.0),
			vec4(normalize(cross(INV_VIEW_MATRIX[0].xyz, vec3(0.0, 1.0, 0.0))) * sx.z, 0.0),
			MODEL_MATRIX[3]);
		MODELVIEW_MATRIX = VIEW_MATRIX * bb;
		MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
	}
}

void fragment() {
	vec4 t = texture(sprite_tex, UV);
	ALBEDO = t.rgb * tint.rgb;
	ALPHA = t.a;
	if (dissolve > 0.0 && bayer4(FRAGCOORD.xy) < dissolve) {
		ALPHA = 0.0;
	}
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = flag;
	METALLIC = 0.0;
	SPECULAR = 0.0;
	if (use_normal) {
		vec3 n = texture(sprite_normal, UV).rgb;
		if (flip) {
			n.x = 1.0 - n.x;
		}
		NORMAL_MAP = n;
		NORMAL_MAP_DEPTH = 1.0;
	}
	if (self_light > 0.0 || unshaded > 0.0) {
		EMISSION = ALBEDO * (self_light + unshaded);
	}
}

void light() {
	vec3 lc = LIGHT_COLOR / PI;
	float lum = max(dot(lc, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
	float I = clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION * lum;
	float x = sqrt(clamp(I / toon_max, 0.0, 1.0)) * toon_steps;
	float f = fract(x);
	float up = step(bayer4(FRAGCOORD.xy), clamp((f - 0.5) / toon_seam + 0.5, 0.0, 1.0));
	float lv = min(floor(x) + up, toon_steps) / toon_steps;
	DIFFUSE_LIGHT += lc * (lv * lv * toon_max / lum) * (1.0 - clamp(unshaded, 0.0, 1.0));
}
