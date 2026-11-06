extends "res://scripts/actors/npc.gd"
## NPC whose presence follows the story (Chapter 3+): visible only after `show_after` is complete and until
## `hide_after` is complete (objective ids; empty = no limit). Presentation only — the Story engine never
## asks NPCs anything. A hidden NPC leaves the "npcs" group so it neither talks nor affects dialogue docking.
## Inside a memory (§12.10) of a level file shared by several Story scenes (the levels built on
## scripts/levels/c3p2_archive/registry_level.gd) the live Story does not decide: the NPC reads the level's gated-art
## rule (objective_done) — only objectives of scenes BEFORE the remembered one count, its own and later ones do not
## (the cellar memory has Lev at his desk after the whole chapter, the siding memory has him at the siding). A level
## of one Story scene keeps the live Story (the memory is of a completed scene: who stood there at its end).
## §12.11 in-level protagonist switch: Game makes the protagonist who is not controlled a StoryNPC with
## `stand_in = true` (idles, turns to the new player, talks when his lines come). walk_to() lets him walk to his
## post after the hand-over (walk cycle at the protagonists' 45 px/s, feet planted; a conversation pauses the walk);
## set_suppressed(true) hides an authored NPC for good while that protagonist is the one being played.

signal arrived

const WALK_SPEED := 45.0                ## px/s, the protagonists' walking speed (player.gd)

@export var show_after := ""
@export var hide_after := ""

var stand_in := false                   ## Game's stand-in for the protagonist who is not controlled (§12.11)
var _present := true
var _suppressed := false
var _walk_to = null                     ## Vector2 while walking to a post, else null
var _walk_speed := WALK_SPEED


func _ready() -> void:
	super._ready()
	var st := get_node_or_null("/root/Story")
	if st:
		for sig in ["objective_completed", "state_replaced"]:
			if st.has_signal(sig):
				st.connect(sig, func(_x): _refresh())
	_refresh()


func is_present() -> bool:
	return _present


func _done(oid: String) -> bool:
	var lvl := _rule_level()
	if lvl != null and bool(lvl.in_memory()):
		return bool(lvl.objective_done(oid, false))
	var st := get_node_or_null("/root/Story")
	return st != null and st.has_method("objective_state") and str(st.objective_state(oid)) == "complete"


## The level this NPC stands in when it carries the gated-art rule (registry_level.gd: in_memory + objective_done),
## else null. Asked before the level's own _ready (children first): the rule reads its scene chain on first use.
func _rule_level() -> Node:
	var n := get_parent()
	while n != null:
		if n.has_method("in_memory") and n.has_method("objective_done"):
			return n
		n = n.get_parent()
	return null


func _refresh() -> void:
	var on := (show_after == "" or _done(show_after)) and (hide_after == "" or not _done(hide_after)) and not _suppressed
	_present = on
	visible = on
	process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	if on and not is_in_group("npcs"):
		add_to_group("npcs")
	elif not on and is_in_group("npcs"):
		remove_from_group("npcs")


## Keeps the NPC hidden whatever the objectives say (the protagonist it shows is being played right now).
func set_suppressed(on: bool) -> void:
	_suppressed = on
	_refresh()


func is_suppressed() -> bool:
	return _suppressed


## Walk (straight line) to `target` in the playfield, then idle facing the player. Instant when already there.
func walk_to(target: Vector2, speed := WALK_SPEED) -> void:
	if position.distance_to(target) < 1.0:
		position = target
		_walk_to = null
		_home = position
		return
	_walk_to = target
	_walk_speed = maxf(5.0, speed)
	var left := target.x < position.x
	if absf(target.x - position.x) > 1.0 and left != rig.is_flipped():
		rig.turn_to(left, 0.1, "walk_front")


func is_walking() -> bool:
	return _walk_to != null


## Where the NPC will stand: the end of its walk, else where it is (saves store this).
func rest_position() -> Vector2:
	return _walk_to if _walk_to != null else position


## Turn softly towards a point (sideways), e.g. the protagonist who just took over.
func turn_toward(p: Vector2) -> void:
	if rig == null or absf(p.x - global_position.x) < 2.0:
		return
	var left := p.x < global_position.x
	if left != rig.is_flipped() or rig.is_turning():
		rig.turn_to(left)


func set_talking(on: bool) -> void:
	if on and _walk_to != null:      # a conversation pauses the walk; it goes on afterwards
		rig.speed_scale = 1.0
	super.set_talking(on)


func _process(delta: float) -> void:
	if not _present:
		return
	if _walk_to != null and not talking and not _releasing:
		_walk_step(delta)
		return
	super._process(delta)


func _walk_step(delta: float) -> void:
	var to: Vector2 = _walk_to - position
	var step := _walk_speed * delta
	if to.length() <= step:
		position = _walk_to
		_walk_to = null
		_home = position
		rig.speed_scale = 1.0
		rig.play(_idle_name())
		_face_player(true)
		arrived.emit()
		return
	position += to.normalized() * step
	if not rig.is_turning():
		if absf(to.x) > 1.0:
			rig.set_flip(to.x < 0.0)
		rig.play("walk_side")
		var gs: float = rig.ground_speed("walk_side")
		rig.speed_scale = clampf(_walk_speed / gs, 0.5, 2.0) if gs > 0.0 else 1.0
