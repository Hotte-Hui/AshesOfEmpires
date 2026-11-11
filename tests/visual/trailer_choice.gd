extends SceneTree
## Trailer capture (marketing): the real DialogueBox over a 640x360 world frame (shown 3x, nearest) playing the annex
## counter decision c4d — the registrar's line types out, the two choices appear, the focus moves between them.
## Nothing is chosen, nothing is saved (no Story, no saves, no profile, no settings: Settings.values in memory only).
## Record it with Godot's movie writer:
##   godot --path . --write-movie C:/abs/choice.avi --fixed-fps 30 --quit-after 200 \
##         --script res://tests/visual/trailer_choice.gd -- --bg=C:/abs/frame_640x360.png --lang=en

const Kit := preload("res://scripts/ui/ui_kit.gd")
const DLG := preload("res://scenes/ui/DialogueBox.tscn")

var _dlg: Control


func _initialize() -> void:
	var bg_path := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--bg="):
			bg_path = a.substr(5)
	root.size = Vector2i(1920, 1080)
	var s = Kit.svc("Settings")
	if s != null and "values" in s:
		s.values = s.DEFAULTS.duplicate(true)
	var ui := Control.new()
	ui.size = Vector2(1920, 1080)
	ui.theme = Kit.theme()
	root.add_child(ui)
	var back := TextureRect.new()
	back.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	back.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	back.stretch_mode = TextureRect.STRETCH_SCALE
	back.size = Vector2(1920, 1080)
	if bg_path != "" and FileAccess.file_exists(bg_path):
		back.texture = ImageTexture.create_from_image(Image.load_from_file(bg_path))
	ui.add_child(back)
	_dlg = DLG.instantiate()
	ui.add_child(_dlg)
	_run.call_deferred()


func _wait(t: float) -> void:
	await create_timer(t, true).timeout


func _focus(i: int) -> void:
	var box = _dlg.get("_choices_box")
	if box != null and (box as Node).get_child_count() > i:
		((box as Node).get_child(i) as Control).grab_focus()


func _run() -> void:
	await _wait(0.2)
	_dlg.show_line("registrar", Kit.t("dlg.c4.cnt_09"), "neutral")
	_dlg.show_choices([{"id": "name_marta", "text": "choice.c4d.name_marta"},
		{"id": "protect_marta", "text": "choice.c4d.protect_marta"}])
	await _wait(3.6)
	_dlg.skip_typing()
	await _wait(0.9)
	_focus(1)
	await _wait(0.8)
	_focus(0)
	await _wait(0.8)
	_focus(1)
	await _wait(3.0)
	quit(0)
