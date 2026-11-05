extends Node
## Visual test harness for the Great Hall reveal (owner: great_hall_3d).
## Instances scenes/levels/L_M1_HallReveal.tscn inside a 640x360 SubViewport (shown at 3x, nearest), plays
## the cinematic in real time and saves exact frames of the viewport at t = 2, 7, 11, 16, 20.5, 23.5 s to
## assets/architecture/great_hall/_preview/ (1:1 PNG + 3x nearest PNG), prints frame-time statistics
## (Performance monitors + measured viewport CPU/GPU render time) and quits.
## Run windowed (headless has no renderer):
##   "$LOCALAPPDATA/Programs/Godot/Godot_v4.7.2-stable_win64.exe" --path C:/Spiele/AshesOfEmpires \
##       res://tests/visual/HallPreview.tscn
## Optional user args after "--":  --times=0.5,2.2  --prefix=iter2  --debug=1 (post debug view)
##   --symbols=0|1 (historical insignia off/on for this run, handled by the Settings autoload)
##   --size=642x362 (match the in-game world viewport)  --nosnow  --still=2.5,10 (seek, no playback)
##   --placeholders  (force the generated placeholder people instead of assets/characters sheets)
##   --selftest  (logic checks, also works with --headless: finished-once, skip, cues, sprite overrides,
##                viewport restore; exit code 0 = pass)

const LEVEL_PATH := "res://scenes/levels/L_M1_HallReveal.tscn"
const OUT_DIR := "res://assets/architecture/great_hall/_preview/"

var capture_times: Array = [2.0, 7.0, 11.0, 16.0, 20.5, 23.5]
var prefix := "hall"
var debug_view := 0
var no_snow := false
var still := -1.0
var selftest := false
var use_placeholders := false
var level: Node
var _next := 0
var _busy := false
var _done := false
var _samples := {"frame": [], "process": [], "gpu": [], "cpu": [], "draws": [], "prims": []}
var _log: PackedStringArray = []

@onready var vp: SubViewport = $SubViewport
@onready var view: TextureRect = $View


func _ready() -> void:
	# safety net first: the harness must always quit
	get_tree().create_timer(90.0).timeout.connect(func(): _say("TIMEOUT"); _quit(1))
	_parse_args()
	if selftest:
		await _selftest()
		return
	view.texture = vp.get_texture()
	view.size = Vector2(vp.size) * 3.0
	var scene: PackedScene = load(LEVEL_PATH)
	if scene == null:
		_say("FAIL: cannot load " + LEVEL_PATH)
		get_tree().quit(1)
		return
	level = scene.instantiate()
	if use_placeholders:
		var ph := {}
		for r in ["berlin_father", "berlin_mother", "berlin_child", "guard"]:
			ph[r] = "res://assets/architecture/great_hall/people/%s.png" % r
		level.set_people_sprites(ph)
	vp.add_child(level)
	if debug_view != 0 and level.get("post_mat") != null:
		(level.post_mat as ShaderMaterial).set_shader_parameter("debug_view", debug_view)
	if no_snow and level.get("post_mat") != null:
		(level.post_mat as ShaderMaterial).set_shader_parameter("snow_density", 0.0)
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	level.connect("finished", _on_finished)
	# warm-up: compile pipelines before the clock starts
	for i in 8:
		await RenderingServer.frame_post_draw
	_say("people sources: " + str(level.people.get_sources()))
	_say("set stats: " + str(level.builder.stats))
	if still >= 0.0:
		for t in capture_times:
			await _capture(float(t))
		_quit(0)
		return
	level.play()


func _selftest() -> void:
	var fails: PackedStringArray = []
	vp.size = Vector2i(642, 362)          # same as the lead's World viewport
	vp.msaa_3d = Viewport.MSAA_4X         # deliberately "wrong": the level must override and restore it
	vp.use_taa = true
	var scene: PackedScene = load(LEVEL_PATH)
	var lv = scene.instantiate()
	lv.set_people_sprites({"guard": "res://assets/architecture/great_hall/people/guard.png"})   # before _ready
	vp.add_child(lv)
	await get_tree().process_frame
	var fin := [0]
	var cues: Array = []
	lv.finished.connect(func(): fin[0] += 1)
	lv.cue.connect(func(k): cues.append(k))
	if vp.get_camera_3d() != lv.camera:
		fails.append("level camera is not the current camera of the viewport")
	if vp.msaa_3d != Viewport.MSAA_DISABLED or vp.use_taa:
		fails.append("viewport AA was not disabled by the level")
	if str(lv.people.get_sources().get("guard", "")) != "res://assets/architecture/great_hall/people/guard.png":
		fails.append("pending set_people_sprites override not applied: " + str(lv.people.get_sources()))
	# skip twice -> exactly one finished, final pose
	lv.skip()
	lv.skip()
	if fin[0] != 1:
		fails.append("skip(): finished emitted %d times (expected 1)" % fin[0])
	if absf(lv.get_time() - lv.get_duration()) > 0.001:
		fails.append("skip(): time %.3f != duration" % lv.get_time())
	# full playback (accelerated) -> finished once more, all cues in order
	Engine.time_scale = 25.0
	lv.play()
	var guard_ms := Time.get_ticks_msec()       # wall-clock guard (the reveal runs 24 s since round 3)
	while fin[0] < 2 and Time.get_ticks_msec() - guard_ms < 30000:
		await get_tree().process_frame
	Engine.time_scale = 1.0
	if fin[0] != 2:
		fails.append("play(): finished count %d after playback (expected 2)" % fin[0])
	var expected: Array = []
	for c in lv.CUES:
		expected.append(str(c[1]))
	if cues != expected:
		fails.append("cues %s != %s" % [str(cues), str(expected)])
	lv.skip()
	if fin[0] != 2:
		fails.append("skip() after natural end emitted finished again")
	# runtime override of a role with a sprite sheet
	lv.set_people_sprites({"berlin_father": "res://assets/architecture/great_hall/people/berlin_father.png"})
	if str(lv.people.get_sources().get("berlin_father", "")) != "res://assets/architecture/great_hall/people/berlin_father.png":
		fails.append("runtime set_people_sprites failed")
	# every locale key used by the cues exists
	var loc = JSON.parse_string(FileAccess.get_file_as_string("res://data/locale/de_hall.json"))
	var table: Dictionary = loc.get("strings", loc) if typeof(loc) == TYPE_DICTIONARY else {}
	for k in expected:
		if not table.has(k):
			fails.append("missing locale key " + k)
	# leaving the tree restores the viewport settings
	lv.queue_free()
	await get_tree().process_frame
	if vp.msaa_3d != Viewport.MSAA_4X or not vp.use_taa:
		fails.append("viewport settings not restored on exit")
	for f in fails:
		_say("FAIL: " + f)
	_say("selftest: %s (%d checks failed)" % ["PASS" if fails.is_empty() else "FAIL", fails.size()])
	_quit(0 if fails.is_empty() else 1)


func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--times="):
			capture_times = []
			for s in a.substr(8).split(","):
				capture_times.append(float(s))
		elif a.begins_with("--prefix="):
			prefix = a.substr(9)
		elif a.begins_with("--debug="):
			debug_view = int(a.substr(8))
		elif a.begins_with("--size="):
			var p := a.substr(7).split("x")
			if p.size() == 2:
				$SubViewport.size = Vector2i(int(p[0]), int(p[1]))
		elif a == "--nosnow":
			no_snow = true
		elif a == "--selftest":
			selftest = true
		elif a == "--placeholders":
			use_placeholders = true
		elif a.begins_with("--still="):
			# fast path for look-dev: seek straight to the given times without playing
			still = 0.0
			capture_times = []
			for s in a.substr(8).split(","):
				capture_times.append(float(s))


func _process(delta: float) -> void:
	if level == null or _busy or _done or still >= 0.0:
		return
	if level.is_playing():
		if OS.get_cmdline_user_args().has("--perfdump") and _samples["frame"].size() % 97 == 5:
			_say("perfdump: delta %.4f s  TIME_PROCESS %.6f  TIME_FPS %.1f  Engine.get_frames_per_second %.1f" % [
				delta, Performance.get_monitor(Performance.TIME_PROCESS), Performance.get_monitor(Performance.TIME_FPS),
				Engine.get_frames_per_second()])
		_samples["frame"].append(delta * 1000.0)
		_samples["process"].append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		_samples["gpu"].append(RenderingServer.viewport_get_measured_render_time_gpu(vp.get_viewport_rid()))
		_samples["cpu"].append(RenderingServer.viewport_get_measured_render_time_cpu(vp.get_viewport_rid()))
		_samples["draws"].append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
		_samples["prims"].append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	if _next < capture_times.size() and level.get_time() >= float(capture_times[_next]):
		_capture(float(capture_times[_next]))


func _capture(t: float) -> void:
	_busy = true
	level.set_paused(true)
	level.seek(t)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img: Image = vp.get_texture().get_image()
	var dir := ProjectSettings.globalize_path(OUT_DIR)
	DirAccess.make_dir_recursive_absolute(dir)
	var gd := dir.path_join(".gdignore")
	if not FileAccess.file_exists(gd):
		FileAccess.open(gd, FileAccess.WRITE).close()
	var name := "%s_t%05.2f" % [prefix, t]
	name = name.replace(".", "_")
	img.save_png(dir.path_join(name + ".png"))
	var big := img.duplicate() as Image
	big.resize(img.get_width() * 3, img.get_height() * 3, Image.INTERPOLATE_NEAREST)
	big.save_png(dir.path_join(name + "_x3.png"))
	_say("captured t=%.2f shot=%s -> %s.png" % [t, level.get_shot_id(), name])
	_next += 1
	level.set_paused(false)
	_busy = false


func _on_finished() -> void:
	# let a pending capture at the very end finish
	while _busy:
		await RenderingServer.frame_post_draw
	while _next < capture_times.size():
		await _capture(float(capture_times[_next]))
	_done = true
	_report()
	_quit(0)


func _stat(arr: Array) -> String:
	if arr.is_empty():
		return "n/a"
	var s := arr.duplicate()
	s.sort()
	var sum := 0.0
	for v in s:
		sum += float(v)
	return "avg %.2f  p50 %.2f  p95 %.2f  max %.2f" % [sum / s.size(), float(s[s.size() / 2]),
		float(s[int(s.size() * 0.95)]), float(s[s.size() - 1])]


func _report() -> void:
	_say("frames sampled: %d" % _samples["frame"].size())
	_say("frame delta ms : " + _stat(_samples["frame"]))
	_say("TIME_PROCESS ms: " + _stat(_samples["process"]) + "   (monitor value; in 4.7.2 it refreshes ~1x/s)")
	_say("viewport GPU ms: " + _stat(_samples["gpu"]))
	_say("viewport CPU ms: " + _stat(_samples["cpu"]))
	_say("draw calls     : " + _stat(_samples["draws"]))
	_say("primitives     : " + _stat(_samples["prims"]))
	_say("FPS (engine)   : %.1f" % Performance.get_monitor(Performance.TIME_FPS))
	var pf: Dictionary = level.get("perf") if level.get("perf") != null else {}
	if not pf.is_empty() and int(pf.get("n", 0)) > 0:
		_say("level update us: avg %.0f  max %d  (%d updates; camera + sprites + life + halos)" % [
			float(pf["sum"]) / float(pf["n"]), int(pf["max"]), int(pf["n"])])
	if level.get("people") != null:
		_say("sprites        : %d (visible at the end: %d)" % [level.people.actors.size(), level.people.count_visible()])
	_say("video mem MB   : %.1f" % (Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0))


func _say(s: String) -> void:
	print("[HallPreview] " + s)
	_log.append(s)


func _quit(code: int) -> void:
	var dir := ProjectSettings.globalize_path(OUT_DIR)
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir.path_join(prefix + "_log.txt"), FileAccess.WRITE)
	if f:
		f.store_string("\n".join(_log) + "\n")
		f.close()
	get_tree().quit(code)
