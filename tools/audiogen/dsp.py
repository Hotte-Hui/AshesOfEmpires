"""dsp.py -- core DSP toolkit for the ASHES OF EMPIRES soundscape (numpy only, no samples).

Everything in assets/audio/ is synthesised from scratch with these primitives:
noise generators (FFT / STFT domain, periodic so loops are seamless by construction),
zero-phase spectral filters, causal biquads (via impulse response + FFT convolution),
circular convolution, a generated stereo convolution reverb, periodic smooth control
signals, a look-ahead limiter and a 16-bit WAV writer (stdlib `wave`) that appends a RIFF
`smpl` loop chunk which Godot's WAV importer reads ("Detect From WAV").

Conventions
-----------
* Sample rate SR = 44100 Hz.  Signals are float64 arrays, mono (n,) or stereo (n, 2).
* "circular=True" means the signal is one period of a loop: every filter / reverb / event
  wraps around the end, so sample n-1 flows into sample 0 without a seam.
* Levels: dBFS where 1.0 == full scale (a full-scale sine therefore has RMS -3.01 dBFS).
"""
from __future__ import annotations

import os
import struct
import wave

import numpy as np

SR = 44100
TAU = 2.0 * np.pi


# --------------------------------------------------------------------------- basics
def secs(s: float) -> int:
    return int(round(s * SR))


def db2a(db):
    return 10.0 ** (np.asarray(db, dtype=float) / 20.0)


def a2db(a):
    return 20.0 * np.log10(np.maximum(np.abs(np.asarray(a, dtype=float)), 1e-12))


def as2d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[:, None] if x.ndim == 1 else x


def rms(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x * x))) if x.size else 0.0


def rms_db(x) -> float:
    return float(a2db(rms(x)))


def peak_db(x) -> float:
    return float(a2db(np.max(np.abs(x)) if np.size(x) else 0.0))


def midi_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def to_stereo(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x


def pan2(x: np.ndarray, p) -> np.ndarray:
    """Equal-power pan of a mono signal; p in [-1, 1] (scalar or per-sample array)."""
    x = np.asarray(x, dtype=float)
    a = (np.clip(p, -1.0, 1.0) + 1.0) * (np.pi / 4.0)
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def width(st: np.ndarray, w: float) -> np.ndarray:
    """Mid/side stereo width (0 = mono, 1 = unchanged, >1 wider)."""
    m = 0.5 * (st[:, 0] + st[:, 1])
    s = 0.5 * (st[:, 0] - st[:, 1]) * w
    return np.stack([m + s, m - s], axis=1)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


# --------------------------------------------------------------------------- event placement
def place(buf: np.ndarray, sig: np.ndarray, start: int, gain: float = 1.0, circular: bool = True) -> None:
    """Add `sig` into `buf` at sample `start`.  circular: wrap past the end to the beginning."""
    n = buf.shape[0]
    sig = np.asarray(sig, dtype=float) * gain
    if buf.ndim == 2 and sig.ndim == 1:
        sig = to_stereo(sig) if buf.shape[1] == 2 else sig[:, None]
    m = sig.shape[0]
    if circular:
        start %= n
        pos = 0
        while pos < m:
            s = (start + pos) % n
            k = min(m - pos, n - s)
            buf[s:s + k] += sig[pos:pos + k]
            pos += k
    else:
        if start >= n or start + m <= 0:
            return
        a = max(0, start)
        b = min(n, start + m)
        buf[a:b] += sig[a - start:b - start]


def fold(x: np.ndarray, n: int) -> np.ndarray:
    """Fold a long linear render into a loop of length n (tails wrap around)."""
    out = np.zeros((n,) + x.shape[1:])
    for i in range(0, x.shape[0], n):
        seg = x[i:i + n]
        out[:seg.shape[0]] += seg
    return out


# --------------------------------------------------------------------------- spectral shaping
def mag_lp(f, fc, order=2):
    return 1.0 / np.sqrt(1.0 + (np.asarray(f) / fc) ** (2 * order))


def mag_hp(f, fc, order=2):
    f = np.maximum(np.asarray(f, dtype=float), 1e-6)
    return 1.0 / np.sqrt(1.0 + (fc / f) ** (2 * order))


def mag_bp(f, lo, hi, order=2):
    return mag_hp(f, lo, order) * mag_lp(f, hi, order)


def mag_bell(f, fc, gain_db, oct_bw=1.0):
    """Smooth bell on a log-frequency axis (gain_db at fc, Gaussian with sigma = oct_bw/2 octaves)."""
    f = np.maximum(np.asarray(f, dtype=float), 1e-3)
    d = np.log2(f / fc) / (0.5 * oct_bw)
    return 10.0 ** (gain_db * np.exp(-0.5 * d * d) / 20.0)


def mag_shelf(f, fc, gain_db, high=True, steep=1.0):
    """Smooth shelf on a log axis (logistic over ~2/steep octaves)."""
    f = np.maximum(np.asarray(f, dtype=float), 1e-3)
    s = 1.0 / (1.0 + np.exp(-2.2 * steep * np.log2(f / fc)))
    if not high:
        s = 1.0 - s
    return 10.0 ** (gain_db * s / 20.0)


def mag_tilt(f, db_per_oct, f0=1000.0, fmin=20.0):
    f = np.maximum(np.asarray(f, dtype=float), fmin)
    return 10.0 ** (db_per_oct * np.log2(f / f0) / 20.0)


def spectral(x: np.ndarray, H, circular: bool = True, pad: int | None = None) -> np.ndarray:
    """Zero-phase filter: multiply the rFFT by real gains H(f).  H: callable(freqs) or array.
    circular=False pads both ends (pre-ring room) and returns the original length."""
    x = np.asarray(x, dtype=float)
    mono = x.ndim == 1
    X2 = x[:, None] if mono else x
    n = X2.shape[0]
    if circular:
        buf, off, N = X2, 0, n
    else:
        p = pad if pad is not None else min(secs(0.25), max(256, n // 4))
        N = n + 2 * p
        buf = np.zeros((N, X2.shape[1]))
        buf[p:p + n] = X2
        off = p
    F = np.fft.rfft(buf, axis=0)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    g = H(f) if callable(H) else np.asarray(H)
    F *= g[:, None]
    y = np.fft.irfft(F, N, axis=0)[off:off + n]
    return y[:, 0] if mono else y


def eq(x: np.ndarray, *bands, circular: bool = True) -> np.ndarray:
    """Chain of zero-phase magnitude shapes. bands: ('lp', fc, order) ('hp', fc, order)
    ('bell', fc, db, oct) ('hs', fc, db) ('ls', fc, db) ('tilt', db_per_oct)."""
    def H(f):
        g = np.ones_like(f)
        for b in bands:
            k = b[0]
            if k == 'lp':
                g = g * mag_lp(f, b[1], b[2] if len(b) > 2 else 2)
            elif k == 'hp':
                g = g * mag_hp(f, b[1], b[2] if len(b) > 2 else 2)
            elif k == 'bell':
                g = g * mag_bell(f, b[1], b[2], b[3] if len(b) > 3 else 1.0)
            elif k == 'hs':
                g = g * mag_shelf(f, b[1], b[2], True, b[3] if len(b) > 3 else 1.0)
            elif k == 'ls':
                g = g * mag_shelf(f, b[1], b[2], False, b[3] if len(b) > 3 else 1.0)
            elif k == 'tilt':
                g = g * mag_tilt(f, b[1], b[2] if len(b) > 2 else 1000.0)
            else:
                raise ValueError(k)
        return g
    return spectral(x, H, circular=circular)


# --------------------------------------------------------------------------- causal biquads
def biquad(kind: str, fc: float, q: float = 0.7071, gain_db: float = 0.0):
    """RBJ cookbook biquad -> (b, a) normalised."""
    A = 10.0 ** (gain_db / 40.0)
    w0 = TAU * min(fc, 0.49 * SR) / SR
    cw, sw = np.cos(w0), np.sin(w0)
    al = sw / (2.0 * q)
    if kind == 'lp':
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == 'hp':
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == 'bp':  # 0 dB peak
        b = [al, 0.0, -al]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == 'peak':
        b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind in ('ls', 'hs'):
        sq = 2.0 * np.sqrt(A) * al
        if kind == 'ls':
            b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
            a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
            a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.array(b, dtype=float); a = np.array(a, dtype=float)
    return b / a[0], a / a[0]


_IR_CACHE: dict = {}


def iir_ir(b, a, max_len: int = SR * 4, tol: float = 1e-9) -> np.ndarray:
    """Impulse response of a 2nd-order IIR via the closed-form pole solution (vectorised)."""
    key = (tuple(np.round(b, 14)), tuple(np.round(a, 14)), max_len)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    b0, b1, b2 = b
    _, a1, a2 = a
    poles = np.roots([1.0, a1, a2])
    r = float(np.max(np.abs(poles)))
    if r >= 1.0:
        raise ValueError('unstable biquad')
    n_need = 8 if r < 1e-6 else int(min(max_len, 8 + np.log(tol) / np.log(r)))
    # simulate a head exactly (whole IR when short), then extend analytically through the poles
    head = n_need if n_need <= 4096 else 64
    y = np.zeros(head)
    for i in range(head):
        acc = b0 if i == 0 else 0.0
        if i == 1:
            acc += b1
        if i == 2:
            acc += b2
        if i >= 1:
            acc -= a1 * y[i - 1]
        if i >= 2:
            acc -= a2 * y[i - 2]
        y[i] = acc
    if n_need <= head:
        out = y
    else:
        # homogeneous solution for n >= 2: y[n] = c1 p1^n + c2 p2^n, fit on y[head-2], y[head-1]
        p1, p2 = poles
        n0 = head - 2
        if abs(p1 - p2) < 1e-12:
            M = np.array([[p1 ** n0, n0 * p1 ** n0], [p1 ** (n0 + 1), (n0 + 1) * p1 ** (n0 + 1)]], dtype=complex)
            c = np.linalg.solve(M, y[n0:n0 + 2].astype(complex))
            k = np.arange(head, n_need)
            ext = (c[0] + c[1] * k) * p1 ** k
        else:
            M = np.array([[p1 ** n0, p2 ** n0], [p1 ** (n0 + 1), p2 ** (n0 + 1)]], dtype=complex)
            c = np.linalg.solve(M, y[n0:n0 + 2].astype(complex))
            k = np.arange(head, n_need)
            ext = c[0] * np.exp(k * np.log(p1 + 0j)) + c[1] * np.exp(k * np.log(p2 + 0j))
        out = np.concatenate([y, ext.real])
    _IR_CACHE[key] = out
    return out


def next_fast(n: int) -> int:
    """Smallest 2^a 3^b 5^c >= n."""
    best = 1 << (int(n - 1).bit_length())
    p5 = 1
    while p5 < best:
        p35 = p5
        while p35 < best:
            v = p35
            while v < n:
                v *= 2
            best = min(best, v)
            p35 *= 3
        p5 *= 5
    return best


def fftconv(x: np.ndarray, h: np.ndarray, circular: bool = False, full: bool = False) -> np.ndarray:
    """FFT convolution, channel-broadcasting (mono x with stereo h -> stereo).
    circular: result has len(x) and wraps.  Otherwise returns len(x) samples (or full length)."""
    x = np.asarray(x, dtype=float); h = np.asarray(h, dtype=float)
    mono = x.ndim == 1 and h.ndim == 1
    X2, H2 = as2d(x), as2d(h)
    n, m = X2.shape[0], H2.shape[0]
    if circular:
        if m > n:
            H2 = fold(H2, n)
            m = n
        N = n
        Xf = np.fft.rfft(X2, N, axis=0)
        Hf = np.fft.rfft(H2, N, axis=0)
        y = np.fft.irfft(Xf * Hf, N, axis=0)
    else:
        L = n + m - 1
        N = next_fast(L)
        Xf = np.fft.rfft(X2, N, axis=0)
        Hf = np.fft.rfft(H2, N, axis=0)
        y = np.fft.irfft(Xf * Hf, N, axis=0)[:L if full else n]
    return y[:, 0] if mono else y


def filt(x: np.ndarray, kind: str, fc: float, q: float = 0.7071, gain_db: float = 0.0,
         circular: bool = False) -> np.ndarray:
    """Causal biquad filter (exact IR, FFT convolution)."""
    b, a = biquad(kind, fc, q, gain_db)
    return fftconv(x, iir_ir(b, a), circular=circular)


def resonators(x: np.ndarray, modes, circular: bool = False) -> np.ndarray:
    """Bank of parallel 2-pole resonators. modes: [(freq, t60_s, gain)] -> causal, summed."""
    n_max = 1
    irs = []
    for f, t60, g in modes:
        if f >= 0.47 * SR:
            continue
        L = secs(min(t60 * 1.2, 6.0)) + 1
        t = np.arange(L) / SR
        irs.append(g * np.exp(-6.9078 * t / t60) * np.sin(TAU * f * t))
        n_max = max(n_max, L)
    h = np.zeros(n_max)
    for ir in irs:
        h[:len(ir)] += ir
    return fftconv(x, h, circular=circular)


# --------------------------------------------------------------------------- noise
def white(n: int, rng: np.random.Generator, ch: int = 1) -> np.ndarray:
    return rng.standard_normal(n) if ch == 1 else rng.standard_normal((n, ch))


def shaped_noise(n: int, rng: np.random.Generator, H, ch: int = 1, corr: float = 0.0) -> np.ndarray:
    """Periodic noise (one loop of length n) with magnitude spectrum H(f); unit RMS.
    corr: inter-channel correlation for stereo (0 = independent)."""
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = H(f) if callable(H) else H
    def one():
        Z = rng.standard_normal(len(f)) + 1j * rng.standard_normal(len(f))
        Z[0] = 0.0
        return Z
    if ch == 1:
        y = np.fft.irfft(one() * g, n)
    else:
        common = one()
        cols = []
        for _ in range(ch):
            Z = np.sqrt(corr) * common + np.sqrt(1.0 - corr) * one()
            cols.append(np.fft.irfft(Z * g, n))
        y = np.stack(cols, axis=1)
    r = rms(y)
    return y / r if r > 0 else y


def hann(n: int) -> np.ndarray:
    return 0.5 - 0.5 * np.cos(TAU * np.arange(n) / n)


def _ola(frames: np.ndarray, hop: int, n: int) -> np.ndarray:
    """Circular overlap-add of frames (F, nfft) with nfft = R*hop, frame k starts at k*hop."""
    F, nfft = frames.shape
    R = nfft // hop
    out = np.zeros((F, hop))
    for j in range(R):
        out += np.roll(frames[:, j * hop:(j + 1) * hop], j, axis=0)
    return out.reshape(-1)[:n]


def stft_noise(n: int, gain_fn, rng: np.random.Generator, ch: int = 2, nfft: int = 2048,
               hop: int = 512, corr: float = 0.0) -> np.ndarray:
    """Periodic noise with a time-varying spectrum.  gain_fn(tc, f) -> (F, B) magnitudes, where
    tc are frame-centre times (s) and f the bin frequencies.  n must be a multiple of hop."""
    assert n % hop == 0, 'length must be a multiple of hop'
    F = n // hop
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    tc = (np.arange(F) * hop + nfft / 2) / SR % (n / SR)
    G = np.asarray(gain_fn(tc, f), dtype=np.float32)
    w = np.sqrt(hann(nfft)).astype(np.float32)
    B = len(f)
    def rnd():
        return (rng.standard_normal((F, B), dtype=np.float32)
                + 1j * rng.standard_normal((F, B), dtype=np.float32)).astype(np.complex64)
    common = rnd() if (ch > 1 and corr > 0) else None
    outs = []
    for c in range(ch):
        Z = rnd()
        if common is not None:
            Z = np.sqrt(corr) * common + np.sqrt(1.0 - corr) * Z
        Gc = G[..., c] if G.ndim == 3 else G
        frames = np.fft.irfft(Z * Gc, nfft, axis=1).astype(np.float32) * w
        outs.append(_ola(frames, hop, n))
    y = outs[0] if ch == 1 else np.stack(outs, axis=1)
    return y.astype(float)


def stft_filter(x: np.ndarray, gain_fn, nfft: int = 2048, hop: int = 512) -> np.ndarray:
    """Circular time-varying zero-phase filtering.  gain_fn(tc, f) -> (F, B)."""
    x = np.asarray(x, dtype=float)
    mono = x.ndim == 1
    X2 = as2d(x)
    n = X2.shape[0]
    pad = (-n) % hop
    N = n + pad
    F = N // hop
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    tc = (np.arange(F) * hop + nfft / 2) / SR
    G = np.asarray(gain_fn(tc, f), dtype=np.float32)
    w = np.sqrt(hann(nfft))
    idx = (np.arange(F)[:, None] * hop + np.arange(nfft)[None, :]) % N
    outs = []
    for c in range(X2.shape[1]):
        xc = np.concatenate([X2[:, c], np.zeros(pad)]) if pad else X2[:, c]
        fr = xc[idx] * w
        S = np.fft.rfft(fr, axis=1)
        Gc = G[..., c] if G.ndim == 3 else G
        y = np.fft.irfft(S * Gc, nfft, axis=1) * w
        outs.append(_ola(y, hop, N)[:n] / (nfft / hop / 2.0))
    y = np.stack(outs, axis=1)
    return y[:, 0] if mono else y


# --------------------------------------------------------------------------- control signals
def smooth_periodic(n: int, n_ctrl: int, rng: np.random.Generator) -> np.ndarray:
    """Periodic, band-limited random curve of length n with ~n_ctrl independent values per
    period (zero mean, unit std)."""
    n_ctrl = max(3, int(n_ctrl))
    c = rng.standard_normal(n_ctrl)
    C = np.fft.rfft(c)
    Y = np.zeros(n // 2 + 1, dtype=complex)
    k = min(len(C), len(Y))
    taper = np.cos(0.5 * np.pi * np.arange(k) / k) ** 2  # soften the band edge
    Y[:k] = C[:k] * taper * (n / n_ctrl)
    y = np.fft.irfft(Y, n)
    y -= y.mean()
    s = y.std()
    return y / s if s > 0 else y


def smooth_rand(n: int, rate_hz: float, rng: np.random.Generator) -> np.ndarray:
    """Non-periodic use: smooth random curve with ~rate_hz independent values per second."""
    m = n + secs(2.0 / max(rate_hz, 0.05))
    y = smooth_periodic(m, max(3, int(m / SR * rate_hz)), rng)
    return y[:n]


def env_ar(n: int, attack: float, release: float, hold: float | None = None, curve: float = 1.0) -> np.ndarray:
    """Attack / (hold) / exponential-ish release envelope of n samples (seconds)."""
    t = np.arange(n) / SR
    a = smoothstep(t / max(attack, 1e-4)) if attack > 0 else np.ones(n)
    if hold is None:
        hold = max(0.0, n / SR - attack - release)
    r0 = attack + hold
    r = np.where(t < r0, 1.0, np.exp(-6.9078 * (t - r0) / max(release, 1e-4) * curve))
    e = a * r
    return e


def exp_decay(n: int, t60: float) -> np.ndarray:
    return np.exp(-6.9078 * (np.arange(n) / SR) / t60)


def fade(x: np.ndarray, fin: float = 0.0, fout: float = 0.0) -> np.ndarray:
    x = np.array(x, dtype=float, copy=True)
    n = x.shape[0]
    if fin > 0:
        k = min(n, secs(fin))
        g = np.sin(0.5 * np.pi * np.arange(k) / k) ** 2
        x[:k] *= g if x.ndim == 1 else g[:, None]
    if fout > 0:
        k = min(n, secs(fout))
        g = np.cos(0.5 * np.pi * np.arange(k) / k) ** 2
        x[n - k:] *= g if x.ndim == 1 else g[:, None]
    return x


# --------------------------------------------------------------------------- reverb
def make_ir(length: float = 3.0, rt_low: float = 2.4, rt_high: float = 1.0, predelay: float = 0.02,
            er_taps: int = 10, er_span: float = 0.07, er_gain: float = 0.6, seed: int = 1,
            lowcut: float = 60.0, highcut: float = 9000.0, stereo_corr: float = 0.0,
            build: float = 0.012, slap=None) -> np.ndarray:
    """Generated stereo impulse response: frequency-dependent exponential decay of
    decorrelated noise (8 log bands), early reflections and optional discrete slap echoes
    slap=[(delay_s, gain, lp_hz)] (outdoor facades).  Energy-normalised."""
    rng = np.random.default_rng(seed)
    n = secs(length)
    t = np.arange(n) / SR
    noise = rng.standard_normal((n, 2))
    if stereo_corr > 0:
        m = noise.mean(axis=1, keepdims=True)
        noise = np.sqrt(stereo_corr) * m * np.sqrt(2) + np.sqrt(1 - stereo_corr) * noise
    Fq = np.fft.rfft(noise, axis=0)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    centers = np.array([63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000], dtype=float)
    lc = np.log2(np.maximum(f, 1.0))
    lcen = np.log2(centers)
    # partition of unity with triangular weights on log-frequency
    W = np.zeros((len(centers), len(f)))
    for i in range(len(centers)):
        if i == 0:
            W[i] = np.clip((lcen[1] - lc) / (lcen[1] - lcen[0]), 0, 1)
        elif i == len(centers) - 1:
            W[i] = np.clip((lc - lcen[i - 1]) / (lcen[i] - lcen[i - 1]), 0, 1)
        else:
            up = (lc - lcen[i - 1]) / (lcen[i] - lcen[i - 1])
            dn = (lcen[i + 1] - lc) / (lcen[i + 1] - lcen[i])
            W[i] = np.clip(np.minimum(up, dn), 0, 1)
    # rt per band: rt_low below 250 Hz, log-interpolated to rt_high at 8 kHz
    x = np.clip((lcen - np.log2(250)) / (np.log2(8000) - np.log2(250)), 0, 1)
    rts = rt_low * (rt_high / rt_low) ** x
    ir = np.zeros((n, 2))
    for i in range(len(centers)):
        band = np.fft.irfft(Fq * W[i][:, None], n, axis=0)
        ir += band * np.exp(-6.9078 * t / rts[i])[:, None]
    ir *= smoothstep(t / max(build, 1e-4))[:, None]
    # early reflections
    for _ in range(er_taps):
        d = secs(rng.uniform(0.004, er_span))
        g = er_gain * rng.uniform(0.3, 1.0) * np.exp(-d / SR / er_span)
        side = rng.uniform(-1, 1)
        if d < n:
            ir[d, 0] += g * (1 + 0.5 * side) * rng.choice([-1, 1]) * 4.0
            ir[min(n - 1, d + rng.integers(0, 40)), 1] += g * (1 - 0.5 * side) * rng.choice([-1, 1]) * 4.0
    if slap:
        for (dl, g, lp) in slap:
            d = secs(dl)
            if d >= n:
                continue
            k = secs(0.02)
            burst = rng.standard_normal((k, 2)) * np.hanning(k)[:, None]
            burst = eq(burst, ('lp', lp, 2), circular=False)
            burst /= max(rms(burst), 1e-9)
            e = min(n, d + k)
            ir[d:e] += g * burst[:e - d] * 0.5
    ir = eq(ir, ('hp', lowcut, 2), ('lp', highcut, 4), circular=False)
    pre = np.zeros((secs(predelay), 2))
    ir = np.concatenate([pre, ir], axis=0)
    ir /= np.sqrt(np.sum(ir ** 2) / 2.0)
    return ir


def reverb(x: np.ndarray, ir: np.ndarray, wet: float = 0.3, dry: float = 1.0, circular: bool = True,
           tail: bool = False) -> np.ndarray:
    """Convolution reverb.  x mono/stereo -> stereo.  circular for loops; tail=True returns
    len(x)+len(ir)-1 samples for one-shots."""
    xs = to_stereo(as2d(x))
    if circular:
        w = fftconv(xs, ir, circular=True)
        return dry * xs + wet * w
    w = fftconv(xs, ir, circular=False, full=True)
    out = wet * w
    out[:xs.shape[0]] += dry * xs
    return out if tail else out[:xs.shape[0]]


# --------------------------------------------------------------------------- dynamics
def _win_min(x: np.ndarray, w: int, forward: bool = True) -> np.ndarray:
    """Sliding-window minimum (van Herk / Gil-Werman).  forward: min(x[i:i+w]) else min(x[i-w+1:i+1])."""
    if w <= 1:
        return x.copy()
    n = len(x)
    src = x if forward else x[::-1]
    pad = (-n) % w
    big = np.concatenate([src, np.full(pad + w, src[-1] if not forward else np.inf)])
    big[n:] = np.inf
    nb = len(big) // w
    B = big[:nb * w].reshape(nb, w)
    pre = np.minimum.accumulate(B, axis=1).reshape(-1)
    suf = np.minimum.accumulate(B[:, ::-1], axis=1)[:, ::-1].reshape(-1)
    i = np.arange(n)
    res = np.minimum(suf[i], pre[np.minimum(i + w - 1, len(pre) - 1)])
    return res if forward else res[::-1]


def limiter(x: np.ndarray, ceiling_db: float = -1.0, lookahead: float = 0.005, hold: float = 0.06,
            circular: bool = False) -> np.ndarray:
    """Look-ahead brickwall-ish limiter (gain never above 1, reaches required reduction before peaks)."""
    X2 = as2d(x)
    n = X2.shape[0]
    c = db2a(ceiling_db)
    a = np.max(np.abs(X2), axis=1)
    if a.max() <= c:
        return x
    L = max(2, secs(lookahead)); H = max(1, secs(hold))
    if circular:
        ext = L + H + 4
        a_ext = np.concatenate([a[-ext:], a, a[:ext]])
    else:
        ext = 0
        a_ext = a
    g = np.minimum(1.0, c / np.maximum(a_ext, 1e-12))
    g = _win_min(g, L, forward=True)
    g = _win_min(g, H, forward=False)
    k = np.ones(L) / L
    cs = np.concatenate([[0.0], np.cumsum(g)])
    sm = np.empty_like(g)
    idx = np.arange(len(g))
    lo = np.maximum(0, idx - L + 1)
    sm[:] = (cs[idx + 1] - cs[lo]) / (idx + 1 - lo)
    if circular:
        sm = sm[ext:ext + n]
    y = X2 * sm[:, None]
    # final safety (should be no-op)
    y = np.clip(y, -c, c)
    return y[:, 0] if np.asarray(x).ndim == 1 else y


def glue(x: np.ndarray, thr_db: float, ratio: float = 1.6, win: float = 0.4, smooth: float = 0.35,
         circular: bool = True) -> np.ndarray:
    """Gentle look-ahead RMS compressor (offline, zero-latency, centred windows): reduces the
    loudness of the few loudest moments above thr_db (short-term RMS over `win` s) by ratio."""
    X2 = as2d(x)
    n = X2.shape[0]
    m = np.mean(X2 * X2, axis=1)
    def movavg(v, k):
        k = max(1, k)
        if circular:
            box = np.zeros(n)
            box[:k] = 1.0 / k
            box = np.roll(box, -(k // 2))
            return fftconv(v, box, circular=True)
        pad = np.concatenate([np.full(k, v[0]), v, np.full(k, v[-1])])
        c = np.concatenate([[0.0], np.cumsum(pad)])
        out = (c[k:] - c[:-k]) / k
        return out[k // 2:k // 2 + n]
    env = np.maximum(movavg(m, secs(win)), 1e-20)
    lvl = 10.0 * np.log10(env)
    gr = -np.maximum(0.0, lvl - thr_db) * (1.0 - 1.0 / ratio)
    g = 10.0 ** (movavg(gr, secs(smooth)) / 20.0)
    y = X2 * g[:, None]
    return y[:, 0] if np.asarray(x).ndim == 1 else y


def soft_clip(x: np.ndarray, drive: float = 1.0) -> np.ndarray:
    return np.tanh(drive * x) / np.tanh(drive)


def normalize_rms(x: np.ndarray, target_db: float) -> np.ndarray:
    r = rms(x)
    return x * (db2a(target_db) / r) if r > 0 else x


def normalize_peak(x: np.ndarray, target_db: float) -> np.ndarray:
    p = np.max(np.abs(x))
    return x * (db2a(target_db) / p) if p > 0 else x


def remove_dc(x: np.ndarray, circular: bool = True, fc: float = 18.0) -> np.ndarray:
    y = eq(x, ('hp', fc, 2), circular=circular)
    return y - np.mean(y, axis=0)


# --------------------------------------------------------------------------- resampling
def decimate2(x: np.ndarray) -> np.ndarray:
    """FFT-domain anti-aliased decimation by 2 (input rendered at 2*SR)."""
    X2 = as2d(x)
    n = X2.shape[0] - (X2.shape[0] % 2)
    X2 = X2[:n]
    F = np.fft.rfft(X2, axis=0)
    f = np.fft.rfftfreq(n, 1.0 / (2 * SR))
    keep = n // 4 + 1
    g = mag_lp(f[:keep], 19000.0, 8)
    y = np.fft.irfft(F[:keep] * g[:, None], n // 2, axis=0) * 0.5
    return y[:, 0] if np.asarray(x).ndim == 1 else y


def resample_ratio(x: np.ndarray, ratio: float) -> np.ndarray:
    """Pitch/time change by `ratio` (>1 = higher & shorter) via band-limited FFT interpolation."""
    X2 = as2d(x)
    n = X2.shape[0]
    m = max(2, int(round(n / ratio)))
    F = np.fft.rfft(X2, axis=0)
    k = min(F.shape[0], m // 2 + 1)
    G = np.zeros((m // 2 + 1, X2.shape[1]), dtype=complex)
    G[:k] = F[:k]
    y = np.fft.irfft(G, m, axis=0) * (m / n)
    return y[:, 0] if np.asarray(x).ndim == 1 else y


# --------------------------------------------------------------------------- WAV I/O
def write_wav(path: str, x: np.ndarray, loop: tuple[int, int] | None = None, dither: bool = True,
              seed: int = 7) -> dict:
    """16-bit PCM WAV via the stdlib `wave` module (+ RIFF 'smpl' loop chunk when loop given).
    loop=(start, end) in frames, end EXCLUSIVE (Godot semantics: loop_end == frame count loops
    the whole file).  Returns basic stats of the written data."""
    X2 = as2d(np.asarray(x, dtype=float))
    n, ch = X2.shape
    rng = np.random.default_rng(seed)
    y = X2 * 32767.0
    if dither:
        d = rng.random((n, ch)) - rng.random((n, ch))
        d[X2 == 0.0] = 0.0
        y = y + d
    clipped = int(np.sum(np.abs(y) > 32767.0))
    pcm = np.clip(np.round(y), -32768, 32767).astype('<i2')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if loop is not None:
        _append_smpl(path, int(loop[0]), int(loop[1]))
    return {'frames': n, 'channels': ch, 'clipped_samples': clipped}


def _append_smpl(path: str, start: int, end: int) -> None:
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE'
    period_ns = int(round(1e9 / SR))
    chunk = struct.pack('<4sI9I6I', b'smpl', 60,
                        0, 0, period_ns, 60, 0, 0, 0, 1, 0,   # header, 1 loop
                        0, 0, start, end, 0, 0)                 # id, type=forward, start, end, frac, count=inf
    data += chunk
    struct.pack_into('<I', data, 4, len(data) - 8)
    with open(path, 'wb') as f:
        f.write(data)


def read_wav(path: str):
    """Returns (float array (n, ch), sr, loop or None)."""
    with wave.open(path, 'rb') as w:
        ch = w.getnchannels(); sr = w.getframerate(); sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    assert sw == 2
    x = np.frombuffer(raw, dtype='<i2').astype(float).reshape(-1, ch) / 32768.0
    loop = None
    with open(path, 'rb') as f:
        data = f.read()
    pos = 12
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if cid == b'smpl' and size >= 60:
            vals = struct.unpack_from('<9I6I', data, pos + 8)
            loop = (vals[11], vals[12])
        pos += 8 + size + (size & 1)
    return x, sr, loop
