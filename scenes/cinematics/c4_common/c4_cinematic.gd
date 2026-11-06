extends "res://scenes/cinematics/c3p2_common/c3p2_cinematic.gd"
## Shared base of the Chapter-4 cinematics LS_C4_Homeward / _Number / _Card / _Stamp / _Voices (C4_DESIGN §2.9).
## Owner: cine stream (round 9).  Reuses the §12.5 runtime of ch3_common/c3_cinematic.gd and the C3P2 helpers
## (choice(), schedule(), shot tables, snow, flame frames) unchanged and adds:
##   * textures from assets/cinematics/c4/ (tools/pixelgen/env_c4_cine*.py) and its layout.json sections
##   * line_dur(key)       a subtitle duration that keeps every line readable (<= READ_CPS characters per second)
##   * fig()/fig_frame()   the game's own character sheets re-lit per shot: named frame ranges from layout.json
##   * walk helpers        the in-game stride (45 px/s, 8 frames per 36 px) so feet never slide
##   * fx()                a draw node whose callback paints from the timeline time
##   * optional_music()    a music cue only when its file exists (the audio stream's tracks are optional)
## Every frame stays a pure function of t; match cuts are hard cuts (no white dip).

const ASSETS4 := "res://assets/cinematics/c4/"
## readable subtitles: at most this many characters per second (the tests allow 22.5)
const READ_CPS := 19.0
const WALK_SPEED := 45.0          ## px/s, player.gd walk speed
const STRIDE := 4.5               ## px per walk frame (45 px/s at 10 fps)
const FIG_W := 32
const FIG_H := 56
const FEET_OFF := Vector2(16, 54) ## sheet.json origin

var _layout4: Dictionary = {}


func _layout_section(section: String) -> Dictionary:
	if _layout4.is_empty():
		var p := ASSETS4 + "layout.json"
		if FileAccess.file_exists(p):
			var d = JSON.parse_string(FileAccess.get_file_as_string(p))
			if d is Dictionary:
				_layout4 = d
	var s = _layout4.get(section, {})
	return s if s is Dictionary else {}


## Texture under assets/cinematics/c4/ (same fallbacks and `missing` bookkeeping as the base).
func tex(rel: String) -> Texture2D:
	var path := ASSETS4 + rel
	if ResourceLoader.exists(path):
		var r = load(path)
		if r is Texture2D:
			return r
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	if not missing.has(path):
		missing.append(path)
	return null


## Seconds a subtitle needs: its length at READ_CPS plus a beat, clamped to [lo, hi].
func line_dur(key: String, lo := 1.4, hi := 4.6) -> float:
	var n := Loc.t(key).length() if Loc else key.length()
	return clampf(float(n) / READ_CPS + 0.35, lo, hi)


## Subtitle cue that starts at `at`: {t, say, dur}.
func say_at(key: String, at: float, lo := 1.4, hi := 4.6) -> Dictionary:
	return {"t": at, "say": key, "dur": line_dur(key, lo, hi)}


## A music cue only when the track exists (the music is another stream's file; never a missing-file cue).
func optional_music(at: float, id: String, fade := 2.0) -> Array:
	if ResourceLoader.exists("res://assets/audio/music/%s.wav" % id):
		return [{"t": at, "music": id, "fade": fade}]
	return []


func fx(parent: Node, n: String, fn: Callable) -> Node2D:
	var d := Node2D.new()
	d.name = n
	d.draw.connect(fn)
	parent.add_child(d)
	return d


func lv(section: Dictionary, key: String, fallback := Vector2.ZERO) -> Vector2:
	var v = section.get(key)
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return fallback


## A character sheet sprite (one row of 32 x 56 cells, see env_c4_cine_kit.fig_sheet).
func fig(rel: String, parent: Node) -> Sprite2D:
	var s := sprite(rel, Vector2.ZERO, parent)
	if s.texture:
		s.hframes = maxi(1, s.texture.get_width() / FIG_W)
	return s


## Show frame `i` (wrapped) of the named range `anim` of `index` ({anim: [first, count]}) at feet position `feet`.
func fig_frame(s: Sprite2D, index: Dictionary, anim: String, i: int, feet: Vector2) -> void:
	var r = index.get(anim, [0, 1])
	s.frame = clampi(int(r[0]) + posmod(i, maxi(1, int(r[1]))), 0, maxi(0, s.hframes - 1))
	s.position = (feet - FEET_OFF).round()


## Walk-cycle frame for a walked distance (in-game stride: no foot sliding).
static func walk_i(dist: float) -> int:
	return int(floor(absf(dist) / STRIDE))


## Position along a walk from x0 to x1 starting at t0 (in-game speed); returns [x, walking?].
static func walk_x(time: float, t0: float, x0: float, x1: float, speed := WALK_SPEED) -> Array:
	var d := maxf(0.0, time - t0) * speed
	var span := absf(x1 - x0)
	var dir := signf(x1 - x0)
	if d >= span:
		return [x1, false]
	return [x0 + dir * d, time >= t0]


## Ease in-out of `time` between a and b (0..1).
static func ease01(time: float, a: float, b: float) -> float:
	return ramp01(time, a, b)


## Ease-out (decelerating) 0..1.
static func ease_out(time: float, a: float, b: float) -> float:
	var u := clampf((time - a) / maxf(0.0001, b - a), 0.0, 1.0)
	return 1.0 - (1.0 - u) * (1.0 - u)


## Ease-in (accelerating) 0..1.
static func ease_in(time: float, a: float, b: float) -> float:
	var u := clampf((time - a) / maxf(0.0001, b - a), 0.0, 1.0)
	return u * u


## A strip sprite showing `w` px of a texture (non-tiled when the texture is wider than w).
func window_strip(rel: String, pos: Vector2, w: int, parent: Node) -> Sprite2D:
	return strip(rel, pos, w, parent)


## Draw a horizontal-sheet frame (top-left anchored) on a draw node.
static func draw_cell(ci: CanvasItem, sheet: Texture2D, n: int, i: int, top_left: Vector2,
		mod := Color(1, 1, 1, 1)) -> void:
	if sheet == null:
		return
	var fw := sheet.get_width() / maxi(1, n)
	var src := Rect2(posmod(i, n) * fw, 0, fw, sheet.get_height())
	ci.draw_texture_rect_region(sheet, Rect2(top_left.round(), Vector2(fw, sheet.get_height())), src, mod)


# ------------------------------------------------------------------ polish-pass helpers (additive; nothing above
# changed).  All of them stay pure functions of the timeline time.

## A looping sprite-sheet animation (the levels' own fx strips): frame of `frames` at `fps` with a phase.
func loop_frame(time: float, frames: int, fps: float, phase := 0.0) -> int:
	var r := fps * (0.6 if reduced_motion() else 1.0)
	return posmod(int(floor(time * r + phase * frames)), maxi(1, frames))


## A sprite showing one frame of a horizontal fx strip (frames of equal width), top-left at `pos`.
func fx_sprite(rel: String, frames: int, pos: Vector2, parent: Node, add := false) -> Sprite2D:
	return sprite(rel, pos, parent, maxi(1, frames), add)


## Puffs (steam, smoke, breath) rising from `origin`: `count` puffs spread over a `period`-second life, each
## drifting `drift` px sideways and `rise` px up while it grows through the sheet's frames and fades.
func draw_puffs(ci: CanvasItem, sheet: Texture2D, n: int, origin: Vector2, time: float, count: int, period: float,
		rise: float, drift: float, alpha := 0.7, phase := 0.0, sway := 3.0) -> void:
	if sheet == null:
		return
	var k := motion_k()
	for i in count:
		var age := fposmod(time / period + phase + float(i) / float(count), 1.0)
		var p := origin + Vector2(drift * age * k + sin(age * 5.0 + i * 1.7) * sway * k, -rise * age * k)
		var a := alpha * (1.0 - age) * clampf(age * 6.0, 0.0, 1.0)
		draw_frame(ci, sheet, n, int(age * float(n - 1) + 0.5), p, false, Color(1, 1, 1, a))


## Dust motes drifting slowly inside `rect` (a lamp's beam): `count` specks, each a pure function of t, brighter
## near `focus`; drawn with a 4-frame speck sheet (env_c4_cine_places._motes).
func draw_motes(ci: CanvasItem, sheet: Texture2D, rect: Rect2, focus: Vector2, radius: float, time: float,
		count: int, seed: int, alpha := 0.8) -> void:
	if sheet == null:
		return
	var k := motion_k()
	for i in count:
		var h1 := h01(i, seed)
		var h2 := h01(i, seed + 11)
		var h3 := h01(i, seed + 23)
		var x := rect.position.x + fposmod(h1 * rect.size.x + time * (h3 - 0.5) * 9.0 * k, rect.size.x)
		var y := rect.position.y + fposmod(h2 * rect.size.y + time * (2.0 + h3 * 5.0) * k + sin(time * 0.9 + i) * 3.0,
			rect.size.y)
		var d := Vector2(x, y).distance_to(focus) / maxf(1.0, radius)
		var a := alpha * clampf(1.0 - d, 0.0, 1.0)
		if a <= 0.03:
			continue
		var fi := clampi(int((1.0 - d) * 3.99), 0, 3)
		draw_cell(ci, sheet, 4, fi, Vector2(x, y), Color(1, 1, 1, a))


## Water drops falling from `top` to `bottom` at x positions inside [x0, x1] (each drop a pure function of t),
## with a two-pixel splash where it lands.
func draw_drips(ci: CanvasItem, x0: float, x1: float, top: float, bottom: float, time: float, count: int,
		seed: int, col := Color(0.62, 0.66, 0.70, 0.8)) -> void:
	var k := motion_k()
	for i in count:
		var x := roundf(x0 + h01(i, seed) * (x1 - x0))
		var period := 1.6 + h01(i, seed + 5) * 1.8
		var age := fposmod(time / period + h01(i, seed + 9), 1.0)
		var fall := 0.55
		if age < fall:
			var u := age / fall
			var y := top + (bottom - top) * u * u
			ci.draw_rect(Rect2(Vector2(x, roundf(y)), Vector2(1, 2 + int(u * 3.0 * k))), col)
		elif age < fall + 0.08:
			ci.draw_rect(Rect2(Vector2(x - 2, bottom), Vector2(1, 1)), col)
			ci.draw_rect(Rect2(Vector2(x + 2, bottom), Vector2(1, 1)), col)


## Place a layer of a parallax stack: its home position shifted by the camera x times its parallax factor.
static func par_pos(home: Vector2, cam_x: float, par: float) -> Vector2:
	return Vector2(roundf(home.x - cam_x * par), home.y)


## Snow lit by a lamp: flakes falling through the cone under each light (cones = [[x, y_lamp, half_width_at_floor,
## floor_y], ...]), brighter near the lamp; each flake a pure function of t.
func draw_lit_snow(ci: CanvasItem, cones: Array, time: float, per_cone: int, seed: int,
		col := Color(1.0, 0.86, 0.6, 1.0)) -> void:
	var k := 0.6 if reduced_motion() else 1.0
	for c in cones:
		var cx := float(c[0])
		var top := float(c[1])
		var hw := float(c[2])
		var floor_y := float(c[3])
		for i in per_cone:
			var period := 3.2 + h01(i, seed + 3) * 2.4
			var age := fposmod(time * k / period + h01(i, seed + int(cx)), 1.0)
			var y := top + age * (floor_y - top)
			var spread := hw * (y - top) / maxf(1.0, floor_y - top)
			var x := cx + (h01(i, seed + 7) * 2.0 - 1.0) * spread + sin(time * 1.3 + i) * 2.0 * k
			var a := clampf(1.0 - absf(x - cx) / maxf(1.0, spread + 1.0), 0.0, 1.0) * clampf((1.0 - age) * 2.5, 0.0, 1.0)
			ci.draw_rect(Rect2(Vector2(roundf(x), roundf(y)), Vector2(1 + int(i % 3 == 0), 1 + int(i % 3 == 0))),
				Color(col.r, col.g, col.b, col.a * a * 0.9))


## Deterministic hash in 0..1 (the base's _h is -1..1).
static func h01(i: int, seed: int) -> float:
	return (_h(i, seed) + 1.0) * 0.5


# ------------------------------------------------------------------ round-10 helpers (additive; nothing above changed)

## fig_frame that draws only the part of the cell inside `clip` (a screen rect): a figure inside a door, behind a
## sill, a parapet or a jamb is cut exactly by it.  A clip that holds the whole cell draws it like fig_frame (the
## sprite's region is switched off again); a cell wholly outside the clip hides the sprite.
func fig_frame_clip(s: Sprite2D, index: Dictionary, anim: String, i: int, feet: Vector2, clip: Rect2) -> void:
	var n := maxi(1, s.texture.get_width() / FIG_W) if s.texture else 1
	var r = index.get(anim, [0, 1])
	var f := clampi(int(r[0]) + posmod(i, maxi(1, int(r[1]))), 0, n - 1)
	var tl := (feet - FEET_OFF).round()
	var cell := Rect2(tl, Vector2(FIG_W, FIG_H))
	var c := Rect2(clip.position.round(), clip.size.round())
	if c.encloses(cell):
		s.region_enabled = false
		s.region_rect = Rect2()
		s.hframes = n
		s.frame = f
		s.position = tl
		return
	var vis := cell.intersection(c)
	s.frame = 0
	s.hframes = 1
	s.region_enabled = true
	if vis.size.x < 1.0 or vis.size.y < 1.0:
		s.region_rect = Rect2(f * FIG_W, 0, 1, 1)
		s.position = tl
		s.visible = false
		return
	s.region_rect = Rect2(Vector2(f * FIG_W, 0) + (vis.position - tl), vis.size)
	s.position = vis.position


## No clip at all (for fig_frame_clip).
const NO_CLIP := Rect2(-4096, -4096, 8192, 8192)


## A sprite placed by its frame position that is cut to `clip` (screen rect) -- the same idea for any sheet sprite
## (hframes cells of one row): only the part inside the clip is drawn.
func sprite_clip(s: Sprite2D, frames: int, f: int, top_left: Vector2, clip: Rect2) -> void:
	if s.texture == null:
		return
	var fw := s.texture.get_width() / maxi(1, frames)
	var fh := s.texture.get_height()
	var tl := top_left.round()
	var cell := Rect2(tl, Vector2(fw, fh))
	var c := Rect2(clip.position.round(), clip.size.round())
	var vis := cell.intersection(c)
	s.frame = 0
	s.hframes = 1
	s.region_enabled = true
	if vis.size.x < 1.0 or vis.size.y < 1.0:
		s.region_rect = Rect2(0, 0, 1, 1)
		s.position = tl
		s.visible = false
		return
	s.region_rect = Rect2(Vector2(posmod(f, maxi(1, frames)) * fw, 0) + (vis.position - tl), vis.size)
	s.position = vis.position
