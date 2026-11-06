extends RefCounted
## The registry art of Chapter 3 part 2 (L_C3_Registry, assets/environments/veltrava_registry,
## tools/pixelgen/env_c3p2_archive*.py, scripts/levels/c3p2_archive/registry_level.gd):
##  * the art contract of C3P2_DESIGN §5.1 / §4: world, walk band, every story hotspot / spawn / blocker unchanged
##  * every referenced file exists; strips are whole numbers of frames; _n / _e maps match; opaque art is binary
##    alpha; the insignia sites keep their neutral + _hist pair (§12.4); the room looks are palette-pure
##  * every story hotspot stands at the painted object it belongs to; the foreground frame keeps them clear
##  * the level script: story + exploration nodes kept, the four looks follow the scene (A night/torch, B green
##    lamp, C fire, D fire in the Karteisaal), story patches follow objectives / the c3d choice, blockers follow
##    the design, a memory sees only what its scene implies, a live change cross-fades without a dip

const Kit := preload("res://tests/support/test_kit.gd")
const ENV := "res://assets/environments/veltrava_registry/"
const LEVEL := "res://scenes/levels/L_C3_Registry.tscn"
const SCRIPT := "res://scripts/levels/c3p2_archive/registry_level.gd"
const RegistryLevel := preload("res://scripts/levels/c3p2_archive/registry_level.gd")
const HOTSPOTS := {"crates": 232, "ramp_door": 398, "alexei_chute": 440, "chute_door": 476, "intake_desk": 505,
	"fire_case": 560, "porter_booth": 612, "konrad_booth": 640, "konrad_cards": 880, "alexei_table": 950,
	"sorting_table": 1012, "drawer_c17": 1104, "plan_wall": 1340}
const SPAWNS := {"SP_C3_Gate": 44, "SP_C3_KonradCards": 898, "SP_C3_AlexeiTable": 968, "SP_C3_KonradBooth": 658,
	"SP_C3_AlexeiChute": 458}
const BLOCKERS := {"ramp_bolted": [[384, 280, 12, 40], "c3d_choose"], "fire_c": [[1236, 270, 24, 60], "c3d_choose"],
	"fire_d": [[690, 270, 24, 60], "c3e_reach_konrad"]}
## Playfield node -> [objective, hotspot] (the story shell of the design, never touched by art)
const STORY_NODES := {"Crates": ["c3c_inspect_crates", "crates"], "NightBook": ["c3c_inspect_night_book", "porter_booth"],
	"TalkKonrad": ["c3c_talk_konrad", "konrad_cards"], "IntakeBook": ["c3d_inspect_intake", "intake_desk"],
	"DrawerC17": ["c3d_inspect_drawer", "drawer_c17"], "TalkCompare": ["c3d_talk_compare", "alexei_table"],
	"CheckTable": ["c3d_solve_check", "sorting_table"], "PlanWall": ["c3d_inspect_plan", "plan_wall"],
	"TalkPartner": ["c3d_talk_partner", "alexei_table"], "ChoicePlan": ["c3d_choose", "alexei_table"],
	"TakeFile": ["c3e_take_file", "sorting_table"], "RampDoor": ["c3e_try_ramp", "ramp_door"],
	"TalkSmoke": ["c3e_reach_konrad", "konrad_booth"], "FireCase": ["c3f_inspect_hose", "fire_case"],
	"TalkDesk": ["c3f_push_desk", "intake_desk"], "TalkChute": ["c3f_climb", "chute_door"]}
const SCENE_OF := {"a": "L_C3_RegistryA", "b": "L_C3_RegistryB", "c": "L_C3_RegistryC", "d": "L_C3_RegistryD"}

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "veltrava_registry/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("design_contract", _contract)
	kit.run_case("files_maps_and_strips", _files)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("room_looks_palette_pure", _palette)
	kit.run_case("hotspots_at_their_objects", _objects)
	kit.run_case("foreground_keeps_hotspots_clear", _fg_clear)
	kit.run_case("level_script_and_story_nodes", _level_nodes)
	kit.run_case("looks_follow_the_scene", _looks)
	kit.run_case("story_patches_and_blockers", _patches)
	kit.run_case("memory_and_crossfade", _memory_and_fade)
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


# ------------------------------------------------------------------ contract
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


func _contract() -> bool:
	kit.eq(m.get("id"), "veltrava_registry", "env id")
	kit.eq(_ints(m.get("world_size")), [1920, 360], "world 1920 x 360")
	kit.eq(_ints(m.get("walkable")), [[18, 296], [1902, 296], [1902, 306], [18, 306]], "walk band y 296-306, x 18-1902")
	var hs: Dictionary = m.get("hotspots", {})
	for k in HOTSPOTS:
		kit.eq(_ints(hs.get(k)), [HOTSPOTS[k], 300], "story hotspot %s at (%d, 300)" % [k, HOTSPOTS[k]])
	var sp: Dictionary = m.get("spawns", {})
	for k in SPAWNS:
		kit.eq(_ints(sp.get(k)), [SPAWNS[k], 300], "spawn %s at (%d, 300)" % [k, SPAWNS[k]])
	var seen := {}
	for b in m.get("blockers", []):
		seen[str(b.get("name"))] = b
	for k in BLOCKERS:
		if kit.ok(seen.has(k), "blocker %s present" % k):
			kit.eq(_ints(seen[k].get("rect")), BLOCKERS[k][0], "blocker %s rect" % k)
			kit.eq(seen[k].get("after"), BLOCKERS[k][1], "blocker %s after %s" % [k, BLOCKERS[k][1]])
	var zones: Dictionary = m.get("zones", {})
	for z in ["yard", "annahme", "karteisaal", "planarchiv", "magazin"]:
		kit.ok(zones.has(z), "zone %s kept" % z)
	return true


# ------------------------------------------------------------------ files
func _files() -> bool:
	var names := {}
	for pair in _entries():
		var section: String = pair[0]
		var e: Dictionary = pair[1]
		var nm := str(e.get("name", e.get("file", "")))
		kit.ok(not names.has(section + nm), "%s: unique name %s" % [section, nm])
		names[section + nm] = true
		var path: String = ENV + str(e.get("file", ""))
		var img := _img(path)
		if not kit.ok(img != null, "%s %s: file %s exists" % [section, nm, path]):
			continue
		var frames := int(e.get("frames", 1))
		kit.ok(frames >= 1 and img.get_width() % frames == 0, "%s: width %d is a whole number of %d frames" % [nm, img.get_width(), frames])
		kit.ok(img.get_width() <= 16384 and img.get_height() <= 360, "%s: size %s within texture limits" % [nm, img.get_size()])
		if frames > 1:
			kit.ok(float(e.get("fps", 0)) > 0.0 and float(e.get("fps", 0)) <= 12.0, "%s: fps in (0, 12]" % nm)
		var opaque := section == "props" or nm.begins_with("room") or str(e.get("file", "")).begins_with("patches/") \
			or str(e.get("file", "")).begins_with("fx/flames") or nm == "fg_frame" or nm == "outside"
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
	var lights := {}
	for li in m.get("lights", []):
		var ln := str(li.get("name", ""))
		kit.ok(not lights.has(ln), "light %s unique" % ln)
		lights[ln] = true
		var p: Array = li.get("pos", [0, 0])
		kit.ok(float(p[0]) >= 0 and float(p[0]) <= 1920 and float(p[1]) >= 0 and float(p[1]) <= 360, "light %s inside the world" % ln)
		kit.ok(float(li.get("flicker_hz", 0.0)) <= 3.0, "light %s: slow flicker <= 3 Hz" % ln)
	for need in ["room", "room_a", "room_fire_c", "room_fire_d", "outside", "shafts", "smoke_c", "smoke_d", "fg_frame"]:
		var found := false
		for L in m.get("layers", []):
			found = found or str(L.get("name")) == need
		kit.ok(found, "layer %s present" % need)
	return true


func _insignia() -> bool:
	var sites := 0
	for pair in _entries():
		var e: Dictionary = pair[1]
		if not e.has("hist_variant"):
			continue
		sites += 1
		var hv: String = ENV + str(e["hist_variant"])
		var base: String = ENV + str(e["file"])
		kit.eq(hv, Symbols.hist_path(base), "%s: hist variant follows the <name>_hist rule" % e.get("name"))
		var hi := _img(hv)
		var bi := _img(base)
		if kit.ok(hi != null and bi != null, "%s: neutral + _hist files exist" % e.get("name")):
			kit.eq(hi.get_size(), bi.get_size(), "%s: _hist has the size of the neutral file" % e.get("name"))
	kit.ok(sites >= 6, "insignia sites: handcart (2) + Magazin plates (4 looks), got %d" % sites)
	return true


func _palette() -> bool:
	var c3 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c3.json"))
	var allowed := {}
	for ramp in c3.get("palettes", {}).get("registry", {}).values():
		for h in ramp:
			allowed[str(h).to_upper().trim_prefix("#")] = true
	for nm in ["room", "room_a", "room_fire_c", "room_fire_d"]:
		var img := _img(ENV + nm + ".png")
		if not kit.ok(img != null, nm + " loads"):
			continue
		var bad := 0
		for y in range(0, img.get_height(), 3):
			for x in range(0, img.get_width(), 3):
				var c := img.get_pixel(x, y)
				if c.a > 0.5 and not allowed.has(c.to_html(false).to_upper()):
					bad += 1
		kit.eq(bad, 0, "%s: every sampled pixel is a 'registry' palette colour" % nm)
	return true


# ------------------------------------------------------------------ placement
func _objects() -> bool:
	var info: Dictionary = m.get("hotspot_info", {})
	for k in HOTSPOTS:
		if not kit.ok(info.has(k), "hotspot_info names the object of %s" % k):
			continue
		var span: Array = info[k].get("span", [])
		kit.ok(span.size() == 2 and float(span[0]) <= HOTSPOTS[k] and HOTSPOTS[k] <= float(span[1]),
			"%s (x %d) stands at its object %s %s" % [k, HOTSPOTS[k], info[k].get("what", ""), span])
	# the partner spots of the switch scenes are next to their dialogue hotspots (design §4)
	kit.ok(absi(SPAWNS["SP_C3_KonradCards"] - HOTSPOTS["konrad_cards"]) <= 24, "Konrad stands beside konrad_cards")
	kit.ok(absi(SPAWNS["SP_C3_AlexeiTable"] - HOTSPOTS["alexei_table"]) <= 24, "Alexei stands beside alexei_table")
	kit.ok(absi(SPAWNS["SP_C3_KonradBooth"] - HOTSPOTS["konrad_booth"]) <= 24, "Konrad stands beside konrad_booth")
	# no FX strip or gated decal hides a story hotspot's interaction point behind a wall of flames before the fire
	for d in m.get("decals", []):
		if str(d.get("file", "")).begins_with("fx/flames"):
			kit.ok(d.has("after"), "%s only burns once the fire started" % d.get("name"))
	return true


func _fg_clear() -> bool:
	var fg := _img(ENV + "fg_frame.png")
	if not kit.ok(fg != null, "fg_frame loads"):
		return false
	var par := 1.25
	for L in m.get("layers", []):
		if str(L.get("name")) == "fg_frame":
			par = float(L.get("parallax", [1.25, 1])[0])
	var all := HOTSPOTS.duplicate()
	all.merge(SPAWNS)
	for k in all:
		var hx := float(all[k])
		var cam := clampf(hx - 320.0, 0.0, 1280.0)
		var fx := int(round(hx - cam + par * cam))
		var covered := false
		for y in range(250, 306):
			for x in range(maxi(0, fx - 12), mini(fg.get_width(), fx + 13)):
				if fg.get_pixel(x, y).a > 0.0:
					covered = true
		kit.ok(not covered, "foreground frame keeps %s clear (camera centred on it)" % k)
	return true


# ------------------------------------------------------------------ level script
func _mount() -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	return lvl


func _apply_state(lvl: Node, look: String, done := {}, choice := {}) -> void:
	lvl.set("level_id", SCENE_OF[look])
	lvl.set("done_override", done)
	lvl.set("choice_override", choice)
	lvl.set("memory_override", false)
	lvl.set("hidden_override", false)
	lvl.call("refresh", true)


func _level_nodes() -> bool:
	var lvl := _mount()
	kit.eq((lvl.get_script() as Script).resource_path, SCRIPT, "the shell runs registry_level.gd")
	kit.ok(lvl is Level, "registry_level extends Level")
	var pf: Node = lvl.get_node_or_null("Playfield")
	for nm in STORY_NODES:
		var n: Node = pf.get_node_or_null(nm) if pf else null
		if not kit.ok(n != null, "story node %s kept" % nm):
			continue
		kit.eq(str(n.get("objective_id")), STORY_NODES[nm][0], "%s objective" % nm)
		kit.eq(str(n.get("hotspot_id")), STORY_NODES[nm][1], "%s hotspot" % nm)
		kit.eq((n as Node2D).position, Vector2(HOTSPOTS[STORY_NODES[nm][1]], 300), "%s placed at its hotspot" % nm)
	var groups: Array = lvl.get("groups")
	kit.ok(groups.size() >= 10, "gate groups built (%d)" % groups.size())
	var man: Dictionary = lvl.get("manifest")
	for section in ["layers", "props", "decals", "fx", "lights"]:
		for e in man.get(section, []):
			kit.ok(not RegistryLevel.is_gated(e), "%s %s: no gated entry left for the base build" % [section, e.get("name", "")])
	kit.eq((lvl.get("blockers") as Dictionary).size(), 3, "three gated walls built")
	return true


func _looks() -> bool:
	var lvl := _mount()
	var want := {"a": ["registry", false, false, false], "b": ["registry", false, false, false],
		"c": ["registry_fire", true, true, false], "d": ["registry_fire", true, true, true]}
	for lk in ["a", "b", "c", "d"]:
		_apply_state(lvl, lk)
		kit.eq(lvl.call("look"), lk, "scene %s plays look %s" % [SCENE_OF[lk], lk])
		kit.eq(str(lvl.get("grade_preset")), want[lk][0], "look %s: grade %s" % [lk, want[lk][0]])
		kit.eq(lvl.call("blocker_on", "ramp_bolted"), want[lk][1], "look %s: ramp door bolted = %s" % [lk, want[lk][1]])
		kit.eq(lvl.call("blocker_on", "fire_c"), want[lk][2], "look %s: fire front C = %s" % [lk, want[lk][2]])
		kit.eq(lvl.call("blocker_on", "fire_d"), want[lk][3], "look %s: fire front D = %s" % [lk, want[lk][3]])
		kit.eq(lvl.call("is_shown", "torch"), lk == "a", "look %s: Konrad's torch only before the lamp" % lk)
		kit.eq(lvl.call("is_shown", "green_lamp"), lk == "b", "look %s: green lamp (steady) in B" % lk)
		kit.eq(lvl.call("is_shown", "flames_c17"), lk in ["c", "d"], "look %s: the C-17 shelf burns from C on" % lk)
		kit.eq(lvl.call("is_shown", "flames_bank"), lk == "d", "look %s: the Karteisaal burns in D" % lk)
		kit.eq(lvl.call("is_shown", "guard_feet"), lk in ["a", "b"], "look %s: the guard passes the window at night" % lk)
		kit.eq(lvl.call("is_shown", "cart"), lk == "a", "look %s: seal wire on the crates until inspected" % lk)
		kit.eq(lvl.call("is_shown", "cart_open"), lk != "a", "look %s: crates without the seal afterwards" % lk)
		kit.eq(lvl.call("is_shown", "snow_yard"), false, "snow in the yard is ungated (always built by the base)")
	return true


func _patches() -> bool:
	var lvl := _mount()
	_apply_state(lvl, "a", {"c3c_inspect_crates": true})
	kit.ok(lvl.call("is_shown", "cart_open") and not lvl.call("is_shown", "cart"), "A: the seal is taken right after the inspection")
	_apply_state(lvl, "b")
	kit.ok(not lvl.call("is_shown", "scarf_taken_b") and not lvl.call("is_shown", "halves_b"), "B starts with the scarf, no halves")
	_apply_state(lvl, "b", {"c3d_inspect_drawer": true, "c3d_talk_compare": true})
	kit.ok(lvl.call("is_shown", "scarf_taken_b") and lvl.call("is_shown", "halves_b"), "B: scarf taken, halves on the table")
	_apply_state(lvl, "c", {}, {"c3d_choose": "admit_plan"})
	kit.ok(not lvl.call("is_shown", "blatt7_pocketed_c"), "C after admit_plan: Blatt 7 still hangs (it burns)")
	_apply_state(lvl, "c", {"c3e_take_file": true}, {"c3d_choose": "pocket_plan"})
	kit.ok(lvl.call("is_shown", "blatt7_pocketed_c"), "C after pocket_plan: the frame is empty")
	kit.ok(lvl.call("is_shown", "file_taken_c"), "C: the file is gone from the table once taken")
	_apply_state(lvl, "d", {"c3f_inspect_hose": true}, {"c3d_choose": "pocket_plan"})
	kit.ok(lvl.call("is_shown", "case_broken_d") and not lvl.call("is_shown", "desk_pushed_d"), "D: case smashed, desk still in place")
	kit.ok(lvl.call("is_shown", "blatt7_pocketed_d"), "D keeps the empty frame (pocket_plan)")
	_apply_state(lvl, "d", {"c3f_inspect_hose": true, "c3f_push_desk": true})
	kit.ok(lvl.call("is_shown", "desk_pushed_d") and lvl.call("is_shown", "desk_lamp_pushed"), "D: the desk (and its lamp) pushed away")
	kit.ok(not lvl.call("is_shown", "desk_lamp"), "D: the desk lamp light moved with the desk")
	return true


func _memory_and_fade() -> bool:
	var lvl := _mount()
	# a memory of scene A sees A, whatever the present has done (done_override null -> the live Story is asked
	# only outside a memory)
	lvl.set("done_override", null)
	lvl.set("choice_override", {})
	lvl.set("memory_override", true)
	lvl.set("hidden_override", false)
	lvl.set("level_id", SCENE_OF["a"])
	lvl.call("refresh", true)
	kit.eq(lvl.call("look"), "a", "memory of A: night, lamp off")
	lvl.set("level_id", SCENE_OF["c"])
	lvl.call("refresh", true)
	kit.eq(lvl.call("look"), "c", "memory of C: the fire of C (implied by the scene)")
	kit.ok(not lvl.call("is_shown", "file_taken_c"), "memory of C: the file still on the table")
	# live C -> D (c3e_reach_konrad): D fades in over C, C stays until D covers it (no dip to the night look)
	_apply_state(lvl, "c")
	lvl.set("done_override", {"c3e_reach_konrad": true})
	lvl.call("refresh", false)
	var gc: Dictionary = {}
	var gd: Dictionary = {}
	for g in lvl.get("groups"):
		if "room_fire_c" in g["names"]:
			gc = g
		if "room_fire_d" in g["names"]:
			gd = g
	if kit.ok(not gc.is_empty() and not gd.is_empty(), "room look groups found"):
		kit.eq(float(gd["target"]), 1.0, "D look appears")
		kit.ok(float(gd["cur"]) < 1.0, "D look fades in (live)")
		kit.eq(float(gc["target"]), 0.0, "C look goes")
		kit.ok(float(gc["delay"]) >= float(gd["fade"]) - 0.001, "C look waits until D has covered it")
		kit.eq(float(gc["cur"]), 1.0, "C look still fully visible at the start of the fade")
	# a hidden level (cinematic) changes instantly
	lvl.set("hidden_override", true)
	lvl.set("done_override", {})
	lvl.set("level_id", SCENE_OF["b"])
	lvl.call("refresh", false)
	kit.eq(lvl.call("look"), "b", "hidden level: back to B")
	for g in lvl.get("groups"):
		kit.eq(float(g["cur"]), float(g["target"]), "hidden level: %s applied instantly" % str(g["names"][0]))
	return true
