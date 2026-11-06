"""chargen_portrait2_paint -- turns the traced G-buffer into pixel art.

Light model (art-directed, not physical): one warm key light with soft-edged cast shadows, a low navy
ambient with occlusion, and a cool rim from behind.  The light value is posterised onto short hand-picked
hue-shifted ramps (navy shadow -> warm key) with optional ordered dithering per material, then cleaned up
pixel-art style (orphans, one-pixel peninsulas), outlined selectively (dark only on the shadow side and at
depth breaks; the lit side keeps colour edges) and composited over a painted background.
"""
from __future__ import annotations

import numpy as np

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 + 1 / 32


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


def ramp(*hs):
    return np.stack([hexc(h) for h in hs])


def bayer(h, w, x0=0, y0=0):
    ys = (np.arange(h) + y0) % 4
    xs = (np.arange(w) + x0) % 4
    return BAYER4[ys[:, None], xs[None, :]]


class Look:
    def __init__(self, key=(0.62, -0.52, 0.58), rim=(-0.85, -0.25, -0.45), ambient=0.07, wrap=0.12,
                 bg='karsk', glow=(0.70, 0.22), fill=0.10, fill_dir=(0.15, 0.25, 1.0), ao=0.45):
        k = np.asarray(key, float)
        self.key = k / np.linalg.norm(k)
        r = np.asarray(rim, float)
        self.rim = r / np.linalg.norm(r)
        self.ambient = ambient
        self.wrap = wrap
        self.bg = bg
        self.glow = glow
        self.fill = fill
        f = np.asarray(fill_dir, float)
        self.fill_dir = f / np.linalg.norm(f)
        self.ao = ao


class MatStyle:
    """How one material is painted: ramp (dark -> light), thresholds (len(ramp) - 1 increasing light
    values), dither amplitude, rim colour, outline colour, specular boost."""

    def __init__(self, ramp_, th, dither=0.0, rim=None, outline=None, spec=0.0, spec_pow=12.0, wrap=None,
                 rim_th=0.55, flat=0.0, lift=0.0, ao=None):
        self.ramp = ramp_
        self.th = np.asarray(th, np.float32)
        self.dither = dither
        self.rim = hexc(rim) if isinstance(rim, str) else rim
        self.outline = hexc(outline) if isinstance(outline, str) else (outline if outline is not None else ramp_[0])
        self.spec = spec
        self.spec_pow = spec_pow
        self.wrap = wrap
        self.rim_th = rim_th
        self.flat = flat
        self.lift = lift          # cast shadows keep this fraction of the key (skin: soft, warm shadows)
        self.ao = ao              # per-material occlusion weight (None = look default)


def light_value(d, look: Look, styles: dict, names: list):
    """Scalar light per pixel plus helper channels."""
    n = d.n
    L = look.key
    ndl = (n * L).sum(2)
    wrap = np.full(ndl.shape, look.wrap, np.float32)
    flat = np.zeros(ndl.shape, np.float32)
    spec = np.zeros(ndl.shape, np.float32)
    spow = np.full(ndl.shape, 12.0, np.float32)
    lift = np.zeros(ndl.shape, np.float32)
    aow = np.full(ndl.shape, look.ao, np.float32)
    for i, nm in enumerate(names):
        st = styles.get(nm)
        if st is None:
            continue
        m = d.mat == i
        if st.wrap is not None:
            wrap[m] = st.wrap
        flat[m] = st.flat
        spec[m] = st.spec
        spow[m] = st.spec_pow
        lift[m] = st.lift
        if st.ao is not None:
            aow[m] = st.ao
    diff = np.clip((ndl + wrap) / (1 + wrap), 0, 1)
    vis = np.clip((d.shadow - 0.25) / 0.5, 0, 1)
    vis = vis * vis * (3 - 2 * vis)
    ao = np.clip(d.ao, 0, 1)
    key = diff * (vis + (1 - vis) * lift)
    # half vector spec (view = +z)
    Hv = L + np.array([0, 0, 1.0])
    Hv /= np.linalg.norm(Hv)
    nh = np.clip((n * Hv).sum(2), 0, 1)
    sp = spec * nh ** spow * vis
    amb = look.ambient * (0.55 + 0.45 * ao) * (1.0 + 0.35 * np.clip(-n[..., 1], 0, 1))
    fill = look.fill * np.clip((n * look.fill_dir).sum(2), 0, 1) * ao
    aok = (1.0 - aow) + aow * ao
    v = amb + fill + key * aok + sp
    v = v * (1 - flat) + flat * 0.5
    rim = np.clip((n * look.rim).sum(2), 0, 1) * np.clip(1.0 - n[..., 2] * 0.6, 0, 1)
    return v.astype(np.float32), rim.astype(np.float32), key.astype(np.float32)


def smooth_by_material(v, mat, passes=1, w_center=4.0):
    """Material-aware 3x3 smoothing of the light field: band edges become clean iso-curves instead of
    jagged stair noise.  Pixels only average with neighbours of the same material."""
    h, w = v.shape
    for _ in range(passes):
        vp = np.pad(v, 1, mode='edge')
        mp = np.pad(mat, 1, mode='constant', constant_values=-9)
        acc = v * w_center
        wsum = np.full(v.shape, w_center, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                wt = 1.0 if dx == 0 or dy == 0 else 0.6
                same = mp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] == mat
                acc = acc + np.where(same, vp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] * wt, 0)
                wsum = wsum + np.where(same, wt, 0)
        v = (acc / wsum).astype(np.float32)
    return v


def quantise(d, v, styles: dict, names: list):
    """Tone index per pixel (-1 = background)."""
    h, w = v.shape
    tone = np.full((h, w), -1, np.int16)
    bay = bayer(h, w) - 0.5
    for i, nm in enumerate(names):
        st = styles.get(nm)
        m = d.mat == i
        if st is None or not m.any():
            continue
        vv = v[m] + bay[m] * st.dither
        tone[m] = np.searchsorted(st.th, vv).astype(np.int16)
    return tone


def clean(tone, mat, passes=2, protect=None):
    """Pixel-art cleanup inside each material: isolated pixels and 1-px spurs take the neighbours' tone."""
    h, w = tone.shape
    for _ in range(passes):
        tp = np.pad(tone, 1, mode='edge')
        mp = np.pad(mat, 1, mode='edge')
        nb_t = [tp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        nb_m = [mp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        same_mat = [nm == mat for nm in nb_m]
        n_same = sum(((nt == tone) & sm).astype(int) for nt, sm in zip(nb_t, same_mat))
        n_mat = sum(sm.astype(int) for sm in same_mat)
        cand = (n_same == 0) & (n_mat >= 3) | (n_same == 1) & (n_mat == 4) & (
            ((nb_t[0] == nb_t[1]) & (nb_t[0] != tone)) | ((nb_t[2] == nb_t[3]) & (nb_t[2] != tone)))
        if protect is not None:
            cand &= ~protect
        cand &= tone >= 0
        if not cand.any():
            break
        st = np.stack([np.where(sm, nt, -999) for nt, sm in zip(nb_t, same_mat)])
        # most common neighbour tone (ties -> the darker one, which keeps shadow shapes intact)
        best = np.full((h, w), -1, np.int16)
        bestc = np.zeros((h, w), np.int16)
        for k in range(4):
            c = (st == st[k]).sum(0).astype(np.int16)
            better = (c > bestc) | ((c == bestc) & (st[k] < best))
            better &= st[k] != -999
            best = np.where(better, st[k], best)
            bestc = np.where(better, c, bestc)
        tone = np.where(cand & (best >= 0), best, tone)
    return tone


def colorize(d, tone, styles, names):
    h, w = tone.shape
    rgb = np.zeros((h, w, 3), np.uint8)
    for i, nm in enumerate(names):
        st = styles.get(nm)
        m = (d.mat == i) & (tone >= 0)
        if st is None or not m.any():
            continue
        t = np.clip(tone[m], 0, len(st.ramp) - 1)
        rgb[m] = st.ramp[t]
    return rgb


def neighbours(a, fill):
    h, w = a.shape[:2]
    p = np.pad(a, ((1, 1), (1, 1)) + ((0, 0),) * (a.ndim - 2), constant_values=fill)
    return {(dx, dy): p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in
            ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))}


def apply_rim(rgb, d, rim, key, styles, names, tone, width=1):
    """Cool rim on the silhouette pixels that face the rim light (only where the key does not reach)."""
    hit = d.hit
    nb = neighbours(hit, False)
    edge = hit & ~(nb[(1, 0)] & nb[(-1, 0)] & nb[(0, 1)] & nb[(0, -1)])
    if width > 1:
        nb2 = neighbours(edge, False)
        edge2 = hit & (nb2[(1, 0)] | nb2[(-1, 0)] | nb2[(0, 1)] | nb2[(0, -1)])
    else:
        edge2 = edge
    for i, nm in enumerate(names):
        st = styles.get(nm)
        if st is None or st.rim is None:
            continue
        m = (d.mat == i) & edge2 & (rim > st.rim_th) & (key < 0.25)
        rgb[m] = st.rim
    return rgb


def outline(rgb, d, styles, names, light_side_skip=True, look=None):
    """Selective outline: silhouette pixels facing away from the key get the material's outline colour."""
    hit = d.hit
    nb = neighbours(hit, False)
    edge = hit & ~(nb[(1, 0)] & nb[(-1, 0)] & nb[(0, 1)] & nb[(0, -1)])
    n = d.n
    facing = np.ones(hit.shape, bool)
    if light_side_skip and look is not None:
        lx, ly = look.key[0], look.key[1]
        facing = (n[..., 0] * lx + n[..., 1] * ly) < 0.15
    for i, nm in enumerate(names):
        st = styles.get(nm)
        if st is None:
            continue
        m = (d.mat == i) & edge & facing
        rgb[m] = st.outline
    return rgb


def depth_lines(rgb, d, styles, names, groups, gap=2.5, skip=()):
    """Darken the pixel BEHIND a depth break between different groups (contact shadow line)."""
    h, w = d.mat.shape
    gid = np.full((h, w), -1, np.int32)
    for i, nm in enumerate(names):
        gid[d.mat == i] = groups.get(nm, i)
    z = np.where(d.hit, d.z, -1e9)
    zp = np.pad(z, 1, constant_values=-1e9)
    gp = np.pad(gid, 1, constant_values=-1)
    mark = np.zeros((h, w), bool)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        zn = zp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        gn = gp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        mark |= d.hit & (gn >= 0) & (gn != gid) & (zn > z + gap)
    for i, nm in enumerate(names):
        st = styles.get(nm)
        if st is None or nm in skip:
            continue
        m = mark & (d.mat == i)
        rgb[m] = st.outline
    return rgb, mark


# ----------------------------------------------------------------------------------------- background
BG = {
    # (top, bottom, glow colour, speck colour)
    'karsk': ('#0a141a', '#05090f', '#1d3236', '#3a5650'),
    'berlin': ('#151120', '#08070d', '#3b2a35', '#6a4a40'),
    'archive': ('#0d1a22', '#04090d', '#2a2a2a', '#6e5032'),
    # round 7, Chapter 3: Veltrava station at a slate-blue dawn (lamp glow), the commission palace (navy-teal,
    # cold window daylight)
    'veltrava': ('#0c121d', '#05070d', '#22303f', '#5c6e86'),
    'palais': ('#0a1417', '#04080a', '#1e3032', '#5e7468'),
}


def background(w, h, look: Look, seed=0, extra=None):
    """Opaque painted backdrop: vertical gradient, soft key-side glow (dithered), faint haze bands."""
    top, bot, glow, speck = (hexc(c).astype(np.float32) for c in BG[look.bg])
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    t = ys / (h - 1)
    base = top[None, None] * (1 - t[..., None]) + bot[None, None] * t[..., None]
    gx, gy = look.glow
    r = np.sqrt(((xs / w - gx) * 1.0) ** 2 + ((ys / h - gy) * 1.25) ** 2)
    g = np.clip(1.0 - r / 0.62, 0, 1) ** 1.6
    bay = bayer(h, w)
    # posterise the glow into 4 dithered steps so it reads as pixel art, not a smooth gradient
    steps = 4
    gq = np.floor(g * steps + bay * 0.999) / steps
    col = base + (glow[None, None] - base) * (gq[..., None] * 0.85)
    # haze band behind the shoulders
    band = np.clip(1 - np.abs(ys - h * 0.80) / (h * 0.10), 0, 1)
    bq = (band * 2 + bay * 0.999 > 1.6).astype(np.float32)
    col = col + (glow[None, None] - col) * (bq[..., None] * 0.18)
    return np.clip(np.round(col), 0, 255).astype(np.uint8)
