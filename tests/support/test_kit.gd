extends RefCounted
## Minimal assertion kit for tests/test_*.gd. Test files keep `extends RefCounted` and hold one Kit in a
## member called `kit` (run_all.gd reads kit.checks / kit.cases for the summary).
##
## Every case is a Callable that must `return true` at its end: a GDScript runtime error aborts the
## function (returns null) and is reported as a failure instead of passing silently.

const ENGINE_PATH := "res://scripts/story/story_engine.gd"
const SAVES_PATH := "res://scripts/core/save_system.gd"
const A1_SYMBOLS := ["square", "circle", "triangle"]
const M1_OVERLAY := {"rotation_steps": 0, "offset_x": 2, "offset_y": -1}
## pz_c3_protocol (documentation/C3_DESIGN.md §2.7): who spoke on Anlage C, in order.
const C3_PROTOCOL := ["chair", "reich", "secretariat", "soviet"]
## The scene chain and the stages of the canonical route (each stage ends with its quest's choice).
const CHAIN := ["L_A1_Railyard", "L_M1_Archive", "L_C3_Station", "L_C3_Hall", "L_X1_Montage"]
const STAGES := ["a1", "m1", "c3a", "c3b"]
const DEFAULT_CHOICES := {"a1": "share_with_irina", "m1": "preserve_evidence", "c3a": "ask_elena", "c3b": "share_protocol"}

var failures: Array = []
var context := ""
var checks := 0
var cases := 0
var _nodes: Array = []


func run_case(case_name: String, fn: Callable) -> void:
	context = case_name
	cases += 1
	var r = fn.call()
	if not (typeof(r) == TYPE_BOOL and r == true):
		failures.append("%s: aborted (runtime error) or did not return true" % case_name)
	context = ""


func fail(msg: String) -> void:
	failures.append(("%s: %s" % [context, msg]) if context != "" else msg)


func ok(cond: bool, msg: String) -> bool:
	checks += 1
	if not cond:
		fail(msg)
	return cond


## Strict deep equality (int 1 != float 1.0; typed and untyped arrays compare by content).
func eq(actual, expected, msg: String) -> bool:
	checks += 1
	if not strict_eq(actual, expected):
		fail("%s — expected %s, got %s" % [msg, fmt(expected), fmt(actual)])
		return false
	return true


func ne(actual, unexpected, msg: String) -> bool:
	checks += 1
	if strict_eq(actual, unexpected):
		fail("%s — did not expect %s" % [msg, fmt(unexpected)])
		return false
	return true


func is_ok(r, msg: String) -> bool:
	checks += 1
	if not (r is Dictionary and r.get("ok", false) == true):
		fail("%s — expected ok, got %s" % [msg, fmt(r)])
		return false
	return true


func is_err(r, msg: String) -> bool:
	checks += 1
	if not (r is Dictionary and r.get("ok", true) == false and str(r.get("error", "")) != ""):
		fail("%s — expected an error result, got %s" % [msg, fmt(r)])
		return false
	return true


## Runs fn with run_all's engine-error trap paused — only for cases that provoke engine errors on purpose
## (e.g. an unwritable save directory makes Godot print "Could not create directory").
func quietly(fn: Callable) -> Variant:
	var trap = Engine.get_meta("ashes_test_error_trap") if Engine.has_meta("ashes_test_error_trap") else null
	var was: bool = trap.enabled if trap != null else false
	if trap != null:
		trap.enabled = false
	var r = fn.call()
	if trap != null:
		trap.enabled = was
	return r


static func strict_eq(a, b) -> bool:
	var ta := typeof(a)
	var tb := typeof(b)
	if ta == TYPE_STRING_NAME:
		ta = TYPE_STRING
	if tb == TYPE_STRING_NAME:
		tb = TYPE_STRING
	if ta != tb:
		return false
	if ta == TYPE_ARRAY:
		if a.size() != b.size():
			return false
		for i in a.size():
			if not strict_eq(a[i], b[i]):
				return false
		return true
	if ta == TYPE_DICTIONARY:
		if a.size() != b.size():
			return false
		for k in a:
			if not b.has(k) or not strict_eq(a[k], b[k]):
				return false
		return true
	if ta == TYPE_STRING:
		return str(a) == str(b)
	return a == b


## Sorted copy of an Array (or of a Dictionary's keys).
static func sorted(v) -> Array:
	var a: Array = (v as Dictionary).keys() if v is Dictionary else Array(v).duplicate()
	a.sort()
	return a


static func fmt(v) -> String:
	var s := ("\"%s\"" % v) if typeof(v) == TYPE_STRING else var_to_str(v)
	s = s.replace("\n", " ")
	return s if s.length() <= 500 else s.substr(0, 500) + "…"


# ------------------------------------------------------------------ factories (freed by cleanup())
func story() -> Node:
	var s: Node = load(ENGINE_PATH).new()
	_nodes.append(s)
	return s


func saves() -> Node:
	var s: Node = load(SAVES_PATH).new()
	_nodes.append(s)
	return s


func track(n: Node) -> Node:
	_nodes.append(n)
	return n


# ------------------------------------------------------------------ scene tree (run_all.gd extends SceneTree)
## The running SceneTree (tests run inside its first _process frame, so the autoloads exist).
static func tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


static func root() -> Window:
	var t := tree()
	return t.root if t != null else null


## Adds a node under /root (its _ready() runs now) and frees it in cleanup().
func mount(n: Node) -> Node:
	var r := root()
	if r != null:
		r.add_child(n)
	return track(n)


func cleanup() -> void:
	for n in _nodes:
		if is_instance_valid(n):
			n.free()
	_nodes.clear()


# ------------------------------------------------------------------ story helpers (public API only)
func step(r, what: String) -> Dictionary:
	if not (r is Dictionary and r.get("ok", false)):
		fail("step '%s' failed: %s" % [what, fmt(r)])
		return {}
	return r


## Plays a dialogue objective to its end exactly like the Python tests:
## start_dialogue, then advance while the objective is in dialogue_progress.
func play_dialogue(g: Node, objective_id: String) -> int:
	step(g.start_dialogue(objective_id), "start " + objective_id)
	var count := 0
	while g.state["dialogue_progress"].has(objective_id) and count < 100:
		step(g.advance_dialogue(objective_id), "advance " + objective_id)
		count += 1
	return count


## Port of TestStoryV4.get_to_signal.
func get_to_signal(g: Node) -> void:
	play_dialogue(g, "a1_talk_irina")
	step(g.inspect("a1_inspect_seal"), "inspect seal")
	step(g.inspect("a1_inspect_timetable"), "inspect timetable")


## The canonical route through the whole chain A1 → M1 → C3a → C3b → finale (the Python counterpart is
## play_full_route() in tests/reference/make_python_reference.py; story_engine_v4.play_verified_route()
## itself ends after M1, where the finale is locked since Chapter 3 was inserted). Authentic dialogue and
## puzzle flows, no bypass; every cinematic is consumed at the end, then the finale.
func play_verified_route(a1 := "share_with_irina", m1 := "preserve_evidence", skip := false,
		c3a := "ask_elena", c3b := "share_protocol") -> Node:
	var g := story()
	play_route_on(g, a1, m1, skip, false, c3a, c3b)
	return g


## Same route on an existing instance. consume_now = consume each cinematic as soon as it is queued
## (what the Game director does) instead of all at the end (what the Python helper does).
func play_route_on(g: Node, a1: String, m1: String, skip: bool, consume_now: bool,
		c3a := "ask_elena", c3b := "share_protocol") -> void:
	var drain := func() -> void:
		if consume_now:
			for seq in g.pending_cinematics():
				step(g.consume_cinematic(seq, skip), "cinematic " + seq)
	play_a1(g, a1, drain)
	play_m1(g, m1, drain)
	drain.call()
	play_c3a(g, c3a)
	drain.call()
	play_c3b(g, c3b)
	for seq in g.pending_cinematics():
		step(g.consume_cinematic(seq, skip), "cinematic " + seq)
	step(g.finale(skip), "finale")


## Stage helpers (public API only). `after_choice` / `after_puzzle` run right after the step that queues a
## cinematic (play_route_on drains the queue there in consume_now mode).
func play_a1(g: Node, a1 := "share_with_irina", after_choice := Callable()) -> void:
	play_dialogue(g, "a1_talk_irina")
	step(g.inspect("a1_inspect_seal"), "inspect seal")
	step(g.inspect("a1_inspect_timetable"), "inspect timetable")
	step(g.solve_puzzle("a1_solve_signal", A1_SYMBOLS.duplicate()), "solve signal")
	step(g.inspect("a1_inspect_ledger"), "inspect ledger")
	step(g.choose("a1_choose", a1), "a1 choice")
	if after_choice.is_valid():
		after_choice.call()


func play_m1(g: Node, m1 := "preserve_evidence", after_puzzle := Callable()) -> void:
	step(g.inspect("m1_inspect_plan_a"), "plan a")
	step(g.inspect("m1_inspect_plan_b"), "plan b")
	step(g.solve_puzzle("m1_align_plans", M1_OVERLAY.duplicate()), "overlay")
	if after_puzzle.is_valid():
		after_puzzle.call()
	play_dialogue(g, "m1_talk_emil")
	step(g.choose("m1_choose", m1), "m1 choice")


func play_c3a(g: Node, c3a := "ask_elena") -> void:
	play_dialogue(g, "c3a_talk_conductor")
	step(g.inspect("c3a_inspect_weighbill"), "inspect weighbill")
	step(g.inspect("c3a_inspect_departures"), "inspect departures")
	play_dialogue(g, "c3a_pass_control")
	play_dialogue(g, "c3a_talk_elena")
	step(g.choose("c3a_choose", c3a), "c3a choice")


func play_c3b(g: Node, c3b := "share_protocol") -> void:
	play_dialogue(g, "c3b_arrival")
	step(g.inspect("c3b_inspect_seating"), "inspect seating")
	step(g.inspect("c3b_inspect_log"), "inspect booth log")
	step(g.solve_puzzle("c3b_solve_protocol", C3_PROTOCOL.duplicate()), "solve protocol")
	step(g.inspect("c3b_inspect_booth"), "inspect booth 2")
	play_dialogue(g, "c3b_talk_alexei")
	step(g.choose("c3b_choose", c3b), "c3b choice")


## Plays the canonical route up to and including the choice of `stage` ("a1" … "c3b"); no cinematic is
## consumed and the finale is not called. choices: {stage: option} overrides DEFAULT_CHOICES.
func play_until(g: Node, stage: String, choices := {}) -> void:
	var c := DEFAULT_CHOICES.duplicate()
	c.merge(choices, true)
	var last := STAGES.find(stage)
	if last < 0:
		fail("play_until: unknown stage " + stage)
		return
	for i in last + 1:
		match STAGES[i]:
			"a1":
				play_a1(g, c["a1"])
			"m1":
				play_m1(g, c["m1"])
			"c3a":
				play_c3a(g, c["c3a"])
			"c3b":
				play_c3b(g, c["c3b"])


static func parse(text: String) -> Variant:
	var r: Dictionary = load(ENGINE_PATH).json_parse(text)
	return r["value"] if r["ok"] else null


static func dumps(v: Variant, indent := 2) -> String:
	return load(ENGINE_PATH).json_dumps(v, indent)
