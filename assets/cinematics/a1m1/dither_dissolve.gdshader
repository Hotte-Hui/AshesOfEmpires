shader_type canvas_item;
// Ordered (8x8 Bayer) pixel dissolve for the A1 -> M1 match dissolve (owner: trans-a1m1).
// progress 0 = invisible, 1 = fully visible. `radial` > 0 orders the reveal by distance from `center`
// (in texture pixels): with `edges_first` the frame edges change first and the centre (the C-17 glyph)
// last. Hard per-pixel cut, no alpha blending -> stays crisp pixel art at every step.

uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform vec2 center = vec2(320.0, 176.0);
uniform float radius = 420.0;
uniform float radial : hint_range(0.0, 1.0) = 0.0;
uniform bool edges_first = true;

const float B8[64] = float[64](
	 0.0, 32.0,  8.0, 40.0,  2.0, 34.0, 10.0, 42.0,
	48.0, 16.0, 56.0, 24.0, 50.0, 18.0, 58.0, 26.0,
	12.0, 44.0,  4.0, 36.0, 14.0, 46.0,  6.0, 38.0,
	60.0, 28.0, 52.0, 20.0, 62.0, 30.0, 54.0, 22.0,
	 3.0, 35.0, 11.0, 43.0,  1.0, 33.0,  9.0, 41.0,
	51.0, 19.0, 59.0, 27.0, 49.0, 17.0, 57.0, 25.0,
	15.0, 47.0,  7.0, 39.0, 13.0, 45.0,  5.0, 37.0,
	63.0, 31.0, 55.0, 23.0, 61.0, 29.0, 53.0, 21.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	vec2 px = floor(UV / TEXTURE_PIXEL_SIZE);
	int bi = int(mod(px.y, 8.0)) * 8 + int(mod(px.x, 8.0));
	float b = (B8[bi] + 0.5) / 64.0;
	float d = clamp(distance(px, center) / radius, 0.0, 1.0);
	float order = edges_first ? (1.0 - d) : d;
	float thr = mix(b, order * 0.8 + b * 0.2, radial);
	if (thr >= progress) {
		discard;
	}
	COLOR = c;
}
