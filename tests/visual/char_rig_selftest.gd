extends Node
## Headless self-test for scripts/actors/sprite_rig.gd + npc.gd (owner: characters / chars-sprites).
## Runs as a scene (the autoloads must exist: layer_stack.gd uses Game):
##   godot --headless --path C:/Spiele/AshesOfEmpires res://tests/visual/CharRigSelftest.tscn
## Checks: every sheet loads and its variant rows exist; idle variants appear while `anim` stays the base
## name; play_once returns to the base; turn_to mirrors after the front frame; NPC idle_anim override,
## talk start / release on a resting frame, wander playback scaled by ground_speed.
## Round 7: the Chapter-3 cast is in the list (same row set as the round-2 NPCs), talk_front / talk_back exist,
## view_hint maps "*_side" requests to the facing view, a walking turn shows walk_front and survives row
## changes, turning back mid-turn cancels, front-on NPCs talk front-on, wanderers turn softly, the player
## turns softly. Exit code 0 = pass.

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const NPC := preload("res://scripts/actors/npc.gd")
const IDS := ["alexei", "konrad", "irina", "emil", "worker_a", "babushka", "child_a", "berlin_father",
	"berlin_mother", "berlin_child", "clerk", "guard", "librarian", "porter", "vendor", "worker_b",
	"elena", "border_officer", "conductor", "voronova", "kessler", "typist", "journalist"]

var fails: PackedStringArray = []


func _check(cond: bool, msg: String) -> void:
	if not cond:
		fails.append(msg)


func _step(n: Node, seconds: float, dt := 0.05) -> void:
	var t := 0.0
	while t < seconds:
		n._process(dt)
		t += dt


func _ready() -> void:
	get_tree().create_timer(60.0).timeout.connect(func(): print("TIMEOUT"); get_tree().quit(2))
	_run.call_deferred()


func _run() -> void:
	var root := self
	# 1. every sheet: loads, required rows, variants point at existing one-shot rows
	for id in IDS:
		var r: Node2D = SpriteRig.new()
		root.add_child(r)
		_check(r.load_character(id), "%s: load_character failed" % id)
		for a in ["idle_side", "walk_side", "talk_side", "idle_front", "talk_front", "blink_side", "look_side",
				"gesture_side"]:
			_check(r.has_anim(a), "%s: missing %s" % [id, a])
		_check(int(r.sheet["anims"]["talk_side"].get("frames", 0)) == 8, "%s: talk_side is not 8 frames" % id)
		_check(int(r.sheet["anims"]["idle_side"].get("frames", 0)) == 8, "%s: idle_side is not 8 frames" % id)
		var anims: Dictionary = r.sheet.get("anims", {})
		for a in anims:
			for v in anims[a].get("variants", []):
				_check(anims.has(v), "%s: variant %s of %s missing" % [id, v, a])
				_check(anims.has(v) and not bool(anims[v].get("loop", true)), "%s: variant %s loops" % [id, v])
		_check(r.ground_speed("walk_side") > 0.0, "%s: no ground_speed" % id)
		r.queue_free()
	# protagonists keep the stride contract (player walks 45 px/s, playback = speed / ground_speed)
	for id in ["alexei", "konrad"]:
		var r: Node2D = SpriteRig.new()
		root.add_child(r)
		r.load_character(id)
		var gs: float = r.ground_speed("walk_side")
		_check(gs >= 34.0 and gs <= 35.5, "%s: walk ground_speed %.1f outside 34..35.5" % [id, gs])
		r.queue_free()

	# 2. idle variants: rows change, logical anim does not; re-requesting the base never cancels a variant
	var rig: Node2D = SpriteRig.new()
	root.add_child(rig)
	rig.load_character("alexei")
	rig.play("idle_side")
	var seen := {}
	var t := 0.0
	while t < 40.0:
		rig._process(0.05)
		rig.play("idle_side")          # like player.gd does every physics frame
		seen[rig.current_row()] = true
		_check(rig.anim == "idle_side", "variant changed the logical anim to %s" % rig.anim)
		t += 0.05
	_check(seen.has("blink_side"), "no blink variant within 40 s")
	_check(seen.has("look_side") or seen.has("gesture_side"), "no look / gesture variant within 40 s")
	rig.variants_enabled = false
	rig.play("walk_side")
	seen.clear()
	_step(rig, 5.0)
	_check(rig.current_row() == "walk_side", "walk row replaced by %s" % rig.current_row())

	# 3. play_once returns to the previous animation and reports anim_finished
	var finished: Array = []
	rig.anim_finished.connect(func(a): finished.append(a))
	rig.play("idle_side")
	rig.play_once("gesture_side")
	_check(rig.anim == "gesture_side", "play_once did not start")
	_step(rig, 3.0)
	_check(rig.anim == "idle_side", "play_once did not return to idle_side (%s)" % rig.anim)
	_check(finished.has("gesture_side"), "anim_finished not emitted for gesture_side")

	# 4. soft turn: front frame first, mirrored afterwards
	rig.set_flip(false)
	_check(rig.turn_to(true), "turn_to refused")
	_check(rig.is_turning() and not rig.is_flipped(), "turn did not hold the front frame")
	_step(rig, 0.3)
	_check(rig.is_flipped() and not rig.is_turning(), "turn did not finish")
	# 4b. walking turn: the walk_front frame at the walk phase, kept through a row change; back mid-turn cancels
	var cols: int = rig.sprite.hframes
	var wf_row := int(rig.sheet["anims"]["walk_front"]["row"])
	rig.play("walk_side")
	_step(rig, 0.25)
	_check(rig.turn_to(false, 0.1, "walk_front"), "walking turn refused")
	_check(int(rig.sprite.frame / cols) == wf_row, "walking turn does not show walk_front")
	rig.play("idle_side")
	_check(rig.is_turning() and int(rig.sprite.frame / cols) == wf_row, "row change replaced the turn frame")
	_check(rig.turn_to(true), "turning back refused")
	_check(not rig.is_turning() and rig.is_flipped(), "turning back mid-turn did not cancel the turn")
	_check(int(rig.sprite.frame / cols) == int(rig.sheet["anims"]["idle_side"]["row"]), "cancelled turn left a stale frame")
	# 4c. view_hint: side requests follow the facing view
	rig.view_hint = "front"
	rig.play("talk_side")
	_check(rig.anim == "talk_front", "view_hint front: talk_side played %s" % rig.anim)
	rig.view_hint = "back"
	rig.play("idle_side")
	_check(rig.anim == "idle_back", "view_hint back: idle_side played %s" % rig.anim)
	rig.play("talk_side")
	_check(rig.anim == "talk_back", "view_hint back: talk_side played %s" % rig.anim)
	rig.view_hint = ""
	rig.play("talk_side")
	_check(rig.anim == "talk_side", "no view_hint: talk_side played %s" % rig.anim)
	rig.queue_free()

	# 5. NPC: idle override, talking, release on a resting frame, wander playback scaling
	var npc: Node2D = NPC.new()
	npc.char_id = "vendor"
	npc.idle_anim = "work_side"
	npc.look_at_player = false
	root.add_child(npc)
	_check(npc.rig.anim == "work_side", "npc idle_anim override ignored (%s)" % npc.rig.anim)
	npc.set_talking(true)
	_check(npc.rig.anim == "talk_side", "npc did not start talking")
	npc.set_talking(true)
	_check(npc.rig.current_frame() == 0, "repeated set_talking(true) restarted the gesture")
	_step(npc.rig, 0.45)                  # move into a gesture frame
	npc.set_talking(false)
	_check(not npc.talking, "talking flag not cleared")
	var guard := 0
	while npc.rig.anim == "talk_side" and guard < 40:
		npc.rig._process(0.05)
		npc._process(0.05)
		guard += 1
	_check(npc.rig.anim == "work_side", "npc did not settle back into work_side (%s)" % npc.rig.anim)
	npc.queue_free()
	# soft turn before talking: player on the other side -> front frame first, talk after the turn
	var fake_player := Node2D.new()
	fake_player.add_to_group("player")
	fake_player.position = Vector2(-40, 0)
	add_child(fake_player)
	var talker: Node2D = NPC.new()
	talker.char_id = "irina"
	talker.look_at_player = false
	add_child(talker)
	talker.rig.set_flip(false)
	talker.set_talking(true)
	_check(talker.rig.is_turning(), "talker did not start a soft turn toward the player")
	_check(talker.rig.anim != "talk_side", "talk started before the turn finished")
	var g2 := 0
	while talker.rig.anim != "talk_side" and g2 < 20:
		talker.rig._process(0.05)
		talker._process(0.05)
		g2 += 1
	_check(talker.rig.is_flipped(), "talker not facing the player (left) after the turn")
	_check(talker.rig.anim == "talk_side", "talk did not start after the turn")
	talker.queue_free()
	fake_player.queue_free()
	var walker: Node2D = NPC.new()
	walker.char_id = "clerk"
	walker.wander = 40.0
	walker.wander_speed = 20.0
	root.add_child(walker)
	walker._pause = 0.0
	walker._process(0.05)
	var gs2: float = walker.rig.ground_speed("walk_side")
	_check(walker.rig.anim == "walk_side", "wanderer not walking")
	_check(absf(walker.rig.speed_scale - 20.0 / gs2) < 0.01, "wander playback not scaled by ground_speed")
	# soft turn at the end of the path
	var g3 := 0
	while not walker.rig.is_turning() and g3 < 200:
		walker._process(0.05)
		g3 += 1
	_check(walker.rig.is_turning(), "wanderer did not turn softly at the end of its path")
	walker.queue_free()
	# front-on NPC that does not turn to talk: talks facing the camera
	var front_npc: Node2D = NPC.new()
	front_npc.char_id = "border_officer"
	front_npc.idle_anim = "idle_front"
	front_npc.turn_to_talk = false
	front_npc.look_at_player = false
	root.add_child(front_npc)
	_check(front_npc.rig.anim == "idle_front", "front npc idle is %s" % front_npc.rig.anim)
	front_npc.set_talking(true)
	_check(front_npc.rig.anim == "talk_front", "front-on npc talks with %s" % front_npc.rig.anim)
	front_npc.set_talking(false)
	var g4 := 0
	while front_npc.rig.anim != "idle_front" and g4 < 40:
		front_npc.rig._process(0.05)
		front_npc._process(0.05)
		g4 += 1
	_check(front_npc.rig.anim == "idle_front", "front-on npc did not settle back (%s)" % front_npc.rig.anim)
	front_npc.queue_free()
	# the player turns softly: in-between frame first, mirrored afterwards; instant flip on request
	var PlayerScript := load("res://scripts/actors/player.gd")
	var pl: Node2D = PlayerScript.new()
	pl.setup("konrad", "oblique", Vector2(100, 300), "concrete")
	root.add_child(pl)
	pl.face(-1.0)
	_check(pl.rig.is_turning() and not pl.rig.is_flipped(), "player flipped instantly instead of turning")
	_step(pl.rig, 0.3)
	_check(pl.rig.is_flipped() and not pl.rig.is_turning(), "player turn did not finish")
	pl.face(1.0, false)
	_check(not pl.rig.is_flipped() and not pl.rig.is_turning(), "instant face() did not flip at once")
	pl.face_point(Vector2(102, 340))
	_check(pl.get_view() == "front" and pl.rig.view_hint == "front", "player does not face the camera for a target below")
	pl.rig.play("talk_side")
	_check(pl.rig.anim == "talk_front", "player facing the camera talks with %s" % pl.rig.anim)
	pl.face_point(Vector2(60, 302))
	_check(pl.get_view() == "side" and pl.rig.view_hint == "", "player does not face sideways for a target beside it")
	pl.queue_free()

	if fails.is_empty():
		print("CHAR_RIG_SELFTEST PASS")
		get_tree().quit(0)
	else:
		for f in fails:
			print("FAIL: ", f)
		print("CHAR_RIG_SELFTEST FAIL (%d)" % fails.size())
		get_tree().quit(1)
