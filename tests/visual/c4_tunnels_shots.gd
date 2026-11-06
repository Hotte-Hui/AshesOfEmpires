extends Node
## Visual check of the Karsk tunnels art (L_C4_Tunnels, scenes A and C) in the real renderer. Boots Main in capture
## mode (no autosave, no intro) on the scene given by --scene, then for every camera position saves the composed
## 1920x1080 window (HUD hidden), optionally with story states applied and one shot in the middle of a passing train.
##   godot --path . res://tests/visual/c4_tunnels_shots.tscn -- --scene=L_C4_TunnelsA --char=alexei \
##         --capture=<dir>/boot.png --frames=100000 --ts-out=<abs dir> [--ts-cams=0,80] [--ts-done=obj,obj]
##         [--ts-prefix=a_] [--ts-train=1] [--ts-wait=40] [--ts-player=x]
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## Prints TS_SHOT <path> per image and TS_DONE shots=<n> problems=<n>; exit code 0 = all shots taken.

const MAIN := "res://scenes/main/Main.tscn"
const TunnelsLevel := preload("res://scripts/levels/c4/tunnels_level.gd")

var out_dir := ""
var prefix := ""
var cams: Array = [0]
var wait_frames := 40
var extra_done: Array = []
var train := false
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
		elif a.begins_with("--ts-player="):
			player_x = float(a.substr(12))
	if out_dir == "":
		problems.append("--ts-out missing")
		_finish()
		return
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0 + cams.size() * 6.0 + (12.0 if train else 0.0)
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
	if Game.level == null or Game.player == null or not Game.level.has_method("start_train"):
		problems.append("tunnels level/player never appeared")
		_finish()
		return
	await _frames(20)
	var lvl: Node = Game.level
	lvl.set("events_enabled", false)
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
		lvl.call("start_train")
		var t0 := Time.get_ticks_msec()
		for at in [1.3, 2.6]:                   # s into the vault's beat (it follows the sound by BEAT_DELAY)
			while Time.get_ticks_msec() - t0 < int((TunnelsLevel.BEAT_DELAY + at) * 1000.0):
				await get_tree().process_frame
			await _shot("train_%02d" % int(at * 10))
	_finish()


func _finish() -> void:
	for pr in problems:
		print("TS_PROBLEM ", pr)
	print("TS_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
