extends Node3D
## The parade on the plaza before the Great Hall (owner: parade), built at runtime on top of the hall set
## (hall_builder.gd, reused read-only).  Deterministic.  Units: metres, +Y up, the camera looks along -Z.
## Layout (z): crowd -805..-854 (backs to the camera) | barrier -856, guards -858 facing the crowd | parade lane
## -869..-883 (infantry blocks march +x, then tanks and half-tracks) | standing formations -897..-930 | tribune
## -918..-932 under the portico eagle | the hall at -1000.  Searchlight pillars ("Lichtdom") along the plaza sides
## and behind the hall.  Massed figures are MultiMesh billboards (parade_figures.gdshader, figures.png atlas).
## The same people also line the avenue (z -128..-797, behind hall_avenue.gd's cordon barriers) for shot p8.
## Insignia only through the hall builder's Symbols-resolved materials (banner_portico, flag_street).

const Kit := preload("res://scripts/levels/hall/hall_mesh_kit.gd")
const Vehicles := preload("res://scripts/levels/parade/parade_vehicles.gd")
const Avenue := preload("res://scripts/levels/hall/hall_avenue.gd")
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
const AV_Z_NEAR := -128.0        ## the avenue's crowds (shot p8): from the cleared street ...
const AV_Z_FAR := -797.0         ## ... to the plaza crowd's ragged back edge

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
var veh: Node3D                  ## the armoured column (parade_vehicles.gd)
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
	_build_konrad_trail()
	_flush()
	_build_crowd()
	_build_avenue_crowd()
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
	fig_mat.set_shader_parameter("smooth_min", _smooth_min(t))
	# shot p8 cranes over ~35 000 figures 150 - 1000 m away: band lock + far calm (parade_figures.gdshader); every
	# other shot keeps the per-figure lock and the drawn colours
	var far := _far_shot(t)
	if far != _far_on:
		_far_on = far
		fig_mat.set_shader_parameter("snap_band", SNAP_BAND if far else 0.0)
		fig_mat.set_shader_parameter("calm", 1.0 if far else 0.0)
		fig_mat.set_shader_parameter("calm_px", CALM_PX)
	puff_mat.set_shader_parameter("min_depth", min_depth)
	for k in march_blocks.size():
		(march_blocks[k] as Node3D).position.x = MARCH_X0 - k * BLOCK_PITCH + MARCH_SPEED * t
	if veh:
		veh.update(t)                                           # parade_vehicles.gd: column, tracks, wheels, whips
	_update_puffs(t)
	if jets:
		jets.visible = t > 30.6 and t < 35.5
		jets.position = Vector3(HX - 330.0 + 230.0 * (t - 31.2), 228.0, -905.0)


func vehicle_x(j: int, t: float) -> float:
	return VEH_X0 - j * VEH_PITCH + VEH_SPEED * t


# ------------------------------------------------------------------------------------------ figures
const ParadeShots := preload("res://scripts/levels/parade/parade_shots.gd")
const SMOOTH_MIN_PX := 30.0      ## figures from this height scale continuously while the camera moves in depth
const VIEW_TAN := 0.4            ## tan of half the horizontal field of view (24 deg vertical, 16:9) + margin
var _lod_spans: Array = []       ## [start, end, smooth_min] per shot
const SNAP_BAND := 6.0           ## m: depth bands of the band lock in shot p8 (parade_figures.gdshader snap_band)
const CALM_PX := 9.0             ## p8: figures below ~9 px fade into flat silhouettes of their group's colour
var _far_from := -1.0            ## start of shot p8
var _far_on := false


## Shot p8 (the crane over the avenue) uses the band lock and the far calm of the figure shader.
func _far_shot(t: float) -> bool:
	if _far_from < 0.0:
		_far_from = 1e9
		for s: Dictionary in ParadeShots.SHOTS:
			if str(s["id"]) == "p8":
				_far_from = float(s["start"])
	return t >= _far_from


## LOD mode of the figure shader per shot (parade_figures.gdshader `smooth_min`).  While the camera moves in depth
## the near and mid figures grow and shrink continuously instead of jumping 32 % between two LOD strips; a pure
## sideways track (p2) keeps every figure at a constant depth, so it stays exactly pixel-locked.
func _smooth_min(t: float) -> float:
	if _lod_spans.is_empty():
		for s: Dictionary in ParadeShots.SHOTS:
			var moves := absf((s["p0"] as Vector3).z - (s["p1"] as Vector3).z) > 0.001
			_lod_spans.append([float(s["start"]), float(s["end"]), SMOOTH_MIN_PX if moves else 1e9])
	for sp: Array in _lod_spans:
		if t < float(sp[1]):
			return float(sp[2])
	return float(_lod_spans[_lod_spans.size() - 1][2])


func _fig_material(height_m: float, self_light: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = FIG_SHADER
	var tex: Texture2D = load(DIR + "figures.png")
	m.set_shader_parameter("atlas", tex)
	var asz: Array = meta.get("atlas", [1, 1])
	m.set_shader_parameter("atlas_size", Vector2(float(asz[0]), float(asz[1])))
	var lods := PackedVector4Array()
	var lod_slots := PackedFloat32Array()
	var n_slots := 0
	for k in slots:
		n_slots = maxi(n_slots, int(slots[k][0]) + int(slots[k][1]))
	for l in meta.get("lods", []):
		lods.append(Vector4(float(l[0]), float(l[1]), float(l[2]), float(l[3])))
		# 5th field: slots present in this strip (the large strips only hold the first slots)
		lod_slots.append(float(l[4]) if (l as Array).size() > 4 else float(maxi(n_slots, 1)))
	m.set_shader_parameter("lods", lods)
	m.set_shader_parameter("lod_slots", lod_slots)
	m.set_shader_parameter("lod_count", mini(lods.size(), 24))
	m.set_shader_parameter("height_m", height_m)
	m.set_shader_parameter("self_light", self_light)
	return m


func _slot(name: String) -> Array:
	return slots.get(name, [0, 1])


## Per-instance flip + tone + group packed into the 4th custom channel (parade_figures.gdshader TONE, CALM_COLS):
## tone 0 = as drawn, 1 = darker (x0.74), 2 = lighter (x1.32), 3 = darkest (x0.56), 4 = x0.9, 5 = x1.12, 6 = x0.82,
## 7 = x1.2; group = the colour a calmed far figure takes (0 dark coats, 1..4 the avenue's delegations).
static func _ft(flip: bool, tone: int, group: int = 0) -> float:
	return (1.0 if flip else 0.0) + 2.0 * float(clampi(tone, 0, 7)) + 16.0 * float(clampi(group, 0, 7))


## points: Array of [Vector3 feet (local), slot, frames, phase, flip (+ 2 * tone, see _ft)]
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


## The crowd behind the barriers, backs to the camera.  Staggered lattice (every person owns one cell, so nobody
## stands inside anybody: >= 0.42 m side by side, >= 0.38 m diagonally), thinned by a density field: pressed
## against the barrier in near-rows, looser further back, in loose clusters with gaps and a few clearings, fraying
## over ~10 m into a ragged back edge with stragglers (shot p7) and thinning out towards both plaza ends.  Coats,
## hats and heights come from the drawn variants + children, mirrored at random, with a per-person tone; direct
## neighbours never wear the same coat and the ~22 people nearest to the p5 lens are all different.  Nobody stands
## where a moving camera would pass him closer than its min_depth while he is in the frame (the shader hides
## figures nearer than min_depth: he would vanish mid-shot).
func _build_crowd() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 1966
	var pts: Array = []
	var cs := _slot("crowd")
	var cf := _slot("child_flag")
	var ck := _slot("child")
	var n_var := maxi(int(cs[1]), 1)
	# the crowd's backs face away from the floodlights: a little extra self light keeps the coats apart, a bit more
	# on the small far figures (shot p7 looks across the whole depth of the crowd)
	fig_mat.set_shader_parameter("lift_slots", float(maxi(int(cs[0]) + int(cs[1]), maxi(int(cf[0]),
		int(ck[0])) + 1)))
	fig_mat.set_shader_parameter("lift", 0.16)
	fig_mat.set_shader_parameter("lift_far", 1.0)
	var cams := _min_depth_paths()
	var span := P5_EYE.z - (Z_CROWD_FRONT + 0.4)
	var konrad := Vector2(-104.0, Z_CROWD_BACK + 13.0)
	var holes: Array = []
	for i in 34:
		holes.append(Vector3(r.randf_range(X_MIN + 6.0, X_MAX - 6.0), r.randf_range(Z_CROWD_FRONT + 7.0,
			Z_CROWD_BACK - 4.0), r.randf_range(0.9, 2.6)))
	var grid := {}                                            # 1 m cell -> variant slots standing in it
	var aside: Array = []                                     # stand in the way of the moving p5 lens
	var z := Z_CROWD_FRONT + 0.35
	var row := 0
	while z < Z_CROWD_BACK + 4.0:
		var din := z - Z_CROWD_FRONT                          # metres behind the barrier line
		var k := clampf(din / 40.0, 0.0, 1.0)
		var dx := lerpf(0.6, 0.86, k)
		var dz := lerpf(0.62, 0.95, k)
		var x := X_MIN + (0.5 * dx if row % 2 == 1 else 0.0)
		var row_holes: Array = []
		for hv: Vector3 in holes:
			if absf(z - hv.y) * 1.3 < hv.z + 0.3:
				row_holes.append(hv)
		while x < X_MAX:
			var px := x + r.randf_range(-0.09, 0.09)
			var pz := z + r.randf_range(-0.13, 0.13)
			x += dx
			# density: pressed at the barrier, looser behind, clustered, ragged back edge and plaza ends
			var dens := lerpf(0.93, 0.62, clampf((din - 2.5) / 26.0, 0.0, 1.0))
			var edge := 45.5 + 2.6 * sin(px * 0.21) + 1.7 * sin(px * 0.067 + 1.0)
			if din > edge:
				dens = 0.05 if din < edge + 5.0 else 0.0
			else:
				dens *= lerpf(0.3, 1.0, clampf((edge - din) / 10.0, 0.0, 1.0))
			var n := 0.5 + 0.32 * sin(px * 0.41 + pz * 0.23) * sin(px * 0.17 - pz * 0.37 + 1.3) \
				+ 0.18 * sin(px * 0.9 + pz * 1.3)
			if din > 3.0:
				dens *= lerpf(0.5, 1.2, clampf(n, 0.0, 1.0))
			dens *= smoothstep(X_MIN - 1.0, X_MIN + 9.0, px) * smoothstep(X_MAX + 1.0, X_MAX - 9.0, px)
			if r.randf() >= dens:
				continue
			var skip := false
			for hv: Vector3 in row_holes:
				if Vector2(px - hv.x, (pz - hv.y) * 1.3).length() < hv.z:
					skip = true
					break
			if skip:
				continue
			# the narrow line of sight through which shot p5 looks at the family (camera ~ P5_EYE)
			if pz > Z_CROWD_FRONT + 1.0 and pz < P5_EYE.z:
				var d := P5_EYE.z - pz
				var xc := lerpf(P5_EYE.x, FAMILY_X, d / span)
				if absf(px - xc) < 0.55 + 1.9 * d / span:
					continue
			if absf(px - FAMILY_X) < 2.6 and pz <= Z_CROWD_FRONT + 1.4:
				continue
			# Konrad's spot behind the back edge (shot p7) stays clear
			if Vector2(px, pz).distance_to(konrad) < 7.0:
				continue
			if _pops_in_view(px, pz, cams):
				aside.append(Vector2(px, pz))
				continue
			var tone := 0
			var tr := r.randf()
			if tr < 0.16:
				tone = 1
			elif tr < 0.3:
				tone = 4
			elif tr < 0.44:
				tone = 2
			elif tr < 0.56:
				tone = 5
			elif tr < 0.59:
				tone = 3
			var u := r.randf()
			var slot: int
			if u < 0.018:
				slot = int(cf[0])
			elif u < 0.05:
				slot = int(ck[0])
			else:
				# no two direct neighbours in the same coat
				var cell := Vector2i(floori(px), floori(pz))
				slot = int(cs[0]) + r.randi_range(0, n_var - 1)
				for attempt in 8:
					if not _variant_near(grid, cell, slot):
						break
					slot = int(cs[0]) + r.randi_range(0, n_var - 1)
				if not grid.has(cell):
					grid[cell] = []
				(grid[cell] as Array).append(slot)
			pts.append([Vector3(px, 0.0, pz), slot, 1, 0, _ft(r.randf() < 0.5, tone)])
		z += dz
		row += 1
	stats["crowd_stepped_aside"] = aside.size()
	stats["crowd_no_room_aside"] = _step_aside(pts, aside, cams, cs, r)
	_p5_unique(pts, cs, r)
	_mm(self, pts, fig_mat, "Crowd")


## The people lining the avenue between the street and the plaza (hall_avenue.gd stages the avenue itself; only
## shot p8 sees them, from its crane above the street): held back behind both cordon barriers, from the cleared
## street -- a few small knots -- to the plaza, where they stand 17-24 m deep (Avenue.crowd_depth).  Even the
## spectators are organised (Avenue.LANES / CROSS / crowd_groups): from ~260 m on, marshals' lanes run along the
## avenue through each crowd and cross-gaps cut through it at the gates, first-aid posts and loudspeaker masts.  The
## front strip is pressed against the barrier in close rows; the middle strip is taken by delegations standing in
## blocks in like coats (works brigades in grey-blue, leagues in brown, clubs in black, women's leagues in light
## coats) between stretches of ordinary people; the back strip loosens into clusters with clearings, families and a
## ragged edge with stragglers.  Lines across the depth every 0.85 m along the avenue (heavily foreshortened from
## p8); room around lamp posts and masts (Avenue.crowd_clear).  The plaza crowd's drawn coats, children and tones;
## direct neighbours never wear the same coat where the group allows it.  Each figure carries its group, so the
## far calm of shot p8 turns a delegation into one patch of its colour instead of gravel.
func _build_avenue_crowd() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 1968
	var pts: Array = []
	var cs := _slot("crowd")
	var cf := _slot("child_flag")
	var ck := _slot("child")
	var n_var := maxi(int(cs[1]), 1)
	var grid := {}                                              # 1 m cell -> variant slots standing in it
	var counts := [0, 0, 0, 0, 0]
	for side: float in [-1.0, 1.0]:
		var xb: float = Avenue.X_BARRIER_L if side < 0.0 else Avenue.X_BARRIER_R
		var groups := Avenue.crowd_groups(side)
		var lanes: Array = Avenue.LANES[int(side)]
		var l_end: float = (lanes[lanes.size() - 1] as Array)[1]
		var holes := {}                                         # 5 m bucket along z -> clearings [depth, z, r]
		for i in 44:
			var hv := Vector3(r.randf_range(9.0, 26.0), r.randf_range(AV_Z_FAR + 4.0, -230.0), r.randf_range(0.9, 2.4))
			for b in range(floori((hv.y - hv.z) / 5.0), floori((hv.y + hv.z) / 5.0) + 1):
				if not holes.has(b):
					holes[b] = []
				(holes[b] as Array).append(hv)
		var zl := AV_Z_NEAR
		var li := 0
		while zl > AV_Z_FAR:
			var edge0 := Avenue.crowd_depth(side, zl)
			var near := smoothstep(-135.0, -210.0, zl)
			var knot := clampf(sin(zl * 0.37 + side * 2.1) * sin(zl * 0.113 + 0.7) * 2.6 - 0.7, 0.0, 1.0)
			var grp_mid := Avenue.group_at(groups, zl)
			var organised := Avenue.lane_active(side, 0, zl)
			var dd := 0.45 + (0.31 if li % 2 == 1 else 0.0)
			while dd < edge0 + 4.0:
				var strip := Avenue.strip_at(side, dd, zl)
				var orderly := (strip == 0 and organised) or (strip == 1 and grp_mid > 0)
				var pd := dd + (r.randf_range(-0.05, 0.05) if orderly else r.randf_range(-0.1, 0.1))
				var pz := zl + (r.randf_range(-0.08, 0.08) if orderly else r.randf_range(-0.16, 0.16))
				# rows across the depth: close in front and in the delegations, looser towards the back edge
				if strip == 2:
					dd += lerpf(0.7, 0.95, clampf((dd - l_end) / 8.0, 0.0, 1.0))
				elif organised:
					dd += 0.62 if (strip == 1 and grp_mid > 0) else 0.64
				else:
					dd += lerpf(0.62, 0.92, clampf(dd / 20.0, 0.0, 1.0))
				if strip == -1 or Avenue.cross_gap(side, pz):
					continue
				if side > 0.0 and pd > l_end and Avenue.in_stand(pz, 0.6):
					continue                                        # the grandstand rises behind the right lane
				var grp := grp_mid if strip == 1 else 0
				var n := 0.5 + 0.32 * sin(pz * 0.41 + pd * 0.23 + side) * sin(pz * 0.17 - pd * 0.37 + 1.3) \
					+ 0.18 * sin(pz * 0.9 + pd * 1.3)
				var dens: float
				if pd > edge0:
					dens = 0.05                                     # stragglers behind the ragged back edge
				elif not organised:
					dens = lerpf(0.94, 0.52, clampf((pd - 1.6) / 9.0, 0.0, 1.0))
					dens *= lerpf(0.3, 1.0, clampf((edge0 - pd) / 6.0, 0.0, 1.0))
					if pd > 2.2:
						dens *= lerpf(0.5, 1.2, clampf(n, 0.0, 1.0))
				elif strip == 0:
					dens = lerpf(0.96, 0.86, clampf(pd / 6.0, 0.0, 1.0))
				elif strip == 1:
					dens = 0.95 if grp > 0 else 0.84 * lerpf(0.75, 1.1, clampf(n, 0.0, 1.0))
				else:
					dens = lerpf(0.82, 0.55, clampf((pd - l_end) / 7.0, 0.0, 1.0))
					dens *= lerpf(0.3, 1.0, clampf((edge0 - pd) / 5.0, 0.0, 1.0))
					dens *= lerpf(0.4, 1.25, clampf(n, 0.0, 1.0))
				if near < 1.0:                                      # the cleared street: only small knots
					dens *= lerpf(knot * clampf(1.0 - pd / 5.0, 0.0, 1.0), 1.0, near)
				if r.randf() >= dens or Avenue.gate_corridor(side, pz):
					continue
				var px := xb + side * pd
				if not Avenue.crowd_clear(px, pz):
					continue
				if strip == 2 or not organised:
					var skip := false
					for hv: Vector3 in holes.get(floori(pz / 5.0), []):
						if Vector2(pd - hv.x, pz - hv.y).length() < hv.z:
							skip = true
							break
					if skip:
						continue
				var tone := 0
				var tr := r.randf()
				if tr < 0.16:
					tone = 1
				elif tr < 0.3:
					tone = 4
				elif tr < 0.44:
					tone = 2
				elif tr < 0.56:
					tone = 5
				elif tr < 0.59:
					tone = 3
				var u := r.randf()
				var slot: int
				if grp == 0 and strip != 0 and u < 0.02:
					slot = int(cf[0])
				elif grp == 0 and strip != 0 and u < 0.06:
					slot = int(ck[0])
				else:
					var cell := Vector2i(floori(px), floori(pz))
					slot = int(cs[0]) + mini(_coat(r, grp), n_var - 1)
					for attempt in 6:
						if not _variant_near(grid, cell, slot):
							break
						slot = int(cs[0]) + mini(_coat(r, grp), n_var - 1)
					if not grid.has(cell):
						grid[cell] = []
					(grid[cell] as Array).append(slot)
				counts[grp] += 1
				pts.append([Vector3(px, 0.0, pz), slot, 1, 0, _ft(r.randf() < 0.5, tone, grp)])
			zl -= 0.85
			li += 1
	# the right grandstands (Avenue.STAND_*): two rows on every tier; delegations in blocks of two tiers by half a
	# section between ordinary spectators
	var seq := [0, 1, 0, 2, 3, 0, 4, 0, 1, 0, 2, 0, 0, 3, 1, 4, 0, 2]
	var n_stand := 0
	for si in Avenue.STAND_SECTIONS.size():
		var sec: Array = Avenue.STAND_SECTIONS[si]
		var zmid := (float(sec[0]) + float(sec[1])) * 0.5
		for i in Avenue.STAND_TIERS:
			var t: Vector3 = Avenue.stand_tier(i)
			for xr: float in [t.x + 0.55, t.x + 1.3]:
				var zs: float = float(sec[0]) - 0.35 - r.randf_range(0.0, 0.3)
				while zs > float(sec[1]) + 0.35:
					var grp: int = seq[(si * 6 + (i / 2) * 2 + (0 if zs > zmid else 1)) % seq.size()]
					if r.randf() < 0.92:
						var slot := int(cs[0]) + mini(_coat(r, grp), n_var - 1)
						var tone: int = [0, 0, 1, 4, 2, 5][r.randi_range(0, 5)]
						pts.append([Vector3(xr + r.randf_range(-0.08, 0.08), t.y, zs), slot, 1, 0,
							_ft(r.randf() < 0.5, tone, grp)])
						counts[grp] += 1
						n_stand += 1
					zs -= r.randf_range(0.5, 0.62)
	stats["avenue_groups"] = counts
	stats["grandstand_people"] = n_stand
	_mm(self, pts, fig_mat, "AvenueCrowd")


## A coat (index into the drawn crowd variants) for a person of clothing group `grp` (Avenue.COATS_*).
static func _coat(r: RandomNumberGenerator, grp: int) -> int:
	var u := r.randf()
	var pool: Array
	match grp:
		1:
			pool = Avenue.COATS_STEEL if u < 0.8 else Avenue.COATS_DARK
		2:
			pool = Avenue.COATS_BROWN if u < 0.72 else (Avenue.COATS_DARK if u < 0.9 else Avenue.COATS_WARM)
		3:
			pool = [0, 4, 10, 17, 20]
		4:
			pool = Avenue.COATS_PALE if u < 0.45 else (Avenue.COATS_STEEL if u < 0.75 else Avenue.COATS_DARK)
		_:
			if u < 0.7:
				pool = Avenue.COATS_DARK
			elif u < 0.82:
				pool = Avenue.COATS_STEEL
			elif u < 0.93:
				pool = Avenue.COATS_BROWN
			elif u < 0.97:
				pool = Avenue.COATS_WARM
			else:
				pool = Avenue.COATS_PALE
	return int(pool[r.randi_range(0, pool.size() - 1)])


func _variant_near(grid: Dictionary, cell: Vector2i, slot: int) -> bool:
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			var a: Variant = grid.get(cell + Vector2i(ox, oy))
			if a != null and (a as Array).has(slot):
				return true
	return false


## People the moving lens would pass too closely (they would vanish in mid-frame, see _pops_in_view) step aside
## instead: each moves sideways, away from the camera path, to the nearest free spot (>= 0.45 m from everybody)
## from which he leaves the frame before the lens comes closer than min_depth -- so the big backs still frame the
## shot and slide out of it.  Returns how many found no such spot (they are left out).
func _step_aside(pts: Array, aside: Array, cams: Array, cs: Array, r: RandomNumberGenerator) -> int:
	if aside.is_empty():
		return 0
	var zlo := 1e9
	var zhi := -1e9
	for a: Vector2 in aside:
		zlo = minf(zlo, a.y)
		zhi = maxf(zhi, a.y)
	var near := {}                                            # 0.5 m cell -> positions (only around the movers)
	for p: Array in pts:
		var v: Vector3 = p[0]
		if v.z > zlo - 2.0 and v.z < zhi + 2.0:
			_cell_add(near, Vector2(v.x, v.z))
	var lost := 0
	for a: Vector2 in aside:
		var side := 1.0 if a.x >= P5_EYE.x else -1.0
		var spot := Vector2.INF
		for k in range(1, 16):
			for oz: float in [0.0, 0.22, -0.22]:
				var q := Vector2(a.x + side * 0.2 * float(k), a.y + oz)
				if not _cell_free(near, q, 0.45) or _pops_in_view(q.x, q.y, cams):
					continue
				spot = q
				break
			if spot != Vector2.INF:
				break
		if spot == Vector2.INF:
			lost += 1
			continue
		_cell_add(near, spot)
		var tone: int = [0, 0, 4, 5, 1][r.randi_range(0, 4)]
		pts.append([Vector3(spot.x, 0.0, spot.y), int(cs[0]) + r.randi_range(0, maxi(int(cs[1]), 1) - 1), 1, 0,
			_ft(r.randf() < 0.5, tone)])
	return lost


static func _cell_add(cells: Dictionary, q: Vector2) -> void:
	var key := Vector2i(floori(q.x * 2.0), floori(q.y * 2.0))
	if not cells.has(key):
		cells[key] = []
	(cells[key] as Array).append(q)


static func _cell_free(cells: Dictionary, q: Vector2, d: float) -> bool:
	var key := Vector2i(floori(q.x * 2.0), floori(q.y * 2.0))
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			var a: Variant = cells.get(key + Vector2i(ox, oy))
			if a == null:
				continue
			for o: Vector2 in (a as Array):
				if o.distance_to(q) < d:
					return false
	return true


## The people nearest to the p5 lens (the largest figures of the whole cinematic) all wear different coats:
## they are dealt from a shuffled deck of the drawn variants, nearest first.
func _p5_unique(pts: Array, cs: Array, r: RandomNumberGenerator) -> void:
	var c0 := int(cs[0])
	var n := maxi(int(cs[1]), 1)
	var near: Array = []
	for i in pts.size():
		var s := int(pts[i][1])
		if s < c0 or s >= c0 + n:
			continue
		var p: Vector3 = pts[i][0]
		var d := P5_EYE.z - p.z
		if d > 2.0 and d < 18.0 and absf(p.x - P5_EYE.x) < d * 0.42 + 0.6:
			near.append([d, i])
	near.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
	var deck: Array = []
	for e: Array in near:
		if deck.is_empty():
			for v in n:
				deck.append(c0 + v)
			for v in range(n - 1, 0, -1):
				var j := r.randi_range(0, v)
				var tmp: int = deck[v]
				deck[v] = deck[j]
				deck[j] = tmp
		pts[int(e[1])][1] = deck.pop_back()
		# the big near backs keep their drawn colours (no darkened coats fusing into a wall at the frame edge)
		var flip := fposmod(float(pts[int(e[1])][4]), 2.0) > 0.5
		pts[int(e[1])][4] = _ft(flip, [0, 0, 4, 5, 2][r.randi_range(0, 4)])


## Camera paths of the shots that stand inside the crowd and move in depth (min_depth > 0, p0.z != p1.z):
## [PackedVector3Array samples, min_depth, lowest z, highest z].
func _min_depth_paths() -> Array:
	var out: Array = []
	var sh: RefCounted = ParadeShots.new()
	for s: Dictionary in ParadeShots.SHOTS:
		var md := float(s.get("min_depth", 0.0))
		if md <= 0.0 or absf((s["p0"] as Vector3).z - (s["p1"] as Vector3).z) < 0.001:
			continue
		var path := PackedVector3Array()
		var zlo := 1e9
		var zhi := -1e9
		for i in 41:
			var t := lerpf(float(s["start"]), float(s["end"]), float(i) / 40.0)
			var cp: Vector3 = sh.call("sample", t)["pos"]
			path.append(cp)
			zlo = minf(zlo, cp.z)
			zhi = maxf(zhi, cp.z)
		out.append([path, md, zlo, zhi])
	return out


## True when a figure at (px, pz) would be inside the frame both nearer and farther than the shot's min_depth
## (the shader hides it while it is nearer: it would pop in or out of existence in front of the lens).
func _pops_in_view(px: float, pz: float, cams: Array) -> bool:
	for c: Array in cams:
		var md: float = c[1]
		if pz < float(c[2]) - md - 0.6 or pz > float(c[3]) - md + 0.6:
			continue
		var near := false
		var far := false
		for cp: Vector3 in (c[0] as PackedVector3Array):
			var d := cp.z - pz
			if d <= 0.06 or absf(px - cp.x) > d * VIEW_TAN + 0.55:
				continue
			if d < md + 0.15:
				near = true
			if d >= md - 0.15:
				far = true
		if near and far:
			return true
	return false


## Guards at the barrier, facing the crowd (every 8 m, rifle at order / slung alternating).  At the evicted family
## (shot p5) the regular post is replaced by two guards right behind the barrier who frame them instead of
## standing in them.
func _build_guards() -> void:
	var pts: Array = []
	var g := _slot("guard")
	var nb := int(g[1]) - 1
	var x := X_MIN + 4.0
	var k := 0
	while x < X_MAX:
		if absf(x - FAMILY_X) > 4.5:
			pts.append([Vector3(x, 0.0, Z_GUARDS), int(g[0]) + (mini(nb, 1) if k % 3 == 1 else 0), 1, 0,
				_ft(k % 2 == 1, 0)])
		x += 8.0
		k += 1
	pts.append([Vector3(FAMILY_X - 2.4, 0.0, Z_GUARDS + 0.7), int(g[0]), 1, 0, _ft(false, 0)])
	pts.append([Vector3(FAMILY_X + 2.3, 0.0, Z_GUARDS + 0.7), int(g[0]) + mini(nb, 1), 1, 0, _ft(true, 0)])
	_mm(self, pts, fig_mat, "Guards")


## Standing formations beside the tribune: 6 x 2 blocks of 14 files x 10 ranks on an exact grid (straight
## dressing), each with its leader one pace in front; one rank lines the far side of the lane.
func _build_formations() -> void:
	var pts: Array = []
	var s := _slot("stand")
	var ld := _slot("leader")
	for side: float in [-1.0, 1.0]:
		for b in 3:
			for r in 2:
				var x0: float = HX + side * (40.0 + b * 23.5) - (17.5 if side < 0 else 0.0)
				var z0 := -912.0 - r * 18.0
				for i in 14:
					for j in 10:
						pts.append([Vector3(x0 + i * 1.25 + 0.6, 0.0, z0 - j * 1.5), s[0], 1, 0, _ft(false, 0)])
				pts.append([Vector3(x0 + 6.5 * 1.25 + 0.6, 0.0, z0 + 1.7), ld[0], 1, 0, _ft(false, 0)])
	# a single rank lines the far side of the lane, facing the crowd -- not in front of the tribune, and not where
	# the low p2 camera would see it through the gaps between the ranks of the marching column (it would stand
	# among the marching men at two thirds of their size)
	var x := X_MIN + 2.0
	while x < X_MAX:
		if absf(x - HX) > 60.0:
			pts.append([Vector3(x, 0.0, -888.5), s[0], 1, 0, _ft(false, 0)])
		x += 2.2
	_mm(self, pts, fig_mat, "Formations")


func _build_officials() -> void:
	var pts: Array = []
	var o := _slot("official")
	var n := maxi(int(o[1]), 1)
	var front := [1, 2, 1, 0, 2, 0, 2, 0, 1, 2, 1]
	var back := [2, 0, 1, 0, 1, 0, 2]
	for k in 11:
		pts.append([Vector3(HX - 10.0 + k * 2.0, 6.0, Z_TRIBUNE - 3.0), int(o[0]) + int(front[k]) % n, 1, 0,
			_ft(k > 5, 0)])
	for k in 7:
		pts.append([Vector3(HX - 8.0 + k * 2.6 + 1.0, 6.0, Z_TRIBUNE - 6.5), int(o[0]) + int(back[k]) % n, 1, 0,
			_ft(k % 2 == 0, 1)])
	_mm(self, pts, fig_mat, "Officials")


## Marching blocks: 15 ranks x 4 files (1.45 m x 1.0 m) on the crowd side of the lane (the lane centre stays the
## vehicles').  Four abreast instead of a wide block: from the low p2 camera every rank of an 8-file block stacked
## into one slanted slab of half-hidden men; four abreast, each rank reads as men one behind the other with clear
## air between the ranks.  Straight dressing, the whole block in step with a hair of per-man timing, the tones
## vary only a little (no dark rear files).  A colour party (bearer + 2 escorts) leads each block.
func _build_march() -> void:
	var m := _slot("march")
	var frames := maxi(int(m[1]), 1)
	fig_mat.set_shader_parameter("fps", STEP_FPS * float(frames) / 4.0)
	var bn: Material = mats.get("flag_street")
	var r := RandomNumberGenerator.new()
	r.seed = 1967
	var files := 4
	var ranks := 15
	var zc := Z_LANE + 1.6
	var oz := zc - Z_LANE
	for k in BLOCKS:
		var blk := Node3D.new()
		blk.name = "MarchBlock%d" % k
		add_child(blk)
		var pts: Array = []
		for rank in ranks:
			for file in files:
				var lx := -2.7 - rank * 1.45 + r.randf_range(-0.02, 0.02)
				var lz := zc + (float(file) - 0.5 * float(files - 1)) * 1.0
				var tone := 0 if file == files - 1 else (4 if r.randf() < 0.4 else 0)
				pts.append([Vector3(lx, 0.0, lz), m[0], frames, r.randf() * 0.2, _ft(false, tone)])
		# colour party: the bearer holds the pole in front of him, two escorts beside him
		pts.append([Vector3(0.42, 0.0, Z_LANE + 0.3 + oz), m[0], frames, r.randf() * 0.2, _ft(false, 0)])
		pts.append([Vector3(0.42, 0.0, Z_LANE + 1.45 + oz), m[0], frames, r.randf() * 0.2, _ft(false, 0)])
		pts.append([Vector3(0.42, 0.0, Z_LANE - 1.25 + oz), m[0], frames, r.randf() * 0.2, _ft(false, 4)])
		_mm(blk, pts, fig_mat, "March%d" % k)
		# pole + banner (Symbols-resolved flag_street material); the pole starts at the bearer's hands
		var kit := Kit.new()
		kit.box(Vector3(0.6, 0.95, Z_LANE - 0.05 + oz), Vector3(0.1, 3.65, 0.1), c(NIGHT[3]))
		kit.box(Vector3(0.0, 4.45, Z_LANE - 0.05 + oz), Vector3(1.6, 0.08, 0.08), c(NIGHT[3]))
		var pole := MeshInstance3D.new()
		pole.mesh = kit.commit()
		pole.material_override = mats.get("metal")
		blk.add_child(pole)
		if bn:
			var fz := Z_LANE + 0.05 + oz
			var fk := Kit.new()
			fk.quad(Vector3(0.05, 2.0, fz), Vector3(0.05, 4.4, fz), Vector3(1.55, 4.4, fz), Vector3(1.55, 2.0, fz),
				Color.WHITE, 0.3)
			var fl := MeshInstance3D.new()
			fl.mesh = fk.commit()
			fl.material_override = bn
			blk.add_child(fl)
		march_blocks.append(blk)


## Snow dust thrown off the rear of every track + cold exhaust vapour (emitters live in parade_vehicles.gd).
## (dithered low veils, vehicle_dust.gdshader -- no longer the opaque figure-atlas puff sprites)
func _build_puffs() -> void:
	if veh:
		veh.build_dust()
		stats["Puffs"] = int(veh.stats.get("dust_puffs", 0))


func _update_puffs(t: float) -> void:
	if veh:
		veh.update_dust(t)


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


## The reviewing stand.  Stone platform (deck y = 6, front edge z = Z_TRIBUNE) with plinth and cornice bands,
## pilasters and ashlar courses (course joints from the material, staggered vertical joints as strips); a
## balustrade along the front and both ends; a broad central stair in two flights with a landing, cheek walls with
## copings and pedestals carrying floodlight frames; the lectern with a fan of microphones at the head of the stair;
## the back wall with pilasters, moulding and dentils, three banners hanging in folds from rods (Symbols-resolved
## banner_portico material); two stepped, fluted pylons with loudspeaker clusters; floodlight frames on the deck
## corners.  The deck behind the balustrade (z Z_TRIBUNE - 0.8 .. - 11) stays free for the officials.
func _build_tribune() -> void:
	if not mats.has("trib_stone") and mats.get("stone") is ShaderMaterial:
		var tm: ShaderMaterial = (mats["stone"] as ShaderMaterial).duplicate()
		tm.set_shader_parameter("course", 0.9)
		tm.set_shader_parameter("course_dark", 0.8)
		mats["trib_stone"] = tm
	var s := K("trib_stone")
	var m := K("metal")
	var l := K("lamp")
	var zf := Z_TRIBUNE
	var x0 := HX - 30.0
	var x1 := HX + 30.0
	var sw := 7.0                                    # half width of the stair
	var zs := zf + 10.0                              # foot of the stair
	var face := {"front": c(VIOLET[3]), "side": c(VIOLET[2]), "top": c(SNOW[3])}
	var lite := {"front": c(STONE[4]), "side": c(STONE[3]), "top": c(SNOW[4])}
	var base := {"front": c(VIOLET[2]), "side": c(VIOLET[1]), "top": c(SNOW[3])}
	var jc := c(VIOLET[2])                           # joints on the platform (lighter face)
	var jd := c(VIOLET[1])                           # joints / flutes on the darker back wall and pylons
	# --- platform body, plinth / cornice bands around front and ends, pilasters, vertical joints
	s.box(Vector3(x0, 0.0, zf - 12.0), Vector3(60.0, 6.0, 12.0), face)
	for band in [[0.0, 0.72, 0.22, base], [5.42, 6.04, 0.26, lite]]:
		var y0: float = band[0]
		var y1: float = band[1]
		var o: float = band[2]
		s.box(Vector3(x0 - o, y0, zf - 0.3), Vector3(HX - sw - 0.8 - x0 + o, y1 - y0, 0.3 + o), band[3])
		s.box(Vector3(HX + sw + 0.8, y0, zf - 0.3), Vector3(x1 + o - HX - sw - 0.8, y1 - y0, 0.3 + o), band[3])
		s.box(Vector3(x0 - o, y0, zf - 11.6), Vector3(0.3 + o, y1 - y0, 11.3), band[3])
		s.box(Vector3(x1 - 0.3, y0, zf - 11.6), Vector3(0.3 + o, y1 - y0, 11.3), band[3])
	var pil: Array = [x0 + 0.6, HX - 26.2, HX - 18.8, HX - 11.4, HX + 11.4, HX + 18.8, HX + 26.2, x1 - 0.6]
	for px: float in pil:
		s.box(Vector3(px - 0.55, 0.72, zf), Vector3(1.1, 4.7, 0.2), face)
	for k in range(1, 6):
		var y0 := 0.9 * k
		var h := minf(0.9, 5.42 - y0)
		var x := x0 + 0.9 * float(k % 2) + 0.9
		while x < x1 - 0.5:
			var near_pil := false
			for px: float in pil:
				if absf(x - px) < 0.75:
					near_pil = true
			if not near_pil and absf(x - HX) > sw + 1.0:
				s.box(Vector3(x - 0.045, y0, zf), Vector3(0.09, h, 0.006), jc, Kit.FACE_PZ)
			x += 1.8
		var z := zf - 0.9 - 0.9 * float(k % 2)
		while z > zf - 11.5:
			s.box(Vector3(x1, y0, z - 0.045), Vector3(0.006, h, 0.09), jc, Kit.FACE_PX)
			s.box(Vector3(x0 - 0.006, y0, z - 0.045), Vector3(0.006, h, 0.09), jc, Kit.FACE_NX)
			z -= 1.8
	# --- balustrade: plinth, balusters, coping, posts; front (either side of the stair) and both ends
	var by := 6.0
	for sp in [[x0 + 0.05, HX - sw], [HX + sw, x1 - 0.05]]:
		var xa: float = sp[0]
		var xb: float = sp[1]
		s.box(Vector3(xa, by, zf - 0.68), Vector3(xb - xa, 0.22, 0.7), base)
		s.box(Vector3(xa - 0.04, by + 0.84, zf - 0.74), Vector3(xb - xa + 0.08, 0.2, 0.82), lite)
		var n := int((xb - xa) / 0.42)
		for i in n:
			_baluster(s, Vector3(xa + (i + 0.5) * (xb - xa) / n, by + 0.22, zf - 0.33), lite)
	for xc: float in [x0 + 0.38, x1 - 0.38]:
		s.box(Vector3(xc - 0.35, by, zf - 11.0), Vector3(0.7, 0.22, 10.32), base)
		s.box(Vector3(xc - 0.41, by + 0.84, zf - 11.0), Vector3(0.82, 0.2, 10.26), lite)
		for i in 24:
			_baluster(s, Vector3(xc, by + 0.22, zf - 0.9 - (i + 0.5) * 10.0 / 24.0), lite)
	for px: float in pil + [HX - sw - 0.3, HX + sw + 0.3]:
		s.box(Vector3(px - 0.3, by, zf - 0.72), Vector3(0.6, 1.1, 0.76), lite)
	# --- central stair: 15 + 15 risers of 0.2 m, treads 0.3 m, a 1.3 m landing halfway
	var stair := {"front": c(VIOLET[3]), "side": c(VIOLET[2]), "top": c(SNOW[3])}
	for i in 30:
		var zfr := zs - 0.3 * i if i < 15 else zs - 5.5 - 0.3 * (i - 15)
		s.box(Vector3(HX - sw, 0.0, zf), Vector3(2.0 * sw, 0.2 * (i + 1), zfr - zf), stair, Kit.FACE_PZ | Kit.FACE_PY)
	var zlf := zs - 4.2
	var zlb := zs - 5.5
	for side: float in [-1.0, 1.0]:
		var wa := minf(HX + side * sw, HX + side * (sw + 0.8))
		var wb := maxf(HX + side * sw, HX + side * (sw + 0.8))
		var xc := (wa + wb) * 0.5
		s.prism([Vector2(zs + 0.3, 0.0), Vector2(zs + 0.3, 1.1), Vector2(zlf, 3.9), Vector2(zlb, 3.9),
			Vector2(zlb, 0.0)], Vector3.ZERO, Vector3.BACK, Vector3.UP, Vector3.RIGHT, wa, wb, face)
		s.prism([Vector2(zlb, 0.0), Vector2(zlb, 3.9), Vector2(zf + 0.3, 6.9), Vector2(zf, 6.9), Vector2(zf, 0.0)],
			Vector3.ZERO, Vector3.BACK, Vector3.UP, Vector3.RIGHT, wa, wb, face)
		# stepped coping: level blocks climbing with each flight (a sloped coping catches the snow and the floods
		# as one flat bright wedge), stone faces towards the plaza, snow only on the level tops
		var cop := {"front": c(STONE[3]), "side": c(STONE[2]), "top": c(SNOW[3])}
		for fl in [[zs + 0.3, 1.1, zlf, 3.9, 6], [zlb, 3.9, zf + 0.3, 6.9, 6]]:
			var za0: float = fl[0]
			var ya0: float = fl[1]
			var zb0: float = fl[2]
			var yb0: float = fl[3]
			var nb: int = fl[4]
			for i in nb:
				var za := lerpf(za0, zb0, float(i) / nb)
				var zb := lerpf(za0, zb0, float(i + 1) / nb)
				var ylo := lerpf(ya0, yb0, float(i) / nb) - 0.06
				var yhi := lerpf(ya0, yb0, float(i + 1) / nb) + 0.12
				s.box(Vector3(xc - 0.5, ylo, zb), Vector3(1.0, yhi - ylo, za - zb), cop, Kit.FACES_ALL)
				s.box(Vector3(xc - 0.53, yhi - 0.04, zb - 0.025), Vector3(1.06, 0.065, za - zb + 0.05),
					{"front": c(STONE[4]), "side": c(STONE[3]), "top": c(SNOW[4])})
		s.box(Vector3(xc - 0.5, 3.84, zlb), Vector3(1.0, 0.18, zlf - zlb), cop, Kit.FACES_ALL)
		s.box(Vector3(xc - 0.5, 6.84, zf), Vector3(1.0, 0.18, 0.3), cop, Kit.FACES_ALL)
		# pedestal at the foot with a floodlight frame aimed up at the speaker
		s.box(Vector3(xc - 0.75, 0.0, zs - 0.2), Vector3(1.5, 1.7, 1.5), face)
		s.box(Vector3(xc - 0.86, 1.7, zs - 0.31), Vector3(1.72, 0.2, 1.72), lite)
		_floodframe(m, l, Vector3(xc, 1.9, zs + 0.55), Vector3(HX, 7.4, zf - 0.6), 2, 2, 2.0)
	# --- lectern at the head of the stair: plinth, tapered body, slanted desk, front panel, microphones
	s.box(Vector3(HX - 0.78, by, zf - 1.02), Vector3(1.56, 0.12, 0.96), lite)
	s.prism([Vector2(-0.55, 0.12), Vector2(0.55, 0.12), Vector2(0.7, 1.15), Vector2(-0.7, 1.15)],
		Vector3(HX, by, 0.0), Vector3.RIGHT, Vector3.UP, Vector3.BACK, zf - 0.92, zf - 0.24, lite)
	s.prism([Vector2(zf - 0.16, 1.27), Vector2(zf - 0.16, 1.15), Vector2(zf - 1.0, 1.15), Vector2(zf - 1.0, 1.19)],
		Vector3(0.0, by, 0.0), Vector3.BACK, Vector3.UP, Vector3.RIGHT, HX - 0.78, HX + 0.78, lite)
	s.box(Vector3(HX - 0.36, by + 0.36, zf - 0.24), Vector3(0.72, 0.6, 0.03), base)
	m.beam(Vector3(HX - 0.36, by + 1.36, zf - 0.12), Vector3(HX + 0.36, by + 1.36, zf - 0.12), 0.035, 0.035,
		c(STEEL[3]))
	for sx: float in [-0.3, 0.3]:
		m.beam(Vector3(HX + sx, by + 1.24, zf - 0.17), Vector3(HX + sx, by + 1.36, zf - 0.12), 0.03, 0.03, c(STEEL[2]))
	for i in 6:
		var mx := HX - 0.3 + i * 0.12
		var tip := Vector3(mx + (i - 2.5) * 0.05, by + 1.6 + 0.03 * float(i % 2), zf - 0.24)
		m.polyline([Vector3(mx, by + 1.36, zf - 0.12), Vector3(mx + (i - 2.5) * 0.02, by + 1.5, zf - 0.13), tip],
			0.022, 0.022, c(STEEL[4]))
		m.cyl(tip, tip + Vector3(0, -0.02, -0.12), 0.04, 0.035, 6, c(NIGHT[3]))
	m.polyline([Vector3(HX + 0.24, by + 1.36, zf - 0.1), Vector3(HX + 0.28, by + 0.14, zf - 0.08),
		Vector3(HX + 0.6, by + 0.03, zf + 0.05), Vector3(HX + 1.6, by + 0.03, zf + 0.1)], 0.03, 0.03, c(NIGHT[2]))
	# --- back wall: pilasters with bases and capitals, moulding, dentils, cornice, vertical joints
	var bw := {"front": c(VIOLET[2]), "side": c(VIOLET[1]), "top": c(SNOW[3])}
	s.box(Vector3(HX - 26.0, 0.0, zf - 14.0), Vector3(52.0, 20.0, 2.0), bw)
	s.box(Vector3(HX - 27.0, 20.0, zf - 14.6), Vector3(54.0, 1.4, 2.8), lite)
	s.box(Vector3(HX - 26.4, 19.62, zf - 12.0), Vector3(52.8, 0.16, 0.12), lite)
	for i in 87:
		s.box(Vector3(HX - 25.95 + i * 0.6, 19.78, zf - 12.0), Vector3(0.3, 0.22, 0.2), lite)
	var bpil: Array = [HX - 19.5, HX - 6.5, HX + 6.5, HX + 19.5]
	for px: float in bpil:
		s.box(Vector3(px - 0.7, by, zf - 12.0), Vector3(1.4, 13.62, 0.45), face)
		s.box(Vector3(px - 0.85, by, zf - 12.0), Vector3(1.7, 0.5, 0.55), lite)
		s.box(Vector3(px - 0.85, 19.0, zf - 12.0), Vector3(1.7, 0.62, 0.55), lite)
	for k in range(7, 22):
		var y0 := 0.9 * k
		var h := minf(0.9, 19.62 - y0)
		var x := HX - 26.0 + 0.9 * float(k % 2) + 0.9
		while x < HX + 25.6:
			var near_pil := false
			for px: float in bpil:
				if absf(x - px) < 0.9:
					near_pil = true
			if not near_pil:
				s.box(Vector3(x - 0.045, y0, zf - 12.0), Vector3(0.09, h, 0.006), jd, Kit.FACE_PZ)
			x += 1.8
	# --- banners: rod with brackets and finials, the cloth hanging in folds, a weighted hem
	var b := K("banner_portico")
	for k in 3:
		var bx := HX - 13.0 + k * 13.0
		var zr := zf - 11.55
		m.cyl(Vector3(bx - 2.5, 19.72, zr), Vector3(bx + 2.5, 19.72, zr), 0.07, 0.07, 8, c(STEEL[2]), true,
			Vector3.UP, PI / 8.0)
		for sd: float in [-1.0, 1.0]:
			m.cyl(Vector3(bx + sd * 2.5, 19.72, zr), Vector3(bx + sd * 2.72, 19.72, zr), 0.11, 0.0, 6, c(STEEL[3]))
			m.beam(Vector3(bx + sd * 1.9, 19.72, zf - 12.0), Vector3(bx + sd * 1.9, 19.72, zr), 0.06, 0.08,
				c(STEEL[1]))
		var nf := 10
		for i in nf:
			var xa := bx - 2.2 + 4.4 * float(i) / nf
			var xb := bx - 2.2 + 4.4 * float(i + 1) / nf
			var za := zr - 0.14 + (0.36 if i % 2 == 1 else 0.0)
			var zb := zr - 0.14 + (0.36 if i % 2 == 0 else 0.0)
			var ta := zr - 0.06 + (0.08 if i % 2 == 1 else 0.0)
			var tb := zr - 0.06 + (0.08 if i % 2 == 0 else 0.0)
			b.quad_uv_out(Vector3(xa, 6.4, za), Vector3(xa, 19.62, ta), Vector3(xb, 19.62, tb), Vector3(xb, 6.4, zb),
				Vector3.BACK, Color.WHITE, Vector2(float(i) / nf, 1.0), Vector2(float(i + 1) / nf, 0.0), 0.45)
		m.cyl(Vector3(bx - 2.25, 6.42, zr), Vector3(bx + 2.25, 6.42, zr), 0.05, 0.05, 6, c(STEEL[1]))
	# --- pylons: plinth, fluted shaft, setback, cap slab, loudspeaker cluster on top
	for side: float in [-1.0, 1.0]:
		var px: float = HX + side * 31.5 - 2.5
		var pz := zf - 15.0
		s.box(Vector3(px - 0.15, 0.0, pz - 0.15), Vector3(5.3, 0.9, 4.3), base)
		s.box(Vector3(px, 0.0, pz), Vector3(5.0, 22.4, 4.0), {"front": c(VIOLET[3]), "side": c(VIOLET[1]),
			"top": c(SNOW[4])})
		s.box(Vector3(px + 0.3, 22.4, pz + 0.3), Vector3(4.4, 1.6, 3.4), face)
		s.box(Vector3(px - 0.12, 24.0, pz - 0.12), Vector3(5.24, 0.45, 4.24), lite)
		for gx: float in [1.25, 2.5, 3.75]:
			s.box(Vector3(px + gx - 0.07, 1.4, pz + 4.0), Vector3(0.14, 20.4, 0.008), jd, Kit.FACE_PZ)
		for gz: float in [1.0, 2.0, 3.0]:
			s.box(Vector3(px + 5.0, 1.4, pz + gz - 0.07), Vector3(0.008, 20.4, 0.14), jd, Kit.FACE_PX)
			s.box(Vector3(px - 0.008, 1.4, pz + gz - 0.07), Vector3(0.008, 20.4, 0.14), jd, Kit.FACE_NX)
		_horns(m, Vector3(px + 2.5, 24.45, pz + 2.0), 4)
	# --- floodlight frames on the deck corners, aimed at the lectern
	for xc: float in [x0 + 1.3, x1 - 1.3]:
		_floodframe(m, l, Vector3(xc, by, zf - 1.4), Vector3(HX, 7.4, zf - 0.6), 3, 2, 5.2)


## Konrad's own trail in the snow (shot p7): one line of footprints coming from behind the camera, bending a
## little, ending where he stands apart behind the crowd -- the street's footprint motif (hall_builder) again.
## Konrad's lone trail in the snow (shot p7): he came along the crowd's back edge from the left and stopped.  Pairs of
## prints 0.65 m apart, left / right of his line, each a shallow trough one tone darker than the snow (the same tones
## near and far: no dark dashes); the trail stays at his depth, so it lies above the subtitle plate.
func _build_konrad_trail() -> void:
	var g := K("ground")
	var r := RandomNumberGenerator.new()
	r.seed = 1792
	var a := Vector3(-118.5, 0.0, -795.6)
	var b := Vector3(-104.55, 0.0, Z_CROWD_BACK + 13.0 + 0.1)
	var steps := int(a.distance_to(b) / 0.65)
	var dir := (b - a).normalized()
	var side := Vector3(-dir.z, 0.0, dir.x)
	for k in steps + 1:
		var u := float(k) / float(steps)
		var q := a.lerp(b, u) + side * ((0.11 if k % 2 == 0 else -0.11) + 0.35 * sin(u * PI)) \
			+ dir * r.randf_range(-0.04, 0.04)
		var hl := r.randf_range(0.13, 0.16)             # half length along the walk
		var hw := 0.11                                  # half width (the print and the snow it pushed aside)
		var f := q + dir * hl
		var bk := q - dir * hl
		g.quad(bk - side * hw + Vector3(0, 0.013, 0), f - side * hw + Vector3(0, 0.013, 0),
			f + side * hw + Vector3(0, 0.013, 0), bk + side * hw + Vector3(0, 0.013, 0), c(SNOW[0]))
	stats["konrad_trail"] = steps + 1


func _baluster(s: Kit, p: Vector3, col) -> void:
	s.box(Vector3(p.x - 0.12, p.y, p.z - 0.12), Vector3(0.24, 0.1, 0.24), col)
	s.box(Vector3(p.x - 0.085, p.y + 0.1, p.z - 0.085), Vector3(0.17, 0.42, 0.17), col)
	s.box(Vector3(p.x - 0.12, p.y + 0.52, p.z - 0.12), Vector3(0.24, 0.1, 0.24), col)


## Floodlight frame: tapered lattice mast (4 posts, zig-zag bracing), yoke, a cols x rows rack of lamp drums with
## glowing lenses (lamp kit), aimed at `aim`.
func _floodframe(m: Kit, l: Kit, base: Vector3, aim: Vector3, cols: int, rows: int, h: float) -> void:
	var post := c(STEEL[1])
	var hw := 0.25
	for cx: float in [-hw, hw]:
		for cz: float in [-hw, hw]:
			m.beam(base + Vector3(cx, 0, cz), base + Vector3(cx * 0.6, h, cz * 0.6), 0.06, 0.06, post)
	var nb := maxi(2, int(h / 0.7))
	for i in nb:
		var ya := h * float(i) / nb
		var yb := h * float(i + 1) / nb
		var sa := lerpf(1.0, 0.6, ya / h) * hw
		var sb := lerpf(1.0, 0.6, yb / h) * hw
		var fl := 1.0 if i % 2 == 0 else -1.0
		for sd: float in [-1.0, 1.0]:
			m.beam(base + Vector3(-sa * fl, ya, sd * sa), base + Vector3(sb * fl, yb, sd * sb), 0.035, 0.035, post)
			m.beam(base + Vector3(sd * sa, ya, -sa * fl), base + Vector3(sd * sb, yb, sb * fl), 0.035, 0.035, post)
	var top := base + Vector3(0, h, 0)
	var d := (aim - top).normalized()
	var r := d.cross(Vector3.UP).normalized()
	var u := r.cross(d).normalized()
	var fw := cols * 0.62
	var fh := rows * 0.62
	var hc := top + Vector3(0, 0.2 + fh * 0.5, 0)
	m.polyline([hc - r * fw * 0.5 - u * fh * 0.5, hc - r * fw * 0.5 + u * fh * 0.5, hc + r * fw * 0.5 + u * fh * 0.5,
		hc + r * fw * 0.5 - u * fh * 0.5], 0.06, 0.06, post, Vector3.UP, true)
	m.beam(top, hc - u * fh * 0.5, 0.09, 0.09, post)
	m.box(top - Vector3(0.2, 0.5, 0.2), Vector3(0.4, 0.3, 0.4), {"front": c(STEEL[2]), "side": c(STEEL[1]),
		"top": c(SNOW[3])})
	for i in cols:
		for j in rows:
			var p := hc + r * ((i - (cols - 1) * 0.5) * 0.62) + u * ((j - (rows - 1) * 0.5) * 0.62)
			m.cyl(p - d * 0.3, p + d * 0.1, 0.19, 0.25, 10, c(STEEL[2]))
			m.cyl(p + d * 0.1, p + d * 0.17, 0.27, 0.27, 10, c(STEEL[1]), false)
			l.disc_uv(p + d * 0.11, d, u, 0.23, 10, c(SNOW[4]), Rect2(0, 0, 1, 1), 0.9)


## Loudspeaker cluster on a mast head (`top`): n flared horns per row (two rows from n >= 4) aimed at the crowd
## (+z), tilted down and fanned; driver units behind the throats, cross-bars, junction box.
func _horns(m: Kit, top: Vector3, n: int) -> void:
	var rows := 2 if n >= 4 else 1
	var w := n * 0.72
	m.cyl(top - Vector3(0, 0.25, 0), top + Vector3(0, 1.0 + rows * 0.78, 0), 0.09, 0.075, 8, c(NIGHT[3]))
	m.box(Vector3(top.x - 0.16, top.y + 0.15, top.z + 0.06), Vector3(0.32, 0.42, 0.2), {"front": c(STEEL[2]),
		"side": c(STEEL[1]), "top": c(SNOW[3])})
	for r in rows:
		var y := top.y + 0.95 + r * 0.78
		m.beam(Vector3(top.x - w * 0.5, y, top.z), Vector3(top.x + w * 0.5, y, top.z), 0.07, 0.07, c(STEEL[1]))
		for k in n:
			var yaw := (float(k) - (n - 1) * 0.5) * 0.16
			var d := Vector3(sin(yaw), -0.2 - 0.06 * r, cos(yaw)).normalized()
			var p0 := Vector3(top.x - w * 0.5 + 0.36 + k * 0.72, y + 0.05, top.z + 0.08)
			var rt := Vector3.UP.cross(d).normalized()
			var up := d.cross(rt).normalized()
			var rings: Array = []
			for spec in [[0.0, 0.07, 0.06], [0.32, 0.13, 0.1], [0.62, 0.28, 0.2]]:
				var cc: Vector3 = p0 + d * float(spec[0])
				var hx: float = spec[1]
				var hy: float = spec[2]
				rings.append([cc - rt * hx - up * hy, cc + rt * hx - up * hy, cc + rt * hx + up * hy,
					cc - rt * hx + up * hy])
			m.loft(rings, [c(STEEL[1]), c(STEEL[2])])
			var mc := p0 + d * 0.58
			m.quad_out(mc - rt * 0.26 - up * 0.185, mc - rt * 0.26 + up * 0.185, mc + rt * 0.26 + up * 0.185,
				mc + rt * 0.26 - up * 0.185, c(NIGHT[0]), d)
			m.cyl(p0 - d * 0.2, p0 + d * 0.02, 0.1, 0.09, 8, c(NIGHT[3]))


## Crowd barrier of interlocking steel sections (2.5 m: tube frame, flat pickets, splayed feet, couplings) and the
## loudspeaker masts along the lane (footing, bolted flange, tapered pole, clamps, junction box, conduit, cable,
## climbing pegs, horn cluster).  The pickets stay below the top tube, so the knee-height shots look over them.
func _build_barrier() -> void:
	var m := K("metal")
	var s := K("stone")
	var zb := Z_BARRIER
	var bar := {"front": c(STEEL[2]), "side": c(STEEL[1]), "top": c(SNOW[3])}
	var sec := 2.5
	var x := X_MIN
	while x < X_MAX - 0.01:
		var xa := x + 0.05
		var xb := x + sec - 0.05
		for ux: float in [xa, xb]:
			m.cyl(Vector3(ux, 0.1, zb), Vector3(ux, 1.05, zb), 0.024, 0.024, 6, c(STEEL[2]))
		m.cyl(Vector3(xa, 1.0, zb), Vector3(xb, 1.0, zb), 0.028, 0.028, 6, c(STEEL[3]), false)
		m.cyl(Vector3(xa, 0.2, zb), Vector3(xb, 0.2, zb), 0.022, 0.022, 6, c(STEEL[2]), false)
		var n := int((xb - xa) / 0.25)
		for i in range(1, n):
			var px := xa + i * (xb - xa) / n
			m.box(Vector3(px - 0.02, 0.2, zb - 0.006), Vector3(0.04, 0.8, 0.012), bar)
		x += sec
	x = X_MIN
	while x <= X_MAX + 0.01:
		m.box(Vector3(x - 0.035, 0.0, zb - 0.4), Vector3(0.07, 0.045, 0.8), bar)
		for sd: float in [-1.0, 1.0]:
			m.beam(Vector3(x, 0.04, zb + sd * 0.34), Vector3(x, 0.42, zb + sd * 0.02), 0.03, 0.03, c(STEEL[1]),
				Vector3.RIGHT)
		m.box(Vector3(x - 0.07, 0.9, zb - 0.025), Vector3(0.14, 0.06, 0.05), c(STEEL[1]))
		x += sec
	# loudspeaker masts along the lane
	for px: float in [-95.0, -35.0, 25.0, 85.0, 145.0, 205.0]:
		var zp := zb - 3.0
		s.box(Vector3(px - 0.42, 0.0, zp - 0.42), Vector3(0.84, 0.14, 0.84), {"front": c(VIOLET[2]),
			"side": c(VIOLET[1]), "top": c(SNOW[3])})
		m.cyl(Vector3(px, 0.14, zp), Vector3(px, 0.22, zp), 0.3, 0.3, 8, c(STEEL[1]))
		for k in 4:
			var a := PI * 0.25 + k * PI * 0.5
			m.box(Vector3(px + cos(a) * 0.22 - 0.03, 0.22, zp + sin(a) * 0.22 - 0.03), Vector3(0.06, 0.05, 0.06),
				c(STEEL[3]))
		m.cyl(Vector3(px, 0.22, zp), Vector3(px, 7.2, zp), 0.15, 0.09, 8, c(NIGHT[3]), false, Vector3.RIGHT, PI / 8.0)
		for cy: float in [3.3, 5.0, 6.6]:
			var rr := lerpf(0.15, 0.09, (cy - 0.22) / 6.98) + 0.018
			m.cyl(Vector3(px, cy, zp), Vector3(px, cy + 0.07, zp), rr, rr, 8, c(STEEL[1]), false, Vector3.RIGHT,
				PI / 8.0)
		m.box(Vector3(px - 0.15, 1.9, zp + 0.13), Vector3(0.3, 0.44, 0.17), bar)
		m.box(Vector3(px - 0.11, 1.95, zp + 0.3), Vector3(0.22, 0.34, 0.012), c(STEEL[3]))
		m.beam(Vector3(px + 0.06, 2.34, zp + 0.2), Vector3(px + 0.06, 7.1, zp + 0.12), 0.045, 0.045, c(STEEL[1]),
			Vector3.BACK)
		m.polyline([Vector3(px - 0.06, 1.9, zp + 0.22), Vector3(px - 0.06, 0.25, zp + 0.3),
			Vector3(px - 0.1, 0.03, zp + 0.7), Vector3(px - 0.4, 0.03, zp + 2.6)], 0.04, 0.04, c(NIGHT[2]),
			Vector3(0.7, 0.7, 0.0))                       # cable faces tilted: no snow cap on a lying cable
		for i in 10:
			var py := 2.6 + i * 0.42
			var sd := 1.0 if i % 2 == 0 else -1.0
			m.beam(Vector3(px, py, zp), Vector3(px + sd * 0.3, py, zp), 0.035, 0.035, c(STEEL[2]))
		_horns(m, Vector3(px, 7.2, zp), 2)


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
	var ys := [2.4, 30.0, 140.0, 380.0, 800.0, 1500.0]       # the pillar starts at the lens of the unit
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
		_searchlight(m, l, bpos, lean)
		halos.append({"pos": bpos + Vector3(0, 2.0, 0), "col": c(SNOW[4]), "r": 7.0, "k": 0.35})
	stats["beams"] = bases.size()


## Searchlight unit under every light pillar: trailer with wheels and jacks, turntable, yoke with trunnions,
## finned drum along the pillar's lean, lamp housing, hood and the glowing lens (lamp kit).
func _searchlight(m: Kit, l: Kit, b: Vector3, lean: Vector3) -> void:
	var dk := {"front": c(STEEL[1]), "side": c(STEEL[0]), "top": c(SNOW[3])}
	m.box(Vector3(b.x - 1.3, 0.3, b.z - 0.85), Vector3(2.6, 0.32, 1.7), dk)
	for wx: float in [-0.85, 0.85]:
		for wz: float in [-0.98, 0.98]:
			m.cyl(Vector3(b.x + wx, 0.3, b.z + wz - 0.1), Vector3(b.x + wx, 0.3, b.z + wz + 0.1), 0.3, 0.3, 8,
				c(NIGHT[2]))
	for jx: float in [-1.2, 1.2]:
		m.beam(Vector3(b.x + jx, 0.3, b.z), Vector3(b.x + jx * 1.15, 0.0, b.z), 0.08, 0.08, c(STEEL[1]))
	m.cyl(b + Vector3(0, 0.62, 0), b + Vector3(0, 0.78, 0), 0.78, 0.72, 12, c(STEEL[2]))
	var cen := b + Vector3(0, 1.65, 0)
	for sd: float in [-1.0, 1.0]:
		m.beam(b + Vector3(sd * 0.98, 0.78, 0), cen + Vector3(sd * 0.98, 0, 0), 0.14, 0.18, c(STEEL[1]), Vector3.BACK)
		m.cyl(cen + Vector3(sd * 0.8, 0, 0), cen + Vector3(sd * 1.05, 0, 0), 0.12, 0.12, 6, c(STEEL[2]))
	var c0 := cen - lean * 0.55
	var c1 := cen + lean * 0.7
	m.cyl(c0, c1, 0.74, 0.8, 14, c(STEEL[2]))
	for f in 3:
		var fp := c0 + lean * (0.15 + f * 0.18)
		m.cyl(fp, fp + lean * 0.05, 0.86, 0.86, 14, c(STEEL[1]), false)
	m.cyl(c0 - lean * 0.25, c0, 0.25, 0.4, 8, c(STEEL[1]))
	m.cyl(c1, c1 + lean * 0.14, 0.86, 0.86, 14, c(STEEL[3]), false)
	l.disc_uv(c1 + lean * 0.02, lean, Vector3.BACK, 0.74, 14, c(SNOW[4]), Rect2(0, 0, 1, 1), 1.0)


## The armoured column (tanks + half-tracks, two staggered files) lives in parade_vehicles.gd.
func _build_vehicles() -> void:
	veh = Vehicles.new()
	veh.name = "Vehicles"
	add_child(veh)
	veh.build({"z_lane": Z_LANE, "x0": VEH_X0, "speed": VEH_SPEED, "pitch": VEH_PITCH})
	stats.merge(veh.stats)


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
