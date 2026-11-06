extends CharacterBody2D
## Player controller for both protagonists.
## Mode "oblique" (2.5D): walk on x and y inside the level's walkable polygon, y-sorted, depth at 0.62x.
## Mode "side" (2D): walk on x along the floor line.  Walk 45 px/s (~1.6 m/s at the 3.7 cm/px figure
## scale), run 90 px/s. Walk-cycle playback is scaled by speed / sheet ground_speed so feet stay planted.
## Rendering (owner render-camera): movement stays in _physics_process (60 Hz); the sprite rig is drawn at the
## position interpolated between the last two physics states, so motion is smooth at any display rate
## (60-360 Hz), on the pixel grid chosen by the world camera (WorldCamera.draw_pos_for: keeps its screen pixel
## while camera and player move together -> no 1-px vibration; keeps its world pixel while standing). The sprite
## material is assigned by scripts/render/pixel_view.gd, as for every world sprite.
## Round 7: turning around is soft like the NPCs' (a short front-facing in-between frame, the walk_front frame
## while walking so the stride continues; movement itself still reverses at once), and the player faces the
## person or thing it interacts with -- sideways, or towards / away from the camera in oblique levels when the
## other one stands below / above. The rig's view_hint follows the facing view, so the dialogue's
## "talk_side" / "idle_side" requests show talk_front / idle_front (or the back rows) when facing the camera.

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const TURN_STAND := 0.12        ## s the in-between (front) frame is shown when turning on the spot
const TURN_WALK := 0.07         ## s while walking / running (about one stride frame)
const FACE_VERTICAL := 2.0      ## oblique: |dy| (depth-scaled) > |dx| * this -> face the camera / away from it

var char_id := "alexei"
var mode := "oblique"
var surface := "gravel"
var walk_speed := 45.0
var run_speed := 90.0
var depth_factor := 0.62
var floor_y := 300.0
var rig: Node2D
var focus: Node = null          # nearest usable interactable
var _facing := 1.0
var _dir := "side"
var _step_frames := [1, 5]
var _phys_prev := Vector2.ZERO     # position before / after the last physics step (render interpolation)
var _phys_cur := Vector2.ZERO


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
	if mode == "side":
		# Side levels have a thin walk band around the feet line (e.g. y 296-306): a flat collider keeps
		# the y-walls from pinning the player while still stopping it at the left/right ends.
		var r := RectangleShape2D.new()
		r.size = Vector2(8, 2)
		shape.shape = r
	else:
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
	_phys_prev = position
	_phys_cur = position


func get_facing() -> float:
	return _facing


func get_view() -> String:
	return _dir


## Face left / right. soft = a short turn (front in-between frame) like the NPCs; false = instant flip.
func face(dir_x: float, soft := true) -> void:
	if absf(dir_x) <= 0.01 or rig == null:
		return
	var f := signf(dir_x)
	if f == _facing and (rig.is_flipped() == (f < 0.0) or rig.is_turning()):
		return
	_facing = f
	if soft:
		var moving := velocity.length() > 1.0
		rig.turn_to(f < 0.0, TURN_WALK if moving else TURN_STAND, "walk_front" if moving else "")
	else:
		rig.set_flip(f < 0.0)


## Facing view: "side" | "front" (towards the camera) | "back". Keeps the rig's view_hint in step.
func _set_dir(d: String) -> void:
	_dir = d
	if rig:
		rig.view_hint = "" if d == "side" else d


## Turn towards a point before talking / using something: sideways, or (oblique levels) towards or away from
## the camera when the point lies clearly below / above.
func face_point(p: Vector2) -> void:
	var d := p - global_position
	if mode == "oblique" and absf(d.y) * 1.6 > absf(d.x) * FACE_VERTICAL and absf(d.y) > 4.0:
		_set_dir("front" if d.y > 0.0 else "back")
		return
	_set_dir("side")
	if absf(d.x) > 0.5:
		face(d.x)


func _physics_process(delta: float) -> void:
	_phys_prev = position
	_physics_step(delta)
	_phys_cur = position


## Interpolated body position for rendering (between the last two physics states). A position set outside
## the physics step (spawn, teleport, save restore) is taken over immediately.
func get_visual_position() -> Vector2:
	if position != _phys_cur:
		_phys_prev = position
		_phys_cur = position
		return position
	return _phys_prev.lerp(_phys_cur, clampf(Engine.get_physics_interpolation_fraction(), 0.0, 1.0))


func _process(_delta: float) -> void:
	if rig == null:
		return
	var vis := get_visual_position()
	var cam = Game.camera
	var draw_at := vis
	if cam and cam.has_method("draw_pos_for"):
		draw_at = cam.draw_pos_for(self, vis)
	rig.position = draw_at - position


func _physics_step(_delta: float) -> void:
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
			_set_dir("back" if inp.y < 0.0 else "front")
		else:
			_set_dir("side")
			face(inp.x)
		rig.play("walk_" + _dir)
		var gs: float = rig.ground_speed(rig.anim)
		if gs > 0.0:
			rig.speed_scale = clampf(velocity.length() / gs, 0.6, 2.2)
		else:
			rig.speed_scale = 1.55 if running else 1.0
	else:
		rig.speed_scale = 1.0
		rig.play("idle_" + _dir)
	_update_focus(false)


func play_action(a: String) -> void:
	_set_dir("side")
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
	# Game clears its focus when an interaction starts; a modal that pauses the tree (DiscoveryView) keeps this
	# node from noticing, so resync whenever Game's focus differs (else a chained step on the same hotspot,
	# §12.9, never becomes Game's focus again).
	if best != focus or Game._focus != best:
		focus = best
		Game.set_focus(focus)
	elif focus:
		Game.update_prompt(focus)


## Called by Game._unhandled_input (root viewport): nodes inside the world SubViewport receive no input
## events, only the global Input state. Returns true when the press was used.
func try_interact() -> bool:
	if Game.input_locked or get_tree().paused or focus == null or not is_instance_valid(focus):
		return false
	if Time.get_ticks_msec() < Game.interact_ready_at:
		return true     # swallow: same press that just closed the previous interaction
	face_point(_look_target(focus))
	Game.interact(focus)
	return true


## Where to look when using `it`: the NPC it names (npc_id; the hotspot itself often sits beside the person),
## else the hotspot.
func _look_target(it: Node) -> Vector2:
	var who := str(it.get("npc_id")) if it.get("npc_id") != null else ""
	if who != "":
		var best: Node2D = null
		var best_d := 1e9
		for n in get_tree().get_nodes_in_group("npcs"):
			if n is Node2D and str(n.get("char_id")) == who and (n as Node2D).is_visible_in_tree():
				var dd := (n as Node2D).global_position.distance_to(global_position)
				if dd < best_d:
					best_d = dd
					best = n
		if best != null and best_d < 160.0:
			return best.global_position
	return (it as Node2D).global_position


func _on_frame(a: String, f: int) -> void:
	if a.begins_with("walk") and f in _step_frames:
		Audio.sfx("step_%s_%d" % [surface, randi() % 4 + 1], -10.0 if rig.speed_scale < 1.2 else -7.0)
