"""mg_audio_terminal -- original synthesized sounds of the data desk of Nebenstelle Sued (round 13, owner: terminal;
mini-games "Die Datenstelle" and "Planspiel Abgang", TECHNICAL_ARCHITECTURE §12.8).

Run:  py -3 -P tools/audiogen/mg_audio_terminal.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
  mg_term_hum        LOOP 2 s: the display unit at rest -- mains transformer (50 / 100 / 150 Hz), the cabinet fan as
                     periodic band noise, a faint deflection whine; every partial fits the loop, so it never clicks
  mg_term_relay      one relay: armature, contact bounce, a small body thump (menu steps, the beat of the posts)
  mg_term_key        one teleprinter key: type bar clack, the platen's thud, a short spring ring (digits)
  mg_term_ok         the number is accepted: a relay pulls, one clean 880 Hz tone, the relay drops
  mg_term_refuse     a refusal: a relay and a low, short mains buzzer (never a game-show buzzer)
  mg_term_tape       the release: two relays, the tape drive's motor running up, the reels' hiss settling
  mg_abgang_step     one step of the figure on the vector display: a dry tick of the deflection relay
  mg_abgang_seen     the post has seen the figure: a relay and a falling two-tone signal (660 -> 440 Hz)
  mg_abgang_through  a map is passed: three short rising pips
  mg_abgang_print    the run is over: the teleprinter hammers the result onto the strip, the margin bell
Run with sound names as arguments to write only those.
Shared DSP helpers: tools/audiogen/mg_audio_r7_v.py (band, mode, place, fade), the loop writer of mg_audio_r7_kb.py.
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_audio_r7_v as A  # noqa: E402
import mg_audio_r7_kb as KB  # noqa: E402

SR = A.SR


def _burst(r, sec: float, lo: float, hi: float, decay: float, amp: float = 1.0) -> np.ndarray:
    t = A.t_axis(sec)
    return A.band(r.standard_normal(t.size), lo, hi) * np.exp(-t / max(1e-4, decay)) * amp


def _relay(r, pitch: float = 1.0, amp: float = 1.0) -> np.ndarray:
    out = np.zeros(int(0.09 * SR))
    A.place(out, _burst(r, 0.02, 1800 * pitch, 7000, 0.0025), 0.0, amp)
    A.place(out, _burst(r, 0.015, 2500 * pitch, 9000, 0.0015), 0.011, amp * 0.55)      # contact bounce
    t = A.t_axis(0.07)
    A.place(out, A.mode(t, 190 * pitch, 0.018, 0.7) + A.mode(t, 520 * pitch, 0.01, 0.3), 0.001, amp)
    return out


def _square(t: np.ndarray, f: float, partials: int = 7) -> np.ndarray:
    y = np.zeros_like(t)
    for k in range(1, partials + 1, 2):
        y += np.sin(2 * np.pi * f * k * t) / k
    return y


def _tone(f: float, sec: float, attack: float = 0.008, release: float = 0.04) -> np.ndarray:
    t = A.t_axis(sec)
    env = np.minimum(t / attack, 1.0) * np.minimum((sec - t) / release, 1.0)
    return np.sin(2 * np.pi * f * t) * np.clip(env, 0.0, 1.0)


def hum() -> np.ndarray:
    r = A.rng('term_hum')
    n = 2 * SR
    t = np.arange(n) / SR
    y = 0.9 * np.sin(2 * np.pi * 50 * t) + 0.55 * np.sin(2 * np.pi * 100 * t + 0.7) + 0.22 * np.sin(2 * np.pi * 150 * t + 1.9)
    y += 0.08 * np.sin(2 * np.pi * 300 * t + 0.3)
    # the fan: noise built in the frequency domain, so it is periodic over the loop
    spec = np.zeros(n // 2 + 1, complex)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    mag = np.exp(-((np.log(np.maximum(f, 1.0)) - np.log(520.0)) ** 2) / 0.9)
    spec[:] = mag * np.exp(1j * r.uniform(0, 2 * np.pi, f.size))
    fan = np.fft.irfft(spec, n)
    y += 0.5 * fan / (np.max(np.abs(fan)) + 1e-9)
    y += 0.02 * np.sin(2 * np.pi * 3150 * t) * (1.0 + 0.3 * np.sin(2 * np.pi * 0.5 * t))
    return y


def relay() -> np.ndarray:
    return _relay(A.rng('term_relay'))


def key() -> np.ndarray:
    r = A.rng('term_key')
    out = np.zeros(int(0.14 * SR))
    A.place(out, _burst(r, 0.025, 2200, 9000, 0.003), 0.0, 1.0)
    t = A.t_axis(0.12)
    A.place(out, A.mode(t, 310, 0.022, 0.8) + A.mode(t, 1240, 0.012, 0.35) + A.mode(t, 2650, 0.02, 0.12), 0.002, 1.0)
    A.place(out, _burst(r, 0.03, 600, 2400, 0.008), 0.03, 0.25)                      # the bar falling back
    return out


def ok() -> np.ndarray:
    r = A.rng('term_ok')
    out = np.zeros(int(0.52 * SR))
    A.place(out, _relay(r, 1.0), 0.0, 0.9)
    A.place(out, _tone(880.0, 0.2), 0.09, 0.55)
    A.place(out, _relay(r, 0.85), 0.34, 0.7)
    return out


def refuse() -> np.ndarray:
    r = A.rng('term_refuse')
    out = np.zeros(int(0.38 * SR))
    A.place(out, _relay(r, 0.9), 0.0, 0.8)
    t = A.t_axis(0.24)
    env = np.minimum(t / 0.006, 1.0) * np.minimum((0.24 - t) / 0.05, 1.0)
    buzz = A.band(_square(t, 100.0, 9), 70, 1400) * env
    A.place(out, buzz, 0.05, 0.6)
    return out


def tape() -> np.ndarray:
    r = A.rng('term_tape')
    sec = 1.5
    out = np.zeros(int(sec * SR))
    A.place(out, _relay(r, 0.8), 0.0, 1.0)
    A.place(out, _relay(r, 1.1), 0.13, 0.8)
    t = A.t_axis(1.25)
    f = 55.0 + 185.0 * (1.0 - np.exp(-t / 0.35))                                     # the motor runs up
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(t / 0.05, 1.0) * np.minimum((1.25 - t) / 0.3, 1.0)
    motor = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * env * 0.5
    hiss = A.band(r.standard_normal(t.size), 1500, 6000) * env * (0.15 + 0.2 * np.minimum(t / 0.6, 1.0))
    wow = 1.0 + 0.25 * np.sin(2 * np.pi * 7.0 * t)
    A.place(out, motor + hiss * wow, 0.2, 1.0)
    return out


def step() -> np.ndarray:
    r = A.rng('abgang_step')
    out = np.zeros(int(0.06 * SR))
    A.place(out, _burst(r, 0.012, 2600, 8000, 0.0016), 0.0, 0.8)
    t = A.t_axis(0.05)
    A.place(out, A.mode(t, 1750, 0.007, 0.5) + A.mode(t, 420, 0.01, 0.3), 0.0, 1.0)
    return out


def seen() -> np.ndarray:
    r = A.rng('abgang_seen')
    out = np.zeros(int(0.66 * SR))
    A.place(out, _relay(r, 0.9), 0.0, 0.9)
    for f0, at, sec in ((660.0, 0.06, 0.2), (440.0, 0.28, 0.34)):
        t = A.t_axis(sec)
        env = np.minimum(t / 0.006, 1.0) * np.minimum((sec - t) / 0.06, 1.0)
        trem = 1.0 + 0.12 * np.sin(2 * np.pi * 18.0 * t)
        A.place(out, A.band(_square(t, f0, 7), 200, 5000) * env * trem, at, 0.5)
    return out


def through() -> np.ndarray:
    out = np.zeros(int(0.46 * SR))
    for i, f0 in enumerate((660.0, 880.0, 1320.0)):
        A.place(out, _tone(f0, 0.09, 0.004, 0.05), 0.02 + i * 0.13, 0.6)
    return out


def print_strip() -> np.ndarray:
    r = A.rng('abgang_print')
    sec = 1.9
    out = np.zeros(int(sec * SR))
    at = 0.03
    k = 0
    while at < 1.3:
        hit = _burst(r, 0.02, 2000, 9000, 0.0028)
        t = A.t_axis(0.06)
        body = A.mode(t, 300 + 25 * r.standard_normal(), 0.016, 0.7) + A.mode(t, 1180, 0.008, 0.25)
        gain = 0.75 + 0.25 * r.random()
        A.place(out, hit, at, gain)
        A.place(out, body, at + 0.001, gain)
        k += 1
        at += 0.062 + 0.012 * r.random() + (0.09 if k % 7 == 0 else 0.0)              # a word space now and then
    t = A.t_axis(1.5)
    carriage = A.band(r.standard_normal(t.size), 300, 1800) * 0.05 * np.minimum((1.5 - t) / 0.2, 1.0)
    A.place(out, carriage, 0.0, 1.0)
    tb = A.t_axis(0.55)
    bell = A.mode(tb, 2100, 0.16, 0.5) + A.mode(tb, 3370, 0.09, 0.2) + A.mode(tb, 5200, 0.05, 0.08)
    A.place(out, bell, 1.34, 0.8)
    return out


# name, generator, peak dB, loop
SOUNDS = [
    ('mg_term_hum', hum, -16.0, True),
    ('mg_term_relay', relay, -6.0, False),
    ('mg_term_key', key, -5.0, False),
    ('mg_term_ok', ok, -6.0, False),
    ('mg_term_refuse', refuse, -8.0, False),
    ('mg_term_tape', tape, -6.0, False),
    ('mg_abgang_step', step, -8.0, False),
    ('mg_abgang_seen', seen, -6.0, False),
    ('mg_abgang_through', through, -8.0, False),
    ('mg_abgang_print', print_strip, -5.0, False),
]


def main(argv) -> None:
    """No arguments: every sound. Otherwise only the named ones."""
    for name, fn, db, loop in SOUNDS:
        if argv and name not in argv:
            continue
        x = fn()
        if not loop:
            x = A.fade(x, 0.001, 0.012)
        p = KB.write_wav(name, x, loop=loop, peak_db=db)
        print('wrote', os.path.relpath(p, os.path.join(HERE, '..', '..')).replace('\\', '/'))


if __name__ == '__main__':
    main(sys.argv[1:])
