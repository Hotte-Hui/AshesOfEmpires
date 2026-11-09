extends RefCounted
## Flashback films of four real-history cards (TECHNICAL_ARCHITECTURE §12.15; scripts/core/flashbacks.gd,
## scenes/cinematics/flashback_*/, scripts/ui/flashback_view.gd, the button in scripts/ui/discovery_view.gd).
## Headless and stand-alone (use_director = false, mock Settings / Explore through the ui_kit overrides; the Story,
## saves, the profile and the settings file are never written):
##   the registry names four films, two per regime side, each for one existing card, 12–18 s, three shots, a
##   place-and-date caption on the first and one line on each later shot, and is unknown to the Story data;
##   both languages carry the same keys; every number and every long word of a caption stands on its card;
##   captions are readable (<= 19 characters per second);
##   each film finishes exactly once (natural end, fast-forward, skip, skip twice, skip before play, replay);
##   the picture is a pure function of t, the gate never leaves its plate, the lamps of the Nuremberg desk light
##   one after the other; reduced motion halves the drift and drops weave, flicker, scratches and dust;
##   the plates use the 13-step sepia ramp only (the two lamp sprites their accent colours);
##   the captions fit inside the gate at 100 / 125 / 150 % in German and English;
##   the view plays above its host, skips once, hands the buses back exactly and leaves the Story alone;
##   „Rückblende ansehen“ is on the four cards only, only once the card is found, and starts by button focus, F and
##   pad X while the card stays open; Game.memory_films lists the four after the story films.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const Flashbacks := preload("res://scripts/core/flashbacks.gd")
const VIEW := preload("res://scripts/ui/flashback_view.gd")
const DISCOVERY := "res://scenes/ui/DiscoveryView.tscn"
const IDS := ["LS_FB_Nuremberg", "LS_FB_Evictions", "LS_FB_Settlement", "LS_FB_Kyshtym"]
const CARDS := ["hist.reich.nuremberg_interpreters", "hist.reich.evictions", "hist.soviet.special_settlements",
	"hist.soviet.kyshtym"]
const READ_CPS := 19.0
const SCALES := [1.0, 1.25, 1.5]
const GATE := Rect2(80, 0, 480, 360)


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"reduced_motion": false, "text_scale": 1.0, "high_contrast": false}

	func get_value(key: String):
		return values.get(key)

	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockAudio extends Node:
	func ui(_id) -> void:
		pass


## The real cards, a found-set of our own.
class MockExplore extends Node:
	var real: Node = null
	var found := {}

	func card(id: String) -> Dictionary:
		return real.card(id)

	func entry(_id: String) -> Dictionary:
		return {}

	func cards_of(_id: String) -> Array:
		return []

	func is_card_found(id: String) -> bool:
		return found.has(id)


var kit: TKit
var _settings: MockSettings
var _explore: MockExplore


func run() -> Array:
	kit = TKit.new()
	var saved := UIKit.overrides.duplicate()
	_settings = MockSettings.new()
	kit.track(_settings)
	var audio := MockAudio.new()
	kit.track(audio)
	_explore = MockExplore.new()
	_explore.real = _root().get_node_or_null("Explore")
	kit.track(_explore)
	Flashbacks.reload()
	kit.run_case("registry_four_films_two_per_side_not_story", _registry)
	kit.run_case("both_languages_and_only_facts_of_the_card", _texts)
	kit.run_case("each_film_finishes_exactly_once", _finishes_once)
	kit.run_case("picture_is_a_pure_function_of_t", _pure)
	kit.run_case("reduced_motion_is_calm", _reduced)
	kit.run_case("plates_use_the_sepia_ramp_only", _palette)
	var o := saved.duplicate()
	o["Settings"] = _settings
	o["Audio"] = audio
	UIKit.overrides = o
	kit.run_case("captions_fit_at_100_125_150_in_both_languages", _captions_fit)
	kit.run_case("view_plays_skips_once_and_hands_the_sound_back", _view)
	o["Explore"] = _explore
	UIKit.overrides = o
	kit.run_case("button_only_on_the_four_found_cards", _button)
	UIKit.overrides = saved
	kit.run_case("listed_after_the_story_films", _listed)
	_settings.values["text_scale"] = 1.0
	UIKit.refresh_text_scale()
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _root() -> Window:
	return (Engine.get_main_loop() as SceneTree).root


func _strings(path: String) -> Dictionary:
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	return d["strings"] if d is Dictionary and d.get("strings") is Dictionary else {}


## Every string of data/locale/<lang>_history*.json.
func _history(lang: String) -> Dictionary:
	var out := {}
	var dir := DirAccess.open("res://data/locale")
	if dir != null:
		for f in dir.get_files():
			if f.begins_with(lang + "_history") and f.ends_with(".json"):
				out.merge(_strings("res://data/locale/" + f))
	return out


func _make(id: String, rm := -1) -> Node2D:
	var cin: Node2D = load(str(Flashbacks.film(id)["scene"])).instantiate()
	cin.set("use_director", false)
	cin.set("reduced_motion_override", rm)
	kit.mount(cin)
	return cin


func _numbers(s: String) -> Array:
	var re := RegEx.new()
	re.compile("\\d+(?:[.,]\\d{3})*")
	var out: Array = []
	for m in re.search_all(s):
		out.append(m.get_string())
	return out


func _long_words(s: String) -> Array:
	var re := RegEx.new()
	re.compile("[\\p{L}]{7,}")
	var out: Array = []
	for m in re.search_all(s):
		out.append(m.get_string().to_lower())
	return out


func _state(cin: Node2D) -> Array:
	var out: Array = [cin.get_shot_id(), (cin.get("_cover") as Polygon2D).color.a]
	for sh in cin.get("shots"):
		var sp: Sprite2D = sh["sprite"]
		out.append([sp.visible, sp.position if sp.visible else Vector2.ZERO])   # a hidden plate is not part of the picture
		for o in sh["overlays"]:
			out.append(sp.visible and (o["sprite"] as Sprite2D).visible)
	return out


# ------------------------------------------------------------------ cases
func _registry() -> bool:
	var films: Array = Flashbacks.all()
	kit.eq(films.size(), 4, "four films")
	var ids: Array = []
	var cards: Array = []
	var sides := {}
	var ex: Node = _root().get_node_or_null("Explore")
	for f in films:
		var id := str(f["id"])
		ids.append(id)
		cards.append(str(f["card"]))
		kit.ok(ex != null and ex.has_card(str(f["card"])), "%s: its card exists" % id)
		var side := str(ex.card(str(f["card"])).get("side", "")) if ex != null else ""
		sides[side] = int(sides.get(side, 0)) + 1
		kit.ok(Flashbacks.exists(id), "%s: scene exists" % id)
		kit.eq(str(Flashbacks.for_card(str(f["card"])).get("id", "")), id, "%s: found by its card" % id)
		var d := Flashbacks.duration(id)
		kit.ok(d >= 12.0 and d <= 18.0, "%s: 12–18 s (%.1f)" % [id, d])
		var shots: Array = f["shots"]
		kit.ok(shots.size() >= 2 and shots.size() <= 3, "%s: two or three shots" % id)
		var lines := 0
		for s in shots:
			if str((s as Dictionary).get("line", "")) != "":
				lines += 1
		kit.ok(lines >= 1 and lines <= 2, "%s: one or two lines" % id)
		kit.ok(str(f.get("place", "")) != "", "%s: a place-and-date caption" % id)
		kit.ok(str((shots[0] as Dictionary).get("line", "")) == "", "%s: the first shot carries the caption alone" % id)
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % str(f.get("bed", ""))), "%s: its bed exists" % id)
	kit.eq(ids, IDS, "ids in order")
	kit.eq(cards, CARDS, "cards in order")
	kit.eq(int(sides.get("reich", 0)), 2, "two on the Reich side")
	kit.eq(int(sides.get("soviet", 0)), 2, "two on the Soviet side")
	var with_film := 0
	var total := 0
	if ex != null:
		for c in ex.cards_list():
			total += 1
			if not Flashbacks.for_card(str((c as Dictionary).get("id", ""))).is_empty():
				with_film += 1
	kit.ok(total >= 29, "the history cards are loaded (%d)" % total)
	kit.eq(with_film, 4, "only four cards have a film")
	# never Story data
	kit.ok(not FileAccess.get_file_as_string("res://data/v3/cinematics.json").contains("LS_FB_"), "not a Story cinematic")
	var dir := DirAccess.open("res://data/chapters")
	if dir != null:
		for fn in dir.get_files():
			if fn.ends_with(".json"):
				kit.ok(not FileAccess.get_file_as_string("res://data/chapters/" + fn).contains("LS_FB_"), "%s does not know the films" % fn)
	kit.ok(not Flashbacks.is_film("LS_Prologue") and Flashbacks.film("nope").is_empty(), "other films are not flashbacks")
	return true


func _texts() -> bool:
	var de := _strings("res://data/locale/de_flashback.json")
	var en := _strings("res://data/locale/en_flashback.json")
	var dk: Array = de.keys()
	var ek: Array = en.keys()
	dk.sort()
	ek.sort()
	kit.eq(ek, dk, "German and English carry the same keys")
	kit.eq(str(de.get("ui.flashback.watch", "")), "Rückblende ansehen", "the German button")
	kit.eq(str(en.get("ui.flashback.watch", "")), "Watch flashback", "the English button")
	var ex: Node = _root().get_node_or_null("Explore")
	var hist := {"de": _history("de"), "en": _history("en")}
	var own := {"de": de, "en": en}
	for f in Flashbacks.all():
		var id := str(f["id"])
		var keys: Array = [str(f["place"])]
		for s in f["shots"]:
			if str((s as Dictionary).get("line", "")) != "":
				keys.append(str(s["line"]))
		var card: Dictionary = ex.card(str(f["card"])) if ex != null else {}
		for lang in ["de", "en"]:
			var t: Dictionary = own[lang]
			kit.ok(str(t.get("ui.memories.film." + id, "")) != "" and str(t.get("ui.memories.film_sub." + id, "")) != "",
				"%s %s: title and sub line on the film page" % [id, lang])
			var h: Dictionary = hist[lang]
			var card_text := (str(h.get(str(card.get("title_key", "")), "")) + " " + str(h.get(str(card.get("text_key", "")), ""))).to_lower()
			kit.ok(card_text.length() > 300, "%s %s: the card text is there" % [id, lang])
			for k in keys:
				var line := str(t.get(k, ""))
				kit.ok(line != "", "%s %s: %s has a text" % [id, lang, k])
				kit.ok(not line.contains("!"), "%s %s: %s is sober" % [id, lang, k])
				for n in _numbers(line):
					kit.ok(card_text.contains(str(n)), "%s %s: the number %s of %s stands on the card" % [id, lang, n, k])
				for w in _long_words(line):
					kit.ok(card_text.contains(str(w).substr(0, 6)), "%s %s: the word '%s' of %s comes from the card" % [id, lang, w, k])
	return true


func _finishes_once() -> bool:
	var de := _strings("res://data/locale/de_flashback.json")
	var en := _strings("res://data/locale/en_flashback.json")
	for id in IDS:
		var cin := _make(id)
		var fired := [0]
		cin.connect("finished", func(): fired[0] += 1)
		kit.ok((cin.get("missing") as Array).is_empty(), "%s: every texture is there %s" % [id, str(cin.get("missing"))])
		kit.ok(is_equal_approx(cin.get_duration(), Flashbacks.duration(id)), "%s: lasts the sum of its shots" % id)
		kit.ok(float(cin.get("max_duration")) > cin.get_duration(), "%s: the runner's limit lies beyond the end" % id)
		cin.skip()                                   # before play
		kit.eq(fired[0], 1, "%s: skip before play finishes once" % id)
		cin.skip()
		kit.eq(fired[0], 1, "%s: a second skip does nothing" % id)
		cin.play()                                   # natural end in small steps
		var guard := 0
		while not cin.is_finished() and guard < 400:
			cin.advance(0.1)
			guard += 1
		kit.eq(fired[0], 2, "%s: the natural end finishes once" % id)
		cin.advance(1.0)
		cin.skip()
		kit.eq(fired[0], 2, "%s: nothing after the end" % id)
		kit.eq(cin.get("said"), cin.chosen_lines(), "%s: caption and lines shown in order" % id)
		cin.play()                                   # fast-forward
		cin.advance(60.0)
		kit.eq(fired[0], 3, "%s: fast-forward finishes once" % id)
		cin.play()                                   # skip, twice
		cin.advance(2.0)
		cin.skip()
		cin.skip()
		kit.eq(fired[0], 4, "%s: skip then skip finishes once" % id)
		kit.eq(int(cin.get("finish_count")), 4, "%s: four runs, four ends" % id)
		kit.ok(is_equal_approx(cin.get_time(), cin.get_duration()), "%s: a skipped film stands on its last frame" % id)
		# readable: every caption has time for its length in both languages
		var pw: Vector2 = cin.place_window()
		for t in [de, en]:
			var place := str((t as Dictionary).get(str(cin.get("place_key")), ""))
			kit.ok(place.length() / maxf(0.1, pw.y - pw.x) <= READ_CPS, "%s: the caption is readable (%s)" % [id, place])
			var shots: Array = cin.get("shots")
			for i in shots.size():
				var key := str(shots[i]["line"])
				if key == "":
					continue
				var lw: Vector2 = cin.line_window(i)
				var line := str((t as Dictionary).get(key, ""))
				kit.ok(line.length() / maxf(0.1, lw.y - lw.x) <= READ_CPS,
					"%s: %s is readable (%.1f chars/s)" % [id, key, line.length() / maxf(0.1, lw.y - lw.x)])
	return true


func _pure() -> bool:
	for id in IDS:
		var cin := _make(id)
		var shots: Array = cin.get("shots")
		var d: float = cin.get_duration()
		var order: Array = []
		var t := 0.0
		while t <= d:
			cin.seek(t)
			var a := _state(cin)
			cin.seek(fmod(t * 7.3 + 1.1, d))
			cin.seek(t)
			kit.ok(TKit.strict_eq(_state(cin), a), "%s: the same picture at %.2f s after seeking away" % [id, t])
			var sid: String = cin.get_shot_id()
			if order.is_empty() or str(order[-1]) != sid:
				order.append(sid)
			var sh: Dictionary = shots[cin.shot_index(t)]
			var sp: Sprite2D = sh["sprite"]
			var r := Rect2(sp.position, sp.texture.get_size())
			kit.ok(r.encloses(GATE), "%s: the gate stays on the plate at %.2f s" % [id, t])
			kit.ok(is_equal_approx(sp.position.x * 3.0, roundf(sp.position.x * 3.0)), "%s: drift in whole screen pixels at %.2f s" % [id, t])
			t += 0.17
		var want: Array = []
		for sh in shots:
			want.append(str(sh["id"]))
		kit.eq(order, want, "%s: the shots in sheet order" % id)
		cin.seek(0.0)
		kit.eq((cin.get("_cover") as Polygon2D).color.a, 1.0, "%s: starts in black" % id)
		cin.seek(d)
		kit.eq((cin.get("_cover") as Polygon2D).color.a, 1.0, "%s: ends in black" % id)
		cin.seek(float(shots[0]["t0"]) + 2.0)
		kit.eq((cin.get("_cover") as Polygon2D).color.a, 0.0, "%s: clear inside a shot" % id)
		var st: Dictionary = cin.caption_state(float(shots[0]["t0"]) + 2.0)
		kit.ok(str(st["place"]) == str(cin.get("place_key")) and float(st["place_a"]) == 1.0 and str(st["line"]) == "",
			"%s: the first shot shows the place and date alone" % id)
		st = cin.caption_state(float(shots[1]["t0"]) + 2.0)
		kit.ok(float(st["place_a"]) == 0.0 and str(st["line"]) == str(shots[1]["line"]) and float(st["line_a"]) == 1.0,
			"%s: the second shot shows its line alone" % id)
	# the lamps of the Nuremberg desk: yellow, then red, never both
	var n := _make("LS_FB_Nuremberg")
	var desk: Dictionary = (n.get("shots") as Array)[2]
	var lamp := {}
	for o in desk["overlays"]:
		lamp[str(o["id"])] = o["sprite"]
	kit.ok(lamp.has("yellow") and lamp.has("red"), "the desk has both lamps")
	if lamp.has("yellow") and lamp.has("red"):
		var seen := {"yellow": false, "red": false}
		var first := ""
		var tt := float(desk["t0"])
		while tt < float(desk["t1"]):
			n.seek(tt)
			var y: bool = (lamp["yellow"] as Sprite2D).visible
			var r: bool = (lamp["red"] as Sprite2D).visible
			kit.ok(not (y and r), "never both lamps at %.2f s" % tt)
			if y:
				seen["yellow"] = true
			if r:
				seen["red"] = true
			if first == "" and (y or r):
				first = "yellow" if y else "red"
			tt += 0.1
		kit.ok(seen["yellow"] and seen["red"] and first == "yellow", "the yellow lamp lights first, then the red one")
		n.seek(float(desk["t0"]) + 0.5)
		kit.ok(not (lamp["yellow"] as Sprite2D).visible and not (lamp["red"] as Sprite2D).visible, "both dark at first")
	return true


func _reduced() -> bool:
	for id in IDS:
		var calm := _make(id, 1)
		var live := _make(id, 0)
		var shots: Array = calm.get("shots")
		var moved := false
		var wear := false
		for i in shots.size():
			var from: Vector2 = shots[i]["from"]
			var to: Vector2 = shots[i]["to"]
			kit.ok(calm.drift(i, 1.0, true).distance_to(from.lerp(to, 0.5)) < 0.34, "%s: half the drift in shot %d" % [id, i])
			kit.ok(live.drift(i, 1.0, false).distance_to(to) < 0.34, "%s: the whole drift without reduced motion" % id)
		var t := 0.0
		while t <= calm.get_duration():
			calm.seek(t)
			live.seek(t)
			var si: int = calm.shot_index(t)
			var sh: Dictionary = shots[si]
			var u := (t - float(sh["t0"])) / (float(sh["t1"]) - float(sh["t0"]))
			kit.ok(((sh["sprite"] as Sprite2D).position - (GATE.position - calm.drift(si, u, true))).length() < 0.01,
				"%s: no weave at %.2f s" % [id, t])
			kit.eq((calm.get("_pictures") as Node2D).modulate, Color.WHITE, "%s: no flicker at %.2f s" % [id, t])
			for s in (calm.get("_scratches") as Array) + (calm.get("_dust") as Array):
				kit.ok(not (s as Sprite2D).visible, "%s: no scratches or dust at %.2f s" % [id, t])
			if live.weave(t) != Vector2.ZERO:
				moved = true
				kit.ok(live.weave(t).x == roundf(live.weave(t).x) and live.weave(t).y == roundf(live.weave(t).y), "the weave jumps whole pixels")
			for s in (live.get("_scratches") as Array) + (live.get("_dust") as Array):
				if (s as Sprite2D).visible:
					wear = true
			t += 0.05
		kit.ok(moved and wear, "%s: weave and wear exist without reduced motion" % id)
	return true


func _palette() -> bool:
	var lay: Dictionary = Flashbacks.layout()
	var ramp := {}
	for h in lay.get("ramp", []):
		ramp[str(h).trim_prefix("#").to_lower()] = true
	kit.eq(ramp.size(), 13, "a ramp of thirteen sepia steps")
	var accents := {}
	for k in lay.get("accents", {}):
		for h in lay["accents"][k]:
			accents[str(h).trim_prefix("#").to_lower()] = true
	var films: Dictionary = lay.get("films", {})
	var plates := 0
	for fk in films:
		var shots: Dictionary = films[fk]["shots"]
		for sk in shots:
			var geo: Dictionary = shots[sk]
			var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/cinematics/flashback/" + str(geo["tex"])))
			kit.ok(img != null and img.get_width() == 512 and img.get_height() == 368, "%s/%s: a 512 x 368 plate" % [fk, sk])
			if img == null:
				continue
			plates += 1
			var bad := 0
			for y in range(0, img.get_height(), 2):
				for x in range(y % 4 / 2, img.get_width(), 2):
					if not ramp.has(img.get_pixel(x, y).to_html(false)):
						bad += 1
			kit.eq(bad, 0, "%s/%s: only ramp colours" % [fk, sk])
			for a in [geo["from"], geo["to"]]:
				kit.ok(float(a[0]) >= 2.0 and float(a[1]) >= 2.0 and float(a[0]) + 480.0 <= 510.0 and float(a[1]) + 360.0 <= 366.0,
					"%s/%s: the drift leaves two pixels for the weave" % [fk, sk])
			for o in geo.get("overlays", []):
				var oi := Image.load_from_file(ProjectSettings.globalize_path("res://assets/cinematics/flashback/" + str(o["tex"])))
				var odd := 0
				for y in oi.get_height():
					for x in oi.get_width():
						var c := oi.get_pixel(x, y)
						if c.a > 0.0 and not (c.a == 1.0 and (accents.has(c.to_html(false)) or ramp.has(c.to_html(false)))):
							odd += 1
				kit.eq(odd, 0, "%s: a lamp in its accent colours, hard-edged" % str(o["tex"]))
	kit.eq(plates, 12, "twelve plates")
	return true


func _scale(s: float) -> void:
	_settings.values["text_scale"] = s
	UIKit.refresh_text_scale()


func _new_view() -> Control:
	var fv: Control = VIEW.new()
	kit.mount(fv)
	fv.theme = UIKit.theme(false)
	fv.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	fv.size = Vector2(1920, 1080)
	return fv


func _captions_fit() -> bool:
	var fv := _new_view()
	var texts := {"de": _strings("res://data/locale/de_flashback.json"), "en": _strings("res://data/locale/en_flashback.json")}
	var gate: Rect2 = fv.gate_rect()
	kit.eq(gate, Rect2(240, 0, 1440, 1080), "the gate: 480 x 360 world pixels at x3, centred")
	for s in SCALES:
		_scale(s)
		for f in Flashbacks.all():
			for lang in ["de", "en"]:
				var t: Dictionary = texts[lang]
				var place := str(t.get(str(f["place"]), ""))
				for sh in f["shots"]:
					var key := str((sh as Dictionary).get("line", ""))
					if key == "":
						continue
					fv.show_captions("", "")
					fv.show_captions(place, str(t[key]))
					var what := "%s %s %d %%" % [key, lang, int(s * 100.0)]
					var sr: Rect2 = fv.slate_rect()
					var lr: Rect2 = fv.line_rect()
					kit.ok(gate.grow(-16.0).encloses(sr), "%s: the place and date inside the gate %s" % [what, str(sr)])
					kit.ok(gate.grow(-16.0).encloses(lr), "%s: the line inside the gate %s" % [what, str(lr)])
					kit.ok(sr.end.y + 24.0 <= lr.position.y, "%s: caption and line do not meet" % what)
					kit.ok(fv.line_count() >= 1 and fv.line_count() <= 3, "%s: at most three lines (%d)" % [what, fv.line_count()])
					var l: Label = fv.get("_line")
					var p: Label = fv.get("_place")
					kit.ok(l.size.y + 0.5 >= l.get_minimum_size().y and l.get_visible_line_count() == l.get_line_count(),
						"%s: every line of the text is shown" % what)
					kit.ok(p.size.y + 0.5 >= p.get_minimum_size().y and p.get_visible_line_count() == p.get_line_count(),
						"%s: the whole caption is shown" % what)
					kit.ok(absf((lr.position.x + lr.size.x * 0.5) - gate.get_center().x) <= 1.0, "%s: the line is centred" % what)
	_scale(1.0)
	return true


func _view() -> bool:
	var keep_story: String = Story.save_json()
	var before := {}
	for b in ["Music", "Ambience", "SFX"]:
		var i := AudioServer.get_bus_index(b)
		if i >= 0:
			before[b] = AudioServer.get_bus_volume_db(i)
	var fv := _new_view()
	var closed := [0]
	var ended: Array = []
	fv.connect("closed", func(): closed[0] += 1)
	fv.connect("film_finished", func(id, skipped): ended.append([id, skipped]))
	kit.ok(not fv.play("LS_Prologue") and not fv.play("nope") and not fv.is_open, "only flashback films are played")
	kit.ok(fv.play("LS_FB_Kyshtym"), "the film starts")
	kit.ok(fv.is_open and fv.visible and fv.get("film") != null, "the view is open with its film")
	kit.ok(fv.pauses_game and not fv.closes_on_cancel, "a pausing modal that Esc skips, not closes")
	kit.ok(not fv.play("LS_FB_Nuremberg"), "no second film while one runs")
	var film: Node2D = fv.get("film")
	kit.ok(film.is_playing() and not bool(film.get("use_director")), "it plays without the game director")
	kit.ok(fv.is_ducking(), "the world's buses are held while it runs")
	film.advance(2.0)
	fv._process(0.0)
	kit.ok((fv.get("_slate") as Control).visible and not (fv.get("_line_bg") as Control).visible, "the caption of the first shot is on")
	# the press that opened it does not skip; a later one does, once
	var ev := InputEventAction.new()
	ev.action = "ui_accept"
	ev.pressed = true
	kit.ok(fv.modal_input(ev) and not bool(fv.get("skipped")), "inside the guard nothing is skipped, the press is swallowed")
	fv.set("_opened_ms", 0)
	var key := InputEventKey.new()
	key.physical_keycode = KEY_K
	key.pressed = true
	kit.ok(fv.modal_input(key) and not bool(fv.get("skipped")), "other keys do nothing and do not pass below")
	kit.ok(fv.handle_cancel() and bool(fv.get("skipped")), "Esc skips")
	fv.skip()
	fv.handle_cancel()
	kit.eq(int(film.get("finish_count")), 1, "the film finished once")
	fv._done()                                   # what the short fade to black calls
	fv._done()
	kit.eq(closed[0], 1, "closed once")
	kit.eq(ended, [["LS_FB_Kyshtym", true]], "reported once, as skipped")
	kit.ok(not fv.is_open and fv.get("film") == null, "closed, the film is gone")
	# a full run ends by itself
	kit.ok(fv.play("LS_FB_Evictions"), "it plays again")
	(fv.get("film") as Node2D).advance(60.0)
	fv._done()
	kit.eq(ended.size(), 2, "the natural end reports too")
	kit.ok(ended.size() == 2 and not bool(ended[1][1]), "not as skipped")
	fv.get_parent().remove_child(fv)             # leaving the tree hands the buses back at once
	for b in before:
		kit.eq(AudioServer.get_bus_volume_db(AudioServer.get_bus_index(b)), before[b], "bus %s is back where it was" % b)
	kit.ok(not fv.is_ducking(), "nothing held any more")
	kit.eq(Story.save_json(), keep_story, "the Story state was never touched")
	return true


func _press(action: String) -> InputEventAction:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	return ev


## Lays the open view out as on a 1920x1080 screen (wrapped labels re-break at the width just assigned).
func _layout(dv: Control) -> void:
	var stage: Control = dv.get("_stage")
	stage.set_anchors_preset(Control.PRESET_TOP_LEFT)
	for _pass in 6:
		stage.position = Vector2.ZERO
		stage.size = Vector2(1920, 1080 - 196)
		_sort(stage)
		dv._fit_scroll()


static func _sort(n: Node) -> void:
	if n is Container:
		n.notification(Container.NOTIFICATION_SORT_CHILDREN)
	for c in n.get_children():
		if c is Label:
			c.notification(Control.NOTIFICATION_THEME_CHANGED)
		_sort(c)


func _end_film(dv: Control) -> void:
	var fv := dv.get_node_or_null("FlashbackView") as Control
	if fv != null and fv.is_open:
		fv.skip()
		fv._done()


func _button() -> bool:
	var keep_story: String = Story.save_json()
	var dv: Control = load(DISCOVERY).instantiate()
	kit.mount(dv)
	dv.theme = UIKit.theme(false)
	dv.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	dv.size = Vector2(1920, 1080)
	var all_ids: Array = []
	for c in _explore.real.cards_list():
		all_ids.append(str((c as Dictionary).get("id", "")))
	_explore.found = {}
	for id in all_ids:
		_explore.found[id] = true
	var with_button: Array = []
	for id in all_ids:
		dv.open_cards([id])
		if dv.has_flashback():
			with_button.append(id)
			kit.eq((dv.get("_fb_btn") as Button).text, "Rückblende ansehen", "%s: the button says what it does" % id)
		else:
			kit.ok(dv.get("_fb_btn") == null and str(dv.get("_fb_film")) == "", "%s: no button" % id)
		dv.close()
	with_button.sort()
	var want: Array = CARDS.duplicate()
	want.sort()
	kit.eq(with_button, want, "the button is on the four cards only (of %d)" % all_ids.size())
	# only once the card is found — or filed this moment
	_explore.found = {}
	dv.open_cards([CARDS[0]])
	kit.ok(not dv.has_flashback(), "a card that is not found offers nothing")
	var f_key := InputEventKey.new()
	f_key.physical_keycode = KEY_F
	f_key.pressed = true
	kit.ok(not dv.modal_input(f_key) and dv.get_node_or_null("FlashbackView") == null, "F does nothing there")
	dv.close()
	dv.open_cards([CARDS[0]], true)
	kit.ok(dv.has_flashback(), "a card filed right now has it")
	dv.close()
	# at 150 % the card with its button still fits above the footer
	_explore.found = {CARDS[1]: true, CARDS[2]: true}
	_scale(1.5)
	for cid in [CARDS[1], CARDS[2]]:
		dv.open_cards([cid])
		_layout(dv)
		var panel: Control = dv.get("_page_panel")
		var btn: Button = dv.get("_fb_btn")
		var pr := panel.get_global_rect()
		var br := btn.get_global_rect()
		kit.ok(pr.size.y <= 1080.0 - 196.0 - 72.0, "%s: the card with its button fits above the footer at 150 %% (%s)" % [cid, str(pr.size)])
		kit.ok(pr.grow(1.0).encloses(br) and br.size.x <= pr.size.x - 100.0, "%s: the button lies on the card at 150 %% (%s)" % [cid, str(br)])
		kit.ok(btn.get_theme_font_size("font_size") > int(dv.get_theme_font_size("font_size", "Button")), "%s: its text follows the text scale" % cid)
		dv.close()
	_scale(1.0)
	# keys, pad, focus: each starts the film above the card, which stays open on its page
	for how in ["key", "pad", "focus", "button"]:
		dv.open_cards([CARDS[2], CARDS[1]])
		dv.set("_opened_ms", 0)
		kit.ok(dv.has_flashback() and dv.flashback_key_text() == "F", "%s: the first card offers its film (F)" % how)
		var handled := true
		match how:
			"key":
				handled = dv.modal_input(f_key)
			"pad":
				var pad := InputEventJoypadButton.new()
				pad.button_index = JOY_BUTTON_X
				pad.pressed = true
				handled = dv.modal_input(pad)
			"focus":
				(dv.get("_fb_btn") as Button).grab_focus()
				handled = dv.modal_input(_press("ui_accept"))
			"button":
				(dv.get("_fb_btn") as Button).pressed.emit()
		var fv := dv.get_node_or_null("FlashbackView") as Control
		kit.ok(handled and fv != null and fv.is_open and str(fv.get("film_id")) == "LS_FB_Settlement", "%s: the film of this card plays" % how)
		kit.ok(dv.is_open and int(dv.get("page")) == 0 and dv.current_type() == "card", "%s: the card stays open underneath" % how)
		_end_film(dv)
		kit.ok(fv != null and not fv.is_open and dv.is_open and dv.has_flashback(), "%s: back on the card" % how)
		dv._page_forward()                       # the second card has its own film
		kit.ok(dv.has_flashback() and str(dv.get("_fb_film")) == "LS_FB_Evictions", "%s: the next card offers its own film" % how)
		dv.close()
		kit.ok(not dv.has_flashback(), "%s: nothing offered once the view is closed" % how)
	# E always turns the page, even with the focus on the film button
	dv.open_cards([CARDS[2], CARDS[1]])
	dv.set("_opened_ms", 0)
	(dv.get("_fb_btn") as Button).grab_focus()
	var e_key := InputEventKey.new()
	e_key.physical_keycode = KEY_E
	e_key.pressed = true
	if InputMap.has_action("interact") and e_key.is_action_pressed("interact"):
		dv.set("_scroll", null)                     # (a long page would scroll first)
		dv.modal_input(e_key)
		kit.ok(int(dv.get("page")) == 1 and not (dv.get_node_or_null("FlashbackView") as Control).is_open,
			"E goes on to the next page and starts no film")
	dv.close()
	kit.eq(Story.save_json(), keep_story, "the Story state was never touched")
	return true


func _listed() -> bool:
	var game: Node = _root().get_node_or_null("Game")
	if game == null or not game.has_method("memory_films"):
		return true
	var keep_story: String = Story.save_json()
	var keep_explore: Dictionary = Explore.state()
	var keep_data = game.memories.data
	Explore.restore({"found": [], "cards": []})
	var films: Array = game.memory_films("game")
	var ids: Array = []
	for f in films:
		ids.append(str(f["id"]))
	kit.eq(ids.slice(ids.size() - 4), IDS, "the four flashbacks close the list")
	kit.eq(str(ids[0]), "LS_Prologue", "the prologue still comes first")
	for f in films.slice(films.size() - 4):
		kit.ok(not bool(f["unlocked"]) and str(f["title"]) == "", "%s: locked and wordless before its card is found" % f["id"])
		kit.ok(game._film_exists(str(f["id"])), "%s: exists as a film" % f["id"])
		kit.eq(game._film_snapshot(str(f["id"])), "", "%s: needs no Story state" % f["id"])
	kit.ok(not game.rewatch_film("LS_FB_Kyshtym", false), "a locked flashback cannot be started")
	Explore.restore({"found": [], "cards": [CARDS[3]]})
	films = game.memory_films("game")
	var row: Dictionary = films[films.size() - 1]
	kit.ok(bool(row["unlocked"]) and str(row["title"]) != "" and str(row["sub"]) != "", "found card: the film is offered with its title")
	kit.ok(not bool(films[films.size() - 2]["unlocked"]), "the others stay locked")
	# from the main menu the profile's cards count
	game.memories.data = {"version": 1, "completed": {}, "explore": {"found": [], "cards": [CARDS[0]]}}
	var menu: Array = game.memory_films("menu")
	kit.ok(bool(menu[menu.size() - 4]["unlocked"]) and not bool(menu[menu.size() - 1]["unlocked"]), "menu: unlocked by the cards the profile remembers")
	game.memories.data = keep_data
	Explore.restore(keep_explore)
	kit.eq(Story.save_json(), keep_story, "the Story state was never touched")
	return true
