extends Node2D
## Plays a character sprite sheet (assets/characters/<id>/sheet.json, TECHNICAL_ARCHITECTURE §4) on a
## Sprite2D with a CanvasTexture (diffuse + normal) so scene lights wrap around characters.
## Missing art -> a crisp placeholder silhouette, so gameplay never depends on asset delivery.
##
## Round 2 additions (all optional, driven by sheet.json):
## * Idle variants: a looping row may list one-shot "variants" (blink, glance back, character gesture)
##   with a "variant_gap" [min, max] in seconds. At the end of a loop the rig occasionally shows one variant
##   and returns to the base row. `anim` keeps the logical (base) name, so callers that re-request the same
##   animation every frame (player.gd) never cancel a variant.
## * Soft turns: turn_to(left) shows the front-facing frame for a moment before mirroring (NPCs, and since
##   round 7 the player: turn_to(left, hold, "walk_front") keeps the stride while walking). Row changes during
##   the turn keep the turn frame on screen; turning back mid-turn cancels it.
## * play_once(name, then): one-shot row that returns to `then` afterwards.
## * view_hint (round 7): "front" / "back" -- requests for "*_side" rows play the matching "*_front" /
##   "*_back" row when the sheet has it. Dialogue code asks for "talk_side" / "idle_side" without knowing
##   how the actor stands; an actor facing the camera now talks facing the camera (talk_front).
## Normal maps: the sprite is mirrored with flip_h (never a negative scale), so Godot negates the normal
## map's x for flipped draws and lights keep wrapping around the correct side (verified in
## tests/visual/char_light_test.tscn).

signal anim_finished(anim_name: String)
signal frame_changed(anim_name: String, frame: int)

const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const FALLBACK := {
	"walk_front": "walk_side", "walk_back": "walk_side", "idle_front": "idle_side", "idle_back": "idle_side",
	"talk_side": "idle_side", "inspect_side": "interact_side", "interact_side": "idle_side",
	"walk_side": "idle_side", "talk_front": "talk_side", "work_side": "idle_side",
	"gesture_side": "idle_side", "look_side": "idle_side", "blink_side": "idle_side",
	"blink_front": "idle_front", "talk_back": "idle_back",
}

var char_id := ""
var sheet: Dictionary = {}
var sprite: Sprite2D
var anim := ""                  ## logical animation (what callers asked for)
var speed_scale := 1.0
var variants_enabled := true    ## occasional idle variants (blink / glance / gesture)
var view_hint := ""             ## "" | "front" | "back": maps "*_side" requests to that view (see header)
var _row_anim := ""             ## row actually shown (== anim, or one of its variants)
var _frame := 0
var _t := 0.0
var _flip := false
var _cell := Vector2(32, 56)
var _origin := Vector2(16, 54)
var _done := false
var _var_wait := 0.0
var _once_then := ""
var _turn_left := false
var _turn_t := -1.0
var _turn_row := ""             ## row shown while turning (idle_front, or walk_front for a walking turn)
var _rng := RandomNumberGenerator.new()
## Round 8 (C3P2 §6): per-scene LOOKS -- character id -> sheet directory ("alexei" -> "alexei_soot"). Game sets it
## whenever the playing Story scene changes; identity (char_id, dialogue speaker) never changes.
static var looks: Dictionary = {}
var carry := false              ## holding the file: idle/walk side rows play carry_idle_side / carry_side when present


static func look_of(id: String) -> String:
	var l := str(looks.get(id, ""))
	return l if l != "" and FileAccess.file_exists("res://assets/characters/%s/sheet.json" % l) else id



func _init() -> void:
	_rng.randomize()


func load_character(id: String) -> bool:
	char_id = id
	if sprite:
		sprite.queue_free()
	sprite = Sprite2D.new()
	sprite.centered = false
	add_child(sprite)
	var dir := "res://assets/characters/%s/" % look_of(id)
	if FileAccess.file_exists(dir + "sheet.json"):
		var data = JSON.parse_string(FileAccess.get_file_as_string(dir + "sheet.json"))
		var t := LayerStack.canvas_tex(dir + "sheet.png", true)
		if typeof(data) == TYPE_DICTIONARY and t:
			sheet = data
			_cell = LayerStack._v2(sheet.get("cell", [32, 56]))
			_origin = LayerStack._v2(sheet.get("origin", [_cell.x * 0.5, _cell.y - 2]))
			sprite.texture = t
			sprite.hframes = maxi(1, int(t.get_width() / _cell.x))
			sprite.vframes = maxi(1, int(t.get_height() / _cell.y))
			_apply_offset()
			play(first_idle(), true)
			return true
	_placeholder()
	return false


func first_idle() -> String:
	for a in ["idle_side", "idle_front"]:
		if has_anim(a):
			return a
	var anims: Dictionary = sheet.get("anims", {})
	return anims.keys()[0] if not anims.is_empty() else ""


func has_anim(a: String) -> bool:
	return sheet.get("anims", {}).has(a)


## Movement speed (px/s) at which the planted foot of a walk animation does not slide (sheet.json
## "ground_speed"); 0 if unknown. Callers scale playback by actual_speed / ground_speed.
func ground_speed(a: String) -> float:
	var gs = sheet.get("ground_speed", {})
	if gs is Dictionary and gs.has(a):
		return float(gs[a])
	return 0.0


func resolve(a: String) -> String:
	var guard := 0
	while not has_anim(a) and FALLBACK.has(a) and guard < 6:
		a = FALLBACK[a]
		guard += 1
	return a


## "talk_side" -> "talk_front" while view_hint is "front" (only when the sheet has that row).
func view_row(a: String) -> String:
	if carry and view_hint == "" and (a == "idle_side" or a == "walk_side"):
		var cr := "carry_idle_side" if a == "idle_side" else "carry_side"
		if has_anim(cr):
			return cr
	if view_hint != "" and a.ends_with("_side"):
		var v := a.trim_suffix("_side") + "_" + view_hint
		if has_anim(v):
			return v
	return a


func play(a: String, restart := false) -> void:
	a = resolve(view_row(a))
	if a == anim and not restart:
		return
	anim = a
	_once_then = ""
	_start_row(a)
	_roll_variant_wait()


## Plays a one-shot row, then continues with `then` (default: the previous logical animation).
func play_once(a: String, then := "") -> void:
	var back := then if then != "" else anim
	a = resolve(a)
	if not has_anim(a):
		return
	anim = a
	_once_then = resolve(back)
	_start_row(a)


func set_flip(left: bool) -> void:
	_turn_t = -1.0
	if left == _flip:
		return
	_flip = left
	if sprite:
		sprite.flip_h = left
		_apply_offset()


func is_flipped() -> bool:
	return _flip


## Soft turn: shows the front-facing frame for `hold` seconds, then mirrors (falls back to an instant flip
## when the sheet has no front row). `row` picks the in-between frame: "" = idle_front frame 0, "walk_front" =
## the walk_front frame at the current walk phase (a turn while walking keeps the stride). Returns true when
## a turn was started or is running; turning back to the current facing mid-turn cancels the turn.
func turn_to(left: bool, hold := 0.14, row := "") -> bool:
	if left == _flip and _turn_t < 0.0:
		return false
	if _turn_t >= 0.0:
		if left == _turn_left:
			return true
		if left == _flip:            # changed its mind mid-turn: back to the current facing at once
			_turn_t = -1.0
			_show()
			return true
	var front := row if row != "" and has_anim(row) else ("idle_front" if has_anim("idle_front") else "")
	if front == "" or hold <= 0.0:
		set_flip(left)
		return true
	_turn_left = left
	_turn_t = hold
	_turn_row = front
	_show()
	return true


func is_turning() -> bool:
	return _turn_t >= 0.0


func current_row() -> String:
	return _row_anim


func current_frame() -> int:
	return _frame


func _apply_offset() -> void:
	if sprite == null:
		return
	var ox := (_cell.x - _origin.x) if _flip else _origin.x
	sprite.offset = -Vector2(ox, _origin.y)


func _row(a: String) -> Dictionary:
	return sheet.get("anims", {}).get(a, {})


func _start_row(a: String) -> void:
	_row_anim = a
	_frame = 0
	_t = 0.0
	_done = false
	_show()


func _roll_variant_wait() -> void:
	var gap = _row(anim).get("variant_gap", [2.5, 6.0])
	if gap is Array and gap.size() == 2:
		_var_wait = _rng.randf_range(float(gap[0]), float(gap[1]))
	else:
		_var_wait = _rng.randf_range(2.5, 6.0)


func _show() -> void:
	if _turn_t >= 0.0 and _turn_row != "":
		var n := int(_row(_turn_row).get("frames", 1))
		_show_cell(_turn_row, (_frame % maxi(1, n)) if _turn_row.begins_with("walk") else 0)
		return
	_show_cell(_row_anim, _frame)


func _show_cell(row_name: String, f: int) -> void:
	var A := _row(row_name)
	if A.is_empty() or sprite == null or sprite.hframes <= 1 and sprite.vframes <= 1:
		return
	var idx := int(A.get("row", 0)) * sprite.hframes + f
	sprite.frame = clampi(idx, 0, sprite.hframes * sprite.vframes - 1)


func _process(delta: float) -> void:
	if _turn_t >= 0.0:
		_turn_t -= delta
		if _turn_t < 0.0:
			var l := _turn_left
			set_flip(l)
			_show()
		return
	var A := _row(_row_anim)
	if A.is_empty() or _done:
		return
	if _row_anim == anim and variants_enabled and A.has("variants"):
		_var_wait -= delta
	_t += delta * speed_scale
	var spf := 1.0 / maxf(0.1, float(A.get("fps", 8)))
	while _t >= spf:
		_t -= spf
		_frame += 1
		var n := int(A.get("frames", 1))
		if _frame >= n:
			if _row_anim != anim:
				# a variant finished -> back to the base loop
				_start_row(anim)
				_roll_variant_wait()
				frame_changed.emit(anim, _frame)
				return
			if bool(A.get("loop", true)):
				if _var_wait <= 0.0 and variants_enabled and A.has("variants"):
					var vs: Array = A["variants"]
					var v := str(vs[_rng.randi() % vs.size()])
					if has_anim(v):
						_start_row(v)
						frame_changed.emit(anim, _frame)
						return
					_roll_variant_wait()
				_frame = 0
			else:
				_frame = n - 1
				_done = true
				_show()
				var fin := anim
				anim_finished.emit(fin)
				if _once_then != "" and anim == fin:
					var nxt := _once_then
					_once_then = ""
					anim = nxt
					_start_row(nxt)
					_roll_variant_wait()
				return
		_show()
		frame_changed.emit(anim, _frame)


func _placeholder() -> void:
	var img := Image.create(16, 48, false, Image.FORMAT_RGBA8)
	var body := Color("#1b2a2c")
	var rim := Color("#6c7a62")
	for y in 48:
		for x in 16:
			var inside := false
			if y < 9:
				inside = Vector2(x - 7.5, y - 4.5).length() < 4.2
			elif y < 46:
				var half := 5.5 if y < 30 else 4.5
				inside = absf(x - 7.5) < half
			if inside:
				img.set_pixel(x, y, rim if x >= 11 or (y < 9 and x >= 9) else body)
	sprite.texture = ImageTexture.create_from_image(img)
	_cell = Vector2(16, 48)
	_origin = Vector2(8, 47)
	_apply_offset()
