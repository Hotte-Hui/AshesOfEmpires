extends SceneTree
## Headless verification of the generated soundscape and of scripts/core/audio.gd.
## Run:  Godot_v4.7.2-stable_win64_console.exe --headless --path <project> --script res://tools/audiogen/test_audio_headless.gd
## Checks: bus layout, every WAV imports as 44.1 kHz 16-bit PCM AudioStreamWAV with the right
## loop flags, the Audio API (crossfades, variants, ui, sting, loops, graceful missing files),
## and plays every stream into a muted bus.  Exit code 0 = pass, 1 = failures.

const AUDIO_SCRIPT := "res://scripts/core/audio.gd"
const DIRS := ["res://assets/audio/amb/", "res://assets/audio/music/", "res://assets/audio/sfx/"]
const LOOP_NAMES := ["mus_karsk", "mus_berlin", "mus_menu", "fire_crackle_loop"]

var failures: Array[String] = []
var notes: Array[String] = []
var audio: Node
var phase := 0
var clock := 0.0
var wall0 := 0
var test_players: Array[AudioStreamPlayer] = []
var finished_ids: Dictionary = {}
var all_streams: Dictionary = {}


func _initialize() -> void:
	print("== audio headless test (Godot %s, driver %s) ==" % [Engine.get_version_info().string, AudioServer.get_driver_name() if AudioServer.has_method("get_driver_name") else "?"])
	_check_bus_layout()
	_check_streams()
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), true)
	AudioServer.add_bus()
	var tb := AudioServer.bus_count - 1
	AudioServer.set_bus_name(tb, "TestMute")
	AudioServer.set_bus_mute(tb, true)
	var scr = load(AUDIO_SCRIPT)
	if scr == null:
		_fail("cannot load " + AUDIO_SCRIPT)
		return
	audio = scr.new()
	audio.name = "AudioUnderTest"
	root.add_child(audio)
	wall0 = Time.get_ticks_msec()


func _process(delta: float) -> bool:
	if audio == null:
		return _finish()
	clock += delta
	match phase:
		0:
			audio.play_ambience("amb_karsk_yard", 0.3)
			audio.play_music("mus_karsk", 0.3)
			for i in 6:
				audio.sfx("step_gravel")
			audio.sfx("stamp_thud", -3.0, 0.0)
			audio.ui("move")
			audio.ui("select")
			audio.ui("type_tick")
			audio.ui("puzzle_success")
			audio.sfx("this_sound_does_not_exist")      # must be a silent no-op
			audio.ui("nope")
			audio.play_music("mus_not_there", 0.5)     # must keep the current music
			# voices are checked right away (footsteps / ticks are only 0.06-0.5 s long)
			var sfx_busy := _playing_in(audio, "Sfx")
			_expect(sfx_busy.size() >= 7, "sfx voices playing (%d)" % sfx_busy.size())
			var names := {}
			var pitches := {}
			for p in sfx_busy:
				names[p.stream.resource_path.get_file()] = true
				pitches[snappedf(p.pitch_scale, 0.0001)] = true
				_expect(p.bus == "SFX", "sfx on SFX bus")
			_expect(names.size() >= 3, "step variants picked at random (%s)" % ", ".join(names.keys()))
			_expect(pitches.size() >= 3, "random pitch variation applied (%d distinct)" % pitches.size())
			# UI clicks/ticks are 60-70 ms long and may already be over when we look, so check
			# the voice allocation (distinct players, distinct streams) instead of `playing`
			var ui_used := {}
			for c in audio.get_children():
				if String(c.name).begins_with("Ui") and (c as AudioStreamPlayer).stream != null:
					ui_used[(c as AudioStreamPlayer).stream.resource_path.get_file()] = (c as AudioStreamPlayer).bus
			_expect(ui_used.size() == 4, "ui() resolved 4 sounds on 4 voices (%s)" % ", ".join(ui_used.keys()))
			for k in ui_used:
				_expect(ui_used[k] == "UI", "ui sound on UI bus (%s)" % k)
			_next()
		1:
			if clock > 0.45:
				_expect(audio.current_ambience() == "amb_karsk_yard", "ambience name")
				_expect(audio.current_music() == "mus_karsk", "music kept after missing play_music")
				var amb := _playing_in(audio, "Amb")
				_check_settings_wiring()
				_expect(amb.size() == 1, "one ambience player playing (got %d)" % amb.size())
				if amb.size() == 1:
					_expect(amb[0].volume_db > -1.0, "ambience faded in (%.1f dB)" % amb[0].volume_db)
					_expect(amb[0].bus == "Ambience", "ambience on Ambience bus")
					var st := amb[0].stream as AudioStreamWAV
					_expect(st != null and st.loop_mode == AudioStreamWAV.LOOP_FORWARD, "ambience stream loops")
				var mus0 := _playing_in(audio, "Mus")
				_expect(mus0.size() == 1 and mus0[0].bus == "Music", "music on Music bus")
				audio.play_music("mus_karsk", 0.4)                  # same name: no restart
				_expect(_playing_in(audio, "Mus").size() == 1, "same music requested again: no restart")
				audio.play_music("mus_berlin", 0.4)
				_next()
		2:
			if clock > 0.2:
				var mus := _playing_in(audio, "Mus")
				_expect(mus.size() == 2, "crossfade: both music players active mid-fade (got %d)" % mus.size())
				_next()
		3:
			if clock > 0.5:
				var mus := _playing_in(audio, "Mus")
				_expect(mus.size() == 1, "crossfade finished: one music player (got %d)" % mus.size())
				_expect(audio.current_music() == "mus_berlin", "current music = mus_berlin")
				audio.sting("mus_choice", -9.0, 0.1)
				audio.play_ambience("", 0.2)
				audio.sfx_loop("fire_crackle_loop", "fire", -6.0, 0.1)
				_next()
		4:
			if clock > 0.4:
				_expect(_playing_in(audio, "Amb").is_empty(), "ambience faded out")
				_expect(audio.current_ambience() == "", "ambience name cleared")
				var mus := _playing_in(audio, "Mus")
				if mus.size() == 1:
					_expect(mus[0].volume_db < -6.0, "music ducked under sting (%.1f dB)" % mus[0].volume_db)
				_expect(_playing_in(audio, "Sting").size() == 1, "sting playing")
				_expect(_playing_in(audio, "Loop_fire").size() == 1, "sfx loop playing")
				audio.stop_sfx_loop("fire", 0.1)
				audio.stop_music(0.2)
				_next()
		5:
			if clock > 0.5:
				_expect(_playing_in(audio, "Mus").is_empty(), "music stopped")
				_expect(audio.current_music() == "", "music name cleared")
				_expect(audio.get_node_or_null("Loop_fire") == null or not (audio.get_node("Loop_fire") as AudioStreamPlayer).playing, "loop stopped")
				_expect(audio.has_sound("step_snow") and audio.has_sound("mus_menu") and not audio.has_sound("xyz"), "has_sound()")
				# three changes in one frame: every track must keep its own player and fade
				audio.play_music("mus_karsk", 0.3)
				audio.play_music("mus_menu", 0.3)
				audio.play_music("mus_berlin", 0.3)
				_next()
		6:
			if clock > 0.05:
				_expect(_playing_in(audio, "Mus").size() == 3, "rapid changes: 3 overlapping music players (got %d)" % _playing_in(audio, "Mus").size())
				_next()
		7:
			if clock > 0.6:
				var mus := _playing_in(audio, "Mus")
				_expect(mus.size() == 1 and audio.current_music() == "mus_berlin", "rapid changes settle on the last track (%d players)" % mus.size())
				audio.play_music("mus_choice", 0.05)          # one-shot cue: must end by itself
				_next()
		8:
			if clock > 5.6:
				_expect(_playing_in(audio, "Mus").is_empty() and audio.current_music() == "", "one-shot cue ended and cleared current_music()")
				# play every stream into a muted bus
				for path in all_streams:
					var p := AudioStreamPlayer.new()
					p.stream = all_streams[path]
					p.bus = "TestMute"
					root.add_child(p)
					p.finished.connect(_on_test_finished.bind(p.get_instance_id()))
					p.play()
					test_players.append(p)
				_next()
		9:
			if clock > 0.35:
				var playing := 0
				var advanced := 0
				for p in test_players:
					var done := finished_ids.has(p.get_instance_id())
					if p.playing or done:
						playing += 1
					if done or p.get_playback_position() > 0.0:
						advanced += 1
				_expect(playing == test_players.size(), "all %d streams started on the muted bus (%d ok)" % [test_players.size(), playing])
				notes.append("playback position advanced for %d/%d streams (needs a mixing audio driver)" % [advanced, test_players.size()])
				# stop everything and give the mixer a moment to drop its playback references
				for p in test_players:
					p.stop()
				if audio != null:
					audio.stop_music(0.0)
					audio.stop_ambience(0.0)
					for c in audio.get_children():
						if c is AudioStreamPlayer:
							(c as AudioStreamPlayer).stop()
				_next()
		10:
			if clock > 0.3:
				return _finish()
	return false


func _finish() -> bool:
	# release everything we created so the engine exits without leak reports from this test
	var checked := all_streams.size()
	for p in test_players:
		p.free()
	test_players.clear()
	all_streams.clear()
	if audio != null:
		audio.free()
		audio = null
	print("")
	for n in notes:
		print("  note: ", n)
	if failures.is_empty():
		print("AUDIO TEST PASSED (%d streams checked)" % checked)
		quit(0)
	else:
		for f in failures:
			print("  FAIL: ", f)
		print("AUDIO TEST FAILED (%d failures)" % failures.size())
		quit(1)
	return true


func _on_test_finished(id: int) -> void:
	finished_ids[id] = true


func _next() -> void:
	phase += 1
	clock = 0.0


func _playing_in(parent: Node, prefix: String) -> Array[AudioStreamPlayer]:
	var out: Array[AudioStreamPlayer] = []
	for c in parent.get_children():
		if c is AudioStreamPlayer and String(c.name).begins_with(prefix) and (c as AudioStreamPlayer).playing:
			out.append(c)
	return out


func _expect(cond: bool, what: String) -> void:
	if cond:
		print("  ok   ", what)
	else:
		_fail(what)


func _fail(what: String) -> void:
	failures.append(what)
	print("  FAIL ", what)


func _check_bus_layout() -> void:
	for b in ["Master", "Music", "Ambience", "SFX", "UI"]:
		var idx := AudioServer.get_bus_index(b)
		_expect(idx >= 0, "bus '%s' exists" % b)
		if idx > 0:
			_expect(AudioServer.get_bus_send(idx) == &"Master", "bus '%s' sends to Master" % b)
	var m := AudioServer.get_bus_index("Master")
	_expect(AudioServer.get_bus_effect_count(m) >= 1 and AudioServer.get_bus_effect(m, 0) is AudioEffectHardLimiter, "Master has a hard limiter")


func _check_settings_wiring() -> void:
	# the project autoloads (Settings + Audio) must have applied the player's volume settings to
	# all five buses, including SFX/UI which Settings alone cannot resolve ("Sfx"/"Ui")
	var settings := root.get_node_or_null("Settings")
	if settings != null and root.get_node_or_null("Audio") != null:
		for key in ["master_volume", "music_volume", "ambience_volume", "sfx_volume", "ui_volume"]:
			var bus: String = {"master_volume": "Master", "music_volume": "Music", "ambience_volume": "Ambience",
				"sfx_volume": "SFX", "ui_volume": "UI"}[key]
			var want := linear_to_db(maxf(0.0001, float(settings.get_value(key))))
			var got := AudioServer.get_bus_volume_db(AudioServer.get_bus_index(bus))
			_expect(absf(want - got) < 0.05, "Settings.%s applied to bus %s (%.2f dB)" % [key, bus, got])
	else:
		notes.append("Settings/Audio autoloads not present: volume wiring not checked")


func _check_streams() -> void:
	var count := 0
	for d: String in DIRS:
		for f in DirAccess.get_files_at(d):
			if not f.ends_with(".wav"):
				continue
			var path: String = d + f
			var s = load(path)
			var nm := f.get_basename()
			if not (s is AudioStreamWAV):
				_fail("%s is not an AudioStreamWAV" % path)
				continue
			var w := s as AudioStreamWAV
			all_streams[path] = w
			count += 1
			var ch := 2 if w.stereo else 1
			var frames := w.data.size() / (2 * ch)
			var ok := w.mix_rate == 44100 and w.format == AudioStreamWAV.FORMAT_16_BITS and frames > 0
			var want_loop: bool = String(d).ends_with("amb/") or nm in LOOP_NAMES
			if want_loop:
				ok = ok and w.loop_mode == AudioStreamWAV.LOOP_FORWARD and w.loop_begin == 0 and w.loop_end == frames
			else:
				ok = ok and w.loop_mode == AudioStreamWAV.LOOP_DISABLED
			if d.ends_with("amb/") or d.ends_with("music/"):
				ok = ok and w.stereo
			if not ok:
				_fail("%s: rate %d fmt %d stereo %s loop %d [%d..%d] frames %d" % [path, w.mix_rate, w.format, w.stereo, w.loop_mode, w.loop_begin, w.loop_end, frames])
	_expect(count >= 50, "imported %d WAV streams (PCM 16-bit, 44.1 kHz, loop flags as designed)" % count)
