"""c4_audio.py -- Chapter 4, part 1 („Stimmen unter Beton“): original synthesised sound for the Karsk freight-office
cellar, Service Tunnel 3 and the hidden siding, the Berlin tram loop Süd 8 and the registry annex underneath it
(documentation/C4_DESIGN.md section 8, audio brief).

    py -3 -P tools/audiogen/c4_audio.py                         # build all + .import + analysis + numeric checks
    py -3 -P tools/audiogen/c4_audio.py --only amb_karsk_cellar # subset (comma separated builder names)
    py -3 -P tools/audiogen/c4_audio.py --list                  # what exists and where it is (to be) wired
    py -3 -P tools/audiogen/c4_audio.py --no-spectro            # skip the spectrogram PNGs

LEVEL AMBIENCES (assets/audio/amb, 60 s stereo loops; ids fixed by the contract, wired by c4.json "switches")
  amb_karsk_cellar   the archive cellar of the freight office before dawn (L_C4_TunnelsA): the brick vault's close
                     room tone, the stove (a low fire, the iron ticking as it heats), the samovar simmering and once
                     singing, the wall clock, two trains passing over the vault (rumble, rail joints, dust trickling,
                     the lamp chain), wind and snow at the high barred window, the night shift's boots in the yard
                     snow above, pages turned at Lev's desk
  amb_karsk_tunnel   Service Tunnel 3 and the transfer siding (L_C4_TunnelsB): a concrete tube's long echo, a draught,
                     water dripping (one steady drip from a cable run, others at random), a fan turning in an air
                     shaft, shunting overhead through the ground, the work lamp's hum (and one flicker), a train
                     overhead, a plank settling in the converted wagon
  amb_berlin_loop    the tram loop Süd 8 at dawn (L_C4_AnnexA): cold air and a little snow, the city waking far away,
                     the trolley wire humming and singing in the gusts, tram 74's air compressor starting and
                     stopping, warm air breathing out of the advertising column's grate, the first lorry idling at
                     the freight hatch (tailgate, crates), crane chains of the axis far off, another line's tram bell
                     far away, early-shift workers crunching past and a murmur at the shelter (no words)
  amb_berlin_annex   the registry annex (L_C4_AnnexB): two huge fans behind the grille (their blade tones beating
                     slowly against each other: the breath of the column), fluorescent tubes (ballast hum, one tube
                     flickering), tube capsules shooting through the pipes and landing, typewriters muffled behind
                     glass, a card drawer, a sliding ladder, a stamp at the counter, the street above as a rumble
MUSIC (assets/audio/music, loops; every loop point sits in a rest)
  mus_c4_karsk       sparse low strings in D Aeolian (Alexei's key), a bayan breath -- reed chords swelling and
                     falling like the bellows, never a folk tune -- and one quiet echo of the K motif on the felt
                     piano (54 bpm, 64 beats, 71.1 s)
  mus_c4_berlin      cool and mechanical in G Aeolian (Konrad's key): a muted-piano pulse in 3+3+2 like a card
                     sorter, a dry machine tick, the low brass pedal on G, a cold harmonic line, the B motif on the
                     celesta and low in the piano (72 bpm, 64 beats, 53.3 s)
  mus_c4_voices      the closing (LS_C4_Voices): both themes on one clock -- a clock ticks every beat; the Karsk
                     drone, K on the piano, then B on the celesta over the G pedal, then both together where B
                     bends its Eb to E, and the clock alone again.  The first 24 s are a complete arc (the
                     cinematic is ~24 s); the loop goes on for longer scenes (60 bpm, 48 beats, 48.0 s)
SFX (assets/audio/sfx, one-shots; ids for the cinematic stream -- C4_DESIGN section 2.9)
  c4_stencil_brush   a stippling brush dabbed through a stencil on wagon planks, then wiped on the tin (LS_C4_Number)
  c4_card_tear       a stiff registry card torn along its perforation (LS_C4_Card match cut)
  c4_stamp_accept    the Karsk stamp „ПРИНЯТЬ“: ink pad, then down on the card on the siding office's desk
  c4_stamp_dispatch  the Berlin stamp „ABGANG“ on the annex counter (same timing: the LS_C4_Stamp match cut)
  c4_bell_once / c4_bell_twice   Marta's foot gong in the open loop, one ring or two (LS_C4_Voices v2, per c4d)
  c4_train_overhead  a freight train crossing above the vault: rumble, rail joints, dust, the lamp chain (12 s)
  c4_lamp_out        the work lamp switched off: the hum, the switch, the filament ticking as it cools (v4)
(the existing `tram_bell` stays available; these are recorded in the places of this chapter)

Everything reuses dsp / instruments / foley / ambience / music / c3_audio / c3p2_audio by import (none of them is
modified; build_all.py's registry does not know this module: run this file directly).  Seeds derive from
zlib.crc32(name) (c3_audio.seed_of), so every run is bit-identical.  Unintelligible voices only (prosody profiles
over random vowel targets): no words, no language.  The bayan is a free-reed tone synthesised here (additive reeds,
bellows envelope and air), playing breaths and chords only -- no folk melody, no national cliché.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

from dsp import (SR, TAU, secs, eq, fftconv, place, pan2, smooth_periodic, shaped_noise, mag_bp, rms,  # noqa: E402
                 db2a, smoothstep, make_ir, fade, midi_hz, write_wav, limiter, normalize_peak, remove_dc,
                 to_stereo, glue)
from instruments import impact, random_modes, noise_burst, ctrl_noise, modal, bell_modes, make_table, wt_read  # noqa: E402
from foley import (wind, gust_curve, norm_peak, bump, ir_outdoor_far, ir_small, grain_cloud, paper_rustle,  # noqa: E402
                   tram_bell, wood_knock, metal_clank, shunting_chain, page_turn, drawer_slide, creak_train)
from ambience import Mix, N, periodic_tone, clock_tick  # noqa: E402
from music import Track, hall_ir, K_A, K_B, B_1, B_2, tr, STR_EQ, STR_HI_EQ, BRASS_EQ, MUTED_EQ, CEL_EQ, PLUCK_EQ  # noqa: E402
import c3_audio as C3A  # noqa: E402  (seed_of, far, voice, typewriter, analysis helpers)
import c3p2_audio as P2A  # noqa: E402  (one_shot, loop_master, fire_bed, snow_steps, timber_groan, R)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AUDIO = os.path.join(ROOT, 'assets', 'audio')
seed_of = C3A.seed_of
far = C3A.far
R = P2A.R
one_shot = P2A.one_shot


# =============================================================================== rooms
def ir_cellar(seed: int) -> np.ndarray:
    """Brick-vaulted cellar full of freight books: close, warm, a short bloom."""
    return make_ir(length=1.6, rt_low=1.1, rt_high=0.42, predelay=0.006, er_taps=14, er_span=0.03, er_gain=0.45,
                   seed=seed, lowcut=55.0, highcut=6000.0, build=0.006)


def ir_tunnel(seed: int) -> np.ndarray:
    """A concrete tube and the vaulted siding hall: long, dark, a flutter between the walls."""
    return make_ir(length=4.6, rt_low=3.4, rt_high=1.1, predelay=0.018, er_taps=10, er_span=0.06, er_gain=0.3,
                   seed=seed, lowcut=45.0, highcut=5200.0, build=0.02,
                   slap=[(0.085, 0.32, 3000.0), (0.17, 0.22, 2400.0), (0.34, 0.14, 1800.0), (0.68, 0.08, 1200.0)])


def ir_loop(seed: int) -> np.ndarray:
    """The tram loop at the cleared block: open ground, one bare party wall (a clear slap), far facades."""
    return make_ir(length=3.2, rt_low=1.7, rt_high=0.7, predelay=0.02, er_taps=4, er_span=0.06, er_gain=0.12,
                   seed=seed, lowcut=60.0, highcut=6500.0, build=0.02,
                   slap=[(0.14, 0.42, 3600.0), (0.33, 0.20, 2400.0), (0.9, 0.10, 1500.0)])


def ir_annex(seed: int) -> np.ndarray:
    """Concrete card hall with steel cabinets to the ceiling: hard, bright-ish early reflections."""
    return make_ir(length=2.6, rt_low=1.6, rt_high=0.75, predelay=0.01, er_taps=18, er_span=0.045, er_gain=0.42,
                   seed=seed, lowcut=60.0, highcut=7000.0, build=0.008)


def ir_booth(seed: int) -> np.ndarray:
    """The siding office: a small wooden booth inside the big hall."""
    return make_ir(length=1.4, rt_low=0.7, rt_high=0.3, predelay=0.004, er_taps=12, er_span=0.018, er_gain=0.5,
                   seed=seed, lowcut=70.0, highcut=6500.0, build=0.004)


# =============================================================================== shared sources
def train_overhead(rng: np.random.Generator, dur: float = 12.0, wagons: int = 9, pass_at: float = 5.5,
                   dust: float = 1.0, chain: float = 1.0) -> np.ndarray:
    """A goods train crossing above a vault (mono, dry; heard through earth and brick): a rumble that swells and
    recedes, the double thumps of the wheelsets over a rail joint travelling along the train, the vault answering
    in its low modes, dust trickling from the joints of the vault, the lamp's chain rattling at the loudest part."""
    n = secs(dur)
    t = np.arange(n) / SR
    env = bump(n, pass_at * 0.8, (dur - pass_at) * 0.42, peak_at=pass_at)
    rum = noise_burst(dur, rng, 18.0, 160.0, 1e6, attack=0.0)
    rum = norm_peak(rum) * (0.8 + 0.2 * ctrl_noise(n, 4.0, rng))
    y = 0.55 * rum * env
    # the vault's own low modes, excited by the rumble (a slow hum that comes and goes)
    for f, a in ((41.0, 1.0), (57.5, 0.6), (83.0, 0.35)):
        y += 0.05 * a * np.sin(TAU * f * t + rng.uniform(0, TAU)) * env ** 1.5
    # wheelsets over a rail joint: (loco: 3 pairs) then two-axle wagons; spacing at ~35 km/h
    tc = pass_at - 3.2
    seq = [0.0, 0.16, 0.32, 0.9, 1.06, 1.22] + [1.9 + i * 0.86 + o for i in range(wagons) for o in (0.0, 0.52)]
    for s in seq:
        tt = tc + s
        if not 0.05 < tt < dur - 0.6:
            continue
        g = float(np.interp(tt, t, env))
        for k, off in enumerate((0.0, 0.045)):
            m = secs(0.25)
            tb = np.arange(m) / SR
            th = np.sin(TAU * rng.uniform(46, 62) * tb) * np.exp(-tb / 0.06) * smoothstep(tb / 0.004)
            th += 0.3 * noise_burst(0.25, rng, 60.0, 600.0, 0.05, attack=0.002)[:m]
            place(y, th * 0.55 * g * (1.0 if k == 0 else 0.7), secs(tt + off), circular=False)
    y = eq(y, ('lp', 420.0, 2), ('hp', 22.0, 2), circular=False)
    # dust and grit from the vault's joints (high, sparse), strongest while the train is overhead
    if dust:
        rate = 160.0 * np.clip(env - 0.35, 0, None) ** 1.3 + 2.0
        d = grain_cloud(rng, dur, rate, 2500.0, 9000.0, 0.001, 0.004)
        y += 0.06 * dust * norm_peak(eq(d, ('hp', 1800.0, 2), circular=False))
    # the lamp's chain / shade rattling in short bursts at the loudest moment
    if chain:
        for k in range(7):
            tt = pass_at - 1.0 + k * rng.uniform(0.25, 0.5)
            if tt < dur - 0.4:
                ck = impact(rng, random_modes(rng, 1800.0, 6500.0, 5, 0.02, 0.09), 0.2, hard=0.8, noise_amt=0.2)
                place(y, 0.05 * chain * ck * float(np.interp(tt, t, env)), secs(tt), circular=False)
    return y


def drip(rng: np.random.Generator, f0: float = 1100.0) -> np.ndarray:
    """A water drop into a puddle: a short rising 'plink' (bubble resonance) with a tiny splash."""
    m = secs(0.16)
    tb = np.arange(m) / SR
    f = f0 * (1.0 + 0.7 * (1 - np.exp(-tb / 0.012)))
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-tb / 0.022) * smoothstep(tb / 0.0015)
    sp = noise_burst(0.02, rng, 2000.0, 9000.0, 0.006, attack=0.0004)
    y[:len(sp)] += 0.25 * norm_peak(sp)
    return y


def fan(n: int, rng: np.random.Generator, rot_hz: float, blades: int, lo: float, hi: float, tone: float = 0.25,
        depth: float = 0.35) -> np.ndarray:
    """A big axial fan (circular, mono): broadband air whose level pulses at the blade-pass rate, plus the
    blade-pass tone and its first harmonics (whole cycles per loop)."""
    air = shaped_noise(n, rng, lambda f: mag_bp(f, lo, hi, 2))
    air = air[:, 0] if air.ndim == 2 else air
    bp = rot_hz * blades
    am = 1.0 + depth * periodic_tone(n, bp, rng)
    y = air * am / max(rms(air), 1e-9)
    for h, a in ((1, 1.0), (2, 0.45), (3, 0.2)):
        y += tone * a * periodic_tone(n, bp * h, rng, fm=0.002 * smooth_periodic(n, 7, rng))
    return y


def hum(n: int, rng: np.random.Generator, base: float = 100.0, parts=((1, 1.0), (2, 0.5), (3, 0.3), (5, 0.12)),
        buzz: float = 0.0) -> np.ndarray:
    """Mains hum of a lamp / ballast (whole cycles per loop) with an optional buzzy upper band."""
    y = sum(a * periodic_tone(n, base * h, rng) for h, a in parts)
    if buzz:
        b = shaped_noise(n, rng, lambda f: mag_bp(f, 900.0, 4000.0, 2))
        b = b[:, 0] if b.ndim == 2 else b
        y = y + buzz * (b / max(rms(b), 1e-9)) * (0.5 + 0.5 * periodic_tone(n, base, rng))
    return y


def compressor(rng: np.random.Generator, dur: float = 5.0, rate: float = 8.6) -> np.ndarray:
    """A tram's air compressor running for a few seconds: piston chugs that speed up and settle, a valve hiss."""
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    ph, k = 0.0, 0
    while True:
        r = rate * (0.6 + 0.4 * min(1.0, ph / 0.8))
        ph += 1.0 / r
        if ph > dur - 0.4:
            break
        th = impact(rng, random_modes(rng, 90.0, 900.0, 6, 0.03, 0.09), 0.12, hard=0.25, noise_amt=0.35,
                    noise_decay=0.01)
        place(y, th * (0.8 if k % 2 else 1.0), secs(ph), circular=False)
        k += 1
    env = smoothstep(t / 0.3) * smoothstep((dur - t) / 0.5)
    hiss = noise_burst(dur, rng, 1200.0, 6000.0, 1e6, attack=0.0) * 0.04
    end = noise_burst(0.6, rng, 1500.0, 7000.0, 0.25, attack=0.01)
    place(y, 0.25 * norm_peak(end), secs(dur - 0.55), circular=False)
    return eq((y + hiss) * env, ('lp', 3500.0, 2), circular=False)


def lorry_idle(n: int, rng: np.random.Generator, rpm_hz: float = 12.5) -> np.ndarray:
    """A 1960s diesel lorry idling (circular, mono): firing pulses at the idle rate through the exhaust, a little
    rpm wander, the body rattling faintly."""
    ph = np.cumsum(np.full(n, rpm_hz) * (1.0 + 0.012 * smooth_periodic(n, 9, rng))) / SR
    ph *= np.round(ph[-1]) / ph[-1]
    pulse = np.zeros(n)
    for h in range(1, 14):
        pulse += (1.0 / h ** 0.9) * np.sin(TAU * h * ph + rng.uniform(0, TAU))
    pulse = eq(pulse, ('lp', 320.0, 2), ('hp', 25.0, 2), circular=True)
    rat = shaped_noise(n, rng, lambda f: mag_bp(f, 600.0, 2500.0, 2))
    rat = rat[:, 0] if rat.ndim == 2 else rat
    return pulse / max(rms(pulse), 1e-9) + 0.08 * rat / max(rms(rat), 1e-9)


def crane_chain(rng: np.random.Generator, dur: float = 2.6) -> np.ndarray:
    """A crane's hook chain paid out far away: rapid link clinks with a ratchet rhythm."""
    n = secs(dur)
    y = np.zeros(n)
    t = 0.05
    while t < dur - 0.3:
        ck = impact(rng, random_modes(rng, 700.0, 5200.0, 7, 0.03, 0.18), 0.3, hard=0.6, noise_amt=0.3)
        place(y, ck * rng.uniform(0.4, 1.0), secs(t), circular=False)
        t += rng.uniform(0.045, 0.09)
    return y * bump(n, 0.2, dur * 0.4, peak_at=0.3)


def capsule(rng: np.random.Generator, dur: float = 2.6) -> np.ndarray:
    """A pneumatic-tube capsule arriving: a rising rush of air in the pipe, a rattle, the thunk into the basket."""
    n = secs(dur)
    t = np.arange(n) / SR
    arr = dur - 0.7
    env = smoothstep(t / arr) ** 2.2 * np.exp(-np.maximum(t - arr, 0) / 0.05)
    rush = noise_burst(dur, rng, 300.0, 5000.0, 1e6, attack=0.0) * env
    rush = eq(rush, ('bell', 900.0, 6.0, 1.4), circular=False)
    y = 0.5 * norm_peak(rush)
    for k in range(10):
        tt = arr - 0.6 + k * 0.05
        ck = impact(rng, random_modes(rng, 500.0, 3000.0, 5, 0.02, 0.08), 0.1, hard=0.5)
        place(y, 0.12 * ck * (k / 10.0), secs(tt), circular=False)
    th = impact(rng, random_modes(rng, 120.0, 1800.0, 8, 0.05, 0.25), 0.6, hard=0.45, noise_amt=0.4)
    place(y, 0.9 * th, secs(arr), circular=False)
    lid = impact(rng, random_modes(rng, 600.0, 4000.0, 6, 0.03, 0.12), 0.2, hard=0.7)
    place(y, 0.3 * lid, secs(arr + 0.32), circular=False)
    return y


def sliding_ladder(rng: np.random.Generator, dur: float = 2.2) -> np.ndarray:
    """A library ladder rolled along its rail: steel wheels rumbling on the rail, a clack at the stop."""
    n = secs(dur)
    roll = noise_burst(dur, rng, 150.0, 2500.0, 1e6, attack=0.0)
    roll = norm_peak(roll) * bump(n, 0.25, 0.5, peak_at=0.6) * (0.7 + 0.3 * ctrl_noise(n, 30.0, rng))
    y = 0.4 * roll
    place(y, 0.05 * creak_train(rng, dur * 0.8, 40, 60, [(820.0, 0.05, 1.0), (1650.0, 0.04, 0.5)]), 0,
          circular=False)
    stop = impact(rng, random_modes(rng, 300.0, 3500.0, 8, 0.05, 0.3), 0.6, hard=0.6)
    place(y, 0.7 * stop, secs(dur - 0.7), circular=False)
    return y


def samovar(n: int, rng: np.random.Generator) -> np.ndarray:
    """A samovar on the simmer (circular, mono): soft boiling hiss with bubble grains and its body's low hum."""
    hiss = shaped_noise(n, rng, lambda f: mag_bp(f, 900.0, 5200.0, 2))
    hiss = hiss[:, 0] if hiss.ndim == 2 else hiss
    hiss = hiss / max(rms(hiss), 1e-9) * (0.7 + 0.3 * smooth_periodic(n, 20, rng))
    bub = grain_cloud(rng, n / SR, np.full(n, 26.0), 300.0, 1400.0, 0.004, 0.012)
    return 0.35 * hiss + 0.9 * bub / max(float(np.max(np.abs(bub))), 1e-9)


# =============================================================================== ambiences
def amb_karsk_cellar():
    name = 'amb_karsk_cellar'
    rng = R(name)
    M = Mix()
    room = ir_cellar(seed_of(name, 1))
    # close room tone of the vault, the freight yard above as a faint low rumble
    air = shaped_noise(N, rng, lambda f: mag_bp(f, 70.0, 900.0, 2) * (np.maximum(f, 20.0) / 150.0) ** -0.4, ch=2,
                       corr=0.6)
    M.bed(air, -6.0)
    yard = shaped_noise(N, rng, lambda f: mag_bp(f, 30.0, 140.0, 2), ch=2, corr=0.75)
    yard *= (1.0 + 0.3 * smooth_periodic(N, 8, rng))[:, None]
    M.bed(yard, -15.0)
    # wind and snow at the high barred window (up, left): thin, a whistle in the bars
    g = gust_curve(N, rng, [(3.0, 0.8, 1.8, 2.6), (19.0, 0.6, 1.4, 2.2), (33.5, 1.0, 2.2, 3.2), (50.0, 0.7, 1.6, 2.4)],
                   base=0.28, turb=0.07)
    w = wind(N, rng, g, lp_base=240.0, lp_gust=800.0, whistle=0.32, whistle_f=(760.0, 1150.0), corr=0.5,
             pan_sweep=0.1)
    w[:, 1] *= 0.5
    M.bed(w, -10.0)
    flakes = grain_cloud(rng, N / SR, np.full(N, 6.0), 3000.0, 8000.0, 0.001, 0.003)
    M.bed(pan2(flakes, -0.55), -29.0)
    # the stove (right): a low fire behind the iron door, muffled
    fire = P2A.fire_bed(rng, N, 0.2)
    fire = eq(fire, ('lp', 900.0, 2), circular=True)
    fire[:, 0] *= 0.55
    M.bed(fire, -11.0)
    for t in (2.6, 9.1, 9.35, 17.8, 24.4, 31.0, 38.2, 38.5, 45.9, 53.1, 57.6):
        tk = impact(rng, random_modes(rng, 1200.0, 4800.0, 5, 0.012, 0.05), 0.15, hard=0.7, noise_amt=0.3)
        M.event(far(tk, room, wet=0.3, dry=1.0, pan=rng.uniform(0.3, 0.6)), t, -10.0 + rng.uniform(-3, 2), mode='peak')
    # the samovar on Lev's desk (left of centre), simmering; once it sings softly
    sv = samovar(N, rng)
    M.bed(pan2(eq(sv, ('lp', 6000.0, 2), circular=True), -0.25), -16.0)
    sing = np.sin(TAU * np.cumsum(1880.0 * (1 + 0.004 * ctrl_noise(secs(4.0), 3.0, rng))) / SR)
    sing *= bump(secs(4.0), 1.2, 1.1, peak_at=1.6)
    M.event(far(sing, room, wet=0.4, dry=1.0, pan=-0.25), 27.5, -14.0)
    # the wall clock: one tick a second (tick / tock), on the right wall
    ticks = np.zeros(N)
    for i in range(60):
        place(ticks, clock_tick(np.random.default_rng(4300 + i % 6), i % 2 == 1) * (1.0 if i % 2 == 0 else 0.86),
              secs(i * 1.0 + 0.4), circular=True)
    tk = pan2(ticks, 0.4)
    tk = tk + 0.3 * fftconv(tk, room, circular=True)
    M.buf += tk * (db2a(20.0) / float(np.max(np.abs(tk))))
    # two trains over the vault (every 20-40 s, C4_DESIGN 4.1)
    for t0, w_ in ((10.5, 9), (39.0, 12)):
        tr_ = train_overhead(rng, dur=12.0, wagons=w_, pass_at=5.5, dust=0.7, chain=0.6)
        M.event(far(eq(tr_, ('hp', 38.0, 2), circular=False), room, wet=0.35, dry=1.0,
                    pan=rng.uniform(-0.1, 0.1)), t0, -3.0)
    # the night shift crossing the yard snow above the window (muffled, left)
    steps = P2A.snow_steps(rng, 8, 0.6, -0.8, -0.3)
    M.event(eq(steps, ('lp', 1300.0, 2), ('hp', 90.0, 2), circular=False), 24.0, -14.0)
    # pages turned and a chair at Lev's desk
    for t in (6.8, 47.3):
        M.event(far(page_turn(rng), room, wet=0.35, dry=1.0, pan=-0.2), t, -9.0)
    chair = creak_train(rng, 0.7, 60, 30, [(rng.uniform(300, 380), 0.06, 1.0), (rng.uniform(800, 950), 0.05, 0.6)])
    M.event(far(chair * bump(len(chair), 0.15, 0.25, peak_at=0.25), room, wet=0.3, dry=1.0, pan=-0.2), 33.4, -12.0)
    return M.master(-26.0, lp=11000.0), (0, N)


def amb_karsk_tunnel():
    name = 'amb_karsk_tunnel'
    rng = R(name)
    M = Mix()
    tun = ir_tunnel(seed_of(name, 1))
    # the tube's air: a low draught moving through, the vault's dark bloom
    g = gust_curve(N, rng, [(8.0, 0.5, 3.0, 4.0), (29.0, 0.7, 4.0, 5.0), (47.0, 0.4, 3.0, 4.0)], base=0.35, turb=0.05,
                   turb_rate=0.3)
    draught = wind(N, rng, g, lp_base=240.0, lp_gust=560.0, whistle=0.0, corr=0.7, pan_sweep=0.3, hp=60.0, tilt=-0.5)
    M.bed(draught, -4.0)
    deep = shaped_noise(N, rng, lambda f: mag_bp(f, 30.0, 110.0, 2), ch=2, corr=0.8)
    deep *= (1.0 + 0.25 * smooth_periodic(N, 6, rng))[:, None]
    M.bed(deep, -14.0)
    # the fan in an air shaft (up, right): slow blades, a soft breathing tone
    fn = fan(N, rng, rot_hz=5.0, blades=7, lo=160.0, hi=1400.0, tone=0.22, depth=0.45)
    fn = eq(fn, ('lp', 1100.0, 2), circular=True)
    st = pan2(fn, 0.55)
    M.bed(st + 0.5 * fftconv(st, tun, circular=True), -11.0)
    # the work lamps: mains hum (and once a flicker)
    lamp = hum(N, rng, 100.0, buzz=0.12)
    M.bed(pan2(eq(lamp, ('lp', 2400.0, 2), circular=True), 0.1), -20.0)
    flick = np.zeros(secs(0.5))
    for k in range(4):
        place(flick, impact(rng, random_modes(rng, 2400.0, 6400.0, 4, 0.01, 0.03), 0.06, hard=0.8) * (1 - k * 0.2),
              secs(k * rng.uniform(0.07, 0.12)), circular=False)
    M.event(far(flick, tun, wet=0.4, dry=1.0, pan=0.1), 36.2, -2.0, mode='peak')
    # water: one steady drip from a cable run (every ~2.7 s, centre-left), others at random
    t = 0.9
    while t < 59.0:
        M.event(far(drip(rng, 1050.0 * rng.uniform(0.97, 1.03)), tun, wet=0.65, dry=1.0, pan=-0.3), t,
                8.0 + rng.uniform(-1.5, 1.0), mode='peak')
        t += rng.uniform(2.5, 2.9)
    for t in (4.2, 13.7, 15.1, 22.9, 31.6, 44.4, 50.8, 56.3):
        M.event(far(drip(rng, rng.uniform(700.0, 1600.0)), tun, wet=0.75, dry=0.7, pan=rng.uniform(-0.8, 0.8)), t,
                rng.uniform(2.0, 6.0), mode='peak')
    # shunting overhead, through the ground (buffer bumps travelling down a line of wagons)
    for t0, bumps, pan in ((7.0, 4, -0.3), (34.5, 3, 0.4)):
        ch = shunting_chain(rng, bumps, 0.5)
        ch = eq(ch, ('lp', 420.0, 2), ('hp', 45.0, 2), circular=False)
        M.event(far(ch, tun, wet=0.6, dry=0.8, pan=pan), t0, 4.0)
    # a train overhead, deep above
    tr_ = train_overhead(rng, dur=12.0, wagons=10, pass_at=5.5, dust=0.4, chain=0.0)
    M.event(far(eq(tr_, ('lp', 280.0, 2), ('hp', 38.0, 2), circular=False), tun, wet=0.5, dry=1.0), 46.0, -3.0)
    # the converted wagon: a plank settles, a stove-pipe elbow ticks in the cold
    for t, lowf in ((19.6, True), (52.4, False)):
        M.event(far(P2A.timber_groan(rng, 1.2, low=lowf), tun, wet=0.5, dry=1.0, pan=0.45), t, -10.0)
    ck = metal_clank(rng, 'light')
    M.event(far(ck, tun, wet=0.6, dry=0.8, pan=0.5), 27.4, 2.0, mode='peak')
    return M.master(-25.0, lp=10500.0), (0, N)


def amb_berlin_loop():
    name = 'amb_berlin_loop'
    rng = R(name)
    M = Mix()
    loop_ir = ir_loop(seed_of(name, 1))
    farir = ir_outdoor_far(seed_of(name, 2))
    # dawn air: soft gusts over the cleared ground, a little snow, the city waking far away
    g = gust_curve(N, rng, [(4.0, 0.55, 2.0, 3.0), (17.0, 0.8, 2.5, 3.5), (31.0, 0.5, 2.0, 2.5), (45.0, 0.9, 2.5, 3.5)],
                   base=0.3, turb=0.07, turb_rate=0.5)
    M.bed(wind(N, rng, g, lp_base=260.0, lp_gust=1000.0, whistle=0.0, hush=0.05, corr=0.35, pan_sweep=0.3), 0.0)
    city = shaped_noise(N, rng, lambda f: mag_bp(f, 25.0, 220.0, 2), ch=2, corr=0.75)
    city *= (1.0 + 0.3 * smooth_periodic(N, 10, rng))[:, None]
    M.bed(city, -8.0)
    flakes = grain_cloud(rng, N / SR, np.full(N, 7.0), 3500.0, 9000.0, 0.001, 0.003)
    M.bed(np.stack([flakes, np.roll(flakes, secs(2.3))], axis=1), -29.0)
    # the trolley wire above the loop: a faint electrical hum and aeolian singing that follows the gusts
    gn = (g - g.mean()) / (g.std() + 1e-9)
    wires = np.zeros(N)
    for (f, a) in [(138.0, 1.0), (143.5, 0.8), (276.0, 0.25), (287.0, 0.2), (414.0, 0.08)]:
        wires += a * periodic_tone(N, f, rng, fm=0.025 * gn)
    wires *= np.clip(g / g.max(), 0, 1) ** 1.5
    M.bed(pan2(wires, 0.05), -13.0)
    M.bed(pan2(hum(N, rng, 100.0), 0.0), -27.0)
    # tram 74 standing in the loop (left of centre): its compressor starts twice
    for t0 in (6.5, 37.0):
        M.event(far(compressor(rng, 5.2), loop_ir, wet=0.3, dry=1.0, pan=-0.3), t0, -4.0)
    # warm air breathing out of the advertising column's grate, steam hissing softly (right of centre)
    br = shaped_noise(N, rng, lambda f: mag_bp(f, 150.0, 1400.0, 2))
    br = br[:, 0] if br.ndim == 2 else br
    br *= 0.6 + 0.4 * (0.5 + 0.5 * np.sin(TAU * 5 * np.arange(N) / N + 1.1))
    M.bed(pan2(br, 0.3), -17.0)
    steam = shaped_noise(N, rng, lambda f: mag_bp(f, 1500.0, 5000.0, 2))
    steam = steam[:, 0] if steam.ndim == 2 else steam
    M.bed(pan2(steam * (0.5 + 0.5 * np.abs(smooth_periodic(N, 14, rng))), 0.3), -27.0)
    # the first lorry idling at the freight hatch (right), its tailgate and the crates
    lorry = eq(lorry_idle(N, rng), ('lp', 900.0, 2), circular=True)
    lst = pan2(lorry, 0.65)
    M.bed(lst + 0.25 * fftconv(lst, loop_ir, circular=True), -14.0)
    for t, kind in ((14.2, 'tail'), (21.0, 'crate'), (22.4, 'crate'), (49.6, 'crate')):
        if kind == 'tail':
            ev_ = metal_clank(rng, 'heavy')
            lvl = 0.0
        else:
            ev_ = wood_knock(rng, rng.uniform(90.0, 130.0), 0.6, hard=0.4)
            lvl = -3.0
        M.event(far(ev_, loop_ir, wet=0.45, dry=0.8, pan=0.7, lp=3800.0), t, lvl + 10.0, mode='peak')
    # crane chains of the axis, far off (left), and a crane motor's whine
    for t0 in (9.0, 41.5):
        M.event(far(crane_chain(rng, 2.6), farir, wet=0.9, dry=0.2, pan=-0.6, lp=2600.0), t0, -6.0)
    tt = np.arange(secs(6.0)) / SR
    whine = (np.sin(TAU * np.cumsum(310.0 * (1 + 0.06 * smoothstep(tt / 2.0))) / SR) * bump(len(tt), 1.0, 1.6,
                                                                                               peak_at=2.4))
    M.event(far(whine, farir, wet=1.0, dry=0.1, pan=-0.55, lp=1400.0), 26.0, -18.0)
    # another line's tram bell far away (towards the Great Hall)
    fb = tram_bell(rng, 2, 760.0)
    M.event(far(eq(fb, ('lp', 2200.0, 2), circular=False), farir, wet=1.0, dry=0.15, pan=0.45), 33.4, -8.0)
    # early-shift workers crunching past the shelter, a murmur (unintelligible by construction)
    M.event(eq(P2A.snow_steps(rng, 7, 0.55, -0.5, 0.2), ('lp', 3000.0, 2), circular=False), 52.0, -12.0)
    M.event(eq(P2A.snow_steps(rng, 6, 0.6, 0.6, -0.1), ('lp', 2600.0, 2), circular=False), 18.2, -14.0)
    v = C3A.voice(rng, 3.6, 118.0, 'even', pause=(0.4, 0.9), phrase=(0.8, 1.6))
    M.event(far(eq(v, ('hp', 140.0, 2), ('lp', 2400.0, 2), circular=False), loop_ir, wet=0.4, dry=0.9, pan=-0.1), 28.6,
            -20.0)
    return M.master(-24.0, lp=11000.0), (0, N)


def amb_berlin_annex():
    name = 'amb_berlin_annex'
    rng = R(name)
    M = Mix()
    hall = ir_annex(seed_of(name, 1))
    # the street above as a rumble (a tram passing over once), the hall's air
    street = shaped_noise(N, rng, lambda f: mag_bp(f, 20.0, 130.0, 2), ch=2, corr=0.8)
    street *= (1.0 + 0.35 * smooth_periodic(N, 9, rng))[:, None]
    M.bed(street, -7.0)
    air = shaped_noise(N, rng, lambda f: mag_bp(f, 60.0, 2000.0, 2) * (np.maximum(f, 20.0) / 200.0) ** -0.6, ch=2,
                       corr=0.4)
    M.bed(air, -10.0)
    # two huge fans behind the grille (left): blade tones 31 / 33 Hz beating against each other
    f1 = fan(N, rng, rot_hz=5.5, blades=6, lo=80.0, hi=1200.0, tone=0.35, depth=0.3)
    f2 = fan(N, rng, rot_hz=5.1666666667, blades=6, lo=90.0, hi=1100.0, tone=0.35, depth=0.3)
    fans = pan2(f1, -0.65) + pan2(f2, -0.35)
    fans = eq(fans, ('lp', 1600.0, 2), circular=True)
    M.bed(fans + 0.35 * fftconv(fans, hall, circular=True), -2.0)
    # fluorescent tubes: ballast hum and buzz; one tube flickering for a moment
    M.bed(pan2(eq(hum(N, rng, 100.0, buzz=0.3), ('lp', 5000.0, 2), circular=True), 0.2), -19.0)
    fl = np.zeros(secs(1.4))
    for k in range(9):
        place(fl, impact(rng, random_modes(rng, 2000.0, 7000.0, 4, 0.008, 0.03), 0.05, hard=0.9) *
              rng.uniform(0.4, 1.0), secs(k * rng.uniform(0.08, 0.17)), circular=False)
    M.event(far(fl, hall, wet=0.3, dry=1.0, pan=0.35), 18.6, 4.0, mode='peak')
    # tube capsules landing at the station (right of centre)
    for t0, pan in ((11.0, 0.35), (42.2, 0.4)):
        M.event(far(capsule(rng), hall, wet=0.4, dry=1.0, pan=pan), t0, 1.0)
    # typewriters muffled behind the glass of the typists' room (right)
    for t0, chars, bell in ((3.5, 26, 18), (24.0, 34, None), (50.5, 22, 15)):
        tw = C3A.typewriter(rng, chars, bell_at=bell)
        tw = eq(tw, ('lp', 1300.0, 3), ('hp', 120.0, 2), circular=False)
        M.event(far(tw, hall, wet=0.6, dry=0.5, pan=0.7), t0, -9.0)
    # a card drawer, a sliding ladder, a stamp at the counter, a capsule station lid
    M.event(far(drawer_slide(rng), hall, wet=0.4, dry=1.0, pan=-0.1), 31.0, -6.0)
    M.event(far(sliding_ladder(rng), hall, wet=0.45, dry=1.0, pan=0.0), 55.0, -8.0)
    st = stamp_take(rng, 'steel')
    M.event(far(st, hall, wet=0.4, dry=0.8, pan=0.55), 36.4, 6.0, mode='peak')
    # a tram passing over the street above (rumble swell, rail joints through the concrete)
    tr_ = train_overhead(rng, dur=10.0, wagons=1, pass_at=4.5, dust=0.0, chain=0.0)
    M.event(far(eq(tr_, ('lp', 200.0, 2), circular=False), hall, wet=0.4, dry=1.0), 22.0, -6.0)
    out = M.master(-25.0, lp=11000.0)
    return glue(out, -25.0 + 6.0, ratio=1.6, circular=True), (0, N)


# =============================================================================== one-shots
def stamp_take(rng: np.random.Generator, surface: str) -> np.ndarray:
    """Ink pad dab at 0.00 s, lift, the stroke at 0.36 s (both stamps share this timing: the match cut).
    surface 'wood' = the Karsk siding office desk, 'steel' = the annex counter (linoleum over steel)."""
    n = secs(1.3)
    y = np.zeros(n)
    t = np.arange(n) / SR
    pad = noise_burst(0.07, rng, 150.0, 1800.0, 0.035, attack=0.002)
    pad = 0.35 * norm_peak(pad)
    pad[:secs(0.05)] += 0.2 * np.sin(TAU * 260.0 * t[:secs(0.05)]) * np.exp(-t[:secs(0.05)] / 0.012)
    place(y, pad, 0, circular=False)
    hit_at = secs(0.36)
    m = n - hit_at
    tb = np.arange(m) / SR
    if surface == 'wood':
        desk = wood_knock(rng, 96.0, 0.9, hard=0.32)[:m]
        slap = noise_burst(0.05, rng, 180.0, 2400.0, 0.02, attack=0.0008)
        body = 0.45 * np.sin(TAU * 58.0 * tb) * np.exp(-tb / 0.06) * smoothstep(tb / 0.002)
        handle = modal([(1420.0, 0.6, 0.035), (2210.0, 0.4, 0.025)], 0.12, seed=int(rng.integers(1 << 30)))
    else:
        desk = impact(rng, random_modes(rng, 170.0, 2600.0, 10, 0.12, 0.55, tilt=0.6), 0.9, hard=0.55,
                      noise_amt=0.3)[:m] * 0.55
        slap = noise_burst(0.04, rng, 300.0, 4200.0, 0.015, attack=0.0006)
        body = 0.5 * np.sin(TAU * 72.0 * tb) * np.exp(-tb / 0.04) * smoothstep(tb / 0.0015)
        handle = modal([(1850.0, 0.5, 0.03), (2950.0, 0.35, 0.02)], 0.1, seed=int(rng.integers(1 << 30)))
    strike = body.copy()
    strike[:min(m, len(desk))] += desk[:m]
    strike[:len(slap)] += 0.6 * norm_peak(slap)
    strike[:len(handle)] += 0.15 * handle
    place(y, strike, hit_at, circular=False)
    return y


def c4_stencil_brush():
    rng = R('c4_stencil_brush')
    n = secs(3.8)
    y = np.zeros(n)
    t = 0.1
    while t < 2.9:
        hit = noise_burst(0.07, rng, 250.0, 3800.0, 0.035, attack=0.002)
        knock = wood_knock(rng, rng.uniform(150.0, 190.0), 0.25, hard=0.2)
        ev_ = 0.6 * norm_peak(hit)
        ev_[:len(knock)] += 0.3 * norm_peak(knock)[:len(ev_)]
        place(y, ev_ * rng.uniform(0.7, 1.0), secs(t), circular=False)
        tack = noise_burst(0.02, rng, 1500.0, 6000.0, 0.008, attack=0.0005)
        place(y, 0.16 * norm_peak(tack), secs(t + rng.uniform(0.05, 0.08)), circular=False)
        t += rng.uniform(0.15, 0.24) if rng.random() > 0.15 else rng.uniform(0.38, 0.5)
    wipe = noise_burst(0.4, rng, 900.0, 5000.0, 1e6, attack=0.0)
    wipe = norm_peak(wipe) * bump(len(wipe), 0.08, 0.12, peak_at=0.15)
    place(y, 0.3 * wipe, secs(3.0), circular=False)
    tink = impact(rng, random_modes(rng, 900.0, 4800.0, 6, 0.05, 0.25), 0.5, hard=0.5)
    place(y, 0.28 * tink, secs(3.18), circular=False)
    y = eq(y, ('hp', 80.0, 2), circular=False)
    st = far(y, ir_tunnel(seed_of('c4_stencil_brush', 1)), wet=0.22, dry=1.0, pan=0.05)
    return one_shot(st[:secs(5.0)], -9.0, fout=0.6), None


def c4_card_tear():
    rng = R('c4_card_tear')
    n = secs(1.4)
    y = np.zeros(n)
    flex = paper_rustle(rng, 0.22, 0.25, 1)
    place(y, 0.18 * flex, secs(0.0), circular=False)
    holes = 28
    u = np.linspace(0.0, 1.0, holes)
    times = 0.2 + 0.42 * (u ** 0.8) + rng.normal(0, 0.004, holes)
    for k, t in enumerate(times):
        ck = noise_burst(0.006, rng, 2200.0, 9000.0, 0.002, attack=0.0002)
        place(y, ck * rng.uniform(0.45, 1.0) * (0.7 + 0.3 * np.sin(np.pi * u[k])), secs(t), circular=False)
    fib = noise_burst(0.5, rng, 1500.0, 8000.0, 1e6, attack=0.0)
    fib = norm_peak(fib) * bump(len(fib), 0.08, 0.1, peak_at=0.24) * (0.6 + 0.4 * np.abs(ctrl_noise(len(fib), 60.0,
                                                                                                    rng)))
    place(y, 0.32 * fib, secs(0.2), circular=False)
    sep = noise_burst(0.06, rng, 200.0, 1400.0, 0.03, attack=0.001)
    place(y, 0.5 * norm_peak(sep), secs(0.66), circular=False)
    st = np.stack([y, np.roll(y, 9)], axis=1)
    return one_shot(st, -10.0, fout=0.3), None


def c4_stamp_accept():
    rng = R('c4_stamp_accept')
    y = stamp_take(rng, 'wood')
    st = far(y, ir_booth(seed_of('c4_stamp_accept', 1)), wet=0.3, dry=1.0, pan=0.0)
    return one_shot(st[:secs(2.0)], -6.0, fout=0.4), None


def c4_stamp_dispatch():
    rng = R('c4_stamp_dispatch')
    y = stamp_take(rng, 'steel')
    st = far(y, ir_annex(seed_of('c4_stamp_dispatch', 1)), wet=0.35, dry=1.0, pan=0.0)
    return one_shot(st[:secs(2.4)], -6.0, fout=0.5), None


def _bell(name: str, strikes: int):
    rng = R(name)
    b = tram_bell(rng, strikes, 820.0, gap=0.26, dur=3.8)
    st = far(b, ir_loop(seed_of(name, 1)), wet=0.45, dry=1.0, pan=-0.1)
    return one_shot(st[:secs(4.6)], -7.0, fout=0.8), None


def c4_bell_once():
    return _bell('c4_bell_once', 1)


def c4_bell_twice():
    return _bell('c4_bell_twice', 2)


def c4_train_overhead():
    rng = R('c4_train_overhead')
    y = train_overhead(rng, dur=12.0, wagons=10, pass_at=5.5, dust=1.0, chain=1.0)
    st = far(y, ir_cellar(seed_of('c4_train_overhead', 1)), wet=0.4, dry=1.0, pan=0.0)
    st[:, 1] = np.roll(st[:, 1], 23)
    return one_shot(st[:secs(13.0)], -6.0, fin=0.3, fout=2.0), None


def c4_lamp_out():
    rng = R('c4_lamp_out')
    n = secs(2.4)
    t = np.arange(n) / SR
    off = 0.62
    h = (np.sin(TAU * 100.0 * t) + 0.45 * np.sin(TAU * 200.0 * t) + 0.25 * np.sin(TAU * 300.0 * t))
    buzz = noise_burst(2.4, rng, 1500.0, 5000.0, 1e6, attack=0.0) * 0.08
    hm = (0.25 * h + buzz) * smoothstep(t / 0.05) * np.clip((off + 0.03 - t) / 0.03, 0, 1)
    y = hm.copy()
    sw = impact(rng, random_modes(rng, 900.0, 5200.0, 7, 0.02, 0.08), 0.18, hard=0.85, noise_amt=0.5)
    place(y, 0.8 * sw, secs(off - 0.012), circular=False)
    sw2 = impact(rng, random_modes(rng, 1200.0, 6000.0, 5, 0.015, 0.05), 0.1, hard=0.9, noise_amt=0.4)
    place(y, 0.35 * sw2, secs(off + 0.05), circular=False)
    for tt, a in ((1.1, 0.06), (1.62, 0.035)):
        tk = impact(rng, random_modes(rng, 3500.0, 8000.0, 3, 0.006, 0.02), 0.04, hard=0.9)
        place(y, a * tk, secs(tt), circular=False)
    st = far(y, ir_tunnel(seed_of('c4_lamp_out', 1)), wet=0.3, dry=1.0, pan=0.0)
    return one_shot(st[:secs(3.6)], -9.0, fin=0.04, fout=0.9), None


# =============================================================================== the bayan (free reeds)
def reed_note(midi: float, dur: float, vel: float = 0.5, seed: int = 0, swell=(0.35, 0.3), reversal: float | None
              = None, octave_down: float = 0.35, air: float = 0.05) -> np.ndarray:
    """A bayan voice (stereo): two dry-tuned treble reeds and a reed an octave lower, a rich, slightly nasal
    spectrum (formant near 1.4 kHz), the bellows' swell / decay, an optional bellows reversal (a short dip), the
    breath of the air through the valves and a soft key click."""
    rng = np.random.default_rng(seed)
    n = secs(dur)
    t = np.arange(n) / SR
    f0 = float(midi_hz(midi))
    K = max(2, int(9000 / (f0 * 1.05)))
    k = np.arange(1, K + 1)
    amps = k ** -1.05 * (1.0 + 1.6 * np.exp(-0.5 * ((k * f0 - 1400.0) / 500.0) ** 2))
    amps[1::2] *= 0.75
    tab = make_table(amps)
    y = np.zeros(n)
    for det, g in ((-0.0006, 0.5), (0.0007, 0.5)):
        y += g * wt_read(tab, np.cumsum(np.full(n, f0 * (1.0 + det))) / SR + rng.uniform())
    if octave_down:
        y += octave_down * wt_read(tab, np.cumsum(np.full(n, f0 * 0.5)) / SR + rng.uniform())
    a, r = swell
    env = np.minimum(smoothstep(t / max(a * dur, 0.08)), 1.0) * np.clip((dur - t) / max(r * dur, 0.08), 0, 1) ** 1.3
    if reversal is not None:
        env *= 1.0 - 0.55 * np.exp(-0.5 * ((t - reversal * dur) / 0.06) ** 2)
    env *= 1.0 + 0.04 * ctrl_noise(n, 1.5, rng)
    y = y * env
    br = noise_burst(dur, rng, 250.0, 2200.0, 1e6, attack=0.0)
    y += air * norm_peak(br) * env
    click = noise_burst(0.01, rng, 1000.0, 6000.0, 0.004)
    y[:len(click)] += 0.04 * norm_peak(click)
    y = eq(y, ('hp', 60.0, 2), ('lp', 6500.0, 2), circular=False) * vel
    return pan2(y, float(np.interp(midi, [40, 80], [-0.2, 0.25])))


def bayan_breath(T: Track, beat: float, beats: float, midis, vel: float = 0.4, reversal: float = 0.52):
    for i, m in enumerate(midis):
        sig = reed_note(m, beats * T.spb, vel=vel * (1.0 if i == 0 else 0.8), seed=T.sd(), swell=(0.42, 0.4),
                        reversal=reversal)
        T.put('bayan', beat, sig, jitter=0.01)


REED_EQ = (('hp', 70, 2), ('bell', 1400, -2.0, 1.2), ('lp', 5200, 2))
LOW_STR_EQ = (('hp', 42, 2), ('ls', 110, -2.5), ('bell', 300, 1.0, 1.2), ('bell', 700, -1.0, 1.2), ('lp', 5000, 2))


# =============================================================================== music
def mus_c4_karsk():
    """Sparse low strings in D Aeolian, a bayan breath twice per loop, one quiet echo of K on the felt piano."""
    name = 'mus_c4_karsk'
    T = Track(name, bpm=54, beats=64, loop=True, seed=seed_of(name))
    plan = [(0, [38, 45], 8.6), (8, [38, 45, 53], 8.6), (16, [34, 41], 8.6), (24, [38, 43, 46], 8.6),
            (32, [38, 45], 8.6), (40, [38, 45, 50], 8.6), (48, [40, 48], 8.6), (56, [33, 40], 8.6)]
    for b, ch, d in plan:
        T.strings(b, d, ch, vel=0.40, stem='low', attack=2.4, release=3.2, bright=0.26, vib=3.5, voices=3,
                  bass_boost=1.0)
    # a cello line descending slowly in the second half (D3 C3 Bb2 A2), long bows
    for b, m in ((32, 50), (40, 48), (48, 46), (56, 45)):
        T.strings(b + 0.5, 7.2, [m], vel=0.30, stem='cello', attack=1.8, release=2.6, bright=0.3, vib=5.0, voices=2)
    # the bayan breath: a chord swells (bellows pushed), turns, and falls away
    bayan_breath(T, 9.0, 7.0, [50, 53, 57], vel=0.36)            # Dm (D3 F3 A3)
    bayan_breath(T, 41.0, 7.0, [50, 52, 57], vel=0.34)           # Dsus2 (D3 E3 A3)
    bayan_breath(T, 57.5, 5.5, [45, 52], vel=0.26, reversal=0.6)  # A2 E3, an open fifth into the loop
    # low plucks, very soft
    T.pluck([(0, 2, 38), (16, 2, 34), (32, 2, 38), (48, 2, 40)], vel=0.42, t60=2.4, bright=0.3)
    # K echoes once, low and quiet, on the felt piano
    T.piano(tr(K_A, octave=-1), vel=0.30, beat0=24, felt=0.85, decay=0.9, pan=0.1)
    ir = hall_ir(seed_of(name, 1), rt_low=3.0, rt_high=1.2, predelay=0.03)
    mix = {'low': (0.0, 0.28, LOW_STR_EQ), 'cello': (-3.0, 0.3, STR_EQ), 'bayan': (-2.0, 0.22, REED_EQ),
           'pluck': (-10.0, 0.3, PLUCK_EQ), 'piano': (-6.0, 0.32, C3A.FELT_EQ)}
    out = T.mixdown(mix, ir, target_rms=-22.0, master_lp=8500.0)
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)       # the loop point sits in a rest
    return out, (0, out.shape[0])


MACHINE_ACC = [0.32, 0.17, 0.17, 0.28, 0.17, 0.17, 0.26, 0.19]       # 3+3+2 accents of the pulse


def machine_tick(rng: np.random.Generator, heavy: bool = False) -> np.ndarray:
    """A dry mechanical tick of a card machine (mono); heavy = the card-feed 'chunk' every two bars."""
    if heavy:
        y = impact(rng, random_modes(rng, 160.0, 2200.0, 8, 0.03, 0.12), 0.25, hard=0.4, noise_amt=0.5,
                   noise_decay=0.01)
    else:
        y = impact(rng, random_modes(rng, 1800.0, 5200.0, 4, 0.008, 0.03), 0.08, hard=0.8, noise_amt=0.4,
                   noise_decay=0.003)
    return y


def mus_c4_berlin():
    """Cool, mechanical: a muted-piano pulse in 3+3+2 over the G pedal, a card machine's tick, the B motif."""
    name = 'mus_c4_berlin'
    T = Track(name, bpm=72, beats=64, loop=True, seed=seed_of(name))
    rng = np.random.default_rng(seed_of(name, 2))
    # pulse pitches per 4-beat bar (low note, high note) following the harmony
    bars = [('Gm', 55, 62), ('Gm', 55, 62), ('Gm', 55, 62), ('Gm', 55, 62), ('Eb', 51, 58), ('Eb', 51, 58),
            ('Cm', 48, 55), ('Cm', 48, 55), ('Gm', 55, 62), ('Gm', 55, 62), ('Ab', 56, 63), ('Ab', 56, 63),
            ('Eb', 51, 58), ('Eb', 51, 58), ('Dsus', 50, 57), ('Dsus', 50, 57)]
    for i, (_, lo, hi) in enumerate(bars):
        b0 = 4 * i
        for k in range(8):
            m = lo if k in (0, 3, 6) else hi
            T.piano([(b0 + 0.5 * k, 0.5, m)], vel=MACHINE_ACC[k], stem='pulse', felt=1.0, decay=0.35, legato=0.55)
            sig = to_stereo(machine_tick(rng, heavy=(k == 0 and i % 2 == 0)))
            T.put('machine', b0 + 0.5 * k, sig * (0.9 if k in (0, 3, 6) else 0.55), jitter=0.002)
    pads = [(0, [43, 50, 58]), (16, [39, 46, 55]), (24, [36, 43, 51]), (32, [43, 50, 58]), (40, [44, 51, 60]),
            (48, [39, 46, 55]), (56, [38, 45, 50])]
    for b, ch in pads:
        d = 16.4 if b == 0 else 8.4
        T.brass(b, d, ch, vel=0.30, attack=1.2, release=2.2, bright=0.28)
    for b in range(0, 64, 16):
        T.brass(b, 16.6, [31, 43], vel=0.36, stem='pedal', attack=1.8, release=2.6, bright=0.18)
    T.strings(16, 15.5, [79], vel=0.13, stem='strings_hi', harmonic=True, attack=3.0, vib=2.5)
    T.strings(48, 15.0, [74], vel=0.12, stem='strings_hi', harmonic=True, attack=3.0, vib=2.5)
    T.celesta(tr(B_1, octave=1), vel=0.34, beat0=32, pan=0.25)
    T.piano(tr(B_2, octave=-1), vel=0.34, beat0=48, felt=1.0, decay=0.6, stem='low', legato=0.9)
    ir = hall_ir(seed_of(name, 1), rt_low=2.6, rt_high=1.1, predelay=0.03)
    mix = {'pulse': (-1.0, 0.18, MUTED_EQ), 'machine': (-14.0, 0.12, (('hp', 200, 2), ('lp', 7000, 2))),
           'brass': (-4.0, 0.26, BRASS_EQ), 'pedal': (-7.0, 0.22, BRASS_EQ), 'strings_hi': (-16.0, 0.45, STR_HI_EQ),
           'celesta': (-3.0, 0.36, CEL_EQ), 'low': (-3.0, 0.24, MUTED_EQ)}
    out = T.mixdown(mix, ir, target_rms=-21.0, master_lp=9500.0)
    out = np.roll(out, int(round(0.25 * T.spb * SR)), axis=0)      # the loop point sits between two pulses
    return out, (0, out.shape[0])


def mus_c4_voices():
    """Both themes on one clock: the clock alone, the Karsk drone and K, then B over the G pedal, both together
    (B bends its Eb to E where they meet), the clock alone again.  The first 24 beats (24 s) are a full arc."""
    name = 'mus_c4_voices'
    T = Track(name, bpm=60, beats=48, loop=True, seed=seed_of(name))
    rng = np.random.default_rng(seed_of(name, 2))
    for i in range(48):
        tk = clock_tick(np.random.default_rng(seed_of(name, 10 + i % 6)), i % 2 == 1)
        T.put('clock', i, to_stereo(tk) * (1.0 if i % 2 == 0 else 0.84), jitter=0.0)
    T.strings(0.0, 22.5, [38, 45], vel=0.36, stem='drone', attack=4.0, release=3.5, bright=0.2, vib=3.0, voices=4)
    T.strings(24.0, 18.5, [38, 45], vel=0.32, stem='drone', attack=3.0, release=4.0, bright=0.2, vib=3.0, voices=4)
    T.brass(14.0, 9.5, [31, 43], vel=0.30, stem='pedal', attack=2.5, release=3.0, bright=0.16)
    T.brass(24.0, 16.0, [31, 43], vel=0.28, stem='pedal', attack=2.0, release=4.0, bright=0.16)
    # Karsk: K_A on the felt piano
    T.piano(K_A, vel=0.40, beat0=6, felt=0.8, decay=0.95, pan=-0.12)
    # Berlin: the first half of B on the celesta over the G pedal
    T.celesta(tr(B_1[:7], octave=0), vel=0.36, beat0=15, pan=0.22)
    # together: K_B on the piano and B_2 on the celesta, B's Eb bent to E where they meet
    b2 = [(b, d, 64 if m == 63 else m) for (b, d, m) in B_2]
    T.piano(K_B, vel=0.36, beat0=26, felt=0.8, decay=0.95, pan=-0.12)
    T.celesta(tr(b2, octave=1), vel=0.30, beat0=27, pan=0.22)
    T.strings(34.0, 8.0, [69, 74], vel=0.12, stem='hi', harmonic=True, attack=2.5, release=3.0, vib=2.0)
    _ = rng
    ir = hall_ir(seed_of(name, 1), rt_low=3.2, rt_high=1.3, predelay=0.03)
    mix = {'clock': (-7.0, 0.12, (('hp', 300, 2), ('lp', 8000, 2))), 'drone': (-3.0, 0.28, C3A.DRONE_EQ),
           'pedal': (-8.0, 0.22, BRASS_EQ), 'piano': (0.0, 0.3, C3A.FELT_EQ), 'celesta': (-3.0, 0.38, CEL_EQ),
           'hi': (-15.0, 0.45, STR_HI_EQ)}
    out = T.mixdown(mix, ir, target_rms=-21.0, master_lp=9000.0)
    out = np.roll(out, int(round(0.5 * T.spb * SR)), axis=0)       # the loop point sits between two ticks
    return out, (0, out.shape[0])


# =============================================================================== registry
BUILDERS = {
    'amb_karsk_cellar': ('amb', amb_karsk_cellar),
    'amb_karsk_tunnel': ('amb', amb_karsk_tunnel),
    'amb_berlin_loop': ('amb', amb_berlin_loop),
    'amb_berlin_annex': ('amb', amb_berlin_annex),
    'mus_c4_karsk': ('music', mus_c4_karsk),
    'mus_c4_berlin': ('music', mus_c4_berlin),
    'mus_c4_voices': ('music', mus_c4_voices),
    'c4_stencil_brush': ('sfx', c4_stencil_brush),
    'c4_card_tear': ('sfx', c4_card_tear),
    'c4_stamp_accept': ('sfx', c4_stamp_accept),
    'c4_stamp_dispatch': ('sfx', c4_stamp_dispatch),
    'c4_bell_once': ('sfx', c4_bell_once),
    'c4_bell_twice': ('sfx', c4_bell_twice),
    'c4_train_overhead': ('sfx', c4_train_overhead),
    'c4_lamp_out': ('sfx', c4_lamp_out),
}
# where each sound is (or should be) wired -- the --list output and documentation/asset_manifest_parts/c4_cast_audio.md
WIRING = {
    'amb_karsk_cellar': 'L_C4_Tunnels.tscn ambience; c4.json switches L_C4_TunnelsA "ambience"',
    'amb_karsk_tunnel': 'c4.json switches L_C4_TunnelsB "ambience"',
    'amb_berlin_loop': 'L_C4_Annex.tscn ambience; c4.json switches L_C4_AnnexA "ambience"',
    'amb_berlin_annex': 'c4.json switches L_C4_AnnexB "ambience"',
    'mus_c4_karsk': 'L_C4_Tunnels.tscn music; c4.json switches L_C4_TunnelsA / B "music"',
    'mus_c4_berlin': 'L_C4_Annex.tscn music; c4.json switches L_C4_AnnexA / B "music"',
    'mus_c4_voices': 'LS_C4_Voices (cinematic cue {"music": "mus_c4_voices"})',
    'c4_stencil_brush': 'LS_C4_Number n1 / n2',
    'c4_card_tear': 'LS_C4_Card c1 / c2',
    'c4_stamp_accept': 'LS_C4_Stamp s1 / s2',
    'c4_stamp_dispatch': 'LS_C4_Stamp s3',
    'c4_bell_once': 'LS_C4_Voices v2 (c4d = name_marta)',
    'c4_bell_twice': 'LS_C4_Voices v2 (c4d = protect_marta)',
    'c4_train_overhead': 'LS_C4_Homeward w3 / tunnels level script (every 20-40 s, C4_DESIGN 4.1)',
    'c4_lamp_out': 'LS_C4_Voices v4 (the lamp goes out)',
}
# loudness envelope the checks enforce: (min RMS, max RMS, max peak) in dBFS (same windows as round 8)
TARGETS = {'amb': (-28.0, -21.0, -2.5), 'music': (-25.0, -19.0, -0.8), 'loop': (-36.0, -19.0, -2.5),
           'sfx': (-45.0, -9.0, -2.5)}


def outputs_of(name: str):
    kind, fn = BUILDERS[name]
    r = fn()
    if isinstance(r, list):
        return kind, r
    sig, loop = r
    return kind, [(name, sig, loop)]


def wav_path(kind: str, name: str) -> str:
    return os.path.join(AUDIO, kind, name + '.wav')


def build_one(name: str) -> list[dict]:
    t0 = time.time()
    kind, outs = outputs_of(name)
    rows = []
    for fname, sig, loop in outs:
        path = wav_path(kind, fname)
        st = write_wav(path, sig, loop=loop, seed=zlib.crc32(fname.encode()))
        rows.append({'name': fname, 'kind': kind, 'path': path, 'loop': loop, 'seconds': round(time.time() - t0, 1),
                     **st})
    return rows


def check_rows(rows: list[dict]) -> list[str]:
    return P2A.check_rows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--only', default='', help='comma separated builder names: ' + ', '.join(BUILDERS))
    ap.add_argument('--jobs', type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--no-analysis', action='store_true')
    ap.add_argument('--no-spectro', action='store_true')
    args = ap.parse_args()
    if args.list:
        for n, (k, _) in BUILDERS.items():
            print(f'{k:6s} {n:20s} {WIRING.get(n, "")}')
        return
    names = [n.strip() for n in args.only.split(',') if n.strip()] or list(BUILDERS)
    for n in names:
        if n not in BUILDERS:
            sys.exit(f'unknown builder {n!r}; known: {", ".join(BUILDERS)}')
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max(1, min(args.jobs, len(names)))) as ex:
        built = [r for rows in ex.map(build_one, names) for r in rows]
    for b in built:
        print(f"  built {b['name']:<22}{b['seconds']:>6.1f}s  {b['frames']:>8} fr x {b['channels']} ch  "
              f"loop {b['loop']}  clipped {b['clipped_samples']}")
        if C3A.ensure_import(b['path']):
            print(f"  wrote {os.path.relpath(b['path'], ROOT)}.import")
    print(f'synthesis done in {time.time() - t0:.1f}s')
    fails = check_rows(built)
    if not args.no_analysis:
        import analyze
        preview = None
        if not args.no_spectro:
            preview = analyze.PREVIEW
            analyze.ensure_preview_dir()
        rows = [C3A.analyse(b['path'], b['name'], preview if b['kind'] != 'sfx' or b['loop'] else None) for b in built]
        C3A.print_rows(rows)
        os.makedirs(analyze.PREVIEW, exist_ok=True)
        with open(os.path.join(analyze.PREVIEW, 'c4_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, default=str)
    for f in fails:
        print('  FAIL', f)
    print('OK: c4 audio checks pass' if not fails else f'FAIL: {len(fails)} c4 audio checks')
    print(f'total {time.time() - t0:.1f}s')
    if fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
