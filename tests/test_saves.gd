extends RefCounted
## Saves (scripts/core/save_system.gd): slot round trips, atomic write + .bak, corrupt/oversized/
## tampered file rejection with the live state untouched, legacy payload migration, signals, listing.
## Works in a temporary user:// directory that is removed afterwards.

const Kit := preload("res://tests/support/test_kit.gd")
const Legacy := preload("res://tests/support/legacy_runtime_v2.gd")

var kit: Kit
var _dir := ""


func run() -> Array:
	kit = Kit.new()
	_dir = "user://test_saves_%d_%d" % [Time.get_ticks_usec(), randi() % 100000]
	kit.run_case("round_trip_restores_exact_state", _round_trip)
	kit.run_case("all_slots_list_latest_has_any", _all_slots)
	kit.run_case("unknown_and_empty_slots", _unknown_and_empty)
	kit.run_case("atomic_write_keeps_bak", _atomic_write_keeps_bak)
	kit.run_case("corrupt_files_rejected_live_state_unchanged", _corrupt_files)
	kit.run_case("tampered_story_and_meta_rejected", _tampered)
	kit.run_case("backup_fallback_after_corruption", _backup_fallback)
	kit.run_case("legacy_v2_payload_migrates", _legacy_payload)
	kit.run_case("mid_dialogue_and_puzzle_attempts_survive", _mid_dialogue)
	kit.run_case("extra_data_sanitised_and_playtime", _extra_data)
	kit.run_case("autosave_quicksave_delete", _autosave_quick_delete)
	kit.run_case("stale_tmp_file_is_harmless", _stale_tmp)
	kit.run_case("unwritable_directory_reports_error", _unwritable)
	kit.cleanup()
	_remove_dir(_dir)
	return kit.failures


# ------------------------------------------------------------------ helpers
func _new_saves(sub: String, story: Node = null) -> Node:
	var s := kit.saves()
	s.base_dir = _dir.path_join(sub)
	s.story = story if story != null else kit.story()
	s.extra_provider = Callable()
	return s


func _write(path: String, text: String) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(text)
	f.close()


func _write_bytes(path: String, bytes: PackedByteArray) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_buffer(bytes)
	f.close()


func _read(path: String) -> String:
	return FileAccess.get_file_as_string(path)


static func _remove_dir(path: String) -> void:
	if not DirAccess.dir_exists_absolute(path):
		return
	var d := DirAccess.open(path)
	for sub in d.get_directories():
		_remove_dir(path.path_join(sub))
	for f in d.get_files():
		DirAccess.remove_absolute(path.path_join(f))
	DirAccess.remove_absolute(path)


func _progress_a1(g: Node) -> void:
	kit.play_dialogue(g, "a1_talk_irina")
	kit.step(g.inspect("a1_inspect_seal"), "seal")


# ------------------------------------------------------------------ cases
func _round_trip() -> bool:
	var g := kit.story()
	_progress_a1(g)
	var s := _new_saves("rt", g)
	s.extra_provider = func() -> Dictionary: return {"player_pos": Vector2(140.5, 300), "playtime": 42.5, "scene": g.current_scene}
	var saved_slots: Array = []
	s.saved.connect(func(slot: String) -> void: saved_slots.append(slot))
	var r: Dictionary = s.save("1", "Vor dem Fahrplan")
	kit.is_ok(r, "save slot 1")
	kit.eq(saved_slots, ["1"], "saved signal once")
	var meta: Dictionary = r.get("meta", {})
	kit.eq(meta.get("version"), 1, "container version")
	kit.eq(meta.get("chapter_key"), "ui.chapter_a1", "chapter key")
	kit.eq(meta.get("character"), "alexei", "character")
	kit.eq(meta.get("scene"), "L_A1_Railyard", "scene")
	kit.eq(meta.get("playtime_s"), 42.5, "playtime from extra")
	kit.eq(meta.get("label"), "Vor dem Fahrplan", "label")
	kit.ok(float(meta.get("timestamp", 0)) > 1.7e9, "unix timestamp")
	# load into a different live game
	var other := kit.story()
	var s2 := _new_saves("rt", other)
	var loaded_slots: Array = []
	s2.loaded.connect(func(slot: String) -> void: loaded_slots.append(slot))
	var l: Dictionary = s2.load("1")
	kit.is_ok(l, "load slot 1")
	kit.eq(other.snapshot(), g.snapshot(), "exact story state restored")
	kit.eq(other.save_json(), g.save_json(), "identical story JSON")
	kit.eq(loaded_slots, ["1"], "loaded signal once")
	kit.eq(s2.last_loaded_extra.get("player_pos"), [140.5, 300.0], "extra restored (vector → array)")
	kit.eq(s2.last_loaded_meta.get("label"), "Vor dem Fahrplan", "meta exposed")
	kit.eq(s2.playtime_s, 42.5, "playtime restored")
	# file is pretty JSON with the three sections
	var doc = Kit.parse(_read(s.slot_path("1")))
	kit.ok(doc is Dictionary and doc.has("meta") and doc.has("story") and doc.has("extra"), "container sections")
	kit.eq(doc["story"]["format"], "ashes_of_empires_story_reference_v4", "story payload format")
	kit.eq(doc["story"]["save_version"], 3, "story payload version")
	return true


func _all_slots() -> bool:
	var g := kit.story()
	var s := _new_saves("all", g)
	kit.eq(s.has_any(), false, "no saves yet")
	kit.eq(s.latest(), "", "no latest")
	for slot in ["1", "2", "3", "auto", "quick"]:
		kit.is_ok(s.save(slot), "save " + slot)
	_progress_a1(g)
	kit.is_ok(s.save(2), "int slot id accepted")
	var slots: Array = s.list_slots()
	kit.eq(slots.size(), 5, "five slots")
	for info in slots:
		kit.ok(info["exists"] and info["valid"], "slot %s exists+valid" % info["slot"])
		kit.ok(info.has("timestamp") and info.has("chapter_key") and info.has("label"), "meta fields listed")
	kit.eq(s.has_any(), true, "has_any")
	kit.eq(s.latest(), "2", "latest = slot saved last")
	kit.eq(s.slot_info("2").get("chapter_key"), "ui.chapter_a1", "slot_info")
	kit.eq(s.slot_label_key("quick"), "sys.save.slot.quick", "label key")
	return true


func _unknown_and_empty() -> bool:
	var s := _new_saves("unknown")
	var failed: Array = []
	s.load_failed.connect(func(slot: String, _e: String) -> void: failed.append(slot))
	var r: Dictionary = s.save("4")
	kit.is_err(r, "slot 4 does not exist")
	kit.eq(r.get("error_key"), "sys.save.err.unknown_slot", "unknown slot key")
	kit.is_err(s.load("../evil"), "path traversal rejected")
	var e: Dictionary = s.load("3")
	kit.is_err(e, "empty slot")
	kit.eq(e.get("error_key"), "sys.save.err.empty", "empty key")
	kit.eq(failed, ["../evil", "3"], "load_failed signals")
	return true


func _atomic_write_keeps_bak() -> bool:
	var g := kit.story()
	var s := _new_saves("atomic", g)
	var path: String = s.slot_path("1")
	kit.is_ok(s.save("1"), "first save")
	kit.ok(FileAccess.file_exists(path), "slot file written")
	kit.ok(not FileAccess.file_exists(path + ".tmp"), "no tmp left")
	kit.ok(not FileAccess.file_exists(path + ".bak"), "no bak after first save")
	var first := _read(path)
	var first_state: Dictionary = g.snapshot()
	_progress_a1(g)
	kit.is_ok(s.save("1"), "second save")
	kit.ok(not FileAccess.file_exists(path + ".tmp"), "no tmp left (2)")
	kit.eq(_read(path + ".bak"), first, ".bak holds the previous file byte-for-byte")
	kit.ne(_read(path), first, "slot holds the new state")
	var h := kit.story()
	var s2 := _new_saves("atomic", h)
	kit.is_ok(s2.load_backup("1"), "load_backup")
	kit.eq(h.snapshot(), first_state, "backup restores the previous state")
	kit.is_ok(s2.load("1"), "load main")
	kit.eq(h.snapshot(), g.snapshot(), "main restores the newest state")
	return true


func _corrupt_files() -> bool:
	var live := kit.story()
	_progress_a1(live)
	var before: Dictionary = live.snapshot()
	var replaced := [0]
	live.state_replaced.connect(func(_r: String) -> void: replaced[0] += 1)
	var s := _new_saves("corrupt", live)
	var src := kit.story()
	var writer := _new_saves("corrupt", src)
	kit.is_ok(writer.save("1"), "valid save to corrupt")
	var path: String = s.slot_path("1")
	var good := _read(path)
	var cases := {
		"empty_file": "",
		"truncated": good.substr(0, good.length() / 2),
		"trailing_garbage": good + "}",
		"not_object": "[1, 2, 3]",
		"missing_story": Kit.dumps({"meta": Kit.parse(good)["meta"]}),
		"container_v2": good.replace("\"version\": 1", "\"version\": 2"),
		"container_version_float": good.replace("\"version\": 1", "\"version\": 1.0"),
		"meta_types": good.replace("\"label\": \"\"", "\"label\": 5"),
		"oversized": good + " ".repeat(600 * 1024),
		"story_not_object": good.replace("\"story\": {", "\"story\": [{").replace("\n }\n}", "\n }]\n}"),
	}
	var loaded := [0]
	s.loaded.connect(func(_slot: String) -> void: loaded[0] += 1)
	for label in cases:
		_write(path, cases[label])
		var r: Dictionary = s.load("1")
		kit.is_err(r, "corrupt case " + label)
		kit.eq(live.snapshot(), before, "live state untouched (%s)" % label)
		var info: Dictionary = s.slot_info("1")
		kit.ok(info.get("exists", false) and not info.get("valid", true), "listed as invalid (%s)" % label)
	# invalid UTF-8 bytes
	_write_bytes(path, PackedByteArray([0x7B, 0x22, 0xC3, 0x28, 0x22, 0x7D]))
	kit.is_err(s.load("1"), "invalid utf-8")
	_write_bytes(path, PackedByteArray([0xFF, 0xFE, 0x00, 0x01, 0x80, 0x81]))
	kit.is_err(s.load("1"), "random bytes")
	kit.eq(live.snapshot(), before, "live state untouched (bytes)")
	kit.eq(loaded[0], 0, "loaded never emitted")
	kit.eq(replaced[0], 0, "Story.load_json never reached")
	# A UTF-8 BOM written by a text editor is tolerated on the container (payload still fully validated).
	_write(path, "﻿" + good)
	kit.is_ok(s.load("1"), "BOM-prefixed container accepted")
	kit.eq(live.snapshot(), src.snapshot(), "BOM case loads the saved state")
	return true


func _tampered() -> bool:
	var live := kit.story()
	var before: Dictionary = live.snapshot()
	var s := _new_saves("tamper", live)
	var src := kit.story()
	_progress_a1(src)
	var writer := _new_saves("tamper", src)
	kit.is_ok(writer.save("2"), "valid save")
	var path: String = s.slot_path("2")
	var good: Dictionary = Kit.parse(_read(path))
	var edits := {
		"forged_item": func(d: Dictionary) -> void: d["story"]["inventory"].append("ev_ledger"),
		"skipped_prerequisite": func(d: Dictionary) -> void: d["story"]["completed_objectives"].append("a1_solve_signal"),
		"flag_cheat": func(d: Dictionary) -> void: d["story"]["flags"]["irina_trust"] = 3,
		"meta_scene_mismatch": func(d: Dictionary) -> void: d["meta"]["scene"] = "L_M1_Archive",
		"meta_character_mismatch": func(d: Dictionary) -> void: d["meta"]["character"] = "konrad",
		"story_version_1": func(d: Dictionary) -> void: d["story"]["save_version"] = 1,
		"unknown_format": func(d: Dictionary) -> void: d["story"]["format"] = "other_game",
		"negative_attempts": func(d: Dictionary) -> void: d["story"]["puzzle_attempts"] = {"a1_solve_signal": -1},
	}
	for label in edits:
		var doc: Dictionary = good.duplicate(true)
		(edits[label] as Callable).call(doc)
		_write(path, Kit.dumps(doc, 1))
		var r: Dictionary = s.load("2")
		kit.is_err(r, "tampered " + label)
		kit.ok(str(r.get("error_key", "")).begins_with("sys.save.err."), "error key (%s)" % label)
		kit.eq(live.snapshot(), before, "live state untouched (%s)" % label)
	# unknown container field + extra garbage type are tolerated with warnings
	var doc2: Dictionary = good.duplicate(true)
	doc2["future_field"] = 1
	doc2["extra"] = "not a dict"
	_write(path, Kit.dumps(doc2, 1))
	var ok2: Dictionary = s.load("2")
	kit.is_ok(ok2, "unknown container fields tolerated")
	kit.eq((ok2.get("warnings", []) as Array).size(), 2, "two warnings reported")
	kit.eq(live.snapshot(), src.snapshot(), "valid payload loaded")
	return true


func _backup_fallback() -> bool:
	var g := kit.story()
	var s := _new_saves("bak", g)
	kit.is_ok(s.save("3"), "save 1st")
	_progress_a1(g)
	kit.is_ok(s.save("3"), "save 2nd")
	_write(s.slot_path("3"), "{broken")
	var live := kit.story()
	var s2 := _new_saves("bak", live)
	var r: Dictionary = s2.load("3")
	kit.is_err(r, "broken main file")
	kit.eq(r.get("backup_valid"), true, "result reports a valid backup")
	kit.eq(s2.slot_info("3").get("backup"), true, "listing shows backup")
	kit.is_ok(s2.load_backup("3"), "backup loads")
	kit.eq(live.snapshot()["completed_objectives"], [], "backup = state of the first save")
	return true


func _legacy_payload() -> bool:
	var legacy_text: String = Legacy.play_route("keep_private", "request_explanation").save_json()
	var payload = Kit.parse(legacy_text)
	var doc := {"meta": {"version": 1, "timestamp": 1.0, "chapter_key": "world.x1.title", "character": "none",
		"scene": "L_X1_Montage", "playtime_s": 0, "label": "v0.3"}, "story": payload, "extra": {}}
	var s := _new_saves("legacy")
	_write(s.slot_path("1"), Kit.dumps(doc))
	var r: Dictionary = s.load("1")
	kit.is_ok(r, "legacy story payload migrates through Saves")
	kit.eq(s.story.snapshot().get("save_version"), 3, "migrated to v3")
	kit.eq(s.story.choice_history(), {"a1_choose": "keep_private", "m1_choose": "request_explanation"}, "choices kept")
	kit.ok((r.get("warnings", []) as Array).size() >= 1, "migration reported as warning")
	return true


func _mid_dialogue() -> bool:
	var g := kit.story()
	g.start_dialogue("a1_talk_irina")
	g.advance_dialogue("a1_talk_irina")
	g.advance_dialogue("a1_talk_irina")
	var s := _new_saves("mid", g)
	kit.is_ok(s.quicksave(), "quicksave mid-dialogue")
	var h := kit.story()
	var s2 := _new_saves("mid", h)
	kit.is_ok(s2.quickload(), "quickload")
	kit.eq(h.current_dialogue_line("a1_talk_irina").get("node"), "irina_02", "dialogue resumes at the exact node")
	kit.eq(h.objective_state("a1_talk_irina"), "available", "dialogue still incomplete")
	return true


func _extra_data() -> bool:
	var g := kit.story()
	var s := _new_saves("extra", g)
	var obj := RefCounted.new()
	s.extra_provider = func() -> Dictionary: return {"pos": Vector2i(3, 4), "name": &"x", "object": obj, "nested": {"c": Color(1, 0, 0, 1)}}
	s.playtime_s = 12.34
	var r: Dictionary = s.save("1")
	kit.is_ok(r, "save with odd extra")
	kit.eq(r["meta"]["playtime_s"], 12.3, "fallback playtime counter used when extra has none")
	var s2 := _new_saves("extra", kit.story())
	kit.is_ok(s2.load("1"), "load")
	kit.eq(s2.last_loaded_extra, {"pos": [3, 4], "name": "x", "object": null, "nested": {"c": [1.0, 0.0, 0.0, 1.0]}}, "sanitised extra")
	s.extra_provider = func() -> Dictionary: return {"blob": "x".repeat(40000)}
	kit.is_ok(s.save("2"), "oversized extra does not block saving")
	var s3 := _new_saves("extra", kit.story())
	kit.is_ok(s3.load("2"), "load 2")
	kit.eq(s3.last_loaded_extra, {}, "oversized extra dropped")
	return true


func _autosave_quick_delete() -> bool:
	var g := kit.story()
	var s := _new_saves("auto", g)
	kit.is_ok(s.autosave("a1_completed"), "autosave")
	kit.eq(s.slot_info("auto").get("label"), "a1_completed", "autosave label = reason")
	kit.is_ok(s.quicksave(), "quicksave")
	kit.is_ok(s.save("1"), "manual")
	kit.is_ok(s.save("1"), "manual again (creates .bak)")
	var deleted: Array = []
	s.deleted.connect(func(slot: String) -> void: deleted.append(slot))
	var d: Dictionary = s.delete("1")
	kit.is_ok(d, "delete")
	kit.eq(d.get("existed"), true, "existed")
	kit.ok(not FileAccess.file_exists(s.slot_path("1")) and not FileAccess.file_exists(s.slot_path("1") + ".bak"), "files removed")
	kit.eq(deleted, ["1"], "deleted signal")
	kit.eq(s.slot_info("1").get("exists"), false, "listed as empty")
	s.delete("auto")
	s.delete("quick")
	kit.eq(s.has_any(), false, "no saves left")
	kit.eq(s.delete("2").get("existed"), false, "deleting an empty slot is ok")
	return true


func _stale_tmp() -> bool:
	var g := kit.story()
	var s := _new_saves("tmp", g)
	_write(s.slot_path("1") + ".tmp", "half written garbage")
	kit.is_ok(s.save("1"), "save over stale tmp")
	kit.ok(not FileAccess.file_exists(s.slot_path("1") + ".tmp"), "tmp consumed")
	kit.is_ok(_new_saves("tmp", kit.story()).load("1"), "file valid")
	return true


func _unwritable() -> bool:
	var s := _new_saves("unwritable")
	# a FILE where the save directory should be → directory creation / writing must fail cleanly
	_write(_dir.path_join("blocker"), "x")
	s.base_dir = _dir.path_join("blocker").path_join("saves")
	var failed: Array = []
	s.save_failed.connect(func(slot: String, _e: String) -> void: failed.append(slot))
	var r: Dictionary = kit.quietly(func() -> Dictionary: return s.save("1"))
	kit.is_err(r, "write into a path below a file fails")
	kit.eq(r.get("error_key"), "sys.save.err.write", "write error key")
	kit.eq(failed, ["1"], "save_failed signal")
	return true
