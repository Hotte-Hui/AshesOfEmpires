extends "res://scripts/levels/karsk/karsk_actor.gd"
## The press photographer's flash on the stepladder (L_M1_Plaza, owner plaza-env): every 8–14 s one short
## flash (a small additive star + a brief cold light on the crowd) and the shutter/bulb sound. A single flash,
## never a strobe; with reduced_motion the light burst is much weaker. Never touches Story / Explore state.

const LayerStackLib := preload("res://scripts/levels/layer_stack.gd")

var sprite := ""
var interval: Array = [8.0, 14.0]
var radius := 120.0

var _light: PointLight2D
var _spr: Sprite2D
var _wait := 4.0
var _t := -1.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 4711
	var t := load_tex(sprite)
	if t != null:
		_spr = make_strip(t, 1, false)
		_spr.offset = -Vector2(t.get_width(), t.get_height()) * 0.5
		_spr.offset = _spr.offset.round()
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		_spr.material = mat
		_spr.visible = false
	_light = PointLight2D.new()
	_light.texture = LayerStackLib.light_texture()
	_light.texture_scale = radius / 128.0
	_light.color = Color("#D2CCCB")
	_light.energy = 0.0
	_light.height = 30.0
	add_child(_light)
	_wait = _rng.randf_range(3.0, 6.0)


func _tick(delta: float) -> void:
	if _t < 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_t = 0.0
			sfx("plaza_shutter", dist_db(position, -9.0, -26.0), 0.08)
		return
	_t += delta
	var peak := 0.45 if reduced_motion() else 1.5
	_light.energy = peak * maxf(0.0, 1.0 - _t / 0.3)
	if _spr != null:
		_spr.visible = _t < 0.1
	if _t > 0.35:
		_t = -1.0
		_light.energy = 0.0
		_wait = _rng.randf_range(float(interval[0]), float(interval[1]))
