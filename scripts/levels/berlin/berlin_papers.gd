extends Node2D
## Loose sheets on the reading table under the tilted fanlight: gusts of cold air lift the top sheet's corner
## now and then (sometimes twice in a row), with a dry rustle.  Y-sorted just in front of the table prop.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var sheet_path := ""
@export var sheet_offset := [0, -30]
@export var frames := 8
@export var fps := 11.0
@export var rustle_path := ""

var _spr: Sprite2D
var _f := -1.0
var _t := 2.0
var _repeat := 0
var _snd: AudioStreamPlayer2D
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 1100
	_spr = Sprite2D.new()
	_spr.texture = U.tex(sheet_path)
	_spr.hframes = frames
	_spr.centered = false
	_spr.position = U.v2(sheet_offset)
	add_child(_spr)
	_spr.frame = 0
	if _spr.texture:
		U.texel(_spr, global_position + _spr.position, Vector2(_spr.texture.get_width() / frames, _spr.texture.get_height()))
	_snd = U.make_sound(self, rustle_path, -20.0, 220.0, 1.8)
	_t = _rng.randf_range(1.5, 5.0)


func _process(delta: float) -> void:
	if _f >= 0.0:
		_f += delta * fps
		if int(_f) >= frames:
			_f = -1.0
			_spr.frame = 0
			if _repeat > 0:
				_repeat -= 1
				_t = 0.15
		else:
			_spr.frame = int(_f)
		return
	_t -= delta
	if _t <= 0.0:
		_f = 0.0
		if _repeat == 0:
			_repeat = 1 if _rng.randf() < 0.35 else 0
			if _snd:
				_snd.pitch_scale = _rng.randf_range(0.9, 1.15)
				_snd.play()
		_t = _rng.randf_range(3.0, 9.0)
