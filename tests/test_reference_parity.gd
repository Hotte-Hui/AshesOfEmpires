extends RefCounted
## Cross-check against the ORIGINAL Python reference. tests/reference/make_python_reference.py runs
## preproduction/tools/story_engine_v4.py + simulate_slice.py (on preproduction/data/v3, ids mapped to this
## project) and stores routes, legacy saves, API traces, a mutated/corrupted save corpus and json cases in
## tests/reference/python_reference.json.gz. This test replays everything with the GDScript port and
## demands identical results: byte-identical save JSON, identical accept/reject verdicts, identical
## StoryError messages and identical loaded states.

const Kit := preload("res://tests/support/test_kit.gd")
const Legacy := preload("res://tests/support/legacy_runtime_v2.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const FIXTURE := "res://tests/reference/python_reference.json.gz"
const MAX_REPORTED := 25

var kit: Kit
var fx: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var t0 := Time.get_ticks_msec()
	fx = _load_fixture()
	if fx.is_empty():
		kit.fail("fixture missing/unreadable: %s — run: py -3 -P tests/reference/make_python_reference.py" % FIXTURE)
		return kit.failures
	print("      fixture parsed in %d ms (generated with Python %s)" % [Time.get_ticks_msec() - t0, fx.get("python", "?")])
	kit.run_case("fixture_matches_current_reference_and_data", _fixture_current)
	kit.run_case("routes_byte_identical", _routes)
	kit.run_case("legacy_saves_and_migration_identical", _legacy)
	kit.run_case("api_traces_identical", _traces)
	kit.run_case("load_corpus_verdicts_identical", _corpus)
	kit.run_case("json_loads_identical", _json_loads)
	kit.run_case("json_dumps_identical", _json_dumps)
	kit.cleanup()
	return kit.failures


func _load_fixture() -> Dictionary:
	if not FileAccess.file_exists(FIXTURE):
		return {}
	var packed := FileAccess.get_file_as_bytes(FIXTURE)
	var raw := packed.decompress_dynamic(64 * 1024 * 1024, FileAccess.COMPRESSION_GZIP)
	if raw.is_empty():
		return {}
	var r: Dictionary = ENGINE.json_parse(raw.get_string_from_utf8())
	return r["value"] if r["ok"] and typeof(r["value"]) == TYPE_DICTIONARY else {}


func _fixture_current() -> bool:
	for f in fx["reference_sha256"]:
		var path: String = "res://preproduction/tools/" + str(f)
		kit.eq(FileAccess.get_sha256(path), fx["reference_sha256"][f], "%s unchanged since the fixture was generated" % f)
	for stem in fx["data_sha256"]:
		kit.eq(FileAccess.get_sha256("res://data/v3/%s.json" % stem), fx["data_sha256"][stem],
			"data/v3/%s.json unchanged since the fixture was generated (else regenerate it)" % stem)
	for stem in fx["data_equivalent"]:
		kit.eq(fx["data_equivalent"][stem], true, "preproduction %s equals data/v3 after the id mapping" % stem)
	kit.eq(fx["format"], ENGINE.FORMAT, "save format id")
	kit.eq(fx["version"], ENGINE.VERSION, "save version")
	return true


func _routes() -> bool:
	for key in fx["routes"]:
		var parts: PackedStringArray = (key as String).split("|")
		var g := kit.play_verified_route(parts[0], parts[1], parts[2] == "skip")
		kit.eq(g.save_json(), fx["routes"][key], "route %s" % key)
		g.free()
	return true


func _legacy() -> bool:
	for key in fx["legacy"]:
		var exp: Dictionary = fx["legacy"][key]
		var parts: PackedStringArray = (key as String).split("|")
		var v2 := ""
		if parts[0] == "boundary":
			var rt := Legacy.new()
			for o in ["a1_talk_irina", "a1_inspect_seal", "a1_inspect_timetable", "a1_solve_signal", "a1_inspect_ledger"]:
				rt.perform(o)
			rt.perform("a1_choose", parts[1])
			v2 = rt.save_json()
		else:
			v2 = Legacy.play_route(parts[0], parts[1]).save_json()
		kit.eq(v2, exp["v2"], "legacy v0.3 save %s (simulate_slice port)" % key)
		var g := kit.story()
		kit.is_ok(g.load_json(exp["v2"]), "migrate %s" % key)
		kit.eq(g.save_json(), exp["migrated"], "migrated v3 save %s" % key)
		g.free()
	return true


func _traces() -> bool:
	for name in fx["traces"]:
		var actions: Array = fx["traces"][name]["actions"]
		var expected: Array = fx["traces"][name]["expected"]
		var g := kit.story()
		for i in actions.size():
			var act: Array = actions[i]
			var op: String = act[0]
			var a: Array = act.slice(1)
			var r := {}
			var res = null
			match op:
				"available":
					res = Array(g.available())
				"pending":
					res = Array(g.pending_cinematics())
				"hint":
					# Python raises for a non-available puzzle; compare the core result exactly and check that
					# the public bool API reports false in that case.
					r = g.get("_core").puzzle_hint_available(a[0])
					if r["ok"]:
						res = r["available"]
					kit.eq(g.puzzle_hint_available(a[0]), r["ok"] and r.get("available", false), "%s[%d] public hint API" % [name, i])
				"start_dialogue":
					r = g.start_dialogue(a[0])
					res = r.get("node")
				"current_line":
					r = g.current_dialogue_line(a[0])
					res = r.get("node")
				"advance_dialogue":
					r = g.advance_dialogue(a[0])
					res = null if r.get("finished", false) else r.get("node")
				"inspect":
					r = g.inspect(a[0])
				"solve_puzzle":
					r = g.solve_puzzle(a[0], a[1])
					res = r.get("solved")
				"choose":
					r = g.choose(a[0], a[1])
				"consume":
					r = g.consume_cinematic(a[0], a[1])
				"finale":
					r = g.finale(a[0])
				"save_load":
					var text: String = g.save_json()
					g.free()
					g = kit.story()
					r = g.load_json(text)
				"new_game":
					r = g.new_game()
			var e: Dictionary = expected[i]
			var label := "%s[%d] %s" % [name, i, Kit.fmt(act)]
			var ok: bool = not r.has("ok") or r["ok"] == true
			kit.eq(ok, e["ok"], label + " ok")
			if e["ok"]:
				if ok:
					kit.eq(res, e["result"], label + " result")
			else:
				kit.eq(str(r.get("error", "")), e["error"], label + " error message")
			kit.eq(g.save_json(), e["state"], label + " state")
		g.free()
	return true


func _raw_of(c: Dictionary, bases: Dictionary) -> String:
	if c.has("raw"):
		return c["raw"]
	# Same algorithm as gen_raw() in make_python_reference.py, applied in this project's id space.
	var compact: String = ENGINE.json_dumps(Kit.parse(bases[c["base"]]), -1)
	var gen: Dictionary = c["gen"]
	match gen["op"]:
		"pad_to":
			return compact + " ".repeat(int(gen["bytes"]) - compact.to_utf8_buffer().size())
		"junk_to":
			var head := compact.substr(0, compact.length() - 1) + ", \"junk\": \""
			var tail := "\"}"
			var room: int = int(gen["bytes"]) - (head + tail).to_utf8_buffer().size()
			return head + (gen["char"] as String).repeat(room / 2) + "a".repeat(room % 2) + tail
		"junk_nest":
			var d: int = gen["depth"]
			return compact.substr(0, compact.length() - 1) + ", \"junk\": " + "[".repeat(d) + "]".repeat(d) + "}"
	return ""


func _corpus() -> bool:
	var corpus: Dictionary = fx["corpus"]
	var results: Array = corpus["results"]
	var g := kit.story()
	var stats := {"cases": 0, "accepted": 0, "rejected": 0, "messages": 0, "mismatch": 0}
	var reported := 0
	for c in corpus["cases"]:
		var raw := _raw_of(c, corpus["bases"])
		if c.has("bytes"):
			kit.eq(raw.to_utf8_buffer().size(), c["bytes"], "generated case %s/%s has the reference byte size" % [c["base"], c["label"]])
		var r: Dictionary = g.validate_save_json(raw)
		stats["cases"] += 1
		var problem := ""
		if c["accept"]:
			if not r["ok"]:
				problem = "Python accepted, GDScript rejected (%s)" % r["error"]
			elif ENGINE.json_dumps(r["state"], 2) != results[c["result"]]:
				problem = "accepted but loaded state differs"
			else:
				stats["accepted"] += 1
		else:
			if r["ok"]:
				problem = "Python rejected (%s), GDScript accepted" % c.get("error", c.get("exception", "?"))
			elif c.has("error") and r["error"] != c["error"]:
				problem = "message differs: Python '%s' vs GDScript '%s'" % [c["error"], r["error"]]
			else:
				stats["rejected"] += 1
				if c.has("error"):
					stats["messages"] += 1
		if problem != "":
			stats["mismatch"] += 1
			if reported < MAX_REPORTED:
				reported += 1
				kit.fail("corpus %s/%s: %s" % [c["base"], c["label"], problem])
	kit.checks += stats["cases"]
	kit.eq(stats["mismatch"], 0, "corpus mismatches")
	kit.eq(ENGINE.Json.MAX_DEPTH, int(corpus["python_max_junk_depth"]) + 1, "parser depth limit equals the reference's")
	print("      corpus: %d cases — %d accepted with identical state, %d rejected (%d with identical StoryError message), %d mismatches"
		% [stats["cases"], stats["accepted"], stats["rejected"], stats["messages"], stats["mismatch"]])
	return true


static func _typed(v) -> Dictionary:
	match typeof(v):
		TYPE_BOOL:
			return {"b": v}
		TYPE_INT:
			return {"i": str(v)}
		TYPE_FLOAT:
			return {"f": v}
		TYPE_NIL:
			return {"n": 0}
		TYPE_STRING:
			return {"s": v}
		TYPE_ARRAY:
			return {"l": (v as Array).map(func(x) -> Dictionary: return _typed(x))}
		TYPE_DICTIONARY:
			var out: Array = []
			for k in v:
				out.append([k, _typed(v[k])])
			return {"d": out}
	return {"?": type_string(typeof(v))}


static func _typed_eq(mine: Dictionary, py: Dictionary) -> bool:
	if mine.has("f") and py.has("f"):
		var f: float = mine["f"]
		var r: String = py["f"]
		if r == "nan":
			return is_nan(f)
		if r == "inf" or r == "-inf":
			return is_inf(f) and (f > 0) == (r == "inf")
		return r.to_float() == f
	if mine.size() != 1 or py.size() != 1 or mine.keys()[0] != py.keys()[0]:
		return false
	var k: String = mine.keys()[0]
	if k == "l":
		if mine["l"].size() != py["l"].size():
			return false
		for i in mine["l"].size():
			if not _typed_eq(mine["l"][i], py["l"][i]):
				return false
		return true
	if k == "d":
		if mine["d"].size() != py["d"].size():
			return false
		for i in mine["d"].size():
			if mine["d"][i][0] != py["d"][i][0] or not _typed_eq(mine["d"][i][1], py["d"][i][1]):
				return false
		return true
	return Kit.strict_eq(mine[k], py[k])


func _json_loads() -> bool:
	for c in fx["json_cases"]["loads"]:
		var r: Dictionary = ENGINE.json_parse(c["text"])
		var label := "json.loads(%s)" % Kit.fmt((c["text"] as String).substr(0, 40))
		kit.eq(r["ok"], c["ok"], label + " accepted?")
		if r["ok"] and c["ok"]:
			kit.checks += 1
			if not _typed_eq(_typed(r["value"]), c["typed"]):   # message only on failure (deep values)
				kit.fail("%s typed value — GDScript %s vs Python %s" % [label, Kit.fmt(_typed(r["value"])), Kit.fmt(c["typed"])])
	return true


func _json_dumps() -> bool:
	for c in fx["json_cases"]["dumps"]:
		var v = Kit.parse(c["value"])
		kit.eq(ENGINE.json_dumps(v, 2), c["pretty"], "json.dumps(indent=2, sort_keys) of %s" % c["value"])
		kit.eq(ENGINE.json_dumps(v, -1), c["compact"], "json.dumps(sort_keys) of %s" % c["value"])
	return true
