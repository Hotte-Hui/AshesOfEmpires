"""env_c4p2_cine_book3d -- the guidebook as one small 3-D model (owner: cine stream, round 10).

The shared object of LS_C4P2_Book must be the same object on both sides of the cut, so it is built once: two
halves (page blocks with their boards) hinged at the spine, rendered with a pinhole camera as textured quads
(inverse-bilinear sampling, painter's order), lit per face by the shot's lamp, then snapped to the shot's palette.
The right half (pages 213 ff. and the back board) turns about the spine: theta 0 = open flat, 180 = closed on the
left half.  b1 looks down on the dining-car table and sees it rise; b2 looks along the fore-edge at table height and
sees the last degrees and the shut; b3a is the same camera on the Karsk oilcloth seeing it open; b3b looks down on
the book open at 212/213 again.  Textures: the pages (the guidebook's text, the engraved plan on 213), the card half
(upside down, as the item says) and the folded tracing lying on 213, the fore-edge (page lines), the boards'
dark red cloth with a blind-stamped compass rose.  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_kit as K

W, D, H = 104.0, 160.0, 7.0            # page width (x), page height (z, head at 0), half-block thickness (y)


# ================================================================================================= camera
class Cam:
    def __init__(self, eye, target, f=520.0, c=(320.0, 200.0), up=(0.0, 1.0, 0.0)):
        self.eye = np.asarray(eye, float)
        F = np.asarray(target, float) - self.eye
        self.F = F / np.linalg.norm(F)
        R = np.cross(self.F, np.asarray(up, float))
        self.R = R / np.linalg.norm(R)
        self.U = np.cross(self.R, self.F)
        self.f, self.c = f, c

    def p(self, P):
        d = np.asarray(P, float) - self.eye
        x, y, z = d @ self.R, d @ self.U, d @ self.F
        return np.array([self.c[0] + self.f * x / z, self.c[1] - self.f * y / z]), z


# ================================================================================================= textures
def tex_page(which, card=False, trace=False):
    """Page texture (RGB uint8, D x W: rows = z from the head, cols = x from the spine side outward)."""
    import env_c4p2_cine_book as B
    g = B.page_tex(int(W), int(D), which, 21 if which == 212 else 23)
    lin = g.alb.copy()
    img = np.round(K.to_srgb(lin) * 255).astype(np.uint8)
    if which == 213:
        if card:
            c = B.card_rgba(True)
            m = c[..., 3] > 0
            ox, oy = B.CARD_ON[0] - (B.GUTTER + 2), B.CARD_ON[1] - B.SPREAD[1]
            sub = img[oy:oy + c.shape[0], ox:ox + c.shape[1]]
            sub[m[:sub.shape[0], :sub.shape[1]]] = c[..., :3][:sub.shape[0], :sub.shape[1]][m[:sub.shape[0], :sub.shape[1]]]
        if trace:
            t = B.tracing_rgba()
            m = t[..., 3] > 0
            ox, oy = B.TRACE_ON[0] - (B.GUTTER + 2), B.TRACE_ON[1] - B.SPREAD[1] + 30
            sub = img[oy:oy + t.shape[0], ox:ox + t.shape[1]]
            mm = m[:sub.shape[0], :sub.shape[1]]
            sub[mm] = t[..., :3][:sub.shape[0], :sub.shape[1]][mm]
    else:
        pass                                   # the left page: u runs from its outer edge to the spine (as painted)
    return img


def tex_cover(w=int(W), d=int(D)):
    """Dark red bookcloth, worn at the corners, a blind-stamped compass rose and a gilt rule."""
    g = K.GB(w, d)
    g.put(np.ones((d, w), bool), '#5e1c16', tex=K.tex_noise(g, 2, 91, 0.10) * K.tex_noise(g, 7, 92, 0.06), z=10)
    wear = np.clip(1 - np.minimum.reduce([g.xx, w - 1 - g.xx, g.yy, d - 1 - g.yy]) / 5.0, 0, 1)
    g.mul(np.ones((d, w), bool), 1 + wear * 0.25)
    cx, cy = w * 0.55, d * 0.42
    rose = np.zeros((d, w), bool)
    for k in range(8):
        a = k * math.pi / 4
        r = 18 if k % 2 == 0 else 10
        rose |= g.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], 0.8 if k % 2 == 0 else 0.5)
    rose |= g.ell(cx, cy, 12, 12) & ~g.ell(cx, cy, 11, 11)
    g.mul(rose, 0.72)
    g.put(g.box(6, 6, w - 6, 7) | g.box(6, d - 7, w - 6, d - 6), '#b08a3a', z=9)
    lin = g.alb
    return np.round(K.to_srgb(lin) * 255).astype(np.uint8)


def tex_edge(n, d=int(D), seed=0, gilt=False):
    """A page block's edge: cream, fine page lines along it (rows = across the block, cols = along it)."""
    h = max(2, int(n))
    rows = np.arange(h)[:, None]
    base = np.array([226, 214, 186], np.float32)
    k = 0.86 + 0.14 * (K.hash2(rows + np.zeros((1, d)), np.arange(d)[None, :] // 9, seed))
    img = (base[None, None] * k[..., None]).astype(np.uint8)
    img[::2] = (img[::2] * 0.9).astype(np.uint8)
    return img


def tex_solid(col, h=4, w=8):
    c = (K.hx(col) * 255).astype(np.uint8)
    return np.broadcast_to(c, (h, w, 3)).copy()


# ================================================================================================= render
def _inv_bilinear(px, py, a, b, c, d):
    """Inverse bilinear map of points (px, py) into the quad a-b-c-d (a=(0,0), b=(1,0), c=(1,1), d=(0,1));
    returns (u, v, inside)."""
    e = b - a
    f = d - a
    g = a - b + c - d
    hx_ = px - a[0]
    hy_ = py - a[1]
    k2 = g[0] * f[1] - g[1] * f[0]
    k1 = e[0] * f[1] - e[1] * f[0] + hx_ * g[1] - hy_ * g[0]
    k0 = hx_ * e[1] - hy_ * e[0]
    if abs(k2) < 1e-6:
        v = -k0 / np.where(np.abs(k1) < 1e-9, 1e-9, k1)
    else:
        disc = k1 * k1 - 4 * k0 * k2
        sq = np.sqrt(np.clip(disc, 0, None))
        v1 = (-k1 - sq) / (2 * k2)
        v2 = (-k1 + sq) / (2 * k2)
        v = np.where((v1 >= -0.001) & (v1 <= 1.001), v1, v2)
    den_x = e[0] + g[0] * v
    den_y = e[1] + g[1] * v
    u = np.where(np.abs(den_x) > np.abs(den_y), (hx_ - f[0] * v) / np.where(np.abs(den_x) < 1e-9, 1e-9, den_x),
                 (hy_ - f[1] * v) / np.where(np.abs(den_y) < 1e-9, 1e-9, den_y))
    inside = (u >= -0.001) & (u <= 1.001) & (v >= -0.001) & (v <= 1.001)
    return np.clip(u, 0, 0.9999), np.clip(v, 0, 0.9999), inside


def _rot(P, theta, hinge_y):
    """Turn a point of the right half about the spine axis (x = 0, y = hinge_y) by theta degrees."""
    a = math.radians(theta)
    x, y, z = P
    return (x * math.cos(a) - (y - hinge_y) * math.sin(a), hinge_y + x * math.sin(a) + (y - hinge_y) * math.cos(a), z)


def faces(theta, page213, page212, cover, edge_w, edge_d, card_tip=True):
    """World-space quads of the book at opening angle theta: (corners a, b, c, d (u along a->b, v along a->d),
    texture, normal)."""
    out = []
    # left half: x in [-W, 0], y in [0, H] (page face on top)
    L = [((-W, H, 0), (0, H, 0), (0, H, D), (-W, H, D), page212, (0, 1, 0)),
         ((-W, 0, D), (-W, 0, 0), (-W, H, 0), (-W, H, D), edge_d, (-1, 0, 0)),
         ((-W, 0, D), (0, 0, D), (0, H, D), (-W, H, D), edge_w, (0, 0, 1)),
         ((-W, 0, 0), (0, 0, 0), (0, H, 0), (-W, H, 0), edge_w, (0, 0, -1))]
    out += L
    # right half (pages 213 on its top face, the back board under it), turned about the spine
    hy = H
    Rq = [((0, H, 0), (W, H, 0), (W, H, D), (0, H, D), page213, (0, 1, 0)),
          ((W, 0, 0), (0, 0, 0), (0, 0, D), (W, 0, D), cover, (0, -1, 0)),
          ((W, 0, 0), (W, 0, D), (W, H, D), (W, H, 0), edge_d, (1, 0, 0)),
          ((0, 0, D), (W, 0, D), (W, H, D), (0, H, D), edge_w, (0, 0, 1)),
          ((0, 0, 0), (W, 0, 0), (W, H, 0), (0, H, 0), edge_w, (0, 0, -1))]
    for (a, b, c, d, tx, n) in Rq:
        n2 = _rot(n, theta, 0.0)
        out.append((_rot(a, theta, hy), _rot(b, theta, hy), _rot(c, theta, hy), _rot(d, theta, hy), tx, n2))
    if card_tip:
        # the card half's corner sticks out of the fore-edge of the shut book (lies on 213, near the head)
        a, b, c, d = (W - 2, H + 0.3, 30), (W + 7, H + 0.3, 30), (W + 7, H + 0.3, 70), (W - 2, H + 0.3, 70)
        out.append((_rot(a, theta, hy), _rot(b, theta, hy), _rot(c, theta, hy), _rot(d, theta, hy),
                    tex_solid('#ece2c6'), _rot((0, 1, 0), theta, 0.0)))
    return out


def render(cam: Cam, quads, size=(640, 360), key=(0.4, 0.8, 0.45), lamp=(1.0, 0.86, 0.66), amb=0.42, box=None):
    """Painter's-order render of the quads -> RGBA uint8 (unquantised, straight sRGB)."""
    w, h = size
    img = np.zeros((h, w, 4), np.uint8)
    zbuf = np.full((h, w), np.inf)
    keyv = np.asarray(key, float)
    keyv /= np.linalg.norm(keyv)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    for (a, b, c, d, tx, n) in quads:
        P = [cam.p(np.asarray(q, float)) for q in (a, b, c, d)]
        pts = [p for p, z in P]
        zs = [z for p, z in P]
        if min(zs) <= 1:
            continue
        nn = np.asarray(n, float)
        cen = (np.asarray(a, float) + np.asarray(c, float)) / 2
        if np.dot(nn, cam.eye - cen) <= 0:
            continue                                  # back face
        x0 = max(0, int(min(p[0] for p in pts)) - 1)
        x1 = min(w, int(max(p[0] for p in pts)) + 2)
        y0 = max(0, int(min(p[1] for p in pts)) - 1)
        y1 = min(h, int(max(p[1] for p in pts)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        sx, sy = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
        u, v, ins = _inv_bilinear(sx, sy, *pts)
        if not ins.any():
            continue
        th, tw = tx.shape[:2]
        col = tx[(v * th).astype(int), (u * tw).astype(int)].astype(np.float32)
        lam = max(0.0, float(np.dot(nn, keyv)))
        shade = amb + (1 - amb) * lam
        col = col * shade * np.asarray(lamp, np.float32)[None, None]
        zq = np.mean(zs)
        zb = zbuf[y0:y1, x0:x1]
        upd = ins & (zq < zb)
        zb[upd] = zq
        sub = img[y0:y1, x0:x1]
        sub[upd, :3] = np.clip(col[upd], 0, 255).astype(np.uint8)
        sub[upd, 3] = 255
    return img


def book_frames(cam, thetas, pal, key, lamp, amb, card=True, size=(640, 360), spread=0.03):
    p213 = tex_page(213, card=card, trace=card)
    p212 = tex_page(212)
    cov = tex_cover()
    ew = tex_edge(H, int(W), seed=3)
    ed = tex_edge(H, int(D), seed=5)
    out = []
    for th in thetas:
        q = faces(th, p213, p212, cov, ew, ed, card_tip=card)
        rg = render(cam, q, size, key, lamp, amb)
        lin = K.to_lin(rg[..., :3].astype(np.float32) / 255.0)
        out.append(K.quant(lin, pal, spread=spread, alpha=rg[..., 3] > 0))
    return out
