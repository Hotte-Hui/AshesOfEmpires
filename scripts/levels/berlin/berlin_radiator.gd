extends Node2D
## The cast-iron radiator under the first reading-room window (exp_heater): every so often the valve lets off
## a puff of steam with a hiss, and the pipes knock (water hammer) at irregular intervals -- the old building
## talking.  Y-sorted at the wall line (behind the player).

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var steam_path := ""
@export var valve_offset := [0, -16]
@export var frames := 12
@export var fps := 9.0
@export var knock_path := ""
@export var hiss_path := ""

var puffing := false
var _spr: Sprite2D
var _f := 0.0
var _puff_t := 4.0
var _knock_t := 7.0
var _knock: AudioStreamPlayer2D
var _hiss: AudioStreamPlayer2D
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 746
	_spr = Sprite2D.new()
	_spr.texture = U.tex(steam_path)
	_spr.hframes = frames
	_spr.centered = false
	_spr.light_mask = 0
	var tw := (_spr.texture.get_width() / frames) if _spr.texture else 12
	var th := _spr.texture.get_height() if _spr.texture else 20
	_spr.position = U.v2(valve_offset) - Vector2(tw / 2, th - 2)
	_spr.visible = false
	add_child(_spr)
	U.texel(_spr, Vector2.ZERO, Vector2(tw, th))
	_knock = U.make_sound(self, knock_path, -10.0, 520.0, 1.3)
	_hiss = U.make_sound(self, hiss_path, -17.0, 300.0, 1.6)
	_puff_t = _rng.randf_range(3.0, 8.0)
	_knock_t = _rng.randf_range(5.0, 12.0)


func _process(delta: float) -> void:
	if puffing:
		_f += delta * fps
		if int(_f) >= frames:
			puffing = false
			_spr.visible = false
		else:
			_spr.frame = int(_f)
	else:
		_puff_t -= delta
		if _puff_t <= 0.0:
			puffing = true
			_f = 0.0
			_spr.visible = true
			_puff_t = _rng.randf_range(10.0, 22.0)
			if _hiss:
				_hiss.pitch_scale = _rng.randf_range(0.9, 1.1)
				_hiss.play()
	_knock_t -= delta
	if _knock_t <= 0.0:
		_knock_t = _rng.randf_range(14.0, 36.0)
		if _knock:
			_knock.pitch_scale = _rng.randf_range(0.94, 1.06)
			_knock.play()
