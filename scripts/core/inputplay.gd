extends Node
## Real-input end-to-end test. Unlike autoplay.gd (which calls Game.interact directly), this driver touches
## the game ONLY through synthetic keyboard events (Input.parse_input_event), exactly like a player:
##   main menu (arrow keys + Enter) -> disclaimer -> intro pan -> journal + pause menu -> walking to every
##   hotspot (WASD + Shift) -> E to interact -> dialogue advanced with Space -> inspect views closed with E/Esc
##   -> signal puzzle via number keys (one wrong attempt) -> blueprint puzzle via R + arrows (one wrong attempt)
##   -> choices via arrow keys / number keys -> cinematics watched or skipped with Esc -> end card ->
##   main menu -> "Fortsetzen" resumes the last autosave.
##   godot --path . -- --inputplay=share_with_irina,preserve_evidence [--inputplay-skip] [--inputplay-shots=DIR]
## Prints INPUTPLAY_PASS / INPUTPLAY_FAIL and quits with exit code 0 / 1.
## Chapter 3: after M1 the route continues through L_C3_Station (one exploration find + one optional chat by real
## input first) and L_C3_Hall incl. the protocol puzzle (one wrong order, then the right one); optional 3rd/4th spec
## values choose c3a_choose / c3b_choose. Chapter 3 part 2 (documentation/C3P2_DESIGN.md): the registry scenes A–D
## in ONE level file with three in-level protagonist switches (TECHNICAL_ARCHITECTURE §12.11; the driver always
## walks Game.player) incl. the check puzzle (CheckPuzzle: one wrong order, then the right one), then the quay;
## optional 5th/6th spec values choose c3d_choose / c3g_choose. "Fortsetzen" must resume before the last decision
## (c3g_choose on the quay). Saves of the run go to user://e2e/saves (never the player's slots).
## --inputplay-explore (§12 + §12.9 side tasks): walks every level at its start, the parade plaza, and once more
## right before each level's final decision (story-gated chats are active by then); a walk repeats, nearest first,
## until nothing new is findable (requirements unlock entries, chained hotspots move on to their next entry), and
## the last walk of a level checks that every side task of that level is done.

const Autoplay := preload("res://scripts/core/autoplay.gd")

const A1 := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger",
	"a1_choose"]
const M1 := ["m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans", "m1_talk_emil", "m1_choose"]
const C3A := ["c3a_talk_conductor", "c3a_inspect_weighbill", "c3a_inspect_departures", "c3a_pass_control",
	"c3a_talk_elena", "c3a_choose"]
const C3B := ["c3b_arrival", "c3b_inspect_seating", "c3b_inspect_log", "c3b_solve_protocol", "c3b_inspect_booth",
	"c3b_talk_alexei", "c3b_choose"]
## Chapter 3 part 2 (C3P2_DESIGN.md §2.3): registry A (Alexei) → B (Konrad) → C (Alexei) → D (Konrad) → quay (Alexei)
const C3C := ["c3c_inspect_crates", "c3c_inspect_night_book", "c3c_talk_konrad"]
const C3D := ["c3d_inspect_intake", "c3d_inspect_drawer", "c3d_talk_compare", "c3d_solve_check", "c3d_inspect_plan",
	"c3d_talk_partner", "c3d_choose"]
const C3E := ["c3e_take_file", "c3e_try_ramp", "c3e_reach_konrad"]
const C3F := ["c3f_inspect_hose", "c3f_push_desk", "c3f_climb"]
const C3G := ["c3g_inspect_halves", "c3g_talk_konrad", "c3g_choose"]
## Scenes of a shared level whose route does not end the level's exploration: their last walk is not "final" (the
## registry's side tasks are checked at the end of B, the last registry scene with finds; C/D have none).
const NOT_FINAL_WALK := ["L_C3_RegistryA", "L_C3_RegistryC", "L_C3_RegistryD"]
## Choices answered with arrow keys + Enter (the others with number keys).
const ARROW_CHOICES := ["a1_choose", "c3a_choose", "c3g_choose"]
const E2E_SAVES := "user://e2e/saves"

var choices := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence", "c3a_choose": "ask_elena",
	"c3b_choose": "share_protocol", "c3d_choose": "admit_plan", "c3g_choose": "split_by_language"}
var skip_cine := false
var shots_dir := ""
var failures: Array = []
var ui: Node
var _held: Dictionary = {}
var _shot := 0
var _inspect_by_escape := false


func configure(spec: String, do_skip: bool, shots: String) -> void:
	var parts := spec.split(",")
	if parts.size() >= 1 and parts[0] != "" and parts[0] != "1":
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
	skip_cine = do_skip
	shots_dir = shots


func run() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	ui = Game.ui
	# Isolate the test from the real mouse: the fullscreen window would otherwise receive hover events from
	# whoever is using the computer (hovering a menu button moves the focus). Mouse events now pass through.
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mouse_passthrough(PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)]))
	_isolate_saves()
	print("INPUTPLAY start choices=", choices, " skip=", skip_cine)
	var t0 := Time.get_ticks_msec()
	if ui == null:
		_fail("no UI loaded")
		_finish(t0)
		return
	if await _menu_new_game() and await _intro() and await _menus_in_game() \
			and await _play_route(A1, "L_A1_Railyard") and await _play_route(M1, "L_M1_Archive") \
			and await _memories_trip() and await _explore_sample() and await _play_route(C3A, "L_C3_Station") \
			and await _play_route(C3B, "L_C3_Hall") and await _play_route(C3C, "L_C3_RegistryA") \
			and await _play_route(C3D, "L_C3_RegistryB") and await _play_route(C3E, "L_C3_RegistryC") \
			and await _play_route(C3F, "L_C3_RegistryD") and await _play_route(C3G, "L_C3_Quay") and await _ending():
		await _continue_from_menu()
	_finish(t0)


## The run plays a whole game with autosaves: keep them out of the player's user://saves (same machine, same build).
func _isolate_saves() -> void:
	DirAccess.make_dir_recursive_absolute(E2E_SAVES)
	var d := DirAccess.open(E2E_SAVES)
	if d:
		for f in d.get_files():
			d.remove(f)
	Saves.base_dir = E2E_SAVES


func _finish(t0: int) -> void:
	_release_all()
	var secs := (Time.get_ticks_msec() - t0) / 1000.0
	if failures.is_empty():
		print("INPUTPLAY_PASS choices=", choices, " skip=", skip_cine, " seconds=", snapped(secs, 0.1))
		get_tree().quit(0)
	else:
		for f in failures:
			print("INPUTPLAY_FAIL ", f)
		get_tree().quit(1)


# ------------------------------------------------------------------ phases
func _menu_new_game() -> bool:
	var mm: Node = ui.get("main_menu")
	if not await _until(func(): return mm.is_open, 15.0):
		return _fail("main menu did not open")
	await _wait(1.2)
	await _shoot("main_menu")
	var target: Control = mm._buttons["new"]
	for i in 8:
		if get_viewport().gui_get_focus_owner() == target:
			break
		await _tap(KEY_DOWN)
	if get_viewport().gui_get_focus_owner() != target:
		return _fail("could not focus 'Neues Spiel' with the arrow keys")
	await _tap(KEY_ENTER)
	if not await _until(func(): return Game.in_cinematic, 6.0):   # disclaimer card
		return _fail("disclaimer did not start after 'Neues Spiel'")
	await _wait(1.5)
	await _shoot("disclaimer")
	if skip_cine:
		await _tap(KEY_SPACE)
	return true


func _intro() -> bool:
	if not await _until(func(): return Game.level != null and str(Game.level.level_id) == "L_A1_Railyard", 20.0):
		return _fail("A1 did not load after new game")
	# first visit: establishing pan (cinematic) -> watch a bit, then skip it with Esc
	if await _until(func(): return Game.in_cinematic, 4.0):
		await _wait(2.0)
		await _shoot("intro_pan")
		await _tap(KEY_ESCAPE)
	if not await _until(_gameplay_ready, 20.0):
		return _fail("no control after the intro pan")
	await _wait(0.8)
	await _shoot("a1_start")
	return true


func _menus_in_game() -> bool:
	await _tap(KEY_J)
	var jr: Node = ui.get("journal")
	if not await _until(func(): return jr.is_open and get_tree().paused, 3.0):
		return _fail("J did not open the journal (or the game was not paused)")
	await _wait(0.6)
	await _shoot("journal")
	await _tap(KEY_ESCAPE)
	if not await _until(func(): return not jr.is_open and not get_tree().paused, 3.0):
		return _fail("Esc did not close the journal")
	await _tap(KEY_ESCAPE)
	var pm: Node = ui.get("pause_menu")
	if not await _until(func(): return pm.is_open and get_tree().paused, 3.0):
		return _fail("Esc did not open the pause menu")
	await _wait(0.5)
	await _shoot("pause")
	await _tap(KEY_ESCAPE)
	if not await _until(func(): return not pm.is_open and not get_tree().paused, 3.0):
		return _fail("Esc did not close the pause menu")
	await _wait(0.3)
	return true


## §12.10 (--inputplay-memories): at the start of the station, keys only — Esc → „Erinnerungen“ → the Karsk card →
## Enter, one find and the remembered conversation there, Esc → „In die Gegenwart zurückkehren“ → Enter.
func _memories_trip() -> bool:
	if not Game.args.has("inputplay-memories"):
		return true
	if not await _until(func(): return _gameplay_ready() and str(Game.level.level_id) == "L_C3_Station", 120.0):
		return _fail("memories: never got control in L_C3_Station")
	var md: Node = load("res://scripts/core/memory_drive.gd").new()
	add_child(md)
	var ok: bool = await md.inputplay(self)
	for f in md.failures:
		_fail("memories: " + str(f))
	md.queue_free()
	return ok and failures.is_empty()


func _play_route(route: Array, level_id: String) -> bool:
	if not await _until(func(): return _gameplay_ready() and str(Game.level.level_id) == level_id, 90.0):
		return _fail("never got control in " + level_id)
	if Game.args.has("inputplay-explore"):
		await _explore_level(level_id)
		if not failures.is_empty():
			return false
	for oid in route:
		if not await _until(func(): return Story.is_available(oid) and _gameplay_ready(), 30.0):
			return _fail("objective never available: " + oid)
		if oid == "c3b_inspect_booth" and Game.args.has("inputplay-explore"):
			await _explore_level(level_id)          # the session is running: the relay desk is open now
			if not failures.is_empty():
				return false
		if oid == route[route.size() - 1] and Game.args.has("inputplay-explore"):
			await _explore_level(level_id, not NOT_FINAL_WALK.has(level_id))   # §12.9: gated chats open; finish every task
			if not failures.is_empty():
				return false
			if not await _until(func(): return Story.is_available(oid) and _gameplay_ready(), 30.0):
				return _fail("objective not available after the exploration walk: " + oid)
		var it := _interactable(oid)
		if it == null:
			return _fail("no interactable for " + oid)
		if not await _walk_to_focus(it):
			return _fail("could not walk into the prompt range of " + oid + " (player at %s, target %s)" % [
				Game.player.global_position if Game.player else Vector2.ZERO, it.global_position])
		await _shoot("prompt_" + oid)
		await _tap(KEY_E)
		if not await _until(func(): return Game.busy, 3.0):
			return _fail("E did not start the interaction for " + oid)
		match str(it.kind):
			"dialogue":
				await _dialogue(oid, "")
			"choice":
				await _dialogue(oid, str(choices.get(oid, "")))
			"inspect":
				await _inspect(oid)
			"puzzle":
				if oid == "a1_solve_signal":
					await _signal_puzzle()
				elif oid == "c3b_solve_protocol":
					await _protocol_puzzle()
				elif oid == "c3d_solve_check":
					await _check_puzzle()
				else:
					await _blueprint_puzzle()
		if not await _until(func(): return not Game.busy, 20.0):
			return _fail("interaction never finished: " + oid)
		if Story.objective_state(oid) != "complete":
			return _fail("objective not complete after real input: " + oid)
		await _settle(oid)
		if not failures.is_empty():
			return false
		if Game.side_level:
			await _visit_side_level_keys()
			if not failures.is_empty():
				return false
	return true


func _ending() -> bool:
	var mm: Node = ui.get("main_menu")
	# the closing credits roll (≈84 s) is skipped with Esc, like a player would
	var credits: Node = ui.get("end_credits")
	var waited := 0.0
	while not mm.is_open and waited < 180.0:
		if credits and credits.visible:
			await _wait(1.0)
			await _shoot("end_credits")
			await _tap(KEY_ESCAPE)
			await _wait(1.0)
			waited += 2.0
			continue
		await _wait(0.25)
		waited += 0.25
	if not mm.is_open:
		return _fail("never returned to the main menu after the finale")
	if not Story.flag("slice_finished"):
		_fail("slice_finished flag missing after the finale")
	var hist: Dictionary = Story.choice_history()
	for k in choices:
		if str(hist.get(k, "")) != choices[k]:
			_fail("choice %s recorded as %s" % [k, hist.get(k)])
	return failures.is_empty()


func _continue_from_menu() -> void:
	var mm: Node = ui.get("main_menu")
	await _wait(1.2)
	await _shoot("menu_after_demo")
	var cont: Control = mm._buttons["continue"]
	if not cont.visible:
		_fail("'Fortsetzen' not offered although autosaves exist")
		return
	for i in 8:
		if get_viewport().gui_get_focus_owner() == cont:
			break
		await _tap(KEY_UP)
	await _tap(KEY_ENTER)
	if not await _until(func(): return _gameplay_ready(), 30.0):
		_fail("'Fortsetzen' did not resume play")
		return
	if str(Game.level.level_id) != "L_C3_Quay" or Story.objective_state("c3g_choose") != "available":
		_fail("'Fortsetzen' resumed at %s (c3g_choose %s), expected the last playable autosave" % [
			Game.level.level_id, Story.objective_state("c3g_choose")])
	await _wait(0.8)
	await _shoot("continued")


# ------------------------------------------------------------------ interaction handlers (keys only)
func _dialogue(oid: String, choice_id: String) -> void:
	var dlg: Node = ui.get("dialogue")
	var picked := false
	var lines := 0
	var t := 0.0
	while Game.busy and t < 90.0:
		if dlg._choices_active:
			if choice_id == "" or picked:
				_fail("unexpected choice list in " + oid)
				return
			await _wait(0.6)          # longer than the mashed-key guard
			await _shoot("choice_" + oid)
			var ids: Array = []
			for c in Game.objectives.get(oid, {}).get("choices", []):
				ids.append(str(c["id"]))
			var idx := ids.find(choice_id)
			if idx < 0:
				_fail("unknown choice id " + choice_id)
				return
			if ARROW_CHOICES.has(oid):    # arrow keys + Enter
				for i in idx:
					await _tap(KEY_DOWN)
				await _tap(KEY_ENTER)
			else:                     # number key
				await _tap(KEY_1 + idx)
			picked = true
			await _wait(0.4)
			continue
		if dlg.is_open:
			lines += 1
			if lines == 2:
				await _shoot("dialogue_" + oid)
			await _tap(KEY_SPACE)     # first press completes typing, second advances
			await _wait(0.18)
			await _tap(KEY_SPACE)
			await _wait(0.3)
			t += 0.6
			continue
		await _wait(0.1)
		t += 0.1
	if choice_id != "" and not picked:
		_fail("choice list never appeared for " + oid)


func _inspect(oid: String) -> void:
	var insp: Node = ui.get("inspect")
	if not await _until(func(): return insp.is_open, 5.0):
		_fail("inspect view did not open for " + oid)
		return
	await _wait(0.7)
	await _shoot("inspect_" + oid)
	_inspect_by_escape = not _inspect_by_escape
	await _tap(KEY_ESCAPE if _inspect_by_escape else KEY_E)
	if not await _until(func(): return not insp.is_open, 3.0):
		_fail("inspect view did not close with " + ("Esc" if _inspect_by_escape else "E"))


func _signal_puzzle() -> void:
	var pz: Node = ui.get("signal_puzzle")
	if not await _until(func(): return pz.is_open, 5.0):
		_fail("signal puzzle did not open")
		return
	await _wait(0.6)
	for k in [KEY_1, KEY_2, KEY_3]:          # display order = triangle, square, circle -> wrong
		await _tap(k)
	await _tap(KEY_ENTER)
	await _wait(0.6)
	if Story.objective_state("a1_solve_signal") == "complete":
		_fail("signal puzzle accepted a wrong order")
		return
	for i in 3:
		await _tap(KEY_BACKSPACE)
	for sym in ["square", "circle", "triangle"]:
		var idx: int = pz.symbols.find(sym)
		await _tap(KEY_1 + idx)
	await _wait(0.3)
	await _shoot("signal_puzzle")
	await _tap(KEY_ENTER)
	if not await _until(func(): return not pz.is_open, 6.0):
		_fail("signal puzzle did not close after the correct order (state %s)" % Story.objective_state("a1_solve_signal"))


func _blueprint_puzzle() -> void:
	var pz: Node = ui.get("blueprint_puzzle")
	if not await _until(func(): return pz.is_open, 5.0):
		_fail("blueprint puzzle did not open")
		return
	await _wait(0.6)
	await _shoot("blueprint_start")
	await _tap(KEY_ENTER)                     # wrong: start pose is rotated 180 degrees
	await _wait(0.6)
	if Story.objective_state("m1_align_plans") == "complete":
		_fail("blueprint puzzle accepted the unaligned start pose")
		return
	for k in [KEY_R, KEY_R, KEY_RIGHT, KEY_RIGHT, KEY_UP]:
		await _tap(k)
	await _wait(0.3)
	await _shoot("blueprint_aligned")
	await _tap(KEY_ENTER)
	if not await _until(func(): return not pz.is_open, 6.0):
		_fail("blueprint puzzle did not close after aligning (state %s)" % Story.objective_state("m1_align_plans"))


## Chapter-3 protocol puzzle (scenes/ui/ProtocolPuzzle.tscn, registered by data/chapters/c3.json): number keys
## place the n-th card of the tray (display order) into the next slot; one wrong order first, then the right one.
func _protocol_puzzle() -> void:
	var pz: Node = null
	var t := 0.0
	while t < 5.0 and (pz == null or not pz.is_open):
		pz = _ui_child("protocol_puzzle.gd")
		await get_tree().process_frame
		t += get_process_delta_time()
	if pz == null or not pz.is_open:
		_fail("protocol puzzle did not open")
		return
	await _wait(0.6)
	await _shoot("protocol_start")
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:     # display order soviet, secretariat, chair, reich -> wrong
		await _tap(k)
	await _tap(KEY_ENTER)
	await _wait(0.6)
	if Story.objective_state("c3b_solve_protocol") == "complete":
		_fail("protocol puzzle accepted a wrong order")
		return
	for i in 4:
		await _tap(KEY_BACKSPACE)
	var shown: Array = pz.get("symbols") if pz.get("symbols") is Array else ["soviet", "secretariat", "chair", "reich"]
	for sym in ["chair", "reich", "secretariat", "soviet"]:
		await _tap(KEY_1 + shown.find(sym))
	await _wait(0.3)
	await _shoot("protocol_solved")
	await _tap(KEY_ENTER)
	if not await _until(func(): return not pz.is_open, 8.0):
		_fail("protocol puzzle did not close after the correct order (state %s)" % Story.objective_state("c3b_solve_protocol"))


## Chapter-3 part-2 check puzzle (scenes/ui/CheckPuzzle.tscn, C3P2_DESIGN.md §2.7 key contract = the protocol
## puzzle's): number key n places the n-th tray card on the next row; one wrong order first, then the right one.
func _check_puzzle() -> void:
	var pz: Node = null
	var t := 0.0
	while t < 5.0 and (pz == null or not pz.is_open):
		pz = _ui_child("check_puzzle.gd")
		await get_tree().process_frame
		t += get_process_delta_time()
	if pz == null or not pz.is_open:
		_fail("check puzzle did not open")
		return
	var data_shown: Array = Story.puzzle_for("c3d_solve_check").get("display_symbols", [])
	var shown: Array = pz.get("symbols") if pz.get("symbols") is Array else data_shown
	await _wait(0.6)
	await _shoot("check_start")
	for k in [KEY_1, KEY_2, KEY_3, KEY_4]:     # the tray order is a wrong answer (C3P2_DESIGN §2.7)
		await _tap(k)
	await _tap(KEY_ENTER)
	await _wait(0.6)
	if Story.objective_state("c3d_solve_check") == "complete":
		_fail("check puzzle accepted a wrong order")
		return
	for i in 4:
		await _tap(KEY_BACKSPACE)
	for sym in ["in_c17_44", "out_2340", "par_4", "january"]:
		await _tap(KEY_1 + shown.find(sym))
	await _wait(0.3)
	await _shoot("check_solved")
	await _tap(KEY_ENTER)
	if not await _until(func(): return not pz.is_open, 8.0):
		_fail("check puzzle did not close after the correct order (state %s)" % Story.objective_state("c3d_solve_check"))


func _ui_child(script_suffix: String) -> Node:
	for c in ui.get_children():
		var sc = c.get_script()
		if sc and str(sc.resource_path).ends_with(script_suffix):
			return c
	return null


## Station: one exploration find and one optional conversation, by real input (§12 interactables).
func _explore_sample() -> bool:
	if not await _until(func(): return _gameplay_ready() and str(Game.level.level_id) == "L_C3_Station", 120.0):
		return _fail("never got control in L_C3_Station")
	for eid in ["veltrava.station.four_rails", "veltrava.station.chat_voronova"]:
		var it := _optional(eid)
		if it == null:
			return _fail("no interactable for " + eid)
		if not await _walk_to_focus(it):
			return _fail("could not walk into the prompt range of " + eid)
		await _shoot("prompt_" + eid)
		await _tap(KEY_E)
		if not await _until(func(): return Game.busy, 3.0):
			return _fail("E did not start " + eid)
		await _drain_interaction(eid)      # pages through the DiscoveryView / chat lines with Space
		if not await _until(func(): return not Game.busy, 20.0):
			return _fail("interaction never finished: " + eid)
		if Explore.has_method("is_found") and not Explore.is_found(eid):
			return _fail("exploration entry not recorded: " + eid)
		await _wait(0.5)
	return true


func _optional(explore_id: String) -> Node:
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.get("explore_id")) == explore_id:
			return it
	return null


## After an objective: run through any cinematic / level change until the player has control again
## (or the main menu is back after the finale).
func _settle(tag: String) -> void:
	var t := 0.0
	while t < 150.0:
		if Game.in_cinematic:
			await _wait(1.6)
			await _shoot("cinematic_after_" + tag)
			if skip_cine:
				await _tap(KEY_ESCAPE)
			var w := 0.0
			while Game.in_cinematic and w < 60.0:
				await _wait(0.2)
				w += 0.2
			continue
		if _gameplay_ready() or ui.get("main_menu").is_open:
			await _wait(0.4)
			if not Game.in_cinematic:
				return
		await _wait(0.2)
		t += 0.2
	_fail("game did not settle after " + tag)


# ------------------------------------------------------------------ side levels (parade plaza)
func _visit_side_level_keys() -> void:
	if not await _until(_gameplay_ready, 30.0):
		_fail("no control on the side level")
		return
	var lid := str(Game.level.level_id)
	await _shoot("side_" + lid)
	if Game.args.has("inputplay-explore"):
		await _explore_level(lid, true)
	var ex: Node = null
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.kind) == "exit":
			ex = it
	if ex == null:
		_fail("side level %s has no exit" % lid)
		return
	if not await _walk_to_focus(ex, 60.0):
		_fail("could not reach the exit of " + lid)
		return
	await _tap(KEY_E)
	if not await _until(func(): return not Game.side_level and _gameplay_ready(), 40.0):
		_fail("the exit of %s did not lead back" % lid)


# ------------------------------------------------------------------ exploration pass (§12, --inputplay-explore)
## Walks to EVERY optional find / chat of the level that has something new right now (nearest first), opens it
## with E and pages through it with Space exactly like a player, then checks that Explore recorded it. §12.9: the
## candidates are re-collected after every interaction, so entries unlocked by "requires" and the next entry of a
## chained hotspot (an NPC hosting several task steps) are visited too; each hotspot+entry pair is tried once.
## `final`: afterwards every side task of the level must be done.
func _explore_level(level_id: String, final := false) -> void:
	var done := 0
	var shots := 0
	var tried := {}
	var guard := 0
	while guard < 500:
		guard += 1
		var todo: Array = []
		for cand in Autoplay.pending_finds(get_tree().get_nodes_in_group("interactables"), Explore):
			if not tried.has("%d:%s" % [cand.get_instance_id(), cand.explore_id]):
				todo.append(cand)
		if todo.is_empty() or Game.player == null:
			break
		var from: Vector2 = Game.player.global_position
		todo.sort_custom(func(a, b): return a.global_position.distance_to(from) < b.global_position.distance_to(from))
		var it: Node = todo[0]
		var id := str(it.explore_id)
		tried["%d:%s" % [it.get_instance_id(), id]] = true
		if not await _walk_to_focus(it, 60.0):
			var near: Array = []
			for o in get_tree().get_nodes_in_group("interactables"):
				if is_instance_valid(o) and o.global_position.distance_to(Game.player.global_position) < 40.0:
					near.append("%s(%s,%s,active=%s)" % [o.name, o.get("kind"), o.get("explore_id"), o.is_active()])
			_fail("explore: could not get the prompt of %s in %s (player %s, target %s; locked=%s busy=%s paused=%s modal=%s player.focus=%s Game._focus=%s near=%s)" % [
				id, level_id, Game.player.global_position, it.global_position, Game.input_locked, Game.busy,
				get_tree().paused, ui.is_modal_open() if ui and ui.has_method("is_modal_open") else "?",
				Game.player.get("focus"), Game._focus, near])
			continue
		await _tap(KEY_E)
		if not await _until(func(): return Game.busy, 3.0):
			_fail("explore: E did not open " + id)
			continue
		if shots < 3:
			shots += 1
			await _wait(0.8)
			await _shoot("explore_" + id.replace(".", "_"))
		await _drain_interaction(id)
		if not Explore.is_found(id):
			_fail("explore: %s was not recorded as found" % id)
		done += 1
		await _wait(0.45)
	var finished := 0
	# a level file shared by several Story scenes files its finds and tasks under its first scene (C3P2_DESIGN §7)
	var key := str(Game.ext.level_key(level_id)) if Game.get("ext") != null and Game.ext.has_method("level_key") else level_id
	var tasks: Array = Explore.tasks_for(key) if Explore.has_method("tasks_for") else []
	for t in tasks:
		var st: Dictionary = Explore.task_state(str(t["id"]))
		if str(st["state"]) == "done":
			finished += 1
		elif final:
			_fail("explore: side task %s not completed in %s (%s, step %d)" % [t["id"], key, st["state"], st["step"]])
	var c: Dictionary = Explore.counts(key)
	print("INPUTPLAY explored %d finds in %s (Explore counts %s/%s, history %s, tasks %d/%d%s)" % [done, level_id,
		c.get("found", 0), c.get("total", 0), Explore.history_counts(), finished, tasks.size(),
		", final walk" if final else ""])


## Space through whatever the interaction opened (find pages, history cards, chat lines) until it is over.
func _drain_interaction(id: String) -> void:
	var t := 0.0
	var solved := {}
	while Game.busy and t < 90.0:
		# §12.8 mini-games solve themselves through synthetic key presses (demo_solve), exactly once each
		for mg in get_tree().get_nodes_in_group("minigame"):
			if is_instance_valid(mg) and mg.has_method("demo_solve") and not solved.has(mg.get_instance_id()):
				solved[mg.get_instance_id()] = true
				await mg.demo_solve()
		await _tap(KEY_SPACE)
		await _wait(0.35)
		t += 0.45
	if Game.busy:
		_fail("explore: interaction %s never finished" % id)


# ------------------------------------------------------------------ walking (held keys, like a player)
func _walk_to_focus(it: Node, timeout := 45.0) -> bool:
	var t := 0.0
	var stuck := 0.0
	var last := Vector2.INF
	var replans := 0
	var p: Node2D = Game.player
	if p == null:
		return false
	# oblique levels: route around props like a player would (grid BFS over the walkable area)
	var path: Array = [] if str(p.mode) == "side" else _plan_path(p.global_position, it.global_position + Vector2(0, 3))
	while t < timeout:
		_hold(KEY_SHIFT, true)                # run
		if Game._focus == it:
			break
		p = Game.player
		if p == null:
			break
		while not path.is_empty() and p.global_position.distance_to(path[0]) < 3.0:
			path.pop_front()
		var goal: Vector2
		if not path.is_empty():
			goal = path[0]
		else:
			var side := -1.0 if p.global_position.x < it.global_position.x else 1.0
			goal = it.global_position + Vector2(10.0 * side, 3.0)
			if p.global_position.distance_to(goal) < 5.0 and Game._focus != it:
				goal = it.global_position + Vector2(0, 2)   # a neighbouring find is nearer: stand right on this one
		var d := goal - p.global_position
		var want := {}
		if absf(d.x) > 1.5:
			want[KEY_D if d.x > 0.0 else KEY_A] = true
		if str(p.mode) != "side" and absf(d.y) > 1.5:
			want[KEY_S if d.y > 0.0 else KEY_W] = true
		for k in [KEY_A, KEY_D, KEY_W, KEY_S]:
			_hold(k, want.has(k))
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		if not want.is_empty() and p.global_position.distance_to(last) < 0.02:
			stuck += get_physics_process_delta_time()
			if stuck > 0.5 and replans < 6 and str(p.mode) != "side":
				replans += 1
				stuck = 0.0
				path = _plan_path(p.global_position, it.global_position + Vector2(0, 3))
		else:
			stuck = 0.0
		last = p.global_position
	_release_all()
	await _frames(4)
	return Game._focus == it


## Waypoints (world px) from `from` to the free cell nearest `to`: 4-px grid over the level's walkable polygon minus
## every prop collision polygon inflated by the player's radius, 8-neighbour BFS. Falls back to [to].
func _plan_path(from: Vector2, to: Vector2) -> Array:
	var lvl = Game.level
	var m = lvl.get("manifest") if lvl else null
	if not (m is Dictionary):
		return [to]
	var walk: Array = m.get("walkable", [])
	if walk.size() < 3:
		return [to]
	var poly := PackedVector2Array()
	for q in walk:
		poly.append(Vector2(float(q[0]), float(q[1])))
	var blocks: Array = []
	for pr in m.get("props", []):
		var c = pr.get("collision", []) if pr is Dictionary else []
		if c is Array and c.size() >= 3:
			var pp := PackedVector2Array()
			for q in c:
				pp.append(Vector2(float(q[0]), float(q[1])))
			for inflated in Geometry2D.offset_polygon(pp, 5.0):
				blocks.append(inflated)
	var r := Rect2(poly[0], Vector2.ZERO)
	for q in poly:
		r = r.expand(q)
	var cs := 4.0
	var w := int(r.size.x / cs) + 1
	var h := int(r.size.y / cs) + 1
	var free := PackedByteArray()
	free.resize(w * h)
	for gy in h:
		for gx in w:
			var pt := r.position + (Vector2(gx, gy) + Vector2(0.5, 0.5)) * cs
			var ok := Geometry2D.is_point_in_polygon(pt, poly)
			if ok:
				for b in blocks:
					if Geometry2D.is_point_in_polygon(pt, b):
						ok = false
						break
			free[gy * w + gx] = 1 if ok else 0
	var start := Vector2i(clampi(int((from.x - r.position.x) / cs), 0, w - 1), clampi(int((from.y - r.position.y) / cs), 0, h - 1))
	var goal := Vector2i(clampi(int((to.x - r.position.x) / cs), 0, w - 1), clampi(int((to.y - r.position.y) / cs), 0, h - 1))
	if free[goal.y * w + goal.x] == 0:
		var best := goal
		var bd := 1e9
		for gy in h:
			for gx in w:
				if free[gy * w + gx] == 1:
					var dd := Vector2(gx - goal.x, (gy - goal.y) * 1.6).length()
					if dd < bd:
						bd = dd
						best = Vector2i(gx, gy)
		goal = best
	var prev := {start: start}
	var queue: Array = [start]
	var head := 0
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
		Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]
	while head < queue.size():
		var cur: Vector2i = queue[head]
		head += 1
		if cur == goal:
			break
		for dv in dirs:
			var n: Vector2i = cur + dv
			if n.x < 0 or n.y < 0 or n.x >= w or n.y >= h or prev.has(n) or free[n.y * w + n.x] == 0:
				continue
			prev[n] = cur
			queue.append(n)
	if not prev.has(goal):
		return [to]
	var path: Array = []
	var c2: Vector2i = goal
	while c2 != start:
		path.push_front(r.position + (Vector2(c2) + Vector2(0.5, 0.5)) * cs)
		c2 = prev[c2]
	return path


func _gameplay_ready() -> bool:
	return Game.level != null and is_instance_valid(Game.level) and Game.player != null \
		and is_instance_valid(Game.player) and not Game.busy and not Game.in_cinematic and not Game.input_locked \
		and not get_tree().paused and Game._fade.color.a < 0.05


func _interactable(oid: String) -> Node:
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.objective_id) == oid:
			return it
	return null


# ------------------------------------------------------------------ input + timing helpers
func _key(k: int, down: bool) -> void:
	var ev := InputEventKey.new()
	ev.set("keycode", k)
	ev.set("physical_keycode", k)
	ev.pressed = down
	Input.parse_input_event(ev)


func _hold(k: int, down: bool) -> void:
	# Re-assert held keys every call: if the window loses focus, Godot releases all pressed keys
	# (Input.release_pressed_events), exactly as it would for a real player.
	if bool(_held.get(k, false)) == down and (not down or Input.is_physical_key_pressed(k) or Input.is_key_pressed(k)):
		return
	_held[k] = down
	_key(k, down)


func _release_all() -> void:
	for k in _held.keys():
		_hold(k, false)


func _tap(k: int) -> void:
	_key(k, true)
	await _frames(2)
	_key(k, false)
	await _frames(2)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func _until(cond: Callable, timeout: float) -> bool:
	var t := 0.0
	while t < timeout:
		if cond.call():
			return true
		await get_tree().process_frame
		t += get_process_delta_time()
	return bool(cond.call())


func _fail(msg: String) -> bool:
	failures.append(msg)
	push_error("INPUTPLAY " + msg)
	return false


func _shoot(tag: String) -> void:
	if shots_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	_shot += 1
	get_viewport().get_texture().get_image().save_png("%s/%02d_%s.png" % [shots_dir, _shot, tag])
