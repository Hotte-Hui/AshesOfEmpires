extends Node
## Windowed in-game check of the round-7 mini-games (owner: minigames_r7_kb). Boots the real Main scene into
## L_A1_Railyard (Morsetaster) or L_M1_Archive (Rohrpost) in capture mode, puts the protagonist on the find's
## hotspot, captures the HUD prompt, opens the find through Game.interact() — i.e. the real §12.8 path
## Game._do_discover -> _run_minigame — and then drives the mini-game ONLY with synthetic key events through UIRoot:
## two wrong inputs (refusal + hint), then demo_solve() (the real-input driver's path) while shots are taken at
## fixed moments; finally the DiscoveryView of the find. Writes PNGs only into --r7-out=<absolute dir>.
##   godot --path . res://tests/visual/minigames_r7_kb_shots.tscn -- --scene=L_A1_Railyard \
##         --capture=<dir>/boot.png --frames=100000 --r7-out=<dir> [--r7-ts=1.5] [--r7-hc=1] [--r7-tag=x]
## Exit code 0 = prompt focus right, mini-game finished(true), find recorded; 1 otherwise. Writes no saves.

const MAIN := "res://scenes/main/Main.tscn"
const TARGETS := {"L_A1_Railyard": "ExpMorse", "L_M1_Archive": "ExpRohrpost"}

var out_dir := ""
var tag := ""
var problems: Array = []
var shots := 0
var _ts := 0.0
var _hc := false


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--r7-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--r7-ts="):
			_ts = float(a.substr(8))
		elif a.begins_with("--r7-hc="):
			_hc = a.substr(8) == "1"
		elif a.begins_with("--r7-tag="):
			tag = a.substr(9) + "_"
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://minigames_r7_kb_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _wait(t: float) -> void:
	await get_tree().create_timer(t, true).timeout


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(tag + label + ".png")
	img.save_png(path)
	shots += 1
	print("R7_SHOT ", path)


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


func _until(cond: Callable, timeout: float) -> bool:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(timeout * 1000.0):
		if cond.call():
			return true
		await get_tree().process_frame
	return bool(cond.call())


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 900:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	if _ts > 0.0:
		Settings.values["text_scale"] = _ts
		Kit_refresh()
	if _hc:
		Settings.values["high_contrast"] = true
	await _frames(40)
	var lid := str(Game.level.level_id)
	var it: Node = Game.level.get_node_or_null("Playfield/" + str(TARGETS.get(lid, "")))
	if it == null:
		problems.append("no find node in " + lid)
		_finish()
		return
	var p: Node2D = Game.player
	p.global_position = it.global_position + Vector2(-6, 2)
	Game.camera.snap_now()
	await _frames(30)
	if p.focus != it:
		problems.append("%s: focus is %s, not the find" % [it.name, p.focus.name if p.focus else "none"])
	await _shot("prompt_" + str(it.name))
	Game.interact(it)
	var mg: Node = null
	if not await _until(func():
			for n in get_tree().get_nodes_in_group("minigame"):
				if is_instance_valid(n) and n.get("is_open") == true:
					return true
			return false, 5.0):
		problems.append("the mini-game did not open")
		_finish()
		return
	for n in get_tree().get_nodes_in_group("minigame"):
		if is_instance_valid(n) and n.get("is_open") == true:
			mg = n
	var res := {"done": false, "ok": false}
	mg.finished.connect(func(ok: bool):
		res["done"] = true
		res["ok"] = ok)
	if lid == "L_A1_Railyard":
		await _morse(mg)
	else:
		await _tube(mg)
	if not await _until(func(): return res["done"], 12.0):
		problems.append("finished never arrived")
	elif not res["ok"]:
		problems.append("finished(false)")
	# the find itself (DiscoveryView)
	await _wait(1.6)
	await _shot("view_find")
	var view = Game.ui.get("discovery") if Game.ui else null
	if view and view.get("is_open") == true:
		view.close()
	await _until(func(): return not Game.busy, 6.0)
	if not Explore.is_found(str(it.get("explore_id"))):
		problems.append("the find was not recorded")
	_finish()


func Kit_refresh() -> void:
	var kit = load("res://scripts/ui/ui_kit.gd")
	kit.refresh_text_scale()


func _morse(mg: Node) -> void:
	await _wait(1.0)
	await _shot("morse_1_open")
	await _wait(5.2)
	await _shot("morse_2_routine")
	await _until(func(): return mg.logic.can_pick(), 30.0)
	await _wait(0.3)
	await _tap(KEY_ENTER)              # cursor on А: wrong for Н
	await _wait(0.2)
	await _tap(KEY_ENTER)
	await _wait(0.35)
	await _shot("morse_3_refused_hint")
	if int(mg.get("fails")) < 2 or not mg.get("_hint_box").visible:
		problems.append("morse: two wrong letters did not show the hint (fails %d)" % int(mg.get("fails")))
	var state := {"mid": false, "key": false}
	mg.demo_solve()                     # runs on its own (synthetic keys); shots are taken meanwhile
	var t0 := Time.get_ticks_msec()
	while not mg.solved and Time.get_ticks_msec() - t0 < 90000:
		if not state["mid"] and int(mg.logic.cursor) >= 6:
			state["mid"] = true
			await _shot("morse_4_decoding")
		if not state["key"] and float(mg.get("_press_t")) > 0.32:
			state["key"] = true
			await _shot("morse_5_receipt_dash")
		await get_tree().process_frame
	await _wait(0.5)
	await _shot("morse_6_solved")


func _tube(mg: Node) -> void:
	await _wait(1.0)
	await _shot("tube_1_open")
	await _tap(KEY_ENTER)              # board 1 as found: the capsule goes to the registry
	await _until(func(): return mg.get("_dist") > 60.0, 5.0)
	await _shot("tube_2_travel")
	await _until(func(): return str(mg.get("_state")) == "returning", 8.0)
	await _wait(0.2)
	await _shot("tube_3_wrong")
	await _until(func(): return str(mg.get("_state")) == "ready", 8.0)
	await _tap(KEY_SPACE)              # knob 1 to W-N: now the capsule reaches Abt. III
	await _tap(KEY_ENTER)
	await _until(func(): return str(mg.get("_state")) == "returning", 10.0)
	await _wait(0.3)
	await _shot("tube_4_hint")
	if int(mg.get("fails")) < 2 or not mg.get("_hint_box").visible:
		problems.append("tube: two wrong capsules did not show the hint")
	await _until(func(): return str(mg.get("_state")) == "ready", 8.0)
	var state := {"delivered": false, "board2": false, "board3": false, "travel3": false}
	mg.demo_solve()
	var t0 := Time.get_ticks_msec()
	while not mg.solved and Time.get_ticks_msec() - t0 < 120000:
		if not state["delivered"] and str(mg.get("_state")) == "delivered" and float(mg.get("_state_t")) > 0.6:
			state["delivered"] = true
			await _shot("tube_5_delivered")
		if not state["board2"] and int(mg.logic.board_i) == 1 and str(mg.get("_state")) == "ready":
			state["board2"] = true
			await _shot("tube_5b_board2")
		if not state["board3"] and int(mg.logic.board_i) == 2 and str(mg.get("_state")) == "ready":
			state["board3"] = true
			await _shot("tube_6_board3")
		if not state["travel3"] and int(mg.logic.board_i) == 2 and str(mg.get("_state")) == "travel" and float(mg.get("_dist")) > 200.0:
			state["travel3"] = true
			await _shot("tube_7_board3_travel")
		await get_tree().process_frame
	await _wait(0.6)
	await _shot("tube_8_solved")


func _finish() -> void:
	for pr in problems:
		print("R7_PROBLEM ", pr)
	print("R7_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
