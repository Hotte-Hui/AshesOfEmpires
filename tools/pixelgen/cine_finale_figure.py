"""cine_finale_figure -- the people at the two desks of the X1 finale close-ups (owner: trans-finale).

Over-the-shoulder staging: the back of the head and the shoulders sit in the foreground at the bottom of the
frame.  Every arm is a 3D chain with real proportions -- shoulder -> upper arm (29 cm) -> elbow -> forearm
(26 cm) -> wrist -> hand (palm 9.5 cm, three-joint fingers, two-joint thumb) -- solved with a 3D two-bone IK
(elbow pole out and down, or down in front of the chest when the hand crosses the body) and projected through
a perspective camera fitted to the set (high behind the sitter, looking down over the shoulder).  So the
foreshortening comes from the camera, not from animated screen lengths: a hanging upper arm is short on
screen, a reaching forearm gets shorter, a hand on the desk is seen from above (back of the hand, knuckles,
curled fingers dropping out of sight under them).  When a target is out of reach the upper body leans in
(rotation about the hips), and the head and shoulders of the body art follow the projected lean.

* layers: the arm layers hold forearm + hand (+ a held prop); the body layer holds the upper arms (under the
  coat's back and shoulder caps), the back, collar / scarf and the head -- so the sleeve runs on unbroken
  from the shoulder seam over the elbow to the cuff, and an elbow behind the back is simply hidden
* light: one lamp model for the whole figure -- the set lamp's pool (irradiance) with the 3D direction to the
  bulb for the lambert term; the back faces away from the lamp and stays dark, the forearms brighten towards
  the wrist as they reach into the pool
* hands: z-buffered capsules (fingers, thumb) and a domed palm, shaded from a height field; knuckle and
  tendon highlights, nails on fingers that point at the camera, separating creases, contact shadow on the desk
Everything is rasterised fresh per frame from geometry (no scaled or rotated pixels), deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import pg

H_ = pg.hx


def R(*hexes):
    return [H_(h) for h in hexes]


# ------------------------------------------------------------------------------------------- costumes
COSTUMES = {
    'konrad': {
        'skin': R('#1E1418', '#372A37', '#5B3B43', '#86584F', '#A86E58', '#C38A6C', '#D4A17F', '#E2B691',
                  '#ECC9A1', '#F6DDBA'),
        'nail': R('#86584F', '#B98C78', '#D9B4A0', '#F1D6C2'),
        'sleeve': R('#020210', '#060818', '#0B0F24', '#131A35', '#1F2747', '#2B3858', '#3B4A6C', '#4E5D80',
                    '#66749A', '#8590B2'),
        'cuff': R('#24302E', '#3E4A47', '#62716E', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'),
        'cuff_style': 'shirt',
        'hair': R('#08060B', '#130E12', '#1F161A', '#2E2026', '#432F30', '#5B4038', '#765443', '#946B50',
                  '#B08660'),
        'scarf': R('#1A1810', '#2E2A1E', '#48422E', '#666046', '#857C5C', '#A49A76', '#C1B793', '#D9D0AE',
                   '#EEE6C9'),
        'quilt': False,
        'shoulder_w': 64, 'half_w_m': 0.19, 'r_m': (0.060, 0.050, 0.040), 'hand': 0.88, 'head': 'bare',
    },
    'alexei': {
        'skin': R('#1B1414', '#36262E', '#5C3637', '#8A5242', '#B5724F', '#C98A60', '#D69868', '#E3AE7C',
                  '#EFC490', '#F8DCAE'),
        'nail': R('#8A5242', '#BE8C70', '#DDB494', '#F2D2B4'),
        'sleeve': R('#010B0B', '#03140F', '#0A2420', '#123129', '#1C4034', '#2C5242', '#3D624F', '#52735C',
                    '#698870', '#86A08A'),
        'cuff': R('#141413', '#1D1D1B', '#2A2C2B', '#3D3C37', '#595B5A', '#76787A', '#94968F', '#B2B3AA'),
        'cuff_style': 'knit',
        'fur': R('#0E0C0B', '#1D1916', '#2A2420', '#3A2F28', '#4C3F33', '#5E5044', '#76664F', '#8F7E64',
                 '#A9987C'),
        'quilt': True,
        'shoulder_w': 70, 'half_w_m': 0.205, 'r_m': (0.068, 0.056, 0.045), 'hand': 0.93, 'head': 'ushanka',
    },
    'irina': {
        'skin': R('#1B1414', '#3A2A30', '#5E3E3E', '#8A5A4E', '#B07A62', '#C8957A', '#D9AE90', '#E8C6A6',
                  '#F4DEC4', '#FBEBD8'),
        'nail': R('#8A5A4E', '#C29A8A', '#E0BCAA', '#F6DCCC'),
        'sleeve': R('#05090F', '#0A1219', '#10191F', '#1A2328', '#2A2D2C', '#3B3F3B', '#4F534C', '#666A60',
                    '#7F8275', '#9A9B8B'),
        'cuff': R('#1E1218', '#2E1C24', '#46283A', '#5E3348', '#7A4458', '#965A6C', '#B07888'),
        'cuff_style': 'knit',
        'quilt': False,
        'shoulder_w': 58, 'half_w_m': 0.17, 'r_m': (0.056, 0.047, 0.036), 'hand': 0.84, 'head': None,
        'lu': 0.36, 'lf': 0.33, 'coat': R('#05090F', '#0A1219', '#10191F', '#1A2328', '#2A2D2C', '#3B3F3B'),
    },
}

LU, LF = 0.29, 0.26            # upper arm, forearm (m)
COMFORT = 0.86                 # beyond this share of the full reach the upper body leans in instead
HIP_R = 0.52                   # shoulder line above the hip pivot (lean radius, m)


# ------------------------------------------------------------------------------------------- camera
def _v(*a):
    return np.array(a, np.float64)


def _norm(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


class Cam3:
    """Perspective camera of one close-up, in the sitter's frame: x right, y up, z forward (metres); desk
    top y = 0, the mid-shoulder point at rest S0 = (0, HS, 0) projects onto `anchor` (set px), and the
    shoulder joints (+-half_w_m) land +-half_w_px from it.  Fitted to the sets (camera 1.7 m above the
    shoulders, 0.4 m behind): the home row of the typewriter 33 cm in front of the shoulders sits ~110 px
    above them, the platen ~170 px, the head centre ~45 px, a hand is ~20 px wide."""

    def __init__(self, anchor, half_w_px, half_w_m=0.19, HS=0.31, CH=1.7, CB=0.4, pitch_deg=23.0):
        self.ax, self.ay = float(anchor[0]), float(anchor[1])
        self.HS = HS
        th = math.radians(pitch_deg)
        self.f = _v(0.0, -math.sin(th), math.cos(th))
        self.u = _v(0.0, math.cos(th), math.sin(th))
        self.r = _v(1.0, 0.0, 0.0)
        self.C = _v(0.0, HS + CH, -CB)
        self.F = 1.0
        self.ox = self.oy = 0.0
        x, y, Z = self._raw(_v(half_w_m, HS, 0.0))
        self.F = half_w_px * Z / half_w_m
        x0, y0, _ = self._raw(_v(0.0, HS, 0.0))
        self.ox, self.oy = self.ax - x0, self.ay - y0

    def _raw(self, p):
        d = np.asarray(p, np.float64) - self.C
        Z = float(d @ self.f)
        Y = float(d @ self.u)
        return self.F * float(d[0]) / Z, -self.F * Y / Z, Z

    def proj(self, p):
        x, y, Z = self._raw(p)
        return x + self.ox, y + self.oy, Z

    def p2(self, p):
        x, y, _ = self.proj(p)
        return (x, y)

    def scale(self, p) -> float:
        return self.F / self._raw(p)[2]

    def ray(self, sx, sy):
        X = (sx - self.ox) / self.F
        Y = -(sy - self.oy) / self.F
        return X * self.r + Y * self.u + self.f

    def on_plane_y(self, sx, sy, h=0.0):
        d = self.ray(sx, sy)
        t = (h - self.C[1]) / d[1]
        return self.C + t * d

    def on_plane_z(self, sx, sy, z):
        d = self.ray(sx, sy)
        t = (z - self.C[2]) / d[2]
        return self.C + t * d

    def to_cam(self, v):
        """World vector -> screen-space vector (x right, y DOWN, z towards the viewer)."""
        return np.stack([v[..., 0], -(v[..., 1] * self.u[1] + v[..., 2] * self.u[2]),
                         -(v[..., 1] * self.f[1] + v[..., 2] * self.f[2])], -1)

    def from_screen_normal(self, n):
        """Screen-space normal (x right, y down, z to viewer) -> world."""
        nx, ny, nz = n[..., 0], n[..., 1], n[..., 2]
        return np.stack([nx, -ny * self.u[1] - nz * self.f[1], -ny * self.u[2] - nz * self.f[2]], -1)

    def depth_grid(self, xx, yy, P0, n):
        """Camera depth Z of the plane (P0, n) under the pixels (xx, yy)."""
        X = (xx - self.ox) / self.F
        Y = -(yy - self.oy) / self.F
        dx = X
        dy = Y * self.u[1] + self.f[1]
        dz = Y * self.u[2] + self.f[2]
        num = (P0[0] - self.C[0]) * n[0] + (P0[1] - self.C[1]) * n[1] + (P0[2] - self.C[2]) * n[2]
        den = dx * n[0] + dy * n[1] + dz * n[2]
        den = np.where(np.abs(den) < 1e-6, 1e-6, den)
        return num / den


class Light3:
    """The set lamp seen by a figure: irradiance from the set's lamp pool (so the hands match the desk art),
    direction from the 3D bulb position (foot point unprojected onto the desk, height from the lamp's z)."""

    def __init__(self, lamp: kit.Lamp, cam: Cam3, ambient=0.08, gain=1.0):
        self.lamp = lamp
        self.cam = cam
        foot = cam.on_plane_y(lamp.sx, lamp.sy, 0.0)
        sc = cam.scale(foot)
        self.pos = foot + _v(0.0, lamp.z / sc * 0.95, 0.0)
        self.ambient = ambient
        self.gain = gain

    def pool_at(self, P):
        """Irradiance at world points P (..., 3), sampled where the desk lies under them."""
        sh = P.shape[:-1]
        Pf = P.reshape(-1, 3)
        cam = self.cam
        d = np.stack([Pf[:, 0] - cam.C[0], -cam.C[1] + 0.0 * Pf[:, 1], Pf[:, 2] - cam.C[2]], -1)
        Z = d[:, 1] * cam.f[1] + d[:, 2] * cam.f[2]
        Y = d[:, 1] * cam.u[1] + d[:, 2] * cam.u[2]
        sx = cam.F * d[:, 0] / Z + cam.ox
        sy = -cam.F * Y / Z + cam.oy
        return self.lamp.pool(sx, sy).reshape(sh)

    def lambert(self, P, n_world, wrap=0.25):
        L = self.pos - P
        L = L / (np.linalg.norm(L, axis=-1, keepdims=True) + 1e-9)
        d = (n_world * L).sum(-1)
        return np.clip((d + wrap) / (1.0 + wrap), 0, 1)


# ------------------------------------------------------------------------------------------- IK
def ik3(S, W, pole, lu=LU, lf=LF):
    """Two-bone IK in 3D.  Returns (elbow, wrist, overflow) -- the wrist is pulled back onto the reach
    sphere when the target is too far (overflow = the missing distance)."""
    d = W - S
    D = float(np.linalg.norm(d))
    reach = (lu + lf) * 0.995
    over = max(0.0, D - COMFORT * (lu + lf))
    n = d / max(D, 1e-9)
    if D > reach:
        W = S + n * reach
        D = reach
    D = max(D, abs(lu - lf) + 0.01)
    a = (lu * lu - lf * lf + D * D) / (2.0 * D)
    r = math.sqrt(max(lu * lu - a * a, 0.0))
    c = S + n * a
    pv = pole - c
    pv = pv - n * float(pv @ n)
    pv = _norm(pv)
    if float(np.linalg.norm(pv)) < 0.5:
        pv = _norm(np.cross(n, _v(0, 0, 1)))
    return c + pv * r, W, over


def default_pole(S, W, side: str, mid_x: float = 0.0, crossing=None):
    """Elbow pole: out and down beside the body; when the wrist crosses the midline the elbow drops in
    front of the chest instead of swinging up past the head."""
    sgn = -1.0 if side == 'L' else 1.0
    out = _v(S[0] + sgn * 0.26, S[1] - 0.42, S[2] - 0.12)
    across = _v(S[0] + sgn * 0.05, S[1] - 0.42, S[2] + 0.22)
    cr = (mid_x - W[0]) * sgn if crossing is None else crossing
    k = float(np.clip((cr + 0.02) / 0.10, 0.0, 1.0))
    return out * (1 - k) + across * k


# ------------------------------------------------------------------------------------------- hand model
F_LEN = [(0.044, 0.026, 0.020), (0.048, 0.029, 0.021), (0.045, 0.028, 0.020), (0.035, 0.020, 0.018)]
F_RAD = [0.0088, 0.0092, 0.0086, 0.0076]
F_OFF = [-0.36, -0.12, 0.12, 0.35]          # finger bases across the knuckle line (x knuckle width, thumb side -)
PALM_L, PALM_WW, PALM_WK = 0.094, 0.058, 0.084
CURL_J = (1.05, 1.55, 0.95)                 # MCP, PIP, DIP angles at curl 1 (rad)


ANCHOR_NAMES = ('palm', 'tips', 'pinch', 'grip', 'knuckles')


def anchor_offset(parts, anchor, W):
    """Offset (world) from the wrist to the hand's acting point: a name or blend weights over ANCHOR_NAMES."""
    if isinstance(anchor, str):
        return parts['anchors'][anchor] - W
    wsum = float(sum(anchor)) or 1.0
    off = np.zeros(3)
    for wgt, nm in zip(anchor, ANCHOR_NAMES):
        if wgt:
            off = off + (parts['anchors'][nm] - W) * (float(wgt) / wsum)
    return off


class HandPose:
    """curl 0 = straight .. 1 = fist (per finger override `curls`); thumb: side | under | pinch | out | wrap;
    spread fans the fingers; pitch raises the fingers (+) / drops them (-) at the wrist; roll turns the hand
    on its long axis (+ = thumb side up); rest adds the relaxed bend of a hand lying on a desk."""

    def __init__(self, curl=0.25, curls=None, thumb='side', spread=0.0, pitch=0.0, roll=0.0, lifted=None):
        self.curl = curl
        self.curls = list(curls) if curls else [None] * 4
        self.thumb = thumb
        self.spread = spread
        self.pitch = pitch
        self.roll = roll
        self.lifted = list(lifted) if lifted else [0.0] * 4


def hand_frame(yaw, pitch, roll, side):
    """Orthonormal hand frame: a along the hand (to the fingers), t towards the thumb, n out of the back
    of the hand.  yaw 0 = straight forward (+z), + turns right; pitch + lifts the fingers."""
    a = _v(math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch))
    up = _v(0.0, 1.0, 0.0)
    left = _norm(np.cross(a, up))                     # for a forward hand: (-1, 0, 0)
    t = left if side == 'R' else -left
    n = _norm(np.cross(t, a)) if side == 'R' else _norm(np.cross(a, t))
    if n[1] < 0:
        n = -n
    if abs(roll) > 1e-4:
        c, s = math.cos(roll), math.sin(roll)
        t, n = t * c + n * s, n * c - t * s
    return a, t, n


def hand_parts(W, yaw, pose: HandPose, side: str, k=1.0):
    """3D parts of a hand with its wrist at W.  Returns dict: caps [(A, B, rA, rB, pid, finger, seg)],
    palm (outline pts, centre, normal, half thickness), anchors {palm, tips, pinch, grip, knuckles}."""
    a, t, n = hand_frame(yaw, pose.pitch, pose.roll, side)

    def L(lx, lt, ln):
        return W + a * (lx * k) + t * (lt * k) + n * (ln * k)
    caps = []
    pl = PALM_L
    # palm outline (thumb side t+): wrist narrower, thenar bulge on the thumb side, knuckle line arched
    outline = [L(-0.004, 0.029, 0), L(0.024, 0.040, 0), L(0.052, 0.044, 0), L(pl - 0.006, 0.040, 0),
               L(pl + 0.002, 0.016, 0), L(pl + 0.004, -0.006, 0), L(pl - 0.001, -0.028, 0), L(pl - 0.010, -0.041, 0),
               L(0.050, -0.040, 0), L(0.020, -0.033, 0), L(-0.004, -0.028, 0)]
    centre = L(pl * 0.48, 0.0, 0.0)
    tips = []
    knuck = []
    fing = []
    nails = []
    curl_l = []
    for i in range(4):
        c = pose.curls[i] if pose.curls[i] is not None else pose.curl
        c = float(np.clip(c, 0, 1))
        base_t = -F_OFF[i] * PALM_WK            # index on the thumb side (+t)
        kx = pl - (0.0045 if i == 3 else (0.0015 if i == 2 else 0.0)) - (0.002 if i == 0 else 0.0)
        p = L(kx, base_t, 0.002)
        knuck.append(p)
        # relaxed fingers converge a little towards the middle finger; spread fans them out
        sp = -F_OFF[i] * pose.spread * 0.55 + F_OFF[i] * 0.22 * (1.0 - min(1.0, pose.spread * 2.0))
        # direction in the palm plane fanned by spread, then bent down (towards -n) joint by joint
        d0 = _norm(a * math.cos(sp) + t * math.sin(sp))
        ang = 0.0
        rr = F_RAD[i] * k
        pts = [p]
        lift = pose.lifted[i]
        for j in range(3):
            ang += c * CURL_J[j] + (0.0 if j else -lift)
            dj = d0 * math.cos(ang) - n * math.sin(ang)
            q = p + dj * (F_LEN[i][j] * k)
            r1 = rr * (0.94 if j < 2 else 0.86)
            caps.append((p, q, rr, r1, 10 + i * 3 + j, i, j))
            p, rr = q, r1
            pts.append(p)
        tips.append(p)
        fing.append(pts)
        curl_l.append(c)
        nails.append(d0 * math.sin(ang) + n * math.cos(ang))     # dorsal normal of the last segment
    # thumb (two visible segments from the base of the thenar)
    tb = L(0.020, 0.031, -0.006)
    th = pose.thumb
    if th == 'side':
        d1 = _norm(a * 0.80 + t * 0.52 - n * 0.18)
        d2 = _norm(a * 0.92 + t * 0.20 - n * 0.30)
    elif th == 'under':
        d1 = _norm(a * 0.62 + t * 0.10 - n * 0.78)
        d2 = _norm(a * 0.55 - t * 0.45 - n * 0.70)
    elif th == 'out':
        d1 = _norm(a * 0.45 + t * 0.88 - n * 0.10)
        d2 = _norm(a * 0.62 + t * 0.75 - n * 0.15)
    elif th == 'wrap':                                   # round a knob / an edge: down and across
        d1 = _norm(a * 0.70 + t * 0.20 - n * 0.68)
        d2 = _norm(a * 0.45 - t * 0.50 - n * 0.74)
    else:                                                # pinch: thumb tip meets the index fingertip
        tgt = tips[0] - n * 0.004 * k
        mid = tb + (tgt - tb) * 0.55 + t * 0.012 * k - n * 0.006 * k
        d1 = _norm(mid - tb)
        d2 = _norm(tgt - mid)
    if th == 'pinch':
        m1 = mid
        m2 = tgt
    else:
        m1 = tb + d1 * 0.046 * k
        m2 = m1 + d2 * 0.034 * k
    rt = 0.0105 * k
    caps.append((tb, m1, rt * 1.08, rt, 30, 4, 0))
    caps.append((m1, m2, rt, rt * 0.86, 31, 4, 1))
    anchors = {
        'palm': L(pl * 0.52, 0.0, -0.012),
        'tips': sum(tips) / 4.0,
        'pinch': (tips[0] + m2) * 0.5,
        'grip': (fing[1][1] + fing[2][1]) * 0.5,
        'knuckles': sum(knuck) / 4.0,
        'index': tips[0],
        'thumb': m2,
    }
    return {'caps': caps, 'outline': outline, 'centre': centre, 'n': n, 'a': a, 't': t, 'k': k,
            'anchors': anchors, 'tips': tips, 'knuckles': knuck, 'nails': nails, 'curl': curl_l,
            'pip': [f[1] for f in fing]}


def taper(xx, yy, a, b, r0, r1):
    """Height field of a tapered rod a->b (radius r0 at a, r1 at b).  Returns (h, t, u)."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy + 1e-9
    t = np.clip(((xx - a[0]) * vx + (yy - a[1]) * vy) / L2, 0.0, 1.0)
    px, py = a[0] + t * vx, a[1] + t * vy
    r = r0 + (r1 - r0) * t
    d2 = (xx - px) ** 2 + (yy - py) ** 2
    hgt = np.sqrt(np.clip(r * r - d2, 0, None))
    L = math.sqrt(L2)
    u = ((xx - a[0]) * (-vy) + (yy - a[1]) * vx) / L / np.maximum(r, 1e-3)
    return hgt, t, u


def _bbox(points, pad, w, h):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = min(max(0, int(min(xs) - pad)), w - 1)
    y0 = min(max(0, int(min(ys) - pad)), h - 1)
    x1 = min(w, int(max(xs) + pad) + 1)
    y1 = min(h, int(max(ys) + pad) + 1)
    return x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)


def _ramp_px(t, ramp):
    return kit.tone_to_ramp(np.array([[float(np.clip(t, 0, 1))]], np.float32), ramp, dither=False)[0, 0]


def render_hand(w, h, cam: Cam3, light: Light3, parts, cost: dict, gain=1.0, ambient=0.30):
    """Rasterise one hand (z-buffered).  Returns (rgba, mask, info) on a (h, w) canvas."""
    caps = parts['caps']
    pr = []
    pts2 = []
    for (A, B, rA, rB, pid, fi, sj) in caps:
        ax_, ay_, za = cam.proj(A)
        bx_, by_, zb = cam.proj(B)
        sa, sb = cam.F / za, cam.F / zb
        pr.append(((ax_, ay_), (bx_, by_), rA * sa, rB * sb, za, zb, sa, sb, pid, fi, sj, A, B))
        pts2 += [(ax_, ay_), (bx_, by_)]
    ol = [cam.p2(p) for p in parts['outline']]
    pts2 += ol
    x0, y0, x1, y1 = _bbox(pts2, 5, w, h)
    sw_, sh_ = x1 - x0, y1 - y0
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    xx += 0.5
    yy += 0.5
    zbuf = np.full((sh_, sw_), 1e9)
    owner = np.zeros((sh_, sw_), np.int32)
    Pw = np.zeros((sh_, sw_, 3))
    zc = cam.proj(parts['centre'])[2]
    sc_c = cam.F / zc
    # palm: the plane of the back of the hand, domed
    pm = kit.poly_mask_full(w, h, ol)[y0:y1, x0:x1]
    n = parts['n']
    k = parts['k']
    P0 = parts['centre'] + n * 0.013 * k
    zp = cam.depth_grid(xx, yy, P0, n)
    cx_, cy_ = cam.p2(parts['centre'])
    half = max(4.0, PALM_WK * k * sc_c * 0.55)
    rr = np.sqrt((xx - cx_) ** 2 + (yy - cy_) ** 2) / half
    dome = np.clip(1.0 - rr * rr * 0.55, 0.0, 1.0) * 0.010 * k
    zpalm = zp - dome
    sel = pm & (zpalm < zbuf)
    zbuf[sel] = zpalm[sel]
    owner[sel] = 1
    # world points of the palm pixels (for the light): ray * depth
    X = (xx - cam.ox) / cam.F
    Y = -(yy - cam.oy) / cam.F
    for c_ in range(3):
        rayc = X * cam.r[c_] + Y * cam.u[c_] + cam.f[c_]
        Pw[..., c_] = np.where(sel, cam.C[c_] + rayc * zpalm, Pw[..., c_])
    for (a2, b2, ra, rb, za, zb, sa, sb, pid, fi, sj, A, B) in pr:
        hh, tt, _ = taper(xx, yy, a2, b2, max(ra, 0.7), max(rb, 0.7))
        cov = hh > 0.05
        if not cov.any():
            continue
        zz = za + (zb - za) * tt - hh / (sa + (sb - sa) * tt)
        if fi < 4 and sj == 0:
            zz = zz + 0.0015            # the knuckle of the palm overlaps the finger root
        s2 = cov & (zz < zbuf)
        zbuf[s2] = zz[s2]
        owner[s2] = pid
        for c_ in range(3):
            Pw[..., c_] = np.where(s2, A[c_] + (B[c_] - A[c_]) * tt, Pw[..., c_])
    mask_s = owner > 0
    if not mask_s.any():
        return np.zeros((h, w, 4), np.uint8), np.zeros((h, w), bool), {}
    # height field towards the viewer (px) for the shading normals
    zref = float(zbuf[mask_s].max())
    hgt = np.where(mask_s, (zref - zbuf) * sc_c, 0.0)
    nrm = kit.normals_from_height(hgt.astype(np.float32) * 0.9)
    nw = cam.from_screen_normal(nrm.astype(np.float64))
    lam = light.lambert(Pw, nw, wrap=0.30)
    pool = np.clip(light.pool_at(Pw), 0, 1.2)
    tone = ambient + gain * 0.92 * lam * pool
    # fingers that curl down turn away from the lamp: middle / distal segments darker
    for i in range(4):
        for j in (1, 2):
            tone = np.where(owner == 10 + i * 3 + j, tone - 0.04 * j, tone)
    # the back of the hand darkens towards the wrist (the cuff shades it); tendons from wrist to knuckles
    wx, wy = cam.p2(parts['anchors']['palm'] - parts['a'] * 0.05 * k)
    dw = np.sqrt((xx - wx) ** 2 + (yy - wy) ** 2) / max(PALM_L * k * sc_c * 0.5, 1.0)
    tone = np.where(owner == 1, tone - 0.10 * np.clip(1.0 - dw, 0, 1), tone)
    for i in range(4):
        kx, ky = cam.p2(parts['knuckles'][i])
        bx, by = cam.p2(parts['outline'][0] * 0.5 + parts['outline'][-1] * 0.5 + parts['t'] * F_OFF[i] * -0.02)
        hh, tpar, _ = taper(xx, yy, (bx, by), (kx, ky), 0.8, 0.8)
        tone = np.where((hh > 0.3) & (owner == 1) & (tpar > 0.35), tone + 0.045, tone)
    col = kit.tone_to_ramp(np.clip(tone, 0, 1), cost['skin'], dither=False)
    # creases between parts (different finger / thumb), half-tone at joints inside a finger
    p = np.pad(owner, 1, mode='edge')
    fid = np.where(owner >= 10, np.where(owner >= 30, 4, (owner - 10) // 3), np.where(owner == 1, -2, -1))
    pf = np.pad(fid, 1, mode='edge')
    pz = np.pad(zbuf, 1, mode='edge')
    crease = np.zeros_like(mask_s)
    for q, qz in ((pf[1:-1, 2:], pz[1:-1, 2:]), (pf[2:, 1:-1], pz[2:, 1:-1]), (pf[1:-1, :-2], pz[1:-1, :-2]),
                  (pf[:-2, 1:-1], pz[:-2, 1:-1])):
        # mark the pixel on the far side of a depth step between two different parts
        crease |= (q != fid) & (q != -1) & (fid != -1) & (zbuf > qz + 0.003)
    crease &= mask_s
    # side-by-side fingers: a dark seam on the far / outer one of every pair of touching fingers
    for q, qz in ((pf[1:-1, 2:], pz[1:-1, 2:]), (pf[2:, 1:-1], pz[2:, 1:-1]), (pf[1:-1, :-2], pz[1:-1, :-2]),
                  (pf[:-2, 1:-1], pz[:-2, 1:-1])):
        crease |= (fid >= 0) & (q >= 0) & (q != fid) & ((zbuf > qz - 0.0008) & ((zbuf > qz + 0.0008) | (fid > q)))
    crease &= mask_s
    dark = kit.tone_to_ramp(np.clip(tone - 0.30, 0, 1), cost['skin'], dither=False)
    col[crease] = dark[crease]
    jc = np.zeros_like(mask_s)
    for q in (p[1:-1, 2:], p[2:, 1:-1]):
        jc |= (q != owner) & (q >= 10) & (owner >= 10) & (q < 30) & (owner < 30) & ((q - 10) // 3 == (owner - 10) // 3)
    jc &= mask_s & ~crease
    mid = kit.tone_to_ramp(np.clip(tone - 0.10, 0, 1), cost['skin'], dither=False)
    col[jc] = mid[jc]

    def put_px(pt, t_off, ramp=None, only=None):
        ix, iy = int(pt[0]) - x0, int(pt[1]) - y0
        if 0 <= iy < sh_ and 0 <= ix < sw_ and mask_s[iy, ix] and (only is None or owner[iy, ix] in only):
            col[iy, ix] = _ramp_px(tone[iy, ix] + t_off, ramp or cost['skin'])
    # knuckle highlights (they face the lamp and the camera), shallow valleys between them, and the
    # middle-joint knuckles of curled fingers
    for i in range(4):
        q = cam.p2(parts['knuckles'][i] + parts['n'] * 0.004 * k)
        put_px(q, 0.14)
        put_px((q[0] + 1, q[1]), 0.08)
        if i < 3:
            vq = cam.p2((parts['knuckles'][i] + parts['knuckles'][i + 1]) * 0.5 - parts['a'] * 0.006 * k)
            put_px(vq, -0.08, only=(1,))
        if parts['curl'][i] > 0.3:
            put_px(cam.p2(parts['pip'][i] + parts['n'] * 0.004 * k), 0.12)
    # nails: on a finger whose last segment points away from the camera the nail plate faces it
    for i in range(4):
        A, B = [c for c in caps if c[4] == 10 + i * 3 + 2][0][:2]
        a2, b2 = cam.p2(A), cam.p2(B)
        dl = math.dist(a2, b2)
        if dl < 1.6 or float(parts['nails'][i] @ (-cam.f)) < 0.35:
            continue
        for ss in (0.55, 0.85):
            put_px((a2[0] + (b2[0] - a2[0]) * ss, a2[1] + (b2[1] - a2[1]) * ss), 0.14, cost['nail'],
                   only=(10 + i * 3 + 2,))
    tip = [c for c in caps if c[4] == 31][0][1]
    put_px(cam.p2(tip), 0.10, cost['nail'], only=(31,))
    # silhouette: dark rim away from the lamp, a lighter pixel towards it
    edge = kit.outline_of(mask_s)
    lpx, lpy = cam.p2(light.pos)
    pm2 = np.pad(mask_s, 1)
    ox = pm2[1:-1, 2:].astype(np.float32) - pm2[1:-1, :-2]
    oy = pm2[2:, 1:-1].astype(np.float32) - pm2[:-2, 1:-1]
    lvx, lvy = lpx - xx, lpy - yy
    ln = np.sqrt(lvx * lvx + lvy * lvy) + 1e-6
    facing = -(ox * lvx + oy * lvy) / ln
    col[edge & (facing <= 0.15)] = np.asarray(cost['skin'][1], np.uint8)
    lit = edge & (facing > 0.6)
    col[lit] = kit.tone_to_ramp(np.clip(tone + 0.06, 0, 1), cost['skin'], dither=False)[lit]
    rgba = np.zeros((h, w, 4), np.uint8)
    sub = rgba[y0:y1, x0:x1]
    sub[mask_s, :3] = col[mask_s, :3]
    sub[..., 3] = np.where(mask_s, 255, 0)
    full = np.zeros((h, w), bool)
    full[y0:y1, x0:x1] = mask_s
    return rgba, full, {'bbox': (x0, y0, x1, y1)}


# ------------------------------------------------------------------------------------------- sleeves
def render_tube(w, h, cam: Cam3, light: Light3, A3, B3, rA, rB, cost: dict, along_from=None, seed=0,
                ambient=0.10, gain=1.0, cuff=False, elbow_end=False, bend_dir=None, bend=0.0, shade_body=None,
                flat_end=False):
    """One sleeve segment A3 -> B3 (radii in metres) as a shaded tube.  cuff=True draws the hem and the
    shirt / knit cuff at B.  shade_body=(t_dark_at_A, t_light) blends the lamp light from A (in the shade
    of the body) to B.  Returns (rgba, mask)."""
    a2x, a2y, za = cam.proj(A3)
    b2x, b2y, zb = cam.proj(B3)
    sa, sb = cam.F / za, cam.F / zb
    ra, rb = rA * sa, rB * sb
    x0, y0, x1, y1 = _bbox([(a2x, a2y), (b2x, b2y)], max(ra, rb) + 4, w, h)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    xx += 0.5
    yy += 0.5
    hh, tt, uu = taper(xx, yy, (a2x, a2y), (b2x, b2y), ra, rb)
    if flat_end:
        vx, vy = b2x - a2x, b2y - a2y
        traw = ((xx - a2x) * vx + (yy - a2y) * vy) / (vx * vx + vy * vy + 1e-9)
        hh = np.where(traw > 1.0, 0.0, hh)
    m = hh > 0.05
    if not m.any():
        return np.zeros((h, w, 4), np.uint8), np.zeros((h, w), bool)
    if elbow_end:
        # the end cap at B is the elbow: a slightly pointed, rounder end
        de = np.sqrt((xx - b2x) ** 2 + (yy - b2y) ** 2)
        hh = np.where(de < rb * 1.06, np.maximum(hh, np.sqrt(np.clip((rb * 1.06) ** 2 - de * de, 0, None))), hh)
        m = hh > 0.05
    Lpx = math.hypot(b2x - a2x, b2y - a2y)
    Lm = float(np.linalg.norm(B3 - A3))
    P = np.zeros(hh.shape + (3,))
    for c_ in range(3):
        P[..., c_] = A3[c_] + (B3[c_] - A3[c_]) * tt
    nrm = kit.normals_from_height(hh.astype(np.float32) * 0.85)
    nw = cam.from_screen_normal(nrm.astype(np.float64))
    lam = light.lambert(P, nw, wrap=0.22)
    pool = np.clip(light.pool_at(P), 0, 1.1)
    k_l = np.ones_like(tt)
    if shade_body is not None:
        k_l = shade_body[0] + (shade_body[1] - shade_body[0]) * kit.smoothstep(0.0, 1.0, tt)
    tone = ambient + gain * 0.95 * lam * pool * k_l
    tone = tone - 0.14 * np.clip(np.abs(uu) - 0.72, 0, 1) * 3.0
    along = (1.0 - tt) * Lm if along_from is None else along_from(tt)           # metres from the wrist
    fold = np.zeros_like(tone)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28)
    if cost.get('quilt'):
        qv = np.sin(along / 0.045 * math.pi + ph)
        fold += np.where(qv > 0.86, -0.20, 0.0) + np.where((qv > 0.0) & (qv <= 0.86), 0.05 * qv, 0.0)
    else:
        f1 = np.sin(along / 0.040 + uu * 1.6 + ph)
        f2 = np.sin(along / 0.026 - uu * 2.1 + ph * 1.7)
        fold += np.where(f1 > 0.90, -0.14, 0.0) + np.where((f2 > 0.92) & (np.abs(uu) < 0.55), 0.06, 0.0)
    if bend_dir is not None and bend > 0.05:
        # creases on the inner side of the elbow bend
        bx, by = bend_dir
        dxe, dye = xx - (a2x if not elbow_end else b2x), yy - (a2y if not elbow_end else b2y)
        de = np.sqrt(dxe * dxe + dye * dye)
        inner = (dxe * bx + dye * by) / np.maximum(de, 1e-3)
        ring = np.sin(de / 2.4 + ph)
        rr_ = ra if not elbow_end else rb
        cz = m & (inner > 0.15) & (de > rr_ * 0.3) & (de < rr_ * 2.1)
        fold = np.where(cz & (ring > 0.78), fold - 0.16 * bend, fold)
        fold = np.where(cz & (ring < -0.85), fold + 0.05 * bend, fold)
    tone = tone + fold
    col = kit.tone_to_ramp(np.clip(tone, 0, 1), cost['sleeve'], x0, y0, dither=True)
    if cuff:
        cs = cost.get('cuff_style', 'shirt')
        alm = (1.0 - tt) * Lm
        if cs == 'shirt':
            cm = m & (alm < 0.011)
            ctone = ambient + 1.05 * lam * pool + 0.12
            ccol = kit.tone_to_ramp(np.clip(ctone, 0, 1), cost['cuff'], dither=False)
            col[cm] = ccol[cm]
            hem = m & (alm >= 0.011) & (alm < 0.016)
            dk = kit.tone_to_ramp(np.clip(tone - 0.22, 0, 1), cost['sleeve'], dither=False)
            col[hem] = dk[hem]
            btn = m & (alm >= 0.003) & (alm < 0.007) & (np.abs(uu + 0.55) < 0.2)
            col[btn] = np.asarray(cost['cuff'][2], np.uint8)
            bunch = m & (alm > 0.016) & (alm < 0.05) & (np.sin(alm / 0.007 + uu * 0.8 + ph) > 0.7)
            col[bunch] = dk[bunch]
        else:
            km = m & (alm < 0.018)
            ktone = ambient + 0.95 * lam * pool + 0.04 + 0.12 * (np.sin(uu * 9.0) > 0.25)
            kcol = kit.tone_to_ramp(np.clip(ktone, 0, 1), cost['cuff'], dither=False)
            col[km] = kcol[km]
            seam = m & (alm >= 0.018) & (alm < 0.023)
            dk = kit.tone_to_ramp(np.clip(tone - 0.22, 0, 1), cost['sleeve'], dither=False)
            col[seam] = dk[seam]
    edge = kit.outline_of(m)
    lpx, lpy = cam.p2(light.pos)
    pm2 = np.pad(m, 1)
    ox = pm2[1:-1, 2:].astype(np.float32) - pm2[1:-1, :-2]
    oy = pm2[2:, 1:-1].astype(np.float32) - pm2[:-2, 1:-1]
    lvx, lvy = lpx - xx, lpy - yy
    ln = np.sqrt(lvx * lvx + lvy * lvy) + 1e-6
    facing = -(ox * lvx + oy * lvy) / ln
    col[edge & (facing <= 0.2)] = np.asarray(cost['sleeve'][1], np.uint8)
    rim = edge & (facing > 0.55) & (pool > 0.18)
    rc = kit.tone_to_ramp(np.clip(tone + 0.12, 0, 1), cost['sleeve'], dither=False)
    col[rim] = rc[rim]
    rgba = np.zeros((h, w, 4), np.uint8)
    sub = rgba[y0:y1, x0:x1]
    sub[m, :3] = col[m, :3]
    sub[..., 3] = np.where(m, 255, 0)
    full = np.zeros((h, w), bool)
    full[y0:y1, x0:x1] = m
    return rgba, full


# ------------------------------------------------------------------------------------------- bodies
def _light_tone(xx, yy, hgt, light_xy, ambient, gain, lz=0.45):
    n = kit.normals_from_height(hgt)
    lx = light_xy[0] - xx
    ly = light_xy[1] - yy
    ln = np.sqrt(lx * lx + ly * ly + 1e-6)
    lx, ly = lx / ln, ly / ln
    nrm = math.sqrt(1 + lz * lz)
    d = (n[..., 0] * lx + n[..., 1] * ly) / nrm + n[..., 2] * lz / nrm
    return ambient + gain * np.clip(d, 0, 1)


def sphere(xx, yy, c, r):
    d2 = (xx - c[0]) ** 2 + (yy - c[1]) ** 2
    return np.sqrt(np.clip(r * r - d2, 0, None))


def render_body(w, h, who: str, sh_c, head_c, light_xy=(0, 0), seed=0, breathe=0.0, upper=None):
    """Back of the head + shoulders + upper arms, seen from behind and above.  sh_c = screen centre of the
    shoulder line, head_c = screen point 50 px above it at rest (moves with lean / head turn).  upper =
    {'L': (rgba, mask), 'R': ...} upper-arm sleeves drawn under the back.  Returns (rgba, mask)."""
    cost = COSTUMES[who]
    ax, ay = sh_c[0], sh_c[1] - breathe
    hx, hy = head_c[0], head_c[1] + 50.0
    sw = cost['shoulder_w']
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx += 0.5
    yy += 0.5
    rgba = np.zeros((h, w, 4), np.uint8)
    mask = np.zeros((h, w), bool)
    if upper:
        for side in ('L', 'R'):
            if upper.get(side) is not None:
                u_rgba, u_m = upper[side]
                rgba[u_m] = u_rgba[u_m]
                mask |= u_m
    # ---- the back of the coat: the trunk with rounded shoulder caps (the upper arms hang outside it)
    tw = sw + 6
    pts = [(ax - sw + 2, ay + 150), (ax - sw - 4, ay + 26), (ax - sw - 9, ay + 6), (ax - sw * 0.62, ay - 9),
           (ax - sw * 0.22, ay - 15), (ax + sw * 0.22, ay - 15), (ax + sw * 0.62, ay - 9), (ax + sw + 9, ay + 6),
           (ax + sw + 4, ay + 26), (ax + sw - 2, ay + 150)]
    curve = pg.bezier(pts[:4], n=30) + pg.bezier(pts[3:7], n=30) + pg.bezier(pts[6:], n=30)
    tm = kit.poly_mask_full(w, h, curve)
    du = (xx - ax) / (tw + 4)
    dv = (yy - (ay - 12)) / 60.0
    th = np.where(tm, 34.0 * np.sqrt(np.clip(1.0 - du * du * 0.9, 0.02, None)) * np.clip(1.15 - dv * 0.3, 0.5, 1.2), 0)
    tone = _light_tone(xx, yy, th * 0.9, light_xy, 0.09, 0.60, lz=0.30)
    tone = tone - 0.17 * np.clip((yy - ay) / 44.0, 0, 1)
    # the shoulder blades / back muscles under the cloth: two soft swells either side of the spine
    for s_ in (-1, 1):
        bl = np.exp(-(((xx - ax - s_ * sw * 0.48) / (sw * 0.36)) ** 2) - (((yy - ay - 22) / 22.0) ** 2))
        tone = tone + 0.04 * bl
    if cost.get('quilt'):
        q = np.sin((yy - ay + 4 * du * du * 10) / 7.5 * math.pi)
        tone = tone + np.where(q > 0.85, -0.16, 0.04 * np.clip(q, 0, 1))
        tone = np.where(np.abs(((xx - ax) % 22.0) - 11.0) < 0.6, tone - 0.06, tone)
    else:
        tone = np.where(np.abs(xx - ax) < 0.6, tone - 0.08, tone)
        for s_ in (-1, 1):
            sx = ax + s_ * sw * 0.80
            tone = np.where((np.abs(xx - sx - (yy - ay) * 0.25 * s_) < 0.6) & (yy > ay - 6), tone - 0.07, tone)
        f = np.sin((xx - ax) / 9.0 + (yy - ay) / 14.0 + 1.0)
        tone = np.where(f > 0.93, tone - 0.06, tone)
    col = kit.tone_to_ramp(np.clip(tone, 0, 1), cost['sleeve'], dither=True)
    rgba[tm] = col[tm]
    edge = kit.outline_of(tm)
    up = edge & (yy < ay + 12)
    rc = kit.tone_to_ramp(np.clip(tone + 0.20, 0, 1), cost['sleeve'], dither=False)
    rgba[up] = rc[up]
    # where a sleeve leaves the shoulder cap: a dark seam line on the trunk's edge (armhole)
    side_e = edge & (yy >= ay + 12) & mask
    rgba[side_e] = np.asarray(cost['sleeve'][1], np.uint8)
    mask |= tm
    if who == 'konrad':
        cm = kit.ellipse_full(w, h, (ax + hx) / 2, ay - 14, 30, 9) & (yy > ay - 20)
        ct = _light_tone(xx, yy, np.where(cm, 6.0, 0), light_xy, 0.10, 0.55)
        rgba[cm] = kit.tone_to_ramp(np.clip(ct, 0, 1), cost['sleeve'], dither=False)[cm]
        rgba[kit.outline_of(cm) & (yy > ay - 14)] = np.asarray(cost['sleeve'][1], np.uint8)
        mask |= cm
        sm = kit.ellipse_full(w, h, hx, hy - 22, 25, 9.5)
        sh_h = sphere(xx, yy * 2.2, (hx, (hy - 22) * 2.2), 21.0)
        st = _light_tone(xx, yy, np.where(sm, 8.0, 0) + sh_h * 0.2, light_xy, 0.26, 0.62)
        st = st + 0.09 * (np.sin((xx - hx) * 1.6) > 0.35) - 0.07 * (np.sin((xx - hx) * 1.6) < -0.8)
        st = st - 0.20 * np.clip((yy - (hy - 24)) / 9, 0, 1)
        rgba[sm] = kit.tone_to_ramp(np.clip(st, 0, 1), cost['scarf'], dither=False)[sm]
        rgba[kit.outline_of(sm) & (yy > hy - 22)] = np.asarray(cost['scarf'][1], np.uint8)
        mask |= sm
        nm = kit.ellipse_full(w, h, hx, hy - 31, 12, 6) & ~sm
        nt = _light_tone(xx, yy, np.where(nm, 4.0, 0), light_xy, 0.10, 0.50)
        rgba[nm] = kit.tone_to_ramp(np.clip(nt - 0.1, 0, 1), cost['skin'], dither=False)[nm]
        mask |= nm
        for s_ in (-1, 1):
            em = kit.ellipse_full(w, h, hx + s_ * 21.5, hy - 46, 3.5, 6.5)
            et = _light_tone(xx, yy, sphere(xx, yy, (hx + s_ * 21.5, hy - 46), 6.0), light_xy, 0.14, 0.6)
            rgba[em] = kit.tone_to_ramp(np.clip(et, 0, 1), cost['skin'], dither=False)[em]
            inner = kit.ellipse_full(w, h, hx + s_ * 21.0, hy - 46, 1.5, 3.5)
            rgba[inner & em] = np.asarray(cost['skin'][2], np.uint8)
            rgba[kit.outline_of(em)] = np.asarray(cost['skin'][1], np.uint8)
            mask |= em
        hm = kit.ellipse_full(w, h, hx, hy - 50, 21, 22)
        hh = sphere(xx, (yy - (hy - 50)) * 0.95 + (hy - 50), (hx, hy - 50), 22.0)
        ht = _light_tone(xx, yy, hh, light_xy, 0.04, 0.85, lz=0.35)
        wave = (xx - hx) * 1.15 + 1.6 * np.sin((yy - hy) * 0.21) + 0.012 * (xx - hx) * (yy - hy + 72)
        strand = np.sin(wave)
        ht = ht + 0.09 * (strand > 0.55) - 0.07 * (strand < -0.75)
        whorl = np.sqrt((xx - hx - 3) ** 2 + (yy - hy + 64) ** 2)
        ht = np.where(whorl < 3.5, ht - 0.06, ht)
        ht = ht - 0.18 * np.clip((yy - (hy - 44)) / 16.0, 0, 1)
        rgba[hm] = kit.tone_to_ramp(np.clip(ht, 0, 1), cost['hair'], dither=True)[hm]
        nape = hm & (yy > hy - 36)
        rgba[nape & ((xx.astype(int) % 3) == 0)] = np.asarray(cost['hair'][2], np.uint8)
        hed = kit.outline_of(hm)
        rgba[hed & (yy > hy - 50)] = np.asarray(cost['hair'][0], np.uint8)
        rgba[hed & (yy <= hy - 58)] = kit.tone_to_ramp(np.clip(ht + 0.12, 0, 1), cost['hair'], dither=False)[hed & (yy <= hy - 58)]
        mask |= hm
    else:
        km = kit.ellipse_full(w, h, hx, hy - 20, 26, 9)
        kt = _light_tone(xx, yy, np.where(km, 8.0, 0), light_xy, 0.08, 0.5) + 0.10 * (np.sin((xx - hx) * 1.6) > 0.3)
        kt = kt - 0.12 * np.clip((yy - (hy - 20)) / 9, 0, 1)
        rgba[km] = kit.tone_to_ramp(np.clip(kt, 0, 1), cost['cuff'], dither=False)[km]
        rgba[kit.outline_of(km) & (yy > hy - 20)] = np.asarray(cost['cuff'][0], np.uint8)
        mask |= km
        cx_, cy_ = hx, hy - 47
        nz = pg.value_noise(w, h, 3, kit.seed_of('ushanka_fur'), octaves=2)
        crown = kit.ellipse_full(w, h, cx_, cy_ - 5, 22, 19)
        roll = kit.ellipse_full(w, h, cx_, cy_ + 8, 28, 15) & (yy > cy_ - 6)
        fm = crown | roll
        ch = sphere(xx, yy, (cx_, cy_ - 5), 22.0)
        ct = _light_tone(xx, yy, ch, light_xy, 0.05, 0.85, lz=0.35)
        tuft = np.sin((xx - cx_) * 0.9 + nz * 9.0) * np.cos((yy - cy_) * 0.8 + nz * 7.0)
        ct = ct + 0.10 * (tuft > 0.5) - 0.08 * (tuft < -0.55) + (nz - 0.5) * 0.10
        rgba[crown] = kit.tone_to_ramp(np.clip(ct, 0, 1), cost['fur'], dither=True)[crown]
        seam = crown & (np.abs(xx - cx_) < 0.6) & (yy < cy_ - 8) & (nz > 0.35)
        rgba[seam] = kit.tone_to_ramp(np.clip(ct - 0.08, 0, 1), cost['fur'], dither=False)[seam]
        rh = sphere(xx, (yy - (cy_ + 8)) * 1.8 + (cy_ + 8), (cx_, cy_ + 8), 28.0)
        rt = _light_tone(xx, yy, rh, light_xy, 0.06, 0.70, lz=0.30)
        rt = rt + 0.13 * (tuft > 0.35) - 0.10 * (tuft < -0.45) + (nz - 0.5) * 0.14
        rt = rt - 0.18 * np.clip((yy - (cy_ + 8)) / 14.0, 0, 1)
        rgba[roll] = kit.tone_to_ramp(np.clip(rt, 0, 1), cost['fur'], dither=True)[roll]
        rim_r = roll & ~kit.erode(roll, 1) & (yy < cy_ + 6) & crown
        brk = (np.sin(xx * 1.7 + nz * 6.0) > -0.2)
        rgba[rim_r & brk] = kit.tone_to_ramp(np.clip(rt - 0.10, 0, 1), cost['fur'], dither=False)[rim_r & brk]
        for (tx, ty, c_) in ((cx_ - 3, cy_ - 22, 2), (cx_ - 2, cy_ - 22, 3), (cx_ - 1, cy_ - 21, 3),
                             (cx_, cy_ - 21, 4), (cx_ + 1, cy_ - 21, 3), (cx_ + 2, cy_ - 22, 3),
                             (cx_ + 3, cy_ - 23, 2), (cx_ - 1, cy_ - 20, 2), (cx_ + 1, cy_ - 19, 2)):
            if 0 <= int(ty) < h and 0 <= int(tx) < w:
                rgba[int(ty), int(tx), :3] = np.asarray(cost['cuff'][c_], np.uint8)[:3]
        fed = kit.outline_of(fm)
        rgba[fed & (yy > cy_ + 4)] = np.asarray(cost['fur'][0], np.uint8)
        top_rim = fed & (yy <= cy_ - 12)
        rgba[top_rim] = kit.tone_to_ramp(np.clip(ct + 0.14, 0, 1), cost['fur'], dither=False)[top_rim]
        mask |= fm
    rgba[..., 3] = np.where(mask, 255, 0)
    rgba[~mask] = 0
    return rgba, mask


# ------------------------------------------------------------------------------------------- the rig
def screen_yaw(cam: Cam3, W, ang):
    """Desk-plane yaw of a hand at world point W whose axis should point along screen angle `ang`."""
    x, y = cam.p2(W)
    q = cam.on_plane_y(x + math.cos(ang) * 12.0, y + math.sin(ang) * 12.0, float(W[1]))
    d = q - W
    return math.atan2(float(d[0]), float(d[2]))


class FigureRig:
    """Body + two arms of one seated person, keyed on kit.Track objects.

    body track:  lean (side, forward) radians about the hips, head (dx, dy) px (turn / nod), breathe (px)
    arm track:   at (x, y) screen target of the hand's `anchor` (palm | tips | pinch | grip | knuckles) at
                 height h (m above the desk); ang (screen direction of the fingers); curl / curls / thumb /
                 spread / pitch / roll; typing (0/1); hidden; follow (max wrist deviation, rad);
                 pole ('out' | 'front' | (x, y, z) offset from the shoulder) optional
    Out-of-reach targets make the body lean in automatically (up to max_lean rad)."""

    def __init__(self, who, body: kit.Track, arm_l: kit.Track, arm_r: kit.Track, lamp, light_xy, anchor,
                 shadow=None, max_lean=0.45, w=680, h=380):
        self.who = who
        self.cost = COSTUMES[who]
        self.body = body
        self.arms = {'L': arm_l, 'R': arm_r}
        self.cam = Cam3(anchor, self.cost['shoulder_w'], self.cost['half_w_m'])
        self.light = Light3(lamp, self.cam)
        self.lamp = lamp
        self.light_xy = light_xy
        self.anchor = anchor
        self.shadow = shadow
        self.max_lean = max_lean
        self.W, self.H = w, h
        self.hip = _v(0.0, self.cam.HS - HIP_R, -0.04)

    # --- body pose
    def _lean_pts(self, side_a, fwd_a):
        """World shoulder joints, mid-shoulder and head centre after leaning (side, forward) about the hips."""
        hw = self.cost['half_w_m']
        base = {'L': _v(-hw, self.cam.HS - 0.015, 0.0), 'R': _v(hw, self.cam.HS - 0.015, 0.0),
                'M': _v(0.0, self.cam.HS, 0.0), 'H': _v(0.0, self.cam.HS + 0.20, 0.03)}
        cf, sf = math.cos(fwd_a), math.sin(fwd_a)
        cs, ss = math.cos(side_a), math.sin(side_a)
        out = {}
        for k_, p in base.items():
            q = p - self.hip
            # forward: rotate about x (y -> z); side: rotate about z (y -> x)
            y1 = q[1] * cf - q[2] * sf
            z1 = q[1] * sf + q[2] * cf
            x2 = q[0] * cs + y1 * ss
            y2 = -q[0] * ss + y1 * cs
            out[k_] = self.hip + _v(x2, y2, z1)
        return out

    def arm_target(self, s, side, W_prev=None):
        """World grip target of an arm state."""
        x, y = s['at']
        return self.cam.on_plane_y(x, y, float(s.get('h', 0.0)))

    def pose_of(self, s, curls=None):
        return HandPose(curl=s.get('curl', 0.25), curls=curls if curls is not None else s.get('curls'),
                        thumb=s.get('thumb', 'side'), spread=s.get('spread', 0.0), pitch=s.get('pitch', 0.0),
                        roll=s.get('roll', 0.0), lifted=s.get('lifted'))

    def solve_arm(self, s, side, S, pose, mid_x=0.0):
        """Wrist / elbow for an arm state with the shoulder at S.  Returns dict."""
        tgt = self.arm_target(s, side)
        anchor = s.get('anchor', 'palm')
        k = self.cost['hand']
        yaw = screen_yaw(self.cam, tgt, s.get('ang', -math.pi / 2))
        W = tgt.copy()
        el = None
        over = 0.0
        follow = s.get('follow', 0.55)
        for _ in range(3):
            parts = hand_parts(W, yaw, pose, side, k)
            off = anchor_offset(parts, anchor, W)
            Wt = tgt - off
            pole = self._pole(s, side, S, Wt, mid_x)
            el, W, over = ik3(S, Wt, pole)
            # keep the hand continuing the forearm (wrist deviation limited)
            fdir = W - el
            fyaw = math.atan2(float(fdir[0]), float(fdir[2]))
            want = screen_yaw(self.cam, tgt, s.get('ang', -math.pi / 2))
            dv = (want - fyaw + math.pi) % (2 * math.pi) - math.pi
            dv = max(-follow, min(follow, dv))
            yaw = fyaw + dv
        parts = hand_parts(W, yaw, pose, side, k)
        return {'S': S, 'E': el, 'W': W, 'yaw': yaw, 'over': over, 'parts': parts, 'tgt': tgt}

    def _pole(self, s, side, S, W, mid_x):
        p = s.get('pole')
        if isinstance(p, (tuple, list)):
            return S + _v(*p)
        if p == 'front':
            return default_pole(S, W, side, mid_x, crossing=1.0)
        if p == 'out':
            return default_pole(S, W, side, mid_x, crossing=-1.0)
        if p == 'wide':                                  # elbow flared out (reaching sideways, pushing)
            sgn = -1.0 if side == 'L' else 1.0
            return S + _v(sgn * 0.45, -0.25, -0.05)
        return default_pole(S, W, side, mid_x)

    def solve(self, t, curls_override=None):
        """Full pose at time t: lean (auto-extended for reach), shoulders, both arms."""
        bs = self.body.at(t)
        side_a, fwd_a = bs.get('lean', (0.0, 0.0))
        arms = {sd: self.arms[sd].at(t) for sd in ('L', 'R')}
        poses = {}
        for sd in ('L', 'R'):
            s = arms[sd]
            if not s.get('hidden'):
                cu = curls_override.get(sd) if curls_override else None
                poses[sd] = self.pose_of(s, cu)
        add_f, add_s = 0.0, 0.0
        res = {}
        for it in range(6):
            pts = self._lean_pts(side_a + add_s, fwd_a + add_f)
            res = {}
            worst = (0.0, None)
            for sd in ('L', 'R'):
                s = arms[sd]
                if s.get('hidden'):
                    continue
                r = self.solve_arm(s, sd, pts[sd], poses[sd], mid_x=float(pts['M'][0]))
                res[sd] = r
                if r['over'] > worst[0]:
                    worst = (r['over'], sd)
            if worst[0] < 0.004 or it == 5:
                break
            r = res[worst[1]]
            d = r['tgt'] - pts[worst[1]]
            # lean towards the target: forward share by z, sideways by x (both small-angle on HIP_R)
            dn = d / max(float(np.linalg.norm(d)), 1e-6)
            add_f += max(0.0, float(dn[2])) * (worst[0] + 0.01) / HIP_R
            add_s += float(dn[0]) * (worst[0] + 0.01) / HIP_R * 0.6
            add_f = min(add_f, self.max_lean)
            add_s = max(-0.3, min(0.3, add_s))
        pts = self._lean_pts(side_a + add_s, fwd_a + add_f)
        return bs, pts, res, arms

    # --- drawing
    def body_screen(self, bs, pts):
        hdx, hdy = bs.get('head', (0.0, 0.0))
        m = self.cam.p2(pts['M'])
        hd = self.cam.p2(pts['H'])
        rest_h = self.cam.p2(_v(0.0, self.cam.HS + 0.20, 0.03))
        # the art puts the head 50 px above the shoulder line; leaning moves the head a little further than
        # the shoulders (it is further from the hips), kept within the collar
        rx = (hd[0] - rest_h[0]) - (m[0] - self.anchor[0])
        ry = (hd[1] - rest_h[1]) - (m[1] - self.anchor[1])
        rx = max(-10.0, min(10.0, rx * 0.6))
        ry = max(-10.0, min(10.0, ry * 0.6))
        return m, (m[0] + rx + hdx, m[1] - 50.0 + ry + hdy)

    def render_upper(self, r, side, seed):
        """Upper-arm sleeve shoulder -> elbow (body layer)."""
        rs, re_, rw = self.cost['r_m']
        S, E, W = r['S'], r['E'], r['W']
        u = _norm(S - E)
        f = _norm(W - E)
        bend = float(np.clip((1.0 + float(u @ f)) * 0.5 + 0.35, 0, 1))
        e2, w2 = self.cam.p2(E), self.cam.p2(W)
        s2 = self.cam.p2(S)
        bx = (s2[0] - e2[0]) / max(1e-3, math.dist(s2, e2)) + (w2[0] - e2[0]) / max(1e-3, math.dist(w2, e2))
        by = (s2[1] - e2[1]) / max(1e-3, math.dist(s2, e2)) + (w2[1] - e2[1]) / max(1e-3, math.dist(w2, e2))
        bl = math.hypot(bx, by) or 1.0
        return render_tube(self.W, self.H, self.cam, self.light, S, E, rs, re_ * 1.04, self.cost, seed=seed,
                           ambient=0.10, gain=0.85, elbow_end=True, bend_dir=(bx / bl, by / bl), bend=bend,
                           along_from=lambda tt: LF + (1.0 - tt) * LU, shade_body=(0.45, 0.75))

    def render_fore(self, r, side, seed, extra=None, ex_state=None):
        """Forearm + hand (+ held prop) of one arm (arm layer)."""
        rs, re_, rw = self.cost['r_m']
        E, W = r['E'], r['W']
        rgba = np.zeros((self.H, self.W, 4), np.uint8)
        sl, sm = render_tube(self.W, self.H, self.cam, self.light, E, W + _norm(W - E) * 0.012, re_, rw, self.cost,
                             seed=seed + 7, ambient=0.10, gain=0.95, cuff=True, shade_body=(0.55, 1.0),
                             flat_end=True)
        hand, hm, _ = render_hand(self.W, self.H, self.cam, self.light, r['parts'], self.cost)
        if self.shadow is not None and float(W[1]) < 0.10:
            _cast_shadow(rgba, hm, sm, self.cam.p2(W), self.cam.p2(E), self.shadow,
                         1.0 + max(0.0, float(W[1])) * 14.0, self.W, self.H)
        if extra is not None:
            extra(rgba, self.hand_info(r))
        kit.over(rgba, hand)
        kit.over(rgba, sl)
        return rgba

    def hand_info(self, r):
        p = r['parts']
        an = {k_: self.cam.p2(v) for k_, v in p['anchors'].items()}
        w2 = self.cam.p2(r['W'])
        tip = an['tips']
        return {'anchors': an, 'wrist': w2, 'ang': math.atan2(tip[1] - w2[1], tip[0] - w2[0]),
                'scale': self.cam.scale(r['W']), 'W3': r['W'], 'parts': p}

    def render_body(self, t, bs, pts, res, seed):
        upper = {}
        for sd in ('L', 'R'):
            if sd in res:
                upper[sd] = self.render_upper(res[sd], sd, seed + (1 if sd == 'L' else 2))
        m, hc = self.body_screen(bs, pts)
        rgba, msk = render_body(self.W, self.H, self.who, m, hc, light_xy=self.light_xy, seed=seed,
                                breathe=bs.get('breathe', 0.0), upper=upper)
        return rgba


def hash_seed(name):
    return kit.seed_of('fig_' + name)


def _cast_shadow(rgba, hand_m, sleeve_m, w2, e2, shadow, k, W, H):
    """Contact shadow of the hand (and the wrist end of the sleeve) on the desk: solid core, one dithered
    pixel of penumbra, offset away from the lamp (longer when the hand is lifted)."""
    sdx, sdy, scol = shadow
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    near = (xx - w2[0]) ** 2 + (yy - w2[1]) ** 2 < (0.30 * max(8.0, math.dist(w2, e2))) ** 2
    caster = hand_m | (sleeve_m & near)
    dx, dy = int(round(sdx * k * 0.7)), int(round(sdy * k * 0.7))
    sh_m = (kit.shift(caster, dx, dy) | kit.shift(caster, int(round(sdx * k * 0.35)), int(round(sdy * k * 0.35))))
    sh_m &= ~(hand_m | sleeve_m)
    core = kit.erode(sh_m, 1)
    bay = kit.bayer_full(W, H)
    sel = core | (sh_m & (bay < 0.5))
    rgba[sel, :3] = np.asarray(scol, np.uint8)[:3]
    rgba[sel, 3] = 255


# ------------------------------------------------------------------------------------------- per-frame tracks
def _typing_curls(s, side, i, phase=0):
    if s.get('typing', 0) <= 0.5:
        return None
    pat = kit.TYPE_PATTERNS[(i * 5 + (3 if side == 'L' else 0) + phase) % len(kit.TYPE_PATTERNS)]
    base = s.get('curl', 0.7)
    return [float(np.clip(base - 0.16 + 0.32 * (p - 0.5) * 2.0, 0, 1)) for p in pat]


def _sig_r(r, s, curls, extra_sig):
    def q3(v):
        return tuple(int(round(float(c) * 400)) for c in v)
    return (q3(r['S']), q3(r['E']), q3(r['W']), round(r['yaw'], 2), round(s.get('curl', 0.25), 2),
            tuple(round(c, 2) for c in curls) if curls else (tuple(s.get('curls')) if s.get('curls') else None),
            s.get('thumb', 'side'), round(s.get('spread', 0.0), 2), round(s.get('pitch', 0.0), 2),
            round(s.get('roll', 0.0), 2), tuple(s.get('lifted') or (0, 0, 0, 0)), extra_sig)


def render_tracks(rig: FigureRig, atlases: dict, t0: float, t1: float, fps: float = 12.0, extras=None):
    """Render the figure frame by frame into atlases {'L', 'R', 'B'}.  extras = {'L': fn, 'R': fn}:
    fn(t, state, rgba, info) draws a held prop under the hand (rgba None -> return a hashable signature).
    Returns {'L': keys, 'R': keys, 'B': keys} with times local to t0."""
    extras = extras or {}
    keys = {'L': [], 'R': [], 'B': []}
    last = {'L': None, 'R': None, 'B': None}
    cache = {'L': {}, 'R': {}, 'B': {}}
    n = int(math.ceil((t1 - t0) * fps)) + 1
    seed = hash_seed(rig.who)
    for i in range(n):
        t = t0 + i / fps
        arms_now = {sd: rig.arms[sd].at(t) for sd in ('L', 'R')}
        co = {sd: _typing_curls(arms_now[sd], sd, i) for sd in ('L', 'R')}
        bs, pts, res, arms = rig.solve(t, curls_override=co)
        for sd in ('L', 'R'):
            s = arms[sd]
            if sd not in res:
                fr = -1
            else:
                r = res[sd]
                ex = extras.get(sd)
                info = rig.hand_info(r)
                sig = (sd,) + _sig_r(r, s, co[sd], ex(t, s, None, info) if ex else None)
                if sig in cache[sd]:
                    fr = cache[sd][sig]
                else:
                    draw = (lambda rgba, inf, _ex=ex, _t=t, _s=s: _ex(_t, _s, rgba, inf)) if ex else None
                    rgba = rig.render_fore(r, sd, seed + (11 if sd == 'L' else 23), extra=draw)
                    fr = atlases[sd].add(rgba)
                    cache[sd][sig] = fr
            if fr != last[sd]:
                keys[sd].append([round(t - t0, 3), fr])
                last[sd] = fr
        m, hc = rig.body_screen(bs, pts)
        bsig = (round(m[0]), round(m[1]), round(hc[0]), round(hc[1]), round(bs.get('breathe', 0.0)),
                tuple((sd, tuple(int(round(float(c) * 300)) for c in res[sd]['E']),
                       tuple(int(round(float(c) * 300)) for c in res[sd]['S'])) for sd in ('L', 'R') if sd in res))
        if bsig in cache['B']:
            fr = cache['B'][bsig]
        else:
            fr = atlases['B'].add(rig.render_body(t, bs, pts, res, seed))
            cache['B'][bsig] = fr
        if fr != last['B']:
            keys['B'].append([round(t - t0, 3), fr])
            last['B'] = fr
    rig._t_end = t1
    return keys


def render_tap(rig: FigureRig, side: str, atlas, t: float = None, extra=None) -> int:
    """Rhyme beat: the arm's final pose with the index finger lifted off the desk.  Returns the new frame
    index in `atlas`, or -1 when the arm is hidden at that time."""
    t = rig._t_end if t is None else t
    s = rig.arms[side].at(t)
    if s.get('hidden'):
        return -1
    c = s.get('curl', 0.25)
    cu = s.get('curls') or [None] * 4
    curls = [min(1.0, (cu[0] if cu[0] is not None else c) * 0.4), cu[1], cu[2], cu[3]]
    bs, pts, res, arms = rig.solve(t, curls_override={side: curls})
    if side not in res:
        return -1
    r = res[side]
    pose = rig.pose_of(s, curls)
    pose.lifted = [0.55, 0.0, 0.0, 0.0]
    r = dict(r)
    r['parts'] = hand_parts(r['W'], r['yaw'], pose, side, rig.cost['hand'])
    draw = (lambda rgba, inf: extra(t, s, rgba, inf)) if extra else None
    rgba = rig.render_fore(r, side, hash_seed(rig.who) + (11 if side == 'L' else 23), extra=draw)
    return atlas.add(rgba)


def rig_nodes(nodes: list, rig: FigureRig, out_dir: str, set_dir: str, prefix: str, tag: str, dur: float, fps: float,
              extras=None, z=(20, 21, 23)):
    """Render a FigureRig over [0, dur] and append its three anim nodes (<prefix>_arm_l, _arm_r, _body)."""
    names = {'L': 'arm_l', 'R': 'arm_r', 'B': 'body'}
    ats = {k_: kit.Atlas('%s_%s_%s' % (prefix, v_, tag)) for k_, v_ in names.items()}
    keys = render_tracks(rig, ats, 0.0, dur, fps, extras=extras)
    for side, zz in (('L', z[0]), ('R', z[1]), ('B', z[2])):
        rel = '%s/%s_%s.png' % (set_dir, names[side], tag)
        path = '%s/%s' % (out_dir, rel)
        nodes.append({'id': '%s_%s' % (prefix, names[side]), 'type': 'anim', 'atlas': rel,
                      'frames': ats[side].save(path), 'keys': keys[side], 'z': zz,
                      '_atlas': ats[side], '_path': path, '_rig': rig, '_side': side,
                      '_extra': (extras or {}).get(side)})
    return nodes


class StandingArm:
    """An arm whose body stands off to the side (Irina at the door): shoulder keyed in the sitter's world
    frame (track field 'sh' = (x, y, z) m), hand target like FigureRig ('at', 'h', 'anchor', 'ang', pose).
    The shoulder cap and the top of the upper arm are drawn as part of the sleeve."""

    def __init__(self, who, track: kit.Track, cam: Cam3, light: Light3, shadow=None, w=680, h=380, side='R'):
        self.who = who
        self.cost = COSTUMES[who]
        self.track = track
        self.cam = cam
        self.light = light
        self.shadow = shadow
        self.W, self.H = w, h
        self.side = side

    def solve(self, s):
        S = _v(*s['sh'])
        tgt = self.cam.on_plane_y(s['at'][0], s['at'][1], float(s.get('h', 0.0)))
        pose = HandPose(curl=s.get('curl', 0.2), curls=s.get('curls'), thumb=s.get('thumb', 'side'),
                        spread=s.get('spread', 0.0), pitch=s.get('pitch', 0.0), roll=s.get('roll', 0.0))
        k = self.cost['hand']
        yaw = screen_yaw(self.cam, tgt, s.get('ang', math.pi))
        W = tgt.copy()
        for _ in range(3):
            parts = hand_parts(W, yaw, pose, self.side, k)
            Wt = tgt - anchor_offset(parts, s.get('anchor', 'pinch'), W)
            pole = S + _v(*s.get('pole', (0.25, -0.40, -0.30)))
            el, W, over = ik3(S, Wt, pole, self.cost.get('lu', LU), self.cost.get('lf', LF))
            fdir = W - el
            fyaw = math.atan2(float(fdir[0]), float(fdir[2]))
            want = screen_yaw(self.cam, tgt, s.get('ang', math.pi))
            dv = (want - fyaw + math.pi) % (2 * math.pi) - math.pi
            yaw = fyaw + max(-0.6, min(0.6, dv))
        parts = hand_parts(W, yaw, pose, self.side, k)
        return {'S': S, 'E': el, 'W': W, 'yaw': yaw, 'parts': parts, 'tgt': tgt}

    def render(self, s, extra=None, seed=0):
        r = self.solve(s)
        rs, re_, rw = self.cost['r_m']
        rgba = np.zeros((self.H, self.W, 4), np.uint8)
        body = None
        if s.get('body', 0) > 0.5:
            # her shoulder and the top of her back, leaning in at the frame edge (the coat, rim-lit by the
            # cold light of the open door behind her)
            sc = self.cam.scale(r['S'])
            c2 = self.cam.p2(r['S'] + _v(0.10, 0.03, 0.02))
            rx, ry = 0.15 * sc, 0.085 * sc
            yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32) + 0.5
            m = ((xx - c2[0]) / rx) ** 2 + ((yy - c2[1]) / ry) ** 2 <= 1.0
            if m.any():
                hgt = np.sqrt(np.clip(1.0 - ((xx - c2[0]) / rx) ** 2 - ((yy - c2[1]) / ry) ** 2, 0, 1)) * 8.0
                n = kit.normals_from_height(hgt.astype(np.float32))
                tone = 0.10 + 0.30 * np.clip(n[..., 0] * 0.7 - n[..., 1] * 0.5, 0, 1)
                ramp = self.cost.get('coat', self.cost['sleeve'])
                body = np.zeros((self.H, self.W, 4), np.uint8)
                col = kit.tone_to_ramp(np.clip(tone, 0, 1), ramp, dither=True)
                body[m, :3] = col[m, :3]
                body[m, 3] = 255
                e = kit.outline_of(m)
                body[e & (xx > c2[0])] = np.asarray(list(ramp[-1][:3]) + [255], np.uint8)
                body[e & (xx <= c2[0])] = np.asarray(list(ramp[0][:3]) + [255], np.uint8)
        up, um = render_tube(self.W, self.H, self.cam, self.light, r['S'], r['E'], rs, re_ * 1.04, self.cost,
                             seed=seed, ambient=0.10, gain=0.9, elbow_end=True, shade_body=(0.5, 0.8))
        fo, fm = render_tube(self.W, self.H, self.cam, self.light, r['E'], r['W'] + _norm(r['W'] - r['E']) * 0.012,
                             re_, rw, self.cost, seed=seed + 3, ambient=0.10, gain=0.95, cuff=True,
                             shade_body=(0.8, 1.0), flat_end=True)
        hand, hm, _ = render_hand(self.W, self.H, self.cam, self.light, r['parts'], self.cost)
        if self.shadow is not None and float(r['W'][1]) < 0.12:
            _cast_shadow(rgba, hm, fm, self.cam.p2(r['W']), self.cam.p2(r['E']), self.shadow,
                         1.0 + max(0.0, float(r['W'][1])) * 14.0, self.W, self.H)
        info = {'anchors': {k_: self.cam.p2(v) for k_, v in r['parts']['anchors'].items()}, 'wrist': self.cam.p2(r['W'])}
        if extra is not None:
            extra(rgba, info)
        kit.over(rgba, hand)
        kit.over(rgba, fo)
        kit.over(rgba, up)
        if body is not None:
            kit.over(rgba, body)
        return rgba, info


def standing_arm_track(arm: StandingArm, atlas, t0, t1, fps, extra=None) -> list:
    """Keys of a StandingArm over [t0, t1] (hidden states -> -1).  extra(t, s, rgba, info)."""
    keys, last, cache = [], None, {}
    n = int(math.ceil((t1 - t0) * fps)) + 1
    for i in range(n):
        t = t0 + i / fps
        s = arm.track.at(t)
        if s.get('hidden'):
            fr = -1
        else:
            r = arm.solve(s)
            info = {'anchors': {k_: arm.cam.p2(v) for k_, v in r['parts']['anchors'].items()}}
            sig = (tuple(int(round(float(c) * 400)) for c in r['S']), tuple(int(round(float(c) * 400)) for c in r['W']),
                   round(r['yaw'], 2), round(s.get('curl', 0.2), 2), s.get('thumb', 'side'), s.get('body', 0) > 0.5,
                   extra(t, s, None, info) if extra else None)
            if sig in cache:
                fr = cache[sig]
            else:
                draw = (lambda rgba, inf, _t=t, _s=s: extra(_t, _s, rgba, inf)) if extra else None
                rgba, _ = arm.render(s, extra=draw, seed=hash_seed(arm.who))
                fr = atlas.add(rgba)
                cache[sig] = fr
        if fr != last:
            keys.append([round(t - t0, 3), fr])
            last = fr
    return keys
