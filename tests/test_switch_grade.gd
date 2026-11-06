extends RefCounted
## Round 10 (NEXT_STEPS §1; owner: polish): the "grade" of a chapter switch (data/chapters/*.json "switches") is applied
## on a level load -- Game._setup_level → Game._apply_switch_grade -- the way the annex and the tunnels pick theirs per
## scene; a level that sets its grade itself (grade looks: registry, tunnels, annex) keeps its own, also when a switch
## would name another grade; an unknown grade key changes nothing. Every switch grade of the chapters exists.
## Fixture (memory only, data/ is never touched): Game.ext.switches gets test settings (reloaded afterwards); the plain
## test level scenes/levels/test/L_Test_Switch.tscn (grade_preset "veltrava", no looks) and the real L_C4_Annex /
## L_C4_Tunnels are mounted the way Game._load_level does it (without the frame wait) and run the real level setup.

const TKit := preload("res://tests/support/test_kit.gd")
const CAMERA := preload("res://scripts/render/world_camera.gd")
const PLAIN := "res://scenes/levels/test/L_Test_Switch.tscn"
const PLAIN_GRADE := "veltrava"          # the plain level's own grade_preset (its .tscn)
const PLAIN_SCENE := "L_C3_Station"      # a Story scene without switch settings of its own
const SWITCH_GRADE := "palais"           # an existing grade the test switch names
const OWN := {"L_C4_AnnexB": ["res://scenes/levels/L_C4_Annex.tscn", "annex"],
	"L_C4_TunnelsB": ["res://scenes/levels/L_C4_Tunnels.tscn", "tunnels_siding"]}

var kit: TKit
var game: Node
var _keep := {}


func run() -> Array:
	kit = TKit.new()
	game = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Game")
	if not kit.ok(game != null and game.has_method("_apply_switch_grade"), "Game autoload with _apply_switch_grade()"):
		return kit.failures
	_begin()
	kit.run_case("every_switch_grade_exists", _data)
	kit.run_case("switch_grade_applies_on_load", _applies)
	kit.run_case("levels_with_their_own_grade_untouched", _own_grade)
	_end()
	kit.cleanup()
	return kit.failures


func _begin() -> void:
	_keep = {"story": Story.save_json(), "camera": game.camera, "level": game.level, "player": game.player}
	Story.new_game()
	var cam: Camera2D = CAMERA.new()
	kit.mount(cam)
	game.camera = cam


func _end() -> void:
	_unmount()
	game.ext.reload()
	game.camera = _keep["camera"]
	game.level = _keep["level"]
	game.player = _keep["player"]
	if not Story.load_json(str(_keep["story"])).get("ok", false):
		Story.new_game()


## Instances `path` for Story scene `id` as Game._load_level() does and runs the real level setup.
func _mount(path: String, id: String) -> Node:
	_unmount()
	var lvl: Node = (load(path) as PackedScene).instantiate()
	lvl.set("ambience", "")                      # no players left running at exit (headless runner)
	lvl.set("music", "")
	game._adopt_scene(lvl, id)
	game._level_file = path
	(Engine.get_main_loop() as SceneTree).root.add_child(lvl)
	game.level = lvl
	game._setup_level("")
	return lvl


func _unmount() -> void:
	game.set_focus(null)
	var lvl = game.level
	game.level = null
	game.player = null
	game._stand_in = null
	game._level_file = ""
	if lvl != null and is_instance_valid(lvl) and lvl != _keep.get("level"):
		lvl.get_parent().remove_child(lvl)
		lvl.free()


func _data() -> bool:
	var n := 0
	for f in DirAccess.get_files_at("res://data/chapters"):
		if not f.ends_with(".json"):
			continue
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://data/chapters/" + f))
		if not (d is Dictionary):
			continue
		var sw = d.get("switches", {})
		for sid in (sw if sw is Dictionary else {}):
			var g := str((sw[sid] as Dictionary).get("grade", ""))
			if g != "":
				n += 1
				kit.ok(game.grades.has(g), "%s %s: switch grade '%s' exists" % [f, sid, g])
	kit.ok(n >= 6, "chapter switches with a grade checked (%d)" % n)
	return true


func _applies() -> bool:
	kit.ok(game.grades.has(SWITCH_GRADE) and SWITCH_GRADE != PLAIN_GRADE, "the test grade exists and differs")
	# without a switch grade the plain level keeps its own
	game.ext.switches.erase(PLAIN_SCENE)
	var lvl := _mount(PLAIN, PLAIN_SCENE)
	kit.eq(str(lvl.get("grade_preset")), PLAIN_GRADE, "no switch grade: the level's own grade")
	kit.ok(not game.level_sets_grade(lvl), "the plain level has no grade looks")
	# a switch grade applies on the load
	game.ext.switches[PLAIN_SCENE] = {"grade": SWITCH_GRADE}
	lvl = _mount(PLAIN, PLAIN_SCENE)
	kit.eq(str(lvl.get("grade_preset")), SWITCH_GRADE, "the switch grade applies on the level load")
	kit.eq(str(game.level.get("level_id")), PLAIN_SCENE, "for the Story scene the level plays")
	# an unknown key changes nothing (never the default look by a typo)
	game.ext.switches[PLAIN_SCENE] = {"grade": "no_such_grade_r10"}
	lvl = _mount(PLAIN, PLAIN_SCENE)
	kit.eq(str(lvl.get("grade_preset")), PLAIN_GRADE, "an unknown switch grade: the level keeps its own")
	game.ext.switches.erase(PLAIN_SCENE)
	_unmount()
	return true


func _own_grade() -> bool:
	for sid in OWN:
		var path: String = OWN[sid][0]
		var own: String = OWN[sid][1]
		kit.eq(str(game.ext.switch_settings(sid).get("grade", "")), own, "%s: the chapter switch names the same grade" % sid)
		var sw: Dictionary = game.ext.switches.get(sid, {}).duplicate(true)
		sw.erase("ambience")                     # no players left running at exit (headless runner)
		sw.erase("music")
		game.ext.switches[sid] = sw
		var lvl := _mount(path, sid)
		kit.ok(game.level_sets_grade(lvl), "%s sets its grade itself (grade looks)" % sid)
		kit.eq(str(lvl.get("grade_preset")), own, "%s: its own look's grade" % sid)
		# a switch naming another grade does not change a level that sets its own
		game.ext.switches[sid] = sw.merged({"grade": SWITCH_GRADE}, true)
		lvl = _mount(path, sid)
		kit.eq(str(lvl.get("grade_preset")), own, "%s: a switch with another grade leaves the level's own" % sid)
		_unmount()
	return true
