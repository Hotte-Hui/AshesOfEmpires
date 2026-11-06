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
