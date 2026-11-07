extends Node
## Harness for the X1 finale montage (owner: trans-finale).  Never writes saves: it boots the real Main
## scene with --cinematic=none (no level, no menu, no autosave) and then drives the montage itself.
##
## Modes (user args after --):
##   --fin-mode=shots  --fin-choices=<m1>,<a1> --fin-symbols=0|1 --fin-out=DIR [--fin-times=t1,t2,...]
##        seeks the montage to each time and saves the composed window (1920x1080, letterbox + subtitles)
##        as DIR/<prefix>_<t>.png and the 640x360 world as DIR/<prefix>_<t>_w.png
##   --fin-mode=run  --fin-choices=<m1>,<a1> [--fin-skip-at=SECONDS] [--fin-report=FILE]
##        plays the montage in real time through the proposed Game._cin_final body (_cin_final_body below
##        is the exact code handed to the lead), optionally presses the real "skip" input, and reports:
##        finished emissions, return value, wall time, frame-time statistics.
##   --fin-mode=endcard --fin-endcard=<m1>,<a1>,<c3a>,<c3b>,<c3d>,<c3g>,<c4d>,<c4g> --fin-out=DIR [--fin-prefix=P]
##        [--fin-textscale=1.25]   (the text-size setting for this run only: Settings.values, never saved)
##        shows the end card exactly as Game._show_end_card lays it out (title + "Ende der Demo" + one bullet
##        per decision in story order, via Game.end_card_decisions) and saves the window as DIR/<prefix>.png;
##        prints the laid-out caption height so an overflow below the frame is caught.
## Run: "$GODOT" --path . res://tests/visual/cine_finale_harness.tscn -- --cinematic=none --fin-mode=...

const FINALE := "res://scenes/cinematics/finale/Finale.tscn"

var args := {}
var finished_count := 0
var frame_ms: Array[float] = []
var frame_log: Array = []          # [montage_time, ms]
var _fin: Node = null


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	get_window().size = Vector2i(1920, 1080)
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	add_child(main)
	for i in 3:
		await get_tree().process_frame
	if str(args.get("fin-nograde", "0")) == "1" and Game.grade:
		# diagnostic only: bypass the shared post-grade pass (e.g. while another area is editing its shader)
		Game.grade.visible = false
	match str(args.get("fin-mode", "shots")):
		"probe":
			await _mode_probe()
		"shots":
			await _mode_shots()
		"run":
			await _mode_run()
		"endcard":
			await _mode_endcard()
	get_tree().quit()


# ------------------------------------------------------------------------------------------- end card
const ENDCARD_OBJECTIVES := ["m1_choose", "a1_choose", "c3a_choose", "c3b_choose", "c3d_choose", "c3g_choose",
	"c4d_choose", "c4g_choose"]


func _mode_endcard() -> void:
	var out := str(args.get("fin-out", "user://finale_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	var prefix := str(args.get("fin-prefix", "endcard"))
	var ch := {}
	var parts := str(args.get("fin-endcard", "")).split(",")
	for i in mini(parts.size(), ENDCARD_OBJECTIVES.size()):
		if parts[i] != "":
			ch[ENDCARD_OBJECTIVES[i]] = parts[i]
	if args.has("fin-textscale"):
		# runtime only (Settings.values + changed signal), like memory_drive: the settings file is never written
		Settings.values["text_scale"] = float(args["fin-textscale"])
		if Settings.has_signal("changed"):
			Settings.changed.emit("text_scale", Settings.values["text_scale"])
	Game.input_locked = true
	Game.in_cinematic = true
	# the harness has no finished story, so the HUD would show the first objective; at the real end card every
	# objective is done and the objective box stays empty
	Game._call(Game._ui("hud"), "hide_hud")
	# exactly Game._show_end_card() (its layout at the text size), fed with an explicit choice history
	var bullets: Array = Game.end_card_decisions(ch)
	Game._show_end_card(ch)
	await Game.fade_in(0.01)
	for i in 6:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(prefix + ".png"))
	var cap: Label = Game._caption
	var bottom := cap.global_position.y + cap.get_minimum_size().y
	print("ENDCARD ", prefix, " bullets=", bullets.size(), " text_scale=", Settings.get_value("text_scale"),
		" title_font=", Game._title.get_theme_font_size("font_size"), " caption_font=",
		cap.get_theme_font_size("font_size"), " title_top=", Game._title.position.y, " caption_bottom=", bottom,
		" visible_lines=", cap.get_visible_line_count(), " line_count=", cap.get_line_count())


func _ctx() -> Dictionary:
	var ch := {}
	var parts := str(args.get("fin-choices", "preserve_evidence,share_with_irina")).split(",")
	if parts.size() >= 1 and parts[0] != "":
		ch["m1_choose"] = parts[0]
	if parts.size() >= 2 and parts[1] != "":
		ch["a1_choose"] = parts[1]
	var sym := str(args.get("fin-symbols", "1")) != "0"
	return {"choices": ch, "flags": {}, "symbols": sym}


# ------------------------------------------------------------------------------------------- probe
## Colour pipeline probe: draws the b_close base with and without the finale set shader and prints the
## captured value of known texels next to the source value (detects gamma / grading differences).
func _mode_probe() -> void:
	await Game.fade_in(0.01)
	Game.camera.cinematic = true
	Game.camera.set_top_left(Vector2(20, 10), false)
	var tex: Texture2D = load("res://assets/cinematics/finale/b_close/base.png")
	var src: Image = tex.get_image()
	for variant in ["plain", "shader"]:
		var sp := Sprite2D.new()
		sp.centered = false
		sp.texture = tex
		if variant == "shader":
			var m := ShaderMaterial.new()
			m.shader = load("res://assets/cinematics/finale/finale_set.gdshader")
			sp.material = m
		Game.main.level_root.add_child(sp)
		for i in 4:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var img: Image = Game.view.capture_world_image() if Game.view.has_method("capture_world_image") \
			else Game.world.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))
		var line: String = str(variant) + ":"
		for p in [Vector2i(500, 250), Vector2i(560, 200), Vector2i(100, 250), Vector2i(250, 200)]:
			var c := img.get_pixelv(p)
			var s := src.get_pixelv(p + Vector2i(20, 10))
			line += " %s eng=(%d,%d,%d) src=(%d,%d,%d)" % [p, c.r8, c.g8, c.b8, s.r8, s.g8, s.b8]
		print("PROBE ", line, " hires=", Game.view.is_hires() if Game.view.has_method("is_hires") else "n/a",
			" vp=", Game.world.size, " fmt=", img.get_format())
		sp.queue_free()
		await get_tree().process_frame


# ------------------------------------------------------------------------------------------- shots
func _mode_shots() -> void:
	var out := str(args.get("fin-out", "user://finale_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	var prefix := str(args.get("fin-prefix", "fin"))
	var times: Array = []
	for s in str(args.get("fin-times", "2,7,10,12,13.5,15,18,23,26,28,29,31,33,36,40,43,45")).split(","):
		times.append(float(s))
	Game.input_locked = true
	Game.in_cinematic = true
	var fin: Node = load(FINALE).instantiate()
	Game.main.level_root.add_child(fin)
	fin.configure(_ctx())
	print("SYMBOLS ctx=", _ctx().get("symbols"), " montage=", fin.symbols)
	Game._apply_grade(fin)
	Game._call(Game._ui("hud"), "hide_hud")
	Game._call(Game._ui("fade"), "letterbox", [true, 0.0])
	await Game.fade_in(0.01)
	for t in times:
		fin.seek(float(t))
		_show_active_subtitles(fin, float(t))
		for i in 4:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var tag := "%s_%05.1f" % [prefix, float(t)]
		get_viewport().get_texture().get_image().save_png(out.path_join(tag + ".png"))
		var wi: Image
		if Game.view and Game.view.has_method("capture_world_image"):
			wi = Game.view.capture_world_image()       # hi-res world path: one sample per world texel
		else:
			wi = Game.world.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))
		wi.save_png(out.path_join(tag + "_w.png"))
		print("SHOT ", tag)
	fin.queue_free()


func _show_active_subtitles(fin: Node, t: float) -> void:
	var sub := Game._ui("subtitles")
	if sub and sub.has_method("clear"):
		sub.clear()
	for e in fin._events:
		if str(e.get("type", "")) != "subtitle":
			continue
		var et := float(e.get("t", 0.0))
		var dur := float(e.get("dur", 3.0))
		if t >= et and t < et + dur:
			Game.subtitle(Loc.t(str(e.get("key", ""))), dur - (t - et))


# ------------------------------------------------------------------------------------------- run
func _mode_run() -> void:
	var skip_at := float(args.get("fin-skip-at", "-1"))
	var t_start := Time.get_ticks_msec()
	if skip_at >= 0.0:
		_press_skip_later(skip_at)
	var stats_on := [true]
	_collect_frames(stats_on)
	var skipped: bool = await _cin_final_body(_ctx())
	stats_on[0] = false
	var wall := (Time.get_ticks_msec() - t_start) / 1000.0
	frame_ms.sort()
	var n := frame_ms.size()
	var avg := 0.0
	for v in frame_ms:
		avg += v
	avg = avg / maxf(1.0, n)
	var p95: float = frame_ms[int(n * 0.95)] if n > 0 else 0.0
	var mx: float = frame_ms[n - 1] if n > 0 else 0.0
	var worst := [0.0, 0.0]
	var worst_playing := [0.0, 0.0]
	for fl in frame_log:
		if float(fl[1]) > worst[1]:
			worst = fl
		if float(fl[0]) > 0.05 and float(fl[1]) > worst_playing[1]:
			worst_playing = fl
	var rep := {"worst_frame": worst, "worst_frame_while_playing": worst_playing, "skip_at": skip_at, "returned_skipped": skipped, "finished_emitted": finished_count,
		"wall_s": wall, "frames": n, "frame_ms_avg": avg, "frame_ms_p95": p95, "frame_ms_max": mx,
		"montage_freed": _fin == null or not is_instance_valid(_fin),
		"camera_cinematic_after": Game.camera.cinematic, "in_cinematic_after": Game.in_cinematic}
	print("FINALE_REPORT ", JSON.stringify(rep))
	if args.has("fin-report"):
		var f := FileAccess.open(str(args["fin-report"]), FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify(rep, "  "))


func _press_skip_later(sec: float) -> void:
	await get_tree().create_timer(sec).timeout
	var ev := InputEventAction.new()
	ev.action = "skip"
	ev.pressed = true
	Input.parse_input_event(ev)
	await get_tree().process_frame
	var up := InputEventAction.new()
	up.action = "skip"
	up.pressed = false
	Input.parse_input_event(up)
	# a second press must not cause a second `finished`
	await get_tree().create_timer(0.1).timeout
	Input.parse_input_event(ev)


func _collect_frames(on: Array) -> void:
	while on[0]:
		await get_tree().process_frame
		var ms := get_process_delta_time() * 1000.0
		frame_ms.append(ms)
		var mt := -1.0
		if _fin and is_instance_valid(_fin) and _fin.has_method("time"):
			mt = _fin.time()
		frame_log.append([mt, ms])


# ------------------------------------------------------------------------------------------- body
## The proposed replacement for Game._cin_final (integration_notes): identical except that the harness
## passes ctx explicitly instead of reading Story.choice_history(), and uses Game.* for its members.
func _cin_final_body(ctx: Dictionary) -> bool:
	var g := Game
	if not ResourceLoader.exists(FINALE):
		return false
	g._begin_cinematic()
	Audio.stop_music(1.2)
	Audio.stop_ambience(1.2)
	await g.fade_out(0.9)
	var prev_level: Node = g.level
	if prev_level:
		prev_level.visible = false
		prev_level.process_mode = Node.PROCESS_MODE_DISABLED
	var fin: Node = load(FINALE).instantiate()
	_fin = fin
	g.main.level_root.add_child(fin)
	fin.configure(ctx)
	g._apply_grade(fin)
	var done := [false]
	fin.finished.connect(func():
		done[0] = true
		finished_count += 1)
	fin.play()
	await g.fade_in(0.8)
	while not done[0]:
		if g._skip:
			fin.skip()
			break
		await get_tree().process_frame
	await g.fade_out(1.0)
	fin.queue_free()
	g.camera.release()
	if prev_level and is_instance_valid(prev_level):
		prev_level.visible = true
		prev_level.process_mode = Node.PROCESS_MODE_INHERIT
	var skipped: bool = g._end_cinematic()
	await get_tree().process_frame
	return skipped
