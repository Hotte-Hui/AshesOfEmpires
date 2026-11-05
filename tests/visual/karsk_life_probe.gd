extends Node2D
## Visual probe for the Karsk ambient actors (owner: karsk-env). Instances L_A1_Railyard at 3x without Main,
## stands in for Game.camera / Game.player, walks a fake player past the crows and the cat, forces a wind gust
## and a glint, and saves PNG frames to --out (nothing else is written; no saves, no autoplay).
##   godot --path . res://tests/visual/karsk_life_probe.tscn -- --out=C:/tmp/karsk_probe [--symbols=0|1]
## (No post grade here — compare colours with real --capture runs.)

const ProbeCam := preload("res://tests/visual/karsk_probe_cam.gd")

var _out := ""
var _cam: Camera2D
var _player: CharacterBody2D
var _level: Node2D
var _t := 0.0
var _steps: Array = []
var _orig_cam: Variant = null
var _orig_player: Variant = null


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			_out = a.substr(6)
	if _out == "":
		_out = OS.get_user_data_dir() + "/karsk_probe"
	DirAccess.make_dir_recursive_absolute(_out)
	get_window().mode = Window.MODE_WINDOWED
	get_window().size = Vector2i(1920, 1080)
	scale = Vector2(3, 3)
	_cam = ProbeCam.new()
	_cam.anchor_mode = Camera2D.ANCHOR_MODE_FIXED_TOP_LEFT
	add_child(_cam)
	_cam.make_current()
	_player = CharacterBody2D.new()
	var mark := ColorRect.new()
	mark.color = Color(0.9, 0.2, 0.9)
	mark.size = Vector2(4, 30)
	mark.position = Vector2(-2, -30)
	_player.add_child(mark)
	var g := get_node("/root/Game")
	_orig_cam = g.camera
	_orig_player = g.player
	g.camera = _cam
	_level = load("res://scenes/levels/L_A1_Railyard.tscn").instantiate()
	add_child(_level)
	(_level.get_node("Playfield") as Node2D).add_child(_player)
	g.player = _player
	# [time, cam_x, player(x, y), player speed (for velocity), capture name or "", action]
	_steps = [
		[0.0, 360.0, Vector2(420, 330), 0.0, "", ""],
		[1.6, 360.0, Vector2(420, 330), 0.0, "01_crows_idle", ""],
		[2.0, 360.0, Vector2(610, 322), 40.0, "", ""],
		[3.4, 360.0, Vector2(610, 322), 0.0, "02_crows_nervous", ""],
		[3.5, 360.0, Vector2(652, 258), 40.0, "", ""],
		[3.95, 360.0, Vector2(652, 258), 0.0, "03_crows_takeoff", ""],
		[4.6, 360.0, Vector2(652, 258), 0.0, "04_crows_flying", ""],
		[4.7, 700.0, Vector2(880, 330), 0.0, "", "gust"],
		[5.3, 700.0, Vector2(880, 330), 0.0, "05_gust_cat_sleep", ""],
		[5.4, 700.0, Vector2(1030, 312), 40.0, "", ""],
		[6.4, 700.0, Vector2(1030, 312), 0.0, "06_cat_awake", ""],
		[6.5, 1120.0, Vector2(1470, 312), 0.0, "", "glint"],
		[6.65, 1120.0, Vector2(1470, 312), 0.0, "07_stash_glint", ""],
		[7.0, 1150.0, Vector2(1470, 312), 0.0, "", "gust"],
		[7.7, 1150.0, Vector2(1470, 312), 0.0, "08_mitten_gust", ""],
		[8.0, 250.0, Vector2(200, 330), 0.0, "", "gust"],
		[8.8, 250.0, Vector2(200, 330), 0.0, "09_cache_laundry_gust", ""],
		[9.6, 0.0, Vector2(120, 330), 0.0, "", ""],
		[10.4, 0.0, Vector2(120, 330), 0.0, "12_cam0_windows", ""],
		[10.6, 1280.0, Vector2(1700, 330), 0.0, "", ""],
		[11.4, 1280.0, Vector2(1700, 330), 0.0, "13_cam1280_windows", ""],
		[16.0, 160.0, Vector2(200, 330), 0.0, "10_train", ""],
		[19.0, 160.0, Vector2(200, 330), 0.0, "11_train_later", ""],
		[19.2, 0.0, Vector2(200, 330), 0.0, "", "quit"],
	]


func _process(delta: float) -> void:
	_t += delta
	while not _steps.is_empty() and _t >= float(_steps[0][0]):
		var s: Array = _steps.pop_front()
		var cx: float = s[1]
		_cam.position = Vector2(cx, 0)        # camera is a child of the x3-scaled root
		_cam.drawn = Vector2(cx, 0)
		var target: Vector2 = s[2]
		_player.velocity = (target - _player.position).normalized() * float(s[3]) if float(s[3]) > 0.0 else Vector2.ZERO
		_player.position = target
		match str(s[5]):
			"gust":
				for n in _find(_level, "karsk_wind.gd"):
					n.set("_next", 0.0)
			"glint":
				for n in _find(_level, "karsk_glint.gd"):
					if str(n.get("mode")) == "glint":
						n.set("_wait", 0.0)
			"quit":
				_restore()
				get_tree().quit()
				return
		if str(s[4]) != "":
			await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			img.save_png(_out + "/" + str(s[4]) + ".png")
			print("PROBE ", s[4], " t=", snappedf(_t, 0.01))


func _find(root: Node, script_file: String) -> Array:
	var out: Array = []
	for c in root.get_children():
		var sc = c.get_script()
		if sc != null and str(sc.resource_path).ends_with(script_file):
			out.append(c)
		out.append_array(_find(c, script_file))
	return out


func _restore() -> void:
	var g := get_node("/root/Game")
	g.camera = _orig_cam
	g.player = _orig_player
