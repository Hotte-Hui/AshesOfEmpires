extends SceneTree
## Headless behaviour check for the Berlin archive ambient actors (env_berlin area, round 2).
##   godot --headless --path . --script res://tests/visual/berlin_actors_check.gd
## Loads scene.json, instances every declared actor exactly like Level._spawn_actors() does, steps them by
## hand (no real time needed) and checks: textures resolve, insignia decals follow the historical_symbols
## setting (neutral file / _hist file), pigeons flee from and return after the player, the mouse hides, the
## tram runs, clears the street and comes back, the clock draws hands.  Prints BERLIN_ACTORS_PASS / _FAIL.

const MANIFEST := "res://assets/environments/berlin_archive/scene.json"

var failures: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _fail(msg: String) -> void:
	failures.append(msg)
	print("  FAIL ", msg)


func _ok(msg: String) -> void:
	print("  ok   ", msg)


func _spawn(a: Dictionary, parent: Node) -> Node:
	var node: Node = load(str(a["scene"])).instantiate()
	(node as Node2D).position = Vector2(float(a["pos"][0]), float(a["pos"][1]))
	for k in a.get("props", {}):
		node.set(k, a["props"][k])
	parent.add_child(node)
	return node


func _step(node: Node, seconds: float, dt := 1.0 / 30.0) -> void:
	var t := 0.0
	while t < seconds:
		node._process(dt)
		t += dt


func _run() -> void:
	var m = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if typeof(m) != TYPE_DICTIONARY:
		_fail("scene.json does not parse")
		_finish()
		return
	var world := Node2D.new()
	root.add_child(world)
	var player := Node2D.new()
	player.add_to_group("player")
	player.position = Vector2(-5000, 300)
	world.add_child(player)
	var actors: Array = m.get("actors", [])
	_ok("%d actors declared" % actors.size())
	var by_scene := {}
	for a in actors:
		if not ResourceLoader.exists(str(a.get("scene", ""))):
			_fail("missing actor scene " + str(a.get("scene")))
			continue
		var n := _spawn(a, world)
		var key := str(a["scene"]).get_file().get_basename()
		if not by_scene.has(key):
			by_scene[key] = []
		by_scene[key].append(n)
		for k in a.get("props", {}):
			var v = a["props"][k]
			if v is String and (v as String).begins_with("res://") and not ResourceLoader.exists(v) \
					and not FileAccess.file_exists(v):
				_fail("%s: %s -> missing %s" % [key, k, v])
	await process_frame
	# ---- hotspots / spawns required by TECHNICAL_ARCHITECTURE 12.2
	var need := ["exp_lib_shelf_1", "exp_lib_shelf_2", "exp_lib_shelf_3", "exp_lib_shelf_4", "exp_lib_shelf_5",
		"exp_lib_hidden", "exp_card_catalogue", "exp_librarian_desk", "exp_reading_table", "exp_globe",
		"exp_poster_aufbau", "exp_photo", "exp_master_plan", "exp_pneumatic_tube", "exp_radio", "exp_mouse",
		"exp_pigeons", "exp_coat_stand", "exp_porter", "exp_clock", "exp_heater",
		"plan_a", "plan_b", "overlay_table", "emil", "obs_window", "obs_photo", "obs_notice"]
	var hs: Dictionary = m.get("hotspots", {})
	var miss := need.filter(func(n): return not hs.has(n))
	if miss.is_empty():
		_ok("all %d hotspots of 12.2 + canonical present" % need.size())
	else:
		_fail("missing hotspots %s" % str(miss))
	for sp in ["SP_M1_Arrival", "SP_M1_Office"]:
		if not m.get("spawns", {}).has(sp):
			_fail("missing spawn " + sp)
	# ---- insignia decals (scene.json "decals", built by layer_stack.gd through Symbols.pick)
	var settings := root.get_node_or_null("/root/Settings")
	var base := MANIFEST.get_base_dir() + "/"
	var decals: Array = m.get("decals", [])
	for d in decals:
		var f := base + str(d.get("file", ""))
		var h := f.get_basename() + "_hist.png"
		for p in [f, h]:
			if not (ResourceLoader.exists(p) or FileAccess.file_exists(p)):
				_fail("decal file missing " + p)
		if bool(d.get("lit", false)) and bool(d.get("normal", false)):
			for p in [f.get_basename() + "_n.png", h.get_basename() + "_n.png"]:
				if not (ResourceLoader.exists(p) or FileAccess.file_exists(p)):
					_fail("decal normal map missing " + p)
		if settings:
			settings.values["historical_symbols"] = true
			if Symbols.pick(f) != h:
				_fail("Symbols.pick does not choose the _hist variant for " + f)
			settings.values["historical_symbols"] = false
			if Symbols.pick(f) != f:
				_fail("Symbols.pick does not keep the neutral file for " + f)
			settings.values["historical_symbols"] = true
		if not ["room", "ext_near"].has(str(d.get("layer", ""))):
			_fail("decal %s on unexpected layer %s" % [str(d.get("name")), str(d.get("layer"))])
	if decals.size() < 4:
		_fail("expected >= 4 insignia decals, found %d" % decals.size())
	else:
		_ok("insignia decals: %d sites, neutral + _hist files, Symbols.pick switches" % decals.size())
	# ---- pigeons
	for pg in by_scene.get("BerlinPigeons", []):
		_step(pg, 1.0)
		if not pg.present:
			_fail("pigeons not present at start")
		player.position = Vector2(pg.global_position.x + 10, 300)
		_step(pg, 0.2)
		if pg.present:
			_fail("pigeons did not take off when the player came close")
		_step(pg, 3.0)
		var gone: bool = pg.birds.all(func(b): return str(b["state"]) == "away")
		if not gone:
			_fail("pigeons not out of sight after 3 s")
		player.position = Vector2(-5000, 300)
		_step(pg, 45.0)
		var back: bool = pg.birds.all(func(b): return str(b["state"]) != "away")
		if not (pg.present and back):
			_fail("pigeons did not come back")
		else:
			_ok("pigeons: take off near the player, return later")
	# ---- mouse
	for ms in by_scene.get("BerlinMouse", []):
		player.position = Vector2(-5000, 300)
		var seen := false
		for i in 600:
			ms._process(1.0 / 30.0)
			if ms.state != "hidden":
				seen = true
				break
		if not seen:
			_fail("mouse never peeked in 20 s")
		player.position = Vector2(ms.global_position.x + 5, 300)
		ms._process(1.0 / 30.0)
		if ms.state != "hidden":
			_fail("mouse did not hide from the player")
		else:
			_ok("mouse: peeks out, hides when the player comes close")
		player.position = Vector2(-5000, 300)
	# ---- tram
	for tr in by_scene.get("BerlinTram", []):
		_step(tr, float(tr.first_delay) + 0.5)
		if not tr.running:
			_fail("tram did not start after first_delay")
		_step(tr, 60.0)
		var runs := 0
		var was := false
		for i in 3600:
			tr._process(1.0 / 30.0)
			if tr.running and not was:
				runs += 1
			was = tr.running
		if runs < 2:
			_fail("tram ran %d times in 120 s (expected >= 2)" % runs)
		else:
			_ok("tram: %d departures in 120 s (period %.0f s)" % [runs, float(tr.period)])
	# ---- clocks
	for ck in by_scene.get("BerlinClock", []):
		ck._process(0.016)
		var img: Image = ck._img
		var used := 0
		for y in img.get_height():
			for x in img.get_width():
				if img.get_pixel(x, y).a > 0.5:
					used += 1
		if used < 4:
			_fail("clock hands not drawn")
	if not by_scene.get("BerlinClock", []).is_empty():
		_ok("clocks draw their hands")
	# ---- remaining actors at least run a minute without errors
	for key in ["BerlinRadiator", "BerlinRadio", "BerlinPapers", "BerlinTube", "BerlinAnim"]:
		for n in by_scene.get(key, []):
			_step(n, 60.0)
		if by_scene.has(key):
			_ok("%s x%d stepped 60 s" % [key, by_scene[key].size()])
		else:
			_fail("no %s declared" % key)
	_finish()


func _finish() -> void:
	if failures.is_empty():
		print("BERLIN_ACTORS_PASS")
		quit(0)
	else:
		print("BERLIN_ACTORS_FAIL %d" % failures.size())
		quit(1)
