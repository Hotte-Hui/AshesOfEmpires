"""plaza_sfx -- original synthesized sounds for the plaza before the Great Hall (L_M1_Plaza, area plaza-env).

Run:  py -3 -P tools/audiogen/plaza_sfx.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
  plaza_march_loop.wav  8 s seamless loop: distant bass drum + side drum figure + thousands of boots in step on
                        packed snow (120 steps/min), muffled by distance, plaza echo; RIFF 'smpl' loop chunk
                        (Godot WAV import loop_mode 'detect').  Played by PlazaParade via Audio.sfx_loop.
  plaza_tank_pass.wav   9 s one-shot: a tank passing on the avenue (engine drone, track clatter, approach/recede)
  plaza_shutter.wav     0.6 s one-shot: press camera shutter + flash bulb pop (PlazaFlash)
Tone: cold and mechanical, never triumphant (no brass, no melody).
"""
from __future__ import annotations

import math
import os
import struct
import wave
import zlib

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def rng(name):
    return np.random.default_rng(zlib.crc32(name.encode()))


def spec_filter(x, lo=0.0, hi=SR / 2, tilt=0.0):
    """circular FFT band filter with soft edges (periodic signals stay seamless)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-3
    H = np.ones_like(f)
    if lo > 0:
        H *= 1 / (1 + (lo / f) ** 4)
    if hi < SR / 2:
        H *= 1 / (1 + (f / hi) ** 4)
    if tilt:
        H *= (f / 1000.0) ** (tilt / 6.02)
    return np.fft.irfft(X * H, len(x))


def noise(n, r, lo, hi, tilt=0.0):
    return spec_filter(r.standard_normal(n), lo, hi, tilt)


def place(buf, sig, at, gain=1.0, circular=True):
    i = int(round(at * SR)) % len(buf) if circular else int(round(at * SR))
    n = len(sig)
    if circular:
        idx = (np.arange(n) + i) % len(buf)
        np.add.at(buf, idx, sig * gain)
    else:
        e = min(len(buf), i + n)
        if e > i:
            buf[i:e] += sig[:e - i] * gain


def env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(att, 1e-4)) * np.exp(-t / dec)


def norm(x, peak_db=-3.0):
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)


def write_wav(name, x, loop=False, peak_db=-3.0):
    os.makedirs(OUT, exist_ok=True)
    pcm = np.clip(np.round(norm(x, peak_db) * 32767), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if loop:
        n = len(pcm)
        smpl = struct.pack('<9I', 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0) + struct.pack('<6I', 0, 0, 0, n - 1, 0, 0)
        with open(path, 'r+b') as f:
            data = f.read()
            data += b'smpl' + struct.pack('<I', len(smpl)) + smpl
            data = data[:4] + struct.pack('<I', len(data) - 8) + data[8:]
            f.seek(0)
            f.write(data)
    return path


def march_loop():
    sec, r = 8.0, rng('plaza_march')
    n = int(sec * SR)
    buf = np.zeros(n)
    # boots: every 0.5 s, ~40 feet smeared over +-25 ms (a mass in step), crunch of packed snow
    for k in range(16):
        for j in range(40):
            m = int(0.09 * SR)
            crunch = noise(m, r, 180, 2600, tilt=-2) * env(m, 0.002, 0.03)
            thud = np.sin(2 * math.pi * 70 * np.arange(m) / SR) * env(m, 0.001, 0.025) * 0.6
            place(buf, (crunch + thud) * r.uniform(0.5, 1.0), k * 0.5 + r.normal(0, 0.012), 0.08)
    # bass drum on every second step, a little ahead of the boots
    for k in range(8):
        m = int(0.6 * SR)
        t = np.arange(m) / SR
        f = 52 + 30 * np.exp(-t / 0.03)
        body = np.sin(2 * math.pi * np.cumsum(f) / SR) * env(m, 0.002, 0.28)
        place(buf, body + 0.15 * noise(m, r, 60, 400) * env(m, 0.001, 0.05), k * 1.0 - 0.01, 0.9)
    # side drum: a dry, repetitive figure (2 s bar), far away
    figure = (0.0, 0.25, 0.5, 0.625, 0.75, 1.0, 1.5, 1.625, 1.75)
    for bar in range(4):
        for i, a in enumerate(figure):
            m = int(0.16 * SR)
            hit = noise(m, r, 900, 4200) * env(m, 0.001, 0.045) + 0.4 * np.sin(2 * math.pi * 210 * np.arange(m) / SR) * env(m, 0.001, 0.03)
            place(buf, hit, bar * 2.0 + a, 0.22 if i % 3 else 0.3)
    # distance: muffle highs, plaza echo (circular -> the loop stays seamless)
    buf = spec_filter(buf, 40, 1900, tilt=-1.5)
    m = int(0.9 * SR)
    ir = r.standard_normal(m) * np.exp(-np.arange(m) / SR / 0.28)
    ir = spec_filter(ir, 80, 1500)
    ir[:int(0.11 * SR)] = 0.0
    echo = np.fft.irfft(np.fft.rfft(buf) * np.fft.rfft(np.pad(ir, (0, n - m))), n)
    buf = buf + 0.5 * echo / (np.max(np.abs(echo)) + 1e-9) * np.max(np.abs(buf))
    buf += 0.02 * noise(n, r, 60, 900)                         # low city/crowd bed
    return buf


def tank_pass():
    sec, r = 9.0, rng('plaza_tank')
    n = int(sec * SR)
    t = np.arange(n) / SR
    near = np.exp(-((t - 4.6) / 1.9) ** 2)
    f0 = 31.0 * (1 + 0.03 * np.sin(2 * math.pi * 0.4 * t))
    ph = 2 * math.pi * np.cumsum(f0) / SR
    eng = sum(a * np.sin(h * ph) for h, a in ((1, 1.0), (2, 0.7), (3, 0.45), (4, 0.3), (6, 0.18)))
    eng *= 1 + 0.35 * noise(n, r, 4, 25)
    eng += 0.6 * noise(n, r, 25, 220)
    clat = np.zeros(n)
    rate = 13.0
    k = 0.0
    while k < sec:
        m = int(0.03 * SR)
        click = noise(m, r, 500, 3800) * env(m, 0.0005, 0.008)
        place(clat, click * r.uniform(0.4, 1.0), k, 1.0, circular=False)
        k += 1 / rate * r.uniform(0.85, 1.15)
    squeal = noise(n, r, 1100, 1500) * (0.25 + 0.75 * (noise(n, r, 0.3, 2) > 0.5))
    x = eng * (0.25 + 0.75 * near) + clat * (0.05 + 1.1 * near ** 1.5) + 0.08 * squeal * near
    x = spec_filter(x, 20, 2600)
    x *= np.minimum(1, t / 1.2) * np.minimum(1, (sec - t) / 1.5)
    return x


def shutter():
    r = rng('plaza_shutter')
    n = int(0.6 * SR)
    x = np.zeros(n)
    for at, g in ((0.0, 1.0), (0.034, 0.7)):
        m = int(0.02 * SR)
        place(x, noise(m, r, 1800, 7000) * env(m, 0.0003, 0.004), at, g, circular=False)
    m = int(0.25 * SR)
    place(x, noise(m, r, 250, 1600) * env(m, 0.004, 0.07), 0.012, 0.5, circular=False)
    m = int(0.12 * SR)
    place(x, noise(m, r, 3000, 9000) * env(m, 0.001, 0.02), 0.09, 0.15, circular=False)
    return x


def main():
    print(write_wav('plaza_march_loop', march_loop(), loop=True, peak_db=-4.0))
    print(write_wav('plaza_tank_pass', tank_pass(), peak_db=-3.0))
    print(write_wav('plaza_shutter', shutter(), peak_db=-6.0))


if __name__ == '__main__':
    main()
