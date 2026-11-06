extends "res://scripts/levels/karsk/karsk_actor.gd"
## Travellers, a railwayman with his hand lamp and a porter with a luggage barrow walking on the island
## platform between tracks 4 and 5 (parallax 0.93, seen between courier wagon 4 and the concourse).
## Up to `count` people are on the island at a time; each walks the lane in one direction, sometimes stops
## at a pause spot (looking at the board, waiting), leaves at the far end and is replaced a few seconds later
## by somebody else (deterministic RNG). Purely decorative: no collision, never touches Story / Explore.
## Sheets (tools/pixelgen/env_veltrava_station_life.py): walker_<kind>.png = 18 frames (0-7 walk right,
## 8-15 walk left, 16 stand right, 17 stand left), porter_barrow.png = 16 frames; feet at the cell's bottom
## centre. Node position = (0, feet y) in layer coordinates at camera x 0 (like a scene.json layer pos).

var span: Array = [560.0, 1440.0]       ## layer x range of the lane
var count := 4
var sheets: Array = []                  ## [{file, cell: [w, h], frames, speed: [min, max], barrow?: bool}]
var rng_seed := 931
var pause_spots: Array = []             ## [[x, min_s, max_s], ...]
const STRIDE := 17.0                    ## layer px per walk cycle (8 frames) at the island scale

var _tex: Array = []
var _people: Array = []                 # [{spr, sheet, x, dir, speed, ph, pause, paused_at, wait}]
var _rng := RandomNumberGenerator.new()


func _setup() -> void:
	_rng.seed = rng_seed
	for s in sheets:
		_tex.append(load_tex(str(s.get("file", ""))))
	if _tex.is_empty():
		return
	for i in count:
		var p := {"spr": null, "sheet": -1, "x": 0.0, "dir": 1.0, "speed": 18.0, "ph": 0.0, "pause": 0.0,
			"paused_at": -9999.0, "wait": 0.0}
		_people.append(p)
		_spawn(p, true)


func _spawn(p: Dictionary, initial := false) -> void:
	# pick a sheet nobody else uses right now (the porter at most once)
	var used := {}
	for q in _people:
		if q != p and int(q["sheet"]) >= 0:
			used[int(q["sheet"])] = true
	var choice := -1
	for _i in 8:
		var c := _rng.randi() % sheets.size()
		if not used.has(c) and _tex[c] != null:
			choice = c
			break
	if choice < 0:
		choice = _rng.randi() % sheets.size()
	var sh: Dictionary = sheets[choice]
	if p["spr"] != null and is_instance_valid(p["spr"]):
		(p["spr"] as Node).queue_free()
	var spr := make_strip(_tex[choice], int(sh.get("frames", 18)))
	var cell: Array = sh.get("cell", [23, 37])
	spr.offset = Vector2(-floorf(float(cell[0]) * 0.5), -float(cell[1]) + 1.0)
	p["spr"] = spr
	p["sheet"] = choice
	p["dir"] = 1.0 if _rng.randf() < 0.5 else -1.0
	var sp: Array = sh.get("speed", [17.0, 23.0])
	p["speed"] = _rng.randf_range(float(sp[0]), float(sp[1]))
	p["ph"] = _rng.randf()
	p["pause"] = 0.0
	p["paused_at"] = -9999.0
	if initial:
		p["x"] = _rng.randf_range(float(span[0]) + 40.0, float(span[1]) - 40.0)
		p["wait"] = 0.0
	else:
		p["x"] = float(span[0]) if float(p["dir"]) > 0.0 else float(span[1])
		p["wait"] = _rng.randf_range(2.0, 9.0)
	spr.visible = float(p["wait"]) <= 0.0
	_place(p)


func _place(p: Dictionary) -> void:
	var spr: Sprite2D = p["spr"]
	var sh: Dictionary = sheets[int(p["sheet"])]
	var walk_frames := 8
	var standing := float(p["pause"]) > 0.0
	var f := int(float(p["ph"]) * walk_frames) % walk_frames
	if bool(sh.get("barrow", false)):
		spr.frame = (f if float(p["dir"]) > 0.0 else f + 8) if not standing else (0 if float(p["dir"]) > 0.0 else 8)
	else:
		if standing:
			spr.frame = 16 if float(p["dir"]) > 0.0 else 17
		else:
			spr.frame = f if float(p["dir"]) > 0.0 else f + 8
	spr.position = Vector2(roundf(float(p["x"])), 0.0)


func _tick(delta: float) -> void:
	for p in _people:
		if p["spr"] == null:
			continue
		if float(p["wait"]) > 0.0:
			p["wait"] = float(p["wait"]) - delta
			if float(p["wait"]) <= 0.0:
				(p["spr"] as Sprite2D).visible = true
			continue
		if float(p["pause"]) > 0.0:
			p["pause"] = float(p["pause"]) - delta
			_place(p)
			continue
		var dx := float(p["dir"]) * float(p["speed"]) * delta
		p["x"] = float(p["x"]) + dx
		p["ph"] = fmod(float(p["ph"]) + absf(dx) / STRIDE, 1.0)
		for ps in pause_spots:
			var sx := float(ps[0])
			if absf(float(p["x"]) - sx) < 0.6 and absf(float(p["paused_at"]) - sx) > 1.0:
				p["paused_at"] = sx
				if _rng.randf() < 0.45 and not bool(sheets[int(p["sheet"])].get("barrow", false)):
					p["pause"] = _rng.randf_range(float(ps[1]), float(ps[2]))
		_place(p)
		if float(p["x"]) < float(span[0]) - 30.0 or float(p["x"]) > float(span[1]) + 30.0:
			_spawn(p)
