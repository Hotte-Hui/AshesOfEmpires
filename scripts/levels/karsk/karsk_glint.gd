extends "res://scripts/levels/karsk/karsk_actor.gd"
## Small animated details that make hidden or tiny finds discoverable without pointing at them:
##   mode "glint": a cold glint every `period` seconds (frames 1-2-3-2-1, then off) — additive, unshaded
##   mode "gust":  frame 0 at rest; flaps through frames 1..n-1 while KarskWind blows (cloth corner, mitten)
## `offset` = sprite top-left relative to the node (the node sits at the y it should sort with).

const Wind := preload("res://scripts/levels/karsk/karsk_wind.gd")

var sprite := ""
var frames := 5.0
var offset: Array = [0, 0]
var period: Array = [4.0, 7.0]
var mode := "glint"
var lit := false

var _spr: Sprite2D
var _wait := 2.0
var _t := -1.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = int(position.x) * 7 + int(position.y)
	var tex: Texture2D = canvas_tex(sprite, true) if lit else load_tex(sprite)
	if tex == null:
		return
	_spr = make_strip(tex, int(frames), lit)
	_spr.offset = Vector2(float(offset[0]), float(offset[1]))
	if mode == "glint":
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		_spr.material = mat
		_wait = _rng.randf_range(1.0, float(period[1]))
	_spr.frame = 0


func _tick(delta: float) -> void:
	if _spr == null:
		return
	if mode == "glint":
		if _t < 0.0:
			_wait -= delta
			_spr.frame = 0
			if _wait <= 0.0:
				_t = 0.0
		else:
			_t += delta
			var seq := [1, 2, 3, 2, 1]
			var k := int(_t / 0.07)
			if k >= seq.size():
				_t = -1.0
				_wait = _rng.randf_range(float(period[0]), float(period[1]))
				_spr.frame = 0
			else:
				_spr.frame = seq[k]
	else:
		var g: float = Wind.gust
		var n := int(frames)
		if g > 0.22 and n > 1:
			var rate := 6.0 + g * 8.0
			_spr.frame = 1 + int(Wind.t_global * rate + position.x * 0.1) % (n - 1)
		else:
			_spr.frame = 0
