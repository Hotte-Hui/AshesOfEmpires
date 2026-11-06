extends Node
## Visual check of the Karsk depot art (L_C4P2_Karsk, scenes A and B) in the real renderer. Boots Main in capture
## mode (no autosave, no intro) on the scene given by --scene, then for every camera position saves the composed
## 1920x1080 window (HUD hidden), optionally with story states applied and one shot with the passing train (A).
##   godot --path . res://tests/visual/c4p2_karsk_shots.tscn -- --scene=L_C4P2_KarskA --char=alexei \
##         --capture=<dir>/boot.png --frames=100000 --ts-out=<abs dir> [--ts-cams=0,238] [--ts-done=obj,obj]
##         [--ts-prefix=a_] [--ts-train=1] [--ts-train-at=420] [--ts-wait=40] [--ts-player=x] [--symbols=0|1]
## The train shot is taken at the last camera with the loco at screen x --ts-train-at (default 420: at camera
## 238 the far embankment shows in the gap between the coal stage and the roundhouse, screen 366-474).
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## Prints TS_SHOT <path> per image and TS_DONE shots=<n> problems=<n>; exit code 0 = all shots taken.

const MAIN := "res://scenes/main/Main.tscn"

var out_dir := ""
var prefix := ""
var cams: Array = [0]
var wait_frames := 40
var extra_done: Array = []
var train := false
var train_at := 420.0
var player_x := -1.0
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--ts-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--ts-prefix="):
			prefix = a.substr(12)
		elif a.begins_with("--ts-cams="):
			cams = []
			for c in a.substr(10).split(",", false):
				cams.append(int(c))
		elif a.begins_with("--ts-wait="):
			wait_frames = int(a.substr(10))
		elif a.begins_with("--ts-done="):
			extra_done = Array(a.substr(10).split(",", false))
		elif a == "--ts-train=1":
			train = true
		elif a.begins_with("--ts-train-at="):
			train_at = float(a.substr(14))
		elif a.begins_with("--ts-player="):
			player_x = float(a.substr(12))
	if out_dir == "":
		problems.append("--ts-out missing")
		_finish()
		return
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0 + cams.size() * 6.0 + (16.0 if train else 0.0)
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("TS_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(prefix + name + ".png")
	img.save_png(path)
	shots += 1
	print("TS_SHOT ", path, " look=", Game.level.call("look") if Game.level and Game.level.has_method("look") else "?")


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("depot level/player never appeared")
		_finish()
		return
	await _frames(20)
	var lvl: Node = Game.level
	if not extra_done.is_empty():
		var d := {}
		for o in extra_done:
			d[o] = true
		lvl.set("done_override", d)
		lvl.call("refresh", true)
	var hud = Game.ui.get("hud") if Game.ui else null
	if hud and hud.has_method("hide_hud"):
		hud.hide_hud()
	var b: Rect2 = lvl.call("get_camera_bounds")
	for cx in cams:
		var c := clampf(float(cx), b.position.x, maxf(b.position.x, b.end.x - 640.0))
		Game.player.global_position = Vector2(player_x if player_x >= 0.0 else c + 300.0, 300.0)
		Game.camera.cinematic = true
		Game.camera.set_top_left(Vector2(c, 0.0))
		await _frames(wait_frames)
		await _shot("cam%04d" % int(c))
	if train:
		var tr: Node = null
		for n in lvl.playfield.get_children():
			if n.get_script() != null and str(n.get_script().resource_path).ends_with("karsk_depot_train.gd"):
				tr = n
		if tr == null:
			problems.append("no depot train in this scene")
		else:
			tr.call("_start")
			# Where a fresh train starts depends on its direction and on the camera; for the picture it is put
			# straight into the current view (loco near the middle) and runs on for a moment so its smoke trails --
			# the 'train' shot is never empty, whatever --ts-cams said.
			var par := float(tr.get("parallax"))
			var view_x: float = (tr.call("cam_pos") as Vector2).x * par
			var ln := float(tr.get("_len"))
			var moving_left := float(tr.get("_dir")) < 0.0
			var run := 2.0 * float(tr.get("speed"))
			var x := view_x + train_at + run if moving_left else view_x + train_at - run - ln
			tr.set("_x", x)
			var cars = tr.get("_cars")
			if cars is Node2D:
				(cars as Node2D).position = Vector2(x, 0).round()
			await get_tree().create_timer(2.0).timeout
			var loco_x := float(tr.get("_x")) - view_x + (0.0 if moving_left else ln)
			if loco_x < 0.0 or loco_x > 640.0:
				problems.append("train not in view at the shot (loco at screen x %d)" % int(loco_x))
			await _shot("train")
	_finish()


func _finish() -> void:
	for pr in problems:
		print("TS_PROBLEM ", pr)
	print("TS_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
