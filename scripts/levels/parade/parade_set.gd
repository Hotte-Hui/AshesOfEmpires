extends Node3D
## The parade on the plaza before the Great Hall (owner: parade), built at runtime on top of the hall set
## (hall_builder.gd, reused read-only).  Deterministic.  Units: metres, +Y up, the camera looks along -Z.
## Layout (z): crowd -805..-854 (backs to the camera) | barrier -856, guards -858 facing the crowd | parade lane
## -869..-883 (infantry blocks march +x, then tanks and half-tracks) | standing formations -897..-930 | tribune
## -918..-932 under the portico eagle | the hall at -1000.  Searchlight pillars ("Lichtdom") along the plaza sides
## and behind the hall.  Massed figures are MultiMesh billboards (parade_figures.gdshader, figures.png atlas).
## Insignia only through the hall builder's Symbols-resolved materials (banner_portico, flag_street).

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const FIG_SHADER := preload("res://assets/architecture/parade/parade_figures.gdshader")
const DIR := "res://assets/architecture/parade/"
const HX := 45.0
const X_MIN := -125.0
const X_MAX := 215.0
const Z_BARRIER := -856.0
const Z_GUARDS := -858.0
const Z_CROWD_FRONT := -854.0
const Z_CROWD_BACK := -805.0
const Z_LANE := -876.0
const Z_TRIBUNE := -918.0
const MARCH_SPEED := 1.4
const MARCH_X0 := 170.0          ## head of block 0 at t = 0
const BLOCK_PITCH := 30.0
const BLOCKS := 6
const VEH_SPEED := 2.8
const VEH_X0 := -77.0            ## centre of vehicle 0 at t = 0 (passes the p3 camera at x = -37 around 14 s)
const VEH_PITCH := 16.0
const FAMILY_X := 62.0           ## the evicted family stands at the barrier here (shot p5)
const P5_EYE := Vector3(64.75, 1.55, -823.0)   ## mid pose of shot p5 (parade_shots.gd)
const STEP_FPS := 3.8            ## 4-frame cycle = 2 steps at 114 steps/min

const NIGHT := ["#120C14", "#1B1520", "#211623", "#2A2130"]
const VIOLET := ["#25202B", "#342F37", "#443B43", "#57494D"]
const STONE := ["#4A3A35", "#5F4A40", "#7A5E4E", "#94735C", "#AE8A6C", "#C9A585"]
const STEEL := ["#1E2329", "#2F363F", "#454E58", "#5F6973", "#7C8690", "#A3ACB4"]
const SNOW := ["#6E6A73", "#8F8A92", "#B2ACB0", "#D2CCCB", "#ECE6E0"]

var meta: Dictionary = {}
var slots: Dictionary = {}
var fig_mat: ShaderMaterial
var puff_mat: ShaderMaterial
var mats: Dictionary = {}
var march_blocks: Array = []
var vehicles: Array = []
var jets: Node3D
var puff_mm: MultiMesh
var halos: Array = []            ## static post halos {pos, col, r, k}
var stats: Dictionary = {}
var rng := RandomNumberGenerator.new()
var _quad: QuadMesh
var _kits: Dictionary = {}


static func c(h: String) -> Color:
	return Color(h)


func build(builder) -> void:
	rng.seed = 1965
	mats = builder.mats
	_quad = QuadMesh.new()
	_quad.size = Vector2(1, 1)
	var txt := FileAccess.get_file_as_string(DIR + "figures.json")
	meta = JSON.parse_string(txt) if txt != "" else {}
	slots = meta.get("slots", {})
	fig_mat = _fig_material(1.8, 0.18)
	fig_mat.set_shader_parameter("fps", STEP_FPS)
	puff_mat = _fig_material(1.3, 0.04)
	_build_tribune()
	_build_barrier()
	_build_beams()
	_flush()
	_build_crowd()
	_build_guards()
	_build_formations()
	_build_officials()
	_build_march()
	_build_vehicles()
	_build_puffs()
	_build_jets()
	_build_lights()


# ------------------------------------------------------------------------------------------ per frame
func update(t: float, min_depth: float) -> void:
	fig_mat.set_shader_parameter("time", t)
	fig_mat.set_shader_parameter("min_depth", min_depth)
	puff_mat.set_shader_parameter("min_depth", min_depth)
	for k in march_blocks.size():
		(march_blocks[k] as Node3D).position.x = MARCH_X0 - k * BLOCK_PITCH + MARCH_SPEED * t
	for j in vehicles.size():
		var v: Node3D = vehicles[j]
		v.position.x = vehicle_x(j, t)
		v.position.y = 0.025 * sin(t * 9.0 + j * 1.7)          # engine judder
	_update_puffs(t)
	if jets:
		jets.visible = t > 30.6 and t < 35.5
		jets.position = Vector3(HX - 330.0 + 230.0 * (t - 31.2), 228.0, -905.0)


func vehicle_x(j: int, t: float) -> float:
	return VEH_X0 - j * VEH_PITCH + VEH_SPEED * t


# ------------------------------------------------------------------------------------------ figures
func _fig_material(height_m: float, self_light: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = FIG_SHADER
	var tex: Texture2D = load(DIR + "figures.png")
	m.set_shader_parameter("atlas", tex)
	var asz: Array = meta.get("atlas", [1, 1])
	m.set_shader_parameter("atlas_size", Vector2(float(asz[0]), float(asz[1])))
	var lods := PackedVector4Array()
	for l in meta.get("lods", []):
		lods.append(Vector4(float(l[0]), float(l[1]), float(l[2]), float(l[3])))
	m.set_shader_parameter("lods", lods)
	m.set_shader_parameter("lod_count", lods.size())
	m.set_shader_parameter("height_m", height_m)
	m.set_shader_parameter("self_light", self_light)
	return m


func _slot(name: String) -> Array:
	return slots.get(name, [0, 1])


## points: Array of [Vector3 feet (local), slot, frames, phase, flip]
func _mm(parent: Node3D, points: Array, mat: ShaderMaterial, node_name: String) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _quad
	mm.instance_count = points.size()
	var buf := PackedFloat32Array()
	buf.resize(points.size() * 16)
	var lo := Vector3(1e9, 1e9, 1e9)
	var hi := Vector3(-1e9, -1e9, -1e9)
	var i := 0
	for p in points:
		var v: Vector3 = p[0]
		lo = lo.min(v)
		hi = hi.max(v)
		var o := i * 16
		buf[o] = 1.0
		buf[o + 3] = v.x
		buf[o + 5] = 1.0
		buf[o + 7] = v.y
		buf[o + 10] = 1.0
		buf[o + 11] = v.z
		buf[o + 12] = float(p[1])
		buf[o + 13] = float(p[2])
		buf[o + 14] = float(p[3])
		buf[o + 15] = float(p[4])
		i += 1
	mm.buffer = buf
	var mi := MultiMeshInstance3D.new()
	mi.name = node_name
	mi.multimesh = mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if points.size() > 0:
		mi.custom_aabb = AABB(lo - Vector3(4, 1, 4), hi - lo + Vector3(8, 6, 8))
	parent.add_child(mi)
	stats[node_name] = points.size()
	return mi


func _build_crowd() -> void:
	var pts: Array = []
	var cs := _slot("crowd")
	var ch := _slot("child_flag")
	var z := Z_CROWD_FRONT
	var row := 0
	while z < Z_CROWD_BACK:
		var dx := lerpf(0.72, 1.15, clampf(float(row) / 40.0, 0.0, 1.0))
		var x := X_MIN + rng.randf() * dx
		while x < X_MAX:
			var px := x + rng.randf_range(-0.22, 0.22)
			var pz := z + rng.randf_range(-0.25, 0.25)
			x += dx
			# the narrow line of sight through which shot p5 looks at the family (camera ~ P5_EYE)
			if pz > Z_CROWD_FRONT + 1.0 and pz < P5_EYE.z:
				var d := P5_EYE.z - pz
				var span := P5_EYE.z - (Z_CROWD_FRONT + 0.4)
				var xc := lerpf(P5_EYE.x, FAMILY_X, d / span)
				if absf(px - xc) < 0.55 + 1.9 * d / span:
					continue
			if absf(px - FAMILY_X) < 2.6 and pz <= Z_CROWD_FRONT + 1.4:
				continue
			# Konrad's spot at the back edge (shot p7)
			if rng.randf() < 0.025:
				pts.append([Vector3(px, 0.0, pz), ch[0], 1, 0, rng.randf() < 0.5])
			else:
				pts.append([Vector3(px, 0.0, pz), cs[0] + rng.randi_range(0, int(cs[1]) - 1), 1, 0,
					rng.randf() < 0.5])
		z += lerpf(0.85, 1.7, clampf(float(row) / 30.0, 0.0, 1.0))
		row += 1
	_mm(self, pts, fig_mat, "Crowd")


func _build_guards() -> void:
	var pts: Array = []
	var g := _slot("guard")
	var x := X_MIN + 4.0
	while x < X_MAX:
		pts.append([Vector3(x, 0.0, Z_GUARDS), g[0], 1, 0, false])
		x += 8.0
	_mm(self, pts, fig_mat, "Guards")


func _build_formations() -> void:
	var pts: Array = []
	var s := _slot("stand")
	for side: float in [-1.0, 1.0]:
		for b in 3:
			for r in 2:
				var x0: float = HX + side * (40.0 + b * 23.5) - (17.5 if side < 0 else 0.0)
				var z0 := -912.0 - r * 18.0
				for i in 14:
					for j in 10:
						pts.append([Vector3(x0 + i * 1.25 + 0.6, 0.0, z0 - j * 1.5), s[0], 1, 0, false])
	# a single rank lines the far side of the lane, facing the crowd
	var x := X_MIN + 2.0
	while x < X_MAX:
		if absf(x - HX) > 34.0:
			pts.append([Vector3(x, 0.0, -888.5), s[0], 1, 0, false])
		x += 2.2
	_mm(self, pts, fig_mat, "Formations")


func _build_officials() -> void:
	var pts: Array = []
	var o := _slot("official")
	for k in 11:
		pts.append([Vector3(HX - 10.0 + k * 2.0, 6.0, Z_TRIBUNE - 3.0), o[0] + (k % 2), 1, 0, false])
	for k in 7:
		pts.append([Vector3(HX - 8.0 + k * 2.6 + 1.0, 6.0, Z_TRIBUNE - 6.5), o[0] + ((k + 1) % 2), 1, 0, false])
	_mm(self, pts, fig_mat, "Officials")


func _build_march() -> void:
	var m := _slot("march")
	var bn: Material = mats.get("flag_street")
	for k in BLOCKS:
		var blk := Node3D.new()
		blk.name = "MarchBlock%d" % k
		add_child(blk)
		var pts: Array = []
		for rank in 10:
			for file in 12:
				var lx := -2.0 - rank * 1.6
				var lz := Z_LANE - 7.2 + file * 1.3
				# whole block in step, files a hair apart so the cycle never looks mechanical in the far shots
				pts.append([Vector3(lx, 0.0, lz), m[0], m[1], 0.0, false])
		_mm(blk, pts, fig_mat, "March%d" % k)
		# colour bearer ahead of the block: pole + banner (Symbols-resolved flag_street material)
		var kit := Kit.new()
		kit.box(Vector3(0.6, 0.0, Z_LANE - 0.05), Vector3(0.1, 4.6, 0.1), c(NIGHT[3]))
		kit.box(Vector3(0.0, 4.45, Z_LANE - 0.05), Vector3(1.6, 0.08, 0.08), c(NIGHT[3]))
		var pole := MeshInstance3D.new()
		pole.mesh = kit.commit()
		pole.material_override = mats.get("metal")
		blk.add_child(pole)
		if bn:
			var fk := Kit.new()
			fk.quad(Vector3(0.05, 2.0, Z_LANE + 0.05), Vector3(0.05, 4.4, Z_LANE + 0.05),
				Vector3(1.55, 4.4, Z_LANE + 0.05), Vector3(1.55, 2.0, Z_LANE + 0.05), Color.WHITE, 0.3)
			var fl := MeshInstance3D.new()
			fl.mesh = fk.commit()
			fl.material_override = bn
			blk.add_child(fl)
		march_blocks.append(blk)


func _build_puffs() -> void:
	var p := _slot("puff")
	var pts: Array = []
	for i in 7 * 8:
		pts.append([Vector3(0, -50, 0), p[0], 1, 0, false])
	var mi := _mm(self, pts, puff_mat, "Puffs")
	mi.custom_aabb = AABB(Vector3(-400, -60, -1000), Vector3(800, 120, 400))
	puff_mm = mi.multimesh


func _update_puffs(t: float) -> void:
	if puff_mm == null:
		return
	var p := _slot("puff")
	var per := 2.0
	var i := 0
	for j in vehicles.size():
		for q in 8:
			var o := float(q) * per / 8.0 + j * 0.37
			var age := fposmod(t - o, per)
			var tb := t - age
			var side := -1.0 if q % 2 == 0 else 1.0
			var x := vehicle_x(j, tb) - 3.2 - age * 0.6
			var pos := Vector3(x, 0.05 + age * 0.35, Z_LANE + side * 1.5 + age * 0.4)
			var fr := 0 if age < 0.45 else (1 if age < 1.1 else 2)
			if tb < 0.0:
				pos.y = -50.0
			puff_mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, pos))
			puff_mm.set_instance_custom_data(i, Color(float(p[0]) + fr, 1.0, 0.0, float(q % 3 == 0)))
			i += 1


# ------------------------------------------------------------------------------------------ geometry
func K(name: String) -> Kit:
	if not _kits.has(name):
		_kits[name] = Kit.new()
	return _kits[name]


func _flush() -> void:
	var geo := Node3D.new()
	geo.name = "ParadeGeometry"
	add_child(geo)
	for name in _kits:
		var kit: Kit = _kits[name]
		if kit.count == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "P_" + name
		mi.mesh = kit.commit()
		mi.material_override = mats.get(name, mats.get("stone"))
		if name in ["lamp"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geo.add_child(mi)


func _build_tribune() -> void:
	var s := K("stone")
	var x0 := HX - 30.0
	s.box(Vector3(x0, 0.0, Z_TRIBUNE - 12.0), Vector3(60.0, 6.0, 12.0), {"front": c(VIOLET[3]), "side": c(VIOLET[2]),
		"top": c(SNOW[3])})
	s.box(Vector3(x0, 6.0, Z_TRIBUNE - 0.7), Vector3(60.0, 1.1, 0.7), {"front": c(STONE[4]), "side": c(STONE[3]),
		"top": c(SNOW[4])})
	for i in 3:
		s.box(Vector3(HX - 8.0, i * 2.0, Z_TRIBUNE + 3.0 - i * 1.2 - 1.2), Vector3(16.0, 2.0, 1.2 + 0.01),
			{"front": c(STONE[4]), "side": c(STONE[3]), "top": c(SNOW[4])})
	s.box(Vector3(HX - 8.0, 0.0, Z_TRIBUNE - 0.01), Vector3(16.0, 6.0, 3.0 - 1.2), {"front": c(STONE[3]),
		"side": c(STONE[2]), "top": c(SNOW[4])})
	# back wall and the two pylons (loudspeaker clusters on top)
	s.box(Vector3(HX - 26.0, 0.0, Z_TRIBUNE - 14.0), Vector3(52.0, 20.0, 2.0), {"front": c(VIOLET[2]),
		"side": c(VIOLET[1]), "top": c(SNOW[3])})
	s.box(Vector3(HX - 27.0, 20.0, Z_TRIBUNE - 14.6), Vector3(54.0, 1.4, 2.8), {"front": c(STONE[4]),
		"side": c(STONE[2]), "top": c(SNOW[4])})
	var m := K("metal")
	for side: float in [-1.0, 1.0]:
		var px: float = HX + side * 31.5 - 2.5
		s.box(Vector3(px, 0.0, Z_TRIBUNE - 15.0), Vector3(5.0, 25.0, 4.0), {"front": c(VIOLET[3]),
			"side": c(VIOLET[1]), "top": c(SNOW[4])})
		_horns(m, Vector3(px + 2.5, 25.0, Z_TRIBUNE - 13.0), 4)
	# banners on the back wall: the regime's cloth (neutral seal / historical banner via Symbols)
	var b := K("banner_portico")
	for k in 3:
		var bx := HX - 13.0 + k * 13.0
		b.quad(Vector3(bx - 2.2, 6.4, Z_TRIBUNE - 11.9), Vector3(bx - 2.2, 19.6, Z_TRIBUNE - 11.9),
			Vector3(bx + 2.2, 19.6, Z_TRIBUNE - 11.9), Vector3(bx + 2.2, 6.4, Z_TRIBUNE - 11.9), Color.WHITE, 0.45)
	# lectern with a microphone cluster
	s.box(Vector3(HX - 0.8, 6.0, Z_TRIBUNE - 1.6), Vector3(1.6, 1.3, 0.9), {"front": c(STONE[4]),
		"side": c(STONE[3]), "top": c(STONE[4])})
	m.box(Vector3(HX - 0.05, 7.3, Z_TRIBUNE - 1.3), Vector3(0.1, 0.5, 0.1), c(STEEL[1]))


func _horns(m: Kit, top: Vector3, n: int) -> void:
	m.box(Vector3(top.x - 0.12, top.y - 0.2, top.z - 0.12), Vector3(0.24, 2.6, 0.24), c(NIGHT[3]))
	for k in n:
		var hx := top.x - 1.2 + k * 0.8
		var y := top.y + 2.0
		for r in 3:
			var w := 0.18 + r * 0.12
			m.box(Vector3(hx - w, y - w * 0.6, top.z + 0.1 + r * 0.2), Vector3(w * 2.0, w * 1.4, 0.2),
				{"front": c(STEEL[2] if r == 2 else STEEL[1]), "side": c(STEEL[0]), "top": c(SNOW[3])})


func _build_barrier() -> void:
	var m := K("metal")
	m.box(Vector3(X_MIN, 0.98, Z_BARRIER - 0.04), Vector3(X_MAX - X_MIN, 0.08, 0.08), {"front": c(STEEL[3]),
		"top": c(SNOW[3])})
	m.box(Vector3(X_MIN, 0.5, Z_BARRIER - 0.03), Vector3(X_MAX - X_MIN, 0.06, 0.06), c(STEEL[2]))
	var x := X_MIN
	while x <= X_MAX:
		m.box(Vector3(x - 0.05, 0.0, Z_BARRIER - 0.05), Vector3(0.1, 1.06, 0.1), {"front": c(STEEL[2]),
			"side": c(STEEL[1]), "top": c(SNOW[4])})
		m.box(Vector3(x - 0.35, 0.0, Z_BARRIER - 0.3), Vector3(0.7, 0.08, 0.6), c(STEEL[1]))
		x += 2.5
	# loudspeaker poles along the lane
	for px: float in [-95.0, -35.0, 25.0, 85.0, 145.0, 205.0]:
		m.pillar(px, Z_BARRIER - 3.0, 0.0, 0.22, 0.22, 8.0, {"front": c(NIGHT[3]), "side": c(NIGHT[2]),
			"top": c(SNOW[4])})
		_horns(m, Vector3(px, 7.2, Z_BARRIER - 3.0), 2)


func _build_beams() -> void:
	var l := K("lamp")
	var m := K("metal")
	var bases: Array = []
	var z := -640.0
	while z > -980.0:
		for side: float in [-1.0, 1.0]:
			bases.append(Vector3(HX + side * 118.0, 0.0, z))
		z -= 42.0
	for d: float in [-250.0, -190.0, -130.0, 130.0, 190.0, 250.0]:
		bases.append(Vector3(HX + d, 0.0, -1115.0))
	for d: float in [-90.0, 0.0, 90.0]:
		bases.append(Vector3(HX + d, 0.0, -1330.0))
	var cols := [SNOW[3], SNOW[2], SNOW[1], SNOW[0], VIOLET[3]]
	var ems := [0.85, 0.7, 0.55, 0.4, 0.25]
	var ys := [0.0, 30.0, 140.0, 380.0, 800.0, 1500.0]
	for bpos: Vector3 in bases:
		# pillars lean a little towards the axis and back over the dome
		var lean := Vector3(signf(HX - bpos.x) * 0.05, 1.0, -0.03).normalized()
		var w := 1.15
		for k in 5:
			var a: Vector3 = bpos + lean * float(ys[k])
			var b2: Vector3 = bpos + lean * float(ys[k + 1])
			var cc: Color = c(cols[k])
			l.quad(a + Vector3(-w, 0, 0), b2 + Vector3(-w * 1.5, 0, 0), b2 + Vector3(w * 1.5, 0, 0),
				a + Vector3(w, 0, 0), cc, float(ems[k]))
		m.box(Vector3(bpos.x - 1.2, 0.0, bpos.z - 1.2), Vector3(2.4, 1.6, 2.4), {"front": c(STEEL[1]),
			"side": c(STEEL[0]), "top": c(SNOW[3])})
		halos.append({"pos": bpos + Vector3(0, 2.0, 0), "col": c(SNOW[4]), "r": 7.0, "k": 0.35})
	stats["beams"] = bases.size()


func _build_vehicles() -> void:
	var tank := _tank_mesh()
	var ht := _halftrack_mesh()
	for j in 7:
		var mi := MeshInstance3D.new()
		mi.name = "Vehicle%d" % j
		mi.mesh = tank if j < 4 else ht
		mi.material_override = mats.get("metal")
		add_child(mi)
		mi.position = Vector3(vehicle_x(j, 0.0), 0.0, Z_LANE)
		vehicles.append(mi)


## Fictional 1960s main battle tank, local frame: +x = driving direction, origin = hull centre on the ground.
func _tank_mesh() -> ArrayMesh:
	var k := Kit.new()
	var hull := {"front": c(STEEL[3]), "side": c(STEEL[2]), "top": c(STEEL[4])}
	var dark := {"front": c(NIGHT[3]), "side": c(NIGHT[2]), "top": c(STEEL[1])}
	for s: float in [-1.0, 1.0]:
		var zc: float = s * 1.25
		k.box(Vector3(-3.4, 0.0, zc - 0.35), Vector3(6.8, 0.95, 0.7), dark)
		for w in 6:
			k.box(Vector3(-2.7 + w * 1.05, 0.12, zc + s * 0.36 - 0.02), Vector3(0.62, 0.62, 0.04),
				{"front": c(STEEL[1]), "side": c(NIGHT[2])})
		k.box(Vector3(-3.5, 0.9, zc - 0.42), Vector3(7.0, 0.1, 0.84), c(STEEL[1]))
	k.box(Vector3(-3.3, 0.55, -1.6), Vector3(6.4, 0.95, 3.2), hull)
	k.quad(Vector3(3.1, 0.6, 1.6), Vector3(2.4, 1.5, 1.6), Vector3(2.4, 1.5, -1.6), Vector3(3.1, 0.6, -1.6),
		c(STEEL[3]))
	k.box(Vector3(-1.9, 1.5, -1.25), Vector3(2.9, 0.75, 2.5), hull)
	k.box(Vector3(-1.5, 2.25, -0.95), Vector3(2.0, 0.22, 1.9), {"front": c(STEEL[2]), "side": c(STEEL[1]),
		"top": c(SNOW[3])})
	k.box(Vector3(-1.3, 2.47, 0.25), Vector3(0.6, 0.32, 0.6), hull)
	k.box(Vector3(1.0, 1.82, -0.09), Vector3(4.7, 0.18, 0.18), dark)
	k.box(Vector3(2.9, 1.78, -0.13), Vector3(0.6, 0.26, 0.26), dark)
	k.box(Vector3(-3.35, 1.5, -1.5), Vector3(0.6, 0.35, 3.0), dark)
	return k.commit()


func _halftrack_mesh() -> ArrayMesh:
	var k := Kit.new()
	var body := {"front": c(STEEL[2]), "side": c(STEEL[1]), "top": c(STEEL[3])}
	var dark := {"front": c(NIGHT[2]), "side": c(NIGHT[1]), "top": c(NIGHT[3])}
	for s: float in [-1.0, 1.0]:
		k.box(Vector3(-3.0, 0.0, s * 1.0 - 0.3), Vector3(3.4, 0.85, 0.6), dark)
		k.box(Vector3(1.6, 0.0, s * 1.0 - 0.25), Vector3(0.9, 0.9, 0.5), dark)
	k.box(Vector3(-3.0, 0.6, -1.15), Vector3(4.2, 1.35, 2.3), body)
	k.box(Vector3(1.2, 0.6, -1.0), Vector3(1.9, 0.9, 2.0), body)
	k.quad(Vector3(3.1, 0.75, 1.0), Vector3(2.5, 1.5, 1.0), Vector3(2.5, 1.5, -1.0), Vector3(3.1, 0.75, -1.0),
		c(STEEL[3]))
	k.box(Vector3(0.9, 1.5, -1.1), Vector3(0.3, 0.6, 2.2), dark)
	# two rows of helmets above the open compartment: faceless, all looking the same way
	for r in 2:
		for q in 4:
			k.box(Vector3(-2.6 + q * 0.85, 1.95, -0.75 + r * 0.95), Vector3(0.42, 0.34, 0.42),
				{"front": c(STEEL[1]), "side": c(STEEL[0]), "top": c(STEEL[3])})
	return k.commit()


func _build_jets() -> void:
	var k := Kit.new()
	var col := c(NIGHT[2])
	k.box(Vector3(-7.0, -0.7, -0.7), Vector3(14.0, 1.4, 1.4), {"front": col, "side": c(NIGHT[1]),
		"top": c(STEEL[1])})
	k.tri(Vector3(2.0, 0.0, 0.7), Vector3(-3.5, 0.0, 6.0), Vector3(-4.5, 0.0, 0.7), col)
	k.tri(Vector3(2.0, 0.0, -0.7), Vector3(-4.5, 0.0, -0.7), Vector3(-3.5, 0.0, -6.0), col)
	k.tri(Vector3(2.0, 0.05, 0.7), Vector3(-4.5, 0.05, 0.7), Vector3(-3.5, 0.05, 6.0), col)
	k.tri(Vector3(2.0, 0.05, -0.7), Vector3(-3.5, 0.05, -6.0), Vector3(-4.5, 0.05, -0.7), col)
	k.box(Vector3(-7.0, 0.7, -0.1), Vector3(2.4, 2.8, 0.2), col)
	var mesh := k.commit()
	jets = Node3D.new()
	jets.name = "Jets"
	add_child(jets)
	for o: Vector3 in [Vector3(0, 0, 0), Vector3(-22, -3, 14), Vector3(-22, -3, -14), Vector3(-44, -6, 28),
			Vector3(-44, -6, -28)]:
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		mi.material_override = mats.get("metal")
		mi.position = o
		mi.scale = Vector3(1.6, 1.6, 1.6)
		jets.add_child(mi)
	jets.visible = false


func _build_lights() -> void:
	var lights := Node3D.new()
	lights.name = "ParadeLights"
	add_child(lights)
	var cold := c(STEEL[5])
	# cold rim lights for the hand-animated characters only (people layer 4): the family (p5) and Konrad (p7)
	var fam := _spot(lights, Vector3(FAMILY_X + 3.0, 9.0, -872.0), Vector3(FAMILY_X, 1.0, Z_CROWD_FRONT), cold, 2.2,
		40.0, 18.0)
	fam.light_cull_mask = 4
	var kon := _spot(lights, Vector3(-95.0, 7.0, -776.0), Vector3(-104.0, 1.2, -792.0), cold, 3.0, 40.0, 22.0)
	kon.light_cull_mask = 4
	# the tanks' flanks catch a cold flood where they pass the barrier camera (p3)
	_spot(lights, Vector3(-37.0, 14.0, -845.0), Vector3(-40.0, 1.0, Z_LANE), cold, 2.4, 70.0, 34.0)
	for side: float in [-1.0, 1.0]:
		_spot(lights, Vector3(HX + side * 24.0, 26.0, -868.0), Vector3(HX + side * 4.0, 6.0, Z_TRIBUNE - 6.0),
			cold, 2.0, 110.0, 32.0)
		_spot(lights, Vector3(HX + side * 90.0, 34.0, -830.0), Vector3(HX + side * 40.0, 0.0, Z_LANE), cold, 2.0,
			170.0, 48.0)
		_spot(lights, Vector3(HX + side * 120.0, 30.0, -900.0), Vector3(HX + side * 70.0, 0.0, -840.0), cold,
			1.5, 150.0, 40.0)


func _spot(parent: Node3D, from: Vector3, to: Vector3, col: Color, energy: float, rng_m: float,
		angle: float) -> SpotLight3D:
	var s := SpotLight3D.new()
	s.light_color = col
	s.light_energy = energy
	s.spot_range = rng_m
	s.spot_angle = angle
	s.spot_attenuation = 0.0
	s.spot_angle_attenuation = 0.6
	s.light_specular = 0.0
	s.shadow_enabled = false
	parent.add_child(s)
	s.look_at_from_position(from, to, Vector3.UP)
	return s
