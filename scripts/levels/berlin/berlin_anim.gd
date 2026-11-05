extends Node2D
## Generic looping sprite-strip actor (y-sorted in the Playfield), e.g. the smoke curl over the porter's
## ashtray.  The node position is the sort point; the strip is drawn at sheet_offset from it.  Unlit by default.

const U := preload("res://scripts/levels/berlin/berlin_util.gd")

@export var sheet_path := ""
@export var frames := 16
@export var fps := 6.0
@export var sheet_offset := [0, 0]
@export var lit := false

var _spr: Sprite2D
var _t := 0.0


func _ready() -> void:
	_spr = Sprite2D.new()
	_spr.texture = U.tex(sheet_path)
	_spr.hframes = maxi(1, frames)
	_spr.centered = false
	_spr.position = U.v2(sheet_offset)
	if not lit:
		_spr.light_mask = 0
	add_child(_spr)
	if _spr.texture:
		U.texel(_spr, Vector2.ZERO, Vector2(_spr.texture.get_width() / maxi(1, frames), _spr.texture.get_height()))
	_t = float(int(position.x * 7.0) % 97) / 10.0


func _process(delta: float) -> void:
	_t += delta
	_spr.frame = int(_t * fps) % maxi(1, frames)
