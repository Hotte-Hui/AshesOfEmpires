"""mg_audio_c3p2 -- original synthesized sounds for the Chapter-3 part-2 mini-game "Die Suchkartei"
(registry card hall, owner: exploration c3p2, TECHNICAL_ARCHITECTURE §12.8).

Run:  py -3 -P tools/audiogen/mg_audio_c3p2.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
  mg_c3p2_card_take    an index card lifted off the parquet: a dry paper flick and a short slide of card on wood
  mg_c3p2_card_file    the card slipped into the drawer between its neighbours: a papery hiss, then the soft tick
                       of the card settling on the rod
  mg_c3p2_rattle       a refused card: the drawer jolts on its runners, a dozen cards rattle once, the brass rod
                       rings quietly -- never a buzzer
  mg_c3p2_drawer_shut  the drawer slid home into its cabinet: a wooden rumble on the runners and a muffled knock
Shared DSP helpers come from tools/audiogen/mg_audio_r7_v.py (band, mode, place, fade, write_wav).
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_audio_r7_v as A  # noqa: E402

SR = A.SR


def paper(r, sec: float, lo: float, hi: float, decay: float) -> np.ndarray:
    t = A.t_axis(sec)
    return A.band(r.standard_normal(len(t)), lo, hi) * np.exp(-t / decay)


def card_take() -> np.ndarray:
    r = A.rng('mg_c3p2_card_take')
    x = np.zeros(int(0.22 * SR))
    A.place(x, paper(r, 0.03, 2500, 11000, 0.004), 0.0, 0.9)           # the flick
    n = int(0.14 * SR)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    slide = A.band(r.standard_normal(n), 900, 5200) * env               # card over wood
    A.place(x, slide, 0.02, 0.35)
    A.place(x, A.mode(A.t_axis(0.05), 420, 0.02, 0.25), 0.005)
    return A.fade(x, 0.0005, 0.03)


def card_file() -> np.ndarray:
    r = A.rng('mg_c3p2_card_file')
    x = np.zeros(int(0.3 * SR))
    n = int(0.13 * SR)
    env = np.linspace(0.2, 1.0, n) ** 2
    A.place(x, A.band(r.standard_normal(n), 1800, 9000) * env, 0.0, 0.45)   # sliding between the cards
    tick = A.mode(A.t_axis(0.08), 1250, 0.018, 0.5) + A.mode(A.t_axis(0.08), 2900, 0.01, 0.25) \
        + A.mode(A.t_axis(0.08), 330, 0.035, 0.6)
    A.place(x, tick, 0.13, 0.9)                                             # settling on the rod
    A.place(x, paper(r, 0.08, 1200, 6000, 0.003), 0.13, 0.9)
    return A.fade(x, 0.001, 0.05)


def rattle() -> np.ndarray:
    r = A.rng('mg_c3p2_rattle')
    x = np.zeros(int(0.45 * SR))
    jolt = A.mode(A.t_axis(0.2), 140, 0.08, 0.8) + A.mode(A.t_axis(0.2), 260, 0.05, 0.4)
    A.place(x, jolt, 0.0, 0.9)
    A.place(x, paper(r, 0.2, 200, 1500, 0.02), 0.0, 0.55)
    at = 0.012
    for i in range(12):                                                  # the cards rattle once
        A.place(x, paper(r, 0.02, 2000, 9000, 0.002), at, 0.5 - 0.03 * i)
        A.place(x, A.mode(A.t_axis(0.02), 1500 + 90 * i, 0.006, 0.2), at, 0.5 - 0.03 * i)
        at += 0.009 + 0.002 * r.random()
    A.place(x, A.mode(A.t_axis(0.3), 1960, 0.22, 0.12) + A.mode(A.t_axis(0.3), 3120, 0.15, 0.06), 0.04)  # the rod
    return A.fade(x, 0.0005, 0.08)


def drawer_shut() -> np.ndarray:
    r = A.rng('mg_c3p2_drawer_shut')
    sec = 0.75
    x = np.zeros(int(sec * SR))
    n = int(0.5 * SR)
    env = np.minimum(np.linspace(0, 1, n) * 3.0, 1.0) * np.linspace(1.0, 0.6, n)
    rumble = A.band(r.standard_normal(n), 60, 700) * env
    A.place(x, rumble, 0.0, 0.6)
    for k in range(6):                                                   # runner joints
        A.place(x, A.mode(A.t_axis(0.06), 180 + 15 * k, 0.03, 0.25), 0.06 + 0.07 * k)
    knock = A.mode(A.t_axis(0.25), 110, 0.12, 1.0) + A.mode(A.t_axis(0.25), 205, 0.08, 0.5)
    A.place(x, knock, 0.5, 1.0)
    A.place(x, paper(r, 0.05, 300, 3000, 0.01), 0.5, 0.4)
    A.place(x, A.mode(A.t_axis(0.2), 2100, 0.12, 0.1), 0.505)            # the rod's brass, once
    return A.fade(x, 0.002, 0.1)


def main(argv) -> None:
    for name, fn, db in (('mg_c3p2_card_take', card_take, -6.0), ('mg_c3p2_card_file', card_file, -5.0),
                         ('mg_c3p2_rattle', rattle, -6.0), ('mg_c3p2_drawer_shut', drawer_shut, -4.0)):
        p = A.write_wav(name, fn(), db)
        print('wrote', os.path.relpath(p, os.path.join(HERE, '..', '..')).replace('\\', '/'))


if __name__ == '__main__':
    main(sys.argv[1:])
