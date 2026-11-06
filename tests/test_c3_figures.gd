extends RefCounted
## Round 10, the figures of LS_C3_Trains / LS_C3_ToHall / LS_C3_Close (owner: figures stream):
## the seated Konrad and Alexei sheets have their 4 frames and the boxes the runtime reads from layout.json
## (the boxes now reach the cup and the tea-glass handle: the whole arm is in the figure); the walking Konrad
## under the palais clock is an 8-frame cycle; every extra listed in layout.json (tohall/close "extras") has its
## sheet, a sole anchor inside the frame and a time-ordered path; the scenes mount the people drawers in the
## right shots and their frames are pure functions of the timeline; c3_people.gd interpolates paths and steps
## walk cycles by the distance walked.
## Round 10b (art-director pass): the walking Konrad is a whole man inside the letterbox (rows 46..314) who walks
## along konrad_path from the left edge to the clock (no skating: his cycle follows the floor he covers); the hotel
## windows of LS_C3_Close step through their in-between states on a schedule instead of popping.

const Kit := preload("res://tests/support/test_kit.gd")
const People := preload("res://scenes/cinematics/ch3_common/c3_people.gd")
const ASSETS := "res://assets/cinematics/ch3/"

var kit: Kit


func run() -> Array:
	kit = Kit.new()
	kit.run_case("seated_heroes_sheets_and_boxes", _seated)
	kit.run_case("walking_konrad_cycle", _walk)
	kit.run_case("extras_sheets_and_paths", _extras)
	kit.run_case("people_drawer_paths_and_frames", _drawer)
	kit.run_case("scenes_mount_the_people", _mounted)
	kit.run_case("konrad_walks_in_frame_to_the_clock", _walk_path)
	kit.run_case("hotel_windows_step_not_pop", _windows)
	kit.cleanup()
	return kit.failures


func _layout() -> Dictionary:
	var p := ASSETS + "layout.json"
	if not FileAccess.file_exists(p):
		return {}
	var L = JSON.parse_string(FileAccess.get_file_as_string(p))
	return L if L is Dictionary else {}


func _tex(rel: String) -> Texture2D:
	var p := ASSETS + rel
	return load(p) as Texture2D if ResourceLoader.exists(p) else null


func _seated() -> bool:
	var tr: Dictionary = _layout().get("trains", {})
	for pair in [["fig_konrad", 236, 232], ["fig_alexei", 252, 232]]:
		var t := _tex("trains/%s.png" % pair[0])
		if not kit.ok(t != null, "%s.png exists" % pair[0]):
			continue
		kit.eq(t.get_width(), int(pair[1]) * 4, "%s: four frames of %d px" % [pair[0], pair[1]])
		kit.eq(t.get_height(), int(pair[2]), "%s height" % pair[0])
		var pos: Array = tr.get(pair[0], [])
		kit.ok(pos.size() == 2, "layout trains.%s" % pair[0])
	# the boxes reach the cup / the tea-glass handle (the arm and hand are part of the figure sprite)
	var pk: Array = tr.get("fig_konrad", [9999, 0])
	var pa: Array = tr.get("fig_alexei", [0, 0])
	kit.ok(float(pk[0]) <= 352.0, "Konrad's box starts left of his cup (x %s)" % str(pk[0]))
	kit.ok(float(pa[0]) + 252.0 >= 322.0, "Alexei's box reaches the holder's handle")
	return true


func _walk() -> bool:
	var th: Dictionary = _layout().get("tohall", {})
	var n := int(th.get("konrad_frames", 0))
	kit.eq(n, 8, "the walk under the palais clock has 8 frames")
	var t := _tex("tohall/k2_konrad.png")
	if kit.ok(t != null, "k2_konrad.png exists") and n > 0:
		kit.eq(t.get_width() % n, 0, "the sheet splits into equal frames")
	return true


func _extras() -> bool:
	var L := _layout()
	for part in ["tohall", "close"]:
		var ex: Array = (L.get(part, {}) as Dictionary).get("extras", [])
		kit.ok(ex.size() >= 4, "%s: extras listed (%d)" % [part, ex.size()])
		for e in ex:
			var d: Dictionary = e
			var t := _tex(str(d.get("tex", "")))
			if not kit.ok(t != null, "%s: %s exists" % [part, str(d.get("tex", ""))]):
				continue
			var nf := int(d.get("frames", 0))
			kit.ok(nf >= 1 and t.get_width() % nf == 0, "%s: frames of %s" % [part, d.get("name", "?")])
			var fw := t.get_width() / maxi(1, nf)
			var anc: Array = d.get("anchor", [])
			kit.ok(anc.size() == 2 and float(anc[0]) >= 0 and float(anc[0]) < fw and float(anc[1]) < t.get_height(),
				"%s: anchor of %s inside the frame" % [part, d.get("name", "?")])
			var path: Array = d.get("path", [])
			var ordered := path.size() >= 1
			for i in range(1, path.size()):
				ordered = ordered and float(path[i][0]) >= float(path[i - 1][0])
			kit.ok(ordered, "%s: path of %s is time-ordered" % [part, d.get("name", "?")])
	return true


func _drawer() -> bool:
	var path := [[1.0, 10.0, 50.0], [3.0, 50.0, 50.0], [4.0, 50.0, 80.0]]
	var a: Array = People.path_at(path, 0.0)
	kit.eq(a[0], Vector2(10, 50), "held at the first key before it starts")
	var b: Array = People.path_at(path, 2.0)
	kit.eq(b[0], Vector2(30, 50), "halfway along the first leg")
	kit.ok(absf(float(b[1]) - 20.0) < 0.001, "distance walked so far")
	var c: Array = People.path_at(path, 9.0)
	kit.eq(c[0], Vector2(50, 80), "held at the last key")
	kit.ok(absf(float(c[1]) - 70.0) < 0.001, "the whole path walked")
	var p := People.new()
	kit.track(p)
	var e := {"frames": 8, "stride": 40.0}
	kit.eq(p.frame_of(e, 0.0), 0, "cycle starts at frame 0")
	kit.eq(p.frame_of(e, 20.0), 4, "half a stride = half the cycle")
	kit.eq(p.frame_of(e, 40.0), 0, "one stride = one full cycle")
	var idle := {"frames": 4, "fps": 2.0}
	p.t = 1.0
	kit.eq(p.frame_of(idle, 0.0), 2, "idle frames run on the timeline")
	return true


func _find_people(n: Node, out: Array) -> void:
	for c in n.get_children():
		if c.get_script() == People:
			out.append(c)
		_find_people(c, out)


func _mounted() -> bool:
	for pair in [["res://scenes/cinematics/ch3_tohall/Ch3ToHall.tscn", 2], ["res://scenes/cinematics/ch3_close/Ch3Close.tscn", 2]]:
		var s: Node = load(str(pair[0])).instantiate()
		s.set("use_director", false)
		(Engine.get_main_loop() as SceneTree).root.add_child(s)
		kit.track(s)
		var found: Array = []
		_find_people(s, found)
		kit.eq(found.size(), int(pair[1]), "%s: one people drawer per shot" % str(pair[0]).get_file())
		var total := 0
		for f in found:
			total += (f.get("entries") as Array).size()
		kit.ok(total >= 4, "%s: extras mounted (%d)" % [str(pair[0]).get_file(), total])
		# deterministic: the same time draws the same frame
		s.call("seek", 4.2)
		var t1: Array = []
		for f in found:
			t1.append(f.get("t"))
		s.call("seek", 1.0)
		s.call("seek", 4.2)
		var t2: Array = []
		for f in found:
			t2.append(f.get("t"))
		kit.eq(t2, t1, "%s: people follow the timeline" % str(pair[0]).get_file())
	return true


const LETTERBOX := [46.0, 314.0]


func _walk_path() -> bool:
	var th: Dictionary = _layout().get("tohall", {})
	var kp: Array = th.get("konrad_path", [])
	if not kit.ok(kp.size() >= 2, "layout tohall.konrad_path"):
		return true
	var t := _tex("tohall/k2_konrad.png")
	var n := int(th.get("konrad_frames", 8))
	if not kit.ok(t != null, "k2_konrad.png exists"):
		return true
	var fw := t.get_width() / maxi(1, n)
	var anc: Array = th.get("konrad_anchor", [])
	kit.ok(anc.size() == 2 and float(anc[0]) >= 0 and float(anc[0]) < fw and float(anc[1]) < t.get_height(),
		"the soles' anchor lies inside the frame")
	kit.ok(float(th.get("konrad_stride", 0.0)) > 20.0, "a stride (px of floor per cycle)")
	# the whole figure (hat to soles) stays between the letterbox bars on the whole path
	for k in kp:
		var top := float(k[2]) - float(anc[1])
		kit.ok(top >= LETTERBOX[0] and float(k[2]) < LETTERBOX[1],
			"Konrad fits between the bars at t=%s (top %d, soles %d)" % [str(k[0]), int(top), int(k[2])])
	var first: Array = kp[0]
	var last: Array = kp[kp.size() - 1]
	kit.ok(float(first[0]) <= 3.05, "he is walking when the palais shot cuts in")
	kit.ok(float(last[1]) >= 240.0 and float(last[1]) <= 400.0, "he ends under the clock (x %s)" % str(last[1]))
	# the runtime: the cycle follows the floor he covers (one stride = one cycle), deterministic per time
	var s: Node = load("res://scenes/cinematics/ch3_tohall/Ch3ToHall.tscn").instantiate()
	s.set("use_director", false)
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	kit.track(s)
	var spr: Sprite2D = s.get("_konrad")
	if not kit.ok(spr != null, "the scene has its Konrad sprite"):
		return true
	s.call("seek", 3.2)
	var p0 := spr.position
	var f0 := spr.frame
	s.call("seek", 5.8)
	var p1 := spr.position
	kit.ok(p1.x > p0.x + 150.0, "he walks right across the foyer (%d -> %d)" % [int(p0.x), int(p1.x)])
	kit.ok(spr.visible, "visible while he walks")
	var stride := float(th.get("konrad_stride", 88.0))
	var v := (float(last[1]) - float(first[1])) / maxf(0.01, float(last[0]) - float(first[0]))
	s.call("seek", 3.2 + stride / v)
	kit.eq(spr.frame, f0, "one stride later the cycle is back on the same frame")
	s.call("seek", 3.2)
	kit.eq(spr.position, p0, "seek is deterministic")
	return true


func _windows() -> bool:
	var cl: Dictionary = _layout().get("close", {})
	var nf := int(cl.get("win_frames", 0))
	kit.ok(nf >= 5, "the windows have in-between states (%d frames)" % nf)
	var seq: Dictionary = cl.get("win_seq", {})
	for who in ["konrad", "alexei"]:
		var t := _tex("close/n2_win_%s.png" % who)
		if kit.ok(t != null, "n2_win_%s.png exists" % who) and nf > 0:
			kit.eq(t.get_width() % nf, 0, "%s: the sheet splits into %d frames" % [who, nf])
		var e: Array = seq.get(who, [])
		if not kit.ok(e.size() >= 5, "%s: a schedule of window states" % who):
			continue
		var ordered := true
		var steps := true
		for i in range(1, e.size()):
			ordered = ordered and float(e[i][0]) >= float(e[i - 1][0])
			steps = steps and int(e[i][1]) == int(e[i - 1][1]) + 1
		kit.ok(ordered and steps, "%s: the states follow one another in time" % who)
		kit.eq(int(e[0][1]), 0, "%s: the window starts empty" % who)
		kit.ok(float(e[e.size() - 1][0]) > 8.4, "%s: he turns after the whistle (8.4 s)" % who)
	var s: Node = load("res://scenes/cinematics/ch3_close/Ch3Close.tscn").instantiate()
	s.set("use_director", false)
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	kit.track(s)
	s.call("seek", 6.5)
	kit.eq(s.call("window_frame", "konrad", 6.5), 0, "Konrad's window is still empty at 6.5 s")
	kit.eq(s.call("window_frame", "konrad", 11.5), maxi(0, nf - 1), "Konrad in profile at the end")
	kit.ok(int(s.call("window_frame", "alexei", 7.6)) > 0 and int(s.call("window_frame", "alexei", 7.6)) < 3,
		"Alexei is still on his way to the glass at 7.6 s")
	return true
