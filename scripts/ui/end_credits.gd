extends "res://scripts/ui/ui_modal.gd"
## EndCredits (scenes/ui/EndCredits.tscn; UIRoot instances it as `end_credits`, UIRoot.play_end_credits()
## awaits play()). A calm roll after the demo end card: title, the alternative-history note, the production
## credits of the "Mitwirkende" panel (credits.gd) and "Quellen der historischen Karten" — every real-history
## card from the Explore autoload (cards_list() for the order, card() for the details) with its Loc title and
## year, then each source label and URL, set like an archive index.
##
## * Drawn on an own CanvasLayer (LAYER 95) above Game's fade layer (90): start it while the screen is black.
##   It fades in from black by itself, ends on black and then hides, so whatever is below shows again (black
##   in Game._finale_flow) — nothing pops.
## * Timeline: fade-in FADE_IN, title hold until HOLD_TITLE, roll (speed = travel / ROLL_TIME, so the roll
##   lasts ≈ 84 s at every text scale), end hold HOLD_END, fade-out FADE_OUT. Esc / pad B or Y (skip, cancel,
##   ui_cancel) ends it with a short fade; Space / Enter / pad A (advance, ui_accept, interact) held = FAST×.
##   Reduced motion: page by page with a short cross-fade instead of a moving roll.
## * `finished` is emitted exactly once per start(); skip() is idempotent; closing the modal from outside
##   (UIRoot.close_all) finishes it too. step(delta) drives the timeline (tests and harnesses call it).
## * Text scale (Kit.scalable) and high contrast (theme_hc + brighter colours, rebuilt on change) respected.

signal finished

const SnowField := preload("res://scripts/ui/snow_field.gd")

const LAYER := 95
const ROLL_TIME := 74.0
const FAST := 6.0
const FADE_IN := 1.6
const HOLD_TITLE := 4.5
const HOLD_END := 4.0
const FADE_OUT := 1.4
const FADE_SKIP := 0.45
const PAGE_FADE := 0.6
const COL_W := 1180.0
const EDGE := 150.0
const MUSIC := "mus_menu"
const ORNAMENT := "icons/ornament_diamond.png"
## Production credits shared with the "Mitwirkende" panel (the alternative-history note is shown first).
const PROD_SECTIONS := [["ui.credits.h_project", "ui.credits.project"], ["ui.credits.h_tools", "ui.credits.tools"],
	["ui.credits.h_generators", "ui.credits.generators"], ["ui.credits.h_fonts", "ui.credits.fonts"],
	["ui.credits.h_assets", "ui.credits.assets"], ["ui.credits.h_ai", "ui.credits.ai"]]
const SKIP_ACTIONS := ["skip", "cancel", "ui_cancel"]
const FAST_ACTIONS := ["advance", "ui_accept", "interact"]

enum Phase { IDLE, INTRO, ROLL, OUTRO, FADE, DONE }

var phase: int = Phase.IDLE
## Scroll position of the reel in px (0 = the title page fills the screen, travel() = the end page does).
var offset := 0.0
## Roll speed in px/s at normal speed (set when the roll starts).
var speed := 0.0
## Seconds since start().
var elapsed := 0.0
## How often `finished` was emitted (tests).
var finish_count := 0
## Plays MUSIC through Audio on start (tests switch it off).
var music := true

var _t := 0.0
var _fast := false
var _alpha_from := 1.0
var _fade_len := FADE_OUT
var _page_t := 0.0
var _jump := -1.0
var _jumped := false
var _hint_bump := 0.0
var _layer: CanvasLayer
var _root: Control
var _content: Control
var _bg: ColorRect
var _snow: Control
var _clip: Control
var _edges: Array = []
var _reel: VBoxContainer
var _hints: Control
## First card block of the source list (harness: "a source page").
var sources_anchor: Control


func _ready() -> void:
	pauses_game = false
	closes_on_cancel = false
	_layer = CanvasLayer.new()
	_layer.layer = LAYER
	_layer.visible = false
	add_child(_layer)
	_root = _plain(Control.new())
	_root.name = "Screen"
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_layer.add_child(_root)
	var black := ColorRect.new()
	black.color = Color.BLACK
	_root.add_child(_plain(black))
	_content = _plain(Control.new())
	_root.add_child(_content)
	_bg = ColorRect.new()
	_content.add_child(_plain(_bg))
	_snow = _plain(SnowField.new())
	_content.add_child(_snow)
	_clip = _plain(Control.new())
	_clip.clip_contents = true
	_content.add_child(_clip)
	_content.add_child(_edge(true))
	_content.add_child(_edge(false))
	_apply_look()


# ================================================================ public API
## Starts the roll (no-op while it runs). Use play() to wait for the end.
func start() -> void:
	if is_playing() or _layer == null:
		return
	_build_reel()
	phase = Phase.INTRO
	_t = 0.0
	elapsed = 0.0
	offset = 0.0
	speed = 0.0
	_fast = false
	_page_t = 0.0
	_jump = -1.0
	_hint_bump = 0.0
	_content.modulate.a = 0.0
	_clip.modulate.a = 1.0
	_refresh_hints()
	_apply_offset()
	_layer.visible = true
	open_modal()
	if music:
		Kit.call_svc("Audio", "play_music", [MUSIC, 2.5])


## Starts the roll and returns when it ended or was skipped (also when it was already running).
func play() -> void:
	start()
	if is_playing():
		await finished


## Esc: ends the roll with a short fade. Idempotent (no-op while fading out or when not playing).
func skip() -> void:
	if not is_playing() or phase == Phase.FADE:
		return
	_begin_fade(FADE_SKIP)


func is_playing() -> bool:
	return phase != Phase.IDLE and phase != Phase.DONE


## Scroll distance from the title page to the end page.
func travel() -> float:
	if _reel == null:
		return 0.0
	return maxf(_reel.get_combined_minimum_size().y - _vh(), 0.0)


## Advances the timeline by `delta` seconds (called from _process; tests and harnesses call it directly).
func step(delta: float) -> void:
	if not is_playing():
		return
	elapsed += delta
	_t += delta
	match phase:
		Phase.INTRO:
			_content.modulate.a = clampf(_t / FADE_IN, 0.0, 1.0)
			if _t >= HOLD_TITLE or (_fast and _t >= FADE_IN):
				phase = Phase.ROLL
				_t = 0.0
				speed = maxf(travel(), 1.0) / ROLL_TIME
		Phase.ROLL:
			_roll(delta * (FAST if _fast else 1.0))
			if offset >= travel() and _jump < 0.0:
				offset = travel()
				phase = Phase.OUTRO
				_t = 0.0
		Phase.OUTRO:
			if _t >= HOLD_END or (_fast and _t >= 1.0):
				_begin_fade(FADE_OUT)
		Phase.FADE:
			_content.modulate.a = lerpf(_alpha_from, 0.0, clampf(_t / _fade_len, 0.0, 1.0))
			if _t >= _fade_len:
				_finish()
				return
	if _jump < 0.0:
		_clip.modulate.a = move_toward(_clip.modulate.a, 1.0, delta * 4.0)
	_apply_offset()
	_update_hints(delta)


## Every text on the reel, in order (tests / harness).
func reel_texts() -> Array:
	var out: Array = []
	if _reel != null:
		collect_texts(_reel, out)
	return out


static func collect_texts(n: Node, out: Array) -> void:
	if n is Label:
		out.append((n as Label).text)
	for c in n.get_children():
		collect_texts(c, out)


# ================================================================ modal hooks
func modal_input(event: InputEvent) -> bool:
	if not is_playing():
		return false
	if _is_action(event, SKIP_ACTIONS, true):
		skip()
		return true
	if _is_action(event, FAST_ACTIONS, true):
		_fast = true
		_hint_bump = 3.0
		return true
	if _is_action(event, FAST_ACTIONS, false):
		_fast = false
		return true
	# The roll owns the screen: nothing reaches the GUI or the world below while it runs (any other press
	# shows the key hints again for a moment).
	var consumed := event is InputEventKey or event is InputEventJoypadButton or event is InputEventMouseButton
	if consumed and event.is_pressed():
		_hint_bump = 3.0
	return consumed


func handle_cancel() -> bool:
	skip()
	return true


func _on_close() -> void:
	if is_playing():
		_finish()


func _on_contrast_changed() -> void:
	_apply_look()
	if is_playing():
		var o := offset
		_build_reel()
		offset = o
		_apply_offset()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		_fast = false


func _process(delta: float) -> void:
	if is_playing():
		step(delta)


# ================================================================ timeline internals
func _begin_fade(length: float) -> void:
	phase = Phase.FADE
	_t = 0.0
	_fade_len = length
	_alpha_from = _content.modulate.a


func _finish() -> void:
	if not is_playing():
		return
	phase = Phase.DONE
	_fast = false
	_layer.visible = false
	if _reel != null:
		_clip.remove_child(_reel)
		_reel.queue_free()
		_reel = null
		sources_anchor = null
	if is_open:
		close()
	finish_count += 1
	finished.emit()


func _roll(d: float) -> void:
	var end := travel()
	if not Kit.reduced_motion():
		offset = minf(offset + speed * d, end)
		return
	# Reduced motion: whole pages with a short cross-fade, same overall length as the roll.
	var page := floorf(_vh() * 0.8)
	var pages := maxf(ceilf(end / page), 1.0)
	if _jump >= 0.0:
		_jump += d
		var half := PAGE_FADE * 0.5
		_clip.modulate.a = clampf(absf(_jump - half) / half, 0.0, 1.0)
		if _jump >= half and not _jumped:
			_jumped = true
			offset = minf(offset + page, end)
		if _jump >= PAGE_FADE:
			_jump = -1.0
			_clip.modulate.a = 1.0
		return
	_page_t += d
	if offset < end and _page_t >= maxf(ROLL_TIME / pages - PAGE_FADE, 2.5):
		_page_t = 0.0
		_jump = 0.0
		_jumped = false


func _apply_offset() -> void:
	if _reel == null:
		return
	var w := _clip.size.x if _clip.size.x > 1.0 else 1920.0
	_reel.position = Vector2(roundf((w - COL_W) * 0.5), -roundf(offset))


func _vh() -> float:
	return _root.size.y if _root != null and _root.size.y > 1.0 else 1080.0


func _update_hints(delta: float) -> void:
	if _hints == null:
		return
	_hint_bump = maxf(_hint_bump - delta, 0.0)
	var target := 0.0
	if phase == Phase.INTRO:
		target = 0.8 if _t > FADE_IN else 0.0
	elif phase == Phase.ROLL or phase == Phase.OUTRO:
		target = 0.8 if (elapsed < 16.0 or _hint_bump > 0.0) else 0.0
	_hints.modulate.a = move_toward(_hints.modulate.a, target, delta * 1.2)


static func _is_action(event: InputEvent, actions: Array, pressed: bool) -> bool:
	for a in actions:
		if not InputMap.has_action(a):
			continue
		if (event.is_action_pressed(a) if pressed else event.is_action_released(a)):
			return true
	return false


# ================================================================ look
func _apply_look() -> void:
	var hc := Kit.high_contrast()
	var th := Kit.theme(hc)
	if th != null:
		_root.theme = th
	var bg := Color.BLACK if hc else Kit.C_NIGHT
	_bg.color = bg
	_snow.modulate.a = 0.2 if hc else 0.35
	for e in _edges:
		var g: Gradient = ((e as TextureRect).texture as GradientTexture2D).gradient
		g.set_color(0, Color(bg, 1.0))
		g.set_color(1, Color(bg, 0.0))


func _edge(top: bool) -> TextureRect:
	var gt := GradientTexture2D.new()
	gt.gradient = Gradient.new()
	gt.width = 4
	gt.height = 64
	gt.fill_from = Vector2(0.0, 0.0 if top else 1.0)
	gt.fill_to = Vector2(0.0, 1.0 if top else 0.0)
	var r := TextureRect.new()
	r.texture = gt
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.anchor_right = 1.0
	if top:
		r.offset_bottom = EDGE
	else:
		r.anchor_top = 1.0
		r.anchor_bottom = 1.0
		r.offset_top = -EDGE
	_edges.append(r)
	return r


func _refresh_hints() -> void:
	if _hints != null:
		_content.remove_child(_hints)
		_hints.queue_free()
	var pairs := [[Kit.action_key_text("skip"), Kit.t("credits.end.skip")],
		[Kit.action_key_text("advance"), Kit.t("credits.end.faster")]]
	_hints = Kit.controls_row(pairs, BoxContainer.ALIGNMENT_END)
	_hints.anchor_left = 1.0
	_hints.anchor_top = 1.0
	_hints.anchor_right = 1.0
	_hints.anchor_bottom = 1.0
	_hints.offset_left = -56.0
	_hints.offset_top = -48.0
	_hints.offset_right = -56.0
	_hints.offset_bottom = -48.0
	_hints.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_hints.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hints.modulate.a = 0.0
	_content.add_child(_hints)


func _build_reel() -> void:
	if _reel != null:
		_clip.remove_child(_reel)
		_reel.queue_free()
	var hc := Kit.high_contrast()
	var col := colors(hc)
	var vh := _vh()
	_reel = Kit.vbox(0)
	_reel.name = "Reel"
	_reel.custom_minimum_size.x = COL_W
	_reel.size = Vector2(COL_W, 0.0)
	_reel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_clip.add_child(_reel)
	_reel.add_child(_title_page(vh, col))
	_reel.add_child(_section(Kit.t("ui.credits.h_disclaimer"), Kit.t("ui.credits.disclaimer"), col, true))
	_reel.add_child(_gap(160))
	_reel.add_child(_heading(Kit.t("ui.credits.title"), col))
	var version := str(ProjectSettings.get_setting("application/config/version", "0.1.0"))
	for s in PROD_SECTIONS:
		_reel.add_child(_gap(72))
		_reel.add_child(_section(Kit.t(s[0]), Kit.t(s[1], {"version": version}), col, false))
	_reel.add_child(_gap(180))
	_reel.add_child(_heading(Kit.t("credits.end.h_sources"), col))
	_reel.add_child(_gap(26))
	_reel.add_child(_prose(Kit.t("credits.end.sources_intro"), col, false))
	var list := Kit.vbox(0)
	add_source_list(list, hc)
	sources_anchor = list.get_child(1) if list.get_child_count() > 1 else list
	_reel.add_child(list)
	_reel.add_child(_gap(130))
	_reel.add_child(_prose(Kit.t("credits.end.menu_hint"), col, true))
	_reel.add_child(_end_page(vh, col))


func _title_page(vh: float, col: Dictionary) -> Control:
	var page := CenterContainer.new()
	page.custom_minimum_size.y = vh
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var v := Kit.vbox(12)
	page.add_child(v)
	var kick := Kit.label(Kit.t("ui.menu.kicker").to_upper(), "KickerLabel", 24)
	kick.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(kick, 24)
	v.add_child(kick)
	var title := Kit.label(Kit.t("ui.menu.title"), "TitleLabel")
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(title)
	var row := Kit.hbox(18)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(_line(col, 84, 3))
	row.add_child(Kit.label(Kit.t("ui.menu.subtitle"), "SubtitleLabel"))
	row.add_child(_line(col, 84, 3))
	v.add_child(row)
	return page


func _end_page(vh: float, col: Dictionary) -> Control:
	var page := CenterContainer.new()
	page.custom_minimum_size.y = vh
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var v := Kit.vbox(24)
	page.add_child(v)
	var l := Kit.label(Kit.t("ui.credits.thanks"), "BodyLabel", 0, col["bright"])
	l.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(l, 40)
	v.add_child(l)
	var row := Kit.hbox(14)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(_line(col, 60, 2))
	row.add_child(_orn())
	row.add_child(_line(col, 60, 2))
	v.add_child(row)
	return page


func _heading(text: String, col: Dictionary) -> Control:
	var v := Kit.vbox(14)
	var l := Kit.label(text.to_upper(), "HeadingLabel", 0, col["bright"])
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(l, 40)
	v.add_child(l)
	var row := Kit.hbox(14)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(_line(col, 60, 2))
	row.add_child(_orn())
	row.add_child(_line(col, 60, 2))
	v.add_child(row)
	return v


func _section(head: String, body: String, col: Dictionary, italic: bool) -> Control:
	var v := Kit.vbox(16)
	var row := Kit.hbox(16)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(_orn())
	var h := Kit.label(head.to_upper(), "KickerLabel", 24)
	Kit.scalable(h, 24)
	row.add_child(h)
	row.add_child(_orn())
	v.add_child(row)
	v.add_child(_prose(body, col, italic))
	return v


func _prose(text: String, col: Dictionary, italic: bool) -> Control:
	var m := Kit.margin(110, 0, 110, 0)
	var l := Kit.wrap_label(text, "BodyLabel", 0, col["text"])
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if italic:
		l.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	Kit.scalable(l, 29)
	m.add_child(l)
	return m


static func _gap(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size.y = h
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


static func _orn() -> TextureRect:
	var o := Kit.sprite(ORNAMENT)
	o.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return o


static func _line(col: Dictionary, w: int, thick: int) -> ColorRect:
	var r := Kit.rule(col["accent"], thick, w)
	r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return r


static func _plain(c: Control) -> Control:
	Kit.full_rect(c)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


# ================================================================ source list (shared with credits.gd)
## Colours of the reel and the source list (high contrast: brighter text, amber accents).
static func colors(hc: bool) -> Dictionary:
	return {"text": Kit.C_TEXT_BRIGHT if hc else Kit.C_TEXT, "dim": Kit.C_TEXT if hc else Kit.C_TEXT_DIM,
		"accent": Kit.C_AMBER if hc else Kit.C_COPPER_L, "line": Kit.C_COPPER_L if hc else Kit.C_COPPER_D,
		"bright": Kit.C_TEXT_BRIGHT}


## Adds the sources of every real-history card to `parent`: a heading per side, then per card its Loc title
## and year and each source (label, URL) — order of Explore.cards_list(), details via Explore.card().
## Shared by the end credits and the main-menu "Mitwirkende" panel. Returns the number of sources added.
static func add_source_list(parent: Control, hc := false) -> int:
	var ex := Kit.svc("Explore")
	if ex == null or not ex.has_method("cards_list"):
		return 0
	var col := colors(hc)
	var n := 0
	var side := ""
	for c in ex.cards_list():
		var cd: Dictionary = ex.card(str(c.get("id", ""))) if ex.has_method("card") else {}
		if cd.is_empty():
			cd = c
		var s := str(cd.get("side", ""))
		if s != side:
			side = s
			parent.add_child(_side_heading(s, col))
		parent.add_child(_card_block(cd, col))
		var srcs = cd.get("sources", [])
		n += (srcs as Array).size() if srcs is Array else 0
	return n


static func _side_heading(side: String, col: Dictionary) -> Control:
	var m := Kit.margin(0, 64, 0, 8)
	var row := Kit.hbox(18)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	m.add_child(row)
	var key := "credits.end.side." + side
	var l := Kit.label((Kit.t(key) if Kit.has_key(key) else side).to_upper(), "KickerLabel", 24, col["accent"])
	Kit.scalable(l, 24)
	row.add_child(_line(col, 90, 2))
	row.add_child(l)
	row.add_child(_line(col, 90, 2))
	return m


static func _card_block(c: Dictionary, col: Dictionary) -> Control:
	var m := Kit.margin(0, 30, 0, 6)
	var v := Kit.vbox(12)
	m.add_child(v)
	v.add_child(Kit.rule(col["line"], 2, 0))
	var head := Kit.hbox(24)
	v.add_child(head)
	var title := Kit.wrap_label(Kit.t(str(c.get("title_key", ""))), "", 0, col["bright"])
	title.add_theme_font_override("font", Kit.font("fv_serif_bold"))
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	Kit.scalable(title, 30)
	head.add_child(title)
	var year := Kit.label(str(c.get("year", "")), "", 0, col["accent"])
	year.add_theme_font_override("font", Kit.font("fv_mono"))
	year.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	Kit.scalable(year, 22)
	head.add_child(year)
	var srcs = c.get("sources", [])
	if srcs is Array:
		var i := 0
		for s in srcs:
			if s is Dictionary:
				i += 1
				v.add_child(_source_row(i, s, col))
	return m


static func _source_row(i: int, s: Dictionary, col: Dictionary) -> Control:
	var row := Kit.hbox(18)
	var num := Kit.label("%02d" % i, "", 0, col["accent"])
	num.add_theme_font_override("font", Kit.font("fv_mono"))
	Kit.scalable(num, 20)
	var nm := Kit.margin(0, 4, 0, 0)
	nm.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	nm.add_child(num)
	row.add_child(nm)
	var v := Kit.vbox(2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(v)
	var lab := Kit.wrap_label(str(s.get("label", "")), "BodyLabel", 0, col["text"])
	Kit.scalable(lab, 24)
	v.add_child(lab)
	var url := str(s.get("url", ""))
	var ul := Kit.wrap_label(url if url != "" else Kit.t("credits.end.no_url"), "", 0, col["dim"])
	ul.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
	ul.add_theme_font_override("font", Kit.font("fv_mono"))
	Kit.scalable(ul, 18)
	v.add_child(ul)
	return row
