extends Camera2D
## Pixel-snapped follow camera. `pos` is the continuous top-left of the visible 640x360 window; the Camera2D
## itself sits on whole pixels (viewport has a 1 px margin) and the remainder goes to PixelView.

signal moved(top_left: Vector2)

const VIEW := Vector2(640, 360)

var target: Node2D = null
var bounds := Rect2(0, 0, 640, 360)
var pos := Vector2.ZERO
var drawn := Vector2.ZERO        # what is actually on screen (pixel-locked in gameplay)
var follow_offset := Vector2(0, -70)
var look_ahead := 34.0
var smoothing := 3.2
var cinematic := false   # true: pos is driven by a cinematic (set_top_left / tween_to)
var _look := 0.0
var _tween: Tween


func _ready() -> void:
	anchor_mode = Camera2D.ANCHOR_MODE_FIXED_TOP_LEFT
	position_smoothing_enabled = false
	make_current()


func set_bounds(r: Rect2) -> void:
	bounds = r


func clamp_pos(p: Vector2) -> Vector2:
	var mx := maxf(bounds.position.x, bounds.end.x - VIEW.x)
	var my := maxf(bounds.position.y, bounds.end.y - VIEW.y)
	return Vector2(clampf(p.x, bounds.position.x, mx), clampf(p.y, bounds.position.y, my))


func desired() -> Vector2:
	if target == null or not is_instance_valid(target):
		return pos
	var facing := 0.0
	if target.has_method("get_facing"):
		facing = target.get_facing()
	_look = lerpf(_look, facing * look_ahead, 0.03)
	return clamp_pos(target.global_position + follow_offset + Vector2(_look, 0) - VIEW * 0.5)


func snap_now() -> void:
	_look = 0.0
	pos = desired()
	_apply()


func set_top_left(p: Vector2, clamp_to_bounds := true) -> void:
	pos = clamp_pos(p) if clamp_to_bounds else p
	_apply()


## Cinematic move of the visible window's top-left. Returns the tween (await tween.finished).
func tween_to(p: Vector2, duration: float, trans := Tween.TRANS_SINE) -> Tween:
	cinematic = true
	if _tween and _tween.is_valid():
		_tween.kill()
	_tween = create_tween().set_trans(trans).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(self, "pos", clamp_pos(p), maxf(0.01, duration))
	return _tween


func release() -> void:
	cinematic = false


func _process(delta: float) -> void:
	if not cinematic:
		var d := desired()
		var rate := smoothing
		if Settings.get_value("reduced_motion"):
			rate = 9.0
		pos = pos.lerp(d, 1.0 - exp(-rate * delta))
		if pos.distance_squared_to(d) < 0.0004:
			pos = d
	_apply()


func _apply() -> void:
	# Gameplay: camera locked to whole pixels (player and world share one pixel grid -> no relative jitter).
	# Cinematic pans: sub-pixel remainder applied at display scale for silky slow moves.
	var draw := pos if cinematic else pos.round()
	drawn = draw
	var fl := draw.floor()
	position = fl - Vector2.ONE
	if Game.view:
		Game.view.set_fraction(draw - fl)
	moved.emit(draw)


func top_left() -> Vector2:
	return drawn
