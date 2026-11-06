extends "res://scenes/cinematics/c4_common/c4_cinematic.gd"
## Shared base of the Chapter-4-part-2 cinematics LS_C4P2_Depot / _Steam / _Book / _Express / _Clock
## (documentation/C4P2_DESIGN.md §2.9).  Owner: cine stream (round 10).  Reuses the §12.5 runtime of
## ch3_common/c3_cinematic.gd (finished exactly once, idempotent skip(), configure(ctx), seek()/advance(), cue list,
## reduced motion), the C3P2 helpers (choice(), schedule(), shot tables, snow, flames) and the C4 helpers (line_dur,
## walk_x / walk_i at the in-game stride, optional_music, fx draw nodes) unchanged, and adds:
##   * textures from assets/cinematics/c4p2/ (tools/pixelgen/env_c4p2_cine*.py) and its layout.json sections
##   * cells(): sprite sheets with any cell width (the films' rig figures are 48 px wide: shovels, instruments)
##   * puffs(): steam / smoke / breath emitters drawn as pure functions of t (born on a fixed beat, each puff plays
##     its sheet over its life while it drifts)
##   * optional_amb(): an ambience cue only when the file exists (the audio stream's loops are optional)
##   * c4g() / c4d(): the recorded part-2 / part-1 decisions with their defaults (publish_now / name_marta)
## Every frame stays a pure function of t; match cuts are hard cuts (no white dip).

const ASSETS5 := "res://assets/cinematics/c4p2/"

var _layout5: Dictionary = {}


func _layout_section(section: String) -> Dictionary:
	if _layout5.is_empty():
		var p := ASSETS5 + "layout.json"
		if FileAccess.file_exists(p):
			var d = JSON.parse_string(FileAccess.get_file_as_string(p))
			if d is Dictionary:
				_layout5 = d
	var s = _layout5.get(section, {})
	return s if s is Dictionary else {}


## Texture under assets/cinematics/c4p2/ (same fallbacks and `missing` bookkeeping as the base).
func tex(rel: String) -> Texture2D:
	var path := ASSETS5 + rel
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


## A sprite sheet of `cell_w` px wide cells (one row); frame 0 shown.
func cells(rel: String, parent: Node, cell_w: int, pos := Vector2.ZERO, add := false) -> Sprite2D:
	var s := sprite(rel, pos, parent, 1, add)
	if s.texture:
		s.hframes = maxi(1, s.texture.get_width() / maxi(1, cell_w))
	return s


## Frame of a looping animation: `fps` frames per second from t0 with a phase (frames).
static func loop_frame(time: float, fps: float, n: int, phase := 0, t0 := 0.0) -> int:
	return posmod(int(floor(maxf(0.0, time - t0) * fps)) + phase, maxi(1, n))


## Frame of a one-shot animation: plays n frames over [t0, t1] and holds the last.
static func once_frame(time: float, t0: float, t1: float, n: int) -> int:
	if time <= t0:
		return 0
	return clampi(int(floor((time - t0) / maxf(0.0001, t1 - t0) * n)), 0, n - 1)


## Steam / breath puffs drawn into `ci` (call from its draw callback): a puff is born every `every` s from t0
## until t1 at `pos` (+ a small deterministic jitter), lives `life` s, drifts with `vel` (px/s) and plays the n
## frames of `sheet` over its life.  Reduced motion halves the drift.
func puffs(ci: CanvasItem, sheet: Texture2D, n: int, time: float, t0: float, t1: float, every: float, life: float,
		pos: Vector2, vel: Vector2, seed: int, mod := Color(1, 1, 1, 1), jit := Vector2(3, 2)) -> void:
	if sheet == null or time < t0:
		return
	var k := maxi(0, int(floor((time - t0 - life) / every)))
	var guard := 0
	while guard < 64:
		guard += 1
		var born := t0 + k * every
		if born > time or born > t1:
			break
		var age := time - born
		if age < life:
			var u := age / life
			var j := Vector2(hnoise(k * 1.7, seed) * jit.x, hnoise(k * 2.3, seed + 5) * jit.y)
			draw_frame(ci, sheet, n, mini(n - 1, int(u * n)), (pos + j + vel * age * motion_k()).round(), false, mod)
		k += 1


## An ambience cue only when its file exists (the audio stream's loops are optional at runtime).
func optional_amb(at: float, id: String, fade := 1.5) -> Array:
	if id == "" or ResourceLoader.exists("res://assets/audio/amb/%s.wav" % id):
		return [{"t": at, "amb": id, "fade": fade}]
	return []


## c4g_choose (KarskB): publish_now unless protect_first was recorded (the first option is the default, like
## every other default of the drivers).
func c4g() -> String:
	return "protect_first" if choice("c4g_choose") == "protect_first" else "publish_now"


## c4d_choose (part 1, the annex counter): name_marta unless protect_marta was recorded.
func c4d() -> String:
	return "protect_marta" if choice("c4d_choose") == "protect_marta" else "name_marta"


## Additive sprite (glows, beams) with a modulate alpha.
func glow(rel: String, parent: Node, pos := Vector2.ZERO) -> Sprite2D:
	return sprite(rel, pos, parent, 1, true)
