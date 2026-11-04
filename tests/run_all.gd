extends SceneTree
## Test runner: loads every res://tests/test_*.gd (extends RefCounted, func run() -> Array of failure
## strings), runs them, prints a report and quits with exit code 0 (all passed) or 1.
##
##   Godot_v4.7.2-stable_win64_console.exe --headless --path C:/Spiele/AshesOfEmpires --script res://tests/run_all.gd
##   ... --script res://tests/run_all.gd -- --filter=saves      (only files whose name contains "saves")
##
## Engine/script errors printed while a test file runs (push_error, SCRIPT ERROR) are captured with a
## Logger and count as failures, so a crashing test can never pass silently.

const TEST_DIR := "res://tests"
const TRAP_META := "ashes_test_error_trap"


class ErrorTrap extends Logger:
	var enabled := false
	var errors: Array = []
	var _mutex := Mutex.new()

	func _log_error(function: String, file: String, line: int, code: String, rationale: String,
			_editor_notify: bool, error_type: int, _script_backtraces: Array) -> void:
		if not enabled or error_type == ERROR_TYPE_WARNING:
			return
		_mutex.lock()
		errors.append("%s [%s:%d %s]" % [rationale if rationale != "" else code, file, line, function])
		_mutex.unlock()

	func _log_message(_message: String, _error: bool) -> void:
		pass


var _started := false
var _done := false


## Tests run on the first frame (not in _initialize) so the project's autoloads have received _ready().
func _process(_delta: float) -> bool:
	if _done:
		return false
	if _started:
		printerr("run_all: the runner itself aborted (script error in run_all.gd)")
		_done = true
		quit(1)
		return false
	_started = true
	var code := _run()
	_done = true
	quit(code)
	return false


func _run() -> int:
	var filter := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--filter="):
			filter = a.substr(9)
	var files: Array = []
	var dir := DirAccess.open(TEST_DIR)
	if dir == null:
		printerr("run_all: cannot open " + TEST_DIR)
		return 1
	for f in dir.get_files():
		if f.begins_with("test_") and f.ends_with(".gd") and (filter == "" or f.contains(filter)):
			files.append(f)
	files.sort()
	var trap := ErrorTrap.new()
	OS.add_logger(trap)
	Engine.set_meta(TRAP_META, trap)   # tests pause it around intentionally failing I/O (Kit.quietly)
	print("== ASHES OF EMPIRES — test suite (Godot %s) ==" % Engine.get_version_info()["string"])
	var total_failures := 0
	var total_cases := 0
	var total_checks := 0
	var failed_files := 0
	var t_all := Time.get_ticks_msec()
	for f in files:
		var path: String = TEST_DIR.path_join(f)
		var failures: Array = []
		var cases := 0
		var checks := 0
		var t0 := Time.get_ticks_msec()
		trap.errors.clear()
		trap.enabled = true
		var script = load(path)
		if script == null or not (script is GDScript) or not script.can_instantiate():
			failures.append("cannot load/instantiate (parse error?)")
		else:
			var inst = script.new()
			if not inst.has_method("run"):
				failures.append("no run() method")
			else:
				var res = inst.run()
				if typeof(res) != TYPE_ARRAY:
					failures.append("run() aborted or returned %s instead of an Array" % type_string(typeof(res)))
				else:
					for x in res:
						failures.append(str(x))
				var kit = inst.get("kit")
				if kit != null:
					cases = int(kit.get("cases"))
					checks = int(kit.get("checks"))
		trap.enabled = false
		for e in trap.errors:
			failures.append("unexpected engine error: " + str(e))
		var ms := Time.get_ticks_msec() - t0
		total_cases += cases
		total_checks += checks
		if failures.is_empty():
			print("PASS  %-34s %3d cases %5d checks %6d ms" % [f, cases, checks, ms])
		else:
			failed_files += 1
			total_failures += failures.size()
			print("FAIL  %-34s %3d cases %5d checks %6d ms" % [f, cases, checks, ms])
			for x in failures:
				print("      - " + str(x))
	OS.remove_logger(trap)
	Engine.remove_meta(TRAP_META)
	var secs := (Time.get_ticks_msec() - t_all) / 1000.0
	print("------------------------------------------------------------------------------")
	if total_failures == 0 and not files.is_empty():
		print("SUMMARY: %d files, %d cases, %d checks — ALL PASSED in %.2f s" % [files.size(), total_cases, total_checks, secs])
		return 0
	print("SUMMARY: %d files, %d cases, %d checks — %d FAILURE(S) in %d file(s) (%.2f s)" % [files.size(), total_cases,
		total_checks, total_failures, failed_files, secs])
	return 1
