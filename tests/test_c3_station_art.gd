extends RefCounted
## Veltrava station art polish (L_C3_Station, owner env_veltrava_station; tools/pixelgen/env_veltrava_station*.py):
##  * the ambient actors declared by assets/environments/veltrava_station/scene.json exist and are complete
##    (pigeon flock at exp_pigeons, island walkers, the waiting tram, the viaduct train, window life, breath)
##  * every sprite strip has the frame geometry its actor script assumes
##  * the named decal hook `heater_leak_23` (side task "Wagen drei ist kalt") sits at the coupling hotspot
##  * insignia layers/props keep a neutral file + `_hist` twin of the same size (TECHNICAL_ARCHITECTURE §12.4)
##  * actor and prop sprites use only the 'veltrava' palette (data/chapters/c3.json)
##  * the station actors run headless: walkers walk inside their lane, the tram waits / leaves / comes back,
##    the pigeons tolerate a walking observer and fly up when somebody runs past, then come back

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/veltrava_station"
const SCN := "res://scenes/levels/veltrava_station/"

var kit: Kit
var man: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var txt := FileAccess.get_file_as_string(ENV + "/scene.json")
	var parsed = JSON.parse_string(txt)
	man = parsed if parsed is Dictionary else {}
	kit.run_case("manifest_actors_complete", _actors_complete)
	kit.run_case("strip_geometry", _strip_geometry)
	kit.run_case("heater_leak_decal_hook", _decal_hook)
	kit.run_case("insignia_neutral_and_hist", _insignia)
	kit.run_case("actor_and_prop_palette", _palette)
	kit.run_case("walkers_and_tram_run", _walkers_and_tram)
	kit.run_case("pigeons_watchable_then_flee", _pigeons)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
func _actors(scene_name: String) -> Array:
	var out: Array = []
	for a in man.get("actors", []):
		if a is Dictionary and str(a.get("scene", "")).ends_with("/" + scene_name):
			out.append(a)
	return out


static func _exists(path: String) -> bool:
	return ResourceLoader.exists(path) or FileAccess.file_exists(path)


func _walkable() -> PackedVector2Array:
	var poly := PackedVector2Array()
	for p in man.get("walkable", []):
		poly.append(Vector2(float(p[0]), float(p[1])))
	return poly


func _tex_size(path: String) -> Vector2i:
	var img := Image.load_from_file(ProjectSettings.globalize_path(path))
	return img.get_size() if img != null else Vector2i.ZERO


## Instances an actor scene like Level._spawn_actors (props set before _ready) under a mounted Node2D.
func _spawn(entry: Dictionary, holder: Node2D) -> Node2D:
	var node: Node2D = load(str(entry["scene"])).instantiate()
	node.position = Vector2(float(entry["pos"][0]), float(entry["pos"][1]))
	var props: Dictionary = entry.get("props", {})
	for k in props:
		node.set(k, props[k])
	holder.add_child(node)
	return node


# ------------------------------------------------------------------ cases
func _actors_complete() -> bool:
	if not kit.ok(not man.is_empty(), "scene.json parses"):
		return true
	var expect := {"StationPigeons.tscn": 1, "StationWalkers.tscn": 1, "StationTram.tscn": 1, "KarskTrain.tscn": 1,
		"KarskWindowLife.tscn": 1, "KarskBreath.tscn": 3}
	for scene_name in expect:
		kit.ok(_actors(scene_name).size() >= int(expect[scene_name]),
			"at least %d actor(s) %s in scene.json" % [expect[scene_name], scene_name])
	var missing: Array = []
	for a in man.get("actors", []):
		if not _exists(str(a.get("scene", ""))):
			missing.append(str(a.get("scene", "")))
		var props: Dictionary = a.get("props", {})
		for k in props:
			var v = props[k]
			var paths: Array = []
			if v is String and str(v).ends_with(".png"):
				paths.append(v)
			elif v is Array:
				for x in v:
					if x is String and str(x).ends_with(".png"):
						paths.append(x)
					elif x is Dictionary and x.has("file"):
						paths.append(x["file"])
			for p in paths:
				if not _exists(str(p)):
					missing.append(str(p))
	kit.eq(missing, [], "files named by the station actors that do not exist")
	# the pigeons stand where the find is (exp_pigeons) and on the walkable platform
	var poly := _walkable()
	var pg: Array = _actors("StationPigeons.tscn")
	if pg.size() > 0:
		var hs: Array = man.get("hotspots", {}).get("exp_pigeons", [0, 0])
		for sp in pg[0]["props"]["spots"]:
			var v := Vector2(float(sp[0]), float(sp[1]))
			kit.ok(Geometry2D.is_point_in_polygon(v, poly), "pigeon spot %s inside the walkable platform" % v)
			kit.ok(absf(v.x - float(hs[0])) < 40.0 and v.y < float(hs[1]), "pigeon spot %s next to exp_pigeons %s" % [v, hs])
	# the walkers' lane stays behind wagon 4 / the concourse at both ends (they never pop up in view)
	var wk: Array = _actors("StationWalkers.tscn")
	if wk.size() > 0:
		var span: Array = wk[0]["props"]["span"]
		kit.ok(float(span[0]) <= 700.0 and float(span[1]) >= 1310.0, "island lane %s spans the visible island" % [span])
		kit.ok((wk[0]["props"]["sheets"] as Array).size() >= 5, "at least five different people on the island")
	return true


func _strip_geometry() -> bool:
	var wk: Array = _actors("StationWalkers.tscn")
	if kit.ok(wk.size() > 0, "walkers actor present"):
		for s in wk[0]["props"]["sheets"]:
			var size := _tex_size(str(s["file"]))
			kit.eq(size.x, int(s["cell"][0]) * int(s["frames"]), "%s: width = cell x frames" % s["file"])
			kit.eq(size.y, int(s["cell"][1]), "%s: height = cell height" % s["file"])
	var pg: Array = _actors("StationPigeons.tscn")
	if pg.size() > 0:
		kit.eq(_tex_size(str(pg[0]["props"]["sprite"])), Vector2i(12 * 11, 10), "pigeon sheet = 11 frames of 12x10")
	var wl: Array = _actors("KarskWindowLife.tscn")
	if wl.size() > 0:
		kit.eq(_tex_size(str(wl[0]["props"]["sprite"])), Vector2i(16 * 4, 17), "window life strip = 4 frames of 16x17")
	var br: Array = _actors("KarskBreath.tscn")
	if br.size() > 0:
		kit.eq(_tex_size(str(br[0]["props"]["sprite"])), Vector2i(7 * 6, 7), "breath puff strip = 6 frames of 7x7")
	return true


func _decal_hook() -> bool:
	var found: Dictionary = {}
	for d in man.get("decals", []):
		if d is Dictionary and str(d.get("name", "")) == "heater_leak_23":
			found = d
	if not kit.ok(not found.is_empty(), "decal heater_leak_23 (steam leak between wagons 2 and 3) declared"):
		return true
	kit.ok(_exists(ENV + "/" + str(found["file"])), "heater_leak_23 file exists")
	kit.ok(int(found.get("frames", 1)) > 1, "heater_leak_23 is animated")
	# it hangs at the coupling the side task points at (explore_hotspots.json exp_task_coupling, if declared)
	var xh = JSON.parse_string(FileAccess.get_file_as_string(ENV + "/explore_hotspots.json"))
	var hs = xh.get("hotspots", {}).get("exp_task_coupling") if xh is Dictionary else null
	if hs is Array:
		var fw := 28.0
		var cx := float(found["pos"][0]) + fw * 0.3
		kit.ok(absf(cx - float(hs[0])) < 14.0, "steam leak x %.0f at the coupling hotspot x %s" % [cx, hs[0]])
	return true


func _insignia() -> bool:
	var n := 0
	for section in ["layers", "props"]:
		for e in man.get(section, []):
			if not (e is Dictionary) or not e.has("hist_variant"):
				continue
			n += 1
			var a := ENV + "/" + str(e["file"])
			var b := ENV + "/" + str(e["hist_variant"])
			if kit.ok(_exists(a) and _exists(b), "%s: neutral and _hist files exist" % e["name"]):
				var ia := Image.load_from_file(ProjectSettings.globalize_path(a))
				var ib := Image.load_from_file(ProjectSettings.globalize_path(b))
				kit.eq(ia.get_size(), ib.get_size(), "%s: neutral and _hist have the same size" % e["name"])
				kit.ok(ia.get_data() != ib.get_data(), "%s: the _hist variant differs from the neutral twin" % e["name"])
	kit.ok(n >= 3, "insignia sites with variants: pennants_reich, flag_ussr, flag_reich (%d)" % n)
	return true


func _palette() -> bool:
	var c3 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c3.json"))
	var pal := {}
	if c3 is Dictionary:
		var ramps: Dictionary = c3.get("palettes", {}).get("veltrava", {})
		for r in ramps:
			for h in ramps[r]:
				pal[str(h).to_upper().trim_prefix("#")] = true
	if not kit.ok(pal.size() >= 40, "veltrava palette read from data/chapters/c3.json (%d colours)" % pal.size()):
		return true
	var bad: Array = []
	for sub in ["actors", "props"]:
		var dir := DirAccess.open(ENV + "/" + sub)
		if dir == null:
			continue
		for f in dir.get_files():
			if not f.ends_with(".png") or f.ends_with("_n.png") or f.ends_with("_e.png"):
				continue
			var img := Image.load_from_file(ProjectSettings.globalize_path(ENV + "/" + sub + "/" + f))
			if img == null:
				bad.append(f + " (unreadable)")
				continue
			img.convert(Image.FORMAT_RGBA8)
			var data := img.get_data()
			var off := {}
			for i in range(0, data.size(), 4):
				if data[i + 3] == 0:
					continue
				var key := "%02X%02X%02X" % [data[i], data[i + 1], data[i + 2]]
				if not pal.has(key):
					off[key] = true
			if not off.is_empty():
				bad.append("%s %s" % [f, Kit.sorted(off.keys()).slice(0, 4)])
	kit.eq(bad, [], "actor/prop sprites with colours outside the veltrava palette")
	return true


func _walkers_and_tram() -> bool:
	var holder := Node2D.new()
	kit.mount(holder)
	var wk: Array = _actors("StationWalkers.tscn")
	var tr: Array = _actors("StationTram.tscn")
	if not (kit.ok(wk.size() > 0, "walkers declared") and kit.ok(tr.size() > 0, "tram declared")):
		return true
	var w := _spawn(wk[0], holder)
	var t := _spawn(tr[0], holder)
	var span: Array = wk[0]["props"]["span"]
	var seen_states := {}
	var moved := false
	var first_x := {}
	for i in 1600:                                   # 80 s at 20 fps
		w._process(0.05)
		t._process(0.05)
		seen_states[str(t.get("_state"))] = true
		for p in w.get("_people"):
			var spr: Sprite2D = p["spr"]
			if spr == null:
				continue
			if not first_x.has(spr.get_instance_id()):
				first_x[spr.get_instance_id()] = spr.position.x
			elif absf(spr.position.x - float(first_x[spr.get_instance_id()])) > 20.0:
				moved = true
			if spr.visible and (spr.position.x < float(span[0]) - 40.0 or spr.position.x > float(span[1]) + 40.0):
				kit.fail("walker visible outside its lane at x %.0f" % spr.position.x)
				return true
	kit.ok(moved, "island walkers actually walk")
	kit.eq((w.get("_people") as Array).size(), int(wk[0]["props"]["count"]), "walker count")
	for s in ["wait", "leave", "away", "enter"]:
		kit.ok(seen_states.has(s), "tram went through state '%s' within 80 s" % s)
	return true


func _pigeons() -> bool:
	var pg: Array = _actors("StationPigeons.tscn")
	if not kit.ok(pg.size() > 0, "pigeons declared"):
		return true
	var holder := Node2D.new()
	kit.mount(holder)
	# the whole scene is shifted 2000 px to the right of the (absent) camera: identical behaviour, but the
	# coo / flutter one-shots stay silent (a headless run that quits while they play leaks their playbacks)
	var entry: Dictionary = (pg[0] as Dictionary).duplicate(true)
	var shift := 2000.0
	entry["pos"] = [float(entry["pos"][0]) + shift, entry["pos"][1]]
	entry["props"]["bread_pos"] = [float(entry["props"]["bread_pos"][0]) + shift, entry["props"]["bread_pos"][1]]
	var spots: Array = []
	for sp in entry["props"]["spots"]:
		spots.append([float(sp[0]) + shift, sp[1]])
	entry["props"]["spots"] = spots
	var flock := _spawn(entry, holder)
	var game := Kit.root().get_node_or_null("Game")
	if not kit.ok(game != null, "Game autoload present"):
		return true
	var keep = game.get("player")
	var fake := CharacterBody2D.new()
	holder.add_child(fake)
	game.set("player", fake)
	var hs: Array = man.get("hotspots", {}).get("exp_pigeons", [480, 296])
	# 1) somebody stands at the find and watches -> they keep tugging at the sandwich
	fake.global_position = Vector2(float(hs[0]) + shift, float(hs[1]))
	fake.velocity = Vector2.ZERO
	for i in 200:
		flock._process(0.05)
	var down := 0
	for b in flock.get("_birds"):
		if str(b["state"]) == "ground":
			down += 1
	kit.eq(down, (flock.get("_birds") as Array).size(), "a walking/standing observer at exp_pigeons does not scare them")
	# 2) running past -> they fly up to the canopy girder
	fake.velocity = Vector2(90, 0)
	for i in 60:
		flock._process(0.05)
	var up := 0
	for b in flock.get("_birds"):
		if str(b["state"]) in ["alarm", "fly", "away"]:
			up += 1
	kit.ok(up >= 3, "running past makes the flock fly up (%d birds)" % up)
	# 3) the runner is gone -> they glide back to their spots
	fake.velocity = Vector2.ZERO
	fake.global_position = Vector2(1500.0 + shift, 320)
	for i in 1200:
		flock._process(0.05)
	var back := 0
	for b in flock.get("_birds"):
		if str(b["state"]) == "ground":
			back += 1
	kit.eq(back, (flock.get("_birds") as Array).size(), "after the runner left all pigeons are back on the ground")
	game.set("player", keep)
	return true
