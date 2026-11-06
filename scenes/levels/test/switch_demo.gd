extends Node
## Windowed check of the in-level protagonist switch (TECHNICAL_ARCHITECTURE §12.11) in real frames, with the real
## director path (Story event → Game._after_story_change() → goto_level() → in-level switch):
##   godot --path . -- --switch-demo=C:/abs/out_dir        → SWITCHDEMO_PASS (exit 0) or SWITCHDEMO_FAIL … (exit 1)
## (an empty dir value skips the screenshots). Same fixture as tests/test_switch.gd: four Story scenes mapped onto
## scenes/levels/test/L_Test_Switch.tscn through Game.level_overrides (A1 → M1 → C3 station → C3 hall = Alexei →
## Konrad → Alexei → Konrad), test switch settings in Game.ext.switches, the live Story played on with the canonical
## route helpers. Private saves (user://switchdemo/saves); settings only in memory; no profile writes (editor binary).
## Checks: no reload, Game.player valid and alone in the "player" group in every frame after a switch, input locked
## until the glide is nearly done, key presses during the glide and the cooldown swallowed, the glide's duration and
## shape, save/load inside a switch scene, memory travel and return, reduced-motion cut, the black screen a cinematic
## leaves (cut + fade-in), photo mode afterwards. Shots: 1_before … 8_photo.

const TKit := preload("res://tests/support/test_kit.gd")
const LEVEL := "res://scenes/levels/test/L_Test_Switch.tscn"
const SCENES := ["L_A1_Railyard", "L_M1_Archive", "L_C3_Station", "L_C3_Hall"]
const SWITCHES := {
	"L_A1_Railyard": {"partner": "konrad", "partner_spawn": "SP_Test_KonradWaits"},
	"L_M1_Archive": {"partner_spawn": "SP_Test_AlexeiPost"},
	"L_C3_Hall": {"switch_spawn": "SP_Test_Switch"},
}
const KONRAD_WAITS := Vector2(560, 292)
const ALEXEI_POST := Vector2(380, 306)
const SWITCH_SPOT := Vector2(980, 298)

var out_dir := ""
var failures: Array = []
var kit = TKit.new()
var _watch := false
var _watch_frames := 0
var _cam_track: Array = []        # [t, distance to the goal] while a glide runs
var _cam_t := 0.0


func _process(delta: float) -> void:
	if not _watch:
		return
	_watch_frames += 1
	var p = Game.player
	if p == null or not is_instance_valid(p) or not p.is_inside_tree() or not p.is_in_group("player"):
		_fail("frame %d after a switch: Game.player is not a valid body in the tree" % _watch_frames)
	elif get_tree().get_nodes_in_group("player").size() != 1:
		_fail("frame %d after a switch: %d bodies in the 'player' group" % [_watch_frames,
			get_tree().get_nodes_in_group("player").size()])
	if Game.camera != null and Game.camera.is_gliding():
		_cam_t += delta
		_cam_track.append([_cam_t, (Game.camera.desired() - Game.camera.pos).length()])


func run(dir: String) -> void:
	out_dir = "" if dir in ["", "1"] else dir      # bare --switch-demo: checks only, no screenshots
	process_mode = Node.PROCESS_MODE_ALWAYS
	if out_dir != "":
		DirAccess.make_dir_recursive_absolute(out_dir)
	get_tree().create_timer(300.0, true, false, true).timeout.connect(func() -> void:
		print("SWITCHDEMO_FAIL watchdog: gave up after 300 s")
		get_tree().quit(3))
	Saves.base_dir = "user://switchdemo/saves"
	DirAccess.make_dir_recursive_absolute(Saves.base_dir)
	Settings.values["reduced_motion"] = false
	for s in SCENES:
		Game.level_overrides[s] = LEVEL
	for s in SWITCHES:
		Game.ext.switches[s] = SWITCHES[s].duplicate(true)
	Story.new_game()
	Explore.reset()
	Game._quiet_load = true            # no chapter card over the first shot
	await Game.goto_level("L_A1_Railyard", "", false)
	await _phase_before()
	await _phase_glide()
	await _phase_save_load()
	await _phase_memory()
	await _phase_cut()
	await _phase_black()
	await _phase_photo()
	_finish()


# ------------------------------------------------------------------ phases
func _phase_before() -> void:
	if not await _until(_free_play, 10.0):
		_fail("scene A: no free play")
	await _wait(0.8)
	_eq(str(Game.player.char_id), "alexei", "scene A: Alexei is played")
	var si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "konrad", "scene A: Konrad stands in")
	if si != null:
		_near(si.position, KONRAD_WAITS, "scene A: Konrad at his partner_spawn")
	# Alexei walks a little (real input)
	Input.action_press("move_right")
	await _wait(1.0)
	Input.action_release("move_right")
	await _wait(0.5)
	await _shoot("1_before")


func _phase_glide() -> void:
	var lvl: Node = Game.level
	var alexei: Node = Game.player
	var alexei_at: Vector2 = alexei.position
	var probe: Node = lvl.playfield.get_node("SwitchProbe")
	kit.play_a1(Story)
	_drain()
	_eq(Game._story_scene(), "L_M1_Archive", "Story moved on to B")
	_watch = true
	_watch_frames = 0
	_cam_track.clear()
	_cam_t = 0.0
	var t0 := Time.get_ticks_msec()
	var done := [false]
	_story_change(done)                          # what Game.interact() does after the exit event
	_ok(Game.switching and Game.busy and Game.input_locked, "switch running: busy and input locked")
	_ok(Game.level == lvl, "no reload: the same level instance")
	_eq(str(lvl.level_id), "L_M1_Archive", "level plays B")
	_eq(str(Game.player.char_id), "konrad", "Konrad is played at once")
	_near(Game.player.position, KONRAD_WAITS, "Konrad takes over where he stood in")
	_ok(Game._fade.color.a < 0.01, "no fade")
	_ok(not Game.ui.photo.can_open(), "photo mode cannot open during the glide")
	await _wait(0.12)
	_key(KEY_E)                                   # mashing the key that ended the last line …
	await _wait(0.25)
	_ok(not probe.used, "a key press during the glide does nothing")
	_ok(Game.ui.hud.is_protagonist_tag_visible(), "name plate shows during the glide")
	await _shoot("2_glide")
	if not await _until(func() -> bool: return not Game.switching, 3.0):
		_fail("the switch never ended")
	var unlock_ms := Time.get_ticks_msec() - t0
	_ok(unlock_ms >= 500 and unlock_ms <= 1000, "input unlocks after ~0.7 s of the 1.2 s glide (%d ms)" % unlock_ms)
	_ok(not Game.input_locked and not Game.busy, "input free after the switch")
	await _wait(0.08)                             # Konrad's focus is on the probe now …
	_ok(Game.player.focus == probe, "Konrad stands at the probe hotspot")
	_key(KEY_E)                                   # … but a press right after the unlock is the cooldown's
	await _wait(0.1)
	_ok(not probe.used, "a key press inside the cooldown does nothing")
	if not await _until(func() -> bool: return done[0], 3.0):
		_fail("_after_story_change never returned")
	if not await _until(func() -> bool: return not Game.camera.is_gliding(), 3.0):
		_fail("the glide never settled")
	# glide shape: monotone approach, ~1.2 s to 99 %
	var first := float(_cam_track[0][1]) if not _cam_track.is_empty() else 0.0
	var mono := true
	var t99 := -1.0
	for i in range(1, _cam_track.size()):
		if float(_cam_track[i][1]) > float(_cam_track[i - 1][1]) + 0.01:
			mono = false
		if t99 < 0.0 and first > 0.0 and float(_cam_track[i][1]) <= first * 0.01:
			t99 = float(_cam_track[i][0])
	_ok(first > 100.0, "the camera had a way to glide (%.0f px)" % first)
	_ok(mono, "the camera approaches monotonically (no overshoot)")
	_ok(t99 >= 1.0 and t99 <= 1.45, "99 %% of the glide after ~1.2 s (%.2f s)" % t99)
	await _wait(1.6)                             # Alexei reaches his post
	_watch = false
	_ok(_watch_frames > 60, "Game.player checked in every frame of the switch (%d frames)" % _watch_frames)
	var si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "alexei", "Alexei stays as a story NPC")
	if si != null:
		_ok(si.position.distance_to(alexei_at) > 20.0, "Alexei walked off towards his post")
		_ok(si.position.distance_to(ALEXEI_POST) < 40.0 or si.is_walking(), "…to B's partner_spawn")
	_ok(not is_instance_valid(alexei), "Alexei's old body is freed")
	await _shoot("3_after")
	# the first press after the cooldown works: the new protagonist can act
	Game.auto = true                             # (spoken lines close by themselves)
	_key(KEY_E)
	var used := await _until(func() -> bool: return probe.used, 3.0)
	_ok(used, "after the cooldown Konrad interacts normally")
	await _until(_free_play, 5.0)
	Game.auto = false
	if not await _until(func() -> bool: return Game.stand_in() != null and not Game.stand_in().is_walking(), 8.0):
		_fail("Alexei never arrived at his post")


func _phase_save_load() -> void:
	var lvl_id := Game.level.get_instance_id()
	var r: Dictionary = Saves.save("1")
	_ok(r.get("ok", false), "save inside B: %s" % r.get("error", ""))
	var k_pos: Vector2 = Game.player.position
	var a_pos: Vector2 = Game.stand_in().rest_position()
	Input.action_press("move_left")
	await _wait(0.6)
	Input.action_release("move_left")
	await _wait(0.2)
	Game._on_load_slot("1")
	if not await _until(func() -> bool: return _free_play() and Game.level.get_instance_id() != lvl_id, 20.0):
		_fail("load: no free play")
		return
	await _wait(0.5)
	_eq(str(Game.level.level_id), "L_M1_Archive", "load: the shared file plays B")
	_eq(str(Game.player.char_id), "konrad", "load: Konrad is played")
	_near(Game.player.position, k_pos, "load: Konrad where he was saved", 0.5)
	var si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "alexei", "load: Alexei stands in")
	if si != null:
		_near(si.position, a_pos, "load: Alexei where he was", 0.5)
	await _shoot("4_loaded")


func _phase_memory() -> void:
	var k_pos: Vector2 = Game.player.position
	var a_pos: Vector2 = Game.stand_in().position if Game.stand_in() != null else Vector2.INF
	var ok: bool = await Game.travel_to_memory("L_A1_Railyard")
	_ok(ok, "memory of A opens")
	if not ok:
		return
	await _until(_free_play, 10.0)
	_ok(Game.memory_mode, "inside the memory")
	_eq(str(Game.player.char_id), "alexei", "memory of A opens with Alexei")
	var si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "konrad", "memory: Konrad stands in")
	await _wait(1.6)
	await _shoot("5_memory")
	await Game.return_from_memory()
	await _until(_free_play, 10.0)
	_ok(not Game.memory_mode, "back in the present")
	_eq(str(Game.level.level_id), "L_M1_Archive", "present: B again")
	_eq(str(Game.player.char_id), "konrad", "present: Konrad is played")
	_near(Game.player.position, k_pos, "present: Konrad where he was", 0.5)
	si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "alexei", "present: Alexei stands in again")
	if si != null:
		_near(si.position, a_pos, "present: Alexei where he was", 0.5)


func _phase_cut() -> void:
	Settings.values["reduced_motion"] = true
	kit.play_m1(Story)
	_drain()
	_eq(Game._story_scene(), "L_C3_Station", "Story moved on to A2")
	_watch = true
	_watch_frames = 0
	var lvl: Node = Game.level
	var done := [false]
	_story_change(done)
	_ok(Game.level == lvl, "A2: no reload")
	_eq(str(Game.player.char_id), "alexei", "A2: control back with Alexei")
	_ok(Game.camera.pos.distance_to(Game.camera.desired()) < 0.01 and not Game.camera.is_gliding(),
		"reduced motion: the camera cuts")
	await _until(func() -> bool: return done[0], 2.0)
	_ok(not Game.switching and not Game.input_locked, "reduced motion: control at once")
	await _wait(0.5)
	_watch = false
	await _shoot("6_cut")
	Settings.values["reduced_motion"] = false


func _phase_black() -> void:
	# what a §12.5 cinematic on the way leaves behind: black screen, the level hidden and paused
	Game._begin_cinematic()
	await Game.fade_out(0.3)
	Game.level.visible = false
	Game.level.process_mode = Node.PROCESS_MODE_DISABLED
	Game._end_cinematic()
	kit.play_c3a(Story)
	_drain()
	_eq(Game._story_scene(), "L_C3_Hall", "Story moved on to B2")
	_watch = true
	_watch_frames = 0
	await Game._after_story_change()
	_ok(Game.level.visible and Game.level.process_mode == Node.PROCESS_MODE_INHERIT, "B2: level shown and running")
	_ok(Game._fade.color.a < 0.05, "B2: faded back in")
	_eq(str(Game.player.char_id), "konrad", "B2: Konrad is played")
	_near(Game.player.position, SWITCH_SPOT, "B2: Konrad at the switch_spawn")
	var si = Game.stand_in()
	_ok(si != null and str(si.char_id) == "alexei", "B2: Alexei stands in")
	await _wait(1.0)
	_watch = false
	await _shoot("7_after_black")


func _phase_photo() -> void:
	await _until(_free_play, 5.0)
	_ok(Game.ui.open_photo(), "photo mode opens after a switch")
	await _wait(0.6)
	await _shoot("8_photo")
	Game.ui.photo.close()
	await _wait(0.3)
	_ok(Game.camera.target == Game.player and not Game.camera.cinematic, "photo mode hands the camera back to Konrad")
	_ok(Game.player.visible and Game.stand_in() != null and Game.stand_in().visible, "both protagonists visible again")


# ------------------------------------------------------------------ helpers
func _story_change(done: Array) -> void:
	await Game._after_story_change()
	done[0] = true


func _drain() -> void:
	for seq in Story.pending_cinematics():
		Story.consume_cinematic(seq, true)


func _key(k: int) -> void:
	for down in [true, false]:
		var ev := InputEventKey.new()
		ev.set("keycode", k)
		ev.set("physical_keycode", k)
		ev.pressed = down
		Input.parse_input_event(ev)


func _free_play() -> bool:
	return Game.level != null and is_instance_valid(Game.level) and Game.player != null \
		and is_instance_valid(Game.player) and not Game.busy and not Game.in_cinematic and not Game.input_locked \
		and not get_tree().paused and Game._fade.color.a < 0.05 and not Game.memory_travelling


func _until(cond: Callable, timeout: float) -> bool:
	var t := 0.0
	while t < timeout:
		if cond.call():
			return true
		await get_tree().process_frame
		t += get_process_delta_time()
	return bool(cond.call())


func _wait(s: float) -> void:
	var t := 0.0
	while t < s:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shoot(shot: String) -> void:
	if out_dir == "":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join(shot + ".png"))
	print("SWITCHDEMO shot ", shot)


func _fail(msg: String) -> void:
	if not (msg in failures):
		failures.append(msg)
	push_warning("SWITCHDEMO " + msg)


func _ok(cond: bool, msg: String) -> void:
	if not cond:
		_fail(msg)


func _eq(a, b, msg: String) -> void:
	if a != b:
		_fail("%s (got %s, expected %s)" % [msg, a, b])


func _near(a: Vector2, b: Vector2, msg: String, tol := 0.01) -> void:
	if a.distance_to(b) > tol:
		_fail("%s (at %s, expected %s)" % [msg, a, b])


func _finish() -> void:
	for f in kit.failures:
		_fail("story route: " + str(f))
	Game.level_overrides.clear()
	Game.ext.reload()
	for s in ["1", "auto", "quick"]:
		Saves.delete(s)
	if failures.is_empty():
		print("SWITCHDEMO_PASS frames-checked, shots in ", out_dir)
		get_tree().quit(0)
	else:
		for f in failures:
			print("SWITCHDEMO_FAIL ", f)
		get_tree().quit(1)
