extends Node2D
## Ambient walkers (round 8, feel pass): anonymous people who walk a path through a level, stop now and then
## (look round, face the room), turn softly at the ends and give way to the player. Purely decorative and
## deterministic: no collision, no group membership (dialogue / interaction code never sees them), never
## touches Story or Explore, seeded RNG per walker (no randf), so every run and capture looks the same.
##
## Instanced by Level._spawn_actors from a scene.json "actors" entry (one manager per level):
##   {"scene": "res://scenes/actors/AmbientWalkers.tscn", "pos": [0, 0],
##    "props": {"data": "res://assets/environments/<env>/walkers.json"}}
## The manager is y-sorted itself, so its walkers sort with the player, NPCs and props of the Playfield.
##
## walkers.json = {"walkers": [{
##   "id": "hall_secretary",                unique; the RNG seed comes from it (or "seed")
##   "char": "typist",                       character whose sheet.json / sheet_n.png / rows are used
##   "sheet": "walkers/secretary.png",       optional diffuse variant next to walkers.json (same silhouette,
##                                           tools/pixelgen/walkers_r8.py), so no walker is a speaker's twin
##   "path": [[x, y], ...],                  feet positions in world px (Playfield coordinates), >= 2 points
##   "loop": "pingpong" | "cycle",           back and forth (default) or a closed round
##   "speed": 20,                            px/s (walk playback = speed / sheet ground_speed)
##   "start": 0.3, "dir": 1 | -1,            start as a fraction of the path length, initial direction
##   "pauses": {"2": [1.5, 4.0]},            stop at path point 2 for 1.5..4 s; the ends of a pingpong always
##                                           stop briefly ("end_pause", default [0.8, 2.2]) and turn round
##   "pause_rows": ["look_side", "idle_front"],  what a pause shows (default idle; one-shot rows return to idle)
##   "give_way": 30,                         look-ahead for the player in px (0 = never yields: back lanes of
##                                           side levels, where the player always passes in front)
##   "dodge": 14, "bounds": [x0, y0, x1, y1],  oblique floors: side step around the player, clamped to bounds
##   "pause_clear": 36,                      a pause is skipped while the player stands closer than this
##   "tint": "#ffffff"}]}
## Side levels keep the lane between the props (base_y <= 294/295) and the player's walk band (>= 296): the
## player and every speaking NPC are always drawn in front, the walkers in front of the furniture.

const SpriteRig := preload("res://scripts/actors/sprite_rig.gd")
const TexelLightLib := preload("res://scripts/render/texel_light.gd")
const LayerStack := preload("res://scripts/levels/layer_stack.gd")

var data := ""                  ## res:// path of walkers.json (set by Level from the manifest props)
var walkers: Array = []         ## inline walker specs (alternative to `data`)

var list: Array = []            ## Walker nodes (read by tests / tools)
var _player: Node2D


func _ready() -> void:
	y_sort_enabled = true
	var specs: Array = walkers.duplicate()
	var base_dir := data.get_base_dir()
	if data != "" and FileAccess.file_exists(data):
		var d = JSON.parse_string(FileAccess.get_file_as_string(data))
		if d is Dictionary and d.get("walkers", null) is Array:
			specs.append_array(d["walkers"])
		else:
			push_warning("AmbientWalkers: cannot parse " + data)
	for s in specs:
		if s is Dictionary:
			var w := Walker.new()
			if w.setup(s, base_dir):
				w.name = "Walker_" + str(s.get("id", list.size()))
				add_child(w)
				list.append(w)
			else:
				w.free()


func _process(_delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	var pp := _player.global_position if _player != null else Vector2(INF, INF)
	for w in list:
		w.player_pos = pp


## One walker. States: walk -> (pause | yield | turn) -> walk. Position = point on the path + side step.
class Walker extends Node2D:
	const LANE := 10.0              ## half width of the walker's lane for the give-way test (px)
	const CLEAR := 12.0             ## lateral clearance a side step must reach
	const YIELD_TURN := 3.2         ## s of waiting for the player before turning back
	var id := ""
	var rig: Node2D
	var pts := PackedVector2Array()
	var pingpong := true
	var speed := 20.0
	var from_i := 0
	var to_i := 1
	var base := Vector2.ZERO
	var offset := 0.0
	var offset_target := 0.0
	var state := "walk"
	var timer := 0.0
	var yield_t := 0.0
	var clear_t := 0.0
	var pauses: Dictionary = {}
	var end_pause := Vector2(0.8, 2.2)
	var pause_rows: Array = []
	var give_way := 0.0
	var dodge := 0.0
	var bounds := Rect2()
	var has_bounds := false
	var pause_clear := 36.0
	var player_pos := Vector2(INF, INF)
	var rng := RandomNumberGenerator.new()
	var _gs := 0.0
	var _left := false

	func setup(s: Dictionary, base_dir: String) -> bool:
		id = str(s.get("id", "walker"))
		for p in s.get("path", []):
			pts.append(LayerStack._v2(p))
		if pts.size() < 2:
			push_warning("AmbientWalkers: %s needs a path of >= 2 points" % id)
			return false
		rng.seed = int(s["seed"]) if s.has("seed") else LayerStack.name_hash(id)
		pingpong = str(s.get("loop", "pingpong")) != "cycle"
		speed = maxf(4.0, float(s.get("speed", 20.0)))
		give_way = maxf(0.0, float(s.get("give_way", 0.0)))
		dodge = maxf(0.0, float(s.get("dodge", 0.0)))
		pause_clear = float(s.get("pause_clear", 36.0))
		var b = s.get("bounds", [])
		if b is Array and b.size() == 4:
			bounds = Rect2(float(b[0]), float(b[1]), float(b[2]) - float(b[0]), float(b[3]) - float(b[1]))
			has_bounds = true
		var ps = s.get("pauses", {})
		if ps is Dictionary:
			for k in ps:
				if ps[k] is Array and ps[k].size() == 2:
					pauses[int(k)] = Vector2(float(ps[k][0]), float(ps[k][1]))
		var ep = s.get("end_pause", [])
		if ep is Array and ep.size() == 2:
			end_pause = Vector2(float(ep[0]), float(ep[1]))
		rig = SpriteRig.new()
		add_child(rig)
		if not rig.load_character(str(s.get("char", ""))):
			push_warning("AmbientWalkers: %s: no sheet for '%s'" % [id, str(s.get("char", ""))])
		var vpath := str(s.get("sheet", ""))
		if vpath != "" and rig.sprite != null:
			var full := vpath if vpath.begins_with("res://") else base_dir + "/" + vpath
			var diffuse := LayerStack.tex(full)
			if diffuse != null and rig.sprite.texture is CanvasTexture:
				var ct := CanvasTexture.new()
				ct.diffuse_texture = diffuse
				ct.normal_texture = (rig.sprite.texture as CanvasTexture).normal_texture
				ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				rig.sprite.texture = ct
			elif diffuse == null:
				push_warning("AmbientWalkers: %s: missing variant %s" % [id, full])
		TexelLightLib.apply_tree(rig)
		var rr = rig.get("_rng")
		if rr is RandomNumberGenerator:
			(rr as RandomNumberGenerator).seed = rng.seed + 7      # deterministic blinks / glances
		for r in s.get("pause_rows", []):
			if rig.has_anim(str(r)):
				pause_rows.append(str(r))
		if s.has("tint"):
			modulate = Color(str(s["tint"]))
		_gs = rig.ground_speed("walk_side")
		_place_at(clampf(float(s.get("start", 0.0)), 0.0, 1.0), int(s.get("dir", 1)) < 0)
		return true

	## Puts the walker at `frac` of the path length, heading forward (or back).
	func _place_at(frac: float, backwards: bool) -> void:
		var segs := pts.size() if not pingpong else pts.size() - 1
		var total := 0.0
		for i in segs:
			total += pts[i].distance_to(pts[(i + 1) % pts.size()])
		var want := frac * total
		var i := 0
		while i < segs - 1 and want > pts[i].distance_to(pts[(i + 1) % pts.size()]):
			want -= pts[i].distance_to(pts[(i + 1) % pts.size()])
			i += 1
		var a := pts[i]
		var b2 := pts[(i + 1) % pts.size()]
		base = a.move_toward(b2, want)
		if backwards:
			from_i = (i + 1) % pts.size()
			to_i = i
		else:
			from_i = i
			to_i = (i + 1) % pts.size()
		var d := pts[to_i] - pts[from_i]
		_left = d.x < 0.0
		rig.set_flip(_left)
		position = base
		rig.play("walk_side")

	func _process(delta: float) -> void:
		match state:
			"pause":
				timer -= delta
				if timer <= 0.0:
					_leave_point()
			"turn":
				if not rig.is_turning():
					state = "walk"
			"yield":
				_yield_tick(delta)
			_:
				_walk(delta)
		position = base + _normal() * offset

	func _dir() -> Vector2:
		var d := pts[to_i] - pts[from_i]
		return d.normalized() if d.length() > 0.001 else Vector2.RIGHT

	func _normal() -> Vector2:
		var u := _dir()
		return Vector2(-u.y, u.x)

	func _walk(delta: float) -> void:
		var u := _dir()
		if give_way > 0.0 and _in_way(u):
			if not _try_dodge(u):
				state = "yield"
				yield_t = 0.0
				clear_t = 0.0
				rig.speed_scale = 1.0
				rig.play("idle_side")
				if rig.has_anim("look_side"):
					rig.play_once("look_side", "idle_side")
				return
		elif _passed(u):
			clear_t += delta
			if clear_t > 0.5:
				offset_target = 0.0        # back onto the path once the player is behind or far away
		else:
			clear_t = 0.0
		var spd := speed * (0.55 if absf(offset - offset_target) > 0.5 else 1.0)
		offset = move_toward(offset, offset_target, speed * 0.8 * delta)
		var target := pts[to_i]
		var step := spd * delta
		var left := base.distance_to(target)
		if step >= left:
			base = target
			_arrive()
		else:
			base += u * step
		rig.play("walk_side")
		rig.speed_scale = clampf(spd / _gs, 0.5, 2.0) if _gs > 0.0 else 1.0

	## The player stands (or walks) inside the walker's lane, less than give_way px ahead.
	func _in_way(u: Vector2) -> bool:
		if not is_finite(player_pos.x):
			return false
		var rel := player_pos - base
		var along := rel.dot(u)
		var lat := rel.dot(Vector2(-u.y, u.x))
		return along > -2.0 and along < give_way and absf(lat - offset) < LANE

	## The player is behind the walker or well clear of its lane ahead (the side step may end).
	func _passed(u: Vector2) -> bool:
		if not is_finite(player_pos.x):
			return true
		var rel := player_pos - base
		return rel.dot(u) < -10.0 or rel.length() > give_way + 14.0

	## Side step around the player (oblique floors only); false when no step within dodge / bounds clears.
	func _try_dodge(u: Vector2) -> bool:
		if dodge <= 0.0:
			return false
		clear_t = 0.0
		var n := Vector2(-u.y, u.x)
		var lat := (player_pos - base).dot(n)
		var best := INF
		for cand in [lat + CLEAR, lat - CLEAR]:
			var c := clampf(cand, -dodge, dodge)
			if absf(lat - c) < CLEAR - 0.5:
				continue
			if has_bounds and not bounds.has_point(base + n * c):
				continue
			if absf(c) < absf(best):
				best = c
		if best == INF:
			return false
		offset_target = best
		return true

	func _yield_tick(delta: float) -> void:
		yield_t += delta
		var u := _dir()
		if _in_way(u) and not _try_dodge(u):
			clear_t = 0.0
			if yield_t > YIELD_TURN:
				_reverse()
			return
		clear_t += delta
		if clear_t > 0.35:
			state = "walk"

	## Turn back along the path (waited too long for the player).
	func _reverse() -> void:
		var t := from_i
		from_i = to_i
		to_i = t
		offset = -offset
		offset_target = -offset_target
		_turn_to_dir()

	func _arrive() -> void:
		var i := to_i
		var is_end := pingpong and (i == 0 or i == pts.size() - 1)
		var near := is_finite(player_pos.x) and player_pos.distance_to(base) < pause_clear
		if is_end or (pauses.has(i) and not near):
			var r: Vector2 = pauses.get(i, end_pause)
			if is_end and not pauses.has(i):
				r = end_pause
			if near and is_end:
				r = Vector2(0.3, 0.6)          # a short beat only: the player is right here
			timer = rng.randf_range(r.x, r.y)
			state = "pause"
			rig.speed_scale = 1.0
			_pause_pose(is_end)
			_next_target()
			return
		_next_target()
		if _turn_to_dir():
			return

	func _pause_pose(is_end: bool) -> void:
		var row := "idle_side"
		if not pause_rows.is_empty() and (not is_end or rng.randf() < 0.5):
			row = str(pause_rows[rng.randi() % pause_rows.size()])
		if row == "idle_side" or row.begins_with("idle_"):
			rig.play(row)
		else:
			rig.play("idle_side")
			rig.play_once(row, "idle_side")

	func _next_target() -> void:
		var n := pts.size()
		if pingpong:
			var fwd := to_i > from_i
			var nxt := to_i + (1 if fwd else -1)
			if nxt < 0 or nxt >= n:
				nxt = to_i + (-1 if fwd else 1)
			from_i = to_i
			to_i = nxt
		else:
			from_i = to_i
			to_i = (to_i + 1) % n

	func _leave_point() -> void:
		rig.play("idle_side")
		if not _turn_to_dir():
			state = "walk"

	## Soft turn (rig.turn_to: front frame, then mirrored) when the new heading points the other way.
	func _turn_to_dir() -> bool:
		var d := pts[to_i] - pts[from_i]
		if absf(d.x) < 0.15 * d.length():
			return false
		var left := d.x < 0.0
		if left == _left:
			return false
		_left = left
		if rig.turn_to(left, 0.22):
			state = "turn"
			return true
		return false
