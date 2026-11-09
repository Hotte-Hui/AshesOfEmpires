extends Control
## Capture harness of the history-card flashback films (TECHNICAL_ARCHITECTURE §12.15; owner: flashback stream).
## Stand-alone: no Main scene, no level, no Story; Settings and Explore are mocked through the ui_kit overrides, so
## nothing is read from or written to the player's saves, profile or settings file.
##   --fb-out=DIR                 where the PNGs go (default user://flashback_shots)
##   --fb-mode=films|card|both    films: every shot of every film in the FlashbackView, frozen in the middle of the
##                                shot (and at --fb-times=1.2,7.5 when given); card: the four cards in the
##                                DiscoveryView with „Rückblende ansehen“
##                                game: the real Main scene (--cinematic=none: no level, no menu, no autosave) — a
##                                card in UIRoot's DiscoveryView, its film as a modal above it, skipped by a real
##                                „cancel“ event, the focus back on the card; then Game.rewatch_film (memories page)
##   --fb-films=LS_FB_Nuremberg,… (default: all)   --fb-scale=1.0|1.25|1.5   --fb-lang=de|en   --fb-rm=0|1
## Run: "$GODOT" --path . res://tests/visual/flashback_shots.tscn -- --cinematic=none --fb-mode=both --fb-out=DIR

const UIKit := preload("res://scripts/ui/ui_kit.gd")
const Flashbacks := preload("res://scripts/core/flashbacks.gd")
const VIEW := preload("res://scripts/ui/flashback_view.gd")

var args := {}


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"reduced_motion": false, "text_scale": 1.0, "high_contrast": false}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockExplore extends Node:
	var real: Node = null

	func card(id: String) -> Dictionary:
		return real.card(id)

	func entry(_id: String) -> Dictionary:
		return {}

	func cards_of(_id: String) -> Array:
		return []

	func is_card_found(_id: String) -> bool:
		return true


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	get_window().size = Vector2i(1920, 1080)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UIKit.theme(false)
	var bg := ColorRect.new()
	bg.color = Color("14171c")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var settings := MockSettings.new()
	settings.values["text_scale"] = float(args.get("fb-scale", "1.0"))
	add_child(settings)
	var explore := MockExplore.new()
	explore.real = get_node_or_null("/root/Explore")
	add_child(explore)
	var o := UIKit.overrides.duplicate()
	o["Settings"] = settings
	o["Explore"] = explore
	UIKit.overrides = o
	var lang := str(args.get("fb-lang", "de"))
	if lang != "de" and get_node_or_null("/root/Loc") != null:
		get_node("/root/Loc").set_language(lang)
	for i in 3:
		await get_tree().process_frame
	var mode := str(args.get("fb-mode", "films"))
	if mode == "films" or mode == "both":
		await _films()
	if mode == "card" or mode == "both":
		await _cards()
	if mode == "game":
		await _game()
	get_tree().quit()


func _out() -> String:
	var out := str(args.get("fb-out", "user://flashback_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	return out


func _tag() -> String:
	return "%s_%d" % [str(args.get("fb-lang", "de")), int(float(args.get("fb-scale", "1.0")) * 100.0)]


func _shoot(file: String) -> void:
	for i in 3:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(_out() + "/" + file)
	print("saved ", file, " ", img.get_size())


func _films() -> void:
	var want: PackedStringArray = str(args.get("fb-films", "")).split(",", false)
	var fv: Control = VIEW.new()
	add_child(fv)
	for f in Flashbacks.all():
		var id := str(f["id"])
		if not want.is_empty() and not want.has(id):
			continue
		if not fv.play(id):
			push_warning("flashback_shots: cannot play " + id)
			continue
		var film: Node2D = fv.get("film")
		if args.has("fb-rm"):
			film.set("reduced_motion_override", int(args["fb-rm"]))
		film.set("time_scale", 0.0)                # frozen: every frame is the one we seek to
		await get_tree().create_timer(0.35).timeout   # the modal has faded in
		var times: Array = []
		for sh in film.get("shots"):
			times.append([str(sh["id"]), (float(sh["t0"]) + float(sh["t1"])) * 0.5])
		for t in str(args.get("fb-times", "")).split(",", false):
			times.append(["t" + t, float(t)])
		for pair in times:
			film.seek(float(pair[1]))
			await _shoot("%s_%s_%s.png" % [id, pair[0], _tag()])
		fv.skip()
		while fv.is_open:
			await get_tree().process_frame
	fv.queue_free()


func _cards() -> void:
	var dv: Control = load("res://scenes/ui/DiscoveryView.tscn").instantiate()
	add_child(dv)
	for f in Flashbacks.all():
		dv.open_cards([str(f["card"])])
		await _shoot("card_%s_%s.png" % [str(f["key"]), _tag()])
		dv.close()
	dv.queue_free()


func _cancel_later(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout
	var ev := InputEventAction.new()
	ev.action = "cancel"
	ev.pressed = true
	Input.parse_input_event(ev)


func _top(ui: Node) -> String:
	var m: Control = ui.top_modal()
	return str(m.name) if m != null else "none"


func _game() -> void:
	var main: Node = load("res://scenes/main/Main.tscn").instantiate()
	add_child(main)
	for i in 5:
		await get_tree().process_frame
	var fade = Game.get("_fade")                # without a level the director leaves the screen black
	if fade is ColorRect:
		(fade as ColorRect).color = Color(0, 0, 0, 0)
	var ui: Node = Game.get("ui")
	var dv: Control = ui.get("discovery")
	dv.open_cards([str(Flashbacks.all()[1]["card"])])
	await get_tree().create_timer(0.5).timeout
	await _shoot("game_card_%s.png" % _tag())
	print("card: open=", dv.is_open, " button=", dv.has_flashback(), " top=", _top(ui), " paused=", get_tree().paused)
	var started: bool = dv.watch_flashback()
	await get_tree().create_timer(1.6).timeout
	var fv := ui.get_node_or_null("FlashbackView") as Control
	var film: Node2D = fv.get("film") if fv != null else null
	print("film: started=", started, " top=", _top(ui), " open=", fv != null and fv.is_open, " paused=", get_tree().paused,
		" t=", film.get_time() if film != null else -1.0, " ducking=", fv != null and fv.is_ducking())
	await _shoot("game_film_%s.png" % _tag())
	_cancel_later(0.05)
	await get_tree().create_timer(1.4).timeout
	var fo := get_viewport().gui_get_focus_owner()
	print("after skip: top=", _top(ui), " card open=", dv.is_open, " film open=", fv.is_open, " focus=",
		(fo as Button).text if fo is Button else str(fo), " ducking=", fv.is_ducking(), " paused=", get_tree().paused)
	await _shoot("game_back_%s.png" % _tag())
	dv.close()
	await get_tree().process_frame
	var keep: Dictionary = Explore.state()
	Explore.restore({"found": [], "cards": [str(Flashbacks.all()[3]["card"])]})
	var rows: Array = Game.memory_films("game")
	print("list: ", rows.size(), " films, last=", rows[rows.size() - 1])
	_cancel_later(1.2)
	var played: bool = await Game.rewatch_film("LS_FB_Kyshtym", false)
	print("rewatch: played=", played, " top=", _top(ui), " paused=", get_tree().paused, " story=", Story.save_json().length())
	Explore.restore(keep)
