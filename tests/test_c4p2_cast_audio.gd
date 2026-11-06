extends RefCounted
## Chapter 4 part 2 — cast and sound (owner: cast-audio; documentation/asset_manifest_parts/c4p2_cast_audio.md):
##  * the new speakers of C4P2_DESIGN §5 (maria, hanna, wendt, blockwart): sheets on the round-2 rig (the NPC rows,
##    8-frame idle and talk, blink / glance / gesture variants, front views, an NPC walking speed; Maria shovels and
##    Kuhnert walks his card box in a work loop), normal maps, they load and play on SpriteRig; living portraits
##    (4 expressions x 6 states: the mouth opens, the eyes close, the expressions differ); names in
##    de_c4p2_characters.json; individual silhouettes and faces (no twin of each other or of the existing cast)
##  * the three life sheets (guard_karsk, press_officer, stapo_civil): side rows + a working idle, no portrait
##  * the optional look alexei_press (KarskB): Alexei's rows + the carry rows (the guidebook under his arm), his
##    silhouette and pace, the look readable in the world (flaps tied up, a new cream scarf), a living portrait
##  * round 10 art review: no new figure is a recolour of the one it was taken for (Hanna / Elena, Wendt / Kessler,
##    Maria / Irina: sprite head colours and portrait colour layout differ clearly); the working idles play in the
##    part-2 level shells (idle_anim = "work_side" on Maria, the guard, the minder, the man at the kiosk, Kuhnert)
##  * real insignia only as *_hist (§12.4): blockwart's armband and the guard's star exist only in sheet_hist.png,
##    same size and alpha as the neutral sheet (the normal map serves both), a handful of pixels apart
##  * every speaker of the part-2 dialogues and every char_id of the two part-2 level shells has a sheet (and the
##    speakers a portrait)
##  * sound (§8): the four level ambiences, two music loops and the closing cue, the puzzle sounds — 44.1 kHz /
##    16 bit, loop chunks exactly on the loops (imported LOOP_FORWARD, lossless), levels inside the round-8 windows,
##    seamless seams, one-shots ending in silence; the steps and the teeth are complete random-variant sets, every
##    other one-shot is not named like a variant; Audio loops the two loops and not the cue; every puzzle sound the
##    puzzle UIs' fallback chains ask for exists and Audio resolves it (has_sound)
##  * the closing cue sits on LS_C4P2_Clock: the generator's shot times are the registered shots, the tick sounds on
##    every second from k1 and never on k5, nothing sounds after the tick has stopped but the dying dyad
##  * wiring: the level shells and the c4p2.json switches name existing files of this chapter; every c4p2 sound a
##    part-2 film or puzzle script names exists; who does not call the puzzle sounds yet is reported as pending

const Kit := preload("res://tests/support/test_kit.gd")
const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const AudioSvc := preload("res://scripts/core/audio.gd")
const CHAR := "res://assets/characters/"
const AMB := "res://assets/audio/amb/"
const MUS := "res://assets/audio/music/"
const SFX := "res://assets/audio/sfx/"
const SPEAKERS := ["maria", "hanna", "wendt", "blockwart"]
const LIFE := ["guard_karsk", "press_officer", "stapo_civil"]
const NPC_ROWS := ["idle_side", "walk_side", "idle_front", "talk_side", "blink_side", "look_side", "gesture_side",
	"blink_front", "talk_front"]
const LIFE_ROWS := ["idle_side", "walk_side", "talk_side", "blink_side", "look_side", "gesture_side", "work_side"]
const EXTRA_ROWS := {"maria": ["work_side"], "blockwart": ["work_side"]}
const HIST := ["blockwart", "guard_karsk"]
## looks of existing characters -> their base
const LOOKS := {"alexei_press": "alexei"}
const CARRY_ROWS := ["carry_side", "carry_idle_side"]
const EXPR := ["neutral", "concerned", "determined", "surprised"]
## existing figures the new silhouettes must not copy (idle_side frame 0)
const REFERENCE := ["alexei", "konrad", "emil", "clerk", "guard", "conductor", "kessler", "typist", "berlin_mother",
	"berlin_father", "porter", "librarian", "worker_a", "worker_b", "border_officer", "babushka", "irina", "vendor",
	"elena", "journalist", "voronova", "lev", "marta", "registrar"]
## existing faces the new portraits must not copy
const FACES := ["konrad", "alexei", "irina", "vendor", "babushka", "elena", "marta", "kessler", "typist", "lev",
	"registrar", "berlin_mother", "berlin_father", "journalist", "clerk"]
## round-10 art review: the figures the new ones were taken for (new -> existing).  The sprite's head (hair /
## headgear, top 9 rows of idle_side frame 0) and the portrait's colour layout must differ clearly -- a recolour of
## the same design does not pass (the reviewed versions measured 25-57 and 26-40)
const TWINS := {"hanna": "elena", "wendt": "kessler", "maria": "irina"}
const TWIN_HEAD_MIN := 60.0       ## sum of |dR|+|dG|+|dB| (0..255 each) of the mean head colours
const TWIN_PORTRAIT_MIN := 40.0   ## mean colour distance of the 14 x 14 cells of the neutral portraits
## the working idles play in the part-2 levels (C4P2_DESIGN §4: people placed with intent): char_id -> level
const WORKERS := {"maria": "res://scenes/levels/L_C4P2_Karsk.tscn", "guard_karsk": "res://scenes/levels/L_C4P2_Karsk.tscn",
	"press_officer": "res://scenes/levels/L_C4P2_Karsk.tscn", "stapo_civil": "res://scenes/levels/L_C4P2_Berlin.tscn",
	"blockwart": "res://scenes/levels/L_C4P2_Berlin.tscn"}
## file -> [dir, channels, loop, frames (0 = any)]
const SOUNDS := {
	"amb_karsk_depot": [AMB, 2, true, 2646000], "amb_karsk_platform": [AMB, 2, true, 2646000],
	"amb_berlin_station": [AMB, 2, true, 2646000], "amb_berlin_courtyard": [AMB, 2, true, 2646000],
	"mus_c4p2_karsk": [MUS, 2, true, 3763200], "mus_c4p2_berlin": [MUS, 2, true, 2688000],
	"mus_c4p2_clock": [MUS, 2, false, 1080450],
	"c4p2_halves_snap": [SFX, 2, false, 0], "c4p2_stamp_close": [SFX, 2, false, 0], "c4p2_shutter": [SFX, 2, false, 0],
	"c4p2_tooth_1": [SFX, 2, false, 0], "c4p2_tooth_2": [SFX, 2, false, 0], "c4p2_tooth_3": [SFX, 2, false, 0],
	"c4p2_steps_1": [SFX, 2, false, 0], "c4p2_steps_2": [SFX, 2, false, 0], "c4p2_steps_3": [SFX, 2, false, 0],
	"c4p2_steps_down_1": [SFX, 2, false, 0], "c4p2_steps_down_2": [SFX, 2, false, 0],
	"c4p2_steps_down_3": [SFX, 2, false, 0], "c4p2_attic_door": [SFX, 2, false, 0], "c4p2_spyhole": [SFX, 2, false, 0],
	"c4p2_door": [SFX, 2, false, 0], "c4p2_pencil": [SFX, 2, false, 0], "c4p2_knock": [SFX, 2, false, 0],
}
## random-variant sets (Audio.ui / Audio.sfx("c4p2_steps") picks one of them)
const VARIANT_SETS := {"c4p2_steps": 3, "c4p2_steps_down": 3, "c4p2_tooth": 3}
## the puzzle sounds (ids = the ones the puzzle UIs ask for) and who plays them; reported as pending until called
const PUZZLE_CUES := {"c4p2_halves_snap": "JoinPuzzle", "c4p2_tooth": "JoinPuzzle", "c4p2_stamp_close": "JoinPuzzle",
	"c4p2_shutter": "JoinPuzzle", "c4p2_steps": "HousePuzzle", "c4p2_steps_down": "HousePuzzle",
	"c4p2_attic_door": "HousePuzzle", "c4p2_spyhole": "HousePuzzle", "c4p2_door": "HousePuzzle",
	"c4p2_pencil": "HousePuzzle", "c4p2_knock": "HousePuzzle"}
const GEN := "res://tools/audiogen/c4p2_audio.py"
## loudness windows (dBFS RMS min, max; peak max), as enforced by tools/audiogen/c4p2_audio.py (the round-8 windows)
const WINDOW := {"amb": [-28.0, -21.0, -2.5], "music": [-25.0, -19.0, -0.8], "loop": [-36.0, -19.0, -2.5],
	"sfx": [-45.0, -9.0, -2.5]}
const LEVELS := {"res://scenes/levels/L_C4P2_Karsk.tscn": ["amb_karsk_depot", "mus_c4p2_karsk"],
	"res://scenes/levels/L_C4P2_Berlin.tscn": ["amb_berlin_station", "mus_c4p2_berlin"]}
## C4P2_DESIGN §3: ambience / music per part-2 scene
const SWITCHES := {"L_C4P2_KarskA": ["amb_karsk_depot", "mus_c4p2_karsk"],
	"L_C4P2_BerlinA": ["amb_berlin_station", "mus_c4p2_berlin"],
	"L_C4P2_KarskB": ["amb_karsk_platform", "mus_c4p2_karsk"],
	"L_C4P2_BerlinB": ["amb_berlin_courtyard", "mus_c4p2_berlin"]}
const CINE_DIRS := ["res://scenes/cinematics/ch4p2_common/", "res://scenes/cinematics/ch4p2_depot/",
	"res://scenes/cinematics/ch4p2_steam/", "res://scenes/cinematics/ch4p2_book/",
	"res://scenes/cinematics/ch4p2_express/", "res://scenes/cinematics/ch4p2_clock/"]
const PUZZLE_SCRIPTS := ["res://scripts/ui/house_puzzle.gd", "res://scripts/ui/join_puzzle.gd",
	"res://scripts/ui/route_puzzle.gd"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("cast_sheets_contract", _sheets)
	kit.run_case("cast_plays_on_the_rig", _rig)
	kit.run_case("cast_living_portraits", _portraits)
	kit.run_case("cast_life_sheets_and_hist_variants", _life_and_hist)
	kit.run_case("cast_look_alexei_press", _looks)
	kit.run_case("cast_individual_silhouettes_and_faces", _individual)
	kit.run_case("cast_no_twins_of_the_review", _no_twins)
	kit.run_case("cast_work_loops_play_in_the_levels", _work_loops)
	kit.run_case("cast_names_and_speakers", _speakers)
	kit.run_case("audio_files_format_and_loops", _audio_files)
	kit.run_case("audio_levels_and_seams", _audio_levels)
	kit.run_case("audio_registry_variants_and_loops", _registry)
	kit.run_case("audio_clock_cue_on_the_film", _clock)
	kit.run_case("audio_wiring", _wiring)
	kit.run_case("audio_pending_report", _pending)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


static func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	var im := Image.load_from_file(ProjectSettings.globalize_path(path))
	if im != null and im.get_format() != Image.FORMAT_RGBA8:
		im.convert(Image.FORMAT_RGBA8)
	return im


static func _rows_of(id: String) -> Array:
	return (LIFE_ROWS if id in LIFE else NPC_ROWS + EXTRA_ROWS.get(id, []))


# ------------------------------------------------------------------------------------------------ cast
func _sheets() -> bool:
	for id in SPEAKERS + LIFE:
		var meta = _json(CHAR + id + "/sheet.json")
		if not kit.ok(meta is Dictionary, "%s: sheet.json" % id):
			continue
		kit.eq(meta.get("cell"), [32.0, 56.0], "%s: cell" % id)
		kit.eq(meta.get("origin"), [16.0, 54.0], "%s: origin (feet)" % id)
		kit.eq(str(meta.get("facing", "")), "right", "%s: drawn facing right" % id)
		var anims: Dictionary = meta.get("anims", {})
		kit.eq(anims.keys(), _rows_of(id), "%s: the rows in their order" % id)
		for a in ["idle_side", "talk_side", "idle_front", "talk_front", "walk_side"]:
			if anims.has(a):
				kit.eq(int(anims[a].get("frames", 0)), 8, "%s: %s has 8 frames (round-2 rhythm)" % [id, a])
		var vars: Array = anims.get("idle_side", {}).get("variants", [])
		for v in ["blink_side", "look_side", "gesture_side"]:
			kit.ok(v in vars, "%s: %s is an idle variant" % [id, v])
			kit.ok(not bool(anims.get(v, {}).get("loop", true)), "%s: the variant %s does not loop" % [id, v])
		if anims.has("work_side"):
			kit.ok(bool(anims["work_side"].get("loop", false)) and int(anims["work_side"].get("frames", 0)) >= 6,
				"%s: work_side is a loop of >= 6 frames" % id)
		var gs := float(meta.get("ground_speed", {}).get("walk_side", 0.0))
		kit.ok(gs >= 15.0 and gs <= 30.0, "%s: walk_side ground speed %.1f px/s (an NPC's pace)" % [id, gs])
		var img := _img(CHAR + id + "/sheet.png")
		var nrm := _img(CHAR + id + "/sheet_n.png")
		if not kit.ok(img != null and nrm != null, "%s: sheet.png + sheet_n.png load" % id):
			continue
		var cols := 0
		for a in anims:
			cols = maxi(cols, int(anims[a].get("frames", 0)))
		kit.eq([img.get_width(), img.get_height()], [cols * 32, anims.size() * 56], "%s: sheet size = frames x rows" % id)
		kit.eq([nrm.get_width(), nrm.get_height()], [img.get_width(), img.get_height()], "%s: normal map size" % id)
		var feet := -1
		var top := 56
		for y in 56:
			for x in 32:
				if img.get_pixel(x, y).a > 0.0:
					feet = maxi(feet, y)
					top = mini(top, y)
		kit.eq(feet, 54, "%s: feet on the origin row" % id)
		kit.ok(top >= 4 and 54 - top + 1 >= 40, "%s: figure height %d px (adult, not clipped)" % [id, 54 - top + 1])
		# the work loops really work: the figure changes over the loop (shovel, cards, fire, cigarette, paper)
		if anims.has("work_side"):
			var r := int(anims["work_side"]["row"])
			var moved := 0
			for f in range(1, int(anims["work_side"]["frames"])):
				var n := 0
				for y in 56:
					for x in 32:
						if (img.get_pixel(x, r * 56 + y).a > 0.0) != (img.get_pixel(f * 32 + x, r * 56 + y).a > 0.0):
							n += 1
				moved = maxi(moved, n)
			kit.ok(moved >= 8, "%s: the work loop moves (%d px)" % [id, moved])
	return true


func _rig() -> bool:
	for id in SPEAKERS + LIFE:
		var r: Node2D = kit.mount(SpriteRig.new())
		if not kit.ok(r.load_character(id), "%s loads on the rig" % id):
			continue
		for a in _rows_of(id):
			kit.ok(r.has_anim(a), "%s: has %s" % [id, a])
		r.play("talk_side")
		kit.eq(r.anim, "talk_side", "%s: talk_side plays" % id)
		var idle := "work_side" if r.has_anim("work_side") else "idle_side"
		r.play(idle)
		kit.eq(r.anim, idle, "%s: %s plays" % [id, idle])
		kit.ok(r.ground_speed("walk_side") > 10.0, "%s: walk_side has a ground speed" % id)
	return true


func _portraits() -> bool:
	for id in SPEAKERS:
		var p = _json(CHAR + id + "/portrait.json")
		if not kit.ok(p is Dictionary, "%s: portrait.json" % id):
			continue
		kit.eq(p.get("size"), [112.0, 112.0], "%s: portrait size" % id)
		kit.eq(p.get("expressions"), EXPR, "%s: the four expressions" % id)
		var anim: Dictionary = p.get("anim", {}) if p.get("anim") is Dictionary else {}
		kit.eq(str(anim.get("file", "")), "portrait_anim.png", "%s: living portrait" % id)
		kit.eq(str(anim.get("spec", "")), "tools/pixelgen/characters_c4p2.py", "%s: made by the c4p2 generator" % id)
		var rows: Array = anim.get("rows", [])
		kit.ok(rows.size() >= 4 and "talk_open" in rows and "blink" in rows, "%s: talk and blink rows" % id)
		var grid := _img(CHAR + id + "/portrait_anim.png")
		var strip := _img(CHAR + id + "/portrait.png")
		if not kit.ok(grid != null and strip != null, "%s: portrait images load" % id):
			continue
		kit.eq([grid.get_width(), grid.get_height()], [448, 112 * rows.size()], "%s: grid = 4 expressions x rows" % id)
		kit.eq([strip.get_width(), strip.get_height()], [448, 112], "%s: static strip" % id)
		kit.ok(_opaque(strip), "%s: the strip is opaque (painted backdrop)" % id)
		var r_talk := rows.find("talk_open")
		var r_blink := rows.find("blink")
		for e in 4:
			kit.ok(_region_diff(grid, e, 0, e, r_talk) >= 6, "%s/%s: the mouth opens" % [id, EXPR[e]])
			kit.ok(_region_diff(grid, e, 0, e, r_blink) >= 6, "%s/%s: the eyes close" % [id, EXPR[e]])
		for e in range(1, 4):
			kit.ok(_region_diff(grid, 0, 0, e, 0) >= 30, "%s: %s differs from neutral" % [id, EXPR[e]])
		# the static strip is the grid's rest row
		kit.eq(_region_diff_imgs(strip, grid, 0), 0, "%s: portrait.png = the rest row of the grid" % id)
	return true


static func _opaque(img: Image) -> bool:
	for y in range(0, img.get_height(), 3):
		for x in range(0, img.get_width(), 3):
			if img.get_pixel(x, y).a < 1.0:
				return false
	return true


## Changed pixels between two 112 px cells of a portrait grid (column, row), inside the face area.
static func _region_diff(img: Image, ca: int, ra: int, cb: int, rb: int) -> int:
	if ra < 0 or rb < 0:
		return 0
	var n := 0
	for y in range(16, 104):
		for x in range(16, 104):
			if img.get_pixel(ca * 112 + x, ra * 112 + y) != img.get_pixel(cb * 112 + x, rb * 112 + y):
				n += 1
	return n


## Changed pixels (sampled every 2nd px) between the strip and row `row` of the grid, all four columns.
static func _region_diff_imgs(strip: Image, grid: Image, row: int) -> int:
	var n := 0
	for y in range(0, 112, 2):
		for x in range(0, 448, 2):
			if strip.get_pixel(x, y) != grid.get_pixel(x, row * 112 + y):
				n += 1
	return n


func _looks() -> bool:
	for id in LOOKS:
		var base: String = LOOKS[id]
		var meta = _json(CHAR + id + "/sheet.json")
		var bmeta = _json(CHAR + base + "/sheet.json")
		if not kit.ok(meta is Dictionary and bmeta is Dictionary, "%s and %s: sheet.json" % [id, base]):
			continue
		var anims: Dictionary = meta.get("anims", {})
		var banims: Dictionary = bmeta.get("anims", {})
		var want: Array = banims.keys() + CARRY_ROWS
		kit.eq(anims.keys(), want, "%s: %s's rows in their order, the carry rows appended" % [id, base])
		for a in banims:
			kit.eq([int(anims.get(a, {}).get("row", -1)), int(anims.get(a, {}).get("frames", 0))],
				[int(banims[a]["row"]), int(banims[a]["frames"])], "%s: %s keeps its row and length" % [id, a])
		var gs: Dictionary = meta.get("ground_speed", {})
		kit.eq(float(gs.get("walk_side", 0.0)), float(bmeta.get("ground_speed", {}).get("walk_side", -1.0)), "%s walks at %s's pace" % [id, base])
		kit.eq(float(gs.get("carry_side", 0.0)), float(gs.get("walk_side", -1.0)), "%s: carry_side walks like walk_side" % id)
		var img := _img(CHAR + id + "/sheet.png")
		var bimg := _img(CHAR + base + "/sheet.png")
		if not kit.ok(img != null and bimg != null, "%s: sheets load" % id):
			continue
		# the same person: idle_side frame 0 has the base's silhouette; the clean scarf changes colours only
		var same := 0
		var uni := 0
		var col := 0
		for y in 56:
			for x in 32:
				var pa := img.get_pixel(x, y)
				var pb := bimg.get_pixel(x, y)
				if pa.a > 0.0 and pb.a > 0.0:
					same += 1
					if pa != pb:
						col += 1
				if pa.a > 0.0 or pb.a > 0.0:
					uni += 1
		kit.ok(float(same) / maxf(1.0, float(uni)) >= 0.95, "%s: %s's silhouette (IoU %.2f)" % [id, base, float(same) / maxf(1.0, float(uni))])
		# round 10 review: the look must read in the world (flaps tied up, the new cream scarf), not only in the portrait
		kit.ok(col >= 30, "%s: the look shows in the world (%d px differ from %s, >= 30)" % [id, col, base])
		# the guidebook is in his hands in the carry rows
		var r_idle := int(anims["idle_side"]["row"])
		var r_carry := int(anims.get("carry_idle_side", {}).get("row", -1))
		var diff := 0
		if r_carry >= 0:
			for y in 56:
				for x in 32:
					if img.get_pixel(x, r_idle * 56 + y) != img.get_pixel(x, r_carry * 56 + y):
						diff += 1
		kit.ok(diff >= 12, "%s: the carry rows hold the guidebook (%d px)" % [id, diff])
		var r := SpriteRig.new()
		kit.mount(r)
		if kit.ok(r.load_character(id), "%s loads on the rig" % id):
			for a in want:
				kit.ok(r.has_anim(a), "%s: has %s" % [id, a])
		# a look needs its own living portrait (the dialogue box resolves the look first)
		var p = _json(CHAR + id + "/portrait.json")
		if kit.ok(p is Dictionary, "%s: portrait.json" % id):
			kit.eq(p.get("expressions"), EXPR, "%s: the four expressions" % id)
			kit.eq(str((p.get("anim", {}) as Dictionary).get("file", "")), "portrait_anim.png", "%s: living portrait" % id)
			var a2 := _img(CHAR + id + "/portrait.png")
			var b2 := _img(CHAR + base + "/portrait.png")
			if kit.ok(a2 != null and b2 != null, "%s: portraits load" % id):
				kit.ok(_region_diff(a2, 0, 0, 0, 0) == 0 and _region_diff_pair(a2, b2) > 30, "%s: shaved, its own portrait" % id)
	return true


## Changed pixels between the neutral columns of two portrait strips, inside the face area.
static func _region_diff_pair(a: Image, b: Image) -> int:
	var n := 0
	for y in range(16, 104):
		for x in range(16, 104):
			if a.get_pixel(x, y) != b.get_pixel(x, y):
				n += 1
	return n


func _life_and_hist() -> bool:
	for id in LIFE:
		kit.ok(not FileAccess.file_exists(CHAR + id + "/portrait.png"), "%s: a life sheet ships no portrait" % id)
		var meta = _json(CHAR + id + "/sheet.json")
		if meta is Dictionary:
			kit.ok(not meta.get("anims", {}).has("idle_front"), "%s: side rows only" % id)
	for id in HIST:
		var a := _img(CHAR + id + "/sheet.png")
		var h := _img(CHAR + id + "/sheet_hist.png")
		if not kit.ok(a != null and h != null, "%s: sheet.png and sheet_hist.png" % id):
			continue
		if not kit.eq([h.get_width(), h.get_height()], [a.get_width(), a.get_height()], "%s: hist sheet size" % id):
			continue
		var alpha_diff := 0
		var col_diff := 0
		var cells := {}
		for y in a.get_height():
			for x in a.get_width():
				var pa := a.get_pixel(x, y)
				var ph := h.get_pixel(x, y)
				if (pa.a > 0.0) != (ph.a > 0.0):
					alpha_diff += 1
				elif pa != ph:
					col_diff += 1
					var key := "%d_%d" % [x / 32, y / 56]
					cells[key] = int(cells.get(key, 0)) + 1
		kit.eq(alpha_diff, 0, "%s: the hist sheet keeps the neutral alpha (one normal map)" % id)
		var worst := 0
		for k in cells:
			worst = maxi(worst, int(cells[k]))
		kit.ok(col_diff > 0 and worst <= 24, "%s: the insignia is a few pixels per cell (%d px, max %d per cell)" % [id, col_diff, worst])
		# the neutral sheet carries no red insignia colour at all (§12.4)
		kit.ok(not _has_red(a), "%s: the neutral sheet has no red insignia" % id)
	return true


## Any strongly red pixel (r high, g / b low): the hist armband / star colour.
static func _has_red(img: Image) -> bool:
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			if c.a > 0.0 and c.r > 0.45 and c.g < 0.25 and c.b < 0.25:
				return true
	return false


## Opaque mask of idle_side frame 0 (32 x 56) of a sheet directory, or an empty array.
static func _silhouette(id: String) -> PackedByteArray:
	var meta = _json(CHAR + id + "/sheet.json")
	var img := _img(CHAR + id + "/sheet.png")
	var out := PackedByteArray()
	if not (meta is Dictionary) or img == null:
		return out
	var r := int(meta.get("anims", {}).get("idle_side", {}).get("row", 0))
	out.resize(32 * 56)
	for y in 56:
		for x in 32:
			out[y * 32 + x] = 1 if img.get_pixel(x, r * 56 + y).a > 0.0 else 0
	return out


func _individual() -> bool:
	var cast: Array = SPEAKERS + LIFE
	var sil := {}
	for id in cast + REFERENCE:
		var s := _silhouette(id)
		if s.size() > 0:
			sil[id] = s
	for a in cast:
		if not kit.ok(sil.has(a), "%s: silhouette" % a):
			continue
		for b in sil:
			if a == b or (b in cast and cast.find(b) < cast.find(a)):
				continue
			var inter := 0
			var uni := 0
			var sa: PackedByteArray = sil[a]
			var sb: PackedByteArray = sil[b]
			for i in sa.size():
				inter += sa[i] & sb[i]
				uni += sa[i] | sb[i]
			var iou := float(inter) / maxf(1.0, float(uni))
			kit.ok(iou <= 0.90, "%s vs %s: silhouettes differ (IoU %.2f)" % [a, b, iou])
	# faces: the neutral portraits of the four differ from each other and from the existing speakers
	var faces := {}
	for id in SPEAKERS + FACES:
		var im := _img(CHAR + id + "/portrait.png")
		if im != null:
			faces[id] = im
	for a in SPEAKERS:
		if not faces.has(a):
			continue
		for b in faces:
			if a == b or (b in SPEAKERS and SPEAKERS.find(b) < SPEAKERS.find(a)):
				continue
			var n := 0
			for y in range(16, 104, 2):
				for x in range(16, 104, 2):
					if faces[a].get_pixel(x, y) != faces[b].get_pixel(x, y):
						n += 1
			kit.ok(n > 1200, "%s vs %s: an individual face (%d of 1936 samples differ)" % [a, b, n])
	return true


## Mean colour (0..255) of the top 9 opaque rows of idle_side frame 0: hair, headgear, the upper face.
static func _head_colour(id: String) -> Vector3:
	var meta = _json(CHAR + id + "/sheet.json")
	var img := _img(CHAR + id + "/sheet.png")
	if not (meta is Dictionary) or img == null:
		return Vector3(-1000, -1000, -1000)
	var r := int(meta.get("anims", {}).get("idle_side", {}).get("row", 0))
	var top := -1
	for y in 56:
		for x in 32:
			if img.get_pixel(x, r * 56 + y).a > 0.0:
				top = y
				break
		if top >= 0:
			break
	var sum := Vector3.ZERO
	var n := 0
	for y in range(maxi(top, 0), mini(top + 9, 56)):
		for x in 32:
			var c := img.get_pixel(x, r * 56 + y)
			if c.a > 0.0:
				sum += Vector3(c.r, c.g, c.b) * 255.0
				n += 1
	return sum / maxf(1.0, float(n))


## Mean colour distance of the 14 x 14 cells (8 x 8 px) of two neutral portraits (the first 112 px column).
static func _portrait_cell_distance(a: Image, b: Image) -> float:
	var total := 0.0
	for cy in 14:
		for cx in 14:
			var sa := Vector3.ZERO
			var sb := Vector3.ZERO
			for y in range(cy * 8, cy * 8 + 8):
				for x in range(cx * 8, cx * 8 + 8):
					var pa := a.get_pixel(x, y)
					var pb := b.get_pixel(x, y)
					sa += Vector3(pa.r, pa.g, pa.b)
					sb += Vector3(pb.r, pb.g, pb.b)
			var d := (sa - sb) * (255.0 / 64.0)
			total += absf(d.x) + absf(d.y) + absf(d.z)
	return total / 196.0


func _no_twins() -> bool:
	for id in TWINS:
		var other: String = TWINS[id]
		var ha := _head_colour(id)
		var hb := _head_colour(other)
		var dh := absf(ha.x - hb.x) + absf(ha.y - hb.y) + absf(ha.z - hb.z)
		kit.ok(dh >= TWIN_HEAD_MIN, "%s is no recolour of %s: head colours differ by %.1f (>= %.0f)" % [id, other, dh, TWIN_HEAD_MIN])
		var pa := _img(CHAR + id + "/portrait.png")
		var pb := _img(CHAR + other + "/portrait.png")
		if kit.ok(pa != null and pb != null, "%s / %s: portraits load" % [id, other]):
			var dp := _portrait_cell_distance(pa, pb)
			kit.ok(dp >= TWIN_PORTRAIT_MIN, "%s's portrait is no copy of %s's: cell colour distance %.1f (>= %.0f)" % [id, other, dp, TWIN_PORTRAIT_MIN])
	return true


## The node block (text up to the next "[node") of the NPC with this char_id in a level file, or "".
static func _npc_block(level_text: String, id: String) -> String:
	var at := level_text.find("char_id = \"%s\"" % id)
	if at < 0:
		return ""
	var end := level_text.find("[node", at)
	return level_text.substr(at, (end if end >= 0 else level_text.length()) - at)


func _work_loops() -> bool:
	for id in WORKERS:
		var path: String = WORKERS[id]
		if not kit.ok(FileAccess.file_exists(path), "%s exists" % path):
			continue
		var block := _npc_block(FileAccess.get_file_as_string(path), id)
		if not kit.ok(block != "", "%s stands in %s" % [id, path.get_file()]):
			continue
		kit.ok(block.contains("idle_anim = \"work_side\""), "%s plays its work loop in %s (idle_anim = \"work_side\")" % [id, path.get_file()])
		var meta = _json(CHAR + id + "/sheet.json")
		var row: Dictionary = (meta.get("anims", {}) as Dictionary).get("work_side", {}) if meta is Dictionary else {}
		kit.ok(int(row.get("frames", 0)) >= 6 and bool(row.get("loop", false)), "%s: work_side is a loop of >= 6 frames" % id)
		var r := SpriteRig.new()
		kit.mount(r)
		if kit.ok(r.load_character(id), "%s loads on the rig" % id):
			kit.ok(r.has_anim("work_side"), "%s: the rig has work_side" % id)
	return true


func _speakers() -> bool:
	var names = _json("res://data/locale/de_c4p2_characters.json")
	var strings: Dictionary = names.get("strings", {}) if names is Dictionary else {}
	for id in SPEAKERS + LIFE:
		kit.ok(str(strings.get("char.%s.name" % id, "")) != "", "%s: a German name in de_c4p2_characters.json" % id)
	var d = _json("res://data/v3/dialogue.json")
	var speakers := {}
	if kit.ok(d is Dictionary, "dialogue.json parses"):
		for c in d.get("conversations", []):
			if str(c.get("id", "")).substr(0, 7) in ["dlg_c4e", "dlg_c4f", "dlg_c4g", "dlg_c4h"]:
				for n in c.get("nodes", []):
					speakers[str(n.get("speaker", ""))] = true
	for id in SPEAKERS:
		kit.ok(speakers.has(id), "%s speaks in the part-2 dialogues" % id)
	for s in speakers:
		kit.ok(FileAccess.file_exists(CHAR + s + "/sheet.json"), "part-2 speaker %s has a sheet" % s)
		kit.ok(FileAccess.file_exists(CHAR + s + "/portrait.json") and FileAccess.file_exists(CHAR + s + "/portrait.png"),
			"part-2 speaker %s has a portrait" % s)
	var rx := RegEx.create_from_string("(?m)^char_id = \"([^\"]+)\"")
	var seen := {}
	for lvl in LEVELS:
		if not kit.ok(FileAccess.file_exists(lvl), "%s exists" % lvl):
			continue
		for m in rx.search_all(FileAccess.get_file_as_string(lvl)):
			seen[m.get_string(1)] = true
			kit.ok(FileAccess.file_exists(CHAR + m.get_string(1) + "/sheet.json"), "%s: char_id %s has a sheet" % [lvl.get_file(), m.get_string(1)])
	for id in SPEAKERS + LIFE:
		kit.ok(seen.has(id), "%s stands in a part-2 level shell" % id)
	return true


# ------------------------------------------------------------------------------------------------ sound
## RIFF header + chunk table of a WAV; "data_at" = byte offset of the PCM data.
static func _wav(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var b := f.get_buffer(f.get_length())
	var out := {"riff": b.slice(0, 4).get_string_from_ascii(), "wave": b.slice(8, 12).get_string_from_ascii(), "bytes": b}
	var i := 12
	while i + 8 <= b.size():
		var id := b.slice(i, i + 4).get_string_from_ascii()
		var sz := b.decode_u32(i + 4)
		if id == "fmt ":
			out["channels"] = b.decode_u16(i + 10)
			out["rate"] = b.decode_u32(i + 12)
			out["bits"] = b.decode_u16(i + 22)
		elif id == "data":
			out["data_at"] = i + 8
			out["data_size"] = sz
		elif id == "smpl":
			out["loop_start"] = b.decode_u32(i + 8 + 44)
			out["loop_end"] = b.decode_u32(i + 8 + 48)
		out[id] = true
		i += 8 + sz + (sz % 2)
	if out.has("data_size") and out.has("channels"):
		out["frames"] = int(out["data_size"]) / (2 * int(out["channels"]))
	return out


func _audio_files() -> bool:
	for n in SOUNDS:
		var spec: Array = SOUNDS[n]
		var path: String = spec[0] + n + ".wav"
		var w := _wav(path)
		if not kit.ok(not w.is_empty(), "%s exists" % n):
			continue
		kit.eq([w.get("riff"), w.get("wave"), w.get("rate"), w.get("bits"), w.get("channels")], ["RIFF", "WAVE", 44100, 16, spec[1]],
			"%s: 44.1 kHz / 16 bit / %d ch" % [n, spec[1]])
		kit.eq(w.has("smpl"), spec[2], "%s: loop chunk only on the loops" % n)
		if int(spec[3]) > 0:
			kit.eq(int(w.get("frames", 0)), int(spec[3]), "%s: length" % n)
		if spec[2]:
			kit.eq([int(w.get("loop_start", -1)), int(w.get("loop_end", -1))], [0, int(w.get("frames", 0))], "%s: loop spans the file" % n)
		if kit.ok(ResourceLoader.exists(path), "%s imported" % n):
			var s := load(path) as AudioStreamWAV
			if kit.ok(s != null, "%s loads as AudioStreamWAV" % n):
				kit.eq(s.loop_mode == AudioStreamWAV.LOOP_FORWARD, spec[2], "%s: imported loop mode" % n)
				kit.eq(s.format, AudioStreamWAV.FORMAT_16_BITS, "%s: lossless PCM import" % n)
	return true


## RMS / peak (dBFS) over a strided read, the seam (last vs first 50 ms) of loops, the tail of one-shots.
static func _levels(w: Dictionary) -> Dictionary:
	var b: PackedByteArray = w["bytes"]
	var at: int = w["data_at"]
	var ch: int = w["channels"]
	var frames: int = w["frames"]
	var stride := maxi(1, frames / 60000)
	var sum := 0.0
	var cnt := 0
	var peak := 0.0
	var f := 0
	while f < frames:
		for c in ch:
			var v := b.decode_s16(at + (f * ch + c) * 2) / 32768.0
			sum += v * v
			peak = maxf(peak, absf(v))
			cnt += 1
		f += stride
	var k := 0
	while k < frames:
		peak = maxf(peak, absf(b.decode_s16(at + k * ch * 2) / 32768.0))
		k += 7
	var win := 2205
	var e_last := 0.0
	var e_first := 0.0
	var step_seam := 0.0
	var steps := 0.0
	for c in ch:
		for i in win:
			var vl := b.decode_s16(at + ((frames - win + i) * ch + c) * 2) / 32768.0
			var vf := b.decode_s16(at + (i * ch + c) * 2) / 32768.0
			e_last += vl * vl
			e_first += vf * vf
		var a0 := b.decode_s16(at + ((frames - 1) * ch + c) * 2) / 32768.0
		var a1 := b.decode_s16(at + c * 2) / 32768.0
		step_seam = maxf(step_seam, absf(a1 - a0))
		for i in range(1, win):
			steps += absf(b.decode_s16(at + (i * ch + c) * 2) - b.decode_s16(at + ((i - 1) * ch + c) * 2)) / 32768.0
	var tail := 0.0
	for i in range(maxi(0, frames - 441), frames):
		for c in ch:
			tail = maxf(tail, absf(b.decode_s16(at + (i * ch + c) * 2) / 32768.0))
	return {"rms_db": linear_to_db(sqrt(sum / maxf(1.0, cnt))), "peak_db": linear_to_db(maxf(peak, 1e-9)),
		"seam_db": linear_to_db(sqrt(e_first / win) + 1e-12) - linear_to_db(sqrt(e_last / win) + 1e-12),
		"seam_step": step_seam, "mean_step": steps / maxf(1.0, (win - 1) * ch), "tail": tail}


func _audio_levels() -> bool:
	for n in SOUNDS:
		var spec: Array = SOUNDS[n]
		var w := _wav(spec[0] + n + ".wav")
		if w.is_empty() or not w.has("data_at"):
			continue
		var lv := _levels(w)
		var kind := "amb" if spec[0] == AMB else ("music" if spec[0] == MUS else ("loop" if spec[2] else "sfx"))
		var win: Array = WINDOW[kind]
		kit.ok(lv["rms_db"] >= win[0] - 0.7 and lv["rms_db"] <= win[1] + 0.7,
			"%s: RMS %.1f dBFS inside [%s, %s]" % [n, lv["rms_db"], win[0], win[1]])
		kit.ok(lv["peak_db"] <= win[2] + 0.05, "%s: peak %.1f dBFS <= %s" % [n, lv["peak_db"], win[2]])
		if spec[2]:
			kit.ok(absf(lv["seam_db"]) < 3.0, "%s: level continuous across the loop point (%.1f dB)" % [n, lv["seam_db"]])
			kit.ok(lv["seam_step"] < maxf(0.02, 8.0 * lv["mean_step"]), "%s: no click at the loop point (step %.4f, mean %.4f)"
				% [n, lv["seam_step"], lv["mean_step"]])
		else:
			kit.ok(lv["tail"] < 0.01, "%s: the one-shot ends in silence" % n)
	return true


func _registry() -> bool:
	# Audio loops the two scene loops and plays the closing cue once
	kit.ok("mus_c4p2_karsk" in AudioSvc.LOOPING_MUSIC and "mus_c4p2_berlin" in AudioSvc.LOOPING_MUSIC,
		"Audio.LOOPING_MUSIC loops the two part-2 scene loops")
	kit.ok(not ("mus_c4p2_clock" in AudioSvc.LOOPING_MUSIC), "mus_c4p2_clock is a one-shot cue (the tick stops)")
	# the stair steps: complete random-variant sets, the base id itself does not exist (Audio picks a variant)
	for base in VARIANT_SETS:
		kit.ok(not ResourceLoader.exists(SFX + base + ".wav"), "%s: only variants (no bare file shadows them)" % base)
		for i in range(1, int(VARIANT_SETS[base]) + 1):
			kit.ok(ResourceLoader.exists(SFX + "%s_%d.wav" % [base, i]), "%s_%d exists" % [base, i])
		kit.ok(not ResourceLoader.exists(SFX + "%s_%d.wav" % [base, int(VARIANT_SETS[base]) + 1]), "%s: exactly %d variants" % [base, VARIANT_SETS[base]])
	# the UIs ask through Kit.ui_sound_first -> Audio.has_sound: every puzzle cue resolves (a file or its variants)
	var au: Node = Kit.root().get_node_or_null("Audio")
	if au == null:
		au = kit.mount(AudioSvc.new())
	for id in PUZZLE_CUES:
		kit.ok(au.has_sound(id), "Audio.has_sound(%s)" % id)
	# what the generator builds is what SOUNDS checks (a builder is a file or a variant set); no other one-shot is
	# named like a random variant (Audio.sfx would mix them up)
	var gen := FileAccess.get_file_as_string(GEN)
	var built: Array = []
	for m in RegEx.create_from_string("'(c4p2_[a-z0-9_]+)': \\('sfx'").search_all(gen):
		built.append(m.get_string(1))
	kit.ok(built.size() >= 10, "the generator builds its one-shots (%s)" % [built])
	for n in built:
		kit.ok(SOUNDS.has(n) or VARIANT_SETS.has(n), "%s is a checked one-shot (SOUNDS / VARIANT_SETS)" % n)
		kit.ok(PUZZLE_CUES.has(n), "%s has a place in a puzzle (PUZZLE_CUES)" % n)
	var variant_rx := RegEx.create_from_string("_\\d+$")
	for key in SOUNDS:
		var n: String = key
		if SOUNDS[n][0] != SFX:
			continue
		var base: String = n
		for vs in VARIANT_SETS:
			var v: String = vs
			if n.begins_with(v + "_") and n.substr(v.length() + 1).is_valid_int():
				base = v
		kit.ok(base in built, "%s: SOUNDS lists only what the generator builds" % n)
		kit.ok(base != n or variant_rx.search(n) == null, "%s: not named like a random variant" % n)
	return true


## The generator's LS_C4P2_Clock times: {"CLOCK_SHOTS": [...], "CLOCK_STOP": [x], "CLOCK_LEN": [x]}
static func _gen_times() -> Dictionary:
	var out := {}
	var rx := RegEx.create_from_string("(?m)^(CLOCK_SHOTS|CLOCK_STOP|CLOCK_LEN) = \\(?([0-9., ]+)\\)?")
	for m in rx.search_all(FileAccess.get_file_as_string(GEN)):
		var vals: Array = []
		for v in m.get_string(2).split(",", false):
			if v.strip_edges() != "":
				vals.append(float(v))
		out[m.get_string(1)] = vals
	return out


## RMS (dBFS, both channels) of the window [t0, t1) s; diff = of the first difference (a 6 dB/oct high-pass: the
## clock's tick against the low drone and the piano, the way the ear separates them).
static func _win_db(w: Dictionary, t0: float, t1: float, diff := false) -> float:
	var b: PackedByteArray = w["bytes"]
	var at: int = w["data_at"]
	var ch: int = w["channels"]
	var f0 := clampi(int(t0 * 44100.0), 1, int(w["frames"]))
	var f1 := clampi(int(t1 * 44100.0), f0, int(w["frames"]))
	var sum := 0.0
	for f in range(f0, f1):
		for c in ch:
			var v := b.decode_s16(at + (f * ch + c) * 2) / 32768.0
			if diff:
				v -= b.decode_s16(at + ((f - 1) * ch + c) * 2) / 32768.0
			sum += v * v
	return linear_to_db(sqrt(sum / maxf(1.0, float((f1 - f0) * ch))) + 1e-9)


func _clock() -> bool:
	var g := _gen_times()
	var shots: Array = g.get("CLOCK_SHOTS", [])
	var stop: float = (g.get("CLOCK_STOP", [0.0]) as Array)[0]
	kit.eq(shots.size(), 6, "c4p2_audio.py gives CLOCK_SHOTS (k1..k5 + end)")
	# the registered film: k1..k5 with their durations (data/v3/cinematics.json, C4P2_DESIGN 2.9)
	var cin = _json("res://data/v3/cinematics.json")
	var starts: Array = []
	if kit.ok(cin is Dictionary, "cinematics.json parses"):
		for s in cin.get("sequences", []):
			if str(s.get("id", "")) == "LS_C4P2_Clock":
				var t := 0.0
				for sh in s.get("shots", []):
					starts.append(t)
					t += float(sh.get("duration_s", 0.0))
				starts.append(t)
	kit.eq(starts, shots, "the cue's shot times are the registered shots of LS_C4P2_Clock")
	if shots.size() == 6:
		kit.eq(stop, float(shots[4]), "the tick stops on k5")
	var w := _wav(MUS + "mus_c4p2_clock.wav")
	if not kit.ok(w.has("data_at"), "mus_c4p2_clock readable"):
		return true
	# a tick on every second from k1 (an onset: louder than the 100 ms before it), none where the tick stops
	for i in range(1, int(stop)):
		var on := _win_db(w, i - 0.002, i + 0.04, true)
		var before := _win_db(w, i - 0.12, i - 0.02, true)
		kit.ok(on > before + 4.0, "the tick at %d s (%.1f vs %.1f dB, high band)" % [i, on, before])
	var at_stop := _win_db(w, stop - 0.002, stop + 0.04, true)
	var before_stop := _win_db(w, stop - 0.12, stop - 0.02, true)
	kit.ok(at_stop < before_stop + 1.0, "no tick at %.0f s: the clock has stopped (%.1f vs %.1f dB)" % [stop, at_stop, before_stop])
	for t in [stop + 1.0, stop + 2.0]:
		kit.ok(_win_db(w, t - 0.002, t + 0.04, true) < _win_db(w, t - 0.12, t - 0.02, true) + 1.0, "no tick at %.0f s" % t)
	kit.ok(_win_db(w, stop + 2.8, float(shots[5]) if shots.size() == 6 else 24.0) < -60.0, "k5 ends in silence")
	return true


# ------------------------------------------------------------------------------------------------ wiring
func _wiring() -> bool:
	for lvl in LEVELS:
		if not kit.ok(FileAccess.file_exists(lvl), "%s exists" % lvl):
			continue
		var src := FileAccess.get_file_as_string(lvl)
		for key in ["ambience", "music"]:
			var m := RegEx.create_from_string("(?m)^%s = \"([^\"]*)\"" % key).search(src)
			if not kit.ok(m != null and m.get_string(1) != "", "%s: has a %s" % [lvl.get_file(), key]):
				continue
			var dir := AMB if key == "ambience" else MUS
			kit.ok(ResourceLoader.exists(dir + m.get_string(1) + ".wav"), "%s: %s %s exists" % [lvl.get_file(), key, m.get_string(1)])
			kit.ok(m.get_string(1) in LEVELS[lvl], "%s: %s is this chapter's (%s)" % [lvl.get_file(), key, m.get_string(1)])
	var c4p2 = _json("res://data/chapters/c4p2.json")
	if kit.ok(c4p2 is Dictionary, "c4p2.json parses"):
		var sw: Dictionary = c4p2.get("switches", {})
		for sid in SWITCHES:
			var st: Dictionary = sw.get(sid, {})
			kit.eq([str(st.get("ambience", "")), str(st.get("music", ""))], SWITCHES[sid], "%s plays the contract's ambience and music" % sid)
			kit.ok(ResourceLoader.exists(AMB + str(st.get("ambience", "")) + ".wav"), "%s: switch ambience exists" % sid)
			kit.ok(ResourceLoader.exists(MUS + str(st.get("music", "")) + ".wav"), "%s: switch music exists" % sid)
		var looks = c4p2.get("looks", {})
		if looks is Dictionary:
			for sid in looks:
				for who in looks[sid]:
					kit.ok(FileAccess.file_exists(CHAR + str(looks[sid][who]) + "/sheet.json"), "looks %s/%s has a sheet" % [sid, who])
	# every c4p2 / chapter sound a part-2 film or puzzle script names exists (sfx variants `id_1` count)
	var rx := RegEx.create_from_string("\"((?:c4p2_|mus_c4p2_|amb_karsk_depot|amb_karsk_platform|amb_berlin_station|amb_berlin_courtyard)[a-z0-9_]*)\"")
	for path in _scripts():
		for m in rx.search_all(FileAccess.get_file_as_string(path)):
			var id := m.get_string(1)
			if id.begins_with("c4p2_") and not SOUNDS.has(id) and not VARIANT_SETS.has(id) and not ResourceLoader.exists(SFX + id + ".wav"):
				continue   # not a sound id of ours (a node / texture / locale key of the other streams)
			var found := ResourceLoader.exists(SFX + id + ".wav") or ResourceLoader.exists(SFX + id + "_1.wav") \
				or ResourceLoader.exists(AMB + id + ".wav") or ResourceLoader.exists(MUS + id + ".wav")
			kit.ok(found, "%s names %s: it exists" % [path.get_file(), id])
	return true


## The .gd files of the part-2 films and of the puzzle UIs that exist so far.
static func _scripts() -> Array:
	var out: Array = []
	for d in CINE_DIRS:
		var dir := DirAccess.open(d)
		if dir == null:
			continue
		for f in dir.get_files():
			if f.ends_with(".gd"):
				out.append(d + f)
	for p in PUZZLE_SCRIPTS:
		if FileAccess.file_exists(p):
			out.append(p)
	return out


## What the other streams wire this round: reported while missing (the lead wires them at integration).
func _pending() -> bool:
	var pend: Array = []
	var puzzle_src := ""
	for p in PUZZLE_SCRIPTS:
		if FileAccess.file_exists(p):
			puzzle_src += FileAccess.get_file_as_string(p) + "\n"
	for id in PUZZLE_CUES:
		if not puzzle_src.contains("\"%s\"" % id):
			pend.append("%s calls %s" % [PUZZLE_CUES[id], id])
	var clock_src := ""
	var d := DirAccess.open("res://scenes/cinematics/ch4p2_clock/")
	if d != null:
		for f in d.get_files():
			if f.ends_with(".gd"):
				clock_src += FileAccess.get_file_as_string("res://scenes/cinematics/ch4p2_clock/" + f)
	if not clock_src.contains("\"mus_c4p2_clock\""):
		pend.append("LS_C4P2_Clock plays mus_c4p2_clock from t = 0")
	for p in pend:
		print("      pending (round 10): " + str(p))
	kit.ok(true, "pending report printed (%d)" % pend.size())
	return true
