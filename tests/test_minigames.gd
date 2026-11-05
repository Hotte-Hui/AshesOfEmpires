extends RefCounted
## §12.8 optional mini-games (owner: minigames): the three puzzles are solvable and accept their solution, refuse
## wrong moves with a reason, resolve themselves in auto mode, react to keyboard events through modal_input, and
## their explore entries / hotspots / Interactables / Loc keys are valid and placed by the §12.2 rules.
## Logic is tested on the pure RefCounted classes; scenes are instanced under the SceneTree root (stand-alone,
## no UIRoot) and driven synchronously (time via _process(delta), keys via modal_input(event)).

const Kit := preload("res://tests/support/test_kit.gd")
const SHUNT := "res://scripts/ui/minigames/shunting_logic.gd"
const CHESS := "res://scripts/ui/minigames/chess_logic.gd"
const RADIO := "res://scripts/ui/minigames/radio_logic.gd"
const ENTRIES := {
	"karsk.shunting": ["res://data/explore/karsk.json", "res://scenes/ui/minigames/Shunting.tscn", "exp_shunting",
		"res://scenes/levels/L_A1_Railyard.tscn", "res://assets/environments/karsk_railyard/", "ExpShunting"],
	"karsk.chess": ["res://data/explore/karsk.json", "res://scenes/ui/minigames/ChessProblem.tscn", "exp_chess",
		"res://scenes/levels/L_A1_Railyard.tscn", "res://assets/environments/karsk_railyard/", "ExpChess"],
	"berlin.radio_dial": ["res://data/explore/berlin.json", "res://scenes/ui/minigames/RadioDial.tscn", "exp_radio_dial",
		"res://scenes/levels/L_M1_Archive.tscn", "res://assets/environments/berlin_archive/", "ExpRadioDial"],
}
const STORY := {"L_A1_Railyard": ["irina", "seal", "timetable", "signal_board", "ledger"],
	"L_M1_Archive": ["plan_a", "plan_b", "overlay_table", "emil", "obs_window", "obs_photo", "obs_notice"]}
const MIN_GAP := 26.0

var kit: Kit
var loc: Node


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	kit.run_case("shunting_solver_and_solution", _shunting)
	kit.run_case("shunting_rejects_wrong_moves", _shunting_rejects)
	kit.run_case("chess_solution_lines", _chess)
	kit.run_case("chess_rejects_wrong_moves", _chess_rejects)
	kit.run_case("radio_tuning_and_porter", _radio)
	kit.run_case("explore_entries_valid", _data)
	kit.run_case("hotspots_and_interactables_placed", _placement)
	kit.run_case("loc_keys_exist", _loc_keys)
	kit.run_case("scenes_auto_mode", _auto)
	kit.run_case("scenes_keyboard_and_giveup", _keyboard)
	kit.cleanup()
	return kit.failures


func _json(path: String):
	var f := FileAccess.open(path, FileAccess.READ)
	return JSON.parse_string(f.get_as_text()) if f != null else null


# ================================================================ shunting
func _play_shunt(g, plan: Array) -> bool:
	for mv in plan:
		if not g.set_route(str(mv[0])):
			return false
		g.enter()
		g.set_cut(int(mv[1]))
		if not bool(g.leave().get("ok", false)):
			return false
	return true


func _shunting() -> bool:
	var g = load(SHUNT).new()
	kit.ok(not g.is_solved(), "start position is not solved")
	var plan: Array = g.solve()
	kit.ok(plan.size() >= 5 and plan.size() <= 8, "optimal plan has 5-8 trips (%d)" % plan.size())
	kit.ok(_play_shunt(g, plan), "solver plan is accepted trip by trip")
	kit.ok(g.is_solved(), "plan solves siding 1")
	kit.eq(str(g.tracks["1"]), g.GOAL, "siding 1 holds the waybill order")
	kit.eq(g.trips, plan.size(), "trip counter")
	# the documented hand solution (same length)
	g.reset()
	kit.ok(_play_shunt(g, [["1", 2], ["3", 1], ["1", 0], ["2", 1], ["3", 2], ["1", 0]]), "hand solution accepted")
	kit.ok(g.is_solved(), "hand solution solves")
	return true


func _shunting_rejects() -> bool:
	var g = load(SHUNT).new()
	kit.ok(g.set_route("2"), "route to siding 2")
	g.enter()
	kit.ok(not g.throw_points(1), "points cannot be thrown while coupled up in the throat")
	g.set_cut(2)
	kit.eq(str(g.leave().get("reason", "")), "", "taking both wagons of siding 2 is fine")
	g.set_route("1")
	g.enter()
	g.set_cut(4)
	kit.eq(str(g.leave().get("reason", "")), "headshunt", "4 wagons do not fit the headshunt")
	g.set_cut(0)
	kit.eq(str(g.leave().get("reason", "")), "siding", "4 wagons do not fit siding 1 (3)")
	kit.eq(g.phase, "in", "a refused pull-out leaves the engine coupled up")
	g.set_cut(2)
	var r: Dictionary = g.leave()
	kit.ok(bool(r.get("ok", false)) and not bool(r.get("changed", true)), "pulling out with what it brought is a no-op")
	kit.eq(g.key(), "PG|KU||", "state unchanged by refused moves")
	return true


# ================================================================ chess
func _chess() -> bool:
	var c = load(CHESS).new()
	kit.ok(c.pseudo_legal("c4", "g8"), "Qc4-g8 is geometrically legal (d5 e6 f7 empty)")
	kit.ok(c.gives_check("c4", "g8"), "Qg8 gives check")
	var r: Dictionary = c.try_move("c4", "g8")
	kit.ok(bool(r.get("ok", false)), "key move accepted")
	kit.eq(c.phase, 1, "night shift to move")
	kit.eq(c.reply(), ["e8", "g8"], "forced reply Re8xg8")
	kit.eq(c.piece_at("g8"), "bR", "black rook now on g8")
	r = c.try_move("h6", "f7")
	kit.ok(bool(r.get("ok", false)) and bool(r.get("mate", false)), "Nf7 mates")
	kit.ok(c.is_mate(), "mate recorded")
	kit.eq(c.history, ["mg.chess.line.1w", "mg.chess.line.1b", "mg.chess.line.2w"], "move list")
	# the problem is sound: after Qg8+ only Rxg8 helps (king has no square, the queen is covered by the knight)
	c.reset()
	var bd: Dictionary = c.board.duplicate()
	bd["g8"] = bd["c4"]
	bd.erase("c4")
	var takers: Array = []
	for s in bd:
		if str(bd[s])[0] == "b" and c.pseudo_legal(s, "g8", bd):
			takers.append(s)
	kit.eq(takers, ["h8", "e8"], "only the king (illegal: g8 is covered) and Re8 reach g8")
	var bd2 := bd.duplicate()
	bd2["g8"] = "bQ"
	kit.ok(c.pseudo_legal("h6", "g8", bd2), "the knight covers g8")
	return true


func _chess_rejects() -> bool:
	var c = load(CHESS).new()
	kit.eq(str(c.try_move("h8", "g8").get("reason", "")), "night", "night-shift pieces cannot be moved")
	kit.eq(str(c.try_move("h6", "h5").get("reason", "")), "illegal", "knight cannot move like a pawn")
	kit.eq(str(c.try_move("c4", "c8").get("reason", "")), "slow", "quiet queen move is too slow")
	kit.eq(str(c.try_move("h6", "f7").get("reason", "")), "nf7", "Nf7+ first is refused with its refutation")
	kit.eq(str(c.try_move("g1", "f1").get("reason", "")), "slow", "king move is too slow")
	kit.eq(str(c.try_move("e4", "e5").get("reason", "")), "empty", "empty square")
	kit.eq(c.phase, 0, "still the key move to find")
	kit.eq(c.board, c.START, "refused moves leave the board untouched")
	c.try_move("c4", "g8")
	kit.eq(str(c.try_move("h6", "f5").get("reason", "")), "wait", "no White move before the night shift replied")
	c.reply()
	kit.eq(str(c.try_move("h6", "g8").get("reason", "")), "nxg8", "Nxg8 is not mate")
	kit.eq(str(c.try_move("g1", "h1").get("reason", "")), "nomate", "other second moves are not mate")
	kit.eq(c.phase, 2, "mate still to find")
	return true


# ================================================================ radio
func _radio() -> bool:
	var r = load(RADIO).new()
	kit.ok(r.on_reich(), "starts on the Reichssender")
	kit.ok(r.foreign_signal() == 0.0, "no foreign signal on the red line")
	r.set_needle(r.FOREIGN)
	kit.ok(r.foreign_signal() >= r.CLEAR, "the pencil dot is clear")
	r.set_needle(r.FOREIGN + 0.03)
	kit.ok(r.foreign_signal() < r.CLEAR, "a little off is not clear (needs fine tuning)")
	# listen while the porter reads: AWAY[0] = 8.5 s > LISTEN_NEED
	r.reset()
	r.set_needle(r.FOREIGN)
	var ev: Array = []
	for i in 60 * 6:
		ev.append_array(r.step(1.0 / 60.0))
		if r.done:
			break
	kit.ok(ev.has("solved") and r.done, "5 s of clear listening solve it")
	# caught: the porter looks while the needle is off the red line
	r.reset()
	r.set_needle(0.5)
	ev = []
	for i in 60 * 11:
		ev.append_array(r.step(1.0 / 60.0))
	kit.ok(ev.has("warn") and ev.has("look") and ev.has("caught"), "warn -> look -> caught (%s)" % [ev])
	kit.ok(r.on_reich() and r.caught == 1, "caught: needle back on the Reichssender, counted once")
	# safe: on the red line while he looks
	r.reset()
	ev = []
	for i in 60 * 13:
		ev.append_array(r.step(1.0 / 60.0))
	kit.ok(not ev.has("caught") and ev.has("away"), "on the red line nothing happens")
	# held turning accelerates, a tap is a fine step
	r.reset()
	r.nudge(1)
	kit.ok(absf(r.needle - (r.REICH + r.TAP_STEP)) < 0.0001, "tap = fine step")
	var n0: float = r.needle
	for i in 30:
		r.turn(1, 1.0 / 60.0)
	var slow: float = r.needle - n0
	n0 = r.needle
	for i in 30:
		r.turn(1, 1.0 / 60.0)
	kit.ok(r.needle - n0 > slow * 1.5, "holding turns faster")
	return true


# ================================================================ data
func _data() -> bool:
	for id in ENTRIES:
		var spec: Array = ENTRIES[id]
		var d = _json(spec[0])
		if not kit.ok(d is Dictionary, "%s parses" % spec[0]):
			continue
		var found: Dictionary = {}
		for e in d.get("entries", []):
			if str(e.get("id", "")) == id:
				found = e
		if not kit.ok(not found.is_empty(), "%s exists" % id):
			continue
		kit.ok(str(found.get("kind", "")) in ["detail", "secret"], "%s kind detail|secret" % id)
		kit.eq(str(found.get("minigame", "")), spec[1], "%s minigame scene" % id)
		kit.ok(ResourceLoader.exists(spec[1]), "%s scene exists" % spec[1])
		kit.ok((found.get("history", []) as Array).is_empty(), "%s links no history card" % id)
		var ps = load(spec[1])
		if kit.ok(ps is PackedScene, "%s loads" % spec[1]):
			var inst: Node = ps.instantiate()
			kit.ok(inst.has_signal("finished") and inst.has_method("open") and inst.has_method("demo_solve"),
				"%s honours the §12.8 contract (finished, open, demo_solve)" % spec[1])
			kit.ok(inst.get_script() != null and str(inst.get_script().get_base_script().resource_path).ends_with("minigame_base.gd"),
				"%s extends minigame_base.gd" % spec[1])
			inst.free()
	return true


func _placement() -> bool:
	for id in ENTRIES:
		var spec: Array = ENTRIES[id]
		var env: String = spec[4]
		var extra = _json(env + "explore_hotspots.json")
		var art = _json(env + "scene.json")
		if not kit.ok(extra is Dictionary and art is Dictionary, "%s: hotspot files parse" % id):
			continue
		var hs: Dictionary = (extra.get("hotspots", {}) as Dictionary).duplicate()
		for k in art.get("hotspots", {}):
			hs[k] = art["hotspots"][k]
		kit.ok(not (art.get("hotspots", {}) as Dictionary).has(spec[2]), "%s: hotspot is content-owned (no art clash)" % spec[2])
		if not kit.ok(hs.has(spec[2]), "%s exists" % spec[2]):
			continue
		var p := Vector2(float(hs[spec[2]][0]), float(hs[spec[2]][1]))
		var walk := PackedVector2Array()
		for q in art.get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		kit.ok(walk.size() < 3 or Geometry2D.is_point_in_polygon(p, walk), "%s %s inside the walkable area" % [spec[2], p])
		for pr in art.get("props", []):
			if pr is Dictionary and pr.get("collision", []).size() >= 3:
				var poly := PackedVector2Array()
				for q in pr["collision"]:
					poly.append(Vector2(float(q[0]), float(q[1])))
				kit.ok(not Geometry2D.is_point_in_polygon(p, poly), "%s outside the collision of %s" % [spec[2], pr.get("name", "")])
		var level := str(spec[3]).get_file().get_basename()
		var oblique := level == "L_A1_Railyard"
		for k in hs:
			if k == spec[2]:
				continue
			var is_story: bool = k in STORY.get(level, [])
			if not (is_story or str(k).begins_with("exp_")):
				continue
			var q2 := Vector2(float(hs[k][0]), float(hs[k][1]))
			var dv := p - q2
			if oblique:
				dv.y *= 1.6
			kit.ok(dv.length() >= MIN_GAP, "%s keeps %d px from %s (%.1f)" % [spec[2], int(MIN_GAP), k, dv.length()])
		# the Interactable
		var st: SceneState = (load(spec[3]) as PackedScene).get_state()
		var ok := false
		for i in st.get_node_count():
			if str(st.get_node_name(i)) != spec[5]:
				continue
			var props := {}
			for j in st.get_node_property_count(i):
				props[str(st.get_node_property_name(i, j))] = st.get_node_property_value(i, j)
			ok = str(props.get("kind", "")) == "discover" and str(props.get("explore_id", "")) == id \
				and str(props.get("hotspot_id", "")) == spec[2] and str(st.get_node_path(i, true)).ends_with("Playfield")
		kit.ok(ok, "%s: Interactable %s (discover, %s, under Playfield)" % [id, spec[5], spec[2]])
	return true


func _loc_keys() -> bool:
	var f = _json("res://data/locale/de_minigames.json")
	if not kit.ok(f is Dictionary and f.get("strings") is Dictionary, "de_minigames.json parses"):
		return true
	for k in f["strings"]:
		kit.ok(str(k).begins_with("mg."), "%s lives in the mg. namespace" % k)
		kit.ok(loc.source_of(k).ends_with("de_minigames.json"), "%s is not overridden" % k)
	# every Loc key the mini-game scripts use literally exists
	var re := RegEx.new()
	re.compile("\"(mg\\.[a-z0-9_.]+[a-z0-9_])\"")
	for path in ["res://scripts/ui/minigames/minigame_base.gd", "res://scripts/ui/minigames/shunting_game.gd",
			"res://scripts/ui/minigames/chess_game.gd", "res://scripts/ui/minigames/radio_game.gd",
			"res://scripts/ui/minigames/chess_logic.gd"]:
		for m in re.search_all(FileAccess.get_file_as_string(path)):
			var key := m.get_string(1)
			if key.ends_with("."):
				continue
			kit.ok(loc.has(key), "%s: key %s exists" % [path.get_file(), key])
	for key in ["mg.chess.hint.1", "mg.chess.hint.2", "mg.chess.hint.3", "mg.radio.hint.1", "mg.radio.hint.2",
			"mg.radio.porter.reading", "mg.radio.porter.lowering", "mg.radio.porter.looking", "mg.radio.key.4",
			"mg.chess.fail.slow", "mg.chess.fail.nf7", "mg.chess.fail.check", "mg.chess.fail.nomate",
			"mg.chess.fail.nxg8", "mg.chess.fail.night", "mg.chess.fail.empty", "mg.chess.fail.wait",
			"mg.shunt.wagon.K", "mg.shunt.wagon.U", "mg.shunt.wagon.P", "mg.shunt.wagon.G"]:
		kit.ok(loc.has(key), "dynamic key %s exists" % key)
	return true


# ================================================================ scenes (stand-alone, synchronous)
func _instance(path: String) -> Node:
	var mg: Node = load(path).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(mg)
	kit.track(mg)
	return mg


func _auto() -> bool:
	for id in ENTRIES:
		var mg := _instance(ENTRIES[id][1])
		kit.ok(mg.is_in_group("minigame"), "%s joins group minigame" % id)
		var got: Array = []
		mg.finished.connect(func(ok: bool): got.append(ok))
		mg.open({"explore_id": id, "auto": true})
		kit.ok(mg.is_open, "%s opens" % id)
		mg._process(0.1)
		kit.eq(got, [], "%s: not resolved before ~0.2 s" % id)
		mg._process(0.15)
		kit.eq(got, [true], "%s: auto mode resolves with success" % id)
		kit.ok(not mg.is_open, "%s closes itself" % id)
	return true


func _key(k: int) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = true
	return ev


func _keyboard() -> bool:
	# shunting: Down routes to siding 2, Right drives in, Left/Right move the cut, Enter pulls out
	var sh := _instance(ENTRIES["karsk.shunting"][1])
	sh.open({"explore_id": "karsk.shunting", "auto": false})
	kit.ok(sh.modal_input(_key(KEY_DOWN)), "shunting consumes Down")
	kit.eq(sh.logic.route(), "2", "Down routes to siding 2")
	sh.modal_input(_key(KEY_RIGHT))
	kit.eq(sh.logic.phase, "in", "Right drives in")
	sh._process(3.0)
	sh.modal_input(_key(KEY_RIGHT))
	kit.eq(sh.logic.cut, 1, "Right moves the cut")
	sh.modal_input(_key(KEY_ENTER))
	sh._process(3.0)
	kit.eq(sh.logic.key(), "P|KU|G|", "Right + Enter: pulled out with one wagon")
	kit.eq(str(sh.logic.tracks["H"]), "P", "Enter pulled out with one wagon")
	# a refused move counts as a failure and the hint appears after two
	sh.modal_input(_key(KEY_UP))
	sh.modal_input(_key(KEY_ENTER))
	sh._process(3.0)
	sh.modal_input(_key(KEY_RIGHT))
	sh.modal_input(_key(KEY_RIGHT))
	sh.modal_input(_key(KEY_RIGHT))
	sh.modal_input(_key(KEY_ENTER))
	sh.modal_input(_key(KEY_ENTER))
	kit.ok(sh.fails >= 2 and sh._hint_box.visible, "two refused pull-outs show a hint (fails %d)" % sh.fails)
	kit.ok(sh.modal_input(_key(KEY_R)), "R starts over")
	kit.eq(sh.logic.key(), "|KU|PG|", "start position again")
	var res: Array = []
	sh.finished.connect(func(ok: bool): res.append(ok))
	kit.ok(sh.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "giving up resolves with failure")
	# chess: cursor keys + Enter play the solution
	var ch := _instance(ENTRIES["karsk.chess"][1])
	ch.open({"explore_id": "karsk.chess", "auto": false})
	for k in [KEY_LEFT, KEY_LEFT, KEY_UP, KEY_UP, KEY_UP]:
		ch.modal_input(_key(k))
	kit.eq(ch.cursor, Vector2i(2, 3), "cursor on c4")
	ch.modal_input(_key(KEY_ENTER))
	kit.eq(ch.selected, "c4", "queen picked up")
	kit.ok(ch.handle_cancel() and ch.selected == "" and ch.is_open, "Esc puts the piece back first")
	ch.modal_input(_key(KEY_ENTER))
	for k in [KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_RIGHT, KEY_UP, KEY_UP, KEY_UP, KEY_UP]:
		ch.modal_input(_key(k))
	ch.modal_input(_key(KEY_ENTER))
	kit.eq(ch.logic.phase, 1, "Qg8+ played by keys")
	ch._process(0.3)
	ch._process(1.0)
	kit.eq(ch.logic.phase, 2, "the night shift replied")
	ch._process(0.3)
	ch.cursor = Vector2i(7, 5)
	ch.modal_input(_key(KEY_ENTER))
	ch.cursor = Vector2i(5, 6)
	ch.modal_input(_key(KEY_ENTER))
	kit.ok(ch.solved and ch.logic.is_mate(), "Nf7# by keys solves")
	var cres: Array = []
	ch.finished.connect(func(ok: bool): cres.append(ok))
	ch._process(3.0)
	kit.eq(cres, [true], "solved -> finished(true) after the hold")
	# radio: R is the station key, Left/Right nudge
	var ra := _instance(ENTRIES["berlin.radio_dial"][1])
	ra.open({"explore_id": "berlin.radio_dial", "auto": false})
	var before: float = ra.logic.needle
	ra.modal_input(_key(KEY_RIGHT))
	kit.ok(ra.logic.needle > before, "Right nudges the needle")
	ra.logic.set_needle(0.6)
	ra.modal_input(_key(KEY_R))
	kit.ok(ra.logic.on_reich(), "R presses the station key")
	ra.logic.set_needle(ra.logic.FOREIGN)
	var rres: Array = []
	ra.finished.connect(func(ok: bool): rres.append(ok))
	for i in 60 * 6:
		ra._process(1.0 / 60.0)
	kit.ok(ra.solved, "listening at the dot solves the radio")
	for i in 60 * 3:
		ra._process(1.0 / 60.0)
	kit.eq(rres, [true], "radio resolves with success")
	return true
