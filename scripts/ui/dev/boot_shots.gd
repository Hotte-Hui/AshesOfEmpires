extends Node
## Windowed check run of the boot sequence (TECHNICAL_ARCHITECTURE §12.13, round 11):
##   godot --path . -- --splash-shots=DIR
## plays the REAL boot (scripts/ui/boot_flow.gd treats this one argument as a player's launch), forces a 1920x1080
## window, saves frames of every card, the main menu and the demo letter as DIR/<nn>_<card>_<s>.png and quits WITHOUT
## confirming the letter (the settings flag is never written). Instanced by scripts/ui/boot_splash.gd only when the
## argument is given. Prints BOOT_SHOTS lines (cards shown, menu load time, letter state).

const BootFlow := preload("res://scripts/ui/boot_flow.gd")
const PLAN := {"black": [0.4], "studio": [0.8, 2.0], "engine": [1.0], "title": [0.3, 1.6, 2.6, 3.8, 5.0]}

var splash: Node = null
var _dir := ""
var _taken := {}
var _n := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_dir = BootFlow.shots_dir()
	DirAccess.make_dir_recursive_absolute(_dir)
	get_window().mode = Window.MODE_WINDOWED
	get_window().size = Vector2i(1920, 1080)
	_run()


func _run() -> void:
	var cards: Array = []
	while is_instance_valid(splash) and not bool(splash.get("done")):
		await get_tree().process_frame
		if not is_instance_valid(splash):
			break
		cards = splash.get("cards").duplicate()
		var c := str(splash.get("card"))
		var t := float(splash.get("card_time"))
		for at in PLAN.get(c, []):
			var key := "%s@%.1f" % [c, at]
			if t >= float(at) and not _taken.has(key):
				_taken[key] = true
				await _shot("%s_%.1f" % [c, at])
	var t_done := Time.get_ticks_msec()
	while Game.ui == null:
		await get_tree().process_frame
	print("BOOT_SHOTS cards=", cards, " menu_ui_ready_ms=", Time.get_ticks_msec() - t_done)
	await _wait(0.45)
	await _shot("menu_0.5")
	await _wait(2.1)
	var dn = Game.ui.get("demo_notice")
	print("BOOT_SHOTS notice_opened=", BootFlow.notice_opened, " notice_visible=",
		dn != null and dn.is_open and dn.is_visible_in_tree(), " seen_flag=", BootFlow.notice_seen(),
		" sheet=", (dn.get("_paper") as Control).get_global_rect() if dn != null else Rect2())
	await _shot("notice_2.5")
	get_tree().quit()


func _wait(s: float) -> void:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(s * 1000.0):
		await get_tree().process_frame


func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	_n += 1
	var path := _dir.path_join("%02d_%s.png" % [_n, label])
	img.save_png(path)
	print("BOOT_SHOTS shot ", path, " ", img.get_size())
