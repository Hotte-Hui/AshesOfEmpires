extends "res://scripts/levels/c3p2_archive/registry_level.gd"
## L_C4_Tunnels — Karsk, Chapter 4 part 1 (documentation/C4_DESIGN.md §4.1): ONE level file for two Story scenes that
## are not consecutive — L_C4_TunnelsA (Alexei in the Archivkeller of the freight office, ≈ 4.40) and L_C4_TunnelsB
## (Alexei in Dienststollen 3 and at the Umsetzgleis, ≈ 7.30). Every C4 scene starts with a level load, so the scene
## is known before _ready (Game._adopt_scene sets level_id). Art: assets/environments/karsk_tunnels (generator
## tools/pixelgen/env_c4_tunnels.py).
##
## On top of the registry gates (after / until / choice / fade, blockers; objectives of earlier scenes count):
##  * "scene": [ids] on a layer / prop / decal / fx / light / swing / event_fx entry: built only while the level
##    plays one of those Story scenes (the cellar's samovar steam is never built at the siding and vice versa);
##  * camera_zones {scene: [x, y, w, h]} (as in the annex level): the camera window of the scene (the other walk
##    area stays off screen behind the door wall);
##  * looks [{name, scene, canvas_modulate, grade}]: canvas modulate + grade of the scene (cellar warm, siding cold);
##  * "swing": 7-frame lamp strips (frame "rest" hangs still) that the passing train swings, each with its light;
##    "event_fx": dust shaken from the vault (played once per train, after "delay" s); "train": the freight train
##    rolling over the yard above the tunnel (scene C).
## Passing trains (not headless, not while a cinematic hides the level; round-9 fix: no pile-up with the trains the
## ambiences already carry):
##  * scene C only (OWN_TRAIN_SCENES): the level's own freight train every 20–40 s, c4_train_overhead at TRAIN_DB
##    (−8 dB, under the ambience) -- and never while the ambience's own train is audible or about to come;
##  * scene A is left to its ambience: amb_karsk_cellar carries two trains of its own (AMB_TRAINS);
##  * every train you hear -- the level's or one inside the ambience loop (read from the playing ambience's position)
##    -- shakes the vault in time with its sound: BEAT_DELAY s after the sound starts, where its rumble is loudest,
##    dust falls from the vault, the lamps swing ≤ 2° (≤ 3 px at the shade; reduced motion: a third), the lights dip a
##    little (≤ 3 Hz, never a strobe) and the train crosses the yard above (scene C).
## Nothing here changes Story state.

const LayerStackT := preload("res://scripts/levels/layer_stack.gd")
const TRAIN_SFX := ["c4_train_overhead", "c4cine_train_overhead", "karsk_train_far"]
const OBJ_SFX := {"c4a_open_door": ["c3p2_bolt", "door_open"], "c4c_inspect_wagon": ["c3p2_desk_push"]}
const TRAIN_DB := -8.0                  ## the level's own train, under the ambience's trains
const OWN_TRAIN_SCENES := ["L_C4_TunnelsB"]
## Seconds from the start of a train's sound to the vault's beat: c4_train_overhead (and the ambiences' trains, the
## same train_overhead of tools/audiogen/c4_audio.py, pass_at 5.5 s) is loudest ≈ 4.5–5.8 s after its start.
const BEAT_DELAY := 3.0
const EVENT_LEN := BEAT_DELAY + 7.5
const TRAIN_SOUND_LEN := 13.0           ## c4_train_overhead.wav with its tail: the level's train waits this long
## Trains inside the ambience loops: start times (s) in the loop (tools/audiogen/c4_audio.py) and their length.
const AMB_TRAINS := {"amb_karsk_cellar": [10.5, 39.0], "amb_karsk_tunnel": [46.0]}
const AMB_TRAIN_LEN := 12.0
const SWING_PERIOD := 1.7

var swings: Array = []          # [{name, node, sprites: [Sprite2D], frames, rest, max_px, light, light_x}]
var events: Array = []          # [{name, node, sprite, frames, fps, delay}]
var train_node: Sprite2D = null
var train_def: Dictionary = {}
var events_enabled := true      ## false: no passing trains (headless tests; captures never run long enough)
var train_t := -1.0             ## seconds since the current train's sound started (-1 = none)
var own_train := false          ## the running train is the level's own (else one inside the ambience)
var swing_px := 0               ## current swing of the lamps in px at the shade (tests / debug)
var amb_override = null         ## tests: [ambience id, playback position s, loop length s] instead of Audio's players
var _next_train := 0.0
var _train_rng := RandomNumberGenerator.new()
var _ev := 1.0                  # light factor of the passing train (1 = none)


# ------------------------------------------------------------------ scene filter (before the registry split)
func _split_gated() -> void:
	_filter_scenes()
	super._split_gated()


## Drops every manifest entry whose "scene" list does not name the Story scene this level plays.
func _filter_scenes() -> void:
	var here := str(level_id)
	for section in ["layers", "props", "decals", "fx", "lights", "swing", "event_fx"]:
		var arr = manifest.get(section, [])
		if not (arr is Array):
			continue
		var keep: Array = []
		for e in arr:
			if e is Dictionary and (e as Dictionary).has("scene") and not (here in _list(e["scene"])):
				continue
			keep.append(e)
		manifest[section] = keep
	var tr = manifest.get("train", {})
	if tr is Dictionary and (tr as Dictionary).has("scene") and not (here in _list(tr["scene"])):
		manifest["train"] = {}


func _ready() -> void:
	_train_rng.seed = 1964
	super._ready()
	events_enabled = DisplayServer.get_name() != "headless"
	_build_swings()
	_build_events()
	_build_train()
	_next_train = _train_rng.randf_range(14.0, 26.0)


# ------------------------------------------------------------------ camera + look per scene
func get_camera_bounds() -> Rect2:
	var sb = manifest.get("camera_zones", {})      # same key as the annex level (scripts/levels/c4/annex_level.gd)
	if sb is Dictionary and sb.has(str(level_id)):
		var b: Array = sb[str(level_id)]
		if b.size() == 4:
			return Rect2(float(b[0]), float(b[1]), float(b[2]), float(b[3]))
	return super.get_camera_bounds()


func _refresh_look(instant: bool) -> void:
	var pick: Dictionary = {}
	for lk in looks:
		if lk is Dictionary and (not (lk as Dictionary).has("scene") or str(level_id) in _list(lk["scene"])) \
				and holds(_cond_of(lk), true):
			pick = lk
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
		_canvas.color = Color(str(pick["canvas_modulate"]))


## "cellar" (scene A) | "siding" (scene C).
func look() -> String:
	return look_name


# ------------------------------------------------------------------ swinging lamps, event strips, the train
func _strip_sprite(path: String, frames: int, emission: bool, strength: float) -> Array:
	var out: Array = []
	var t := LayerStackT.tex(path)
	if t == null:
		push_warning("tunnels_level: missing " + path)
		return out
	var spr := Sprite2D.new()
	spr.texture = t
	spr.centered = false
	spr.hframes = maxi(1, frames)
	spr.light_mask = 0
	out.append(spr)
	if emission:
		var e := LayerStackT.tex(LayerStackT.map_path(path, "_e"))
		if e != null:
			var es := Sprite2D.new()
			es.texture = e
			es.centered = false
			es.hframes = maxi(1, frames)
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
			es.material = mat
			es.modulate = Color(1, 1, 1, strength)
			out.append(es)
	return out


func _named_light(nm: String) -> PointLight2D:
	for g in groups:
		for l in g["lights"]:
			if (l["node"] as Node).name == nm:
				return l["node"]
	return null


func _build_swings() -> void:
	var base := art_manifest.get_base_dir()
	for s in manifest.get("swing", []):
		if not (s is Dictionary):
			continue
		var sprites := _strip_sprite(base + "/" + str(s.get("file", "")), int(s.get("frames", 7)),
			bool(s.get("emission", false)), float(s.get("emission_strength", 0.6)))
		if sprites.is_empty():
			continue
		var node := Node2D.new()
		node.name = "Swing_" + str(s.get("name", "lamp"))
		node.position = LayerStackT._v2(s.get("pos", [0, 0]))
		node.z_index = int(s.get("z", -30))
		for spr in sprites:
			(spr as Sprite2D).frame = int(s.get("rest", 3))
			node.add_child(spr)
		fx.add_child(node)
		var li := _named_light(str(s.get("light", "")))
		swings.append({"name": str(s.get("name", "")), "node": node, "sprites": sprites,
			"frames": int(s.get("frames", 7)), "rest": int(s.get("rest", 3)), "max_px": int(s.get("max_px", 3)),
			"light": li, "light_x": li.position.x if li != null else 0.0})


func _build_events() -> void:
	var base := art_manifest.get_base_dir()
	for e in manifest.get("event_fx", []):
		if not (e is Dictionary):
			continue
		var sprites := _strip_sprite(base + "/" + str(e.get("file", "")), int(e.get("frames", 1)), false, 0.0)
		if sprites.is_empty():
			continue
		var node := Node2D.new()
		node.name = "Event_" + str(e.get("name", "fx"))
		node.position = LayerStackT._v2(e.get("pos", [0, 0]))
		node.z_index = int(e.get("z", 14))
		node.visible = false
		node.add_child(sprites[0])
		fx.add_child(node)
		events.append({"name": str(e.get("name", "")), "node": node, "sprite": sprites[0],
			"frames": int(e.get("frames", 1)), "fps": float(e.get("fps", 10)), "delay": float(e.get("delay", 0.0))})


func _build_train() -> void:
	var tr = manifest.get("train", {})
	if not (tr is Dictionary) or not (tr as Dictionary).has("file"):
		return
	train_def = tr
	var sprites := _strip_sprite(art_manifest.get_base_dir() + "/" + str(tr["file"]), 1, false, 0.0)
	if sprites.is_empty():
		return
	train_node = sprites[0]
	train_node.name = "TrainOverhead"
	train_node.z_index = int(tr.get("z", -45))
	train_node.position = Vector2(float(tr.get("from_x", 1940)), float(tr.get("y", -10)))
	train_node.visible = false
	fx.add_child(train_node)


## Starts the level's own train now (tests and harnesses call it; normally every 20–40 s in scene C): its sound at
## TRAIN_DB -- only in OWN_TRAIN_SCENES, scene A is left to its ambience (there it is a silent beat for captures) --
## and BEAT_DELAY s later the vault's beat.
func start_train() -> void:
	train_t = 0.0
	own_train = true
	_next_train = _train_rng.randf_range(20.0, 40.0)
	if _hidden_now() or not plays_own_trains():
		return
	for id in TRAIN_SFX:
		if FileAccess.file_exists("res://assets/audio/sfx/%s.wav" % id) or ResourceLoader.exists("res://assets/audio/sfx/%s.wav" % id):
			Audio.sfx(id, TRAIN_DB, 0.04)
			break


## True in the Story scenes that run trains of their own (scene C); scene A hears only its ambience's trains.
func plays_own_trains() -> bool:
	return str(level_id) in OWN_TRAIN_SCENES


## [ambience id, playback position s, loop length s] of the ambience playing now when it carries trains (AMB_TRAINS);
## [] when none / unknown. Read from Audio's player of that ambience (the newest, a fade may hold an older one).
func _amb_now() -> Array:
	if amb_override is Array:
		return amb_override
	var au := get_node_or_null("/root/Audio")
	if au == null or not au.has_method("current_ambience"):
		return []
	var id := str(au.call("current_ambience"))
	if not AMB_TRAINS.has(id):
		return []
	var path := "res://assets/audio/amb/%s.wav" % id
	var best: AudioStreamPlayer = null
	for c in au.get_children():
		var p := c as AudioStreamPlayer
		if p != null and p.playing and p.stream != null and p.stream.resource_path == path:
			best = p
	if best == null:
		return []
	return [id, best.get_playback_position(), best.stream.get_length()]


## Seconds since the start of the ambience's train that is audible now (AMB_TRAINS), -1 when none.
func amb_train_time() -> float:
	var a := _amb_now()
	if a.size() < 3:
		return -1.0
	var length := maxf(1.0, float(a[2]))
	for t0 in AMB_TRAINS.get(str(a[0]), []):
		for k in [-1.0, 0.0]:                    # a train that began before the loop's seam
			var d: float = float(a[1]) - (float(t0) + float(k) * length)
			if d >= 0.0 and d < AMB_TRAIN_LEN:
				return d
	return -1.0


## True while the ambience's own train is audible or starts within `within` s (the level's train waits for it).
func amb_train_near(within: float) -> bool:
	var a := _amb_now()
	if a.size() < 3:
		return false
	var length := maxf(1.0, float(a[2]))
	for t0 in AMB_TRAINS.get(str(a[0]), []):
		for k in [-1.0, 0.0, 1.0]:
			var d: float = float(a[1]) - (float(t0) + float(k) * length)
			if d >= -within and d < AMB_TRAIN_LEN:
				return true
	return false


## Swing (px at the shade) of the passing train at time t: builds up with the rumble, then dies away.
static func swing_at(t: float, max_px: int, reduced: bool) -> int:
	if t < 0.0:
		return 0
	var env := smoothstep(0.3, 1.4, t) * exp(-maxf(0.0, t - 2.8) / 1.6)
	var amp := float(max_px) * (0.34 if reduced else 1.0)
	return clampi(int(round(amp * env * sin(TAU * t / SWING_PERIOD))), -max_px, max_px)


## The vault's beat at `t` s after the train's sound started (it runs BEAT_DELAY s behind the sound's start).
func _update_train(t: float) -> void:
	t -= BEAT_DELAY
	var rm: bool = Settings != null and Settings.has_method("get_value") and Settings.get_value("reduced_motion") == true
	for s in swings:
		var px := swing_at(t, int(s["max_px"]), rm)
		swing_px = px
		for spr in s["sprites"]:
			(spr as Sprite2D).frame = clampi(int(s["rest"]) + px, 0, int(s["frames"]) - 1)
		if s["light"] != null and is_instance_valid(s["light"]):
			(s["light"] as PointLight2D).position.x = float(s["light_x"]) + float(px)
	for e in events:
		var k := int(floor((t - float(e["delay"])) * float(e["fps"])))
		var on := k >= 0 and k < int(e["frames"])
		(e["node"] as Node2D).visible = on
		if on:
			(e["sprite"] as Sprite2D).frame = k
	if train_node != null:
		var dur := float(train_def.get("seconds", 7.0))
		var p := clampf((t - 0.5) / dur, 0.0, 1.0)
		train_node.visible = p > 0.0 and p < 1.0
		train_node.position.x = lerpf(float(train_def.get("from_x", 1940)), float(train_def.get("to_x", -800)), p)
	var env := smoothstep(0.4, 1.2, t) * exp(-maxf(0.0, t - 3.0) / 1.4)
	_ev = 1.0 - 0.1 * env * (0.6 + 0.4 * sin(t * 15.0))        # ≈ 2.4 Hz flutter, ≤ 10 % dip


func _end_train() -> void:
	train_t = -1.0
	own_train = false
	_ev = 1.0
	swing_px = 0
	for s in swings:
		for spr in s["sprites"]:
			(spr as Sprite2D).frame = int(s["rest"])
		if s["light"] != null and is_instance_valid(s["light"]):
			(s["light"] as PointLight2D).position.x = float(s["light_x"])
	for e in events:
		(e["node"] as Node2D).visible = false
	if train_node != null:
		train_node.visible = false


## Replaces the registry's radio / fire sounds: the passing trains -- the level's own (scene C) runs on its clock,
## a train inside the ambience follows the ambience's playback position.
func _sound_step(delta: float) -> void:
	if train_t >= 0.0 and own_train:
		train_t += delta
		_update_train(train_t)
		if train_t >= EVENT_LEN:
			_end_train()
		return
	if not events_enabled or _hidden_now():
		return
	var at := amb_train_time()
	if at >= 0.0 and at < EVENT_LEN:
		train_t = at                            # the ambience's train: the vault answers it, in time with its sound
		_update_train(at)
		return
	if train_t >= 0.0:
		_end_train()
	if not plays_own_trains():
		return
	_next_train -= delta
	if _next_train <= 0.0:
		if amb_train_near(TRAIN_SOUND_LEN):
			_next_train = 2.0                   # the ambience's train is (about to be) heard: no second one on top
		else:
			start_train()


## Slow flicker of the registry plus the dip of the passing train, for every named light.
func _flicker(g: Dictionary) -> void:
	var a := clampf(float(g["cur"]), 0.0, 1.0)
	var rm: bool = Settings != null and Settings.has_method("get_value") and Settings.get_value("reduced_motion") == true
	for l in g["lights"]:
		var amp := float(l["slow"]) * (0.35 if rm else 1.0)
		var n := 0.0
		if amp > 0.0:
			n = _noise.get_noise_1d(_t * float(l["hz"]) + float(l["seed"]) * 13.0)
		(l["node"] as PointLight2D).energy = float(l["base"]) * a * (1.0 + amp * n) * _ev


func _on_objective_sfx(id: String) -> void:
	if not OBJ_SFX.has(id) or _hidden_now():
		return
	var ids: Array = OBJ_SFX[id]
	Audio.sfx(str(ids[0]), -3.0)
	if ids.size() > 1 and is_inside_tree():
		get_tree().create_timer(0.3).timeout.connect(func() -> void: Audio.sfx(str(ids[1]), -4.0))


func _exit_tree() -> void:
	super._exit_tree()
