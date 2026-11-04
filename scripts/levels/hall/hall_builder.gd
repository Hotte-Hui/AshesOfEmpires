extends RefCounted
## Builds the whole set of the Great Hall reveal (owner: great_hall_3d) at runtime, deterministically:
## archive window room (shot h1), a short Berlin tenement street that opens onto the plaza, the family's
## chamfered corner with the sealed door, tram wires, loudspeakers, the floodlit plaza and the fictional
## completed "Grosse Halle" (cubic podium with a relentless rhythm of colossal square pilasters, portico of
## square piers, heavy cornice, ribbed green-black patina dome with a plain lantern, endless colonnaded
## wings).  NO real insignia: the only emblem is the fictional Reichssiegel (white pillar in a black disc),
## small, on grey-black banners.
## Units: metres, +Y up, the camera looks along -Z and never rotates.  Hall axis x = HX, podium front z = HZ.
## Geometry is grouped by material into a few ArrayMeshes (one MeshInstance3D per material bucket).

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const TOON := preload("res://assets/shaders/pixel3d_toon.gdshader")
const TEX := "res://assets/architecture/great_hall/"

const HX := 45.0
const HZ := -1000.0
const LAYER_OUT := 1
const LAYER_IN := 2
const LAYER_PEOPLE := 4             ## sprites: lit by the scene AND by character key lights
## Street layout
const WIN_X := -7.0                 ## archive window centre (camera path axis during h1)
const STREET_HALF := 12.0
const NEAR_LEFT_END := -30.0
const CHAMFER_A := Vector3(-17.0, 0.0, -51.0)
const CHAMFER_B := Vector3(-12.0, 0.0, -56.0)
const FAMILY_BLOCK_END := -62.0
const RIGHT_BLOCK_END := -60.0
const PLAZA_EDGE := -63.0
const FLOOR_H := 3.9
const GROUND_H := 4.6
const FLOORS := 4

# --- pg.PALETTES['berlin'] (sRGB) -------------------------------------------------------------
const NIGHT := ["#120C14", "#1B1520", "#211623", "#2A2130"]
const VIOLET := ["#25202B", "#342F37", "#443B43", "#57494D"]
const STONE := ["#4A3A35", "#5F4A40", "#7A5E4E", "#94735C", "#AE8A6C", "#C9A585"]
const OCHRE := ["#5F4530", "#735145", "#8D5542", "#AF6C47", "#D07744", "#E5945A"]
const GLOW := ["#E5945A", "#F0AE6E", "#F4BA81", "#F8D2A0", "#FCE9C8"]
const STEEL := ["#1E2329", "#2F363F", "#454E58", "#5F6973", "#7C8690", "#A3ACB4"]
const PATINA := ["#1E2E2C", "#2C4440", "#3E5D55", "#56776A", "#73927F"]
const SNOW := ["#6E6A73", "#8F8A92", "#B2ACB0", "#D2CCCB", "#ECE6E0"]

var root: Node3D
var kits: Dictionary = {}
var mats: Dictionary = {}
var kit_layer: Dictionary = {}
var rng := RandomNumberGenerator.new()
var people_spec: Array = []
var story_window: MeshInstance3D
var story_window_mat: ShaderMaterial
var stats: Dictionary = {}
var _xf := Transform3D.IDENTITY
var wash_x_portico: Array = []
var wash_x_podium: Array = []
var wash_x_wings: Array = []
## Calibration (final camera pose) so the pilaster rhythm of the facade lands on whole pixels.
var cal_cam := Vector3(-6.85, 1.9, -20.0)
var cal_shift := Vector2(0, 56)
var cal_vp := Vector2(640, 360)
var cal_f := 846.8


static func c(hexs: String) -> Color:
	return Color(hexs)


func build(p_root: Node3D, calib: Dictionary) -> void:
	root = p_root
	rng.seed = 1964
	cal_cam = calib.get("cam", cal_cam)
	cal_shift = calib.get("shift", cal_shift)
	cal_vp = calib.get("vp", cal_vp)
	cal_f = calib.get("f", cal_f)
	_make_materials()
	_build_ground()
	_build_archive_room()
	_build_street()
	_build_family_corner()
	_build_street_furniture()
	_build_wires()
	_build_tram()
	_build_plaza()
	_build_hall()
	_build_far_city()
	_flush()
	_build_lights()


# ============================================================================== materials
func _toon(params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = TOON
	for k in params:
		m.set_shader_parameter(k, params[k])
	return m


func _tex(path: String) -> Texture2D:
	if ResourceLoader.exists(TEX + path):
		return load(TEX + path)
	return null


func _make_materials() -> void:
	mats["stone"] = _toon({"snow": 1.0, "snow_threshold": 0.7, "rim": 1.0, "rim_threshold": 0.5})
	mats["hall_far"] = _toon({"snow": 1.0, "snow_threshold": 0.7, "rim": 0.0})
	# flag 0.3 = "patina allowed": only these pixels may snap to the green-black patina ramp
	mats["patina"] = _toon({"snow": 1.0, "snow_threshold": 0.93, "rim": 1.0, "rim_threshold": 0.5,
		"toon_steps": 5.0, "flag": 0.3})
	mats["plaster"] = _toon({"snow": 1.0, "snow_threshold": 0.7, "rim": 0.6})
	mats["roof"] = _toon({"snow": 1.0, "snow_threshold": 0.35, "rim": 0.8})
	mats["glass"] = _toon({"flag": 0.0, "toon_steps": 3.0})
	mats["glass_lit"] = _toon({"flag": 0.75, "emission_energy": 1.0, "toon_steps": 3.0})
	mats["ground"] = _toon({"snow": 0.0, "toon_steps": 5.0, "toon_seam": 0.22})
	mats["metal"] = _toon({"snow": 1.0, "snow_threshold": 0.75, "rim": 1.0})
	mats["lamp"] = _toon({"flag": 0.75, "emission_energy": 1.0})
	mats["cloth"] = _toon({"light_wrap": 0.35, "snow": 0.0})
	mats["interior"] = _toon({"toon_steps": 4.0})
	mats["cloth_in"] = _toon({"light_wrap": 0.4})
	mats["wires"] = _toon({"flag": 1.0, "toon_steps": 2.0})
	var paper := _tex("textures/drawing.png")
	mats["paper"] = _toon({"use_tex": paper != null, "albedo_tex": paper, "use_vertex_color": false,
		"toon_steps": 4.0})
	var door := _tex("textures/door_sealed.png")
	mats["door"] = _toon({"use_tex": door != null, "albedo_tex": door, "use_vertex_color": false,
		"toon_steps": 4.0})
	var banner := _tex("textures/banner.png")
	mats["banner"] = _toon({"use_tex": banner != null, "albedo_tex": banner, "use_vertex_color": false,
		"alpha_scissor": 0.5, "toon_steps": 3.0, "light_wrap": 0.3})
	var poster := _tex("textures/posters.png")
	mats["poster"] = _toon({"use_tex": poster != null, "albedo_tex": poster, "use_vertex_color": false,
		"toon_steps": 3.0})
	for k in ["interior", "paper", "cloth_in", "lamp_in", "glass_in"]:
		kit_layer[k] = LAYER_IN
	mats["lamp_in"] = mats["lamp"]
	mats["glass_in"] = _toon({"flag": 0.0, "toon_steps": 3.0})


func K(name: String, primitive: int = Mesh.PRIMITIVE_TRIANGLES) -> Kit:
	if not kits.has(name):
		kits[name] = Kit.new(primitive)
	var k: Kit = kits[name]
	k.xf = _xf
	return k


## Build subsequent geometry in a local frame: local +X along the facade, +Y up, +Z = outward normal.
func _frame(origin: Vector3, along: Vector3) -> void:
	var x := along.normalized()
	var z := x.cross(Vector3.UP).normalized()      # outward normal (right-handed: x × y = z)
	_xf = Transform3D(Basis(x, Vector3.UP, z), origin)
	for k in kits.values():
		(k as Kit).xf = _xf


func _world() -> void:
	_frame(Vector3.ZERO, Vector3.RIGHT)


func _flush() -> void:
	var geo := Node3D.new()
	geo.name = "Geometry"
	root.add_child(geo)
	var tris := 0
	for name in kits:
		var kit: Kit = kits[name]
		if kit.count == 0:
			continue
		var mesh := kit.commit()
		var mi := MeshInstance3D.new()
		mi.name = "M_" + name
		mi.mesh = mesh
		mi.material_override = mats.get(name, mats["stone"])
		mi.layers = kit_layer.get(name, LAYER_OUT)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		if name in ["wires", "lamp", "glass_lit", "lamp_in"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geo.add_child(mi)
		tris += kit.count / (2 if kit.primitive == Mesh.PRIMITIVE_LINES else 3)
	stats["primitives"] = tris
	stats["meshes"] = geo.get_child_count()


# ============================================================================== helpers
func _jit(col: String, amount: float = 0.0) -> Color:
	var cc := Color(col)
	if amount > 0.0:
		var k := 1.0 + rng.randf_range(-amount, amount)
		cc = Color(cc.r * k, cc.g * k, cc.b * k)
	return cc


## screen-x -> world-x on a plane at depth z (calibration camera), for pixel-aligned rhythms
func _world_x_for_px(px: float, z: float) -> float:
	var depth := cal_cam.z - z
	return cal_cam.x + (px - cal_vp.x * 0.5 + cal_shift.x) / cal_f * depth


func _px_per_m(z: float) -> float:
	return cal_f / (cal_cam.z - z)


func _screen_x(x: float, z: float) -> float:
	return cal_vp.x * 0.5 - cal_shift.x + (x - cal_cam.x) * _px_per_m(z)


# ============================================================================== ground
func _build_ground() -> void:
	_world()
	var g := K("ground")
	# Big snowfield (plaza + city ground), split in bands so vertex colours can vary with distance.
	var z_bands := [40.0, 0.0, -30.0, -63.0, -130.0, -260.0, -480.0, -760.0, -1000.0, -1500.0, -4000.0]
	for i in z_bands.size() - 1:
		var z0: float = z_bands[i]
		var z1: float = z_bands[i + 1]
		var col := c(SNOW[3]) if i < 4 else c(SNOW[2])
		g.quad(Vector3(-3000, 0, z0), Vector3(-3000, 0, z1), Vector3(3000, 0, z1), Vector3(3000, 0, z0), col)
	# Street: trampled slush lanes along the tram tracks and wheel ruts (irregular strips)
	# continuous ruts (no gaps: gaps read as road markings), mottled between three slush tones
	var lanes := [[-4.0, 0.7], [-1.7, 0.6], [2.2, 0.7], [4.4, 0.7], [6.2, 0.5]]
	for l in lanes:
		var x0: float = l[0]
		var w: float = l[1]
		var z := 1.0
		var wob := 0.0
		while z > PLAZA_EDGE - 4.0:
			var seg := rng.randf_range(1.5, 4.0)
			var r := rng.randf()
			var tone: String = SNOW[1] if r < 0.5 else (SNOW[0] if r < 0.85 else VIOLET[3])
			var wob2 := clampf(wob + rng.randf_range(-0.12, 0.12), -0.3, 0.3)
			var ww := w * rng.randf_range(0.7, 1.15)
			g.quad(Vector3(x0 + wob, 0.012, z), Vector3(x0 + wob2, 0.012, z - seg),
				Vector3(x0 + ww + wob2, 0.012, z - seg), Vector3(x0 + ww + wob, 0.012, z), c(tone))
			wob = wob2
			z -= seg
	# footprints: a trail on the left sidewalk towards the family's corner
	var fp := 0
	var p := Vector3(-9.6, 0.17, -50.0)
	while fp < 34:
		var side := 0.16 if fp % 2 == 0 else -0.16
		var q := p + Vector3(side + rng.randf_range(-0.05, 0.05), 0, rng.randf_range(-0.08, 0.08))
		var hl := rng.randf_range(0.11, 0.16)
		g.quad(Vector3(q.x - 0.09, 0.172, q.z + hl), Vector3(q.x - 0.09, 0.172, q.z - hl),
			Vector3(q.x + 0.09, 0.172, q.z - hl), Vector3(q.x + 0.09, 0.172, q.z + hl),
			c(SNOW[1]) if rng.randf() < 0.7 else c(SNOW[2]))
		p += Vector3(rng.randf_range(-0.08, 0.14), 0, rng.randf_range(0.55, 0.8))
		if fp == 16:
			p = Vector3(-10.6, 0.17, -46.0)     # a second, older trail
		fp += 1
	# Cleared walking paths across the plaza converging on the portico (leading lines).
	for side: float in [-1.0, 1.0]:
		var a := Vector3(side * 8.0 + 2.0, 0.01, PLAZA_EDGE - 6.0)
		var b := Vector3(HX + side * 30.0, 0.01, HZ + 70.0)
		var dir := (b - a)
		var n := Vector3(-dir.z, 0, dir.x).normalized() * 2.6
		g.quad(a - n, b - n, b + n, a + n, c(SNOW[1]))
	# Kerbs and sidewalks (snow topped); a raised corner apron in front of the family's chamfered corner
	var kerb := K("stone")
	kerb.box(Vector3(-22.0, 0.0, -60.0), Vector3(13.5, 0.16, 10.5), {"top": c(SNOW[3]), "front": c(STONE[1]),
		"side": c(STONE[1])})
	for side: float in [-1.0, 1.0]:
		var x_in: float = 8.5 * side
		var z_end: float = FAMILY_BLOCK_END if side < 0 else RIGHT_BLOCK_END
		var xmin := minf(x_in, 12.0 * side)
		kerb.box(Vector3(xmin, 0.0, z_end), Vector3(3.5, 0.16, -z_end), {"top": c(SNOW[3]),
			"front": c(STONE[1]), "side": c(STONE[1])})
		var z := -2.0
		while z > z_end + 2.0:
			var l := rng.randf_range(2.0, 5.5)
			var h := rng.randf_range(0.18, 0.34)
			var w := rng.randf_range(0.5, 0.9)
			if not (side < 0.0 and z < NEAR_LEFT_END + 2.0 and z > -60.0):
				_snow_bank(g, x_in, z, l, h, w, side)
			z -= l + rng.randf_range(1.5, 7.0)
	# granite bollards along the plaza edge
	var x := -9.0
	while x < 14.0:
		kerb.pillar(x, PLAZA_EDGE - 1.0, 0.0, 0.42, 0.42, 0.7, {"front": c(STONE[1]), "side": c(STONE[0]),
			"top": c(SNOW[4])})
		x += 3.4


## Snow pushed against the kerb: a low wedge (kerb side high, street side flat) with tapered ends.
func _snow_bank(g: Kit, x_kerb: float, z0: float, l: float, h: float, w: float, side: float) -> void:
	var xs: float = x_kerb - side * w          # street-side foot of the wedge
	var za := z0
	var zb := z0 - l
	var top := c(SNOW[4])
	var face := c(SNOW[3])
	var e := minf(0.8, l * 0.25)
	var pk1 := Vector3(x_kerb, h, za - e)
	var pk2 := Vector3(x_kerb, h, zb + e)
	var f1 := Vector3(xs, 0.0, za - e)
	var f2 := Vector3(xs, 0.0, zb + e)
	if side < 0.0:
		g.quad(f1, pk1, pk2, f2, face)
		g.tri(Vector3(x_kerb, 0.0, za), pk1, f1, top)
		g.tri(f2, pk2, Vector3(x_kerb, 0.0, zb), top)
	else:
		g.quad(f2, pk2, pk1, f1, face)
		g.tri(f1, pk1, Vector3(x_kerb, 0.0, za), top)
		g.tri(Vector3(x_kerb, 0.0, zb), pk2, f2, top)


# ============================================================================== archive room (h1)
func _build_archive_room() -> void:
	_world()
	var k := K("interior")
	var wall := c(NIGHT[3])
	var reveal := c(VIOLET[1])
	var wx0 := WIN_X - 0.75
	var wx1 := WIN_X + 0.75
	var wy0 := 7.45
	var wy1 := 10.25
	var z_out := 0.0
	var z_in := 0.7
	k.box(Vector3(wx0 - 8.0, 6.5, z_out), Vector3(8.0, 5.0, z_in), {"front": wall, "side": reveal})
	k.box(Vector3(wx1, 6.5, z_out), Vector3(8.0, 5.0, z_in), {"front": wall, "side": reveal})
	k.box(Vector3(wx0, 6.5, z_out), Vector3(wx1 - wx0, wy0 - 6.5, z_in), {"front": wall, "top": reveal})
	k.box(Vector3(wx0, wy1, z_out), Vector3(wx1 - wx0, 1.25, z_in), {"front": wall, "side": reveal,
		"bottom": reveal}, Kit.FACES_ALL)
	var sill := K("stone")
	sill.box(Vector3(wx0 - 0.15, wy0 - 0.12, -0.32), Vector3(wx1 - wx0 + 0.3, 0.12, 0.34),
		{"top": c(SNOW[4]), "front": c(STONE[2]), "side": c(STONE[1])})
	k.box(Vector3(WIN_X - 3.5, 6.3, z_in), Vector3(7.0, 0.2, 7.0), c(NIGHT[2]))
	k.box(Vector3(WIN_X - 3.5, 10.9, z_in), Vector3(7.0, 0.2, 7.0), c(NIGHT[1]), Kit.FACES_ALL)
	k.box(Vector3(WIN_X - 3.7, 6.5, z_in), Vector3(0.2, 4.4, 7.0), c(NIGHT[2]))
	k.box(Vector3(WIN_X + 3.5, 6.5, z_in), Vector3(0.2, 4.4, 7.0), c(NIGHT[2]))
	var fr := c("#2A2130")
	var ft := 0.07
	k.box(Vector3(wx0, wy0, 0.42), Vector3(ft, wy1 - wy0, 0.08), fr, Kit.FACES_ALL)
	k.box(Vector3(wx1 - ft, wy0, 0.42), Vector3(ft, wy1 - wy0, 0.08), fr, Kit.FACES_ALL)
	k.box(Vector3(wx0, wy1 - ft, 0.42), Vector3(wx1 - wx0, ft, 0.08), fr, Kit.FACES_ALL)
	k.box(Vector3(wx0, wy0, 0.42), Vector3(wx1 - wx0, ft, 0.08), fr, Kit.FACES_ALL)
	k.box(Vector3(wx0, 9.55, 0.42), Vector3(wx1 - wx0, 0.09, 0.08), fr, Kit.FACES_ALL)
	# two casement leaves opened inwards (~104 deg), hinged on the opening sides
	for side: float in [-1.0, 1.0]:
		var hinge_x: float = wx0 + ft if side < 0 else wx1 - ft
		var ang: float = deg_to_rad(104.0) * (-side)
		var basis := Basis(Vector3.UP, ang)
		var lw := (wx1 - wx0) * 0.5 - ft
		var centre: Vector3 = Vector3(hinge_x, (wy0 + 9.55) * 0.5, 0.5) + basis * Vector3(-side * lw * 0.5, 0, 0)
		var h := Vector3(lw * 0.5, (9.55 - wy0) * 0.5 - 0.02, 0.03)
		var bx := basis.x
		var by := basis.y
		k.obox(centre + by * (h.y - 0.035), basis, Vector3(h.x, 0.035, 0.035), fr)
		k.obox(centre - by * (h.y - 0.035), basis, Vector3(h.x, 0.035, 0.035), fr)
		k.obox(centre + bx * (h.x - 0.035), basis, Vector3(0.035, h.y, 0.035), fr)
		k.obox(centre - bx * (h.x - 0.035), basis, Vector3(0.035, h.y, 0.035), fr)
		k.obox(centre, basis, Vector3(h.x, 0.025, 0.03), fr)
		var gl := K("glass_in")
		gl.obox(centre, basis, Vector3(h.x - 0.05, h.y - 0.05, 0.004), c(VIOLET[0]), Kit.FACE_PZ | Kit.FACE_NZ)
	# heavy curtains (zig-zag folds), the left one close to the camera
	var cu := K("cloth_in")
	var folds := 7
	var cx0 := WIN_X - 2.15
	var cx1 := WIN_X - 0.95
	for i in folds:
		var xa := lerpf(cx0, cx1, float(i) / folds)
		var xb := lerpf(cx0, cx1, float(i + 1) / folds)
		var za := 0.95 + (0.12 if i % 2 == 0 else 0.0)
		var zb := 0.95 + (0.12 if i % 2 == 1 else 0.0)
		var col := c("#342F37") if i % 2 == 0 else c("#25202B")
		cu.quad(Vector3(xa, 6.55, za), Vector3(xa, 10.75, za), Vector3(xb, 10.75, zb), Vector3(xb, 6.55, zb), col)
	for i in 4:
		var xa := lerpf(WIN_X + 1.05, WIN_X + 1.7, float(i) / 4)
		var xb := lerpf(WIN_X + 1.05, WIN_X + 1.7, float(i + 1) / 4)
		var za := 0.95 + (0.1 if i % 2 == 0 else 0.0)
		var zb := 0.95 + (0.1 if i % 2 == 1 else 0.0)
		cu.quad(Vector3(xa, 6.55, za), Vector3(xa, 10.75, za), Vector3(xb, 10.75, zb), Vector3(xb, 6.55, zb),
			c("#25202B") if i % 2 else c("#342F37"))
	# desk under the window with the drawing, a rolled plan and a lamp
	var desk := c("#3D2820")
	k.box(Vector3(WIN_X - 1.2, 6.5, 0.72), Vector3(2.4, 0.84, 1.15), {"top": c("#55372A"), "front": desk,
		"side": desk})
	var pp := K("paper")
	var pc := Vector3(WIN_X - 0.1, 7.345, 1.02)
	var rot := Basis(Vector3.UP, deg_to_rad(4.0))
	var hw := 0.52
	var hd := 0.36
	pp.quad(pc + rot * Vector3(-hw, 0, hd), pc + rot * Vector3(-hw, 0, -hd), pc + rot * Vector3(hw, 0, -hd),
		pc + rot * Vector3(hw, 0, hd), Color.WHITE)
	k.obox(Vector3(WIN_X - 0.95, 7.38, 0.9), Basis(Vector3.UP, deg_to_rad(-12.0)), Vector3(0.3, 0.035, 0.035),
		c("#8E8A78"))
	k.box(Vector3(WIN_X + 0.92, 7.34, 0.86), Vector3(0.12, 0.03, 0.12), c(NIGHT[1]))
	k.box(Vector3(WIN_X + 0.97, 7.37, 0.9), Vector3(0.025, 0.3, 0.025), c(NIGHT[1]))
	k.obox(Vector3(WIN_X + 0.9, 7.7, 0.93), Basis(Vector3.FORWARD, deg_to_rad(-30.0)), Vector3(0.09, 0.05, 0.09),
		c("#2C4440"))
	var lamp := K("lamp_in")
	lamp.box(Vector3(WIN_X + 0.84, 7.62, 0.9), Vector3(0.08, 0.025, 0.08), c(GLOW[4]), Kit.FACES_ALL, 1.0)


# ============================================================================== tenements
## Gruenderzeit facade in the current local frame: facade plane z = 0 facing +z, from x = 0 to `length`.
func _tenement(length: float, seed_: int, base_col: String, lit_prob: float, opts: Dictionary = {}) -> void:
	rng.seed = seed_
	var p := K("plaster")
	var st := K("stone")
	var height := GROUND_H + FLOOR_H * FLOORS
	var depth := float(opts.get("depth", 14.0))
	var body := _jit(base_col, 0.03)
	p.box(Vector3(0.0, 0.0, -depth), Vector3(length, height, depth), {"front": body, "side": body,
		"top": c(SNOW[3])})
	st.box(Vector3(0.0, 0.0, 0.0), Vector3(length, GROUND_H, 0.18), {"front": c(STONE[1]), "side": c(STONE[1]),
		"top": c(SNOW[3])})
	var gy := 0.6
	while gy < GROUND_H - 0.4:
		st.box(Vector3(0.0, gy, 0.18), Vector3(length, 0.05, 0.01), c(STONE[0]), Kit.FACE_PZ)
		gy += 0.62
	for f in range(FLOORS + 1):
		var y := GROUND_H + f * FLOOR_H - 0.25
		st.box(Vector3(0.0, y, 0.0), Vector3(length, 0.3, 0.22), {"front": c(STONE[3]), "side": c(STONE[2]),
			"top": c(SNOW[4])})
	st.box(Vector3(-0.3, height - 0.9, 0.0), Vector3(length + 0.6, 0.9, 0.75), {"front": c(STONE[2]),
		"side": c(STONE[1]), "top": c(SNOW[4]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	var roof := K("roof")
	roof.quad(Vector3(0.0, height, 0.75), Vector3(0.0, height + 4.2, -3.2), Vector3(length, height + 4.2, -3.2),
		Vector3(length, height, 0.75), c(STEEL[1]))
	roof.box(Vector3(0.0, height + 4.19, -depth), Vector3(length, 0.02, depth - 3.2), c(SNOW[3]))
	var cz := 3.0
	while cz < length - 2.0:
		st.box(Vector3(cz, height + 3.7, -rng.randf_range(5.0, 9.0)), Vector3(1.6, rng.randf_range(1.6, 2.6), 1.0),
			{"front": c(STONE[1]), "side": c(STONE[0]), "top": c(SNOW[3])})
		cz += rng.randf_range(7.0, 12.0)
	var bay := 3.7
	var nb := int(floor(length / bay))
	var margin := (length - nb * bay) * 0.5
	var skip_ground: Array = opts.get("skip_ground", [])
	for f in range(FLOORS + 1):
		for i in nb:
			var xc := margin + (i + 0.5) * bay
			if f == 0 and (rng.randf() < 0.15 or i in skip_ground):
				continue
			var wh := 2.15 if f > 0 else 2.4
			var y0 := (GROUND_H + (f - 1) * FLOOR_H + 0.95) if f > 0 else 1.35
			_window(xc, y0, 1.25, wh, f, lit_prob)
		if f >= 2 and f <= FLOORS - 1 and not bool(opts.get("no_balconies", false)):
			for i in nb:
				if (i + f + seed_) % 5 != 0:
					continue
				_balcony(margin + (i + 0.5) * bay, GROUND_H + (f - 1) * FLOOR_H + 0.6)


func _balcony(xc: float, yb: float) -> void:
	var m := K("metal")
	m.box(Vector3(xc - 1.5, yb, 0.0), Vector3(3.0, 0.18, 1.1), {"front": c(STONE[2]), "top": c(SNOW[4]),
		"side": c(STONE[1]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	m.box(Vector3(xc - 1.5, yb + 1.0, 1.04), Vector3(3.0, 0.06, 0.06), {"front": c(NIGHT[2]), "top": c(SNOW[4])})
	var px := xc - 1.5
	while px <= xc + 1.5:
		m.box(Vector3(px - 0.03, yb + 0.18, 1.04), Vector3(0.06, 0.85, 0.06), c(NIGHT[2]))
		px += 0.25


## Window in the current local frame (facade plane z = 0, normal +z).  force: -1 random, 0 dark, 1 lit
func _window(xc: float, y0: float, ww: float, wh: float, floor_i: int, lit_prob: float, force: int = -1) -> void:
	if floor_i == 0:
		# the rusticated plinth is 0.18 m proud of the facade: ground-floor windows sit on its face
		var saved := _xf
		_xf = _xf * Transform3D(Basis.IDENTITY, Vector3(0, 0, 0.18))
		for k in kits.values():
			(k as Kit).xf = _xf
		_window_body(xc, y0, ww, wh, floor_i, lit_prob, force)
		_xf = saved
		for k in kits.values():
			(k as Kit).xf = _xf
		return
	_window_body(xc, y0, ww, wh, floor_i, lit_prob, force)


func _window_body(xc: float, y0: float, ww: float, wh: float, floor_i: int, lit_prob: float, force: int) -> void:
	var st := K("stone")
	var lit := rng.randf() < lit_prob if force < 0 else force == 1
	var frame := c(STONE[3]) if floor_i > 0 else c(STONE[2])
	st.box(Vector3(xc - ww * 0.5 - 0.22, y0 - 0.12, 0.0), Vector3(0.22, wh + 0.24, 0.1), frame)
	st.box(Vector3(xc + ww * 0.5, y0 - 0.12, 0.0), Vector3(0.22, wh + 0.24, 0.1), frame)
	st.box(Vector3(xc - ww * 0.5 - 0.3, y0 - 0.2, 0.0), Vector3(ww + 0.6, 0.14, 0.24),
		{"front": c(STONE[3]), "top": c(SNOW[4]), "side": c(STONE[2])})
	st.box(Vector3(xc - ww * 0.5 - 0.35, y0 + wh + 0.1, 0.0), Vector3(ww + 0.7, 0.32, 0.3),
		{"front": c(STONE[3]), "top": c(SNOW[4]), "side": c(STONE[2]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	var ctr := Vector3(xc, y0 + wh * 0.5, 0.01)
	var n := Vector3.BACK
	if lit:
		var gll := K("glass_lit")
		var warm: String = GLOW[rng.randi_range(1, 3)]
		gll.face(ctr, n, Vector3.UP, ww * 0.5, wh * 0.5, c(warm), 1.0)
		var cur := c(OCHRE[3])
		gll.face(ctr + Vector3(-ww * 0.36, 0, 0.003), n, Vector3.UP, ww * 0.14, wh * 0.5, cur, 0.8)
		gll.face(ctr + Vector3(ww * 0.36, 0, 0.003), n, Vector3.UP, ww * 0.14, wh * 0.5, cur, 0.8)
	else:
		var gl := K("glass")
		var dark := c(VIOLET[0]) if rng.randf() < 0.6 else c(NIGHT[3])
		gl.face(ctr, n, Vector3.UP, ww * 0.5, wh * 0.5, dark)
		gl.face(ctr + Vector3(0, wh * 0.33, 0.004), n, Vector3.UP, ww * 0.42, wh * 0.08, c(STEEL[2]))
	var m := K("metal")
	var bar := c(NIGHT[2]) if lit else c(STONE[1])
	m.face(ctr + Vector3(0, wh * 0.18, 0.006), n, Vector3.UP, ww * 0.5, 0.045, bar)
	m.face(ctr + Vector3(0, 0, 0.006), n, Vector3.UP, 0.04, wh * 0.5, bar)


func _build_street() -> void:
	# near-left block (archive side): facade x = -12 facing +x, running from z = 0 to NEAR_LEFT_END
	_frame(Vector3(-STREET_HALF, 0, 0), Vector3(0, 0, -1))
	_tenement(-NEAR_LEFT_END, 11, STONE[1], 0.22, {"no_balconies": true})
	# right block: facade x = +12 facing -x (local x runs towards +z)
	_frame(Vector3(STREET_HALF, 0, RIGHT_BLOCK_END), Vector3(0, 0, 1))
	_tenement(-RIGHT_BLOCK_END, 23, STONE[2], 0.3)
	# family block, street side (beyond the chamfer)
	_frame(Vector3(-STREET_HALF, 0, CHAMFER_B.z), Vector3(0, 0, -1))
	_tenement(CHAMFER_B.z - FAMILY_BLOCK_END, 37, STONE[2], 0.28)
	# family block, cross-street side (faces the camera, +z): from x = -60 to the chamfer
	_frame(Vector3(-60.0, 0, CHAMFER_A.z), Vector3(1, 0, 0))
	_tenement(CHAMFER_A.x + 60.0, 41, STONE[1], 0.35, {"skip_ground": [9, 10]})
	_world()
	var p := K("plaster")
	# back wall of the near-left block on the cross street and end walls at the plaza
	p.box(Vector3(-60.0, 0.0, NEAR_LEFT_END - 0.1), Vector3(48.0, 21.2, 14.0), {"front": c(VIOLET[1]),
		"side": c(VIOLET[1]), "top": c(SNOW[3])}, Kit.FACES_NO_BOTTOM & ~Kit.FACE_NZ)
	p.box(Vector3(-40.0, 0.0, FAMILY_BLOCK_END - 18.0), Vector3(28.0, 21.2, 18.0), {"front": c(STONE[0]),
		"side": c(STONE[0]), "top": c(SNOW[3])})
	# archive facade (behind the camera at the end of h1): street-side face only
	p.box(Vector3(-40.0, 0.0, -0.1), Vector3(80.0, 24.0, 0.1), c(STONE[1]), Kit.FACE_NZ)


func _build_family_corner() -> void:
	# Chamfered corner of the family's block (faces the camera diagonally): sealed door, lamp, lit windows.
	var along := CHAMFER_B - CHAMFER_A
	var L := along.length()
	_frame(CHAMFER_A, along)
	var p := K("plaster")
	var st := K("stone")
	var height := GROUND_H + FLOOR_H * FLOORS
	p.quad(Vector3(0, 0, 0), Vector3(0, height, 0), Vector3(L, height, 0), Vector3(L, 0, 0), c(STONE[2]))
	st.box(Vector3(-0.4, height - 0.9, 0.0), Vector3(L + 0.8, 0.9, 0.75), {"front": c(STONE[2]),
		"top": c(SNOW[4]), "side": c(STONE[1]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	for f in range(FLOORS + 1):
		var y := GROUND_H + f * FLOOR_H - 0.25
		st.box(Vector3(0.0, y, 0.0), Vector3(L, 0.3, 0.22), {"front": c(STONE[3]), "top": c(SNOW[4])})
	st.box(Vector3(0.0, 0.0, 0.0), Vector3(L, GROUND_H, 0.18), {"front": c(STONE[1]), "top": c(SNOW[3])})
	var gy := 0.6
	while gy < GROUND_H - 0.4:
		st.box(Vector3(0.0, gy, 0.18), Vector3(L, 0.05, 0.01), c(STONE[0]), Kit.FACE_PZ)
		gy += 0.62
	var roof := K("roof")
	roof.quad(Vector3(0.0, height, 0.75), Vector3(0.0, height + 4.2, -3.2), Vector3(L, height + 4.2, -3.2),
		Vector3(L, height, 0.75), c(STEEL[1]))
	# sealed door (texture) with stone surround, step and the warm lamp above
	var dx := L * 0.5 - 0.5
	var dw := 1.2
	var dh := 2.3
	var dk := K("door")
	dk.quad(Vector3(dx - dw * 0.5, 0.16, 0.2), Vector3(dx - dw * 0.5, 0.16 + dh, 0.2),
		Vector3(dx + dw * 0.5, 0.16 + dh, 0.2), Vector3(dx + dw * 0.5, 0.16, 0.2), Color.WHITE)
	st.box(Vector3(dx - dw * 0.5 - 0.22, 0.16, 0.18), Vector3(0.22, dh + 0.1, 0.16), c(STONE[3]))
	st.box(Vector3(dx + dw * 0.5, 0.16, 0.18), Vector3(0.22, dh + 0.1, 0.16), c(STONE[3]))
	st.box(Vector3(dx - dw * 0.5 - 0.35, 0.16 + dh + 0.08, 0.18), Vector3(dw + 0.7, 0.26, 0.24),
		{"front": c(STONE[4]), "top": c(SNOW[4]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	st.box(Vector3(dx - 1.0, 0.16, 0.18), Vector3(2.0, 0.14, 0.5), {"front": c(STONE[2]), "top": c(SNOW[3])})
	var lamp := K("lamp")
	var lp := Vector3(dx + 0.9, 0.16 + dh + 0.75, 1.15)
	lamp.box(lp - Vector3(0.11, 0.16, 0.11), Vector3(0.22, 0.26, 0.22), c(GLOW[3]), Kit.FACES_ALL, 1.0)
	var m := K("metal")
	m.box(lp + Vector3(-0.15, 0.1, -0.15), Vector3(0.3, 0.07, 0.3), {"front": c(NIGHT[2]), "top": c(SNOW[4])})
	m.box(lp + Vector3(-0.02, 0.13, -1.15), Vector3(0.04, 0.04, 1.15), c(NIGHT[2]))
	m.box(lp + Vector3(-0.02, -0.5, -1.15), Vector3(0.04, 0.66, 0.04), c(NIGHT[2]))
	# ground floor: lit window right of the door (the neighbours), notice board left of it
	_window(dx + 2.25, 1.35, 1.0, 2.0, 0, 0.0, 1)
	var po := K("poster")
	po.quad(Vector3(dx - 1.95, 1.0, 0.2), Vector3(dx - 1.95, 1.9, 0.2), Vector3(dx - 1.3, 1.9, 0.2),
		Vector3(dx - 1.3, 1.0, 0.2), Color.WHITE)
	# upper floors: two windows each; the one above the family (floor 1, right) is the story window
	for f in range(1, FLOORS + 1):
		for s: float in [-1.0, 1.0]:
			var xc: float = dx + s * 1.75
			var y0 := GROUND_H + (f - 1) * FLOOR_H + 0.95
			if f == 1 and s > 0.0:
				_story_window(xc, y0)
			else:
				_window(xc, y0, 1.05, 2.1, f, 0.3 if f > 1 else 0.0)
	# people (sprites) around the door, standing on the corner apron (y = 0.16)
	var xf := _xf
	var fam := func(x: float, z: float) -> Vector3: return xf * Vector3(x, 0.16, z)
	people_spec.append({"role": "suitcase_b", "pos": fam.call(dx + 0.75, 1.0), "flip": true,
		"file": "res://assets/architecture/great_hall/props/suitcase_b.png"})
	people_spec.append({"role": "berlin_father", "pos": fam.call(dx + 1.35, 1.6), "flip": false})
	people_spec.append({"role": "suitcase_a", "pos": fam.call(dx + 2.05, 2.2), "flip": false,
		"file": "res://assets/architecture/great_hall/props/suitcase_a.png"})
	people_spec.append({"role": "berlin_mother", "pos": fam.call(dx + 2.75, 1.75), "flip": true})
	people_spec.append({"role": "berlin_child", "pos": fam.call(dx + 3.15, 2.6), "flip": false})
	people_spec.append({"role": "bundle", "pos": fam.call(dx + 3.7, 1.5), "flip": false,
		"file": "res://assets/architecture/great_hall/props/bundle.png"})
	stats["door_world"] = xf * Vector3(dx, 1.3, 0.2)
	_world()


func _story_window(xc: float, y0: float) -> void:
	# the window that closes in h3 (own mesh + material so it can be switched off)
	var ww := 1.05
	var wh := 2.1
	var st := K("stone")
	st.box(Vector3(xc - ww * 0.5 - 0.3, y0 - 0.2, 0.0), Vector3(ww + 0.6, 0.14, 0.24),
		{"front": c(STONE[3]), "top": c(SNOW[4])})
	st.box(Vector3(xc - ww * 0.5 - 0.35, y0 + wh + 0.1, 0.0), Vector3(ww + 0.7, 0.32, 0.3),
		{"front": c(STONE[3]), "top": c(SNOW[4]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	var kit := Kit.new()
	kit.xf = _xf
	var ctr := Vector3(xc, y0 + wh * 0.5, 0.01)
	var n := Vector3.BACK
	kit.face(ctr, n, Vector3.UP, ww * 0.5, wh * 0.5, c(GLOW[2]), 1.0)
	kit.face(ctr + Vector3(-ww * 0.36, 0, 0.004), n, Vector3.UP, ww * 0.14, wh * 0.5, c(OCHRE[3]), 0.8)
	kit.face(ctr + Vector3(ww * 0.36, 0, 0.004), n, Vector3.UP, ww * 0.14, wh * 0.5, c(OCHRE[3]), 0.8)
	kit.face(ctr + Vector3(0, wh * 0.18, 0.008), n, Vector3.UP, ww * 0.5, 0.045, c(NIGHT[2]))
	kit.face(ctr + Vector3(0, 0, 0.008), n, Vector3.UP, 0.04, wh * 0.5, c(NIGHT[2]))
	story_window = MeshInstance3D.new()
	story_window.name = "StoryWindow"
	story_window.mesh = kit.commit()
	story_window_mat = _toon({"flag": 0.75, "emission_energy": 1.0, "toon_steps": 3.0})
	story_window.material_override = story_window_mat
	root.add_child(story_window)


# ============================================================================== furniture
func _loudspeaker_pole(base: Vector3, tall: float = 8.5) -> void:
	_world()
	var m := K("metal")
	m.pillar(base.x, base.z, 0.0, 0.22, 0.22, tall, {"front": c(NIGHT[3]), "side": c(NIGHT[2]),
		"top": c(SNOW[4])})
	m.pillar(base.x, base.z, 0.0, 0.42, 0.42, 1.1, {"front": c(STEEL[1]), "side": c(STEEL[0]),
		"top": c(SNOW[4])})
	m.box(Vector3(base.x - 0.2, 2.6, base.z - 0.16), Vector3(0.4, 0.55, 0.32), {"front": c(STEEL[1]),
		"top": c(SNOW[4])})
	m.box(Vector3(base.x - 0.9, tall - 0.5, base.z - 0.06), Vector3(1.8, 0.12, 0.12), c(NIGHT[2]))
	for s: float in [-1.0, 1.0]:
		var hx: float = base.x + s * 0.75
		for k in 4:
			var r := 0.12 + k * 0.09
			var z := base.z + (0.1 + k * 0.17)
			m.box(Vector3(hx - r, tall - 0.75 - r * 0.6, z - 0.09), Vector3(r * 2.0, r * 1.6, 0.18),
				{"front": c(STEEL[2] if k == 3 else STEEL[1]), "side": c(STEEL[0]), "top": c(SNOW[3])})


func _street_lamp(base: Vector3, lit: bool) -> void:
	_world()
	var m := K("metal")
	m.pillar(base.x, base.z, 0.0, 0.16, 0.16, 4.4, {"front": c(NIGHT[3]), "side": c(NIGHT[2])})
	m.pillar(base.x, base.z, 0.0, 0.34, 0.34, 0.7, c(NIGHT[2]))
	m.pillar(base.x, base.z, 4.4, 0.62, 0.62, 0.08, {"front": c(NIGHT[2]), "top": c(SNOW[4])})
	if lit:
		K("lamp").box(Vector3(base.x - 0.24, 4.48, base.z - 0.24), Vector3(0.48, 0.55, 0.48), c(GLOW[2]),
			Kit.FACES_ALL, 1.0)
	else:
		m.box(Vector3(base.x - 0.24, 4.48, base.z - 0.24), Vector3(0.48, 0.55, 0.48), c(VIOLET[1]))
	m.pillar(base.x, base.z, 5.03, 0.66, 0.66, 0.12, {"front": c(NIGHT[2]), "top": c(SNOW[4])})


func _build_street_furniture() -> void:
	_loudspeaker_pole(Vector3(-9.6, 0, -9.0))
	_loudspeaker_pole(Vector3(10.3, 0, -18.0))
	_loudspeaker_pole(Vector3(6.2, 0, PLAZA_EDGE - 5.5), 9.0)
	_street_lamp(Vector3(-9.4, 0, -4.0), true)
	_street_lamp(Vector3(9.6, 0, -42.0), false)
	# advertising column (Litfasssaeule) on the right sidewalk with patchy posters
	_world()
	var colm := K("metal")
	var cc := Vector3(9.7, 0, -30.0)
	colm.lathe(cc, [Vector2(0.72, 0.0), Vector2(0.72, 0.5)], 12, func(_i, _j): return c(STONE[1]))
	var poster_cols := [SNOW[3], OCHRE[2], SNOW[2], STEEL[3], STONE[4], NIGHT[3]]
	colm.lathe(cc, [Vector2(0.66, 0.5), Vector2(0.66, 1.8), Vector2(0.66, 3.2)], 12,
		func(i, j): return c(poster_cols[(i * 2 + j * 3) % poster_cols.size()]))
	colm.lathe(cc, [Vector2(0.8, 3.2), Vector2(0.8, 3.45), Vector2(0.45, 3.85), Vector2(0.0, 3.95)], 12,
		func(_i, j): return c(SNOW[4]) if j >= 1 else c(STEEL[1]))
	# the guard at the plaza edge under the loudspeaker, facing the family
	people_spec.append({"role": "guard", "pos": Vector3(1.2, 0.0, PLAZA_EDGE - 2.6), "flip": true})
	# passers-by on the plaza (medium ~110 m, small ~200-260 m): the ordinary city keeps moving
	var crowd := [
		[Vector3(-14.0, 0.0, -128.0), "m", 0, false], [Vector3(30.0, 0.0, -134.0), "m", 1, true],
		[Vector3(32.0, 0.0, -134.5), "m", 3, true],
		[Vector3(-30.0, 0.0, -215.0), "s", 2, false], [Vector3(-27.5, 0.0, -216.0), "s", 3, false],
		[Vector3(-25.0, 0.0, -214.0), "s", 4, true], [Vector3(64.0, 0.0, -236.0), "s", 5, true],
		[Vector3(66.5, 0.0, -237.0), "s", 6, false], [Vector3(69.0, 0.0, -235.5), "s", 2, true],
		[Vector3(10.0, 0.0, -250.0), "s", 7, false], [Vector3(12.5, 0.0, -251.0), "s", 3, true],
		[Vector3(15.0, 0.0, -250.5), "s", 4, false], [Vector3(17.5, 0.0, -251.5), "s", 0, true],
		[Vector3(20.0, 0.0, -250.2), "s", 1, false], [Vector3(-8.0, 0.0, -262.0), "s", 5, false],
	]
	for e in crowd:
		var pos: Vector3 = e[0]
		var sz: String = e[1]
		var idx: int = e[2]
		people_spec.append({"role": "crowd_%s%d" % [sz, idx], "pos": pos, "flip": e[3],
			"file": "res://assets/architecture/great_hall/people/crowd_%s%d.png" % [sz, idx]})


# ============================================================================== wires
func _build_wires() -> void:
	_world()
	var w := K("wires", Mesh.PRIMITIVE_LINES)
	var dark := c(NIGHT[1])
	var zs := [-6.0, -30.0, -54.0]
	var track_x := [-2.9, 3.4]
	var prev := {}
	for z: float in zs:
		w.cable(Vector3(-11.9, 7.9, z), Vector3(11.9, 7.9, z), 0.55, dark)
		for tx: float in track_x:
			var p := Vector3(tx, 6.3, z)
			if prev.has(tx):
				w.cable(prev[tx], p, 0.18, dark)
			prev[tx] = p
	# last span on a centre mast at the plaza edge, then the wires follow the curve to the right
	var mast := K("metal")
	mast.pillar(0.3, PLAZA_EDGE - 2.0, 0.0, 0.3, 0.3, 8.2, {"front": c(NIGHT[3]), "side": c(NIGHT[2]),
		"top": c(SNOW[4])})
	mast.box(Vector3(-3.4, 7.6, PLAZA_EDGE - 2.08), Vector3(7.4, 0.16, 0.16), c(NIGHT[2]))
	for tx: float in track_x:
		var p := Vector3(tx, 6.3, PLAZA_EDGE - 2.0)
		w.cable(prev[tx], p, 0.2, dark)
		w.cable(p, Vector3(tx + 26.0, 6.3, PLAZA_EDGE - 36.0), 0.4, dark)
	w.cable(Vector3(6.2, 8.6, PLAZA_EDGE - 5.5), Vector3(11.95, 10.4, PLAZA_EDGE + 6.0), 0.4, dark)
	w.cable(Vector3(6.2, 8.6, PLAZA_EDGE - 5.5), Vector3(-11.95, 9.6, FAMILY_BLOCK_END + 4.0), 1.2, dark)
	w.cable(Vector3(10.3, 8.1, -18.0), Vector3(-9.6, 8.1, -9.0), 0.9, dark)
	# tram rails (1 px lines) curving away to the right at the plaza edge
	for tx: float in track_x:
		for g: float in [-0.72, 0.72]:
			var x0: float = tx + g
			var pts := []
			var z := 2.0
			while z > -120.0:
				var x := x0
				if z < PLAZA_EDGE:
					var k := (PLAZA_EDGE - z) / 40.0
					x += 34.0 * k * k
				pts.append(Vector3(x, 0.02, z))
				z -= 2.0
			for i in pts.size() - 1:
				w.seg(pts[i], pts[i + 1], c(NIGHT[2]))


func _build_tram() -> void:
	# a waiting tram on the curve at the right edge of the frame: ordinary life, warm windows
	var z0 := PLAZA_EDGE - 19.0
	var k := (PLAZA_EDGE - z0) / 40.0
	var x0 := 3.4 + 34.0 * k * k
	var dirv := Vector3(34.0 * 2.0 * k / 40.0, 0, -1.0).normalized()
	_frame(Vector3(x0, 0.0, z0) - dirv * 6.0, dirv)
	var b := K("metal")
	var L := 12.0
	var W := 2.2
	b.box(Vector3(0.0, 0.45, -W * 0.5), Vector3(L, 2.75, W), {"front": c(OCHRE[1]), "side": c(OCHRE[0]),
		"top": c(SNOW[4])}, Kit.FACES_ALL)
	b.box(Vector3(0.0, 0.25, -W * 0.5 + 0.1), Vector3(L, 0.25, W - 0.2), c(NIGHT[1]))
	b.box(Vector3(-0.15, 1.2, -W * 0.5 - 0.02), Vector3(L + 0.3, 0.12, W + 0.04), c(SNOW[3]), Kit.FACES_ALL)
	b.box(Vector3(0.3, 3.2, -0.6), Vector3(L - 0.6, 0.18, 1.2), {"front": c(STEEL[1]), "top": c(SNOW[4])})
	var x := 0.8
	var i := 0
	while x < L - 1.2:
		var lit := i != 3
		var col := c(GLOW[2]) if lit else c(VIOLET[0])
		for side: float in [-1.0, 1.0]:
			var zz: float = side * (W * 0.5 + 0.005)
			var n := Vector3(0, 0, side)
			if lit:
				K("glass_lit").face(Vector3(x + 0.55, 2.15, zz), n, Vector3.UP, 0.5, 0.55, col, 1.0)
			else:
				K("glass").face(Vector3(x + 0.55, 2.15, zz), n, Vector3.UP, 0.5, 0.55, col)
		x += 1.45
		i += 1
	K("wires", Mesh.PRIMITIVE_LINES).seg(Vector3(3.0, 3.4, 0.0), Vector3(7.8, 6.3, 0.0), c(NIGHT[1]))
	_world()


# ============================================================================== plaza
func _build_plaza() -> void:
	_world()
	var m := K("metal")
	var lamp := K("lamp")
	for side: float in [-1.0, 1.0]:
		var z := -170.0
		while z > -880.0:
			var x: float = HX + side * 72.0
			m.pillar(x, z, 0.0, 0.9, 0.9, 26.0, {"front": c(STEEL[1]), "side": c(STEEL[0]), "top": c(SNOW[3])})
			m.box(Vector3(x - 3.0, 26.0, z - 0.8), Vector3(6.0, 0.7, 1.6), c(STEEL[1]))
			lamp.box(Vector3(x - 2.6, 26.7, z + 0.1), Vector3(5.2, 1.6, 0.9), c(STEEL[5]), Kit.FACES_ALL, 1.0)
			z -= 150.0
	var bn := K("banner")
	for side: float in [-1.0, 1.0]:
		var z := -520.0
		while z > -930.0:
			var x: float = HX + side * 96.0
			m.pillar(x, z, 0.0, 0.6, 0.6, 34.0, {"front": c(NIGHT[3]), "side": c(NIGHT[2])})
			m.box(Vector3(x - 3.2, 33.0, z - 0.2), Vector3(6.4, 0.4, 0.4), c(NIGHT[2]))
			bn.quad(Vector3(x - 2.8, 9.0, z + 0.4), Vector3(x - 2.8, 33.0, z + 0.4), Vector3(x + 2.8, 33.0, z + 0.4),
				Vector3(x + 2.8, 9.0, z + 0.4), Color.WHITE)
			z -= 102.0
	for side: float in [-1.0, 1.0]:
		var z := -150.0
		while z > -960.0:
			m.pillar(HX + side * 46.0, z, 0.0, 0.5, 0.5, 1.4, {"front": c(STEEL[1]), "top": c(SNOW[4])})
			z -= 24.0


# ============================================================================== the hall
func _build_hall() -> void:
	_world()
	var hs := K("hall_far")
	var front_wall := c(STONE[1])
	var pil := c(STONE[3])
	var pil_side := c(STONE[2])
	var recess := c(VIOLET[2])
	var w := 320.0
	var x0 := HX - w * 0.5
	var x1 := HX + w * 0.5
	var zf := HZ
	var depth := 320.0
	var top := 66.0
	hs.box(Vector3(x0, 0.0, zf - depth), Vector3(w, top, depth), {"front": recess, "side": recess,
		"top": c(SNOW[3])})
	hs.box(Vector3(x0 - 2.0, 0.0, zf - depth - 2.0), Vector3(w + 4.0, 8.0, depth + 4.0), {"front": front_wall,
		"side": c(STONE[0]), "top": c(SNOW[4])})
	# pilaster rhythm on the front face, aligned to whole pixels at the final camera pose
	var ppm := _px_per_m(zf + 2.5)
	var period_px := 12.0
	var pil_px := 5.0
	var axis_px := roundf(_screen_x(HX, zf + 2.5))
	var n_pil := 0
	for k in range(-15, 16):
		var left_px := axis_px + k * period_px - floorf(pil_px * 0.5)
		var xa := _world_x_for_px(left_px, zf + 2.5)
		var xb := _world_x_for_px(left_px + pil_px, zf + 2.5)
		if xa > x0 + 30.0 and xb < x1 - 30.0 and absi(k) > 4:
			wash_x_podium.append((xa + xb) * 0.5)
			hs.box(Vector3(xa, 8.0, zf), Vector3(xb - xa, top - 8.0, 2.5), {"front": pil, "side": pil_side,
				"top": c(SNOW[4])})
			hs.box(Vector3(xa - 0.6, top - 4.0, zf), Vector3(xb - xa + 1.2, 4.0, 3.0), {"front": c(STONE[4]),
				"side": pil_side, "top": c(SNOW[4])})
			n_pil += 1
	stats["pilaster_period_m"] = period_px / ppm
	for s: float in [-1.0, 1.0]:
		var cx: float = x0 if s < 0 else x1 - 30.0
		hs.box(Vector3(cx, 8.0, zf), Vector3(30.0, top - 8.0, 3.0), {"front": front_wall, "side": pil_side,
			"top": c(SNOW[4])})
	var zz := zf - 10.0
	while zz > zf - depth + 10.0:
		for s: float in [-1.0, 1.0]:
			var sx: float = x0 - 2.5 if s < 0 else x1
			hs.box(Vector3(sx, 8.0, zz - 3.0), Vector3(2.5, top - 8.0, 6.0), {"front": pil_side, "side": pil,
				"top": c(SNOW[4])})
		zz -= 14.0
	hs.box(Vector3(x0 - 3.5, top, zf - depth - 3.5), Vector3(w + 7.0, 3.5, depth + 7.0), {"front": c(STONE[2]),
		"side": c(STONE[1]), "top": c(SNOW[4]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	hs.box(Vector3(x0 - 5.0, top + 3.5, zf - depth - 5.0), Vector3(w + 10.0, 4.5, depth + 10.0),
		{"front": c(STONE[3]), "side": c(STONE[2]), "top": c(SNOW[4]), "bottom": c(VIOLET[1])}, Kit.FACES_ALL)
	hs.box(Vector3(x0 + 2.0, top + 8.0, zf - depth + 2.0), Vector3(w - 4.0, 9.0, depth - 4.0),
		{"front": c(STONE[1]), "side": c(STONE[0]), "top": c(SNOW[3])})
	_build_portico(hs)
	_build_wings(hs)
	_build_dome()
	stats["pilasters"] = n_pil


func _build_portico(hs: Kit) -> void:
	var zf := HZ
	var pz := zf + 34.0
	var axis_px := roundf(_screen_x(HX, pz))
	var period_px := 15.0
	var pier_px := 7.0
	var n := 8
	var x_left := _world_x_for_px(axis_px - period_px * (n - 1) * 0.5 - pier_px * 0.5, pz)
	var x_right := _world_x_for_px(axis_px + period_px * (n - 1) * 0.5 + pier_px * 0.5, pz)
	for s in 4:
		var out := 8.0 - s * 2.0
		hs.box(Vector3(x_left - 10.0 - out, s * 2.0, zf), Vector3(x_right - x_left + 20.0 + out * 2.0, 2.0,
			34.0 + out + 4.0), {"front": c(STONE[2]), "side": c(STONE[1]), "top": c(SNOW[4])})
	var pier_d := 7.0
	var pier_top := 58.0
	for i in n:
		var lp := axis_px - period_px * (n - 1) * 0.5 + i * period_px - floorf(pier_px * 0.5)
		var xa := _world_x_for_px(lp, pz)
		var xb := _world_x_for_px(lp + pier_px, pz)
		wash_x_portico.append((xa + xb) * 0.5)
		hs.box(Vector3(xa, 8.0, pz - pier_d), Vector3(xb - xa, pier_top - 8.0, pier_d), {"front": c(STONE[3]),
			"side": c(STONE[2]), "top": c(SNOW[4])})
		hs.box(Vector3(xa, 8.0, pz - pier_d - 16.0), Vector3(xb - xa, pier_top - 8.0, pier_d),
			{"front": c(STONE[1]), "side": c(STONE[1])})
	var door := c(STEEL[0])
	for d: float in [-1.0, 0.0, 1.0]:
		var dx: float = HX + d * 34.0
		hs.box(Vector3(dx - 7.0, 8.0, zf), Vector3(14.0, 30.0, 0.6), {"front": door, "side": door})
		hs.box(Vector3(dx - 8.5, 38.0, zf), Vector3(17.0, 2.2, 1.0), {"front": c(STONE[2]), "top": c(SNOW[4])})
	hs.box(Vector3(x_left - 2.0, pier_top, zf), Vector3(x_right - x_left + 4.0, 9.0, 36.0),
		{"front": c(STONE[2]), "side": c(STONE[1]), "top": c(SNOW[4]), "bottom": c(VIOLET[0])}, Kit.FACES_ALL)
	hs.box(Vector3(x_left - 3.0, pier_top + 9.0, zf + 1.0), Vector3(x_right - x_left + 6.0, 2.2, 36.0),
		{"front": c(STONE[4]), "side": c(STONE[2]), "top": c(SNOW[4]), "bottom": c(VIOLET[0])}, Kit.FACES_ALL)
	hs.box(Vector3(x_left + 2.0, pier_top + 11.2, zf), Vector3(x_right - x_left - 4.0, 8.0, 30.0),
		{"front": c(STONE[1]), "side": c(STONE[0]), "top": c(SNOW[3])})
	var bn := K("banner")
	for i in range(1, n - 1, 2):
		var gap_px := axis_px - period_px * (n - 1) * 0.5 + i * period_px + period_px * 0.5
		var gx := _world_x_for_px(gap_px, pz)
		var hw := 3.4
		bn.quad(Vector3(gx - hw, 24.0, pz - 2.0), Vector3(gx - hw, pier_top - 1.0, pz - 2.0),
			Vector3(gx + hw, pier_top - 1.0, pz - 2.0), Vector3(gx + hw, 24.0, pz - 2.0), Color.WHITE)


func _build_wings(hs: Kit) -> void:
	# long lower wings with a colonnade of square piers (the rhythm runs out of the frame)
	var zf := HZ - 30.0
	var top := 40.0
	for s: float in [-1.0, 1.0]:
		var xa: float = HX + s * 160.0
		var xb: float = HX + s * 700.0
		var mn := minf(xa, xb)
		var mx := maxf(xa, xb)
		hs.box(Vector3(mn, 0.0, zf - 90.0), Vector3(mx - mn, top, 90.0), {"front": c(VIOLET[2]),
			"side": c(VIOLET[1]), "top": c(SNOW[3])})
		hs.box(Vector3(mn, top, zf - 92.0), Vector3(mx - mn, 4.0, 94.0), {"front": c(STONE[2]),
			"side": c(STONE[1]), "top": c(SNOW[4])})
		# pier rhythm aligned to whole pixels (period 10 px, pier 4 px)
		var ppm := _px_per_m(zf + 4.0)
		var px0 := _screen_x(mn, zf + 4.0)
		var px1 := _screen_x(mx, zf + 4.0)
		var kpx := ceilf(px0) + 2.0
		var nk := 0
		while kpx + 4.0 < px1 - 2.0:
			nk += 1
			var wa := _world_x_for_px(kpx, zf + 4.0)
			var wb := _world_x_for_px(kpx + 4.0, zf + 4.0)
			hs.box(Vector3(wa, 0.0, zf), Vector3(wb - wa, top, 4.0), {"front": c(STONE[2]), "side": c(STONE[1]),
				"top": c(SNOW[4])})
			if nk % 2 == 0 and absf((wa + wb) * 0.5 - HX) < 520.0:
				wash_x_wings.append((wa + wb) * 0.5)
			kpx += 10.0
		stats["wing_period_m"] = 10.0 / ppm


func _build_dome() -> void:
	var dk := K("patina")
	var st := K("hall_far")
	var cz := HZ - 160.0
	var base_y := 66.0 + 17.0
	var R := 106.0
	var ctr := Vector3(HX, 0, cz)
	var seg := 64
	st.lathe(ctr, [Vector2(R + 6.0, base_y), Vector2(R + 6.0, base_y + 4.0)], seg, func(_i, _j): return c(STONE[2]))
	st.lathe(ctr, [Vector2(R, base_y + 4.0), Vector2(R, base_y + 30.0)], seg, func(_i, _j): return c(VIOLET[2]))
	for i in seg:
		var a := TAU * (i + 0.5) / seg
		var d := Vector3(cos(a), 0, sin(a))
		if d.z < -0.35:
			continue
		var p := ctr + d * (R + 1.0) + Vector3(0, base_y + 17.0, 0)
		st.obox(p, Basis(Vector3.UP, -a + PI * 0.5), Vector3(2.4, 13.0, 1.2), {"front": c(STONE[3]),
			"side": c(STONE[2]), "top": c(STONE[3])})
	# drum cornice incl. its underside (an open underside lets the sky show through between pilasters)
	st.lathe(ctr, [Vector2(R - 0.5, base_y + 30.0), Vector2(R + 3.5, base_y + 30.0), Vector2(R + 3.5, base_y + 33.0),
		Vector2(R - 2.0, base_y + 35.0)], seg, func(_i, j): return c(SNOW[4]) if j == 2 else (c(VIOLET[1]) if j == 0
		else c(STONE[3])))
	var prof := []
	var rows := 11
	var H := 112.0
	var y0 := base_y + 35.0
	# the dome foot starts inside the drum cornice (no gaps between the 32 facets and the 64-gon ring)
	prof.append(Vector2(R + 1.5, y0 - 2.5))
	for j in range(1, rows + 1):
		var th := (PI * 0.5) * float(j) / rows
		var r := (R - 2.0) * cos(th)
		var y := y0 + H * sin(th)
		if j == rows:
			y = y0 + H * sin(th * 0.995)
		prof.append(Vector2(maxf(r, 13.0), y))
	var facets := 32
	dk.lathe(ctr, prof, facets, func(i, j):
		var t := float(j) / rows
		var cols := [PATINA[2], PATINA[2], PATINA[3], PATINA[3], PATINA[4], PATINA[4]]
		var idx := clampi(int(t * cols.size()), 0, cols.size() - 1)
		var base := Color(cols[idx])
		if i % 2 == 1:
			base = base.darkened(0.06)
		return base)
	for i in facets:
		var a := TAU * float(i) / facets
		var d := Vector3(cos(a), 0, sin(a))
		if d.z < -0.5:
			continue
		for j in rows:
			var pa: Vector2 = prof[j]
			var pb: Vector2 = prof[j + 1]
			var A := ctr + d * pa.x + Vector3(0, pa.y, 0)
			var B := ctr + d * pb.x + Vector3(0, pb.y, 0)
			var along := (B - A).normalized()
			var outn := (d * (pb.y - pa.y) - Vector3(0, pb.x - pa.x, 0)).normalized()
			var side := along.cross(outn).normalized()
			var basis := Basis(side, along, outn)
			var mid := (A + B) * 0.5 + outn * 0.9
			st.obox(mid, basis, Vector3(1.3, A.distance_to(B) * 0.5 + 0.4, 0.9), {"front": c(STONE[2]),
				"side": c(STONE[1]), "top": c(STONE[2])})
	var ly := (prof[rows] as Vector2).y - 1.0
	st.lathe(ctr, [Vector2(15.5, ly), Vector2(15.5, ly + 3.0)], 24, func(_i, _j): return c(STONE[2]))
	dk.lathe(ctr, [Vector2(12.0, ly + 3.0), Vector2(12.0, ly + 25.0)], 24,
		func(i, _j): return c(PATINA[0]) if i % 3 == 0 else c(PATINA[2]))
	st.lathe(ctr, [Vector2(11.5, ly + 25.0), Vector2(14.5, ly + 25.0), Vector2(14.5, ly + 27.5), Vector2(9.0, ly + 31.0),
		Vector2(2.4, ly + 32.0)], 24, func(_i, j): return c(SNOW[4]) if j >= 2 else (c(VIOLET[1]) if j == 0
		else c(STONE[3])))
	st.lathe(ctr, [Vector2(1.6, ly + 32.0), Vector2(1.6, ly + 39.0), Vector2(0.0, ly + 40.0)], 8,
		func(_i, _j): return c(STONE[2]))
	stats["dome_top_y"] = ly + 40.0


# ============================================================================== far city
func _build_far_city() -> void:
	_world()
	var p := K("hall_far")
	rng.seed = 77
	for i in 26:
		var side := -1.0 if i % 2 == 0 else 1.0
		var x := HX + side * rng.randf_range(260.0, 900.0)
		var z := rng.randf_range(-300.0, -1500.0)
		var w := rng.randf_range(40.0, 120.0)
		var d := rng.randf_range(30.0, 80.0)
		var h := rng.randf_range(18.0, 36.0)
		p.box(Vector3(x - w * 0.5, 0.0, z - d * 0.5), Vector3(w, h, d), {"front": c(VIOLET[1]), "side": c(VIOLET[0]),
			"top": c(SNOW[2])})
	for i in 14:
		var x := HX + rng.randf_range(-700.0, 700.0)
		var z := rng.randf_range(-1500.0, -2600.0)
		p.box(Vector3(x - 60.0, 0.0, z - 30.0), Vector3(rng.randf_range(60.0, 160.0), rng.randf_range(20.0, 45.0), 60.0),
			{"front": c(VIOLET[1]), "top": c(SNOW[2])})


# ============================================================================== lights
func _spot(parent: Node3D, from: Vector3, to: Vector3, col: Color, energy: float, rng_m: float, angle: float,
		atten: float = 0.0) -> SpotLight3D:
	var s := SpotLight3D.new()
	s.light_color = col
	s.light_energy = energy
	s.spot_range = rng_m
	s.spot_angle = angle
	s.spot_attenuation = atten
	s.spot_angle_attenuation = 0.6
	s.light_specular = 0.0
	s.light_cull_mask = LAYER_OUT
	parent.add_child(s)
	s.look_at_from_position(from, to, Vector3.UP)
	return s


func _build_lights() -> void:
	var lights := Node3D.new()
	lights.name = "Lights"
	root.add_child(lights)
	# Sun: low, behind the hall (slightly right): warm slivers on sun-facing sides + rim
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.light_color = c(GLOW[1])
	sun.light_energy = 1.0
	sun.shadow_enabled = true
	sun.shadow_blur = 0.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 2600.0
	sun.light_specular = 0.0
	sun.light_cull_mask = LAYER_OUT
	lights.add_child(sun)
	sun.look_at_from_position(Vector3.ZERO, Vector3(-0.07, -0.065, 1.0), Vector3.UP)
	# Cold sky fill from above / camera side (no shadows)
	var fill := DirectionalLight3D.new()
	fill.name = "SkyFill"
	fill.light_color = c(STEEL[4])
	fill.light_energy = 0.5
	fill.shadow_enabled = false
	fill.light_specular = 0.0
	fill.light_cull_mask = LAYER_OUT
	lights.add_child(fill)
	fill.look_at_from_position(Vector3.ZERO, Vector3(0.2, -0.8, -0.55), Vector3.UP)
	# Cold floodlights (blue-white): wall-washers at the foot of every portico pier and podium pilaster,
	# aimed steeply up the stone -> long vertical washes instead of round pools.
	var fl_col := Color(0.6, 0.76, 1.0)
	for xw: float in wash_x_portico:
		_spot(lights, Vector3(xw, 8.4, HZ + 34.0 + 9.0), Vector3(xw, 40.0, HZ + 34.0 - 1.0), fl_col, 6.0, 70.0, 6.5,
			0.0)
	for xw: float in wash_x_podium:
		_spot(lights, Vector3(xw, 8.4, HZ + 2.5 + 10.0), Vector3(xw, 46.0, HZ + 2.5 - 1.0), fl_col, 5.0, 80.0, 6.0, 0.0)
	for xw: float in wash_x_wings:
		_spot(lights, Vector3(xw, 0.6, HZ - 30.0 + 4.0 + 8.0), Vector3(xw, 28.0, HZ - 30.0 + 3.0), fl_col, 4.0, 55.0,
			7.0, 0.0)
	for side: float in [-1.0, 1.0]:
		var z := -170.0
		while z > -880.0:
			var x: float = HX + side * 72.0
			_spot(lights, Vector3(x, 27.0, z + 1.0), Vector3(x - side * 30.0, 0.0, z - 26.0), fl_col, 3.0, 90.0, 34.0)
			z -= 150.0
	# a cold work light on the guard's corner of the plaza
	_spot(lights, Vector3(5.4, 8.0, PLAZA_EDGE - 4.2), Vector3(3.0, 0.0, PLAZA_EDGE - 1.0), fl_col, 1.6, 14.0, 30.0,
		0.5)
	# the warm door lamp: the one warm focal light (family, sealed door)
	var door_lamp := OmniLight3D.new()
	door_lamp.name = "DoorLamp"
	door_lamp.light_color = c(GLOW[2])
	door_lamp.light_energy = 1.7
	door_lamp.omni_range = 6.0
	door_lamp.omni_attenuation = 1.2
	door_lamp.light_specular = 0.0
	door_lamp.light_cull_mask = LAYER_OUT
	lights.add_child(door_lamp)
	var along := (CHAMFER_B - CHAMFER_A)
	var nrm := along.normalized().cross(Vector3.UP).normalized()
	var dx := along.length() * 0.5 - 0.5
	door_lamp.global_position = CHAMFER_A + along.normalized() * (dx + 0.9) + nrm * 1.2 + Vector3(0, 3.1, 0)
	door_lamp.light_energy = 2.0
	door_lamp.omni_range = 4.6
	door_lamp.omni_attenuation = 1.1
	# character key light: only the people layer, so the family reads without blowing out the facade
	var key := OmniLight3D.new()
	key.name = "FamilyKey"
	key.light_color = c(GLOW[2])
	key.light_energy = 3.2
	key.omni_range = 7.0
	key.omni_attenuation = 0.6
	key.light_specular = 0.0
	key.light_cull_mask = LAYER_PEOPLE
	lights.add_child(key)
	key.global_position = CHAMFER_A + along.normalized() * (dx + 0.4) + nrm * 3.4 + Vector3(0, 3.0, 0)
	var gkey := OmniLight3D.new()
	gkey.name = "GuardKey"
	gkey.light_color = Color(0.62, 0.78, 1.0)
	gkey.light_energy = 2.2
	gkey.omni_range = 6.0
	gkey.omni_attenuation = 0.6
	gkey.light_specular = 0.0
	gkey.light_cull_mask = LAYER_PEOPLE
	lights.add_child(gkey)
	gkey.global_position = Vector3(3.6, 5.5, PLAZA_EDGE - 4.5)
	# warm bounce from the lit snow apron and the neighbours' window: keeps the family readable
	var bounce := OmniLight3D.new()
	bounce.name = "FamilyBounce"
	bounce.light_color = c(GLOW[1])
	bounce.light_energy = 0.7
	bounce.omni_range = 4.5
	bounce.omni_attenuation = 1.0
	bounce.light_specular = 0.0
	bounce.light_cull_mask = LAYER_OUT
	lights.add_child(bounce)
	bounce.global_position = CHAMFER_A + along.normalized() * (dx + 3.4) + nrm * 3.6 + Vector3(0, 0.9, 0)
	for pos: Vector3 in [Vector3(-9.4, 4.75, -14.0), Vector3(-9.4, 4.75, NEAR_LEFT_END + 1.5)]:
		var o := OmniLight3D.new()
		o.light_color = c(GLOW[1])
		o.light_energy = 1.0
		o.omni_range = 6.0
		o.omni_attenuation = 1.0
		o.light_specular = 0.0
		o.light_cull_mask = LAYER_OUT
		lights.add_child(o)
		o.global_position = pos
	var desk := OmniLight3D.new()
	desk.name = "DeskLamp"
	desk.light_color = c(GLOW[3])
	desk.light_energy = 1.5
	desk.omni_range = 1.5
	desk.omni_attenuation = 1.0
	desk.light_specular = 0.0
	desk.light_cull_mask = LAYER_IN
	lights.add_child(desk)
	desk.global_position = Vector3(WIN_X + 0.82, 7.58, 0.95)
	var win := SpotLight3D.new()
	win.light_color = c(STEEL[3])
	win.light_energy = 1.2
	win.spot_range = 6.0
	win.spot_angle = 30.0
	win.spot_attenuation = 0.5
	win.light_specular = 0.0
	win.light_cull_mask = LAYER_IN
	lights.add_child(win)
	win.look_at_from_position(Vector3(WIN_X, 10.0, -0.5), Vector3(WIN_X, 6.5, 3.0), Vector3.UP)
