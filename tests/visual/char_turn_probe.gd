extends Node
## Visual probe of the player's soft turn (owner: characters): boots the real Main scene into a level, walks the
## player right with synthetic input, reverses to the left and saves the player's surroundings for the frames
## around the reversal (enlarged, nearest) into one strip -- the in-between walk_front frame must show between the
## right- and the left-facing walk. Also reports whether the rig turned softly (is_turning seen) and ended mirrored.
##   godot --path . res://tests/visual/char_turn_probe.tscn -- --scene=L_A1_Railyard --capture=<dir>/boot.png \
##         --frames=100000 --tp-out=<dir>
## Never writes saves or settings (capture mode). Exit code 0 = soft turn seen and finished.

const MAIN := "res://scenes/main/Main.tscn"

var out_dir := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tp-out="):
			out_dir = a.substr(9)
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("user://char_turn_probe")
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_tree().create_timer(40.0).timeout.connect(func(): print("TURN_PROBE TIMEOUT"); get_tree().quit(2))
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
	var p: Node2D = Game.player
	if p == null:
		print("TURN_PROBE FAIL: no player")
		get_tree().quit(1)
		return
	Game.input_locked = false
	await _frames(30)
	Input.action_press("move_right")
	await _frames(40)
	var tiles: Array = []
	var turning_seen := false
	Input.action_release("move_right")
	Input.action_press("move_left")
	var t_start := -1
	var t_end := -1
	for i in 14:
		await RenderingServer.frame_post_draw
		if p.rig.is_turning():
			turning_seen = true
			if t_start < 0:
				t_start = Time.get_ticks_msec()
		elif turning_seen and t_end < 0:
			t_end = Time.get_ticks_msec()
		tiles.append(_grab(p))
		await get_tree().process_frame
	print("TURN_PROBE turn visible for about %d ms (frame readbacks slow the loop down)" % (t_end - t_start))
	Input.action_release("move_left")
	await _frames(10)
	var ok: bool = turning_seen and p.rig.is_flipped()
	var w: int = (tiles[0] as Image).get_width()
	var h: int = (tiles[0] as Image).get_height()
	var strip := Image.create(w * tiles.size(), h, false, (tiles[0] as Image).get_format())
	for i in tiles.size():
		strip.blit_rect(tiles[i], Rect2i(0, 0, w, h), Vector2i(i * w, 0))
	strip.resize(strip.get_width() * 2, strip.get_height() * 2, Image.INTERPOLATE_NEAREST)
	strip.save_png(out_dir.path_join("turn_strip.png"))
	print("TURN_PROBE ", "PASS" if ok else "FAIL", " turning_seen=", turning_seen, " flipped=", p.rig.is_flipped())
	get_tree().quit(0 if ok else 1)


## The player's neighbourhood in the composed window (world -> screen via the camera's drawn position).
func _grab(p: Node2D) -> Image:
	var img := get_viewport().get_texture().get_image()
	var pos: Vector2 = Game.world_to_ui(p.global_position) if Game.has_method("world_to_ui") else Vector2(960, 800)
	var k := 3
	var r := Rect2i(int(pos.x) - 20 * k, int(pos.y) - 56 * k, 40 * k, 60 * k)
	r = r.intersection(Rect2i(0, 0, img.get_width(), img.get_height()))
	return img.get_region(r)
