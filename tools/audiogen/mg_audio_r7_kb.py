"""mg_audio_r7_kb -- original synthesized sounds for the round-7 mini-games "Der Morsetaster" (Karsk signal box)
and "Rohrpost" (Berlin archive), TECHNICAL_ARCHITECTURE 12.8.

Run:  py -3 -P tools/audiogen/mg_audio_r7_kb.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono WAV):
  mg_morse_down      sounder armature striking the lower stop (the "click" that starts every element)
  mg_morse_up        armature flying back against the upper stop (the lighter "clack" that ends it)
  mg_morse_key_down  the operator's key closing its contact (bakelite knob, brass contact, a thump in the desk)
  mg_morse_key_up    the key's spring lifting the lever again
  mg_morse_bell      the call bell of the telegraph line: an electric trembler bell, then its ring-out
  mg_morse_inker     LOOP 2 s: clockwork of the Morse register drawing the paper tape (gear ticks + paper)
  mg_tube_turn       a diverter knob of the tube board turned into its next detent (ratchet + brass tock)
  mg_tube_bell       the small desk bell that calls the porter's lodge ("send the capsule")
  mg_tube_send       a capsule dropping into the tube far away, the valve opening, the air taking it
  mg_tube_rush       LOOP 2 s: air rushing through a brass tube (the capsule under way)
  mg_tube_arrive     the capsule shooting out into the wicker basket of a station
  mg_tube_stuck      the capsule jamming in a closed diverter or a frozen line: thud, knock, escaping air
Loops are built periodic (circular filtering) and carry a RIFF 'smpl' chunk (Godot's WAV importer, loop_mode
'detect' -> forward loop).
"""
from __future__ import annotations

import math
import os
import struct
import sys
import wave
import zlib

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


def t_axis(sec: float) -> np.ndarray:
    return np.arange(int(round(sec * SR)), dtype=np.float64) / SR


def band(x: np.ndarray, lo: float, hi: float, order: int = 4) -> np.ndarray:
    """circular FFT band-pass (periodic -> keeps loops seamless)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = 1.0 / np.sqrt(1.0 + (np.maximum(lo, 1e-3) / np.maximum(f, 1e-3)) ** order) if lo > 0 else np.ones_like(f)
    g = g / np.sqrt(1.0 + (f / hi) ** order)
    return np.fft.irfft(X * g, len(x))


def mode(t, f, decay, amp=1.0, phase=0.0):
    """damped sine; decay = time to -60 dB"""
    return amp * np.sin(2 * math.pi * f * t + phase) * np.exp(-6.9 * t / decay)


def place(dst, src, at_sec, gain=1.0, wrap=False):
    i = int(round(at_sec * SR))
    if wrap:
        idx = (np.arange(len(src)) + i) % len(dst)
        np.add.at(dst, idx, src * gain)
        return
    if i < 0:
        src = src[-i:]
        i = 0
    j = min(len(dst), i + len(src))
    if j > i:
        dst[i:j] += src[:j - i] * gain


def fade(x, fin=0.002, fout=0.02):
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write_wav(name: str, x: np.ndarray, loop: bool = False, peak_db: float = -3.0) -> str:
    os.makedirs(OUT, exist_ok=True)
    y = x * (10 ** (peak_db / 20.0)) / (np.max(np.abs(x)) + 1e-9)
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if loop:
        n = len(pcm)
        smpl = struct.pack('<9I', 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack('<6I', 0, 0, 0, n - 1, 0, 0)
        with open(path, 'r+b') as f:
            data = f.read()
            data += b'smpl' + struct.pack('<I', len(smpl)) + smpl
            data = data[:4] + struct.pack('<I', len(data) - 8) + data[8:]
            f.seek(0)
            f.write(data)
    return path


def click(r, sec, lo, hi, tau):
    n = r.standard_normal(int(sec * SR))
    env = np.exp(-np.arange(len(n)) / SR / tau)
    return band(n * env, lo, hi)


def metal(r, t, f0, ratios, decay, amps=None):
    y = np.zeros_like(t)
    for k, rt in enumerate(ratios):
        a = (amps[k] if amps else 1.0 / (1 + 0.6 * k)) * r.uniform(0.85, 1.15)
        y += mode(t, f0 * rt * r.uniform(0.985, 1.015), decay / (1 + 0.35 * k), a, r.uniform(0, 6.28))
    return y


# =========================================================================== Morse (Karsk signal box)
def morse_down():
    r = rng('morse_down')
    t = t_axis(0.14)
    y = metal(r, t, 1850, [1.0, 1.71, 2.53, 3.4], 0.045, [1.0, 0.7, 0.45, 0.3])
    y += mode(t, 430, 0.07, 0.9) + mode(t, 690, 0.05, 0.5)          # wooden base
    y += 0.9 * click(r, 0.14, 1800, 9000, 0.0012)
    return fade(y, 0.0003, 0.02)


def morse_up():
    r = rng('morse_up')
    t = t_axis(0.11)
    y = metal(r, t, 2450, [1.0, 1.58, 2.31], 0.03, [0.8, 0.55, 0.35])
    y += mode(t, 560, 0.04, 0.35)
    y += 0.7 * click(r, 0.11, 2500, 11000, 0.0008)
    return fade(y, 0.0003, 0.02)


def morse_key_down():
    r = rng('morse_key_down')
    t = t_axis(0.15)
    y = metal(r, t, 1480, [1.0, 1.9, 2.75], 0.035, [0.7, 0.4, 0.25])
    y += mode(t, 175, 0.09, 1.0) + mode(t, 320, 0.06, 0.5)          # thump through the desk
    y += 0.6 * click(r, 0.15, 900, 6000, 0.0018)
    return fade(y, 0.0003, 0.025)


def morse_key_up():
    r = rng('morse_key_up')
    t = t_axis(0.14)
    y = 0.5 * click(r, 0.14, 2000, 9000, 0.001)
    y += mode(t, 1320, 0.03, 0.35)
    y += mode(t, 4150, 0.09, 0.12) * (1 + 0.3 * np.sin(2 * math.pi * 31 * t))   # spring
    return fade(y, 0.0003, 0.02)


def morse_bell():
    r = rng('morse_bell')
    dur = 1.35
    x = np.zeros(int(dur * SR))
    t = t_axis(0.9)
    strike_rate = 17.5
    n_strikes = int(0.62 * strike_rate)
    for i in range(n_strikes):
        at = i / strike_rate + r.uniform(-0.002, 0.002)
        g = 0.65 + 0.35 * r.random()
        y = metal(r, t, 1260, [1.0, 2.32, 3.61, 4.93, 6.1], 0.8, [1.0, 0.55, 0.35, 0.22, 0.12])
        place(x, y * g, at)
        place(x, click(r, 0.02, 1500, 7000, 0.0015) * 0.4, at)
    # buzz of the trembler contact
    tb = t_axis(0.62)
    buzz = np.sign(np.sin(2 * math.pi * strike_rate * tb)) * 0.04 + band(r.standard_normal(len(tb)), 2000, 6000) * 0.05
    place(x, buzz, 0.0)
    return fade(x, 0.001, 0.25)


def morse_inker():
    r = rng('morse_inker')
    n = int(2.0 * SR)
    x = np.zeros(n)
    tick = 22.0                            # gear teeth per second (44 per loop -> seamless)
    for i in range(int(2.0 * tick)):
        at = i / tick
        g = 0.55 + 0.25 * math.sin(i * 0.9) + 0.2 * r.random()
        y = mode(t_axis(0.03), 3100 + 400 * (i % 3), 0.012, 1.0) + click(r, 0.03, 2500, 9000, 0.0009) * 0.6
        place(x, y * g, at, wrap=True)
    hum = band(r.standard_normal(n), 120, 900) * 0.18
    paper = band(r.standard_normal(n), 3000, 9000) * 0.12
    am = 1.0 + 0.25 * np.sin(2 * math.pi * 1.0 * np.arange(n) / SR)
    x += (hum + paper) * am
    return x


# =========================================================================== Rohrpost (Berlin archive)
def tube_turn():
    r = rng('tube_turn')
    x = np.zeros(int(0.3 * SR))
    for at, g in ((0.0, 0.45), (0.035, 0.55), (0.075, 1.0)):
        y = metal(r, t_axis(0.2), 1650 if g < 1 else 920, [1.0, 1.83, 2.9], 0.06 if g < 1 else 0.12)
        place(x, y * g, at)
        place(x, click(r, 0.05, 1200, 8000, 0.0012) * g * 0.6, at)
    place(x, mode(t_axis(0.12), 210, 0.08, 0.6), 0.075)
    return fade(x, 0.0003, 0.04)


def tube_bell():
    r = rng('tube_bell')
    t = t_axis(1.2)
    y = metal(r, t, 2140, [1.0, 2.71, 4.02, 5.4], 1.1, [1.0, 0.4, 0.22, 0.1])
    y += click(r, 1.2, 2000, 8000, 0.002) * 0.3
    return fade(y, 0.0005, 0.2)


def tube_send():
    r = rng('tube_send')
    dur = 1.05
    x = np.zeros(int(dur * SR))
    t = t_axis(0.3)
    # capsule dropped into the mouth (leather on brass, heard through the tube: dull)
    thunk = mode(t, 140, 0.18, 1.0) + mode(t, 310, 0.1, 0.5) + mode(t, 720, 0.05, 0.3)
    place(x, thunk, 0.0, 0.9)
    # valve opening: a soft "pfump" (low-passed burst)
    nb = r.standard_normal(int(0.3 * SR))
    env = np.minimum(1.0, np.arange(len(nb)) / (0.01 * SR)) * np.exp(-np.arange(len(nb)) / SR / 0.08)
    place(x, band(nb * env, 60, 700), 0.09, 1.1)
    # the air takes it: noise band sweeping upwards, fading into the rush
    n = int(0.85 * SR)
    noise = r.standard_normal(n)
    seg = 2048
    out = np.zeros(n)
    win = np.hanning(seg)
    for i in range(0, n - seg, seg // 2):
        f = i / n
        lo, hi = 250 + 500 * f, 900 + 2400 * f
        out[i:i + seg] += band(noise[i:i + seg] * win, lo, hi)
    env2 = np.minimum(1.0, np.arange(n) / (0.25 * SR)) * np.linspace(1.0, 0.55, n)
    place(x, out * env2 * 0.7, 0.2)
    return fade(x, 0.001, 0.12)


def tube_rush():
    r = rng('tube_rush')
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    x = band(r.standard_normal(n), 180, 1900)
    x /= np.max(np.abs(x))
    # tube resonances (low Q): built from noise filtered narrowly -> periodic and seamless
    for f0, g in ((310.0, 0.5), (620.0, 0.3), (930.0, 0.18)):
        x += band(r.standard_normal(n), f0 * 0.94, f0 * 1.06, 8) * g * 4.0
    am = 1.0 + 0.18 * np.sin(2 * math.pi * 1.5 * t) + 0.08 * np.sin(2 * math.pi * 4.0 * t)
    x *= am
    hiss = band(r.standard_normal(n), 3000, 8000) * 0.08
    return x + hiss


def tube_arrive():
    r = rng('tube_arrive')
    dur = 0.85
    x = np.zeros(int(dur * SR))
    # whoosh tail (falling)
    n = int(0.22 * SR)
    tail = band(r.standard_normal(n), 300, 1500) * np.linspace(1, 0, n) ** 1.5
    place(x, tail, 0.0, 0.6)
    t = t_axis(0.4)
    # capsule shooting out and landing in the wicker basket
    thump = mode(t, 118, 0.22, 1.0) + mode(t, 260, 0.12, 0.6) + mode(t, 540, 0.06, 0.3)
    place(x, thump, 0.16, 1.0)
    place(x, click(r, 0.05, 600, 5000, 0.003), 0.16, 0.6)
    for k in range(6):                      # basket rattle
        at = 0.2 + k * 0.035 + r.uniform(0, 0.01)
        place(x, click(r, 0.03, 1500, 7000, 0.0015), at, 0.35 * (1 - k / 7))
    # brass cap knocks once against the rim
    place(x, metal(r, t_axis(0.2), 1730, [1.0, 2.2, 3.3], 0.09), 0.26, 0.35)
    return fade(x, 0.001, 0.08)


def tube_stuck():
    r = rng('tube_stuck')
    dur = 0.9
    x = np.zeros(int(dur * SR))
    t = t_axis(0.5)
    place(x, mode(t, 82, 0.3, 1.0) + mode(t, 165, 0.2, 0.6) + mode(t, 420, 0.08, 0.3), 0.0, 1.0)
    place(x, metal(r, t_axis(0.25), 640, [1.0, 2.4, 3.9], 0.14), 0.01, 0.45)
    n = int(0.7 * SR)
    hiss = band(r.standard_normal(n), 2200, 7500) * np.exp(-np.arange(n) / SR / 0.25)
    hiss *= np.minimum(1.0, np.arange(n) / (0.03 * SR))
    place(x, hiss, 0.08, 0.5)
    return fade(x, 0.001, 0.1)


def main(argv):
    out = [write_wav('mg_morse_down', morse_down(), peak_db=-4.0),
           write_wav('mg_morse_up', morse_up(), peak_db=-7.0),
           write_wav('mg_morse_key_down', morse_key_down(), peak_db=-5.0),
           write_wav('mg_morse_key_up', morse_key_up(), peak_db=-9.0),
           write_wav('mg_morse_bell', morse_bell(), peak_db=-6.0),
           write_wav('mg_morse_inker', morse_inker(), loop=True, peak_db=-14.0),
           write_wav('mg_tube_turn', tube_turn(), peak_db=-5.0),
           write_wav('mg_tube_bell', tube_bell(), peak_db=-8.0),
           write_wav('mg_tube_send', tube_send(), peak_db=-4.0),
           write_wav('mg_tube_rush', tube_rush(), loop=True, peak_db=-9.0),
           write_wav('mg_tube_arrive', tube_arrive(), peak_db=-3.0),
           write_wav('mg_tube_stuck', tube_stuck(), peak_db=-4.0)]
    for p in out:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main(sys.argv[1:])
