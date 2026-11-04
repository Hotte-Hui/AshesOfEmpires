class_name Symbols
extends RefCounted
## Historical-insignia switch (TECHNICAL_ARCHITECTURE §12.4).
## Every asset that shows real regime insignia exists twice:
##   <name>.<ext>        neutral / fictional emblem (always present, the safe default file)
##   <name>_hist.<ext>   the same image with the real historical insignia
## Loaders call Symbols.pick(path): it returns the _hist variant when the player setting
## "historical_symbols" is on and that file exists, otherwise the neutral path.
## The insignia are shown only as in-world iconography of oppressive regimes inside a critical, fictional
## narrative (social-adequacy clause, StGB §86 Abs. 4) — never as decoration of the UI, menus or rewards.


static func enabled() -> bool:
	var s = Engine.get_main_loop().root.get_node_or_null("/root/Settings") if Engine.get_main_loop() else null
	if s == null:
		return true
	return bool(s.get_value("historical_symbols"))


static func hist_path(path: String) -> String:
	return path.get_basename() + "_hist." + path.get_extension()


static func pick(path: String) -> String:
	if path == "" or not enabled():
		return path
	var h := hist_path(path)
	if ResourceLoader.exists(h) or FileAccess.file_exists(h):
		return h
	return path
