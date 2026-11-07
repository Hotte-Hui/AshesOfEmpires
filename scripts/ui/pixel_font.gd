extends RefCounted
## Own 5x7 pixel capitals for the boot cards (TECHNICAL_ARCHITECTURE §12.13, round 11): texts come from locale keys
## (the studio name is renamable in data/locale/de_splash.json) and are lettered at runtime — no font file, no
## third-party glyphs. Umlauts follow tools/pixelgen/pixfont_umlauts.py: the dots sit one row ABOVE the cap line and
## the letter is one row shorter, so every line is 8 rows (row 0 = umlaut dots). ß becomes SS.
## render(text, opts) -> Image, or null when a character has no glyph (the caller then falls back to a Label).
## opts: smooth (Scale2x: twice the size, rounded diagonals), bold (+1 px verticals), tracking (px between letters),
##       ramp (Array of Color, top → bottom), outline (Color), shadow (Color, drawn 1 px down-right), bevel (bool).

const ROWS := 8
const GLYPHS := {
	"A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
	"B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
	"C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
	"D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
	"E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
	"F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
	"G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
	"H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
	"I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
	"J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
	"K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
	"L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
	"M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
	"N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
	"O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
	"P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
	"Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
	"R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
	"S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
	"T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
	"U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
	"V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
	"W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
	"X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
	"Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
	"Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
	"Ä": [".#.#.", ".....", ".###.", "#...#", "#...#", "#####", "#...#", "#...#"],
	"Ö": [".#.#.", ".....", ".###.", "#...#", "#...#", "#...#", "#...#", ".###."],
	"Ü": [".#.#.", ".....", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
	"0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
	"1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
	"2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
	"3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
	"4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
	"5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
	"6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
	"7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
	"8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
	"9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
	"-": ["...", "...", "...", "###", "...", "...", "..."],
	".": [".", ".", ".", ".", ".", ".", "#"],
	",": ["..", "..", "..", "..", "..", ".#", "#."],
	"!": ["#", "#", "#", "#", "#", ".", "#"],
	"?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
	"'": ["#", "#", ".", ".", ".", ".", "."],
	":": [".", ".", "#", ".", ".", "#", "."],
	"·": [".", ".", ".", "#", ".", ".", "."],
	"&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
	"/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
	"+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
	" ": ["...", "...", "...", "...", "...", "...", "..."],
}


static func supports(text: String) -> bool:
	for ch in _norm(text):
		if not GLYPHS.has(ch):
			return false
	return true


static func _norm(text: String) -> String:
	return text.to_upper().replace("ß", "SS").replace("ẞ", "SS")


## Binary mask of the text (Array of PackedByteArray rows), or [] when a glyph is missing.
static func mask(text: String, tracking := 1) -> Array:
	var t := _norm(text)
	var rows: Array = []
	for r in ROWS:
		rows.append(PackedByteArray())
	for i in t.length():
		var ch := t[i]
		if not GLYPHS.has(ch):
			return []
		var g: Array = GLYPHS[ch]
		var top := ROWS - g.size()          # 7-row glyphs start on row 1, umlauts on row 0
		var gw: int = str(g[0]).length()
		for r in ROWS:
			var line: String = str(g[r - top]) if r >= top else ".".repeat(gw)
			var row: PackedByteArray = rows[r]
			for c in gw:
				row.append(1 if line[c] == "#" else 0)
			if i < t.length() - 1:
				for k in tracking:
					row.append(0)
			rows[r] = row
	return rows


## Scale2x (EPX) on a mask: twice the size, diagonals rounded.
static func scale2x(m: Array) -> Array:
	var h := m.size()
	var w: int = (m[0] as PackedByteArray).size() if h > 0 else 0
	var out: Array = []
	for y in h * 2:
		var row := PackedByteArray()
		row.resize(w * 2)
		out.append(row)
	for y in h:
		for x in w:
			var e := _px(m, x, y, w, h)
			var b := _px(m, x, y - 1, w, h)
			var d := _px(m, x - 1, y, w, h)
			var f := _px(m, x + 1, y, w, h)
			var hh := _px(m, x, y + 1, w, h)
			var r0: PackedByteArray = out[y * 2]
			var r1: PackedByteArray = out[y * 2 + 1]
			r0[x * 2] = d if (b == d and b != f and d != hh) else e
			r0[x * 2 + 1] = f if (b == f and b != d and f != hh) else e
			r1[x * 2] = d if (d == hh and d != b and hh != f) else e
			r1[x * 2 + 1] = f if (hh == f and d != hh and b != f) else e
			out[y * 2] = r0
			out[y * 2 + 1] = r1
	return out


static func _px(m: Array, x: int, y: int, w: int, h: int) -> int:
	if x < 0 or y < 0 or x >= w or y >= h:
		return 0
	return (m[y] as PackedByteArray)[x]


static func render(text: String, opts := {}) -> Image:
	var m := mask(text, int(opts.get("tracking", 1)))
	if m.is_empty():
		return null
	if bool(opts.get("smooth", false)):
		m = scale2x(m)
	var h := m.size()
	var w: int = (m[0] as PackedByteArray).size()
	if bool(opts.get("bold", false)):
		for y in h:
			var row: PackedByteArray = m[y]
			var src := row.duplicate()
			row.append(0)
			for x in range(1, w + 1):
				if src[x - 1] == 1:
					row[x] = 1
			m[y] = row
		w += 1
	var ramp: Array = opts.get("ramp", [Color.WHITE])
	var outline = opts.get("outline", null)
	var shadow = opts.get("shadow", null)
	var bevel := bool(opts.get("bevel", false))
	var pad := 2
	var img := Image.create(w + pad * 2, h + pad * 2, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var cap_top := float(h) / ROWS          # skip the umlaut row when spreading the ramp
	# outlined shape = the letters + a 1-px ring; the drop shadow is that shape moved 1 px down-right
	var ring := {}
	for y in range(-1, h + 1):
		for x in range(-1, w + 1):
			if _px(m, x, y, w, h) == 1:
				continue
			for d in [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(-1, 0), Vector2i(1, 0),
					Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)]:
				if _px(m, x + d.x, y + d.y, w, h) == 1:
					ring[Vector2i(x, y)] = true
					break
	if shadow != null:
		for y in range(-1, h + 1):
			for x in range(-1, w + 1):
				var p := Vector2i(x, y)
				if not (ring.has(p) or _px(m, x, y, w, h) == 1):
					continue
				var q := p + Vector2i(1, 1)
				if not ring.has(q) and _px(m, q.x, q.y, w, h) == 0:
					img.set_pixel(q.x + pad, q.y + pad, shadow)
	if outline != null:
		for p in ring:
			img.set_pixel(p.x + pad, p.y + pad, outline)
	for y in h:
		for x in w:
			if _px(m, x, y, w, h) == 0:
				continue
			var t := clampf((float(y) - cap_top) / maxf(1.0, float(h) - cap_top - 1.0), 0.0, 1.0)
			var fi := t * float(ramp.size() - 1)
			var i := int(fi)
			if fi - float(i) > _bayer(x, y) and i < ramp.size() - 1:
				i += 1
			var c: Color = ramp[i]
			if bevel:
				if _px(m, x, y - 1, w, h) == 0:
					c = c.lerp(Color.WHITE, 0.35)
				elif _px(m, x, y + 1, w, h) == 0:
					c = c.darkened(0.3)
			img.set_pixel(x + pad, y + pad, c)
	return img


static func _bayer(x: int, y: int) -> float:
	const B := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
	return (float(B[(y % 4) * 4 + (x % 4)]) + 0.5) / 16.0


## TextureRect showing the lettering at an integer pixel scale (nearest), or null (no glyph for a character).
static func rect(text: String, scale: int, opts := {}) -> TextureRect:
	var img := render(text, opts)
	if img == null:
		return null
	var r := TextureRect.new()
	r.texture = ImageTexture.create_from_image(img)
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.custom_minimum_size = Vector2(img.get_width(), img.get_height()) * scale
	r.size = r.custom_minimum_size
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r
