shader_type canvas_item;
render_mode blend_add;
// Additive twin of c3_dissolve.gdshader (glows / light sweeps inside a dissolving shot group).
uniform float progress : hint_range(0.0, 1.0) = 1.0;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void fragment() {
	ivec2 p = ivec2(mod(floor(FRAGCOORD.xy), 4.0));
	float th = (BAYER[p.y * 4 + p.x] + 0.5) / 16.0;
	if (th >= progress) {
		discard;
	}
}
