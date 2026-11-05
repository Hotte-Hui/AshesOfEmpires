extends Node
## End-to-end test driver. Plays the real vertical slice inside the real Main scene, through the real
## Game director, levels, hotspots and Story engine:
##   godot --path . -- --autoplay=share_with_irina,preserve_evidence [--autoplay-skip] [--autoplay-shots=DIR]
## For each objective on the canonical route it waits until the Story engine reports it AVAILABLE (gates are
## never bypassed), walks/teleports the player to the hotspot and triggers the normal interaction. Puzzles are
## first answered WRONG once (failure path), then correctly. Mid-run it saves to slot 1, later loads it back and
## verifies the restored state. Prints AUTOPLAY_PASS / AUTOPLAY_FAIL and quits with exit code 0 / 1.
## Chapter 3 (C3_DESIGN.md): the route continues through L_C3_Station and L_C3_Hall; optional 3rd/4th spec values
## choose c3a_choose / c3b_choose (default ask_elena / share_protocol). A second save (slot 2) is taken in the
## station and reloaded at the end; the dialogue history is checked for the flag-dependent line variants.

const ROUTE := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal",
	"a1_inspect_ledger", "a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans",
	"m1_talk_emil", "m1_choose",
	"c3a_talk_conductor", "c3a_inspect_weighbill", "c3a_inspect_departures", "c3a_pass_control", "c3a_talk_elena",
	"c3a_choose", "c3b_arrival", "c3b_inspect_seating", "c3b_inspect_log", "c3b_solve_protocol", "c3b_inspect_booth",
	"c3b_talk_alexei", "c3b_choose"]
## flag written by each choice (C3_DESIGN §2.4); used to verify the consequence meters at the end
const CHOICE_FLAG := {"share_with_irina": "irina_trust", "keep_private": "alexei_secrecy",
	"preserve_evidence": "konrad_evidence", "request_explanation": "office_suspicion",
	"ask_elena": "elena_trust", "note_alone": "evidence_chain", "share_protocol": "alexei_konrad_trust",
	"search_elena": "elena_trust", "report_delegation": "kessler_alerted"}

var choices := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence", "c3a_choose": "ask_elena",
	"c3b_choose": "share_protocol"}
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
	if parts.size() >= 3 and parts[2] != "":
		choices["c3a_choose"] = parts[2]
	if parts.size() >= 4 and parts[3] != "":
		choices["c3b_choose"] = parts[3]
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
	var saved_c3 := ""
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
		if Game.side_level:
			await _visit_side_level()
		if oid == "a1_inspect_ledger":
			var r = Saves.save("1")
			if not (r is Dictionary and r.get("ok", false)):
				_fail("save slot 1 failed: " + str(r))
			saved_snapshot = Story.save_json()
		if oid == "c3a_pass_control":
			var r2 = Saves.save("2")
			if not (r2 is Dictionary and r2.get("ok", false)):
				_fail("save slot 2 failed: " + str(r2))
			saved_c3 = Story.save_json()
	# finale: the director runs LS_C3_Close + the end card after c3b_choose; wait for completion
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
	var want := {}
	for k in choices:
		var fl: String = CHOICE_FLAG.get(choices[k], "")
		want[fl] = int(want.get(fl, 0)) + 1
	for fl in want:
		if int(Story.flag(fl)) != int(want[fl]):
			_fail("flag %s should be %d, is %s" % [fl, want[fl], Story.flag(fl)])
	for fl in ["courier_files_seen", "protocol_matched", "elena_missing"]:
		if not bool(Story.flag(fl)):
			_fail("flag %s should be set after Chapter 3" % fl)
	_check_variants()
	# load the mid-game save and verify restoration
	if saved_snapshot != "":
		var lr = Saves.load("1")
		if not (lr is Dictionary and lr.get("ok", false)):
			_fail("load slot 1 failed: " + str(lr))
		elif Story.save_json() != saved_snapshot:
			_fail("loaded state differs from saved snapshot")
		elif Game._story_scene() != "L_A1_Railyard" or Story.objective_state("a1_choose") != "available":
			_fail("loaded save has wrong scene/progress")
	if saved_c3 != "":
		var l2 = Saves.load("2")
		if not (l2 is Dictionary and l2.get("ok", false)):
			_fail("load slot 2 failed: " + str(l2))
		elif Story.save_json() != saved_c3:
			_fail("loaded Chapter-3 state differs from saved snapshot")
		elif Game._story_scene() != "L_C3_Station" or Story.objective_state("c3a_talk_elena") != "available":
			_fail("loaded Chapter-3 save has wrong scene/progress")
	if failures.is_empty():
		print("AUTOPLAY_PASS choices=", choices, " skip=", skip, " playtime=", snapped(Game.playtime, 0.1))
		get_tree().quit(0)
	else:
		for f in failures:
			print("AUTOPLAY_FAIL ", f)
		get_tree().quit(1)


## The flag-dependent line variants (data/chapters/c3.json) must actually have been spoken on this route.
func _check_variants() -> void:
	var dlg = Game.ui.get("dialogue") if Game.ui else null
	if dlg == null or not ("history" in dlg):
		return
	var spoken := {}
	for h in dlg.history:
		spoken[str(h.get("text", ""))] = true
	var keys: Array = []
	match choices["a1_choose"]:
		"share_with_irina":
			keys += ["dlg.c3.cond_02.irina", "dlg.c3.ctrl_05.irina", "dlg.c3.el_02.irina", "dlg.c3.meet_07.irina"]
		"keep_private":
			keys += ["dlg.c3.cond_02.secrecy", "dlg.c3.ctrl_05.secrecy", "dlg.c3.el_06.secrecy", "dlg.c3.meet_07.secrecy"]
	match choices["m1_choose"]:
		"preserve_evidence":
			keys += ["dlg.c3.arr_02.evidence", "dlg.c3.meet_08.evidence", "dlg.c3.arr_03"]
		"request_explanation":
			keys += ["dlg.c3.arr_02.suspicion", "dlg.c3.arr_03.suspicion", "dlg.c3.meet_08.suspicion"]
	keys.append("dlg.c3.meet_03.elena" if choices["c3a_choose"] == "ask_elena" else "dlg.c3.meet_03.evidence")
	keys.append("dlg.c3.react." + choices["c3a_choose"])
	var rd: String = choices["c3b_choose"]
	keys.append("dlg.c3.react." + rd + (".elena" if rd == "report_delegation" and choices["c3a_choose"] == "ask_elena" else ""))
	for k in keys:
		if not spoken.has(Loc.t(k)):
			_fail("line variant %s was not spoken on this route" % k)


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


## Optional side level (parade plaza): explore it in explore mode, then leave through its exit.
func _visit_side_level() -> void:
	var t := 0.0
	while (Game.busy or Game.in_cinematic) and t < 30.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	if Game.args.has("autoplay-explore"):
		await _explore_pass()
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.kind) == "exit":
			_place_player_near(it)
			await get_tree().create_timer(0.05).timeout
			await Game.interact(it)
			break
	if Game.side_level:
		_fail("side level %s was not left through its exit" % Game.level.level_id)


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
