extends Node
## Visual harness for the Berlin archive environment (env_berlin area, round 2).
## Renders L_M1_Archive in its own 640x360 SubViewport with the real world camera script -- WITHOUT the
## post-process grade -- so the environment art, parallax, decals and ambient actors can be checked in
## isolation (palette-pure, independent of other areas' work in progress).  Writes no save files.
##   godot --path . res://tests/visual/berlin_env_capture.tscn -- --cam=0 [--cam2=...] --out=C:/tmp/x.png
##         [--frames=120] [--seconds=0] [--symbols=0|1] [--player=x]
## --seconds > 0 waits that much real time instead of a frame count (e.g. to catch the tram).
## Several cameras: --cams=0,560,900 --out=C:/tmp/prefix  ->  prefix_cam0000.png ...

const LEVEL := "res://scenes/levels/L_M1_Archive.tscn"
const CAMERA_SCRIPT := "res://scripts/render/world_camera.gd"

var args := {}


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	get_window().size = Vector2i(1280, 720)
	_run.call_deferred()


func _run() -> void:
	var vp := SubViewport.new()
	vp.size = Vector2i(642, 362)
	vp.snap_2d_transforms_to_pixel = true
	vp.snap_2d_vertices_to_pixel = true
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.audio_listener_enable_2d = true
	add_child(vp)
	var level: Node = load(LEVEL).instantiate()
	vp.add_child(level)
	var cam := Camera2D.new()
	cam.set_script(load(CAMERA_SCRIPT))
	vp.add_child(cam)
	var game := get_node_or_null("/root/Game")
	if game:
		game.set("camera", cam)
	await get_tree().process_frame
	await get_tree().process_frame
	cam.set_bounds(level.get_camera_bounds())
	cam.cinematic = true
	if args.has("player"):
		# a stand-in "player" node so proximity actors (pigeons, mouse) can be tested
		var p := Node2D.new()
		p.position = Vector2(float(args["player"]), 300.0)
		p.add_to_group("player")
		level.get_node("Playfield").add_child(p)
	var cams: Array = []
	if args.has("cams"):
		for c in str(args["cams"]).split(","):
			cams.append(float(c))
	else:
		cams.append(float(args.get("cam", "0")))
	var out := str(args.get("out", "user://berlin_env_capture"))
	var frames := int(args.get("frames", "120"))
	var seconds := float(args.get("seconds", "0"))
	var t0 := Time.get_ticks_msec()
	var frame_count := 0
	for c in cams:
		cam.set_top_left(Vector2(c, 0))
		if seconds > 0.0:
			var until := Time.get_ticks_msec() + int(seconds * 1000.0)
			while Time.get_ticks_msec() < until:
				await get_tree().process_frame
				frame_count += 1
		else:
			for i in frames:
				await get_tree().process_frame
				frame_count += 1
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image().get_region(Rect2i(1, 1, 640, 360))
		var path := out if cams.size() == 1 else "%s_cam%04d.png" % [out, int(c)]
		if not path.ends_with(".png"):
			path += ".png"
		img.save_png(path)
		print("BERLIN_CAPTURE ", path, " cam=", c)
	var secs := (Time.get_ticks_msec() - t0) / 1000.0
	print("BERLIN_FPS avg=", snappedf(frame_count / maxf(secs, 0.001), 0.1), " frames=", frame_count,
		" seconds=", snappedf(secs, 0.01))
	get_tree().quit(0)
