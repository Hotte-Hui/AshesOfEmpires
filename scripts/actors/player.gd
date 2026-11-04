extends CharacterBody2D
## Player controller for both protagonists.
## Mode "oblique" (2.5D): walk on x and y inside the level's walkable polygon, y-sorted, depth at 0.62x.
## Mode "side" (2D): walk on x along the floor line.  60 px/s walk = exactly 1 px per physics tick
## (clean pixel cadence), run 120 px/s.

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")

var char_id := "alexei"
var mode := "oblique"
var surface := "gravel"
var walk_speed := 60.0
var run_speed := 120.0
var depth_factor := 0.62
var floor_y := 300.0
var rig: Node2D
var focus: Node = null          # nearest usable interactable
var _facing := 1.0
var _dir := "side"
var _step_frames := [1, 5]


func setup(id: String, level_mode: String, spawn: Vector2, step_surface: String) -> void:
	char_id = id
	mode = level_mode
	surface = step_surface
	position = spawn
	floor_y = spawn.y


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	collision_layer = 2
	collision_mask = 1
	var shape := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = 4.0
	shape.shape = c
	shape.position = Vector2(0, -2)
	add_child(shape)
	rig = SpriteRig.new()
	add_child(rig)
	rig.load_character(char_id)
	rig.frame_changed.connect(_on_frame)
	add_to_group("player")


func get_facing() -> float:
	return _facing


func face(dir_x: float) -> void:
	if absf(dir_x) > 0.01:
		_facing = signf(dir_x)
		rig.set_flip(_facing < 0.0)


func _physics_process(_delta: float) -> void:
	if Game.input_locked or get_tree().paused:
		velocity = Vector2.ZERO
		if not rig.anim.begins_with("inspect") and not rig.anim.begins_with("interact") and not rig.anim.begins_with("talk"):
			rig.play("idle_" + _dir)
		_update_focus(true)
		return
	var inp := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if mode == "side":
		inp.y = 0.0
	var running := Input.is_action_pressed("run")
	var spd := run_speed if running else walk_speed
	velocity = Vector2(inp.x * spd, inp.y * spd * depth_factor)
	move_and_slide()
	if mode == "side":
		position.y = floor_y
	if inp.length() > 0.1:
		if mode == "oblique" and absf(inp.y) > absf(inp.x) * 1.4:
			_dir = "back" if inp.y < 0.0 else "front"
		else:
			_dir = "side"
			face(inp.x)
		rig.speed_scale = 1.55 if running else 1.0
		rig.play("walk_" + _dir)
	else:
		rig.speed_scale = 1.0
		rig.play("idle_" + _dir)
	_update_focus(false)


func play_action(a: String) -> void:
	_dir = "side"
	rig.play(a, true)


func _update_focus(hide_only: bool) -> void:
	var best: Node = null
	if not hide_only:
		var best_d := 1e9
		for it in get_tree().get_nodes_in_group("interactables"):
			if not it.is_inside_tree() or not it.is_active():
				continue
			var d: Vector2 = it.global_position - global_position
			if mode == "oblique":
				d.y *= 1.6
			var dist := d.length()
			if dist <= it.radius and dist < best_d:
				best_d = dist
				best = it
	if best != focus:
		focus = best
		Game.set_focus(focus)
	elif focus:
		Game.update_prompt(focus)


func _unhandled_input(event: InputEvent) -> void:
	if Game.input_locked or get_tree().paused:
		return
	if event.is_action_pressed("interact") and focus:
		get_viewport().set_input_as_handled()
		if focus.global_position.x != global_position.x:
			face(focus.global_position.x - global_position.x)
		Game.interact(focus)


func _on_frame(a: String, f: int) -> void:
	if a.begins_with("walk") and f in _step_frames:
		Audio.sfx("step_%s_%d" % [surface, randi() % 4 + 1], -10.0 if rig.speed_scale < 1.2 else -7.0)
