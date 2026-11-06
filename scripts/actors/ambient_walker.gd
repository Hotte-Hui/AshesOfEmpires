extends Node2D
## Ambient walkers (round 8, feel pass; round 9, feel pass 2): anonymous people who walk a path through a level,
## stop now and then (look round, face the room), turn softly at the ends, give way to the player and to each
## other. Purely decorative and deterministic: no collision, no group membership (dialogue / interaction code
## never sees them), never touches Story or Explore, seeded RNG per walker (no randf), so every run and capture
## looks the same.
##
## Instanced by Level._spawn_actors from a scene.json "actors" entry (one manager per level):
##   {"scene": "res://scenes/actors/AmbientWalkers.tscn", "pos": [0, 0],
##    "props": {"data": "res://assets/environments/<env>/walkers.json"}}
## The manager is y-sorted itself, so its walkers sort with the player, NPCs and props of the Playfield.
##
## walkers.json = {"walkers": [{
##   "id": "hall_secretary",                unique; the RNG seed and the passing rank come from it (or "seed")
##   "char": "typist",                       character whose sheet.json / sheet_n.png / rows are used
##   "rig": "walkers/secretary_rig.json",    round 9: the walker's OWN sheet (json + .png + _n.png next to it,
##                                           tools/pixelgen/walkers_r8.py): the source's rows plus walk_front /
##                                           idle_back / walk_back, so paths may run diagonally; preferred
##   "sheet": "walkers/secretary.png",       round 8: diffuse variant over the source's rows (same silhouette,
##                                           the source's sheet_n.png); used when there is no "rig"
##   "path": [[x, y], ...],                  feet positions in world px (Playfield coordinates), >= 2 points
##   "loop": "pingpong" | "cycle",           back and forth (default) or a closed round
##   "speed": 20,                            px/s (walk playback = speed / ground_speed of the shown row)
##   "start": 0.3, "dir": 1 | -1,            start as a fraction of the path length, initial direction
##   "pauses": {"2": [1.5, 4.0]},            stop at path point 2 for 1.5..4 s; the ends of a pingpong always
##                                           stop briefly ("end_pause", default [0.8, 2.2]) and turn round
##   "pause_rows": ["look_side", "idle_front"],  what a pause shows (default idle; one-shot rows return to idle)
##   "give_way": 30,                         look-ahead for the player in px (0 = never yields: back lanes of
##                                           side levels, where the player always passes in front)
##   "dodge": 14, "bounds": [x0, y0, x1, y1],  oblique floors: side step around the player, clamped to bounds
##   "pause_clear": 36,                      a pause is skipped while the player stands closer than this
##   "pass": 0.5,                            step aside for another walker (px along the path normal; side lanes:
##                                           a half-pixel depth step backwards, so the two pass one behind the
##                                           other; default 0.5, or `dodge` on oblique floors; 0 = never)
##   "tint": "#ffffff"}]}
## Side levels keep the lane between the props (base_y <= 294/295) and the player's walk band (>= 296): the
## player and every speaking NPC are always drawn in front, the walkers in front of the furniture.
## Walkers among themselves (round 9): nobody walks into another one. Head-on in one lane, the walker with the
## lower rank steps aside (or, without room, the other one does; without room for either, the lower rank waits a
## moment and turns back); a walker that catches up with a slower or standing one keeps its distance, passes it
## with a step aside when there is room, else waits and finally turns back.

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
	for w in list:
		w.peers = list


func _process(_delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	var pp := _player.global_position if _player != null else Vector2(INF, INF)
	for w in list:
		w.player_pos = pp


## One walker. States: walk -> (pause | yield | wait | turn) -> walk. Position = point on the path + side step.
class Walker extends Node2D:
	## Loads a walker's own sheet (round 9 "rig": sheet json + <name>.png + <name>_n.png) into `r`, replacing
	## the source character's rows. Returns false (rig untouched) when the files are missing.
	static func load_rig_sheet(r: Node2D, json_path: String) -> bool:
		if not FileAccess.file_exists(json_path):
			return false
		var d = JSON.parse_string(FileAccess.get_file_as_string(json_path))
		var t := LayerStack.canvas_tex(json_path.get_basename() + ".png", true)
		if not (d is Dictionary and d.get("anims") is Dictionary) or t == null:
			return false
		var sp: Sprite2D = r.get("sprite")
		if sp == null:
			return false
		r.set("sheet", d)
		var cell := LayerStack._v2(d.get("cell", [32, 56]))
		r.set("_cell", cell)
		r.set("_origin", LayerStack._v2(d.get("origin", [cell.x * 0.5, cell.y - 2])))
		sp.texture = t
		sp.hframes = maxi(1, int(t.get_width() / cell.x))
		sp.vframes = maxi(1, int(t.get_height() / cell.y))
		r.call("_apply_offset")
		r.call("play", r.call("first_idle"), true)
		return true

	const LANE := 10.0              ## half width of the walker's lane for the give-way test (px)
	const CLEAR := 12.0             ## lateral clearance a side step must reach
	const YIELD_TURN := 3.2         ## s of waiting for the player before turning back
	const PEER_LOOK := 34.0         ## look-ahead for other walkers (px, feet to feet)
	const PEER_GAP := 18.0          ## a walker never closes in on another one in its lane below this
	const PEER_TURN := 4.0          ## s of waiting for a blocked lane before turning back (lower rank: 1.2 s)
	const DIAG := 1.2               ## |dy| > DIAG * |dx|: walk_front / walk_back (when the sheet has them)
	var id := ""
	var rig: Node2D
	var pts := PackedVector2Array()
	var pingpong := true
	var speed := 20.0
	var from_i := 0
	var to_i := 1
	var base := Vector2.ZERO
	var offset := 0.0
	var offset_target := 0.0        ## side step around the player
	var peer_target := 0.0          ## side step for another walker (used while offset_target is 0)
	var state := "walk"
	var timer := 0.0
	var yield_t := 0.0
	var clear_t := 0.0
	var wait_t := 0.0
	var pauses: Dictionary = {}
	var end_pause := Vector2(0.8, 2.2)
	var pause_rows: Array = []
	var give_way := 0.0
	var dodge := 0.0
	var pass_off := 0.5
	var peer_lane := 2.0
	var bounds := Rect2()
	var has_bounds := false
	var pause_clear := 36.0
	var player_pos := Vector2(INF, INF)
	var peers: Array = []           ## every walker of the manager (self included; skipped)
	var rank := 0                   ## stable passing priority: the lower rank gives way first
	var view := "side"              ## "side" | "front" | "back": the view of the current walk row
	var cur_speed := 0.0            ## px/s actually walked in the last step (followers match it)
	var aside_for: Walker = null    ## the walker this one is stepping aside for
	var rng := RandomNumberGenerator.new()
	var _gs := 0.0
	var _left := false
	var _aside_clear_t := 0.0

	func setup(s: Dictionary, base_dir: String) -> bool:
		id = str(s.get("id", "walker"))
		for p in s.get("path", []):
			pts.append(LayerStack._v2(p))
		if pts.size() < 2:
			push_warning("AmbientWalkers: %s needs a path of >= 2 points" % id)
			return false
		rng.seed = int(s["seed"]) if s.has("seed") else LayerStack.name_hash(id)
		rank = LayerStack.name_hash(id)
		pingpong = str(s.get("loop", "pingpong")) != "cycle"
		speed = maxf(4.0, float(s.get("speed", 20.0)))
		give_way = maxf(0.0, float(s.get("give_way", 0.0)))
		dodge = maxf(0.0, float(s.get("dodge", 0.0)))
		pass_off = maxf(0.0, float(s.get("pass", dodge if dodge > 0.0 else 0.5)))
		peer_lane = 8.0 if dodge > 0.0 else 2.0
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
		var src := str(s.get("char", ""))
		var loaded: bool = rig.load_character(src)
		var rpath := str(s.get("rig", ""))
		var own := false
		if rpath != "" and rig.sprite != null:
			var fullr := rpath if rpath.begins_with("res://") else base_dir + "/" + rpath
			own = load_rig_sheet(rig, fullr)
			if not own:
				push_warning("AmbientWalkers: %s: missing rig %s" % [id, fullr])
		if not loaded and not own:
			push_warning("AmbientWalkers: %s: no sheet for '%s'" % [id, src])
		var vpath := str(s.get("sheet", ""))
		if vpath != "" and not own and rig.sprite != null:
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
		view = view_for(_dir(), rig)
		rig.play(_walk_row())

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
			"wait":
				_wait_tick(delta)
			_:
				_walk(delta)
		if state != "walk":
			cur_speed = 0.0
		position = base + _normal() * offset

	func _dir() -> Vector2:
		var d := pts[to_i] - pts[from_i]
		return d.normalized() if d.length() > 0.001 else Vector2.RIGHT

	func _normal() -> Vector2:
		var u := _dir()
		return Vector2(-u.y, u.x)

	## "side" | "front" | "back" for a heading: steep headings show the front / back walk when the sheet has it.
	static func view_for(u: Vector2, r: Node2D) -> String:
		if absf(u.y) > DIAG * absf(u.x):
			var v := "front" if u.y > 0.0 else "back"
			if r != null and r.has_anim("walk_" + v):
				return v
		return "side"

	func _walk_row() -> String:
		return "walk_side" if view == "side" else "walk_" + view

	func _idle_row() -> String:
		if view != "side" and rig.has_anim("idle_" + view):
			return "idle_" + view
		return "idle_side"

	func _walk(delta: float) -> void:
		var u := _dir()
		if give_way > 0.0 and _in_way(u):
			if not _try_dodge(u):
				state = "yield"
				yield_t = 0.0
				clear_t = 0.0
				rig.speed_scale = 1.0
				rig.play(_idle_row())
				if view == "side" and rig.has_anim("look_side"):
					rig.play_once("look_side", "idle_side")
				return
		elif _passed(u):
			clear_t += delta
			if clear_t > 0.5:
				offset_target = 0.0        # back onto the path once the player is behind or far away
		else:
			clear_t = 0.0
		var cap := _peers(u, delta)
		if cap <= 0.0:
			_start_wait()
			return
		var target_off := offset_target if offset_target != 0.0 else peer_target
		var spd := speed * (0.55 if absf(offset - target_off) > 0.5 else 1.0)
		if aside_for != null:
			spd *= 0.8
		spd = minf(spd, cap)
		offset = move_toward(offset, target_off, speed * 0.8 * delta)
		var target := pts[to_i]
		var step := spd * delta
		var left := base.distance_to(target)
		cur_speed = spd
		if step >= left:
			base = target
			_arrive()
			if state != "walk":
				return                     # the pause pose / the soft turn stays on screen (round 8 overwrote it)
		else:
			base += u * step
		_play_walk(_dir(), spd)

	func _play_walk(u: Vector2, spd: float) -> void:
		view = view_for(u, rig)
		var row := _walk_row()
		rig.play(row)
		var gs: float = rig.ground_speed(row)
		if gs <= 0.0:
			gs = _gs
		rig.speed_scale = clampf(spd / gs, 0.5, 2.0) if gs > 0.0 else 1.0

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

	# ------------------------------------------------------------------ other walkers
	func is_moving() -> bool:
		return state == "walk" and cur_speed > 0.5

	## The nearest other walker ahead in this walker's lane (within PEER_LOOK), or null.
	func _peer_ahead(u: Vector2) -> Walker:
		var n := Vector2(-u.y, u.x)
		var best: Walker = null
		var best_d := INF
		for o in peers:
			if o == self or not is_instance_valid(o):
				continue
			var w: Walker = o
			var rel := w.position - position
			var along := rel.dot(u)
			if along <= 0.5 or along > PEER_LOOK:
				continue
			if absf(rel.dot(n)) >= maxf(peer_lane, w.peer_lane):
				continue
			if along < best_d:
				best_d = along
				best = w
		return best

	## Free step-aside offset (along this walker's normal) that clears `o`, or NAN without room. Side lanes
	## (pass < 2 px) step backwards in depth (smaller y), oblique floors sideways away from the other walker.
	func aside_offset(o: Walker) -> float:
		if pass_off <= 0.0:
			return NAN
		var u := _dir()
		var n := Vector2(-u.y, u.x)
		var cands: Array = []
		if pass_off < 2.0:
			cands = [pass_off * (-1.0 if n.y > 0.0 else 1.0)]           # half a pixel further back
		else:
			var lat := (o.position - base).dot(n)
			cands = [-pass_off, pass_off] if lat >= 0.0 else [pass_off, -pass_off]
		for c in cands:
			if has_bounds and not bounds.has_point(base + n * float(c)):
				continue
			return float(c)
		return NAN

	## Speed cap from the other walkers (INF = free, 0 = stop and wait); starts / ends side steps.
	func _peers(u: Vector2, delta: float) -> float:
		if aside_for != null and not is_instance_valid(aside_for):
			aside_for = null
			peer_target = 0.0
		if aside_for != null:
			var rel: Vector2 = aside_for.position - position
			if rel.dot(u) < -12.0 or rel.length() > PEER_LOOK + 12.0:
				_aside_clear_t += delta
				if _aside_clear_t > 0.3:
					aside_for = null
					peer_target = 0.0
			else:
				_aside_clear_t = 0.0
		var o := _peer_ahead(u)
		if o == null:
			return INF
		if o.aside_for == self or aside_for == o:
			# one of the two makes room: pass once the step is made (slowly while it is still being made)
			var who: Walker = o if o.aside_for == self else self
			var settled := absf(who.offset - who.peer_target) < 0.25
			return INF if settled else (speed * 0.35 if (o.position - position).length() > PEER_GAP else 0.0)
		var head_on: bool = o.is_moving() and o._dir().dot(u) < -0.3
		var along := (o.position - position).dot(u)
		if not head_on and o.is_moving():
			# same way: follow at its pace, never closer than PEER_GAP
			if along < PEER_GAP:
				return 0.0
			return o.cur_speed if along < PEER_GAP + 10.0 else INF
		# head-on, or the other one stands in the lane: someone steps aside
		var mine := aside_offset(o)
		var theirs := o.aside_offset(self) if head_on else NAN
		var me_first := not head_on or rank < o.rank
		if me_first and not is_nan(mine):
			_step_aside(o, mine)
			return INF
		if not me_first and is_nan(theirs) and not is_nan(mine):
			_step_aside(o, mine)
			return INF
		if not me_first and not is_nan(theirs):
			return speed * 0.35 if along > PEER_GAP else 0.0     # the other one steps aside
		return 0.0 if along < PEER_GAP + 8.0 else speed * 0.5    # nobody has room: stop short and wait

	func _step_aside(o: Walker, off: float) -> void:
		aside_for = o
		peer_target = off
		_aside_clear_t = 0.0

	func _start_wait() -> void:
		state = "wait"
		wait_t = 0.0
		rig.speed_scale = 1.0
		rig.play(_idle_row())
		if view == "side" and rig.has_anim("look_side"):
			rig.play_once("look_side", "idle_side")

	func _wait_tick(delta: float) -> void:
		wait_t += delta
		var u := _dir()
		var o := _peer_ahead(u)
		var blocked := o != null and (o.position - position).dot(u) < PEER_GAP + 10.0 and not (o.aside_for == self \
			and absf(o.offset - o.peer_target) < 0.25)
		if not blocked and wait_t > 0.35:
			state = "walk"
			return
		var limit := PEER_TURN if o == null or rank > o.rank else 1.2
		if wait_t > limit:
			_reverse()

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

	## Turn back along the path (waited too long for the player or a blocked lane).
	func _reverse() -> void:
		var t := from_i
		from_i = to_i
		to_i = t
		offset = -offset
		offset_target = -offset_target
		peer_target = -peer_target
		state = "walk"
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
		if view != "side":
			rig.play(_idle_row())           # arrived walking toward / away from the camera: stands that way
			return
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
		var n_old := _normal()
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
		if n_old.dot(_normal()) < 0.0:
			# heading back: the side steps keep their side of the path (the normal flipped)
			offset = -offset
			offset_target = -offset_target
			peer_target = -peer_target

	func _leave_point() -> void:
		rig.play(_idle_row())
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
