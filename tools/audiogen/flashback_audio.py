"""flashback_audio -- the one sound of the history-card flashback films (TECHNICAL_ARCHITECTURE 12.15).

Run:  py -3 -P tools/audiogen/flashback_audio.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/fb_projector_bed.wav (44.1 kHz, 16-bit, stereo, one-shot, ~19 s):
  a small film projector in a quiet room -- the switch, the motor running up in under a second, then a steady
  whirr with the claw ticking sixteen times a second, a low motor hum, the hiss and a few soft pops of an optical
  track that carries no sound; the motor runs down at the end.  Deliberately no music and no tone that comments:
  the real-history cards are never celebrated and never scored (12.3).  The films are 16 to 16.5 s long; the view
  fades the bed when a film ends or is skipped.
Every value comes from one fixed seed (zlib.crc32 of the sound name): a re-run writes a byte-identical file.
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
NAME = 'fb_projector_bed'
LENGTH = 19.0
FPS = 16.0


def band(x: np.ndarray, lo: float, hi: float, order: int = 4) -> np.ndarray:
    """FFT band-pass (zero phase)."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = np.ones_like(f)
    if lo > 0:
        g = g / np.sqrt(1.0 + (lo / np.maximum(f, 1e-3)) ** order)
    if hi > 0:
        g = g / np.sqrt(1.0 + (f / hi) ** order)
    return np.fft.irfft(spec * g, n)


def build() -> np.ndarray:
    r = np.random.default_rng(zlib.crc32(NAME.encode('utf-8')))
    n = int(round(LENGTH * SR))
    t = np.arange(n, dtype=np.float64) / SR
    # the motor: up to speed in 0.8 s, down again in the last 1.3 s
    speed = np.clip(t / 0.8, 0.0, 1.0) ** 0.7 * np.clip((LENGTH - t) / 1.3, 0.0, 1.0) ** 0.6
    phase = np.cumsum(speed) / SR                                     # running time of the mechanism
    # whirr: band noise, breathing with the shutter
    whirr = band(r.standard_normal(n), 320.0, 2400.0)
    whirr *= 0.55 + 0.45 * np.sin(2 * math.pi * FPS * phase) ** 2
    # the claw: one tick per frame, a lighter one between, a little uneven
    ticks = np.zeros(n)
    click_len = int(0.006 * SR)
    env = np.exp(-np.arange(click_len) / (0.0011 * SR))
    frame = 0
    while True:
        at = None
        target = (frame + 0.02 * r.standard_normal()) / FPS
        idx = int(np.searchsorted(phase, target))
        if idx >= n - click_len:
            break
        at = idx
        ticks[at:at + click_len] += r.standard_normal(click_len) * env * (0.9 + 0.2 * r.random())
        half = int(np.searchsorted(phase, (frame + 0.5) / FPS))
        if half < n - click_len:
            ticks[half:half + click_len] += r.standard_normal(click_len) * env * 0.35
        frame += 1
    ticks = band(ticks, 1500.0, 6500.0)
    hum = (np.sin(2 * math.pi * 96.0 * phase) + 0.4 * np.sin(2 * math.pi * 192.0 * phase + 0.7)) * speed
    hiss_l = band(r.standard_normal(n), 4200.0, 9500.0)
    hiss_r = band(r.standard_normal(n), 4200.0, 9500.0)
    pops = np.zeros(n)
    for _ in range(26):                                               # soft pops of the empty optical track
        at = int(r.uniform(1.0, LENGTH - 1.6) * SR)
        ln = int(0.004 * SR)
        pops[at:at + ln] += r.standard_normal(ln) * np.exp(-np.arange(ln) / (0.0008 * SR)) * r.uniform(0.3, 1.0)
    pops = band(pops, 700.0, 5000.0)
    switch = np.zeros(n)                                              # the switch at the start
    ln = int(0.03 * SR)
    switch[200:200 + ln] = r.standard_normal(ln) * np.exp(-np.arange(ln) / (0.004 * SR))
    switch = band(switch, 500.0, 4000.0)

    def norm(x: np.ndarray) -> np.ndarray:
        return x / max(1e-9, float(np.sqrt(np.mean(x * x))))

    mono = (0.050 * norm(whirr) * speed + 0.016 * norm(ticks) * 3.0 + 0.012 * hum + 0.012 * norm(pops) * 0.6
            + 0.02 * norm(switch) * 0.25)
    left = mono + 0.010 * norm(hiss_l) * speed
    right = mono + 0.010 * norm(hiss_r) * speed
    st = np.stack([left, right], axis=1)
    fade = int(0.02 * SR)
    st[:fade] *= np.linspace(0.0, 1.0, fade)[:, None]
    st[-fade:] *= np.linspace(1.0, 0.0, fade)[:, None]
    peak = float(np.max(np.abs(st)))
    if peak > 0.5:
        st *= 0.5 / peak
    return st


def write(path: str, st: np.ndarray) -> None:
    r = np.random.default_rng(zlib.crc32((NAME + '/dither').encode('utf-8')))
    d = (r.random(st.shape) - r.random(st.shape)) / 32768.0           # TPDF dither
    pcm = np.clip(np.round((st + d) * 32767.0), -32768, 32767).astype('<i2')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> int:
    st = build()
    path = os.path.join(OUT, NAME + '.wav')
    write(path, st)
    rms = float(np.sqrt(np.mean(st * st)))
    print('%s  %.2f s  rms %.1f dBFS  peak %.1f dBFS' % (NAME, len(st) / SR, 20 * math.log10(max(rms, 1e-9)),
                                                          20 * math.log10(float(np.max(np.abs(st))))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
