extends RefCounted
## Edge cases of the engine's Python-compatible JSON layer beyond the parity fixture: int64 boundaries,
## the iterative nesting limit, the encoder's escapes and float formatting, compact mode, json_depth.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("integer_typing_and_int64_bounds", _ints)
	kit.run_case("nesting_limit_matches_cpython", _nesting)
	kit.run_case("strict_strings", _strings)
	kit.run_case("encoder_format", _encoder)
	kit.run_case("round_trip_random_values", _round_trip)
	kit.cleanup()
	return kit.failures


func _parse(text: String) -> Variant:
	var r: Dictionary = ENGINE.json_parse(text)
	return r["value"] if r["ok"] else "<error>"


func _ints() -> bool:
	kit.eq(typeof(_parse("1")), TYPE_INT, "1 is int")
	kit.eq(typeof(_parse("1.0")), TYPE_FLOAT, "1.0 is float")
	kit.eq(typeof(_parse("1e0")), TYPE_FLOAT, "1e0 is float")
	kit.eq(_parse("-0"), 0, "-0")
	kit.eq(_parse("9223372036854775807"), 9223372036854775807, "int64 max stays int")
	kit.eq(_parse("-9223372036854775808"), -9223372036854775807 - 1, "int64 min stays int")
	kit.eq(typeof(_parse("9223372036854775808")), TYPE_FLOAT, "beyond int64 → float, never wraps")
	kit.eq(typeof(_parse("-9223372036854775809")), TYPE_FLOAT, "below int64 → float")
	kit.eq(typeof(_parse("123456789012345678901234567890")), TYPE_FLOAT, "huge → float")
	kit.ok(is_nan(_parse("NaN")), "NaN literal")
	kit.eq(_parse("[Infinity, -Infinity]"), [INF, -INF], "infinities")
	kit.eq(_parse("{\"a\": 1, \"a\": 2}"), {"a": 2}, "duplicate keys: last wins")
	kit.eq(_parse("{\"save_version\": 3}")["save_version"], 3, "typed save_version")
	return true


func _nesting() -> bool:
	var limit: int = ENGINE.Json.MAX_DEPTH
	kit.eq(limit, 2998, "CPython 3.13 C scanner limit")
	kit.ok(typeof(_parse("[".repeat(limit) + "]".repeat(limit))) == TYPE_ARRAY, "limit depth parses (iteratively)")
	kit.eq(_parse("[".repeat(limit + 1) + "]".repeat(limit + 1)), "<error>", "limit + 1 rejected")
	kit.eq(_parse("{\"a\":".repeat(limit) + "1" + "}".repeat(limit)) is Dictionary, true, "deep objects parse")
	kit.eq(ENGINE.json_depth(_parse("[[], {\"a\": [1]}]")), 3, "json_depth")
	kit.eq(ENGINE.json_depth(5), 0, "scalar depth")
	return true


func _strings() -> bool:
	kit.eq(_parse("\"\\u00e4\\ud83d\\ude00\\n\\t\\/\""), "ä😀\n\t/", "escapes and surrogate pairs")
	kit.eq(_parse("\"a\tb\""), "<error>", "raw tab inside a string is invalid (strict)")
	kit.eq(_parse("\"a\u0001b\""), "<error>", "raw control char invalid")
	kit.eq(_parse("\"\\x41\""), "<error>", "invalid escape")
	kit.eq(_parse("\ufeff[]"), "<error>", "BOM rejected like json.loads(str)")
	kit.eq(_parse("[1] [2]"), "<error>", "extra data")
	kit.eq(_parse(" \r\n\t[1]\r\n"), [1], "JSON whitespace accepted")
	return true


func _encoder() -> bool:
	kit.eq(ENGINE.json_dumps({"b": [], "a": {}, "c": [1, {"x": null}]}),
		"{\n  \"a\": {},\n  \"b\": [],\n  \"c\": [\n    1,\n    {\n      \"x\": null\n    }\n  ]\n}", "pretty layout like json.dumps(indent=2, sort_keys=True)")
	kit.eq(ENGINE.json_dumps({"b": [1, 2], "a": true}, -1), "{\"a\": true, \"b\": [1, 2]}", "compact separators")
	kit.eq(ENGINE.json_dumps("\"\\\n\u0001\u001f\u007fä"), "\"\\\"\\\\\\n\\u0001\\u001f\u007fä\"", "string escapes")
	kit.eq(ENGINE.json_dumps([1.0, 0.5, -2.25, 100.0, 0.1, 1.0 / 3.0, -0.0]),
		"[\n  1.0,\n  0.5,\n  -2.25,\n  100.0,\n  0.1,\n  0.3333333333333333,\n  -0.0\n]", "float repr")
	kit.eq(ENGINE.json_dumps([NAN, INF, -INF], -1), "[NaN, Infinity, -Infinity]", "non-finite floats like Python")
	kit.eq(ENGINE.json_dumps({&"k": PackedStringArray(["x"]), "v": Vector2(1, 2)}, -1), "{\"k\": [\"x\"], \"v\": [1.0, 2.0]}", "GDScript types")
	return true


func _round_trip() -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 200:
		var v = _random_value(rng, 0)
		var text: String = ENGINE.json_dumps(v, (i % 3) - 1)
		var back = _parse(text)
		kit.ok(ENGINE.py_eq(back, v) and Kit.strict_eq(back, v), "round trip %d: %s" % [i, text.substr(0, 80)])
	return true


func _random_value(rng: RandomNumberGenerator, depth: int) -> Variant:
	var pick := rng.randi_range(0, 7 if depth < 4 else 4)
	match pick:
		0:
			return null
		1:
			return rng.randf() < 0.5
		2:
			return rng.randi_range(-100000, 100000)
		3:
			# realistic decimals (positions, timestamps); see Json.float_repr for the 17-digit caveat
			return ("%d.%03d" % [rng.randi_range(-1000, 1000), rng.randi_range(0, 999)]).to_float()
		4:
			var chars := "abcäöü \"\\/\n\t😀€C-17_"
			var s := ""
			for k in rng.randi_range(0, 8):
				s += chars[rng.randi_range(0, chars.length() - 1)]
			return s
		5, 6:
			var a: Array = []
			for k in rng.randi_range(0, 4):
				a.append(_random_value(rng, depth + 1))
			return a
	var d := {}
	for k in rng.randi_range(0, 4):
		d["k%d" % rng.randi_range(0, 9)] = _random_value(rng, depth + 1)
	return d
