extends Node2D
## Plays a character sprite sheet (assets/characters/<id>/sheet.json, TECHNICAL_ARCHITECTURE §4) on a
## Sprite2D with a CanvasTexture (diffuse + normal) so scene lights wrap around characters.
## Missing art -> a crisp placeholder silhouette, so gameplay never depends on asset delivery.

signal anim_finished(anim_name: String)
signal frame_changed(anim_name: String, frame: int)

const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const FALLBACK := {
	"walk_front": "walk_side", "walk_back": "walk_side", "idle_front": "idle_side", "idle_back": "idle_side",
	"talk_side": "idle_side", "inspect_side": "interact_side", "interact_side": "idle_side",
	"walk_side": "idle_side", "talk_front": "talk_side",
}

var char_id := ""
var sheet: Dictionary = {}
var sprite: Sprite2D
var anim := ""
var speed_scale := 1.0
var _frame := 0
var _t := 0.0
var _flip := false
var _cell := Vector2(32, 56)
var _origin := Vector2(16, 54)
var _done := false


func load_character(id: String) -> bool:
	char_id = id
	if sprite:
		sprite.queue_free()
	sprite = Sprite2D.new()
	sprite.centered = false
	add_child(sprite)
	var dir := "res://assets/characters/%s/" % id
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


func play(a: String, restart := false) -> void:
	a = resolve(a)
	if a == anim and not restart:
		return
	anim = a
	_frame = 0
	_t = 0.0
	_done = false
	_show()


func set_flip(left: bool) -> void:
	if left == _flip:
		return
	_flip = left
	if sprite:
		sprite.flip_h = left
		_apply_offset()


func is_flipped() -> bool:
	return _flip


func _apply_offset() -> void:
	if sprite == null:
		return
	var ox := (_cell.x - _origin.x) if _flip else _origin.x
	sprite.offset = -Vector2(ox, _origin.y)


func _show() -> void:
	var A: Dictionary = sheet.get("anims", {}).get(anim, {})
	if A.is_empty() or sprite == null or sprite.hframes <= 1 and sprite.vframes <= 1:
		return
	var idx := int(A.get("row", 0)) * sprite.hframes + _frame
	sprite.frame = clampi(idx, 0, sprite.hframes * sprite.vframes - 1)


func _process(delta: float) -> void:
	var A: Dictionary = sheet.get("anims", {}).get(anim, {})
	if A.is_empty() or _done:
		return
	_t += delta * speed_scale
	var spf := 1.0 / maxf(0.1, float(A.get("fps", 8)))
	while _t >= spf:
		_t -= spf
		_frame += 1
		var n := int(A.get("frames", 1))
		if _frame >= n:
			if bool(A.get("loop", true)):
				_frame = 0
			else:
				_frame = n - 1
				_done = true
				_show()
				anim_finished.emit(anim)
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
