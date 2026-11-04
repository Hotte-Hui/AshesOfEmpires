extends "res://scripts/ui/ui_modal.gd"
## Journal / dossier with four paper index tabs: Ziele, Beweise, Personen, Entscheidungen.
## Data comes from Story.journal() (objectives with state, evidence items, people met, decisions); the parser
## accepts arrays or dictionaries for every section and falls back to Story.objective_state/inventory/
## choice_history + data/v3 when journal() is missing. Locked objectives are never listed (no false promises).
## Q / E (LB / RB) switch tabs, J / Tab / Esc close. "Ansehen" opens the InspectView on top.

const TABS := ["objectives", "evidence", "people", "decisions"]

var suppress_toasts := true
var current_tab := "objectives"
var _tab_buttons: Dictionary = {}
var _sheet: PanelContainer
var _body: Control
var _subtitle: Label
var _data: Dictionary = {}
var _group := ButtonGroup.new()


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
	_subtitle = Kit.label("", "DimLabel", 26)
	_subtitle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_subtitle.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(_subtitle)
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 18))
	var tabs := Kit.hbox(6)
	tabs.add_theme_constant_override("separation", 6)
	var pad := Control.new()
	pad.custom_minimum_size.x = 30
	tabs.add_child(pad)
	root.add_child(tabs)
	for id in TABS:
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
	open_modal()
	show_tab(current_tab)


func _update_tab_titles() -> void:
	for id in TABS:
		var n: int = (_data.get(id, []) as Array).size()
		if id == "objectives":
			n = 0
			for o in _data.get("objectives", []):
				if str(o.get("state", "")) == "available":
					n += 1
		var t := Kit.t("ui.journal.tab." + id).to_upper()
		(_tab_buttons[id] as Button).text = t + ("   %d" % n if n > 0 else "")


func show_tab(id: String) -> void:
	current_tab = id
	(_tab_buttons[id] as Button).button_pressed = true
	if _body != null:
		_body.queue_free()
	match id:
		"objectives":
			_body = _build_objectives()
		"evidence":
			_body = _build_list_detail("evidence")
		"people":
			_body = _build_list_detail("people")
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
			var k := Kit.label(str(chapter).to_upper(), "PaperKicker")
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
		var tag := Kit.label(Kit.t("ui.journal.state." + str(o["state"])).to_upper(), "PaperKicker" if not done else "HintLabel", 19)
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
	var h := Kit.hbox(40)
	var left_scroll := _scroll()
	left_scroll.custom_minimum_size.x = 470
	h.add_child(left_scroll)
	var list := Kit.vbox(4)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left_scroll.add_child(list)
	var vsep := ColorRect.new()
	vsep.color = Color("b0aa93")
	vsep.custom_minimum_size.x = 3
	vsep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(vsep)
	var detail := Kit.vbox(16)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(detail)
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
	if kind == "evidence":
		var doc := Kit.doc_for_item(str(e["id"]))
		var t2 := Kit.optional_tex(Kit.DOCS_DIR + doc + ".png") if doc != "" else null
		if t2 != null:
			var s := 2
			while s > 1 and (t2.get_width() * s > 640 or t2.get_height() * s > 330):
				s -= 1
			var img := Kit.pixel_image(t2, s)
			img.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			if t2.get_width() > 640 or t2.get_height() > 330:
				var k := minf(640.0 / t2.get_width(), 330.0 / t2.get_height())
				img.custom_minimum_size = (t2.get_size() * k).floor()
			detail.add_child(img)
		var kick := Kit.label(Kit.t("ui.inspect.kicker." + str(e.get("category", "document"))).to_upper(), "PaperKicker")
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
			col.add_child(Kit.label(str(d["chapter"]).to_upper(), "PaperKicker"))
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
		h.add_child(_stamp(Kit.t("ui.journal.stamp").to_upper()))
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
