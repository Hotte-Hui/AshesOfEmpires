extends Level
## L_C3_Registry — the commission's registry (C3P2_DESIGN §4 / §5.1): ONE level file for the four Story scenes
## L_C3_RegistryA–D (in-level switch, TECHNICAL_ARCHITECTURE §12.11) and two looks of the same rooms:
## night (A: green lamp off, Konrad's torch · B: green lamp on) and fire (C: smoke, Magazin + Planarchiv burning,
## ramp door shut · D: the fire in the Karteisaal). Art: assets/environments/veltrava_registry (generator
## tools/pixelgen/env_c3p2_archive.py).
##
## Gates. scene.json entries of `layers`, `props`, `decals`, `fx`, `lights` with one of the keys
##   "after": [objective…]  (all complete)   "until": [objective…] (none complete)   "choice": {objective: id | "!id"}
## are taken out of the manifest before the base Level builds it (`_merge_explore_hotspots` hook) and built here in
## gate groups (one LayerStack per condition); `"blockers": [{name, rect, after?, until?}]` become StaticBody2D walls;
## `"looks": [{after?, until?, canvas_modulate, grade}]` (last match wins) set the CanvasModulate and the grade.
## "fade" = seconds of the live cross-fade; loads, switch cuts and a hidden level change instantly.
##
## When is an objective complete for the art? An objective of a Story scene BEFORE the one this level plays
## (level_id) always counts (fresh loads, captures, memories); inside a memory only those count. Otherwise the live
## Story decides — except c3d_choose: the fire starts in LS_C3_Fire, so its look waits until the cinematic hides
## the level (or the scene is C). Nothing here changes Story state.

const LayerStackScript := preload("res://scripts/levels/layer_stack.gd")
const FlickerLightScript := preload("res://scripts/levels/flicker_light.gd")
const GATE_KEYS := ["after", "until", "choice"]
const SECTIONS := ["layers", "props", "decals", "fx", "lights"]
## objectives whose look waits for the cut (the cinematic shows the change itself)
const DEFER_UNTIL_HIDDEN := ["c3d_choose"]
const SCENES_FILE := "res://data/v3/scenes.json"
const QUESTS_FILE := "res://data/v3/quests.json"
const POLL_S := 0.25

## tests: Dictionary objective -> bool replaces the Story; choice_override objective -> choice id;
## memory_override / hidden_override force those conditions (null = ask Game)
var done_override = null
var choice_override = null
var memory_override = null
var hidden_override = null

var _gated := {}                 # section -> [entry]
var _blocker_defs: Array = []
var _split_done := false
var groups: Array = []           # [{key, cond, fade, names, stack, play, fx, lights:[{node, base, slow, hz, seed}],
								 #   cur, target, delay, shown}]
var blockers: Dictionary = {}    # name -> {cond, body, shape, on}
var looks: Array = []
var look_name := ""
var _obj_scene: Dictionary = {}  # objective -> scene id
var _scene_idx: Dictionary = {}  # scene id -> chain index
var _last_scene := ""
var _poll := 0.0
var _t := 0.0
var _canvas: CanvasModulate
var _cm_from := Color.WHITE
var _cm_to := Color.WHITE
var _cm_k := 1.0
var _cm_dur := 0.0
var _noise := FastNoiseLite.new()
var _connected := false
## sound (round 8 integration): the porter's radio in the quiet night (A/B), roof and glass in the fire (C/D)
const RADIO_KEY := "registry_porter_radio"
const OBJECTIVE_SFX := {"c3e_try_ramp": "c3p2_bolt", "c3f_push_desk": "c3p2_desk_push"}
var _snd_rng := RandomNumberGenerator.new()
var _snd_next := 7.0
var _snd_poll := 0.0
var _radio_on := false
var _booth: Node2D = null


## Base-class hook: called by Level._ready() after the manifest is loaded and before the backdrop is built.
func _merge_explore_hotspots() -> void:
	super._merge_explore_hotspots()
	_split_gated()


func _ready() -> void:
	_noise.seed = 1909
	_noise.frequency = 1.0
	_snd_rng.seed = 1940
	super._ready()
	if not _split_done:          # (a base class that no longer calls the hook: nothing gated was built twice)
		_split_gated()
	_load_chain()
	for c in get_children():
		if c is CanvasModulate:
			_canvas = c
	looks = manifest.get("looks", []) if manifest.get("looks") is Array else []
	_build_gates()
	_build_blockers()
	_connect_signals()
	refresh(true)


func _exit_tree() -> void:
	_disconnect_signals()
	if _radio_on:
		Audio.stop_sfx_loop(RADIO_KEY, 0.6)
		_radio_on = false


# ------------------------------------------------------------------ manifest split
static func is_gated(e) -> bool:
	if not (e is Dictionary):
		return false
	for k in GATE_KEYS:
		if (e as Dictionary).has(k):
			return true
	return false


func _split_gated() -> void:
	_split_done = true
	for section in SECTIONS:
		var keep: Array = []
		var gated: Array = []
		var arr = manifest.get(section, [])
		if arr is Array:
			for e in arr:
				if is_gated(e):
					gated.append(e)
				else:
					keep.append(e)
		manifest[section] = keep
		_gated[section] = gated
	var bl = manifest.get("blockers", [])
	_blocker_defs = bl if bl is Array else []


# ------------------------------------------------------------------ chain (which objectives a scene implies)
func _load_chain() -> void:
	var sd = JSON.parse_string(FileAccess.get_file_as_string(SCENES_FILE)) if FileAccess.file_exists(SCENES_FILE) else null
	var qd = JSON.parse_string(FileAccess.get_file_as_string(QUESTS_FILE)) if FileAccess.file_exists(QUESTS_FILE) else null
	if not (sd is Dictionary) or not (qd is Dictionary):
		return
	var by_id := {}
	for s in sd.get("scenes", []):
		by_id[str(s.get("id", ""))] = s
	var cur := str(sd.get("start_scene", ""))
	var i := 0
	while by_id.has(cur) and not _scene_idx.has(cur):
		_scene_idx[cur] = i
		i += 1
		cur = str(by_id[cur].get("next_scene", ""))
	for q in qd.get("quests", []):
		for o in q.get("objectives", []):
			_obj_scene[str(o.get("id", ""))] = str(q.get("scene", ""))


## True when objective `obj` belongs to a Story scene that comes before the scene this level plays.
func implied(obj: String) -> bool:
	var s := str(_obj_scene.get(obj, ""))
	var here := str(level_id)
	if s == "" or not _scene_idx.has(s) or not _scene_idx.has(here):
		return false
	return int(_scene_idx[s]) < int(_scene_idx[here])


# ------------------------------------------------------------------ conditions
func _in_memory() -> bool:
	if memory_override != null:
		return bool(memory_override)
	return Game != null and Game.get("memory_mode") == true


func _hidden_now() -> bool:
	if hidden_override != null:
		return bool(hidden_override)
	if not is_inside_tree() or not is_visible_in_tree():
		return true
	return Game != null and Game.get("in_cinematic") == true


func objective_done(obj: String, visual := true) -> bool:
	if done_override is Dictionary:
		return bool((done_override as Dictionary).get(obj, false)) or implied(obj)
	if implied(obj):
		return true
	if _in_memory():
		return false
	if not Story.has_method("objective_state") or str(Story.objective_state(obj)) != "complete":
		return false
	if visual and obj in DEFER_UNTIL_HIDDEN and not _hidden_now():
		return false
	return true


func choice_of(obj: String) -> String:
	if choice_override is Dictionary:
		return str((choice_override as Dictionary).get(obj, ""))
	if not Story.has_method("choice_history"):
		return ""
	var h = Story.choice_history()
	if not (h is Dictionary):
		return ""
	var v = (h as Dictionary).get(obj, "")
	if v is Dictionary:
		v = (v as Dictionary).get("choice", (v as Dictionary).get("id", ""))
	return str(v)


static func _list(v) -> Array:
	if v == null:
		return []
	if v is Array:
		return v
	return [v]


func holds(cond: Dictionary, visual := true) -> bool:
	for o in _list(cond.get("after")):
		if not objective_done(str(o), visual):
			return false
	for o in _list(cond.get("until")):
		if objective_done(str(o), visual):
			return false
	var ch = cond.get("choice")
	if ch is Dictionary:
		for obj in ch:
			var want := str(ch[obj])
			var got := choice_of(str(obj))
			if want.begins_with("!"):
				if got == want.substr(1):
					return false
			elif got != want:
				return false
	return true


static func _cond_of(e: Dictionary) -> Dictionary:
	var c := {}
	for k in GATE_KEYS:
		if e.has(k):
			c[k] = e[k]
	return c


# ------------------------------------------------------------------ build
func _build_gates() -> void:
	var by_key := {}
	for section in SECTIONS:
		for e in _gated.get(section, []):
			var cond := _cond_of(e)
			var key := JSON.stringify(cond, "", true) + "|" + str(e.get("fade", 0.6))
			if not by_key.has(key):
				by_key[key] = {"key": key, "cond": cond, "fade": float(e.get("fade", 0.6)), "names": [],
					"m": {"layers": [], "props": [], "decals": [], "fx": [], "lights": [],
						"world_size": manifest.get("world_size", [1920, 360])}}
			by_key[key]["m"][section].append(e)
			by_key[key]["names"].append(str(e.get("name", e.get("file", ""))))
	var base_dir := art_manifest.get_base_dir()
	var at := backdrop.get_index() + 1 if backdrop else 0
	var i := 0
	for key in by_key:
		var g: Dictionary = by_key[key]
		var stack: Node2D = Node2D.new()
		stack.set_script(LayerStackScript)
		stack.name = "Gate%02d" % i
		var play := Node2D.new()
		play.name = "GatePlay%02d" % i
		play.y_sort_enabled = true
		var fxn := Node2D.new()
		fxn.name = "GateFX%02d" % i
		var ln := Node2D.new()
		ln.name = "GateLights%02d" % i
		add_child(stack)
		move_child(stack, at + i)
		playfield.add_child(play)
		fx.add_child(fxn)
		lights.add_child(ln)
		var m: Dictionary = g["m"]
		stack.build({"layers": m["layers"], "props": m["props"], "decals": m["decals"], "fx": m["fx"],
			"world_size": m["world_size"]}, base_dir, play, ln, fxn)
		var lts: Array = []
		for li in m["lights"]:
			lts.append(_make_light(li, ln))
		groups.append({"key": key, "cond": g["cond"], "fade": g["fade"], "names": g["names"], "stack": stack,
			"play": play, "fxn": fxn, "lights": lts, "cur": 0.0, "target": 0.0, "delay": 0.0, "shown": false})
		_apply_group(groups[-1])
		i += 1


func _make_light(li: Dictionary, parent: Node2D) -> Dictionary:
	var l := PointLight2D.new()
	l.set_script(FlickerLightScript)
	l.texture = LayerStackScript.light_texture()
	l.color = Color(str(li.get("color", "#F0C487")))
	l.texture_scale = float(li.get("radius", 80)) / 128.0
	l.height = float(li.get("height", 24))
	l.position = LayerStackScript._v2(li.get("pos", [0, 0]))
	l.name = str(li.get("name", "light"))
	var base := float(li.get("energy", 1.0))
	l.energy = base
	l.set("base_energy", base)
	l.set("flicker", float(li.get("flicker", 0.0)))
	parent.add_child(l)
	return {"node": l, "base": base, "slow": float(li.get("flicker_slow", 0.0)),
		"hz": minf(3.0, float(li.get("flicker_hz", 1.5))), "seed": float(LayerStackScript.name_hash(l.name) % 997)}


func _build_blockers() -> void:
	for b in _blocker_defs:
		if not (b is Dictionary) or not (b.get("rect") is Array) or (b["rect"] as Array).size() < 4:
			continue
		var r: Array = b["rect"]
		var body := StaticBody2D.new()
		body.name = "Blocker_" + str(b.get("name", "wall"))
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(float(r[2]), float(r[3]))
		cs.shape = shape
		cs.position = Vector2(float(r[0]) + float(r[2]) * 0.5, float(r[1]) + float(r[3]) * 0.5)
		cs.disabled = true
		body.add_child(cs)
		add_child(body)
		blockers[str(b.get("name", "wall"))] = {"cond": _cond_of(b), "body": body, "shape": cs, "on": false}


# ------------------------------------------------------------------ evaluation
## Re-evaluates every gate. `instant`: no fades (load, cut, hidden level).
func refresh(instant := false) -> void:
	var scene_changed := str(level_id) != _last_scene
	if scene_changed and _last_scene != "":
		instant = true
	_last_scene = str(level_id)
	if _hidden_now():
		instant = true
	var appear := 0.0
	for g in groups:
		var want := 1.0 if holds(g["cond"], true) else 0.0
		if want != float(g["target"]) and want > 0.5:
			appear = maxf(appear, float(g["fade"]))
	for g in groups:
		var want := 1.0 if holds(g["cond"], true) else 0.0
		if want == float(g["target"]) and not instant:
			continue
		g["target"] = want
		if instant:
			g["cur"] = want
			g["delay"] = 0.0
		elif want < 0.5:
			g["delay"] = appear          # the look that replaces it covers it first: no dip in between
		else:
			g["delay"] = 0.0
		_apply_group(g)
	for nm in blockers:
		var b: Dictionary = blockers[nm]
		var on := holds(b["cond"], false)
		if on != bool(b["on"]) or instant:
			b["on"] = on
			(b["shape"] as CollisionShape2D).set_deferred("disabled", not on)
	_refresh_look(instant)


func _refresh_look(instant: bool) -> void:
	var pick: Dictionary = {}
	for L in looks:
		if L is Dictionary and holds(_cond_of(L), true):
			pick = L
	var nm := str(pick.get("name", ""))
	if nm == look_name and not instant:
		return
	var first := look_name == ""
	look_name = nm
	if pick.has("grade") and str(pick["grade"]) != "":
		grade_preset = str(pick["grade"])
		if not first and not _in_memory() and Game != null and Game.get("level") == self \
				and Game.get("in_cinematic") != true and Game.has_method("_apply_grade"):
			Game._apply_grade(self)
	if _canvas != null and pick.has("canvas_modulate"):
		_cm_from = _canvas.color
		_cm_to = Color(str(pick["canvas_modulate"]))
		_cm_dur = 0.0 if instant else float(pick.get("fade", 0.8))
		_cm_k = 0.0
		if _cm_dur <= 0.0:
			_canvas.color = _cm_to
			_cm_k = 1.0


func _apply_group(g: Dictionary) -> void:
	var a := clampf(float(g["cur"]), 0.0, 1.0)
	var vis := a > 0.001
	for key in ["stack", "play", "fxn"]:
		var n: CanvasItem = g[key]
		if n == null:
			continue
		n.visible = vis
		n.modulate.a = a
	for l in g["lights"]:
		var node: PointLight2D = l["node"]
		node.visible = vis
		node.set("base_energy", float(l["base"]) * a)
		if float(node.get("flicker")) <= 0.0:
			node.energy = float(l["base"]) * a
	g["shown"] = vis


func _process(delta: float) -> void:
	_t += delta
	_sound_step(delta)
	_poll += delta
	if _poll >= POLL_S:
		_poll = 0.0
		refresh(false)
	for g in groups:
		var tgt := float(g["target"])
		var cur := float(g["cur"])
		if cur != tgt:
			if float(g["delay"]) > 0.0:
				g["delay"] = float(g["delay"]) - delta
			else:
				var rate := 1.0 / maxf(0.05, float(g["fade"]) if tgt > cur else minf(0.4, float(g["fade"])))
				g["cur"] = move_toward(cur, tgt, rate * delta)
				_apply_group(g)
		if bool(g["shown"]):
			_flicker(g)
	if _canvas != null and _cm_k < 1.0:
		_cm_k = minf(1.0, _cm_k + delta / maxf(0.05, _cm_dur))
		_canvas.color = _cm_from.lerp(_cm_to, _cm_k)


## Fire lights breathe slowly (<= 3 Hz, never strobing); reduced motion damps them further.
func _flicker(g: Dictionary) -> void:
	var a := clampf(float(g["cur"]), 0.0, 1.0)
	var rm: bool = Settings != null and Settings.has_method("get_value") and Settings.get_value("reduced_motion") == true
	for l in g["lights"]:
		var amp := float(l["slow"])
		if amp <= 0.0:
			continue
		amp *= 0.35 if rm else 1.0
		var n := _noise.get_noise_1d(_t * float(l["hz"]) + float(l["seed"]) * 13.0)
		(l["node"] as PointLight2D).energy = float(l["base"]) * a * (1.0 + amp * n)


# ------------------------------------------------------------------ signals
func _connect_signals() -> void:
	if _connected:
		return
	_connected = true
	for s in ["objective_completed", "state_replaced", "scene_changed"]:
		if Story.has_signal(s):
			Story.connect(s, _on_story_signal)
	if Game != null and Game.has_signal("protagonist_switched"):
		Game.protagonist_switched.connect(_on_switched)
	if Story.has_signal("objective_completed"):
		Story.objective_completed.connect(_on_objective_sfx)


func _disconnect_signals() -> void:
	if not _connected:
		return
	_connected = false
	for s in ["objective_completed", "state_replaced", "scene_changed"]:
		if Story.has_signal(s) and Story.is_connected(s, _on_story_signal):
			Story.disconnect(s, _on_story_signal)
	if Game != null and Game.has_signal("protagonist_switched") and Game.protagonist_switched.is_connected(_on_switched):
		Game.protagonist_switched.disconnect(_on_switched)
	if Story.has_signal("objective_completed") and Story.objective_completed.is_connected(_on_objective_sfx):
		Story.objective_completed.disconnect(_on_objective_sfx)


func _on_story_signal(_arg = null) -> void:
	refresh(false)


func _on_switched(_scene_id: String, _char_id: String) -> void:
	refresh(false)


# ------------------------------------------------------------------ sound
## A/B: the porter's radio plays a waltz, louder near his booth. C/D: the roof creaks and glass bursts every 6–15 s.
## Silent while a cinematic hides the level.
func _sound_step(delta: float) -> void:
	_snd_poll -= delta
	var hidden := _hidden_now()
	var lk := look()
	var fire := lk == "c" or lk == "d"
	if not fire and not hidden:
		if _snd_poll <= 0.0:
			_snd_poll = POLL_S
			Audio.sfx_loop("c3p2_radio_waltz", RADIO_KEY, _radio_db(), 1.2)
			_radio_on = true
	elif _radio_on:
		Audio.stop_sfx_loop(RADIO_KEY, 1.0)
		_radio_on = false
	if fire and not hidden:
		_snd_next -= delta
		if _snd_next <= 0.0:
			_snd_next = _snd_rng.randf_range(6.0, 15.0)
			Audio.sfx("c3p2_roof_creak" if _snd_rng.randf() < 0.6 else "c3p2_glass", -7.0, 0.08)


func _radio_db() -> float:
	if _booth == null or not is_instance_valid(_booth):
		_booth = null
		for n in find_children("*", "", true, false):
			if n is Node2D and str(n.get("hotspot_id")) == "porter_booth":
				_booth = n
				break
	var p = Game.player if Game != null else null
	if _booth == null or p == null or not is_instance_valid(p):
		return -24.0
	var d := absf((p as Node2D).global_position.x - _booth.global_position.x)
	return lerpf(-10.0, -32.0, clampf((d - 24.0) / 460.0, 0.0, 1.0))


func _on_objective_sfx(id: String) -> void:
	if OBJECTIVE_SFX.has(id) and not _hidden_now():
		Audio.sfx(str(OBJECTIVE_SFX[id]), -3.0)


# ------------------------------------------------------------------ queries (tests, debug)
## Names of the gated entries that are shown (target) right now.
func shown_names() -> Array:
	var out: Array = []
	for g in groups:
		if float(g["target"]) > 0.5:
			out.append_array(g["names"])
	return out


func is_shown(entry_name: String) -> bool:
	return entry_name in shown_names()


func blocker_on(blocker_name: String) -> bool:
	return blockers.has(blocker_name) and bool(blockers[blocker_name]["on"])


## "a" | "b" | "c" | "d": the look of the rooms right now (which room layer is on top).
func look() -> String:
	if is_shown("room_fire_d"):
		return "d"
	if is_shown("room_fire_c"):
		return "c"
	if is_shown("room_a"):
		return "a"
	return "b"
