extends Control
## Base class of every modal UI panel (inspect, puzzles, journal, menus, dialogue, confirm).
## UIRoot keeps them on a modal stack: the top modal receives input first (modal_input / handle_cancel),
## pausing modals pause the SceneTree (UI itself runs with PROCESS_MODE_ALWAYS), focus is restored when a
## modal above is closed. Works stand-alone too (without UIRoot) for tests.

const Kit := preload("res://scripts/ui/ui_kit.gd")

signal opened
signal closed

## Pauses the world while open (get_tree().paused via UIRoot).
var pauses_game := true
## Escape / B closes this modal.
var closes_on_cancel := true
## Set by UIRoot.
var ui_root: Node = null
var is_open := false
var _restore_focus: Control = null


func _init() -> void:
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP


## Push onto the UIRoot stack (or just show when used stand-alone).
func open_modal() -> void:
	if ui_root != null and ui_root.has_method("push_modal"):
		ui_root.push_modal(self)
	elif not is_open:
		_modal_shown()


func close() -> void:
	if not is_open:
		return
	if ui_root != null and ui_root.has_method("pop_modal"):
		ui_root.pop_modal(self)
	else:
		_modal_hidden()


# ---- called by UIRoot ------------------------------------------------------------------------
func _modal_shown() -> void:
	is_open = true
	visible = true
	_on_open()
	Kit.appear(self, 0.16)
	opened.emit()
	focus_default.call_deferred()


func _modal_hidden() -> void:
	is_open = false
	visible = false
	_restore_focus = null
	_on_close()
	closed.emit()


func _modal_covered() -> void:
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	_restore_focus = f if f != null and is_ancestor_of(f) else null


func _modal_uncovered() -> void:
	if _restore_focus != null and is_instance_valid(_restore_focus) and _restore_focus.is_visible_in_tree():
		_restore_focus.grab_focus.call_deferred()
	else:
		focus_default.call_deferred()


# ---- overridables ------------------------------------------------------------------------------
## Return true to consume the event (called from UIRoot._input before the GUI sees it).
func modal_input(_event: InputEvent) -> bool:
	return false


## Escape / B / cancel action. Return true when handled.
func handle_cancel() -> bool:
	if closes_on_cancel:
		Kit.ui_sound("back")
		close()
		return true
	return false


func focus_default() -> void:
	pass


func _on_open() -> void:
	pass


func _on_close() -> void:
	pass


## Helper: first visible, enabled focusable descendant.
func _focus_first(root: Node) -> void:
	for c in root.get_children():
		if c is Control and (c as Control).is_visible_in_tree():
			var cc := c as Control
			if cc.focus_mode == Control.FOCUS_ALL and not (cc is BaseButton and (cc as BaseButton).disabled):
				cc.grab_focus()
				return
			_focus_first(cc)
			if get_viewport().gui_get_focus_owner() != null and is_ancestor_of(get_viewport().gui_get_focus_owner()):
				return
