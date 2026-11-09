extends "res://scenes/cinematics/ch3_common/c3_cinematic.gd"
## Shared base of the Chapter-3 part-2 cinematics LS_C3_Radio / _Fire / _Escape / _Halves (C3P2_DESIGN §2.9).
## Owner: cinematics stream (round 8).  Reuses the §12.5 runtime of ch3_common/c3_cinematic.gd unchanged
## (finished exactly once, idempotent skip(), configure(ctx), seek()/advance(), cue list, reduced motion) and adds:
##   * textures from assets/cinematics/c3p2/ (tools/pixelgen/env_c3p2_cine*.py) and its layout.json section
##   * choice(objective)      the recorded option of a choice objective (ctx.choices; "" = not chosen)
##   * schedule(lines)        subtitle cues placed one after another: [{key, at, dur}] -> start = max(at, prev end)
##   * shot(t) / SHOTS        the current shot id from a [[id, start, end], ...] table
##   * draw helpers for animated sheets (flames, puffs) that stay pure functions of t
## Dev-only switch (in addition to the base's --cine-t / --cine-rm / --cine-flags):
##   --cine-choices=c3d_choose=pocket_plan,c3g_choose=swap_halves   merge recorded choices into configure(ctx)

const ASSETS2 := "res://assets/cinematics/c3p2/"
const FX := preload("res://scenes/cinematics/ch3_common/pixel_fx.gd")
## the pixel fire kit (flames, smoke, sparks, fire light): tools/pixelgen/pixel_fire.py -> assets/fx/pixel_fire/
const PF := preload("res://scripts/render/pixel_fire.gd")
## gap between two subtitles that follow each other
const LINE_GAP := 0.1

var layout: Dictionary = {}
var _shots: Array = []
var _layout_cache: Dictionary = {}


func _layout_section(section: String) -> Dictionary:
	if _layout_cache.is_empty():
		var p := ASSETS2 + "layout.json"
		if FileAccess.file_exists(p):
			var d = JSON.parse_string(FileAccess.get_file_as_string(p))
			if d is Dictionary:
				_layout_cache = d
	var s = _layout_cache.get(section, {})
	return s if s is Dictionary else {}


## Texture under assets/cinematics/c3p2/ (same fallbacks and `missing` bookkeeping as the base).
func tex(rel: String) -> Texture2D:
	var path := ASSETS2 + rel
	if ResourceLoader.exists(path):
		var r = load(path)
		if r is Texture2D:
			return r
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img:
			return ImageTexture.create_from_image(img)
	if not missing.has(path):
		missing.append(path)
	return null


func configure(ctx: Dictionary) -> void:
	var c := ctx.duplicate()
	var ch: Dictionary = {}
	if ctx.get("choices") is Dictionary:
		ch = (ctx["choices"] as Dictionary).duplicate(true)
	ch.merge(_dev_choices(), true)
	c["choices"] = ch
	super.configure(c)


func choice(objective: String) -> String:
	var v = choices.get(objective, "")
	return "" if v == null else str(v)


func _dev_choices() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--cine-choices="):
			for kv in a.substr(15).split(",", false):
				var p := kv.split("=")
				if p.size() == 2:
					out[p[0]] = p[1]
	return out


## Subtitle cues one after the other: each line starts at max(its `at`, the previous line's end + LINE_GAP).
func schedule(lines: Array) -> Array:
	var out: Array = []
	var end := -1.0
	for l in lines:
		var d: Dictionary = l
		var start := maxf(float(d.get("at", 0.0)), end + LINE_GAP)
		var dur := float(d.get("dur", 3.0))
		out.append({"t": start, "say": str(d["key"]), "dur": dur})
		end = start + dur
	return out


func shot_at(time: float) -> String:
	for s in _shots:
		if time < float(s[2]):
			return str(s[0])
	return str(_shots[-1][0]) if not _shots.is_empty() else ""


func get_shot_id() -> String:
	return shot_at(t)


## true while `time` lies in shot `id`
func in_shot(id: String, time: float) -> bool:
	for s in _shots:
		if str(s[0]) == id:
			return time >= float(s[1]) and time < float(s[2])
	return false


## Draw frame `i` of a horizontal sheet with `n` frames, bottom-centre anchored at `pos` (whole pixels).
static func draw_frame(ci: CanvasItem, sheet: Texture2D, n: int, i: int, pos: Vector2, flip := false,
		mod := Color(1, 1, 1, 1)) -> void:
	if sheet == null:
		return
	var fw := sheet.get_width() / maxi(1, n)
	var fh := sheet.get_height()
	var at := Vector2(roundf(pos.x - fw * 0.5), roundf(pos.y - fh))
	var src := Rect2(posmod(i, n) * fw, 0, fw, fh)
	ci.draw_texture_rect_region(sheet, Rect2(at, Vector2(fw * (-1 if flip else 1), fh)), src, mod)


## Flame of an n-frame sheet: frame rate `fps`, a per-flame phase; reduced motion halves the rate.
func flame_frame(time: float, n: int, phase: float, fps := 9.0) -> int:
	var r := fps * (0.5 if reduced_motion() else 1.0)
	return int(floor(time * r + phase * n)) % n


## Rate of the pixel fire kit's flames and light pools: reduced motion halves it.
func fire_rate() -> float:
	return 0.5 if reduced_motion() else 1.0


## The kit sheets a film uses must exist (same `missing` bookkeeping as tex()).
func need_kit(names: Array) -> void:
	for n in names:
		if PF.sheet(str(n)) == null and not missing.has(PF.DIR + str(n) + ".png"):
			missing.append(PF.DIR + str(n) + ".png")


## A film's own sheet of the kit's make (assets/cinematics/c3p2/...), registered under `sheet_name` for PF.*.
func own_sheet(sheet_name: String, rel: String, n: int) -> void:
	PF.register(sheet_name, tex(rel), n)


## Smoke rolling along a ceiling behind a moving head at x = head (dir +1: it comes from the left, -1: from
## the right; whole pixels): big puffs roll at the head, behind them a veil, then the bank.  The billows travel
## with the head when `carried` (smoke drifting in), or hang where they are (smoke spreading from a fire).
func smoke_front(ci: CanvasItem, head: float, dir: float, foot_y: float, time: float, carried := false,
		veil := 96.0, warm := true) -> void:
	var tag := "" if warm else "_grey"
	var hx := roundf(head)
	var o := {"rate": 0.3 * motion_k(), "shift": int(-hx) if carried else 23}
	var a := hx - dir * veil
	PF.wall(ci, ["veil_a" + tag, "veil_b" + tag], clampf(minf(hx, a), 0.0, 640.0), clampf(maxf(hx, a), 0.0, 640.0),
		foot_y, time, o)
	if dir > 0.0:
		PF.wall(ci, ["bank_a" + tag, "bank_b" + tag], 0.0, clampf(a, 0.0, 640.0), foot_y, time, o)
	else:
		PF.wall(ci, ["bank_a" + tag, "bank_b" + tag], clampf(a, 0.0, 640.0), 640.0, foot_y, time, o)
	for i in 3:
		PF.puff(ci, ("puff_xl" if i == 1 else "puff_l") + tag,
			Vector2(hx - dir * (6.0 + i * 16.0), foot_y - 30.0 + (i % 2) * 12.0),
			0.3 + 0.12 * absf(sin(time * 1.3 * motion_k() + i * 2.1)), i)


## A light step (-1, 0 or 1) that changes at most PF.LIGHT_HZ times a second: fire light breathes in whole
## steps, it never ramps and never strobes.
func light_step(time: float, seed: int) -> int:
	return int(roundf(hnoise(floorf(time * PF.LIGHT_HZ * fire_rate()) * 1.37, seed)))


## Slow (< 3 Hz) brightness wobble of fire light, softened by reduced motion: 1 +- amp.
func fire_wobble(time: float, seed: int, amp := 0.12) -> float:
	var a := amp * (0.45 if reduced_motion() else 1.0)
	return 1.0 + a * (0.65 * hnoise(time * 2.2, seed) + 0.35 * hnoise(time * 1.1, seed + 7))


## A snow layer clipped to `clip` (empty = whole frame), deterministic, scaled by reduced motion.
func snow(parent: Node, rect: Rect2, layers: Array, seed: int, clip := Rect2()) -> Node2D:
	var s := FX.new()
	s.name = "Snow%d" % seed
	parent.add_child(s)
	var k := 0.6 if reduced_motion() else 1.0
	var L2: Array = []
	for l in layers:
		var d: Dictionary = (l as Dictionary).duplicate()
		d["count"] = int(float(d.get("count", 40)) * k)
		L2.append(d)
	s.setup_snow(rect, L2, seed)
	s.visible_rect = clip
	return s


func motion_k() -> float:
	return 0.5 if reduced_motion() else 1.0
