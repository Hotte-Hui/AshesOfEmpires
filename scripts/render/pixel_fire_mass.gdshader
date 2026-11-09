shader_type canvas_item;
// Pixel fire kit (scripts/render/pixel_fire.gd): one pass of a MASS of fire.  Kit flames that stand in front of
// each other each bring their own dark rim, and those rims cross the hot bodies behind them -- a wall of fire
// then reads as a tangle of outlines.  A mass is drawn band by band instead: six nodes draw the same flames, the
// first only the cooling flamelets, the others one band each (level 0 = rim .. 4 = white-hot core), and a pass
// paints every texel that is AT LEAST that hot in the band's flat colour.  Painted in this order every band is
// the union over all flames: one body with a rim around the whole and the hot cores inside it.
// Hard pixels only: a texel is drawn in a ramp colour or not at all.
uniform int level = 0;                          // -1 = cooling flamelets, 0 .. 4 = the bands, rim first
uniform vec4 ramp[5] : source_color;            // FIRE of tools/pixelgen/pixel_fire.py, rim first
uniform vec4 cool : source_color = vec4(0.431, 0.118, 0.047, 1.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	if (c.a < 0.5) {
		discard;
	}
	int heat = -1;
	float best = distance(c.rgb, cool.rgb);
	for (int i = 0; i < 5; i++) {
		float d = distance(c.rgb, ramp[i].rgb);
		if (d < best) {
			best = d;
			heat = i;
		}
	}
	if (level < 0) {
		if (heat >= 0) {
			discard;
		}
		COLOR = vec4(cool.rgb, 1.0);
	} else {
		if (heat < level) {
			discard;
		}
		COLOR = vec4(ramp[level].rgb, 1.0);
	}
}
