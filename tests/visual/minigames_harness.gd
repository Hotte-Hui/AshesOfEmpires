extends SceneTree
## Windowed capture harness for the §12.8 mini-games (owner: minigames). Builds the real UIRoot over a game
## screenshot (Karsk / Berlin) and, for each mini-game, opens it the way Game._run_minigame does
## (ui.add_child + open(ctx)), then drives it ONLY with synthetic key events routed through UIRoot:
##   1_start  as opened
##   2_hint   after two refused moves (shunting: train too long for the headshunt; chess: two wrong first moves;
##            radio: caught twice by the porter)
##   3_solved right after demo_solve() (the real-input driver's path), before the solved hold ends
## and checks that finished(true) arrives. Writes no saves.
##
## godot --path . --script res://tests/visual/minigames_harness.gd -- --shots=<dir> [--only=shunting|chess|radio]

const GAMES := [
	["shunting", "karsk.shunting", "res://scenes/ui/minigames/Shunting.tscn", "res://documentation/screenshots/03_karsk_prompt.png"],
	["chess", "karsk.chess", "res://scenes/ui/minigames/ChessProblem.tscn", "res://documentation/screenshots/03_karsk_prompt.png"],
	["radio", "berlin.radio_dial", "res://scenes/ui/minigames/RadioDial.tscn", "res://documentation/screenshots/13_berlin_office.png"],
]

var _out := ""
var _only := ""
var _ui: Control
var _bg: TextureRect
var _fail := 0


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			_out = a.substr(8)
		elif a.begins_with("--only="):
			_only = a.substr(7)
	if _out == "":
		_out = "user://minigames_shots"
	DirAccess.make_dir_recursive_absolute(_out)
	# like Main: the backdrop and the UI live on canvas layers sized to the 1920x1080 logical viewport
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
	var path := _out.path_join(name + ".png")
	img.save_png(path)
	print("SHOT ", path, " ", img.get_size())


func _run() -> void:
	await _frames(12)
	for g in GAMES:
		if _only != "" and _only != g[0]:
			continue
		var img := Image.load_from_file(ProjectSettings.globalize_path(g[3]))
		_bg.texture = ImageTexture.create_from_image(img) if img != null else null
		var mg: Node = load(g[2]).instantiate()
		_ui.add_child(mg)
		var res := {"done": false, "ok": false}
		mg.finished.connect(func(ok: bool):
			res["done"] = true
			res["ok"] = ok)
		mg.open({"explore_id": g[1], "auto": false})
		await _wait(0.6)
		var pn: Control = mg.get("_panel")
		print("LAYOUT %s root=%s vp=%s win=%s scale=%s mg=%s panel=%s min=%s" % [g[0], root.size, root.get_visible_rect().size,
			DisplayServer.window_get_size(), root.content_scale_factor, (mg as Control).get_global_rect(), pn.get_global_rect(), pn.get_combined_minimum_size()])
		await _shot("minigames_%s_1_start" % g[0])
		match g[0]:
			"shunting":
				await _taps([KEY_DOWN, KEY_RIGHT])
				await _wait(2.0)
				await _taps([KEY_RIGHT, KEY_RIGHT, KEY_ENTER])
				await _wait(2.0)
				await _taps([KEY_UP, KEY_RIGHT])
				await _wait(2.5)
				await _taps([KEY_RIGHT, KEY_ENTER, KEY_ENTER])
			"chess":
				await _taps([KEY_LEFT, KEY_LEFT, KEY_UP, KEY_UP, KEY_UP, KEY_ENTER, KEY_UP, KEY_UP, KEY_UP, KEY_UP, KEY_ENTER])
				await _wait(0.4)
				await _taps([KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_DOWN, KEY_DOWN, KEY_ENTER,
					KEY_LEFT, KEY_LEFT, KEY_UP, KEY_ENTER])
				await _wait(0.3)
				await _taps([KEY_ENTER])      # pick the knight up again: shows its targets
			"radio":
				var warned := false
				for i in 2:
					_key(KEY_RIGHT, true)
					await _wait(1.6)
					_key(KEY_RIGHT, false)
					var t := 0.0
					while int(mg.get("fails")) <= i and t < 30.0:
						await _wait(0.25)
						t += 0.25
						if i == 1 and str(mg.logic.porter) == "lowering" and not warned:
							warned = true
							await _shot("minigames_radio_2b_warning")
				await _wait(0.5)
		await _wait(0.5)
		print("HINT %s fails=%d hint_visible=%s" % [g[0], int(mg.get("fails")), mg.get("_hint_box").visible])
		await _shot("minigames_%s_2_hint" % g[0])
		var t0 := Time.get_ticks_msec()
		await mg.demo_solve()
		print("SOLVE %s demo_solve took %.1f s, solved=%s" % [g[0], (Time.get_ticks_msec() - t0) / 1000.0, mg.get("solved")])
		await _wait(0.45)
		await _shot("minigames_%s_3_solved" % g[0])
		var guard := 0.0
		while not res["done"] and guard < 8.0:
			await _wait(0.1)
			guard += 0.1
		print("RESULT %s finished=%s success=%s paused_after=%s" % [g[0], res["done"], res["ok"], paused])
		if not (res["done"] and res["ok"]):
			_fail += 1
		if is_instance_valid(mg):
			mg.queue_free()
		await _frames(5)
	print("MINIGAMES HARNESS ", "OK" if _fail == 0 else "FAILED (%d)" % _fail)
	quit(0 if _fail == 0 else 1)
