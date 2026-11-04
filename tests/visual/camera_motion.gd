extends Node
## Camera / render-path test harness (owner: render-camera). Instances the real Main scene in Game capture mode
## (`--capture=...` must be given: no saves, no autosave, no pause on focus loss; `--frames=1000000` keeps
## Game's capture flow from quitting first), drives the player with synthetic input actions and records, every
## frame, the camera's continuous / drawn position and the player's drawn position (CSV), optionally a strip of
## the composed window per frame so the real on-screen scroll can be measured offline with
## tests/visual/camera_motion_analyze.py. Writes only into --mt-out (default: user data dir), never saves.
##
## Motion run (windowed; --fixed-fps simulates a display rate deterministically):
##   godot --path . --fixed-fps 144 res://tests/visual/camera_motion.tscn -- --scene=L_A1_Railyard ##        --capture=<scratch>/unused.png --frames=1000000 --mt-out=<dir> [--mt-tag=new144] [--mt-strips=1]
##        [--mt-shots=300,301] [--mt-size=3840x2160] [--mt-rm=1 (reduced motion, in memory only)] [--mt-x=700]
## Other modes (same base arguments):
##   --mt-fps=1      real-time FPS while walking back and forth (vsync off for this run only)
##   --mt-subpx=1    isolated actor placement (everything but the player hidden)
##   --mt-dither=1   dither-phase test + debug views of the post (threshold / alpha codes)
##   --mt-cw=<path>  PixelView.capture_world_image() at 1080p, after a resize to 4K and back
##   --mt-decal=1    decals injected through LayerStack (Great Hall insignia, read-only), run with --symbols=0|1
##   --mt-hall=1     render-path round trip 2D -> Game._cin_hall() (3D low-res) -> 2D (use --scene=L_M1_Archive)

const MAIN := preload("res://scenes/main/Main.tscn")

var args := {}
var out_dir := ""
var tag := "run"
var strips := false
var fps_mode := false
var rows: PackedStringArray = []
var frame := 0
var phase := "boot"
var _strip_rect := Rect2i()
var _frame_ms: Array = []


func _ready() -> void:
	process_priority = 1000          # sample after camera, player, layers
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	out_dir = str(args.get("mt-out", OS.get_user_data_dir()))
	tag = str(args.get("mt-tag", "run"))
	strips = args.has("mt-strips")
	fps_mode = args.has("mt-fps")
	if args.has("mt-rm"):
		Settings.values["reduced_motion"] = true      # in memory only, never saved
	get_tree().create_timer(240.0, true, false, true).timeout.connect(func(): print("MT TIMEOUT"); get_tree().quit(2))
	add_child(MAIN.instantiate())
	if args.has("mt-size"):
		var p: PackedStringArray = str(args["mt-size"]).split("x")
		var w := get_window()
		w.mode = Window.MODE_WINDOWED
		w.borderless = true
		w.position = Vector2i(0, 0)
		w.size = Vector2i(int(p[0]), int(p[1]))
	if fps_mode:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	_run.call_deferred()


func _wait_ready() -> void:
	var guard := 0
	while guard < 2000:
		guard += 1
		await get_tree().process_frame
		if Game.player and is_instance_valid(Game.player) and Game.level and not Game.input_locked \
				and Game._fade.color.a < 0.02:
			break
	for i in 10:
		await get_tree().process_frame


func _hold(action: String, seconds: float) -> void:
	Input.action_press(action)
	await _seconds(seconds)
	Input.action_release(action)


func _seconds(s: float) -> void:
	var t := 0.0
	while t < s:
		await get_tree().process_frame
		t += get_process_delta_time()


func _run() -> void:
	await _wait_ready()
	var p: Node2D = Game.player
	print("MT window ", get_window().size, " world vp ", Game.world.size, " zoom ", Game.camera.zoom)
	# start in the middle of the yard so the camera can follow both ways
	p.position = Vector2(float(args.get("mt-x", "700")), p.position.y)
	Game.camera.snap_now()
	for i in 20:
		await get_tree().process_frame
	var vh := get_window().size.y
	var s := float(vh) / 1080.0
	_strip_rect = Rect2i(0, int(round(786 * s)), get_window().size.x, int(round(90 * s)))
	if fps_mode:
		await _fps_run()
		return
	if args.has("mt-subpx"):
		await _subpx_run()
		return
	if args.has("mt-dither"):
		await _dither_run()
		return
	if args.has("mt-cw"):
		await _capture_world_run()
		return
	if args.has("mt-decal"):
		await _decal_run()
		return
	if args.has("mt-hall"):
		await _hall_roundtrip_run()
		return
	phase = "walk_r"
	await _hold("move_right", 4.0)
	phase = "stop_r"
	await _seconds(2.5)
	phase = "run_r"
	Input.action_press("run")
	await _hold("move_right", 2.0)
	Input.action_release("run")
	phase = "stop_r2"
	await _seconds(2.0)
	phase = "walk_l"
	await _hold("move_left", 3.0)
	phase = "stop_l"
	await _seconds(2.5)
	phase = "pan"
	var start: Vector2 = Game.camera.pos
	Game.camera.cinematic = true
	var tw: Tween = Game.camera.tween_to(start + Vector2(-260, 0), 5.0)
	await tw.finished
	phase = "pan_hold"
	await _seconds(0.5)
	Game.camera.release()
	Game.camera.snap_now()
	phase = "end"
	await _seconds(0.3)
	_write()
	get_tree().quit(0)


## Isolated actor placement check: everything but the player hidden, camera fixed (cinematic) or moving in
## lockstep; the player is placed at x0 + i/6 world px. Prints the player's measured left edge per step.
func _subpx_run() -> void:
	phase = "subpx"
	var p: Node2D = Game.player
	var lv: Node = Game.level
	for c in lv.get_children():
		if c is CanvasItem and c != lv.get("playfield"):
			(c as CanvasItem).visible = false
	for c in lv.get("playfield").get_children():
		if c != p and c is CanvasItem:
			(c as CanvasItem).visible = false
	var cam: Camera2D = Game.camera
	cam.cinematic = true
	var rig = p.get("rig")
	if rig:
		rig.set("speed_scale", 0.0)
	var x0 := 800.0
	var vh := get_window().size.y
	for mode in ["static_cam", "lockstep_cam"]:
		var xs: Array = []
		for i in 13:
			var x := x0 + i / 6.0
			p.position = Vector2(x, p.position.y)
			cam.set_top_left(Vector2(480.0 + (i / 6.0 if mode == "lockstep_cam" else 0.0), 0.0), false)
			for j in 3:
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			var y := int(vh * 0.80)
			var sx := int((x - cam.drawn.x) * 3.0 * float(vh) / 1080.0)
			var left := -1
			for xx in range(sx - 90 * vh / 1080, sx + 90 * vh / 1080):
				var c := img.get_pixel(xx, y)
				if c.r + c.g + c.b > 0.12:
					left = xx
					break
			xs.append("%d@%.4f/%.4f" % [left, p.global_position.x, (p.get("rig") as Node2D).global_position.x])
			var s := float(vh) / 1080.0
			img.get_region(Rect2i(int(780 * s), int(760 * s), int(360 * s), int(200 * s))).save_png(
				"%s/subpx_%d_%s_%02d.png" % [out_dir, vh, mode, i])
		print("MT subpx %s window %s left edges (px): %s" % [mode, str(get_window().size), str(xs)])
	get_tree().quit(0)


## Where does the post palette dither act? Same frame rendered with the Bayer phase shifted by (0..1, 0..1)
## texels; pixels that change are dither-affected. Saves full frames.
func _dither_run() -> void:
	phase = "dither"
	var cam: Camera2D = Game.camera
	cam.cinematic = true
	cam.set_top_left(Vector2(float(args.get("mt-camx", "640")), 0.0))
	var mat := Game.grade.material as ShaderMaterial
	for j in 4:
		await get_tree().process_frame
	Engine.time_scale = 0.0          # freeze animation, snow, smoke: only the dither phase changes
	var i := 0
	for sh in [Vector2.ZERO, Vector2(1, 0), Vector2(0, 1), Vector2(2, 2)]:
		mat.set_shader_parameter("dither_shift", sh)
		mat.set_shader_parameter("grain", 0.0)
		for j in 4:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/dither_%d.png" % [out_dir, i])
		i += 1
	mat.set_shader_parameter("dither_shift", Vector2.ZERO)
	mat.set_shader_parameter("debug_view", 1)
	for j in 2:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/dither_debug.png" % out_dir)
	mat.set_shader_parameter("debug_view", 2)
	for j in 2:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/dither_alpha.png" % out_dir)
	mat.set_shader_parameter("debug_view", 0)
	var coded := 0
	var plain := 0
	var other := 0
	for n in Game.level.find_children("*", "Sprite2D", true, false):
		var m: Material = (n as Sprite2D).material
		if m is ShaderMaterial and (m as ShaderMaterial).shader.resource_path.ends_with("pixel_sprite.gdshader"):
			coded += 1
		elif m is ShaderMaterial:
			plain += 1
		else:
			other += 1
	print("MT sprites coded %d plain %d other %d" % [coded, plain, other])
	print("MT dither done")
	get_tree().quit(0)


## PixelView.capture_world_image() at an integer camera position, at 1080p, after a runtime resize to 4K and
## back (resolution switch), saved as <mt-cw>_<k>.png (640x360 world pixels).
func _capture_world_run() -> void:
	phase = "cw"
	var cam: Camera2D = Game.camera
	cam.cinematic = true
	cam.set_top_left(Vector2(float(args.get("mt-camx", "640")), 0.0))
	Engine.time_scale = 0.0
	for sz in [Vector2i(1920, 1080), Vector2i(3840, 2160), Vector2i(1920, 1080)]:
		get_window().size = sz
		for j in 6:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var img: Image = Game.view.capture_world_image()
		var k: int = Game.view.world_scale
		img.save_png("%s_%d.png" % [str(args["mt-cw"]), k])
		print("MT cw window %s k %d world vp %s zoom %s image %s" % [str(get_window().size), k, str(Game.world.size),
			str(cam.zoom), str(img.get_size())])
	get_tree().quit(0)


## In-engine decal check: injects decals through LayerStack._build_decal (playfield, on a layer, own parallax)
## using the Great Hall insignia assets (read-only; neutral + _hist variants), then captures the window.
## Run once with --symbols=0 and once with --symbols=1.
func _decal_run() -> void:
	phase = "decal"
	var stack = Game.level.get("backdrop")
	var old_dir: String = stack.base_dir
	stack.base_dir = "res://assets/architecture/great_hall/symbols"
	stack._build_decal({"name": "t_play", "file": "eagle_portico.png", "pos": [690, 236], "layer": "playfield",
		"base_y": 300}, Game.level.get("playfield"))
	stack._build_decal({"name": "t_layer", "file": "banner_portico.png", "pos": [930, 150], "layer": "yard_back",
		"z": 1}, Game.level.get("playfield"))
	stack._build_decal({"name": "t_par", "file": "flag_pole.png", "pos": [560, 120], "parallax": [0.45, 0.0],
		"z": -73}, Game.level.get("playfield"))
	stack.base_dir = old_dir
	var cam: Camera2D = Game.camera
	cam.cinematic = true
	cam.set_top_left(Vector2(float(args.get("mt-camx", "520")), 0.0))
	for j in 8:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path := "%s/decal_sym%s.png" % [out_dir, "1" if Symbols.enabled() else "0"]
	get_viewport().get_texture().get_image().save_png(path)
	print("MT decal capture ", path)
	get_tree().quit(0)


## Render-path round trip: 2D level (hi-res) -> Game._cin_hall() (3D, low-res path) -> back to the 2D level.
## Captures the window mid-hall and after returning; prints the world viewport size / zoom at each step.
func _hall_roundtrip_run() -> void:
	phase = "hall"
	print("MT hall before: vp %s zoom %s hires %s" % [str(Game.world.size), str(Game.camera.zoom), str(Game.view.is_hires())])
	var done := [false]
	var run := func():
		await Game._cin_hall()
		done[0] = true
	run.call()
	var t := 0.0
	var shot := false
	while not done[0] and t < 30.0:
		await get_tree().process_frame
		t += get_process_delta_time()
		if not shot and t > 5.0:
			shot = true
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png("%s/hall_mid.png" % out_dir)
			print("MT hall mid: vp %s hires %s transparent %s" % [str(Game.world.size), str(Game.view.is_hires()), str(Game.world.transparent_bg)])
	for j in 30:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/hall_after.png" % out_dir)
	print("MT hall after: vp %s zoom %s hires %s cam enabled %s" % [str(Game.world.size), str(Game.camera.zoom),
		str(Game.view.is_hires()), str(Game.camera.enabled)])
	get_tree().quit(0)


func _fps_run() -> void:
	phase = "fps"
	_frame_ms.clear()
	var t0 := Time.get_ticks_usec()
	Input.action_press("move_right")
	var last := Time.get_ticks_usec()
	while Time.get_ticks_usec() - t0 < 6_000_000:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		_frame_ms.append((now - last) / 1000.0)
		last = now
		if Game.player.position.x > 1700:
			Input.action_release("move_right")
			Input.action_press("move_left")
		elif Game.player.position.x < 300:
			Input.action_release("move_left")
			Input.action_press("move_right")
	Input.action_release("move_right")
	Input.action_release("move_left")
	_frame_ms.sort()
	var n := _frame_ms.size()
	var sum := 0.0
	for v in _frame_ms:
		sum += v
	var avg := sum / n
	var p99: float = _frame_ms[int(n * 0.99)]
	var p999: float = _frame_ms[mini(n - 1, int(n * 0.999))]
	print("MT FPS window %s frames %d avg_ms %.3f avg_fps %.1f p99_ms %.3f (1%%-low fps %.1f) p99.9_ms %.3f" % [
		str(get_window().size), n, avg, 1000.0 / avg, p99, 1000.0 / p99, p999])
	get_tree().quit(0)


func _process(delta: float) -> void:
	if phase == "boot" or phase == "fps" or Game.camera == null:
		return
	frame += 1
	var cam: Camera2D = Game.camera
	var p: Node2D = Game.player
	if p == null or not is_instance_valid(p):
		return
	var rig: Node2D = p.get("rig")
	var k: float = cam.zoom.x
	var pd: Vector2 = rig.global_position if rig else p.global_position
	var pdq: Vector2 = (pd * k + Vector2(0.5, 0.5)).floor() / k   # what the engine draws (snap to viewport px)
	var cpos: Vector2 = cam.get("pos")
	var cdrawn: Vector2 = cam.get("drawn")
	rows.append("%d,%s,%.6f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.3f" % [frame, phase, delta, cpos.x, cpos.y,
		cdrawn.x, cdrawn.y, p.global_position.x, p.global_position.y, pdq.x, pdq.y, k])
	if strips and phase != "end":
		_save_strip.call_deferred(frame)
	if args.has("mt-shots") and str(frame) in str(args["mt-shots"]).split(","):
		_save_full.call_deferred(frame)


func _save_strip(f: int) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.get_region(_strip_rect).save_png("%s/%s_strip_%04d.png" % [out_dir, tag, f])


func _save_full(f: int) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s_shot_%04d.png" % [out_dir, tag, f])
	var p: Node2D = Game.player
	print("MT shot %d player %s rig %s cam %s" % [f, str(p.global_position), str(p.get("rig").global_position), str(Game.camera.get("drawn"))])


func _write() -> void:
	var path := "%s/%s_frames.csv" % [out_dir, tag]
	var fa := FileAccess.open(path, FileAccess.WRITE)
	fa.store_line("frame,phase,dt,cam_x,cam_y,drawn_x,drawn_y,player_x,player_y,pdraw_x,pdraw_y,k")
	for r in rows:
		fa.store_line(r)
	fa.close()
	print("MT wrote ", path, " rows ", rows.size())
