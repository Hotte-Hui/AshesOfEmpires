extends RefCounted
## The pixel fire kit (round 13; tools/pixelgen/pixel_fire.py -> assets/fx/pixel_fire/, scripts/render/pixel_fire.gd):
## the rules that make its fire pixel art are checked on the files and on the two films that use it first
## (LS_C3_Fire, LS_C3_Escape):
##  * every sheet of kit.json exists and is n frames of w x h; every pixel of every sheet is HARD (alpha 0 or
##    255: no soft edges, no alpha gradients)
##  * a limited ramp: flames use only the five fire colours + the cooling one, puffs and banks three tones,
##    light pools three flat bands
##  * tiles of one set join in any order (their edge columns are the same in every frame) and wrap
##  * neighbouring instances never pulse in sync (PF.phase), light pools step slower than 3 Hz
##  * the films draw no flame, smoke or glow scaled, grown or alpha-faded any more (source guard), and every kit
##    sheet they ask for exists
##  * rollout (tools/pixelgen/pixel_fire_bake.py): the levels' fire strips and the other films' flame sheets are
##    baked from the kit -- hard pixels, a limited ramp; LS_C3_Fire draws its wall of fire as one mass (six band
##    passes) and its light layers are palette differences; the soft fire assets of the converted films are gone

const Kit := preload("res://tests/support/test_kit.gd")
const PF := preload("res://scripts/render/pixel_fire.gd")
const FILMS := ["res://scenes/cinematics/ch3_fire/ch3_fire.gd", "res://scenes/cinematics/ch3_escape/ch3_escape.gd",
	"res://scenes/cinematics/ch3_halves/ch3_halves.gd"]
const OWN := {"res://assets/cinematics/c3p2/fire/wisp_s.png": 3, "res://assets/cinematics/c3p2/fire/wisp_m.png": 3,
	"res://assets/cinematics/c3p2/fire/f3_warm.png": 3, "res://assets/cinematics/c3p2/escape/e3a_glow.png": 3,
	"res://assets/cinematics/c3p2/escape/breath.png": 3}

## level strips / film sheets baked from the kit -> the most colours they may hold
const ENV := "res://assets/environments/"
const BAKED := {
	ENV + "veltrava_registry/fx/flames_front_c.png": 6, ENV + "veltrava_registry/fx/flames_rows.png": 6,
	ENV + "veltrava_registry/fx/flames_chests.png": 6, ENV + "veltrava_registry/smoke_c.png": 6,
	ENV + "veltrava_registry/smoke_d.png": 6, ENV + "veltrava_registry/fx/roll_c0.png": 3,
	ENV + "veltrava_registry/fx/roll_d1.png": 3, ENV + "veltrava_registry/fx/plume_front_c.png": 6,
	ENV + "veltrava_registry/fx/heat_c.png": 6, ENV + "veltrava_quay/life/fire_win_1.png": 4,
	ENV + "veltrava_quay/fx/smoke_1.png": 6, ENV + "veltrava_quay/fx/smoke_ladder.png": 6,
	ENV + "karsk_c4p2/fx/barrel_flames.png": 5, ENV + "karsk_c4p2/fx/brazier_smoke.png": 3,
	ENV + "karsk_c4p2/fx/sandhouse_smoke.png": 3, ENV + "karsk_tunnels/fx/booth_smoke.png": 3,
	ENV + "karsk_railyard/fx/barrel_flames.png": 5, "res://assets/cinematics/c4p2/depot/flame.png": 6}
const GONE := ["res://assets/cinematics/c3p2/halves/flame_s.png", "res://assets/cinematics/c3p2/halves/smoke.png",
	"res://assets/cinematics/c3p2/halves/h3_plume.png", "res://assets/cinematics/c4p2/depot/embers.png"]

var kit: Kit
var _json: Dictionary = {}
var _cols: Dictionary = {}


func run() -> Array:
	kit = Kit.new()
	_json = JSON.parse_string(FileAccess.get_file_as_string(PF.DIR + "kit.json"))
	kit.run_case("sheets_exist_fit_and_are_hard_pixels", _sheets)
	kit.run_case("limited_ramp", _ramp)
	kit.run_case("tiles_join_in_any_order", _tiles)
	kit.run_case("neighbours_out_of_phase_and_light_under_3_hz", _phase)
	kit.run_case("films_use_the_kit_only", _films)
	kit.run_case("rollout_levels_and_films_bake_from_the_kit", _rollout)
	kit.cleanup()
	return kit.failures


func _img(path: String) -> Image:
	return Image.load_from_file(ProjectSettings.globalize_path(path))


## colours of the opaque pixels (RRGGBB -> true); hard[0] = how many pixels are neither clear nor opaque
func _colours(img: Image, hard: Array) -> Dictionary:
	var out := {}
	var soft := 0
	var data := img.get_data()
	var i := 0
	var n := data.size()
	while i < n:
		var a := data[i + 3]
		if a != 0:
			if a != 255:
				soft += 1
			out[(data[i] << 16) | (data[i + 1] << 8) | data[i + 2]] = true
		i += 4
	hard.append(soft)
	var named := {}
	for k in out:
		named["%06X" % int(k)] = true
	return named


func _sheets() -> bool:
	var sheets: Dictionary = _json.get("sheets", {})
	kit.ok(sheets.size() >= 30, "kit.json lists the kit (%d sheets)" % sheets.size())
	kit.eq(float(_json.get("tick", 0)), PF.TICK, "runtime tick == generator tick")
	var spark: Array = _json.get("spark", [])
	kit.eq(spark.size(), PF.SPARK.size(), "runtime spark ramp == generator spark ramp (length)")
	for i in mini(spark.size(), PF.SPARK.size()):
		kit.eq((PF.SPARK[i] as Color).to_html(false).to_upper(), str(spark[i]).trim_prefix("#"), "spark colour %d" % i)
	for sheet_name in sheets:
		var d: Dictionary = sheets[sheet_name]
		var img := _img(PF.DIR + sheet_name + ".png")
		if not kit.ok(img != null, "%s.png exists" % sheet_name):
			continue
		img.convert(Image.FORMAT_RGBA8)
		kit.eq([img.get_width(), img.get_height()], [int(d["n"]) * int(d["w"]), int(d["h"])], "%s: n x w, h" % sheet_name)
		kit.ok(int(d["n"]) >= 4 and int(d["n"]) <= 12, "%s: %d frames" % [sheet_name, int(d["n"])])
		var soft: Array = []
		_cols[sheet_name] = _colours(img, soft)
		kit.eq(soft[0], 0, "%s: hard pixels only (alpha 0 or 255)" % sheet_name)
		kit.ok(PF.sheet(sheet_name) != null, "%s loads through the runtime" % sheet_name)
	kit.eq(PF.missing, [], "no kit sheet missing")
	for path in OWN:
		var img2 := _img(path)
		if kit.ok(img2 != null, "%s exists" % path):
			img2.convert(Image.FORMAT_RGBA8)
			var soft2: Array = []
			var cols := _colours(img2, soft2)
			kit.eq(soft2[0], 0, "%s: hard pixels only" % path)
			kit.ok(cols.size() <= int(OWN[path]), "%s: %d colours" % [path, cols.size()])
	return true


func _ramp() -> bool:
	var fire := {}
	for c in _json.get("fire", []):
		fire[str(c).trim_prefix("#").to_upper()] = true
	fire[str(_json.get("cool", "")).trim_prefix("#").to_upper()] = true
	kit.eq(fire.size(), 6, "five fire colours and the cooling one")
	var sheets: Dictionary = _json.get("sheets", {})
	for sheet_name in sheets:
		if not _cols.has(sheet_name):
			continue
		var cols: Dictionary = _cols[sheet_name]
		var n := str(sheet_name)
		if n.begins_with("puff") or n.begins_with("bank") or n.begins_with("veil") or n.begins_with("glow") \
				or n.begins_with("pool"):
			kit.ok(cols.size() <= 3, "%s: three tones (%d)" % [n, cols.size()])
		elif not n.begins_with("sparks"):
			for c in cols:
				kit.ok(fire.has(c), "%s: #%s is a fire colour" % [n, c])
	return true


func _tiles() -> bool:
	for pair in [["wall_a", "wall_b"], ["low_a", "low_b"], ["bank_a", "bank_b"], ["veil_a", "veil_b"],
			["bank_a_grey", "bank_b_grey"]]:
		var a := _img(PF.DIR + str(pair[0]) + ".png")
		var b := _img(PF.DIR + str(pair[1]) + ".png")
		var d := PF.info(str(pair[0]))
		if not kit.ok(a != null and b != null and not d.is_empty(), "%s / %s exist" % pair):
			continue
		kit.eq(PF.info(str(pair[1])), d, "%s / %s: same frames and size" % pair)
		var w := int(d["w"])
		var bad := 0
		for f in int(d["n"]):
			for y in int(d["h"]):
				for x in [f * w, f * w + w - 1]:
					if a.get_pixel(x, y) != b.get_pixel(x, y):
						bad += 1
		kit.eq(bad, 0, "%s / %s: the same edge columns in every frame (they join in any order)" % pair)
	return true


func _phase() -> bool:
	var worst := 1.0
	for i in 64:
		var d := absf(PF.phase(i) - PF.phase(i + 1))
		worst = minf(worst, minf(d, 1.0 - d))
	kit.ok(worst >= 0.3, "neighbouring instances are at least 0.3 of a loop apart (%.2f)" % worst)
	var flips := 0
	for i in 64:
		if PF.mirror(i):
			flips += 1
	kit.ok(flips >= 24 and flips <= 40, "about half of the instances are mirrored (%d of 64)" % flips)
	kit.ok(PF.LIGHT_HZ < 3.0, "light pools step slower than 3 Hz")
	kit.ok(PF.tick(1.0) == int(PF.TICK) and PF.tick(1.0, 0.5) == int(PF.TICK) / 2, "reduced motion halves the flame rate")
	return true


func _films() -> bool:
	for path in FILMS:
		var src := FileAccess.get_file_as_string(path)
		kit.ok(src.contains("PF.flame(") and src.contains("PF.plume("), "%s plays the kit" % path.get_file())
		for old in ["_draw_scaled", "_draw_grown", "fire_halo", "smoke_hot", "flame_out", "fire_wobble(", "ember.png",
				"smoke.png"]:
			kit.ok(not src.contains(old), "%s: no %s any more" % [path.get_file(), old])
	return true


## Round 13 rollout: what burns in the levels and in the other films is baked from the kit's parts.
func _rollout() -> bool:
	for path: String in BAKED:
		var img := _img(path)
		if not kit.ok(img != null, "%s loads" % path.get_file()):
			continue
		img.convert(Image.FORMAT_RGBA8)
		var hard: Array = []
		var cols := _colours(img, hard)
		kit.eq(hard[0], 0, "%s: hard pixels only" % path.trim_prefix(ENV))
		kit.ok(cols.size() >= 2 and cols.size() <= int(BAKED[path]),
			"%s: a limited ramp (%d colours)" % [path.trim_prefix(ENV), cols.size()])
	for path: String in GONE:
		kit.ok(not FileAccess.file_exists(path), "%s (soft) is gone" % path.get_file())
	# a mass of fire: six passes, cooling flamelets first, then the bands from the rim to the core
	var mats := PF.mass_materials()
	kit.eq(mats.size(), 6, "a mass of fire is drawn in six passes")
	for i in mats.size():
		kit.eq(int(mats[i].get_shader_parameter("level")), i - 1, "pass %d paints band %d" % [i, i - 1])
	var fire_src := FileAccess.get_file_as_string("res://scenes/cinematics/ch3_fire/ch3_fire.gd")
	kit.ok(fire_src.contains("PF.mass_materials()"), "LS_C3_Fire draws its wall of fire as one mass")
	# the fire's light layers are palette differences: background + layer is a picture in few colours again
	for pair in [["fire/f2_bg.png", "fire/f2_glow.png"], ["fire/f4_bg.png", "fire/f4_lit.png"]]:
		var bg := _img("res://assets/cinematics/c3p2/" + str(pair[0]))
		var lit := _img("res://assets/cinematics/c3p2/" + str(pair[1]))
		if not kit.ok(bg != null and lit != null and bg.get_size() == lit.get_size(), "%s + %s load" % pair):
			continue
		bg.convert(Image.FORMAT_RGBA8)
		lit.convert(Image.FORMAT_RGBA8)
		var a := bg.get_data()
		var b := lit.get_data()
		var seen := {}
		var i := 0
		while i < a.size():
			var k := 1 if b[i + 3] > 0 else 0
			seen[(mini(255, a[i] + b[i] * k) << 16) | (mini(255, a[i + 1] + b[i + 1] * k) << 8)
				| mini(255, a[i + 2] + b[i + 2] * k)] = true
			i += 4
		kit.ok(seen.size() <= 96, "%s + %s is a palette picture (%d colours)" % [pair[0], pair[1], seen.size()])
	return true
