extends Node3D
## Street life of the Great Hall reveal (owner: hall / great_hall_3d).
## Adds sprite specs (walkers, the queue at the stop, the patrol, the sweeper, pigeons and crows, chimney smoke,
## manhole steam) to the builder's people_spec BEFORE hall_people.gd builds the sprites, and animates what is not
## a sprite: the departing tram, cars and a lorry (with moving head lights), plus the lamp halos that the post
## process draws.  Everything is a pure function of the shot time t, so seek()/skip() are deterministic.
##
## Depth bands (texel lock => one sprite size per distance band, people move mostly sideways):
##   46 px character sheets  d ~ 30-36 m (street at the family's corner)
##   walk_36 / stand_36      d ~ 40-46 m (plaza edge, tram stop)
##   walk_24                 d ~ 60-70 m (plaza ring, behind the tram)
##   walk_14 / march_14      d ~ 100-130 m
##   walk_8                  d ~ 180-450 m

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const B := preload("res://scripts/levels/hall/hall_builder.gd")
const LIFE := "res://assets/architecture/great_hall/life/"
const CHAR := "res://assets/characters/"
## Round 3 timeline (24 s, see hall_camera_rig.gd): h1 crane 0-5.5 s, h2 hold 5.5-14.5 s, h3 push 14.5-21.5 s + hold.
## The near band (plaza edge, d ~ 40-46 m) is kept quiet so the evicted family stays the focus; the life is spread
## over the middle and the back of the square (ring, mid plaza, far plaza) and timed to fill the long hold.
const H1_SCALE := 5.5 / 3.0      ## the crane is the round-2 crane, 1.83x slower: h1-only timings scale with it
const T_TRAM := 6.4              ## tram bell + departure (cue hall.cue.tram_bell)
const T_PIGEONS := 8.75          ## loudspeaker_1 (8.6 s) startles the pigeons (cue hall.cue.pigeons)
const T_PATROL := 3.0            ## the patrol starts off-frame right and enters the frame at ~10.9 s (cue)

var builder
var rig
var post_mat: ShaderMaterial
var vp_h := 360.0
var _halos: Array = []
var _vehicles: Array = []          ## {node, path: _Path, s0, speed, t0, t1, accel, vmax, lights: Array}
var _tram: Dictionary = {}
var _rng := RandomNumberGenerator.new()


## Polyline with arclength sampling.
class _Path:
	var pts: PackedVector3Array = PackedVector3Array()
	var lens: PackedFloat32Array = PackedFloat32Array()
	var total := 0.0

	func _init(p: Array) -> void:
		var acc := 0.0
		for i in p.size():
			pts.append(p[i])
			if i > 0:
				acc += (p[i] as Vector3).distance_to(p[i - 1])
			lens.append(acc)
		total = acc

	## Returns [position, unit direction]
	func sample(s: float) -> Array:
		s = clampf(s, 0.0, total)
		var i := 1
		while i < lens.size() - 1 and lens[i] < s:
			i += 1
		var l0 := lens[i - 1]
		var l1 := lens[i]
		var k := 0.0 if l1 - l0 < 1e-5 else (s - l0) / (l1 - l0)
		var a := pts[i - 1]
		var b := pts[i]
		var d := (b - a).normalized() if a.distance_to(b) > 1e-5 else Vector3.FORWARD
		return [a.lerp(b, k), d]


# ============================================================================== setup
func setup(p_builder, p_rig) -> void:
	builder = p_builder
	rig = p_rig
	_rng.seed = 1964
	_add_walkers()
	_add_queue_arrival()
	_add_patrol()
	_add_sweeper()
	_add_birds()
	_add_smoke_and_steam()
	_add_belongings()
	_add_paper()
	_halos = builder.halos.duplicate()
	_add_static_halos()
	_setup_tram()
	_setup_vehicles()


func _spec(sheet: String, row: int, extra: Dictionary) -> Dictionary:
	return builder.life_spec(sheet, row, extra)


func _add(spec: Dictionary) -> void:
	builder.people_spec.append(spec)


# ------------------------------------------------------------------------------ walkers
func _add_walkers() -> void:
	# a clerk with his parcel comes round the family's corner and crosses the street past them -- without a look
	if ResourceLoader.exists(CHAR + "clerk/sheet.png"):
		var p0 := Vector3(-11.0, 0.16, -48.5)
		_add({"role": "clerk", "pos": p0, "anim": "walk_side", "speed": 1.1, "t0": 3.5, "s0": 2.1,
			"path": [p0, Vector3(-8.6, 0.0, -53.0), Vector3(-7.6, 0.0, -53.6), Vector3(9.0, 0.0, -53.6)],
			"stride_ref_depth": 34.0, "phase": 0.0})
	# an old woman with her bag, h1 only, on the far sidewalk of the cross street
	if ResourceLoader.exists(CHAR + "babushka/sheet.png"):
		var b0 := Vector3(-30.0, 0.16, -49.6)
		_add({"role": "babushka", "pos": b0, "anim": "walk_side", "speed": 0.9, "t0": 0.0,
			"path": [b0, Vector3(-18.5, 0.16, -49.6)], "stride_ref_depth": 52.0, "show": Vector2(0.0, 3.0 * H1_SCALE)})
	# plaza edge (walk_36): only the woman who walks to the stop and joins the queue (_add_queue_arrival); the two
	# other near walkers of round 2 were moved back onto the square (user: the front of the plaza was overloaded)
	# behind the tram on the plaza ring (walk_24): looping paths whose ends lie outside the visible wedge
	# (x < -14 is hidden by the family's block, x > 16 is outside the frame) -> no walker stops or pops in view.
	# [row, z, direction, speed, x at t = 0]
	var ring := [[1, -84.0, 1.0, 1.3, -20.0], [4, -86.5, -1.0, 1.4, 12.0], [2, -88.0, 1.0, 1.2, 0.0],
		[0, -82.5, -1.0, 1.5, 26.0], [3, -90.5, 1.0, 1.1, -34.0]]
	for e in ring:
		var z1: float = e[1]
		var dir1: float = e[2]
		var sp1: float = e[3]
		var xs := -44.0 if dir1 > 0.0 else 30.0
		var xe := 30.0 if dir1 > 0.0 else -44.0
		var a2 := Vector3(xs, 0.0, z1)
		_add(_spec("walk_24", int(e[0]), {"role": "ring_%d" % int(e[0]), "pos": a2, "path": [a2, Vector3(xe, 0.0, z1)],
			"speed": sp1, "t0": -absf(float(e[4]) - xs) / sp1, "stride_ref_depth": 66.0,
			"phase": 0.2 * float(e[0]), "loop_path": true}))
	# mid plaza (walk_14): people crossing the square in both directions, spread along a 106 m loop
	for i in 10:
		var z := -116.0 - float(i) * 2.6
		var right := i % 2 == 0
		var xa := -60.0 if right else 46.0
		var xb := 46.0 if right else -60.0
		var sp := 1.15 + 0.1 * float(i % 3)
		_add(_spec("walk_14", i % 4, {"role": "mid_%d" % i, "pos": Vector3(xa, 0, z),
			"path": [Vector3(xa, 0, z), Vector3(xb, 0, z)], "speed": sp,
			"t0": -fposmod(float(i) * 37.3 + 20.0, 106.0) / sp, "stride_ref_depth": 105.0, "loop_path": true}))
	# the far plaza (walk_8): small groups streaming towards the portico and along the ring
	for i in 28:
		var z2 := -190.0 - float(i) * 8.4
		var dir := 1.0 if (i * 7) % 3 != 0 else -1.0
		var x0 := -70.0
		var x1 := 210.0
		var pa := Vector3(x0 if dir > 0.0 else x1, 0.0, z2)
		var pb := Vector3(x1 if dir > 0.0 else x0, 0.0, z2 - 6.0)
		_add(_spec("walk_8", i % 4, {"role": "far_%d" % i, "pos": pa, "path": [pa, pb],
			"speed": 1.2 + 0.05 * float(i % 4), "t0": -float((i * 53) % 197) - 20.0, "stride_ref_depth": 220.0,
			"loop_path": true}))


## The woman walking along the plaza edge reaches the end of the (shorter) queue and waits there (~13.2 s).
func _add_queue_arrival() -> void:
	var a := Vector3(10.5, 0.0, -61.8)
	var b := Vector3(-1.5, 0.0, -61.8)
	var c := Vector3(-5.15, 0.14, -63.25)
	var t0 := 0.5
	var t_arr := t0 + (a.distance_to(b) + b.distance_to(c)) / 1.25
	_add(_spec("walk_36", 3, {"role": "edge_3", "pos": a, "path": [a, b, c], "speed": 1.25, "t0": t0,
		"stride_ref_depth": 43.0, "phase": 0.39, "show": Vector2(0.0, t_arr)}))
	_add(_spec("stand_36", 3, {"role": "queue_new", "pos": c, "flip": false, "face_motion": false,
		"phase": 0.9, "show": Vector2(t_arr, 99.0)}))


# ------------------------------------------------------------------------------ patrol, sweeper
func _add_patrol() -> void:
	# a patrol of four, marching in step across the square (right to left), no insignia: starts outside the frame
	# and crosses the mid plaza through the hold and the push (still marching in the final frame)
	for k in 4:
		var x0 := 44.0 + k * 1.7
		var a := Vector3(x0, 0.0, -127.0)
		var b := Vector3(x0 - 92.0, 0.0, -127.0)
		_add(_spec("march_14", 0, {"role": "patrol_%d" % k, "pos": a, "path": [a, b], "speed": 1.55,
			"t0": T_PATROL, "stride_ref_depth": 108.0, "phase": 0.0}))


func _add_sweeper() -> void:
	var p := Vector3(-3.4, 0.0, -50.2)
	_add(_spec("sweeper", 0, {"role": "sweeper", "pos": p, "flip": true, "face_motion": false, "fps": 5.0}))
	_add(_spec("handcart", 0, {"role": "handcart", "pos": Vector3(-1.5, 0.0, -50.6), "flip": false,
		"face_motion": false}))


# ------------------------------------------------------------------------------ birds
func _add_birds() -> void:
	# pigeons on the snow at the plaza edge; the loudspeaker (3.6 s) startles them: up and away to the hall
	var take_off := T_PIGEONS
	for i in 7:
		var gp := Vector3(-1.4 + i * 0.55 + _rng.randf_range(-0.2, 0.2), 0.0, -58.6 - _rng.randf_range(0.0, 2.4))
		var t_go := take_off + i * 0.06
		_add(_spec("birds", 0, {"role": "pigeon_%d" % i, "pos": gp, "fps": 2.5 + 0.4 * float(i % 3),
			"phase": float(i) * 0.37, "flip": i % 2 == 0, "face_motion": false, "show": Vector2(0.0, t_go),
			"self_light": 0.2}))
		var up := gp + Vector3(_rng.randf_range(-3.0, 3.0), 6.0 + i * 0.4, -14.0)
		var away := gp + Vector3(_rng.randf_range(-12.0, 16.0), 28.0 + i * 2.0, -120.0)
		_add(_spec("birds", 1, {"role": "pigeon_fly_%d" % i, "pos": gp, "path": [gp, up, away],
			"speed": 11.0, "t0": t_go, "fps": 9.0, "phase": float(i) * 0.11, "face_motion": true,
			"show": Vector2(t_go, t_go + 9.0), "dissolve": Vector4(t_go, t_go, t_go + 5.0, t_go + 7.0),
			"unshaded": 0.5, "no_lock": true}))
	# crows sitting on the cable from the loudspeaker mast to the family's block
	var c0 := Vector3(6.2, 8.6, -68.5)
	var c1 := Vector3(-11.95, 9.6, -58.0)
	for u: float in [0.31, 0.36, 0.64]:
		var pc := c0.lerp(c1, u) + Vector3(0, -1.2 * 4.0 * u * (1.0 - u), 0)
		_add(_spec("birds", 2, {"role": "crow", "pos": pc + Vector3(0, 0.02, 0), "fps": 1.2,
			"phase": u * 9.0, "flip": u > 0.5, "face_motion": false}))
	# a flock wheeling over the plaza in front of the dome (ominous, slow)
	for i in 9:
		var ph := float(i) / 9.0 * TAU
		var rad := 60.0 + float(i % 3) * 14.0
		var ctr := Vector3(B.HX - 10.0, 120.0 + float(i % 4) * 6.0, -640.0)
		var om := 0.16 + 0.01 * float(i % 2)
		var fn := func(t: float) -> Vector3:
			var a := ph + t * om
			return ctr + Vector3(cos(a) * rad, sin(a * 2.0) * 6.0, sin(a) * rad * 0.5)
		_add(_spec("birds", 1, {"role": "flock_%d" % i, "pos": fn.call(0.0), "pos_fn": fn, "fps": 6.0,
			"phase": float(i) * 0.21, "unshaded": 0.6, "always_lock": true}))


# ------------------------------------------------------------------------------ smoke & steam
func _add_smoke_and_steam() -> void:
	var i := 0
	for sp in builder.smoke_spots:
		var pos: Vector3 = sp["pos"]
		var far := bool(sp.get("far", false))
		_add(_spec("smoke", 0, {"role": "smoke_%d" % i, "pos": pos, "fps": 6.0 if far else 7.0,
			"phase": float(i) * 0.53, "face_motion": false, "unshaded": 0.7, "always_lock": far,
			"show": Vector2(0.0, 99.0) if far else Vector2(0.0, 3.2 * H1_SCALE)}))
		i += 1
	var j := 0
	for mp in builder.steam_spots:
		_add(_spec("steam", 0, {"role": "steam_%d" % j, "pos": mp, "fps": 7.0, "phase": float(j) * 0.37,
			"face_motion": false, "unshaded": 0.15}))
		j += 1


# ------------------------------------------------------------------------------ the family's things, paper
func _add_belongings() -> void:
	# carried out of the sealed flat and set down left of the door, under the notice board
	var along: Vector3 = (B.CHAMFER_B - B.CHAMFER_A).normalized()
	var nrm := along.cross(Vector3.UP).normalized()
	var dx: float = (B.CHAMFER_B - B.CHAMFER_A).length() * 0.5 - 0.5
	var at := func(x: float, z: float) -> Vector3: return B.CHAMFER_A + along * x + nrm * z + Vector3(0, 0.16, 0)
	_add(_spec("belong_bedding", 0, {"role": "belong_bedding", "pos": at.call(dx - 2.3, 1.25), "face_motion": false}))
	_add(_spec("belong_chair", 0, {"role": "belong_chair", "pos": at.call(dx - 1.55, 0.75), "face_motion": false}))
	_add(_spec("belong_crate", 0, {"role": "belong_crate", "pos": at.call(dx - 0.95, 1.3), "face_motion": false}))
	# the canary in its cage, next to the child
	_add(_spec("belong_cage", 0, {"role": "belong_cage", "pos": at.call(dx + 3.55, 2.95), "face_motion": false,
		"fps": 0.7, "phase": 0.4}))


func _add_paper() -> void:
	# a newspaper page blown out of the side street, tumbling across the road in the wind
	var t0 := 9.0
	var fn := func(t: float) -> Vector3:
		var u := maxf(0.0, t - t0)
		var x := -18.0 + 3.1 * u + 0.4 * sin(u * 1.7)
		var hop := absf(sin(u * 2.6)) * 0.35 * (0.6 + 0.4 * sin(u * 0.9))
		return Vector3(x, 0.02 + hop, -44.2 + 0.6 * sin(u * 0.7))
	_add(_spec("paper", 0, {"role": "paper", "pos": fn.call(0.0), "pos_fn": fn, "fps": 9.0, "face_motion": false,
		"show": Vector2(t0, 99.0), "unshaded": 0.35}))


# ------------------------------------------------------------------------------ halos
func _add_static_halos() -> void:
	var door: Vector3 = builder.stats.get("door_world", Vector3(-14.7, 1.3, -53.0))
	var along: Vector3 = (B.CHAMFER_B - B.CHAMFER_A).normalized()
	var nrm := along.cross(Vector3.UP).normalized()
	# the warm lamp over the sealed door: the one warm focal light
	_halos.append({"pos": door + along * 0.9 + nrm * 0.95 + Vector3(0, 1.9, 0), "col": Color("#F0AE6E"),
		"r": 1.5, "k": 0.24})


# ------------------------------------------------------------------------------ tram + vehicles
func _setup_tram() -> void:
	if builder.tram_node == null:
		return
	var pts: Array = []
	var z := B.PLAZA_EDGE + 2.0
	while z > -260.0:
		pts.append(Vector3(B.track_x(3.4, z), 0.0, z))
		z -= 1.0
	var path := _Path.new(pts)
	# arclength of the starting centre (z = PLAZA_EDGE - 19)
	var s0 := 0.0
	var zc: float = B.PLAZA_EDGE - 19.0
	for i in pts.size():
		if (pts[i] as Vector3).z <= zc:
			s0 = path.lens[i]
			break
	var head := SpotLight3D.new()
	head.light_color = Color("#F8D2A0")
	head.light_energy = 2.5
	head.spot_range = 22.0
	head.spot_angle = 24.0
	head.light_specular = 0.0
	head.light_cull_mask = B.LAYER_OUT
	builder.tram_node.add_child(head)
	head.position = Vector3(builder.tram_len * 0.5 + 0.1, 0.9, 0.0)
	head.rotation = Vector3(0.0, -PI * 0.5, 0.0)
	head.rotate_object_local(Vector3.RIGHT, -0.12)
	_tram = {"node": builder.tram_node, "path": path, "s0": s0, "t_dep": T_TRAM, "accel": 0.5, "vmax": 6.0}
	_halos.append({"node": builder.tram_node, "local": Vector3(0.0, 2.1, 0.0), "col": Color("#F4BA81"),
		"r": 4.0, "k": 0.13})
	_halos.append({"node": builder.tram_node, "local": Vector3(builder.tram_len * 0.5 + 0.2, 0.9, 0.0),
		"col": Color("#FCE9C8"), "r": 1.2, "k": 0.3})


func _vehicle(kind: String, body: Color, path_pts: Array, speed: float, t0: float, t1: float = 99.0) -> void:
	var node := Node3D.new()
	node.name = "Vehicle_" + kind
	var kb := Kit.new()
	var kg := Kit.new()
	var kl := Kit.new()
	var kt := Kit.new()
	if kind == "truck":
		builder.truck_into(kb, kg, kl, body, Color("#3E5D55"))
	else:
		builder.car_into(kb, kg, kl, kt, body, 4.5)
	for pair in [[kb, "metal"], [kg, "glass"], [kl, "glass_lit"], [kt, "lamp"]]:
		var kit: Kit = pair[0]
		if kit.count == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = kit.commit()
		mi.material_override = builder.mats[pair[1]]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.add_child(mi)
	var head := SpotLight3D.new()
	head.light_color = Color("#F8D2A0")
	head.light_energy = 3.0
	head.spot_range = 18.0
	head.spot_angle = 26.0
	head.light_specular = 0.0
	head.light_cull_mask = B.LAYER_OUT
	node.add_child(head)
	head.position = Vector3(2.4 if kind != "truck" else 3.7, 0.7, 0.0)
	head.rotation = Vector3(0.0, -PI * 0.5, 0.0)
	head.rotate_object_local(Vector3.RIGHT, -0.16)
	add_child(node)
	var path := _Path.new(path_pts)
	_vehicles.append({"node": node, "path": path, "speed": speed, "t0": t0, "t1": t1})
	var front := 2.3 if kind != "truck" else 3.62
	for sd: float in [-1.0, 1.0]:
		_halos.append({"node": node, "local": Vector3(front, 0.72, sd * 0.6), "col": Color("#FCE9C8"),
			"r": 0.9, "k": 0.3})
	_halos.append({"node": node, "local": Vector3(-2.3, 0.72, 0.0), "col": Color("#AF6C47"), "r": 0.7, "k": 0.22})


func _setup_vehicles() -> void:
	# A: a grey saloon drives down the street (seen in the crane shot) and turns onto the plaza ring
	var pa: Array = [Vector3(5.6, 0.0, 10.0), Vector3(5.6, 0.0, -56.0)]
	var z := -58.0
	while z > -120.0:
		pa.append(Vector3(B.track_x(5.6, z) + 1.2, 0.0, z))
		z -= 4.0
	# (passes under the crane at 2.6 s like round 2 at 1.4 s; enters the hold's frame at the plaza edge at ~8.9 s and
	# leaves it on the curve to the right at ~14.5 s)
	_vehicle("car_a", Color("#5F6973"), pa, 8.5, 1.17)
	# B: a dark saloon crosses the plaza ring behind the waiting people, left to right (in view ~12.3-15.1 s)
	_vehicle("car_b", Color("#2A2130"), [Vector3(-34.0, 0.0, -73.5), Vector3(48.0, 0.0, -73.5)], 9.0, 10.0)
	# C: a covered lorry far out on the square, right to left (in view ~10.6-19.6 s)
	_vehicle("truck", Color("#454E58"), [Vector3(66.0, 0.0, -142.0), Vector3(-50.0, 0.0, -142.0)], 6.2, 6.0)
	# D: a second tram far away on the ring (lit windows sliding past)
	var far := Node3D.new()
	far.name = "FarTram"
	var kb := Kit.new()
	var kl := Kit.new()
	kb.box(Vector3(-6.0, 0.45, -1.1), Vector3(12.0, 2.75, 2.2), {"front": Color("#735145"), "side": Color("#5F4530"),
		"top": Color("#ECE6E0")}, Kit.FACES_ALL)
	var x := -5.2
	while x < 4.8:
		kl.face(Vector3(x + 0.55, 2.15, 1.105), Vector3.BACK, Vector3.UP, 0.5, 0.55, Color("#F4BA81"), 1.0)
		x += 1.45
	for pair in [[kb, "metal"], [kl, "glass_lit"]]:
		var mi := MeshInstance3D.new()
		mi.mesh = (pair[0] as Kit).commit()
		mi.material_override = builder.mats[pair[1]]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		far.add_child(mi)
	add_child(far)
	_vehicles.append({"node": far, "path": _Path.new([Vector3(-90.0, 0.0, -300.0), Vector3(120.0, 0.0, -300.0)]),
		"speed": 5.5, "t0": -7.0, "t1": 99.0})


# ============================================================================== per frame
func update(t: float) -> void:
	# tram: waits, rings (cue at T_TRAM), departs along the curve
	if not _tram.is_empty():
		var tau := maxf(0.0, t - float(_tram["t_dep"]))
		var a: float = _tram["accel"]
		var vmax: float = _tram["vmax"]
		var t_acc := vmax / a
		var ds := 0.5 * a * tau * tau if tau < t_acc else 0.5 * a * t_acc * t_acc + vmax * (tau - t_acc)
		var smp: Array = (_tram["path"] as _Path).sample(float(_tram["s0"]) + ds)
		_place(_tram["node"], smp[0], smp[1])
	for v in _vehicles:
		var node: Node3D = v["node"]
		var path: _Path = v["path"]
		var s := (t - float(v["t0"])) * float(v["speed"])
		var on := s >= 0.0 and s <= path.total and t <= float(v["t1"])
		node.visible = on
		if on:
			var smp2: Array = path.sample(s)
			_place(node, smp2[0], smp2[1])
	_update_halos(t)


func _place(node: Node3D, pos: Vector3, dir: Vector3) -> void:
	dir.y = 0.0
	if dir.length() < 1e-4:
		return
	dir = dir.normalized()
	node.global_transform = Transform3D(Basis(dir, Vector3.UP, dir.cross(Vector3.UP)), pos)


func _update_halos(t: float) -> void:
	if post_mat == null:
		return
	var fpx: float = rig.focal_px(rig.cur_vp.y)
	var va := PackedVector4Array()
	var vb := PackedVector4Array()
	for h in _halos:
		if t > float(h.get("until", 999.0)) or t < float(h.get("from", -1.0)):
			continue
		var wp: Vector3
		if h.has("node"):
			var n: Node3D = h["node"]
			if not n.visible or not n.is_inside_tree():
				continue
			wp = n.global_transform * (h["local"] as Vector3)
		else:
			wp = h["pos"]
		var pr: Vector3 = rig.project(wp)
		if pr.z <= 0.5:
			continue
		var r_px := clampf(float(h["r"]) * fpx / pr.z, 2.5, 64.0)
		if pr.x < -r_px or pr.y < -r_px or pr.x > rig.cur_vp.x + r_px or pr.y > rig.cur_vp.y + r_px:
			continue
		var k := float(h["k"])
		if h.has("blink"):
			# slow warning-light blink: on 60 % of the period, hard on/off (no strobe)
			var per := float(h["blink"])
			k *= 1.0 if fposmod(t, per) < per * 0.6 else 0.0
			if k <= 0.0:
				continue
		var col: Color = h["col"]
		va.append(Vector4(pr.x, pr.y, pr.z, r_px))
		vb.append(Vector4(col.r, col.g, col.b, k))
		if va.size() >= 32:
			break
	post_mat.set_shader_parameter("halo_count", va.size())
	if va.size() > 0:
		post_mat.set_shader_parameter("halo_a", va)
		post_mat.set_shader_parameter("halo_b", vb)
