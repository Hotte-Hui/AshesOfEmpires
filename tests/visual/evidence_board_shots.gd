extends SceneTree
## Windowed captures of „Die Akte C-17“ in the running game (owner: board, §12.12): boots the real Main scene on the
## quay, advances the in-memory Story through the public API to the last Chapter-3 scene (c3a … c3f, then the halves
## and Konrad on the quay — no decision, so nothing reloads), opens the journal on the tab „Akte“ and the board the
## way a player does (journal → „Pinnwand öffnen“), moves the focus with synthetic arrow keys and captures at 100 %,
## 150 % text and high contrast (mock Settings through ui_kit overrides — the player's settings.cfg is never written),
## the InspectView on top and a memory of the station (Game.memory_mode set for the shot only).
## Writes NO saves (Main boots in capture mode; --frames keeps Game's own capture flow from quitting first).
##
## godot --path . --script res://tests/visual/evidence_board_shots.gd -- --scene=L_C3_Quay --char=alexei
##       --capture=<dir>/_unused.png --frames=999999 --shots=<dir>

const TK := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")


class ShotSettings extends Node:
	signal changed(key: String, value)
	var values := {"text_scale": 1.0, "high_contrast": false, "reduced_motion": true, "subtitles": true}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


var _args := {}
var _out := ""
var _settings: ShotSettings


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	_out = str(_args.get("shots", "user://evidence_board_shots"))
	DirAccess.make_dir_recursive_absolute(_out)
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	root.add_child(main)
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var path := _out.path_join(name + ".png")
	img.save_png(path)
	print("SHOT ", path)


func _drain(st: Node) -> void:
	for c in st.pending_cinematics():
		st.consume_cinematic(c, true)


func _key(code: int) -> void:
	for pressed in [true, false]:
		var ev := InputEventKey.new()
		ev.keycode = code as Key
		ev.physical_keycode = code as Key
		ev.pressed = pressed
		Input.parse_input_event(ev)
		await process_frame


func _run() -> void:
	var g: Node = root.get_node("Game")
	var guard := 0
	while (g.level == null or g.player == null) and guard < 900:
		guard += 1
		await process_frame
	if g.level == null:
		printerr("HARNESS: level did not load")
		quit(1)
		return
	var st: Node = root.get_node("Story")
	var tk := TK.new()
	for stage in ["a1", "m1", "c3a", "c3b", "c3c", "c3d", "c3e", "c3f"]:
		if stage == "a1":
			tk.play_a1(st)
		else:
			_stage(tk, st, stage)
		_drain(st)
	st.inspect("c3g_inspect_halves")
	tk.play_dialogue(st, "c3g_talk_konrad")
	_drain(st)
	if not tk.failures.is_empty():
		printerr("HARNESS story: ", tk.failures)
	print("STORY scene ", st.current_scene, " items ", st.inventory().size())
	_settings = ShotSettings.new()
	root.add_child(_settings)
	UIKit.overrides["Settings"] = _settings
	await _frames(30)
	var ui: Node = g.ui
	ui.open_journal("board")
	await _frames(40)
	await _shot("1_journal_akte_100")
	var j: Node = ui.journal
	j.open_board()
	await _frames(60)
	await _shot("2_board_100")
	var board: Node = j.board
	board.focus_card("ev_c3_intake_book")
	await _frames(20)
	await _shot("3_board_100_focus_intake")
	for k in [KEY_RIGHT, KEY_DOWN, KEY_DOWN]:
		await _key(k)
	await _frames(10)
	print("FOCUS after keys ", board.focused_item)
	await _shot("4_board_100_keys")
	board.inspect(board.focused_item)
	await _frames(30)
	await _shot("5_inspect_over_board")
	ui.inspect.close()
	await _frames(10)
	board.close()
	j.close()
	# 150 % text
	_settings.values["text_scale"] = 1.5
	UIKit.refresh_text_scale()
	ui.open_journal("board")
	await _frames(20)
	await _shot("6_journal_akte_150")
	j.open_board()
	await _frames(60)
	board.focus_card("ev_c3_kordon_plan")
	await _frames(20)
	await _shot("7_board_150")
	board.close()
	j.close()
	# high contrast at 100 %
	_settings.values["text_scale"] = 1.0
	_settings.values["high_contrast"] = true
	UIKit.refresh_text_scale()
	if ui.has_method("_apply_theme"):
		ui._apply_theme()
	ui.open_journal("board")
	await _frames(10)
	j.open_board()
	await _frames(60)
	board.focus_card("ev_c3_weighbill")
	await _frames(20)
	await _shot("8_board_hc")
	board.close()
	j.close()
	_settings.values["high_contrast"] = false
	if ui.has_method("_apply_theme"):
		ui._apply_theme()
	# the file as it was in a memory of the station (Game state only for this shot; nothing is saved)
	g.memory_mode = true
	g.memory_scene = "L_C3_Station"
	ui.open_journal("board")
	await _frames(20)
	await _shot("9_journal_memory_station")
	j.open_board()
	await _frames(60)
	await _shot("10_board_memory_station")
	board.close()
	j.close()
	g.memory_mode = false
	g.memory_scene = ""
	UIKit.overrides.erase("Settings")
	print("RESULT owned=%d threads=%d summary=%d" % [board.model.get("owned", 0), board.model.get("threads", []).size(),
		board.model.get("summary", []).size()])
	quit(0)


func _stage(tk: TK, st: Node, stage: String) -> void:
	match stage:
		"m1":
			tk.play_m1(st)
		"c3a":
			tk.play_c3a(st)
		"c3b":
			tk.play_c3b(st)
		"c3c":
			tk.play_c3c(st)
		"c3d":
			tk.play_c3d(st, "admit_plan")
		"c3e":
			tk.play_c3e(st)
		"c3f":
			tk.play_c3f(st)
