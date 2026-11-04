shader_type canvas_item;
// Finale montage (owner: trans-finale): pixel-art transitions for whole shots.
// * reveal / node_reveal: ordered (4x4 Bayer) dissolve, locked to world pixels -> no blending, no blur.
// * clip_rect: world-space rectangle (x0, y0, x1, y1); the split screen keeps each desk in its half.
// * tint / tint_color: dithered fade towards a colour (snow veil, darkness) without leaving the palette.
// Children of a set inherit this material (use_parent_material) so 2D lights and normal maps still apply.

uniform float reveal = 1.0;
uniform float node_reveal = 1.0;
uniform vec4 clip_rect = vec4(-100000.0, -100000.0, 100000.0, 100000.0);
uniform vec4 tint_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float tint = 0.0;

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
	vec4 c = COLOR;   // already texture * modulate in Godot 4
	if (th < tint) {
		c.rgb = tint_color.rgb;
	}
	COLOR = c;
}
