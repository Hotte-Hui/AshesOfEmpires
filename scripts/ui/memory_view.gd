extends "res://scripts/ui/ui_modal.gd"
## MemoryView „Erinnerungen“ (TECHNICAL_ARCHITECTURE §12.10): one photograph card per walkable scene in story
## order (rows of three). An unlocked card shows the sepia print of the place (assets/ui/memories/<scene>.png),
## the chapter, the place and date, who was there and the finds counter (Explore.counts); choosing it starts the
## „Zeitreise“ (Game.travel_to_memory). Locked cards stay an unexposed print: „Noch nicht erlebt“, no names, no
## image (no spoilers). The scene the player stands in right now is shown but cannot be chosen.
## open(context): "game" (pause menu; unlocked = completed in this playthrough) or "menu" (main menu; unlocked =
## completed at least once, from the profile). Second page „Filmsequenzen“: every cinematic already seen can be
## watched again (Game.rewatch_film). Keyboard / pad: arrows or WASD move, Enter / Space / A choose, Q / E or
## LB / RB switch the page, Esc / B back; mouse: hover selects, click chooses, the page tabs are clickable.
## Text scale and high contrast follow the settings.
## Data: Game.memory_scenes(context) -> [{id, unlocked, current, place, date, chapter, who, thumb, found, total}],
## Game.memory_films(context) -> [{id, unlocked, title, sub}].

signal travel_requested(scene_id: String, from_menu: bool)
signal film_requested(film_id: String, from_menu: bool)

const PAGES := ["scenes", "films"]

const COLUMNS := 3
const PHOTO := Vector2(320, 180)          ## print size in UI px (the thumbnails are stored 1:1)
const MOUNT_PAD := Vector2(42, 45)        ## photo_mount.png 9-slice content margins (l+r, t+b)
const TEXT_W := 470.0                     ## caption width (wider than the print: date · person · finds in one row)
const C_UNEXPOSED := Color("1d1914")
const C_UNEXPOSED_HC := Color("2a2a2a")

var context := "game"
var page := "scenes"
var cards: Array = []
var films: Array = []
## scene id (page "scenes") or film id (page "films") -> card Button (unlocked and selectable cards only)
var buttons: Dictionary = {}
var _tabs: Dictionary = {}
var _tab_group := ButtonGroup.new()
var suppress_toasts := true
var _rows: VBoxContainer
var _scroll: ScrollContainer
var _subtitle: Label
var _note: Label
var _empty: Label
var _footer: Control
var _footer_box: VBoxContainer
var _selected := ""


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.95))   # the panel it was opened from (pause / main menu) stays out of sight
	var root := Kit.vbox(0)
	Kit.full_rect(root)
	root.offset_left = 150
	root.offset_right = -150
	root.offset_top = 52
	root.offset_bottom = -40
	add_child(root)
	var head := Kit.hbox(40)
	root.add_child(head)
	var left := Kit.vbox(6)
	left.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(left)
	var title := Kit.label(Kit.t("ui.memories.title"), "HeadingLabel")
	left.add_child(title)
	var tabs := Kit.hbox(6)
	left.add_child(tabs)
	for id in PAGES:
		var tb := Kit.button(Kit.t("ui.memories.page." + id).to_upper().replace("ß", "SS"), "TabButton")
		tb.toggle_mode = true
		tb.button_group = _tab_group
		tb.focus_mode = Control.FOCUS_NONE        # Q / E and the mouse switch pages; arrows stay on the cards
		tb.pressed.connect(show_page.bind(id))
		tabs.add_child(tb)
		_tabs[id] = tb
	var right := Kit.vbox(2)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_SHRINK_END
	head.add_child(right)
	_subtitle = Kit.wrap_label("", "DimLabel")
	_subtitle.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	_subtitle.add_theme_color_override("font_color", Kit.C_TEXT)
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	Kit.scalable(_subtitle, 26)
	right.add_child(_subtitle)
	# what a memory is (nothing changes, nothing is saved, finds are kept) — right under the subtitle
	_note = Kit.wrap_label("", "DimLabel")
	_note.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	Kit.scalable(_note, 22)
	right.add_child(_note)
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 8))
	root.add_child(Kit.rule(Kit.C_COPPER_D, 3))
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 14))
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.follow_focus = true
	root.add_child(_scroll)
	var pad := Kit.margin(0, 4, 0, 4)
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(pad)
	_rows = Kit.vbox(14)
	_rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_child(_rows)
	_empty = Kit.wrap_label("", "BodyLabel")
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(_empty, 28)
	_empty.visible = false
	root.add_child(_empty)
	root.add_child(Kit.rule(Color(0, 0, 0, 0), 8))
	_footer_box = Kit.vbox(0)
	root.add_child(_footer_box)
	_build_footer()


func _build_footer() -> void:
	if _footer != null and is_instance_valid(_footer):
		_footer_box.remove_child(_footer)
		_footer.queue_free()
	_footer = Kit.controls_row([[Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT), Kit.t("ui.memories.hint.select")],
		[Kit.key_name(KEY_ENTER), Kit.t("ui.memories.hint.travel" if page == "scenes" else "ui.memories.hint.watch")],
		["Q|E", Kit.t("ui.memories.hint.page")], [Kit.key_name(KEY_ESCAPE), Kit.t("ui.memories.hint.back")]])
	_footer_box.add_child(_footer)


## context "game" | "menu"; page "scenes" (default) | "films".
func open(ctx := "game", start_page := "scenes") -> void:
	context = "menu" if ctx == "menu" else "game"
	page = start_page if start_page in PAGES else "scenes"
	open_modal()
	refresh()


func show_page(id: String) -> void:
	if not (id in PAGES):
		return
	if id != page:
		Kit.ui_sound("page")
	page = id
	_selected = ""
	refresh()


func cycle_page(d: int) -> void:
	show_page(PAGES[(PAGES.find(page) + d + PAGES.size()) % PAGES.size()])


func refresh() -> void:
	cards = collect()
	films = collect_films()
	(_tabs[page] as Button).button_pressed = true
	var keep := _selected
	_selected = ""
	for c in _rows.get_children():
		_rows.remove_child(c)
		c.queue_free()
	buttons.clear()
	var row: HBoxContainer = null
	var n := 0
	var any_open := false
	var list: Array = cards if page == "scenes" else films
	for c in list:
		if n % COLUMNS == 0:
			row = Kit.hbox(36)
			row.alignment = BoxContainer.ALIGNMENT_CENTER
			_rows.add_child(row)
		n += 1
		row.add_child(_make_card(c) if page == "scenes" else _make_film(c))
		if bool(c.get("unlocked", false)):
			any_open = true
	_subtitle.text = Kit.t(("ui.memories.subtitle_films." if page == "films" else "ui.memories.subtitle.") + context)
	_note.text = Kit.t("ui.memories.note.menu" if context == "menu" else "ui.memories.note.game")
	_empty.text = Kit.t("ui.memories.empty" if page == "scenes" else "ui.memories.empty_films")
	_empty.visible = not any_open
	_build_footer()
	if keep != "" and buttons.has(keep):
		_selected = keep
	if is_open:
		focus_default.call_deferred()


func collect() -> Array:
	var r = Kit.call_svc("Game", "memory_scenes", [context], null)
	return r if r is Array else []


func collect_films() -> Array:
	var r = Kit.call_svc("Game", "memory_films", [context], null)
	return r if r is Array else []


func is_selectable(c: Dictionary) -> bool:
	return bool(c.get("unlocked", false)) and not bool(c.get("current", false))


func _card(id: String) -> Dictionary:
	for c in cards:
		if str(c.get("id", "")) == id:
			return c
	return {}


# ================================================================ cards
## A card = a zero-margin container that sizes itself from its content; the transparent CardButton fills the
## same rect on top (focus frame, hover, click), so text scale can grow the card freely.
func _make_card(c: Dictionary) -> Control:
	var id := str(c.get("id", ""))
	var open_card := bool(c.get("unlocked", false))
	var current := bool(c.get("current", false))
	var card := Kit.margin(0, 0, 0, 0)
	card.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	var m := Kit.margin(15, 12, 15, 16)
	card.add_child(m)
	var b := Kit.button("", "CardButton")
	b.set_meta("scene", id)
	b.focus_mode = Control.FOCUS_ALL if is_selectable(c) else Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP if is_selectable(c) else Control.MOUSE_FILTER_IGNORE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if is_selectable(c) else Control.CURSOR_ARROW
	card.add_child(b)
	var v := Kit.vbox(10)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_child(v)
	v.add_child(_photo(c))
	var txt := Kit.vbox(2)
	txt.custom_minimum_size.x = TEXT_W
	v.add_child(txt)
	if open_card:
		var kick := Kit.wrap_label(str(c.get("chapter", "")).to_upper().replace("ß", "SS"), "KickerLabel")
		Kit.scalable(kick, 20)
		txt.add_child(kick)
		var place := Kit.wrap_label(str(c.get("place", "")), "BodyLabel")
		place.add_theme_font_override("font", Kit.font("fv_serif_italic"))
		Kit.scalable(place, 30)
		txt.add_child(place)
		# date · who was there ............ finds of this place
		var info := Kit.hbox(12)
		txt.add_child(info)
		var parts: Array = []
		if str(c.get("date", "")) != "":
			parts.append(str(c["date"]))
		if str(c.get("who", "")) != "":
			parts.append(Kit.char_name(str(c["who"])))
		var date := Kit.wrap_label("  ·  ".join(parts), "DimLabel")
		date.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		Kit.scalable(date, 22)
		info.add_child(date)
		if int(c.get("total", 0)) > 0:
			var ic := Kit.ex_sprite("icons/icon_discovery.png")
			ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			info.add_child(ic)
			var cnt := Kit.label("%d / %d" % [int(c.get("found", 0)), int(c.get("total", 0))], "HintLabel")
			cnt.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			cnt.tooltip_text = Kit.t("ui.memories.finds")
			Kit.scalable(cnt, 20)
			info.add_child(cnt)
		if current:
			var here := Kit.label(Kit.t("ui.memories.current"), "HintLabel")
			here.add_theme_color_override("font_color", Kit.C_AMBER)
			Kit.scalable(here, 20)
			txt.add_child(here)
	else:
		var lk := Kit.label(Kit.t("ui.memories.locked").to_upper().replace("ß", "SS"), "KickerLabel")
		lk.add_theme_color_override("font_color", Kit.C_TEXT_DIM)
		Kit.scalable(lk, 21)
		txt.add_child(lk)
	for cc in m.find_children("*", "Control", true, false):
		(cc as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not open_card:
		m.modulate = Color(1, 1, 1, 0.62 if not Kit.high_contrast() else 0.85)
	elif current:
		m.modulate = Color(1, 1, 1, 0.7)
	if is_selectable(c):
		buttons[id] = b
		b.focus_entered.connect(_on_focus.bind(id))
		b.mouse_entered.connect(func(): if is_open and b.focus_mode != Control.FOCUS_NONE: b.grab_focus())
		b.pressed.connect(activate.bind(id))
	return card


## A film card: a dark plate with a strip of film perforation on the left, the title and a short line.
func _make_film(c: Dictionary) -> Control:
	var id := str(c.get("id", ""))
	var open_card := bool(c.get("unlocked", false))
	var card := Kit.margin(0, 0, 0, 0)
	card.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	var m := Kit.margin(15, 12, 15, 14)
	card.add_child(m)
	var b := Kit.button("", "CardButton")
	b.set_meta("film", id)
	b.focus_mode = Control.FOCUS_ALL if open_card else Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP if open_card else Control.MOUSE_FILTER_IGNORE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if open_card else Control.CURSOR_ARROW
	card.add_child(b)
	var plate := Kit.panel("PlatePanel")
	plate.custom_minimum_size = Vector2(TEXT_W, 132)
	m.add_child(plate)
	var h := Kit.hbox(22)
	plate.add_child(h)
	var strip := Control.new()
	strip.custom_minimum_size = Vector2(27, 108)
	var hc := Kit.high_contrast()
	strip.draw.connect(func() -> void:
		strip.draw_rect(Rect2(Vector2.ZERO, strip.size), Color("0d0b09") if not hc else Color.BLACK)
		var y := 6.0
		while y + 9.0 <= strip.size.y:
			strip.draw_rect(Rect2(9, y, 9, 9), Kit.C_PAPER_D if open_card else Kit.C_WALL)
			y += 18.0)
	h.add_child(strip)
	var v := Kit.vbox(4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(v)
	if open_card:
		var kick := Kit.wrap_label(Kit.t("ui.memories.film_kicker").to_upper().replace("ß", "SS"), "KickerLabel")
		Kit.scalable(kick, 20)
		v.add_child(kick)
		var t := Kit.wrap_label(str(c.get("title", "")), "BodyLabel")
		t.add_theme_font_override("font", Kit.font("fv_serif_italic"))
		Kit.scalable(t, 30)
		v.add_child(t)
		if str(c.get("sub", "")) != "":
			var s := Kit.wrap_label(str(c["sub"]), "DimLabel")
			Kit.scalable(s, 22)
			v.add_child(s)
	else:
		var lk := Kit.wrap_label(Kit.t("ui.memories.locked_film").to_upper().replace("ß", "SS"), "KickerLabel")
		lk.add_theme_color_override("font_color", Kit.C_TEXT_DIM)
		Kit.scalable(lk, 20)
		v.add_child(lk)
	for cc in m.find_children("*", "Control", true, false):
		(cc as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not open_card:
		m.modulate = Color(1, 1, 1, 0.55 if not hc else 0.85)
	else:
		buttons[id] = b
		b.focus_entered.connect(_on_focus.bind(id))
		b.mouse_entered.connect(func(): if is_open and b.focus_mode != Control.FOCUS_NONE: b.grab_focus())
		b.pressed.connect(activate.bind(id))
	return card


## The print in its mount (unexposed paper for locked cards — no image, nothing to read).
func _photo(c: Dictionary) -> Control:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mount_sz := PHOTO + MOUNT_PAD
	holder.custom_minimum_size = mount_sz + Vector2(0, 18)
	var mount := PanelContainer.new()
	mount.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mount.add_theme_stylebox_override("panel", Kit.ex_style("frames/photo_mount.png", [21, 21, 21, 24], [21, 21, 21, 24], true, true))
	mount.position = Vector2(0, 18)
	mount.size = mount_sz
	holder.add_child(mount)
	var tex: Texture2D = Kit.optional_tex(str(c.get("thumb", ""))) if bool(c.get("unlocked", false)) and str(c.get("thumb", "")) != "" else null
	if tex != null:
		var img := Kit.pixel_image(tex, 1)
		img.custom_minimum_size = PHOTO
		img.stretch_mode = TextureRect.STRETCH_SCALE
		mount.add_child(img)
	else:
		var blank := ColorRect.new()
		blank.color = C_UNEXPOSED_HC if Kit.high_contrast() else C_UNEXPOSED
		blank.custom_minimum_size = PHOTO
		blank.mouse_filter = Control.MOUSE_FILTER_IGNORE
		mount.add_child(blank)
		if not bool(c.get("unlocked", false)):   # an unexposed print: only the small diamond of the UI kit
			var orn := Kit.sprite("icons/ornament_diamond.png")
			Kit.full_rect(orn)
			orn.modulate = Color(1, 1, 1, 0.35)
			blank.add_child(orn)
	if bool(c.get("unlocked", false)):
		var tl := Kit.ex_sprite("icons/tape_l.png")
		tl.position = Vector2(-24, 0)
		tl.size = Vector2(66, 36)
		holder.add_child(tl)
		var tr := Kit.ex_sprite("icons/tape_r.png")
		tr.position = Vector2(mount_sz.x - 42, 0)
		tr.size = Vector2(66, 36)
		holder.add_child(tr)
	return holder


func _on_focus(id: String) -> void:
	_selected = id
	Kit.ui_sound("move")


## Selects a card by scene id (keyboard focus); false when it cannot be chosen.
func select(id: String) -> bool:
	if not buttons.has(id):
		return false
	(buttons[id] as Button).grab_focus()
	_selected = id
	return true


func selected() -> String:
	return _selected


## Page "scenes": starts the trip into `id` (unlocked, not the current scene). Page "films": plays the seen film
## `id` again. Returns false when that is not possible.
func activate(id: String) -> bool:
	var from_menu := context == "menu"
	if page == "films":
		var f := _film(id)
		if f.is_empty() or not bool(f.get("unlocked", false)):
			Kit.ui_sound("back")
			return false
		Kit.ui_sound("confirm")
		if not get_signal_connection_list("film_requested").is_empty():
			film_requested.emit(id, from_menu)
			return true
		var gf := Kit.svc("Game")
		if gf != null and gf.has_method("rewatch_film"):
			if gf.has_method("can_travel") and not bool(gf.can_travel(from_menu)):
				return false
			gf.rewatch_film(id, from_menu)
			return true
		return false
	var c := _card(id)
	if c.is_empty() or not is_selectable(c):
		Kit.ui_sound("back")
		return false
	Kit.ui_sound("confirm")
	if not get_signal_connection_list("travel_requested").is_empty():
		travel_requested.emit(id, from_menu)
		return true
	var g := Kit.svc("Game")
	if g != null and g.has_method("travel_to_memory"):
		if g.has_method("can_travel") and not bool(g.can_travel(from_menu)):
			return false
		g.travel_to_memory(id, from_menu)   # closes every panel itself and runs the transition
		return true
	return false


func _film(id: String) -> Dictionary:
	for f in films:
		if str(f.get("id", "")) == id:
			return f
	return {}


## Q / E (PageUp / PageDown, LB / RB) switch between „Orte“ and „Filmsequenzen“.
func modal_input(event: InputEvent) -> bool:
	if event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).physical_keycode
		if k == KEY_Q or k == KEY_PAGEUP:
			cycle_page(-1)
			return true
		if k == KEY_E or k == KEY_PAGEDOWN:
			cycle_page(1)
			return true
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER:
			cycle_page(-1)
			return true
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER:
			cycle_page(1)
			return true
	return false


func focus_default() -> void:
	if _selected != "" and buttons.has(_selected):
		(buttons[_selected] as Button).grab_focus()
		return
	var list: Array = cards if page == "scenes" else films
	for c in list:
		var id := str(c.get("id", ""))
		if buttons.has(id):
			(buttons[id] as Button).grab_focus()
			_selected = id
			return


func _on_contrast_changed() -> void:
	if is_open:
		refresh()


func _modal_uncovered() -> void:
	_build_footer()
	super._modal_uncovered()
