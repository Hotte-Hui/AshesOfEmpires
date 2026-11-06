"""memories_audio -- original synthesized sounds of the „Erinnerungen“ feature (TECHNICAL_ARCHITECTURE 12.10).

Run:  py -3 -P tools/audiogen/memories_audio.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/mem_*.wav (44.1 kHz, 16-bit, stereo, one-shots):
  mem_rewind   ~2.9 s  travel into a memory: a soft pocket-clock tick running BACKWARDS (each tick time-reversed:
                       the ring swells and stops on the click) and speeding up like a hand winding the clock back,
                       over a reversed airy swell and a faint tape-wow drone that sinks a little in pitch;
                       ends in a hushed low settle when the darkroom is reached. No chime, no fanfare.
  mem_return   ~2.6 s  back to the present: the same clock running FORWARD, fast at first and settling into an
                       ordinary tick-tock, the swell played forward and fading out; the drone rises back to pitch.
Every value comes from fixed seeds (zlib.crc32 of the sound name): a re-run writes byte-identical files.
"""
from __future__ import annotations

import math
import os
import wave
import zlib

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def rng(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode('utf-8')))


def t_axis(sec: float) -> np.ndarray:
    return np.arange(int(round(sec * SR)), dtype=np.float64) / SR


def band(x: np.ndarray, lo: float, hi: float, order: int = 4) -> np.ndarray:
    """FFT band-pass (zero phase)."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = np.ones_like(f)
    if lo > 0:
        g = g / np.sqrt(1.0 + (lo / np.maximum(f, 1e-3)) ** order)
    if hi > 0:
        g = g / np.sqrt(1.0 + (f / hi) ** order)
    return np.fft.irfft(X * g, n)


def band_pad(x: np.ndarray, lo: float, hi: float, pad: int = 8192) -> np.ndarray:
    """band() of a short one-shot with zero padding, so the FFT filter cannot wrap energy around its ends."""
    y = band(np.concatenate([np.zeros(pad), x, np.zeros(pad)]), lo, hi)
    return y[pad:pad + len(x)]


def place(dst: np.ndarray, src: np.ndarray, at_sec: float, gain: float = 1.0) -> None:
    i = int(round(at_sec * SR))
    j = min(len(dst), i + len(src))
    if j > i >= 0:
        dst[i:j] += src[:j - i] * gain


def tick(r: np.random.Generator, pitch: float = 1.0, body: float = 1.0) -> np.ndarray:
    """One small clock tick: escapement click + two short metallic ring modes + a wooden case knock."""
    t = t_axis(0.09)
    click = r.standard_normal(len(t)) * np.exp(-t / 0.0011)
    click = band_pad(click, 1800 * pitch, 9000)
    ring = np.zeros_like(t)
    for f0, dec, amp in ((3150.0, 0.012, 0.55), (4720.0, 0.008, 0.35), (2210.0, 0.018, 0.25)):
        f = f0 * pitch * r.uniform(0.985, 1.015)
        ring += amp * np.sin(2 * math.pi * f * t + r.uniform(0, 6.28)) * np.exp(-t / dec)
    case = np.sin(2 * math.pi * 620 * pitch * t) * np.exp(-t / 0.01) * 0.35 * body
    y = 0.8 * click + ring + case
    y[:12] *= np.linspace(0.0, 1.0, 12)
    y[-600:] *= np.linspace(1.0, 0.0, 600)   # no step at the end of the tail (it starts a reversed tick)
    return y


def swell(r: np.random.Generator, sec: float, lo: float, hi: float, release: float = 0.16) -> np.ndarray:
    """Airy noise swell (rises with a soft curve, short soft release at the peak), band-limited, slow shimmer."""
    t = t_axis(sec)
    n = band_pad(r.standard_normal(len(t)), lo, hi)
    env = (t / sec) ** 2.2
    rel = int(release * SR)
    if rel > 0:
        env[-rel:] *= np.cos(np.linspace(0.0, math.pi / 2, rel)) ** 2
    shimmer = 1.0 + 0.18 * np.sin(2 * math.pi * 5.3 * t + r.uniform(0, 6.28))
    return n * env * shimmer


def drone(sec: float, f_from: float, f_to: float) -> np.ndarray:
    """Faint tape-wow drone: two detuned sines sliding between f_from and f_to with a slow wow."""
    t = t_axis(sec)
    k = t / sec
    f = f_from + (f_to - f_from) * (k * k * (3 - 2 * k))
    wow = 1.0 + 0.006 * np.sin(2 * math.pi * 0.9 * t)
    ph = 2 * math.pi * np.cumsum(f * wow) / SR
    y = np.sin(ph) + 0.6 * np.sin(1.503 * ph) + 0.25 * np.sin(2.01 * ph)
    env = np.sin(np.pi * np.clip(k, 0, 1)) ** 1.5
    return y * env


def settle(sec: float = 0.7) -> np.ndarray:
    """Hushed low settle (a felt-muted low thump with a short soft tail)."""
    t = t_axis(sec)
    y = np.sin(2 * math.pi * 58 * t) * np.exp(-t / 0.22) + 0.4 * np.sin(2 * math.pi * 87 * t) * np.exp(-t / 0.15)
    y[:200] *= np.linspace(0, 1, 200)
    return y


def stereo(x: np.ndarray, pan: float) -> np.ndarray:
    a = (pan + 1.0) * math.pi / 4.0
    return np.stack([x * math.cos(a), x * math.sin(a)], axis=1)


def write(name: str, st: np.ndarray, peak_db: float = -4.0) -> str:
    os.makedirs(OUT, exist_ok=True)
    y = st * (10 ** (peak_db / 20.0)) / (np.max(np.abs(st)) + 1e-12)
    pcm = np.clip(np.round(y * 32767.0), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def fade(x: np.ndarray, fin: float, fout: float) -> np.ndarray:
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


# =========================================================================== sounds
def mem_rewind() -> np.ndarray:
    r = rng('mem_rewind')
    dur = 2.9
    L = np.zeros(int(dur * SR))
    R = np.zeros(int(dur * SR))
    # ticks: intervals shrink from 0.42 s to 0.09 s (the hand winds the clock back), each tick time-reversed
    at = 0.05
    gap = 0.42
    i = 0
    while at < 2.05:
        tk = tick(r, pitch=1.0 + 0.10 * (at / 2.05), body=1.0 if i % 2 == 0 else 0.6)[::-1]
        g = 0.55 + 0.45 * min(1.0, at / 1.2)
        pan = -0.18 if i % 2 == 0 else 0.18
        a = (pan + 1.0) * math.pi / 4.0
        place(L, tk, at, g * math.cos(a))
        place(R, tk, at, g * math.sin(a))
        at += gap
        gap = max(0.09, gap * 0.82)
        i += 1
    # rising swell (peaks when the darkroom is reached); an independent noise per channel keeps it wide
    place(L, swell(r, 2.2, 900, 6500), 0.15, 0.15)
    place(R, swell(r, 2.2, 900, 6500), 0.15, 0.15)
    dr = drone(2.6, 196.0, 176.0)
    place(L, dr, 0.1, 0.07)
    place(R, dr, 0.1, 0.065)
    st = settle()
    place(L, st, 2.2, 0.55)
    place(R, st, 2.2, 0.55)
    y = np.stack([L, R], axis=1)
    return fade(y, 0.01, 0.35)


def mem_return() -> np.ndarray:
    r = rng('mem_return')
    dur = 2.6
    L = np.zeros(int(dur * SR))
    R = np.zeros(int(dur * SR))
    # forward ticks: fast at first, settling into an ordinary tick-tock (0.5 s)
    at = 0.04
    gap = 0.09
    i = 0
    while at < 2.35:
        tk = tick(r, pitch=1.10 - 0.10 * min(1.0, at / 1.6), body=1.0 if i % 2 == 0 else 0.55)
        if i % 2 == 1:
            tk = band_pad(tk, 300, 4200)    # the "tock": duller
        g = 0.9 - 0.35 * min(1.0, at / 2.2)
        pan = -0.18 if i % 2 == 0 else 0.18
        a = (pan + 1.0) * math.pi / 4.0
        place(L, tk, at, g * math.cos(a))
        place(R, tk, at, g * math.sin(a))
        at += gap
        gap = min(0.5, gap * 1.28)
        i += 1
    # the swell from its peak, fading out (time-reversed rise), one noise per channel
    place(L, swell(r, 1.6, 900, 6500, 0.02)[::-1], 0.0, 0.14)
    place(R, swell(r, 1.6, 900, 6500, 0.02)[::-1], 0.012, 0.14)
    dr = drone(2.2, 176.0, 196.0)
    place(L, dr, 0.0, 0.06)
    place(R, dr, 0.0, 0.055)
    y = np.stack([L, R], axis=1)
    return fade(y, 0.004, 0.3)


SOUNDS = {'mem_rewind': mem_rewind, 'mem_return': mem_return}


def main() -> None:
    for name, fn in SOUNDS.items():
        path = write(name, fn())
        print('wrote', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
