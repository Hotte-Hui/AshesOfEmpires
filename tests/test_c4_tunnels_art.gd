extends RefCounted
## The Karsk tunnels art of Chapter 4 part 1 (L_C4_Tunnels, assets/environments/karsk_tunnels,
## tools/pixelgen/env_c4_tunnels*.py, scripts/levels/c4/tunnels_level.gd, assets/ui/documents/karsk_tunnels_*):
##  * the art contract of C4_DESIGN §4.1: world, walk band, every story hotspot / spawn / NPC anchor / the blocker
##  * every referenced file exists; strips are whole numbers of frames; maps match; opaque art is binary alpha; every
##    light is named (gated) and slow; the insignia sites keep their neutral + _hist pair (§12.4); palette-pure room
##  * every story hotspot stands at its painted object; the foreground keeps hotspots and spawns clear
##  * the level script: the shell runs tunnels_level.gd, story nodes kept; each scene builds only its own art, has
##    its own camera window and look; story patches follow objectives; a memory sees what its scene implies
##  * the passing train: the lamps swing at most 3 px (reduced motion 1 px), lights dip <= 10 % and slower than 3 Hz,
##    every event strip shows only during the train, everything rests afterwards; round-9 fix (train pile-up): only
##    scene C runs a train of its own (about −8 dB, never on top of the ambience's train), scene A is left to the
##    trains of its ambience, and dust / swing / dip fall on the loudest part of the train's sound (c4_train_overhead
##    read from the WAV; the ambiences' trains followed through their playback position)
##  * the inspect documents: one image per tunnels item, alt texts in German, InspectView finds them

const Kit := preload("res://tests/support/test_kit.gd")
const UiKit := preload("res://scripts/ui/ui_kit.gd")
const ENV := "res://assets/environments/karsk_tunnels/"
const LEVEL := "res://scenes/levels/L_C4_Tunnels.tscn"
const SCRIPT := "res://scripts/levels/c4/tunnels_level.gd"
const TunnelsLevel := preload("res://scripts/levels/c4/tunnels_level.gd")
const RegistryLevel := preload("res://scripts/levels/c3p2_archive/registry_level.gd")
const SA := "L_C4_TunnelsA"
const SC := "L_C4_TunnelsB"
const HOTSPOTS := {"book_shelf": 184, "desk_book": 372, "lev_cellar": 428, "lamp_table": 520, "tunnel_door": 664,
	"office_desk": 1346, "paint_stand": 1468, "wagon_side": 1590, "wagon_door": 1680, "lev_siding": 1772}
const SPAWNS := {"SP_C4_Stairs": 48, "SP_C4_Office": 1322}
const AREA := {SA: [18, 700], SC: [720, 1902]}
const STORY_NODES := {"S_c4a_inspect_shelf": "book_shelf", "S_c4a_talk_lev": "lev_cellar", "S_c4a_inspect_book": "desk_book",
	"S_c4a_inspect_carbon": "lamp_table", "S_c4a_talk_tunnel": "lev_cellar", "S_c4a_open_door": "tunnel_door",
	"S_c4c_inspect_card": "office_desk", "S_c4c_inspect_stencils": "paint_stand", "S_c4c_solve_numbers": "wagon_side",
	"S_c4c_inspect_wagon": "wagon_door", "S_c4c_talk_lev": "lev_siding"}
const DOC_ITEMS := {"ev_c4_book_gap": "karsk_tunnels_book_gap", "ev_c4_cut_signatures": "karsk_tunnels_freight_book",
	"ev_c4_carbon": "karsk_tunnels_carbon", "ev_c4_tunnel_plan": "karsk_tunnels_plan",
	"ev_c4_fresh_tracks": "karsk_tunnels_tracks", "ev_c4_card_ru": "karsk_tunnels_card_ru",
	"ev_c4_stencils": "karsk_tunnels_stencils", "ev_c4_wagon_inside": "karsk_tunnels_wagon_inside"}

var kit: Kit
var m: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ENV + "scene.json"))
	if not kit.ok(parsed is Dictionary, "karsk_tunnels/scene.json parses"):
		return kit.failures
	m = parsed
	kit.run_case("design_contract", _contract)
	kit.run_case("files_maps_and_strips", _files)
	kit.run_case("insignia_pairs", _insignia)
	kit.run_case("room_palette_pure", _palette)
	kit.run_case("hotspots_at_their_objects", _objects)
	kit.run_case("foreground_keeps_hotspots_clear", _fg_clear)
	kit.run_case("level_script_and_scene_filter", _level)
	kit.run_case("story_patches_and_memory", _patches)
	kit.run_case("passing_train", _train)
	kit.run_case("inspect_documents", _documents)
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
	for section in ["layers", "props", "decals", "fx", "swing", "event_fx"]:
		for e in m.get(section, []):
			if e is Dictionary:
				out.append([section, e])
	return out


# ------------------------------------------------------------------ contract
func _contract() -> bool:
	kit.eq(m.get("id"), "karsk_tunnels", "env id")
	kit.eq(_ints(m.get("world_size")), [1920, 360], "world 1920 x 360")
	kit.eq(_ints(m.get("walkable")), [[18, 296], [1902, 296], [1902, 306], [18, 306]], "walk band y 296-306, x 18-1902")
	var hs: Dictionary = m.get("hotspots", {})
	for k in HOTSPOTS:
		kit.eq(_ints(hs.get(k)), [HOTSPOTS[k], 300], "story hotspot %s at (%d, 300)" % [k, HOTSPOTS[k]])
	var sp: Dictionary = m.get("spawns", {})
	for k in SPAWNS:
		kit.eq(_ints(sp.get(k)), [SPAWNS[k], 300], "spawn %s at (%d, 300)" % [k, SPAWNS[k]])
	var bl: Array = m.get("blockers", [])
	if kit.eq(bl.size(), 1, "one permanent blocker"):
		kit.eq(str(bl[0].get("name")), "cellar_door", "blocker cellar_door")
		kit.eq(_ints(bl[0].get("rect")), [700, 270, 20, 60], "the door wall 700-720")
		kit.ok(not RegistryLevel.is_gated(bl[0]), "the door wall is never opened by a gate")
	var npcs: Dictionary = m.get("npcs", {})
	kit.eq(_ints(npcs.get("lev_cellar", {}).get("feet")), [446, 300], "Lev in the cellar at (446, 300)")
	kit.eq(_ints(npcs.get("lev_siding", {}).get("feet")), [1790, 300], "Lev at the siding at (1790, 300)")
	kit.eq(npcs.get("lev_siding", {}).get("show_after"), "c4a_open_door", "Lev at the siding after the door")
	kit.eq(npcs.get("lev_cellar", {}).get("hide_after"), "c4c_inspect_card", "Lev leaves the cellar")
	var zones: Dictionary = m.get("zones", {})
	for z in ["cellar", "door", "tunnel", "siding"]:
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
		if frames > 1 and section != "swing":
			kit.ok(float(e.get("fps", 0)) > 0.0 and float(e.get("fps", 0)) <= 12.0, "%s: fps in (0, 12]" % nm)
		var opaque := nm == "room" or str(e.get("file", "")).begins_with("patches/") or nm == "fg_frame" or nm == "outside"
		if opaque:
			kit.ok(img.detect_alpha() != Image.ALPHA_BLEND, "%s: binary alpha (coded texel material)" % nm)
		var maps: Array = []
		if bool(e.get("normal", section == "props")):
			maps.append("_n")
		if bool(e.get("emission", false)):
			maps.append("_e")
		for suffix in maps:
			var mi := _img(path.get_basename() + suffix + ".png")
			if kit.ok(mi != null, "%s: map %s exists" % [nm, suffix]):
				kit.eq(mi.get_size(), img.get_size(), "%s: %s map matches the image" % [nm, suffix])
		if e.has("fade"):
			kit.ok(float(e["fade"]) >= 0.0 and float(e["fade"]) <= 3.0, "%s: fade within 0..3 s" % nm)
		for s in RegistryLevel._list(e.get("scene", [SA, SC])):
			kit.ok(str(s) in [SA, SC], "%s: scene filter names a tunnels scene (%s)" % [nm, s])
	for e in m.get("swing", []):
		var img := _img(ENV + str(e.get("file", "")))
		kit.eq(int(e.get("frames", 0)), 7, "%s: 7 swing frames" % e.get("name"))
		kit.ok(int(e.get("rest", -1)) == 3 and int(e.get("max_px", 9)) <= 3, "%s: rests on frame 3, swings <= 3 px" % e.get("name"))
		kit.ok(img != null and img.get_height() >= 100, "%s: the cord is long enough for <= 2 deg" % e.get("name"))
	var tr: Dictionary = m.get("train", {})
	kit.ok(_img(ENV + str(tr.get("file", ""))) != null, "the train over the yard exists")
	var lights := {}
	for li in m.get("lights", []):
		var ln := str(li.get("name", ""))
		kit.ok(not lights.has(ln), "light %s unique" % ln)
		lights[ln] = true
		var p: Array = li.get("pos", [0, 0])
		kit.ok(float(p[0]) >= 0 and float(p[0]) <= 1920 and float(p[1]) >= 0 and float(p[1]) <= 360, "light %s inside the world" % ln)
		kit.ok(float(li.get("flicker_hz", 0.0)) <= 3.0, "light %s: slow flicker <= 3 Hz" % ln)
		kit.ok(RegistryLevel.is_gated(li), "light %s is gated (named, flicker driven by the level)" % ln)
	for need in ["green_lamp", "hang_lamp", "stove", "lightbox", "cage_902", "bulb_wagon", "work_left", "kerosene", "portal_dawn"]:
		kit.ok(lights.has(need), "light %s present" % need)
	for need in ["room", "outside", "veils", "fg_frame"]:
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
			kit.ok(hi.get_data() != bi.get_data(), "%s: the _hist file shows a different emblem" % e.get("name"))
	kit.eq(sites, 3, "insignia sites: wall calendar, lever-frame plate, wagon stencil")
	return true


func _palette() -> bool:
	var allowed := {}
	var meta: Dictionary = m.get("meta", {})
	for ramp in meta.get("palette_ramps", {}).values():
		for h in ramp:
			allowed[str(h).to_upper().trim_prefix("#")] = true
	var c4 = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/c4.json"))
	for ramp in (c4.get("palettes", {}).get("tunnels", {}) as Dictionary).values():
		for h in ramp:
			kit.ok(allowed.has(str(h).to_upper().trim_prefix("#")), "c4.json tunnels colour %s kept in the art palette" % h)
	for nm in ["room", "patches/door_open", "patches/wagon_open"]:
		var img := _img(ENV + nm + ".png")
		if not kit.ok(img != null, nm + " loads"):
			continue
		var bad := 0
		for y in range(0, img.get_height(), 3):
			for x in range(0, img.get_width(), 3):
				var c := img.get_pixel(x, y)
				if c.a > 0.5 and not allowed.has(c.to_html(false).to_upper()):
					bad += 1
		kit.eq(bad, 0, "%s: every sampled pixel is a 'tunnels' palette colour" % nm)
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
	# the art under the story hotspots differs from the bare wall (something is painted there)
	var room := _img(ENV + "room.png")
	if kit.ok(room != null, "room loads"):
		for k in HOTSPOTS:
			if k.begins_with("lev_"):
				continue
			var cols := {}
			for y in range(230, 288, 2):
				for x in range(HOTSPOTS[k] - 6, HOTSPOTS[k] + 7, 2):
					cols[room.get_pixel(x, y).to_html(false)] = true
			kit.ok(cols.size() >= 6, "%s: a detailed object is painted above the hotspot (%d colours)" % [k, cols.size()])
	return true


func _fg_clear() -> bool:
	var fg := _img(ENV + "fg_frame.png")
	if not kit.ok(fg != null, "fg_frame loads"):
		return false
	var par := 1.25
	for L in m.get("layers", []):
		if str(L.get("name")) == "fg_frame":
			par = float(L.get("parallax", [1.25, 1])[0])
	var sb: Dictionary = m.get("camera_zones", {})
	var all := HOTSPOTS.duplicate()
	all.merge(SPAWNS)
	for k in all:
		var hx := float(all[k])
		var sid := SA if hx < 710.0 else SC
		var b: Array = sb.get(sid, [0, 0, 1920, 360])
		var cam := clampf(hx - 320.0, float(b[0]), float(b[0]) + float(b[2]) - 640.0)
		var fx := int(round(hx - cam + par * cam))
		var covered := false
		for y in range(250, 306):
			for x in range(maxi(0, fx - 12), mini(fg.get_width(), fx + 13)):
				if fg.get_pixel(x, y).a > 0.0:
					covered = true
		kit.ok(not covered, "foreground frame keeps %s clear (camera centred on it)" % k)
	return true


# ------------------------------------------------------------------ level script
func _mount(scene_id: String) -> Node:
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("level_id", scene_id)
	lvl.set("ambience", "")
	lvl.set("music", "")
	kit.mount(lvl)
	return lvl


func _apply(lvl: Node, done := {}, memory := false) -> void:
	lvl.set("done_override", done)
	lvl.set("choice_override", {})
	lvl.set("memory_override", memory)
	lvl.set("hidden_override", false)
	lvl.call("refresh", true)


func _built(lvl: Node, entry_name: String) -> bool:
	for g in lvl.get("groups"):
		if entry_name in g["names"]:
			return true
	var bd: Node = lvl.get_node_or_null("Backdrop")
	if bd != null and (bd.get("decals_by_name") as Dictionary).has(entry_name):
		return true
	return false


func _level() -> bool:
	var a := _mount(SA)
	kit.eq((a.get_script() as Script).resource_path, SCRIPT, "the shell runs tunnels_level.gd")
	kit.ok(a is Level and a is RegistryLevel, "tunnels_level extends the registry level (gates, blockers, looks)")
	var pf: Node = a.get_node_or_null("Playfield")
	for nm in STORY_NODES:
		var n: Node = pf.get_node_or_null(nm) if pf else null
		if kit.ok(n != null, "story node %s kept" % nm):
			kit.eq(str(n.get("hotspot_id")), STORY_NODES[nm], "%s hotspot" % nm)
			kit.eq((n as Node2D).position, Vector2(HOTSPOTS[STORY_NODES[nm]], 300), "%s placed at its hotspot" % nm)
	kit.ok(a.call("blocker_on", "cellar_door"), "the door wall blocks walking")
	kit.eq(a.call("get_camera_bounds"), Rect2(0, 0, 720, 360), "scene A: the camera stays in the cellar")
	kit.eq(a.call("look"), "cellar", "scene A looks like the cellar")
	kit.eq(str(a.get("grade_preset")), "tunnels", "scene A: grade tunnels")
	kit.ok(_built(a, "door_open") and _built(a, "plan_taken"), "scene A builds its story patches")
	kit.ok(not _built(a, "wagon_open") and not _built(a, "bulb_wagon"), "scene A builds nothing of the siding")
	kit.eq((a.get("swings") as Array).size(), 1, "scene A: one swinging lamp (the enamel shade)")
	kit.ok(a.get("train_node") == null, "scene A: no train over the cellar")
	var c := _mount(SC)
	kit.eq(c.call("get_camera_bounds"), Rect2(700, 0, 1220, 360), "scene C: the camera stays right of the door wall")
	kit.eq(c.call("look"), "siding", "scene C looks like the siding")
	kit.eq(str(c.get("grade_preset")), "tunnels_siding", "scene C: grade tunnels_siding")
	kit.ok(_built(c, "wagon_open") and _built(c, "bulb_wagon"), "scene C builds the siding art")
	kit.ok(not _built(c, "door_open") and not _built(c, "green_lamp"), "scene C builds nothing of the cellar")
	kit.eq((c.get("swings") as Array).size(), 1, "scene C: one swinging lamp (the bulb over the wagon)")
	kit.ok(c.get("train_node") != null, "scene C: the train over the yard is built")
	for nm in ["LevCellar", "LevSiding"]:
		kit.ok(c.get_node_or_null("Playfield/" + nm) != null, "%s kept" % nm)
	var man: Dictionary = c.get("manifest")
	for section in ["layers", "props", "decals", "fx", "lights"]:
		for e in man.get(section, []):
			kit.ok(not RegistryLevel.is_gated(e), "%s %s: no gated entry left for the base build" % [section, e.get("name", "")])
			kit.ok(not (e as Dictionary).has("scene") or SC in RegistryLevel._list(e["scene"]), "%s %s: only scene C entries" % [section, e.get("name", "")])
	return true


func _patches() -> bool:
	var a := _mount(SA)
	_apply(a)
	kit.ok(not a.call("is_shown", "door_open") and not a.call("is_shown", "plan_taken"), "A starts: door shut, plan on the desk")
	_apply(a, {"c4a_talk_tunnel": true})
	kit.ok(a.call("is_shown", "plan_taken") and not a.call("is_shown", "door_open"), "A: Lev hands over the plan")
	_apply(a, {"c4a_talk_tunnel": true, "c4a_open_door": true})
	kit.ok(a.call("is_shown", "door_open") and a.call("is_shown", "door_cold"), "A: the iron door stands open, cold air")
	_apply(a, {}, true)
	kit.ok(not a.call("is_shown", "door_open"), "memory of A: the door is shut again")
	var c := _mount(SC)
	_apply(c)
	kit.ok(not c.call("is_shown", "wagon_open"), "C starts with the wagon door half open")
	_apply(c, {"c4c_inspect_wagon": true})
	kit.ok(c.call("is_shown", "wagon_open"), "C: the door slid open after the inspection")
	_apply(c, {}, true)
	kit.ok(not c.call("is_shown", "wagon_open"), "memory of C: the door half open again")
	return true


func _train() -> bool:
	for t in [0.0, 0.5, 1.0, 1.4, 2.0, 2.6, 3.3, 4.0, 5.5, 7.4]:
		var px: int = TunnelsLevel.swing_at(t, 3, false)
		kit.ok(absi(px) <= 3, "swing at %.1f s within 3 px" % t)
		kit.ok(absi(TunnelsLevel.swing_at(t, 3, true)) <= 1, "reduced motion: swing at %.1f s within 1 px" % t)
	kit.eq(TunnelsLevel.swing_at(-1.0, 3, false), 0, "no train: the lamps hang still")
	var peak := 0
	for i in 80:
		peak = maxi(peak, absi(TunnelsLevel.swing_at(i * 0.1, 3, false)))
	kit.ok(peak >= 2, "the lamps visibly swing (peak %d px)" % peak)
	kit.ok(15.0 / TAU <= 3.0, "the light flutter stays below 3 Hz")
	var c := _mount(SC)
	c.set("hidden_override", true)            # no rumble in the test run (the sound would outlive the test)
	c.call("start_train")
	c.set("hidden_override", false)
	var seen_fx := false
	var seen_train := false
	var min_ev := 1.0
	var dt := 1.0 / 30.0
	for i in int((TunnelsLevel.EVENT_LEN + 0.5) / dt):
		c.call("_sound_step", dt)
		min_ev = minf(min_ev, float(c.get("_ev")))
		for e in c.get("events"):
			seen_fx = seen_fx or (e["node"] as Node2D).visible
		var tn = c.get("train_node")
		seen_train = seen_train or (tn != null and (tn as Node2D).visible)
	kit.ok(seen_fx, "dust falls from the vault during the train")
	kit.ok(seen_train, "the train rolls over the yard above")
	kit.ok(min_ev >= 0.89 and min_ev < 1.0, "the lights dip a little, at most 10 %% (min %.3f)" % min_ev)
	kit.eq(float(c.get("train_t")), -1.0, "the event ends")
	kit.eq(int(c.get("swing_px")), 0, "the lamps rest again")
	var still := true
	for e in c.get("events"):
		still = still and not (e["node"] as Node2D).visible
	kit.ok(still and not (c.get("train_node") as Node2D).visible, "no event strip stays visible")
	for s in c.get("swings"):
		for spr in s["sprites"]:
			kit.eq((spr as Sprite2D).frame, int(s["rest"]), "%s back on its rest frame" % s["name"])
	_train_in_time(c)
	_train_scenes()
	return true


## The vault's beat lies on the loudest part of c4_train_overhead (read from the WAV): the lamps swing hardest and
## the lights dip deepest around the loudest second, the dust falls while the rumble swells to it.
func _train_in_time(c: Node) -> void:
	kit.ok(TunnelsLevel.TRAIN_DB >= -9.0 and TunnelsLevel.TRAIN_DB <= -7.0, "the level's train plays at about −8 dB (%.1f)" % TunnelsLevel.TRAIN_DB)
	var loud := _loudest_second("res://assets/audio/sfx/c4_train_overhead.wav")
	if not kit.ok(loud >= 0.0, "c4_train_overhead.wav readable (16-bit PCM)"):
		return
	var mid := loud + 0.5
	c.set("hidden_override", true)
	c.call("start_train")
	c.set("hidden_override", false)
	var dt := 1.0 / 30.0
	var sw := [0.0, 0.0]
	var dip := [0.0, 0.0]
	var dust := [0.0, 0.0]
	var t := 0.0
	for i in int((TunnelsLevel.EVENT_LEN + 0.5) / dt):
		c.call("_sound_step", dt)
		t += dt
		var a := absf(float(c.get("swing_px")))
		sw[0] += t * a
		sw[1] += a
		var d := 1.0 - float(c.get("_ev"))
		dip[0] += t * d
		dip[1] += d
		for e in c.get("events"):
			if (e["node"] as Node2D).visible:
				dust[0] += t
				dust[1] += 1.0
	if kit.ok(sw[1] > 0.0 and dip[1] > 0.0 and dust[1] > 0.0, "the beat swings, dips and drops dust"):
		var ts: float = sw[0] / sw[1]
		var td: float = dip[0] / dip[1]
		var tf: float = dust[0] / dust[1]
		kit.ok(absf(ts - mid) <= 1.0, "the lamps swing hardest at the sound's loudest second (%.2f s vs %.2f s)" % [ts, mid])
		kit.ok(absf(td - mid) <= 1.0, "the lights dip deepest at the sound's loudest second (%.2f s vs %.2f s)" % [td, mid])
		kit.ok(tf >= mid - 2.5 and tf <= mid + 0.5, "the dust falls while the rumble swells (%.2f s, loudest %.2f s)" % [tf, mid])


## Scene A has no train of its own -- its ambience carries them, and the vault answers those at their playback
## position; scene C's own train never starts on top of the ambience's train.
func _train_scenes() -> void:
	kit.eq(TunnelsLevel.OWN_TRAIN_SCENES, [SC], "only scene C runs trains of its own")
	var a := _mount(SA)
	_apply(a)
	a.set("events_enabled", true)
	a.set("amb_override", [])
	var started := false
	for i in 700:                                # 70 s: more than the longest wait between two trains
		a.call("_sound_step", 0.1)
		started = started or float(a.get("train_t")) >= 0.0
	kit.ok(not started and not bool(a.get("own_train")), "scene A starts no train of its own")
	var t0: float = (TunnelsLevel.AMB_TRAINS["amb_karsk_cellar"] as Array)[0]
	a.set("amb_override", ["amb_karsk_cellar", t0 + TunnelsLevel.BEAT_DELAY + 2.0, 60.0])
	a.call("_sound_step", 0.1)
	var dust_a := false
	for e in a.get("events"):
		dust_a = dust_a or (e["node"] as Node2D).visible
	kit.ok(is_equal_approx(float(a.get("train_t")), TunnelsLevel.BEAT_DELAY + 2.0) and not bool(a.get("own_train")),
		"scene A follows the ambience's train (its playback position)")
	kit.ok(int(a.get("swing_px")) != 0 and dust_a, "scene A: the lamp swings and dust falls with the ambience's train")
	a.set("amb_override", ["amb_karsk_cellar", 30.0, 60.0])
	a.call("_sound_step", 0.1)
	kit.ok(float(a.get("train_t")) < 0.0 and int(a.get("swing_px")) == 0, "scene A: between the ambience's trains the vault is still")
	var c := _mount(SC)
	_apply(c)
	c.set("events_enabled", true)
	var ta: float = (TunnelsLevel.AMB_TRAINS["amb_karsk_tunnel"] as Array)[0]
	for pos in [ta - 6.0, ta + 4.0]:
		c.set("amb_override", ["amb_karsk_tunnel", pos, 60.0])
		kit.ok(c.call("amb_train_near", TunnelsLevel.TRAIN_SOUND_LEN), "scene C: the ambience's train is near at %.1f s" % pos)
	c.set("amb_override", ["amb_karsk_tunnel", ta - 6.0, 60.0])
	c.set("_next_train", 0.0)
	c.call("_sound_step", 0.1)
	kit.ok(float(c.get("train_t")) < 0.0 and float(c.get("_next_train")) > 0.0, "scene C: the level's train waits for the ambience's train")
	c.set("amb_override", ["amb_karsk_tunnel", 10.0, 60.0])
	kit.ok(not c.call("amb_train_near", TunnelsLevel.TRAIN_SOUND_LEN), "scene C: far from the ambience's train the level's may run")


## Start (s) of the loudest second of a 16-bit PCM WAV (1 s windows in 0.25 s steps), -1 when unreadable.
static func _loudest_second(path: String) -> float:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return -1.0
	var b := f.get_buffer(f.get_length())
	if b.size() < 44 or b.slice(0, 4).get_string_from_ascii() != "RIFF":
		return -1.0
	var ch := 1
	var rate := 44100
	var bits := 0
	var at := -1
	var size := 0
	var i := 12
	while i + 8 <= b.size():
		var id := b.slice(i, i + 4).get_string_from_ascii()
		var sz := b.decode_u32(i + 4)
		if id == "fmt ":
			ch = b.decode_u16(i + 10)
			rate = b.decode_u32(i + 12)
			bits = b.decode_u16(i + 22)
		elif id == "data":
			at = i + 8
			size = mini(sz, b.size() - at)
			break
		i += 8 + sz + (sz % 2)
	if at < 0 or bits != 16 or ch < 1:
		return -1.0
	var frame := 2 * ch
	var hop := int(rate / 4.0)
	var windows := int(floor(float(size) / float(frame * hop)))
	var energy: Array = []
	for w in windows:
		var e := 0.0
		var n := 0
		for fr in range(w * hop, (w + 1) * hop, 8):
			var v := b.decode_s16(at + fr * frame) / 32768.0
			e += v * v
			n += 1
		energy.append(e / maxf(1.0, n))
	var best := -1.0
	var best_e := -1.0
	for w in range(0, energy.size() - 3):
		var s: float = energy[w] + energy[w + 1] + energy[w + 2] + energy[w + 3]
		if s > best_e:
			best_e = s
			best = w * 0.25
	return best


# ------------------------------------------------------------------ documents
func _documents() -> bool:
	var meta = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/documents/karsk_tunnels_documents.json"))
	if not kit.ok(meta is Dictionary, "karsk_tunnels_documents.json parses"):
		return false
	var by_item := {}
	for d in meta.get("documents", []):
		by_item[str(d.get("item_id"))] = d
	for item in DOC_ITEMS:
		if not kit.ok(by_item.has(item), "%s has a document" % item):
			continue
		var d: Dictionary = by_item[item]
		kit.eq(str(d.get("id")), DOC_ITEMS[item], "%s -> %s" % [item, DOC_ITEMS[item]])
		kit.eq(UiKit.doc_for_item(item), DOC_ITEMS[item], "InspectView finds the document of %s" % item)
		var img := _img("res://assets/ui/documents/%s.png" % DOC_ITEMS[item])
		if kit.ok(img != null, "%s image exists" % DOC_ITEMS[item]):
			kit.ok(img.get_width() * 3 <= 1060 and img.get_height() * 3 <= 760, "%s shows at 3x" % DOC_ITEMS[item])
			kit.eq(_ints(d.get("size")), [img.get_width(), img.get_height()], "%s: size in the metadata" % DOC_ITEMS[item])
		var alt := str(d.get("alt_key", ""))
		kit.ok(UiKit.has_key(alt), "%s: German caption %s" % [item, alt])
		var txt := UiKit.t(alt)
		kit.ok(txt.length() > 40 and (txt.ends_with(".") or txt.ends_with(".“")), "%s: caption reads as a sentence" % item)
		kit.ok(not txt.contains("\"") and not txt.contains(" - "), "%s: German typography („…“, –)" % item)
	var card: Dictionary = by_item.get("ev_c4_card_ru", {}).get("card", {})
	kit.eq(_ints(card.get("perforation", {}).get("pitch")), 6, "card No. 0417: shared perforation pitch")
	return true
