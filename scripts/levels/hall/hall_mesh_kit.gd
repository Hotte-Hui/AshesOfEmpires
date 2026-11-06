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


## Quad with an explicit UV rectangle (uv0 = top-left, uv1 = bottom-right in texture space); corners clockwise
## as seen from the front (bl, tl, tr, br).  Used for atlas regions (silhouettes, kiosk display, signs).
func quad_uv(bl: Vector3, tl: Vector3, tr: Vector3, br: Vector3, col: Color, uv0: Vector2, uv1: Vector2,
		em: float = 0.0) -> void:
	var n := -((tl - bl).cross(br - bl)).normalized()
	var c := col.srgb_to_linear()
	var a := Vector2(uv0.x, uv1.y)
	var b := uv0
	var d := Vector2(uv1.x, uv0.y)
	var e := uv1
	_v(bl, n, c, a, em)
	_v(tl, n, c, b, em)
	_v(tr, n, c, d, em)
	_v(bl, n, c, a, em)
	_v(tr, n, c, d, em)
	_v(br, n, c, e, em)


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


# ---------------------------------------------------------------------------------------------------------------
# Helpers added for the parade set (vehicles, tribune, barrier; owner: parade).  Pure additions: every function
# above keeps its behaviour.  All of them emit through quad()/_tri()/_v() and therefore honour `xf`.

## Quad from corners a, b, c, d (in order around the face, either winding) flipped if needed so that its normal
## points along `out`.  UVs are 0 (untextured).
func quad_out(a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color, out: Vector3, em: float = 0.0) -> void:
	var n := -((b - a).cross(d - a))
	if n.dot(out) < 0.0:
		quad(d, c, b, a, col, em, Vector2.ZERO)
	else:
		quad(a, b, c, d, col, em, Vector2.ZERO)


## Triangle facing `out` (winding fixed automatically).
func tri_out(a: Vector3, b: Vector3, c: Vector3, col: Color, out: Vector3, em: float = 0.0) -> void:
	var n := -((b - a).cross(c - a))
	if n.dot(out) < 0.0:
		_tri(a, c, b, col, em)
	else:
		_tri(a, b, c, col, em)


## Triangle with explicit UVs, facing `out`.
func tri_uv_out(a: Vector3, b: Vector3, c: Vector3, ua: Vector2, ub: Vector2, uc: Vector2, col: Color,
		out: Vector3, em: float = 0.0) -> void:
	var n := -((b - a).cross(c - a))
	if n.dot(out) < 0.0:
		var t := b
		b = c
		c = t
		var tu := ub
		ub = uc
		uc = tu
		n = -n
	n = n.normalized()
	var lc := col.srgb_to_linear()
	_v(a, n, lc, ua, em)
	_v(b, n, lc, ub, em)
	_v(c, n, lc, uc, em)


## Points of an ellipse around `c` in the plane of the unit vectors u, v (radii ru, rv), n points from angle a0.
static func ring(c: Vector3, u: Vector3, v: Vector3, ru: float, rv: float, n: int, a0: float = 0.0) -> Array:
	var pts: Array = []
	for i in n:
		var a := a0 + TAU * float(i) / n
		pts.append(c + u * (cos(a) * ru) + v * (sin(a) * rv))
	return pts


static func centroid(pts: Array) -> Vector3:
	var s := Vector3.ZERO
	for p in pts:
		s += p
	return s / maxf(pts.size(), 1)


## Loft through closed rings (Arrays of Vector3 with equal counts).  Band faces point away from the line through
## the ring centroids; caps (fans) close the first / last ring.  cols: a Color, or an Array with one Color per
## band (rings.size() - 1); cap_col: a Color, or null (= the adjacent band's colour).
func loft(rings: Array, cols, cap0: bool = false, cap1: bool = false, cap_col = null) -> void:
	var nr := rings.size()
	if nr < 2:
		return
	var cens: Array = []
	for r in rings:
		cens.append(centroid(r))
	for j in nr - 1:
		var r0: Array = rings[j]
		var r1: Array = rings[j + 1]
		var col: Color = cols if cols is Color else cols[mini(j, cols.size() - 1)]
		var c0: Vector3 = cens[j]
		var ax: Vector3 = cens[j + 1] - c0
		var n := r0.size()
		for i in n:
			var a: Vector3 = r0[i]
			var b: Vector3 = r0[(i + 1) % n]
			var cc: Vector3 = r1[(i + 1) % n]
			var d: Vector3 = r1[i]
			var mid := (a + b + cc + d) * 0.25
			var t := 0.5
			if ax.length_squared() > 1e-10:
				t = clampf((mid - c0).dot(ax) / ax.length_squared(), 0.0, 1.0)
			var out := mid - (c0 + ax * t)
			if out.length_squared() < 1e-12:
				out = ax
			quad_out(a, d, cc, b, col, out)
	for k in 2:
		if (k == 0 and not cap0) or (k == 1 and not cap1):
			continue
		var r: Array = rings[0] if k == 0 else rings[nr - 1]
		var cen: Vector3 = cens[0] if k == 0 else cens[nr - 1]
		var other: Vector3 = cens[1] if k == 0 else cens[nr - 2]
		var col2: Color
		if cap_col is Color:
			col2 = cap_col
		elif cols is Color:
			col2 = cols
		else:
			col2 = cols[0] if k == 0 else cols[cols.size() - 1]
		var out2 := cen - other
		for i in r.size():
			tri_out(cen, r[i], r[(i + 1) % r.size()], col2, out2)


## Truncated cone / n-sided prism from a to b (radius ra at a, rb at b).  `up` orients the first facet.
func cyl(a: Vector3, b: Vector3, ra: float, rb: float, n: int, col, caps: bool = true,
		up: Vector3 = Vector3.UP, a0: float = 0.0) -> void:
	var ax := (b - a).normalized()
	var u := up - ax * up.dot(ax)
	if u.length_squared() < 1e-6:
		u = Vector3.RIGHT - ax * ax.x
	u = u.normalized()
	var v := ax.cross(u).normalized()
	loft([ring(a, u, v, ra, ra, n, a0), ring(b, u, v, rb, rb, n, a0)], col, caps, caps)


## Box between two points (beam, strap, cable piece): cross-section w (sideways) x h (along `up`).
func beam(a: Vector3, b: Vector3, w: float, h: float, col, up: Vector3 = Vector3.UP) -> void:
	var ax := b - a
	var l := ax.length()
	if l < 1e-5:
		return
	ax /= l
	var u := up - ax * up.dot(ax)
	if u.length_squared() < 1e-6:
		u = Vector3.FORWARD - ax * ax.dot(Vector3.FORWARD)
	if u.length_squared() < 1e-6:
		u = Vector3.RIGHT - ax * ax.dot(Vector3.RIGHT)
	u = u.normalized()
	var s := u.cross(ax).normalized()
	obox((a + b) * 0.5, Basis(s, u, ax), Vector3(w * 0.5, h * 0.5, l * 0.5), col)


## Chain of beams through `pts` (cables, straps, rails); `closed` joins the last point to the first.
func polyline(pts: Array, w: float, h: float, col, up: Vector3 = Vector3.UP, closed: bool = false) -> void:
	var n := pts.size()
	for i in (n if closed else n - 1):
		beam(pts[i], pts[(i + 1) % n], w, h, col, up)


## Prism: simple polygon `pts` (Vector2 in the u/v plane through o; convex, or star-shaped around its centroid)
## extruded along the unit vector w from w0 to w1.  cols: Color or {"front": caps, "side": walls, "top": walls
## facing up}.  Either winding; walls face away from the centroid, caps face -w / +w.
func prism(pts: Array, o: Vector3, u: Vector3, v: Vector3, w: Vector3, w0: float, w1: float, cols,
		caps: bool = true) -> void:
	var cap_c: Color = cols if cols is Color else cols.get("front", Color.WHITE)
	var side_c: Color = cols if cols is Color else cols.get("side", cap_c)
	var top_c: Color = cols if cols is Color else cols.get("top", side_c)
	var n := pts.size()
	var cen2 := Vector2.ZERO
	for p in pts:
		cen2 += p
	cen2 /= n
	var p0s: Array = []
	var p1s: Array = []
	for p in pts:
		var q: Vector2 = p
		p0s.append(o + u * q.x + v * q.y + w * w0)
		p1s.append(o + u * q.x + v * q.y + w * w1)
	for i in n:
		var a2: Vector2 = pts[i]
		var b2: Vector2 = pts[(i + 1) % n]
		var e := b2 - a2
		var nn := Vector2(e.y, -e.x)
		if nn.dot((a2 + b2) * 0.5 - cen2) < 0.0:
			nn = -nn
		var out := (u * nn.x + v * nn.y).normalized()
		var col: Color = top_c if out.dot(Vector3.UP) > 0.55 else side_c
		quad_out(p0s[i], p1s[i], p1s[(i + 1) % n], p0s[(i + 1) % n], col, out)
	if caps:
		var c0 := o + u * cen2.x + v * cen2.y
		for i in n:
			tri_out(c0 + w * w0, p0s[i], p0s[(i + 1) % n], cap_c, -w)
			tri_out(c0 + w * w1, p1s[i], p1s[(i + 1) % n], cap_c, w)


## Disc (polygon fan) with UVs from an atlas rectangle: centre, normal, up (texture top), radius, sides.
func disc_uv(c: Vector3, n: Vector3, up: Vector3, r: float, sides: int, col: Color, uvr: Rect2,
		em: float = 0.0, a0: float = 0.0) -> void:
	n = n.normalized()
	var v := (up - n * up.dot(n)).normalized()
	var u := v.cross(n).normalized()
	var cuv := uvr.position + uvr.size * 0.5
	for i in sides:
		var t0 := a0 + TAU * float(i) / sides
		var t1 := a0 + TAU * float(i + 1) / sides
		var p0 := c + (u * cos(t0) + v * sin(t0)) * r
		var p1 := c + (u * cos(t1) + v * sin(t1)) * r
		var q0 := cuv + Vector2(cos(t0), -sin(t0)) * uvr.size * 0.5
		var q1 := cuv + Vector2(cos(t1), -sin(t1)) * uvr.size * 0.5
		tri_uv_out(c, p0, p1, cuv, q0, q1, col, n, em)


## Quad (corners a, b, c, d around the face, either winding) facing `out` with a UV rectangle: uva at corner a,
## uvc at the opposite corner c (a-b share u, a-d share v).  For atlas decals and repeating textures.
func quad_uv_out(a: Vector3, b: Vector3, c: Vector3, d: Vector3, out: Vector3, col: Color, uva: Vector2,
		uvc: Vector2, em: float = 0.0) -> void:
	var ub := Vector2(uva.x, uvc.y)
	var ud := Vector2(uvc.x, uva.y)
	tri_uv_out(a, b, c, uva, ub, uvc, col, out, em)
	tri_uv_out(a, c, d, uva, uvc, ud, col, out, em)
