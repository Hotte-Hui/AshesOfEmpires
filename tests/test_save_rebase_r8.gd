extends RefCounted
## Round 8: the story chain grew behind c3b_completed (it used to lead to the montage L_X1_Montage, now to the
## registry L_C3_RegistryA). Saves and memory snapshots taken at the end of the old chain continue in the scene that
## now follows their last completed event instead of failing the replay validation (SaveSystem.rebase_story, used by
## read_container and Memories.snapshot_raw). Valid current states, finished playthroughs and unknown shapes stay
## untouched.

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
	for stage in ["a1", "c3b", "c3d", "c3g"]:
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
