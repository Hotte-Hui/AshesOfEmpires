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
## --autoplay-explore (§12 + §12.9 side tasks): an exploration pass at the start of every level, on the parade
## plaza and once more right before each level's final decision (story-gated optional chats are active by then).
## A pass repeats until nothing new is findable — requirements unlock further entries, a chained hotspot moves on
## to its next entry — and the last pass of a level checks that every side task of that level is done.
## Chapter 3 part 2 (documentation/C3P2_DESIGN.md): the route goes on through the registry scenes A–D (one level file,
## three in-level protagonist switches — the driver always uses Game.player) and the quay; optional 5th/6th spec
## values choose c3d_choose / c3g_choose (default admit_plan / split_by_language). A third save (slot 3) is taken in
## registry B (Konrad playing, Alexei standing in) and reloaded at the end. Every save of the run goes to
## user://e2e/saves, never to the player's slots (same machine, same build).
## Chapter 4 part 1 (documentation/C4_DESIGN.md): the route goes on through Karsk (cellar) → Berlin (tram loop, route
## overlay) → Karsk (transfer siding, number chain) → Berlin (annex, the decision) — a level load at every city change;
## an optional 7th spec value chooses c4d_choose (default name_marta). A fourth save (the quicksave slot) is taken at the siding
## (the second scene of the tunnels file) and reloaded at the end.

## Objectives before which a level's last exploration pass runs (all its tasks must be done afterwards).
## The registry's last pass is before c3d_choose (registry B: the last registry scene with finds; its tasks are filed
## under the level key L_C3_RegistryA, ChapterExt.level_key).
## Chapter 4: the tunnels' last pass is before c4c_talk_lev (siding), the annex's before c4d_choose (C4_DESIGN §9).
const FINAL_PASS := ["a1_choose", "m1_choose", "c3a_choose", "c3b_choose", "c3d_choose", "c3g_choose", "c4c_talk_lev",
	"c4d_choose"]
## Objectives before which a (non-final) exploration pass runs: level starts and story-gated openings.
const EXPLORE_AT := ["a1_talk_irina", "m1_inspect_plan_a", "c3a_talk_conductor", "c3b_arrival", "c3b_inspect_booth",
	"c3c_inspect_crates", "c3c_talk_konrad", "c3d_inspect_intake", "c3g_inspect_halves",
	"c4a_inspect_shelf", "c4a_open_door", "c4b_inspect_notice", "c4b_inspect_crates", "c4c_inspect_card",
	"c4d_inspect_drawer"]
const E2E_SAVES := "user://e2e/saves"

const ROUTE := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal",
	"a1_inspect_ledger", "a1_choose", "m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans",
	"m1_talk_emil", "m1_choose",
	"c3a_talk_conductor", "c3a_inspect_weighbill", "c3a_inspect_departures", "c3a_pass_control", "c3a_talk_elena",
	"c3a_choose", "c3b_arrival", "c3b_inspect_seating", "c3b_inspect_log", "c3b_solve_protocol", "c3b_inspect_booth",
	"c3b_talk_alexei", "c3b_choose",
	"c3c_inspect_crates", "c3c_inspect_night_book", "c3c_talk_konrad",
	"c3d_inspect_intake", "c3d_inspect_drawer", "c3d_talk_compare", "c3d_solve_check", "c3d_inspect_plan",
	"c3d_talk_partner", "c3d_choose", "c3e_take_file", "c3e_try_ramp", "c3e_reach_konrad",
	"c3f_inspect_hose", "c3f_push_desk", "c3f_climb", "c3g_inspect_halves", "c3g_talk_konrad", "c3g_choose",
	"c4a_inspect_shelf", "c4a_talk_lev", "c4a_inspect_book", "c4a_inspect_carbon", "c4a_talk_tunnel", "c4a_open_door",
	"c4b_inspect_notice", "c4b_talk_marta", "c4b_solve_routes", "c4b_inspect_column", "c4b_talk_ilse", "c4b_inspect_crates",
	"c4c_inspect_card", "c4c_inspect_stencils", "c4c_solve_numbers", "c4c_inspect_wagon", "c4c_talk_lev",
	"c4d_inspect_drawer", "c4d_inspect_plan", "c4d_inspect_tube", "c4d_talk_registrar", "c4d_choose"]
## flag written by each choice (C3_DESIGN §2.4); used to verify the consequence meters at the end
const CHOICE_FLAG := {"share_with_irina": "irina_trust", "keep_private": "alexei_secrecy",
	"preserve_evidence": "konrad_evidence", "request_explanation": "office_suspicion",
	"ask_elena": "elena_trust", "note_alone": "evidence_chain", "share_protocol": "alexei_konrad_trust",
	"search_elena": "elena_trust", "report_delegation": "kessler_alerted",
	"admit_plan": "alexei_konrad_trust", "pocket_plan": "evidence_chain", "split_by_language": "evidence_chain",
	"swap_halves": "alexei_konrad_trust", "hide_for_elena": "elena_trust",
	"name_marta": "evidence_chain", "protect_marta": "civilian_welfare"}

var choices := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence", "c3a_choose": "ask_elena",
	"c3b_choose": "share_protocol", "c3d_choose": "admit_plan", "c3g_choose": "split_by_language",
	"c4d_choose": "name_marta"}
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
	if parts.size() >= 5 and parts[4] != "":
		choices["c3d_choose"] = parts[4]
	if parts.size() >= 6 and parts[5] != "":
		choices["c3g_choose"] = parts[5]
	if parts.size() >= 7 and parts[6] != "":
		choices["c4d_choose"] = parts[6]
	skip = do_skip
	shots_dir = shots


func run() -> void:
	_isolate_saves()
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
	var saved_switch := ""
	var saved_switch_pos := Vector2.ZERO
	var saved_c4 := ""
	for oid in ROUTE:
		# cinematics between the scenes play in real time unless skipped (the night: LS_C3_Close + LS_C3_Radio ≈ 41 s)
		var ok := await _wait_available(oid, 120.0)
		if not ok:
			_fail("objective never became available: " + oid + " scene=" + Game._story_scene())
			break
		if oid in EXPLORE_AT and Game.args.has("autoplay-explore"):
			await _explore_pass()
		if oid in FINAL_PASS and Game.args.has("autoplay-explore"):
			await _explore_pass(true)
		if oid == "c3a_talk_conductor" and Game.args.has("autoplay-memories"):   # §12.10 memory round trip
			var md: Node = load("res://scripts/core/memory_drive.gd").new()
			add_child(md)
			if not await md.autoplay(self):
				for f in md.failures:
					_fail("memories: " + str(f))
			md.queue_free()
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
		if oid == "c3d_inspect_intake":   # registry B: a save inside a switch scene (TECHNICAL_ARCHITECTURE §12.11)
			if Game.player == null or str(Game.player.get("char_id")) != "konrad" or str(Game.level.level_id) != "L_C3_RegistryB":
				_fail("registry B is not played by Konrad in the shared level (player %s, level %s)" % [
					Game.player.get("char_id") if Game.player else "none", Game.level.level_id])
			var r3 = Saves.save("3")
			if not (r3 is Dictionary and r3.get("ok", false)):
				_fail("save slot 3 failed: " + str(r3))
			saved_switch = Story.save_json()
			saved_switch_pos = Game.player.position if Game.player else Vector2.ZERO
		if oid == "c4c_inspect_card":     # the siding: the SECOND scene of the tunnels file, reached by a level load
			if Game.level == null or str(Game.level.level_id) != "L_C4_TunnelsB" or Game.player == null \
					or str(Game.player.get("char_id")) != "alexei":
				_fail("the siding is not L_C4_TunnelsB played by Alexei (level %s)" % [Game.level.level_id if Game.level else "none"])
			var r4 = Saves.save("quick")
			if not (r4 is Dictionary and r4.get("ok", false)):
				_fail("quicksave at the siding failed: " + str(r4))
			saved_c4 = Story.save_json()
	# finale: the director runs LS_C3_Close + the end card after c3b_choose; wait for completion
	var t := 0.0
	while not Story.flag("slice_finished") and t < 240.0:
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
	for ev in ["c4a_completed", "c4b_completed", "c4c_completed", "c4d_completed"]:
		if not Story.has_event(ev):
			_fail("Chapter 4 event %s missing" % ev)
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
	if saved_switch != "":
		await _check_switch_save(saved_switch, saved_switch_pos)
	if saved_c4 != "":
		await _check_c4_save(saved_c4)
	if failures.is_empty():
		print("AUTOPLAY_PASS choices=", choices, " skip=", skip, " playtime=", snapped(Game.playtime, 0.1))
		get_tree().quit(0)
	else:
		for f in failures:
			print("AUTOPLAY_FAIL ", f)
		get_tree().quit(1)


## Slot 3 (registry B) restores the shared level as scene B: Konrad controlled near where he was, Alexei standing in.
func _check_switch_save(saved: String, pos: Vector2) -> void:
	if not Game.has_method("_on_load_slot"):
		_fail("Game cannot load a slot into the game (_on_load_slot missing)")
		return
	var w := 0.0
	while Game.in_cinematic and w < 30.0:     # let the finale flow (end card) finish first
		await get_tree().process_frame
		w += get_process_delta_time()
	await Game._on_load_slot("3")      # Saves.load + the director's own continuation (level, positions, partner)
	var t := 0.0
	while (Game.level == null or Game.player == null or Game.busy) and t < 20.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	if Story.save_json() != saved:
		_fail("loaded registry-B state differs from saved snapshot")
	if Game.level == null or str(Game.level.level_id) != "L_C3_RegistryB" or Game._story_scene() != "L_C3_RegistryB":
		_fail("slot 3 did not restore registry B (level %s, story %s)" % [Game.level.level_id if Game.level else "none", Game._story_scene()])
		return
	if Game.player == null or str(Game.player.get("char_id")) != "konrad":
		_fail("slot 3: Konrad is not the controlled protagonist")
	elif Game.player.position.distance_to(pos) > 4.0:
		_fail("slot 3: player restored at %s, saved at %s" % [Game.player.position, pos])
	var partner_here := false
	for n in get_tree().get_nodes_in_group("npcs"):
		if str(n.get("char_id")) == "alexei" and n.get("visible") != false:
			partner_here = true
	if not partner_here:
		_fail("slot 3: Alexei does not stand in as the partner")
	if Story.objective_state("c3d_inspect_drawer") != "available":
		_fail("slot 3: wrong progress (c3d_inspect_drawer %s)" % Story.objective_state("c3d_inspect_drawer"))


## The quicksave of the transfer siding restores the tunnels file as its second scene: Alexei in the siding area, Lev there.
func _check_c4_save(saved: String) -> void:
	var w := 0.0
	while Game.in_cinematic and w < 30.0:
		await get_tree().process_frame
		w += get_process_delta_time()
	await Game._on_load_slot("quick")
	var t := 0.0
	while (Game.level == null or Game.player == null or Game.busy) and t < 20.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	if Story.save_json() != saved:
		_fail("loaded siding state differs from saved snapshot")
	if Game.level == null or str(Game.level.level_id) != "L_C4_TunnelsB" or Game._story_scene() != "L_C4_TunnelsB":
		_fail("the siding save did not restore the siding (level %s, story %s)" % [Game.level.level_id if Game.level else "none", Game._story_scene()])
		return
	if Game.player == null or str(Game.player.get("char_id")) != "alexei":
		_fail("siding save: Alexei is not the controlled protagonist")
	elif Game.player.position.x < 720.0:
		_fail("siding save: Alexei restored in the cellar area (x %.0f), not at the siding" % Game.player.position.x)
	var lev_here := false
	for n in get_tree().get_nodes_in_group("npcs"):
		if str(n.get("char_id")) == "lev" and n.get("visible") != false and (n as Node2D).position.x > 720.0:
			lev_here = true
	if not lev_here:
		_fail("siding save: Lev is not at the siding")
	if Story.objective_state("c4c_inspect_stencils") != "available":
		_fail("siding save: wrong progress (c4c_inspect_stencils %s)" % Story.objective_state("c4c_inspect_stencils"))


## Every save of the run goes to a private folder: the player's slots in user://saves are never touched.
func _isolate_saves() -> void:
	DirAccess.make_dir_recursive_absolute(E2E_SAVES)
	var d := DirAccess.open(E2E_SAVES)
	if d:
		for f in d.get_files():
			d.remove(f)
	Saves.base_dir = E2E_SAVES


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
	# Chapter 3 part 2 (C3P2_DESIGN §2.8): the variants every route must hear, and the reactions of both decisions
	keys.append("dlg.c3p2.night_04." + ("cafe" if choices["c3a_choose"] == "ask_elena" else "alone"))
	keys.append("dlg.c3p2.night_11." + ("evidence" if choices["m1_choose"] == "preserve_evidence" else "suspicion"))
	keys.append("dlg.c3p2.cmp_04." + ("evidence" if choices["m1_choose"] == "preserve_evidence" else "suspicion"))
	keys.append("dlg.c3p2.cmp_05." + ("irina" if choices["a1_choose"] == "share_with_irina" else "secrecy"))
	if rd == "report_delegation":
		keys += ["dlg.c3p2.night_01.report", "dlg.c3p2.night_13.report", "dlg.c3p2.par_06.report", "dlg.c3p2.snw_11.report"]
	elif rd == "share_protocol":
		keys += ["dlg.c3p2.night_01.share", "dlg.c3p2.cmp_03.share"]
	else:
		keys.append("dlg.c3p2.night_05.search")
	if choices["c3d_choose"] == "pocket_plan":
		keys.append("dlg.c3p2.smk_06.pocket")
	keys.append("dlg.c3p2.react.%s%s" % [choices["c3d_choose"],
		".report" if choices["c3d_choose"] == "admit_plan" and rd == "report_delegation" else ""])
	keys.append("dlg.c3p2.react." + choices["c3g_choose"])
	# Chapter 4 part 1 (C4_DESIGN §2.8): the variants every route must hear, and the reaction of the decision
	keys.append("dlg.c4.lev_01." + ("irina" if choices["a1_choose"] == "share_with_irina" else "secrecy"))
	if choices["a1_choose"] == "keep_private":
		keys.append("dlg.c4.tun_08.secrecy")
	keys.append("dlg.c4.mar_02." + ("evidence" if choices["m1_choose"] == "preserve_evidence" else "suspicion"))
	keys.append("dlg.c4.mar_04.admit" if choices["c3d_choose"] == "admit_plan" else "dlg.c4.mar_12.pocket")
	match choices["c3g_choose"]:
		"split_by_language":
			keys.append("dlg.c4.sid_08.split")
		"swap_halves":
			keys += ["dlg.c4.lev_04.swap", "dlg.c4.sid_08.swap"]
		"hide_for_elena":
			keys += ["dlg.c4.lev_04.elena", "dlg.c4.sid_08.elena"]
	if rd == "report_delegation":
		keys.append("dlg.c4.cnt_03.kessler")
	elif choices["m1_choose"] == "request_explanation":
		keys.append("dlg.c4.cnt_03.suspicion")
	var trust := int(rd == "share_protocol") + int(choices["c3d_choose"] == "admit_plan") + int(choices["c3g_choose"] == "swap_halves")
	if trust >= 2:
		keys.append("dlg.c4.sid_10.trust")
	keys.append("dlg.c4.react." + choices["c4d_choose"])
	for k in keys:
		if not spoken.has(Loc.t(k)):
			_fail("line variant %s was not spoken on this route" % k)


## §12 / §12.9: interactables that would record something new right now — discover/chat hotspots in the tree whose
## current entry is not found yet and which are active (story gates, "requires", once) — in the given order.
## Pure helper shared with inputplay.gd; `ex` = the Explore service (or a test double with is_found).
static func pending_finds(nodes: Array, ex: Object) -> Array:
	var out: Array = []
	for it in nodes:
		if not is_instance_valid(it) or not it.is_inside_tree():
			continue
		if not (str(it.get("kind")) == "discover" or str(it.get("kind")) == "chat"):
			continue
		var id := str(it.get("explore_id"))
		if id == "" or ex.is_found(id) or not it.has_method("is_active") or not it.is_active():
			continue
		out.append(it)
	return out


## Every explore id an exploration interactable can show (its explore_id and its explore_chain).
static func explore_ids_of(it: Node) -> Array:
	var ids: Array = []
	var chain = it.get("explore_chain")
	if chain != null:
		for c in chain:
			if not (str(c) in ids):
				ids.append(str(c))
	var id := str(it.get("explore_id"))
	if not (id in ids):
		ids.append(id)
	return ids


## §12: trigger every optional find / chat of the current level through the normal Game.interact path and
## check Explore recorded it (gates of the canonical route are untouched: these never change Story state).
## §12.9: repeats until nothing new is findable (requirements unlock entries, chains move on to their next
## entry); each hotspot+entry pair is tried once. `final`: afterwards every side task of the level must be done.
func _explore_pass(final := false) -> void:
	var snapshot := Story.save_json()
	var lid := str(Game.level.level_id)
	# a level file shared by several Story scenes files its finds and tasks under its first scene (C3P2_DESIGN §7)
	if Game.get("ext") != null and Game.ext.has_method("level_key"):
		lid = str(Game.ext.level_key(lid))
	for it in get_tree().get_nodes_in_group("interactables"):
		if not it.is_inside_tree() or not (str(it.kind) == "discover" or str(it.kind) == "chat"):
			continue
		for id in explore_ids_of(it):
			if str(id) == "" or not Explore.has_entry(str(id)):
				_fail("explore: interactable %s has unknown explore_id '%s'" % [it.name, id])
	var n := 0
	var tried := {}
	var guard := 0
	while guard < 500:
		guard += 1
		var it: Node = null
		for cand in pending_finds(get_tree().get_nodes_in_group("interactables"), Explore):
			if not tried.has("%d:%s" % [cand.get_instance_id(), cand.explore_id]):
				it = cand
				break
		if it == null:
			break
		var id := str(it.explore_id)
		tried["%d:%s" % [it.get_instance_id(), id]] = true
		_place_player_near(it)
		await get_tree().create_timer(0.05).timeout
		await Game.interact(it)
		if not Explore.is_found(id):
			_fail("explore: %s not recorded" % id)
		n += 1
	if Story.save_json() != snapshot:
		_fail("explore: optional content changed the canonical Story state")
	var done := 0
	var tasks: Array = Explore.tasks_for(lid) if Explore.has_method("tasks_for") else []
	for t in tasks:
		var st: Dictionary = Explore.task_state(str(t["id"]))
		if str(st["state"]) == "done":
			done += 1
		elif final:
			_fail("explore: side task %s not completed in %s (%s, step %d)" % [t["id"], lid, st["state"], st["step"]])
	var c: Dictionary = Explore.counts(lid)
	print("AUTOPLAY explored %d finds in %s (%s/%s), history %s, tasks %d/%d%s" % [n, lid, c.get("found", 0),
		c.get("total", 0), Explore.history_counts(), done, tasks.size(), " (final pass)" if final else ""])


## Optional side level (parade plaza): explore it in explore mode, then leave through its exit.
func _visit_side_level() -> void:
	var t := 0.0
	while (Game.busy or Game.in_cinematic) and t < 30.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	if Game.args.has("autoplay-explore"):
		await _explore_pass(true)
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
