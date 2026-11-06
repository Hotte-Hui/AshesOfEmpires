extends Node3D
## The armoured column of L_M1_Parade (owner: parade), built by parade_set.gd (_build_vehicles) and driven by its
## update().  Original fictional 1960s designs (no copy of a real vehicle), procedural (hall_mesh_kit.gd),
## deterministic, toon-lit like the rest of the set (pixel3d_toon) and palette-snapped by pixel3d_post.
##   * Main battle tank: welded hull with a steep glacis and sponsons over the tracks, cast turret with bustle,
##     mantlet with dust cover, long gun with fume extractor and double-baffle muzzle brake, commander's cupola
##     with vision blocks and the loader's hatch -- both lids open, the crew out to the chest (faceless shadow
##     under the padded helmets) -- 6 road wheels, rear sprocket, front idler, 3 return rollers, segmented
##     tracks, fenders with stowage boxes, tools, fuel tanks and tow cables, headlights in wire guards, spare
##     track links, rear drums and exhaust louvres, smoke dischargers, stowage basket with a tarp, 2 whips.
##   * Half-track troop carrier: armoured bonnet with radiator grille and unditching roller, cab with visors and
##     a pintle MG, open troop compartment with ten seated soldiers (helmets, rifles upright, two rows facing
##     each other), steerable front wheels under curved mudguards, track unit with front sprocket, stowage,
##     jerry cans, one whip.
## Column: two files 7 m apart in the lane; the far file trails by half a pitch (a staggered column, so the knee
## height camera p3 sees steel in every gap): 7 tanks on the near (crowd) side, 7 half-tracks with their seated
## infantry on the far (tribune) side -- the lower carriers show in the gaps between the tanks.  Near-file vehicle j
## keeps the old timing x = x0 - j * pitch + v * t (vehicle 0 passes the p3 camera at ~14 s).
## Rendering: one MultiMesh per part and vehicle type (body, track wraps, 4 straight track runs, each wheel kind,
## whips) -> ~20 draw calls for all 14 vehicles; per frame only instance transforms are written (no allocations).
## Tracks: the straight runs are instances shifted along their run by fmod(distance, link pitch) in the direction
## the belt flows (top run forward, bottom run backward relative to the hull), so the links scroll exactly with
## the ground; the wraps around sprocket / idler are static; wheels turn by distance / radius; the sprung body
## judders a little above the running gear; whips lean back and sway.
## Detail maps: assets/architecture/parade/vehicles/ (tools/pixelgen/gen_parade_vehicles.py).

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const TOON := preload("res://assets/shaders/pixel3d_toon.gdshader")
const DIR := "res://assets/architecture/parade/vehicles/"

const NIGHT := ["#120C14", "#1B1520", "#211623", "#2A2130"]
const VIOLET := ["#25202B", "#342F37", "#443B43", "#57494D"]
const STONE := ["#4A3A35", "#5F4A40", "#7A5E4E", "#94735C", "#AE8A6C", "#C9A585"]
const OCHRE := ["#5F4530", "#735145", "#8D5542", "#AF6C47", "#D07744", "#E5945A"]
const STEEL := ["#1E2329", "#2F363F", "#454E58", "#5F6973", "#7C8690", "#A3ACB4"]
const PATINA := ["#1E2E2C", "#2C4440", "#3E5D55", "#56776A", "#73927F"]
const SNOW := ["#6E6A73", "#8F8A92", "#B2ACB0", "#D2CCCB", "#ECE6E0"]

const PITCH := 0.1875            ## track link pitch (m) = 6 texels of track.png
const TILE := 1.5                ## track.png repeats every 1.5 m (8 links)
const TRACK_EDGE_V := 0.25       ## track.png rows 0..8 of 32 = outer edge of the links, below = tread face
## decals.png regions in texels (tools/pixelgen/gen_parade_vehicles.py DECALS)
const DEC_SIZE := Vector2(128, 64)
const DEC := {"white": Rect2(0, 0, 8, 8), "louvre": Rect2(8, 0, 32, 16), "tarp": Rect2(40, 0, 32, 16),
	"planks": Rect2(72, 0, 16, 16), "bolts": Rect2(88, 0, 32, 4), "weld": Rect2(88, 4, 32, 4),
	"visor": Rect2(0, 16, 32, 16), "radiator": Rect2(32, 16, 32, 24), "jerry": Rect2(64, 16, 12, 16),
	"lens": Rect2(80, 16, 8, 8), "glass": Rect2(88, 16, 8, 4)}
## wheels.png faces (UV rects)
const UV_ROAD := Rect2(0.0, 0.0, 0.25, 1.0)
const UV_SPROCKET := Rect2(0.25, 0.0, 0.25, 1.0)
const UV_IDLER := Rect2(0.5, 0.0, 0.25, 1.0)
const UV_FRONT := Rect2(0.75, 0.0, 0.25, 1.0)

const FILE_DZ := 3.5             ## the two files sit at z_lane +- 3.5 m
const ORDER := [[0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1]]   ## type ids per file: near = tanks, far = half-tracks
const DUST := preload("res://assets/architecture/parade/vehicles/vehicle_dust.gdshader")

## Running gear (local frame: +x forward, +y up, +z right = the side the barrier cameras see).
const TANK_RG := {"rear": Vector2(-3.02, 0.70), "rear_r": 0.33, "front": Vector2(3.02, 0.67), "front_r": 0.31,
	"rw": [-2.38, -1.44, -0.50, 0.44, 1.38, 2.32], "rw_y": 0.47, "rw_r": 0.36,
	"rr": [-1.90, -0.30, 1.30], "rr_r": 0.10, "tt": 0.11, "tw": 0.58, "tz": 1.36, "drive_rear": true}
const HT_RG := {"rear": Vector2(-2.72, 0.40), "rear_r": 0.23, "front": Vector2(0.55, 0.42), "front_r": 0.25,
	"rw": [-2.10, -1.42, -0.74, -0.06], "rw_y": 0.33, "rw_r": 0.26,
	"rr": [], "rr_r": 0.0, "tt": 0.07, "tw": 0.36, "tz": 0.86, "drive_rear": false}

var stats: Dictionary = {}
var speed := 2.8
var z_lane := -876.0
var vehs: Array = []             ## {"type": int, "x0": float, "z": float, "ph": float}
var types: Array = []            ## per type: {"veh": Array of vehicle ids, "parts": Array, "emit": Array}
var _m: Dictionary = {}          ## own materials
var S: Array = []
var N: Array = []
var V: Array = []
var K: Array = []
var O: Array = []
var P: Array = []
var W: Array = []


static func _cols(a: Array) -> Array:
	var r: Array = []
	for h in a:
		r.append(Color(h))
	return r


## cfg: {"z_lane", "x0", "speed", "pitch"} (parade_set constants).
func build(cfg: Dictionary) -> void:
	S = _cols(STEEL)
	N = _cols(NIGHT)
	V = _cols(VIOLET)
	K = _cols(STONE)
	O = _cols(OCHRE)
	P = _cols(PATINA)
	W = _cols(SNOW)
	z_lane = float(cfg.get("z_lane", -876.0))
	speed = float(cfg.get("speed", 2.8))
	var x0 := float(cfg.get("x0", -77.0))
	var pitch := float(cfg.get("pitch", 16.0))
	_make_materials()
	types = [{"veh": [], "parts": [], "emit": []},
		{"veh": [], "parts": [], "emit": []}]
	for f in 2:
		for j in (ORDER[f] as Array).size():
			var ti: int = ORDER[f][j]
			var vi := vehs.size()
			vehs.append({"type": ti, "x0": x0 - j * pitch - f * pitch * 0.5,
				"z": z_lane + (FILE_DZ if f == 0 else -FILE_DZ), "ph": float(vi) * 1.7})
			(types[ti]["veh"] as Array).append(vi)
	var t0 := Time.get_ticks_usec()
	_build_type(0, TANK_RG)
	_build_type(1, HT_RG)
	stats["vehicles"] = vehs.size()
	stats["vehicle_build_ms"] = snappedf((Time.get_ticks_usec() - t0) / 1000.0, 0.1)
	update(0.0)


func _make_materials() -> void:
	var dec: Texture2D = load(DIR + "decals.png") if ResourceLoader.exists(DIR + "decals.png") else null
	var trk: Texture2D = load(DIR + "track.png") if ResourceLoader.exists(DIR + "track.png") else null
	var whl: Texture2D = load(DIR + "wheels.png") if ResourceLoader.exists(DIR + "wheels.png") else null
	_m["body"] = _toon({"snow": 0.3, "snow_threshold": 0.82, "rim": 1.0, "rim_threshold": 0.5})
	_m["decal"] = _toon({"use_tex": dec != null, "albedo_tex": dec, "alpha_scissor": 0.5, "snow": 0.0,
		"rim": 1.0, "rim_threshold": 0.5, "toon_steps": 4.0})
	_m["track"] = _toon({"use_tex": trk != null, "albedo_tex": trk, "snow": 0.35, "snow_threshold": 0.86,
		"rim": 0.6})
	_m["wheel"] = _toon({"use_tex": whl != null, "albedo_tex": whl, "rim": 0.8, "toon_steps": 4.0})


func _toon(params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = TOON
	for k in params:
		m.set_shader_parameter(k, params[k])
	return m


# ------------------------------------------------------------------------------------------ per frame
func vehicle_pos(vi: int, t: float) -> Vector3:
	var v: Dictionary = vehs[vi]
	return Vector3(float(v["x0"]) + speed * t, 0.0, float(v["z"]))


func update(t: float) -> void:
	var s := speed * t
	var off := fposmod(s, PITCH)
	for tp in types:
		var vl: Array = tp["veh"]
		for part in tp["parts"]:
			var mm: MultiMesh = part["mm"]
			var kind: int = part["kind"]
			if kind == 0 or kind == 1:              # body (sprung, judders) / static running-gear parts
				for q in vl.size():
					var v: Dictionary = vehs[vl[q]]
					var y := 0.02 * sin(t * 9.0 + float(v["ph"])) if kind == 0 else 0.0
					mm.set_instance_transform(q, Transform3D(Basis.IDENTITY,
						Vector3(float(v["x0"]) + s, y, float(v["z"]))))
			elif kind == 2:                          # straight track run: links scroll along the belt
				var d: Vector3 = part["dir"] * off
				for q in vl.size():
					var v: Dictionary = vehs[vl[q]]
					mm.set_instance_transform(q, Transform3D(Basis.IDENTITY,
						Vector3(float(v["x0"]) + s, 0.0, float(v["z"])) + d))
			elif kind == 3:                          # wheels: turn by distance / radius
				var b := Basis(Vector3.BACK, -s / float(part["r"]))
				var lps: PackedVector3Array = part["lps"]
				var n := lps.size()
				for q in vl.size():
					var v: Dictionary = vehs[vl[q]]
					var o := Vector3(float(v["x0"]) + s, 0.0, float(v["z"]))
					for i in n:
						mm.set_instance_transform(q * n + i, Transform3D(b, o + lps[i]))
			elif kind == 4:                          # whips: lean back with the head wind, sway with the judder
				var lps: PackedVector3Array = part["lps"]
				var n := lps.size()
				for q in vl.size():
					var v: Dictionary = vehs[vl[q]]
					var ph := float(v["ph"])
					var o := Vector3(float(v["x0"]) + s, 0.02 * sin(t * 9.0 + ph), float(v["z"]))
					for i in n:
						var a := 0.13 + 0.07 * sin(t * 4.1 + ph + i * 1.3) + 0.025 * sin(t * 13.0 + ph * 2.0)
						var sd := 0.05 * sin(t * 3.3 + ph * 0.7 + i)
						mm.set_instance_transform(q * n + i,
							Transform3D(Basis(Vector3.BACK, a) * Basis(Vector3.RIGHT, sd), o + lps[i]))


## Powder snow thrown off the rear of every track and cold exhaust vapour: camera-facing dithered veils
## (vehicle_dust.gdshader), one MultiMesh for the whole column.  Each emitter [local point, kind 0 dust /
## 1 exhaust, count, period s, size] keeps `count` puffs cycling: a puff is born at the emitter, stays where it
## was born on the ground (drifting back and outward, the vapour rising), grows and thins out over one period.
## Everything is a pure function of t (seekable, deterministic); per frame only transforms + custom data.
var dust_mm: MultiMesh


func build_dust() -> void:
	var n := 0
	for vi in vehs.size():
		for e in types[int(vehs[vi]["type"])]["emit"]:
			n += int(e[2])
	var mat := ShaderMaterial.new()
	mat.shader = DUST
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	dust_mm = MultiMesh.new()
	dust_mm.transform_format = MultiMesh.TRANSFORM_3D
	dust_mm.use_custom_data = true
	dust_mm.mesh = quad
	dust_mm.instance_count = n
	var mi := MultiMeshInstance3D.new()
	mi.name = "Dust"
	mi.multimesh = dust_mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.custom_aabb = AABB(Vector3(-500.0, -2.0, z_lane - 30.0), Vector3(1000.0, 12.0, 60.0))
	add_child(mi)
	stats["dust_puffs"] = n
	update_dust(0.0)


func update_dust(t: float) -> void:
	if dust_mm == null:
		return
	var i := 0
	for vi in vehs.size():
		var ne: int = (types[int(vehs[vi]["type"])]["emit"] as Array).size()
		for ei in ne:
			var nq: int = types[int(vehs[vi]["type"])]["emit"][ei][2]
			for q in nq:
				puff_at(vi, ei, q, t)
				dust_mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, puff_pos))
				dust_mm.set_instance_custom_data(i, puff_cd)
				i += 1


## Puff q of emitter ei of vehicle vi at time t -> puff_pos (ground point under it), puff_cd (width m, height m,
## density, seed + 100 * kind).  Pure function of its arguments; writes members instead of returning an Array so
## the per-frame loop allocates nothing.
var puff_pos := Vector3.ZERO
var puff_cd := Color(0, 0, 0, 0)


func puff_at(vi: int, ei: int, q: int, t: float) -> void:
	var v: Dictionary = vehs[vi]
	var e: Array = types[int(v["type"])]["emit"][ei]
	var lp: Vector3 = e[0]
	var kind: int = e[1]
	var nq: int = e[2]
	var per: float = e[3]
	var sz: float = e[4]
	var o := float(q) * per / nq + vi * 0.37 + ei * 0.53
	var age := fposmod(t - o, per)
	var a := age / per
	var cyc := floorf((t - o) / per)
	var tb := t - age
	var x := float(v["x0"]) + speed * tb + lp.x
	var vz := float(v["z"])
	var w: float
	var h: float
	var dn: float
	if kind == 0:
		puff_pos = Vector3(x - age * 0.4, 0.0, vz + lp.z + signf(lp.z) * age * 0.15)
		w = lerpf(0.8, 2.4, sqrt(a)) * sz
		h = lerpf(0.55, 1.15, sqrt(a)) * sz
		# a dense clot of thrown snow that thins quickly; the inner track (towards the other file) throws less
		# past the hull
		dn = (1.0 if lp.z > 0.0 else 0.7) * smoothstep(0.0, 0.07, a) * pow(1.0 - a, 1.4)
	else:
		puff_pos = Vector3(x - age * 0.6, lp.y - 0.2 + age * 0.2, vz + lp.z + age * 0.2)
		w = lerpf(0.4, 1.8, sqrt(a)) * sz
		h = lerpf(0.35, 1.2, a) * sz
		dn = 0.5 * smoothstep(0.0, 0.1, a) * pow(1.0 - a, 1.7)
	if tb < 0.0:
		dn = 0.0
	var seed := fposmod(cyc * 0.618 + float(vi) * 0.31 + float(q) * 0.13 + float(ei) * 0.07, 1.0) * 31.0
	puff_cd = Color(w, h, dn, seed + 100.0 * kind)


# ------------------------------------------------------------------------------------------ assembly
func _mmi(mesh: Mesh, n: int, nm: String, shadows: bool) -> MultiMesh:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = n
	var mi := MultiMeshInstance3D.new()
	mi.name = nm
	mi.multimesh = mm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows \
		else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.custom_aabb = AABB(Vector3(-500.0, -60.0, z_lane - 30.0), Vector3(1000.0, 120.0, 60.0))
	add_child(mi)
	return mm


func _build_type(ti: int, rg: Dictionary) -> void:
	var tp: Dictionary = types[ti]
	var nv: int = (tp["veh"] as Array).size()
	var tag := "Tank" if ti == 0 else "HalfTrack"
	var parts: Array = tp["parts"]
	var tris := 0
	# body: plain steel surface + decal surface
	var k := Kit.new()
	var d := Kit.new()
	if ti == 0:
		_tank_body(k, d)
	else:
		_halftrack_body(k, d)
	var body := k.commit()
	body = d.commit(body)
	body.surface_set_material(0, _m["body"])
	if body.get_surface_count() > 1:
		body.surface_set_material(1, _m["decal"])
	tris += (k.count + d.count) / 3
	parts.append({"kind": 0, "mm": _mmi(body, nv, tag + "Body", true)})
	# tracks: belt around sprocket, idler and the end road wheels
	var belt := _belt(rg)
	var wraps := Kit.new()
	for a in belt["arcs"]:
		_track_arc(wraps, a, rg)
	var wm := wraps.commit()
	wm.surface_set_material(0, _m["track"])
	tris += wraps.count / 3
	parts.append({"kind": 1, "mm": _mmi(wm, nv, tag + "TrackWraps", true)})
	var li := 0
	for ln in belt["lines"]:
		var rk := Kit.new()
		_track_run(rk, ln, rg)
		var rm := rk.commit()
		rm.surface_set_material(0, _m["track"])
		tris += rk.count / 3
		var a2: Vector2 = ln["a"]
		var b2: Vector2 = ln["b"]
		var dv := (b2 - a2).normalized()
		parts.append({"kind": 2, "mm": _mmi(rm, nv, tag + "TrackRun%d" % li, true), "dir": Vector3(dv.x, dv.y, 0.0)})
		li += 1
	# wheels
	var tz: float = rg["tz"]
	var rw_lps := PackedVector3Array()
	for x in rg["rw"]:
		for sd: float in [-1.0, 1.0]:
			rw_lps.append(Vector3(float(x), float(rg["rw_y"]), sd * tz))
	var rw_r: float = rg["rw_r"]
	var rw_mesh := _wheel_mesh(rw_r, float(rg["tw"]) * 0.47, UV_ROAD, 0.085 if ti == 0 else 0.07, N[2], 0.035)
	_add_wheels(parts, rw_mesh, rw_lps, rw_r, nv, tag + "RoadWheels")
	var rear: Vector2 = rg["rear"]
	var front: Vector2 = rg["front"]
	var drive_rear: bool = rg["drive_rear"]
	var spr_lps := PackedVector3Array()
	var idl_lps := PackedVector3Array()
	for sd: float in [-1.0, 1.0]:
		var pr := Vector3(rear.x, rear.y, sd * tz)
		var pf := Vector3(front.x, front.y, sd * tz)
		spr_lps.append(pr if drive_rear else pf)
		idl_lps.append(pf if drive_rear else pr)
	var spr_r: float = rg["rear_r"] if drive_rear else rg["front_r"]
	var idl_r: float = rg["front_r"] if drive_rear else rg["rear_r"]
	_add_wheels(parts, _sprocket_mesh(spr_r, float(rg["tw"]) * 0.5 + 0.03), spr_lps, spr_r + float(rg["tt"]) * 0.5, nv,
		tag + "Sprockets")
	_add_wheels(parts, _wheel_mesh(idl_r, float(rg["tw"]) * 0.5 + 0.02, UV_IDLER, 0.07, S[2], 0.03), idl_lps,
		idl_r + float(rg["tt"]) * 0.5, nv, tag + "Idlers")
	if (rg["rr"] as Array).size() > 0:
		var rr_lps := PackedVector3Array()
		var top: Dictionary = belt["lines"][0]
		var ta: Vector2 = top["a"]
		var tb: Vector2 = top["b"]
		var rr_r: float = rg["rr_r"]
		for x in rg["rr"]:
			var u := (float(x) - ta.x) / (tb.x - ta.x)
			var y := lerpf(ta.y, tb.y, u) - float(rg["tt"]) * 0.5 - rr_r
			for sd: float in [-1.0, 1.0]:
				rr_lps.append(Vector3(float(x), y, sd * tz))
		_add_wheels(parts, _wheel_mesh(rr_r, 0.2, UV_ROAD, 0.04, S[1], 0.02), rr_lps, rr_r, nv, tag + "Rollers")
	if ti == 1:
		var fw := PackedVector3Array([Vector3(2.32, 0.45, -0.97), Vector3(2.32, 0.45, 0.97)])
		_add_wheels(parts, _wheel_mesh(0.45, 0.14, UV_FRONT, 0.10, N[2], 0.05), fw, 0.45, nv, tag + "FrontWheels")
	# whips
	var ant := _antenna_mesh(2.9 if ti == 0 else 2.4)
	var a_lps := PackedVector3Array([Vector3(-1.62, 2.38, -0.62), Vector3(-1.62, 2.38, 0.62)]) if ti == 0 \
		else PackedVector3Array([Vector3(-2.82, 1.88, -0.96)])
	parts.append({"kind": 4, "mm": _mmi(ant, nv * a_lps.size(), tag + "Whips", false), "lps": a_lps})
	# dust / vapour emitters [local point, kind 0 dust / 1 exhaust, count, period s, size] (update_dust)
	var x_back := minf(rear.x - float(rg["rear_r"]), float(rg["rw"][0]) - rw_r) - 0.15
	var dsz := 1.0 if ti == 0 else 0.72
	tp["emit"] = [[Vector3(x_back, 0.0, tz), 0, 5, 1.7, dsz], [Vector3(x_back, 0.0, -tz), 0, 5, 1.7, dsz]]
	if ti == 0:                                  # exhaust vapour trails low behind the rear drums
		(tp["emit"] as Array).append([Vector3(-3.9, 0.85, 0.0), 1, 4, 2.4, 1.0])
	else:                                        # muffler under the right running board
		(tp["emit"] as Array).append([Vector3(0.9, 0.5, 1.15), 1, 3, 2.0, 0.7])
	stats[tag.to_lower() + "_tris"] = tris


func _add_wheels(parts: Array, mesh: ArrayMesh, lps: PackedVector3Array, r: float, nv: int, nm: String) -> void:
	parts.append({"kind": 3, "mm": _mmi(mesh, nv * lps.size(), nm, false), "lps": lps, "r": r})


# ------------------------------------------------------------------------------------------ tracks
## Belt around [rear top wheel, front top wheel, front road wheel, rear road wheel] along the track midline,
## clockwise as seen from +z (the top run flows forward).  Returns {"lines": [{a, b, n}], "arcs": [{c, r, t0, sw}]}.
func _belt(rg: Dictionary) -> Dictionary:
	var h := float(rg["tt"]) * 0.5
	var rw: Array = rg["rw"]
	var circ := [[rg["rear"], float(rg["rear_r"]) + h], [rg["front"], float(rg["front_r"]) + h],
		[Vector2(float(rw[rw.size() - 1]), float(rg["rw_y"])), float(rg["rw_r"]) + h],
		[Vector2(float(rw[0]), float(rg["rw_y"])), float(rg["rw_r"]) + h]]
	var lines: Array = []
	for i in 4:
		var ca: Vector2 = circ[i][0]
		var ra: float = circ[i][1]
		var cb: Vector2 = circ[(i + 1) % 4][0]
		var rb: float = circ[(i + 1) % 4][1]
		var dd := cb - ca
		var dist := dd.length()
		var dh := dd / dist
		var perp := Vector2(-dh.y, dh.x)
		var a := (ra - rb) / dist
		var n := dh * a + perp * sqrt(maxf(0.0, 1.0 - a * a))
		lines.append({"a": ca + n * ra, "b": cb + n * rb, "n": n})
	var arcs: Array = []
	for i in 4:
		var nin: Vector2 = lines[(i + 3) % 4]["n"]
		var nout: Vector2 = lines[i]["n"]
		var t0 := atan2(nin.y, nin.x)
		var sw := fposmod(t0 - atan2(nout.y, nout.x), TAU)
		if sw > 0.01:
			arcs.append({"c": circ[i][0], "r": circ[i][1], "t0": t0, "sw": sw})
	return {"lines": lines, "arcs": arcs}


## One link-strip piece (both tracks) between midline points p0 -> p1 with outward normals n0 / n1 (x-y plane).
func _track_piece(k: Kit, p0: Vector2, p1: Vector2, n0: Vector2, n1: Vector2, u0: float, u1: float,
		rg: Dictionary) -> void:
	var h := float(rg["tt"]) * 0.5
	var tz: float = rg["tz"]
	var hw := float(rg["tw"]) * 0.5
	var o0 := p0 + n0 * h
	var o1 := p1 + n1 * h
	var i0 := p0 - n0 * h
	var i1 := p1 - n1 * h
	var nm := ((n0 + n1) * 0.5).normalized()
	var on := Vector3(nm.x, nm.y, 0.0)
	for sd: float in [-1.0, 1.0]:
		var za := sd * tz - hw
		var zb := sd * tz + hw
		var A := func(q: Vector2, z: float) -> Vector3: return Vector3(q.x, q.y, z)
		# tread face (outer) and inner face: grousers / guide horns, v across the width
		k.quad_uv_out(A.call(o0, za), A.call(o0, zb), A.call(o1, zb), A.call(o1, za), on, S[2],
			Vector2(u0, TRACK_EDGE_V), Vector2(u1, 1.0))
		k.quad_uv_out(A.call(i0, za), A.call(i0, zb), A.call(i1, zb), A.call(i1, za), -on, S[1],
			Vector2(u0, TRACK_EDGE_V), Vector2(u1, 1.0))
		# link edges on both sides of the track (end connectors), v from the tread side inwards
		for z: float in [za, zb]:
			var out := Vector3(0, 0, 1.0 if z > sd * tz else -1.0)
			k.quad_uv_out(A.call(o0, z), A.call(i0, z), A.call(i1, z), A.call(o1, z), out, S[2],
				Vector2(u0, 0.0), Vector2(u1, TRACK_EDGE_V))


## Straight run: mesh from one pitch behind its start to its end, so the scrolled instance always covers it.
func _track_run(k: Kit, ln: Dictionary, rg: Dictionary) -> void:
	var a: Vector2 = ln["a"]
	var b: Vector2 = ln["b"]
	var n: Vector2 = ln["n"]
	var dv := (b - a).normalized()
	var p0 := a - dv * PITCH
	var l := p0.distance_to(b)
	_track_piece(k, p0, b, n, n, 0.0, l / TILE, rg)


## Static wrap: one chord per link around the wheel.
func _track_arc(k: Kit, arc: Dictionary, rg: Dictionary) -> void:
	var c: Vector2 = arc["c"]
	var r: float = arc["r"]
	var t0: float = arc["t0"]
	var sw: float = arc["sw"]
	var nseg := maxi(1, int(round(sw * r / PITCH)))
	for i in nseg:
		var ta := t0 - sw * float(i) / nseg
		var tb := t0 - sw * float(i + 1) / nseg
		var na := Vector2(cos(ta), sin(ta))
		var nb := Vector2(cos(tb), sin(tb))
		var u0 := float(i % 8) * PITCH / TILE
		_track_piece(k, c + na * r, c + nb * r, na, nb, u0, u0 + PITCH / TILE, rg)


# ------------------------------------------------------------------------------------------ wheels / whips
## Symmetric wheel about its own z = 0 plane (the same mesh serves both sides): tyre / rim band, textured faces,
## protruding hubs.  hw = half width.
func _wheel_mesh(r: float, hw: float, uv: Rect2, hub_r: float, tyre: Color, hub_h: float) -> ArrayMesh:
	var k := Kit.new()
	var n := 16 if r > 0.2 else 10
	k.loft([Kit.ring(Vector3(0, 0, -hw), Vector3.RIGHT, Vector3.UP, r, r, n),
		Kit.ring(Vector3(0, 0, hw), Vector3.RIGHT, Vector3.UP, r, r, n)], tyre)
	for sd: float in [-1.0, 1.0]:
		k.disc_uv(Vector3(0, 0, sd * hw), Vector3(0, 0, sd), Vector3.UP, r, n, S[3], uv)
		k.cyl(Vector3(0, 0, sd * (hw - 0.01)), Vector3(0, 0, sd * (hw + hub_h)), hub_r, hub_r * 0.8, 8, S[3])
	var m := k.commit()
	m.surface_set_material(0, _m["wheel"])
	return m


## Drive sprocket: toothed rings (12 teeth) beside the textured face, hub.
func _sprocket_mesh(r: float, hw: float) -> ArrayMesh:
	var k := Kit.new()
	for sd: float in [-1.0, 1.0]:
		var pts: Array = []
		for i in 24:
			var a := TAU * float(i) / 24.0
			var rr := r + (0.05 if i % 2 == 0 else -0.01)
			pts.append(Vector2(cos(a) * rr, sin(a) * rr))
		k.prism(pts, Vector3.ZERO, Vector3.RIGHT, Vector3.UP, Vector3.BACK, sd * (hw - 0.09), sd * (hw - 0.03),
			{"front": S[2], "side": S[1]})
		k.disc_uv(Vector3(0, 0, sd * hw), Vector3(0, 0, sd), Vector3.UP, r * 0.96, 16, S[3], UV_SPROCKET)
		k.cyl(Vector3(0, 0, sd * (hw - 0.01)), Vector3(0, 0, sd * (hw + 0.05)), 0.09, 0.07, 8, S[3])
	k.loft([Kit.ring(Vector3(0, 0, -hw), Vector3.RIGHT, Vector3.UP, r * 0.96, r * 0.96, 16),
		Kit.ring(Vector3(0, 0, hw), Vector3.RIGHT, Vector3.UP, r * 0.96, r * 0.96, 16)], S[1])
	var m := k.commit()
	m.surface_set_material(0, _m["wheel"])
	return m


## Whip antenna bent back by the head wind; origin = mount.
func _antenna_mesh(h: float) -> ArrayMesh:
	var k := Kit.new()
	k.cyl(Vector3(0, -0.04, 0), Vector3(0, 0.10, 0), 0.05, 0.04, 6, S[1])
	k.cyl(Vector3(0, 0.10, 0), Vector3(0, 0.24, 0), 0.03, 0.03, 6, N[3])
	var pts: Array = []
	for i in 7:
		var u := float(i) / 6.0
		pts.append(Vector3(-0.22 * u * u, 0.24 + u * (h - 0.24), 0.0))
	k.polyline(pts, 0.032, 0.032, N[3])
	var m := k.commit()
	m.surface_set_material(0, _m["body"])
	return m


# ------------------------------------------------------------------------------------------ shared detail
## Atlas decal on a face: centre, outward normal, up, size (m).  Slightly lifted off the face.
func _decal(d: Kit, c: Vector3, n: Vector3, up: Vector3, w: float, h: float, region: String,
		col: Color = Color.WHITE) -> void:
	n = n.normalized()
	if col == Color.WHITE and region != "lens" and region != "glass":
		col = S[3]                                  # grey detail maps tint the steel; only lens / glass are coloured
	var u := (up - n * up.dot(n)).normalized()
	var r := u.cross(n).normalized()
	c += n * 0.008
	var rc: Rect2 = DEC[region]
	var inset := Vector2(0.02, 0.02)
	var uv0 := (rc.position + inset) / DEC_SIZE
	var uv1 := (rc.end - inset) / DEC_SIZE
	var bl := c - r * w * 0.5 - u * h * 0.5
	var tl := c - r * w * 0.5 + u * h * 0.5
	var tr := c + r * w * 0.5 + u * h * 0.5
	var br := c + r * w * 0.5 - u * h * 0.5
	d.quad_uv_out(bl, tl, tr, br, n, col, Vector2(uv0.x, uv1.y), Vector2(uv1.x, uv0.y))


## Strip decal repeated every metre (bolt rows, weld beads) from a to b on a face with normal n.
func _strip(d: Kit, a: Vector3, b: Vector3, n: Vector3, h: float, region: String, col: Color = Color.WHITE) -> void:
	var l := a.distance_to(b)
	var cnt := maxi(1, int(round(l)))
	var dv := (b - a) / cnt
	var up := n.cross(dv).normalized()
	for i in cnt:
		_decal(d, a + dv * (i + 0.5), n, up, dv.length(), h, region, col)


## Seated / standing figure from the hips up: torso loft, helmet, a dark face patch towards `face` (faceless:
## the face is a shadow band under the helmet).  helmet: 0 = padded crew helmet, 1 = steel helmet.
func _crew(k: Kit, base: Vector3, face: Vector3, hip_y: float, sh_y: float, coat: Color, helmet: int) -> void:
	var f := face.normalized()
	var sx := Vector3(-f.z, 0.0, f.x)          # shoulder axis (left-right of the figure)
	var rings: Array = []
	for spec in [[hip_y, 0.16, 0.12], [lerpf(hip_y, sh_y, 0.6), 0.19, 0.13], [sh_y - 0.05, 0.21, 0.13],
			[sh_y, 0.16, 0.11], [sh_y + 0.05, 0.06, 0.055]]:
		rings.append(Kit.ring(Vector3(base.x, float(spec[0]), base.z), sx, f, float(spec[1]), float(spec[2]), 10))
	k.loft(rings, [coat, coat, coat.lightened(0.06), coat], false, true)
	var hy := sh_y + 0.05
	var hc := Vector3(base.x, 0.0, base.z)
	# head
	var hr: Array = []
	for spec in [[hy, 0.07], [hy + 0.06, 0.095], [hy + 0.14, 0.1], [hy + 0.2, 0.07]]:
		hr.append(Kit.ring(hc + Vector3(0, float(spec[0]), 0), sx, f, float(spec[1]), float(spec[1]), 8))
	k.loft(hr, K[1], false, true)
	if helmet == 0:
		var hh: Array = []
		for spec in [[hy + 0.07, 0.108, 0.0], [hy + 0.15, 0.113, 0.0], [hy + 0.22, 0.09, 0.0], [hy + 0.26, 0.04, 0.0]]:
			hh.append(Kit.ring(hc + Vector3(0, float(spec[0]), 0) - f * 0.012, sx, f, float(spec[1]),
				float(spec[1]) * 0.95, 10))
		k.loft(hh, [N[2], N[2], N[3]], false, true)
		for sd: float in [-1.0, 1.0]:
			k.cyl(hc + Vector3(0, hy + 0.1, 0) + sx * sd * 0.1, hc + Vector3(0, hy + 0.1, 0) + sx * sd * 0.135,
				0.04, 0.035, 6, N[1])
	else:
		var hs: Array = []
		for spec in [[hy + 0.1, 0.165], [hy + 0.115, 0.155], [hy + 0.17, 0.135], [hy + 0.22, 0.1], [hy + 0.25, 0.04]]:
			hs.append(Kit.ring(hc + Vector3(0, float(spec[0]), 0), sx, f, float(spec[1]), float(spec[1]) * 0.92, 10))
		k.loft(hs, [S[1], S[2], S[2], S[3]], true, true)
	# the shadow under the brim where a face would be
	var fc := hc + Vector3(0, hy + 0.085, 0) + f * 0.105
	k.quad_out(fc - sx * 0.06 - Vector3(0, 0.05, 0), fc - sx * 0.06 + Vector3(0, 0.04, 0),
		fc + sx * 0.06 + Vector3(0, 0.04, 0), fc + sx * 0.06 - Vector3(0, 0.05, 0), K[0], f)


## Headlight with a wire guard: housing along `fwd`, lens decal, three hoops.
func _headlight(k: Kit, d: Kit, c: Vector3, fwd: Vector3) -> void:
	var f := fwd.normalized()
	k.cyl(c - f * 0.1, c + f * 0.07, 0.085, 0.1, 10, S[2])
	k.beam(c - f * 0.04, c - f * 0.04 - Vector3(0, 0.16, 0), 0.05, 0.05, S[1])
	var ld := c + f * 0.071
	var side := f.cross(Vector3.UP).normalized()
	d.disc_uv(ld, f, Vector3.UP, 0.09, 10, Color.WHITE, Rect2(DEC["lens"].position / DEC_SIZE,
		DEC["lens"].size / DEC_SIZE), 0.15)
	for o: float in [-0.055, 0.055]:
		k.polyline([c + Vector3(0, 0.12, 0) + side * o - f * 0.05, c + Vector3(0, 0.12, 0) + side * o + f * 0.15,
			c - Vector3(0, 0.12, 0) + side * o + f * 0.15, c - Vector3(0, 0.12, 0) + side * o - f * 0.05],
			0.025, 0.025, S[1])
	k.polyline([c - side * 0.13 - f * 0.05, c - side * 0.13 + f * 0.15, c + side * 0.13 + f * 0.15,
		c + side * 0.13 - f * 0.05], 0.025, 0.025, S[1])


## Stowage box with an overhanging lid and two latches; out = the face with the latches.
func _box(k: Kit, mn: Vector3, size: Vector3, out_z: float) -> void:
	var lid := 0.06
	k.box(mn, Vector3(size.x, size.y - lid, size.z), {"front": S[2], "side": S[2], "top": S[3]})
	k.box(mn + Vector3(-0.015, size.y - lid, -0.015), Vector3(size.x + 0.03, lid, size.z + 0.03),
		{"front": S[3], "side": S[2], "top": S[3]})
	var zf := mn.z + size.z if out_z > 0.0 else mn.z - 0.02
	for fx: float in [0.22, 0.78]:
		k.box(Vector3(mn.x + size.x * fx - 0.03, mn.y + size.y - lid - 0.09, zf), Vector3(0.06, 0.08, 0.02), S[4])


## Shovel / axe / crowbar lying along x on a fender (y = top of the fender).
func _tools(k: Kit, x0: float, y: float, z: float) -> void:
	k.beam(Vector3(x0, y + 0.03, z), Vector3(x0 + 1.05, y + 0.03, z), 0.045, 0.045, O[1])          # shovel
	k.box(Vector3(x0 + 1.05, y + 0.005, z - 0.11), Vector3(0.3, 0.025, 0.22), {"front": S[3], "top": S[4]})
	k.beam(Vector3(x0 - 0.05, y + 0.03, z), Vector3(x0 + 0.06, y + 0.03, z), 0.1, 0.03, O[1])
	k.beam(Vector3(x0 - 0.75, y + 0.025, z + 0.05), Vector3(x0 - 0.05, y + 0.025, z + 0.05), 0.04, 0.04, O[0])  # axe
	k.box(Vector3(x0 - 0.88, y + 0.005, z - 0.02), Vector3(0.14, 0.04, 0.14), {"front": S[3], "top": S[4]})
	k.beam(Vector3(x0 - 1.5, y + 0.02, z - 0.06), Vector3(x0 - 0.15, y + 0.02, z - 0.06), 0.035, 0.035, S[1])
	for fx: float in [x0 + 0.2, x0 + 0.85, x0 - 0.5]:                                         # clamps
		k.box(Vector3(fx - 0.03, y, z - 0.1), Vector3(0.06, 0.06, 0.2), S[1])


# ------------------------------------------------------------------------------------------ tank
func _tank_body(k: Kit, d: Kit) -> void:
	var X := Vector3.RIGHT
	var Y := Vector3.UP
	var Z := Vector3.BACK
	var hull := {"front": S[2], "side": S[2], "top": S[3]}
	var dark := {"front": S[1], "side": S[1], "top": S[2]}
	# lower hull between the tracks: lower glacis, belly, sloped rear plate
	k.prism([Vector2(-3.22, 0.46), Vector2(2.78, 0.46), Vector2(3.44, 1.04), Vector2(3.22, 1.17),
		Vector2(-3.34, 1.17), Vector2(-3.37, 0.90)], Vector3.ZERO, X, Y, Z, -1.04, 1.04, dark)
	# upper hull with the sponsons over the tracks: 67-degree glacis, engine deck, rear plate
	k.prism([Vector2(-3.36, 1.17), Vector2(3.22, 1.17), Vector2(1.78, 1.77), Vector2(-3.18, 1.73),
		Vector2(-3.40, 1.58)], Vector3.ZERO, X, Y, Z, -1.46, 1.46, hull)
	var gl0 := Vector2(3.22, 1.17)
	var gl1 := Vector2(1.78, 1.77)
	var gdir := (gl1 - gl0).normalized()
	var gn := Vector2(-gdir.y, gdir.x)
	if gn.y < 0.0:
		gn = -gn
	var gn3 := Vector3(gn.x, gn.y, 0.0)
	var G := func(t: float, z: float, lift: float) -> Vector3:
		var p := gl0.lerp(gl1, t) + gn * lift
		return Vector3(p.x, p.y, z)
	# plate joints: weld beads along the glacis edges and the sponson tops, bolt rows on the fender lips
	for sd: float in [-1.0, 1.0]:
		var wa := gl0.lerp(gl1, 0.12) - gn * 0.06
		var wb := gl0.lerp(gl1, 0.92) - gn * 0.06
		_strip(d, Vector3(wa.x, wa.y, sd * 1.46), Vector3(wb.x, wb.y, sd * 1.46), Vector3(0, 0, sd), 0.08, "weld")
	_strip(d, Vector3(1.72, 1.77, -1.3), Vector3(1.72, 1.77, 1.3), Vector3.UP, 0.1, "weld")
	# fenders over the tracks with lips, front mudguards and rear flaps
	for sd: float in [-1.0, 1.0]:
		var zi := sd * 1.44
		var zo := sd * 1.71
		k.box(Vector3(-3.28, 1.155, minf(zi, zo)), Vector3(6.5, 0.03, 0.27), {"front": S[2], "side": S[1],
			"top": S[3]}, Kit.FACES_ALL)
		k.box(Vector3(-3.28, 1.09, zo - (0.025 if sd > 0.0 else 0.0)), Vector3(6.5, 0.095, 0.025),
			{"front": S[3], "side": S[2], "top": S[3]}, Kit.FACES_ALL)
		_strip(d, Vector3(-3.2, 1.137, zo + sd * 0.001), Vector3(3.2, 1.137, zo + sd * 0.001), Vector3(0, 0, sd),
			0.1, "bolts")
		k.prism([Vector2(3.22, 1.155), Vector2(3.22, 1.185), Vector2(3.63, 1.0), Vector2(3.61, 0.97)], Vector3.ZERO,
			X, Y, Z, sd * 1.05, sd * 1.71, {"front": S[2], "side": S[2], "top": S[3]})
		k.prism([Vector2(-3.28, 1.155), Vector2(-3.28, 1.185), Vector2(-3.49, 1.12), Vector2(-3.47, 1.09)],
			Vector3.ZERO, X, Y, Z, sd * 1.05, sd * 1.71, dark)
		# rubber mud flaps hanging behind the fender ends
		k.box(Vector3(-3.52, 0.78, minf(sd * 1.07, sd * 1.67)), Vector3(0.02, 0.34, 0.6), N[2], Kit.FACES_ALL)
	# --- right fender (the side the crowd sees): stowage boxes, tools, convoy light
	_box(k, Vector3(1.45, 1.185, 1.46), Vector3(0.8, 0.44, 0.23), 1.0)
	_box(k, Vector3(0.55, 1.185, 1.46), Vector3(0.8, 0.44, 0.23), 1.0)
	_box(k, Vector3(-3.22, 1.185, 1.46), Vector3(0.5, 0.36, 0.23), 1.0)
	_tools(k, -1.2, 1.185, 1.6)
	k.box(Vector3(2.5, 1.185, 1.55), Vector3(0.12, 0.1, 0.1), S[1])
	_decal(d, Vector3(2.62, 1.235, 1.6), X, Y, 0.07, 0.05, "lens")
	# --- left fender: external fuel tanks with straps, a box, a crate
	for x0: float in [-1.15, 0.05]:
		k.cyl(Vector3(x0, 1.36, -1.585), Vector3(x0 + 1.0, 1.36, -1.585), 0.165, 0.165, 10, S[1])
		for fx: float in [0.2, 0.8]:
			k.cyl(Vector3(x0 + fx - 0.025, 1.36, -1.585), Vector3(x0 + fx + 0.025, 1.36, -1.585), 0.18, 0.18, 10, N[3],
				false)
		k.cyl(Vector3(x0 + 0.5, 1.5, -1.585), Vector3(x0 + 0.5, 1.56, -1.585), 0.04, 0.04, 6, S[3])
	_box(k, Vector3(1.45, 1.185, -1.69), Vector3(0.8, 0.44, 0.23), -1.0)
	k.box(Vector3(-2.95, 1.185, -1.69), Vector3(0.7, 0.32, 0.24), O[1])
	_decal(d, Vector3(-2.6, 1.345, -1.69), -Z, Y, 0.68, 0.3, "planks", O[2])
	# tow cables on the sponson walls: eyes, two clamps, a sag between them
	for sd: float in [-1.0, 1.0]:
		var zc := sd * 1.49
		var pts: Array = [Vector3(2.85, 1.66, zc)]
		for i in 9:
			var x := lerpf(2.6, -2.95, float(i) / 8.0)
			pts.append(Vector3(x, 1.665 - 0.02 * sin(float(i) / 8.0 * PI * 2.0), zc))
		pts.append(Vector3(-3.1, 1.6, zc))
		k.polyline(pts, 0.05, 0.05, N[3], Z)
		for ex: float in [2.85, -3.1]:
			k.polyline(Kit.ring(Vector3(ex, 1.63, zc), X, Y, 0.075, 0.05, 6), 0.03, 0.03, N[3], Z, true)
		for cx: float in [1.4, -0.4, -2.0]:
			k.box(Vector3(cx - 0.04, 1.62, zc - 0.03), Vector3(0.08, 0.1, 0.06), S[3])
	# glacis: driver's hatch and periscopes, spare track links, headlights, tow hooks
	k.cyl(Vector3(1.42, 1.755, -0.55), Vector3(1.42, 1.80, -0.55), 0.3, 0.29, 12, S[3])
	k.box(Vector3(1.24, 1.80, -0.6), Vector3(0.3, 0.025, 0.1), S[2])
	for pz: float in [-0.68, -0.42]:
		k.box(Vector3(1.66, 1.76, pz - 0.05), Vector3(0.1, 0.1, 0.1), S[1])
		_decal(d, Vector3(1.76, 1.815, pz), X, Y, 0.08, 0.04, "glass")
	for sd: float in [-1.0, 1.0]:
		var zc := sd * 0.6
		k.beam(G.call(0.18, zc, 0.03), G.call(0.55, zc, 0.03), 0.55, 0.05, S[1], gn3)
		for i in 5:
			var t := 0.2 + i * 0.085
			k.beam(G.call(t, zc - 0.27, 0.07), G.call(t, zc + 0.27, 0.07), 0.05, 0.035, S[2], gn3)
		_headlight(k, d, Vector3(3.0, 1.41, sd * 1.2), X)
		k.box(Vector3(3.36, 0.86, sd * 0.78 - 0.06), Vector3(0.16, 0.14, 0.12), S[1])
		k.beam(Vector3(3.44, 0.93, sd * 0.78 - 0.05), Vector3(3.44, 0.93, sd * 0.78 + 0.05), 0.06, 0.06, S[3])
	# engine deck: louvre grilles, filler caps, a grab rail
	for sd: float in [-1.0, 1.0]:
		_decal(d, Vector3(-2.35, 1.737, sd * 0.5), Y, -X, 0.75, 1.3, "louvre")
		k.cyl(Vector3(-1.3, 1.75, sd * 1.15), Vector3(-1.3, 1.8, sd * 1.15), 0.09, 0.08, 8, S[3])
	k.polyline([Vector3(-3.15, 1.74, -0.9), Vector3(-3.15, 1.86, -0.9), Vector3(-3.15, 1.86, 0.9),
		Vector3(-3.15, 1.74, 0.9)], 0.03, 0.03, S[2])
	# rear plate: two drums on brackets, exhaust louvres, tail lights, tow pintle
	for sd: float in [-1.0, 1.0]:
		var zc := sd * 0.62
		k.cyl(Vector3(-3.66, 1.3, zc - 0.38), Vector3(-3.66, 1.3, zc + 0.38), 0.25, 0.25, 12, S[2])
		# rolled chime at both ends, a recessed dark lid inside it, filler bung + vent on the outer lid
		for ez: float in [-1.0, 1.0]:
			var z0 := zc + ez * 0.38
			k.cyl(Vector3(-3.66, 1.3, z0), Vector3(-3.66, 1.3, z0 + ez * 0.035), 0.268, 0.262, 12, S[4], false)
			var ring := []
			for j in 13:
				var ang := TAU * float(j) / 12.0
				ring.append(Vector3(-3.66 + cos(ang) * 0.262, 1.3 + sin(ang) * 0.262, z0 + ez * 0.035))
			for j in 12:
				var a0: Vector3 = ring[j]
				var a1: Vector3 = ring[j + 1]
				var c0 := Vector3(-3.66, 1.3, z0 + ez * 0.035) + (a0 - Vector3(-3.66, 1.3, z0 + ez * 0.035)) * 0.8
				var c1 := Vector3(-3.66, 1.3, z0 + ez * 0.035) + (a1 - Vector3(-3.66, 1.3, z0 + ez * 0.035)) * 0.8
				k.quad_out(a0, a1, c1, c0, S[3] if a0.y + a1.y > 2.6 else S[2], Vector3(0, 0, ez))
			k.cyl(Vector3(-3.66, 1.3, z0 + ez * 0.012), Vector3(-3.66, 1.3, z0 + ez * 0.018), 0.21, 0.21, 12, S[1])
			# the upper half of the lid catches the floods (pressed rib = a lighter half moon)
			var lc := Vector3(-3.66, 1.3, z0 + ez * 0.024)
			for j in 6:
				var b0 := lc + Vector3(cos(PI * j / 6.0), sin(PI * j / 6.0), 0.0) * 0.17
				var b1 := lc + Vector3(cos(PI * (j + 1) / 6.0), sin(PI * (j + 1) / 6.0), 0.0) * 0.17
				k.tri_out(lc + Vector3(0, 0.03, 0), b0, b1, S[2], Vector3(0, 0, ez))
		k.cyl(Vector3(-3.66, 1.42, zc + 0.38), Vector3(-3.66, 1.42, zc + 0.43), 0.05, 0.05, 8, S[4])
		k.cyl(Vector3(-3.66, 1.16, zc + 0.38), Vector3(-3.66, 1.16, zc + 0.41), 0.03, 0.03, 6, S[3])
		for bz: float in [-0.22, 0.22]:
			k.cyl(Vector3(-3.66, 1.3, zc + bz - 0.02), Vector3(-3.66, 1.3, zc + bz + 0.02), 0.265, 0.265, 12, N[3],
				false)
			k.beam(Vector3(-3.4, 1.12, zc + bz), Vector3(-3.66, 1.04, zc + bz), 0.04, 0.04, S[1])
		k.box(Vector3(-3.42, 0.98, sd * 1.25 - 0.06), Vector3(0.05, 0.08, 0.12), O[2])
	_decal(d, Vector3(-3.393, 1.5, 0.0), Vector3(-1, -0.1, 0), Y, 0.45, 0.16, "louvre")
	k.box(Vector3(-3.45, 0.62, -0.1), Vector3(0.12, 0.16, 0.2), S[1])
	# turret: cast, rounded, with a long bustle
	var tc := Vector3(-0.30, 1.75, 0.0)
	var rings: Array = []
	for spec in [[0.0, 0.95, 0.95], [0.1, 1.0, 1.0], [0.3, 0.985, 0.975], [0.48, 0.91, 0.9], [0.6, 0.78, 0.78],
			[0.66, 0.62, 0.62]]:
		rings.append(_turret_ring(tc + Vector3(0, float(spec[0]), 0), float(spec[1]), float(spec[2])))
	k.loft(rings, [S[2], S[2], S[2], S[3], S[3]], false, true, S[3])
	k.cyl(Vector3(tc.x, 1.71, 0.0), Vector3(tc.x, 1.77, 0.0), 1.0, 1.0, 20, S[1], false)
	# cast seam + lifting eyes
	for sd: float in [-1.0, 1.0]:
		k.box(Vector3(-0.4, 2.36, sd * 0.76 - 0.03), Vector3(0.08, 0.08, 0.06), S[3])
		k.box(Vector3(-1.6, 2.33, sd * 0.68 - 0.03), Vector3(0.08, 0.08, 0.06), S[3])
	# mantlet with a canvas dust cover, coax port, sight, IR lamp
	k.cyl(Vector3(1.08, 2.02, -0.46), Vector3(1.08, 2.02, 0.46), 0.26, 0.26, 10, S[2])
	k.box(Vector3(0.82, 1.78, -0.42), Vector3(0.3, 0.48, 0.84), S[1])
	var cov: Array = []
	for spec in [[1.28, 0.2], [1.34, 0.17], [1.39, 0.185], [1.44, 0.16], [1.5, 0.15]]:
		cov.append(Kit.ring(Vector3(float(spec[0]), 2.02, 0.0), Z, Y, float(spec[1]), float(spec[1]), 10))
	k.loft(cov, [P[1], P[2], P[1], P[2]])
	k.box(Vector3(1.3, 1.99, 0.18), Vector3(0.05, 0.06, 0.06), N[0])
	k.box(Vector3(1.0, 2.22, -0.32), Vector3(0.22, 0.14, 0.14), S[1])
	_decal(d, Vector3(1.221, 2.29, -0.25), X, Y, 0.1, 0.05, "glass")
	k.cyl(Vector3(0.92, 2.46, -0.62), Vector3(1.22, 2.46, -0.62), 0.15, 0.17, 10, S[1])
	k.cyl(Vector3(1.22, 2.46, -0.62), Vector3(1.23, 2.46, -0.62), 0.13, 0.13, 10, N[1])
	k.box(Vector3(1.0, 2.2, -0.66), Vector3(0.1, 0.16, 0.08), S[2])
	# gun: base, tube, fume extractor, tube, double-baffle muzzle brake, bore
	var gy := 2.02
	for g in [[1.40, 1.95, 0.115, 0.1, 10], [1.95, 3.55, 0.085, 0.08, 8], [3.55, 3.68, 0.08, 0.135, 10],
			[3.68, 4.26, 0.135, 0.135, 10], [4.26, 4.40, 0.135, 0.078, 10], [4.40, 6.36, 0.078, 0.072, 8],
			[6.36, 6.44, 0.072, 0.112, 8], [6.44, 6.58, 0.112, 0.112, 8], [6.58, 6.66, 0.075, 0.075, 8],
			[6.66, 6.80, 0.112, 0.108, 8]]:
		k.cyl(Vector3(float(g[0]), gy, 0.0), Vector3(float(g[1]), gy, 0.0), float(g[2]), float(g[3]), int(g[4]), S[2],
			false, Y, PI / float(g[4]))
	for cx: float in [2.7, 5.4]:
		k.cyl(Vector3(cx, gy, 0.0), Vector3(cx + 0.06, gy, 0.0), 0.092, 0.09, 8, S[3], false, Y, PI / 8.0)
	k.cyl(Vector3(6.80, gy, 0.0), Vector3(6.805, gy, 0.0), 0.108, 0.108, 8, S[3], true, Y, PI / 8.0)
	k.cyl(Vector3(6.806, gy, 0.0), Vector3(6.81, gy, 0.0), 0.05, 0.05, 8, N[0], true)
	# commander's cupola (right rear): vision blocks, open lid upright behind, the commander out to the chest
	var cc := Vector3(-0.78, 2.3, 0.5)
	k.cyl(cc, cc + Vector3(0, 0.27, 0), 0.37, 0.34, 12, S[2], true)
	k.cyl(cc + Vector3(0, 0.27, 0), cc + Vector3(0, 0.275, 0), 0.27, 0.27, 12, N[1], true)
	for i in 5:
		var a := -PI * 0.55 + i * PI * 0.275
		var nrm := Vector3(cos(a), 0.0, sin(a))
		var bc := cc + Vector3(0, 0.19, 0) + nrm * 0.355
		k.obox(bc, Basis(nrm.cross(Y), Y, nrm), Vector3(0.06, 0.04, 0.03), S[3])
		_decal(d, bc + nrm * 0.03, nrm, Y, 0.09, 0.045, "glass")
	k.cyl(cc + Vector3(-0.36, 0.6, 0), cc + Vector3(-0.33, 0.6, 0), 0.31, 0.31, 12, S[3], true, Y)
	k.box(cc + Vector3(-0.4, 0.24, -0.08), Vector3(0.1, 0.08, 0.16), S[1])
	_crew(k, cc + Vector3(0.02, 0, 0), X, 2.42, 2.86, N[3], 0)
	k.beam(cc + Vector3(0.05, 0.5, -0.19), cc + Vector3(0.27, 0.3, -0.25), 0.08, 0.08, N[3])      # arm on the rim
	k.box(cc + Vector3(0.22, 0.27, -0.3), Vector3(0.1, 0.06, 0.1), K[1])
	# loader's hatch (left): lid open to the side, the loader looking ahead
	var lc := Vector3(-0.55, 2.33, -0.5)
	k.cyl(lc, lc + Vector3(0, 0.08, 0), 0.31, 0.3, 12, S[3], true)
	k.cyl(lc + Vector3(0, 0.08, 0), lc + Vector3(0, 0.085, 0), 0.24, 0.24, 12, N[1], true)
	k.cyl(lc + Vector3(0, 0.38, -0.33), lc + Vector3(0, 0.38, -0.30), 0.28, 0.28, 12, S[3], true, X)
	_crew(k, lc, X, 2.42, 2.76, V[1], 0)
	# smoke dischargers, hand rails, antenna mounts, stowage basket with a tarp roll
	for sd: float in [-1.0, 1.0]:
		k.box(Vector3(0.3, 2.04, sd * 0.97 - 0.05), Vector3(0.42, 0.06, 0.1), S[1])
		for i in 3:
			var b0 := Vector3(0.36 + i * 0.13, 2.1, sd * 0.97)
			k.cyl(b0, b0 + Vector3(0.11, 0.12, sd * 0.1), 0.045, 0.045, 6, S[2], true)
		k.polyline([Vector3(0.2, 2.2, sd * 1.0), Vector3(-0.5, 2.24, sd * 1.06), Vector3(-1.3, 2.22, sd * 1.0)],
			0.03, 0.03, S[1])
		k.cyl(Vector3(-1.62, 2.28, sd * 0.62), Vector3(-1.62, 2.4, sd * 0.62), 0.06, 0.05, 6, S[1])
	var bk: Array = []
	for i in 9:
		var a := PI * 0.62 + i * PI * 0.76 / 8.0
		var p := _turret_pt(a)
		bk.append(Vector3(tc.x + p.x * 1.1, 2.3, p.y * 1.08))
	k.polyline(bk, 0.035, 0.035, S[1])
	for i in [0, 2, 4, 6, 8]:
		var p0: Vector3 = bk[i]
		k.beam(p0, p0 - Vector3(0, 0.22, 0) + (Vector3(tc.x, 2.08, 0) - p0) * 0.1, 0.03, 0.03, S[1], Z)
	var tarp: Array = []
	for i in 7:
		var z := lerpf(-0.7, 0.7, float(i) / 6.0)
		var rr := 0.16 + (0.025 if i % 2 == 1 else 0.0)
		tarp.append(Kit.ring(Vector3(-2.02, 2.28, z), X, Y, rr, rr * 0.9, 10))
	k.loft(tarp, [V[2], V[3], V[2], V[3], V[2], V[3]], true, true)
	for z: float in [-0.35, 0.35]:
		k.cyl(Vector3(-2.02, 2.28, z - 0.025), Vector3(-2.02, 2.28, z + 0.025), 0.2, 0.2, 10, N[2], false)


## Cast turret outline (superellipse): rounder nose, boxier bustle.  Returns (x, z) for angle a (0 = +x).
static func _turret_pt(a: float) -> Vector2:
	var ca := cos(a)
	var sa := sin(a)
	var front := ca >= 0.0
	var ax := 1.32 if front else 1.62
	var p := 2.0 if front else 2.7
	var x := signf(ca) * ax * pow(absf(ca), 2.0 / p)
	var z := signf(sa) * 1.12 * pow(absf(sa), 2.0 / p)
	return Vector2(x, z)


func _turret_ring(c: Vector3, sx: float, sz: float) -> Array:
	var pts: Array = []
	for i in 22:
		var p := _turret_pt(TAU * float(i) / 22.0)
		pts.append(c + Vector3(p.x * sx, 0.0, p.y * sz))
	return pts


# ------------------------------------------------------------------------------------------ half-track
func _halftrack_body(k: Kit, d: Kit) -> void:
	var X := Vector3.RIGHT
	var Y := Vector3.UP
	var Z := Vector3.BACK
	var hull := {"front": S[2], "side": S[2], "top": S[3]}
	var dark := {"front": S[1], "side": S[1], "top": S[2]}
	# chassis rails, front axle, lower hull between the tracks
	for sd: float in [-1.0, 1.0]:
		k.box(Vector3(-2.9, 0.48, sd * 0.56 - 0.06), Vector3(5.85, 0.24, 0.12), N[3])
	k.beam(Vector3(2.32, 0.45, -0.85), Vector3(2.32, 0.45, 0.85), 0.12, 0.12, N[3])
	k.box(Vector3(-2.98, 0.66, -0.66), Vector3(4.3, 0.3, 1.32), dark)
	# fenders over the track units
	for sd: float in [-1.0, 1.0]:
		k.box(Vector3(-2.98, 0.80, minf(sd * 0.64, sd * 1.12)), Vector3(3.98, 0.04, 0.48), {"front": S[2],
			"side": S[1], "top": S[3]}, Kit.FACES_ALL)
		k.box(Vector3(-2.98, 0.74, sd * 1.12 - (0.02 if sd > 0.0 else 0.0)), Vector3(3.98, 0.1, 0.02), S[3],
			Kit.FACES_ALL)
		_strip(d, Vector3(-2.9, 0.79, sd * 1.122), Vector3(0.9, 0.79, sd * 1.122), Vector3(0, 0, sd), 0.1, "bolts")
	# armoured side walls (vertical lower plate, upper plate leaning in) from the rear to the cab
	for sd: float in [-1.0, 1.0]:
		var poly: Array = [Vector2(sd * 1.07, 0.84), Vector2(sd * 1.12, 0.84), Vector2(sd * 1.12, 1.32),
			Vector2(sd * 0.98, 1.88), Vector2(sd * 0.93, 1.88), Vector2(sd * 1.07, 1.32)]
		k.prism(poly, Vector3.ZERO, Z, Y, X, -3.0, 1.32, hull)
		# pistol ports with hinged flaps, a jerry-can rack at the rear corner, a grab rail along the top
		for qx: float in [-1.95, -1.05]:
			k.box(Vector3(qx - 0.12, 1.08, sd * 1.12 - (0.0 if sd > 0.0 else 0.03)), Vector3(0.24, 0.16, 0.03),
				{"front": S[3], "side": S[2], "top": S[3]})
			k.box(Vector3(qx - 0.08, 1.13, sd * 1.15 - (0.0 if sd > 0.0 else 0.01)), Vector3(0.16, 0.04, 0.01), N[0])
		k.box(Vector3(-2.92, 0.86, sd * 1.12 - (0.0 if sd > 0.0 else 0.04)), Vector3(0.62, 0.05, 0.04), S[1])
		for jx: float in [-2.88, -2.58]:
			var jz := sd * 1.12 + (0.0 if sd > 0.0 else -0.14)
			k.box(Vector3(jx, 0.91, jz), Vector3(0.26, 0.44, 0.14), P[1])
			_decal(d, Vector3(jx + 0.13, 1.13, sd * 1.26 + (0.0 if sd > 0.0 else 0.0)), Vector3(0, 0, sd), Vector3.UP,
				0.24, 0.42, "jerry", P[2])
		k.polyline([Vector3(-2.8, 1.9, sd * 0.96), Vector3(-2.8, 1.97, sd * 0.97), Vector3(0.9, 1.97, sd * 0.97),
			Vector3(0.9, 1.9, sd * 0.96)], 0.03, 0.03, S[2])
		_strip(d, Vector3(-2.9, 1.84, sd * 0.99), Vector3(1.2, 1.84, sd * 0.99), Vector3(0, 0.25, sd), 0.1, "bolts")
	# rear wall with the door, hinges, handle, two jerry cans, tail lights, hitch
	k.box(Vector3(-3.04, 0.84, -1.1), Vector3(0.06, 0.98, 2.2), hull)
	k.box(Vector3(-3.06, 0.9, -0.4), Vector3(0.02, 0.85, 0.8), S[3])
	for hy: float in [1.0, 1.55]:
		k.box(Vector3(-3.09, hy, -0.46), Vector3(0.04, 0.1, 0.1), S[1])
	k.beam(Vector3(-3.09, 1.3, 0.2), Vector3(-3.09, 1.3, 0.32), 0.03, 0.03, S[4])
	for sd: float in [-1.0, 1.0]:
		var jz := sd * 0.72
		k.box(Vector3(-3.2, 1.0, jz - 0.17), Vector3(0.14, 0.46, 0.34), P[1])
		_decal(d, Vector3(-3.2, 1.23, jz), -X, Y, 0.32, 0.44, "jerry", P[2])
		k.box(Vector3(-3.1, 0.88, sd * 1.0 - 0.05), Vector3(0.04, 0.07, 0.1), O[2])
	k.box(Vector3(-3.18, 0.62, -0.08), Vector3(0.16, 0.12, 0.16), S[1])
	# floor and benches of the open compartment
	k.box(Vector3(-2.98, 0.96, -1.04), Vector3(3.9, 0.04, 2.08), N[2])
	for sd: float in [-1.0, 1.0]:
		k.box(Vector3(-2.9, 1.2, minf(sd * 0.62, sd * 1.02)), Vector3(3.2, 0.1, 0.4), O[0])
	# cab: sloped front plate with two armoured visors, dashboard, pintle MG on a post
	k.prism([Vector2(1.32, 1.2), Vector2(1.38, 1.2), Vector2(1.13, 1.88), Vector2(1.07, 1.88)], Vector3.ZERO, X, Y,
		Z, -0.98, 0.98, hull)
	var vdir := (Vector2(1.13, 1.88) - Vector2(1.38, 1.2)).normalized()
	var vn := Vector3(vdir.y, -vdir.x, 0.0)
	if vn.x < 0.0:
		vn = -vn
	for vz: float in [-0.45, 0.45]:
		_decal(d, Vector3(1.255, 1.55, vz), vn, Vector3(vdir.x, vdir.y, 0.0), 0.78, 0.4, "visor")
	k.box(Vector3(0.95, 1.2, -0.95), Vector3(0.15, 0.3, 1.9), N[3])
	k.cyl(Vector3(0.95, 1.86, 0.35), Vector3(0.95, 2.1, 0.35), 0.035, 0.035, 6, S[1])
	k.box(Vector3(0.82, 2.1, 0.3), Vector3(0.36, 0.1, 0.1), N[2])
	k.cyl(Vector3(1.18, 2.15, 0.35), Vector3(1.7, 2.19, 0.35), 0.04, 0.03, 6, N[3])
	k.cyl(Vector3(1.18, 2.15, 0.35), Vector3(1.42, 2.165, 0.35), 0.055, 0.055, 8, S[1])
	k.box(Vector3(1.12, 2.0, 0.08), Vector3(0.03, 0.34, 0.54), S[2])
	# crew: driver + co-driver facing forward, ten troops in two rows facing each other, rifles upright
	for cz: float in [-0.45, 0.45]:
		_crew(k, Vector3(0.62, 0, cz), X, 1.3, 1.82, S[1], 1)
	for sd: float in [-1.0, 1.0]:
		for i in 5:
			var px := -2.55 + i * 0.53
			var zc := sd * 0.74
			var face := Vector3(0, 0, -sd)
			_crew(k, Vector3(px, 0, zc), face, 1.3, 1.83 + 0.02 * float((i + int(sd > 0.0)) % 2), S[1], 1)
			var rz := zc - sd * 0.27
			k.beam(Vector3(px + 0.1, 1.26, rz), Vector3(px + 0.1, 1.72, rz + sd * 0.03), 0.045, 0.06, O[0], Z)
			k.beam(Vector3(px + 0.1, 1.72, rz + sd * 0.03), Vector3(px + 0.1, 2.24, rz + sd * 0.05), 0.03, 0.03, N[3], Z)
	# bonnet: armoured, sloped sides, louvred top, radiator grille, hinge
	k.prism([Vector2(-0.74, 0.8), Vector2(0.74, 0.8), Vector2(0.74, 1.1), Vector2(0.55, 1.38), Vector2(-0.55, 1.38),
		Vector2(-0.74, 1.1)], Vector3.ZERO, Z, Y, X, 1.3, 2.86, hull)
	k.prism([Vector2(2.84, 0.8), Vector2(2.98, 0.8), Vector2(2.9, 1.38), Vector2(2.84, 1.38)], Vector3.ZERO, X, Y, Z,
		-0.74, 0.74, hull)
	var rdir := (Vector2(2.9, 1.38) - Vector2(2.98, 0.8)).normalized()
	_decal(d, Vector3(2.945, 1.08, 0.0), Vector3(-rdir.y, rdir.x, 0.0) * -1.0, Vector3(rdir.x, rdir.y, 0.0),
		1.25, 0.5, "radiator")
	for sd: float in [-1.0, 1.0]:
		_decal(d, Vector3(2.1, 1.382, sd * 0.27), Y, -X, 0.42, 0.95, "louvre")
	k.beam(Vector3(1.32, 1.39, 0.0), Vector3(2.85, 1.39, 0.0), 0.05, 0.03, S[3])
	# front mudguards curving over the wheels, running boards, headlights, unditching roller
	for sd: float in [-1.0, 1.0]:
		var cw := Vector2(2.32, 0.45)
		for i in 9:
			var a0 := deg_to_rad(165.0 - i * 150.0 / 9.0)
			var a1 := deg_to_rad(165.0 - (i + 1) * 150.0 / 9.0)
			var ri := 0.56
			var ro := 0.59
			var poly: Array = [cw + Vector2(cos(a0), sin(a0)) * ri, cw + Vector2(cos(a0), sin(a0)) * ro,
				cw + Vector2(cos(a1), sin(a1)) * ro, cw + Vector2(cos(a1), sin(a1)) * ri]
			k.prism(poly, Vector3.ZERO, X, Y, Z, sd * 0.74, sd * 1.2, {"front": S[2], "side": S[2], "top": S[3]})
		k.box(Vector3(0.95, 0.78, minf(sd * 0.74, sd * 1.2)), Vector3(0.84, 0.04, 0.46), {"front": S[2], "side": S[1],
			"top": S[3]}, Kit.FACES_ALL)
		_headlight(k, d, Vector3(2.62, 1.18, sd * 0.97), X)
		k.beam(Vector3(2.9, 0.62, sd * 0.7), Vector3(3.1, 0.66, sd * 0.7), 0.08, 0.08, S[1])
	k.cyl(Vector3(3.1, 0.66, -0.9), Vector3(3.1, 0.66, 0.9), 0.14, 0.14, 10, S[2], true, Y)
	for rz: float in [-0.6, 0.0, 0.6]:
		k.cyl(Vector3(3.1, 0.66, rz - 0.02), Vector3(3.1, 0.66, rz + 0.02), 0.155, 0.155, 10, S[1], false, Y)
	# exhaust muffler under the right running board
	k.cyl(Vector3(1.0, 0.56, 1.02), Vector3(1.7, 0.58, 1.02), 0.08, 0.08, 8, N[3], true)
	# stowage on the walls: bedroll, shovel (right), tarp bundle (left)
	var roll: Array = []
	for i in 7:
		var x := lerpf(-2.6, -0.9, float(i) / 6.0)
		var rr := 0.11 + (0.018 if i % 2 == 1 else 0.0)
		roll.append(Kit.ring(Vector3(x, 1.6, 1.17), Z, Y, rr, rr, 8))
	k.loft(roll, [V[2], V[3], V[2], V[3], V[2], V[3]], true, true)
	for x: float in [-2.2, -1.3]:
		k.cyl(Vector3(x - 0.02, 1.6, 1.17), Vector3(x + 0.02, 1.6, 1.17), 0.14, 0.14, 8, N[2], false, Z)
	k.beam(Vector3(-0.6, 1.12, 1.14), Vector3(0.6, 1.12, 1.14), 0.035, 0.04, O[1], Z)
	k.box(Vector3(0.6, 1.02, 1.12), Vector3(0.28, 0.2, 0.025), {"front": S[3], "side": S[2]})
	var bun: Array = []
	for i in 5:
		var x := lerpf(-2.4, -1.0, float(i) / 4.0)
		bun.append(Kit.ring(Vector3(x, 1.55, -1.22), Z, Y, 0.12 + 0.02 * float(i % 2), 0.15, 8))
	k.loft(bun, [K[1], K[2], K[1], K[2]], true, true)
