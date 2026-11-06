extends "res://scripts/ui/ui_modal.gd"
## „Haus 14“ (pz_c4_house / objective c4h_solve_house, documentation/C4P2_DESIGN.md §2.7) — Konrad at the courtyard
## pump of Kolonnenstraße 14, Tuesday 22.40, looking up at the house; he knows how houses are built — he draws them
## before they are emptied.  The board is the house seen from the courtyard: Vorderhaus, Seitenflügel, Hinterhaus
## as three columns, six storeys from the cellar to the drying lofts, the stairwells cut open, the cobbler's
## souterrain right of the back cellar.  Every window shows who is awake.  The player leads Ilse (with Konrad
## behind her) from Hanna's flat (s3) room by room to a place no household card knows: up the stairs, across the
## lofts, down another stair, along the cellar — past no watching eye.  „Probegang“ submits the route.
## Art and layout: assets/ui/puzzle/c4p2_house*.png / c4p2_house.json (tools/pixelgen/gen_ui_c4p2.py; it verifies
## the passages of the contract and that the answer is the only safe way).
##
## Registered by data/chapters/c4p2.json (puzzles.c4h_solve_house); ChapterExt.puzzle_ui instances this scene once
## under UIRoot, sets `ui_root`, Game calls open(obj_id) and awaits `closed`.  Works stand-alone (tests) as well.
##
## Key contract (scripts/core/inputplay.gd relies on it): property `is_open`; the route starts as ["s3"] with the head
## on s3; arrows / WASD move the head into the neighbouring room in that direction when a passage exists (UP / DOWN =
## stairs and the attic / cellar doors, LEFT / RIGHT = along the attic and the cellar corridor; hk -> ws is RIGHT);
## moving onto a room already on the route cuts the route back to it (onto the previous room = undo); a move without
## a passage is refused (`ui.c4p2.house.no_way`, a soft knock); Backspace undoes the last step (also bound to cancel:
## consumed before UIRoot closes the modal); R resets to ["s3"]; K toggles the card notes (Kuhnert's box —
## presentation only); L toggles the 22.40 lights (presentation only); Enter („Probegang“) submits the route ids
## through Story.solve_puzzle at once — the walk of the markers (≤ WALK_MAX s; reduced motion: none) is presentation
## only and never swallows input: a key during the walk ends it and is then applied; Esc closes.  The first two
## failures keep the route; from the third on, a walk that ran into a watcher leaves Ilse on the last safe landing
## (the route is cut back there).  The hint appears per Settings.puzzle_hints (after `hint_after_attempts`).
## Pad (as the TracePuzzle): D-pad / left stick move the head, A or Y Probegang, B takes back the last step, X
## Kartei, LB Licht, RB Neu, Back/Select closes.  Mouse: click a neighbouring room to extend the route (or drag
## through the house with the button held), click a room of the route to cut it back there, right-click takes back
## a step; buttons Probegang · Zurück · Neu · Kartei · Licht · Schließen; hovering a room shows its nameplate, card
## note and window in the side panel.
## The Probegang walks the two figures (Ilse leading, Konrad a step behind) over the floors and the flights of the
## route and stops at the first unsafe room with its reason
## (`ui.c4p2.house.stop.s2|se|ve`), or at the end of a route that ends in a household (`stop.flat`) or anywhere but
## the workshop (`stop.short`) — presentation only; the verdict is Story.solve_puzzle's.  Unsafe rooms are
## shape-coded (a spy-hole eye, a lamp, a hat — never colour alone); the K overlay and every stopped walk show them.
## Success: the two walk down into Pietsch's workshop, a candle is lit there, Konrad's red pencil rings it, stamp +
## text, `solved(obj_id)` once; the modal closes after a reading beat (≤ SUCCESS_BEAT_MAX) or earlier on confirm.

signal solved(obj_id: String)

const PX := 3
const ART := "res://assets/ui/puzzle/"
const LAYOUT := "res://assets/ui/puzzle/c4p2_house.json"
const SUCCESS_GUARD_MS := 600
const SUCCESS_BEAT_MAX := 7.0
## The walk of the markers never takes longer than this (seconds), and one room never longer than WALK_STEP.
const WALK_MAX := 1.0
const WALK_STEP := 0.14
## From this failure on, a walk that ran into a watcher cuts the route back to the last safe room.
const TRIM_FROM_FAIL := 3
const DIRS := {"up": Vector2i(0, 1), "down": Vector2i(0, -1), "left": Vector2i(-1, 0), "right": Vector2i(1, 0)}
const DIR_ORDER := ["up", "right", "down", "left"]


## The house: two renderings (overview / 22.40 lights), window animations, labels and Kuhnert's cards, the route
## line, the two walking figures, watcher marks, the stop mark and the success overlays.
## The figures stand on floors and walk the stairs: every room has a place on its floor (`stand`), every passage a
## path of feet points along the flights or the floor (`paths`, c4p2_house.json); Ilse leads, Konrad walks TRAIL
## px of the way behind her (round 10 review: the old tokens slid down a straight line and stood in floor slabs).
class HouseBoard extends Control:
	signal room_pressed(id: String)
	signal room_dragged(id: String)
	signal hover_changed(id: String)
	signal step_back_requested
	signal walk_finished

	const UIKit := preload("res://scripts/ui/ui_kit.gd")
	const P := 3
	const FRAME := Color("0a0e14")
	const LINE_OUT := Color(0.02, 0.03, 0.05, 0.92)
	const LINE := Color("f0c487")
	const LINE_HC := Color("ffffff")
	const LINE_DONE := Color("d8604c")
	const PLATE := Color(0.02, 0.06, 0.09, 0.82)
	const PLATE_HC := Color(0.0, 0.0, 0.0, 1.0)
	const LABEL := Color("e6dec2")
	const LABEL_HC := Color("ffffff")
	const TAG_BG := Color("f2ead3")
	const TAG_INK := Color("1a1c2a")
	const TAG_RULE := Color("a8382e")
	const WARN := Color("d8604c")
	const WARN_HC := Color("ffb000")
	const HOVER := Color(0.94, 0.77, 0.53, 0.9)
	const HOVER_HC := Color(1.0, 1.0, 1.0, 1.0)
	## Card text sizes at 100 % (scaled by the text scale, never shrunk to fit: long notes wrap).
	const CARD_NAME_FS := 14
	const CARD_NOTE_FS := 13
	const CARD_PAD := 6.0
	## The legs move this many frames per second while a figure walks.
	const STEP_FPS := 11.0

	var art_size := Vector2(316, 246)
	## id -> {rect: Rect2, extra: [Rect2], node: Vector2, stand: Vector2, mate: Vector2, label_at: Vector2, col, row,
	## kind, wing, floor}
	var rooms := {}
	## "a>b" -> PackedVector2Array of feet points (art px) from a's stand to b's
	var paths := {}
	## unsafe id -> {mark: String, at: Vector2}
	var watch := {}
	## [{rect: Rect2, frames: [a, b], period: float}]
	var anims: Array = []
	var wing_at := {}
	var rows := {}
	var tex_board: Texture2D
	var tex_night: Texture2D
	var tex_anim: Texture2D
	var tex_konrad: Texture2D
	var tex_ilse: Texture2D
	var tex_circle: Texture2D
	var tex_ws_lit: Texture2D
	var tex_marks := {}
	var anim_frame := Vector2i(15, 21)
	var konrad_frame := Vector2i(15, 23)
	var konrad_feet := Vector2(8, 21)
	var ilse_frame := Vector2i(12, 17)
	var ilse_feet := Vector2(6, 15)
	var fig_frames := 5
	var trail := 14.0
	var circle_at := Vector2(284, 214)
	var names := {}
	var tags := {}
	var wing_names := {}
	var floor_letters := {}
	var route: Array = ["s3"]
	var lights := false
	var cards := false
	var learned := {}
	var hover_id := ""
	var stop_id := ""
	var lit_ws := false
	var circled := false
	var done := false
	var hc := false
	var reduced := false
	var text_scale := 1.0
	var anim_t := 0.0
	## The walk (presentation only): the rooms walked, the room where it stops, its feet points and how far along.
	var walk_route: Array = []
	var walk_end := 0
	var walk_pts := PackedVector2Array()
	var walk_len := 0.0
	var walk_s := -1.0
	## After a walk: where the figures stand (index into walk_route); -1 = at the head of `route`.
	var rest_index := -1
	var _walk_speed := 120.0
	var _pressing := false
	var _last_sig := ""

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		clip_contents = true
		focus_mode = Control.FOCUS_NONE
		mouse_exited.connect(func() -> void:
			_pressing = false
			if hover_id != "":
				hover_id = ""
				hover_changed.emit("")
				queue_redraw())

	func setup() -> void:
		custom_minimum_size = art_size * P
		size = custom_minimum_size
		queue_redraw()

	func node_px(id: String) -> Vector2:
		if not rooms.has(id):
			return Vector2.ZERO
		return (Vector2(rooms[id]["node"]) + Vector2(0.5, 0.5)) * P

	## A feet point (art px: x = the pixel column, y = the top of the floor) on the board in screen px.
	static func feet_px(p: Vector2) -> Vector2:
		return Vector2(p.x + 0.5, p.y) * P

	func stand_of(id: String) -> Vector2:
		return Vector2(rooms[id]["stand"]) if rooms.has(id) else Vector2.ZERO

	func room_rect_px(id: String) -> Rect2:
		if not rooms.has(id):
			return Rect2()
		var r: Rect2 = rooms[id]["rect"]
		return Rect2(r.position * P, r.size * P)

	## The room's own rect and the parts of it right of the back stairs (screen px).
	func room_rects_px(id: String) -> Array:
		var out: Array = [room_rect_px(id)]
		for e in rooms.get(id, {}).get("extra", []):
			out.append(Rect2((e as Rect2).position * P, (e as Rect2).size * P))
		return out

	func room_at(p: Vector2) -> String:
		var a := p / P
		var best := ""
		for id in rooms:
			var r: Rect2 = rooms[id]["rect"]
			if r.has_point(a):
				best = id
			for e in rooms[id].get("extra", []):
				if (e as Rect2).has_point(a):
					best = id
		return best

	# -------------------------------------------------------------- the ways (feet points)
	func path_between(a: String, b: String) -> PackedVector2Array:
		if paths.has(a + ">" + b):
			return paths[a + ">" + b]
		if paths.has(b + ">" + a):
			var r := PackedVector2Array(paths[b + ">" + a])
			r.reverse()
			return r
		return PackedVector2Array([stand_of(a), stand_of(b)])

	## Feet points from ids[0]'s place along the passages to ids[upto]'s place.
	func way_points(ids: Array, upto: int) -> PackedVector2Array:
		var pts := PackedVector2Array()
		if ids.is_empty():
			return pts
		pts.append(stand_of(str(ids[0])))
		for i in range(1, clampi(upto, 0, ids.size() - 1) + 1):
			var seg := path_between(str(ids[i - 1]), str(ids[i]))
			for k in range(1, seg.size()):
				pts.append(seg[k])
		return pts

	static func poly_length(pts: PackedVector2Array) -> float:
		var l := 0.0
		for i in range(1, pts.size()):
			l += pts[i - 1].distance_to(pts[i])
		return l

	## The point at arc length s along a polyline, and the facing there (+1 right, -1 left, 0 = straight up/down:
	## the last sideways step decides).
	static func poly_at(pts: PackedVector2Array, s: float) -> Array:
		if pts.is_empty():
			return [Vector2.ZERO, 0]
		if pts.size() == 1 or s <= 0.0:
			return [pts[0], _facing_from(pts, 1)]
		var acc := 0.0
		for i in range(1, pts.size()):
			var l := pts[i - 1].distance_to(pts[i])
			if acc + l >= s and l > 0.0:
				return [pts[i - 1].lerp(pts[i], (s - acc) / l), _facing_from(pts, i)]
			acc += l
		return [pts[pts.size() - 1], _facing_from(pts, pts.size() - 1)]

	static func _facing_from(pts: PackedVector2Array, i: int) -> int:
		var k := clampi(i, 1, pts.size() - 1)
		while k >= 1:
			var dx := pts[k].x - pts[k - 1].x
			if absf(dx) > 0.01:
				return 1 if dx > 0.0 else -1
			k -= 1
		return 0

	# -------------------------------------------------------------- the walk (presentation only)
	func start_walk(path: Array, end_index: int) -> void:
		walk_route = path.duplicate()
		walk_end = clampi(end_index, 0, path.size() - 1)
		rest_index = -1
		walk_pts = way_points(walk_route, walk_end)
		walk_len = poly_length(walk_pts)
		# ≤ WALK_MAX: short ways at a walking pace, the long way down the back stairs quicker
		var dur := clampf(walk_len / 300.0, 0.45, 0.95)
		_walk_speed = maxf(walk_len / dur, 1.0)
		walk_s = 0.0
		set_process(true)
		queue_redraw()

	## Seconds the current walk takes in all.
	func walk_duration() -> float:
		return walk_len / _walk_speed if _walk_speed > 0.0 else 0.0

	func is_walking() -> bool:
		return walk_s >= 0.0

	## Ends a running walk at its stop at once (a key during the walk, reduced motion, closing).
	func finish_walk() -> void:
		if walk_s < 0.0:
			return
		walk_s = -1.0
		rest_index = walk_end
		queue_redraw()
		walk_finished.emit()

	func clear_rest() -> void:
		rest_index = -1
		walk_route = []
		queue_redraw()

	func _process(delta: float) -> void:
		anim_t += delta
		if walk_s >= 0.0:
			walk_s += delta * _walk_speed
			if walk_s >= walk_len:
				finish_walk()
			else:
				queue_redraw()
			return
		if lights and not reduced and not anims.is_empty():
			var sig := ""
			for a in anims:
				sig += str(int(floor(anim_t / float(a["period"]))) % 2)
			if sig != _last_sig:
				_last_sig = sig
				queue_redraw()

	## Where the two figures are now (art px feet points) and how they stand:
	## {ilse, konrad, ilse_face, konrad_face, ilse_moving, konrad_moving}.
	func figures() -> Dictionary:
		var ids: Array = route
		var upto := route.size() - 1
		var s := -1.0
		if walk_s >= 0.0:
			ids = walk_route
			upto = walk_end
			s = walk_s
		elif rest_index >= 0 and rest_index < walk_route.size():
			ids = walk_route
			upto = rest_index
		var pts := walk_pts if walk_s >= 0.0 else way_points(ids, upto)
		var total := poly_length(pts)
		if s < 0.0:
			s = total
		var a := poly_at(pts, s)
		# Konrad: from his place beside her in the first room, TRAIL px of the way behind her
		var mate := Vector2(rooms.get(str(ids[0]), {}).get("mate", stand_of(str(ids[0])) - Vector2(9, 0))) if not ids.is_empty() else Vector2.ZERO
		var kpts := PackedVector2Array([mate])
		kpts.append_array(pts)
		var d0 := mate.distance_to(pts[0]) if not pts.is_empty() else 0.0
		var u := maxf(0.0, s - trail_for(pts) + d0)
		var k := poly_at(kpts, u)
		var walking := walk_s >= 0.0
		var iface: int = a[1]
		var kface: int = k[1]
		if total <= 0.0:                     # nobody has gone anywhere: they stand face to face
			iface = -1 if mate.x < a[0].x else 1
			kface = -iface
		if iface == 0:
			iface = 1
		if kface == 0:
			kface = iface
		return {"ilse": a[0], "konrad": k[0], "ilse_face": iface, "konrad_face": kface,
			"ilse_moving": walking, "konrad_moving": walking and u > 0.0}

	## How far behind Ilse Konrad walks on this way: when she has just come off the stairs onto her landing, he stops
	## at the head (or foot) of the flight on the same floor — a step behind her, both standing on the landing — else
	## TRAIL px back along the way.
	func trail_for(pts: PackedVector2Array) -> float:
		var n := pts.size()
		if n >= 3:
			var last := pts[n - 1]
			var bend := pts[n - 2]
			var seg := bend.distance_to(last)
			if absf(bend.y - last.y) < 0.01 and absf(pts[n - 3].y - bend.y) > 0.01 and seg >= 8.0 and seg <= trail:
				return seg
		return trail

	## The figure's sprite rect on the board (screen px) for a feet point.
	func figure_rect(feet: Vector2, frame: Vector2i, anchor: Vector2) -> Rect2:
		var at := feet_px(feet)
		return Rect2(at - (anchor + Vector2(0.5, 1.0)) * P, Vector2(frame) * P)

	# -------------------------------------------------------------- drawing
	func _font() -> Font:
		var f := get_theme_font("font", "BodyLabel")
		return f if f != null else ThemeDB.fallback_font

	func _fit_size(f: Font, text: String, base: int, max_w: float) -> int:
		var fs := base
		while fs > 11 and f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > max_w:
			fs -= 1
		return fs

	func _draw() -> void:
		var full := Rect2(Vector2.ZERO, size)
		var tex := tex_night if lights and tex_night != null else tex_board
		if tex != null:
			draw_texture_rect(tex, full, false)
		else:
			draw_rect(full, Color("0b1c24"))
		if lights and tex_anim != null and not reduced:
			for a in anims:
				var fi: Array = a["frames"]
				var f := int(floor(anim_t / float(a["period"]))) % 2
				var r: Rect2 = a["rect"]
				draw_texture_rect_region(tex_anim, Rect2(r.position * P, r.size * P),
					Rect2(Vector2(int(fi[f]) * anim_frame.x, 0), Vector2(anim_frame)))
		if lit_ws and tex_ws_lit != null and rooms.has("ws"):
			var wr: Rect2 = rooms["ws"]["rect"]
			draw_texture_rect(tex_ws_lit, Rect2(wr.position * P, Vector2(tex_ws_lit.get_size()) * P), false)
		# watchers: a dashed frame around the room (K overlay or after a walk ran into them)
		for id in watch:
			if cards or learned.has(id):
				_dashed_rect(room_rect_px(id).grow(-3), WARN_HC if hc else WARN, 4.0 if hc else 3.0)
		if hover_id != "" and not done:
			for r in room_rects_px(hover_id):
				draw_rect((r as Rect2).grow(-2), HOVER_HC if hc else HOVER, false, 3.0)
		_draw_labels()
		_draw_route()
		var tagged := {}
		if cards:
			for id in watch:
				var c := card_rect(id)
				if c.size.x > 0.0:
					tagged[id] = true
					_draw_mark(str(watch[id]["mark"]), card_mark_at(id))
		for id in watch:
			if (cards or learned.has(id)) and not tagged.has(id):
				_draw_mark(str(watch[id]["mark"]), Vector2(watch[id]["at"]) * P)
		if circled and tex_circle != null:          # Konrad's pencil ring on the board, the two of them in front of it
			var c2 := circle_at * P
			var cs := Vector2(tex_circle.get_size()) * P
			draw_texture_rect(tex_circle, Rect2(c2 - cs * 0.5, cs), false)
		_draw_markers()
		if stop_id != "" and rooms.has(stop_id) and tex_marks.has("stop"):
			_draw_mark("stop", stop_mark_at())
		draw_rect(Rect2(2, 2, size.x - 4, size.y - 4), FRAME, false, 4.0)

	func _dashed_rect(r: Rect2, col: Color, w: float) -> void:
		var pts := [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y), r.position]
		for i in 4:
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var ln := a.distance_to(b)
			var d := (b - a) / ln
			var s := 0.0
			while s < ln:
				draw_line(a + d * s, a + d * minf(s + 12.0, ln), col, w)
				s += 20.0

	## Size of a mark on the board incl. its high-contrast disc (screen px).
	func mark_size(kind: String) -> Vector2:
		var t: Texture2D = tex_marks.get(kind)
		var sz := Vector2(t.get_size()) * P if t != null else Vector2(45, 45)
		return sz + Vector2(8, 8) if hc else sz

	func _draw_mark(kind: String, at: Vector2) -> void:
		var t: Texture2D = tex_marks.get(kind)
		if t == null:
			return
		var sz := Vector2(t.get_size()) * P
		if hc:
			draw_circle(at, sz.x * 0.5 + 4, Color(0, 0, 0, 1))
		draw_texture_rect(t, Rect2(at - sz * 0.5, sz), false)

	func _draw_labels() -> void:
		var f := _font()
		# wings above the roofs, floor letters in the gutter
		for w in wing_at:
			var txt := str(wing_names.get(w, ""))
			if txt == "":
				continue
			var fs := int(round(17 * text_scale))
			var ts := f.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs)
			var at := Vector2(wing_at[w]) * P
			var r := Rect2(at.x - ts.x * 0.5 - 6, at.y, ts.x + 12, ts.y + 2)
			draw_rect(r, PLATE_HC if hc else PLATE)
			draw_string(f, Vector2(r.position.x + 6, r.position.y + f.get_ascent(fs) + 1), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, LABEL_HC if hc else LABEL)
		for fl in floor_letters:
			if not rows.has(fl):
				continue
			var yh: Array = rows[fl]
			var cy := (float(yh[0]) + float(yh[1]) * 0.5) * P
			var fs2 := int(round(16 * text_scale))
			var t := str(floor_letters[fl])
			var ts2 := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2)
			draw_rect(Rect2(2, cy - ts2.y * 0.5 - 2, 26, ts2.y + 4), PLATE_HC if hc else PLATE)
			draw_string(f, Vector2(15 - ts2.x * 0.5, cy - ts2.y * 0.5 + f.get_ascent(fs2)), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, LABEL_HC if hc else LABEL)
		for id in rooms:
			var name := str(names.get(id, ""))
			if name == "" or (id == "ws" and lit_ws and not cards):
				continue                    # the lit workshop speaks for itself (the success card names it)
			var at2 := Vector2(rooms[id]["label_at"]) * P
			var max_w := card_width(id)
			if cards:
				_draw_card(f, id, name)
				continue
			var fs3 := _fit_size(f, name, int(round(15 * text_scale)), max_w - 10)
			var ts3 := f.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3)
			var pr := Rect2(at2, Vector2(ts3.x + 10, ts3.y + 2))
			draw_rect(pr, PLATE_HC if hc else PLATE)
			if id == hover_id or (not done and id == str(route[route.size() - 1])):
				draw_rect(pr, HOVER_HC if hc else HOVER, false, 2.0)
			draw_string(f, Vector2(at2.x + 5, at2.y + 1 + f.get_ascent(fs3)), name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3, LABEL_HC if hc else LABEL)

	## Width reserved at a watched card's right edge for its mark (the mark hangs over the edge, the text stops short).
	func card_mark_reserve(id: String) -> float:
		return mark_size(str(watch[id]["mark"])).x * 0.5 + 6.0 if watch.has(id) else 0.0

	## K: the room as Kuhnert's box knows it — an index card with the name and the note in two fixed sizes (the
	## note wraps, it is never shrunk: round 10 review); a watched room's card carries its mark at the right edge.
	## Returns the card's text area for the tests: {card: Rect2, text: Rect2, name_fs, note_fs, lines}.
	func card_layout(id: String) -> Dictionary:
		var f := _font()
		var name := str(names.get(id, ""))
		var tag := str(tags.get(id, ""))
		var w := card_width(id)
		var tw := w - 2.0 * CARD_PAD - card_mark_reserve(id)
		var nfs := int(round(CARD_NAME_FS * text_scale))
		var tfs := int(round(CARD_NOTE_FS * text_scale))
		var ns := f.get_multiline_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, tw, nfs, -1, TextServer.BREAK_WORD_BOUND | TextServer.BREAK_MANDATORY)
		var ts := Vector2.ZERO
		if tag != "":
			ts = f.get_multiline_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, tw, tfs, -1, TextServer.BREAK_WORD_BOUND | TextServer.BREAK_MANDATORY)
		var at := Vector2(rooms[id]["label_at"]) * P
		var h := 3.0 + 3.0 + ns.y + ts.y + 4.0
		at.y = minf(at.y, size.y - 8.0 - h)          # a long card at 150 % moves up rather than off the board
		at.x = minf(at.x, size.x - 8.0 - w)
		var card := Rect2(at, Vector2(w, h))
		var text := Rect2(at + Vector2(CARD_PAD, 6.0), Vector2(maxf(ns.x, ts.x), ns.y + ts.y))
		return {"card": card, "text": text, "name_fs": nfs, "note_fs": tfs, "name_h": ns.y, "text_w": tw}

	func card_rect(id: String) -> Rect2:
		if not cards or not rooms.has(id):
			return Rect2()
		return card_layout(id)["card"]

	## Where a watched room's mark hangs on its card (screen px): half over the card's right edge, at its top.
	func card_mark_at(id: String) -> Vector2:
		var c: Rect2 = card_layout(id)["card"]
		var ms := mark_size(str(watch[id]["mark"]))
		return Vector2(c.end.x - 4.0, c.position.y + ms.y * 0.5 + 2.0)

	func _draw_card(f: Font, id: String, name: String) -> void:
		var lay := card_layout(id)
		var r: Rect2 = lay["card"]
		var tag := str(tags.get(id, ""))
		draw_rect(Rect2(r.position + Vector2(3, 3), r.size), Color(0, 0, 0, 0.45))
		draw_rect(r, TAG_BG)
		draw_rect(Rect2(r.position, Vector2(r.size.x, 3)), TAG_RULE)
		if watch.has(id):
			draw_rect(r, WARN_HC if hc else WARN, false, 3.0)
		var tw: float = lay["text_w"]
		var x := r.position.x + CARD_PAD
		var y := r.position.y + 6.0
		var brk := TextServer.BREAK_WORD_BOUND | TextServer.BREAK_MANDATORY
		draw_multiline_string(f, Vector2(x, y + f.get_ascent(int(lay["name_fs"]))), name, HORIZONTAL_ALIGNMENT_LEFT, tw,
			int(lay["name_fs"]), -1, TAG_INK, brk)
		if tag != "":
			draw_multiline_string(f, Vector2(x, y + float(lay["name_h"]) + f.get_ascent(int(lay["note_fs"]))), tag,
				HORIZONTAL_ALIGNMENT_LEFT, tw, int(lay["note_fs"]), -1, TAG_INK, brk)

	## Card width per room: the attic and the cellar have the whole wing, a flat its facade part.
	func card_width(id: String) -> float:
		var k := str(rooms.get(id, {}).get("kind", "flat"))
		if k in ["attic", "cellar", "workshop"]:
			return 168.0
		return 158.0

	func _draw_route() -> void:
		var pts := PackedVector2Array()
		for id in route:
			pts.append(node_px(str(id)))
		var core := LINE_DONE if done else (LINE_HC if hc else LINE)
		var w_out := 13.0 if hc else 11.0
		var w_in := 7.0 if hc else 5.0
		if pts.size() >= 2:
			draw_polyline(pts, LINE_OUT, w_out, true)
			draw_polyline(pts, core, w_in, true)
		for i in pts.size():
			draw_circle(pts[i], 7.0 if hc else 6.0, LINE_OUT)
			draw_circle(pts[i], 4.0 if hc else 3.5, core)
		if not done and pts.size() > 0:     # the head: a ring on the floor around Ilse's feet
			var c := feet_px(stand_of(head_id()))
			draw_set_transform(c, 0.0, Vector2(1.0, 0.38))
			draw_arc(Vector2.ZERO, 30.0, 0.0, TAU, 32, LINE_OUT, 9.0)
			draw_arc(Vector2.ZERO, 30.0, 0.0, TAU, 32, core, 5.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	func head_id() -> String:
		return str(route[route.size() - 1])

	func _draw_markers() -> void:
		var m := figures()
		var walk_frame := 1 + int(anim_t * STEP_FPS) % maxi(1, fig_frames - 1)
		var kf := walk_frame if bool(m["konrad_moving"]) else 0
		var i_f := walk_frame if bool(m["ilse_moving"]) else 0
		if fig_frames <= 1:
			kf = 0
			i_f = 0
		# Konrad behind, Ilse in front (she leads)
		_draw_sprite(tex_konrad, konrad_frame, kf, konrad_feet, feet_px(m["konrad"]), int(m["konrad_face"]) < 0)
		_draw_sprite(tex_ilse, ilse_frame, i_f, ilse_feet, feet_px(m["ilse"]), int(m["ilse_face"]) < 0)

	func _draw_sprite(t: Texture2D, fr: Vector2i, idx: int, feet: Vector2, at: Vector2, flip: bool) -> void:
		if t == null:
			return
		var src := Rect2(Vector2(idx * fr.x, 0), Vector2(fr))
		var sz := Vector2(fr) * P
		var anchor := (feet + Vector2(0.5, 1.0)) * P
		if flip:
			draw_set_transform(at, 0.0, Vector2(-1, 1))
			draw_texture_rect_region(t, Rect2(-anchor, sz), src)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		else:
			draw_texture_rect_region(t, Rect2(at - anchor, sz), src)

	## The two figures' rects (screen px, a little grown) — the stop mark keeps clear of them.
	func figure_rects() -> Array:
		var m := figures()
		return [figure_rect(m["ilse"], ilse_frame, ilse_feet).grow(3.0), figure_rect(m["konrad"], konrad_frame, konrad_feet).grow(3.0)]

	## The stop mark beside Ilse's head, on the side away from Konrad, never over either figure, a watcher's mark or
	## the board's edge (round 10 review: it used to cover Konrad).
	func stop_mark_at() -> Vector2:
		var m := figures()
		var ms := mark_size("stop")
		var ir: Rect2 = figure_rect(m["ilse"], ilse_frame, ilse_feet)
		var away := 1.0 if Vector2(m["konrad"]).x <= Vector2(m["ilse"]).x else -1.0
		var head := Vector2(ir.get_center().x, ir.position.y + ms.y * 0.25)
		var must: Array = figure_rects()
		for id in watch:
			if cards or learned.has(id):
				var at: Vector2 = card_mark_at(id) if cards else Vector2(watch[id]["at"]) * P
				must.append(Rect2(at - mark_size(str(watch[id]["mark"])) * 0.5, mark_size(str(watch[id]["mark"]))))
		var writing: Array = []                      # nameplates and cards: kept clear when there is room
		for id in rooms:
			var lr := card_rect(id) if cards else label_rect(id)
			if lr.size.x > 0.0:
				writing.append(lr)
		var inside := Rect2(Vector2.ZERO, size).grow(-6.0)
		# rings around her head, nearest first; on each ring: level with her head on the side away from Konrad,
		# then upwards, then the other side
		for avoid in [must + writing, must]:
			for radius in [ir.size.x * 0.5 + ms.x * 0.5 + 4.0, ms.x * 1.35 + ir.size.x * 0.5, ms.x * 2.0 + ir.size.x * 0.5]:
				for deg in [0, -30, -60, -90, 30, -120, -150, 180, 150]:
					var ang := deg_to_rad(float(deg))
					var c := head + Vector2(cos(ang) * away, sin(ang)) * float(radius)
					var r := Rect2(c - ms * 0.5, ms)
					if not inside.encloses(r):
						continue
					var free := true
					for a in avoid:
						if r.intersects(a):
							free = false
							break
					if free:
						return c
		return head + Vector2(away * (ir.size.x * 0.5 + ms.x * 0.5 + 4.0), 0.0)

	## The nameplate of a room as _draw_labels draws it (screen px; empty when the room has none).
	func label_rect(id: String) -> Rect2:
		var name := str(names.get(id, ""))
		if name == "" or not rooms.has(id) or (id == "ws" and lit_ws):
			return Rect2()
		var f := _font()
		var fs3 := _fit_size(f, name, int(round(15 * text_scale)), card_width(id) - 10)
		var ts3 := f.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3)
		return Rect2(Vector2(rooms[id]["label_at"]) * P, Vector2(ts3.x + 10, ts3.y + 2))

	# -------------------------------------------------------------- mouse
	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT:
				if mb.pressed:
					var id := room_at(mb.position)
					if id != "":
						_pressing = true
						room_pressed.emit(id)
					accept_event()
				else:
					_pressing = false
					accept_event()
			elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
				step_back_requested.emit()
				accept_event()
		elif event is InputEventMouseMotion:
			var mm := event as InputEventMouseMotion
			var id2 := room_at(mm.position)
			if id2 != hover_id:
				hover_id = id2
				hover_changed.emit(id2)
				queue_redraw()
				if _pressing and id2 != "" and (mm.button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
					room_dragged.emit(id2)
			mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if id2 != "" and not done else Control.CURSOR_ARROW


var suppress_toasts := true
var obj_id := ""
## The route Ilse would walk (room ids, starting in Hanna's flat).
var route: Array = ["s3"]
var solved_count := 0

var _puzzle: Dictionary = {}
var _layout: Dictionary = {}
var _start := "s3"
var _goal := "ws"
var _unsafe: Array = []
var _households: Array = []
## id -> {dir: neighbour}
var _step := {}
## id -> [neighbours]
var _adj := {}
var _fails := 0
var _done := false
var _solved_at := 0
var _beat_token := 0
var _pending := {}
var _board: HouseBoard
var _panel: PanelContainer
var _root_box: VBoxContainer
var _side: VBoxContainer
var _instr: Label
var _legend_rows: Array[Control] = []
var _legend_labels: Array[Label] = []
var _state_label: Label
var _info_box: VBoxContainer
var _info_title: Label
var _info_place: Label
var _info_card: PanelContainer
var _info_note: Label
var _info_window: Label
var _info_exits: Label
var _feedback: Label
var _hint_box: PanelContainer
var _hint_label: Label
var _success_box: PanelContainer
var _success_label: Label
var _tip: Label
var _check_btn: Button
var _undo_btn: Button
var _reset_btn: Button
var _cards_btn: Button
var _lights_btn: Button
var _close_btn: Button
var _controls: Control


# ================================================================ build
func _ready() -> void:
	pauses_game = true
	var lay = Kit.json(LAYOUT)
	_layout = lay if lay is Dictionary else {}
	add_child(Kit.dimmer(0.84))
	_panel = Kit.panel()
	Kit.full_rect(_panel)
	_panel.offset_left = 28
	_panel.offset_right = -28
	_panel.offset_top = 10
	_panel.offset_bottom = -10
	add_child(_panel)
	_root_box = Kit.vbox(0)
	_panel.add_child(_root_box)
	var head := Kit.hbox(28)
	_root_box.add_child(head)
	head.add_child(Kit.label(Kit.t("ui.c4p2.house.title"), "HeadingLabel"))
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	push.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(push)
	var sub := Kit.label(Kit.t("ui.c4p2.house.subtitle"), "DimLabel")
	sub.size_flags_vertical = Control.SIZE_SHRINK_END
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(sub)
	_root_box.add_child(HSeparator.new())
	_root_box.add_child(_gap(8))
	var row := Kit.hbox(28)
	row.name = "Content"
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root_box.add_child(row)
	var left := Kit.vbox(10)
	left.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(left)
	_board = HouseBoard.new()
	_board.name = "Board"
	_board.room_pressed.connect(_on_room_pressed)
	_board.room_dragged.connect(_on_room_dragged)
	_board.hover_changed.connect(func(_id: String) -> void: _refresh_info())
	_board.step_back_requested.connect(func() -> void: undo())
	_board.walk_finished.connect(_on_walk_finished)
	_board.tooltip_text = Kit.t("ui.c4p2.house.board_tip")
	_board.size_flags_horizontal = Control.SIZE_SHRINK_CENTER     # pixel art stays at exactly x3
	left.add_child(_board)
	var actions := Kit.hbox(10)
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(actions)
	_check_btn = Kit.button(Kit.t("ui.c4p2.house.btn.check"), "", 140)
	_check_btn.pressed.connect(func() -> void: submit())
	_undo_btn = Kit.button(Kit.t("ui.c4p2.house.btn.undo"), "", 104)
	_undo_btn.pressed.connect(func() -> void: undo())
	_reset_btn = Kit.button(Kit.t("ui.c4p2.house.btn.reset"), "", 90)
	_reset_btn.pressed.connect(func() -> void: reset_route())
	_cards_btn = Kit.button(Kit.t("ui.c4p2.house.cards_off"), "", 150)
	_cards_btn.toggle_mode = true
	_cards_btn.toggled.connect(func(on: bool) -> void: set_cards(on))
	_lights_btn = Kit.button(Kit.t("ui.c4p2.house.lights_off"), "", 150)
	_lights_btn.toggle_mode = true
	_lights_btn.toggled.connect(func(on: bool) -> void: set_lights(on))
	_close_btn = Kit.button(Kit.t("ui.c4p2.house.btn.close"), "", 120)
	_close_btn.pressed.connect(close)
	for b in [_check_btn, _undo_btn, _reset_btn, _cards_btn, _lights_btn, _close_btn]:
		b.add_theme_font_size_override("font_size", 27)
		actions.add_child(b)
	_side = Kit.vbox(12)
	_side.name = "Side"
	_side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(_side)
	_build_side(_side)
	_root_box.add_child(_gap(6))
	_controls = Kit.controls_row([
		["%s|%s|%s|%s" % [Kit.t("ui.key.up"), Kit.t("ui.key.right"), Kit.t("ui.key.down"), Kit.t("ui.key.left")],
			Kit.t("ui.c4p2.house.hint_move")],
		[Kit.key_name(KEY_BACKSPACE), Kit.t("ui.c4p2.house.hint_undo")], ["R", Kit.t("ui.c4p2.house.hint_reset")],
		["K", Kit.t("ui.c4p2.house.hint_cards")], ["L", Kit.t("ui.c4p2.house.hint_lights")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.c4p2.house.hint_check")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]])
	_controls.tooltip_text = Kit.t("ui.c4p2.house.controls")
	_controls.mouse_filter = Control.MOUSE_FILTER_PASS
	_root_box.add_child(_controls)
	_load_layout()
	_refresh()
	var s := Kit.svc("Settings")
	if s != null and s.has_signal("changed"):
		s.changed.connect(_on_setting_changed)


func _gap(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _build_side(v: VBoxContainer) -> void:
	_instr = Kit.wrap_label(Kit.t("ui.c4p2.house.instruction"), "BodyLabel")
	_instr.name = "Instruction"
	Kit.scalable(_instr, 25)
	v.add_child(_instr)
	for k in ["eye", "lamp", "hat"]:
		var lr := Kit.hbox(14)
		var icon := TextureRect.new()
		icon.texture = Kit.optional_tex(ART + "c4p2_house_%s.png" % k)
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.custom_minimum_size = Vector2(45, 45)      # the 15-px marks at exactly x3, like on the board
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		lr.add_child(icon)
		var ll := Kit.wrap_label(Kit.t("ui.c4p2.house.legend." + k), "BodyLabel")
		Kit.scalable(ll, 21)
		ll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ll.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		lr.add_child(ll)
		v.add_child(lr)
		_legend_rows.append(lr)
		_legend_labels.append(ll)
	var sep := HSeparator.new()
	sep.theme_type_variation = "FaintSeparator"
	v.add_child(sep)
	_state_label = Kit.label("", "KickerLabel")
	_state_label.name = "State"
	v.add_child(_state_label)
	_info_box = Kit.vbox(6)
	_info_box.name = "Info"
	v.add_child(_info_box)
	_info_title = Kit.wrap_label("", "BodyLabel")
	_info_title.add_theme_color_override("font_color", Kit.C_TEXT_BRIGHT)
	Kit.scalable(_info_title, 25)
	_info_box.add_child(_info_title)
	_info_place = Kit.label("", "DimLabel")
	Kit.scalable(_info_place, 20)
	_info_box.add_child(_info_place)
	_info_card = Kit.panel("PaperCardPanel")
	_info_card.add_theme_stylebox_override("panel", _card_box())
	_info_note = Kit.wrap_label("", "TypeLabel")
	Kit.scalable(_info_note, 21)
	_info_card.add_child(_info_note)
	_info_box.add_child(_info_card)
	_info_window = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_info_window, 21)
	_info_box.add_child(_info_window)
	_info_exits = Kit.wrap_label("", "BodyLabel")
	_info_exits.add_theme_color_override("font_color", Kit.C_AMBER)
	Kit.scalable(_info_exits, 21)
	_info_box.add_child(_info_exits)
	_feedback = Kit.wrap_label("", "BodyLabel")
	_feedback.name = "Feedback"
	_feedback.visible = false
	Kit.scalable(_feedback, 23)
	v.add_child(_feedback)
	_hint_box = Kit.panel("PlatePanel")
	_hint_box.name = "Hint"
	var hh := Kit.hbox(14)
	_hint_box.add_child(hh)
	var hic := Kit.sprite("icons/icon_hint.png")
	hic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hh.add_child(hic)
	_hint_label = Kit.wrap_label(Kit.t("ui.c4p2.house.hint"), "BodyLabel")
	_hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_hint_label, 21)
	hh.add_child(_hint_label)
	_hint_box.visible = false
	v.add_child(_hint_box)
	_tip = Kit.wrap_label("", "ControlHintLabel")
	_tip.name = "Tip"
	v.add_child(_tip)
	_success_box = Kit.panel("PaperCardPanel")
	_success_box.name = "Success"
	_success_box.add_theme_stylebox_override("panel", _paper_box())
	var sv := Kit.vbox(10)
	_success_box.add_child(sv)
	var stamp := _make_stamp(Kit.t("ui.c4p2.house.stamp").to_upper().replace("ß", "SS"))
	stamp.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	sv.add_child(stamp)
	_success_label = Kit.wrap_label(Kit.t("ui.c4p2.house.success"), "TypeLabel")
	_success_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(_success_label, 22)
	sv.add_child(_success_label)
	_success_box.visible = false
	v.add_child(_success_box)


func _paper_box() -> StyleBox:
	var st := StyleBoxTexture.new()
	st.texture = Kit.tex("res://assets/ui/frames/paper.png")
	for side in 4:
		st.set_texture_margin(side, 21)
	st.set_content_margin(SIDE_LEFT, 26)
	st.set_content_margin(SIDE_RIGHT, 26)
	st.set_content_margin(SIDE_TOP, 16)
	st.set_content_margin(SIDE_BOTTOM, 18)
	return st


## Kuhnert's index card in the side panel: paper with a red rule at the top.
func _card_box() -> StyleBox:
	var st := StyleBoxFlat.new()
	st.bg_color = Color("f2ead3")
	st.border_color = Color("a8382e")
	st.border_width_top = 4
	st.content_margin_left = 14
	st.content_margin_right = 14
	st.content_margin_top = 8
	st.content_margin_bottom = 8
	st.shadow_color = Color(0, 0, 0, 0.4)
	st.shadow_size = 3
	st.shadow_offset = Vector2(3, 3)
	return st


func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	var f := l.get_theme_font("font")
	if f != null:
		var fs := 27
		while fs > 16 and f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 214.0:
			fs -= 1
		l.add_theme_font_size_override("font_size", fs)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


func _v2(v, fallback := Vector2.ZERO) -> Vector2:
	if v is Array and v.size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return fallback


func _v2i(v, fallback := Vector2i.ZERO) -> Vector2i:
	if v is Array and v.size() >= 2:
		return Vector2i(int(v[0]), int(v[1]))
	return fallback


## Reads c4p2_house.json (rooms, passages, watchers, households, art) into the board and the passage tables.
func _load_layout() -> void:
	var b := _board
	var board: Dictionary = _layout.get("board", {}) if _layout.get("board") is Dictionary else {}
	b.art_size = _v2(board.get("size"), Vector2(316, 246))
	b.tex_board = Kit.optional_tex(ART + str(board.get("file", "c4p2_house_board.png")))
	b.tex_night = Kit.optional_tex(ART + str(board.get("night_file", "c4p2_house_night.png")))
	var marks: Dictionary = _layout.get("marks", {}) if _layout.get("marks") is Dictionary else {}
	b.tex_anim = Kit.optional_tex(ART + str(marks.get("anim", "c4p2_house_anim.png")))
	b.anim_frame = _v2i(marks.get("anim_frame"), Vector2i(15, 21))
	var figs: Dictionary = _layout.get("figures", {}) if _layout.get("figures") is Dictionary else {}
	var kfig: Dictionary = figs.get("konrad", {}) if figs.get("konrad") is Dictionary else {}
	var ifig: Dictionary = figs.get("ilse", {}) if figs.get("ilse") is Dictionary else {}
	b.tex_konrad = Kit.optional_tex(ART + str(kfig.get("file", "c4p2_house_konrad.png")))
	b.konrad_frame = _v2i(kfig.get("frame"), Vector2i(15, 23))
	b.konrad_feet = _v2(kfig.get("feet"), Vector2(8, 21))
	b.tex_ilse = Kit.optional_tex(ART + str(ifig.get("file", "c4p2_house_ilse.png")))
	b.ilse_frame = _v2i(ifig.get("frame"), Vector2i(12, 17))
	b.ilse_feet = _v2(ifig.get("feet"), Vector2(6, 15))
	b.fig_frames = maxi(1, int(kfig.get("frames", 5)))
	b.trail = float(figs.get("trail_px", 14))
	b.tex_circle = Kit.optional_tex(ART + str(marks.get("circle", "c4p2_house_circle.png")))
	b.circle_at = _v2(marks.get("circle_at"), Vector2(284, 214))
	b.tex_ws_lit = Kit.optional_tex(ART + str(marks.get("ws_lit", "c4p2_house_ws_lit.png")))
	for k in ["eye", "lamp", "hat", "stop"]:
		b.tex_marks[k] = Kit.optional_tex(ART + str(marks.get(k, "c4p2_house_%s.png" % k)))
	b.rooms.clear()
	var rooms: Dictionary = _layout.get("rooms", {}) if _layout.get("rooms") is Dictionary else {}
	for id in rooms:
		var r: Dictionary = rooms[id]
		var rect: Array = r.get("rect", [0, 0, 1, 1])
		var extra: Array = []
		for e in r.get("extra", []):
			extra.append(Rect2(float(e[0]), float(e[1]), float(e[2]), float(e[3])))
		var node := _v2(r.get("node"))
		var stand := _v2(r.get("stand"), node + Vector2(0, 2))
		b.rooms[str(id)] = {"rect": Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])),
			"extra": extra, "node": node, "stand": stand, "mate": _v2(r.get("mate"), stand - Vector2(9, 0)),
			"label_at": _v2(r.get("label_at")), "col": int(r.get("col", 0)),
			"row": int(r.get("row", 0)), "kind": str(r.get("kind", "flat")), "wing": str(r.get("wing", "")),
			"floor": str(r.get("floor", ""))}
		b.names[str(id)] = Kit.t("ui.c4p2.house.short." + str(id))
		b.tags[str(id)] = Kit.t("ui.c4p2.house.tag." + str(id))
	b.rows = {}
	var rws: Dictionary = _layout.get("rows", {}) if _layout.get("rows") is Dictionary else {}
	for f in rws:
		b.rows[str(f)] = rws[f]
		b.floor_letters[str(f)] = Kit.t("ui.c4p2.house.floor_short." + str(f))
	var wings: Dictionary = _layout.get("wings", {}) if _layout.get("wings") is Dictionary else {}
	for w in wings:
		b.wing_at[str(w)] = _v2(wings[w].get("label_at"))
		b.wing_names[str(w)] = Kit.t("ui.c4p2.house.wing." + str(w))
	b.watch.clear()
	var wt: Dictionary = _layout.get("watch", {}) if _layout.get("watch") is Dictionary else {}
	for id in wt:
		b.watch[str(id)] = {"mark": str(wt[id].get("mark", "eye")), "at": _v2(wt[id].get("at"))}
	b.anims.clear()
	for a in _layout.get("anims", []):
		var rr: Array = a.get("rect", [0, 0, 15, 21])
		b.anims.append({"rect": Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3])),
			"frames": a.get("frames", [0, 1]), "period": maxf(0.3, float(a.get("period", 1.0)))})
	_start = str(_layout.get("start", "s3"))
	_goal = str(_layout.get("goal", "ws"))
	_unsafe = (_layout.get("unsafe", []) as Array).map(func(x) -> String: return str(x))
	_households = (_layout.get("households", []) as Array).map(func(x) -> String: return str(x))
	b.paths.clear()
	var edges: Array = _layout.get("edges", [])
	var ways: Array = _layout.get("paths", [])
	for i in mini(edges.size(), ways.size()):
		var pts := PackedVector2Array()
		for q in ways[i]:
			pts.append(Vector2(float(q[0]), float(q[1])))
		b.paths["%s>%s" % [str(edges[i][0]), str(edges[i][1])]] = pts
	_adj.clear()
	_step.clear()
	for id in b.rooms:
		_adj[id] = []
		_step[id] = {}
	for e in _layout.get("edges", []):
		var a1 := str(e[0])
		var b1 := str(e[1])
		if not (b.rooms.has(a1) and b.rooms.has(b1)):
			continue
		_adj[a1].append(b1)
		_adj[b1].append(a1)
		_step[a1][_dir_between(a1, b1)] = b1
		_step[b1][_dir_between(b1, a1)] = a1
	route = [_start]
	b.route = route
	b.setup()


## The arrow that leads from room a to its neighbour b (from the grid cells of the layout).
func _dir_between(a: String, b: String) -> String:
	var ca := Vector2i(int(_board.rooms[a]["col"]), int(_board.rooms[a]["row"]))
	var cb := Vector2i(int(_board.rooms[b]["col"]), int(_board.rooms[b]["row"]))
	var d := cb - ca
	for k in DIRS:
		if DIRS[k] == d:
			return k
	return ""


# ================================================================ open / state
func open(id: String) -> void:
	obj_id = id
	var p = Kit.call_svc("Story", "puzzle_for", [id], null)
	_puzzle = p if p is Dictionary and not p.is_empty() else Kit.puzzle_for_objective(id)
	_fails = 0
	_done = false
	_pending = {}
	_beat_token += 1
	route = [_start]
	var b := _board
	b.route = route
	b.done = false
	b.lit_ws = false
	b.circled = false
	b.stop_id = ""
	b.learned.clear()
	b.hover_id = ""
	b.walk_s = -1.0
	b.clear_rest()
	_set_toggle(_cards_btn, false)
	_set_toggle(_lights_btn, false)
	b.cards = false
	b.lights = false
	_close_btn.text = Kit.t("ui.c4p2.house.btn.close")
	_set_feedback("")
	_refresh()
	open_modal()


func _set_toggle(btn: Button, on: bool) -> void:
	btn.set_pressed_no_signal(on)


func route_ids() -> Array:
	return route.duplicate()


func head() -> String:
	return str(route[route.size() - 1])


func is_done() -> bool:
	return _done


func is_walking() -> bool:
	return _board.is_walking()


func cards_on() -> bool:
	return _board.cards


func lights_on() -> bool:
	return _board.lights


func stop_room() -> String:
	return _board.stop_id


func learned_rooms() -> Array:
	return _board.learned.keys()


func success_stage() -> int:
	return (1 if _done else 0) + (1 if _board.lit_ws else 0) + (1 if _board.circled else 0)


func feedback_text() -> String:
	return _feedback.text if _feedback != null and _feedback.visible else ""


func hint_shown() -> bool:
	return _hint_box != null and _hint_box.visible


func success_shown() -> bool:
	return _success_box != null and _success_box.visible


func tip_text() -> String:
	return _tip.text if _tip != null and _tip.visible else ""


## The neighbour of a room in an arrow direction ("" = no passage).
func neighbour(id: String, dir: String) -> String:
	return str(_step.get(id, {}).get(dir, ""))


func neighbours(id: String) -> Array:
	return (_adj.get(id, []) as Array).duplicate()


# ================================================================ actions
## Arrow / WASD / D-pad / stick: into the neighbouring room in that direction.  quiet: a held key repeating
## into a wall knocks only once.
func step(dir: String, quiet := false) -> bool:
	if _done:
		return false
	var n := neighbour(head(), dir)
	if n == "":
		if not quiet:
			_no_way()
		return false
	return go_to(n)


## Onto a room of the route: cut back there; onto a neighbour of the head: one step further.
func go_to(id: String, quiet := false) -> bool:
	if _done or not _board.rooms.has(id):
		return false
	var i := route.find(id)
	if i >= 0:
		if i == route.size() - 1:
			return false
		route.resize(i + 1)
		Kit.ui_sound("back")
		_after_route_change()
		return true
	if not (_adj.get(head(), []) as Array).has(id):
		if not quiet:
			_no_way()
		return false
	var prev := head()
	route.append(id)
	Kit.ui_sound_first(step_sound_ids(prev, id))
	_after_route_change()
	return true


## The sound of one step of Ilse's way (C4P2_DESIGN §8): the attic door into a drying loft, the wooden stairs going
## down, else the tick of the pencil on the plan.
func step_sound_ids(prev: String, to: String) -> Array:
	if to in ["vd", "sd", "hd"] and not (prev in ["vd", "sd", "hd"]):
		return ["c4p2_attic_door", "tick"]
	if int(_board.rooms.get(to, {}).get("row", 0)) < int(_board.rooms.get(prev, {}).get("row", 0)):
		return ["c4p2_steps_down", "tick"]
	return ["tick"]


## Backspace / pad B / right-click / „Zurück“: the last step back.
func undo() -> bool:
	if _done or route.size() <= 1:
		return false
	route.pop_back()
	Kit.ui_sound("back")
	_after_route_change()
	return true


## R / pad RB / „Neu“: Ilse back in Hanna's flat.
func reset_route() -> bool:
	if _done or route.size() <= 1:
		return false
	route = [_start]
	Kit.ui_sound("page")
	_after_route_change()
	return true


func set_cards(on: bool) -> void:
	if _board.cards == on:
		return
	_board.cards = on
	_set_toggle(_cards_btn, on)
	Kit.ui_sound_first(["mg_c3p2_card_file", "page"])
	_refresh()


func toggle_cards() -> void:
	set_cards(not _board.cards)


func set_lights(on: bool) -> void:
	if _board.lights == on:
		return
	_board.lights = on
	_set_toggle(_lights_btn, on)
	Kit.ui_sound_first(["mg_relay_click", "tick"])
	_board.set_process(true)
	_refresh()


func toggle_lights() -> void:
	set_lights(not _board.lights)


func _after_route_change() -> void:
	_board.route = route
	_board.stop_id = ""
	_board.clear_rest()
	_set_feedback("")
	_refresh()


func _no_way() -> void:
	_set_feedback(Kit.t("ui.c4p2.house.no_way"))
	Kit.ui_sound_first(["ui_knock", "c4p2_knock", "back"])
	_nudge_head()


## Where a walk of this route stops, and why (presentation only — the verdict is Story.solve_puzzle's).
func walk_stop(path: Array) -> Dictionary:
	for i in range(1, path.size()):
		var id := str(path[i])
		if _unsafe.has(id):
			return {"index": i, "room": id, "key": "ui.c4p2.house.stop." + id, "unsafe": true}
	var last := str(path[path.size() - 1])
	if last == _goal:
		return {"index": path.size() - 1, "room": last, "key": "", "unsafe": false, "goal": true}
	var key := "ui.c4p2.house.stop.flat" if _households.has(last) else "ui.c4p2.house.stop.short"
	return {"index": path.size() - 1, "room": last, "key": key, "unsafe": false}


## Enter / pad A or Y / „Probegang“: the route goes to the engine at once; the walk only shows it.
func submit() -> Dictionary:
	if _board.is_walking():
		_board.finish_walk()
	if _done:
		return {}
	var answer := route.duplicate()
	var r = Kit.call_svc("Story", "solve_puzzle", [obj_id, answer], null)
	var ok := r is bool or Kit.ok(r)
	if r == null or not ok:
		_set_feedback(Kit.t("ui.c4p2.house.error", {"error": _error_text(r)}))
		Kit.ui_sound("fail")
		return r if r is Dictionary else {"ok": false, "error": "no Story service"}
	var is_solved: bool = bool(r) if r is bool else bool((r as Dictionary).get("solved", false))
	if is_solved:
		_on_solved()
	else:
		_fails += 1
		var stop := walk_stop(answer)
		if bool(stop.get("goal", false)):
			stop = {"index": answer.size() - 1, "room": str(answer[answer.size() - 1]), "key": "ui.c4p2.house.wrong", "unsafe": false}
		_pending = {"kind": "fail", "stop": stop, "fails": _fails}
		_set_feedback("")
		_walk(answer, int(stop["index"]))
	return r if r is Dictionary else {"ok": true, "solved": is_solved}


func _walk(path: Array, end_index: int) -> void:
	if Kit.reduced_motion() or not is_inside_tree() or end_index <= 0:
		_board.walk_route = path.duplicate()
		_board.walk_end = end_index
		_board.walk_s = -1.0
		_board.rest_index = end_index
		_on_walk_finished()
		return
	_board.start_walk(path, end_index)
	Kit.ui_sound_first(["c4p2_steps", "step_wood", "tick"])     # one creak of the stairs as they set off
	_state_label.text = Kit.t("ui.c4p2.house.walking")


func _on_walk_finished() -> void:
	var p := _pending
	_pending = {}
	if p.is_empty():
		_refresh()
		return
	if str(p.get("kind", "")) == "fail":
		var stop: Dictionary = p["stop"]
		var room := str(stop.get("room", ""))
		_board.stop_id = room
		if bool(stop.get("unsafe", false)):
			_board.learned[room] = true
		var key := str(stop.get("key", "ui.c4p2.house.wrong"))
		_set_feedback(Kit.t(key, {"room": Kit.t("ui.c4p2.house.room." + room)}))
		# Frau Pohl („meldet zuverlässig“) slides her spy-hole cover; every other stop is the plain fail
		Kit.ui_sound_first(["c4p2_spyhole", "fail"] if room == "s2" else ["fail"])
		_nudge()
		if bool(stop.get("unsafe", false)) and int(p.get("fails", 0)) >= TRIM_FROM_FAIL:
			var idx := int(stop.get("index", 1))
			if idx >= 1 and idx <= route.size():
				route.resize(idx)
				_board.route = route
				_board.clear_rest()
		_refresh()
	elif str(p.get("kind", "")) == "success":
		_reveal_workshop(int(p.get("token", -1)))


func _error_text(r) -> String:
	if r is Dictionary:
		var k := str(r.get("error_key", ""))
		if k != "" and Kit.has_key(k):
			return Kit.t(k)
		var e := str(r.get("error", ""))
		if e != "":
			return e
	return Kit.t("ui.common.unavailable")


func _on_solved() -> void:
	_done = true
	_board.done = true
	_board.hover_id = ""
	_solved_at = Time.get_ticks_msec()
	_set_feedback("")
	solved_count += 1
	solved.emit(obj_id)
	_beat_token += 1
	var token := _beat_token
	_close_btn.text = Kit.t("ui.c4p2.house.btn.continue")
	_close_btn.grab_focus.call_deferred()
	_pending = {"kind": "success", "token": token}
	_refresh()
	_walk(route.duplicate(), route.size() - 1)
	if is_inside_tree():
		get_tree().create_timer(success_beat(), true).timeout.connect(_on_beat.bind(token), CONNECT_ONE_SHOT)


## They are down: Pietsch lights a candle, the success card appears, then Konrad's red pencil rings the workshop.
func _reveal_workshop(token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.lit_ws = true
	_board.queue_redraw()
	Kit.ui_sound_first(["c4p2_door", "door_open", "snap"])
	_refresh()
	if not Kit.reduced_motion():
		Kit.appear(_success_box, 0.22)
	if Kit.reduced_motion() or not is_inside_tree():
		_reveal_circle(token)
	else:
		get_tree().create_timer(0.55, true).timeout.connect(_reveal_circle.bind(token), CONNECT_ONE_SHOT)


func _reveal_circle(token: int) -> void:
	if token != _beat_token or not _done:
		return
	_board.circled = true
	_board.queue_redraw()
	Kit.ui_sound_first(["c4p2_pencil", "cine_finale_pencil", "tick"])


## Seconds the solved modal stays open by itself (walk + reading beat, ≤ SUCCESS_BEAT_MAX); confirm closes earlier.
func success_beat() -> float:
	return clampf(2.0 + Kit.t("ui.c4p2.house.success").length() * 0.03, 3.0, SUCCESS_BEAT_MAX)


func _on_beat(token: int) -> void:
	if token == _beat_token and _done and is_open:
		close()


func _set_feedback(text: String) -> void:
	if _feedback == null:
		return
	_feedback.text = text
	_feedback.visible = text != ""
	if _tip != null:
		_refresh()


func _nudge() -> void:
	if Kit.reduced_motion() or _board == null or not _board.is_inside_tree():
		return
	var base := _board.position.x
	var tw := _board.create_tween()
	for dx in [6, -6, 3, 0]:
		tw.tween_property(_board, "position:x", base + float(dx), 0.05)


func _nudge_head() -> void:
	if Kit.reduced_motion() or _board == null or not _board.is_inside_tree():
		return
	var base := _board.position.y
	var tw := _board.create_tween()
	for dy in [3, -2, 0]:
		tw.tween_property(_board, "position:y", base + float(dy), 0.04)


func _hint_visible() -> bool:
	if _done:
		return false
	var mode := int(Kit.setting("puzzle_hints", 1))
	if mode <= 0:
		return false
	if mode >= 2:
		return true
	var r = Kit.call_svc("Story", "puzzle_hint_available", [obj_id], null)
	if r is bool:
		return r
	if r is Dictionary:
		return bool(r.get("available", r.get("hint", false)))
	return _fails >= int(_puzzle.get("hint_after_attempts", 2))


func _room_name(id: String) -> String:
	return Kit.t("ui.c4p2.house.room." + id)


func _refresh() -> void:
	if _board == null or _state_label == null:
		return
	var hc := Kit.high_contrast()
	var b := _board
	var redraw := false
	if b.hc != hc:
		b.hc = hc
		redraw = true
	var rm := Kit.reduced_motion()
	if b.reduced != rm:
		b.reduced = rm
		redraw = true
	var ts := Kit.text_scale()
	if not is_equal_approx(b.text_scale, ts):
		b.text_scale = ts
		redraw = true
	if redraw:
		b.queue_redraw()
	b.route = route
	b.queue_redraw()
	if b.is_walking():
		_state_label.text = Kit.t("ui.c4p2.house.walking")
	elif route.size() <= 1:
		_state_label.text = Kit.t("ui.c4p2.house.state_start")
	else:
		_state_label.text = Kit.t("ui.c4p2.house.state", {"n": route.size(), "room": Kit.t("ui.c4p2.house.short." + head())})
	_state_label.add_theme_color_override("font_color", Kit.C_TEXT if hc else Kit.C_AMBER)
	_cards_btn.text = Kit.t("ui.c4p2.house.cards_on" if b.cards else "ui.c4p2.house.cards_off")
	_lights_btn.text = Kit.t("ui.c4p2.house.lights_on" if b.lights else "ui.c4p2.house.lights_off")
	_check_btn.disabled = _done
	_undo_btn.disabled = _done or route.size() <= 1
	_reset_btn.disabled = _done or route.size() <= 1
	_cards_btn.disabled = false
	_lights_btn.disabled = false
	_hint_box.visible = _hint_visible()
	_success_box.visible = _done and (b.lit_ws or rm)
	_tip.text = Kit.t("ui.c4p2.house.tip_pad" if Kit.last_input_pad else "ui.c4p2.house.tip_mouse")
	var wide := ts > 1.1
	var busy := _feedback.visible or _hint_box.visible
	_tip.visible = not _done and not busy                # the side panel is full: notes and hint get the room
	_instr.visible = not _done and not (wide and busy)   # the success card takes the instruction's place
	for r in _legend_rows:                               # the legend stays up to 125 %, solved or not
		r.visible = not ((_done or busy) and ts > 1.3)
	_info_box.visible = not (_done and wide)
	_refresh_info()


## Side panel: the hovered room, else the room Ilse stands in — nameplate, place, Kuhnert's card, the window at
## 22.40 and (for her room) the passages from here.
func _refresh_info() -> void:
	if _info_title == null:
		return
	var id := _board.hover_id if _board.hover_id != "" else head()
	if not _board.rooms.has(id):
		return
	var r: Dictionary = _board.rooms[id]
	_info_title.text = _room_name(id)
	if Kit.has_key("ui.c4p2.house.place." + id):
		_info_place.text = Kit.t("ui.c4p2.house.place." + id)
	else:
		_info_place.text = Kit.t("ui.c4p2.house.place", {"wing": Kit.t("ui.c4p2.house.wing." + str(r["wing"])),
			"floor": Kit.t("ui.c4p2.house.floor." + str(r["floor"]))})
	_info_note.text = Kit.t("ui.c4p2.house.card", {"note": Kit.t("ui.c4p2.house.note." + id)})
	_info_window.text = Kit.t("ui.c4p2.house.window_line", {"text": Kit.t("ui.c4p2.house.window." + id)})
	_info_window.add_theme_color_override("font_color", Kit.C_TEXT_BRIGHT if Kit.high_contrast() else Kit.C_TEXT)
	if id == head() and not _done:
		var parts: Array = []
		for d in DIR_ORDER:
			var n := neighbour(id, d)
			if n != "":
				parts.append("%s %s" % [Kit.t("ui.key." + d), Kit.t("ui.c4p2.house.short." + n)])
		_info_exits.text = Kit.t("ui.c4p2.house.exits", {"list": "  ·  ".join(parts)})
		_info_exits.visible = true
	else:
		_info_exits.visible = false


func _on_setting_changed(key: String, _value) -> void:
	if key in ["text_scale", "high_contrast", "reduced_motion"]:
		_refresh()


func focus_default() -> void:
	if _done:
		_close_btn.grab_focus()
	else:
		_check_btn.grab_focus()


func _on_open() -> void:
	Kit.ui_sound("paper")
	_board.set_process(true)
	_refresh()


func _on_close() -> void:
	_beat_token += 1
	_pending = {}
	_board.walk_s = -1.0
	_board.set_process(false)


# ================================================================ mouse
func _on_room_pressed(id: String) -> void:
	if _board.is_walking():
		_board.finish_walk()
	if _done:
		return
	go_to(id)


func _on_room_dragged(id: String) -> void:
	if _done or _board.is_walking():
		return
	if route.has(id) or (_adj.get(head(), []) as Array).has(id):
		go_to(id, true)


# ================================================================ input (called by UIRoot before the GUI)
const STICK := {"ui_left": "left", "ui_right": "right", "ui_up": "up", "ui_down": "down"}


func _is_press(event: InputEvent) -> bool:
	return (event is InputEventKey and event.pressed) or (event is InputEventJoypadButton and event.pressed)


func modal_input(event: InputEvent) -> bool:
	if _board.is_walking() and _is_press(event):
		_board.finish_walk()            # a key during the walk ends it and is then applied
	if _done:
		return _done_input(event)
	if event is InputEventJoypadButton:
		return _pad_input(event as InputEventJoypadButton)
	if event is InputEventJoypadMotion:
		for a in STICK:
			if InputMap.has_action(a) and event.is_action_pressed(a):
				step(STICK[a])
				return true
		return false
	if not (event is InputEventKey) or not event.pressed:
		return false
	var ke := event as InputEventKey
	if ke.ctrl_pressed or ke.alt_pressed or ke.meta_pressed:
		return false
	var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
	match k:
		KEY_LEFT, KEY_A:
			step("left", ke.echo)
			return true
		KEY_RIGHT, KEY_D:
			step("right", ke.echo)
			return true
		KEY_UP, KEY_W:
			step("up", ke.echo)
			return true
		KEY_DOWN, KEY_S:
			step("down", ke.echo)
			return true
		KEY_BACKSPACE:              # also bound to "cancel": consume it before UIRoot closes the modal
			if not ke.echo:
				undo()
			return true
		KEY_R:
			if not ke.echo:
				reset_route()
			return true
		KEY_K:
			if not ke.echo:
				toggle_cards()
			return true
		KEY_L:
			if not ke.echo:
				toggle_lights()
			return true
		KEY_ENTER, KEY_KP_ENTER:
			if ke.echo:
				return true
			var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
			if f != null and f in [_undo_btn, _reset_btn, _cards_btn, _lights_btn, _close_btn]:
				return false            # Enter on another action button presses that button
			submit()
			return true
	return false


## Controller (C4P2_DESIGN §2.7, as the TracePuzzle): D-pad moves the head, A or Y Probegang, B takes back the last
## step, X Kartei, LB Licht, RB Neu, Back/Select closes.
func _pad_input(jb: InputEventJoypadButton) -> bool:
	var mine := [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_X, JOY_BUTTON_Y, JOY_BUTTON_BACK, JOY_BUTTON_DPAD_LEFT,
		JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_LEFT_SHOULDER,
		JOY_BUTTON_RIGHT_SHOULDER]
	if not jb.pressed:
		return jb.button_index in mine
	match jb.button_index:
		JOY_BUTTON_DPAD_LEFT:
			step("left")
		JOY_BUTTON_DPAD_RIGHT:
			step("right")
		JOY_BUTTON_DPAD_UP:
			step("up")
		JOY_BUTTON_DPAD_DOWN:
			step("down")
		JOY_BUTTON_A, JOY_BUTTON_Y:
			submit()
		JOY_BUTTON_B:
			undo()
		JOY_BUTTON_X:
			toggle_cards()
		JOY_BUTTON_LEFT_SHOULDER:
			toggle_lights()
		JOY_BUTTON_RIGHT_SHOULDER:
			reset_route()
		JOY_BUTTON_BACK:
			Kit.ui_sound("back")
			close()
		_:
			return false
	return true


## After success: confirm / cancel (after a short guard) closes; everything else is swallowed.
func _done_input(event: InputEvent) -> bool:
	var confirm := false
	if event is InputEventKey and event.pressed and not event.echo:
		var ke := event as InputEventKey
		var k := ke.physical_keycode if ke.physical_keycode != 0 else ke.keycode
		confirm = k in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_ESCAPE, KEY_BACKSPACE]
	elif event is InputEventJoypadButton and event.pressed:
		confirm = (event as InputEventJoypadButton).button_index in [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_BACK]
	elif event is InputEventMouseButton:
		return false                    # the „Weiter“ button stays clickable
	if not confirm:
		return event is InputEventKey or event is InputEventJoypadButton
	if Time.get_ticks_msec() - _solved_at >= SUCCESS_GUARD_MS and is_open:
		close()
	return true


func handle_cancel() -> bool:
	if _board.is_walking():
		_board.finish_walk()
	if _done and Time.get_ticks_msec() - _solved_at < SUCCESS_GUARD_MS:
		return true
	return super.handle_cancel()


# ================================================================ accessibility report (tests)
## Text colour / background pairs this puzzle draws itself (WCAG contrast is checked by tests/test_c4p2_puzzle_ui.gd).
func contrast_pairs() -> Array:
	var hc := Kit.high_contrast()
	return [
		{"what": "room nameplate on its plate", "fg": HouseBoard.LABEL_HC if hc else HouseBoard.LABEL,
			"bg": HouseBoard.PLATE_HC if hc else Color(0.02, 0.06, 0.09)},
		{"what": "card tag (K) on the index card", "fg": HouseBoard.TAG_INK, "bg": HouseBoard.TAG_BG},
		{"what": "Kuhnert's card note in the side panel", "fg": Kit.C_INK, "bg": Color("f2ead3")},
		{"what": "state line", "fg": Kit.C_TEXT if hc else Kit.C_AMBER, "bg": Kit.C_NAVY},
		{"what": "window line", "fg": Kit.C_TEXT_BRIGHT if hc else Kit.C_TEXT, "bg": Kit.C_NAVY},
		{"what": "passages from here", "fg": Kit.C_AMBER, "bg": Kit.C_NAVY},
		{"what": "success text on the paper card", "fg": Kit.C_INK, "bg": Kit.C_PAPER},
	]
