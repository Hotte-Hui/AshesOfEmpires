extends Node
## Visual check of the registry art (L_C3_Registry, all four looks) in the real renderer. Boots Main in capture
## mode (no autosave, no intro), then for every look switches the level's scene id (the art follows level_id, see
## registry_level.gd) and for every camera position saves the composed 1920x1080 window (HUD hidden).
##   godot --path . res://scripts/levels/c3p2_archive/registry_shots.tscn -- --scene=L_C3_RegistryA --char=alexei \
##         --capture=<dir>/boot.png --frames=100000 --rs-out=<abs dir> [--symbols=0|1] [--rs-prefix=x_]
##         [--rs-looks=a,b,c,d] [--rs-cams=0,320,640,960,1280] [--rs-wait=40] [--rs-done=obj,obj] [--rs-choice=obj:id]
##         [--rs-live=1]  (afterwards: the live C -> D cross-fade at camera 640, shots at 0.3 / 1.3 / 2.4 / 3.8 s)
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## Prints RS_SHOT <path> per image and RS_DONE shots=<n> problems=<n>; exit code 0 = all shots taken.

const MAIN := "res://scenes/main/Main.tscn"
const SCENE_OF := {"a": "L_C3_RegistryA", "b": "L_C3_RegistryB", "c": "L_C3_RegistryC", "d": "L_C3_RegistryD"}

var out_dir := ""
var prefix := ""
var looks: Array = ["a", "b", "c", "d"]
var cams: Array = [0, 320, 640, 960, 1280]
var wait_frames := 40
var extra_done: Array = []
var choices := {}
var live := false
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--rs-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--rs-prefix="):
			prefix = a.substr(12)
		elif a.begins_with("--rs-looks="):
			looks = Array(a.substr(11).split(",", false))
		elif a.begins_with("--rs-cams="):
			cams = []
			for c in a.substr(10).split(",", false):
				cams.append(int(c))
		elif a.begins_with("--rs-wait="):
			wait_frames = int(a.substr(10))
		elif a.begins_with("--rs-done="):
			extra_done = Array(a.substr(10).split(",", false))
		elif a == "--rs-live=1":
			live = true
		elif a.begins_with("--rs-choice="):
			for pair in a.substr(12).split(",", false):
				var kv := pair.split(":")
				if kv.size() == 2:
					choices[kv[0]] = kv[1]
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://registry_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0 + looks.size() * cams.size() * 6.0
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("RS_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("RS_PROBLEM the Game autoload is missing")
		get_tree().quit(2)
		return
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null or not Game.level.has_method("refresh"):
		problems.append("registry level/player never appeared")
		_finish()
		return
	await _frames(20)
	var lvl: Node = Game.level
	for lk in looks:
		lvl.set("level_id", SCENE_OF.get(lk, "L_C3_RegistryA"))
		if not extra_done.is_empty() or not choices.is_empty():
			var d := {}
			for o in extra_done:
				d[o] = true
			lvl.set("done_override", d)
			lvl.set("choice_override", choices)
		lvl.refresh(true)
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and hud.has_method("hide_hud"):
			hud.hide_hud()
		for cx in cams:
			var p: Node2D = Game.player
			p.global_position = Vector2(float(cx) + 300.0, 300.0)
			Game.camera.cinematic = true
			Game.camera.set_top_left(Vector2(float(cx), 0.0))
			await _frames(wait_frames)
			await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			var path := out_dir.path_join("%slook_%s_cam%04d.png" % [prefix, lk, int(cx)])
			img.save_png(path)
			shots += 1
			print("RS_SHOT ", path, " look=", lvl.call("look"))
	if live:
		await _live(lvl)
	_finish()


## The fire reaches the Karteisaal while the player watches (c3e_reach_konrad): D fades in over C, no dip.
func _live(lvl: Node) -> void:
	lvl.set("level_id", SCENE_OF["c"])
	lvl.set("done_override", {})
	lvl.call("refresh", true)
	Game.player.global_position = Vector2(940.0, 300.0)
	Game.camera.cinematic = true
	Game.camera.set_top_left(Vector2(640.0, 0.0))
	await _frames(30)
	lvl.set("done_override", {"c3e_reach_konrad": true})
	lvl.call("refresh", false)
	var t0 := Time.get_ticks_msec()
	for at in [0.3, 1.3, 2.4, 3.8]:
		while Time.get_ticks_msec() - t0 < int(at * 1000.0):
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var path := out_dir.path_join("%slive_c_to_d_%02d.png" % [prefix, int(at * 10)])
		img.save_png(path)
		shots += 1
		print("RS_SHOT ", path, " look=", lvl.call("look"))


func _finish() -> void:
	for pr in problems:
		print("RS_PROBLEM ", pr)
	print("RS_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
