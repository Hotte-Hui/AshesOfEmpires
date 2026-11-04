extends "res://scripts/ui/ui_modal.gd"
## Small yes/no confirmation (overwrite / delete / load / quit). `await ask(text)` -> bool.
## Default focus is "Nein" unless default_yes, so a hasty Enter never destroys anything.

signal answered(yes: bool)

var _msg: Label
var _yes: Button
var _no: Button
var _default_yes := false
var _answered := false


func _ready() -> void:
	pauses_game = true
	add_child(Kit.dimmer(0.5))
	var p := Kit.panel("SolidPanel")
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -440
	p.offset_right = 440
	p.offset_top = -150
	p.offset_bottom = 150
	p.grow_vertical = Control.GROW_DIRECTION_BOTH
	add_child(p)
	var v := Kit.vbox(30)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	p.add_child(v)
	_msg = Kit.wrap_label("", "BodyLabel")
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(_msg, 30)
	v.add_child(_msg)
	var row := Kit.hbox(24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(row)
	_yes = Kit.button(Kit.t("ui.common.yes"), "", 220)
	_yes.pressed.connect(_answer.bind(true))
	row.add_child(_yes)
	_no = Kit.button(Kit.t("ui.common.no"), "", 220)
	_no.pressed.connect(_answer.bind(false))
	row.add_child(_no)


func ask(text: String, yes_text := "", no_text := "", default_yes := false) -> bool:
	_msg.text = text
	_yes.text = yes_text if yes_text != "" else Kit.t("ui.common.yes")
	_no.text = no_text if no_text != "" else Kit.t("ui.common.no")
	_default_yes = default_yes
	_answered = false
	open_modal()
	var r: bool = await answered
	return r


func _answer(yes: bool) -> void:
	if _answered:
		return
	_answered = true
	Kit.ui_sound("confirm" if yes else "back")
	close()
	answered.emit(yes)


func handle_cancel() -> bool:
	_answer(false)
	return true


func _on_close() -> void:
	if not _answered:
		_answered = true
		answered.emit(false)


func focus_default() -> void:
	(_yes if _default_yes else _no).grab_focus()
