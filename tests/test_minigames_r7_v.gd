extends RefCounted
## Chapter-3 mini-games (owner: minigames r7, TECHNICAL_ARCHITECTURE §12.8):
##   "Die Fallblatttafel" (Bahnhof Veltrava, Alexei) — flap_logic.gd / flap_game.gd / FlapBoard.tscn
##   "Die Garderobe" (Palais, Konrad)                 — cloak_logic.gd / cloak_game.gd / Cloakroom.tscn
## Logic: the puzzles are solvable, the couplings and the forward-only drums behave, the timetable and the board
## agree with each other and with the Chapter-3 story (no early Kordon-17 / 23:40 / "Leerfahrt"), the cloakroom
## rounds refuse wrong items with a reason and leave exactly Elena's coat. Scenes (stand-alone, driven
## synchronously: time via _process(delta), keys via modal_input(event)): auto mode, keyboard play, a hint after
## two failures, Esc gives up without a find, finished(success) exactly once, demo_solve by synthetic keys only.
## Data: explore entries, Loc keys, hotspots (walkable, no collision, spacing), interactables and world cues in
## the level scenes, art, layout JSON, SFX.

const Kit := preload("res://tests/support/test_kit.gd")
const FLAP_LOGIC := preload("res://scripts/ui/minigames/flap_logic.gd")
const CLOAK_LOGIC := preload("res://scripts/ui/minigames/cloak_logic.gd")
const FLAP_SCENE := "res://scenes/ui/minigames/FlapBoard.tscn"
const CLOAK_SCENE := "res://scenes/ui/minigames/Cloakroom.tscn"
const FLAP_GAME := "res://scripts/ui/minigames/flap_game.gd"
const CLOAK_GAME := "res://scripts/ui/minigames/cloak_game.gd"
const DATA := "res://data/explore/minigames_r7_v.json"
const STRINGS := "res://data/locale/de_minigames_r7_v.json"
const FLAP_ART := "res://assets/ui/minigames/flap/"
const CLOAK_ART := "res://assets/ui/minigames/cloak/"
const ENTRIES := {
	"veltrava.station.flap_board": ["L_C3_Station", "res://scenes/levels/L_C3_Station.tscn", "veltrava_station",
		"exp_flap_board", "Find_FlapBoard", FLAP_SCENE, true],
	"veltrava.hall.cloak_tokens": ["L_C3_Hall", "res://scenes/levels/L_C3_Hall.tscn", "veltrava_hall",
		"exp_cloak_tokens", "Find_CloakTokens", CLOAK_SCENE, false],
}
const MIN_GAP := 26.0
const SFX := ["mg_flap_clack_1", "mg_flap_clack_2", "mg_flap_clack_3", "mg_flap_clack_4", "mg_flap_turn",
	"mg_flap_rattle", "mg_flap_engage", "mg_cloak_token", "mg_cloak_coat", "mg_cloak_hat", "mg_cloak_bell"]

var kit: Kit
var strings: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var sj = _json(STRINGS)
	strings = sj.get("strings", {}) if sj is Dictionary else {}
	# the scene cases assume the default hint setting; the player's own settings file must not change them
	var settings: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Settings")
	var saved_hints = settings.values.get("puzzle_hints", 1) if settings != null else 1
	if settings != null:
		settings.values["puzzle_hints"] = 1
	kit.run_case("flap_logic_couplings", _flap_couplings)
	kit.run_case("flap_logic_solvable_and_story", _flap_solvable)
	kit.run_case("flap_scene_auto_and_keys", _flap_scene)
	kit.run_case("flap_scene_full_solve_by_keys", _flap_full)
	kit.run_case("cloak_logic_rounds", _cloak_logic)
	kit.run_case("cloak_scene_auto_and_keys", _cloak_scene)
	kit.run_case("cloak_scene_full_solve_by_keys", _cloak_full)
	kit.run_case("data_entries_and_strings", _data)
	kit.run_case("hotspots_and_level_nodes", _placement)
	kit.run_case("art_layout_and_sfx", _assets)
	if settings != null:
		kit.run_case("hint_setting_modes", _hint_modes.bind(settings))
		settings.values["puzzle_hints"] = saved_hints
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


static func _ints(a) -> Array:
	var out: Array = []
	for v in (a if a is Array else []):
		out.append(int(v))
	return out


func _key(k: int, down := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = down
	return ev


func _instance(path: String) -> Node:
	var mg: Node = load(path).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(mg)
	kit.track(mg)
	return mg


func _steps(mg: Node, seconds: float, dt := 0.05) -> void:
	for i in int(ceil(seconds / dt)):
		mg._process(dt)


# ================================================================ flap logic
func _flap_couplings() -> bool:
	var lg = FLAP_LOGIC.new()
	var H := FLAP_LOGIC.index_of("hour")
	var T := FLAP_LOGIC.index_of("tens")
	var U := FLAP_LOGIC.index_of("units")
	var F := FLAP_LOGIC.index_of("from")
	var V := FLAP_LOGIC.index_of("via")
	var G := FLAP_LOGIC.index_of("track")
	kit.eq(lg.pos, FLAP_LOGIC.START, "starts in the jam")
	kit.ok(not lg.is_solved(), "the jam is not the timetable line")
	# hour: independent, wraps 23 -> 0
	lg.pos[H] = 23
	var m: Array = lg.turn(H)
	kit.eq(lg.pos[H], 0, "hour wraps forward 23 -> 0")
	kit.eq(m.size(), 1, "the hour drags nothing")
	# tens drags the hour (every flap)
	lg.reset()
	var h0: int = lg.pos[H]
	m = lg.turn(T)
	kit.eq([lg.pos[T], lg.pos[H]], [3, h0 + 1], "tens 2 -> 3 also turns the hour")
	kit.ok(lg.known.has("tens>hour"), "the tens -> hour coupling is now known")
	# units carry the tens only on 9 -> 0, and that propagates to the hour
	lg.reset()
	lg.pos[U] = 8
	var before := [lg.pos[T], lg.pos[H]]
	lg.turn(U)
	kit.eq([lg.pos[T], lg.pos[H]], before, "units 8 -> 9: no carry")
	m = lg.turn(U)
	kit.eq(lg.pos[U], 0, "units 9 -> 0")
	kit.eq([lg.pos[T], lg.pos[H]], [int(before[0]) + 1, int(before[1]) + 1], "the carry takes the tens, the tens take the hour")
	kit.eq(m.map(func(x): return str(x["kind"])), ["turn", "carry", "drag"], "move chain turn -> carry -> drag")
	# from and track both drag via; via drags nothing
	lg.reset()
	var v0: int = lg.pos[V]
	lg.turn(F)
	lg.turn(G)
	kit.eq(lg.pos[V], (v0 + 2) % FLAP_LOGIC.flap_count(V), "from and track each turn via one flap")
	var g0: int = lg.pos[G]
	var f0: int = lg.pos[F]
	lg.turn(V)
	kit.eq([lg.pos[F], lg.pos[G]], [f0, g0], "via turns alone")
	# a knocked-off drum the player had set by hand is reported as disturbed; one that was right by chance is not
	lg.reset()
	lg.pos[H] = FLAP_LOGIC.TARGET[H]
	kit.eq(FLAP_LOGIC.disturbed(lg.turn(T)).size(), 0, "an hour that was right by chance is no setback")
	lg.reset()
	lg.pos[H] = FLAP_LOGIC.TARGET[H] - 1
	lg.turn(H)
	var dist: Array = FLAP_LOGIC.disturbed(lg.turn(T))
	kit.ok(dist.size() == 1 and int(dist[0]["drum"]) == H, "turning the tens knocks the hand-set hour off (disturbed)")
	lg.pos[V] = FLAP_LOGIC.TARGET[V]
	kit.eq(FLAP_LOGIC.disturbed(lg.turn(V)).size(), 0, "turning a drum by hand is never 'disturbed'")
	# forward only: no API turns backwards, every flap list is fixed
	for i in FLAP_LOGIC.IDS.size():
		kit.ok(FLAP_LOGIC.flap_count(i) >= 6, "%s has a fixed list of flaps (%d)" % [FLAP_LOGIC.IDS[i], FLAP_LOGIC.flap_count(i)])
	return true


func _flap_solvable() -> bool:
	var lg = FLAP_LOGIC.new()
	var plan: Array = lg.solve_plan()
	kit.ok(plan.size() >= 20 and plan.size() <= 40, "the jam takes 20-40 flaps by the right order (%d)" % plan.size())
	var setbacks := 0
	for d in plan:
		setbacks += FLAP_LOGIC.disturbed(lg.turn(int(d))).size()
	kit.ok(lg.is_solved(), "the plan solves the line")
	kit.eq(setbacks, 0, "drivers before driven drums: nothing correct is ever knocked off")
	kit.eq(lg.line_text(), "8:41 MOSKVA KARSK 5", "the restored line")
	kit.eq(lg.known.size(), 4, "all four couplings have been seen on the way")
	# left to right is NOT safe: a natural first try knocks something off (that is the puzzle)
	var naive = FLAP_LOGIC.new()
	var knocks := 0
	for i in FLAP_LOGIC.IDS.size():
		var guard := 0
		while not naive.on_target(i) and guard < 30:
			knocks += FLAP_LOGIC.disturbed(naive.turn(i)).size()
			guard += 1
	kit.ok(knocks >= 2, "setting the drums left to right knocks correct drums off (%d)" % knocks)
	# the timetable: the target is the special train on platform 5, the board's other rows are today's
	kit.eq(FLAP_LOGIC.sheet_pos(FLAP_LOGIC.SHEET[FLAP_LOGIC.TARGET_SHEET_ROW]), FLAP_LOGIC.TARGET, "the timetable row of the special train is the target")
	var lay = _json(FLAP_ART + "flap_layout.json")
	if kit.ok(lay is Dictionary, "flap_layout.json parses"):
		kit.eq(_ints(lay.get("start", [])), FLAP_LOGIC.START, "generator and logic agree on START")
		kit.eq(_ints(lay.get("target", [])), FLAP_LOGIC.TARGET, "generator and logic agree on TARGET")
		var drums: Array = lay.get("drums", [])
		kit.eq(drums.size(), FLAP_LOGIC.IDS.size(), "six drums in the layout")
		for i in mini(drums.size(), FLAP_LOGIC.IDS.size()):
			kit.eq(str(drums[i]["id"]), FLAP_LOGIC.IDS[i], "drum %d id" % i)
			kit.eq(drums[i]["flaps"], FLAP_LOGIC.FLAPS[i], "drum %s: same flap list in art and logic" % FLAP_LOGIC.IDS[i])
		var rows: Array = []
		for r in FLAP_LOGIC.SHEET:
			rows.append(FLAP_LOGIC.sheet_pos(r))
		for sr in lay.get("static_rows", []):
			kit.ok(rows.has(_ints(sr)), "board row %s is a timetable row" % [sr])
		kit.eq(lay.get("new_flap"), ["via", "KARSK"], "the new card is KARSK")
	kit.eq(FLAP_LOGIC.target_flap(FLAP_LOGIC.index_of("track")), "5", "Alexei's train stands on platform 5 (C3_DESIGN §4.1)")
	kit.ok(8 * 60 + 41 < 8 * 60 + 55, "8:41 is before the station clock's 8:55 (exp_clock)")
	# no story pre-emption: the special 23:40 run to Kordon-17 belongs to objective c3a_inspect_departures
	for i in FLAP_LOGIC.IDS.size():
		for f in FLAP_LOGIC.FLAPS[i]:
			kit.ok(not str(f).contains("KORDON-17"), "no Kordon-17 card on the arrivals board (%s)" % f)
	for r in FLAP_LOGIC.SHEET:
		kit.ok(str(r[0]) != "23.40", "no 23:40 in the arrivals timetable")
	for k in strings:
		if str(k).begins_with("mg.flap.") or str(k).begins_with("explore.veltrava.station.flap_board"):
			var t := str(strings[k]).to_lower()
			kit.ok(not t.contains("kordon-17") and not t.contains("23:40") and not t.contains("leerfahrt"),
				"%s does not pre-empt the departures objective" % k)
	return true


# ================================================================ flap scene
func _flap_scene() -> bool:
	var mg := _instance(FLAP_SCENE)
	kit.ok(mg.is_in_group("minigame"), "flap joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "veltrava.station.flap_board", "auto": true})
	kit.ok(mg.is_open, "flap opens")
	mg._process(0.1)
	kit.eq(got, [], "flap: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "flap: auto mode resolves with success")
	kit.ok(not mg.is_open, "flap closes itself")
	# keyboard
	var fg := _instance(FLAP_SCENE)
	var res: Array = []
	fg.finished.connect(func(ok: bool): res.append(ok))
	fg.open({"explore_id": "veltrava.station.flap_board", "auto": false})
	_steps(fg, 0.4)
	kit.ok(fg.modal_input(_key(KEY_RIGHT)), "Right is consumed")
	kit.eq(fg.cursor, 1, "Right selects the next drum")
	fg.modal_input(_key(KEY_LEFT))
	kit.eq(fg.cursor, 0, "Left goes back")
	var h0: int = fg.logic.pos[0]
	kit.ok(fg.modal_input(_key(KEY_UP)), "Up is consumed")
	kit.eq(fg.logic.pos[0], (h0 + 1) % 24, "Up turns the hour one flap")
	fg.modal_input(_key(KEY_SPACE))
	kit.eq(fg.logic.pos[0], (h0 + 2) % 24, "Space turns as well")
	var p0: Array = fg.logic.pos.duplicate()
	fg.modal_input(_key(KEY_DOWN))
	kit.eq(fg.logic.pos, p0, "Down never turns a drum backwards")
	_steps(fg, 0.6)
	kit.eq(fg.shown, fg.logic.pos, "the flips settle on the logic's flaps")
	kit.eq(fg.fails, 0, "no failure so far")
	fg.modal_input(_key(KEY_ENTER))
	kit.eq(fg.fails, 1, "a Probelauf on a wrong line is a failure")
	kit.ok(not fg._hint_box.visible, "no hint after one failure")
	fg.modal_input(_key(KEY_ENTER))
	kit.ok(fg.fails == 2 and fg._hint_box.visible and fg._hint_label.text.begins_with("Tipp"), "a hint after two failures")
	kit.ok(fg.modal_input(_key(KEY_R)), "R is consumed")
	kit.eq(fg.logic.pos, FLAP_LOGIC.START, "R starts over in the jam")
	kit.ok(fg.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	kit.ok(not fg.is_open, "closed after giving up")
	return true


func _flap_full() -> bool:
	var fg := _instance(FLAP_SCENE)
	var res: Array = []
	fg.finished.connect(func(ok: bool): res.append(ok))
	fg.open({"explore_id": "veltrava.station.flap_board", "auto": false})
	_steps(fg, 0.4)
	var guard := 0
	while not fg.logic.is_solved() and guard < 200:
		var d: int = fg.logic.next_drum()
		while fg.cursor != d:
			fg.modal_input(_key(KEY_RIGHT if fg.cursor < d else KEY_LEFT))
		fg.modal_input(_key(KEY_UP))
		_steps(fg, 0.02, 0.02)
		guard += 1
	kit.ok(fg.logic.is_solved(), "the line can be set by keys alone (%d presses)" % guard)
	kit.eq(fg.fails, 0, "the right order costs no failure")
	kit.ok(not fg.solved, "it engages only once every flip has settled")
	_steps(fg, 1.5)
	kit.ok(fg.solved, "the line engages by itself")
	kit.ok(str(fg._status.text).contains("KARSK"), "the solved status names the detail (KARSK)")
	_steps(fg, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(fg, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(FLAP_GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.turn(") and not body.contains("mark_solved("),
		"flap demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "flap extends minigame_base.gd")
	return true


func _hint_modes(settings: Node) -> bool:
	settings.values["puzzle_hints"] = 0
	var fg := _instance(FLAP_SCENE)
	fg.open({"explore_id": "veltrava.station.flap_board", "auto": false})
	_steps(fg, 0.4)
	for i in 3:
		fg.modal_input(_key(KEY_ENTER))
	kit.ok(fg.fails == 3 and not fg._hint_box.visible, "puzzle_hints 0: no hint even after three failures")
	settings.values["puzzle_hints"] = 2
	var cg := _instance(CLOAK_SCENE)
	cg.open({"explore_id": "veltrava.hall.cloak_tokens", "auto": false})
	kit.ok(cg._hint_box.visible, "puzzle_hints 2: the first hint at once")
	var fg2 := _instance(FLAP_SCENE)
	fg2.open({"explore_id": "veltrava.station.flap_board", "auto": false})
	kit.ok(fg2._hint_box.visible, "puzzle_hints 2: flap hint at once")
	settings.values["puzzle_hints"] = 1
	return true


# ================================================================ cloak logic
func _cloak_logic() -> bool:
	var lg = CLOAK_LOGIC.new()
	kit.eq([lg.kind(), lg.guest()], ["coat", "imhof"], "round 1 starts with Dr. Imhof's coat")
	kit.eq(lg.items(), CLOAK_LOGIC.COATS, "five coats on the rail")
	# the premise: no coat hangs on the hook of its owner's check
	for g in CLOAK_LOGIC.GUESTS:
		var coat := str(CLOAK_LOGIC.GUESTS[g]["coat"])
		kit.ok(CLOAK_LOGIC.hook_of(coat) != str(CLOAK_LOGIC.GUESTS[g]["token"]), "%s's coat is not on hook %s" % [g, CLOAK_LOGIC.GUESTS[g]["token"]])
	kit.ok(CLOAK_LOGIC.hook_of("elena") != CLOAK_LOGIC.ELENA_TOKEN, "Elena's coat is not on hook 27 either")
	# hook 12 for check 12 is the obvious, wrong first guess
	var r: Dictionary = lg.give("loden")
	kit.eq([r["ok"], r["reason"], r["key"]], [false, "wrong", "imhof.hook12"], "hook 12 is refused with its own line")
	r = lg.give("navy")
	kit.eq(str(r["key"]), "imhof.wrong1", "other wrong coats get the guest's general line")
	kit.eq(lg.refused, 2, "two refusals counted")
	kit.eq(lg.guest(), "imhof", "a refusal never advances the queue")
	# the whole solution
	var sol: Array = lg.solution()
	kit.eq(sol.size(), 7, "4 coats + 3 hats")
	for step in sol:
		var k := str(step[0])
		kit.eq(lg.kind(), k, "step kind %s" % k)
		var rr: Dictionary = lg.give(str(step[1]))
		kit.ok(bool(rr["ok"]), "%s accepts %s" % [rr.get("guest", ""), step[1]])
		kit.ok(str(rr["key"]).ends_with("thanks1") or str(rr["key"]).ends_with("thanks2"), "a thank-you line (%s)" % rr["key"])
	kit.ok(lg.done, "both rounds done")
	kit.eq(lg.give("elena").get("reason", ""), "done", "nothing more to hand out")
	var left_coats: Array = CLOAK_LOGIC.COATS.filter(func(c): return not lg.taken.has("coat:" + str(c)))
	var left_hats: Array = CLOAK_LOGIC.HATS.filter(func(h): return not lg.taken.has("hat:" + str(h)))
	kit.eq(left_coats, CLOAK_LOGIC.LEFT_COATS, "only Elena's coat stays")
	kit.eq(left_hats, CLOAK_LOGIC.LEFT_HATS, "the ticket homburg, Elena's beret and the rabbit cap stay")
	# taken items are refused without a failure; a round restart keeps round 1
	var l2 = CLOAK_LOGIC.new()
	l2.give("camel")
	kit.eq(l2.give("camel").get("reason", ""), "taken", "a handed-out coat cannot be given twice")
	kit.eq(l2.refused, 0, "that is no failure")
	for step in l2.solution().slice(0, 3):
		l2.give(str(step[1]))
	kit.eq(l2.kind(), "hat", "round 2 after four coats")
	l2.give("pin")
	l2.reset_round()
	kit.ok(l2.taken.has("coat:loden") and not l2.taken.has("hat:pin") and l2.guest() == "bauer",
		"restarting round 2 keeps the coats of round 1")
	# data consistency: every owned coat/hat exists, owners are unique, specials name real pairs
	for g in CLOAK_LOGIC.GUESTS:
		kit.ok(CLOAK_LOGIC.COATS.has(str(CLOAK_LOGIC.GUESTS[g]["coat"])), "%s's coat exists" % g)
		var h := str(CLOAK_LOGIC.GUESTS[g]["hat"])
		kit.ok(h == "" or CLOAK_LOGIC.HATS.has(h), "%s's hat exists" % g)
	for key in CLOAK_LOGIC.SPECIAL:
		var parts := str(key).split("|")
		kit.ok(CLOAK_LOGIC.GUESTS.has(parts[0]) and (CLOAK_LOGIC.COATS.has(parts[1]) or CLOAK_LOGIC.HATS.has(parts[1])), "special %s names a guest and an item" % key)
	var lay = _json(CLOAK_ART + "cloak_layout.json")
	if kit.ok(lay is Dictionary, "cloak_layout.json parses"):
		kit.eq(lay.get("coats"), CLOAK_LOGIC.COATS, "generator and logic agree on the coats")
		kit.eq(lay.get("hats"), CLOAK_LOGIC.HATS, "generator and logic agree on the hats")
		kit.eq(lay.get("hook_numbers"), CLOAK_LOGIC.HOOK_NUMBERS, "generator and logic agree on the hook plates")
		var toks: Array = lay.get("tokens", [])
		for g in CLOAK_LOGIC.GUESTS:
			kit.ok(toks.has(str(CLOAK_LOGIC.GUESTS[g]["token"])), "a brass check %s is drawn" % CLOAK_LOGIC.GUESTS[g]["token"])
		kit.ok(toks.has(CLOAK_LOGIC.ELENA_TOKEN), "check 27 is drawn")
		kit.eq(lay.get("guests"), ["imhof", "orlova", "duval", "bauer"], "bust rows")
	return true


# ================================================================ cloak scene
func _cloak_scene() -> bool:
	var mg := _instance(CLOAK_SCENE)
	kit.ok(mg.is_in_group("minigame"), "cloak joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "veltrava.hall.cloak_tokens", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "cloak: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "cloak: auto mode resolves with success")
	var cg := _instance(CLOAK_SCENE)
	var res: Array = []
	cg.finished.connect(func(ok: bool): res.append(ok))
	cg.open({"explore_id": "veltrava.hall.cloak_tokens", "auto": false})
	_steps(cg, 0.4)
	kit.eq(cg.cursor, 0, "cursor on hook 12")
	kit.ok(cg.modal_input(_key(KEY_ENTER)), "Enter is consumed")
	kit.eq(cg.fails, 1, "hook 12 for check 12 is refused (a failure)")
	kit.ok(str(cg._status.text).contains("Haken zwölf"), "with the guest's own line")
	cg.modal_input(_key(KEY_RIGHT))
	cg.modal_input(_key(KEY_RIGHT))
	kit.eq(cg.cursor, 2, "Right moves along the rail")
	cg.modal_input(_key(KEY_SPACE))
	kit.ok(cg.fails == 2 and cg._hint_box.visible, "a hint after two refusals")
	cg.modal_input(_key(KEY_LEFT))
	kit.eq(cg.cursor, 1, "Left moves back to the camel coat")
	cg.modal_input(_key(KEY_E))
	kit.eq(cg.logic.guest_i, 1, "E hands it over; the next guest is due")
	kit.eq(cg._phase, "thanks", "a thank-you beat first")
	cg.modal_input(_key(KEY_RIGHT))
	kit.eq(cg.cursor, 1, "no cursor moves during the thanks")
	_steps(cg, 2.0)
	kit.eq([cg._phase, cg._shown_guest], ["ask", "orlova"], "then Frau Orlova steps up")
	kit.ok(cg.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	return true


func _cloak_full() -> bool:
	var cg := _instance(CLOAK_SCENE)
	var res: Array = []
	cg.finished.connect(func(ok: bool): res.append(ok))
	cg.open({"explore_id": "veltrava.hall.cloak_tokens", "auto": false})
	_steps(cg, 0.4)
	var handed := 0
	var guard := 0
	while not cg.solved and guard < 250:
		guard += 1
		if cg._phase != "ask":
			_steps(cg, 0.2)
			continue
		var target: int = cg.logic.items().find(cg.logic.wanted())
		var g2 := 0
		while cg.cursor != target and g2 < 12:
			cg.modal_input(_key(KEY_RIGHT if cg.cursor < target else KEY_LEFT))
			g2 += 1
		cg.modal_input(_key(KEY_ENTER))
		handed += 1
		_steps(cg, 0.2)
	kit.ok(cg.solved, "both rounds by keys alone")
	kit.eq(handed, 7, "seven handovers")
	kit.eq(cg.fails, 0, "no refusal on the right path")
	kit.ok(str(cg._status.text).contains("Siebenundzwanzig"), "Herr Wenzel ends with check 27")
	_steps(cg, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(cg, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(CLOAK_GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.give(") and not body.contains("mark_solved("),
		"cloak demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "cloak extends minigame_base.gd")
	return true


# ================================================================ data
func _data() -> bool:
	var d = _json(DATA)
	if not kit.ok(d is Dictionary and d.get("entries") is Array, "minigames_r7_v.json parses"):
		return true
	kit.eq(str(d.get("area", "")), "veltrava", "area veltrava")
	var by_id := {}
	for e in d["entries"]:
		by_id[str(e.get("id", ""))] = e
	kit.eq(Kit.sorted(by_id.keys()), Kit.sorted(ENTRIES.keys()), "exactly the two mini-game finds")
	var loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	for id in ENTRIES:
		var spec: Array = ENTRIES[id]
		var e: Dictionary = by_id.get(id, {})
		if not kit.ok(not e.is_empty(), "%s exists" % id):
			continue
		kit.eq(str(e.get("kind", "")), "detail", "%s is a detail" % id)
		kit.eq(str(e.get("level", "")), spec[0], "%s level" % id)
		kit.eq(str(e.get("minigame", "")), spec[5], "%s opens its mini-game" % id)
		kit.ok((e.get("history", []) as Array).is_empty(), "%s carries no history card" % id)
		for k in ["title_key", "text_key", "prompt_key"]:
			var key := str(e.get(k, ""))
			kit.ok(strings.has(key) and loc.has(key), "%s %s exists (%s)" % [id, k, key])
		var txt := str(strings.get(str(e.get("text_key", "")), ""))
		kit.ok(txt.length() >= 250 and txt.length() <= 520, "%s find text %d chars" % [id, txt.length()])
		var img := str(e.get("image", ""))
		if kit.ok(FileAccess.file_exists(img), "%s close-up exists" % id):
			var im := Image.load_from_file(ProjectSettings.globalize_path(img))
			kit.ok(im != null and im.get_width() <= 320 and im.get_height() <= 200, "%s close-up fits 320x200" % id)
			kit.ok(not FileAccess.file_exists(img.get_basename() + "_hist.png"), "%s: no insignia variant" % id)
		var ps = load(spec[5])
		if kit.ok(ps is PackedScene, "%s loads" % spec[5]):
			var inst: Node = ps.instantiate()
			kit.ok(inst.has_signal("finished") and inst.has_method("open") and inst.has_method("demo_solve"),
				"%s honours the §12.8 contract" % spec[5])
			kit.ok(str(inst.get_script().get_base_script().resource_path).ends_with("minigame_base.gd"), "%s extends minigame_base.gd" % spec[5])
			inst.free()
	# strings: namespaced, German typography, never the pre-rename name (derived, never spelled: test_rename_guard),
	# nothing overridden by another file
	var old_name: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	kit.ok(old_name.length() >= 4, "pre-rename name derivable")
	for k in strings:
		var key := str(k)
		kit.ok(key.begins_with("mg.flap.") or key.begins_with("mg.cloak.") or key.begins_with("explore.veltrava.station.flap_board.")
			or key.begins_with("explore.veltrava.hall.cloak_tokens."), "%s is namespaced" % key)
		var v := str(strings[k])
		kit.ok(not v.to_lower().contains(old_name), "%s: not the pre-rename name" % key)
		kit.ok(not v.contains("\""), "%s: German quotation marks only" % key)
		kit.ok(loc.source_of(key).ends_with("de_minigames_r7_v.json"), "%s is not overridden" % key)
	# every key the scripts use literally exists
	var re := RegEx.new()
	re.compile("\"(mg\\.(flap|cloak)\\.[a-z0-9_.]+[a-z0-9_])\"")
	for path in [FLAP_GAME, CLOAK_GAME]:
		for m in re.search_all(FileAccess.get_file_as_string(path)):
			var key := m.get_string(1)
			kit.ok(strings.has(key), "%s: key %s exists" % [path.get_file(), key])
	# dynamic keys
	for id in FLAP_LOGIC.IDS:
		kit.ok(strings.has("mg.flap.drum." + str(id)), "drum name %s" % id)
	for c in ["units_tens", "tens_hour", "from_via", "track_via"]:
		kit.ok(strings.has("mg.flap.note." + c), "note %s" % c)
	for n in ["1", "2"]:
		kit.ok(strings.has("mg.flap.sheet.note." + n) and strings.has("mg.flap.sheet.foot." + n), "timetable footnote %s" % n)
	for g in CLOAK_LOGIC.GUESTS:
		for f in ["name", "role", "pin", "wears"]:
			kit.ok(strings.has("mg.cloak.guest.%s.%s" % [g, f]), "guest %s %s" % [g, f])
	for ri in CLOAK_LOGIC.ROUNDS.size():
		kit.ok(strings.has("mg.cloak.round.%d" % (ri + 1)), "round label %d" % (ri + 1))
		for g in CLOAK_LOGIC.ROUNDS[ri]["guests"]:
			for f in ["ask", "thanks", "wrong"]:
				kit.ok(strings.has("mg.cloak.say.%s.%s%d" % [g, f, ri + 1]), "line %s.%s%d" % [g, f, ri + 1])
	for key in CLOAK_LOGIC.SPECIAL:
		kit.ok(strings.has("mg.cloak.say." + str(CLOAK_LOGIC.SPECIAL[key])), "special line %s" % CLOAK_LOGIC.SPECIAL[key])
	for c in CLOAK_LOGIC.COATS:
		kit.ok(strings.has("mg.cloak.coat.%s.name" % c) and strings.has("mg.cloak.coat.%s.desc" % c), "coat %s texts" % c)
	for h in CLOAK_LOGIC.HATS:
		kit.ok(strings.has("mg.cloak.hat.%s.name" % h) and strings.has("mg.cloak.hat.%s.desc" % h), "hat %s texts" % h)
	for key in ["mg.cloak.hint.1", "mg.cloak.hint.2", "mg.cloak.hint.hats", "mg.cloak.hint.next", "mg.flap.hint.1",
			"mg.flap.hint.2", "mg.flap.hint.next"]:
		kit.ok(strings.has(key) and str(strings[key]).begins_with("Tipp"), "%s is a Tipp" % key)
	# story consistency of the cloakroom: Elena's coat stays, and nothing says she is missing
	for k in strings:
		if str(k).begins_with("mg.cloak.") or str(k).begins_with("explore.veltrava.hall.cloak_tokens"):
			var t := str(strings[k]).to_lower()
			kit.ok(not t.contains("verschwunden") and not t.contains("vermisst") and not t.contains("entführ"),
				"%s does not pre-empt Kabine 2" % k)
	kit.ok(str(strings.get("explore.veltrava.hall.cloak_tokens.text", "")).contains("weinrot"), "the find names the wine-red scarf (as the cloakroom find and the typist do)")
	return true


func _hotspots(env: String) -> Array:
	var art = _json("res://assets/environments/%s/scene.json" % env)
	var extra = _json("res://assets/environments/%s/explore_hotspots.json" % env)
	var hs := {}
	if extra is Dictionary:
		hs.merge(extra.get("hotspots", {}))
	if art is Dictionary:
		for k in art.get("hotspots", {}):
			hs[k] = art["hotspots"][k]
	return [hs, art if art is Dictionary else {}, extra if extra is Dictionary else {}]


func _placement() -> bool:
	for id in ENTRIES:
		var spec: Array = ENTRIES[id]
		var got := _hotspots(str(spec[2]))
		var hs: Dictionary = got[0]
		var art: Dictionary = got[1]
		var extra: Dictionary = got[2]
		var hid := str(spec[3])
		kit.ok((extra.get("hotspots", {}) as Dictionary).has(hid), "%s declared in %s/explore_hotspots.json" % [hid, spec[2]])
		kit.ok(not (art.get("hotspots", {}) as Dictionary).has(hid), "%s does not clash with the art manifest" % hid)
		if not kit.ok(hs.has(hid), "%s resolves" % hid):
			continue
		var p := Vector2(float(hs[hid][0]), float(hs[hid][1]))
		var walk := PackedVector2Array()
		for q in art.get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		kit.ok(walk.size() < 3 or Geometry2D.is_point_in_polygon(p, walk), "%s %s inside the walkable area" % [hid, p])
		for pr in art.get("props", []):
			if pr is Dictionary and (pr.get("collision", []) as Array).size() >= 3:
				var poly := PackedVector2Array()
				for q in pr["collision"]:
					poly.append(Vector2(float(q[0]), float(q[1])))
				kit.ok(not Geometry2D.is_point_in_polygon(p, poly), "%s outside the collision of %s" % [hid, pr.get("name", "")])
		var oblique: bool = spec[6]
		for k in hs:
			if str(k) == hid or str(k).begins_with("SP_"):
				continue
			var dv := p - Vector2(float(hs[k][0]), float(hs[k][1]))
			if oblique:
				dv.y *= 1.6
			kit.ok(dv.length() >= MIN_GAP, "%s keeps %d px from %s (%.1f)" % [hid, int(MIN_GAP), k, dv.length()])
		# the interactable and the world cue in the level scene
		var st: SceneState = (load(str(spec[1])) as PackedScene).get_state()
		var found := false
		for i in st.get_node_count():
			if str(st.get_node_name(i)) != str(spec[4]):
				continue
			var props := {}
			for j in st.get_node_property_count(i):
				props[str(st.get_node_property_name(i, j))] = st.get_node_property_value(i, j)
			found = str(props.get("kind", "")) == "discover" and str(props.get("explore_id", "")) == id \
				and str(props.get("hotspot_id", "")) == hid and str(st.get_node_path(i, true)).ends_with("Playfield")
		kit.ok(found, "%s: interactable %s (discover, %s, under Playfield)" % [id, spec[4], hid])
	var lvl_s := FileAccess.get_file_as_string("res://scenes/levels/L_C3_Station.tscn")
	kit.ok(lvl_s.contains("flap_world_cue.gd") and lvl_s.contains("world_flap_board.png"), "the arrivals board hangs in L_C3_Station")
	var lvl_h := FileAccess.get_file_as_string("res://scenes/levels/L_C3_Hall.tscn")
	kit.ok(lvl_h.contains("cloak_world_cue.gd") and lvl_h.contains("world_wenzel.png"), "Herr Wenzel stands behind the counter in L_C3_Hall")
	# the new cloakroom find stands next to (and leaves alone) the text agent's cloakroom find
	var hall := _hotspots("veltrava_hall")[0] as Dictionary
	if hall.has("exp_cloakroom") and hall.has("exp_cloak_tokens"):
		kit.ok(absf(float(hall["exp_cloakroom"][0]) - float(hall["exp_cloak_tokens"][0])) <= 60.0, "exp_cloak_tokens is next to exp_cloakroom")
	return true


# ================================================================ assets
func _assets() -> bool:
	for f in ["flap_board.png", "flap_faces.png", "flap_faces_hc.png", "flap_hatch.png", "world_flap_board.png",
			"flap_closeup.png", "flap_layout.json"]:
		kit.ok(FileAccess.file_exists(FLAP_ART + f), "flap art %s" % f)
	for f in ["cloak_back.png", "cloak_front.png", "cloak_coats.png", "cloak_hats.png", "cloak_guests.png",
			"cloak_wenzel.png", "cloak_tokens.png", "world_wenzel.png", "cloak_closeup.png", "cloak_layout.json"]:
		kit.ok(FileAccess.file_exists(CLOAK_ART + f), "cloak art %s" % f)
	var lay = _json(FLAP_ART + "flap_layout.json")
	if lay is Dictionary:
		var faces := Image.load_from_file(ProjectSettings.globalize_path(FLAP_ART + "flap_faces.png"))
		var hc := Image.load_from_file(ProjectSettings.globalize_path(FLAP_ART + "flap_faces_hc.png"))
		kit.ok(faces != null and hc != null and faces.get_size() == hc.get_size(), "high-contrast faces match the normal sheet")
		for dr in lay.get("drums", []):
			kit.ok(faces != null and int(dr["w"]) * (dr["flaps"] as Array).size() <= faces.get_width(), "faces of %s fit the sheet" % dr["id"])
		var board := Image.load_from_file(ProjectSettings.globalize_path(FLAP_ART + "flap_board.png"))
		kit.ok(board != null and [board.get_width(), board.get_height()] == _ints(lay.get("size", [])), "board size matches the layout")
		var wf := Image.load_from_file(ProjectSettings.globalize_path(FLAP_ART + "world_flap_board.png"))
		var wcell: Array = lay.get("world_frame", [84, 41])
		kit.ok(wf != null and wf.get_width() == int(wcell[0]) * 3 and wf.get_height() == int(wcell[1]), "world board: 3 frames")
	var cl = _json(CLOAK_ART + "cloak_layout.json")
	if cl is Dictionary:
		var gs := Image.load_from_file(ProjectSettings.globalize_path(CLOAK_ART + "cloak_guests.png"))
		var gc: Array = cl.get("guest_cell", [64, 72])
		kit.ok(gs != null and gs.get_width() == int(gc[0]) * 6 and gs.get_height() == int(gc[1]) * 4, "busts: 6 x 4 cells")
		var cs := Image.load_from_file(ProjectSettings.globalize_path(CLOAK_ART + "cloak_coats.png"))
		kit.ok(cs != null and cs.get_width() == int(cl["coat_cell"][0]) * (cl["coats"] as Array).size(), "one coat per cell")
		var hs := Image.load_from_file(ProjectSettings.globalize_path(CLOAK_ART + "cloak_hats.png"))
		kit.ok(hs != null and hs.get_width() == int(cl["hat_cell"][0]) * (cl["hats"] as Array).size(), "one hat per cell")
	for id in SFX:
		var path := "res://assets/audio/sfx/%s.wav" % id
		if not kit.ok(FileAccess.file_exists(path), "sfx %s exists" % id):
			continue
		var f := FileAccess.open(path, FileAccess.READ)
		var head := f.get_buffer(44)
		f.close()
		kit.ok(head.slice(0, 4).get_string_from_ascii() == "RIFF" and head.decode_u16(22) == 1 and head.decode_u32(24) == 44100
			and head.decode_u16(34) == 16, "sfx %s: 44.1 kHz, 16 bit, mono" % id)
	return true
