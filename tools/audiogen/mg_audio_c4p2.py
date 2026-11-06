"""mg_audio_c4p2 -- original synthesized sounds for the two mini-games of Chapter 4 part 2 (owner: exploration c4p2,
TECHNICAL_ARCHITECTURE §12.8, documentation/C4P2_DESIGN.md §6).

Run:  py -3 -P tools/audiogen/mg_audio_c4p2.py        (numpy only, deterministic, no samples, no network)

Writes assets/audio/sfx/ (44.1 kHz, 16-bit, mono):
„Die Drehscheibe“ (the 30-m turntable at the Karsk depot):
  mg_c4p2_tt_start    the controller notched up: a contactor clacks in, the old motor's hum rises under the bridge
  mg_c4p2_tt_brake    the band brake bites: a short hiss of air, iron grinding on iron, a thin squeal that dies away
  mg_c4p2_tt_bump     a refused pull: the engine eases forward, a wheel flange knocks against the rail edge, the
                      buffers clank and the engine rolls back a hand's width -- dull iron, never a buzzer
  mg_c4p2_tt_lock     stall 7: the locking bolt drops into its seat, the engine rolls off the bridge over the rail
                      joint (two knocks), a chuff of steam, the wooden stall gates swing shut
  mg_c4p2_tt_roll     a seamless 2-s loop (RIFF 'smpl' chunk): the bridge's wheels on the circular running rail, a low
                      rumble with rail-joint ticks; the game sets its volume by the bridge's speed
„Die Gepäckwaage“ (the decimal scale at the baggage counter of the Ostbahnhof):
  mg_c4p2_poise_coarse  the big sliding weight lifted over into the next notch: brass on steel, a heavy click
  mg_c4p2_poise_fine    the small weight one step along its rail: a light, bright tick
  mg_c4p2_beam_knock    the beam's tongue knocks against its stop in the frame
  mg_c4p2_stamp         the clerk's rubber stamp: a breath on the ink pad, a firm thump on the slip
Run with sound names as arguments to write only those. Shared DSP helpers come from tools/audiogen/mg_audio_r7_v.py.
"""
from __future__ import annotations

import os
import struct
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


def _thump(f: float, amp: float, decay: float = 0.09, sec: float = 0.45) -> np.ndarray:
    t = A.t_axis(sec)
    return A.mode(t, f, decay, amp) + A.mode(t, f * 2.1, decay * 0.6, amp * 0.45) + A.mode(t, f * 3.6, decay * 0.3, amp * 0.2)


def _knock(r, f: float, amp: float) -> np.ndarray:
    """Iron on iron: a short inharmonic ring with a dull body."""
    t = A.t_axis(0.25)
    ring = A.mode(t, f, 0.06, amp) + A.mode(t, f * 2.76, 0.035, amp * 0.5) + A.mode(t, f * 5.4, 0.02, amp * 0.25)
    return ring + _noise(r, 0.25, 200, 2500, 0.02) * amp * 0.5 + _thump(f * 0.35, amp * 0.6, 0.05, 0.25)


def tt_start() -> np.ndarray:
    r = A.rng('mg_c4p2_tt_start')
    x = np.zeros(int(0.8 * SR))
    A.place(x, _click(r, 1500, 0.9), 0.0)                       # the contactor
    A.place(x, _click(r, 1100, 0.6), 0.012)
    n = int(0.75 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.25, 1.0) * np.exp(-np.maximum(t - 0.45, 0.0) / 0.12)
    f = 48.0 + 22.0 * np.minimum(t / 0.5, 1.0)                  # the motor runs up
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = (np.sin(ph) * 0.5 + np.sin(2 * ph) * 0.3 + np.sin(3 * ph) * 0.12) * env
    grit = A.band(r.standard_normal(n), 90, 700) * env * 0.25
    A.place(x, hum + grit, 0.03)
    return A.fade(x, 0.001, 0.15)


def tt_brake() -> np.ndarray:
    r = A.rng('mg_c4p2_tt_brake')
    x = np.zeros(int(0.9 * SR))
    A.place(x, _noise(r, 0.12, 900, 6000, 0.05), 0.0, 0.5)      # the air valve
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.04, 1.0) * np.exp(-t / 0.32)
    grind = A.band(r.standard_normal(n), 250, 3200) * env * 0.7
    vib = 2200.0 + 60.0 * np.sin(2 * np.pi * 7.0 * t) - 500.0 * t
    squeal = np.sin(2 * np.pi * np.cumsum(vib) / SR) * env * 0.22
    A.place(x, grind + squeal, 0.05)
    A.place(x, _thump(70, 0.35, 0.1), 0.06)
    return A.fade(x, 0.001, 0.2)


def tt_bump() -> np.ndarray:
    r = A.rng('mg_c4p2_tt_bump')
    x = np.zeros(int(0.8 * SR))
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    roll = A.band(r.standard_normal(n), 60, 400) * np.minimum(t / 0.1, 1.0) * 0.4
    A.place(x, roll, 0.0)                                       # the engine eases forward
    A.place(x, _knock(r, 330, 1.0), 0.2)                        # the flange against the rail edge
    A.place(x, _knock(r, 210, 0.6), 0.27)                       # the buffers clank
    n2 = int(0.35 * SR)
    t2 = np.arange(n2) / SR
    back = A.band(r.standard_normal(n2), 50, 300) * np.exp(-t2 / 0.15) * 0.35
    A.place(x, back, 0.32)                                      # it rolls back a hand's width
    return A.fade(x, 0.001, 0.12)


def tt_lock() -> np.ndarray:
    r = A.rng('mg_c4p2_tt_lock')
    x = np.zeros(int(2.0 * SR))
    A.place(x, _click(r, 900, 0.7), 0.0)
    A.place(x, _thump(55, 1.0, 0.14, 0.6), 0.03)                # the bolt drops into its seat
    A.place(x, _knock(r, 260, 0.6), 0.04)
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.3, 1.0) * np.exp(-np.maximum(t - 0.7, 0.0) / 0.2)
    A.place(x, A.band(r.standard_normal(n), 45, 350) * env * 0.45, 0.35)   # rolling off the bridge
    for at in (0.62, 0.70, 0.98, 1.06):                        # the rail joint under both axles
        A.place(x, _knock(r, 190, 0.55), at)
    A.place(x, _noise(r, 0.35, 400, 5000, 0.12), 0.45, 0.35)    # a chuff of steam
    A.place(x, _thump(95, 0.55, 0.12), 1.55)                    # the wooden gates swing shut
    A.place(x, _thump(120, 0.4, 0.1), 1.63)
    A.place(x, _noise(r, 0.15, 150, 1800, 0.05), 1.55, 0.4)
    return A.fade(x, 0.001, 0.3)


def tt_roll() -> np.ndarray:
    """A seamless loop: the FFT band filter is circular, so filtered noise wraps without a seam; the joint ticks
    repeat every 0.5 s inside the 2-s period."""
    r = A.rng('mg_c4p2_tt_roll')
    n = int(2.0 * SR)
    rum = A.band(r.standard_normal(n), 35, 260) * 0.8
    hiss = A.band(r.standard_normal(n), 900, 4000) * 0.06
    x = rum + hiss
    for k in range(4):
        tick = _knock(r, 240 + 10 * k, 0.35)[: int(0.2 * SR)]
        A.place(x, tick, 0.12 + 0.5 * k)
    t = np.arange(n) / SR
    x += np.sin(2 * np.pi * 55.0 * t) * 0.12                    # 110 cycles in 2 s: periodic
    return x


def poise_coarse() -> np.ndarray:
    r = A.rng('mg_c4p2_poise_coarse')
    x = np.zeros(int(0.35 * SR))
    A.place(x, _noise(r, 0.06, 1500, 7000, 0.02), 0.0, 0.35)    # lifted out of the notch
    A.place(x, _knock(r, 1250, 0.8), 0.05)                      # and dropped into the next
    A.place(x, _thump(180, 0.35, 0.05), 0.05)
    return A.fade(x, 0.001, 0.06)


def poise_fine() -> np.ndarray:
    r = A.rng('mg_c4p2_poise_fine')
    x = np.zeros(int(0.12 * SR))
    A.place(x, _click(r, 3400, 0.8), 0.0)
    A.place(x, _noise(r, 0.05, 2000, 8000, 0.012), 0.0, 0.3)
    return A.fade(x, 0.001, 0.03)


def beam_knock() -> np.ndarray:
    r = A.rng('mg_c4p2_beam_knock')
    x = np.zeros(int(0.3 * SR))
    A.place(x, _knock(r, 760, 0.9), 0.0)
    return A.fade(x, 0.001, 0.08)


def stamp() -> np.ndarray:
    r = A.rng('mg_c4p2_stamp')
    x = np.zeros(int(0.5 * SR))
    A.place(x, _noise(r, 0.05, 600, 3000, 0.02), 0.0, 0.25)     # a breath on the ink pad
    A.place(x, _thump(110, 1.0, 0.07), 0.16)                    # the stamp on the slip, on the wooden counter
    A.place(x, _noise(r, 0.08, 300, 4000, 0.015), 0.16, 0.6)
    A.place(x, _click(r, 2600, 0.3), 0.17)
    return A.fade(x, 0.001, 0.1)


SOUNDS = (('mg_c4p2_tt_start', tt_start, -6.0, False), ('mg_c4p2_tt_brake', tt_brake, -6.0, False),
          ('mg_c4p2_tt_bump', tt_bump, -5.0, False), ('mg_c4p2_tt_lock', tt_lock, -4.0, False),
          ('mg_c4p2_tt_roll', tt_roll, -8.0, True),
          ('mg_c4p2_poise_coarse', poise_coarse, -6.0, False), ('mg_c4p2_poise_fine', poise_fine, -9.0, False),
          ('mg_c4p2_beam_knock', beam_knock, -8.0, False), ('mg_c4p2_stamp', stamp, -4.0, False))


def _add_loop_chunk(path: str) -> None:
    """Append a RIFF 'smpl' chunk with one forward loop over the whole file (Godot's importer detects it)."""
    with open(path, 'r+b') as f:
        data = f.read()
        n = (len(data) - 44) // 2
        smpl = struct.pack('<9I', 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack('<6I', 0, 0, 0, n - 1, 0, 0)
        data += b'smpl' + struct.pack('<I', len(smpl)) + smpl
        data = data[:4] + struct.pack('<I', len(data) - 8) + data[8:]
        f.seek(0)
        f.write(data)


def main(argv) -> None:
    """No arguments: every sound. Otherwise only the named ones."""
    for name, fn, db, loop in SOUNDS:
        if argv and name not in argv:
            continue
        p = A.write_wav(name, fn(), db)
        if loop:
            _add_loop_chunk(p)
        print('wrote', os.path.relpath(p, os.path.join(HERE, '..', '..')).replace('\\', '/'))


if __name__ == '__main__':
    main(sys.argv[1:])
