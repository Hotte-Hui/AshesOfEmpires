extends Node
## Memories E2E helpers (TECHNICAL_ARCHITECTURE §12.10) for the end-to-end drivers and a self-contained check run.
##  * autoplay(driver)  — Story-API driver (scripts/core/autoplay.gd, flag --autoplay-memories): opens the
##                        MemoryView, travels into the first completed scene, finds one exploration entry there,
##                        replays one story hotspot (read-only), returns and asserts that Story is byte-identical,
##                        the present (level, position, side-level flag) is back, the find was kept, no save was
##                        written inside and the return autosave exists.
##  * inputplay(driver) — the same through synthetic key presses only (scripts/core/inputplay.gd,
##                        --inputplay-memories): Esc → „Erinnerungen“ → card → Enter, walking (the driver's grid
##                        path-finder), E, Space, Esc → „In die Gegenwart zurückkehren“.
##  * demo(mode, shots) — `godot --path . -- --memory-demo=game|menu|all [--memory-shots=DIR]`: private save
##                        folder and profile (user://memdemo), plays A1+M1 through the Story API, then runs both
##                        trips (from the game and from the main menu) with screenshots of every stage; prints
##                        MEMDEMO_PASS / MEMDEMO_FAIL and quits (0 / 1). Never touches the player's saves.
##                        Films: no control until the present has faded back in; from the main menu (fresh Story
##                        state) a film plays with the decisions recorded in the profile.
## All helpers return true when every check held; failures are collected in `failures` (also push_error).

const ENGINE := preload("res://scripts/story/story_engine.gd")

var failures: Array = []
var shots_dir := ""
var _shot := 0
var _held: Dictionary = {}


func _fail(msg: String) -> bool:
	failures.append(msg)
	push_error("MEMORIES " + msg)
	return false


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


func _shoot(tag: String) -> void:
	if shots_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	_shot += 1
	get_viewport().get_texture().get_image().save_png("%s/mem_%02d_%s.png" % [shots_dir, _shot, tag])


func _key(k: int, down: bool) -> void:
	var ev := InputEventKey.new()
	ev.set("keycode", k)
	ev.set("physical_keycode", k)
	ev.pressed = down
	Input.parse_input_event(ev)


func _tap(k: int) -> void:
	_key(k, true)
	await _frames(2)
	_key(k, false)
	await _frames(2)


func _free_play() -> bool:
	return Game.level != null and is_instance_valid(Game.level) and Game.player != null \
		and is_instance_valid(Game.player) and not Game.busy and not Game.in_cinematic and not Game.input_locked \
		and not Game.memory_travelling and not get_tree().paused


# ------------------------------------------------------------------ shared pieces
## The present as the checks compare it.
func present_state() -> Dictionary:
	return {"story": Story.save_json(), "level": str(Game.level.get("level_id")) if Game.level else "",
		"pos": Game.player.position if Game.player else Vector2.ZERO, "side": Game.side_level,
		"auto_t": float(Saves.slot_info("auto").get("timestamp", 0.0)) if Saves.has_method("slot_info") else 0.0}


## First memory the MemoryView offers (unlocked, not the scene the player stands in).
func first_target(context := "game") -> String:
	for c in Game.memory_scenes(context):
		if bool(c.get("unlocked", false)) and not bool(c.get("current", false)):
			return str(c["id"])
	return ""


## An exploration hotspot of the memory level not found yet (no mini-game), else any discover hotspot.
func pick_find() -> Node:
	var any: Node = null
	for it in get_tree().get_nodes_in_group("interactables"):
		if not it.is_inside_tree() or not Game.level.is_ancestor_of(it) or str(it.kind) != "discover" or not it.is_active():
			continue
		var id := str(it.explore_id)
		if id == "" or str(Explore.entry(id).get("minigame", "")) != "":
			continue
		if not Explore.is_found(id):
			return it
		if any == null:
			any = it
	return any


## The read-only twin of a story hotspot (prefer one of `kind`: dialogue / inspect / choice / puzzle).
func pick_twin(kind := "dialogue") -> Node:
	var any: Node = null
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and it.has_meta("memory_objectives") and Game.level.is_ancestor_of(it):
			if str(it.get_meta("memory_kind", "")) == kind:
				return it
			if any == null:
				any = it
	return any


func _place_near(it: Node) -> void:
	var p = Game.player
	if p == null:
		return
	p.position = it.global_position + Vector2(-14, 2)
	if str(p.mode) == "side":
		p.position.y = p.floor_y
	Game.camera.snap_now()


## Checks that hold inside every memory.
func check_inside(target: String) -> void:
	if not Game.memory_mode or Game.memory_scene != target:
		_fail("not inside the memory of %s (mode %s, scene %s)" % [target, Game.memory_mode, Game.memory_scene])
	if Game.level == null or str(Game.level.get("level_id")) != target:
		_fail("memory level is %s, expected %s" % [Game.level.get("level_id") if Game.level else "none", target])
	var who := str(Game.memories.scene(target).get("protagonist", ""))
	if Game.player != null and who != "" and str(Game.player.char_id) != who:
		_fail("memory of %s is played by %s, expected %s" % [target, Game.player.char_id, who])
	var hud = Game.ui.get("hud") if Game.ui else null
	if hud != null and hud.has_method("is_memory_badge_visible") and not hud.is_memory_badge_visible():
		_fail("HUD badge ERINNERUNG not visible inside the memory")
	var t0 := float(Saves.slot_info("1").get("timestamp", 0.0))
	var r: Dictionary = Saves.save("1")
	var why: String = Game.save_block_key()   # sys.save.err.memory (or …memory_menu from the main menu)
	if r.get("ok", false) or not why.begins_with("sys.save.err.memory") or str(r.get("error_key", "")) != why:
		_fail("manual save inside a memory was not refused: " + str(r))
	if float(Saves.slot_info("1").get("timestamp", 0.0)) != t0:
		_fail("slot 1 changed inside a memory")
	var a0 := float(Saves.slot_info("auto").get("timestamp", 0.0))
	Game.autosave("memory_check")
	if float(Saves.slot_info("auto").get("timestamp", 0.0)) != a0:
		_fail("autosave written inside a memory")
	# photo mode works inside a memory (and keeps the memory grade as its base)
	var photo = Game.ui.get("photo") if Game.ui else null
	if photo != null and _free_play():
		if not Game.ui.open_photo():
			_fail("photo mode does not open inside a memory")
		else:
			photo.close()
	if Game.memory_twins().is_empty() and not bool(Game.memories.scene(target).get("side", false)):
		_fail("no read-only story hotspots inside the memory of " + target)   # side levels have none
	# every twin is reachable: no active optional hotspot stands on it (it would always win the prompt)
	for tw in Game.memory_twins():
		for it in get_tree().get_nodes_in_group("interactables"):
			if it != tw and it.is_inside_tree() and Game.level.is_ancestor_of(it) and it.is_active() \
					and not it.has_meta("memory_objectives") and it.global_position.distance_to(tw.global_position) < 10.0:
				_fail("twin %s is covered by %s in %s" % [tw.name, it.name, target])


## Checks after the return to the present.
func check_returned(before: Dictionary, found_id: String) -> void:
	if Game.memory_mode:
		_fail("still in memory mode after the return")
	if Story.save_json() != str(before["story"]):
		_fail("Story state differs after the memory round trip")
	if Game.level == null or str(Game.level.get("level_id")) != str(before["level"]):
		_fail("returned to %s, expected %s" % [Game.level.get("level_id") if Game.level else "none", before["level"]])
	elif Game.player != null and Game.player.position.distance_to(before["pos"]) > 1.5:
		_fail("player at %s after the return, expected %s" % [Game.player.position, before["pos"]])
	if Game.side_level != bool(before["side"]):
		_fail("side_level %s after the return, expected %s" % [Game.side_level, before["side"]])
	if found_id != "" and not Explore.is_found(found_id):
		_fail("find %s made inside the memory was not kept" % found_id)
	var hud = Game.ui.get("hud") if Game.ui else null
	if hud != null and hud.has_method("is_memory_badge_visible") and hud.is_memory_badge_visible():
		_fail("HUD badge still visible in the present")
	var info: Dictionary = Saves.slot_info("auto")
	if float(info.get("timestamp", 0.0)) <= float(before["auto_t"]) or str(info.get("label", "")) != "memory_return":
		_fail("no autosave after the return (finds of the memory would be lost): " + str(info.get("label", "")))


# ------------------------------------------------------------------ Story-API driver hook (autoplay.gd)
func autoplay(_driver: Node = null) -> bool:
	var n0 := failures.size()
	if not await _until(_free_play, 30.0):
		return _fail("autoplay: no free play before the memory trip")
	var target := first_target("game")
	if target == "":
		return _fail("autoplay: no completed scene to remember in " + str(Game.level.get("level_id")))
	var before := present_state()
	Game.ui.open_memories("game")
	var view = Game.ui.get("memories")
	if view == null or not view.is_open:
		return _fail("autoplay: MemoryView did not open")
	if not view.buttons.has(target):
		return _fail("autoplay: no card for " + target)
	view.activate(target)
	if not await _until(func(): return Game.memory_mode and _free_play(), 30.0):
		return _fail("autoplay: the trip into %s never finished" % target)
	check_inside(target)
	var found_id := ""
	var fi := pick_find()
	if fi != null:
		found_id = str(fi.explore_id)
		_place_near(fi)
		await Game.interact(fi)
		if not Explore.is_found(found_id):
			_fail("autoplay: find %s not recorded inside the memory" % found_id)
	for kind in ["dialogue", "inspect", "choice", "puzzle"]:
		var tw := pick_twin(kind)
		if tw != null and str(tw.get_meta("memory_kind", "")) == kind:
			_place_near(tw)
			await Game.interact(tw)
			if Story.save_json() != str(before["story"]):
				_fail("autoplay: replaying a %s hotspot changed the Story state" % kind)
	await Game.return_from_memory()
	if not await _until(func(): return not Game.memory_mode and _free_play(), 30.0):
		return _fail("autoplay: the return from %s never finished" % target)
	check_returned(before, found_id)
	print("MEMORIES autoplay: %s → %s → %s, find %s, %s" % [before["level"], target, Game.level.get("level_id"),
		found_id, "ok" if failures.size() == n0 else "FAILED"])
	return failures.size() == n0


# ------------------------------------------------------------------ real-input driver hook (inputplay.gd)
## `driver` provides _tap(key), _until(cond, t), _wait(t), _walk_to_focus(node[, t]), _drain_interaction(id),
## _gameplay_ready() and _shoot(tag) (scripts/core/inputplay.gd).
func inputplay(driver: Node) -> bool:
	var n0 := failures.size()
	if not await driver._until(driver._gameplay_ready, 60.0):
		return _fail("inputplay: no control before the memory trip")
	var target := first_target("game")
	if target == "":
		return _fail("inputplay: no completed scene to remember")
	var before := present_state()
	var pm: Node = Game.ui.get("pause_menu")
	var view: Node = Game.ui.get("memories")
	await driver._tap(KEY_ESCAPE)
	if not await driver._until(func(): return pm.is_open, 3.0):
		return _fail("inputplay: Esc did not open the pause menu")
	var entry: Control = pm._buttons["memories"]
	for i in 10:
		if get_viewport().gui_get_focus_owner() == entry:
			break
		await driver._tap(KEY_DOWN)
	if get_viewport().gui_get_focus_owner() != entry:
		return _fail("inputplay: could not focus „Erinnerungen“ with the arrow keys")
	await driver._tap(KEY_ENTER)
	if not await driver._until(func(): return view.is_open, 3.0):
		return _fail("inputplay: Enter did not open the MemoryView")
	await driver._wait(0.6)
	await driver._shoot("memories_view")
	for i in 8:
		if view.selected() == target:
			break
		await driver._tap(KEY_RIGHT)
	if view.selected() != target:
		return _fail("inputplay: could not select the card %s (selected %s)" % [target, view.selected()])
	await driver._tap(KEY_ENTER)
	if not await driver._until(func(): return Game.memory_mode and driver._gameplay_ready(), 40.0):
		return _fail("inputplay: the trip into %s never finished" % target)
	await driver._shoot("memory_" + target)
	check_inside(target)
	var found_id := ""
	var fi := pick_find()
	if fi != null:
		found_id = str(fi.explore_id)
		if not await driver._walk_to_focus(fi, 60.0):
			_fail("inputplay: could not walk to the find %s inside the memory" % found_id)
		else:
			# right after the arrival the 350 ms input cooldown swallows E (as for a player): wait it out, retry once
			await driver._until(func(): return Time.get_ticks_msec() >= Game.interact_ready_at, 2.0)
			await driver._tap(KEY_E)
			if not await driver._until(func(): return Game.busy, 3.0):
				await driver._tap(KEY_E)
			await driver._drain_interaction(found_id)
			if not Explore.is_found(found_id):
				_fail("inputplay: find %s not recorded inside the memory" % found_id)
	var tw := pick_twin("dialogue")
	if tw != null:
		if await driver._walk_to_focus(tw, 60.0):
			await driver._until(func(): return Time.get_ticks_msec() >= Game.interact_ready_at, 2.0)
			await driver._tap(KEY_E)
			if not await driver._until(func(): return Game.busy, 3.0):
				_fail("inputplay: E did not start the remembered conversation")
			await driver._shoot("memory_dialogue")
			await driver._drain_interaction("memory twin")
			if Story.save_json() != str(before["story"]):
				_fail("inputplay: the remembered conversation changed the Story state")
		else:
			_fail("inputplay: could not walk to the remembered conversation")
	if not await driver._until(driver._gameplay_ready, 10.0):
		return _fail("inputplay: no control inside the memory after the interactions")
	await driver._tap(KEY_ESCAPE)
	if not await driver._until(func(): return pm.is_open, 3.0):
		return _fail("inputplay: Esc did not open the pause menu inside the memory")
	if str((entry as Button).text) != Loc.t("ui.memories.pause.return"):
		_fail("inputplay: the pause menu offers „%s“ instead of the return" % (entry as Button).text)
	await driver._shoot("memory_pause")
	for i in 10:
		if get_viewport().gui_get_focus_owner() == entry:
			break
		await driver._tap(KEY_DOWN)
	await driver._tap(KEY_ENTER)
	if not await driver._until(func(): return not Game.memory_mode and driver._gameplay_ready(), 40.0):
		return _fail("inputplay: the return from %s never finished" % target)
	await driver._shoot("memory_returned")
	check_returned(before, found_id)
	print("MEMORIES inputplay: %s → %s → back, find %s, %s" % [before["level"], target, found_id,
		"ok" if failures.size() == n0 else "FAILED"])
	return failures.size() == n0


# ------------------------------------------------------------------ self-contained check run (--memory-demo)
func demo(mode := "all", shots := "") -> void:
	shots_dir = shots
	if shots_dir != "":
		DirAccess.make_dir_recursive_absolute(shots_dir)
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func() -> void:
		print("MEMDEMO_FAIL watchdog: gave up after 300 s")
		get_tree().quit(3))
	# private saves + profile: the player's files are never touched
	Saves.base_dir = "user://memdemo/saves"
	for s in ["1", "2", "3", "auto", "quick"]:
		Saves.delete(s)
	Game.memories.path = "user://memdemo/profile.json"
	Game.memories.clear()
	Game.args["profile"] = Game.memories.path
	Game.memories.save_profile()
	Story.new_game()
	Explore.reset()
	var kit = load("res://tests/support/test_kit.gd").new()
	var drain := func() -> void:
		for seq in Story.pending_cinematics():
			Story.consume_cinematic(seq, true)
	kit.play_a1(Story, "share_with_irina", drain)
	kit.play_m1(Story, "preserve_evidence", drain)
	drain.call()
	if not Game.memories.unlocked_by_profile("L_A1_Railyard") or not Game.memories.unlocked_by_profile("L_M1_Plaza"):
		_fail("demo: completing A1/M1 did not record them in the profile")
	await Game.goto_level(Game._story_scene(), "", false)
	if not await _until(_free_play, 30.0):
		_fail("demo: no free play in " + Game._story_scene())
		_demo_finish()
		return
	await _wait(1.0)
	await _shoot("present")
	if mode == "view":            # the MemoryView only: 100 %, 150 % text, high contrast, main-menu context
		await _demo_view_variants()
		_demo_finish()
		return
	if mode == "quit":            # leaving a memory through „Hauptmenü“ and through „Laden“
		await _demo_quit_paths()
		_demo_finish()
		return
	if mode == "drivers":         # the E2E hooks themselves: autoplay(), then inputplay() with the real key driver
		Game.auto = true             # as scripts/core/autoplay.gd sets it (panels close themselves)
		if not await autoplay(null):
			_fail("demo drivers: autoplay hook failed")
		Game.auto = false
		var ip: Node = load("res://scripts/core/inputplay.gd").new()
		add_child(ip)
		ip.set("ui", Game.ui)
		ip.process_mode = Node.PROCESS_MODE_ALWAYS
		if not await inputplay(ip):
			_fail("demo drivers: inputplay hook failed")
		for f in ip.get("failures"):
			_fail("inputplay driver: " + str(f))
		ip.queue_free()
		_demo_finish()
		return
	if mode in ["game", "all"]:
		await _demo_game_trip()
	if mode in ["films", "all"]:
		for cid in ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains"]:
			await _demo_film(cid)
	if mode in ["c3", "all"]:
		# on to the palace (Konrad); the station (Alexei) becomes a memory: protagonist switch inside the trip
		kit.play_c3a(Story, "ask_elena")
		drain.call()
		await Game.goto_level(Game._story_scene(), "", false)
		if not await _until(_free_play, 30.0):
			_fail("demo: no free play in " + Game._story_scene())
		else:
			await _demo_trip("L_C3_Station", ["dialogue", "inspect", "choice"], "c3")
	if mode in ["menu", "all"]:
		await _demo_menu_trip("L_M1_Plaza")
	if mode == "all":
		# the whole chain done (as after the finale): the palace is only reachable as a memory from the main menu
		kit.play_c3b(Story, "share_protocol")
		drain.call()
		Story.finale(true)
		await _demo_menu_trip("L_C3_Hall")
		# as after a fresh start of the game: the menu's Story state knows no decisions at all
		Story.new_game()
		Explore.reset()
		await _demo_menu_film("LS_C3_Close")
	_demo_finish()


## A film watched again from the main menu: the menu's Story and Explore states stay as they were.
func _demo_menu_film(cid: String) -> void:
	var before_story := Story.save_json()
	var before_explore: Dictionary = Explore.state()
	Game.ui.open_memories("menu")
	var view = Game.ui.get("memories")
	view.show_page("films")
	await _wait(0.6)
	if not view.select(cid):
		_fail("demo: film %s not offered in the main menu" % cid)
		Game.ui.close_all()
		Game.ui.show_main_menu()
		return
	await _shoot("menu_films")
	view.activate(cid)
	if not await _until(func(): return Game.in_cinematic and Game._fade.color.a < 0.5, 20.0):
		_fail("demo: film %s did not start from the menu" % cid)
	# it plays with the decisions of the playthrough in which it was seen (profile), not with the menu's state
	# (memory_mode is set once the screen is black and the recorded state is in place, right before the film)
	await _until(func(): return Game.memory_mode or not Game.memory_travelling, 10.0)
	var then: Dictionary = ENGINE.json_parse(Game._film_snapshot(cid))
	if not then.get("ok", false) or not (then["value"] is Dictionary):
		_fail("demo: no recorded Story state for the film %s" % cid)
	elif Story.choice_history() != (then["value"] as Dictionary).get("choice_history", {}):
		_fail("demo: film %s from the menu plays with %s instead of the recorded decisions" % [cid,
			Story.choice_history()])
	await _wait(3.0)
	await _shoot("menu_film_" + cid)
	await _tap(KEY_ESCAPE)
	var mm = Game.ui.get("main_menu")
	if not await _until(func(): return mm.is_open and not Game.memory_travelling, 40.0):
		_fail("demo: the main menu did not come back after the film")
		return
	if Story.save_json() != before_story or Explore.state() != before_explore:
		_fail("demo: watching a film from the main menu changed the menu's state")


func _demo_finish() -> void:
	if failures.is_empty():
		print("MEMDEMO_PASS shots=%d" % _shot)
		get_tree().quit(0)
	else:
		for f in failures:
			print("MEMDEMO_FAIL ", f)
		get_tree().quit(1)


## Answers whatever the interaction opened (lines with Space, documents with Esc) and shoots the first frame.
func _drive_interaction(tag: String) -> void:
	var shot := false
	var t := 0.0
	while Game.busy and t < 60.0:
		await _wait(0.9)
		t += 0.9
		if not shot:
			shot = true
			await _shoot(tag)
		var insp = Game.ui.get("inspect")
		if insp != null and insp.is_open:
			await _tap(KEY_ESCAPE)
		else:
			await _tap(KEY_SPACE)
			await _wait(0.15)
			await _tap(KEY_SPACE)


## „Hauptmenü“ inside a memory leaves the present autosave as it was and the present Story state in place;
## „Fortsetzen“ then resumes the present. „Laden“ inside a memory ends memory mode and the save becomes the present.
func _demo_quit_paths() -> void:
	var before := present_state()
	var auto0: Dictionary = Saves.slot_info("auto")
	Game.ui.open_pause()
	Game.ui.open_memories("game")
	Game.ui.get("memories").activate("L_M1_Archive")
	if not await _until(func(): return Game.memory_mode and _free_play(), 30.0):
		_fail("demo quit: no memory of the archive")
		return
	await _wait(0.8)
	Game.ui.open_pause()
	await _wait(0.4)
	Game.ui.pause_menu._main_menu()        # asks for confirmation first
	await _wait(0.6)
	await _shoot("quit_confirm")
	if not Game.ui.confirm.is_open:
		_fail("demo quit: „Hauptmenü“ did not ask for confirmation")
	elif not Kit_has_text(Game.ui.confirm._msg.text, "ui.memories.confirm_menu"):
		_fail("demo quit: the confirmation does not warn about the finds of the visit")
	Game.ui.confirm._answer(true)
	if not await _until(func(): return Game.ui.get("main_menu").is_open and not Game.memory_mode, 20.0):
		_fail("demo quit: „Hauptmenü“ inside a memory did not reach the main menu")
		return
	await _wait(0.8)
	await _shoot("quit_main_menu")
	if Story.save_json() != str(before["story"]):
		_fail("demo quit: the Story state after „Hauptmenü“ is not the present one")
	var auto1: Dictionary = Saves.slot_info("auto")
	if float(auto1.get("timestamp", 0.0)) != float(auto0.get("timestamp", 0.0)):
		_fail("demo quit: the present autosave was rewritten by leaving a memory")
	Game._on_continue()
	if not await _until(func(): return _free_play() and str(Game.level.get("level_id")) == str(before["level"]), 30.0):
		_fail("demo quit: „Fortsetzen“ did not resume the present")
		return
	await _wait(0.6)
	await _shoot("quit_continued")
	# „Laden“ inside a memory
	Game.ui.open_pause()
	Game.ui.open_memories("game")
	Game.ui.get("memories").activate("L_A1_Railyard")
	if not await _until(func(): return Game.memory_mode and _free_play(), 30.0):
		_fail("demo quit: no memory of Karsk")
		return
	await _wait(0.6)
	Game._on_load_slot("auto")
	if not await _until(func(): return _free_play() and not Game.memory_mode and str(Game.level.get("level_id")) == str(before["level"]), 30.0):
		_fail("demo quit: loading inside a memory did not end in the loaded present")
		return
	await _wait(0.6)
	await _shoot("quit_loaded")
	var hud = Game.ui.get("hud")
	if hud.is_memory_badge_visible():
		_fail("demo quit: badge left over after loading")
	if Story.save_json() != str(before["story"]):
		_fail("demo quit: loaded state differs from the autosaved present")


func Kit_has_text(shown: String, key: String) -> bool:
	return shown == Loc.t(key)


func _setting(key: String, value) -> void:
	Settings.values[key] = value
	if Settings.has_signal("changed"):
		Settings.changed.emit(key, value)


func _demo_view_variants() -> void:
	var view = Game.ui.get("memories")
	Game.ui.open_pause()
	Game.ui.open_memories("game")
	await _wait(0.7)
	await _shoot("view_100")
	# runtime only (Settings.values + changed signal): the player's settings file is never written
	var keep_scale = Settings.get_value("text_scale")
	var keep_hc = Settings.get_value("high_contrast")
	_setting("text_scale", 1.5)
	await _wait(0.5)
	await _shoot("view_150")
	_setting("text_scale", keep_scale)
	_setting("high_contrast", true)
	await _wait(0.5)
	await _shoot("view_hc")
	_setting("high_contrast", keep_hc)
	await _wait(0.3)
	view.close()
	Game.ui.close_all()
	await _wait(0.3)
	await Game.show_main_menu()
	await _wait(1.0)
	Game.ui.open_memories("menu")
	await _wait(0.7)
	await _shoot("view_menu")
	if view.buttons.is_empty():
		_fail("demo: no selectable memory from the main menu")


## Watches a seen film again from the present (page „Filmsequenzen“), skips it after a few seconds with Esc and
## checks that the present comes back unchanged.
func _demo_film(cid: String) -> void:
	var before := present_state()
	Game.ui.open_pause()
	Game.ui.open_memories("game")
	var view = Game.ui.get("memories")
	view.show_page("films")
	await _wait(0.6)
	if not view.select(cid):
		_fail("demo: film %s not offered" % cid)
		Game.ui.close_all()
		return
	await _wait(0.3)
	await _shoot("films_" + cid)
	view.activate(cid)
	if not await _until(func(): return Game.in_cinematic and Game._fade.color.a < 0.5, 20.0):
		_fail("demo: film %s did not start" % cid)
	await _wait(3.5)
	await _shoot("film_" + cid)
	await _tap(KEY_ESCAPE)
	# the present reloads behind the fade: no walking, interacting or pausing until it is completely back
	await _until(func(): return not Game.memory_travelling or (Game.level != null and Game.player != null), 30.0)
	if Game.memory_travelling and (not Game.input_locked or not Game.in_cinematic):
		_fail("demo: control came back before the present had faded in after %s" % cid)
	if not await _until(func(): return not Game.memory_travelling and _free_play(), 60.0):
		_fail("demo: no control after the film %s" % cid)
		return
	await _wait(0.8)
	await _shoot("after_film_" + cid)
	if Story.save_json() != str(before["story"]):
		_fail("demo: watching %s changed the Story state" % cid)
	if Game.level == null or str(Game.level.get("level_id")) != str(before["level"]):
		_fail("demo: after %s the level is %s" % [cid, Game.level.get("level_id") if Game.level else "none"])
	elif Game.player.position.distance_to(before["pos"]) > 1.5:
		_fail("demo: after %s the player stands at %s, expected %s" % [cid, Game.player.position, before["pos"]])
	if Game.memory_mode or Game.side_level != bool(before["side"]):
		_fail("demo: memory/side-level state wrong after %s" % cid)


func _demo_game_trip() -> void:
	Game.ui.open_pause()
	await _wait(0.5)
	await _shoot("pause_present")
	await _demo_trip("L_A1_Railyard", ["dialogue", "inspect", "puzzle"], "a1", true)


## One trip from the present into `target`: MemoryView, transition, the twins of `kinds`, one find, (menus),
## return; screenshots of every stage, checks inside and after the return.
func _demo_trip(target: String, kinds: Array, tag: String, menus := false) -> void:
	var before := present_state()
	if not Game.ui.is_open(Game.ui.pause_menu):
		Game.ui.open_pause()
	Game.ui.open_memories("game")
	var view = Game.ui.get("memories")
	await _wait(0.6)
	if not view.select(target):
		_fail("demo: card %s not selectable from %s" % [target, before["level"]])
		Game.ui.close_all()
		return
	await _wait(0.3)
	await _shoot("view_" + tag)
	view.activate(target)
	await _wait(0.9)
	await _shoot("drain_" + tag)
	await _until(func(): return Game._mem_card != null and Game._mem_card.visible and Game._mem_card.modulate.a > 0.95, 10.0)
	await _shoot("card_" + tag)
	if not await _until(func(): return Game.memory_mode and _free_play(), 30.0):
		_fail("demo: the trip into %s never finished" % target)
		return
	await _wait(1.6)
	await _shoot("arrived_" + tag)
	check_inside(target)
	for kind in kinds:
		var tw := pick_twin(kind)
		if tw == null or str(tw.get_meta("memory_kind", "")) != kind:
			if kind != "choice":   # a choice taken with a person is part of that person's conversation twin
				_fail("demo: no %s twin in the memory of %s" % [kind, target])
			continue
		_place_near(tw)
		await _wait(0.4)
		await _shoot("prompt_%s_%s" % [tag, kind])
		Game.interact(tw)
		await _drive_interaction("twin_%s_%s" % [tag, kind])
		if Story.save_json() != str(before["story"]):
			_fail("demo: the %s twin changed the Story state" % kind)
	var fi := pick_find()
	var found_id := ""
	if fi != null:
		found_id = str(fi.explore_id)
		_place_near(fi)
		Game.interact(fi)
		await _drive_interaction("find_" + tag)
	if menus:
		Game.ui.open_pause()
		await _wait(0.5)
		await _shoot("pause_in_memory")
		Game.ui.open_saveload("save", true)
		await _wait(0.5)
		await _shoot("save_blocked")
		Game.ui.close_all()
		await _wait(0.3)
	Game.return_from_memory()
	await _wait(1.0)
	await _shoot("return_drain_" + tag)
	await _until(func(): return Game._mem_card != null and Game._mem_card.visible and Game._mem_card.modulate.a > 0.95, 10.0)
	await _shoot("return_card_" + tag)
	await _until(func(): return not Game._mem_card.visible, 10.0)
	await _wait(0.5)
	await _shoot("return_colour_" + tag)
	if not await _until(func(): return not Game.memory_mode and _free_play(), 30.0):
		_fail("demo: the return from %s never finished" % target)
		return
	await _wait(1.0)
	await _shoot("present_again_" + tag)
	check_returned(before, found_id)


func _demo_menu_trip(target: String) -> void:
	var tag := target.to_lower()
	if not Game.ui.get("main_menu").is_open:
		await Game.show_main_menu()
		await _wait(1.2)
	var before_story := Story.save_json()
	var before_explore: Dictionary = Explore.state()
	var mm = Game.ui.get("main_menu")
	if not (mm._buttons["memories"] as Button).visible:
		_fail("demo: main menu does not offer „Erinnerungen“ although the profile has memories")
	await _shoot("main_menu_" + tag)
	Game.ui.open_memories("menu")
	var view = Game.ui.get("memories")
	await _wait(0.6)
	if not view.select(target):
		_fail("demo: card %s not selectable from the main menu" % target)
		Game.ui.close_all()
		Game.ui.show_main_menu()
		return
	await _wait(0.3)
	await _shoot("menu_view_" + tag)
	view.activate(target)
	if not await _until(func(): return Game.memory_mode and _free_play(), 40.0):
		_fail("demo: the trip from the menu into %s never finished" % target)
		return
	await _wait(1.6)
	await _shoot("menu_arrived_" + tag)
	check_inside(target)
	if not Game.memory_from_menu:
		_fail("demo: memory from the menu not flagged")
	var inside := Story.save_json()
	var tw := pick_twin("dialogue")
	if tw != null:
		_place_near(tw)
		Game.interact(tw)
		await _drive_interaction("menu_twin_" + tag)
	var fi := pick_find()
	if fi != null:
		_place_near(fi)
		Game.interact(fi)
		await _drive_interaction("menu_find_" + tag)
	if Story.save_json() != inside:
		_fail("demo: the Story state changed inside the menu memory of " + target)
	# a side level's exit leads back (to the main menu here); otherwise the pause-menu entry
	var ex: Node = null
	for it in get_tree().get_nodes_in_group("interactables"):
		if it.is_inside_tree() and str(it.kind) == "exit" and Game.level.is_ancestor_of(it):
			ex = it
	if ex != null:
		_place_near(ex)
		await Game.interact(ex)
	else:
		Game.ui.open_pause()
		await _wait(0.5)
		await _shoot("menu_pause_" + tag)
		Game.ui.pause_menu._memories()
	if not await _until(func(): return not Game.memory_mode and mm.is_open, 30.0):
		_fail("demo: the return from the menu memory did not reach the main menu")
		return
	await _wait(1.2)
	await _shoot("main_menu_again_" + tag)
	if Story.save_json() != before_story:
		_fail("demo: the menu's Story state was not restored after the menu memory")
	if Explore.state() != before_explore:
		_fail("demo: the menu's Explore state was not restored after the menu memory")
