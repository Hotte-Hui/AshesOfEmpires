extends "res://scripts/ui/ui_modal.gd"
## Save / load screen. Slots come from Saves.list_slots() ({slot, manual, exists, valid, timestamp,
## chapter_key, character, scene, playtime_s, label}); manual slots can be saved, "auto"/"quick" are shown
## read-only when saving. Save/load/delete ask for confirmation where something could be lost.
## Loading hands over to Game through `load_requested(slot)` when connected (Game loads + switches level);
## stand-alone it calls Saves.load() itself and emits `loaded(slot)`.
## While saving is blocked (Saves/Game.save_block_key(), §12.10: inside a memory) the save screen says why and
## every slot is read-only; loading stays possible (a loaded save becomes the new present).

signal load_requested(slot: String)
signal loaded(slot: String)
signal saved(slot: String)
signal main_menu_requested
signal quit_requested

var mode := "load"            # "save" | "load"
var in_game := true
var _title: Label
var _list: VBoxContainer
var _empty_note: Label
var _block_note: Label
var _blocked := ""            # Loc key why saving is impossible now ("" = allowed)
var _primary: Button
var _delete: Button
var _back: Button
var _selected := ""
var _slots: Array = []
var _rows: Dictionary = {}


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.7))
	var p := Kit.panel("SolidPanel")
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -640
	p.offset_right = 640
	p.offset_top = -440
	p.offset_bottom = 440
	add_child(p)
	var v := Kit.vbox(14)
	p.add_child(v)
	_title = Kit.label("", "HeadingLabel")
	v.add_child(_title)
	v.add_child(HSeparator.new())
	_block_note = Kit.wrap_label("", "BodyLabel")
	Kit.scalable(_block_note, 28)
	_block_note.visible = false
	v.add_child(_block_note)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(scroll)
	var pad := Kit.margin(6, 6, 18, 6)
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(pad)
	_list = Kit.vbox(8)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_child(_list)
	_empty_note = Kit.label("", "DimLabel")
	_empty_note.visible = false
	v.add_child(_empty_note)
	var foot := Kit.hbox(18)
	foot.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(foot)
	_delete = Kit.button(Kit.t("ui.saveload.delete"), "", 220)
	_delete.pressed.connect(_delete_selected)
	foot.add_child(_delete)
	_primary = Kit.button("", "", 240)
	_primary.pressed.connect(_primary_selected)
	foot.add_child(_primary)
	_back = Kit.button(Kit.t("ui.back"), "", 220)
	_back.pressed.connect(close)
	foot.add_child(_back)


func open(open_mode := "load", ingame := true) -> void:
	mode = open_mode if open_mode in ["save", "load"] else "load"
	in_game = ingame
	_title.text = Kit.t("ui.saveload.title_save" if mode == "save" else "ui.saveload.title_load")
	_primary.text = Kit.t("ui.saveload.save" if mode == "save" else "ui.saveload.load")
	open_modal()
	refresh()


# ================================================================ data
func collect_slots() -> Array:
	var raw = Kit.call_svc("Saves", "list_slots", [], null)
	var out: Array = []
	if not (raw is Array):
		return out
	for s in raw:
		if not (s is Dictionary):
			continue
		var id := str(s.get("slot", s.get("id", "")))
		if id == "":
			continue
		var manual := bool(s.get("manual", id.is_valid_int()))
		var kind := "manual" if manual else ("quick" if id.contains("quick") else "auto")
		var exists := bool(s.get("exists", not bool(s.get("empty", false))))
		var valid := bool(s.get("valid", exists))
		out.append({"id": id, "kind": kind, "exists": exists, "valid": valid,
			"label": _slot_label(id, kind, str(s.get("label", ""))),
			"chapter": _chapter_text(s), "character": Kit.char_name(str(s.get("character", ""))) if str(s.get("character", "")) not in ["", "none", "<null>"] else "",
			"time": Kit.format_time(s.get("timestamp", s.get("time", 0))),
			"playtime": _playtime(float(s.get("playtime_s", s.get("playtime", 0.0)))),
			"error": _err_text(s)})
	return out


func _slot_label(id: String, kind: String, _label: String) -> String:
	var key = Kit.call_svc("Saves", "slot_label_key", [id], "")
	if str(key) != "" and Kit.has_key(str(key)):
		return Kit.t(str(key))
	match kind:
		"auto":
			return Kit.t("ui.saveload.autosave")
		"quick":
			return Kit.t("ui.saveload.quicksave")
	return Kit.t("ui.saveload.slot", {"n": id})


func _chapter_text(s: Dictionary) -> String:
	var ck := str(s.get("chapter_key", s.get("chapter", "")))
	if ck != "":
		return Kit.resolve(ck)
	var sc := Kit.scene_def(str(s.get("scene", "")))
	return Kit.t(str(sc["title_key"])) if sc.has("title_key") else ""


func _playtime(sec: float) -> String:
	if sec <= 0.0:
		return ""
	var m := maxi(1, int(sec / 60.0))
	if m < 60:
		return Kit.t("ui.saveload.playtime_min", {"m": m})
	return Kit.t("ui.saveload.playtime", {"h": m / 60, "m": "%02d" % (m % 60)})


func _err_text(s: Dictionary) -> String:
	var k := str(s.get("error_key", ""))
	if k != "" and Kit.has_key(k):
		return Kit.t(k)
	return ""


## Loc key why saving is impossible right now ("" = allowed).
func blocked_key() -> String:
	var k = Kit.call_svc("Saves", "save_block_key", [], null)
	if k == null:
		k = Kit.call_svc("Game", "save_block_key", [], "")
	return str(k) if k != null else ""


# ================================================================ list
func refresh() -> void:
	_blocked = blocked_key() if mode == "save" else ""
	_block_note.text = Kit.t(_blocked) if _blocked != "" else ""
	_block_note.visible = _blocked != ""
	_slots = collect_slots()
	for c in _list.get_children():
		c.queue_free()
	_rows.clear()
	var have_api := Kit.has_svc("Saves", "list_slots")
	_empty_note.visible = not have_api or _slots.is_empty()
	_empty_note.text = Kit.t("ui.saveload.unavailable") if not have_api else Kit.t("ui.saveload.none")
	var first_ok: Button = null
	for s in _slots:
		var row := _make_row(s)
		_list.add_child(row)
		_rows[s["id"]] = row
		if first_ok == null and not row.disabled:
			first_ok = row
	if mode == "load" and have_api:
		var any := false
		for s in _slots:
			if s["exists"]:
				any = true
		_empty_note.visible = not any
	_select("" if first_ok == null else str(first_ok.get_meta("slot")))
	if is_open:
		if first_ok != null:
			first_ok.grab_focus.call_deferred()
		else:
			_back.grab_focus.call_deferred()


func _make_row(s: Dictionary) -> Button:
	var b := Kit.button("", "SlotButton")
	b.custom_minimum_size = Vector2(0, 100)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.set_meta("slot", s["id"])
	var can := _can_primary(s)
	b.disabled = not can and not s["exists"]   # existing read-only/broken slots stay focusable (delete)
	var h := Kit.hbox(24)
	Kit.full_rect(h)
	h.offset_left = 30
	h.offset_right = -30
	h.offset_top = 10
	h.offset_bottom = -10
	b.add_child(h)
	var left := Kit.vbox(2)
	left.custom_minimum_size.x = 420
	left.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(left)
	var name_l := Kit.label(str(s["label"]).to_upper().replace("ß", "SS"), "SpeakerLabel", 25)
	left.add_child(name_l)
	var tag := ""
	if not s["valid"] and s["exists"]:
		tag = Kit.t("ui.saveload.invalid").to_upper().replace("ß", "SS")
	elif mode == "save" and s["kind"] != "manual":
		tag = Kit.t("ui.saveload.readonly").to_upper().replace("ß", "SS")
	if tag != "":
		left.add_child(Kit.label(tag, "HintLabel", 18))
	var mid := Kit.vbox(2)
	mid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(mid)
	if s["exists"]:
		var ch := Kit.label(str(s["chapter"]) if str(s["chapter"]) != "" else "—", "BodyLabel", 30)
		ch.add_theme_font_override("font", Kit.font("fv_serif_italic"))
		mid.add_child(ch)
		if str(s["character"]) != "":
			mid.add_child(Kit.label(str(s["character"]), "DimLabel"))
		if str(s["error"]) != "" and not s["valid"]:
			mid.add_child(Kit.label(str(s["error"]), "DimLabel", 22))
	else:
		mid.add_child(Kit.label(Kit.t("ui.saveload.empty"), "DimLabel", 28))
	var right := Kit.vbox(2)
	right.custom_minimum_size.x = 260
	right.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(right)
	if s["exists"]:
		var tl := Kit.label(str(s["time"]), "KickerLabel", 22)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(tl)
		if str(s["playtime"]) != "":
			var pl := Kit.label(str(s["playtime"]), "DimLabel", 22)
			pl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			right.add_child(pl)
	for c in h.find_children("*", "Control", true, false):
		(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	if b.disabled:
		h.modulate = Color(1, 1, 1, 0.5)
	elif not can:
		h.modulate = Color(1, 1, 1, 0.72)
	b.focus_entered.connect(_select.bind(str(s["id"])))
	b.mouse_entered.connect(func(): if not b.disabled: b.grab_focus())
	b.pressed.connect(func():
		_select(str(s["id"]))
		_primary_selected())
	return b


func _slot(id: String) -> Dictionary:
	for s in _slots:
		if s["id"] == id:
			return s
	return {}


func _can_primary(s: Dictionary) -> bool:
	if s.is_empty():
		return false
	if mode == "save":
		return _blocked == "" and s["kind"] == "manual" and Kit.has_svc("Saves", "save")
	return s["exists"] and s["valid"]


func _select(id: String) -> void:
	_selected = id
	var s := _slot(id)
	_primary.disabled = not _can_primary(s)
	_delete.disabled = s.is_empty() or not s["exists"] or not Kit.has_svc("Saves", "delete")


# ================================================================ actions
func _primary_selected() -> void:
	var s := _slot(_selected)
	if not _can_primary(s):
		return
	if mode == "save":
		if s["exists"]:
			var yes: bool = await _ask(Kit.t("ui.saveload.confirm_overwrite", {"label": s["label"]}))
			if not yes:
				return
		var r = Kit.call_svc("Saves", "save", [s["id"]], null)
		if Kit.ok(r):
			Kit.ui_sound("save")
			_toast(Kit.t("ui.toast.saved"), "save")
			saved.emit(s["id"])
			refresh()
			if _rows.has(s["id"]):
				(_rows[s["id"]] as Button).grab_focus.call_deferred()
		else:
			_toast(Kit.t("ui.toast.save_failed", {"error": _result_error(r)}), "info")
		return
	if in_game:
		var yes2: bool = await _ask(Kit.t("ui.saveload.confirm_load", {"label": s["label"]}))
		if not yes2:
			return
	if not get_signal_connection_list("load_requested").is_empty():
		load_requested.emit(s["id"])
		return
	var lr = Kit.call_svc("Saves", "load", [s["id"]], null)
	if Kit.ok(lr):
		loaded.emit(s["id"])
		if ui_root != null and ui_root.has_method("close_all"):
			ui_root.close_all()
		else:
			close()
	else:
		_toast(_result_error(lr) if _result_error(lr) != "" else Kit.t("ui.load_failed"), "info")


func _delete_selected() -> void:
	var s := _slot(_selected)
	if s.is_empty() or not s["exists"]:
		return
	var yes: bool = await _ask(Kit.t("ui.saveload.confirm_delete", {"label": s["label"]}))
	if not yes:
		return
	var r = Kit.call_svc("Saves", "delete", [s["id"]], null)
	if Kit.ok(r):
		_toast(Kit.t("ui.toast.deleted"), "save")
	else:
		_toast(_result_error(r), "info")
	refresh()


func _ask(text: String) -> bool:
	if ui_root != null and ui_root.has_method("ask_confirm"):
		return await ui_root.ask_confirm(text)
	return true


func _toast(text: String, kind: String) -> void:
	if ui_root != null and ui_root.get("hud") != null:
		ui_root.hud.toast(text, kind)


func _result_error(r) -> String:
	if r is Dictionary:
		var k := str(r.get("error_key", ""))
		if k != "" and Kit.has_key(k):
			return Kit.t(k)
		return str(r.get("error", ""))
	return Kit.t("ui.saveload.unavailable")


func modal_input(event: InputEvent) -> bool:
	if event is InputEventKey and event.pressed and not event.echo and (event as InputEventKey).physical_keycode == KEY_DELETE:
		_delete_selected()
		return true
	return false


func focus_default() -> void:
	if _rows.has(_selected):
		(_rows[_selected] as Button).grab_focus()
	else:
		_back.grab_focus()
