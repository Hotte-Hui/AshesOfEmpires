extends RefCounted
## Round-7 mini-games (owner: minigames_r7_kb, TECHNICAL_ARCHITECTURE §12.8): "Der Morsetaster" in the Karsk signal
## box and "Rohrpost" in the Berlin reading room.
## * logic: the Morse chart is complete and unique, the telegram arrives on a timeline, only arrived letters can be
##   decoded, wrong letters / elements are refused with a reason, the receipt is keyed with forgiving timing; the
##   three tube boards are solvable with a unique fewest-change setting (2, 3, 4 changes), start somewhere else,
##   lead through the wrong offices one by one, jam / freeze / loop are detected, the polyline is continuous;
## * scenes: §12.8 contract (finished exactly once, open, demo_solve driven by synthetic keys only, auto mode),
##   keyboard play through modal_input to the solution, hint after two refusals, Esc gives up without a find;
## * data: explore entries, Loc keys and texts, close-up images, art sizes, layout files, audio files;
## * placement: content-owned hotspots inside the walk band, clear of story spots and other finds, one Interactable
##   per find under Playfield.

const Kit := preload("res://tests/support/test_kit.gd")
const MorseLogic := preload("res://scripts/ui/minigames/morse_logic.gd")
const TubeLogic := preload("res://scripts/ui/minigames/rohrpost_logic.gd")
const MORSE_SCENE := "res://scenes/ui/minigames/MorseKey.tscn"
const TUBE_SCENE := "res://scenes/ui/minigames/Rohrpost.tscn"
const MORSE_GAME := "res://scripts/ui/minigames/morse_game.gd"
const TUBE_GAME := "res://scripts/ui/minigames/rohrpost_game.gd"
const SCRIPTS := ["res://scripts/ui/minigames/morse_game.gd", "res://scripts/ui/minigames/morse_logic.gd",
	"res://scripts/ui/minigames/rohrpost_game.gd", "res://scripts/ui/minigames/rohrpost_logic.gd"]
const DATA := "res://data/explore/minigames_r7_kb.json"
const STRINGS := "res://data/locale/de_minigames_r7_kb.json"
const TUBE_LAYOUT := "res://assets/ui/minigames/rohrpost/rohrpost_layout.json"
const MORSE_LAYOUT := "res://assets/ui/minigames/morse/morse_layout.json"
const ENTRIES := {
	"karsk.morse": {"scene": MORSE_SCENE, "level": "res://scenes/levels/L_A1_Railyard.tscn", "level_id": "L_A1_Railyard",
		"env": "res://assets/environments/karsk_railyard/", "hotspot": "exp_morse", "node": "ExpMorse", "area": "karsk",
		"oblique": true, "story": ["irina", "seal", "timetable", "signal_board", "ledger"], "min_find": 12.0},
	"berlin.rohrpost": {"scene": TUBE_SCENE, "level": "res://scenes/levels/L_M1_Archive.tscn", "level_id": "L_M1_Archive",
		"env": "res://assets/environments/berlin_archive/", "hotspot": "exp_rohrpost", "node": "ExpRohrpost", "area": "berlin",
		"oblique": false, "story": ["plan_a", "plan_b", "overlay_table", "emil", "obs_window", "obs_photo", "obs_notice"],
		"min_find": 14.0},
}
const MINIGAME_SPOTS := ["exp_shunting", "exp_chess", "exp_radio_dial"]
const MIN_STORY := 26.0
const MIN_MINIGAME := 26.0
## International Morse of the Latin letters: the chart's "equivalent" column must agree with it.
const INTERNATIONAL := {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
	"I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
	"S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..", "Ä": ".-.-",
	"Ö": "---.", "Ü": "..--", "CH": "----", "É": "..-..", "Ñ": "--.--"}
const DT := 0.05

var kit: Kit
var loc: Node


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("morse_chart_and_message", _morse_chart)
	kit.run_case("morse_timeline", _morse_timeline)
	kit.run_case("morse_solution_accepted", _morse_solution)
	kit.run_case("morse_refusals", _morse_refusals)
	kit.run_case("tube_boards_solvable_and_rising", _tube_boards)
	kit.run_case("tube_outcomes_and_geometry", _tube_outcomes)
	kit.run_case("scenes_contract_and_auto", _scenes_auto)
	kit.run_case("morse_scene_by_keys", _morse_keys)
	kit.run_case("tube_scene_by_keys", _tube_keys)
	kit.run_case("give_up_and_finished_once", _give_up)
	kit.run_case("hints_follow_the_setting", _hint_setting)
	kit.run_case("mouse_paths", _mouse)
	kit.run_case("telegram_form_layout", _form_layout)
	kit.run_case("demo_solve_uses_synthetic_keys", _demo_source)
	kit.run_case("explore_entries_and_texts", _data)
	kit.run_case("loc_keys", _loc_keys)
	kit.run_case("art_and_layout_files", _art)
	kit.run_case("audio_files", _audio)
	kit.run_case("placement_in_the_levels", _placement)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


# ================================================================ Morse logic
func _morse_chart() -> bool:
	var codes := {}
	var letters := {}
	kit.eq(MorseLogic.TABLE.size(), MorseLogic.COLS * MorseLogic.ROWS, "the chart fills its 7 x 6 grid")
	for row in MorseLogic.TABLE:
		var code := str(row[1])
		kit.ok(not codes.has(code), "code %s is unique (%s)" % [code, row[0]])
		kit.ok(not letters.has(str(row[0])), "letter %s appears once" % row[0])
		codes[code] = true
		letters[str(row[0])] = true
		var lat := str(row[2])
		if INTERNATIONAL.has(lat):
			kit.eq(code, INTERNATIONAL[lat], "%s uses the international code of %s" % [row[0], lat])
		elif lat.is_valid_int():
			kit.eq(lat, str(row[0]), "digit %s" % lat)
		else:
			kit.fail("%s: unknown equivalent %s" % [row[0], lat])
	for d in 10:
		kit.ok(letters.has(str(d)), "digit %d on the chart" % d)
	kit.eq(MorseLogic.code_of("Ш"), "----", "Ш is four dashes")
	kit.eq(MorseLogic.code_of("П"), ".--.", "П")
	var lg = MorseLogic.new()
	var target := ""
	for li in lg.targets:
		target += str(lg.letters[li]["ch"])
	kit.eq(target, "НЕВЗВЕШИВАТЬ", "the words to decode")
	for l in lg.letters:
		kit.ok(MorseLogic.code_of(str(l["ch"])) != "", "%s is on the chart" % l["ch"])
	kit.eq(lg.ack_total(), 7, "receipt ПР has 7 elements")
	return true


func _morse_timeline() -> bool:
	var lg = MorseLogic.new()
	var ev: Array = []
	var ons := 0
	var offs := 0
	var arrived := 0
	var on_samples := 0
	var steps := int((lg.end_t + 0.5) / 0.01)
	for i in steps:
		for e in lg.step(0.01):
			var s := str(e)
			if s == "on":
				ons += 1
			elif s == "off":
				offs += 1
			elif s.begins_with("arrived:"):
				arrived += 1
			ev.append(s)
		if lg.signal_on():
			on_samples += 1
	var elements := 0
	for l in lg.letters:
		elements += str(l["code"]).length()
	kit.eq(ev[0], "bell", "the call bell rings first")
	kit.eq(ons, elements, "one sounder click per element (%d)" % elements)
	kit.eq(offs, elements, "and one release per element")
	kit.eq(arrived, lg.letters.size(), "every letter arrives once")
	kit.eq(ev.count("end"), 1, "the transmission ends once")
	kit.ok(on_samples > 0 and on_samples < steps, "the lamp is lit only while an element is on")
	kit.ok(lg.end_t > 8.0 and lg.end_t < 26.0, "the telegram takes %.1f s (8-26)" % lg.end_t)
	kit.ok(not lg.transmitting(), "transmission over")
	# a big step still announces every letter in order
	var lg2 = MorseLogic.new()
	var ev2: Array = lg2.step(lg2.end_t + 1.0)
	var arr2: Array = ev2.filter(func(x): return str(x).begins_with("arrived:"))
	kit.eq(arr2.size(), lg2.letters.size(), "a long step announces all letters")
	kit.eq(str(arr2[0]), "arrived:0", "in order")
	# the slow words are slower than the routine
	var fast := float(lg.letters[0]["t1"]) - float(lg.letters[0]["t0"])
	var li_w := int(lg.targets[2])           # В of ВЗВЕШИВАТЬ, same code as the routine В
	var slow := float(lg.letters[li_w]["t1"]) - float(lg.letters[li_w]["t0"])
	kit.ok(slow > fast * 1.3, "the unusual words come slower (%.2f s vs %.2f s)" % [slow, fast])
	return true


func _decode_all(lg) -> int:
	var waits := 0
	while lg.phase == "decode" and waits < 4000:
		if lg.can_pick():
			var r: Dictionary = lg.pick(str(lg.letters[lg.current_letter()]["ch"]))
			if not kit.ok(bool(r.get("ok", false)), "correct letter accepted"):
				return waits
		else:
			lg.step(DT)
			waits += 1
	return waits


func _morse_solution() -> bool:
	var lg = MorseLogic.new()
	_decode_all(lg)
	kit.eq(lg.phase, "answer", "all letters decoded -> receipt")
	kit.eq(lg.decoded, "НЕВЗВЕШИВАТЬ", "decoded text")
	kit.eq(lg.group_text(3), "ВЗВЕШИВАТЬ", "group text after decoding")
	kit.eq(lg.group_text(1), "24311", "routine group written by itself")
	for a in lg.ack_codes:
		for e in str(a[1]):
			var r: Dictionary = lg.key(0.1 if e == "." else 0.45)
			kit.ok(bool(r.get("ok", false)), "receipt element %s of %s accepted" % [e, a[0]])
	kit.eq(lg.phase, "reply", "the line answers")
	var ev: Array = []
	for i in 200:
		ev.append_array(lg.step(DT))
		if lg.phase == "done":
			break
	kit.ok("reply_on" in ev and "done" in ev, "reply clicks, then done (%s)" % [ev.slice(0, 6)])
	kit.eq(lg.phase, "done", "solved")
	kit.eq(lg.wrong_picks + lg.wrong_keys, 0, "a careful player is never refused")
	return true


func _morse_refusals() -> bool:
	var lg = MorseLogic.new()
	kit.eq(str(lg.pick("Н").get("reason", "")), "wait", "nothing can be decoded before it arrived")
	while not lg.can_pick():
		lg.step(DT)
	var r: Dictionary = lg.pick("Т")
	kit.eq(str(r.get("reason", "")), "wrong", "a wrong letter is refused")
	kit.eq(str(r.get("code", "")), "-.", "the refusal names the code on the tape")
	kit.eq(str(r.get("other", "")), "-", "and the code of the picked letter")
	kit.eq(lg.cursor, 0, "nothing written")
	kit.eq(lg.wrong_picks, 1, "one wrong pick counted")
	kit.eq(str(lg.key(0.1).get("reason", "")), "phase", "the key does nothing while decoding")
	_decode_all(lg)
	# forgiving timing: below DASH_AT a dot, from DASH_AT on a dash
	var e1: Dictionary = lg.key(MorseLogic.DASH_AT - 0.01)
	kit.ok(bool(e1.get("ok", false)) and str(e1["element"]) == ".", "a press just under the mark is a dot")
	var e2: Dictionary = lg.key(MorseLogic.DASH_AT)
	kit.ok(bool(e2.get("ok", false)) and str(e2["element"]) == "-", "a press at the mark is a dash")
	kit.eq(lg.ack_confirmed(), 2, "two elements confirmed")
	var bad: Dictionary = lg.key(0.1)                     # П = .--. : a dash is wanted here
	kit.eq(str(bad.get("reason", "")), "dash", "a dot where a dash belongs is refused")
	kit.eq(lg.ack_confirmed(), 0, "the letter starts again")
	kit.eq(lg.ack_letter, 0, "still the first letter")
	for e in ".--.":
		lg.key(0.1 if e == "." else 0.5)
	kit.eq(lg.ack_letter, 1, "П complete")
	var bad2: Dictionary = lg.key(0.6)                    # Р = .-. : a dot first
	kit.eq(str(bad2.get("reason", "")), "dot", "a dash where a dot belongs is refused")
	kit.eq(lg.ack_letter, 1, "only Р restarts, П stays")
	kit.eq(str(lg.pick("А").get("reason", "")), "phase", "no more decoding during the receipt")
	return true


# ================================================================ tube logic
func _tube_boards() -> bool:
	var lg = TubeLogic.new()
	if not kit.eq(lg.board_count(), 3, "three boards"):
		return true
	var mins: Array = []
	for bi in 3:
		lg.board_i = bi
		lg.reset_board()
		var start := lg.simulate()
		kit.ok(not (str(start["result"]) == "arrive" and str(start.get("station", "")) == lg.target()),
			"board %d does not start solved" % (bi + 1))
		var sols: Array = lg.solutions()
		if not kit.ok(not sols.is_empty(), "board %d is solvable" % (bi + 1)):
			continue
		mins.append(int(sols[0][0]))
		kit.ok(sols.size() == 1 or int(sols[1][0]) > int(sols[0][0]), "board %d: one fewest-change setting" % (bi + 1))
		var gen: Array = (lg.boards[bi].get("solution", []) as Array).map(func(x): return int(x))
		kit.eq(sols[0][1], gen, "board %d: generator solution matches the logic" % (bi + 1))
		# fixing the knobs in the order the capsule meets them: every fix brings the capsule somewhere new or
		# further (one knob fewer to turn), and no office is visited twice
		var seen := {}
		var outcomes := 0
		var guard := 0
		var left: int = lg.wrong_diverters().size()
		while guard < 8:
			guard += 1
			var run := lg.simulate()
			if str(run["result"]) == "arrive" and str(run["station"]) == lg.target():
				break
			outcomes += 1
			if str(run["result"]) == "arrive":
				var where := str(run["station"])
				kit.ok(not seen.has(where), "board %d: the capsule lands in '%s' only once" % [bi + 1, where])
				seen[where] = true
			var w: Array = lg.wrong_diverters()
			if w.is_empty():
				break
			var di := int(w[0])
			lg.states[di] = int(sols[0][1][di])
			kit.eq(lg.wrong_diverters().size(), left - 1, "board %d: one knob fewer to turn" % (bi + 1))
			left = lg.wrong_diverters().size()
		kit.ok(guard <= 6, "board %d: solved by fixing knob after knob" % (bi + 1))
		kit.eq(outcomes, bi + 2, "board %d: %d wrong runs on the way" % [bi + 1, bi + 2])
	kit.eq(mins, [2, 3, 4], "rising difficulty: 2, 3, 4 knobs to turn")
	return true


func _tube_outcomes() -> bool:
	var lg = TubeLogic.new()
	var r1 := lg.send()
	kit.ok(not bool(r1["ok"]) and str(r1["result"]) == "arrive" and str(r1["station"]) == "registratur",
		"board 1 as found: the capsule lands in the registry")
	kit.eq(lg.wrong, 1, "counted as one wrong capsule")
	# jam: knob 1 joins N-E, the capsule comes from W
	lg.states[0] = 2
	var r2 := lg.simulate()
	kit.ok(str(r2["result"]) == "jam" and int(r2.get("diverter", -1)) == 0, "a knob that does not join the incoming tube jams")
	# frozen: board 2 as found
	lg.board_i = 1
	lg.reset_board()
	kit.eq(str(lg.simulate()["result"]), "frozen", "board 2 as found: the main line is frozen")
	# a full run with the solutions
	var lg2 = TubeLogic.new()
	for bi in 3:
		var sol: Array = lg2.solutions()[0][1]
		lg2.states = sol.duplicate()
		var r := lg2.send()
		kit.ok(bool(r["ok"]), "board %d solution delivers" % (bi + 1))
		var pts: PackedVector2Array = lg2.polyline(r)
		kit.ok(pts.size() >= 4, "board %d: polyline has %d points" % [bi + 1, pts.size()])
		kit.ok(pts[0].distance_to(lg2.source_mouth()) < 0.01, "starts at the lodge's mouth")
		kit.ok(pts[pts.size() - 1].distance_to(lg2.station_mouth(lg2.target())) < 0.01, "ends at the reading room's mouth")
		var maxstep := 0.0
		for i in range(1, pts.size()):
			maxstep = maxf(maxstep, pts[i - 1].distance_to(pts[i]))
		kit.ok(maxstep <= lg2.cell_size() + 0.01, "board %d: continuous path (max step %.1f)" % [bi + 1, maxstep])
		var more: bool = lg2.next_board()
		kit.eq(more, bi < 2, "next board after %d" % (bi + 1))
	kit.ok(lg2.done and lg2.delivered == [0, 1, 2], "all three capsules delivered")
	kit.eq(str(lg2.send()["result"]), "done", "nothing more to send")
	# loop detection (a ring with no exit)
	var lg3 = TubeLogic.new()
	lg3.boards = [{"id": 9, "source": {"cell": [0, 0], "side": "W"}, "target": "x", "stations": [],
		"tiles": {"0,0": "D", "1,0": "SW", "1,1": "NW", "0,1": "NE"},
		"diverters": [{"cell": [0, 0], "states": ["WE", "ES"], "start": 0}], "frozen": []}]
	lg3.data["grid"] = [2, 2]
	lg3.board_i = 0
	lg3.reset_board()
	kit.eq(str(lg3.simulate()["result"]), "jam", "ring board: the capsule meets the knob again from the south")
	lg3.boards[0]["tiles"]["0,0"] = "x"
	lg3.boards[0]["diverters"] = []
	lg3.boards[0]["tiles"]["0,1"] = "NE"
	lg3.boards[0]["source"] = {"cell": [1, 0], "side": "W"}
	lg3.boards[0]["tiles"]["1,0"] = "SW"
	lg3.boards[0]["tiles"]["0,0"] = "SE"
	lg3.reset_board()
	var r3: Dictionary = lg3.simulate()
	kit.eq(str(r3["result"]), "loop", "a closed ring is detected as a loop")
	return true


# ================================================================ scenes
func _instance(path: String) -> Node:
	var mg: Node = load(path).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(mg)
	kit.track(mg)
	return mg


func _scenes_auto() -> bool:
	for id in ENTRIES:
		var path: String = ENTRIES[id]["scene"]
		var mg := _instance(path)
		kit.ok(mg.is_in_group("minigame"), "%s joins group minigame" % id)
		kit.ok(mg.has_signal("finished") and mg.has_method("open") and mg.has_method("demo_solve"),
			"%s honours the §12.8 contract" % id)
		kit.ok(str(mg.get_script().get_base_script().resource_path).ends_with("minigame_base.gd"), "%s extends minigame_base.gd" % id)
		var got: Array = []
		mg.finished.connect(func(ok: bool): got.append(ok))
		mg.open({"explore_id": id, "auto": true})
		kit.ok(mg.is_open, "%s opens" % id)
		mg._process(0.1)
		kit.eq(got, [], "%s: not resolved before ~0.2 s" % id)
		mg._process(0.15)
		kit.eq(got, [true], "%s: auto mode resolves with success" % id)
		kit.ok(not mg.is_open, "%s closes itself" % id)
		mg._process(1.0)
		kit.eq(got, [true], "%s: finished exactly once" % id)
	return true


func _key(k: int, pressed := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = pressed
	return ev


func _press(mg: Node, k: int) -> void:
	mg.modal_input(_key(k, true))
	mg.modal_input(_key(k, false))


func _morse_keys() -> bool:
	var mg := _instance(MORSE_SCENE)
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "karsk.morse", "auto": false})
	_press(mg, KEY_ENTER)
	kit.eq(mg.logic.cursor, 0, "the key that opened the game writes nothing")
	mg._process(0.4)
	kit.ok(mg.modal_input(_key(KEY_RIGHT)), "Right is consumed (chart cursor)")
	kit.eq(mg.cursor, Vector2i(1, 0), "cursor moved")
	mg.modal_input(_key(KEY_LEFT))
	# wait for the first word, then refuse a wrong letter twice -> hint
	var guard := 0
	while not mg.logic.can_pick() and guard < 600:
		mg._process(DT)
		guard += 1
	kit.ok(mg.logic.can_pick(), "the first letter to decode arrives (%.1f s)" % mg.logic.t)
	mg.cursor = Vector2i(0, 0)                          # А, wrong for Н
	_press(mg, KEY_ENTER)
	_press(mg, KEY_SPACE)
	kit.eq(mg.fails, 2, "two wrong letters refused")
	kit.ok(mg._hint_box.visible and mg._hint_label.text.begins_with("Tipp"), "hint after two refusals")
	kit.eq(mg.logic.cursor, 0, "nothing written by wrong picks")
	# decode by keys: cursor moves on the chart, Enter writes
	guard = 0
	while mg.logic.phase == "decode" and guard < 2000:
		guard += 1
		if not mg.logic.can_pick():
			mg._process(DT)
			continue
		var want: Vector2i = MorseLogic.cell_of(MorseLogic.table_index(str(mg.logic.letters[mg.logic.current_letter()]["ch"])))
		var n := 0
		while mg.cursor != want and n < 20:
			n += 1
			if mg.cursor.x != want.x:
				_press(mg, KEY_RIGHT if want.x > mg.cursor.x else KEY_LEFT)
			else:
				_press(mg, KEY_DOWN if want.y > mg.cursor.y else KEY_UP)
		_press(mg, KEY_ENTER)
		mg._process(DT)
	kit.eq(mg.logic.decoded, "НЕВЗВЕШИВАТЬ", "decoded by keyboard")
	kit.eq(mg.logic.phase, "answer", "receipt phase")
	kit.ok(not mg._hint_box.visible, "the decode hint is put away for the receipt")
	# the receipt by holding Space: short = dot, long = dash
	for a in mg.logic.ack_codes:
		for e in str(a[1]):
			mg.modal_input(_key(KEY_SPACE, true))
			var hold := 0.1 if e == "." else 0.45
			var t := 0.0
			while t < hold:
				mg._process(DT)
				t += DT
			mg.modal_input(_key(KEY_SPACE, false))
			mg._process(DT)
	kit.eq(mg.logic.phase, "reply", "receipt keyed (wrong keys: %d)" % mg.logic.wrong_keys)
	guard = 0
	while not mg.solved and guard < 200:
		mg._process(DT)
		guard += 1
	kit.ok(mg.solved, "solved after the line's answer")
	for i in 80:
		mg._process(DT)
	kit.eq(got, [true], "finished(true) once after the hold")
	_press(mg, KEY_ENTER)
	mg.handle_cancel()
	kit.eq(got, [true], "no second finished")
	return true


func _tube_keys() -> bool:
	var nav := _instance(TUBE_SCENE)
	for bi in nav.logic.board_count():
		nav.logic.board_i = bi
		nav.logic.reset_board()
		var n_div: int = nav.logic.diverters().size()
		for a in n_div:
			for b in n_div:
				var cur := a
				var presses := 0
				var dirs := {KEY_RIGHT: Vector2.RIGHT, KEY_LEFT: Vector2.LEFT, KEY_UP: Vector2.UP, KEY_DOWN: Vector2.DOWN}
				while cur != b and presses < 10:
					presses += 1
					cur = nav.nav_target(cur, dirs[nav.nav_key_toward(cur, b)])
				kit.ok(cur == b, "board %d: knob %d reaches knob %d by arrows (%d presses)" % [bi + 1, a + 1, b + 1, presses])
		for a in n_div:
			for d in [Vector2.RIGHT, Vector2.LEFT, Vector2.UP, Vector2.DOWN]:
				kit.ok(n_div < 2 or nav.nav_target(a, d) >= 0, "board %d: every arrow leads somewhere from knob %d" % [bi + 1, a + 1])
	var mg := _instance(TUBE_SCENE)
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "berlin.rohrpost", "auto": false})
	mg._process(0.4)
	# two wrong capsules -> hint naming a knob
	_press(mg, KEY_ENTER)
	var guard := 0
	while mg._state != "ready" and guard < 400:
		mg._process(DT)
		guard += 1
	kit.eq(mg.logic.wrong, 1, "a wrong capsule comes back")
	_press(mg, KEY_ENTER)
	guard = 0
	while mg._state != "ready" and guard < 400:
		mg._process(DT)
		guard += 1
	kit.ok(mg.fails >= 2 and mg._hint_box.visible, "hint after two wrong capsules")
	# R puts the knobs back
	_press(mg, KEY_SPACE)
	kit.ne(mg.logic.states, [0, 1], "Space turned knob 1")
	_press(mg, KEY_R)
	kit.eq(mg.logic.states, [0, 1], "R puts the knobs of the board back")
	# play all three boards by keys
	for bi in 3:
		kit.eq(mg.logic.board_i, bi, "board %d" % (bi + 1))
		var need: Array = mg.logic.turns_needed()
		for di in need.size():
			var n := 0
			while mg.selected != di and n < 12:
				n += 1
				_press(mg, mg.nav_key_toward(mg.selected, di))
			kit.eq(mg.selected, di, "board %d: knob %d selected by arrows" % [bi + 1, di + 1])
			for t in int(need[di]):
				_press(mg, KEY_SPACE)
		kit.eq(mg.logic.turns_needed().reduce(func(a, b): return a + b, 0), 0, "board %d set" % (bi + 1))
		_press(mg, KEY_ENTER)
		kit.eq(mg._state, "travel", "board %d: the capsule is under way" % (bi + 1))
		guard = 0
		while mg._state == "travel" and guard < 600:
			mg._process(DT)
			guard += 1
		kit.eq(mg._state, "delivered", "board %d: delivered" % (bi + 1))
		kit.ok(mg.logic.delivered.has(bi), "board %d recorded" % (bi + 1))
		guard = 0
		while mg._state == "delivered" and not mg.solved and guard < 200:
			mg._process(DT)
			guard += 1
	kit.ok(mg.solved, "all three capsules: solved")
	for i in 80:
		mg._process(DT)
	kit.eq(got, [true], "finished(true) exactly once")
	return true


func _give_up() -> bool:
	for id in ENTRIES:
		var mg := _instance(ENTRIES[id]["scene"])
		var got: Array = []
		mg.finished.connect(func(ok: bool): got.append(ok))
		mg.open({"explore_id": id, "auto": false})
		mg._process(0.5)
		kit.ok(mg.handle_cancel(), "%s: Esc handled" % id)
		kit.eq(got, [false], "%s: giving up resolves without a find" % id)
		mg.handle_cancel()
		mg._process(3.0)
		kit.eq(got, [false], "%s: finished exactly once" % id)
	return true


func _click(mg: Node, pos: Vector2, pressed: bool, button := MOUSE_BUTTON_LEFT) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = button
	ev.pressed = pressed
	ev.position = pos
	mg.stage_input(ev)


## Mouse: hover + click on the chart writes a letter, holding the mouse on the key keys a dash; a click on a knob
## turns it, a right click turns it back.
func _mouse() -> bool:
	var mg := _instance(MORSE_SCENE)
	mg.open({"explore_id": "karsk.morse", "auto": false})
	mg.relayout()
	var guard := 0
	while not mg.logic.can_pick() and guard < 600:
		mg._process(DT)
		guard += 1
	var want := MorseLogic.table_index(str(mg.logic.letters[mg.logic.current_letter()]["ch"]))
	var c: Vector2 = mg._cell_rect(want).get_center()
	var mm := InputEventMouseMotion.new()
	mm.position = c
	mg.stage_input(mm)
	kit.eq(mg.cursor, MorseLogic.cell_of(want), "hovering a field moves the cursor there")
	_click(mg, c, true)
	_click(mg, c, false)
	kit.eq(mg.logic.cursor, 1, "a click on the right field writes the letter")
	# straight to the receipt: decode the rest by logic, then hold the mouse on the key
	while mg.logic.phase == "decode" and guard < 3000:
		guard += 1
		if mg.logic.can_pick():
			mg.logic.pick(str(mg.logic.letters[mg.logic.current_letter()]["ch"]))
		else:
			mg._process(DT)
	mg._process(DT)
	var kc: Vector2 = mg._key_rect().get_center()
	_click(mg, kc, true)
	kit.ok(mg._press_t >= 0.0, "pressing the mouse on the key presses the key")
	mg._process(0.1)
	_click(mg, kc + Vector2(300, 0), false)
	kit.ok(mg._press_t < 0.0 and mg.logic.ack_confirmed() == 1, "releasing anywhere ends the press: one dot keyed")
	var tb := _instance(TUBE_SCENE)
	tb.open({"explore_id": "berlin.rohrpost", "auto": false})
	tb.relayout()
	tb._process(0.4)
	var k2: Vector2 = tb._art(tb._div_pos(1))
	_click(tb, k2, true)
	kit.eq(tb.selected, 1, "a click selects the knob")
	kit.eq(tb.logic.states, [0, 2], "and turns it on")
	_click(tb, k2, true, MOUSE_BUTTON_RIGHT)
	kit.eq(tb.logic.states, [0, 1], "a right click turns it back")
	return true


## At the normal text size the telegram form lies on the desk below the register (the tape stays visible); larger
## text pulls it up over the register before anything shrinks; it never needs more than the tall place.
func _form_layout() -> bool:
	var st: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Settings")
	if not kit.ok(st != null, "Settings autoload present"):
		return true
	var keep = st.values.get("text_scale", 1.0)
	var mg := _instance(MORSE_SCENE)
	for ts in [1.0, 1.25, 1.5]:
		st.values["text_scale"] = ts
		for p in [3, 2]:
			mg._px = p
			mg._tall_form = false
			var need: float = mg._form_height(ts)
			var normal: float = mg._form_rect().size.y
			mg._tall_form = true
			var tall: float = mg._form_rect().size.y
			if ts == 1.0 and p == 3:
				kit.ok(need <= normal, "100 %% text at x3: the form fits below the register (%.0f <= %.0f)" % [need, normal])
			kit.ok(need <= tall, "%d %% text at x%d: the tall form holds it (%.0f <= %.0f)" % [int(ts * 100), p, need, tall])
	st.values["text_scale"] = keep
	return true


## Settings "puzzle_hints": 0 = never, 1 = after two refusals (default), 2 = at once.
func _hint_setting() -> bool:
	var st: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Settings")
	if not kit.ok(st != null and "values" in st, "Settings autoload present"):
		return true
	var keep = st.values.get("puzzle_hints", 1)
	for id in ENTRIES:
		st.values["puzzle_hints"] = 2
		var a := _instance(ENTRIES[id]["scene"])
		a.open({"explore_id": id, "auto": false})
		kit.ok(a._hint_box.visible, "%s: puzzle_hints 2 shows the hint at once" % id)
		st.values["puzzle_hints"] = 0
		var b := _instance(ENTRIES[id]["scene"])
		b.open({"explore_id": id, "auto": false})
		b._process(0.4)
		for i in 3:
			b.register_fail("x")
		kit.ok(not b._hint_box.visible and b.fails == 3, "%s: puzzle_hints 0 never shows a hint" % id)
		st.values["puzzle_hints"] = 1
		var c := _instance(ENTRIES[id]["scene"])
		c.open({"explore_id": id, "auto": false})
		c._process(0.4)
		c.register_fail("x")
		kit.ok(not c._hint_box.visible, "%s: default: no hint after one refusal" % id)
		c.register_fail("x")
		kit.ok(c._hint_box.visible, "%s: default: hint after two refusals" % id)
	st.values["puzzle_hints"] = keep
	return true


func _demo_source() -> bool:
	for path in [MORSE_GAME, TUBE_GAME]:
		var src := FileAccess.get_file_as_string(path)
		kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "%s extends minigame_base.gd" % path.get_file())
		var body := src.substr(src.find("# ================================================================ synthetic solve"))
		kit.ok(body.contains("func demo_solve") and (body.contains("_key_event(") or body.contains("_tap(")),
			"%s: demo_solve sends synthetic key events" % path.get_file())
		for banned in ["logic.pick(", "logic.key(", "logic.turn(", "logic.send(", "mark_solved(", "_finish(", "logic.states[",
				"logic.next_board(", "_pick(", "turn_selected(", "send_capsule(", "_key_press(", "_key_release("]:
			kit.ok(not _calls(body, banned), "%s: demo_solve never calls %s" % [path.get_file(), banned])
	return true


## `token` occurs in `src` as a call of its own (not as the tail of a longer name, e.g. can_pick( for _pick().
static func _calls(src: String, token: String) -> bool:
	var at := src.find(token)
	while at >= 0:
		var prev := src.substr(at - 1, 1) if at > 0 else " "
		if not (prev.to_lower() != prev.to_upper() or prev == "_" or prev.is_valid_int()):
			return true
		at = src.find(token, at + 1)
	return false


# ================================================================ data
func _sentences(s: String) -> int:
	var re := RegEx.new()
	re.compile("[.!?…][“”\"‘’]?(\\s|$)")
	return re.search_all(s).size()


func _data() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary and d.get("entries") is Array, "minigames_r7_kb.json parses"):
		return true
	kit.ok(str(d.get("area", "")) != "", "file has an area name")
	var ex: Node = kit.track(load("res://scripts/core/explore.gd").new())
	ex.print_warnings = false
	ex.reload()
	var seen := {}
	for e in d["entries"]:
		var id := str(e.get("id", ""))
		seen[id] = true
		if not kit.ok(ENTRIES.has(id), "entry %s is one of ours" % id):
			continue
		var spec: Dictionary = ENTRIES[id]
		kit.eq(str(e.get("kind", "")), "detail", "%s kind" % id)
		kit.eq(str(e.get("area", "")), spec["area"], "%s is listed with %s" % [id, spec["area"]])
		kit.eq(str(e.get("level", "")), spec["level_id"], "%s level" % id)
		kit.eq(str(e.get("minigame", "")), spec["scene"], "%s opens its mini-game" % id)
		kit.ok(ResourceLoader.exists(spec["scene"]), "%s scene exists" % id)
		kit.ok((e.get("history", []) as Array).is_empty(), "%s links no history card" % id)
		var img := str(e.get("image", ""))
		var im := Image.load_from_file(ProjectSettings.globalize_path(img)) if FileAccess.file_exists(img) else null
		if kit.ok(im != null and not im.is_empty(), "%s close-up %s loads" % [id, img]):
			kit.ok(im.get_width() <= 320 and im.get_height() <= 200 and im.get_width() >= 160, "%s close-up %s fits" % [id, im.get_size()])
		kit.ok(not FileAccess.file_exists(img.get_basename() + "_hist.png"), "%s: no insignia variant" % id)
		var title: String = loc.t(str(e.get("title_key", "")))
		var prompt: String = loc.t(str(e.get("prompt_key", "")))
		var text: String = loc.t(str(e.get("text_key", "")))
		kit.ok(title.length() >= 3 and title.length() <= 32, "%s title '%s'" % [id, title])
		kit.ok(prompt.length() >= 5 and prompt.length() <= 32, "%s prompt '%s'" % [id, prompt])
		kit.ok(text.length() >= 250 and text.length() <= 520, "%s find text fits the notebook page (%d)" % [id, text.length()])
		kit.ok(_sentences(text) >= 1 and _sentences(text) <= 4, "%s: 1-4 sentences (%d)" % [id, _sentences(text)])
		kit.ok(ex.has_entry(id) and str(ex.entry(id).get("area", "")) == spec["area"], "Explore loads %s into %s" % [id, spec["area"]])
		var found_in_level := false
		for le in ex.entries_for(spec["level_id"]):
			if str(le["id"]) == id:
				found_in_level = true
		kit.ok(found_in_level, "Explore counts %s for %s" % [id, spec["level_id"]])
		for w in ex.warnings:
			kit.ok(not str(w).contains(id), "no Explore warning about %s (%s)" % [id, w])
	kit.eq(seen.size(), ENTRIES.size(), "exactly our two entries")
	return true


func _loc_keys() -> bool:
	var f = _json(STRINGS)
	if not kit.ok(f is Dictionary and f.get("strings") is Dictionary, "de_minigames_r7_kb.json parses"):
		return true
	kit.eq(str(f.get("locale", "")), "de-DE", "locale tag")
	var strings: Dictionary = f["strings"]
	var used := {}
	var re := RegEx.new()
	re.compile("\"((mg\\.(morse|tube)|explore\\.(karsk|berlin))\\.[a-z0-9_.]+[a-z0-9_])\"")
	for path in SCRIPTS + [DATA, TUBE_LAYOUT]:
		for m in re.search_all(FileAccess.get_file_as_string(path)):
			used[m.get_string(1)] = true
	for k in ["mg.morse.fail.dot", "mg.morse.fail.dash"]:
		used[k] = true
	var lg = TubeLogic.new()
	for b in lg.boards:
		for s in b.get("stations", []):
			used["mg.tube.station." + str(s["id"])] = true
			if str(s["id"]) != str(b.get("target", "")):
				used["mg.tube.fail." + str(s["id"])] = true
	for key in used:
		kit.ok(strings.has(key), "string %s exists" % key)
		if strings.has(key):
			kit.ok(str(loc.source_of(key)).ends_with("de_minigames_r7_kb.json"), "%s is not overridden elsewhere" % key)
	for key in strings:
		kit.ok(used.has(key), "string %s is used" % key)
		var s := str(strings[key])
		kit.ok(s.strip_edges() == s and s != "", "%s is clean" % key)
		kit.ok(not s.contains("!") and not s.contains("\""), "%s is calm and uses German quotes" % key)
		kit.ok(str(key).begins_with("mg.morse.") or str(key).begins_with("mg.tube.") or str(key) in used,
			"%s lives in our namespaces" % key)
	# the old protagonist name must never appear in anything this area writes
	var old := "Matth" + "ias"
	for path in SCRIPTS + [DATA, STRINGS, "res://tools/pixelgen/gen_mg_morse.py", "res://tools/pixelgen/gen_mg_rohrpost.py",
			"res://tools/pixelgen/mg_r7_kb_lib.py", "res://tools/audiogen/mg_audio_r7_kb.py"]:
		kit.ok(not FileAccess.get_file_as_string(path).contains(old), "%s is free of the old name" % path.get_file())
	return true


func _art() -> bool:
	var sizes := {
		"res://assets/ui/minigames/morse/morse_desk.png": Vector2i(900, 432),
		"res://assets/ui/minigames/morse/morse_table.png": Vector2i(666, 432),
		"res://assets/ui/minigames/morse/morse_sounder.png": Vector2i(240, 90),
		"res://assets/ui/minigames/morse/morse_key.png": Vector2i(324, 72),
		"res://assets/ui/minigames/morse/morse_lamp.png": Vector2i(120, 60),
		"res://assets/ui/minigames/morse/morse_tape.png": Vector2i(144, 18),
		"res://assets/ui/minigames/morse/find_telegram.png": Vector2i(300, 190),
		"res://assets/ui/minigames/rohrpost/rohrpost_board_1.png": Vector2i(858, 426),
		"res://assets/ui/minigames/rohrpost/rohrpost_board_2.png": Vector2i(858, 426),
		"res://assets/ui/minigames/rohrpost/rohrpost_board_3.png": Vector2i(858, 426),
		"res://assets/ui/minigames/rohrpost/rohrpost_knob.png": Vector2i(324, 54),
		"res://assets/ui/minigames/rohrpost/rohrpost_capsule.png": Vector2i(72, 36),
		"res://assets/ui/minigames/rohrpost/rohrpost_lamp.png": Vector2i(48, 24),
		"res://assets/ui/minigames/rohrpost/find_capsules.png": Vector2i(300, 180),
	}
	for p in sizes:
		var im := Image.load_from_file(ProjectSettings.globalize_path(p)) if FileAccess.file_exists(p) else null
		if kit.ok(im != null and not im.is_empty(), "%s exists" % p.get_file()):
			kit.eq(im.get_size(), sizes[p], "%s size" % p.get_file())
		kit.ok(ResourceLoader.exists(p), "%s is imported" % p.get_file())
		kit.ok(not FileAccess.file_exists(p.get_basename() + "_hist.png"), "%s: no insignia variant" % p.get_file())
	var ml = _json(MORSE_LAYOUT)
	if kit.ok(ml is Dictionary, "morse_layout.json parses"):
		var tbl: Array = ml.get("table", [])
		kit.eq(tbl.size(), MorseLogic.TABLE.size(), "the chart art has a cell for every sign")
		for i in mini(tbl.size(), MorseLogic.TABLE.size()):
			kit.ok(str(tbl[i][0]) == str(MorseLogic.TABLE[i][0]) and str(tbl[i][1]) == str(MorseLogic.TABLE[i][1]),
				"chart cell %d agrees with the logic (%s)" % [i, MorseLogic.TABLE[i][0]])
		var g: Array = ml.get("table_grid", [])
		kit.ok(g.size() == 4 and float(g[0]) + 7 * float(g[2]) <= float(ml["table_size"][0])
			and float(g[1]) + 6 * float(g[3]) <= float(ml["table_size"][1]), "the 7 x 6 grid fits the chart")
		var f: Array = ml.get("form", [])
		kit.ok(f.size() == 4 and float(f[2]) <= float(ml["desk_size"][0]) and float(f[3]) <= float(ml["desk_size"][1]),
			"the telegram form lies on the desk")
	var tl = _json(TUBE_LAYOUT)
	if kit.ok(tl is Dictionary, "rohrpost_layout.json parses"):
		kit.eq((tl.get("boards", []) as Array).size(), 3, "three boards in the layout")
		kit.eq(tl.get("knob_frames", []), ["WE", "NS", "NE", "ES", "SW", "WN"], "knob frames")
		for b in tl.get("boards", []):
			for dv in b.get("diverters", []):
				for p2 in dv.get("states", []):
					kit.ok(str(p2) in tl["knob_frames"], "board %s: knob state %s has a frame" % [b["id"], p2])
			for key in [str(b.get("note", "")), str(b.get("content", ""))]:
				kit.ok(loc.has(key), "board %s text %s exists" % [b["id"], key])
	return true


func _wav_info(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var b := f.get_buffer(f.get_length())
	var info := {"riff": b.slice(0, 4).get_string_from_ascii(), "wave": b.slice(8, 12).get_string_from_ascii()}
	var i := 12
	while i + 8 <= b.size():
		var id := b.slice(i, i + 4).get_string_from_ascii()
		var n := b.decode_u32(i + 4)
		if id == "fmt ":
			info["format"] = b.decode_u16(i + 8)
			info["channels"] = b.decode_u16(i + 10)
			info["rate"] = b.decode_u32(i + 12)
			info["bits"] = b.decode_u16(i + 22)
		elif id == "data":
			info["frames"] = n / 2
		elif id == "smpl":
			info["loop"] = true
		i += 8 + n + (n % 2)
	return info


func _audio() -> bool:
	var loops := ["mg_morse_inker", "mg_tube_rush"]
	for n in ["mg_morse_down", "mg_morse_up", "mg_morse_key_down", "mg_morse_key_up", "mg_morse_bell", "mg_morse_inker",
			"mg_tube_turn", "mg_tube_bell", "mg_tube_send", "mg_tube_rush", "mg_tube_arrive", "mg_tube_stuck"]:
		var p := "res://assets/audio/sfx/%s.wav" % n
		var info := _wav_info(p)
		if not kit.ok(not info.is_empty(), "%s exists" % n):
			continue
		kit.ok(info["riff"] == "RIFF" and info["wave"] == "WAVE", "%s is a WAV" % n)
		kit.ok(int(info.get("format", 0)) == 1 and int(info.get("channels", 0)) == 1 and int(info.get("rate", 0)) == 44100
			and int(info.get("bits", 0)) == 16, "%s: 44.1 kHz 16-bit mono PCM" % n)
		var secs := float(info.get("frames", 0)) / 44100.0
		kit.ok(secs > 0.05 and secs < 3.0, "%s length %.2f s" % [n, secs])
		kit.eq(bool(info.get("loop", false)), n in loops, "%s loop flag" % n)
		kit.ok(ResourceLoader.exists(p), "%s is imported" % n)
	return true


# ================================================================ placement
func _placement() -> bool:
	for id in ENTRIES:
		var spec: Dictionary = ENTRIES[id]
		var env: String = spec["env"]
		var extra = _json(env + "explore_hotspots.json")
		var art = _json(env + "scene.json")
		if not kit.ok(extra is Dictionary and art is Dictionary, "%s: hotspot files parse" % id):
			continue
		var hs: Dictionary = (extra.get("hotspots", {}) as Dictionary).duplicate()
		for k in art.get("hotspots", {}):
			hs[k] = art["hotspots"][k]
		var hid: String = spec["hotspot"]
		kit.ok((extra.get("hotspots", {}) as Dictionary).has(hid), "%s is content-owned (explore_hotspots.json)" % hid)
		kit.ok(not (art.get("hotspots", {}) as Dictionary).has(hid), "%s does not clash with the art manifest" % hid)
		if not kit.ok(hs.has(hid), "%s exists" % hid):
			continue
		var p := Vector2(float(hs[hid][0]), float(hs[hid][1]))
		var walk := PackedVector2Array()
		for q in art.get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		kit.ok(walk.size() < 3 or Geometry2D.is_point_in_polygon(p, walk), "%s %s inside the walkable area" % [hid, p])
		for pr in art.get("props", []):
			if pr is Dictionary and pr.get("collision", []) is Array and (pr.get("collision", []) as Array).size() >= 3:
				var poly := PackedVector2Array()
				for q in pr["collision"]:
					poly.append(Vector2(float(q[0]), float(q[1])))
				kit.ok(not Geometry2D.is_point_in_polygon(p, poly), "%s outside the collision of %s" % [hid, pr.get("name", "")])
		for k in hs:
			if k == hid:
				continue
			var q2 := Vector2(float(hs[k][0]), float(hs[k][1]))
			var dv := p - q2
			if spec["oblique"]:
				dv.y *= 1.6
			var dist := dv.length()
			if str(k) in spec["story"]:
				kit.ok(dist >= MIN_STORY, "%s keeps %d px from story spot %s (%.1f)" % [hid, int(MIN_STORY), k, dist])
			elif str(k) in MINIGAME_SPOTS:
				kit.ok(dist >= MIN_MINIGAME, "%s keeps %d px from mini-game spot %s (%.1f)" % [hid, int(MIN_MINIGAME), k, dist])
			elif str(k).begins_with("exp_"):
				kit.ok(dist >= float(spec["min_find"]), "%s keeps %d px from %s (%.1f)" % [hid, int(spec["min_find"]), k, dist])
		# the Interactable (exactly one, under Playfield)
		var st: SceneState = (load(spec["level"]) as PackedScene).get_state()
		var count := 0
		var ok := false
		for i in st.get_node_count():
			var props := {}
			var script_path := ""
			for j in st.get_node_property_count(i):
				var pn := str(st.get_node_property_name(i, j))
				var pv = st.get_node_property_value(i, j)
				if pn == "script" and pv is Script:
					script_path = (pv as Script).resource_path
				else:
					props[pn] = pv
			if str(props.get("explore_id", "")) != id:
				continue
			count += 1
			ok = str(st.get_node_name(i)) == spec["node"] and script_path == "res://scripts/actors/interactable.gd" \
				and str(props.get("kind", "")) == "discover" and str(props.get("hotspot_id", "")) == hid \
				and str(st.get_node_path(i, true)).ends_with("Playfield")
			if not spec["oblique"]:
				var feet_y := float(art.get("spawns", {}).get("SP_M1_Office", [0, 300])[1])
				kit.ok(absf(p.y - feet_y) < float(props.get("radius", 30.0)) - 1.0, "%s reachable from the feet line" % hid)
		kit.eq(count, 1, "%s is placed by exactly one Interactable" % id)
		kit.ok(ok, "%s: Interactable %s (discover, %s, interactable.gd, under Playfield)" % [id, spec["node"], hid])
	return true
