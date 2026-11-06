extends SceneTree
## Windowed capture harness for the two Chapter-3 mini-games (owner: minigames r7, §12.8): "Die Fallblatttafel"
## (FlapBoard.tscn) and "Die Garderobe" (Cloakroom.tscn). Builds the real UIRoot over a backdrop screenshot and opens
## each game the way Game._run_minigame does (ui.add_child + open(ctx)), then drives it ONLY with synthetic key
## events routed through UIRoot:
##   1_start  as opened
##   2_hint   after two refused moves (flap: two „Probelauf" runs on the jammed line; cloak: two wrong coats)
##   3_solved right after demo_solve() (the real-input driver's path), before the solved hold ends
## and checks that finished(true) arrives exactly once. Optional variants: --scale=1.5 (text scale) and --hc=1
## (high contrast) — set for this run only (Settings.values + changed signal, nothing is saved). Writes no saves.
##
## godot --path . --script res://tests/visual/minigames_r7_v_harness.gd -- --shots=<dir> [--only=flap|cloak]
##       [--bg_flap=<png>] [--bg_cloak=<png>] [--scale=1.5] [--hc=1] [--tag=<suffix>]

const GAMES := [
	["flap", "veltrava.station.flap_board", "res://scenes/ui/minigames/FlapBoard.tscn"],
	["cloak", "veltrava.hall.cloak_tokens", "res://scenes/ui/minigames/Cloakroom.tscn"],
]

var _out := ""
var _only := ""
var _tag := ""
var _bgs := {}
var _scale := 1.0
var _hc := false
var _ui: Control
var _bg: TextureRect
var _fail := 0


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			_out = a.substr(8)
		elif a.begins_with("--only="):
			_only = a.substr(7)
		elif a.begins_with("--bg_flap="):
			_bgs["flap"] = a.substr(10)
		elif a.begins_with("--bg_cloak="):
			_bgs["cloak"] = a.substr(11)
		elif a.begins_with("--scale="):
			_scale = float(a.substr(8))
		elif a.begins_with("--hc="):
			_hc = a.substr(5) == "1"
		elif a.begins_with("--tag="):
			_tag = a.substr(6)
	if _out == "":
		_out = "user://minigames_r7_v_shots"
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
	await _frames(2)
	_key(k, false)
	await _frames(3)


func _taps(keys: Array) -> void:
	for k in keys:
		await _tap(int(k))


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
	for g in GAMES:
		if _only != "" and _only != g[0]:
			continue
		var bgp := str(_bgs.get(g[0], ""))
		var img := Image.load_from_file(bgp) if bgp != "" else null
		_bg.texture = ImageTexture.create_from_image(img) if img != null else null
		var mg: Node = load(g[2]).instantiate()
		_ui.add_child(mg)
		var res := {"done": 0, "ok": false}
		mg.finished.connect(func(ok: bool):
			res["done"] = int(res["done"]) + 1
			res["ok"] = ok)
		mg.open({"explore_id": g[1], "auto": false})
		await _wait(0.7)
		var pn: Control = mg.get("_panel")
		print("LAYOUT %s panel=%s min=%s" % [g[0], pn.get_global_rect(), pn.get_combined_minimum_size()])
		await _shot("r7v_%s_1_start" % g[0])
		match g[0]:
			"flap":
				# turn the hour drum to 8 first (the natural left-to-right way), then the tens: the hour runs off
				for i in 15:
					await _tap(KEY_UP)
				await _taps([KEY_RIGHT, KEY_UP])
				await _wait(0.6)
				await _shot("r7v_flap_1b_coupling")
				await _taps([KEY_ENTER])
				await _wait(0.5)
				await _taps([KEY_ENTER])
				await _wait(0.6)
			"cloak":
				await _taps([KEY_ENTER])          # hook 12 for token 12: the obvious wrong guess
				await _wait(1.0)
				await _taps([KEY_RIGHT, KEY_RIGHT, KEY_ENTER])
				await _wait(1.0)
		print("HINT %s fails=%d hint_visible=%s" % [g[0], int(mg.get("fails")), mg.get("_hint_box").visible])
		await _shot("r7v_%s_2_hint" % g[0])
		var t0 := Time.get_ticks_msec()
		await mg.demo_solve()
		print("SOLVE %s demo_solve took %.1f s, solved=%s" % [g[0], (Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
		await _wait(0.5)
		await _shot("r7v_%s_3_solved" % g[0])
		var guard := 0.0
		while int(res["done"]) == 0 and guard < 8.0:
			await _wait(0.1)
			guard += 0.1
		await _wait(0.3)
		print("RESULT %s finished=%d success=%s" % [g[0], int(res["done"]), res["ok"]])
		if not (int(res["done"]) == 1 and res["ok"]):
			_fail += 1
		if is_instance_valid(mg):
			mg.queue_free()
		await _frames(5)
	print("MINIGAMES R7V HARNESS ", "OK" if _fail == 0 else "FAILED (%d)" % _fail)
	quit(0 if _fail == 0 else 1)
