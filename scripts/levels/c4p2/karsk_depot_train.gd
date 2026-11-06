extends "res://scripts/levels/karsk/karsk_train.gd"
## L_C4P2_Karsk, scene A (Monday dawn): the first goods trains of the day passing on the far embankment behind the
## depot (C4P2_DESIGN §4.1: "a passing train in A every 30–50 s at −8 dB (never while a film runs)"). The Chapter-1
## train (karsk_train.gd: loco + mixed wagons, a lingering smoke plume, alternating direction) with this level's
## sprites (tools/pixelgen/env_c4p2_karsk_fx.py). Placed from assets/environments/karsk_c4p2/scene.json "actors"
## (scene_id L_C4P2_KarskA). Never touches Story.
##  * every train enters the view at once (the embankment is only seen between the buildings) and its own sound
##    plays at `train_db`;
##  * no pile-up with the ambience (the round-9 lesson of the tunnels): amb_karsk_depot carries a goods train of its
##    own (`amb_trains`: start times in its loop). When that train starts, the picture follows it -- a train
##    passes in time with the ambience's sound, silently; and the level's own train is held back while the
##    ambience's train is audible or due within `sound_len` s;
##  * while a cinematic runs nothing starts, moves or sounds (the level is hidden behind the film).

var train_db := -8.0
var amb_trains: Dictionary = {}       ## {ambience id: [start s, ...]} trains inside the ambience loop
var amb_train_len := 18.0             ## seconds of one ambience train
var sound_len := 13.0                 ## seconds of the level's own train sound (karsk_train_far.wav with its tail)
var amb_override = null               ## tests: [ambience id, playback position s, loop length s]
var silent := false                   ## the running train follows the ambience's sound (no own sound)


func _tick(delta: float) -> void:
	if film_running():
		return
	if not _active:
		var at := amb_train_time()
		if at >= 0.0 and at < 2.5:
			silent = true
			_start()
			return
		if amb_train_near(sound_len + 2.0):
			_wait = maxf(_wait, 2.0)          # the ambience's train is (about to be) heard: no second one on top
	super._tick(delta)
	if not _active:
		silent = false


## Every train enters the visible stretch of the embankment at once, from the side it comes from.
func _start() -> void:
	super._start()
	var view_x := cam_pos().x * parallax
	_x = (view_x + 650.0) if _dir < 0.0 else (view_x - _len - 10.0)
	_cars.position = Vector2(_x, 0).round()


## True while a cinematic hides the level (Game.in_cinematic).
func film_running() -> bool:
	var g := game()
	return g != null and g.get("in_cinematic") == true


func sfx(id: String, volume_db := 0.0, pitch_var := 0.06) -> void:
	if film_running() or (silent and id == "karsk_train_far"):
		return
	super.sfx(id, train_db if id == "karsk_train_far" else volume_db, pitch_var)


## [ambience id, playback position s, loop length s] of the ambience playing now when it carries trains; [] else.
func _amb_now() -> Array:
	if amb_override is Array:
		return amb_override
	var au := get_node_or_null("/root/Audio")
	if au == null or not au.has_method("current_ambience"):
		return []
	var id := str(au.call("current_ambience"))
	if not amb_trains.has(id):
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


## Seconds since the ambience's train started (audible now), -1 when none.
func amb_train_time() -> float:
	var a := _amb_now()
	if a.size() < 3:
		return -1.0
	var length := maxf(1.0, float(a[2]))
	for t0 in amb_trains.get(str(a[0]), []):
		for k in [-1.0, 0.0]:
			var d: float = float(a[1]) - (float(t0) + k * length)
			if d >= 0.0 and d < amb_train_len:
				return d
	return -1.0


## True while the ambience's train is audible or starts within `within` s.
func amb_train_near(within: float) -> bool:
	var a := _amb_now()
	if a.size() < 3:
		return false
	var length := maxf(1.0, float(a[2]))
	for t0 in amb_trains.get(str(a[0]), []):
		for k in [-1.0, 0.0, 1.0]:
			var d: float = float(a[1]) - (float(t0) + k * length)
			if d >= -within and d < amb_train_len:
				return true
	return false
