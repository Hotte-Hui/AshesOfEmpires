extends RefCounted
## Chapter-3 presentation layer (documentation/C3_DESIGN.md §3): unit tests of scripts/core/chapter_ext.gd —
## compare() / matches() / pick() / line_key() / choice_options() / reaction() — always with EXPLICIT flag
## dictionaries (never the live Story), and the consistency of data/chapters/*.json with data/v3, the locale
## files (resolved through a fresh Loc), the flags, dialogue nodes, objectives, choices, characters, chapter
## cards, levels, palettes and grades.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const EXT_PATH := "res://scripts/core/chapter_ext.gd"
const CHAPTER_DIR := "res://data/chapters/"
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
const OPERATORS := [">=", "<=", "==", "!=", ">", "<"]
const TOP_KEYS := ["chapter", "doc", "levels", "entry_spawn", "chapter_cards", "palettes", "grades", "line_expr",
	"line_variants", "choice_text", "reactions", "puzzles", "cinematics"]

var kit: Kit
var CE: GDScript
var ext: RefCounted
var loc: Node
var data: Dictionary = {}
var files: Dictionary = {}       # path -> parsed chapter file
var nodes: Dictionary = {}       # dialogue node id -> node
var node_dialogue: Dictionary = {}   # dialogue node id -> dialogue id
var objectives: Dictionary = {}  # objective id -> objective
var defaults: Dictionary = {}    # flag -> default value


func run() -> Array:
	kit = Kit.new()
	CE = load(EXT_PATH)
	ext = CE.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	data = ENGINE.load_data()["data"]
	for conv in data["dialogue"]["conversations"]:
		for n in conv["nodes"]:
			nodes[n["id"]] = n
			node_dialogue[n["id"]] = conv["id"]
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			objectives[o["id"]] = o
	for f in data["flags"]["flags"]:
		defaults[f] = data["flags"]["flags"][f]["default"]
	_read_files()
	kit.run_case("compare_operators", _compare)
	kit.run_case("matches_all_conditions", _matches)
	kit.run_case("pick_first_match_wins", _pick)
	kit.run_case("line_key_and_expressions", _line_key)
	kit.run_case("choice_options_variants", _choice_options)
	kit.run_case("reaction_variants", _reaction)
	kit.run_case("director_queries", _director_queries)
	kit.run_case("chapter_files_parse_and_merge", _files)
	kit.run_case("keys_resolve_in_a_fresh_loc", _keys_resolve)
	kit.run_case("conditions_name_existing_flags", _condition_flags)
	kit.run_case("nodes_objectives_choices_exist", _ids_exist)
	kit.run_case("expressions_and_speakers_known", _expressions_speakers)
	kit.run_case("chapter_cards_levels_spawns", _cards)
	kit.run_case("palettes_and_grades_well_formed", _palettes_grades)
	kit.cleanup()
	return kit.failures


func _read_files() -> void:
	var d := DirAccess.open(CHAPTER_DIR)
	if d == null:
		return
	var names := Array(d.get_files())
	names.sort()
	for f in names:
		if f.ends_with(".json"):
			var r: Dictionary = ENGINE.json_parse(FileAccess.get_file_as_string(CHAPTER_DIR + f))
			files[CHAPTER_DIR + f] = r["value"] if r["ok"] else null


## Every [label, variant list] of the chapter data (line variants, option texts, reactions).
func _variant_lists() -> Array:
	var out: Array = []
	for node_id in ext.line_variants:
		out.append(["line_variants." + node_id, ext.line_variants[node_id]])
	for oid in ext.choice_text:
		for cid in ext.choice_text[oid]:
			out.append(["choice_text.%s.%s" % [oid, cid], ext.choice_text[oid][cid]])
	for oid in ext.reactions:
		for cid in ext.reactions[oid]:
			out.append(["reactions.%s.%s" % [oid, cid], ext.reactions[oid][cid]])
	return out


func _flags(extra: Dictionary) -> Dictionary:
	var f := defaults.duplicate()
	f.merge(extra, true)
	return f


# ------------------------------------------------------------------ unit tests
func _compare() -> bool:
	var cases := [
		[1, ">=1", true], [0, ">=1", false], [2, "<=2", true], [3, "<=2", false], [0, "==0", true], [1, "==0", false],
		[1, "!=0", true], [0, "!=0", false], [2, ">1", true], [1, ">1", false], [0, "<1", true], [1, "<1", false],
		[1.0, ">=1", true], [2, " >= 1 ", true], [3, ">=2.5", true], [2, ">=2.5", false],
		# bool specs compare truthiness of bool/int flag values
		[true, true, true], [false, true, false], [false, false, true], [true, false, false], [1, true, true], [0, true, false],
		# a missing flag (null) or a bool never satisfies a numeric comparison
		[null, ">=1", false], [null, "<=2", false], [null, "==0", false], [true, ">=1", false], [false, "==0", false],
		# numeric specs
		[1, 1, true], [1.0, 1, true], [2, 1, false], [null, 0, false],
		# anything else: string equality
		["x", "x", true], ["y", "x", false], [1, "1", true],
	]
	for c in cases:
		kit.eq(CE.compare(c[0], c[1]), c[2], "compare(%s, %s)" % [Kit.fmt(c[0]), Kit.fmt(c[1])])
	return true


func _matches() -> bool:
	var both := {"irina_trust": ">=1", "office_suspicion": "==0"}
	var cases := [
		[null, {}, true], [{}, {"irina_trust": 1}, true], ["not a dict", {}, true],
		[{"irina_trust": ">=1"}, {"irina_trust": 1}, true], [{"irina_trust": ">=1"}, {"irina_trust": 0}, false],
		[both, {"irina_trust": 1, "office_suspicion": 0}, true], [both, {"irina_trust": 1, "office_suspicion": 1}, false],
		[both, {"irina_trust": 0, "office_suspicion": 0}, false],
		[{"irina_trust": ">=1"}, {}, false],
		[{"c17_confirmed": true}, {"c17_confirmed": true}, true], [{"c17_confirmed": true}, {"c17_confirmed": false}, false],
		[{&"irina_trust": ">=1"}, {"irina_trust": 2}, true],
	]
	for c in cases:
		kit.eq(CE.matches(c[0], c[1]), c[2], "matches(%s, %s)" % [Kit.fmt(c[0]), Kit.fmt(c[1])])
	return true


func _pick() -> bool:
	var variants := [{"when": {"a": ">=1"}, "key": "k1"}, {"when": {"b": ">=1"}, "key": "k2"}, {"key": "fallback"}]
	kit.eq(ext.pick(variants, {"a": 1, "b": 1}).get("key"), "k1", "first matching entry wins")
	kit.eq(ext.pick(variants, {"b": 1}).get("key"), "k2", "second entry")
	kit.eq(ext.pick(variants, {}).get("key"), "fallback", "an entry without when always matches")
	kit.eq(ext.pick(variants.slice(0, 2), {"a": 0}), {}, "no match → {}")
	kit.eq(ext.pick("not an array", {"a": 1}), {}, "non-list → {}")
	kit.eq(ext.pick([42, "x", {"when": {}, "key": "k"}], {}).get("key"), "k", "non-dictionary entries skipped; empty when matches")
	kit.eq(ext.pick(variants, {"a": 1}), variants[0], "returns the variant itself")
	# The explicit dictionary is used as is (the live Story's default irina_trust 0 would match "==0").
	kit.eq(ext.pick([{"when": {"irina_trust": "==0"}, "key": "k"}], {}), {}, "explicit {} flags, no live-Story fallback")
	return true


func _line_key() -> bool:
	var cases := [
		["c3a_cond_02", {"irina_trust": 1}, "dlg.c3.cond_02.irina"],
		["c3a_cond_02", {"alexei_secrecy": 1}, "dlg.c3.cond_02.secrecy"],
		["c3a_cond_02", {"irina_trust": 1, "alexei_secrecy": 1}, "dlg.c3.cond_02.irina"],
		["c3a_cond_02", {}, "dlg.c3.cond_02"],
		["c3a_ctrl_05", {"alexei_secrecy": 1}, "dlg.c3.ctrl_05.secrecy"],
		["c3b_arr_02", {"konrad_evidence": 1, "office_suspicion": 1}, "dlg.c3.arr_02.evidence"],
		["c3b_arr_03", {"konrad_evidence": 1}, "dlg.c3.arr_03"],
		["c3b_arr_03", {"office_suspicion": 1}, "dlg.c3.arr_03.suspicion"],
		["c3b_meet_03", {"elena_trust": 1, "evidence_chain": 1}, "dlg.c3.meet_03.elena"],
		["c3b_meet_03", {"evidence_chain": 1}, "dlg.c3.meet_03.evidence"],
		["c3b_meet_08", {"office_suspicion": 1}, "dlg.c3.meet_08.suspicion"],
		["c3b_meet_09", {"irina_trust": 3}, "dlg.c3.meet_09"],
		["irina_01", {"irina_trust": 1}, "dlg.irina.01"],
	]
	for c in cases:
		var base: String = nodes[c[0]]["text_key"]
		kit.eq(ext.line_key(c[0], base, _flags(c[1])), c[2], "line_key(%s, %s)" % [c[0], Kit.fmt(c[1])])
	kit.eq(ext.line_key("no_such_node", "some.key", {}), "some.key", "unknown node keeps its key")
	# Every variant node shows its canonical line in a state where no condition holds (the defaults) …
	for node_id in ext.line_variants:
		var base: String = nodes.get(node_id, {}).get("text_key", "?")
		var first: Dictionary = ext.pick(ext.line_variants[node_id], defaults)
		kit.eq(ext.line_key(node_id, base, defaults), str(first.get("key", base)), "line_key(%s) with default flags" % node_id)
	# … and the flags of a real playthrough select the expected lines at the meeting (share/preserve/ask_elena).
	var g := kit.story()
	kit.play_until(g, "c3a", {"a1": "share_with_irina", "m1": "preserve_evidence", "c3a": "ask_elena"})
	var f: Dictionary = g.flags()
	kit.eq(["c3b_arr_02", "c3b_meet_03", "c3b_meet_07", "c3b_meet_08"].map(func(n: String) -> String: return ext.line_key(n, nodes[n]["text_key"], f)),
		["dlg.c3.arr_02.evidence", "dlg.c3.meet_03.elena", "dlg.c3.meet_07.irina", "dlg.c3.meet_08.evidence"], "variants of a share/preserve/ask_elena playthrough")
	kit.eq(ext.expr_for("c3a_ctrl_05"), "surprised", "expr_for")
	kit.eq(ext.expr_for("no_such_node"), "neutral", "expr_for default")
	kit.eq(ext.expr_for("no_such_node", "concerned"), "concerned", "expr_for fallback")
	return true


func _choice_options() -> bool:
	var make := func(oid: String) -> Array:
		var opts: Array = []
		for o in objectives[oid]["choices"]:
			opts.append({"id": o["id"], "text": loc.t(o["text_key"]), "text_key": o["text_key"]})
		return opts
	var base: Array = make.call("c3b_choose")
	var copy: Array = base.duplicate(true)
	var cases := [
		[{}, ["choice.c3b.share_protocol", "choice.c3b.search_elena", "choice.c3b.report_delegation"]],
		[{"konrad_evidence": 1}, ["choice.c3b.share_protocol.evidence", "choice.c3b.search_elena", "choice.c3b.report_delegation"]],
		[{"office_suspicion": 1}, ["choice.c3b.share_protocol.suspicion", "choice.c3b.search_elena", "choice.c3b.report_delegation.suspicion"]],
		[{"konrad_evidence": 1, "office_suspicion": 1}, ["choice.c3b.share_protocol.evidence", "choice.c3b.search_elena", "choice.c3b.report_delegation.suspicion"]],
	]
	for c in cases:
		var out: Array = ext.choice_options("c3b_choose", base, _flags(c[0]))
		kit.eq(out.map(func(o: Dictionary) -> String: return o["id"]), ["share_protocol", "search_elena", "report_delegation"], "ids and order kept %s" % Kit.fmt(c[0]))
		kit.eq(out.map(func(o: Dictionary) -> String: return o["text"]), (c[1] as Array).map(func(k: String) -> String: return loc.t(k)),
			"option texts for %s" % Kit.fmt(c[0]))
		kit.eq(out.map(func(o: Dictionary) -> String: return o["text_key"]), base.map(func(o: Dictionary) -> String: return o["text_key"]), "other fields kept")
	kit.eq(base, copy, "input options not mutated")
	var c3a: Array = make.call("c3a_choose")
	kit.eq(ext.choice_options("c3a_choose", c3a, _flags({"irina_trust": 1}))[1]["text"], loc.t("choice.c3a.note_alone.irina"), "note_alone, Irina variant")
	kit.eq(ext.choice_options("c3a_choose", c3a, _flags({"alexei_secrecy": 1}))[1]["text"], loc.t("choice.c3a.note_alone.secrecy"), "note_alone, secrecy variant")
	kit.eq(ext.choice_options("c3a_choose", c3a, _flags({"irina_trust": 1}))[0]["text"], loc.t("choice.c3a.ask_elena"), "ask_elena has no variant")
	var a1: Array = make.call("a1_choose")
	kit.eq(ext.choice_options("a1_choose", a1, _flags({"irina_trust": 1})), a1, "objective without option texts: unchanged")
	return true


func _reaction() -> bool:
	var cases := [
		["c3a_choose", "ask_elena", {}, ["elena", "dlg.c3.react.ask_elena", "determined"]],
		["c3a_choose", "note_alone", {"irina_trust": 1}, ["elena", "dlg.c3.react.note_alone", "concerned"]],
		["c3b_choose", "share_protocol", {}, ["alexei", "dlg.c3.react.share_protocol", "determined"]],
		["c3b_choose", "search_elena", {}, ["alexei", "dlg.c3.react.search_elena", "concerned"]],
		["c3b_choose", "report_delegation", {"elena_trust": 1}, ["alexei", "dlg.c3.react.report_delegation.elena", "concerned"]],
		["c3b_choose", "report_delegation", {"elena_trust": 0}, ["alexei", "dlg.c3.react.report_delegation", "neutral"]],
		["c3b_choose", "no_such_choice", {}, []],
		["a1_choose", "share_with_irina", {}, []],
	]
	for c in cases:
		kit.eq(ext.reaction(c[0], c[1], _flags(c[2])), c[3], "reaction(%s, %s, %s)" % [c[0], c[1], Kit.fmt(c[2])])
	return true


func _director_queries() -> bool:
	for sid in ["L_C3_Station", "L_C3_Hall"]:
		var scene: Dictionary = data["scenes"]["scenes"].filter(func(s: Dictionary) -> bool: return s["id"] == sid)[0]
		kit.eq(ext.level_path(sid), "res://scenes/levels/%s.tscn" % sid, "level_path " + sid)
		kit.eq(ext.spawn_for(sid), scene["entry_spawn"], "spawn_for %s = scenes.json entry_spawn" % sid)
		kit.eq(ext.chapter_card(sid).size(), 2, "chapter card of " + sid)
	kit.eq(ext.chapter_card("L_C3_Station"), ["ui.chapter_c3", "world.c3a.title"], "station card")
	kit.eq([ext.level_path("nope"), ext.spawn_for("nope"), ext.chapter_card("nope")], ["", "", []], "unknown level")
	kit.eq(ext.has_cinematic("LS_nope"), false, "unknown cinematic")
	kit.eq(ext.puzzles.get("c3b_solve_protocol"), "res://scenes/ui/ProtocolPuzzle.tscn", "protocol puzzle UI registered")
	return true


# ------------------------------------------------------------------ data consistency
func _files() -> bool:
	kit.ok(files.has(CHAPTER_DIR + "c3.json"), "data/chapters/c3.json present")
	kit.eq(Kit.sorted(ext.files), Kit.sorted(files.keys()), "ChapterExt loaded every chapter file")
	var owner := {}   # "section/key" -> file (a later file would silently override an earlier one)
	for path in files:
		var d = files[path]
		if not kit.ok(d is Dictionary, "%s parses as strict JSON" % path):
			continue
		for k in d:
			kit.ok(TOP_KEYS.has(k), "%s: known section %s" % [path, k])
			if CE.SECTIONS.has(k):
				kit.ok(d[k] is Dictionary, "%s: section %s is an object" % [path, k])
				if d[k] is Dictionary:
					for key in d[k]:
						kit.ok(not owner.has("%s/%s" % [k, key]), "%s: %s.%s already defined in %s" % [path, k, key, owner.get("%s/%s" % [k, key], "")])
						owner["%s/%s" % [k, key]] = path
	return true


func _keys_resolve() -> bool:
	var keys: Array = []
	for vl in _variant_lists():
		for v in vl[1]:
			kit.ok(v is Dictionary and typeof(v.get("key")) == TYPE_STRING, "%s: entries carry a key" % vl[0])
			if v is Dictionary:
				keys.append(str(v.get("key")))
	for sid in ext.chapter_cards:
		keys.append_array(ext.chapter_cards[sid])
	kit.ok(keys.size() >= 30, "keys collected (%d)" % keys.size())
	kit.eq(loc.missing(keys), [], "chapter keys without German text")
	for k in keys:
		kit.ok(loc.t(str(k)).strip_edges() != "", "%s has text" % k)
	for node_id in ext.line_variants:
		for v in ext.line_variants[node_id]:
			kit.ne(v.get("key"), nodes.get(node_id, {}).get("text_key"), "variant of %s differs from its base key" % node_id)
			kit.ne(loc.t(str(v.get("key"))), loc.t(str(nodes.get(node_id, {}).get("text_key", ""))), "variant text of %s differs from the base line" % node_id)
	return true


func _condition_flags() -> bool:
	var n := 0
	for vl in _variant_lists():
		for v in vl[1]:
			var when = v.get("when") if v is Dictionary else null
			if when == null:
				continue
			kit.ok(when is Dictionary and not (when as Dictionary).is_empty(), "%s: when is a non-empty object" % vl[0])
			if not (when is Dictionary):
				continue
			for flag in when:
				n += 1
				kit.ok(defaults.has(flag), "%s: flag %s exists in data/v3/flags.json" % [vl[0], flag])
				var spec = when[flag]
				var valid: bool = spec is bool or spec is int or spec is float
				if spec is String:
					var s := (spec as String).strip_edges()
					for op in OPERATORS:
						if s.begins_with(op) and s.substr(op.length()).strip_edges().is_valid_float():
							valid = true
							break
				kit.ok(valid, "%s: condition %s %s is bool, number or <op><number>" % [vl[0], flag, Kit.fmt(spec)])
				# A bool spec on a non-bool flag would compare truthiness of a meter — not what the data means.
				if spec is bool and defaults.has(flag):
					kit.eq(typeof(defaults[flag]), TYPE_BOOL, "%s: bool condition on boolean flag %s" % [vl[0], flag])
	kit.ok(n >= 15, "conditions checked (%d)" % n)
	return true


func _ids_exist() -> bool:
	for node_id in ext.line_variants:
		kit.ok(nodes.has(node_id), "line_variants node %s exists in data/v3/dialogue.json" % node_id)
	for node_id in ext.line_expr:
		kit.ok(nodes.has(node_id), "line_expr node %s exists in data/v3/dialogue.json" % node_id)
	for section in ["choice_text", "reactions"]:
		var table: Dictionary = ext.get(section)
		for oid in table:
			kit.eq(objectives.get(oid, {}).get("type"), "choice", "%s: %s is a choice objective" % [section, oid])
			var ids: Array = objectives.get(oid, {}).get("choices", []).map(func(c: Dictionary) -> String: return c["id"])
			for cid in table[oid]:
				kit.ok(ids.has(cid), "%s: %s is an option of %s" % [section, cid, oid])
	for oid in ext.puzzles:
		kit.eq(objectives.get(oid, {}).get("type"), "puzzle", "puzzles: %s is a puzzle objective" % oid)
	var seq_ids: Array = data["cinematics"]["sequences"].map(func(s: Dictionary) -> String: return s["id"])
	for cid in ext.cinematics:
		kit.ok(seq_ids.has(cid), "cinematics: %s is a sequence of data/v3/cinematics.json" % cid)
	for cid in ["LS_C3_Trains", "LS_C3_ToHall", "LS_C3_Close"]:
		kit.ok(ext.cinematics.has(cid), "Chapter-3 sequence %s has a §12.5 scene" % cid)
	# coverage: every Chapter-3 line has an expression, every Chapter-3 option a reaction that always resolves
	for q in data["quests"]["quests"]:
		if not ext.levels.has(q["scene"]):
			continue
		for o in q["objectives"]:
			if o["type"] == "dialogue":
				for n in data["dialogue"]["conversations"].filter(func(c: Dictionary) -> bool: return c["id"] == o["dialogue_id"])[0]["nodes"]:
					kit.ok(ext.line_expr.has(n["id"]), "expression for %s (%s)" % [n["id"], o["dialogue_id"]])
			elif o["type"] == "choice":
				for c in o["choices"]:
					var vs: Array = ext.reactions.get(o["id"], {}).get(c["id"], [])
					kit.ok(not vs.is_empty() and not (vs[-1] as Dictionary).has("when"), "reaction for %s/%s with an unconditional fallback" % [o["id"], c["id"]])
	return true


func _expressions_speakers() -> bool:
	for node_id in ext.line_expr:
		kit.ok(EXPRESSIONS.has(ext.line_expr[node_id]), "line_expr %s = %s" % [node_id, ext.line_expr[node_id]])
	var known := {}
	for p in data["flags"]["protagonists"]:
		known[p] = true
	for n in nodes.values():
		known[n["speaker"]] = true
	for k in loc.keys():
		if str(k).begins_with("char.") and str(k).ends_with(".name"):
			known[str(k).trim_prefix("char.").trim_suffix(".name")] = true
	for oid in ext.reactions:
		for cid in ext.reactions[oid]:
			for v in ext.reactions[oid][cid]:
				kit.ok(known.has(v.get("speaker")), "reaction %s/%s speaker %s is a known character" % [oid, cid, v.get("speaker")])
				kit.ok(EXPRESSIONS.has(v.get("expr", "neutral")), "reaction %s/%s expression %s" % [oid, cid, v.get("expr")])
	# speakers of reactions are the people of the scene: Elena reacts at the station, Alexei in the palais
	kit.eq(ext.reactions["c3a_choose"].values().map(func(vs: Array) -> String: return vs[0]["speaker"]), ["elena", "elena"], "station reactions by Elena")
	kit.eq(ext.reactions["c3b_choose"].values().map(func(vs: Array) -> String: return vs[0]["speaker"]), ["alexei", "alexei", "alexei"], "palais reactions by Alexei")
	return true


func _cards() -> bool:
	var scenes := {}
	for s in data["scenes"]["scenes"]:
		scenes[s["id"]] = s
	for sid in ext.chapter_cards:
		var card = ext.chapter_cards[sid]
		kit.ok(scenes.has(sid), "chapter card for a known scene %s" % sid)
		kit.ok(card is Array and card.size() == 2, "card of %s is [title, subtitle]" % sid)
		if card is Array:
			kit.eq(loc.missing(card), [], "card keys of %s resolve" % sid)
	for sid in ext.levels:
		kit.ok(scenes.has(sid), "level %s is a scene of data/v3/scenes.json" % sid)
		kit.ok(ResourceLoader.exists(str(ext.levels[sid])), "level scene %s exists" % ext.levels[sid])
		kit.ok(ext.chapter_cards.has(sid), "level %s has a chapter card" % sid)
		kit.eq(ext.spawn_for(sid), scenes.get(sid, {}).get("entry_spawn"), "entry spawn of %s matches scenes.json" % sid)
		kit.eq(ext.chapter_cards.get(sid, ["", ""])[1], scenes.get(sid, {}).get("title_key"), "card subtitle of %s = scene title" % sid)
		kit.eq(ext.chapter_cards.get(sid, ["", ""])[0], _quest_title(sid), "card title of %s = quest title" % sid)
	for sid in ["L_C3_Station", "L_C3_Hall"]:
		kit.ok(ext.levels.has(sid), "Chapter-3 scene %s is registered" % sid)
	return true


func _quest_title(scene_id: String) -> String:
	for q in data["quests"]["quests"]:
		if q["scene"] == scene_id:
			return q["title_key"]
	return ""


func _palettes_grades() -> bool:
	var hex := RegEx.create_from_string("^#[0-9A-Fa-f]{6}$")
	var base_pal = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/palettes.json"))["value"]
	var base_grades = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/grades.json"))["value"]
	for name in ext.palettes:
		var p = ext.palettes[name]
		kit.ok(not base_pal.has(name), "palette %s does not collide with data/palettes.json (merge keeps the base)" % name)
		if not kit.ok(p is Dictionary and not p.is_empty(), "palette %s is a non-empty object of ramps" % name):
			continue
		var count := 0
		for ramp in p:
			var cols = p[ramp]
			kit.ok(cols is Array and not cols.is_empty(), "palette %s.%s is a non-empty list" % [name, ramp])
			if cols is Array:
				for c in cols:
					kit.ok(c is String and hex.search(c) != null, "palette %s.%s colour %s is #RRGGBB" % [name, ramp, Kit.fmt(c)])
				count += cols.size()
		kit.ok(count <= 64, "palette %s fits the 64-colour post shader (%d)" % [name, count])
	var palettes := {}
	palettes.merge(base_pal)
	palettes.merge(ext.palettes)
	for name in ext.grades:
		var g = ext.grades[name]
		kit.ok(not base_grades.has(name), "grade %s does not collide with data/grades.json" % name)
		if not kit.ok(g is Dictionary, "grade %s is an object" % name):
			continue
		for k in g:
			kit.ok(["lift", "gamma", "gain", "tint", "saturation", "vignette", "grain", "palette_strength", "palette"].has(k), "grade %s: known field %s" % [name, k])
		for k in ["lift", "gamma", "gain", "tint"]:
			if g.has(k):
				var v = g[k]
				kit.ok(v is Array and v.size() == 3 and v.all(func(x) -> bool: return (x is float or x is int) and x >= 0.0 and x <= 2.0),
					"grade %s.%s is three numbers in [0, 2]" % [name, k])
		for k in ["saturation", "vignette", "grain", "palette_strength"]:
			if g.has(k):
				kit.ok((g[k] is float or g[k] is int) and g[k] >= 0.0 and g[k] <= 2.0, "grade %s.%s in [0, 2]" % [name, k])
		if g.has("palette"):
			kit.ok(palettes.has(g["palette"]), "grade %s uses a known palette %s" % [name, g["palette"]])
	# every Chapter-3 level's grade preset exists
	for sid in ext.levels:
		var text := FileAccess.get_file_as_string(str(ext.levels[sid]))
		var m := RegEx.create_from_string("grade_preset = \"([^\"]+)\"").search(text)
		if m != null:
			kit.ok(ext.grades.has(m.get_string(1)) or base_grades.has(m.get_string(1)), "%s grade preset %s is defined" % [sid, m.get_string(1)])
	return true
