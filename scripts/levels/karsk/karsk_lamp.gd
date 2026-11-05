extends "res://scripts/levels/karsk/karsk_actor.gd"
## The tired platform lamp (lamp post 2): owns its PointLight2D and the bulb glow. Mostly steady, every
## 6–15 s it stutters (2–4 short dips) and now and then drops out for about a second before it catches again,
## with a faint buzz. Accessibility: never more than ~3 transitions per second; reduced motion keeps every dip
## shallow (≥ 70 %).

const LayerStack := preload("res://scripts/levels/layer_stack.gd")

var sprite := ""                ## 2-frame bulb strip (0 lit, 1 dark) + _e glow
var bulb_pos: Array = [714, 230]
var light_pos: Array = [716, 233]
var light_color := "#DEE5DC"
var energy := 0.45
var radius := 84.0
var height := 40.0

var _light: PointLight2D
var _bulb: Sprite2D
var _glow: Sprite2D
var _level := 1.0
var _events: Array = []         # queued [duration, level]
var _ev_t := 0.0
var _next := 5.0
var _noise := FastNoiseLite.new()
var _t := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 700
	_noise.seed = 703
	_noise.frequency = 1.3
	_light = PointLight2D.new()
	_light.texture = LayerStack.light_texture()
	_light.color = Color(light_color)
	_light.energy = energy
	_light.texture_scale = radius / 128.0
	_light.height = height
	_light.position = Vector2(float(light_pos[0]), float(light_pos[1])) - position
	add_child(_light)
	var tex := load_tex(sprite)
	if tex:
		_bulb = make_strip(tex, 2)
		_bulb.position = Vector2(float(bulb_pos[0]), float(bulb_pos[1])) - position
		_glow = make_glow(sprite, 2, 0.6)
		if _glow:
			_glow.position = _bulb.position
	_next = _rng.randf_range(3.0, 7.0)


func _tick(delta: float) -> void:
	_t += delta
	var rm := reduced_motion()
	if _events.is_empty():
		_next -= delta
		if _next <= 0.0:
			_next = _rng.randf_range(6.0, 15.0)
			_schedule(rm)
		_level = lerpf(_level, 1.0, 1.0 - exp(-14.0 * delta))
	else:
		_ev_t += delta
		var ev: Array = _events[0]
		_level = lerpf(_level, float(ev[1]), 1.0 - exp(-40.0 * delta))
		if _ev_t >= float(ev[0]):
			_ev_t = 0.0
			_events.pop_front()
	var hum := 1.0 + _noise.get_noise_1d(_t * 4.0) * 0.03
	var lv := clampf(_level * hum, 0.0, 1.1)
	if _light:
		_light.energy = energy * lv
	if _bulb:
		_bulb.frame = 0 if lv > 0.35 else 1
	if _glow:
		_glow.visible = lv > 0.35
		_glow.modulate.a = 0.6 * clampf(lv, 0.0, 1.0)


func _schedule(rm: bool) -> void:
	var floor_lv := 0.7 if rm else 0.25
	var p := Vector2(float(light_pos[0]), float(light_pos[1]))
	if on_screen(p, 80.0):
		sfx("karsk_lamp_buzz", dist_db(p, -14.0, -28.0), 0.1)
	if not rm and _rng.randf() < 0.22:
		# drop-out: dim, gone for ~1 s, catches again with one soft pulse
		_events = [[0.12, 0.45], [_rng.randf_range(0.7, 1.3), 0.04], [0.18, 0.75], [0.16, 0.4], [0.4, 1.0]]
		return
	_events = []
	for i in _rng.randi_range(2, 4):
		_events.append([_rng.randf_range(0.08, 0.14), _rng.randf_range(floor_lv, floor_lv + 0.25)])
		_events.append([_rng.randf_range(0.22, 0.4), 1.0])
