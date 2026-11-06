extends SceneTree
## Windowed capture harness for the two mini-games of Chapter 4 part 2 (owner: exploration c4p2, §12.8):
## „Die Drehscheibe“ (Turntable.tscn) and „Die Gepäckwaage“ (LuggageScale.tscn). Builds the real UIRoot (over an
## optional backdrop screenshot) and opens each game the way Game._run_minigame does (ui.add_child + open(ctx)), then
## drives it ONLY with synthetic key events routed through the input pipeline:
##   turntable: 1_start · 2_turning (→ held, the bridge swings round) · 3_hint (two refused pulls) · 4_solved
##              (right after demo_solve(): the engine rolls into stall 7)
##   luggage:   1_start · 2_weights (the big weight in its notch, the tongue swinging) · 3_hint (two refused
##              readings) · 4_solved (after demo_solve(): the slip complete)
## and checks that finished(true) arrives exactly once per game. Optional: --scale=1.5 (text scale), --hc=1 (high
## contrast) -- Settings.values for this run only, nothing is saved. Writes no saves, no profile, no settings.
##
## godot --path . --script res://tests/visual/c4p2_explore_shots.gd -- --shots=<dir> [--game=turntable|luggage]
##       [--bg=<png>] [--scale=1.5] [--hc=1] [--tag=<suffix>]

const SCENES := {"turntable": "res://scenes/ui/minigames/Turntable.tscn",
	"luggage": "res://scenes/ui/minigames/LuggageScale.tscn"}
const IDS := {"turntable": "karsk.depot.turntable", "luggage": "berlin.ost.luggage_scale"}

var _out := ""
var _tag := ""
var _game := ""
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
		elif a.begins_with("--game="):
			_game = a.substr(7)
		elif a.begins_with("--bg="):
			_bg_path = a.substr(5)
		elif a.begins_with("--scale="):
			_scale = float(a.substr(8))
		elif a.begins_with("--hc="):
			_hc = a.substr(5) == "1"
		elif a.begins_with("--tag="):
			_tag = a.substr(6)
	if _out == "":
		push_error("c4p2_explore_shots: --shots=<absolute dir> is required (no user:// output)")
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


func _open(game: String) -> Array:
	var mg: Node = load(SCENES[game]).instantiate()
	_ui.add_child(mg)
	var res := {"done": 0, "ok": false}
	mg.finished.connect(func(ok: bool):
		res["done"] = int(res["done"]) + 1
		res["ok"] = ok)
	mg.open({"explore_id": IDS[game], "auto": false})
	await _wait(0.9)
	var pn: Control = mg.get("_panel")
	print("LAYOUT %s panel=%s min=%s" % [game, pn.get_global_rect(), pn.get_combined_minimum_size()])
	return [mg, res]


func _finish(game: String, mg: Node, res: Dictionary) -> void:
	var guard := 0.0
	while int(res["done"]) == 0 and guard < 8.0:
		await _wait(0.1)
		guard += 0.1
	await _wait(0.3)
	print("RESULT %s finished=%d success=%s" % [game, int(res["done"]), res["ok"]])
	if not (int(res["done"]) == 1 and res["ok"]):
		_fail += 1
	if is_instance_valid(mg):
		mg.queue_free()
	await _frames(4)


func _turntable() -> void:
	var o: Array = await _open("turntable")
	var mg: Node = o[0]
	await _shot("c4p2x_tt_1_start")
	_key(KEY_RIGHT, true)
	await _wait(1.6)
	_key(KEY_RIGHT, false)
	await _wait(0.5)
	await _shot("c4p2x_tt_2_turning")
	_key(KEY_SPACE, true)
	await _wait(1.5)
	_key(KEY_SPACE, false)
	await _tap(KEY_E)
	await _wait(0.3)
	await _tap(KEY_E)
	await _wait(0.6)
	print("HINT fails=%d hint_visible=%s" % [int(mg.get("fails")), mg.get("_hint_box").visible])
	await _shot("c4p2x_tt_3_hint")
	var t0 := Time.get_ticks_msec()
	await mg.demo_solve()
	print("SOLVE turntable demo_solve took %.1f s, solved=%s" % [(Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
	await _wait(0.5)
	await _shot("c4p2x_tt_4_solved")
	await _finish("turntable", mg, o[1])


func _luggage() -> void:
	var o: Array = await _open("luggage")
	var mg: Node = o[0]
	await _shot("c4p2x_lg_1_start")
	for i in 4:
		await _tap(KEY_RIGHT)
	await _tap(KEY_PAGEUP)
	await _tap(KEY_PAGEUP)
	await _wait(0.35)
	await _shot("c4p2x_lg_2_weights")
	await _tap(KEY_E)
	await _wait(0.3)
	await _tap(KEY_E)
	await _wait(0.8)
	print("HINT fails=%d hint_visible=%s" % [int(mg.get("fails")), mg.get("_hint_box").visible])
	await _shot("c4p2x_lg_3_hint")
	var t0 := Time.get_ticks_msec()
	await mg.demo_solve()
	print("SOLVE luggage demo_solve took %.1f s, solved=%s" % [(Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
	await _wait(0.4)
	await _shot("c4p2x_lg_4_solved")
	await _finish("luggage", mg, o[1])


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
	if _game == "" or _game == "turntable":
		await _turntable()
	if _game == "" or _game == "luggage":
		await _luggage()
	print("C4P2 EXPLORE SHOTS ", "OK" if _fail == 0 else "FAILED (%d)" % _fail)
	quit(0 if _fail == 0 else 1)
