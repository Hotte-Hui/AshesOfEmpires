extends Node
## Visual check of the Veltrava station (L_C3_Station, owner: env_veltrava_station art). Boots the real Main
## scene in capture mode (Game: no autosave, no intro, no focus pause), then for every shot places Alexei,
## moves the camera (cinematic top-left), optionally shows the post-control state (Elena at the café instead of
## at counter 2) and saves the composed 1920x1080 window (HUD hidden) into --vs-out=<absolute dir>.
##   godot --path . res://tests/visual/c3_station_shots.tscn -- --scene=L_C3_Station \
##         --capture=<dir>/boot.png --frames=100000 --vs-out=<dir> [--symbols=0|1] [--vs-prefix=after_]
##         [--vs-only=cam0000,cam0640] [--vs-wait=90] [--vs-hud=1] [--vs-seconds=0]
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing first.)
## --vs-seconds > 0 waits real time per shot (catch the passing train / walkers); exit code 0 = all shots taken.

const MAIN := "res://scenes/main/Main.tscn"
## label: [camera top-left x, player x, player y, face_left, post_control]
const SHOTS := {
	"cam0000": [0, 140, 300, false, false],
	"cam0260": [260, 430, 304, false, false],
	"cam0480": [480, 640, 296, false, false],
	"cam0700": [700, 905, 300, true, false],
	"cam0960": [960, 1180, 300, false, false],
	"cam1280": [1280, 1560, 306, false, false],
	"cafe1280": [1280, 1612, 304, false, true],
}

var out_dir := ""
var prefix := ""
var only: Array = []
var wait_frames := 90
var wait_seconds := 0.0
var keep_hud := false
var shots := 0
var problems: Array = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--vs-out="):
			out_dir = a.substr(9)
		elif a.begins_with("--vs-only="):
			only = Array(a.substr(10).split(",", false))
		elif a.begins_with("--vs-prefix="):
			prefix = a.substr(12)
		elif a.begins_with("--vs-wait="):
			wait_frames = int(a.substr(10))
		elif a.begins_with("--vs-seconds="):
			wait_seconds = float(a.substr(13))
		elif a == "--vs-hud=1":
			keep_hud = true
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://c3_station_shots")
	DirAccess.make_dir_recursive_absolute(out_dir)
	# watchdog: never hang (e.g. when another script of the project does not parse and Game is missing)
	var limit := 60.0 + SHOTS.size() * (8.0 + wait_seconds)
	get_tree().create_timer(limit, true, false, true).timeout.connect(func() -> void:
		print("VS_PROBLEM watchdog: gave up after %d s" % int(limit))
		get_tree().quit(3))
	if get_node_or_null("/root/Game") == null:
		print("VS_PROBLEM the Game autoload is missing (a project script failed to parse?)")
		get_tree().quit(2)
		return
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out_dir.path_join(prefix + label + ".png")
	img.save_png(path)
	shots += 1
	print("VS_SHOT ", path)


func _set_post_control(on: bool) -> void:
	# presentation only: swap Elena between counter 2 and the café (as after c3a_pass_control)
	var pf: Node = Game.level.get_node_or_null("Playfield")
	if pf == null:
		return
	for pair in [["ElenaControl", not on], ["ElenaCafe", on]]:
		var n: Node = pf.get_node_or_null(str(pair[0]))
		if n is CanvasItem:
			(n as CanvasItem).visible = bool(pair[1])
			n.process_mode = Node.PROCESS_MODE_INHERIT if bool(pair[1]) else Node.PROCESS_MODE_DISABLED


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
	var labels: Array = only if not only.is_empty() else SHOTS.keys()
	for label in labels:
		if not SHOTS.has(label):
			problems.append("unknown shot " + str(label))
			continue
		var s: Array = SHOTS[label]
		var hud = Game.ui.get("hud") if Game.ui else null
		if hud and not keep_hud and hud.has_method("hide_hud"):
			hud.hide_hud()
		_set_post_control(bool(s[4]))
		var p: Node2D = Game.player
		p.global_position = Vector2(float(s[1]), float(s[2]))
		if p.has_method("face"):
			p.face(-1 if bool(s[3]) else 1)
		Game.camera.cinematic = true
		Game.camera.set_top_left(Vector2(float(s[0]), 0.0))
		if wait_seconds > 0.0:
			var until := Time.get_ticks_msec() + int(wait_seconds * 1000.0)
			while Time.get_ticks_msec() < until:
				await get_tree().process_frame
		else:
			await _frames(wait_frames)
		await _shot(str(label))
	_finish()


func _finish() -> void:
	for pr in problems:
		print("VS_PROBLEM ", pr)
	print("VS_DONE shots=%d problems=%d" % [shots, problems.size()])
	get_tree().quit(0 if problems.is_empty() else 1)
