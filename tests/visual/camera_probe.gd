extends Node
## Engine/display probe for the render-camera work (owner: render-camera). Prints display facts and the
## stretch transform of the root window at a few window sizes, then quits. Writes nothing.
##   godot --path . res://tests/visual/camera_probe.tscn


func _ready() -> void:
	var w := get_window()
	w.mode = Window.MODE_WINDOWED
	print("screen count ", DisplayServer.get_screen_count())
	for s in DisplayServer.get_screen_count():
		print("screen ", s, " size ", DisplayServer.screen_get_size(s), " refresh ", DisplayServer.screen_get_refresh_rate(s),
			" scale ", DisplayServer.screen_get_scale(s), " usable ", DisplayServer.screen_get_usable_rect(s))
	print("vsync ", DisplayServer.window_get_vsync_mode(), " physics ticks ", Engine.physics_ticks_per_second,
		" max_fps ", Engine.max_fps)
	print("has get_physics_interpolation_fraction ", Engine.has_method("get_physics_interpolation_fraction"))
	print("delta smoothing ", ProjectSettings.get_setting("application/run/delta_smoothing", "?"))
	for sz in [Vector2i(1920, 1080), Vector2i(3840, 2160), Vector2i(2560, 1440), Vector2i(1600, 900)]:
		w.size = sz
		for i in 4:
			await get_tree().process_frame
		var vp := get_viewport()
		print("win ", w.size, " visible ", vp.get_visible_rect(), " final ", vp.get_final_transform(),
			" screen_xf ", vp.get_screen_transform(), " stretch ", w.get_stretch_transform() if w.has_method("get_stretch_transform") else "n/a",
			" content_scale ", w.content_scale_size, " factor ", w.content_scale_factor)
	get_tree().quit()
