extends Node3D
## L_M1_Parade — the second Great Hall cinematic (owner: parade), played right after L_M1_HallReveal: later that
## day the regime stages a massive military parade on the plaza in front of the Great Hall.  Mode C (3D pixel
## render in the low-res world viewport, palette 'berlin'), same pipeline and API as hall_reveal.gd; the whole
## hall set is reused read-only (hall_builder.gd, hall_people.gd, hall_camera_rig.gd, pixel3d_* shaders).
##
## Contract for the lead (TECHNICAL_ARCHITECTURE §2/§3, like the reveal):
##   signal finished          exactly once per run (natural end or skip(); repeated skip() never re-emits)
##   signal cue(key)          timed keys from data/locale/de_parade.json: "parade.cue.*" = spoken lines
##                            (loudspeaker = subtitle, konrad = inner voice); "parade.sfx.*" = sound cues
##                            (played by the level itself through Audio when own_sfx is on)
##   play() / skip() / seek(t) / set_paused(p) / set_fade(a) / get_time() / get_duration() / get_shot_id()
## Tone (STORY_BIBLE §2): oppressive, never celebratory — faceless helmeted masses at a distance, cold grey light,
## the crowd's forced attendance and fear in the foreground, the cleared street at the end (human cost).
## Insignia: banners/flags through Symbols.pick (hall_builder materials, flag_limp.png / _hist).

signal finished
signal cue(key: String)

const Builder := preload("res://scripts/levels/hall/hall_builder.gd")
const Rig := preload("res://scripts/levels/hall/hall_camera_rig.gd")
const People := preload("res://scripts/levels/hall/hall_people.gd")
const Shots := preload("res://scripts/levels/parade/parade_shots.gd")
const ParadeSet := preload("res://scripts/levels/parade/parade_set.gd")
const POST_SHADER := preload("res://assets/shaders/pixel3d_post.gdshader")
const HALL_TEX := "res://assets/architecture/great_hall/"
const TEX := "res://assets/architecture/parade/"

@export var level_id := "L_M1_Parade"
@export var protagonist := "none"
@export_enum("oblique", "side", "3d", "cinematic") var mode := "3d"
@export var ambience := ""
@export var music := ""
## Identity grade: the 3D post already outputs final palette colours (data/grades.json "hall_3d").
@export var grade_preset := "hall_3d"
@export var autoplay := false
## Play the "parade.sfx.*" cues (boots, tanks, jets, loudspeaker chime) through the Audio autoload.
@export var own_sfx := true
@export_range(0.0, 1.0) var snow_density := 0.3

const CUES := [
	[0.6, "parade.sfx.pa_chime"],
	[0.9, "parade.cue.loudspeaker_1"],
	[6.6, "parade.sfx.boots"],
	[12.6, "parade.sfx.tanks"],
	[18.8, "parade.sfx.pa_chime"],
	[19.1, "parade.cue.loudspeaker_2"],
	[25.0, "parade.cue.loudspeaker_3"],
	[30.8, "parade.sfx.jets"],
	[36.3, "parade.cue.konrad"],
	[41.2, "parade.cue.loudspeaker_4"],
]
const SFX_GAIN := {"parade.sfx.boots": -3.0, "parade.sfx.tanks": -1.0, "parade.sfx.jets": -2.0,
	"parade.sfx.pa_chime": -8.0}

var camera: Camera3D
var post: MeshInstance3D
var post_mat: ShaderMaterial
var rig := Rig.new()
var shots := Shots.new()
var builder := Builder.new()
var pset: Node3D
var people: Node3D
var env: Environment

var _t := 0.0
var _playing := false
var _paused := false
var _finished := false
var _cue_i := 0
var _saved_vp := {}
var _vp_size := Vector2(640, 360)
var _halos: Array = []
## Script cost of the per-frame update in microseconds: {last, max, sum, n}
var perf := {"last": 0, "max": 0, "sum": 0, "n": 0}


func _ready() -> void:
	camera = get_node_or_null("Camera") as Camera3D
	if camera == null:
		camera = Camera3D.new()
		camera.name = "Camera"
		add_child(camera)
	_configure_viewport()
	_vp_size = _viewport_size()
	_make_environment()
	var t0 := Time.get_ticks_usec()
	var cal := shots.sample(float(Shots.SHOTS[Shots.CAL_SHOT]["end"]) - 0.01)
	builder.build(self, {"cam": cal["pos"], "shift": (cal["shift"] as Vector2).round(), "vp": _vp_size,
		"f": Rig.focal_px(_vp_size.y)})
	_after_hall_build()
	pset = ParadeSet.new()
	pset.name = "Parade"
	add_child(pset)
	pset.build(builder)
	builder.stats["build_ms"] = snappedf((Time.get_ticks_usec() - t0) / 1000.0, 0.1)
	_halos = builder.halos.duplicate()
	_halos.append_array(pset.halos)
	people = People.new()
	people.name = "People"
	add_child(people)
	people.setup(_people_spec())
	rig.apply_pose(camera, cal["pos"], (cal["shift"] as Vector2), _vp_size)
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
	_t = shots.duration()
	_cue_i = CUES.size()
	_apply(_t)
	_finish()


func seek(t: float) -> void:
	_t = clampf(t, 0.0, shots.duration())
	_cue_i = 0
	while _cue_i < CUES.size() and float(CUES[_cue_i][0]) < _t:
		_cue_i += 1
	_apply(_t)


func set_paused(p: bool) -> void:
	_paused = p


## Dithered palette fade to black inside the 3D post (0..1).  The lead normally fades the overlay.
func set_fade(amount: float) -> void:
	if post_mat:
		post_mat.set_shader_parameter("fade", clampf(amount, 0.0, 1.0))


func set_people_sprites(paths: Dictionary) -> void:
	if people:
		people.set_overrides(paths)
		_apply(_t)


func get_time() -> float:
	return _t


func get_duration() -> float:
	return shots.duration()


func get_shot_id() -> String:
	return str(Shots.SHOTS[shots.shot_index(_t)]["id"])


func get_shot_ids() -> Array:
	var a: Array = []
	for s in Shots.SHOTS:
		a.append([str(s["id"]), float(s["start"]), float(s["end"])])
	return a


func is_playing() -> bool:
	return _playing


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
	_t = minf(_t + delta, shots.duration())
	_apply(_t)
	while _cue_i < CUES.size() and _t >= float(CUES[_cue_i][0]):
		_emit_cue(str(CUES[_cue_i][1]))
		_cue_i += 1
	if _t >= shots.duration():
		_playing = false
		_finish()


func _emit_cue(key: String) -> void:
	if own_sfx and key.begins_with("parade.sfx."):
		var au := get_node_or_null("/root/Audio")
		if au and au.has_method("sfx"):
			au.call("sfx", "parade_" + key.trim_prefix("parade.sfx."), float(SFX_GAIN.get(key, 0.0)), 0.0)
	cue.emit(key)


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
	var t_us := Time.get_ticks_usec()
	var vs := _viewport_size()
	if vs != _vp_size:
		_vp_size = vs
	var smp := shots.sample(t)
	var st := rig.apply_pose(camera, smp["pos"], smp["shift"], _vp_size)
	pset.update(t, float(smp["min_depth"]))
	people.update_sprites(rig, true, t)
	if post_mat:
		post_mat.set_shader_parameter("lens_shift_px", st["shift"])
		post_mat.set_shader_parameter("cam_pos", st["pos"])
		post_mat.set_shader_parameter("time", t)
		post_mat.set_shader_parameter("px_per_m_at_1m", Rig.focal_px(_vp_size.y))
		post_mat.set_shader_parameter("smoke_offset_px", Vector2(-floorf(t * 1.5), 0.0))
		_update_halos()
	var dt_us := Time.get_ticks_usec() - t_us
	perf["last"] = dt_us
	perf["max"] = maxi(int(perf["max"]), dt_us)
	perf["sum"] = int(perf["sum"]) + dt_us
	perf["n"] = int(perf["n"]) + 1


func _update_halos() -> void:
	var fpx: float = Rig.focal_px(_vp_size.y)
	var va := PackedVector4Array()
	var vb := PackedVector4Array()
	for h in _halos:
		if h.has("node"):
			continue
		var pr: Vector3 = rig.project(h["pos"])
		if pr.z <= 0.5:
			continue
		var r_px := clampf(float(h["r"]) * fpx / pr.z, 2.5, 64.0)
		if pr.x < -r_px or pr.y < -r_px or pr.x > _vp_size.x + r_px or pr.y > _vp_size.y + r_px:
			continue
		var col: Color = h["col"]
		va.append(Vector4(pr.x, pr.y, pr.z, r_px))
		vb.append(Vector4(col.r, col.g, col.b, float(h["k"])))
		if va.size() >= 32:
			break
	post_mat.set_shader_parameter("halo_count", va.size())
	if va.size() > 0:
		post_mat.set_shader_parameter("halo_a", va)
		post_mat.set_shader_parameter("halo_b", vb)


## Later that day: the street life is gone (everyone is on the plaza), the cleared blocks are dark, the
## neighbour's curtains stay closed, the light turns cold and grey.
func _after_hall_build() -> void:
	if builder.tram_node:
		builder.tram_node.visible = false
	var gl: ShaderMaterial = builder.mats.get("glass_lit")
	if gl:
		gl.set_shader_parameter("emission_energy", 0.0)
		gl.set_shader_parameter("albedo", Color(0.34, 0.31, 0.38))
		gl.set_shader_parameter("flag", 0.0)
	for c in builder.story_curtains:
		(c as Node3D).scale = Vector3.ONE
	if builder.story_sil:
		builder.story_sil.visible = false
	var m: ShaderMaterial = builder.story_window_mat
	if m:
		m.set_shader_parameter("emission_energy", 0.0)
		m.set_shader_parameter("albedo", Color(0.18, 0.15, 0.2))
		m.set_shader_parameter("flag", 0.0)
	var cm: ShaderMaterial = builder.story_curtain_mat
	if cm:
		cm.set_shader_parameter("emission_energy", 0.0)
		cm.set_shader_parameter("albedo", Color(0.32, 0.26, 0.3))
		cm.set_shader_parameter("flag", 0.0)
	for n in find_children("*", "DirectionalLight3D", true, false):
		var dl := n as DirectionalLight3D
		if dl.shadow_enabled:
			dl.light_color = Color("#A3ACB4")
			dl.light_energy *= 0.55
		else:
			dl.light_energy *= 1.15


func _people_spec() -> Array:
	var spec: Array = []
	for e in builder.people_spec:
		var role := str(e.get("role", ""))
		if role.begins_with("eagle_"):
			spec.append(e)
		elif role == "guard":                       # the lone guard at the end of the emptied street (p8)
			var g: Dictionary = e.duplicate()
			g["show"] = Vector2(40.4, 99.0)
			spec.append(g)
	var fz := ParadeSet.Z_CROWD_FRONT + 0.4
	var fx := ParadeSet.FAMILY_X
	var p5 := Vector2(24.4, 30.6)
	spec.append({"role": "berlin_father", "pos": Vector3(fx - 1.2, 0.0, fz + 0.15), "flip": false, "show": p5,
		"anim": "idle_side", "phase": 0.0})
	spec.append({"role": "berlin_child", "pos": Vector3(fx + 0.05, 0.0, fz - 0.2), "flip": false, "show": p5,
		"anim": "idle_side", "phase": 0.3})
	spec.append({"role": "berlin_mother", "pos": Vector3(fx + 1.25, 0.0, fz + 0.1), "flip": true, "show": p5,
		"anim": "idle_side", "phase": 0.55})
	spec.append({"role": "flag_limp", "file": TEX + "flag_limp.png", "pos": Vector3(fx + 0.32, 0.42, fz - 0.3),
		"show": p5, "face_motion": false})
	spec.append({"role": "konrad", "pos": Vector3(-104.0, 0.0, ParadeSet.Z_CROWD_BACK + 13.0), "flip": false,
		"show": Vector2(35.4, 40.6), "anim": "idle_back", "phase": 0.2})
	return spec


func _make_environment() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0, 0, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#3A3A4C")
	env.ambient_light_energy = 0.6
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
	for pair in [["sky_tex", TEX + "sky_parade.png"], ["fog_tex", TEX + "fog_parade.png"],
			["smoke_tex", HALL_TEX + "smoke.png"]]:
		var p: String = str(pair[1])
		if ResourceLoader.exists(p):
			post_mat.set_shader_parameter(str(pair[0]), load(p))
	post_mat.set_shader_parameter("sky_anchor", Vector2(512, 430))
	post_mat.set_shader_parameter("snow_density", snow_density)
	post_mat.set_shader_parameter("smoke_alpha", 0.6)
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


## Pixel-art rendering needs plain rasterisation (no MSAA/FXAA/TAA/debanding/upscaling); restored on exit.
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
