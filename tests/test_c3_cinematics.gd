extends RefCounted
## Chapter-3 cinematic scenes (TECHNICAL_ARCHITECTURE §12.5, C3_DESIGN §2.9): every scene is instanced in the
## tree and driven headless.  finished fires exactly once per run (skip; skip twice; natural end; skip after
## the end; replay), the inner lines follow configure(ctx).flags for all flag combinations, the spoken keys
## exist in the locale, reduced motion runs, every texture exists and the runtime layout matches the art
## generator's assets/cinematics/ch3/layout.json; every sound a cue plays exists; the rail-joint beat of the car
## equals the beat cut into the bed sounds (tools/audiogen/c3_cine_audio.py); reduced motion keeps the cars
## still; the dissolves t3 -> t3b -> t4 complete and the t4 crane moves its planes (round 10 rework, 36 s).
## Owner: cinematics stream.

const Kit := preload("res://tests/support/test_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const SCENES := {
	"LS_C3_Trains": "res://scenes/cinematics/ch3_trains/Ch3Trains.tscn",
	"LS_C3_ToHall": "res://scenes/cinematics/ch3_tohall/Ch3ToHall.tscn",
	"LS_C3_Close": "res://scenes/cinematics/ch3_close/Ch3Close.tscn",
}
const DUR := {"LS_C3_Trains": [34.0, 38.0], "LS_C3_ToHall": [5.0, 7.5], "LS_C3_Close": [11.0, 13.5]}
const SHOTS := {"LS_C3_Trains": ["t1", "t2", "t3", "t3b", "t4"], "LS_C3_ToHall": ["k1", "k2"], "LS_C3_Close": ["n1", "n2"]}

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("registered_in_chapter_data", _registered)
	kit.run_case("contract_api_and_properties", _api)
	kit.run_case("skip_then_skip_finishes_once", _skip_twice)
	kit.run_case("skip_before_play_finishes_once", _skip_before_play)
	kit.run_case("natural_end_then_skip_finishes_once", _natural_end)
	kit.run_case("replay_finishes_once_per_run", _replay)
	kit.run_case("trains_lines_for_every_flag_set", _trains_lines)
	kit.run_case("lines_spoken_in_order_and_localised", _spoken)
	kit.run_case("skip_mid_run_stops_cues", _skip_stops_cues)
	kit.run_case("reduced_motion_and_full_motion_run", _reduced)
	kit.run_case("shot_sequence", _shots)
	kit.run_case("assets_present_and_layout_in_sync", _assets)
	kit.run_case("layout_has_everything_the_runtime_reads", _layout_keys)
	kit.run_case("every_cue_sound_exists", _sounds)
	kit.run_case("rail_joints_match_the_bed_sounds", _joints)
	kit.run_case("reduced_motion_keeps_the_cars_still", _still)
	kit.run_case("dawn_dissolve_completes", _dawn)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _make(id: String, flags := {}) -> Node:
	var s: Node = load(SCENES[id]).instantiate()
	s.set("use_director", false)          # no Game/Audio/subtitle side effects in unit tests
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	kit.track(s)
	s.configure({"choices": {}, "flags": flags, "symbols": true})
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


# ------------------------------------------------------------------ cases
func _registered() -> bool:
	var ext = ChapterExt.new()
	for id in SCENES:
		kit.eq(str(ext.cinematics.get(id, "")), SCENES[id], "data/chapters registers %s" % id)
		kit.ok(ext.has_cinematic(id), "%s scene exists" % id)
	kit.ok(ext.grades.has("c3_cine"), "grade c3_cine exists")
	return true


func _api() -> bool:
	for id in SCENES:
		var s := _make(id)
		kit.ok(s is Node2D, "%s root is Node2D" % id)
		for m in ["configure", "play", "skip", "chosen_lines", "seek", "advance"]:
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
		var s := _make(id)
		var n := _counter(s)
		s.play()
		var steps := _run_to_end(s, 0.05)
		kit.ok(s.is_finished(), "%s reaches its natural end (%d steps)" % [id, steps])
		kit.eq(n[0], 1, "%s: natural end -> finished once" % id)
		s.skip()
		s.skip()
		kit.eq(n[0], 1, "%s: skip after the natural end emits nothing" % id)
		_drop(s)
	# a coarse time step (fast-forward) also ends exactly once
	for id in SCENES:
		var s := _make(id)
		var n := _counter(s)
		s.play()
		_run_to_end(s, 1.7)
		kit.eq(n[0], 1, "%s: fast-forward natural end -> finished once" % id)
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


func _trains_lines() -> bool:
	var s := _make("LS_C3_Trains")
	for ke in [0, 1, 2]:
		for os in [0, 1]:
			for it in [0, 1]:
				for sc in [0, 1, 3]:
					var flags := {"konrad_evidence": ke, "office_suspicion": os, "irina_trust": it, "alexei_secrecy": sc}
					s.configure({"flags": flags, "choices": {}, "symbols": true})
					var k := "cin.c3.trains.konrad." + ("evidence" if ke >= 1 else ("suspicion" if os >= 1 else "base"))
					var a := "cin.c3.trains.alexei." + ("irina" if it >= 1 else ("secrecy" if sc >= 1 else "base"))
					kit.eq(s.chosen_lines(), [k, a, "cin.c3.trains.place"], "lines for %s" % str(flags))
	# flags as floats (JSON) and an empty ctx
	s.configure({"flags": {"konrad_evidence": 1.0, "alexei_secrecy": 1.0}})
	kit.eq(s.chosen_lines(), ["cin.c3.trains.konrad.evidence", "cin.c3.trains.alexei.secrecy", "cin.c3.trains.place"],
		"float flags")
	s.configure({})
	kit.eq(s.chosen_lines(), ["cin.c3.trains.konrad.base", "cin.c3.trains.alexei.base", "cin.c3.trains.place"],
		"empty ctx -> base lines")
	_drop(s)
	var th := _make("LS_C3_ToHall")
	kit.eq(th.chosen_lines(), ["cin.c3.tohall.time"], "ToHall line")
	_drop(th)
	var cl := _make("LS_C3_Close")
	kit.eq(cl.chosen_lines(), ["cin.c3.close.train", "cin.c3.close.after"], "Close lines")
	_drop(cl)
	return true


func _spoken() -> bool:
	var sets := [{}, {"konrad_evidence": 1, "irina_trust": 1}, {"office_suspicion": 1, "alexei_secrecy": 1},
		{"konrad_evidence": 1, "office_suspicion": 1, "irina_trust": 1, "alexei_secrecy": 1}]
	for id in SCENES:
		for f in (sets if id == "LS_C3_Trains" else [{}]):
			var s := _make(id, f)
			s.play()
			_run_to_end(s, 0.05)
			kit.eq(s.get("said"), s.chosen_lines(), "%s %s: subtitles spoken in order" % [id, str(f)])
			for key in s.chosen_lines():
				kit.ok(Loc.has(str(key)), "%s: locale has %s" % [id, key])
				kit.ok(Loc.t(str(key)) != str(key) and Loc.t(str(key)).length() > 10, "%s: %s has German text" % [id, key])
			_drop(s)
	return true


func _skip_stops_cues() -> bool:
	for id in SCENES:
		var s := _make(id)
		s.play()
		s.advance(0.2)
		var before: int = (s.get("said") as Array).size()
		s.skip()
		s.advance(30.0)
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


func _assets() -> bool:
	for id in SCENES:
		var s := _make(id)
		kit.eq(s.get("missing"), [], "%s: every texture exists" % id)
		_drop(s)
	var p := "res://assets/cinematics/ch3/layout.json"
	if not kit.ok(FileAccess.file_exists(p), "layout.json written by tools/pixelgen/env_veltrava_cine.py"):
		return true
	var L = JSON.parse_string(FileAccess.get_file_as_string(p))
	if not kit.ok(L is Dictionary, "layout.json parses"):
		return true
	var tr = load("res://scenes/cinematics/ch3_trains/ch3_trains.gd")
	var g: Rect2i = tr.GLASS
	kit.eq(L["trains"]["glass"], [float(g.position.x), float(g.position.y), float(g.end.x), float(g.end.y)],
		"train window glass: runtime == generator (the match cut)")
	var e: Rect2i = tr.EXT
	kit.eq(L["trains"]["ext"], [float(e.position.x), float(e.position.y), float(e.size.x), float(e.size.y)],
		"exterior box: runtime == generator")
	var th = load("res://scenes/cinematics/ch3_tohall/ch3_tohall.gd")
	kit.eq(L["tohall"]["center"], [float(th.CENTER.x), float(th.CENTER.y)], "clock centre: runtime == generator")
	var cl = load("res://scenes/cinematics/ch3_close/ch3_close.gd")
	for k in ["vpx", "vpy", "f", "eye"]:
		kit.eq(float(L["close"]["proj"][k]), float(cl.PROJ[k]), "platform projection %s: runtime == generator" % k)
	return true


func _layout() -> Dictionary:
	var p := "res://assets/cinematics/ch3/layout.json"
	if not FileAccess.file_exists(p):
		return {}
	var L = JSON.parse_string(FileAccess.get_file_as_string(p))
	return L if L is Dictionary else {}


func _layout_keys() -> bool:
	var L := _layout()
	if not kit.ok(not L.is_empty(), "layout.json readable"):
		return true
	var tr: Dictionary = L.get("trains", {})
	for k in ["fig_konrad", "fig_alexei", "glow_lamp", "glow_tea", "steam_tea", "sweep", "spoon", "towers_de",
			"towers_su", "smoke", "train_de", "train_su", "pole", "d4", "d4_glints", "d4_chimneys", "d4_lit_windows",
			"d4_tram", "line", "station_lamps", "mid_de_road", "mid_su_chimneys", "k_tassels", "k_cup", "people"]:
		kit.ok(tr.has(k), "layout trains.%s" % k)
	var d4: Dictionary = tr.get("d4", {})
	for k in ["planes", "de_rail", "su_rail", "water_y", "walker_y"]:
		kit.ok(d4.has(k), "layout trains.d4.%s" % k)
	var pl: Dictionary = d4.get("planes", {})
	kit.ok(float(pl.get("sky", 0)) < float(pl.get("city", 0)) and float(pl.get("city", 0)) < float(pl.get("bridge", 0))
		and float(pl.get("bridge", 0)) < float(pl.get("bank", 0)), "t4 crane: nearer planes travel farther (parallax)")
	var ln: Dictionary = tr.get("line", {})
	kit.ok(ln.has("proj") and ln.has("track_x") and ln.has("towers"), "layout trains.line (t3b projection, tracks, towers)")
	for side in ["train_de", "train_su"]:
		var d: Dictionary = tr.get(side, {})
		kit.ok(d.has("chimney") and d.has("headlamp") and d.has("front") and d.has("y"), "%s anchors" % side)
	kit.eq(int(tr.get("smoke", {}).get("frames", 0)), 8, "smoke atlas frames")
	var th: Dictionary = L.get("tohall", {})
	for k in ["center", "dial_r", "pendulum", "konrad_y", "steam_frames"]:
		kit.ok(th.has(k), "layout tohall.%s" % k)
	var cl: Dictionary = L.get("close", {})
	for k in ["proj", "board", "win_konrad", "win_alexei", "lamp", "ember", "steam_frames"]:
		kit.ok(cl.has(k), "layout close.%s" % k)
	var wk: Array = cl.get("win_konrad", [0, 0])
	var wa: Array = cl.get("win_alexei", [0, 0])
	kit.ok(float(wk[0]) < 214.0 and float(wa[0]) > 428.0, "the lit windows sit in the two different hotels, far apart")
	kit.ok(float(wk[1]) > 46.0 and float(wa[1]) > 46.0 and float(wk[1]) < 300.0 and float(wa[1]) < 300.0,
		"both lit windows inside the letterboxed picture")
	return true


## every sound named by a cue resolves to a file (variants id_1.. count, like Audio.sfx does)
func _sounds() -> bool:
	for id in SCENES:
		var s := _make(id)
		for c in s.get("_cues"):
			var d: Dictionary = c
			if d.has("sfx"):
				var n := str(d["sfx"])
				var ok := ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % n) \
					or ResourceLoader.exists("res://assets/audio/sfx/%s_1.wav" % n)
				kit.ok(ok, "%s: sfx %s exists" % [id, n])
			if d.has("amb") and str(d["amb"]) != "":
				kit.ok(ResourceLoader.exists("res://assets/audio/amb/%s.wav" % str(d["amb"])), "%s: amb %s" % [id, d["amb"]])
			if d.has("music") and str(d["music"]) != "":
				kit.ok(ResourceLoader.exists("res://assets/audio/music/%s.wav" % str(d["music"])),
					"%s: music %s" % [id, d["music"]])
			if d.has("loop"):
				kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % str(d["loop"])), "%s: loop %s" % [id, d["loop"]])
			if d.has("bed"):
				kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % str(d["bed"])), "%s: bed %s" % [id, d["bed"]])
		_drop(s)
	return true


## the visual knocks of both cars (ch3_trains.gd JOINT) and the knocks cut into the bed sounds must agree
func _joints() -> bool:
	var tr = load("res://scenes/cinematics/ch3_trains/ch3_trains.gd")
	var J: Dictionary = tr.JOINT
	var src := FileAccess.get_file_as_string("res://tools/audiogen/c3_cine_audio.py")
	if not kit.ok(src != "", "tools/audiogen/c3_cine_audio.py readable"):
		return true
	var rx := RegEx.new()
	rx.compile("JOINT_(DE|SU) = \\(([0-9.]+), ([0-9.]+)\\)")
	var found := {}
	for m in rx.search_all(src):
		found[m.get_string(1)] = [float(m.get_string(2)), float(m.get_string(3))]
	kit.ok(found.has("DE") and found.has("SU"), "audio generator declares JOINT_DE / JOINT_SU")
	if found.has("DE"):
		kit.ok(absf(float(J["k"][0]) - found["DE"][0]) < 0.001 and absf(float(J["k"][1]) - found["DE"][1]) < 0.001,
			"saloon car: visual joints == c3cine_ride_de joints")
	if found.has("SU"):
		# the Soviet bed starts at the cut (CUT), its joints are relative to that start
		var cut := float(tr.CUT)
		kit.ok(absf(float(J["a"][0]) - cut - found["SU"][0]) < 0.001 and absf(float(J["a"][1]) - found["SU"][1]) < 0.001,
			"Soviet car: visual joints == c3cine_ride_su joints")
	return true


func _still() -> bool:
	for rm in [1, 0]:
		var s: Node = load(SCENES["LS_C3_Trains"]).instantiate()
		s.set("use_director", false)
		s.set("reduced_motion_override", rm)
		(Engine.get_main_loop() as SceneTree).root.add_child(s)
		kit.track(s)
		s.play()
		var moved := 0
		var tt := 0.0
		while tt < 17.5:
			s.seek(tt)
			if s.get("room_k").position.y != 0.0 or s.get("room_a").position.y != 0.0 or s.get("ext").position.y != 0.0:
				moved += 1
			tt += 0.02
		if rm == 1:
			kit.eq(moved, 0, "reduced motion: no knocks, no roll")
		else:
			kit.ok(moved > 20, "full motion: the car knocks over the joints (%d frames)" % moved)
		_drop(s)
	return true


func _dawn() -> bool:
	var s := _make("LS_C3_Trains")
	s.play()
	s.seek(16.0)
	kit.ok(not s.get("line").visible and not s.get("dawn").visible, "t3b and dawn hidden during t3")
	s.seek(19.5)
	kit.ok(s.get("line").visible, "the Line before dawn visible in t3b")
	kit.ok(not s.get("win").visible, "the compartment is gone once the first dissolve has completed")
	for m in s.get("_line_mats"):
		kit.eq(float((m as ShaderMaterial).get_shader_parameter("progress")), 1.0, "t3 -> t3b dissolve finished")
	s.seek(25.0)
	kit.ok(s.get("dawn").visible, "dawn visible in t4")
	kit.ok(not s.get("line").visible, "t3b gone once the dawn dissolve has completed")
	for m in s.get("_dawn_mats"):
		kit.eq(float((m as ShaderMaterial).get_shader_parameter("progress")), 1.0, "t3b -> t4 dissolve finished")
	# the crane: the bridge plane starts high in frame and comes down to its home row; the city rises less
	var b0 := float(s.get("_off")["bridge"])
	s.seek(35.9)
	var b1 := float(s.get("_off")["bridge"])
	var c1 := float(s.get("_off")["city"])
	kit.ok(b0 < -100.0 and absf(b1) < 0.5 and absf(c1) < 0.5, "t4 crane: planes move from the low start to the city view")
	s.skip()
	kit.ok(s.get("dawn").visible, "skip lands on the dawn's final frame")
	_drop(s)
	# reduced motion: no crane, the middle view is held
	var r: Node = load(SCENES["LS_C3_Trains"]).instantiate()
	r.set("use_director", false)
	r.set("reduced_motion_override", 1)
	(Engine.get_main_loop() as SceneTree).root.add_child(r)
	kit.track(r)
	r.play()
	r.seek(25.0)
	var a0 := float(r.get("_off")["bridge"])
	r.seek(35.0)
	kit.eq(float(r.get("_off")["bridge"]), a0, "reduced motion: the crane holds one view")
	_drop(r)
	return true
