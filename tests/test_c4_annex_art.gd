extends RefCounted
## The annex art of Chapter 4 part 1 (L_C4_Annex, assets/environments/berlin_annex, tools/pixelgen/env_c4_annex*.py,
## scripts/levels/c4/annex_level.gd):
##  * the art contract of C4_DESIGN §4.2: world, walk band, every story hotspot / spawn / NPC anchor / the blocker
##    unchanged; the two walk areas and their camera zones (the street never shows underground and vice versa)
##  * every referenced file exists; strips are whole numbers of frames; _n / _e maps match; opaque art is binary
##    alpha; the insignia sites keep their neutral + _hist pair (§12.4); the art is palette-pure ('annex' of
##    c4.json + the proposed 'lamp' ramp); every scene-tagged entry names one of the two scenes
##  * every story hotspot stands at the painted object it belongs to; the foreground frames keep them clear
##  * the level script: the scene filter decides at load (scene A builds no annex entry and vice versa), camera
##    zones, looks / grades per scene, story patches follow their objectives, a memory sees only what its scene
##    implies

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/berlin_annex/"
const LEVEL := "res://scenes/levels/L_C4_Annex.tscn"
const SCRIPT := "res://scripts/levels/c4/annex_level.gd"
const A := "L_C4_AnnexA"
const B := "L_C4_AnnexB"
const HOTSPOTS := {"door_9": 118, "timetable_case": 292, "marta_tram": 404, "column_s2": 646, "loading_hatch": 762,
	"drawer_s8": 1232, "plan_wall": 1376, "tube_station": 1548, "registrar_counter": 1716, "guard_annex": 1868}
const SPAWNS := {"SP_C4_Shelter": 236, "SP_C4_Ladder": 902}
## NPC anchors: [char, x, feet y] -- Fengler stands behind the counter prop (round-9 art fix art-06)
const NPCS := {"marta_tram": ["marta", 422, 300], "registrar_counter": ["registrar", 1734, 276],
	"guard_annex": ["guard", 1868, 300]}
const AREAS := {A: [18, 822], B: [846, 1902]}
const ZONES := {A: [0, 0, 846, 360], B: [846, 0, 1074, 360]}
const SCENE_OF_HOTSPOT := {"door_9": A, "timetable_case": A, "marta_tram": A, "column_s2": A, "loading_hatch": A,
	"drawer_s8": B, "plan_wall": B, "tube_station": B, "registrar_counter": B, "guard_annex": B}
## gated story patches: name -> [scene, objective]
## the annex items with an inspect document (the route board's close-up since the round-9 fix compl-04; the route
## puzzle keeps its own overlay)
const DOCUMENTS := {"ev_c4_notice": "berlin_annex_notice", "ev_c4_shaft": "berlin_annex_shaft",
	"ev_c4_card_de": "berlin_annex_card_de", "ev_c4_drawer_s8": "berlin_annex_drawer",
	"ev_c4_annex_plan": "berlin_annex_plan", "ev_c4_tube_slip": "berlin_annex_tube_slip",
	"ev_c4_route_board": "berlin_annex_route_board"}
const DOCS_JSON := "res://assets/ui/documents/berlin_annex_documents.json"
const ALT_LOCALE := "res://data/locale/de_env_berlin_annex.json"
## round-9 fix art-11: drawer „Süd 3“ stands a finger's width open, Brandt's card standing up (find exp_brandt_card)
const DRAWER_S3 := [1155, 1169]
const DRAWER_S4 := [1169, 1183]
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const PATCHES := {"routes_case": [A, "c4b_solve_routes"], "column_bared": [A, "c4b_inspect_column"],
	"drawer_s8_open": [B, "c4d_inspect_drawer"], "capsule_open": [B, "c4d_inspect_tube"],
	"form_counter": [B, "c4d_talk_registrar"]}

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "berlin_annex/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("design_contract", _contract)
	kit.run_case("files_maps_and_strips", _files)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("palette_pure", _palette)
	kit.run_case("hotspots_at_their_objects", _objects)
	kit.run_case("foreground_keeps_hotspots_clear", _fg_clear)
	kit.run_case("scene_filter_and_camera_zones", _scene_filter)
	kit.run_case("story_patches_follow_objectives", _patches)
	kit.run_case("memory_sees_its_scene", _memory)
	kit.run_case("inspect_documents", _documents)
	kit.run_case("art_fixes_r9_notice_poster_counter", _art_fixes_r9)
	kit.run_case("art_fix_r9_drawer_sued_3", _drawer_s3)
	kit.cleanup()
	return kit.failures


func _img(path: String) -> Image:
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


## JSON numbers arrive as floats: compare integral values as ints.
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
	kit.eq(m.get("id"), "berlin_annex", "env id")
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
		kit.eq([n.get("char"), _ints(n.get("feet"))], [NPCS[k][0], [NPCS[k][1], NPCS[k][2]]], "NPC anchor %s" % k)
	var bl: Array = m.get("blockers", [])
	if kit.eq(bl.size(), 1, "one permanent blocker"):
		kit.eq(bl[0].get("name"), "shaft_wall", "blocker name")
		kit.eq(_ints(bl[0].get("rect")), [822, 270, 24, 60], "blocker rect between the walk areas")
		kit.ok(not (bl[0] as Dictionary).has("after") and not (bl[0] as Dictionary).has("until"), "the blocker is permanent")
	var cz: Dictionary = m.get("camera_zones", {})
	for sid in ZONES:
		kit.eq(_ints(cz.get(sid)), ZONES[sid], "camera zone of %s" % sid)
		var z: Array = ZONES[sid]
		kit.ok(int(z[2]) >= 640 and int(z[3]) == 360, "%s: the zone is at least one screen wide" % sid)
		kit.ok(AREAS[sid][0] >= int(z[0]) and AREAS[sid][1] <= int(z[0]) + int(z[2]), "%s: the walk area lies in its zone" % sid)
	for k in HOTSPOTS:
		var area: Array = AREAS[SCENE_OF_HOTSPOT[k]]
		kit.ok(HOTSPOTS[k] >= area[0] and HOTSPOTS[k] <= area[1], "%s inside the walk area of %s" % [k, SCENE_OF_HOTSPOT[k]])
	kit.ok(SPAWNS["SP_C4_Shelter"] <= AREAS[A][1] and SPAWNS["SP_C4_Ladder"] >= AREAS[B][0], "entry spawns in their own areas")
	for z in ["loop", "shaft", "machine_room", "card_hall", "tube", "counter", "corridor"]:
		kit.ok((m.get("zones", {}) as Dictionary).has(z), "zone %s kept" % z)
	var looks: Array = m.get("looks", [])
	kit.eq(looks.map(func(L: Dictionary) -> Array: return [L.get("scene"), L.get("grade")]),
		[[A, "annex_loop"], [B, "annex"]], "one look per scene with the c4.json grades")
	return true


func _files() -> bool:
	var names := {}
	for pair in _entries():
		var section: String = pair[0]
		var e: Dictionary = pair[1]
		var nm := str(e.get("name", e.get("file", "")))
		kit.ok(not names.has(section + nm), "%s: unique name %s" % [section, nm])
		names[section + nm] = true
		if e.has("scene"):
			kit.ok(str(e["scene"]) in [A, B], "%s: scene tag %s is one of the two scenes" % [nm, e["scene"]])
		var path: String = ENV + str(e.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s %s: file %s exists" % [section, nm, path]):
			continue
		var frames := int(e.get("frames", 1))
		kit.ok(frames >= 1 and img.get_width() % frames == 0, "%s: width %d is a whole number of %d frames" % [nm, img.get_width(), frames])
		kit.ok(img.get_width() <= 16384 and img.get_height() <= 360, "%s: size %s within texture limits" % [nm, img.get_size()])
		if frames > 1:
			kit.ok(float(e.get("fps", 0)) > 0.0 and float(e.get("fps", 0)) <= 12.0, "%s: fps in (0, 12]" % nm)
		var file := str(e.get("file", ""))
		var opaque := nm in ["loop", "annex", "fg_loop", "fg_annex", "sky", "far", "mid", "dome"] or file.begins_with("patches/") \
			or nm.begins_with("fan_") or nm.begins_with("typist_") or nm in ["ilse", "capsule_glass", "tube_flicker"]
		if opaque:
			kit.ok(img.detect_alpha() != Image.ALPHA_BLEND, "%s: binary alpha (coded texel material)" % nm)
		var maps: Array = []
		if bool(e.get("normal", section == "props")):
			maps.append("_n")
		if bool(e.get("emission", false)):
			maps.append("_e")
		for suffix in maps:
			var mp: String = path.get_basename() + suffix + ".png"
			var mi := _img(mp)
			if kit.ok(mi != null, "%s: map %s exists" % [nm, mp]):
				kit.eq(mi.get_size(), img.get_size(), "%s: %s map matches the image" % [nm, suffix])
		if e.has("fade"):
			kit.ok(float(e["fade"]) >= 0.0 and float(e["fade"]) <= 3.0, "%s: fade within 0..3 s" % nm)
		# a parallax layer covers the screen width over the whole camera range of its scene (the dome is a motif)
		var par0 := float((e.get("parallax", [1, 1]) as Array)[0])
		if section == "layers" and e.has("scene") and par0 != 1.0 and nm != "dome":
			var z: Array = ZONES[str(e["scene"])]
			var ok := true
			for cam in [float(z[0]), float(z[0]) + float(z[2]) - 640.0]:
				var sx: float = float(e["pos"][0]) - float(cam) * par0
				ok = ok and sx <= 0.5 and sx + float(img.get_width()) >= 639.5
			kit.ok(ok, "%s: covers the screen width over the camera range of its scene" % nm)
	var lights := {}
	for li in m.get("lights", []):
		var ln := str(li.get("name", ""))
		kit.ok(not lights.has(ln), "light %s unique" % ln)
		lights[ln] = true
		var p: Array = li.get("pos", [0, 0])
		kit.ok(float(p[0]) >= 0 and float(p[0]) <= 1920 and float(p[1]) >= 0 and float(p[1]) <= 360, "light %s inside the world" % ln)
		kit.ok(str(li.get("scene", "")) in [A, B], "light %s belongs to one scene (no light reaches the other area)" % ln)
		if str(li.get("scene", "")) == A:
			kit.ok(float(p[0]) - float(li.get("radius", 0)) < 846.0, "light %s lights the street" % ln)
	for need in ["sky", "dome", "far", "mid", "loop", "annex", "fg_loop", "fg_annex"]:
		var found := false
		for L in m.get("layers", []):
			found = found or str(L.get("name")) == need
		kit.ok(found, "layer %s present" % need)
	for need in ["ilse", "fan_a", "fan_b", "typist_a", "typist_b", "capsule_glass", "tube_flicker", "fence_blinker"]:
		kit.ok(names.has("decals" + need), "life / machinery strip %s present" % need)
	for need in ["snow_a", "snow_b", "steam_s2", "exhaust", "chimney_11", "dust_fans"]:
		kit.ok(names.has("fx" + need), "fx strip %s present" % need)
	return true


func _insignia() -> bool:
	var sites := []
	for pair in _entries():
		var e: Dictionary = pair[1]
		if not e.has("hist_variant"):
			continue
		sites.append(str(e.get("name")))
		var hv: String = ENV + str(e["hist_variant"])
		var base: String = ENV + str(e["file"])
		kit.eq(hv, Symbols.hist_path(base), "%s: hist variant follows the <name>_hist rule" % e.get("name"))
		var hi := _img(hv)
		var bi := _img(base)
		if kit.ok(hi != null and bi != null, "%s: neutral + _hist files exist" % e.get("name")):
			kit.eq(hi.get_size(), bi.get_size(), "%s: _hist has the size of the neutral file" % e.get("name"))
			kit.ne(hi.get_data(), bi.get_data(), "%s: the _hist file differs from the neutral one" % e.get("name"))
	for need in ["dome", "notice_s2", "plate_counter", "plate_stapo"]:
		kit.ok(need in sites, "insignia site %s has its pair" % need)
	return true


func _palette() -> bool:
	var c4 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c4.json"))
	var ramps: Dictionary = m.get("meta", {}).get("palette_ramps", {})
	var allowed := {}
	for ramp in ramps.values():
		for h in ramp:
			allowed[str(h).to_upper().trim_prefix("#")] = true
	# the art's palette contains every colour of c4.json palettes.annex (it may add the proposed ramps)
	for rn in c4.get("palettes", {}).get("annex", {}):
		for h in c4["palettes"]["annex"][rn]:
			kit.ok(allowed.has(str(h).to_upper().trim_prefix("#")), "c4.json annex.%s %s is part of the art palette" % [rn, h])
	var files: Array = ["loop.png", "annex.png", "sky.png", "far.png", "mid.png", "dome.png", "dome_hist.png"]
	for d in m.get("decals", []):
		if str(d.get("file", "")).begins_with("patches/"):
			files.append(str(d["file"]))
	for f in files:
		var img := _img(ENV + f)
		if not kit.ok(img != null, f + " loads"):
			continue
		var bad := 0
		var step := 3 if img.get_width() > 400 else 1
		for y in range(0, img.get_height(), step):
			for x in range(0, img.get_width(), step):
				var c := img.get_pixel(x, y)
				if c.a > 0.5 and not allowed.has(c.to_html(false).to_upper()):
					bad += 1
		kit.eq(bad, 0, "%s: every sampled pixel is an 'annex' palette colour" % f)
	return true


# ------------------------------------------------------------------ placement
func _objects() -> bool:
	var info: Dictionary = m.get("hotspot_info", {})
	for k in HOTSPOTS:
		if not kit.ok(info.has(k), "hotspot_info names the object of %s" % k):
			continue
		var span: Array = info[k].get("object_x", [])
		kit.ok(span.size() == 2 and float(span[0]) <= HOTSPOTS[k] and HOTSPOTS[k] <= float(span[1]),
			"%s (x %d) stands at its object %s %s" % [k, HOTSPOTS[k], info[k].get("what", ""), span])
	# the story patches sit at the objects they change
	for d in m.get("decals", []):
		var nm := str(d.get("name"))
		if PATCHES.has(nm):
			var x := float(d["pos"][0])
			var img := _img(ENV + str(d["file"]))
			var w := float(img.get_width()) if img else 0.0
			var hot: String = {"routes_case": "timetable_case", "column_bared": "column_s2", "drawer_s8_open": "drawer_s8",
				"capsule_open": "tube_station", "form_counter": "registrar_counter"}[nm]
			kit.ok(x - 24.0 <= HOTSPOTS[hot] and HOTSPOTS[hot] <= x + w + 24.0, "%s changes the object at %s" % [nm, hot])
	# a story patch that overlaps an insignia site is drawn above it (the change covers the old state)
	for d in m.get("decals", []):
		if not PATCHES.has(str(d.get("name"))):
			continue
		var r1 := _rect_of(d)
		for s in m.get("decals", []):
			if s.has("hist_variant") and r1.intersects(_rect_of(s)):
				kit.ok(float(d.get("z", 0)) > float(s.get("z", 0)), "%s lies above the insignia site %s" % [d["name"], s["name"]])
	return true


func _rect_of(e: Dictionary) -> Rect2:
	var img := _img(ENV + str(e.get("file", "")))
	var fr := maxi(1, int(e.get("frames", 1)))
	var w := float(img.get_width()) / fr if img else 0.0
	var h := float(img.get_height()) if img else 0.0
	return Rect2(float(e["pos"][0]), float(e["pos"][1]), w, h)


func _fg_clear() -> bool:
	for L in m.get("layers", []):
		var nm := str(L.get("name"))
		if not nm.begins_with("fg_"):
			continue
		var fg := _img(ENV + str(L["file"]))
		if not kit.ok(fg != null, nm + " loads"):
			continue
		var sid := str(L.get("scene", A))
		var z: Array = ZONES[sid]
		var par := float(L.get("parallax", [1.25, 1])[0])
		var all := {}
		for k in HOTSPOTS:
			if SCENE_OF_HOTSPOT[k] == sid:
				all[k] = HOTSPOTS[k]
		for k in SPAWNS:
			if (SPAWNS[k] < 846) == (sid == A):
				all[k] = SPAWNS[k]
		for k in all:
			var hx := float(all[k])
			var cam := clampf(hx - 320.0, float(z[0]), float(z[0]) + float(z[2]) - 640.0)
			var sx := hx - cam                                  # screen x of the hotspot
			var fx := int(round(sx - float(L["pos"][0]) + par * cam))
			var covered := false
			for y in range(maxi(0, 250 - int(L["pos"][1])), mini(fg.get_height(), 306 - int(L["pos"][1]))):
				for x in range(maxi(0, fx - 12), mini(fg.get_width(), fx + 13)):
					if fg.get_pixel(x, y).a > 0.0:
						covered = true
			kit.ok(not covered, "%s keeps %s clear (camera centred on it)" % [nm, k])
	return true


# ------------------------------------------------------------------ level script
func _mount(scene_id: String) -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("level_id", scene_id)               # set before _ready: the scene filter is decided at load
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	return lvl


func _state(lvl: Node, done := {}) -> void:
	lvl.set("done_override", done)
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
		kit.eq((lvl.get_script() as Script).resource_path, SCRIPT, "%s: the shell runs annex_level.gd" % sid)
		kit.ok(lvl is Level, "annex_level extends Level")
		kit.eq(lvl.get_camera_bounds(), Rect2(ZONES[sid][0], ZONES[sid][1], ZONES[sid][2], ZONES[sid][3]), "%s: camera clamped to its zone" % sid)
		_state(lvl)
		kit.eq(lvl.call("look"), "loop" if sid == A else "annex", "%s plays its look" % sid)
		kit.eq(str(lvl.get("grade_preset")), "annex_loop" if sid == A else "annex", "%s: grade of the scene" % sid)
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
		kit.eq(lvl.call("blocker_on", "shaft_wall"), true, "%s: the shaft wall always stands" % sid)
		for nd in ["MartaTram", "Registrar", "GuardAnnex"]:
			kit.ok(lvl.get_node_or_null("Playfield/" + nd) != null, "%s: NPC node %s kept" % [sid, nd])
		lvl.free()
	return true


func _patches() -> bool:
	for nm in PATCHES:
		var sid: String = PATCHES[nm][0]
		var obj: String = PATCHES[nm][1]
		var lvl := _mount(sid)
		_state(lvl, {})
		kit.eq(lvl.call("is_shown", nm), false, "%s hidden before %s" % [nm, obj])
		_state(lvl, {obj: true})
		kit.eq(lvl.call("is_shown", nm), true, "%s shown once %s is complete" % [nm, obj])
		lvl.free()
	return true


func _memory() -> bool:
	var lvl := _mount(B)
	lvl.set("done_override", null)
	lvl.set("memory_override", true)
	lvl.set("hidden_override", false)
	lvl.call("refresh", true)
	kit.eq(lvl.call("objective_done", "c4b_inspect_crates"), true, "memory of B: scene A's objectives count")
	kit.eq(lvl.call("objective_done", "c4d_inspect_drawer"), false, "memory of B: its own objectives start open")
	kit.eq(lvl.call("is_shown", "drawer_s8_open"), false, "memory of B: drawer Sued 8 closed again")
	lvl.free()
	return true


func _documents() -> bool:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(DOCS_JSON))
	if not kit.ok(parsed is Dictionary and parsed.get("documents") is Array, "berlin_annex_documents.json parses"):
		return false
	var lf = JSON.parse_string(FileAccess.get_file_as_string(ALT_LOCALE))
	var alt_strings: Dictionary = lf.get("strings", {}) if lf is Dictionary else {}
	kit.ok(not alt_strings.is_empty(), "de_env_berlin_annex.json parses")
	var items := {}
	var idata = JSON.parse_string(FileAccess.get_file_as_string("res://data/v3/items.json"))
	for it in idata.get("items", []):
		items[str(it["id"])] = it
	var by_item := {}
	for e in parsed["documents"]:
		by_item[str(e.get("item_id"))] = e
	for item in DOCUMENTS:
		var e: Dictionary = by_item.get(item, {})
		if not kit.ok(not e.is_empty(), "%s has a document entry" % item):
			continue
		kit.eq(str(e.get("id")), DOCUMENTS[item], "%s: document id" % item)
		var png := "res://assets/ui/documents/%s.png" % DOCUMENTS[item]
		var img := _img(png)
		if kit.ok(img != null, "%s: InspectView loads %s" % [item, png]):
			kit.eq(_ints(e.get("size")), [img.get_width(), img.get_height()], "%s: size recorded" % item)
			kit.ok(img.get_width() * 3 <= 1060 and img.get_height() * 3 <= 760, "%s: fits the inspect view at 3x (MAX_DOC)" % item)
		kit.ok(items.has(item), "%s is a C4 item" % item)
		if items.has(item):
			kit.eq(str(e.get("title_key")), str(items[item].get("name_key")), "%s: title key = item name key" % item)
		kit.eq(UIKit.doc_for_item(item), DOCUMENTS[item], "%s: UIKit.doc_for_item finds it" % item)
		var marks: Dictionary = e.get("marks", {})
		kit.ok(marks.size() >= 2, "%s: the legible key lines are marked" % item)
		# round-9 fix compl-10: every close-up has its German caption line (the alt text under the art)
		var alt := str(e.get("alt_key", ""))
		kit.eq(alt, "doc.%s.alt" % DOCUMENTS[item], "%s: alt key" % item)
		kit.ok(alt_strings.has(alt), "%s: %s written in de_env_berlin_annex.json" % [item, alt])
		var txt := UIKit.doc_alt_text(item)
		kit.ok(txt.length() > 40 and (txt.ends_with(".") or txt.ends_with(".“")), "%s: caption reads as a sentence" % item)
		kit.ok(not txt.contains("\"") and not txt.contains("'") and not txt.contains(" - ") and not txt.contains("..."),
			"%s: German typography („…“, –, …)" % item)
		kit.ok(txt.count("„") == txt.count("“"), "%s: balanced German quotes" % item)
		kit.ok(txt.length() <= 340, "%s: caption length %d (a few lines under the art)" % [item, txt.length()])
	# the card names the wagon and the time the whole chapter turns on
	var card: Dictionary = by_item.get("ev_c4_card_de", {}).get("marks", {})
	kit.eq([card.get("number", {}).get("text"), card.get("wagon", {}).get("text"), card.get("time", {}).get("text")],
		["NR. 0417", "KURIERWAGEN C-17/45", "DI 18.2., 23.40"], "card 0417: number, wagon and departure legible")
	var plan: Dictionary = by_item.get("ev_c4_annex_plan", {}).get("marks", {})
	kit.eq(plan.get("signed", {}).get("text"), "GEZ. K. ADLER", "the plan is signed by Konrad")
	var bm: Dictionary = by_item.get("ev_c4_route_board", {}).get("marks", {})
	kit.eq([bm.get("title", {}).get("text"), bm.get("okt", {}).get("text"), bm.get("dez", {}).get("text"),
		bm.get("jan", {}).get("text"), bm.get("north", {}).get("text")], ["LINIE 74", "OKT.", "DEZ.", "JAN.", "N"],
		"the route board: line 74, the three detours and the north arrow legible")
	kit.ok(UIKit.doc_alt_text("ev_c4_route_board") != "", "the route board has an alt text")
	return true


# ------------------------------------------------------------------ round-9 art fixes (art-01 / art-05 / art-06)
func _art_fixes_r9() -> bool:
	var loop := _img(ENV + "loop.png")
	# art-01: the notice of No. 9 is on the boarded door (ungated, neutral), the seal strip still shows beside it
	var nd: Dictionary = {}
	for d in m.get("decals", []):
		if str(d.get("name")) == "notice_9":
			nd = d
	if kit.ok(not nd.is_empty(), "decal notice_9 exists"):
		kit.eq(str(nd.get("scene")), A, "notice_9 belongs to the street")
		kit.ok(not nd.has("after") and not nd.has("until") and not nd.has("choice"), "notice_9 is always there")
		kit.ok(not nd.has("hist_variant"), "notice_9 is neutral (no insignia site)")
		var r := _rect_of(nd)
		kit.ok(r.position.x >= 100.0 and r.end.x <= 136.0 and r.position.y >= 236.0 and r.end.y <= 288.0,
			"notice_9 %s lies on the door of No. 9 (x 100-136, y 236-288)" % r)
		var ni := _img(ENV + str(nd.get("file")))
		if ni != null and loop != null:
			var diff := 0
			for y in ni.get_height():
				for x in ni.get_width():
					if ni.get_pixel(x, y) != loop.get_pixel(int(r.position.x) + x, int(r.position.y) + y):
						diff += 1
			kit.ok(diff >= 80, "notice_9 adds the sheet to the door (%d px differ)" % diff)
			kit.ok(r.end.x < 130.0, "the seal strip stays visible right of the notice")
	# art-05: the poster „Berlin baut“ on the shelter's side wall (the find exp_shelter_poster looks at it)
	if loop != null:
		var red := 0
		for y in range(237, 240):
			for x in range(316, 328):
				var c := loop.get_pixel(x, y)
				if c.r > c.g + 0.12 and c.r > c.b + 0.12:
					red += 1
		kit.ok(red >= 18, "the poster's red title band is painted at x 316-327, y 237 (%d red px)" % red)
	var eh = JSON.parse_string(FileAccess.get_file_as_string(ENV + "explore_hotspots.json"))
	if eh is Dictionary:
		kit.ok(not JSON.stringify(eh.get("info", {})).contains("NOT YET PAINTED"), "every explore spot points at painted art")
	# art-06: the counter is a y-sorted prop; Fengler stands behind it, the player passes in front
	var pr: Dictionary = {}
	for p in m.get("props", []):
		if str(p.get("name")) == "counter_front":
			pr = p
	if not kit.ok(not pr.is_empty(), "prop counter_front exists"):
		return true
	kit.eq(str(pr.get("scene")), B, "counter_front belongs to the annex")
	var by := float(pr.get("base_y", 0))
	kit.ok(by > 276.0 and by < 296.0, "counter_front base_y %.0f lies between Fengler's feet (276) and the walk band (296)" % by)
	var pi := _img(ENV + str(pr.get("file")))
	var an := _img(ENV + "annex.png")
	if kit.ok(pi != null and an != null, "counter_front and annex.png load"):
		var px := int(pr["pos"][0])
		var py := int(pr["pos"][1])
		kit.ok(px <= 1652 and px + pi.get_width() >= 1770 and py <= 252 and py + pi.get_height() >= 286,
			"counter_front covers the counter (x 1650-1772, y 250-288)")
		kit.ok(pi.detect_alpha() != Image.ALPHA_BLEND, "counter_front: binary alpha")
		var bad := 0
		var opaque := 0
		for y in pi.get_height():
			for x in pi.get_width():
				var c := pi.get_pixel(x, y)
				if c.a > 0.5:
					opaque += 1
					if c != an.get_pixel(px - 846 + x, py + y):
						bad += 1
		kit.ok(opaque > 3000, "counter_front is the counter body (%d px)" % opaque)
		kit.eq(bad, 0, "counter_front is an exact cut of annex.png")
		# the form decal (after c4d_talk_registrar) lies under the prop: its sheet must stay uncovered
		for d in m.get("decals", []):
			if str(d.get("name")) == "form_counter":
				var fx := int(d["pos"][0]) + 6 - px
				var fy := int(d["pos"][1]) + 5 - py
				if fx >= 0 and fy >= 0 and fx < pi.get_width() and fy < pi.get_height():
					kit.ok(pi.get_pixel(fx, fy).a < 0.5, "counter_front leaves the form on the counter visible")
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	var reg: Node = lvl.get_node_or_null("Playfield/Registrar")
	if kit.ok(reg != null, "the level has the Registrar"):
		var hs: Array = m.get("hotspots", {}).get("registrar_counter", [0, 0])
		var feet: Vector2 = Vector2(float(hs[0]), float(hs[1])) + (reg.get("hotspot_offset") as Vector2)
		kit.eq(feet, Vector2(1734, 276), "Fengler's feet behind the counter")
		kit.ok(feet.y < by, "Fengler sorts behind counter_front")
		# round-9 fix: he works while he waits -- the stamping row of his sheet (hand up over the counter top, down)
		kit.eq(str(reg.get("idle_anim")), "work_side", "Fengler stamps cards at the counter (idle_anim work_side)")
		var sheet = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/registrar/sheet.json"))
		kit.ok(sheet is Dictionary and (sheet.get("anims", {}) as Dictionary).has("work_side"), "the registrar sheet has the work_side row")
	lvl.free()
	return true


## art-11: the hidden find „Eine Karte steht hoch“ looks at drawer Süd 3 -- painted a finger's width open (a dark slit
## above its front) with Brandt's card standing up over the bank's top; the find's stand and focus are on Süd 3.
func _drawer_s3() -> bool:
	var eh = JSON.parse_string(FileAccess.get_file_as_string(ENV + "explore_hotspots.json"))
	var inf: Dictionary = eh.get("info", {}).get("exp_brandt_card", {}) if eh is Dictionary else {}
	var spot: Array = eh.get("hotspots", {}).get("exp_brandt_card", []) if eh is Dictionary else []
	if kit.ok(not inf.is_empty() and spot.size() == 2, "exp_brandt_card has a spot and an art contract"):
		var st: Array = inf.get("stand", [])
		var fc: Array = inf.get("focus", [])
		kit.eq(_ints(spot), _ints(st), "the spot is the contract's stand")
		kit.ok(float(st[0]) >= DRAWER_S3[0] and float(st[0]) <= DRAWER_S3[1], "the stand (x %d) is in front of Süd 3" % int(st[0]))
		kit.ok(float(fc[0]) >= DRAWER_S3[0] and float(fc[0]) <= DRAWER_S3[1] and float(fc[1]) >= 228.0 and float(fc[1]) <= 244.0,
			"the focus %s is the card over Süd 3" % [fc])
	var an := _img(ENV + "annex.png")
	if not kit.ok(an != null, "annex.png loads"):
		return true
	var bright := func(x0: int, x1: int, y0: int, y1: int) -> int:
		var n := 0
		for y in range(y0, y1 + 1):
			for x in range(x0, x1 + 1):
				if an.get_pixel(x - 846, y).get_luminance() > 0.5:
					n += 1
		return n
	var card: int = bright.call(DRAWER_S3[0] + 3, DRAWER_S3[1] - 4, 232, 237)
	var none: int = bright.call(DRAWER_S4[0] + 3, DRAWER_S4[1] - 4, 232, 237)
	kit.ok(card >= 30 and none <= 2, "a card stands up over Süd 3 (%d light px), none over Süd 4 (%d)" % [card, none])
	var slit := 0.0
	var face := 0.0
	for x in [DRAWER_S3[0] + 1, DRAWER_S3[0] + 2, DRAWER_S3[1] - 3, DRAWER_S3[1] - 2]:
		slit = maxf(slit, an.get_pixel(x - 846, 240).get_luminance())
	for x in range(DRAWER_S4[0] + 1, DRAWER_S4[1] - 1):
		face += an.get_pixel(x - 846, 240).get_luminance() / float(DRAWER_S4[1] - DRAWER_S4[0] - 2)
	kit.ok(slit < 0.1 and face > 0.15, "Süd 3 stands open: a dark slit above its front (%.2f), Süd 4 closed (%.2f)" % [slit, face])
	return true
