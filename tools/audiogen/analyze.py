"""analyze.py -- objective checks + spectrogram previews for every generated WAV.

Metrics per file: duration, channels, RMS (dBFS, full scale = 1.0, so a full-scale sine is
-3.01 dBFS), max short-term RMS (400 ms), sample peak, 4x-oversampled true peak, clipped
samples, DC offset, energy above 16 kHz (aliasing / harshness indicator), spectral centroid,
and for loops the seam discontinuity: |x[0]-x[n-1]| relative to the median sample step, and
the >6 kHz energy in a 20 ms window across the seam relative to 400 random positions
(~1.0 = indistinguishable from any other point of the file).

Spectrogram PNGs (log-frequency panel, linear 0-22 kHz panel, short-term RMS strip, and for
loops a zoomed seam panel) go to assets/audio/_preview/ (which carries a .gdignore).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import SR, read_wav, a2db, eq  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
PREVIEW = os.path.join(AUDIO, '_preview')


# --------------------------------------------------------------------------- metrics
def true_peak(x: np.ndarray, over: int = 4, block: int = 1 << 16, ov: int = 256) -> float:
    best = 0.0
    n = x.shape[0]
    for c in range(x.shape[1]):
        i = 0
        while i < n:
            a = max(0, i - ov)
            b = min(n, i + block + ov)
            seg = x[a:b, c]
            m = len(seg)
            F = np.fft.rfft(seg * np.hanning(m) if False else seg)
            G = np.zeros(m * over // 2 + 1, dtype=complex)
            G[:len(F)] = F
            y = np.fft.irfft(G, m * over) * over
            core = y[(i - a) * over:(i - a + min(block, n - i)) * over]
            if core.size:
                best = max(best, float(np.max(np.abs(core))))
            i += block
    return best


def seam_metrics(x: np.ndarray, rng: np.random.Generator) -> dict:
    n = x.shape[0]
    steps = np.abs(np.diff(x, axis=0))
    med = np.median(steps, axis=0) + 1e-9
    jump = np.abs(x[0] - x[-1])
    ratio = float(np.max(jump / med))
    pct = float(np.mean(steps.max(axis=1) < jump.max()) * 100.0)
    # HF energy around seam vs random points (circular)
    w = int(0.02 * SR)
    def hf_energy(center):
        idx = (np.arange(center - w, center + w) % n)
        seg = x[idx].mean(axis=1)
        seg = seg * np.hanning(len(seg))
        S = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(len(seg), 1.0 / SR)
        return float(S[f > 6000].sum()) + 1e-20
    ref = np.array([hf_energy(int(c)) for c in rng.integers(0, n, 400)])
    e0 = hf_energy(0)
    # curvature across the seam vs. everywhere else (a click shows up as an outlier here)
    d2 = np.abs(x[2:] - 2 * x[1:-1] + x[:-2]).max(axis=1)
    s2 = np.abs(np.stack([x[1] - 2 * x[0] + x[-1], x[0] - 2 * x[-1] + x[-2]])).max()
    d2pct = float(np.mean(d2 < s2) * 100.0)
    return {'seam_jump_vs_median_step': round(ratio, 2), 'seam_jump_percentile': round(pct, 2),
            'seam_hf_ratio_vs_median': round(float(e0 / np.median(ref)), 3),
            'seam_hf_percentile': round(float(np.mean(ref < e0) * 100.0), 1),
            'seam_curvature_percentile': round(d2pct, 2)}


def analyze_file(path: str) -> dict:
    x, sr, loop = read_wav(path)
    n, ch = x.shape
    raw = np.round(x * 32768.0)
    clipped = int(np.sum((raw >= 32767) | (raw <= -32768)))
    mono = x.mean(axis=1)
    rmsv = float(np.sqrt(np.mean(x ** 2)))
    win = int(0.4 * SR)
    if n > win:
        c = np.concatenate([[0.0], np.cumsum((x ** 2).mean(axis=1))])
        st = np.sqrt(np.maximum((c[win:] - c[:-win]) / win, 0))
        st_max = float(st.max())
    else:
        st_max = rmsv
    win = np.hanning(n) if n > 4 * SR else np.ones(n)          # short SFX: no window (transients sit at the start)
    S = np.abs(np.fft.rfft(mono * win)) ** 2 if n > 16 else np.zeros(1)
    f = np.fft.rfftfreq(n, 1.0 / SR) if n > 16 else np.zeros(1)
    tot = S.sum() + 1e-20
    res = {
        'file': os.path.relpath(path, ROOT).replace('\\', '/'),
        'sr': sr, 'channels': ch, 'seconds': round(n / sr, 3), 'frames': n,
        'loop': list(loop) if loop else None,
        'rms_dbfs': round(float(a2db(rmsv)), 2),
        'max_rms400ms_dbfs': round(float(a2db(st_max)), 2),
        'peak_dbfs': round(float(a2db(np.max(np.abs(x)))), 2),
        'true_peak_dbfs': round(float(a2db(true_peak(x))), 2),
        'clipped_samples': clipped,
        'dc_offset': [round(float(v), 6) for v in x.mean(axis=0)],
        'hf_above_16k_db': round(float(10 * np.log10(S[f > 16000].sum() / tot + 1e-20)), 1),
        'centroid_hz': round(float((S * f).sum() / tot), 0),
    }
    if loop:
        res.update(seam_metrics(x, np.random.default_rng(1)))
    return res


# --------------------------------------------------------------------------- spectrogram
_CM = np.array([[0, 0, 0], [12, 8, 40], [52, 16, 96], [110, 24, 110], [170, 50, 80],
                [222, 100, 40], [248, 170, 40], [252, 236, 160], [255, 255, 255]], dtype=float)


def colormap(v: np.ndarray) -> np.ndarray:
    v = np.clip(v, 0, 1) * (len(_CM) - 1)
    i = np.minimum(v.astype(int), len(_CM) - 2)
    w = (v - i)[..., None]
    return (_CM[i] * (1 - w) + _CM[i + 1] * w).astype(np.uint8)


def stft_db(mono: np.ndarray, nfft: int, hop: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(mono)
    pad = np.concatenate([np.zeros(nfft // 2), mono, np.zeros(nfft)])
    frames = 1 + max(0, (n) // hop)
    idx = np.arange(frames)[:, None] * hop + np.arange(nfft)[None, :]
    idx = np.minimum(idx, len(pad) - 1)
    w = np.hanning(nfft)
    S = np.abs(np.fft.rfft(pad[idx] * w, axis=1)) / (w.sum() / 2)
    return 20 * np.log10(S + 1e-12), np.fft.rfftfreq(nfft, 1.0 / SR)


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except Exception:  # pragma: no cover
        return ImageFont.load_default()


def render_spectrogram(path: str, out_png: str, title: str = '', db_lo: float = -110.0,
                       db_hi: float = -10.0) -> None:
    x, sr, loop = read_wav(path)
    mono = x.mean(axis=1)
    n = len(mono)
    W = 1400
    hop = max(64, n // W)
    nfft = 4096 if n > SR * 4 else 2048
    D, f = stft_db(mono, nfft, hop)
    D = D[:W]
    cols = D.shape[0]
    # log panel
    H1 = 330
    fl = np.exp(np.linspace(np.log(20000), np.log(20), H1))
    log_panel = np.stack([np.interp(fl, f, D[c]) for c in range(cols)], axis=1)
    H2 = 220
    fli = np.linspace(22050, 0, H2)
    lin_panel = np.stack([np.interp(fli, f, D[c]) for c in range(cols)], axis=1)
    def to_img(P):
        return colormap((P - db_lo) / (db_hi - db_lo))
    img1 = to_img(log_panel)
    img2 = to_img(lin_panel)
    # rms strip
    H3 = 110
    win = max(1, int(0.1 * SR))
    c2 = np.concatenate([[0.0], np.cumsum((x ** 2).mean(axis=1))])
    pos = np.linspace(0, n - 1, cols).astype(int)
    lo = np.maximum(0, pos - win // 2)
    hi = np.minimum(n, lo + win)
    st = np.sqrt(np.maximum((c2[hi] - c2[lo]) / np.maximum(hi - lo, 1), 1e-20))
    st_db = 20 * np.log10(st + 1e-12)
    strip = np.full((H3, cols, 3), 18, np.uint8)
    yv = np.clip(((-st_db) / 60.0) * H3, 0, H3 - 1).astype(int)   # 0 dB top, -60 bottom
    for c in range(cols):
        strip[yv[c]:, c] = (60, 120, 150)
    for ref in (-20, -24, -6):
        ry = int(-ref / 60.0 * H3)
        strip[ry, ::4] = (220, 220, 90) if ref != -6 else (230, 90, 90)
    L = 70
    T = 40
    total_h = T + H1 + 8 + H2 + 8 + H3 + 30
    canvas = Image.new('RGB', (L + cols + 20, total_h), (10, 10, 12))
    canvas.paste(Image.fromarray(img1), (L, T))
    canvas.paste(Image.fromarray(img2), (L, T + H1 + 8))
    canvas.paste(Image.fromarray(strip), (L, T + H1 + 8 + H2 + 8))
    d = ImageDraw.Draw(canvas)
    fnt = _font(13)
    d.text((8, 8), title, fill=(230, 230, 230), font=_font(15))
    for fr in (50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        yy = T + int((np.log(20000) - np.log(fr)) / (np.log(20000) - np.log(20)) * (H1 - 1))
        d.text((6, yy - 7), f'{fr if fr < 1000 else str(fr // 1000) + "k"}', fill=(180, 180, 180), font=fnt)
        d.line([(L - 6, yy), (L - 1, yy)], fill=(180, 180, 180))
    for fr in (0, 5000, 10000, 15000, 20000):
        yy = T + H1 + 8 + int((22050 - fr) / 22050 * (H2 - 1))
        d.text((6, yy - 7), f'{fr // 1000}k', fill=(180, 180, 180), font=fnt)
    d.text((6, T + H1 + 8 + H2 + 8 + 2), 'RMS', fill=(180, 180, 180), font=fnt)
    d.text((6, T + H1 + 8 + H2 + 8 + 2 + int(20 / 60 * H3) - 7), '-20', fill=(220, 220, 90), font=fnt)
    d.text((6, T + H1 + 8 + H2 + 8 + 2 + int(6 / 60 * H3) - 7), '-6', fill=(230, 90, 90), font=fnt)
    dur = n / SR
    step = 1 if dur <= 6 else (5 if dur <= 40 else 10)
    ybase = T + H1 + 8 + H2 + 8 + H3 + 4
    for s in np.arange(0, dur + 1e-9, step):
        xx = L + int(s / dur * (cols - 1))
        d.line([(xx, ybase - 3), (xx, ybase + 2)], fill=(200, 200, 200))
        d.text((xx - 6, ybase + 4), f'{s:g}s', fill=(200, 200, 200), font=fnt)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    canvas.save(out_png)
    if loop:
        render_seam(x, out_png.replace('.png', '_seam.png'), title + '  [loop seam: end | start]')


def render_seam(x: np.ndarray, out_png: str, title: str) -> None:
    n = x.shape[0]
    k = int(1.5 * SR)
    seg = np.concatenate([x[-k:], x[:k]], axis=0)
    mono = seg.mean(axis=1)
    D, f = stft_db(mono, 1024, 64)
    cols = D.shape[0]
    H1 = 260
    fl = np.exp(np.linspace(np.log(20000), np.log(20), H1))
    P = np.stack([np.interp(fl, f, D[c]) for c in range(cols)], axis=1)
    img = colormap((P + 110) / 100)
    # waveform +-12 ms around the seam
    z = int(0.012 * SR)
    wv = np.concatenate([x[-z:], x[:z]], axis=0)
    Wd, Hw = 2 * z, 160
    wimg = np.full((Hw, Wd, 3), 16, np.uint8)
    amp = max(1e-6, float(np.max(np.abs(wv))))
    for c, col in enumerate([(120, 200, 240), (240, 160, 120)]):
        yy = (Hw / 2 - wv[:, c] / amp * (Hw / 2 - 6)).astype(int)
        for i in range(Wd - 1):
            a, b = sorted((yy[i], yy[i + 1]))
            wimg[a:b + 1, i] = col
    wimg[:, z - 1:z + 1] = (200, 60, 60)
    canvas = Image.new('RGB', (max(cols, Wd) + 20, H1 + Hw + 60), (10, 10, 12))
    canvas.paste(Image.fromarray(img), (10, 30))
    canvas.paste(Image.fromarray(wimg), (10, 40 + H1))
    d = ImageDraw.Draw(canvas)
    d.text((10, 8), title, fill=(230, 230, 230), font=_font(13))
    d.line([(10 + cols // 2, 30), (10 + cols // 2, 30 + H1)], fill=(255, 60, 60))
    d.text((10, 44 + H1 + Hw), 'waveform +-12 ms around seam (L blue, R orange), red = loop point',
           fill=(200, 200, 200), font=_font(12))
    canvas.save(out_png)


def ensure_preview_dir() -> None:
    os.makedirs(PREVIEW, exist_ok=True)
    gi = os.path.join(PREVIEW, '.gdignore')
    if not os.path.exists(gi):
        open(gi, 'w').close()


def analyze_all(names_paths: list[tuple[str, str]], spectro: set[str] | None = None) -> list[dict]:
    ensure_preview_dir()
    out = []
    for name, p in names_paths:
        r = analyze_file(p)
        r['name'] = name
        out.append(r)
        if spectro is None or name in spectro:
            render_spectrogram(p, os.path.join(PREVIEW, name + '.png'),
                               f"{name}   RMS {r['rms_dbfs']} dBFS   peak {r['peak_dbfs']} dBFS   {r['seconds']} s")
    return out


if __name__ == '__main__':
    ensure_preview_dir()
    paths = sys.argv[1:]
    for p in paths:
        r = analyze_file(p)
        print(json.dumps(r))
        nm = os.path.splitext(os.path.basename(p))[0]
        render_spectrogram(p, os.path.join(PREVIEW, nm + '.png'), nm)


def render_zoom(path: str, out_png: str, t0: float, t1: float, title: str = '') -> None:
    """High-resolution spectrogram of [t0, t1] seconds (log frequency, 20 Hz-20 kHz)."""
    x, sr, loop = read_wav(path)
    a, b = int(t0 * SR), int(t1 * SR)
    mono = x[a:b].mean(axis=1)
    W = 1400
    hop = max(32, len(mono) // W)
    D, f = stft_db(mono, 4096, hop)
    D = D[:W]
    H1 = 520
    fl = np.exp(np.linspace(np.log(20000), np.log(20), H1))
    P = np.stack([np.interp(fl, f, D[c]) for c in range(D.shape[0])], axis=1)
    img = colormap((P + 110) / 100)
    canvas = Image.new('RGB', (D.shape[0] + 80, H1 + 60), (10, 10, 12))
    canvas.paste(Image.fromarray(img), (70, 30))
    d = ImageDraw.Draw(canvas)
    d.text((8, 8), f'{title}  [{t0:g}-{t1:g} s]', fill=(230, 230, 230), font=_font(14))
    for fr in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
        yy = 30 + int((np.log(20000) - np.log(fr)) / (np.log(20000) - np.log(20)) * (H1 - 1))
        d.text((6, yy - 7), f'{fr if fr < 1000 else str(fr // 1000) + "k"}', fill=(180, 180, 180), font=_font(12))
    for s in np.arange(np.ceil(t0), t1 + 1e-9, 1.0):
        xx = 70 + int((s - t0) / (t1 - t0) * (D.shape[0] - 1))
        d.text((xx - 6, H1 + 36), f'{s:g}', fill=(200, 200, 200), font=_font(12))
    canvas.save(out_png)


def band_shares(path: str) -> dict:
    """Energy share (%) per band of the mono mix + approx. K-weighted loudness (LUFS, ungated)."""
    x, sr, _ = read_wav(path)
    mono = x.mean(axis=1)
    S = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1.0 / SR)
    tot = S.sum() + 1e-20
    edges = [0, 60, 120, 250, 500, 1000, 2000, 4000, 8000, 22050]
    sh = {f'{edges[i]}-{edges[i + 1]}': round(float(S[(f >= edges[i]) & (f < edges[i + 1])].sum() / tot * 100), 1)
          for i in range(len(edges) - 1)}
    k = eq(x, ('hp', 40.0, 2), ('hs', 1700.0, 4.0, 1.5), circular=True)
    ms = float(np.mean(k ** 2, axis=0).sum())
    sh['lufs_approx'] = round(-0.691 + 10 * np.log10(ms + 1e-20), 1)
    return sh



def render_sheet(paths: list, out_png: str, cols: int = 4, cw: int = 360, chh: int = 150) -> None:
    """Contact sheet for short SFX: per file a log-frequency spectrogram (20 Hz-20 kHz) with the
    peak envelope overlaid (blue), name, length and peak in the caption."""
    rows = (len(paths) + cols - 1) // cols
    cap = 18
    canvas = Image.new('RGB', (cols * (cw + 10) + 10, rows * (chh + cap + 12) + 10), (10, 10, 12))
    d = ImageDraw.Draw(canvas)
    for i, p in enumerate(paths):
        x, sr, loop = read_wav(p)
        mono = x.mean(axis=1)
        n = len(mono)
        hop = max(8, n // cw)
        D, f = stft_db(mono, 1024, hop)
        D = D[:cw]
        fl = np.exp(np.linspace(np.log(20000), np.log(20), chh))
        P = np.stack([np.interp(fl, f, D[c]) for c in range(D.shape[0])], axis=1)
        img = colormap((P + 110) / 100)
        cx = 10 + (i % cols) * (cw + 10)
        cy = 10 + (i // cols) * (chh + cap + 12)
        canvas.paste(Image.fromarray(img), (cx, cy + cap))
        env = [float(np.max(np.abs(x[j * hop:(j + 1) * hop]))) if j * hop < n else 0.0 for j in range(D.shape[0])]
        for j, e in enumerate(env):
            h = int(min(1.0, e / 0.5) * (chh // 2 - 2))
            if h > 0:
                d.line([(cx + j, cy + cap + chh // 2 - h), (cx + j, cy + cap + chh // 2 + h)], fill=(90, 200, 255))
        nm = os.path.splitext(os.path.basename(p))[0]
        d.text((cx, cy + 1), f'{nm}  {n / SR:.2f}s  pk {float(a2db(np.max(np.abs(x)))):.1f}',
               fill=(230, 230, 230), font=_font(12))
    canvas.save(out_png)
