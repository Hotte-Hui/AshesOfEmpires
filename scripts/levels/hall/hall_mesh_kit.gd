extends RefCounted
## Procedural mesh kit for the Great Hall reveal (owner: great_hall_3d).
## Collects flat-shaded primitives into one SurfaceTool per material bucket; `commit()` returns an ArrayMesh.
## Conventions: metres, +Y up, the camera looks along -Z.  Godot front faces are wound clockwise.
## Colours are given in sRGB (palette hex) and converted to linear here; UV2.x carries emission (0..1).

var st := SurfaceTool.new()
var primitive := Mesh.PRIMITIVE_TRIANGLES
var count := 0
## Local -> world transform applied to every emitted vertex (lets builders work in a local frame).
var xf := Transform3D.IDENTITY


func _init(p_primitive: int = Mesh.PRIMITIVE_TRIANGLES) -> void:
	primitive = p_primitive
	st.begin(primitive)


func _v(p: Vector3, n: Vector3, col: Color, uv: Vector2, em: float) -> void:
	p = xf * p
	n = (xf.basis * n).normalized()
	st.set_normal(n)
	st.set_color(col)
	st.set_uv(uv)
	st.set_uv2(Vector2(em, 0.0))
	st.add_vertex(p)
	count += 1


## Quad from four corners given clockwise as seen from the front (bl, tl, tr, br).
func quad(bl: Vector3, tl: Vector3, tr: Vector3, br: Vector3, col: Color, em: float = 0.0,
		uv_scale: Vector2 = Vector2.ONE) -> void:
	var n := (tl - bl).cross(br - bl).normalized()
	n = -n
	var c := col.srgb_to_linear()
	var uvs := [Vector2(0, 1), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)]
	for i in 4:
		uvs[i] = uvs[i] * uv_scale
	_v(bl, n, c, uvs[0], em)
	_v(tl, n, c, uvs[1], em)
	_v(tr, n, c, uvs[2], em)
	_v(bl, n, c, uvs[0], em)
	_v(tr, n, c, uvs[2], em)
	_v(br, n, c, uvs[3], em)


## Rectangle face: centre, outward normal, up vector, half width, half height.
func face(c: Vector3, n: Vector3, up: Vector3, hw: float, hh: float, col: Color, em: float = 0.0,
		uv_scale: Vector2 = Vector2.ONE) -> void:
	n = n.normalized()
	up = up.normalized()
	var r := up.cross(n).normalized() * hw
	var u := up * hh
	quad(c - r - u, c - r + u, c + r + u, c + r - u, col, em, uv_scale)


const FACE_PX := 1
const FACE_NX := 2
const FACE_PY := 4
const FACE_NY := 8
const FACE_PZ := 16
const FACE_NZ := 32
const FACES_ALL := 63
const FACES_NO_BOTTOM := 63 & ~8


## Axis-aligned box from min corner and size.  `cols` may be a single Color or a Dictionary
## {"top": Color, "side": Color, "front": Color, "bottom": Color} for per-face tones.
func box(mn: Vector3, size: Vector3, cols, faces: int = FACES_NO_BOTTOM, em: float = 0.0) -> void:
	var h := size * 0.5
	var c := mn + h
	var top: Color
	var side: Color
	var front: Color
	var bottom: Color
	if cols is Dictionary:
		front = cols.get("front", Color.WHITE)
		side = cols.get("side", front)
		top = cols.get("top", front)
		bottom = cols.get("bottom", side)
	else:
		front = cols
		side = cols
		top = cols
		bottom = cols
	if faces & FACE_PZ:
		face(c + Vector3(0, 0, h.z), Vector3.BACK, Vector3.UP, h.x, h.y, front, em)
	if faces & FACE_NZ:
		face(c - Vector3(0, 0, h.z), Vector3.FORWARD, Vector3.UP, h.x, h.y, front, em)
	if faces & FACE_PX:
		face(c + Vector3(h.x, 0, 0), Vector3.RIGHT, Vector3.UP, h.z, h.y, side, em)
	if faces & FACE_NX:
		face(c - Vector3(h.x, 0, 0), Vector3.LEFT, Vector3.UP, h.z, h.y, side, em)
	if faces & FACE_PY:
		face(c + Vector3(0, h.y, 0), Vector3.UP, Vector3.FORWARD, h.x, h.z, top, em)
	if faces & FACE_NY:
		face(c - Vector3(0, h.y, 0), Vector3.DOWN, Vector3.BACK, h.x, h.z, bottom, em)


## Box centred on the XZ footprint (x, z) standing on y0.
func pillar(x: float, z: float, y0: float, w: float, d: float, hgt: float, cols,
		faces: int = FACES_NO_BOTTOM) -> void:
	box(Vector3(x - w * 0.5, y0, z - d * 0.5), Vector3(w, hgt, d), cols, faces)


## Oriented box: centre, basis (columns = local axes, unit), half extents.
func obox(c: Vector3, basis: Basis, h: Vector3, col, faces: int = FACES_ALL) -> void:
	var ax := basis.x.normalized()
	var ay := basis.y.normalized()
	var az := basis.z.normalized()
	var front: Color = col if col is Color else col.get("front", Color.WHITE)
	var side: Color = col if col is Color else col.get("side", front)
	var top: Color = col if col is Color else col.get("top", front)
	if faces & FACE_PZ:
		face(c + az * h.z, az, ay, h.x, h.y, front)
	if faces & FACE_NZ:
		face(c - az * h.z, -az, ay, h.x, h.y, front)
	if faces & FACE_PX:
		face(c + ax * h.x, ax, ay, h.z, h.y, side)
	if faces & FACE_NX:
		face(c - ax * h.x, -ax, ay, h.z, h.y, side)
	if faces & FACE_PY:
		face(c + ay * h.y, ay, -az, h.x, h.z, top)
	if faces & FACE_NY:
		face(c - ay * h.y, -ay, az, h.x, h.z, top)


## Lathe (surface of revolution around the Y axis through `centre`).  profile: Array of Vector2(r, y)
## from bottom to top.  Flat-shaded facets (pixel-art friendly banding).  a0/a1 in radians, 0 = +X.
func lathe(centre: Vector3, profile: Array, segments: int, col_fn: Callable, a0: float = 0.0,
		a1: float = TAU) -> void:
	for i in segments:
		var t0 := a0 + (a1 - a0) * float(i) / segments
		var t1 := a0 + (a1 - a0) * float(i + 1) / segments
		var d0 := Vector3(cos(t0), 0.0, sin(t0))
		var d1 := Vector3(cos(t1), 0.0, sin(t1))
		for j in profile.size() - 1:
			var pa: Vector2 = profile[j]
			var pb: Vector2 = profile[j + 1]
			var b0 := centre + d0 * pa.x + Vector3(0, pa.y, 0)
			var b1 := centre + d1 * pa.x + Vector3(0, pa.y, 0)
			var u0 := centre + d0 * pb.x + Vector3(0, pb.y, 0)
			var u1 := centre + d1 * pb.x + Vector3(0, pb.y, 0)
			var col: Color = col_fn.call(i, j)
			# outward facing: seen from outside, bottom-left=b1 (angle grows to the left when seen
			# from outside because +angle runs from +X towards +Z)
			if pb.x < 0.001:
				_tri(b1, u0, b0, col)
			else:
				quad(b1, u1, u0, b0, col)


func _tri(a: Vector3, b: Vector3, c: Vector3, col: Color, em: float = 0.0) -> void:
	var n := -((b - a).cross(c - a)).normalized()
	var lc := col.srgb_to_linear()
	_v(a, n, lc, Vector2.ZERO, em)
	_v(b, n, lc, Vector2(0, 1), em)
	_v(c, n, lc, Vector2(1, 1), em)


func tri(a: Vector3, b: Vector3, c: Vector3, col: Color, em: float = 0.0) -> void:
	_tri(a, b, c, col, em)


## Line segment (PRIMITIVE_LINES kits only).
func seg(a: Vector3, b: Vector3, col: Color) -> void:
	var c := col.srgb_to_linear()
	_v(a, Vector3.UP, c, Vector2.ZERO, 0.0)
	_v(b, Vector3.UP, c, Vector2.ZERO, 0.0)


## Sagging cable between two points (PRIMITIVE_LINES kits only).
func cable(a: Vector3, b: Vector3, sag: float, col: Color, steps: int = 0) -> void:
	var n := steps if steps > 0 else maxi(2, int(a.distance_to(b) / 1.5))
	var prev := a
	for i in range(1, n + 1):
		var t := float(i) / n
		var p := a.lerp(b, t) + Vector3(0, -sag * 4.0 * t * (1.0 - t), 0)
		seg(prev, p, col)
		prev = p


func commit(mesh: ArrayMesh = null) -> ArrayMesh:
	if count == 0:
		return mesh
	return st.commit(mesh)
