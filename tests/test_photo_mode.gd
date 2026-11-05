extends RefCounted
## Photo mode (scripts/ui/photo_mode.gd): file names, filter presets restore the grade exactly, bounds clamping,
## open/close restores camera / player / grade, and it never opens in a cinematic, a dialogue or without a level.
## Uses a mock Game (ui_kit overrides) with a real WorldCamera and the real post_grade shader material.

const TKit := preload("res://tests/support/test_kit.gd")
const UIKit := preload("res://scripts/ui/ui_kit.gd")
const PM := preload("res://scripts/ui/photo_mode.gd")
const CAM := preload("res://scripts/render/world_camera.gd")
const SHADER := "res://assets/shaders/post_grade.gdshader"
const SCENE := "res://scenes/ui/PhotoMode.tscn"


class MockGame extends Node:
	var level: Node = null
	var camera: Node = null
	var view = null
	var grade: ColorRect = null
	var player: Node = null
	var overlay = null
	var in_cinematic := false
	var busy := false
	var input_locked := false


class MockUI extends Node:
	var cinematic_mode := false
	var dialogue_open := false

	func is_modal_open() -> bool:
		return dialogue_open


var kit: TKit


func run() -> Array:
	kit = TKit.new()
	UIKit.overrides["Audio"] = null   # UI cues off: a one-shot still playing at quit would be reported as a leak
	kit.run_case("file_name_format", _file_names)
	kit.run_case("filter_presets_restore_grade", _filters)
	kit.run_case("bounds_clamping", _clamping)
	kit.run_case("open_close_restores_state", _open_close)
	kit.run_case("blocked_in_cinematic_dialogue_or_without_level", _blocked)
	UIKit.overrides.erase("Game")
	UIKit.overrides.erase("Audio")
	kit.cleanup()
	UIKit.clear_cache()          # textures cached by the panel (Kit.tex) must not outlive the test run
	return kit.failures


func _file_names() -> bool:
	var dt := {"year": 2026, "month": 11, "day": 5, "hour": 9, "minute": 3, "second": 7}
	kit.eq(PM.photo_file_name(dt), "ashes_20261105_090307.png", "YYYYMMDD_HHMMSS")
	kit.eq(PM.photo_file_name(dt, 2), "ashes_20261105_090307_2.png", "second photo in the same second")
	kit.eq(PM.photo_file_name({"year": 1946, "month": 12, "day": 31, "hour": 23, "minute": 59, "second": 59}),
		"ashes_19461231_235959.png", "zero padding / end of year")
	var re := RegEx.create_from_string("^ashes_\\d{8}_\\d{6}\\.png$")
	kit.ok(re.search(PM.photo_file_name(Time.get_datetime_dict_from_system())) != null, "system clock name matches pattern")
	return true


func _material() -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = load(SHADER)
	return mat


## The same values Game._apply_grade writes for the karsk preset.
func _set_level_grade(mat: ShaderMaterial) -> void:
	mat.set_shader_parameter("lift", Vector3(0.012, 0.018, 0.024))
	mat.set_shader_parameter("gamma", Vector3(1, 1, 1))
	mat.set_shader_parameter("gain", Vector3(1, 1, 1))
	mat.set_shader_parameter("tint", Vector3(0.98, 1.0, 1.02))
	mat.set_shader_parameter("saturation", 0.94)
	mat.set_shader_parameter("vignette", 0.27)
	mat.set_shader_parameter("grain", 0.0117)
	mat.set_shader_parameter("palette_strength", 0.468)


func _filters() -> bool:
	var mat := _material()
	_set_level_grade(mat)
	var base := PM.read_grade(mat)
	kit.eq(base.size(), PM.GRADE_KEYS.size(), "snapshot has every grade key")
	for f in PM.FILTERS:
		PM.write_grade(mat, PM.compose_grade(base, f))
		var now := PM.read_grade(mat)
		if f == "normal":
			kit.eq(now, base, "Normal = level grade")
		else:
			kit.ne(now, base, "filter %s changes the grade" % f)
			kit.eq(now["palette_strength"], base["palette_strength"], "filter %s keeps the palette snap" % f)
		PM.write_grade(mat, base)
		kit.eq(PM.read_grade(mat), base, "grade restored after " + f)
	var p := PM.compose_grade(base, "normal", 0, 0)
	kit.eq(p["vignette"], 0.0, "vignette step off")
	kit.eq(p["grain"], 0.0, "grain off")
	p = PM.compose_grade(base, "sepia", PM.VIGNETTES.size() - 1, 1)
	kit.eq(p["vignette"], PM.VIGNETTES[PM.VIGNETTES.size() - 1], "strongest vignette")
	kit.ok(float(p["grain"]) >= PM.GRAIN_ON, "grain on")
	kit.eq(p["saturation"], 0.0, "sepia is monochrome")
	# a material that never got a grade (shader defaults = null) comes back to defaults exactly
	var mat2 := _material()
	var b2 := PM.read_grade(mat2)
	PM.write_grade(mat2, PM.compose_grade(b2, "night", 2, 1))
	kit.ne(PM.read_grade(mat2), b2, "night writes overrides")
	PM.write_grade(mat2, b2)
	kit.eq(PM.read_grade(mat2), b2, "shader defaults restored")
	return true


func _approx(a: Vector2, b: Vector2, msg: String) -> void:
	kit.ok(a.is_equal_approx(b), "%s: got %s, want %s" % [msg, a, b])


func _clamping() -> bool:
	var v := PM.VIEW
	var r := Rect2(0, 0, 1200, 360)
	_approx(PM.clamp_center(Vector2(-100, -100), r, v, 1.0), Vector2(320, 180), "zoom 1, top-left")
	_approx(PM.clamp_center(Vector2(5000, 5000), r, v, 1.0), Vector2(880, 180), "zoom 1, right edge")
	_approx(PM.clamp_center(Vector2(0, 0), r, v, 2.0), Vector2(160, 90), "zoom 2 reaches the corner")
	_approx(PM.clamp_center(Vector2(5000, 5000), r, v, 3.0), Vector2(1200.0 - 640.0 / 6.0, 300), "zoom 3 bottom-right")
	_approx(PM.clamp_center(Vector2(9, 9), Rect2(100, 50, 400, 200), v, 1.0), Vector2(300, 150), "small region centred")
	_approx(PM.clamp_center(Vector2(700, 200), Rect2(-200, 0, 1400, 400), v, 1.0), Vector2(700, 200), "inside stays")
	return true


func _mock() -> MockGame:
	var g: MockGame = kit.track(MockGame.new())
	g.level = kit.track(Node.new())
	var cam: Camera2D = kit.track(CAM.new())
	cam.bounds = Rect2(0, 0, 1600, 400)
	cam.set_top_left(Vector2(400, 20))
	g.camera = cam
	var rect: ColorRect = kit.track(ColorRect.new())
	rect.material = _material()
	_set_level_grade(rect.material)
	g.grade = rect
	g.player = kit.track(Node2D.new())
	UIKit.overrides["Game"] = g
	return g


func _photo_mode() -> Control:
	var pm: Control = (load(SCENE) as PackedScene).instantiate()
	(Engine.get_main_loop() as SceneTree).root.add_child(pm)
	return kit.track(pm)


func _open_close() -> bool:
	var g := _mock()
	var pm := _photo_mode()
	var cam = g.camera
	var base := PM.read_grade(g.grade.material)
	cam.vel = Vector2(3, -1)
	kit.ok(pm.open(), "opens in free play")
	kit.ok(pm.is_open, "is_open")
	kit.eq(cam.cinematic, true, "camera taken over")
	pm.pan_by(Vector2(5000, 0))
	kit.eq(cam.pos, Vector2(960, 20), "pan clamped at the right bound")
	pm.pan_by(Vector2(-99999, 99999))
	kit.eq(cam.pos, Vector2(0, 40), "pan clamped at the left / bottom bound")
	pm.set_zoom(3)
	kit.eq(pm.zoom, 3, "zoom 3")
	pm.set_zoom(7)
	kit.eq(pm.zoom, PM.MAX_ZOOM, "zoom capped")
	pm.set_filter("night")
	kit.ne(PM.read_grade(g.grade.material), base, "filter applied")
	pm.change("vignette", 1)
	pm.change("grain", 1)
	pm.set_frame("print")
	kit.eq(pm.frame_id, "print", "frame set")
	pm.set_figure_visible(false)
	kit.eq(g.player.visible, false, "figure hidden")
	pm.close()
	kit.ok(not pm.is_open, "closed")
	kit.eq(cam.pos, Vector2(400, 20), "camera position restored")
	kit.eq(cam.vel, Vector2(3, -1), "camera spring velocity restored")
	kit.eq(cam.cinematic, false, "camera follows again")
	kit.eq(g.player.visible, true, "figure visible again")
	kit.eq(PM.read_grade(g.grade.material), base, "level grade restored")
	kit.eq(pm.zoom, 1, "zoom reset")
	return true


func _blocked() -> bool:
	var g := _mock()
	var pm := _photo_mode()
	g.in_cinematic = true
	kit.ok(not pm.open(), "not during a cinematic")
	g.in_cinematic = false
	g.busy = true
	kit.ok(not pm.open(), "not while Game is busy (interaction)")
	g.busy = false
	var ui: MockUI = kit.track(MockUI.new())
	pm.ui_root = ui
	ui.dialogue_open = true
	kit.ok(not pm.open(), "not over a dialogue / another panel")
	ui.dialogue_open = false
	ui.cinematic_mode = true
	kit.ok(not pm.open(), "not in UI cinematic mode")
	pm.ui_root = null
	g.level = null
	kit.ok(not pm.open(), "not without a level")
	kit.ok(not pm.is_open, "never opened")
	return true
