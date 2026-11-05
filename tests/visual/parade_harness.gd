extends Node
## Visual + logic harness for L_M1_Parade (owner: parade).
## Instances scenes/levels/L_M1_Parade.tscn in a 642x362 SubViewport (the lead's low-res world size, shown 3x).
##   (windowed)  "$GODOT" --path C:/Spiele/AshesOfEmpires res://tests/visual/parade_harness.tscn -- \
##                   --out=C:/somewhere --symbols=0|1 [--times=3,9.5] [--realtime=47] [--prefix=sym1]
##     -> seeks every shot (default: one frame per shot + 2 extra), saves 1:1 PNGs to --out, checks every saved
##        frame against the 40 colours of pg.PALETTES['berlin'] (exact match), then plays the cinematic in real
##        time with vsync off and reports fps, process time and the viewport's measured CPU/GPU render time.
##   (headless)  "$GODOT" --headless --path C:/Spiele/AshesOfEmpires res://tests/visual/parade_harness.tscn -- --selftest
##     -> finished exactly once (natural end and skip), skip idempotent, cues complete and in order, 7-9 shots,
##        duration 40-50 s, seek/get_time, Symbols-resolved banner textures, viewport settings restored. Exit 0 = pass.

const LEVEL_PATH := "res://scenes/levels/L_M1_Parade.tscn"
const BERLIN := ["#120C14", "#1B1520", "#211623", "#2A2130", "#25202B", "#342F37", "#443B43", "#57494D",
	"#4A3A35", "#5F4A40", "#7A5E4E", "#94735C", "#AE8A6C", "#C9A585", "#5F4530", "#735145", "#8D5542", "#AF6C47",
	"#D07744", "#E5945A", "#F0AE6E", "#F4BA81", "#F8D2A0", "#FCE9C8", "#1E2329", "#2F363F", "#454E58", "#5F6973",
	"#7C8690", "#A3ACB4", "#1E2E2C", "#2C4440", "#3E5D55", "#56776A", "#73927F", "#6E6A73", "#8F8A92", "#B2ACB0",
	"#D2CCCB", "#ECE6E0"]

var out_dir := "user://parade_preview"
var prefix := "parade"
var times: Array = []
var realtime := 0.0
var selftest := false
var level: Node

@onready var vp: SubViewport = $SubViewport
@onready var view: TextureRect = $View


func _ready() -> void:
	get_tree().create_timer(240.0).timeout.connect(func(): print("PARADE TIMEOUT"); get_tree().quit(2))
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.get_slice("=", 1)
		elif a.begins_with("--prefix="):
			prefix = a.get_slice("=", 1)
		elif a.begins_with("--times="):
			for s in a.get_slice("=", 1).split(","):
				times.append(float(s))
		elif a.begins_with("--realtime="):
			realtime = float(a.get_slice("=", 1))
		elif a == "--selftest":
			selftest = true
	if selftest:
		await _selftest()
		return
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	view.texture = vp.get_texture()
	view.size = Vector2(vp.size) * 3.0
	level = (load(LEVEL_PATH) as PackedScene).instantiate()
	level.set("own_sfx", false)
	vp.add_child(level)
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	for i in 10:
		await RenderingServer.frame_post_draw
	print("PARADE set stats: ", level.builder.stats, " parade: ", level.pset.stats)
	print("PARADE symbols hist = ", Symbols.enabled())
	if times.is_empty():
		for s in level.get_shot_ids():
			times.append(snappedf(lerpf(float(s[1]), float(s[2]), 0.62), 0.05))
		times.append(14.6)
		times.append(46.9)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir))
	var bad_total := 0
	var palette := {}
	for h in BERLIN:
		palette[Color(h).to_html(false)] = true
	for t in times:
		level.seek(float(t))
		for i in 4:
			await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		var name := "%s_%s_%05.2f.png" % [prefix, level.get_shot_id(), float(t)]
		img.save_png(out_dir.path_join(name))
		var bad := 0
		var w := img.get_width()
		var h := img.get_height()
		for y in range(0, h, 2):
			for x in range(0, w, 2):
				if not palette.has(img.get_pixel(x, y).to_html(false)):
					bad += 1
		bad_total += bad
		print("PARADE frame %s  shot=%s  off-palette(sampled 1/4)=%d" % [name, level.get_shot_id(), bad])
	print("PARADE palette check: off-palette pixels (sampled) = %d" % bad_total)
	if realtime > 0.0:
		await _realtime(realtime)
	get_tree().quit(0)


func _realtime(secs: float) -> void:
	var rid := vp.get_viewport_rid()
	var fr: Array = []
	var gpu: Array = []
	var cpu: Array = []
	var prc: Array = []
	level.perf = {"last": 0, "max": 0, "sum": 0, "n": 0}
	level.play()
	var t0 := Time.get_ticks_usec()
	var last := t0
	while level.is_playing() and (Time.get_ticks_usec() - t0) < int(secs * 1e6):
		await RenderingServer.frame_post_draw
		var now := Time.get_ticks_usec()
		fr.append((now - last) / 1000.0)
		last = now
		gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
		cpu.append(RenderingServer.viewport_get_measured_render_time_cpu(rid))
		prc.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	fr.pop_front()
	var wall := (Time.get_ticks_usec() - t0) / 1e6
	print("PARADE realtime: frames=%d wall=%.1fs avg_fps=%.1f" % [fr.size(), wall, fr.size() / maxf(wall, 0.001)])
	for pair in [["frame_ms", fr], ["gpu_ms", gpu], ["cpu_ms", cpu], ["process_ms", prc]]:
		var a: Array = pair[1]
		a.sort()
		if a.is_empty():
			continue
		var s := 0.0
		for v in a:
			s += float(v)
		print("PARADE %s avg=%.3f p95=%.3f max=%.3f" % [pair[0], s / a.size(), float(a[int(a.size() * 0.95)]),
			float(a[a.size() - 1])])
	var pf: Dictionary = level.perf
	print("PARADE script update us: avg=%.0f max=%d" % [float(pf["sum"]) / maxf(float(pf["n"]), 1.0), int(pf["max"])])


func _selftest() -> void:
	var fails: PackedStringArray = []
	vp.size = Vector2i(642, 362)
	var saved_msaa := vp.msaa_3d
	vp.msaa_3d = Viewport.MSAA_4X
	level = (load(LEVEL_PATH) as PackedScene).instantiate()
	level.set("own_sfx", false)
	vp.add_child(level)
	await get_tree().process_frame
	if vp.msaa_3d != Viewport.MSAA_DISABLED:
		fails.append("viewport MSAA not disabled while the level runs")
	for k in ["level_id", "mode", "protagonist", "grade_preset", "ambience", "music"]:
		print("PARADE export %s = %s" % [k, str(level.get(k))])
	if str(level.get("level_id")) != "L_M1_Parade" or str(level.get("mode")) != "3d" \
			or str(level.get("protagonist")) != "none" or str(level.get("grade_preset")) != "hall_3d":
		fails.append("root exports wrong")
	var dur: float = level.get_duration()
	if dur < 40.0 or dur > 50.0:
		fails.append("duration %.1f outside 40-50 s" % dur)
	var ids: Array = level.get_shot_ids()
	if ids.size() < 7 or ids.size() > 9:
		fails.append("shot count %d" % ids.size())
	# cues in order + finished exactly once on the natural end
	var got: Array = []
	var fin := [0]
	level.cue.connect(func(k: String): got.append(k))
	level.finished.connect(func(): fin[0] += 1)
	level.play()
	var steps := 0
	while level.is_playing() and steps < 5000:
		level._process(0.05)
		steps += 1
	var want: Array = []
	for c in level.CUES:
		want.append(str(c[1]))
	if got != want:
		fails.append("cues %s != %s" % [str(got), str(want)])
	for k in want:
		if str(k).begins_with("parade.cue.") and not Loc.has(str(k)):
			fails.append("missing locale text for " + str(k))
	if fin[0] != 1:
		fails.append("finished emitted %d times on the natural end" % fin[0])
	level.skip()
	level.skip()
	if fin[0] != 1:
		fails.append("skip() after the end re-emitted finished (%d)" % fin[0])
	# skip mid-run: exactly one more emission, idempotent
	level.play()
	level._process(3.0)
	level.skip()
	level.skip()
	if fin[0] != 2:
		fails.append("skip mid-run: finished count %d (want 2)" % fin[0])
	if absf(level.get_time() - dur) > 0.001:
		fails.append("skip did not land on the final frame")
	level.seek(26.0)
	if level.get_shot_id() != "p5" or absf(level.get_time() - 26.0) > 0.001:
		fails.append("seek/get_shot_id wrong: %s %.2f" % [level.get_shot_id(), level.get_time()])
	# insignia switch: the tribune banners follow Symbols.enabled()
	var bm: ShaderMaterial = level.builder.mats.get("banner_portico")
	var tex: Texture2D = bm.get_shader_parameter("albedo_tex") if bm else null
	var hist_tex := tex != null and tex.resource_path.ends_with("_hist.png")
	print("PARADE symbols=%s banner=%s" % [str(Symbols.enabled()), tex.resource_path if tex else "none"])
	if hist_tex != Symbols.enabled():
		fails.append("banner texture does not follow Symbols.enabled()")
	print("PARADE cues: ", got)
	level.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
	if vp.msaa_3d != Viewport.MSAA_4X:
		fails.append("viewport MSAA not restored")
	vp.msaa_3d = saved_msaa
	if fails.is_empty():
		print("PARADE SELFTEST PASS")
		get_tree().quit(0)
	else:
		for f in fails:
			print("PARADE FAIL: " + f)
		get_tree().quit(1)
