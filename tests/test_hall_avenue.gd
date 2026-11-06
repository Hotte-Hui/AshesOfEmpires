extends RefCounted
## The avenue staging layer of the Great Hall set (scripts/levels/hall/hall_avenue.gd, owner hall), seen by the
## parade's closing shot p8 (L_M1_Parade):
##  * figure atlas contract (tools/pixelgen/gen_great_hall_avenue.py): the json matches the png, LOD strips
##    ascend, every slot the layer uses exists with its frame count, every cell holds a figure at every size,
##    binary alpha, berlin palette only
##  * the layer builds on the hall set: nothing nearer than the cleared street (Z_NEAR), honour files and cordon
##    guards keep their spacing (they read as single men from the roofs, not as a bar), no banner mast on the
##    left (it would stand behind the street's near lamp in p8), the stats name what was staged
##  * the parade route: the marching column moves in separate blocks (each led by its colour party) inside the
##    honour files and never reaches the plaza crowd during p8; the vehicle column (rows abreast, left lane) keeps
##    its intervals and stops short of the halted blocks; the halted blocks stay in their lanes; one flame per fire
##    pylon on both bollard lines and one per fire bowl on the right grandstands' parapet; the delegations stand
##    beyond the right crowd; the crowd helpers (crowd_depth, gate_corridor, crowd_clear) give the parade set's
##    avenue crowd a sane, deterministic zone
##  * the organised crowds: marshals' lanes run inside the crowd's depth (lit, with lamps and marshals), cross-gaps
##    sit where the crowd is, strip_at / crowd_groups / in_stand are consistent, the delegations' banners stand on
##    their blocks, the column's standards use the Symbols-resolved standard texture, the column's vehicles carry
##    snow caps and headlight pools (lamp kit) so they read from the roofs
##  * update(t) is a pure function of t (seek / skip stay deterministic), the crows only fly from p8 on, the
##    plough's beacon turns within its range, and two builds are identical

const Kit := preload("res://tests/support/test_kit.gd")
const AVENUE := "res://scripts/levels/hall/hall_avenue.gd"
const BUILDER := "res://scripts/levels/hall/hall_builder.gd"
const DIR := "res://assets/architecture/great_hall/avenue/"
const FRAMES := {"march_back": 4, "stand_back": 3, "guard_side": 2, "honour": 2, "officer": 2, "shovel": 4,
	"carry": 2, "civ_walk": 4, "civ_walk2": 4, "police": 2, "crow": 3, "puff": 4, "flame": 4}
const P8_END := 47.0             ## last frame of shot p8 (parade_shots.gd)
const BERLIN := ["#120C14", "#1B1520", "#211623", "#2A2130", "#25202B", "#342F37", "#443B43", "#57494D",
	"#4A3A35", "#5F4A40", "#7A5E4E", "#94735C", "#AE8A6C", "#C9A585", "#5F4530", "#735145", "#8D5542", "#AF6C47",
	"#D07744", "#E5945A", "#F0AE6E", "#F4BA81", "#F8D2A0", "#FCE9C8", "#1E2329", "#2F363F", "#454E58", "#5F6973",
	"#7C8690", "#A3ACB4", "#1E2E2C", "#2C4440", "#3E5D55", "#56776A", "#73927F", "#6E6A73", "#8F8A92", "#B2ACB0",
	"#D2CCCB", "#ECE6E0"]

var kit: Kit
var meta: Dictionary = {}
var root: Node3D
var builder
var avenue: Node3D


func run() -> Array:
	kit = Kit.new()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(DIR + "avenue_figures.json"))
	if not kit.ok(parsed is Dictionary, "avenue_figures.json parses"):
		return kit.failures
	meta = parsed
	kit.run_case("atlas_contract", _atlas)
	kit.run_case("atlas_pixels", _pixels)
	if _build():
		kit.run_case("layout_near_limit_and_spacing", _layout)
		kit.run_case("parade_route", _route)
		kit.run_case("crowd_zone_helpers", _crowd_zone)
		kit.run_case("organised_crowd", _organised)
		kit.run_case("update_is_pure_and_crows_from_p8", _update)
		kit.run_case("rebuild_identical", _rebuild)
	kit.cleanup()
	return kit.failures


func _atlas() -> bool:
	var img := Image.load_from_file(ProjectSettings.globalize_path(DIR + "avenue_figures.png"))
	kit.ok(img != null, "atlas png loads")
	var asz: Array = meta.get("atlas", [])
	kit.eq([img.get_width(), img.get_height()], [int(asz[0]), int(asz[1])], "json atlas size = png size")
	var lods: Array = meta.get("lods", [])
	kit.ok(lods.size() >= 8 and lods.size() <= 16, "8..16 LOD strips (shader holds 16)")
	var prev := 0
	for l in lods:
		kit.ok(int(l[3]) > prev, "LOD figure heights ascend (%d)" % int(l[3]))
		kit.ok(int(l[0]) + int(l[2]) <= img.get_height(), "strip at y=%d inside the atlas" % int(l[0]))
		prev = int(l[3])
	var slots: Dictionary = meta.get("slots", {})
	for k in FRAMES:
		kit.ok(slots.has(k), "slot %s exists" % k)
		if slots.has(k):
			kit.eq(int(slots[k][1]), int(FRAMES[k]), "slot %s frame count" % k)
	kit.ok(slots.has("civ_back") and int(slots["civ_back"][1]) >= 8, "at least 8 civilians seen from behind")
	var n := 0
	for k in slots:
		n += int(slots[k][1])
	for l in lods:
		kit.ok(n * int(l[1]) <= img.get_width(), "every slot fits strip h=%d" % int(l[3]))
	return true


func _pixels() -> bool:
	var img := Image.load_from_file(ProjectSettings.globalize_path(DIR + "avenue_figures.png"))
	var pal := {}
	for h in BERLIN:
		pal[Color(h).to_html(false)] = true
	var bad := 0
	var semi := 0
	for y in img.get_height():
		for x in img.get_width():
			var p := img.get_pixel(x, y)
			if p.a8 == 0:
				continue
			if p.a8 != 255:
				semi += 1
			elif not pal.has(p.to_html(false)):
				bad += 1
	kit.eq(bad, 0, "atlas pixels are berlin palette colours")
	kit.eq(semi, 0, "atlas alpha is binary")
	var slots: Dictionary = meta.get("slots", {})
	var total := 0
	for k in slots:
		total = maxi(total, int(slots[k][0]) + int(slots[k][1]))
	var empty: Array = []
	for l in meta.get("lods", []):
		for s in total:
			var filled := false
			for y in range(int(l[0]), int(l[0]) + int(l[2])):
				for x in range(s * int(l[1]), (s + 1) * int(l[1])):
					if img.get_pixel(x, y).a8 > 0:
						filled = true
						break
				if filled:
					break
			if not filled:
				empty.append("slot %d h=%d" % [s, int(l[3])])
	kit.eq(empty, [], "every cell holds a figure at every size")
	return true


func _build() -> bool:
	root = Node3D.new()
	root.name = "AvenueTest"
	kit.mount(root)
	builder = (load(BUILDER) as GDScript).new()
	builder.build(root, {})
	avenue = (load(AVENUE) as GDScript).new()
	avenue.name = "Avenue"
	root.add_child(avenue)
	avenue.call("build", builder, "parade")
	return kit.ok(avenue.get("stats") is Dictionary and int(avenue.stats.get("primitives", 0)) > 0,
		"avenue builds on the hall set")


## Feet positions, slots and flips of a figure MultiMesh, from the points it was built from (the headless
## renderer keeps no MultiMesh buffers).
func _figs(node_name: String) -> Array:
	var out: Array = []
	for p in avenue.placed.get(node_name, []):
		out.append([p[0], int(p[1]), bool(p[4])])
	return out


func _layout() -> bool:
	var A = load(AVENUE)
	var st: Dictionary = avenue.stats
	for k in ["cordon_lamps", "lorries_parked", "buses", "tanks", "far_scaffolds", "AvenueFigures", "Vapour", "Flock",
			"lights", "banner_masts", "fire_pylons", "Flames", "halted_blocks", "ColumnMarch", "column_banners",
			"column_lorries", "ColumnVapour", "delegations"]:
		kit.ok(st.has(k), "stats name %s" % k)
	kit.eq(int(st.get("banner_masts", 0)), 2, "two banner masts, right side only")
	kit.ok(int(st.get("tanks", 0)) >= 6 and int(st.get("lorries_parked", 0)) >= 30 and int(st.get("buses", 0)) >= 20,
		"tanks, motor pool and buses staged")
	# static geometry: nothing nearer than the cleared street, no mast on the left
	var geo := avenue.get_node_or_null("AvenueGeometry")
	kit.ok(geo != null, "AvenueGeometry node")
	if geo:
		for mi in geo.get_children():
			var ab: AABB = (mi as MeshInstance3D).mesh.get_aabb()
			kit.ok(ab.end.z <= A.Z_NEAR + 0.5, "%s stays beyond Z_NEAR (max z %.1f)" % [mi.name, ab.end.z])
	var flags := geo.get_node_or_null("M_flag_pole") as MeshInstance3D if geo else null
	if kit.ok(flags != null, "banner cloth mesh"):
		kit.ok(flags.mesh.get_aabb().position.x > A.HX, "banner cloth only right of the axis")
	# figures: inside the avenue's z range, honour files and cordon guards spaced
	var figs := _figs("AvenueFigures")
	var slots: Dictionary = avenue.slots
	var honour0 := int(slots["honour"][0])
	var guard0 := int(slots["guard_side"][0])
	var hz := {-1: [], 1: []}
	var gz := {-1: [], 1: []}
	var near := 0
	for f in figs:
		var p: Vector3 = f[0]
		if p.z > A.Z_NEAR + 0.01 or p.z < A.Z_FAR - 10.0:
			near += 1
		var s: int = f[1]
		if s >= honour0 and s < honour0 + 2:
			(hz[-1 if p.x < A.HX else 1] as Array).append(p.z)
		if s >= guard0 and s < guard0 + 2 and (absf(p.x - A.X_GUARD_L) < 0.2 or absf(p.x - A.X_GUARD_R) < 0.2):
			(gz[-1 if p.x < A.HX else 1] as Array).append(p.z)
	kit.eq(near, 0, "every figure stands between Z_FAR and Z_NEAR")
	for sd in [-1, 1]:
		kit.ok(_min_gap(hz[sd]) >= A.HONOUR_STEP - 0.01, "honour file %d: one man every %.0f m" % [sd, A.HONOUR_STEP])
		kit.ok((hz[sd] as Array).size() >= 30, "honour file %d lines the lane" % sd)
		kit.ok(_min_gap(gz[sd]) >= A.GUARD_STEP - 0.01, "cordon %d: one guard every %.0f m" % [sd, A.GUARD_STEP])
	# the snow gang faces its windrow / the tipper
	var sh0 := int(slots["shovel"][0])
	var gang := 0
	for f in figs:
		var p: Vector3 = f[0]
		if int(f[1]) == sh0:
			gang += 1
			kit.eq(bool(f[2]), p.x < 12.0 or p.x > 28.4, "shoveller at x=%.1f faces his heap" % p.x)
	kit.ok(gang >= 8, "snow gang at work")
	return true


## The parade route of p8 (all positions at T_MID; the column and the vehicles then move -z at COL_SPEED).
func _route() -> bool:
	var A = load(AVENUE)
	var st: Dictionary = avenue.stats
	var drift: float = A.COL_SPEED * (P8_END - A.T_MID)
	# the marching column: whole blocks plus colour party and officer, in its lane inside the honour files
	var col: Array = avenue.placed.get("ColumnMarch", [])
	kit.eq(col.size(), A.COL_BLOCKS * (A.COL_FILES * A.COL_RANKS + 6), "column = blocks x (files x ranks + colours)")
	var zs: Array = []
	var out_of_lane := 0
	for p in col:
		var v: Vector3 = p[0]
		zs.append(v.z)
		if absf(v.x - A.HX) > A.HONOUR_X - 1.0:
			out_of_lane += 1
	kit.eq(out_of_lane, 0, "the column marches inside the honour files")
	zs.sort()
	var gaps := 0
	for i in zs.size() - 1:
		if float(zs[i + 1]) - float(zs[i]) >= 15.0:
			gaps += 1
	kit.eq(gaps, A.COL_BLOCKS - 1, "every block stands apart (>= 15 m gaps between the blocks)")
	kit.ok(float(zs[0]) - drift > A.Z_FAR - 5.0, "the column's head stays short of the plaza crowd until the end of p8")
	kit.ok(float(zs[zs.size() - 1]) < A.Z_NEAR - 60.0, "the column's tail leaves the cleared street empty")
	kit.eq(int(st.get("column_banners", 0)), A.COL_BLOCKS * 3, "three standards before every block")
	# the vehicle column: rows abreast in the left lane, intervals kept, stopping short of the halted blocks
	var slots: Array = A.vehicle_slots()
	var nt := 0
	var bad := 0
	var lead := 1e9
	for i in slots.size():
		var a: Vector3 = slots[i][1]
		nt += 1 if int(slots[i][0]) == 0 else 0
		lead = minf(lead, a.z - 3.8)
		if a.x < 4.0 or a.x > A.HX - A.HONOUR_X - 4.0:
			bad += 1
		for j in range(i + 1, slots.size()):
			var b: Vector3 = slots[j][1]
			if absf(a.x - b.x) < 4.0 and absf(a.z - b.z) < 9.0:
				bad += 1
	kit.eq(bad, 0, "vehicles keep their lane and their intervals (no two hulls touch)")
	kit.ok(nt >= 12 and slots.size() - nt >= 12, "tanks and lorries in the column (%d / %d)" % [nt, slots.size() - nt])
	kit.eq(int(st.get("tanks", 0)), nt, "stats count the tanks")
	var halted_left := 1e9
	for c in A.HALT_COLS:
		if float(c[0]) < A.HX:
			halted_left = minf(halted_left, -float(c[1]) - (A.HALT_RANKS - 1) * 1.5)
	kit.ok(-lead + drift < halted_left - 3.0, "the vehicle column stops short of the halted blocks (%.1f / %.1f)"
		% [-lead + drift, halted_left])
	# halted blocks: stand_back men in the side lanes, never in the column's lane
	var figs := _figs("AvenueFigures")
	var sb0 := int(avenue.slots["stand_back"][0])
	var halted := 0
	var in_lane := 0
	for f in figs:
		if int(f[1]) >= sb0 and int(f[1]) < sb0 + 3 and float((f[0] as Vector3).z) < -240.0:
			halted += 1
			if absf((f[0] as Vector3).x - A.HX) < A.HONOUR_X + 1.0:
				in_lane += 1
	kit.ok(halted >= int(st.get("halted_blocks", 0)) * A.HALT_FILES * A.HALT_RANKS, "halted blocks complete (%d men)"
		% halted)
	kit.eq(in_lane, 0, "no halted block in the column's lane")
	# fire pylons on both bollard lines and fire bowls on the grandstands' parapet: one flame each, in its bowl
	var pyl: Array = A.pylon_spots()
	var sf: Array = A.stand_fires()
	var left := 0
	for p: Vector3 in pyl:
		left += 1 if p.x < A.HX else 0
	kit.ok(left >= 20 and pyl.size() - left == left, "fire pylons on both lines (%d each)" % left)
	kit.ok(sf.size() >= 20, "fire bowls along the right grandstands (%d)" % sf.size())
	var flames: Array = avenue.placed.get("Flames", [])
	kit.eq(flames.size(), pyl.size() + sf.size(), "one flame per pylon and per parapet bowl")
	var low := 0
	for f in flames:
		var v: Vector3 = f[0]
		var on_stand := absf(v.x - (A.STAND_X - 0.25)) < 0.01
		if (not on_stand and v.y < 3.0) or (on_stand and (v.y < 1.5 or v.y > 1.8)):
			low += 1
	kit.eq(low, 0, "every flame burns in its bowl (pylons y >= 3 m, parapet bowls 1.5 - 1.8 m)")
	# delegations beyond the right crowd and the buses, only where p8's last frame looks
	var cb0 := int(avenue.slots["civ_back"][0])
	var deleg := 0
	var stray := 0
	for f in figs:
		var v: Vector3 = f[0]
		if int(f[1]) >= cb0 and int(f[1]) < cb0 + int(avenue.slots["civ_back"][1]) and v.x > 130.0:
			deleg += 1
			if v.x - 14.0 > A.deleg_reach(v.z - 10.0):     # a block (13 m wide, 10 m deep) starts inside the reach
				stray += 1
	kit.ok(deleg >= int(st.get("delegations", 0)) * 100, "delegation blocks filled (%d people)" % deleg)
	kit.eq(stray, 0, "delegations only where p8's last frame sees them")
	return true


## The zone the parade set's avenue crowd may use (parade_set._build_avenue_crowd reads these helpers).
func _crowd_zone() -> bool:
	var A = load(AVENUE)
	var lo := 1e9
	var hi := -1e9
	var outside := 0
	for i in 200:
		var z := -128.0 - i * 3.35
		for sd: float in [-1.0, 1.0]:
			var d: float = A.crowd_depth(sd, z)
			lo = minf(lo, d)
			hi = maxf(hi, d)
			if A.gate_corridor(sd, z) and not A._is_gate(sd, z):
				outside += 1
	kit.eq(outside, 0, "every crowd corridor lies inside a gate of the cordon")
	kit.ok(lo >= 2.0 and hi <= 28.0, "crowd depth 2..28 m (%.1f..%.1f)" % [lo, hi])
	for sd: float in [-1.0, 1.0]:
		kit.ok(A.crowd_depth(sd, -150.0) < A.crowd_depth(sd, -520.0) - 8.0, "the crowd thickens towards the plaza")
	var dl := 0.0
	var dr := 0.0
	for i in 50:
		dl += A.crowd_depth(-1.0, -450.0 - i * 6.8)
		dr += A.crowd_depth(1.0, -450.0 - i * 6.8)
	kit.ok(dl > dr, "deeper on the wide left side")
	kit.ok(A.X_BARRIER_L - A.crowd_depth(-1.0, -400.0) - 4.0 > -44.0, "the left crowd stays clear of the motor pool")
	kit.ok(not A.crowd_clear(A.X_BARRIER_L - 1.2, -140.0 - 36.0 * 3.0), "nobody inside a cordon lamp post")
	kit.ok(not A.crowd_clear(A.HX + 72.0, -470.0), "nobody inside a plaza lamp mast")
	kit.ok(A.crowd_clear(A.X_BARRIER_R + 6.0, -401.0), "open ground between them")
	return true


## The organised crowds (LANES, CROSS, crowd_groups, the right grandstands) and how the layer stages them.
func _organised() -> bool:
	var A = load(AVENUE)
	var st: Dictionary = avenue.stats
	# lanes lie inside the crowd's depth wherever they run, the strips are ordered front -> lane -> middle -> back
	var bad := 0
	var runs := 0
	for sd: float in [-1.0, 1.0]:
		var lanes: Array = A.LANES[int(sd)]
		for i in 160:
			var z := -230.0 - i * 3.5
			for k in lanes.size():
				if A.lane_active(sd, k, z):
					runs += 1
					var l: Array = lanes[k]
					if float(l[1]) + 2.4 > A.crowd_depth(sd, z) or float(l[0]) >= float(l[1]):
						bad += 1
					if A.strip_at(sd, (float(l[0]) + float(l[1])) * 0.5, z) != -1:
						bad += 1
			if A.lane_active(sd, 0, z) and A.strip_at(sd, 0.3, z) != 0:
				bad += 1
	kit.eq(bad, 0, "marshals' lanes inside the crowd, strips in order")
	kit.ok(runs > 300, "the lanes run most of the avenue (%d samples)" % runs)
	kit.ok(not A.lane_active(-1.0, 0, -200.0), "no lane in the cleared street")
	# cross-gaps: inside the avenue's range; the gates are cross-gaps
	for sd: float in [-1.0, 1.0]:
		for g: Array in A.CROSS[int(sd)]:
			kit.ok(float(g[0]) < A.Z_NEAR - 100.0 and float(g[0]) > A.Z_FAR, "cross-gap %d at %.0f inside the avenue"
				% [sd, float(g[0])])
		kit.ok(A.cross_gap(sd, -336.0 if sd < 0.0 else -290.0), "the gate %d is a cross-gap" % sd)
	# delegations: groups ordered along the avenue, every kind present on both sides
	for sd: float in [-1.0, 1.0]:
		var groups: Array = A.crowd_groups(sd)
		var kinds := {}
		var order := 0
		for i in groups.size():
			var g: Array = groups[i]
			kinds[int(g[2])] = true
			if float(g[0]) <= float(g[1]) or (i > 0 and float(g[0]) > float(groups[i - 1][1])):
				order += 1
		kit.eq(order, 0, "groups %d ordered and apart" % sd)
		kit.ok(kinds.size() >= 5, "mixed spectators and four kinds of delegation on side %d" % sd)
		kit.eq(A.crowd_groups(sd), groups, "crowd_groups is deterministic")
	kit.ok(int(st.get("crowd_banners", 0)) >= 30, "the delegations' banners stand (%d)" % int(st.get("crowd_banners", 0)))
	kit.ok(int(st.get("lane_lamps", 0)) >= 60, "lamps along the lanes (%d)" % int(st.get("lane_lamps", 0)))
	var cloth := avenue.get_node_or_null("AvenueGeometry/M_cloth") as MeshInstance3D
	if kit.ok(cloth != null, "banner cloth mesh"):
		var ab: AABB = cloth.mesh.get_aabb()
		kit.ok(ab.position.y >= 2.4 and ab.end.y <= 3.6, "banners held over the heads (%.1f - %.1f m)"
			% [ab.position.y, ab.end.y])
	# the right grandstands: behind the lane, in their sections, never in a cross-gap
	var ln: Array = A.LANES[1][0]
	kit.ok(A.STAND_X - A.X_BARRIER_R >= float(ln[1]), "the grandstands rise behind the right lane")
	for sec: Array in A.STAND_SECTIONS:
		kit.ok(not A.cross_gap(1.0, float(sec[0]) - 1.0) and not A.cross_gap(1.0, float(sec[1]) + 1.0),
			"stand section %.0f..%.0f between the cross-gaps" % [float(sec[0]), float(sec[1])])
		kit.ok(A.in_stand((float(sec[0]) + float(sec[1])) * 0.5), "in_stand inside section %.0f" % float(sec[0]))
	kit.ok(not A.in_stand(-300.0) and not A.in_stand(-780.0), "no stand outside the sections")
	var t5: Vector3 = A.stand_tier(A.STAND_TIERS - 1)
	kit.ok(t5.y > 5.0 and t5.y < 8.0 and t5.x > A.STAND_X, "six tiers rising away from the avenue (top %.1f m)" % t5.y)
	# the column's standards: their own Symbols-resolved texture (both variants exist)
	var sm: ShaderMaterial = builder.mats.get("standard")
	if kit.ok(sm != null, "standard material registered"):
		var tex: Texture2D = sm.get_shader_parameter("albedo_tex")
		kit.ok(tex != null, "standard texture loaded")
		if tex:
			kit.eq(tex.resource_path.ends_with("_hist.png"), Symbols.enabled(), "standard follows Symbols.enabled()")
	kit.ok(ResourceLoader.exists(DIR + "standard.png") and ResourceLoader.exists(DIR + "standard_hist.png"),
		"neutral standard and its _hist twin")
	var bn := avenue.get_node_or_null("Column/Banners/M_standard")
	kit.ok(bn != null, "the column's banners use the standard material")
	# the vehicle column reads from the roofs: snow caps, lit rears and headlight pools in the lamp kit
	for tag in ["Tanks", "LorriesTroops", "LorriesTarp"]:
		var mi := avenue.get_node_or_null("VehicleColumn/%s_lamp" % tag) as MultiMeshInstance3D
		if kit.ok(mi != null, "%s carry snow caps / headlight pools" % tag):
			var ab: AABB = mi.multimesh.mesh.get_aabb()
			kit.ok(ab.end.x > 12.0 and ab.end.y > 1.8, "%s: pool ahead (to %.1f m) and caps on top (%.1f m)"
				% [tag, ab.end.x, ab.end.y])
	return true


static func _min_gap(zs: Array) -> float:
	var a := zs.duplicate()
	a.sort()
	var m := 1e9
	for i in a.size() - 1:
		m = minf(m, float(a[i + 1]) - float(a[i]))
	return m


func _snapshot() -> Array:
	var out: Array = []
	for m in avenue.get("_movers"):
		out.append((m["node"] as Node3D).position)
	out.append(avenue.get_node("Crows").visible)
	out.append(avenue.get_node("Crows").rotation.y)
	out.append(snappedf((avenue.get("_beacon") as OmniLight3D).light_energy, 0.0001))
	return out


func _update() -> bool:
	var A = load(AVENUE)
	avenue.update(44.0)
	var a := _snapshot()
	avenue.update(41.0)
	var b := _snapshot()
	avenue.update(44.0)
	kit.eq(_snapshot(), a, "update(44) after update(41) = update(44)")
	kit.ne(a, b, "movers move between 41 s and 44 s")
	avenue.update(30.0)
	kit.ok(not avenue.get_node("Crows").visible, "no crows before p8")
	avenue.update(A.CROWS_FROM + 0.1)
	kit.ok(avenue.get_node("Crows").visible, "crows from p8 on")
	var lo := 1e9
	var hi := -1e9
	for i in 200:
		var e: float = A.beacon_energy(40.5 + i * 0.033)
		lo = minf(lo, e)
		hi = maxf(hi, e)
	kit.ok(lo >= 0.2 and lo < 0.4 and hi > 2.0 and hi <= 3.0, "beacon sweeps between glow and flash (%.2f..%.2f)"
		% [lo, hi])
	kit.ok(is_equal_approx(A.beacon_energy(41.0), A.beacon_energy(41.0 + 1.0 / A.BEACON_HZ)), "beacon is periodic")
	return true


func _rebuild() -> bool:
	var other: Node3D = (load(AVENUE) as GDScript).new()
	root.add_child(other)
	other.call("build", builder, "parade")
	var a: Array = avenue.placed["AvenueFigures"]
	var b: Array = other.placed["AvenueFigures"]
	kit.eq(b.size(), a.size(), "same number of figures")
	kit.ok(str(a) == str(b), "identical figures (seeded, deterministic)")
	kit.eq(str(other.placed["Flock"]), str(avenue.placed["Flock"]), "identical flock")
	kit.eq(int(other.stats["primitives"]), int(avenue.stats["primitives"]), "identical geometry")
	other.free()
	return true
