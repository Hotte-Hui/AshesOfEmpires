extends Node2D
## The pneumatic tube station on the archive pier (exp_pneumatic_tube): every minute or two a capsule
## arrives -- a rising whoosh in the brass tube along the ceiling, the flap kicks open, the capsule drops into the
## wire basket and stays there until someone fetches it.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var sheet_path := ""
@export var sheet_offset := [-1, -82]
@export var sound_path := ""
@export var first_delay := 14.0

var _spr: Sprite2D
var _seq: Array = []
var _seq_t := 0.0
var _t := 14.0
var _snd: AudioStreamPlayer2D
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 1070
	_spr = Sprite2D.new()
	_spr.texture = U.tex(sheet_path)
	_spr.hframes = 6
	_spr.centered = false
	_spr.position = U.v2(sheet_offset)
	_spr.frame = 0
	add_child(_spr)
	U.texel(_spr, global_position + _spr.position, Vector2(14, 26))
	_snd = U.make_sound(self, sound_path, -11.0, 520.0, 1.4)
	_t = first_delay


func _process(delta: float) -> void:
	if not _seq.is_empty():
		_seq_t -= delta
		if _seq_t <= 0.0:
			var step: Array = _seq.pop_front()
			_spr.frame = int(step[0])
			_seq_t = float(step[1])
		return
	_t -= delta
	if _t <= 0.0:
		_t = _rng.randf_range(55.0, 110.0)
		if _spr.frame == 4:
			# the last capsule was fetched in the meantime
			_spr.frame = 0
		if _snd:
			_snd.play()
		# whoosh lead-in, flap open, capsule out, falling, in the basket
		_seq = [[0, 0.75], [1, 0.08], [2, 0.08], [3, 0.08], [4, 0.0]]
		_seq_t = 0.0
