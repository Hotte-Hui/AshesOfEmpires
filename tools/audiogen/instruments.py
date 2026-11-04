"""instruments.py -- synthesised instruments for the ASHES OF EMPIRES score and SFX.

Techniques (all original, no samples):
* band-limited wavetable oscillators with morphing (bowed-string ensemble, low brass pad),
* additive synthesis with inharmonic partials and two-stage decay (felt / muted piano),
* 2-operator FM rendered at 2x and decimated (celesta-like bars, bells),
* block-vectorised Karplus-Strong (plucked / pizzicato strings),
* modal synthesis (damped sinusoid banks) for metal, wood and bells.
Every voice returns a float array (mono (n,) or stereo (n, 2)) at dsp.SR.
"""
from __future__ import annotations

import numpy as np

from dsp import (SR, TAU, secs, midi_hz, pan2, smoothstep, eq, shaped_noise, mag_bp, mag_lp,
                 decimate2, filt, fftconv, rms)

TABLE = 8192
_CTRL_SR = 200.0


# --------------------------------------------------------------------------- helpers
def ctrl_noise(n: int, rate_hz: float, rng: np.random.Generator) -> np.ndarray:
    """Cheap smooth random curve (zero mean, ~unit std) built at a 200 Hz control rate."""
    m = int(n / SR * _CTRL_SR) + 8
    k = max(4, int(m / _CTRL_SR * rate_hz) + 2)
    pts = rng.standard_normal(k)
    xs = np.linspace(0, m - 1, k)
    c = np.interp(np.arange(m), xs, pts)
    # smooth the linear segments with a short moving average
    w = max(1, int(_CTRL_SR / max(rate_hz, 0.1) / 2))
    if w > 1:
        c = np.convolve(np.pad(c, (w, w), mode='edge'), np.ones(w) / w, mode='same')[w:-w]
    c = c - c.mean()
    s = c.std()
    c = c / s if s > 0 else c
    return np.interp(np.arange(n) * (_CTRL_SR / SR), np.arange(m), c)


def make_table(amps, phases=None, size: int = TABLE) -> np.ndarray:
    """Single-cycle table whose k-th harmonic (k = 1..K) has amplitude amps[k-1] (sine phase)."""
    amps = np.asarray(amps, dtype=float)
    K = min(len(amps), size // 2 - 1)
    spec = np.zeros(size // 2 + 1, dtype=complex)
    ph = np.zeros(K) if phases is None else np.asarray(phases)[:K]
    spec[1:K + 1] = (size / 2.0) * amps[:K] * np.exp(1j * (ph - np.pi / 2))
    return np.fft.irfft(spec, size)


def wt_read(table: np.ndarray, phase: np.ndarray) -> np.ndarray:
    size = table.shape[-1]
    p = np.mod(phase, 1.0) * size
    j0 = p.astype(np.int64) % size
    fr = p - np.floor(p)
    j1 = (j0 + 1) % size
    return table[j0] + fr * (table[j1] - table[j0])


def wt_morph(tables: np.ndarray, phase: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Read a stack of tables (M, size) and crossfade by pos in [0, M-1] per sample."""
    M, size = tables.shape
    p = np.mod(phase, 1.0) * size
    j0 = p.astype(np.int64) % size
    fr = p - np.floor(p)
    j1 = (j0 + 1) % size
    pos = np.clip(pos, 0.0, M - 1.0 - 1e-9)
    i0 = pos.astype(np.int64)
    w = pos - i0
    a = tables[i0, j0] + fr * (tables[i0, j1] - tables[i0, j0])
    b = tables[i0 + 1, j0] + fr * (tables[i0 + 1, j1] - tables[i0 + 1, j0])
    return a + w * (b - a)


def adsr(n: int, attack: float, hold: float, release: float, curve: float = 1.0) -> np.ndarray:
    """Smooth attack (s-curve), sustain until `hold` seconds, exponential release (t60=release)."""
    t = np.arange(n) / SR
    a = smoothstep(t / max(attack, 1e-4)) ** curve
    r = np.where(t < hold, 1.0, np.exp(-6.9078 * (t - hold) / max(release, 1e-3)))
    return a * r


# --------------------------------------------------------------------------- bowed strings
def string_note(midi: float, dur: float, vel: float = 0.6, attack: float = 0.9, release: float = 2.2,
                voices: int = 5, bright: float = 0.5, seed: int = 0, pan: float = 0.0, spread: float = 0.6,
                vib: float = 9.0, vib_rate: float = 5.2, detune: float = 4.0, bow_noise: float = 0.035,
                swell: float = 0.0, harmonic: bool = False) -> np.ndarray:
    """Bowed-string ensemble note (stereo).  `dur` = bow time; release added after.
    swell > 0 grows the level by that factor across the bow (crescendo), < 0 diminuendo.
    harmonic=True: flautando / harmonic-like (almost sine, slow vibrato) for cold high lines."""
    rng = np.random.default_rng(seed)
    f0 = float(midi_hz(midi))
    n = secs(dur + release)
    t = np.arange(n) / SR
    K = max(1, int(15000.0 / (f0 * 1.012)))
    k = np.arange(1, K + 1, dtype=float)
    if harmonic:
        def amps(fc):
            return np.where(k == 1, 1.0, 0.06 / k ** 2) / np.sqrt(1 + (k * f0 / fc) ** 4)
    else:
        def amps(fc):
            return (1.0 / k) / np.sqrt(1.0 + (k * f0 / fc) ** 3)
    fcs = [620 + 600 * bright, 1300 + 1600 * bright, 2300 + 3000 * bright]
    tables = np.stack([make_table(amps(fc)) for fc in fcs])
    env = adsr(n, attack, dur, release)
    if swell:
        env *= 1.0 + swell * smoothstep(t / max(dur, 1e-3))
    loud = np.clip(vel * env / max(1.0, 1.0 + swell), 0.0, 1.0)
    pos = 2.0 * np.clip(0.25 + 0.9 * loud, 0, 1)
    out = np.zeros((n, 2))
    for v in range(voices):
        det = rng.normal(0.0, detune)
        vr = vib_rate * (1.0 + rng.normal(0.0, 0.07))
        vd = vib * (0.6 + 0.8 * rng.random())
        vdel = attack * 0.5 + rng.uniform(0.1, 0.6)
        venv = smoothstep((t - vdel) / 0.9)
        drift = 2.2 * ctrl_noise(n, 0.6, rng)
        cents = det + drift + vd * venv * np.sin(TAU * vr * t + rng.uniform(0, TAU))
        freq = f0 * np.exp2(cents / 1200.0)
        ph = np.cumsum(freq) / SR + rng.random()
        s = wt_morph(tables, ph, pos)
        jit = 1.0 + 0.07 * ctrl_noise(n, 1.8, rng)
        p = float(np.clip(pan + spread * rng.uniform(-0.5, 0.5), -1, 1))
        out += pan2(s * jit, p)
    out *= (env * vel / np.sqrt(voices))[:, None]
    if bow_noise > 0:
        bow_noise *= float(np.clip((f0 / 260.0) ** 0.5, 0.35, 1.0))   # low strings: less audible scratch
        nz = shaped_noise(n, rng, lambda f: mag_bp(f, max(400.0, 3 * f0), 4200.0, 4), ch=1)
        burst = np.exp(-np.maximum(t - 0.02, 0) / 0.18) * smoothstep(t / 0.03)
        nenv = (0.35 * burst + 0.65 * env) * vel * bow_noise * (1.0 + 0.4 * ctrl_noise(n, 6.0, rng))
        out += pan2(nz * nenv, pan)
    return out


# --------------------------------------------------------------------------- low brass pad
def brass_note(midi: float, dur: float, vel: float = 0.5, attack: float = 0.4, release: float = 1.4,
               players: int = 3, seed: int = 0, pan: float = 0.0, spread: float = 0.35,
               bright: float = 0.5, scoop: float = 14.0, formant: float = 480.0,
               swell: float = 0.0) -> np.ndarray:
    """Soft low-brass ensemble note (horn / trombone-like, muted and dark).  Brightness follows
    loudness (more harmonics when louder), pitch scoops in from below."""
    rng = np.random.default_rng(seed)
    f0 = float(midi_hz(midi))
    n = secs(dur + release)
    t = np.arange(n) / SR
    K = max(1, int(11000.0 / (f0 * 1.01)))
    k = np.arange(1, K + 1, dtype=float)
    fk = k * f0
    form = 1.0 + 1.4 * np.exp(-0.5 * (np.log2(fk / formant) / 0.55) ** 2)
    tabs = []
    for b in (0.0, 0.33, 0.66, 1.0):
        kb = 0.9 + (2.0 + 6.0 * bright) * b
        a = np.exp(-(k - 1) / kb) * form / np.sqrt(1.0 + (fk / (1500 + 2500 * b)) ** 4)
        tabs.append(make_table(a))
    tables = np.stack(tabs)
    env = adsr(n, attack, dur, release, curve=1.3)
    if swell:
        env *= 1.0 + swell * smoothstep(t / max(dur, 1e-3)) ** 1.5
    loud = np.clip(vel * env / max(1.0, 1.0 + swell), 0, 1)
    pos = 3.0 * np.clip(loud ** 1.2, 0, 1)
    out = np.zeros((n, 2))
    for pl in range(players):
        det = rng.normal(0.0, 3.0)
        sc = -scoop * (0.6 + 0.8 * rng.random()) * np.exp(-t / (0.05 + 0.05 * rng.random()))
        late = smoothstep((t - 1.2) / 1.5)
        vibr = 2.5 * late * np.sin(TAU * (4.4 + 0.5 * rng.random()) * t + rng.uniform(0, TAU))
        cents = det + sc + vibr + 1.5 * ctrl_noise(n, 0.5, rng)
        freq = f0 * np.exp2(cents / 1200.0)
        ph = np.cumsum(freq) / SR + rng.random()
        s = wt_morph(tables, ph, pos) * (1.0 + 0.05 * ctrl_noise(n, 1.5, rng))
        p = float(np.clip(pan + spread * rng.uniform(-0.5, 0.5), -1, 1))
        out += pan2(s, p)
    out *= (env * vel / np.sqrt(players))[:, None]
    # breath
    nz = shaped_noise(n, rng, lambda f: mag_bp(f, 250.0, 1500.0, 4), ch=1)
    out += pan2(nz * env * vel * 0.006, pan)
    return out


# --------------------------------------------------------------------------- felt / muted piano
def piano_note(midi: float, vel: float = 0.6, hold: float = 1.0, felt: float = 0.6, seed: int = 0,
               pan: float = 0.0, decay: float = 1.0, bright: float = 0.5, pedal: bool = False,
               max_len: float | None = None) -> np.ndarray:
    """Additive piano: inharmonic partials (B), 1-3 detuned strings, per-partial two-stage
    decay, strike-position comb, hammer/felt thump, damper release after `hold` seconds."""
    rng = np.random.default_rng(seed)
    f0 = float(midi_hz(midi))
    B = float(np.clip(0.00035 * (f0 / 262.0) ** 1.1, 0.00004, 0.004))
    T1 = float(np.clip(decay * 10.0 * (262.0 / f0) ** 0.6, 0.6, 24.0))
    damper = f0 < 1400.0 and not pedal
    rel = 0.32 if damper else T1
    total = (hold + rel * 1.6) if damper else T1 * 1.05
    if max_len:
        total = min(total, max_len)
    n = secs(total)
    t = np.arange(n) / SR
    fh = (700.0 + 4200.0 * vel * bright) * (1.0 - 0.55 * felt)
    x0 = 0.118 + 0.01 * rng.random()          # strike position (fraction of the string)
    strings = 1 if f0 < 70 else (2 if f0 < 140 else 3)
    dets = rng.uniform(0.25, 1.1, strings) * rng.choice([-1, 1], strings)
    if strings == 1:
        dets[:] = 0.0
    out = np.zeros(n)
    # damper envelope
    if damper:
        dmp = np.where(t < hold, 1.0, np.exp(-6.9078 * (t - hold) / rel))
    else:
        dmp = np.ones(n)
    a1 = None
    nmax = int(min(48, 16000.0 / f0))
    for p in range(1, nmax + 1):
        fp = p * f0 * np.sqrt(1.0 + B * p * p)
        if fp > 15000.0:
            break
        amp = p ** -(0.9 + 1.1 * felt) / (1.0 + (fp / fh) ** 2)
        amp *= 0.25 + 0.75 * abs(np.sin(np.pi * p * x0))
        if a1 is None:
            a1 = amp
        if amp < a1 * 1e-3:
            continue
        T = T1 / (1.0 + (fp / 1800.0) ** 1.25 + 0.06 * (p - 1))
        w2 = 0.28
        env = (1 - w2) * np.exp(-6.9078 * t / (T * 0.38)) + w2 * np.exp(-6.9078 * t / T)
        acc = np.zeros(n)
        for s in range(strings):
            fs = fp * 2.0 ** (dets[s] / 1200.0)
            acc += np.sin(TAU * fs * t + rng.uniform(0, TAU))
        out += amp * env * acc / strings
    out *= dmp
    # hammer / felt thump and contact noise
    kn = secs(0.03)
    tk = np.arange(kn) / SR
    thump = np.sin(TAU * (90.0 + 0.3 * f0) * tk) * np.exp(-tk / 0.008) * (0.05 + 0.08 * felt)
    out[:kn] += thump * vel
    hn = secs(0.012)
    hz = rng.standard_normal(hn) * np.exp(-np.arange(hn) / SR / 0.003)
    hz = filt(hz, 'lp', min(9000.0, fh * 2.5), 0.7)
    out[:hn] += hz * 0.025 * vel
    # smooth onset (hammer contact ~1-3 ms depending on felt)
    on = secs(0.0008 + 0.0025 * felt)
    out[:on] *= smoothstep(np.arange(on) / on)
    end = secs(0.02)
    out[-end:] *= np.linspace(1, 0, end)
    return pan2(out * vel, pan)


# --------------------------------------------------------------------------- celesta (FM)
def celesta_note(midi: float, vel: float = 0.6, seed: int = 0, pan: float = 0.0, bright: float = 0.5,
                 t60: float | None = None, hold: float | None = None) -> np.ndarray:
    """Celesta-like struck bar: FM pair (c=1, m=3.5, decaying index) for the metallic attack,
    harmonic FM pair (c=4, m=1) for the tine, sine body.  Rendered at 2x SR, decimated."""
    rng = np.random.default_rng(seed)
    f0 = float(midi_hz(midi))
    T = t60 if t60 else float(np.clip(2.4 * (523.0 / f0) ** 0.45, 0.9, 4.0))
    dur = T * 1.05 if hold is None else min(T * 1.05, hold + 0.45)
    sr2 = 2 * SR
    n = int(dur * sr2)
    t = np.arange(n) / sr2
    amp = np.exp(-6.9078 * t / T)
    if hold is not None:
        amp *= np.where(t < hold, 1.0, np.exp(-6.9078 * (t - hold) / 0.4))
    I1 = (0.35 + 0.9 * vel * bright) * np.exp(-t / 0.07)
    body = np.sin(TAU * f0 * t + I1 * np.sin(TAU * 3.5 * f0 * t + rng.uniform(0, TAU)))
    I2 = 0.55 * np.exp(-t / 0.05)
    tine = np.sin(TAU * 4.0 * f0 * t + I2 * np.sin(TAU * f0 * t)) * np.exp(-6.9078 * t / (0.32 * (523.0 / f0) ** 0.3))
    glint = np.sin(TAU * 6.27 * f0 * t) * np.exp(-6.9078 * t / 0.09) if 6.27 * f0 < 18000 else 0.0
    y = amp * body + (0.16 + 0.1 * bright) * vel * tine + 0.05 * vel * glint
    on = int(0.0012 * sr2)
    y[:on] *= smoothstep(np.arange(on) / on)
    y[-int(0.02 * sr2):] *= np.linspace(1, 0, int(0.02 * sr2))
    y = decimate2(y)
    return pan2(y * vel, pan)


# --------------------------------------------------------------------------- Karplus-Strong
def ks_pluck(midi: float, vel: float = 0.7, t60: float = 2.5, bright: float = 0.5, seed: int = 0,
             pan: float = 0.0, pick: float = 0.22, dur: float | None = None, body: bool = True) -> np.ndarray:
    """Karplus-Strong plucked string, block-vectorised (block = loop delay).  Loop filter =
    two-tap lowpass (brightness) convolved with linear fractional delay (tuning)."""
    rng = np.random.default_rng(seed)
    f0 = float(midi_hz(midi))
    P = SR / f0
    s = 0.5 - 0.42 * float(np.clip(bright, 0.0, 1.0))      # 0.08 (bright) .. 0.5 (dark)
    Dp = P - s
    D = int(np.floor(Dp))
    fr = Dp - D
    c0 = (1 - s) * (1 - fr)
    c1 = (1 - s) * fr + s * (1 - fr)
    c2 = s * fr
    g = 10.0 ** (-3.0 / (f0 * t60))
    dur = dur if dur else t60 * 1.1
    N = secs(dur)
    L = max(2, int(round(P)))
    exc = rng.uniform(-1, 1, 4 * L)
    # soft plectrum / finger: band-limit the burst (no white full-band click)
    exc = eq(exc, ('lp', 900.0 + 3500.0 * bright * vel, 2), circular=True)[:L]
    exc = (exc - exc.mean()) * np.hanning(L + 2)[1:-1] ** 0.5
    exc /= max(np.max(np.abs(exc)), 1e-9)
    pp = max(1, int(round(pick * L)))
    exc = exc - np.concatenate([np.zeros(pp), exc[:-pp]])
    o = D + 3
    y = np.zeros(N + o)
    e = np.zeros(N)
    e[:min(L, N)] = exc[:min(L, N)]
    for i in range(0, N, D):
        j = min(i + D, N)
        a = o + i
        m = j - i
        y[a:a + m] = e[i:j] + g * (c0 * y[a - D:a - D + m] + c1 * y[a - D - 1:a - D - 1 + m]
                                   + c2 * y[a - D - 2:a - D - 2 + m])
    out = y[o:]
    if body:
        out = eq(out, ('hp', 50, 2), ('bell', 220, 3.0, 1.2), ('bell', 520, 2.0, 1.0),
                 ('bell', 2600, -3.0, 1.5), ('lp', 5000, 3), circular=False)
    on = secs(0.0015)
    out[:on] *= smoothstep(np.arange(on) / on)
    out[-secs(0.03):] *= np.linspace(1, 0, secs(0.03))
    r = np.max(np.abs(out)) or 1.0
    return pan2(out / r * vel, pan)


# --------------------------------------------------------------------------- modal / impacts
def modal(modes, dur: float, seed: int = 0, attack: float = 0.0) -> np.ndarray:
    """Damped sinusoid bank. modes: [(freq_hz, amp, t60_s)].  Mono."""
    rng = np.random.default_rng(seed)
    n = secs(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a, T in modes:
        if f <= 0 or f >= 0.45 * SR or a == 0:
            continue
        m = min(n, secs(T * 1.4) + 2)
        out[:m] += a * np.exp(-6.9078 * t[:m] / T) * np.sin(TAU * f * t[:m] + rng.uniform(-0.3, 0.3))
    if attack > 0:
        k = secs(attack)
        out[:k] *= smoothstep(np.arange(k) / k)
    return out


def noise_burst(dur: float, rng: np.random.Generator, lo: float, hi: float, decay: float,
                attack: float = 0.0005) -> np.ndarray:
    """Band-limited noise burst with exponential decay (t60 = decay)."""
    n = max(8, secs(dur))
    t = np.arange(n) / SR
    z = rng.standard_normal(n)
    z = eq(z, ('hp', lo, 2), ('lp', hi, 2), circular=False)
    z /= max(rms(z), 1e-9)
    env = np.exp(-6.9078 * t / decay) * smoothstep(t / max(attack, 1e-5))
    return z * env


def impact(rng: np.random.Generator, modes, dur: float, hard: float = 0.5, noise_lo: float = 300.0,
           noise_hi: float = 8000.0, noise_amt: float = 0.3, noise_decay: float = 0.015) -> np.ndarray:
    """Generic struck object: modal ring + contact noise.  hard (0..1) brightens the strike."""
    fh = 1500.0 + 9000.0 * hard
    ms = [(f, a / (1.0 + (f / fh) ** 2), T) for (f, a, T) in modes]
    y = modal(ms, dur, seed=int(rng.integers(1 << 30)))
    y /= max(np.max(np.abs(y)), 1e-9)
    nb = noise_burst(min(dur, noise_decay * 3 + 0.01), rng, noise_lo, noise_hi * (0.5 + hard), noise_decay)
    nb /= max(np.max(np.abs(nb)), 1e-9)
    y[:len(nb)] += noise_amt * nb
    return y


def random_modes(rng: np.random.Generator, f_lo: float, f_hi: float, count: int, t60_lo: float,
                 t60_hi: float, tilt: float = 0.5):
    """Inharmonic mode set (log-uniform freqs), amplitudes falling with frequency."""
    fs = np.exp(rng.uniform(np.log(f_lo), np.log(f_hi), count))
    fs.sort()
    out = []
    for f in fs:
        a = (f / f_lo) ** (-tilt) * rng.uniform(0.4, 1.0)
        T = np.exp(rng.uniform(np.log(t60_lo), np.log(t60_hi))) * (f_lo / f) ** 0.3
        out.append((float(f), float(a), float(T)))
    return out


def bell_modes(f1: float, kind: str = 'tram'):
    """Partial sets (freq, amp, t60).  'tram' = small dome gong (strongly inharmonic)."""
    if kind == 'tram':
        r = [(1.0, 1.0, 2.6), (1.51, 0.55, 1.9), (2.13, 0.42, 1.4), (2.68, 0.30, 1.1), (3.36, 0.22, 0.8),
             (4.07, 0.16, 0.55), (4.95, 0.10, 0.4), (6.1, 0.06, 0.25)]
    else:
        r = [(0.5, 0.35, 3.5), (1.0, 1.0, 2.8), (1.19, 0.6, 2.2), (1.5, 0.45, 1.7), (2.0, 0.5, 1.4),
             (2.51, 0.25, 0.9), (3.0, 0.18, 0.7), (4.1, 0.08, 0.4)]
    return [(f1 * a, b, c) for (a, b, c) in r]
