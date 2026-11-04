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
## values choose c3a_choose / c3b_choose. "Fortsetzen" must resume before the last decision (c3b_choose).

const A1 := ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger",
	"a1_choose"]
const M1 := ["m1_inspect_plan_a", "m1_inspect_plan_b", "m1_align_plans", "m1_talk_emil", "m1_choose"]
const C3A := ["c3a_talk_conductor", "c3a_inspect_weighbill", "c3a_inspect_departures", "c3a_pass_control",
	"c3a_talk_elena", "c3a_choose"]
const C3B := ["c3b_arrival", "c3b_inspect_seating", "c3b_inspect_log", "c3b_solve_protocol", "c3b_inspect_booth",
	"c3b_talk_alexei", "c3b_choose"]

var choices := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence", "c3a_choose": "ask_elena",
	"c3b_choose": "share_protocol"}
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
	skip_cine = do_skip
	shots_dir = shots


func run() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	ui = Game.ui
	# Isolate the test from the real mouse: the fullscreen window would otherwise receive hover events from
	# whoever is using the computer (hovering a menu button moves the focus). Mouse events now pass through.
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mouse_passthrough(PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)]))
	print("INPUTPLAY start choices=", choices, " skip=", skip_cine)
	var t0 := Time.get_ticks_msec()
	if ui == null:
		_fail("no UI loaded")
		_finish(t0)
		return
	if await _menu_new_game() and await _intro() and await _menus_in_game() \
			and await _play_route(A1, "L_A1_Railyard") and await _play_route(M1, "L_M1_Archive") \
			and await _explore_sample() and await _play_route(C3A, "L_C3_Station") \
			and await _play_route(C3B, "L_C3_Hall") and await _ending():
		await _continue_from_menu()
	_finish(t0)


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


func _play_route(route: Array, level_id: String) -> bool:
	if not await _until(func(): return _gameplay_ready() and str(Game.level.level_id) == level_id, 90.0):
		return _fail("never got control in " + level_id)
	for oid in route:
		if not await _until(func(): return Story.is_available(oid) and _gameplay_ready(), 30.0):
			return _fail("objective never available: " + oid)
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
				else:
					await _blueprint_puzzle()
		if not await _until(func(): return not Game.busy, 20.0):
			return _fail("interaction never finished: " + oid)
		if Story.objective_state(oid) != "complete":
			return _fail("objective not complete after real input: " + oid)
		await _settle(oid)
		if not failures.is_empty():
			return false
	return true


func _ending() -> bool:
	var mm: Node = ui.get("main_menu")
	if not await _until(func(): return mm.is_open, 120.0):
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
	if str(Game.level.level_id) != "L_C3_Hall" or Story.objective_state("c3b_choose") != "available":
		_fail("'Fortsetzen' resumed at %s (c3b_choose %s), expected the last playable autosave" % [
			Game.level.level_id, Story.objective_state("c3b_choose")])
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
			if oid == "a1_choose" or oid == "c3a_choose":    # arrow keys + Enter
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
		await _dialogue(eid, "")
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


# ------------------------------------------------------------------ walking (held keys, like a player)
func _walk_to_focus(it: Node, timeout := 45.0) -> bool:
	var t := 0.0
	var stuck := 0.0
	var detour := 0.0
	var detour_key := KEY_W
	var last := Vector2.INF
	while t < timeout:
		_hold(KEY_SHIFT, true)                # run
		if Game._focus == it:
			break
		var p: Node2D = Game.player
		if p == null:
			break
		var side := -1.0 if p.global_position.x < it.global_position.x else 1.0
		var goal: Vector2 = it.global_position + Vector2(10.0 * side, 3.0)
		var d := goal - p.global_position
		var want := {}
		if absf(d.x) > 2.0:
			want[KEY_D if d.x > 0.0 else KEY_A] = true
		if str(p.mode) != "side":
			if detour > 0.0:
				want[detour_key] = true
				detour -= get_physics_process_delta_time()
			elif absf(d.y) > 2.0:
				want[KEY_S if d.y > 0.0 else KEY_W] = true
		for k in [KEY_A, KEY_D, KEY_W, KEY_S]:
			_hold(k, want.has(k))
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		if not want.is_empty() and p.global_position.distance_to(last) < 0.02:
			stuck += get_physics_process_delta_time()
			if stuck > 0.35:                  # blocked by a prop: step around it
				detour = 0.7
				detour_key = KEY_S if detour_key == KEY_W else KEY_W
				stuck = 0.0
		else:
			stuck = 0.0
		last = p.global_position
	_release_all()
	await _frames(4)
	return Game._focus == it


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
