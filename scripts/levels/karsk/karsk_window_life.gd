extends "res://scripts/levels/karsk/karsk_actor.gd"
## Somebody lives behind the one amber window of the signal box: the signalman's dark silhouette gets up,
## crosses behind the mullion, bends over the desk, sits down with his tea, turns his head.
## Node = window top-left (world), strip frames (env_karsk_sprites.window_silhouettes): 0 empty,
## 1 standing left, 2 crossing, 3 bent over the desk, 4 seated, 5 seated with cup, 6 seated head turned.
## The silhouette is unlit (stays a dark shape against the glowing glass; the window glow is in yard_back).

var sprite := ""
var cell: Array = [24, 24]
var mode := "cabin"             ## "cabin" (the signalman routines) or "small" (distant lit window, frames 0-3)

var _spr: Sprite2D
var _script: Array = []        # [[frame, seconds], ...] current routine
var _t := 0.0
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = 522 + int(position.x) * 3 + int(position.y)
	var tex := load_tex(sprite)
	if tex == null:
		return
	_spr = make_strip(tex, 7 if mode == "cabin" else 4, false)
	_spr.frame = 4 if mode == "cabin" else 0
	_routine()


func _routine() -> void:
	if mode == "small":         # somebody steps to the window now and then, or draws the curtain
		var who := 1 + _rng.randi() % 3
		_script = [[0, _rng.randf_range(7.0, 18.0)], [who, _rng.randf_range(2.0, 6.0)]]
		_t = 0.0
		return
	match _rng.randi() % 4:
		0:      # gets up, goes to the desk, comes back, sits
			_script = [[4, _rng.randf_range(4.0, 9.0)], [1, 1.6], [2, 0.5], [3, _rng.randf_range(2.5, 4.5)],
				[2, 0.5], [1, 1.0], [4, 2.0]]
		1:      # tea
			_script = [[4, _rng.randf_range(3.0, 7.0)], [5, 1.6], [4, 2.5], [5, 1.4], [6, 1.6], [4, 2.0]]
		2:      # leaves the window for a while
			_script = [[4, 3.0], [1, 1.2], [2, 0.5], [0, _rng.randf_range(6.0, 12.0)], [2, 0.5], [1, 1.0], [4, 2.0]]
		_:      # watching the yard
			_script = [[6, _rng.randf_range(2.0, 4.0)], [4, _rng.randf_range(4.0, 8.0)], [6, 1.5], [4, 2.0]]
	_t = 0.0


func _tick(delta: float) -> void:
	if _spr == null or _script.is_empty():
		return
	_t += delta
	var step: Array = _script[0]
	_spr.frame = int(step[0])
	if _t >= float(step[1]):
		_t = 0.0
		_script.pop_front()
		if _script.is_empty():
			_routine()
