extends RefCounted
## Chapter-4 cinematics LS_C4_Homeward / _Number / _Card / _Stamp / _Voices (C4_DESIGN §2.9, TECHNICAL_ARCHITECTURE
## §12.5): every scene is instanced in the tree and driven headless (use_director = false: no Game/Audio/subtitle
## side effects, nothing written anywhere).  finished fires exactly once per run (skip, skip twice, before play,
## natural end, fast-forward, replay); skip() is idempotent and stops the cues; each film lasts exactly the sum of
## its registered shots (data/v3/cinematics.json) in the registered order; the inner lines follow ctx.choices (c3g
## for Homeward, c4d for Voices) with defaults for contexts that lack them, are spoken in order, readable and German;
## every texture and cued sound exists, the runtime anchors match the generators' layout.json and the sound tool's
## times; the picture is a pure function of t; the three match cuts hold (the same 45 at the same place, the same
## perforation mirrored, the same stamp frame at the same point); the c4d choreography (file, bells, the raised
## hand) follows the choice; reduced motion halves the camera travel and the lamp never strobes.
## Owner: cine stream (round 9).

const Kit := preload("res://tests/support/test_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const SCENES := {
	"LS_C4_Homeward": "res://scenes/cinematics/ch4_homeward/Ch4Homeward.tscn",
	"LS_C4_Number": "res://scenes/cinematics/ch4_number/Ch4Number.tscn",
	"LS_C4_Card": "res://scenes/cinematics/ch4_card/Ch4Card.tscn",
	"LS_C4_Stamp": "res://scenes/cinematics/ch4_stamp/Ch4Stamp.tscn",
	"LS_C4_Voices": "res://scenes/cinematics/ch4_voices/Ch4Voices.tscn",
}
const C3G := ["", "split_by_language", "swap_halves", "hide_for_elena"]
const C4D := ["", "name_marta", "protect_marta"]

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
	kit.run_case("homeward_line_for_every_c3g", _homeward_lines)
	kit.run_case("voices_lines_for_every_c4d", _voices_lines)
	kit.run_case("lines_spoken_in_order_fit_readable_german", _spoken)
	kit.run_case("skip_mid_run_stops_cues", _skip_stops_cues)
	kit.run_case("reduced_motion_and_full_motion_run", _reduced)
	kit.run_case("textures_present_and_layout_in_sync", _assets)
	kit.run_case("figures_from_the_game_sheets", _figures)
	kit.run_case("every_cue_sound_exists", _sounds)
	kit.run_case("sound_timings_match_the_pictures", _sync)
	kit.run_case("frames_are_a_pure_function_of_t", _pure)
	kit.run_case("match_cut_number_same_45", _cut_number)
	kit.run_case("match_cut_card_mirrored_perforation", _cut_card)
	kit.run_case("match_cut_stamp_same_frame", _cut_stamp)
	kit.run_case("voices_choreography_follows_c4d", _choreography)
	kit.run_case("reduced_motion_halves_travel", _rm_travel)
	kit.run_case("lamp_never_strobes", _no_strobe)
	kit.run_case("memory_film_titles", _film_titles)
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
	if id == "LS_C4_Homeward":
		for g in C3G:
			out.append({"c3g_choose": g})
	elif id == "LS_C4_Voices":
		for d in C4D:
			out.append({"c4d_choose": d, "c3g_choose": "swap_halves"})
	return out


## data/v3/cinematics.json entry of a film: {id, shots: [{id, duration_s}]}
func _seq(id: String) -> Dictionary:
	if _data.is_empty():
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/cinematics.json"))
		_data = d if d is Dictionary else {}
	for s in _data.get("sequences", []):
		if str(s.get("id", "")) == id:
			return s
	return {}


func _layout() -> Dictionary:
	var p := "res://assets/cinematics/c4/layout.json"
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


## the shot ids and boundaries are those of the registered shot sheet
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


func _homeward_lines() -> bool:
	var s := _make("LS_C4_Homeward")
	var want := {"": "split", "split_by_language": "split", "swap_halves": "swap", "hide_for_elena": "elena"}
	for g in C3G:
		s.configure({"choices": {"c3g_choose": g}})
		kit.eq(s.chosen_lines(), ["cin.c4.homeward.alexei." + str(want[g]), "cin.c4.homeward.place"],
			"homeward lines for c3g=%s" % g)
	s.configure({})
	kit.eq(s.chosen_lines()[0], "cin.c4.homeward.alexei.split", "a context without c3g -> the split line")
	for id in ["LS_C4_Number", "LS_C4_Card", "LS_C4_Stamp"]:
		var f := _make(id)
		kit.ok((f.chosen_lines() as Array).size() >= 2, "%s has its lines" % id)
		_drop(f)
	_drop(s)
	return true


func _voices_lines() -> bool:
	var s := _make("LS_C4_Voices")
	for d in C4D:
		s.configure({"choices": {"c4d_choose": d}})
		var k := "cin.c4.voices.konrad_name" if d == "name_marta" else "cin.c4.voices.konrad_protect"
		kit.eq(s.chosen_lines(), [k, "cin.c4.voices.alexei", "cin.c4.voices.tuesday"], "voices lines for c4d=%s" % d)
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
				kit.ok(float(chars) / float(c["dur"]) <= 22.0, "%s: %s readable (%d chars in %.2f s)" %
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
		for ch in _choice_sets(id).slice(0, 3):
			var s := _make(id, ch)
			kit.eq(s.get("missing"), [], "%s: every texture exists" % id)
			_drop(s)
	var L := _layout()
	if not kit.ok(not L.is_empty(), "layout.json written by tools/pixelgen/env_c4_cine.py"):
		return true
	var need := {
		"places": ["feet", "yard_signal", "yard_window", "yard_stair", "loop_w", "loop_door", "loop_column",
			"loop_shelter", "tram_size", "siding_lamp", "siding_wagon"],
		"homeward": ["vp", "door_k", "door_a", "w1_steam", "w1_konrad", "w1_alexei", "win_k", "win_a", "strip_w",
			"w3_alexei", "w3_walk"],
		"number": ["n1_w", "n1_stencil", "n1_tin", "n1_drip", "macro", "macro_drip", "n3_hatch", "n3_stack",
			"n3_tail", "n3_exhaust", "n3_chain", "n4_konrad"],
		"card": ["card_size", "card_at", "c1_lhand_at", "c1_rhand_tip", "edge_x", "macro_k", "macro_y0",
			"macro_holes", "ru_at", "c3_lamp", "c3_hand_at", "c4_win", "c4_alexei_at"],
		"stamp": ["box", "box_slot", "note_lines", "note_spans", "lev_tip", "pencil_tip", "stamp_c", "stamp_frame",
			"imp_size", "stamp_size", "hand_knob", "lever_pivot", "s3_perf", "s3_split", "s3b_hands_at", "s4_ladder",
			"s4_konrad_x", "s4_konrad"],
		"voices": ["v1_konrad", "v1_off", "v1_walk", "v2_konrad_at", "v2_off", "v3_alexei", "v3_lev", "numbers"],
	}
	for sec in need:
		var S: Dictionary = L.get(sec, {})
		for k in need[sec]:
			kit.ok(S.has(k), "layout %s.%s" % [sec, k])
	kit.eq(L.get("voices", {}).get("numbers", []), ["24 318", "C-17/42", "47 702", "C-17/45"],
		"the notebook carries the puzzle's four numbers (C4_DESIGN §2.7)")
	return true


## the wide shots use the game's own sheets (32 x 56 cells, re-lit): a stand-in is reported, never silent
func _figures() -> bool:
	var L := _layout()
	var stand: Dictionary = L.get("standins", {})
	for cid in stand:
		print("      pending (round 9): %s drawn from stand-in %s until its sheet exists; rerun env_c4_cine.py" %
			[cid, stand[cid]])
	for rel in ["homeward/w1_konrad.png", "homeward/w1_alexei.png", "homeward/w3_alexei.png", "number/n4_konrad.png",
			"stamp/s4_konrad.png", "voices/v1_konrad.png", "voices/v3_alexei.png", "voices/v3_lev.png"]:
		var p: String = "res://assets/cinematics/c4/" + str(rel)
		var ok := ResourceLoader.exists(p)
		kit.ok(ok, "figure sheet %s" % rel)
		if ok:
			var t: Texture2D = load(p)
			kit.eq(t.get_height(), 56, "%s: one row of 56 px cells" % rel)
			kit.eq(t.get_width() % 32, 0, "%s: 32 px wide cells" % rel)
	return true


## every sound named by a cue resolves to a file (variants id_1.. count, like Audio.sfx does)
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


## the door slams, the tram bell, the perforation ticks, the stamps, the perforator and the lamp's flicker are cut
## into the beds at the times the pictures use (tools/audiogen/c4_cine_audio.py)
func _sync() -> bool:
	var src := FileAccess.get_file_as_string("res://tools/audiogen/c4_cine_audio.py")
	if not kit.ok(src != "", "tools/audiogen/c4_cine_audio.py readable"):
		return true
	var rx := RegEx.new()
	rx.compile("(?m)^(DOOR_SLAMS|TRAM_BELL|PERF_TICKS|STAMP_HIT|LEVER_CLACK|LAMP_FLICKS) = \\(?([0-9., ]+)\\)?")
	var found := {}
	for m in rx.search_all(src):
		var vals: Array = []
		for v in m.get_string(2).split(",", false):
			if v.strip_edges() != "":
				vals.append(float(v))
		found[m.get_string(1)] = vals
	var hw = load("res://scenes/cinematics/ch4_homeward/ch4_homeward.gd")
	var nu = load("res://scenes/cinematics/ch4_number/ch4_number.gd")
	var ca = load("res://scenes/cinematics/ch4_card/ch4_card.gd")
	var st = load("res://scenes/cinematics/ch4_stamp/ch4_stamp.gd")
	var vo = load("res://scenes/cinematics/ch4_voices/ch4_voices.gd")
	kit.eq(found.get("DOOR_SLAMS", []), hw.DOOR_SLAMS, "carriage doors: picture == c4cine_station")
	kit.eq(found.get("TRAM_BELL", []), [nu.TRAM_BELL], "tram bell: picture == c4cine_tram")
	kit.eq(found.get("PERF_TICKS", []), ca.PERF_TICKS, "perforation ticks: picture == c4cine_perf")
	kit.eq(found.get("STAMP_HIT", []), [st.STAMP_RU[1], st.STAMP_DE[1]], "stamps: picture == c4cine_stamp_ru/_de")
	kit.eq(found.get("LEVER_CLACK", []), [st.LEVER[1]], "perforator: picture == c4cine_annex")
	kit.eq(found.get("LAMP_FLICKS", []), vo.LAMP_FLICKS, "work lamp: picture == c4cine_lamp_out")
	# the stamp beds start where the shots start, so the thump lands on the contact frame
	var s := _make("LS_C4_Stamp")
	var starts := {}
	for c in s.get("_cues"):
		if (c as Dictionary).has("bed"):
			starts[str(c["bed"])] = float(c["t"])
	kit.eq(starts.get("c4cine_stamp_ru", -1.0), 3.5, "c4cine_stamp_ru starts with s2")
	kit.eq(starts.get("c4cine_stamp_de", -1.0), 5.0, "c4cine_stamp_de starts with s3")
	kit.eq(starts.get("c4cine_annex", -1.0), 6.6, "c4cine_annex starts with the counter")
	_drop(s)
	return true


func _pure() -> bool:
	for id in SCENES:
		var s := _make(id, {"c3g_choose": "swap_halves", "c4d_choose": "protect_marta"})
		s.play()
		for tt in [0.6, 2.1, 4.4, 5.6, 7.3, 9.95, 12.2, 17.0, 18.3, 21.0]:
			if tt > s.get_duration():
				continue
			s.seek(tt)
			var a := _snapshot(s)
			s.seek(s.get_duration() * 0.9)
			s.seek(tt)
			kit.eq(_snapshot(s), a, "%s: the frame at %.2f s is the same after seeking away and back" % [id, tt])
		_drop(s)
	return true


## n2 -> n3: the 45 of the wagon and the 45 of the crate are the same shapes at the same place (one layout entry
## drives both macro plates) and the cut is hard: one frame the wagon, the next the crate
func _cut_number() -> bool:
	var L := _layout()
	var N: Dictionary = L.get("number", {})
	kit.eq((N.get("macro", []) as Array).size(), 3, "number.macro = [x, y, cap height] shared by n2 and n3a")
	var s := _make("LS_C4_Number")
	s.play()
	s.seek(5.49)
	var m2: Node2D = s.get("n2")
	var m3: Node2D = s.get("n3a")
	kit.ok(m2.visible and not m3.visible, "at 5.49 s the wagon's 45")
	s.seek(5.5)
	kit.ok(m3.visible and not m2.visible, "at 5.50 s the crate's 45 (hard cut)")
	# the drip keeps running across n1/n2 and the pan reaches the stencil
	var n1x: float = s.pan_x(0.0)
	var n1e: float = s.pan_x(4.0)
	kit.ok(n1e < n1x, "n1 pans along the planks")
	var st: Array = N.get("n1_stencil", [640, 136, 50])
	kit.ok(float(st[0]) + n1e > 40.0 and float(st[0]) + n1e < 400.0, "the stencil is in view at the end of the pan")
	_drop(s)
	return true


## c2 -> c3: the perforation is cut on the same vertical at the same hole rows; the German half's paper lies left
## of the edge, the Russian half's right of it (mirrored); the shadow runs at the same speed across the cut
func _cut_card() -> bool:
	var L := _layout()
	var Cd: Dictionary = L.get("card", {})
	kit.ok(Cd.has("edge_x") and (Cd.get("macro_holes", []) as Array).size() >= 8, "card macro: edge and hole rows")
	for pair in [["card/c2_macro.png", -6], ["card/c3a_macro.png", 6]]:
		var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/cinematics/c4/" + str(pair[0])))
		if not kit.ok(img != null, "%s loads" % pair[0]):
			continue
		var ex := int(Cd.get("edge_x", 330))
		var holes: Array = Cd.get("macro_holes", [])
		var y := int(float(holes[3]) + 12.0)              # between two holes: paper reaches the edge
		var paper_side := img.get_pixel(ex + int(pair[1]), y).get_luminance()
		var other_side := img.get_pixel(ex - int(pair[1]), y).get_luminance()
		kit.ok(paper_side > other_side, "%s: paper on the %s of the edge" % [pair[0], "left" if int(pair[1]) < 0 else "right"])
	var s := _make("LS_C4_Card")
	s.play()
	var a: float = s.shadow_y(3.5 + 0.6, 3.5, 5.0)
	var b: float = s.shadow_y(5.0 + 0.6, 5.0, 6.5)
	kit.ok(absf(a - b) <= 1.0, "the shadow moves at the same place/speed on both sides of the cut")
	s.seek(4.99)
	kit.ok((s.get("c2") as Node2D).visible, "at 4.99 s the German half")
	s.seek(5.0)
	kit.ok((s.get("c3a") as Node2D).visible and not (s.get("c2") as Node2D).visible, "at 5.00 s the Russian half")
	_drop(s)
	return true


## s2 -> s3: both stamps press at the same point inside the same frame; each impression appears on contact
func _cut_stamp() -> bool:
	var s := _make("LS_C4_Stamp")
	s.play()
	var c4 = load("res://scenes/cinematics/ch4_stamp/ch4_stamp.gd")
	s.seek(float(c4.STAMP_RU[1]) + 0.05)
	var ru: Sprite2D = s.get("_imp_ru")
	var ru_pos := ru.position
	kit.ok(ru.visible, "ПРИНЯТЬ shows from the contact on")
	kit.eq(float(s.stamp_off(float(c4.STAMP_RU[1]) + 0.05, c4.STAMP_RU)), 0.0, "the Karsk stamp is down")
	s.seek(float(c4.STAMP_DE[1]) + 0.05)
	var de: Sprite2D = s.get("_imp_de")
	kit.ok(de.visible, "ABGANG shows from the contact on")
	kit.eq(de.position, ru_pos, "both impressions at the same place (the match cut)")
	kit.eq(ru.texture.get_size(), de.texture.get_size(), "both impressions in the same frame size")
	s.seek(float(c4.STAMP_DE[0]) - 0.05)
	kit.ok(not de.visible, "no ABGANG before the stamp comes down")
	_drop(s)
	return true


func _choreography() -> bool:
	for d in ["name_marta", "protect_marta", ""]:
		var s := _make("LS_C4_Voices", {"c4d_choose": d})
		s.play()
		var named: bool = str(d) == "name_marta"
		s.seek(2.5)
		kit.eq((s.get("_file") as Sprite2D).visible, named, "v1 c4d=%s: the file under the coat %s" % [d, "shown" if named else "absent"])
		s.seek(8.0)
		var k2: Sprite2D = s.get("_k2")
		kit.eq(k2.frame, 0 if named else 2, "v2 c4d=%s: Konrad's hand %s" % [d, "down" if named else "raised"])
		kit.eq((s.get("_tram") as Sprite2D).frame, 0 if named else 1, "v2 c4d=%s: Ilse's hand on the glass" % d)
		var bells := 0
		for c in s.get("_cues"):
			if str((c as Dictionary).get("sfx", "")) == "c4cine_bell":
				bells += 1
		kit.eq(bells, 1 if named else 2, "v2 c4d=%s: %d bell(s)" % [d, 1 if named else 2])
		s.seek(9.6)
		kit.eq(k2.frame, 0, "v2 c4d=%s: the hand is down again before the cut" % d)
		_drop(s)
	return true


func _rm_travel() -> bool:
	var full := _make("LS_C4_Number", {}, 0)
	var half := _make("LS_C4_Number", {}, 1)
	var tf: float = full.pan_x(4.0) - full.pan_x(0.0)
	var th: float = half.pan_x(4.0) - half.pan_x(0.0)
	kit.ok(absf(th - tf * 0.5) <= 1.0, "n1 pan: reduced motion halves the travel (%.0f vs %.0f)" % [th, tf])
	_drop(full)
	_drop(half)
	var vf := _make("LS_C4_Voices", {}, 0)
	var vh := _make("LS_C4_Voices", {}, 1)
	var a: float = vf.tram_x(9.9) - vf.tram_x(5.3)
	var b: float = vh.tram_x(9.9) - vh.tram_x(5.3)
	kit.ok(absf(b - a * 0.5) <= 1.0, "v2 tram: reduced motion halves the travel (%.0f vs %.0f)" % [b, a])
	_drop(vf)
	_drop(vh)
	var cf := _make("LS_C4_Card", {}, 0)
	var ch := _make("LS_C4_Card", {}, 1)
	kit.ok(absf(float(ch.lift_off(0.15)) - float(cf.lift_off(0.15)) * 0.5) <= 1.0, "c1 lift: reduced motion halves it")
	_drop(cf)
	_drop(ch)
	return true


## the work lamp changes at most 3 times in any second; with reduced motion it goes out once
func _no_strobe() -> bool:
	for rm in [0, 1]:
		var s := _make("LS_C4_Voices", {}, rm)
		var changes: Array = []
		var prev: bool = s.lamp_on(15.0)
		var tt := 15.0
		while tt <= 20.0:
			var on: bool = s.lamp_on(tt)
			if on != prev:
				changes.append(tt)
			prev = on
			tt += 0.01
		var worst := 0
		for i in changes.size():
			var n := 0
			for j in range(i, changes.size()):
				if float(changes[j]) - float(changes[i]) < 1.0:
					n += 1
			worst = maxi(worst, n)
		kit.ok(worst <= 3, "rm=%d: at most 3 lamp changes per second (%d)" % [rm, worst])
		kit.ok(not s.lamp_on(19.9), "rm=%d: the lamp is out at the end of v4" % rm)
		if rm == 1:
			kit.eq(changes.size(), 1, "reduced motion: the lamp goes out once, no flicker")
		_drop(s)
	return true


func _film_titles() -> bool:
	for id in SCENES:
		kit.ok(Loc.has("ui.memories.film." + id), "memory film title for %s" % id)
		kit.ok(Loc.has("ui.memories.film_sub." + id), "memory film subtitle for %s" % id)
	return true
