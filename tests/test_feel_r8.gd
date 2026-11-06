extends RefCounted
## Round 8 feel / polish pass (owner feel_r8):
##  * ambient walkers (scripts/actors/ambient_walker.gd + assets/environments/<env>/walkers.json) in the Palais,
##    the station and the Berlin reading room: data complete, variant sheets fit their source silhouettes, lanes
##    sort correctly, walkers walk / pause / turn deterministically and give way to the player
##  * decor loops start at their own deterministic phase (scripts/levels/layer_stack.gd)
##  * station side-task payoff (scripts/levels/veltrava_station/station_thaw.gd): leak hidden once the coupling is
##    thawed, live peephole + wave + thaw sequence, seamless art (frame 0 = the layer)
##  * MemoryView: full dimmer, every card row reachable by the arrows at 150 % text, the reason of a broken
##    main-menu memory shown in the view; Journal: index tabs wrap instead of shrinking below 20 px
##  * art: living portraits of the evicted Berlin family, Voronova's lighter hat edge, the richer t3 compartment

const Kit := preload("res://tests/support/test_kit.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const THAW_SCENE := "res://scenes/levels/veltrava_station/StationThaw.tscn"
const VIEW_SCENE := "res://scenes/ui/MemoryView.tscn"
const JOURNAL_SCENE := "res://scenes/ui/Journal.tscn"
const THEME := "res://assets/ui/theme.tres"
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const THAW_IDS := ["veltrava.task.heating.ask", "veltrava.task.heating.coupling", "veltrava.task.heating.kettle",
	"veltrava.task.heating.thaw"]
const WALKERS_SCENE := "res://scenes/actors/AmbientWalkers.tscn"
const ENVS := {"veltrava_hall": "side", "veltrava_station": "oblique", "berlin_archive": "side"}
## speaking characters of each level: a walker using one of these sheets must bring its own variant
const SPEAKERS := {
	"veltrava_hall": ["kessler", "elena", "voronova", "typist", "journalist", "alexei", "konrad"],
	"veltrava_station": ["conductor", "elena", "border_officer", "voronova", "konrad", "alexei"],
	"berlin_archive": ["emil", "clerk", "porter", "librarian", "konrad"],
}

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("walkers_declared_and_complete", _walkers_complete)
	kit.run_case("walker_variants_fit_their_sheets", _variants_fit)
	kit.run_case("walker_lanes_sort_correctly", _lanes)
	kit.run_case("walkers_walk_pause_turn_deterministic", _walk_run)
	kit.run_case("walkers_give_way_to_the_player", _give_way)
	kit.run_case("decal_loops_start_out_of_sync", _decal_phase)
	kit.run_case("car3_thaw_art_is_seamless", _thaw_art)
	kit.run_case("car3_thaw_live_sequence", _thaw_live)
	kit.run_case("car3_thawed_on_load_after_the_task", _thaw_on_load)
	kit.run_case("memory_view_dims_fully", _mv_dimmer)
	kit.run_case("memory_view_rows_reachable_at_150", _mv_focus)
	kit.run_case("memory_view_says_why_a_memory_is_broken", _mv_broken)
	kit.run_case("journal_tabs_wrap_instead_of_shrinking", _journal_tabs)
	kit.run_case("berlin_family_portraits", _family_portraits)
	kit.run_case("voronova_hat_edge_lighter", _voronova_edge)
	kit.run_case("trains_t3_compartment_enriched", _t3_room)
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ helpers
static func _json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


static func _manifest(env: String) -> Dictionary:
	var m = _json("res://assets/environments/%s/scene.json" % env)
	return m if m is Dictionary else {}


static func _walker_entry(env: String) -> Dictionary:
	for a in _manifest(env).get("actors", []):
		if a is Dictionary and str(a.get("scene", "")) == WALKERS_SCENE:
			return a
	return {}


static func _specs(env: String) -> Array:
	var d = _json("res://assets/environments/%s/walkers.json" % env)
	return d.get("walkers", []) if d is Dictionary else []


## Mounts the manager like Level._spawn_actors does (props set before _ready).
func _spawn(env: String, holder: Node) -> Node2D:
	var entry := _walker_entry(env)
	var node: Node2D = load(WALKERS_SCENE).instantiate()
	for k in entry.get("props", {}):
		node.set(k, entry["props"][k])
	holder.add_child(node)
	return node


func _fake_player(holder: Node, at: Vector2) -> Node2D:
	var p := Node2D.new()
	p.add_to_group("player")
	p.position = at
	holder.add_child(p)
	return p


## Highest footprint (base_y) of the props standing along x0..x1 (the walker's stretch of the room).
static func _max_prop_base(m: Dictionary, x0: float, x1: float) -> float:
	var top := -INF
	for P in m.get("props", []):
		if not (P is Dictionary and P.has("base_y")):
			continue
		var px := float(P.get("pos", [0, 0])[0])
		var img := Image.load_from_file(ProjectSettings.globalize_path(
			"res://assets/environments/%s/%s" % [str(m.get("id", "")), str(P.get("file", ""))]))
		var w := float(img.get_width()) if img != null else 64.0
		if px + w >= x0 and px <= x1:
			top = maxf(top, float(P["base_y"]))
	return top


# ------------------------------------------------------------------ cases
func _walkers_complete() -> bool:
	for env in ENVS:
		var entry := _walker_entry(env)
		if not kit.ok(not entry.is_empty(), "%s: scene.json declares the AmbientWalkers actor" % env):
			continue
		var data := str(entry.get("props", {}).get("data", ""))
		kit.eq(data, "res://assets/environments/%s/walkers.json" % env, "%s: walker data path" % env)
		var specs := _specs(env)
		kit.ok(specs.size() >= 2 and specs.size() <= 3, "%s: 2-3 walkers (%d)" % [env, specs.size()])
		var ids := {}
		for s in specs:
			var id := str(s.get("id", ""))
			kit.ok(id != "" and not ids.has(id), "%s: unique walker id '%s'" % [env, id])
			ids[id] = true
			var ch := str(s.get("char", ""))
			kit.ok(FileAccess.file_exists("res://assets/characters/%s/sheet.json" % ch), "%s: sheet of '%s'" % [id, ch])
			kit.ok((s.get("path", []) as Array).size() >= 2, "%s: path of >= 2 points" % id)
			if ch in SPEAKERS[env]:
				kit.ok(str(s.get("sheet", "")) != "", "%s: '%s' speaks in %s -> the walker needs its own variant" % [id, ch, env])
			var sp := float(s.get("speed", 20))
			kit.ok(sp >= 10.0 and sp <= 30.0, "%s: unhurried speed %.0f px/s (player walks 45)" % [id, sp])
	return true


func _variants_fit() -> bool:
	for env in ENVS:
		for s in _specs(env):
			var v := str(s.get("sheet", ""))
			if v == "":
				continue
			var vp := "res://assets/environments/%s/%s" % [env, v]
			var src := "res://assets/characters/%s/sheet.png" % str(s["char"])
			var a := Image.load_from_file(ProjectSettings.globalize_path(vp))
			var b := Image.load_from_file(ProjectSettings.globalize_path(src))
			if not (kit.ok(a != null, "variant %s readable" % vp) and kit.ok(b != null, "source %s readable" % src)):
				continue
			if not kit.eq(a.get_size(), b.get_size(), "%s: same size as %s" % [v, src]):
				continue
			a.convert(Image.FORMAT_RGBA8)
			b.convert(Image.FORMAT_RGBA8)
			var da := a.get_data()
			var db := b.get_data()
			var diff_alpha := 0
			var diff_rgb := 0
			for i in range(0, da.size(), 4):
				if (da[i + 3] > 0) != (db[i + 3] > 0):
					diff_alpha += 1
				elif da[i + 3] > 0 and (da[i] != db[i] or da[i + 1] != db[i + 1] or da[i + 2] != db[i + 2]):
					diff_rgb += 1
			kit.eq(diff_alpha, 0, "%s: silhouette identical to %s (its normal map is reused)" % [v, src])
			kit.ok(diff_rgb > 800, "%s: clearly recoloured (%d px differ)" % [v, diff_rgb])
	return true


func _lanes() -> bool:
	for env in ENVS:
		var m := _manifest(env)
		var walk: Array = m.get("walkable", [])
		var ymin := INF
		var ymax := -INF
		for q in walk:
			ymin = minf(ymin, float(q[1]))
			ymax = maxf(ymax, float(q[1]))
		for s in _specs(env):
			var x0 := INF
			var x1 := -INF
			for p in s.get("path", []):
				x0 = minf(x0, float(p[0]))
				x1 = maxf(x1, float(p[0]))
			var top := _max_prop_base(m, x0 - 20.0, x1 + 20.0)
			for p in s.get("path", []):
				var y := float(p[1])
				if ENVS[env] == "side":
					# behind the walk band (player + speakers always in front), in front of every prop
					kit.ok(y > top and y < ymin, "%s: lane y %.1f between props (%.0f) and the walk band (%.0f)" % [s["id"], y, top, ymin])
				else:
					kit.ok(y >= ymin + 4.0 and y <= ymax - 2.0, "%s: path y %.0f on the platform" % [s["id"], y])
			if ENVS[env] == "oblique":
				kit.ok(float(s.get("give_way", 0)) > 0.0 and float(s.get("dodge", 0)) > 0.0,
					"%s: gives way on the open platform" % s["id"])
	var holder := Node2D.new()
	kit.mount(holder)
	var mgr := _spawn("veltrava_hall", holder)
	kit.ok(mgr.y_sort_enabled, "manager is y-sorted (its walkers sort with the Playfield)")
	kit.eq((mgr.get("list") as Array).size(), _specs("veltrava_hall").size(), "every hall walker built")
	for w in mgr.get("list"):
		kit.ok(w.get_parent() == mgr and w.rig != null and w.rig.sprite != null, "%s has a sprite" % w.id)
		kit.ok(w.rig.sprite.texture is CanvasTexture and (w.rig.sprite.texture as CanvasTexture).normal_texture != null,
			"%s keeps the source normal map" % w.id)
		kit.ok(not w.is_in_group("npcs") and not w.is_in_group("interactables"), "%s is in no gameplay group" % w.id)
	holder.free()
	return true


## Records (position, state) every step for `secs` at 20 fps.
func _record(env: String, secs: float, player_at := Vector2(-9999, -9999)) -> Dictionary:
	var holder := Node2D.new()
	kit.mount(holder)
	_fake_player(holder, player_at)
	var mgr := _spawn(env, holder)
	var tracks := {}
	for w in mgr.get("list"):
		tracks[w.id] = {"pos": [], "states": {}, "min_x": INF, "max_x": -INF}
	for i in int(secs * 20.0):
		mgr._process(0.05)
		for w in mgr.get("list"):
			w.rig._process(0.05)
			w._process(0.05)
			var t: Dictionary = tracks[w.id]
			(t["pos"] as Array).append(w.position)
			t["states"][w.state] = true
			t["min_x"] = minf(float(t["min_x"]), w.position.x)
			t["max_x"] = maxf(float(t["max_x"]), w.position.x)
	holder.free()
	return tracks


func _walk_run() -> bool:
	for env in ENVS:
		var a := _record(env, 90.0)
		var b := _record(env, 90.0)
		for id in a:
			var t: Dictionary = a[id]
			kit.ok(float(t["max_x"]) - float(t["min_x"]) > 120.0, "%s walks (covers %.0f px in 90 s)" % [id, float(t["max_x"]) - float(t["min_x"])])
			kit.ok(t["states"].has("pause"), "%s pauses within 90 s" % id)
			kit.ok(t["states"].has("turn"), "%s turns round softly within 90 s" % id)
			kit.ok(a[id]["pos"] == b[id]["pos"], "%s: identical track on a second run (deterministic)" % id)
	return true


func _give_way() -> bool:
	# the porter heads for the kiosk; the player stands right on his path in front of him
	var holder := Node2D.new()
	kit.mount(holder)
	var player := _fake_player(holder, Vector2(-9999, -9999))
	var mgr := _spawn("veltrava_station", holder)
	var w: Node2D = null
	for x in mgr.get("list"):
		if x.id == "station_porter":
			w = x
	if not kit.ok(w != null, "station porter built"):
		return true
	# put him on his second segment heading right and stand the player 26 px ahead on the path
	w.from_i = 1
	w.to_i = 2
	w.base = w.pts[1].lerp(w.pts[2], 0.3)
	w.offset = 0.0
	w.offset_target = 0.0
	w.state = "walk"
	w._left = false
	w.rig.set_flip(false)
	var u: Vector2 = (w.pts[2] - w.pts[1]).normalized()
	player.position = w.base + u * 26.0
	var closest := INF
	var stepped := false
	var yielded := false
	for i in 200:                     # 10 s
		mgr._process(0.05)
		w._process(0.05)
		closest = minf(closest, w.position.distance_to(player.position))
		stepped = stepped or absf(w.offset) > 6.0
		yielded = yielded or w.state == "yield"
	kit.ok(stepped or yielded, "porter steps aside or waits for the player")
	kit.ok(closest >= 10.0, "porter never walks into the player (closest %.1f px)" % closest)
	# the player leaves: he gets back onto his path
	player.position = Vector2(-9999, -9999)
	for i in 200:
		mgr._process(0.05)
		w._process(0.05)
	kit.ok(absf(w.offset) < 0.5, "back on his path once the player is gone (offset %.1f)" % w.offset)
	# a player standing still on the path in a dead end (no room for a step) makes him turn back
	w.dodge = 0.0
	w.from_i = 1
	w.to_i = 2
	w.base = w.pts[1].lerp(w.pts[2], 0.5)
	w.state = "walk"
	var before_to: int = w.to_i
	player.position = w.base + (w.pts[2] - w.pts[1]).normalized() * 20.0
	for i in 100:                     # 5 s
		mgr._process(0.05)
		w._process(0.05)
	kit.ok(w.to_i != before_to, "waited, then turned back (heading for point %d)" % w.to_i)
	holder.free()
	return true


func _decal_phase() -> bool:
	var a := LayerStack.loop_t0({}, "lamp@10,20", 6, 6.0)
	var b := LayerStack.loop_t0({}, "lamp@10,20", 6, 6.0)
	var c := LayerStack.loop_t0({}, "lamp@40,20", 6, 6.0)
	kit.eq(a, b, "same decal -> same start phase (deterministic)")
	kit.ok(a != c, "two decals of one file at different spots start at different phases")
	kit.ok(a >= 0.0 and a < 1.0 and c >= 0.0 and c < 1.0, "phase inside one loop (6 frames at 6 fps = 1 s)")
	kit.eq(LayerStack.loop_t0({"t0": 0.4}, "lamp@10,20", 6, 6.0), 0.4, "explicit t0 wins")
	kit.eq(LayerStack.loop_t0({}, "still@0,0", 1, 6.0), 0.0, "still decal has no phase")
	kit.eq(LayerStack.name_hash("heater_leak_23"), LayerStack.name_hash("heater_leak_23"), "stable hash")
	# a real manifest: the Palais life strips no longer start on frame 0 together
	var ls := LayerStack.new()
	var pf := Node2D.new()
	var li := Node2D.new()
	var fx := Node2D.new()
	ls.add_child(pf)
	ls.add_child(li)
	ls.add_child(fx)
	kit.mount(ls)
	ls.build(_manifest("veltrava_hall"), "res://assets/environments/veltrava_hall", pf, li, fx)
	var phases := {}
	var anims: Array = ls.get("_anims")
	for an in anims:
		phases[snappedf(float(an["t"]), 0.001)] = true
	kit.ok(anims.size() >= 6, "Palais has looping decals (%d)" % anims.size())
	kit.ok(phases.size() >= anims.size() / 2 + 1, "their start phases differ (%d distinct of %d strips)" % [phases.size(), anims.size()])
	return true


# ------------------------------------------------------------------ station thaw
class FakeLevel extends Node2D:
	var backdrop: Node2D
	var manifest: Dictionary = {}
	var playfield: Node2D


## Minimal station: the train_near layer + the heater decal built by the real LayerStack, a Playfield and the
## StationThaw actor spawned like Level._spawn_actors does.
func _thaw_level() -> FakeLevel:
	var m := _manifest("veltrava_station")
	var sub := {"layers": [], "decals": m.get("decals", [])}
	for L in m.get("layers", []):
		if str(L.get("name", "")) == "train_near":
			sub["layers"].append(L)
	var lvl := FakeLevel.new()
	lvl.manifest = m
	lvl.backdrop = LayerStack.new()
	lvl.add_child(lvl.backdrop)
	lvl.playfield = Node2D.new()
	lvl.add_child(lvl.playfield)
	var li := Node2D.new()
	var fx := Node2D.new()
	lvl.add_child(li)
	lvl.add_child(fx)
	kit.mount(lvl)
	lvl.backdrop.build(sub, "res://assets/environments/veltrava_station", lvl.playfield, li, fx)
	var entry := {}
	for a in m.get("actors", []):
		if a is Dictionary and str(a.get("scene", "")) == THAW_SCENE:
			entry = a
	kit.ok(not entry.is_empty(), "station scene.json declares StationThaw")
	var node: Node2D = load(THAW_SCENE).instantiate()
	for k in entry.get("props", {}):
		node.set(k, entry["props"][k])
	lvl.playfield.add_child(node)
	return lvl


func _thaw_actor(lvl: FakeLevel) -> Node:
	for c in lvl.playfield.get_children():
		if c.has_method("play_thaw"):
			return c
	return null


func _thaw_art() -> bool:
	var layer := Image.load_from_file(ProjectSettings.globalize_path("res://assets/environments/veltrava_station/train_near.png"))
	var band := Image.load_from_file(ProjectSettings.globalize_path("res://assets/environments/veltrava_station/thaw/car3_thaw.png"))
	var peep := Image.load_from_file(ProjectSettings.globalize_path("res://assets/environments/veltrava_station/thaw/car3_peephole.png"))
	if not (kit.ok(layer != null and band != null and peep != null, "thaw art readable")):
		return true
	kit.eq(band.get_size(), Vector2i(164 * 5, 19), "band strip: 5 frames of 164 x 19")
	kit.eq(peep.get_size(), Vector2i(18 * 10, 19), "peephole strip: 10 frames of 18 x 19")
	for pair in [[band, Vector2i(357, 25), 164], [peep, Vector2i(478, 25), 18]]:
		var img: Image = pair[0]
		var at: Vector2i = pair[1]
		var w: int = pair[2]
		var same := true
		for y in 19:
			for x in w:
				if img.get_pixel(x, y) != layer.get_pixel(at.x + x, at.y + y):
					same = false
		kit.ok(same, "frame 0 at layer %s is the painted layer itself (no seam)" % str(at))
	# the last band frame really changed the frosted windows (W5 / W6 interior differs from frame 0)
	var changed := 0
	for y in 19:
		for x in range(98, 140):
			if band.get_pixel(4 * 164 + x, y) != band.get_pixel(x, y):
				changed += 1
	kit.ok(changed > 120, "windows 5 + 6 are thawed in the last frame (%d px changed)" % changed)
	for f in ["car3_thaw", "car3_peephole"]:
		for suf in ["_n", "_e"]:
			kit.ok(FileAccess.file_exists("res://assets/environments/veltrava_station/thaw/%s%s.png" % [f, suf]), "%s%s.png exists" % [f, suf])
	return true


func _thaw_live() -> bool:
	var before: Dictionary = Explore.state()
	Explore.restore({"found": [], "cards": []})
	var lvl := _thaw_level()
	var th := _thaw_actor(lvl)
	if not kit.ok(th != null, "StationThaw spawned"):
		Explore.restore(before)
		return true
	kit.eq(str(th.state), "frozen", "frozen while the task is open")
	kit.ok(th.leak_visible(), "the steam leak hisses")
	kit.eq(th.band_frame(), -1, "no overlay while frozen")
	th._on_found("veltrava.task.heating.ask")
	kit.eq(str(th.state), "frozen", "other finds change nothing")
	th._on_found("veltrava.task.heating.thaw")
	var peeps: Array = []
	var bands: Array = []
	var leak_gone_at := -1.0
	for i in 600:                    # 30 s at 20 fps
		th._process(0.05)
		var pf: int = th.peep_frame()
		if pf >= 0 and (peeps.is_empty() or peeps[-1] != pf):
			peeps.append(pf)
		var bf: int = th.band_frame()
		if bf >= 0 and (bands.is_empty() or bands[-1] != bf):
			bands.append(bf)
		if leak_gone_at < 0.0 and not th.leak_visible():
			leak_gone_at = i * 0.05
	kit.ok(leak_gone_at >= 0.0 and leak_gone_at <= 2.0, "the leak dies down first (gone after %.2f s)" % leak_gone_at)
	kit.eq(peeps.slice(0, 6), [0, 1, 2, 3, 4, 5], "a hand wipes a peephole (frames 0-4), then a face (5)")
	kit.ok(peeps.count(6) >= 2 and peeps.count(7) >= 2, "and waves (6/7 alternate): %s" % str(peeps))
	kit.eq(bands, [1, 2, 3, 4], "then the frost recedes in stages to the thawed car")
	kit.eq(str(th.state), "thawed", "sequence ends thawed")
	kit.eq(th.peep_frame(), -1, "peephole overlay gone at the end")
	lvl.free()
	Explore.restore(before)
	return true


func _thaw_on_load() -> bool:
	var before: Dictionary = Explore.state()
	Explore.restore({"found": THAW_IDS + ["veltrava.task.heating.return"], "cards": []})
	kit.eq(str(Explore.task_state("veltrava.task.heating").get("state", "")), "done", "task done in this state")
	var lvl := _thaw_level()
	var th := _thaw_actor(lvl)
	if kit.ok(th != null, "StationThaw spawned"):
		kit.eq(str(th.state), "thawed", "loaded thawed")
		kit.ok(not th.leak_visible(), "heater_leak_23 hidden on level load once the task is done")
		kit.eq(th.band_frame(), 4, "car 3 shows its thawed windows")
		var leak = lvl.backdrop.get("decals_by_name").get("heater_leak_23")
		kit.ok(leak != null and not leak.visible, "the decal itself is hidden (level.backdrop.decals_by_name)")
	lvl.free()
	Explore.restore(before)
	return true


# ------------------------------------------------------------------ MemoryView / Journal
class MockMem extends RefCounted:
	var raw: Dictionary = {}

	func snapshot_raw(id: String) -> String:
		return str(raw.get(id, ""))


class MockGame extends Node:
	var cards: Array = []
	var memories := MockMem.new()
	var travelled: Array = []

	func memory_scenes(_context := "game") -> Array:
		return cards

	func memory_films(_context := "game") -> Array:
		return []

	func can_travel(_from_menu := false) -> bool:
		return true

	func travel_to_memory(id: String, from_menu := false) -> bool:
		travelled.append([id, from_menu])
		return true


func _mock_game(n_open: int) -> MockGame:
	var g: MockGame = kit.track(MockGame.new())
	for i in n_open + 1:
		var id := "L_FAKE_%d" % i
		g.cards.append({"id": id, "unlocked": true, "current": i == 1, "place": "Ort %d mit einem langen Namen" % i,
			"date": "Januar 1964", "chapter": "Kapitel %d · Eine lange Kapitelzeile" % (i + 1), "who": "alexei",
			"thumb": "", "found": i, "total": 20})
	UIKit.overrides["Game"] = g
	return g


func _view(holder_size := Vector2(1920, 1080)) -> Control:
	var holder := Control.new()
	holder.theme = load(THEME)
	holder.size = holder_size
	kit.mount(holder)
	var v: Control = load(VIEW_SCENE).instantiate()
	holder.add_child(v)
	return v


func _mv_dimmer() -> bool:
	_mock_game(2)
	var v := _view()
	var dim: ColorRect = null
	for c in v.get_children():
		if c is ColorRect:
			dim = c
			break
	kit.ok(dim != null and is_equal_approx(dim.color.a, 1.0), "the panel behind is dimmed fully (alpha %.2f)" % (dim.color.a if dim else -1.0))
	UIKit.overrides.erase("Game")
	return true


func _mv_focus() -> bool:
	var st := get_node_settings()
	var old = st.values.get("text_scale", 1.0) if st != null else 1.0
	if st != null:
		st.values["text_scale"] = 1.5         # this run only (never saved)
	_mock_game(7)                             # 8 cards (one is the current place): rows 3 / 3 / 2
	var v := _view()
	v.open("game")
	var rows: Array = v._rows.get_children()
	kit.ok(rows.size() >= 3, "three card rows (%d)" % rows.size())
	var row_of := {}
	for r in rows.size():
		for card in rows[r].get_children():
			for b in v.buttons.values():
				if b.get_parent() == card:
					row_of[b] = r
	var seen := {}
	var queue: Array = [v.buttons.values()[0]]
	while not queue.is_empty():
		var b: Button = queue.pop_front()
		if seen.has(b):
			continue
		seen[b] = true
		for side in ["focus_neighbor_bottom", "focus_neighbor_top", "focus_neighbor_left", "focus_neighbor_right"]:
			var path: NodePath = b.get(side)
			var t: Node = b.get_node_or_null(path) if not path.is_empty() else null
			if t is Button and not seen.has(t):
				queue.append(t)
	kit.eq(seen.size(), v.buttons.size(), "every choosable card is reachable with the arrows")
	var down_ok := true
	for b in v.buttons.values():
		if int(row_of.get(b, 0)) == 0:
			var t: Node = b.get_node_or_null(b.focus_neighbor_bottom)
			down_ok = down_ok and t is Button and int(row_of.get(t, -1)) == 1
	kit.ok(down_ok, "Down from the first row lands in the second row")
	var last: Button = null
	for b in v.buttons.values():
		if int(row_of.get(b, 0)) == rows.size() - 1:
			last = b
	kit.ok(last != null and last.get_node_or_null(last.focus_neighbor_bottom) == last, "Down in the last row stays put")
	kit.ok(v._scroll.follow_focus, "the scroll follows the focused card")
	v.close()
	if st != null:
		st.values["text_scale"] = old
	UIKit.overrides.erase("Game")
	return true


func get_node_settings() -> Node:
	return Kit.root().get_node_or_null("Settings") if Kit.root() != null else null


func _mv_broken() -> bool:
	var g := _mock_game(2)
	g.memories.raw = {"L_FAKE_0": "{ kaputt", "L_FAKE_2": ""}
	var v := _view()
	v.open("menu")
	kit.ok(not v.activate("L_FAKE_0"), "a broken record does not travel")
	kit.eq(g.travelled, [], "travel_to_memory is never asked (its toast would surface later, out of context)")
	var note: String = v.notice_text()
	kit.ok(note.begins_with(UIKit.t("ui.memories.broken")), "the view says it cannot be opened: %s" % note)
	kit.ok(note.contains(UIKit.t("sys.save.err.malformed")), "... and why (the save check's reason)")
	kit.ok(not v.activate("L_FAKE_2"), "a missing record does not travel")
	kit.ok(v.notice_text().contains(UIKit.t("ui.memories.broken_reason.missing")), "missing record reason shown")
	v.show_page("films")
	kit.eq(v.notice_text(), "", "the notice goes with the page")
	v.close()
	v.open("game")
	g.memories.raw = {}
	kit.ok(v.activate("L_FAKE_0"), "in the game (no recorded state needed) the trip starts")
	v.close()
	UIKit.overrides.erase("Game")
	return true


func _journal_tabs() -> bool:
	var holder := Control.new()
	holder.theme = load(THEME)
	holder.size = Vector2(1920, 1080)
	kit.mount(holder)
	var j: Control = load(JOURNAL_SCENE).instantiate()
	holder.add_child(j)
	var row: Control = (j._tab_buttons["objectives"] as Button).get_parent()
	kit.ok(row is HFlowContainer, "the index tabs sit in a flow row")
	j._tab_counts = {"objectives": 9, "tasks": 9, "evidence": 99, "people": 99, "decisions": 9, "discoveries": 999, "history": 99}
	j._fit_tabs()
	var fs: int = (j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size")
	kit.ok(fs >= 20, "late-game labels stay at >= 20 px (%d)" % fs)
	kit.ok(j.tabs_wrapped(), "... and wrap onto a second row of tabs instead")
	j._tab_counts = {"objectives": 2, "tasks": 1, "evidence": 3, "people": 1}
	j._fit_tabs()
	kit.ok(not j.tabs_wrapped(), "early game: one row")
	kit.ok((j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size") >= 20, "early game: >= 20 px")
	j._tab_counts = {}
	j._fit_tabs()
	kit.ok(not j.tabs_wrapped(), "no counters: one row")
	kit.eq((j._tab_buttons["objectives"] as Button).get_theme_font_size("font_size"), 24, "no counters: theme size")
	return true


# ------------------------------------------------------------------ art
static func _img(path: String) -> Image:
	var img := Image.load_from_file(ProjectSettings.globalize_path(path))
	if img != null:
		img.convert(Image.FORMAT_RGBA8)
	return img


static func _region_differs(img: Image, a: Rect2i, b: Rect2i) -> bool:
	var n := 0
	for y in a.size.y:
		for x in a.size.x:
			if img.get_pixel(a.position.x + x, a.position.y + y) != img.get_pixel(b.position.x + x, b.position.y + y):
				n += 1
	return n > 40


func _family_portraits() -> bool:
	for id in ["berlin_mother", "berlin_father"]:
		var dir := "res://assets/characters/%s/" % id
		var p = _json(dir + "portrait.json")
		if not kit.ok(p is Dictionary, "%s: portrait.json (no more silhouette placeholder)" % id):
			continue
		kit.eq(p.get("size"), [112.0, 112.0], "%s: 112 px busts" % id)
		kit.eq(p.get("expressions"), ["neutral", "concerned", "determined", "surprised"], "%s: four expressions" % id)
		var anim: Dictionary = p.get("anim", {}) if p.get("anim") is Dictionary else {}
		kit.eq(str(anim.get("file", "")), "portrait_anim.png", "%s: living portrait like the round-2 cast" % id)
		var strip := _img(dir + "portrait.png")
		var grid := _img(dir + "portrait_anim.png")
		if not kit.ok(strip != null and grid != null, "%s: portrait images load" % id):
			continue
		kit.eq(strip.get_size(), Vector2i(448, 112), "%s: rest strip 4 x 112" % id)
		kit.eq(grid.get_size(), Vector2i(448, 112 * (anim.get("rows", []) as Array).size()), "%s: grid size" % id)
		for e in [1, 2, 3]:
			kit.ok(_region_differs(strip, Rect2i(0, 0, 112, 112), Rect2i(112 * e, 0, 112, 112)), "%s: expression %d differs from neutral" % [id, e])
		kit.ok(_region_differs(grid, Rect2i(0, 0, 112, 112), Rect2i(0, 224, 112, 112)), "%s: the mouth opens (talk_open)" % id)
		kit.ok(_region_differs(grid, Rect2i(0, 0, 112, 112), Rect2i(0, 336, 112, 112)), "%s: the eyes close (blink)" % id)
	return true


func _voronova_edge() -> bool:
	var sheet := _img("res://assets/characters/voronova/sheet.png")
	var meta = _json("res://assets/characters/voronova/sheet.json")
	if not kit.ok(sheet != null and meta is Dictionary, "voronova sheet"):
		return true
	for an in ["idle_side", "idle_front", "walk_side", "talk_side"]:
		var r := int(meta["anims"][an]["row"])
		var top := -1
		for y in 56:
			for x in 32:
				if sheet.get_pixel(x, r * 56 + y).a > 0.5:
					top = y
					break
			if top >= 0:
				break
		var lum := func(y: int) -> float:
			var sum := 0.0
			var n := 0
			for x in 32:
				var c := sheet.get_pixel(x, r * 56 + y)
				if c.a > 0.5:
					sum += c.get_luminance()
					n += 1
			return sum / maxf(1.0, float(n))
		var edge: float = lum.call(top + 3)
		var body := maxf(lum.call(top), maxf(lum.call(top + 1), lum.call(top + 2)))
		kit.ok(edge > body + 0.04, "%s: the hat's lowest row is the lighter fur edge (%.2f vs %.2f)" % [an, edge, body])
	return true


func _t3_room() -> bool:
	var ia := _img("res://assets/cinematics/ch3/trains/int_alexei.png")
	var ik := _img("res://assets/cinematics/ch3/trains/int_konrad.png")
	var rf := _img("res://assets/cinematics/ch3/trains/roomflare_a.png")
	if not kit.ok(ia != null and ik != null and rf != null, "t3 art loads"):
		return true
	# the match cut (t2) needs the same glass opening in both cars: nothing new may cover the open glass (only the
	# frost specks and the objects standing on the table differ, as before round 8: 52 px in this window)
	var diff := 0
	for y in range(96, 200):
		for x in range(200, 440):
			if (ia.get_pixel(x, y).a < 0.5) != (ik.get_pixel(x, y).a < 0.5):
				diff += 1
	kit.ok(diff <= 60, "glass opening unchanged against Konrad's car (t2 match cut): %d px differ" % diff)
	var reds := 0
	for y in range(56, 70):
		for x in range(150, 490):
			var c := ia.get_pixel(x, y)
			if c.r > c.g * 1.5 and c.r > c.b * 1.5 and c.r > 0.25:
				reds += 1
	kit.ok(reds > 40, "the pelmet carries its red cross-stitch band (%d px)" % reds)
	var bright := 0
	for y in range(236, 262):
		for x in range(600, 636):
			if ia.get_pixel(x, y).get_luminance() > 0.45:
				bright += 1
	kit.ok(bright > 60, "a white pillow on the right berth (%d px)" % bright)
	var warm := 0
	for y in range(100, 220):
		for x in range(480, 640):
			var c := rf.get_pixel(x, y)
			if c.a > 0.0 and c.r > c.b + 0.08:
				warm += 1
	kit.ok(warm > 400, "the passing station lamp throws the window onto the right wall (%d px)" % warm)
	return true
