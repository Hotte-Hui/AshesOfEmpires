extends RefCounted
## Camera path for LS_M1_Hall (owner: great_hall_3d; round 3 timing: hall-fix).
## The camera NEVER rotates: verticals stay perfectly vertical and the facade of the hall stays parallel to
## the image plane (1-point perspective -> crisp pixel columns for the pilaster rhythm).  "Tilts" are done
## with a lens shift (Camera3D frustum offset), "crane" and "push" with translation only.
## Position: cubic Hermite through keys with explicit velocities.  Lens shift: smoothstep between keys.
## Smoothness (render-camera): the lens shift is applied in whole low-res pixels (the painted sky matte stays
## on the pixel grid) and the sub-pixel remainder is presented as a display offset of the world view
## (PixelView.set_fraction in the 642x362 path) -> tilts glide at screen resolution instead of stepping by
## 3/6 screen pixels. `cur_fraction` holds the offset that was presented (world px, PixelView convention).

const FOV_Y := 24.0          ## vertical field of view in degrees (art direction: <= 30)
const NEAR := 0.05
const FAR := 9000.0

## t (s), position (m), velocity (m/s), lens shift in pixels (+y = horizon moves down on screen)
## Round 3 (user: "imposanter Auftritt, länger"): 24 s instead of 11 s.
##   h1  0.0– 5.5  the same crane path, 1.83x slower (velocities scaled accordingly)
##   h2  5.5–14.5  long establishing hold: the camera nearly stops (drift ~0.01-0.1 m/s), the plaza life plays out
##   h3 14.5–21.5  slow push (1.5 m), the camera sinks 0.3 m and tilts up by 28 px (lens shift 62 -> 90): a low-angle
##                 reveal that ends with the whole dome AND the crowning eagle inside the game's 2.39:1 letterbox
##                 (bars hide world rows 0-45 and 315-361): eagle top ~ row 50, the family's feet ~ row 309
##       21.5–24.0  held monumental final frame (same x/z as round 2 -> facade calibration unchanged)
var keys: Array = [
	{"t": 0.0, "p": Vector3(-7.0, 7.78, 2.95), "v": Vector3(0.0, 0.0, 0.0), "shift": Vector2(0, -30)},
	{"t": 1.1, "p": Vector3(-7.0, 7.95, 2.45), "v": Vector3(0.0, 0.245, -0.98), "shift": Vector2(0, -14)},
	{"t": 2.57, "p": Vector3(-7.2, 7.75, -1.2), "v": Vector3(-0.33, -1.09, -3.38), "shift": Vector2(0, 24)},
	{"t": 5.5, "p": Vector3(-8.75, 2.05, -17.9), "v": Vector3(-0.01, -0.03, -0.23), "shift": Vector2(0, 62)},
	{"t": 14.5, "p": Vector3(-8.82, 1.95, -18.5), "v": Vector3(-0.004, -0.008, -0.09), "shift": Vector2(0, 62)},
	{"t": 21.5, "p": Vector3(-8.9, 1.65, -20.0), "v": Vector3(0.0, 0.0, 0.0), "shift": Vector2(0, 90)},
	{"t": 24.0, "p": Vector3(-8.9, 1.65, -20.0), "v": Vector3(0.0, 0.0, 0.0), "shift": Vector2(0, 90)},
]


func duration() -> float:
	return float(keys[keys.size() - 1]["t"])


static func _hermite(p0: Vector3, v0: Vector3, p1: Vector3, v1: Vector3, dt: float, s: float) -> Vector3:
	var s2 := s * s
	var s3 := s2 * s
	var h00 := 2.0 * s3 - 3.0 * s2 + 1.0
	var h10 := s3 - 2.0 * s2 + s
	var h01 := -2.0 * s3 + 3.0 * s2
	var h11 := s3 - s2
	return p0 * h00 + v0 * (h10 * dt) + p1 * h01 + v1 * (h11 * dt)


## Returns {"pos": Vector3, "shift": Vector2}
func sample(t: float) -> Dictionary:
	t = clampf(t, 0.0, duration())
	var i := 0
	while i < keys.size() - 2 and t > float(keys[i + 1]["t"]):
		i += 1
	var a: Dictionary = keys[i]
	var b: Dictionary = keys[i + 1]
	var dt: float = float(b["t"]) - float(a["t"])
	var s: float = clampf((t - float(a["t"])) / dt, 0.0, 1.0)
	var pos := _hermite(a["p"], a["v"], b["p"], b["v"], dt, s)
	var ss := s * s * (3.0 - 2.0 * s)
	var shift: Vector2 = (a["shift"] as Vector2).lerp(b["shift"], ss)
	return {"pos": pos, "shift": shift}


## Frustum height at the near plane for the configured FOV.
static func frustum_size() -> float:
	return 2.0 * NEAR * tan(deg_to_rad(FOV_Y) * 0.5)


## Focal length in pixels for a viewport of height vh.
static func focal_px(vh: float) -> float:
	return (vh * 0.5) / tan(deg_to_rad(FOV_Y) * 0.5)


## Last applied state (used by the analytic projection helpers below).
var cur_pos := Vector3.ZERO
var cur_shift := Vector2.ZERO
var cur_vp := Vector2(640, 360)
var cur_fraction := Vector2.ZERO


func apply(cam: Camera3D, t: float, vp_size: Vector2) -> Dictionary:
	var smp := sample(t)
	return apply_pose(cam, smp["pos"], smp["shift"], vp_size)


func apply_pose(cam: Camera3D, pos: Vector3, shift: Vector2, vp_size: Vector2) -> Dictionary:
	var size := frustum_size()
	cam.projection = Camera3D.PROJECTION_FRUSTUM
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	cam.near = NEAR
	cam.far = FAR
	cam.size = size
	var px := size / maxf(vp_size.y, 1.0)          # world units per pixel on the near plane
	# Whole-pixel lens shift: the painted sky matte then moves in whole pixels only; the remainder goes to the
	# display. Content displacement of a shift s is (-s.x, +s.y) px; PixelView.set_fraction(f) moves the
	# picture by -f, so f = (r.x, -r.y) for the remainder r.
	var whole := shift.round()
	var rem := shift - whole
	cam.frustum_offset = Vector2(whole.x, whole.y) * px
	cam.global_transform = Transform3D(Basis.IDENTITY, pos)
	cur_pos = pos
	cur_shift = whole
	cur_vp = vp_size
	cur_fraction = Vector2(rem.x, -rem.y)
	_present_fraction(cam, cur_fraction)
	return {"pos": pos, "shift": whole, "fraction": cur_fraction}


## Hands the sub-pixel remainder to the game's world view when this camera renders the low-res world viewport
## (no-op in test harnesses with their own SubViewport).
static func _present_fraction(cam: Camera3D, f: Vector2) -> void:
	if cam == null or not cam.is_inside_tree():
		return
	var game := cam.get_node_or_null("/root/Game")
	if game == null:
		return
	var view = game.get("view")
	var world = game.get("world")
	if view == null or world == null or cam.get_viewport() != world:
		return
	if view.has_method("is_hires") and view.is_hires():
		return
	if view.has_method("set_fraction"):
		view.set_fraction(f)


## Analytic projection for the un-rotated off-axis camera (Camera3D.project_position ignores the
## frustum offset, so we do the maths ourselves).  Returns Vector3(screen_x, screen_y, depth) with
## screen coordinates in viewport pixels, top-left origin.
func project(w: Vector3) -> Vector3:
	var v := w - cur_pos
	var depth := -v.z
	if depth <= 1e-4:
		return Vector3(-1e6, -1e6, depth)
	var f := focal_px(cur_vp.y)
	var sx := cur_vp.x * 0.5 - cur_shift.x + v.x / depth * f
	var sy := cur_vp.y * 0.5 + cur_shift.y - v.y / depth * f
	return Vector3(sx, sy, depth)


func unproject(sx: float, sy: float, depth: float) -> Vector3:
	var f := focal_px(cur_vp.y)
	var x := (sx - cur_vp.x * 0.5 + cur_shift.x) / f * depth
	var y := (cur_vp.y * 0.5 + cur_shift.y - sy) / f * depth
	return cur_pos + Vector3(x, y, -depth)


## World size of one screen pixel at a given depth.
func pixel_size_at(depth: float) -> float:
	return depth / focal_px(cur_vp.y)
