extends "res://scripts/levels/karsk/karsk_actor.gd"
## Tram 7 in the station square, seen only through the exit arch of the concourse (exp_tram; find text:
## "Vor dem Ausgang wartet die Straßenbahn"). It WAITS most of the time with its lit windows, rings, pulls
## away to the right, the stop stays empty for a few seconds and the next car rolls in from the left and
## stops (bell). Lives on the square's parallax plane (0.85) at z -17 (square layer -18, concourse -13).
## Node position = (stop_x, rail y) in layer coordinates at camera x 0; sprite faces right (line board front).

var sprite := ""
var stop_x := 1668.0
var leave_x := 1800.0
var enter_x := 1540.0
var wait: Array = [34.0, 46.0]
var away: Array = [7.0, 11.0]
var speed := 22.0

var _spr: Sprite2D
var _glow: Sprite2D
var _x := 0.0
var _v := 0.0
var _state := "wait"
var _t := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 7707
	var tex := load_tex(sprite)
	if tex == null:
		push_warning("StationTram: missing sprite " + sprite)
		return
	_spr = make_strip(tex, 1)
	_spr.offset = Vector2(0.0, -float(tex.get_height()) + 1.0)
	_glow = make_glow(sprite, 1, 0.55)
	if _glow:
		_glow.offset = _spr.offset
	_x = stop_x
	_t = _rng.randf_range(float(wait[0]) * 0.4, float(wait[1]))
	_place()


func _place() -> void:
	var p := Vector2(roundf(_x - stop_x), 0.0)
	_spr.position = p
	if _glow:
		_glow.position = p


func _arch_visible() -> bool:
	return cam_pos().x > 1120.0


func _tick(delta: float) -> void:
	if _spr == null:
		return
	match _state:
		"wait":
			_t -= delta
			if _t <= 0.0:
				_state = "leave"
				_v = 0.0
				if _arch_visible():
					sfx("tram_bell", -16.0, 0.05)
					sfx("cine_a1m1_tram_depart", -20.0, 0.03)
		"leave":
			_v = minf(speed, _v + speed * 0.35 * delta)
			_x += _v * delta
			if _x > leave_x:
				_state = "away"
				_t = _rng.randf_range(float(away[0]), float(away[1]))
				_spr.visible = false
				if _glow:
					_glow.visible = false
		"away":
			_t -= delta
			if _t <= 0.0:
				_state = "enter"
				_x = enter_x
				_v = speed
				_spr.visible = true
				if _glow:
					_glow.visible = true
				if _arch_visible():
					sfx("cine_a1m1_tram_arrive", -20.0, 0.03)
		"enter":
			var rest := stop_x - _x
			_v = clampf(rest * 0.6, 2.0, speed)
			_x += _v * delta
			if rest <= 0.5:
				_x = stop_x
				_state = "wait"
				_t = _rng.randf_range(float(wait[0]), float(wait[1]))
				if _arch_visible():
					sfx("tram_bell", -18.0, 0.05)
	_place()
