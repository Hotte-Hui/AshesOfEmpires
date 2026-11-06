extends RefCounted
## Chapter 4 part 2 exploration (documentation/C4P2_DESIGN.md §4/§6/§7, TECHNICAL_ARCHITECTURE §12.1/§12.3/§12.8/§12.9;
## owner: exploration c4p2): the finds and chats of the two shared level files (L_C4P2_Karsk: Story scenes A + B under
## the level key L_C4P2_KarskA; L_C4P2_Berlin: A + B under L_C4P2_BerlinA), the side tasks „Ein Paket über die Linie“
## and „Ein Korb für Frau Grabowski“, four real-history cards and the mini-games „Die Drehscheibe“
## (scenes/ui/minigames/Turntable.tscn) and „Die Gepäckwaage“ (scenes/ui/minigames/LuggageScale.tscn).
##  * data: files, ids, kinds, levels, the `scene` of every find, texts (German style, lengths), chats (speakers,
##    expressions, the protagonist of the walk area speaks), cards (sources only in the data, 450–800 characters,
##    unlocked where they belong), Explore validation of the real data
##  * placement: every entry placed exactly once, hotspots resolve (scene.json + explore_hotspots.json, the info block
##    of the art contract), walk band, walk area of the scene, blockers, spacing to story / NPC spots, spawns and the
##    other finds; the gates of every node (after / until / memory_scenes) follow its scene
##  * the drivers: every find, chat and task step is reached in its own scene at the exploration passes of
##    --autoplay-explore and the walks of --inputplay-explore (with the three passes this stream asks the lead to add —
##    a pending note names any that the installed drivers still lack); the real Game path: both real level files
##    mounted with the live Story at every pass, autoplay.pending_finds + Explore.find on the real nodes; memories open
##    the remembered walk area and the memory cards count their own walk area
##  * the mini-games: rules (physics and refusals of the turntable, the weights of the scale, no dead end), scenes (auto
##    mode, keys, pad, mouse, hints, cancel, full solve by keys only, compact layout, contrast, hint modes), sounds
## Writes nothing: Explore / Story / Settings / Game values touched here are restored before the case ends.

const Kit := preload("res://tests/support/test_kit.gd")
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const TTLogic := preload("res://scripts/ui/minigames/turntable_logic.gd")
const TTGame := preload("res://scripts/ui/minigames/turntable_game.gd")
const LGLogic := preload("res://scripts/ui/minigames/luggage_logic.gd")
const LGGame := preload("res://scripts/ui/minigames/luggage_game.gd")
const AUTOPLAY := "res://scripts/core/autoplay.gd"
const INPUTPLAY := "res://scripts/core/inputplay.gd"
const EXPLORE := "res://scripts/core/explore.gd"
const SPOT := "res://scripts/ui/minigames/lever_spot.gd"
const TT_SCENE := "res://scenes/ui/minigames/Turntable.tscn"
const TT_GAME := "res://scripts/ui/minigames/turntable_game.gd"
const LG_SCENE := "res://scenes/ui/minigames/LuggageScale.tscn"
const LG_GAME := "res://scripts/ui/minigames/luggage_game.gd"
const LOCALE := "res://data/locale/de_explore_c4p2.json"
const HISTORY_LOCALE := "res://data/locale/de_history_c4p2.json"
const FILES := ["c4p2_karsk.json", "c4p2_berlin.json", "c4p2_history_soviet.json", "c4p2_history_reich.json"]
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]
## New characters of this round (cast stream): their sheets may still be on the way while this suite runs.
const NEW_CAST := ["maria", "hanna", "wendt", "blockwart", "press_officer", "guard_karsk", "stapo_civil"]
## A voice from a dark window: no figure, no sheet; the dialogue box shows the silhouette.
const VOICE_ONLY := ["grabowski"]
const LEVELS := {
	"L_C4P2_KarskA": {"path": "res://scenes/levels/L_C4P2_Karsk.tscn", "env": "karsk_c4p2", "prefixes": ["karsk.depot."],
		"area": "karsk", "scenes": ["L_C4P2_KarskA", "L_C4P2_KarskB"],
		"story": ["dispatch_window", "irina_window", "coal_list", "maria_coal", "press_notice", "signal_post",
			"canteen_table", "lev_sandhouse", "sand_table", "sand_lamp", "express_door"],
		"npcs": ["irina_window", "maria_coal", "guard_coal", "signal_post", "minder_canteen", "lev_sandhouse",
			"express_door"], "total": 24},
	"L_C4P2_BerlinA": {"path": "res://scenes/levels/L_C4P2_Berlin.tscn", "env": "berlin_c4p2",
		"prefixes": ["berlin.ost.", "berlin.k14."], "area": "berlin", "scenes": ["L_C4P2_BerlinA", "L_C4P2_BerlinB"],
		"story": ["departure_board", "marta_buffet", "courier_car", "ekdahl_window", "dining_table", "gate_notice",
			"wendt_yard", "hanna_yard", "lodge_window", "yard_pump"],
		"npcs": ["marta_buffet", "shadow_kiosk", "ekdahl_window", "kuhnert_gate", "wendt_yard", "hanna_yard"], "total": 21},
}
## Per Story scene: who plays it, the x range of its walk area, the gates of its finds, its id prefix, how many entries.
const SCENES := {
	"L_C4P2_KarskA": {"who": "alexei", "x": [30.0, 852.0], "after": "", "until": "c4e_inspect_notice", "count": 9,
		"prefix": "karsk.depot."},
	"L_C4P2_KarskB": {"who": "alexei", "x": [904.0, 1895.0], "after": "c4e_inspect_notice", "until": "", "count": 15,
		"prefix": "karsk.depot."},
	"L_C4P2_BerlinA": {"who": "konrad", "x": [30.0, 892.0], "after": "", "until": "c4f_inspect_book", "count": 9,
		"prefix": "berlin.ost."},
	"L_C4P2_BerlinB": {"who": "konrad", "x": [944.0, 1895.0], "after": "c4f_inspect_book", "until": "", "count": 12,
		"prefix": "berlin.k14."},
}
## Chats keep their own gates (the first entry of a chain names the node): [after, until].
const CHAT_GATES := {
	"karsk.depot.chat_maria": ["c4e_talk_maria", "c4e_inspect_notice"],
	"karsk.depot.minder": ["c4e_inspect_notice", ""],
	"karsk.depot.chat_lev": ["c4g_inspect_card", "c4g_choose"],
	"karsk.depot.parcel_ask": ["c4e_inspect_notice", ""],
	"karsk.depot.parcel_conductor": ["c4e_inspect_notice", ""],
	"berlin.ost.chat_marta": ["c4f_talk_marta", "c4f_inspect_book"],
	"berlin.k14.chat_kuhnert": ["c4f_inspect_book", "c4h_solve_house"],
	"berlin.k14.chat_hanna": ["c4h_talk_hanna", "c4h_solve_house"],
	"berlin.k14.basket_rope": ["c4f_inspect_book", ""],
}
## Chats on a story NPC's anchor (the NPC must stand there) and chats with a painted life strip (art contract).
const NPC_CHATS := {"maria_coal": "maria", "minder_canteen": "press_officer", "lev_sandhouse": "lev",
	"marta_buffet": "marta", "kuhnert_gate": "blockwart", "hanna_yard": "hanna"}
const STRIP_CHATS := {"exp_task_parcel": "babushka", "exp_task_conductor": "conductor", "exp_task_basket": "grabowski"}
const GAP_STORY := 24.0
const GAP_FIND := 14.0
const GAP_SPAWN := 20.0
const HISTORY_AT := {"hist.soviet.propiska": "karsk.depot.duty_board",
	"hist.soviet.foreign_correspondents": "karsk.depot.minder",
	"hist.reich.schriftleitergesetz": "berlin.ost.kiosk", "hist.reich.blockleiter": "berlin.k14.windows"}
const TASKS := {
	"karsk.task.parcel": {"level": "L_C4P2_KarskA", "scene": "L_C4P2_KarskB", "title": "Ein Paket über die Linie",
		"steps": ["karsk.depot.parcel_ask", "karsk.depot.parcel_scale", "karsk.depot.parcel_letter",
			"karsk.depot.parcel_wire", "karsk.depot.parcel_conductor"],
		"spots": {"karsk.depot.parcel_ask": "exp_task_parcel", "karsk.depot.parcel_scale": "exp_task_scale",
			"karsk.depot.parcel_letter": "exp_task_parcel", "karsk.depot.parcel_wire": "exp_task_wire",
			"karsk.depot.parcel_conductor": "exp_task_conductor"}, "final": "c4g_choose"},
	"berlin.task.basket": {"level": "L_C4P2_BerlinA", "scene": "L_C4P2_BerlinB", "title": "Ein Korb für Frau Grabowski",
		"steps": ["berlin.k14.basket_rope", "berlin.k14.basket_coal", "berlin.k14.basket_up"],
		"spots": {"berlin.k14.basket_rope": "exp_task_basket", "berlin.k14.basket_coal": "exp_task_coal",
			"berlin.k14.basket_up": "exp_task_basket"}, "final": "c4h_talk_wendt"},
}
## explore id -> its mini-game scene (one per level file)
const MINIGAMES := {"karsk.depot.turntable": "res://scenes/ui/minigames/Turntable.tscn",
	"berlin.ost.luggage_scale": "res://scenes/ui/minigames/LuggageScale.tscn"}
const TT_SFX := ["mg_c4p2_tt_start", "mg_c4p2_tt_brake", "mg_c4p2_tt_bump", "mg_c4p2_tt_lock", "mg_c4p2_tt_roll"]
const LG_SFX := ["mg_c4p2_poise_coarse", "mg_c4p2_poise_fine", "mg_c4p2_beam_knock", "mg_c4p2_stamp"]
## The part-2 route through the Story API (C4P2_DESIGN §2.3).
const P2_ROUTE := [["c4e_inspect_order", "inspect"], ["c4e_talk_irina", "dialogue"], ["c4e_inspect_list", "inspect"],
	["c4e_talk_maria", "dialogue"], ["c4e_inspect_notice", "inspect"], ["c4f_inspect_board", "inspect"],
	["c4f_talk_marta", "dialogue"], ["c4f_inspect_courier", "inspect"], ["c4f_talk_ekdahl", "dialogue"],
	["c4f_inspect_book", "inspect"], ["c4g_talk_ekdahl", "dialogue"], ["c4g_inspect_book", "inspect"],
	["c4g_talk_lev", "dialogue"], ["c4g_solve_halves", "puzzle"], ["c4g_inspect_card", "inspect"],
	["c4g_choose", "choice"], ["c4h_inspect_gate", "inspect"], ["c4h_talk_hanna", "dialogue"],
	["c4h_inspect_cards", "inspect"], ["c4h_solve_house", "puzzle"], ["c4h_talk_wendt", "dialogue"]]
## Exploration passes this stream needs in the drivers besides the ones they have (integration notes of round 10):
## autoplay EXPLORE_AT gets all three; inputplay gets a mid-route walk before c4h_solve_house (its route walks already
## cover the other two: they walk before the last objective of every scene).
const REQUESTED_PASSES := ["c4e_inspect_notice", "c4f_inspect_book", "c4h_solve_house"]

var kit: Kit
var loc: Node
var real: Node                     # a private Explore instance with the real data
var data: Dictionary = {}          # file -> parsed
var entries: Dictionary = {}       # id -> entry (my files)
var cards: Dictionary = {}         # id -> card (my files)
var strings: Dictionary = {}       # my locale strings
var nodes: Dictionary = {}         # level key -> [{name, script, props}]
var hotspots: Dictionary = {}      # level key -> merged hotspots
var manifests: Dictionary = {}     # level key -> scene.json
var xinfo: Dictionary = {}         # level key -> explore_hotspots.json info


class MockEx extends RefCounted:
	var found := {}
	var req := {}

	func is_found(id: String) -> bool:
		return found.has(id)

	func can_find(id: String) -> bool:
		for r in req.get(id, []):
			if not found.has(str(r)):
				return false
		return true


## Stands in for a StoryNPC beside a chat spot (lever_spot.npc_present()).
class FakeNpc extends Node2D:
	var char_id := ""
	var present := true

	func is_present() -> bool:
		return present


func run() -> Array:
	kit = Kit.new()
	loc = kit.track(load("res://scripts/story/loc.gd").new())
	loc.reload()
	var settings: Node = Kit.root().get_node_or_null("Settings")
	var saved := {}
	if settings != null:
		for k in ["puzzle_hints", "text_scale", "high_contrast", "reduced_motion"]:
			saved[k] = settings.values.get(k)
		settings.values["puzzle_hints"] = 1
		settings.values["text_scale"] = 1.0
		settings.values["high_contrast"] = false
		settings.values["reduced_motion"] = false
	kit.run_case("data_files_ids_and_texts", _data)
	kit.run_case("history_cards", _history)
	kit.run_case("explore_validation_of_the_real_data", _validation)
	kit.run_case("placement_hotspots_and_spacing", _placement)
	kit.run_case("gates_follow_the_scene_of_every_find", _gates)
	kit.run_case("spot_memory_and_npc_presence", _spot_live)
	kit.run_case("side_task_parcel", _task.bind("karsk.task.parcel"))
	kit.run_case("side_task_basket", _task.bind("berlin.task.basket"))
	kit.run_case("drivers_reach_every_entry_in_its_scene", _drivers)
	kit.run_case("real_game_path_every_pass", _real_path)
	kit.run_case("memory_cards_count_their_walk_area", _memory_counts)
	kit.run_case("turntable_logic", _tt_logic)
	kit.run_case("turntable_scene_auto_keys_mouse_hints_cancel", _tt_scene)
	kit.run_case("turntable_scene_full_solve_by_keys", _tt_full)
	if settings != null:
		kit.run_case("turntable_compact_contrast_and_hint_modes", _tt_compact.bind(settings))
	kit.run_case("luggage_logic", _lg_logic)
	kit.run_case("luggage_scene_auto_keys_mouse_hints_cancel", _lg_scene)
	kit.run_case("luggage_scene_full_solve_by_keys", _lg_full)
	if settings != null:
		kit.run_case("luggage_compact_contrast_and_hint_modes", _lg_compact.bind(settings))
	kit.run_case("minigame_sounds_texts_and_placement", _mg_assets)
	if settings != null:
		for k in saved:
			if saved[k] == null:
				settings.values.erase(k)
			else:
				settings.values[k] = saved[k]
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _key(k: int, down := true) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = k
	ev.physical_keycode = k
	ev.pressed = down
	return ev


func _pad(b: int, down := true) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.button_index = b
	ev.pressed = down
	return ev


func _mouse(button: int, pos: Vector2, down := true) -> InputEventMouseButton:
	var ev := InputEventMouseButton.new()
	ev.button_index = button
	ev.pressed = down
	ev.position = pos
	return ev


func _instance(path: String) -> Node:
	var mg: Node = load(path).instantiate()
	Kit.root().add_child(mg)
	kit.track(mg)
	return mg


func _steps(mg: Node, seconds: float, dt := 1.0 / 60.0) -> void:
	for i in int(ceil(seconds / dt)):
		mg._process(dt)


func _scene_of(id: String) -> String:
	return str(entries.get(id, {}).get("scene", ""))


static func _prefix_ok(id: String, prefixes: Array) -> bool:
	for p in prefixes:
		if id.begins_with(str(p)):
			return true
	return false


# ================================================================ data
func _data() -> bool:
	for f in FILES:
		var d = _json("res://data/explore/" + f)
		if kit.ok(d is Dictionary, "%s parses" % f):
			data[f] = d
	var lf = _json(LOCALE)
	if kit.ok(lf is Dictionary and lf.get("strings") is Dictionary, "de_explore_c4p2.json parses"):
		strings = (lf["strings"] as Dictionary).duplicate()
	var hf = _json(HISTORY_LOCALE)
	if kit.ok(hf is Dictionary and hf.get("strings") is Dictionary, "de_history_c4p2.json parses"):
		strings.merge(hf["strings"])
	for f in data:
		for e in data[f].get("entries", []):
			kit.ok(not entries.has(str(e.get("id", ""))), "entry %s defined once" % e.get("id"))
			var ee: Dictionary = (e as Dictionary).duplicate(true)
			ee["_area"] = str(e.get("area", data[f].get("area", "")))
			entries[str(e.get("id", ""))] = ee
		for c in data[f].get("cards", []):
			cards[str(c.get("id", ""))] = c
	var per := {}
	for id in entries:
		var e: Dictionary = entries[id]
		var lvl := str(e.get("level", ""))
		if not kit.ok(LEVELS.has(lvl), "%s: level %s is a part-2 level key %s" % [id, lvl, LEVELS.keys()]):
			continue
		var spec: Dictionary = LEVELS[lvl]
		kit.ok(_prefix_ok(str(id), spec["prefixes"]), "%s: id follows %s<name>" % [id, spec["prefixes"]])
		kit.eq(str(e["_area"]), str(spec["area"]), "%s: area %s" % [id, spec["area"]])
		var sc := str(e.get("scene", ""))
		if not kit.ok(sc in spec["scenes"], "%s: scene %s is one of %s" % [id, sc, spec["scenes"]]):
			continue
		kit.ok(str(id).begins_with(str(SCENES[sc]["prefix"])), "%s: the id names the place of %s" % [id, sc])
		per[sc] = int(per.get(sc, 0)) + 1
		kit.ok(str(e.get("kind")) in ["detail", "secret", "easter_egg", "chat"], "%s: kind %s" % [id, e.get("kind")])
		for k in ["title_key", "prompt_key", "text_key"]:
			var key := str(e.get(k, ""))
			if kit.ok(loc.has(key) and loc.t(key).strip_edges() != "", "%s: %s %s has German text" % [id, k, key]):
				kit.ok(loc.source_of(key).ends_with("de_explore_c4p2.json"), "%s comes from de_explore_c4p2.json" % key)
		kit.ok(loc.t(str(e.get("title_key"))).length() <= 32, "%s: title at most 32 characters" % id)
		kit.ok(loc.t(str(e.get("prompt_key"))).length() <= 32, "%s: prompt at most 32 characters" % id)
		var tl: int = loc.t(str(e.get("text_key"))).length()
		kit.ok(tl <= (420 if str(e.get("kind")) != "chat" else 260), "%s: text length %d" % [id, tl])
		if e.has("image"):
			kit.ok(ResourceLoader.exists(str(e["image"])), "%s: image %s exists" % [id, e["image"]])
		kit.eq(str(e.get("minigame", "")), str(MINIGAMES.get(id, "")), "%s: the mini-game scene (one per level)" % id)
		if str(e.get("kind")) == "chat":
			var lines: Array = e.get("lines", [])
			kit.ok(lines.size() >= 4 and lines.size() <= 9, "%s: 4-9 lines (%d)" % [id, lines.size()])
			var speakers := {}
			for l in lines:
				var sp := str(l.get("speaker", ""))
				speakers[sp] = true
				if not (sp in NEW_CAST) and not (sp in VOICE_ONLY):
					kit.ok(DirAccess.dir_exists_absolute("res://assets/characters/" + sp), "%s: speaker %s has a character folder" % [id, sp])
				kit.ok(loc.has("char.%s.name" % sp), "%s: speaker %s has a German name" % [id, sp])
				kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression %s" % [id, l.get("expr")])
				kit.ok(loc.has(str(l.get("key", ""))) and loc.t(str(l["key"])).length() <= 140,
					"%s: line %s resolves (<= 140, like every spoken line of part 2)" % [id, l.get("key")])
			kit.ok(speakers.has(str(SCENES[sc]["who"])), "%s: %s (who plays %s) speaks" % [id, SCENES[sc]["who"], sc])
			kit.ok(speakers.size() >= 2, "%s: a conversation, not a monologue" % id)
		else:
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
	for sc in SCENES:
		kit.eq(int(per.get(sc, 0)), int(SCENES[sc]["count"]), "%s: entries reached in this scene" % sc)
	# German typography and the rename guard over every string of my locale files
	for k in strings:
		var s := str(strings[k])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' is not empty and has no stray spaces" % k)
		kit.ok(not s.contains("\""), "'%s': German quotes, not ASCII" % k)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % k)
		kit.ok(not s.contains("..."), "'%s': ellipsis as '…'" % k)
		kit.ok(s.count("„") == s.count("“") and s.count("‚") == s.count("‘"), "'%s': balanced German quotes" % k)
		kit.ok(not s.contains("'"), "'%s': typographic apostrophe, not ASCII" % k)
	var old: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	if kit.ok(old != "", "pre-rename id derivable"):
		var raw := FileAccess.get_file_as_string(LOCALE).to_lower() + FileAccess.get_file_as_string(HISTORY_LOCALE).to_lower()
		for f in FILES:
			raw += FileAccess.get_file_as_string("res://data/explore/" + f).to_lower()
		raw += FileAccess.get_file_as_string(TT_GAME).to_lower() + FileAccess.get_file_as_string(LG_GAME).to_lower()
		kit.ok(not raw.contains(old), "texts, data and mini-games never use the pre-rename name")
	# every key of my locale is used (no orphan text): entries, chats, tasks, cards, mini-games, places, the voice
	var used := {}
	for id in entries:
		for k in ["title_key", "prompt_key", "text_key"]:
			used[str(entries[id][k])] = true
		for l in entries[id].get("lines", []):
			used[str(l["key"])] = true
	for c in cards.values():
		used[str(c["title_key"])] = true
		used[str(c["text_key"])] = true
	for f in data:
		for t in data[f].get("tasks", []):
			used[str(t["title_key"])] = true
			used[str(t["summary_key"])] = true
			for s in t.get("steps", []):
				used[str(s["hint_key"])] = true
	var src := FileAccess.get_file_as_string(TT_GAME) + FileAccess.get_file_as_string(LG_GAME) \
		+ FileAccess.get_file_as_string("res://scripts/ui/minigames/luggage_logic.gd")
	for k in strings:
		var ks := str(k)
		if ks.begins_with("mg.turntable.") or ks.begins_with("mg.luggage."):
			kit.ok(src.contains("\"%s\"" % ks) or (ks.begins_with("mg.luggage.dir.") and src.contains("\"mg.luggage.dir.\""))
				or (ks.begins_with("mg.luggage.item.") and src.contains("\"%s\"" % ks)), "the mini-game uses %s" % ks)
			continue
		if ks.begins_with("ui.explore.place.") or ks == "char.grabowski.name":
			continue
		kit.ok(used.has(k), "locale key %s is used" % k)
	for lid in LEVELS:
		kit.ok(loc.has("ui.explore.place." + lid), "place line for %s" % lid)
	kit.eq(loc.t("char.grabowski.name"), "Frau Grabowski", "the voice from the window has a name")
	return true


func _history() -> bool:
	kit.eq(Kit.sorted(cards.keys()), Kit.sorted(HISTORY_AT.keys()), "four new real-history cards")
	var sides: Array = []
	for f in ["c4p2_history_soviet.json", "c4p2_history_reich.json"]:
		sides.append(str(data.get(f, {}).get("side", "")))
	kit.eq(sides, ["soviet", "reich"], "one file per side")
	# no duplicate of an existing card: ids and topics of the other history files stay theirs
	var others := {}
	var dir := DirAccess.open("res://data/explore/")
	if dir != null:
		for f in dir.get_files():
			if str(f).ends_with(".json") and not (str(f) in FILES):
				var d = _json("res://data/explore/" + str(f))
				if d is Dictionary:
					for c in d.get("cards", []):
						others[str(c.get("id", ""))] = str(c.get("text_key", ""))
	kit.ok(others.size() >= 25, "the earlier cards are there to compare (%d)" % others.size())
	for cid in HISTORY_AT:
		kit.ok(not others.has(cid), "%s is a new topic" % cid)
		var c: Dictionary = cards.get(cid, {})
		if not kit.ok(not c.is_empty(), "card %s exists" % cid):
			continue
		kit.eq(str(c.get("side", "")), str(cid).split(".")[1], "%s: side" % cid)
		kit.ok(str(c.get("year", "")).length() == 4, "%s: year" % cid)
		var txt: String = loc.t(str(c.get("text_key", "")))
		kit.ok(txt.length() >= 450 and txt.length() <= 800, "%s: text length %d within 450-800" % [cid, txt.length()])
		kit.ok(loc.source_of(str(c.get("text_key", ""))).ends_with("de_history_c4p2.json"), "%s: text from de_history_c4p2.json" % cid)
		kit.ok(not txt.contains("http") and not txt.contains("Quelle") and not txt.contains("Wikipedia"), "%s: no sources on the card" % cid)
		var web := 0
		for s in c.get("sources", []):
			kit.ok(s is Dictionary and str(s.get("label", "")).strip_edges() != "", "%s: every source has a label" % cid)
			var url := str(s.get("url", "")) if s is Dictionary else ""
			kit.ok(url == "" or url.begins_with("https://"), "%s: source url %s" % [cid, url])
			if url != "":
				web += 1
		kit.ok(web >= 3, "%s: at least three web sources (%d)" % [cid, web])
		var at: Dictionary = entries.get(HISTORY_AT[cid], {})
		kit.ok((at.get("history", []) as Array).has(cid), "%s is unlocked by %s" % [cid, HISTORY_AT[cid]])
		kit.ok(str(at.get("kind", "")) in ["detail", "chat"], "%s: unlocked by a regular find or chat, never a hidden one" % cid)
		for ok_ in others:
			if loc.has(str(others[ok_])):
				kit.ne(txt, loc.t(str(others[ok_])), "%s is not the text of %s" % [cid, ok_])
	for id in entries:
		if not (id in HISTORY_AT.values()):
			kit.ok((entries[id].get("history", []) as Array).is_empty(), "%s unlocks no card" % id)
	return true


func _validation() -> bool:
	real = kit.track(load(EXPLORE).new())
	real.print_warnings = false
	real.notify_tasks = false
	real.reload()
	var mine: Array = []
	for w in real.warnings:
		var s := str(w)
		var hit := s.contains("c4p2_") or s.contains("karsk.task.parcel") or s.contains("berlin.task.basket")
		for id in entries:
			hit = hit or s.contains("'%s'" % id) or s.contains(str(id) + ":")
		for cid in cards:
			hit = hit or s.contains(cid)
		if hit:
			mine.append(s)
	kit.eq(mine, [], "Explore validation: no problem in the part-2 data")
	for id in entries:
		kit.ok(real.has_entry(id), "Explore loaded %s" % id)
	for cid in cards:
		kit.ok(real.has_card(cid), "Explore loaded card %s" % cid)
	for lid in LEVELS:
		kit.eq(real.counts(lid)["total"], int(LEVELS[lid]["total"]), "counts(%s) sees every find of the level file" % lid)
	kit.eq(real.tasks_for("L_C4P2_KarskA").map(func(t): return str(t["id"])), ["karsk.task.parcel"], "the depot's one side task")
	kit.eq(real.tasks_for("L_C4P2_BerlinA").map(func(t): return str(t["id"])), ["berlin.task.basket"], "the Berlin file's one side task")
	return true


# ================================================================ placement
static func _nodes_of(ps: PackedScene) -> Array:
	var out: Array = []
	var st: SceneState = ps.get_state()
	for i in st.get_node_count():
		var props := {}
		var script_path := ""
		for j in st.get_node_property_count(i):
			var pn := str(st.get_node_property_name(i, j))
			var pv = st.get_node_property_value(i, j)
			if pn == "script":
				script_path = pv.resource_path if pv is Resource else ""
			else:
				props[pn] = pv
		out.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props})
	return out


func _explore_nodes(lid: String) -> Array:
	return (nodes.get(lid, []) as Array).filter(func(n): return str(n["props"].get("kind", "")) in ["discover", "chat"])


func _pos(lid: String, hid: String) -> Vector2:
	var h = (hotspots.get(lid, {}) as Dictionary).get(hid, null)
	return Vector2(float(h[0]), float(h[1])) if h is Array and h.size() >= 2 else Vector2.INF


func _ids_of(n: Dictionary) -> Array:
	var chain: Array = Array(n["props"].get("explore_chain", PackedStringArray()))
	return chain if not chain.is_empty() else [str(n["props"].get("explore_id", ""))]


func _load_levels() -> void:
	if not nodes.is_empty():
		return
	for lid in LEVELS:
		var spec: Dictionary = LEVELS[lid]
		var ps = load(str(spec["path"]))
		if not (ps is PackedScene):
			continue
		nodes[lid] = _nodes_of(ps)
		var env := "res://assets/environments/%s/" % spec["env"]
		var man = _json(env + "scene.json")
		manifests[lid] = man if man is Dictionary else {}
		var hs := {}
		var x = _json(env + "explore_hotspots.json")
		if x is Dictionary and x.get("hotspots") is Dictionary:
			hs.merge(x["hotspots"], true)
			xinfo[lid] = x.get("info", {})
		if manifests[lid].get("hotspots") is Dictionary:
			hs.merge(manifests[lid]["hotspots"], true)        # scene.json wins (Level._merge_explore_hotspots)
		hotspots[lid] = hs


func _placement() -> bool:
	_load_levels()
	for lid in LEVELS:
		kit.ok(nodes.has(lid), "%s loads" % LEVELS[lid]["path"])
	var count := {}
	for lid in nodes:
		var spec: Dictionary = LEVELS[lid]
		var walk := PackedVector2Array()
		for q in manifests[lid].get("walkable", []):
			walk.append(Vector2(float(q[0]), float(q[1])))
		var blockers: Array = []
		for b in manifests[lid].get("blockers", []):
			var r: Array = b.get("rect", []) if b is Dictionary else []
			if r.size() == 4:
				blockers.append(Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])))
		var finds := _explore_nodes(lid)
		kit.ok(finds.size() >= int(spec["total"]) - 3, "%s: exploration nodes placed (%d)" % [lid, finds.size()])
		for n in finds:
			var p: Dictionary = n["props"]
			var who := "%s/%s" % [lid, n["name"]]
			var ids := _ids_of(n)
			for id in ids:
				count[str(id)] = (count.get(str(id), []) as Array) + [who]
				if kit.ok(entries.has(str(id)), "%s: entry %s exists" % [who, id]):
					kit.eq(str(entries[str(id)]["level"]), lid, "%s: %s belongs to this level key" % [who, id])
			var first := str(p.get("explore_id", ""))
			if entries.has(first):
				kit.eq(str(p.get("kind")), "chat" if str(entries[first]["kind"]) == "chat" else "discover", "%s: node kind matches %s" % [who, first])
			if ids.size() > 1:
				var fresh := MockEx.new()
				for id in entries:
					fresh.req[id] = entries[id].get("requires", [])
				kit.eq(first, INTERACTABLE.pick_chain_step(PackedStringArray(ids), fresh), "%s: explore_id is the chain's entry in a new game" % who)
				var sc0 := _scene_of(str(ids[0]))
				for id in ids:
					kit.eq(_scene_of(str(id)), sc0, "%s: every entry of the chain plays in %s" % [who, sc0])
					kit.eq(str(entries.get(str(id), {}).get("kind", "")), str(entries.get(str(ids[0]), {}).get("kind", "")),
						"%s: one kind along the chain" % who)
			kit.ok(bool(p.get("once", false)), "%s: once" % who)
			kit.ok(not p.has("char_id"), "%s: no NPC node (the story stream's NPC list stays its own)" % who)
			var hid := str(p.get("hotspot_id", ""))
			var pos := _pos(lid, hid)
			if not kit.ok(pos.is_finite(), "%s: hotspot %s resolves" % [who, hid]):
				continue
			kit.eq(pos.y, 300.0, "%s: on the feet line" % who)
			if walk.size() >= 3:
				kit.ok(Geometry2D.is_point_in_polygon(pos, walk), "%s at %s lies in the walk band" % [who, pos])
			for b in blockers:
				kit.ok(pos.x < (b as Rect2).position.x - 6.0 or pos.x > (b as Rect2).end.x + 6.0, "%s keeps clear of the blocker %s" % [who, b])
			var sc := _scene_of(first)
			if SCENES.has(sc):
				var xr: Array = SCENES[sc]["x"]
				kit.ok(pos.x >= float(xr[0]) and pos.x <= float(xr[1]), "%s (x %d) lies in the walk area of %s %s" % [who, int(pos.x), sc, xr])
			var on_npc: bool = str(p.get("kind")) == "chat" and NPC_CHATS.has(hid)
			if str(p.get("kind")) == "chat":
				kit.ok(on_npc or STRIP_CHATS.has(hid), "%s: a chat stands on an NPC's spot or at a painted life strip" % who)
			for s in spec["story"] + spec["npcs"]:
				if on_npc and str(s) == hid:
					continue
				var sp := _pos(lid, str(s))
				if sp.is_finite():
					kit.ok(pos.distance_to(sp) >= GAP_STORY, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_STORY), s, pos.distance_to(sp)])
			var speaker := ""
			if on_npc:
				speaker = str(NPC_CHATS[hid])
				kit.eq(str(p.get("npc_id", "")), speaker, "%s: a chat on an NPC anchor turns that NPC" % who)
			elif STRIP_CHATS.has(hid) and str(p.get("kind")) == "chat":
				speaker = str(STRIP_CHATS[hid])
				kit.eq(str(p.get("npc_id", "")), "", "%s: no Story NPC stands at a life strip" % who)
			if speaker != "":
				for id in ids:
					var sps: Array = (entries.get(str(id), {}).get("lines", []) as Array).map(func(l): return str(l.get("speaker", "")))
					kit.ok(speaker in sps, "%s: %s speaks in %s" % [who, speaker, id])
			if not on_npc:
				var inf: Dictionary = (xinfo.get(lid, {}) as Dictionary).get(hid, {})
				if kit.ok(not inf.is_empty(), "%s: %s has an art-contract entry (info)" % [who, hid]):
					var fc: Array = inf.get("focus", [])
					kit.ok(fc.size() == 2 and absf(float(fc[0]) - pos.x) <= 48.0 and float(fc[1]) < 300.0, "%s: focus %s painted near the spot" % [who, fc])
					kit.ok(str(inf.get("what", "")).length() >= 20, "%s: the art contract says what to paint" % who)
					kit.eq(inf.get("stand", []), [pos.x, pos.y], "%s: the art contract's stand is the spot" % who)
			for o in finds:
				var op := _pos(lid, str(o["props"].get("hotspot_id", "")))
				if o["name"] == n["name"] or not op.is_finite() or str(o["props"].get("hotspot_id")) == hid:
					continue
				kit.ok(pos.distance_to(op) >= GAP_FIND, "%s keeps %d px from %s (%.1f)" % [who, int(GAP_FIND), o["name"], pos.distance_to(op)])
		for spn in manifests[lid].get("spawns", {}):
			var sv = manifests[lid]["spawns"][spn]
			var spp := Vector2(float(sv[0]), float(sv[1]))
			for n in finds:
				var pp := _pos(lid, str(n["props"].get("hotspot_id", "")))
				if pp.is_finite():
					kit.ok(pp.distance_to(spp) >= GAP_SPAWN, "%s keeps clear of the spawn %s" % [n["name"], spn])
	for id in entries:
		kit.eq((count.get(id, []) as Array).size(), 1, "%s placed exactly once %s" % [id, count.get(id, [])])
	# the explore stream's own hotspots: only exp_* names, never a story name of §4, each with its art contract
	for lid in LEVELS:
		var x = _json("res://assets/environments/%s/explore_hotspots.json" % LEVELS[lid]["env"])
		var info: Dictionary = x.get("info", {}) if x is Dictionary else {}
		for h in (x.get("hotspots", {}) if x is Dictionary else {}):
			kit.ok(str(h).begins_with("exp_"), "%s: explore hotspot %s is an exp_* name" % [lid, h])
			kit.ok(not (h in LEVELS[lid]["story"]) and not (h in LEVELS[lid]["npcs"]), "%s: %s is no story name" % [lid, h])
			kit.ok(info.has(h), "%s: %s has its art contract" % [lid, h])
		for h in info:
			kit.ok((x.get("hotspots", {}) as Dictionary).has(h), "%s: info %s names a hotspot" % [lid, h])
	return true


# ================================================================ gates
func _gates() -> bool:
	_load_levels()
	var quests = _json("res://data/v3/quests.json")
	var known := {}
	for q in (quests.get("quests", []) if quests is Dictionary else []):
		for o in q.get("objectives", []):
			known[str(o.get("id", ""))] = true
	for lid in nodes:
		for n in _explore_nodes(lid):
			var p: Dictionary = n["props"]
			var who := "%s/%s" % [lid, n["name"]]
			kit.eq(n["script"], SPOT, "%s: the C4 spot script (memory-aware gates, NPC presence)" % who)
			var first := str(_ids_of(n)[0])
			var sc := _scene_of(first)
			if not SCENES.has(sc):
				continue
			var want: Array = [str(SCENES[sc]["after"]), str(SCENES[sc]["until"])]
			if str(p.get("kind")) == "chat":
				kit.ok(CHAT_GATES.has(first), "%s: the chat %s has its gates in this test" % [who, first])
				want = CHAT_GATES.get(first, want)
			kit.eq([str(p.get("after_objective", "")), str(p.get("until_objective", ""))], want, "%s: open in %s (after / until)" % [who, sc])
			# a chat's gates lie inside its scene's gates: never open in the other walk area
			if str(SCENES[sc]["until"]) != "":
				kit.ok(str(p.get("until_objective", "")) != "", "%s: closes with its walk area" % who)
			if str(SCENES[sc]["after"]) != "" and str(p.get("after_objective", "")) != str(SCENES[sc]["after"]):
				var a_i := _route_index(str(p.get("after_objective", "")))
				kit.ok(a_i >= _route_index(str(SCENES[sc]["after"])), "%s: opens no earlier than its walk area" % who)
			kit.eq(Array(p.get("memory_scenes", PackedStringArray())), [sc], "%s: remembered in %s" % [who, sc])
			for g in [str(p.get("after_objective", "")), str(p.get("until_objective", ""))]:
				if g != "":
					kit.ok(known.has(g), "%s: gate %s is a Story objective" % [who, g])
	return true


static func _route_index(oid: String) -> int:
	for i in P2_ROUTE.size():
		if str(P2_ROUTE[i][0]) == oid:
			return i
	return -1


## Live: lever_spot follows the remembered scene inside a memory and hides a chat whose NPC is absent.
func _spot_live() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if game == null or ex == null or not ("memory_mode" in game):
		print("      note: autoloads missing, live spot check skipped")
		return true
	var before: Dictionary = ex.state()
	ex.restore({"found": [], "cards": []})
	var holder := Node2D.new()
	kit.mount(holder)
	var a_spot: Node = load(SPOT).new()
	a_spot.kind = "discover"
	a_spot.explore_id = "karsk.depot.water_crane"
	a_spot.once = true
	a_spot.until_objective = "c4e_inspect_notice"
	a_spot.memory_scenes = PackedStringArray(["L_C4P2_KarskA"])
	holder.add_child(a_spot)
	var b_spot: Node = load(SPOT).new()
	b_spot.kind = "discover"
	b_spot.explore_id = "karsk.depot.turntable"
	b_spot.once = true
	b_spot.after_objective = "c4e_inspect_notice"
	b_spot.memory_scenes = PackedStringArray(["L_C4P2_KarskB"])
	holder.add_child(b_spot)
	var chat: Node = load(SPOT).new()
	chat.kind = "chat"
	chat.explore_id = "karsk.depot.chat_maria"
	chat.npc_id = "maria"
	chat.once = true
	chat.after_objective = "c4e_talk_maria"
	chat.until_objective = "c4e_inspect_notice"
	chat.memory_scenes = PackedStringArray(["L_C4P2_KarskA"])
	chat.position = Vector2(560, 300)
	holder.add_child(chat)
	var maria := FakeNpc.new()
	maria.char_id = "maria"
	maria.position = Vector2(578, 300)
	holder.add_child(maria)
	var mm = game.memory_mode
	var ms = game.memory_scene
	game.memory_mode = true
	game.memory_scene = "L_C4P2_KarskA"
	var in_a := [a_spot.is_active(), b_spot.is_active(), chat.is_active()]
	maria.present = false
	var gone: bool = chat.is_active()
	maria.present = true
	game.memory_scene = "L_C4P2_KarskB"
	var in_b := [a_spot.is_active(), b_spot.is_active(), chat.is_active()]
	game.memory_scene = "L_C4P2_BerlinA"
	var other := [a_spot.is_active(), b_spot.is_active(), chat.is_active()]
	holder.remove_child(maria)
	maria.free()
	game.memory_scene = "L_C4P2_KarskA"
	var no_npc: bool = chat.is_active()
	game.memory_mode = mm
	game.memory_scene = ms
	kit.eq(in_a, [true, false, true], "memory of the coal stage: its finds and Maria's chat, not the showcase")
	kit.ok(not gone, "an absent Maria (StoryNPC hidden) has no chat")
	kit.eq(in_b, [false, true, false], "memory of the showcase: the showcase's finds (the turntable) only")
	kit.eq(other, [false, false, false], "memory of the other city's scene: nothing here")
	kit.ok(no_npc, "without any NPC node (tests, harness) a chat is not blocked")
	ex.restore(before)
	return true


# ================================================================ side tasks
func _task(tid: String) -> bool:
	if real == null:
		return true
	var spec: Dictionary = TASKS[tid]
	var steps: Array = spec["steps"]
	var t: Dictionary = real.task(tid)
	if not kit.ok(not t.is_empty(), "task %s exists" % tid):
		return true
	kit.eq(str(t.get("level", "")), str(spec["level"]), "%s: level key of the file" % tid)
	kit.eq(real.task_steps(tid), steps, "%s: the steps in order" % tid)
	for k in ["title_key", "summary_key"]:
		kit.ok(loc.has(str(t.get(k, ""))) and loc.source_of(str(t[k])).ends_with("de_explore_c4p2.json"), "%s: %s in de_explore_c4p2.json" % [tid, k])
	kit.eq(loc.t(str(t["title_key"])), str(spec["title"]), "%s: the task's title (C4P2_DESIGN §6)" % tid)
	kit.ok(loc.t(str(t["summary_key"])).length() <= 200, "%s: summary at most 200 characters" % tid)
	for s in t.get("steps", []):
		kit.ok(loc.has(str(s.get("hint_key", ""))) and loc.t(str(s["hint_key"])).length() <= 120, "hint %s resolves (<= 120)" % s.get("hint_key"))
	kit.eq(real.requires_of(str(steps[0])), [], "%s: the first step is open as soon as its walk area is" % tid)
	for i in range(1, steps.size()):
		kit.eq(real.requires_of(str(steps[i])), [steps[i - 1]], "%s requires the step before" % steps[i])
	for id in steps:
		kit.eq(_scene_of(str(id)), str(spec["scene"]), "%s: every step in one walk area (%s)" % [id, spec["scene"]])
	kit.eq((t.get("reward_cards", []) as Array), [], "%s: the reward is a human beat, no history card" % tid)
	kit.ok(loc.has("ui.tasks.place." + str(spec["level"])), "the journal names the task's place")
	# placement: each step at its spot, the chats of one person chained on one node, steps are Task_* nodes
	_load_levels()
	var ns: Array = nodes.get(str(spec["level"]), [])
	for id in steps:
		var hit: Array = ns.filter(func(n): return str(id) in _ids_of(n))
		if not kit.ok(hit.size() == 1, "%s has one node" % id):
			continue
		kit.eq(str(hit[0]["props"].get("hotspot_id", "")), str(spec["spots"][id]), "%s stands at %s" % [id, spec["spots"][id]])
		kit.ok(str(hit[0]["name"]).begins_with("Task_"), "%s: a Task_* node" % id)
	# the state machine on the real data
	real.restore({"found": [], "cards": []})
	kit.eq(str(real.task_state(tid)["state"]), "not_started", "%s: not started in a new game" % tid)
	kit.ok(real.can_find(str(steps[0])) and not real.can_find(str(steps[1])), "%s: only the first step is findable at first" % tid)
	for i in steps.size():
		var r: Dictionary = real.find(str(steps[i]))
		kit.ok(bool(r.get("ok", false)) and bool(r.get("new", false)), "step %s found in order" % steps[i])
		kit.eq(str(real.task_state(tid)["state"]), "done" if i == steps.size() - 1 else "active", "state after %s" % steps[i])
	real.restore({"found": [], "cards": []})
	# the last word of each task (its human beat)
	var last: Dictionary = entries.get(str(steps[steps.size() - 1]), {})
	var lines: Array = last.get("lines", [])
	if tid == "karsk.task.parcel":
		kit.ok(not lines.is_empty() and str(lines[lines.size() - 1].get("speaker", "")) == "conductor", "the conductor has the last word")
		kit.ok(loc.t(str(last.get("text_key", ""))).contains("Hand vor den Mund"), "no reward but her face")
	else:
		kit.ok(not lines.is_empty() and str(lines[lines.size() - 1].get("speaker", "")) == "grabowski", "Frau Grabowski has the last word")
		kit.ok(loc.t(str(last.get("text_key", ""))).contains("Licht"), "she leaves her light on")
	return true


# ================================================================ the drivers
static func _done_before(oid: String) -> Dictionary:
	var done := {}
	for s in P2_ROUTE:
		if str(s[0]) == oid:
			break
		done[str(s[0])] = true
	return done


static func _scene_of_obj(oid: String) -> String:
	if oid.begins_with("c4e_"):
		return "L_C4P2_KarskA"
	if oid.begins_with("c4f_"):
		return "L_C4P2_BerlinA"
	if oid.begins_with("c4g_"):
		return "L_C4P2_KarskB"
	return "L_C4P2_BerlinB"


static func _level_of_scene(sc: String) -> String:
	return "L_C4P2_KarskA" if sc.begins_with("L_C4P2_Karsk") else "L_C4P2_BerlinA"


## The part-2 objectives before which --autoplay-explore explores (its EXPLORE_AT + FINAL_PASS), in route order.
func _autoplay_passes(with_requested: bool) -> Array:
	var ap: GDScript = load(AUTOPLAY)
	var m: Dictionary = ap.get_script_constant_map()
	var want := {}
	for oid in Array(m.get("EXPLORE_AT", [])) + Array(m.get("FINAL_PASS", [])):
		want[str(oid)] = true
	if with_requested:
		for oid in REQUESTED_PASSES:
			want[oid] = true
	var out: Array = []
	for s in P2_ROUTE:
		if want.has(str(s[0])):
			out.append(str(s[0]))
	return out


## The part-2 walks of --inputplay-explore: at every scene start and before the last objective of every scene
## (inputplay.gd _play_route), plus a mid-route walk before c4h_solve_house once installed (requested).
func _inputplay_walks(with_requested: bool) -> Array:
	var ip: GDScript = load(INPUTPLAY)
	var m: Dictionary = ip.get_script_constant_map()
	var want := {}
	for c in ["C4E", "C4F", "C4G", "C4H"]:
		var route: Array = m.get(c, [])
		if not route.is_empty():
			want[str(route[0])] = true
			want[str(route[route.size() - 1])] = true
	if with_requested or _inputplay_has_mid_walk("c4h_solve_house"):
		want["c4h_solve_house"] = true
	var out: Array = []
	for s in P2_ROUTE:
		if want.has(str(s[0])):
			out.append(str(s[0]))
	return out


## True when inputplay.gd walks the level before `oid` in the middle of a route: a line naming the objective together
## with the mid-route walk of the relay desk (c3b_inspect_booth) or the explore flag — not the puzzle's own line.
static func _inputplay_has_mid_walk(oid: String) -> bool:
	for line in FileAccess.get_file_as_string(INPUTPLAY).split("\n"):
		if line.contains("\"%s\"" % oid) and (line.contains("c3b_inspect_booth") or line.contains("inputplay-explore")):
			return true
	return false


## The drivers' loop on parsed nodes (MockEx), gates as at the pass before `oid`.
func _drive(ns: Array, m: MockEx, done: Dictionary) -> Array:
	var order: Array = []
	var progressed := true
	var guard := 0
	while progressed and guard < 100:
		guard += 1
		progressed = false
		for n in ns:
			var p: Dictionary = n["props"]
			if str(p.get("after_objective", "")) != "" and not done.has(str(p["after_objective"])):
				continue
			if str(p.get("until_objective", "")) != "" and done.has(str(p["until_objective"])):
				continue
			var chain := PackedStringArray(p.get("explore_chain", PackedStringArray()))
			var cur := INTERACTABLE.pick_chain_step(chain, m) if not chain.is_empty() else str(p.get("explore_id", ""))
			if cur == "" or m.found.has(cur) or not m.can_find(cur):
				continue
			m.found[cur] = true
			order.append(cur)
			progressed = true
	return order


## Which entries a set of passes reaches, and in which Story scene first: {id: scene}.
func _reach(passes: Array) -> Dictionary:
	var m := MockEx.new()
	for id in entries:
		m.req[id] = entries[id].get("requires", [])
	var first_seen := {}
	for oid in passes:
		var sc := _scene_of_obj(str(oid))
		for id in _drive(_explore_nodes(_level_of_scene(sc)), m, _done_before(str(oid))):
			if not first_seen.has(id):
				first_seen[id] = sc
	return first_seen


func _drivers() -> bool:
	_load_levels()
	for label in ["autoplay", "inputplay"]:
		var passes: Array = _autoplay_passes(true) if label == "autoplay" else _inputplay_walks(true)
		var seen := _reach(passes)
		for id in entries:
			kit.eq(str(seen.get(id, "")), _scene_of(id), "%s: %s is reached in its own scene" % [label, id])
		for tid in TASKS:
			kit.ok(str(TASKS[tid]["final"]) in passes, "%s: the level's last pass (%s) is a pass" % [label, TASKS[tid]["final"]])
	# what the drivers as installed still miss: reported, the lead adds the requested passes at integration
	var pending: Array = []
	for label in ["autoplay", "inputplay"]:
		var seen0 := _reach(_autoplay_passes(false) if label == "autoplay" else _inputplay_walks(false))
		for id in entries:
			if str(seen0.get(id, "")) != _scene_of(id):
				pending.append("%s misses %s" % [label, id])
				kit.eq(str(entries[id].get("kind", "")), "chat", "%s: only a story-gated chat waits for a requested pass" % id)
	if not pending.is_empty():
		print("      pending (integration patch of round 10, C4P2 explore): drivers need the passes %s — %s" % [
			REQUESTED_PASSES, ", ".join(pending)])
	return true


# ================================================================ the real Game path
## Plays the live Story to the pass before `oid` (a new game, the default route to c4d, then part 2).
func _story_to(st: Node, oid: String) -> void:
	st.new_game()
	kit.play_until(st, "c4d")
	for s in P2_ROUTE:
		var sid := str(s[0])
		if sid == oid:
			return
		match str(s[1]):
			"inspect":
				kit.step(st.inspect(sid), "inspect " + sid)
			"dialogue":
				kit.play_dialogue(st, sid)
			"puzzle":
				var pay = Kit.C4_HALVES.duplicate()
				if sid == "c4h_solve_house":
					pay = Kit.C4_HOUSE.duplicate()
				kit.step(st.solve_puzzle(sid, pay), "solve " + sid)
			"choice":
				kit.step(st.choose(sid, "publish_now"), "choose " + sid)


func _mount_level(path: String, lid: String) -> Node:
	var lvl: Node = (load(path) as PackedScene).instantiate()
	lvl.set("ambience", "")
	lvl.set("music", "")
	lvl.set("level_id", lid)
	Kit.root().add_child(lvl)
	return lvl


func _unmount_level(lvl: Node) -> void:
	if lvl != null and is_instance_valid(lvl):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


func _level_spots(lvl: Node) -> Array:
	var out: Array = []
	for it in Kit.tree().get_nodes_in_group("interactables"):
		if is_instance_valid(it) and lvl.is_ancestor_of(it):
			out.append(it)
	return out


## The drivers' pass on the real nodes: autoplay.pending_finds + what Game._do_discover / _do_chat do with Explore.
func _real_pass(lvl: Node, ex: Node) -> Array:
	var ap: GDScript = load(AUTOPLAY)
	var order: Array = []
	var tried := {}
	var guard := 0
	while guard < 200:
		guard += 1
		var it: Node = null
		for cand in ap.pending_finds(_level_spots(lvl), ex):
			if not tried.has("%d:%s" % [cand.get_instance_id(), cand.explore_id]):
				it = cand
				break
		if it == null:
			break
		var id := str(it.explore_id)
		tried["%d:%s" % [it.get_instance_id(), id]] = true
		it.used = true
		var r: Dictionary = ex.find(id)
		if bool(r.get("ok", false)):
			order.append(id)
	return order


func _real_path() -> bool:
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	var game: Node = Kit.root().get_node_or_null("Game")
	if st == null or ex == null or game == null:
		print("      note: autoloads missing, real-path check skipped")
		return true
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks, "mm": game.memory_mode,
		"ms": game.memory_scene}
	ex.notify_tasks = false
	game.memory_mode = false
	ex.restore({"found": [], "cards": []})
	var first_seen := {}
	for oid in _autoplay_passes(true):
		var sc := _scene_of_obj(str(oid))
		var lid := _level_of_scene(sc)
		_story_to(st, str(oid))
		if not kit.ok(st.is_available(str(oid)), "the live Story stands before %s" % oid):
			continue
		var snap: String = st.save_json()
		var lvl := _mount_level(str(LEVELS[lid]["path"]), sc)
		for id in _real_pass(lvl, ex):
			if not first_seen.has(id):
				first_seen[id] = sc
		for tid in TASKS:
			if str(TASKS[tid]["final"]) == str(oid):
				kit.eq(str(ex.task_state(tid)["state"]), "done", "the last pass of %s finds %s done" % [lid, tid])
		kit.eq(st.save_json(), snap, "exploring before %s leaves the Story untouched" % oid)
		_unmount_level(lvl)
	for id in entries:
		kit.eq(str(first_seen.get(id, "")), _scene_of(id), "real path: %s found in its own scene" % id)
	# a memory of the coal stage after the showcase: the coal stage's finds open, the showcase's not, and back
	_story_to(st, "c4h_inspect_gate")
	var lvl2 := _mount_level(str(LEVELS["L_C4P2_KarskA"]["path"]), "L_C4P2_KarskA")
	game.memory_mode = true
	var act := {}
	for msc in ["L_C4P2_KarskA", "L_C4P2_KarskB"]:
		game.memory_scene = msc
		var a := {}
		for it in _level_spots(lvl2):
			if str(it.kind) in ["discover", "chat"] and it.is_active():
				a[str(it.explore_id)] = true
		act[msc] = a
	game.memory_mode = false
	_unmount_level(lvl2)
	for id in entries:
		if str(entries[id]["level"]) != "L_C4P2_KarskA" or str(entries[id]["kind"]) == "chat":
			continue
		for msc in act:
			kit.eq((act[msc] as Dictionary).has(id), _scene_of(id) == msc, "memory of %s: %s open = %s" % [msc, id, _scene_of(id) == msc])
	game.memory_mode = keep["mm"]
	game.memory_scene = keep["ms"]
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]
	return true


## The memory cards (Game.memory_scenes) count the finds of their own walk area (game.gd reads the entries' "scene").
func _memory_counts() -> bool:
	var game: Node = Kit.root().get_node_or_null("Game")
	var st: Node = Kit.root().get_node_or_null("Story")
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if game == null or st == null or ex == null or not game.has_method("memory_scenes"):
		print("      note: autoloads missing, memory count check skipped")
		return true
	var ext = game.get("ext")
	if ext != null and ext.has_method("level_key"):
		kit.eq(str(ext.level_key("L_C4P2_KarskB")), "L_C4P2_KarskA", "the showcase counts under the depot's level key")
		kit.eq(str(ext.level_key("L_C4P2_BerlinB")), "L_C4P2_BerlinA", "the courtyard counts under the station's level key")
	kit.ok(FileAccess.get_file_as_string("res://scripts/core/game.gd").contains("e.get(\"scene\""), "game.gd counts per walk area")
	var keep := {"story": st.save_json(), "explore": ex.state(), "notify": ex.notify_tasks}
	ex.notify_tasks = false
	st.new_game()
	kit.play_until(st, "c4h")
	ex.restore({"found": ["karsk.depot.water_crane", "karsk.depot.turntable", "karsk.depot.parcel_ask",
		"berlin.ost.kiosk", "berlin.k14.windows", "berlin.k14.chat_hanna"], "cards": []})
	var got := {}
	for c in game.memory_scenes("game"):
		got[str(c.get("id", ""))] = c
	var want := {"L_C4P2_KarskA": 1, "L_C4P2_KarskB": 2, "L_C4P2_BerlinA": 1, "L_C4P2_BerlinB": 2}
	for sid in want:
		var c: Dictionary = got.get(sid, {})
		if not kit.ok(not c.is_empty() and bool(c.get("unlocked", false)), "memory card %s is unlocked after part 2" % sid):
			continue
		kit.eq([int(c.get("found", -1)), int(c.get("total", -1))], [int(want[sid]), int(SCENES[sid]["count"])],
			"memory card %s counts its own walk area" % sid)
	if not st.load_json(str(keep["story"])).get("ok", false):
		st.new_game()
	ex.restore(keep["explore"])
	ex.notify_tasks = keep["notify"]
	return true


# ================================================================ mini-game: the turntable
func _tt_logic() -> bool:
	var lg = TTLogic.new()
	kit.eq(lg.angle, TTLogic.ENTRY, "the engine stands at the entry track")
	kit.eq(TTLogic.target_angle(), 120.0, "stall 7 at 120° on the scale")
	kit.eq([TTLogic.shortest(270.0, 120.0), TTLogic.shortest(10.0, 350.0), TTLogic.shortest(350.0, 10.0)], [-150.0, -20.0, 20.0],
		"the shorter way round")
	kit.eq(TTLogic.wrap360(-30.0), 330.0, "angles wrap")
	# a tap: a few centimetres, the bridge comes to rest by itself
	lg.set_motor(1)
	lg.set_motor(0)
	for i in 120:
		lg.step(1.0 / 60.0)
	var tap: float = TTLogic.shortest(TTLogic.ENTRY, lg.angle)
	kit.ok(tap > 0.05 and tap < 0.3 and lg.is_still(), "a tap sets the bridge %.2f° on (a few centimetres)" % tap)
	kit.ok(TTLogic.cm_of(tap) < 10.0, "a tap: %.1f cm at the rim" % TTLogic.cm_of(tap))
	# held: accelerates to the top speed; released: coasts far; the brake stops it in a few degrees
	lg.reset()
	lg.set_motor(-1)
	for i in 240:
		lg.step(1.0 / 60.0)
	kit.ok(absf(lg.vel - (-TTLogic.MAX_SPEED)) < 0.01, "held, the bridge reaches its top speed")
	lg.set_motor(0)
	var a0: float = lg.angle
	var coast: float = lg.coast_distance(false)
	var brake: float = lg.coast_distance(true)
	kit.ok(coast > 60.0 and brake < 10.0, "it coasts %.0f° but brakes in %.1f°" % [coast, brake])
	lg.set_brake(true)
	var n := 0
	while not lg.is_still() and n < 600:
		lg.step(1.0 / 60.0)
		n += 1
	lg.set_brake(false)
	var braked: float = absf(TTLogic.shortest(a0, lg.angle))
	kit.ok(lg.is_still() and braked < 10.0, "braked to a stop within %.1f°" % braked)
	# refusals: moving, rails apart, the entry track, another stall; nothing moves on a refusal
	lg.reset()
	lg.vel = 3.0
	var r: Dictionary = lg.pull()
	kit.eq([r["ok"], r["reason"]], [false, "moving"], "a moving bridge cannot pull")
	lg.vel = 0.0
	lg.angle = TTLogic.ENTRY
	kit.eq(str(lg.pull()["reason"]), "entry", "at the entry track: that is where it came from")
	lg.angle = 90.05
	var w: Dictionary = lg.pull()
	kit.eq([w["reason"], w["track"]], ["wrong", 5], "stall 5 is the wrong stall")
	lg.angle = 121.0
	var g: Dictionary = lg.pull()
	kit.ok(str(g["reason"]) == "gap" and absf(float(g["cm"]) - 26.2) < 1.0, "1° off: the rails miss by %.1f cm" % float(g["cm"]))
	kit.eq([lg.angle, lg.vel, lg.done], [121.0, 0.0, false], "a refusal moves nothing")
	kit.eq(lg.pulls, 4, "four refused pulls counted")
	lg.angle = 120.15
	var ok: Dictionary = lg.pull()
	kit.ok(bool(ok["ok"]) and lg.done and lg.angle == 120.0, "within the tolerance at stall 7: the bolt drops, the engine rolls in")
	lg.set_motor(1)
	lg.step(0.5)
	kit.eq(lg.angle, 120.0, "after that the bridge stays")
	# no dead end: from every start angle, the hint's next moves reach stall 7 (simulated at 60 fps)
	var worst := 0.0
	var all_ok := true
	for start in range(0, 360, 15):
		var s = TTLogic.new()
		s.angle = float(start) + 0.37
		var t := 0.0
		var guard := 0
		while not s.done and guard < 4000:
			guard += 1
			var nx: Dictionary = s.next_move()
			match str(nx.get("do", "")):
				"drive":
					s.set_brake(false)
					s.set_motor(int(nx["dir"]))
				"wait":
					s.set_motor(0)
				"brake":
					s.set_motor(0)
					s.set_brake(true)
				"tap":
					s.set_brake(false)
					s.set_motor(int(nx["dir"]))
					s.step(1.0 / 60.0)
					s.set_motor(0)
				"pull":
					s.pull()
			s.step(1.0 / 60.0)
			t += 1.0 / 60.0
		all_ok = all_ok and s.done
		worst = maxf(worst, t)
	kit.ok(all_ok, "no dead end: from every angle the next moves reach stall 7")
	kit.ok(worst < 40.0, "within 40 s from the worst angle (%.1f s)" % worst)
	return true


func _tt_instance() -> Node:
	return _instance(TT_SCENE)


func _tt_scene() -> bool:
	var mg := _tt_instance()
	kit.ok(mg.is_in_group("minigame"), "Turntable joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "karsk.depot.turntable", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var tf := _tt_instance()
	var res: Array = []
	tf.finished.connect(func(ok: bool): res.append(ok))
	tf.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(tf, 0.4)
	kit.ok(str(tf._status.text).contains("Zufahrt"), "the status starts at the entry track")
	kit.ok(str(tf._angle_label.text).contains("270"), "the side panel reads the scale: 270°")
	tf.modal_input(_key(KEY_RIGHT))
	kit.ok(tf.logic.motor == -1 and tf.logic.vel < 0.0, "→ turns clockwise at once (the impulse)")
	_steps(tf, 0.6)
	var v_held: float = absf(tf.logic.vel)
	kit.ok(v_held > TTLogic.NUDGE, "held, the bridge gathers speed (%.1f °/s)" % v_held)
	tf.modal_input(_key(KEY_RIGHT, false))
	kit.eq(tf.logic.motor, 0, "released: the controller is off")
	_steps(tf, 0.3)
	kit.ok(not tf.logic.is_still(), "and the bridge coasts on")
	kit.ok(str(tf._status.text).contains("läuft nach"), "the status says it is coasting")
	tf.modal_input(_key(KEY_E))
	kit.eq(tf.fails, 1, "pulling on a moving bridge is refused (a failure)")
	kit.ok(str(tf._status.text).contains("läuft noch"), "the refusal names why")
	tf.modal_input(_key(KEY_SPACE))
	kit.ok(tf.logic.braking, "Space brakes while held")
	_steps(tf, 2.0)
	kit.ok(tf.logic.is_still(), "braked to a stop")
	tf.modal_input(_key(KEY_SPACE, false))
	kit.ok(not tf.logic.braking, "released, the brake lets go")
	tf.logic.angle = 100.0
	tf.modal_input(_key(KEY_ENTER))
	kit.ok(tf.fails == 2 and tf._hint_box.visible, "between the tracks: refused, a hint after two refusals")
	kit.ok(str(tf._status.text).contains("Zwischen den Gleisen"), "far from any track: the engine finds no rail")
	kit.ok(str(tf._hint_label.text).contains("Leertaste"), "the first hint: let go early and brake")
	tf.logic.angle = 104.0
	tf.modal_input(_key(KEY_ENTER))
	kit.ok(str(tf._status.text).contains("26 cm daneben"), "a degree off stall 6: the refusal says how far the rails miss")
	kit.ok(str(tf._hint_label.text).contains("120,0°"), "the third refusal brings the second hint")
	tf.show_hint(2)
	kit.ok(str(tf._hint_label.text).contains("120,0°"), "the second hint names stall 7's mark")
	tf.modal_input(_key(KEY_R))
	kit.eq([tf.logic.angle, tf.logic.vel], [TTLogic.ENTRY, 0.0], "R starts over at the entry track")
	# the pad: LB turns counter-clockwise while held, A brakes, Y starts over
	tf.modal_input(_pad(JOY_BUTTON_LEFT_SHOULDER))
	kit.eq(tf.logic.motor, 1, "pad LB turns counter-clockwise")
	tf.modal_input(_pad(JOY_BUTTON_LEFT_SHOULDER, false))
	tf.modal_input(_pad(JOY_BUTTON_A))
	kit.ok(tf.logic.braking, "pad A brakes")
	tf.modal_input(_pad(JOY_BUTTON_A, false))
	tf.modal_input(_pad(JOY_BUTTON_Y))
	kit.eq(tf.logic.vel, 0.0, "pad Y starts over")
	kit.ok(tf.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	# mouse: drag the bridge round the pit, the right button brakes, the wheel nudges, the loupe pulls
	var mf := _tt_instance()
	mf.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(mf, 0.4)
	var p0: Vector2 = TTGame.PIT_C + TTGame._dir(250.0) * 40.0
	var p1: Vector2 = TTGame.PIT_C + TTGame._dir(238.0) * 40.0
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, p0 * mf.S))
	var mm := InputEventMouseMotion.new()
	mm.position = p1 * mf.S
	mf.scene_input(mm)
	kit.ok(mf.logic.vel < -1.0, "dragging the rim clockwise pushes the bridge clockwise (%.1f °/s)" % mf.logic.vel)
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, p1 * mf.S, false))
	mf.scene_input(_mouse(MOUSE_BUTTON_RIGHT, p1 * mf.S))
	kit.ok(mf.logic.braking, "the right button brakes while held")
	mf.scene_input(_mouse(MOUSE_BUTTON_RIGHT, p1 * mf.S, false))
	_steps(mf, 3.0)
	mf.logic.reset()
	mf.scene_input(_mouse(MOUSE_BUTTON_WHEEL_UP, p1 * mf.S))
	kit.ok(absf(mf.logic.vel - TTLogic.NUDGE) < 0.001, "the wheel nudges the bridge")
	mf.logic.reset()
	mf.logic.angle = 120.1
	var mres: Array = []
	mf.finished.connect(func(ok: bool): mres.append(ok))
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, (TTGame.LOUPE.position + TTGame.LOUPE.size * 0.5) * mf.S))
	kit.ok(mf.solved, "a click on the loupe pulls the engine when the rails meet")
	_steps(mf, 3.0)
	kit.eq(mres, [true], "and the find is granted")
	return true


## Drives the bridge by key events alone (what demo_solve does, synchronously): hold the turning key, brake at the
## stopping distance, short holds / taps for the last centimetres, E.
func _tt_full() -> bool:
	var tf := _tt_instance()
	var res: Array = []
	tf.finished.connect(func(ok: bool): res.append(ok))
	tf.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(tf, 0.4)
	var guard := 0
	var dt := 1.0 / 60.0
	while not tf.solved and guard < 200:
		guard += 1
		var e: float = tf.logic.err_to_target()
		var dir := 1 if e > 0.0 else -1
		var key := KEY_LEFT if dir > 0 else KEY_RIGHT
		if not tf.logic.is_still():
			tf.modal_input(_key(KEY_SPACE))
			_settle(tf, dt)
			tf.modal_input(_key(KEY_SPACE, false))
			continue
		if absf(e) <= TTLogic.TOL * 0.6:
			tf.modal_input(_key(KEY_E))
			continue
		var n2 := 0
		if absf(e) > 6.0:
			tf.modal_input(_key(key))
			while not tf._demo_brake_point(dir) and n2 < 3000:
				tf._process(dt)
				n2 += 1
			tf.modal_input(_key(key, false))
			tf._process(dt)
			tf.modal_input(_key(KEY_SPACE))
			_settle(tf, dt)
			tf.modal_input(_key(KEY_SPACE, false))
			continue
		if sqrt(2.0 * TTLogic.FRICTION * absf(e)) <= TTLogic.NUDGE * 1.05:
			tf.modal_input(_key(key))
			tf._process(dt)
			tf.modal_input(_key(key, false))
		else:
			tf.modal_input(_key(key))
			while not tf._demo_fast_enough(dir) and n2 < 600:
				tf._process(dt)
				n2 += 1
			tf.modal_input(_key(key, false))
		_settle(tf, dt)
	kit.ok(tf.solved, "turned, braked and pulled into stall 7 by keys alone")
	kit.eq(tf.fails, 0, "no refusal on the right path")
	kit.ok(str(tf._status.text).contains("Stand 7"), "the engine is in stall 7: „Jetzt sieht der Schwede nur noch die Musterlok.“")
	_steps(tf, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(tf, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(TT_GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_key_event(") and body.contains("_tap(") and not body.contains("logic.set_motor(")
		and not body.contains("logic.set_brake(") and not body.contains("logic.pull(") and not body.contains("logic.push(")
		and not body.contains("logic.step(") and not body.contains("mark_solved(") and not body.contains(" pull()"),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "Turntable extends minigame_base.gd")
	return true


func _settle(tf: Node, dt: float) -> void:
	var n := 0
	while not tf.logic.is_still() and n < 900:
		tf._process(dt)
		n += 1
	for i in 10:
		tf._process(dt)


func _tt_compact(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	var tf := _tt_instance()
	tf.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(tf, 0.4)
	kit.ok(tf.compact and tf.S == 2, "larger text: compact layout, stage x2")
	kit.eq(tf._scene.custom_minimum_size, TTGame.STAGE * 2.0, "the stage shrinks to x2")
	kit.ok(not tf._subtitle.visible and not tf._instr.visible, "the flavour gives way to the text")
	kit.ok(tf._scene.custom_minimum_size.x + 820.0 + 36.0 <= 1800.0, "stage and side panel fit the panel width")
	tf.modal_input(_key(KEY_LEFT))
	tf._scene.queue_redraw()
	kit.eq(tf.logic.motor, 1, "high contrast plays the same")
	tf.modal_input(_key(KEY_LEFT, false))
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	var n := _tt_instance()
	n.open({"explore_id": "karsk.depot.turntable", "auto": false})
	kit.ok(not n.compact and n.S == 3, "default text: stage x3")
	kit.ok(n._scene.custom_minimum_size.x + 500.0 + 36.0 <= 1800.0, "x3 stage and side panel fit the panel width")
	kit.ok(n._scene.custom_minimum_size.y <= 450.0, "x3 stage leaves room for header, status, hint and buttons")
	settings.values["puzzle_hints"] = 0
	var a := _tt_instance()
	a.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(a, 0.4)
	for i in 3:
		a.modal_input(_key(KEY_E))
	kit.ok(a.fails == 3 and not a._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var b := _tt_instance()
	b.open({"explore_id": "karsk.depot.turntable", "auto": false})
	kit.ok(b._hint_box.visible, "puzzle_hints 2: the first hint at once")
	settings.values["puzzle_hints"] = 1
	settings.values["reduced_motion"] = true
	var c := _tt_instance()
	c.open({"explore_id": "karsk.depot.turntable", "auto": false})
	_steps(c, 0.5)
	c._scene.queue_redraw()
	kit.ok(c.is_open, "reduced motion: the stage still plays")
	settings.values["reduced_motion"] = false
	return true


# ================================================================ mini-game: the luggage scale
func _lg_logic() -> bool:
	var lg = LGLogic.new()
	kit.eq(LGLogic.ITEMS.map(func(i): return int(i["hg"])), [236, 198, 38], "suitcase 23.6 kg, repacked 19.8 kg, parcel 3.8 kg")
	kit.eq(int(LGLogic.ITEMS[1]["hg"]) + int(LGLogic.ITEMS[2]["hg"]), int(LGLogic.ITEMS[0]["hg"]), "the same 23.6 kg in two pieces")
	kit.eq(LGLogic.ITEMS.map(func(i): return int(i["hg"]) > int(i["limit_hg"])), [true, false, false], "only the first is over the Corridor's limit")
	kit.eq([LGLogic.target_for(236), LGLogic.target_for(198), LGLogic.target_for(38)],
		[{"coarse": 4, "fine": 36}, {"coarse": 3, "fine": 48}, {"coarse": 0, "fine": 38}], "where the weights belong")
	kit.eq(LGLogic.kg_text(236), "23,6 kg", "German reading")
	kit.eq([lg.tongue(), lg.diff_hg()], [-1.0, -236], "empty beam: the tongue stands up")
	kit.eq(str(lg.move_coarse(-1)["reason"]), "end", "the big weight's end stop refuses")
	kit.eq(lg.moves, 0, "a refusal is no move")
	lg.move_coarse(1)
	lg.move_coarse(1)
	lg.move_coarse(1)
	lg.move_coarse(1)
	lg.move_coarse(1)
	kit.eq([lg.poise_hg(), lg.tongue()], [250, 1.0], "25 kg on the beam: too heavy, the tongue down")
	var r: Dictionary = lg.read()
	kit.eq([r["ok"], r["dir"], r["read_hg"]], [false, "down", 250], "a reading away from the mark is refused")
	lg.move_coarse(-1)
	lg.move_fine(1, 34)
	kit.eq([lg.diff_hg(), lg.tongue()], [-2, -0.4], "200 g short: the tongue a little above the mark")
	lg.move_fine(1, 2)
	kit.ok(lg.balanced() and lg.tongue() == 0.0, "23.6 kg: the tongue plays in")
	var r1: Dictionary = lg.read()
	kit.ok(bool(r1["ok"]) and bool(r1["over"]) and lg.round_i == 1 and lg.coarse == 0 and lg.fine == 0,
		"the first reading: too heavy; the repacked suitcase goes on, both weights back to zero")
	kit.eq(str(lg.move_fine(-1)["reason"]), "end", "the small weight's end stop refuses")
	kit.eq(lg.move_fine(1, 99)["ok"], true, "a long slide stops at the end of the rail")
	kit.eq(lg.fine, LGLogic.FINE_MAX, "at 5 kg")
	# no dead end: from every position of both weights, the next moves reach the reading — for all three items
	var all_ok := true
	var worst := 0
	for rnd in LGLogic.ITEMS.size():
		for c in LGLogic.COARSE_MAX + 1:
			for f in range(0, LGLogic.FINE_MAX + 1, 5):
				var s = LGLogic.new()
				s.round_i = rnd
				s.coarse = c
				s.fine = f
				var n := 0
				while n < 80:
					var nx: Dictionary = s.next_move()
					if str(nx.get("beam", "")) == "read":
						break
					if str(nx["beam"]) == "coarse":
						s.move_coarse(int(nx["dir"]))
					else:
						s.move_fine(int(nx["dir"]), 10 if int(nx["steps"]) >= 10 else 1)
					n += 1
				all_ok = all_ok and s.balanced()
				worst = maxi(worst, n)
	kit.ok(all_ok, "no dead end: every position of the weights reaches the reading")
	kit.ok(worst <= 25, "within 25 moves from the worst position (%d)" % worst)
	var full = LGLogic.new()
	var guard := 0
	while not full.done and guard < 200:
		guard += 1
		var nx: Dictionary = full.next_move()
		match str(nx["beam"]):
			"coarse":
				full.move_coarse(int(nx["dir"]))
			"fine":
				full.move_fine(int(nx["dir"]), 10 if int(nx["steps"]) >= 10 else 1)
			_:
				full.read()
	kit.ok(full.done and full.results.size() == 3, "three readings: done")
	kit.eq(full.results.map(func(x): return bool(x["over"])), [true, false, false], "the slip: too heavy, stamped, stamped")
	kit.eq(str(full.read().get("ok")), "false", "after that nothing more to read")
	return true


func _lg_instance() -> Node:
	return _instance(LG_SCENE)


func _lg_scene() -> bool:
	var mg := _lg_instance()
	kit.ok(mg.is_in_group("minigame"), "LuggageScale joins group minigame")
	var got: Array = []
	mg.finished.connect(func(ok: bool): got.append(ok))
	mg.open({"explore_id": "berlin.ost.luggage_scale", "auto": true})
	mg._process(0.1)
	kit.eq(got, [], "auto: not resolved before ~0.2 s")
	mg._process(0.15)
	kit.eq(got, [true], "auto mode resolves with success")
	var sf := _lg_instance()
	var res: Array = []
	sf.finished.connect(func(ok: bool): res.append(ok))
	sf.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	_steps(sf, 0.4)
	kit.ok(str(sf._status.text).contains("zu wenig") or str(sf._status.text).contains("Koffer"), "the status starts with the suitcase")
	kit.eq(sf._rows.size(), 3, "the slip has three lines")
	sf.modal_input(_key(KEY_RIGHT))
	kit.eq(sf.logic.coarse, 1, "→ moves the big weight a notch")
	sf.modal_input(_key(KEY_UP))
	sf.modal_input(_key(KEY_PAGEUP))
	kit.eq(sf.logic.fine, 11, "↑ a step, Page Up a whole kilo")
	sf.modal_input(_key(KEY_E))
	kit.eq(sf.fails, 1, "reading away from the mark is refused")
	kit.ok(str(sf._status.text).contains("oben") and str(sf._status.text).contains("6,1 kg"), "the refusal: the reading and where the tongue stands")
	sf.modal_input(_key(KEY_ENTER))
	kit.ok(sf.fails == 2 and sf._hint_box.visible, "a hint after two refusals")
	kit.ok(str(sf._hint_label.text).contains("Kerbe"), "the first hint: the big weight first")
	sf.show_hint(2)
	kit.ok(str(sf._hint_label.text).contains("20 kg") and str(sf._hint_label.text).contains("3,6"), "the second hint names both weights")
	sf.modal_input(_key(KEY_R))
	kit.eq([sf.logic.coarse, sf.logic.fine, sf.logic.round_i], [0, 0, 0], "R: both weights back to zero")
	# the pad: d-pad by action, RB a kilo, A reads, Y starts over
	sf.modal_input(_pad(JOY_BUTTON_RIGHT_SHOULDER))
	kit.eq(sf.logic.fine, 10, "pad RB slides the small weight a kilo")
	sf.modal_input(_pad(JOY_BUTTON_Y))
	kit.eq(sf.logic.fine, 0, "pad Y starts over")
	# set the first item by keys and read it
	for i in 4:
		sf.modal_input(_key(KEY_RIGHT))
	for i in 3:
		sf.modal_input(_key(KEY_PAGEUP))
	for i in 6:
		sf.modal_input(_key(KEY_UP))
	_steps(sf, 0.2)
	kit.ok(sf.logic.balanced(), "20 kg + 3,6 kg: the tongue plays in")
	sf.modal_input(_key(KEY_SPACE))
	kit.eq(sf.logic.round_i, 1, "read: the repacked suitcase goes on")
	kit.ok(str(sf._status.text).contains("23,6 kg") and str(sf._status.text).contains("packt"), "the first reading: too heavy, she repacks")
	kit.ok(str(sf._rows[0].text).contains("zu schwer"), "the slip notes the first reading")
	kit.ok(sf.handle_cancel(), "Esc handled")
	kit.eq(res, [false], "Esc gives up without a find")
	# mouse: click a notch, drag the small weight, the wheel over a rail
	var mf := _lg_instance()
	mf.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	_steps(mf, 0.4)
	var cy: float = LGGame.COARSE_Y + mf._tilt_y(LGGame.coarse_x(4))
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, Vector2(LGGame.coarse_x(4), cy) * mf.S))
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, Vector2(LGGame.coarse_x(4), cy) * mf.S, false))
	kit.eq(mf.logic.coarse, 4, "a click on the upper rail puts the big weight in that notch")
	var fy: float = LGGame.FINE_Y + mf._tilt_y(LGGame.fine_x(10))
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, Vector2(LGGame.fine_x(10), fy) * mf.S))
	var mm := InputEventMouseMotion.new()
	mm.position = Vector2(LGGame.fine_x(36), fy) * mf.S
	mf.scene_input(mm)
	mf.scene_input(_mouse(MOUSE_BUTTON_LEFT, mm.position, false))
	kit.eq(mf.logic.fine, 36, "dragging the small weight along the lower rail")
	var fy2: float = LGGame.FINE_Y + mf._tilt_y(LGGame.fine_x(36))
	mf.scene_input(_mouse(MOUSE_BUTTON_WHEEL_UP, Vector2(LGGame.fine_x(36), fy2) * mf.S))
	kit.eq(mf.logic.fine, 37, "the wheel over the lower rail moves it a step")
	return true


func _lg_full() -> bool:
	var sf := _lg_instance()
	var res: Array = []
	sf.finished.connect(func(ok: bool): res.append(ok))
	sf.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	_steps(sf, 0.4)
	var guard := 0
	while not sf.solved and guard < 300:
		guard += 1
		var nx: Dictionary = sf.logic.next_move()
		if nx.is_empty():
			break
		match str(nx["beam"]):
			"coarse":
				sf.modal_input(_key(KEY_RIGHT if int(nx["dir"]) > 0 else KEY_LEFT))
			"fine":
				if int(nx["steps"]) >= 10:
					sf.modal_input(_key(KEY_PAGEUP if int(nx["dir"]) > 0 else KEY_PAGEDOWN))
				else:
					sf.modal_input(_key(KEY_UP if int(nx["dir"]) > 0 else KEY_DOWN))
			_:
				sf.modal_input(_key(KEY_E))
		_steps(sf, 0.05)
	kit.ok(sf.solved, "all three items weighed by keys alone")
	kit.eq(sf.fails, 0, "no refusal on the right path")
	kit.ok(str(sf._status.text).contains("zwei Stücken"), "„Alles darf mit, nur in zwei Stücken.“")
	kit.ok(str(sf._rows[2].text).contains("3,8 kg") and str(sf._rows[1].text).contains("gestempelt"), "the slip is complete")
	_steps(sf, 3.0)
	kit.eq(res, [true], "finished(true) exactly once after the solved hold")
	_steps(sf, 1.0)
	kit.eq(res, [true], "never a second finished")
	var src := FileAccess.get_file_as_string(LG_GAME)
	var body := src.substr(src.find("func demo_solve"))
	kit.ok(body.contains("_tap(") and not body.contains("logic.move_") and not body.contains("logic.read(")
		and not body.contains("logic.set_") and not body.contains("mark_solved(") and not body.contains("read_scale()"),
		"demo_solve drives the game through synthetic key events only")
	kit.ok(src.begins_with("extends \"res://scripts/ui/minigames/minigame_base.gd\""), "LuggageScale extends minigame_base.gd")
	return true


func _lg_compact(settings: Node) -> bool:
	settings.values["text_scale"] = 1.5
	settings.values["high_contrast"] = true
	var sf := _lg_instance()
	sf.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	_steps(sf, 0.4)
	kit.ok(sf.compact and sf.S == 2, "larger text: compact layout, stage x2")
	kit.eq(sf._scene.custom_minimum_size, LGGame.STAGE * 2.0, "the stage shrinks to x2")
	kit.ok(sf._scene.custom_minimum_size.x + 820.0 + 36.0 <= 1800.0, "stage and side panel fit the panel width")
	sf.modal_input(_key(KEY_RIGHT))
	sf._scene.queue_redraw()
	kit.eq(sf.logic.coarse, 1, "high contrast plays the same")
	settings.values["text_scale"] = 1.0
	settings.values["high_contrast"] = false
	var n := _lg_instance()
	n.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	kit.ok(not n.compact and n.S == 3, "default text: stage x3")
	kit.ok(n._scene.custom_minimum_size.x + 500.0 + 36.0 <= 1800.0, "x3 stage and side panel fit the panel width")
	kit.ok(n._scene.custom_minimum_size.y <= 450.0, "x3 stage leaves room for header, status, hint and buttons")
	settings.values["puzzle_hints"] = 0
	var a := _lg_instance()
	a.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	_steps(a, 0.4)
	for i in 3:
		a.modal_input(_key(KEY_E))
	kit.ok(a.fails == 3 and not a._hint_box.visible, "puzzle_hints 0: no hint even after three refusals")
	settings.values["puzzle_hints"] = 2
	var b := _lg_instance()
	b.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	kit.ok(b._hint_box.visible, "puzzle_hints 2: the first hint at once")
	settings.values["puzzle_hints"] = 1
	settings.values["reduced_motion"] = true
	var c := _lg_instance()
	c.open({"explore_id": "berlin.ost.luggage_scale", "auto": false})
	c.modal_input(_key(KEY_RIGHT))
	_steps(c, 0.1)
	kit.eq(c._tip, c.logic.tongue(), "reduced motion: the tongue does not swing")
	settings.values["reduced_motion"] = false
	return true


# ================================================================ sounds, texts, placement of the two mini-games
func _mg_assets() -> bool:
	var tsrc := FileAccess.get_file_as_string(TT_GAME)
	var lsrc := FileAccess.get_file_as_string(LG_GAME)
	for s in TT_SFX + LG_SFX:
		kit.ok(ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % s), "sound %s imported" % s)
	for s in TT_SFX:
		kit.ok(tsrc.contains("%s\"" % s) or tsrc.contains("%s.wav\"" % s), "the turntable plays %s" % s)
	for s in LG_SFX:
		kit.ok(lsrc.contains("\"%s\"" % s), "the scale plays %s" % s)
	var gen := FileAccess.get_file_as_string("res://tools/audiogen/mg_audio_c4p2.py")
	for s in TT_SFX + LG_SFX:
		kit.ok(gen.contains("'%s'" % s), "%s comes from tools/audiogen/mg_audio_c4p2.py" % s)
	var roll = load("res://assets/audio/sfx/mg_c4p2_tt_roll.wav") if ResourceLoader.exists("res://assets/audio/sfx/mg_c4p2_tt_roll.wav") else null
	if roll is AudioStreamWAV:
		kit.ok(absf((roll as AudioStreamWAV).get_length() - 2.0) < 0.01, "the rolling loop lasts two seconds")
	for k in ["mg.turntable.kicker", "mg.turntable.title", "mg.turntable.solved", "mg.turntable.hint.1", "mg.turntable.hint.next",
			"mg.turntable.btn.pull", "mg.turntable.btn.brake"]:
		kit.ok(tsrc.contains("\"%s\"" % k), "the turntable uses %s" % k)
		kit.ok(loc.has(k) and loc.source_of(k).ends_with("de_explore_c4p2.json"), "%s has German text" % k)
	for k in ["mg.luggage.kicker", "mg.luggage.title", "mg.luggage.solved", "mg.luggage.hint.1", "mg.luggage.hint.next",
			"mg.luggage.btn.read", "mg.luggage.result.1", "mg.luggage.result.2", "mg.luggage.result.3"]:
		kit.ok(lsrc.contains("\"%s\"" % k) or FileAccess.get_file_as_string("res://scripts/ui/minigames/luggage_logic.gd").contains("\"%s\"" % k),
			"the scale uses %s" % k)
		kit.ok(loc.has(k) and loc.source_of(k).ends_with("de_explore_c4p2.json"), "%s has German text" % k)
	kit.ok(loc.t("mg.turntable.solved").contains("Stand 7"), "the turntable's ending names stall 7")
	_load_levels()
	var where := {"karsk.depot.turntable": ["L_C4P2_KarskA", "exp_turntable", "L_C4P2_KarskB"],
		"berlin.ost.luggage_scale": ["L_C4P2_BerlinA", "exp_luggage_scale", "L_C4P2_BerlinA"]}
	for id in where:
		var w: Array = where[id]
		kit.eq(str(entries.get(id, {}).get("minigame", "")), str(MINIGAMES[id]), "%s runs its mini-game" % id)
		kit.eq(_scene_of(id), str(w[2]), "%s plays in %s" % [id, w[2]])
		var hit: Array = (nodes.get(str(w[0]), []) as Array).filter(func(n): return str(n["props"].get("explore_id", "")) == id)
		if kit.ok(hit.size() == 1, "one node for %s" % id):
			kit.eq(str(hit[0]["props"].get("hotspot_id", "")), str(w[1]), "%s at %s" % [id, w[1]])
	# the scenes load and their roots run the mini-game scripts
	for p in [TT_SCENE, LG_SCENE]:
		var ps = load(p)
		kit.ok(ps is PackedScene, "%s loads" % p)
	return true
