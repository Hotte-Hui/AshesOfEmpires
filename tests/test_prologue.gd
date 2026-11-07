extends RefCounted
## Round 11: the prologue of a new game LS_Prologue (scenes/cinematics/prologue, TECHNICAL_ARCHITECTURE §12.5 runtime).
## The scene is instanced in the tree and driven headless (use_director = false: no Game/Audio/subtitle side effects,
## nothing written).  Contract: finished fires exactly once per run (skip, skip twice, natural end, replay), skip()
## jumps to the final frame; 45-60 s in 4-6 contiguous shots; every line is German text from de_prologue.json,
## spoken in order, readable and never overlapping; every texture, sound and the score exist and layout.json carries
## the runtime anchors; frames are a pure function of t; the story beats sit where the shot sheet says (the Line
## drawn, Veltrava ringed, the stamp's C-17, Konrad at the window, Alexei walking in, the signal clearing); reduced
## motion halves the camera drift.  The director side: Game plays it on a NEW game only (after the opening note,
## before the first level; never on load / continue), offers it first on the „Filmsequenzen“ page, and both E2E drivers
## get past it like a player.  No fiction note in its text (one opening note per new game is enough).

const Kit := preload("res://tests/support/test_kit.gd")
const SCENE := "res://scenes/cinematics/prologue/Prologue.tscn"
const ASSETS := "res://assets/cinematics/prologue/"
const TEXTURES := ["p1_line.png", "p1_windowglow.png", "p2_map.png", "p2_veltrava.png", "p3_papers.png",
	"p3_stamp.png", "p3_shadow.png", "p3_imprint.png", "p4_berlin.png", "p4_konrad.png", "p4_lampglow.png",
	"p5_karsk.png", "p5_alexei_walk.png", "p5_alexei_idle.png", "p5_cone.png", "p5_signal.png", "p5_headlamp.png"]
const MAX_CPS := 22.5

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("contract_api_length_and_shots", _api)
	kit.run_case("skip_then_skip_finishes_once", _skip_twice)
	kit.run_case("natural_end_and_replay_finish_once", _natural_end)
	kit.run_case("lines_german_in_order_readable", _lines)
	kit.run_case("textures_sounds_score_layout", _assets)
	kit.run_case("frames_are_a_pure_function_of_t", _pure)
	kit.run_case("story_beats_on_the_sheet", _beats)
	kit.run_case("reduced_motion_halves_the_drift", _reduced)
	kit.run_case("game_plays_it_on_a_new_game_only", _flow)
	kit.run_case("films_page_offers_it_first", _films)
	kit.run_case("drivers_get_past_it_like_a_player", _drivers)
	kit.cleanup()
	return kit.failures


func _make(rm := -1) -> Node:
	var s: Node = load(SCENE).instantiate()
	s.set("use_director", false)
	if rm >= 0:
		s.set("reduced_motion_override", rm)
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	kit.track(s)
	s.configure({"choices": {}, "flags": {}, "symbols": true})
	return s


func _drop(s: Node) -> void:
	if is_instance_valid(s):
		if s.get_parent():
			s.get_parent().remove_child(s)
		s.free()


func _counter(s: Node) -> Array:
	var n := [0]
	s.finished.connect(func() -> void: n[0] += 1)
	return n


func _run_to_end(s: Node, dt := 0.05) -> void:
	var guard := 0
	while not s.is_finished() and guard < 5000:
		s.advance(dt)
		guard += 1


func _api() -> bool:
	if not kit.ok(ResourceLoader.exists(SCENE), "the prologue scene exists"):
		return true
	var s := _make()
	kit.ok(s is Node2D, "root is Node2D")
	for m in ["configure", "play", "skip", "chosen_lines", "seek", "advance", "is_finished", "get_shot_id"]:
		kit.ok(s.has_method(m), "has %s()" % m)
	kit.ok(s.has_signal("finished"), "has signal finished")
	kit.eq(str(s.get("grade_preset")), "c3_cine", "neutral film grade")
	var d := float(s.get_duration())
	kit.ok(d >= 45.0 and d <= 60.0, "lasts 45-60 s (%.1f s)" % d)
	kit.ok(float(s.get("max_duration")) > d, "max_duration > duration")
	var shots: Array = s.SHOTS
	kit.ok(shots.size() >= 4 and shots.size() <= 6, "4-6 painted shots (%d)" % shots.size())
	kit.eq(float(shots[0][1]), 0.0, "the first shot starts at 0")
	kit.eq(float(shots[-1][2]), d, "the last shot ends with the film")
	for i in range(1, shots.size()):
		kit.eq(float(shots[i][1]), float(shots[i - 1][2]), "shot %s follows %s without a gap" % [shots[i][0], shots[i - 1][0]])
	s.play()
	for sh in shots:
		for probe in [float(sh[1]) + 0.05, (float(sh[1]) + float(sh[2])) * 0.5, float(sh[2]) - 0.05]:
			s.seek(probe)
			kit.eq(str(s.get_shot_id()), str(sh[0]), "at %.2f s the shot is %s" % [probe, sh[0]])
	_drop(s)
	return true


func _skip_twice() -> bool:
	var s := _make()
	var n := _counter(s)
	s.play()
	s.advance(2.0)
	s.skip()
	s.skip()
	kit.eq(n[0], 1, "play, skip, skip -> finished once")
	kit.ok(s.is_finished(), "is_finished after skip")
	kit.ok(absf(s.get_time() - s.get_duration()) < 0.001, "skip jumps to the final frame")
	kit.ok(float(s.dip_alpha(s.get_time())) > 0.99, "the final frame is black (the cut to Chapter 1)")
	s.advance(1.0)
	kit.eq(n[0], 1, "advancing after skip emits nothing")
	_drop(s)
	return true


func _natural_end() -> bool:
	var s := _make()
	var n := _counter(s)
	s.play()
	_run_to_end(s)
	kit.eq(n[0], 1, "natural end -> finished once")
	kit.eq(s.said, s.chosen_lines(), "every line spoken once, in order")
	s.play()
	s.advance(3.0)
	s.skip()
	kit.eq(n[0], 2, "a replay finishes once more")
	kit.ok(s.missing.is_empty(), "no texture missing: %s" % [s.missing])
	_drop(s)
	return true


func _lines() -> bool:
	var s := _make()
	var keys: Array = s.chosen_lines()
	kit.ok(keys.size() >= 8, "a short narration (%d lines)" % keys.size())
	var prev_end := -1.0
	var lines: Array = s.LINES
	var shots: Array = s.SHOTS
	for l in lines:
		var key := str(l[0])
		var at := float(l[1])
		var txt := Loc.t(key)
		kit.ok(Loc.has(key) and txt != key and txt.strip_edges() != "", "%s has German text" % key)
		kit.ok(not txt.to_lower().contains("fiktiv"), "%s carries no fiction note" % key)
		var dur := float(s.line_dur(key))
		kit.ok(float(txt.length()) / dur <= MAX_CPS, "%s readable (%.1f cps)" % [key, float(txt.length()) / dur])
		kit.ok(at >= prev_end, "%s starts after the previous line ended" % key)
		prev_end = at + dur
		kit.ok(prev_end <= float(s.get_duration()) - 0.5, "%s ends before the fade to black" % key)
		var inside := false
		for sh in shots:
			if at >= float(sh[1]) + float(s.DIP) and at + dur <= float(sh[2]) + 0.01:
				inside = true
		kit.ok(inside, "%s stays inside one shot (no line across a cut)" % key)
	for k in ["ui.memories.film.LS_Prologue", "ui.memories.film_sub.LS_Prologue"]:
		kit.ok(Loc.has(k), "%s exists" % k)
	_drop(s)
	return true


func _assets() -> bool:
	for f in TEXTURES:
		kit.ok(ResourceLoader.exists(ASSETS + f), "%s imported" % f)
	kit.ok(ResourceLoader.exists("res://assets/audio/music/mus_prologue.wav"), "the score mus_prologue exists")
	var s := _make()
	for b in s.BEDS:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % b[1]), "sound %s exists" % b[1])
	var has_music := false
	for c in s._make_cues():
		if c.has("music") and str(c["music"]) == "mus_prologue":
			has_music = true
	kit.ok(has_music, "the film cues its score")
	for sec in ["line", "map", "papers", "berlin", "karsk"]:
		kit.ok(not s.pl(sec).is_empty(), "layout.json section %s" % sec)
	kit.eq((s.pl("map").get("corridors", []) as Array).size(), 3, "three corridors on the map")
	var konrad: Texture2D = s.tex("p4_konrad.png")
	var alexei: Texture2D = s.tex("p5_alexei_walk.png")
	kit.ok(konrad != null and konrad.get_height() == 56 and konrad.get_width() % 32 == 0, "Konrad: frames of his game sheet")
	kit.ok(alexei != null and alexei.get_height() == 56 and alexei.get_width() % 32 == 0, "Alexei: frames of his game sheet")
	kit.eq(s.missing, [], "no texture missing")
	_drop(s)
	return true


func _state(s: Node) -> Array:
	return [s.get_shot_id(), s.p1.visible, s.p5.visible, s._pan1.position, s._pan3.position, s._pan4.position,
		s._pan5.position, s._stamp3.position, s._stamp3.visible, s._imprint.visible, s._konrad.frame, s._alexei.position,
		s._alexei.frame, s._alexei.visible, s._signal5.frame, s._label2.visible]


func _pure() -> bool:
	var s := _make()
	s.play()
	for probe in [5.0, 15.2, 20.0, 37.1, 44.0, 52.3, 58.0]:
		s.seek(probe)
		var a := _state(s)
		s.seek(59.5)
		s.seek(1.0)
		s.seek(probe)
		kit.eq(_state(s), a, "the frame at %.1f s does not depend on the way there" % probe)
	_drop(s)
	return true


func _beats() -> bool:
	var s := _make()
	s.play()
	kit.ok(float(s.dip_alpha(0.0)) > 0.99, "the film begins on black")
	kit.ok(float(s.dip_alpha(6.0)) < 0.01, "mid-shot: no dip")
	for sh in (s.SHOTS as Array).slice(1):
		kit.ok(float(s.dip_alpha(float(sh[1]))) > 0.99, "a dip through black at the cut to %s" % sh[0])
	kit.eq(float(s.line_drawn(13.0)), 0.0, "the Line is not drawn before the map")
	kit.eq(float(s.line_drawn(17.0)), 1.0, "the Line is drawn by 17 s")
	for i in 3:
		kit.ok(float(s.corridor_drawn(i, 23.0)) == 0.0 and float(s.corridor_drawn(i, 28.0)) == 1.0,
			"corridor %d is drawn while the Accord is named" % i)
	s.seek(18.0)
	kit.ok(not s._label2.visible, "Veltrava not yet labelled")
	s.seek(20.0)
	kit.ok(s._label2.visible, "Veltrava labelled when it is named")
	s.seek(36.0)
	kit.ok(not s._imprint.visible and not s._stamp3.visible, "no stamp, no imprint before the stamp comes")
	s.seek(float(s.STAMP[1]) + 0.1)
	var land := (s.lv(s.pl("papers"), "imprint_at", Vector2.ZERO) as Vector2) + (s.STAMP_OFF as Vector2)
	kit.ok(s._imprint.visible and s._stamp3.visible and s._stamp3.position == land, "the stamp lands: C-17")
	s.seek(39.0)
	kit.ok(s._imprint.visible and not s._stamp3.visible, "the imprint stays, the stamp is gone")
	s.seek(44.0)
	kit.ok(s.p4.visible and s._konrad.visible, "Konrad at the window in Berlin")
	s.seek(50.0)
	var x1 := float(s.alexei_at(50.0)[0])
	s.seek(53.0)
	kit.ok(float(s.alexei_at(53.0)[0]) < x1 and s._alexei.visible, "Alexei walks in (to the left)")
	kit.eq(s._signal5.frame, 0, "the signal is red while he walks")
	s.seek(59.0)
	kit.ok(not bool(s.alexei_at(59.0)[1]) and s._alexei_idle.visible, "he has stopped by the end")
	kit.eq(s._signal5.frame, 1, "the signal has cleared")
	_drop(s)
	return true


func _reduced() -> bool:
	var full := _make(0)
	var calm := _make(1)
	full.play()
	calm.play()
	full.seek(12.9)
	calm.seek(12.9)
	var a := absf(full._pan1.position.x)
	var b := absf(calm._pan1.position.x)
	kit.ok(a > 20.0 and absf(b - a * 0.5) <= 1.0, "p1 drift %.0f px, reduced %.0f px" % [a, b])
	_drop(full)
	_drop(calm)
	return true


func _body(src: String, fn: String) -> String:
	var at := src.find("\nfunc %s(" % fn)
	if at < 0:
		return ""
	var end := src.find("\nfunc ", at + 1)
	return src.substr(at, (end if end > 0 else src.length()) - at)


func _flow() -> bool:
	var src := FileAccess.get_file_as_string("res://scripts/core/game.gd")
	var ng := _body(src, "_on_new_game")
	var d := ng.find("await _show_disclaimer()")
	var p := ng.find("await _cin_prologue()")
	var g := ng.find("await goto_level(")
	kit.ok(d >= 0 and p > d and g > p, "a new game: the opening note, then the prologue, then the first level")
	for fn in ["_on_continue", "_on_load_slot", "_on_loaded_slot", "_after_story_change"]:
		kit.ok(not _body(src, fn).contains("_cin_prologue"), "%s() never plays the prologue" % fn)
	var cp := _body(src, "_cin_prologue")
	kit.ok(cp.contains("_begin_cinematic()") and cp.contains("_end_cinematic()") and cp.contains("cin.skip()"),
		"the prologue runs as a skippable cinematic (letterbox, Esc)")
	kit.ok(cp.contains("prologue = null"), "Game.prologue is cleared when it ends")
	var game: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if game != null:
		kit.ok(game.get("prologue") == null, "no prologue running in the tests")
	kit.ok(_body(src, "_play_cinematic_by_id").contains("PROLOGUE_ID:"), "--cinematic=LS_Prologue plays it (captures)")
	return true


func _films() -> bool:
	var game: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if game == null or not game.has_method("memory_films"):
		return true
	var keep: String = Story.save_json()
	Story.new_game()
	var films: Array = game.memory_films("game")
	kit.ok(not films.is_empty() and str(films[0]["id"]) == "LS_Prologue", "the prologue is the first film")
	if not films.is_empty():
		kit.ok(bool(films[0]["unlocked"]) and str(films[0]["title"]) != "", "seen by every game (title shown)")
	kit.ok(game._film_exists("LS_Prologue"), "its scene exists")
	kit.eq(game._film_snapshot("LS_Prologue"), "", "no Story state needed to watch it")
	kit.ok(not game.rewatch_film("LS_Prologue", false), "no rewatch without a running level (tests)")
	Story.load_json(keep)
	return true


func _drivers() -> bool:
	var ap := FileAccess.get_file_as_string("res://scripts/core/autoplay.gd")
	var ip := FileAccess.get_file_as_string("res://scripts/core/inputplay.gd")
	var run := _body(ap, "run")
	var p := run.find("Game._cin_prologue()")
	kit.ok(p >= 0 and p < run.find("Game.goto_level("), "autoplay: a new game plays the prologue before the first level")
	var pb := _body(ip, "_prologue")
	kit.ok(_body(ip, "_menu_new_game").contains("_prologue()"), "inputplay: the prologue follows 'Neues Spiel'")
	kit.ok(pb.contains("Game.prologue != null and Game.in_cinematic") and pb.contains("KEY_ESCAPE"),
		"inputplay: Esc only while the prologue runs")
	return true
