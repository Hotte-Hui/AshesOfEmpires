extends RefCounted
## Shared picture tube of the two mini-games at the data desk of Nebenstelle Süd (terminal_game.gd „Die Datenstelle“,
## abgang_game.gd „Planspiel Abgang“; TECHNICAL_ARCHITECTURE §12.8). A 1964 „Sichtgerät“ in the game's pixel style:
## * the picture is an art-pixel texture (the terminal's text raster or the low-resolution SubViewport of the 3D
##   wireframe) whose channels carry beam strength only — green = the main beam, red = the second beam (the posts and
##   what they see) — in three steps (LEVELS);
## * tube_material() turns it into phosphor: every art pixel becomes one palette colour (three greens, two ambers),
##   lit pixels throw a one-pixel halo in a darker step, the dark glass has hard scan rows — no blur, no gradient,
##   and the picture is shown at a whole multiple (x3, x2/x4), so it sits on the 640x360 grid like the rest;
## * text is lettered with the game's own 5x7 capitals (scripts/ui/pixel_font.gd, umlauts included) on a fixed
##   6x10 cell, plus the few signs a data desk needs (EXTRA);
## * draw_housing() paints the steel housing with its side panel (lamp, type plate, knobs).
## High contrast (Settings) swaps the palette for a black glass and brighter steps.

const PixelFont := preload("res://scripts/ui/pixel_font.gd")

const CELL := Vector2i(6, 10)
const BEZEL := 4
const SIDE := 26
## Beam strength written into the picture (0 off, 1 dim, 2 medium, 3 bright).
const LEVELS := [0.0, 0.3, 0.6, 1.0]
const EXTRA := {
	">": ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
	"<": ["....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"],
	"(": ["..#", ".#.", "#..", "#..", "#..", ".#.", "..#"],
	")": ["#..", ".#.", "..#", "..#", "..#", ".#.", "#.."],
	"=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
	"*": [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
	"#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
	"%": ["##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"],
	"_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
	"^": ["..#..", ".#.#.", "#...#", ".....", ".....", ".....", "....."],
	";": ["..", "..", "##", "..", "##", ".#", "#."],
	"[": ["###", "#..", "#..", "#..", "#..", "#..", "###"],
	"]": ["###", "..#", "..#", "..#", "..#", "..#", "###"],
}
const PALETTE := {"bg": Color("07120d"), "bg2": Color("0a1811"), "glow": Color("173a26"), "g1": Color("2f6b45"),
	"g2": Color("6fd08c"), "g3": Color("dcffe2"), "aglow": Color("3a2a14"), "a1": Color("a87a44"),
	"a2": Color("f2c46a"), "alarm": Color("2a0f0c")}
const PALETTE_HC := {"bg": Color("000000"), "bg2": Color("000000"), "glow": Color("1f5a38"), "g1": Color("4fae72"),
	"g2": Color("9df5b6"), "g3": Color("ffffff"), "aglow": Color("5a3c10"), "a1": Color("ffb000"),
	"a2": Color("ffe9a8"), "alarm": Color("3c0c08")}
const STEEL := [Color("15191c"), Color("2f373d"), Color("4a545c"), Color("6c7881"), Color("98a4ac")]
const PLATE := Color("e6e1cf")
const INK := Color("23272b")

const TUBE_SHADER := """shader_type canvas_item;
render_mode unshaded;
uniform vec2 art = vec2(400.0, 150.0);
uniform vec3 bg = vec3(0.03, 0.07, 0.05);
uniform vec3 bg2 = vec3(0.04, 0.09, 0.07);
uniform vec3 glow = vec3(0.09, 0.23, 0.15);
uniform vec3 g1 = vec3(0.18, 0.42, 0.27);
uniform vec3 g2 = vec3(0.43, 0.82, 0.55);
uniform vec3 g3 = vec3(0.86, 1.0, 0.89);
uniform vec3 aglow = vec3(0.23, 0.16, 0.08);
uniform vec3 a1 = vec3(0.66, 0.48, 0.27);
uniform vec3 a2 = vec3(0.95, 0.77, 0.42);
uniform vec3 alarm = vec3(0.16, 0.06, 0.05);
uniform float alarm_on = 0.0;
uniform float corner = 5.0;

void fragment() {
	vec2 ts = vec2(1.0) / art;
	vec2 px = floor(UV * art);
	vec2 uv = (px + vec2(0.5)) * ts;
	vec2 c = texture(TEXTURE, uv).rg;
	vec2 n = max(max(texture(TEXTURE, uv + vec2(ts.x, 0.0)).rg, texture(TEXTURE, uv - vec2(ts.x, 0.0)).rg),
		max(texture(TEXTURE, uv + vec2(0.0, ts.y)).rg, texture(TEXTURE, uv - vec2(0.0, ts.y)).rg));
	vec3 col = mod(px.y, 2.0) < 1.0 ? bg : bg2;
	if (alarm_on > 0.5) {
		col = alarm;
	}
	if (n.y > 0.45) {
		col = glow;
	}
	if (n.x > 0.45) {
		col = aglow;
	}
	if (c.y > 0.8) {
		col = g3;
	} else if (c.y > 0.45) {
		col = g2;
	} else if (c.y > 0.08) {
		col = g1;
	}
	if (c.x > 0.8) {
		col = a2;
	} else if (c.x > 0.08) {
		col = a1;
	}
	vec2 q = min(px, art - vec2(1.0) - px);
	float a = 1.0;
	if (q.x < corner && q.y < corner) {
		vec2 d = vec2(corner) - q - vec2(0.5);
		if (dot(d, d) > corner * corner) {
			a = 0.0;
		}
	}
	COLOR = vec4(col, a);
}
"""

## Lines of the 3D picture: unshaded, never hidden (a vector display draws every edge), vertex colour = beam
## strength; beyond `far_dim` (view distance) the beam is one step weaker.
const LINE_SHADER := """shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled, fog_disabled;
uniform float far_dim = 99.0;

void fragment() {
	vec3 c = COLOR.rgb;
	if (-VERTEX.z > far_dim) {
		c *= 0.6;
	}
	ALBEDO = pow(c, vec3(2.2));
}
"""

static var _tube: Shader
static var _line: Shader


static func norm(text: String) -> String:
	return text.to_upper().replace("ß", "SS").replace("ẞ", "SS")


static func glyph(ch: String) -> Array:
	if PixelFont.GLYPHS.has(ch):
		return PixelFont.GLYPHS[ch]
	if EXTRA.has(ch):
		return EXTRA[ch]
	return []


## True when every character can be lettered on the tube.
static func supports(text: String) -> bool:
	for ch in norm(text):
		if glyph(ch).is_empty():
			return false
	return true


static func palette(hc := false) -> Dictionary:
	return PALETTE_HC if hc else PALETTE


## Colour to write into the picture: beam strength `lv` (0..3) on the green beam, or the second (amber) one.
static func beam(lv: int, second := false) -> Color:
	var v: float = LEVELS[clampi(lv, 0, 3)]
	return Color(v, 0.0, 0.0) if second else Color(0.0, v, 0.0)


static func tube_material(art: Vector2i, hc := false) -> ShaderMaterial:
	if _tube == null:
		_tube = Shader.new()
		_tube.code = TUBE_SHADER
	var m := ShaderMaterial.new()
	m.shader = _tube
	m.set_shader_parameter("art", Vector2(art))
	var p := palette(hc)
	for k in p:
		var c: Color = p[k]
		m.set_shader_parameter(k, Vector3(c.r, c.g, c.b))
	return m


static func line_material() -> ShaderMaterial:
	if _line == null:
		_line = Shader.new()
		_line.code = LINE_SHADER
	var m := ShaderMaterial.new()
	m.shader = _line
	return m


## Screen size of the housing for a picture of `art` pixels at scale `s`.
static func housing_size(art: Vector2i, s: int) -> Vector2:
	return Vector2(art.x + 2 * BEZEL + SIDE, art.y + 2 * BEZEL) * float(s)


## Where the picture sits inside the housing (screen px).
static func tube_rect(art: Vector2i, s: int) -> Rect2:
	return Rect2(Vector2(BEZEL, BEZEL) * float(s), Vector2(art) * float(s))


## Keeps the picture on the screen's pixel grid: shifts `tube` (a child of the housing, nominally at `base`) by up to
## s - 1 px so that every art pixel covers whole cells of the s-px grid (s = 3: the game's 640x360 world pixels).
static func snap(tube: Control, s: int, base: Vector2) -> void:
	var host := tube.get_parent() as Control
	if host == null:
		return
	var g := host.global_position + base
	var want := base - Vector2(fposmod(g.x, float(s)), fposmod(g.y, float(s)))
	if not tube.position.is_equal_approx(want):
		tube.position = want


## Letters `text` with canvas rects, one art pixel = `unit` canvas px; returns the width in art px.
static func draw_text(ci: CanvasItem, text: String, at: Vector2, col: Color, unit := 1.0) -> int:
	var t := norm(text)
	for i in t.length():
		var g := glyph(t[i])
		if g.is_empty():
			continue
		var gw := str(g[0]).length()
		var top := 8 - g.size()
		var ox := at.x + float(i * CELL.x + maxi(0, (5 - gw) / 2))
		for gy in g.size():
			var line: String = g[gy]
			var run := 0
			for gx in gw + 1:
				if gx < gw and line[gx] == "#":
					run += 1
				elif run > 0:
					ci.draw_rect(Rect2((ox + float(gx - run)) * unit, (at.y + float(top + gy)) * unit, float(run) * unit, unit), col)
					run = 0
	return t.length() * CELL.x


static func text_width(text: String) -> int:
	return norm(text).length() * CELL.x


## The text picture of the terminal: `runs` = [{"t": text, "c": column, "r": row, "lv": 1..3}] and boxes
## {"box": [x, y, w, h] (art px), "lv"}; returns an RGB image of `size` art px (green channel = beam strength).
static func raster(runs: Array, size: Vector2i, origin := Vector2i(3, 3)) -> Image:
	var data := PackedByteArray()
	data.resize(size.x * size.y * 3)
	for run in runs:
		var val := int(round(float(LEVELS[clampi(int(run.get("lv", 2)), 0, 3)]) * 255.0))
		if run.has("box"):
			var b: Array = run["box"]
			for y in range(maxi(0, int(b[1])), mini(size.y, int(b[1]) + int(b[3]))):
				for x in range(maxi(0, int(b[0])), mini(size.x, int(b[0]) + int(b[2]))):
					data[(y * size.x + x) * 3 + 1] = val
			continue
		var t := norm(str(run.get("t", "")))
		var x0 := origin.x + int(run.get("c", 0)) * CELL.x
		var y0 := origin.y + int(run.get("r", 0)) * CELL.y
		for i in t.length():
			var g := glyph(t[i])
			if g.is_empty():
				continue
			var gw := str(g[0]).length()
			var top := 8 - g.size()
			var ox := x0 + i * CELL.x + maxi(0, (5 - gw) / 2)
			for gy in g.size():
				var py := y0 + top + gy
				if py < 0 or py >= size.y:
					continue
				var line: String = g[gy]
				for gx in gw:
					var px := ox + gx
					if line[gx] == "#" and px >= 0 and px < size.x:
						data[(py * size.x + px) * 3 + 1] = val
	return Image.create_from_data(size.x, size.y, false, Image.FORMAT_RGB8, data)


## Columns and rows of text that fit a picture of `art` pixels.
static func grid(art: Vector2i) -> Vector2i:
	return Vector2i((art.x - 6) / CELL.x, (art.y - 6) / CELL.y)


## The steel housing around the tube and its side panel: power lamp, type plate, two knobs, a grille.
## `lamp`: 0 off, 1 green (running), 2 amber (the post has seen the figure).
static func draw_housing(ci: CanvasItem, art: Vector2i, s: int, plate: String, lamp := 1, hc := false) -> void:
	var u := float(s)
	var w := art.x + 2 * BEZEL + SIDE
	var h := art.y + 2 * BEZEL
	ci.draw_rect(Rect2(0, 0, w * u, h * u), STEEL[1])
	ci.draw_rect(Rect2(0, 0, w * u, u), STEEL[3])
	ci.draw_rect(Rect2(0, 0, u, h * u), STEEL[2])
	ci.draw_rect(Rect2(0, (h - 1) * u, w * u, u), STEEL[0])
	ci.draw_rect(Rect2((w - 1) * u, 0, u, h * u), STEEL[0])
	# the dark lip around the glass
	ci.draw_rect(Rect2((BEZEL - 2) * u, (BEZEL - 2) * u, (art.x + 4) * u, (art.y + 4) * u), STEEL[0])
	ci.draw_rect(Rect2((BEZEL - 1) * u, (BEZEL - 1) * u, (art.x + 2) * u, (art.y + 2) * u), palette(hc)["bg"])
	# side panel
	var sx := float(art.x + 2 * BEZEL)
	ci.draw_rect(Rect2(sx * u, 2 * u, u, (h - 4) * u), STEEL[0])
	ci.draw_rect(Rect2((sx + 1) * u, 2 * u, u, (h - 4) * u), STEEL[2])
	var cx := sx + float(SIDE) * 0.5
	var lamp_col: Color = STEEL[0]
	if lamp == 1:
		lamp_col = palette(hc)["g2"]
	elif lamp == 2:
		lamp_col = palette(hc)["a2"]
	ci.draw_rect(Rect2((cx - 3) * u, 8 * u, 5 * u, 5 * u), STEEL[0])
	ci.draw_rect(Rect2((cx - 2) * u, 9 * u, 3 * u, 3 * u), lamp_col)
	ci.draw_rect(Rect2((cx - 2) * u, 9 * u, u, u), STEEL[4] if lamp > 0 else STEEL[2])
	var pw := float(text_width(plate)) + 3.0
	ci.draw_rect(Rect2((cx - pw * 0.5) * u, 20 * u, pw * u, 12 * u), PLATE)
	ci.draw_rect(Rect2((cx - pw * 0.5) * u, 31 * u, pw * u, u), STEEL[3])
	draw_text(ci, plate, Vector2(cx - pw * 0.5 + 2.0, 21.0), INK, u)
	for k in 2:
		var ky := 44.0 + float(k) * 20.0
		ci.draw_rect(Rect2((cx - 4) * u, (ky - 1) * u, 7 * u, 9 * u), STEEL[0])
		ci.draw_rect(Rect2((cx - 3) * u, ky * u, 5 * u, 7 * u), STEEL[3])
		ci.draw_rect(Rect2((cx - 3) * u, ky * u, 5 * u, u), STEEL[4])
		ci.draw_rect(Rect2((cx - 1) * u, (ky + 1) * u, u, 3 * u), STEEL[0])
	var gy := 88.0
	while gy < float(h) - 8.0:
		ci.draw_rect(Rect2((sx + 6) * u, gy * u, (SIDE - 11) * u, u), STEEL[0])
		ci.draw_rect(Rect2((sx + 6) * u, (gy + 1) * u, (SIDE - 11) * u, u), STEEL[2])
		gy += 4.0
