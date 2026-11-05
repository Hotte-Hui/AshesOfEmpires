extends RefCounted
## Port of preproduction/tests/test_integrity_v4.py (DeepIntegrityTests, 7 tests).
## The story-data part of validate_integrity_v4.deep_validate lives in the engine
## (deep_validate_data); the production-manifest part (asset registry + shot list CSVs of the
## preproduction package) is ported here because the game does not need it at runtime.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const REGISTRY := "res://preproduction/assets/planned/asset_registry_v4.csv"
const SHOTLIST := "res://preproduction/production/shot_list_v4.csv"

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("test_deep_valid", _test_deep_valid)
	kit.run_case("test_reject_impossible_scene_link", _test_reject_impossible_scene_link)
	kit.run_case("test_reject_cross_scene_item", _test_reject_cross_scene_item)
	kit.run_case("test_reject_unsolvable_puzzle", _test_reject_unsolvable_puzzle)
	kit.run_case("test_reject_inaccessible_clue", _test_reject_inaccessible_clue)
	kit.run_case("test_reject_looping_dialogue", _test_reject_looping_dialogue)
	kit.run_case("test_reject_wrong_quest_protagonist", _test_reject_wrong_quest_protagonist)
	kit.cleanup()
	return kit.failures


static func data() -> Dictionary:
	return ENGINE.load_data()["data"]


static func reference_root() -> String:
	return "res://documentation" if DirAccess.dir_exists_absolute("res://documentation/references") else ""


## Reads a CSV (utf-8-sig like Python's csv.DictReader) into an Array of Dictionaries.
static func read_csv(path: String) -> Array:
	var rows: Array = []
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return rows
	var header := f.get_csv_line()
	if header.size() > 0 and header[0].begins_with("﻿"):
		header[0] = header[0].substr(1)
	while not f.eof_reached():
		var line := f.get_csv_line()
		if line.size() == 1 and line[0] == "":
			continue
		var row := {}
		for i in header.size():
			row[header[i]] = line[i] if i < line.size() else ""
		rows.append(row)
	return rows


## Port of the manifest half of deep_validate (registry + shot list). Returns "" or an error message.
func validate_manifests(d: Dictionary, registry: Array, shotlist: Array, ref_root: String) -> String:
	var scenes := {}
	for s in d["scenes"]["scenes"]:
		scenes[s["id"]] = true
	var aids: Array = []
	for a in registry:
		aids.append(a["id"])
	if ENGINE.Util.as_set(aids).size() != aids.size():
		return "Duplicate asset ID"
	for a in registry:
		if not (scenes.has(a["scene"]) or a["scene"] == "GLOBAL"):
			return "Unknown asset scene"
		if not ["P0", "P1", "P2"].has(a["priority"]):
			return "Bad asset priority"
		if a["visual_reference"] != "none" and ref_root != "" \
				and not FileAccess.file_exists(ref_root.path_join("references").path_join(a["visual_reference"])):
			return "Missing asset reference"
	var ids := ENGINE.Util.as_set(aids)
	var shot_ids := {}
	for shot in shotlist:
		shot_ids[shot["shot_id"]] = true
	if shot_ids.size() != shotlist.size():
		return "Duplicate shot ID"
	for shot in shotlist:
		for asset_id in (shot["asset_ids"] as String).split(" ", false):
			if not ids.has(asset_id):
				return "Shot references missing assets"
		if not (shot["t_start"] <= shot["t_end"]):
			return "Nonmonotone shot timestamp"
	if registry.size() < 25 or shotlist.size() < 12:
		return "Insufficient production manifests"
	return ""


func _test_deep_valid() -> bool:
	var root := reference_root()
	var d := data()
	var r: Dictionary = ENGINE.deep_validate_data(d, root)
	kit.is_ok(r, "canonical data passes deep validation")
	var registry := read_csv(REGISTRY)
	var shotlist := read_csv(SHOTLIST)
	kit.eq(validate_manifests(d, registry, shotlist, root), "", "production manifests valid")
	kit.ok(registry.size() >= 25, "assets >= 25 (got %d)" % registry.size())
	# The slice locked three sequences; Chapter 3 adds LS_C3_Trains, LS_C3_ToHall, LS_C3_Close (C3_DESIGN §2.9).
	kit.eq(r.get("report", {}).get("cinematics"), 6, "six locked cinematics")
	kit.eq(Kit.sorted(ENGINE.LOCKED_CINEMATICS), Kit.sorted(["LS_A1_ToM1", "LS_M1_Hall", "LS_X1_Final", "LS_C3_Trains",
		"LS_C3_ToHall", "LS_C3_Close"]), "validator list of locked cinematics")
	return true


func _test_reject_impossible_scene_link() -> bool:
	var d := data()
	d["scenes"]["scenes"][0]["next_scene"] = "L_X1_Montage"
	kit.is_err(ENGINE.deep_validate_data(d), "A1 cannot skip M1")
	return true


func _test_reject_cross_scene_item() -> bool:
	var d := data()
	d["items"]["items"][0]["scene"] = "L_M1_Archive"
	kit.is_err(ENGINE.deep_validate_data(d), "item granted in the wrong scene")
	return true


func _test_reject_unsolvable_puzzle() -> bool:
	var d := data()
	d["puzzles"]["puzzles"][0]["solution"] = ["moon", "circle", "triangle"]
	kit.is_err(ENGINE.deep_validate_data(d), "solution not built from display symbols")
	return true


func _test_reject_inaccessible_clue() -> bool:
	var d := data()
	d["quests"]["quests"][0]["objectives"][3]["requires"] = ["a1_inspect_timetable"]
	kit.is_err(ENGINE.deep_validate_data(d), "puzzle clue not reachable through prerequisites")
	return true


func _test_reject_looping_dialogue() -> bool:
	var d := data()
	var nodes: Array = d["dialogue"]["conversations"][0]["nodes"]
	nodes[-1].erase("end")
	nodes[-1]["next"] = "irina_01"
	kit.is_err(ENGINE.deep_validate_data(d), "looping dialogue")
	return true


func _test_reject_wrong_quest_protagonist() -> bool:
	var d := data()
	d["scenes"]["scenes"][1]["protagonist"] = "alexei"
	kit.is_err(ENGINE.deep_validate_data(d), "archive must be played by its quest's character")
	return true
