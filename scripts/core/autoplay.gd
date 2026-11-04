extends Node
## End-to-end test driver. Plays the real vertical slice inside the real Main scene, through the real
## Game director, levels, hotspots and Story engine:
##   godot --path . -- --autoplay=share_with_irina,preserve_evidence [--autoplay-skip] [--autoplay-shots=DIR]
## For each objective on the canonical route it waits until the Story engine reports it AVAILABLE (gates are
## never bypassed), walks/teleports the player to the hotspot and triggers the normal interaction. Puzzles are
## first answered WRONG once (failure path), then correctly. Mid-run it saves to slot 1, later loads it back and
## verifies the restored state. Prints AUTOPLAY_PASS / AUTOPLAY_FAIL and quits with exit code 0 / 1.

const ROUTE := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal",
	"a1_inspect_ledger", "a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans",
	"m1_talk_emil", "m1_choose"]

var choices := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence"}
var skip := false
var shots_dir := ""
var failures: Array = []
var _shot := 0


func configure(spec: String, do_skip: bool, shots: String) -> void:
	var parts := spec.split(",")
	if parts.size() >= 1 and parts[0] != "1" and parts[0] != "":
		choices["a1_choose"] = parts[0]
	if parts.size() >= 2:
		choices["m1_choose"] = parts[1]
	skip = do_skip
	shots_dir = shots


func run() -> void:
	print("AUTOPLAY start choices=", choices, " skip=", skip)
	Game.auto = true
	Game.auto_choices = choices
	Game.auto_skip = skip
	Story.new_game()
	if Explore.has_method("reset"):
		Explore.reset()
	await Game.goto_level(Game._story_scene(), "", false)
	await _shoot("start")
	var saved_snapshot := ""
	for oid in ROUTE:
		var ok := await _wait_available(oid, 30.0)
		if not ok:
			_fail("objective never became available: " + oid + " scene=" + Game._story_scene())
			break
		if (oid == "a1_talk_irina" or oid == "m1_inspect_plan_a") and Game.args.has("autoplay-explore"):
			await _explore_pass()
		var it := _find_interactable(oid)
		if it == null:
			_fail("no interactable in level for " + oid)
			break
		_place_player_near(it)
		await get_tree().create_timer(0.15).timeout
		await _shoot("before_" + oid)
		await Game.interact(it)
		if Story.objective_state(oid) != "complete":
			_fail("objective not complete after interaction: " + oid)
			break
		await _shoot("after_" + oid)
		if oid == "a1_inspect_ledger":
			var r = Saves.save("1")
			if not (r is Dictionary and r.get("ok", false)):
				_fail("save slot 1 failed: " + str(r))
			saved_snapshot = Story.save_json()
	# finale: the director runs X1 + end card after m1_choose; wait for slice completion
	var t := 0.0
	while not Story.flag("slice_finished") and t < 90.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	if not Story.flag("slice_finished"):
		_fail("slice_finished flag not set after finale")
	var hist: Dictionary = Story.choice_history()
	for k in choices:
		if str(hist.get(k, "")) != choices[k]:
			_fail("choice history mismatch for %s: %s" % [k, hist.get(k)])
	var expect := {"share_with_irina": "irina_trust", "keep_private": "alexei_secrecy",
		"preserve_evidence": "konrad_evidence", "request_explanation": "office_suspicion"}
	for k in choices:
		if int(Story.flag(expect[choices[k]])) != 1:
			_fail("flag %s should be 1" % expect[choices[k]])
	# load the mid-game save and verify restoration
	if saved_snapshot != "":
		var lr = Saves.load("1")
		if not (lr is Dictionary and lr.get("ok", false)):
			_fail("load slot 1 failed: " + str(lr))
		elif Story.save_json() != saved_snapshot:
			_fail("loaded state differs from saved snapshot")
		elif Game._story_scene() != "L_A1_Railyard" or Story.objective_state("a1_choose") != "available":
			_fail("loaded save has wrong scene/progress")
	if failures.is_empty():
		print("AUTOPLAY_PASS choices=", choices, " skip=", skip, " playtime=", snapped(Game.playtime, 0.1))
		get_tree().quit(0)
	else:
		for f in failures:
			print("AUTOPLAY_FAIL ", f)
		get_tree().quit(1)


## §12: trigger every optional find / chat of the current level through the normal Game.interact path and
## check Explore recorded it (gates of the canonical route are untouched: these never change Story state).
func _explore_pass() -> void:
	var snapshot := Story.save_json()
	var n := 0
	for it in get_tree().get_nodes_in_group("interactables"):
		if not it.is_inside_tree() or not (str(it.kind) == "discover" or str(it.kind) == "chat"):
			continue
		var id := str(it.explore_id)
		if id == "" or not Explore.has_entry(id):
			_fail("explore: interactable %s has unknown explore_id '%s'" % [it.name, id])
			continue
		_place_player_near(it)
		await get_tree().create_timer(0.05).timeout
		await Game.interact(it)
		if not Explore.is_found(id):
			_fail("explore: %s not recorded" % id)
		n += 1
	if Story.save_json() != snapshot:
		_fail("explore: optional content changed the canonical Story state")
	var c: Dictionary = Explore.counts(str(Game.level.level_id))
	print("AUTOPLAY explored %d finds in %s (%s/%s), history %s" % [n, Game.level.level_id, c.get("found", 0),
		c.get("total", 0), Explore.history_counts()])


func _fail(msg: String) -> void:
	failures.append(msg)
	push_error("AUTOPLAY " + msg)


func _wait_available(oid: String, timeout: float) -> bool:
	var t := 0.0
	while t < timeout:
		if Story.is_available(oid) and Game.level and not Game.busy and not Game.in_cinematic \
				and str(Game.level.get("level_id")) == Game._story_scene():
			return true
		await get_tree().process_frame
		t += get_process_delta_time()
	return false


func _find_interactable(oid: String) -> Node:
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.objective_id) == oid:
			return it
	return null


func _place_player_near(it: Node) -> void:
	var p = Game.player
	if p == null:
		return
	p.position = it.global_position + Vector2(-18, 3)
	if str(p.mode) == "side":
		p.position.y = p.floor_y
	p.face(1.0)
	Game.camera.snap_now()


func _shoot(tag: String) -> void:
	if shots_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	_shot += 1
	var img := get_viewport().get_texture().get_image()
	img.save_png("%s/%02d_%s.png" % [shots_dir, _shot, tag])
