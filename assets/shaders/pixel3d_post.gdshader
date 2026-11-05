shader_type spatial;
// PIXEL-3D POST PROCESS (Mode C) — full-screen quad, drawn last (transparent pass).
// Owner: great_hall_3d.  Used by scenes/levels/L_M1_HallReveal.tscn (scripts/levels/hall/hall_reveal.gd).
//
// Pipeline per logical pixel (the world renders at 640x360, so 1 fragment = 1 game pixel):
//   1. scene colour (linear HDR screen copy) -> sRGB, or the painted sky matte where depth = far plane
//   2. 1 px outline from depth discontinuities (on the nearer pixel, tinted to its own shadow)
//      + crease lines from normal discontinuities (convex = light edge, concave = dark seam)
//      + "burning rim": silhouette pixels against a bright sky take the sky glow colour
//   3. depth fog in dithered bands (colour from a painted fog gradient, same screen mapping as the sky)
//      + low ground haze
//   4. screen-space snow (2 flake sizes, 3 parallax layers, depth-tested against the scene)
//   5. palette snap to pg.PALETTES['berlin'] (40 colours) with 4x4 Bayer ordered dithering
// Material flags travel in the roughness channel of the normal-roughness buffer
// (written by pixel3d_toon / pixel3d_sprite as ROUGHNESS).  Godot's screen-space roughness limiter
// can only RAISE roughness on strongly curved surfaces (max ~0.43 from 0.0), so the bands are:
//   < 0.20 = architecture (outline + creases)      0.20..0.45 = architecture that may use the patina ramp
//   0.50..0.65 = people sprites (own outline)
//   0.68..0.90 = emissive (no outline, less fog)   > 0.92 = wires (never outlined, never cause outlines)
render_mode unshaded, fog_disabled, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, repeat_disable, filter_nearest;
uniform sampler2D depth_tex : hint_depth_texture, repeat_disable, filter_nearest;
uniform sampler2D nr_tex : hint_normal_roughness_texture, repeat_disable, filter_nearest;

// Painted mattes (raw sRGB values, NOT source_color: palette maths happens in sRGB space).
uniform sampler2D sky_tex : filter_nearest, repeat_disable;
uniform sampler2D fog_tex : filter_nearest, repeat_disable;
uniform sampler2D smoke_tex : hint_default_transparent, filter_nearest, repeat_enable;
// Texel of the matte that sits on the optical axis (azimuth 0, elevation 0) and the current
// lens shift of the camera in pixels (+x = frustum moved right, +y = frustum moved up).
uniform vec2 sky_anchor = vec2(512.0, 430.0);
uniform vec2 lens_shift_px = vec2(0.0, 0.0);
uniform vec2 smoke_offset_px = vec2(0.0, 0.0);
uniform float smoke_alpha = 1.0;

// Outlines
uniform float outline_rel = 0.035;      // relative depth jump that counts as a silhouette
uniform float outline_abs = 0.08;       // metres
uniform float outline_dark = 0.58;      // multiplier for silhouette pixels
uniform vec3 outline_tint = vec3(0.92, 0.86, 1.06);
uniform float crease_thresh = 0.30;     // 1 - dot(n0, n1)
uniform float crease_light = 1.18;
uniform float crease_dark = 0.78;
uniform float outline_fade_start = 260.0;   // metres: outlines weaken with distance
uniform float outline_fade_end = 1600.0;
uniform float rim_strength = 1.0;
uniform float rim_min_luma = 0.36;      // sky must be at least this bright to burn a rim

// Fog (sRGB space, banded)
uniform float fog_start = 40.0;
uniform float fog_end = 2400.0;
uniform float fog_max = 0.62;
uniform float fog_curve = 0.75;
uniform float fog_bands = 7.0;
uniform float fog_seam = 0.35;          // width of the dithered seam between bands (0..1)
uniform float haze_height = 14.0;       // ground haze scale height (m)
uniform float haze_amount = 0.22;
uniform float haze_start = 60.0;
uniform float patina_fog = 0.5;

// Snow
uniform float time = 0.0;
uniform float snow_density = 0.55;
uniform vec2 snow_wind = vec2(9.0, 0.0);       // px/s at the nearest layer
uniform vec3 cam_pos = vec3(0.0);
uniform float px_per_m_at_1m = 846.8;          // focal length in pixels
uniform vec3 snow_near = vec3(0.925, 0.902, 0.878);
uniform vec3 snow_far = vec3(0.698, 0.675, 0.690);

// Lamp halos (scattering around lights in the snowy haze), set per frame by the level script:
// halo_a = (screen x, screen y [px, top-left origin], depth [m], radius [px]); halo_b = (sRGB colour, strength)
uniform int halo_count = 0;
uniform vec4 halo_a[32];
uniform vec4 halo_b[32];

// Palette
uniform float palette_strength = 1.0;
uniform float dither_spread = 0.62;     // 0 = hard snap, 1 = full ordered-dither gradient
uniform float fade = 0.0;               // 0..1 dithered fade to black (palette darkest)
uniform int debug_view = 0;             // 1 = material flags, 2 = linear depth, 3 = view normals

const int PAL_N = 40;
const vec3 PAL[40] = vec3[40](
	vec3(18.0, 12.0, 20.0), vec3(27.0, 21.0, 32.0), vec3(33.0, 22.0, 35.0), vec3(42.0, 33.0, 48.0),
	vec3(37.0, 32.0, 43.0), vec3(52.0, 47.0, 55.0), vec3(68.0, 59.0, 67.0), vec3(87.0, 73.0, 77.0),
	vec3(74.0, 58.0, 53.0), vec3(95.0, 74.0, 64.0), vec3(122.0, 94.0, 78.0), vec3(148.0, 115.0, 92.0),
	vec3(174.0, 138.0, 108.0), vec3(201.0, 165.0, 133.0),
	vec3(95.0, 69.0, 48.0), vec3(115.0, 81.0, 69.0), vec3(141.0, 85.0, 66.0), vec3(175.0, 108.0, 71.0),
	vec3(208.0, 119.0, 68.0), vec3(229.0, 148.0, 90.0),
	vec3(240.0, 174.0, 110.0), vec3(244.0, 186.0, 129.0), vec3(248.0, 210.0, 160.0), vec3(252.0, 233.0, 200.0),
	vec3(30.0, 35.0, 41.0), vec3(47.0, 54.0, 63.0), vec3(69.0, 78.0, 88.0), vec3(95.0, 105.0, 115.0),
	vec3(124.0, 134.0, 144.0), vec3(163.0, 172.0, 180.0),
	vec3(30.0, 46.0, 44.0), vec3(44.0, 68.0, 64.0), vec3(62.0, 93.0, 85.0), vec3(86.0, 119.0, 106.0),
	vec3(115.0, 146.0, 127.0),
	vec3(110.0, 106.0, 115.0), vec3(143.0, 138.0, 146.0), vec3(178.0, 172.0, 176.0), vec3(210.0, 204.0, 203.0),
	vec3(236.0, 230.0, 224.0)
);

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0,
								  3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	return (BAYER[q.y * 4 + q.x] + 0.5) / 16.0;
}

vec3 to_srgb(vec3 c) {
	c = clamp(c, 0.0, 1.0);
	return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}

vec3 to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

float luma(vec3 c) {
	return dot(c, vec3(0.299, 0.587, 0.114));
}

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.xx + p3.yz) * p3.zy);
}

// Godot 4.7.2 (Forward+) stores ROUGHNESS unmodified in the w channel of the normal-roughness buffer
// (verified with debug_view = 1: flags 0.0 / 0.3 / 0.55 / 0.75 / 1.0 read back exactly).  Older 4.x
// builds packed it as r * 127/255 with a "dynamic object" flip; if this shader is ever back-ported, set
// legacy_roughness_packing = true.
uniform bool legacy_roughness_packing = false;

float unpack_flag(float w) {
	if (!legacy_roughness_packing) {
		return w;
	}
	if (w > 0.5) {
		w = 1.0 - w;
	}
	return clamp(w / (127.0 / 255.0), 0.0, 1.0);
}

float lin_depth(vec2 suv, float raw, mat4 inv_proj) {
	vec4 v = inv_proj * vec4(suv * 2.0 - 1.0, raw, 1.0);
	return -v.z / v.w;
}

// Matte lookup in pixel space: the camera never rotates (lens shift only), so a direction at
// infinity maps 1:1 onto screen pixels.  frag = pixel coordinate (top-left origin).
vec3 matte(sampler2D tex, vec2 frag, vec2 vp) {
	vec2 p = frag - vp * 0.5 + vec2(lens_shift_px.x, -lens_shift_px.y) + sky_anchor;
	vec2 ts = vec2(textureSize(tex, 0));
	p = clamp(p, vec2(0.5), ts - 0.5);
	return texture(tex, p / ts).rgb;
}

vec3 palette_snap(vec3 c, vec2 frag, bool patina_ok) {
	vec3 c255 = clamp(c, 0.0, 1.0) * 255.0;
	float d1 = 1e20;
	float d2 = 1e20;
	vec3 p1 = PAL[0];
	vec3 p2 = PAL[0];
	for (int i = 0; i < PAL_N; i++) {
		vec3 p = PAL[i];
		vec3 dv = c255 - p;
		// perceptual weighting ("redmean"-like): luminance dominates, chroma still matters
		float rm = (c255.r + p.r) * 0.5;
		float d = (2.0 + rm / 256.0) * dv.r * dv.r + 4.0 * dv.g * dv.g + (2.0 + (255.0 - rm) / 256.0) * dv.b * dv.b;
		// the patina ramp (indices 30..34) is reserved for genuinely green input (the dome): neutral and
		// blue-grey snow/slush must not turn green
		if (i >= 30 && i <= 34 && !patina_ok) {
			float green = c255.g - max(c255.r, c255.b);
			d *= mix(6.0, 1.5, smoothstep(0.0, 12.0, green));
		}
		if (d < d1) {
			d2 = d1; p2 = p1; d1 = d; p1 = p;
		} else if (d < d2) {
			d2 = d; p2 = p;
		}
	}
	float a = sqrt(d1);
	float b = sqrt(d2);
	float u = 2.0 * a / (a + b + 1e-5);          // 0 = exactly p1, 1 = half-way to p2
	float pr = 0.5 * smoothstep(1.0 - dither_spread, 1.0, u);
	vec3 s = (bayer4(frag) < pr) ? p2 : p1;
	return s / 255.0;
}

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

void fragment() {
	vec2 vp = VIEWPORT_SIZE;
	vec2 frag = floor(SCREEN_UV * vp) + 0.5;      // pixel centre, top-left origin
	vec2 suv = frag / vp;
	vec2 texel = 1.0 / vp;

	float raw0 = texture(depth_tex, suv).r;
	bool sky0 = raw0 <= 1e-7;
	vec3 col;
	if (sky0) {
		col = matte(sky_tex, frag, vp);
		// drifting smoke ribbons (painted strip, scrolled very slowly)
		vec2 sp = frag - vp * 0.5 + vec2(lens_shift_px.x, -lens_shift_px.y) + sky_anchor + smoke_offset_px;
		vec4 sm = texture(smoke_tex, sp / vec2(textureSize(smoke_tex, 0)));
		if (sm.a > 0.5 && smoke_alpha > bayer4(frag)) {
			col = sm.rgb;
		}
	} else {
		col = to_srgb(texture(screen_tex, suv).rgb);
	}

	float d0 = sky0 ? 1e6 : lin_depth(suv, raw0, INV_PROJECTION_MATRIX);
	vec4 nr0 = texture(nr_tex, suv);
	vec3 n0 = normalize(nr0.xyz * 2.0 - 1.0);
	float f0 = sky0 ? 1.0 : unpack_flag(nr0.w);
	// burning rim is applied AFTER the fog (scattered light is not hazed away)
	vec3 rim_out = vec3(0.0);
	float rim_amt = 0.0;

	if (!sky0 && f0 < 0.92) {
		vec2 offs[4] = vec2[4](vec2(1.0, 0.0), vec2(-1.0, 0.0), vec2(0.0, 1.0), vec2(0.0, -1.0));
		bool sil = false;
		float rim_w = 0.0;
		vec3 rim_col = vec3(0.0);
		float nd = 0.0;
		float dsum = 0.0;
		int dcount = 0;
		for (int k = 0; k < 4; k++) {
			vec2 q = suv + offs[k] * texel;
			float rq = texture(depth_tex, q).r;
			vec4 nq = texture(nr_tex, q);
			float fq = unpack_flag(nq.w);
			bool skyq = rq <= 1e-7;
			if (skyq) {
				vec3 sc = matte(sky_tex, frag + offs[k] * vec2(1.0, 1.0), vp);
				float l = luma(sc);
				if (l > rim_w) {
					rim_w = l;
					rim_col = sc;
				}
				sil = true;
				continue;
			}
			if (fq > 0.92) {
				continue;      // wires never cause outlines
			}
			float dq = lin_depth(q, rq, INV_PROJECTION_MATRIX);
			dsum += dq;
			dcount += 1;
			if (dq - d0 > d0 * outline_rel + outline_abs) {
				sil = true;
			}
			if (abs(dq - d0) < d0 * outline_rel + outline_abs) {
				vec3 n1 = normalize(nq.xyz * 2.0 - 1.0);
				nd = max(nd, 1.0 - dot(n0, n1));
			}
		}
		// second rim pixel: sky two pixels away (left, right, up) burns the next pixel in, if bright
		float rim2 = 0.0;
		vec3 rim2_col = vec3(0.0);
		if (rim_w <= rim_min_luma) {
			vec2 offs2[3] = vec2[3](vec2(2.0, 0.0), vec2(-2.0, 0.0), vec2(0.0, -2.0));
			for (int k = 0; k < 3; k++) {
				vec2 q2 = suv + offs2[k] * texel;
				if (texture(depth_tex, q2).r <= 1e-7) {
					vec3 sc2 = matte(sky_tex, frag + offs2[k], vp);
					float l2 = luma(sc2);
					if (l2 > rim2) {
						rim2 = l2;
						rim2_col = sc2;
					}
				}
			}
		}
		float dist_fade = 1.0 - smoothstep(outline_fade_start, outline_fade_end, d0);
		bool people = f0 > 0.47 && f0 < 0.66;
		bool emissive = f0 > 0.67 && f0 < 0.92;
		if (!sil && rim2 > 0.42 && !people && !emissive && rim_strength > 0.0) {
			rim_out = rim2_col;
			rim_amt = 0.7 * smoothstep(0.42, 0.56, rim2) * rim_strength;
		} else if (sil && !people && !emissive) {
			if (rim_w > rim_min_luma && rim_strength > 0.0) {
				// burning rim: the silhouette catches the glow of the sky right behind it, one step hotter
				rim_out = mix(rim_col, vec3(0.988, 0.914, 0.784), 0.62);
				rim_amt = clamp(smoothstep(rim_min_luma, rim_min_luma + 0.18, rim_w) * rim_strength, 0.0, 1.0);
			} else {
				float k = mix(1.0, outline_dark, 0.35 + 0.65 * dist_fade);
				col = col * k * outline_tint;
			}
		} else if (nd > crease_thresh && !people && !emissive) {
			float lap = (dcount == 4) ? (dsum * 0.25 - d0) : 0.0;
			float w = 0.4 + 0.6 * dist_fade;
			if (lap > 0.0) {
				col = mix(col, col * crease_light + vec3(0.03, 0.02, 0.0), w);
			} else {
				col = mix(col, col * crease_dark, w);
			}
		}
	}

	// ---- depth fog (dithered bands)
	if (!sky0) {
		float th = bayer4(frag);
		float x = clamp((d0 - fog_start) / (fog_end - fog_start), 0.0, 1.0);
		x = pow(x, fog_curve);
		float fb = x * fog_bands;
		float lvl = floor(fb) + step(th, clamp((fract(fb) - 0.5) / max(fog_seam, 0.01) + 0.5, 0.0, 1.0));
		float fog = min(lvl / fog_bands, 1.0) * fog_max;
		// ground haze: reconstruct world height
		vec4 vpos = INV_PROJECTION_MATRIX * vec4(suv * 2.0 - 1.0, raw0, 1.0);
		vpos.xyz /= vpos.w;
		vec3 wpos = (INV_VIEW_MATRIX * vec4(vpos.xyz, 1.0)).xyz;
		float hz = exp(-max(wpos.y, 0.0) / haze_height) * smoothstep(haze_start, haze_start * 6.0, d0) * haze_amount;
		float hzq = floor(hz * 6.0 + th) / 6.0;
		fog = clamp(fog + hzq, 0.0, 0.9);
		if (f0 > 0.67 && f0 < 0.92) {
			fog *= 0.45;    // lamps and lit windows punch through the haze
		} else if (f0 > 0.2 && f0 < 0.45) {
			fog *= patina_fog;    // keep the green-black of the dome readable in the haze
		}
		vec3 fc = matte(fog_tex, frag, vp);
		col = mix(col, fc, fog);
		col = mix(col, rim_out, rim_amt);
	}

	// ---- lamp halos: additive in sRGB, the palette snap turns them into dithered rings; a halo only lights
	// what is behind the lamp (objects in front of it occlude the scattering)
	for (int i = 0; i < halo_count; i++) {
		vec4 ha = halo_a[i];
		vec4 hb = halo_b[i];
		vec2 dv = (frag - ha.xy) * vec2(1.0, 1.2);
		float r = length(dv) / max(ha.w, 0.5);
		if (r < 1.0 && (sky0 || d0 > ha.z * 0.985)) {
			float g = 1.0 - r;
			col += hb.rgb * (g * g * hb.a);
		}
	}

	// ---- screen-space snow: three parallax layers, depth tested
	if (snow_density > 0.0) {
		for (int L = 0; L < 3; L++) {
			float fl = float(L);
			float depth_l = (L == 0) ? 7.0 : ((L == 1) ? 18.0 : 45.0);
			float cell = (L == 0) ? 23.0 : ((L == 1) ? 15.0 : 11.0);
			float size = (L == 0) ? 2.0 : 1.0;
			float speed = (L == 0) ? 1.0 : ((L == 1) ? 0.62 : 0.38);
			float dens = snow_density * ((L == 0) ? 0.30 : ((L == 1) ? 0.45 : 0.55));
			// camera translation parallax (x/y), plus a slow fall and wind
			// (layers keep a constant distance to the camera, so a dolly does not move them)
			vec2 par = vec2(cam_pos.x, -cam_pos.y) * px_per_m_at_1m / depth_l;
			vec2 drift = vec2(snow_wind.x * speed, 34.0 * speed) * time;
			vec2 p = frag + par - drift;
			vec2 cid = floor(p / cell);
			float h = hash12(cid + fl * 37.0);
			if (h < dens) {
				vec2 fo = floor(hash22(cid * 1.7 + fl * 11.0) * (cell - size - 1.0));
				// gentle sideways sway, in whole pixels
				fo.x += floor(sin(time * (0.9 + h * 2.0) + h * 40.0) * 1.5 + 0.5);
				vec2 lp = floor(p - cid * cell) - fo;
				if (lp.x >= 0.0 && lp.y >= 0.0 && lp.x < size && lp.y < size) {
					if (sky0 || d0 > depth_l) {
						col = (L == 0) ? snow_near : snow_far;
					}
				}
			}
		}
	}

	// ---- dithered fade + palette snap
	if (fade > 0.0) {
		float fq = floor(fade * 8.0 + bayer4(frag)) / 8.0;
		col = mix(col, PAL[0] / 255.0, clamp(fq, 0.0, 1.0));
	}
	if (palette_strength > 0.0) {
		bool patina_ok = !sky0 && f0 > 0.2 && f0 < 0.45;
		col = mix(col, palette_snap(col, frag, patina_ok), palette_strength);
	}
	if (debug_view == 1) {
		col = vec3(f0, sky0 ? 1.0 : 0.0, 0.0);
	} else if (debug_view == 2) {
		col = vec3(fract(log2(max(d0, 1.0)) * 0.5));
	} else if (debug_view == 3) {
		col = n0 * 0.5 + 0.5;
	}
	ALBEDO = to_linear(col);
}
