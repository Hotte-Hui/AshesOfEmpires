extends RefCounted
## Desktop shortcut (user request 2026-11-07: downloaded, unpacked, started → „Ashes of Empires“ on the desktop, like an
## installer would do it). Main calls ensure() only on a real player's launch (scripts/ui/boot_flow.gd: never in the
## editor, tests, drivers or harnesses). Once per player (settings flag `desktop_shortcut_done`); only for the exported
## Windows game; never for an exe started from inside a ZIP (it would point into a temp folder); an existing
## „Ashes of Empires.lnk“ is kept as it is. The link is written by Windows' own WScript.Shell through a hidden
## PowerShell that runs in parallel with the boot sequence.
const Kit := preload("res://scripts/ui/ui_kit.gd")
const FLAG := "desktop_shortcut_done"
const LINK_NAME := "Ashes of Empires.lnk"
const DESCRIPTION := "ASHES OF EMPIRES: THE LAST WINTER"


## Pure decision (tests): Windows, an exported game, not done before, not run from a temp / ZIP folder.
static func should_create(os_name: String, is_export: bool, exe_path: String, done: bool) -> bool:
	if os_name != "Windows" or not is_export or done or exe_path == "":
		return false
	var p := exe_path.replace("\\", "/").to_lower()
	return not (p.contains("/temp/") or p.contains("/tmp/") or p.contains(".zip/"))


static func link_path(desktop_dir: String) -> String:
	return desktop_dir.replace("\\", "/").path_join(LINK_NAME)


static func _quote(s: String) -> String:
	return "'" + s.replace("'", "''") + "'"


## The PowerShell command that writes the link (single-quoted strings; a ' in a path is doubled).
static func ps_command(lnk: String, exe: String) -> String:
	var fwd := exe.replace("\\", "/")
	var target := fwd.replace("/", "\\")
	var workdir := fwd.get_base_dir().replace("/", "\\")
	return "$s=(New-Object -ComObject WScript.Shell).CreateShortcut(%s);$s.TargetPath=%s;$s.WorkingDirectory=%s;$s.IconLocation=%s;$s.Description=%s;$s.Save()" % [
		_quote(lnk.replace("/", "\\")), _quote(target), _quote(workdir), _quote(target + ",0"), _quote(DESCRIPTION)]


static func ps_args(lnk: String, exe: String) -> PackedStringArray:
	return PackedStringArray(["-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_command(lnk, exe)])


static func _done(s: Object) -> bool:
	if s == null or not s.has_method("get_value"):
		return true                       # no settings service: never act
	var v = s.get_value(FLAG)
	return v != null and bool(v)


## Main, on a player launch only. Non-blocking: the boot sequence keeps playing while PowerShell writes the link.
static func ensure(settings: Object = null) -> void:
	var s: Object = settings if settings != null else Kit.svc("Settings")
	var exe := OS.get_executable_path()
	if not should_create(OS.get_name(), not OS.has_feature("editor"), exe, _done(s)):
		return
	var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
	if desk == "":
		return
	var lnk := link_path(desk)
	if not FileAccess.file_exists(lnk):
		OS.create_process("powershell.exe", ps_args(lnk, exe), false)
	s.set_value(FLAG, true)
