extends Control
## HUD: objective tracker (from Story.available()), interaction prompt with the bound key,
## toast notifications (evidence / journal / discovery / history / system) and the subtle chapter title card.
## API used by Game: show_prompt(ui_pos, text), hide_prompt(), refresh(), toast(text), show_chapter(title, sub),
## show_hud(), hide_hud(). Exploration (§12): set_prompt_target(node) (UIRoot wires Game.focus_changed) lets the
## prompt mark optional finds — amber spark = not yet discovered, dimmed text + tick = already discovered
## (Interactable.prompt_state()); toasts of kind "discovery" (detected from ui.toast.discovery) show the find
## with its area counter, kind "history" a quiet real-history notice (paper sound, no flourish).
## Memories (§12.10): set_memory(info) replaces the objective tracker by the badge „ERINNERUNG · place · date“
## with the hint how to return (pause key → „In die Gegenwart zurückkehren“); set_memory({}) removes it.

const Kit := preload("res://scripts/ui/ui_kit.gd")

const MAX_OBJECTIVES := 3
const TOAST_TIME := 4.2
const MARGIN := Vector2(48, 42)

var ui_root: Node = null
var _enabled := true          # show_hud / hide_hud
var _suppressed := false      # a modal (dialogue, menus) is covering the play view
var _objective_box: PanelContainer
var _objective_kicker: Label
var _objective_list: VBoxContainer
var _objective_ids: Array = []
var _prompt: Control
var _prompt_panel: PanelContainer
var _prompt_key: Label
var _prompt_keycap: PanelContainer
var _prompt_text: Label
var _prompt_tail: TextureRect
var _prompt_mark: TextureRect
var _prompt_target: Node = null
var _prompt_state := ""
var _prompt_pos := Vector2.ZERO
var _prompt_action := "interact"
var _prompt_wanted := false
var _chapter: Control
var _chapter_kicker: Label
var _chapter_title: Label
var _chapter_sub: Label
var _chapter_tween: Tween
var _toast_layer: Control = null
var _toast_box: VBoxContainer
var _toast_queue: Array = []
var _memory: Dictionary = {}
var _memory_box: PanelContainer
var _memory_kicker: Label
var _memory_place: Label
var _memory_hint: Control
var _memory_hint_box: VBoxContainer

const MEMORY_ICON := "res://assets/ui/memories/icon_memory.png"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(self)
	_build_objectives()
	_build_memory_badge()
	_build_prompt()
	_build_chapter()
	if _toast_layer == null:
		set_toast_layer(self)
	refresh()


# ================================================================ objective tracker
func _build_objectives() -> void:
	_objective_box = Kit.panel("PlatePanel")
	_objective_box.position = MARGIN
	_objective_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_objective_box)
	var v := Kit.vbox(6)
	_objective_box.add_child(v)
	var head := Kit.hbox(12)
	v.add_child(head)
	var ic := Kit.sprite("icons/icon_objective.png")
	head.add_child(ic)
	_objective_kicker = Kit.label(Kit.t("ui.hud.objective").to_upper().replace("ß", "SS"), "KickerLabel")
	_objective_kicker.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_objective_kicker)
	_objective_list = Kit.vbox(4)
	v.add_child(_objective_list)
	_objective_box.visible = false


## Pull the available objectives of the current scene from the Story engine.
func refresh() -> void:
	var ids: Array = []
	var r = Kit.call_svc("Story", "available", [], null)
	if r is Array:
		ids = r
	set_objectives(ids)


func set_objectives(ids: Array) -> void:
	var fresh: Array = []
	var had_previous := not _objective_ids.is_empty()
	for id in ids:
		if not (id in _objective_ids):
			fresh.append(id)
	_objective_ids = ids.duplicate()
	for c in _objective_list.get_children():
		_objective_list.remove_child(c)
		c.queue_free()
	var shown := 0
	for id in ids:
		if shown >= MAX_OBJECTIVES:
			break
		shown += 1
		var l := Kit.label(Kit.objective_text(str(id)), "ObjectiveLabel")
		Kit.scalable(l, 27)
		_objective_list.add_child(l)
		Kit.fit_width(l, 640.0)
		if id in fresh and had_previous and is_inside_tree():
			_flash(l)
	_objective_kicker.text = Kit.t("ui.hud.objective" if ids.size() <= 1 else "ui.hud.objectives").to_upper().replace("ß", "SS")
	_objective_box.reset_size()
	_shrink_objectives.call_deferred()
	_update_visibility()


func _shrink_objectives() -> void:
	_objective_box.reset_size()


func _flash(l: Label) -> void:
	l.modulate = Color(1.35, 1.15, 0.9, 0.0)
	var tw := l.create_tween()
	tw.tween_property(l, "modulate", Color(1.35, 1.15, 0.9, 1.0), 0.35)
	tw.tween_property(l, "modulate", Color.WHITE, 1.4)


# ================================================================ memory badge (§12.10)
func _build_memory_badge() -> void:
	_memory_box = Kit.panel("PlatePanel")
	_memory_box.position = MARGIN
	_memory_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_memory_box.visible = false
	add_child(_memory_box)
	var h := Kit.hbox(18)
	_memory_box.add_child(h)
	var ic := TextureRect.new()
	ic.texture = Kit.optional_tex(MEMORY_ICON)
	ic.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ic.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	ic.visible = ic.texture != null
	h.add_child(ic)
	var v := Kit.vbox(4)
	h.add_child(v)
	_memory_kicker = Kit.label(Kit.t("ui.memories.badge").to_upper().replace("ß", "SS"), "KickerLabel")
	v.add_child(_memory_kicker)
	_memory_place = Kit.label("", "ObjectiveLabel")
	Kit.scalable(_memory_place, 27)
	v.add_child(_memory_place)
	_memory_hint_box = Kit.vbox(0)
	v.add_child(_memory_hint_box)


## info = Game.memory_info() ({} = not inside a memory).
func set_memory(info: Dictionary) -> void:
	_memory = info.duplicate() if info != null else {}
	if not _memory.is_empty():
		var parts: Array = []
		for k in ["place", "date"]:
			if str(_memory.get(k, "")) != "":
				parts.append(str(_memory[k]))
		_memory_place.text = "  ·  ".join(parts)
		_memory_kicker.text = Kit.t("ui.memories.badge").to_upper().replace("ß", "SS")
		_rebuild_memory_hint()
		_memory_box.reset_size()
	_update_visibility()


func is_memory_badge_visible() -> bool:
	return _memory_box != null and _memory_box.visible


func _rebuild_memory_hint() -> void:
	if _memory_hint != null and is_instance_valid(_memory_hint):
		_memory_hint_box.remove_child(_memory_hint)   # out of the layout at once (the badge must not keep its height)
		_memory_hint.queue_free()
	var k := Kit.action_key_text("pause")
	var key := "ui.memories.badge_hint_menu" if bool(_memory.get("from_menu", false)) else "ui.memories.badge_hint"
	_memory_hint = Kit.controls_row([[k if k != "" else Kit.key_name(KEY_ESCAPE), Kit.t(key)]], BoxContainer.ALIGNMENT_BEGIN)
	_memory_hint_box.add_child(_memory_hint)
	_memory_box.reset_size()
	_memory_box.reset_size.call_deferred()


# ================================================================ interaction prompt
func _build_prompt() -> void:
	_prompt = Control.new()
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt.visible = false
	add_child(_prompt)
	_prompt_panel = Kit.panel("PromptPanel")
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt.add_child(_prompt_panel)
	var h := Kit.hbox(14)
	_prompt_panel.add_child(h)
	_prompt_keycap = Kit.panel("KeycapPanel")
	_prompt_keycap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_keycap.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(_prompt_keycap)
	_prompt_key = Kit.label("E", "KeyLabel")
	_prompt_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_key.custom_minimum_size.x = 18
	_prompt_keycap.add_child(_prompt_key)
	_prompt_text = Kit.label("", "BodyLabel", 28)
	_prompt_text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(_prompt_text)
	_prompt_mark = Kit.ex_sprite("icons/mark_new.png")
	_prompt_mark.custom_minimum_size = Vector2(27, 27)
	_prompt_mark.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_prompt_mark.visible = false
	h.add_child(_prompt_mark)
	_prompt_tail = Kit.sprite("icons/prompt_tail.png")
	_prompt.add_child(_prompt_tail)


## ui_pos: anchor point in UI canvas pixels (the tail tip points at it). text: verb ("Untersuchen").
## state: "new" / "found" for exploration hotspots ("" = ask the focused target, see set_prompt_target).
func show_prompt(ui_pos: Vector2, text: String, action := "interact", state := "") -> void:
	_prompt_wanted = true
	_prompt_action = action
	var was_hidden := not _prompt.visible
	_prompt_text.text = text
	_apply_prompt_state(state if state != "" else _target_state())
	refresh_prompt_key()
	_prompt_pos = ui_pos
	_layout_prompt()
	_update_visibility()
	if was_hidden and _prompt.visible:
		Kit.appear(_prompt, 0.14, Vector2(0, 6))


func hide_prompt() -> void:
	_prompt_wanted = false
	_prompt.visible = false


## The interactable the prompt belongs to (UIRoot connects Game.focus_changed here).
func set_prompt_target(target: Node) -> void:
	_prompt_target = target if target != null and is_instance_valid(target) else null


func _target_state() -> String:
	if _prompt_target == null or not is_instance_valid(_prompt_target) or not _prompt_target.has_method("prompt_state"):
		return ""
	return str(_prompt_target.prompt_state())


## "new": amber spark after the verb; "task": side-task mark (§12.9); "found": dimmed verb + tick; "": plain story prompt.
func _apply_prompt_state(state: String) -> void:
	_prompt_state = state
	match state:
		"new":
			_prompt_mark.texture = Kit.ex_tex("icons/mark_new.png")
			_prompt_mark.visible = _prompt_mark.texture != null
			_prompt_text.remove_theme_color_override("font_color")
		"found":
			_prompt_mark.texture = Kit.ex_tex("icons/mark_seen.png")
			_prompt_mark.visible = _prompt_mark.texture != null
			_prompt_text.add_theme_color_override("font_color", Kit.C_TEXT if Kit.high_contrast() else Kit.C_TEXT_DIM)
		"task":   # §12.9: the next step of a side task (falls back to the "new" spark)
			var tt: Texture2D = Kit.optional_tex("res://assets/ui/tasks/mark_task.png")
			_prompt_mark.texture = tt if tt != null else Kit.ex_tex("icons/mark_new.png")
			_prompt_mark.visible = _prompt_mark.texture != null
			_prompt_text.remove_theme_color_override("font_color")
		_:
			_prompt_mark.visible = false
			_prompt_text.remove_theme_color_override("font_color")


func refresh_prompt_key() -> void:
	if _prompt_key == null:
		return
	if not _memory.is_empty() and _memory_hint_box != null:
		_rebuild_memory_hint()
	var k := Kit.action_key_text(_prompt_action)
	_prompt_key.text = k if k != "" else "?"
	_prompt_keycap.visible = k != ""
	if _prompt.visible:
		_layout_prompt.call_deferred()


func _layout_prompt() -> void:
	_prompt_panel.reset_size()
	var sz := _prompt_panel.get_combined_minimum_size()
	_prompt_panel.size = sz
	var tail_sz := Vector2(21, 12)
	var x := roundf(_prompt_pos.x - sz.x * 0.5)
	var y := roundf(_prompt_pos.y - sz.y - tail_sz.y + 3)
	var vp := Vector2(1920, 1080)
	x = clampf(x, 24, vp.x - sz.x - 24)
	y = clampf(y, 24, vp.y - sz.y - 24)
	_prompt.position = Vector2(x, y)
	_prompt_panel.position = Vector2.ZERO
	var tx := clampf(roundf(_prompt_pos.x - x - tail_sz.x * 0.5), 12, sz.x - tail_sz.x - 12)
	tx = floorf(tx / 3.0) * 3.0   # stay on the 3 px art grid
	_prompt_tail.position = Vector2(tx, _prompt_panel.size.y - 3)
	_prompt_tail.size = tail_sz


# ================================================================ chapter card
func _build_chapter() -> void:
	_chapter = Control.new()
	_chapter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chapter.visible = false
	Kit.full_rect(_chapter)
	add_child(_chapter)
	var band := Kit.panel("BandPanel")
	band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	band.set_anchors_preset(Control.PRESET_CENTER_TOP)
	band.offset_left = -470
	band.offset_right = 470
	band.offset_top = 282
	band.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_chapter.add_child(band)
	var v := Kit.vbox(8)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	band.add_child(v)
	_chapter_kicker = Kit.label("", "KickerLabel")
	_chapter_kicker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_chapter_kicker)
	var rule_row := Kit.hbox(14)
	rule_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(rule_row)
	for i in 3:
		if i == 1:
			rule_row.add_child(Kit.sprite("icons/ornament_diamond.png"))
		else:
			var r := Kit.rule(Kit.C_COPPER, 3, 150)
			r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			rule_row.add_child(r)
	_chapter_title = Kit.label("", "HeadingLabel", 62)
	_chapter_title.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	_chapter_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_chapter_title)
	_chapter_sub = Kit.label("", "DimLabel", 27)
	_chapter_sub.add_theme_color_override("font_color", Kit.C_TEXT)
	_chapter_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_chapter_sub)


## Subtle chapter title card: kicker = protagonist (default: Story.active_character).
func show_chapter(title: String, sub := "", kicker := "", hold := 3.6) -> void:
	if kicker == "":
		var who = Kit.svc("Story").get("active_character") if Kit.svc("Story") != null else null
		kicker = Kit.char_name(str(who)) if who != null and str(who) != "" and str(who) != "none" else ""
	_chapter_kicker.text = kicker.to_upper().replace("ß", "SS")
	_chapter_kicker.visible = kicker != ""
	_chapter_title.text = title
	_chapter_sub.text = sub
	_chapter_sub.visible = sub != ""
	if _chapter_tween != null and _chapter_tween.is_valid():
		_chapter_tween.kill()
	_chapter.visible = true
	_chapter.modulate.a = 0.0
	var fade_t := 0.6 if Kit.reduced_motion() else 1.1
	_chapter_tween = create_tween()
	_chapter_tween.tween_property(_chapter, "modulate:a", 1.0, fade_t)
	_chapter_tween.tween_interval(hold)
	_chapter_tween.tween_property(_chapter, "modulate:a", 0.0, fade_t * 1.3)
	_chapter_tween.tween_callback(func(): _chapter.visible = false)


## Alias (contract wording).
func show_chapter_card(title: String, sub := "", kicker := "") -> void:
	show_chapter(title, sub, kicker)


# ================================================================ toasts
func set_toast_layer(layer: Control) -> void:
	_toast_layer = layer
	if _toast_box != null and is_instance_valid(_toast_box):
		_toast_box.queue_free()
	_toast_box = Kit.vbox(12)
	_toast_box.alignment = BoxContainer.ALIGNMENT_BEGIN
	_toast_box.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_toast_box.offset_left = -660
	_toast_box.offset_right = -MARGIN.x
	_toast_box.offset_top = MARGIN.y
	_toast_box.offset_bottom = 600
	_toast_box.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	layer.add_child(_toast_box)


## kind: evidence | journal | person | decision | save | discovery | history | info
## ("" = detect evidence / discovery / history from the text)
func toast(text: String, kind := "") -> void:
	if text == "":
		return
	if kind == "":
		kind = _guess_kind(text)
	_toast_queue.append([text, kind])
	_pump_toasts()


func _guess_kind(text: String) -> String:
	for pair in [["ui.toast.evidence", "evidence"], ["ui.toast.discovery", "discovery"], ["ui.toast.history", "history"], ["ui.toast.task_new", "task_new"], ["ui.toast.task_done", "task_done"]]:
		if not Kit.has_key(pair[0]):
			continue
		var prefix := Kit.t(pair[0]).split("{")[0]
		if prefix.strip_edges() != "" and text.begins_with(prefix):
			return pair[1]
	return "info"


## Strips the "Entdeckt: " / "Historischer Hintergrund: " prefix of a formatted toast.
func _strip_prefix(text: String, key: String) -> String:
	if not Kit.has_key(key):
		return text
	var prefix := Kit.t(key).split("{")[0]
	return text.substr(prefix.length()) if prefix != "" and text.begins_with(prefix) else text


func _pump_toasts() -> void:
	if _toast_box == null or _blocked_for_toasts():
		return
	while not _toast_queue.is_empty() and _toast_box.get_child_count() < 4:
		var e: Array = _toast_queue.pop_front()
		_spawn_toast(e[0], e[1])


func _blocked_for_toasts() -> bool:
	if not _enabled:
		return true
	var top: Control = ui_root.top_modal() if ui_root != null and ui_root.has_method("top_modal") else null
	return top != null and top.get("suppress_toasts") == true


func _spawn_toast(text: String, kind: String) -> void:
	var icon: String = {"evidence": "icon_evidence", "journal": "icon_journal", "person": "icon_person",
		"decision": "icon_decision", "save": "icon_save", "hint": "icon_hint"}.get(kind, "icon_journal")
	var kicker: String = {"evidence": "ui.evidence", "journal": "ui.journal", "person": "ui.journal.tab.people",
		"decision": "ui.journal.tab.decisions"}.get(kind, "")
	var body := text
	if kind == "evidence":
		var fmt := Kit.t("ui.toast.evidence")
		var prefix := fmt.split("{")[0]
		if text.begins_with(prefix):
			body = text.substr(prefix.length())
		kicker = ""
	var counter := ""
	if kind == "discovery":
		body = _strip_prefix(text, "ui.toast.discovery")
		var m := RegEx.create_from_string("\\s*\\((\\d+)\\s*/\\s*(\\d+)\\)\\s*$").search(body)
		if m != null:
			counter = "%s / %s" % [m.get_string(1), m.get_string(2)]
			body = body.substr(0, m.get_start())
	elif kind == "history":
		body = _strip_prefix(text, "ui.toast.history")
	elif kind == "task_new" or kind == "task_done":
		body = _strip_prefix(text, "ui.toast." + kind)
	var p := Kit.panel("PlatePanel")
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var h := Kit.hbox(16)
	p.add_child(h)
	var ic: TextureRect
	if kind == "discovery" or kind == "history":
		ic = Kit.ex_sprite("icons/icon_%s.png" % kind)
	else:
		ic = Kit.sprite("icons/%s.png" % icon)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ic)
	var v := Kit.vbox(2)
	h.add_child(v)
	var kick_text := Kit.t("ui.toast.evidence").split("{")[0].strip_edges().trim_suffix(":") if kind == "evidence" else (Kit.t(kicker) if kicker != "" else "")
	if kind == "discovery":
		kick_text = Kit.t("ui.explore.toast.discovery_kicker")
	elif kind == "history":
		kick_text = Kit.t("ui.history.kicker")
	elif kind == "task_new" or kind == "task_done":
		kick_text = Kit.t("ui.toast." + kind).split("{")[0].strip_edges().trim_suffix(":")
	if kick_text != "":
		var kl := Kit.label(kick_text.to_upper().replace("ß", "SS"), "KickerLabel")
		if kind == "history":
			kl.add_theme_color_override("font_color", Kit.C_TEXT_DIM)
		if counter != "":
			var kr := Kit.hbox(18)
			kr.add_child(kl)
			var cl := Kit.label(counter, "HintLabel")
			cl.size_flags_vertical = Control.SIZE_SHRINK_END
			kr.add_child(cl)
			v.add_child(kr)
		else:
			v.add_child(kl)
	var l := Kit.label(body, "BodyLabel", 27)
	v.add_child(l)
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.size_flags_horizontal = Control.SIZE_SHRINK_END
	holder.add_child(p)
	_toast_box.add_child(holder)
	Kit.fit_width(l, 520.0)
	var sz := p.get_combined_minimum_size()
	holder.custom_minimum_size = sz
	p.size = sz
	Kit.appear(p, 0.24, Vector2(48, 0))
	Kit.ui_sound("history" if kind == "history" else "toast")
	var tw := holder.create_tween()
	tw.tween_interval(TOAST_TIME)
	tw.tween_property(holder, "modulate:a", 0.0, 0.5)
	tw.tween_callback(func():
		holder.queue_free()
		_pump_toasts.call_deferred())


# ================================================================ visibility
func show_hud() -> void:
	_enabled = true
	_update_visibility()
	_pump_toasts()


func hide_hud() -> void:
	_enabled = false
	_update_visibility()


func set_hud_visible(on: bool) -> void:
	if on:
		show_hud()
	else:
		hide_hud()


## Called by UIRoot whenever the modal stack changes.
func on_modal_changed(top: Control) -> void:
	_suppressed = top != null
	_update_visibility()
	if top == null:
		_pump_toasts()


func _update_visibility() -> void:
	var play := _enabled and not _suppressed
	_objective_box.visible = play and not _objective_ids.is_empty() and _memory.is_empty()
	if _memory_box != null:
		var was := _memory_box.visible
		_memory_box.visible = play and not _memory.is_empty()
		if _memory_box.visible and not was and is_inside_tree():
			# Kit.appear slides back to the position it finds: shown again while an earlier slide still runs (a
			# panel opened and closed quickly), the badge would otherwise stay shifted to the left for good
			_memory_box.position = MARGIN
			Kit.appear(_memory_box, 0.4, Vector2(-18, 0))
	_prompt.visible = play and _prompt_wanted
	if not _enabled:
		_chapter.visible = false
	if _toast_box != null:
		_toast_box.visible = (_enabled or (ui_root != null and ui_root.has_method("is_modal_open") and ui_root.is_modal_open())) 			and not _blocked_by_modal()


func _blocked_by_modal() -> bool:
	var top: Control = ui_root.top_modal() if ui_root != null and ui_root.has_method("top_modal") else null
	return top != null and top.get("suppress_toasts") == true
