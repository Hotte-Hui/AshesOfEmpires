"""minigame_sfx -- original synthesized sounds for the three optional mini-games (TECHNICAL_ARCHITECTURE 12.8).

Run:  py -3 -P tools/audiogen/minigame_sfx.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/mg_*.wav (44.1 kHz, 16-bit, mono):
  mg_points        hand-throw points lever: lever clank + blade slide + counterweight thud
  mg_couple        automatic coupler closing / opening: heavy steel clash with a short ring
  mg_shunt         shunting engine moving off: three soft chuffs + rail-joint clicks (one-shot, ~1.4 s)
  mg_chess_tap     a wooden peg piece set into the board
  mg_radio_static  LOOP 4 s: medium-wave hiss with crackles
  mg_radio_jazz    LOOP 8 s: a foreign station far away -- piano comping, walking bass, brushes (original)
  mg_radio_whistle LOOP 1 s: heterodyne whistle near a station (the UI bends its pitch with the detuning)
  mg_radio_key     a piano key of the radio set snapping down
Loops are built periodic and carry a RIFF 'smpl' chunk (Godot's WAV importer, loop_mode 'detect' -> forward loop).
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


def mode(t, f, decay, amp=1.0):
    return amp * np.sin(2 * math.pi * f * t) * np.exp(-6.9 * t / decay)


def place(dst, src, at_sec, gain=1.0, wrap=False):
    i = int(round(at_sec * SR)) % len(dst) if wrap else int(round(at_sec * SR))
    if wrap:
        idx = (np.arange(len(src)) + i) % len(dst)
        np.add.at(dst, idx, src * gain)
        return
    j = min(len(dst), i + len(src))
    if j > i:
        dst[i:j] += src[:j - i] * gain


def fade(x, fin=0.003, fout=0.03):
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


def clank(r, f0, decay, n_modes=7, spread=2.7):
    t = t_axis(decay * 1.2)
    y = np.zeros_like(t)
    for k in range(n_modes):
        f = f0 * (1 + k * spread * r.uniform(0.85, 1.15))
        y += mode(t, f, decay * r.uniform(0.3, 1.0) / (1 + 0.3 * k), r.uniform(0.3, 1.0) / (1 + 0.4 * k))
    click = r.standard_normal(len(t)) * np.exp(-t / 0.004)
    return y + 0.6 * band(click, 800, 9000)


# =========================================================================== sounds
def points():
    r = rng('points')
    x = np.zeros(int(0.9 * SR))
    place(x, clank(r, 420, 0.35), 0.0, 0.8)
    slide = r.standard_normal(int(0.28 * SR))
    slide = band(slide, 1200, 5000) * np.hanning(len(slide)) * 0.35
    place(x, slide, 0.05)
    place(x, clank(r, 180, 0.5, 5, 1.9), 0.33, 1.0)
    thud = mode(t_axis(0.25), 70, 0.2) + mode(t_axis(0.25), 113, 0.12, 0.5)
    place(x, thud, 0.34, 0.9)
    return fade(x)


def couple():
    r = rng('couple')
    x = np.zeros(int(1.1 * SR))
    place(x, clank(r, 230, 0.8, 9, 1.6), 0.0, 1.0)
    place(x, clank(r, 520, 0.3, 5, 2.3), 0.012, 0.6)
    boom = mode(t_axis(0.6), 52, 0.5) + mode(t_axis(0.6), 87, 0.35, 0.6)
    place(x, boom, 0.0, 1.1)
    return fade(x)


def shunt():
    r = rng('shunt')
    x = np.zeros(int(1.5 * SR))
    for i, at in enumerate((0.0, 0.38, 0.7)):
        n = r.standard_normal(int(0.42 * SR))
        env = np.exp(-np.linspace(0, 6, len(n))) * np.minimum(1, np.linspace(0, 30, len(n)))
        puff = band(n, 120, 1900) * env
        place(x, puff, at, 0.9 - 0.15 * i)
    for at in (0.55, 0.62, 1.05, 1.12):
        place(x, clank(r, 900, 0.06, 3, 1.4), at, 0.25)
    rumble = band(r.standard_normal(len(x)), 30, 160) * np.linspace(0.2, 0.6, len(x))
    x += 0.5 * rumble
    return fade(x, 0.01, 0.2)


def chess_tap():
    r = rng('chess')
    t = t_axis(0.22)
    y = mode(t, 1150, 0.05) + mode(t, 1740, 0.035, 0.6) + mode(t, 610, 0.08, 0.5) + mode(t, 2900, 0.02, 0.25)
    y += 0.5 * band(r.standard_normal(len(t)) * np.exp(-t / 0.003), 1500, 8000)
    return fade(y, 0.0005, 0.03)


def radio_static():
    r = rng('static')
    n = int(4.0 * SR)
    x = band(r.standard_normal(n), 250, 4200)
    x /= np.max(np.abs(x))
    am = 1.0 + 0.25 * np.sin(2 * math.pi * 0.5 * np.arange(n) / SR)   # 2 whole cycles -> seamless
    x *= am
    for i in range(40):
        c = r.standard_normal(int(r.integers(20, 160))) * r.uniform(0.6, 1.6)
        place(x, c * np.hanning(len(c)), r.uniform(0, 4.0), 1.0, wrap=True)
    return x


def radio_jazz():
    """8 s (four 4/4 bars at 120 bpm, swung): Dm7 G7 Cmaj7 A7, walking bass, brushes, comping piano;
    then a long way through the air: band-limited, fading, a little hiss."""
    r = rng('jazz')
    sec = 8.0
    n = int(sec * SR)
    x = np.zeros(n)
    beat = 0.5
    swing = 0.17
    chords = [(146.83, [174.61, 220.0, 261.63, 349.23]),     # Dm7
              (98.0, [174.61, 246.94, 293.66, 349.23]),      # G7
              (130.81, [164.81, 196.0, 246.94, 329.63]),     # Cmaj7
              (110.0, [196.0, 277.18, 329.63, 392.0])]       # A7
    walk = [[146.83, 174.61, 220.0, 207.65], [196.0, 174.61, 164.81, 146.83],
            [130.81, 164.81, 196.0, 220.0], [220.0, 196.0, 164.81, 155.56]]

    def bass(f, dur):
        t = t_axis(dur)
        y = np.sin(2 * math.pi * f * t) + 0.35 * np.sin(4 * math.pi * f * t) + 0.12 * np.sin(6 * math.pi * f * t)
        return y * np.exp(-t / 0.35) * np.minimum(1, t / 0.006)

    def piano(fs, dur, vel):
        t = t_axis(dur)
        y = np.zeros_like(t)
        for f in fs:
            for k, a in ((1, 1.0), (2, 0.5), (3, 0.22), (4, 0.12), (5, 0.06)):
                y += a * np.sin(2 * math.pi * f * k * t * (1 + 0.0006 * k * k)) * np.exp(-t * (1.6 + 0.9 * k))
        return vel * y * np.minimum(1, t / 0.004)

    for bar in range(4):
        root, ch = chords[bar]
        for b in range(4):
            st = (bar * 4 + b) * beat
            place(x, bass(walk[bar][b] / 2, 0.48), st, 0.9, wrap=True)
            # brushes: swish on every beat, slap on 2 and 4, swung ride-ish tick on the "and"
            sw = band(r.standard_normal(int(0.32 * SR)), 2500, 9000) * np.hanning(int(0.32 * SR))
            place(x, sw, st, 0.10, wrap=True)
            if b % 2 == 1:
                slap = band(r.standard_normal(int(0.12 * SR)), 1200, 7000) * np.exp(-np.linspace(0, 9, int(0.12 * SR)))
                place(x, slap, st, 0.28, wrap=True)
            tick = band(r.standard_normal(int(0.05 * SR)), 5000, 11000) * np.exp(-np.linspace(0, 8, int(0.05 * SR)))
            place(x, tick, st + beat * (0.5 + swing), 0.12, wrap=True)
        # comping: on 1-and and on 3 (Charleston-ish), a little fill on the last bar
        place(x, piano(ch, 0.9, 0.22), bar * 2.0 + beat * (0.5 + swing), 1.0, wrap=True)
        place(x, piano(ch, 0.6, 0.18), bar * 2.0 + beat * 2.0, 1.0, wrap=True)
        if bar == 3:
            for i, f in enumerate((523.25, 466.16, 440.0, 392.0)):
                place(x, piano([f], 0.3, 0.16), bar * 2.0 + beat * (2.5 + i * 0.4), 1.0, wrap=True)
    # medium wave from far away: narrow band, slow fading (2 whole cycles), hiss
    x = band(x, 280, 3200, 6)
    x /= np.max(np.abs(x)) + 1e-9
    tt = np.arange(n) / SR
    x *= 0.78 + 0.22 * np.sin(2 * math.pi * tt / 4.0)
    x += 0.04 * band(r.standard_normal(n), 2000, 6000)
    return x


def radio_whistle():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * math.pi * 900 * t) + 0.15 * np.sin(2 * math.pi * 1800 * t)
    x *= 1 + 0.1 * np.sin(2 * math.pi * 5 * t)
    return x


def radio_key():
    r = rng('key')
    x = np.zeros(int(0.3 * SR))
    place(x, clank(r, 1400, 0.05, 4, 1.8), 0.0, 0.7)
    place(x, clank(r, 700, 0.09, 4, 1.5), 0.045, 1.0)
    place(x, mode(t_axis(0.12), 160, 0.08), 0.045, 0.6)
    return fade(x, 0.0005, 0.04)


def main(argv):
    out = [write_wav('mg_points', points(), peak_db=-4.0),
           write_wav('mg_couple', couple(), peak_db=-3.0),
           write_wav('mg_shunt', shunt(), peak_db=-6.0),
           write_wav('mg_chess_tap', chess_tap(), peak_db=-5.0),
           write_wav('mg_radio_static', radio_static(), loop=True, peak_db=-8.0),
           write_wav('mg_radio_jazz', radio_jazz(), loop=True, peak_db=-5.0),
           write_wav('mg_radio_whistle', radio_whistle(), loop=True, peak_db=-14.0),
           write_wav('mg_radio_key', radio_key(), peak_db=-5.0)]
    for p in out:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main(sys.argv[1:])
