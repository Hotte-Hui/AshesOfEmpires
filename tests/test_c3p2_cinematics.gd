extends RefCounted
## Chapter-3 part-2 cinematics LS_C3_Radio / LS_C3_Fire / LS_C3_Escape / LS_C3_Halves (C3P2_DESIGN §2.9,
## TECHNICAL_ARCHITECTURE §12.5): every scene is instanced in the tree and driven headless (use_director = false:
## no Game/Audio/subtitle side effects, nothing written anywhere).  finished fires exactly once per run (skip, skip
## twice, before play, natural end, fast-forward, replay), skip() is idempotent and stops the cues, the inner lines
## follow ctx.choices for every combination and are spoken in order, fit the film and exist in German, every
## texture exists and the runtime anchors match the generators' layout.json, every cued sound exists, the picture
## is a pure function of t, the match cut and the choice choreography hold, reduced motion halves the travel.
## Owner: cinematics stream (round 8).

const Kit := preload("res://tests/support/test_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const SCENES := {
	"LS_C3_Radio": "res://scenes/cinematics/ch3_radio/Ch3Radio.tscn",
	"LS_C3_Fire": "res://scenes/cinematics/ch3_fire/Ch3Fire.tscn",
	"LS_C3_Escape": "res://scenes/cinematics/ch3_escape/Ch3Escape.tscn",
	"LS_C3_Halves": "res://scenes/cinematics/ch3_halves/Ch3Halves.tscn",
}
## planned lengths (C3P2_DESIGN §2.9: ≈ 29 / 12 / 16 / 21 s; the radio carries six subtitles -> 30.8 s)
const DUR := {"LS_C3_Radio": [29.0, 32.0], "LS_C3_Fire": [11.5, 12.5], "LS_C3_Escape": [15.5, 16.5],
	"LS_C3_Halves": [20.5, 21.5]}
const SHOTS := {"LS_C3_Radio": ["r1", "r2", "r3", "r4", "r5", "r6"], "LS_C3_Fire": ["f1", "f2", "f3", "f4"],
	"LS_C3_Escape": ["e1", "e2", "e3", "e4"], "LS_C3_Halves": ["h1", "h2", "h3", "h4"]}
const C3A := ["", "ask_elena", "note_alone"]
const C3B := ["", "share_protocol", "search_elena", "report_delegation"]
const C3D := ["", "admit_plan", "pocket_plan"]
const C3G := ["", "split_by_language", "swap_halves", "hide_for_elena"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("registered_in_chapter_data", _registered)
	kit.run_case("contract_api_and_planned_length", _api)
	kit.run_case("skip_then_skip_finishes_once", _skip_twice)
	kit.run_case("skip_before_play_finishes_once", _skip_before_play)
	kit.run_case("natural_end_and_fast_forward_finish_once", _natural_end)
	kit.run_case("replay_finishes_once_per_run", _replay)
	kit.run_case("radio_lines_for_every_choice", _radio_lines)
	kit.run_case("halves_lines_for_every_choice", _halves_lines)
	kit.run_case("variants_spoken_in_order_fit_and_localised", _spoken)
	kit.run_case("skip_mid_run_stops_cues", _skip_stops_cues)
	kit.run_case("reduced_motion_and_full_motion_run", _reduced)
	kit.run_case("shot_sequence", _shots)
	kit.run_case("textures_present_and_layout_in_sync", _assets)
	kit.run_case("every_cue_sound_exists", _sounds)
	kit.run_case("sound_timings_match_the_pictures", _sync)
	kit.run_case("frames_are_a_pure_function_of_t", _pure)
	kit.run_case("radio_match_cut_on_the_dial", _match_cut)
	kit.run_case("halves_choreography_follows_the_choice", _choreography)
	kit.run_case("reduced_motion_halves_travel", _rm_travel)
	kit.run_case("fire_light_never_strobes", _no_strobe)
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
	if id == "LS_C3_Radio":
		for a in C3A:
			for b in C3B:
				out.append({"c3a_choose": a, "c3b_choose": b})
	elif id == "LS_C3_Halves":
		for d in C3D:
			for g in C3G:
				out.append({"c3d_choose": d, "c3g_choose": g})
	return out


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
		var d := float(s.get_duration())
		kit.ok(d >= DUR[id][0] and d <= DUR[id][1], "%s duration %.1f s within %s" % [id, d, str(DUR[id])])
		kit.ok(float(s.get("max_duration")) > d, "%s max_duration > duration" % id)
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


func _radio_lines() -> bool:
	var s := _make("LS_C3_Radio")
	var alexei := {"": "base", "ask_elena": "cafe", "note_alone": "alone"}
	var konrad := {"": "base", "share_protocol": "share", "search_elena": "search", "report_delegation": "report"}
	for a in C3A:
		for b in C3B:
			s.configure({"choices": {"c3a_choose": a, "c3b_choose": b}, "flags": {}})
			var L: Array = s.chosen_lines()
			var ka := "cin.c3p2.radio.alexei." + str(alexei[a])
			var kk := "cin.c3p2.radio.konrad." + str(konrad[b])
			kit.eq(L.size(), 6, "radio %s/%s: six lines" % [a, b])
			kit.ok(L.has(ka) and L.has(kk), "radio %s/%s: %s and %s chosen" % [a, b, ka, kk])
			for key in ["cin.c3p2.radio.time", "cin.c3p2.radio.ru", "cin.c3p2.radio.de", "cin.c3p2.radio.note"]:
				kit.ok(L.has(key), "radio %s/%s: %s" % [a, b, key])
			kit.ok(L.find("cin.c3p2.radio.ru") < L.find("cin.c3p2.radio.de"), "russian news before the german")
			# lines about the note or Elena come after the note; the base lines react to the broadcasts
			var note_i := L.find("cin.c3p2.radio.note")
			if a != "":
				kit.ok(L.find(ka) > note_i, "radio %s: Alexei's line follows the note" % a)
			else:
				kit.ok(L.find(ka) < L.find("cin.c3p2.radio.de"), "radio base: Alexei's line follows the Russian news")
			if b in ["share_protocol", "search_elena"]:
				kit.ok(L.find(kk) > note_i, "radio %s: Konrad's line follows the note" % b)
			else:
				kit.ok(L.find(kk) < note_i, "radio %s: Konrad's line follows the German news" % b)
	s.configure({})
	kit.eq(s.chosen_lines()[2], "cin.c3p2.radio.alexei.base", "empty ctx -> base lines")
	_drop(s)
	return true


func _halves_lines() -> bool:
	var s := _make("LS_C3_Halves")
	var g_key := {"": "split", "split_by_language": "split", "swap_halves": "swap", "hide_for_elena": "elena"}
	for d in C3D:
		for g in C3G:
			s.configure({"choices": {"c3d_choose": d, "c3g_choose": g}})
			var want := ["cin.c3p2.halves." + str(g_key[g]),
				"cin.c3p2.halves." + ("plan_kept" if d == "pocket_plan" else "plan_burnt"), "cin.c3p2.halves.tuesday"]
			kit.eq(s.chosen_lines(), want, "halves lines for c3d=%s c3g=%s" % [d, g])
	var f := _make("LS_C3_Fire")
	kit.eq(f.chosen_lines(), ["cin.c3p2.fire.time"], "fire line")
	var e := _make("LS_C3_Escape")
	kit.eq(e.chosen_lines(), [], "escape has no lines")
	_drop(s)
	_drop(f)
	_drop(e)
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
				kit.ok(float(chars) / float(c["dur"]) <= 22.5, "%s: %s readable (%d chars in %.1f s)" % [id, c["say"], chars, c["dur"]])
			for key in s.chosen_lines():
				kit.ok(Loc.has(str(key)), "%s: locale has %s" % [id, key])
				kit.ok(Loc.t(str(key)) != str(key) and Loc.t(str(key)).length() > 5, "%s: %s has German text" % [id, key])
			_drop(s)
	return true


func _skip_stops_cues() -> bool:
	for id in SCENES:
		var s := _make(id)
		s.play()
		s.advance(0.2)
		var before: int = (s.get("said") as Array).size()
		s.skip()
		s.advance(40.0)
		kit.eq((s.get("said") as Array).size(), before, "%s: no lines after skip" % id)
		_drop(s)
	return true


func _reduced() -> bool:
	for rm in [1, 0]:
		for id in SCENES:
			var s: Node = load(SCENES[id]).instantiate()
			s.set("use_director", false)
			s.set("reduced_motion_override", rm)
			(Engine.get_main_loop() as SceneTree).root.add_child(s)
			kit.track(s)
			var n := _counter(s)
			s.play()
			_run_to_end(s, 0.04)
			kit.eq(n[0], 1, "%s reduced_motion=%d: finished once" % [id, rm])
			kit.ok(s.reduced_motion() == (rm == 1), "%s reduced_motion override %d" % [id, rm])
			_drop(s)
	return true


func _shots() -> bool:
	for id in SCENES:
		var s := _make(id)
		s.play()
		var seen: Array = []
		var tt := 0.0
		while tt <= s.get_duration():
			s.seek(tt)
			var sh := str(s.get_shot_id())
			if seen.is_empty() or seen[-1] != sh:
				seen.append(sh)
			tt += 0.1
		kit.eq(seen, SHOTS[id], "%s shot order" % id)
		_drop(s)
	return true


func _layout() -> Dictionary:
	var p := "res://assets/cinematics/c3p2/layout.json"
	if not FileAccess.file_exists(p):
		return {}
	var L = JSON.parse_string(FileAccess.get_file_as_string(p))
	return L if L is Dictionary else {}


func _assets() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id).slice(0, 2):
			var s := _make(id, ch)
			kit.eq(s.get("missing"), [], "%s: every texture exists" % id)
			_drop(s)
	var L := _layout()
	if not kit.ok(not L.is_empty(), "layout.json written by tools/pixelgen/env_c3p2_cine.py"):
		return true
	var R: Dictionary = L.get("radio", {})
	var rg = load("res://scenes/cinematics/ch3_radio/ch3_radio.gd")
	kit.eq(R.get("dial"), [float(rg.DIAL.x), float(rg.DIAL.y)], "radio dial: runtime == generator (the match cut)")
	kit.eq(float(R.get("dial_r", 0)), float(rg.DIAL_R), "radio dial radius: runtime == generator")
	for k in ["radio", "fig_alexei", "fig_konrad", "arm_alexei", "hand_konrad", "win_konrad", "win_alexei",
			"door_konrad", "door_alexei", "path_konrad", "path_alexei", "prints_konrad", "prints_alexei", "clock",
			"door_floor", "door_cx", "pad_line", "steam_tea", "magic_eye", "cafe_win"]:
		kit.ok(R.has(k), "layout radio.%s" % k)
	kit.ok((R.get("path_konrad", []) as Array).size() >= 40, "walker path long enough for r6")
	var F: Dictionary = L.get("fire", {})
	for k in ["f1_konrad", "f2_door_at", "f2_fire", "f3_gap", "f3_floor", "f4_alexei", "f4_fire"]:
		kit.ok(F.has(k), "layout fire.%s" % k)
	var E: Dictionary = L.get("escape", {})
	for k in ["e1_hatch", "hatch", "hatch_at", "e2_konrad", "e3_hands", "e3b_hatch", "e3b_men", "e3b_breath", "e4_windows"]:
		kit.ok(E.has(k), "layout escape.%s" % k)
	var eg = load("res://scenes/cinematics/ch3_escape/ch3_escape.gd")
	kit.ok((E.get("e4_windows", []) as Array).size() >= (eg.BURST_ORDER as Array).size(), "a window for every burst")
	var H: Dictionary = L.get("halves", {})
	for k in ["bench", "stack_ru", "stack_de", "arms_at", "fig_alexei", "fig_konrad", "prom_y", "h3_towers", "h3_fire",
			"charset", "cell", "rows_y", "row_x", "fresh_row", "fresh"]:
		kit.ok(H.has(k), "layout halves.%s" % k)
	kit.eq(str(H.get("fresh", "")), "DIENSTAG · 23.40 · KORDON-17 · GLEIS 5", "the fresh row on the board")
	var cs := str(H.get("charset", ""))
	for ch in str(H.get("fresh", "")):
		kit.ok(cs.contains(ch), "glyph atlas has %s" % ch)
	return true


## every sound named by a cue resolves to a file (variants id_1.. count, like Audio.sfx does)
func _sounds() -> bool:
	for id in SCENES:
		for ch in _choice_sets(id).slice(0, 3):
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
				for key in ["loop", "bed"]:
					if d.has(key):
						kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % str(d[key])), "%s: %s %s" % [id, key, d[key]])
				if d.has("loop"):
					var stopped := false
					for c2 in s.get("_cues"):
						if (c2 as Dictionary).get("loop_stop", "") == str(d.get("key", d["loop"])):
							stopped = true
					kit.ok(stopped, "%s: loop %s is stopped by a later cue" % [id, d["loop"]])
			_drop(s)
	return true


## the lamp's flicker crackles, the chute's shoves and the window bursts are cut into the beds at the
## same times the picture uses (tools/audiogen/c3p2_cine_audio.py)
func _sync() -> bool:
	var src := FileAccess.get_file_as_string("res://tools/audiogen/c3p2_cine_audio.py")
	if not kit.ok(src != "", "tools/audiogen/c3p2_cine_audio.py readable"):
		return true
	var rx := RegEx.new()
	rx.compile("(LAMP_DIPS|CHUTE_PUSHES|BURST_GAP) = \\(?([0-9., ]+)\\)?")
	var found := {}
	for m in rx.search_all(src):
		var vals: Array = []
		for v in m.get_string(2).split(",", false):
			if v.strip_edges() != "":
				vals.append(float(v))
		found[m.get_string(1)] = vals
	var fire = load("res://scenes/cinematics/ch3_fire/ch3_fire.gd")
	var esc = load("res://scenes/cinematics/ch3_escape/ch3_escape.gd")
	kit.eq(found.get("LAMP_DIPS", []), fire.LAMP_DIPS, "lamp flicker: picture == c3p2cine_lamp")
	kit.eq(found.get("CHUTE_PUSHES", []), esc.PUSHES, "chute shoves: picture == c3p2cine_chute")
	kit.eq(found.get("BURST_GAP", []), [esc.BURST_GAP], "window bursts: picture == c3p2cine_burst")
	return true


func _snapshot(s: Node) -> Array:
	var out: Array = []
	for c in s.get_children():
		if c is CanvasItem:
			out.append([c.name, (c as CanvasItem).visible])
			for g in c.get_children():
				if g is Sprite2D:
					out.append([g.name, (g as Sprite2D).visible, (g as Sprite2D).frame, (g as Sprite2D).position,
						(g as Sprite2D).modulate])
	return out


func _pure() -> bool:
	for id in SCENES:
		var s := _make(id, {"c3g_choose": "swap_halves", "c3a_choose": "ask_elena"})
		s.play()
		for tt in [1.0, 5.3, 9.95, 14.2]:
			if tt > s.get_duration():
				continue
			s.seek(tt)
			var a := _snapshot(s)
			s.seek(s.get_duration() * 0.9)
			s.seek(tt)
			kit.eq(_snapshot(s), a, "%s: the frame at %.2f s is the same after seeking away and back" % [id, tt])
		_drop(s)
	return true


func _match_cut() -> bool:
	var s := _make("LS_C3_Radio")
	s.play()
	var rg = load("res://scenes/cinematics/ch3_radio/ch3_radio.gd")
	var tune: Array = rg.TUNE
	kit.ok(float(tune[0]) < 10.5 and float(tune[1]) > 10.5, "the needle sweep spans the cut r2 -> r3")
	var a0: float = s.needle_angle(10.45)
	var a1: float = s.needle_angle(10.55)
	kit.ok(a1 > a0 and a1 - a0 < 20.0, "the needle continues across the cut (%.1f -> %.1f)" % [a0, a1])
	kit.eq(s.needle_angle(4.0), float(rg.ANG_RU), "Alexei's set on the Russian service")
	kit.eq(s.needle_angle(12.0), float(rg.ANG_DE), "Konrad's set on the German service")
	kit.eq(s.get("_radio_a").position, s.get("_radio_k").position, "the same radio model at the same place in both rooms")
	s.seek(10.4)
	kit.ok(s.get("room_a").visible and not s.get("room_k").visible, "10.4 s: Alexei's room")
	s.seek(10.6)
	kit.ok(s.get("room_k").visible and not s.get("room_a").visible, "10.6 s: Konrad's room")
	_drop(s)
	return true


func _choreography() -> bool:
	var takes := {
		"split_by_language": {"ru": "a", "de": "k"},
		"swap_halves": {"ru": "k", "de": "a"},
		"hide_for_elena": {"ru": "a", "de": "k", "list": "k"},
		"": {"ru": "a", "de": "k"},
	}
	for g in takes:
		var s := _make("LS_C3_Halves", {"c3g_choose": g})
		var got := {}
		for m in s.get("moves"):
			got[str(m["stack"])] = str(m["who"])
			kit.ok(float(m["reach"]) < float(m["take"]) and float(m["take"]) < float(m["hold_end"]) and
				float(m["hold_end"]) < 6.0, "c3g=%s: %s taken inside h1" % [g, m["stack"]])
		kit.eq(got, takes[g], "c3g=%s: who takes which pages" % g)
		if g == "hide_for_elena":
			var lm: Dictionary = {}
			for m in s.get("moves"):
				if m["stack"] == "list":
					lm = m
			for m in s.get("moves"):
				if m["stack"] != "list":
					kit.ok(float(m["reach"]) > float(lm["take"]), "hide_for_elena: the list goes into the coat first")
		# the arms are visible while reaching/holding, hidden otherwise
		s.play()
		s.seek(0.2)
		kit.ok(not s.get("_arm_a").visible and not s.get("_arm_k").visible, "c3g=%s: hands still at 0.2 s" % g)
		_drop(s)
	return true


func _rm_travel() -> bool:
	var xs := {}
	for rm in [0, 1]:
		var s := _make("LS_C3_Halves", {}, rm)
		s.play()
		s.seek(6.0)
		var a0: float = s.get("_walk_a").position.x
		s.seek(10.9)
		xs[rm] = s.get("_walk_a").position.x - a0
		_drop(s)
	kit.ok(xs[0] > 80.0, "full motion: Alexei walks off to the east (%.0f px)" % xs[0])
	kit.ok(absf(xs[1] - xs[0] * 0.5) <= 2.0, "reduced motion: half the travel (%.0f of %.0f px)" % [xs[1], xs[0]])
	return true


## fire light changes slowly: between two 60 Hz frames the glow never jumps by more than a few percent
func _no_strobe() -> bool:
	for rm in [0, 1]:
		var s := _make("LS_C3_Fire", {}, rm)
		s.play()
		var prev := -1.0
		var worst := 0.0
		var tt := 8.6
		while tt < 12.0:
			s.seek(tt)
			var a: float = s.get("_f4glow").modulate.a
			if prev >= 0.0:
				worst = maxf(worst, absf(a - prev))
			prev = a
			tt += 1.0 / 60.0
		kit.ok(worst < 0.06, "fire glow (rm=%d): largest frame-to-frame change %.3f" % [rm, worst])
		_drop(s)
	# the lamp's dips and the window bursts never come faster than 3 per second
	var fire = load("res://scenes/cinematics/ch3_fire/ch3_fire.gd")
	var dips: Array = fire.LAMP_DIPS
	for i in range(1, dips.size()):
		kit.ok(float(dips[i]) - float(dips[i - 1]) >= 1.0 / 3.0, "lamp dips %.2f -> %.2f at most 3 Hz" % [dips[i - 1], dips[i]])
	var esc = load("res://scenes/cinematics/ch3_escape/ch3_escape.gd")
	kit.ok(float(esc.BURST_GAP) >= 1.0 / 3.0, "window bursts at most 3 Hz")
	return true
