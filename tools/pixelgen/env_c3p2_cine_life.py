"""env_c3p2_cine_life -- light, props and living detail for the places of the Chapter-3 part-2 cinematics
(LS_C3_Radio / _Fire / _Escape / _Halves; owner: c3p2 places stream, round 10).

A small float-RGB painter on top of the round-8 kit (env_c3p2_cine_kit): every place is painted as lit colour
(albedo x light field + emission), then snapped to a scene palette with the kit's ordered dither, so the new detail
keeps the pixel look of the rest of the cinematics.  Props are generic and original (bare lime trees, iron lamp
posts, a snowed-in 1950s saloon car, crates, barrels, benches, fences, watchtowers); sheets for the runtime
(steam clouds lit from below, fire smoke, tall flames, burning paper, crows, pigeons, a cat).  No people here --
the figures come from the figures stream (env_c3p2_cine_figs / _hands).
Pure numpy, deterministic (fixed seeds, no global random state), no image inputs.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import C, K, VW, VH
import pg

_NZ: dict = {}


def hexf(h) -> np.ndarray:
    if isinstance(h, str):
        return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32)
    return np.asarray(h, np.float32)


def nz(w, h, cell, seed, octaves=3):
    """Cached value noise (0..1)."""
    k = (w, h, float(cell), seed, octaves)
    if k not in _NZ:
        _NZ[k] = pg.value_noise(w, h, cell, seed, octaves=octaves)
    return _NZ[k]


def hsh(a, b=0.0, seed=0.0):
    """Deterministic hash in 0..1 of (a, b) arrays/scalars."""
    return np.mod(np.sin(np.asarray(a) * 12.9898 + np.asarray(b) * 78.233 + seed * 3.17) * 43758.5453, 1.0)


def vnoise(x, y, seed=0):
    """Smooth value noise (0..1) at arbitrary float coordinates (vectorised, deterministic)."""
    x = np.asarray(x, np.float32)
    y = np.asarray(y, np.float32)
    xi, yi = np.floor(x), np.floor(y)
    fx, fy = x - xi, y - yi
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    h00 = hsh(xi, yi, seed)
    h10 = hsh(xi + 1, yi, seed)
    h01 = hsh(xi, yi + 1, seed)
    h11 = hsh(xi + 1, yi + 1, seed)
    return (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy


# ================================================================================================= canvas
class Cv:
    """Float RGB canvas in absolute frame coordinates (origin ox, oy) with a light field and an alpha mask."""

    def __init__(self, w=VW, h=VH, ox=0, oy=0, amb=(0.30, 0.34, 0.45)):
        self.w, self.h, self.ox, self.oy = int(w), int(h), ox, oy
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.yy = yy + oy
        self.xx = xx + ox
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), bool)
        self.L = np.ones((self.h, self.w, 3), np.float32) * np.asarray(amb, np.float32)[None, None]
        self.z = np.full((self.h, self.w), 1e4, np.float32)          # depth (m) for the haze

    # ------------------------------------------------------------------ masks
    def full(self):
        return np.ones((self.h, self.w), bool)

    def box(self, x0, y0, x1, y1):
        m = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, int(math.floor(x0 - self.ox))), max(0, int(math.floor(y0 - self.oy)))
        X1, Y1 = min(self.w, int(math.floor(x1 - self.ox))), min(self.h, int(math.floor(y1 - self.oy)))
        if X1 > X0 and Y1 > Y0:
            m[Y0:Y1, X0:X1] = True
        return m

    def poly(self, pts):
        return C.poly_mask(self.w, self.h, [(x - self.ox, y - self.oy) for (x, y) in pts])

    def ell(self, cx, cy, rx, ry):
        return ((self.xx + 0.5 - cx) / max(rx, 0.3)) ** 2 + ((self.yy + 0.5 - cy) / max(ry, 0.3)) ** 2 <= 1.0

    def seg(self, pts, r0, r1=None):
        """Tapered capsule chain through pts (radius r0 at the start, r1 at the end)."""
        r1 = r0 if r1 is None else r1
        m = np.zeros((self.h, self.w), bool)
        n = len(pts) - 1
        if n < 1:
            return m
        lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(n)]
        tot = max(1e-6, sum(lens))
        acc = 0.0
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            ra = r0 + (r1 - r0) * acc / tot
            acc += lens[i]
            rb = r0 + (r1 - r0) * acc / tot
            rr = max(ra, rb)
            X0 = max(0, int(math.floor(min(ax, bx) - rr - 1 - self.ox)))
            X1 = min(self.w, int(math.ceil(max(ax, bx) + rr + 1 - self.ox)))
            Y0 = max(0, int(math.floor(min(ay, by) - rr - 1 - self.oy)))
            Y1 = min(self.h, int(math.ceil(max(ay, by) + rr + 1 - self.oy)))
            if X1 <= X0 or Y1 <= Y0:
                continue
            px = self.xx[Y0:Y1, X0:X1] + 0.5
            py = self.yy[Y0:Y1, X0:X1] + 0.5
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(px)
            d = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
            m[Y0:Y1, X0:X1] |= d <= (ra + (rb - ra) * t)
        return m

    def ring(self, cx, cy, r0, r1, sy=1.0):
        d = np.hypot(self.xx + 0.5 - cx, (self.yy + 0.5 - cy) / sy)
        return (d >= r0) & (d < r1)

    def nz(self, cell, seed, octaves=3):
        n = nz(self.w, self.h, cell, seed, octaves)
        return n

    # ------------------------------------------------------------------ light
    def light(self, x, y, r, col, power=1.5, sy=1.0, mask=None):
        """Add a coloured point light (multiplier, e.g. (1.6, 1.1, 0.6)) with a soft falloff."""
        d = np.hypot(self.xx + 0.5 - x, (self.yy + 0.5 - y) / sy) / max(r, 0.5)
        f = np.clip(1 - d, 0, 1) ** power
        if mask is not None:
            f = f * mask
        self.L += f[..., None] * np.asarray(col, np.float32)[None, None]
        return f

    def light_field(self, f, col):
        self.L += np.asarray(f, np.float32)[..., None] * np.asarray(col, np.float32)[None, None]

    def cone(self, x, y, ang, spread, reach, col, power=1.3):
        """Light cone from (x, y) toward angle ang (radians, 0 = down), half-angle spread."""
        dx = self.xx + 0.5 - x
        dy = self.yy + 0.5 - y
        a = np.arctan2(dx, dy) - ang
        a = (a + np.pi) % (2 * np.pi) - np.pi
        d = np.hypot(dx, dy)
        f = np.clip(1 - np.abs(a) / spread, 0, 1) ** 0.8 * np.clip(1 - d / reach, 0, 1) ** power
        self.L += f[..., None] * np.asarray(col, np.float32)[None, None]
        return f

    # ------------------------------------------------------------------ paint
    def put(self, m, col, k=1.0, lit=True, z=None):
        """Paint mask m with colour col (hex or rgb 0..255) times the light field (lit) times k; z = depth (m)."""
        if not np.any(m):
            return
        c = hexf(col)
        kk = k[m] if isinstance(k, np.ndarray) and k.shape == m.shape else k
        if isinstance(kk, np.ndarray) and kk.ndim == 1:
            kk = kk[:, None]
        v = c[None, :] * (self.L[m] if lit else 1.0) * kk
        self.rgb[m] = v
        self.a |= m
        if z is not None:
            self.z[m] = z[m] if isinstance(z, np.ndarray) and z.shape == m.shape else z

    def emit(self, m, col, k=1.0, z=None):
        self.put(m, col, k, lit=False, z=z)

    def haze(self, col, z0, z1, tmax, only=None):
        """Depth haze: blend toward col by tmax * smoothstep(z0..z1) of the depth buffer."""
        u = np.clip((self.z - z0) / max(1e-3, z1 - z0), 0, 1)
        t = (u * u * (3 - 2 * u)) * tmax
        t[self.z >= 9e3] = 0.0
        if only is not None:
            t = t * only
        self.fog(t, col)

    def add(self, m, col, k=1.0):
        """Additive colour (glows) on already painted pixels and new ones."""
        if not np.any(m):
            return
        c = hexf(col)
        kk = k[m] if isinstance(k, np.ndarray) and k.shape == m.shape else k
        if isinstance(kk, np.ndarray) and kk.ndim == 1:
            kk = kk[:, None]
        self.rgb[m] += c[None, :] * kk
        self.a |= m

    def mix(self, m, col, t):
        """Blend toward col (lit) by t (0..1, scalar or full array)."""
        if not np.any(m):
            return
        c = hexf(col)
        tt = t[m] if isinstance(t, np.ndarray) and t.shape == m.shape else t
        if isinstance(tt, np.ndarray) and tt.ndim == 1:
            tt = tt[:, None]
        self.rgb[m] = self.rgb[m] * (1 - tt) + c[None, :] * self.L[m] * tt
        self.a |= m

    def fog(self, amount, col):
        """Atmospheric haze: blend every painted pixel toward col by amount (full array or scalar)."""
        c = hexf(col)
        t = np.asarray(amount, np.float32)
        if t.ndim == 2:
            t = t[..., None]
        self.rgb = self.rgb * (1 - t) + c[None, None] * t

    def quant(self, pal, spread=12.0, alpha=None):
        a = self.a if alpha is None else alpha
        return requant(self.rgb, pal, spread, self.ox, self.oy, a)


def requant(rgb, pal, spread=12.0, ox=0, oy=0, alpha=None):
    """Float RGB -> RGBA uint8 snapped to pal (hex list) with ordered dither (chunked, low memory)."""
    h, w = rgb.shape[:2]
    P = np.stack([hexf(c) for c in pal])
    d = (pg.bayer(w, h, ox, oy) - 0.5)[..., None] * spread
    x = np.clip(rgb, 0, 255) + d
    out = np.zeros((h, w, 4), np.uint8)
    step = max(1, 40000 // max(1, w))
    for y0 in range(0, h, step):
        xs = x[y0:y0 + step]
        dist = ((xs[:, :, None, :] - P[None, None]) ** 2).sum(-1)
        out[y0:y0 + step, :, :3] = P[dist.argmin(-1)].astype(np.uint8)
    out[..., 3] = 255 if alpha is None else np.where(alpha, 255, 0)
    return out


def palette(*groups, extra=()):
    s = []
    for g in groups:
        for c in g:
            c = c.upper()
            if c not in s:
                s.append(c)
    for c in extra:
        c = c.upper()
        if c not in s:
            s.append(c)
    return s


def ramp_between(a, b, n):
    """n hex colours from a to b (inclusive)."""
    ca, cb = hexf(a), hexf(b)
    out = []
    for i in range(n):
        c = ca + (cb - ca) * (i / max(1, n - 1))
        out.append('#%02X%02X%02X' % tuple(int(round(v)) for v in c))
    return out


def edge_top(m, k=1):
    """Pixels of m whose pixel k rows above is not in m (top edges, where snow settles)."""
    return m & ~C.shift(m, 0, -k)


def edge_dir(m, dx, dy, k=1):
    return m & ~C.shift(m, dx * k, dy * k)


# ================================================================================================= props
def snowcap(cv: Cv, m, depth=2, col='#C2C9D2', seed=0, k=1.0, ragged=0.35):
    """Snow settles on the top edges of mask m (depth px, a ragged lower edge)."""
    top = np.zeros_like(m)
    for i in range(1, depth + 1):
        e = edge_top(m, i)
        if i > 1:
            e &= nz(cv.w, cv.h, 2.0, seed + i, 1) > ragged
        top |= e
    cv.put(top, col, k)
    return top


def tree(cv: Cv, x, yb, h, seed, col='#0E1219', snow='#A1AAB7', snow_k=1.0, spread=1.0, lean=0.0, twigs=True,
         trunk_r=None):
    """A bare winter lime/plane tree: tapering trunk, recursive branches, fine twigs, snow on the upper sides."""
    rng = np.random.default_rng(seed)
    tr = trunk_r if trunk_r is not None else max(1.0, h * 0.035)
    m = np.zeros((cv.h, cv.w), bool)
    fine = np.zeros((cv.h, cv.w), bool)
    top = (x + lean * h * 0.3, yb - h * 0.45)
    m |= cv.seg([(x, yb), (x + lean * h * 0.1, yb - h * 0.25), top], tr, tr * 0.65)

    def branch(p, ang, ln, r, depth):
        nonlocal m, fine
        q = (p[0] + math.sin(ang) * ln, p[1] - math.cos(ang) * ln)
        mid = ((p[0] + q[0]) / 2 + rng.uniform(-0.12, 0.12) * ln, (p[1] + q[1]) / 2 + rng.uniform(-0.08, 0.08) * ln)
        if r < 0.75:
            fine |= cv.seg([p, mid, q], 0.5)
        else:
            m |= cv.seg([p, mid, q], r, r * 0.7)
        if depth <= 0 or ln < 3:
            return
        nb = 2 if depth > 1 else rng.integers(2, 4)
        for i in range(nb):
            da = (-0.45 + 0.9 * (i + rng.uniform(0.2, 0.8)) / nb) * spread
            branch(q, ang + da + rng.uniform(-0.12, 0.12), ln * rng.uniform(0.62, 0.78), r * 0.66, depth - 1)

    for i, a0 in enumerate((-0.55, -0.15, 0.25, 0.6)):
        branch(top, a0 * spread + rng.uniform(-0.1, 0.1) + lean * 0.3, h * rng.uniform(0.22, 0.3), tr * 0.75, 4)
    for i in range(3):
        y = yb - h * rng.uniform(0.3, 0.42)
        side = -1 if i % 2 == 0 else 1
        branch((x + lean * h * 0.05, y), side * rng.uniform(0.7, 1.1), h * 0.2, tr * 0.5, 3)
    if twigs:
        cv.put(fine & ~m, col, 0.9)
    cv.put(m, col)
    if snow:
        cap = edge_top(m) & (nz(cv.w, cv.h, 3.0, seed + 5, 2) > 0.3)
        cv.put(cap, snow, snow_k)
    return m | fine


def lamp_post(cv: Cv, x, yb, h, col='#0C0F15', glass='#FCE2B0', lit=True, style='globe', snow='#A1AAB7', k=1.0):
    """Cast-iron lamp post: base, fluted shaft, a globe or a lantern head."""
    s = h / 60.0
    post = cv.seg([(x, yb), (x, yb - h * 0.86)], max(0.6, 1.3 * s), max(0.5, 0.8 * s))
    base = cv.poly([(x - 3.2 * s, yb), (x + 3.2 * s, yb), (x + 2 * s, yb - 6 * s), (x - 2 * s, yb - 6 * s)])
    cv.put(post | base, col, k)
    hy = yb - h * 0.9
    if style == 'globe':
        g = cv.ell(x + 0.5, hy, 3.6 * s + 0.6, 4.2 * s + 0.6)
        if lit:
            cv.emit(g, glass)
            cv.emit(cv.ell(x + 0.5 - s, hy - s, 1.4 * s + 0.4, 1.6 * s + 0.4), '#FFF6DC')
        else:
            cv.put(g, '#3A4859', k)
        cap = cv.box(x - 2 * s, hy - 5.4 * s - 1, x + 3 * s, hy - 3.6 * s)
        cv.put(cap, col, k)
        snowcap(cv, cap, 1, snow, 7)
    else:
        lant = cv.poly([(x - 4 * s, hy - 5 * s), (x + 5 * s, hy - 5 * s), (x + 3.4 * s, hy + 4 * s), (x - 2.4 * s, hy + 4 * s)])
        roof = cv.poly([(x - 5 * s, hy - 5 * s), (x + 6 * s, hy - 5 * s), (x + 0.5, hy - 9 * s)])
        if lit:
            cv.emit(lant, glass)
        else:
            cv.put(lant, '#3A4859', k)
        cv.put(roof, col, k)
        cv.put(cv.seg([(x + 0.5, hy - 5 * s), (x + 0.5, hy + 4 * s)], 0.5), col, k)
        snowcap(cv, roof, 2, snow, 9)
    return post


def car(cv: Cv, x, yb, s=1.0, facing=1, body='#2A3038', snow='#C2C9D2', glass='#0C1119', chrome='#7A828A',
        lit_window=False, seed=3, snow_k=1.0):
    """A snowed-in 1950s saloon car seen from the side (fastback roof, round fenders, chrome bumpers).
    x = centre, yb = ground line, s = px per 10 cm (s=1 -> about 46 px long)."""
    L = 46 * s
    H = 15 * s
    f = facing

    def P(u, v):                                   # u -1..1 along the car (front = +1), v 0 (ground) .. 1 (roof)
        return (x + f * u * L / 2, yb - v * H)

    body_m = cv.poly([P(-1.0, 0.18), P(-1.0, 0.5), P(-0.92, 0.62), P(-0.55, 0.66), P(-0.35, 1.0), P(0.18, 1.0),
                      P(0.42, 0.66), P(0.92, 0.6), P(1.0, 0.45), P(1.0, 0.18)])
    cv.put(body_m, body, 1.0 + 0.25 * (cv.yy < yb - 0.55 * H))
    win = cv.poly([P(-0.5, 0.66), P(-0.33, 0.93), P(0.15, 0.93), P(0.36, 0.66)])
    cv.put(win, glass)
    cv.put(cv.box(*P(-0.08, 0.93), *P(-0.05, 0.66)) if f > 0 else cv.box(*P(-0.05, 0.93), *P(-0.08, 0.66)),
           body)
    if lit_window:
        cv.emit(win & (cv.yy > yb - 0.8 * H), '#3A2C20')
    for u in (-0.62, 0.62):
        wc = P(u, 0.17)
        wh = cv.ell(wc[0], wc[1], 6.2 * s, 6.2 * s)
        cv.put(wh, '#07090C')
        cv.put(cv.ell(wc[0], wc[1], 2.6 * s, 2.6 * s), chrome, 0.6)
        arch = cv.ring(wc[0], wc[1], 6.2 * s, 7.6 * s) & (cv.yy < wc[1])
        cv.put(arch & body_m, body, 0.7)
    bum = cv.box(min(P(0.9, 0.3)[0], P(1.04, 0.22)[0]), yb - 0.3 * H, max(P(0.9, 0.3)[0], P(1.04, 0.22)[0]), yb - 0.18 * H)
    bum |= cv.box(min(P(-1.04, 0.3)[0], P(-0.9, 0.22)[0]), yb - 0.3 * H, max(P(-1.04, 0.3)[0], P(-0.9, 0.22)[0]), yb - 0.18 * H)
    cv.put(bum, chrome)
    hl = cv.ell(*P(0.97, 0.42), 1.2 * s + 0.4, 1.6 * s + 0.4)
    cv.put(hl, '#5E666E')
    sm = body_m | win
    cap = np.zeros_like(sm)
    for i in range(1, int(3 * s) + 2):
        cap |= edge_top(sm, i)
    cap &= (cv.yy < yb - 0.5 * H)
    cap &= nz(cv.w, cv.h, 2.5, seed, 2) > 0.18
    cv.put(cap, snow, snow_k)
    # snow drifted against the wheels
    drift = cv.ell(x, yb + 0.5, L * 0.6, 2.6 * s) & (cv.yy < yb + 1)
    cv.put(drift & (nz(cv.w, cv.h, 3, seed + 1, 2) > 0.3), snow, snow_k * 0.92)
    return body_m | win


def crate(cv: Cv, x0, yb, w, h, col='#3D271A', snow='#A1AAB7', light=1.0, seed=0, lid=True):
    m = cv.box(x0, yb - h, x0 + w, yb)
    cv.put(m, col, light)
    sl = m & (np.mod(cv.yy - (yb - h), max(3, h / 3)) < 1)
    cv.put(sl, col, light * 0.55)
    cv.put(m & ((cv.xx < x0 + 1) | (cv.xx >= x0 + w - 1)), col, light * 0.7)
    if lid and snow:
        snowcap(cv, m, 2, snow, seed + 3)
    return m


def barrel(cv: Cv, x, yb, r, h, col='#2B3038', band='#5E666E', snow='#A1AAB7', light=1.0, seed=0):
    body = cv.box(x - r, yb - h, x + r, yb) | cv.ell(x, yb - 0.5, r, max(1.0, r * 0.25))
    xs = (cv.xx + 0.5 - x) / max(r, 1)
    sh = np.clip(1.15 - np.abs(xs + 0.35) * 0.8, 0.45, 1.2)
    cv.put(body, col, sh * light)
    for v in (0.2, 0.8):
        cv.put(body & (np.abs(cv.yy + 0.5 - (yb - h * v)) < 0.8), band, sh * light)
    topm = cv.ell(x, yb - h, r, max(1.0, r * 0.3))
    cv.put(topm, snow if snow else col, light)
    return body | topm


def railing(cv: Cv, x0, x1, ytop, ybot, step, col='#0C0F15', snow='#A1AAB7', spikes=False):
    m = cv.box(x0, ytop, x1, ytop + 1.5) | cv.box(x0, ybot - 2, x1, ybot - 0.5)
    for x in np.arange(x0, x1, step):
        m |= cv.box(x, ytop, x + 1, ybot)
        if spikes:
            m |= cv.poly([(x - 0.5, ytop), (x + 1.5, ytop), (x + 0.5, ytop - 3)])
    cv.put(m, col)
    snowcap(cv, cv.box(x0, ytop, x1, ytop + 1.5), 1, snow, 11)
    return m


def wire(cv: Cv, a, b, sag, col, r=0.45):
    pts = []
    n = max(2, int(abs(b[0] - a[0]) / 3) + 2)
    for i in range(n + 1):
        u = i / n
        pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + sag * 4 * u * (1 - u)))
    m = cv.seg(pts, r)
    cv.put(m, col)
    return m


# ================================================================================================= sheets
def puff(n, fw, fh, cols, seed, grow=(0.30, 0.48), thin=0.55, light=(0.5, -0.6), drift=0.0):
    return K.puff_sheet(n, fw, fh, cols, seed, grow=grow, thin=thin, light=light, drift=drift)


def steam_sheet(n=6, fw=150, fh=96, seed=4401, warm=True):
    """Big soft steam clouds lit from below (platform lamps): warm undersides, cold tops."""
    cols = (['#2A3646', '#3A4859', '#4F5E70', '#6E6A66', '#8E8070', '#B09A80'] if warm else
            ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7'])
    return K.puff_sheet(n, fw, fh, cols, seed, grow=(0.30, 0.50), thin=0.5, light=(0.15, 0.9), drift=0.06)


def fire_smoke_sheet(n=8, fw=72, fh=56, seed=1021, hot=True):
    """Smoke lit by fire from below: orange-brown undersides, sooty tops."""
    cols = (['#0E0B0A', '#1A1412', '#2A1E18', '#3E2A1E', '#5A3820', '#7A4A24'] if hot else
            ['#0E0F12', '#17191D', '#22242A', '#2E3036', '#3D3E42'])
    return K.puff_sheet(n, fw, fh, cols, seed, grow=(0.28, 0.5), thin=0.42, light=(0.1, 0.95), drift=0.03)


def flame_sheet_tall(n=8, fw=30, fh=64, seed=21):
    return Q.flame_sheet(n, fw, fh, seed=seed)


def paper_sheet(n=6, seed=31):
    """A burning scrap of paper tumbling (6 x 6, n frames): pale sheet, glowing edge."""
    fw = fh = 7
    out = np.zeros((fh, fw * n, 4), np.uint8)
    cols = [hexf('#FCE0A0'), hexf('#F2A044'), hexf('#D8662A'), hexf('#6B6350'), hexf('#B3A98D')]
    for i in range(n):
        a = i / n * math.pi
        cx, cy = 3.0, 3.0
        w2 = abs(math.cos(a)) * 2.6 + 0.6
        h2 = 2.0
        yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
        m = (np.abs(xx + 0.5 - cx) <= w2) & (np.abs(yy + 0.5 - cy) <= h2)
        fr = np.zeros((fh, fw, 4), np.uint8)
        fr[m, :3] = cols[4 if i % 2 else 3].astype(np.uint8)
        e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        fr[e, :3] = cols[(i % 3)].astype(np.uint8)
        fr[m, 3] = 255
        out[:, i * fw:(i + 1) * fw] = fr
    return out


def crow_sheet():
    """A crow flying (4 frames, 11 x 7): wings up, level, down, level."""
    fw, fh = 11, 7
    out = np.zeros((fh, fw * 4, 4), np.uint8)
    body = hexf('#0A0B0E')
    edge = hexf('#2A2E36')
    shapes = [
        ["...#...#...", "....#.#....", ".....#.....", "....###....", "...........", "...........", "..........."],
        ["...........", "...........", "##..###..##", ".#########.", "....###....", "...........", "..........."],
        ["...........", "...........", "....###....", "..#######..", ".##.###.##.", "#.........#", "..........."],
        ["...........", "...........", "#...###...#", ".#########.", "....###....", "...........", "..........."],
    ]
    for i, sh in enumerate(shapes):
        for y, row in enumerate(sh):
            for x, ch in enumerate(row):
                if ch == '#':
                    out[y + 0, i * fw + x, :3] = (edge if y <= 1 else body).astype(np.uint8)
                    out[y + 0, i * fw + x, 3] = 255
    return out


def pigeon_sheet():
    """A pigeon on a ledge (2 frames, 9 x 7): head up / head bobbed."""
    fw, fh = 9, 7
    out = np.zeros((fh, fw * 2, 4), np.uint8)
    pal = {'d': hexf('#2A2E36'), 'm': hexf('#4A5060'), 'l': hexf('#6E7686'), 'w': hexf('#9AA2AE'), 'e': hexf('#0A0B0E')}
    shapes = [
        [".......lm", "......mlw", "..mmmmmm.", ".mllllmm.", "dmmmmmmd.", "..d..d...", "........."],
        [".........", "......lm.", "..mmmmmlw", ".mllllmm.", "dmmmmmmd.", "..d..d...", "........."],
    ]
    for i, sh in enumerate(shapes):
        for y, row in enumerate(sh):
            for x, ch in enumerate(row):
                if ch in pal:
                    out[y, i * fw + x, :3] = pal[ch].astype(np.uint8)
                    out[y, i * fw + x, 3] = 255
    return out


def cat_sheet():
    """A cat curled on a chair cushion (2 frames, 16 x 9): breathing / the tail tip flicks."""
    fw, fh = 16, 9
    out = np.zeros((fh, fw * 2, 4), np.uint8)
    pal = {'d': hexf('#14100E'), 'm': hexf('#2E2620'), 'l': hexf('#4E4034'), 'h': hexf('#6E5A46'), 'e': hexf('#8EA060')}
    shapes = [
        ["................", "..d.d...........", "..dmmd..........", ".dmmmmdmmmmm....", ".dmmlmmmmmlmmd..", "..dmmmmmmlhmmd..",
         "...dmmmmmmmmmd..", "....ddddddddd.dd", "..............d."],
        ["................", "..d.d...........", "..dmmd..........", ".dmmmmdmmmmm....", ".dmmlmmmmmlmmd..", "..dmmmmmmlhmmmd.",
         "...dmmmmmmmmmmd.", "....dddddddddddd", "................"],
    ]
    for i, sh in enumerate(shapes):
        for y, row in enumerate(sh):
            for x, ch in enumerate(row):
                if ch in pal:
                    out[y, i * fw + x, :3] = pal[ch].astype(np.uint8)
                    out[y, i * fw + x, 3] = 255
    return out


def glow(w, h, blobs, step=6.0, ox=0, oy=0):
    """Additive glow sprite (black = clear): blobs = [(cx, cy, rx, ry, (r, g, b), power)]."""
    return Q.glow_sprite(w, h, blobs, step, ox, oy)


def flame_mass(n=8, fw=48, fh=88, seed=51, tongues=3, cool=0.0):
    """n frames of a living fire mass (bottom-anchored, transparent): several licking tongues of different
    lengths, turbulent edges advected upward, deep red outside, orange, yellow, a small pale core at the base.
    Frames cycle smoothly (the tongues' lengths and the noise loop over n)."""
    pal = [hexf(c) for c in ('#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCD27A', '#FFF0C8')]
    out = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    u = (yy + 0.5) / fh                                     # 0 top .. 1 bottom
    rng = np.random.default_rng(seed)
    tg = [(rng.uniform(0.28, 0.72), rng.uniform(0.55, 1.0), rng.uniform(0, 2 * math.pi), rng.uniform(0.2, 0.32))
          for _ in range(tongues)]
    nz2 = pg.value_noise(fw, fh * 2, 5, seed * 13 + 1, octaves=3)
    nz3 = pg.value_noise(fw, fh * 2, 2.5, seed * 17 + 3, octaves=2)
    for i in range(n):
        ph = i / n * 2 * math.pi
        off = int(round((i / n) * fh)) % fh
        turb = nz2[fh - off:2 * fh - off] if off else nz2[fh:2 * fh]
        fine = nz3[fh - off:2 * fh - off] if off else nz3[fh:2 * fh]
        dens = np.zeros((fh, fw), np.float32)
        for (bx, ln, p0, wd) in tg:
            L_ = ln * (0.82 + 0.18 * math.sin(ph + p0)) * (0.9 + 0.1 * math.sin(2 * ph + p0 * 1.7))
            top = 1.0 - L_
            v = np.clip((u - top) / max(1e-3, 1.0 - top), 0, 1)             # 0 at the tongue tip .. 1 at the base
            sway = (np.sin(ph + p0 + u * 6.0) * 0.06 + np.sin(2 * ph + u * 11.0 + p0) * 0.025) * (1 - v)
            cx = bx + sway
            half = wd * (v ** 0.55) * (0.9 + 0.1 * math.sin(ph * 2 + p0))
            d = 1.0 - np.abs((xx + 0.5) / fw - cx) / np.maximum(half, 1e-3)
            dens = np.maximum(dens, np.clip(d, 0, 1) * (u > top))
        dens = dens + (turb - 0.5) * 0.7 * (1 - u * 0.5) + (fine - 0.5) * 0.25
        base = np.clip((u - 0.86) / 0.14, 0, 1) * np.clip(1 - np.abs((xx + 0.5) / fw - 0.5) / 0.48, 0, 1)
        dens = np.maximum(dens, base * 0.9)
        th = pg.bayer(fw, fh, i, 0)
        m = dens > 0.22 + th * 0.12
        heat = np.clip(dens * 0.95 + u * 0.32 - 0.40 - cool, 0, 1)
        idx = np.clip((heat * (len(pal) - 1.2) + (th - 0.5) * 0.8).astype(int), 0, len(pal) - 1)
        fr = np.zeros((fh, fw, 4), np.uint8)
        for k, c in enumerate(pal):
            sel = m & (idx == k)
            fr[sel, :3] = c.astype(np.uint8)
            fr[sel, 3] = 255
        out[:, i * fw:(i + 1) * fw] = fr
    return out


# ================================================================================================= round 11
# Soft smoke and steam (real alpha in a few levels, never an ordered-dither checkerboard) and fire that reads as
# fire: translucent red fringe -> orange -> yellow -> a white-hot core at the base, no dark rim, so the core is the
# brightest pixel and the flame glows against any dark-to-mid background.

def pnoise(x, y, seed=0, py=0):
    """Smooth value noise (0..1) at float coordinates, periodic in y with period `py` cells (0 = not periodic)."""
    x = np.asarray(x, np.float64)
    y = np.asarray(y, np.float64)
    xi, yi = np.floor(x), np.floor(y)
    fx, fy = x - xi, y - yi
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    y0 = np.mod(yi, py) if py else yi
    y1 = np.mod(yi + 1, py) if py else yi + 1
    h00 = hsh(xi, y0, seed)
    h10 = hsh(xi + 1, y0, seed)
    h01 = hsh(xi, y1, seed)
    h11 = hsh(xi + 1, y1, seed)
    return (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy


def fbm(x, y, seed=0, octaves=3, py=0):
    """Fractal sum of pnoise (0..1); with py > 0 every octave stays periodic in y (period py cells of octave 0)."""
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        k = 2 ** o
        v = v + pnoise(np.asarray(x) * k, np.asarray(y) * k, seed + o * 17, py * k) * amp
        tot += amp
        amp *= 0.5
    return v / tot


SMOKE_SOOT = ['#0C0B0B', '#141212', '#1C1918', '#25211F', '#302A26', '#3D342E', '#4B3F36']
SMOKE_FIRE = ['#100C0B', '#1A1412', '#261C17', '#36251C', '#4C3020', '#663E24', '#844E2A', '#A6643A']
SMOKE_GREY = ['#101216', '#181B20', '#22262C', '#2D3138', '#3A3E45', '#4A4D53', '#5C5E62']
STEAM_LAMP = ['#2A3646', '#3A4859', '#4F5E70', '#6A7686', '#8A8E94', '#A9A49C', '#C6BBA8', '#DCD2C2']
STEAM_COLD = ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2']


def soft_puff_sheet(n, fw, fh, ramp, seed, grow=(0.30, 0.50), light=(0.3, -0.8), thin=0.55, drift=0.0, rise=0.0,
                    alpha=0.92, levels=8, lobes=12, wisp=0.45):
    """n frames of a volumetric puff with soft alpha: cauliflower lobes shaded as small spheres lit from `light`
    (x right, y down; (0, 1) = lit from below), the colour snapped to `ramp` (dark -> light) by that shading, the
    alpha a smooth falloff of the density in `levels` steps.  The puff grows (radius fraction of the frame at the
    first / last frame), churns, drifts by `drift` and rises by `rise` (fractions of the frame) and thins out."""
    rng = np.random.default_rng(seed)
    L = []
    for j in range(lobes):
        r = rng.uniform(0.30, 0.72)
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.1, 0.85) * (1.0 - 0.55 * (r - 0.30) / 0.42)
        L.append((math.cos(a) * d, math.sin(a) * d * 0.8, r, rng.uniform(0, 2 * math.pi)))
    rmax = max(l_[2] for l_ in L)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float64)
    pal = np.stack([hexf(c) for c in ramp])
    lx, ly = light
    ln = math.sqrt(lx * lx + ly * ly + 0.25)
    lx, ly, lz = lx / ln, ly / ln, 0.5 / ln
    out = np.zeros((fh, fw * n, 4), np.uint8)
    for i in range(n):
        u = i / max(1, n - 1)
        s = grow[0] + (grow[1] - grow[0]) * u
        rx, ry = fw * s, fh * s * 0.92
        cx = fw / 2 + drift * u * fw
        cy = fh / 2 + 0.05 * fh * (1 - u) - rise * u * fh
        Hh = np.zeros((fh, fw))
        sh = np.zeros((fh, fw))
        for (ox, oy, rr, ph) in L:
            ax = cx + (ox + 0.08 * math.sin(ph + u * 2.4)) * rx
            ay = cy + (oy + 0.06 * math.cos(ph + u * 2.0)) * ry
            k = 0.9 + 0.2 * u
            qx, qy = (xx + 0.5 - ax) / (rx * rr * k), (yy + 0.5 - ay) / (ry * rr * k)
            q = qx * qx + qy * qy
            nz_ = np.sqrt(np.clip(1.0 - q, 0, 1))
            h = nz_ * rr
            top = (q < 1.0) & (h > Hh)
            shade = np.clip(qx * lx + qy * ly + nz_ * lz, -1, 1) * 0.5 + 0.5
            sh = np.where(top, shade, sh)
            Hh = np.where(top, h, Hh)
        nzf = fbm((xx + i * 0.7) / max(3.0, fw / 6.0), (yy - i * 0.9) / max(3.0, fh / 6.0), seed + 3, 3)
        dens = np.clip(Hh / rmax, 0, 1)
        # the rim frays into wisps: noise eats the thin outer part, the dense core stays
        dens = np.clip(dens - (1.0 - nzf) * wisp * (1.0 - dens) * 1.6 + (nzf - 0.5) * 0.1, 0, 1)
        a = np.clip((dens - 0.02) / 0.62, 0, 1)
        a = a * a * (3 - 2 * a) * alpha * (1.0 - thin * u)
        a = np.round(a * levels) / levels
        v = np.clip(sh * 0.85 + (nzf - 0.5) * 0.25 + 0.08, 0, 1)
        idx = np.clip(np.round(v * (len(pal) - 1)).astype(int), 0, len(pal) - 1)
        fr = np.zeros((fh, fw, 4), np.uint8)
        fr[..., :3] = pal[idx].astype(np.uint8)
        fr[..., 3] = np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
        fr[fr[..., 3] == 0, :3] = 0
        out[:, i * fw:(i + 1) * fw] = fr
    return out
