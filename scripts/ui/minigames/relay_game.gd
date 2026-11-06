extends "res://scripts/ui/minigames/minigame_base.gd"
## Palais "Das Relaispult" (scenes/ui/minigames/RelayDesk.tscn, explore entry veltrava.hall.relay, §12.8).
## The commission's sound technician has to go down to the Saal for a few minutes; Konrad keeps the
## interpretation desk: four delegation channels (rows DE/RU/FR/EN) are plugged into the floor original or one of
## three booths (Kabine 1 · FR, Kabine 2 · RU↔DE, Kabine 3 · EN). When the floor language changes, the channels have
## to follow; when an interpreter falls behind, the yellow lamp asks the speaker to slow down, the red one stops him
## for a moment. Three rounds with rising tempo, then the chair adjourns and the interpreter of Kabine 1 has a word.
## Logic: relay_logic.gd (deterministic). Art: assets/ui/minigames/relay/ (tools/pixelgen/gen_mg_relay.py, 1:1, drawn
## x3); sounds: assets/audio/sfx/mg_relay_* (tools/audiogen/mg_audio_relay.py).
## Keys: Up/Down (W/S, d-pad, stick) choose the channel · Left/Right (A/D) move its plug · 1–4 plug straight into
## Saal/K1/K2/K3 · G (pad X) yellow lamp · R (pad Y) red lamp · Space/Enter/E (pad A) start/continue · Esc gives up.
## Mouse: click a socket to plug, a tag to select the channel, a lamp to press it, the display to continue.
## Accessibility: every state is told by text and shape as well as colour (check/cross/silence icons, hatched meter
## zones, labelled lamps); text follows the text-scale setting (boxes shrink a too long line instead of overflowing);
## high contrast brightens the needles, the selection and the guides; reduced motion stops every blink.

const Logic := preload("res://scripts/ui/minigames/relay_logic.gd")
const S := 3
const ART := "res://assets/ui/minigames/relay/"
const SND := "res://assets/audio/sfx/"
const DIGITS := [KEY_1, KEY_2, KEY_3, KEY_4]
const KP_DIGITS := [KEY_KP_1, KEY_KP_2, KEY_KP_3, KEY_KP_4]
const INK := Color("1a1c2a")
const INK_DIM := Color("4d4a42")
const C_BAD := Color("ec6a4e")
const C_YEL := Color("f0cd5c")

var logic = Logic.new()
var layout: Dictionary = {}
var _tex: Dictionary = {}
var _desk: Control
var _beat: Control
var _beat_lines: Array = []
var _beat_portrait: Control
var _lab: Dictionary = {}          # name -> Label
var _fit: Array = []               # [label, box width px, min font size]
var _guides := false               # hint: the matching sockets glow
var _hint_kind := "plug"
var _anim := 0.0
var _fit_t := 0.0
var _press_flash := [0.0, 0.0]     # yellow, red: short flash after a press
var _ignored_flash := [0.0, 0.0]
var _lost_fail_turn := ""
var _last_target := ""
var _plug_flash: Array = [0.0, 0.0, 0.0, 0.0]
var _p_hall: AudioStreamPlayer
var _p_voice: Dictionary = {}       # lang -> AudioStreamPlayer
var _hc := false
var _rm := false


class View extends Control:
	var game: Node
	var kind := ""

	func _draw() -> void:
		game.call("draw_" + kind, self)

	func _gui_input(event: InputEvent) -> void:
		game.call(kind + "_input", event)


# ================================================================ build
func _build_play(area: Control) -> void:
	set_texts("mg.relay.kicker", "mg.relay.title", "mg.relay.subtitle", "mg.relay.instruction")
	var lj = Kit.json(ART + "relay_layout.json")
	layout = lj if lj is Dictionary else {}
	for k in ["relay_desk", "relay_pins", "relay_lamps", "relay_icons", "relay_booths", "relay_interpreter"]:
		_tex[k] = Kit.optional_tex(ART + k + ".png")
	_hc = Kit.high_contrast()
	_rm = Kit.reduced_motion()
	var center := CenterContainer.new()
	center.mouse_filter = Control.MOUSE_FILTER_PASS
	Kit.full_rect(center)
	area.add_child(center)
	var sz: Array = layout.get("size", [568, 140])
	_desk = View.new()
	_desk.game = self
	_desk.kind = "desk"
	_desk.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_desk.mouse_filter = Control.MOUSE_FILTER_STOP
	_desk.custom_minimum_size = Vector2(float(sz[0]), float(sz[1])) * S
	center.add_child(_desk)
	_build_labels()
	_build_beat()
	_p_hall = _loop_player(SND + "mg_relay_hall.wav")
	for l in ["de", "ru", "fr"]:
		_p_voice[l] = _loop_player(SND + "mg_relay_voice_%s.wav" % l)


func _r(rect) -> Rect2:
	var a: Array = rect if rect is Array else [0, 0, 1, 1]
	return Rect2(Vector2(float(a[0]), float(a[1])) * S, Vector2(float(a[2]), float(a[3])) * S)


func _label(name: String, rect: Rect2, variation: String, size: int, color = null, align := HORIZONTAL_ALIGNMENT_LEFT,
		wrap := false, min_size := 14) -> Label:
	var l := Kit.wrap_label("", variation) if wrap else Kit.label("", variation)
	l.position = rect.position
	l.size = rect.size
	l.custom_minimum_size = Vector2.ZERO
	l.clip_text = true
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if not wrap:
		l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	else:
		l.max_lines_visible = 2
		l.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	if color != null:
		l.add_theme_color_override("font_color", color)
	Kit.scalable(l, size)
	_desk.add_child(l)
	_lab[name] = l
	_fit.append([l, rect.size.x, rect.size.y, min_size, 2 if wrap else 1])
	return l


func _build_labels() -> void:
	var fl: Dictionary = layout.get("floor", {})
	_label("floor_kicker", _r(fl.get("kicker", [34, 4, 394, 9])), "KickerLabel", 20)
	var sp := _label("floor_speech", _r(fl.get("speech", [34, 13, 394, 21])), "BodyLabel", 23,
		Kit.C_TEXT_BRIGHT, HORIZONTAL_ALIGNMENT_LEFT, true)
	sp.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	sp.add_theme_constant_override("line_spacing", -3)
	var fr := _r(fl.get("right", [438, 4, 122, 22]))
	_label("floor_tempo", Rect2(fr.position, Vector2(fr.size.x, 30)), "DimLabel", 19)
	_label("floor_round", Rect2(fr.position + Vector2(0, 33), Vector2(fr.size.x, 30)), "KickerLabel", 18)
	var rh := _r(layout.get("rows_head", [6, 43, 120, 31]))
	_label("rows_head", Rect2(rh.position + Vector2(12, 6), Vector2(rh.size.x - 40, 34)), "KickerLabel", 22)
	_label("rows_sub", Rect2(rh.position + Vector2(12, 44), Vector2(rh.size.x - 24, 40)), "DimLabel", 18)
	var rows: Array = layout.get("rows", [])
	for i in rows.size():
		var row: Dictionary = rows[i]
		var code := _label("row_code_%d" % i, _r(row.get("code", [8, 82, 21, 12])), "HeadingLabel", 26, Kit.C_TEXT_BRIGHT,
			HORIZONTAL_ALIGNMENT_CENTER, false, 16)
		code.add_theme_font_override("font", Kit.font("fv_label"))
		var nm := _label("row_name_%d" % i, _r(row.get("name", [32, 81, 74, 8])), "", 20, INK, HORIZONTAL_ALIGNMENT_LEFT,
			false, 14)
		nm.add_theme_font_override("font", Kit.font("fv_serif_bold"))
		var st := _label("row_state_%d" % i, _r(row.get("state", [32, 89, 74, 7])), "", 17, INK_DIM,
			HORIZONTAL_ALIGNMENT_LEFT, false, 12)
		st.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	var cols: Array = layout.get("cols", [])
	for c in cols.size():
		var col: Dictionary = cols[c]
		var nl := _label("col_name_%d" % c, _r(col.get("name", [0, 0, 48, 9])), "KickerLabel", 18, null,
			HORIZONTAL_ALIGNMENT_LEFT, false, 12)
		nl.add_theme_font_override("font", Kit.font("fv_button"))
		var out := _label("col_out_%d" % c, _r(col.get("out", [0, 10, 48, 12])), "", 27, Kit.C_TEXT_BRIGHT,
			HORIZONTAL_ALIGNMENT_LEFT, false, 14)
		out.add_theme_font_override("font", Kit.font("fv_heading"))
		var via := _label("col_via_%d" % c, _r(col.get("via", [0, 22, 48, 7])), "DimLabel", 16, null,
			HORIZONTAL_ALIGNMENT_LEFT, false, 12)
		via.add_theme_font_override("font", Kit.font("fv_serif_italic"))
	var lamps: Array = layout.get("lamps", [])
	for i in lamps.size():
		var lb := _r((lamps[i] as Dictionary).get("label", [495, 55, 67, 24]))
		_label("lamp_title_%d" % i, Rect2(lb.position, Vector2(lb.size.x - 44, 36)), "KickerLabel", 25, null,
			HORIZONTAL_ALIGNMENT_LEFT, false, 14)
		_label("lamp_sub_%d" % i, Rect2(lb.position + Vector2(0, 38), Vector2(lb.size.x, 30)), "DimLabel", 18, null,
			HORIZONTAL_ALIGNMENT_LEFT, false, 12)
		var chip := Kit.panel("KeyChipPanel")
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.position = lb.position + Vector2(lb.size.x - 38, 0)
		var kl := Kit.label("G" if i == 0 else "R", "KeyHintLabel")
		kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		kl.custom_minimum_size.x = 12
		chip.add_child(kl)
		_desk.add_child(chip)
		_lab["lamp_key_%d" % i] = kl


func _build_beat() -> void:
	# the closing beat: a card over the desk body (the floor display above keeps "Der Vorsitz läutet ...")
	var body := _r(layout.get("body", [0, 38, 568, 114]))
	_beat = Kit.panel("PaperCardPanel")
	_beat.position = body.position + Vector2(24, 6)
	_beat.size = body.size - Vector2(48, 12)
	_beat.custom_minimum_size = _beat.size
	_beat.visible = false
	_beat.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_desk.add_child(_beat)
	var row := Kit.hbox(40)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	_beat.add_child(row)
	var frame := Kit.panel("PortraitPanel")
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(frame)
	_beat_portrait = View.new()
	_beat_portrait.game = self
	_beat_portrait.kind = "portrait"
	_beat_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_beat_portrait.custom_minimum_size = Vector2(168, 168)
	_beat_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_beat_portrait)
	var col := Kit.vbox(8)
	col.custom_minimum_size.x = 1180
	col.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(col)
	for i in range(1, Logic.BEAT_LINES):
		var quote := i >= 2
		var l := Kit.wrap_label(Kit.t("mg.relay.beat.%d" % (i + 1)), "PaperBody")
		Kit.scalable(l, 26 if quote else 23)
		if quote:
			l.add_theme_color_override("font_color", INK)
		else:
			l.add_theme_font_override("font", Kit.font("fv_serif_italic"))
			l.add_theme_color_override("font_color", INK_DIM)
		l.modulate.a = 0.0
		col.add_child(l)
		_beat_lines.append(l)


func open(context: Dictionary = {}) -> void:
	super.open(context)
	if int(Kit.setting("puzzle_hints", 1)) == 2:
		_hint_kind = "plug"
		show_hint(1)


func _on_open() -> void:
	if _p_hall != null and _p_hall.stream != null and not _p_hall.playing:
		_p_hall.play()
	for l in _p_voice:
		var p: AudioStreamPlayer = _p_voice[l]
		if p.stream != null and not p.playing:
			p.play()
	_update_audio(0.0)


func _on_end() -> void:
	if _p_hall != null:
		_p_hall.stop()
	for l in _p_voice:
		(_p_voice[l] as AudioStreamPlayer).stop()


## "Neu anfangen" starts the current round again (the rounds already passed stay passed).
func restart() -> void:
	if solved or ended:
		return
	Kit.ui_sound("page")
	if logic.phase == "intro" and logic.round_i == 0 and logic.attempts == 1:
		_reset_game()
	else:
		logic.restart_round()
	_lost_fail_turn = ""
	set_status("")


func _reset_game() -> void:
	logic.reset()
	_lost_fail_turn = ""
	_last_target = ""
	for b in _beat_lines:
		(b as Control).modulate.a = 0.0
	if _beat:
		_beat.visible = false
	_refresh_texts()
	_redraw()


# ================================================================ per frame
func _tick(delta: float) -> void:
	_anim += delta
	_hc = Kit.high_contrast()
	_rm = Kit.reduced_motion()
	for i in 2:
		_press_flash[i] = maxf(0.0, float(_press_flash[i]) - delta)
		_ignored_flash[i] = maxf(0.0, float(_ignored_flash[i]) - delta)
	for i in 4:
		_plug_flash[i] = maxf(0.0, float(_plug_flash[i]) - delta)
	if not solved:
		for e in logic.step(minf(delta, Logic.MAX_STEP)):
			_on_event(str(e))
	var tl: String = logic.target_lang()
	if tl != _last_target:
		_last_target = tl
		if logic.phase == "announce":
			Kit.ui_sound("move")
	_update_beat(delta)
	_update_audio(delta)
	_refresh_texts()
	_update_status()
	_fit_t -= delta
	if _fit_t <= 0.0:
		_fit_t = 0.3
		_fit_all()
	_redraw()


func _on_event(e: String) -> void:
	if e.begins_with("lost:"):
		var k := int(e.get_slice(":", 1))
		_sfx("mg_relay_lost", -2.0)
		var key := "%d.%d" % [logic.round_i, logic.turn_i]
		if key != _lost_fail_turn:      # several booths at once count as one refusal
			_lost_fail_turn = key
			_hint_kind = "lamp"
			register_fail(Kit.t("mg.relay.fail.lost").format({"n": k + 1}))
		return
	if e.begins_with("lost_end:"):
		var k2 := int(e.get_slice(":", 1))
		if _status_hold <= 0.0:
			set_status(Kit.t("mg.relay.status.lost_end").format({"n": k2 + 1}))
			_status_hold = 1.6
		return
	match e:
		"round_start":
			_sfx("mg_relay_switch", -6.0)
		"speech":
			pass
		"announce":
			pass
		"round_passed":
			_sfx("mg_relay_bell", -4.0 if logic.round_i + 1 >= Logic.ROUNDS.size() else -9.0)
			clear_status_hold()
		"round_failed":
			_sfx("mg_relay_bell", -9.0)
			_hint_kind = "lamp" if logic.last_fail == "lost" else "plug"
			var txt := _summary_text()
			register_fail(txt)
		"adjourned":
			# her thanks follow how the session went: lamps in time, or threads lost and caught again
			if _beat_lines.size() > 1:
				(_beat_lines[1] as Label).text = Kit.t("mg.relay.beat.3.lost" if logic.lost_count > 0 else "mg.relay.beat.3")
			_beat.visible = true
			Kit.appear(_beat, 0.5)
		"solved":
			mark_solved(Kit.t("mg.relay.solved"))


func _update_beat(_delta: float) -> void:
	if _beat == null or not _beat.visible:
		return
	var n: int = logic.beat_lines()
	for i in _beat_lines.size():
		var l: Control = _beat_lines[i]
		var target := 1.0 if n >= i + 2 else 0.0
		l.modulate.a = target if _rm else move_toward(l.modulate.a, target, 0.04)


func _update_audio(_delta: float) -> void:
	if _p_hall != null:
		var hall_db := -13.0
		if logic.phase == "beat" or solved:
			hall_db = -9.0             # the break: the hall murmurs louder, nobody on the microphone
		_p_hall.volume_db = move_toward(_p_hall.volume_db, hall_db, 1.5)
	var fl: String = logic.floor_lang()
	var tau: float = logic.effective_tempo()
	for l in _p_voice:
		var p: AudioStreamPlayer = _p_voice[l]
		var want := -7.0 if l == fl else -80.0
		p.volume_db = move_toward(p.volume_db, want, 6.0 if want > p.volume_db else 9.0)
		if l == fl:
			p.pitch_scale = clampf(1.0 + (tau - 1.0) * 0.22, 0.88, 1.14)


# ================================================================ texts
func _set_text(name: String, text: String, color = null) -> void:
	var l: Label = _lab.get(name)
	if l == null:
		return
	if l.text != text:
		l.text = text
	if color != null:
		l.add_theme_color_override("font_color", color)


## High contrast: the dim texts of the desk become full text colour (on the dark plates and the cream tags).
func _c_dim() -> Color:
	return Kit.C_TEXT if _hc else Kit.C_TEXT_DIM


func _c_ink_dim() -> Color:
	return INK if _hc else INK_DIM


func _lang(code: String) -> String:
	return Kit.t("mg.relay.lang." + code) if code != "" else ""


func _code(code: String) -> String:
	return Kit.t("mg.relay.code." + code) if code != "" else ""


func _who(who: String) -> String:
	return Kit.t("mg.relay.who." + who)


func _confirm_key() -> String:
	var k := Kit.action_key_text("interact")
	return k if k != "" else Kit.key_name(KEY_SPACE)


func _summary_text() -> String:
	var p := int(round(logic.last_ratio * 100.0))
	if logic.last_passed:
		return Kit.t("mg.relay.summary.ok").format({"n": logic.round_i + 1, "p": p})
	if logic.last_fail == "lost":
		return Kit.t("mg.relay.summary.fail_lost").format({"n": logic.round_lost})
	return Kit.t("mg.relay.summary.fail_ratio").format({"p": p})


func _refresh_texts() -> void:
	var rk := str(logic.round_def()["key"])
	var nround := Logic.ROUNDS.size()
	var bright := Kit.C_TEXT_BRIGHT
	# ---- floor display
	match logic.phase:
		"intro":
			var first: Dictionary = (logic.turns()[0] as Dictionary)
			var who := str(first.get("who", "chair"))
			_set_text("floor_kicker", (Kit.t("mg.relay.round").format({"n": logic.round_i + 1, "total": nround}) + " · "
				+ Kit.t("mg.relay.intro.opens").format({"who": _who(who), "lang": _lang(logic.speaker_lang(who))})).to_upper().replace("ß", "SS"),
				Kit.C_COPPER_L)
			var note := Kit.t("mg.relay.%s.note" % rk)
			if logic.attempts > 1 and logic.last_fail != "":
				note = Kit.t("mg.relay.intro.again") + " " + note
			_set_text("floor_speech", Kit.t("mg.relay.%s.title" % rk) + "\n" + note, bright)
			_set_text("floor_tempo", Kit.t("mg.relay.intro.go").format({"key": _confirm_key()}).to_upper().replace("ß", "SS"), Kit.C_AMBER)
		"announce":
			var head := Kit.t("mg.relay.floor.interject") if logic.is_interjection() else Kit.t("mg.relay.floor.announce")
			_set_text("floor_kicker", (head + " · " + _who(logic.speaker()) + " · " + _lang(logic.speaker_lang())).to_upper().replace("ß", "SS"),
				Kit.C_AMBER)
			_set_text("floor_speech", "", bright)
			_set_text("floor_tempo", "", null)
		"speech":
			var lang := _lang(logic.speaker_lang())
			_set_text("floor_kicker", (Kit.t("mg.relay.floor.at_mic") + " · " + _who(logic.speaker()) + " · " + lang).to_upper().replace("ß", "SS"),
				Kit.C_COPPER_L)
			var full := Kit.t(logic.turn_key())
			if logic.pause_left > 0.0:
				_set_text("floor_speech", _reveal(full, logic.speech_progress()) + "  —  " + Kit.t("mg.relay.floor.paused"), bright)
			else:
				_set_text("floor_speech", _reveal(full, logic.speech_progress()), bright)
			_set_text("floor_tempo", (Kit.t("mg.relay.tempo") + " · " + _tempo_word()).to_upper().replace("ß", "SS"),
				C_YEL if logic.yellow_left > 0.0 else (C_BAD if logic.pause_left > 0.0 else _c_dim()))
		"summary":
			_set_text("floor_kicker", (Kit.t("mg.relay.round").format({"n": logic.round_i + 1, "total": nround})).to_upper().replace("ß", "SS"),
				Kit.C_COPPER_L if logic.last_passed else C_BAD)
			var t := _summary_text()
			if logic.last_passed:
				t += "\n" + Kit.t("mg.relay.%s.done" % rk)
			_set_text("floor_speech", t, bright)
			_set_text("floor_tempo", Kit.t("mg.relay.summary.next").format({"key": _confirm_key()}).to_upper().replace("ß", "SS"), Kit.C_AMBER)
		_:
			_set_text("floor_kicker", Kit.t("mg.relay.beat.1").to_upper().replace("ß", "SS"), Kit.C_COPPER_L)
			_set_text("floor_speech", Kit.t("mg.relay.floor.silent"), _c_dim())
			_set_text("floor_tempo", Kit.t("mg.relay.summary.next").format({"key": _confirm_key()}).to_upper().replace("ß", "SS") if logic.phase == "beat" else "",
				Kit.C_AMBER)
	var ratio_p := int(round(logic.ratio() * 100.0))
	var rt := Kit.t("mg.relay.round").format({"n": logic.round_i + 1, "total": nround})
	if logic.phase == "speech" or logic.phase == "announce":
		rt += " · " + Kit.t("mg.relay.score").format({"p": ratio_p})
	_set_text("floor_round", rt.to_upper().replace("ß", "SS"), Kit.C_COPPER_L)
	# ---- channels
	_set_text("rows_head", Kit.t("mg.relay.rows.head").to_upper().replace("ß", "SS"), Kit.C_COPPER_L)
	_set_text("rows_sub", Kit.t("mg.relay.rows.sub"), null)
	var predicted: String = logic.target_lang()
	for r in Logic.ROWS.size():
		var code: String = Logic.ROWS[r]
		_set_text("row_code_%d" % r, _code(code), bright)
		_set_text("row_name_%d" % r, Kit.t("mg.relay.row." + code).to_upper().replace("ß", "SS"), INK)
		var hs := ""
		var col := _c_ink_dim()
		if logic.phase == "speech":
			var h: String = logic.heard(r)
			hs = Kit.t("mg.relay.hears.none") if h == "" else Kit.t("mg.relay.hears").format({"code": _code(h)})
			col = INK if logic.row_ok(r) else Color("8a2a20")
		elif predicted != "":
			var c := int(logic.plugs[r])
			var will := logic.correct_col(r, predicted)
			hs = Kit.t("mg.relay.hears").format({"code": _code(_source_lang(c, predicted))})
			col = _c_ink_dim() if c == will else Color("8a2a20")
		_set_text("row_state_%d" % r, hs, col)
	# ---- sources
	var fl := logic.floor_lang()
	var shown := fl if fl != "" else predicted
	for c in Logic.SOURCES.size():
		if c == 0:
			_set_text("col_name_0", Kit.t("mg.relay.col.saal").to_upper().replace("ß", "SS"), null)
			_set_text("col_out_0", Kit.t("mg.relay.out").format({"code": _code(shown)}) if shown != "" else Kit.t("mg.relay.tempo.none"),
				bright if fl != "" else _c_dim())
			_set_text("col_via_0", Kit.t("mg.relay.col.saal.sub"), null)
			continue
		var k := c - 1
		_set_text("col_name_%d" % c, Kit.t("mg.relay.col.k").format({"n": c}).to_upper().replace("ß", "SS") + " · " + Kit.t("mg.relay.booth.k%d" % c), null)
		var out := ""
		var via := ""
		var oc := bright
		var vc = null
		if float(logic.lost[k]) > 0.0:
			out = Kit.t("mg.relay.state.lost")
			oc = C_BAD
		elif shown == "":
			out = Kit.t("mg.relay.state.idle")
			oc = _c_dim()
		else:
			var o: String = logic.booth_out(k, shown)
			out = Kit.t("mg.relay.out").format({"code": _code(o)})
			var pv: int = logic.pivot(k, shown)
			if pv >= 0:
				via = Kit.t("mg.relay.via").format({"n": pv + 1})
				vc = C_YEL
			elif shown == str(Logic.INTO[Logic.BOOTHS[k]]):
				via = Kit.t("mg.relay.out.retour")
			else:
				via = Kit.t("mg.relay.direct")
			if fl == "":
				oc = Kit.C_TEXT if logic.phase == "announce" else _c_dim()
		_set_text("col_out_%d" % c, out, oc)
		_set_text("col_via_%d" % c, via, vc if vc != null else _c_dim())
	# ---- lamps
	_set_text("lamp_title_0", Kit.t("mg.relay.lamp.yellow").to_upper().replace("ß", "SS"), C_YEL if logic.yellow_left > 0.0 else Kit.C_COPPER_L)
	_set_text("lamp_sub_0", Kit.t("mg.relay.lamp.yellow.sub"), null)
	_set_text("lamp_title_1", Kit.t("mg.relay.lamp.red").to_upper().replace("ß", "SS"), C_BAD if logic.pause_left > 0.0 else Kit.C_COPPER_L)
	_set_text("lamp_sub_1", Kit.t("mg.relay.lamp.red.sub"), null)
	var yk: Label = _lab.get("lamp_key_0")
	var rk2: Label = _lab.get("lamp_key_1")
	if yk:
		yk.text = "X" if Kit.last_input_pad else Kit.key_name(KEY_G)
	if rk2:
		rk2.text = "Y" if Kit.last_input_pad else Kit.key_name(KEY_R)


## Language a source carries for floor language fl.
func _source_lang(c: int, fl: String) -> String:
	if c == 0:
		return fl
	return logic.booth_out(c - 1, fl)


## The speech text revealed up to the speaker's progress (whole words), so the display follows his pace.
func _reveal(full: String, p: float) -> String:
	if p >= 0.999:
		return full
	var n := int(ceil(full.length() * clampf(p * 1.08, 0.0, 1.0)))
	if n <= 0:
		return ""
	var cut := full.substr(0, n)
	var sp := cut.rfind(" ")
	if sp > 0 and n < full.length():
		cut = cut.substr(0, sp)
	return cut + " …"


func _tempo_word() -> String:
	if logic.pause_left > 0.0:
		return Kit.t("mg.relay.tempo.stopped")
	if logic.yellow_left > 0.0:
		return Kit.t("mg.relay.tempo.slowed")
	var t: float = logic.tempo()
	if t < 0.95:
		return Kit.t("mg.relay.tempo.calm")
	if t < 1.15:
		return Kit.t("mg.relay.tempo.normal")
	if t < 1.38:
		return Kit.t("mg.relay.tempo.brisk")
	return Kit.t("mg.relay.tempo.fast")


func _update_status() -> void:
	if solved:
		return
	match logic.phase:
		"intro":
			status_auto(Kit.t("mg.relay.status.intro"))
		"announce":
			var key := "mg.relay.status.interject" if logic.is_interjection() else "mg.relay.status.announce"
			status_auto(Kit.t(key).format({"who": _who(logic.speaker()), "lang": _lang(logic.speaker_lang())}))
		"speech":
			for r in Logic.ROWS.size():
				if not logic.row_ok(r):
					var h: String = logic.heard(r)
					var row := Kit.t("mg.relay.row." + str(Logic.ROWS[r]))
					if h == "":
						status_auto(Kit.t("mg.relay.status.silence").format({"row": row}))
					else:
						status_auto(Kit.t("mg.relay.status.wrong").format({"row": row, "lang": _lang(h)}))
					return
			var worst := -1
			var wb := 0.0
			for k in Logic.BOOTHS.size():
				if float(logic.lost[k]) <= 0.0 and float(logic.backlog[k]) > wb:
					wb = float(logic.backlog[k])
					worst = k
			if worst >= 0 and wb >= Logic.ZONE_RED and logic.pause_left <= 0.0:
				status_auto(Kit.t("mg.relay.status.far_behind").format({"n": worst + 1}))
			elif worst >= 0 and wb >= Logic.ZONE_YELLOW and logic.yellow_left <= 0.0 and logic.pause_left <= 0.0:
				status_auto(Kit.t("mg.relay.status.behind").format({"n": worst + 1}))
			elif logic.pause_left > 0.0:
				status_auto(Kit.t("mg.relay.status.red"))
			elif logic.yellow_left > 0.0:
				status_auto(Kit.t("mg.relay.status.yellow"))
			else:
				status_auto(Kit.t("mg.relay.status.all_ok"))
		"summary":
			status_auto(_summary_text())
		_:
			status_auto("")


## The desk is fixed pixel art: its labels follow the text-scale setting as far as their plates allow and shrink
## a line that would not fit (width, and the height of one or two lines) instead of overflowing; never below min.
## The chrome around the desk (instruction, status, hints) scales fully; with enlarged text the flavour subtitle
## gives its room to the desk.
func _fit_all() -> void:
	var ts := Kit.text_scale()
	if _subtitle != null:
		_subtitle.visible = ts <= 1.1
	for f in _fit:
		var l: Label = f[0]
		if not is_instance_valid(l):
			continue
		var base := int(l.get_meta("aoe_base_size", 20))
		var size := int(round(base * ts))
		var font := l.get_theme_font("font")
		var maxw: float = float(f[1]) - 4.0
		var maxh: float = float(f[2]) + (6.0 if int(f[4]) == 1 else 3.0)
		var lines := int(f[4])
		while size > int(f[3]):
			var hh := font.get_height(size) * lines + (lines - 1) * float(l.get_theme_constant("line_spacing"))
			var ww := 0.0 if lines > 1 or l.text == "" else font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			if hh <= maxh and ww <= maxw:
				break
			size -= 1
		if l.get_theme_font_size("font_size") != size:
			l.add_theme_font_size_override("font_size", size)


## Hints follow the cause of the refusals: lost threads -> the lamps; channels that were wrong -> the guide lights
## (the matching sockets glow from now on); from the second hint on the guides stay on; the third explains the
## announcements. Settings "puzzle_hints" 0 switches them off, 2 shows the first one at once.
func _hint_text(level: int) -> String:
	if int(Kit.setting("puzzle_hints", 1)) == 0:
		return ""
	if level >= 2:
		_guides = true
	if level >= 3:
		return Kit.t("mg.relay.hint.announce")
	if _hint_kind == "lamp":
		return Kit.t("mg.relay.hint.lamp")
	_guides = true
	return Kit.t("mg.relay.hint.plug")


func show_hint(level: int) -> void:
	super.show_hint(level)
	if _hint_box != null and _hint_box.visible and _instr != null:
		_instr.visible = false          # the hint takes the instruction's place (keeps the desk inside the panel)


func _controls() -> Array:
	if solved or logic.phase == "beat":
		return [[_confirm_key(), Kit.t("mg.relay.ctrl.next")]]
	var keys_ud := Kit.key_name(KEY_UP) + "|" + Kit.key_name(KEY_DOWN)
	var keys_lr := Kit.key_name(KEY_LEFT) + "|" + Kit.key_name(KEY_RIGHT)
	var pairs := [[keys_ud, Kit.t("mg.relay.ctrl.row")], [keys_lr, Kit.t("mg.relay.ctrl.plug")],
		["1|2|3|4", Kit.t("mg.relay.ctrl.direct")]]
	if Kit.last_input_pad:
		pairs = [["↑|↓", Kit.t("mg.relay.ctrl.row")], ["←|→", Kit.t("mg.relay.ctrl.plug")]]
	pairs.append(["X" if Kit.last_input_pad else Kit.key_name(KEY_G), Kit.t("mg.relay.ctrl.yellow")])
	pairs.append(["Y" if Kit.last_input_pad else Kit.key_name(KEY_R), Kit.t("mg.relay.ctrl.red")])
	if logic.phase in ["intro", "summary", "beat"]:
		pairs.append([_confirm_key(), Kit.t("mg.relay.ctrl.next")])
	return pairs


# ================================================================ input
func _game_input(event: InputEvent) -> bool:
	var k := _key(event, true)
	var pb := _pad(event)
	if k == KEY_G or pb == JOY_BUTTON_X:
		if not (event is InputEventKey and (event as InputEventKey).echo):
			_press_lamp(0)
		return true
	if k == KEY_R or pb == JOY_BUTTON_Y:
		if not (event is InputEventKey and (event as InputEventKey).echo):
			_press_lamp(1)
		return true
	for i in 4:
		if k == DIGITS[i] or k == KP_DIGITS[i]:
			if not (event is InputEventKey and (event as InputEventKey).echo):
				_plug(logic.sel, i)
			return true
	if _is(event, ["ui_up", "move_up"], true):
		_move_sel(-1)
		return true
	if _is(event, ["ui_down", "move_down"], true):
		_move_sel(1)
		return true
	if _is(event, ["ui_left", "move_left"], true):
		_shift(-1)
		return true
	if _is(event, ["ui_right", "move_right"], true):
		_shift(1)
		return true
	if _is(event, ["ui_accept", "interact"]):
		if logic.advance():
			Kit.ui_sound("confirm")
		return true
	if event is InputEventKey and event.echo:
		return true
	return false


func _move_sel(d: int) -> void:
	if logic.phase == "beat":
		return
	logic.move_sel(d)
	Kit.ui_sound("move")


func _shift(d: int) -> void:
	if logic.shift(d):
		_after_plug(logic.sel)


func _plug(r: int, c: int) -> void:
	if logic.plug(r, c):
		_after_plug(r)
	else:
		logic.select(r)


func _after_plug(r: int) -> void:
	_plug_flash[r] = 0.18
	_sfx("mg_relay_plug", -3.0)
	clear_status_hold()


func _press_lamp(i: int) -> void:
	var res: String = logic.yellow() if i == 0 else logic.red()
	match res:
		"yellow":
			_press_flash[0] = 0.25
			_sfx("mg_relay_lamp_yellow", -3.0)
			set_status(Kit.t("mg.relay.status.yellow"))
			_status_hold = 1.8
		"red":
			_press_flash[1] = 0.25
			_sfx("mg_relay_lamp_red", -3.0)
			set_status(Kit.t("mg.relay.status.red"))
			_status_hold = 1.8
		"yellow_ignored", "red_ignored":
			_ignored_flash[i] = 0.35
			_sfx("mg_relay_click", -4.0)
			set_status(Kit.t("mg.relay.status." + res))
			_status_hold = 2.6
		_:
			_ignored_flash[i] = 0.2
			_sfx("mg_relay_click", -8.0)


func desk_input(event: InputEvent) -> void:
	if ended or solved:
		return
	if not (event is InputEventMouseButton) or not (event as InputEventMouseButton).pressed:
		return
	var mb := event as InputEventMouseButton
	if mb.button_index != MOUSE_BUTTON_LEFT:
		return
	var p := mb.position / S
	if logic.phase in ["intro", "summary", "beat"] and _in(p, (layout.get("floor", {}) as Dictionary).get("rect", [0, 0, 568, 30])):
		if logic.advance():
			Kit.ui_sound("confirm")
		return
	if logic.phase == "beat":
		if logic.advance():
			Kit.ui_sound("confirm")
		return
	var lamps: Array = layout.get("lamps", [])
	for i in lamps.size():
		var lc: Array = (lamps[i] as Dictionary).get("centre", [0, 0])
		var lb: Array = (lamps[i] as Dictionary).get("label", [0, 0, 0, 0])
		if p.distance_to(Vector2(float(lc[0]), float(lc[1]))) <= float((lamps[i] as Dictionary).get("r", 13)) + 3.0 or _in(p, lb):
			_press_lamp(i)
			return
	var rows: Array = layout.get("rows", [])
	var cols: Array = layout.get("cols", [])
	for r in rows.size():
		var row: Dictionary = rows[r]
		var y0 := float(row.get("y", 0))
		if p.y < y0 or p.y >= y0 + float(row.get("h", 17)):
			continue
		for c in cols.size():
			var col: Dictionary = cols[c]
			var x0 := float(col.get("x", 0))
			if p.x >= x0 and p.x < x0 + float(col.get("w", 82)):
				_plug(r, c)
				return
		if _in(p, row.get("tag", [0, 0, 0, 0])):
			logic.select(r)
			Kit.ui_sound("move")
		return


func portrait_input(_event: InputEvent) -> void:
	pass


static func _in(p: Vector2, rect) -> bool:
	var a: Array = rect if rect is Array else [0, 0, 0, 0]
	return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3])).has_point(p)


func _redraw() -> void:
	if _desk:
		_desk.queue_redraw()
	if _beat_portrait and _beat and _beat.visible:
		_beat_portrait.queue_redraw()


# ================================================================ drawing (art px, x3)
func _cell(tex_key: String, idx: int, cell: Vector2, dst: Vector2, mod := Color.WHITE, row := 0) -> void:
	var t: Texture2D = _tex.get(tex_key)
	if t == null:
		return
	_desk.draw_texture_rect_region(t, Rect2(dst, cell), Rect2(Vector2(idx * cell.x, row * cell.y), cell), mod)


func draw_desk(v: Control) -> void:
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2(S, S))
	var dt: Texture2D = _tex.get("relay_desk")
	if dt != null:
		v.draw_texture(dt, Vector2.ZERO)
	else:
		v.draw_rect(Rect2(Vector2.ZERO, v.size / S), Kit.C_NAVY)
	var cells: Dictionary = layout.get("cells", {})
	var pin_cell := _v(cells.get("pin", [13, 15]))
	var pin_org := _v(cells.get("pin_origin", [6, 9]))
	var lamp_cell := _v(cells.get("lamp", [30, 30]))
	var icon_cell := _v(cells.get("icon", [9, 9]))
	var booth_cell := _v(cells.get("booth", [20, 24]))
	var blink_on := _rm or fmod(_anim, 0.9) < 0.6
	var fl: String = logic.floor_lang()
	var target: String = logic.target_lang()
	# ---- floor lamp
	var flp := _v((layout.get("floor", {}) as Dictionary).get("lamp", [18, 15]))
	var floor_on: bool = fl != "" or (logic.phase == "announce" and blink_on)
	_cell("relay_lamps", 5 if floor_on else 4, lamp_cell, flp - lamp_cell / 2.0)
	# ---- progress groove (speech progress / announcement / intro countdown)
	var pg: Array = (layout.get("floor", {}) as Dictionary).get("progress", [439, 23, 120, 2])
	var pr := Rect2(float(pg[0]), float(pg[1]), float(pg[2]), float(pg[3]))
	var pv := 0.0
	var pcol := Kit.C_COPPER_L
	match logic.phase:
		"speech":
			pv = logic.speech_progress()
		"announce":
			pv = logic.announce_left() / maxf(0.01, float(logic.turn().get("announce", 1.0)))
			pcol = Kit.C_AMBER
		"intro":
			pv = 1.0 - logic.phase_t / Logic.INTRO_TIME
			pcol = Kit.C_AMBER
		"summary":
			pv = 1.0 - logic.phase_t / Logic.SUMMARY_TIME
			pcol = Kit.C_AMBER
	if pv > 0.0:
		v.draw_rect(Rect2(pr.position, Vector2(roundf(pr.size.x * clampf(pv, 0.0, 1.0)), pr.size.y)), pcol)
	# ---- source plates: booth windows, meters
	var cols: Array = layout.get("cols", [])
	for c in cols.size():
		var col: Dictionary = cols[c]
		var win := _rect(col.get("window", [0, 0, 20, 24]))
		var st := 0
		var who := 3 if c == 0 else c - 1
		if c == 0:
			st = (1 + int(_anim * 5.0) % 2 if not _rm else 1) if fl != "" else 0
		else:
			var k := c - 1
			if float(logic.lost[k]) > 0.0:
				st = 4
			elif fl == "" or logic.booth_silent(k):
				st = 0
			elif logic.zone(k) == "red" or logic.zone(k) == "yellow" and float(logic.backlog[k]) > 0.6:
				st = 3
			else:
				var rate := 3.0 if logic.yellow_left > 0.0 else 5.0
				st = 1 + (int(_anim * rate + k) % 2 if not _rm else 0)
		_cell("relay_booths", st, booth_cell, win.position, Color.WHITE, who)
		if c > 0 and col.get("meter") is Array:
			_draw_meter(v, c - 1, _rect(col["meter"]), blink_on)
	# ---- selection band
	var rows: Array = layout.get("rows", [])
	var rp := _rect(layout.get("rows_panel", [2, 33, 114, 106]))
	var xb := _rect(layout.get("crossbar", [120, 71, 328, 68]))
	if logic.phase != "beat" and logic.sel < rows.size():
		var row: Dictionary = rows[logic.sel]
		var y0 := float(row.get("y", 71))
		var hh := float(row.get("h", 17))
		var band := Rect2(rp.position.x + 1, y0, xb.end.x - rp.position.x - 1, hh + 1)
		var sc := Color(1, 1, 1, 0.95) if _hc else Color(Kit.C_AMBER, 0.9)
		v.draw_rect(band, sc, false, 1.0)
		if _hc:
			v.draw_rect(band.grow(-1), Color(0, 0, 0, 0.8), false, 1.0)
		v.draw_rect(Rect2(xb.position.x, y0 + 1, xb.size.x, hh - 1), Color(Kit.C_AMBER, 0.07))
	# ---- guides (hint) and pins
	for r in rows.size():
		var row: Dictionary = rows[r]
		var sy := float(row.get("socket_y", 79))
		if _guides and target != "":
			var gc := logic.correct_col(r, target)
			if gc >= 0 and gc != int(logic.plugs[r]):
				var gx := float((cols[gc] as Dictionary).get("socket_x", 0))
				var ga := 1.0 if (blink_on or _hc) else 0.55
				_cell("relay_pins", 2, pin_cell, Vector2(gx, sy) - pin_org, Color(1, 1, 1, ga))
		var c2 := int(logic.plugs[r])
		var sx := float((cols[c2] as Dictionary).get("socket_x", 0))
		var lift := -1.0 if float(_plug_flash[r]) > 0.0 else 0.0
		if r == logic.sel and logic.phase != "beat":
			_cell("relay_pins", 1, pin_cell, Vector2(sx, sy) - pin_org, Color(1, 1, 1, 0.95) if not _hc else Color(1.4, 1.4, 1.4))
		_cell("relay_pins", 0, pin_cell, Vector2(sx, sy + lift) - pin_org)
		# row status icon (actual during speech, predicted while the floor is being given)
		var ip := _v(row.get("icon", [108, 84]))
		var icon := -1
		var ia := 1.0
		if logic.phase == "speech":
			icon = 0 if logic.row_ok(r) else (2 if logic.heard(r) == "" else 1)
		elif target != "":
			icon = 0 if c2 == logic.correct_col(r, target) else 1
			ia = 0.65 if blink_on else 0.4
		if icon >= 0:
			v.draw_rect(Rect2(ip - Vector2(1, 1), icon_cell + Vector2(2, 2)), Color(0.08, 0.08, 0.1, 0.55 * ia))
			_cell("relay_icons", icon, icon_cell, ip, Color(1, 1, 1, ia))
	# ---- lamps
	var lamps: Array = layout.get("lamps", [])
	for i in lamps.size():
		var lc := _v((lamps[i] as Dictionary).get("centre", [474, 58]))
		var lit: bool = (logic.yellow_left > 0.0) if i == 0 else (logic.pause_left > 0.0)
		if float(_press_flash[i]) > 0.0:
			lit = true
		var frame := (1 if lit else 0) + i * 2
		var mod := Color.WHITE
		if float(_ignored_flash[i]) > 0.0:
			mod = Color(0.75, 0.75, 0.8)
		_cell("relay_lamps", frame, lamp_cell, lc - lamp_cell / 2.0, mod)
		var left: float = logic.yellow_left / Logic.YELLOW_TIME if i == 0 else logic.pause_left / Logic.RED_TIME
		if left > 0.0:
			var rr := float((lamps[i] as Dictionary).get("r", 13)) + 3.5
			var col2 := C_YEL if i == 0 else C_BAD
			v.draw_arc(lc + Vector2(0.5, 0.5), rr, -PI / 2.0, -PI / 2.0 + TAU * clampf(left, 0.0, 1.0), 40,
				Color(col2, 0.95), 1.0 if not _hc else 1.6)
	v.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_meter(v: Control, k: int, m: Rect2, blink_on: bool) -> void:
	var b := clampf(float(logic.backlog[k]), 0.0, 1.0)
	var lost := float(logic.lost[k]) > 0.0
	# darken the part of the scale above the level: the painted zones up to the level stay bright
	var lx := m.position.x + roundf(b * m.size.x)
	if lx < m.end.x:
		v.draw_rect(Rect2(Vector2(lx, m.position.y), Vector2(m.end.x - lx, m.size.y)), Color(0.03, 0.04, 0.05, 0.5))
	var nc := Color(1, 1, 1) if _hc else Color("f5efda")
	if lost:
		nc = C_BAD
	# the needle: a bright line through the scale with a small notch under it (clear of the text above)
	var nx := clampf(lx - 1.0, m.position.x, m.end.x - 1.0)
	v.draw_rect(Rect2(Vector2(nx, m.position.y - 1.0), Vector2(1.0, m.size.y + 2.0)), nc)
	v.draw_colored_polygon(PackedVector2Array([Vector2(nx - 1.5, m.end.y + 2.5), Vector2(nx + 2.5, m.end.y + 2.5),
		Vector2(nx + 0.5, m.end.y + 0.5)]), nc)
	var z: String = logic.zone(k)
	if (z == "red" or lost) and blink_on:
		v.draw_rect(m.grow(1.0), C_BAD, false, 1.0)
	elif z == "yellow" and (blink_on or logic.yellow_left > 0.0):
		v.draw_rect(m.grow(1.0), Color(C_YEL, 0.85), false, 1.0)


func draw_portrait(v: Control) -> void:
	var t: Texture2D = _tex.get("relay_interpreter")
	var cell := _v((layout.get("cells", {}) as Dictionary).get("interpreter", [56, 56]))
	if t == null:
		v.draw_rect(Rect2(Vector2.ZERO, v.size), Kit.C_NAVY)
		return
	var f := 1 if logic.beat_lines() >= 6 or solved else 0
	v.draw_texture_rect_region(t, Rect2(Vector2.ZERO, cell * 3.0), Rect2(Vector2(f * cell.x, 0), cell))


static func _v(a) -> Vector2:
	var arr: Array = a if a is Array else [0, 0]
	return Vector2(float(arr[0]), float(arr[1]))


static func _rect(a) -> Rect2:
	var arr: Array = a if a is Array else [0, 0, 0, 0]
	return Rect2(float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


# ================================================================ synthetic solve (real-input driver)
## Plays the whole session through synthetic key events only (scripts/core/inputplay.gd calls it once): during
## every announcement it re-plugs the channels for the coming speaker (Up/Down to the row, a digit for the socket),
## gives Yellow when a needle enters the yellow zone and Red when one runs deep into the red, and confirms the
## intros, summaries and the closing beat with Space.
func demo_solve() -> void:
	var t0 := Time.get_ticks_msec()
	await _frames(2)
	while not solved and not ended and Time.get_ticks_msec() - t0 < 420000:
		var ph: String = logic.phase
		if ph == "intro" or ph == "summary" or ph == "beat":
			var fl0: String = logic.target_lang()
			if ph == "intro" and fl0 != "" and not logic.desk_right(fl0):
				await _demo_plug(fl0)
				continue
			if logic.phase_t > 0.6:
				await _tap(KEY_SPACE)
			else:
				await _frames(2)
			continue
		var fl: String = logic.target_lang()
		if fl != "" and not logic.desk_right(fl):
			await _demo_plug(fl)
			continue
		var m: float = logic.max_backlog()
		if ph == "speech" and m >= 0.8 and logic.pause_left <= 0.0:
			await _tap(KEY_R)
			continue
		if ph == "speech" and m >= Logic.ZONE_YELLOW and logic.yellow_left <= 0.0 and logic.pause_left <= 0.0:
			await _tap(KEY_G)
			continue
		await _frames(2)


## One re-plug through keys: move the cursor to the first wrong row, then press its socket digit.
func _demo_plug(fl: String) -> void:
	for r in Logic.ROWS.size():
		var want: int = logic.correct_col(r, fl)
		if want < 0 or int(logic.plugs[r]) == want:
			continue
		var guard := 0
		while logic.sel != r and guard < 6:
			guard += 1
			await _tap(KEY_DOWN if r > logic.sel else KEY_UP)
		await _tap(DIGITS[want])
		return
