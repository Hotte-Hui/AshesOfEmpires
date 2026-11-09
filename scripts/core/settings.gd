extends Node
## Player options + input map (rebindable). Persisted in user://settings.cfg.
## "language" (TECHNICAL_ARCHITECTURE §12.14): the first launch picks English unless the OS speaks German and keeps that
## choice in the file; automated runs always play German and `-- --lang=en` forces English for checks — both only for
## that run, never written (forced_language). Changing it switches Loc live (apply).
signal changed(key: String, value)

const LocScript := preload("res://scripts/story/loc.gd")
const PATH := "user://settings.cfg"
const LANG_ARG := "--lang="
const DEFAULTS := {
	"fullscreen": true, "vsync": true,
	"master_volume": 0.9, "music_volume": 0.75, "ambience_volume": 0.85, "sfx_volume": 0.9, "ui_volume": 0.8,
	"text_scale": 1.0,            # 1.0 / 1.25 / 1.5
	"subtitles": true, "dialogue_speed": 1.0,   # 0 = instant
	"high_contrast": false, "reduced_motion": false,
	"pixel_post": 1.0,            # 0..1 strength of palette snap / grain
	"puzzle_hints": 1,            # 0 off, 1 after 2 fails (default), 2 immediate
	"historical_symbols": true,   # real regime insignia (swastika, hammer & sickle) in a critical, historical-
	                              # artistic context (StGB §86 Abs. 4); off = fictional emblems (see Symbols.pick)
	"demo_notice_seen": false,    # §12.13: the demo letter was confirmed once (main menu shows it on first opening)
	"language": "de",             # §12.14: "de" | "en" (Loc.LANGUAGES); a file without it gets default_language()
}
## action -> default keys (physical keycodes) + joypad buttons
const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
	"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
	"run": [KEY_SHIFT], "interact": [KEY_E, KEY_SPACE, KEY_ENTER],
	"cancel": [KEY_ESCAPE, KEY_BACKSPACE], "journal": [KEY_J, KEY_TAB],
	"pause": [KEY_ESCAPE], "skip": [KEY_ESCAPE], "advance": [KEY_SPACE, KEY_ENTER, KEY_E],
	"photo_mode": [KEY_P],
}
const PAD := {
	"interact": [JOY_BUTTON_A], "advance": [JOY_BUTTON_A], "cancel": [JOY_BUTTON_B],
	"journal": [JOY_BUTTON_BACK], "pause": [JOY_BUTTON_START], "skip": [JOY_BUTTON_Y],
	"run": [JOY_BUTTON_LEFT_SHOULDER], "photo_mode": [JOY_BUTTON_RIGHT_STICK],
}

var values: Dictionary = DEFAULTS.duplicate(true)
## The settings file; tests point a fresh instance at a temporary file (never the player's settings.cfg).
var path := PATH
var _runtime_overrides: Dictionary = {}   # forced for this run only (CLI), never written to disk
var _persisted: Dictionary = {}           # on-disk values of overridden keys
## true when load_settings() found no language in the file and picked one from the OS locale (first launch)
var language_picked := false

func _ready() -> void:
	_build_input_map()
	load_settings()
	apply_run_overrides(OS.get_cmdline_user_args(), OS.get_cmdline_args(), DisplayServer.get_name())
	apply_all()

## The values this run forces (never persisted) — call after load_settings():
## * `-- --symbols=0|1` forces the historical-insignia setting for this run only (lets several tools capture both
##   variants without touching the player's settings file);
## * the language of an automated run or of `--lang=xx` (forced_language). A player's first launch instead writes
##   the language picked from the OS locale (only that key).
func apply_run_overrides(user_args: PackedStringArray, engine_args: PackedStringArray, display: String) -> void:
	for a in user_args:
		if a.begins_with("--symbols="):
			_runtime_overrides["historical_symbols"] = a.get_slice("=", 1) != "0"
	var forced := forced_language(user_args, engine_args, display)
	if forced != "":
		_runtime_overrides["language"] = forced
	for k in _runtime_overrides:
		if not (k == "language" and language_picked):   # an automated run never writes a first-launch pick
			_persisted[k] = values.get(k, DEFAULTS.get(k))
		values[k] = _runtime_overrides[k]
	if language_picked and not _runtime_overrides.has("language"):
		_write_key("language")   # a player's first launch: the picked language stays from now on

## First launch: English unless the OS locale is German.
static func default_language(os_language: String) -> String:
	return "de" if os_language.to_lower().begins_with("de") else "en"

## The language forced for this run ("" = the player's setting): `-- --lang=xx` (checks; an unknown code = German);
## German for every other automated run — any other user argument (drivers, tools, --splash-shots), a `--script`
## main loop, the headless display or a directly started scene (visual harnesses).
static func forced_language(user_args: PackedStringArray, engine_args: PackedStringArray, display: String) -> String:
	for a in user_args:
		if a.begins_with(LANG_ARG):
			var l := a.substr(LANG_ARG.length()).strip_edges().to_lower()
			return l if LocScript.LANGUAGES.has(l) else LocScript.SOURCE
	if display == "headless" or not user_args.is_empty():
		return LocScript.SOURCE
	for a in engine_args:
		if a in ["--script", "-s", "--headless"] or a.get_extension() in ["tscn", "scn"]:
			return LocScript.SOURCE
	return ""

func _build_input_map() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.25)
		InputMap.action_erase_events(action)
		for k in ACTIONS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)
		for b in PAD.get(action, []):
			var jb := InputEventJoypadButton.new()
			jb.button_index = b
			InputMap.action_add_event(action, jb)
	# Pad A presses the focused button in every menu: Godot's built-in ui_accept has no pad button (Enter, Kp Enter,
	# Space only). Modals that also read "interact"/"advance" (pad A too) treat both as one press.
	var has_a := false
	for e in InputMap.action_get_events("ui_accept"):
		if e is InputEventJoypadButton and (e as InputEventJoypadButton).button_index == JOY_BUTTON_A:
			has_a = true
	if not has_a:
		var ja := InputEventJoypadButton.new()
		ja.button_index = JOY_BUTTON_A
		InputMap.action_add_event("ui_accept", ja)
	var axes := {"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0],
		"move_up": [JOY_AXIS_LEFT_Y, -1.0], "move_down": [JOY_AXIS_LEFT_Y, 1.0]}
	for action in axes:
		var jm := InputEventJoypadMotion.new()
		jm.axis = axes[action][0]
		jm.axis_value = axes[action][1]
		InputMap.action_add_event(action, jm)

func rebind(action: String, keycode: Key) -> void:
	for ev in InputMap.action_get_events(action):
		if ev is InputEventKey:
			InputMap.action_erase_event(action, ev)
			break
	var e := InputEventKey.new()
	e.physical_keycode = keycode
	InputMap.action_add_event(action, e)
	values["bind_" + action] = int(keycode)
	save_settings()

func get_value(key: String):
	return values.get(key, DEFAULTS.get(key))

func set_value(key: String, value) -> void:
	values[key] = value
	apply(key)
	save_settings()
	changed.emit(key, value)

func apply_all() -> void:
	for k in values:
		apply(k)

func apply(key: String) -> void:
	match key:
		"fullscreen":
			if DisplayServer.get_name() != "headless":
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if values[key] else DisplayServer.WINDOW_MODE_WINDOWED)
		"vsync":
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if values[key] else DisplayServer.VSYNC_DISABLED)
		"language":
			# only the autoload drives the live language (test instances never switch it); at boot Loc reads it itself
			if is_inside_tree() and get_tree().root.get_node_or_null("Settings") == self:
				var loc := get_tree().root.get_node_or_null("Loc")
				if loc != null and loc.has_method("set_language"):
					loc.set_language(str(values[key]))
		_:
			if key.ends_with("_volume"):
				var short := key.trim_suffix("_volume")
				var bus: String = {"master": "Master", "music": "Music", "ambience": "Ambience", "sfx": "SFX", "ui": "UI"}.get(short, short.capitalize())
				var idx := AudioServer.get_bus_index(bus)
				if idx >= 0:
					AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(0.0001, float(values[key]))))
			elif key.begins_with("bind_"):
				pass

func save_settings() -> void:
	var cfg := ConfigFile.new()
	for k in values:
		# a CLI-forced value (e.g. --symbols=0, --lang=en, German in a driver run) is never persisted; the player's own
		# value stays on disk (none yet: the key is left out)
		if _runtime_overrides.has(k):
			if _persisted.has(k):
				cfg.set_value("settings", k, _persisted[k])
			continue
		cfg.set_value("settings", k, values[k])
	cfg.save(path)

## Writes one key into the file and keeps everything else in it as it is.
func _write_key(key: String) -> void:
	var cfg := ConfigFile.new()
	cfg.load(path)
	cfg.set_value("settings", key, values[key])
	cfg.save(path)

func load_settings() -> void:
	var cfg := ConfigFile.new()
	var loaded := cfg.load(path) == OK
	language_picked = not (loaded and cfg.has_section_key("settings", "language")
		and LocScript.LANGUAGES.has(str(cfg.get_value("settings", "language"))))
	if language_picked:
		values["language"] = default_language(OS.get_locale_language())
	if not loaded:
		return
	for k in cfg.get_section_keys("settings"):
		if k == "language" and language_picked:
			continue
		values[k] = cfg.get_value("settings", k)
	for k in values.keys():
		if str(k).begins_with("bind_"):
			var action := str(k).trim_prefix("bind_")
			if InputMap.has_action(action):
				rebind(action, values[k])
