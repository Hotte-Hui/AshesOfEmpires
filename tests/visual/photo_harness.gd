extends Node
## Photo-mode harness (owner: photo-mode). Boots the real Main scene into a level in capture mode (Game: no
## autosave, no intro, no focus pause), opens the photo mode through the real "photo_mode" action, pans with the
## polled move action, changes filter / frame / figure with synthetic key presses, zooms, takes a photo with a
## synthetic Enter, checks both PNGs, hides the UI with H, closes with Esc and checks that camera, grade, figure,
## HUD, Display transform and pause are restored. Screenshots: --ph-out=<dir>.
##   godot --path . res://tests/visual/photo_harness.tscn -- --scene=L_A1_Railyard --capture=<dir>/boot.png \
##         --frames=100000 --ph-out=<dir> [--ph-real]
## --ph-real: the second copy goes to <Pictures>/Ashes of Empires (default: <ph-out>/pictures).
## (--capture only switches Game into its test mode; --frames keeps Game's own capture from firing.)
## Exit code 0 = every check passed.

const MAIN := "res://scenes/main/Main.tscn"

var out_dir := ""
var real_export := false
var tag := "level"
var problems: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--ph-out="):
			out_dir = a.substr(9)
		elif a == "--ph-real":
			real_export = true
		elif a.begins_with("--scene="):
			tag = a.substr(8)
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://photo_harness")
	DirAccess.make_dir_recursive_absolute(out_dir)
	add_child(load(MAIN).instantiate())
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out_dir.path_join("%s_%s.png" % [tag, name]))


func _check(cond: bool, msg: String) -> void:
	print(("OK   " if cond else "FAIL ") + msg)
	if not cond:
		problems.append(msg)


func _key(code: Key, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	Input.parse_input_event(e)


func _tap(code: Key) -> void:
	_key(code, true)
	await _frames(2)
	_key(code, false)
	await _frames(2)


func _run() -> void:
	var t0 := Time.get_ticks_msec()
	while (Game.level == null or Game.ui == null or Game.busy) and Time.get_ticks_msec() - t0 < 30000:
		await get_tree().process_frame
	await _frames(120)
	var ui = Game.ui
	var pm = ui.get("photo") if ui != null else null
	_check(pm != null, "UIRoot.photo registered")
	if pm == null:
		_finish()
		return
	var cam = Game.camera
	var before := {"pos": cam.pos, "cin": cam.cinematic}
	var grade0: Dictionary = pm.read_grade(Game.grade.material)
	var pvis = Game.player.visible if Game.player else null
	var hud_vis: bool = ui.hud.visible
	var disp = Game.view.display
	var disp0 := [disp.position, disp.scale]
	print("level ", tag, " hires=", Game.view.is_hires(), " k=", Game.view.world_scale, " cam=", cam.pos, " bounds=", cam.bounds)

	Game.in_cinematic = true
	_check(not ui.open_photo(), "blocked during a cinematic")
	Game.in_cinematic = false

	var ev := InputEventAction.new()
	ev.action = "photo_mode"
	ev.pressed = true
	Input.parse_input_event(ev)
	await _frames(3)
	var ev_up := InputEventAction.new()
	ev_up.action = "photo_mode"
	Input.parse_input_event(ev_up)
	_check(pm.is_open, "opened by the photo_mode action (Game._unhandled_input -> UIRoot.open_photo)")
	_check(get_tree().paused, "world paused")
	_check(not ui.hud.visible, "HUD hidden")
	if not real_export:
		pm.export_dir_override = out_dir.path_join("pictures")
	await get_tree().create_timer(0.5, true, false, true).timeout   # frames are not time: let the fade-in finish
	await _shot("01_open")

	var can_pan: bool = cam.clamp_pos(cam.pos + Vector2(8, 0)).x > cam.pos.x
	var p_before: Vector2 = cam.pos
	Input.action_press("move_right")
	await _frames(30)
	Input.action_release("move_right")
	if can_pan:
		_check(cam.pos.x > p_before.x, "move_right pans the camera (%s -> %s)" % [p_before, cam.pos])
	_check(cam.cinematic, "camera in cinematic mode while open")

	await _tap(KEY_F)
	for i in 4:
		await _tap(KEY_R)
	_check(pm.filter_id == "sepia", "F -> Archiv-Sepia")
	_check(pm.frame_id == "print", "R x4 -> Fotoabzug")
	_check(pm.read_grade(Game.grade.material) != grade0, "grade changed by the filter")
	await _frames(4)
	await _shot("02_sepia_print")

	pm.set_zoom(2)
	pm.set_filter("night")
	pm.set_frame("scope")
	await _frames(4)
	_check(disp.scale == Vector2(2, 2), "Display zoomed x2")
	await _shot("03_zoom2_night_scope")

	pm.set_zoom(1)
	pm.set_filter("bw")
	pm.set_frame("academy")
	await _tap(KEY_C)
	_check(Game.player == null or not Game.player.visible, "C hides the figure")
	await _frames(4)
	await _shot("04_bw_43_nofigure")

	pm.set_filter("sepia")
	pm.set_frame("print")
	await _frames(3)
	_key(KEY_ENTER, true)
	var paths: Array = await pm.photo_taken
	_key(KEY_ENTER, false)
	_check(paths.size() == 2, "photo saved to user:// and the export folder: %s" % [paths])
	for p in paths:
		var img := Image.load_from_file(str(p))
		_check(img != null and img.get_size() == get_window().size, "%s is %s" % [p, img.get_size() if img else "missing"])
		_check(str(p).get_file().begins_with("ashes_") and str(p).ends_with(".png"), "file name " + str(p).get_file())
	if not paths.is_empty():
		Image.load_from_file(str(paths[0])).save_png(out_dir.path_join("%s_05_photo.png" % tag))
	await _frames(10)
	await _shot("06_toast")

	await _tap(KEY_H)
	await _frames(4)
	_check(not pm._ui.visible, "H hides the photo UI")
	await _shot("07_ui_hidden")
	await _tap(KEY_H)

	await _tap(KEY_ESCAPE)
	await _frames(5)
	_check(not pm.is_open, "Esc closes")
	_check(not get_tree().paused, "world unpaused")
	_check(cam.pos == before["pos"], "camera position restored (%s vs %s)" % [cam.pos, before["pos"]])
	_check(cam.cinematic == before["cin"], "camera cinematic flag restored")
	_check(pm.read_grade(Game.grade.material) == grade0, "level grade restored")
	_check(Game.player == null or Game.player.visible == pvis, "figure visibility restored")
	_check(ui.hud.visible == hud_vis, "HUD restored")
	_check(disp.position == disp0[0] and disp.scale == disp0[1], "Display transform restored")
	await _frames(10)
	await _shot("08_closed")
	_finish()


func _finish() -> void:
	print("PHOTO_HARNESS ", tag, " ", "PASS" if problems.is_empty() else "FAIL %s" % [problems])
	get_tree().quit(0 if problems.is_empty() else 1)
