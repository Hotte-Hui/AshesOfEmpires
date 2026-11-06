"""mg_audio_r7_v -- original synthesized sounds for the two Chapter-3 mini-games (owner: minigames r7, §12.8).

Run:  py -3 -P tools/audiogen/mg_audio_r7_v.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
  Bahnhof Veltrava, "Die Fallblatttafel"
    mg_flap_clack_1..4  one split-flap card falling onto the next: a dry tick of card on card, a small
                        resonance of the aluminium drum, a soft knock of the stop (four pitches, Audio picks one)
    mg_flap_turn        Alexei's thumb on the drum: a ratchet pawl clicking over one tooth
    mg_flap_rattle      "Probelauf": the motor runs up, the cards rattle past, the line does not catch and the
                        motor runs down again (~1.1 s)
    mg_flap_engage      the line engages: a settling cascade of cards slowing down, the stop, the relay of the
                        row lamp -- understated, no fanfare (~0.9 s)
  Palais, "Die Garderobe"
    mg_cloak_token      a brass coat check laid on the walnut counter (short ring, wooden tap)
    mg_cloak_coat       a wooden hanger lifted off the brass rail, wool brushing wool
    mg_cloak_hat        a felt hat taken from the shelf: soft thump and brush
    mg_cloak_bell       the counter bell, struck once with the flat of the hand
"""
from __future__ import annotations

import math
import os
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
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = 1.0 / np.sqrt(1.0 + (np.maximum(lo, 1e-3) / np.maximum(f, 1e-3)) ** order) if lo > 0 else np.ones_like(f)
    g = g / np.sqrt(1.0 + (f / hi) ** order)
    return np.fft.irfft(X * g, len(x))


def mode(t, f, decay, amp=1.0, phase=0.0):
    return amp * np.sin(2 * math.pi * f * t + phase) * np.exp(-6.9 * t / decay)


def place(dst, src, at_sec, gain=1.0):
    i = int(round(at_sec * SR))
    j = min(len(dst), i + len(src))
    if j > i >= 0:
        dst[i:j] += src[:j - i] * gain


def fade(x, fin=0.002, fout=0.02):
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write_wav(name: str, x: np.ndarray, peak_db: float = -3.0) -> str:
    os.makedirs(OUT, exist_ok=True)
    y = x * (10 ** (peak_db / 20.0)) / (np.max(np.abs(x)) + 1e-9)
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


# =========================================================================== split-flap board
def flap_tick(r, pitch: float = 1.0, level: float = 1.0) -> np.ndarray:
    """One card falling onto the stop: noise snap + drum resonance + a soft knock."""
    t = t_axis(0.09)
    snap = band(r.standard_normal(len(t)), 1800 * pitch, 9000) * np.exp(-t / 0.0028)
    res = mode(t, 1650 * pitch, 0.028, 0.55) + mode(t, 2780 * pitch, 0.016, 0.3) + mode(t, 960 * pitch, 0.035, 0.25)
    knock = mode(t, 310 * pitch, 0.02, 0.45)
    return (snap + res + knock) * level


def flap_clack(i: int) -> np.ndarray:
    r = rng('flap_clack_%d' % i)
    pitch = [1.0, 0.93, 1.06, 0.98][i]
    x = np.zeros(int(0.12 * SR))
    place(x, flap_tick(r, pitch), 0.0)
    # the card's tail flicks the next one a hair later (quieter)
    place(x, flap_tick(r, pitch * 1.08, 0.18), 0.011 + 0.002 * i)
    return fade(x, 0.0005, 0.02)


def flap_turn() -> np.ndarray:
    r = rng('flap_turn')
    x = np.zeros(int(0.12 * SR))
    for k, at in enumerate((0.0, 0.034)):
        t = t_axis(0.05)
        c = band(r.standard_normal(len(t)), 2500, 10000) * np.exp(-t / 0.0015)
        c += mode(t, 3400 - 600 * k, 0.012, 0.4)
        place(x, c, at, 0.7 - 0.25 * k)
    return fade(x, 0.0005, 0.02)


def motor(sec: float, f0: float, env: np.ndarray) -> np.ndarray:
    t = t_axis(sec)
    ph = 2 * math.pi * np.cumsum(f0 * (0.6 + 0.4 * env)) / SR
    y = 0.6 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph + 0.4)
    return y * env


def flap_rattle() -> np.ndarray:
    r = rng('flap_rattle')
    sec = 1.15
    n = int(sec * SR)
    x = np.zeros(n)
    tt = np.arange(n) / SR
    env = np.clip(np.minimum(tt / 0.18, (sec - tt) / 0.3), 0, 1)
    x += 0.18 * motor(sec, 118.0, env)
    # cards rattling past (rate follows the motor), the line never catches
    at = 0.1
    while at < sec - 0.25:
        e = float(np.clip(min((at) / 0.18, (sec - at) / 0.3), 0, 1))
        place(x, flap_tick(r, 1.0 + 0.08 * r.standard_normal(), 0.35 + 0.4 * e), at)
        at += 1.0 / (9.0 + 13.0 * e)
    # the stop: a dull double knock and the gear grinding down
    place(x, mode(t_axis(0.2), 190, 0.12, 0.6) + mode(t_axis(0.2), 290, 0.08, 0.3), sec - 0.28)
    grind = band(r.standard_normal(int(0.25 * SR)), 300, 1800) * np.linspace(0.5, 0.0, int(0.25 * SR))
    place(x, grind, sec - 0.32, 0.25)
    return fade(x, 0.003, 0.08)


def flap_engage() -> np.ndarray:
    r = rng('flap_engage')
    sec = 0.95
    x = np.zeros(int(sec * SR))
    # settling cascade: fast, then slower, the last card lands firmly
    gaps = [0.018, 0.02, 0.023, 0.027, 0.033, 0.042, 0.055, 0.075, 0.1]
    at = 0.0
    for k, g in enumerate(gaps):
        place(x, flap_tick(r, 1.0 + 0.02 * (k % 3), 0.55 + 0.04 * k), at)
        at += g
    place(x, flap_tick(r, 0.92, 1.0), at)
    place(x, mode(t_axis(0.25), 220, 0.15, 0.7) + mode(t_axis(0.25), 147, 0.2, 0.4), at)
    # relay of the row lamp: a small dry click, then a faint electric hum fading in
    t = t_axis(0.04)
    relay = band(r.standard_normal(len(t)), 1500, 7000) * np.exp(-t / 0.002) + mode(t, 2300, 0.01, 0.3)
    place(x, relay, at + 0.12, 0.6)
    hum_t = t_axis(sec - (at + 0.14))
    hum = (np.sin(2 * math.pi * 100 * hum_t) + 0.3 * np.sin(2 * math.pi * 200 * hum_t)) * np.minimum(1, hum_t / 0.15)
    place(x, hum * 0.04, at + 0.14)
    return fade(x, 0.001, 0.12)


# =========================================================================== cloakroom
def cloak_token() -> np.ndarray:
    r = rng('cloak_token')
    x = np.zeros(int(0.6 * SR))
    t = t_axis(0.55)
    ring = mode(t, 3120, 0.35, 0.5) + mode(t, 4670, 0.22, 0.32) + mode(t, 7020, 0.12, 0.18) + mode(t, 2210, 0.3, 0.2)
    tap = band(r.standard_normal(len(t)), 600, 5000) * np.exp(-t / 0.004)
    wood = mode(t, 420, 0.05, 0.5) + mode(t, 690, 0.03, 0.3)
    place(x, ring * 0.6 + tap * 0.5 + wood, 0.0)
    # it settles: a second, smaller touch
    place(x, (ring * 0.25 + wood * 0.4)[:int(0.3 * SR)], 0.045)
    return fade(x, 0.0005, 0.1)


def cloak_coat() -> np.ndarray:
    r = rng('cloak_coat')
    x = np.zeros(int(0.8 * SR))
    t = t_axis(0.12)
    scrape = band(r.standard_normal(int(0.1 * SR)), 1500, 6000) * np.hanning(int(0.1 * SR))
    place(x, scrape, 0.0, 0.35)
    clack = mode(t, 640, 0.05, 0.6) + mode(t, 1180, 0.03, 0.35) + band(r.standard_normal(len(t)), 800, 5000) * np.exp(-t / 0.003)
    place(x, clack, 0.09, 0.8)
    n = int(0.55 * SR)
    rustle = band(r.standard_normal(n), 400, 3500)
    rustle *= np.hanning(n) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 9, n))))
    place(x, rustle, 0.16, 0.45)
    return fade(x, 0.002, 0.1)


def cloak_hat() -> np.ndarray:
    r = rng('cloak_hat')
    x = np.zeros(int(0.45 * SR))
    t = t_axis(0.2)
    thump = mode(t, 140, 0.09, 0.8) + mode(t, 230, 0.05, 0.4)
    thump += band(r.standard_normal(len(t)), 150, 1200) * np.exp(-t / 0.02) * 0.5
    place(x, thump, 0.0)
    n = int(0.3 * SR)
    brush = band(r.standard_normal(n), 900, 4500) * np.hanning(n)
    place(x, brush, 0.08, 0.25)
    return fade(x, 0.001, 0.08)


def cloak_bell() -> np.ndarray:
    x = np.zeros(int(1.6 * SR))
    t = t_axis(1.55)
    f0 = 2093.0
    y = (mode(t, f0, 1.3, 1.0) + mode(t, f0 * 2.43, 0.7, 0.45) + mode(t, f0 * 3.91, 0.35, 0.25)
         + mode(t, f0 * 0.5, 0.5, 0.15) + mode(t, f0 * 5.4, 0.15, 0.1))
    beat = 1.0 + 0.06 * np.sin(2 * math.pi * 3.1 * t)
    strike = band(rng('bell').standard_normal(len(t)), 2000, 9000) * np.exp(-t / 0.002)
    place(x, y * beat + strike * 0.4, 0.0)
    return fade(x, 0.0005, 0.25)


def main(argv) -> None:
    out = [write_wav('mg_flap_clack_%d' % (i + 1), flap_clack(i), peak_db=-6.0) for i in range(4)]
    out += [write_wav('mg_flap_turn', flap_turn(), peak_db=-9.0),
            write_wav('mg_flap_rattle', flap_rattle(), peak_db=-5.0),
            write_wav('mg_flap_engage', flap_engage(), peak_db=-4.0),
            write_wav('mg_cloak_token', cloak_token(), peak_db=-7.0),
            write_wav('mg_cloak_coat', cloak_coat(), peak_db=-6.0),
            write_wav('mg_cloak_hat', cloak_hat(), peak_db=-7.0),
            write_wav('mg_cloak_bell', cloak_bell(), peak_db=-8.0)]
    for p in out:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main(sys.argv[1:])
