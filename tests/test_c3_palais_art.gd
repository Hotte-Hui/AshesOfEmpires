extends RefCounted
## The Palais der Kommission art (L_C3_Hall, assets/environments/veltrava_hall, tools/pixelgen/env_veltrava_hall*):
## the ambient-life decals (looping figure strips and small touches, env_veltrava_hall_life.py) and the art
## contract the story relies on.
##  * every decal file exists, its width is a whole number of frames, its normal / emission strips match it,
##    the strips are binary-alpha pixel art (coded texel material, no blending), the target layer exists
##  * figures in the Playfield stand behind the walk band (actors always pass in front of them) and never on
##    a story NPC's spot or a story hotspot; booth / landing figures stay inside their booth / on the landing
##  * the historical-insignia sites keep their neutral + _hist pair (§12.4); no life strip has a _hist twin
##    (nobody in the palais wears a regime insignia)
##  * every exported light sits inside the world and has a unique name

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/veltrava_hall/"
const LEVEL := "res://scenes/levels/L_C3_Hall.tscn"
const STORY_HOTSPOTS := ["kessler", "seating", "booth_log", "protocol_table", "booth_2", "alexei_meet"]
## NPC feet = hotspot + hotspot_offset in L_C3_Hall.tscn (story NPCs)
const NPC_FEET := {"kessler": 316, "elena": 353, "voronova": 700, "typist": 1134, "journalist": 574, "alexei": 1718}
const EXPECTED_LIFE := ["garderobiere", "cleaner", "landing_pair", "waiter", "interp_1", "interp_3", "saal_life",
	"door_flash", "pigeon", "clock_vestibule", "clock_corridor"]

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var txt := FileAccess.get_file_as_string(ENV + "scene.json")
	var parsed = JSON.parse_string(txt)
	if not kit.ok(parsed is Dictionary, "veltrava_hall/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("decal_files_and_strips", _decal_files)
	kit.run_case("life_figures_placed_off_the_story", _placement)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("lights_valid", _lights)
	kit.cleanup()
	return kit.failures


func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	return Image.load_from_file(ProjectSettings.globalize_path(path))


func _decals() -> Array:
	var out: Array = []
	for d in m.get("decals", []):
		if d is Dictionary:
			out.append(d)
	return out


func _decal_files() -> bool:
	var names := {}
	var layer_names := {}
	for L in m.get("layers", []):
		layer_names[str(L.get("name", ""))] = true
	for d in _decals():
		names[str(d.get("name", ""))] = true
	for want in EXPECTED_LIFE:
		kit.ok(names.has(want), "life decal %s present in scene.json" % want)
	for d in _decals():
		var nm := str(d.get("name", ""))
		var path: String = ENV + str(d.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s: file %s exists" % [nm, path]):
			continue
		var frames := int(d.get("frames", 1))
		kit.ok(frames >= 1 and img.get_width() % frames == 0, "%s: width %d is a whole number of %d frames" % [nm, img.get_width(), frames])
		kit.ok(img.get_width() <= 16384 and img.get_height() <= 256, "%s: strip size %s within texture limits" % [nm, img.get_size()])
		kit.ok(float(d.get("fps", 0)) > 0.0, "%s: fps > 0" % nm)
		kit.ok(img.detect_alpha() != Image.ALPHA_BLEND, "%s: binary alpha (coded texel material, no blending)" % nm)
		for suffix in (["_n"] if bool(d.get("normal", false)) else []) + (["_e"] if bool(d.get("emission", false)) else []):
			var mp: String = path.get_basename() + suffix + ".png"
			var mi := _img(mp)
			if kit.ok(mi != null, "%s: map %s exists" % [nm, mp]):
				kit.eq(mi.get_size(), img.get_size(), "%s: %s strip matches the diffuse strip" % [nm, suffix])
		var on := str(d.get("layer", ""))
		kit.ok(on == "" or on == "playfield" or layer_names.has(on), "%s: target layer '%s' exists" % [nm, on])
		kit.ok(not FileAccess.file_exists(path.get_basename() + "_hist.png"), "%s: no historical-insignia twin (nobody in the palais wears one)" % nm)
		var pos: Array = d.get("pos", [0, 0])
		kit.ok(pos.size() == 2, "%s: pos is [x, y]" % nm)
	return true


func _placement() -> bool:
	var walk_top := 1e9
	for p in m.get("walkable", []):
		walk_top = minf(walk_top, float(p[1]))
	var hs: Dictionary = m.get("hotspots", {})
	for d in _decals():
		var nm := str(d.get("name", ""))
		var img := _img(ENV + str(d.get("file", "")))
		if img == null:
			continue
		var fw := img.get_width() / maxi(1, int(d.get("frames", 1)))
		var x0 := float(d["pos"][0])
		var x1 := x0 + fw
		if str(d.get("layer", "")) == "playfield":
			kit.ok(d.has("base_y") and float(d["base_y"]) < walk_top, "%s: base_y %s behind the walk band (top %s)" % [nm, d.get("base_y"), walk_top])
			for npc in NPC_FEET:
				var fx := float(NPC_FEET[npc])
				kit.ok(fx + 6 <= x0 + 2 or fx - 6 >= x1 - 2, "%s (x %d..%d) does not stand on %s's spot (x %d)" % [nm, x0, x1, npc, fx])
			for h in STORY_HOTSPOTS:
				if hs.has(h):
					var hx := float(hs[h][0])
					kit.ok(hx < x0 or hx > x1, "%s (x %d..%d) leaves story hotspot %s (x %d) free" % [nm, x0, x1, h, hx])
	# booth interpreters stay inside booths 1 / 3 (x ranges of the booths), the landing group on the landing
	var booths := {"interp_1": [1556, 1616], "interp_3": [1688, 1748]}
	for d in _decals():
		var nm := str(d.get("name", ""))
		if booths.has(nm):
			var img := _img(ENV + str(d.get("file", "")))
			if img:
				var fw := img.get_width() / maxi(1, int(d.get("frames", 1)))
				var cx := float(d["pos"][0]) + fw / 2.0
				kit.ok(cx > booths[nm][0] and cx < booths[nm][1], "%s centred inside its booth (x %d)" % [nm, cx])
				kit.ok(not (nm == "interp_3" and absf(cx - NPC_FEET["alexei"]) < 8.0), "interp_3 not directly behind Alexei")
		if nm == "landing_pair":
			kit.ok(float(d["pos"][0]) >= 690 and float(d["pos"][0]) < 760, "landing group on the stair landing")
	return true


func _insignia() -> bool:
	for p in m.get("props", []):
		var nm := str(p.get("name", ""))
		if nm in ["flag_ussr", "flag_reich"]:
			kit.ok(p.has("hist_variant") and FileAccess.file_exists(ENV + str(p["hist_variant"])), "%s keeps its _hist variant" % nm)
			kit.ok(FileAccess.file_exists(ENV + str(p.get("file", ""))), "%s keeps its neutral file" % nm)
	var far_ok := false
	for L in m.get("layers", []):
		if str(L.get("name", "")) == "saal_far":
			far_ok = L.has("hist_variant") and FileAccess.file_exists(ENV + str(L["hist_variant"]))
	kit.ok(far_ok, "saal_far keeps its _hist variant (the Saal flags)")
	return true


func _lights() -> bool:
	var seen := {}
	var ws: Array = m.get("world_size", [1920, 360])
	for li in m.get("lights", []):
		var nm := str(li.get("name", ""))
		kit.ok(not seen.has(nm), "light %s unique" % nm)
		seen[nm] = true
		var p: Array = li.get("pos", [0, 0])
		kit.ok(float(p[0]) >= 0 and float(p[0]) <= float(ws[0]) and float(p[1]) >= 0 and float(p[1]) <= float(ws[1]), "light %s inside the world" % nm)
		kit.ok(float(li.get("energy", 0)) > 0.0 and float(li.get("radius", 0)) > 0.0, "light %s has energy and radius" % nm)
	return true
