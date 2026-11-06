extends "res://scripts/ui/ui_modal.gd"
## Journal / dossier with seven paper index tabs: Ziele, Aufgaben, Beweise, Personen, Entscheidungen, Entdeckungen,
## Geschichte. Data comes from Story.journal() (objectives with state, evidence items, people met, decisions); the
## parser accepts arrays or dictionaries for every section and falls back to Story.objective_state/inventory/
## choice_history + data/v3 when journal() is missing. Locked objectives are never listed (no false promises).
## Exploration (§12, Explore autoload): "Entdeckungen" lists found entries per area with found/total and opens a
## find again in the DiscoveryView; "Geschichte" lists the real-history cards found so far (re-readable, archive
## style) and shows the unknown ones only as a count. The header shows the overall exploration progress.
## Side tasks (§12.9): "Aufgaben" lists the started tasks — open ones first with the current hint, then the
## finished ones — each with its place, summary and the steps done so far (re-readable in the DiscoveryView).
## Tasks nobody has asked for yet stay hidden; only the current place says that someone here still needs help.
## Q / E (LB / RB) switch tabs, J / Tab / Esc close. "Ansehen" opens the InspectView on top.
## Round 9 (owner: board, §12.12): the eighth tab „Akte“ is a file divider standing out of the sheet's right edge
## (the round-1 paper tab turned by 90°; outside the flow row, so the seven index tabs keep their size). Its page is
## the cover of „Die Akte C-17“: the folder, the counters, „Was die Akte bisher zeigt“ and „Pinnwand öffnen“, which
## opens the EvidenceBoard (scenes/ui/EvidenceBoard.tscn) on top. Inside a memory both show the file as it was then.

const TABS := ["objectives", "tasks", "evidence", "people", "decisions", "discoveries", "history", "board"]
## The index tabs of the flow row (the board tab is the vertical divider on the sheet's right edge).
const ROW_TABS := ["objectives", "tasks", "evidence", "people", "decisions", "discoveries", "history"]
const BOARD_SCENE := "res://scenes/ui/EvidenceBoard.tscn"
const BOARD_SCRIPT := "res://scripts/ui/evidence_board.gd"
const VTAB_DIR := "res://assets/ui/board/"

var suppress_toasts := true
var current_tab := "objectives"
var _tab_buttons: Dictionary = {}
var _sheet: PanelContainer
var _body: Control
var _subtitle: Label
var _progress: Label
var _data: Dictionary = {}
var _group := ButtonGroup.new()
var _tab_counts: Dictionary = {}    # tab id -> counter shown on the index tab (0 = none)
var board: Control = null           # EvidenceBoard, instanced on first use under UIRoot (or beside the journal)
var _vtab_label: Label


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.74))
	var root := Kit.vbox(0)
	Kit.full_rect(root)
	root.offset_left = 210
	root.offset_right = -210
	root.offset_top = 54
	root.offset_bottom = -54
	add_child(root)
	var head := Kit.hbox(20)
	root.add_child(head)
	var title := Kit.label(Kit.t("ui.journal.title"), "HeadingLabel")
	head.add_child(title)
	var right := Kit.vbox(4)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(right)
	_subtitle = Kit.label("", "DimLabel", 26)
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(_subtitle)
	_progress = Kit.label("", "HintLabel")
	_progress.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(_progress)
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 18))
	# round 8: a flow row -- when seven tabs with late-game counters do not fit at a readable size they wrap onto
	# a second row of index tabs instead of shrinking to 16 px
	var tabs := HFlowContainer.new()
	tabs.add_theme_constant_override("h_separation", 6)
	tabs.add_theme_constant_override("v_separation", 4)
	var pad := Control.new()
	pad.custom_minimum_size.x = 30
	tabs.add_child(pad)
	root.add_child(tabs)
	for id in ROW_TABS:
		var b := Kit.button("", "PaperTabButton")
		b.toggle_mode = true
		b.button_group = _group
		b.pressed.connect(show_tab.bind(id))
		tabs.add_child(b)
		_tab_buttons[id] = b
	_sheet = Kit.panel("PaperPanel")
	_sheet.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_sheet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_sheet)
	_tab_buttons["board"] = _make_board_tab()
	_sheet.item_rect_changed.connect(_place_board_tab)
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 12))
	root.add_child(Kit.controls_row([["Q|E", Kit.t("ui.hint.tabs")],
		[Kit.action_key_text("journal") + "|" + Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]]))


func open(tab := "") -> void:
	_data = collect()
	if tab != "" and tab in TABS:
		current_tab = tab
	_update_tab_titles()
	var who = Kit.svc("Story").get("active_character") if Kit.svc("Story") != null else null
	var scene = Kit.svc("Story").get("current_scene") if Kit.svc("Story") != null else null
	var parts: Array = []
	if who != null and str(who) != "" and str(who) != "none":
		parts.append(Kit.char_name(str(who)))
	var q := Kit.quest_for_scene(str(scene)) if scene != null else {}
	if q.has("title_key"):
		parts.append(Kit.t(str(q["title_key"])))
	_subtitle.text = "  ·  ".join(parts)
	var pr := Kit.explore_progress()
	_progress.text = Kit.t("ui.journal.progress", {"n": pr["found"], "total": pr["total"], "h": pr["cards_found"],
		"ht": pr["cards_total"]}).to_upper().replace("ß", "SS") if int(pr["total"]) > 0 else ""
	_progress.visible = _progress.text != ""
	open_modal()
	show_tab(current_tab)
	_vtab_style()
	_place_board_tab.call_deferred()


func _update_tab_titles() -> void:
	var pr := Kit.explore_progress()
	for id in TABS:
		var n: int = (_data.get(id, []) as Array).size() if _data.get(id, []) is Array else 0
		if id == "objectives":
			n = 0
			for o in _data.get("objectives", []):
				if str(o.get("state", "")) == "available":
					n += 1
		elif id == "discoveries":
			n = int(pr["found"])
		elif id == "history":
			n = int(pr["cards_found"])
		elif id == "tasks":
			n = int((_ex_call("task_counts", [""], {"active": 0}) as Dictionary).get("active", 0))
		_tab_counts[id] = n
	_fit_tabs()


## Seven index tabs with their counters on the 1500 px sheet: the label size steps down from the theme's 24 px
## (counters three spaces after the label, as before) to TAB_MIN_FS; then the counters move closer and the lead-in
## before the first tab shrinks; if even that is too wide, the labels keep TAB_MIN_FS and the flow row wraps onto
## a second row of tabs (round 8: late-game counters used to shrink them to 16-17 px).
const TAB_MIN_FS := 20


func _fit_tabs() -> void:
	var row: Control = (_tab_buttons[TABS[0]] as Button).get_parent()
	var pad: Control = row.get_child(0) if row != null and row.get_child_count() > 0 else null
	var sep := 6.0
	if row is FlowContainer:
		sep = float(row.get_theme_constant("h_separation"))
	elif row is BoxContainer:
		sep = float(row.get_theme_constant("separation"))
	for variant in [["   ", 30.0, [24, 22, 21, TAB_MIN_FS]], ["  ", 12.0, [TAB_MIN_FS]]]:
		var avail: float = 1500.0 - float(variant[1]) - sep * float(ROW_TABS.size())
		for fs in variant[2]:
			var total := 0.0
			for id in ROW_TABS:
				var b: Button = _tab_buttons[id]
				var n := int(_tab_counts.get(id, 0))
				b.text = Kit.t("ui.journal.tab." + id).to_upper().replace("ß", "SS") + ((str(variant[0]) + str(n)) if n > 0 else "")
				b.add_theme_font_size_override("font_size", int(fs))
				total += _tab_width(b, int(fs))
			if pad != null:
				pad.custom_minimum_size.x = float(variant[1])
			if total <= avail:
				return


## True when the index tabs currently need two rows (the flow row wraps).
func tabs_wrapped() -> bool:
	var row: Control = (_tab_buttons[TABS[0]] as Button).get_parent()
	if not (row is FlowContainer):
		return false
	var sep := float(row.get_theme_constant("h_separation"))
	var total := 0.0
	for c in row.get_children():
		if c is Button:
			total += _tab_width(c as Button, (c as Button).get_theme_font_size("font_size")) + sep
		elif c is Control:
			total += (c as Control).custom_minimum_size.x + sep
	return total - sep > 1500.0


## Width a tab needs at font size fs: measured text + the widest of its paper tab frames.
func _tab_width(b: Button, fs: int) -> float:
	var f: Font = b.get_theme_font("font", "PaperTabButton")
	var w := f.get_string_size(b.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x if f != null else 0.0
	var frame := 0.0
	for st in ["normal", "pressed", "hover", "hover_pressed", "focus"]:
		var sb: StyleBox = b.get_theme_stylebox(st, "PaperTabButton")
		if sb != null:
			frame = maxf(frame, sb.get_minimum_size().x)
	return w + frame


func show_tab(id: String) -> void:
	current_tab = id
	(_tab_buttons[id] as Button).button_pressed = true
	if _body != null:
		_body.queue_free()
	match id:
		"objectives":
			_body = _build_objectives()
		"tasks":
			_body = _build_tasks()
		"evidence":
			_body = _build_list_detail("evidence")
		"people":
			_body = _build_list_detail("people")
		"discoveries":
			_body = _build_discoveries()
		"history":
			_body = _build_history()
		"board":
			_body = _build_board_cover()
		_:
			_body = _build_decisions()
	_sheet.add_child(_body)
	if is_open:
		Kit.ui_sound("page")


func cycle_tab(d: int) -> void:
	var i := (TABS.find(current_tab) + d + TABS.size()) % TABS.size()
	show_tab(TABS[i])
	(_tab_buttons[TABS[i]] as Button).grab_focus()


# ================================================================ data
func collect() -> Dictionary:
	var out := {"objectives": [], "evidence": [], "people": [], "decisions": []}
	var j = Kit.call_svc("Story", "journal", [], null)
	if not (j is Dictionary):
		j = {}
	# objectives
	var objs = _first(j, ["objectives", "goals"])
	var seen := {}
	if objs is Array:
		for o in objs:
			var e := _norm_objective(o, "")
			if not e.is_empty():
				out["objectives"].append(e)
				seen[e["id"]] = true
	elif objs is Dictionary:
		for k in objs:
			var e := _norm_objective(objs[k], str(k))
			if not e.is_empty():
				out["objectives"].append(e)
				seen[e["id"]] = true
	if objs == null:
		for q in Kit.quests():
			for o in q.get("objectives", []):
				var st = Kit.call_svc("Story", "objective_state", [str(o["id"])], "locked")
				var e := _norm_objective({"id": o["id"], "state": st}, "")
				if not e.is_empty():
					out["objectives"].append(e)
	# evidence
	var ev = _first(j, ["evidence", "items", "inventory"])
	if ev == null:
		ev = Kit.call_svc("Story", "inventory", [], [])
	for x in _as_list(ev):
		var id := str(x.get("id", x.get("item", ""))) if x is Dictionary else str(x)
		if id == "":
			continue
		var d := Kit.item_def(id)
		out["evidence"].append({"id": id, "name": Kit.t(str(d["name_key"])) if d.has("name_key") else id,
			"desc": Kit.t(str(d["description_key"])) if d.has("description_key") else "",
			"category": str(d.get("category", "document"))})
	# people
	var pp = _first(j, ["people", "people_met", "persons", "characters"])
	var people_ids: Array = []
	if pp == null:
		for o in out["objectives"]:
			if o["state"] == "complete" and str(o.get("type", "")) == "dialogue":
				var conv := Kit.conversation(str(Kit.objective_def(o["id"]).get("dialogue_id", "")))
				for n in conv.get("nodes", []):
					var sp := str(n.get("speaker", ""))
					if sp != "" and not (sp in Kit.PROTAGONISTS) and not (sp in people_ids):
						people_ids.append(sp)
	else:
		for x in _as_list(pp):
			var pid := str(x.get("id", x.get("character", ""))) if x is Dictionary else str(x)
			if pid != "" and not (pid in people_ids):
				people_ids.append(pid)
	for pid in people_ids:
		out["people"].append({"id": pid, "name": Kit.char_name(pid), "role": Kit.char_role(pid)})
	# decisions
	var dec = _first(j, ["decisions", "choices", "choice_history"])
	if dec == null:
		dec = Kit.call_svc("Story", "choice_history", [], {})
	var pairs: Array = []
	if dec is Dictionary:
		for k in dec:
			var v = dec[k]
			pairs.append([str(k), str(v.get("choice", v.get("choice_id", v.get("id", "")))) if v is Dictionary else str(v)])
	elif dec is Array:
		for x in dec:
			if x is Dictionary:
				pairs.append([str(x.get("objective", x.get("objective_id", x.get("obj_id", "")))),
					str(x.get("choice", x.get("choice_id", "")))])
	for p in pairs:
		var od := Kit.objective_def(str(p[0]))
		var text: String = str(p[1])
		for c in od.get("choices", []):
			if str(c.get("id", "")) == p[1]:
				text = Kit.t(str(c.get("text_key", p[1])))
		var q: Dictionary = od.get("_quest", {})
		out["decisions"].append({"objective": p[0], "choice": p[1], "text": text,
			"prompt": Kit.t(str(od["text_key"])) if od.has("text_key") else "",
			"chapter": Kit.t(str(q["title_key"])) if q.has("title_key") else ""})
	return out


func _first(d: Dictionary, keys: Array):
	for k in keys:
		if d.has(k):
			return d[k]
	return null


func _as_list(v) -> Array:
	if v is Array:
		return v
	if v is Dictionary:
		var out: Array = []
		for k in v:
			out.append(v[k] if v[k] is Dictionary else str(k))
		return out
	return []


func _norm_objective(o, key: String) -> Dictionary:
	var id := key
	var st := ""
	var text := ""
	if o is Dictionary:
		id = str(o.get("id", o.get("objective_id", key)))
		st = str(o.get("state", o.get("status", "")))
		if o.has("text"):
			text = str(o["text"])
		elif o.has("text_key"):
			text = Kit.t(str(o["text_key"]))
		if st == "" and o.has("complete"):
			st = "complete" if bool(o["complete"]) else "available"
	else:
		st = str(o)
	if st == "" or st == "locked" or id == "":
		return {}
	var def := Kit.objective_def(id)
	if text == "":
		text = Kit.t(str(def["text_key"])) if def.has("text_key") else id
	var q: Dictionary = def.get("_quest", {})
	return {"id": id, "state": "complete" if st in ["complete", "completed", "done"] else "available",
		"text": text, "type": str(def.get("type", "")), "quest": str(q.get("id", "")),
		"chapter": Kit.t(str(q["title_key"])) if q.has("title_key") else ""}


# ================================================================ tab bodies
func _scroll() -> ScrollContainer:
	var s := ScrollContainer.new()
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return s


func _empty(key: String) -> Control:
	var l := Kit.label(Kit.t(key), "TypeDim", 28)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


func _build_objectives() -> Control:
	var objs: Array = _data.get("objectives", [])
	if objs.is_empty():
		return _empty("ui.journal.empty.objectives")
	var s := _scroll()
	var v := Kit.vbox(10)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(v)
	var chapter := "<none>"
	# open objectives first within each chapter, chapters in data order
	var order: Array = []
	for q in Kit.quests():
		order.append(str(q.get("id", "")))
	objs = objs.duplicate()
	objs.sort_custom(func(a, b):
		var qa := order.find(a["quest"])
		var qb := order.find(b["quest"])
		if qa != qb:
			return qa > qb   # current chapter (later quest) first
		return a["state"] == "available" and b["state"] != "available")
	for o in objs:
		if o["chapter"] != chapter:
			chapter = o["chapter"]
			if v.get_child_count() > 0:
				v.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
			var k := Kit.label(str(chapter).to_upper().replace("ß", "SS"), "PaperKicker")
			v.add_child(k)
		var row := Kit.hbox(18)
		var done: bool = o["state"] == "complete"
		var mark := Kit.sprite("icons/%s.png" % ("mark_done" if done else "mark_open"))
		mark.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		mark.custom_minimum_size = Vector2(27, 36)
		row.add_child(mark)
		var l := Kit.wrap_label(o["text"], "TypeLabel")
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		Kit.scalable(l, 28)
		if done:
			l.add_theme_color_override("font_color", Kit.C_INK_DIM)
		row.add_child(l)
		var tag := Kit.label(Kit.t("ui.journal.state." + str(o["state"])).to_upper().replace("ß", "SS"), "PaperKicker" if not done else "HintLabel", 19)
		if done:
			tag.add_theme_color_override("font_color", Kit.C_INK_DIM)
		tag.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		row.add_child(tag)
		v.add_child(row)
	return s


func _build_list_detail(kind: String) -> Control:
	var entries: Array = _data.get(kind, [])
	if entries.is_empty():
		return _empty("ui.journal.empty." + kind)
	# list | scrolling detail with the „Ansehen“ row pinned below it (_list_split): a long record (Lindner's card,
	# the tube slip) scrolls inside the sheet instead of pushing the sheet off the screen, also at 150 % text
	var parts := _list_split(470.0)
	var h: HBoxContainer = parts[0]
	var list: VBoxContainer = parts[1]
	var detail: VBoxContainer = parts[2]
	detail.add_theme_constant_override("separation", 16)
	var first: Button = null
	for e in entries:
		var b := Kit.button(str(e["name"]), "PaperListButton")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.icon = Kit.tex("res://assets/ui/icons/%s.png" % ("icon_evidence" if kind == "evidence" else "icon_person_ink"))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.focus_entered.connect(_show_detail.bind(detail, kind, e))
		b.mouse_entered.connect(b.grab_focus)
		if kind == "evidence":
			b.pressed.connect(_inspect.bind(str(e["id"])))
		list.add_child(b)
		if first == null:
			first = b
	_show_detail(detail, kind, entries[0])
	if first != null and is_open:
		first.grab_focus.call_deferred()
	return h


func _show_detail(detail: VBoxContainer, kind: String, e: Dictionary) -> void:
	for c in detail.get_children():
		c.queue_free()
	var act := _actions_of(detail)
	var sc := detail.get_parent() as ScrollContainer
	if sc != null:
		sc.scroll_vertical = 0
	if kind == "evidence":
		var doc := Kit.doc_for_item(str(e["id"]))
		var t2 := Kit.optional_tex(Kit.DOCS_DIR + doc + ".png") if doc != "" else null
		if t2 == null:
			t2 = Kit.optional_tex("res://assets/ui/board/thumbs/%s.png" % str(e["id"]))   # a clue without a document
		if t2 != null:
			# x2 while it fits; at 125 / 150 % text a tall picture drops to x1 so the text starts on the first screen
			var s := 2
			while s > 1 and (t2.get_width() * s > 640 or t2.get_height() * s > 330
					or (Kit.text_scale() > 1.01 and t2.get_height() * s > 240)):
				s -= 1
			var img := Kit.pixel_image(t2, s)
			img.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			if t2.get_width() > 640 or t2.get_height() > 330:
				var k := minf(640.0 / t2.get_width(), 330.0 / t2.get_height())
				img.custom_minimum_size = (t2.get_size() * k).floor()
			detail.add_child(img)
		var kick := Kit.label(Kit.t("ui.inspect.kicker." + str(e.get("category", "document"))).to_upper().replace("ß", "SS"), "PaperKicker")
		detail.add_child(kick)
		var n := Kit.wrap_label(str(e["name"]), "TypeHeading")
		Kit.scalable(n, 34)
		detail.add_child(n)
		var sep := HSeparator.new()
		sep.theme_type_variation = "PaperSeparator"
		detail.add_child(sep)
		var d := Kit.wrap_label(str(e["desc"]), "TypeLabel")
		Kit.scalable(d, 28)
		detail.add_child(d)
		var b := Kit.button(Kit.t("ui.journal.view"), "", 220)
		b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		b.pressed.connect(_inspect.bind(str(e["id"])))
		if act != null:
			act.add_child(b)
		else:
			detail.add_child(b)
	else:
		var row := Kit.hbox(28)
		detail.add_child(row)
		var frame := Kit.panel("PortraitPanel")
		frame.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var tex2 := _portrait_frame(str(e["id"]))
		var img := Kit.pixel_image(tex2, 2)
		img.custom_minimum_size = Vector2(224, 224)
		frame.add_child(img)
		row.add_child(frame)
		var v := Kit.vbox(12)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(v)
		var n := Kit.wrap_label(str(e["name"]), "TypeHeading")
		Kit.scalable(n, 34)
		v.add_child(n)
		var sep := HSeparator.new()
		sep.theme_type_variation = "PaperSeparator"
		v.add_child(sep)
		var d := Kit.wrap_label(str(e["role"]), "TypeLabel")
		Kit.scalable(d, 28)
		v.add_child(d)


func _portrait_frame(id: String) -> Texture2D:
	var t2 := Kit.optional_tex(Kit.CHAR_DIR + id + "/portrait.png")
	if t2 == null:
		return Kit.tex("res://assets/ui/portrait_placeholder.png")
	var meta = Kit.json(Kit.CHAR_DIR + id + "/portrait.json")
	var sz := Vector2i(112, 112)
	if meta is Dictionary and meta.get("size") is Array:
		sz = Vector2i(int(meta["size"][0]), int(meta["size"][1]))
	var at := AtlasTexture.new()
	at.atlas = t2
	at.region = Rect2(0, 0, sz.x, sz.y)
	return at


func _build_decisions() -> Control:
	var decs: Array = _data.get("decisions", [])
	if decs.is_empty():
		return _empty("ui.journal.empty.decisions")
	var s := _scroll()
	var v := Kit.vbox(12)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(v)
	v.add_theme_constant_override("separation", 22)
	for d in decs:
		var card := Kit.panel("PaperCardPanel")
		card.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(card)
		var h := Kit.hbox(24)
		card.add_child(h)
		var col := Kit.vbox(6)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		if str(d["chapter"]) != "":
			col.add_child(Kit.label(str(d["chapter"]).to_upper().replace("ß", "SS"), "PaperKicker"))
		if str(d["prompt"]) != "":
			var p := Kit.wrap_label(str(d["prompt"]), "TypeDim")
			Kit.scalable(p, 24)
			col.add_child(p)
		var row := Kit.hbox(16)
		var ic := Kit.sprite("icons/icon_decision.png")
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ic.modulate = Color(0.22, 0.22, 0.28)
		row.add_child(ic)
		var l := Kit.wrap_label(Kit.t("ui.journal.decided") + ":  " + str(d["text"]), "TypeLabel")
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		Kit.scalable(l, 29)
		row.add_child(l)
		col.add_child(row)
		h.add_child(_stamp(Kit.t("ui.journal.stamp").to_upper().replace("ß", "SS")))
	return s


func _stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(210, 72)
	c.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_record.png")
	frame.size = Vector2(210, 72)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 25)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(210, 72)
	l.pivot_offset = Vector2(105, 36)
	l.rotation = deg_to_rad(2.5)
	l.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	l.modulate = Color(1, 1, 1, 0.9)
	c.add_child(l)
	return c


func _inspect(item_id: String) -> void:
	if ui_root != null and ui_root.get("inspect") != null:
		ui_root.inspect.open(item_id)


# ================================================================ exploration tabs (§12)
func _ex_call(method: String, args: Array, fallback):
	var ex := Kit.explore()
	if ex == null or not ex.has_method(method):
		return fallback
	return ex.callv(method, args)


## Story chronology of a level (quest order in data/v3; unknown levels last).
func _level_rank(level: String) -> int:
	var qs := Kit.quests()
	for i in qs.size():
		if str(qs[i].get("scene", "")) == level:
			return i
	return 999


## Areas in story order (Karsk before Berlin), not file-name order.
func _areas_in_story_order() -> Array:
	var areas: Array = _ex_call("areas", [], [])
	var rank := {}
	for a in areas:
		var r := 999
		for e in _ex_call("entries_for", [str(a)], []):
			r = mini(r, _level_rank(str(e.get("level", ""))))
		rank[a] = r
	var out := areas.duplicate()
	out.sort_custom(func(x, y): return rank[x] < rank[y] if rank[x] != rank[y] else areas.find(x) < areas.find(y))
	return out


## History sides in the story order of the finds that lead to them.
func _sides_in_story_order() -> Array:
	var rank := {}
	var order: Array = []
	for c in _ex_call("cards_list", [], []):
		var sd := str(c.get("side", ""))
		if not rank.has(sd):
			rank[sd] = 999
			order.append(sd)
	for e in _ex_call("entries_for", [""], []):
		var hist = e.get("history", [])
		if not (hist is Array):
			continue
		for cid in hist:
			var sd := str((_ex_call("card", [str(cid)], {}) as Dictionary).get("side", ""))
			if rank.has(sd):
				rank[sd] = mini(rank[sd], _level_rank(str(e.get("level", ""))))
	var out := order.duplicate()
	out.sort_custom(func(x, y): return rank[x] < rank[y] if rank[x] != rank[y] else order.find(x) < order.find(y))
	return out


func _list_split(list_w := 560.0) -> Array:
	var h := Kit.hbox(40)
	h.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var left_scroll := _scroll()
	left_scroll.custom_minimum_size.x = list_w
	h.add_child(left_scroll)
	var list := Kit.vbox(4)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_scroll.add_child(list)
	var vsep := ColorRect.new()
	vsep.color = Color("b0aa93")
	vsep.custom_minimum_size.x = 3
	vsep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(vsep)
	# right column: scrolling detail + an action row pinned below it (always visible, also at 150 % text)
	var right := Kit.vbox(14)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(right)
	var right_scroll := _scroll()
	right_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_child(right_scroll)
	var detail := Kit.vbox(14)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_scroll.add_child(detail)
	var actions := Kit.hbox(18)
	actions.name = "Actions"
	right.add_child(actions)
	detail.set_meta("actions", actions)
	return [h, list, detail]


## The pinned action row of a detail column (see _list_split), emptied.
func _actions_of(detail: VBoxContainer) -> HBoxContainer:
	var a: HBoxContainer = detail.get_meta("actions") if detail.has_meta("actions") else null
	if a != null:
		for c in a.get_children():
			c.queue_free()
	return a


func _group_head(text: String, count: String) -> Control:
	var head := Kit.hbox(12)
	var al := Kit.wrap_label(text.to_upper().replace("ß", "SS"), "PaperKicker")
	al.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(al)
	var cl := Kit.label(count, "TypeDim")
	Kit.scalable(cl, 23)
	cl.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(cl)
	return head


func _dim_line(text: String) -> Label:
	var l := Kit.wrap_label(text, "TypeDim")
	Kit.scalable(l, 22)
	return l


## "Entdeckungen": per area found/total + progress bar, the found titles (focus shows the detail, Enter /
## click opens the find again in the DiscoveryView), and how many are still undiscovered.
func _build_discoveries() -> Control:
	var areas: Array = _areas_in_story_order()
	var pr := Kit.explore_progress()
	if areas.is_empty() or int(pr["found"]) == 0:
		var v := Kit.vbox(18)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		var e := _empty("ui.journal.empty.discoveries")
		(e as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(e)
		if int(pr["total"]) > 0:
			var c := _dim_line(Kit.t("ui.explore.count", {"n": 0, "total": pr["total"]}))
			c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(c)
		return v
	var parts := _list_split()
	var list: VBoxContainer = parts[1]
	var detail: VBoxContainer = parts[2]
	var first: Button = null
	var first_e: Dictionary = {}
	for a in areas:
		var c: Dictionary = _ex_call("counts", [str(a)], {"found": 0, "total": 0})
		if list.get_child_count() > 0:
			list.add_child(Kit.rule(Color(0, 0, 0, 0), 16))
		list.add_child(_group_head(Kit.explore_area_label(str(a)), Kit.t("ui.explore.count", {"n": c["found"], "total": c["total"]})))
		list.add_child(Kit.ex_bar(float(c["found"]) / maxf(1.0, float(c["total"])), 480))
		list.add_child(Kit.rule(Color(0, 0, 0, 0), 6))
		for e in _ex_call("found_entries", [str(a)], []):
			var b := Kit.button(Kit.explore_title(e), "PaperListButton")
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.icon = Kit.ex_tex(Kit.explore_kind_icon(str(e.get("kind", ""))))
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			b.focus_entered.connect(_show_find_detail.bind(detail, e))
			b.mouse_entered.connect(b.grab_focus)
			b.pressed.connect(_reopen_find.bind(str(e["id"])))
			list.add_child(b)
			if first == null:
				first = b
				first_e = e
		var left := int(c["total"]) - int(c["found"])
		var txt := Kit.t("ui.explore.all_found") if left <= 0 else (Kit.t("ui.explore.remaining_one") if left == 1 else Kit.t("ui.explore.remaining", {"n": left}))
		var rl := _dim_line(txt)
		rl.add_theme_font_override("font", Kit.font("fv_serif_italic"))
		list.add_child(rl)
	if not first_e.is_empty():
		_show_find_detail(detail, first_e)
	if first != null and is_open:
		first.grab_focus.call_deferred()
	return parts[0]


func _show_find_detail(detail: VBoxContainer, e: Dictionary) -> void:
	for c in detail.get_children():
		c.queue_free()
	var id := str(e.get("id", ""))
	var img := str(_ex_call("entry_image", [id], ""))
	var t2 := Kit.optional_tex(img) if img != "" else null
	if t2 != null:
		var s := 2 if Kit.text_scale() < 1.2 else 1
		while s > 1 and (t2.get_width() * s > 720 or t2.get_height() * s > 300):
			s -= 1
		var pic := Kit.pixel_image(t2, s)
		pic.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		if t2.get_width() * s > 720 or t2.get_height() * s > 300:
			var k := minf(720.0 / t2.get_width(), 300.0 / t2.get_height())
			pic.custom_minimum_size = (t2.get_size() * k).floor()
		detail.add_child(pic)
	var kind := str(e.get("kind", "detail"))
	var kick := Kit.wrap_label((Kit.explore_kind_label(kind) + "  ·  " + Kit.explore_place(e)).to_upper().replace("ß", "SS"), "PaperKicker")
	detail.add_child(kick)
	var n := Kit.wrap_label(Kit.explore_title(e), "TypeHeading")
	Kit.scalable(n, 34)
	detail.add_child(n)
	var sep := HSeparator.new()
	sep.theme_type_variation = "PaperSeparator"
	detail.add_child(sep)
	var body := ""
	if str(e.get("text_key", "")) != "":
		body = Kit.t(str(e["text_key"]))
	else:
		var lines: PackedStringArray = []
		for l in e.get("lines", []):
			if l is Dictionary:
				lines.append("%s: %s" % [Kit.char_name(str(l.get("speaker", ""))), Kit.t(str(l.get("key", "")))])
		body = "\n".join(lines)
	var d := Kit.wrap_label(body, "TypeLabel")
	Kit.scalable(d, 27)
	d.max_lines_visible = 7 if Kit.text_scale() < 1.2 else 5
	d.text_overrun_behavior = TextServer.OVERRUN_TRIM_WORD_ELLIPSIS
	detail.add_child(d)
	var cards: Array = _ex_call("cards_of", [id], [])
	if not cards.is_empty():
		var row := Kit.hbox(12)
		var ic := Kit.ex_sprite("icons/kind_history.png")
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(ic)
		var ll := _dim_line(Kit.t("ui.explore.linked_one") if cards.size() == 1 else Kit.t("ui.explore.linked_n", {"n": cards.size()}))
		ll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ll.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(ll)
		detail.add_child(row)
	var b := Kit.button(Kit.t("ui.explore.reopen"), "", 260)
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.pressed.connect(_reopen_find.bind(id))
	var act := _actions_of(detail)
	if act != null:
		act.add_child(b)
	else:
		detail.add_child(b)


func _reopen_find(id: String) -> void:
	if ui_root != null and ui_root.get("discovery") != null:
		ui_root.discovery.open(id)


# ================================================================ side tasks (§12.9)
## Started tasks as journal rows: open ones first, then finished ones; inside each group the most recent place
## first (like the objectives), then data order. Pure — `ex` is the Explore service or any object with
## tasks_for / task_state; `rank` maps a level id to its story position.
## Row: {id, title_key, summary_key, level, state ("active"|"done"), step, total, hint_key, done_steps}.
static func task_rows(ex: Object, rank: Callable) -> Array:
	var rows: Array = []
	if ex == null or not ex.has_method("tasks_for") or not ex.has_method("task_state"):
		return rows
	var order := 0
	for t in ex.tasks_for(""):
		var tid := str(t.get("id", ""))
		var st: Dictionary = ex.task_state(tid)
		var s := str(st.get("state", ""))
		if s != "active" and s != "done":
			continue
		var steps = t.get("steps", [])
		rows.append({"id": tid, "title_key": str(t.get("title_key", "")), "summary_key": str(t.get("summary_key", "")),
			"level": str(t.get("level", "")), "state": s, "step": int(st.get("step", 0)),
			"total": (steps as Array).size() if steps is Array else 0, "hint_key": str(st.get("hint_key", "")),
			"done_steps": (st.get("done_steps", []) as Array).duplicate(), "_rank": float(rank.call(str(t.get("level", "")))),
			"_order": order})
		order += 1
	rows.sort_custom(func(a, b):
		if a["state"] != b["state"]:
			return a["state"] == "active"
		if a["_rank"] != b["_rank"]:
			return a["_rank"] > b["_rank"]
		return a["_order"] < b["_order"])
	return rows


## Story position of a level; side levels (L_M1_Plaza) sit right after the quest scene of their chapter (L_M1_*).
func _task_rank(level: String) -> float:
	var r := _level_rank(level)
	if r < 999:
		return float(r)
	var parts := level.split("_")
	if parts.size() >= 2:
		var qs := Kit.quests()
		for i in qs.size():
			if str(qs[i].get("scene", "")).begins_with(parts[0] + "_" + parts[1] + "_"):
				return float(i) + 0.5
	return 999.0


func _task_place(level: String) -> String:
	var k := "ui.tasks.place." + level
	if Kit.has_key(k):
		return Kit.t(k)
	return Kit.explore_place({"level": level})


func _current_level() -> String:
	var g = Kit.svc("Game")
	if g != null:
		var lvl = g.get("level")
		if lvl != null and is_instance_valid(lvl) and lvl.get("level_id") != null:
			return str(lvl.get("level_id"))
	var st = Kit.svc("Story")
	if st != null and st.get("current_scene") != null:
		return str(st.get("current_scene"))
	return ""


## Tasks of the current place nobody has asked for yet (only counted, never named).
func _tasks_waiting_here() -> int:
	var lvl := _current_level()
	if lvl == "":
		return 0
	var n := 0
	for t in _ex_call("tasks_for", [lvl], []):
		if str((_ex_call("task_state", [str(t.get("id", ""))], {}) as Dictionary).get("state", "")) == "not_started":
			n += 1
	return n


func _waiting_line(n: int) -> Label:
	var l := _dim_line(Kit.t("ui.tasks.here_one") if n == 1 else Kit.t("ui.tasks.here", {"n": n}))
	l.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	return l


## "Aufgaben": open tasks first with the current hint, then the finished ones.
func _build_tasks() -> Control:
	var rows := task_rows(Kit.explore(), _task_rank)
	var here := _tasks_waiting_here()
	if rows.is_empty():
		var v := Kit.vbox(18)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		var e := _empty("ui.journal.empty.tasks")
		(e as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(e)
		if here > 0:
			var w := _waiting_line(here)
			w.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(w)
		return v
	var parts := _list_split()
	var list: VBoxContainer = parts[1]
	var detail: VBoxContainer = parts[2]
	var first: Button = null
	var first_r: Dictionary = {}
	var group := ""
	for r in rows:
		if str(r["state"]) != group:
			group = str(r["state"])
			if list.get_child_count() > 0:
				list.add_child(Kit.rule(Color(0, 0, 0, 0), 16))
			var g := group
			var cnt := rows.filter(func(x): return str(x["state"]) == g).size()
			list.add_child(_group_head(Kit.t("ui.tasks.kicker." + group), str(cnt)))
			list.add_child(Kit.rule(Color(0, 0, 0, 0), 6))
		var b := Kit.button(Kit.t(str(r["title_key"])), "PaperListButton")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.icon = Kit.tex("res://assets/ui/icons/%s.png" % ("mark_done" if str(r["state"]) == "done" else "mark_open"))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.focus_entered.connect(_show_task_detail.bind(detail, r))
		b.mouse_entered.connect(b.grab_focus)
		b.pressed.connect(_reopen_task_step.bind(r))
		list.add_child(b)
		if first == null:
			first = b
			first_r = r
	if here > 0:
		list.add_child(Kit.rule(Color(0, 0, 0, 0), 16))
		list.add_child(_waiting_line(here))
	_show_task_detail(detail, first_r)
	if first != null and is_open:
		first.grab_focus.call_deferred()
	return parts[0]


func _show_task_detail(detail: VBoxContainer, r: Dictionary) -> void:
	for c in detail.get_children():
		c.queue_free()
	if r.is_empty():
		return
	var done: bool = str(r["state"]) == "done"
	var kick := Kit.wrap_label((Kit.t("ui.tasks.kicker." + str(r["state"])) + "  ·  " + _task_place(str(r["level"]))).to_upper().replace("ß", "SS"),
		"PaperKicker")
	detail.add_child(kick)
	var n := Kit.wrap_label(Kit.t(str(r["title_key"])), "TypeHeading")
	Kit.scalable(n, 34)
	detail.add_child(n)
	var sep := HSeparator.new()
	sep.theme_type_variation = "PaperSeparator"
	detail.add_child(sep)
	var s := Kit.wrap_label(Kit.t(str(r["summary_key"])), "TypeLabel")
	Kit.scalable(s, 27)
	detail.add_child(s)
	detail.add_child(Kit.rule(Color(0, 0, 0, 0), 6))
	if not done and str(r["hint_key"]) != "":
		detail.add_child(Kit.label(Kit.t("ui.tasks.next").to_upper().replace("ß", "SS"), "PaperKicker"))
		var row := Kit.hbox(14)
		var mark := Kit.sprite("icons/mark_open.png")
		mark.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		row.add_child(mark)
		var h := Kit.wrap_label(Kit.t(str(r["hint_key"])), "TypeLabel")
		h.add_theme_font_override("font", Kit.font("fv_serif_italic"))
		Kit.scalable(h, 27)
		h.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(h)
		detail.add_child(row)
	if not done:   # a finished task lists its steps below; no progress line needed
		detail.add_child(_dim_line(Kit.t("ui.tasks.steps", {"n": int(r["step"]) + 1, "total": r["total"]})))
	var steps: Array = r.get("done_steps", [])
	if not steps.is_empty():
		detail.add_child(Kit.rule(Color(0, 0, 0, 0), 4))
		detail.add_child(Kit.label(Kit.t("ui.tasks.all_steps" if done else "ui.tasks.done_steps").to_upper().replace("ß", "SS"), "PaperKicker"))
		for sid in steps:
			var e: Dictionary = _ex_call("entry", [str(sid)], {})
			var srow := Kit.hbox(12)
			var tick := Kit.sprite("icons/mark_done.png")
			tick.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			tick.modulate = Color(1, 1, 1, 0.7)
			srow.add_child(tick)
			var sl := _dim_line(Kit.explore_title(e) if not e.is_empty() else str(sid))
			sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			srow.add_child(sl)
			detail.add_child(srow)
		var b := Kit.button(Kit.t("ui.explore.reopen"), "", 260)
		b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		b.pressed.connect(_reopen_task_step.bind(r))
		var act := _actions_of(detail)
		if act != null:
			act.add_child(b)
		else:
			detail.add_child(b)
	else:
		_actions_of(detail)


## Opens the most recent finished step of a task again (find page or the chat's notebook summary).
func _reopen_task_step(r: Dictionary) -> void:
	var steps: Array = r.get("done_steps", [])
	if steps.is_empty():
		return
	_reopen_find(str(steps[steps.size() - 1]))


## "Geschichte": the real-history cards found so far (re-readable), unknown ones only as a count.
func _build_history() -> Control:
	var hc_all: Dictionary = _ex_call("history_counts", [], {"found": 0, "total": 0})
	var count_line := Kit.t("ui.history.count", {"n": hc_all["found"], "total": hc_all["total"]})
	if int(hc_all["found"]) == 0:
		var v := Kit.vbox(18)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		var e := _empty("ui.journal.empty.history")
		(e as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(e)
		if int(hc_all["total"]) > 0:
			var c := _dim_line(count_line)
			c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(c)
		return v
	var outer := Kit.vbox(14)
	var top := Kit.hbox(24)
	var cl := Kit.label(count_line, "TypeLabel")
	Kit.scalable(cl, 25)
	top.add_child(cl)
	outer.add_child(top)
	var intro := _dim_line(Kit.t("ui.history.intro"))
	intro.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	outer.add_child(intro)
	outer.add_child(Kit.rule(Color(0, 0, 0, 0), 4))
	var parts := _list_split()
	(parts[0] as Control).size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(parts[0])
	var list: VBoxContainer = parts[1]
	var detail: VBoxContainer = parts[2]
	var sides: Array = _sides_in_story_order()
	var first: Button = null
	var first_c: Dictionary = {}
	for sd in sides:
		var cnt: Dictionary = _ex_call("history_counts", [sd], {"found": 0, "total": 0})
		if list.get_child_count() > 0:
			list.add_child(Kit.rule(Color(0, 0, 0, 0), 16))
		list.add_child(_group_head(Kit.history_side_label(sd), Kit.t("ui.history.side_count", {"n": cnt["found"], "total": cnt["total"]})))
		list.add_child(Kit.ex_bar(float(cnt["found"]) / maxf(1.0, float(cnt["total"])), 480, true))
		list.add_child(Kit.rule(Color(0, 0, 0, 0), 6))
		for c in _ex_call("found_cards", [sd], []):
			var b := Kit.button("%s  %s" % [str(c.get("year", "")), Kit.t(str(c.get("title_key", "")))], "PaperListButton")
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.icon = Kit.ex_tex("icons/kind_history.png")
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			b.focus_entered.connect(_show_card_detail.bind(detail, c))
			b.mouse_entered.connect(b.grab_focus)
			b.pressed.connect(_read_card.bind(str(c["id"])))
			list.add_child(b)
			if first == null:
				first = b
				first_c = c
		var unknown := int(cnt["total"]) - int(cnt["found"])
		if unknown > 0:
			var ul := _dim_line(Kit.t("ui.history.unknown_one") if unknown == 1 else Kit.t("ui.history.unknown", {"n": unknown}))
			ul.add_theme_font_override("font", Kit.font("fv_serif_italic"))
			list.add_child(ul)
	if not first_c.is_empty():
		_show_card_detail(detail, first_c)
	if first != null and is_open:
		first.grab_focus.call_deferred()
	return outer


## Archive-style preview card (cool paper, slate band, no regime symbols) inside the warm dossier sheet:
## year, title and the beginning of the text; "Karte lesen" / Enter on the list row opens the full card
## (text, sources, note) in the DiscoveryView.
func _show_card_detail(detail: VBoxContainer, c: Dictionary) -> void:
	for x in detail.get_children():
		x.queue_free()
	var hc := Kit.high_contrast()
	var ink := Color.BLACK if hc else Color("1a1c2a")
	var dim := Color("24373a") if hc else Color("4a5a5b")
	var card := PanelContainer.new()
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_theme_stylebox_override("panel", Kit.ex_style("frames/archive_card_hc.png" if hc else "frames/archive_card.png",
		[24, 48, 24, 24], [42, 3, 42, 30]))
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_child(card)
	var v := Kit.vbox(0)
	card.add_child(v)
	var band := Kit.hbox(14)
	band.custom_minimum_size.y = 36
	v.add_child(band)
	var bl := Kit.label(Kit.t("ui.history.kicker").to_upper().replace("ß", "SS"), "KickerLabel", 20, Color("dee5dc"))
	bl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	band.add_child(bl)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 22))
	var hrow := Kit.hbox(22)
	v.add_child(hrow)
	var year := Kit.label(str(c.get("year", "")), "", 0, dim)
	year.add_theme_font_override("font", Kit.font("fv_heading"))
	Kit.scalable(year, 38)
	year.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	hrow.add_child(year)
	var title := Kit.wrap_label(Kit.t(str(c.get("title_key", ""))), "", 0, ink)
	title.add_theme_font_override("font", Kit.font("fv_serif_bold"))
	Kit.scalable(title, 31)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hrow.add_child(title)
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 12))
	v.add_child(Kit.rule(Color("a3b1ad") if not hc else Color.BLACK, 3))
	v.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
	var text := Kit.wrap_label(Kit.t(str(c.get("text_key", ""))), "", 0, ink)
	text.add_theme_font_override("font", Kit.font("fv_serif"))
	text.add_theme_constant_override("line_spacing", 6)
	Kit.scalable(text, 25)
	text.max_lines_visible = 6 if Kit.text_scale() < 1.2 else 4
	text.text_overrun_behavior = TextServer.OVERRUN_TRIM_WORD_ELLIPSIS
	v.add_child(text)
	var srcs = []   # sources are listed in the planned end-credits scene, not on the cards (user decision 2026-11-05)
	if srcs is Array and not srcs.is_empty():
		v.add_child(Kit.rule(Color(0, 0, 0, 0), 10))
		var sk := Kit.label("%s: %d" % [Kit.t("ui.history.sources").to_upper().replace("ß", "SS"), srcs.size()], "HintLabel", 0, dim)
		Kit.scalable(sk, 18)
		v.add_child(sk)
	var b := Kit.button(Kit.t("ui.history.read"), "", 240)
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.pressed.connect(_read_card.bind(str(c.get("id", ""))))
	var act := _actions_of(detail)
	if act != null:
		act.add_child(b)
	else:
		detail.add_child(b)


func _read_card(card_id: String) -> void:
	if ui_root != null and ui_root.get("discovery") != null:
		ui_root.discovery.open_cards([card_id])


# ================================================================ „Akte“ (round 9, §12.12)
## The eighth tab: the round-1 paper tab turned 90° (assets/ui/board/vtab_*.png), standing out of the sheet's
## right edge, its label reading upwards like a file spine.
func _make_board_tab() -> Button:
	var b := Button.new()
	b.name = "BoardTab"
	b.toggle_mode = true
	b.button_group = _group
	b.focus_mode = Control.FOCUS_ALL
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	var styles := {"normal": "normal", "hover": "hover", "pressed": "pressed", "hover_pressed": "pressed",
		"focus": "focus", "disabled": "normal"}
	for st in styles:
		var sb := StyleBoxTexture.new()
		sb.texture = Kit.optional_tex(VTAB_DIR + "vtab_%s.png" % styles[st])
		sb.texture_margin_left = 6
		sb.texture_margin_top = 12
		sb.texture_margin_right = 12
		sb.texture_margin_bottom = 12
		b.add_theme_stylebox_override(st, sb)
	b.pressed.connect(show_tab.bind("board"))
	add_child(b)
	# the label borrows the paper tab's font and colours (theme type PaperTabButton), turned to read upwards
	_vtab_label = Kit.label(Kit.t("ui.journal.tab.board").to_upper().replace("ß", "SS"), "PaperTabButton")
	_vtab_label.add_theme_stylebox_override("normal", StyleBoxEmpty.new())   # not the tab frame a second time
	_vtab_label.rotation = -PI * 0.5
	b.add_child(_vtab_label)
	b.toggled.connect(_vtab_style.unbind(1))
	for sig in [b.mouse_entered, b.mouse_exited, b.focus_entered, b.focus_exited]:
		sig.connect(_vtab_style)
	return b


func _vtab_style() -> void:
	var b: Button = _tab_buttons.get("board")
	if b == null or _vtab_label == null:
		return
	var col := "font_color"
	if b.button_pressed:
		col = "font_pressed_color"
	elif b.has_focus() or b.is_hovered():
		col = "font_hover_color"
	_vtab_label.add_theme_color_override("font_color", b.get_theme_color(col, "PaperTabButton"))
	var ts := _vtab_label.get_combined_minimum_size()
	b.custom_minimum_size = Vector2(ceilf(ts.y) + 27.0, ceilf(ts.x) + 60.0)
	b.size = b.custom_minimum_size
	_vtab_label.position = Vector2(12.0, ceilf(ts.x) + 30.0)


## Keeps the divider on the sheet's right edge (3 px over the paper), a little below its top.
func _place_board_tab() -> void:
	var b: Button = _tab_buttons.get("board")
	if b == null or _sheet == null or not _sheet.is_inside_tree():
		return
	var r := _sheet.get_global_rect()
	var me := get_global_rect().position
	b.position = Vector2(r.end.x - 3.0, r.position.y + 36.0) - me


## Cover page of the file: folder with the places, counters, „Pinnwand öffnen“; the running summary on the right.
func _build_board_cover() -> Control:
	var script: Script = load(BOARD_SCRIPT)
	var m: Dictionary = script.live_model()
	var h := Kit.hbox(54)
	var left := Kit.vbox(18)
	left.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(left)
	var fold := Control.new()
	fold.custom_minimum_size = Vector2(372, 258)
	fold.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ft := TextureRect.new()
	ft.texture = Kit.optional_tex(VTAB_DIR + "folder.png")
	ft.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ft.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fold.add_child(ft)
	var ftitle := Kit.label(Kit.t("board.title"), "DimLabel", 22)
	ftitle.add_theme_color_override("font_color", Kit.C_INK)
	ftitle.position = Vector2(39, 72)
	fold.add_child(ftitle)
	# the cities on the folder's label strip, each once („Karsk · Güterbahnhof“ and „Karsk“ are one city), clipped
	# with an ellipsis to the strip (clip_text before size: else the label keeps the text's own width)
	var fplaces := Kit.label(" · ".join(board_cities(m)), "DimLabel", 17)
	fplaces.add_theme_color_override("font_color", Kit.C_INK_B)
	fplaces.clip_text = true
	fplaces.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	fplaces.position = Vector2(39, 105)
	fplaces.size = Vector2(210, 24)
	fold.add_child(fplaces)
	left.add_child(fold)
	var threads: int = (m.get("threads", []) as Array).size()
	var cnt := Kit.wrap_label(Kit.t("board.count.items", {"n": m.get("owned", 0), "total": m.get("total", 0)}) + "\n"
		+ Kit.t("board.count.threads", {"k": threads}), "TypeDim")
	cnt.custom_minimum_size.x = 372
	Kit.scalable(cnt, 23)
	left.add_child(cnt)
	var b := Kit.button(Kit.t("board.open"), "", 300)
	b.name = "OpenBoard"
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.pressed.connect(open_board)
	left.add_child(b)
	if is_open:
		b.grab_focus.call_deferred()
	var right := Kit.vbox(12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(right)
	right.add_child(Kit.label(Kit.t("board.summary.title").to_upper().replace("ß", "SS"), "PaperKicker"))
	var mem: String = str(m.get("memory_scene", ""))
	if mem != "":
		var stamp := Kit.wrap_label(_board_memory_line(mem).to_upper().replace("ß", "SS"), "StampLabel")
		Kit.scalable(stamp, 21)
		right.add_child(stamp)
		var then := Kit.wrap_label(Kit.t("board.memory.note"), "DimLabel")
		Kit.scalable(then, 22)
		then.add_theme_color_override("font_color", Kit.C_INK_DIM)
		right.add_child(then)
	var s := _scroll()
	right.add_child(s)
	var v := Kit.vbox(14)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(v)
	# the cover opens on the newest lines of the summary (mouse wheel / the board's sheet for the older ones)
	var vb := s.get_v_scroll_bar()
	vb.changed.connect(func() -> void: s.scroll_vertical = int(vb.max_value))
	var entries: Array = m.get("summary", [])
	if entries.is_empty():
		var e := Kit.wrap_label(Kit.t("board.cover.empty") + " " + Kit.t("board.summary.empty"), "TypeDim")
		Kit.scalable(e, 25)
		v.add_child(e)
	for i in entries.size():
		var row := Kit.hbox(14)
		var num := Kit.label("%d." % (i + 1), "TypeDim")
		Kit.scalable(num, 24)
		num.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		if i == entries.size() - 1:
			num.add_theme_color_override("font_color", Kit.C_STAMP)
		row.add_child(num)
		var l := Kit.wrap_label(Kit.t(str(entries[i]["text_key"])), "TypeLabel")
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		Kit.scalable(l, 25)
		row.add_child(l)
		v.add_child(row)
	return h


## The known places of the board model as cities, each once, in board order: the part of a place title before
## " · " („Karsk · Güterbahnhof“ → „Karsk“).
static func board_cities(model: Dictionary) -> Array:
	var out: Array = []
	for g in model.get("places", []):
		if not (g is Dictionary) or not g.get("known", false) or str(g.get("title_key", "")) == "":
			continue
		var city := Kit.t(str(g["title_key"])).split(" · ")[0].strip_edges()
		if city != "" and not out.has(city):
			out.append(city)
	return out


func _board_memory_line(scene: String) -> String:
	var g := Kit.svc("Game")
	var info = g.memory_info() if g != null and g.has_method("memory_info") else {}
	var place := str(info.get("place", "")) if info is Dictionary else ""
	var date := str(info.get("date", "")) if info is Dictionary else ""
	if place == "":
		place = Kit.t("ui.memories.place." + scene) if Kit.has_key("ui.memories.place." + scene) else scene
	if date == "" and Kit.has_key("ui.memories.date." + scene):
		date = Kit.t("ui.memories.date." + scene)
	return Kit.t("board.memory.stamp", {"place": place, "date": date})


## The EvidenceBoard, instanced once: under UIRoot when there is one (its modal stack moves it), else beside the
## journal (tests, previews).
func board_node() -> Control:
	if board != null and is_instance_valid(board):
		return board
	board = (load(BOARD_SCENE) as PackedScene).instantiate() as Control
	board.name = "EvidenceBoard"
	var host: Node = ui_root if ui_root != null else get_parent()
	if host == null:
		host = self
	host.add_child(board)
	if ui_root != null and ui_root.get("toast_layer") != null:
		ui_root.move_child(board, (ui_root.toast_layer as Node).get_index())
	board.set("ui_root", ui_root)
	return board


func open_board() -> void:
	Kit.ui_sound("confirm")
	board_node().open()


# ================================================================ input
func modal_input(event: InputEvent) -> bool:
	if event.is_action_pressed("journal"):
		close()
		return true
	if event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).physical_keycode
		if k == KEY_Q or k == KEY_PAGEUP:
			cycle_tab(-1)
			return true
		if k == KEY_E or k == KEY_PAGEDOWN:
			cycle_tab(1)
			return true
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER:
			cycle_tab(-1)
			return true
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER:
			cycle_tab(1)
			return true
	return false


func focus_default() -> void:
	(_tab_buttons[current_tab] as Button).grab_focus()
