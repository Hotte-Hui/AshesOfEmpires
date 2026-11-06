extends RefCounted
## In-level protagonist switch (TECHNICAL_ARCHITECTURE §12.11) on the test level scenes/levels/test/L_Test_Switch.tscn.
## Fixture (in memory only, data/ is never touched): Game.level_overrides maps four consecutive Story scenes onto that
## one file — L_A1_Railyard → L_M1_Archive → L_C3_Station → L_C3_Hall = Alexei → Konrad → Alexei → Konrad (A → B →
## A2 → B2) — and Game.ext.switches gets test settings; the live Story is played forward with the canonical route
## helpers. The runner cannot await, so this checks the synchronous parts (switch detection, Game.switch_now(), level
## setup, saves, memory entry, the camera glide stepped by hand, the HUD plate). The async flow — glide wait, input
## lock, swallowed key presses, fades after a cinematic, autosave, memory travel and return, photo mode, Game.player
## valid in every frame — is checked frame by frame in a real window by `-- --switch-demo=<dir>`
## (scenes/levels/test/switch_demo.gd, prints SWITCHDEMO_PASS / SWITCHDEMO_FAIL).
## Never writes the player's files: saves go to user://test_switch (removed afterwards), settings stay in memory.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const CAMERA := preload("res://scripts/render/world_camera.gd")
const LEVEL := "res://scenes/levels/test/L_Test_Switch.tscn"
const HUD_SCENE := "res://scenes/ui/HUD.tscn"
const SCENES := ["L_A1_Railyard", "L_M1_Archive", "L_C3_Station", "L_C3_Hall"]
const TMP := "user://test_switch"
const SWITCHES := {
	"L_A1_Railyard": {"partner": "konrad", "partner_spawn": "SP_Test_KonradWaits"},
	"L_M1_Archive": {"partner_spawn": "SP_Test_AlexeiPost"},
	"L_C3_Hall": {"switch_spawn": "SP_Test_Switch"},
}
const KONRAD_WAITS := Vector2(560, 292)
const ALEXEI_POST := Vector2(380, 306)
const SWITCH_SPOT := Vector2(980, 298)
const A1_START := Vector2(200, 300)

var kit: TKit
var game: Node
var _keep := {}
var _signals: Array = []


func run() -> Array:
	kit = TKit.new()
	game = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if not kit.ok(game != null and game.has_method("switch_now"), "Game autoload with switch_now()"):
		return kit.failures
	_begin()
	kit.run_case("chapter_ext_switch_settings", _ext_settings)
	kit.run_case("detection_and_partners", _detection)
	kit.run_case("level_setup_places_the_partner", _setup_partner)
	kit.run_case("switch_without_reload_positions_kept", _switch_a_to_b)
	kit.run_case("camera_glide_is_critically_damped", _glide)
	kit.run_case("save_and_load_inside_a_switch_scene", _save_load)
	kit.run_case("memory_opens_with_the_scenes_protagonist", _memory_entry)
	kit.run_case("reduced_motion_cuts_and_control_goes_back", _cut_back)
	kit.run_case("hidden_level_after_cinematic_and_switch_spawn", _hidden_level)
	kit.run_case("same_person_next_scene_keeps_the_body", _same_person)
	kit.run_case("existing_levels_untouched", _untouched)
	kit.run_case("hud_name_plate", _hud_plate)
	_end()
	kit.cleanup()
	return kit.failures


# ------------------------------------------------------------------ fixture
func _begin() -> void:
	_keep = {"story": Story.save_json(), "explore": Explore.state(), "rm": Settings.values.get("reduced_motion", false),
		"saves_dir": Saves.base_dir, "camera": game.camera, "level": game.level, "player": game.player}
	DirAccess.make_dir_recursive_absolute(TMP + "/saves")
	Saves.base_dir = TMP + "/saves"
	Settings.values["reduced_motion"] = false
	Story.new_game()
	Explore.reset()
	for s in SCENES:
		game.level_overrides[s] = LEVEL
	for s in SWITCHES:
		game.ext.switches[s] = SWITCHES[s].duplicate(true)
	var cam: Camera2D = CAMERA.new()
	kit.mount(cam)
	game.camera = cam
	game.protagonist_switched.connect(_on_switched)


func _end() -> void:
	_unmount()
	if game.protagonist_switched.is_connected(_on_switched):
		game.protagonist_switched.disconnect(_on_switched)
	game.level_overrides.clear()
	game.ext.reload()
	game.memory_mode = false
	game.memory_scene = ""
	game._pending_spawn_pos = null
	game._pending_stand_in = null
	game.camera = _keep["camera"]
	game.level = _keep["level"]
	game.player = _keep["player"]
	Settings.values["reduced_motion"] = _keep["rm"]
	Saves.base_dir = _keep["saves_dir"]
	if not Story.load_json(str(_keep["story"])).get("ok", false):
		Story.new_game()
	Explore.restore(_keep["explore"])
	_rm_tree(TMP)


func _on_switched(scene_id: String, char_id: String) -> void:
	_signals.append([scene_id, char_id])


func _rm_tree(dir: String) -> void:
	var d := DirAccess.open(dir)
	if d == null:
		return
	for f in d.get_files():
		DirAccess.remove_absolute(dir.path_join(f))
	for sub in d.get_directories():
		_rm_tree(dir.path_join(sub))
	DirAccess.remove_absolute(dir)


## Loads the test level for Story scene `id` the way Game._load_level() does (without the frame wait) and runs the
## real level setup (player, camera, partner).
func _mount(id: String, spawn := "") -> Node:
	_unmount()
	var lvl: Node = (load(LEVEL) as PackedScene).instantiate()
	lvl.set("ambience", "")                      # no players left running at exit (headless runner)
	lvl.set("music", "")
	game._adopt_scene(lvl, id)
	game._level_file = LEVEL
	(Engine.get_main_loop() as SceneTree).root.add_child(lvl)
	game.level = lvl
	game._setup_level(spawn)
	return lvl


func _unmount() -> void:
	game.set_focus(null)
	var lvl = game.level
	game.level = null
	game.player = null
	game._stand_in = null
	game._level_file = ""
	if lvl != null and is_instance_valid(lvl):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


func _drain() -> void:
	for seq in Story.pending_cinematics():
		Story.consume_cinematic(seq, true)


func _players() -> Array:
	return (Engine.get_main_loop() as SceneTree).get_nodes_in_group("player")


func _stand_ins() -> Array:
	var out: Array = []
	if game.level == null:
		return out
	for n in game.level.playfield.get_children():
		if n.has_meta("stand_in") and not n.is_queued_for_deletion():
			out.append(n)
	return out


## Game.player is what both E2E drivers use: valid, in the tree, the only member of "player", the Story's character,
## and the level plays the Story's scene (autoplay's _wait_available condition).
func _driver_view(what: String) -> void:
	var p = game.player
	kit.ok(p != null and is_instance_valid(p) and p.is_inside_tree(), what + ": Game.player valid and in the tree")
	kit.eq(_players(), [p], what + ": exactly one body in the 'player' group")
	kit.eq(str(p.char_id), Story.active_character, what + ": Game.player is the Story's active character")
	kit.eq(str(game.level.level_id), game._story_scene(), what + ": level plays the Story's current scene")


func _near(a: Vector2, b: Vector2, what: String, tol := 0.01) -> bool:
	return kit.ok(a.distance_to(b) <= tol, "%s (%s, expected %s)" % [what, a, b])


# ------------------------------------------------------------------ cases
func _ext_settings() -> bool:
	kit.ok(game.ext.SECTIONS.has("switches"), "ChapterExt merges a 'switches' section from data/chapters/*.json")
	var s: Dictionary = game.ext.switch_settings("L_C3_Hall")
	kit.eq(s, {"switch_spawn": "SP_Test_Switch"}, "switch_settings returns the scene's settings")
	s["switch_spawn"] = "changed"
	kit.eq(game.ext.switch_spawn("L_C3_Hall"), "SP_Test_Switch", "switch_settings is a copy (read-only access)")
	kit.eq(game.ext.switch_settings("L_Unknown"), {}, "no settings → {}")
	kit.eq(game.ext.switch_spawn("L_Unknown"), "", "no switch_spawn → ''")
	return true


func _detection() -> bool:
	for s in SCENES:
		kit.eq(game.level_file(s), LEVEL, "level_overrides decide the file of " + s)
		kit.ok(game.is_switch_scene(s), s + " shares its file → switch scene")
	kit.eq(game.level_file("L_M1_Plaza"), str(game.LEVELS["L_M1_Plaza"]), "other scenes keep their file")
	kit.ok(not game.is_switch_scene("L_M1_Plaza"), "a level of its own is no switch scene")
	kit.ok(not game.is_switch_scene("res://scenes/levels/L_Test.tscn"), "a res:// path is no Story scene")
	kit.eq(game.scene_partner("L_A1_Railyard"), "konrad", "first scene: partner only by setting")
	kit.eq(game.scene_partner("L_M1_Archive"), "alexei", "B: the protagonist of A stands in (same file)")
	kit.eq(game.scene_partner("L_C3_Station"), "konrad", "A2: Konrad stands in")
	kit.eq(game.scene_partner("L_C3_Hall"), "alexei", "B2: Alexei stands in")
	game.ext.switches["L_C3_Station"] = {"partner": "none"}
	kit.eq(game.scene_partner("L_C3_Station"), "", "partner 'none' sends the other one off")
	game.ext.switches.erase("L_C3_Station")
	kit.ok(not game.can_switch_in_level("L_M1_Archive"), "no switch without a loaded level")
	return true


func _setup_partner() -> bool:
	Story.new_game()
	var lvl := _mount("L_A1_Railyard")
	kit.eq(str(lvl.level_id), "L_A1_Railyard", "the shared file plays the scene it was loaded for")
	kit.eq(str(lvl.protagonist), "alexei", "protagonist follows the scene")
	kit.eq(str(game.player.char_id), "alexei", "Alexei is played in scene A")
	_near(game.player.position, A1_START, "Alexei at the scene's entry spawn")
	var si = game.stand_in()
	if not kit.ok(si != null, "Konrad stands in (partner setting of A)"):
		return true
	kit.eq(str(si.char_id), "konrad", "stand-in shows Konrad (his own sheet)")
	_near(si.position, KONRAD_WAITS, "Konrad at the scene's partner_spawn")
	kit.ok(si.is_in_group("npcs") and bool(si.stand_in) and si.has_meta("stand_in"), "stand-in is a story NPC marked as such")
	kit.ok(not (si is CharacterBody2D) and not si.has_method("try_interact"), "stand-in takes no input")
	kit.ok(si.rig.is_flipped(), "Konrad faces Alexei (left)")
	kit.eq(_stand_ins().size(), 1, "one stand-in")
	_driver_view("scene A")
	kit.ok(not game.can_switch_in_level("L_A1_Railyard"), "the scene being played is no switch target")
	kit.ok(game.can_switch_in_level("L_M1_Archive"), "the next scene in the same file is a switch target")
	game._quiet_load = true
	kit.ok(not game.can_switch_in_level("L_M1_Archive"), "no switch while a quiet (return) load is pending")
	game._quiet_load = false
	var ex: Dictionary = game.save_extra()
	kit.eq(ex.get("controlled"), "alexei", "save_extra names who is controlled")
	kit.eq(ex.get("stand_in"), {"char": "konrad", "pos": [KONRAD_WAITS.x, KONRAD_WAITS.y]}, "save_extra stores the stand-in")
	return true


func _switch_a_to_b() -> bool:
	var lvl: Node = game.level
	var alexei: Node = game.player
	alexei.position = Vector2(245, 300)          # he walked a little
	var konrad_npc = game.stand_in()
	kit.play_a1(Story)
	_drain()
	kit.eq(game._story_scene(), "L_M1_Archive", "Story moved on to B")
	kit.ok(game.can_switch_in_level("L_M1_Archive"), "B plays in the loaded file → in-level switch")
	var cam_before: Vector2 = game.camera.pos
	_signals.clear()
	var info: Dictionary = game.switch_now("L_M1_Archive", "", false)
	kit.ok(game.level == lvl and is_instance_valid(lvl), "no reload: the same level instance")
	kit.eq(str(lvl.level_id), "L_M1_Archive", "level plays B now")
	kit.eq(str(lvl.protagonist), "konrad", "level protagonist follows")
	kit.eq([info["from"], info["to"], info["took_over"], info["cut"]], ["alexei", "konrad", true, false], "switch info")
	kit.eq(_signals, [["L_M1_Archive", "konrad"]], "protagonist_switched emitted once")
	kit.ok(game.player != alexei, "a new body for Konrad")
	_driver_view("after A → B")
	_near(game.player.position, KONRAD_WAITS, "Konrad takes over where he stood in")
	kit.eq(game.player.get_facing(), -1.0, "and keeps looking towards Alexei")
	kit.ok(not alexei.is_in_group("player") and alexei.is_queued_for_deletion(), "Alexei's body left the group and frees itself")
	kit.ok(not alexei.is_physics_processing() and not alexei.visible, "the old body neither moves nor shows")
	kit.ok(not is_instance_valid(konrad_npc) or konrad_npc.is_queued_for_deletion(), "Konrad's stand-in retired")
	kit.ok(not is_instance_valid(konrad_npc) or not konrad_npc.is_in_group("npcs"), "…and left the npcs group at once")
	var si = game.stand_in()
	if not kit.ok(si != null and str(si.char_id) == "alexei", "Alexei stays in the level as a story NPC"):
		return true
	_near(si.position, Vector2(245, 300), "Alexei stands where he handed over")
	kit.ok(si.is_walking(), "Alexei walks to B's partner_spawn")
	_near(si.rest_position(), ALEXEI_POST, "his walk ends at the partner_spawn")
	kit.eq(_stand_ins().size(), 1, "exactly one stand-in")
	kit.ok(game._focus == null, "no hotspot focused by the switch")
	kit.ok(game.camera.target == game.player, "camera follows Konrad")
	_near(game.camera.pos, cam_before, "camera does not jump (glides from where it was)")
	kit.ok(game.camera.is_gliding() and game.camera.glide_progress() < 0.05, "glide started")
	var ex: Dictionary = game.save_extra()
	kit.eq([ex.get("scene"), ex.get("controlled")], ["L_M1_Archive", "konrad"], "save_extra: scene B, Konrad controlled")
	kit.eq(ex.get("stand_in"), {"char": "alexei", "pos": [ALEXEI_POST.x, ALEXEI_POST.y]},
		"save_extra stores where Alexei will stand (end of his walk)")
	# one body moves: the new player follows the input, the old body and the stand-in never poll it
	Input.action_press("move_right")
	game.player._physics_step(1.0 / 60.0)
	Input.action_release("move_right")
	kit.ok(game.player.velocity.x > 0.0, "Konrad walks on input")
	kit.ok(not si.is_physics_processing() and not si.has_method("_physics_step"), "the stand-in never polls input")
	game.player.velocity = Vector2.ZERO
	game.player.position = KONRAD_WAITS
	# a stand-in that is being retired stays hidden even if a Story signal arrives before the frame ends
	var probe: Node2D = game._make_stand_in("irina", Vector2(1500, 300), {})
	game._retire_npc(probe)
	probe._refresh()
	kit.ok(not probe.visible and not probe.is_in_group("npcs") and probe.is_queued_for_deletion(),
		"a retired stand-in cannot come back before it is freed")
	return true


func _glide() -> bool:
	var cam = game.camera
	var dt := 1.0 / 60.0
	var t := 0.0
	var first: Vector2 = cam.desired() - cam.pos
	var last_d: float = first.length()
	kit.ok(last_d > 100.0, "the glide has a way to go (%.1f px)" % last_d)
	var monotone := true
	var overshoot := false
	var t90 := -1.0
	var t99 := -1.0
	var t_end := -1.0
	while t < 3.0:
		cam._process(dt)
		t += dt
		var off: Vector2 = cam.desired() - cam.pos
		if off.length() > last_d + 0.001:
			monotone = false
		if off.dot(first) < -0.001:
			overshoot = true
		last_d = off.length()
		if t90 < 0.0 and cam.glide_progress() >= game.SWITCH_UNLOCK:
			t90 = t
		if t99 < 0.0 and cam.glide_progress() >= 0.99:
			t99 = t
		if t_end < 0.0 and not cam.is_gliding():
			t_end = t
	kit.ok(monotone, "the window approaches Konrad monotonically")
	kit.ok(not overshoot, "no overshoot (critically damped)")
	kit.ok(t99 >= 1.05 and t99 <= 1.35, "99 %% of the way after ~1.2 s (%.2f s)" % t99)
	kit.ok(t90 >= 0.55 and t90 <= 0.85, "input unlocks at 90 %% after ~0.7 s (%.2f s)" % t90)
	kit.ok(t_end > 0.0 and t_end < 2.95, "the glide ends and plain following resumes (%.2f s)" % t_end)
	_near(cam.pos, cam.desired(), "settled on Konrad", 0.01)
	return true


func _save_load() -> bool:
	var r: Dictionary = Saves.save("1")
	if not kit.ok(r.get("ok", false), "save inside the switch scene: %s" % r.get("error", "")):
		return true
	var doc = JSON.parse_string(FileAccess.get_file_as_string(TMP + "/saves/1.json"))
	kit.eq(doc["meta"]["scene"], "L_M1_Archive", "meta.scene is B")
	kit.eq(doc["meta"]["character"], "konrad", "meta.character is Konrad")
	kit.eq(doc["extra"].get("controlled"), "konrad", "extra.controlled")
	kit.eq(doc["extra"].get("stand_in"), {"char": "alexei", "pos": [ALEXEI_POST.x, ALEXEI_POST.y]}, "extra.stand_in")
	kit.eq(doc["extra"].get("player_pos"), [KONRAD_WAITS.x, KONRAD_WAITS.y], "extra.player_pos")
	var story_then := Story.save_json()
	game.player.position = Vector2(900, 300)     # play on a little …
	Story.new_game()                             # … and something else entirely before loading
	var l: Dictionary = Saves.load("1")
	if not kit.ok(l.get("ok", false), "load: %s" % l.get("error", "")):
		return true
	kit.eq(Story.save_json(), story_then, "Story state restored")
	game.apply_loaded_extra(Saves.last_loaded_extra)
	var lvl := _mount(game._story_scene())
	kit.eq(str(lvl.level_id), "L_M1_Archive", "the shared file plays B after loading")
	kit.eq(str(game.player.char_id), "konrad", "Konrad is controlled again")
	_near(game.player.position, KONRAD_WAITS, "Konrad where he was saved")
	var si = game.stand_in()
	if kit.ok(si != null and str(si.char_id) == "alexei", "Alexei stands in again"):
		_near(si.position, ALEXEI_POST, "Alexei where he was going to stand")
		kit.ok(not si.is_walking(), "no walk after loading")
	kit.eq(_stand_ins().size(), 1, "one stand-in after loading")
	_driver_view("after loading B")
	kit.ok(game._pending_stand_in == null and game._pending_spawn_pos == null, "pending restore data consumed")
	return true


func _memory_entry() -> bool:
	game.memory_mode = true
	game.memory_scene = "L_A1_Railyard"
	_mount("L_A1_Railyard", "SP_A1_Platform")
	kit.eq(str(game.player.char_id), "alexei", "memory of A opens with A's protagonist (Konrad is played now)")
	var si = game.stand_in()
	kit.ok(si != null and str(si.char_id) == "konrad", "Konrad stands in inside the memory")
	if si != null:
		_near(si.position, KONRAD_WAITS, "…at A's partner_spawn")
	kit.ok(not game.can_switch_in_level("L_M1_Archive"), "never a switch inside a memory")
	game.memory_scene = "L_M1_Archive"
	_mount("L_M1_Archive", "SP_M1_Arrival")
	kit.eq(str(game.player.char_id), "konrad", "memory of B opens with B's protagonist")
	si = game.stand_in()
	kit.ok(si != null and str(si.char_id) == "alexei", "Alexei stands in inside the memory of B")
	if si != null:
		_near(si.position, ALEXEI_POST, "…at B's partner_spawn")
	game.memory_mode = false
	game.memory_scene = ""
	# the present again (a return trip restores position and stand-in like a load)
	game._pending_spawn_pos = KONRAD_WAITS
	game._pending_stand_in = {"char": "alexei", "pos": [ALEXEI_POST.x, ALEXEI_POST.y]}
	_mount("L_M1_Archive")
	_driver_view("present after the memory")
	return true


func _cut_back() -> bool:
	Settings.values["reduced_motion"] = true
	kit.ok(game.switch_cuts(), "reduced motion → the switch cuts")
	Settings.values["reduced_motion"] = false
	kit.ok(not game.switch_cuts(), "normal motion → the switch glides")
	var alexei_npc = game.stand_in()
	alexei_npc.position = Vector2(420, 304)      # still on his way
	kit.play_m1(Story)
	_drain()
	kit.eq(game._story_scene(), "L_C3_Station", "Story moved on to A2 (Alexei)")
	var info: Dictionary = game.switch_now("L_C3_Station", "", true)
	kit.eq([info["from"], info["to"], info["took_over"]], ["konrad", "alexei", true], "control goes back to Alexei")
	_driver_view("after B → A2")
	_near(game.player.position, Vector2(420, 304), "Alexei takes over where he stood")
	_near(game.camera.pos, game.camera.desired(), "cut: the camera is on Alexei at once")
	kit.ok(not game.camera.is_gliding(), "cut: no glide")
	var si = game.stand_in()
	kit.ok(si != null and str(si.char_id) == "konrad", "Konrad stays as the stand-in")
	if si != null:
		_near(si.position, KONRAD_WAITS, "Konrad where he handed over")
		kit.ok(not si.is_walking(), "A2 names no partner_spawn: he stays")
		kit.ok(si.rig.is_flipped() or si.rig.is_turning(), "Konrad turns to Alexei (left)")
	kit.eq(_stand_ins().size(), 1, "one stand-in")
	return true


func _hidden_level() -> bool:
	var lvl: Node = game.level
	lvl.visible = false                           # what a §12.5 cinematic on the way leaves behind
	lvl.process_mode = Node.PROCESS_MODE_DISABLED
	kit.ok(game.switch_cuts(), "a hidden level makes the switch a cut")
	kit.play_c3a(Story)
	_drain()
	kit.eq(game._story_scene(), "L_C3_Hall", "Story moved on to B2 (Konrad)")
	var info: Dictionary = game.switch_now("L_C3_Hall", "", true)
	kit.ok(lvl.visible and lvl.process_mode == Node.PROCESS_MODE_INHERIT, "the level is shown and runs again")
	kit.eq(info["took_over"], false, "an explicit switch_spawn wins over the stand-in's spot")
	_near(game.player.position, SWITCH_SPOT, "Konrad takes over at B2's switch_spawn")
	_driver_view("after A2 → B2")
	var si = game.stand_in()
	kit.ok(si != null and str(si.char_id) == "alexei", "Alexei stands in")
	if si != null:
		_near(si.position, Vector2(420, 304), "Alexei where he handed over")
	kit.eq(_stand_ins().size(), 1, "Konrad's stand-in gone, one stand-in left")
	return true


func _same_person() -> bool:
	var body: Node = game.player
	var si = game.stand_in()
	var info: Dictionary = game.switch_now("L_M1_Archive", "", true)   # Konrad's scene after Konrad's scene
	kit.eq([info["from"], info["to"]], ["konrad", "konrad"], "same protagonist")
	kit.ok(game.player == body and is_instance_valid(body) and not body.is_queued_for_deletion(), "the body stays")
	kit.ok(game.stand_in() == si, "the stand-in stays")
	kit.eq(str(game.level.level_id), "L_M1_Archive", "the level plays the new scene")
	return true


func _untouched() -> bool:
	var keep: Dictionary = game.level_overrides.duplicate()
	var keep_sw: Dictionary = game.ext.switches.duplicate(true)
	game.level_overrides.clear()
	for s in SWITCHES:
		game.ext.switches.erase(s)
	var expected := {"L_A1_Railyard": "res://scenes/levels/L_A1_Railyard.tscn",
		"L_M1_Archive": "res://scenes/levels/L_M1_Archive.tscn",
		"L_C3_Station": "res://scenes/levels/L_C3_Station.tscn", "L_C3_Hall": "res://scenes/levels/L_C3_Hall.tscn"}
	for s in expected:
		kit.eq(game.level_file(s), expected[s], s + " keeps its own level file")
		kit.ok(not game.is_switch_scene(s), s + " is no switch scene")
		kit.eq(game.scene_partner(s), "", s + " has no stand-in")
	var lvl: Node = (load(expected["L_A1_Railyard"]) as PackedScene).instantiate()
	game._adopt_scene(lvl, "L_A1_Railyard")
	kit.eq([str(lvl.level_id), str(lvl.protagonist)], ["L_A1_Railyard", "alexei"], "a level of its own is not changed")
	game._adopt_scene(lvl, "res://scenes/levels/L_A1_Railyard.tscn")
	kit.eq(str(lvl.level_id), "L_A1_Railyard", "--scene=res://… keeps the file's own id")
	lvl.free()
	game.level_overrides.merge(keep, true)
	game.ext.switches.merge(keep_sw, true)
	return true


func _hud_plate() -> bool:
	var h: Control = (load(HUD_SCENE) as PackedScene).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(h)
	kit.track(h)
	h.show_hud()
	kit.ok(not h.is_protagonist_tag_visible(), "no plate before a switch")
	h.show_protagonist("konrad")
	kit.ok(h.is_protagonist_tag_visible(), "plate shows when control passes")
	kit.eq(h._who_label.text, UIKit.char_name("konrad").to_upper(), "plate names the protagonist")
	kit.ok(h._who.offset_right > h._who.offset_left, "plate has a width (centred)")
	h.hide_hud()
	kit.ok(not h.is_protagonist_tag_visible(), "plate hidden with the HUD (cinematic, photo mode)")
	h.show_hud()
	kit.ok(h.is_protagonist_tag_visible(), "…and back while its time runs")
	h.show_protagonist("none")
	kit.ok(h.is_protagonist_tag_visible(), "'none' changes nothing")
	return true
