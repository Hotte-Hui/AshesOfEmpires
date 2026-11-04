"""cine_a1m1_sfx -- original synthesized sound effects for the A1 -> M1 transition cinematic.

Self-contained (numpy + stdlib wave), deterministic (seeds from crc32 of names), 44.1 kHz / 16-bit.
Writes assets/audio/sfx/cine_a1m1_*.wav (owner: trans-a1m1). Levels follow the existing SFX set
(peaks -6 .. -12 dBFS).

  cine_a1m1_couple        buffers meet + coupling chain + yard reverb                (mono, 1.8 s)
  cine_a1m1_whistle       deep chord steam whistle, near                             (stereo, 2.6 s)
  cine_a1m1_whistle_far   the same whistle far away (low-passed, long tail) = sound bridge (stereo, 3.6 s)
  cine_a1m1_chuff         one exhaust beat of a starting steam locomotive            (mono, 0.8 s)
  cine_a1m1_hiss          cylinder cocks venting steam                               (stereo, 2.6 s)
  cine_a1m1_depart        slack running out through the couplings + rail joints     (stereo, 6.0 s)
  cine_a1m1_stamp         rubber stamp: short swish, wooden knock, rubber squish     (mono, 0.9 s)
  cine_a1m1_swell         soft string-like pad under the stamp and the dissolve      (stereo, 9.0 s)
  cine_a1m1_tram_arrive   tram rolling in, brake squeal, stop                        (stereo, 4.0 s)
  cine_a1m1_tram_depart   tram motor whine rising, rumble receding                   (stereo, 4.5 s)
  cine_a1m1_door          heavy portal door: latch, swing, closing thud in a hall    (mono, 1.8 s)
  cine_a1m1_pigeons       pigeons taking off (wing flutter)                          (stereo, 1.4 s)
Run:  py -3 -P tools/audiogen/cine_a1m1_sfx.py
"""
from __future__ import annotations

import os
import wave
import zlib

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def rng(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF)


def t_axis(sec: float) -> np.ndarray:
    return np.arange(int(round(sec * SR))) / SR


def env_adsr(n: int, a: float, d: float, s: float, r: float, sus: float = 0.0) -> np.ndarray:
    """a/d/r in seconds, s = sustain level, sus = sustain duration (s)."""
    e = np.zeros(n)
    ia, idd, isu, ir = (int(a * SR), int(d * SR), int(sus * SR), int(r * SR))
    k = 0
    seg = [(ia, 0.0, 1.0), (idd, 1.0, s), (isu, s, s), (ir, s, 0.0)]
    for ln, v0, v1 in seg:
        ln = max(0, min(ln, n - k))
        if ln:
            e[k:k + ln] = np.linspace(v0, v1, ln, endpoint=False)
        k += ln
    return e


def bandpass(x: np.ndarray, lo: float, hi: float, soft: float = 0.15) -> np.ndarray:
    """Zero-phase FFT band-pass with smooth (raised-cosine) skirts."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo > 0:
        w = max(1.0, lo * soft)
        g *= np.clip((f - (lo - w)) / (2 * w), 0, 1)
    if hi < SR / 2:
        w = max(1.0, hi * soft)
        g *= np.clip(((hi + w) - f) / (2 * w), 0, 1)
    return np.fft.irfft(X * g, n)


def lowpass(x, hi, soft=0.3):
    return bandpass(x, 0, hi, soft)


def highpass(x, lo, soft=0.3):
    return bandpass(x, lo, SR / 2, soft)


def reverb(x: np.ndarray, seconds: float, mix: float, name: str, damp: float = 3000.0, stereo: bool = True):
    """Convolution with generated, exponentially decaying, low-passed noise (one IR per channel)."""
    r = rng('rv' + name)
    n_ir = int(seconds * SR)
    t = np.arange(n_ir) / SR
    outs = []
    for ch in range(2 if stereo else 1):
        ir = r.standard_normal(n_ir) * np.exp(-6.9 * t / seconds)
        ir = lowpass(ir, damp)
        ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        n = len(x) + n_ir
        wet = np.fft.irfft(np.fft.rfft(x, n * 2) * np.fft.rfft(ir, n * 2), n * 2)[:len(x) + n_ir]
        dry = np.concatenate([x, np.zeros(n_ir)])
        outs.append(dry * (1 - mix) + wet * mix)
    return np.stack(outs, 1) if stereo else outs[0]


def fit(x: np.ndarray, sec: float) -> np.ndarray:
    n = int(sec * SR)
    if len(x) >= n:
        x = x[:n].copy()
    else:
        pad = np.zeros((n - len(x),) + x.shape[1:])
        x = np.concatenate([x, pad])
    fade = int(0.03 * SR)
    ramp = np.linspace(1, 0, fade)
    if x.ndim == 2:
        x[-fade:] *= ramp[:, None]
    else:
        x[-fade:] *= ramp
    return x


def norm(x: np.ndarray, peak_db: float) -> np.ndarray:
    p = np.abs(x).max() + 1e-12
    return x / p * (10 ** (peak_db / 20))


def write(name: str, x: np.ndarray):
    os.makedirs(OUT, exist_ok=True)
    x = np.clip(x, -1, 1)
    ch = 1 if x.ndim == 1 else x.shape[1]
    data = (x * 32767).astype('<i2').tobytes()
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    return {'file': 'assets/audio/sfx/%s.wav' % name, 'seconds': round(len(x) / SR, 2), 'channels': ch}


# =========================================================================== sounds
def couple():
    r = rng('couple')
    t = t_axis(1.0)
    n = len(t)
    thump = np.sin(2 * np.pi * (70 - 25 * t) * t) * np.exp(-t * 18)
    thump += lowpass(r.standard_normal(n), 400) * np.exp(-t * 40) * 0.6
    clank = np.zeros(n)
    for f, a, dec in ((412, 1.0, 9), (1127, 0.7, 14), (2213, 0.45, 20), (3391, 0.3, 26), (5120, 0.15, 35)):
        clank += a * np.sin(2 * np.pi * f * t + r.uniform(0, 6)) * np.exp(-t * dec)
    clank *= 0.5
    chain = np.zeros(n)
    for k in range(9):
        t0 = 0.05 + r.uniform(0, 0.42)
        i0 = int(t0 * SR)
        ln = int(0.03 * SR)
        burst = bandpass(r.standard_normal(ln), 1800, 5200) * np.exp(-np.arange(ln) / SR * 120)
        chain[i0:i0 + ln] += burst[:max(0, min(ln, n - i0))] * r.uniform(0.2, 0.5)
    x = thump * 0.9 + clank + chain
    x = reverb(x, 1.3, 0.35, 'couple', damp=2500, stereo=False)
    return write('cine_a1m1_couple', norm(fit(x, 1.8), -6.0))


def _whistle_dry(sec: float):
    r = rng('whistle')
    t = t_axis(sec)
    n = len(t)
    pitch_env = 1 - 0.05 * np.exp(-t * 7)                       # slight upward slide as steam pressure builds
    amp = env_adsr(n, 0.12, 0.2, 0.85, 0.45, sus=sec - 0.85)
    x = np.zeros(n)
    for f0, a in ((233.0, 1.0), (277.0, 0.8), (349.0, 0.65)):   # deep three-chime chord (B-flat minor-ish)
        ph = 2 * np.pi * np.cumsum(f0 * pitch_env * (1 + 0.002 * np.sin(2 * np.pi * 5.1 * t))) / SR
        tone = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph) + 0.08 * np.sin(4 * ph)
        x += a * tone
    breath = bandpass(r.standard_normal(n), 180, 1600) * 0.35
    x = (x * 0.3 + breath) * amp
    return x


def whistle():
    x = _whistle_dry(2.0)
    x = reverb(x, 1.6, 0.3, 'whistle', damp=4000)
    return write('cine_a1m1_whistle', norm(fit(x, 2.6), -8.0))


def whistle_far():
    x = _whistle_dry(2.4)
    x = lowpass(x, 1100) * 0.8 + highpass(x, 3000) * 0.0
    x = reverb(x, 3.0, 0.6, 'whistle_far', damp=1500)
    return write('cine_a1m1_whistle_far', norm(fit(x, 3.6), -14.0))


def chuff():
    r = rng('chuff')
    t = t_axis(0.8)
    n = len(t)
    burst = bandpass(r.standard_normal(n), 120, 2400) * (np.exp(-t * 9) * (1 - np.exp(-t * 300)))
    low = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 14) * 0.7
    x = burst + low
    x = reverb(x, 0.9, 0.25, 'chuff', damp=2000, stereo=False)
    return write('cine_a1m1_chuff', norm(fit(x, 0.8), -7.0))


def hiss():
    r = rng('hiss')
    t = t_axis(2.6)
    n = len(t)
    e = env_adsr(n, 0.04, 0.5, 0.45, 1.2, sus=0.8)
    x = np.stack([highpass(r.standard_normal(n), 2200) * e, highpass(r.standard_normal(n), 2000) * e], 1)
    x *= (1 + 0.15 * np.sin(2 * np.pi * 7 * t))[:, None]
    return write('cine_a1m1_hiss', norm(fit(x, 2.6), -12.0))


def depart():
    r = rng('depart')
    sec = 6.0
    t = t_axis(sec)
    n = len(t)
    x = np.zeros(n)
    # slack running out through the couplings: clanks travelling away down the train
    for k in range(5):
        t0 = 0.15 + k * 0.32
        i0 = int(t0 * SR)
        ln = int(0.5 * SR)
        tt = np.arange(ln) / SR
        c = sum(a * np.sin(2 * np.pi * f * tt + r.uniform(0, 6)) * np.exp(-tt * d)
                for f, a, d in ((380, 1.0, 12), (1040, 0.6, 18), (2090, 0.35, 26)))
        c += lowpass(r.standard_normal(ln), 300) * np.exp(-tt * 30) * 0.8
        g = 0.9 * (0.72 ** k)
        x[i0:i0 + ln] += c[:max(0, min(ln, n - i0))] * g
    # wheels over rail joints: clack pairs accelerating
    tj, gap = 1.8, 1.1
    while tj < sec - 0.2:
        for dt in (0.0, 0.12 * max(0.35, gap)):
            i0 = int((tj + dt) * SR)
            ln = int(0.06 * SR)
            k = bandpass(r.standard_normal(ln), 600, 4000) * np.exp(-np.arange(ln) / SR * 90)
            x[i0:i0 + ln] += k[:max(0, min(ln, n - i0))] * 0.35
        tj += gap
        gap = max(0.32, gap * 0.82)
    rumble = lowpass(r.standard_normal(n), 140) * np.clip((t - 1.0) / 4.0, 0, 1) * 0.5
    x += rumble
    x = reverb(x, 1.4, 0.3, 'depart', damp=2200)
    return write('cine_a1m1_depart', norm(fit(x, sec), -9.0))


def stamp():
    r = rng('stamp')
    t = t_axis(0.9)
    n = len(t)
    x = np.zeros(n)
    sw = int(0.12 * SR)                                         # swish of the hand coming down
    x[:sw] += bandpass(r.standard_normal(sw), 800, 5000) * np.linspace(0, 1, sw) ** 2 * 0.25
    i0 = sw
    ln = n - i0
    tt = np.arange(ln) / SR
    knock = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in ((180, 1.0, 30), (420, 0.6, 45),
                                                                                    (960, 0.3, 60)))
    knock += lowpass(r.standard_normal(ln), 900) * np.exp(-tt * 70) * 0.8
    squish = bandpass(r.standard_normal(ln), 300, 1800) * np.exp(-tt * 25) * 0.15
    x[i0:] += knock + squish
    x = reverb(x, 0.5, 0.18, 'stamp', damp=3000, stereo=False)
    return write('cine_a1m1_stamp', norm(fit(x, 0.9), -5.0))


def swell():
    r = rng('swell')
    sec = 9.0
    t = t_axis(sec)
    n = len(t)
    x = np.zeros((n, 2))
    notes = [73.42, 110.0, 146.83, 164.81, 220.0]                # D2 A2 D3 E3 A3 (open, unresolved)
    amp = np.clip(t / 3.5, 0, 1) ** 1.5 * np.clip((sec - t) / 2.5, 0, 1)
    for i, f in enumerate(notes):
        for ch in range(2):
            det = 1 + (ch * 2 - 1) * 0.0025 * (i + 1)
            ph = 2 * np.pi * f * det * t + r.uniform(0, 6)
            saw = sum(np.sin(k * ph) / k for k in range(1, 9))
            x[:, ch] += saw * (0.5 if i < 2 else 0.35)
    for ch in range(2):
        x[:, ch] = lowpass(x[:, ch], 900 + 400 * ch)
    x *= amp[:, None] * (1 + 0.08 * np.sin(2 * np.pi * 0.23 * t))[:, None]
    wet = reverb(x[:, 0], 2.5, 0.45, 'swell', damp=1800)
    out = fit(wet, sec)
    return write('cine_a1m1_swell', norm(out, -14.0))


def _tram_body(sec, speed_fn, name):
    r = rng(name)
    t = t_axis(sec)
    n = len(t)
    v = speed_fn(t)
    rumble = lowpass(r.standard_normal(n), 220) * (0.4 + 0.6 * v)
    whine_f = 320 + 900 * v
    whine = np.sin(2 * np.pi * np.cumsum(whine_f) / SR) * 0.12 * v
    joints = np.zeros(n)
    pos = 0.0
    for i in range(n):
        pos += v[i] / SR * 3.2
        if pos >= 1.0:
            pos -= 1.0
            ln = min(int(0.05 * SR), n - i)
            joints[i:i + ln] += bandpass(r.standard_normal(ln), 500, 3500)[:ln] * np.exp(-np.arange(ln) / SR * 80) * 0.5
    x = rumble + whine + joints
    return x, t, v


def tram_arrive():
    sec = 4.0
    x, t, v = _tram_body(sec, lambda t: np.clip(1 - t / 3.2, 0, 1) ** 0.8, 'tram_arrive')
    r = rng('squeal')
    sq = np.sin(2 * np.pi * np.cumsum(2400 + 300 * np.sin(2 * np.pi * 3 * t)) / SR)
    sq *= np.clip((t - 2.0) / 0.4, 0, 1) * np.clip((3.3 - t) / 0.3, 0, 1) * 0.12
    x = x + sq + bandpass(r.standard_normal(len(t)), 1500, 6000) * np.exp(-np.abs(t - 3.4) * 6) * 0.15
    vol = np.clip(0.3 + t / 2.5, 0, 1)                           # approaching
    st = np.stack([x * vol * np.clip(1.2 - t / 4, 0.4, 1), x * vol * np.clip(0.4 + t / 4, 0.4, 1)], 1)
    st = np.stack([reverb(st[:, 0], 1.0, 0.25, 'ta0', stereo=False)[:len(t)],
                   reverb(st[:, 1], 1.0, 0.25, 'ta1', stereo=False)[:len(t)]], 1)
    return write('cine_a1m1_tram_arrive', norm(fit(st, sec), -10.0))


def tram_depart():
    sec = 4.5
    x, t, v = _tram_body(sec, lambda t: np.clip(t / 3.0, 0, 1) ** 1.2, 'tram_depart')
    vol = np.clip(1.3 - t / 4.0, 0.15, 1)                         # receding to the left
    st = np.stack([x * vol * np.clip(0.5 + t / 3, 0.5, 1.1), x * vol * np.clip(1.0 - t / 4, 0.2, 1)], 1)
    st = np.stack([reverb(st[:, 0], 1.0, 0.25, 'td0', stereo=False)[:len(t)],
                   reverb(st[:, 1], 1.0, 0.25, 'td1', stereo=False)[:len(t)]], 1)
    return write('cine_a1m1_tram_depart', norm(fit(st, sec), -10.0))


def door():
    r = rng('door')
    t = t_axis(1.8)
    n = len(t)
    x = np.zeros(n)
    ln = int(0.04 * SR)
    x[:ln] += bandpass(r.standard_normal(ln), 1500, 6000) * np.exp(-np.arange(ln) / SR * 100) * 0.4  # latch
    cr0, cr1 = int(0.1 * SR), int(0.7 * SR)
    tt = np.arange(cr1 - cr0) / SR
    creak = np.sin(2 * np.pi * np.cumsum(260 + 60 * np.sin(2 * np.pi * 1.7 * tt)) / SR) * 0.08
    creak *= np.sin(np.pi * tt / tt[-1])
    x[cr0:cr1] += creak
    i0 = int(0.95 * SR)
    tt = np.arange(n - i0) / SR
    thud = np.sin(2 * np.pi * 62 * tt) * np.exp(-tt * 16) + lowpass(r.standard_normal(n - i0), 500) * np.exp(-tt * 30) * 0.7
    x[i0:] += thud
    x = reverb(x, 1.6, 0.4, 'door', damp=2400, stereo=False)
    return write('cine_a1m1_door', norm(fit(x, 1.8), -8.0))


def pigeons():
    r = rng('pigeons')
    t = t_axis(1.4)
    n = len(t)
    x = np.zeros((n, 2))
    for bird in range(3):
        start = 0.05 + bird * 0.12
        rate = r.uniform(9, 12)
        for k in range(int(0.9 * rate)):
            i0 = int((start + k / rate) * SR)
            ln = int(0.05 * SR)
            if i0 + ln >= n:
                break
            f = bandpass(r.standard_normal(ln), 300, 2500) * np.hanning(ln) * (1 - k / (0.9 * rate)) * 0.6
            pan = r.uniform(0.2, 0.8)
            x[i0:i0 + ln, 0] += f * (1 - pan)
            x[i0:i0 + ln, 1] += f * pan
    return write('cine_a1m1_pigeons', norm(fit(x, 1.4), -14.0))


def build():
    return [couple(), whistle(), whistle_far(), chuff(), hiss(), depart(), stamp(), swell(), tram_arrive(),
            tram_depart(), door(), pigeons()]


if __name__ == '__main__':
    import json
    print(json.dumps(build(), indent=1))
