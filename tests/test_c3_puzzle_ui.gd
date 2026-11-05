extends RefCounted
## Chapter-3 protocol puzzle UI (scenes/ui/ProtocolPuzzle.tscn, scripts/ui/protocol_puzzle.gd,
## documentation/C3_DESIGN.md §2.7): the scene is registered for c3b_solve_protocol and instanced by
## ChapterExt like the slice puzzles; it is driven here stand-alone (headless) against a REAL Story engine
## instance (scripts/story/story_engine.gd, reached through the public API only) plus mock Settings/Audio
## injected through ui_kit overrides. Covers: incomplete submit = no attempt, wrong order = one attempt +
## neutral note with the cards kept, hint after two failures (puzzle_hints 0/1/2), keys 1-4 by the ORIGINAL
## tray order, Backspace/R, correct order = objective complete + flag + `solved` exactly once, Esc closes,
## engine errors (locked objective without clue items, missing clues) shown without breaking, every Loc key
## and the inspect-document metadata.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const ChapterExt := preload("res://scripts/core/chapter_ext.gd")
const SCENE := "res://scenes/ui/ProtocolPuzzle.tscn"
const SCRIPT := "res://scripts/ui/protocol_puzzle.gd"
const OBJ := "c3b_solve_protocol"
const SOLUTION := ["chair", "reich", "secretariat", "soviet"]
const DISPLAY := ["soviet", "secretariat", "chair", "reich"]


class MockSettings extends Node:
	signal changed(key: String, value)
	var values := {"puzzle_hints": 1, "reduced_motion": true, "text_scale": 1.0, "high_contrast": false}

	func get_value(key: String):
		return values.get(key)

	## Like the real Settings: stores, then emits `changed` (UIRoot rescales labels, the puzzle re-lays out).
	func set_value(key: String, v) -> void:
		values[key] = v
		changed.emit(key, v)


class MockAudio extends Node:
	var played: Array = []

	func ui(id) -> void:
		played.append(str(id))


## The engine refuses although the objective is open (inventory without the clue items).
class RefusingStory extends Node:
	var calls := 0

	func puzzle_hint_available(_id) -> bool:
		return false

	func solve_puzzle(_id, _answer) -> Dictionary:
		calls += 1
		return {"ok": false, "error": "Missing clues for puzzle", "error_key": "sys.err.missing_clues"}


class FakeRoot extends Control:
	var toast_layer: Control


class FakeGame extends Node:
	var ui: Node


var kit: TKit
var _saved: Dictionary = {}


func run() -> Array:
	kit = TKit.new()
	_saved = UIKit.overrides.duplicate()
	kit.run_case("scene_registered_and_instanced_by_chapter_ext", _registered)
	kit.run_case("real_story_route_reaches_the_puzzle", _route)
	kit.run_case("incomplete_submit_counts_no_attempt", _incomplete)
	kit.run_case("wrong_order_counts_one_attempt_and_keeps_cards", _wrong)
	kit.run_case("hint_follows_settings_and_attempts", _hints)
	kit.run_case("keys_use_the_original_tray_order", _keys)
	kit.run_case("correct_order_solves_once", _correct)
	kit.run_case("layout_follows_the_text_scale", _layout)
	kit.run_case("escape_closes", _escape)
	kit.run_case("locked_without_clues_shows_engine_error", _locked)
	kit.run_case("refused_or_missing_story_never_breaks", _refused)
	kit.run_case("loc_keys_exist", _loc_keys)
	kit.run_case("documents_and_board_metadata", _documents)
	UIKit.overrides = _saved
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
## Plays the verified route through the public Story API up to c3b_solve_protocol. with_clues = false stops
## after the arrival dialogue (seating plan and booth log NOT inspected -> the puzzle stays locked).
## Also used by tests/visual/protocol_puzzle_preview.gd.
static func play_to_protocol(g: Node, with_clues := true) -> bool:
	var talk := func(oid: String) -> void:
		g.start_dialogue(oid)
		for _i in 64:
			var r = g.advance_dialogue(oid)
			if not (r is Dictionary) or not r.get("ok", false) or r.get("finished", false):
				break
	talk.call("a1_talk_irina")
	g.inspect("a1_inspect_seal")
	g.inspect("a1_inspect_timetable")
	g.solve_puzzle("a1_solve_signal", ["square", "circle", "triangle"])
	g.inspect("a1_inspect_ledger")
	g.choose("a1_choose", "share_with_irina")
	g.inspect("m1_inspect_plan_a")
	g.inspect("m1_inspect_plan_b")
	g.solve_puzzle("m1_align_plans", {"rotation_steps": 0, "offset_x": 2, "offset_y": -1})
	talk.call("m1_talk_emil")
	g.choose("m1_choose", "preserve_evidence")
	talk.call("c3a_talk_conductor")
	g.inspect("c3a_inspect_weighbill")
	g.inspect("c3a_inspect_departures")
	talk.call("c3a_pass_control")
	talk.call("c3a_talk_elena")
	g.choose("c3a_choose", "ask_elena")
	talk.call("c3b_arrival")
	if with_clues:
		g.inspect("c3b_inspect_seating")
		g.inspect("c3b_inspect_log")
	return g.is_available(OBJ) == with_clues and g.objective_state("c3b_arrival") == "complete"


func _story(with_clues := true) -> Node:
	var g := kit.story()
	kit.ok(play_to_protocol(g, with_clues), "route to the protocol puzzle (clues: %s)" % with_clues)
	return g


func _make(story, hints := 1) -> Control:
	var settings := MockSettings.new()
	settings.values["puzzle_hints"] = hints
	kit.track(settings)
	var audio := MockAudio.new()
	kit.track(audio)
	UIKit.overrides = {"Story": story, "Settings": settings, "Audio": audio}
	var pz: Control = load(SCENE).instantiate()
	kit.track(pz)
	(Engine.get_main_loop() as SceneTree).root.add_child(pz)
	return pz


static func key_event(code: int, pressed := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = code as Key
	ev.pressed = pressed
	return ev


func _fill(pz: Control, ids: Array) -> void:
	for id in ids:
		pz.place(str(id))


# ------------------------------------------------------------------ cases
func _registered() -> bool:
	var c3 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c3.json"))
	kit.eq(str(c3.get("puzzles", {}).get(OBJ, "")), SCENE, "data/chapters/c3.json registers the scene")
	var root := FakeRoot.new()
	kit.track(root)
	root.toast_layer = Control.new()
	root.add_child(root.toast_layer)
	var game := FakeGame.new()
	kit.track(game)
	game.ui = root
	UIKit.overrides = {"Settings": MockSettings.new(), "Audio": MockAudio.new()}
	kit.track(UIKit.overrides["Settings"])
	kit.track(UIKit.overrides["Audio"])
	var ext := ChapterExt.new()
	var node: Node = ext.puzzle_ui(game, OBJ)
	kit.ok(node != null and node.get_script() == load(SCRIPT), "ChapterExt.puzzle_ui instances ProtocolPuzzle")
	if node == null:
		return true
	kit.ok(node.get_parent() == root and node.get_index() < root.toast_layer.get_index(), "added under UIRoot before the toasts")
	kit.ok(node.get("ui_root") == root, "ui_root set")
	kit.ok(ext.puzzle_ui(game, OBJ) == node, "instanced once")
	kit.ok(node.has_signal("solved") and node.has_signal("closed"), "signals solved + closed")
	kit.eq(node.get("suppress_toasts"), true, "suppress_toasts")
	kit.eq(node.get("symbols"), DISPLAY, "default tray order")
	kit.eq(node.visible, false, "hidden until opened")
	return true


func _route() -> bool:
	var g := _story(true)
	var p: Dictionary = g.puzzle_for(OBJ)
	kit.eq(p.get("display_symbols"), DISPLAY, "display_symbols of pz_c3_protocol")
	kit.ok(not p.has("solution"), "the UI never sees the solution")
	var pz := _make(g)
	pz.open(OBJ)
	kit.ok(pz.is_open and pz.visible, "open() shows the modal")
	kit.eq(pz.symbols, DISPLAY, "tray follows display_symbols")
	kit.eq(pz.slots, ["", "", "", ""], "empty slots")
	var tray: Array = []
	for c in pz._tray.get_children():
		tray.append(str(c.name).trim_prefix("Card_"))
	kit.eq(tray, DISPLAY, "tray buttons in display order")
	return true


func _incomplete() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, ["chair", "reich"])
	var r: Dictionary = pz.submit()
	kit.eq(r, {}, "nothing submitted")
	kit.eq(g.puzzle_attempts(OBJ), 0, "no attempt counted")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3.protocol.incomplete"), "incomplete note")
	kit.eq(pz.slots, ["chair", "reich", "", ""], "cards stay")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter is consumed")
	kit.eq(g.puzzle_attempts(OBJ), 0, "Enter with free slots: still no attempt")
	kit.ok(pz.is_open and not pz.is_done(), "still open")
	return true


func _wrong() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	var r: Dictionary = pz.submit()
	kit.ok(r.get("ok", false) and not r.get("solved", true), "engine answers wrong, ok")
	kit.eq(g.puzzle_attempts(OBJ), 1, "one attempt counted by the engine")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3.protocol.wrong"), "neutral wrong note")
	kit.eq(pz.slots, DISPLAY, "cards stay for editing")
	kit.ok(not pz.is_done() and pz.is_open, "puzzle continues")
	kit.ok(not pz.hint_shown(), "no hint after one failure (puzzle_hints = 1)")
	kit.eq(g.objective_state(OBJ), "available", "objective still open")
	kit.ok(pz.take_back(0), "a filled slot can be cleared")
	kit.eq(pz.feedback_text(), "", "editing clears the note")
	return true


func _hints() -> bool:
	var g := _story(true)
	var pz := _make(g, 1)
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	pz.submit()
	pz.undo()
	pz.undo()
	_fill(pz, ["reich", "chair"])
	pz.submit()
	kit.eq(g.puzzle_attempts(OBJ), 2, "two failed attempts")
	kit.ok(g.puzzle_hint_available(OBJ), "engine offers the hint")
	kit.ok(pz.hint_shown(), "hint visible after two failures (puzzle_hints = 1)")
	kit.eq(pz._hint_label.text, UIKit.t("ui.c3.protocol.hint"), "hint text")
	UIKit.overrides["Settings"].values["puzzle_hints"] = 0
	pz._refresh()
	kit.ok(not pz.hint_shown(), "puzzle_hints = 0: never")
	var g2 := _story(true)
	var pz2 := _make(g2, 2)
	pz2.open(OBJ)
	kit.ok(pz2.hint_shown(), "puzzle_hints = 2: immediately")
	return true


func _keys() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	kit.ok(pz.modal_input(key_event(KEY_3)), "key 3 consumed")
	kit.eq(pz.slots, ["chair", "", "", ""], "key 3 = third tray card (chair)")
	pz.modal_input(key_event(KEY_1))
	kit.eq(pz.slots, ["chair", "soviet", "", ""], "key 1 = first tray card even after a placement")
	pz.modal_input(key_event(KEY_3))
	kit.eq(pz.slots, ["chair", "soviet", "", ""], "a laid card cannot be laid twice")
	kit.ok(pz.modal_input(key_event(KEY_BACKSPACE)), "Backspace consumed (it is also bound to cancel)")
	kit.eq(pz.slots, ["chair", "", "", ""], "Backspace takes back the card laid last")
	kit.ok(pz.is_open, "Backspace never closes the puzzle")
	pz.modal_input(key_event(KEY_KP_2))
	kit.eq(pz.slots, ["chair", "secretariat", "", ""], "keypad 2 = secretariat")
	pz.take_back(0)
	pz.modal_input(key_event(KEY_4))
	kit.eq(pz.slots, ["reich", "secretariat", "", ""], "next free slot is filled first")
	pz.modal_input(key_event(KEY_BACKSPACE))
	kit.eq(pz.slots, ["", "secretariat", "", ""], "the last laid card (reich) goes back first")
	kit.eq(pz.history, ["secretariat"], "placement history")
	kit.ok(pz.modal_input(key_event(KEY_R)), "R consumed")
	kit.eq(pz.slots, ["", "", "", ""], "R clears the order")
	kit.ok(not pz.modal_input(key_event(KEY_ESCAPE)), "Esc is left to UIRoot -> handle_cancel")
	kit.ok(not pz.modal_input(key_event(KEY_3, false)), "key releases are ignored")
	kit.eq(pz.slots, ["", "", "", ""], "release did not lay a card")
	return true


func _correct() -> bool:
	var g := _story(true)
	var pz := _make(g)
	var count := [0]
	pz.solved.connect(func(id: String) -> void:
		count[0] += 1
		kit.eq(id, OBJ, "solved(obj_id)"))
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(OBJ)
	_fill(pz, DISPLAY)
	pz.submit()                                   # one wrong attempt first
	pz.reset_order()
	for n in [3, 4, 2, 1]:                        # chair, reich, secretariat, soviet by keys
		pz.modal_input(key_event(KEY_1 + n - 1))
	kit.eq(pz.slots, SOLUTION, "solution laid by keys")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter submits")
	kit.eq(g.objective_state(OBJ), "complete", "objective complete in the Story engine")
	kit.eq(g.flag("protocol_matched"), true, "effect protocol_matched")
	kit.eq(count[0], 1, "solved emitted once")
	kit.ok(pz.is_done() and pz.success_shown(), "success text shown")
	kit.eq(pz._success_label.text, UIKit.t("ui.c3.protocol.success"), "success text")
	kit.eq(pz._close_btn.text, UIKit.t("ui.c3.protocol.continue"), "close button becomes Weiter")
	kit.ok(not pz.hint_shown(), "no hint after success")
	kit.eq(pz.submit(), {}, "a second submit does nothing")
	kit.ok(not pz.place("soviet") and not pz.undo() and not pz.reset_order(), "board locked after success")
	kit.eq(count[0], 1, "still exactly one solved signal")
	kit.ok(pz.modal_input(key_event(KEY_ENTER)) and pz.is_open, "Enter right after success is swallowed (guard)")
	var beat: float = pz.success_beat()
	kit.ok(beat >= 3.0 and beat <= 6.0, "auto-close beat %.2f s: a reading pause, but inside the 8 s the input driver waits" % beat)
	pz._solved_at -= 1000
	kit.ok(pz.modal_input(key_event(KEY_ENTER)), "Enter after the guard confirms")
	kit.ok(not pz.is_open and not pz.visible, "closed on confirm")
	kit.eq(closed[0], 1, "closed emitted once")
	pz.open(OBJ)
	kit.ok(not pz.is_done() and pz.slots == ["", "", "", ""], "reopening starts clean")
	return true


## 100 % / 125 %: the four actions sit in a 2x2 grid under the notes; 150 %: the notes need the whole
## column, the actions move into the footer row. Live when Settings emits `changed`, and again on open().
func _layout() -> bool:
	var g := _story(true)
	var pz := _make(g)
	pz.open(OBJ)
	kit.ok(pz._actions.get_parent() == pz._col_b and pz._actions.columns == 2, "100 %: 2x2 grid under the notes")
	var s = UIKit.overrides["Settings"]
	s.set_value("text_scale", 1.5)
	kit.ok(pz._actions.get_parent() == pz._footer and pz._actions.columns == 4, "150 % (live): actions in the footer row")
	for b in [pz._undo_btn, pz._reset_btn, pz._check_btn, pz._close_btn]:
		kit.ok(b.get_parent() == pz._actions and b.custom_minimum_size.x > 0, "button keeps a fixed width in the footer")
	s.set_value("text_scale", 1.25)
	kit.ok(pz._actions.get_parent() == pz._col_b and pz._actions.columns == 2, "125 %: grid under the notes")
	s.set_value("text_scale", 1.5)
	pz.close()
	s.values["text_scale"] = 1.0              # changed silently (e.g. settings loaded from disk)
	pz.open(OBJ)
	kit.ok(pz._actions.get_parent() == pz._col_b and pz._actions.columns == 2, "open() re-applies the layout")
	kit.ok(pz.is_open and pz.slots == ["", "", "", ""], "the board itself is untouched by the re-layout")
	return true


func _escape() -> bool:
	var g := _story(true)
	var pz := _make(g)
	var closed := [0]
	pz.closed.connect(func() -> void: closed[0] += 1)
	pz.open(OBJ)
	_fill(pz, ["chair"])
	kit.ok(pz.handle_cancel(), "Esc/cancel handled")
	kit.ok(not pz.is_open and not pz.visible, "Esc closes")
	kit.eq(closed[0], 1, "closed emitted")
	kit.eq(g.puzzle_attempts(OBJ), 0, "closing is not an attempt")
	kit.eq(g.objective_state(OBJ), "available", "objective still available")
	return true


func _locked() -> bool:
	var g := _story(false)
	kit.eq(g.objective_state(OBJ), "locked", "without the seating plan and log the puzzle is locked")
	var pz := _make(g)
	pz.open(OBJ)
	_fill(pz, SOLUTION)
	var r: Dictionary = pz.submit()
	kit.eq(r.get("ok"), false, "engine refuses")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3.protocol.error", {"error": UIKit.t("sys.err.locked")}), "localised engine error shown")
	kit.eq(g.puzzle_attempts(OBJ), 0, "no attempt")
	kit.ok(pz.is_open and not pz.is_done(), "nothing breaks: still open, not solved")
	kit.eq(pz.slots, SOLUTION, "cards stay")
	kit.eq(g.objective_state(OBJ), "locked", "still locked")
	kit.ok(pz.handle_cancel() and not pz.is_open, "can be closed")
	return true


func _refused() -> bool:
	var st := RefusingStory.new()
	kit.track(st)
	var pz := _make(st)
	pz.open(OBJ)
	kit.eq(pz.symbols, DISPLAY, "display order from data/v3 when the Story has no puzzle_for")
	_fill(pz, SOLUTION)
	pz.submit()
	kit.eq(st.calls, 1, "submitted once")
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3.protocol.error", {"error": UIKit.t("sys.err.missing_clues")}),
		"missing clues: localised engine message")
	kit.ok(not pz.is_done() and pz.is_open, "still open")
	# no Story service at all
	UIKit.overrides["Story"] = null
	pz.submit()
	kit.eq(pz.feedback_text(), UIKit.t("ui.c3.protocol.error", {"error": UIKit.t("ui.common.unavailable")}),
		"no Story: 'Nicht verfügbar'")
	kit.ok(not pz.is_done(), "not solved")
	return true


func _loc_keys() -> bool:
	var loc: Node = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var re := RegEx.new()
	re.compile("\"((?:ui|doc)\\.[a-z0-9_.]+)\"")
	var wanted := {}
	for m in re.search_all(FileAccess.get_file_as_string(SCRIPT)):
		var k := m.get_string(1)
		if not k.ends_with("."):
			wanted[k] = true
	for sym in DISPLAY:
		wanted["ui.c3.protocol.card." + sym] = true
	for e in range(1, 5):
		for f in ["time", "mic", "channel", "remark"]:
			wanted["ui.c3.protocol.log.r%d.%s" % [e, f]] = true
	for f in ["time", "mic", "channel"]:
		wanted["ui.c3.protocol.log.col." + f] = true
	for f in ["title", "subtitle", "chair", "soviet", "reich", "observer_se", "observer_ch", "secretariat", "booths"]:
		wanted["ui.c3.protocol.plan." + f] = true
	wanted["doc.c3.seating.alt"] = true
	wanted["doc.c3.booth_log.alt"] = true
	kit.ok(wanted.size() >= 60, "keys collected (%d)" % wanted.size())
	kit.eq(loc.missing(wanted.keys()), [], "Loc keys used by the protocol puzzle")
	kit.eq(loc.t("ui.c3.protocol.success"), "Paragraph vier kam vom Sekretariat der Kommission – nicht von einer Delegation. Beide Seiten haben zugestimmt, ohne nachzufragen.", "success text (C3_DESIGN §2.7)")
	kit.eq(loc.t("ui.c3.protocol.hint"), "Die Mikrofone sind im Uhrzeigersinn nummeriert, beginnend beim Vorsitz. Zähle die Plätze am Hufeisen ab – das Sekretariat hat einen eigenen Tisch.", "hint text (C3_DESIGN §2.7)")
	return true


func _documents() -> bool:
	var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/documents/veltrava_protocol_documents.json"))
	kit.ok(d is Dictionary and d.get("documents") is Array, "documents json parses")
	var want := {"ev_c3_seating": ["c3b_inspect_seating", "seating", "veltrava_protocol_seating"],
		"ev_c3_booth_log": ["c3b_inspect_log", "booth_log", "veltrava_protocol_booth_log"]}
	var seen := {}
	for e in d.get("documents", []):
		var it := str(e.get("item_id", ""))
		if not want.has(it):
			continue
		seen[it] = true
		var w: Array = want[it]
		kit.eq([str(e.get("objective")), str(e.get("hotspot")), str(e.get("id"))], w, it + ": objective/hotspot/id")
		kit.eq(str(e.get("file")), "res://assets/ui/documents/%s.png" % w[2], it + ": file")
		var img := Image.load_from_file(ProjectSettings.globalize_path(str(e.get("file"))))
		kit.ok(img != null and not img.is_empty(), it + ": png exists")
		if img != null and not img.is_empty():
			kit.ok(img.get_width() * 3 <= 1060 and img.get_height() * 3 <= 760, it + ": fits InspectView at x3")
			kit.eq([img.get_width(), img.get_height()], [int(e["size"][0]), int(e["size"][1])], it + ": size")
		kit.eq(UIKit.doc_for_item(it), w[2], it + ": ui_kit resolves the document")
	kit.eq(seen.size(), 2, "both protocol documents listed")
	var b = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/puzzle/c3_protocol_board.json"))
	kit.ok(b is Dictionary, "board json parses")
	var tags: Array = b["plan"]["tags"].keys()
	tags.sort()
	kit.eq(tags, ["1", "12", "2"], "the plan prints only the numbers 1, 2 and 12")
	var block := {}
	for s in b["plan"]["seats"]:
		block[int(s["mic"])] = str(s["block"])
	kit.eq(block.size(), 12, "twelve microphones")
	var by_block := {}
	for m in block:
		by_block[block[m]] = by_block.get(block[m], []) + [m]
	kit.eq(by_block.get("chair"), [1], "mic 1 = Vorsitz")
	kit.eq(by_block.get("soviet"), [2, 3, 4, 5], "right arm 2-5 = Sowjetische Delegation")
	kit.eq(by_block.get("reich"), [8, 9, 10, 11], "left arm 8-11 = Reichsdelegation")
	kit.eq(by_block.get("secretariat"), [12], "mic 12 = Sekretariat")
	var order: Array = []
	for e in b["log"]["entries"]:
		order.append(block[int(e["mic"])])
	var pzj = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/puzzles.json"))
	var sol: Array = []
	for p in pzj["puzzles"]:
		if p["id"] == "pz_c3_protocol":
			sol = p["solution"]
	kit.eq(order, sol, "log mics read on the plan give the canonical solution")
	kit.eq(sol, SOLUTION, "solution of pz_c3_protocol")
	return true
