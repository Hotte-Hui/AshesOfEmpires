extends RefCounted
## Boot flow (TECHNICAL_ARCHITECTURE §12.13, round 11): decides ONCE per run whether this is a real player's launch.
## Only then does Main play the boot sequence before handing over to Game (scenes/ui/BootSplash.tscn: black → studio
## card → engine card → title picture) and does the main menu show the demo notice on its first opening
## (scenes/ui/DemoNotice.tscn; flag `demo_notice_seen` in the player's settings, never in a save).
## Every automated run boots exactly as before: any user argument after `--` (drivers and tools: --autoplay,
## --inputplay, --capture, --cinematic=none, --scene, --memory-demo, …), a `--script` main loop, the headless display,
## or a Main that is not the startup scene (visual harnesses instance it as a child). The one exception is
## `--splash-shots=DIR`: the windowed check run of this very sequence (scripts/ui/dev/boot_shots.gd).

const Kit := preload("res://scripts/ui/ui_kit.gd")
const SHOTS_ARG := "--splash-shots="
const NOTICE_KEY := "demo_notice_seen"
const ENGINE_ARGS_OFF := ["--script", "-s", "--headless"]

## Set by decide() (Main, at boot) — true only for a real player's launch.
static var player_launch := false
## The notice was opened in this run already (at most once per session on its own).
static var notice_opened := false


## Pure decision (tests): user args (after `--`), engine args, DisplayServer name, Main is the startup scene.
static func is_player_launch(user_args: PackedStringArray, engine_args: PackedStringArray, display: String,
		main_is_startup_scene: bool) -> bool:
	if display == "headless" or not main_is_startup_scene:
		return false
	for a in engine_args:
		if a in ENGINE_ARGS_OFF:
			return false
	for a in user_args:
		if not a.begins_with(SHOTS_ARG):
			return false
	return true


## Called once by Main._ready(): remembers and returns the decision for this run.
static func decide(main: Node) -> bool:
	var tree := main.get_tree()
	player_launch = is_player_launch(OS.get_cmdline_user_args(), OS.get_cmdline_args(), DisplayServer.get_name(),
		tree != null and tree.current_scene == main)
	return player_launch


## Output folder of the windowed check run (`--splash-shots=DIR`), "" otherwise.
static func shots_dir() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(SHOTS_ARG):
			return a.substr(SHOTS_ARG.length())
	return ""


# ---------------------------------------------------------------- demo notice flag (Settings API)
static func _settings(settings: Object) -> Object:
	return settings if settings != null else Kit.svc("Settings")


static func notice_seen(settings: Object = null) -> bool:
	var s := _settings(settings)
	if s == null or not s.has_method("get_value"):
		return true                       # no settings service: never nag
	var v = s.get_value(NOTICE_KEY)
	return v != null and bool(v)


## True when the main menu should open the notice now (first opening of a real launch, not confirmed before).
static func notice_due(settings: Object = null) -> bool:
	return player_launch and not notice_opened and not notice_seen(settings)


## „Los geht's“ / Esc: persisted through Settings.set_value (user://settings.cfg).
static func mark_notice_seen(settings: Object = null) -> void:
	var s := _settings(settings)
	if s != null and s.has_method("set_value") and not notice_seen(s):
		s.set_value(NOTICE_KEY, true)
