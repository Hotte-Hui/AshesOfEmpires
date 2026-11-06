extends Node3D
## Avenue staging layer of the Great Hall set (owner: hall / great_hall_3d).  Opt-in: hall_builder.gd builds
## exactly what it always built; a level that wants the long avenue between the street (z = -63) and the plaza
## filled adds this node AFTER builder.build():
##     var avenue = load("res://scripts/levels/hall/hall_avenue.gd").new()
##     add_child(avenue)
##     avenue.build(builder, "parade")
## and the node follows its parent's clock on its own (parent.get_time(); update(t) is a pure function of t, so
## seek()/skip() stay deterministic).  Used by L_M1_Parade: shot p8 cranes up from the cleared street and looks
## down the whole avenue to the hall.  The near stretch stays the cleared street (the story beat: work crews, a
## few knots of people); from ~260 m on the avenue IS the spectacle -- a cold, regimented mass event that dwarfs
## everybody in it, seen from far away.
##
## What stands on the avenue (all original; regime insignia only through the Symbols-resolved flag / standard
## textures):
##   cordon     guards along both bollard lines (x = -1 / 91, one every 7 m), facing the people, crowd barriers
##              behind them, lamp posts every 36 m (cold heads, every other one throws a pool), loudspeakers,
##              the plaza's banner masts continued on the right (the left row would stand behind the street's
##              near lamp in p8, so it is left out)
##   fire       stone pylons with fire bowls on both bollard lines (every 24 m from the cleared street to the plaza):
##              two converging lines of flickering flames, every one throwing warm light on the cordon and the front
##              rows; on the right a third line of fire bowls along the grandstands' parapet
##   column     the marching column in the middle of the avenue: 15 blocks of 11 x 10 men in step, each led by an
##              officer and a colour party with three standards abreast (standard.png: silver-grey neutral cloth or
##              its _hist twin, Symbols-resolved -- pale over the dark blocks in both variants), ~20 m gaps between
##              the blocks; it moves up the avenue as one body (COL_SPEED), its tail ~85 m beyond Z_NEAR
##   honour     an honour file down each side of the column's lane (x = HX -+ 11, one man every 12 m): pale parade
##              greatcoats, white belts, bayonets -- they read as single men, not as a bar
##   vehicles   the vehicle column in the left lane, rows of three abreast (a row every 20 m, so every row reads on
##              its own from the roofs): six rows of tanks (commanders out of the hatches, guns fore and aft), then
##              six of lorries with seated infantry or under tarps, exhaust vapour; snow on the decks, turrets, guns,
##              tarps and helmets, rears dimly lit and each vehicle in the pool of its own dimmed headlights (from the
##              roofs: a chain of silhouettes, not dark gaps); it crawls along with the column; every design is
##              built once and instanced
##   halted     blocks formed up and waiting: a double file of 9 x 8 blocks the whole length of the right lane, and
##              in the left lane before the plaza, an officer in front of each (clean blocks with straight gaps);
##              delegations of civilians in blocks with banners on the right side plaza beyond the grandstands (only
##              where p8's last frame can see them, deleg_reach())
##   crowds     the people behind both barriers are the parade set's (parade_set.gd, same figures as on the plaza),
##              organised like everything here: marshals' lanes along the avenue through each crowd (LANES: lit snow,
##              lamps on short posts, marshals), cross-gaps at the gates, first-aid tents and loudspeaker masts
##              (CROSS), delegations in like coats behind plain banners in the middle strip (crowd_groups); on the
##              right, behind the lane, long grandstands packed with people (STAND_*).  crowd_depth() / crowd_clear()
##              / strip_at() / in_stand() say where the parade set may place whom; late arrivals walking up behind
##              them, traffic police at the gates, a barrier crew closing a gate
##   transport  the motor pool (lorries parked herring-bone, a fuel bowser, flood lamps, drivers waiting), two rows
##              of buses that brought the crowd (noses to the avenue, destination boards lit), staff cars, barrier
##              lorries being unloaded
##   work       a snow-clearing gang with shovels in the cleared lane, windrows of swept snow along it, the plough
##              lorry crawling ahead with its amber beacon turning (a pulsing light on the snow), a tipper being
##              loaded by hand, a spectator stand (far left) already packed on its finished part while the rest is
##              still a bare frame under work lights, scaffolding with work lamps on the dark blocks behind it
##   air        vapour leaning in the wind from vents / exhausts, a flock of crows circling over the roofs
## Figures are MultiMesh billboards (avenue_figures.gdshader, atlas from tools/pixelgen/gen_great_hall_avenue.py;
## band lock + far calm, see the shader), vehicles and street furniture are flat-shaded meshes in the builder's
## materials; the column, its banners and the vehicle column are two rigid moving nodes.  Per frame: only node
## positions, one light energy, the column's band-lock origin and shader time are written (no allocations).

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const B := preload("res://scripts/levels/hall/hall_builder.gd")
const FIG_SHADER := preload("res://assets/architecture/great_hall/avenue/avenue_figures.gdshader")
const DIR := "res://assets/architecture/great_hall/avenue/"
const HX := 45.0
const X_GUARD_L := 0.4               ## guards just inside the left bollard line (bollards at HX - 46)
const X_GUARD_R := 89.6
const X_BARRIER_L := -2.6            ## crowd barriers just outside the bollards
const X_BARRIER_R := 92.6
const Z_NEAR := -124.0               ## nothing nearer: the street before the plaza stays cleared
const Z_FAR := -792.0                ## nothing farther: the plaza crowd of the parade's set frays out from ~-799
const GUARD_STEP := 7.0              ## cordon guards: one man every 7 m
const HONOUR_STEP := 12.0            ## honour files: one man every 12 m (closer, the file fuses into a bar from p8)
const HONOUR_X := 11.0               ## honour files at HX -+ 11: they line the column's lane
const HONOUR_FROM := -150.0
const HONOUR_TO := -790.0
const STEP_FPS := 3.8
const COL_FILES := 11                ## the marching column: blocks of 11 files x 10 ranks
const COL_RANKS := 10
const COL_DX := 1.45
const COL_DZ := 1.6
const COL_BLOCKS := 15
const COL_PITCH := 40.0              ## front rank to front rank (block 20 m incl. officer + colours, 20 m gap)
const COL_HEAD := -784.0             ## front rank of the leading block at T_MID
const COL_SPEED := 1.4               ## m/s, the vehicle column crawls along at the same pace
const VEH_ROW_X := [8.5, 17.0, 25.5] ## the vehicle column drives three abreast in the left lane
const VEH_HEAD := -490.0             ## noses of the leading row at T_MID
const VEH_ROW_PITCH := 20.0          ## nose to nose: wide enough that every row reads on its own from p8
const VEH_ROWS := [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]   ## 0 tanks, 1 lorries with infantry
const HALT_FILES := 9                ## halted blocks: 9 files x 8 ranks, a double file of blocks
const HALT_RANKS := 8
const HALT_PITCH := 22.0
## [x of the block centre, front rank of the nearest block]: right lane all along, left lane before the plaza
const HALT_COLS := [[66.0, -258.0], [80.0, -258.0], [10.0, -512.0], [24.0, -512.0]]
const PYLON_FROM := -162.0           ## fire pylons on both bollard lines, between the bollards, every 24 m
const PYLON_STEP := 24.0
const X_PYLON_L := -1.0
const X_PYLON_R := 91.0
const FLAME_H := 1.5                 ## flame cell height (m): the fire stands ~1.4 m over the bowl
const DELEG_COLS := [150.0, 178.0, 206.0, 234.0, 262.0]   ## delegation blocks on the right side plaza (x centres)
const DELEG_FROM := -455.0           ## their rows: front ranks from here towards the plaza, every 30 m
const DELEG_TO := -760.0
## The crowds lining the avenue are organised, like everything here.  Marshals' lanes run along the avenue through
## each crowd ([from, to] metres behind the barrier, z where the lane begins): lit by lamps on short posts every
## LANE_LAMP_STEP, a marshal here and there.  Cross-gaps cut through the whole crowd (z centre, half width, kind):
## the cordon's gates, first-aid posts (a tent under a lamp) and loudspeaker masts.  Between the lanes the middle
## strip is taken by delegations standing in blocks in like coats behind two banners (crowd_groups()); the front
## strip is pressed against the barrier, the back strip loosens into clusters and a ragged edge.
const LANES := {-1: [[6.0, 8.2, -262.0], [14.6, 16.8, -336.0]], 1: [[7.4, 9.6, -366.0]]}
const LANE_LAMP_STEP := 12.0
const CROSS := {
	-1: [[-262.0, 2.4, "aid"], [-336.0, 4.6, "gate"], [-395.0, 2.4, "mast"], [-455.0, 4.0, "gate"],
		[-528.0, 2.4, "aid"], [-602.0, 2.4, "mast"], [-676.0, 2.4, "aid"], [-748.0, 2.4, "mast"]],
	1: [[-290.0, 4.0, "gate"], [-366.0, 2.4, "mast"], [-442.0, 2.4, "aid"], [-518.0, 2.4, "mast"],
		[-594.0, 2.4, "aid"], [-670.0, 2.4, "mast"], [-742.0, 2.4, "aid"]],
}
## Clothing groups (indices into the plaza crowd's 22 drawn coats, gen_parade_figs.CROWD) and the group colour
## the far calm pulls them towards (parade_figures.gdshader CALM_COLS): 0 mixed civilians (mostly dark coats),
## 1 works brigade (grey-blue work coats), 2 league (brown), 3 club (black), 4 women's league (light coats).
const COATS_DARK := [0, 3, 4, 10, 17, 20, 18, 11, 9, 19]
const COATS_STEEL := [2, 7, 12, 21]
const COATS_BROWN := [1, 8, 13, 15]
const COATS_WARM := [5, 16]
const COATS_PALE := [6, 14]
## banner cloth and lettered band colour per group (0 unused): works brigade cream, league rust, club pale grey with a
## black band, women's league grey-blue
const GROUP_CLOTH := [["#D2CCCB", "#443B43"], ["#D2CCCB", "#443B43"], ["#AF6C47", "#5F4530"], ["#B2ACB0", "#211623"],
	["#A3ACB4", "#454E58"]]
const T_MID := 43.75                 ## middle of shot p8 (40.5 - 47.0): moving things are placed for this time
const CROWS_FROM := 40.5             ## the flock is only shown from shot p8 on
const CROW_H := 1.4                  ## crow cell height in metres: the wing span (~1 m) fills the cell width
const FLOCK := Vector3(8.0, 40.0, -100.0)
const BEACON_HZ := 1.3               ## the plough's turning beacon: sweeps per second
const SNAP_BAND := 6.0               ## m: depth bands of the band lock (avenue_figures.gdshader)

var builder
var variant := "parade"
var meta: Dictionary = {}
var slots: Dictionary = {}
var fig_mat: ShaderMaterial
var puff_mat: ShaderMaterial
var crow_mat: ShaderMaterial
var flame_mat: ShaderMaterial
var col_mat: ShaderMaterial          ## the marching column's figures: band lock measured from the moving column
var _col: Node3D
var stats: Dictionary = {}
var placed: Dictionary = {}          ## node name -> the figure points it was built from (tests, tools)
var rng := RandomNumberGenerator.new()
var _quad: QuadMesh
var _kits: Dictionary = {}
var _movers: Array = []              ## {node, p0: Vector3, v: Vector3}  position = p0 + v * (t - T_MID)
var _crows: Node3D
var _beacon: OmniLight3D
var _last_t := -1.0


static func c(h: String) -> Color:
	return Color(h)


# ================================================================================================== build
func build(p_builder, p_variant: String = "parade") -> void:
	builder = p_builder
	variant = p_variant
	rng.seed = 1966
	var t0 := Time.get_ticks_usec()
	_quad = QuadMesh.new()
	_quad.size = Vector2(1, 1)
	var txt := FileAccess.get_file_as_string(DIR + "avenue_figures.json")
	var parsed = JSON.parse_string(txt) if txt != "" else {}
	meta = parsed if typeof(parsed) == TYPE_DICTIONARY else {}
	slots = meta.get("slots", {})
	fig_mat = _fig_material(1.8, 0.22)
	fig_mat.set_shader_parameter("fps", STEP_FPS)
	# the layer is only ever seen from p8's crane, 120 - 900 m away: band lock + far calm (avenue_figures.gdshader)
	fig_mat.set_shader_parameter("snap_band", SNAP_BAND)
	fig_mat.set_shader_parameter("calm", 1.0)
	col_mat = fig_mat.duplicate()
	# the column's standards: silver-grey neutral cloth or its _hist twin (Symbols.pick, gen_great_hall_avenue.py)
	if not builder.mats.has("standard"):
		var stp := Symbols.pick(DIR + "standard.png")
		var stt: Texture2D = load(stp) if ResourceLoader.exists(stp) else null
		builder.mats["standard"] = builder._toon({"use_tex": stt != null, "albedo_tex": stt, "use_vertex_color": false,
			"alpha_scissor": 0.5, "toon_steps": 4.0, "light_wrap": 0.35, "snow": 0.0})
	puff_mat = _fig_material(3.0, 0.05)
	puff_mat.set_shader_parameter("rise_h", 3.2)
	puff_mat.set_shader_parameter("period", 4.2)
	puff_mat.set_shader_parameter("drift", Vector3(2.6, 0.0, -0.8))
	crow_mat = _fig_material(CROW_H, 0.0)
	crow_mat.set_shader_parameter("fps", 7.0)
	flame_mat = _fig_material(FLAME_H, 1.5)
	flame_mat.set_shader_parameter("fps", 7.5)
	_build_cordon()
	_build_fire_pylons()
	_build_flag_masts()
	_build_motor_pool()
	_build_buses()
	_build_stand()
	_build_far_scaffolds()
	_build_snow_work()
	_build_lane_start()
	_build_vents()
	_build_delegation_banners()
	_build_crowd_lanes()
	_build_grandstand()
	_flush()
	_build_static_figures()
	_build_column()
	_build_vehicle_column()
	_build_walkers()
	_build_moving_vehicles()
	_build_puffs()
	_build_flames()
	_build_crows()
	_build_lights()
	stats["build_ms"] = snappedf((Time.get_ticks_usec() - t0) / 1000.0, 0.1)
	update(0.0)


# ================================================================================================ per frame
func _process(_delta: float) -> void:
	var p := get_parent()
	if p == null or not p.has_method("get_time"):
		return
	var t: float = p.get_time()
	if t != _last_t:
		update(t)


func update(t: float) -> void:
	_last_t = t
	fig_mat.set_shader_parameter("time", t)
	col_mat.set_shader_parameter("time", t)
	puff_mat.set_shader_parameter("time", t)
	crow_mat.set_shader_parameter("time", t)
	flame_mat.set_shader_parameter("time", t)
	for m in _movers:
		(m["node"] as Node3D).position = (m["p0"] as Vector3) + (m["v"] as Vector3) * (t - T_MID)
	if _col:
		col_mat.set_shader_parameter("snap_origin", _col.position)
	if _crows:
		_crows.visible = t >= CROWS_FROM
		_crows.rotation.y = 0.22 * (t - T_MID)
	if _beacon:
		_beacon.light_energy = beacon_energy(t)


## The turning beacon: a narrow bright sweep once per turn, a faint glow in between.
static func beacon_energy(t: float) -> float:
	var s := maxf(0.0, cos(fposmod(t * BEACON_HZ, 1.0) * TAU))
	return 0.25 + 2.6 * pow(s, 6.0)


# ================================================================================================ materials
func _fig_material(height_m: float, self_light: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = FIG_SHADER
	var tex: Texture2D = load(DIR + "avenue_figures.png") if ResourceLoader.exists(DIR + "avenue_figures.png") \
		else null
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


func K(name: String, primitive: int = Mesh.PRIMITIVE_TRIANGLES) -> Kit:
	if not _kits.has(name):
		_kits[name] = Kit.new(primitive)
	return _kits[name]


## Local frame for the next objects: x along `along` (vehicle front), y up, z across.
func _at(origin: Vector3, along: Vector3) -> void:
	var x := along.normalized()
	var z := x.cross(Vector3.UP).normalized()
	var xf := Transform3D(Basis(x, Vector3.UP, z), origin)
	for k in _kits.values():
		(k as Kit).xf = xf


func _world() -> void:
	for k in _kits.values():
		(k as Kit).xf = Transform3D.IDENTITY


func _ensure_kits(names: Array) -> void:
	for n in names:
		K(str(n))


func _flush() -> void:
	var geo := Node3D.new()
	geo.name = "AvenueGeometry"
	add_child(geo)
	var tris := 0
	for name in _kits:
		var kit: Kit = _kits[name]
		if kit.count == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "M_" + str(name)
		mi.mesh = kit.commit()
		mi.material_override = builder.mats.get(name, builder.mats["metal"])
		mi.layers = B.LAYER_OUT
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if name in ["lamp", "wires"] \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		geo.add_child(mi)
		tris += kit.count / (2 if kit.primitive == Mesh.PRIMITIVE_LINES else 3)
	stats["primitives"] = tris
	_kits = {}


## A self-contained mesh node (moving vehicles, the column's banners): the given builder callable fills fresh kits
## in a local frame; the node is added under `parent` (default: this layer).
func _mesh_node(node_name: String, fill: Callable, parent: Node3D = null) -> Node3D:
	var saved := _kits
	_kits = {}
	_ensure_kits(["metal", "glass", "lamp"])
	fill.call()
	var n := Node3D.new()
	n.name = node_name
	(parent if parent != null else self).add_child(n)
	var tris := 0
	for name in _kits:
		var kit: Kit = _kits[name]
		if kit.count == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "M_" + str(name)
		mi.mesh = kit.commit()
		mi.material_override = builder.mats.get(name, builder.mats["metal"])
		mi.layers = B.LAYER_OUT
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if name in ["lamp", "wires"] \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		n.add_child(mi)
		tris += kit.count / (2 if kit.primitive == Mesh.PRIMITIVE_LINES else 3)
	n.set_meta("primitives", tris)
	_kits = saved
	return n


# ============================================================================================ shape helpers
## Side profile `pts` (Vector2(x, y) in the vehicle frame) extruded across from z0 to z1 (either order).
static func _xprism(k: Kit, pts: Array, z0: float, z1: float, cols) -> void:
	k.prism(pts, Vector3.ZERO, Vector3.RIGHT, Vector3.UP, Vector3.BACK, minf(z0, z1), maxf(z0, z1), cols)


## Cross-section `pts` (Vector2(z, y)) extruded along the vehicle from x0 to x1.
static func _zprism(k: Kit, pts: Array, x0: float, x1: float, cols) -> void:
	k.prism(pts, Vector3.ZERO, Vector3.BACK, Vector3.UP, Vector3.RIGHT, minf(x0, x1), maxf(x0, x1), cols)


## Wheel on the side `sd` (+1 / -1): tyre (axis across), a pale hub on the outer face when `hub`.
static func _wheel(k: Kit, ctr: Vector3, r: float, wid: float, sd: float, hub: bool, sides: int = 8) -> void:
	k.cyl(ctr - Vector3(0, 0, wid * 0.5), ctr + Vector3(0, 0, wid * 0.5), r, r, sides, c(B.NIGHT[0]))
	if hub:
		var o := ctr + Vector3(0, 0, sd * wid * 0.5)
		k.cyl(o, o + Vector3(0, 0, sd * 0.03), r * 0.46, r * 0.4, 6, c(B.STEEL[2]))


# ================================================================================================ the cordon
func _build_cordon() -> void:
	_world()
	var m := K("metal")
	var lamp := K("lamp")
	var dark := {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2]), "top": c(B.SNOW[3])}
	for side: float in [-1.0, 1.0]:
		var xb: float = X_BARRIER_L if side < 0.0 else X_BARRIER_R
		# crowd barriers: 2.4 m sections (a dark mesh panel under a pale top rail), gates for the vehicles
		var z := Z_NEAR - 2.0
		while z > Z_FAR:
			if not _is_gate(side, z):
				m.box(Vector3(xb - 0.05, 0.22, z - 2.35), Vector3(0.1, 0.8, 2.35), {"front": c(B.STEEL[1]),
					"side": c(B.STEEL[1]), "top": c(B.STEEL[3])})
				m.box(Vector3(xb - 0.07, 1.0, z - 2.4), Vector3(0.14, 0.1, 2.4), {"front": c(B.STEEL[4]),
					"side": c(B.STEEL[4]), "top": c(B.SNOW[4])})
				m.box(Vector3(xb - 0.35, 0.0, z - 0.1), Vector3(0.7, 0.08, 0.16), c(B.STEEL[2]))
			z -= 2.45
		# lamp posts of the cordon (cold heads), a loudspeaker on every third
		var xl: float = xb + side * 1.2
		var zl := -140.0
		var i := 0
		while zl > Z_FAR + 4.0:
			m.pillar(xl, zl, 0.0, 0.22, 0.22, 7.0, dark)
			m.pillar(xl, zl, 0.0, 0.42, 0.42, 0.9, {"front": c(B.NIGHT[2]), "side": c(B.NIGHT[1])})
			m.box(Vector3(xl - 0.45, 6.95, zl - 0.06), Vector3(0.9, 0.12, 0.12), c(B.NIGHT[2]))
			lamp.box(Vector3(xl - 0.3, 6.25, zl - 0.3), Vector3(0.6, 0.72, 0.6), c(B.SNOW[4]), Kit.FACES_ALL, 1.0)
			m.box(Vector3(xl - 0.36, 6.95, zl - 0.36), Vector3(0.72, 0.14, 0.72), {"front": c(B.NIGHT[2]),
				"top": c(B.SNOW[4])})
			if i % 3 == 1:
				for sx: float in [-1.0, 1.0]:
					m.box(Vector3(xl + sx * 0.18 - (0.34 if sx < 0.0 else 0.0), 5.3, zl - 0.25),
						Vector3(0.34, 0.5, 0.5), {"front": c(B.STEEL[1]), "side": c(B.STEEL[0])})
			zl -= 36.0
			i += 1
	stats["cordon_lamps"] = 2 * int((-140.0 - (Z_FAR + 4.0)) / 36.0 + 1.0)


static func _is_gate(side: float, z: float) -> bool:
	return (side < 0.0 and (absf(z + 336.0) < 7.0 or absf(z + 455.0) < 6.0)) \
		or (side > 0.0 and absf(z + 290.0) < 6.0)


## The crowd behind the barrier (built by parade_set.gd with the plaza's figures) keeps a corridor open at every
## gate of the cordon, a little narrower than the gate itself (people press up to its edges).
static func gate_corridor(side: float, z: float) -> bool:
	return (side < 0.0 and (absf(z + 336.0) < 4.6 or absf(z + 455.0) < 4.0)) \
		or (side > 0.0 and absf(z + 290.0) < 4.0)


## How deep the people stand behind the barrier at z (metres from the barrier to the ragged back edge): a few
## metres at the cleared street, 24 m (left) / 21 m (right, the buses park behind) towards the plaza, with a slow
## wave along the avenue.  The left edge stays clear of the motor pool and the buses (x < -44).
static func crowd_depth(side: float, z: float) -> float:
	var k := smoothstep(-140.0, -380.0, z)
	var full := 24.0 if side < 0.0 else 21.0
	return maxf(2.0, lerpf(4.5, full, k) + 2.4 * sin(z * 0.043 + side) + 1.5 * sin(z * 0.017 + 2.0))


## False where nobody of the crowd may stand: the cordon's lamp posts, the plaza's lamp masts, the flood poles.
static func crowd_clear(x: float, z: float) -> bool:
	for side: float in [-1.0, 1.0]:
		var xl: float = (X_BARRIER_L if side < 0.0 else X_BARRIER_R) + side * 1.2
		if absf(x - xl) < 0.6 and absf(fposmod(-140.0 - z + 18.0, 36.0) - 18.0) < 0.6:
			return false
		if absf(x - (HX + side * 72.0)) < 1.4 and z < -165.0 and z > -885.0 \
				and absf(fposmod(-170.0 - z + 75.0, 150.0) - 75.0) < 1.4:
			return false
	return true


## Is z inside one of the cross-gaps of `side` (widened by `pad` metres)?
static func cross_gap(side: float, z: float, pad: float = 0.0) -> bool:
	for g: Array in CROSS[int(side)]:
		if absf(z - float(g[0])) < float(g[1]) + pad:
			return true
	return false


## Does marshals' lane k of `side` run at z?
static func lane_active(side: float, k: int, z: float) -> bool:
	var l: Array = LANES[int(side)][k]
	return z <= float(l[2]) and z > Z_FAR + 2.0 and crowd_depth(side, z) >= float(l[1]) + 2.5


## Which part of the crowd stands `pd` metres behind the barrier at z: -1 a marshals' lane, 0 the front strip, 1 the
## middle strip (delegations), 2 the back strip.  Where no lane runs yet, everything is front strip.
static func strip_at(side: float, pd: float, z: float) -> int:
	var lanes: Array = LANES[int(side)]
	var l0: Array = lanes[0]
	if not lane_active(side, 0, z) or pd < float(l0[0]):
		return 0
	if pd < float(l0[1]):
		return -1
	if lanes.size() > 1:
		var l1: Array = lanes[1]
		if not lane_active(side, 1, z):
			return 2
		if pd < float(l1[0]):
			return 1
		if pd < float(l1[1]):
			return -1
		return 2
	return 1 if pd < float(l0[1]) + 7.0 else 2


## The delegations of the middle strip: [z near end, z far end, group 1..4 or 0 = mixed civilians], one to three per
## section between the cross-gaps (a fixed sequence, the right side offset against the left), deterministic.
static func crowd_groups(side: float) -> Array:
	var out: Array = []
	var lane0: Array = LANES[int(side)][0]
	var cuts: Array = [float(lane0[2])]
	for g: Array in CROSS[int(side)]:
		if float(g[0]) < float(lane0[2]) - 1.0:
			cuts.append(float(g[0]))
	cuts.append(Z_FAR)
	var seq := [1, 0, 2, 3, 0, 1, 4, 2, 0, 3, 1, 0, 2, 4, 0, 1, 3, 2]
	var si := 0 if side < 0.0 else 5
	for i in cuts.size() - 1:
		var za: float = cuts[i] - 3.0
		var zb: float = cuts[i + 1] + 3.0
		var n := 1 if za - zb < 34.0 else (2 if za - zb < 62.0 else 3)
		var step := (za - zb) / float(n)
		for k in n:
			var z0 := za - k * step
			var z1 := z0 - step + (2.2 if k < n - 1 else 0.0)
			out.append([z0, z1, int(seq[si % seq.size()])])
			si += 1
	return out


## Group of the middle strip at z (0 = mixed civilians, also between the groups).
static func group_at(groups: Array, z: float) -> int:
	for g: Array in groups:
		if z <= float(g[0]) and z >= float(g[1]):
			return int(g[2])
	return 0


## Right edge of what p8's last frame (camera x = -6.5, z = -6, 24 deg vertical FOV, 16:9) sees at depth z, minus
## a margin: the delegation blocks are only staged up to here.
static func deleg_reach(z: float) -> float:
	return -6.5 + 0.377 * (-6.0 - z) - 2.0


## Fire pylon positions (feet) along both bollard lines, between the bollards, from the cleared street to the plaza.
static func pylon_spots() -> Array:
	var out: Array = []
	for x: float in [X_PYLON_L, X_PYLON_R]:
		var z := PYLON_FROM
		while z > Z_FAR + 4.0:
			out.append(Vector3(x, 0.0, z))
			z -= PYLON_STEP
	return out


## Stone pylons with fire bowls on both bollard lines: a stepped plinth, a squat fluted shaft, a cornice, a short
## bronze stem and a wide shallow bowl with a rolled lip; the fire itself is a flickering billboard (_build_flames)
## and every one lights the cordon and the front rows of the crowd (_build_lights).
func _build_fire_pylons() -> void:
	_world()
	var s := K("stone")
	var m := K("metal")
	var plinth := {"front": c(B.STONE[1]), "side": c(B.STONE[0]), "top": c(B.SNOW[3])}
	var shaft := {"front": c(B.STONE[2]), "side": c(B.STONE[1]), "top": c(B.SNOW[3])}
	var corn := {"front": c(B.STONE[3]), "side": c(B.STONE[2]), "top": c(B.SNOW[4])}
	for p: Vector3 in pylon_spots():
		s.box(Vector3(p.x - 0.75, 0.0, p.z - 0.75), Vector3(1.5, 0.3, 1.5), plinth)
		s.box(Vector3(p.x - 0.6, 0.3, p.z - 0.6), Vector3(1.2, 0.22, 1.2), plinth)
		s.box(Vector3(p.x - 0.45, 0.52, p.z - 0.45), Vector3(0.9, 2.0, 0.9), shaft)
		for fx: float in [-0.22, 0.0, 0.22]:                                   # flutes on the faces
			s.box(Vector3(p.x + fx - 0.03, 0.7, p.z + 0.451), Vector3(0.06, 1.6, 0.004), c(B.STONE[0]), Kit.FACE_PZ)
			s.box(Vector3(p.x + 0.451, 0.7, p.z + fx - 0.03), Vector3(0.004, 1.6, 0.06), c(B.STONE[0]), Kit.FACE_PX)
			s.box(Vector3(p.x - 0.455, 0.7, p.z + fx - 0.03), Vector3(0.004, 1.6, 0.06), c(B.STONE[0]), Kit.FACE_NX)
		s.box(Vector3(p.x - 0.58, 2.52, p.z - 0.58), Vector3(1.16, 0.2, 1.16), corn)
		m.cyl(Vector3(p.x, 2.72, p.z), Vector3(p.x, 2.92, p.z), 0.2, 0.14, 8, c(B.OCHRE[1]))
		m.lathe(Vector3(p.x, 2.9, p.z), [Vector2(0.14, 0.0), Vector2(0.5, 0.18), Vector2(0.72, 0.38),
			Vector2(0.78, 0.44), Vector2(0.7, 0.46)], 10,
			func(_i, j): return c(B.OCHRE[0]) if j < 2 else (c(B.OCHRE[2]) if j == 2 else c(B.OCHRE[3])))
		K("lamp").box(Vector3(p.x - 0.46, 3.22, p.z - 0.46), Vector3(0.92, 0.08, 0.92), c(B.OCHRE[4]), Kit.FACES_ALL,
			1.0)                                                                # the glowing embers in the bowl
	stats["fire_pylons"] = pylon_spots().size()


func _build_flag_masts() -> void:
	# the plaza's mast rows (hall_builder: HX +- 96, every 102 m from z = -520) continued towards the street on the
	# right, same mast and cloth (flag_pole: neutral file or its _hist twin through Symbols.pick).  Not on the left:
	# from p8's roof there the masts stand straight behind the street's near lamp and its head cuts the cloth.
	_world()
	var m := K("metal")
	var fl := K("flag_pole")
	var x: float = HX + 96.0
	for z: float in [-418.0, -316.0]:
		m.pillar(x, z, 0.0, 0.6, 0.6, 34.0, {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2])})
		m.box(Vector3(x - 3.2, 33.0, z - 0.2), Vector3(6.4, 0.4, 0.4), c(B.NIGHT[2]))
		fl.quad(Vector3(x - 2.8, 16.0, z + 0.4), Vector3(x - 2.8, 33.0, z + 0.4), Vector3(x + 2.8, 33.0, z + 0.4),
			Vector3(x + 2.8, 16.0, z + 0.4), Color.WHITE, 0.5)
	stats["banner_masts"] = 2


# ================================================================================================ vehicles
## Army lorry (original design), front = +x, 7.4 x 2.35 m: sloping bonnet and flat-fronted cab with a raked
## windscreen, arched front mudguards, single front / dual rear wheels, a planked bed.  cargo: 0 tarp on hoops
## (snow on its roof), 1 open with stacked barrier sections, 2 fuel tank (bowser), 3 cable drum, 4 seated infantry.
## fine: hubs + 8-sided tyres.
func lorry_into(kb: Kit, kg: Kit, kl: Kit, body: Color, tarp: Color, head_lit := false, cargo := 0,
		fine := true) -> void:
	var W := 2.35
	var hw := W * 0.5
	var bd := {"front": body, "side": body.darkened(0.18), "top": body.lightened(0.06)}
	kb.box(Vector3(-3.7, 0.55, -0.5), Vector3(7.2, 0.28, 1.0), c(B.NIGHT[1]), Kit.FACES_ALL)
	kb.box(Vector3(3.5, 0.48, -hw + 0.05), Vector3(0.16, 0.24, W - 0.1), c(B.NIGHT[2]), Kit.FACES_ALL)
	_xprism(kb, [Vector2(2.25, 0.82), Vector2(3.5, 0.82), Vector2(3.5, 1.5), Vector2(3.35, 1.66),
		Vector2(2.25, 1.72)], -0.78, 0.78, bd)
	kg.face(Vector3(3.505, 1.16, 0.0), Vector3.RIGHT, Vector3.UP, 0.55, 0.3, c(B.NIGHT[2]))       # grille
	_xprism(kb, [Vector2(0.85, 0.82), Vector2(2.3, 0.82), Vector2(2.3, 1.82), Vector2(2.12, 2.72),
		Vector2(0.85, 2.76)], -hw + 0.08, hw - 0.08, bd)
	kg.face(Vector3(2.215, 2.27, 0.0), Vector3(0.985, 0.171, 0.0), Vector3(-0.171, 0.985, 0.0), 0.92, 0.36,
		c(B.STEEL[2]))                                                                             # windscreen
	kg.face(Vector3(0.845, 2.2, 0.0), Vector3.LEFT, Vector3.UP, 0.6, 0.25, c(B.STEEL[1]))         # cab back window
	for sd: float in [-1.0, 1.0]:
		var zs := sd * (hw - 0.075)
		kg.face(Vector3(1.75, 2.27, zs), Vector3(0, 0, sd), Vector3.UP, 0.42, 0.3, c(B.STEEL[1]))    # door window
		kb.face(Vector3(1.18, 1.4, zs + sd * 0.006), Vector3(0, 0, sd), Vector3.UP, 0.025, 0.5,
			body.darkened(0.4))                                                                    # door seam
		_xprism(kb, [Vector2(2.15, 0.82), Vector2(2.4, 1.22), Vector2(3.2, 1.28), Vector2(3.52, 0.98),
			Vector2(3.52, 0.82)], sd * 0.78, sd * (hw + 0.02), bd)                                  # mudguard
		kb.box(Vector3(-3.4, 1.02, (hw - 0.4) if sd > 0.0 else -hw - 0.02), Vector3(2.6, 0.06, 0.42),
			c(B.NIGHT[2]))                                                                         # rear guard
		var hl := Vector3(3.53, 1.08, sd * 0.9)
		if head_lit:
			kl.box(hl - Vector3(0.06, 0.1, 0.1), Vector3(0.1, 0.2, 0.2), c(B.GLOW[4]), Kit.FACES_ALL, 1.0)
		else:
			kb.box(hl - Vector3(0.06, 0.1, 0.1), Vector3(0.1, 0.2, 0.2), c(B.STEEL[3]), Kit.FACES_ALL)
		kl.box(Vector3(-3.82, 0.86, sd * 0.95 - 0.08), Vector3(0.06, 0.12, 0.16), c(B.OCHRE[3]), Kit.FACES_ALL,
			0.7)                                                                                   # tail light
		for wx: float in [2.82, -1.55, -2.75]:
			_wheel(kb, Vector3(wx, 0.5, sd * (hw - 0.2)), 0.5, 0.36 if wx > 0.0 else 0.44, sd, fine,
				8 if fine else 6)
	# planked bed
	var plank := {"front": c(B.STONE[2]), "side": c(B.STONE[1]), "top": c(B.STONE[3])}
	kb.box(Vector3(-3.78, 0.83, -hw), Vector3(4.5, 0.14, W), c(B.STONE[1]), Kit.FACES_ALL)
	if cargo != 2:
		for sd: float in [-1.0, 1.0]:
			kb.box(Vector3(-3.78, 0.97, (hw - 0.07) if sd > 0.0 else -hw), Vector3(4.5, 0.55, 0.07), plank)
			if fine:
				for y: float in [1.15, 1.34]:
					kb.face(Vector3(-1.53, y, sd * (hw + 0.002)), Vector3(0, 0, sd), Vector3.UP, 2.25, 0.012,
						c(B.STONE[0]))
		kb.box(Vector3(-3.82, 0.97, -hw), Vector3(0.07, 0.55, W), plank)
	if cargo == 0:
		var tp := {"front": tarp.darkened(0.14), "side": tarp, "top": c(B.SNOW[3])}
		_zprism(kb, [Vector2(-hw + 0.02, 1.5), Vector2(hw - 0.02, 1.5), Vector2(hw - 0.02, 2.62), Vector2(0.78, 2.98),
			Vector2(-0.78, 2.98), Vector2(-hw + 0.02, 2.62)], -3.8, 0.72, tp)
		for xh: float in [-3.1, -1.7, -0.3]:
			for sd: float in [-1.0, 1.0]:
				kb.face(Vector3(xh, 2.06, sd * (hw - 0.012)), Vector3(0, 0, sd), Vector3.UP, 0.05, 0.56,
					tarp.darkened(0.3))                                                            # hoop ribs
		kb.face(Vector3(-3.805, 2.2, 0.0), Vector3.LEFT, Vector3.UP, 0.7, 0.55, tarp.darkened(0.3))  # rear flap
	elif cargo == 1:
		for s in 5:
			kb.box(Vector3(-3.6 + s * 0.06, 1.0 + s * 0.13, -0.95), Vector3(4.0, 0.1, 1.9), {"front": c(B.STEEL[4]),
				"side": c(B.STEEL[3]), "top": c(B.STEEL[4]) if s < 4 else c(B.SNOW[3])})
	elif cargo == 4:
		# infantry seated on two benches facing each other: greatcoats, helmets in two rows (snow on top), rifles
		# upright between the knees
		var coat := {"front": c(B.STEEL[2]), "side": c(B.STEEL[1]), "top": c(B.STEEL[3])}
		var helm := {"front": c(B.STEEL[2]), "side": c(B.STEEL[1]), "top": c(B.SNOW[3])}
		for sd: float in [-1.0, 1.0]:
			for i in 5:
				var tx := -3.45 + i * 0.84
				var tz := sd * 0.66
				kb.box(Vector3(tx - 0.19, 1.06, tz - 0.17), Vector3(0.38, 0.66, 0.34), coat)
				kb.box(Vector3(tx - 0.15, 1.72, tz - 0.15), Vector3(0.3, 0.2, 0.3), helm)
				kb.box(Vector3(tx + 0.14, 1.1, tz - sd * 0.24 - 0.02), Vector3(0.04, 0.98, 0.04), c(B.NIGHT[1]))
	elif cargo == 3:
		for zf: float in [-0.85, 0.65]:
			kb.cyl(Vector3(-1.7, 1.95, zf), Vector3(-1.7, 1.95, zf + 0.2), 0.95, 0.95, 10, c(B.STONE[2]))   # flanges
		kb.cyl(Vector3(-1.7, 1.95, -0.65), Vector3(-1.7, 1.95, 0.65), 0.7, 0.7, 10, c(B.NIGHT[2]))      # cable
		kb.box(Vector3(-2.3, 0.97, -0.9), Vector3(1.2, 0.2, 1.8), c(B.STONE[1]))                    # cradle
	else:
		_zprism(kb, [Vector2(-0.95, 1.0), Vector2(0.95, 1.0), Vector2(1.08, 1.55), Vector2(0.95, 2.1),
			Vector2(-0.95, 2.1), Vector2(-1.08, 1.55)], -3.6, 0.6, {"front": c(B.PATINA[1]), "side": c(B.PATINA[2]),
			"top": c(B.SNOW[3])})
		kb.box(Vector3(-1.7, 2.1, -0.25), Vector3(0.5, 0.18, 0.5), c(B.PATINA[1]))              # filler dome
		kb.box(Vector3(-3.75, 0.9, -0.6), Vector3(0.12, 0.5, 1.2), c(B.NIGHT[2]))               # pump box


## A city bus (original design): front = +x, 11 x 2.5 x 3 m, rounded roof, cream upper body over a livery skirt
## with a chrome strip, window band (some dimly lit: drivers waiting), lit destination board, doors, wheel
## arches, roof hatches under snow.
func bus_into(kb: Kit, kg: Kit, kl: Kit, body: Color, upper: Color, cabin_lit := false) -> void:
	var L := 11.0
	var W := 2.5
	var hw := W * 0.5
	var x0 := -L * 0.5
	_zprism(kb, [Vector2(-hw, 0.4), Vector2(hw, 0.4), Vector2(hw, 2.68), Vector2(hw - 0.22, 2.95),
		Vector2(-hw + 0.22, 2.95), Vector2(-hw, 2.68)], x0, -x0, {"front": upper, "side": upper.darkened(0.1),
		"top": c(B.SNOW[3])})
	for sd: float in [-1.0, 1.0]:
		var zz := sd * (hw + 0.004)
		var n := Vector3(0, 0, sd)
		kb.face(Vector3(0.0, 0.97, zz), n, Vector3.UP, L * 0.5, 0.57, body)                     # livery skirt
		kb.face(Vector3(0.0, 1.56, zz + sd * 0.002), n, Vector3.UP, L * 0.5, 0.03, c(B.STEEL[4]))  # chrome strip
		var xw := x0 + 1.15
		var i := 0
		while xw < L * 0.5 - 1.4:
			if cabin_lit and (i + int(sd)) % 3 == 0:
				kl.face(Vector3(xw + 0.6, 2.12, zz + sd * 0.002), n, Vector3.UP, 0.58, 0.38, c(B.GLOW[0]), 0.35)
			else:
				kg.face(Vector3(xw + 0.6, 2.12, zz + sd * 0.002), n, Vector3.UP, 0.58, 0.38, c(B.STEEL[1]))
			xw += 1.42
			i += 1
		for wx: float in [x0 + 2.2, L * 0.5 - 2.1]:
			kb.face(Vector3(wx, 0.62, zz + sd * 0.003), n, Vector3.UP, 0.66, 0.3, c(B.NIGHT[0]))   # wheel arch
			_wheel(kb, Vector3(wx, 0.5, sd * (hw - 0.12)), 0.5, 0.3, sd, true, 6)
	# doors on the kerb side
	for xd: float in [L * 0.5 - 1.25, -0.4]:
		kg.face(Vector3(xd, 1.55, hw + 0.008), Vector3.BACK, Vector3.UP, 0.5, 1.05, c(B.STEEL[1]))
	# front: windscreen, lit destination board, head lamps, bumper; rear: window, engine grille
	kg.face(Vector3(L * 0.5 + 0.005, 2.0, 0.0), Vector3.RIGHT, Vector3.UP, 1.08, 0.52, c(B.STEEL[2]))
	kl.face(Vector3(L * 0.5 + 0.007, 2.72, 0.0), Vector3.RIGHT, Vector3.UP, 0.85, 0.13, c(B.SNOW[3]), 0.6)
	for sd: float in [-1.0, 1.0]:
		kg.face(Vector3(L * 0.5 + 0.007, 0.78, sd * 0.88), Vector3.RIGHT, Vector3.UP, 0.13, 0.11, c(B.STEEL[4]))
	kb.box(Vector3(L * 0.5 - 0.02, 0.4, -hw + 0.05), Vector3(0.14, 0.2, W - 0.1), c(B.STEEL[4]), Kit.FACES_ALL)
	kg.face(Vector3(x0 - 0.005, 2.2, 0.0), Vector3.LEFT, Vector3.UP, 0.95, 0.35, c(B.STEEL[1]))
	kb.face(Vector3(x0 - 0.006, 0.95, 0.0), Vector3.LEFT, Vector3.UP, 0.8, 0.28, c(B.NIGHT[2]))
	for xr: float in [-2.5, 1.5]:
		kb.box(Vector3(xr, 2.95, -0.45), Vector3(0.9, 0.12, 0.9), {"front": upper.darkened(0.2), "top": c(B.SNOW[4])})


## Fictional main battle tank (original design, same family as the parade's column), front = +x, origin = hull
## centre on the ground: tracks with six road wheels a side (pale discs in front of the dark belt), sprocket and
## idler, track guards with stowage boxes and tools, welded hull with a steep glacis, engine deck louvres, rear
## jerry cans, cast turret with bustle, stowage basket and tarp roll, mantlet, long gun with fume extractor and
## muzzle brake, cupola with the hatch open and the commander out to the chest, a short whip.
func tank_into(kb: Kit, kw: Kit, gun_yaw := 0.0) -> void:
	var hull := {"front": c(B.STEEL[2]), "side": c(B.STEEL[1]), "top": c(B.STEEL[3])}
	var box := {"front": c(B.STEEL[1]), "side": c(B.STEEL[0]), "top": c(B.STEEL[3])}
	for sd: float in [-1.0, 1.0]:
		var zi := 1.02 * sd
		var zo := 1.62 * sd
		_xprism(kb, [Vector2(-3.45, 0.42), Vector2(-3.15, 0.04), Vector2(3.05, 0.04), Vector2(3.5, 0.5),
			Vector2(3.25, 0.88), Vector2(-3.3, 0.86)], zi, zo, {"front": c(B.NIGHT[1]), "side": c(B.NIGHT[2]),
			"top": c(B.STEEL[1])})
		for i in 6:
			var wx := -2.45 + i * 0.98
			kb.cyl(Vector3(wx, 0.42, zo), Vector3(wx, 0.42, zo + sd * 0.07), 0.36, 0.36, 8, c(B.STEEL[2]))
			kb.cyl(Vector3(wx, 0.42, zo + sd * 0.07), Vector3(wx, 0.42, zo + sd * 0.1), 0.13, 0.11, 6, c(B.NIGHT[3]))
		kb.cyl(Vector3(-3.1, 0.58, zo), Vector3(-3.1, 0.58, zo + sd * 0.08), 0.3, 0.3, 8, c(B.STEEL[1]))   # sprocket
		kb.cyl(Vector3(3.1, 0.52, zo), Vector3(3.1, 0.52, zo + sd * 0.08), 0.27, 0.27, 8, c(B.STEEL[1]))   # idler
		kb.box(Vector3(-3.5, 0.9, minf(zi, zo + sd * 0.12)), Vector3(7.0, 0.06, 0.72), hull)       # track guard
		var zb := (1.12 if sd > 0.0 else -1.62)
		kb.box(Vector3(-2.7, 0.96, zb), Vector3(1.15, 0.4, 0.5), box)                              # stowage
		kb.box(Vector3(0.25, 0.96, zb), Vector3(0.9, 0.3, 0.5), box)
		kb.box(Vector3(-1.35, 0.97, zb + 0.18), Vector3(1.3, 0.05, 0.1), c(B.STONE[3]))         # pick handle
		kb.box(Vector3(-3.6, 0.95, sd * 0.78 - 0.16), Vector3(0.14, 0.44, 0.32), c(B.PATINA[1]))   # jerry can
		kb.box(Vector3(3.3, 0.95, sd * 0.78 - 0.12), Vector3(0.22, 0.22, 0.24), c(B.NIGHT[2]))    # head light
	_xprism(kb, [Vector2(-3.35, 0.38), Vector2(2.95, 0.38), Vector2(3.5, 0.78), Vector2(2.35, 1.36),
		Vector2(-3.15, 1.42), Vector2(-3.4, 0.95)], -1.02, 1.02, hull)
	kb.box(Vector3(-3.05, 1.42, -0.8), Vector3(1.5, 0.04, 1.6), c(B.NIGHT[3]))                    # louvres
	kb.box(Vector3(-3.5, 0.82, -0.7), Vector3(0.12, 0.42, 1.4), c(B.NIGHT[2]))                    # exhaust grille
	# turret (traversed by gun_yaw about its ring centre)
	var hull_xf := kb.xf
	var hull_xw := kw.xf
	var ring := Transform3D(Basis.IDENTITY, Vector3(-0.35, 0.0, 0.0)) * Transform3D(Basis(Vector3.UP, gun_yaw),
		Vector3.ZERO) * Transform3D(Basis.IDENTITY, Vector3(0.35, 0.0, 0.0))
	kb.xf = hull_xf * ring
	kw.xf = hull_xw * ring
	kb.lathe(Vector3(-0.35, 1.4, 0.0), [Vector2(1.5, 0.0), Vector2(1.44, 0.36), Vector2(1.1, 0.68), Vector2(0.55, 0.78),
		Vector2(0.0, 0.8)], 10, func(_i, j): return c(B.STEEL[3]) if j >= 2 else c(B.STEEL[2]))
	kb.box(Vector3(-2.45, 1.48, -0.85), Vector3(1.1, 0.58, 1.7), hull)                             # bustle
	kb.box(Vector3(-2.65, 2.06, -0.8), Vector3(0.95, 0.2, 1.6), c(B.STEEL[1]))                  # basket
	kb.cyl(Vector3(-2.2, 2.3, -0.78), Vector3(-2.2, 2.3, 0.78), 0.2, 0.2, 6, c(B.STONE[2]))      # tarp roll
	kb.box(Vector3(0.95, 1.55, -0.48), Vector3(0.55, 0.58, 0.96), hull)                            # mantlet
	kb.cyl(Vector3(1.45, 1.86, 0.0), Vector3(5.7, 1.9, 0.0), 0.11, 0.1, 6, c(B.STEEL[1]))         # gun
	kb.cyl(Vector3(3.1, 1.875, 0.0), Vector3(3.8, 1.885, 0.0), 0.17, 0.17, 6, c(B.STEEL[2]))      # fume extractor
	kb.box(Vector3(5.55, 1.74, -0.17), Vector3(0.42, 0.3, 0.34), c(B.NIGHT[3]), Kit.FACES_ALL)  # muzzle brake
	kb.box(Vector3(0.0, 1.62, 0.95), Vector3(0.4, 0.3, 0.3), c(B.STEEL[4]))                     # searchlight
	kb.lathe(Vector3(-0.75, 2.12, 0.45), [Vector2(0.42, 0.0), Vector2(0.4, 0.26), Vector2(0.3, 0.32)], 8,
		func(_i, _j): return c(B.STEEL[2]))                                                        # cupola
	kb.obox(Vector3(-1.18, 2.62, 0.45), Basis(Vector3.BACK, 0.35), Vector3(0.05, 0.34, 0.32), c(B.STEEL[2]))  # lid
	kb.box(Vector3(-0.95, 2.38, 0.25), Vector3(0.4, 0.4, 0.4), c(B.STEEL[1]))                   # commander
	kb.box(Vector3(-0.87, 2.78, 0.33), Vector3(0.24, 0.22, 0.24), c(B.NIGHT[3]))                # padded helmet
	kw.seg(Vector3(-1.9, 2.06, -0.6), Vector3(-2.15, 3.7, -0.6), c(B.NIGHT[1]))
	kb.xf = hull_xf
	kw.xf = hull_xw


## Municipal plough lorry (original design), front = +x: orange-brown cab and bonnet, angled blade on push arms
## with snow banked against it, a steel tipper bed with outside ribs heaped with snow, warning stripes on the
## tailgate, dual rear wheels with mud flaps, amber beacon on a roof bar (its light turns: beacon_energy()).
func plough_into(kb: Kit, kg: Kit, kl: Kit) -> void:
	var body := c(B.OCHRE[2])
	var bd := {"front": body, "side": body.darkened(0.18), "top": body.lightened(0.06)}
	var W := 2.4
	var hw := W * 0.5
	kb.box(Vector3(-3.45, 0.5, -0.5), Vector3(6.9, 0.32, 1.0), c(B.NIGHT[1]), Kit.FACES_ALL)
	_xprism(kb, [Vector2(2.3, 0.82), Vector2(3.45, 0.82), Vector2(3.45, 1.45), Vector2(3.3, 1.62),
		Vector2(2.3, 1.68)], -0.8, 0.8, bd)
	kg.face(Vector3(3.455, 1.13, 0.0), Vector3.RIGHT, Vector3.UP, 0.55, 0.28, c(B.NIGHT[2]))
	_xprism(kb, [Vector2(1.15, 0.82), Vector2(2.35, 0.82), Vector2(2.35, 1.8), Vector2(2.18, 2.66),
		Vector2(1.15, 2.7)], -hw + 0.06, hw - 0.06, bd)
	kg.face(Vector3(2.265, 2.24, 0.0), Vector3(0.985, 0.171, 0.0), Vector3(-0.171, 0.985, 0.0), 0.95, 0.34,
		c(B.STEEL[2]))
	kg.face(Vector3(1.145, 2.2, 0.0), Vector3.LEFT, Vector3.UP, 0.75, 0.26, c(B.STEEL[1]))      # cab back window
	for sd: float in [-1.0, 1.0]:
		kg.face(Vector3(1.8, 2.24, sd * (hw - 0.055)), Vector3(0, 0, sd), Vector3.UP, 0.42, 0.28, c(B.STEEL[1]))
		kb.box(Vector3(1.65, 3.0, sd * 0.85 - 0.04), Vector3(0.08, 0.05, 0.08), c(B.NIGHT[2]))   # mirror arm
	kb.box(Vector3(1.5, 2.7, -0.75), Vector3(0.12, 0.12, 1.5), c(B.NIGHT[2]))                   # roof bar
	kl.box(Vector3(1.42, 2.82, -0.16), Vector3(0.28, 0.28, 0.32), c(B.OCHRE[4]), Kit.FACES_ALL, 1.0)   # beacon
	# blade on push arms, snow banked against it
	for sd: float in [-1.0, 1.0]:
		kb.beam(Vector3(3.4, 0.62, sd * 0.6), Vector3(4.2, 0.58, sd * 0.75), 0.14, 0.14, c(B.NIGHT[2]))
	kb.obox(Vector3(4.3, 0.6, 0.0), Basis(Vector3.UP, 0.45), Vector3(0.1, 0.52, 1.95), {"front": c(B.STEEL[4]),
		"side": c(B.STEEL[3]), "top": c(B.SNOW[4])})
	kb.lathe(Vector3(4.95, 0.0, -0.75), [Vector2(1.0, 0.0), Vector2(0.65, 0.42), Vector2(0.0, 0.58)], 7,
		func(_i, j): return c(B.SNOW[4]) if j > 0 else c(B.SNOW[3]))
	# tipper bed: low steel walls with outside ribs, snow heaped above the rim
	var bed := {"front": c(B.STEEL[2]), "side": c(B.STEEL[1]), "top": c(B.STEEL[3])}
	kb.box(Vector3(-3.45, 0.82, -hw), Vector3(4.45, 0.12, W), c(B.STEEL[1]), Kit.FACES_ALL)
	for sd: float in [-1.0, 1.0]:
		kb.box(Vector3(-3.45, 0.94, (hw - 0.1) if sd > 0.0 else -hw), Vector3(4.45, 0.92, 0.1), bed, Kit.FACES_ALL)
		for xr: float in [-2.9, -1.9, -0.9, 0.1]:
			kb.box(Vector3(xr, 0.94, (hw) if sd > 0.0 else -hw - 0.06), Vector3(0.1, 0.92, 0.06), c(B.STEEL[0]))
		_wheel(kb, Vector3(2.75, 0.48, sd * (hw - 0.2)), 0.48, 0.34, sd, true)
		_wheel(kb, Vector3(-1.55, 0.48, sd * (hw - 0.22)), 0.48, 0.44, sd, true)
		_wheel(kb, Vector3(-2.65, 0.48, sd * (hw - 0.22)), 0.48, 0.44, sd, true)
		kb.face(Vector3(-3.2, 0.42, sd * (hw - 0.22)), Vector3.LEFT, Vector3.UP, 0.22, 0.3, c(B.NIGHT[0]))   # flap
		kl.box(Vector3(-3.56, 0.98, sd * 0.92 - 0.1), Vector3(0.06, 0.14, 0.2), c(B.OCHRE[4]), Kit.FACES_ALL, 0.8)
	kb.box(Vector3(-3.5, 0.94, -hw), Vector3(0.1, 0.92, W), bed, Kit.FACES_ALL)                 # tailgate
	kb.box(Vector3(0.9, 0.94, -hw), Vector3(0.12, 1.05, W), bed, Kit.FACES_ALL)                 # headboard
	for s in 5:                                                                                     # warning stripes
		var zc := -hw + 0.24 + s * 0.48
		kb.face(Vector3(-3.505, 1.17, zc), Vector3.LEFT, Vector3.UP, 0.12, 0.17, c(B.OCHRE[4]) if s % 2 == 0
			else c(B.NIGHT[1]))
	kb.lathe(Vector3(-1.25, 1.75, 0.0), [Vector2(1.15, 0.0), Vector2(0.95, 0.32), Vector2(0.5, 0.55),
		Vector2(0.0, 0.62)], 8, func(_i, j): return c(B.SNOW[4]) if j > 0 else c(B.SNOW[3]))


# ================================================================================================ transport
func _build_motor_pool() -> void:
	# lorries parked herring-bone in three rows (noses angled towards the avenue and the camera), a fuel bowser,
	# gaps where drivers stand
	_ensure_kits(["metal", "glass", "lamp"])
	var tarps := [B.STEEL[2], B.STEEL[3], B.PATINA[1], B.STONE[1], B.PATINA[2]]
	var n := 0
	var ang := deg_to_rad(28.0)
	for row in 3:
		var x := -48.0 - row * 15.0
		var z := -334.0 - row * 1.8
		var k := 0
		while z > -426.0:
			if rng.randf() < 0.88:
				var a := ang + rng.randf_range(-0.04, 0.04)
				_at(Vector3(x + rng.randf_range(-0.3, 0.3), 0.0, z), Vector3(cos(a), 0.0, sin(a)))
				var cargo := 2 if (row == 0 and k == 5) else (1 if rng.randf() < 0.12 else 0)
				lorry_into(K("metal"), K("glass"), K("lamp"), c(B.STEEL[2]),
					c(tarps[rng.randi_range(0, tarps.size() - 1)]), rng.randf() < 0.3, cargo, row == 0)
				n += 1
			z -= 4.6
			k += 1
	# two flood lamps on poles over the pool
	_world()
	for p: Vector3 in [Vector3(-38.0, 0, -350.0), Vector3(-38.0, 0, -405.0)]:
		K("metal").pillar(p.x, p.z, 0.0, 0.3, 0.3, 11.0, {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2])})
		K("lamp").box(Vector3(p.x - 0.9, 10.6, p.z - 0.3), Vector3(1.8, 0.6, 0.6), c(B.SNOW[4]), Kit.FACES_ALL, 1.0)
	stats["lorries_parked"] = n
	_world()


func _build_buses() -> void:
	_ensure_kits(["metal", "glass", "lamp"])
	var bodies := [B.PATINA[1], B.STEEL[2], B.OCHRE[1], B.VIOLET[2]]
	var n := 0
	# the buses that brought the crowd: two rows, noses to the avenue (left of the motor pool)
	for row in 2:
		var z := -468.0 - row * 17.0
		var x := -44.0
		while x > -134.0:
			if rng.randf() < 0.9:
				_at(Vector3(x, 0.0, z), Vector3(0, 0, 1))
				bus_into(K("metal"), K("glass"), K("lamp"), c(bodies[rng.randi_range(0, bodies.size() - 1)]),
					c(B.SNOW[1]), rng.randf() < 0.3)
				n += 1
			x -= 3.9
	stats["buses"] = n
	_world()


# ================================================================================================ work
func _build_stand() -> void:
	# a stepped spectator stand (far left of the avenue): the left part planked and already packed with guests
	# (_build_static_figures), the right part still a bare frame, two work-light towers and a crane lifting the
	# next section
	_world()
	var m := K("metal")
	var lamp := K("lamp")
	var post := {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2]), "top": c(B.SNOW[3])}
	var x0 := -186.0
	var x1 := -96.0
	var xm := x0 + (x1 - x0) * 0.68
	var zf := -566.0
	for tier in 5:
		var zt := zf - tier * 3.2
		var yt := 1.2 + tier * 2.6
		m.box(Vector3(x0, 0.0, zt - 3.2), Vector3(xm - x0, yt + 0.35, 3.2), {"front": c(B.STONE[2]),
			"side": c(B.STONE[1]), "top": c(B.SNOW[3])})
		m.box(Vector3(x0, yt + 0.35, zt - 0.3), Vector3(xm - x0, 0.16, 0.3), c(B.STONE[3]))       # bench edge
		m.box(Vector3(xm, yt, zt - 0.3), Vector3(x1 - xm, 0.3, 0.3), c(B.STEEL[2]))               # bare beam
		var x := xm
		while x <= x1 + 0.1:
			m.pillar(x, zt, 0.0, 0.3, 0.3, yt + 0.3, post)
			x += 4.0
	# back wall (boarded), higher in the middle where the officials will stand
	var zb := zf - 5 * 3.2 - 0.6
	m.box(Vector3(x0, 0.0, zb), Vector3(x1 - x0, 15.0, 0.6), {"front": c(B.STONE[1]), "side": c(B.STONE[0]),
		"top": c(B.SNOW[3])})
	m.box(Vector3(x0 + 30.0, 15.0, zb), Vector3(26.0, 4.0, 0.6), {"front": c(B.STONE[1]), "top": c(B.SNOW[3])})
	var y := 3.0
	while y < 15.0:
		m.box(Vector3(x0, y, zb + 0.6), Vector3(x1 - x0, 0.25, 0.05), c(B.STONE[3]), Kit.FACE_PZ)
		y += 3.0
	for p: float in [x0 - 6.0, x1 + 5.0]:
		m.pillar(p, zf - 4.0, 0.0, 0.5, 0.5, 20.0, post)
		lamp.box(Vector3(p - 1.4, 20.0, zf - 4.2), Vector3(2.8, 1.0, 0.6), c(B.SNOW[4]), Kit.FACES_ALL, 1.0)
	# a crane lifting the next section
	m.pillar(x1 + 14.0, zf - 20.0, 0.0, 1.6, 1.6, 34.0, post)
	m.box(Vector3(x1 - 14.0, 34.0, zf - 20.8), Vector3(36.0, 1.1, 1.6), post)
	K("wires", Mesh.PRIMITIVE_LINES).seg(Vector3(x1 + 2.0, 34.0, zf - 20.0), Vector3(x1 + 2.0, 19.0, zf - 20.0),
		c(B.NIGHT[1]))
	m.box(Vector3(x1 - 2.0, 17.0, zf - 21.0), Vector3(8.0, 2.0, 2.0), {"front": c(B.STONE[2]), "top": c(B.SNOW[4])})
	lamp.box(Vector3(x1 - 14.6, 34.6, zf - 20.6), Vector3(1.2, 1.2, 1.2), c(B.OCHRE[4]), Kit.FACES_ALL, 1.0)


## The dark city blocks left of the plaza (hall_builder._build_far_city, same RNG sequence) get scaffolding on
## their avenue face, work lamps and a few lit windows: the city is still being rebuilt for the regime.
func _build_far_scaffolds() -> void:
	_world()
	var m := K("metal")
	var lamp := K("lamp")
	var r := RandomNumberGenerator.new()
	r.seed = 77                      # replays the builder's sequence: exactly 5 draws per block, nothing else
	var rw := RandomNumberGenerator.new()
	rw.seed = 7701
	var n := 0
	for i in 26:
		var side := -1.0 if i % 2 == 0 else 1.0
		var x := HX + side * r.randf_range(260.0, 900.0)
		var z := r.randf_range(-300.0, -1500.0)
		var w := r.randf_range(40.0, 120.0)
		var d := r.randf_range(30.0, 80.0)
		var h := r.randf_range(18.0, 36.0)
		if side > 0.0 or z + d * 0.5 < -1000.0:
			continue
		var zf := z + d * 0.5 + 0.8
		var xa := x - w * 0.5
		var xb := x + w * 0.5
		# scaffold over the left 60 % of the face: standards every 6 m, boarded lifts every 4 m
		var xs := xa + 2.0
		var xe := xa + w * 0.6
		var xx := xs
		while xx <= xe:
			m.box(Vector3(xx - 0.35, 0.0, zf), Vector3(0.7, h + 2.0, 0.7), {"front": c(B.STEEL[1]),
				"side": c(B.STEEL[0])})
			xx += 6.0
		var yy := 4.0
		while yy < h + 1.0:
			m.box(Vector3(xs - 0.5, yy, zf - 0.2), Vector3(xe - xs + 1.0, 0.9, 1.4), {"front": c(B.STONE[2]),
				"side": c(B.STONE[1]), "top": c(B.SNOW[4])})
			yy += 4.0
		# work lamps on the scaffold, a few lit windows in the finished part
		for k in 2:
			var lx := lerpf(xs, xe, 0.25 + 0.5 * k)
			lamp.box(Vector3(lx - 0.8, h - 2.0 - k * 6.0, zf + 0.7), Vector3(1.6, 1.2, 0.4), c(B.SNOW[4]),
				Kit.FACES_ALL, 1.0)
		for k in 6:
			var wx := rw.randf_range(xe + 3.0, xb - 3.0)
			var wy := 4.0 + 4.0 * rw.randi_range(0, int(h / 4.0) - 2)
			lamp.box(Vector3(wx - 1.0, wy, zf - 0.75), Vector3(2.0, 1.6, 0.1), c(B.GLOW[rw.randi_range(0, 2)]),
				Kit.FACE_PZ, 0.8)
		n += 1
	stats["far_scaffolds"] = n


## Windrow of swept snow along x = `x`, from z0 towards -z: a continuous ridge with slowly varying height and
## width (smooth slopes: no glitter of small facets in the light pools), broken where the gang is digging.
func _windrow(g: Kit, x: float, z0: float, z1: float, rs: RandomNumberGenerator, open_at: Array) -> void:
	var z := z0
	var h := 0.6
	var w := 1.1
	var xo := 0.0
	var open := true
	while z > z1:
		var seg := rs.randf_range(2.5, 4.0)
		var zb := z - seg
		var h2 := clampf(h + rs.randf_range(-0.15, 0.15), 0.4, 0.9)
		var w2 := clampf(w + rs.randf_range(-0.15, 0.15), 0.8, 1.4)
		var xo2 := clampf(xo + rs.randf_range(-0.2, 0.2), -0.4, 0.4)
		var gap := false
		for oz in open_at:
			if absf(z - float(oz)) < 2.5:
				gap = true
		if not gap:
			var a0 := Vector3(x + xo - w, 0.0, z)
			var a1 := Vector3(x + xo2 - w2, 0.0, zb)
			var r0 := Vector3(x + xo - 0.25, h, z)
			var r1 := Vector3(x + xo2 - 0.25, h2, zb)
			var s0 := Vector3(x + xo + 0.25, h, z)
			var s1 := Vector3(x + xo2 + 0.25, h2, zb)
			var b0 := Vector3(x + xo + w, 0.0, z)
			var b1 := Vector3(x + xo2 + w2, 0.0, zb)
			g.quad_out(a0, r0, r1, a1, c(B.SNOW[2]), Vector3(-1, 1, 0))
			g.quad_out(r0, s0, s1, r1, c(B.SNOW[3]), Vector3.UP)
			g.quad_out(s0, b0, b1, s1, c(B.SNOW[1]), Vector3(1, 1, 0))
			if open:                                   # end face towards the camera after a gap
				g.quad_out(a0, r0, s0, b0, c(B.SNOW[2]), Vector3.BACK)
		open = gap
		z = zb
		h = h2
		w = w2
		xo = xo2


func _build_snow_work() -> void:
	# swept snow in two windrows along the cleared lane (nearest to the camera) + a lorry being loaded
	_world()
	var g := K("ground")
	var rs := RandomNumberGenerator.new()
	rs.seed = 6060
	_windrow(g, 2.6, Z_NEAR - 1.0, -236.0, rs, [-149.0, -181.0, -205.0])
	_windrow(g, 22.2, Z_NEAR - 1.0, -236.0, rs, [-146.5, -170.0, -188.0, -215.0])
	# trampled slush between them: irregular patches along the wheel tracks of the plough
	for lane: float in [8.8, 15.2]:
		var z2 := Z_NEAR
		var wob := 0.0
		while z2 > -232.0:
			var seg := rs.randf_range(1.5, 4.0)
			var wob2 := clampf(wob + rs.randf_range(-0.25, 0.25), -0.6, 0.6)
			var ww := rs.randf_range(0.7, 1.3)
			var tone: String = B.SNOW[1] if rs.randf() < 0.6 else B.SNOW[0]
			g.quad(Vector3(lane + wob, 0.014, z2), Vector3(lane + wob2, 0.014, z2 - seg),
				Vector3(lane + wob2 + ww, 0.014, z2 - seg), Vector3(lane + wob + ww, 0.014, z2), c(tone))
			wob = wob2
			z2 -= seg
	# barrier sections stacked by the right cordon, two lorries unloading them; spare sections at the left gate
	_ensure_kits(["metal", "glass", "lamp"])
	for i in 2:
		_at(Vector3(82.0 + i * 1.5, 0.0, -232.0 - i * 11.0), Vector3(1, 0, -0.15))
		lorry_into(K("metal"), K("glass"), K("lamp"), c(B.STEEL[2]), c(B.STEEL[3]), false, 1)
	_world()
	var m := K("metal")
	for s in 4:
		m.box(Vector3(76.0 + s * 3.0, 0.0, -226.0 - s * 0.4), Vector3(2.5, 0.6 + 0.12 * s, 1.2), {"front": c(B.STEEL[3]),
			"side": c(B.STEEL[2]), "top": c(B.SNOW[3])})
	for s in 3:
		m.box(Vector3(1.0 + s * 0.2, 0.0, -344.0 - s * 1.6), Vector3(1.3, 0.5 + 0.1 * s, 2.4), {"front": c(B.STEEL[3]),
			"side": c(B.STEEL[2]), "top": c(B.SNOW[3])})


## Where the honour lane begins: two sentry boxes, the officers' cars parked in a row (drivers stamping their
## feet beside them), a lorry with a cable drum and the crew laying the loudspeaker cable along the lane.
func _build_lane_start() -> void:
	_world()
	var m := K("metal")
	for x: float in [HX - 10.6, HX + 10.6]:
		var z := HONOUR_FROM + 14.0
		m.box(Vector3(x - 0.65, 0.0, z - 0.65), Vector3(1.3, 2.4, 1.3), {"front": c(B.STONE[1]), "side": c(B.STONE[0]),
			"top": c(B.SNOW[3])})
		m.face(Vector3(x, 1.2, z + 0.655), Vector3.BACK, Vector3.UP, 0.42, 0.95, c(B.NIGHT[1]))     # open front
		m.prism([Vector2(-0.85, 2.4), Vector2(0.85, 2.4), Vector2(0.0, 3.05)], Vector3(x, 0.0, z), Vector3.RIGHT,
			Vector3.UP, Vector3.BACK, -0.85, 0.85, {"front": c(B.STONE[0]), "side": c(B.SNOW[3]), "top": c(B.SNOW[3])})
	_ensure_kits(["metal", "glass", "lamp"])
	for k in staff_parking().size():
		var p: Vector3 = staff_parking()[k]
		_at(p, Vector3(0.0, 0.0, -1.0))
		builder.car_into(K("metal"), K("glass"), K("lamp"), K("lamp"), c(B.NIGHT[1]), 4.8, k == 0)
	_at(Vector3(30.5, 0.0, -150.0), Vector3(0.0, 0.0, -1.0))
	lorry_into(K("metal"), K("glass"), K("lamp"), c(B.STEEL[2]), c(B.STEEL[3]), false, 3)
	_world()


static func staff_parking() -> Array:
	return [Vector3(31.0, 0.0, -206.0), Vector3(31.2, 0.0, -213.5), Vector3(30.9, 0.0, -221.0)]


func _build_vents() -> void:
	_world()
	var g := K("ground")
	for p: Vector3 in _vent_spots():
		g.quad(Vector3(p.x - 0.7, 0.02, p.z + 0.7), Vector3(p.x - 0.7, 0.02, p.z - 0.7),
			Vector3(p.x + 0.7, 0.02, p.z - 0.7), Vector3(p.x + 0.7, 0.02, p.z + 0.7), c(B.NIGHT[2]))


## The delegations' banners on the right side plaza (one per block, flag_street: Symbols-resolved), the poles
## held by the bearer in front of each block (_build_static_figures stages the people).
func _build_delegation_banners() -> void:
	_world()
	var m := K("metal")
	var fl := K("flag_street")
	var zd := DELEG_FROM
	while zd >= DELEG_TO:
		for bx: float in DELEG_COLS:
			if bx - 6.0 > deleg_reach(zd):
				continue
			var x := bx + 0.55
			var z := zd - 1.45
			m.box(Vector3(x - 0.045, 0.9, z - 0.045), Vector3(0.09, 4.0, 0.09), c(B.NIGHT[3]))
			m.box(Vector3(x - 0.8, 4.82, z - 0.04), Vector3(1.6, 0.07, 0.07), c(B.NIGHT[3]))
			fl.quad(Vector3(x - 0.74, 2.6, z + 0.06), Vector3(x - 0.74, 4.8, z + 0.06), Vector3(x + 0.74, 4.8, z + 0.06),
				Vector3(x + 0.74, 2.6, z + 0.06), Color.WHITE, 0.5)
		zd -= 30.0


## The crowds' marshals' lanes (lit snow under lamps on short posts), the cross-gaps (lit; a first-aid tent or a
## loudspeaker mast in each) and the delegations' banners (two per block, plain cloth with a lettered band: no
## insignia).  From p8's roof the lanes are pale lines converging on the hall, splitting each crowd into strips.
func _build_crowd_lanes() -> void:
	_world()
	var g := K("ground")
	var m := K("metal")
	var lamp := K("lamp")
	var cl := K("cloth")
	var post := {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2]), "top": c(B.SNOW[3])}
	var n_lamps := 0
	var n_banners := 0
	for side: float in [-1.0, 1.0]:
		var xb: float = X_BARRIER_L if side < 0.0 else X_BARRIER_R
		var lanes: Array = LANES[int(side)]
		for k in lanes.size():
			var l: Array = lanes[k]
			var xa: float = minf(xb + side * float(l[0]), xb + side * float(l[1]))
			var xe: float = maxf(xb + side * float(l[0]), xb + side * float(l[1]))
			var z0: float = float(l[2]) - 6.0                      # the first lamp
			var z := float(l[2])
			while z > Z_FAR + 2.0:
				if lane_active(side, k, z) and lane_active(side, k, z - 2.0):
					# lit snow, brightest under the lamps, dim halfway between them
					var u := fposmod(z0 - (z - 1.0), LANE_LAMP_STEP)
					var dl := minf(u, LANE_LAMP_STEP - u)
					var em := lerpf(1.0, 0.42, clampf(dl / 5.0, 0.0, 1.0))
					g.quad(Vector3(xa, 0.016, z), Vector3(xa, 0.016, z - 2.0), Vector3(xe, 0.016, z - 2.0),
						Vector3(xe, 0.016, z), c(B.SNOW[3]), em)
				z -= 2.0
			var zl := z0
			while zl > Z_FAR + 4.0:
				if lane_active(side, k, zl) and not cross_gap(side, zl, 1.0):
					var xp: float = xb + side * (float(l[0]) + 0.2)
					m.pillar(xp, zl, 0.0, 0.1, 0.1, 3.0, post)
					lamp.box(Vector3(xp - 0.17, 3.0, zl - 0.17), Vector3(0.34, 0.3, 0.34), c(B.SNOW[4]),
						Kit.FACES_ALL, 1.0)
					n_lamps += 1
				zl -= LANE_LAMP_STEP
		for cg: Array in CROSS[int(side)]:
			var zc: float = cg[0]
			var hw: float = cg[1]
			var dep := crowd_depth(side, zc)
			var xa2: float = minf(xb + side * 0.4, xb + side * (dep + 1.0))
			var xe2: float = maxf(xb + side * 0.4, xb + side * (dep + 1.0))
			g.quad(Vector3(xa2, 0.016, zc + hw), Vector3(xa2, 0.016, zc - hw), Vector3(xe2, 0.016, zc - hw),
				Vector3(xe2, 0.016, zc + hw), c(B.SNOW[2]), 0.45)
			match str(cg[2]):
				"aid":
					_aid_tent(m, lamp, Vector3(xb + side * (dep - 1.6), 0.0, zc), side)
				"mast":
					_speaker_mast(m, lamp, Vector3(xb + side * (dep * 0.5), 0.0, zc))
		# the delegations' banners: two cloths on pole pairs over the front rank of each block, facing the street
		var last: int = lanes.size() - 1
		var mid0: float = float((lanes[0] as Array)[1]) if last > 0 else float((lanes[0] as Array)[1])
		var mid1: float = float((lanes[last] as Array)[0]) if last > 0 else mid0 + 7.0
		for gr: Array in crowd_groups(side):
			var grp := int(gr[2])
			var zb: float = float(gr[0]) - 0.9
			if grp <= 0 or not lane_active(side, last, zb) or cross_gap(side, zb, 1.0):
				continue
			var cols: Array = GROUP_CLOTH[grp]
			for f: float in [0.27, 0.73]:
				var xc: float = xb + side * lerpf(mid0, mid1, f)
				_banner_cloth(m, cl, Vector3(xc, 0.0, zb), c(str(cols[0])), c(str(cols[1])))
				n_banners += 1
	stats["lane_lamps"] = n_lamps
	stats["crowd_banners"] = n_banners


## A plain banner over a delegation: two poles, a 2.6 x 1.0 m cloth between them (facing +z, towards the street and
## the roofs) with a darker lettered band across it (unreadable at any distance), snow on the top hem; the lane
## lamps beside the block light it.
func _banner_cloth(m: Kit, cl: Kit, p: Vector3, cloth: Color, band: Color) -> void:
	for sx: float in [-1.3, 1.3]:
		m.box(Vector3(p.x + sx - 0.035, 0.9, p.z - 0.035), Vector3(0.07, 2.85, 0.07), c(B.NIGHT[3]))
	var z1 := p.z + 0.04
	cl.quad(Vector3(p.x - 1.26, 2.5, z1), Vector3(p.x - 1.26, 3.5, z1), Vector3(p.x + 1.26, 3.5, z1),
		Vector3(p.x + 1.26, 2.5, z1), cloth, 0.45)
	cl.quad(Vector3(p.x - 1.0, 2.9, z1 + 0.01), Vector3(p.x - 1.0, 3.08, z1 + 0.01), Vector3(p.x + 1.0, 3.08, z1 + 0.01),
		Vector3(p.x + 1.0, 2.9, z1 + 0.01), band, 0.2)
	cl.quad(Vector3(p.x - 1.26, 3.5, z1), Vector3(p.x - 1.26, 3.5, p.z - 0.06), Vector3(p.x + 1.26, 3.5, p.z - 0.06),
		Vector3(p.x + 1.26, 3.5, z1), c(B.SNOW[4]), 0.45)


## First-aid post at the back of a cross-gap: a ridge tent of pale canvas (its door towards the avenue) under a
## lamp on a pole, a stretcher leaning against it.
func _aid_tent(m: Kit, lamp: Kit, p: Vector3, side: float) -> void:
	var canvas := {"front": c(B.SNOW[1]), "side": c(B.SNOW[2]), "top": c(B.SNOW[3])}
	m.prism([Vector2(-1.3, 0.0), Vector2(1.3, 0.0), Vector2(1.3, 1.1), Vector2(0.0, 2.3), Vector2(-1.3, 1.1)],
		p, Vector3.BACK, Vector3.UP, Vector3.RIGHT, -1.6, 1.6, canvas)
	m.face(p + Vector3(-side * 1.605, 0.75, 0.0), Vector3(-side, 0.0, 0.0), Vector3.UP, 0.45, 0.75, c(B.NIGHT[1]))
	m.pillar(p.x - side * 2.2, p.z + 1.6, 0.0, 0.09, 0.09, 3.4, {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2])})
	lamp.box(Vector3(p.x - side * 2.2 - 0.16, 3.25, p.z + 1.44), Vector3(0.32, 0.3, 0.32), c(B.SNOW[4]), Kit.FACES_ALL,
		1.0)
	m.box(Vector3(p.x - side * 1.75 - 0.3, 0.0, p.z - 1.2), Vector3(0.6, 1.9, 0.08), {"front": c(B.STONE[3]),
		"side": c(B.STONE[2])})


## Loudspeaker mast in a cross-gap: a lattice-dark pole, a cross-arm with four horns towards the avenue and the
## plaza, a lamp under them.
func _speaker_mast(m: Kit, lamp: Kit, p: Vector3) -> void:
	m.pillar(p.x, p.z, 0.0, 0.26, 0.26, 8.4, {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2]), "top": c(B.SNOW[3])})
	m.box(Vector3(p.x - 1.1, 8.1, p.z - 0.08), Vector3(2.2, 0.14, 0.16), c(B.NIGHT[2]))
	for sx: float in [-0.85, 0.85]:
		for sz: float in [-1.0, 1.0]:
			m.box(Vector3(p.x + sx - 0.2, 7.6, p.z + (0.05 if sz > 0.0 else -0.55)), Vector3(0.4, 0.42, 0.5),
				{"front": c(B.STEEL[2]), "side": c(B.STEEL[1]), "top": c(B.SNOW[3])})
	lamp.box(Vector3(p.x - 0.2, 6.9, p.z - 0.2), Vector3(0.4, 0.34, 0.4), c(B.SNOW[4]), Kit.FACES_ALL, 1.0)


## The right side's grandstands, finished and packed: right behind the marshals' lane (the front strip of the crowd
## stands below them at the barrier), six tiers rising away from the avenue in five sections between the cross-gaps,
## a stone parapet, lamps along the back wall, banner masts in the lane (flag_street, Symbols-resolved, facing the
## street).  Seen from p8's roof they are a bank of people rising over the right crowd; parade_set fills the tiers
## with the crowd's figures (delegations in blocks, stand_tier / in_stand).
const STAND_X := X_BARRIER_R + 10.0  ## front edge (lowest tier) of the right grandstands
const STAND_TIERS := 6
const STAND_STEP := Vector2(1.9, 0.95)   ## tier depth (x) and rise (y)
const STAND_SECTIONS := [[-372.0, -436.0], [-448.0, -512.0], [-524.0, -588.0], [-600.0, -664.0], [-676.0, -736.0]]


## Fire bowls on the grandstands' parapet (feet of the flame), every 8 m: the right edge's line of fire.
static func stand_fires() -> Array:
	var out: Array = []
	for sec: Array in STAND_SECTIONS:
		var z: float = float(sec[0]) - 4.0
		while z > float(sec[1]) + 2.0:
			out.append(Vector3(STAND_X - 0.25, 1.62, z))
			z -= 8.0
	return out


## Is z within one of the right grandstand's sections (widened by `pad`)?
static func in_stand(z: float, pad: float = 0.0) -> bool:
	for sec: Array in STAND_SECTIONS:
		if z <= float(sec[0]) + pad and z >= float(sec[1]) - pad:
			return true
	return false


static func stand_tier(i: int) -> Vector3:
	## (x front edge, y top, x back edge) of tier i
	return Vector3(STAND_X + i * STAND_STEP.x, 0.6 + i * STAND_STEP.y, STAND_X + (i + 1) * STAND_STEP.x)


func _build_grandstand() -> void:
	_world()
	var m := K("metal")
	var lamp := K("lamp")
	var fl := K("flag_street")
	var stone := {"front": c(B.STONE[2]), "side": c(B.STONE[1]), "top": c(B.SNOW[3])}
	var riser := {"front": c(B.STONE[1]), "side": c(B.STONE[0]), "top": c(B.SNOW[2])}
	var xback: float = stand_tier(STAND_TIERS - 1).z
	for sec: Array in STAND_SECTIONS:
		var za: float = sec[0]
		var zb: float = sec[1]
		for i in STAND_TIERS:
			var t := stand_tier(i)
			m.box(Vector3(t.x, 0.0, zb), Vector3(t.z - t.x, t.y, za - zb), riser if i % 2 == 0 else stone)
		# parapet in front, back wall, end walls
		m.box(Vector3(STAND_X - 0.5, 0.0, zb), Vector3(0.5, 1.15, za - zb), {"front": c(B.STONE[3]), "side": c(B.STONE[2]),
			"top": c(B.SNOW[4])})
		var yb: float = stand_tier(STAND_TIERS - 1).y
		m.box(Vector3(xback, 0.0, zb), Vector3(0.6, yb + 2.6, za - zb), {"front": c(B.STONE[1]), "side": c(B.STONE[0]),
			"top": c(B.SNOW[3])})
		for ze: float in [za, zb - 0.6]:
			m.prism([Vector2(STAND_X - 0.5, 0.0), Vector2(xback + 0.6, 0.0), Vector2(xback + 0.6, yb + 2.6),
				Vector2(STAND_X - 0.5, 1.6)], Vector3.ZERO, Vector3.RIGHT, Vector3.UP, Vector3.BACK, ze, ze + 0.6, stone)
		# fire bowls on the parapet (_build_flames lights them)
		for f: Vector3 in stand_fires():
			if f.z <= za and f.z >= zb:
				m.cyl(Vector3(f.x, 1.15, f.z), Vector3(f.x, 1.3, f.z), 0.16, 0.12, 6, c(B.OCHRE[1]))
				m.lathe(Vector3(f.x, 1.3, f.z), [Vector2(0.1, 0.0), Vector2(0.42, 0.14), Vector2(0.48, 0.3),
					Vector2(0.42, 0.32)], 8, func(_i, j): return c(B.OCHRE[0]) if j < 2 else c(B.OCHRE[3]))
				lamp.box(Vector3(f.x - 0.3, 1.55, f.z - 0.3), Vector3(0.6, 0.06, 0.6), c(B.OCHRE[4]), Kit.FACES_ALL, 1.0)
		# lamps on the back wall
		var zw := za - 3.0
		while zw > zb + 1.0:
			m.box(Vector3(xback + 0.1, yb + 2.6, zw - 0.06), Vector3(0.12, 1.6, 0.12), c(B.NIGHT[2]))
			lamp.box(Vector3(xback - 0.15, yb + 4.1, zw - 0.25), Vector3(0.5, 0.36, 0.5), c(B.SNOW[4]), Kit.FACES_ALL, 1.0)
			zw -= 8.0
	# banner masts in the lane before the stands: the cloth hangs from a cross-bar, facing the street (and the roofs)
	var zm := -381.0
	var nm := 0
	while zm > -736.0:
		var xm := STAND_X - 1.5
		m.pillar(xm, zm, 0.0, 0.32, 0.32, 13.0, {"front": c(B.NIGHT[3]), "side": c(B.NIGHT[2]), "top": c(B.SNOW[3])})
		m.box(Vector3(xm - 1.1, 12.5, zm - 0.07), Vector3(2.2, 0.14, 0.14), c(B.NIGHT[2]))
		fl.quad(Vector3(xm - 0.95, 7.7, zm + 0.12), Vector3(xm - 0.95, 12.4, zm + 0.12), Vector3(xm + 0.95, 12.4, zm + 0.12),
			Vector3(xm + 0.95, 7.7, zm + 0.12), Color.WHITE, 0.4)
		zm -= 38.0
		nm += 1
	stats["grandstand_sections"] = STAND_SECTIONS.size()
	stats["grandstand_masts"] = nm


## Steaming manholes: only in the cleared stretch (further up the formations stand on them).
func _vent_spots() -> Array:
	return [Vector3(26.0, 0, -176.0), Vector3(41.0, 0, -188.0), Vector3(64.0, 0, -236.0), Vector3(8.0, 0, -226.0)]


# ================================================================================================ figures
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
		buf[o + 15] = 1.0 if bool(p[4]) else 0.0
		i += 1
	mm.buffer = buf
	var mi := MultiMeshInstance3D.new()
	mi.name = node_name
	mi.multimesh = mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if points.size() > 0:
		mi.custom_aabb = AABB(lo - Vector3(4, 1, 4), hi - lo + Vector3(8, 8, 8))
	parent.add_child(mi)
	stats[node_name] = points.size()
	placed[node_name] = points
	return mi


func _pt(pos: Vector3, slot_name: String, variant_i: int = -1, animated := false, flip := false) -> Array:
	var s := _slot(slot_name)
	var n := int(s[1])
	if animated:
		return [pos, int(s[0]), n, rng.randf_range(0.0, 8.0), flip]
	var v := variant_i if variant_i >= 0 else rng.randi_range(0, n - 1)
	return [pos, int(s[0]) + clampi(v, 0, n - 1), 1, 0.0, flip]


## A block of infantry: `cols` x `rows`, front row at z0 (rows extend towards -z), centred on x.
func _block_points(pts: Array, x: float, z0: float, cols: int, rows: int, slot_name: String, animated: bool,
		dx: float = 1.45, dz: float = 1.5) -> void:
	for r in rows:
		for k in cols:
			var px := x + (k - (cols - 1) * 0.5) * dx + rng.randf_range(-0.04, 0.04)
			var pz := z0 - r * dz + rng.randf_range(-0.04, 0.04)
			if animated:
				# the whole block steps in time: one phase per block, a few men out of step
				var ph := 0.0 if rng.randf() < 0.9 else 2.0
				var s := _slot(slot_name)
				pts.append([Vector3(px, 0.0, pz), int(s[0]), int(s[1]), ph, false])
			else:
				pts.append(_pt(Vector3(px, 0.0, pz), slot_name, rng.randi_range(0, 1) if rng.randf() < 0.85 else 2))


func _build_static_figures() -> void:
	var pts: Array = []
	# cordon guards, facing the people outside (left line faces -x, right line +x), one every GUARD_STEP
	for side: float in [-1.0, 1.0]:
		var x: float = X_GUARD_L if side < 0.0 else X_GUARD_R
		var z := Z_NEAR - 4.0
		while z > Z_FAR:
			if not _is_gate(side, z):
				pts.append(_pt(Vector3(x + rng.randf_range(-0.1, 0.1), 0.0, z), "guard_side",
					0 if rng.randf() < 0.75 else 1, false, side < 0.0))
			z -= GUARD_STEP
	# honour files lining the column's lane, facing each other across it
	for side: float in [-1.0, 1.0]:
		var z := HONOUR_FROM - (HONOUR_STEP * 0.5 if side > 0.0 else 0.0)
		while z > HONOUR_TO:
			pts.append(_pt(Vector3(HX + side * HONOUR_X, 0.0, z), "honour", 0, false, side > 0.0))
			z -= HONOUR_STEP
	# halted blocks formed up and waiting (they face the plaza): a double file of blocks down the right lane, two
	# more in the left lane before the plaza; front rank most -z, the officer two paces before it
	var nb := 0
	for col: Array in HALT_COLS:
		var bx: float = col[0]
		var zf: float = col[1]
		while zf - 2.4 >= Z_FAR:
			_block_points(pts, bx, zf + (HALT_RANKS - 1) * 1.5, HALT_FILES, HALT_RANKS, "stand_back", false, 1.45,
				1.5)
			pts.append(_pt(Vector3(bx + rng.randf_range(-0.4, 0.4), 0.0, zf - 2.4), "officer", 0))
			zf -= HALT_PITCH
			nb += 1
	stats["halted_blocks"] = nb
	# delegations formed up in blocks on the right side plaza beyond the buses (works brigades, leagues, schools:
	# civilians in rows, a banner before each block) -- only where p8's last frame can see them
	var cb0 := _slot("civ_back")
	var nd := 0
	var zd := DELEG_FROM
	while zd >= DELEG_TO:
		for bx: float in DELEG_COLS:
			if bx - 6.0 > deleg_reach(zd):
				continue
			for rr in 10:
				for i in 13:
					if rng.randf() < 0.94:
						pts.append([Vector3(bx + (i - 6) * 0.98 + rng.randf_range(-0.08, 0.08), 0.0,
							zd + rr * 1.05 + rng.randf_range(-0.08, 0.08)), int(cb0[0]) + rng.randi_range(0,
							int(cb0[1]) - 1), 1, 0.0, rng.randf() < 0.5])
			pts.append(_pt(Vector3(bx + 0.4, 0.0, zd - 1.4), "civ_back", 0))       # the banner bearer
			nd += 1
		zd -= 30.0
	stats["delegations"] = nd
	# snow-clearing gang (shovels animated, each on its own beat) and the foreman: everyone faces his windrow
	# (left lane x < 12 throws to the left, right lane to the right) or the tipper
	var sh := _slot("shovel")
	for p: Vector3 in gang_spots():
		var face_left := p.x < 12.0 or p.x > 28.4
		pts.append([p, int(sh[0]), int(sh[1]), rng.randf_range(0.0, 4.0), face_left])
	pts.append(_pt(Vector3(12.5, 0.0, -141.0), "officer", 1, false, true))
	# barrier crews: at the right cordon carrying sections from the lorries, at the left gate closing it
	for i in 6:
		pts.append(_pt(Vector3(77.0 + i * 2.3, 0.0, -238.0 + rng.randf_range(-1.5, 1.5)), "carry", 0 if i % 3 else 1,
			false, i % 2 == 0))
	for i in 4:
		pts.append(_pt(Vector3(0.5 + i * 1.6, 0.0, -339.5 - i * 0.9), "carry", 0, false, true))
	# the sentries at the boxes, the drivers by the parked cars, the cable crew walking up the lane with coils
	for x: float in [HX - 10.6, HX + 10.6]:
		pts.append(_pt(Vector3(x + (1.1 if x < HX else -1.1), 0.0, HONOUR_FROM + 14.6), "guard_side", 0, false, x > HX))
	for p: Vector3 in staff_parking():
		pts.append(_pt(p + Vector3(-1.5, 0.0, 0.6), "guard_side", 1, false, rng.randf() < 0.5))
		if rng.randf() < 0.6:
			pts.append(_pt(p + Vector3(-1.9, 0.0, -0.4), "officer", 1, false, true))
	for i in 5:
		pts.append(_pt(Vector3(31.4 + (i % 2) * 0.6, 0.0, -157.0 - i * 3.8), "carry", 1, false, false))
	# officers and an adjutant by the staff cars, traffic police at the gates
	for p: Vector3 in [Vector3(27.0, 0, -252.0), Vector3(28.1, 0, -252.6), Vector3(26.4, 0, -253.4)]:
		pts.append(_pt(p, "officer", 1, false, rng.randf() < 0.5))
	pts.append([Vector3(-2.0, 0.0, -331.0), int(_slot("police")[0]), 2, 0.0, false])
	pts.append([Vector3(-2.2, 0.0, -455.0), int(_slot("police")[0]), 2, 1.0, true])
	pts.append([Vector3(91.0, 0.0, -290.0), int(_slot("police")[0]), 2, 0.5, true])
	# the stand's finished part packed with guests: two rows on every tier (the bare frame stays empty)
	var cb := _slot("civ_back")
	for tier in 5:
		var zt := -566.0 - tier * 3.2
		var yt := 1.2 + tier * 2.6 + 0.35
		for zr: float in [zt - 0.9, zt - 2.2]:
			var x := -185.2 + rng.randf_range(0.0, 0.3)
			while x < -125.8:
				if rng.randf() < 0.88:
					pts.append([Vector3(x, yt, zr + rng.randf_range(-0.12, 0.12)), int(cb[0]) + rng.randi_range(0,
						int(cb[1]) - 1), 1, 0.0, rng.randf() < 0.5])
				x += rng.randf_range(0.55, 0.72)
	# marshals in the crowds' lanes (one every ~26 m), orderlies at the first-aid tents
	for side: float in [-1.0, 1.0]:
		var xb: float = X_BARRIER_L if side < 0.0 else X_BARRIER_R
		var lanes: Array = LANES[int(side)]
		for k in lanes.size():
			var l: Array = lanes[k]
			var zm: float = float(l[2]) - 14.0 - k * 9.0
			while zm > Z_FAR + 4.0:
				if lane_active(side, k, zm):
					var xm: float = xb + side * lerpf(float(l[0]), float(l[1]), rng.randf_range(0.3, 0.7))
					pts.append(_pt(Vector3(xm, 0.0, zm + rng.randf_range(-2.0, 2.0)), "guard_side", 1, false,
						rng.randf() < 0.5))
				zm -= rng.randf_range(22.0, 30.0)
		for cg: Array in CROSS[int(side)]:
			if str(cg[2]) == "aid":
				var xt: float = xb + side * (crowd_depth(side, float(cg[0])) - 1.6 - 2.2)
				for i in 2:
					pts.append(_pt(Vector3(xt + side * 0.5 * i, 0.0, float(cg[0]) - 0.9 + 1.5 * i), "civ_back", -1, false,
						i == 0))
	# drivers waiting at the motor pool in twos and threes
	for g in 6:
		var gz := -340.0 - g * 15.0
		for i in rng.randi_range(2, 3):
			pts.append(_pt(Vector3(-40.5 + rng.randf_range(-1.2, 1.2), 0.0, gz + rng.randf_range(-1.0, 1.0)),
				"guard_side", 1, false, rng.randf() < 0.5))
	_mm(self, pts, fig_mat, "AvenueFigures")


static func gang_spots() -> Array:
	return [Vector3(4.4, 0, -131.0), Vector3(5.6, 0, -140.5), Vector3(4.2, 0, -149.0), Vector3(20.2, 0, -135.5),
		Vector3(19.8, 0, -146.5), Vector3(5.2, 0, -163.0), Vector3(20.4, 0, -161.0), Vector3(4.8, 0, -181.0),
		Vector3(20.2, 0, -188.0), Vector3(26.0, 0, -180.5), Vector3(31.0, 0, -183.5), Vector3(25.6, 0, -190.0)]


## Front rank of column block k at T_MID (block 0 leads, nearest the plaza).
static func column_front(k: int) -> float:
	return COL_HEAD + k * COL_PITCH


## The marching column up the middle of the avenue: COL_BLOCKS blocks of COL_FILES x COL_RANKS men marching away
## from the camera, every block in step (its own beat), a few men a step out; before each block its colour party --
## three standard bearers abreast between two escorts, the banners on cross-bar poles (flag_street,
## Symbols-resolved; big enough to read as a row of standards from the roofs) -- and before that the officer.  One
## MultiMesh and one banner mesh under a single node that moves up the avenue at COL_SPEED.
func _build_column() -> void:
	var col := Node3D.new()
	col.name = "Column"
	add_child(col)
	var m := _slot("march_back")
	var frames := int(m[1])
	var pts: Array = []
	for k in COL_BLOCKS:
		var zf := column_front(k)
		var beat := rng.randf_range(0.0, 4.0)
		for r in COL_RANKS:
			for i in COL_FILES:
				var px := HX + (i - (COL_FILES - 1) * 0.5) * COL_DX + rng.randf_range(-0.03, 0.03)
				var pz := zf + r * COL_DZ + rng.randf_range(-0.03, 0.03)
				pts.append([Vector3(px, 0.0, pz), int(m[0]), frames, beat if rng.randf() < 0.95 else beat + 2.0, false])
		for ex: float in [-5.8, -4.35, 0.0, 4.35, 5.8]:                       # colour party
			pts.append([Vector3(HX + ex, 0.0, zf - 3.0), int(m[0]), frames, beat, false])
		pts.append([Vector3(HX, 0.0, zf - 6.2), int(m[0]), frames, beat, false])   # the officer leads
	_mm(col, pts, col_mat, "ColumnMarch")
	_col = col
	# the standards: pole from the bearer's hands, cross-bar, the cloth hanging from it (facing the camera)
	var banners := _mesh_node("Banners", func():
		var pm := K("metal")
		var fl := K("standard")
		for k in COL_BLOCKS:
			var zb := column_front(k) - 3.0
			for bx: float in [HX - 4.35, HX, HX + 4.35]:
				pm.box(Vector3(bx + 0.14, 0.95, zb - 0.05), Vector3(0.09, 4.55, 0.09), c(B.NIGHT[3]))
				pm.box(Vector3(bx - 0.86, 5.36, zb - 0.04), Vector3(1.86, 0.08, 0.08), c(B.NIGHT[3]))
				pm.box(Vector3(bx + 0.08, 5.44, zb - 0.06), Vector3(0.22, 0.24, 0.12), c(B.OCHRE[3]))   # finial
				fl.quad(Vector3(bx - 0.8, 2.5, zb + 0.06), Vector3(bx - 0.8, 5.34, zb + 0.06),
					Vector3(bx + 0.86, 5.34, zb + 0.06), Vector3(bx + 0.86, 2.5, zb + 0.06), Color.WHITE, 0.55), col)
	stats["column_banners"] = COL_BLOCKS * 3
	stats["column_primitives"] = int(banners.get_meta("primitives", 0))
	_movers.append({"node": col, "p0": Vector3.ZERO, "v": Vector3(0.0, 0.0, -COL_SPEED)})


## Places of the vehicle column at T_MID: [type (0 tank, 1 lorry with infantry), hull centre].  Rows of three
## abreast in the left lane, nose to the plaza: six rows of tanks, then six of lorries.
static func vehicle_slots() -> Array:
	var out: Array = []
	for i in VEH_ROWS.size():
		var tp: int = VEH_ROWS[i]
		for x: float in VEH_ROW_X:
			out.append([tp, Vector3(x, 0.0, VEH_HEAD + i * VEH_ROW_PITCH + (3.5 if tp == 0 else 3.8))])
	return out


## The vehicle column crawling up the left lane with the marching column: one rigid node; every design (tank,
## lorry with infantry, lorry under a tarp) is built once and instanced (one MultiMesh per material), the exhaust
## vapour rides along.
func _build_vehicle_column() -> void:
	var vc := Node3D.new()
	vc.name = "VehicleColumn"
	add_child(vc)
	var slots := vehicle_slots()
	var designs := [[], [], []]                    # transforms: tanks, lorries with infantry, lorries under a tarp
	for s: Array in slots:
		var fwd := Vector3(0.0, 0.0, -1.0)
		var xf := Transform3D(Basis(fwd, Vector3.UP, fwd.cross(Vector3.UP)), s[1])
		if int(s[0]) == 0:
			designs[0].append(xf)
		else:
			designs[1 if rng.randf() < 0.75 else 2].append(xf)
	var tris := _instance_design(vc, func():
		tank_into(K("metal"), K("wires"), 0.0)
		_snowcaps_tank(K("lamp"))
		_headlight_pool(K("lamp"), 3.6), designs[0], "Tanks")
	tris += _instance_design(vc, func():
		lorry_into(K("metal"), K("glass"), K("lamp"), c(B.STEEL[2]), c(B.STEEL[3]), true, 4, false)
		_snowcaps_lorry(K("lamp"), 4)
		_headlight_pool(K("lamp"), 3.7), designs[1], "LorriesTroops")
	tris += _instance_design(vc, func():
		lorry_into(K("metal"), K("glass"), K("lamp"), c(B.STEEL[2]), c(B.PATINA[1]), true, 0, false)
		_snowcaps_lorry(K("lamp"), 0)
		_headlight_pool(K("lamp"), 3.7), designs[2], "LorriesTarp")
	var pf := _slot("puff")
	var pts: Array = []
	for xf: Transform3D in designs[0]:
		for e in 2:
			pts.append([xf.origin + Vector3(rng.randf_range(-0.6, 0.6), 0.9, 3.5), int(pf[0]), int(pf[1]),
				rng.randf_range(0.0, 4.2), rng.randf() < 0.5])
	_mm(vc, pts, puff_mat, "ColumnVapour")
	stats["tanks"] = designs[0].size()
	stats["column_lorries"] = slots.size() - designs[0].size()
	stats["vehicle_primitives"] = tris
	_movers.append({"node": vc, "p0": Vector3.ZERO, "v": Vector3(0.0, 0.0, -COL_SPEED)})


## Snow lying on the column's vehicles, catching the glow of the searchlight dome (CAP_EM self light, drawn in the
## lamp kit: the post process does not outline it, so the pale top survives on a vehicle of 10 x 6 px): from the
## roofs a tank reads as a dark hull under a pale turret, deck and gun, a lorry as a pale tarp or a cab roof over a
## bed of snow-dusted helmets -- silhouettes instead of dark gaps in the avenue.  Local frame (front = +x).
const CAP_EM := 0.4


func _cap(k: Kit, x0: float, x1: float, z0: float, z1: float, y: float, em: float = CAP_EM) -> void:
	k.face(Vector3((x0 + x1) * 0.5, y, (z0 + z1) * 0.5), Vector3.UP, Vector3.RIGHT, absf(z1 - z0) * 0.5,
		absf(x1 - x0) * 0.5, c(B.SNOW[3]), em)


## The rear of a column vehicle dimly lit by the headlights of the one behind it (local frame, rear face at -x):
## plates and flaps as faint self-lit faces in the lamp kit, so the rear silhouette has an inside -- a tank's low hull
## under the turret bustle, a lorry's tailgate under a pale tarp flap or a row of backs.
func _rear_lit(k: Kit, x: float, y0: float, y1: float, hw: float, col: Color, em: float) -> void:
	k.face(Vector3(x, (y0 + y1) * 0.5, 0.0), Vector3.LEFT, Vector3.UP, hw, (y1 - y0) * 0.5, col, em)


func _snowcaps_tank(k: Kit) -> void:
	_rear_lit(k, -3.53, 0.42, 1.38, 0.95, c(B.STEEL[2]), 0.16)      # hull rear plate
	_rear_lit(k, -2.47, 1.5, 2.04, 0.82, c(B.STEEL[3]), 0.2)        # turret bustle
	_rear_lit(k, -2.67, 2.08, 2.25, 0.78, c(B.STONE[2]), 0.18)      # stowage basket
	_cap(k, -3.15, -1.5, -0.98, 0.98, 1.475)                      # engine deck
	_cap(k, 1.2, 2.3, -0.95, 0.95, 1.39)                          # front deck
	_cap(k, 2.4, 3.3, -0.9, 0.9, 1.0, CAP_EM * 0.6)               # glacis (sloped: dimmer)
	for sd: float in [-1.0, 1.0]:
		_cap(k, -3.45, 3.45, sd * 1.06, sd * 1.7, 0.975)          # track guards
	_cap(k, -0.98, 0.3, -0.62, 0.62, 2.215)                      # turret roof
	_cap(k, -2.65, -1.72, -0.78, 0.78, 2.275)                     # stowage basket
	_cap(k, 1.5, 5.6, -0.075, 0.075, 2.0)                         # snow along the gun


## The dimmed headlights of a column vehicle on the snow ahead of it (a pale fan, brightest near the lamps): from the
## roofs every vehicle stands dark against its own pool of light and the vehicle ahead -- the column reads as a
## chain of silhouettes.  Drawn in the lamp kit (no outline), instanced with the vehicle.
func _headlight_pool(k: Kit, nose: float) -> void:
	var steps := [[0.0, 4.0, 0.9, 1.7, 0.6], [4.0, 9.0, 1.7, 2.5, 0.45], [9.0, 15.0, 2.5, 3.2, 0.28]]
	for st: Array in steps:
		var x0: float = nose + float(st[0])
		var x1: float = nose + float(st[1])
		k.quad(Vector3(x0, 0.03, -float(st[2])), Vector3(x1, 0.03, -float(st[3])), Vector3(x1, 0.03, float(st[3])),
			Vector3(x0, 0.03, float(st[2])), c(B.SNOW[3]), float(st[4]))


func _snowcaps_lorry(k: Kit, cargo: int) -> void:
	_rear_lit(k, -3.84, 0.98, 1.5, 1.15, c(B.STONE[2]), 0.2)        # tailgate planks
	if cargo == 0:
		_rear_lit(k, -3.82, 1.55, 2.6, 1.12, c(B.STEEL[3]), 0.24)   # tarp rear flap
	elif cargo == 4:
		_rear_lit(k, 0.83, 1.9, 2.6, 1.0, c(B.STEEL[2]), 0.14)      # cab back above the troops
	_cap(k, 0.86, 2.1, -1.06, 1.06, 2.78)                         # cab roof
	_cap(k, 2.26, 3.38, -0.74, 0.74, 1.735, CAP_EM * 0.8)         # bonnet
	if cargo == 0:
		_cap(k, -3.78, 0.7, -0.76, 0.76, 2.995)                   # tarp roof
		for sd: float in [-1.0, 1.0]:
			_cap(k, -3.78, 0.7, sd * 0.78, sd * 1.12, 2.82, CAP_EM * 0.55)   # upper slopes of the tarp
	elif cargo == 4:
		for sd: float in [-1.0, 1.0]:
			for i in 5:
				var tx := -3.45 + i * 0.84
				_cap(k, tx - 0.15, tx + 0.15, sd * 0.66 - 0.15, sd * 0.66 + 0.15, 1.93)   # helmets
			_cap(k, -3.78, 0.72, sd * (1.175 - 0.07), sd * 1.175, 1.53, CAP_EM * 0.7)   # side boards


## Builds one vehicle design once (local frame, front = +x) and instances it at `xforms` under `parent`: one
## MultiMeshInstance3D per material.  Returns the primitives of all copies.
func _instance_design(parent: Node3D, fill: Callable, xforms: Array, tag: String) -> int:
	if xforms.is_empty():
		return 0
	var saved := _kits
	_kits = {}
	_ensure_kits(["metal", "glass", "lamp"])
	K("wires", Mesh.PRIMITIVE_LINES)
	fill.call()
	var prims := 0
	for name in _kits:
		var kit: Kit = _kits[name]
		if kit.count == 0:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = kit.commit()
		mm.instance_count = xforms.size()
		for i in xforms.size():
			mm.set_instance_transform(i, xforms[i])
		var mi := MultiMeshInstance3D.new()
		mi.name = "%s_%s" % [tag, name]
		mi.multimesh = mm
		mi.material_override = builder.mats.get(name, builder.mats["metal"])
		mi.layers = B.LAYER_OUT
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if name in ["lamp", "wires"] \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		parent.add_child(mi)
		prims += xforms.size() * kit.count / (2 if kit.primitive == Mesh.PRIMITIVE_LINES else 3)
	_kits = saved
	return prims


func _build_walkers() -> void:
	# late arrivals walking up behind the crowds towards the plaza in twos and threes (left), a few on the right
	var w1 := _slot("civ_walk")
	var w2 := _slot("civ_walk2")
	var groups := [[-34.5, -310.0, -1.0], [-34.0, -430.0, -1.0], [-35.0, -560.0, -1.0], [119.5, -520.0, 1.0]]
	var gi := 0
	for g in groups:
		var pts: Array = []
		var z := 36.0
		while z > -36.0:                       # little groups (a couple, a family) with gaps between them
			var gx := rng.randf_range(-1.6, 1.6)
			for i in rng.randi_range(1, 3):
				var w: Array = w1 if rng.randf() < 0.55 else w2
				var p := Vector3(gx + i * 0.7, 0.0, z - i * rng.randf_range(0.2, 0.9))
				pts.append([p, int(w[0]), int(w[1]), rng.randf_range(0.0, 4.0), float(g[2]) > 0.0])
			z -= rng.randf_range(7.0, 13.0)
		var node := Node3D.new()
		node.name = "Walkers%d" % gi
		add_child(node)
		_mm(node, pts, fig_mat, "WalkStream%d" % gi)
		_movers.append({"node": node, "p0": Vector3(float(g[0]), 0.0, float(g[1])), "v": Vector3(0.0, 0.0, -1.25)})
		gi += 1


func _build_moving_vehicles() -> void:
	# parked staff cars by the officers
	for k in 2:
		var pc := _mesh_node("StaffCarParked%d" % k, func():
			_at(Vector3.ZERO, Vector3(0, 0, -1))
			builder.car_into(K("metal"), K("glass"), K("lamp"), K("lamp"), c(B.NIGHT[1]), 4.8, false))
		pc.position = Vector3(23.0 - k * 2.4, 0.0, -249.0 - k * 1.0)
	# the snow plough crawling up the cleared lane, its beacon turning (light on the snow around it)
	var plough := _mesh_node("Plough", func():
		_at(Vector3.ZERO, Vector3(0, 0, -1))
		plough_into(K("metal"), K("glass"), K("lamp")))
	_movers.append({"node": plough, "p0": Vector3(12.0, 0.0, -160.0), "v": Vector3(0, 0, -1.6)})
	_beacon = OmniLight3D.new()
	_beacon.name = "Beacon"
	_beacon.light_color = c(B.OCHRE[4])
	_beacon.omni_range = 9.0
	_beacon.omni_attenuation = 1.2
	_beacon.light_specular = 0.0
	_beacon.light_cull_mask = B.LAYER_OUT
	_beacon.position = Vector3(0.0, 3.1, -1.42)
	plough.add_child(_beacon)
	# a second one standing in the lane as a tipper, being loaded by hand
	var tip := _mesh_node("Tipper", func():
		_at(Vector3.ZERO, Vector3(0, 0, -1))
		plough_into(K("metal"), K("glass"), K("lamp")))
	tip.position = Vector3(28.4, 0.0, -184.0)


func _build_puffs() -> void:
	var pf := _slot("puff")
	var pts: Array = []
	var spots: Array = []
	for v: Vector3 in _vent_spots():
		for k in 2:
			spots.append(v + Vector3(rng.randf_range(-0.3, 0.3), 0.0, rng.randf_range(-0.3, 0.3)))
	for i in 5:                                                                    # motor pool engines warming
		spots.append(Vector3(-44.0 - (i % 3) * 15.0, 0.6, -338.0 - i * 17.0))
	for s: Vector3 in spots:
		pts.append([s, int(pf[0]), int(pf[1]), rng.randf_range(0.0, 4.2), rng.randf() < 0.5])
	_mm(self, pts, puff_mat, "Vapour")


## The fires in the pylons' bowls: one flickering billboard each (flame slot, self-lit material), every one on its
## own beat.
func _build_flames() -> void:
	var fs := _slot("flame")
	var pts: Array = []
	for p: Vector3 in pylon_spots():
		pts.append([p + Vector3(0.0, 3.2, 0.0), int(fs[0]), int(fs[1]), rng.randf_range(0.0, 8.0), rng.randf() < 0.5])
	for p: Vector3 in stand_fires():
		pts.append([p, int(fs[0]), int(fs[1]), rng.randf_range(0.0, 8.0), rng.randf() < 0.5])
	_mm(self, pts, flame_mat, "Flames")


func _build_crows() -> void:
	var cr := _slot("crow")
	var pts: Array = []
	for i in 22:
		var a := rng.randf() * TAU
		var r := rng.randf_range(5.0, 20.0)
		pts.append([Vector3(cos(a) * r, rng.randf_range(-3.0, 4.0), sin(a) * r * 0.6), int(cr[0]), int(cr[1]),
			rng.randf_range(0.0, 3.0), rng.randf() < 0.5])
	_crows = Node3D.new()
	_crows.name = "Crows"
	add_child(_crows)
	_crows.position = FLOCK
	_mm(_crows, pts, crow_mat, "Flock")


# ================================================================================================ lights
func _spot(from: Vector3, to: Vector3, col: Color, energy: float, rng_m: float, angle: float) -> SpotLight3D:
	var s := SpotLight3D.new()
	s.light_color = col
	s.light_energy = energy
	s.spot_range = rng_m
	s.spot_angle = angle
	s.spot_attenuation = 0.6
	s.spot_angle_attenuation = 0.8
	s.light_specular = 0.0
	s.shadow_enabled = false
	s.light_cull_mask = B.LAYER_OUT
	add_child(s)
	s.look_at_from_position(from, to, Vector3.UP)
	return s


func _build_lights() -> void:
	var cold := Color(0.66, 0.78, 1.0)
	var n := 0
	for side: float in [-1.0, 1.0]:
		var xl: float = (X_BARRIER_L if side < 0.0 else X_BARRIER_R) + side * 1.2
		var zl := -140.0
		var i := 0
		while zl > Z_FAR + 4.0:
			if i % 2 == 0:
				_spot(Vector3(xl, 6.6, zl), Vector3(xl - side * 3.5, 0.0, zl - 1.5), cold, 2.4, 16.0, 46.0)
				n += 1
			zl -= 36.0
			i += 1
	# work lights on the stand, flood lamps over the buses and the motor pool
	for p: float in [-170.0, -118.0]:
		_spot(Vector3(p, 16.0, -538.0), Vector3(p, 5.0, -576.0), cold, 5.0, 60.0, 44.0)
		n += 1
	for p: float in [-62.0, -108.0]:
		_spot(Vector3(p, 12.0, -446.0), Vector3(p, 0.0, -474.0), cold, 3.0, 40.0, 50.0)
		n += 1
	for z: float in [-350.0, -405.0]:
		_spot(Vector3(-38.0, 10.6, z), Vector3(-58.0, 0.0, z), cold, 3.4, 36.0, 58.0)
		n += 1
	# the warm light of every fire bowl on the cordon: the guards, the barrier and the front rows of both crowds
	# glow along both edges of the avenue up to the plaza (the near ones a little stronger)
	for p: Vector3 in pylon_spots():
		var o := OmniLight3D.new()
		o.name = "Fire%d" % n
		o.light_color = c(B.GLOW[1])
		o.light_energy = 2.2 if p.z > -330.0 else 2.6
		o.omni_range = 10.0 if p.z > -330.0 else 11.5
		o.omni_attenuation = 1.3
		o.light_specular = 0.0
		o.light_cull_mask = B.LAYER_OUT
		add_child(o)
		o.position = p + Vector3(0.0, 4.0, 0.0)
		n += 1
	# the grandstands' fire bowls light the parapet and the front tiers (every other one)
	var sf := stand_fires()
	for i in range(0, sf.size(), 2):
		var o := OmniLight3D.new()
		o.name = "StandFire%d" % i
		o.light_color = c(B.GLOW[1])
		o.light_energy = 2.4
		o.omni_range = 10.0
		o.omni_attenuation = 1.3
		o.light_specular = 0.0
		o.light_cull_mask = B.LAYER_OUT
		add_child(o)
		o.position = (sf[i] as Vector3) + Vector3(0.0, 2.2, 0.0)
		n += 1
	# floodlights from the right grandstand's banner masts onto its tiers
	var zm := -381.0
	while zm > -736.0:
		_spot(Vector3(STAND_X - 1.5, 11.0, zm + 2.0), Vector3(STAND_X + 5.5, 3.0, zm - 6.0), cold, 3.0, 32.0, 56.0)
		zm -= 38.0
		n += 1
	stats["lights"] = n + 1
