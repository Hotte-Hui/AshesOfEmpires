"""c4p2_cine_audio -- original synthesised sound for the five Chapter-4-part-2 cinematics (owner: cine stream, round 10).

Self-contained numpy synthesis on the helpers of tools/audiogen/c3_cine_audio.py (band-pass, envelopes, panning,
generated rooms, WAV writer, knocks, chuffs, clinks), c3p2_cine_audio.py (snow crunch, creaks, wind, metal hits,
crackles, wordless babble) and c4_cine_audio.py (steps, door slams, whistles, thumps, paper) -- all imported
read-only.  Deterministic (seeds = crc32 of the sound's name), 44.1 kHz / 16-bit, nothing sampled or downloaded.
Writes assets/audio/sfx/c4p2cine_*.wav.  Every bed starts where its shot starts (the film cues it there); the
events inside are cut at the FILM times the pictures use (scenes/cinematics/ch4p2_*/; checked by
tests/test_c4p2_cinematics.gd), each bed subtracting its own start:

  LS_C4P2_Depot   depot (0.0: wind, the barrel fire, every shovel of Kolonne 4 biting at its contact frame -- the
                  layout's cycle phases -- and its coal landing in the wagon, the stall engine's valve at VALVE_LIFT),
                  arch (5.0: Alexei's boots on frozen cinders at ALEXEI_STEPS, a hammer on steel in the stall, the
                  roundhouse's hiss), window (9.0: wind on the glass, the samovar, ONE ring of the telephone at
                  PHONE_RING, muffled by the double window)
  LS_C4P2_Steam   coal (0.0: coal down the chute over COAL_RUN into the tender, the tarpaulin cracking taut at
                  TARP_SNAPS), jet (4.0: ONE hiss across the cut -- open air, then from CUT on the glass hall's
                  echo), hall (5.5: the hall, the split-flap board running at FLAP_T, an announcement, pigeons, a
                  luggage cart, Konrad's steps at KONRAD_M4)
  LS_C4P2_Book    dining (0.0: cutlery, the onion-skin paper and the card sliding over SLIDE_T, the pages lifting at
                  CLOSE_T), shut (3.5: the soft thud at BOOK_SHUT), canteen (5.0: the cover leaving the page block at
                  BOOK_OPEN, tea glasses, the canteen), band (MARCH_T0: the works band's march -- an original 2/4 tune,
                  the bass drum on the picture's beat -- and the match at MATCH_STRIKE)
  LS_C4P2_Express express (0.0: the whistle at WHISTLE, the brakes off at BRAKE_OFF, the couplings taking up slack
                  at COUPLINGS, the first exhaust beats), recede (4.0: wheels fading, the band's cases), knock (8.0:
                  one last rail joint at KNOCK_T, then quiet), street (9.5: the coat's swish over WIPE, Konrad's steps
                  in snow at KONRAD_STEPS, the S-Bahn over SBAHN_T, a radio behind a window, wind in the passage)
  LS_C4P2_Clock   k14 (0.0: two car doors at CAR_DOORS, the engine at ENGINE_T, the car rolling out through the gate
                  passage over CAR_T), kordon_publish / kordon_protect (5.0: the plain's wind and the floodlights' hum;
                  the flashbulb at FLASH_T and far voices -- or the heavy door at DOOR_OPEN / DOOR_SHUT),
                  tty_publish / tty_protect (11.0: the teleprinter's keys on every character from TYPE_T0 at
                  TYPE_CPS), desk (16.0: the lamp's hum, a spoon), tick (0.0: the stand-in clock tick when the music
                  is missing -- one per second, the last before TICK_END)

Run:  py -3 -P tools/audiogen/c4p2_cine_audio.py [--only name,name]   (then the shared --import)
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import c3_cine_audio as A  # noqa: E402  (read-only)
import c3p2_cine_audio as B  # noqa: E402  (read-only)
import c4_cine_audio as C4  # noqa: E402  (read-only)

SR = A.SR
n_of, band, lp, hp, decay, place, pan, fades, norm, room, rng = (
    A.n_of, A.band, A.lp, A.hp, A.decay, A.place, A.pan, A.fades, A.norm, A.room, A.rng)

# ---------------------------------------------------------------------------------------- times (FILM time)
# Depot (ch4p2_depot.gd; the shovel bites come from assets/cinematics/c4p2/layout.json depot.bites / p1_gang)
VALVE_LIFT = 2.6
ALEXEI_STEPS = (5.0, 5.4, 5.8, 6.2, 6.6, 7.0, 7.4, 7.8, 8.2, 8.6)
PHONE_RING = 10.2
# Steam (ch4p2_steam.gd)
COAL_RUN = (0.25, 3.7)
TARP_SNAPS = (1.55, 3.05)
JET_T0 = 4.0
CUT = 5.5
FLAP_T = (6.85, 7.95)
KONRAD_M4 = (9.5, 9.9, 10.3, 10.7, 11.1, 11.5, 11.9)
# Book (ch4p2_book.gd)
SLIDE_T = (0.3, 1.5)
CLOSE_T = (2.6, 3.5)
BOOK_SHUT = 4.15
BOOK_OPEN = 5.12
MARCH_T0 = 9.15
MARCH_BPM = 112.0
MATCH_STRIKE = 10.05
# Express (ch4p2_express.gd)
WHISTLE = 0.3
BRAKE_OFF = 0.9
COUPLINGS = (1.02, 1.24, 1.47, 1.73)
KNOCK_T = 8.4
WIPE = (10.25, 10.7)
KONRAD_STEPS = (10.475, 10.875, 11.275, 11.675, 12.075, 12.475, 12.875)
SBAHN_T = (10.9, 12.6)
# Clock (ch4p2_clock.gd; the teleprinter's characters from layout.json clock.text)
CAR_DOORS = (0.3, 0.55)
ENGINE_T = 0.75
CAR_T = (0.9, 3.4)
FLASH_T = 7.35
DOOR_OPEN = 6.2
DOOR_SHUT = 9.7
TYPE_T0 = 11.6
TYPE_CPS = 7.0
TICK_END = 20.0


def layout():
    p = os.path.join(ROOT, 'assets', 'cinematics', 'c4p2', 'layout.json')
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def write(name, x):
    return A.write(name, x)


def st(sec):
    return np.zeros((n_of(sec), 2))


def at(x, t, start):
    """Place-time of film time t in a bed that starts at film time `start`."""
    return t - start


# ---------------------------------------------------------------------------------------- elements
def shovel_bite(r, gain=1.0):
    """A shovel driven into heaped coal: a gritty scrape and the blade's ring."""
    m = n_of(0.24)
    t = np.arange(m) / SR
    grit = band(r.standard_normal(m), 900, 5200) * decay(m, 0.06, 0.006) * (0.6 + 0.4 * np.abs(r.standard_normal(m)))
    ring = (np.sin(2 * np.pi * 1180 * t) * 0.3 + np.sin(2 * np.pi * 2430 * t) * 0.15) * decay(m, 0.05, 0.001)
    thud = lp(r.standard_normal(m), 300) * decay(m, 0.03, 0.002) * 0.6
    return (grit + ring + thud) * gain


def coal_land(r, gain=1.0, metal=False, n=14):
    """A shovelful of coal landing: a spray of small hard impacts over ~0.3 s (on steel: a dull boom too)."""
    m = n_of(0.5)
    x = np.zeros(m)
    for i in range(n):
        tt = abs(r.normal(0.06, 0.06))
        L = n_of(0.03)
        c = band(r.standard_normal(L), 1400, 6500) * decay(L, 0.006, 0.0004) * r.uniform(0.3, 1.0)
        place(x, c, tt)
    if metal:
        t = np.arange(m) / SR
        x += np.sin(2 * np.pi * 96 * t) * decay(m, 0.12, 0.004) * 0.5
    return x * gain


def valve(r, sec, f_tone=2850.0, gain=1.0, attack=0.08):
    """A safety valve blowing off: a roaring white hiss with a resonant scream in it."""
    m = n_of(sec)
    t = np.arange(m) / SR
    env = np.clip(t / attack, 0, 1) * np.clip((sec - t) / 0.35, 0, 1)
    x = band(r.standard_normal(m), 900, 9000) * 0.8 + band(r.standard_normal(m), 250, 1100) * 0.5
    x += band(r.standard_normal(m), f_tone * 0.93, f_tone * 1.07, 0.1) * 1.6
    flutter = 1 + 0.12 * np.sin(2 * np.pi * 7.3 * t) * r.uniform(0.6, 1.0)
    return x * env * flutter * gain


def phone_ring(r, sec=1.15, gain=1.0):
    """An old desk telephone: the clapper hammering two bells (~22 Hz) for one ring."""
    m = n_of(sec)
    x = np.zeros(m)
    tt = 0.0
    k = 0
    while tt < sec - 0.25:
        f0 = 1960.0 if k % 2 == 0 else 2410.0
        L = n_of(0.3)
        t = np.arange(L) / SR
        s = (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.7 * t)) * decay(L, 0.08, 0.0006)
        place(x, s * 0.5, tt)
        tt += 1 / 22.0
        k += 1
    return x * gain


def simmer(r, sec, gain=1.0):
    """A samovar on the boil: low rolling bubbles and a soft hiss."""
    m = n_of(sec)
    x = band(r.standard_normal(m), 120, 900) * 0.15
    tt = 0.0
    while tt < sec:
        L = n_of(0.05)
        t = np.arange(L) / SR
        f = r.uniform(180, 420)
        place(x, np.sin(2 * np.pi * f * t * (1 + 2 * t)) * decay(L, 0.015, 0.002) * r.uniform(0.2, 0.6), tt)
        tt += r.uniform(0.03, 0.12)
    return x * gain


def snap(r, gain=1.0):
    """Canvas cracking taut in the wind: a low whump and a sharp flap."""
    m = n_of(0.4)
    t = np.arange(m) / SR
    x = lp(r.standard_normal(m), 260) * decay(m, 0.05, 0.004) * 1.2
    x += band(r.standard_normal(m), 500, 4000) * decay(m, 0.012, 0.001) * 0.9
    x += np.sin(2 * np.pi * 70 * t) * decay(m, 0.06, 0.003) * 0.5
    return x * gain


def flap_run(r, sec, rate=34.0, gain=1.0):
    """The split-flap board: a clatter of flaps falling, slowing toward the end."""
    x = np.zeros(n_of(sec))
    tt = 0.0
    while tt < sec - 0.05:
        L = n_of(0.012)
        c = band(r.standard_normal(L), 1100, 4200) * decay(L, 0.0025, 0.0003)
        c += np.sin(2 * np.pi * 2750 * np.arange(L) / SR) * decay(L, 0.003, 0.0003) * 0.3
        place(x, c * r.uniform(0.5, 1.0), tt)
        tt += 1.0 / rate * r.uniform(0.7, 1.3)
        rate *= 0.985
    return x * gain


def brass(f, sec, r, bright=1.0, vib=5.5):
    """One brass note: harmonics with a bright attack ('blat'), a little vibrato, breath noise."""
    m = n_of(sec)
    t = np.arange(m) / SR
    fv = f * (1 + 0.004 * np.sin(2 * np.pi * vib * t) * np.clip(t / 0.25, 0, 1))
    ph = np.cumsum(fv / SR) * 2 * np.pi
    x = np.zeros(m)
    for k in range(1, 12):
        amp = (1.0 / k ** 1.1) * (1 + bright * 0.6 * np.exp(-t / 0.05) * (k > 3))
        x += np.sin(ph * k) * amp
    env = np.clip(t / 0.025, 0, 1) * np.clip((sec - t) / 0.06, 0, 1)
    x += band(r.standard_normal(m), f * 2, f * 6) * 0.05
    return x * env


def drum(r, kind='bass', gain=1.0):
    m = n_of(0.5)
    t = np.arange(m) / SR
    if kind == 'bass':
        x = np.sin(2 * np.pi * 62 * t * (1 - 0.25 * t)) * decay(m, 0.16, 0.002) + lp(r.standard_normal(m), 400) * decay(m, 0.03, 0.001) * 0.6
    else:
        x = band(r.standard_normal(m), 1500, 7000) * decay(m, 0.07, 0.001) * 0.7 + np.sin(2 * np.pi * 220 * t) * decay(m, 0.03, 0.001) * 0.4
    return x * gain


def march(sec, r):
    """An original works-band march (2/4, 112 bpm, B-flat major): cornets on the tune, a tenor horn below, the
    helicon on the beats, bass drum on 1, snare on the off-beats; it ends on the tonic as the film ends."""
    beat = 60.0 / MARCH_BPM
    hz = lambda n: 440.0 * 2 ** ((n - 69) / 12.0)  # noqa: E731
    # (start in beats, length in beats, midi)
    tune = [(0, 0.5, 65), (0.5, 0.5, 70), (1, 0.75, 74), (1.75, 0.25, 72), (2, 0.5, 74), (2.5, 0.5, 77),
            (3, 1.0, 74), (4, 0.5, 72), (4.5, 0.5, 69), (5, 0.5, 65), (5.5, 0.5, 69), (6, 0.5, 72), (6.5, 0.25, 70),
            (6.75, 0.25, 69), (7, 0.5, 67), (7.5, 0.5, 70), (8, 1.4, 70)]
    harm = [(0, 1, 62), (1, 1, 65), (2, 1, 65), (3, 1, 65), (4, 1, 63), (5, 1, 60), (6, 1, 63), (7, 1, 62),
            (8, 1.4, 62)]
    bass = [(0, 0.5, 46), (1, 0.5, 41), (2, 0.5, 46), (3, 0.5, 41), (4, 0.5, 48), (5, 0.5, 41), (6, 0.5, 39),
            (7, 0.5, 41), (8, 1.2, 46)]
    m = n_of(sec)
    L = np.zeros(m)
    Rr = np.zeros(m)
    for (b0, bl, nn) in tune:
        s = brass(hz(nn), bl * beat * 0.92, r, 1.0)
        place(L, s * 0.30, b0 * beat)
        place(Rr, s * 0.24, b0 * beat + 0.004)
    for (b0, bl, nn) in harm:
        s = brass(hz(nn), bl * beat * 0.9, r, 0.6)
        place(L, s * 0.14, b0 * beat)
        place(Rr, s * 0.18, b0 * beat)
    for (b0, bl, nn) in bass:
        s = lp(brass(hz(nn), bl * beat * 0.85, r, 0.3), 900)
        place(L, s * 0.32, b0 * beat)
        place(Rr, s * 0.36, b0 * beat)
    for k in range(9):
        place(L, drum(r, 'bass', 0.55), k * beat)
        place(Rr, drum(r, 'bass', 0.55), k * beat)
        if k < 8:
            place(L, drum(r, 'snare', 0.22), (k + 0.5) * beat)
            place(Rr, drum(r, 'snare', 0.26), (k + 0.5) * beat)
    x = np.stack([L, Rr], 1)
    return x


def match_strike(r, gain=1.0):
    m = n_of(0.7)
    t = np.arange(m) / SR
    scratch = band(r.standard_normal(m), 1800, 9000) * np.clip(1 - t / 0.08, 0, 1) * (t < 0.08) * 1.2
    flare = band(r.standard_normal(m), 300, 4000) * decay(m, 0.18, 0.02) * 0.6 * (t > 0.06)
    return (scratch + flare) * gain


def coupling(r, gain=1.0):
    m = n_of(0.6)
    t = np.arange(m) / SR
    x = B.metal_hit(r, (180, 430, 960, 1700), 0.22, 1.0, 0.6)[:m]
    x += lp(r.standard_normal(m), 400) * decay(m, 0.05, 0.002) * 0.7
    return x * gain


def air_release(r, sec=0.7, gain=1.0):
    m = n_of(sec)
    t = np.arange(m) / SR
    return band(r.standard_normal(m), 1200, 9000) * np.clip(t / 0.04, 0, 1) * np.exp(-t / 0.3) * gain


def car_door(r, gain=1.0):
    m = n_of(0.8)
    t = np.arange(m) / SR
    x = lp(r.standard_normal(m), 350) * decay(m, 0.06, 0.002) * 1.3 + np.sin(2 * np.pi * 110 * t) * decay(m, 0.09, 0.002)
    x += B.metal_hit(r, (420, 980, 1720), 0.08, 0.35, 0.8)[:m]
    return x * gain


def engine(r, sec, rpm0=700.0, rpm1=1400.0, t_rev=(0.4, 1.6), gain=1.0):
    """A 1960s six-cylinder: firing pulses (rpm/120*6 Hz), exhaust burble, revving between t_rev."""
    m = n_of(sec)
    t = np.arange(m) / SR
    u = np.clip((t - t_rev[0]) / max(0.01, t_rev[1] - t_rev[0]), 0, 1)
    rpm = rpm0 + (rpm1 - rpm0) * (u * u * (3 - 2 * u))
    f = rpm / 120.0 * 6.0
    ph = np.cumsum(f / SR) * 2 * np.pi
    x = (np.sin(ph) * 0.6 + np.sin(ph * 0.5) * 0.4 + np.sign(np.sin(ph)) * 0.15)
    x = lp(x, 500) + lp(r.standard_normal(m), 300) * 0.3
    return x * gain


def tty_key(r, gain=1.0, space=False):
    """A teleprinter's type bar striking and the platen stepping."""
    m = n_of(0.08)
    t = np.arange(m) / SR
    x = band(r.standard_normal(m), 1800, 7000) * decay(m, 0.008, 0.0004) * (0.4 if space else 1.0)
    x += np.sin(2 * np.pi * 640 * t) * decay(m, 0.012, 0.0005) * 0.4
    x += lp(r.standard_normal(m), 600) * decay(m, 0.02, 0.001) * 0.5
    return x * gain


def tick(r, tock=False):
    m = n_of(0.08)
    t = np.arange(m) / SR
    c = band(r.standard_normal(m), 2000 if tock else 2600, 7000) * decay(m, 0.003, 0.0003)
    body = np.sin(2 * np.pi * (760 if tock else 880) * t) * decay(m, 0.015, 0.0008) * 0.5
    return c + body


def radio_waltz(sec, r):
    """A dance band on a radio behind a window: a simple original waltz, thin and muffled."""
    hz = lambda n: 440.0 * 2 ** ((n - 69) / 12.0)  # noqa: E731
    beat = 0.42
    tune = [64, 67, 72, 71, 67, 64, 62, 65, 69, 67, 65, 62]
    m = n_of(sec)
    x = np.zeros(m)
    for i, nn in enumerate(tune * 3):
        tt = i * beat * 3 / 2
        if tt > sec:
            break
        L = n_of(beat * 1.4)
        t = np.arange(L) / SR
        s = (np.sin(2 * np.pi * hz(nn) * t) + 0.3 * np.sin(2 * np.pi * hz(nn) * 2 * t)) * decay(L, 0.35, 0.01)
        place(x, s * 0.25, tt)
        place(x, np.sin(2 * np.pi * hz(nn - 24) * t) * decay(L, 0.2, 0.005) * 0.15, i * beat * 3)
    return band(x, 300, 2600) + band(r.standard_normal(m), 2000, 5000) * 0.01


# ---------------------------------------------------------------------------------------- LS_C4P2_Depot
def depot():
    name = 'c4p2cine_depot'
    r = rng(name)
    sec = 5.4
    x = st(sec)
    place(x, pan(B.wind(r, sec, 120, 900, 0.35) * 0.18, -0.2), 0.0)
    place(x, pan(B.crackles(r, sec, 16.0, 0.6) * 0.5, 0.8), 0.0)
    place(x, pan(lp(r.standard_normal(n_of(sec)), 160) * 0.12, 0.3), 0.0)
    L = layout().get('depot', {})
    gang = L.get('p1_gang', [])
    fps = float(L.get('cycle_fps', 8.0))
    contact = int(L.get('contact_frame', 1))
    near = set(int(i) for i in L.get('near_gang', []))
    for i, g in enumerate(gang):
        ph = int(g[2])
        px = (float(g[0]) + 24 - 320) / 320.0
        k = 0
        while True:
            t = ((contact - ph) % 8 + 8 * k) / fps
            if t >= sec - 0.3:
                break
            gain = 0.55 if i in near else 0.16
            place(x, pan(shovel_bite(r, gain), np.clip(px, -0.9, 0.9)), t)
            place(x, pan(coal_land(r, gain * 0.7, metal=i >= 8), np.clip(px + 0.12, -0.9, 0.9)), t + 3.0 / fps)
            k += 1
    place(x, pan(valve(r, 1.5, 2850.0, 0.35), 0.45), VALVE_LIFT)
    place(x, pan(C4.whistle(r, 540.0, 1.0, 0.12), -0.7), 4.1)
    x = room(x, name, 2.6, 2.0, 1.0, 0.22)
    return norm(fades(x, 0.4, 0.4), -3.0)


def arch():
    name = 'c4p2cine_arch'
    start = 5.0
    r = rng(name)
    sec = 4.3
    x = st(sec)
    for k, t in enumerate(ALEXEI_STEPS):
        p = -0.6 + 0.6 * k / max(1, len(ALEXEI_STEPS) - 1)
        s = B.crunch(r, 0.8, dark=0.6) + band(r.standard_normal(n_of(0.16)), 900, 3200) * \
            decay(n_of(0.16), 0.025, 0.002) * 0.35
        place(x, pan(s * (0.85 + 0.15 * (k % 2)), p), at(x, t, start))
    place(x, pan(B.metal_hit(r, (380, 910, 1620, 2600), 0.25, 0.3, 1.0), 0.35), 1.1)
    place(x, pan(B.metal_hit(r, (390, 930, 1650, 2650), 0.25, 0.25, 1.0), 0.38), 2.6)
    place(x, pan(band(r.standard_normal(n_of(sec)), 600, 4000) * 0.05, 0.1), 0.0)
    for tt in (0.7, 1.9, 3.3):
        place(x, pan(C4.drip(r, 1500.0, 0.25), 0.2), tt)
    place(x, pan(valve(r, sec, 2300.0, 0.06, 0.6), 0.0), 0.0)
    x = room(x, name, 2.2, 1.8, 0.9, 0.3)
    return norm(fades(x, 0.15, 0.35), -4.0)


def window():
    name = 'c4p2cine_window'
    start = 9.0
    r = rng(name)
    sec = 4.4
    x = st(sec)
    place(x, pan(B.wind(r, sec, 200, 1400, 0.45) * 0.3, -0.1), 0.0)
    inside = simmer(r, sec, 0.5)
    ring = np.zeros(n_of(sec))
    place(ring, phone_ring(r, 1.15, 1.0), at(None, PHONE_RING, start))
    inside = lp(inside + ring * 0.9, 2400)
    place(x, pan(inside, -0.15), 0.0)
    x = room(x, name, 1.2, 0.6, 0.3, 0.15)
    return norm(fades(x, 0.2, 0.4), -6.0)


# ---------------------------------------------------------------------------------------- LS_C4P2_Steam
def coal():
    name = 'c4p2cine_coal'
    r = rng(name)
    sec = 4.1
    x = st(sec)
    place(x, pan(B.wind(r, sec, 150, 1100, 0.5) * 0.2, 0.3), 0.0)
    a, b = COAL_RUN
    tt = a
    k = 0
    while tt < b:
        g = 0.9 if tt - a < 0.3 else 0.55
        place(x, pan(coal_land(r, g, metal=tt - a < 0.5, n=10), -0.05 + 0.05 * math.sin(k)), tt)
        tt += r.uniform(0.07, 0.14)
        k += 1
    slide = band(r.standard_normal(n_of(b - a)), 200, 2400) * 0.25
    place(x, pan(fades(slide, 0.1, 0.3), -0.05), a)
    for t in TARP_SNAPS:
        place(x, pan(snap(r, 0.9), 0.6), t)
    for t in (0.6, 1.4, 2.3, 3.1):
        place(x, pan(shovel_bite(r, 0.12), 0.8), t)
    x = room(x, name, 2.4, 1.6, 0.9, 0.2)
    return norm(fades(x, 0.3, 0.2), -3.0)


def jet():
    """ONE hiss across the cut: the Karsk valve in the open air, from CUT on the Berlin valve in the hall."""
    name = 'c4p2cine_jet'
    start = JET_T0
    r = rng(name)
    sec = 4.0
    a = valve(r, sec, 2850.0, 1.0, 0.05)
    cut = n_of(CUT - start)
    outdoor = np.stack([a, a * 0.92], 1)
    hall = room(np.stack([a * 0.9, a], 1), name + '_hall', 3.4, 3.0, 1.6, 0.55)
    x = outdoor.copy()
    x[cut:] = hall[cut:] * 0.85
    t = np.arange(x.shape[0]) / SR
    env = np.where(t < CUT - start, 1.0, np.clip(1 - (t - (CUT - start)) / 2.4, 0.15, 1.0))
    x *= env[:, None]
    return norm(fades(x, 0.03, 0.6), -2.0)


def hall():
    name = 'c4p2cine_hall'
    start = CUT
    r = rng(name)
    sec = 7.1
    x = st(sec)
    crowd = sum(B.babble(name + str(k), sec, 110 + 30 * k, 4.6, (1.0, 2.0), (0.3, 0.8), 0.8) * (0.25 - 0.04 * k)
                for k in range(4))
    place(x, pan(lp(crowd, 2500) * 0.5, 0.1), 0.0)
    fl = flap_run(r, FLAP_T[1] - FLAP_T[0], 36.0, 0.8)
    place(x, pan(fl, 0.55), at(None, FLAP_T[0], start))
    ann = B.babble(name + 'ann', 1.9, 96, 4.2, (1.6, 1.8), (0.2, 0.3), 1.2)
    place(x, pan(band(ann, 350, 3200) * 0.8, -0.3), 8.4 - start)
    for k in range(5):
        L = n_of(0.05)
        place(x, pan(band(r.standard_normal(L), 400, 2500) * decay(L, 0.02, 0.003) * 0.35, 0.3), 9.9 - start + k * 0.06)
    cart = band(r.standard_normal(n_of(2.0)), 80, 400) * 0.4 + np.sin(2 * np.pi * 1880 *
                                                                       np.arange(n_of(2.0)) / SR) * 0.03
    place(x, pan(fades(cart, 0.3, 0.6), np.linspace(0.6, -0.2, n_of(2.0))), 10.0 - start)
    for t in KONRAD_M4:
        m = n_of(0.14)
        s = lp(r.standard_normal(m), 420) * decay(m, 0.03, 0.002) + band(r.standard_normal(m), 1500, 5000) * \
            decay(m, 0.008, 0.0005) * 0.4
        place(x, pan(s * 0.5, -0.6), t - start)
    x = room(x, name, 3.6, 3.2, 1.8, 0.45)
    return norm(fades(x, 0.05, 0.6), -4.0)


# ---------------------------------------------------------------------------------------- LS_C4P2_Book
def dining():
    name = 'c4p2cine_dining'
    r = rng(name)
    sec = 3.6
    x = st(sec)
    hum = lp(r.standard_normal(n_of(sec)), 140) * 0.12 + B.babble(name, sec, 120, 4.0, (1.2, 2.0), (0.5, 1.0), 0.5) * 0.08
    place(x, pan(lp(hum, 1600), 0.2), 0.0)
    for t, g, p in ((0.15, 0.4, -0.5), (1.9, 0.3, 0.6), (3.1, 0.35, -0.4)):
        place(x, pan(A.clink(r, g, 2900.0), p), t)
    a, b = SLIDE_T
    sl = C4.paper(r, b - a, 1.0) + band(r.standard_normal(n_of(b - a)), 400, 2000) * np.hanning(n_of(b - a)) * 0.2
    place(x, pan(sl, np.linspace(0.6, 0.15, n_of(b - a))), a)
    place(x, pan(C4.paper(r, 0.8, 0.8), 0.1), CLOSE_T[0])
    x = room(x, name, 1.0, 0.5, 0.3, 0.15)
    return norm(fades(x, 0.2, 0.15), -5.0)


def shut():
    name = 'c4p2cine_shut'
    start = 3.5
    r = rng(name)
    sec = 1.6
    x = st(sec)
    place(x, pan(C4.paper(r, 0.5, 0.6), 0.0), 0.05)
    th = C4.thump(r, 82.0, True, 1.0)
    th += band(r.standard_normal(th.shape[0]), 800, 5000) * decay(th.shape[0], 0.01, 0.0005) * 0.5
    place(x, pan(th, 0.0), BOOK_SHUT - start)
    L = n_of(0.4)
    place(x, pan(band(r.standard_normal(L), 300, 3000) * decay(L, 0.12, 0.01) * 0.25, 0.0), BOOK_SHUT - start + 0.02)
    x = room(x, name, 0.8, 0.5, 0.3, 0.12)
    return norm(fades(x, 0.05, 0.3), -3.0)


def canteen():
    name = 'c4p2cine_canteen'
    start = 5.0
    r = rng(name)
    sec = 4.1
    x = st(sec)
    m = n_of(0.5)
    kiss = band(r.standard_normal(m), 500, 4000) * decay(m, 0.06, 0.004) * 0.6
    kiss += B.creak(r, 0.3, (220, 150), 0.25)[:m] if B.creak(r, 0.3, (220, 150), 0.25).shape[0] >= m else 0
    place(x, pan(kiss, 0.0), BOOK_OPEN - start)
    place(x, pan(C4.paper(r, 0.5, 0.5), 0.05), BOOK_OPEN - start + 0.2)
    crowd = sum(B.babble(name + str(k), sec, 105 + 25 * k, 4.0, (1.0, 2.2), (0.4, 0.9), 0.6) * 0.12 for k in range(3))
    place(x, pan(lp(crowd, 1800), -0.2), 0.0)
    for t, g, p in ((0.9, 0.35, -0.6), (2.0, 0.3, 0.7), (2.4, 0.25, 0.7), (3.4, 0.3, -0.5)):
        place(x, pan(A.clink(r, g, 2500.0), p), t)
    x = room(x, name, 1.8, 1.0, 0.6, 0.2)
    return norm(fades(x, 0.1, 0.3), -5.0)


def band_bed():
    name = 'c4p2cine_band'
    start = MARCH_T0
    r = rng(name)
    sec = 12.0 - start + 1.0
    x = st(sec)
    mu = march(sec, r)
    place(x, mu * 0.9, 0.0)
    place(x, pan(match_strike(r, 0.45), 0.55), MATCH_STRIKE - start)
    crowd = B.babble(name, sec, 120, 4.4, (1.0, 2.0), (0.4, 1.0), 0.6) * 0.1
    place(x, pan(lp(crowd, 2000), 0.4), 0.0)
    x = room(x, name, 2.8, 2.2, 1.2, 0.3)
    return norm(fades(x, 0.01, 0.5), -2.5)


# ---------------------------------------------------------------------------------------- LS_C4P2_Express
def express():
    name = 'c4p2cine_express'
    r = rng(name)
    sec = 4.2
    x = st(sec)
    place(x, pan(C4.whistle(r, 470.0, 1.5, 1.0), -0.6), WHISTLE)
    place(x, pan(air_release(r, 0.8, 0.5), 0.1), BRAKE_OFF)
    for k, t in enumerate(COUPLINGS):
        place(x, pan(coupling(r, 0.8 - 0.12 * k), 0.6 - 0.35 * k), t)
    for k, t in enumerate((1.3, 1.95, 2.5, 2.95, 3.35, 3.7)):
        place(x, pan(A.chuff(r, 1.1, 900.0) * (0.7 - 0.05 * k), -0.85), t)
    creak_ = B.creak(r, 2.0, (140, 90), 0.2)
    place(x, pan(creak_, 0.0), 1.1)
    place(x, pan(B.wind(r, sec, 150, 900, 0.3) * 0.12, 0.2), 0.0)
    crowd = B.babble(name, sec, 125, 4.4, (1.0, 2.0), (0.4, 1.0), 0.6) * 0.08
    place(x, pan(lp(crowd, 2000), 0.5), 0.0)
    x = room(x, name, 2.4, 1.8, 1.0, 0.22)
    return norm(fades(x, 0.1, 0.3), -2.5)


def recede():
    name = 'c4p2cine_recede'
    start = 4.0
    r = rng(name)
    sec = 4.2
    x = st(sec)
    tt = 0.0
    k = 0
    while tt < sec - 0.3:
        g = 0.6 * np.exp(-tt / 1.4)
        place(x, pan(lp(A.knock(r, 1.0, 0.4), 2000 * np.exp(-tt / 2.0) + 300) * g, -0.6), tt)
        place(x, pan(lp(A.knock(r, 0.8, 0.3), 1800 * np.exp(-tt / 2.0) + 300) * g, -0.6), tt + 0.11)
        tt += 0.42 + 0.06 * tt
        k += 1
    rum = lp(r.standard_normal(n_of(sec)), 140) * np.exp(-np.arange(n_of(sec)) / SR / 1.5) * 0.3
    place(x, pan(rum, -0.5), 0.0)
    for t in (1.2, 2.4):
        place(x, pan(C4.ticks(r, 0.2, 0.0, 0.08, 2, 0.8, (1500, 5000)), 0.4), t)
    place(x, pan(B.metal_hit(r, (260, 640, 1180), 0.3, 0.2, 0.8), 0.35), 2.0)
    place(x, C4.steps(r, sec, 2.6, 0.55, 'snow', 0.3, (0.3, 0.6)), 0.0)
    place(x, pan(B.wind(r, sec, 150, 900, 0.4) * 0.2, 0.0), 0.0)
    x = room(x, name, 2.6, 2.0, 1.0, 0.25)
    return norm(fades(x, 0.05, 0.4), -4.0)


def knock_bed():
    name = 'c4p2cine_knock'
    start = 8.0
    r = rng(name)
    sec = 1.6
    x = st(sec)
    place(x, pan(B.wind(r, sec, 150, 700, 0.3) * 0.12, 0.0), 0.0)
    place(x, pan(A.knock(r, 1.3, 0.5, 64.0), 0.0), KNOCK_T - start)
    place(x, pan(A.knock(r, 0.9, 0.4, 66.0) * 0.6, 0.0), KNOCK_T - start + 0.12)
    x = room(x, name, 2.8, 2.4, 1.2, 0.35)
    return norm(fades(x, 0.05, 0.4), -4.0)


def street():
    name = 'c4p2cine_street'
    start = 9.5
    r = rng(name)
    sec = 3.8
    x = st(sec)
    place(x, pan(B.wind(r, sec, 150, 1200, 0.4) * 0.18, 0.0), 0.0)
    a, b = WIPE
    L = n_of(b - a + 0.2)
    sw = band(r.standard_normal(L), 300, 3000) * np.hanning(L) * 0.7
    place(x, pan(sw, np.linspace(-0.9, 0.9, L)), a - start - 0.05)
    for k, t in enumerate(KONRAD_STEPS):
        place(x, pan(B.crunch(r, 0.7) * (0.85 + 0.15 * (k % 2)), 0.0), t - start)
    m = n_of(SBAHN_T[1] - SBAHN_T[0] + 0.8)
    tm = np.arange(m) / SR
    env = np.sin(np.clip(tm / (SBAHN_T[1] - SBAHN_T[0] + 0.8), 0, 1) * math.pi) ** 1.5
    sb = (lp(r.standard_normal(m), 240) + band(r.standard_normal(m), 600, 1800) * 0.15) * env * 0.5
    place(x, pan(sb, np.linspace(-0.7, 0.7, m)), SBAHN_T[0] - start)
    place(x, pan(radio_waltz(sec, r) * 0.5, 0.55), 0.0)
    gate = band(r.standard_normal(n_of(1.2)), 500, 1600) * np.hanning(n_of(1.2)) * 0.2
    place(x, pan(gate, 0.2), 12.3 - start)
    x = room(x, name, 2.0, 1.6, 0.9, 0.22)
    return norm(fades(x, 0.1, 0.3), -4.0)


# ---------------------------------------------------------------------------------------- LS_C4P2_Clock
def k14():
    name = 'c4p2cine_k14'
    r = rng(name)
    sec = 5.2
    x = st(sec)
    place(x, pan(B.wind(r, sec, 150, 900, 0.3) * 0.14, 0.0), 0.0)
    for t in CAR_DOORS:
        place(x, pan(car_door(r, 0.8), 0.0), t)
    st_ = band(r.standard_normal(n_of(0.35)), 300, 2500) * np.hanning(n_of(0.35)) * 0.3
    place(x, pan(st_, 0.0), ENGINE_T - 0.1)
    e = engine(r, 4.4, 700, 1500, (CAR_T[0] - ENGINE_T, CAR_T[0] - ENGINE_T + 1.2), 0.5)
    tm = np.arange(e.shape[0]) / SR
    away = np.clip(1 - (tm - (CAR_T[1] - ENGINE_T)) / 1.2, 0.0, 1.0)
    e = e * away
    eng = pan(e, 0.0)
    pas = room(eng, name + '_passage', 0.6, 0.9, 0.5, 0.6, slap=((0.03, 0.5, 2500.0),))
    i0 = n_of(CAR_T[1] - 0.5 - ENGINE_T)
    eng[i0:] = pas[i0:eng.shape[0]]
    place(x, eng, ENGINE_T)
    cr = sum(B.crunch(r, 0.3) for _ in range(1))
    for k in range(10):
        place(x, pan(B.crunch(r, 0.25), 0.0), CAR_T[0] + k * 0.22)
    place(x, pan(band(r.standard_normal(n_of(0.35)), 500, 2000) * decay(n_of(0.35), 0.06, 0.01) * 0.25, -0.8), 4.3)
    x = room(x, name, 1.8, 1.4, 0.8, 0.25)
    return norm(fades(x, 0.1, 0.4), -3.0)


def kordon(variant):
    name = 'c4p2cine_kordon_' + variant
    start = 5.0
    r = rng(name)
    sec = 6.2
    x = st(sec)
    hum = (np.sin(2 * np.pi * 100 * np.arange(n_of(sec)) / SR) * 0.03 + band(r.standard_normal(n_of(sec)), 90, 300) * 0.05)
    place(x, pan(hum, 0.1), 0.0)
    place(x, pan(B.wind(r, sec, 120, 900, 0.5) * 0.3, -0.2), 0.0)
    if variant == 'publish':
        m = n_of(0.3)
        t = np.arange(m) / SR
        pop = band(r.standard_normal(m), 1500, 9000) * decay(m, 0.012, 0.0003) + np.sin(2 * np.pi * 300 * t) * decay(m, 0.02, 0.001) * 0.4
        place(x, pan(pop * 0.6, 0.15), FLASH_T - start)
        voices = sum(B.babble(name + str(k), 3.0, 110 + 35 * k, 4.8, (0.6, 1.4), (0.3, 0.8), 0.6) * 0.15 for k in range(3))
        place(x, pan(lp(voices, 1400), 0.1), FLASH_T - start + 0.35)
    else:
        place(x, pan(B.creak(r, 0.9, (160, 110), 0.35), 0.3), DOOR_OPEN - start)
        m = n_of(1.2)
        t = np.arange(m) / SR
        boom = np.sin(2 * np.pi * 58 * t * (1 - 0.2 * t)) * decay(m, 0.25, 0.004) + lp(r.standard_normal(m), 300) * decay(m, 0.1, 0.002)
        boom += B.metal_hit(r, (240, 610, 1130), 0.3, 0.3, 1.2)[:m]
        place(x, pan(boom * 0.6, 0.3), DOOR_SHUT - start)
    x = room(x, name, 3.4, 3.0, 1.4, 0.4)
    return norm(fades(x, 0.3, 0.5), -6.0)


def tty(variant):
    name = 'c4p2cine_tty_' + variant
    start = 11.0
    r = rng(name)
    sec = 5.2
    x = st(sec)
    L = layout().get('clock', {})
    txt = str(L.get('text', {}).get(variant + ('_now' if variant == 'publish' else '_first'), ''))
    motor = lp(r.standard_normal(n_of(sec)), 220) * 0.08 + np.sin(2 * np.pi * 50 * np.arange(n_of(sec)) / SR) * 0.03
    motor *= np.clip((np.arange(n_of(sec)) / SR - (TYPE_T0 - start - 0.3)) / 0.2, 0, 1)
    place(x, pan(motor, 0.5), 0.0)
    for i, ch in enumerate(txt):
        t = TYPE_T0 + i / TYPE_CPS
        if t - start >= sec - 0.1:
            break
        place(x, pan(tty_key(r, 0.6, ch == ' '), 0.5), t - start)
    end = TYPE_T0 + len(txt) / TYPE_CPS
    if end - start < sec - 0.3:
        place(x, pan(A.bell_strike(r, 1850.0, 0.4) * 0.25, 0.5), end - start + 0.1)
    place(x, pan(B.crackles(r, sec, 6.0, 0.15), -0.4), 0.0)
    x = room(x, name, 1.4, 0.8, 0.5, 0.18)
    return norm(fades(x, 0.15, 0.3), -5.0)


def desk():
    name = 'c4p2cine_desk'
    r = rng(name)
    sec = 4.0
    x = st(sec)
    hum = np.sin(2 * np.pi * 100 * np.arange(n_of(sec)) / SR) * 0.02 + band(r.standard_normal(n_of(sec)), 2000, 6000) * 0.004
    place(x, pan(hum, 0.0), 0.0)
    place(x, pan(A.clink(r, 0.25, 2600.0), 0.45), 1.3)
    x = room(x, name, 1.0, 0.6, 0.3, 0.15)
    x = fades(x, 0.3, 0.06)
    return norm(x, -14.0)


def tick_bed():
    name = 'c4p2cine_tick'
    r = rng(name)
    sec = TICK_END
    x = st(sec)
    k = 0
    while k < int(TICK_END):
        place(x, pan(tick(r, k % 2 == 1) * 0.6, 0.0), float(k))
        k += 1
    x = room(x, name, 1.0, 0.5, 0.3, 0.12)[:n_of(sec)]
    return norm(x, -10.0)


SOUNDS = {
    'c4p2cine_depot': depot, 'c4p2cine_arch': arch, 'c4p2cine_window': window,
    'c4p2cine_coal': coal, 'c4p2cine_jet': jet, 'c4p2cine_hall': hall,
    'c4p2cine_dining': dining, 'c4p2cine_shut': shut, 'c4p2cine_canteen': canteen, 'c4p2cine_band': band_bed,
    'c4p2cine_express': express, 'c4p2cine_recede': recede, 'c4p2cine_knock': knock_bed, 'c4p2cine_street': street,
    'c4p2cine_k14': k14, 'c4p2cine_kordon_publish': lambda: kordon('publish'),
    'c4p2cine_kordon_protect': lambda: kordon('protect'), 'c4p2cine_tty_publish': lambda: tty('publish'),
    'c4p2cine_tty_protect': lambda: tty('protect'), 'c4p2cine_desk': desk, 'c4p2cine_tick': tick_bed,
}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args(argv)
    only = [s.strip() for s in a.only.split(',') if s.strip()]
    for name, fn in SOUNDS.items():
        if only and name not in only:
            continue
        x = fn()
        info = write(name, x)
        print('%-26s %5.2f s  peak %5.1f dB' % (name, info['seconds'], info['peak_db']))


if __name__ == '__main__':
    main()
