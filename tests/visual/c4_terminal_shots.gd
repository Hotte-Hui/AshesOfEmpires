extends SceneTree
## Windowed capture harness for the data desk's two mini-games (round 13, §12.8): „Die Datenstelle“
## (DataTerminal.tscn) and „Planspiel Abgang“ (PlanspielAbgang.tscn). Builds the real UIRoot and opens each game the
## way Game._run_minigame does (ui.add_child + open(ctx)), then drives it ONLY with synthetic key events:
##   term_1_login   as opened                      term_2_hint    after two refused numbers
##   term_3_menu    logged in                      term_4_file    Wendt's memo on the screen
##   term_5_done    right after demo_solve()
##   ab_1_street    map 1 after the fly-in         ab_2_seen      the shortest way, walked at once: „Zugriff“
##   ab_3_trace     after three arrests: tip + trace
##   ab_4_map2 / ab_5_map3   during demo_solve()   ab_6_done      the run is over
## and checks that each game ends with finished(true) exactly once. Optional: --scale=1.5 (text scale), --hc=1 (high
## contrast), --rm=1 (reduced motion), --only=term|ab — Settings.values for this run only, nothing is saved.
## English: add `--lang=en`. Writes no saves, no profile, no settings.
##
## godot --path . --script res://tests/visual/c4_terminal_shots.gd -- --shots=<dir> [--scale=1.5] [--hc=1] [--rm=1]
##       [--only=term|ab] [--tag=<suffix>] [--lang=en]

const TERM := "res://scenes/ui/minigames/DataTerminal.tscn"
const AB := "res://scenes/ui/minigames/PlanspielAbgang.tscn"
const DIR_KEYS := [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_LEFT]

var _out := ""
var _tag := ""
var _scale := 1.0
var _hc := false
var _rm := false
var _only := ""
var _ui: Control
var _fail := 0


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			_out = a.substr(8)
		elif a.begins_with("--scale="):
			_scale = float(a.substr(8))
		elif a.begins_with("--hc="):
			_hc = a.substr(5) == "1"
		elif a.begins_with("--rm="):
			_rm = a.substr(5) == "1"
		elif a.begins_with("--only="):
			_only = a.substr(7)
		elif a.begins_with("--tag="):
			_tag = a.substr(6)
	if _out == "":
		push_error("c4_terminal_shots: --shots=<absolute dir> is required (no user:// output)")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(_out)
	var back := CanvasLayer.new()
	back.layer = -1
	root.add_child(back)
	var bg := ColorRect.new()
	bg.color = Color("10151a")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	back.add_child(bg)
	var layer := CanvasLayer.new()
	layer.layer = 10
	root.add_child(layer)
	_ui = load("res://scenes/ui/UIRoot.tscn").instantiate()
	layer.add_child(_ui)
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _wait(t: float) -> void:
	await create_timer(t, true).timeout


func _key(k: int, down: bool) -> void:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = down
	Input.parse_input_event(ev)


func _tap(k: int) -> void:
	_key(k, true)
	await _frames(3)
	_key(k, false)
	await _frames(3)


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var path := _out.path_join(name + _tag + ".png")
	img.save_png(path)
	print("SHOT ", path, " ", img.get_size())


func _settings(key: String, value) -> void:
	var s := root.get_node_or_null("Settings")
	if s == null:
		return
	s.values[key] = value
	s.changed.emit(key, value)


func _open(path: String, id: String, res: Dictionary) -> Node:
	var mg: Node = load(path).instantiate()
	_ui.add_child(mg)
	mg.finished.connect(func(ok: bool):
		res["done"] = int(res["done"]) + 1
		res["ok"] = ok)
	mg.open({"explore_id": id, "auto": false})
	return mg


func _finish(mg: Node, res: Dictionary, what: String) -> void:
	var guard := 0.0
	while int(res["done"]) == 0 and guard < 8.0:
		await _wait(0.1)
		guard += 0.1
	await _wait(0.3)
	print("RESULT %s finished=%d success=%s fails=%d" % [what, int(res["done"]), res["ok"], int(mg.get("fails")) if is_instance_valid(mg) else -1])
	if not (int(res["done"]) == 1 and res["ok"]):
		_fail += 1
	if is_instance_valid(mg):
		mg.queue_free()
	await _frames(4)


func _run() -> void:
	await _frames(12)
	if _scale != 1.0:
		_settings("text_scale", _scale)
	if _hc:
		_settings("high_contrast", true)
	if _rm:
		_settings("reduced_motion", true)
	if _only != "ab":
		await _terminal()
	if _only != "term":
		await _planspiel()
	print("C4 TERMINAL SHOTS ", "OK" if _fail == 0 else "FAILED (%d)" % _fail)
	quit(0 if _fail == 0 else 1)


func _terminal() -> void:
	var res := {"done": 0, "ok": false}
	var mg: Node = _open(TERM, "berlin.annex.term_files", res)
	await _wait(0.9)
	var pn: Control = mg.get("_panel")
	print("LAYOUT terminal panel=%s min=%s" % [pn.get_global_rect(), pn.get_combined_minimum_size()])
	await _shot("term_1_login")
	await _tap(KEY_ENTER)
	await _wait(0.3)
	await _tap(KEY_ENTER)
	await _wait(0.6)
	print("HINT fails=%d hint_visible=%s min=%s" % [int(mg.get("fails")), mg.get("_hint_box").visible, pn.get_combined_minimum_size()])
	await _shot("term_2_hint")
	for ch in "2741":
		await _tap(KEY_0 + int(ch))
	await _tap(KEY_ENTER)
	await _wait(0.5)
	await _shot("term_3_menu")
	await _tap(KEY_DOWN)
	await _tap(KEY_ENTER)
	await _tap(KEY_DOWN)
	await _tap(KEY_DOWN)
	await _tap(KEY_ENTER)
	await _wait(0.4)
	await _shot("term_4_file")
	await _tap(KEY_BACKSPACE)
	var t0 := Time.get_ticks_msec()
	await mg.demo_solve()
	print("SOLVE terminal demo_solve took %.1f s, solved=%s" % [(Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
	await _wait(0.4)
	await _shot("term_5_done")
	await _finish(mg, res, "terminal")


func _planspiel() -> void:
	var res := {"done": 0, "ok": false}
	var ab: Node = _open(AB, "berlin.annex.planspiel", res)
	await _wait(1.6)
	var pn: Control = ab.get("_panel")
	print("LAYOUT planspiel panel=%s min=%s" % [pn.get_global_rect(), pn.get_combined_minimum_size()])
	await _shot("ab_1_street")
	var lg = ab.get("logic")
	for n in 3:
		var dirs: Array = lg.shortest_dirs()
		var held := -1
		var t := 0.0
		while not lg.caught and t < 25.0:
			var want := int(dirs[lg.steps]) if lg.steps < dirs.size() else -1
			if want != held:
				if held >= 0:
					_key(DIR_KEYS[held], false)
				if want >= 0:
					_key(DIR_KEYS[want], true)
				held = want
			await process_frame
			t += 1.0 / 60.0
		if held >= 0:
			_key(DIR_KEYS[held], false)
		print("ARREST %d caught=%s by=%d fails=%d" % [n + 1, lg.caught, int(lg.caught_by), int(ab.get("fails"))])
		if n == 0:
			await _wait(0.5)
			await _shot("ab_2_seen")
		await _wait(1.6)
	await _wait(1.4)
	print("HINT trace_on=%s hint_visible=%s min=%s" % [ab.get("trace_on"), ab.get("_hint_box").visible, pn.get_combined_minimum_size()])
	await _shot("ab_3_trace")
	var done := [false]
	var t0 := Time.get_ticks_msec()
	var runner := func() -> void:
		await ab.demo_solve()
		done[0] = true
	runner.call()
	var shown := {0: true}
	var guard := 0.0
	while not done[0] and guard < 200.0:
		await process_frame
		guard += 1.0 / 60.0
		var idx := int(lg.index)
		if not shown.has(idx):
			shown[idx] = true
			await _wait(4.0 if idx == 2 else 2.2)
			await _shot("ab_%d_map%d" % [idx + 3, idx + 1])
	print("SOLVE planspiel demo_solve took %.1f s, solved=%s fails=%d" % [(Time.get_ticks_msec() - t0) / 1000.0, ab.get("solved"), int(ab.get("fails"))])
	await _wait(0.4)
	await _shot("ab_6_done")
	await _finish(ab, res, "planspiel")
