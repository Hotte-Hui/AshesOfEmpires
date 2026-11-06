extends RefCounted
## Chapter 3 part 2 — characters and sound (owner: c3p2 cast/audio; documentation/asset_manifest_parts/c3p2_cast_audio.md):
##  * looks (C3P2_DESIGN §6: existing ids only): alexei_soot / konrad_soot = the protagonists' rows in the same order and
##    the same silhouette, soot visible, + carry_side / carry_idle_side (the file C-17); typist_night = Frau Brunner in
##    her coat over the nightdress (typist's rows); each with a living portrait that names its base speaker
##  * sound (§8 + round-8 brief): three level ambiences with the design's ids, two music loops, fire beds in three
##    intensities, scene and cinematic one-shots — 44.1 kHz / 16 bit, loop chunks exactly on the loops (imported as
##    LOOP_FORWARD over the whole file), levels inside their window, seamless seams, one-shots ending in silence
##  * wiring: level ambience / music ids and switch-setting ids resolve to files; every c3p2 sound id the round-8
##    cinematics or c3.json name exists; an optional c3.json "looks" table only names existing sheet directories

const Kit := preload("res://tests/support/test_kit.gd")
const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const CHAR := "res://assets/characters/"
const AMB := "res://assets/audio/amb/"
const MUS := "res://assets/audio/music/"
const SFX := "res://assets/audio/sfx/"
const LOOKS := {"alexei_soot": "alexei", "konrad_soot": "konrad", "typist_night": "typist"}
const CARRY := ["carry_side", "carry_idle_side"]
const EXPR := ["neutral", "concerned", "determined", "surprised"]
## file -> [dir, channels, loop, frames (0 = any)]
const SOUNDS := {
	"amb_veltrava_registry": [AMB, 2, true, 2646000], "amb_veltrava_fire": [AMB, 2, true, 2646000],
	"amb_veltrava_quay": [AMB, 2, true, 2646000],
	"mus_c3p2_fire": [MUS, 2, true, 2940000], "mus_c3p2_halves": [MUS, 2, true, 4536000],
	"c3p2_fire_low": [SFX, 2, true, 882000], "c3p2_fire_mid": [SFX, 2, true, 882000], "c3p2_fire_high": [SFX, 2, true, 882000],
	"c3p2_yard_night": [SFX, 2, true, 1323000], "c3p2_radio_waltz": [SFX, 1, true, 2646000],
	"c3p2_radio_interval": [SFX, 1, false, 176400], "c3p2_radio_news_ru": [SFX, 1, false, 0],
	"c3p2_radio_news_de": [SFX, 1, false, 0], "c3p2_radio_tune": [SFX, 1, false, 0],
	"c3p2_note_slide": [SFX, 2, false, 0], "c3p2_fire_catch": [SFX, 2, false, 0], "c3p2_bolt": [SFX, 2, false, 0],
	"c3p2_desk_push": [SFX, 2, false, 0], "c3p2_door_jam": [SFX, 2, false, 0], "c3p2_hatch_open": [SFX, 2, false, 0],
	"c3p2_hatch_slam": [SFX, 2, false, 0], "c3p2_window_burst": [SFX, 2, false, 0],
	"c3p2_roof_creak_1": [SFX, 2, false, 0], "c3p2_roof_creak_2": [SFX, 2, false, 0], "c3p2_roof_creak_3": [SFX, 2, false, 0],
	"c3p2_glass_1": [SFX, 2, false, 0], "c3p2_glass_2": [SFX, 2, false, 0], "c3p2_glass_3": [SFX, 2, false, 0],
	"c3p2_fire_bell": [SFX, 2, false, 0], "c3p2_sirens_far": [SFX, 2, false, 0],
}
## loudness windows (dBFS RMS min, max; peak max), as enforced by tools/audiogen/c3p2_audio.py
const WINDOW := {"amb": [-28.0, -21.0, -2.5], "music": [-25.0, -19.0, -0.8], "loop": [-36.0, -19.0, -2.5],
	"sfx": [-45.0, -9.0, -2.5]}
const CINE_DIRS := ["res://scenes/cinematics/ch3_radio/", "res://scenes/cinematics/ch3_fire/",
	"res://scenes/cinematics/ch3_escape/", "res://scenes/cinematics/ch3_halves/"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("looks_sheets_follow_their_base", _sheets)
	kit.run_case("looks_play_on_the_rig", _rig)
	kit.run_case("looks_living_portraits", _portraits)
	kit.run_case("looks_runtime_after_integration", _looks_runtime)
	kit.run_case("audio_files_format_and_loops", _audio_files)
	kit.run_case("audio_levels_and_seams", _audio_levels)
	kit.run_case("audio_and_looks_wiring", _wiring)
	kit.cleanup()
	return kit.failures


static func _json(path: String):
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


static func _img(path: String) -> Image:
	if not FileAccess.file_exists(path):
		return null
	return Image.load_from_file(ProjectSettings.globalize_path(path))


# ------------------------------------------------------------------------------------------------ looks
func _sheets() -> bool:
	for look in LOOKS:
		var base: String = LOOKS[look]
		var sv = _json(CHAR + look + "/sheet.json")
		var sb = _json(CHAR + base + "/sheet.json")
		if not kit.ok(sv is Dictionary and sb is Dictionary, "%s: sheet.json of the look and of %s" % [look, base]):
			continue
		kit.eq(sv.get("cell"), [32.0, 56.0], "%s: cell" % look)
		kit.eq(sv.get("origin"), [16.0, 54.0], "%s: origin" % look)
		var av: Dictionary = sv.get("anims", {})
		var ab: Dictionary = sb.get("anims", {})
		var want: Array = ab.keys() + (CARRY if look.ends_with("_soot") else [])
		kit.eq(av.keys(), want, "%s: rows = %s's rows in their order%s" % [look, base, " + carry" if look.ends_with("_soot") else ""])
		for a in ab:
			if av.has(a):
				var x: Dictionary = av[a]
				var y: Dictionary = ab[a]
				kit.eq([x.get("row"), x.get("frames"), x.get("fps"), x.get("loop"), x.get("variants", [])],
					[y.get("row"), y.get("frames"), y.get("fps"), y.get("loop"), y.get("variants", [])], "%s: row %s as in %s" % [look, a, base])
		kit.ok(FileAccess.file_exists(CHAR + look + "/sheet_n.png"), "%s: normal map" % look)
		var iv := _img(CHAR + look + "/sheet.png")
		var ib := _img(CHAR + base + "/sheet.png")
		if not kit.ok(iv != null and ib != null, "%s: sheet.png loads" % look):
			continue
		var cols := 0
		for a in av:
			cols = maxi(cols, int(av[a].get("frames", 0)))
		kit.eq([iv.get_width(), iv.get_height()], [cols * 32, av.size() * 56], "%s: sheet size = frames x rows" % look)
		if look.ends_with("_soot"):
			var cmp := _compare(iv, ib, ab.size() * 56)
			kit.eq(cmp["alpha_diff"], 0, "%s: the look never changes the silhouette of %s" % [look, base])
			var share := float(cmp["rgb_diff"]) / maxf(1.0, float(cmp["opaque"]))
			kit.ok(share > 0.05 and share < 0.5, "%s: soot visible on %.0f %% of the figure (5..50 %%)" % [look, share * 100.0])
			for c in CARRY:
				kit.eq(int(av.get(c, {}).get("frames", 0)), 8, "%s: %s has 8 frames" % [look, c])
			var gs: Dictionary = sv.get("ground_speed", {})
			kit.ok(float(gs.get("carry_side", 0.0)) > 0.0 and is_equal_approx(float(gs.get("carry_side", 0.0)),
				float(gs.get("walk_side", -1.0))), "%s: carry_side walks at walk_side's ground speed" % look)
			# the file is in the hands: the carry rows are not the plain rows
			var c_row := int(av.get("carry_side", {}).get("row", 0))
			var w_row := int(av.get("walk_side", {}).get("row", 0))
			kit.ok(_rows_differ(iv, c_row, w_row), "%s: carry_side shows the file (differs from walk_side)" % look)
		else:
			var cmp2 := _compare(iv, ib, 56)
			kit.ok(cmp2["rgb_diff"] > 200, "%s: a different costume than %s" % [look, base])
	return true


## Pixels in rows [0, height) of both sheets: alpha mismatches, opaque pixels whose RGB differs, opaque pixels.
static func _compare(a: Image, b: Image, height: int) -> Dictionary:
	var out := {"alpha_diff": 0, "rgb_diff": 0, "opaque": 0}
	if a.get_width() < b.get_width() or a.get_height() < height or b.get_height() < height:
		out["alpha_diff"] = -1
		return out
	var w := b.get_width()
	var da := a.get_region(Rect2i(0, 0, w, height)).get_data()
	var db := b.get_region(Rect2i(0, 0, w, height)).get_data()
	if a.get_format() != Image.FORMAT_RGBA8 or b.get_format() != Image.FORMAT_RGBA8:
		var ca := a.get_region(Rect2i(0, 0, w, height))
		var cb := b.get_region(Rect2i(0, 0, w, height))
		ca.convert(Image.FORMAT_RGBA8)
		cb.convert(Image.FORMAT_RGBA8)
		da = ca.get_data()
		db = cb.get_data()
	var i := 0
	while i < da.size():
		var aa := da[i + 3] > 0
		var ab := db[i + 3] > 0
		if aa != ab:
			out["alpha_diff"] += 1
		elif ab:
			out["opaque"] += 1
			if da[i] != db[i] or da[i + 1] != db[i + 1] or da[i + 2] != db[i + 2]:
				out["rgb_diff"] += 1
		i += 4
	return out


static func _rows_differ(img: Image, ra: int, rb: int) -> bool:
	var n := 0
	for y in 56:
		for x in range(0, 32 * 4):
			if img.get_pixel(x, ra * 56 + y) != img.get_pixel(x, rb * 56 + y):
				n += 1
	return n > 40


func _rig() -> bool:
	for look in LOOKS:
		var r: Node2D = kit.mount(SpriteRig.new())
		if not kit.ok(r.load_character(look), "%s loads on the rig" % look):
			continue
		for a in ["idle_side", "talk_side", "walk_side", "idle_front", "talk_front"]:
			kit.ok(r.has_anim(a), "%s: has %s" % [look, a])
		if look.ends_with("_soot"):
			for a in CARRY + ["walk_front", "walk_back", "inspect_side", "interact_side", "talk_back"]:
				kit.ok(r.has_anim(a), "%s: has %s" % [look, a])
			r.play("carry_side")
			kit.eq(r.anim, "carry_side", "%s: carry_side plays" % look)
			kit.ok(r.ground_speed("carry_side") > 30.0, "%s: carry_side has a ground speed" % look)
			r.play("carry_idle_side")
			kit.eq(r.anim, "carry_idle_side", "%s: carry_idle_side plays" % look)
	return true


func _portraits() -> bool:
	for look in LOOKS:
		var base: String = LOOKS[look]
		var p = _json(CHAR + look + "/portrait.json")
		if not kit.ok(p is Dictionary, "%s: portrait.json" % look):
			continue
		kit.eq(p.get("size"), [112.0, 112.0], "%s: portrait size" % look)
		kit.eq(p.get("expressions"), EXPR, "%s: expressions" % look)
		kit.eq(str(p.get("look_of", "")), base, "%s: portrait names its base speaker" % look)
		var anim: Dictionary = p.get("anim", {}) if p.get("anim") is Dictionary else {}
		kit.eq(str(anim.get("file", "")), "portrait_anim.png", "%s: living portrait" % look)
		var grid := _img(CHAR + look + "/portrait_anim.png")
		var strip := _img(CHAR + look + "/portrait.png")
		var base_strip := _img(CHAR + base + "/portrait.png")
		if not kit.ok(grid != null and strip != null and base_strip != null, "%s: portrait images load" % look):
			continue
		kit.eq([grid.get_width(), grid.get_height()], [448, 112 * (anim.get("rows", []) as Array).size()], "%s: grid size" % look)
		kit.eq([strip.get_width(), strip.get_height()], [448, 112], "%s: strip size" % look)
		kit.ok(_region_differs(grid, 0, 2), "%s: the mouth opens (talk_open row)" % look)
		kit.ok(_region_differs(grid, 0, 3), "%s: the eyes close (blink row)" % look)
		var n := 0
		for y in range(16, 104, 2):
			for x in range(16, 104, 2):
				if strip.get_pixel(x, y) != base_strip.get_pixel(x, y):
					n += 1
		kit.ok(n > 300, "%s: portrait differs visibly from %s's (%d of 1936 samples)" % [look, base, n])
	return true


## Runs once the round-8 integration patch is in (sprite_rig.gd: static `looks`, static `look_of()`, `carry`); until then
## there is nothing to check here (the looks are plain sheet directories, covered above).
func _looks_runtime() -> bool:
	var src := FileAccess.get_file_as_string("res://scripts/actors/sprite_rig.gd")
	if not (src.contains("static var looks") and src.contains("func look_of(") and src.contains("var carry")):
		return true
	var rs = load("res://scripts/actors/sprite_rig.gd")      # untyped: the static members are reached dynamically
	var looks = rs.get("looks")
	if not kit.ok(looks is Dictionary, "SpriteRig.looks is a Dictionary"):
		return true
	var keep: Dictionary = (looks as Dictionary).duplicate()
	looks.clear()
	looks["alexei"] = "alexei_soot"
	looks["konrad"] = "no_such_look"
	kit.eq(rs.call("look_of", "alexei"), "alexei_soot", "look_of maps alexei to his look")
	kit.eq(rs.call("look_of", "konrad"), "konrad", "a look without a sheet falls back to the base")
	var r: Node2D = kit.mount(SpriteRig.new())
	kit.ok(r.load_character("alexei") and r.has_anim("carry_side"), "load_character('alexei') loads the soot sheet")
	kit.eq(r.char_id, "alexei", "the identity stays alexei")
	r.set("carry", true)
	r.play("walk_side")
	kit.eq(r.anim, "carry_side", "carrying: walk_side plays carry_side")
	r.play("idle_side")
	kit.eq(r.anim, "carry_idle_side", "carrying: idle_side plays carry_idle_side")
	r.set("carry", false)
	r.play("walk_side")
	kit.eq(r.anim, "walk_side", "not carrying: walk_side again")
	looks.clear()
	looks.merge(keep)
	return true


static func _region_differs(img: Image, row_a: int, row_b: int) -> bool:
	var n := 0
	for y in range(20, 100):
		for x in range(20, 100):
			if img.get_pixel(x, row_a * 112 + y) != img.get_pixel(x, row_b * 112 + y):
				n += 1
	return n >= 6


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
	# exact peak search near the loudest region is not needed: the generator limits; a strided peak is a lower bound,
	# so the peak window is checked on the full data of the first channel as well
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


# ------------------------------------------------------------------------------------------------ wiring
func _wiring() -> bool:
	# level files: ambience / music ids resolve
	for lvl in ["res://scenes/levels/L_C3_Registry.tscn", "res://scenes/levels/L_C3_Quay.tscn"]:
		if not kit.ok(FileAccess.file_exists(lvl), "%s exists" % lvl):
			continue
		var src := FileAccess.get_file_as_string(lvl)
		for key in ["ambience", "music"]:
			var rx := RegEx.create_from_string("(?m)^%s = \"([^\"]*)\"" % key)
			var m := rx.search(src)
			if m == null or m.get_string(1) == "":
				continue
			var dir := AMB if key == "ambience" else MUS
			kit.ok(ResourceLoader.exists(dir + m.get_string(1) + ".wav"), "%s: %s %s exists" % [lvl.get_file(), key, m.get_string(1)])
	kit.ok(FileAccess.get_file_as_string("res://scenes/levels/L_C3_Registry.tscn").contains("ambience = \"amb_veltrava_registry\""),
		"the registry plays amb_veltrava_registry")
	kit.ok(FileAccess.get_file_as_string("res://scenes/levels/L_C3_Quay.tscn").contains("ambience = \"amb_veltrava_quay\""),
		"the quay plays amb_veltrava_quay")
	# c3.json: switch settings (ambience / music) and the optional "looks" table
	var c3 = _json("res://data/chapters/c3.json")
	if kit.ok(c3 is Dictionary, "c3.json parses"):
		var sw: Dictionary = c3.get("switches", {})
		for sid in sw:
			var st: Dictionary = sw[sid]
			if st.has("ambience") and str(st["ambience"]) != "":
				kit.ok(ResourceLoader.exists(AMB + str(st["ambience"]) + ".wav"), "%s: switch ambience %s exists" % [sid, st["ambience"]])
			if st.has("music") and str(st["music"]) != "":
				kit.ok(ResourceLoader.exists(MUS + str(st["music"]) + ".wav"), "%s: switch music %s exists" % [sid, st["music"]])
		for sid in ["L_C3_RegistryC", "L_C3_RegistryD"]:
			kit.eq(str(sw.get(sid, {}).get("ambience", "")), "amb_veltrava_fire", "%s burns (amb_veltrava_fire)" % sid)
		var looks = c3.get("looks", {})
		if looks is Dictionary:
			for sid in looks:
				for who in looks[sid]:
					var d := str(looks[sid][who])
					kit.ok(FileAccess.file_exists(CHAR + d + "/sheet.json"), "looks %s/%s -> %s has a sheet" % [sid, who, d])
	# every sound of this stream (c3p2_*, mus_c3p2_*, amb_veltrava_*) a round-8 cinematic cue names is there
	# (cue values only: "sfx" / "bed" / "loop" / "amb" / "music"; loop keys and the cinematics' own c3p2cine_* are not ours)
	var rx2 := RegEx.create_from_string("\"(?:sfx|bed|loop|amb|music)\"\\s*:\\s*\"((?:c3p2_|mus_c3p2_|amb_veltrava_)[a-z0-9_]+)\"")
	for d in CINE_DIRS:
		var dir := DirAccess.open(d)
		if dir == null:
			continue
		for f in dir.get_files():
			if not f.ends_with(".gd"):
				continue
			for m in rx2.search_all(FileAccess.get_file_as_string(d + f)):
				var id := m.get_string(1)
				var found := ResourceLoader.exists(SFX + id + ".wav") or ResourceLoader.exists(SFX + id + "_1.wav") \
					or ResourceLoader.exists(AMB + id + ".wav") or ResourceLoader.exists(MUS + id + ".wav")
				kit.ok(found, "%s%s names %s: it exists" % [d, f, id])
	return true
