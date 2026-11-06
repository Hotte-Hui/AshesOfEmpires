extends Camera2D
## World camera (TECHNICAL_ARCHITECTURE §2; render contract of round 2 in documentation/asset_manifest_parts/
## render-camera.md).
##
## `pos`   continuous top-left of the visible 640x360 world window, in world pixels (cinematics tween it).
## `drawn` what is on screen: `pos` quantised to the world viewport's pixel grid. The 2D world renders at
##         k viewport pixels per world pixel (PixelView.world_scale: 3 @1080p, 4 @1440p, 6 @2160p), so pans and
##         follows advance in single screen pixels while every texel stays a crisp k x k block.
##
## Follow model (frame-rate independent):
##  * dead zone: the target moves freely inside +-dead_zone around the follow focus (no camera twitch on small
##    steps or turns);
##  * look-ahead: after the target has committed to a walking direction (LOOK_COMMIT px), the view eases
##    `look_ahead` px ahead of it (own critically damped spring, held when the target stops);
##  * the window follows the goal with an exactly integrated critically damped spring (no overshoot, no
##    oscillation when stopping, identical result at 60/144/240/360 Hz);
##  * draw_pos_for(target): the followed actor's pixel is chosen with "minimal change" quantisation: it keeps its
##    screen pixel while that stays within TARGET_TOL screen px of the true position (camera and actor moving
##    together -> no 1-px vibration against the screen), keeps its world pixel while it stands (feet planted
##    while the camera settles) and never steps backwards against its walking direction.
## reduced_motion: tighter spring, faster/shorter look-ahead, smaller dead zone.
## In-level protagonist switch (TECHNICAL_ARCHITECTURE §12.11): retarget(actor) hands the follow to the other
## protagonist; the window glides over on its own critically damped spring (settles in `glide` s, no overshoot) and
## then simply keeps following; retarget(actor, true) cuts (reduced motion, black screen).

signal moved(top_left: Vector2)

const VIEW := Vector2(640, 360)
const LOOK_COMMIT := 10.0          ## px walked in a new direction before the look-ahead swings over
const SETTLE_EPS := 0.004          ## px; below this (and nearly at rest) the spring snaps onto its goal
const TARGET_TOL := 1.0            ## screen px the followed actor may deviate to keep its screen/world pixel

var target: Node2D = null
var bounds := Rect2(0, 0, 640, 360)
var pos := Vector2.ZERO            ## continuous top-left (world px)
var drawn := Vector2.ZERO          ## quantised top-left actually on screen
var vel := Vector2.ZERO            ## follow-spring velocity (world px/s)
var follow_offset := Vector2(0, -70)
var look_ahead := 40.0             ## px the view leads the walking direction
var dead_zone := Vector2(6, 4)     ## px of free movement around the follow focus
var smoothing := 5.2               ## follow spring angular frequency (1/s); ~1.2 s to settle
var look_smoothing := 2.1          ## look-ahead spring angular frequency (1/s)
var cinematic := false             ## true: pos is driven by a cinematic (set_top_left / tween_to)

var _look := 0.0
var _look_v := 0.0
var _dir := 0.0                    # committed walking direction (-1, 0, 1)
var _dir_travel := 0.0
var _focus := Vector2.ZERO
var _tp := Vector2.ZERO            # target visual position this frame
var _tp_prev := Vector2.INF
var _pos_prev := Vector2.ZERO
var _t_draw := Vector2.ZERO        # target's drawn position (world px, on the viewport pixel grid)
var _tq := Vector2.ZERO            # target's drawn position in viewport px (integers)
var _tq_screen := Vector2.ZERO     # _tq minus the camera's viewport px (screen pixel of the target)
var _tq_valid := false
var _tween: Tween
var _k := 1.0                      # viewport px per world px of the active render path
var _glide_w := 0.0                # > 0: spring frequency of a running switch glide (§12.11)
var _glide_dist := 0.0             # distance to the goal when the glide began (progress)


func _ready() -> void:
	anchor_mode = Camera2D.ANCHOR_MODE_FIXED_TOP_LEFT
	position_smoothing_enabled = false
	make_current()


func set_bounds(r: Rect2) -> void:
	bounds = r


func clamp_pos(p: Vector2) -> Vector2:
	var mx := maxf(bounds.position.x, bounds.end.x - VIEW.x)
	var my := maxf(bounds.position.y, bounds.end.y - VIEW.y)
	return Vector2(clampf(p.x, bounds.position.x, mx), clampf(p.y, bounds.position.y, my))


## Goal top-left of the follow (dead-zone focus + eased look-ahead), clamped to the bounds.
func desired() -> Vector2:
	if not _has_target():
		return pos
	return clamp_pos(_focus + follow_offset + Vector2(_look, 0.0) - VIEW * 0.5)


func snap_now() -> void:
	if _has_target():
		_tp = _target_pos()
		_tp_prev = _tp
		_focus = _tp
	_look = 0.0
	_look_v = 0.0
	_dir = 0.0
	_dir_travel = 0.0
	_glide_w = 0.0
	pos = desired()
	vel = Vector2.ZERO
	_pos_prev = pos
	_tq_valid = false
	_apply()
	_update_target_draw(0.0)


func set_top_left(p: Vector2, clamp_to_bounds := true) -> void:
	_kill_tween()
	pos = clamp_pos(p) if clamp_to_bounds else p
	vel = Vector2.ZERO
	_pos_prev = pos
	_apply()
	_update_target_draw(0.0)


## Cinematic move of the visible window's top-left. Returns the tween (await tween.finished).
## Sub-pixel smooth: the window advances in single screen pixels (1/k world px).
func tween_to(p: Vector2, duration: float, trans := Tween.TRANS_SINE) -> Tween:
	cinematic = true
	_kill_tween()
	vel = Vector2.ZERO
	_tween = create_tween().set_trans(trans).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(self, "pos", clamp_pos(p), maxf(0.01, duration))
	return _tween


## Back to following: the spring eases from wherever the cinematic left the window (a running tween_to is
## stopped so it cannot fight the follow).
func release() -> void:
	_kill_tween()
	cinematic = false
	vel = Vector2.ZERO
	if _has_target():
		_tp = _target_pos()
		_tp_prev = _tp
		_focus = _tp


## Hands the follow to another actor (§12.11 in-level protagonist switch). The window glides from where it is to the
## new target on a critically damped spring that has covered 99 % of the way after `glide` s ((1 + wt)·e^-wt = 1 %
## at wt = 6.64); look-ahead, dead zone and the target's pixel lock start fresh. cut = snap at once.
func retarget(t: Node2D, cut := false, glide := 1.2) -> void:
	_kill_tween()
	cinematic = false
	target = t
	vel = Vector2.ZERO
	_look = 0.0
	_look_v = 0.0
	_dir = 0.0
	_dir_travel = 0.0
	_tq_valid = false
	_glide_w = 0.0
	_glide_dist = 0.0
	if not _has_target():
		return
	_tp = _target_pos()
	_tp_prev = _tp
	_focus = _tp
	if cut:
		snap_now()
		return
	_glide_dist = (desired() - pos).length()
	if _glide_dist > 0.5:
		_glide_w = 6.64 / maxf(0.2, glide)


## True while a switch glide (retarget without cut) has not settled yet.
func is_gliding() -> bool:
	return _glide_w > 0.0


## 0…1: share of the way the running switch glide has covered (1 when none runs).
func glide_progress() -> float:
	if _glide_w <= 0.0 or _glide_dist <= 0.5:
		return 1.0
	return clampf(1.0 - (desired() - pos).length() / _glide_dist, 0.0, 1.0)


func top_left() -> Vector2:
	return drawn


## Viewport pixels per world pixel of the active render path (3 @1080p ... 6 @2160p; 1 in the 3D low-res path).
func px_scale() -> float:
	return _k


## Where the followed actor must be drawn this frame (world px, on the viewport pixel grid); other nodes get
## their own `visual` position back. Called by the player after the camera has processed (same frame).
func draw_pos_for(node: Node, visual: Vector2) -> Vector2:
	if node == target and not cinematic and _k > 1.0:
		return _t_draw
	return visual


## Re-applies zoom/position after a render-path change (PixelView calls it).
func refresh() -> void:
	_tq_valid = false
	_apply()
	_update_target_draw(0.0)


func _kill_tween() -> void:
	if _tween and _tween.is_valid():
		_tween.kill()
	_tween = null
	_glide_w = 0.0                     # a cinematic move or a new hand-over ends a running switch glide


func _has_target() -> bool:
	return target != null and is_instance_valid(target) and target.is_inside_tree()


func _target_pos() -> Vector2:
	if target.has_method("get_visual_position"):
		return target.get_visual_position()
	return target.global_position


func _process(delta: float) -> void:
	if _has_target():
		_tp = _target_pos()
	if not cinematic:
		_update_follow(delta)
	_apply()
	_update_target_draw(delta)
	_pos_prev = pos
	_tp_prev = _tp


## Exact step of a critically damped spring x'' = -w^2 (x - g) - 2 w x' over dt (goal constant over the step).
static func spring_step(x: float, v: float, g: float, w: float, dt: float) -> Vector2:
	var d := x - g
	var e := exp(-w * dt)
	var t1 := (v + w * d) * dt
	return Vector2(g + (d + t1) * e, (v - w * t1) * e)


func _update_follow(delta: float) -> void:
	if delta <= 0.0:
		return
	var rm := bool(Settings.get_value("reduced_motion"))
	var w := smoothing * (2.0 if rm else 1.0)
	if _glide_w > 0.0:
		w = _glide_w
	var wl := look_smoothing * (2.2 if rm else 1.0)
	var la := look_ahead * (0.6 if rm else 1.0)
	var dz := dead_zone * (0.6 if rm else 1.0)
	if _has_target():
		# dead zone: drag the focus only when the target leaves it
		for a in 2:
			if _tp[a] > _focus[a] + dz[a]:
				_focus[a] = _tp[a] - dz[a]
			elif _tp[a] < _focus[a] - dz[a]:
				_focus[a] = _tp[a] + dz[a]
		# look-ahead direction commitment (ignores small back-steps and turning on the spot)
		if _tp_prev.x != INF:
			var dx := _tp.x - _tp_prev.x
			if absf(dx) > 0.0001:
				var s := signf(dx)
				if s == _dir:
					_dir_travel = 0.0
				else:
					_dir_travel += absf(dx)
					if _dir_travel >= LOOK_COMMIT:
						_dir = s
						_dir_travel = 0.0
		var ls := spring_step(_look, _look_v, _dir * la, wl, delta)
		_look = ls.x
		_look_v = ls.y
	var g := desired()
	for a in 2:
		var r := spring_step(pos[a], vel[a], g[a], w, delta)
		pos[a] = r.x
		vel[a] = r.y
		if absf(pos[a] - g[a]) < SETTLE_EPS and absf(vel[a]) < 0.05:
			pos[a] = g[a]
			vel[a] = 0.0
	var c := clamp_pos(pos)
	if c.x != pos.x:
		vel.x = 0.0
	if c.y != pos.y:
		vel.y = 0.0
	pos = c
	if _glide_w > 0.0 and pos == g and vel == Vector2.ZERO:
		_glide_w = 0.0                 # the switch glide has arrived: plain following from here on


func _apply() -> void:
	var view = Game.view
	var hires: bool = view != null and view.has_method("is_hires") and view.is_hires()
	var k: float = float(view.get("world_scale")) if hires else 1.0
	_k = k
	var draw: Vector2
	if hires:
		draw = (pos * k + Vector2(0.5, 0.5)).floor() / k
		if zoom != Vector2(k, k):
			zoom = Vector2(k, k)
		position = draw - Vector2.ONE             # 1 world px overscan margin (PixelView.MARGIN)
	else:
		# 642x362 low-res path (3D levels / legacy world captures): pixel-locked gameplay, sub-pixel remainder of
		# cinematic moves shown as a display offset.
		draw = pos if cinematic else pos.round()
		if zoom != Vector2.ONE:
			zoom = Vector2.ONE
		var fl := draw.floor()
		position = fl - Vector2.ONE
		if enabled and view and view.has_method("set_fraction"):
			view.set_fraction(draw - fl)
	drawn = draw
	moved.emit(draw)


## Quantise the followed actor (see class doc), per axis, in viewport pixels.
func _update_target_draw(delta: float) -> void:
	if not _has_target():
		return
	var k := _k
	if k <= 1.0:
		_t_draw = _tp
		_tq_valid = false
		return
	var cq := (drawn * k + Vector2(0.5, 0.5)).floor()
	for a in 2:
		var pk: float = _tp[a] * k
		var world_px := floorf(pk + 0.5)
		var q := world_px
		if _tq_valid and not cinematic:
			var prev: float = _tq[a]
			var vp := 0.0
			if delta > 0.0 and _tp_prev.x != INF:
				vp = (_tp[a] - _tp_prev[a]) / delta
			if absf(vp) < 0.5:
				# standing: keep the world pixel (feet planted while the camera settles)
				q = prev if absf(prev - pk) <= TARGET_TOL else world_px
			else:
				var dirn := signf(vp)
				var keep: float = cq[a] + _tq_screen[a]       # same screen pixel as last frame
				if absf(keep - pk) <= TARGET_TOL and (keep - prev) * dirn >= 0.0:
					q = keep
				else:
					q = world_px
					if (q - prev) * dirn < 0.0 and absf(prev - pk) <= TARGET_TOL + 0.5:
						q = prev                         # never step back against the walking direction
		_tq[a] = q
		_tq_screen[a] = q - cq[a]
		_t_draw[a] = q / k
	_tq_valid = true
