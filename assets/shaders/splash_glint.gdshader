shader_type canvas_item;
// Boot sequence title (TECHNICAL_ARCHITECTURE §12.13, round 11): one warm glint sweeps across the copper letters of
// assets/ui/splash/title_logo.png. Quantised to the art pixels (one texel = one art pixel) and to three strengths, so
// it stays pixel art; the dark outline / shadow pixels are never lit.

uniform float sweep = -1.0;          // UV.x position of the glint centre (-0.3 .. 1.3 crosses the logo once)
uniform float width = 0.06;          // half width in UV.x
uniform float slant = 0.16;          // shift per UV.y (leans the band)
uniform vec4 glint_color : source_color = vec4(1.0, 0.95, 0.80, 1.0);

void fragment() {
	vec4 c = COLOR;
	vec2 px = (floor(UV / TEXTURE_PIXEL_SIZE) + 0.5) * TEXTURE_PIXEL_SIZE;
	vec4 tex = texture(TEXTURE, px);
	float lum = dot(tex.rgb, vec3(0.3, 0.59, 0.11));
	float d = abs(px.x + px.y * slant - sweep);
	float g = clamp(1.0 - d / width, 0.0, 1.0);
	g = floor(g * 3.0 + 0.5) / 3.0;
	g *= step(0.3, lum) * step(0.5, tex.a);
	c.rgb = mix(c.rgb, glint_color.rgb, g * 0.75);
	COLOR = c;
}
