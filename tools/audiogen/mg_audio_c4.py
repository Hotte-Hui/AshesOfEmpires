"""mg_audio_c4 -- original synthesized sounds for the Chapter-4 mini-game "Der Hebelrahmen" (Service Tunnel 3 under
the Karsk freight yard, owner: exploration c4, TECHNICAL_ARCHITECTURE §12.8, documentation/C4_DESIGN.md §6).

Run:  py -3 -P tools/audiogen/mg_audio_c4.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
  mg_c4_lever_pull    a lever pulled over: the catch handle clicks out, iron slides in its quadrant, a heavy thump
                      as it lands in the reversed position, the locking bar behind the frame shifts with a dry rattle
  mg_c4_lever_back    a lever put back to normal: a shorter slide, a lower thump, the catch snapping home
  mg_c4_lever_locked  a refused lever: the catch handle is squeezed, the lever moves a finger's width and stops hard
                      against the locking bar -- a dull iron knock and a small rattle, never a buzzer
  mg_c4_route_set     an order carried out: the signal wire runs along the tunnel wall (a creaking pulley), the
                      signal arm drops far away, one stroke of the tunnel's small electric bell
and for "Die Lüftungsklappen" (machine room of Nebenstelle Süd, round-9 fix compl-01):
  mg_c4_flap_open     a flap handle one notch open: detent, the blade turning, a breath of air in the duct
  mg_c4_flap_close    a flap handle one notch shut: a lower notch, the air dropping away
  mg_c4_alarm_bell    the fault bell: an electric striker on a small steel gong and its ring-out
  mg_c4_air_settled   the fault acknowledged: the relay drops, a last tap on the gong, the fans settle
Run with sound names as arguments to write only those (py -3 -P tools/audiogen/mg_audio_c4.py mg_c4_flap_open ...).
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


def _noise(r, sec: float, lo: float, hi: float, decay: float) -> np.ndarray:
    t = A.t_axis(sec)
    return A.band(r.standard_normal(t.size), lo, hi) * np.exp(-t / max(1e-4, decay))


def _click(r, f: float, amp: float = 1.0) -> np.ndarray:
    t = A.t_axis(0.03)
    return (A.mode(t, f, 0.006, amp) + A.mode(t, f * 1.73, 0.004, amp * 0.5)) + _noise(r, 0.03, 2500, 9000, 0.003) * amp * 0.6


def _thump(f: float, amp: float, decay: float = 0.09) -> np.ndarray:
    t = A.t_axis(0.4)
    return A.mode(t, f, decay, amp) + A.mode(t, f * 2.1, decay * 0.6, amp * 0.45) + A.mode(t, f * 3.6, decay * 0.3, amp * 0.2)


def _slide(r, sec: float, lo: float, hi: float) -> np.ndarray:
    n = int(sec * SR)
    env = np.minimum(np.linspace(0, 1, n) * 4.0, 1.0) * np.linspace(1.0, 0.5, n)
    grit = A.band(r.standard_normal(n), lo, hi) * env
    t = np.arange(n) / SR
    whine = np.sin(2 * np.pi * (520 + 140 * t / max(1e-3, sec)) * t) * env * 0.08
    return grit + whine


def _rattle(r, n_hits: int, f0: float, amp: float) -> np.ndarray:
    x = np.zeros(int(0.25 * SR))
    at = 0.0
    for i in range(n_hits):
        A.place(x, A.mode(A.t_axis(0.04), f0 + 70 * i + 40 * r.random(), 0.012, amp * (1.0 - 0.12 * i)), at)
        at += 0.012 + 0.006 * r.random()
    return x


def lever_pull() -> np.ndarray:
    r = A.rng('mg_c4_lever_pull')
    x = np.zeros(int(0.7 * SR))
    A.place(x, _click(r, 2300, 0.7), 0.0)                       # catch handle squeezed
    A.place(x, _slide(r, 0.22, 300, 2600), 0.02, 0.5)           # iron in the quadrant
    A.place(x, _thump(72, 1.0), 0.24)                           # lands in the reversed position
    A.place(x, _noise(r, 0.12, 150, 1200, 0.03), 0.24, 0.5)
    A.place(x, _rattle(r, 5, 900, 0.35), 0.27)                  # the locking bar shifts behind the frame
    A.place(x, _click(r, 1900, 0.8), 0.33)                      # catch snaps into the notch
    return A.fade(x, 0.001, 0.12)


def lever_back() -> np.ndarray:
    r = A.rng('mg_c4_lever_back')
    x = np.zeros(int(0.6 * SR))
    A.place(x, _click(r, 2100, 0.6), 0.0)
    A.place(x, _slide(r, 0.16, 250, 2000), 0.02, 0.45)
    A.place(x, _thump(58, 0.95, 0.11), 0.18)
    A.place(x, _rattle(r, 4, 760, 0.3), 0.2)
    A.place(x, _click(r, 1700, 0.75), 0.25)
    return A.fade(x, 0.001, 0.12)


def lever_locked() -> np.ndarray:
    r = A.rng('mg_c4_lever_locked')
    x = np.zeros(int(0.42 * SR))
    A.place(x, _click(r, 2200, 0.5), 0.0)
    A.place(x, _slide(r, 0.05, 400, 2400), 0.015, 0.35)
    knock = A.mode(A.t_axis(0.3), 180, 0.05, 1.0) + A.mode(A.t_axis(0.3), 410, 0.035, 0.6) + \
        A.mode(A.t_axis(0.3), 1260, 0.02, 0.25)
    A.place(x, knock, 0.06)                                     # hard stop against the locking bar
    A.place(x, _noise(r, 0.06, 300, 3000, 0.012), 0.06, 0.45)
    A.place(x, _rattle(r, 3, 1400, 0.2), 0.08)
    return A.fade(x, 0.001, 0.1)


def route_set() -> np.ndarray:
    r = A.rng('mg_c4_route_set')
    sec = 1.6
    x = np.zeros(int(sec * SR))
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.05, 1.0) * np.exp(-t / 0.4)
    wire = A.band(r.standard_normal(n), 900, 4200) * env * 0.35          # the signal wire along the wall
    squeak = np.sin(2 * np.pi * (1100 + 220 * np.sin(2 * np.pi * 3.0 * t)) * t) * env * 0.12
    A.place(x, wire + squeak, 0.0)
    for k in range(4):                                                  # pulleys
        A.place(x, A.mode(A.t_axis(0.05), 1500 - 120 * k, 0.015, 0.18), 0.06 + 0.09 * k)
    A.place(x, _thump(48, 0.35, 0.15), 0.5)                             # the arm drops, far away
    bell = A.mode(A.t_axis(1.0), 1318, 0.55, 0.55) + A.mode(A.t_axis(1.0), 2637, 0.3, 0.2) + \
        A.mode(A.t_axis(1.0), 3550, 0.18, 0.1)
    A.place(x, bell, 0.62)                                              # one stroke of the tunnel bell
    return A.fade(x, 0.002, 0.25)


# ----------------------------------------------------------------------------- "Die Lüftungsklappen" (annex, scene D)
def _air(r, sec: float, lo: float, hi: float, rise: float, fall: float) -> np.ndarray:
    n = int(sec * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / max(1e-3, rise), 1.0) * np.exp(-t / max(1e-3, fall))
    return A.band(r.standard_normal(n), lo, hi) * env


def flap_open() -> np.ndarray:
    """A flap handle moved one notch open: the detent lifts, the blade turns in the duct, a breath of air."""
    r = A.rng('mg_c4_flap_open')
    x = np.zeros(int(0.62 * SR))
    A.place(x, _click(r, 2400, 0.65), 0.0)                      # the detent lifts
    A.place(x, _slide(r, 0.1, 600, 2800), 0.01, 0.4)            # the handle in its quadrant
    A.place(x, _thump(150, 0.45, 0.05), 0.11)                   # the next notch
    A.place(x, _click(r, 1900, 0.55), 0.115)
    A.place(x, _air(r, 0.45, 280, 1900, 0.09, 0.2), 0.12, 0.45)  # more air rushes through the duct
    return A.fade(x, 0.001, 0.1)


def flap_close() -> np.ndarray:
    """A flap handle moved one notch shut: a lower notch, the air in the duct drops away."""
    r = A.rng('mg_c4_flap_close')
    x = np.zeros(int(0.55 * SR))
    A.place(x, _click(r, 2100, 0.6), 0.0)
    A.place(x, _slide(r, 0.09, 450, 2200), 0.01, 0.38)
    A.place(x, _thump(110, 0.5, 0.06), 0.1)
    A.place(x, _click(r, 1600, 0.5), 0.105)
    A.place(x, _air(r, 0.3, 200, 1100, 0.01, 0.07), 0.1, 0.3)  # a short sigh as the duct narrows
    return A.fade(x, 0.001, 0.1)


def alarm_bell() -> np.ndarray:
    """The machine room's fault bell: an electric striker at ~21 Hz on a small steel gong, then the ring-out."""
    r = A.rng('mg_c4_alarm_bell')
    x = np.zeros(int(1.6 * SR))
    strike = A.mode(A.t_axis(0.12), 1175, 0.09, 0.55) + A.mode(A.t_axis(0.12), 2938, 0.05, 0.22) + \
        A.mode(A.t_axis(0.12), 4105, 0.025, 0.1)
    at = 0.0
    while at < 1.1:
        A.place(x, strike, at, 0.85 + 0.15 * r.random())
        A.place(x, _click(r, 5200, 0.1), at)
        at += 1.0 / 21.0 + 0.002 * r.random()
    ring = A.mode(A.t_axis(0.5), 1175, 0.32, 0.45) + A.mode(A.t_axis(0.5), 2938, 0.14, 0.12)
    A.place(x, ring, 1.1)
    return A.fade(x, 0.002, 0.15)


def air_settled() -> np.ndarray:
    """The fault acknowledged: the relay drops, one last tap on the gong, the fans settle into an even breath."""
    r = A.rng('mg_c4_air_settled')
    x = np.zeros(int(1.5 * SR))
    A.place(x, _click(r, 3100, 0.8), 0.0)                       # the relay drops
    A.place(x, _thump(90, 0.4, 0.07), 0.01)
    A.place(x, A.mode(A.t_axis(0.8), 1175, 0.45, 0.35) + A.mode(A.t_axis(0.8), 2938, 0.2, 0.1), 0.06)
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.3, 1.0) * np.exp(-t / 0.7)
    hum = (np.sin(2 * np.pi * 49 * t) * 0.25 + np.sin(2 * np.pi * 98 * t) * 0.12) * env
    A.place(x, A.band(r.standard_normal(n), 120, 900) * env * 0.35 + hum, 0.15)
    return A.fade(x, 0.002, 0.3)


SOUNDS = (('mg_c4_lever_pull', lever_pull, -4.0), ('mg_c4_lever_back', lever_back, -5.0),
          ('mg_c4_lever_locked', lever_locked, -6.0), ('mg_c4_route_set', route_set, -6.0),
          ('mg_c4_flap_open', flap_open, -6.0), ('mg_c4_flap_close', flap_close, -6.0),
          ('mg_c4_alarm_bell', alarm_bell, -5.0), ('mg_c4_air_settled', air_settled, -6.0))


def main(argv) -> None:
    """No arguments: every sound. Otherwise only the named ones (e.g. the four of the flaps)."""
    for name, fn, db in SOUNDS:
        if argv and name not in argv:
            continue
        p = A.write_wav(name, fn(), db)
        print('wrote', os.path.relpath(p, os.path.join(HERE, '..', '..')).replace('\\', '/'))


if __name__ == '__main__':
    main(sys.argv[1:])
