extends "res://scripts/levels/karsk/karsk_actor.gd"
## Payoff of the station side task „Wagen drei ist kalt“ (round 8, feel_r8). The step text of
## veltrava.task.heating.thaw says it: the hissing outside dies down, the pipes inside start to knock, and behind
## the frosted window somebody wipes a peephole and raises a hand. So, once that step is found (it is part of the
## finished task as well):
##  * live, as soon as the interaction is over: the steam leak heater_leak_23 fades out, the pipes knock, a hand
##    wipes a peephole into window 6 of car 3 and waves (window_life frame 3, the raised hand), then the frost of
##    all compartments recedes from the top, and a lamp goes on in compartment 4 (the typists, coats off);
##  * on every later level load (and when the task is done): the leak decal is hidden and car 3 is thawed.
## Purely visual; never touches Story, Explore or the task state. Art: tools/pixelgen/env_veltrava_station_thaw.py
## (assets/environments/veltrava_station/thaw/: every strip's frame 0 is the layer itself -> no seam). The
## sprites are children of the train_near layer (same plane, same per-texel light and dither anchor).

var band_sprite := "res://assets/environments/veltrava_station/thaw/car3_thaw.png"
var peep_sprite := "res://assets/environments/veltrava_station/thaw/car3_peephole.png"
var layer_name := "train_near"
var band_at := Vector2(357, 25)        ## layer px of the window band's top-left
var peep_at := Vector2(478, 25)        ## layer px of window 6 (incl. its frame)
var band_frames := 5                   ## 0 as painted, 1..3 frost receding, 4 thawed
var peep_frames := 10                  ## 0 frosted, 1-4 wiping, 5 face, 6/7 waving, 8 face, 9 hand down
var leak_decal := "heater_leak_23"
var thaw_step := "veltrava.task.heating.thaw"
var task_id := "veltrava.task.heating"
var knock_sfx := "berlin_radiator_knock"

## [frame, seconds] of the peephole scene; then the band steps through the thaw
const PEEP_SCRIPT := [[0, 0.35], [1, 0.22], [2, 0.22], [3, 0.22], [4, 0.36], [5, 0.85], [6, 0.24], [7, 0.24],
	[6, 0.24], [7, 0.24], [6, 0.24], [7, 0.3], [8, 1.3], [9, 0.9]]
const THAW_STEPS := [[1, 2.2], [2, 2.2], [3, 2.6], [4, 0.0]]
const LEAK_FADE := 1.4
const PEEP_DELAY := 1.1

var state := "frozen"                  ## frozen | waiting (step found, interaction still open) | live | thawed
var _band: Sprite2D
var _band_e: Sprite2D
var _peep: Sprite2D
var _peep_e: Sprite2D
var _leak: Node2D
var _leak_a := 1.0
var _t := 0.0
var _seq: Array = []                   # remaining [kind, frame, seconds] of the live sequence
var _knocks: Array = []                # seconds until the next pipe knocks
var _explore: Node


func _setup() -> void:
	var lvl := _level()
	var holder: Node2D = null
	var strength := 0.22
	if lvl != null:
		var bd = lvl.get("backdrop")
		if bd != null:
			holder = (bd.get("layers_by_name") as Dictionary).get(layer_name, null)
			_leak = (bd.get("decals_by_name") as Dictionary).get(leak_decal, null)
		var man = lvl.get("manifest")
		if man is Dictionary:
			for L in man.get("layers", []):
				if L is Dictionary and str(L.get("name", "")) == layer_name:
					strength = float(L.get("emission_strength", 0.22))
	if _leak != null:
		_leak_a = _leak.modulate.a
	var home := Vector2(0, 157)
	if holder != null:
		home = holder.get_meta("home", holder.position)
	_band = _sprite(band_sprite, band_frames, holder, band_at, home)
	_band_e = _glow(band_sprite, band_frames, holder, band_at, strength)
	_peep = _sprite(peep_sprite, peep_frames, holder, peep_at, home)
	_peep_e = _glow(peep_sprite, peep_frames, holder, peep_at, strength)
	_show_band(-1)
	_show_peep(-1)
	_explore = get_node_or_null("/root/Explore")
	if is_thawed_now():
		set_thawed()
	elif _explore != null and _explore.has_signal("found"):
		_explore.found.connect(_on_found)


func _exit_tree() -> void:
	if _explore != null and _explore.has_signal("found") and _explore.found.is_connected(_on_found):
		_explore.found.disconnect(_on_found)


## True when the stop cock was thawed in this state (the step, or the whole task, is done).
func is_thawed_now() -> bool:
	if _explore == null:
		return false
	if _explore.has_method("is_found") and bool(_explore.is_found(thaw_step)):
		return true
	if _explore.has_method("task_state"):
		return str(_explore.task_state(task_id).get("state", "")) == "done"
	return false


## Final look without the sequence (level load after the task).
func set_thawed() -> void:
	state = "thawed"
	_seq.clear()
	if _leak != null:
		_leak.visible = false
	_show_peep(-1)
	_show_band(band_frames - 1)


func _on_found(id: String) -> void:
	if id == thaw_step and state == "frozen":
		state = "waiting"


## Starts the live sequence (also used by tests and the capture harness).
func play_thaw() -> void:
	state = "live"
	_t = 0.0
	_seq.clear()
	_seq.append(["wait", -1, PEEP_DELAY])
	for s in PEEP_SCRIPT:
		_seq.append(["peep", int(s[0]), float(s[1])])
	for s in THAW_STEPS:
		_seq.append(["band", int(s[0]), float(s[1])])
	_knocks = [0.55, 1.7, 5.2, 8.9]


func _tick(delta: float) -> void:
	match state:
		"waiting":
			var g := game()
			if g == null or not (bool(g.get("busy")) or bool(g.get("in_cinematic"))):
				play_thaw()
		"live":
			_live(delta)


func _live(delta: float) -> void:
	_t += delta
	if _leak != null and _leak.visible:
		_leak.modulate.a = _leak_a * clampf(1.0 - _t / LEAK_FADE, 0.0, 1.0)
		if _t >= LEAK_FADE:
			_leak.visible = false
	while not _knocks.is_empty() and _t >= float(_knocks[0]):
		_knocks.pop_front()
		sfx(knock_sfx, dist_db(Vector2(440, 190), -10.0, -24.0), 0.08)
	if _seq.is_empty():
		state = "thawed"
		return
	var cur: Array = _seq[0]
	match str(cur[0]):
		"peep":
			_show_peep(int(cur[1]))
		"band":
			_show_peep(-1)
			_show_band(int(cur[1]))
	cur[2] = float(cur[2]) - delta
	if float(cur[2]) <= 0.0:
		_seq.pop_front()
		if _seq.is_empty():
			state = "thawed"
			_show_band(band_frames - 1)


func _show_band(frame: int) -> void:
	for s in [_band, _band_e]:
		if s != null:
			s.visible = frame >= 0
			s.frame = clampi(frame, 0, band_frames - 1)


func _show_peep(frame: int) -> void:
	for s in [_peep, _peep_e]:
		if s != null:
			s.visible = frame >= 0
			s.frame = clampi(frame, 0, peep_frames - 1)


func band_frame() -> int:
	return _band.frame if _band != null and _band.visible else -1


func peep_frame() -> int:
	return _peep.frame if _peep != null and _peep.visible else -1


func leak_visible() -> bool:
	return _leak != null and _leak.visible


func _level() -> Node:
	var n := get_parent()
	while n != null and n.get("backdrop") == null:
		n = n.get_parent()
	return n


func _sprite(path: String, frames: int, holder: Node2D, at: Vector2, home: Vector2) -> Sprite2D:
	var t := canvas_tex(path, true)
	if t == null:
		push_warning("StationThaw: missing " + path)
		return null
	var s := Sprite2D.new()
	s.texture = t
	s.centered = false
	s.hframes = frames
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.position = at if holder != null else home + at
	var parent_node: Node2D = holder if holder != null else self
	parent_node.add_child(s)
	texel(s, Vector2(t.get_width() / float(frames), t.get_height()), home + at)
	return s


func _glow(path: String, frames: int, holder: Node2D, at: Vector2, strength: float) -> Sprite2D:
	var e := load_tex(path.get_basename() + "_e.png")
	if e == null:
		return null
	var s := Sprite2D.new()
	s.texture = e
	s.centered = false
	s.hframes = frames
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	s.material = mat
	s.modulate = Color(1, 1, 1, strength)
	s.position = at if holder != null else Vector2(0, 157) + at
	var parent_node: Node2D = holder if holder != null else self
	parent_node.add_child(s)
	return s
