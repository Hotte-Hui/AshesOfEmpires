extends RefCounted
## The Karsk depot art of Chapter 4 part 2 (L_C4P2_Karsk, assets/environments/karsk_c4p2,
## tools/pixelgen/env_c4p2_karsk*.py, scenes/levels/c4p2 + scripts/levels/c4p2 actors,
## assets/ui/documents/karsk_c4p2_*):
##  * the art contract of C4P2_DESIGN §4.1: world, walk band, every story hotspot / spawn / NPC anchor (with their
##    gates), the one blocker `tarpaulin`, the camera zones, the zones, one look + grade per scene
##  * every referenced file exists; strips are whole numbers of frames; maps match; fps sane; every entry names the
##    one Story scene it belongs to and stays inside that scene's painted place (A 0-904, B 856-1920)
##  * the insignia sites keep their neutral + _hist pair (§12.4); the two bakes are palette-pure ('depot')
##  * people: Kolonne 4 (>= 6 readable life strips in A), the band in time, the platform; every figure stands behind
##    the walk band and under the player
##  * story patches follow the objectives (order taken, book taken, the halves on the bench, the card joined)
##  * every story hotspot stands at its painted object; the explore suggestions keep 24 px from them
##  * the level: the shell keeps annex_level.gd, each scene builds only its own art and actors, has its own camera
##    window and look; the passing train (-8 dB, every 30-50 s, waits while a film runs), the dog, the sparrows
##  * the inspect documents: one image per Karsk item of part 2, German alt texts, InspectView finds them

const Kit := preload("res://tests/support/test_kit.gd")
const UiKit := preload("res://scripts/ui/ui_kit.gd")
const RegistryLevel := preload("res://scripts/levels/c3p2_archive/registry_level.gd")
const ENV := "res://assets/environments/karsk_c4p2/"
const LEVEL := "res://scenes/levels/L_C4P2_Karsk.tscn"
const SCRIPT := "res://scripts/levels/c4/annex_level.gd"
const SA := "L_C4P2_KarskA"
const SB := "L_C4P2_KarskB"
const HOTSPOTS := {"dispatch_window": 132, "irina_window": 196, "coal_list": 400, "maria_coal": 560, "guard_coal": 690,
	"press_notice": 780, "signal_post": 980, "minder_canteen": 1110, "canteen_table": 1170, "lev_sandhouse": 1350,
	"sand_table": 1460, "sand_lamp": 1520, "express_door": 1780}
const NPC_FEET := {"irina_window": 214, "maria_coal": 578, "guard_coal": 690, "signal_post": 998, "minder_canteen": 1110,
	"lev_sandhouse": 1368, "express_door": 1798}
const SPAN := {SA: [0, 904], SB: [856, 1920]}
const AREA := {SA: [18, 858], SB: [898, 1902]}
const PATCHES := {"order_taken": [SA, ["c4e_inspect_order"], [], "dispatch_window"],
	"book_taken": [SB, ["c4g_inspect_book"], [], "canteen_table"],
	"halves_on_bench": [SB, ["c4g_talk_lev"], ["c4g_solve_halves"], "sand_table"],
	"card_joined": [SB, ["c4g_solve_halves"], [], "sand_table"]}
const DOC_ITEMS := {"ev_c4_special_order": "karsk_c4p2_order", "ev_c4_work_list": "karsk_c4p2_work_list",
	"ev_c4_press_notice": "karsk_c4p2_press_notice", "ev_c4_guidebook": "karsk_c4p2_guidebook",
	"ev_c4_card_ru_original": "karsk_c4p2_card_ru", "ev_c4_card_whole": "karsk_c4p2_card_whole"}

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "karsk_c4p2/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("design_contract", _contract)
	kit.run_case("files_maps_and_strips", _files)
	kit.run_case("each_entry_in_its_own_place", _places)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("bakes_palette_pure", _palette)
	kit.run_case("people_of_both_places", _people)
	kit.run_case("story_patches", _patches)
	kit.run_case("hotspots_at_their_objects", _objects)
	kit.run_case("level_scene_filter_and_actors", _level)
	kit.run_case("passing_train_contract", _train)
	kit.run_case("inspect_documents", _documents)
	kit.run_case("story_text_stays_readable", _readable)
	kit.run_case("cook_inside_the_hatch", _cook)
	kit.run_case("evening_sky_not_black", _sky_b)
	kit.run_case("no_twins_in_the_crowd", _twins)
	kit.run_case("showcase_middle_populated", _middle)
	kit.run_case("barrel_emblem_train_read", _yard_reads)
	kit.cleanup()
	return kit.failures


func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	return Image.load_from_file(ProjectSettings.globalize_path(path))


static func _ints(v):
	if v is Array:
		var out: Array = []
		for x in v:
			out.append(_ints(x))
		return out
	if v is float and is_equal_approx(v, round(v)):
		return int(v)
	return v


func _entries() -> Array:
	var out: Array = []
	for section in ["layers", "props", "decals", "fx"]:
		for e in m.get(section, []):
			if e is Dictionary:
				out.append([section, e])
	return out


# ------------------------------------------------------------------ contract
func _contract() -> bool:
	kit.eq(m.get("id"), "karsk_c4p2", "env id")
	kit.ok(not m.get("placeholder", false), "the placeholder is replaced")
	kit.eq(m.get("palette"), "depot", "palette depot")
	kit.eq(_ints(m.get("world_size")), [1920, 360], "world 1920 x 360")
	kit.eq(_ints(m.get("walkable")), [[18, 296], [1902, 296], [1902, 306], [18, 306]], "walk band y 296-306, x 18-1902")
	var hs: Dictionary = m.get("hotspots", {})
	for k in HOTSPOTS:
		kit.eq(_ints(hs.get(k)), [HOTSPOTS[k], 300], "story hotspot %s at (%d, 300)" % [k, HOTSPOTS[k]])
	var sp: Dictionary = m.get("spawns", {})
	kit.eq(_ints(sp.get("SP_C4P2_Yard")), [48, 300], "spawn SP_C4P2_Yard")
	kit.eq(_ints(sp.get("SP_C4P2_Signal")), [930, 300], "spawn SP_C4P2_Signal")
	var bl: Array = m.get("blockers", [])
	if kit.eq(bl.size(), 1, "one permanent blocker"):
		kit.eq(str(bl[0].get("name")), "tarpaulin", "blocker tarpaulin")
		kit.eq(_ints(bl[0].get("rect")), [858, 270, 40, 60], "the tarpaulin 858-898")
		kit.ok(not RegistryLevel.is_gated(bl[0]), "the tarpaulin is never opened by a gate")
	var npcs: Dictionary = m.get("npcs", {})
	for k in NPC_FEET:
		kit.eq(_ints(npcs.get(k, {}).get("feet")), [NPC_FEET[k], 300], "NPC anchor %s at (%d, 300)" % [k, NPC_FEET[k]])
	kit.eq(npcs.get("signal_post", {}).get("hide_after"), "c4g_inspect_card", "Ekdahl at the signal until the card is whole")
	kit.eq(npcs.get("express_door", {}).get("show_after"), "c4g_inspect_card", "then at the express door")
	kit.eq(npcs.get("lev_sandhouse", {}).get("show_after"), "c4g_inspect_book", "Lev after the book")
	var z: Dictionary = m.get("camera_zones", {})
	kit.eq(_ints(z.get(SA)), [0, 0, 878, 360], "camera zone A")
	kit.eq(_ints(z.get(SB)), [878, 0, 1042, 360], "camera zone B")
	for zn in ["yard", "tarpaulin", "showcase", "platform_1"]:
		kit.ok((m.get("zones", {}) as Dictionary).has(zn), "zone %s kept" % zn)
	var looks := {}
	for lk in m.get("looks", []):
		looks[str(lk.get("scene"))] = lk
	kit.eq([str(looks.get(SA, {}).get("name")), str(looks.get(SA, {}).get("grade"))], ["dawn", "depot_dawn"], "look of A")
	kit.eq([str(looks.get(SB, {}).get("name")), str(looks.get(SB, {}).get("grade"))], ["evening", "depot_evening"], "look of B")
	return true


func _files() -> bool:
	var names := {}
	for se in _entries():
		var section: String = se[0]
		var e: Dictionary = se[1]
		var nm := str(e.get("name", e.get("file", "")))
		kit.ok(not names.has(section + nm), "%s: unique name %s" % [section, nm])
		names[section + nm] = true
		var path := ENV + str(e.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s %s: file %s exists" % [section, nm, path]):
			continue
		var frames := int(e.get("frames", 1))
		kit.ok(frames >= 1 and img.get_width() % frames == 0, "%s: width %d is a whole number of %d frames" % [nm, img.get_width(), frames])
		kit.ok(img.get_height() <= 360, "%s: height within the world" % nm)
		if frames > 1:
			kit.ok(float(e.get("fps", 0)) > 0.0 and float(e.get("fps", 0)) <= 12.0, "%s: fps in (0, 12]" % nm)
		for flag in [["normal", "_n"], ["emission", "_e"]]:
			if bool(e.get(flag[0], false)) and not (section == "layers" and flag[0] == "normal" and not bool(e.get("lit", true))):
				var mi := _img(path.get_basename() + flag[1] + ".png")
				if kit.ok(mi != null, "%s: map %s exists" % [nm, flag[1]]):
					kit.eq(mi.get_size(), img.get_size(), "%s: %s map matches the image" % [nm, flag[1]])
	for li in m.get("lights", []):
		kit.ok(str(li.get("name", "")) != "" and li.has("after"), "light %s named and gated (registry flicker)" % li.get("name", "?"))
		kit.ok(float(li.get("flicker_hz", 0.0)) <= 3.0, "light %s: slower than 3 Hz" % li.get("name", "?"))
	return true


func _places() -> bool:
	for se in _entries():
		var e: Dictionary = se[1]
		var nm := str(e.get("name", e.get("file", "")))
		var sc: Array = RegistryLevel._list(e.get("scene"))
		if not kit.ok(sc.size() == 1 and str(sc[0]) in [SA, SB], "%s: names exactly one Story scene" % nm):
			continue
		var par = e.get("parallax", [1, 1])
		var p := float(par[0]) if par is Array else float(par)
		if not is_equal_approx(p, 1.0):
			continue
		var img := _img(ENV + str(e.get("file", "")))
		if img == null:
			continue
		var x0 := float(e["pos"][0])
		var x1 := x0 + img.get_width() / maxi(1, int(e.get("frames", 1)))
		var span: Array = SPAN[str(sc[0])]
		kit.ok(x0 >= float(span[0]) - 1.0 and x1 <= float(span[1]) + 1.0, "%s: inside the painted place of %s (%d-%d)" % [nm, sc[0], int(x0), int(x1)])
	for a in m.get("actors", []):
		kit.ok(str(a.get("scene_id", "")) in [SA, SB], "actor %s names its Story scene" % str(a.get("scene", "")).get_file())
		kit.ok(ResourceLoader.exists(str(a.get("scene", ""))), "actor scene %s exists" % a.get("scene", ""))
		var pr: Dictionary = a.get("props", {})
		for k in ["sprite", "loco", "puff", "flames", "breath"]:
			if pr.has(k):
				kit.ok(FileAccess.file_exists(str(pr[k])), "actor sprite %s exists" % pr[k])
	for li in m.get("lights", []):
		var sc2: Array = RegistryLevel._list(li.get("scene"))
		if kit.ok(sc2.size() == 1, "light %s names its Story scene" % li.get("name", "?")):
			var span2: Array = SPAN[str(sc2[0])]
			kit.ok(float(li["pos"][0]) >= float(span2[0]) and float(li["pos"][0]) <= float(span2[1]), "light %s inside its place" % li.get("name", "?"))
	# the foreground keeps the walk band and the hotspots clear: nothing opaque above y 318
	for e in m.get("layers", []):
		if str(e.get("name", "")).begins_with("fg_"):
			var img2 := _img(ENV + str(e["file"]))
			var clear := true
			for y in range(0, 318, 2):
				for x in range(0, img2.get_width(), 3):
					if img2.get_pixel(x, y).a > 0.0:
						clear = false
						break
				if not clear:
					break
			kit.ok(clear, "%s: nothing above y 318" % e["name"])
	return true


func _insignia() -> bool:
	var sites := 0
	for e in m.get("decals", []):
		if str(e.get("name", "")).begins_with("insignia_"):
			sites += 1
			var a := _img(ENV + str(e["file"]))
			var h := _img(ENV + str(e["file"]).get_basename() + "_hist.png")
			if kit.ok(a != null and h != null, "%s: neutral + _hist pair" % e["name"]):
				kit.eq(a.get_size(), h.get_size(), "%s: the pair has one size" % e["name"])
				kit.ok(a.get_data() != h.get_data(), "%s: the _hist variant differs" % e["name"])
				kit.ok(FileAccess.file_exists(ENV + str(e["file"]).get_basename() + "_hist_n.png"), "%s: _hist normal map" % e["name"])
	kit.eq(sites, 3, "three insignia sites (roundhouse back, roundhouse front, the engine)")
	return true


func _palette() -> bool:
	var allowed := {}
	var ramps: Dictionary = m.get("meta", {}).get("palette_ramps", {})
	for r in ramps:
		for hx in ramps[r]:
			allowed[str(hx).to_upper().substr(1)] = true
	kit.ok(allowed.size() >= 60, "palette_ramps listed in meta (%d colours)" % allowed.size())
	for nm in ["depot_a.png", "depot_b.png", "life/k4_shovel_a.png", "life/band_tuba.png"]:
		var img := _img(ENV + nm)
		if not kit.ok(img != null, "%s exists" % nm):
			continue
		var bad := {}
		for y in range(0, img.get_height(), 2):
			for x in range(0, img.get_width(), 2):
				var c := img.get_pixel(x, y)
				if c.a > 0.0:
					var hx := c.to_html(false).to_upper()
					if not allowed.has(hx):
						bad[hx] = true
		kit.ok(bad.is_empty(), "%s: palette-pure (%s)" % [nm, str(bad.keys().slice(0, 4))])
	return true


func _people() -> bool:
	var k4 := 0
	var a_life := 0
	var b_life := 0
	var band: Array = []
	for e in m.get("decals", []):
		var f := str(e.get("file", ""))
		if not f.begins_with("life/"):
			continue
		var sc := str(RegistryLevel._list(e.get("scene"))[0])
		var img := _img(ENV + f)
		if img == null:
			continue
		var frames := int(e.get("frames", 1))
		kit.ok(frames >= 6, "%s: a living loop (>= 6 frames)" % e["name"])
		kit.ok(int(e.get("z", 0)) < 0, "%s: drawn under the player and the NPCs" % e["name"])
		kit.ok(float(e["pos"][1]) + img.get_height() <= 296.0 + 0.5, "%s: stands behind the walk band" % e["name"])
		kit.ok(bool(e.get("lit", false)) and bool(e.get("normal", false)), "%s: lit with its normal map" % e["name"])
		if sc == SA:
			a_life += 1
			if str(e["name"]).begins_with("k4_"):
				k4 += 1
				kit.ok(img.get_height() >= 50, "%s: a readable adult figure (frame %d px)" % [e["name"], img.get_height()])
		else:
			b_life += 1
			if str(e["name"]).begins_with("band_"):
				band.append(e)
	kit.ok(k4 >= 6, "Kolonne 4: at least six readable life strips (%d)" % k4)
	kit.ok(a_life >= 10 and b_life >= 14, "both places populated (A %d, B %d)" % [a_life, b_life])
	kit.eq(band.size(), 5, "the band: five players")
	for e in band:
		kit.eq(float(e.get("t0", -1.0)), 0.0, "%s plays in time (t0 0)" % e["name"])
	kit.ok(m.get("npcs", {}).get("maria_coal", {}).get("char") == "maria", "Maria is the eleventh of Kolonne 4 (speaking NPC)")
	return true


func _patches() -> bool:
	var found := {}
	for e in m.get("decals", []):
		var nm := str(e.get("name", ""))
		if not PATCHES.has(nm):
			continue
		found[nm] = true
		var want: Array = PATCHES[nm]
		kit.eq(RegistryLevel._list(e.get("scene")), [want[0]], "%s: scene" % nm)
		kit.eq(RegistryLevel._list(e.get("after")), want[1], "%s: after" % nm)
		kit.eq(RegistryLevel._list(e.get("until")), want[2], "%s: until" % nm)
		var img := _img(ENV + str(e["file"]))
		if img != null:
			var x0 := float(e["pos"][0])
			var hx := float(HOTSPOTS[want[3]])
			kit.ok(x0 - 30.0 <= hx and hx <= x0 + img.get_width() + 70.0, "%s: painted at %s" % [nm, want[3]])
	for nm in PATCHES:
		kit.ok(found.has(nm), "story patch %s present" % nm)
	return true


func _objects() -> bool:
	var info: Dictionary = m.get("hotspot_info", {})
	for k in HOTSPOTS:
		if kit.ok(info.has(k), "hotspot_info %s" % k):
			var span: Array = info[k].get("span", [0, 0])
			var x := float(HOTSPOTS[k])
			kit.ok(x >= float(span[0]) - 24.0 and x <= float(span[1]) + 24.0, "%s stands at its painted object %s" % [k, str(span)])
	# the explore stream's art contract (explore_hotspots.json `info`): every painted find lies in its place
	var xh = JSON.parse_string(FileAccess.get_file_as_string(ENV + "explore_hotspots.json")) if FileAccess.file_exists(ENV + "explore_hotspots.json") else null
	if xh is Dictionary:
		for k in (xh as Dictionary).get("info", {}):
			var fx := float(xh["info"][k].get("focus", [0, 0])[0])
			kit.ok((fx >= SPAN[SA][0] and fx <= AREA[SA][1] + 12) or (fx >= AREA[SB][0] - 12 and fx <= SPAN[SB][1]), "explore find %s painted inside a place (x %d)" % [k, int(fx)])
	return true


# ------------------------------------------------------------------ the level
func _mount(scene_id: String) -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("level_id", scene_id)
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	return lvl


func _built(lvl: Node, entry_name: String) -> bool:
	for g in lvl.get("groups"):
		if entry_name in g["names"]:
			return true
	var bd: Node = lvl.get_node_or_null("Backdrop")
	if bd != null and ((bd.get("decals_by_name") as Dictionary).has(entry_name) or (bd.get("layers_by_name") as Dictionary).has(entry_name)):
		return true
	return false


func _actor_scripts(lvl: Node) -> Array:
	var out: Array = []
	for n in lvl.get("playfield").get_children():
		if n.get_script() != null:
			out.append(str((n.get_script() as Script).resource_path).get_file())
	return out


func _level() -> bool:
	var a := _mount(SA)
	kit.eq((a.get_script() as Script).resource_path, SCRIPT, "the shell keeps annex_level.gd (scene filter, camera zones)")
	kit.eq(a.call("get_camera_bounds"), Rect2(0, 0, 878, 360), "scene A: the camera stays in the back yard")
	kit.eq(a.call("look"), "dawn", "scene A looks like dawn")
	kit.eq(str(a.get("grade_preset")), "depot_dawn", "scene A: grade depot_dawn")
	kit.ok(_built(a, "depot_a") and not _built(a, "depot_b"), "scene A builds only the back yard")
	kit.ok(_built(a, "k4_shovel_a") and not _built(a, "band_tuba"), "scene A: Kolonne 4, not the band")
	var sa := _actor_scripts(a)
	for s in ["karsk_depot_train.gd", "karsk_depot_dog.gd", "karsk_depot_sparrows.gd", "karsk_barrel.gd"]:
		kit.ok(s in sa, "scene A actor %s" % s)
	var b := _mount(SB)
	kit.eq(b.call("get_camera_bounds"), Rect2(878, 0, 1042, 360), "scene B: the camera stays right of the tarpaulin")
	kit.eq(b.call("look"), "evening", "scene B looks like the evening")
	kit.eq(str(b.get("grade_preset")), "depot_evening", "scene B: grade depot_evening")
	kit.ok(_built(b, "depot_b") and not _built(b, "depot_a"), "scene B builds only the showcase and the platform")
	var sb := _actor_scripts(b)
	kit.ok(not ("karsk_depot_train.gd" in sb) and not ("karsk_depot_dog.gd" in sb), "scene B: no train behind, no dog")
	kit.ok(b.call("blocker_on", "tarpaulin"), "the tarpaulin blocks walking")
	# story patches follow the objectives
	b.set("done_override", {"c4g_talk_ekdahl": true, "c4g_inspect_book": true, "c4g_talk_lev": true})
	b.set("choice_override", {})
	b.set("memory_override", false)
	b.set("hidden_override", false)
	b.call("refresh", true)
	kit.ok(b.call("is_shown", "book_taken") and b.call("is_shown", "halves_on_bench") and not b.call("is_shown", "card_joined"), "B: the book taken, the halves on the bench")
	b.set("done_override", {"c4g_talk_ekdahl": true, "c4g_inspect_book": true, "c4g_talk_lev": true, "c4g_solve_halves": true})
	b.call("refresh", true)
	kit.ok(b.call("is_shown", "card_joined") and not b.call("is_shown", "halves_on_bench"), "B: the card joined")
	kit.ok(a.call("is_shown", "order_taken") == false, "A at its start: the order still on the sill")
	return true


func _train() -> bool:
	var tr: Dictionary = {}
	for a in m.get("actors", []):
		if str(a.get("scene", "")).ends_with("KarskDepotTrain.tscn"):
			tr = a
	if not kit.ok(not tr.is_empty(), "the passing train is placed"):
		return true
	kit.eq(tr.get("scene_id"), SA, "the train passes in scene A only")
	var pr: Dictionary = tr.get("props", {})
	kit.eq(float(pr.get("train_db", 0.0)), -8.0, "the train sounds at -8 dB")
	kit.eq(_ints(pr.get("interval")), [30, 50], "every 30-50 s")
	for w in pr.get("wagons", []):
		kit.ok(FileAccess.file_exists(str(w)), "wagon sprite %s" % w)
	kit.eq(_ints(pr.get("amb_trains", {}).get("amb_karsk_depot")), [0], "the ambience's own train (0-18 s of its loop) is known")
	var node: Node = (load(str(tr["scene"])) as PackedScene).instantiate()
	kit.ok(node.has_method("film_running") and node.get("train_db") != null, "the train script waits while a film runs")
	node.set("amb_trains", pr.get("amb_trains", {}))
	node.set("amb_train_len", float(pr.get("amb_train_len", 18.0)))
	node.set("amb_override", ["amb_karsk_depot", 4.0, 60.0])
	kit.ok(absf(float(node.call("amb_train_time")) - 4.0) < 0.01, "the picture follows the ambience's train (4 s in)")
	node.set("amb_override", ["amb_karsk_depot", 30.0, 60.0])
	kit.ok(float(node.call("amb_train_time")) < 0.0 and not node.call("amb_train_near", 13.0), "mid-loop: free for the level's own train")
	node.set("amb_override", ["amb_karsk_depot", 50.0, 60.0])
	kit.ok(node.call("amb_train_near", 13.0), "the ambience's train is due in 10 s: the own train waits")
	node.free()
	return true


func _documents() -> bool:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/documents/karsk_c4p2_documents.json"))
	if not kit.ok(parsed is Dictionary, "karsk_c4p2_documents.json parses"):
		return true
	var loc = JSON.parse_string(FileAccess.get_file_as_string("res://data/locale/de_env_karsk_c4p2.json"))
	var strings: Dictionary = loc.get("strings", {}) if loc is Dictionary else {}
	var by_item := {}
	for d in parsed.get("documents", []):
		by_item[str(d.get("item_id"))] = d
	for item in DOC_ITEMS:
		if not kit.ok(by_item.has(item), "document for %s" % item):
			continue
		var d: Dictionary = by_item[item]
		kit.eq(str(d.get("id")), DOC_ITEMS[item], "%s: document id" % item)
		var img := _img(str(d.get("file")))
		if kit.ok(img != null, "%s: image exists" % item):
			kit.ok(img.get_width() <= 320 and img.get_height() <= 220, "%s: fits the inspect stage at x3" % item)
		var alt := str(strings.get(str(d.get("alt_key")), ""))
		kit.ok(alt.length() > 40 and (alt.contains("„") or alt.contains("ä") or alt.contains("ü")), "%s: German alt text" % item)
		kit.eq(UiKit.doc_for_item(item), DOC_ITEMS[item], "%s: InspectView finds it" % item)
		kit.ok((d.get("marks", {}) as Dictionary).size() >= 3, "%s: marks for the story lines" % item)
	return true


# ------------------------------------------------------------------ round-10 art review
static func _hit(r: Array, x0: float, y0: float, x1: float, y1: float) -> bool:
	return x0 < float(r[0]) + float(r[2]) and x1 > float(r[0]) and y0 < float(r[1]) + float(r[3]) and y1 > float(r[1])


## Opaque pixels of every frame of a life strip that fall inside the world rect r.
func _strip_pixels_in(e: Dictionary, img: Image, r: Array) -> int:
	var frames := int(e.get("frames", 1))
	var fw := img.get_width() / maxi(1, frames)
	var px := float(e["pos"][0])
	var py := float(e["pos"][1])
	var n := 0
	var x0 := maxi(0, int(float(r[0]) - px))
	var x1 := mini(fw, int(float(r[0]) + float(r[2]) - px))
	var y0 := maxi(0, int(float(r[1]) - py))
	var y1 := mini(img.get_height(), int(float(r[1]) + float(r[3]) - py))
	for f in frames:
		for y in range(y0, y1):
			for x in range(x0, x1):
				if img.get_pixel(f * fw + x, y).a > 0.0:
					n += 1
	return n


func _readable() -> bool:
	var rd: Dictionary = m.get("readable", {})
	for k in ["hatch_sign", "roundhouse_banner", "press_notice", "duty_board", "tarpaulin_panel", "gate_clocks",
			"gate_sign", "express_route_board", "express_sleeping_car", "express_dining_car", "engine_plate_1939"]:
		kit.ok(rd.has(k), "readable story text listed: %s" % k)
	for k in rd:
		var r: Array = rd[k].get("rect", [0, 0, 0, 0])
		var sc := str(rd[k].get("scene", ""))
		# no people in front of it
		for e in m.get("decals", []):
			if not str(e.get("file", "")).begins_with("life/") or str(RegistryLevel._list(e.get("scene"))[0]) != sc:
				continue
			var img := _img(ENV + str(e["file"]))
			if img != null:
				var n := _strip_pixels_in(e, img, r)
				kit.ok(n == 0, "%s stays readable: %s covers %d px of it" % [k, e["name"], n])
		# no sparrow perched on it, no speaking NPC standing in front of it
		for a in m.get("actors", []):
			if str(a.get("scene_id", "")) != sc or not str(a.get("scene", "")).ends_with("Sparrows.tscn"):
				continue
			for p in a.get("props", {}).get("perches", []):
				kit.ok(not _hit(r, float(p[0]) - 6.0, float(p[1]) - 11.0, float(p[0]) + 8.0, float(p[1]) + 1.0), "%s: no sparrow on it (perch %s)" % [k, str(p)])
		for nk in m.get("npcs", {}):
			var ft: Array = m["npcs"][nk].get("feet", [0, 0])
			var area: Array = AREA[sc]
			if float(ft[0]) >= float(area[0]) - 20.0 and float(ft[0]) <= float(area[1]) + 20.0:
				kit.ok(not _hit(r, float(ft[0]) - 8.0, float(ft[1]) - 46.0, float(ft[0]) + 8.0, float(ft[1])), "%s: NPC %s does not stand in front of it" % [k, nk])
	return true


func _cook() -> bool:
	for e in m.get("decals", []):
		if str(e.get("name", "")) != "cook_hatch":
			continue
		var img := _img(ENV + str(e["file"]))
		if not kit.ok(img != null, "cook strip exists"):
			return true
		var opening := [260, 246, 40, 22]                     # env_c4p2_karsk_layout.HATCH
		var frames := int(e.get("frames", 1))
		var fw := img.get_width() / frames
		var outside := 0
		var inside := 0
		for f in frames:
			for y in img.get_height():
				for x in fw:
					if img.get_pixel(f * fw + x, y).a > 0.0:
						var wx := float(e["pos"][0]) + x
						var wy := float(e["pos"][1]) + y
						if _hit(opening, wx, wy, wx + 1.0, wy + 1.0):
							inside += 1
						else:
							outside += 1
		kit.eq(outside, 0, "the cook shows only through the hatch opening (never over its frame or the board)")
		kit.ok(inside > 100 * frames / 8, "the cook is there (%d px)" % inside)
		return true
	kit.ok(false, "cook_hatch strip placed")
	return true


static func _luma(c: Color) -> float:
	return (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) * 255.0


func _sky_b() -> bool:
	# the evening sky is a lit town's night: never a near-black upper picture (review: 75 % of the top was luma < 25)
	var img := _img(ENV + "sky_b.png")
	if not kit.ok(img != null, "sky_b exists"):
		return true
	var dark := 0
	var all := 0
	for y in range(0, 144, 2):
		for x in range(0, img.get_width(), 3):
			all += 1
			if _luma(img.get_pixel(x, y)) < 30.0:
				dark += 1
	kit.ok(float(dark) / float(all) < 0.12, "sky_b: upper 40 %% mostly lit (%d %% darker than luma 30)" % (100 * dark / all))
	var warm := 0
	for y in range(60, 200, 2):
		for x in range(0, img.get_width(), 3):
			var c := img.get_pixel(x, y)
			if c.r > c.b + 0.04:
				warm += 1
	kit.ok(warm > 400, "sky_b: the town's sodium glow on the low cloud (%d warm px)" % warm)
	return true


func _first_frame_colours(e: Dictionary) -> Dictionary:
	var img := _img(ENV + str(e["file"]))
	var cols := {}
	if img == null:
		return cols
	var fw := img.get_width() / maxi(1, int(e.get("frames", 1)))
	for y in img.get_height():
		for x in fw:
			var c := img.get_pixel(x, y)
			if c.a > 0.0:
				cols[c.to_html(false)] = int(cols.get(c.to_html(false), 0)) + 1
	return cols


func _top_row(e: Dictionary) -> int:
	var img := _img(ENV + str(e["file"]))
	var fw := img.get_width() / maxi(1, int(e.get("frames", 1)))
	for y in img.get_height():
		for x in fw:
			if img.get_pixel(x, y).a > 0.0:
				return int(e["pos"][1]) + y
	return -1


static func _dominant(cols: Dictionary) -> String:
	var best := ""
	var n := -1
	for k in cols:
		if int(cols[k]) > n:
			n = int(cols[k])
			best = k
	return best


func _twins() -> bool:
	var by_name := {}
	for e in m.get("decals", []):
		by_name[str(e.get("name", ""))] = e
	# the band: five different people (heights, faces, coats), not one figure five times
	var tops := {}
	var palettes: Array = []
	for k in ["band_tuba", "band_trumpet", "band_trumpet2", "band_horn", "band_drum"]:
		if not kit.ok(by_name.has(k), "%s placed" % k):
			continue
		tops[_top_row(by_name[k])] = true
		palettes.append(_first_frame_colours(by_name[k]))
	kit.ok(tops.size() >= 4, "the band: different heights (%d distinct)" % tops.size())
	var doms := {}
	for p in palettes:
		doms[_dominant(p)] = true
	kit.ok(doms.size() >= 3, "the band: different coats (%d distinct main colours)" % doms.size())
	# the patrol, the conductor and the porter do not share one uniform
	var d := {}
	for k in ["militia_0", "conductor", "porter"]:
		if kit.ok(by_name.has(k), "%s placed" % k):
			d[k] = _dominant(_first_frame_colours(by_name[k]))
	kit.ok(d.size() == 3 and d["militia_0"] != d["conductor"] and d["conductor"] != d["porter"] and d["militia_0"] != d["porter"], "militia, conductor and porter dressed apart (%s)" % str(d))
	return true


func _middle() -> bool:
	# before Lev arrives the sand-drying house and the turntable are not empty (x 1262-1590)
	var n := 0
	for e in m.get("decals", []):
		if not str(e.get("file", "")).begins_with("life/") or str(RegistryLevel._list(e.get("scene"))[0]) != SB:
			continue
		if RegistryLevel._list(e.get("after")).size() > 0:
			continue
		var img := _img(ENV + str(e["file"]))
		if img == null:
			continue
		var x0 := float(e["pos"][0])
		var x1 := x0 + img.get_width() / maxi(1, int(e.get("frames", 1)))
		if x1 > 1262.0 and x0 < 1590.0:
			n += 1
	kit.ok(n >= 3, "turntable + sand-drying house populated before c4g_inspect_book (%d life strips)" % n)
	return true


func _yard_reads() -> bool:
	# the fire barrel: no snow bank in front of the drum
	var a := _img(ENV + "depot_a.png")
	if kit.ok(a != null, "depot_a exists"):
		var snow := {"C2C9D2": true, "DEE2E7": true, "F2F3F5": true}
		var n := 0
		var all := 0
		for y in range(278, 292):
			for x in range(666, 679):
				all += 1
				if snow.has(a.get_pixel(x, y).to_html(false).to_upper()):
					n += 1
		kit.ok(n * 10 < all, "the fire barrel's lower half is not hidden under snow (%d / %d)" % [n, all])
	# the gable emblem sits on the parapet, above the window bays (the wall starts at y 120)
	for e in m.get("decals", []):
		if str(e.get("name", "")) == "insignia_roundhouse_back":
			var img := _img(ENV + str(e["file"]))
			if img != null:
				kit.ok(float(e["pos"][1]) + img.get_height() <= 122.0, "the roundhouse emblem stays above the window bays (bottom y %d)" % int(float(e["pos"][1]) + img.get_height()))
	# the far goods train reads against the dark town: snow on every roof, light in the colours
	for f in ["train_loco", "train_wag_box", "train_wag_gond", "train_wag_tank", "train_wag_flat"]:
		var img := _img(ENV + "actors/%s.png" % f)
		if not kit.ok(img != null, "%s exists" % f):
			continue
		var lit := 0
		for y in img.get_height():
			for x in img.get_width():
				var c := img.get_pixel(x, y)
				if c.a > 0.0 and _luma(c) > 110.0:
					lit += 1
		kit.ok(lit >= 18, "%s: reads against the town (%d light px)" % [f, lit])
	return true
