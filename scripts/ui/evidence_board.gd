extends "res://scripts/ui/ui_modal.gd"
## EvidenceBoard „Die Akte C-17“ (round 9, owner: board; TECHNICAL_ARCHITECTURE §12.12). A cork board that makes the
## investigation tangible: every evidence item of data/v3/items.json the player owns hangs as a small paper card
## (the telling detail of its inspect close-up, else an original drawing — assets/ui/board/thumbs, generator
## tools/pixelgen/gen_ui_board.py) with its German name; cards hang in columns per place (Karsk, Berlin, Veltrava,
## later chapters: data/board/c17_board.json "places"), steel pins for Alexei's finds, brass pins for Konrad's,
## the finder's initials on the card. Red threads (data/board/c17_links.json) join items that prove the same link —
## only ever between owned items; the focused card's threads light up and carry their one-line caption. A typed
## sheet „Was die Akte bisher zeigt“ grows with milestones (c17_board.json "summary": owned items, completed
## objectives, events, recorded choices). Items not owned yet are empty pins with „?“ (no names, no pictures); a
## place the story has not reached shows only a compact column of „?“ pins under „?“.
## Opened from the journal tab „Akte“ (scripts/ui/journal.gd). Never changes Story state: it only reads
## Story.inventory / completed_objectives / has_event / choice_history / current_scene; Enter opens the existing,
## read-only InspectView. Inside a memory (Game.memory_mode) it shows the file as it was then: only what lies at or
## before the remembered scene in the story chain counts (items, objectives, events, choices), stamped
## „Erinnerung · place · month“.
## Arrows / WASD / D-pad / left stick move between cards (spatial, `neighbor()`), Enter / Space / A opens the
## close-up, Esc / B goes back, J closes board and journal, Page Up/Down or the right stick scroll the sheet; mouse
## hover focuses, click opens. Text 100/125/150 % (cards, labels and strips grow; the cork pans to the focused
## card when the board no longer fits), high contrast (dark cork, black ink, thick bright threads). The detail strip
## never cuts a name or a note (its left column widens for a long line, the strip grows only when that is not
## enough), and the sheet's first visible line is always whole (it stops on lines, also when paging).

signal inspect_requested(item_id: String)
signal card_focused(item_id: String)

const LINKS_PATH := "res://data/board/c17_links.json"
const BOARD_PATH := "res://data/board/c17_board.json"
const SCENES_PATH := "res://data/v3/scenes.json"
const ART := "res://assets/ui/board/"
const THUMB_DIR := "res://assets/ui/board/thumbs/"

const SCREEN := Vector2(1920, 1080)
const FRAME_RECT := Rect2(24, 12, 1872, 990)    # wooden frame (outer); the cork starts 30 px inside
const FRAME_M := 30.0
const INNER := 12.0                              # cork padding inside the frame
const THUMB := Vector2(162, 72)                  # card picture: 54x24 art pixels at x3
const PAD := 6.0
const GAP := 9.0
const GROUP_GAP := 33.0
const LABEL_BASE := 20
const CARD_MIN_W := 180.0
const CARD_MAX_W := 264.0
const UNKNOWN_CELL := Vector2(54, 66)
const UNKNOWN_GAP := 6.0
const BIG := 1 << 20
const PIN_SIZE := Vector2(27, 30)
const PIN_KNOT := Vector2(10.5, 9.0)
const NOTE_LIFT := 3.0                           # a sheet stop lies this far above a line's box (umlauts stay whole)

const INK := Color("1a1c2a")
const INK_DIM := Color("4d4a42")
const PAPER := Color("e6dec2")
const PAPER_L := Color("f5efda")
const RED := Color("a8382e")
const THREAD := Color("b23a2e")
const THREAD_HOT := Color("e2503c")
const THREAD_SHADOW := Color(0.02, 0.01, 0.0, 0.42)
const THREAD_HC := Color("ff3b2f")
const STEEL_INK := Color("2b3c50")
const BRASS_INK := Color("7a5228")

var model: Dictionary = {}
var state: Dictionary = {}
var layout_info: Dictionary = {}
var focused_item := ""
var last_inspected := ""
var memory_scene := ""
var card_size := Vector2(CARD_MIN_W, 160)
var new_items: Array = []          # pinned since the last opening in this session (see _mark_seen)

var _ctx: Dictionary = {}
var _cards: Dictionary = {}        # item -> Button
var _shadows: Dictionary = {}      # item -> ColorRect
var _pins: Dictionary = {}         # item -> Vector2 (pin top-left in canvas coordinates)
var _cork: TextureRect
var _frame: Panel
var _title: Label
var _subtitle: Label
var _counts: Label
var _note: PanelContainer
var _note_scroll: ScrollContainer
var _note_list: VBoxContainer
var _note_kicker: Label
var _note_stamp: Label
var _note_pin: TextureRect
var _regions: Dictionary = {}    # node name -> Rect2 (absolute; panels never shrink on their own)
var _scroll: ScrollContainer
var _canvas: Control
var _layer_back: Control
var _layer_cards: Control
var _threads: Control
var _layer_pins: Control
var _layer_tags: Control
var _strip: PanelContainer
var _d_left: VBoxContainer
var _d_kicker: Label
var _d_name: Label
var _d_threads: Label
var _d_note: Label
var _d_note_below: Label
var _d_who: Label
var _d_threads_kicker: Label
var _strip_base := 0.0             # left column width at the 1 : 1.4 split
var _strip_wide := 0.0             # widest left column (64 %) for a card whose line would not fit the base width
var _note_pad: MarginContainer
var _controls: Control
var _head_plate: PanelContainer
var _count_plate: PanelContainer
var _thread_t := 1.0
var _note_to_end := true
var _tween: Tween


# ================================================================ data (static, testable without a scene)
static func _json(path: String) -> Dictionary:
	var d = Kit.json(path)
	return d if d is Dictionary else {}


## Story scenes in chain order (start_scene → next_scene …), unknown leftovers appended.
static func scene_chain() -> Array:
	var d := _json(SCENES_PATH)
	var by_id := {}
	for s in d.get("scenes", []):
		if s is Dictionary and s.has("id"):
			by_id[str(s["id"])] = s
	var out: Array = []
	var cur := str(d.get("start_scene", ""))
	while cur != "" and by_id.has(cur) and not (cur in out):
		out.append(cur)
		var nx = by_id[cur].get("next_scene")
		cur = str(nx) if nx != null else ""
	for id in by_id:
		if not (id in out):
			out.append(id)
	return out


## Every static lookup the board needs, built once per opening: chain ranks, scene defs, objective → scene,
## event → scene, the items of data/v3/items.json, the board and link data.
static func data_context() -> Dictionary:
	var chain := scene_chain()
	var rank := {}
	for i in chain.size():
		rank[str(chain[i])] = i
	var scenes := {}
	for s in _json(SCENES_PATH).get("scenes", []):
		if s is Dictionary and s.has("id"):
			scenes[str(s["id"])] = s
	var obj_scene := {}
	var event_scene := {}
	for q in Kit.quests():
		var qs := str(q.get("scene", ""))
		for o in q.get("objectives", []):
			obj_scene[str(o.get("id", ""))] = qs
		if q.get("completion_event") != null:
			event_scene[str(q["completion_event"])] = qs
	for id in scenes:
		var ev = scenes[id].get("exit_on_event")
		if ev != null and str(ev) != "" and not event_scene.has(str(ev)):
			event_scene[str(ev)] = str(id)
	var items: Array = []
	for it in Kit.all_items():
		if it is Dictionary and it.has("id"):
			items.append(it)
	return {"chain": chain, "rank": rank, "scenes": scenes, "obj_scene": obj_scene, "event_scene": event_scene,
		"items": items, "board": _json(BOARD_PATH), "links": _json(LINKS_PATH)}


static func _rank_of_scene(ctx: Dictionary, scene: String) -> int:
	return int(ctx["rank"].get(scene, BIG - 1))


static func item_scene(ctx: Dictionary, id: String) -> String:
	for it in ctx["items"]:
		if str(it["id"]) == id:
			return str(it.get("scene", ""))
	return ""


## The plain facts the board reads (never a Story reference is kept): owned items, completed objectives, happened
## events, recorded choices, how far the story has come (`reached`, a chain rank) and the memory cut-off (`cutoff`:
## only what lies at or before that rank counts). memory_scene "" = the present.
static func snapshot(story: Object, mem_scene := "", ctx := {}) -> Dictionary:
	if ctx.is_empty():
		ctx = data_context()
	var st := {"owned": {}, "objectives": {}, "events": {}, "choices": {}, "reached": -1, "cutoff": BIG,
		"memory_scene": ""}
	if story != null:
		if story.has_method("inventory"):
			for id in story.inventory():
				st["owned"][str(id)] = true
		if story.has_method("completed_objectives"):
			for id in story.completed_objectives():
				st["objectives"][str(id)] = true
		if story.has_method("has_event"):
			for ev in _events_used(ctx):
				if story.has_event(ev):
					st["events"][ev] = true
		if story.has_method("choice_history"):
			var ch = story.choice_history()
			if ch is Dictionary:
				for k in ch:
					var v = ch[k]
					st["choices"][str(k)] = str(v.get("choice", v.get("choice_id", ""))) if v is Dictionary else str(v)
		var cur = story.get("current_scene")
		if cur != null and ctx["rank"].has(str(cur)):
			st["reached"] = int(ctx["rank"][str(cur)])
	if mem_scene != "" and ctx["rank"].has(mem_scene):
		st["cutoff"] = int(ctx["rank"][mem_scene])
		st["reached"] = st["cutoff"]
		st["memory_scene"] = mem_scene
	return st


static func _events_used(ctx: Dictionary) -> Array:
	var out: Array = ctx["event_scene"].keys()
	var whens: Array = []
	for g in ctx["links"].get("groups", []):
		whens.append(g.get("when"))
	for k in ["summary", "looks"]:
		for m in ctx["board"].get(k, []):
			whens.append(m.get("when"))
	for w in whens:
		if w is Dictionary and w.get("events") is Array:
			for e in w["events"]:
				if not (str(e) in out):
					out.append(str(e))
	return out


static func owned_now(st: Dictionary, ctx: Dictionary, id: String) -> bool:
	return st["owned"].has(id) and _rank_of_scene(ctx, item_scene(ctx, id)) <= int(st["cutoff"])


## Board conditions (all must hold): items / any_items (owned evidence), objectives (completed), events (happened),
## "choice.<objective>": "<id>" | "!<id>". Inside a memory only facts of scenes up to the remembered one count.
## Unknown keys never hold (tests reject them in the data).
static func holds(when, st: Dictionary, ctx: Dictionary) -> bool:
	if when == null:
		return true
	if not (when is Dictionary):
		return false
	var cut := int(st["cutoff"])
	for k in when:
		var key := str(k)
		var v = when[k]
		if key == "items" or key == "any_items":
			if not (v is Array):
				return false
			var any := false
			var all := true
			for id in v:
				if owned_now(st, ctx, str(id)):
					any = true
				else:
					all = false
			if (key == "items" and not all) or (key == "any_items" and not any):
				return false
		elif key == "objectives" or key == "events":
			if not (v is Array):
				return false
			var have: Dictionary = st[key]
			var where: Dictionary = ctx["obj_scene"] if key == "objectives" else ctx["event_scene"]
			for id in v:
				if not have.has(str(id)) or _rank_of_scene(ctx, str(where.get(str(id), ""))) > cut:
					return false
		elif key.begins_with("choice."):
			var obj := key.substr(7)
			var got := ""
			if st["choices"].has(obj) and _rank_of_scene(ctx, str(ctx["obj_scene"].get(obj, ""))) <= cut:
				got = str(st["choices"][obj])
			var want := str(v)
			if want.begins_with("!"):
				if got == want.substr(1):
					return false
			elif got != want:
				return false
		else:
			return false
	return true


## The board's content for a snapshot: places (columns, story order) with their slots, the threads between owned
## items, the milestones of the running summary and the counters. Pure data — no nodes, no Story calls.
static func build_model(st: Dictionary, ctx := {}) -> Dictionary:
	if ctx.is_empty():
		ctx = data_context()
	var board: Dictionary = ctx["board"]
	var place_of := {}
	var place_defs := {}
	for p in board.get("places", []):
		if p is Dictionary and p.has("id"):
			place_defs[str(p["id"])] = p
			for s in p.get("scenes", []):
				place_of[str(s)] = str(p["id"])
	var groups := {}
	var order: Array = []
	var owned_n := 0
	for it in ctx["items"]:
		var id := str(it["id"])
		var scene := str(it.get("scene", ""))
		var pid: String = place_of.get(scene, "scene:" + scene)
		if not groups.has(pid):
			var g := {"id": pid, "title_key": "", "rank": BIG, "known": false, "slots": [], "finders": []}
			if place_defs.has(pid):
				g["title_key"] = str(place_defs[pid].get("title_key", ""))
				for s in place_defs[pid].get("scenes", []):
					g["rank"] = mini(int(g["rank"]), _rank_of_scene(ctx, str(s)))
			else:
				g["title_key"] = str(ctx["scenes"].get(scene, {}).get("title_key", ""))
			groups[pid] = g
			order.append(pid)
		var g2: Dictionary = groups[pid]
		g2["rank"] = mini(int(g2["rank"]), _rank_of_scene(ctx, scene))
		var who := str(ctx["scenes"].get(scene, {}).get("protagonist", ""))
		var slot := {"item": id, "scene": scene, "owned": owned_now(st, ctx, id), "who": who,
			"category": str(it.get("category", "document")), "name_key": str(it.get("name_key", "")),
			"look": "", "note_key": ""}
		if slot["owned"]:
			owned_n += 1
			for lk in board.get("looks", []):
				if lk is Dictionary and str(lk.get("item", "")) == id and holds(lk.get("when"), st, ctx):
					slot["look"] = str(lk.get("look", ""))
					slot["note_key"] = str(lk.get("note_key", ""))
					break
		g2["slots"].append(slot)
	var places: Array = []
	for pid in order:
		var g: Dictionary = groups[pid]
		var any_owned := false
		for s in g["slots"]:
			if s["owned"]:
				any_owned = true
				if s["who"] != "" and s["who"] != "none" and not (s["who"] in g["finders"]):
					g["finders"].append(s["who"])
		g["known"] = any_owned or (int(g["rank"]) <= int(st["reached"]))
		places.append(g)
	places.sort_custom(func(a, b): return int(a["rank"]) < int(b["rank"]))
	# every place the story has not reached becomes ONE compact column of „?“ pins (how many places lie ahead
	# stays as unknown as their names)
	var known_places: Array = []
	var ahead := {"id": "unknown", "title_key": "", "rank": BIG, "known": false, "slots": [], "finders": []}
	for g in places:
		if g["known"]:
			known_places.append(g)
		else:
			ahead["rank"] = mini(int(ahead["rank"]), int(g["rank"]))
			ahead["slots"].append_array(g["slots"])
	if not (ahead["slots"] as Array).is_empty():
		known_places.append(ahead)
	places = known_places
	var threads: Array = []
	for grp in ctx["links"].get("groups", []):
		if not (grp is Dictionary) or not holds(grp.get("when"), st, ctx):
			continue
		var chain: Array = []
		for id in grp.get("items", []):
			if owned_now(st, ctx, str(id)):
				chain.append(str(id))
		for i in range(chain.size() - 1):
			threads.append({"group": str(grp.get("id", "")), "caption_key": str(grp.get("caption_key", "")),
				"a": chain[i], "b": chain[i + 1]})
	var summary: Array = []
	var slots_used := {}
	for m in board.get("summary", []):
		if not (m is Dictionary):
			continue
		var slot_id := str(m.get("slot", ""))
		if slot_id != "" and slots_used.has(slot_id):
			continue
		if holds(m.get("when"), st, ctx):
			summary.append({"id": str(m.get("id", "")), "text_key": str(m.get("text_key", ""))})
			if slot_id != "":
				slots_used[slot_id] = true
	return {"places": places, "threads": threads, "summary": summary, "owned": owned_n,
		"total": (ctx["items"] as Array).size(), "memory_scene": str(st.get("memory_scene", ""))}


## Snapshot + model of the running game (Story autoload; a memory of Game when one is running).
static func live_model() -> Dictionary:
	var ctx := data_context()
	return build_model(snapshot(Kit.svc("Story"), game_memory_scene(), ctx), ctx)


static func game_memory_scene() -> String:
	var g := Kit.svc("Game")
	if g != null and g.get("memory_mode") == true:
		return str(g.get("memory_scene"))
	return ""


## Card label: a short handwritten title (board.short.<item>) or the item's name.
static func card_label(id: String, name_key := "") -> String:
	var k := "board.short." + id
	if Kit.has_key(k):
		return Kit.t(k)
	return Kit.t(name_key) if name_key != "" else id


## Card rectangles (canvas coordinates) for a model: known places get full card slots in columns (filled top to
## bottom, story order), places not reached yet a compact column of „?“ markers. Pure arithmetic on the 3-px grid.
static func compute_layout(m: Dictionary, h: float, card: Vector2, header_h: float, header_w := {}) -> Dictionary:
	var rects := {}
	var compact := {}
	var heads: Array = []
	var x := 0.0
	for g in m.get("places", []):
		var slots: Array = g["slots"]
		var n := slots.size()
		if n == 0:
			continue
		var gw := 0.0
		if g["known"]:
			var rows := maxi(1, int(floor((h - header_h + GAP) / (card.y + GAP))))
			var cols := int(ceil(float(n) / float(rows)))
			rows = int(ceil(float(n) / float(cols)))
			for i in n:
				var c := i / rows
				var r := i % rows
				rects[str(slots[i]["item"])] = Rect2(x + c * (card.x + GAP), header_h + r * (card.y + GAP), card.x, card.y)
			gw = cols * card.x + (cols - 1) * GAP
		else:
			var rows2 := maxi(1, int(floor((h - header_h + UNKNOWN_GAP) / (UNKNOWN_CELL.y + UNKNOWN_GAP))))
			var cols2 := int(ceil(float(n) / float(rows2)))
			rows2 = int(ceil(float(n) / float(cols2)))
			for i in n:
				var c2 := i / rows2
				var r2 := i % rows2
				compact[str(slots[i]["item"])] = Rect2(x + c2 * (UNKNOWN_CELL.x + UNKNOWN_GAP),
					header_h + r2 * (UNKNOWN_CELL.y + UNKNOWN_GAP), UNKNOWN_CELL.x, UNKNOWN_CELL.y)
			gw = cols2 * UNKNOWN_CELL.x + (cols2 - 1) * UNKNOWN_GAP
		gw = maxf(gw, _snap(float(header_w.get(str(g["id"]), 0.0))))
		heads.append({"place": str(g["id"]), "rect": Rect2(x, 0, gw, header_h)})
		x += gw + GROUP_GAP
	return {"cards": rects, "compact": compact, "heads": heads, "size": Vector2(maxf(0.0, x - GROUP_GAP), h)}


static func _snap(v: float) -> float:
	return ceilf(v / 3.0) * 3.0


## Spatial navigation: the card whose centre lies best in direction `dir` from card `from` (a cone of about
## ±65°, distance along the direction plus 2.5 × the sideways offset), or -1.
static func neighbor(centers: Array, from: int, dir: Vector2) -> int:
	if from < 0 or from >= centers.size():
		return -1
	var best := -1
	var best_score := INF
	var o: Vector2 = centers[from]
	for i in centers.size():
		if i == from:
			continue
		var v: Vector2 = centers[i] - o
		var along := v.dot(dir)
		if along < 6.0:
			continue
		var side := absf(v.x * dir.y - v.y * dir.x)
		if side > along * 2.2:
			continue
		var score := along + side * 2.5
		if score < best_score:
			best_score = score
			best = i
	return best


## Thread curve between two pins: a quadratic sag (gravity), sampled on the 3-px grid. t_max < 1 draws a part.
static func thread_points(a: Vector2, b: Vector2, t_max := 1.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	var d := a.distance_to(b)
	var sag := clampf(d * 0.11, 6.0, 66.0)
	var ctl := (a + b) * 0.5 + Vector2(0, sag)
	var steps := maxi(2, int(d / 2.0))
	var last := Vector2(-99999, -99999)
	for i in steps + 1:
		var t := float(i) / float(steps)
		if t > t_max:
			break
		var p := a.lerp(ctl, t).lerp(ctl.lerp(b, t), t)
		var q := Vector2(floorf(p.x / 3.0) * 3.0, floorf(p.y / 3.0) * 3.0)
		if q != last:
			out.append(q)
			last = q
	return out


static func thread_mid(a: Vector2, b: Vector2, t := 0.5) -> Vector2:
	var d := a.distance_to(b)
	var ctl := (a + b) * 0.5 + Vector2(0, clampf(d * 0.11, 6.0, 66.0))
	return a.lerp(ctl, t).lerp(ctl.lerp(b, t), t)


# ================================================================ scene
func _ready() -> void:
	pauses_game = true
	var st := Kit.svc("Story")
	if st != null and st.has_signal("state_replaced"):
		var cb := reset_seen.unbind(1)   # a new game or a load: nothing is „new“ on the next opening
		if not st.state_replaced.is_connected(cb):
			st.state_replaced.connect(cb)
	add_child(Kit.dimmer(0.95))
	_frame_rect_nodes()
	_controls = Control.new()
	_controls.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_controls)


func _frame_rect_nodes() -> void:
	_cork = TextureRect.new()
	_cork.stretch_mode = TextureRect.STRETCH_TILE
	_cork.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_cork.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cork.position = FRAME_RECT.position + Vector2(FRAME_M, FRAME_M) - Vector2(3, 3)
	_cork.size = FRAME_RECT.size - Vector2(FRAME_M, FRAME_M) * 2 + Vector2(6, 6)
	add_child(_cork)
	# header plate (title + subtitle) and counters
	_head_plate = PanelContainer.new()
	_head_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_head_plate)
	var hv := Kit.hbox(18)
	_head_plate.add_child(hv)
	_title = Kit.label(Kit.t("board.title").to_upper().replace("ß", "SS"), "StampLabel", 30)
	_title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hv.add_child(_title)
	_subtitle = Kit.label(Kit.t("board.subtitle"), "DimLabel", 22)
	_subtitle.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hv.add_child(_subtitle)
	_count_plate = PanelContainer.new()
	_count_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_count_plate)
	_counts = Kit.label("", "TypeDim", 20)
	_counts.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_count_plate.add_child(_counts)
	# summary sheet
	_note = PanelContainer.new()
	_note.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(_note)
	var nv := Kit.vbox(10)
	_note.add_child(nv)
	_note_kicker = Kit.label(Kit.t("board.summary.title").to_upper().replace("ß", "SS"), "PaperKicker")
	_note_kicker.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_note_kicker.custom_minimum_size.x = 300
	nv.add_child(_note_kicker)
	_note_stamp = Kit.wrap_label("", "StampLabel", 20)
	_note_stamp.custom_minimum_size.x = 300
	nv.add_child(_note_stamp)
	_note_scroll = ScrollContainer.new()
	_note_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_note_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	nv.add_child(_note_scroll)
	# the list sits in a margin whose bottom lets the sheet stop on a whole line at its end (_note_follow_end)
	_note_pad = MarginContainer.new()
	_note_pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_note_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		_note_pad.add_theme_constant_override(side, 0)
	_note_scroll.add_child(_note_pad)
	_note_list = Kit.vbox(12)
	_note_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_note_pad.add_child(_note_list)
	_note_scroll.get_v_scroll_bar().changed.connect(_note_follow_end)
	_note_pin = TextureRect.new()
	_note_pin.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_note_pin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_note_pin)
	# the canvas (pans when the board no longer fits)
	_scroll = ScrollContainer.new()
	_scroll.follow_focus = true
	_scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(_scroll)
	_canvas = Control.new()
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scroll.add_child(_canvas)
	_layer_back = _layer()
	_layer_cards = _layer()
	_threads = _layer()
	_threads.draw.connect(_draw_threads)
	_layer_pins = _layer()
	_layer_tags = _layer()
	# detail strip: left the place, the name and a decision note; right the red threads of the focused card. Nothing
	# in the left column is ever cut: the column widens for a long line (_left_width), its lines wrap beyond that and
	# the strip grows for them (_strip_layout).
	_strip = PanelContainer.new()
	_strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_strip)
	var sh := Kit.hbox(30)
	_strip.add_child(sh)
	_d_left = Kit.vbox(3)
	_d_left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_d_left.size_flags_stretch_ratio = 1.0
	sh.add_child(_d_left)
	_d_kicker = Kit.wrap_label("", "PaperKicker")
	Kit.scalable(_d_kicker, 19)
	_d_left.add_child(_d_kicker)
	_d_name = Kit.wrap_label("", "TypeHeading")
	Kit.scalable(_d_name, 27)
	_d_left.add_child(_d_name)
	var who_row := Kit.hbox(0)
	_d_left.add_child(who_row)
	_d_who = Kit.label("", "DimLabel")
	_d_who.add_theme_color_override("font_color", INK_DIM)
	Kit.scalable(_d_who, 19)
	who_row.add_child(_d_who)
	_d_note = Kit.label("", "DimLabel")      # the decision note beside the finder, when it fits there …
	_d_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_d_note.add_theme_color_override("font_color", RED)
	Kit.scalable(_d_note, 19)
	who_row.add_child(_d_note)
	_d_note_below = Kit.wrap_label("", "DimLabel")   # … else on its own lines below it
	_d_note_below.add_theme_color_override("font_color", RED)
	_d_note_below.visible = false
	Kit.scalable(_d_note_below, 19)
	_d_left.add_child(_d_note_below)
	var rule := ColorRect.new()
	rule.color = Color(0.69, 0.67, 0.58)
	rule.custom_minimum_size.x = 3
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sh.add_child(rule)
	var tv := Kit.vbox(3)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tv.size_flags_stretch_ratio = 1.4
	sh.add_child(tv)
	_d_threads_kicker = Kit.label("", "PaperKicker")
	Kit.scalable(_d_threads_kicker, 19)
	tv.add_child(_d_threads_kicker)
	_d_threads = Kit.wrap_label("", "TypeLabel")
	_d_threads.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_d_threads.custom_minimum_size.x = 120
	_d_threads.max_lines_visible = 2
	_d_threads.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	Kit.scalable(_d_threads, 18)
	tv.add_child(_d_threads)
	for k in ["note", "strip", "head", "counts"]:
		var c: Control = {"note": _note, "strip": _strip, "head": _head_plate, "counts": _count_plate}[k]
		c.item_rect_changed.connect(_keep_region.bind(k, c))
	_frame = Panel.new()
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_frame.position = FRAME_RECT.position
	_frame.size = FRAME_RECT.size
	add_child(_frame)


func _layer() -> Control:
	var c := Control.new()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.add_child(c)
	return c


func _tex(name: String) -> Texture2D:
	return Kit.optional_tex(ART + name)


func _sb9(name: String, m: float, content := -1.0) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = _tex(name)
	sb.texture_margin_left = m
	sb.texture_margin_top = m
	sb.texture_margin_right = m
	sb.texture_margin_bottom = m
	var cm := m if content < 0.0 else content
	sb.content_margin_left = cm
	sb.content_margin_top = cm
	sb.content_margin_right = cm
	sb.content_margin_bottom = cm
	return sb


func _hc() -> bool:
	return Kit.high_contrast()


# ================================================================ open / build
## opts (all optional): "story" (object with the Story read API; default the Story autoload), "memory_scene"
## (scene id; default Game's running memory). Builds the board from a fresh snapshot and shows it.
func open(opts := {}) -> void:
	_ctx = data_context()
	var story: Object = opts.get("story", Kit.svc("Story"))
	memory_scene = str(opts.get("memory_scene", game_memory_scene()))
	state = snapshot(story, memory_scene, _ctx)
	model = build_model(state, _ctx)
	new_items = _mark_seen(state)
	if not new_items.is_empty():
		focused_item = str(new_items[-1])
	rebuild()
	open_modal()


## Items pinned since the board was last open in this session („Neu“; the focus starts on the newest). Session
## only — the first opening after a start or a load marks nothing; a memory never marks or records anything.
static var _seen: Dictionary = {}
static var _seen_ready := false


static func _mark_seen(st: Dictionary) -> Array:
	var fresh: Array = []
	if str(st.get("memory_scene", "")) != "":
		return fresh
	for id in st["owned"]:
		if _seen_ready and not _seen.has(id):
			fresh.append(str(id))
		_seen[id] = true
	_seen_ready = true
	return fresh


static func reset_seen() -> void:
	_seen.clear()
	_seen_ready = false


## Rebuilds every node from `model` for the current text scale / contrast (also used by tests).
func rebuild() -> void:
	var ts := Kit.text_scale()
	var hc := _hc()
	_cork.texture = _tex("cork_hc.png" if hc else "cork.png")
	var fsb := _sb9("frame.png", FRAME_M)
	fsb.draw_center = false
	_frame.add_theme_stylebox_override("panel", fsb)
	var plate_sb := _sb9("note.png", 24.0, 18.0)
	plate_sb.content_margin_top = 6.0
	plate_sb.content_margin_bottom = 6.0
	_head_plate.add_theme_stylebox_override("panel", plate_sb)
	_count_plate.add_theme_stylebox_override("panel", _sb9("tag.png", 9.0, 9.0))
	_note.add_theme_stylebox_override("panel", _sb9("note.png", 24.0, 21.0))
	var strip_sb := _sb9("note.png", 24.0, 21.0)
	strip_sb.content_margin_top = 12.0
	strip_sb.content_margin_bottom = 9.0
	_strip.add_theme_stylebox_override("panel", strip_sb)
	_note_pin.texture = _tex("pin_red.png")
	_title.add_theme_font_size_override("font_size", int(round(30 * sqrt(ts))))
	_subtitle.text = Kit.t("board.memory.note") if memory_scene != "" else Kit.t("board.subtitle")
	_subtitle.add_theme_font_size_override("font_size", int(round(22 * sqrt(ts))))
	_subtitle.add_theme_color_override("font_color", INK_DIM if not hc else INK)
	_counts.add_theme_font_size_override("font_size", int(round(20 * sqrt(ts))))
	_counts.add_theme_color_override("font_color", INK)
	_counts.text = "%s  ·  %s" % [Kit.t("board.count.items", {"n": model.get("owned", 0), "total": model.get("total", 0)}),
		Kit.t("board.count.threads", {"k": (model.get("threads", []) as Array).size()})]
	_build_summary()
	_build_controls()
	_compute_regions()
	_apply_regions()
	_build_canvas((_regions["scroll"] as Rect2).size)
	if not focused_item.is_empty() and _cards.has(focused_item):
		_show_detail(focused_item)
	else:
		_show_detail(_first_card())
	_apply_regions()
	_apply_regions.call_deferred()


## Absolute regions at the design resolution 1920x1080 (text scale grows the strips and the sheet): header plate,
## counters, the summary sheet (left), the cork canvas (right), the detail strip (bottom).
func _compute_regions() -> void:
	var ts := Kit.text_scale()
	var inner := Rect2(FRAME_RECT.position + Vector2(FRAME_M + INNER, FRAME_M + INNER),
		FRAME_RECT.size - Vector2(FRAME_M + INNER, FRAME_M + INNER) * 2)
	var head := _head_plate.get_combined_minimum_size()
	var head_h := _snap(head.y)
	var cps := _count_plate.get_combined_minimum_size()
	var strip_h := _snap(120.0 * pow(ts, 0.75))
	var note_w := _snap(372.0 * pow(ts, 0.6))
	strip_h = maxf(strip_h, _snap(_strip_layout(inner.size.x)))
	_fit_threads(strip_h)
	var body_top := inner.position.y + head_h + 12.0
	var body_bottom := inner.end.y - strip_h - 12.0
	_regions = {
		"head": Rect2(inner.position, Vector2(_snap(head.x), head_h)),
		"counts": Rect2(Vector2(inner.end.x - _snap(cps.x), inner.position.y + _snap((head_h - cps.y) * 0.5)), Vector2(_snap(cps.x), _snap(cps.y))),
		"note": Rect2(Vector2(inner.position.x, body_top + 12.0), Vector2(note_w, body_bottom - body_top - 12.0)),
		"strip": Rect2(Vector2(inner.position.x, inner.end.y - strip_h), Vector2(inner.size.x, strip_h)),
		"scroll": Rect2(Vector2(inner.position.x + note_w + 24.0, body_top), Vector2(inner.end.x - (inner.position.x + note_w + 24.0), body_bottom - body_top)),
	}


## Detail strip columns for the file at the current text scale. The left column (place · spot, name, finder · note)
## keeps its 1 : 1.4 share while each of its lines fits on one line; a card with a longer line widens it just enough
## for that line (on the 3-px grid, at most 64 % -- the threads keep the rest). Returns the panel height every owned
## card needs: within the base height as long as every line fits that way; text that would still wrap makes the strip
## taller (the cork above it gives way, it is never overlapped).
func _strip_layout(strip_w: float) -> float:
	for l in [_d_kicker, _d_name, _d_who, _d_note, _d_note_below, _d_threads_kicker, _d_threads]:
		Kit.apply_text_scale(l)
	var sb := _strip.get_theme_stylebox("panel")
	var cm := sb.get_minimum_size() if sb != null else Vector2.ZERO
	var row := _d_left.get_parent() as BoxContainer
	var free := strip_w - cm.x - 3.0 - 2.0 * float(row.get_theme_constant("separation"))
	_strip_base = floorf(free / 2.4)
	_strip_wide = floorf(free * 0.64 / 3.0) * 3.0
	var texts: Array = []
	for g in model.get("places", []):
		for s in g["slots"]:
			if s["owned"]:
				texts.append(_detail_texts(str(s["item"])))
	if texts.is_empty():
		texts.append(_detail_texts(""))
	var tv := _d_threads.get_parent() as BoxContainer
	var h := text_height(_d_threads_kicker, "R") + float(tv.get_theme_constant("separation")) + text_height(_d_threads, "→\n→", 1e6)
	for t in texts:
		h = maxf(h, _left_height(t, _left_width(t)))
	return h + cm.y


## The threads show as many lines as the strip holds beside the left column (two at the base height).
func _fit_threads(strip_h: float) -> void:
	var sb := _strip.get_theme_stylebox("panel")
	var tv := _d_threads.get_parent() as BoxContainer
	var avail := strip_h - (sb.get_minimum_size().y if sb != null else 0.0) - text_height(_d_threads_kicker, "R") \
		- float(tv.get_theme_constant("separation"))
	var ls := float(_d_threads.get_theme_constant("line_spacing"))
	var pitch := text_height(_d_threads, "→") + ls
	_d_threads.max_lines_visible = maxi(2, int(floorf((avail + ls) / pitch)))


## The detail strip's texts for a card: place · spot (capitals), the full name, the finder and the decision note
## (id "" or a card not on the board: the empty file).
func _detail_texts(id: String) -> Dictionary:
	var s := _slot(id)
	if s.is_empty():
		return {"kicker": "", "name": Kit.t("board.summary.empty") if int(model.get("owned", 0)) == 0 else "", "who": "",
			"note": ""}
	var place := ""
	for g in model.get("places", []):
		for s2 in g["slots"]:
			if s2["item"] == id:
				place = _place_title(g)
	var spot_key := str(_ctx.get("board", {}).get("spots", {}).get(str(s["scene"]), ""))
	var parts: Array = [place]
	if spot_key != "":
		parts.append(Kit.t(spot_key))
	var nk := str(s.get("note_key", ""))
	return {"kicker": "  ·  ".join(parts).to_upper().replace("ß", "SS"),
		"name": Kit.t(str(s["name_key"])) if str(s["name_key"]) != "" else id,
		"who": Kit.t("board.found_by", {"who": Kit.char_name(str(s["who"]))}) if str(s["who"]) in Kit.PROTAGONISTS else "",
		"note": Kit.t(nk) if nk != "" else ""}


## The note as it stands beside the finder („gefunden von … · note“).
static func _inline_note(t: Dictionary) -> String:
	if str(t["note"]) == "":
		return ""
	return ("  ·  " if str(t["who"]) != "" else "") + str(t["note"])


## Width the left column needs to hold each of the card's lines on one line.
func _left_need(t: Dictionary) -> float:
	var w := maxf(line_width(_d_kicker, str(t["kicker"])), line_width(_d_name, str(t["name"])))
	w = maxf(w, line_width(_d_who, str(t["who"])) + line_width(_d_note, _inline_note(t)))
	return ceilf(w) + 3.0


## The left column's width for a card: its share, or just as wide as the card's longest line (at most _strip_wide).
func _left_width(t: Dictionary) -> float:
	var need := _left_need(t)
	return _strip_base if need <= _strip_base else minf(_snap(need), _strip_wide)


func _note_inline(t: Dictionary, w: float) -> bool:
	return str(t["note"]) == "" or line_width(_d_who, str(t["who"])) + line_width(_d_note, _inline_note(t)) <= w


## Height of the left column for the card's texts at the column width `w` -- the lines _show_detail lays out (an
## empty line is hidden there).
func _left_height(t: Dictionary, w: float) -> float:
	var inline := _note_inline(t, w)
	var who := str(t["who"])
	var beside := _inline_note(t) if inline else ""
	var rows: Array = [text_height(_d_name, str(t["name"]), w)]
	if str(t["kicker"]) != "":
		rows.append(text_height(_d_kicker, str(t["kicker"]), w))
	if who != "" or beside != "":
		rows.append(maxf(text_height(_d_who, who) if who != "" else 0.0, text_height(_d_note, beside) if beside != "" else 0.0))
	if not inline:
		rows.append(text_height(_d_note_below, str(t["note"]), w))
	var h := float(_d_left.get_theme_constant("separation")) * (rows.size() - 1)
	for r in rows:
		h += r
	return h


## Width of `text` on one line in the label `l` (its font, size and margins).
static func line_width(l: Label, text: String) -> float:
	if text == "":
		return 0.0
	var sb := l.get_theme_stylebox("normal")
	return l.get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, l.get_theme_font_size("font_size")).x \
		+ (sb.get_minimum_size().x if sb != null else 0.0)


## Height of `text` in the label `l` at the width `width` (a wrapping label breaks there; -1 = one line per paragraph),
## line by line as the Label shapes it -- a line with a fallback glyph (the arrow „→“) is taller than the font height.
static func text_height(l: Label, text: String, width := -1.0) -> float:
	var f := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var sb := l.get_theme_stylebox("normal")
	var m := sb.get_minimum_size() if sb != null else Vector2.ZERO
	if text == "":
		return f.get_height(fs) + m.y
	var p := TextParagraph.new()
	p.break_flags = TextServer.BREAK_MANDATORY
	if l.autowrap_mode != TextServer.AUTOWRAP_OFF and width > 0.0:
		p.width = maxf(1.0, width - m.x)
		p.break_flags = TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE | l.autowrap_trim_flags
	p.add_string(text, f, fs)
	var n := p.get_line_count()
	if l.max_lines_visible >= 0:
		n = mini(n, l.max_lines_visible)
	var h := m.y + maxf(0.0, n - 1.0) * float(l.get_theme_constant("line_spacing"))
	for i in n:
		h += p.get_line_size(i).y
	return h


## A panel that grew while its wrapped labels were measured at width 0 is put back into its region (deferred: never
## inside the resize itself; a panel whose content really needs more room keeps its minimum).
func _keep_region(k: String, c: Control) -> void:
	if _regions.has(k) and c.size != (_regions[k] as Rect2).size:
		_apply_regions.call_deferred()


func _apply_regions() -> void:
	if _regions.is_empty():
		return
	var pairs := {"head": _head_plate, "counts": _count_plate, "note": _note, "strip": _strip, "scroll": _scroll}
	for k in pairs:
		var c: Control = pairs[k]
		var r: Rect2 = _regions[k]
		c.position = r.position
		c.size = r.size
	var n: Rect2 = _regions["note"]
	_note_pin.position = Vector2(_snap(n.position.x + n.size.x * 0.5 - PIN_SIZE.x * 0.5), n.position.y - 12.0)
	_note_pin.size = PIN_SIZE


func _build_summary() -> void:
	_note_to_end = true
	for c in _note_list.get_children():
		_note_list.remove_child(c)    # gone from the measurement at once (_note_line_stops), freed later
		c.queue_free()
	_note_pad.add_theme_constant_override("margin_bottom", 0)
	var hc := _hc()
	_note_stamp.visible = memory_scene != ""
	if memory_scene != "":
		var mem := _memory_line()
		_note_stamp.text = mem.to_upper().replace("ß", "SS")
		Kit.scalable(_note_stamp, 19)
	var entries: Array = model.get("summary", [])
	if entries.is_empty():
		var e := Kit.wrap_label(Kit.t("board.summary.empty"), "TypeDim")
		Kit.scalable(e, 20)
		_note_list.add_child(e)
		return
	for i in entries.size():
		var row := Kit.hbox(9)
		var num := Kit.label("%d." % (i + 1), "TypeDim")
		Kit.scalable(num, 19)
		num.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		num.add_theme_color_override("font_color", RED if i == entries.size() - 1 else (INK if hc else INK_DIM))
		row.add_child(num)
		var l := Kit.wrap_label(Kit.t(str(entries[i]["text_key"])), "TypeLabel")
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.add_theme_constant_override("line_spacing", 2)
		Kit.scalable(l, 19)
		l.add_theme_color_override("font_color", INK)
		row.add_child(l)
		_note_list.add_child(row)


func _memory_line() -> String:
	var g := Kit.svc("Game")
	var info: Dictionary = {}
	if g != null and g.has_method("memory_info"):
		var mi = g.memory_info()
		if mi is Dictionary:
			info = mi
	var place := str(info.get("place", ""))
	var date := str(info.get("date", ""))
	if place == "":
		place = Kit.t("ui.memories.place." + memory_scene) if Kit.has_key("ui.memories.place." + memory_scene) else memory_scene
	if date == "" and Kit.has_key("ui.memories.date." + memory_scene):
		date = Kit.t("ui.memories.date." + memory_scene)
	return Kit.t("board.memory.stamp", {"place": place, "date": date})


func _label_font() -> Font:
	return Kit.font("fv_serif_italic")


## Card size for the owned labels at the current text scale: wide enough for the longest word, tall enough for the
## longest label (at most three lines), on the 3-px grid.
func measure_card() -> Vector2:
	var fs := int(round(LABEL_BASE * Kit.text_scale()))
	var f := _label_font()
	var w := CARD_MIN_W
	var texts: Array = []
	for g in model.get("places", []):
		for s in g["slots"]:
			if s["owned"]:
				texts.append(card_label(str(s["item"]), str(s["name_key"])))
	for t in texts:
		for word in str(t).split(" ", false):
			w = maxf(w, f.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 2.0 * PAD + 12.0)
	w = minf(_snap(w), CARD_MAX_W)
	var inner := w - 2.0 * PAD - 6.0
	var line_h := f.get_height(fs)
	var lh := line_h
	for t in texts:
		lh = maxf(lh, f.get_multiline_string_size(str(t), HORIZONTAL_ALIGNMENT_LEFT, inner, fs).y)
	lh = minf(lh, line_h * 3.0)
	return Vector2(w, _snap(PAD + THUMB.y + 6.0 + lh + PAD + 3.0))


## Place headers above their column: the place in red capitals, the finders in italics on the line below (a header
## never makes a one-card column wider than its card; the pins hang below the second line).
func _header_metrics() -> Dictionary:
	var ts := Kit.text_scale()
	var h := _snap((26.0 + 24.0) * ts + 12.0)
	var widths := {}
	var kf := _kicker_font()
	var df := _label_font()
	for g in model.get("places", []):
		var w := kf.get_string_size(_place_title(g), HORIZONTAL_ALIGNMENT_LEFT, -1, int(round(21 * ts))).x + 12.0
		var fl := _finder_line(g)
		if fl != "":
			w = maxf(w, df.get_string_size(fl, HORIZONTAL_ALIGNMENT_LEFT, -1, int(round(18 * ts))).x + 12.0)
		widths[str(g["id"])] = w
	return {"h": h, "w": widths}


func _kicker_font() -> Font:
	var f := get_theme_font("font", "PaperKicker")
	return f if f != null else Kit.font("fv_label")


func _place_title(g: Dictionary) -> String:
	if not g["known"]:
		return Kit.t("board.place.unknown")
	var k := str(g.get("title_key", ""))
	return (Kit.t(k) if k != "" else str(g["id"])).to_upper().replace("ß", "SS")


func _finder_line(g: Dictionary) -> String:
	if not g["known"]:
		return ""
	var names: Array = []
	for who in g.get("finders", []):
		names.append(Kit.char_name(str(who)))
	return " · ".join(names)


func _build_canvas(area: Vector2) -> void:
	for layer in [_layer_back, _layer_cards, _layer_pins, _layer_tags]:
		for c in layer.get_children():
			c.free()
	_cards.clear()
	_shadows.clear()
	_pins.clear()
	card_size = measure_card()
	var hm := _header_metrics()
	var lay_h := area.y - 12.0
	layout_info = compute_layout(model, lay_h, card_size, float(hm["h"]), hm["w"])
	var size: Vector2 = layout_info["size"]
	var csize := Vector2(maxf(size.x + 12.0, area.x - 12.0), maxf(size.y, lay_h))
	# centre the board when it is narrower than the cork
	var off := Vector2(maxf(0.0, _snap((area.x - 12.0 - size.x) * 0.5)), 3.0)
	_canvas.custom_minimum_size = csize
	_canvas.size = csize
	for layer in [_layer_back, _layer_cards, _threads, _layer_pins, _layer_tags]:
		layer.position = off
		layer.size = csize
	var hc := _hc()
	var ts := Kit.text_scale()
	# place headers
	var by_id := {}
	for g in model.get("places", []):
		by_id[str(g["id"])] = g
	for hd in layout_info["heads"]:
		var g: Dictionary = by_id[hd["place"]]
		var r: Rect2 = hd["rect"]
		var title := _place_title(g)
		var t := Kit.label(title, "PaperKicker")
		Kit.scalable(t, 21)
		t.add_theme_color_override("font_color", Color("f0c487") if not hc else Color("fff27a"))
		t.position = r.position
		_layer_back.add_child(t)
		var fl := _finder_line(g)
		if fl != "":
			var f := Kit.label(fl, "DimLabel")
			Kit.scalable(f, 18)
			f.add_theme_color_override("font_color", PAPER if not hc else Color.WHITE)
			f.position = r.position + Vector2(0, _snap(25.0 * ts))
			_layer_back.add_child(f)
	var slots := {}
	for g in model.get("places", []):
		for s in g["slots"]:
			slots[str(s["item"])] = s
	for id in layout_info["cards"]:
		var s: Dictionary = slots[id]
		var r: Rect2 = layout_info["cards"][id]
		if s["owned"]:
			_add_card(s, r)
		else:
			_add_reserved(r)
	for id in layout_info["compact"]:
		var r2: Rect2 = layout_info["compact"][id]
		var u := TextureRect.new()
		u.texture = _tex("unknown.png")
		u.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		u.mouse_filter = Control.MOUSE_FILTER_IGNORE
		u.position = r2.position
		u.size = r2.size
		u.tooltip_text = Kit.t("board.unknown")
		_layer_pins.add_child(u)
	_wire_focus_neighbors()
	_threads.queue_redraw()


func _card_style(s: Dictionary) -> StyleBoxTexture:
	var name := "card_paper.png"
	if str(s["look"]) == "burned":
		name = "card_burned.png"
	elif str(s["category"]) == "physical_clue":
		name = "card_photo.png"
	return _sb9(name, 15.0, PAD)


func _thumb_for(s: Dictionary) -> Texture2D:
	var id := str(s["item"])
	if str(s["look"]) != "":
		var tl := Kit.optional_tex(THUMB_DIR + id + "_" + str(s["look"]) + ".png")
		if tl != null:
			return tl
	var t := Kit.optional_tex(THUMB_DIR + id + ".png")
	if t != null:
		return t
	return Kit.optional_tex(THUMB_DIR + ("_physical_clue.png" if str(s["category"]) == "physical_clue" else "_document.png"))


func _add_card(s: Dictionary, r: Rect2) -> void:
	var id := str(s["item"])
	var hc := _hc()
	var sh := ColorRect.new()
	sh.color = Color(0.02, 0.01, 0.0, 0.42)
	sh.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sh.position = r.position + Vector2(6, 6)
	sh.size = r.size
	_layer_back.add_child(sh)
	_shadows[id] = sh
	var b := Button.new()
	b.name = "Card_" + id
	b.focus_mode = Control.FOCUS_ALL
	b.position = r.position
	b.size = r.size
	b.clip_contents = false
	var sb := _card_style(s)
	for st in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_stylebox_override("focus", _sb9("focus_hc.png" if hc else "focus.png", 9.0, 0.0))
	b.set_meta("item", id)
	b.tooltip_text = Kit.t(str(s["name_key"])) if str(s["name_key"]) != "" else id
	var th := TextureRect.new()
	th.texture = _thumb_for(s)
	th.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	th.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	th.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	th.clip_contents = true
	th.mouse_filter = Control.MOUSE_FILTER_IGNORE
	th.position = Vector2(_snap((r.size.x - THUMB.x) * 0.5), PAD)
	th.size = THUMB
	b.add_child(th)
	var frame := ReferenceRect.new()
	frame.border_color = Color(0, 0, 0, 0.35)
	frame.border_width = 1.0
	frame.editor_only = false
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.position = th.position
	frame.size = THUMB
	b.add_child(frame)
	var l := Kit.label(card_label(id, str(s["name_key"])), "DimLabel")
	l.add_theme_font_override("font", _label_font())
	l.add_theme_font_size_override("font_size", int(round(LABEL_BASE * Kit.text_scale())))
	l.add_theme_color_override("font_color", INK if not hc else Color.BLACK)
	l.add_theme_constant_override("line_spacing", 0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.max_lines_visible = 3
	l.position = Vector2(PAD + 3.0, PAD + THUMB.y + 4.0)
	l.size = Vector2(r.size.x - 2.0 * PAD - 6.0, r.size.y - (PAD + THUMB.y + 4.0) - PAD)
	b.add_child(l)
	# finder initials: a small ink mark in the picture's lower corner (steel blue / brass, never colour alone)
	var who := str(s["who"])
	if who in Kit.PROTAGONISTS:
		var chip := PanelContainer.new()
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.add_theme_stylebox_override("panel", _sb9("tag.png", 9.0, 3.0))
		var cl := Kit.label(Kit.t("board.initials." + who), "KickerLabel", int(round(15 * Kit.text_scale())))
		cl.add_theme_color_override("font_color", (STEEL_INK if who == "alexei" else BRASS_INK) if not hc else Color.BLACK)
		chip.add_child(cl)
		b.add_child(chip)
		chip.reset_size()
		var cs := chip.get_combined_minimum_size()
		chip.position = Vector2(th.position.x + THUMB.x - cs.x + 3.0, th.position.y + THUMB.y - cs.y + 3.0)
	b.mouse_entered.connect(_hover.bind(b))
	b.focus_entered.connect(_on_card_focus.bind(id))
	b.pressed.connect(inspect.bind(id))
	if id in new_items:
		var nt := PanelContainer.new()
		nt.name = "New"
		nt.mouse_filter = Control.MOUSE_FILTER_IGNORE
		nt.add_theme_stylebox_override("panel", _sb9("tag.png", 9.0, 4.0))
		var nl := Kit.label(Kit.t("board.new").to_upper().replace("ß", "SS"), "PaperKicker", int(round(16 * Kit.text_scale())))
		nl.add_theme_color_override("font_color", RED if not hc else Color.BLACK)
		nt.add_child(nl)
		b.add_child(nt)
		nt.position = Vector2(-6, -6)
	_layer_cards.add_child(b)
	_cards[id] = b
	# pin: top centre with a small deterministic offset, steel for Alexei, brass for Konrad
	var jitter := float((hash(id) % 5) - 2) * 3.0
	var pp := Vector2(_snap(r.position.x + r.size.x * 0.5 - PIN_SIZE.x * 0.5) + jitter, r.position.y - 9.0)
	_pins[id] = pp
	var pin := TextureRect.new()
	pin.texture = _tex("pin_konrad.png" if who == "konrad" else "pin_alexei.png")
	pin.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	pin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pin.position = pp
	pin.size = PIN_SIZE
	pin.set_meta("item", id)
	_layer_pins.add_child(pin)


func _add_reserved(r: Rect2) -> void:
	var g := Panel.new()
	g.mouse_filter = Control.MOUSE_FILTER_IGNORE
	g.add_theme_stylebox_override("panel", _sb9("ghost.png", 12.0, 0.0))
	g.position = r.position
	g.size = r.size
	g.modulate = Color(1, 1, 1, 0.9 if not _hc() else 0.6)
	_layer_back.add_child(g)
	var u := TextureRect.new()
	u.texture = _tex("unknown.png")
	u.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	u.mouse_filter = Control.MOUSE_FILTER_IGNORE
	u.position = Vector2(_snap(r.position.x + (r.size.x - UNKNOWN_CELL.x) * 0.5), r.position.y - 6.0)
	u.size = UNKNOWN_CELL
	u.tooltip_text = Kit.t("board.unknown")
	_layer_pins.add_child(u)


func _first_card() -> String:
	var best := ""
	var best_p := Vector2(INF, INF)
	for id in _cards:
		var p: Vector2 = (_cards[id] as Control).position
		if p.x < best_p.x - 1.0 or (absf(p.x - best_p.x) <= 1.0 and p.y < best_p.y):
			best_p = p
			best = id
	return best


## Card ids in a stable order and their centres (canvas coordinates) — the input of neighbor().
func card_centers() -> Dictionary:
	var ids: Array = _cards.keys()
	var centers: Array = []
	for id in ids:
		var c: Control = _cards[id]
		centers.append(c.position + c.size * 0.5)
	return {"ids": ids, "centers": centers}


## Godot's own focus neighbours follow the same spatial rule (mouse / tab users and any GUI navigation).
func _wire_focus_neighbors() -> void:
	var cc := card_centers()
	var ids: Array = cc["ids"]
	var dirs := {SIDE_LEFT: Vector2.LEFT, SIDE_RIGHT: Vector2.RIGHT, SIDE_TOP: Vector2.UP, SIDE_BOTTOM: Vector2.DOWN}
	for i in ids.size():
		var b: Control = _cards[ids[i]]
		for side in dirs:
			var j := neighbor(cc["centers"], i, dirs[side])
			b.set_focus_neighbor(side, b.get_path_to(_cards[ids[j]]) if j >= 0 else b.get_path_to(b))
		b.focus_next = b.get_path_to(_cards[ids[(i + 1) % ids.size()]])
		b.focus_previous = b.get_path_to(_cards[ids[(i - 1 + ids.size()) % ids.size()]])


## Moves the focus one card in `dir`; returns the new item ("" when nothing lies that way).
func move_focus(dir: Vector2) -> String:
	if _cards.is_empty():
		return ""
	var cc := card_centers()
	var ids: Array = cc["ids"]
	var from := ids.find(focused_item)
	if from < 0:
		focus_card(_first_card())
		return focused_item
	var j := neighbor(cc["centers"], from, dir)
	if j < 0:
		return ""
	focus_card(str(ids[j]))
	Kit.ui_sound("move")
	return focused_item


func focus_card(id: String) -> void:
	if not _cards.has(id):
		return
	var b: Button = _cards[id]
	if b.is_inside_tree() and b.is_visible_in_tree():
		b.grab_focus()
	if focused_item != id:
		_on_card_focus(id)


func _hover(b: Button) -> void:
	if is_open and b.is_visible_in_tree():
		b.grab_focus()


func _on_card_focus(id: String) -> void:
	var prev := focused_item
	focused_item = id
	for k in _shadows:
		var lifted: bool = k == id
		var sh: ColorRect = _shadows[k]
		var c: Control = _cards[k]
		sh.position = c.position + (Vector2(9, 12) if lifted else Vector2(6, 6))
		sh.color.a = 0.5 if lifted else 0.42
	_show_detail(id)
	_build_tags()
	_threads.queue_redraw()
	if prev != id:
		card_focused.emit(id)


func _slot(id: String) -> Dictionary:
	for g in model.get("places", []):
		for s in g["slots"]:
			if str(s["item"]) == id:
				return s
	return {}


## Threads that touch `id`: [{group, caption_key, other}].
func threads_of(id: String) -> Array:
	var out: Array = []
	for t in model.get("threads", []):
		if t["a"] == id:
			out.append({"group": t["group"], "caption_key": t["caption_key"], "other": t["b"]})
		elif t["b"] == id:
			out.append({"group": t["group"], "caption_key": t["caption_key"], "other": t["a"]})
	return out


## Detail strip of a card: place and spot, the full name, who found it (+ the decision note in red, beside the finder
## or on its own lines below); on the right the red threads of the card: „caption → partner, partner“, groups
## separated by „·“. The left column takes its share, or the width the card's longest line needs (_left_width).
func _show_detail(id: String) -> void:
	var tx := _detail_texts(id)
	var w := _left_width(tx)
	var inline := _note_inline(tx, w)
	# the wrapping labels get the column width as their minimum: they break at it at once, before any layout pass
	for c in [_d_left, _d_kicker, _d_name, _d_note_below]:
		(c as Control).custom_minimum_size.x = w
	_d_kicker.text = str(tx["kicker"])
	_d_kicker.visible = _d_kicker.text != ""
	_d_name.text = str(tx["name"])
	_d_who.text = str(tx["who"])
	_d_who.visible = _d_who.text != ""
	_d_note.text = _inline_note(tx) if inline else ""
	_d_note.visible = _d_note.text != ""
	(_d_who.get_parent() as Control).visible = _d_who.visible or _d_note.visible
	_d_note_below.text = "" if inline else str(tx["note"])
	_d_note_below.visible = _d_note_below.text != ""
	var s := _slot(id)
	if s.is_empty():
		_d_threads.text = ""
		return
	var by_group := {}
	var order: Array = []
	for t in threads_of(id):
		var g := str(t["group"])
		if not by_group.has(g):
			by_group[g] = {"caption": Kit.t(str(t["caption_key"])), "others": []}
			order.append(g)
		var os := _slot(str(t["other"]))
		by_group[g]["others"].append(card_label(str(t["other"]), str(os.get("name_key", ""))))
	if order.is_empty():
		_d_threads.text = Kit.t("board.detail.no_threads")
	else:
		var bits: Array = []
		for g in order:
			bits.append("%s → %s" % [by_group[g]["caption"], ", ".join(by_group[g]["others"])])
		_d_threads.text = "  ·  ".join(bits)
	_d_threads.add_theme_color_override("font_color", INK)
	_d_threads_kicker.text = (Kit.t("board.detail.threads") + (": %d" % order.size() if not order.is_empty() else "")).to_upper().replace("ß", "SS")


## Caption tags on the focused card's threads: a strip of tape on the thread wherever it crosses bare cork (tried
## from the middle outwards along the thread); a tag would never cover a card, a header or another tag — when no
## free spot exists the caption stays in the detail strip only. Returns the number of tags placed.
func _build_tags() -> int:
	for c in _layer_tags.get_children():
		c.free()
	if focused_item == "" or not _pins.has(focused_item):
		return 0
	var blocked: Array = []
	for id in layout_info.get("cards", {}):
		blocked.append((layout_info["cards"][id] as Rect2).grow(3.0))
	for id in layout_info.get("compact", {}):
		blocked.append(layout_info["compact"][id])
	for hd in layout_info.get("heads", []):
		blocked.append(hd["rect"])
	var hc := _hc()
	var n := 0
	for t in threads_of(focused_item):
		var other := str(t["other"])
		if not _pins.has(other):
			continue
		var a: Vector2 = _pins[focused_item] + PIN_KNOT
		var b: Vector2 = _pins[other] + PIN_KNOT
		var tag := PanelContainer.new()
		tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
		tag.add_theme_stylebox_override("panel", _sb9("tag.png", 9.0, 6.0))
		var l := Kit.label(Kit.t(str(t["caption_key"])), "KickerLabel")
		Kit.scalable(l, 16)
		l.add_theme_color_override("font_color", INK if not hc else Color.BLACK)
		tag.add_child(l)
		_layer_tags.add_child(tag)
		tag.reset_size()
		var sz := tag.get_combined_minimum_size()
		var spot := Rect2()
		for tt in [0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74]:
			var p := thread_mid(a, b, tt)
			var r := Rect2(Vector2(_snap(p.x - sz.x * 0.5), _snap(p.y - sz.y * 0.5)), sz)
			if r.position.x < 0.0 or r.end.x > _canvas.size.x or r.position.y < 0.0 or r.end.y > _canvas.size.y:
				continue
			if not _overlaps(r, blocked):
				spot = r
				break
		if spot.size == Vector2.ZERO:
			tag.free()
			continue
		tag.position = spot.position
		blocked.append(spot)
		n += 1
	return n


static func _overlaps(r: Rect2, list: Array) -> bool:
	for o in list:
		if (o as Rect2).intersects(r):
			return true
	return false


## Threads as 3-px pixels along a sagging curve: a soft shadow 6 px below, the quiet threads, then the focused card's
## threads on top — brighter and two pixels thick (high contrast: bright red, the focused card's threads 6 px).
func _draw_threads() -> void:
	var hc := _hc()
	for pass_i in 3:
		for t in model.get("threads", []):
			if not (_pins.has(t["a"]) and _pins.has(t["b"])):
				continue
			var is_hot: bool = focused_item != "" and (t["a"] == focused_item or t["b"] == focused_item)
			if (pass_i == 1 and is_hot) or (pass_i == 2 and not is_hot):
				continue
			var pts := thread_points(_pins[t["a"]] + PIN_KNOT, _pins[t["b"]] + PIN_KNOT, _thread_t)
			var col: Color
			if pass_i == 0:
				col = THREAD_SHADOW
			elif hc:
				col = THREAD_HC if is_hot or focused_item == "" else Color(THREAD_HC, 0.55)
			else:
				col = THREAD_HOT if is_hot else Color(THREAD, 0.62 if focused_item != "" else 0.9)
			var off := Vector2(0, 6) if pass_i == 0 else Vector2.ZERO
			var sq := 6.0 if hc and is_hot else 3.0
			for p in pts:
				_threads.draw_rect(Rect2(p + off, Vector2(sq, sq)), col)
				if pass_i == 2 and not hc:
					_threads.draw_rect(Rect2(p + Vector2(0, 3), Vector2(3, 3)), THREAD_HOT.darkened(0.42))


func _build_controls() -> void:
	for c in _controls.get_children():
		c.free()
	var pad := Kit.last_input_pad
	var pairs: Array
	if pad:
		pairs = [["LS", Kit.t("board.hint.move")], ["A", Kit.t("board.hint.view")], ["RS", Kit.t("board.hint.scroll")],
			["B", Kit.t("board.hint.back")]]
	else:
		pairs = [[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT) + "|" + Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN),
			Kit.t("board.hint.move")], [Kit.key_name(KEY_ENTER), Kit.t("board.hint.view")],
			[Kit.key_name(KEY_PAGEUP) + "|" + Kit.key_name(KEY_PAGEDOWN), Kit.t("board.hint.scroll")],
			[Kit.key_name(KEY_ESCAPE), Kit.t("board.hint.back")]]
	var row := Kit.controls_row(pairs)
	row.position = Vector2(0, FRAME_RECT.end.y + 14)
	row.size = Vector2(SCREEN.x, 50)
	_controls.add_child(row)


# ================================================================ modal behaviour
func _on_open() -> void:
	Kit.ui_sound("paper")
	_thread_t = 1.0
	if Kit.reduced_motion():
		return
	var i := 0
	for id in _cards:
		var c: Control = _cards[id]
		c.modulate.a = 0.0
		var tw := c.create_tween()
		tw.tween_interval(0.008 * i)
		tw.tween_property(c, "modulate:a", 1.0, 0.14)
		i += 1
	_thread_t = 0.0
	if _tween != null and _tween.is_valid():
		_tween.kill()
	_tween = create_tween()
	_tween.tween_interval(0.08 + 0.008 * i)
	_tween.tween_method(_set_thread_t, 0.0, 1.0, 0.4).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_tween.tween_callback(Kit.ui_sound.bind("card"))


func _set_thread_t(v: float) -> void:
	_thread_t = v
	_threads.queue_redraw()


func _on_close() -> void:
	if _tween != null and _tween.is_valid():
		_tween.kill()
	_thread_t = 1.0


func focus_default() -> void:
	var id := focused_item if _cards.has(focused_item) else _first_card()
	if id != "":
		focus_card(id)


func _on_contrast_changed() -> void:
	if is_open:
		rebuild()
		focus_default()


## Read-only close-up of the item (the existing InspectView path).
func inspect(id: String) -> void:
	if not _cards.has(id):
		return
	last_inspected = id
	Kit.ui_sound("confirm")
	inspect_requested.emit(id)
	if ui_root != null and ui_root.get("inspect") != null:
		ui_root.inspect.open(id)


func modal_input(event: InputEvent) -> bool:
	if event.is_action_pressed("journal"):
		close()
		if ui_root != null and ui_root.get("journal") != null and ui_root.journal.get("is_open") == true:
			ui_root.journal.close()
		return true
	var dirs := {"ui_left": Vector2.LEFT, "ui_right": Vector2.RIGHT, "ui_up": Vector2.UP, "ui_down": Vector2.DOWN,
		"move_left": Vector2.LEFT, "move_right": Vector2.RIGHT, "move_up": Vector2.UP, "move_down": Vector2.DOWN}
	for a in dirs:
		if InputMap.has_action(a) and event.is_action_pressed(a, true):
			move_focus(dirs[a])
			return true
	if event.is_action_pressed("ui_accept") or (InputMap.has_action("interact") and event.is_action_pressed("interact")):
		if focused_item != "":
			inspect(focused_item)
		return true
	if event is InputEventKey and event.pressed:
		var k := (event as InputEventKey).physical_keycode
		if k == KEY_PAGEDOWN or k == KEY_PAGEUP:
			scroll_note(1.0 if k == KEY_PAGEDOWN else -1.0)
			return true
	return false


## The sheet opens on its newest lines (the latest milestone carries the red number), and its first visible line is
## whole: the view stops on a line (_note_line_stops) at or after the point where the last line would touch the bottom,
## and a margin under the last entry makes that stop reachable. Scrolling by hand ends the following.
func _note_follow_end() -> void:
	if not _note_to_end or _note_scroll == null:
		return
	var bar := _note_scroll.get_v_scroll_bar()
	var content := _note_list.get_combined_minimum_size().y
	var stop := 0.0
	if content > bar.page + 0.5:
		stop = content - bar.page
		for s in _note_line_stops():
			if s >= content - bar.page - 0.5:
				stop = s
				break
	var pad := maxi(0, int(ceilf(stop + bar.page - content)))
	if _note_pad.get_theme_constant("margin_bottom") != pad:
		_note_pad.add_theme_constant_override("margin_bottom", pad)
	_note_scroll.scroll_vertical = int(roundf(stop))


## Where the sheet may stop so that its first visible line is whole: NOTE_LIFT px above the top of every line of the
## list (an umlaut stands a little above its line box; the line above ends inside its own box), in list coordinates.
## Measured from the labels as they are laid out now -- the scroll bar's range is measured from the same state.
func _note_line_stops() -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var y := 0.0
	var sep := float(_note_list.get_theme_constant("separation"))
	for c in _note_list.get_children():
		var ctl := c as Control
		if ctl == null or not ctl.visible:
			continue
		var l := ctl as Label
		if l == null:
			for cc in ctl.get_children():
				if cc is Label and (cc as Label).autowrap_mode != TextServer.AUTOWRAP_OFF:
					l = cc
		if l != null:
			var lsb := l.get_theme_stylebox("normal")
			var ly := y + (lsb.get_margin(SIDE_TOP) if lsb != null else 0.0)   # a row's text fills it from its top
			var ls := float(l.get_theme_constant("line_spacing"))
			for i in l.get_line_count():
				out.append(maxf(0.0, ly - NOTE_LIFT))
				ly += float(l.get_line_height(i)) + ls
		y += ctl.get_combined_minimum_size().y + sep
	return out


## Page Up / Down: about two thirds of the sheet, landing on a line stop (the first visible line stays whole).
func scroll_note(d: float) -> void:
	_note_to_end = false
	if _note_scroll == null:
		return
	var bar := _note_scroll.get_v_scroll_bar()
	var end := maxf(0.0, bar.max_value - bar.page)
	var target := clampf(_note_scroll.scroll_vertical + d * maxf(120.0, _note_scroll.size.y * 0.6), 0.0, end)
	var stop := 0.0
	for s in _note_line_stops():
		if s <= target + 0.5:
			stop = s
	_note_scroll.scroll_vertical = int(roundf(end if target >= end - 0.5 else stop))


func _process(delta: float) -> void:
	if not is_open or _note_scroll == null:
		return
	if ui_root != null and ui_root.has_method("top_modal") and ui_root.top_modal() != self:
		return   # the close-up lies on top
	var ry := Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y)
	if absf(ry) > 0.35:
		_note_to_end = false
		_note_scroll.scroll_vertical = int(_note_scroll.scroll_vertical + ry * 900.0 * delta)
