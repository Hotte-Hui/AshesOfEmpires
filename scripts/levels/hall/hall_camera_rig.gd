extends RefCounted
## Camera path for LS_M1_Hall (owner: great_hall_3d).
## The camera NEVER rotates: verticals stay perfectly vertical and the facade of the hall stays parallel to
## the image plane (1-point perspective -> crisp pixel columns for the pilaster rhythm).  "Tilts" are done
## with a lens shift (Camera3D frustum offset), "crane" and "push" with translation only.
## Position: cubic Hermite through keys with explicit velocities.  Lens shift: smoothstep between keys.

const FOV_Y := 24.0          ## vertical field of view in degrees (art direction: <= 30)
const NEAR := 0.05
const FAR := 9000.0

## t (s), position (m), velocity (m/s), lens shift in pixels (+y = horizon moves down on screen)
var keys: Array = [
	{"t": 0.0, "p": Vector3(-7.0, 7.78, 2.95), "v": Vector3(0.0, 0.0, 0.0), "shift": Vector2(0, -30)},
	{"t": 0.6, "p": Vector3(-7.0, 7.95, 2.45), "v": Vector3(0.0, 0.45, -1.8), "shift": Vector2(0, -14)},
	{"t": 1.4, "p": Vector3(-7.2, 7.75, -1.2), "v": Vector3(-0.6, -2.0, -6.2), "shift": Vector2(0, 24)},
	{"t": 3.0, "p": Vector3(-8.75, 2.05, -17.9), "v": Vector3(-0.03, -0.12, -0.42), "shift": Vector2(0, 56)},
	{"t": 8.0, "p": Vector3(-8.88, 1.92, -19.3), "v": Vector3(-0.01, -0.01, -0.2), "shift": Vector2(0, 56)},
	{"t": 11.0, "p": Vector3(-8.9, 1.9, -20.0), "v": Vector3(0.0, 0.0, 0.0), "shift": Vector2(0, 56)},
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
	# Whole-pixel lens shift: the painted sky matte then moves in whole pixels only.
	shift = shift.round()
	cam.frustum_offset = Vector2(shift.x, shift.y) * px
	cam.global_transform = Transform3D(Basis.IDENTITY, pos)
	cur_pos = pos
	cur_shift = shift
	cur_vp = vp_size
	return {"pos": pos, "shift": shift}


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
