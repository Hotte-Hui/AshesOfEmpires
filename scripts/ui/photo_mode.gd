extends "res://scripts/ui/ui_modal.gd"
## PhotoMode (scenes/ui/PhotoMode.tscn; UIRoot property `photo`, opened by Game through UIRoot.open_photo() on the
## "photo_mode" action = P / pad R3, only in free play). Documented in documentation/asset_manifest_parts/
## photo_mode.md. While open the world is paused (modal stack), the HUD and every other UI panel are hidden and:
##  * free camera: WASD / arrows / left stick / mouse drag pan Game.camera (cinematic = true, set_top_left, always
##    inside the level's camera bounds); Shift / LB = faster. Zoom 1x/2x/3x (Z, + / -, mouse wheel, RB) scales the
##    finished Display image by an integer factor with nearest filtering on whole screen pixels, so every texel
##    stays a crisp block (the world viewport, its grade and dither are untouched). 3D / low-res levels: the
##    camera is never moved (the hall drives its own lens); there pan moves only the zoomed crop.
##  * figure on/off (C), filters through the shared grade material (F: Normal = level grade, Archiv-Sepia,
##    Schwarzweiss, Kalt, Warm, Nacht), film grain on/off (G), vignette strength (V), frames (R: none, 2.39:1
##    letterbox, 4:3, square, paper print with deckle edge and album corners). Shift + key = previous value.
##    Pad: d-pad up/down picks a row, left/right changes it; X filter, Y frame, RB zoom, Back hides the UI.
##  * photo: Enter / Space / F12 / pad A. The photo UI is hidden for the captured frame (the frame overlay is part
##    of the picture), the composed window image (1920x1080 at 1080p, else the window size) is saved as
##    user://photos/ashes_YYYYMMDD_HHMMSS.png and into <Pictures>/Ashes of Empires/, then a gentle shutter flash
##    (dimmer with reduced motion), a shutter sound when the audio set has one (none yet), and a toast.
##  * H / pad Back hides the panel and the help strip; Esc / B / P / R3 / Start closes. On close the camera
##    (position, spring velocity, cinematic flag), the Display transform, the grade, the player's visibility and
##    every hidden UI node are restored exactly.
## API: open() -> bool, can_open(), close(), take_photo(), pan_by(world_px), set_filter(id), set_frame(id),
##      set_zoom(z), set_figure_visible(on), change(row, dir); signals closed (modal base), photo_taken(paths).
## Static helpers (unit tested): photo_file_name(), clamp_center(), filter_params(), compose_grade(),
##      read_grade(), write_grade().

signal photo_taken(paths: Array)

const SCREEN := Vector2(1920, 1080)
const VIEW := Vector2(640, 360)           ## world window (WorldCamera.VIEW)
const SCALE := 3.0                        ## UI canvas units per world px (PixelView.SCALE)
const MARGIN := 1.0                       ## world px overscan of the Display (PixelView.MARGIN)
const PAN_SPEED := 150.0                  ## world px/s at zoom 1
const PAN_FAST := 2.6
const MAX_ZOOM := 3
const USER_DIR := "user://photos"
const EXPORT_FOLDER := "Ashes of Empires"
const FILTERS := ["normal", "sepia", "bw", "cold", "warm", "night"]
const FRAMES := ["none", "scope", "academy", "square", "print"]
const VIGNETTES := [0.0, 0.15, 0.3, 0.45, 0.65]
const VIG_NAMES := ["off", "light", "medium", "strong", "max"]
const GRAIN_ON := 0.035
const GRADE_KEYS := ["lift", "gamma", "gain", "tint", "saturation", "vignette", "grain", "palette_strength"]
const ROWS := ["filter", "frame", "vignette", "grain", "figure", "zoom"]
const ROW_KEYS := {"filter": KEY_F, "frame": KEY_R, "vignette": KEY_V, "grain": KEY_G, "figure": KEY_C, "zoom": KEY_Z}
const PRINT_TEX := "res://assets/ui/photo/frame_print.png"
const ICON_TEX := "res://assets/ui/photo/icon_camera.png"
const SHUTTER_SOUNDS := ["ui_shutter", "camera_shutter", "shutter"]
## Letterbox / pillar bars on the 1920x1080 canvas, multiples of 3 (one world texel at 1080p).
const BARS := {"scope": [Rect2(0, 0, 1920, 138), Rect2(0, 942, 1920, 138)],
	"academy": [Rect2(0, 0, 240, 1080), Rect2(1680, 0, 240, 1080)],
	"square": [Rect2(0, 0, 420, 1080), Rect2(1500, 0, 420, 1080)]}

## Tests / harness: write the "Pictures" copy here instead of <Pictures>/Ashes of Empires.
var export_dir_override := ""
var filter_id := "normal"
var frame_id := "none"
var vignette_index := -1                  ## -1 = the scene's own vignette
var grain_mode := -1                      ## -1 = scene grain, 0 = off, 1 = on
var figure_visible := true
var zoom := 1
var center := Vector2.ZERO                ## world px shown at the screen centre
var last_paths: Array = []

var _base: Dictionary = {}                # level grade, snapshot taken on open
var _mat: ShaderMaterial = null
var _cam = null
var _pan_camera := false
var _saved_cam: Dictionary = {}
var _saved_display: Dictionary = {}
var _saved_player: Dictionary = {}
var _hidden: Array = []
var _capturing := false
var _dragging := false
var _sel := 0
var _ui_hidden := false
var _pad_hints := false

var _frame_root: Control
var _bars: Array = []
var _print: TextureRect
var _ui: Control
var _panel: PanelContainer
var _rows: Dictionary = {}
var _help_box: VBoxContainer
var _help: Control = null
var _toast: PanelContainer
var _toast_label: Label
var _toast_tween: Tween
var _hint: Label
var _hint_tween: Tween
var _flash: ColorRect


func _ready() -> void:
	pauses_game = true
	closes_on_cancel = true
	_frame_root = _layer()
	add_child(_frame_root)
	for i in 2:
		var b := ColorRect.new()
		b.color = Color.BLACK
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.visible = false
		_frame_root.add_child(b)
		_bars.append(b)
	_print = TextureRect.new()
	_print.texture = Kit.tex(PRINT_TEX)
	_print.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_print.stretch_mode = TextureRect.STRETCH_SCALE
	_print.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_print.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_print.position = Vector2.ZERO
	_print.size = SCREEN
	_print.visible = false
	_frame_root.add_child(_print)
	_ui = _layer()
	add_child(_ui)
	_build_panel()
	_help_box = Kit.vbox(10)
	_help_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_help_box.offset_left = -900
	_help_box.offset_right = 900
	_help_box.offset_top = -170
	_help_box.offset_bottom = -26
	_help_box.alignment = BoxContainer.ALIGNMENT_END
	_help_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_help_box)
	_toast = Kit.panel("PromptPanel")
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_toast_label = Kit.label("", "BodyLabel")
	_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.scalable(_toast_label, 22)
	_toast.add_child(_toast_label)
	_toast.visible = false
	_help_box.add_child(_toast)
	_hint = Kit.label("", "HintLabel")
	Kit.scalable(_hint, 20)
	_hint.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_hint.offset_left = -700
	_hint.offset_right = -36
	_hint.offset_top = -64
	_hint.offset_bottom = -28
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_hint.visible = false
	add_child(_hint)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(_flash)
	_flash.visible = false
	add_child(_flash)


func _layer() -> Control:
	var c := Control.new()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	Kit.full_rect(c)
	return c


func _build_panel() -> void:
	_panel = Kit.panel("")
	_panel.position = Vector2(36, 36)
	_ui.add_child(_panel)
	var m := Kit.margin(20, 14, 20, 16)
	_panel.add_child(m)
	var v := Kit.vbox(8)
	m.add_child(v)
	var head := Kit.hbox(14)
	var icon := TextureRect.new()
	icon.texture = Kit.tex(ICON_TEX)
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	icon.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(icon)
	var title := Kit.label(Kit.t("ui.photo.title").to_upper(), "KickerLabel")
	Kit.scalable(title, 24)
	title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(title)
	v.add_child(head)
	v.add_child(Kit.rule(Kit.C_COPPER, 2))
	for id in ROWS:
		v.add_child(_build_row(id))


func _build_row(id: String) -> Control:
	var row := Kit.hbox(10)
	var mark := ColorRect.new()
	mark.color = Kit.C_COPPER_L
	mark.custom_minimum_size = Vector2(5, 30)
	mark.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mark.modulate.a = 0.0
	row.add_child(mark)
	var chip := Kit.panel("KeyChipPanel")
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip.custom_minimum_size.x = 38
	var kl := Kit.label(hotkey_name(ROW_KEYS[id]), "KeyHintLabel")
	kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	chip.add_child(kl)
	row.add_child(chip)
	var nm := Kit.label(Kit.t("ui.photo.row." + id), "BodyLabel")
	Kit.scalable(nm, 22)
	nm.custom_minimum_size.x = 130
	nm.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(nm)
	var prev := Kit.button("<", "SmallButton", 40)
	prev.focus_mode = Control.FOCUS_NONE
	prev.pressed.connect(change.bind(id, -1))
	row.add_child(prev)
	var val := Kit.label("", "BodyLabel")
	Kit.scalable(val, 22)
	val.custom_minimum_size.x = 236
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	val.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(val)
	var nxt := Kit.button(">", "SmallButton", 40)
	nxt.focus_mode = Control.FOCUS_NONE
	nxt.pressed.connect(change.bind(id, 1))
	row.add_child(nxt)
	_rows[id] = {"value": val, "chip": chip, "mark": mark}
	return row


# ================================================================ open / close
## Opens the photo mode when the game is in free play (a level, no cinematic, no dialogue or other panel).
func open() -> bool:
	if not can_open():
		return false
	open_modal()
	return is_open


func can_open() -> bool:
	if is_open:
		return false
	var g := _game()
	if g == null:
		return false
	var lvl = g.get("level")
	if lvl == null or not is_instance_valid(lvl):
		return false
	if g.get("in_cinematic") == true or g.get("busy") == true or g.get("input_locked") == true:
		return false
	if ui_root != null:
		if ui_root.get("cinematic_mode") == true:
			return false
		if ui_root.has_method("is_modal_open") and ui_root.is_modal_open():
			return false
	return true


func _on_open() -> void:
	filter_id = "normal"
	frame_id = "none"
	vignette_index = -1
	grain_mode = -1
	zoom = 1
	_sel = 0
	_ui_hidden = false
	_dragging = false
	_capturing = false
	var g := _game()
	var gr = g.get("grade") if g != null else null
	_mat = gr.material as ShaderMaterial if gr is CanvasItem and gr.material is ShaderMaterial else null
	_base = read_grade(_mat) if _mat != null else {}
	_take_camera()
	_take_display()
	var p = g.get("player") if g != null else null
	_saved_player = {}
	figure_visible = true
	if p != null and is_instance_valid(p) and "visible" in p:
		_saved_player = {"node": p, "visible": bool(p.visible)}
		figure_visible = bool(p.visible)
	_hide_other_ui()
	set_frame("none")
	_ui.visible = true
	_hint.visible = false
	_toast.visible = false
	_flash.visible = false
	_pad_hints = Kit.last_input_pad
	_rebuild_help()
	_refresh_rows()


func _on_close() -> void:
	_dragging = false
	for tw in [_toast_tween, _hint_tween]:
		if tw != null and tw.is_valid():
			tw.kill()
	zoom = 1
	var d = _display()
	if d != null and not _saved_display.is_empty():
		d.scale = _saved_display["scale"]
		d.position = _saved_display["position"]
	if _cam != null and is_instance_valid(_cam) and not _saved_cam.is_empty():
		if _pan_camera:
			_cam.set_top_left(_saved_cam["pos"], false)
		_cam.vel = _saved_cam["vel"]
		_cam.cinematic = _saved_cam["cinematic"]
	if _mat != null:
		write_grade(_mat, _base)
	else:
		var g := _game()
		if g != null and g.has_method("_apply_grade") and g.get("level") != null:
			g._apply_grade(g.get("level"))
	if not _saved_player.is_empty() and is_instance_valid(_saved_player["node"]):
		_saved_player["node"].visible = _saved_player["visible"]
	for n in _hidden:
		if is_instance_valid(n):
			n.visible = true
	_hidden.clear()
	set_frame("none")
	_cam = null
	_saved_cam = {}
	_saved_display = {}
	_saved_player = {}


func _take_camera() -> void:
	var g := _game()
	_cam = g.get("camera") if g != null else null
	_saved_cam = {}
	_pan_camera = false
	if _cam == null or not is_instance_valid(_cam) or not ("pos" in _cam):
		_cam = null
		center = VIEW * 0.5
		return
	_saved_cam = {"pos": _cam.pos, "vel": _cam.vel, "cinematic": _cam.cinematic}
	_pan_camera = not _is_lowres()
	if _pan_camera:
		_cam.cinematic = true
		center = clamp_center(_cam.drawn + VIEW * 0.5, _region(), VIEW, 1.0)
	else:
		center = VIEW * 0.5


func _take_display() -> void:
	_saved_display = {}
	var d = _display()
	if d == null:
		return
	var fr = _view().get("_fraction")
	_saved_display = {"position": d.position, "scale": d.scale, "fraction": fr if fr is Vector2 else Vector2.ZERO}


## Hides the HUD, toasts, subtitles, letterbox and every other UIRoot panel plus Game.overlay (restored on close).
func _hide_other_ui() -> void:
	_hidden.clear()
	if ui_root != null:
		for c in ui_root.get_children():
			if c != self and c is CanvasItem and (c as CanvasItem).visible:
				(c as CanvasItem).visible = false
				_hidden.append(c)
	var g := _game()
	var ov = g.get("overlay") if g != null else null
	if ov is CanvasLayer and (ov as CanvasLayer).visible:
		(ov as CanvasLayer).visible = false
		_hidden.append(ov)


# ================================================================ settings
func change(id: String, dir: int) -> void:
	match id:
		"filter":
			set_filter(FILTERS[wrapi(FILTERS.find(filter_id) + dir, 0, FILTERS.size())])
		"frame":
			set_frame(FRAMES[wrapi(FRAMES.find(frame_id) + dir, 0, FRAMES.size())])
		"vignette":
			vignette_index = _next_vignette(dir)
			_apply_grade_now()
		"grain":
			grain_mode = 0 if grain_on() else 1
			_apply_grade_now()
		"figure":
			set_figure_visible(not figure_visible)
		"zoom":
			set_zoom(wrapi(zoom - 1 + dir, 0, MAX_ZOOM) + 1)
	Kit.ui_sound("move")
	_refresh_rows()


func set_filter(id: String) -> void:
	filter_id = id if id in FILTERS else "normal"
	_apply_grade_now()
	_refresh_rows()


func set_frame(id: String) -> void:
	frame_id = id if id in FRAMES else "none"
	for b in _bars:
		b.visible = false
	var rects: Array = BARS.get(frame_id, [])
	for i in rects.size():
		_bars[i].position = rects[i].position
		_bars[i].size = rects[i].size
		_bars[i].visible = true
	if _print != null:
		_print.visible = frame_id == "print" and _print.texture != null
	_refresh_rows()


func set_figure_visible(on: bool) -> void:
	if _saved_player.is_empty() or not is_instance_valid(_saved_player["node"]):
		figure_visible = true
		return
	figure_visible = on
	_saved_player["node"].visible = on
	_refresh_rows()


func set_zoom(z: int) -> void:
	zoom = clampi(z, 1, MAX_ZOOM)
	center = clamp_center(center, _region(), VIEW, float(zoom))
	_apply_view()
	_refresh_rows()


func grain_on() -> bool:
	if grain_mode >= 0:
		return grain_mode == 1
	return _f(_base.get("grain"), 0.0) > 0.0005


func _next_vignette(dir: int) -> int:
	var n := VIGNETTES.size()
	if vignette_index >= 0:
		return wrapi(vignette_index + dir, 0, n)
	var cur := _f(_base.get("vignette"), 0.22)
	if dir > 0:
		for i in n:
			if VIGNETTES[i] > cur + 0.001:
				return i
		return 0
	for i in range(n - 1, -1, -1):
		if VIGNETTES[i] < cur - 0.001:
			return i
	return n - 1


func _apply_grade_now() -> void:
	if _mat != null:
		write_grade(_mat, compose_grade(_base, filter_id, vignette_index, grain_mode))


# ================================================================ camera / view
## Moves the view by `d` world px (clamped to the level's camera bounds; 3D levels: inside the fixed window).
func pan_by(d: Vector2) -> void:
	var c := clamp_center(center + d, _region(), VIEW, float(zoom))
	if c.is_equal_approx(center):
		return
	center = c
	_apply_view()


func _region() -> Rect2:
	if _pan_camera and _cam != null and is_instance_valid(_cam):
		return _cam.bounds
	return Rect2(Vector2.ZERO, VIEW)


func _apply_view() -> void:
	if _pan_camera and _cam != null and is_instance_valid(_cam):
		_cam.set_top_left(center - VIEW * 0.5)
	_apply_display()


## Integer zoom of the finished image: the Display (nearest) is scaled by `zoom` and placed on whole screen pixels
## so that `center` is in the middle of the screen. zoom 1 = the Display exactly as PixelView placed it.
func _apply_display() -> void:
	var d = _display()
	if d == null or _saved_display.is_empty():
		return
	if zoom <= 1:
		d.scale = _saved_display["scale"]
		d.position = _saved_display["position"]
		return
	var ref: Vector2 = _cam.drawn if (_pan_camera and _cam != null and is_instance_valid(_cam)) else Vector2.ZERO
	var o: Vector2 = center - ref + _saved_display["fraction"] + Vector2.ONE * MARGIN
	var p: Vector2 = SCREEN * 0.5 - o * SCALE * float(zoom)
	var s := _stretch_scale()
	d.scale = Vector2(zoom, zoom)
	d.position = (p * s).round() / s


func _stretch_scale() -> float:
	var w := get_window()
	if w == null or not w.has_method("get_stretch_transform"):
		return 1.0
	var s: float = w.get_stretch_transform().get_scale().x
	return s if s > 0.0 else 1.0


func _is_lowres() -> bool:
	var v = _view()
	return v != null and v.has_method("is_hires") and not v.is_hires()


# ================================================================ photo
## Hides the photo UI for one frame, saves the composed frame (frame overlay included) and gives feedback.
func take_photo() -> void:
	if _capturing or not is_open:
		return
	_capturing = true
	_ui.visible = false
	_hint.visible = false
	_flash.visible = false
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var vp := get_viewport()
	var img: Image = vp.get_texture().get_image() if vp != null else null
	var paths := save_image(img)
	last_paths = paths
	_capturing = false
	if is_open:
		_ui.visible = not _ui_hidden
		_feedback(paths)
	photo_taken.emit(paths)


## Saves `img` under one unused file name into user://photos and the export folder; returns the absolute paths.
func save_image(img: Image) -> Array:
	var out: Array = []
	if img == null or img.is_empty():
		return out
	var dirs: Array = [ProjectSettings.globalize_path(USER_DIR)]
	var ex := export_dir()
	if ex != "":
		dirs.append(ex)
	var dt := Time.get_datetime_dict_from_system()
	var file := photo_file_name(dt)
	for n in range(2, 100):
		var taken := false
		for d in dirs:
			taken = taken or FileAccess.file_exists(str(d).path_join(file))
		if not taken:
			break
		file = photo_file_name(dt, n)
	for d in dirs:
		DirAccess.make_dir_recursive_absolute(str(d))
		var path := str(d).path_join(file)
		if img.save_png(path) == OK:
			out.append(path)
	return out


func export_dir() -> String:
	if export_dir_override != "":
		return export_dir_override
	var pics := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
	return pics.path_join(EXPORT_FOLDER) if pics != "" else ""


func _feedback(paths: Array) -> void:
	if paths.is_empty():
		Kit.ui_sound("fail")
		_show_toast(Kit.t("ui.photo.failed"))
		return
	Kit.ui_sound_first(SHUTTER_SOUNDS)
	var rm := Kit.reduced_motion()
	_flash.visible = true
	_flash.color = Color(1, 1, 1, 0.14 if rm else 0.5)
	var tw := create_tween()
	tw.tween_property(_flash, "color:a", 0.0, 0.14 if rm else 0.32).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func() -> void: _flash.visible = false)
	var last := str(paths[paths.size() - 1])
	_show_toast(Kit.t("ui.photo.saved", {"file": last.get_file()}) + "\n" \
		+ Kit.t("ui.photo.saved_where", {"dir": last.get_base_dir().replace("/", "\\") if OS.get_name() == "Windows" else last.get_base_dir()}))


func _show_toast(text: String) -> void:
	_toast_label.text = text
	_toast.visible = true
	_toast.modulate.a = 1.0
	if _toast_tween != null and _toast_tween.is_valid():
		_toast_tween.kill()
	_toast_tween = create_tween()
	_toast_tween.tween_interval(3.2)
	_toast_tween.tween_property(_toast, "modulate:a", 0.0, 0.4)
	_toast_tween.tween_callback(func() -> void: _toast.visible = false)


func toggle_ui() -> void:
	_ui_hidden = not _ui_hidden
	_ui.visible = not _ui_hidden
	_dragging = false
	if _hint_tween != null and _hint_tween.is_valid():
		_hint_tween.kill()
	_hint.visible = _ui_hidden
	if _ui_hidden:
		var key := Kit.pad_button_name(JOY_BUTTON_BACK) if _pad_hints else hotkey_name(KEY_H)
		_hint.text = Kit.t("ui.photo.show_ui", {"key": key})
		_hint.modulate.a = 1.0
		_hint_tween = create_tween()
		_hint_tween.tween_interval(2.4)
		_hint_tween.tween_property(_hint, "modulate:a", 0.0, 0.6)


# ================================================================ UI state
func _rebuild_help() -> void:
	if _help != null and is_instance_valid(_help):
		_help_box.remove_child(_help)
		_help.queue_free()
	var pairs: Array
	if _pad_hints:
		pairs = [[Kit.t("ui.photo.key.lstick"), Kit.t("ui.photo.hint.move")],
			[Kit.t("ui.photo.key.dpad"), Kit.t("ui.photo.hint.change")],
			[Kit.pad_button_name(JOY_BUTTON_RIGHT_SHOULDER), Kit.t("ui.photo.hint.zoom")],
			[Kit.pad_button_name(JOY_BUTTON_A), Kit.t("ui.photo.hint.shoot")],
			[Kit.pad_button_name(JOY_BUTTON_BACK), Kit.t("ui.photo.hint.hide")],
			[Kit.pad_button_name(JOY_BUTTON_B), Kit.t("ui.hint.close")]]
	else:
		pairs = [["WASD|" + Kit.t("ui.photo.key.mouse"), Kit.t("ui.photo.hint.move")],
			[Kit.key_name(KEY_SHIFT), Kit.t("ui.photo.hint.fast")],
			[hotkey_name(KEY_Z) + "|" + Kit.t("ui.photo.key.wheel"), Kit.t("ui.photo.hint.zoom")],
			[Kit.key_name(KEY_ENTER) + "|F12", Kit.t("ui.photo.hint.shoot")],
			[hotkey_name(KEY_H), Kit.t("ui.photo.hint.hide")],
			[Kit.key_name(KEY_ESCAPE), Kit.t("ui.hint.close")]]
	_help = Kit.controls_row(pairs)
	_help_box.add_child(_help)


func _refresh_rows() -> void:
	if _rows.is_empty():
		return
	_set_val("filter", Kit.t("ui.photo.filter." + filter_id))
	_set_val("frame", Kit.t("ui.photo.frame." + frame_id))
	_set_val("vignette", Kit.t("ui.photo.vignette." + ("scene" if vignette_index < 0 else VIG_NAMES[vignette_index])))
	_set_val("grain", Kit.t("ui.photo.on" if grain_on() else "ui.photo.off"))
	if _saved_player.is_empty():
		_set_val("figure", Kit.t("ui.photo.figure.none"))
	else:
		_set_val("figure", Kit.t("ui.photo.figure.shown" if figure_visible else "ui.photo.figure.hidden"))
	_set_val("zoom", Kit.t("ui.photo.zoom.value", {"z": zoom}))
	for i in ROWS.size():
		var r: Dictionary = _rows[ROWS[i]]
		r["chip"].visible = not _pad_hints
		r["mark"].modulate.a = 1.0 if (_pad_hints and i == _sel) else 0.0


## Hotkeys are matched by their logical key (the letter printed on the keycap: Z is Z on QWERTZ too), so their
## chips show the logical name (Kit.key_name maps physical positions, right for WASD, wrong for mnemonics).
static func hotkey_name(code: int) -> String:
	return OS.get_keycode_string(code)


func _set_val(id: String, text: String) -> void:
	(_rows[id]["value"] as Label).text = text


func _process(delta: float) -> void:
	if not is_open:
		return
	if _pad_hints != Kit.last_input_pad:
		_pad_hints = Kit.last_input_pad
		_rebuild_help()
		_refresh_rows()
	if _capturing:
		return
	var v := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if v != Vector2.ZERO:
		var fast := Input.is_action_pressed("run")
		pan_by(v * PAN_SPEED * (PAN_FAST if fast else 1.0) * delta / float(zoom))
	elif zoom > 1:
		_apply_display()          # keeps the crop if PixelView re-placed the Display (window resize)


# ================================================================ input (UIRoot routes it here first)
func modal_input(event: InputEvent) -> bool:
	if not is_open:
		return false
	if _capturing:
		return true
	if event is InputEventMouseButton:
		return _mouse_button(event as InputEventMouseButton)
	if event is InputEventMouseMotion:
		if _dragging:
			pan_by(-(event as InputEventMouseMotion).relative / (SCALE * float(zoom)))
			return true
		return false
	if event.is_action_pressed("photo_mode"):
		Kit.ui_sound("back")
		close()
		return true
	if event is InputEventKey:
		if event.is_action("cancel"):
			return false                      # Esc / Backspace -> UIRoot -> handle_cancel() -> close
		var k := event as InputEventKey
		if k.pressed and not k.echo:
			_key(k)
		return true                           # every other key belongs to the photo mode
	if event is InputEventJoypadButton:
		var b := event as InputEventJoypadButton
		if b.button_index == JOY_BUTTON_B:
			return false
		if b.pressed:
			_pad_button(b.button_index)
		return true
	return event is InputEventJoypadMotion    # sticks are polled in _process


func _key(k: InputEventKey) -> void:
	for a in ["move_left", "move_right", "move_up", "move_down", "run"]:
		if k.is_action(a):
			return
	var code := int(k.keycode) if k.keycode != KEY_NONE else int(k.physical_keycode)
	var dir := -1 if k.shift_pressed else 1
	match code:
		KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_F12:
			take_photo()
		KEY_F:
			change("filter", dir)
		KEY_R:
			change("frame", dir)
		KEY_V:
			change("vignette", dir)
		KEY_G:
			change("grain", 1)
		KEY_C:
			change("figure", 1)
		KEY_Z:
			change("zoom", dir)
		KEY_PLUS, KEY_EQUAL, KEY_KP_ADD:
			set_zoom(zoom + 1)
		KEY_MINUS, KEY_KP_SUBTRACT:
			set_zoom(zoom - 1)
		KEY_H:
			toggle_ui()


func _pad_button(b: int) -> void:
	match b:
		JOY_BUTTON_A:
			take_photo()
		JOY_BUTTON_X:
			change("filter", 1)
		JOY_BUTTON_Y:
			change("frame", 1)
		JOY_BUTTON_RIGHT_SHOULDER:
			change("zoom", 1)
		JOY_BUTTON_BACK:
			toggle_ui()
		JOY_BUTTON_START:
			Kit.ui_sound("back")
			close()
		JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN:
			_sel = wrapi(_sel + (1 if b == JOY_BUTTON_DPAD_DOWN else -1), 0, ROWS.size())
			Kit.ui_sound("move")
			_refresh_rows()
		JOY_BUTTON_DPAD_LEFT:
			change(ROWS[_sel], -1)
		JOY_BUTTON_DPAD_RIGHT:
			change(ROWS[_sel], 1)


func _mouse_button(e: InputEventMouseButton) -> bool:
	if e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_UP:
		set_zoom(zoom + 1)
		return true
	if e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		set_zoom(zoom - 1)
		return true
	if e.button_index != MOUSE_BUTTON_LEFT:
		return false
	if e.pressed:
		if _ui.visible and _panel.get_global_rect().has_point(e.position):
			return false                      # the panel's buttons
		_dragging = true
		return true
	if _dragging:
		_dragging = false
		return true
	return false


# ================================================================ services
func _game() -> Object:
	return Kit.svc("Game")


func _view() -> Object:
	var g := _game()
	var v = g.get("view") if g != null else null
	return v if v != null and is_instance_valid(v) else null


func _display() -> Object:
	var v := _view()
	var d = v.get("display") if v != null else null
	return d if d is Control else null


# ================================================================ static helpers (unit tested)
## ashes_YYYYMMDD_HHMMSS.png (n > 1: _n before the extension, for several photos in one second).
static func photo_file_name(dt: Dictionary, n := 1) -> String:
	var s := "ashes_%04d%02d%02d_%02d%02d%02d" % [int(dt.get("year", 0)), int(dt.get("month", 0)),
		int(dt.get("day", 0)), int(dt.get("hour", 0)), int(dt.get("minute", 0)), int(dt.get("second", 0))]
	if n > 1:
		s += "_%d" % n
	return s + ".png"


## Screen-centre point (world px) clamped so the visible window (view / zoom) stays inside `region`; a region
## smaller than the window is centred.
static func clamp_center(c: Vector2, region: Rect2, view: Vector2, z: float) -> Vector2:
	var h := view / (2.0 * maxf(z, 1.0))
	var out := c
	for axis in 2:
		var lo: float = region.position[axis] + h[axis]
		var hi: float = region.end[axis] - h[axis]
		out[axis] = (lo + hi) * 0.5 if hi < lo else clampf(c[axis], lo, hi)
	return out


## Grade parameters of a filter on top of the level grade `base` (keys GRADE_KEYS; null = shader default).
static func filter_params(base: Dictionary, id: String) -> Dictionary:
	var p := base.duplicate(true)
	var lift := _v3(base.get("lift"), Vector3.ZERO)
	var gain := _v3(base.get("gain"), Vector3.ONE)
	var sat := _f(base.get("saturation"), 1.0)
	match id:
		"sepia":       # archive print: monochrome, warm brown-cream, lifted blacks
			p["saturation"] = 0.0
			p["tint"] = Vector3(1.12, 0.96, 0.74)
			p["lift"] = lift + Vector3(0.035, 0.022, 0.004)
			p["gamma"] = Vector3(1.04, 1.04, 1.04)
		"bw":          # neutral black and white, a little more contrast
			p["saturation"] = 0.0
			p["tint"] = Vector3.ONE
			p["gain"] = gain * 1.08
			p["lift"] = lift - Vector3(0.02, 0.02, 0.02)
		"cold":
			p["saturation"] = sat * 0.78
			p["tint"] = Vector3(0.88, 0.97, 1.12)
			p["lift"] = lift + Vector3(0.0, 0.008, 0.026)
		"warm":
			p["saturation"] = sat * 1.08
			p["tint"] = Vector3(1.12, 1.0, 0.84)
			p["lift"] = lift + Vector3(0.022, 0.01, 0.0)
		"night":       # day-for-night: darker, desaturated, blue
			p["saturation"] = sat * 0.5
			p["gain"] = gain * Vector3(0.52, 0.6, 0.82)
			p["gamma"] = Vector3(0.9, 0.9, 0.9)
			p["tint"] = Vector3(0.84, 0.94, 1.16)
			p["lift"] = lift + Vector3(0.0, 0.004, 0.018)
	return p


## Filter + vignette step (-1 = scene) + grain mode (-1 scene, 0 off, 1 on).
static func compose_grade(base: Dictionary, id: String, vig_index := -1, grain := -1) -> Dictionary:
	var p := filter_params(base, id)
	if vig_index >= 0 and vig_index < VIGNETTES.size():
		p["vignette"] = VIGNETTES[vig_index]
	if grain == 0:
		p["grain"] = 0.0
	elif grain == 1:
		p["grain"] = maxf(_f(base.get("grain"), 0.0), GRAIN_ON)
	return p


static func read_grade(mat: ShaderMaterial) -> Dictionary:
	var out := {}
	if mat == null:
		return out
	for k in GRADE_KEYS:
		out[k] = mat.get_shader_parameter(k)
	return out


## null values remove the override (shader default) -> restoring a snapshot is exact.
static func write_grade(mat: ShaderMaterial, p: Dictionary) -> void:
	if mat == null:
		return
	for k in p:
		mat.set_shader_parameter(k, p[k])


static func _v3(v, d: Vector3) -> Vector3:
	return v if v is Vector3 else d


static func _f(v, d: float) -> float:
	return float(v) if (v is float or v is int) else d
