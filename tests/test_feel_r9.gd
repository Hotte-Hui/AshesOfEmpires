extends RefCounted
## Round 9 feel pass 2 (owner feel_r9):
##  * quay walkers (assets/environments/veltrava_quay/walkers.json): firemen, onlookers, a clerk, a policeman --
##    own rig sheets (tools/pixelgen/walkers_r8.py) with walk_front / idle_back / walk_back, lanes clear of the
##    props and the story spots
##  * walkers avoid each other in every level (no two in one lane on top of each other; head-on: step aside /
##    wait / turn back; followers keep their distance) and show front / back walks on steep path segments
##  * HUD toasts keep their remaining time while a modal holds them and come back when it closes
##  * side task „Eine Decke für Frau Brunner“ on the quay (data/explore/quay_tasks.json)

const Kit := preload("res://tests/support/test_kit.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const WALKERS_SCENE := "res://scenes/actors/AmbientWalkers.tscn"
const WALKER_SCRIPT := preload("res://scripts/actors/ambient_walker.gd")
const ENVS := {"veltrava_quay": "side", "veltrava_hall": "side", "berlin_archive": "side", "veltrava_station": "oblique"}
const RIG_ROWS := ["walk_front", "idle_back", "walk_back"]
## quay: x ranges a walker never enters (fire engine, bench with the file + Konrad, trestle, cars)
const QUAY_KEEP_OUT := [[258.0, 432.0], [720.0, 830.0], [1060.0, 1104.0], [1106.0, 1422.0]]
## every speaking character of the quay (a walker must never be a recognisable twin)
const QUAY_SPEAKERS := ["alexei", "konrad", "typist", "journalist", "voronova", "kessler", "border_officer"]
const TASK := "veltrava.task.blanket"
const TASK_STEPS := ["veltrava.task.blanket.ask", "veltrava.task.blanket.locker", "veltrava.task.blanket.return"]
const TASK_FILE := "res://data/explore/quay_tasks.json"
const TASK_LOCALE := "res://data/locale/de_quay_tasks.json"
const QUAY_SCENE := "res://scenes/levels/L_C3_Quay.tscn"
const INTERACTABLE := preload("res://scripts/actors/interactable.gd")
const EXPRESSIONS := ["neutral", "concerned", "determined", "surprised"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("quay_walkers_declared_and_placed", _quay_walkers)
	kit.run_case("walker_rigs_complete", _rigs)
	kit.run_case("walkers_never_overlap_in_a_lane", _no_overlap)
	kit.run_case("walkers_resolve_head_on_meetings", _head_on)
	kit.run_case("walkers_follow_at_a_distance", _follow)
	kit.run_case("walkers_walk_front_and_back_on_steep_segments", _diagonal)
	kit.run_case("toasts_keep_their_time_under_a_modal", _toasts)
	kit.run_case("quay_task_data_and_texts", _task_data)
	kit.run_case("quay_task_placed_in_the_level", _task_placed)
	kit.run_case("quay_task_drivers_complete_it_in_order", _task_drivers)
	kit.run_case("quay_task_live_chain_and_marks", _task_live)
	kit.run_case("cinematic_figures_and_board_umlauts", _cine_figures)
	kit.cleanup()
	return kit.failures


class MockEx extends RefCounted:
	var found := {}
	var req := {}

	func is_found(id: String) -> bool:
		return found.has(id)

	func can_find(id: String) -> bool:
		for r in req.get(id, []):
			if not found.has(r):
				return false
		return true


class StubRoot extends Node:
	var modal: Control = null

	func top_modal() -> Control:
		return modal

	func is_modal_open() -> bool:
		return modal != null


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


func _spawn(env: String, holder: Node, override: Array = []) -> Node2D:
	var node: Node2D = load(WALKERS_SCENE).instantiate()
	if override.is_empty():
		var entry := _walker_entry(env)
		for k in entry.get("props", {}):
			node.set(k, entry["props"][k])
	else:
		node.set("walkers", override)
	holder.add_child(node)
	return node


func _fake_player(holder: Node, at: Vector2) -> Node2D:
	var p := Node2D.new()
	p.add_to_group("player")
	p.position = at
	holder.add_child(p)
	return p


func _step(mgr: Node2D, dt: float) -> void:
	mgr._process(dt)
	for w in mgr.get("list"):
		w.rig._process(dt)
		w._process(dt)


## Records every walker for `secs` at 20 fps: positions, states, views, peer side steps.
func _record(mgr: Node2D, secs: float) -> Dictionary:
	var tr := {"frames": [], "states": {}, "views": {}, "asides": {}, "waits": {}}
	for w in mgr.get("list"):
		tr["states"][w.id] = {}
		tr["views"][w.id] = {}
		tr["asides"][w.id] = 0
		tr["waits"][w.id] = 0
	for i in int(secs * 20.0):
		_step(mgr, 0.05)
		var fr := {}
		for w in mgr.get("list"):
			fr[w.id] = [w.position, w.state, w._dir()]
			tr["states"][w.id][w.state] = true
			tr["views"][w.id][w.rig.current_row()] = true
			if w.aside_for != null:
				tr["asides"][w.id] += 1
			if w.state == "wait":
				tr["waits"][w.id] += 1
		(tr["frames"] as Array).append(fr)
	return tr


# ------------------------------------------------------------------ cases
func _quay_walkers() -> bool:
	var entry := _walker_entry("veltrava_quay")
	if not kit.ok(not entry.is_empty(), "quay scene.json declares the AmbientWalkers actor"):
		return true
	kit.eq(str(entry.get("props", {}).get("data", "")), "res://assets/environments/veltrava_quay/walkers.json", "quay walker data path")
	var m := _manifest("veltrava_quay")
	var specs := _specs("veltrava_quay")
	kit.ok(specs.size() >= 4 and specs.size() <= 6, "4-6 walkers on the quay (%d)" % specs.size())
	var story: Array = []
	for k in m.get("hotspots", {}):
		story.append(float(m["hotspots"][k][0]))
	for k in m.get("npcs", {}):
		story.append(float(m["npcs"][k]["feet"][0]))
	var ids := {}
	var lanes := {}
	for s in specs:
		var id := str(s.get("id", ""))
		kit.ok(id != "" and not ids.has(id), "unique walker id '%s'" % id)
		ids[id] = true
		kit.ok(str(s.get("rig", "")) != "", "%s brings its own rig" % id)
		kit.ok(not (str(s.get("char", "")) in QUAY_SPEAKERS), "%s: source '%s' is no quay speaker" % [id, s.get("char")])
		var sp := float(s.get("speed", 20))
		kit.ok(sp >= 10.0 and sp <= 30.0, "%s: unhurried speed %.0f px/s" % [id, sp])
		kit.eq(float(s.get("give_way", 0)), 0.0, "%s: back lane, the player always passes in front" % id)
		var path: Array = s.get("path", [])
		kit.ok(path.size() >= 2, "%s: path of >= 2 points" % id)
		for p in path:
			var x := float(p[0])
			var y := float(p[1])
			kit.ok(y > 294.0 and y < 296.0, "%s: lane y %.1f between the props (<= 294) and the walk band (>= 296)" % [id, y])
			for z in QUAY_KEEP_OUT:
				kit.ok(x < float(z[0]) or x > float(z[1]), "%s: x %.0f keeps out of %s" % [id, x, z])
		for i in path.size() - 1:
			var a := float(path[i][0])
			var b := float(path[i + 1][0])
			for z in QUAY_KEEP_OUT:
				kit.ok(maxf(a, b) < float(z[0]) or minf(a, b) > float(z[1]), "%s: segment %.0f-%.0f does not cross %s" % [id, a, b, z])
		# pauses (and the ends of the pingpong) never on a story spot
		var stops: Array = [0, path.size() - 1]
		for k in s.get("pauses", {}):
			stops.append(int(k))
		for i in stops:
			var x := float(path[i][0])
			for sx in story:
				kit.ok(absf(x - sx) >= 24.0, "%s: stop at x %.0f keeps 24 px from the story spot at %.0f" % [id, x, sx])
		lanes[id] = path
	# the props along each lane stand behind it
	for P in m.get("props", []):
		kit.ok(float(P.get("base_y", 0)) <= 294.0, "prop %s stands behind the lane (base_y %s)" % [P.get("name"), P.get("base_y")])
	return true


func _rigs() -> bool:
	for env in ENVS:
		for s in _specs(env):
			var r := str(s.get("rig", ""))
			if not kit.ok(r != "", "%s/%s has a rig" % [env, s.get("id")]):
				continue
			var jp := "res://assets/environments/%s/%s" % [env, r]
			var meta = _json(jp)
			if not kit.ok(meta is Dictionary and meta.get("anims") is Dictionary, "%s parses" % jp):
				continue
			for row in RIG_ROWS:
				kit.ok(meta["anims"].has(row), "%s: row %s" % [r, row])
			var gs: Dictionary = meta.get("ground_speed", {})
			kit.ok(float(gs.get("walk_front", 0)) > 0.0 and float(gs.get("walk_back", 0)) > 0.0, "%s: ground speeds of the front / back walks" % r)
			var png := jp.get_basename() + ".png"
			var npng := jp.get_basename() + "_n.png"
			var a := Image.load_from_file(ProjectSettings.globalize_path(png))
			var n := Image.load_from_file(ProjectSettings.globalize_path(npng))
			if not (kit.ok(a != null, "%s readable" % png) and kit.ok(n != null, "%s readable" % npng)):
				continue
			kit.eq(a.get_size(), n.get_size(), "%s: normal map has the diffuse's size" % r)
			var rows := 0
			for k in meta["anims"]:
				rows = maxi(rows, int(meta["anims"][k]["row"]) + 1)
			kit.eq(a.get_height(), rows * 56, "%s: one 56 px row per animation" % r)
			# the source's rows keep the source silhouette, the colours differ (no twin of a speaking character)
			var src := Image.load_from_file(ProjectSettings.globalize_path("res://assets/characters/%s/sheet.png" % str(s.get("char", ""))))
			if not kit.ok(src != null, "%s: source sheet readable" % r):
				continue
			a.convert(Image.FORMAT_RGBA8)
			src.convert(Image.FORMAT_RGBA8)
			var diff_alpha := 0
			var diff_rgb := 0
			for y in src.get_height():
				for x in src.get_width():
					var ca := a.get_pixel(x, y)
					var cb := src.get_pixel(x, y)
					if (ca.a > 0.0) != (cb.a > 0.0):
						diff_alpha += 1
					elif ca.a > 0.0 and not ca.is_equal_approx(cb):
						diff_rgb += 1
			kit.eq(diff_alpha, 0, "%s: source rows keep the silhouette of %s" % [r, s.get("char")])
			kit.ok(diff_rgb > 800, "%s: clearly recoloured (%d px differ)" % [r, diff_rgb])
			# the back walk shows no face: no eye pixels of the front view's colour in the head area
			var wb: Dictionary = meta["anims"]["walk_back"]
			var wf: Dictionary = meta["anims"]["walk_front"]
			kit.ok(_head_differs(a, int(wb["row"]), int(wf["row"])), "%s: the back walk shows the back of the head" % r)
	# the manager loads them: every walker on its own rig with a normal map and the extra rows
	var holder := Node2D.new()
	kit.mount(holder)
	var mgr := _spawn("veltrava_quay", holder)
	kit.eq((mgr.get("list") as Array).size(), _specs("veltrava_quay").size(), "every quay walker built")
	for w in mgr.get("list"):
		kit.ok(w.rig.sprite.texture is CanvasTexture and (w.rig.sprite.texture as CanvasTexture).normal_texture != null, "%s: rig with a normal map" % w.id)
		kit.ok(w.rig.has_anim("walk_front") and w.rig.has_anim("walk_back"), "%s: front / back walks loaded" % w.id)
		kit.ok(not w.is_in_group("npcs") and not w.is_in_group("interactables"), "%s is in no gameplay group" % w.id)
	holder.free()
	return true


## Head area (top 22 px of the cell, frame 0) of the back walk differs clearly from the front walk.
static func _head_differs(img: Image, row_back: int, row_front: int) -> bool:
	var diff := 0
	for y in 22:
		for x in 32:
			var a := img.get_pixel(x, row_back * 56 + y)
			var b := img.get_pixel(x, row_front * 56 + y)
			if a.a > 0.0 and b.a > 0.0 and absf(a.get_luminance() - b.get_luminance()) > 0.04:
				diff += 1
	return diff >= 12


func _no_overlap() -> bool:
	for env in ENVS:
		var holder := Node2D.new()
		kit.mount(holder)
		_fake_player(holder, Vector2(-9999, -9999))
		var mgr := _spawn(env, holder)
		var tr := _record(mgr, 150.0)
		var worst := INF
		var who := ""
		var lane := 0.3 if ENVS[env] == "side" else 4.0
		for fr in tr["frames"]:
			var ids: Array = fr.keys()
			for i in ids.size():
				for j in range(i + 1, ids.size()):
					var a: Vector2 = fr[ids[i]][0]
					var b: Vector2 = fr[ids[j]][0]
					if absf(a.y - b.y) < lane and absf(a.x - b.x) < worst:
						worst = absf(a.x - b.x)
						who = "%s/%s" % [ids[i], ids[j]]
		kit.ok(worst >= 12.0, "%s: no two walkers on top of each other in one lane (closest %.1f px %s)" % [env, worst, who])
		# everybody still walks, pauses and turns
		for w in mgr.get("list"):
			var xs: Array = (tr["frames"] as Array).map(func(f): return (f[w.id][0] as Vector2).x)
			kit.ok(float(xs.max()) - float(xs.min()) > 100.0, "%s: %s still walks (%.0f px)" % [env, w.id, float(xs.max()) - float(xs.min())])
			kit.ok(tr["states"][w.id].has("pause"), "%s: %s pauses" % [env, w.id])
		# deterministic
		var holder2 := Node2D.new()
		kit.mount(holder2)
		_fake_player(holder2, Vector2(-9999, -9999))
		var tr2 := _record(_spawn(env, holder2), 150.0)
		var same := true
		for k in (tr["frames"] as Array).size():
			for id in tr["frames"][k]:
				same = same and (tr["frames"][k][id][0] as Vector2).is_equal_approx(tr2["frames"][k][id][0])
		kit.ok(same, "%s: identical tracks on a second run" % env)
		holder.free()
		holder2.free()
	return true


## Two walkers set head-on in one side lane: one steps half a pixel back and both pass; without room (pass 0)
## the lower rank waits and turns back, nobody walks through the other.
func _head_on() -> bool:
	var a := {"id": "test_a", "char": "clerk", "path": [[100, 295.0], [400, 295.0]], "speed": 20, "start": 0.0, "dir": 1}
	var b := {"id": "test_b", "char": "typist", "path": [[100, 295.0], [400, 295.0]], "speed": 20, "start": 1.0, "dir": -1}
	var holder := Node2D.new()
	kit.mount(holder)
	_fake_player(holder, Vector2(-9999, -9999))
	var mgr := _spawn("", holder, [a, b])
	var tr := _record(mgr, 12.0)
	var crossed := false
	var min_dx := INF
	var min_dy_close := INF
	for fr in tr["frames"]:
		var pa: Vector2 = fr["test_a"][0]
		var pb: Vector2 = fr["test_b"][0]
		crossed = crossed or pa.x > pb.x
		if absf(pa.x - pb.x) < 12.0:
			min_dy_close = minf(min_dy_close, absf(pa.y - pb.y))
		min_dx = minf(min_dx, absf(pa.x - pb.x))
	kit.ok(crossed, "head-on with room: they pass each other")
	kit.ok(min_dy_close >= 0.3, "while passing they walk at different depths (dy %.2f)" % min_dy_close)
	kit.ok(int(tr["asides"]["test_a"]) + int(tr["asides"]["test_b"]) > 0, "one of them stepped aside")
	holder.free()
	# no room for anybody: the lower rank waits, then turns back; they never overlap
	a["pass"] = 0
	b["pass"] = 0
	var holder2 := Node2D.new()
	kit.mount(holder2)
	_fake_player(holder2, Vector2(-9999, -9999))
	var mgr2 := _spawn("", holder2, [a, b])
	var tr2 := _record(mgr2, 14.0)
	var closest := INF
	for fr in tr2["frames"]:
		closest = minf(closest, absf((fr["test_a"][0] as Vector2).x - (fr["test_b"][0] as Vector2).x))
	kit.ok(closest >= 12.0, "no room: they never walk into each other (closest %.1f px)" % closest)
	kit.ok(int(tr2["waits"]["test_a"]) + int(tr2["waits"]["test_b"]) > 0, "no room: somebody waits")
	var lower: String = "test_a" if LayerStack.name_hash("test_a") < LayerStack.name_hash("test_b") else "test_b"
	var turned := false
	var prev := Vector2.ZERO
	var first := true
	for fr in tr2["frames"]:
		var d: Vector2 = fr[lower][2]
		if not first and d.dot(prev) < -0.5:
			turned = true
		prev = d
		first = false
	kit.ok(turned, "no room: the lower rank (%s) turns back" % lower)
	holder2.free()
	return true


## A fast walker behind a slow one in the same lane and direction keeps its distance (and passes when it can).
func _follow() -> bool:
	var slow := {"id": "slow", "char": "clerk", "path": [[100, 295.0], [700, 295.0]], "speed": 10, "start": 0.1, "dir": 1, "pass": 0}
	var fast := {"id": "fast", "char": "typist", "path": [[100, 295.0], [700, 295.0]], "speed": 26, "start": 0.0, "dir": 1, "pass": 0}
	var holder := Node2D.new()
	kit.mount(holder)
	_fake_player(holder, Vector2(-9999, -9999))
	var mgr := _spawn("", holder, [slow, fast])
	var tr := _record(mgr, 20.0)
	var gap := INF
	for fr in tr["frames"]:
		var d: float = (fr["slow"][0] as Vector2).x - (fr["fast"][0] as Vector2).x
		gap = minf(gap, d)
	kit.ok(gap >= 14.0, "the fast walker stays behind the slow one (smallest gap %.1f px)" % gap)
	holder.free()
	return true


func _diagonal() -> bool:
	var spec := {"id": "diag", "char": "porter", "rig": "res://assets/environments/veltrava_station/walkers/porter_rig.json",
		"path": [[200, 280], [220, 340], [420, 344]], "speed": 20, "start": 0.0, "dir": 1}
	var holder := Node2D.new()
	kit.mount(holder)
	_fake_player(holder, Vector2(-9999, -9999))
	var mgr := _spawn("", holder, [spec])
	var w = (mgr.get("list") as Array)[0]
	var rows := {}
	for i in 900:                       # 45 s: down the steep segment, along, back, up
		_step(mgr, 0.05)
		rows[w.rig.current_row()] = true
	kit.ok(rows.has("walk_front"), "walking toward the camera shows walk_front %s" % [rows.keys()])
	kit.ok(rows.has("walk_back"), "walking away from the camera shows walk_back")
	kit.ok(rows.has("walk_side"), "the flat segment stays a side walk")
	holder.free()
	# the station porter crosses the platform at the kiosk (data): a steep segment in his path
	var steep := false
	for s in _specs("veltrava_station"):
		if str(s.get("id")) == "station_porter":
			var p: Array = s["path"]
			for i in p.size() - 1:
				var d := Vector2(float(p[i + 1][0]) - float(p[i][0]), float(p[i + 1][1]) - float(p[i][1]))
				steep = steep or absf(d.y) > 1.2 * absf(d.x)
	kit.ok(steep, "the station porter's path has a steep segment (front / back walk)")
	return true


## A toast on screen when a modal opens: hidden, its timer paused (remaining time kept); back with a running timer
## when the modal closes. Toasts arriving meanwhile wait in the queue and follow afterwards.
func _toasts() -> bool:
	var root := StubRoot.new()
	kit.track(root)
	var hud: Control = load("res://scripts/ui/hud.gd").new()
	hud.set("ui_root", root)
	kit.mount(hud)
	hud.toast("Erste Nachricht", "info")
	var box: VBoxContainer = hud.get("_toast_box")
	if not kit.ok(box != null and box.get_child_count() == 1, "the toast is on screen"):
		return true
	var holder: Control = box.get_child(0)
	var tw = holder.get_meta("toast_tween") if holder.has_meta("toast_tween") else null
	if not kit.ok(tw is Tween, "the toast keeps its timer tween"):
		return true
	(tw as Tween).custom_step(1.5)
	kit.ok(tw.is_running(), "timer runs while the toast is shown")
	var modal := Control.new()
	kit.track(modal)
	root.modal = modal
	hud.on_modal_changed(modal)
	kit.ok(not box.visible, "a modal hides the toasts")
	kit.ok(hud.toasts_held(), "toasts held")
	kit.ok(not tw.is_running(), "the timer of the shown toast stands still while it is hidden")
	var elapsed: float = tw.get_total_elapsed_time()
	hud.toast("Zweite Nachricht", "info")
	kit.eq(box.get_child_count(), 1, "a new toast waits in the queue while the modal is open")
	root.modal = null
	hud.on_modal_changed(null)
	kit.ok(box.visible and not hud.toasts_held(), "the modal closed: toasts visible again")
	kit.ok(is_instance_valid(holder) and holder.get_parent() == box, "the first toast came back")
	kit.ok(tw.is_running(), "its timer runs again")
	kit.ok(absf(tw.get_total_elapsed_time() - elapsed) < 0.001, "with the remaining time it had (%.2f s used)" % elapsed)
	kit.eq(box.get_child_count(), 2, "the queued toast follows")
	# the hidden HUD (cinematics) holds them the same way
	hud.hide_hud()
	kit.ok(hud.toasts_held() and not tw.is_running(), "hide_hud holds the toasts too")
	hud.show_hud()
	kit.ok(not hud.toasts_held() and tw.is_running(), "show_hud releases them")
	return true


# ------------------------------------------------------------------ side task „Eine Decke für Frau Brunner“
func _real_explore() -> Node:
	var ex: Node = load("res://scripts/core/explore.gd").new()
	ex.print_warnings = false
	ex.notify_tasks = false
	kit.track(ex)
	ex.reload()
	return ex


func _task_data() -> bool:
	var ex := _real_explore()
	var mine: Array = []
	for w in ex.warnings:
		var t := str(w)
		if t.contains("quay_tasks") or t.contains("blanket"):
			mine.append(t)
	kit.eq(mine, [], "Explore validation: no problem in the quay task")
	var t: Dictionary = ex.task(TASK)
	if not kit.ok(not t.is_empty(), "task %s exists" % TASK):
		return true
	kit.eq(str(t.get("level", "")), "L_C3_Quay", "task level")
	kit.eq(ex.task_steps(TASK), TASK_STEPS, "Frau Brunner -> the fire engine's locker -> back to her")
	kit.eq(ex.requires_of(TASK_STEPS[0]), ["veltrava.quay.chat_typist"], "the task starts after her quay chat")
	for i in range(1, TASK_STEPS.size()):
		kit.eq(ex.requires_of(TASK_STEPS[i]), [TASK_STEPS[i - 1]], "%s requires the step before" % TASK_STEPS[i])
	kit.eq(ex.tasks_for("L_C3_Quay").map(func(x): return str(x["id"])), [TASK], "the quay's one side task")
	var loc: Node = Kit.root().get_node_or_null("Loc")
	if not kit.ok(loc != null, "Loc autoload"):
		return true
	var keys := [str(t["title_key"]), str(t["summary_key"])]
	kit.ok(loc.t(keys[0]).length() <= 32, "task title at most 32 characters")
	kit.ok(loc.t(keys[1]).length() <= 200, "task summary at most 200 characters")
	for s in t.get("steps", []):
		keys.append(str(s["hint_key"]))
		kit.ok(loc.t(str(s["hint_key"])).length() <= 120, "hint %s at most 120 characters" % s["hint_key"])
	for id in TASK_STEPS:
		var e: Dictionary = ex.entry(id)
		kit.eq(str(e.get("level", "")), "L_C3_Quay", "%s: level" % id)
		for k in ["title_key", "prompt_key", "text_key"]:
			keys.append(str(e.get(k, "")))
		kit.ok(loc.t(str(e["title_key"])).length() <= 32 and loc.t(str(e["prompt_key"])).length() <= 32, "%s: title / prompt fit" % id)
		kit.ok(loc.t(str(e["text_key"])).length() <= (420 if str(e["kind"]) != "chat" else 260), "%s: text length" % id)
		if str(e["kind"]) == "chat":
			var lines: Array = e.get("lines", [])
			kit.ok(lines.size() >= 4 and lines.size() <= 9, "%s: 4-9 lines" % id)
			var sp := {}
			for l in lines:
				sp[str(l["speaker"])] = true
				keys.append(str(l["key"]))
				kit.ok(str(l.get("expr", "neutral")) in EXPRESSIONS, "%s: expression %s" % [id, l.get("expr")])
				kit.ok(loc.t(str(l["key"])).length() <= 200, "%s: line %s at most 200 characters" % [id, l["key"]])
			kit.eq(Kit.sorted(sp.keys()), ["alexei", "typist"], "%s: Alexei and Frau Brunner talk" % id)
		else:
			kit.ok(not e.has("lines"), "%s: only chats carry lines" % id)
		kit.ok((e.get("history", []) as Array).is_empty(), "%s: no history card on a side task" % id)
	kit.eq(str(ex.entry(TASK_STEPS[0]).get("kind")), "chat", "starts with a conversation")
	kit.eq(str(ex.entry(TASK_STEPS[2]).get("kind")), "chat", "ends with a closing conversation")
	# every key from de_quay_tasks.json, every string used, German typography
	var lf = _json(TASK_LOCALE)
	if not kit.ok(lf is Dictionary and lf.get("strings") is Dictionary, "de_quay_tasks.json parses"):
		return true
	var strings: Dictionary = lf["strings"]
	for k in keys:
		kit.ok(strings.has(k) and loc.source_of(k).ends_with("de_quay_tasks.json"), "'%s' comes from de_quay_tasks.json" % k)
	for k in strings:
		kit.ok(k in keys, "locale string '%s' is used" % k)
		var s := str(strings[k])
		kit.ok(s.strip_edges() != "" and s == s.strip_edges(), "'%s' is not empty and has no stray spaces" % k)
		kit.ok(not s.contains("\"") and not s.contains("..."), "'%s': German quotes and '…'" % k)
		kit.ok(not s.contains(" - ") and not s.contains("--"), "'%s': dash as ' – '" % k)
		kit.ok(s.count("„") == s.count("“") and s.count("‚") == s.count("‘"), "'%s': balanced German quotes" % k)
		kit.ok(not s.contains("Frank"), "'%s': no francs in Veltrava" % k)
	var old: String = load("res://tests/test_rename_guard.gd").old_id().to_lower()
	kit.ok(old != "" and not (FileAccess.get_file_as_string(TASK_LOCALE) + FileAccess.get_file_as_string(TASK_FILE)).to_lower().contains(old),
		"task texts never use the pre-rename name")
	return true


static func _nodes_of(ps: PackedScene) -> Array:
	var out: Array = []
	var st: SceneState = ps.get_state()
	for i in st.get_node_count():
		var props := {}
		var script_path := ""
		for j in st.get_node_property_count(i):
			var pn := str(st.get_node_property_name(i, j))
			var pv = st.get_node_property_value(i, j)
			if pn == "script":
				script_path = pv.resource_path if pv is Resource else ""
			else:
				props[pn] = pv
		out.append({"name": str(st.get_node_name(i)), "script": script_path, "props": props})
	return out


func _quay_hotspots() -> Dictionary:
	var hs := {}
	var x = _json("res://assets/environments/veltrava_quay/explore_hotspots.json")
	if x is Dictionary and x.get("hotspots") is Dictionary:
		hs.merge(x["hotspots"], true)
	var m := _manifest("veltrava_quay")
	if m.get("hotspots") is Dictionary:
		hs.merge(m["hotspots"], true)
	return hs


func _task_placed() -> bool:
	var nodes := _nodes_of(load(QUAY_SCENE))
	var hs := _quay_hotspots()
	var m := _manifest("veltrava_quay")
	var placed := {}
	var finds: Array = []
	for n in nodes:
		var p: Dictionary = n["props"]
		if not (str(p.get("kind", "")) in ["discover", "chat"]):
			continue
		finds.append(n)
		var chain: Array = Array(p.get("explore_chain", PackedStringArray()))
		for id in (chain if not chain.is_empty() else [str(p.get("explore_id", ""))]):
			placed[str(id)] = (placed.get(str(id), []) as Array) + [n["name"]]
	for id in TASK_STEPS:
		kit.eq((placed.get(id, []) as Array).size(), 1, "%s placed exactly once %s" % [id, placed.get(id, [])])
	var chat: Dictionary = {}
	var locker: Dictionary = {}
	for n in finds:
		if n["name"] == "ChatTypistQuay":
			chat = n
		if str(n["props"].get("explore_id", "")) == TASK_STEPS[1]:
			locker = n
	if kit.ok(not chat.is_empty(), "Frau Brunner's chat node"):
		kit.eq(Array(chat["props"].get("explore_chain", PackedStringArray())), ["veltrava.quay.chat_typist", TASK_STEPS[0], TASK_STEPS[2]],
			"her chat hosts the task's ask and return (chain after her chat)")
		kit.eq(str(chat["props"].get("explore_id", "")), "veltrava.quay.chat_typist", "a new game shows her own chat first")
		kit.eq(str(chat["props"].get("npc_id", "")), "typist", "the chat turns Frau Brunner")
	if not kit.ok(not locker.is_empty(), "the locker node"):
		return true
	var lp: Dictionary = locker["props"]
	kit.eq(str(lp.get("hotspot_id", "")), "exp_task_blanket", "locker on the new task hotspot")
	kit.ok(bool(lp.get("once", false)) and str(lp.get("kind", "")) == "discover", "locker: a once discover spot")
	var h = hs.get("exp_task_blanket", null)
	if not kit.ok(h is Array, "exp_task_blanket resolves"):
		return true
	var pos := Vector2(float(h[0]), float(h[1]))
	var site: Dictionary = m.get("explore_sites", {}).get("blanket_source", {})
	kit.eq(pos, Vector2(float(site.get("stand", [0, 0])[0]), float(site.get("stand", [0, 0])[1])), "at the art's explore site blanket_source")
	var walk := PackedVector2Array()
	for q in m.get("walkable", []):
		walk.append(Vector2(float(q[0]), float(q[1])))
	kit.ok(Geometry2D.is_point_in_polygon(pos, walk), "locker spot in the walk area")
	for k in ["bench", "konrad_quay", "typist_quay", "guard_quay", "kessler_quay", "voronova_quay", "journalist_quay"]:
		var sp: Array = m["hotspots"][k]
		kit.ok(pos.distance_to(Vector2(float(sp[0]), float(sp[1]))) >= 24.0, "locker keeps 24 px from %s" % k)
	for n in finds:
		var hid := str(n["props"].get("hotspot_id", ""))
		if hid == "exp_task_blanket" or not hs.has(hid):
			continue
		var op := Vector2(float(hs[hid][0]), float(hs[hid][1]))
		kit.ok(pos.distance_to(op) >= 14.0, "locker keeps 14 px from %s (%.0f)" % [n["name"], pos.distance_to(op)])
	return true


## The drivers' loop (autoplay / inputplay pending_finds) on the parsed quay: re-collect what is new and findable
## until nothing changes -- it must reach every find and complete the task in step order.
func _task_drivers() -> bool:
	var ex := _real_explore()
	var nodes := _nodes_of(load(QUAY_SCENE)).filter(func(n): return str(n["props"].get("kind", "")) in ["discover", "chat"])
	var mk := MockEx.new()
	for id in ex._entries:
		mk.req[str(id)] = ex.requires_of(str(id))
	var order: Array = []
	var progressed := true
	var guard := 0
	while progressed and guard < 100:
		guard += 1
		progressed = false
		for n in nodes:
			var p: Dictionary = n["props"]
			var chain := PackedStringArray(p.get("explore_chain", PackedStringArray()))
			var cur := INTERACTABLE.pick_chain_step(chain, mk) if not chain.is_empty() else str(p.get("explore_id", ""))
			if cur == "" or mk.found.has(cur) or not mk.can_find(cur):
				continue
			mk.found[cur] = true
			order.append(cur)
			progressed = true
	kit.eq(order.filter(func(x): return x in TASK_STEPS), TASK_STEPS, "the drivers' loop completes the task in step order")
	kit.eq(order.size(), int(ex.counts("L_C3_Quay")["total"]), "and reaches every quay find (%d)" % order.size())
	# the real Explore follows: states and the closing find
	ex.restore({"found": [], "cards": []})
	kit.eq(str(ex.task_state(TASK)["state"]), "not_started", "not started in a new game")
	kit.ok(not ex.can_find(TASK_STEPS[0]), "the task waits for her quay chat")
	ex.find("veltrava.quay.chat_typist")
	for i in TASK_STEPS.size():
		var r: Dictionary = ex.find(TASK_STEPS[i])
		kit.ok(bool(r.get("ok", false)) and bool(r.get("new", false)), "step %s found in order" % TASK_STEPS[i])
		kit.eq(str(ex.task_state(TASK)["state"]), "done" if i == TASK_STEPS.size() - 1 else "active", "state after %s" % TASK_STEPS[i])
	return true


## Live hotspots on the Explore autoload: her chat shows the task step with the HUD's task mark, re-arms (once),
## and the locker only opens after she asked.
func _task_live() -> bool:
	var ex: Node = Kit.root().get_node_or_null("Explore")
	if not kit.ok(ex != null and ex.has_method("task_state") and ex.has_entry(TASK_STEPS[0]), "Explore autoload knows the quay task"):
		return true
	var saved: Dictionary = ex.state()
	var notify: bool = ex.notify_tasks
	ex.notify_tasks = false
	ex.reset()
	var chat: Node = INTERACTABLE.new()
	chat.kind = "chat"
	chat.once = true
	chat.explore_id = "veltrava.quay.chat_typist"
	chat.explore_chain = PackedStringArray(["veltrava.quay.chat_typist", TASK_STEPS[0], TASK_STEPS[2]])
	kit.mount(chat)
	var locker: Node = INTERACTABLE.new()
	locker.kind = "discover"
	locker.once = true
	locker.explore_id = TASK_STEPS[1]
	kit.mount(locker)
	kit.ok(not locker.is_active(), "the locker is closed before she asked")
	chat.used = true
	ex.find("veltrava.quay.chat_typist")
	kit.eq(chat.explore_id, TASK_STEPS[0], "after her chat the hotspot offers the task")
	kit.ok(chat.is_active() and not chat.used, "re-armed for the task step")
	kit.eq(chat.prompt_state(), "task", "prompt mark 'task' (HUD)")
	chat.used = true
	ex.find(TASK_STEPS[0])
	kit.ok(locker.is_active(), "the locker opens")
	kit.eq(locker.prompt_state(), "task", "locker: prompt mark 'task'")
	kit.ok(not chat.is_active(), "her spot waits until the blanket is fetched")
	locker.used = true
	ex.find(TASK_STEPS[1])
	kit.eq(chat.explore_id, TASK_STEPS[2], "then she is next")
	kit.ok(chat.is_active(), "and her spot is open again")
	ex.find(TASK_STEPS[2])
	kit.eq(str(ex.task_state(TASK)["state"]), "done", "task done")
	ex.reset()
	ex.restore(saved)
	ex.notify_tasks = notify
	return true


# ------------------------------------------------------------------ cinematic figures (env_c3p2_cine_hands.py)
static func _img(path: String) -> Image:
	var im := Image.load_from_file(ProjectSettings.globalize_path(path))
	if im != null:
		im.convert(Image.FORMAT_RGBA8)
	return im


static func _opaque_rect(im: Image, r: Rect2i) -> Rect2i:
	var x0 := 99999
	var y0 := 99999
	var x1 := -1
	var y1 := -1
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			if im.get_pixel(x, y).a > 0.0:
				x0 = mini(x0, x)
				y0 = mini(y0, y)
				x1 = maxi(x1, x)
				y1 = maxi(y1, y)
	return Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1) if x1 >= 0 else Rect2i()


func _cine_figures() -> bool:
	var base := "res://assets/cinematics/c3p2/"
	var lay = _json(base + "layout.json")
	if not kit.ok(lay is Dictionary, "layout.json parses"):
		return true
	var esc: Dictionary = lay.get("escape", {})
	var hal: Dictionary = lay.get("halves", {})
	# e3a: 520 x 360 frames (round 11: seven -- the reach-in and a three-step pull); the hand rises and is pulled up
	# (the last frame higher than the first)
	var hands := _img(base + "escape/e3a_hands.png")
	var nh := hands.get_width() / 520 if hands != null else 0
	if kit.ok(hands != null and hands.get_height() == 360 and hands.get_width() % 520 == 0 and nh >= 4,
			"e3a_hands: frames of 520 x 360 (%d)" % nh):
		var tops: Array = []
		for f in nh:
			var r := _opaque_rect(hands, Rect2i(f * 520, 0, 520, 360))
			tops.append(r.position.y)
			kit.ok(r.size.x > 40 and r.size.y > 150, "e3a frame %d: the arm and hand are drawn (%s)" % [f, r])
		kit.ok(int(tops[nh - 1]) < int(tops[0]) - 20, "e3a: the hand is pulled up (top %d -> %d)" % [tops[0], tops[nh - 1]])
	# e3b: the breath puffs start at the two faces
	var men := _img(base + "escape/e3b_men.png")
	var at: Array = esc.get("e3b_men", [40, 220])
	if kit.ok(men != null and men.get_size() == Vector2i(1120, 96), "e3b_men: 2 frames of 560 x 96"):
		for p in esc.get("e3b_breath", []):
			var lx := int(p[0]) - int(at[0])
			var ly := int(p[1]) - int(at[1])
			var near := _opaque_rect(men, Rect2i(clampi(lx - 10, 0, 559), clampi(ly, 0, 95), 20, 16).intersection(Rect2i(0, 0, 560, 96)))
			kit.ok(near.size.x > 0, "e3b: breath point %s sits on a face" % [p])
	# h1 arms: every reaching arm leaves its body at the shoulder (the bench figures cover its root)
	var arms := _img(base + "halves/arms.png")
	var aat: Array = hal.get("arms_at", [210, 170])
	var figs := {"a": [_img(base + "halves/fig_alexei.png"), hal.get("fig_alexei", [112, 150])],
		"k": [_img(base + "halves/fig_konrad.png"), hal.get("fig_konrad", [378, 148])]}
	# round 11: layout halves.arm_cols cells per row (reach x 3, the pull, the hold, Konrad's list); the bodies have 4
	# frames (breath x 2, leaning over x 2).  Every drawn cell starts under its body; all but the hold show the arm.
	var cols := int(hal.get("arm_cols", 3))
	var nfig := 4 if cols >= 14 else 2
	if kit.ok(arms != null and arms.get_width() % cols == 0 and arms.get_height() % 2 == 0,
			"arms: %d x 2 cells" % cols):
		var cw := arms.get_width() / cols
		var chh := arms.get_height() / 2
		for row in 2:
			var who := "a" if row == 0 else "k"
			var fig: Image = figs[who][0]
			var fat: Array = figs[who][1]
			for col in cols:
				# the body frame the runtime shows with this cell: leaning over (2 half / 3 full) for the far reach
				var bf := 0
				if cols >= 14:
					bf = {3: 2, 4: 3, 5: 3, 8: 3, 9: 2}.get(col, 0)
				var bw := fig.get_width() / nfig if fig != null else 0
				var hidden := 0
				var shown := 0
				for y in chh:
					for x in cw:
						if arms.get_pixel(col * cw + x, row * chh + y).a <= 0.0:
							continue
						var fx := int(aat[0]) + x - int(fat[0])
						var fy := int(aat[1]) + y - int(fat[1])
						var covered := fig != null and fx >= 0 and fy >= 0 and fx < bw and fy < fig.get_height() \
							and fig.get_pixel(bf * bw + fx, fy).a > 0.0
						if covered:
							hidden += 1
						else:
							shown += 1
				if hidden + shown == 0 and cols >= 14 and col >= 11:
					continue                    # Alexei has no list cells
				# the late pull and the hold slide the hand with the pages under his thigh (mostly behind the body)
				var under := cols >= 14 and col in [7, 9, 10]
				kit.ok(hidden > 20 and (under or shown > 40), "%s arm frame %d: starts inside the body (%d px under the figure, %d visible)" % [who, col, hidden, shown])
	# the board's umlaut flaps keep their dots (row above the letter) -- distinct from A / O / U
	var glyphs := _img(base + "halves/glyphs.png")
	var charset := str(hal.get("charset", ""))
	if kit.ok(glyphs != null and charset.contains("Ü"), "board glyph atlas with umlauts"):
		for pair in [["A", "Ä"], ["O", "Ö"], ["U", "Ü"]]:
			var a := charset.find(pair[0])
			var u := charset.find(pair[1])
			var diff := 0
			for y in 18:
				for x in 12:
					if not glyphs.get_pixel(a * 12 + x, y).is_equal_approx(glyphs.get_pixel(u * 12 + x, y)):
						diff += 1
			kit.ok(diff >= 12, "flap %s differs clearly from %s (%d px)" % [pair[1], pair[0], diff])
	return true
