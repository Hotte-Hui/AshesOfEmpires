extends RefCounted
## Round 10 save flag migration (documentation/NEXT_STEPS.md §1, C4P2_DESIGN.md §1.1): a v3 Story payload written by an
## earlier build lacks every Story flag added to data/v3/flags.json since — and the replay validation compares the
## flags dictionary as a whole. SaveSystem.rebase_story() (read_container, Memories.snapshot_raw) therefore fills the
## missing flags with their defaults before Story.validate_save_json(); Memories.memory_flags() does the same for the
## replayed line variants. Covered: the slice-era payloads (9 flags, rounds 1–6), the round-7 / round-8 / round-9
## shapes (16 flags: montage forms, mid-chapter saves with dialogue cursors / puzzle attempts / pending films, memory
## snapshots), finished playthroughs, the strictness of the validation, and the byte-identical round trip of a save
## of the current build. The Story engine itself (and its Python reference) is unchanged.

const Kit := preload("res://tests/support/test_kit.gd")
const SAVES := preload("res://scripts/core/save_system.gd")
const MEM := preload("res://scripts/core/memories.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const TMP := "user://test_save_migration_r10"

## The Story flags of the slice builds (rounds 1–6, flags.json of the project skeleton).
const SLICE_FLAGS := ["irina_trust", "alexei_secrecy", "konrad_evidence", "office_suspicion", "civilian_welfare",
	"c17_confirmed", "signal_restored", "blueprint_match_confirmed", "slice_finished"]
## The Story flags of the round-7, round-8 and round-9 builds (Chapter 3 added seven, Chapter 4 part 1 none).
const ROUND9_FLAGS := ["irina_trust", "alexei_secrecy", "konrad_evidence", "office_suspicion", "civilian_welfare",
	"c17_confirmed", "signal_restored", "blueprint_match_confirmed", "slice_finished", "alexei_konrad_trust",
	"elena_trust", "evidence_chain", "kessler_alerted", "courier_files_seen", "protocol_matched", "elena_missing"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	_clear()
	DirAccess.make_dir_recursive_absolute(TMP)
	kit.run_case("fill_is_pure_and_keeps_stored_values", _fill_rules)
	kit.run_case("slice_era_payloads_load_with_defaults", _slice_era)
	kit.run_case("round7_8_9_montage_forms_load", _montage_forms)
	kit.run_case("mid_chapter_saves_of_every_generation_load", _mid_chapter)
	kit.run_case("finished_playthrough_loads", _finished)
	kit.run_case("memory_snapshots_of_every_generation", _memory_snapshots)
	kit.run_case("validation_stays_strict", _strict)
	kit.run_case("current_save_round_trips_byte_identical", _round_trip)
	_clear()
	kit.cleanup()
	return kit.failures


static func _clear() -> void:
	if not DirAccess.dir_exists_absolute(TMP):
		return
	for sub in DirAccess.get_directories_at(TMP):
		for f in DirAccess.get_files_at(TMP.path_join(sub)):
			DirAccess.remove_absolute(TMP.path_join(sub).path_join(f))
		DirAccess.remove_absolute(TMP.path_join(sub))
	for f in DirAccess.get_files_at(TMP):
		DirAccess.remove_absolute(TMP.path_join(f))
	DirAccess.remove_absolute(TMP)


# ------------------------------------------------------------------ helpers
func _state(g: Node) -> Dictionary:
	return ENGINE.json_parse(g.save_json())["value"]


## The payload as a build that knew only `known` flags wrote it (the other flag keys removed).
static func _as_written_by(st: Dictionary, known: Array) -> Dictionary:
	var out: Dictionary = st.duplicate(true)
	var fl: Dictionary = out["flags"]
	for name in fl.keys():
		if not known.has(name):
			fl.erase(name)
	return out


## The montage form of an older chain end: the scene changed to the montage on the exit event, nobody playing.
static func _montage_form(st: Dictionary) -> Dictionary:
	var out: Dictionary = st.duplicate(true)
	out["current_scene"] = "L_X1_Montage"
	out["active_character"] = "none"
	return out


## Writes a save container (as Saves.save() writes it) with `story` as payload; returns its path.
func _container(file: String, story: Dictionary) -> String:
	var meta := {"version": SAVES.CONTAINER_VERSION, "timestamp": 1.0, "chapter_key": "",
		"character": str(story.get("active_character", "")), "scene": str(story.get("current_scene", "")),
		"playtime_s": 600.0, "label": ""}
	var path := TMP.path_join(file)
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(ENGINE.json_dumps({"meta": meta, "story": story, "extra": {}}, 1))
	f.close()
	return path


## Reads a container like the load menu (re-base + flag fill), validates it and loads it into a fresh engine.
## Returns the loaded engine (null on failure, reported).
func _load_container(path: String, what: String) -> Node:
	var c: Dictionary = SAVES.read_container(path)
	if not kit.ok(c.get("ok", false), what + ": container reads — " + str(c.get("error", ""))):
		return null
	var g := kit.story()
	var v: Dictionary = g.validate_save_json(c["story_raw"])
	if not kit.ok(v.get("ok", false), what + ": validates — " + str(v.get("error", ""))):
		return null
	var r: Dictionary = g.load_json(c["story_raw"])
	if not kit.ok(r.get("ok", false), what + ": loads — " + str(r.get("error", ""))):
		return null
	return g


## Flags of flags.json that `known` lacks (what a payload of that generation misses today).
static func _new_since(known: Array) -> Array:
	var out: Array = []
	for name in SAVES.flag_defaults():
		if not known.has(name):
			out.append(name)
	return out


# ------------------------------------------------------------------ cases
func _fill_rules() -> bool:
	var defaults := SAVES.flag_defaults()
	var flags_doc: Dictionary = Kit.parse(FileAccess.get_file_as_string("res://data/v3/flags.json"))
	kit.eq(defaults.keys(), (flags_doc["flags"] as Dictionary).keys(), "flag_defaults covers flags.json in data order")
	for name in defaults:
		kit.ok(Kit.strict_eq(defaults[name], flags_doc["flags"][name]["default"]), "default of " + name)
	var g := kit.story()
	kit.play_until(g, "a1")
	var full := _state(g)
	var old := _as_written_by(full, SLICE_FLAGS)
	old["flags"]["irina_trust"] = 7          # a stored value is never changed, even an invalid one
	var before := old.duplicate(true)
	var filled := SAVES.fill_flag_defaults(old)
	kit.ok(Kit.strict_eq(old, before), "the input dictionary is not modified")
	kit.eq(filled["flags"].keys().size(), defaults.size(), "every flags.json flag present after the fill")
	kit.eq(filled["flags"]["irina_trust"], 7, "stored value kept")
	for name in _new_since(SLICE_FLAGS):
		kit.ok(Kit.strict_eq(filled["flags"][name], defaults[name]), "missing %s filled with its default" % name)
	kit.eq(SAVES.missing_flags(old), _new_since(SLICE_FLAGS), "missing_flags lists them in flags.json order")
	kit.eq(SAVES.missing_flags(full), [], "a payload of this build misses nothing")
	kit.ok(Kit.strict_eq(SAVES.fill_flag_defaults(full), full), "a payload of this build is unchanged")
	var odd_unknown: Dictionary = full.duplicate(true)
	odd_unknown["flags"]["no_such_flag"] = 1
	kit.ok(SAVES.fill_flag_defaults(odd_unknown)["flags"].has("no_such_flag"), "an unknown key is kept (validation refuses it)")
	for odd in [{}, {"flags": "x"}, {"flags": [1, 2]}, {"completed_events": ["a1_completed", "slice_completed"],
			"current_scene": "L_X1_Montage"}]:
		kit.ok(Kit.strict_eq(SAVES.fill_flag_defaults(odd), odd), "shape without a flags dictionary unchanged: " + str(odd))
		kit.ok(Kit.strict_eq(SAVES.rebase_story(odd), odd), "and re-based unchanged: " + str(odd))
		kit.eq(SAVES.missing_flags(odd), [], "nothing missing without a flags dictionary: " + str(odd))
	return true


func _slice_era() -> bool:
	# a slice-era autosave in the rail yard (the real 1.json.bak shape: start of A1, nine flags)
	var start := kit.story()
	var path := _container("slice_start.json", _as_written_by(_state(start), SLICE_FLAGS))
	var c: Dictionary = SAVES.read_container(path)
	kit.ok(str(c.get("warnings", [])).contains("flags filled"), "the fill is reported as a warning")
	kit.ok(str(c.get("warnings", [])).contains("evidence_chain"), "the warning names the filled flags")
	var g := _load_container(path, "slice start")
	if g != null:
		kit.eq(g.save_json(), start.save_json(), "slice start: identical to a new game of this build")
	# mid A1 (dialogue done, one inspect), after A1 (in M1, puzzle attempt), after M1 (the old demo end: Chapter 3)
	var mid := kit.story()
	kit.play_dialogue(mid, "a1_talk_irina")
	kit.step(mid.inspect("a1_inspect_seal"), "seal")
	var after_a1 := kit.story()
	kit.play_until(after_a1, "a1")
	kit.step(after_a1.inspect("m1_inspect_plan_a"), "plan a")
	kit.step(after_a1.inspect("m1_inspect_plan_b"), "plan b")
	kit.step(after_a1.solve_puzzle("m1_align_plans", {"rotation_steps": 1, "offset_x": 0, "offset_y": 0}), "wrong overlay")
	var after_m1 := kit.story()
	kit.play_until(after_m1, "m1", {"a1": "keep_private", "m1": "request_explanation"})
	for pair in [["slice_mid_a1.json", mid], ["slice_after_a1.json", after_a1], ["slice_after_m1.json", after_m1]]:
		var ref: Node = pair[1]
		var h := _load_container(_container(pair[0], _as_written_by(_state(ref), SLICE_FLAGS)), pair[0])
		if h != null:
			kit.eq(h.save_json(), ref.save_json(), pair[0] + ": the loaded state is this build's state at that point")
	if after_m1 != null:
		kit.eq(after_m1.current_scene, "L_C3_Station", "precondition: after M1 the chain goes on in Veltrava")
	return true


func _montage_forms() -> bool:
	# round 7: the montage after c3b_completed · round 8: after c3g_completed · round 9: after c4d_completed —
	# each continues in the scene that now follows its last exit event, with the flags of this build filled in.
	for spec in [["c3b", {"c3b": "report_delegation"}], ["c3g", {"c3g": "hide_for_elena"}], ["c4d", {"c4d": "protect_marta"}]]:
		var stage: String = spec[0]
		var ref := kit.story()
		kit.play_until(ref, stage, spec[1])
		var old := _montage_form(_as_written_by(_state(ref), ROUND9_FLAGS))
		var reb := SAVES.rebase_story(old)
		kit.eq([reb.get("current_scene"), reb.get("active_character")], [ref.current_scene, ref.active_character],
			"montage form after %s re-based to the scene after it" % stage)
		kit.eq(SAVES.missing_flags(reb), [], "montage form after %s: no flag missing after the re-base" % stage)
		var g := _load_container(_container("montage_%s.json" % stage, old), "montage form after " + stage)
		if g == null:
			continue
		kit.eq(g.save_json(), ref.save_json(), "montage form after %s = this build's state after %s" % [stage, stage])
		if g.current_scene != "L_X1_Montage":
			kit.ok(not g.available().is_empty(), "montage form after %s: something to do in %s" % [stage, g.current_scene])
	# the round-7 form plays on through the whole grown chain to the finale
	var r7 := kit.story()
	kit.play_until(r7, "c3b")
	var g7 := _load_container(_container("montage_r7_full.json", _montage_form(_as_written_by(_state(r7), ROUND9_FLAGS))),
		"round-7 montage form")
	if g7 != null:
		for i in range(Kit.STAGES.find("c3b") + 1, Kit.STAGES.size()):
			kit.play_stage(g7, Kit.STAGES[i])
		for seq in g7.pending_cinematics():
			kit.step(g7.consume_cinematic(seq, true), "cinematic " + seq)
		kit.is_ok(g7.finale(), "the round-7 montage form plays on to the finale")
	return true


func _mid_chapter() -> bool:
	var shapes: Array = []
	# round 7 — Veltrava station, mid-conversation with the conductor; the palais with one failed protocol attempt
	var a := kit.story()
	kit.play_until(a, "m1")
	kit.step(a.start_dialogue("c3a_talk_conductor"), "start conductor")
	kit.step(a.advance_dialogue("c3a_talk_conductor"), "advance conductor")
	shapes.append(["r7_station_mid_dialogue.json", a])
	var b := kit.story()
	kit.play_until(b, "c3a")
	kit.play_dialogue(b, "c3b_arrival")
	kit.step(b.inspect("c3b_inspect_seating"), "seating")
	kit.step(b.inspect("c3b_inspect_log"), "log")
	kit.step(b.solve_puzzle("c3b_solve_protocol", ["soviet", "chair", "reich", "secretariat"]), "wrong protocol")
	shapes.append(["r7_palais_attempt.json", b])
	# round 8 — the registry check with two failed attempts (hint state), mid-way on the quay (films pending)
	var c := kit.story()
	kit.play_until(c, "c3c")
	kit.step(c.inspect("c3d_inspect_intake"), "intake")
	kit.step(c.inspect("c3d_inspect_drawer"), "drawer")
	kit.play_dialogue(c, "c3d_talk_compare")
	for i in 2:
		kit.step(c.solve_puzzle("c3d_solve_check", ["january", "par_4", "out_2340", "in_c17_44"]), "wrong check %d" % i)
	shapes.append(["r8_registry_two_attempts.json", c])
	var d := kit.story()
	kit.play_until(d, "c3f", {"c3d": "pocket_plan"})
	kit.step(d.inspect("c3g_inspect_halves"), "halves")
	shapes.append(["r8_quay_films_pending.json", d])
	# round 9 — the tram loop mid-conversation with Marta (films seen), the siding with one failed number chain
	var e := kit.story()
	kit.play_until(e, "c4a")
	for seq in e.pending_cinematics():
		kit.step(e.consume_cinematic(seq, false), "consume " + seq)
	kit.step(e.inspect("c4b_inspect_notice"), "notice")
	kit.step(e.start_dialogue("c4b_talk_marta"), "start marta")
	for i in 3:
		kit.step(e.advance_dialogue("c4b_talk_marta"), "advance marta %d" % i)
	shapes.append(["r9_loop_mid_dialogue.json", e])
	var f := kit.story()
	kit.play_until(f, "c4b")
	kit.step(f.inspect("c4c_inspect_card"), "card")
	kit.step(f.inspect("c4c_inspect_stencils"), "stencils")
	kit.step(f.solve_puzzle("c4c_solve_numbers", ["c1745", "n47702", "n24318", "c1742"]), "wrong chain")
	shapes.append(["r9_siding_attempt.json", f])
	for s in shapes:
		var ref: Node = s[1]
		var known: Array = SLICE_FLAGS if str(s[0]).begins_with("slice") else ROUND9_FLAGS
		var g := _load_container(_container(s[0], _as_written_by(_state(ref), known)), s[0])
		if g == null:
			continue
		kit.eq(g.save_json(), ref.save_json(), s[0] + ": byte-identical to this build's state at that point")
		kit.eq(g.available(), ref.available(), s[0] + ": the same objectives are open")
	return true


## A finished playthrough of this build loads byte-identically, also when its payload lacks flags that stayed at
## their default on its route (the shape a build that did not know them would have written). A finished playthrough
## of an OLDER, shorter chain stays refused: the grown chain's finale needs the new chapters, and no build ever saved
## after the finale (Game: no autosave in the montage, the credits lead to the main menu), so no player has one.
func _finished() -> bool:
	var defaults := SAVES.flag_defaults()
	for route in [["share_with_irina", "preserve_evidence"], ["keep_private", "request_explanation"]]:
		var ref := kit.play_verified_route(route[0], route[1], true)
		kit.ok(ref.is_finished(), "precondition: the playthrough is finished")
		var full := _state(ref)
		var g := _load_container(_container("finished_full.json", full), "finished playthrough")
		if g != null:
			kit.eq(g.save_json(), ref.save_json(), "finished playthrough: byte-identical")
		var at_default: Array = []
		for name in defaults:
			if Kit.strict_eq(full["flags"][name], defaults[name]):
				at_default.append(name)
		kit.ok(not at_default.is_empty(), "precondition: some flags stayed at their default on this route")
		var known: Array = []
		for name in defaults:
			if not at_default.has(name):
				known.append(name)
		var h := _load_container(_container("finished_stripped.json", _as_written_by(full, known)),
			"finished playthrough without %s" % ", ".join(at_default))
		if h != null:
			kit.eq(h.save_json(), ref.save_json(), "finished playthrough: identical after the fill")
			kit.ok(h.is_finished(), "and still finished")
	# the round-9 chain's end: a1 … c4d, then the finale — re-based like every other state? No: it keeps its scene
	var r9 := kit.story()
	kit.play_until(r9, "c4d")
	var old: Dictionary = _montage_form(_as_written_by(_state(r9), ROUND9_FLAGS))
	(old["completed_events"] as Array).append("slice_completed")
	old["flags"]["slice_finished"] = true
	old["finale_viewed"] = true
	var reb := SAVES.rebase_story(old)
	kit.eq([reb["current_scene"], reb["completed_events"]], [old["current_scene"], old["completed_events"]],
		"an older finished playthrough keeps its scene and events (rebase leaves finished playthroughs alone)")
	kit.eq(SAVES.missing_flags(reb), [], "but its flags are filled")
	var last_scene := ""
	for s in (Kit.parse(FileAccess.get_file_as_string("res://data/v3/scenes.json"))["scenes"] as Array):
		if str(s.get("exit_on_event", "")) == "c4d_completed":
			last_scene = str(s.get("next_scene"))
	if last_scene != "L_X1_Montage":
		kit.ok(not kit.story().validate_save_json(ENGINE.json_dumps(reb, 2)).get("ok", true),
			"the grown chain's finale is not reachable from it: refused, as before the migration")
	return true


func _memory_snapshots() -> bool:
	var m = MEM.new(TMP.path_join("profile.json"))
	var defaults := SAVES.flag_defaults()
	var specs := [
		["L_A1_Railyard", "a1", SLICE_FLAGS, {}],
		["L_C3_Hall", "c3b", ROUND9_FLAGS, {"c3b": "search_elena"}],
		["L_C3_RegistryB", "c3d", ROUND9_FLAGS, {"c3d": "pocket_plan"}],
		["L_C3_Quay", "c3g", ROUND9_FLAGS, {"c3g": "swap_halves"}],
		["L_C4_AnnexB", "c4d", ROUND9_FLAGS, {"c4d": "protect_marta"}],
	]
	for spec in specs:
		var ref := kit.story()
		kit.play_until(ref, spec[1], spec[3])
		var st := _as_written_by(_state(ref), spec[2])
		# the profile records the state at the exit event; at a chain end of its build that was the montage form
		if spec[1] in ["c3b", "c3g", "c4d"]:
			st = _montage_form(st)
		m.data["completed"][spec[0]] = {"t": 1.0, "story": st}
		var raw: String = m.snapshot_raw(spec[0])
		var v: Dictionary = kit.story().validate_save_json(raw)
		kit.ok(v.get("ok", false), "%s snapshot validates — %s" % [spec[0], str(v.get("error", ""))])
		kit.eq(raw, ref.save_json(), spec[0] + ": the snapshot reads as this build's state at its exit event")
		var mf: Dictionary = m.memory_flags(spec[0], {}, ref.choice_history())
		kit.eq(mf.keys().size(), defaults.size(), spec[0] + ": memory_flags names every flag of this build")
		for name in spec[2]:
			kit.ok(Kit.strict_eq(mf[name], st["flags"][name]), "%s: stored %s kept" % [spec[0], name])
		for name in _new_since(spec[2]):
			kit.ok(Kit.strict_eq(mf[name], defaults[name]), "%s: %s at its default" % [spec[0], name])
		# a snapshot whose decisions disagree with the live playthrough still answers with the live flags
		var other := {"a1_choose": "no_such_choice"}
		kit.ok(Kit.strict_eq(m.memory_flags(spec[0], {"live": 1}, other), {"live": 1}), spec[0] + ": live flags otherwise")
	return true


func _strict() -> bool:
	var g := kit.story()
	kit.play_until(g, "c3d")
	var full := _state(g)
	# a stored value that contradicts the progress is still refused
	var wrong := _as_written_by(full, ROUND9_FLAGS)
	wrong["flags"]["evidence_chain"] = 5
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(SAVES.rebase_story(wrong), 2)).get("ok", true),
		"a contradicting stored value is refused after the fill")
	var wrong_type := _as_written_by(full, ROUND9_FLAGS)
	wrong_type["flags"]["c17_confirmed"] = "ja"
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(SAVES.rebase_story(wrong_type), 2)).get("ok", true),
		"a stored value of the wrong type is refused")
	var unknown := _as_written_by(full, ROUND9_FLAGS)
	unknown["flags"]["no_such_flag"] = 0
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(SAVES.rebase_story(unknown), 2)).get("ok", true),
		"an unknown flag is refused")
	var no_flags: Dictionary = full.duplicate(true)
	no_flags.erase("flags")
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(SAVES.rebase_story(no_flags), 2)).get("ok", true),
		"a payload without flags is refused")
	# the engine itself stays strict (the Python reference parity): a payload lacking a flag fails without the fill
	var stripped: Dictionary = full.duplicate(true)
	kit.eq(stripped["flags"]["office_suspicion"], 0, "precondition: office_suspicion stayed at its default")
	stripped["flags"].erase("office_suspicion")
	kit.ok(not g.validate_save_json(ENGINE.json_dumps(stripped, 2)).get("ok", true),
		"Story.validate_save_json alone still refuses a payload with a missing flag")
	kit.ok(g.validate_save_json(ENGINE.json_dumps(SAVES.rebase_story(stripped), 2)).get("ok", false),
		"the same payload validates after the save system's fill")
	return true


func _round_trip() -> bool:
	for stage in Kit.STAGES:
		var g := kit.story()
		kit.play_until(g, stage)
		var s := kit.saves()
		s.base_dir = TMP.path_join("rt")
		s.story = g
		s.extra_provider = func() -> Dictionary: return {"playtime": 12.5}
		s.block_provider = func() -> String: return ""
		if not kit.is_ok(s.save("1"), "save after " + stage):
			continue
		var c: Dictionary = SAVES.read_container(s.slot_path("1"))
		kit.eq(c.get("warnings"), [], stage + ": a save of this build needs no migration (no warning)")
		var other := kit.story()
		var s2 := kit.saves()
		s2.base_dir = TMP.path_join("rt")
		s2.story = other
		s2.extra_provider = func() -> Dictionary: return {"playtime": 12.5}
		s2.block_provider = func() -> String: return ""
		kit.is_ok(s2.load("1"), "load after " + stage)
		kit.eq(other.save_json(), g.save_json(), stage + ": the loaded Story state is byte-identical")
		kit.is_ok(s2.save("2"), "save again after " + stage)
		var first: Dictionary = Kit.parse(FileAccess.get_file_as_string(s.slot_path("1")))
		var second: Dictionary = Kit.parse(FileAccess.get_file_as_string(s.slot_path("2")))
		kit.eq(ENGINE.json_dumps(second["story"], 1), ENGINE.json_dumps(first["story"], 1),
			stage + ": the story section of the second save is byte-identical")
	return true
