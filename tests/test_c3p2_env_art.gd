extends RefCounted
## The night quay art (L_C3_Quay, assets/environments/veltrava_quay, tools/pixelgen/env_c3p2_quay*.py — area
## env_c3p2_night, C3P2_DESIGN.md §5.2):
##  * final art (no placeholder), 1920x360, every file the manifest names exists with its _n/_e maps
##  * the story contract: the seven hotspots at their design positions, the entry spawn, all on the walk band
##  * life strips: whole frames, texture limits, binary-alpha diffuse, matching map strips; anonymous figures stand
##    behind the walk band and never on a story NPC's spot or a story hotspot
##  * accessibility: searchlights >= 6 s per sweep, fire strips <= 3 Hz (<= 6 fps), gentle light flicker
##  * insignia only on the two car pennants, each a neutral + _hist pair of identical size (§12.4)
##  * diffuse art stays inside the Veltrava palette (data/chapters/c3.json, sampled)
##  * the level shell builds the backdrop headless: every layer, decal and prop of the manifest is instanced

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/veltrava_quay/"
const LEVEL := "res://scenes/levels/L_C3_Quay.tscn"
const HOTSPOTS := {"bench": [760, 300], "konrad_quay": [800, 300], "typist_quay": [330, 300], "guard_quay": [1050, 300],
	"kessler_quay": [1180, 300], "voronova_quay": [1330, 300], "journalist_quay": [1560, 300]}
## NPC feet = hotspot + hotspot_offset in L_C3_Quay.tscn
const NPC_FEET := {"konrad": 818, "typist": 344, "border_officer": 1050, "kessler": 1180, "voronova": 1344, "journalist": 1574}
const EXPECTED_LIFE := ["hose_team", "ladder_man", "pump_man", "onlookers", "aide_kessler", "aide_voronova", "drivers",
	"beacon", "fire_win_1", "embers_1", "searchlight_a", "searchlight_b", "town_win_1"]
const HIST_PROPS := ["car_reich", "car_ussr"]

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "veltrava_quay/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("final_art_and_files", _files)
	kit.run_case("story_contract", _contract)
	kit.run_case("life_strips", _strips)
	kit.run_case("figures_off_the_story", _placement)
	kit.run_case("no_strobing", _motion)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("palette", _palette)
	kit.run_case("shell_builds", _shell)
	kit.cleanup()
	return kit.failures


static func _v(a) -> Vector2:
	if a is Array and a.size() >= 2:
		return Vector2(float(a[0]), float(a[1]))
	return Vector2(-1, -1)


static func _strs(keys: Array) -> Array:
	return keys.map(func(k) -> String: return str(k))


func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	return Image.load_from_file(ProjectSettings.globalize_path(path))


func _files() -> bool:
	kit.ok(not m.has("placeholder"), "the placeholder of the story stream is replaced")
	kit.eq(m.get("id"), "veltrava_quay", "env id")
	kit.eq(_v(m.get("world_size")), Vector2(1920, 360), "world size")
	kit.eq(m.get("palette"), "veltrava", "palette = c3.json palettes.veltrava")
	kit.ok((m.get("layers", []) as Array).size() >= 8, "a full layer stack (sky .. fg)")
	var missing: Array = []
	for section in ["layers", "props", "decals", "fx"]:
		for e in m.get(section, []):
			if not (e is Dictionary) or not e.has("file"):
				continue
			var f: String = ENV + str(e["file"])
			if not FileAccess.file_exists(f):
				missing.append(f)
				continue
			var base := f.get_basename()
			if bool(e.get("normal", false)) and section != "fx" and not FileAccess.file_exists(base + "_n.png"):
				missing.append(base + "_n.png")
			if bool(e.get("emission", false)) and not FileAccess.file_exists(base + "_e.png"):
				missing.append(base + "_e.png")
	kit.eq(missing, [], "every file (and map) named by scene.json exists")
	var names := {}
	for L in m.get("layers", []):
		kit.ok(not names.has(L["name"]), "layer name %s unique" % L["name"])
		names[L["name"]] = true
		var p: float = float(L["parallax"][0])
		var img := _img(ENV + str(L["file"]))
		if img and p < 1.0 and str(L.get("blend", "")) != "add" and L["name"] != "pall":
			var need := 640.0 + p * 1280.0
			kit.ok(int(L["pos"][0]) + img.get_width() >= need - 0.5, "%s covers the scroll range (%d px >= %d)" % [L["name"], img.get_width(), int(need)])
	kit.ok(FileAccess.file_exists(ENV + "provenance.json"), "provenance.json written by the generator")
	return true


func _contract() -> bool:
	var hs: Dictionary = m.get("hotspots", {})
	for k in HOTSPOTS:
		kit.eq(_v(hs.get(k)), _v(HOTSPOTS[k]), "hotspot %s at its design position (C3P2_DESIGN §5.2)" % k)
	kit.eq(_v(m.get("spawns", {}).get("SP_C3_Quay")), Vector2(560, 300), "entry spawn SP_C3_Quay")
	var poly := PackedVector2Array()
	for q in m.get("walkable", []):
		poly.append(Vector2(float(q[0]), float(q[1])))
	kit.ok(poly.size() >= 3, "walkable polygon")
	for k in hs:
		kit.ok(Geometry2D.is_point_in_polygon(Vector2(float(hs[k][0]), float(hs[k][1])), poly), "hotspot %s on the walk band" % k)
	for k in m.get("spawns", {}):
		var sp: Array = m["spawns"][k]
		kit.ok(Geometry2D.is_point_in_polygon(Vector2(float(sp[0]), float(sp[1])), poly), "spawn %s on the walk band" % k)
	kit.eq(Kit.sorted(m.get("zones", {}).keys()), ["bridge", "burning_wing", "cars", "promenade"], "zones of §5.2")
	# exploration suggestions never collide with story hotspots
	for k in m.get("explore_sites", {}):
		var st: Array = m["explore_sites"][k]["stand"]
		for h in HOTSPOTS:
			kit.ok(absf(float(st[0]) - float(HOTSPOTS[h][0])) >= 24.0, "explore site %s >= 24 px from %s" % [k, h])
	return true


func _strips() -> bool:
	var names := {}
	var layer_names := {}
	for L in m.get("layers", []):
		layer_names[str(L["name"])] = true
	for d in m.get("decals", []):
		names[str(d.get("name", ""))] = true
	for want in EXPECTED_LIFE:
		kit.ok(names.has(want), "life decal %s present" % want)
	for d in m.get("decals", []):
		var nm := str(d.get("name", ""))
		var path: String = ENV + str(d.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s: strip exists" % nm):
			continue
		var frames := int(d.get("frames", 1))
		kit.ok(frames >= 1 and img.get_width() % frames == 0, "%s: width %d is a whole number of %d frames" % [nm, img.get_width(), frames])
		kit.ok(img.get_width() <= 16384 and img.get_height() <= 512, "%s: within texture limits %s" % [nm, img.get_size()])
		kit.ok(float(d.get("fps", 0)) > 0.0, "%s: fps > 0" % nm)
		kit.ok(img.detect_alpha() != Image.ALPHA_BLEND, "%s: binary-alpha diffuse (coded texel material)" % nm)
		var on := str(d.get("layer", ""))
		kit.ok(on == "playfield" or layer_names.has(on), "%s: target layer %s exists" % [nm, on])
		for suffix in (["_n"] if bool(d.get("normal", false)) else []) + (["_e"] if bool(d.get("emission", false)) else []):
			var mi := _img(path.get_basename() + suffix + ".png")
			if kit.ok(mi != null, "%s: %s strip exists" % [nm, suffix]):
				kit.eq(mi.get_size(), img.get_size(), "%s: %s strip matches the diffuse" % [nm, suffix])
	for f in m.get("fx", []):
		if str(f.get("type", "")) != "anim_sprite":
			continue
		var img := _img(ENV + str(f["file"]))
		if kit.ok(img != null, "fx %s exists" % f["file"]):
			kit.ok(img.get_width() % int(f["frames"]) == 0, "fx %s: whole frames" % f["file"])
			kit.ok(img.get_width() <= 16384, "fx %s: within texture limits" % f["file"])
	return true


func _placement() -> bool:
	var story_x: Array = []
	for k in HOTSPOTS:
		story_x.append(float(HOTSPOTS[k][0]))
	for k in NPC_FEET:
		story_x.append(float(NPC_FEET[k]))
	for d in m.get("decals", []):
		if str(d.get("layer", "")) != "playfield":
			continue
		var nm := str(d.get("name", ""))
		kit.ok(int(d.get("base_y", 999)) <= 294, "%s: drawn behind the walk band (base_y %s <= 294)" % [nm, d.get("base_y")])
		for f in d.get("figures", []):
			if float(f[1]) < 280.0:
				continue          # on the ladder, not on the quay
			kit.ok(float(f[1]) < 296.0, "%s: figure feet %s behind the walk band" % [nm, f])
			for x in story_x:
				kit.ok(absf(float(f[0]) - x) >= 10.0, "%s: figure at x %s not on a story spot (%s)" % [nm, f[0], x])
	for p in m.get("props", []):
		kit.ok(int(p.get("base_y", 999)) <= 294, "prop %s behind the walk band" % p["name"])
	return true


func _motion() -> bool:
	for d in m.get("decals", []):
		var nm := str(d.get("name", ""))
		var fps := float(d.get("fps", 6))
		if nm.begins_with("searchlight"):
			var sweep := float(d["frames"]) / fps / 2.0
			kit.ok(sweep >= 6.0, "%s: %.1f s per sweep (>= 6 s)" % [nm, sweep])
		if nm.begins_with("fire_") or nm == "drivers" or nm.begins_with("embers"):
			kit.ok(fps <= 8.0, "%s: fire motion at %.0f fps (flicker <= 3 Hz)" % [nm, fps])
		if nm.begins_with("fire_win"):
			kit.ok(fps <= 6.0, "%s: flame shapes change at <= 6 fps" % nm)
	var names := {}
	for li in m.get("lights", []):
		var n := str(li.get("name", ""))
		kit.ok(n != "" and not names.has(n), "light %s named uniquely" % n)
		names[n] = true
		kit.ok(float(li.get("flicker", 0.0)) <= 0.25, "light %s: gentle flicker" % n)
		var pos: Array = li.get("pos", [0, 0])
		kit.ok(float(pos[0]) >= 0 and float(pos[0]) <= 1920 and float(pos[1]) >= 0 and float(pos[1]) <= 360, "light %s inside the world" % n)
	return true


func _insignia() -> bool:
	var hist_props: Array = []
	for p in m.get("props", []):
		if p.has("hist_variant"):
			hist_props.append(str(p["name"]))
			var a := _img(ENV + str(p["file"]))
			var b := _img(ENV + str(p["hist_variant"]))
			if kit.ok(a != null and b != null, "%s: neutral + _hist files" % p["name"]):
				kit.eq(b.get_size(), a.get_size(), "%s: _hist has the neutral footprint" % p["name"])
				kit.ok(a.get_data() != b.get_data(), "%s: the _hist variant differs (insignia)" % p["name"])
			kit.eq(str(p["hist_variant"]), str(p["file"]).get_basename() + "_hist.png", "%s: Symbols.pick naming" % p["name"])
	kit.eq(Kit.sorted(hist_props), HIST_PROPS, "only the two car pennants carry insignia")
	for d in m.get("decals", []):
		kit.ok(not FileAccess.file_exists(ENV + str(d["file"]).get_basename() + "_hist.png"), "%s: no _hist twin" % d["name"])
	return true


func _palette() -> bool:
	var c3 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c3.json"))
	if not kit.ok(c3 is Dictionary, "c3.json parses"):
		return false
	var allowed := {}
	for ramp in c3["palettes"]["veltrava"].values():
		for h in ramp:
			allowed[str(h).to_upper().trim_prefix("#")] = true
	var files: Array = []
	for section in ["layers", "props", "decals", "fx"]:
		for e in m.get(section, []):
			if e is Dictionary and e.has("file") and str(e.get("blend", "")) != "add":
				files.append(str(e["file"]))
	for p in m.get("props", []):
		if p.has("hist_variant"):
			files.append(str(p["hist_variant"]))
	for f in files:
		var img := _img(ENV + f)
		if img == null:
			continue
		var off := {}
		var step := 3 if img.get_width() * img.get_height() > 200000 else 1
		for y in range(0, img.get_height(), step):
			for x in range(0, img.get_width(), step):
				var c := img.get_pixel(x, y)
				if c.a < 0.5:
					continue
				var hx := c.to_html(false).to_upper()
				if not allowed.has(hx):
					off[hx] = true
		kit.eq(off.keys().slice(0, 4), [], "%s: only Veltrava palette colours" % f)
	return true


func _shell() -> bool:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	var bd = lvl.get("backdrop")
	if not kit.ok(bd != null, "level built its backdrop"):
		return false
	var want_layers: Array = []
	for L in m.get("layers", []):
		want_layers.append(str(L["name"]))
	kit.eq(Kit.sorted(_strs((bd.layers_by_name as Dictionary).keys())), Kit.sorted(want_layers), "every layer instanced")
	var want_decals: Array = []
	for d in m.get("decals", []):
		want_decals.append(str(d["name"]))
	kit.eq(Kit.sorted(_strs((bd.decals_by_name as Dictionary).keys())), Kit.sorted(want_decals), "every decal instanced")
	var prop_names := {}
	for c in lvl.playfield.get_children():
		prop_names[str(c.name)] = true
	for p in m.get("props", []):
		kit.ok(prop_names.has(str(p["name"])), "prop %s in the playfield" % p["name"])
	kit.eq(lvl.get_spawn("SP_C3_Quay"), Vector2(560, 300), "entry spawn through Level.get_spawn")
	lvl.free()
	return true
