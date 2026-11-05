extends Node2D
## A mouse living in the plinth of the archive shelving (exp_mouse): now and then it pushes its nose out of
## the hole, sniffs, sometimes scurries a little way along the skirting and back.  It vanishes into the hole
## the moment the player comes close.  Y-sorted at the wall line (behind the player).

const U := preload("res://scripts/levels/berlin/berlin_util.gd")
const F := {"hidden": 0, "nose": 1, "head": 2, "sniff": 3, "half": 4, "out": 5, "run_a": 6, "run_b": 7}

@export var sheet_path := ""
@export var squeak_path := ""
@export var shy_distance := 46.0

var state := "hidden"
var _spr: Sprite2D
var _t := 3.0
var _run_x := 0.0
var _run_dir := 1.0
var _squeak: AudioStreamPlayer2D
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 918
	_spr = Sprite2D.new()
	_spr.texture = U.tex(sheet_path)
	_spr.hframes = 8
	_spr.centered = false
	_spr.position = Vector2(-2, -8)
	add_child(_spr)
	U.texel(_spr, Vector2.ZERO, Vector2(12, 8))
	_squeak = U.make_sound(self, squeak_path, -16.0, 240.0, 1.8)
	_go("hidden")
	_t = _rng.randf_range(2.0, 6.0)


func _go(s: String) -> void:
	state = s
	_spr.frame = F.get(s if F.has(s) else "hidden", 0)


func _process(delta: float) -> void:
	var pp = U.player_pos(self)
	var near := pp != null and absf((pp as Vector2).x - global_position.x) < shy_distance
	if near and state != "hidden":
		if _squeak and state != "nose":
			_squeak.play()
		_spr.position.x = -2.0
		_go("hidden")
		_t = _rng.randf_range(6.0, 12.0)
		return
	_t -= delta
	match state:
		"hidden":
			if _t <= 0.0 and not near:
				_go("nose")
				_t = _rng.randf_range(0.6, 1.2)
		"nose":
			if _t <= 0.0:
				_go("head")
				_t = _rng.randf_range(0.8, 1.8)
		"head", "sniff":
			# whiskers twitch while it sniffs
			if int(Time.get_ticks_msec() / 140) % 3 == 0:
				_spr.frame = F["sniff"]
			else:
				_spr.frame = F["head"]
			if _t <= 0.0:
				var r := _rng.randf()
				if r < 0.45:
					_go("half")
					_t = _rng.randf_range(0.4, 0.9)
				elif r < 0.75:
					_go("hidden")
					_t = _rng.randf_range(4.0, 10.0)
				else:
					_t = _rng.randf_range(0.6, 1.4)
		"half":
			if _t <= 0.0:
				if _rng.randf() < 0.6:
					_go("out")
					_t = _rng.randf_range(0.5, 1.2)
				else:
					_go("head")
					_t = 0.8
		"out":
			if _t <= 0.0:
				_run_x = 0.0
				_run_dir = 1.0
				_go("run_a")
				_t = _rng.randf_range(0.6, 1.1)
				if _squeak and _rng.randf() < 0.4:
					_squeak.play()
		"run_a", "run_b":
			_run_x += _run_dir * 34.0 * delta
			if _t <= 0.0 and _run_dir > 0.0:
				_run_dir = -1.0
				_spr.flip_h = true
			if _run_dir < 0.0 and _run_x <= 0.0:
				_run_x = 0.0
				_spr.flip_h = false
				_go("half")
				_t = 0.3
				_spr.position.x = -2.0
				return
			_spr.position.x = -2.0 + roundf(_run_x) - (8.0 if _spr.flip_h else 0.0)
			_spr.frame = F["run_a"] if int(Time.get_ticks_msec() / 90) % 2 == 0 else F["run_b"]
