extends RefCounted
## The Berlin art of Chapter 4 part 2 (L_C4P2_Berlin, assets/environments/berlin_c4p2, tools/pixelgen/env_c4p2_berlin*.py,
## scripts/levels/c4p2/berlin_c4p2_level.gd; owner env-berlin, round 10):
##  * the art contract of C4P2_DESIGN §4.2: world, walk band, every story hotspot / spawn / NPC anchor / the blocker
##    of the story stream's placeholder unchanged; the two walk areas and their camera zones
##  * every referenced file exists; strips are whole numbers of frames; _n / _e maps match; opaque layers and props
##    are binary alpha; the insignia sites and the two documents with insignia keep their neutral + _hist pair (§12.4);
##    the art is palette-pure (ostbahnhof / courtyard of c4p2.json + the proposed ramps, recorded in scene.json meta)
##  * every scene-tagged entry names one of the two scenes; the foreground stays below the walk band
##  * the households of the house puzzle (§2.7) are named with their windows; the life strips of the windows exist
##  * the level script: the scene filter decides at load, camera zones, looks / grades / footsteps per place;
##    Marta's roster follows c4d_choose; the stairwells, the car's lights, the candle and the sweep's men follow
##    c4h_solve_house, Ilse's window until it, Hanna's after it; a memory of B sees only what scene A implies
##  * the inspect documents (five items, alt texts), the walkers of the platform, the station clock actor

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/berlin_c4p2/"
const LEVEL := "res://scenes/levels/L_C4P2_Berlin.tscn"
const SCRIPT := "res://scripts/levels/c4p2/berlin_c4p2_level.gd"
const A := "L_C4P2_BerlinA"
const B := "L_C4P2_BerlinB"
const HOTSPOTS := {"departure_board": 110, "marta_buffet": 300, "shadow_kiosk": 410, "courier_car": 500,
	"ekdahl_window": 680, "dining_table": 800, "gate_notice": 1000, "kuhnert_gate": 1060, "wendt_yard": 1110,
	"hanna_yard": 1250, "lodge_window": 1420, "yard_pump": 1600}
const SPAWNS := {"SP_C4P2_Platform": 60, "SP_C4P2_Gate": 960}
## NPC anchors: [char, x]
const NPCS := {"marta_buffet": ["marta", 318], "shadow_kiosk": ["stapo_civil", 410], "ekdahl_window": ["journalist", 698],
	"kuhnert_gate": ["blockwart", 1060], "wendt_yard": ["wendt", 1128], "hanna_yard": ["hanna", 1268]}
const AREAS := {A: [18, 898], B: [938, 1902]}
const ZONES := {A: [0, 0, 918, 360], B: [918, 0, 1002, 360]}
## the rooms of the house puzzle (§2.7) that face the courtyard with windows (the passage, the hallway and the cellars
## have none of their own)
const ROOMS := ["v1", "v2", "v3", "vd", "s1", "s2", "s3", "se", "sd", "h1", "h2", "h3", "hd", "ws"]
## gated art: name -> [scene, kind, objective / choice]
const GATED := {"roster_l3": [A, "choice", "name_marta"], "roster_l74": [A, "choice", "!name_marta"],
	"stairs_v": [B, "after", "c4h_solve_house"], "stairs_s": [B, "after", "c4h_solve_house"],
	"stairs_h": [B, "after", "c4h_solve_house"], "candle_ws": [B, "after", "c4h_solve_house"],
	"headlights": [B, "after", "c4h_solve_house"], "car": [B, "after", "c4h_solve_house"],
	"sweep_men": [B, "after", "c4h_solve_house"], "candle_flame": [B, "after", "c4h_solve_house"],
	"s3_hanna": [B, "after", "c4h_solve_house"], "s3_ilse": [B, "until", "c4h_solve_house"],
	"yard_coal": [B, "until", "c4h_solve_house"], "yard_wash": [B, "until", "c4h_solve_house"]}
const INSIGNIA := ["plates_booth", "plate_cab", "notice_k14", "yd_dome"]
const DOCUMENTS := {"ev_c4_departures_east": "berlin_c4p2_departures", "ev_c4_courier_seals": "berlin_c4p2_seals",
	"ev_c4_konrad_tracing": "berlin_c4p2_tracing", "ev_c4_house_notice": "berlin_c4p2_house_notice",
	"ev_c4_house_cards": "berlin_c4p2_house_cards"}
const DOC_HIST := ["berlin_c4p2_seals", "berlin_c4p2_house_notice"]
## the words every document must carry legibly (marks)
const DOC_WORDS := {"berlin_c4p2_departures": ["D 303", "21.10", "BERLIN OST – KORDON-17 – KARSK", "BAHNSTEIG K AB 15 UHR GESPERRT."],
	"berlin_c4p2_seals": ["DI – KORDON"], "berlin_c4p2_tracing": ["MOROZOV – 0417", "DI 23.40 – TÜR OST", "212"],
	"berlin_c4p2_house_notice": ["KINDER SIND VORZUZEIGEN.", "BAUABSCHNITT SÜD 9", "KOLONNENSTR. 12 BIS 18", "GEZ. K. A."],
	"berlin_c4p2_house_cards": ["SF 2: POHL, GERTRUD – WITWE – MELDET ZUVERLÄSSIG", "HH 3: LEER, UMGESETZT 10/63"]}
const DOCS_JSON := "res://assets/ui/documents/berlin_c4p2_documents.json"
const ALT_LOCALE := "res://data/locale/de_env_berlin_c4p2.json"

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "berlin_c4p2/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("design_contract", _contract)
	kit.run_case("files_maps_and_strips", _files)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("palette_pure", _palette)
	kit.run_case("scene_tags_and_foreground", _tags)
	kit.run_case("households_in_the_windows", _households)
	kit.run_case("scene_filter_looks_footsteps", _scene_filter)
	kit.run_case("gated_art_follows_story", _gates)
	kit.run_case("memory_sees_its_scene", _memory)
	kit.run_case("inspect_documents", _documents)
	kit.run_case("walkers_of_the_platform", _walkers)
	kit.run_case("station_clock", _clock)
	kit.run_case("strips_over_patches_and_insignia", _layering)
	kit.run_case("dome_banners_above_the_ridge", _dome)
	kit.run_case("no_empty_dark_bands", _bands)
	kit.cleanup()
	return kit.failures


static func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	return Image.load_from_file(ProjectSettings.globalize_path(path))


func _entries() -> Array:
	var out: Array = []
	for section in ["layers", "props", "decals", "fx"]:
		for e in m.get(section, []):
			if e is Dictionary:
				out.append([section, e])
	return out


static func _ints(v):
	if v is Array:
		var out: Array = []
		for x in v:
			out.append(_ints(x))
		return out
	if v is float and is_equal_approx(v, round(v)):
		return int(v)
	return v


# ------------------------------------------------------------------ contract
func _contract() -> bool:
	kit.eq(m.get("id"), "berlin_c4p2", "env id")
	kit.ok(not m.has("placeholder"), "the placeholder flag is gone (art delivered)")
	kit.eq(_ints(m.get("world_size")), [1920, 360], "world 1920 x 360")
	kit.eq(_ints(m.get("walkable")), [[18, 296], [1902, 296], [1902, 306], [18, 306]], "walk band y 296-306, x 18-1902")
	var hs: Dictionary = m.get("hotspots", {})
	for k in HOTSPOTS:
		kit.eq(_ints(hs.get(k)), [HOTSPOTS[k], 300], "story hotspot %s at (%d, 300)" % [k, HOTSPOTS[k]])
	var sp: Dictionary = m.get("spawns", {})
	for k in SPAWNS:
		kit.eq(_ints(sp.get(k)), [SPAWNS[k], 300], "spawn %s at (%d, 300)" % [k, SPAWNS[k]])
	var npcs: Dictionary = m.get("npcs", {})
	for k in NPCS:
		var n: Dictionary = npcs.get(k, {})
		kit.eq([n.get("char"), _ints(n.get("feet"))], [NPCS[k][0], [NPCS[k][1], 300]], "NPC anchor %s" % k)
	kit.eq(npcs.get("wendt_yard", {}).get("show_after"), "c4h_solve_house", "Wendt after the house")
	kit.eq(npcs.get("hanna_yard", {}).get("hide_after"), "c4h_solve_house", "Hanna until the house")
	var bl: Array = m.get("blockers", [])
	if kit.eq(bl.size(), 1, "one permanent blocker"):
		kit.eq(bl[0].get("name"), "platform_end", "blocker name")
		kit.eq(_ints(bl[0].get("rect")), [898, 270, 40, 60], "blocker rect between the walk areas")
		kit.ok(not (bl[0] as Dictionary).has("after") and not (bl[0] as Dictionary).has("until"), "the blocker is permanent")
	var cz: Dictionary = m.get("camera_zones", {})
	for sid in ZONES:
		kit.eq(_ints(cz.get(sid)), ZONES[sid], "camera zone of %s" % sid)
		var z: Array = ZONES[sid]
		kit.ok(AREAS[sid][0] >= int(z[0]) and AREAS[sid][1] <= int(z[0]) + int(z[2]), "%s: the walk area lies in its zone" % sid)
	for k in HOTSPOTS:
		var sid := A if HOTSPOTS[k] < 898 else B
		kit.ok(HOTSPOTS[k] >= AREAS[sid][0] and HOTSPOTS[k] <= AREAS[sid][1], "%s inside the walk area of %s" % [k, sid])
	var info: Dictionary = m.get("hotspot_info", {})
	for k in HOTSPOTS:
		var e: Dictionary = info.get(k, {})
		if kit.ok(e.has("object_x") and e.has("what"), "hotspot_info %s" % k):
			var ox: Array = e["object_x"]
			kit.ok(absf(float(HOTSPOTS[k]) - clampf(float(HOTSPOTS[k]), float(ox[0]), float(ox[1]))) <= 40.0,
				"%s stands at its painted object (x %s)" % [k, str(ox)])
	var looks: Array = m.get("looks", [])
	kit.eq(looks.size(), 2, "two looks")
	return true


# ------------------------------------------------------------------ files
func _files() -> bool:
	for pair in _entries():
		var section: String = pair[0]
		var e: Dictionary = pair[1]
		var path: String = ENV + str(e.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s file %s exists" % [section, e.get("file")]):
			continue
		var frames := int(e.get("frames", 1))
		kit.ok(img.get_width() % frames == 0, "%s: %d frames divide its width %d" % [e.get("file"), frames, img.get_width()])
		if bool(e.get("normal", false)):
			var n := _img(path.get_basename() + "_n.png")
			if kit.ok(n != null, "%s has its normal map" % e.get("file")):
				kit.eq(n.get_size(), img.get_size(), "%s: normal map size" % e.get("file"))
		if bool(e.get("emission", false)):
			var em := _img(path.get_basename() + "_e.png")
			if kit.ok(em != null, "%s has its emission map" % e.get("file")):
				kit.eq(em.get_size(), img.get_size(), "%s: emission map size" % e.get("file"))
		if section in ["layers", "props"] and bool(e.get("lit", true)) and str(e.get("name", "")) in ["station", "yard", "counter_front"]:
			var soft := 0
			for y in range(0, img.get_height(), 3):
				for x in range(0, img.get_width(), 3):
					var a := img.get_pixel(x, y).a
					if a > 0.01 and a < 0.99:
						soft += 1
			kit.eq(soft, 0, "%s: binary alpha" % e.get("file"))
	for a in m.get("actors", []):
		var sc := str(a.get("scene", ""))
		kit.ok(ResourceLoader.exists(sc), "actor scene %s exists" % sc)
		var pr: Dictionary = a.get("props", {})
		for key in ["sprite", "bread", "glow_path", "data", "loop_path"]:
			if pr.has(key):
				kit.ok(FileAccess.file_exists(str(pr[key])) or ResourceLoader.exists(str(pr[key])), "actor %s: %s %s exists" % [sc.get_file(), key, pr[key]])
	return true


func _insignia() -> bool:
	var seen := {}
	for pair in _entries():
		var e: Dictionary = pair[1]
		if e.has("hist_variant"):
			seen[str(e.get("name"))] = true
			var n := _img(ENV + str(e["file"]))
			var h := _img(ENV + str(e["hist_variant"]))
			if kit.ok(n != null and h != null, "%s: neutral + _hist exist" % e.get("name")):
				kit.eq(h.get_size(), n.get_size(), "%s: same footprint" % e.get("name"))
				kit.ok(h.get_data() != n.get_data(), "%s: the historical variant differs" % e.get("name"))
				kit.eq(str(e["hist_variant"]), str(e["file"]).get_basename() + "_hist.png", "%s: Symbols.pick() finds the _hist twin" % e.get("name"))
	for nm in INSIGNIA:
		kit.ok(seen.has(nm), "insignia site %s declared (12.4)" % nm)
	for d in DOC_HIST:
		var n := _img("res://assets/ui/documents/%s.png" % d)
		var h := _img("res://assets/ui/documents/%s_hist.png" % d)
		if kit.ok(n != null and h != null, "document %s: neutral + _hist" % d):
			kit.ok(n.get_data() != h.get_data(), "document %s: the historical variant differs" % d)
	return true


func _palette() -> bool:
	var meta: Dictionary = m.get("meta", {})
	var pals := {}
	for key in ["palette_ostbahnhof", "palette_courtyard"]:
		var allowed := {}
		var pal: Dictionary = meta.get(key, {})
		for ramp in pal:
			for hexc in pal[ramp]:
				allowed[str(hexc).to_upper().substr(1)] = true
		pals[key] = allowed
	kit.ok(not (pals["palette_ostbahnhof"] as Dictionary).is_empty() and not (pals["palette_courtyard"] as Dictionary).is_empty(), "palettes recorded in scene.json meta")
	kit.ok((pals["palette_ostbahnhof"] as Dictionary).size() <= 64 and (pals["palette_courtyard"] as Dictionary).size() <= 64, "each palette fits the grade's 64 colours")
	for pair in _entries():
		var e: Dictionary = pair[1]
		var allowed: Dictionary = pals["palette_ostbahnhof" if str(e.get("scene", "")) == A else "palette_courtyard"]
		for f in [str(e["file"]), str(e["file"]).get_basename() + "_e.png", str(e.get("hist_variant", ""))]:
			if f == "" or not FileAccess.file_exists(ENV + f):
				continue
			var img := _img(ENV + f)
			var off := 0
			for y in range(0, img.get_height(), 2):
				for x in range(0, img.get_width(), 2):
					var c := img.get_pixel(x, y)
					if c.a > 0.0 and not allowed.has(c.to_html(false).to_upper()):
						off += 1
			kit.eq(off, 0, "%s palette-pure" % f)
	return true


func _tags() -> bool:
	for pair in _entries():
		var e: Dictionary = pair[1]
		kit.ok(str(e.get("scene", "")) in [A, B], "%s names its scene" % e.get("name", e.get("file")))
		if str(e.get("name", "")).begins_with("fg_"):
			kit.ok(int(e["pos"][1]) >= 318, "%s stays below the walk band (y >= 318)" % e["name"])
		if pair[0] == "props":
			kit.ok(float(e.get("base_y", 0)) <= 294.0, "prop %s stands behind the walk band" % e.get("name"))
	for a in m.get("actors", []):
		kit.ok(str(a.get("scene_id", "")) in [A, B], "actor %s names its scene" % a.get("scene"))
	return true


func _households() -> bool:
	var hh: Dictionary = m.get("households", {})
	for r in ROOMS:
		kit.ok(hh.has(r), "household %s named with its windows (§2.7)" % r)
	var lit := 0
	for r in hh:
		if str(hh[r].get("light")) in ["lit", "dim"]:
			lit += 1
	kit.ok(lit >= 7, "at least seven households lit or dim (%d)" % lit)
	var names := {}
	for e in m.get("decals", []):
		names[str(e.get("name"))] = e
	for nm in ["v1_schulz", "v3_lenz", "s1_mertens", "s2_pohl", "s3_ilse", "s3_hanna", "se_kuhnert", "h1_kuehn"]:
		kit.ok(names.has(nm) and int(names[nm].get("frames", 1)) > 1, "window life %s animates" % nm)
	for nm in ["booth_officials", "baggage_clerk", "sleeping_boy", "kiosk_woman", "loco_crew", "diners", "sleeper_passenger"]:
		kit.ok(names.has(nm) and int(names[nm].get("frames", 1)) > 1, "platform life %s animates" % nm)
	return true


# ------------------------------------------------------------------ the level script
func _mount(scene_id: String) -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("level_id", scene_id)
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	return lvl


func _state(lvl: Node, done := {}, choice := {}) -> void:
	lvl.set("done_override", done)
	lvl.set("choice_override", choice)
	lvl.set("memory_override", false)
	lvl.set("hidden_override", false)
	lvl.call("refresh", true)


func _built_names(lvl: Node) -> Array:
	var out: Array = []
	var man: Dictionary = lvl.get("manifest")
	for section in ["layers", "props", "decals", "fx", "lights"]:
		for e in man.get(section, []):
			out.append(str(e.get("name", e.get("file", ""))))
	for g in lvl.get("groups"):
		out.append_array(g["names"])
	return out


func _scene_filter() -> bool:
	for sid in [A, B]:
		var lvl := _mount(sid)
		kit.eq((lvl.get_script() as Script).resource_path, SCRIPT, "%s: the shell runs berlin_c4p2_level.gd" % sid)
		kit.ok(lvl is Level, "berlin_c4p2_level extends Level")
		kit.eq(lvl.get_camera_bounds(), Rect2(ZONES[sid][0], ZONES[sid][1], ZONES[sid][2], ZONES[sid][3]), "%s: camera clamped to its zone" % sid)
		_state(lvl)
		kit.eq(lvl.call("look"), "station" if sid == A else "courtyard", "%s plays its look" % sid)
		kit.eq(str(lvl.get("grade_preset")), "ostbahnhof" if sid == A else "courtyard_night", "%s: grade of the scene" % sid)
		kit.eq(str(lvl.get("footstep_surface")), "concrete" if sid == A else "snow", "%s: footsteps of the place" % sid)
		var built := _built_names(lvl)
		for pair in _entries():
			var e: Dictionary = pair[1]
			if e.has("scene"):
				var nm := str(e.get("name", e.get("file", "")))
				kit.eq(nm in built, str(e["scene"]) == sid, "%s: %s built only in its own scene" % [sid, nm])
		var man: Dictionary = lvl.get("manifest")
		for a in man.get("actors", []):
			if (a as Dictionary).has("scene_id"):
				kit.eq(str(a["scene_id"]), sid, "%s: actor %s of this scene" % [sid, a.get("scene")])
		kit.eq(lvl.call("blocker_on", "platform_end"), true, "%s: the end of platform K always stands" % sid)
		for nd in ["MartaBuffet", "ShadowKiosk", "EkdahlWindow", "KuhnertGate", "WendtYard", "HannaYard"]:
			kit.ok(lvl.get_node_or_null("Playfield/" + nd) != null, "%s: NPC node %s kept" % [sid, nd])
		lvl.free()
	return true


func _gates() -> bool:
	var lvl := _mount(A)
	for ch in [["name_marta", "roster_l3"], ["protect_marta", "roster_l74"], ["", "roster_l74"]]:
		_state(lvl, {}, {"c4d_choose": ch[0]} if ch[0] != "" else {})
		kit.eq(lvl.call("is_shown", ch[1]), true, "c4d %s: %s on the counter" % [ch[0] if ch[0] != "" else "(none)", ch[1]])
		var other: String = "roster_l74" if ch[1] == "roster_l3" else "roster_l3"
		kit.eq(lvl.call("is_shown", other), false, "c4d %s: not %s" % [ch[0] if ch[0] != "" else "(none)", other])
	lvl.free()
	lvl = _mount(B)
	for nm in GATED:
		if GATED[nm][0] != B:
			continue
		var kind: String = GATED[nm][1]
		_state(lvl, {})
		kit.eq(lvl.call("is_shown", nm), kind == "until", "%s before c4h_solve_house" % nm)
		_state(lvl, {"c4h_solve_house": true})
		kit.eq(lvl.call("is_shown", nm), kind == "after", "%s after c4h_solve_house" % nm)
	lvl.free()
	return true


func _memory() -> bool:
	var lvl := _mount(B)
	lvl.set("done_override", null)
	lvl.set("memory_override", true)
	lvl.set("hidden_override", false)
	lvl.call("refresh", true)
	kit.eq(lvl.call("objective_done", "c4f_inspect_book"), true, "memory of B: scene A's objectives count")
	kit.eq(lvl.call("objective_done", "c4h_solve_house"), false, "memory of B: its own objectives start open")
	kit.eq(lvl.call("is_shown", "s3_ilse"), true, "memory of B: Ilse draws at Hanna's table again")
	kit.eq(lvl.call("is_shown", "stairs_s"), false, "memory of B: the stairwells dark again")
	lvl.free()
	return true


# ------------------------------------------------------------------ documents, walkers, clock
func _documents() -> bool:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(DOCS_JSON))
	if not kit.ok(parsed is Dictionary and parsed.get("documents") is Array, "berlin_c4p2_documents.json parses"):
		return false
	var lf = JSON.parse_string(FileAccess.get_file_as_string(ALT_LOCALE))
	var alt_strings: Dictionary = lf.get("strings", {}) if lf is Dictionary else {}
	kit.ok(not alt_strings.is_empty(), "de_env_berlin_c4p2.json parses")
	var by_item := {}
	for e in parsed["documents"]:
		by_item[str(e.get("item_id"))] = e
	for item in DOCUMENTS:
		var e: Dictionary = by_item.get(item, {})
		if not kit.ok(not e.is_empty(), "%s has a document entry" % item):
			continue
		kit.eq(str(e.get("id")), DOCUMENTS[item], "%s: document id" % item)
		var img := _img("res://assets/ui/documents/%s.png" % DOCUMENTS[item])
		if kit.ok(img != null, "%s: InspectView loads it" % item):
			kit.eq(_ints(e.get("size")), [img.get_width(), img.get_height()], "%s: size recorded" % item)
			kit.ok(img.get_width() * 3 <= 1060 and img.get_height() * 3 <= 760, "%s: fits the inspect view at 3x" % item)
		var alt := str(e.get("alt_key", ""))
		kit.ok(alt_strings.has(alt) and str(alt_strings[alt]).length() > 40, "%s: German alt text %s" % [item, alt])
		var texts: Array = []
		for mk in (e.get("marks", {}) as Dictionary).values():
			texts.append(str(mk.get("text", "")))
		for w in DOC_WORDS.get(DOCUMENTS[item], []):
			kit.ok(w in texts, "%s: „%s“ legible" % [DOCUMENTS[item], w])
		var UIKit = load("res://scripts/ui/ui_kit.gd")
		kit.eq(UIKit.doc_for_item(item), DOCUMENTS[item], "%s: ui_kit finds the document" % item)
	return true


func _walkers() -> bool:
	var wj = JSON.parse_string(FileAccess.get_file_as_string(ENV + "walkers_a.json"))
	if not kit.ok(wj is Dictionary and wj.get("walkers") is Array, "walkers_a.json parses"):
		return false
	var ids := {}
	for w in wj["walkers"]:
		var id := str(w.get("id"))
		kit.ok(not ids.has(id), "walker %s unique" % id)
		ids[id] = true
		var rig := ENV + str(w.get("rig", ""))
		kit.ok(FileAccess.file_exists(rig) and FileAccess.file_exists(rig.get_basename() + ".png") and FileAccess.file_exists(rig.get_basename() + "_n.png"), "walker %s: rig json + png + normal map" % id)
		for p in w.get("path", []):
			kit.ok(float(p[0]) >= AREAS[A][0] and float(p[0]) <= AREAS[A][1], "walker %s stays on platform K (x %s)" % [id, p[0]])
			kit.ok(float(p[1]) <= 295.5, "walker %s walks behind the walk band (y %s)" % [id, p[1]])
	kit.ok(ids.size() >= 10, "a populated platform (%d walkers)" % ids.size())
	return true


## the drawn rect of a decal (one frame of a strip)
func _rect(e: Dictionary) -> Rect2:
	var img := _img(ENV + str(e.get("file", "")))
	if img == null:
		return Rect2()
	var fr := maxi(1, int(e.get("frames", 1)))
	return Rect2(float(e["pos"][0]), float(e["pos"][1]), float(img.get_width() / fr), float(img.get_height()))


## Review round 10: a life strip that sits on a story patch is drawn above it (the sweep's men on the headlights,
## the candle flame on the souterrain window); whatever is drawn above an insignia site switches with it (_hist).
func _layering() -> bool:
	var decals: Array = []
	for e in m.get("decals", []):
		if e is Dictionary and str(e.get("layer", "")) != "playfield":
			decals.append(e)
	for s in decals:
		if int(s.get("frames", 1)) <= 1:
			continue
		var rs := _rect(s)
		for p in decals:
			if p == s or int(p.get("frames", 1)) > 1 or str(p.get("scene")) != str(s.get("scene")):
				continue
			if not (p.has("after") or p.has("until") or p.has("choice") or p.has("hist_variant")):
				continue
			if rs.intersects(_rect(p)):
				kit.ok(int(s.get("z", 0)) > int(p.get("z", 0)), "strip %s is drawn above patch %s" % [s.get("name"), p.get("name")])
	for ins in decals:
		if not ins.has("hist_variant"):
			continue
		var ri := _rect(ins)
		for o in decals:
			if o == ins or str(o.get("scene")) != str(ins.get("scene")) or not ri.intersects(_rect(o)):
				continue
			if int(o.get("z", 0)) >= int(ins.get("z", 0)) and not _see_through(o):
				kit.ok(o.has("hist_variant"), "%s over the insignia site %s switches with it" % [o.get("name"), ins.get("name")])
	return true


## a figure strip on a transparent ground (people standing in front of the site) -- not a crop of the layer
func _see_through(e: Dictionary) -> bool:
	var img := _img(ENV + str(e.get("file", "")))
	if img == null or int(e.get("frames", 1)) <= 1:
		return false
	var fw := img.get_width() / int(e["frames"])
	var clear := 0
	for y in range(0, img.get_height(), 2):
		for x in range(0, fw, 2):
			if img.get_pixel(x, y).a < 0.01:
				clear += 1
	return clear * 4 >= fw * img.get_height() / 2


## the Great Hall's banners (the only difference of yd_dome / _hist) stand above the courtyard's ridge (y 60)
func _dome() -> bool:
	for e in m.get("layers", []):
		if str(e.get("name")) != "yd_dome":
			continue
		var n := _img(ENV + str(e["file"]))
		var h := _img(ENV + str(e["hist_variant"]))
		if not kit.ok(n != null and h != null and n.get_size() == h.get_size(), "yd_dome: both variants"):
			return false
		var top := -1
		for y in n.get_height():
			for x in n.get_width():
				if n.get_pixel(x, y) != h.get_pixel(x, y):
					top = y
					break
			if top >= 0:
				break
		kit.ok(top >= 0, "yd_dome: the banners differ")
		kit.ok(top + int(e["pos"][1]) < 60, "yd_dome: the banners show above the courtyard's ridge (y %d)" % (top + int(e["pos"][1])))
	return true


## the foregrounds and the vault are painted places, not near-black bands (review round 10)
func _bands() -> bool:
	for spec in [["fg_station.png", 0, 42, 0.12], ["fg_yard.png", 0, 42, 0.2], ["st_hall.png", 0, 150, 0.12]]:
		var img := _img(ENV + str(spec[0]))
		if not kit.ok(img != null, "%s exists" % spec[0]):
			continue
		var sum := 0.0
		var sq := 0.0
		var n := 0
		for y in range(int(spec[1]), mini(int(spec[2]), img.get_height()), 2):
			for x in range(0, img.get_width(), 2):
				var c := img.get_pixel(x, y)
				if c.a <= 0.0:
					continue
				var l := c.get_luminance()
				sum += l
				sq += l * l
				n += 1
		var mean := sum / maxf(1.0, float(n))
		var sd := sqrt(maxf(0.0, sq / maxf(1.0, float(n)) - mean * mean))
		kit.ok(mean >= float(spec[3]), "%s: mean luminance %.3f >= %.2f" % [spec[0], mean, spec[3]])
		kit.ok(sd >= 0.06, "%s: detail (std %.3f)" % [spec[0], sd])
	return true


func _clock() -> bool:
	var sc = load("res://scenes/levels/c4p2/C4P2StationClock.tscn")
	if not kit.ok(sc is PackedScene, "the station clock actor scene loads"):
		return false
	var c: Node = (sc as PackedScene).instantiate()
	var a0: Dictionary = c.call("hand_angles", 20.0 * 3600.0 + 31.0 * 60.0)
	var a1: Dictionary = c.call("hand_angles", 20.0 * 3600.0 + 31.0 * 60.0 + 59.0)
	kit.ok(is_equal_approx(float(a0["minute"]), 31.0 / 60.0 * TAU), "20.31: the minute hand on 31")
	kit.ok(is_equal_approx(float(a1["minute"]), float(a0["minute"])), "the minute hand jumps, it does not creep")
	kit.ok(is_equal_approx(float(a1["second"]), TAU), "the second hand waits at the top before the jump")
	c.free()
	return true
