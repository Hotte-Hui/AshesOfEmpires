extends RefCounted
## Pixel fire kit, runtime half (art: tools/pixelgen/pixel_fire.py -> assets/fx/pixel_fire/*.png + kit.json).
## Plays the kit's sheets as pixel art: whole world pixels only (integer positions), never scaled or rotated,
## no alpha fades -- things grow by switching to a bigger sheet, fade by the dither drawn into their frames.
## Neighbours never pulse together: every instance gets its own phase and mirror from its number.
## Every call is a pure function of the time t (seek-safe), made from a CanvasItem's _draw()/draw signal:
##
##   const PF := preload("res://scripts/render/pixel_fire.gd")
##   PF.flame(self, "flame_m", Vector2(x, y_foot), t, i)            looping flame, bottom-centre at the foot
##   PF.wall(self, ["wall_a", "wall_b"], x0, x1, y_foot, t)         wall of fire / fire in an opening (tiles)
##   PF.puff(self, "puff_m", centre, age01, i)                      one puff at age 0..1 of its life
##   PF.plume(self, {"from": .., "rise": .., ...}, t)               a column of puffs
##   PF.sparks(self, {"rect": .., "rise": .., ...}, t)              single-pixel sparks on arcs
##   PF.light(self, "glow_m", centre, t, i)                         breathing light pool; the node's material
##                                                                   must be PF.additive()
##   PF.reveal_material() + PF.set_reveal(..)                       a big additive light layer shown as a
##                                                                   growing dithered pool / a wipe
##   PF.mass_materials()                                            six pass materials: flames that overlap
##                                                                   become ONE body (see mass_materials)
## Reduced motion: pass rate = 0.5 (flames and light step half as often, smoke and sparks travel half as far).
## Sheets: flame_xs/s/m/l/xl/xxl, lick, tiles window/ground/low_a|b/wall_a|b, puff_s/m/l/xl(_grey),
## tiles bank_a|b(_grey) and their veils veil_a|b(_grey), sparks_s/m, glow_s/m/l, pool_s/m/l -- see kit.json.

const DIR := "res://assets/fx/pixel_fire/"
const REVEAL := preload("res://scripts/render/pixel_fire_reveal.gdshader")
const MASS := preload("res://scripts/render/pixel_fire_mass.gdshader")
## frames per second of the flame sheets (== TICK in pixel_fire.py)
const TICK := 10.0
## a light pool steps to another frame at most this often: fire light breathes, it never strobes
const LIGHT_HZ := 2.5
## spark colours from hot to gone (== SPARK in pixel_fire.py)
const SPARK := [Color("#FFF6DC"), Color("#FCE0A0"), Color("#F2A044"), Color("#D8662A"), Color("#A8381A"),
	Color("#6E1E0C")]

static var _meta: Dictionary = {}
static var _tex: Dictionary = {}
## sheets that were asked for and do not exist (tests read this)
static var missing: Array = []


static func _sheets() -> Dictionary:
	if _meta.is_empty():
		var p := DIR + "kit.json"
		if FileAccess.file_exists(p):
			var d = JSON.parse_string(FileAccess.get_file_as_string(p))
			if d is Dictionary and d.get("sheets") is Dictionary:
				_meta = d["sheets"]
	return _meta


## {n, w, h, kind} of a sheet ({} if unknown)
static func info(sheet_name: String) -> Dictionary:
	var d = _sheets().get(sheet_name, {})
	return d if d is Dictionary else {}


static func sheet(sheet_name: String) -> Texture2D:
	if _tex.has(sheet_name):
		return _tex[sheet_name]
	var path := DIR + sheet_name + ".png"
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	elif FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			t = ImageTexture.create_from_image(img)
	if t == null and not missing.has(path):
		missing.append(path)
	_tex[sheet_name] = t
	return t


## A sheet of the same make that is not in the kit's table (a generator's own palette or size): n frames side
## by side.  Afterwards every call here takes its name like a kit sheet's.
static func register(sheet_name: String, tx: Texture2D, n: int, kind := "puff") -> void:
	if tx == null or n < 1:
		return
	_sheets()
	_meta[sheet_name] = {"n": n, "w": tx.get_width() / n, "h": tx.get_height(), "kind": kind}
	_tex[sheet_name] = tx


static func additive() -> CanvasItemMaterial:
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return m


## whole animation steps since t = 0
static func tick(t: float, rate := 1.0, fps := TICK) -> int:
	return int(floor(t * fps * rate + 0.0001))


## Phase 0..1 of instance i: the golden-ratio sequence, so instances next to each other in a row are as far
## apart in their loops as can be (a hash would clump); mirror(i) flips about every second one.
static func phase(i: int) -> float:
	return fposmod(float(i) * 0.61803399, 1.0)


static func mirror(i: int) -> bool:
	return fposmod(float(i) * 0.75487767 + 0.3, 1.0) < 0.5


## deterministic 0..1 for instance / birth number i
static func h01(i: int, salt := 0) -> float:
	var n := (i * 374761393 + salt * 668265263 + 1013904223) & 0x7fffffff
	n = ((n ^ (n >> 13)) * 1274126177) & 0x7fffffff
	return float((n ^ (n >> 16)) & 0xffff) / 65536.0


## Frame f of a sheet with its top-left at `at` (whole pixels); flip mirrors it in place.
static func frame(ci: CanvasItem, sheet_name: String, f: int, at: Vector2, flip := false) -> void:
	var tx := sheet(sheet_name)
	var d := info(sheet_name)
	if tx == null or d.is_empty():
		return
	var w := int(d["w"])
	var h := int(d["h"])
	ci.draw_texture_rect_region(tx, Rect2(at.round(), Vector2(-w if flip else w, h)),
		Rect2(posmod(f, int(d["n"])) * w, 0, w, h))


## A looping flame standing on `foot` (bottom-centre).  i = instance number: its phase in the loop and (unless
## mirrored is false) whether it is mirrored.
static func flame(ci: CanvasItem, sheet_name: String, foot: Vector2, t: float, i := 0, rate := 1.0,
		mirrored := true) -> void:
	var d := info(sheet_name)
	if d.is_empty():
		sheet(sheet_name)
		return
	var n := int(d["n"])
	var f := tick(t, rate) + int(phase(i) * n)
	frame(ci, sheet_name, f, Vector2(roundf(foot.x) - int(d["w"]) / 2, roundf(foot.y) - int(d["h"])),
		mirrored and mirror(i))


## Tiles of one set (e.g. ["wall_a", "wall_b"]) from x0 to x1 standing on foot_y, anchored to the world so
## nothing slides when x0 / x1 move.  opt:
##   rate      animation rate (reduced motion 0.5)
##   shift     px into the endless strip (shows another part of the tiles), phase = frames ahead
##   clip_top  rows above this world y are not drawn (an opening's lintel)
##   front, ramp, side   a fire still catching: within `ramp` px behind the front at x = front (side +1: the
##             fire stands to the right of it, -1: to the left) the columns stand lower -- they sink behind the
##             foot line, a whole pixel at a time, so the wall rises out of it instead of popping up
static func wall(ci: CanvasItem, names: Array, x0: float, x1: float, foot_y: float, t: float, opt := {}) -> void:
	if names.is_empty():
		return
	var d := info(str(names[0]))
	if d.is_empty():
		sheet(str(names[0]))
		return
	var tw := int(d["w"])
	var th := int(d["h"])
	var f := posmod(tick(t, float(opt.get("rate", 1.0))) + int(opt.get("phase", 0)), int(d["n"]))
	var xa := int(roundf(x0))
	var xb := int(roundf(x1))
	var yb := int(roundf(foot_y))
	var shift := int(opt.get("shift", 0))
	var clip_top := int(opt.get("clip_top", -100000))
	var ramp := float(opt.get("ramp", 0.0))
	var front := float(opt.get("front", 0.0))
	var side := float(opt.get("side", 1.0))
	var x := xa
	while x < xb:
		var gx := x + shift
		var k := floori(float(gx) / tw)
		var u := gx - k * tw
		var w := mini(tw - u, xb - x)
		var sink := 0
		if ramp > 0.0:
			var behind := (float(x) - front) * side
			if behind < 0.0:
				x += 1
				continue
			if behind < ramp:
				w = 1
				var q := behind / ramp
				sink = int(roundf(th * (1.0 - q * q * (3.0 - 2.0 * q))))
			elif side < 0.0:
				w = clampi(int(floorf(front - ramp)) - x + 1, 1, w)      # stop where the rising part begins
		var top := yb - th + sink
		var sy := maxi(0, clip_top - top)
		var h := th - sink - sy
		var tx := sheet(str(names[posmod(k, names.size())]))
		if tx and h > 0:
			ci.draw_texture_rect_region(tx, Rect2(x, top + sy, w, h), Rect2(f * tw + u, sy, w, h))
		x += w


## One puff at age01 (0 born .. 1 gone) of the life drawn into its sheet, centred on `centre`.
static func puff(ci: CanvasItem, sheet_name: String, centre: Vector2, age01: float, i := 0) -> void:
	var d := info(sheet_name)
	if d.is_empty():
		sheet(sheet_name)
		return
	var n := int(d["n"])
	frame(ci, sheet_name, clampi(int(age01 * n), 0, n - 1),
		Vector2(roundf(centre.x) - int(d["w"]) / 2, roundf(centre.y) - int(d["h"]) / 2), h01(i, 17) < 0.5)


## A column of puffs.  cfg:
##   sheets [names]  picked per puff          from Vector2, spread Vector2 (+- where a puff is born)
##   count, life (s) puffs alive, how long    rise px/s at birth, slow 0..1 (share of the rise lost with age)
##   drift Vector2 px/s (the wind), bend px/s^2 (the wind takes it more the longer it lives), sway px
##   t0, t1          puffs are born only between them
##   ages Vector2    the part of the sheet's life a puff runs through (default 0 -> 1; e.g. (0.5, 0) = it
##                   shrinks away into the distance)
##   seed, rate      variation; motion scale (reduced motion 0.5)
static func plume(ci: CanvasItem, cfg: Dictionary, t: float) -> void:
	var sheets: Array = cfg.get("sheets", ["puff_m"])
	var count := int(cfg.get("count", 6))
	var life := float(cfg.get("life", 2.0))
	var t0 := float(cfg.get("t0", 0.0))
	var t1 := float(cfg.get("t1", 1.0e9))
	if count < 1 or sheets.is_empty() or t < t0:
		return
	var rate := float(cfg.get("rate", 1.0))
	var from: Vector2 = cfg.get("from", Vector2.ZERO)
	var spread: Vector2 = cfg.get("spread", Vector2.ZERO)
	var drift: Vector2 = cfg.get("drift", Vector2.ZERO)
	var ages: Vector2 = cfg.get("ages", Vector2(0.0, 1.0))
	var rise := float(cfg.get("rise", 30.0))
	var slow := float(cfg.get("slow", 0.4))
	var bend := float(cfg.get("bend", 0.0))
	var sway := float(cfg.get("sway", 2.0))
	var seed := int(cfg.get("seed", 0))
	var gap := life / float(count)
	var newest := int(floor((t - t0) / gap))
	for j in range(count, -1, -1):           # oldest first: the young, dense puffs stand in front
		var b := newest - j
		if b < 0:
			continue
		var born := t0 + b * gap
		var age := t - born
		if born > t1 or age < 0.0 or age >= life:
			continue
		var u := age / life
		var a := age * rate
		var p := from + Vector2((h01(b, seed + 1) * 2.0 - 1.0) * spread.x, (h01(b, seed + 2) * 2.0 - 1.0) * spread.y)
		p += Vector2(drift.x * a + 0.5 * bend * a * a + sin(a * 2.1 + float(b)) * sway,
			drift.y * a - rise * a * (1.0 - 0.5 * slow * u))
		puff(ci, str(sheets[int(h01(b, seed + 3) * sheets.size()) % sheets.size()]), p, lerpf(ages.x, ages.y, u),
			b + seed)


## Single-pixel sparks on arcs, cooling down SPARK as they age (no fade).  cfg:
##   rect Rect2      where they are born       count, life (s)
##   rise px/s       kick px/s (+- sideways at birth), wind px/s, gravity px/s^2 (bends the arc back down)
##   t0, t1          born only between them    seed, rate (reduced motion 0.5)
static func sparks(ci: CanvasItem, cfg: Dictionary, t: float) -> void:
	var count := int(cfg.get("count", 8))
	var life := float(cfg.get("life", 1.2))
	var t0 := float(cfg.get("t0", 0.0))
	var t1 := float(cfg.get("t1", 1.0e9))
	if count < 1 or t < t0:
		return
	var rate := float(cfg.get("rate", 1.0))
	var rect: Rect2 = cfg.get("rect", Rect2())
	var rise := float(cfg.get("rise", 50.0))
	var kick := float(cfg.get("kick", 10.0))
	var wind := float(cfg.get("wind", 0.0))
	var grav := float(cfg.get("gravity", 0.0))
	var seed := int(cfg.get("seed", 0))
	var gap := life / float(count)
	var newest := int(floor((t - t0) / gap))
	for j in count + 1:
		var b := newest - j
		if b < 0:
			continue
		var born := t0 + b * gap
		var age := t - born
		var mine := life * (0.55 + 0.45 * h01(b, seed + 5))
		if born > t1 or age < 0.0 or age >= mine:
			continue
		var a := age * rate
		var x := rect.position.x + h01(b, seed + 1) * rect.size.x \
			+ ((h01(b, seed + 3) * 2.0 - 1.0) * kick + wind) * a + sin(a * 5.0 + float(b)) * 1.5
		var y := rect.position.y + h01(b, seed + 2) * rect.size.y \
			- rise * (0.6 + 0.4 * h01(b, seed + 4)) * a + 0.5 * grav * a * a
		var u := age / mine
		var at := Vector2(floorf(x), floorf(y))
		ci.draw_rect(Rect2(at, Vector2.ONE), SPARK[mini(SPARK.size() - 1, int(u * SPARK.size()))])
		if u < 0.16:                         # a young spark draws a short tail
			ci.draw_rect(Rect2(at + Vector2(0, 1), Vector2.ONE), SPARK[2])


## A light pool (glow_* on walls, pool_* on floors and snow) centred on `centre`, breathing: it steps through
## its frames at LIGHT_HZ (never faster), each instance on its own beat.  Draw it from a node whose material is
## additive().
static func light(ci: CanvasItem, sheet_name: String, centre: Vector2, t: float, i := 0, rate := 1.0) -> void:
	var d := info(sheet_name)
	if d.is_empty():
		sheet(sheet_name)
		return
	var f := int(floor(t * LIGHT_HZ * rate + phase(i + 3) * 4.0))
	frame(ci, sheet_name, f, Vector2(roundf(centre.x) - int(d["w"]) / 2, roundf(centre.y) - int(d["h"]) / 2))


## A MASS of fire (a wall of fire with towers behind it and flames in front): kit flames that overlap each bring
## their own dark rim, and the rims cross the hot bodies behind them.  Drawn band by band they merge instead:
## give SIX sibling nodes these materials, in this order, and let every one of them draw the SAME flames (the
## same PF.flame / PF.wall calls).  The first pass keeps only the cooling flamelets, the others paint every
## texel that is at least as hot as their band (rim .. white-hot core) in that band's flat colour -- so each band
## is the union over all flames: one body, a rim around the whole, the hot cores inside.  Kit colours only
## (sheets in another palette keep their own rims: bake them as one sheet instead).
static func mass_materials() -> Array[ShaderMaterial]:
	var out: Array[ShaderMaterial] = []
	var ramp := PackedColorArray([SPARK[4], SPARK[3], SPARK[2], SPARK[1], SPARK[0]])
	for level in range(-1, 5):
		var m := ShaderMaterial.new()
		m.shader = MASS
		m.set_shader_parameter("level", level)
		m.set_shader_parameter("ramp", ramp)
		m.set_shader_parameter("cool", SPARK[5])
		out.append(m)
	return out


## Material for a big additive light layer (a baked lit-minus-unlit image) that is shown as a hard-pixel
## dithered pool or wipe; drive it with set_reveal().
static func reveal_material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = REVEAL
	return m


## origin (texels of the layer's texture), core = half extents of the fully lit box (ZERO: a pool), reach =
## width of the dithered falloff around it, soft = dithered share of that falloff.  Step the values (whole
## pixels, a few times per second) -- the shape is hard-edged, so it may jump, it must not crawl.
static func set_reveal(m: ShaderMaterial, origin: Vector2, core: Vector2, reach: Vector2, soft := 0.6) -> void:
	if m == null:
		return
	m.set_shader_parameter("origin", origin.round())
	m.set_shader_parameter("core", core.round())
	m.set_shader_parameter("reach", reach.round().max(Vector2.ONE))
	m.set_shader_parameter("soft", soft)
