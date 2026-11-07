extends "res://scripts/ui/ui_modal.gd"
## Demo notice (round 11, TECHNICAL_ARCHITECTURE §12.13): a letter from the studio on the game's paper — early demo
## (Chapters 1–4, about an hour of story), graphics / music / texts are still being improved, the story will grow by
## many chapters, thanks, feedback welcome, warm greetings + studio name (texts: data/locale/de_splash.json).
## One button „Los geht's“ (Enter / Space / E / pad A / click); Esc / B close it as well.
## Opened by the main menu on its first opening of a real player's launch (BootFlow.notice_due(): never in automated
## runs) — the letter then arrives after the menu has faded in and swallows presses for a moment, so keys mashed through
## the boot sequence cannot close it unread — and any time from „Mitwirkende“ → „Demo-Hinweis“ (UIRoot.open_demo_notice).
## Closing sets the settings flag `demo_notice_seen` (Settings → user://settings.cfg, never a save).
## Text 100 / 125 / 150 %: the sheet widens with the text and stays inside the 1920x1080 frame.

const BootFlow := preload("res://scripts/ui/boot_flow.gd")
const W_BASE := 1060.0
const FIRST_DELAY := 0.9            # s: first opening — the menu fades in, then the letter arrives
const INPUT_GUARD := 0.6            # s after the letter is there before a press counts (first opening)
const REOPEN_GUARD := 0.2           # s: from the credits
const GAP := 12                     # px between the rows of the letter

var first_run := false
var _dim: ColorRect
var _paper: PanelContainer
var _kicker: Label
var _heading: Label
var _body: Label
var _sign: Label
var _ok: Button
var _guard_until := 0
var _tween: Tween
var _slide := 0.0                   # px: the arrival slide of the sheet
var _place_queued := false


func _ready() -> void:
	pauses_game = false
	closes_on_cancel = true
	_dim = Kit.dimmer(0.66)
	add_child(_dim)
	# the sheet is placed by hand (_place): a full-rect CenterContainer would keep the height the wrapping labels
	# report before they have a width (thousands of px) and centre the letter far below the screen
	_paper = Kit.panel("PaperPanel")
	_paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_paper)
	_paper.minimum_size_changed.connect(_queue_place)
	var v := Kit.vbox(GAP)
	_paper.add_child(v)
	var head := Kit.hbox(12)
	v.add_child(head)
	_kicker = Kit.label("", "PaperKicker")
	_kicker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_kicker.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_kicker)
	var slot := Control.new()                # the stamp hangs over the heading's free right end (no extra row)
	slot.custom_minimum_size = Vector2(252, 30)
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var stamp := _make_stamp(Kit.t("ui.demo.stamp").to_upper().replace("ß", "SS"))
	stamp.position = Vector2(0, -4)
	slot.add_child(stamp)
	head.add_child(slot)
	_heading = Kit.wrap_label(Kit.t("ui.demo.title"), "TypeHeading")
	Kit.scalable(_heading, 38)
	v.add_child(_heading)
	var sep := HSeparator.new()
	sep.theme_type_variation = "PaperSeparator"
	v.add_child(sep)
	_body = Kit.wrap_label(Kit.t("ui.demo.body"), "TypeLabel")
	Kit.scalable(_body, 27)
	v.add_child(_body)
	var foot := Kit.hbox(24)                 # last line of the letter: the button left, the signature right
	v.add_child(foot)
	_ok = Kit.button(Kit.t("ui.demo.ok"), "", 320)
	_ok.size_flags_vertical = Control.SIZE_SHRINK_END
	_ok.pressed.connect(_confirm)
	foot.add_child(_ok)
	_sign = Kit.wrap_label("", "TypeLabel")
	_sign.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_sign.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_sign.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	Kit.scalable(_sign, 31)
	foot.add_child(_sign)


## Red rubber stamp on the letter (same frame as the inspect card's stamp).
func _make_stamp(text: String) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(252, 78)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Kit.sprite("icons/stamp_evidence.png")
	frame.size = Vector2(252, 78)
	c.add_child(frame)
	var l := Kit.label(text, "StampLabel", 27)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size = Vector2(252, 78)
	l.pivot_offset = Vector2(126, 39)
	l.rotation = deg_to_rad(-3.0)
	l.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	l.modulate = Color(1, 1, 1, 0.92)
	c.add_child(l)
	return c


## first: the main menu's first opening (delayed arrival + input guard); false: from the credits.
func open(first := false) -> void:
	first_run = first
	open_modal()


func _on_open() -> void:
	var version := str(ProjectSettings.get_setting("application/config/version", "0.1.0"))
	_kicker.text = Kit.t("ui.demo.kicker", {"version": version}).to_upper().replace("ß", "SS")
	_sign.text = Kit.t("ui.demo.signoff", {"studio": Kit.t("splash.studio")})
	_paper.custom_minimum_size.x = sheet_width(Kit.text_scale())
	if _tween != null and _tween.is_valid():
		_tween.kill()
	var delay := FIRST_DELAY if first_run else 0.0
	_guard_until = Time.get_ticks_msec() + int((delay + (INPUT_GUARD if first_run else REOPEN_GUARD)) * 1000.0)
	_slide = 0.0
	if first_run:
		_dim.modulate.a = 0.0
		_paper.modulate.a = 0.0
		_tween = create_tween().set_parallel(true)
		_tween.tween_property(_dim, "modulate:a", 1.0, 0.6).set_delay(maxf(0.0, delay - 0.25))
		_tween.tween_property(_paper, "modulate:a", 1.0, 0.5).set_delay(delay)
		if not Kit.reduced_motion():
			_slide = 36.0
			_tween.tween_method(_set_slide, 36.0, 0.0, 0.65).set_delay(delay) \
				.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		_tween.tween_callback(Kit.ui_sound.bind("page")).set_delay(delay)
	else:
		_dim.modulate.a = 1.0
		_paper.modulate.a = 1.0
		Kit.ui_sound("page")
	_place()
	_queue_place()


## Centres the sheet in the frame at its current minimum size (+ the arrival slide).
func _place() -> void:
	_place_queued = false
	var frame := size if size.x > 0.0 and size.y > 0.0 else Vector2(1920, 1080)
	var ms := _paper.get_combined_minimum_size()
	_paper.size = ms
	_paper.position = ((frame - ms) / 2.0).round() + Vector2(0.0, roundf(_slide))


func _queue_place() -> void:
	if not _place_queued:
		_place_queued = true
		_place.call_deferred()


func _set_slide(v: float) -> void:
	_slide = v
	_place()


## Sheet width for a text scale: 1060 px at 100 %, wider with larger text so the letter never grows past the frame.
static func sheet_width(ts: float) -> float:
	return roundf(W_BASE * (1.0 + (clampf(ts, 1.0, 1.5) - 1.0) * 1.25))


func guarded() -> bool:
	return Time.get_ticks_msec() < _guard_until


func modal_input(event: InputEvent) -> bool:
	if guarded() and (event is InputEventKey or event is InputEventJoypadButton or event is InputEventMouseButton):
		return true                       # the letter is still arriving: swallow the press
	return false


func handle_cancel() -> bool:
	if not guarded():
		Kit.ui_sound("back")
		close()
	return true


func focus_default() -> void:
	_ok.grab_focus()


func _confirm() -> void:
	if guarded():
		return
	Kit.ui_sound("confirm")
	close()


func _on_close() -> void:
	first_run = false
	BootFlow.mark_notice_seen()
