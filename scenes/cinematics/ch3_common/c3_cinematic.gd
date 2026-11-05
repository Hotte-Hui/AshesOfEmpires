extends Node2D
## Shared base of the Chapter-3 cinematic scenes (TECHNICAL_ARCHITECTURE §12.5, C3_DESIGN §2.9).
## Owner: cinematics stream.  Contract (runner: scripts/core/chapter_ext.gd play_cinematic):
##   signal finished          exactly once per run: natural end, skip(), or skip() after the natural end
##   configure(ctx)           ctx = {"choices": {...}, "flags": {...}, "symbols": bool}; picks the inner lines
##   play()                   starts the timeline at t = 0 (calling it again starts a new run)
##   skip()                   idempotent; jumps to the final frame and finishes
##   grade_preset / max_duration (exported; the runner reads them)
## Everything on screen is a pure function of the timeline time `t` (`_apply(t)`), so frames are
## deterministic: seek(t) / advance(dt) drive it for tools and tests, cues (subtitles, sound) fire once
## when `t` passes them.  Content is drawn in world pixels 0..640 x 0..360; the camera is parked at the
## origin in cinematic mode while the scene is in the tree and released on exit.
## Dev-only command-line switches (read here, nowhere else):
##   --cine-t=SECONDS        after play(): jump to SECONDS and freeze (deterministic --capture frames)
##   --cine-rm=0|1           force reduced motion off/on for this run
##   --cine-flags=a=1,b=0    merge story flags into configure(ctx) (to capture the line variants)

signal finished

const ASSETS := "res://assets/cinematics/ch3/"
const VIEW := Vector2(640, 360)
## visible band inside the cinematic letterbox (138 px bars at 1080p = 46 world px)
const SAFE_TOP := 46
const SAFE_BOTTOM := 314

@export var grade_preset := "c3_cine"
@export var max_duration := 30.0
## -1 = Settings "reduced_motion", 0 = force off, 1 = force on (tests, tools)
@export var reduced_motion_override := -1
## false = never touch Game/Audio/Loc subtitles (unit tests construct scenes without the director)
@export var use_director := true
## playback speed of the frame-driven timeline (tools; 1.0 in the game)
@export var time_scale := 1.0

var duration := 10.0
var t := 0.0
var flags: Dictionary = {}
var choices: Dictionary = {}
var symbols := true
## subtitle keys spoken during the current run, in order (tests compare with chosen_lines())
var said: Array = []
## texture paths that could not be loaded (tests require this to stay empty)
var missing: Array = []
var finish_count := 0

var _playing := false
var _finished := false
var _cues: Array = []
var _cue_i := 0
var _cam_taken := false
var _sub_until := -1.0
var _freeze_at := -1.0
var _frozen := false
var _dev_flags: Dictionary = {}
var _rm_cli := -1
var _configured := false


func _ready() -> void:
	_parse_dev_args()
	_build()
	if not _configured:
		configure({})
	_take_camera()
	_apply(0.0)


func _exit_tree() -> void:
	if _cam_taken and _live() and is_instance_valid(Game.camera):
		Game.camera.release()
	_cam_taken = false
	if _live() and t < _sub_until:
		_hide_subtitle()


# ------------------------------------------------------------------ contract
func configure(ctx: Dictionary) -> void:
	_configured = true
	var f = ctx.get("flags", {})
	flags = (f as Dictionary).duplicate(true) if f is Dictionary else {}
	flags.merge(_dev_flags, true)
	var c = ctx.get("choices", {})
	choices = (c as Dictionary).duplicate(true) if c is Dictionary else {}
	symbols = bool(ctx.get("symbols", true))
	_on_configured()
	_cues = _make_cues()
	_cues.sort_custom(func(a, b): return float(a["t"]) < float(b["t"]))


func play() -> void:
	t = 0.0
	_cue_i = 0
	_finished = false
	_playing = true
	_frozen = false
	said.clear()
	_sub_until = -1.0
	_take_camera()
	_apply(0.0)
	_fire_cues(0.0)
	if _freeze_at >= 0.0:
		seek(_freeze_at)
		_frozen = true


func skip() -> void:
	if _finished:
		return
	var was := t
	_playing = false
	t = duration
	_apply(t)
	if _live() and was < _sub_until:
		_hide_subtitle()   # a line of ours would otherwise linger over the next level's fade-in
	_finish()


func is_finished() -> bool:
	return _finished


func is_playing() -> bool:
	return _playing


## Jump to time `time` without firing the cues before it (tools / dev captures).
func seek(time: float) -> void:
	t = clampf(time, 0.0, duration)
	_cue_i = 0
	while _cue_i < _cues.size() and float(_cues[_cue_i]["t"]) < t:
		_cue_i += 1
	_apply(t)


## Advance the timeline by dt seconds exactly like _process does (tests drive scenes without frames).
func advance(dt: float) -> void:
	if _playing:
		_step(dt)


func get_time() -> float:
	return t


func get_duration() -> float:
	return duration


## Ordered subtitle keys this run will show for the configured flags (overridden per scene).
func chosen_lines() -> Array:
	return []


func get_shot_id() -> String:
	return ""


# ------------------------------------------------------------------ to override
func _build() -> void:
	pass


func _on_configured() -> void:
	pass


func _make_cues() -> Array:
	return []


func _apply(_time: float) -> void:
	pass


# ------------------------------------------------------------------ timeline
func _process(delta: float) -> void:
	if _playing and not _frozen:
		_step(delta * time_scale)


func _step(dt: float) -> void:
	t = minf(t + maxf(dt, 0.0), duration)
	_apply(t)
	_fire_cues(t)
	if t >= duration:
		_playing = false
		_finish()


func _finish() -> void:
	if _finished:
		return
	_finished = true
	_playing = false
	finish_count += 1
	finished.emit()


func _fire_cues(now: float) -> void:
	while _cue_i < _cues.size() and float(_cues[_cue_i]["t"]) <= now + 0.00001:
		_run_cue(_cues[_cue_i])
		_cue_i += 1


func _run_cue(c: Dictionary) -> void:
	if c.has("say"):
		_say(str(c["say"]), float(c.get("dur", 4.0)))
	if not _live():
		return
	if c.has("sfx"):
		Audio.sfx(str(c["sfx"]), float(c.get("db", 0.0)), float(c.get("pv", 0.05)))
	if c.has("amb"):
		Audio.play_ambience(str(c["amb"]), float(c.get("fade", 1.5)))
	if c.has("music"):
		if str(c["music"]) == "":
			Audio.stop_music(float(c.get("fade", 2.0)))
		else:
			Audio.play_music(str(c["music"]), float(c.get("fade", 2.0)))


func _say(key: String, dur: float) -> void:
	said.append(key)
	_sub_until = t + dur
	if _live():
		Game.subtitle(Loc.t(key), dur)


func _hide_subtitle() -> void:
	var u = Game.get("ui")
	if u == null:
		return
	var sub = u.get("subtitles")
	if sub and sub.has_method("hide_subtitle"):
		sub.hide_subtitle()


## true when the scene runs inside the game director (main scene registered): subtitles, audio, camera.
func _live() -> bool:
	return use_director and is_inside_tree() and Game != null and Game.get("main") != null


func _take_camera() -> void:
	if not _live():
		return
	var cam = Game.get("camera")
	if cam == null or not is_instance_valid(cam):
		return
	cam.cinematic = true
	cam.set_top_left(Vector2.ZERO, false)
	_cam_taken = true


func reduced_motion() -> bool:
	if reduced_motion_override >= 0:
		return reduced_motion_override == 1
	if _rm_cli >= 0:
		return _rm_cli == 1
	return bool(Settings.get_value("reduced_motion")) if Settings else false


func _parse_dev_args() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--cine-t="):
			_freeze_at = float(a.get_slice("=", 1))
		elif a.begins_with("--cine-rm="):
			_rm_cli = 1 if a.get_slice("=", 1) != "0" else 0
		elif a.begins_with("--cine-flags="):
			for kv in a.substr(13).split(",", false):
				var p := kv.split("=")
				if p.size() == 2:
					_dev_flags[p[0]] = int(p[1]) if p[1].is_valid_int() else p[1]


# ------------------------------------------------------------------ helpers for subclasses
static func ge1(f: Dictionary, key: String) -> bool:
	var v = f.get(key)
	if v == null or typeof(v) == TYPE_BOOL:
		return v == true
	if typeof(v) == TYPE_STRING:
		return str(v).is_valid_float() and float(v) >= 1.0
	return float(v) >= 1.0


func tex(rel: String) -> Texture2D:
	var path := ASSETS + rel
	if ResourceLoader.exists(path):
		var r = load(path)
		if r is Texture2D:
			return r
	if FileAccess.file_exists(path):   # not imported yet (fresh generator run in a dev checkout)
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	if not missing.has(path):
		missing.append(path)
	return null


static func additive() -> CanvasItemMaterial:
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return m


## Sprite at an integer top-left; hframes for sheets; optional region (scrolling strips).
func sprite(rel: String, pos: Vector2, parent: Node, hframes := 1, add := false, vframes := 1) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex(rel)
	s.centered = false
	s.position = pos.round()
	s.hframes = maxi(1, hframes)
	s.vframes = maxi(1, vframes)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if add:
		s.material = additive()
	s.light_mask = 0
	parent.add_child(s)
	return s


## Horizontally scrolling strip: shows `w` px of a tileable texture starting at `offset`.
func strip(rel: String, pos: Vector2, w: int, parent: Node, add := false) -> Sprite2D:
	var s := sprite(rel, pos, parent, 1, add)
	s.region_enabled = true
	s.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	var h := s.texture.get_height() if s.texture else 1
	s.region_rect = Rect2(0, 0, w, h)
	return s


static func set_scroll(s: Sprite2D, offset: float) -> void:
	if s == null or s.texture == null:
		return
	var tw := float(s.texture.get_width())
	var r := s.region_rect
	r.position.x = fposmod(floorf(offset), tw)
	s.region_rect = r


func group(n: String, parent: Node = null) -> Node2D:
	var g := Node2D.new()
	g.name = n
	(parent if parent else self).add_child(g)
	return g


## Smooth 0..1 ramp of `x` between a and b.
static func ramp01(x: float, a: float, b: float) -> float:
	if b <= a:
		return 1.0 if x >= b else 0.0
	var u := clampf((x - a) / (b - a), 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


## Deterministic hash noise in -1..1 (no global random state).
static func hnoise(x: float, seed := 0) -> float:
	var i := floori(x)
	var f := x - i
	var a := _h(i, seed)
	var b := _h(i + 1, seed)
	f = f * f * (3.0 - 2.0 * f)
	return lerpf(a, b, f)


static func _h(i: int, seed: int) -> float:
	var n := (i * 374761393 + seed * 668265263) & 0x7fffffff
	n = ((n ^ (n >> 13)) * 1274126177) & 0x7fffffff
	return float(n & 0xffff) / 32767.5 - 1.0
