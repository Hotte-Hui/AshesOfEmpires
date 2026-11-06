extends SceneTree
## Windowed capture harness for the annex mini-game "Die Lüftungsklappen" (VentFlaps.tscn, round-9 fix compl-01,
## §12.8). Builds the real UIRoot (over an optional backdrop screenshot) and opens the game the way Game._run_minigame
## does (ui.add_child + open(ctx)), then drives it ONLY with synthetic key events routed through UIRoot:
##   1_start   as opened (the night shift's setting: the bell rings, the corridor gets no air)
##   2_hint    after two refused acknowledgements (the hint about the long corridor duct)
##   3_turned  flap 3 opened two steps (all needles moved)
##   4_solved  right after demo_solve() (the real-input driver's path), before the hold ends
## and checks that finished(true) arrives exactly once. Optional: --scale=1.5 (text scale), --hc=1 (high contrast) --
## Settings.values for this run only, nothing is saved. Writes no saves, no profile, no settings.
##
## godot --path . --script res://tests/visual/c4_vent_shots.gd -- --shots=<dir> [--bg=<png>] [--scale=1.5] [--hc=1]
##       [--tag=<suffix>]

const GAME_SCENE := "res://scenes/ui/minigames/VentFlaps.tscn"

var _out := ""
var _tag := ""
var _bg_path := ""
var _scale := 1.0
var _hc := false
var _ui: Control
var _bg: TextureRect
var _fail := 0


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			_out = a.substr(8)
		elif a.begins_with("--bg="):
			_bg_path = a.substr(5)
		elif a.begins_with("--scale="):
			_scale = float(a.substr(8))
		elif a.begins_with("--hc="):
			_hc = a.substr(5) == "1"
		elif a.begins_with("--tag="):
			_tag = a.substr(6)
	if _out == "":
		push_error("c4_vent_shots: --shots=<absolute dir> is required (no user:// output)")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(_out)
	var back := CanvasLayer.new()
	back.layer = -1
	root.add_child(back)
	_bg = TextureRect.new()
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.stretch_mode = TextureRect.STRETCH_SCALE
	_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	back.add_child(_bg)
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


func _tap(k: int) -> void:
	for down in [true, false]:
		var ev := InputEventKey.new()
		ev.keycode = k
		ev.physical_keycode = k
		ev.pressed = down
		Input.parse_input_event(ev)
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


func _run() -> void:
	await _frames(12)
	if _scale != 1.0:
		_settings("text_scale", _scale)
	if _hc:
		_settings("high_contrast", true)
	if _bg_path != "":
		var img := Image.load_from_file(_bg_path)
		if img != null:
			_bg.texture = ImageTexture.create_from_image(img)
	var mg: Node = load(GAME_SCENE).instantiate()
	_ui.add_child(mg)
	var res := {"done": 0, "ok": false}
	mg.finished.connect(func(ok: bool):
		res["done"] = int(res["done"]) + 1
		res["ok"] = ok)
	mg.open({"explore_id": "berlin.annex.fans", "auto": false})
	await _wait(0.9)
	var pn: Control = mg.get("_panel")
	print("LAYOUT vent panel=%s min=%s" % [pn.get_global_rect(), pn.get_combined_minimum_size()])
	await _shot("c4x_vent_1_start")
	await _tap(KEY_E)
	await _wait(0.3)
	await _tap(KEY_E)
	await _wait(0.6)
	print("HINT fails=%d hint_visible=%s" % [int(mg.get("fails")), mg.get("_hint_box").visible])
	await _shot("c4x_vent_2_hint")
	await _tap(KEY_3)
	for i in 2:
		await _tap(KEY_UP)
		await _wait(0.25)
	await _wait(0.8)
	await _shot("c4x_vent_3_turned")
	var t0 := Time.get_ticks_msec()
	await mg.demo_solve()
	print("SOLVE demo_solve took %.1f s, solved=%s" % [(Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
	await _wait(0.4)
	await _shot("c4x_vent_4_solved")
	var guard := 0.0
	while int(res["done"]) == 0 and guard < 8.0:
		await _wait(0.1)
		guard += 0.1
	await _wait(0.3)
	print("RESULT finished=%d success=%s" % [int(res["done"]), res["ok"]])
	if not (int(res["done"]) == 1 and res["ok"]):
		_fail += 1
	print("C4 VENT SHOTS ", "OK" if _fail == 0 else "FAILED (%d)" % _fail)
	quit(0 if _fail == 0 else 1)
