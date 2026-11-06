extends Node2D
## LS_A1_ToM1 -- the soft protagonist switch Alexei (Karsk, dusk) -> Konrad (Berlin, next morning).
## TECHNICAL_ARCHITECTURE §12.5: signal finished, configure(ctx), play(), skip() (idempotent, finished
## exactly once). Rendered in the world viewport under Game.level_root; camera via Game.camera (sub-pixel
## cinematic path), subtitles via Game.subtitle, music/ambience via Audio; Game owns the letterbox.
##
## Everything on screen is a pure function of the timeline time `t` (_apply), so the shot can be seeked
## frame-exactly (harness captures) and skipped at any moment. Sound cues fire only while playing forward.
##
## Shots (≈43.0 s):
##   1A  0.0  Karsk platform at dusk: the westbound train backs onto wagon 24-311 (C-17), clank, snow falls
##   1B  5.2  the locomotive (red star / hammer & sickle, or the neutral gear-and-wheat): whistle, cylinder
##            cocks, the slack runs out wagon by wagon (clank, clank ...), the drivers slip once, bite, and it
##            pulls out to the west; rods + Walschaerts valve gear in phase with the distance travelled,
##            exhaust beats 4 per revolution, rail-joint clatter per axle; camera pans along
##   1C 11.4  platform: the C-17 wagon slides out of frame, Alexei watches (Irina beside him, or alone with
##            the ledger under his arm); inner voice, different per branch
##   2  18.4  close-up: the rubber stamp comes down on the ledger -> red C-17, ink spreads
##   3  22.4  match dissolve (ordered dither): page -> Berlin plan, then the red stamp -> the pencil C-17 at
##            the identical position; sound bridge distant train whistle -> tram bell
##   4  26.0  Berlin, early morning snow: crane down from the Great Hall dome to the street, the tram stops
##            and pulls away, Konrad (who got off) crosses to the Bauarchiv and goes in; the banners work
##            in the wind (travelling cloth wave, gusts); inner voice
##   end 41.8 fade to black -> Game shows the chapter card and loads M1 at SP_M1_Arrival

signal finished

const LayerStack := preload("res://scripts/levels/layer_stack.gd")
const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const SnowFx := preload("res://scripts/levels/fx_snow.gd")
const DISSOLVE_SHADER := preload("res://assets/cinematics/a1m1/dither_dissolve.gdshader")
const A := "res://assets/cinematics/a1m1/"
const KE := "res://assets/environments/karsk_railyard/"
const SFX_DIR := "res://assets/audio/sfx/"

# ------------------------------------------------------------------ timeline (seconds)
const EXT := 2.4                           # 2026-11-05: longer departure (1B +1.2 s, 1C +1.2 s)
const T_COUPLE := 3.0
const T_SHOT_LOCO := 5.2
const T_WHISTLE := 5.6
const T_DEPART := 6.2
const T_SHOT_PLAT := 11.4
const T_LINE_A := 12.0
const T_TURN := 14.9 + EXT
const T_SHOT_STAMP := 16.0 + EXT
const T_PRESS := 17.25 + EXT
const T_LIFT := 17.75 + EXT
const T_DISSOLVE := 20.0 + EXT
const T_BERLIN := 23.6 + EXT
const T_CRANE0 := 24.6 + EXT
const T_CRANE1 := 31.6 + EXT
const T_TRAM_IN := 25.8 + EXT
const T_TRAM_STOP := 29.6 + EXT
const T_TRAM_GO := 31.2 + EXT
const T_KONRAD_WALK := 32.6 + EXT
const T_LINE_K := 33.0 + EXT
const T_DOOR_OPEN := 36.0 + EXT
const T_ENTER := 36.55 + EXT
const T_DOOR_CLOSE := 37.45 + EXT
const T_PIGEONS := 37.9 + EXT
const T_FADE := 39.4 + EXT
const DURATION := 40.6 + EXT

# ------------------------------------------------------------------ set geometry (world pixels)
const CLOSE_O := Vector2(2000, 0)
const BERLIN_O := Vector2(4000, 0)
const C17_X := 1200.0
const TRAIN := [["loco", 284.0], ["tender", 196.0], ["gondola", 180.0], ["boxcar", 196.0]]
const SIM_HZ := 240.0                      # departure simulation rate
const A0 := 12.5                           # traction (px/s^2 per unit train) once the regulator is open
const V_POWER := 36.0                      # px/s: above it constant power (acceleration falls with speed)
const SLACK := [1.0, 2.0, 2.0, 2.0]        # free slack per coupling: loco|tender, tender|gondola, ... |C-17
const SNATCH_KEEP := [0.85, 0.85, 0.88, 0.9]   # speed kept by the engine when each coupling snatches
const SLIP := [1.85, 2.6, 0.8]             # wheel slip window after T_DEPART (s) + regulator recovery (s)
const SLIP_REV := 1.5                      # extra driver revolutions while slipping
const JOINT := 150.0                       # rail length (px); joints at JOINT_X0 + n * JOINT
const JOINT_X0 := 75.0
const JET_POOL := 6
const CAM_K_A := [Vector2(1000, 0), Vector2(1022, 0)]
const CAM_K_B := [Vector2(250, 0), Vector2(200, 0)]
const CAM_K_C := [Vector2(1010, 0), Vector2(988, 0)]
const CAM_B := [Vector2(4190, -200), Vector2(4170, 0), Vector2(4135, 0)]
const K_REF := Vector2(1000, 0)            # reference camera for the Karsk parallax anchors
const B_REF := Vector2(4190, -200)         # reference camera for the Berlin parallax anchors
const ALEXEI_POS := Vector2(1452, 302)
const IRINA_POS := Vector2(1416, 300)
const TRAM_STOP_X := 380.0
const KONRAD_FROM := 500.0
const KONRAD_TO := 356.0
const PUFF_LIFE := 1.8
const PUFF_POOL := 24
const BANNER_X := [300.0, 386.0]

# ------------------------------------------------------------------ state
var ctx: Dictionary = {}
var branch := "keep_private"
var symbols := true
var t := 0.0
var playing := false
var layout: Dictionary = {}
var _built := false
var _finished_emitted := false
var _cue_done: Dictionary = {}
var _parallax: Array = []                 # {node, anchor, ref, p}
var _old_bounds := Rect2()
var _old_enabled := true
var _sets: Dictionary = {}
var _n: Dictionary = {}                   # named nodes
var _beats: PackedFloat32Array = PackedFloat32Array()
var _sim_d := PackedFloat32Array()         # loco travel west after T_DEPART (px) at SIM_HZ
var _sim_v := PackedFloat32Array()         # loco speed (px/s)
var _snatch := PackedFloat32Array()        # absolute times at which each coupling snatched taut
var _joint_t: Array = []                   # per vehicle: PackedFloat32Array of rail-joint hit times
var _joint_ev: Array = []                  # [time, joint_x] for every axle over a joint (sound cues)
var _puffs: Array = []
var _players: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _modulate: CanvasModulate
var _fade_rect: ColorRect
var _shake_until := -1.0
var _grade_state := ""
var _last_step := -1


# ================================================================== §12.5 API
func configure(c: Dictionary) -> void:
	ctx = c if c != null else {}
	var ch = ctx.get("choices", {})
	branch = "keep_private"
	if ch is Dictionary and str(ch.get("a1_choose", "")) == "share_with_irina":
		branch = "share_with_irina"
	symbols = bool(ctx.get("symbols", Symbols.enabled()))
	if _built:
		_apply_variants()


func play() -> void:
	if not _built:
		_build()
	t = 0.0
	_cue_done.clear()
	_finished_emitted = false
	playing = true
	_take_camera()
	Audio.stop_music(2.0)
	_apply(t)


func skip() -> void:
	if _finished_emitted:
		return
	playing = false
	_stop_sounds()
	_hide_subtitle()
	if _built:
		t = DURATION
		_apply(t)
	_finish()


## Harness helpers: seek renders the exact frame of time `time` without firing sound cues.
func seek(time: float) -> void:
	if not _built:
		_build()
	_take_camera()
	t = clampf(time, 0.0, DURATION)
	_apply(t)


func get_duration() -> float:
	return DURATION


func get_time() -> float:
	return t


# ================================================================== lifecycle
func _init() -> void:
	process_priority = 5           # after the world camera (-10)


func _ready() -> void:
	if not _built:
		_build()


func _process(delta: float) -> void:
	if not playing:
		return
	var prev := t
	t = minf(t + delta, DURATION)
	_apply(t)
	_cues(prev, t)
	if t >= DURATION:
		playing = false
		_finish()


func _exit_tree() -> void:
	_stop_sounds()
	if Game.view and Game.view.has_method("set_shake"):
		Game.view.set_shake(Vector2.ZERO)


func _finish() -> void:
	if _finished_emitted:
		return
	_finished_emitted = true
	if Game.view and Game.view.has_method("set_shake"):
		Game.view.set_shake(Vector2.ZERO)
	finished.emit()


func _take_camera() -> void:
	var cam = Game.camera
	if cam == null:
		return
	if _old_bounds == Rect2():
		_old_bounds = cam.bounds
		_old_enabled = cam.enabled
	cam.enabled = true
	cam.set_bounds(Rect2(-2000, -2000, 12000, 6000))
	cam.cinematic = true


# ================================================================== building
func _build() -> void:
	_built = true
	var lj = _json(A + "layout.json")
	layout = lj if lj is Dictionary else {}
	_modulate = CanvasModulate.new()
	add_child(_modulate)
	for sname in ["karsk", "close", "berlin"]:
		var s := Node2D.new()
		s.name = sname.capitalize()
		add_child(s)
		_sets[sname] = s
	_build_karsk()
	_build_close()
	_build_berlin()
	_build_overlays()
	_build_audio()
	_simulate()
	_compute_beats()
	_compute_joints()
	_apply_variants()


func _build_karsk() -> void:
	var S: Node2D = _sets["karsk"]
	var K: Dictionary = layout.get("karsk", {})
	# sky + clouds + re-used Karsk far layers (read-only), tinted to dusk silhouettes
	_par(S, _spr(A + "karsk/sky.png", false), K_REF + Vector2(-1, -1), K_REF, Vector2(0, 0), -100)
	_par(S, _spr(A + "karsk/clouds.png", false), K_REF + Vector2(-150, 34), K_REF, Vector2(0.04, 0), -98)
	var tints := {"far_city": [Color(0.40, 0.50, 0.53), Vector2(-120, 132), 0.12, -92],
		"far_industry": [Color(0.31, 0.41, 0.44), Vector2(-200, 99), 0.25, -88],
		"mid": [Color(0.24, 0.32, 0.35), Vector2(-400, 71), 0.45, -84],
		"poles": [Color(0.19, 0.24, 0.27), Vector2(-1000, 132), 0.86, -60]}
	var scene = _json(KE + "scene.json")
	var homes := {}
	if scene is Dictionary:
		for L in scene.get("layers", []):
			homes[str(L.get("name", ""))] = LayerStack._v2(L.get("pos", [0, 0]))
	for lname in tints:
		var spec: Array = tints[lname]
		var node := _spr(KE + lname + ".png", false, 0.0, 1, (lname == "far_city"))
		node.modulate = spec[0]
		_par(S, node, K_REF + spec[1], K_REF, Vector2(spec[2], 0), spec[3])
		_n["k_" + lname] = node
	# the A1 level's industrial smoke ribbons, re-anchored on the same layers (read-only re-use)
	if scene is Dictionary:
		for fx in scene.get("fx", []):
			var ln := str(fx.get("layer", ""))
			if str(fx.get("type", "")) != "anim_sprite" or not tints.has(ln) or not homes.has(ln):
				continue
			var off: Vector2 = LayerStack._v2(fx.get("pos", [0, 0])) - homes[ln]
			var frames := int(fx.get("frames", 1))
			var sm := _spr(KE + str(fx.get("file", "")), false, 0.0, frames)
			sm.modulate = (tints[ln][0] as Color).lightened(0.12)
			var spec2: Array = tints[ln]
			_par(S, sm, K_REF + spec2[1] + off, K_REF, Vector2(spec2[2], 0), int(spec2[3]) + 1)
			sm.set_meta("anim_fps", float(fx.get("fps", 5)))
			_n.get_or_add("k_smoke", []).append(sm)
	# yard (p = 1) and props
	var yard := _spr(A + "karsk/yard.png", true, 0.3)
	yard.position = LayerStack._v2(K.get("yard", [0, 140]))
	yard.z_index = -40
	S.add_child(yard)
	var pf := Node2D.new()
	pf.y_sort_enabled = true
	pf.name = "Playfield"
	S.add_child(pf)
	_n["k_pf"] = pf
	var rail: float = float(K.get("rail_y", 272))
	# train: loco body + wheels, tender, wagons, the C-17 wagon (re-used A1 prop) + tail lamp
	var x := C17_X
	var vehicles: Array = []
	for i in range(TRAIN.size() - 1, -1, -1):
		var v: Array = TRAIN[i]
		x -= float(v[1])
		vehicles.push_front([v[0], x])
	for v in vehicles:
		var vid: String = v[0]
		var holder := Node2D.new()
		holder.name = vid
		holder.position = Vector2(v[1], rail)
		pf.add_child(holder)
		if vid == "loco":
			var body := _spr(A + "karsk/loco.png", true, 0.55)
			body.position = Vector2(0, -float(K.get("loco_size", [284, 112])[1]) + 1)
			body.set_meta("y0", body.position.y)
			holder.add_child(body)
			_n["loco_body"] = body
			var crop: Array = K.get("wheels_crop", [0, 0, 284, 112])
			var wh := _spr(A + "karsk/loco_wheels.png", true, 0.0, int(K.get("wheel_frames", 8)))
			wh.position = body.position + Vector2(float(crop[0]), float(crop[1]))
			holder.add_child(wh)
			_n["loco_wheels"] = wh
		else:
			var spr := _spr(A + "karsk/%s.png" % vid, true, 0.3)
			var tex_h := _tex_h(A + "karsk/%s.png" % vid)
			spr.position = Vector2(0, -tex_h + 1)
			holder.add_child(spr)
		_n["veh_" + vid] = holder
		# small spoked wheels turning over the static ones of the vehicle image (pilot truck, bogies)
		var vi := ["loco", "tender", "gondola", "boxcar"].find(vid)
		var img_h := _tex_h(A + "karsk/%s.png" % vid)
		for w in K.get("small_wheels", {}).get(vid, []):
			var st := str(w[0])
			var ws := _spr(A + "karsk/%s.png" % st, true, 0.0, int(K.get("small_frames", 8)))
			ws.position = Vector2(float(w[1]) - 11.0, -img_h + 1.0 + float(w[2]) - 11.0)
			holder.add_child(ws)
			_n.get_or_add("small_wheels", []).append([ws, vi, float(K.get("small_r", {}).get(st, 9.5)),
				int(K.get("small_spokes", {}).get(st, 8))])
	var c17 := Node2D.new()
	c17.position = Vector2(C17_X, rail)
	pf.add_child(c17)
	var cw := _spr(KE + "props/wagon_c17.png", true, 0.0)
	cw.position = Vector2(0, -_tex_h(KE + "props/wagon_c17.png") + 1)
	c17.add_child(cw)
	_n["c17_spr"] = cw
	var tl := _spr(A + "karsk/tail_lamp.png", false, 0.9)
	tl.position = Vector2(192, -36)
	c17.add_child(tl)
	_n["c17"] = c17
	# platform props (re-used A1 props) and the people
	var lamp := _spr(KE + "props/lamp_post_1.png", true, 0.6)
	var lamp_node := Node2D.new()
	lamp_node.position = Vector2(1480, 304)
	lamp.position = Vector2(0, -_tex_h(KE + "props/lamp_post_1.png"))
	lamp_node.add_child(lamp)
	pf.add_child(lamp_node)
	var bench := _spr(KE + "props/bench.png", true, 0.0)
	_n["bench_spr"] = bench
	var bench_node := Node2D.new()
	bench_node.position = Vector2(1546, 296)
	bench.position = Vector2(0, -_tex_h(KE + "props/bench.png"))
	bench_node.add_child(bench)
	pf.add_child(bench_node)
	var alexei := Act.new()
	alexei.setup("alexei")
	alexei.position = ALEXEI_POS
	pf.add_child(alexei)
	_n["alexei"] = alexei
	var ledger := _spr(A + "karsk/ledger_arm.png", true, 0.0)
	ledger.position = Vector2(1, -33)
	ledger.show_behind_parent = true          # behind Alexei's sprite: only the part under his arm shows
	alexei.add_child(ledger)
	_n["ledger_arm"] = ledger
	var irina := Act.new()
	irina.setup("irina")
	irina.position = IRINA_POS
	pf.add_child(irina)
	_n["irina"] = irina
	# FX: puffs pool, cylinder steam, whistle plume, snow sliding off the roof
	for i in PUFF_POOL:
		var p := _spr(A + "karsk/fx_puff.png", false, 0.0, 12)
		p.z_index = 5
		p.visible = false
		S.add_child(p)
		_puffs.append(p)
	for fxn in ["fx_steam", "fx_whistle", "fx_snowdrop"]:
		var f := _spr(A + "karsk/%s.png" % fxn, false, 0.0, 8)
		f.z_index = 6
		f.visible = false
		S.add_child(f)
		_n[fxn] = f
	for i in JET_POOL:                          # cylinder-cock jets, one per piston stroke, left in the air
		var jf := _spr(A + "karsk/fx_steam.png", false, 0.0, 8)
		jf.z_index = 6
		jf.visible = false
		S.add_child(jf)
		_n.get_or_add("jets", []).append(jf)
	var fg := _spr(A + "karsk/fg.png", false)
	_par(S, fg, K_REF + Vector2(-980, 210), K_REF, Vector2(1.15, 1.0), 30)
	# lights
	_n["k_lights"] = Node2D.new()
	S.add_child(_n["k_lights"])
	_light(_n["k_lights"], Vector2(1500, 236), Color("#F0C487"), 1.25, 70, 30, 0.03)
	_n["l_cab"] = _light(_n["k_lights"], Vector2.ZERO, Color("#DCA16E"), 1.0, 40, 14, 0.12)
	_n["l_head"] = _light(_n["k_lights"], Vector2.ZERO, Color("#FBE3AE"), 0.9, 60, 18, 0.0)
	_n["l_ash"] = _light(_n["k_lights"], Vector2.ZERO, Color("#E0782E"), 0.45, 26, 6, 0.0)   # ash pan glow
	_n["l_tail"] = _light(_n["k_lights"], Vector2.ZERO, Color("#C8503C"), 0.8, 22, 8, 0.0)
	_light(_n["k_lights"], Vector2(1641, 162), Color("#C8503C"), 0.6, 16, 6, 0.0)
	var west := DirectionalLight2D.new()
	west.color = Color("#DCA16E")
	west.energy = 0.22
	west.height = 0.3
	west.rotation_degrees = -90.0
	S.add_child(west)
	_n["k_west"] = west
	var snow := SnowFx.new()
	snow.density = 0.42
	snow.wind = 5.0
	snow.color_far = Color("#A3B1AD")
	snow.color_near = Color("#DEE5DC")
	S.add_child(snow)
	_n["k_snow"] = snow


func _build_close() -> void:
	var S: Node2D = _sets["close"]
	S.position = CLOSE_O
	var C: Dictionary = layout.get("close", {})
	var glyph: Vector2 = LayerStack._v2(C.get("glyph", [320, 176]))
	var ledger := _spr(A + "close/ledger.png", false)
	ledger.z_index = 0
	S.add_child(ledger)
	_n["ledger"] = ledger
	var ini := _spr(A + "close/initials.png", false)
	ini.position = LayerStack._v2(C.get("initials", [46, 152]))
	ini.z_index = 1
	S.add_child(ini)
	_n["initials"] = ini
	var plan := _spr(A + "close/plan.png", false, 0.0, 1, false, false)
	plan.z_index = 2
	plan.material = _dissolve_mat(glyph, 0.75, true)
	S.add_child(plan)
	_n["plan"] = plan
	var imp := _spr(A + "close/imprint.png", false, 0.0, 4, false, false)
	imp.position = LayerStack._v2(C.get("imprint", [229, 125]))
	imp.z_index = 3
	imp.material = _dissolve_mat(glyph - imp.position, 0.0, true)
	S.add_child(imp)
	_n["imprint"] = imp
	var sh := _spr(A + "close/stamp_shadow.png", false, 0.0, 3)
	sh.z_index = 4
	S.add_child(sh)
	_n["stamp_shadow"] = sh
	var st := _spr(A + "close/stamp.png", false, 0.0, 3)
	st.z_index = 5
	S.add_child(st)
	_n["stamp"] = st
	var pen := _spr(A + "close/pencil.png", false, 0.0, 1, false, false)
	pen.position = LayerStack._v2(C.get("pencil", [109, 83]))
	pen.z_index = 6
	pen.material = _dissolve_mat(glyph - pen.position, 0.35, false)
	S.add_child(pen)
	_n["pencil"] = pen


func _build_berlin() -> void:
	var S: Node2D = _sets["berlin"]
	var G: Dictionary = layout.get("berlin", {})
	var y0 := float(G.get("y0", -260))
	var bsky := _spr(A + "berlin/sky.png", false)
	bsky.modulate = Color(1.5, 1.45, 1.32)          # the haze glows: counter the cold CanvasModulate on the sky
	_par(S, bsky, B_REF + Vector2(-1, -1), B_REF, Vector2(0, 0), -100)
	var dome := _spr(A + "berlin/dome.png", false)
	dome.modulate = Color(1.42, 1.42, 1.34)
	_par(S, dome, B_REF + Vector2(40, 64), B_REF, Vector2(0.12, 0.2), -96)
	_n["dome"] = dome
	_n["l_dome"] = _light(dome, Vector2(310, 9), Color("#C8503C"), 0.0, 14, 8, 0.0)
	var far := _spr(A + "berlin/far.png", false, 0.4)
	far.modulate = Color(1.22, 1.22, 1.16)
	_par(S, far, B_REF + Vector2(-80, 100), B_REF, Vector2(0.45, 0.45), -90)
	# smoke from the tenement chimneys (street plane)
	var chim: Array = G.get("chimneys", [])
	var k := 0
	for c in chim:
		var cp: Vector2 = LayerStack._v2(c)
		if cp.x < 480 or k >= 6:
			continue
		var sm := _spr(A + "berlin/smoke.png", false, 0.0, 8)
		sm.modulate = Color(1.35, 1.35, 1.3)           # coal smoke catches the city glow: lighter than the sky
		sm.position = BERLIN_O + cp + Vector2(-14, -60)
		sm.z_index = -45
		sm.set_meta("phase", float(k) * 0.37)
		S.add_child(sm)
		_n.get_or_add("b_smoke", []).append(sm)
		k += 1
	var street := _spr(A + "berlin/street.png", true, 0.3)
	street.position = BERLIN_O + Vector2(0, y0)
	street.z_index = -50
	S.add_child(street)
	# facade sprites: banners, eagle relief, door, window that lights up, queue, pigeons
	var bn: Array = G.get("banner", [24, 96, 22, 0])
	for bx in BANNER_X:
		var b := _spr(A + "berlin/banner.png", false, 0.0, maxi(3, 2 * int(bn[3])))
		b.position = BERLIN_O + Vector2(bx - (float(bn[0]) - 24.0) * 0.5, 104)
		b.z_index = -48
		S.add_child(b)
		_n.get_or_add("banners", []).append(b)
	var rel := _spr(A + "berlin/relief.png", true, 0.0)
	rel.position = BERLIN_O + Vector2(355 - 26, 160)
	rel.z_index = -48
	S.add_child(rel)
	_n["relief"] = rel
	var door_r: Array = G.get("door", [338, 206, 34, 50])
	var door := _spr(A + "berlin/door.png", false, 0.8, 3)
	door.position = BERLIN_O + Vector2(float(door_r[0]), float(door_r[1]))
	door.z_index = -47
	S.add_child(door)
	_n["door"] = door
	var jambs := _spr(A + "berlin/jambs.png", true, 0.0)
	jambs.position = BERLIN_O + Vector2(float(door_r[0]) - 10, float(door_r[1]) - 14)
	jambs.z_index = 8
	jambs.visible = false
	S.add_child(jambs)
	_n["jambs"] = jambs
	var won := _spr(A + "berlin/window_on.png", false, 0.7)
	won.position = BERLIN_O + Vector2(590, 130)
	won.z_index = -48
	S.add_child(won)
	_n["window_on"] = won
	var q := _spr(A + "berlin/queue.png", false, 0.0, 2)
	q.position = BERLIN_O + Vector2(598, 232)
	q.z_index = -46
	S.add_child(q)
	_n["queue"] = q
	var pig := _spr(A + "berlin/pigeons.png", false, 0.0, 2)
	pig.z_index = -46
	S.add_child(pig)
	_n["pigeons"] = pig
	# playfield: people + tram (y-sorted)
	var pf := Node2D.new()
	pf.y_sort_enabled = true
	S.add_child(pf)
	var tram := Node2D.new()
	tram.name = "Tram"
	pf.add_child(tram)
	var tb := _spr(A + "berlin/tram.png", true, 0.85)
	tb.position = Vector2(0, -_tex_h(A + "berlin/tram.png") + 1)
	tram.add_child(tb)
	var pole := _spr(A + "berlin/tram_pole.png", false, 0.9, 3)
	pole.position = tb.position + Vector2(142, -54)
	tram.add_child(pole)
	_n["tram"] = tram
	_n["tram_pole"] = pole
	_n["l_tram_in"] = _light(tram, Vector2(107, -40), Color("#F4BA81"), 0.7, 80, 16, 0.02)
	_n["l_tram_head"] = _light(tram, Vector2(-4, -22), Color("#FCE9C8"), 0.7, 56, 10, 0.0)
	_n["l_spark"] = _light(tram, tb.position + Vector2(205, -52), Color("#CFE3FF"), 0.0, 44, 20, 0.0)
	var people := {"konrad": Vector2(KONRAD_FROM, 272), "guard": Vector2(304, 269), "clerk": Vector2(120, 274),
		"berlin_mother": Vector2(860, 270), "berlin_child": Vector2(876, 271)}
	for id in people:
		var a := Act.new()
		a.setup(id)
		a.position = BERLIN_O + people[id]
		pf.add_child(a)
		_n["p_" + id] = a
	var fg := _spr(A + "berlin/fg.png", false, 0.8)
	_par(S, fg, B_REF + Vector2(-331, 350), B_REF, Vector2(1.15, 1.15), 30)
	# lights: portal lanterns, gas lamps, bakery, door glow, window
	var L := Node2D.new()
	S.add_child(L)
	for lp in [Vector2(320, 202), Vector2(390, 202)]:
		_light(L, BERLIN_O + lp, Color("#F4BA81"), 0.75, 46, 18, 0.04)
	for lp in [Vector2(152, 190), Vector2(642, 190), Vector2(907, 190)]:
		_light(L, BERLIN_O + lp, Color("#F0AE6E"), 0.7, 58, 24, 0.05)
	_light(L, BERLIN_O + Vector2(600, 246), Color("#F4BA81"), 0.7, 52, 10, 0.0)
	_n["l_door"] = _light(L, BERLIN_O + Vector2(355, 252), Color("#F8D2A0"), 0.0, 40, 8, 0.0)
	_n["l_window"] = _light(L, BERLIN_O + Vector2(596, 140), Color("#F4BA81"), 0.0, 22, 8, 0.0)
	var snow := SnowFx.new()
	snow.density = 0.55
	snow.wind = -4.0
	snow.color_far = Color("#8F8A92")
	snow.color_near = Color("#D2CCCB")
	S.add_child(snow)
	_n["b_snow"] = snow


func _build_overlays() -> void:
	# screen-space plan copy for the plan -> Berlin dissolve (inside the world viewport, under the grade)
	var cl := CanvasLayer.new()
	cl.layer = 98
	add_child(cl)
	var C: Dictionary = layout.get("close", {})
	var glyph: Vector2 = LayerStack._v2(C.get("glyph", [320, 176]))
	var plan := _spr(A + "close/plan.png", false, 0.0, 1, false, false)
	plan.position = Vector2(1, 1)
	plan.material = _dissolve_mat(glyph, 0.9, false)
	cl.add_child(plan)
	var pen := _spr(A + "close/pencil.png", false, 0.0, 1, false, false)
	pen.position = Vector2(1, 1) + LayerStack._v2(C.get("pencil", [109, 83]))
	pen.material = _dissolve_mat(glyph - LayerStack._v2(C.get("pencil", [109, 83])), 0.9, false)
	cl.add_child(pen)
	_n["ov_plan"] = plan
	_n["ov_pencil"] = pen
	cl.visible = false
	_n["ov"] = cl
	var fl := CanvasLayer.new()
	fl.layer = 99
	add_child(fl)
	_fade_rect = ColorRect.new()
	_fade_rect.color = Color(0, 0, 0, 1)
	_fade_rect.size = Vector2(642, 362)
	_fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fl.add_child(_fade_rect)


func _apply_variants() -> void:
	# historical insignia switch (§12.4): neutral base file or the _hist variant
	var lb = _n.get("loco_body")
	if lb:
		_set_tex(lb, _pick(A + "karsk/loco.png"), true, 0.55)
	var cs = _n.get("c17_spr")
	if cs:
		_set_tex(cs, _pick(KE + "props/wagon_c17.png"), true, 0.0)      # A1 prop's own _hist variant (env_karsk)
	var bs = _n.get("bench_spr")
	if bs:
		_set_tex(bs, _pick(KE + "props/bench.png"), true, 0.0)
	for lname in ["far_city", "far_industry", "mid", "poles"]:
		var ln = _n.get("k_" + lname)
		if ln:
			_set_tex(ln, _pick(KE + lname + ".png"), false, 0.3 if lname == "far_city" else 0.0)
	var led = _n.get("ledger")
	if led:
		_set_tex(led, _pick(A + "close/ledger.png"), false, 0.0)
	for node in [_n.get("plan"), _n.get("ov_plan")]:
		if node:
			_set_tex(node, _pick(A + "close/plan.png"), false, 0.0)
	for b in _n.get("banners", []):
		_set_tex(b, _pick(A + "berlin/banner.png"), false, 0.0)
	var rel = _n.get("relief")
	if rel:
		_set_tex(rel, _pick(A + "berlin/relief.png"), true, 0.0)
	var share := branch == "share_with_irina"
	if _n.has("irina"):
		_n["irina"].visible = share
	if _n.has("initials"):
		_n["initials"].visible = share
	if _n.has("ledger_arm"):
		_n["ledger_arm"].visible = not share


func _pick(path: String) -> String:
	if not symbols:
		return path
	var h := Symbols.hist_path(path)
	if ResourceLoader.exists(h) or FileAccess.file_exists(h):
		return h
	return path


# ================================================================== per-frame state (pure function of t)
func _apply(time: float) -> void:
	var shot := _shot(time)
	for sname in _sets:
		var on: bool = (sname == "karsk" and shot.begins_with("k")) or (sname == "close" and shot == "close") \
			or (sname == "berlin" and shot == "berlin")
		_sets[sname].visible = on
		_sets[sname].process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	var cam := _cam_at(time)
	if Game.camera:
		Game.camera.cinematic = true
		Game.camera.set_top_left(cam, false)
	for e in _parallax:
		var node: Node2D = e["node"]
		if not node.is_visible_in_tree():
			continue
		var p: Vector2 = e["p"]
		node.position = e["anchor"] + (cam - e["ref"]) * (Vector2.ONE - p)   # hi-res path: 1/k px steps
	match shot:
		"kA", "kB", "kC":
			_apply_karsk(time, shot)
		"close":
			_apply_close(time)
		"berlin":
			_apply_berlin(time)
	_apply_grade(time)
	_apply_fade(time)
	_apply_shake(time)


func _shot(time: float) -> String:
	if time < T_SHOT_LOCO:
		return "kA"
	if time < T_SHOT_PLAT:
		return "kB"
	if time < T_SHOT_STAMP:
		return "kC"
	if time < T_BERLIN:
		return "close"
	return "berlin"


func _cam_at(time: float) -> Vector2:
	if time < T_SHOT_LOCO:
		return CAM_K_A[0].lerp(CAM_K_A[1], _sine(_seg(time, 0.0, T_SHOT_LOCO)))
	if time < T_SHOT_PLAT:
		return CAM_K_B[0].lerp(CAM_K_B[1], _sine(_seg(time, T_SHOT_LOCO + 0.6, T_SHOT_PLAT)))
	if time < T_SHOT_STAMP:
		return CAM_K_C[0].lerp(CAM_K_C[1], _sine(_seg(time, T_SHOT_PLAT, T_SHOT_STAMP)))
	if time < T_BERLIN:
		return CLOSE_O
	if time < T_CRANE1:
		return CAM_B[0].lerp(CAM_B[1], _smoother(_seg(time, T_CRANE0, T_CRANE1)))
	return CAM_B[1].lerp(CAM_B[2], _sine(_seg(time, T_KONRAD_WALK, T_ENTER + 0.3)))


# ------------------------------------------------------------------ Karsk: train dynamics
## The departure is simulated once at build time (SIM_HZ) and sampled afterwards, so every frame stays a pure
## function of t (seek/skip). Model: the regulator opens over 1 s; traction A0 (px/s^2) is limited by constant
## power above V_POWER; rolling resistance; the free slack of each coupling runs out in turn -- every snatch
## shares momentum (the engine visibly jerks) and recoils in the draft gear; the drivers slip once when the
## whole train hangs on the drawbar (adhesion lost, the driver eases the regulator, it bites again).
func _simulate() -> void:
	_sim_d = PackedFloat32Array()
	_sim_v = PackedFloat32Array()
	_snatch = PackedFloat32Array()
	var cums: Array = []
	var cum := 0.0
	for s in SLACK:
		cum += float(s)
		cums.append(cum)
	var d := 0.0
	var v := 0.0
	var nxt := 0
	var n := int((T_SHOT_STAMP + 0.5 - T_DEPART) * SIM_HZ) + 2
	for i in n:
		var tau := float(i) / SIM_HZ
		var a := A0 * _smooth(tau) * (1.0 - 0.9 * _slip_env(tau)) * minf(1.0, V_POWER / maxf(v, 0.001))
		if v > 0.0:
			a -= 0.4 + 0.0004 * v * v
		v = maxf(0.0, v + a / SIM_HZ)
		d += v / SIM_HZ
		while nxt < cums.size() and d >= float(cums[nxt]):
			v *= float(SNATCH_KEEP[nxt])
			_snatch.append(T_DEPART + tau)
			nxt += 1
		_sim_d.append(d)
		_sim_v.append(v)


## Adhesion loss envelope of the wheel slip (tau = seconds after T_DEPART).
static func _slip_env(tau: float) -> float:
	if tau < SLIP[0]:
		return 0.0
	if tau < SLIP[1]:
		return 1.0
	return 1.0 - _smooth((tau - SLIP[1]) / SLIP[2])


## Extra driver rotation while slipping (radians): the wheels race, then grip again.
func _slip_angle(time: float) -> float:
	return TAU * SLIP_REV * _smoother(_seg(time - T_DEPART, SLIP[0], SLIP[1] + 0.25))


func _sample(arr: PackedFloat32Array, time: float) -> float:
	if time <= T_DEPART or arr.is_empty():
		return 0.0
	var f := (time - T_DEPART) * SIM_HZ
	var i := int(floor(f))
	if i >= arr.size() - 1:
		return arr[arr.size() - 1]
	return lerpf(arr[i], arr[i + 1], f - float(i))


## Loco travel west since the departure (px) and speed (px/s).
func _loco_d(time: float) -> float:
	return _sample(_sim_d, time)


func _loco_v(time: float) -> float:
	return _sample(_sim_v, time)


## Backing onto the C-17 wagon (slowing to a gentle buffer contact), then the buffer bump after coupling.
static func _approach(time: float) -> float:
	if time < T_COUPLE:
		var u := 1.0 - time / T_COUPLE
		return -(62.0 - 24.0) * u * u - 24.0 * u
	var dt := time - T_COUPLE
	return 2.4 * (1.0 - exp(-dt * 8.0)) * exp(-dt * 2.0)


## World-x offset of vehicle i (0 loco, 1 tender, 2 gondola, 3 boxcar, 4 C-17) from its rest position:
## the loco's travel minus the slack still free in front of that vehicle, plus the draft-gear recoil after
## its coupling snatched taut (buffers were compressed while backing up, so the gaps open one by one).
func _veh_off(i: int, time: float) -> float:
	var off := _approach(time) if (i < 4 or time >= T_COUPLE) else 0.0
	if time <= T_DEPART:
		return off
	var free := 0.0
	for j in i:
		free += float(SLACK[j])
	var travel := maxf(0.0, _loco_d(time) - free)
	if i > 0 and _snatch.size() >= i:
		var s := time - _snatch[i - 1]
		if s > 0.0:
			travel += 0.9 * exp(-s * 7.0) * sin(s * TAU * 3.2)
	return off - travel


static func _snap(v: float, k: float) -> float:
	return roundf(v * k) / k


func _driver_angle(time: float) -> float:
	var r := float(layout.get("karsk", {}).get("wheel_r", 16))
	return -_veh_off(0, time) / r + _slip_angle(time)


func _compute_beats() -> void:
	# exhaust beats (two cylinders, double acting: 4 per driver revolution, slip included) -> puffs, chuffs,
	# cylinder-cock jets, firebox pulses
	_beats = PackedFloat32Array()
	var a0 := _driver_angle(T_DEPART)
	var n := 0
	var tt := T_DEPART
	while tt < T_SHOT_STAMP and _beats.size() < 400:
		var k := int(floor((_driver_angle(tt) - a0) / (PI * 0.5) + 0.97))
		while n < k:
			_beats.append(tt)
			n += 1
		tt += 1.0 / 240.0


## Rail joints: every axle that crosses a joint (JOINT_X0 + n * JOINT) -> clack + a one-pixel dip of that
## vehicle. Times per vehicle (sorted) and a flat event list [time, joint_x] for the sound cues.
func _compute_joints() -> void:
	var K: Dictionary = layout.get("karsk", {})
	var ax: Dictionary = K.get("axles", {})
	var names := ["loco", "tender", "gondola", "boxcar", "c17"]
	var base := _veh_base()
	_joint_t = []
	_joint_ev = []
	var prev: Array = []
	for i in 5:
		_joint_t.append(PackedFloat32Array())
		prev.append(_veh_off(i, 0.0))
	var tt := 1.0 / 120.0
	while tt < T_SHOT_STAMP:
		for i in 5:
			var o := _veh_off(i, tt)
			if absf(o - float(prev[i])) > 0.0001:
				for a in ax.get(names[i], []):
					var xa := float(base[i]) + float(a) + float(prev[i])
					var xb := float(base[i]) + float(a) + o
					var ja := floorf((xa - JOINT_X0) / JOINT)
					var jb := floorf((xb - JOINT_X0) / JOINT)
					if ja != jb:
						_joint_t[i].append(tt)
						_joint_ev.append([tt, JOINT_X0 + maxf(ja, jb) * JOINT])
			prev[i] = o
		tt += 1.0 / 120.0
	for i in 5:
		_joint_t[i].sort()
	_joint_ev.sort_custom(func(p, q): return p[0] < q[0])


func _veh_base() -> Array:
	var xs: Array = [0.0, 0.0, 0.0, 0.0, C17_X]
	var x := C17_X
	for i in range(TRAIN.size() - 1, -1, -1):
		x -= float(TRAIN[i][1])
		xs[i] = x
	return xs


## One screen pixel down while an axle of vehicle i runs over a joint.
func _bump(i: int, time: float, k: float) -> float:
	if _joint_t.size() <= i:
		return 0.0
	var arr: PackedFloat32Array = _joint_t[i]
	var j := arr.bsearch(time, false)
	return (1.0 / k) if j > 0 and time - arr[j - 1] < 0.06 else 0.0


func _last_beat(time: float) -> float:
	var j := _beats.bsearch(time, false)
	return _beats[j - 1] if j > 0 else -100.0


func _apply_karsk(time: float, shot: String) -> void:
	var K: Dictionary = layout.get("karsk", {})
	var rail := float(K.get("rail_y", 272))
	var k := _px_scale()
	var base := _veh_base()
	var offs: Array = []
	for i in 5:
		offs.append(_snap(_veh_off(i, time), k))          # whole viewport pixels: no relative jitter
	for i in TRAIN.size():
		var h: Node2D = _n["veh_" + str(TRAIN[i][0])]
		h.position = Vector2(float(base[i]) + float(offs[i]), rail + _bump(i, time, k))
	var c17: Node2D = _n["c17"]
	c17.position = Vector2(C17_X + float(offs[4]), rail + _bump(4, time, k))
	var loco_x := float(base[0]) + float(offs[0])
	var loco_top := rail - float(K.get("loco_size", [284, 112])[1]) + 1
	var v := _loco_v(time)
	# drivers + rods + valve gear: one frame per 6 deg of the driver angle taken from the DRAWN travel
	# (+ slip), so the crank phase always matches the distance the engine has moved
	var r := float(K.get("wheel_r", 16))
	var nf := int(K.get("wheel_frames", 60))
	var ang := -float(offs[0]) / r + _slip_angle(time)
	_n["loco_wheels"].set_frame(posmod(int(floor(ang / TAU * nf)), nf))
	var sf := int(K.get("small_frames", 8))
	for sw in _n.get("small_wheels", []):                 # [sprite, vehicle, radius, spokes]
		var a2: float = -float(offs[sw[1]]) / float(sw[2])
		sw[0].set_frame(posmod(int(floor(a2 / (TAU / float(sw[3])) * sf)), sf))
	# the engine heaves a pixel on each exhaust beat while it is working hard at low speed
	var lb_age := time - _last_beat(time)
	var heave := lb_age >= 0.0 and lb_age < 0.07 and v > 0.5 and v < 55.0
	_n["loco_body"].position.y = float(_n["loco_body"].get_meta("y0")) - (1.0 / k if heave else 0.0)
	# lights that ride with the train; the blast draws the fire after every beat
	var pulse := exp(-maxf(0.0, lb_age) * 7.0) if lb_age < 2.0 else 0.0
	var cw: Array = K.get("cab_window", [232, 44, 16, 14])
	_n["l_cab"].position = Vector2(loco_x + float(cw[0]) + 8, loco_top + float(cw[1]) + 6)
	_n["l_cab"].energy = 0.95 + 0.1 * sin(time * 23.0) * sin(time * 7.3) + 0.45 * pulse
	_n["l_ash"].position = Vector2(loco_x + 238.0, rail - 9.0)
	_n["l_ash"].energy = 0.45 + 0.08 * sin(time * 17.0 + 1.3) + 0.35 * pulse
	var hl: Array = K.get("headlamp", [16, 22])
	_n["l_head"].position = Vector2(loco_x + float(hl[0]) - 2, loco_top + float(hl[1]) + 4)
	_n["l_tail"].position = c17.position + Vector2(196, -32)
	# exhaust: one puff per beat, launched from the chimney with the engine's own speed (drag) and the blast,
	# then carried east by the wind and rising -- the plume lies back as the train gathers speed
	var ch: Array = K.get("chimney", [40, 11])
	for p in _puffs:
		p.visible = false
	var slot := 0
	for bi in _beats.size():
		var tb := _beats[bi]
		var age := time - tb
		if age < 0.0:
			break
		if age >= PUFF_LIFE:
			continue
		var p: Node2D = _puffs[slot % _puffs.size()]
		slot += 1
		var ve := _loco_v(tb)
		var p0 := Vector2(float(base[0]) + _veh_off(0, tb) + float(ch[0]) - 28.0, loco_top + float(ch[1]) - 54.0)
		var drift := -ve * 0.3 * (1.0 - exp(-age / 0.3)) + 11.0 * age
		var rise := 55.0 * 0.25 * (1.0 - exp(-age / 0.25)) + 7.0 * age
		p.position = Vector2(_snap(p0.x + drift, k), _snap(p0.y - rise, k))
		p.set_frame(clampi(int(age / PUFF_LIFE * 12.0), 0, 11))
		p.visible = true
	# standing loco: two lazy idle puffs before the whistle
	for j in 2:
		var ti := T_SHOT_LOCO - 0.6 + j * 0.7
		var age2 := time - ti
		if age2 >= 0.0 and age2 < PUFF_LIFE and time < T_DEPART + 0.5:
			var p2: Node2D = _puffs[(_puffs.size() - 1 - j)]
			p2.position = Vector2(loco_x + float(ch[0]) - 28.0, loco_top + float(ch[1]) - 54.0) + Vector2(8.0, -14.0) * age2
			p2.set_frame(clampi(int(age2 / PUFF_LIFE * 12.0) + 2, 0, 11))
			p2.visible = true
	# cylinder cocks: a soft hiss while standing, then a jet on every piston stroke for the first metres,
	# left behind in the air as the engine pulls away
	var cs: Array = K.get("cyl_steam", [26, 98])
	var st: Node2D = _n["fx_steam"]
	st.visible = time >= T_SHOT_LOCO and time < T_DEPART + 0.15
	if st.visible:
		st.position = Vector2(loco_x + float(cs[0]) - 8, loco_top + float(cs[1]) - 18)
		st.set_frame(int((time - T_SHOT_LOCO) * 10.0) % 3)
	var jets: Array = _n.get("jets", [])
	for jn in jets:
		jn.visible = false
	var js := 0
	for bi in _beats.size():
		var tb2 := _beats[bi]
		if tb2 > time or tb2 > T_DEPART + 3.4:
			break
		var age3 := time - tb2
		if age3 >= 0.8 or jets.is_empty():
			continue
		var jn2: Node2D = jets[js % jets.size()]
		js += 1
		var j0 := Vector2(float(base[0]) + _veh_off(0, tb2) + float(cs[0]) - 8, loco_top + float(cs[1]) - 18)
		jn2.position = Vector2(_snap(j0.x + 9.0 * age3, k), _snap(j0.y - 4.0 * age3, k))
		jn2.set_frame(clampi(int(age3 / 0.8 * 8.0), 0, 7))
		jn2.visible = true
	var wst: Node2D = _n["fx_whistle"]
	wst.visible = time >= T_WHISTLE and time < T_WHISTLE + 1.2
	if wst.visible:
		var ws: Array = K.get("whistle", [198, 20])
		wst.position = Vector2(loco_x + float(ws[0]) - 15, loco_top + float(ws[1]) - 44)
		wst.set_frame(clampi(int((time - T_WHISTLE) / 1.2 * 8.0), 0, 7))
	var sd: Node2D = _n["fx_snowdrop"]
	sd.visible = time >= T_COUPLE and time < T_COUPLE + 1.0
	if sd.visible:
		sd.position = Vector2(c17.position.x - 6, rail - 92)
		sd.set_frame(clampi(int((time - T_COUPLE) * 8.0), 0, 7))
	# the A1 smoke ribbons keep drifting
	for sm in _n.get("k_smoke", []):
		var frames: int = sm.get_meta("frames", 1)
		sm.set_frame(int(time * float(sm.get_meta("anim_fps", 5.0))) % maxi(1, frames))
	# people
	var alexei: Act = _n["alexei"]
	var irina: Act = _n["irina"]
	alexei.face(true)
	irina.face(true)
	var share := branch == "share_with_irina"
	if share and time >= T_TURN:
		irina.face(false)                        # she turns to Alexei: now two people know
		irina.anim("idle_side", time)
	elif share and time > 0.9 and time < T_COUPLE + 0.2:
		irina.anim("talk_side", time)            # she calls the shunting signal
	else:
		irina.anim("idle_side", time + 0.4)
	if not share and time >= T_TURN + 0.2:
		alexei.anim("inspect_side", time - T_TURN - 0.2, false)   # alone: he looks down at the ledger
	else:
		alexei.anim("idle_side", time)
	_modulate.color = Color(0.70, 0.74, 0.79)


# ------------------------------------------------------------------ close-ups
func _apply_close(time: float) -> void:
	var C: Dictionary = layout.get("close", {})
	var glyph: Vector2 = LayerStack._v2(C.get("glyph", [320, 176]))
	var anchor: Vector2 = LayerStack._v2(C.get("stamp_anchor", [130, 250]))
	var r := time - T_SHOT_STAMP
	var st: Node2D = _n["stamp"]
	var sh: Node2D = _n["stamp_shadow"]
	var off := Vector2.ZERO
	var frame := 0
	var vis := true
	var tp := T_PRESS - T_SHOT_STAMP
	var tl := T_LIFT - T_SHOT_STAMP
	if r < 0.55:
		off = Vector2(150, -170).lerp(Vector2(12, -14), _out_cubic(r / 0.55))
	elif r < tp - 0.1:
		off = Vector2(12, -14).lerp(Vector2(14, -22), _sine(_seg(r, 0.55, tp - 0.1)))
		frame = 1 if r > 0.75 else 0
	elif r < tp:
		off = Vector2(14, -22).lerp(Vector2.ZERO, _seg(r, tp - 0.1, tp))
		frame = 2 if r > tp - 0.05 else 1
	elif r < tl:
		off = Vector2.ZERO
		frame = 2
	elif r < tl + 0.7:
		var u := _seg(r, tl, tl + 0.7)
		off = Vector2.ZERO.lerp(Vector2(190, -260), u * u)
		frame = 1 if u < 0.3 else 0
	else:
		vis = false
	st.visible = vis
	sh.visible = vis
	st.position = glyph - anchor + off
	sh.position = glyph - anchor + off * Vector2(0.85, 0.85)
	st.set_frame(frame)
	sh.set_frame(frame)
	# imprint: wet -> spreading -> soaked -> dry
	var imp: Node2D = _n["imprint"]
	imp.visible = r >= tl - 0.02
	var ir := r - tl
	imp.set_frame(0 if ir < 0.25 else (1 if ir < 0.6 else (2 if ir < 1.0 else 3)))
	# match dissolve: page first (edges -> centre), then the glyph (red out, pencil in)
	var d0 := T_DISSOLVE
	_mat(_n["plan"], "progress", _seg(time, d0, d0 + 1.7))
	_mat(imp, "progress", 1.0 - _seg(time, d0 + 1.25, d0 + 2.6))
	_mat(_n["pencil"], "progress", _seg(time, d0 + 1.35, d0 + 2.75))
	_modulate.color = Color(1, 1, 1)


# ------------------------------------------------------------------ Berlin
func _tram_x(time: float) -> float:
	if time < T_TRAM_IN:
		return 1200.0
	if time < T_TRAM_STOP:
		var u := _seg(time, T_TRAM_IN, T_TRAM_STOP)
		return TRAM_STOP_X + 470.0 * pow(1.0 - u, 2.0)
	if time < T_TRAM_GO:
		return TRAM_STOP_X
	return TRAM_STOP_X - 0.5 * 64.0 * pow(time - T_TRAM_GO, 2.0)


func _apply_berlin(time: float) -> void:
	var G: Dictionary = layout.get("berlin", {})
	var rail_far: Array = G.get("rail_far", [288, 292])
	# overlay: the plan dissolves away (centre first) and reveals the dome in the haze
	var ov: CanvasLayer = _n["ov"]
	var dv := 1.0 - _seg(time, T_BERLIN, T_BERLIN + 1.3)
	ov.visible = dv > 0.0
	_mat(_n["ov_plan"], "progress", dv)
	_mat(_n["ov_pencil"], "progress", dv)
	# tram
	var tram: Node2D = _n["tram"]
	var tx := _tram_x(time)
	tram.position = BERLIN_O + Vector2(tx, float(rail_far[1]))
	var moving := (time > T_TRAM_IN and time < T_TRAM_STOP) or time > T_TRAM_GO
	if moving and int(time * 6.0) % 2 == 0:
		tram.position.y -= 1.0 / _px_scale()          # one screen pixel of bounce over the rail joints
	var spark := 0
	for ts in [27.6 + EXT, 28.7 + EXT, 32.1 + EXT, 32.9 + EXT]:
		if time >= ts and time < ts + 0.1:
			spark = 1 if time < ts + 0.05 else 2
	_n["tram_pole"].set_frame(spark)
	_n["l_spark"].energy = 1.3 if spark > 0 else 0.0
	# Konrad: hidden behind the tram, waits a beat, walks to the portal, turns, steps in
	var kon: Act = _n["p_konrad"]
	var kx := KONRAD_FROM
	var ky := 272.0
	kon.visible = time < T_DOOR_CLOSE + 0.05
	if time < T_KONRAD_WALK:
		kon.face(true)
		kon.anim("idle_side", time)
	elif time < T_ENTER - 0.15:
		var u := _seg(time, T_KONRAD_WALK, T_ENTER - 0.15)
		var dist := (KONRAD_FROM - KONRAD_TO) * u
		kx = KONRAD_FROM - dist
		kon.face(true)
		kon.walk("walk_side", dist)
		var stepi := int(floor(dist / maxf(1.0, kon.ground_speed("walk_side")) * 10.0 / 4.0))
		if playing and stepi != _last_step:
			_last_step = stepi
			Audio.sfx("step_snow", -11.0, 0.08)
	else:
		kx = KONRAD_TO
		var u2 := _seg(time, T_ENTER - 0.15, T_DOOR_CLOSE)
		ky = 272.0 - 15.0 * u2
		kon.face(false)
		if u2 < 1.0:
			kon.walk("walk_back", 15.0 * u2)
		else:
			kon.anim("idle_back", time)
		kon.modulate = Color(1, 1, 1).lerp(Color(0.55, 0.5, 0.48), u2)
	if time < T_ENTER - 0.15:
		kon.modulate = Color(1, 1, 1)
	kon.position = BERLIN_O + Vector2(kx, ky)
	_n["jambs"].visible = time >= T_ENTER
	# door: opens before Konrad arrives (the porter inside), closes behind him
	var door: Node2D = _n["door"]
	var df := 0
	if time >= T_DOOR_OPEN and time < T_DOOR_CLOSE:
		df = 1 if time < T_DOOR_OPEN + 0.2 else 2
	elif time >= T_DOOR_CLOSE and time < T_DOOR_CLOSE + 0.35:
		df = 2 if time < T_DOOR_CLOSE + 0.15 else 1
	door.set_frame(df)
	door.z_index = 9 if time >= T_DOOR_CLOSE + 0.05 else -47
	_n["l_door"].energy = [0.0, 0.5, 0.9][df]
	# other people
	var guard: Act = _n["p_guard"]
	guard.face(false)
	guard.anim("idle_side", time)
	var clerk: Act = _n["p_clerk"]
	var cu := maxf(0.0, time - 33.4 - EXT)
	clerk.face(false)
	clerk.position = BERLIN_O + Vector2(120.0 + 23.0 * cu, 274)
	clerk.walk("walk_side", 23.0 * cu)
	for id in ["berlin_mother", "berlin_child"]:
		var a: Act = _n["p_" + id]
		var mu := maxf(0.0, time - 32.8 - EXT)
		var x0 := 860.0 if id == "berlin_mother" else 876.0
		a.face(true)
		a.position = BERLIN_O + Vector2(x0 - 17.0 * mu, 270 if id == "berlin_mother" else 271)
		a.walk("walk_side", 17.0 * mu)
	# life on the facade
	var bph := int(G.get("banner", [0, 0, 0, 0])[3])
	for i in _n.get("banners", []).size():
		_n["banners"][i].set_frame(_banner_frame(time, i, bph))
	_n["queue"].set_frame(int(time / 0.9) % 2)
	var won: Node2D = _n["window_on"]
	won.visible = time >= 27.3 + EXT
	_n["l_window"].energy = 0.45 if won.visible else 0.0
	for sm in _n.get("b_smoke", []):
		sm.set_frame(int(time * 5.0 + float(sm.get_meta("phase", 0.0)) * 8.0) % 8)
	var pig: Node2D = _n["pigeons"]
	var pg0 := Vector2(430, 180)
	if time < T_PIGEONS:
		pig.position = BERLIN_O + pg0
		pig.set_frame(int(time / 0.5) % 2)
		pig.visible = true
	else:
		var fu := time - T_PIGEONS
		pig.position = BERLIN_O + pg0 + Vector2(-55.0, -70.0) * fu + Vector2(0, -12.0) * fu * fu
		pig.set_frame(int(fu * 14.0) % 2)
		pig.visible = fu < 1.4
	_n["l_dome"].energy = 0.7 if fmod(time, 2.0) < 0.5 else 0.0
	_modulate.color = Color(0.56, 0.58, 0.74)


## Banner wind: a travelling cloth wave whose speed follows a gust envelope (closed-form phase integral, so
## the frame is a pure function of t); strong gusts switch to the large-amplitude set. Each banner has its own
## phase and feels the gust a moment later.
func _banner_frame(time: float, i: int, phases: int) -> int:
	if phases <= 0:
		return [0, 1, 2, 1][int(time * 1.6 + i * 1.3) % 4]
	var tt := time - 0.35 * float(i)
	var g := 0.5 + 0.4 * sin(TAU * tt / 7.3 + 1.1) + 0.25 * sin(TAU * tt / 3.1 + 0.4)
	var cyc := (0.9 + 0.8 * 0.5) * tt - 0.8 * 0.4 * 7.3 / TAU * cos(TAU * tt / 7.3 + 1.1) \
		- 0.8 * 0.25 * 3.1 / TAU * cos(TAU * tt / 3.1 + 0.4)      # integral of 0.9 + 0.8 * g (cycles)
	var ph := posmod(int(floor(cyc * float(phases) + 5.3 * float(i))), phases)
	return ph + (phases if g > 0.62 else 0)


# ------------------------------------------------------------------ grade, fades, shake
func _apply_grade(time: float) -> void:
	if Game.grade == null or not (Game.grade.material is ShaderMaterial):
		return
	if time < T_SHOT_STAMP:
		_grade_blend("karsk", "karsk", 0.0)
	elif time < T_DISSOLVE:
		_grade_blend("sepia", "sepia", 0.0)
	elif time < T_BERLIN:
		_grade_blend("sepia", "archive", _seg(time, T_DISSOLVE, T_DISSOLVE + 2.8))
	else:
		_grade_blend("archive", "berlin", _seg(time, T_BERLIN, T_BERLIN + 1.3))


func _grade_blend(a_name: String, b_name: String, k: float) -> void:
	var key := "%s>%s@%.3f" % [a_name, b_name, k]
	if key == _grade_state:
		return
	_grade_state = key
	var grades: Dictionary = Game.grades if Game.grades is Dictionary else {}
	var ga: Dictionary = grades.get(a_name, grades.get("default", {}))
	var gb: Dictionary = grades.get(b_name, grades.get("default", {}))
	var mat := Game.grade.material as ShaderMaterial
	for p in ["lift", "gamma", "gain", "tint"]:
		var dv: Array = [0, 0, 0] if p == "lift" else [1, 1, 1]
		var va: Array = ga.get(p, dv)
		var vb: Array = gb.get(p, dv)
		mat.set_shader_parameter(p, Vector3(va[0], va[1], va[2]).lerp(Vector3(vb[0], vb[1], vb[2]), k))
	for p in ["saturation", "vignette", "grain"]:
		var dflt := 1.0 if p == "saturation" else (0.22 if p == "vignette" else 0.0)
		var v := lerpf(float(ga.get(p, dflt)), float(gb.get(p, dflt)), k)
		if p == "grain":
			v *= float(Settings.get_value("pixel_post"))
		mat.set_shader_parameter(p, v)
	# palette: fade the snap out, swap palettes at zero strength, fade it back in
	var pal_a := str(ga.get("palette", a_name))
	var pal_b := str(gb.get("palette", b_name))
	var sa := float(ga.get("palette_strength", 0.0))
	var sb := float(gb.get("palette_strength", 0.0))
	var use_b := k >= 0.5 or pal_a == pal_b
	var strength := 0.0
	if pal_a == pal_b:
		strength = lerpf(sa, sb, k)
	else:
		strength = sa * clampf(1.0 - k * 2.0, 0.0, 1.0) if k < 0.5 else sb * clampf(k * 2.0 - 1.0, 0.0, 1.0)
	var cols := _palette_cols(pal_b if use_b else pal_a)
	mat.set_shader_parameter("palette_size", cols.size())
	if cols.size() > 0:
		while cols.size() < 128:
			cols.append(cols[0])
		mat.set_shader_parameter("palette", cols)
	mat.set_shader_parameter("palette_strength", strength * float(Settings.get_value("pixel_post")) if cols.size() > 1 else 0.0)


func _palette_cols(name: String) -> Array:
	var cols: Array = []
	var P = Game.palettes.get(name, {}) if Game.palettes is Dictionary else {}
	if P is Dictionary:
		for ramp in P.values():
			for hexc in ramp:
				var c := Color(str(hexc))
				cols.append(Vector3(c.r, c.g, c.b))
	return cols.slice(0, 128)


func _apply_fade(time: float) -> void:
	var a := 0.0
	if time < 1.2:
		a = 1.0 - _sine(time / 1.2)
	elif time >= T_FADE:
		a = _sine(_seg(time, T_FADE, DURATION - 0.05))
	_fade_rect.color.a = a


func _apply_shake(time: float) -> void:
	if Game.view == null or not Game.view.has_method("set_shake"):
		return
	var on := time >= T_PRESS and time < T_PRESS + 0.09 and not bool(Settings.get_value("reduced_motion"))
	Game.view.set_shake(Vector2(0, 3) if on else Vector2.ZERO)


# ================================================================== sound + text cues
func _cues(prev: float, now: float) -> void:
	var share := branch == "share_with_irina"
	_cue("wind", 0.4, prev, now, func(): _play("wind_gust", -12.0))
	_cue("couple", T_COUPLE - 0.04, prev, now, func(): _play("cine_a1m1_couple", -1.0))
	_cue("hiss", T_SHOT_LOCO + 0.05, prev, now, func(): _play("cine_a1m1_hiss", -3.0))
	_cue("whistle", T_WHISTLE, prev, now, func(): _play("cine_a1m1_whistle", 0.0))
	_cue("depart", T_DEPART, prev, now, func(): _play("cine_a1m1_depart", -2.0))
	for i in _beats.size():
		var tb := _beats[i]
		if tb > prev and tb <= now:
			var near := tb < T_SHOT_PLAT
			_play("cine_a1m1_chuff", (-3.0 if near else -10.0) - minf(8.0, float(i) * 0.08), 0.06)
	for i in _snatch.size():                    # the slack runs out down the train: clank, clank, clank
		if _snatch[i] > prev and _snatch[i] <= now:
			_play("cine_a1m1_clank", -2.0 - 3.5 * float(i), 0.04)
	if now < T_SHOT_STAMP:
		var cc := _cam_at(now).x + 320.0
		for ev in _joint_ev:
			var te: float = ev[0]
			if te > now:
				break
			if te > prev:
				var db := -6.0 - absf(float(ev[1]) - cc) * 0.03
				if db > -24.0:
					_play("cine_a1m1_clack", db, 0.08)
	_cue("line_a", T_LINE_A, prev, now, func():
		Game.subtitle(Loc.t("cin.a1m1.alexei.share" if share else "cin.a1m1.alexei.keep"), 4.9))
	_cue("amb_out", T_SHOT_STAMP, prev, now, func(): Audio.stop_ambience(1.4))
	_cue("swell", T_SHOT_STAMP + 0.1, prev, now, func(): _play("cine_a1m1_swell", -4.0))
	_cue("stamp", T_PRESS - 0.12, prev, now, func(): _play("cine_a1m1_stamp", 0.0))
	_cue("thud", T_PRESS, prev, now, func(): _play("stamp_thud", -6.0))
	_cue("far_whistle", T_LIFT + 0.6, prev, now, func(): _play("cine_a1m1_whistle_far", 0.0))
	_cue("bell_far", T_DISSOLVE + 1.8, prev, now, func(): _play("tram_bell", -9.0))
	_cue("berlin_amb", T_BERLIN, prev, now, func():
		Audio.play_ambience("amb_berlin_street", 2.5)
		Audio.play_music("mus_berlin", 5.0))
	_cue("tram_in", T_TRAM_IN + 0.4, prev, now, func(): _play("cine_a1m1_tram_arrive", -1.0))
	_cue("bell_near", T_TRAM_STOP - 0.3, prev, now, func(): _play("tram_bell", -3.0))
	_cue("tram_go", T_TRAM_GO - 0.1, prev, now, func(): _play("cine_a1m1_tram_depart", -1.0))
	_cue("line_k", T_LINE_K, prev, now, func(): Game.subtitle(Loc.t("cin.a1m1.konrad"), 4.9))
	_cue("door", T_DOOR_CLOSE - 0.9, prev, now, func(): _play("cine_a1m1_door", -2.0))
	_cue("pigeons", T_PIGEONS, prev, now, func(): _play("cine_a1m1_pigeons", -3.0))


func _cue(id: String, at: float, prev: float, now: float, f: Callable) -> void:
	if _cue_done.has(id):
		return
	if at > prev and at <= now or (prev == 0.0 and at <= now and at <= 0.0):
		_cue_done[id] = true
		f.call()


const SOUNDS := ["cine_a1m1_couple", "cine_a1m1_hiss", "cine_a1m1_whistle", "cine_a1m1_depart", "cine_a1m1_chuff",
	"cine_a1m1_clank", "cine_a1m1_clack",
	"cine_a1m1_swell", "cine_a1m1_stamp", "cine_a1m1_whistle_far", "cine_a1m1_tram_arrive", "cine_a1m1_tram_depart",
	"cine_a1m1_door", "cine_a1m1_pigeons", "stamp_thud", "tram_bell", "wind_gust"]


func _build_audio() -> void:
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX" if AudioServer.get_bus_index("SFX") >= 0 else "Master"
		add_child(p)
		_players.append(p)
	for id in SOUNDS:                          # warm the cache: no disk load in the middle of the shot
		var path := SFX_DIR + str(id) + ".wav"
		if ResourceLoader.exists(path):
			_streams[path] = load(path)
	# music / ambience / footsteps that Audio loads later: holding a reference keeps them in the resource cache
	for path in ["res://assets/audio/music/mus_berlin.wav", "res://assets/audio/amb/amb_berlin_street.wav",
			SFX_DIR + "step_snow_1.wav", SFX_DIR + "step_snow_2.wav", SFX_DIR + "step_snow_3.wav",
			SFX_DIR + "step_snow_4.wav"]:
		if ResourceLoader.exists(path):
			_streams[path] = load(path)


func _play(id: String, db: float = 0.0, pitch_var: float = 0.0) -> void:
	var path := SFX_DIR + id + ".wav"
	var s: AudioStream = _streams.get(path)
	if s == null:
		if not ResourceLoader.exists(path):
			return
		s = load(path) as AudioStream
		_streams[path] = s
	var pl: AudioStreamPlayer = null
	for p in _players:
		if not p.playing:
			pl = p
			break
	if pl == null:
		pl = _players[0]
	pl.stream = s
	pl.volume_db = db
	pl.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
	pl.play()


func _stop_sounds() -> void:
	for p in _players:
		if is_instance_valid(p):
			p.stop()


func _hide_subtitle() -> void:
	var sub = Game.ui.get("subtitles") if Game.ui else null
	if sub and sub.has_method("hide_subtitle"):
		sub.hide_subtitle()


# ================================================================== helpers
## Viewport pixels per world pixel of the active render path (hi-res 2D path: 3 @1080p).
func _px_scale() -> float:
	if Game.view and Game.view.get("world_scale") != null and Game.view.has_method("is_hires") and Game.view.is_hires():
		return maxf(1.0, float(Game.view.world_scale))
	return 1.0


static func _seg(x: float, a: float, b: float) -> float:
	return clampf((x - a) / maxf(0.0001, b - a), 0.0, 1.0)


static func _sine(u: float) -> float:
	return 0.5 - 0.5 * cos(PI * clampf(u, 0.0, 1.0))


static func _smooth(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


static func _smoother(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


static func _out_cubic(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return 1.0 - pow(1.0 - u, 3.0)


func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _tex_h(path: String) -> float:
	var tx := Spr.load_tex(path)
	return float(tx.get_height()) if tx else 0.0


func _mat(node: Node2D, param: String, v: float) -> void:
	var m := node.material as ShaderMaterial
	if m:
		m.set_shader_parameter(param, v)


func _dissolve_mat(center: Vector2, radial: float, edges_first: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = DISSOLVE_SHADER
	m.set_shader_parameter("center", center)
	m.set_shader_parameter("radial", radial)
	m.set_shader_parameter("edges_first", edges_first)
	m.set_shader_parameter("progress", 0.0)
	return m


## A sprite holder: base Sprite2D (+ optional additive unshaded emission sprite), hframes strip support.
func _spr(path: String, lit: bool, emission: float = 0.0, hframes: int = 1, emissive_layer: bool = false,
		texel := true) -> Spr:
	var s := Spr.new()
	s.setup(path, lit, emission if emission > 0.0 else (0.3 if emissive_layer else 0.0), hframes)
	if texel and s.base.texture:
		s.texel(Vector2.ZERO)
	return s


func _set_tex(node, path: String, lit: bool, emission: float) -> void:
	if node is Spr:
		(node as Spr).retexture(path, lit, emission)


func _par(parent: Node, node: Node2D, anchor: Vector2, ref: Vector2, p: Vector2, z: int) -> void:
	node.z_index = z
	parent.add_child(node)
	node.position = anchor
	_parallax.append({"node": node, "anchor": anchor, "ref": ref, "p": p})


static var _light_tex: Texture2D


func _light(parent: Node, pos: Vector2, col: Color, energy: float, radius: float, height: float, flicker: float) -> PointLight2D:
	if _light_tex == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.45, Color(1, 1, 1, 0.42))
		var gt := GradientTexture2D.new()
		gt.gradient = g
		gt.width = 256
		gt.height = 256
		gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.5)
		gt.fill_to = Vector2(1.0, 0.5)
		_light_tex = gt
	var l := PointLight2D.new()
	var k := _px_scale()
	l.texture = _light_tex
	l.color = col
	l.energy = energy
	l.texture_scale = radius * k / 128.0       # light textures/heights are in viewport px (hi-res path: k per texel)
	l.height = height * k
	l.position = pos
	if flicker > 0.0:
		l.set_meta("flicker", flicker)
	parent.add_child(l)
	return l


# ================================================================== inner classes
class Spr extends Node2D:
	var base: Sprite2D
	var em: Sprite2D
	var frames := 1

	func setup(path: String, lit: bool, emission: float, hframes: int) -> void:
		frames = maxi(1, hframes)
		set_meta("frames", frames)
		base = Sprite2D.new()
		base.centered = false
		base.use_parent_material = true          # a ShaderMaterial on the holder (dissolve) drives the sprite
		add_child(base)
		retexture(path, lit, emission)

	static func load_tex(path: String) -> Texture2D:
		if ResourceLoader.exists(path):
			return load(path) as Texture2D
		if FileAccess.file_exists(path):          # not imported yet (dev run)
			var img := Image.load_from_file(ProjectSettings.globalize_path(path))
			if img:
				return ImageTexture.create_from_image(img)
		return null

	static func canvas_tex(path: String, with_normal: bool) -> Texture2D:
		var d := load_tex(path)
		if d == null or not with_normal:
			return d
		var n := load_tex(path.get_basename() + "_n.png")
		if n == null:
			return d
		var ct := CanvasTexture.new()
		ct.diffuse_texture = d
		ct.normal_texture = n
		ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		return ct

	## Per-texel lighting + texel-anchored dither code of the hi-res world path (render-camera contract).
	func texel(anchor: Vector2) -> void:
		base.use_parent_material = false
		var cell := Vector2(base.texture.get_width() / frames, base.texture.get_height()) if base.texture and frames > 1 else Vector2.ZERO
		TexelLightLib.apply(base, anchor, cell)

	func retexture(path: String, lit: bool, emission: float) -> void:
		var tx := canvas_tex(path, lit)
		base.texture = tx
		base.hframes = frames
		if not lit:
			base.light_mask = 0
		if em:
			em.queue_free()
			em = null
		if emission > 0.0:
			var et := load_tex(path.get_basename() + "_e.png")
			if et:
				em = Sprite2D.new()
				em.centered = false
				em.texture = et
				em.hframes = frames
				var mat := CanvasItemMaterial.new()
				mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
				mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
				em.material = mat
				em.modulate = Color(1, 1, 1, emission)
				add_child(em)

	func set_frame(f: int) -> void:
		var k := clampi(f, 0, frames - 1)
		if base:
			base.frame = k
		if em:
			em.frame = k


class Act extends Node2D:
	## A character from assets/characters/<id>/ (sheet.json + sheet.png + sheet_n.png), frames set from
	## the timeline (deterministic); missing art -> invisible (never blocks the cinematic).
	const FALLBACK := {"walk_back": "walk_side", "idle_back": "idle_side", "inspect_side": "idle_side",
		"talk_side": "idle_side", "walk_side": "idle_side", "idle_front": "idle_side"}
	var sheet: Dictionary = {}
	var spr: Sprite2D
	var hf := 1
	var cell := Vector2(32, 56)
	var origin := Vector2(16, 54)
	var left := false

	func setup(id: String) -> bool:
		spr = Sprite2D.new()
		spr.centered = false
		add_child(spr)
		var dir := "res://assets/characters/%s/" % id
		if not FileAccess.file_exists(dir + "sheet.json"):
			spr.visible = false
			return false
		var d = JSON.parse_string(FileAccess.get_file_as_string(dir + "sheet.json"))
		var tx := Spr.canvas_tex(dir + "sheet.png", true)
		if typeof(d) != TYPE_DICTIONARY or tx == null:
			spr.visible = false
			return false
		sheet = d
		cell = LayerStack._v2(d.get("cell", [32, 56]))
		origin = LayerStack._v2(d.get("origin", [cell.x * 0.5, cell.y - 2]))
		spr.texture = tx
		hf = maxi(1, int(tx.get_width() / cell.x))
		spr.hframes = hf
		spr.vframes = maxi(1, int(tx.get_height() / cell.y))
		_offset()
		anim("idle_side", 0.0)
		TexelLightLib.apply(spr, Vector2.ZERO, cell)
		return true

	func face(l: bool) -> void:
		if l == left:
			return
		left = l
		spr.flip_h = l
		_offset()

	func _offset() -> void:
		spr.offset = -Vector2((cell.x - origin.x) if left else origin.x, origin.y)

	func _resolve(a: String) -> Dictionary:
		var anims: Dictionary = sheet.get("anims", {})
		var guard := 0
		while not anims.has(a) and FALLBACK.has(a) and guard < 5:
			a = FALLBACK[a]
			guard += 1
		return anims.get(a, {})

	func anim(a: String, time: float, loop := true) -> void:
		var A2: Dictionary = _resolve(a)
		if A2.is_empty():
			return
		var n := maxi(1, int(A2.get("frames", 1)))
		var f := int(floor(maxf(0.0, time) * float(A2.get("fps", 6))))
		f = f % n if loop else mini(f, n - 1)
		spr.frame = clampi(int(A2.get("row", 0)) * hf + f, 0, hf * spr.vframes - 1)

	func ground_speed(a: String) -> float:
		var gs = sheet.get("ground_speed", {})
		if gs is Dictionary and gs.has(a):
			return float(gs[a])
		return 30.0

	## Walk cycle driven by the distance covered, so the planted foot never slides.
	func walk(a: String, dist: float) -> void:
		var A2: Dictionary = _resolve(a)
		if A2.is_empty():
			return
		var fps := float(A2.get("fps", 10))
		anim(a, dist / maxf(1.0, ground_speed(a)) * fps / fps)
