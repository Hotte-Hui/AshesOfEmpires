extends RefCounted
## End credits (scenes/ui/EndCredits.tscn) and the main-menu "Mitwirkende" panel: every real-history card
## (Loc title, year) and every source (label, URL) appears; Esc / skip() ends the roll exactly once; the
## natural roll lasts 60–90 s; holding Space/Enter speeds it up; UIRoot exposes play_end_credits().

const TKit := preload("res://tests/support/test_kit.gd")
const UKit := preload("res://scripts/ui/ui_kit.gd")
const EC := preload("res://scripts/ui/end_credits.gd")
const END_SCENE := "res://scenes/ui/EndCredits.tscn"
const CREDITS_SCENE := "res://scenes/ui/Credits.tscn"

var kit: TKit


func run() -> Array:
	kit = TKit.new()
	kit.run_case("end_credits_list_every_card_and_source", _end_lists_all)
	kit.run_case("menu_credits_list_every_card_and_source", _menu_lists_all)
	kit.run_case("skip_ends_once", _skip_once)
	kit.run_case("natural_roll_60_to_90_s", _natural)
	kit.run_case("space_enter_speed_up", _fast)
	kit.run_case("ui_root_api", _ui_root_api)
	kit.cleanup()
	return kit.failures


func _instance(path: String) -> Control:
	var n := (load(path) as PackedScene).instantiate() as Control
	(Engine.get_main_loop() as SceneTree).root.add_child(n)
	kit.track(n)
	return n


func _end() -> Control:
	var ec := _instance(END_SCENE)
	ec.music = false
	return ec


## Checks that every card title/year and every source label/URL of the Explore data is in `texts`.
func _check_all(texts: Array, where: String) -> void:
	var have := {}
	for t in texts:
		have[str(t)] = true
	var ex := UKit.svc("Explore")
	if not kit.ok(ex != null and ex.has_method("cards_list"), where + ": Explore autoload present"):
		return
	var cards: Array = ex.cards_list()
	var expected := _cards_in_data()   # every card of every data/explore/*.json history file (16 slice + 3 Chapter 3)
	kit.eq(cards.size(), expected, where + ": %d real-history cards" % expected)
	var n_src := 0
	for c in cards:
		var cd: Dictionary = ex.card(str(c["id"]))
		var title := UKit.t(str(cd["title_key"]))
		kit.ok(title != str(cd["title_key"]), "%s: title of %s is localised" % [where, cd["id"]])
		kit.ok(have.has(title), "%s: title of %s listed" % [where, cd["id"]])
		kit.ok(have.has(str(cd["year"])), "%s: year of %s listed" % [where, cd["id"]])
		for s in cd["sources"]:
			n_src += 1
			kit.ok(have.has(str(s["label"])), "%s: source '%s' listed" % [where, s["label"]])
			if str(s.get("url", "")) != "":
				kit.ok(have.has(str(s["url"])), "%s: url %s listed" % [where, s["url"]])
	kit.ok(n_src >= cards.size(), where + ": at least one source per card (%d)" % n_src)


func _end_lists_all() -> bool:
	var ec := _end()
	ec.start()
	_check_all(ec.reel_texts(), "end credits")
	kit.ok(ec.reel_texts().has(UKit.t("credits.end.h_sources").to_upper()), "sources heading on the reel")
	kit.ok(ec.reel_texts().has(UKit.t("ui.credits.disclaimer")), "alternative-history note on the reel")
	ec.skip()
	for i in 10:
		ec.step(0.1)
	return true


func _menu_lists_all() -> bool:
	var cr := _instance(CREDITS_SCENE)
	var texts: Array = []
	EC.collect_texts(cr, texts)
	_check_all(texts, "Mitwirkende panel")
	return true


func _skip_once() -> bool:
	var ec := _end()
	var count := [0]
	ec.finished.connect(func() -> void: count[0] += 1)
	ec.start()
	kit.ok(ec.is_playing() and ec.is_open, "playing and open after start()")
	for i in 8:
		ec.step(0.5)
	ec.skip()
	ec.skip()
	for i in 10:
		ec.step(0.1)
	kit.eq(count[0], 1, "finished emitted once after two skips")
	kit.ok(not ec.is_playing() and not ec.is_open, "closed after skip")
	ec.skip()
	ec.step(1.0)
	kit.eq(count[0], 1, "skip after the end does nothing")
	# Esc through the modal input path (as UIRoot routes it)
	ec.start()
	ec.step(2.0)
	var ev := InputEventAction.new()
	ev.action = "skip" if InputMap.has_action("skip") else "ui_cancel"
	ev.pressed = true
	kit.ok(ec.modal_input(ev), "Esc consumed by the roll")
	kit.ok(ec.modal_input(ev), "second Esc consumed too")
	for i in 10:
		ec.step(0.1)
	kit.eq(count[0], 2, "Esc ends the second run exactly once")
	kit.eq(ec.finish_count, 2, "finish_count matches")
	# closing from outside (UIRoot.close_all) also finishes it, once
	ec.start()
	ec.step(1.0)
	ec.close()
	kit.eq(count[0], 3, "external close finishes once")
	ec.step(1.0)
	kit.eq(count[0], 3, "no second finish after an external close")
	return true


func _natural() -> bool:
	var ec := _end()
	ec.start()
	var t := 0.0
	var max_offset := 0.0
	while ec.is_playing() and t < 300.0:
		ec.step(0.25)
		t += 0.25
		max_offset = maxf(max_offset, ec.offset)
	kit.ok(t >= 60.0 and t <= 90.0, "natural roll lasts 60–90 s (%.1f s)" % t)
	kit.ok(max_offset > 0.0, "the reel actually moved")
	kit.eq(ec.finish_count, 1, "finished once at the natural end")
	return true


func _fast() -> bool:
	var ec := _end()
	ec.start()
	var ev := InputEventAction.new()
	ev.action = "advance" if InputMap.has_action("advance") else "ui_accept"
	ev.pressed = true
	kit.ok(ec.modal_input(ev), "Space/Enter consumed")
	var t := 0.0
	while ec.is_playing() and t < 300.0:
		ec.step(0.25)
		t += 0.25
	kit.ok(t < 30.0, "held Space/Enter shortens the roll (%.1f s)" % t)
	return true


func _ui_root_api() -> bool:
	var src := FileAccess.get_file_as_string("res://scripts/ui/ui_root.gd")
	kit.ok(src.contains("func play_end_credits() -> void:"), "UIRoot.play_end_credits() exists")
	kit.ok(src.contains("var end_credits"), "UIRoot registers end_credits")
	return true


## Number of real-history cards delivered by the data (so the check follows the data instead of a constant).
func _cards_in_data() -> int:
	var n := 0
	var dir := DirAccess.open("res://data/explore")
	if dir == null:
		return 0
	for f in dir.get_files():
		if not f.ends_with(".json"):
			continue
		var data = JSON.parse_string(FileAccess.get_file_as_string("res://data/explore/" + f))
		if data is Dictionary and data.get("cards", null) is Array:
			n += (data["cards"] as Array).size()
	return n
