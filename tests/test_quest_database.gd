extends RefCounted
## documentation/QUEST_DATABASE.md must stay in sync with data/v3: every quest, objective, item, flag, event,
## choice, puzzle, dialogue node, scene and cinematic id appears in the document, every objective/item/choice
## German text is quoted correctly, and the document names the protagonist Konrad.

const Kit := preload("res://tests/support/test_kit.gd")
const ENGINE := preload("res://scripts/story/story_engine.gd")
const DOC := "res://documentation/QUEST_DATABASE.md"

var kit: Kit
var doc := ""
var data: Dictionary = {}
var strings: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	doc = FileAccess.get_file_as_string(DOC)
	data = ENGINE.load_data()["data"]
	strings = data["locale_de"]["strings"]
	kit.run_case("document_exists", func() -> bool:
		kit.ok(doc.length() > 2000, "QUEST_DATABASE.md present")
		return true)
	kit.run_case("all_ids_documented", _ids)
	kit.run_case("german_texts_quoted", _texts)
	kit.run_case("protagonist_and_callbacks", _content)
	kit.cleanup()
	return kit.failures


func _has_id(id: String) -> bool:
	return doc.contains("`" + id + "`")


func _ids() -> bool:
	var ids: Array = []
	for q in data["quests"]["quests"]:
		ids.append(q["id"])
		for o in q["objectives"]:
			ids.append(o["id"])
			for c in o.get("choices", []):
				ids.append(c["id"])
	for it in data["items"]["items"]:
		ids.append(it["id"])
	for f in data["flags"]["flags"]:
		ids.append(f)
	ids.append_array(data["flags"]["events"])
	for p in data["puzzles"]["puzzles"]:
		ids.append(p["id"])
	for conv in data["dialogue"]["conversations"]:
		ids.append(conv["id"])
		for node in conv["nodes"]:
			ids.append(node["id"])
	for s in data["scenes"]["scenes"]:
		ids.append(s["id"])
	for seq in data["cinematics"]["sequences"]:
		ids.append(seq["id"])
	var missing: Array = ids.filter(func(id) -> bool: return not _has_id(str(id)))
	kit.eq(missing, [], "ids not documented in QUEST_DATABASE.md")
	return true


func _texts() -> bool:
	var keys: Array = []
	for q in data["quests"]["quests"]:
		for o in q["objectives"]:
			keys.append(o["text_key"])
			for c in o.get("choices", []):
				keys.append(c["text_key"])
	for it in data["items"]["items"]:
		keys.append_array([it["name_key"], it["description_key"]])
	for conv in data["dialogue"]["conversations"]:
		for node in conv["nodes"]:
			keys.append(node["text_key"])
	for k in keys:
		kit.ok(doc.contains(strings[k]), "German text of %s quoted verbatim" % k)
	return true


func _content() -> bool:
	kit.ok(doc.contains("Konrad Adler"), "protagonist named Konrad Adler")
	for hook in ["C3_IRINA_WITNESS", "C3_ALEXEI_SILENCE", "C3_KONRAD_COPY", "C3_ARCHIVE_ALERTED"]:
		kit.ok(doc.contains(hook), "Chapter-3 callback %s documented" % hook)
	kit.ok(doc.contains("PLANNED, NOT IMPLEMENTED"), "callbacks clearly marked as planned")
	return true
