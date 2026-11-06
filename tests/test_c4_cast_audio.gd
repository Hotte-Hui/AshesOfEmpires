extends RefCounted
## Chapter 4 part 1 — cast and sound (owner: cast-audio; documentation/asset_manifest_parts/c4_cast_audio.md):
##  * the new speakers of C4_DESIGN §5 (lev, marta, registrar): sheets on the round-2 rig (the NPC rows, 8-frame idle
##    and talk, blink / glance / gesture variants, front views, an NPC walking speed), normal maps, they load and play
##    on SpriteRig; living portraits (4 expressions x 6 states: the mouth opens, the eyes close, the expressions
##    differ); names in de_c4_characters.json; individual silhouettes (no twin of each other or of the existing cast)
##    and individual faces
##  * every speaker of the C4 dialogues and every char_id of the two C4 level shells has a sheet and a portrait
##  * sound (§8): the four level ambiences with the contract's ids, three music loops, the cinematic cues —
##    44.1 kHz / 16 bit, loop chunks exactly on the loops (imported LOOP_FORWARD over the whole file, lossless), levels
##    inside the round-8 windows, seamless seams, one-shots ending in silence; no c4 sfx id looks like a random
##    variant (`name_1`), so Audio.sfx() never mixes them up
##  * wiring: the level shells and the c4.json switches name existing files; every c4 sound a C4 cinematic cue names
##    exists (cinematics that do not exist yet are skipped)

const Kit := preload("res://tests/support/test_kit.gd")
const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const CHAR := "res://assets/characters/"
const AMB := "res://assets/audio/amb/"
const MUS := "res://assets/audio/music/"
const SFX := "res://assets/audio/sfx/"
const CAST := ["lev", "marta", "registrar"]
const ROWS := ["idle_side", "walk_side", "idle_front", "talk_side", "blink_side", "look_side", "gesture_side",
	"blink_front", "talk_front"]
const EXTRA_ROWS := {"registrar": ["work_side"]}
const EXPR := ["neutral", "concerned", "determined", "surprised"]
## existing figures the new silhouettes must not copy (idle_side frame 0)
const REFERENCE := ["alexei", "konrad", "emil", "clerk", "guard", "conductor", "kessler", "typist", "berlin_mother",
	"berlin_father", "porter", "librarian", "worker_b", "border_officer", "babushka", "irina"]
## file -> [dir, channels, loop, frames (0 = any)]
const SOUNDS := {
	"amb_karsk_cellar": [AMB, 2, true, 2646000], "amb_karsk_tunnel": [AMB, 2, true, 2646000],
	"amb_berlin_loop": [AMB, 2, true, 2646000], "amb_berlin_annex": [AMB, 2, true, 2646000],
	"mus_c4_karsk": [MUS, 2, true, 3136000], "mus_c4_berlin": [MUS, 2, true, 2352000],
	"mus_c4_voices": [MUS, 2, true, 2116800],
	"c4_stencil_brush": [SFX, 2, false, 0], "c4_card_tear": [SFX, 2, false, 0], "c4_stamp_accept": [SFX, 2, false, 0],
	"c4_stamp_dispatch": [SFX, 2, false, 0], "c4_bell_once": [SFX, 2, false, 0], "c4_bell_twice": [SFX, 2, false, 0],
	"c4_train_overhead": [SFX, 2, false, 0], "c4_lamp_out": [SFX, 2, false, 0],
}
## loudness windows (dBFS RMS min, max; peak max), as enforced by tools/audiogen/c4_audio.py (the round-8 windows)
const WINDOW := {"amb": [-28.0, -21.0, -2.5], "music": [-25.0, -19.0, -0.8], "loop": [-36.0, -19.0, -2.5],
	"sfx": [-45.0, -9.0, -2.5]}
const LEVELS := ["res://scenes/levels/L_C4_Tunnels.tscn", "res://scenes/levels/L_C4_Annex.tscn"]
const CINE_DIRS := ["res://scenes/cinematics/ch4_homeward/", "res://scenes/cinematics/ch4_number/",
	"res://scenes/cinematics/ch4_card/", "res://scenes/cinematics/ch4_stamp/", "res://scenes/cinematics/ch4_voices/"]

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("cast_sheets_contract", _sheets)
	kit.run_case("cast_plays_on_the_rig", _rig)
	kit.run_case("cast_living_portraits", _portraits)
	kit.run_case("cast_individual_silhouettes_and_faces", _individual)
	kit.run_case("cast_names_and_speakers", _speakers)
	kit.run_case("audio_files_format_and_loops", _audio_files)
	kit.run_case("audio_levels_and_seams", _audio_levels)
	kit.run_case("audio_wiring", _wiring)
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


# ------------------------------------------------------------------------------------------------ cast
func _sheets() -> bool:
	for id in CAST:
		var meta = _json(CHAR + id + "/sheet.json")
		if not kit.ok(meta is Dictionary, "%s: sheet.json" % id):
			continue
		kit.eq(meta.get("cell"), [32.0, 56.0], "%s: cell" % id)
		kit.eq(meta.get("origin"), [16.0, 54.0], "%s: origin (feet)" % id)
		kit.eq(str(meta.get("facing", "")), "right", "%s: drawn facing right" % id)
		var anims: Dictionary = meta.get("anims", {})
		kit.eq(anims.keys(), ROWS + EXTRA_ROWS.get(id, []), "%s: the NPC rows in their order" % id)
		for a in ["idle_side", "talk_side", "idle_front", "talk_front", "walk_side"]:
			kit.eq(int(anims.get(a, {}).get("frames", 0)), 8, "%s: %s has 8 frames (round-2 rhythm)" % [id, a])
		var vars: Array = anims.get("idle_side", {}).get("variants", [])
		for v in ["blink_side", "look_side", "gesture_side"]:
			kit.ok(v in vars, "%s: %s is an idle variant" % [id, v])
			kit.ok(not bool(anims.get(v, {}).get("loop", true)), "%s: the variant %s does not loop" % [id, v])
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
		# the feet stand on the origin row in idle frame 0, the figure is not clipped at the cell top
		var feet := -1
		var top := 56
		for y in 56:
			for x in 32:
				if img.get_pixel(x, y).a > 0.0:
					feet = maxi(feet, y)
					top = mini(top, y)
		kit.eq(feet, 54, "%s: feet on the origin row" % id)
		kit.ok(top >= 4 and 54 - top + 1 >= 40, "%s: figure height %d px (adult, not clipped)" % [id, 54 - top + 1])
	return true


func _rig() -> bool:
	for id in CAST:
		var r: Node2D = kit.mount(SpriteRig.new())
		if not kit.ok(r.load_character(id), "%s loads on the rig" % id):
			continue
		for a in ROWS + EXTRA_ROWS.get(id, []):
			kit.ok(r.has_anim(a), "%s: has %s" % [id, a])
		r.play("talk_side")
		kit.eq(r.anim, "talk_side", "%s: talk_side plays" % id)
		r.play("idle_front")
		kit.eq(r.anim, "idle_front", "%s: idle_front plays" % id)
		kit.ok(r.ground_speed("walk_side") > 10.0, "%s: walk_side has a ground speed" % id)
	return true


func _portraits() -> bool:
	for id in CAST:
		var p = _json(CHAR + id + "/portrait.json")
		if not kit.ok(p is Dictionary, "%s: portrait.json" % id):
			continue
		kit.eq(p.get("size"), [112.0, 112.0], "%s: portrait size" % id)
		kit.eq(p.get("expressions"), EXPR, "%s: the four expressions" % id)
		var anim: Dictionary = p.get("anim", {}) if p.get("anim") is Dictionary else {}
		kit.eq(str(anim.get("file", "")), "portrait_anim.png", "%s: living portrait" % id)
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
	var sil := {}
	for id in CAST + REFERENCE:
		var s := _silhouette(id)
		if s.size() > 0:
			sil[id] = s
	for a in CAST:
		if not kit.ok(sil.has(a), "%s: silhouette" % a):
			continue
		for b in sil:
			if a == b or (b in CAST and CAST.find(b) < CAST.find(a)):
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
	# faces: the neutral portraits of the three differ from each other and from the existing Berlin / Karsk speakers
	var faces := {}
	for id in CAST + ["konrad", "alexei", "emil", "clerk", "kessler", "typist", "berlin_mother"]:
		var im := _img(CHAR + id + "/portrait.png")
		if im != null:
			faces[id] = im
	for a in CAST:
		if not faces.has(a):
			continue
		for b in faces:
			if a == b or (b in CAST and CAST.find(b) < CAST.find(a)):
				continue
			var n := 0
			for y in range(16, 104, 2):
				for x in range(16, 104, 2):
					if faces[a].get_pixel(x, y) != faces[b].get_pixel(x, y):
						n += 1
			kit.ok(n > 1200, "%s vs %s: an individual face (%d of 1936 samples differ)" % [a, b, n])
	return true


func _speakers() -> bool:
	var names = _json("res://data/locale/de_c4_characters.json")
	var strings: Dictionary = names.get("strings", {}) if names is Dictionary else {}
	for id in CAST:
		kit.ok(str(strings.get("char.%s.name" % id, "")) != "", "%s: a German name in de_c4_characters.json" % id)
	# every speaker of the C4 dialogues has a sheet and a portrait
	var d = _json("res://data/v3/dialogue.json")
	var speakers := {}
	if kit.ok(d is Dictionary, "dialogue.json parses"):
		for c in d.get("conversations", []):
			if str(c.get("id", "")).begins_with("dlg_c4"):
				for n in c.get("nodes", []):
					speakers[str(n.get("speaker", ""))] = true
	for id in CAST:
		kit.ok(speakers.has(id), "%s speaks in the C4 dialogues" % id)
	for s in speakers:
		kit.ok(FileAccess.file_exists(CHAR + s + "/sheet.json"), "C4 speaker %s has a sheet" % s)
		kit.ok(FileAccess.file_exists(CHAR + s + "/portrait.json") and FileAccess.file_exists(CHAR + s + "/portrait.png"),
			"C4 speaker %s has a portrait" % s)
	# every char_id of the two level shells resolves to a sheet
	var rx := RegEx.create_from_string("(?m)^char_id = \"([^\"]+)\"")
	for lvl in LEVELS:
		if not kit.ok(FileAccess.file_exists(lvl), "%s exists" % lvl):
			continue
		for m in rx.search_all(FileAccess.get_file_as_string(lvl)):
			kit.ok(FileAccess.file_exists(CHAR + m.get_string(1) + "/sheet.json"), "%s: char_id %s has a sheet" % [lvl.get_file(), m.get_string(1)])
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
	var variant_rx := RegEx.create_from_string("_\\d+$")
	for n in SOUNDS:
		var spec: Array = SOUNDS[n]
		var path: String = spec[0] + n + ".wav"
		if spec[0] == SFX:
			kit.ok(variant_rx.search(n) == null, "%s: not named like a random variant" % n)
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


# ------------------------------------------------------------------------------------------------ wiring
func _wiring() -> bool:
	# the level shells: ambience / music ids resolve, and they are this chapter's
	var want := {"res://scenes/levels/L_C4_Tunnels.tscn": ["amb_karsk_cellar", "mus_c4_karsk"],
		"res://scenes/levels/L_C4_Annex.tscn": ["amb_berlin_loop", "mus_c4_berlin"]}
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
			kit.ok(m.get_string(1) in want[lvl], "%s: %s is this chapter's (%s)" % [lvl.get_file(), key, m.get_string(1)])
	# c4.json: every switch's ambience / music exists; the four scenes use the contract's four ambiences
	var c4 = _json("res://data/chapters/c4.json")
	if kit.ok(c4 is Dictionary, "c4.json parses"):
		var sw: Dictionary = c4.get("switches", {})
		for sid in sw:
			var st: Dictionary = sw[sid]
			if st.has("ambience") and str(st["ambience"]) != "":
				kit.ok(ResourceLoader.exists(AMB + str(st["ambience"]) + ".wav"), "%s: switch ambience %s exists" % [sid, st["ambience"]])
			if st.has("music") and str(st["music"]) != "":
				kit.ok(ResourceLoader.exists(MUS + str(st["music"]) + ".wav"), "%s: switch music %s exists" % [sid, st["music"]])
		var amb := {"L_C4_TunnelsA": "amb_karsk_cellar", "L_C4_TunnelsB": "amb_karsk_tunnel", "L_C4_AnnexA": "amb_berlin_loop",
			"L_C4_AnnexB": "amb_berlin_annex"}
		for sid in amb:
			kit.eq(str(sw.get(sid, {}).get("ambience", "")), amb[sid], "%s plays %s" % [sid, amb[sid]])
		var looks = c4.get("looks", {})
		if looks is Dictionary:
			for sid in looks:
				for who in looks[sid]:
					kit.ok(FileAccess.file_exists(CHAR + str(looks[sid][who]) + "/sheet.json"), "looks %s/%s has a sheet" % [sid, who])
	# every c4 sound a C4 cinematic cue names exists (sfx variants `id_1` count; the cinematics' own ids are not ours)
	var rx2 := RegEx.create_from_string("\"(?:sfx|bed|loop|amb|music)\"\\s*:\\s*\"((?:c4_|mus_c4_|amb_karsk_|amb_berlin_)[a-z0-9_]+)\"")
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
