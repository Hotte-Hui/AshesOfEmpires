extends RefCounted
## „Erinnerungen“ (TECHNICAL_ARCHITECTURE §12.10): scene table and unlock rules, the global profile file
## (round trip, seeding from saves, broken files), read-only echo plans for every story hotspot, the memory
## grade overlay, a memory round trip on the live Game/Story/Explore autoloads (Story byte-identical after
## simulated interactions, safety-net restore, Explore finds kept, no autosave or manual save inside), the save
## guard of the save system, and the MemoryView / HUD badge / pause-menu entry / save screen built headless.
## Second-pass regressions: loading a save inside a memory is no Story leak, the save reason of a main-menu memory,
## main-menu films play with the recorded decisions, the arrival's film look stops with the memory, the badge never
## creeps left when it is shown again mid-slide, the eight-entry pause column fits a 1080-px screen.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const MEM := preload("res://scripts/core/memories.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const VIEW_SCENE := "res://scenes/ui/MemoryView.tscn"
const HUD_SCENE := "res://scenes/ui/HUD.tscn"
const PAUSE_SCENE := "res://scenes/ui/PauseMenu.tscn"
const SAVELOAD_SCENE := "res://scenes/ui/SaveLoadMenu.tscn"
const TMP := "user://test_memories"
const EXPECTED := [["L_A1_Railyard", "a1_completed", "alexei", 1, false],
	["L_M1_Archive", "m1_completed", "konrad", 2, false], ["L_M1_Plaza", "m1_completed", "konrad", 2, true],
	["L_C3_Station", "c3a_completed", "alexei", 3, false], ["L_C3_Hall", "c3b_completed", "konrad", 3, false],
	# Chapter 3 part 2 (C3P2_DESIGN.md): four registry scenes in one level file (each its own memory, opened with
	# its own protagonist, TECHNICAL_ARCHITECTURE §12.11) and the quay
	["L_C3_RegistryA", "c3c_completed", "alexei", 3, false], ["L_C3_RegistryB", "c3d_completed", "konrad", 3, false],
	["L_C3_RegistryC", "c3e_completed", "alexei", 3, false], ["L_C3_RegistryD", "c3f_completed", "konrad", 3, false],
	["L_C3_Quay", "c3g_completed", "alexei", 3, false],
	# Chapter 4 part 1 (C4_DESIGN.md §7): two level files, two scenes each, alternating between Karsk and Berlin
	["L_C4_TunnelsA", "c4a_completed", "alexei", 4, false], ["L_C4_AnnexA", "c4b_completed", "konrad", 4, false],
	["L_C4_TunnelsB", "c4c_completed", "alexei", 4, false], ["L_C4_AnnexB", "c4d_completed", "konrad", 4, false],
	# Chapter 4 part 2 (C4P2_DESIGN.md §7): again two level files, two scenes each, Karsk and Berlin alternating
	["L_C4P2_KarskA", "c4e_completed", "alexei", 4, false], ["L_C4P2_BerlinA", "c4f_completed", "konrad", 4, false],
	["L_C4P2_KarskB", "c4g_completed", "alexei", 4, false], ["L_C4P2_BerlinB", "c4h_completed", "konrad", 4, false]]
## Prints the lead makes after the art lands (C4_DESIGN §7, C4P2_DESIGN §7) — reported, not failed, while missing.
## Empty: the Chapter 4 prints exist since round 9, the four Chapter-4-part-2 prints since round 10 (lead), so every
## print is checked (exists, 320x180).
const PENDING_PRINTS: Array = []


class MockGame extends Node:
	var cards: Array = []
	var films: Array = [{"id": "LS_A1_ToM1", "unlocked": true, "title": "Abfahrt aus Karsk", "sub": "Kapitel 1 → 2"},
		{"id": "LS_M1_Hall", "unlocked": false, "title": "", "sub": ""}]
	var info: Dictionary = {}
	var travelled: Array = []
	var watched: Array = []
	var block := ""

	func memory_scenes(_context := "game") -> Array:
		return cards

	func memory_films(_context := "game") -> Array:
		return films

	func rewatch_film(id: String, from_menu := false) -> bool:
		watched.append([id, from_menu])
		return true

	func memory_info() -> Dictionary:
		return info

	func can_travel(_from_menu := false) -> bool:
		return true

	func travel_to_memory(id: String, from_menu := false) -> bool:
		travelled.append([id, from_menu])
		return true

	func save_block_key() -> String:
		return block


class MockSaves extends Node:
	var block := ""

	func list_slots() -> Array:
		return [{"slot": "1", "manual": true, "exists": true, "valid": true, "timestamp": 1.0, "chapter_key": "",
			"character": "alexei", "scene": "L_A1_Railyard", "playtime_s": 60.0, "label": ""},
			{"slot": "2", "manual": true, "exists": false, "valid": false}]

	func save(_slot) -> Dictionary:
		return {"ok": false, "error": "blocked", "error_key": block}

	func save_block_key() -> String:
		return block


var kit: TKit


func run() -> Array:
	kit = TKit.new()
	UIKit.overrides["Audio"] = null   # UI cues off (no one-shots alive at quit)
	DirAccess.make_dir_recursive_absolute(TMP)
	kit.run_case("scene_table_and_assets", _scene_table)
	kit.run_case("unlock_follows_exit_events", _unlock)
	kit.run_case("profile_round_trip_and_seeding", _profile)
	kit.run_case("profile_broken_files", _profile_broken)
	kit.run_case("echo_plans_read_only", _echo_plans)
	kit.run_case("memory_flags_of_the_playthrough", _memory_flags)
	kit.run_case("grade_overlay", _grade_overlay)
	kit.run_case("save_system_refuses_inside_a_memory", _save_guard)
	kit.run_case("round_trip_story_identical_finds_kept", _round_trip)
	kit.run_case("load_inside_a_memory_keeps_the_loaded_state", _end_state_after_load)
	kit.run_case("save_reason_of_a_main_menu_memory", _save_reason_menu)
	kit.run_case("menu_film_plays_with_the_recorded_decisions", _film_snapshot)
	kit.run_case("film_look_stops_with_the_memory", _film_look_stops)
	kit.run_case("a_new_present_never_keeps_the_side_level_flag", _side_level_reset)
	kit.run_case("game_memory_scenes_cards", _game_cards)
	kit.run_case("memory_cards_count_their_own_scene", _scene_counts)
	kit.run_case("memory_view_builds_and_navigates", _view)
	kit.run_case("hud_badge", _hud_badge)
	kit.run_case("pause_menu_entry", _pause_entry)
	kit.run_case("save_screen_explains_why", _save_screen)
	kit.run_case("drive_helpers_load", _drive)
	UIKit.overrides.erase("Game")
	UIKit.overrides.erase("Saves")
	UIKit.overrides.erase("Audio")
	kit.cleanup()
	UIKit.clear_cache()
	_rm_tree(TMP)
	return kit.failures


func _rm_tree(dir: String) -> void:
	var d := DirAccess.open(dir)
	if d == null:
		return
	for f in d.get_files():
		DirAccess.remove_absolute(dir.path_join(f))
	for sub in d.get_directories():
		_rm_tree(dir.path_join(sub))
	DirAccess.remove_absolute(dir)


# ------------------------------------------------------------------ scene table
func _scene_table() -> bool:
	var m = MEM.new(TMP + "/unused.json")
	var s: Array = m.scenes()
	kit.eq(s.size(), EXPECTED.size(), "%d walkable memory scenes (montage excluded)" % EXPECTED.size())
	for i in mini(s.size(), EXPECTED.size()):
		var e: Array = EXPECTED[i]
		kit.eq(str(s[i]["id"]), e[0], "scene %d id" % i)
		kit.eq(str(s[i]["unlock"]), e[1], "%s unlocks with %s" % [e[0], e[1]])
		kit.eq(str(s[i]["protagonist"]), e[2], "%s protagonist" % e[0])
		kit.eq(int(s[i]["chapter_no"]), e[3], "%s chapter number" % e[0])
		kit.eq(bool(s[i]["side"]), e[4], "%s side-level flag" % e[0])
		var thumb := str(s[i]["thumb"])
		if PENDING_PRINTS.has(e[0]) and not ResourceLoader.exists(thumb):
			print("      pending: memory print %s" % thumb)
		else:
			kit.ok(ResourceLoader.exists(thumb), "%s print exists (%s)" % [e[0], thumb])
		var tex = load(thumb) if ResourceLoader.exists(thumb) else null
		if tex is Texture2D:
			kit.eq((tex as Texture2D).get_size(), Vector2(320, 180), "%s print is 320x180" % e[0])
		kit.ok(MEM.has_text("ui.memories.place." + str(e[0])), "%s place text" % e[0])
		kit.ok(MEM.has_text("ui.memories.date." + str(e[0])), "%s date text" % e[0])
		kit.ok(m.chapter_line(str(e[0])).begins_with("Kapitel %d · " % e[3]), "%s chapter line" % e[0])
	kit.ok(not m.is_memory_scene("L_X1_Montage"), "the montage is not a memory")
	kit.ok(not m.is_memory_scene("L_M1_HallReveal"), "the hall cinematic is not a memory")
	kit.ok(ResourceLoader.exists("res://assets/ui/memories/icon_memory.png"), "badge icon exists")
	for snd in ["mem_rewind", "mem_return"]:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % snd), "sound %s exists" % snd)
	for k in ["ui.memories.title", "ui.memories.pause.open", "ui.memories.pause.return", "ui.memories.pause.return_menu",
			"ui.memories.badge", "ui.memories.badge_hint", "ui.memories.card.kicker", "ui.memories.card.present",
			"ui.memories.card.ended", "ui.memories.locked", "ui.memories.current", "sys.save.err.memory",
			"ui.memories.confirm_menu", "ui.memories.note.game", "ui.memories.note.menu", "ui.memories.menu"]:
		kit.ok(MEM.has_text(k), "string %s exists" % k)
	for k in ["ui.memories.prompt.inspect", "ui.memories.prompt.dialogue", "ui.memories.prompt.puzzle",
			"ui.memories.prompt.choice"]:
		kit.ok(MEM.has_text(k), "prompt %s exists" % k)
	return true


# ------------------------------------------------------------------ unlocks
func _unlock() -> bool:
	var m = MEM.new(TMP + "/unused.json")
	var g := kit.story()
	g.new_game()
	for s in m.scenes():
		kit.ok(not m.unlocked_by_story(str(s["id"]), g), "%s locked in a new game" % s["id"])
	kit.play_a1(g)
	kit.ok(m.unlocked_by_story("L_A1_Railyard", g), "Karsk unlocked after a1_completed")
	kit.ok(not m.unlocked_by_story("L_M1_Archive", g), "archive still locked after A1")
	kit.ok(not m.unlocked_by_story("L_M1_Plaza", g), "plaza still locked after A1")
	kit.play_m1(g)
	kit.ok(m.unlocked_by_story("L_M1_Archive", g), "archive unlocked after m1_completed")
	kit.ok(m.unlocked_by_story("L_M1_Plaza", g), "plaza unlocks with m1_completed")
	kit.ok(not m.unlocked_by_story("L_C3_Station", g), "station still locked")
	for seq in g.pending_cinematics():
		g.consume_cinematic(seq, true)
	kit.play_c3a(g)
	kit.ok(m.unlocked_by_story("L_C3_Station", g), "station unlocked after c3a_completed")
	kit.ok(not m.unlocked_by_story("L_C3_Hall", g), "palace still locked")
	kit.play_c3b(g)
	kit.ok(m.unlocked_by_story("L_C3_Hall", g), "palace unlocked after c3b_completed")
	kit.ok(not m.unlocked_by_story("nope", g), "unknown scene never unlocked")
	kit.ok(not m.unlocked_by_story("L_A1_Railyard", null), "no Story, no memory")
	return true


# ------------------------------------------------------------------ profile
func _profile() -> bool:
	var path := TMP + "/profile.json"
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	var m = MEM.new(path)
	m.load_profile()
	kit.ok(not m.any(), "no file: empty profile")
	kit.eq(m.last_error, "", "a missing file is no error")
	var g := kit.story()
	g.new_game()
	kit.play_a1(g)
	var a1_raw: String = g.save_json()
	kit.ok(m.record("L_A1_Railyard", a1_raw), "record Karsk")
	kit.ok(not m.record("L_X1_Montage", a1_raw), "the montage is never recorded")
	kit.ok(not m.record("L_M1_Archive", "{broken"), "a broken Story text is never recorded")
	kit.ok(m.merge_explore({"found": ["karsk.cat", "karsk.crows"], "cards": ["hist.soviet.gulag"]}), "merge finds")
	kit.ok(not m.merge_explore({"found": ["karsk.cat"], "cards": []}), "merging known finds changes nothing")
	kit.ok(m.merge_explore({"found": ["berlin.mouse", "karsk.cat"]}), "merge appends new ids")
	kit.eq(m.explore_state()["found"], ["karsk.cat", "karsk.crows", "berlin.mouse"], "union keeps the find order")
	kit.ok(m.save_profile(), "profile written")
	kit.ok(not FileAccess.file_exists(path + ".tmp"), "no .tmp left behind (atomic write)")
	var m2 = MEM.new(path)
	m2.load_profile()
	kit.eq(m2.last_error, "", "profile reads back")
	kit.eq(m2.completed_ids(), ["L_A1_Railyard"], "completed scenes read back")
	kit.eq(m2.explore_state(), m.explore_state(), "finds read back")
	var snap: String = m2.snapshot_raw("L_A1_Railyard")
	kit.eq(snap, a1_raw, "recorded Story state reads back byte-identical")
	kit.is_ok(g.validate_save_json(snap), "recorded Story state validates")
	kit.eq(m2.snapshot_raw("L_M1_Archive"), "", "no snapshot for an unrecorded scene")
	# seeding from a later save: only missing scenes are added, recorded ones are never replaced
	kit.play_m1(g)
	var m1_raw: String = g.save_json()
	kit.eq(m2.seed_from_story(m1_raw), 2, "seed adds the archive and the plaza")
	kit.eq(m2.snapshot_raw("L_A1_Railyard"), a1_raw, "seed keeps the snapshot recorded at completion")
	kit.eq(m2.snapshot_raw("L_M1_Plaza"), m1_raw, "the plaza is seeded with the archive's state")
	kit.eq(m2.seed_from_story(m1_raw), 0, "seeding twice adds nothing")
	kit.eq(m2.seed_from_story("not json"), 0, "seeding from garbage adds nothing")
	# record of a parent scene also records its side level
	var m3 = MEM.new(TMP + "/p3.json")
	m3.record("L_M1_Archive", m1_raw)
	kit.ok(m3.unlocked_by_profile("L_M1_Plaza"), "recording the archive records the plaza too")
	m3.clear()
	kit.ok(not m3.any(), "clear() empties the profile")
	return true


func _profile_broken() -> bool:
	var path := TMP + "/broken.json"
	for content in ["{not json", "[]", "{\"version\": 99, \"completed\": {}}",
			"{\"version\": 1, \"completed\": {\"L_A1_Railyard\": 5, \"Nowhere\": {\"story\": {}}}, \"explore\": 3}"]:
		var f := FileAccess.open(path, FileAccess.WRITE)
		f.store_string(content)
		f.close()
		var m = MEM.new(path)
		m.load_profile()
		kit.ok(not m.any(), "broken profile %s loads as empty" % content.substr(0, 24))
		kit.eq(m.explore_state(), {"found": [], "cards": []}, "broken profile has no finds")
	var f2 := FileAccess.open(path, FileAccess.WRITE)
	f2.store_string("{\"version\": 1.0, \"completed\": {}}")
	f2.close()
	var m2 = MEM.new(path)
	m2.load_profile()
	kit.ne(m2.last_error, "", "a float version is reported")
	# a big file is refused before parsing
	var f3 := FileAccess.open(path, FileAccess.WRITE)
	f3.store_string("{\"pad\": \"" + "x".repeat(MEM.MAX_PROFILE_BYTES + 10) + "\"}")
	f3.close()
	var m3 = MEM.new(path)
	m3.load_profile()
	kit.eq(m3.last_error, "profile too large", "oversized profile refused")
	DirAccess.remove_absolute(path)
	return true


# ------------------------------------------------------------------ echo plans
func _echo_plans() -> bool:
	var m = MEM.new(TMP + "/unused.json")
	var g := kit.story()
	g.new_game()
	kit.play_until(g, "c4h", {"a1": "keep_private", "c3a": "note_alone", "c3b": "report_delegation", "c3d": "pocket_plan",
		"c3g": "hide_for_elena", "c4d": "protect_marta", "c4g": "protect_first"})
	var before: String = g.save_json()
	var live_before: String = Story.save_json()
	var game_script = load("res://scripts/core/game.gd")
	var ext = load("res://scripts/core/chapter_ext.gd").new()
	var ctx := {"protagonist": "alexei", "choices": g.choice_history(), "flags": g.flags(), "ext": ext,
		"reactions": game_script.REACTIONS, "line_expr": game_script.LINE_EXPR}
	var qd = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/v3/quests.json"))["value"]
	var dd = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/v3/dialogue.json"))["value"]
	var conv := {}
	for c in dd["conversations"]:
		conv[c["id"]] = c
	var n := 0
	for q in qd["quests"]:
		for o in q["objectives"]:
			var steps: Array = m.echo_plan([o["id"]], ctx)
			n += 1
			kit.ok(not steps.is_empty(), "%s has a memory echo" % o["id"])
			for s in steps:
				if str(s["type"]) == "line":
					kit.ok(str(s["text"]) != "" and not str(s["text"]).begins_with("["), "%s: line text resolves (%s)" % [o["id"], s["key"]])
					kit.ok(str(s["speaker"]) != "", "%s: line has a speaker" % o["id"])
			match str(o["type"]):
				"inspect":
					kit.eq(steps[0]["type"], "inspect", "%s shows its document" % o["id"])
					kit.eq(steps[0]["item"], o.get("grant_item", ""), "%s document = its evidence item" % o["id"])
				"dialogue":
					kit.eq(steps.size(), (conv[o["dialogue_id"]]["nodes"] as Array).size(), "%s replays every line" % o["id"])
				"choice":
					kit.ok(steps.size() >= 1, "%s remembers the decision" % o["id"])
					kit.eq(str(steps[0]["key"]), "ui.memories.decided." + str(g.choice_history()[o["id"]]),
						"%s names the decision that was taken" % o["id"])
				"puzzle":
					kit.eq(steps.size(), 1, "%s: one line remembering the puzzle" % o["id"])
					kit.eq(str(steps[0]["key"]), "ui.memories.echo." + str(o["id"]), "%s has its own memory line" % o["id"])
	kit.ok(n >= 24, "every objective of the chain was checked (%d)" % n)
	# a conversation and the choice taken with the same person: one hotspot, dialogue first, then the decision
	var merged: Array = m.echo_plan(["a1_choose", "a1_talk_irina"], ctx)
	kit.eq(str(merged[0]["key"]), "dlg.irina.01", "merged twin starts with the conversation")
	kit.eq(str(merged[merged.size() - 2]["key"]), "ui.memories.decided.keep_private", "…then what was decided")
	kit.eq(str(merged[merged.size() - 1]["key"]), "dlg.irina.branch_b", "…then the answer that followed")
	# flag-dependent variants are resolved with the flags of the playthrough
	var c3: Array = m.echo_plan(["c3a_talk_conductor"], ctx)
	kit.eq(str(c3[1]["key"]), "dlg.c3.cond_02.secrecy", "variant line of the secrecy route")
	var r: Array = m.echo_plan(["c3b_choose"], ctx)
	kit.ok(str(r[r.size() - 1]["key"]).begins_with("dlg.c3.react.report_delegation"), "reaction variant of the route")
	kit.eq(g.save_json(), before, "building every plan leaves the Story state byte-identical")
	kit.eq(Story.save_json(), live_before, "…and the live Story autoload untouched")
	# no choice recorded (cannot happen in a completed scene): a neutral memory line, never a decision UI
	var none: Array = m.echo_plan(["a1_choose"], {"protagonist": "alexei", "choices": {}, "flags": {}})
	kit.eq(str(none[0]["key"]), "ui.memories.decided_none", "unknown decision → neutral line")
	return true


func _memory_flags() -> bool:
	var m = MEM.new(TMP + "/unused.json")
	var g := kit.story()
	g.new_game()
	kit.play_until(g, "c3a", {"c3a": "note_alone"})
	m.record("L_C3_Station", g.save_json())
	var at_station: Dictionary = g.flags()
	for seq in g.pending_cinematics():
		g.consume_cinematic(seq, true)
	kit.play_c3b(g, "search_elena")   # elena_trust +1 AFTER the station
	kit.ne(g.flags().get("elena_trust"), at_station.get("elena_trust"), "a later choice changed a flag")
	kit.eq(m.memory_flags("L_C3_Station", g.flags(), g.choice_history()), at_station,
		"the station is remembered with the flags it was played with")
	var other: Dictionary = g.choice_history()
	other["a1_choose"] = "share_with_irina" if str(other["a1_choose"]) != "share_with_irina" else "keep_private"
	kit.eq(m.memory_flags("L_C3_Station", g.flags(), other), g.flags(), "another playthrough: live flags")
	kit.eq(m.memory_flags("L_A1_Railyard", g.flags(), g.choice_history()), g.flags(), "no snapshot: live flags")
	return true


# ------------------------------------------------------------------ grade
func _grade_overlay() -> bool:
	var grades = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/grades.json"))["value"]
	kit.ok(grades.has("memory"), "data/grades.json has a memory preset")
	var mem: Dictionary = grades.get("memory", {})
	for k in ["lift", "gain", "tint", "saturation", "vignette", "grain"]:
		kit.ok(mem.has(k), "memory preset field " + k)
	var karsk: Dictionary = grades["karsk"]
	var o: Dictionary = MEM.overlay_grade(karsk, mem)
	kit.ok(is_equal_approx(float(o["saturation"]), float(karsk["saturation"]) * float(mem["saturation"])), "saturation multiplies")
	kit.ok(float(o["saturation"]) < 0.5, "a memory is clearly desaturated")
	kit.ok(is_equal_approx(float(o["lift"][0]), float(karsk["lift"][0]) + float(mem["lift"][0])), "lift adds")
	kit.ok(is_equal_approx(float(o["tint"][2]), float(karsk["tint"][2]) * float(mem["tint"][2])), "tint multiplies")
	kit.ok(float(o["tint"][0]) > float(o["tint"][2]), "warm: more red than blue")
	kit.eq(float(o["vignette"]), maxf(float(karsk["vignette"]), float(mem["vignette"])), "vignette = max")
	kit.ok(is_equal_approx(float(o["grain"]), float(karsk["grain"]) + float(mem["grain"])), "grain adds")
	kit.eq(o["palette"], karsk["palette"], "palette of the level kept")
	kit.eq(o["palette_strength"], karsk["palette_strength"], "palette snap of the level kept")
	kit.eq(MEM.overlay_grade(karsk, {}), karsk, "an empty overlay changes nothing")
	var v: Dictionary = MEM.grade_values(o)
	kit.ok(v["lift"] is Vector3 and v["tint"] is Vector3, "shader values are vectors")
	var half: Dictionary = MEM.lerp_values(MEM.grade_values(karsk), v, 0.5)
	kit.ok(float(half["saturation"]) < float(karsk["saturation"]) and float(half["saturation"]) > float(o["saturation"]),
		"the transition blends between the two")
	return true


# ------------------------------------------------------------------ save system guard
func _save_guard() -> bool:
	var s: Node = kit.saves()
	s.base_dir = TMP + "/saves"
	var g := kit.story()
	g.new_game()
	s.story = g
	var block := ["sys.save.err.memory"]
	s.block_provider = func() -> String: return block[0]
	var r: Dictionary = s.save("1")
	kit.ok(not r.get("ok", true), "manual save refused inside a memory")
	kit.eq(r.get("error_key", ""), "sys.save.err.memory", "refusal names the memory reason")
	kit.ok(not FileAccess.file_exists(TMP + "/saves/1.json"), "no file written")
	kit.ok(not s.autosave("x").get("ok", true), "autosave refused")
	kit.ok(not s.quicksave().get("ok", true), "quicksave refused")
	kit.ok(not FileAccess.file_exists(TMP + "/saves/auto.json"), "no autosave file")
	block[0] = ""
	kit.is_ok(s.save("1"), "saving works again outside the memory")
	kit.ok(FileAccess.file_exists(TMP + "/saves/1.json"), "file written after the memory")
	s.delete("1")
	return true


# ------------------------------------------------------------------ live round trip (Game/Story/Explore autoloads)
func _round_trip() -> bool:
	var game: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if not kit.ok(game != null and game.has_method("travel_to_memory"), "Game autoload with the memory API"):
		return true
	var keep_story: String = Story.save_json()
	var keep_explore: Dictionary = Explore.state()
	var keep_path: String = game.memories.path
	var keep_base: String = Saves.base_dir
	game.memories.path = TMP + "/live_profile.json"
	Saves.base_dir = TMP + "/live_saves"
	# a present in Chapter 3 (A1 + M1 complete)
	Story.new_game()
	Explore.reset()
	kit.play_a1(Story)
	kit.play_m1(Story)
	for seq in Story.pending_cinematics():
		Story.consume_cinematic(seq, true)
	var present: String = Story.save_json()
	kit.ok(not game.memory_mode, "not in a memory at the start")
	# inside (what travel_to_memory sets up, without loading a level)
	game._mem_present = {"story": present, "inside": present, "from_menu": false, "level": "", "side_level": false}
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	kit.eq(game.save_block_key(), "sys.save.err.memory", "Game names the reason saving is blocked")
	kit.eq(Saves.save_block_key(), "sys.save.err.memory", "Saves asks Game")
	var sr: Dictionary = Saves.save("1")
	kit.eq(sr.get("error_key", ""), "sys.save.err.memory", "manual save refused inside the memory")
	game.autosave("inside")
	kit.ok(not FileAccess.file_exists(TMP + "/live_saves/auto.json"), "no autosave inside the memory")
	# every Story path of the director returns at its guard (synchronously, before any await)
	var it = load("res://scripts/actors/interactable.gd").new()
	for pair in [["inspect", "a1_inspect_seal"], ["dialogue", "a1_talk_irina"], ["puzzle", "a1_solve_signal"],
			["choice", "a1_choose"]]:
		it.kind = pair[0]
		it.objective_id = pair[1]
		match pair[0]:
			"inspect":
				game._do_inspect(it)
			"dialogue":
				game._do_dialogue(it)
			"puzzle":
				game._do_puzzle(it)
			"choice":
				game._do_choice(it)
	game._after_story_change()      # cinematics and scene changes stay off inside a memory
	game.goto_level("L_X1_Montage")  # the finale never starts inside a memory
	game._play_cinematic_by_id("LS_A1_ToM1")
	kit.ok(not game.in_cinematic, "no cinematic started inside the memory")
	kit.eq(Story.pending_cinematics().size(), 0, "no cinematic queued or consumed")
	# the echo plans the twins use
	var plan: Array = game.memories.echo_plan(["a1_talk_irina", "a1_choose"], {"protagonist": "alexei",
		"choices": Story.choice_history(), "flags": Story.flags(), "ext": game.ext, "reactions": game.REACTIONS,
		"line_expr": game.LINE_EXPR})
	kit.ok(plan.size() >= 6, "twin plan: the conversation and the decision")
	# exploration works normally inside and is kept
	var fr: Dictionary = Explore.find("karsk.cat")
	kit.ok(fr.get("ok", false), "a find inside the memory")
	kit.eq(Story.save_json(), present, "Story byte-identical after the simulated interactions")
	game._end_memory_state()
	kit.ok(not game.memory_mode, "memory mode left")
	kit.eq(Story.save_json(), present, "Story byte-identical after the round trip")
	kit.ok(Explore.is_found("karsk.cat"), "the find made inside the memory is kept")
	kit.eq(game.save_block_key(), "", "saving allowed again")
	# safety net: a Story change that slipped through inside a memory is undone on return
	game._mem_present = {"story": present, "inside": present, "from_menu": false}
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	Story.new_game()   # simulated leak (warning expected)
	kit.ne(Story.save_json(), present, "simulated leak changed the state")
	game._end_memory_state()
	kit.eq(Story.save_json(), present, "safety net restores the present byte-identically")
	# a memory from the main menu: the menu's Story and Explore states come back
	var menu_state: String = Story.save_json()
	var menu_explore: Dictionary = Explore.state()
	game.memories.record("L_A1_Railyard", present)
	game._mem_present = {"story": menu_state, "inside": game.memories.snapshot_raw("L_A1_Railyard"),
		"from_menu": true, "explore": menu_explore}
	Story.load_json(game.memories.snapshot_raw("L_A1_Railyard"))
	Explore.restore({"found": ["karsk.cat", "karsk.crows"], "cards": []})
	game.memory_mode = true
	game.memory_from_menu = true
	game.memory_scene = "L_A1_Railyard"
	game._end_memory_state()
	kit.eq(Story.save_json(), menu_state, "menu memory: the menu's Story state is back")
	kit.eq(Explore.state(), menu_explore, "menu memory: the menu's Explore state is back")
	kit.ok(not game.memory_from_menu, "menu flag cleared")
	# no profile writes from tests (no Main scene): the player's file is never touched
	kit.ok(not game._profile_writes(), "unit tests never write the player's profile")
	kit.ok(not FileAccess.file_exists(TMP + "/live_profile.json"), "…not even the redirected one")
	# restore the autoloads
	it.free()
	game.memories.path = keep_path
	game.memories.load_profile()
	Saves.base_dir = keep_base
	_restore_story(keep_story)
	Explore.restore(keep_explore)
	return true


func _restore_story(raw: String) -> void:
	if raw != "" and Story.load_json(raw).get("ok", false):
		return
	Story.new_game()


# ------------------------------------------------------------------ second-pass regressions (review)
func _game() -> Node:
	return (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")


## Loading a save inside a memory makes it the new present: memory mode ends WITHOUT the safety net (the old
## present is not put back and no "Story state changed inside a memory" leak is reported); a real leak is still
## undone and counted.
func _end_state_after_load() -> bool:
	var game := _game()
	if not kit.ok(game != null and "_mem_leaks" in game, "Game autoload counts safety-net restores"):
		return true
	var keep_story: String = Story.save_json()
	var keep_explore: Dictionary = Explore.state()
	var keep_data: Dictionary = (game.memories.data as Dictionary).duplicate(true)
	Story.new_game()
	kit.play_a1(Story)
	var present: String = Story.save_json()
	game._mem_present = {"story": present, "inside": present, "from_menu": false, "level": "", "side_level": false}
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	Story.new_game()                 # what Saves.load() did before Game._on_loaded_slot() ends the memory
	var loaded: String = Story.save_json()
	var leaks0: int = game._mem_leaks
	game._end_memory_state(false)
	kit.ok(not game.memory_mode, "memory mode ends when a save is loaded")
	kit.eq(Story.save_json(), loaded, "the loaded save stays the present (the old present is not put back)")
	kit.eq(game._mem_leaks, leaks0, "loading a save is no Story leak (no safety-net warning)")
	game._mem_present = {"story": present, "inside": present, "from_menu": false}
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	Story.new_game()                 # simulated leak (warning expected)
	game._end_memory_state()
	kit.eq(Story.save_json(), present, "a real leak is undone")
	kit.eq(game._mem_leaks, leaks0 + 1, "…and counted")
	game._mem_leaks = leaks0
	game.memories.data = keep_data
	_restore_story(keep_story)
	Explore.restore(keep_explore)
	return true


## A memory opened from the main menu has no present to return to and its finds reach no save: the save screen
## must not tell the player to return to the present first so that the finds are secured.
func _save_reason_menu() -> bool:
	var game := _game()
	if game == null:
		return true
	var keep := [game.memory_mode, game.memory_from_menu]
	game.memory_mode = true
	game.memory_from_menu = false
	kit.eq(game.save_block_key(), "sys.save.err.memory", "in-game memory: return first, the finds are secured then")
	game.memory_from_menu = true
	var k: String = game.save_block_key()
	var own := Loc.has("sys.save.err.memory_menu")
	kit.eq(k, "sys.save.err.memory_menu" if own else "sys.save.err.memory", "main-menu memory: its own reason")
	kit.ok(Loc.has(k), "the reason resolves to a text")
	if own:
		kit.ok(not Loc.t(k).contains("Gegenwart"), "…which does not send the player to a present that is not there")
	game.memory_mode = false
	kit.eq(game.save_block_key(), "", "outside a memory saving is allowed")
	game.memory_mode = keep[0]
	game.memory_from_menu = keep[1]
	return true


## From the main menu a film is played with the Story state of the playthrough in which it was seen (decisions,
## flags): the first profile snapshot (story order) whose state contains the film's trigger — not the menu's own
## state (after a fresh start it knows no decision, the cinematics would show their default variants).
func _film_snapshot() -> bool:
	var game := _game()
	if not kit.ok(game != null and game.has_method("_film_snapshot"), "Game._film_snapshot exists"):
		return true
	var keep_path: String = game.memories.path
	var keep_data: Dictionary = (game.memories.data as Dictionary).duplicate(true)
	var keep_story: String = Story.save_json()
	game.memories.path = TMP + "/film_profile.json"
	game.memories.clear()
	var g := kit.story()
	g.new_game()
	kit.play_a1(g, "keep_private")
	var a1_raw: String = g.save_json()
	game.memories.record("L_A1_Railyard", a1_raw)
	kit.play_m1(g, "request_explanation")
	var m1_raw: String = g.save_json()
	game.memories.record("L_M1_Archive", m1_raw)
	kit.eq(game._film_snapshot("LS_A1_ToM1"), a1_raw, "the departure from Karsk: the state when Karsk was completed")
	kit.eq(game._film_snapshot("LS_M1_Hall"), m1_raw, "the Great Hall (trigger objective): the archive's state")
	kit.eq(game._film_snapshot("LS_X1_Final"), m1_raw, "the two desks: both decisions known")
	kit.eq(game._film_snapshot("LS_C3_Close"), "", "a film never seen: no state")
	kit.eq(game._film_snapshot("nope"), "", "unknown film: no state")
	var open := {}
	for f in game.memory_films("menu"):
		open[str(f["id"])] = bool(f["unlocked"])
	kit.ok(bool(open.get("LS_A1_ToM1", false)) and bool(open.get("LS_X1_Final", false)), "recorded films are offered")
	kit.ok(not bool(open.get("LS_C3_Close", true)), "films of unrecorded scenes stay locked")
	kit.eq(Story.save_json(), keep_story, "choosing the state never touches the live Story")
	kit.ok(not FileAccess.file_exists(TMP + "/film_profile.json"), "nothing written")
	game.memories.path = keep_path
	game.memories.data = keep_data
	return true


## The film look (flicker, scratches, dust) of an arrival fades out by a tween; leaving the memory before it has
## ended must stop it — otherwise it comes back over the main menu (CanvasLayer 89 lies above every panel).
func _film_look_stops() -> bool:
	var game := _game()
	if not kit.ok(game != null and game.has_method("_mem_film_stop"), "Game._mem_film_stop exists"):
		return true
	var keep_story: String = Story.save_json()
	var keep_data: Dictionary = (game.memories.data as Dictionary).duplicate(true)
	game._mem_film_set(0.5)
	game._mem_film_fade(1.4)
	var tw: Tween = game._mem_film_tween
	kit.ok(tw != null and tw.is_valid(), "the arrival's film fade runs")
	game._mem_present = {"story": keep_story, "inside": keep_story, "from_menu": false}
	game.memory_mode = true
	game._end_memory_state()
	kit.ok(tw == null or not tw.is_valid(), "leaving the memory stops the fade (it cannot bring the film back)")
	kit.eq(game._mem_film_level, 0.0, "film look off")
	kit.eq(Story.save_json(), keep_story, "Story untouched")
	game.memories.data = keep_data
	return true


## Game.side_level (the parade plaza) gates every scene change in _after_story_change(); memories save and restore
## it with the present. A new game or a loaded save always starts in the Story scene chain, so both reset it — a
## flag left over from the plaza (plaza → Hauptmenü / Laden) soft-locked the end of the archive (the level stayed
## L_M1_Archive while Story moved on to L_C3_Station). The flows need Main (fades), so this checks the source;
## the behaviour was verified with a windowed run (save on the plaza → load → m1_completed → L_C3_Station).
func _side_level_reset() -> bool:
	var src := FileAccess.get_file_as_string("res://scripts/core/game.gd")
	for fn in ["_on_new_game", "_on_loaded_slot"]:
		var at := src.find("\nfunc %s(" % fn)
		var body := src.substr(at, src.find("\nfunc ", at + 1) - at) if at >= 0 else ""
		kit.ok(body.contains("\tside_level = false"), "%s() resets side_level (starts in the Story scene chain)" % fn)
	return true


func _game_cards() -> bool:
	var game: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if game == null:
		return true
	var keep_story: String = Story.save_json()
	Story.new_game()
	kit.play_a1(Story)
	var cards: Array = game.memory_scenes("game")
	kit.eq(cards.size(), EXPECTED.size(), "one card per memory scene")
	kit.ok(bool(cards[0]["unlocked"]) and str(cards[0]["place"]) != "", "Karsk card open with its place")
	kit.ok(int(cards[0]["total"]) > 0, "Karsk card counts its finds")
	for i in range(1, cards.size()):
		kit.ok(not bool(cards[i]["unlocked"]), "%s locked" % cards[i]["id"])
		kit.eq(str(cards[i]["place"]) + str(cards[i]["chapter"]) + str(cards[i]["thumb"]), "", "%s: no spoilers" % cards[i]["id"])
	kit.ok(not game.can_travel(false), "no travel without a level (tests)")
	kit.ok(not game.travel_to_memory("L_M1_Archive", false), "locked scene: no travel")
	# films: unlocked by their trigger, in story order, only when the scene exists
	var films: Array = game.memory_films("game")
	var ids: Array = []
	for f in films:
		ids.append(str(f["id"]))
	kit.eq(ids.slice(0, 3), ["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final"], "films in story order")
	kit.ok(bool(films[0]["unlocked"]) and str(films[0]["title"]) != "", "the departure from Karsk was seen after A1")
	kit.ok(not bool(films[1]["unlocked"]) and str(films[1]["title"]) == "", "the Great Hall not yet (no spoiler)")
	Story.inspect("m1_inspect_plan_a")
	Story.inspect("m1_inspect_plan_b")
	Story.solve_puzzle("m1_align_plans", kit.M1_OVERLAY.duplicate())
	kit.ok(bool(game.memory_films("game")[1]["unlocked"]), "the Great Hall film unlocks with its trigger objective")
	kit.ok(not game.rewatch_film("LS_X1_Final", false), "an unseen film cannot be started")
	kit.ok(not game.rewatch_film("LS_A1_ToM1", false), "no film without a running level (tests)")
	for f in game.memory_films("game"):
		kit.ok(MEM.has_text("ui.memories.film." + str(f["id"])), "film %s has a title" % f["id"])
	_restore_story(keep_story)
	return true


## Round 9: a card counts the finds of its own scene (Game.memory_scenes). In a level file shared by several Story
## scenes an Explore entry naming its "scene" counts on that scene's card only (the C4 tunnels and annex: each card
## its own walk area, not the file's 22 / 18); entries without one (the registry) count on every card of the file —
## in the running game (Explore state) and from the main menu (the profile's finds) alike.
func _scene_counts() -> bool:
	var game := _game()
	if game == null or not game.has_method("memory_scenes"):
		return true
	var keep_story: String = Story.save_json()
	var keep_explore: Dictionary = Explore.state()
	var keep_notify: bool = Explore.notify_tasks
	var keep_data: Dictionary = (game.memories.data as Dictionary).duplicate(true)
	Explore.notify_tasks = false
	Story.new_game()
	kit.play_until(Story, "c4d")
	# what each card should count, straight from the Explore data: the two scenes of each C4 file
	var files := {"L_C4_TunnelsA": ["L_C4_TunnelsA", "L_C4_TunnelsB"], "L_C4_AnnexA": ["L_C4_AnnexA", "L_C4_AnnexB"]}
	var mine := {}
	for key in files:
		kit.eq(str(game.ext.level_key(str(files[key][1]))), key, "%s counts under the level key %s" % [files[key][1], key])
		var all: Array = Explore.entries_for(key)
		for sid in files[key]:
			mine[sid] = []
			for e in all:
				if str(e.get("scene", "")) == sid:
					mine[sid].append(str(e["id"]))
			kit.ok((mine[sid] as Array).size() >= 2, "%s has finds of its own (%d)" % [sid, (mine[sid] as Array).size()])
		kit.eq((mine[files[key][0]] as Array).size() + (mine[files[key][1]] as Array).size(), all.size(),
			"%s: every find names one of the file's two scenes" % key)
	var reg_key := str(game.ext.level_key("L_C3_RegistryD"))
	var reg: Array = Explore.entries_for(reg_key)
	kit.ok(not reg.is_empty() and not (reg[0] as Dictionary).has("scene"), "the registry's finds name no scene (%d)" % reg.size())
	# one find in the cellar, two at the siding, one at the tram loop, none in the annex, one in the registry
	var found: Array = [mine["L_C4_TunnelsA"][0], mine["L_C4_TunnelsB"][0], mine["L_C4_TunnelsB"][1],
		mine["L_C4_AnnexA"][0], str(reg[0]["id"]) if not reg.is_empty() else ""]
	var want := {"L_C4_TunnelsA": [1, (mine["L_C4_TunnelsA"] as Array).size()],
		"L_C4_TunnelsB": [2, (mine["L_C4_TunnelsB"] as Array).size()],
		"L_C4_AnnexA": [1, (mine["L_C4_AnnexA"] as Array).size()], "L_C4_AnnexB": [0, (mine["L_C4_AnnexB"] as Array).size()]}
	for sid in ["L_C3_RegistryA", "L_C3_RegistryB", "L_C3_RegistryC", "L_C3_RegistryD"]:
		want[sid] = [1, reg.size()]       # the whole file on every card, as before
	Explore.restore({"found": found, "cards": []})
	_check_counts(game.memory_scenes("game"), want, "game")
	# the main menu: every scene completed once, the profile's finds (the running Explore state is not read)
	var prof := {"version": 1, "completed": {}, "explore": {"found": found.duplicate(), "cards": []}}
	for sid in want:
		prof["completed"][sid] = {"t": 0.0, "story": {}}
	game.memories.data = prof
	Explore.restore({"found": [], "cards": []})
	_check_counts(game.memory_scenes("menu"), want, "menu")
	game.memories.data = keep_data
	_restore_story(keep_story)
	Explore.restore(keep_explore)
	Explore.notify_tasks = keep_notify
	return true


func _check_counts(cards: Array, want: Dictionary, ctx: String) -> void:
	var got := {}
	for c in cards:
		got[str(c.get("id", ""))] = c
	for sid in want:
		var c: Dictionary = got.get(sid, {})
		if not kit.ok(bool(c.get("unlocked", false)), "%s card unlocked (%s)" % [sid, ctx]):
			continue
		kit.eq([int(c.get("found", -1)), int(c.get("total", -1))], want[sid], "%s card (%s): found / total of its scene" % [sid, ctx])


# ------------------------------------------------------------------ UI built headless
func _mock_game() -> MockGame:
	var g: MockGame = kit.track(MockGame.new())
	g.cards = [
		{"id": "L_A1_Railyard", "unlocked": true, "current": false, "place": "Verladebahnhof Karsk", "date": "Januar 1964",
			"chapter": "Kapitel 1 · Das letzte Signal", "who": "alexei", "thumb": "res://assets/ui/memories/L_A1_Railyard.png",
			"found": 3, "total": 25},
		{"id": "L_M1_Archive", "unlocked": true, "current": false, "place": "Berliner Bauarchiv", "date": "Januar 1964",
			"chapter": "Kapitel 2 · Die falsche Zeichnung", "who": "konrad", "thumb": "res://assets/ui/memories/L_M1_Archive.png",
			"found": 0, "total": 28},
		{"id": "L_M1_Plaza", "unlocked": true, "current": true, "place": "Platz", "date": "", "chapter": "Kapitel 2",
			"who": "konrad", "thumb": "res://assets/ui/memories/L_M1_Plaza.png", "found": 0, "total": 21},
		{"id": "L_C3_Station", "unlocked": false, "current": false, "place": "", "date": "", "chapter": "", "who": "",
			"thumb": "", "found": 0, "total": 0},
		{"id": "L_C3_Hall", "unlocked": false, "current": false, "place": "", "date": "", "chapter": "", "who": "",
			"thumb": "", "found": 0, "total": 0}]
	UIKit.overrides["Game"] = g
	return g


func _mount(path: String) -> Control:
	var c: Control = (load(path) as PackedScene).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(c)
	return kit.track(c)


func _labels_text(root: Node) -> String:
	var out := ""
	for l in root.find_children("*", "Label", true, false):
		out += (l as Label).text + "|"
	return out


func _view() -> bool:
	var g := _mock_game()
	var v: Control = _mount(VIEW_SCENE)
	v.open("game")
	kit.ok(v.is_open, "MemoryView opens")
	kit.eq(v.cards.size(), 5, "five cards (the mock game's)")
	kit.eq(TKit.sorted(v.buttons), ["L_A1_Railyard", "L_M1_Archive"], "only unlocked, non-current cards can be chosen")
	var text := _labels_text(v)
	kit.ok(text.contains("Verladebahnhof Karsk") and text.contains("3 / 25"), "unlocked card shows place and finds")
	kit.ok(text.contains(UIKit.t("ui.memories.locked").to_upper()), "locked cards say „Noch nicht erlebt“")
	kit.ok(text.contains(UIKit.t("ui.memories.current")), "the current scene is marked")
	kit.ok(not text.contains("Bahnhof Veltrava"), "locked cards reveal nothing")
	kit.ok(v.select("L_M1_Archive"), "select a card")
	kit.eq(v.selected(), "L_M1_Archive", "selection follows")
	kit.ok(not v.select("L_C3_Station"), "a locked card cannot be selected")
	kit.ok(not v.select("L_M1_Plaza"), "the current scene cannot be selected")
	kit.ok(not v.activate("L_C3_Hall"), "a locked card does not travel")
	kit.ok(v.activate("L_A1_Railyard"), "an unlocked card travels")
	kit.eq(g.travelled, [["L_A1_Railyard", false]], "travel requested from the game")
	v.close()
	v.open("menu")
	kit.eq(v.context, "menu", "menu context")
	v.activate("L_M1_Archive")
	kit.eq(g.travelled.back(), ["L_M1_Archive", true], "travel from the main menu is flagged")
	# Q / E switch to the films page and back (like the journal's tabs)
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_E
	ev.pressed = true
	kit.ok(v.modal_input(ev), "E is handled by the view")
	kit.eq(v.page, "films", "E shows the films page")
	kit.eq(TKit.sorted(v.buttons), ["LS_A1_ToM1"], "only seen films can be chosen")
	kit.ok(_labels_text(v).contains("Abfahrt aus Karsk"), "film card shows its title")
	kit.ok(_labels_text(v).contains(UIKit.t("ui.memories.locked_film").to_upper()), "unseen films stay locked")
	kit.ok(not v.activate("LS_M1_Hall"), "an unseen film does not play")
	kit.ok(v.activate("LS_A1_ToM1"), "a seen film plays again")
	kit.eq(g.watched, [["LS_A1_ToM1", true]], "rewatch requested (from the main menu)")
	ev.physical_keycode = KEY_Q
	kit.ok(v.modal_input(ev), "Q is handled by the view")
	kit.eq(v.page, "scenes", "Q goes back to the places")
	# signal mode (no Game call when someone listens)
	var got := []
	v.travel_requested.connect(func(id: String, fm: bool) -> void: got.append([id, fm]))
	v.activate("L_M1_Archive")
	kit.eq(got, [["L_M1_Archive", true]], "travel_requested emitted when connected")
	# text scale: captions follow the 100/125/150 % setting
	var scaled := 0
	for l in v.find_children("*", "Label", true, false):
		if l.has_meta("aoe_base_size"):
			scaled += 1
	kit.ok(scaled >= 8, "captions registered for text scaling (%d)" % scaled)
	# nothing open: the empty note shows
	g.cards = [{"id": "L_A1_Railyard", "unlocked": false}]
	v.refresh()
	kit.ok(v.buttons.is_empty(), "no selectable card without memories")
	kit.ok(_labels_text(v).contains(UIKit.t("ui.memories.empty")), "empty note shown")
	v.close()
	return true


func _hud_badge() -> bool:
	var h: Control = _mount(HUD_SCENE)
	h.show_hud()
	kit.ok(not h.is_memory_badge_visible(), "no badge in the present")
	h.set_memory({"scene": "L_A1_Railyard", "place": "Verladebahnhof Karsk", "date": "Januar 1964", "from_menu": false})
	kit.ok(h.is_memory_badge_visible(), "badge visible inside a memory")
	# shown again while its slide-in still runs (a panel opened and closed at once): it must not creep left
	var x0: float = h._memory_box.position.x
	for _i in 3:
		h.hide_hud()
		h.show_hud()
	kit.ok(h._memory_box.position.x >= x0 - 0.5, "badge slides in from its own place every time (x %.1f, first %.1f)"
		% [h._memory_box.position.x, x0])
	var text := _labels_text(h)
	kit.ok(text.contains(UIKit.t("ui.memories.badge").to_upper()), "badge says ERINNERUNG")
	kit.ok(text.contains("Verladebahnhof Karsk  ·  Januar 1964"), "badge names place and date")
	kit.ok(text.contains(UIKit.t("ui.memories.badge_hint")), "badge says how to return")
	h.set_objectives(["a1_talk_irina"])
	kit.ok(not h._objective_box.visible, "objectives hidden inside a memory")
	h.hide_hud()
	kit.ok(not h.is_memory_badge_visible(), "badge hidden with the HUD (cinematics, photo mode)")
	h.show_hud()
	h.set_memory({"place": "Platz", "from_menu": true})
	kit.ok(_labels_text(h).contains(UIKit.t("ui.memories.badge_hint_menu")), "from the menu: „Erinnerung beenden“")
	h.set_memory({})
	kit.ok(not h.is_memory_badge_visible(), "badge gone in the present")
	kit.ok(h._objective_box.visible, "objectives back in the present")
	return true


func _pause_entry() -> bool:
	var g := _mock_game()
	var p: Control = _mount(PAUSE_SCENE)
	p.open()
	var b: Button = p._buttons["memories"]
	kit.eq(b.text, UIKit.t("ui.memories.pause.open"), "present: „Erinnerungen“")
	kit.ok(b.visible and not b.disabled, "entry usable")
	# eight entries now: with the game's theme the whole column (frame and Esc hint included) stays on screen
	p.theme = UIKit.theme(false)
	var pnl = p.get("_panel")
	var need: float = (pnl as Control).get_combined_minimum_size().y if pnl is Control else 9999.0
	kit.ok(pnl is Control and (pnl as Control).offset_top + need <= 1080.0 - 24.0,
		"pause column fits a 1080-px screen (top %s + %.0f px)" % [(pnl as Control).offset_top if pnl is Control else -1.0, need])
	p.theme = null
	p.close()
	g.info = {"scene": "L_A1_Railyard", "place": "Verladebahnhof Karsk", "date": "Januar 1964", "chapter": "Kapitel 1",
		"who": "alexei", "from_menu": false}
	p.open()
	kit.eq(b.text, UIKit.t("ui.memories.pause.return"), "inside: „In die Gegenwart zurückkehren“")
	kit.ok(p._who.text.contains(UIKit.char_name("alexei").to_upper()), "header names who is remembered")
	kit.ok(p._where.text.contains("Verladebahnhof Karsk"), "header names the place")
	p.close()
	g.info["from_menu"] = true
	p.open()
	kit.eq(b.text, UIKit.t("ui.memories.pause.return_menu"), "from the menu: „Erinnerung beenden“")
	var asked := []
	p.memory_return_requested.connect(func() -> void: asked.append(true))
	p._memories()
	kit.eq(asked.size(), 1, "the entry asks Game to return")
	kit.ok(not p.is_open, "the pause menu closes for the return")
	return true


func _save_screen() -> bool:
	var g := _mock_game()
	var s: MockSaves = kit.track(MockSaves.new())
	UIKit.overrides["Saves"] = s
	var m: Control = _mount(SAVELOAD_SCENE)
	m.open("save", true)
	kit.ok(not m._block_note.visible, "present: no note")
	kit.ok(m._can_primary(m._slot("1")), "present: manual slot can be saved")
	m.close()
	s.block = "sys.save.err.memory"
	g.block = s.block
	m.open("save", true)
	kit.ok(m._block_note.visible, "inside a memory: the save screen explains why")
	kit.eq(m._block_note.text, UIKit.t("sys.save.err.memory"), "explanation text")
	kit.ok(not m._can_primary(m._slot("1")), "inside a memory: no slot can be saved")
	kit.ok(not m._can_primary(m._slot("2")), "…not even an empty one")
	m.close()
	m.open("load", true)
	kit.ok(not m._block_note.visible, "loading is still possible (no note)")
	kit.ok(m._can_primary(m._slot("1")), "a save can be loaded from inside a memory")
	m.close()
	UIKit.overrides.erase("Saves")
	return true


func _drive() -> bool:
	var d = load("res://scripts/core/memory_drive.gd").new()
	for fn in ["autoplay", "inputplay", "demo", "present_state", "check_inside", "check_returned", "first_target"]:
		kit.ok(d.has_method(fn), "memory_drive.%s exists" % fn)
	d.free()
	return true
