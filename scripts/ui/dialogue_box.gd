extends "res://scripts/ui/ui_modal.gd"
## Dialogue box (bottom of the screen): 112x112 portrait strip shown x3 (nearest) with expressions from
## portrait.json, speaker name (Loc "char.<id>.name"), typewriter text honouring Settings.dialogue_speed,
## advance via the `advance` action / click (first press completes the line), choice list with keyboard /
## controller focus, and a history log (H / button).
## API: show_line(speaker_id, text, expression), show_choices([{id, text}]) -> signal chosen(id),
##      signal advanced, close() / hide_box(), skip_typing(), clear_history().
## Living portraits: when portrait.json has an "anim" block (grid portrait_anim.png: column = expression,
## rows = rest, talk_half, talk_open, blink, blink_talk_half, blink_talk_open) the mouth moves while the
## typewriter types (shape picked from the last revealed letter, rests on punctuation pauses and at the end of
## the line) and the eyes blink every few seconds; the expression column never changes within a line.
## Strips without "anim" stay static; speakers without a portrait keep the silhouette placeholder.

signal advanced
signal chosen(id: String)
signal line_finished

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const BASE_CPS := 42.0
const PORTRAIT := 112
const PLACEHOLDER := "res://assets/ui/portrait_placeholder.png"
const HISTORY_ACTION := "ui_dialogue_history"

var history: Array = []          # [{speaker, text}]
var suppress_toasts := false
var _row: HBoxContainer
## true: box docks at the top edge (Game sets this when the speakers stand in the lower part of the frame,
## so the dialogue never covers the people who are talking).
var dock_top := false:
	set(v):
		dock_top = v
		_apply_dock()
var _portrait_panel: PanelContainer
var _portrait: TextureRect
var _text_panel: PanelContainer
var _speaker: Label
var _text: Label
var _choices_box: VBoxContainer
var _choice_kicker: Label
var _advance_arrow: TextureRect
var _history_btn: Button
var _history_panel: Control
var _history_list: VBoxContainer
var _history_scroll: ScrollContainer
var _typing := false
var _shown := 0.0
var _delay := 0.0
var _pending_choices: Array = []
var _choice_texts: Dictionary = {}
var _choices_active := false
var _choices_since := 0          # ticks (ms) when choices appeared: guards against mashed confirm keys
const CHOICE_GUARD_MS := 450
var _speaker_id := ""
var _portrait_cache: Dictionary = {}
var _blink := 0.0
# ---- living portrait state
const MOUTH_REST := 0
const MOUTH_HALF := 1
const MOUTH_OPEN := 2
const VOWELS := "aeiouyäöüAEIOUYÄÖÜаеёиоуыэюяАЕЁИОУЫЭЮЯ"
const LABIALS := "mbpMBPмбпМБП"
var _p_entry: Dictionary = {}      # cache entry of the current speaker (tex, anim, size, ...)
var _p_atlas: AtlasTexture = null  # region is moved per frame (no texture churn)
var _p_col := 0
var _p_mouth := MOUTH_REST
var _p_eyes_closed := false
var _p_mouth_t := 0.0
var _p_blink_t := 0.0
var _p_next_blink := 3.0
var _p_blink_left := 0.0
var _p_double := false
var _p_rng := RandomNumberGenerator.new()


func _ready() -> void:
	pauses_game = false
	closes_on_cancel = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	_ensure_history_action()
	_build()


func _ensure_history_action() -> void:
	if InputMap.has_action(HISTORY_ACTION):
		return
	InputMap.add_action(HISTORY_ACTION)
	var k := InputEventKey.new()
	k.physical_keycode = KEY_H
	InputMap.action_add_event(HISTORY_ACTION, k)
	var j := InputEventJoypadButton.new()
	j.button_index = JOY_BUTTON_X
	InputMap.action_add_event(HISTORY_ACTION, j)


func _build() -> void:
	_row = Kit.hbox(0)
	_row.alignment = BoxContainer.ALIGNMENT_BEGIN
	add_child(_row)
	_apply_dock()

	_portrait_panel = Kit.panel("PortraitPanel")
	_portrait_panel.size_flags_vertical = Control.SIZE_SHRINK_END
	_portrait_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_row.add_child(_portrait_panel)
	_portrait = TextureRect.new()
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_SCALE
	_portrait.custom_minimum_size = Vector2(PORTRAIT * 3, PORTRAIT * 3)
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait_panel.add_child(_portrait)

	_text_panel = Kit.panel("DialoguePanel")
	_text_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_text_panel.size_flags_vertical = Control.SIZE_SHRINK_END
	_text_panel.custom_minimum_size.y = 204
	_text_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_row.add_child(_text_panel)
	_apply_dock()
	var v := Kit.vbox(8)
	_text_panel.add_child(v)
	var head := Kit.hbox(16)
	v.add_child(head)
	_speaker = Kit.label("", "SpeakerLabel")
	_speaker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(_speaker)
	_history_btn = Kit.button(Kit.t("ui.dlg.history").to_upper().replace("ß", "SS") + "  ·  H", "SmallButton")
	_history_btn.focus_mode = Control.FOCUS_NONE
	_history_btn.pressed.connect(toggle_history)
	head.add_child(_history_btn)
	var sep := HSeparator.new()
	sep.theme_type_variation = "FaintSeparator"
	sep.add_theme_constant_override("separation", 6)
	v.add_child(sep)
	_text = Kit.wrap_label("", "DialogueLabel")
	_text.visible_characters_behavior = TextServer.VC_CHARS_AFTER_SHAPING
	_text.custom_minimum_size = Vector2(800, 0)
	Kit.scalable(_text, 34)
	v.add_child(_text)
	_choice_kicker = Kit.label(Kit.t("ui.dlg.decision").to_upper().replace("ß", "SS"), "KickerLabel")
	_choice_kicker.visible = false
	v.add_child(_choice_kicker)
	_choices_box = Kit.vbox(2)
	_choices_box.visible = false
	v.add_child(_choices_box)
	var foot := Kit.hbox(0)
	foot.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(foot)
	_advance_arrow = Kit.sprite("icons/advance_arrow.png")
	_advance_arrow.custom_minimum_size = Vector2(27, 18)
	foot.add_child(_advance_arrow)
	_build_history()


func _apply_dock() -> void:
	# Top-docked, the box occupies the toast column's corner: the HUD then queues toasts until it closes.
	suppress_toasts = dock_top
	if _row == null:
		return
	if dock_top:
		_row.set_anchors_preset(Control.PRESET_TOP_WIDE)
		_row.offset_top = 42
		_row.offset_bottom = 42
		_row.grow_vertical = Control.GROW_DIRECTION_END
	else:
		_row.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
		_row.offset_top = -42
		_row.offset_bottom = -42
		_row.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_row.offset_left = 96
	_row.offset_right = -96
	# hug the docked edge: text panel and portrait align to the top when docked at the top
	var flag := Control.SIZE_SHRINK_BEGIN if dock_top else Control.SIZE_SHRINK_END
	if _portrait_panel:
		_portrait_panel.size_flags_vertical = flag
	if _text_panel:
		_text_panel.size_flags_vertical = flag


func _build_history() -> void:
	_history_panel = Control.new()
	_history_panel.visible = false
	Kit.full_rect(_history_panel)
	_history_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_history_panel)
	_history_panel.add_child(Kit.dimmer(0.55))
	var p := Kit.panel("SolidPanel")
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -600
	p.offset_right = 600
	p.offset_top = -420
	p.offset_bottom = 330
	_history_panel.add_child(p)
	var v := Kit.vbox(14)
	p.add_child(v)
	var head := Kit.hbox(16)
	v.add_child(head)
	var t := Kit.label(Kit.t("ui.dlg.history_title"), "HeadingLabel", 40)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	var close_btn := Kit.button(Kit.t("ui.common.close"), "SmallButton")
	close_btn.pressed.connect(toggle_history)
	head.add_child(close_btn)
	v.add_child(HSeparator.new())
	_history_scroll = ScrollContainer.new()
	_history_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_history_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(_history_scroll)
	_history_list = Kit.vbox(18)
	_history_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_history_scroll.add_child(_history_list)


# ================================================================ API
func show_line(speaker_id: String, text: String, expression := "neutral") -> void:
	if not is_open:
		open_modal()
	_clear_choices()
	_speaker_id = speaker_id
	var line := Kit.resolve(text)
	_speaker.text = Kit.char_name(speaker_id).to_upper().replace("ß", "SS")
	_speaker.visible = speaker_id != ""
	_set_portrait(speaker_id, expression)
	_text.text = line
	history.append({"speaker": speaker_id, "text": line})
	var speed := float(Kit.setting("dialogue_speed", 1.0))
	if speed <= 0.0:
		_text.visible_characters = -1
		_typing = false
	else:
		_text.visible_characters = 0
		_shown = 0.0
		_delay = 0.0
		_typing = true
	_advance_arrow.modulate.a = 0.0 if _typing else 1.0
	if not _typing:
		line_finished.emit()


## choices: [{id, text}] (text may be a loc key). Shown once the current line has finished typing.
func show_choices(choices: Array) -> void:
	if not is_open:
		open_modal()
	_pending_choices = choices.duplicate(true)
	if not _typing:
		_present_choices()


func hide_box() -> void:
	close()


func skip_typing() -> void:
	if _typing:
		_finish_typing()


func is_typing() -> bool:
	return _typing


func clear_history() -> void:
	history.clear()


## Optional convenience for Game: plays a whole dialogue objective through the Story API.
func play_objective(obj_id: String, expressions: Dictionary = {}) -> bool:
	var r = Kit.call_svc("Story", "start_dialogue", [obj_id], null)
	if not Kit.ok(r):
		return false
	for _i in 64:
		var line = Kit.call_svc("Story", "current_dialogue_line", [obj_id], {})
		if not (line is Dictionary) or line.is_empty() or line.has("error"):
			break
		show_line(str(line.get("speaker", "")), Kit.t(str(line.get("text_key", ""))),
			str(expressions.get(str(line.get("node", "")), "neutral")))
		await advanced
		var adv = Kit.call_svc("Story", "advance_dialogue", [obj_id], {})
		if not Kit.ok(adv) or bool(adv.get("finished", false)):
			break
	close()
	return true


# ================================================================ portrait
func _set_portrait(speaker_id: String, expression: String) -> void:
	if speaker_id == "":
		_portrait_panel.visible = false
		_p_entry = {}
		return
	_portrait_panel.visible = true
	var entry := _portrait_entry(speaker_id)
	var tex2: Texture2D = entry["tex"]
	if tex2 == null:
		_p_entry = {}
		_portrait.texture = Kit.tex(PLACEHOLDER)
		return
	var sz: Vector2i = entry["size"]
	var frames := maxi(1, int(tex2.get_width() / maxi(1, sz.x)))
	var idx: int = maxi(0, (entry["expressions"] as Array).find(expression))
	idx = clampi(idx, 0, frames - 1)
	var same_speaker: bool = not _p_entry.is_empty() and _p_entry.get("id", "") == speaker_id
	_p_entry = entry
	_p_col = idx
	if _p_atlas == null:
		_p_atlas = AtlasTexture.new()
	var anim: Texture2D = entry.get("anim_tex")
	_p_atlas.atlas = anim if anim != null else tex2
	_p_mouth = MOUTH_REST
	_p_mouth_t = 0.0
	if not same_speaker:
		# a new face on screen: eyes open, first blink after a short random wait
		_p_eyes_closed = false
		_p_blink_left = 0.0
		_p_blink_t = 0.0
		_p_rng.seed = speaker_id.hash() & 0x7fffffff
		_p_next_blink = _p_rng.randf_range(1.2, 2.6)
	_portrait.texture = _p_atlas
	_portrait.custom_minimum_size = Vector2(sz) * 3
	_apply_portrait_frame()


## Loads (once) the portrait strip, its metadata and the optional animation grid of a speaker.
func _portrait_entry(speaker_id: String) -> Dictionary:
	var look: String = SpriteRig.look_of(speaker_id)     # round 8: per-scene look (soot / night portraits)
	var entry: Dictionary = _portrait_cache.get(look, {})
	if not entry.is_empty():
		return entry
	var dir := Kit.CHAR_DIR + look + "/"
	var t2 := Kit.optional_tex(dir + "portrait.png")
	var meta = Kit.json(dir + "portrait.json")
	var size := Vector2i(PORTRAIT, PORTRAIT)
	var exprs: Array = ["neutral"]
	var anim_tex: Texture2D = null
	var rows: Array = []
	var anim_meta: Dictionary = {}
	if meta is Dictionary:
		var s = meta.get("size", [PORTRAIT, PORTRAIT])
		if s is Array and s.size() >= 2:
			size = Vector2i(int(s[0]), int(s[1]))
		exprs = meta.get("expressions", exprs)
		var a = meta.get("anim")
		if t2 != null and a is Dictionary and str(a.get("file", "")) != "":
			anim_tex = Kit.optional_tex(dir + str(a["file"]))
			rows = a.get("rows", [])
			anim_meta = a
			# the grid must really hold every expression column and every documented row
			if anim_tex != null and (anim_tex.get_width() < size.x * exprs.size() or rows.is_empty()
					or anim_tex.get_height() < size.y * rows.size()):
				anim_tex = null
	entry = {"id": speaker_id, "tex": t2, "size": size, "expressions": exprs, "anim_tex": anim_tex,
		"rows": rows, "blink_offset": int(anim_meta.get("blink_offset", 3)),
		"mouth_fps": float(anim_meta.get("mouth_fps", 11.0)), "blink_ms": float(anim_meta.get("blink_ms", 130.0)),
		"blink_interval": anim_meta.get("blink_interval_s", [2.6, 5.2])}
	_portrait_cache[look] = entry
	return entry


func _p_animated() -> bool:
	return not _p_entry.is_empty() and _p_entry.get("anim_tex") != null


func _apply_portrait_frame() -> void:
	if _p_atlas == null or _p_entry.is_empty():
		return
	var sz: Vector2i = _p_entry["size"]
	var row := 0
	if _p_animated():
		var rows: Array = _p_entry["rows"]
		row = _p_mouth + (int(_p_entry["blink_offset"]) if _p_eyes_closed else 0)
		row = clampi(row, 0, rows.size() - 1)
	_p_atlas.region = Rect2(_p_col * sz.x, row * sz.y, sz.x, sz.y)


## Mouth shape for the text revealed so far: vowels open, labials and gaps close, the rest half-open.
func _mouth_for_text() -> int:
	var n := _text.visible_characters
	if n <= 0:
		return MOUTH_REST
	var ch := _text.text.substr(n - 1, 1)
	if ch == " " or ch == "\n" or LABIALS.contains(ch) or not (ch.to_upper().replace("ß", "SS") != ch.to_lower() or ch.is_valid_int()):
		return MOUTH_REST
	if VOWELS.contains(ch):
		return MOUTH_HALF if _p_mouth == MOUTH_OPEN else MOUTH_OPEN
	return MOUTH_HALF


func _animate_portrait(delta: float) -> void:
	if not _p_animated() or not _portrait_panel.visible:
		return
	var changed := false
	# ---- mouth: follows the typewriter, at most mouth_fps changes per second
	var want := MOUTH_REST
	if _typing and _delay <= 0.0:
		_p_mouth_t += delta
		var step := 1.0 / maxf(1.0, float(_p_entry["mouth_fps"]) * (0.5 if Kit.reduced_motion() else 1.0))
		if _p_mouth_t >= step:
			_p_mouth_t = fmod(_p_mouth_t, step)
			want = _mouth_for_text()
			if Kit.reduced_motion() and want == MOUTH_OPEN:
				want = MOUTH_HALF
		else:
			want = _p_mouth
	if want != _p_mouth:
		_p_mouth = want
		changed = true
	# ---- blink: every few seconds, sometimes twice
	if _p_blink_left > 0.0:
		_p_blink_left -= delta
		if _p_blink_left <= 0.0:
			_p_eyes_closed = false
			changed = true
			if _p_double:
				_p_double = false
				_p_next_blink = 0.16
	else:
		_p_blink_t += delta
		if _p_blink_t >= _p_next_blink:
			_p_blink_t = 0.0
			var iv: Array = _p_entry.get("blink_interval", [2.6, 5.2])
			_p_next_blink = _p_rng.randf_range(float(iv[0]), float(iv[1])) if iv.size() >= 2 else 3.6
			_p_eyes_closed = true
			_p_blink_left = float(_p_entry["blink_ms"]) / 1000.0
			_p_double = _p_rng.randf() < 0.18
			changed = true
	if changed:
		_apply_portrait_frame()


## Test / debug view of the living portrait (read-only).
func portrait_state() -> Dictionary:
	var region := _p_atlas.region if _p_atlas != null else Rect2()
	return {"speaker": _speaker_id, "animated": _p_animated(), "column": _p_col, "mouth": _p_mouth,
		"eyes_closed": _p_eyes_closed, "region": region,
		"placeholder": _portrait.texture == Kit.tex(PLACEHOLDER)}


# ================================================================ typewriter
func _process(delta: float) -> void:
	if not is_open:
		return
	var was_typing := _typing
	if _typing:
		_type(delta)
	_animate_portrait(delta)
	if not was_typing and _advance_arrow.visible and not _choices_active:
		_blink += delta
		if Kit.reduced_motion():
			_advance_arrow.modulate.a = 1.0
		else:
			_advance_arrow.modulate.a = 0.55 + 0.45 * absf(sin(_blink * 2.6))


func _type(delta: float) -> void:
	var speed := maxf(0.05, float(Kit.setting("dialogue_speed", 1.0)))
	var cps := BASE_CPS * speed
	if _delay > 0.0:
		_delay -= delta
		return
	var total := _text.get_total_character_count()
	_shown += delta * cps
	var n := int(_shown)
	if n > _text.visible_characters:
		var prev := maxi(0, _text.visible_characters)
		_text.visible_characters = mini(n, total)
		var last := _text.text.substr(_text.visible_characters - 1, 1) if _text.visible_characters > 0 else ""
		if _text.visible_characters > prev:
			if last in [".", "!", "?", "…", ":"]:
				_delay = 0.28 / speed
			elif last in [",", ";", "–"]:
				_delay = 0.12 / speed
	if _text.visible_characters >= total:
		_finish_typing()


func _finish_typing() -> void:
	_typing = false
	_text.visible_characters = -1
	_advance_arrow.modulate.a = 1.0
	_blink = 0.0
	if _p_mouth != MOUTH_REST:
		_p_mouth = MOUTH_REST
		_apply_portrait_frame()
	line_finished.emit()
	if not _pending_choices.is_empty():
		_present_choices()


# ================================================================ choices
func _present_choices() -> void:
	_clear_choices()
	var choices := _pending_choices
	_pending_choices = []
	_choices_active = true
	_choices_since = Time.get_ticks_msec()
	_choice_kicker.visible = true
	_choices_box.visible = true
	_advance_arrow.visible = false
	var i := 0
	for c in choices:
		i += 1
		var id := str(c.get("id", i)) if c is Dictionary else str(c)
		var txt := Kit.resolve(str(c.get("text", c.get("text_key", id)))) if c is Dictionary else str(c)
		_choice_texts[id] = txt
		var b := Kit.button("%d.   %s" % [i, txt], "ChoiceButton")
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		Kit.scalable(b, 32)
		b.pressed.connect(_on_choice.bind(id))
		b.mouse_entered.connect(b.grab_focus)
		_choices_box.add_child(b)
	_wire_focus(_choices_box)
	if _choices_box.get_child_count() > 0:
		(_choices_box.get_child(0) as Control).grab_focus.call_deferred()


func _wire_focus(box: Container) -> void:
	var n := box.get_child_count()
	for k in n:
		var b := box.get_child(k) as Control
		b.focus_neighbor_top = b.get_path_to(box.get_child((k - 1 + n) % n))
		b.focus_neighbor_bottom = b.get_path_to(box.get_child((k + 1) % n))
		b.focus_neighbor_left = b.get_path()
		b.focus_neighbor_right = b.get_path()


func _clear_choices() -> void:
	_choices_active = false
	for c in _choices_box.get_children():
		c.queue_free()
	_choices_box.visible = false
	_choice_kicker.visible = false
	_advance_arrow.visible = true


func _on_choice(id: String) -> void:
	if not _choices_active:
		return
	Kit.ui_sound("confirm")
	var label := str(_choice_texts.get(id, ""))
	_clear_choices()
	_choice_texts.clear()
	if label != "":
		history.append({"speaker": "", "text": "→ " + label, "choice": true})
	chosen.emit(id)


# ================================================================ input
func modal_input(event: InputEvent) -> bool:
	if _history_panel.visible:
		if event.is_action_pressed(HISTORY_ACTION) or event.is_action_pressed("cancel") or event.is_action_pressed("ui_cancel"):
			toggle_history()
			return true
		return event is InputEventKey and not (event.is_action("ui_up") or event.is_action("ui_down") or event.is_action("ui_page_up") or event.is_action("ui_page_down"))
	if event.is_action_pressed(HISTORY_ACTION):
		toggle_history()
		return true
	if _choices_active:
		# A decision must never be taken by a confirm key that was still being mashed for the previous line.
		if Time.get_ticks_msec() - _choices_since < CHOICE_GUARD_MS and (event.is_action_pressed("advance") 				or event.is_action_pressed("ui_accept") or event.is_action_pressed("interact")):
			return true
		if event is InputEventKey and event.pressed and not event.echo:
			var k := (event as InputEventKey).physical_keycode
			if k >= KEY_1 and k <= KEY_9:
				var i := int(k - KEY_1)
				if i < _choices_box.get_child_count():
					(_choices_box.get_child(i) as Button).pressed.emit()
				return true
		if event.is_action_pressed("advance") and not event.is_action_pressed("ui_accept"):
			var f := get_viewport().gui_get_focus_owner()
			if f is Button and _choices_box.is_ancestor_of(f):
				(f as Button).pressed.emit()
				return true
		return false
	if event.is_action_pressed("advance") or event.is_action_pressed("ui_accept"):
		_advance()
		return true
	if event.is_action_pressed("skip") and not event.is_action_pressed("cancel"):
		_advance()
		return true
	return false


func handle_cancel() -> bool:
	if _history_panel.visible:
		toggle_history()
	elif _typing:
		_finish_typing()
	return true


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if not _choices_active and not _history_panel.visible:
			_advance()
			accept_event()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
		if not _history_panel.visible and not history.is_empty():
			toggle_history()
			accept_event()


func _advance() -> void:
	if _typing:
		_finish_typing()
		return
	if _choices_active or not _pending_choices.is_empty():
		return
	Kit.ui_sound("advance")
	advanced.emit()


func toggle_history() -> void:
	if _history_panel.visible:
		_history_panel.visible = false
		return
	for c in _history_list.get_children():
		c.queue_free()
	if history.is_empty():
		_history_list.add_child(Kit.label(Kit.t("ui.dlg.history_empty"), "DimLabel"))
	for e in history:
		var v := Kit.vbox(2)
		var sp := str(e.get("speaker", ""))
		if sp != "":
			v.add_child(Kit.label(Kit.char_name(sp).to_upper().replace("ß", "SS"), "SpeakerLabel", 22))
		var l := Kit.wrap_label(str(e.get("text", "")), "DimLabel" if e.get("choice", false) else "BodyLabel")
		Kit.scalable(l, 26 if e.get("choice", false) else 29)
		v.add_child(l)
		_history_list.add_child(v)
	_history_panel.visible = true
	_scroll_history_to_end.call_deferred()


func _scroll_history_to_end() -> void:
	await get_tree().process_frame
	_history_scroll.scroll_vertical = int(_history_scroll.get_v_scroll_bar().max_value)


func _on_open() -> void:
	_history_panel.visible = false


func _on_close() -> void:
	_typing = false
	_p_mouth = MOUTH_REST
	_p_eyes_closed = false
	_p_blink_left = 0.0
	_apply_portrait_frame()
	_pending_choices = []
	_clear_choices()
	_history_panel.visible = false


func focus_default() -> void:
	if _choices_active and _choices_box.get_child_count() > 0:
		(_choices_box.get_child(0) as Control).grab_focus()
