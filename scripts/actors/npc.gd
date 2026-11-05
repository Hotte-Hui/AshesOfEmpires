extends Node2D
## Non-player character: idles (with occasional blinks / glances / gestures from the sheet's idle
## variants), turns softly toward the player when close or while talking, plays talk gestures while
## speaking and settles back into its idle on a resting talk frame (no snapping mid-gesture).
## Optional simple routine: wander between two x positions (civilians), or stay (story NPCs).
## `idle_anim` overrides the idle row, e.g. "work_side" (vendor pouring tea, librarian stamping cards,
## worker warming his hands) or "idle_front" (porter facing the hall).

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const TALK_REST_FRAMES := [0, 7]        ## talk_side frames with the hand down (safe to leave talking)
const LOOK_RADIUS := 90.0

@export var char_id := "irina"
@export var hotspot_id := ""
@export var hotspot_offset := Vector2.ZERO
@export var face_left := false
@export var look_at_player := true
@export var wander := 0.0               ## > 0: walks back and forth this many px
@export var wander_speed := 22.0
@export var tint := Color.WHITE          ## far civilians can be darkened to sit in the haze
@export var idle_anim := ""             ## optional idle row override ("work_side", "idle_front", ...)
@export var idle_variants := true       ## occasional blink / glance / gesture variants
@export var turn_to_talk := true        ## face the player while talking

var rig: Node2D
var talking := false
var _home := Vector2.ZERO
var _dir := 1.0
var _pause := 0.0
var _releasing := false                 ## talk ended: finish the current gesture first
var _release_timeout := 0.0
var _talk_after_turn := false           ## talk starts once the soft turn toward the player is done


func _ready() -> void:
	rig = SpriteRig.new()
	add_child(rig)
	rig.load_character(char_id)
	TexelLightLib.apply_tree(rig)        # light once per texel, like the player (high-res world path)
	rig.variants_enabled = idle_variants
	rig.set_flip(face_left)
	modulate = tint
	add_to_group("npcs")
	_home = position
	if wander > 0.0:
		_pause = randf_range(0.0, 2.0)
	rig.play(_idle_name())


func _idle_name() -> String:
	if idle_anim != "" and rig and rig.has_anim(idle_anim):
		return idle_anim
	return "idle_side"


func set_talking(on: bool) -> void:
	if on:
		_releasing = false
		if not talking:
			talking = true
			rig.speed_scale = 1.0
			if turn_to_talk:
				_face_player(true)
			if rig.is_turning():
				_talk_after_turn = true       # keep the front-facing turn frame visible, then talk
			else:
				rig.play("talk_side")
		return
	if not talking:
		return
	talking = false
	_talk_after_turn = false
	# leave the talk loop on a resting frame so the hand never snaps down mid-gesture
	if rig.anim == "talk_side" and not (rig.current_frame() in TALK_REST_FRAMES):
		_releasing = true
		_release_timeout = 0.8
	else:
		rig.play(_idle_name())


func _face_player(force := false) -> void:
	var p := get_tree().get_first_node_in_group("player") as Node2D
	if p == null:
		return
	var dx := p.global_position.x - global_position.x
	if absf(dx) < 2.0:
		return
	if not force and absf(dx) > LOOK_RADIUS:
		return
	var left := dx < 0.0
	if left != rig.is_flipped() or rig.is_turning():
		rig.turn_to(left)


func _process(delta: float) -> void:
	if _releasing:
		_release_timeout -= delta
		if rig.current_frame() in TALK_REST_FRAMES or _release_timeout <= 0.0:
			_releasing = false
			rig.play(_idle_name())
		return
	if talking:
		if _talk_after_turn and not rig.is_turning():
			_talk_after_turn = false
			rig.play("talk_side")
		return
	if wander > 0.0:
		if _pause > 0.0:
			_pause -= delta
			rig.speed_scale = 1.0
			rig.play(_idle_name())
		else:
			position.x += _dir * wander_speed * delta
			rig.set_flip(_dir < 0.0)
			rig.play("walk_side")
			var gs: float = rig.ground_speed("walk_side")
			rig.speed_scale = clampf(wander_speed / gs, 0.5, 2.0) if gs > 0.0 else 1.0
			if absf(position.x - _home.x) > wander:
				_dir = -_dir
				position.x = _home.x + signf(position.x - _home.x) * wander
				_pause = randf_range(1.5, 4.0)
		return
	if look_at_player:
		_face_player(false)
