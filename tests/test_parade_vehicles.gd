extends RefCounted
## The armoured column of L_M1_Parade (scripts/levels/parade/parade_vehicles.gd, owner parade):
##  * column layout: 2 files x 7, tanks on the near (crowd / camera) side, half-tracks on the far side, the far file
##    trailing by half a pitch; near-file vehicle j keeps parade_set's timing x0 - j * pitch + v * t (the shot-3
##    camera relies on it); no two vehicles of a file touch (pitch > hull length incl. the gun)
##  * budget: ~20 draw calls for the whole column, triangle counts per design inside their budgets
##  * vehicle_pos(t) / puff_at(t) are pure functions of t (seek / skip stay deterministic); the track links scroll
##    by less than one link pitch; the whips stay near upright
##  * dust + vapour stay low veils (vehicle_dust.gdshader): no puff taller than 1.5 m or above the turret roof,
##    density <= 1, unborn puffs (before t = 0) invisible
##  * detail maps exist (tools/pixelgen/gen_parade_vehicles.py) and two builds are identical

const Kit := preload("res://tests/support/test_kit.gd")
const VEH := "res://scripts/levels/parade/parade_vehicles.gd"
const DIR := "res://assets/architecture/parade/vehicles/"
const CFG := {"z_lane": -876.0, "x0": -77.0, "speed": 2.8, "pitch": 16.0}
const LINK_PITCH := 0.1875       ## parade_vehicles.gd PITCH (6 texels of track.png)

var kit: Kit
var root: Node3D
var veh: Node3D


func run() -> Array:
	kit = Kit.new()
	root = Node3D.new()
	root.name = "ParadeVehiclesTest"
	kit.mount(root)
	veh = _make()
	kit.run_case("column_layout", _layout)
	kit.run_case("draw_calls_and_budget", _budget)
	kit.run_case("update_is_pure", _update)
	kit.run_case("dust_stays_low", _dust)
	kit.run_case("detail_maps_and_rebuild", _maps)
	kit.cleanup()
	return kit.failures


func _make() -> Node3D:
	var v: Node3D = (load(VEH) as GDScript).new()
	v.name = "Vehicles"
	root.add_child(v)
	v.build(CFG)
	v.build_dust()
	return v


func _layout() -> bool:
	var vehs: Array = veh.vehs
	kit.eq(vehs.size(), 14, "14 vehicles")
	var near: Array = []
	var far: Array = []
	for v in vehs:
		(near if float(v["z"]) > CFG["z_lane"] else far).append(v)
	kit.eq(near.size(), 7, "7 vehicles in the near file")
	kit.eq(far.size(), 7, "7 vehicles in the far file")
	for j in near.size():
		kit.eq(int(near[j]["type"]), 0, "near file %d is a tank" % j)
		kit.ok(is_equal_approx(float(near[j]["x0"]), CFG["x0"] - j * CFG["pitch"]),
			"near file %d keeps parade_set timing" % j)
		kit.ok(is_equal_approx(veh.vehicle_pos(vehs.find(near[j]), 14.0).x,
			CFG["x0"] - j * CFG["pitch"] + CFG["speed"] * 14.0), "vehicle_pos follows x0 + v t")
	for j in far.size():
		kit.eq(int(far[j]["type"]), 1, "far file %d is a half-track" % j)
		kit.ok(is_equal_approx(float(far[j]["x0"]), CFG["x0"] - (j + 0.5) * CFG["pitch"]),
			"far file %d trails by half a pitch" % j)
	# hull extents per type from the body meshes: a file never touches itself
	for tp in veh.types:
		var mm: MultiMesh = tp["parts"][0]["mm"]
		var aabb := mm.mesh.get_aabb()
		kit.ok(aabb.size.x < CFG["pitch"] - 2.0, "vehicle %.1f m long leaves a gap at pitch %.0f m" % [aabb.size.x,
			CFG["pitch"]])
		kit.ok(aabb.size.y > 1.5 and aabb.size.y < 3.6, "vehicle height %.2f m is plausible" % aabb.size.y)
	kit.ok(absf(float(near[0]["z"]) - float(far[0]["z"])) >= 6.0, "the files are >= 6 m apart")
	return true


func _budget() -> bool:
	var calls := 0
	for c in veh.get_children():
		if c is MultiMeshInstance3D:
			calls += 1
	kit.ok(calls <= 26, "%d draw calls for the column (<= 26)" % calls)
	kit.ok(int(veh.stats.get("tank_tris", 0)) > 3000 and int(veh.stats.get("tank_tris", 0)) < 9000,
		"tank triangles in budget (%d)" % int(veh.stats.get("tank_tris", 0)))
	kit.ok(int(veh.stats.get("halftrack_tris", 0)) > 3000 and int(veh.stats.get("halftrack_tris", 0)) < 9000,
		"half-track triangles in budget (%d)" % int(veh.stats.get("halftrack_tris", 0)))
	return true


## Every puff of the column at time t via the pure puff_at() (MultiMesh buffers are not kept by the headless
## rendering server, so the test reads the function the per-frame loop writes from).
func _puffs(v: Node3D, t: float) -> Array:
	var out: Array = []
	for vi in (v.vehs as Array).size():
		var em: Array = v.types[int(v.vehs[vi]["type"])]["emit"]
		for ei in em.size():
			for q in int(em[ei][2]):
				v.puff_at(vi, ei, q, t)
				out.append([v.puff_pos, v.puff_cd])
	return out


func _update() -> bool:
	var d: Vector3 = veh.vehicle_pos(0, 15.3) - veh.vehicle_pos(0, 3.0)
	kit.ok(is_equal_approx(d.x, CFG["speed"] * 12.3) and is_zero_approx(d.z), "the column drives along +x at v")
	var a := _puffs(veh, 15.3)
	var mid := _puffs(veh, 3.0)
	var b := _puffs(veh, 15.3)
	kit.ok(a == b, "puffs at t depend on t only")
	kit.ok(a != mid, "the dust moves between t = 3 and t = 15.3")
	kit.eq(a.size(), veh.dust_mm.instance_count, "one MultiMesh instance per puff")
	# the per-frame writers run (no errors); where the renderer keeps the buffers, check tracks and whips
	veh.update(15.3)
	veh.update_dust(15.3)
	for tp in veh.types:
		for part in tp["parts"]:
			var kind: int = part["kind"]
			var mm: MultiMesh = part["mm"]
			if mm.buffer.is_empty():
				continue
			if kind == 2:
				var body: Transform3D = (tp["parts"][0]["mm"] as MultiMesh).get_instance_transform(0)
				var t2: Transform3D = mm.get_instance_transform(0)
				var o := Vector2(t2.origin.x - body.origin.x, t2.origin.y)
				kit.ok(o.length() <= LINK_PITCH + 0.001, "track run offset %.3f m < link pitch" % o.length())
			elif kind == 4:
				for i in mm.instance_count:
					var up := mm.get_instance_transform(i).basis.y.normalized()
					kit.ok(up.y > cos(deg_to_rad(25.0)), "whip %d near upright" % i)
	return true


func _dust() -> bool:
	var mm: MultiMesh = veh.dust_mm
	kit.ok(mm != null and mm.instance_count >= 100, "dust MultiMesh with puffs for every vehicle")
	if mm == null:
		return false
	kit.ok(mm.use_custom_data, "dust uses per-instance custom data")
	for t: float in [0.2, 9.0, 14.6, 18.0, 40.0]:
		var bad := 0
		var lit := 0
		var all := _puffs(veh, t)
		for pc in all:
			var p: Vector3 = pc[0]
			var cd: Color = pc[1]
			if cd.b > 0.0:
				lit += 1
			if p.y < -0.01 or p.y + cd.g > 2.4 or cd.g > 1.5 or cd.r > 3.0 or cd.b > 1.0 or cd.b < 0.0:
				bad += 1
			if absf(p.z - CFG["z_lane"]) > 6.0:
				bad += 1
		kit.eq(bad, 0, "t=%.1f: every puff is a low veil in the lane (base >= 0, top <= turret roof 2.4 m, density 0..1)" % t)
		if t > 5.0:
			kit.ok(lit > all.size() / 2, "t=%.1f: the column raises dust (%d live puffs)" % [t, lit])
	# a puff whose birth lies before t = 0 is invisible
	var early := 0
	for pc in _puffs(veh, 0.05):
		if (pc[1] as Color).b > 0.0:
			early += 1
	kit.ok(early < mm.instance_count / 4, "at t=0.05 only just-born puffs show (%d)" % early)
	var mi := veh.get_node_or_null("Dust") as MultiMeshInstance3D
	kit.ok(mi != null and mi.material_override is ShaderMaterial, "dust has its own shader material")
	if mi:
		kit.eq(mi.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "dust casts no shadow")
	return true


func _maps() -> bool:
	for f in ["decals.png", "track.png", "wheels.png", "vehicle_dust.gdshader"]:
		kit.ok(ResourceLoader.exists(DIR + f), "%s exists" % f)
	var b: Node3D = _make()
	kit.ok(veh.vehs == b.vehs, "two builds lay out the same column")
	kit.ok(_puffs(veh, 12.5) == _puffs(b, 12.5), "two builds raise the same dust")
	kit.eq(veh.stats.get("tank_tris"), b.stats.get("tank_tris"), "same tank triangle count on rebuild")
	kit.eq(veh.stats.get("halftrack_tris"), b.stats.get("halftrack_tris"), "same half-track triangle count")
	return true
