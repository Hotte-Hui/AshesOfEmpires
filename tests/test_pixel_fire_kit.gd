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

const Kit := preload("res://tests/support/test_kit.gd")
const PF := preload("res://scripts/render/pixel_fire.gd")
const FILMS := ["res://scenes/cinematics/ch3_fire/ch3_fire.gd", "res://scenes/cinematics/ch3_escape/ch3_escape.gd"]
const OWN := {"res://assets/cinematics/c3p2/fire/wisp_s.png": 3, "res://assets/cinematics/c3p2/fire/wisp_m.png": 3,
	"res://assets/cinematics/c3p2/fire/f3_warm.png": 3, "res://assets/cinematics/c3p2/escape/e3a_glow.png": 3,
	"res://assets/cinematics/c3p2/escape/breath.png": 3}

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
