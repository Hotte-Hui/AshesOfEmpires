extends Control
## UI preview / smoke test (tests/visual/UIPreview.tscn).
## Instances scenes/ui/UIRoot.tscn over a stand-in game frame, injects mock Story/Saves services through
## ui_kit overrides, walks through every UI state, checks key behaviours (puzzle submit/hint, overlay
## alignment, journal parsing, modal stack + pause) and saves 1920x1080 screenshots to
## assets/ui/_preview/*.png, then quits. Headless runs skip the screenshots (logic only).
##   godot --path . res://tests/visual/UIPreview.tscn
## Exit code: 0 = all checks passed, 1 = a check failed.

const Kit := preload("res://scripts/ui/ui_kit.gd")
const UIROOT := preload("res://scenes/ui/UIRoot.tscn")
const OUT := "res://assets/ui/_preview/"


class MockStory extends Node:
	signal objective_completed(id: String)
	signal scene_changed(scene_id: String)
	signal item_granted(id: String)
	var current_scene := "L_A1_Railyard"
	var active_character := "alexei"
	var attempts := {}
	var avail: Array = ["a1_inspect_seal", "a1_inspect_timetable"]
	var states := {"a1_talk_irina": "complete", "a1_inspect_seal": "available", "a1_inspect_timetable": "available"}
	var inv: Array = ["ev_damaged_seal", "ev_timetable", "ev_ledger"]
	var people: Array = ["irina"]
	var choices := {"a1_choose": "share_with_irina"}

	func available() -> Array:
		return avail

	func is_available(id) -> bool:
		return id in avail

	func objective_state(id) -> String:
		return str(states.get(id, "locked"))

	func inventory() -> Array:
		return inv

	func choice_history() -> Dictionary:
		return choices

	func chapter_key() -> String:
		return "ui.chapter_a1"

	func puzzle_hint_available(id) -> bool:
		return int(attempts.get(id, 0)) >= 2

	func solve_puzzle(id, answer) -> Dictionary:
		var ok := false
		if id == "a1_solve_signal":
			ok = answer == ["square", "circle", "triangle"]
		elif id == "m1_align_plans":
			ok = answer is Dictionary and answer == {"rotation_steps": 0, "offset_x": 2, "offset_y": -1}
		if not ok:
			attempts[id] = int(attempts.get(id, 0)) + 1
		return {"ok": true, "solved": ok, "error": ""}

	func journal() -> Dictionary:
		var objs: Array = []
		for q in Kit.quests():
			for o in q["objectives"]:
				objs.append({"id": o["id"], "quest": q["id"], "text_key": o["text_key"], "type": o["type"],
					"state": states.get(o["id"], "locked")})
		var ev: Array = []
		for i in inv:
			var d := Kit.item_def(i)
			ev.append({"id": i, "name_key": d.get("name_key", ""), "description_key": d.get("description_key", ""),
				"category": d.get("category", "")})
		var dec: Array = []
		for k in choices:
			dec.append({"objective": k, "choice": choices[k]})
		return {"objectives": objs, "evidence": ev, "people": people, "decisions": dec,
			"chapter_key": "ui.chapter_a1", "scene": current_scene, "character": active_character}


class MockSaves extends Node:
	signal loaded(slot: String)
	var deleted: Array = []
	var saved_slots: Array = []

	func list_slots() -> Array:
		var now := 1793893320.0   # 2026-11-04 18:42 UTC
		return [
			{"slot": "1", "manual": true, "exists": true, "valid": true, "timestamp": now - 3600.0 * 26,
				"chapter_key": "ui.chapter_a1", "character": "alexei", "scene": "L_A1_Railyard", "playtime_s": 1260.0},
			{"slot": "2", "manual": true, "exists": true, "valid": true, "timestamp": now - 600.0,
				"chapter_key": "ui.chapter_m1", "character": "konrad", "scene": "L_M1_Archive", "playtime_s": 3900.0},
			{"slot": "3", "manual": true, "exists": false, "valid": false},
			{"slot": "auto", "manual": false, "exists": true, "valid": true, "timestamp": now - 60.0,
				"chapter_key": "ui.chapter_m1", "character": "konrad", "scene": "L_M1_Archive", "playtime_s": 3960.0},
			{"slot": "quick", "manual": false, "exists": false, "valid": false},
		]

	func has_any() -> bool:
		return true

	func save(slot, _label := "") -> Dictionary:
		saved_slots.append(str(slot))
		return {"ok": true, "error": "", "slot": str(slot)}

	func load(slot) -> Dictionary:
		loaded.emit(str(slot))
		return {"ok": true, "error": "", "slot": str(slot)}

	func delete(slot) -> Dictionary:
		deleted.append(str(slot))
		return {"ok": true, "error": ""}


var ui: Control
var story := MockStory.new()
var saves := MockSaves.new()
var failures: Array = []
var shots := 0
var headless := false
var _world: TextureRect


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	headless = DisplayServer.get_name() == "headless"
	_setup_window()
	add_child(story)
	add_child(saves)
	Kit.overrides = {"Story": story, "Saves": saves}
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)   # deterministic, in memory only (never saved here)
	_world = TextureRect.new()
	_world.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_world.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_world.stretch_mode = TextureRect.STRETCH_SCALE
	_world.size = Vector2(1920, 1080)
	_world.texture = _load_png(OUT + "karsk_frame.png")
	if _world.texture == null:
		_world.texture = _load_png(OUT + "mock_world.png")
	add_child(_world)
	ui = UIROOT.instantiate()
	add_child(ui)
	_run.call_deferred()


func _setup_window() -> void:
	if headless:
		return
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	var scr := DisplayServer.screen_get_size()
	if scr.x <= 1920 or scr.y <= 1130:
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
		DisplayServer.window_set_position(Vector2i.ZERO)
	DisplayServer.window_set_size(Vector2i(1920, 1080))
	print("UIPREVIEW screen ", scr, " window ", DisplayServer.window_get_size())


func _load_png(path: String) -> Texture2D:
	var full := ProjectSettings.globalize_path(path)
	if not FileAccess.file_exists(full):
		return null
	var img := Image.load_from_file(full)
	return ImageTexture.create_from_image(img) if img != null and not img.is_empty() else null


func check(cond: bool, what: String) -> void:
	if cond:
		print("  PASS ", what)
	else:
		print("  FAIL ", what)
		failures.append(what)


func wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func shot(name: String) -> void:
	shots += 1
	if headless:
		print("SHOT (headless, skipped) ", name)
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(OUT + "%02d_%s.png" % [shots, name])
	img.save_png(path)
	print("SHOT ", path, " ", img.get_size())


## Phase 2: the same UI against the REAL Story and Saves autoloads (no mocks). Saves are redirected to
## user://ui_preview_saves and removed afterwards, so the player's save files are never touched.
func _real_services_phase() -> void:
	var st := get_node_or_null("/root/Story")
	var sv := get_node_or_null("/root/Saves")
	if st == null or not st.has_method("journal") or not st.has_method("new_game"):
		print("  SKIP real-services phase (Story autoload not implemented yet)")
		return
	print("-- real services phase")
	Kit.overrides = {}
	ui.close_all()
	ui.connect_story()
	st.new_game()
	var r = st.start_dialogue("a1_talk_irina")
	check(Kit.ok(r), "real Story.start_dialogue ok")
	for _i in 12:
		var adv = st.advance_dialogue("a1_talk_irina")
		if not Kit.ok(adv) or bool(adv.get("finished", false)):
			break
	check(Kit.ok(st.inspect("a1_inspect_seal")) and Kit.ok(st.inspect("a1_inspect_timetable")), "real inspect seal + timetable")
	ui.hud.show_hud()
	ui.hud.refresh()
	await wait(0.4)
	check(ui.hud._objective_ids == ["a1_solve_signal"], "HUD tracks the real next objective")
	ui.open_journal("evidence")
	await wait(0.6)
	var data: Dictionary = ui.journal._data
	check(data["evidence"].size() == 2, "real journal: 2 evidence items")
	var met := []
	for p in data["people"]:
		met.append(p["id"])
	check("irina" in met, "real journal: Irina met")
	await shot("real_journal_evidence")
	ui.journal.show_tab("objectives")
	await wait(0.4)
	await shot("real_journal_objectives")
	ui.journal.close()
	var sp = ui.signal_puzzle
	sp.open("a1_solve_signal")
	await wait(0.4)
	for o in [["circle", "triangle", "square"], ["triangle", "circle", "square"]]:
		for sym in o:
			sp.place(sym)
		sp.submit()
	await wait(0.3)
	check(sp._hint_box.visible, "real Story: hint after two failures (puzzle_hint_available)")
	for sym in ["square", "circle", "triangle"]:
		sp.place(sym)
	sp.submit()
	await wait(0.3)
	check(sp._done and st.objective_state("a1_solve_signal") == "complete", "real Story: signal solved once")
	await wait(2.2)
	if sv != null and "base_dir" in sv and sv.has_method("save"):
		var old_dir: String = sv.base_dir
		sv.base_dir = "user://ui_preview_saves"
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(sv.base_dir))
		var res = sv.save("2")
		check(Kit.ok(res), "real Saves.save into the preview folder")
		ui.open_saveload("load", false)
		await wait(0.6)
		var row = ui.saveload_menu._rows.get("2")
		check(row != null and not row.disabled, "real save listed and loadable")
		await shot("real_load_menu")
		ui.saveload_menu.close()
		if sv.has_method("delete"):
			sv.delete("2")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(sv.base_dir))
		sv.base_dir = old_dir


func _run() -> void:
	await wait(0.6)
	# ------------------------------------------------------------ main menu
	_world.visible = false
	ui.show_main_menu()
	await wait(1.6)
	check(ui.main_menu.is_open and ui.top_modal() == ui.main_menu, "main menu open on stack")
	check((ui.main_menu._buttons["continue"] as Button).visible, "Fortsetzen visible when Saves.has_any()")
	await shot("main_menu")
	ui.close_all()
	_world.visible = true
	# ------------------------------------------------------------ HUD
	ui.hud.show_hud()
	ui.hud.refresh()
	ui.hud.show_prompt(Vector2(853 - 300, 304 - 58) * 3, Kit.t("ui.prompt.inspect"))
	ui.hud.toast(Kit.t("ui.toast.evidence", {"name": Kit.item_name("ev_damaged_seal")}))
	ui.hud.toast(Kit.t("ui.toast.person", {"name": Kit.char_name("irina")}), "person")
	ui.hud.show_chapter(Kit.t("ui.chapter_a1"), Kit.t("world.a1.title"))
	await wait(1.5)
	check(ui.hud._objective_box.visible, "objective tracker visible")
	check(ui.hud._objective_list.get_child_count() == 2, "two available objectives listed")
	await shot("hud")
	ui.hud.hide_prompt()
	await wait(4.5)
	# ------------------------------------------------------------ dialogue
	ui.dialogue.show_line("irina", Kit.t("dlg.irina.02"), "concerned")
	await wait(0.4)
	check(ui.dialogue.is_typing(), "typewriter running")
	var adv := [0]
	ui.dialogue.advanced.connect(func(): adv[0] += 1)
	ui.dialogue._advance()
	check(not ui.dialogue.is_typing() and adv[0] == 0, "first advance completes the line without advancing")
	ui.dialogue._advance()
	check(adv[0] == 1, "second advance emits advanced")
	ui.dialogue.show_line("alexei", Kit.t("dlg.alexei.02"), "determined")
	ui.dialogue.skip_typing()
	await wait(0.5)
	check(not get_tree().paused, "dialogue does not pause the world")
	await shot("dialogue_line")
	ui.dialogue.show_line("alexei", Kit.t("obj.a1_choice"), "concerned")
	ui.dialogue.show_choices([{"id": "share_with_irina", "text": "choice.share_irina"},
		{"id": "keep_private", "text": "choice.keep_private"}])
	ui.dialogue.skip_typing()
	await wait(0.5)
	check(ui.dialogue._choices_box.get_child_count() == 2, "two choices shown")
	await shot("dialogue_choices")
	var picked := [""]
	ui.dialogue.chosen.connect(func(id): picked[0] = id)
	(ui.dialogue._choices_box.get_child(1) as Button).pressed.emit()
	check(picked[0] == "keep_private", "choice emits chosen(id)")
	ui.dialogue.show_line("irina", Kit.t("dlg.irina.branch_b"), "concerned")
	ui.dialogue.skip_typing()
	ui.dialogue.toggle_history()
	await wait(0.5)
	await shot("dialogue_history")
	ui.dialogue.toggle_history()
	ui.dialogue.close()
	# ------------------------------------------------------------ inspect
	ui.inspect.open("ev_damaged_seal")
	await wait(0.8)
	check(get_tree().paused, "inspect pauses the world")
	await shot("inspect_seal")
	ui.inspect.close()
	check(not get_tree().paused, "closing inspect unpauses")
	ui.inspect.open("a1_inspect_timetable")
	await wait(0.6)
	check(ui.inspect.item_id == "ev_timetable", "inspect accepts objective id (grant_item)")
	ui.inspect.close()
	# ------------------------------------------------------------ signal puzzle
	var sp = ui.signal_puzzle
	sp.open("a1_solve_signal")
	await wait(0.5)
	check(sp.symbols == ["triangle", "square", "circle"], "display_symbols from puzzles.json")
	for o in [["triangle", "square", "circle"], ["circle", "square", "triangle"]]:
		for sym in o:
			sp.place(sym)
		sp.submit()
	await wait(0.3)
	check(sp._fails == 2 and sp._hint_box.visible, "hint after two failed attempts")
	sp.place("square")
	sp.place("circle")
	await wait(0.6)
	await shot("signal_puzzle_hint")
	sp.place("triangle")
	sp.submit()
	await wait(0.4)
	check(sp._done, "correct order solves via Story.solve_puzzle")
	await shot("signal_puzzle_solved")
	await wait(2.0)
	check(not sp.is_open, "puzzle closes itself after success")
	# ------------------------------------------------------------ blueprint puzzle
	story.current_scene = "L_M1_Archive"
	story.active_character = "konrad"
	var bp = ui.blueprint_puzzle
	bp.open("m1_align_plans")
	await wait(0.6)
	await shot("blueprint_start")
	bp._board.set_state(0, Vector2i(1, -1))
	bp.submit()
	bp._board.set_state(0, Vector2i(2, 0))
	bp.submit()
	bp._board.set_state(0, Vector2i(2, -1))
	await wait(0.4)
	check(bp._board.aligned_count() == bp._board.landmarks.size() and bp._board.landmarks.size() > 0, "marks align at the canonical answer")
	check(bp._hint_box.visible, "blueprint hint after two failed attempts")
	await shot("blueprint_aligned")
	bp.submit()
	await wait(0.3)
	check(bp._done, "overlay solved with {rotation_steps 0, offset_x 2, offset_y -1}")
	await wait(2.4)
	# ------------------------------------------------------------ journal
	story.current_scene = "L_A1_Railyard"
	story.active_character = "alexei"
	story.states["a1_inspect_seal"] = "complete"
	story.states["a1_inspect_timetable"] = "complete"
	story.states["a1_solve_signal"] = "complete"
	story.states["a1_inspect_ledger"] = "complete"
	story.states["a1_choose"] = "complete"
	story.states["m1_inspect_plan_a"] = "available"
	story.states["m1_inspect_plan_b"] = "available"
	ui.open_journal("objectives")
	await wait(0.7)
	var data: Dictionary = ui.journal._data
	check(data["evidence"].size() == 3 and data["people"].size() == 1 and data["decisions"].size() == 1, "journal parses Story.journal()")
	var locked_listed := false
	for o in data["objectives"]:
		if o["id"] == "m1_align_plans":
			locked_listed = true
	check(not locked_listed, "locked objectives are not listed")
	await shot("journal_objectives")
	for tab in ["evidence", "people", "decisions"]:
		ui.journal.show_tab(tab)
		await wait(0.5)
		await shot("journal_" + tab)
	ui.journal.close()
	# ------------------------------------------------------------ pause, settings, save/load, confirm, credits
	ui.open_pause()
	await wait(0.6)
	check(get_tree().paused, "pause menu pauses")
	await shot("pause")
	ui.open_settings()
	ui.settings_menu.show_tab("access")
	await wait(0.6)
	await shot("settings_access")
	ui.settings_menu.show_tab("controls")
	await wait(0.4)
	await shot("settings_controls")
	ui.settings_menu.show_tab("audio")
	await wait(0.4)
	await shot("settings_audio")
	ui.settings_menu.close()
	ui.open_saveload("save", true)
	await wait(0.6)
	await shot("save_menu")
	ui.saveload_menu._select("2")
	ui.saveload_menu._primary_selected()
	await wait(0.5)
	check(ui.top_modal() == ui.confirm, "overwrite asks for confirmation")
	await shot("confirm_overwrite")
	ui.confirm._answer(true)
	await wait(0.3)
	check("2" in saves.saved_slots, "confirmed save calls Saves.save")
	ui.saveload_menu.close()
	ui.open_saveload("load", true)
	await wait(0.6)
	await shot("load_menu")
	ui.saveload_menu.close()
	ui.pause_menu.close()
	check(not get_tree().paused and ui.top_modal() == null, "stack empty and unpaused after closing all")
	ui.open_credits()
	await wait(1.0)
	await shot("credits")
	ui.credits.close()
	# ------------------------------------------------------------ cinematic: letterbox + subtitles
	ui.set_cinematic(true)
	await wait(0.8)
	ui.subtitles.show_subtitle(Kit.t("cinematic.hall_reveal"), 6.0)
	await wait(0.6)
	await shot("cinematic_subtitles")
	ui.subtitles.clear()
	ui.set_cinematic(false)
	ui.hud.show_hud()
	await wait(0.8)
	# ------------------------------------------------------------ accessibility: text scale 150 %, high contrast
	var s := Kit.svc("Settings")
	if s != null and "values" in s:
		s.values["text_scale"] = 1.5
		Kit.refresh_text_scale()
		ui.dialogue.show_line("emil", Kit.t("dlg.emil.03"), "determined")
		ui.dialogue.skip_typing()
		await wait(0.5)
		check(ui.dialogue._text.get_theme_font_size("font_size") == 51, "text scale 150 % applied live")
		await shot("dialogue_text150")
		ui.dialogue.close()
		ui.inspect.open("ev_emil_note")
		await wait(0.7)
		await shot("inspect_text150")
		ui.inspect.close()
		s.values["text_scale"] = 1.0
		Kit.refresh_text_scale()
		s.values["high_contrast"] = true
		ui._apply_theme()
		ui.open_pause()
		await wait(0.6)
		await shot("pause_high_contrast")
		ui.pause_menu.close()
		s.values["high_contrast"] = false
		ui._apply_theme()
	await _real_services_phase()
	print("UIPREVIEW done: %d shots, %d failures" % [shots, failures.size()])
	for f in failures:
		print("  failed: ", f)
	get_tree().quit(0 if failures.is_empty() else 1)
