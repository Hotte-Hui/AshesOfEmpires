shader_type canvas_item;
render_mode unshaded;
// Finale montage (owner: trans-finale): the red C-17 route draws itself along the rails.
// order_tex stores each route pixel's normalised arc length (16 bit: R + G/255).  Pixels with an order
// beyond `progress` are discarded; the frontier gets the bright pen-tip colour.  Same dither/clip
// uniforms as finale_set.gdshader so the whole map can dissolve in and out.

uniform sampler2D order_tex : filter_nearest;
uniform float progress = 0.0;
uniform vec4 tip_color : source_color = vec4(0.984, 0.890, 0.682, 1.0);
uniform float tip_len = 0.012;
uniform float reveal = 1.0;
uniform float node_reveal = 1.0;
uniform vec4 clip_rect = vec4(-100000.0, -100000.0, 100000.0, 100000.0);
uniform float tint = 0.0;
uniform vec4 tint_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);

varying vec2 wpos;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

void fragment() {
	vec2 p = floor(wpos);
	if (p.x < clip_rect.x || p.y < clip_rect.y || p.x >= clip_rect.z || p.y >= clip_rect.w) {
		discard;
	}
	ivec2 b = ivec2(mod(p, 4.0));
	float th = (BAYER[b.y * 4 + b.x] + 0.5) / 16.0;
	if (th >= min(reveal, node_reveal)) {
		discard;
	}
	vec4 o = texture(order_tex, UV);
	float ord = o.r + o.g / 255.0;
	if (o.a < 0.5 || ord > progress) {
		discard;
	}
	vec4 c = COLOR;   // already texture * modulate in Godot 4
	if (progress < 0.999 && progress - ord < tip_len) {
		c.rgb = tip_color.rgb;
	}
	if (th < tint) {
		c.rgb = tint_color.rgb;
	}
	COLOR = c;
}
