extends Node2D
## The porter's tube radio (exp_radio): the dial glows and wavers, the magic eye breathes as the station fades
## in and out, and a little dance music leaks out of the lodge (positional, only audible nearby).
## Y-sorted behind the lodge front, so it is seen through the lodge glazing.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var glow_path := ""
@export var glow_offset := [0, -28]
@export var loop_path := ""

var _spr: Sprite2D
var _music: AudioStreamPlayer2D
var _t := 0.0
var _eye_t := 1.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 209
	_spr = Sprite2D.new()
	_spr.texture = U.tex(glow_path)
	_spr.hframes = 3
	_spr.centered = false
	_spr.position = U.v2(glow_offset)
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_spr.material = mat
	_spr.modulate = Color(1, 1, 1, 0.5)
	add_child(_spr)
	var glow := PointLight2D.new()
	glow.texture = U.light_texture()
	glow.color = Color("#F2C27E")
	glow.energy = 0.22
	glow.texture_scale = 0.32
	glow.height = 6.0
	glow.position = U.v2(glow_offset) + Vector2(11, 10)
	add_child(glow)
	_music = U.make_sound(self, loop_path, -19.0, 230.0, 1.7, true)
	if _music:
		_music.play()


func _process(delta: float) -> void:
	_t += delta
	var a := 0.46 + 0.08 * sin(_t * 1.7) + 0.04 * sin(_t * 5.3 + 1.0)
	_spr.modulate.a = a
	_eye_t -= delta
	if _eye_t <= 0.0:
		_eye_t = _rng.randf_range(0.8, 3.0)
		_spr.frame = _rng.randi_range(0, 2)
