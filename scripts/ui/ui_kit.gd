extends RefCounted
## Shared helpers for every UI scene (no class_name on purpose: preload it as `const Kit := preload(...)`).
## * palette + font resources of the UI style (documentation/ART_DIRECTION.md, UI brief)
## * safe access to the autoload services (Loc, Settings, Story, Saves, Audio, Game) with optional overrides
##   so tests/visual/UIPreview can inject mock data; every call is guarded with has_method
## * canonical data lookups (data/v3/*.json), key/button names, live text scaling, small builders

const THEME_PATH := "res://assets/ui/theme.tres"
const THEME_HC_PATH := "res://assets/ui/theme_hc.tres"
const UI_DIR := "res://assets/ui/"
const DOCS_DIR := "res://assets/ui/documents/"
const CHAR_DIR := "res://assets/characters/"
const SCALE_GROUP := &"aoe_text_scalable"

# ---------------------------------------------------------------- palette (archive / karsk ramps)
const C_NIGHT := Color("04090d")
const C_NIGHT1 := Color("06151d")
const C_NAVY := Color("0b1c24")
const C_NAVY_L := Color("14272b")
const C_WALL := Color("354448")
const C_TEXT := Color("e6dec2")
const C_TEXT_BRIGHT := Color("f5efda")
const C_TEXT_DIM := Color("a3aca2")
const C_COPPER_D := Color("7a3e26")
const C_COPPER := Color("ba775b")
const C_COPPER_L := Color("dca16e")
const C_AMBER := Color("f0c487")
const C_PAPER := Color("e6dec2")
const C_PAPER_M := Color("cec6aa")
const C_PAPER_D := Color("b0aa93")
const C_INK := Color("1a1c2a")
const C_INK_B := Color("2e3248")
const C_INK_DIM := Color("4d4a42")
const C_STAMP := Color("a8382e")
const C_BLUE_INK := Color("2b3c50")
const C_DIM_BG := Color(0.016, 0.035, 0.05, 0.62)

## item id -> document image in assets/ui/documents/ (drawn by the environment artists)
const ITEM_DOCS := {
	"ev_damaged_seal": "karsk_seal", "ev_timetable": "karsk_timetable", "ev_ledger": "karsk_ledger",
	"ev_plan_a": "berlin_plan_a", "ev_plan_b": "berlin_plan_b", "ev_emil_note": "berlin_emil_note",
}
const PROTAGONISTS := ["alexei", "konrad"]

## Mock/override services: {"Story": obj, "Saves": obj, ...}. Empty in the real game.
static var overrides: Dictionary = {}
## true when the last meaningful input came from a joypad (prompts then show pad buttons)
static var last_input_pad := false
static var _json_cache: Dictionary = {}
static var _res_cache: Dictionary = {}


# ================================================================ services
static func tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


static func svc(name: String) -> Object:
	if overrides.has(name):
		return overrides[name]
	var t := tree()
	if t == null or t.root == null:
		return null
	return t.root.get_node_or_null(NodePath(name))


static func call_svc(name: String, method: String, args: Array = [], fallback = null):
	var s := svc(name)
	if s == null or not s.has_method(method):
		return fallback
	return s.callv(method, args)


static func has_svc(name: String, method: String) -> bool:
	var s := svc(name)
	return s != null and s.has_method(method)


static func ok(r) -> bool:
	if r is Dictionary:
		return bool(r.get("ok", false))
	if r is bool:
		return r
	return r != null


static func err_text(r) -> String:
	if r is Dictionary:
		return str(r.get("error", ""))
	return ""


# ================================================================ localisation
static func t(key: String, args: Dictionary = {}) -> String:
	var loc := svc("Loc")
	if loc != null and loc.has_method("t"):
		return str(loc.t(key, args))
	return key.format(args) if not args.is_empty() else key


static func has_key(key: String) -> bool:
	var loc := svc("Loc")
	return loc != null and loc.has_method("has") and bool(loc.has(key))


## A quotation in the marks of the current language (ui.quote: German „…“, English “…”).
static func quoted(s: String) -> String:
	return t("ui.quote", {"text": s}) if has_key("ui.quote") else "„%s“" % s


## A decimal number as the current language writes it (ui.decimal_point: German 23,6 · English 23.6).
static func decimal(v: float, places := 1) -> String:
	var s := ("%." + str(places) + "f") % v
	return s.replace(".", t("ui.decimal_point") if has_key("ui.decimal_point") else ",")


## Text that may already be localised or may be a key.
static func resolve(text_or_key: String) -> String:
	if text_or_key != "" and not text_or_key.contains(" ") and has_key(text_or_key):
		return t(text_or_key)
	return text_or_key


## Speaker names: canonical "char.<id>.name" (narrative locale) first, then the UI fallback table
## "ui.char.<id>.name" in data/locale/de_ui.json, then the capitalised id.
static func char_name(id: String) -> String:
	if id == "":
		return ""
	for k in ["char.%s.name" % id, "ui.char.%s.name" % id]:
		if has_key(k):
			return t(k)
	return id.capitalize()


static func char_role(id: String) -> String:
	for k in ["char.%s.role" % id, "ui.char.%s.role" % id]:
		if has_key(k):
			return t(k)
	return ""


# ================================================================ settings
static func setting(key: String, fallback = null):
	var s := svc("Settings")
	if s != null and s.has_method("get_value"):
		var v = s.get_value(key)
		return fallback if v == null else v
	return fallback


static func set_setting(key: String, value) -> void:
	var s := svc("Settings")
	if s != null and s.has_method("set_value"):
		s.set_value(key, value)


static func reduced_motion() -> bool:
	return bool(setting("reduced_motion", false))


static func text_scale() -> float:
	return clampf(float(setting("text_scale", 1.0)), 1.0, 1.5)


static func high_contrast() -> bool:
	return bool(setting("high_contrast", false))


# ================================================================ resources
static func res(path: String) -> Resource:
	if _res_cache.has(path):
		return _res_cache[path]
	var r: Resource = load(path) if ResourceLoader.exists(path) else null
	_res_cache[path] = r
	return r


static func tex(path: String) -> Texture2D:
	return res(Symbols.pick(path)) as Texture2D   # §12.4: *_hist variant when historical_symbols is on


static func ui_tex(name: String) -> Texture2D:
	return tex(UI_DIR + name)


static func font(name: String) -> Font:
	var f := res("res://assets/fonts/%s.tres" % name) as Font
	return f if f != null else ThemeDB.fallback_font


static func theme(hc := false) -> Theme:
	var th := res(THEME_HC_PATH if hc else THEME_PATH) as Theme
	if th == null and hc:
		th = res(THEME_PATH) as Theme
	return th


## Optional image that may not exist yet (documents/portraits from other departments).
## Uses the imported resource when available, else loads the PNG directly (unimported fresh files).
static func optional_tex(path: String) -> Texture2D:
	path = Symbols.pick(path)   # §12.4
	if _res_cache.has(path):
		return _res_cache[path]
	var tx: Texture2D = null
	if ResourceLoader.exists(path):
		tx = load(path) as Texture2D
	elif FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			tx = ImageTexture.create_from_image(img)
	_res_cache[path] = tx
	return tx


static func clear_cache() -> void:
	_res_cache.clear()
	_json_cache.clear()


# ================================================================ data (data/v3, canonical)
static func json(path: String):
	if _json_cache.has(path):
		return _json_cache[path]
	var d = null
	if FileAccess.file_exists(path):
		d = JSON.parse_string(FileAccess.get_file_as_string(path))
	_json_cache[path] = d
	return d


static func _index(path: String, list_key: String) -> Dictionary:
	var ck := path + "#" + list_key
	if _json_cache.has(ck):
		return _json_cache[ck]
	var out := {}
	var d = json(path)
	if d is Dictionary:
		for e in d.get(list_key, []):
			if e is Dictionary and e.has("id"):
				out[str(e["id"])] = e
	_json_cache[ck] = out
	return out


static func item_def(id: String) -> Dictionary:
	var s := svc("Story")
	if s != null and s.has_method("item_def"):
		var r = s.item_def(id)
		if r is Dictionary and not r.is_empty():
			return r
	return _index("res://data/v3/items.json", "items").get(id, {})


static func item_name(id: String) -> String:
	var d := item_def(id)
	return t(str(d["name_key"])) if d.has("name_key") else id


static func all_items() -> Array:
	var d = json("res://data/v3/items.json")
	return d.get("items", []) if d is Dictionary else []


static func quests() -> Array:
	var d = json("res://data/v3/quests.json")
	return d.get("quests", []) if d is Dictionary else []


## Objective definition plus "_quest" (quest dictionary) or {}.
static func objective_def(oid: String) -> Dictionary:
	for q in quests():
		for o in q.get("objectives", []):
			if str(o.get("id", "")) == oid:
				var d: Dictionary = o.duplicate()
				d["_quest"] = q
				return d
	return {}


static func objective_text(oid: String) -> String:
	var d := objective_def(oid)
	return t(str(d["text_key"])) if d.has("text_key") else oid


static func puzzle_def(pid: String) -> Dictionary:
	return _index("res://data/v3/puzzles.json", "puzzles").get(pid, {})


static func puzzle_for_objective(oid: String) -> Dictionary:
	var o := objective_def(oid)
	if o.has("puzzle_id"):
		return puzzle_def(str(o["puzzle_id"]))
	var p := puzzle_def(oid)   # tolerate being handed the puzzle id directly
	return p


static func scene_def(sid: String) -> Dictionary:
	return _index("res://data/v3/scenes.json", "scenes").get(sid, {})


static func conversation(did: String) -> Dictionary:
	return _index("res://data/v3/dialogue.json", "conversations").get(did, {})


static func quest_for_scene(sid: String) -> Dictionary:
	for q in quests():
		if str(q.get("scene", "")) == sid:
			return q
	return {}


static func doc_for_item(item_id: String) -> String:
	if ITEM_DOCS.has(item_id):
		return str(ITEM_DOCS[item_id])
	var e: Dictionary = doc_index().get(item_id, {})
	return str(e.get("id", ""))


## item_id -> document entry from every assets/ui/documents/*_documents.json (environment artists' metadata:
## {id, file, alt_key, title_key, marks ...}).
static func doc_index() -> Dictionary:
	if _json_cache.has("#docs"):
		return _json_cache["#docs"]
	var out := {}
	var dir := DirAccess.open(DOCS_DIR)
	if dir != null:
		for f in dir.get_files():
			if f.ends_with("_documents.json"):
				var d = json(DOCS_DIR + f)
				if d is Dictionary:
					for e in d.get("documents", []):
						if e is Dictionary:
							if e.has("item_id") and e["item_id"] != null:
								out[str(e["item_id"])] = e
							out["#" + str(e.get("id", ""))] = e
	_json_cache["#docs"] = out
	return out


## Accessible description of a document image (Loc alt_key from the documents metadata), or "".
static func doc_alt_text(item_id: String, doc_id := "") -> String:
	var idx := doc_index()
	var e: Dictionary = idx.get(item_id, idx.get("#" + doc_id, {}))
	var k := str(e.get("alt_key", ""))
	return t(k) if k != "" and has_key(k) else ""


# ================================================================ input names
static func action_key_text(action: String) -> String:
	if last_input_pad:
		var b := _first_pad_button(action)
		if b >= 0:
			return pad_button_name(b)
	var code := 0
	var s := svc("Settings")
	if s != null and "values" in s and s.values is Dictionary and s.values.has("bind_" + action):
		code = int(s.values["bind_" + action])
	if code == 0 and InputMap.has_action(action):
		for ev in InputMap.action_get_events(action):
			if ev is InputEventKey:
				code = int(ev.physical_keycode) if ev.physical_keycode != 0 else int(ev.keycode)
				break
	return key_name(code) if code != 0 else ""


static func _first_pad_button(action: String) -> int:
	if not InputMap.has_action(action):
		return -1
	for ev in InputMap.action_get_events(action):
		if ev is InputEventJoypadButton:
			return int(ev.button_index)
	return -1


static func key_name(code: int) -> String:
	var special := {
		KEY_SPACE: "ui.key.space", KEY_ENTER: "ui.key.enter", KEY_KP_ENTER: "ui.key.enter",
		KEY_ESCAPE: "ui.key.escape", KEY_SHIFT: "ui.key.shift", KEY_TAB: "ui.key.tab",
		KEY_BACKSPACE: "ui.key.backspace", KEY_CTRL: "ui.key.ctrl", KEY_ALT: "ui.key.alt",
		KEY_LEFT: "ui.key.left", KEY_RIGHT: "ui.key.right", KEY_UP: "ui.key.up", KEY_DOWN: "ui.key.down",
		KEY_DELETE: "ui.key.delete", KEY_INSERT: "ui.key.insert", KEY_HOME: "ui.key.home", KEY_END: "ui.key.end",
		KEY_PAGEUP: "ui.key.pageup", KEY_PAGEDOWN: "ui.key.pagedown", KEY_CAPSLOCK: "ui.key.capslock",
	}
	if special.has(code):
		return t(special[code])
	var shown := code
	var ds := DisplayServer.get_name()
	if ds != "headless" and DisplayServer.has_method("keyboard_get_label_from_physical"):
		var lab := int(DisplayServer.keyboard_get_label_from_physical(code))
		if lab != 0:
			shown = lab
	var s := OS.get_keycode_string(shown)
	return s.to_upper().replace("ß", "SS") if s.length() == 1 else s


static func pad_button_name(b: int) -> String:
	match b:
		JOY_BUTTON_A: return "A"
		JOY_BUTTON_B: return "B"
		JOY_BUTTON_X: return "X"
		JOY_BUTTON_Y: return "Y"
		JOY_BUTTON_BACK: return t("ui.key.pad_back")
		JOY_BUTTON_START: return t("ui.key.pad_start")
		JOY_BUTTON_LEFT_SHOULDER: return "LB"
		JOY_BUTTON_RIGHT_SHOULDER: return "RB"
	return "#%d" % b


# ================================================================ text scale (Settings.text_scale)
## Registers a text control whose font size follows the 100/125/150 % setting.
static func scalable(c: Control, base_size: int) -> Control:
	c.set_meta("aoe_base_size", base_size)
	if not c.is_in_group(SCALE_GROUP):
		c.add_to_group(SCALE_GROUP)
	apply_text_scale(c)
	return c


static func apply_text_scale(c: Control) -> void:
	if not c.has_meta("aoe_base_size"):
		return
	var sz := int(round(float(c.get_meta("aoe_base_size")) * text_scale()))
	if c is RichTextLabel:
		for k in ["normal_font_size", "bold_font_size", "italics_font_size", "bold_italics_font_size", "mono_font_size"]:
			c.add_theme_font_size_override(k, sz)
	else:
		c.add_theme_font_size_override("font_size", sz)


static func refresh_text_scale() -> void:
	var tr := tree()
	if tr == null:
		return
	for n in tr.get_nodes_in_group(SCALE_GROUP):
		if n is Control:
			apply_text_scale(n)


# ================================================================ builders
static func label(text: String, variation := "", size := 0, color = null) -> Label:
	var l := Label.new()
	l.text = text
	if variation != "":
		l.theme_type_variation = variation
	if size > 0:
		l.add_theme_font_size_override("font_size", size)
	if color != null:
		l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func wrap_label(text: String, variation := "", size := 0, color = null) -> Label:
	var l := label(text, variation, size, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## Wrapping label that is only as wide as its text (up to max_w). Call after it is in the tree.
static func fit_width(l: Label, max_w: float) -> void:
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var f := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var w := 0.0
	for line in l.text.split("
"):
		w = maxf(w, f.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x)
	l.custom_minimum_size.x = minf(ceilf(w) + 6.0, max_w)


static func vbox(sep := 0) -> VBoxContainer:
	var b := VBoxContainer.new()
	b.add_theme_constant_override("separation", sep)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


static func hbox(sep := 0) -> HBoxContainer:
	var b := HBoxContainer.new()
	b.add_theme_constant_override("separation", sep)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


static func margin(l: int, tp: int, r: int, b: int) -> MarginContainer:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", l)
	m.add_theme_constant_override("margin_top", tp)
	m.add_theme_constant_override("margin_right", r)
	m.add_theme_constant_override("margin_bottom", b)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return m


static func panel(variation := "") -> PanelContainer:
	var p := PanelContainer.new()
	if variation != "":
		p.theme_type_variation = variation
	return p


static func button(text: String, variation := "", min_w := 0) -> Button:
	var b := Button.new()
	b.text = text
	if variation != "":
		b.theme_type_variation = variation
	if min_w > 0:
		b.custom_minimum_size.x = min_w
	b.focus_mode = Control.FOCUS_ALL
	return b


## Pixel sprite already stored at x3 (frames/icons/puzzle). Drawn 1:1, nearest.
static func sprite(path: String) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex(path if path.begins_with("res://") else UI_DIR + path)
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## 1:1 world-pipeline image (portraits, documents, backdrops) scaled by an integer factor.
static func pixel_image(t2d: Texture2D, scale := 3) -> TextureRect:
	var r := TextureRect.new()
	r.texture = t2d
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if t2d != null:
		r.custom_minimum_size = t2d.get_size() * scale
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func rule(color := C_COPPER, thickness := 3, width := 0) -> ColorRect:
	var r := ColorRect.new()
	r.color = color
	r.custom_minimum_size = Vector2(width, thickness)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func full_rect(c: Control) -> Control:
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.offset_left = 0
	c.offset_top = 0
	c.offset_right = 0
	c.offset_bottom = 0
	return c


static func dimmer(alpha := 0.62) -> ColorRect:
	var d := ColorRect.new()
	d.color = Color(C_DIM_BG.r, C_DIM_BG.g, C_DIM_BG.b, alpha)
	full_rect(d)
	d.mouse_filter = Control.MOUSE_FILTER_STOP
	return d


## Short appear animation. Slides only free-standing controls (a Container would fight the tween);
## reduced motion = fade only.
static func appear(c: CanvasItem, t := 0.18, slide := Vector2.ZERO) -> void:
	if c == null or not c.is_inside_tree():
		return
	c.modulate.a = 0.0
	var tw := c.create_tween().set_parallel(true)
	tw.tween_property(c, "modulate:a", 1.0, t * (0.6 if reduced_motion() else 1.0))
	if slide != Vector2.ZERO and not reduced_motion() and c is Control and not (c.get_parent() is Container):
		var cc := c as Control
		var p := cc.position
		cc.position = p + slide
		tw.tween_property(cc, "position", p, t).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Row of input hints: pairs [[keys, action text], ...]; keys separated by "|" become keycap chips
## (same pixel keycap as the interaction prompt), the action is set in italic.
static func controls_row(pairs: Array, align := BoxContainer.ALIGNMENT_CENTER) -> HBoxContainer:
	var row := hbox(34)
	row.alignment = align
	for p in pairs:
		var item := hbox(8)
		for k in str(p[0]).split("|", false):
			var chip := panel("KeyChipPanel")
			chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
			chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			var kl := label(k, "KeyHintLabel")
			kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			kl.custom_minimum_size.x = 12
			chip.add_child(kl)
			item.add_child(chip)
		var tl := label(str(p[1]), "ControlHintLabel")
		tl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		item.add_child(tl)
		row.add_child(item)
	return row


## UI cue name -> sound id of the audio department (assets/audio/sfx; Audio.ui resolves ui_* and variants).
## Game already plays paper_rustle on inspect and puzzle_success after a solved puzzle closes, so the UI
## uses different, smaller cues for those moments.
const UI_SOUNDS := {"confirm": "select", "back": "back", "move": "move", "advance": "move",
	"toast": "page_turn", "card": "card_place", "snap": "card_place", "tick": "type_tick",
	"fail": "puzzle_fail", "success_signal": "metal_clank", "success_plan": "page_turn",
	"save": "stamp_thud", "page": "page_turn", "paper": ""}
## Cues with fallbacks (first sound the audio department provides wins). "discovery" = soft chime for an
## ordinary find; "history" = neutral paper only (real-history cards are never celebrated, §12.3).
const UI_SOUND_CHAINS := {"discovery": ["ui_discovery", "discovery_chime", "ui_chime", "chime", "page_turn"],
	"history": ["ui_archive", "paper_rustle", "page_turn"]}


static func ui_sound(name: String) -> void:
	if UI_SOUND_CHAINS.has(name):
		ui_sound_first(UI_SOUND_CHAINS[name])
		return
	var id: String = UI_SOUNDS.get(name, name)
	if id == "":
		return
	var a := svc("Audio")
	if a != null and a.has_method("ui"):
		a.ui(id)


## Plays the first sound of `ids` that exists (Audio.has_sound); silent when none does.
static func ui_sound_first(ids: Array) -> void:
	var a := svc("Audio")
	if a == null or not a.has_method("ui"):
		return
	for id in ids:
		if not a.has_method("has_sound") or bool(a.has_sound(str(id))):
			a.ui(str(id))
			return


# ================================================================ exploration (Explore autoload, §12)
const EXPLORE_UI_DIR := "res://assets/ui/explore/"
const EXPLORE_KINDS := ["detail", "secret", "easter_egg", "chat"]


static func explore() -> Object:
	return svc("Explore")


## Texture of the exploration UI kit (tools/pixelgen/gen_ui_explore.py), imported or not.
static func ex_tex(rel: String) -> Texture2D:
	return optional_tex(EXPLORE_UI_DIR + rel)


## Pixel sprite of the exploration kit (already stored at x3), drawn 1:1.
static func ex_sprite(rel: String) -> TextureRect:
	var r := TextureRect.new()
	r.texture = ex_tex(rel)
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## 9-patch style of the exploration kit; margins in screen px (x3 art px), content margins l,t,r,b.
static func ex_style(rel: String, m: Array, cm: Array, tile_h := false, tile_v := false) -> StyleBox:
	var t2 := ex_tex(rel)
	if t2 == null:
		var f := StyleBoxFlat.new()
		f.bg_color = C_PAPER
		f.content_margin_left = cm[0]
		f.content_margin_top = cm[1]
		f.content_margin_right = cm[2]
		f.content_margin_bottom = cm[3]
		return f
	var sb := StyleBoxTexture.new()
	sb.texture = t2
	sb.texture_margin_left = m[0]
	sb.texture_margin_top = m[1]
	sb.texture_margin_right = m[2]
	sb.texture_margin_bottom = m[3]
	sb.content_margin_left = cm[0]
	sb.content_margin_top = cm[1]
	sb.content_margin_right = cm[2]
	sb.content_margin_bottom = cm[3]
	if tile_h:
		sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	if tile_v:
		sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	return sb


static func _key_or(key: String, fallback: String) -> String:
	return t(key) if has_key(key) else fallback


## "Beobachtung", "Versteck", "Kurioses", "Gespräch".
static func explore_kind_label(kind: String) -> String:
	return _key_or("ui.explore.kind." + kind, kind.capitalize())


static func explore_kind_icon(kind: String) -> String:
	return "icons/kind_%s.png" % (kind if kind in EXPLORE_KINDS else "detail")


static func explore_area_label(area: String) -> String:
	return _key_or("ui.explore.area." + area, area.capitalize())


## Place of a find for kickers: per-level label ("Verladebahnhof Karsk"), else the area label.
static func explore_place(e: Dictionary) -> String:
	var lvl := str(e.get("level", ""))
	if lvl != "" and has_key("ui.explore.place." + lvl):
		return t("ui.explore.place." + lvl)
	return explore_area_label(str(e.get("area", "")))


static func explore_title(e: Dictionary) -> String:
	var k := str(e.get("title_key", ""))
	return t(k) if k != "" else str(e.get("id", ""))


static func history_side_label(side: String) -> String:
	return _key_or("ui.history.side." + side, side.capitalize())


## {found, total, cards_found, cards_total} from the Explore autoload (zeros when it is missing).
static func explore_progress() -> Dictionary:
	var p = call_svc("Explore", "progress", [], null)
	if p is Dictionary:
		return p
	return {"found": 0, "total": 0, "cards_found": 0, "cards_total": 0}


## Small horizontal progress bar drawn with the exploration kit (on paper). ratio 0..1; the fill snaps
## to the 3 px art grid and keeps its end caps.
static func ex_bar(ratio: float, width := 240, neutral := false) -> Control:
	var bar := Control.new()
	bar.custom_minimum_size = Vector2(width, 15)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var track := ex_style("frames/bar_track.png", [6, 6, 6, 6], [0, 0, 0, 0])
	var fill := ex_style("frames/bar_fill_neutral.png" if neutral else "frames/bar_fill.png", [6, 6, 6, 6], [0, 0, 0, 0])
	var rr := clampf(ratio, 0.0, 1.0)
	bar.draw.connect(func() -> void:
		bar.draw_style_box(track, Rect2(Vector2.ZERO, bar.size))
		var fw := floorf(bar.size.x * rr / 3.0) * 3.0
		if fw >= 12.0:
			bar.draw_style_box(fill, Rect2(Vector2.ZERO, Vector2(fw, bar.size.y))))
	return bar


static func format_time(v) -> String:
	## Accepts unix seconds, ISO strings or dictionaries; returns "04.11.2026 · 18:42" (English: "4 Nov 2026 · 18:42").
	if v is float or v is int:
		if float(v) <= 0.0:
			return ""
		var bias := int(Time.get_time_zone_from_system().get("bias", 0)) * 60
		var d := Time.get_datetime_dict_from_unix_time(int(v) + bias)
		return _date_time(int(d.day), int(d.month), int(d.year), "%02d:%02d" % [d.hour, d.minute])
	if v is String and v != "":
		var s: String = v
		if s.length() >= 16 and s[4] == "-":
			return _date_time(s.substr(8, 2).to_int(), s.substr(5, 2).to_int(), s.substr(0, 4).to_int(), s.substr(11, 5))
		return s
	return ""


## A date with its time as the current language writes it: ui.date_time with the month from ui.date_months
## (German „04.11.2026 · 18:42“, English „04 Nov 2026 · 18:42“).
static func _date_time(day: int, month: int, year: int, hm: String) -> String:
	var months := t("ui.date_months").split(",") if has_key("ui.date_months") else PackedStringArray()
	if not has_key("ui.date_time") or months.size() != 12 or month < 1 or month > 12:
		return "%02d.%02d.%04d · %s" % [day, month, year, hm]
	return t("ui.date_time", {"d": "%02d" % day, "mon": months[month - 1].strip_edges(), "y": "%04d" % year, "time": hm})
