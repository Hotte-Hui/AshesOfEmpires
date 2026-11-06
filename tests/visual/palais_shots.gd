extends Node
## Visual harness for the Palais der Kommission (L_C3_Hall, owner: the palais art stream).
## Boots the real Main scene (Forward+, hi-res world path, grade, lights) into L_C3_Hall in capture mode
## (Game: no autosave, no intro pan, no focus pause), drives the Story through the public API to the wanted
## stage (so the story NPCs and the HUD objective are the real ones), places Konrad and takes window shots
## along the level.  Writes PNGs only into --px-out=<absolute dir>; never touches save slots.
##   godot --path . res://tests/visual/palais_shots.tscn -- --scene=L_C3_Hall --capture=<dir>/boot.png \
##         --frames=100000 --px-out=<dir> [--px-stage=arrival|booth] [--px-cams=0,320,640,960,1280]
##         [--px-player=<x>,<x>,...] [--px-hud=0] [--px-wait=40] [--px-prefix=shot] [--symbols=0|1]
##         [--px-seq=<frames>,<count>]   (several shots per camera, <frames> apart: animation check)
## stage "arrival": just arrived (Kessler, Elena, Voronova, typist, journalist); "booth": booth 2 inspected
## (Elena gone, Alexei waits in front of booth 3).  --px-player: Konrad's feet x per camera (default: cam+250).
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)

const MAIN := "res://scenes/main/Main.tscn"
const KIT := preload("res://tests/support/test_kit.gd")

var out_dir := ""
var stage := "arrival"
var cams: Array = [0.0, 320.0, 640.0, 960.0, 1280.0]
var players: Array = []
var hud := true
var wait := 40
var prefix := "shot"
var seq_frames := 0
var seq_count := 1
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		var kv := a.substr(2).split("=", true, 1) if a.begins_with("--") else PackedStringArray()
		if kv.size() < 2:
			continue
		match kv[0]:
			"px-out":
				out_dir = kv[1]
			"px-stage":
				stage = kv[1]
			"px-cams":
				cams = Array(kv[1].split(",", false)).map(func(s: String) -> float: return float(s))
			"px-player":
				players = Array(kv[1].split(",", false)).map(func(s: String) -> float: return float(s))
			"px-hud":
				hud = kv[1] != "0"
			"px-wait":
				wait = int(kv[1])
			"px-prefix":
				prefix = kv[1]
			"px-seq":
				var p := kv[1].split(",")
				seq_frames = int(p[0])
				seq_count = int(p[1]) if p.size() > 1 else 4
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://palais_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(label + ".png")
	img.save_png(path)
	print("PX_SHOT ", path)


func _drive_story() -> void:
	var kit := KIT.new()
	var g: Node = Story
	kit.play_a1(g, "share_with_irina")
	kit.play_m1(g, "preserve_evidence")
	for s in g.pending_cinematics():
		kit.step(g.consume_cinematic(s, true), "cinematic " + s)
	kit.play_c3a(g, "ask_elena")
	for s in g.pending_cinematics():
		kit.step(g.consume_cinematic(s, true), "cinematic " + s)
	if stage == "booth":
		kit.play_dialogue(g, "c3b_arrival")
		kit.step(g.inspect("c3b_inspect_seating"), "inspect seating")
		kit.step(g.inspect("c3b_inspect_log"), "inspect booth log")
		kit.step(g.solve_puzzle("c3b_solve_protocol", KIT.C3_PROTOCOL.duplicate()), "solve protocol")
		kit.step(g.inspect("c3b_inspect_booth"), "inspect booth 2")
	problems.append_array(kit.failures)


func _run() -> void:
	var guard := 0
	while (Game.level == null or Game.player == null) and guard < 600:
		guard += 1
		await get_tree().process_frame
	if Game.level == null or Game.player == null:
		problems.append("level/player never appeared")
		_finish()
		return
	_drive_story()
	if not hud and Game.main and Game.main.get("ui_layer"):
		Game.main.ui_layer.visible = false
	await _frames(30)
	var p: Node2D = Game.player
	for i in cams.size():
		var cx: float = cams[i]
		var px: float = players[i] if i < players.size() else cx + 250.0
		p.global_position = Vector2(px, 300.0)
		Game.camera.cinematic = true
		Game.camera.set_top_left(Vector2(cx, 0.0))
		await _frames(wait)
		if seq_frames > 0:
			for k in seq_count:
				await _shot("%s_cam%04d_%02d" % [prefix, int(cx), k])
				await _frames(seq_frames)
		else:
			await _shot("%s_cam%04d" % [prefix, int(cx)])
	_finish()


func _finish() -> void:
	for pr in problems:
		printerr("PX_PROBLEM ", pr)
	print("PX_DONE problems=", problems.size())
	get_tree().quit(1 if not problems.is_empty() else 0)
