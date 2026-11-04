"""chargen_portrait2_sdf -- signed-distance sculpting + orthographic sphere tracer for the dialogue busts.

Part of the second-generation portrait pipeline (entry point: chargen_portrait2.py).  Everything here is
deterministic numpy; nothing is sampled from images.

Coordinate system ("view space", units = final portrait pixels):
  x -> image right, y -> image DOWN, z -> towards the viewer.  The camera is orthographic and looks along -z.
Local frames are given as (origin, R) with p_local = R^T (p_view - origin); see rot().

A scene is a tree of Node objects; every node evaluates a batch of points P (N,3 float32) and returns
(distance (N,), material id (N,) or scalar).  Combinators: Union (smooth), Sub (smooth subtraction), Inter,
Xform (local frame), Displace, Bound (bounding sphere short-cut used to keep the tracer fast).
"""
from __future__ import annotations

import math

import numpy as np

F = np.float32


# ----------------------------------------------------------------------------------------- frames
def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """local -> view rotation.  yaw > 0 turns the local +z (face front) towards image right, pitch > 0 tilts
    the front downwards, roll > 0 tilts clockwise on screen."""
    y, p, r = (math.radians(a) for a in (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), math.sin(p)], [0, -math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return (Ry @ Rx @ Rz).astype(np.float64)


class Frame:
    """Rigid frame: to_view(p_local) and to_local(p_view).  Frames nest via child()."""

    def __init__(self, origin=(0, 0, 0), R=None):
        self.o = np.asarray(origin, np.float64)
        self.R = np.eye(3) if R is None else np.asarray(R, np.float64)

    def to_view(self, p):
        return self.o + self.R @ np.asarray(p, np.float64)

    def dir_to_view(self, v):
        return self.R @ np.asarray(v, np.float64)

    def child(self, origin=(0, 0, 0), R=None):
        R = np.eye(3) if R is None else np.asarray(R, np.float64)
        return Frame(self.to_view(origin), self.R @ R)


# ----------------------------------------------------------------------------------------- nodes
class Node:
    def eval(self, P):
        raise NotImplementedError


def _len(v):
    return np.sqrt((v * v).sum(1))


class Ellipsoid(Node):
    def __init__(self, c, r, mat, R=None):
        self.c = np.asarray(c, F)
        self.r = np.asarray(r, F)
        self.R = (np.eye(3) if R is None else np.asarray(R)).astype(F)
        self.mat = mat

    def eval(self, P):
        q = (P - self.c) @ self.R
        k0 = _len(q / self.r)
        k1 = _len(q / (self.r * self.r))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-5), self.mat


class Sphere(Node):
    def __init__(self, c, r, mat):
        self.c = np.asarray(c, F)
        self.r = F(r)
        self.mat = mat

    def eval(self, P):
        return _len(P - self.c) - self.r, self.mat


class RoundCone(Node):
    """Capsule with radius r1 at a and r2 at b (exact SDF, Quilez)."""

    def __init__(self, a, b, r1, r2, mat):
        self.a = np.asarray(a, F)
        self.b = np.asarray(b, F)
        self.r1, self.r2 = F(r1), F(r2)
        ba = self.b - self.a
        self.ba = ba
        self.l2 = F(ba @ ba)
        self.rr = F(r1 - r2)
        self.a2 = F(self.l2 - self.rr * self.rr)
        self.il2 = F(1.0 / self.l2)
        self.mat = mat

    def eval(self, P):
        pa = P - self.a
        y = pa @ self.ba
        z = y - self.l2
        v = pa * self.l2 - y[:, None] * self.ba
        x2 = (v * v).sum(1)
        y2 = y * y * self.l2
        z2 = z * z * self.l2
        k = np.sign(self.rr) * self.rr * self.rr * x2
        d3 = (np.sqrt(np.maximum(x2 * self.a2 * self.il2, 0)) + y * self.rr) * self.il2 - self.r1
        d1 = np.sqrt(x2 + z2) * self.il2 - self.r2
        d2 = np.sqrt(x2 + y2) * self.il2 - self.r1
        d = np.where(np.sign(z) * self.a2 * z2 > k, d1, np.where(np.sign(y) * self.a2 * y2 < k, d2, d3))
        return d, self.mat


class RoundBox(Node):
    def __init__(self, c, half, rad, mat, R=None):
        self.c = np.asarray(c, F)
        self.h = np.asarray(half, F)
        self.rad = F(rad)
        self.R = (np.eye(3) if R is None else np.asarray(R)).astype(F)
        self.mat = mat

    def eval(self, P):
        q = np.abs((P - self.c) @ self.R) - self.h + self.rad
        out = _len(np.maximum(q, 0))
        inn = np.minimum(np.maximum(q[:, 0], np.maximum(q[:, 1], q[:, 2])), 0)
        return out + inn - self.rad, self.mat


class Cylinder(Node):
    """Capped cylinder around the local y axis (half height h, radius r, edge rounding e)."""

    def __init__(self, c, r, h, mat, R=None, e=0.0):
        self.c = np.asarray(c, F)
        self.r, self.h, self.e = F(r), F(h), F(e)
        self.R = (np.eye(3) if R is None else np.asarray(R)).astype(F)
        self.mat = mat

    def eval(self, P):
        q = (P - self.c) @ self.R
        dx = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - self.r + self.e
        dy = np.abs(q[:, 1]) - self.h + self.e
        out = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2)
        return out + np.minimum(np.maximum(dx, dy), 0) - self.e, self.mat


class Plane(Node):
    """Half space: inside where n.(p-c) < 0."""

    def __init__(self, c, n, mat):
        n = np.asarray(n, F)
        self.n = n / np.linalg.norm(n)
        self.c = np.asarray(c, F)
        self.mat = mat

    def eval(self, P):
        return (P - self.c) @ self.n, self.mat


class Union(Node):
    """Smooth union of children (k = blend radius in px; per child k list allowed)."""

    def __init__(self, children, k=0.0):
        self.ch = [c for c in children if c is not None]
        self.k = k

    def eval(self, P):
        d, m = self.ch[0].eval(P)
        m = np.broadcast_to(np.asarray(m, np.int16), d.shape).copy()
        for i, c in enumerate(self.ch[1:]):
            k = self.k[i] if isinstance(self.k, (list, tuple)) else self.k
            d2, m2 = c.eval(P)
            take = d2 < d
            m = np.where(take, np.asarray(m2, np.int16), m)
            if k > 0:
                h = np.clip(0.5 + 0.5 * (d - d2) / k, 0, 1)
                d = d + (d2 - d) * h - k * h * (1 - h)
            else:
                d = np.minimum(d, d2)
        return d, m


class Sub(Node):
    """a minus b (smooth).  keep_mat: material of a; cut_mat (optional) paints the cut surface."""

    def __init__(self, a, b, k=0.0, cut_mat=None):
        self.a, self.b, self.k, self.cut_mat = a, b, k, cut_mat

    def eval(self, P):
        da, ma = self.a.eval(P)
        db, _ = self.b.eval(P)
        nb = -db
        if self.k > 0:
            h = np.clip(0.5 - 0.5 * (nb - da) / self.k, 0, 1)
            d = nb + (da - nb) * h + self.k * h * (1 - h)
        else:
            d = np.maximum(da, nb)
        if self.cut_mat is not None:
            ma = np.where(nb > da, np.int16(self.cut_mat), np.asarray(ma, np.int16))
        return d, ma


class Inter(Node):
    def __init__(self, a, b, k=0.0):
        self.a, self.b, self.k = a, b, k

    def eval(self, P):
        da, ma = self.a.eval(P)
        db, _ = self.b.eval(P)
        if self.k > 0:
            h = np.clip(0.5 - 0.5 * (db - da) / self.k, 0, 1)
            d = db + (da - db) * h + self.k * h * (1 - h)
        else:
            d = np.maximum(da, db)
        return d, ma


class Xform(Node):
    """Evaluate a child built in a local frame (origin o, rotation R: local -> view)."""

    def __init__(self, child, o=(0, 0, 0), R=None, frame: Frame | None = None):
        if frame is not None:
            o, R = frame.o, frame.R
        self.o = np.asarray(o, F)
        self.R = (np.eye(3) if R is None else np.asarray(R)).astype(F)
        self.child = child

    def eval(self, P):
        return self.child.eval((P - self.o) @ self.R)


class Displace(Node):
    """d - amp * fn(P) where fn returns values roughly in [-1, 1] (bumps grow outwards)."""

    def __init__(self, child, fn, amp=1.0, lipschitz=1.5):
        self.child, self.fn, self.amp, self.lip = child, fn, F(amp), F(lipschitz)

    def eval(self, P):
        d, m = self.child.eval(P)
        near = np.abs(d) < self.amp * 3 + 1
        if near.any():
            d = d.copy()
            d[near] = d[near] - self.amp * self.fn(P[near])
        return d / self.lip if self.lip != 1 else d, m


class Bound(Node):
    """Bounding-sphere short-cut: far points get the (lower-bound) sphere distance."""

    def __init__(self, child, c, r, margin=3.0, mat=0):
        self.child = child
        self.c = np.asarray(c, F)
        self.r = F(r)
        self.margin = F(margin)
        self.mat = mat

    def eval(self, P):
        ds = _len(P - self.c) - self.r
        near = ds < self.margin
        d = ds
        m = np.full(P.shape[0], self.mat, np.int16)
        if near.any():
            d = ds.copy()
            dn, mn = self.child.eval(P[near])
            d[near] = dn
            m[near] = mn
        return d, m


class Mat(Node):
    """Override the material of a child."""

    def __init__(self, child, mat):
        self.child, self.mat = child, mat

    def eval(self, P):
        d, _ = self.child.eval(P)
        return d, self.mat


def bound_of(points, pad):
    pts = np.asarray(points, float)
    c = (pts.max(0) + pts.min(0)) / 2
    r = float(np.sqrt(((pts - c) ** 2).sum(1)).max()) + pad
    return c, r


# ----------------------------------------------------------------------------------------- noise
def hash3(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(F) / F(65535.0)


def vnoise3(P, cell, seed=0):
    """Smooth value noise in [-1, 1] on a 3D lattice (deterministic integer hash)."""
    q = P / F(cell)
    i = np.floor(q).astype(np.int64)
    f = q - i
    u = f * f * (3 - 2 * f)
    out = np.zeros(P.shape[0], F)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * \
                    (u[:, 2] if dz else 1 - u[:, 2])
                out += w * hash3(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return out * 2 - 1


# ----------------------------------------------------------------------------------------- tracing
class GBuffer:
    """Super-sampled G-buffer (h*ss, w*ss)."""
    pass


def trace(root: Node, w, h, ss=3, z0=90.0, zfar=-90.0, steps=110, key=(0.6, -0.5, 0.6), shadow_k=10.0,
          shadow_from=None):
    """Orthographic sphere trace.  Returns a GBuffer with hit, z, n, mat, P, shadow (key visibility 0..1),
    ao (0..1).  `key` is the direction TOWARDS the key light in view space (y down => negative y = from above)."""
    W, Hh = w * ss, h * ss
    ys, xs = np.mgrid[0:Hh, 0:W]
    ox = ((xs + 0.5) / ss).astype(F).ravel()
    oy = ((ys + 0.5) / ss).astype(F).ravel()
    N = ox.size
    t = np.zeros(N, F)
    hit = np.zeros(N, bool)
    alive = np.ones(N, bool)
    idx = np.arange(N)
    for _ in range(steps):
        a = idx[alive]
        if a.size == 0:
            break
        P = np.stack([ox[a], oy[a], F(z0) - t[a]], 1)
        d, _ = root.eval(P)
        t[a] += np.maximum(d, 0.004) * F(0.85)
        done = d < 0.02
        hit[a[done]] = True
        gone = (F(z0) - t[a]) < zfar
        alive[a[done | gone]] = False
    g = GBuffer()
    g.w, g.h, g.ss = W, Hh, ss
    g.hit = hit.reshape(Hh, W)
    P = np.stack([ox, oy, F(z0) - t], 1)
    hi = idx[hit]
    Ph = P[hi]
    # material at the hit
    _, m = root.eval(Ph)
    mat = np.full(N, -1, np.int16)
    mat[hi] = m
    # normal (tetrahedron)
    e = F(0.3)
    ks = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], F)
    n = np.zeros((hi.size, 3), F)
    for k in ks:
        dk, _ = root.eval(Ph + k * e)
        n += k[None, :] * dk[:, None]
    n /= np.linalg.norm(n, axis=1, keepdims=True) + F(1e-6)
    nn = np.zeros((N, 3), F)
    nn[hi] = n
    # key light visibility (soft shadow march)
    L = np.asarray(key, F)
    L /= np.linalg.norm(L)
    vis = np.ones(hi.size, F)
    tt = np.full(hi.size, F(1.2))
    act = np.ones(hi.size, bool)
    ar = np.arange(hi.size)
    base = Ph + n * F(0.45)
    for _ in range(70):
        a = ar[act]
        if a.size == 0:
            break
        Q = base[a] + L[None, :] * tt[a, None]
        d, _ = root.eval(Q)
        vis[a] = np.minimum(vis[a], np.clip(shadow_k * d / tt[a], 0, 1))
        tt[a] += np.clip(d, 0.25, 4.0)
        act[a[(d < 0.01) | (tt[a] > 70)]] = False
    sh = np.ones(N, F)
    sh[hi] = vis
    # ambient occlusion (5 taps along the normal)
    occ = np.zeros(hi.size, F)
    sc = F(1.0)
    for i in range(1, 6):
        hh = F(0.9 * i)
        d, _ = root.eval(Ph + n * hh)
        occ += (hh - d) * sc
        sc *= F(0.62)
    ao = np.ones(N, F)
    ao[hi] = np.clip(1 - 0.18 * occ, 0, 1)
    g.z = P[:, 2].reshape(Hh, W)
    g.P = P.reshape(Hh, W, 3)
    g.n = nn.reshape(Hh, W, 3)
    g.mat = mat.reshape(Hh, W)
    g.shadow = sh.reshape(Hh, W)
    g.ao = ao.reshape(Hh, W)
    return g


def downsample(g: GBuffer, nmat: int, priority=None):
    """Collapse the super-sampled buffer to final pixels.  Material = majority among hit samples
    (ties broken by `priority`), coverage = hit fraction, other channels averaged over the winning
    material's samples."""
    ss = g.ss
    h, w = g.h // ss, g.w // ss

    def blocks(a):
        sh = a.shape
        a = a.reshape(h, ss, w, ss, *sh[2:])
        a = np.moveaxis(a, 2, 1)
        return a.reshape(h, w, ss * ss, *sh[2:])

    mat = blocks(g.mat)
    hit = mat >= 0
    cover = hit.mean(2)
    counts = np.zeros((h, w, nmat), np.float32)
    for i in range(nmat):
        counts[..., i] = (mat == i).sum(2)
    if priority is not None:
        counts += np.asarray(priority, np.float32)[None, None, :] * 0.01
    win = np.argmax(counts, 2).astype(np.int16)
    win[cover <= 0] = -1
    sel = (mat == win[..., None]) & hit
    wsum = np.maximum(sel.sum(2), 1)

    def avg(a):
        b = blocks(a)
        if b.ndim == 4:
            return (b * sel[..., None]).sum(2) / wsum[..., None]
        return (b * sel).sum(2) / wsum

    out = GBuffer()
    out.w, out.h, out.ss = w, h, 1
    out.mat = win
    out.cover = cover
    out.n = avg(g.n)
    out.n /= np.linalg.norm(out.n, axis=2, keepdims=True) + 1e-6
    out.z = avg(g.z)
    out.P = avg(g.P)
    out.shadow = avg(g.shadow)
    out.ao = avg(g.ao)
    out.hit = win >= 0
    return out


class Warp(Node):
    """Evaluate the child at warped points p - fn(p) (fn returns (N,3) offsets).  Keep offsets gentle
    (gradient << 1) so the distance stays usable; `lip` divides the distance for safety."""

    def __init__(self, child, fn, lip=1.2):
        self.child, self.fn, self.lip = child, fn, F(lip)

    def eval(self, P):
        d, m = self.child.eval(P - self.fn(P).astype(F))
        return d / self.lip, m


class Fn(Node):
    """Arbitrary signed function node: fn(P) -> distance-like values (negative inside)."""

    def __init__(self, fn, mat=0):
        self.fn, self.mat = fn, mat

    def eval(self, P):
        return self.fn(P).astype(F), self.mat


class Offset(Node):
    """Inflate (r > 0) or shrink a child surface."""

    def __init__(self, child, r, mat=None):
        self.child, self.r, self.mat = child, F(r), mat

    def eval(self, P):
        d, m = self.child.eval(P)
        return d - self.r, (m if self.mat is None else self.mat)


class Shell(Node):
    """Hollow shell of thickness t around a child surface."""

    def __init__(self, child, t, mat=None):
        self.child, self.t, self.mat = child, F(t), mat

    def eval(self, P):
        d, m = self.child.eval(P)
        return np.abs(d) - self.t, (m if self.mat is None else self.mat)


class Scale(Node):
    """Uniform zoom about centre c: the child appears s times larger."""

    def __init__(self, child, c, s):
        self.child, self.c, self.s = child, np.asarray(c, F), F(s)

    def eval(self, P):
        d, m = self.child.eval((P - self.c) / self.s + self.c)
        return d * self.s, m


class EllipticCylinder(Node):
    """Disc / cylinder around local y with elliptical cross-section (rx, rz), half height h, edge round e.
    Exact for circles, a close bound for mild ellipses."""

    def __init__(self, c, rx, rz, h, mat, e=0.0):
        self.c = np.asarray(c, F)
        self.rx, self.rz, self.h, self.e = F(rx), F(rz), F(h), F(e)
        self.mat = mat

    def eval(self, P):
        q = P - self.c
        sc = self.rz / self.rx
        rr = np.sqrt(q[:, 0] ** 2 + (q[:, 2] / sc) ** 2)
        dx = (rr - self.rx + self.e) * min(F(1), sc)
        dy = np.abs(q[:, 1]) - self.h + self.e
        out = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2)
        return out + np.minimum(np.maximum(dx, dy), 0) - self.e, self.mat
