extends RefCounted
## Chapter-4-part-2 cinematics LS_C4P2_Depot / _Steam / _Book / _Express / _Clock (C4P2_DESIGN §2.9,
## TECHNICAL_ARCHITECTURE §12.5): every scene is instanced in the tree and driven headless (use_director = false: no
## Game/Audio/subtitle side effects, nothing written anywhere).  finished fires exactly once per run (skip, skip
## twice, before play, natural end, fast-forward, replay); skip() is idempotent and stops the cues; each film lasts
## exactly the sum of its registered shots (data/v3/cinematics.json) in the registered order; the lines follow
## ctx.choices (c4g for Express and Clock, c4d for Clock) with defaults for contexts that lack them, are spoken in
## order, readable (<= 19 characters per second) and German; every texture and cued sound exists; the runtime
## anchors match the generators' layout.json and the sound tool's times; the picture is a pure function of t; the
## three match cuts hold (the steam jet, the book, the red lamp: same shape, same place, hard cut); the decision is
## shown (canister / empty hand, Lev's carbons, the teleprinter's strip, the desk) and reduced motion halves the
## travel and softens the flashbulb.  Owner: cine stream (round 10).

const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const Kit := preload("res://tests/support/test_kit.gd")
const SCENES := {
	"LS_C4P2_Depot": "res://scenes/cinematics/ch4p2_depot/Ch4p2Depot.tscn",
	"LS_C4P2_Steam": "res://scenes/cinematics/ch4p2_steam/Ch4p2Steam.tscn",
	"LS_C4P2_Book": "res://scenes/cinematics/ch4p2_book/Ch4p2Book.tscn",
	"LS_C4P2_Express": "res://scenes/cinematics/ch4p2_express/Ch4p2Express.tscn",
	"LS_C4P2_Clock": "res://scenes/cinematics/ch4p2_clock/Ch4p2Clock.tscn",
}
const C4G := ["", "publish_now", "protect_first"]
const C4D := ["", "name_marta", "protect_marta"]
const READ_CPS := 19.0

var kit: Kit
var _data: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	kit.run_case("registered_in_chapter_data", _registered)
	kit.run_case("contract_api_and_registered_length", _api)
	kit.run_case("shots_follow_the_registered_sheet", _shots)
	kit.run_case("skip_then_skip_finishes_once", _skip_twice)
	kit.run_case("skip_before_play_finishes_once", _skip_before_play)
	kit.run_case("natural_end_and_fast_forward_finish_once", _natural_end)
	kit.run_case("replay_finishes_once_per_run", _replay)
	kit.run_case("lines_spoken_in_order_fit_readable_german", _spoken)
	kit.run_case("skip_mid_run_stops_cues", _skip_stops_cues)
	kit.run_case("reduced_motion_and_full_motion_run", _reduced)
	kit.run_case("textures_present_and_layout_in_sync", _assets)
	kit.run_case("every_cue_sound_exists", _sounds)
	kit.run_case("frames_are_a_pure_function_of_t", _pure)
	kit.run_case("depot_sound_sync", _depot_sync)
	kit.run_case("sound_timings_match_the_pictures", _sync_all)
	kit.run_case("match_cut_steam_same_jet", _cut_steam)
	kit.run_case("match_cut_book_same_object", _cut_book)
	kit.run_case("match_cut_red_lamp_same_circle", _cut_lamp)
	kit.run_case("decision_shown_never_explained", _decision_shown)
	kit.run_case("reduced_motion_halves_travel_softens_flash", _rm_travel)
	kit.run_case("memory_film_titles", _film_titles)
	kit.run_case("macro_to_medium_cuts_hard_no_double_exposure", _no_dissolve)
	kit.run_case("close_figures_are_the_dialogue_busts", _busts)
	kit.run_case("kolonne_4_works_as_people_not_a_file", _gang_varied)
	kit.run_case("platform_k_konrads_lane_is_clear", _m4_lane)
	kit.run_case("courtyard_tilts_to_hannas_window", _k1_tilt)
	kit.run_case("lev_gesture_reads_at_a_glance", _lev_gesture)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _make(id: String, choices := {}, rm := -1) -> Node:
	var s: Node = load(SCENES[id]).instantiate()
	s.set("use_director", false)
	if rm >= 0:
		s.set("reduced_motion_override", rm)
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	kit.track(s)
	s.configure({"choices": choices, "flags": {}, "symbols": true})
	return s


func _counter(s: Node) -> Array:
	var n := [0]
	s.finished.connect(func() -> void: n[0] += 1)
	return n


func _run_to_end(s: Node, dt := 0.05) -> int:
	var guard := 0
	while not s.is_finished() and guard < 20000:
		s.advance(dt)
		guard += 1
	return guard


func _drop(s: Node) -> void:
	if is_instance_valid(s):
		if s.get_parent():
			s.get_parent().remove_child(s)
		s.free()


func _choice_sets(id: String) -> Array:
	var out: Array = [{}]
	if id in ["LS_C4P2_Express", "LS_C4P2_Clock"]:
		for g in C4G:
			for d in C4D:
				out.append({"c4g_choose": g, "c4d_choose": d})
	return out


func _seq(id: String) -> Dictionary:
	if _data.is_empty():
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/cinematics.json"))
		_data = d if d is Dictionary else {}
	for s in _data.get("sequences", []):
		if str(s.get("id", "")) == id:
			return s
	return {}


func _layout() -> Dictionary:
	var p := "res://assets/cinematics/c4p2/layout.json"
	if not FileAccess.file_exists(p):
		return {}
	var L = JSON.parse_string(FileAccess.get_file_as_string(p))
	return L if L is Dictionary else {}


func _snapshot(s: Node) -> Array:
	var out: Array = []
	for c in s.get_children():
		if c is CanvasItem:
			out.append([c.name, (c as CanvasItem).visible])
			for g in c.get_children():
				if g is Sprite2D:
					out.append([g.name, (g as Sprite2D).visible, (g as Sprite2D).frame, (g as Sprite2D).position,
						(g as Sprite2D).modulate, (g as Sprite2D).region_rect])
				elif g is Node2D:
					out.append([g.name, (g as Node2D).visible, (g as Node2D).position])
	return out


func _src_floats(src: String, name: String) -> Array:
	var rx := RegEx.new()
	rx.compile("(?m)^" + name + " = \\(?([0-9., ]+)\\)?")
	var m := rx.search(src)
	var vals: Array = []
	if m:
		for v in m.get_string(1).split(",", false):
			if v.strip_edges() != "":
				vals.append(float(v))
	return vals


## two lists of times equal within a millisecond
func _close(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if absf(float(a[i]) - float(b[i])) > 0.001:
			return false
	return true


# ------------------------------------------------------------------ cases
func _registered() -> bool:
	var ext = ChapterExt.new()
	for id in SCENES:
		kit.eq(str(ext.cinematics.get(id, "")), SCENES[id], "data/chapters registers %s" % id)
		kit.ok(ext.has_cinematic(id), "%s scene exists" % id)
	return true


func _api() -> bool:
	for id in SCENES:
		var s := _make(id)
		kit.ok(s is Node2D, "%s root is Node2D" % id)
		for m in ["configure", "play", "skip", "chosen_lines", "seek", "advance", "is_finished", "get_shot_id"]:
			kit.ok(s.has_method(m), "%s has %s()" % [id, m])
		kit.ok(s.has_signal("finished"), "%s has signal finished" % id)
		kit.eq(str(s.get("grade_preset")), "c3_cine", "%s grade_preset" % id)
		var total := 0.0
		for sh in _seq(id).get("shots", []):
			total += float(sh.get("duration_s", 0))
		kit.ok(total > 0.0, "%s registered in data/v3/cinematics.json" % id)
		kit.ok(absf(float(s.get_duration()) - total) < 0.01, "%s lasts %.2f s == the registered shots (%.2f s)" %
			[id, s.get_duration(), total])
		kit.ok(float(s.get("max_duration")) > float(s.get_duration()), "%s max_duration > duration" % id)
		_drop(s)
	return true


func _shots() -> bool:
	for id in SCENES:
		var s := _make(id)
		s.play()
		var start := 0.0
		for sh in _seq(id).get("shots", []):
			var d := float(sh.get("duration_s", 0))
			for probe in [start + 0.01, start + d * 0.5, start + d - 0.01]:
				s.seek(probe)
				kit.eq(str(s.get_shot_id()), str(sh["id"]), "%s at %.2f s is shot %s" % [id, probe, sh["id"]])
			start += d
		_drop(s)
	return true


func _skip_twice() -> bool:
	for id in SCENES:
		var s := _make(id)
		var n := _counter(s)
		s.play()
		s.advance(0.7)
		s.skip()
		s.skip()
		kit.eq(n[0], 1, "%s: play, skip, skip -> finished once" % id)
		kit.ok(s.is_finished(), "%s is_finished after skip" % id)
		kit.ok(absf(s.get_time() - s.get_duration()) < 0.001, "%s skip jumps to the final frame" % id)
		s.advance(1.0)
		kit.eq(n[0], 1, "%s: advancing after skip emits nothing" % id)
		_drop(s)
	return true


func _skip_before_play() -> bool:
	for id in SCENES:
		var s := _make(id)
		var n := _counter(s)
		s.skip()
		s.skip()
		kit.eq(n[0], 1, "%s: skip before play -> finished once" % id)
		_drop(s)
	return true


func _natural_end() -> bool:
	for id in SCENES:
		for dt in [0.05, 1.7]:
			var s := _make(id)
			var n := _counter(s)
			s.play()
			_run_to_end(s, dt)
			kit.ok(s.is_finished(), "%s reaches its natural end (dt %.2f)" % [id, dt])
			kit.eq(n[0], 1, "%s: natural end (dt %.2f) -> finished once" % [id, dt])
			s.skip()
			s.skip()
			kit.eq(n[0], 1, "%s: skip after the natural end emits nothing" % id)
			_drop(s)
	return true


func _replay() -> bool:
	for id in SCENES:
		var s := _make(id)
		var n := _counter(s)
		s.play()
		s.skip()
		s.play()
		kit.ok(not s.is_finished(), "%s: play() after skip starts a new run" % id)
		_run_to_end(s, 0.1)
		s.skip()
		kit.eq(n[0], 2, "%s: two runs -> finished exactly twice" % id)
		_drop(s)
	return true


func _spoken() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id):
			var s := _make(id, ch)
			s.play()
			_run_to_end(s, 0.05)
			kit.eq(s.get("said"), s.chosen_lines(), "%s %s: subtitles spoken in order" % [id, str(ch)])
			var end := -1.0
			for c in s.get("_cues"):
				if not (c as Dictionary).has("say"):
					continue
				var t0 := float(c["t"])
				kit.ok(t0 >= end - 0.001, "%s %s: %s does not overlap the previous line" % [id, str(ch), c["say"]])
				end = t0 + float(c["dur"])
				kit.ok(end <= s.get_duration() + 0.05, "%s %s: %s ends inside the film (%.2f)" % [id, str(ch), c["say"], end])
				var chars := Loc.t(str(c["say"])).length()
				kit.ok(float(chars) / float(c["dur"]) <= READ_CPS + 0.001, "%s: %s readable (%d chars in %.2f s)" %
					[id, c["say"], chars, c["dur"]])
			for key in s.chosen_lines():
				kit.ok(Loc.has(str(key)), "%s: locale has %s" % [id, key])
				kit.ok(Loc.t(str(key)) != str(key) and Loc.t(str(key)).length() > 5, "%s: %s has German text" % [id, key])
			_drop(s)
	return true


func _skip_stops_cues() -> bool:
	for id in SCENES:
		var s := _make(id)
		s.play()
		s.advance(0.1)
		var before: int = (s.get("said") as Array).size()
		s.skip()
		s.advance(40.0)
		kit.eq((s.get("said") as Array).size(), before, "%s: no lines after skip" % id)
		_drop(s)
	return true


func _reduced() -> bool:
	for rm in [1, 0]:
		for id in SCENES:
			var s := _make(id, {}, rm)
			var n := _counter(s)
			s.play()
			_run_to_end(s, 0.04)
			kit.eq(n[0], 1, "%s reduced_motion=%d: finished once" % [id, rm])
			kit.ok(s.reduced_motion() == (rm == 1), "%s reduced_motion override %d" % [id, rm])
			_drop(s)
	return true


func _assets() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id).slice(0, 4):
			var s := _make(id, ch)
			s.play()
			for tt in [0.5, 3.0, 6.0, 10.0, 12.5, 15.0, 19.0, 22.0]:
				if tt < s.get_duration():
					s.seek(tt)
			kit.eq(s.get("missing"), [], "%s %s: every texture exists" % [id, str(ch)])
			_drop(s)
	var L := _layout()
	if not kit.ok(not L.is_empty(), "layout.json written by tools/pixelgen/env_c4p2_cine.py"):
		return true
	var need := {
		"depot": ["p1_fire", "p1_masts", "p1_vent", "p1_gang", "p1_rest", "p1_guard", "cycle_fps", "contact_frame",
			"near_gang", "bites", "p2_floor", "p2_walk", "p2_lamp", "p2_fitter", "p2_cyl", "p3_win", "p3_irina_at",
			"p3_samovar"],
		"steam": ["jet_base", "jet_size", "m1_valve", "m1_tender", "m1_chute", "m1_poles", "tarp_at", "tarp_w", "tarp_t",
			"tarp_snaps", "coal_run", "m1_workers", "m1_alexei", "m3_valve", "hall_w", "m4_ox", "board", "board_row_at",
			"flap_t", "m4_people", "m4_konrad", "m4_feet"],
		"book": ["card", "card_scr", "trace_scr", "swing", "edge_b1", "macro", "edge_m", "ktip", "gtip", "atip",
			"glove_rest", "book_shut", "book_open", "b4_tarp", "b4_people", "match_t", "march_t0", "march_bpm"],
		"express": ["lamp_c", "lamp_r", "car_w", "win1", "ekdahl_at", "train_t0", "train_a", "gesture_t", "nod_t", "vp",
			"trail_t", "trail_n", "trail_cell", "trail_k", "track_b", "x2_alexei", "x2_lev", "carbons_t", "street_w",
			"x4_lamp", "gate", "x4_konrad", "x4_feet", "sbahn_t"],
		"clock": ["car_path", "car_t", "car_cell", "car_doors", "candle", "hall", "door_e", "wagon", "flash_t",
			"door_open", "door_shut", "alexei", "irina", "tty", "clock_c", "type_t0", "type_cps", "tape_x", "text",
			"k4_card", "k4_thing"],
	}
	for sec in need:
		var S: Dictionary = L.get(sec, {})
		for k in need[sec]:
			kit.ok(S.has(k), "layout %s.%s" % [sec, k])
	kit.eq((L.get("depot", {}).get("p1_gang", []) as Array).size(), 11, "Kolonne 4: eleven shovels in the line")
	kit.eq(L.get("clock", {}).get("text", {}), {"publish_now": "ПЕРЕДАЧА ПРИОСТАНОВЛЕНА ТЧК",
		"protect_first": "С-17/45 УБЫЛ КОРДОН-17 ТЧК"}, "the teleprinter's two messages (C4P2_DESIGN §2.9 k3)")
	var stand: Dictionary = L.get("standins", {})
	for cid in stand:
		print("      pending (round 10): %s drawn from stand-in %s until its rig spec exists; rerun env_c4p2_cine.py" %
			[cid, stand[cid]])
	return true


func _sounds() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id).slice(0, 4):
			var s := _make(id, ch)
			for c in s.get("_cues"):
				var d: Dictionary = c
				if d.has("sfx"):
					var n := str(d["sfx"])
					kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % n) or
						ResourceLoader.exists("res://assets/audio/sfx/%s_1.wav" % n), "%s: sfx %s exists" % [id, n])
				if d.has("amb") and str(d["amb"]) != "":
					kit.ok(ResourceLoader.exists("res://assets/audio/amb/%s.wav" % str(d["amb"])), "%s: amb %s" % [id, d["amb"]])
				if d.has("music") and str(d["music"]) != "":
					kit.ok(ResourceLoader.exists("res://assets/audio/music/%s.wav" % str(d["music"])), "%s: music %s" % [id, d["music"]])
				if d.has("bed"):
					kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % str(d["bed"])), "%s: bed %s" % [id, d["bed"]])
			_drop(s)
	return true


func _pure() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id).slice(0, 3):
			var s := _make(id, ch)
			s.play()
			for tt in [0.6, 2.1, 4.4, 5.6, 7.3, 9.95, 12.2, 17.0, 18.3, 21.0]:
				if tt > s.get_duration():
					continue
				s.seek(tt)
				var a := _snapshot(s)
				s.seek(s.get_duration() * 0.9)
				s.seek(tt)
				kit.eq(_snapshot(s), a, "%s %s: the frame at %.2f s is the same after seeking away and back" % [id, str(ch), tt])
			_drop(s)
	return true


## the shovels, the valve, Alexei's boots and the telephone are cut into the beds where the pictures put them
func _depot_sync() -> bool:
	var src := FileAccess.get_file_as_string("res://tools/audiogen/c4p2_cine_audio.py")
	if not kit.ok(src != "", "tools/audiogen/c4p2_cine_audio.py readable"):
		return true
	var gd = load("res://scenes/cinematics/ch4p2_depot/ch4p2_depot.gd")
	kit.eq(_src_floats(src, "VALVE_LIFT"), [gd.VALVE_LIFT], "valve: picture == c4p2cine_depot")
	kit.eq(_src_floats(src, "PHONE_RING"), [gd.PHONE_RING], "telephone: picture == c4p2cine_window")
	var s := _make("LS_C4P2_Depot")
	var L := _layout()
	kit.eq(s.bite_times(), L.get("depot", {}).get("bites", []), "shovel bites: runtime == layout (the sound tool reads them)")
	var steps: Array = s.step_times()
	kit.ok(_close(_src_floats(src, "ALEXEI_STEPS"), steps), "Alexei's boots: picture == c4p2cine_arch %s" % str(steps))
	kit.ok(steps.size() >= 9, "Alexei walks the whole of p2 (%d steps)" % steps.size())
	# the beds start where their shots start
	var starts := {}
	for c in s.get("_cues"):
		if (c as Dictionary).has("bed"):
			starts[str(c["bed"])] = float(c["t"])
	kit.eq(starts.get("c4p2cine_depot", -1.0), 0.0, "c4p2cine_depot starts with p1")
	kit.eq(starts.get("c4p2cine_arch", -1.0), 5.0, "c4p2cine_arch starts with p2")
	kit.eq(starts.get("c4p2cine_window", -1.0), 9.0, "c4p2cine_window starts with p3")
	# Irina looks up after the ring, not before
	s.play()
	s.seek(gd.PHONE_RING - 0.05)
	kit.eq((s.get("_irina") as Sprite2D).frame, 0, "Irina still writes when the telephone rings")
	s.seek(gd.IRINA_LOOK + 0.05)
	kit.eq((s.get("_irina") as Sprite2D).frame, 1, "Irina has looked up")
	_drop(s)
	return true


## coal, tarpaulin, the jet's one hiss, the board, Konrad's steps (Steam); the book, the band (Book); the train, the
## knock, the street (Express); the car, the Kordon, the teleprinter, the tick (Clock): picture == sound tool
func _sync_all() -> bool:
	var src := FileAccess.get_file_as_string("res://tools/audiogen/c4p2_cine_audio.py")
	if not kit.ok(src != "", "tools/audiogen/c4p2_cine_audio.py readable"):
		return true
	var L := _layout()
	var S: Dictionary = L.get("steam", {})
	kit.eq(_src_floats(src, "COAL_RUN"), S.get("coal_run", []), "coal run: picture == c4p2cine_coal")
	kit.eq(_src_floats(src, "TARP_SNAPS"), S.get("tarp_snaps", []), "tarpaulin snaps: picture == c4p2cine_coal")
	kit.eq(_src_floats(src, "FLAP_T"), S.get("flap_t", []), "split-flap board: picture == c4p2cine_hall")
	var st = load("res://scenes/cinematics/ch4p2_steam/ch4p2_steam.gd")
	kit.eq(_src_floats(src, "JET_T0"), [st.JET_T0], "the jet's hiss starts with m2")
	kit.eq(_src_floats(src, "CUT"), [st.CUT], "the hiss changes rooms on the cut")
	var sm := _make("LS_C4P2_Steam")
	kit.ok(_close(_src_floats(src, "KONRAD_M4"), sm.konrad_steps()), "Konrad's steps on platform K: picture == c4p2cine_hall")
	_drop(sm)
	var bk = load("res://scenes/cinematics/ch4p2_book/ch4p2_book.gd")
	kit.eq(_src_floats(src, "BOOK_SHUT"), [bk.BOOK_SHUT], "the book shuts: picture == c4p2cine_shut")
	kit.eq(_src_floats(src, "BOOK_OPEN"), [bk.BOOK_OPEN], "the book opens: picture == c4p2cine_canteen")
	kit.eq(_src_floats(src, "SLIDE_T"), bk.SLIDE_T, "the card slides: picture == c4p2cine_dining")
	kit.eq(_src_floats(src, "CLOSE_T"), bk.CLOSE_T, "the pages lift: picture == c4p2cine_dining")
	kit.eq(_src_floats(src, "MARCH_T0"), [bk.MARCH_T0], "the band strikes up: picture == c4p2cine_band")
	kit.eq(_src_floats(src, "MARCH_BPM"), [bk.MARCH_BPM], "the band's tempo: the drum on the picture's beat")
	kit.eq(_src_floats(src, "MATCH_STRIKE"), [bk.MATCH_T[0]], "the match: picture == c4p2cine_band")
	var ex = load("res://scenes/cinematics/ch4p2_express/ch4p2_express.gd")
	kit.eq(_src_floats(src, "WHISTLE"), [ex.WHISTLE], "whistle: picture == c4p2cine_express")
	kit.eq(_src_floats(src, "COUPLINGS"), ex.COUPLINGS, "couplings: picture == c4p2cine_express")
	kit.eq(_src_floats(src, "KNOCK_T"), [ex.KNOCK_T], "the last rail joint: picture == c4p2cine_knock")
	kit.eq(_src_floats(src, "WIPE"), ex.WIPE, "the coat's swish: picture == c4p2cine_street")
	kit.eq(_src_floats(src, "SBAHN_T"), ex.SBAHN_T, "the S-Bahn: picture == c4p2cine_street")
	var es := _make("LS_C4P2_Express")
	kit.ok(_close(_src_floats(src, "KONRAD_STEPS"), es.konrad_steps()), "Konrad's steps in the snow: picture == c4p2cine_street")
	kit.ok(absf(float(es.get("X").get("train_t0", 0.0)) - _src_floats(src, "BRAKE_OFF")[0] - 0.05) < 0.001,
		"the brakes come off just before the car rolls")
	_drop(es)
	var ck = load("res://scenes/cinematics/ch4p2_clock/ch4p2_clock.gd")
	kit.eq(_src_floats(src, "CAR_DOORS"), ck.CAR_DOORS, "car doors: picture == c4p2cine_k14")
	kit.eq(_src_floats(src, "CAR_T"), ck.CAR_T, "the car rolls out: picture == c4p2cine_k14")
	kit.eq(_src_floats(src, "FLASH_T"), [ck.FLASH_T], "the flashbulb: picture == c4p2cine_kordon_publish")
	kit.eq(_src_floats(src, "DOOR_OPEN"), [ck.DOOR_OPEN], "Tür Ost opens: picture == c4p2cine_kordon_protect")
	kit.eq(_src_floats(src, "DOOR_SHUT"), [ck.DOOR_SHUT], "Tür Ost shuts: picture == c4p2cine_kordon_protect")
	kit.eq(_src_floats(src, "TYPE_T0"), [ck.TYPE_T0], "the teleprinter starts: picture == c4p2cine_tty_*")
	kit.eq(_src_floats(src, "TYPE_CPS"), [ck.TYPE_CPS], "the teleprinter's speed: picture == c4p2cine_tty_*")
	kit.eq(_src_floats(src, "TICK_END"), [ck.TICK_END], "the tick stops on k5")
	var c := _make("LS_C4P2_Clock")
	for v in ["publish_now", "protect_first"]:
		var tt: Array = c.type_times(v)
		kit.ok(tt.size() > 10 and float(tt[-1]) < 16.0, "%s: the tape is typed inside k3 (%d keys)" % [v, tt.size()])
	var music := false
	var tick := false
	for cue in c.get("_cues"):
		var d: Dictionary = cue
		if d.has("music") and str(d["music"]) == "mus_c4p2_clock":
			music = true
			kit.eq(float(d["t"]), 0.0, "the clock music starts with the film (its tick on the second hand)")
		if d.has("bed") and str(d["bed"]) == "c4p2cine_tick":
			tick = true
	kit.ok(music != tick, "either the music's tick or the stand-in tick bed, never both")
	kit.eq(music, ResourceLoader.exists("res://assets/audio/music/mus_c4p2_clock.wav"), "the music is used when it exists")
	var hand: Array = []
	for tt in [10.95, 11.05, 11.95, 12.05]:
		hand.append(c.second_angle(tt))
	kit.ok(hand[0] != hand[1] and hand[1] == hand[2] and hand[2] != hand[3], "the second hand steps on the whole seconds")
	_drop(c)
	return true


## the steam jet: the same sheet frame at the same place on both sides of the hard cut (Karsk valve -> Berlin valve)
func _cut_steam() -> bool:
	var s := _make("LS_C4P2_Steam")
	s.play()
	s.seek(5.49)
	var j2: Sprite2D = s.get("_jet2")
	var j3: Sprite2D = s.get("_jet3")
	var m2: Node2D = s.get("m2")
	var m3: Node2D = s.get("m3a")
	kit.ok(m2.visible and not m3.visible, "at 5.49 s the Karsk valve")
	var f_before := j2.frame
	var p_before := j2.position
	s.seek(5.5)
	kit.ok(m3.visible and not m2.visible, "at 5.50 s the Berlin valve (hard cut)")
	kit.eq(j3.position, p_before, "the jet stands at the same place across the cut")
	kit.ok(absi(j3.frame - f_before) <= 1, "the jet's loop runs on through the cut (frame %d -> %d)" % [f_before, j3.frame])
	s.seek(6.0)
	kit.ok(m3.visible, "m3 opens on the macro")
	s.seek(7.4)
	kit.ok(not m3.visible and (s.get("hall") as Node2D).visible, "the hard cut has gone to the hall")
	s.seek(6.84)
	kit.eq(s.board_frame(6.84), 0, "the board still shows the old train before its flaps run")
	kit.eq(s.board_frame(8.2), 9, "the board shows D 303 KARSK 21.10 after its run")
	_drop(s)
	return true


## the book: the same 3-D model by the same macro camera -- shut in Berlin at the cut, shut in Karsk after it
func _cut_book() -> bool:
	var s := _make("LS_C4P2_Book")
	s.play()
	s.seek(4.99)
	kit.ok((s.get("b2") as Node2D).visible, "at 4.99 s the Berlin macro")
	kit.eq((s.get("_book2") as Sprite2D).frame, 5, "the book is shut at the cut")
	s.seek(5.0)
	kit.ok((s.get("b3a") as Node2D).visible and not (s.get("b2") as Node2D).visible, "at 5.00 s the Karsk macro (hard cut)")
	kit.eq((s.get("_book3") as Sprite2D).frame, 5, "the same shut book opens the Karsk side")
	s.seek(3.6)
	kit.ok((s.get("_book2") as Sprite2D).frame < 5, "b2 begins with the book still open")
	s.seek(5.6)
	kit.eq((s.get("_book3") as Sprite2D).frame, 0, "the cover is up before the cut to the table")
	var a: Texture2D = load("res://assets/cinematics/c4p2/book/b2_book.png")
	var b: Texture2D = load("res://assets/cinematics/c4p2/book/b3a_book.png")
	kit.eq(a.get_size(), b.get_size(), "both macro sheets come from the same camera")
	var ia := a.get_image()
	var ib := b.get_image()
	var same := 0
	var total := 0
	for y in range(46, 314, 6):
		for x in range(0, 640, 6):
			var pa := ia.get_pixel(5 * 640 + x, y).a > 0.5
			var pb := ib.get_pixel(5 * 640 + x, y).a > 0.5
			total += 1
			if pa == pb:
				same += 1
	kit.ok(float(same) / float(total) > 0.995, "the shut book has the same silhouette in Berlin and Karsk (%d/%d)" % [same, total])
	_drop(s)
	return true


## the red lamp: the tail lamp and the warning lamp share their centre and size; hard cut on 9.5 s
func _cut_lamp() -> bool:
	var L := _layout()
	var X: Dictionary = L.get("express", {})
	var c: Array = X.get("lamp_c", [])
	kit.eq(c.size(), 2, "express.lamp_c = the shared centre")
	var s := _make("LS_C4P2_Express")
	s.play()
	s.seek(9.49)
	kit.ok((s.get("x3") as Node2D).visible, "at 9.49 s the tail lamp")
	s.seek(9.5)
	kit.ok((s.get("x4a") as Node2D).visible and not (s.get("x3") as Node2D).visible, "at 9.50 s the warning lamp")
	for rel in ["express/x3_lamp.png", "express/x4_lamp.png"]:
		var img := (load("res://assets/cinematics/c4p2/" + rel) as Texture2D).get_image()
		var p := img.get_pixel(int(c[0]) + 12, int(c[1]) + 12)
		kit.ok(p.r > 0.5 and p.r > p.g * 1.8 and p.r > p.b * 1.8, "%s: red lens at the shared centre" % rel)
		var q := img.get_pixel(int(c[0]) + int(X.get("lamp_r", 46)) + 30, int(c[1]))
		kit.ok(not (q.r > 0.6 and q.g < 0.3), "%s: the lens ends at the shared radius" % rel)
	_drop(s)
	return true


## the decision is shown: Ekdahl's hand, Lev's carbons, the Kordon, the teleprinter's tape, the desk
func _decision_shown() -> bool:
	for g in ["publish_now", "protect_first", ""]:
		var pub: bool = g != "protect_first"
		var e := _make("LS_C4P2_Express", {"c4g_choose": g})
		e.play()
		e.seek(0.3)
		kit.eq((e.get("_ekdahl") as Sprite2D).frame, 0, "x1 c4g=%s: hands down at first" % g)
		e.seek(2.0)
		kit.eq((e.get("_ekdahl") as Sprite2D).frame, 1 if pub else 3, "x1 c4g=%s: %s" % [g, "the canister" if pub else "the empty hand and the nod"])
		e.seek(5.8)
		var lf: int = (e.get("_lev") as Sprite2D).frame
		kit.ok((lf >= 8) == (not pub), "x2 c4g=%s: Lev %s" % [g, "has empty hands" if pub else "buttons the carbons in"])
		kit.eq(e.chosen_lines()[0], "cin.c4p2.express.alexei_" + ("publish" if pub else "protect"), "x2 c4g=%s: Alexei's thought" % g)
		_drop(e)
		var c := _make("LS_C4P2_Clock", {"c4g_choose": g})
		c.play()
		c.seek(7.0)
		kit.eq((c.get("_door") as Sprite2D).visible, not pub, "k2 c4g=%s: Tür Ost %s" % [g, "stays shut" if pub else "stands open"])
		c.seek(c.FLASH_T + 0.05)
		kit.eq((c.get("_flash") as Sprite2D).visible, pub, "k2 c4g=%s: %s flashbulb" % [g, "a" if pub else "no"])
		c.seek(15.5)
		var tapes: Dictionary = c.get("_tapes")
		kit.ok((tapes["publish_now"] as Sprite2D).visible == pub and (tapes["protect_first"] as Sprite2D).visible == (not pub),
			"k3 c4g=%s: the teleprinter types %s" % [g, "the suspension" if pub else "the departure"])
		c.seek(17.0)
		kit.eq((c.get("_canister") as Sprite2D).visible, not pub, "k4 c4g=%s: the film canister" % g)
		kit.eq((c.get("_folder") as Sprite2D).visible, pub, "k4 c4g=%s: Lev's empty folder" % g)
		_drop(c)
	for d in ["name_marta", "protect_marta", ""]:
		var c2 := _make("LS_C4P2_Clock", {"c4d_choose": d, "c4g_choose": "protect_first"})
		var want := "cin.c4p2.clock.konrad_" + ("protect" if d == "protect_marta" else "name")
		kit.eq(c2.chosen_lines()[1], want, "k1 c4d=%s: Konrad's thought" % d)
		kit.eq(c2.chosen_lines()[4], "cin.c4p2.clock.protect", "k4: Alexei's thought follows c4g")
		_drop(c2)
	return true


## reduced motion halves the travel (the car pulling away, the shovels' pace) and softens the flashbulb
func _rm_travel() -> bool:
	var full := _make("LS_C4P2_Express", {}, 0)
	var half := _make("LS_C4P2_Express", {}, 1)
	var a: float = full.car_x(4.0)
	var b: float = half.car_x(4.0)
	kit.ok(absf(b - a * 0.5) <= 1.0, "x1: reduced motion halves the car's travel (%.0f vs %.0f)" % [b, a])
	_drop(full)
	_drop(half)
	for rm in [0, 1]:
		var c := _make("LS_C4P2_Clock", {"c4g_choose": "publish_now"}, rm)
		c.play()
		var frames := {}
		var tt: float = c.FLASH_T
		while tt < c.FLASH_T + 1.0:
			c.seek(tt)
			var f: Sprite2D = c.get("_flash")
			if f.visible:
				frames[f.frame] = true
				if rm == 1:
					kit.ok(f.modulate.a <= 0.56, "rm: the flashbulb is a soft brightening (alpha %.2f)" % f.modulate.a)
			tt += 0.02
		if rm == 1:
			kit.eq(frames.keys(), [2], "rm: only the soft glow frame of the flashbulb")
		else:
			kit.ok(frames.size() == 3, "the flashbulb: burst, halo, fading glow")
		_drop(c)
	return true


func _film_titles() -> bool:
	for id in SCENES:
		kit.ok(Loc.has("ui.memories.film." + id), "memory film title for %s" % id)
		kit.ok(Loc.has("ui.memories.film_sub." + id), "memory film subtitle for %s" % id)
	return true


## the macro_to_medium moves (b3, m3) are hard cuts on the movement with a small settle -- no dithered double
## exposure: no shader material on the macro groups, and at no time are macro and medium visible together
func _no_dissolve() -> bool:
	var b := _make("LS_C4P2_Book")
	b.play()
	kit.ok((b.get("b3a") as Node2D).material == null, "b3a has no dissolve material")
	var tt := 5.0
	while tt < 9.0:
		b.seek(tt)
		kit.ok(not ((b.get("b3a") as Node2D).visible and (b.get("b3b") as Node2D).visible), "b3 at %.2f: one picture" % tt)
		tt += 0.05
	b.seek(b.CUT_B3 - 0.01)
	kit.ok((b.get("b3a") as Node2D).visible, "the macro holds until the cut")
	b.seek(b.CUT_B3)
	kit.ok((b.get("b3b") as Node2D).visible, "the table at the cut")
	kit.ok((b.get("b3b") as Node2D).position.y > 0.0, "the camera settles back after the cut")
	b.seek(8.0)
	kit.eq((b.get("b3b") as Node2D).position.y, 0.0, "the camera has settled")
	_drop(b)
	var st := _make("LS_C4P2_Steam")
	st.play()
	kit.ok((st.get("m3a") as Node2D).material == null, "m3a has no dissolve material")
	tt = 5.5
	while tt < 9.5:
		st.seek(tt)
		var macro: bool = (st.get("m3a") as Node2D).visible
		kit.ok(not (macro and tt >= st.CUT_M3), "m3 at %.2f: the macro is gone after the cut" % tt)
		tt += 0.05
	_drop(st)
	return true


## close figures come from the cast's dialogue busts at their native 112 px (crisp, the faces the player knows),
## never from scaled renders: Irina at her window (p3) and at the teleprinter (k3), Alexei at the window (k3),
## Ekdahl at his compartment window (x1), Lev on the platform (x2)
func _busts() -> bool:
	var L := _layout()
	var D: Dictionary = L.get("depot", {})
	kit.eq(int(D.get("p3_irina_cell", 0)), 112, "p3: Irina's bust cells are 112 px")
	var cases := [["depot/p3_irina.png", 112, 2], ["clock/k3_irina.png", 112, 10], ["clock/k3_alexei.png", 112, 8],
		["express/x2_lev.png", 160, 14], ["express/x1_ekdahl.png", 168, 4]]
	for c in cases:
		var tx: Texture2D = load("res://assets/cinematics/c4p2/" + str(c[0]))
		kit.ok(tx != null, "%s exists" % c[0])
		if tx:
			kit.eq(tx.get_width(), int(c[1]) * int(c[2]), "%s: %d frames of %d px" % [c[0], c[2], c[1]])
	# p3: no window bar crosses Irina's face (the transom is above her head, the mullion right of her)
	var ia: Array = D.get("p3_irina_at", [226, 112])
	var tr_y := 104
	kit.ok(float(ia[1]) + 6.0 > float(tr_y), "p3: the transom (y %d) is above Irina's head (y %d)" % [tr_y, int(ia[1]) + 6])
	kit.ok(float(ia[0]) + 112.0 <= 400.0, "p3: the mullion (x 400) is right of Irina")
	return true


## Kolonne 4: eleven shovels, but not on one ruled line -- the spacing and the footing vary
func _gang_varied() -> bool:
	var gang: Array = (_layout().get("depot", {}) as Dictionary).get("p1_gang", [])
	kit.eq(gang.size(), 11, "eleven shovels")
	var dxs := {}
	var resid := 0.0
	var n := gang.size()
	if n < 3:
		return true
	var x0 := float(gang[0][0])
	var y0 := float(gang[0][1])
	var k := (float(gang[n - 1][1]) - y0) / maxf(1.0, float(gang[n - 1][0]) - x0)
	for i in n:
		if i > 0:
			dxs[int(gang[i][0]) - int(gang[i - 1][0])] = true
		resid = maxf(resid, absf(float(gang[i][1]) - (y0 + (float(gang[i][0]) - x0) * k)))
	kit.ok(dxs.size() >= 4, "the spacing varies (%d different gaps)" % dxs.size())
	kit.ok(resid >= 3.0, "the footing leaves the straight line (max %.1f px)" % resid)
	var phases := {}
	for g in gang:
		phases[int(g[2])] = true
	kit.ok(phases.size() >= 6, "the shovels are out of step (%d phases)" % phases.size())
	return true


## m4: nobody stands in Konrad's lane in front, so he never walks through a passenger
func _m4_lane() -> bool:
	var S: Dictionary = _layout().get("steam", {})
	var feet := float(S.get("m4_feet", 306))
	var kx: Array = S.get("m4_konrad", [580, 690])
	for p in S.get("m4_people", []):
		var px := float(p[0]) + 16.0
		var py := float(p[1]) + 54.0
		var in_path := px > float(kx[0]) - 24.0 and px < float(kx[1]) + 24.0
		kit.ok(not (in_path and absf(py - feet) < 12.0), "no one on Konrad's line at x %.0f (feet %.0f)" % [px, py])
	return true


## k1: the camera starts on the yard (the car, Ilse's window) and tilts up to Hanna's window; reduced motion cuts
func _k1_tilt() -> bool:
	var c := _make("LS_C4P2_Clock", {}, 0)
	c.play()
	c.seek(0.5)
	var a: float = (c.get("k1") as Node2D).position.y
	c.seek(4.9)
	var b: float = (c.get("k1") as Node2D).position.y
	kit.ok(a < b, "k1 tilts up (offset %.0f -> %.0f)" % [a, b])
	_drop(c)
	var r := _make("LS_C4P2_Clock", {}, 1)
	r.play()
	var seen := {}
	var tt := 0.0
	while tt < 5.0:
		r.seek(tt)
		seen[(r.get("k1") as Node2D).position.y] = true
		tt += 0.05
	kit.eq(seen.size(), 2, "reduced motion: the camera holds, then cuts (no travel)")
	_drop(r)
	return true


## x2: protect_first puts a big white bundle of carbons in Lev's hands, publish_now shows his empty hands
func _lev_gesture() -> bool:
	var tx: Texture2D = load("res://assets/cinematics/c4p2/express/x2_lev.png")
	if not kit.ok(tx != null, "x2_lev.png"):
		return true
	var img := tx.get_image()
	var cw := img.get_width() / 14
	var paper := []
	for f in [3, 8]:
		var nb := 0
		for y in img.get_height():
			for x in range(f * cw, (f + 1) * cw):
				var c := img.get_pixel(x, y)
				if c.a > 0.5 and c.r > 0.8 and c.g > 0.8 and c.b > 0.75:
					nb += 1
		paper.append(nb)
	kit.ok(paper[1] >= 600, "protect_first: the carbons are a big white bundle (%d px)" % paper[1])
	kit.ok(paper[0] < 120, "publish_now: no paper in Lev's hands (%d px)" % paper[0])
	return true
