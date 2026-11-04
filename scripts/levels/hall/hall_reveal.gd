extends Node3D
## L_M1_HallReveal — cinematic "Great Hall reveal" (shot S011, data/v3/cinematics.json LS_M1_Hall), Mode C.
## Owner: great_hall_3d.  Rendered in 3D inside the 640x360 world SubViewport in pixel-art style:
## toon-quantised light (pixel3d_toon / pixel3d_sprite), full-screen post quad with 1 px depth/normal
## outlines, banded fog, screen-space snow and a palette snap to pg.PALETTES['berlin'] (pixel3d_post).
##
## Contract for the lead (TECHNICAL_ARCHITECTURE §2/§3):
##   signal finished                  emitted exactly once per run (end of play() or skip(); a second
##                                    skip() or a skip() after the natural end does not emit again)
##   func play()                      starts the ~11 s sequence from t = 0
##   func skip()                      jumps to the final composed frame, emits `finished` once
##   func set_people_sprites(paths)   {role: "res://.../sheet.png" or any PNG}; roles: berlin_father,
##                                    berlin_mother, berlin_child, guard  (sheets: first idle_side frame)
## Extras (optional): signal cue(key) — subtitle/audio cue keys from data/locale/de_hall.json;
##   seek(t), set_paused(p), get_time(), get_shot_id() for tooling and the visual test harness.
## Shots: h1 0–3 s crane out of the archive window, h2 3–8 s establishing, h3 8–11 s slow push and hold.

signal finished
signal cue(key: String)

const Builder := preload("res://scripts/levels/hall/hall_builder.gd")
const Rig := preload("res://scripts/levels/hall/hall_camera_rig.gd")
const People := preload("res://scripts/levels/hall/hall_people.gd")
const POST_SHADER := preload("res://assets/shaders/pixel3d_post.gdshader")
const TEX := "res://assets/architecture/great_hall/"

@export var level_id := "L_M1_HallReveal"
@export var protagonist := "none"
@export_enum("oblique", "side", "3d", "cinematic") var mode := "3d"
@export var ambience := ""
@export var music := ""
## Key the lead's Game._apply_grade() looks up in data/grades.json.  This level already outputs final
## palette colours from its own post process; an identity grade (no vignette/grain) keeps them exact.
@export var grade_preset := "hall_3d"
@export var autoplay := false
@export_range(0.0, 1.0) var snow_density := 0.55
## Seconds at which the people switch to texel lock (camera has settled into h2).
@export var lock_from := 3.0
## Time at which the lit window above the family is closed (h3 story beat).
@export var window_close_at := 9.55

## Shot table (mirrors LS_M1_Hall).
const SHOTS := [
	{"id": "h1", "start": 0.0, "end": 3.0},
	{"id": "h2", "start": 3.0, "end": 8.0},
	{"id": "h3", "start": 8.0, "end": 11.0},
]
## Subtitle / audio cues (keys in data/locale/de_hall.json); the lead decides how to present them.
const CUES := [
	[0.15, "hall.cue.archive_room"],
	[1.6, "hall.cue.tram_bell"],
	[3.6, "hall.cue.loudspeaker_1"],
	[8.4, "hall.cue.loudspeaker_2"],
	[9.55, "hall.cue.window_closes"],
]

var camera: Camera3D
var post: MeshInstance3D
var post_mat: ShaderMaterial
var rig := Rig.new()
var people: Node3D
var builder := Builder.new()
var env: Environment

var _t := 0.0
var _playing := false
var _paused := false
var _finished := false
var _cue_i := 0
var _saved_vp := {}
var _vp_size := Vector2(640, 360)
var _pending_people: Dictionary = {}


func _ready() -> void:
	camera = get_node_or_null("Camera") as Camera3D
	if camera == null:
		camera = Camera3D.new()
		camera.name = "Camera"
		add_child(camera)
	_configure_viewport()
	_vp_size = _viewport_size()
	_make_environment()
	# calibrate the facade rhythm against the final composed frame
	var t0 := Time.get_ticks_usec()
	var final_pose := rig.sample(rig.duration())
	builder.build(self, {"cam": final_pose["pos"], "shift": (final_pose["shift"] as Vector2).round(),
		"vp": _vp_size, "f": Rig.focal_px(_vp_size.y)})
	builder.stats["build_ms"] = snappedf((Time.get_ticks_usec() - t0) / 1000.0, 0.1)
	people = People.new()
	people.name = "People"
	add_child(people)
	if not _pending_people.is_empty():
		for k in _pending_people:
			if _pending_people[k] != null and str(_pending_people[k]) != "":
				people.overrides[k] = str(_pending_people[k])
	people.setup(builder.people_spec)
	# reference pose for the sprite world sizes = first frame of h2
	rig.apply(camera, lock_from, _vp_size)
	people.calibrate(rig)
	_make_post()
	camera.current = true
	_apply(0.0)
	if autoplay:
		play()


func _exit_tree() -> void:
	_restore_viewport()


# ------------------------------------------------------------------------------ public API
func play() -> void:
	_t = 0.0
	_cue_i = 0
	_finished = false
	_playing = true
	_paused = false
	_apply(0.0)


func skip() -> void:
	if _finished:
		return
	_playing = false
	_t = rig.duration()
	_apply(_t)
	_finish()


func set_people_sprites(paths: Dictionary) -> void:
	if people == null:
		_pending_people.merge(paths, true)       # applied in _ready()
		return
	people.set_overrides(paths)
	rig.apply(camera, lock_from, _vp_size)
	people.calibrate(rig)
	_apply(_t)


func seek(t: float) -> void:
	_t = clampf(t, 0.0, rig.duration())
	_apply(_t)


func set_paused(p: bool) -> void:
	_paused = p


## Optional: dithered palette fade to black inside the 3D post (0..1).  The lead normally fades the overlay.
func set_fade(amount: float) -> void:
	if post_mat:
		post_mat.set_shader_parameter("fade", clampf(amount, 0.0, 1.0))


func get_time() -> float:
	return _t


func get_duration() -> float:
	return rig.duration()


func get_shot_id() -> String:
	for s in SHOTS:
		if _t < float(s["end"]):
			return str(s["id"])
	return "h3"


func is_playing() -> bool:
	return _playing


## Level-contract shims (3D cinematic has no walkable playfield).
func get_spawn(_name: String) -> Vector2:
	return Vector2.ZERO


func get_camera_bounds() -> Rect2:
	return Rect2(0, 0, 640, 360)


func is_walkable(_pos: Vector2) -> bool:
	return false


# ------------------------------------------------------------------------------ internals
func _process(delta: float) -> void:
	if not _playing or _paused:
		return
	_t = minf(_t + delta, rig.duration())
	_apply(_t)
	while _cue_i < CUES.size() and _t >= float(CUES[_cue_i][0]):
		cue.emit(str(CUES[_cue_i][1]))
		_cue_i += 1
	if _t >= rig.duration():
		_playing = false
		_finish()


func _finish() -> void:
	if _finished:
		return
	_finished = true
	finished.emit()


func _viewport_size() -> Vector2:
	var vp := get_viewport()
	if vp == null:
		return Vector2(640, 360)
	return Vector2(vp.get_visible_rect().size)


func _apply(t: float) -> void:
	var vs := _viewport_size()
	if vs != _vp_size:
		_vp_size = vs
	var st := rig.apply(camera, t, _vp_size)
	if people:
		people.update_sprites(rig, t >= lock_from - 0.0001)
	if post_mat:
		post_mat.set_shader_parameter("lens_shift_px", st["shift"])
		post_mat.set_shader_parameter("cam_pos", st["pos"])
		post_mat.set_shader_parameter("time", t)
		post_mat.set_shader_parameter("px_per_m_at_1m", Rig.focal_px(_vp_size.y))
		# smoke ribbons drift ~1.5 px/s to the right
		post_mat.set_shader_parameter("smoke_offset_px", Vector2(-floorf(t * 1.5), 0.0))
	_update_story_window(t)


func _update_story_window(t: float) -> void:
	var m: ShaderMaterial = builder.story_window_mat
	if m == null:
		return
	# the curtain is drawn in two beats: half, then dark
	var e := 1.0
	if t >= window_close_at + 0.35:
		e = 0.0
	elif t >= window_close_at:
		e = 0.45
	m.set_shader_parameter("emission_energy", e)
	m.set_shader_parameter("albedo", Color(1, 1, 1) if e > 0.5 else (Color(0.55, 0.45, 0.42) if e > 0.0
		else Color(0.18, 0.15, 0.2)))
	m.set_shader_parameter("flag", 0.75 if e > 0.0 else 0.0)


func _make_environment() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0, 0, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#3A3048")
	env.ambient_light_energy = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_exposure = 1.0
	env.tonemap_white = 1.0
	env.glow_enabled = false
	env.ssao_enabled = false
	env.ssr_enabled = false
	env.ssil_enabled = false
	env.sdfgi_enabled = false
	env.fog_enabled = false
	env.volumetric_fog_enabled = false
	env.adjustment_enabled = false
	camera.environment = env
	var attrs := CameraAttributesPractical.new()
	attrs.auto_exposure_enabled = false
	attrs.dof_blur_far_enabled = false
	attrs.dof_blur_near_enabled = false
	camera.attributes = attrs


func _make_post() -> void:
	post_mat = ShaderMaterial.new()
	post_mat.shader = POST_SHADER
	post_mat.render_priority = 127
	for pair in [["sky_tex", "sky.png"], ["fog_tex", "fog.png"], ["smoke_tex", "smoke.png"]]:
		var p: String = TEX + str(pair[1])
		if ResourceLoader.exists(p):
			post_mat.set_shader_parameter(str(pair[0]), load(p))
	post_mat.set_shader_parameter("sky_anchor", Vector2(512, 430))
	post_mat.set_shader_parameter("snow_density", snow_density)
	post = MeshInstance3D.new()
	post.name = "PixelPost"
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	post.mesh = q
	post.material_override = post_mat
	post.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	post.extra_cull_margin = 16384.0
	post.ignore_occlusion_culling = true
	post.position = Vector3(0, 0, -1.0)
	camera.add_child(post)


## Pixel-art rendering needs plain rasterisation: no MSAA/FXAA/TAA/debanding/upscaling on the viewport the
## level renders into.  Previous values are restored when the level leaves the tree.
func _configure_viewport() -> void:
	var vp := get_viewport()
	if vp == null:
		return
	_saved_vp = {"msaa_3d": vp.msaa_3d, "screen_space_aa": vp.screen_space_aa, "use_taa": vp.use_taa,
		"use_debanding": vp.use_debanding, "scaling_3d_scale": vp.scaling_3d_scale,
		"scaling_3d_mode": vp.scaling_3d_mode}
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	vp.use_taa = false
	vp.use_debanding = false
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = 1.0


func _restore_viewport() -> void:
	var vp := get_viewport()
	if vp == null or _saved_vp.is_empty():
		return
	for k in _saved_vp:
		vp.set(k, _saved_vp[k])
	_saved_vp = {}
