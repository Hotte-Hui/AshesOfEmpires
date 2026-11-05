extends Node
## Harness for the A1 -> M1 transition cinematic (owner: trans-a1m1). Runs the REAL Main scene (world
## viewport, grade, letterbox, subtitles, Audio) and drives scenes/cinematics/a1m1/CinA1ToM1.tscn exactly the
## way the proposed Game._cin_a1_to_m1 does (see _integration_cin below = the replacement body handed to the
## lead). Windowed run (headless has no renderer); never writes save files (Game sees --capture and skips
## autosaves; the capture itself is postponed by --frames=1000000 and this harness quits first).
##
##   GODOT --path C:/Spiele/AshesOfEmpires res://tests/visual/cine_a1m1_harness.tscn -- \
##       --scene=L_A1_Railyard --capture=OUT/unused.png --frames=1000000 --symbols=1 \
##       --cine-mode=frames|play|skip|motion|integ --cine-branch=share|keep --cine-out=DIR [--cine-times=1,5.5,...]
##
## frames : seek to fixed times, save the composed 1920x1080 window + the 640x360 world image per time
## play   : real-time playback, saves frames when the clock passes the capture times, frame-time stats
## skip   : play 2.5 s, skip() twice -> finished must be emitted exactly once, state at the end
## motion : frame-sequence check of the train departure (see _run_motion), contact sheets of the running gear
## integ  : runs _integration_cin (the proposed Game code), presses "skip" via Game._skip after 3 s,
##          checks: finished once, returned skipped flag, black screen, level kept hidden, camera released

const CIN := "res://scenes/cinematics/a1m1/CinA1ToM1.tscn"
const DEFAULT_TIMES := [0.6, 2.2, 3.1, 5.9, 7.3, 8.4, 9.6, 11.0, 12.6, 15.0, 16.8, 18.1, 18.8, 19.7, 21.0, 23.3,
	24.3, 25.3, 26.5, 28.9, 31.4, 33.0, 35.0, 37.2, 39.3, 40.1, 41.4]

var mode := "frames"
var branch := "keep_private"
var out_dir := ""
var times: Array = DEFAULT_TIMES.duplicate()
var main: Node
var cin: Node
var _fin_count := 0
var _log: PackedStringArray = []
var _fails: PackedStringArray = []


func _ready() -> void:
	get_tree().create_timer(150.0).timeout.connect(func(): _say("TIMEOUT"); _quit(2))
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--cine-mode="):
			mode = a.get_slice("=", 1)
		elif a.begins_with("--cine-branch="):
			branch = "share_with_irina" if a.get_slice("=", 1) == "share" else "keep_private"
		elif a.begins_with("--cine-out="):
			out_dir = a.get_slice("=", 1)
		elif a.begins_with("--cine-times="):
			times = []
			for s in a.get_slice("=", 1).split(","):
				times.append(float(s))
	if out_dir != "":
		DirAccess.make_dir_recursive_absolute(out_dir)
	main = load("res://scenes/main/Main.tscn").instantiate()
	add_child(main)
	# wait for Game to load the start level (--scene=...)
	var guard := 0
	while (Game.level == null or not is_instance_valid(Game.level)) and guard < 600:
		await get_tree().process_frame
		guard += 1
	for i in 10:
		await get_tree().process_frame
	_say("mode=%s branch=%s symbols=%s level=%s" % [mode, branch, str(Symbols.enabled()),
		str(Game.level.get("level_id")) if Game.level else "none"])
	if Game.main == null or Game.level == null or not ResourceLoader.exists(CIN):
		_fails.append("setup: Main/level not ready (Game.main=%s level=%s) -- shared scripts broken?" % [str(Game.main), str(Game.level)])
		_quit(1)
		return
	match mode:
		"frames":
			await _run_frames()
		"play":
			await _run_play()
		"skip":
			await _run_skip()
		"integ":
			await _run_integ()
		"motion":
			await _run_motion()
	_quit(0 if _fails.is_empty() else 1)


# ------------------------------------------------------------------ the proposed Game code (mirrored)
## Mirror of the replacement body for Game._cin_a1_to_m1 (integration_notes). `g` is the Game autoload.
func _integration_cin(g: Node) -> bool:
	g._begin_cinematic()
	if not ResourceLoader.exists(CIN):
		return g._end_cinematic()
	Audio.stop_music(1.5)
	await g.fade_out(0.8)
	var prev_level: Node = g.level
	if prev_level:
		prev_level.visible = false
		prev_level.process_mode = Node.PROCESS_MODE_DISABLED
	var c: Node = load(CIN).instantiate()
	g.main.level_root.add_child(c)
	c.configure({"choices": Story.choice_history(), "flags": Story.flags() if Story.has_method("flags") else {},
		"symbols": Symbols.enabled()})
	var done := [false]
	c.finished.connect(func(): done[0] = true, CONNECT_ONE_SHOT)
	c.play()
	g._fade.color.a = 0.0                     # the cinematic fades in from its own black frame
	while not done[0]:
		if g._skip and c.has_method("skip"):
			c.skip()
		await g.get_tree().process_frame
	g._fade.color.a = 1.0                     # stay black: goto_level() fades the M1 level in
	c.queue_free()
	g.camera.release()
	return g._end_cinematic()


# ------------------------------------------------------------------ modes
func _spawn() -> Node:
	Game._begin_cinematic()
	Game._fade.color.a = 0.0
	if Game.level:
		Game.level.visible = false
		Game.level.process_mode = Node.PROCESS_MODE_DISABLED
	var c: Node = load(CIN).instantiate()
	Game.main.level_root.add_child(c)
	if not c.has_method("configure"):
		_fails.append("cinematic script failed to load (parse error?)")
		_quit(1)
		return c
	c.configure({"choices": {"a1_choose": branch}, "flags": {}, "symbols": Symbols.enabled()})
	c.finished.connect(func(): _fin_count += 1)
	return c


func _run_frames() -> void:
	cin = _spawn()
	await get_tree().process_frame
	for tt in times:
		cin.seek(float(tt))
		_subtitle_for(float(tt))
		for i in 3:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		_save("f%06.2f" % float(tt))
	_say("frames saved: %d" % times.size())


func _subtitle_for(tt: float) -> void:
	var key := ""
	if tt >= cin.T_LINE_A and tt < cin.T_LINE_A + 4.9:
		key = "cin.a1m1.alexei.share" if branch == "share_with_irina" else "cin.a1m1.alexei.keep"
	elif tt >= cin.T_LINE_K and tt < cin.T_LINE_K + 4.9:
		key = "cin.a1m1.konrad"
	var sub = Game.ui.get("subtitles") if Game.ui else null
	if key != "":
		Game.subtitle(Loc.t(key), 3.0)
	elif sub and sub.has_method("clear"):
		sub.clear()


func _run_play() -> void:
	cin = _spawn()
	RenderingServer.viewport_set_measure_render_time(Game.world.get_viewport_rid(), true)
	_say("world viewport %s, hi-res path %s" % [str(Game.world.size), str(Game.view.is_hires() if Game.view.has_method("is_hires") else false)])
	await get_tree().process_frame
	cin.play()
	var next := 0
	var deltas: Array = []
	var gpu: Array = []
	var cpu: Array = []
	var last := Time.get_ticks_usec()
	while _fin_count == 0:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		var dt := float(now - last) / 1000.0
		last = now
		if cin.get_time() > 0.5:
			deltas.append(dt)
			if dt > 12.0:
				_say("slow frame %.2f ms at t=%.2f" % [dt, cin.get_time()])
			gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(Game.world.get_viewport_rid()))
			cpu.append(RenderingServer.viewport_get_measured_render_time_cpu(Game.world.get_viewport_rid()))
		if next < times.size() and cin.get_time() >= float(times[next]):
			await RenderingServer.frame_post_draw
			_save("p%05.1f" % cin.get_time())
			next += 1
			last = Time.get_ticks_usec()
	deltas.sort()
	var n := deltas.size()
	if n > 0:
		var avg := 0.0
		for d in deltas:
			avg += d
		avg /= n
		_say("frame_ms avg %.2f  p50 %.2f  p95 %.2f  p99 %.2f  max %.2f  (n=%d frames)" % [avg, deltas[n / 2],
			deltas[int(n * 0.95)], deltas[int(n * 0.99)], deltas[n - 1], n])
		var gavg := 0.0
		var cavg := 0.0
		for g in gpu:
			gavg += g
		for c in cpu:
			cavg += c
		_say("world viewport render ms: gpu avg %.3f  cpu avg %.3f" % [gavg / maxf(1, gpu.size()), cavg / maxf(1, cpu.size())])
		if deltas[int(n * 0.95)] > 20.0:
			_fails.append("p95 frame time %.2f ms > 20 ms" % deltas[int(n * 0.95)])
	if _fin_count != 1:
		_fails.append("finished emitted %d times during playback" % _fin_count)
	_say("played %.2f s, finished=%d" % [cin.get_time(), _fin_count])


func _run_skip() -> void:
	cin = _spawn()
	await get_tree().process_frame
	cin.play()
	var e := 0.0
	while e < 2.5:
		await get_tree().process_frame
		e += get_process_delta_time()
	cin.skip()
	cin.skip()
	if _fin_count != 1:
		_fails.append("skip(): finished emitted %d times (expected 1)" % _fin_count)
	if absf(cin.get_time() - cin.get_duration()) > 0.001:
		_fails.append("skip(): time %.3f != duration %.3f" % [cin.get_time(), cin.get_duration()])
	for i in 30:
		await get_tree().process_frame
	cin.skip()
	if _fin_count != 1:
		_fails.append("after 30 more frames + third skip: finished=%d (expected 1)" % _fin_count)
	# skip before play on a fresh instance
	var c2: Node = load(CIN).instantiate()
	Game.main.level_root.add_child(c2)
	var cnt := [0]
	c2.finished.connect(func(): cnt[0] += 1)
	c2.configure({"choices": {}, "flags": {}, "symbols": false})
	c2.skip()
	c2.skip()
	c2.play()          # a play() after skip() restarts cleanly (finished again later, never twice per run)
	c2.skip()
	if cnt[0] != 2:
		_fails.append("fresh instance: skip/skip/play/skip -> finished %d (expected 2: one per run)" % cnt[0])
	c2.queue_free()
	await RenderingServer.frame_post_draw
	_save("skip_end")
	_say("skip test: finished=%d fails=%d" % [_fin_count, _fails.size()])


func _run_integ() -> void:
	Story.new_game()
	var started := Time.get_ticks_msec()
	var res := [null]
	var runner := func():
		res[0] = await _integration_cin(Game)
	runner.call()
	var noskip := OS.get_cmdline_user_args().has("--cine-noskip")
	var e := 0.0
	while res[0] == null and (e < 3.0 or noskip) and e < 60.0:
		await get_tree().process_frame
		e += get_process_delta_time()
	if not noskip:
		Game._skip = true                     # what the "skip" key does during in_cinematic
	var guard := 0
	while res[0] == null and guard < 300:
		await get_tree().process_frame
		guard += 1
	var want := not noskip
	if res[0] != want:
		_fails.append("integration: returned skipped=%s (expected %s)" % [str(res[0]), str(want)])
	if Game._fade.color.a < 0.99:
		_fails.append("integration: screen not black after the cinematic (alpha %.2f)" % Game._fade.color.a)
	if Game.level and Game.level.visible:
		_fails.append("integration: previous level visible again before goto_level")
	if Game.camera.cinematic:
		_fails.append("integration: camera still in cinematic mode")
	if Game.in_cinematic:
		_fails.append("integration: Game.in_cinematic still true")
	var left := 0
	for c in Game.main.level_root.get_children():
		if c.scene_file_path == CIN and not c.is_queued_for_deletion():
			left += 1
	if left:
		_fails.append("integration: cinematic node not freed")
	_say("integration run: %.1f s wall, skipped=%s, fails=%d" % [(Time.get_ticks_msec() - started) / 1000.0, str(res[0]), _fails.size()])


## Steps the departure at 1/60 s (seek = the frames a player sees) and checks, from the scene graph, that the
## drivers' frame (rods + valve gear) is exactly the one implied by the loco's DRAWN travel (+ slip), that all
## vehicles sit on the 1/k grid, buffers never overlap and gaps stay within the slack, the engine never rolls
## back after the start, and the exhaust beats come 4 per driver revolution. Saves running-gear contact sheets
## (12 consecutive frames) for the start, the slip and the run.
func _run_motion() -> void:
	cin = _spawn()
	await get_tree().process_frame
	var K: Dictionary = cin.layout.get("karsk", {})
	var r := float(K.get("wheel_r", 16))
	var nf := int(K.get("wheel_frames", 60))
	var k := float(cin._px_scale())
	var base: Array = cin._veh_base()
	var widths := [284.0, 196.0, 180.0, 196.0]
	var names := ["veh_loco", "veh_tender", "veh_gondola", "veh_boxcar", "c17"]
	var bad := 0
	var grid_bad := 0
	var gap_bad := 0
	var back_bad := 0
	var n := 0
	var prev_x := INF
	var max_gap := [0.0, 0.0, 0.0, 0.0]
	var tt := 0.0
	while tt < cin.T_SHOT_STAMP:
		cin.seek(tt)
		var lx: float = cin._n["veh_loco"].position.x
		var want := posmod(int(floor(((float(base[0]) - lx) / r + cin._slip_angle(tt)) / TAU * nf)), nf)
		if want != int(cin._n["loco_wheels"].base.frame):
			bad += 1
		var xs: Array = []
		for nm in names:
			var px: float = cin._n[nm].position.x * k
			if absf(px - roundf(px)) > 0.01:
				grid_bad += 1
			xs.append(cin._n[nm].position.x)
		for i in 4:
			var gap: float = float(xs[i + 1]) - float(xs[i]) - float(widths[i])
			max_gap[i] = maxf(max_gap[i], gap)
			if tt >= cin.T_COUPLE and (gap < -0.01 or gap > float(cin.SLACK[i]) + 1.0):
				gap_bad += 1
		if tt > cin.T_DEPART + 0.05 and lx > prev_x + 0.01:
			back_bad += 1
		prev_x = lx
		n += 1
		tt += 1.0 / 60.0
	var revs: float = (cin._driver_angle(cin.T_SHOT_STAMP - 0.01) - cin._driver_angle(cin.T_DEPART)) / TAU
	var beats: int = cin._beats.size()
	_say("motion: %d frames  rod-phase mismatches %d  off-grid %d  gap violations %d  roll-backs %d" % [n, bad, grid_bad, gap_bad, back_bad])
	_say("motion: max gaps %s  snatches %s  revs %.2f beats %d  joint hits %d" % [str(max_gap), str(cin._snatch), revs, beats, cin._joint_ev.size()])
	for tau in [1.0, 2.0, 3.0, 5.2, 8.0, 11.0, 12.2]:
		_say("  tau %.1f: travel %.1f px  v %.1f px/s" % [tau, cin._loco_d(cin.T_DEPART + tau), cin._loco_v(cin.T_DEPART + tau)])
	if bad > 0:
		_fails.append("rod phase != travelled distance in %d frames" % bad)
	if grid_bad > 0 or gap_bad > 0 or back_bad > 0:
		_fails.append("train motion: off-grid %d, gaps %d, roll-backs %d" % [grid_bad, gap_bad, back_bad])
	if absi(beats - int(round(revs * 4.0))) > 1:
		_fails.append("exhaust beats %d != 4 per revolution (%.2f rev)" % [beats, revs])
	# contact sheets: 12 consecutive 1/60 s frames of the running gear (world image, 1 sample per texel)
	for ph in [["start", 1.0], ["slip", 2.15], ["run", 4.6]]:
		var sheet := Image.create(270, 12 * 64, false, Image.FORMAT_RGBA8)
		for j in 12:
			var t2: float = cin.T_DEPART + float(ph[1]) + float(j) / 60.0
			cin.seek(t2)
			for f in 2:
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var wi: Image = Game.view.capture_world_image() if Game.view and Game.view.has_method("capture_world_image") else null
			if wi == null:
				break
			wi.convert(Image.FORMAT_RGBA8)
			var cam: Vector2 = cin._cam_at(t2)
			var lx2: float = cin._n["veh_loco"].position.x
			var src := Rect2i(int(round(lx2 - cam.x)) - 10, 272 - 62 - int(cam.y), 270, 64)
			sheet.blit_rect(wi, src, Vector2i(0, j * 64))
		if out_dir != "":
			sheet.save_png("%s/motion_%s.png" % [out_dir, ph[0]])


# ------------------------------------------------------------------ util
func _save(tag: String) -> void:
	if out_dir == "":
		return
	var img := get_viewport().get_texture().get_image()
	var sym := "h" if Symbols.enabled() else "n"
	var b := "share" if branch == "share_with_irina" else "keep"
	img.save_png("%s/%s_%s_%s.png" % [out_dir, tag, b, sym])
	var wi: Image
	if Game.view and Game.view.has_method("capture_world_image"):
		wi = Game.view.capture_world_image()          # 640x360, one sample per texel (hi-res path aware)
	else:
		wi = Game.world.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))
	wi.save_png("%s/%s_%s_%s_world.png" % [out_dir, tag, b, sym])


func _say(s: String) -> void:
	print("[cine_a1m1] ", s)
	_log.append(s)


func _quit(code: int) -> void:
	for f in _fails:
		print("[cine_a1m1] FAIL: ", f)
	print("[cine_a1m1] RESULT ", "PASS" if _fails.is_empty() and code == 0 else "FAIL")
	get_tree().quit(code if _fails.is_empty() else 1)
