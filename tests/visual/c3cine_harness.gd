extends Node
## Capture / timing harness for the Chapter-3 cinematics (owner: cinematics stream).  Never writes saves:
## it boots the real Main scene with --cinematic=none (no level, no menu, no autosave) and drives one
## §12.5 scene itself, exactly like ChapterExt.play_cinematic() does (grade, letterbox, camera).
##
## Modes (user args after --):
##   --c3-mode=shots --c3-id=LS_C3_Trains --c3-out=DIR [--c3-times=1,4.5,9] [--c3-flags=a=1,b=0] [--c3-rm=0|1]
##        seeks to each time and saves the composed window (letterbox + subtitles) as DIR/<id>_<t>.png and the
##        640x360 world as DIR/<id>_<t>_w.png
##   --c3-mode=seq --c3-id=... --c3-out=DIR --c3-from=8.0 --c3-to=10.0 [--c3-fps=15]
##        saves consecutive world frames (motion review: contact sheets / flip books)
##   --c3-mode=run --c3-id=... [--c3-skip-at=SECONDS] [--c3-report=FILE]
##        plays in real time and reports: finished emissions, wall time, frame-time statistics, cue log
## Run: "$GODOT" --path . res://tests/visual/c3cine_harness.tscn -- --cinematic=none --c3-mode=...

const ChapterExt := preload("res://scripts/core/chapter_ext.gd")

var args := {}
var finished_count := 0
var frame_ms: Array[float] = []
var _cin: Node = null


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
	match str(args.get("c3-mode", "shots")):
		"shots":
			await _mode_shots()
		"seq":
			await _mode_seq()
		"run":
			await _mode_run()
	get_tree().quit()


func _flags() -> Dictionary:
	var f := {}
	for kv in str(args.get("c3-flags", "")).split(",", false):
		var p := kv.split("=")
		if p.size() == 2:
			f[p[0]] = int(p[1]) if p[1].is_valid_int() else p[1]
	return f


func _make() -> Node:
	var ext := ChapterExt.new()
	var id := str(args.get("c3-id", "LS_C3_Trains"))
	var cin: Node = load(str(ext.cinematics[id])).instantiate()
	if args.has("c3-rm"):
		cin.set("reduced_motion_override", int(args["c3-rm"]))
	Game.main.level_root.add_child(cin)
	cin.configure({"choices": {}, "flags": _flags(), "symbols": true})
	Game._apply_grade(cin)
	Game._call(Game._ui("hud"), "hide_hud")
	Game._call(Game._ui("fade"), "letterbox", [true, 0.0])
	_cin = cin
	return cin


func _out() -> String:
	var out := str(args.get("c3-out", "user://c3cine_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	return out


func _world_image() -> Image:
	if Game.view and Game.view.has_method("capture_world_image"):
		return Game.view.capture_world_image()
	return Game.world.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))


## subtitle that would be on screen at time t (cue list of the scene)
func _show_subtitle(cin: Node, t: float) -> void:
	var sub := Game._ui("subtitles")
	if sub and sub.has_method("hide_subtitle"):
		sub.hide_subtitle()
	for c in cin.get("_cues"):
		if not (c as Dictionary).has("say"):
			continue
		var ct := float(c["t"])
		var dur := float(c.get("dur", 4.0))
		if t >= ct and t < ct + dur:
			Game.subtitle(Loc.t(str(c["say"])), dur - (t - ct) + 5.0)


# ------------------------------------------------------------------------------------------- shots
func _mode_shots() -> void:
	var out := _out()
	var cin := _make()
	var id := str(args.get("c3-id", "LS_C3_Trains"))
	var times: Array = []
	for s in str(args.get("c3-times", "0.5,3,6")).split(","):
		times.append(float(s))
	await Game.fade_in(0.01)
	cin.play()
	cin.set("_frozen", true)
	for t in times:
		cin.seek(float(t))
		_show_subtitle(cin, float(t))
		for i in 5:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var tag := "%s_%05.2f" % [id, float(t)]
		if args.has("c3-tag"):
			tag = str(args["c3-tag"]) + "_" + tag
		get_viewport().get_texture().get_image().save_png(out.path_join(tag + ".png"))
		_world_image().save_png(out.path_join(tag + "_w.png"))
		print("SHOT ", tag, " shot=", cin.get_shot_id(), " missing=", cin.get("missing"))


# ------------------------------------------------------------------------------------------- seq
func _mode_seq() -> void:
	var out := _out()
	var cin := _make()
	var id := str(args.get("c3-id", "LS_C3_Trains"))
	var t0 := float(args.get("c3-from", "0"))
	var t1 := float(args.get("c3-to", "2"))
	var fps := float(args.get("c3-fps", "15"))
	await Game.fade_in(0.01)
	cin.play()
	cin.set("_frozen", true)
	var n := 0
	var t := t0
	while t <= t1 + 0.0001:
		cin.seek(t)
		for i in 2:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		_world_image().save_png(out.path_join("%s_seq_%04d.png" % [id, n]))
		n += 1
		t += 1.0 / fps
	print("SEQ ", id, " frames=", n)


# ------------------------------------------------------------------------------------------- run
func _mode_run() -> void:
	var cin := _make()
	var id := str(args.get("c3-id", "LS_C3_Trains"))
	cin.finished.connect(func(): finished_count += 1)
	var skip_at := float(args.get("c3-skip-at", "-1"))
	await Game.fade_in(0.3)
	var t_start := Time.get_ticks_msec()
	cin.play()
	var wall := 0.0
	var skipped := false
	while not cin.is_finished() and wall < float(cin.get("max_duration")) + 2.0:
		await get_tree().process_frame
		var dt := get_process_delta_time()
		wall += dt
		frame_ms.append(dt * 1000.0)
		if skip_at >= 0.0 and wall >= skip_at and not skipped:
			skipped = true
			cin.skip()
			cin.skip()
	# a few frames after the end: nothing more may be emitted
	for i in 10:
		await get_tree().process_frame
	frame_ms.sort()
	var n := frame_ms.size()
	var avg := 0.0
	for v in frame_ms:
		avg += v
	avg /= maxf(1.0, n)
	var rep := {"id": id, "finished_emitted": finished_count, "finish_count": cin.get("finish_count"),
		"wall_s": (Time.get_ticks_msec() - t_start) / 1000.0, "duration": cin.get_duration(), "skipped": skipped,
		"frames": n, "frame_ms_avg": avg, "frame_ms_p95": frame_ms[int(n * 0.95)] if n > 0 else 0.0,
		"frame_ms_max": frame_ms[n - 1] if n > 0 else 0.0, "said": cin.get("said"), "missing": cin.get("missing")}
	print("C3CINE_REPORT ", JSON.stringify(rep))
	if args.has("c3-report"):
		var f := FileAccess.open(str(args["c3-report"]), FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify(rep, "  "))
	cin.queue_free()
