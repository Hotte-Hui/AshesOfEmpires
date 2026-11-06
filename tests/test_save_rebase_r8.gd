extends RefCounted
## Round 8: the story chain grew behind c3b_completed (it used to lead to the montage L_X1_Montage, now to the
## registry L_C3_RegistryA). Saves and memory snapshots taken at the end of the old chain continue in the scene that
## now follows their last completed event instead of failing the replay validation (SaveSystem.rebase_story, used by
## read_container and Memories.snapshot_raw). Valid current states, finished playthroughs and unknown shapes stay
## untouched. Round 9 grew the chain again behind c3g_completed (Chapter 4 part 1, documentation/C4_DESIGN.md §1.1):
## the round-8 form „montage after c3g“ continues in L_C4_TunnelsA with Alexei. Round 10 grew it behind c4d_completed
## (Chapter 4 part 2, documentation/C4P2_DESIGN.md §1.1): the round-9 form „montage after c4d“ — written before the flag
## people_protected existed — continues in L_C4P2_KarskA with Alexei, its missing flag filled with the default.

const Kit := preload("res://tests/support/test_kit.gd")
const SAVES := preload("res://scripts/core/save_system.gd")
const MEM := preload("res://scripts/core/memories.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const TMP := "user://test_save_rebase_r8"

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	DirAccess.make_dir_recursive_absolute(TMP)
	kit.run_case("old_montage_save_continues_in_registry", _old_save)
	kit.run_case("current_states_and_odd_shapes_unchanged", _unchanged)
	kit.run_case("old_memory_snapshot_rebased", _memory)
	kit.run_case("round8_montage_save_continues_in_chapter4", _old_save_r8)
	kit.run_case("round8_quay_snapshot_rebased", _memory_r8)
	kit.run_case("round9_montage_save_continues_in_part2", _old_save_r9)
	kit.run_case("round9_annex_snapshot_rebased", _memory_r9)
	for f in DirAccess.get_files_at(TMP):
		DirAccess.remove_absolute(TMP.path_join(f))
	DirAccess.remove_absolute(TMP)
	kit.cleanup()
	return kit.failures


## A Story state as a round-7 build saved it right after c3b_completed: the montage, nobody playing.
func _stale_after_c3b() -> Dictionary:
	var g := kit.story()
	kit.play_until(g, "c3b")
	var st: Dictionary = ENGINE.json_parse(g.save_json())["value"]
	st["current_scene"] = "L_X1_Montage"
	st["active_character"] = "none"
	return st


func _old_save() -> bool:
	var stale := _stale_after_c3b()
	var g := kit.story()
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(stale, 2)).get("ok", false),
		"precondition: the round-7 form is invalid against the grown chain")
	var reb: Dictionary = SAVES.rebase_story(stale)
	kit.eq(reb.get("current_scene"), "L_C3_RegistryA", "re-based scene = the one after c3b_completed")
	kit.eq(reb.get("active_character"), "alexei", "re-based character = that scene's protagonist")
	kit.eq(stale.get("current_scene"), "L_X1_Montage", "the input dictionary is not modified")
	kit.ok(g.validate_save_json(ENGINE.json_dumps(reb, 2)).get("ok", false), "the re-based state validates")
	# the whole container path, as the load menu reads it
	var meta := {"version": SAVES.CONTAINER_VERSION, "timestamp": 1.0, "chapter_key": "ui.chapter_c3",
		"character": "none", "scene": "L_X1_Montage", "playtime_s": 1200.0, "label": ""}
	var path := TMP.path_join("old.json")
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(ENGINE.json_dumps({"meta": meta, "story": stale, "extra": {}}, 1))
	f.close()
	var c: Dictionary = SAVES.read_container(path)
	if not kit.ok(c.get("ok", false), "container reads: " + str(c.get("error", ""))):
		return false
	kit.ok(str(c.get("warnings", [])).contains("re-based"), "the re-base is reported as a warning")
	var r: Dictionary = g.load_json(c["story_raw"])
	kit.ok(r.get("ok", false), "the old save loads: " + str(r.get("error", "")))
	kit.eq(g.current_scene, "L_C3_RegistryA", "it continues in the registry")
	kit.eq(g.active_character, "alexei", "with Alexei")
	return true


func _unchanged() -> bool:
	for stage in ["a1", "c3b", "c3d", "c3g", "c4a", "c4c", "c4d", "c4e", "c4g", "c4h"]:
		var g := kit.story()
		kit.play_until(g, stage)
		var st: Dictionary = ENGINE.json_parse(g.save_json())["value"]
		kit.ok(Kit.strict_eq(SAVES.rebase_story(st), st), "a valid state after %s is unchanged" % stage)
	var done := {"completed_events": ["a1_completed", "slice_completed"], "current_scene": "L_X1_Montage"}
	kit.ok(Kit.strict_eq(SAVES.rebase_story(done), done), "a finished playthrough is unchanged")
	for odd in [{}, {"completed_events": "a1_completed", "current_scene": "L_A1_Railyard"},
			{"completed_events": ["a1_completed"]}]:
		kit.ok(Kit.strict_eq(SAVES.rebase_story(odd), odd), "odd shape unchanged: " + str(odd))
	return true


func _memory() -> bool:
	var m = MEM.new(TMP.path_join("profile.json"))
	m.data["completed"]["L_C3_Hall"] = {"t": 1.0, "story": _stale_after_c3b()}
	var raw: String = m.snapshot_raw("L_C3_Hall")
	var p: Dictionary = ENGINE.json_parse(raw)
	kit.eq(p["value"].get("current_scene"), "L_C3_RegistryA", "the recorded Hall snapshot is re-based")
	kit.ok(kit.story().validate_save_json(raw).get("ok", false), "and validates (menu memory and film stay usable)")
	return true


## A Story state as a round-8 build stored it right after c3g_completed (memory snapshot of the quay; the montage,
## nobody playing).
func _stale_after_c3g() -> Dictionary:
	var g := kit.story()
	kit.play_until(g, "c3g", {"c3g": "swap_halves"})
	var st: Dictionary = ENGINE.json_parse(g.save_json())["value"]
	st["current_scene"] = "L_X1_Montage"
	st["active_character"] = "none"
	return st


func _old_save_r8() -> bool:
	var stale := _stale_after_c3g()
	var g := kit.story()
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(stale, 2)).get("ok", false),
		"precondition: the round-8 form is invalid against the grown chain")
	var reb: Dictionary = SAVES.rebase_story(stale)
	kit.eq([reb.get("current_scene"), reb.get("active_character")], ["L_C4_TunnelsA", "alexei"],
		"re-based to the scene after c3g_completed (Karsk) and its protagonist")
	kit.eq(stale.get("current_scene"), "L_X1_Montage", "the input dictionary is not modified")
	kit.ok(g.validate_save_json(ENGINE.json_dumps(reb, 2)).get("ok", false), "the re-based state validates")
	var meta := {"version": SAVES.CONTAINER_VERSION, "timestamp": 1.0, "chapter_key": "ui.chapter_c3",
		"character": "none", "scene": "L_X1_Montage", "playtime_s": 2400.0, "label": ""}
	var path := TMP.path_join("old_r8.json")
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(ENGINE.json_dumps({"meta": meta, "story": stale, "extra": {}}, 1))
	f.close()
	var c: Dictionary = SAVES.read_container(path)
	if not kit.ok(c.get("ok", false), "container reads: " + str(c.get("error", ""))):
		return false
	kit.ok(str(c.get("warnings", [])).contains("re-based"), "the re-base is reported as a warning")
	var r: Dictionary = g.load_json(c["story_raw"])
	kit.ok(r.get("ok", false), "the round-8 save loads: " + str(r.get("error", "")))
	kit.eq([g.current_scene, g.active_character, g.available()], ["L_C4_TunnelsA", "alexei", ["c4a_inspect_shelf"]],
		"it continues in the Karsk cellar")
	kit.play_c4a(g)
	kit.play_c4b(g)
	kit.play_c4c(g)
	kit.play_c4d(g)
	for stage in ["c4e", "c4f", "c4g", "c4h"]:
		kit.play_stage(g, stage)
	kit.is_ok(g.finale(), "and plays on to the finale")
	return true


func _memory_r8() -> bool:
	var m = MEM.new(TMP.path_join("profile_r8.json"))
	m.data["completed"]["L_C3_Quay"] = {"t": 1.0, "story": _stale_after_c3g()}
	var raw: String = m.snapshot_raw("L_C3_Quay")
	var p: Dictionary = ENGINE.json_parse(raw)
	kit.eq(p["value"].get("current_scene"), "L_C4_TunnelsA", "the recorded quay snapshot is re-based")
	kit.ok(kit.story().validate_save_json(raw).get("ok", false), "and validates (menu memory of the quay stays usable)")
	return true


## A Story state as a round-9 build stored it right after c4d_completed (memory snapshot of the annex, or the montage):
## the montage, nobody playing, and no flag people_protected (flags.json of round 9 had sixteen flags).
func _stale_after_c4d() -> Dictionary:
	var g := kit.story()
	kit.play_until(g, "c4d", {"c3g": "hide_for_elena", "c4d": "protect_marta"})
	var st: Dictionary = ENGINE.json_parse(g.save_json())["value"]
	st["current_scene"] = "L_X1_Montage"
	st["active_character"] = "none"
	(st["flags"] as Dictionary).erase("people_protected")
	return st


func _old_save_r9() -> bool:
	var stale := _stale_after_c4d()
	var g := kit.story()
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(stale, 2)).get("ok", false),
		"precondition: the round-9 form is invalid against the grown chain and the grown flag table")
	var reb: Dictionary = SAVES.rebase_story(stale)
	kit.eq([reb.get("current_scene"), reb.get("active_character")], ["L_C4P2_KarskA", "alexei"],
		"re-based to the scene after c4d_completed (the Karsk depot) and its protagonist")
	kit.eq(reb["flags"].get("people_protected"), 0, "the flag the round-9 build did not know is filled with its default")
	kit.ok(not (stale["flags"] as Dictionary).has("people_protected"), "the input dictionary is not modified")
	kit.ok(g.validate_save_json(ENGINE.json_dumps(reb, 2)).get("ok", false), "the re-based state validates")
	var meta := {"version": SAVES.CONTAINER_VERSION, "timestamp": 1.0, "chapter_key": "ui.chapter_c4",
		"character": "none", "scene": "L_X1_Montage", "playtime_s": 3600.0, "label": ""}
	var path := TMP.path_join("old_r9.json")
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(ENGINE.json_dumps({"meta": meta, "story": stale, "extra": {}}, 1))
	f.close()
	var c: Dictionary = SAVES.read_container(path)
	if not kit.ok(c.get("ok", false), "container reads: " + str(c.get("error", ""))):
		return false
	kit.ok(str(c.get("warnings", [])).contains("re-based"), "the re-base is reported as a warning")
	kit.ok(str(c.get("warnings", [])).contains("people_protected"), "the flag fill is reported as a warning")
	var r: Dictionary = g.load_json(c["story_raw"])
	kit.ok(r.get("ok", false), "the round-9 save loads: " + str(r.get("error", "")))
	kit.eq([g.current_scene, g.active_character, g.available()],
		["L_C4P2_KarskA", "alexei", ["c4e_inspect_order", "c4e_inspect_list"]], "it continues at the Karsk depot")
	for stage in ["c4e", "c4f", "c4g", "c4h"]:
		kit.play_stage(g, stage, {"c4g": "protect_first"})
	kit.is_ok(g.finale(), "and plays on to the finale")
	kit.eq(g.flags()["people_protected"], 1, "protect_first raises the new meter on the migrated save")
	return true


func _memory_r9() -> bool:
	var m = MEM.new(TMP.path_join("profile_r9.json"))
	m.data["completed"]["L_C4_AnnexB"] = {"t": 1.0, "story": _stale_after_c4d()}
	var raw: String = m.snapshot_raw("L_C4_AnnexB")
	var p: Dictionary = ENGINE.json_parse(raw)
	kit.eq(p["value"].get("current_scene"), "L_C4P2_KarskA", "the recorded annex snapshot is re-based")
	kit.eq(p["value"]["flags"].get("people_protected"), 0, "and its missing flag filled")
	kit.ok(kit.story().validate_save_json(raw).get("ok", false), "and validates (menu memory of the annex stays usable)")
	var mf: Dictionary = m.memory_flags("L_C4_AnnexB", {}, {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence",
		"c3a_choose": "ask_elena", "c3b_choose": "share_protocol", "c3d_choose": "admit_plan", "c3g_choose": "hide_for_elena",
		"c4d_choose": "protect_marta"})
	kit.eq(mf.get("people_protected"), 0, "memory_flags of the snapshot know the new flag")
	return true
