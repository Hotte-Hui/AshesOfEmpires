extends Node2D
## Non-player character: idles, turns to the player when close, plays talk gestures while speaking.
## Optional simple routine: wander between two x positions (civilians), or stay (story NPCs).

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")

@export var char_id := "irina"
@export var hotspot_id := ""
@export var hotspot_offset := Vector2.ZERO
@export var face_left := false
@export var look_at_player := true
@export var wander := 0.0               ## > 0: walks back and forth this many px
@export var wander_speed := 22.0
@export var tint := Color.WHITE          ## far civilians can be darkened to sit in the haze

var rig: Node2D
var talking := false
var _home := Vector2.ZERO
var _dir := 1.0
var _pause := 0.0


func _ready() -> void:
	rig = SpriteRig.new()
	add_child(rig)
	rig.load_character(char_id)
	rig.set_flip(face_left)
	modulate = tint
	add_to_group("npcs")
	_home = position
	if wander > 0.0:
		_pause = randf_range(0.0, 2.0)


func set_talking(on: bool) -> void:
	talking = on
	rig.play("talk_side" if on else "idle_side")


func _process(delta: float) -> void:
	if talking:
		return
	if wander > 0.0:
		if _pause > 0.0:
			_pause -= delta
			rig.play("idle_side")
		else:
			position.x += _dir * wander_speed * delta
			rig.set_flip(_dir < 0.0)
			rig.play("walk_side")
			if absf(position.x - _home.x) > wander:
				_dir = -_dir
				position.x = _home.x + signf(position.x - _home.x) * wander
				_pause = randf_range(1.5, 4.0)
		return
	if look_at_player:
		var p := get_tree().get_first_node_in_group("player") as Node2D
		if p and absf(p.global_position.x - global_position.x) < 90.0:
			rig.set_flip(p.global_position.x < global_position.x)
