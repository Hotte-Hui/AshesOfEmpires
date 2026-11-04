extends RefCounted
## Guards the user's rename of the German protagonist (2026-11-04): the canonical id is "konrad" and the
## pre-rename id must not appear in this project's canonical data, locale files, the story/save code, the
## tests or the story documentation. The old id is DERIVED from the preproduction package (which keeps
## it on purpose), so this file never spells it. Other areas are scanned too, but only reported.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")

const OWNED := ["res://data/v3", "res://data/locale", "res://scripts/story", "res://scripts/core/save_system.gd",
	"res://tests", "res://documentation/QUEST_DATABASE.md", "res://documentation/asset_manifest_parts/story.md"]
const REPORT_ONLY := ["res://scripts", "res://scenes", "res://data", "res://documentation", "res://assets"]
const TEXT_EXT := ["gd", "json", "md", "py", "tscn", "tres", "cfg", "csv", "txt", "gdshader"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("old_id_derivable", _old_id_derivable)
	kit.run_case("canonical_ids_use_konrad", _canonical_ids)
	kit.run_case("owned_files_free_of_old_name", _owned_files)
	kit.run_case("other_areas_report", _report_others)
	kit.cleanup()
	return kit.failures


static func old_id() -> String:
	var pre = ENGINE.json_parse(FileAccess.get_file_as_string("res://preproduction/data/v3/flags.json"))["value"]
	var now = ENGINE.json_parse(FileAccess.get_file_as_string("res://data/v3/flags.json"))["value"]
	for p in pre["protagonists"]:
		if not (now["protagonists"] as Array).has(p):
			return str(p)
	return ""


func _old_id_derivable() -> bool:
	var old := old_id()
	kit.ok(old.length() >= 4, "pre-rename id found in the preproduction package")
	kit.ne(old, "konrad", "old id differs from the new one")
	return true


func _canonical_ids() -> bool:
	var g := kit.story()
	kit.eq(g.scene_def("L_M1_Archive").get("protagonist"), "konrad", "archive protagonist")
	kit.eq(g.quest_for("m1_choose").get("character"), "konrad", "M1 quest character")
	kit.ok(g.flags().has("konrad_evidence"), "flag konrad_evidence")
	g.free()
	return true


static func _collect(path: String, out: Array) -> void:
	if FileAccess.file_exists(path):
		out.append(path)
		return
	var d := DirAccess.open(path)
	if d == null:
		return
	for f in d.get_files():
		if TEXT_EXT.has(f.get_extension().to_lower()):
			out.append(path.path_join(f))
	for sub in d.get_directories():
		if not sub.begins_with(".") and sub != "references":
			_collect(path.path_join(sub), out)


func _owned_files() -> bool:
	var old := old_id().to_lower()
	var files: Array = []
	for p in OWNED:
		_collect(p, files)
	kit.ok(files.size() >= 15, "scanned owned files (%d)" % files.size())
	for f in files:
		var text := FileAccess.get_file_as_string(f).to_lower()
		kit.ok(not text.contains(old), "%s contains the pre-rename protagonist name" % f)
	return true


func _report_others() -> bool:
	var old := old_id().to_lower()
	var files: Array = []
	for p in REPORT_ONLY:
		_collect(p, files)
	var hits: Array = []
	for f in files:
		if FileAccess.get_file_as_string(f).to_lower().contains(old):
			hits.append(f)
	if not hits.is_empty():
		print("      note (other areas, not a failure): pre-rename name found in %s" % ", ".join(hits))
	kit.ok(true, "reported")
	return true
