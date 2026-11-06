extends Node
## Visual check of the annex art (L_C4_Annex, both Story scenes) in the real renderer. Boots Main in capture mode
## (no autosave, no intro), loads each scene with a fresh level load (the scene filter of annex_level.gd is decided
## at load), optionally marks objectives done for the art (done_override), and saves the composed 1920x1080 window
## (HUD hidden) for every camera stop.
##   godot --path . res://scripts/levels/c4/annex_shots.tscn -- --scene=L_C4_AnnexA --char=konrad \
##         --capture=<dir>/boot.png --frames=100000 --as-out=<abs dir> [--symbols=0|1] [--as-prefix=x_]
##         [--as-shots=A:0,A:206,B:846,B:1066,B:1280] [--as-done=obj,obj] [--as-wait=40] [--as-player=x]
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## Prints AS_SHOT <path> per image and AS_DONE shots=<n> problems=<n>; exit code 0 = all shots taken.

const MAIN := "res://scenes/main/Main.tscn"
const SCENE_OF := {"A": "L_C4_AnnexA", "B": "L_C4_AnnexB"}
const PLAYER_X := {"A": 300.0, "B": 1000.0}

var out_dir := ""
var prefix := ""
var shots_spec: Array = ["A:0", "A:206", "B:846", "B:1066", "B:1280"]
var wait_frames := 40
var extra_done: Array = []
var player_x := -1.0
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--as-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--as-prefix="):
			prefix = a.substr(12)
		elif a.begins_with("--as-shots="):
			shots_spec = Array(a.substr(11).split(",", false))
		elif a.begins_with("--as-wait="):
			wait_frames = int(a.substr(10))
		elif a.begins_with("--as-done="):
			extra_done = Array(a.substr(10).split(",", false))
		elif a.begins_with("--as-player="):
			player_x = float(a.substr(12))
	if out_dir == "":
		problems.append("--as-out=<abs dir> missing (the harness never writes into user://)")
		_finish.call_deferred()
		return
	DirAccess.make_dir_recursive_absolute(out_dir)
	var limit := 60.0 + shots_spec.size() * 8.0
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("AS_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("AS_PROBLEM the Game autoload is missing")
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
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	await _frames(20)
	var cur := ""
	for spec in shots_spec:
		var kv: PackedStringArray = str(spec).split(":")
		if kv.size() != 2 or not SCENE_OF.has(kv[0]):
			problems.append("bad shot spec " + str(spec))
			continue
		var sc: String = kv[0]
		if sc != cur:
			Game.set("_force_reload", true)
			await Game.goto_level(SCENE_OF[sc], "", false)
			await _frames(10)
			cur = sc
			var lvl: Node = Game.level
			if lvl == null or str(lvl.get("level_id")) != SCENE_OF[sc]:
				problems.append("scene %s did not load" % SCENE_OF[sc])
				continue
			if not extra_done.is_empty():
				var d := {}
				for o in extra_done:
					d[o] = true
				lvl.set("done_override", d)
				lvl.call("refresh", true)
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and hud.has_method("hide_hud"):
			hud.hide_hud()
		var cx := float(kv[1])
		var p: Node2D = Game.player
		p.global_position = Vector2(player_x if player_x >= 0.0 else clampf(cx + 300.0, PLAYER_X[sc], 1880.0), 300.0)
		Game.camera.cinematic = true
		Game.camera.set_top_left(Vector2(cx, 0.0))
		await _frames(wait_frames)
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var path := out_dir.path_join("%s%s_cam%04d.png" % [prefix, sc, int(cx)])
		img.save_png(path)
		shots += 1
		print("AS_SHOT ", path, " look=", Game.level.call("look"), " bounds=", Game.level.get_camera_bounds())
	_finish()


func _finish() -> void:
	for pr in problems:
		print("AS_PROBLEM ", pr)
	print("AS_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
