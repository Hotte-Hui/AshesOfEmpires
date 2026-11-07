extends RefCounted
## Desktop shortcut on the first real launch (scripts/core/desktop_shortcut.gd): the decision, the PowerShell command
## (quoting) and — on Windows — that the command really writes a working .lnk (into a temporary folder, never onto the
## real desktop).

const Kit := preload("res://tests/support/test_kit.gd")
const DS := preload("res://scripts/core/desktop_shortcut.gd")

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("decision", _decision)
	kit.run_case("powershell_command_quotes_paths", _command)
	kit.run_case("writes_a_link_in_a_temp_folder", _writes)
	kit.cleanup()
	return kit.failures


func _decision() -> bool:
	var exe := "C:/Spiele/AshesOfEmpires/AshesOfEmpires.exe"
	kit.ok(DS.should_create("Windows", true, exe, false), "exported Windows game, first launch → create")
	kit.ok(not DS.should_create("Windows", true, exe, true), "flag set → never again")
	kit.ok(not DS.should_create("Windows", false, exe, false), "editor run → no link")
	kit.ok(not DS.should_create("Linux", true, exe, false), "not Windows → no link")
	kit.ok(not DS.should_create("Windows", true, "C:/Users/x/AppData/Local/Temp/Temp1_Ashes.zip/AshesOfEmpires.exe", false),
		"started from inside a ZIP (temp folder) → no link to a vanishing path")
	kit.eq(DS.link_path("C:\\Users\\x\\Desktop"), "C:/Users/x/Desktop/Ashes of Empires.lnk", "link name on the desktop")
	return true


func _command() -> bool:
	var c := DS.ps_command("C:/Users/x/Desktop/Ashes of Empires.lnk", "D:/Spiele/Kai's Ordner/AshesOfEmpires.exe")
	kit.ok(c.contains("'D:\\Spiele\\Kai''s Ordner\\AshesOfEmpires.exe'"), "target in single quotes, the apostrophe doubled")
	kit.ok(c.contains("WorkingDirectory='D:\\Spiele\\Kai''s Ordner'"), "working directory = the game folder")
	kit.ok(c.contains("IconLocation='D:\\Spiele\\Kai''s Ordner\\AshesOfEmpires.exe,0'"), "icon from the exe")
	kit.ok(DS.ps_args("a", "b").has("-NonInteractive") and DS.ps_args("a", "b").has("Hidden"), "hidden, non-interactive")
	return true


func _writes() -> bool:
	if OS.get_name() != "Windows":
		return true
	var tmp := OS.get_user_data_dir().path_join("test_desktop_shortcut")
	DirAccess.make_dir_recursive_absolute(tmp)
	var lnk := DS.link_path(tmp)
	var exe := OS.get_executable_path()
	var out := []
	var code := OS.execute("powershell.exe", DS.ps_args(lnk, exe), out, true)
	kit.eq(code, 0, "PowerShell exit code: " + str(out))
	kit.ok(FileAccess.file_exists(lnk), "the .lnk exists")
	var probe := []
	OS.execute("powershell.exe", PackedStringArray(["-NoProfile", "-NonInteractive", "-Command",
		"(New-Object -ComObject WScript.Shell).CreateShortcut('%s').TargetPath" % lnk.replace("/", "\\")]), probe, true)
	kit.eq(str(probe[0] if probe.size() > 0 else "").strip_edges().to_lower(), exe.replace("/", "\\").to_lower(),
		"the link points to the game's exe")
	DirAccess.remove_absolute(lnk)
	DirAccess.remove_absolute(tmp)
	return true
