extends Node2D
## X1 finale montage "Zwei Züge, ein Eintrag" (owner: trans-finale; TECHNICAL_ARCHITECTURE §12.5).
##
## Contract: signal finished (emitted exactly once), configure(ctx), play(), skip() (idempotent).
## ctx = {"choices": Story.choice_history(), "flags": {...}, "symbols": bool}.
##
## Data-driven: assets/cinematics/finale/finale.json (written by tools/pixelgen/cine_finale_build.py) holds
## the sets (pixel layers, atlased frame animations, snow, characters), the shot list (time windows,
## dithered transitions, split-screen clips, camera keys) and timed events (sfx, music, subtitles).
## Everything visual is a pure function of the montage time t, so the montage can be seeked (seek(t)) and
## captured frame-exactly by the test harness.  Branch shots are picked by ctx.choices ("when" blocks);
## insignia layers use their *_hist variant when ctx.symbols is true (§12.4).
## Rendering: lives in the 640x360 world viewport under Game.level_root; camera via Game.camera
## (sub-pixel cinematic moves); subtitles via Game.subtitle(); audio: own players on the Music/SFX buses
## (stopped on skip) plus Audio.sfx for one-shots.

signal finished

const DATA_PATH := "res://assets/cinematics/finale/finale.json"
const BASE := "res://assets/cinematics/finale/"
const SFX_DIR := "res://assets/audio/sfx/"
const SET_SHADER := preload("res://assets/cinematics/finale/finale_set.gdshader")
const ROUTE_SHADER := preload("res://assets/cinematics/finale/finale_route.gdshader")
const SnowNode := preload("res://scripts/cinematics/finale/finale_snow.gd")
const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const DEFAULT_CHOICES := {"a1_choose": "share_with_irina", "m1_choose": "preserve_evidence"}
const ACTOR_LIGHT_BIT := 1 << 12

## read by Game._apply_grade (falls back to "default" when data/grades.json has no "finale" preset)
var grade_preset := "finale"
var mode := "cinematic"
var level_id := "LS_X1_Final"

var ctx: Dictionary = {}
var choices: Dictionary = {}
var symbols := true
var duration := 46.0
var reduced_motion := false
var data: Dictionary = {}

var _t := 0.0
var _playing := false
var _done := false
var _skipped := false
var _built := false
var _sets: Dictionary = {}          # id -> {root, mats: Array[ShaderMaterial], nodes: Array, flicker}
var _shots: Array = []
var _events: Array = []
var _cam: Camera2D = null
var _own_cam: Camera2D = null
var _music: AudioStreamPlayer = null
var _loops: Dictionary = {}         # key -> AudioStreamPlayer
var _fired: Dictionary = {}


# ------------------------------------------------------------------------------------------- contract
func configure(c: Dictionary) -> void:
	ctx = c
	choices = DEFAULT_CHOICES.duplicate()
	var ch = c.get("choices", {})
	if ch is Dictionary:
		for k in ch:
			choices[str(k)] = str(ch[k])
	symbols = bool(c.get("symbols", _symbols_default()))
	reduced_motion = bool(c.get("reduced_motion", _setting("reduced_motion", false)))
	_build()


func play() -> void:
	if not _built:
		configure(ctx if not ctx.is_empty() else {})
	if _done:
		return
	_playing = true
	_apply(_t)


func skip() -> void:
	if _done:
		return
	_skipped = true
	_finish()


func is_finished() -> bool:
	return _done


func was_skipped() -> bool:
	return _skipped


func time() -> float:
	return _t


## Test/harness hook: jump to montage time t (no events fire; visuals are a pure function of t).
func seek(t: float) -> void:
	if not _built:
		configure(ctx)
	_t = clampf(t, 0.0, duration)
	for i in _events.size():
		_fired[i] = float(_events[i].get("t", 0.0)) <= _t
	_apply(_t)


# ------------------------------------------------------------------------------------------- runtime
func _process(delta: float) -> void:
	if not _playing or _done:
		return
	var prev := _t
	_t = minf(_t + delta, duration)
	_fire_events(prev, _t)
	_apply(_t)
	if _t >= duration:
		_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	_playing = false
	_stop_audio()
	if _cam and _cam == _game_camera() and _cam.has_method("release"):
		_cam.release()
	finished.emit()


func _exit_tree() -> void:
	_stop_audio()


# ------------------------------------------------------------------------------------------- build
func _build() -> void:
	if _built:
		return
	_built = true
	if not FileAccess.file_exists(DATA_PATH):
		push_warning("FinaleMontage: missing " + DATA_PATH)
		duration = 0.5
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if typeof(d) != TYPE_DICTIONARY:
		push_warning("FinaleMontage: cannot parse " + DATA_PATH)
		duration = 0.5
		return
	data = d
	duration = float(data.get("duration", 46.0))
	_cam = _game_camera()
	if _cam == null:
		_own_cam = Camera2D.new()
		_own_cam.anchor_mode = Camera2D.ANCHOR_MODE_FIXED_TOP_LEFT
		add_child(_own_cam)
		_own_cam.make_current()
	var order := 0
	for sid in data.get("sets", {}):
		_build_set(str(sid), data["sets"][sid])
		order += 1
	for s in data.get("shots", []):
		if _when_ok(s.get("when", {})):
			_shots.append(s)
	for e in data.get("events", []):
		if _when_ok(e.get("when", {})):
			_events.append(e)
	_events.sort_custom(func(a, b): return float(a.get("t", 0)) < float(b.get("t", 0)))
	for i in _events.size():
		_fired[i] = false
	_apply(0.0)


func _build_set(sid: String, sd: Dictionary) -> void:
	var root := Node2D.new()
	root.name = sid
	root.visible = false
	var mat := ShaderMaterial.new()
	mat.shader = SET_SHADER
	root.material = mat
	add_child(root)
	var entry := {"root": root, "mats": [mat], "nodes": [], "flicker": sd.get("flicker", {}), "light_bit": 0}
	for nd in sd.get("nodes", []):
		if not _when_ok(nd.get("when", {})):
			continue
		var n := _build_node(nd, entry)
		if n != null:
			root.add_child(n)
	_sets[sid] = entry


func _build_node(nd: Dictionary, entry: Dictionary) -> Node:
	var kind := str(nd.get("type", "sprite"))
	var node: Node = null
	var rec := {"def": nd, "kind": kind}
	match kind:
		"sprite", "anim", "route":
			var sp := Sprite2D.new()
			sp.centered = false
			sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			var file := str(nd.get("atlas", nd.get("file", "")))
			if symbols and nd.has("hist_atlas"):
				file = str(nd["hist_atlas"])
			elif symbols and nd.has("hist"):
				file = str(nd["hist"])
			sp.texture = _tex(BASE + file)
			if kind == "anim":
				sp.region_enabled = true
				rec["frames"] = nd.get("frames", [])
				sp.visible = false
			var p: Array = nd.get("pos", [0, 0])
			sp.position = Vector2(float(p[0]), float(p[1]))
			rec["home"] = sp.position
			if kind == "route":
				var rm := ShaderMaterial.new()
				rm.shader = ROUTE_SHADER
				rm.set_shader_parameter("order_tex", _tex(BASE + str(nd.get("order", ""))))
				sp.material = rm
				entry["mats"].append(rm)
			elif nd.has("reveal"):
				var nm := ShaderMaterial.new()
				nm.shader = SET_SHADER
				sp.material = nm
				entry["mats"].append(nm)
				rec["mat"] = nm
			else:
				sp.use_parent_material = true
			if nd.has("light"):
				sp.light_mask = ACTOR_LIGHT_BIT
			node = sp
		"snow":
			var sn: Node2D = SnowNode.new()
			sn.setup(nd)
			sn.use_parent_material = true
			node = sn
		"rect":
			var poly := Polygon2D.new()
			var r: Array = nd.get("rect", [0, 0, 680, 380])
			poly.polygon = PackedVector2Array([Vector2(r[0], r[1]), Vector2(r[0] + r[2], r[1]),
				Vector2(r[0] + r[2], r[1] + r[3]), Vector2(r[0], r[1] + r[3])])
			poly.color = Color(str(nd.get("color", "#000000")))
			if nd.has("reveal"):
				var pm := ShaderMaterial.new()
				pm.shader = SET_SHADER
				poly.material = pm
				entry["mats"].append(pm)
				rec["mat"] = pm
			else:
				poly.use_parent_material = true
			node = poly
		"actor":
			node = _build_actor(nd, rec)
		_:
			return null
	if node is CanvasItem:
		(node as CanvasItem).z_index = int(nd.get("z", 0))
	node.name = str(nd.get("id", kind)).validate_node_name()
	rec["node"] = node
	entry["nodes"].append(rec)
	return node


func _build_actor(nd: Dictionary, rec: Dictionary) -> Node:
	var holder := Node2D.new()
	holder.use_parent_material = true
	var rig: Node2D = SpriteRig.new()
	rig.use_parent_material = true
	holder.add_child(rig)
	rig.load_character(str(nd.get("char", "konrad")))
	if rig.sprite:
		rig.sprite.use_parent_material = true
		rig.sprite.light_mask = ACTOR_LIGHT_BIT
		rig.sprite.self_modulate = Color(str(nd.get("modulate", "#8a8f9a")))
	var anim := str(nd.get("anim", "idle_side"))
	rig.play(anim, true)
	rig.set_flip(bool(nd.get("flip", false)))
	var p: Array = nd.get("pos", [0, 0])
	holder.position = Vector2(float(p[0]), float(p[1]))
	var li = nd.get("light", null)
	if li is Dictionary:
		var l := PointLight2D.new()
		l.texture = LayerStack.light_texture()
		l.color = Color(str(li.get("color", "#F2C27E")))
		l.energy = float(li.get("energy", 1.2))
		l.texture_scale = float(li.get("scale", 0.5))
		l.range_item_cull_mask = ACTOR_LIGHT_BIT
		var lp: Array = li.get("pos", [0, -30])
		l.position = Vector2(float(lp[0]), float(lp[1]))
		l.height = float(li.get("height", 24.0))
		holder.add_child(l)
		rec["light"] = l
		rec["light_energy"] = l.energy
	rec["rig"] = rig
	return holder


# ------------------------------------------------------------------------------------------- evaluation
func _apply(t: float) -> void:
	if data.is_empty():
		return
	# which sets are visible, with which reveal/clip, in which order
	var state := {}
	var top_shot: Dictionary = {}
	for i in _shots.size():
		var s: Dictionary = _shots[i]
		var t0 := float(s.get("t0", 0.0))
		var t1 := float(s.get("t1", 0.0))
		if t < t0 or t >= t1:
			continue
		var fin := float(s.get("fade_in", 0.0))
		var rv := 1.0 if fin <= 0.0 else clampf((t - t0) / fin, 0.0, 1.0)
		var fout := float(s.get("fade_out", 0.0))
		if fout > 0.0:
			rv = minf(rv, clampf((t1 - t) / fout, 0.0, 1.0))
		var sid := str(s.get("set", ""))
		state[sid] = {"reveal": rv, "z": i, "shot": s, "t0": t0}
		top_shot = s
	var cam_pos := _camera_at(top_shot, t)
	for sid in _sets:
		var e: Dictionary = _sets[sid]
		var root: Node2D = e["root"]
		if not state.has(sid):
			root.visible = false
			continue
		var st: Dictionary = state[sid]
		root.visible = true
		root.z_index = 100 + int(st["z"]) * 60
		var clip := Rect2(-100000, -100000, 200000, 200000)
		var cl = st["shot"].get("clip", null)
		if cl is Array and cl.size() == 4:
			clip = Rect2(cam_pos.x + float(cl[0]), cam_pos.y + float(cl[1]), float(cl[2]), float(cl[3]))
		var tint := 0.0
		var tk = st["shot"].get("tint", null)
		if tk is Array:
			tint = _interp_keys(tk, t)
		for m: ShaderMaterial in e["mats"]:
			m.set_shader_parameter("reveal", float(st["reveal"]))
			m.set_shader_parameter("clip_rect", Vector4(clip.position.x, clip.position.y, clip.end.x, clip.end.y))
			m.set_shader_parameter("tint", tint)
			var tc = st["shot"].get("tint_color", "#000000")
			m.set_shader_parameter("tint_color", Color(str(tc)))
		var fl := _flicker(e["flicker"], t)
		root.modulate = Color(fl, fl, fl, 1.0)
		var home: Vector2 = Vector2(st["shot"].get("home", [20, 10])[0], st["shot"].get("home", [20, 10])[1])
		for rec: Dictionary in e["nodes"]:
			_apply_node(rec, t, cam_pos - home)
	_set_camera(cam_pos)


func _apply_node(rec: Dictionary, t: float, cam_off: Vector2) -> void:
	var nd: Dictionary = rec["def"]
	var node: Node = rec["node"]
	var par := float(nd.get("parallax", 1.0))
	var off := Vector2.ZERO
	if par != 1.0:
		off = (cam_off * (1.0 - par)).round()
	match str(rec["kind"]):
		"anim":
			var sp: Sprite2D = node
			var f := -1
			if nd.has("loop"):
				var lp: Dictionary = nd["loop"]
				var seq: Array = lp.get("seq", [])
				if not seq.is_empty():
					var t0 := float(lp.get("t0", 0.0))
					var idx := int(floor(maxf(0.0, t - t0) * float(lp.get("fps", 8.0))))
					f = int(seq[idx % seq.size()])
			if nd.has("keys"):
				var k = _step_key(nd["keys"], t)
				if k != null:
					f = int(k[1])
			var frames: Array = rec.get("frames", [])
			if f < 0 or f >= frames.size():
				sp.visible = false
			else:
				var fr: Array = frames[f]
				sp.visible = true
				sp.region_rect = Rect2(float(fr[0]), float(fr[1]), float(fr[2]), float(fr[3]))
				sp.position = rec["home"] + Vector2(float(fr[4]), float(fr[5])) + _pos_at(nd, t) + off
		"sprite":
			var sp2: Sprite2D = node
			sp2.position = rec["home"] + _pos_at(nd, t) + off
			if nd.has("vis"):
				sp2.visible = _step_value(nd["vis"], t, 1.0) > 0.5
		"route":
			var rs: Sprite2D = node
			rs.position = rec["home"] + off
			var rm: ShaderMaterial = rs.material
			rm.set_shader_parameter("progress", _interp_keys(nd.get("progress", [[0.0, 1.0]]), t))
			rm.set_shader_parameter("node_reveal", _interp_keys(nd.get("reveal", [[0.0, 1.0]]), t))
		"snow":
			var sn: Node2D = node
			sn.position = off
			if nd.has("density_keys"):
				sn.density = _interp_keys(nd["density_keys"], t)
			sn.set_time(t)
		"rect":
			(node as Node2D).position = off
		"actor":
			(node as Node2D).position = Vector2(nd.get("pos", [0, 0])[0], nd.get("pos", [0, 0])[1]) + off
			if rec.has("light"):
				var l: PointLight2D = rec["light"]
				l.energy = float(rec["light_energy"]) * (_flicker({"amp": 0.04}, t) if not reduced_motion else 1.0)
	if rec.has("mat") and nd.has("reveal"):
		(rec["mat"] as ShaderMaterial).set_shader_parameter("node_reveal", _interp_keys(nd["reveal"], t))


func _pos_at(nd: Dictionary, t: float) -> Vector2:
	if not nd.has("pos_keys"):
		return Vector2.ZERO
	var keys: Array = nd["pos_keys"]
	if keys.is_empty():
		return Vector2.ZERO
	if bool(nd.get("step", false)) or keys.size() == 1:
		var k = _step_key(keys, t)
		return Vector2.ZERO if k == null else Vector2(float(k[1]), float(k[2]))
	if t <= float(keys[0][0]):
		return Vector2(float(keys[0][1]), float(keys[0][2]))
	for i in range(keys.size() - 1):
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if t < float(b[0]):
			var f := smoothstep(0.0, 1.0, (t - float(a[0])) / maxf(0.0001, float(b[0]) - float(a[0])))
			return Vector2(lerpf(float(a[1]), float(b[1]), f), lerpf(float(a[2]), float(b[2]), f)).round()
	var l: Array = keys[keys.size() - 1]
	return Vector2(float(l[1]), float(l[2]))


func _camera_at(shot: Dictionary, t: float) -> Vector2:
	if shot.is_empty():
		return Vector2(20, 10)
	var home: Array = shot.get("home", [20, 10])
	var keys: Array = shot.get("cam", [])
	if keys.is_empty() or reduced_motion:
		var k0: Array = keys[0] if not keys.is_empty() else [0, home[0], home[1]]
		return Vector2(float(k0[1]), float(k0[2]))
	if t <= float(keys[0][0]):
		return Vector2(float(keys[0][1]), float(keys[0][2]))
	for i in range(keys.size() - 1):
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if t < float(b[0]):
			var f := (t - float(a[0])) / maxf(0.0001, float(b[0]) - float(a[0]))
			f = f * f * (3.0 - 2.0 * f)
			return Vector2(lerpf(float(a[1]), float(b[1]), f), lerpf(float(a[2]), float(b[2]), f))
	var l: Array = keys[keys.size() - 1]
	return Vector2(float(l[1]), float(l[2]))


func _set_camera(p: Vector2) -> void:
	if _cam and is_instance_valid(_cam):
		if "cinematic" in _cam:
			_cam.cinematic = true
		if _cam.has_method("set_top_left"):
			_cam.set_top_left(p, false)
		else:
			_cam.position = p.round()
	elif _own_cam:
		_own_cam.position = p.round()


func _flicker(f, t: float) -> float:
	if not (f is Dictionary) or f.is_empty() or reduced_motion:
		return 1.0
	var amp := float(f.get("amp", 0.0))
	var n := sin(t * 13.1) * 0.5 + sin(t * 7.7 + 1.3) * 0.3 + sin(t * 23.3 + 0.7) * 0.2
	var v := 1.0 - amp * (0.5 + 0.5 * n)
	for d in f.get("dips", []):
		var t0 := float(d[0])
		var dur := float(d[2])
		if t >= t0 and t < t0 + dur:
			var k := (t - t0) / dur
			v -= float(d[1]) * (1.0 - absf(k * 2.0 - 1.0))
	return clampf(v, 0.0, 1.0)


func _interp_keys(keys: Array, t: float) -> float:
	if keys.is_empty():
		return 1.0
	if t <= float(keys[0][0]):
		return float(keys[0][1])
	for i in range(keys.size() - 1):
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if t < float(b[0]):
			var f := (t - float(a[0])) / maxf(0.0001, float(b[0]) - float(a[0]))
			return lerpf(float(a[1]), float(b[1]), f)
	return float(keys[keys.size() - 1][1])


func _step_key(keys: Array, t: float):
	var cur = null
	for k in keys:
		if float(k[0]) <= t + 0.0001:
			cur = k
		else:
			break
	return cur


func _step_value(keys: Array, t: float, dflt: float) -> float:
	var k = _step_key(keys, t)
	return dflt if k == null else float(k[1])


func _when_ok(w) -> bool:
	if not (w is Dictionary):
		return true
	for k in w:
		if str(choices.get(str(k), "")) != str(w[k]):
			return false
	return true


# ------------------------------------------------------------------------------------------- events / audio
func _fire_events(prev: float, now: float) -> void:
	for i in _events.size():
		if _fired.get(i, false):
			continue
		var e: Dictionary = _events[i]
		var et := float(e.get("t", 0.0))
		if et > now:
			break
		if et >= prev - 0.0001 or prev == 0.0:
			_fired[i] = true
			_fire(e)


func _fire(e: Dictionary) -> void:
	match str(e.get("type", "")):
		"sfx":
			var aud := _autoload("Audio")
			if aud and aud.has_method("sfx"):
				aud.sfx(str(e.get("id", "")), float(e.get("db", 0.0)), float(e.get("pitch_var", 0.03)))
		"music":
			_music = _start_player(str(e.get("id", "")), "Music", float(e.get("db", 0.0)), false)
		"loop":
			var key := str(e.get("key", e.get("id", "")))
			if not _loops.has(key):
				var p := _start_player(str(e.get("id", "")), str(e.get("bus", "Ambience")), float(e.get("db", 0.0)), true)
				if p:
					_loops[key] = p
					_ramp(p, float(e.get("db", 0.0)), float(e.get("fade", 0.5)), true)
		"loop_stop":
			var key2 := str(e.get("key", ""))
			if _loops.has(key2):
				var p2: AudioStreamPlayer = _loops[key2]
				_loops.erase(key2)
				_ramp(p2, -60.0, float(e.get("fade", 0.6)), false, true)
		"subtitle":
			var g := _autoload("Game")
			var loc := _autoload("Loc")
			var txt := str(e.get("key", ""))
			if loc and loc.has_method("t"):
				txt = loc.t(txt)
			if g and g.has_method("subtitle"):
				g.subtitle(txt, float(e.get("dur", 3.0)))


func _start_player(id: String, bus: String, db: float, loop: bool) -> AudioStreamPlayer:
	var path := SFX_DIR + id + ".wav"
	if not ResourceLoader.exists(path):
		push_warning("FinaleMontage: missing sound " + path)
		return null
	var s: AudioStream = load(path)
	if loop and s is AudioStreamWAV:
		var w := (s as AudioStreamWAV).duplicate() as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = int(round(w.get_length() * w.mix_rate))
		s = w
	var p := AudioStreamPlayer.new()
	p.stream = s
	p.bus = bus if AudioServer.get_bus_index(bus) >= 0 else "Master"
	p.volume_db = db if not loop else -60.0
	add_child(p)
	p.play()
	return p


func _ramp(p: AudioStreamPlayer, to_db: float, dur: float, _start := false, free_after := false) -> void:
	if p == null or not is_instance_valid(p):
		return
	var tw := create_tween()
	tw.tween_property(p, "volume_db", to_db, maxf(0.01, dur))
	if free_after:
		tw.tween_callback(p.queue_free)


func _stop_audio() -> void:
	for k in _loops:
		var p: AudioStreamPlayer = _loops[k]
		if is_instance_valid(p):
			p.stop()
	_loops.clear()
	if _music and is_instance_valid(_music):
		_music.stop()
	_music = null


# ------------------------------------------------------------------------------------------- helpers
## Loads exactly `path`.  (LayerStack.tex() applies Symbols.pick() itself; the montage resolves the
## insignia variant from ctx.symbols instead, so a caller can force either mode.)
func _tex(path: String) -> Texture2D:
	if path == "" or path.ends_with("/"):
		return null
	if ResourceLoader.exists(path):
		return load(path) as Texture2D
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	return null


func _autoload(n: String) -> Node:
	var tree := get_tree()
	if tree == null:
		return null
	return tree.root.get_node_or_null(n)


func _game_camera() -> Camera2D:
	var g := _autoload("Game")
	if g and "camera" in g and g.camera and is_instance_valid(g.camera):
		return g.camera
	return null


func _setting(key: String, dflt):
	var s := _autoload("Settings")
	if s and s.has_method("get_value"):
		var v = s.get_value(key)
		return dflt if v == null else v
	return dflt


func _symbols_default() -> bool:
	return bool(_setting("historical_symbols", true))
