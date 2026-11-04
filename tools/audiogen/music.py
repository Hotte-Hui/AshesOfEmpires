"""music.py -- original score for the vertical slice (all notes composed here, all sounds synthesised).

Motifs
------
K ("Karsk", Alexei): D Aeolian.  K_A asks (D5 A4 E5 | F5 E5 C5 -- ends open on the b7),
    K_B answers and closes (D5 A4 G4 | F4 E4 D4).  Felt piano, doubled by soft plucks.
B ("Berlin", Konrad): G Aeolian, even quarter-note pulse, narrow range, a b6 neighbour sigh
    (G4 Bb4 A4 G4 | D5 Eb5 D5 | C5 Bb4 A4 Bb4 | G4).  Muted piano and celesta over a low
    brass pedal on G -- order imposed from below.
Menu theme: K in D, B in G, then both together in the shared D-Aeolian / G-Dorian collection
    (B "bends" Eb -> E where they meet).  Finale X1: the motifs meet and stop on an A/Bb rub
    inside Bbmaj7/D -- unresolved.
No national cliches: no folk scales with augmented seconds, no balalaika/accordion, no
march rhythms or fanfares; restrained chamber-orchestral minimalism.

Rendering: every note is an event placed on a circular timeline (loops) so note releases and
the generated convolution-reverb tail wrap from the end into the start -> seamless loops.
"""
from __future__ import annotations

import numpy as np

from dsp import (SR, secs, db2a, rms, place, eq, make_ir, fftconv, to_stereo, limiter,
                 normalize_rms, remove_dc, fade, pan2, smoothstep, shaped_noise, mag_bp, glue, a2db)
from instruments import (string_note, brass_note, piano_note, celesta_note, ks_pluck, modal,
                         ctrl_noise)

# ----------------------------------------------------------------------------- motifs (beat, dur, midi)
K_A = [(0, 1.5, 74), (1.5, 0.5, 69), (2, 2, 76), (4, 1.5, 77), (5.5, 0.5, 76), (6, 2, 72)]
K_B = [(0, 1.5, 74), (1.5, 0.5, 69), (2, 2, 67), (4, 1, 65), (5, 1, 64), (6, 2, 62)]
B_1 = [(0, 1, 67), (1, 1, 70), (2, 1, 69), (3, 1, 67), (4, 2, 74), (6, 1, 75), (7, 1, 74),
       (8, 1, 72), (9, 1, 70), (10, 1, 69), (11, 1, 70), (12, 4, 67)]
B_2 = [(0, 1, 67), (1, 1, 70), (2, 1, 69), (3, 1, 67), (4, 2, 65), (6, 1, 63), (7, 1, 65), (8, 4, 62)]


def tr(motif, semis=0, beat0=0.0, octave=0):
    return [(b + beat0, d, m + semis + 12 * octave) for (b, d, m) in motif]


# ----------------------------------------------------------------------------- score / render
class Track:
    def __init__(self, name: str, bpm: float, beats: float, loop: bool = True, seed: int = 1,
                 tail: float = 0.0):
        self.name = name
        self.bpm = bpm
        self.spb = 60.0 / bpm
        self.loop = loop
        self.n = int(round(beats * self.spb * SR))
        if loop:
            assert abs(beats * self.spb * SR - self.n) < 1e-6, 'loop length must be whole samples'
        self.tail = 0 if loop else secs(tail)
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.stems: dict[str, np.ndarray] = {}
        self.count = 0

    def _buf(self, stem: str) -> np.ndarray:
        if stem not in self.stems:
            self.stems[stem] = np.zeros((self.n + self.tail, 2))
        return self.stems[stem]

    def put(self, stem: str, beat: float, sig: np.ndarray, jitter: float = 0.0) -> None:
        off = self.rng.normal(0.0, jitter) if jitter else 0.0
        off = float(np.clip(off, -2.5 * jitter, 2.5 * jitter)) if jitter else 0.0
        start = int(round((beat * self.spb + off) * SR))
        buf = self._buf(stem)
        if self.loop:
            place(buf, sig, start, circular=True)
        else:
            place(buf, sig, max(0, start), circular=False)

    def sd(self) -> int:
        self.count += 1
        return self.seed * 100003 + self.count * 7919

    # ---- instrument helpers -------------------------------------------------------------
    def strings(self, beat, dur_beats, midis, vel=0.5, stem='strings', attack=1.0, release=2.4,
                bright=0.45, pan=None, swell=0.0, voices=5, harmonic=False, vib=9.0, bass_boost=1.45):
        low = min(midis) if len(midis) > 2 else None
        for i, m in enumerate(midis):
            p = pan if pan is not None else float(np.interp(m, [28, 84], [-0.45, 0.45]))
            v = vel * (1.0 + self.rng.normal(0, 0.04)) * (bass_boost if m == low else 1.0)
            a = attack * (1.0 + self.rng.normal(0, 0.12))
            sig = string_note(m, dur_beats * self.spb, vel=v, attack=max(0.15, a), release=release,
                              voices=voices, bright=bright, seed=self.sd(), pan=p, swell=swell,
                              harmonic=harmonic, vib=vib)
            self.put(stem, beat, sig, jitter=0.03)

    def brass(self, beat, dur_beats, midis, vel=0.45, stem='brass', attack=0.6, release=1.6,
              bright=0.4, swell=0.0, pan=0.0):
        for i, m in enumerate(midis):
            sig = brass_note(m, dur_beats * self.spb, vel=vel * (1.0 + self.rng.normal(0, 0.04)),
                             attack=attack, release=release, seed=self.sd(), bright=bright,
                             swell=swell, pan=pan + 0.15 * (i - (len(midis) - 1) / 2))
            self.put(stem, beat, sig, jitter=0.02)

    def piano(self, notes, vel=0.5, stem='piano', felt=0.6, beat0=0.0, pan=0.05, legato=1.05,
              decay=1.0, bright=0.62, pedal=False, max_len=None):
        for (b, d, m) in notes:
            v = float(np.clip(vel * (1.0 + self.rng.normal(0, 0.07)), 0.05, 1.0))
            sig = piano_note(m, vel=v, hold=d * self.spb * legato, felt=felt, seed=self.sd(),
                             pan=pan + float(np.interp(m, [36, 96], [-0.25, 0.25])), decay=decay,
                             bright=bright, pedal=pedal, max_len=max_len)
            self.put(stem, beat0 + b, sig, jitter=0.012)

    def celesta(self, notes, vel=0.5, stem='celesta', beat0=0.0, pan=0.2, bright=0.55):
        for (b, d, m) in notes:
            v = float(np.clip(vel * (1.0 + self.rng.normal(0, 0.06)), 0.05, 1.0))
            sig = celesta_note(m, vel=v, seed=self.sd(), pan=pan, bright=bright)
            self.put(stem, beat0 + b, sig, jitter=0.01)

    def pluck(self, notes, vel=0.5, stem='pluck', beat0=0.0, t60=2.2, bright=0.35, pan=-0.15):
        for (b, d, m) in notes:
            sig = ks_pluck(m, vel=vel * (1.0 + self.rng.normal(0, 0.06)), t60=t60, bright=bright,
                           seed=self.sd(), pan=pan)
            self.put(stem, beat0 + b, sig, jitter=0.015)

    # ---- mix ---------------------------------------------------------------------------------
    def mixdown(self, mix: dict, ir: np.ndarray, target_rms: float = -20.0, master_lp: float = 12500.0,
                cut: float | None = None, cut_fade: float = 0.03, end_fade: float = 0.0,
                rms_from: tuple[float, float] | None = None) -> np.ndarray:
        """mix: stem -> (gain_db, send, eq_bands).  Stems are levelled by their active RMS."""
        total = self.n + self.tail
        dry = np.zeros((total, 2))
        send = np.zeros((total, 2))
        for stem, buf in self.stems.items():
            g_db, snd, bands = mix.get(stem, (0.0, 0.3, ()))
            x = buf
            if bands:
                x = eq(x, *bands, circular=self.loop)
            ar = active_rms(x)
            if ar <= 0:
                continue
            x = x * (db2a(g_db - 20.0) / ar)
            dry += x
            send += x * snd
        if cut is not None:
            # hard (but click-free) cut of the dry signal; the reverb tail rings on
            c = secs(cut)
            k = secs(cut_fade)
            g = np.ones(total)
            g[c:c + k] = np.cos(0.5 * np.pi * np.arange(min(k, total - c)) / k) ** 2
            g[c + k:] = 0.0
            dry *= g[:, None]
            send *= g[:, None]
        wet = fftconv(send, ir, circular=self.loop)
        if not self.loop:
            wet = wet[:total]
        out = dry + wet
        out = eq(out, ('hp', 30.0, 2), ('lp', master_lp, 2), circular=self.loop)
        out = remove_dc(out, circular=self.loop)
        # keep the stereo image centred (pitch-dependent panning can tilt a whole cue)
        el, er = float(np.mean(out[:, 0] ** 2)), float(np.mean(out[:, 1] ** 2))
        if el > 0 and er > 0 and abs(10 * np.log10(el / er)) > 0.5:
            k = (el / er) ** 0.25
            out[:, 0] /= k
            out[:, 1] *= k
        if self.loop:
            # tame the few loudest moments (restrained score): 1.6:1 above integrated + 5 dB
            out = glue(out, float(a2db(rms(out))) + 5.0, ratio=1.6, circular=True)
        if end_fade:
            out = fade(out, 0.0, end_fade)
        if rms_from:
            a, b = secs(rms_from[0]), secs(rms_from[1])
            r = rms(out[a:b])
            out = out * (db2a(target_rms) / r)
        else:
            out = normalize_rms(out, target_rms)
        pre = float(np.max(np.abs(out)))
        out = limiter(out, -1.0, circular=self.loop)
        self.limiter_gr_db = max(0.0, 20 * np.log10(pre / 10 ** (-1 / 20))) if pre > 0 else 0.0
        print(f'[{self.name}] pre-limiter peak {20 * np.log10(pre):.1f} dBFS -> max gain reduction '
              f'{self.limiter_gr_db:.1f} dB', flush=True)
        return out


def active_rms(x: np.ndarray, floor_db: float = -35.0) -> float:
    m = np.mean(x * x, axis=1)
    win = secs(0.2)
    if len(m) <= win:
        return float(np.sqrt(m.mean()))
    c = np.concatenate([[0.0], np.cumsum(m)])
    st = (c[win:] - c[:-win]) / win
    thr = st.max() * 10 ** (floor_db / 10.0)
    act = st > thr
    if not act.any():
        return float(np.sqrt(m.mean()))
    return float(np.sqrt(st[act].mean()))


# ----------------------------------------------------------------------------- shared settings
STR_EQ = (('hp', 34, 2), ('ls', 110, -1.0), ('bell', 250, 1.0, 1.4), ('bell', 1200, -1.5, 1.5),
          ('bell', 3000, 1.5, 1.2), ('hs', 5000, 2.5), ('lp', 11000, 2))
STR_HI_EQ = (('hp', 300, 2), ('lp', 7000, 2))
BRASS_EQ = (('hp', 36, 2), ('ls', 100, -3.0), ('bell', 480, 2.0, 1.2), ('bell', 1100, 1.0, 1.0), ('lp', 3600, 2))
PIANO_EQ = (('hp', 60, 2), ('hs', 3500, 2.0), ('lp', 10000, 2))
MUTED_EQ = (('hp', 70, 2), ('bell', 300, 1.0, 1.2), ('lp', 4800, 2))
CEL_EQ = (('hp', 200, 2), ('lp', 9000, 2))
PLUCK_EQ = (('hp', 45, 2), ('lp', 4200, 2))


def hall_ir(seed: int, rt_low: float = 3.4, rt_high: float = 1.5, length: float = 4.5, predelay: float = 0.028):
    return make_ir(length=length, rt_low=rt_low, rt_high=rt_high, predelay=predelay, er_taps=12,
                   er_span=0.08, er_gain=0.35, seed=seed, lowcut=70.0, highcut=7500.0, build=0.02)


# ----------------------------------------------------------------------------- mus_karsk
DM9 = [38, 45, 50, 53, 64, 69]        # D2 A2 D3 F3 E4 A4
BBM7 = [34, 41, 46, 50, 64, 69]       # Bb1 F2 Bb2 D3 E4 A4   (Bbmaj7 #11)
GM9 = [43, 50, 58, 65, 69]            # G2 D3 Bb3 F4 A4
ASUS = [33, 40, 55, 62, 64]           # A1 E2 G3 D4 E4    (A7sus4)
AM7 = [33, 40, 55, 60, 64]            # A1 E2 G3 C4 E4
FMAJ9 = [41, 48, 57, 64, 67]          # F2 C3 A3 E4 G4
CADD9 = [40, 48, 55, 62, 67]          # E2 C3 G3 D4 G4    (Cadd9/E)
BBADD9 = [34, 41, 50, 60, 65]         # Bb1 F2 D3 C4 F4
GM_D = [38, 43, 50, 58, 69]           # D2 G2 D3 Bb3 A4   (Gm(add9)/D)
ASUS2 = [33, 40, 50, 52, 57]          # A1 E2 D3 E3 A3


def mus_karsk() -> tuple[np.ndarray, tuple[int, int]]:
    T = Track('mus_karsk', bpm=60, beats=96, loop=True, seed=11)
    plan = [(0, DM9, 0.40), (8, BBM7, 0.42), (16, DM9, 0.46), (24, BBM7, 0.46),
            (32, GM9, 0.48), (40, AM7, 0.44), (48, FMAJ9, 0.48), (56, CADD9, 0.50),
            (64, DM9, 0.58), (72, BBM7, 0.56), (80, GM_D, 0.50), (88, ASUS2, 0.40)]
    for (b, ch, v) in plan:
        sw = 0.25 if b in (64,) else 0.0
        if b == 40:  # A7sus4 -> Am7 inside the slot
            T.strings(b, 4.6, ASUS, vel=v, attack=1.3)
            T.strings(b + 4, 4.6, AM7, vel=v, attack=1.4)
        else:
            T.strings(b, 8.6, ch, vel=v, attack=1.5, swell=sw)
    # high flautando lines (cold air)
    T.strings(0, 15.5, [81], vel=0.20, stem='strings_hi', harmonic=True, attack=3.0, release=3.0, vib=4.0)
    T.strings(64, 7.5, [88], vel=0.16, stem='strings_hi', harmonic=True, attack=2.5, release=3.0, vib=4.0)
    T.strings(72, 7.5, [86], vel=0.15, stem='strings_hi', harmonic=True, attack=2.5, release=3.0, vib=4.0)
    # low plucks (sparse)
    T.pluck([(0, 2, 38), (8, 2, 34), (16, 2, 38), (24, 2, 34), (32, 2, 43), (40, 2, 33),
             (48, 2, 41), (56, 2, 40), (64, 2, 38), (66, 2, 45), (72, 2, 34), (74, 2, 41),
             (80, 2, 38), (88, 2, 33)], vel=0.5, t60=2.6)
    # piano motif
    T.piano(K_A, vel=0.46, beat0=16)
    T.piano(K_B, vel=0.42, beat0=24)
    T.piano(tr(K_A, octave=-1), vel=0.40, beat0=32, felt=0.7)
    T.piano([(0, 2, 76), (2, 2, 69)], vel=0.30, beat0=44)                 # echo over Am7
    T.piano([(0, 2, 81), (2, 3, 76)], vel=0.36, beat0=48)                 # A5 E5 over Fmaj9
    T.piano([(0, 2, 79), (2, 2, 74), (4, 3, 76)], vel=0.36, beat0=56)     # G5 D5 E5 over Cadd9
    T.piano(K_A, vel=0.56, beat0=64)
    T.piano(tr(K_A, octave=-1), vel=0.30, beat0=64, felt=0.75)          # soft octave doubling
    T.piano(K_B, vel=0.50, beat0=72)
    T.piano([(0, 1.5, 74), (1.5, 0.5, 72), (2, 3, 69)], vel=0.40, beat0=80)
    T.piano([(0, 6, 76)], vel=0.30, beat0=88)                             # held E5 over Asus2
    # plucked doubling of a few motif notes (octave below), very soft
    T.pluck([(0, 1, 62), (2, 1, 64), (4, 1, 65)], vel=0.28, beat0=64, t60=1.8, bright=0.3, pan=0.2)
    ir = hall_ir(101, rt_low=3.6, rt_high=1.4)
    mix = {'strings': (0.0, 0.32, STR_EQ), 'strings_hi': (-13.0, 0.5, STR_HI_EQ),
           'piano': (-0.5, 0.30, PIANO_EQ), 'pluck': (-9.0, 0.30, PLUCK_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0)
    return out, (0, out.shape[0])


# ----------------------------------------------------------------------------- mus_berlin
G_PED = [31, 43]                               # G1 G2 pedal
BG_GM = [50, 58]                               # D3 Bb3
BG_EB = [51, 58]                               # Eb3 Bb3   -> Eb/G
BG_CM = [48, 51]                               # C3 Eb3    -> Cm/G
BG_AB = [44, 48, 51]                           # Ab2 C3 Eb3 -> Ab/G (pressure)
BG_DS = [50, 55, 57]                           # D3 G3 A3  -> quartal / Dsus
BG_GS2 = [50, 57]                              # D3 A3     -> G sus2


def mus_berlin() -> tuple[np.ndarray, tuple[int, int]]:
    T = Track('mus_berlin', bpm=70, beats=112, loop=True, seed=23)
    slots = [BG_GM, BG_EB, BG_GM, BG_CM, BG_GM, BG_AB, BG_GM, BG_EB, BG_CM, BG_DS, BG_GM, BG_AB,
             BG_EB, BG_GS2]
    for i, ch in enumerate(slots):
        b = i * 8
        v = 0.42 + (0.12 if i in (10, 11) else 0.0) + (0.05 if i in (5,) else 0.0)
        sw = 0.35 if i in (11,) else 0.0
        T.brass(b, 8.4, ch, vel=v, attack=1.0, release=2.2, bright=0.35, swell=sw)
    # pedal G1/G2 held in overlapping 16-beat breaths (never fully stops: control)
    for b in range(0, 112, 16):
        T.brass(b, 16.6, G_PED, vel=0.40, stem='pedal', attack=1.8, release=2.6, bright=0.2)
    # low strings join in the pressure section
    T.strings(80, 8.5, [43, 50, 55], vel=0.40, attack=2.0)
    T.strings(88, 8.5, [44, 48, 51, 55], vel=0.46, attack=1.6, swell=0.3)
    T.strings(96, 8.5, [43, 51, 58], vel=0.36, attack=1.6)
    # cold high string line (harmonics)
    T.strings(32, 15.0, [79], vel=0.13, stem='strings_hi', harmonic=True, attack=3.0, vib=3.0)
    T.strings(88, 7.5, [80], vel=0.14, stem='strings_hi', harmonic=True, attack=2.5, vib=3.0)
    # muted piano motif
    T.piano(B_1, vel=0.50, beat0=16, felt=1.0, decay=0.55, stem='muted', legato=0.9)
    T.piano(B_2, vel=0.46, beat0=32, felt=1.0, decay=0.55, stem='muted', legato=0.9)
    # celesta motif an octave up, piano 'clock' on D4 underneath
    T.celesta(tr(B_1, octave=1), vel=0.42, beat0=48)
    T.celesta(tr(B_2, octave=1), vel=0.40, beat0=64)
    clock = [(b, 1, 62) for b in range(48, 80)]
    T.piano(clock, vel=0.22, beat0=0, felt=1.0, decay=0.4, stem='muted', legato=0.6)
    # pressure: motif fragments low, in octaves
    T.piano([(0, 1, 55), (1, 1, 58), (2, 1, 57), (3, 1, 55), (4, 3, 62)], vel=0.44, beat0=80,
            felt=1.0, decay=0.6, stem='muted')
    T.piano([(0, 1, 43), (1, 1, 46), (2, 1, 45), (3, 1, 43), (4, 3, 50)], vel=0.30, beat0=80,
            felt=1.0, decay=0.6, stem='muted')
    # coda: sparse celesta
    T.celesta([(0, 2, 79), (4, 2, 86), (10, 2, 81), (15, 4, 79)], vel=0.34, beat0=96)
    ir = hall_ir(202, rt_low=3.0, rt_high=1.3, predelay=0.035)
    mix = {'brass': (-1.0, 0.28, BRASS_EQ), 'pedal': (-6.0, 0.22, BRASS_EQ),
           'strings': (-3.0, 0.32, STR_EQ), 'strings_hi': (-15.0, 0.5, STR_HI_EQ),
           'muted': (-0.5, 0.26, MUTED_EQ), 'celesta': (-3.0, 0.36, CEL_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0, master_lp=10000.0)
    return out, (0, out.shape[0])


# ----------------------------------------------------------------------------- mus_menu
def mus_menu() -> tuple[np.ndarray, tuple[int, int]]:
    # 63 bpm -> 42000 samples per beat; 112 beats = 106.67 s
    T = Track('mus_menu', bpm=63, beats=112, loop=True, seed=37)
    # harmony: D section (K) -> G section (B) -> meeting -> climax -> calm -> return
    plan = [(0, DM9, 0.38), (8, BBM7, 0.42), (16, DM9, 0.44),
            (24, [43, 50, 58, 62], 0.42),             # Gm (B enters)
            (32, [39, 46, 55, 62], 0.42),             # Eb maj7 / pressure-free
            (40, [43, 50, 57, 62], 0.44),             # G sus2 (meeting: Dorian)
            (48, FMAJ9, 0.48), (56, CADD9, 0.50),
            (64, DM9, 0.60), (72, BBM7, 0.58),
            (80, GM9, 0.50), (88, ASUS, 0.44), (96, DM9, 0.40), (104, ASUS2, 0.36)]
    for (b, ch, v) in plan:
        T.strings(b, 8.6, ch, vel=v, attack=1.5, swell=0.25 if b == 64 else 0.0)
    T.strings(0, 15.5, [81], vel=0.18, stem='strings_hi', harmonic=True, attack=3.0, vib=4.0)
    T.strings(64, 15.5, [88], vel=0.14, stem='strings_hi', harmonic=True, attack=3.0, vib=4.0)
    # brass pedal enters with Berlin and stays under the meeting/climax
    T.brass(24, 16.5, [31, 43], vel=0.36, stem='brass', attack=2.0, bright=0.25)
    T.brass(40, 8.5, [43, 50], vel=0.34, stem='brass', attack=1.5, bright=0.25)
    T.brass(64, 16.5, [38, 50], vel=0.40, stem='brass', attack=2.0, bright=0.3)
    # K on felt piano
    T.piano(K_A, vel=0.46, beat0=8)
    T.piano(K_B, vel=0.42, beat0=16)
    # B on celesta (G Aeolian, over Gm / Eb)
    T.celesta(B_1, vel=0.44, beat0=24)
    # meeting (beats 40-63): K answer low on piano, B 'bent' to Dorian (Eb -> E) on celesta
    B_DOR = [(b, d, 76 if m == 75 else m) for (b, d, m) in B_1]
    T.celesta(tr(B_DOR, octave=1)[:8], vel=0.36, beat0=48)
    T.piano(tr(K_A, octave=-1), vel=0.40, beat0=50, felt=0.7)
    T.piano([(0, 2, 79), (2, 2, 74), (4, 3, 76)], vel=0.34, beat0=56)
    # climax: K in octaves, B fragments answer
    T.piano(K_A, vel=0.56, beat0=64)
    T.piano(tr(K_A, octave=-1), vel=0.30, beat0=64, felt=0.75)
    T.celesta([(0, 1, 79), (1, 1, 82), (2, 1, 81), (3, 1, 79)], vel=0.32, beat0=70)
    T.piano(K_B, vel=0.50, beat0=72)
    T.celesta([(0, 2, 86), (2, 1, 88), (3, 1, 86)], vel=0.30, beat0=78)
    # calm
    T.piano([(0, 1.5, 74), (1.5, 0.5, 72), (2, 3, 69)], vel=0.38, beat0=80)
    T.celesta([(0, 1, 79), (1, 1, 82), (2, 1, 81), (3, 3, 79)], vel=0.30, beat0=86)
    T.piano([(0, 1.5, 74), (1.5, 0.5, 69), (2, 4, 76)], vel=0.34, beat0=96)
    T.piano([(0, 6, 76)], vel=0.24, beat0=104)
    T.pluck([(0, 2, 38), (8, 2, 34), (16, 2, 38), (24, 2, 43), (32, 2, 39), (40, 2, 43), (48, 2, 41),
             (56, 2, 40), (64, 2, 38), (66, 2, 45), (72, 2, 34), (80, 2, 43), (88, 2, 33), (96, 2, 38)],
            vel=0.45, t60=2.6)
    ir = hall_ir(303, rt_low=3.6, rt_high=1.5)
    mix = {'strings': (0.0, 0.32, STR_EQ), 'strings_hi': (-13.0, 0.5, STR_HI_EQ),
           'piano': (-0.5, 0.30, PIANO_EQ), 'celesta': (-3.5, 0.36, CEL_EQ),
           'brass': (-5.0, 0.25, BRASS_EQ), 'pluck': (-9.0, 0.30, PLUCK_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0)
    return out, (0, out.shape[0])


# ----------------------------------------------------------------------------- stings
def mus_choice() -> tuple[np.ndarray, None]:
    """5.0 s: weight of a decision.  Open D-A-E chord swells and hangs; piano asks the K head."""
    T = Track('mus_choice', bpm=60, beats=3.2, loop=False, seed=41, tail=1.8)
    T.strings(0, 2.2, [38, 45, 52, 57, 64], vel=0.48, attack=0.8, release=1.4, swell=0.35)
    T.strings(0.15, 2.0, [81], vel=0.16, stem='strings_hi', harmonic=True, attack=0.9, release=1.4)
    T.piano([(0.3, 0.9, 74), (1.2, 2.2, 69)], vel=0.46)
    T.brass(0, 2.0, [38, 45], vel=0.30, attack=0.7, release=1.4, bright=0.2)
    ir = hall_ir(404, rt_low=3.0, rt_high=1.3, length=3.5)
    mix = {'strings': (0.0, 0.32, STR_EQ), 'strings_hi': (-12.0, 0.5, STR_HI_EQ),
           'piano': (0.0, 0.30, PIANO_EQ), 'brass': (-6.0, 0.25, BRASS_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0, end_fade=0.8, rms_from=(0.2, 3.0))
    return out, None


def drum_roll(dur: float, rng: np.random.Generator, rate: float = 13.0) -> np.ndarray:
    """Low soft timpani-like roll (modal membrane hits) -- mono."""
    n = secs(dur)
    out = np.zeros(n)
    t = 0.0
    while t < dur:
        modes = [(58 * (1 + rng.normal(0, 0.01)), 1.0, 1.1), (92, 0.5, 0.7), (124, 0.3, 0.5),
                 (151, 0.18, 0.35), (178, 0.1, 0.25)]
        hit = modal(modes, 1.2, seed=int(rng.integers(1 << 30)), attack=0.003)
        k = secs(0.004)
        nb = rng.standard_normal(k) * np.exp(-np.arange(k) / k * 4)
        hit[:k] += 0.15 * nb
        place(out, hit * rng.uniform(0.6, 1.0), secs(t), circular=False)
        t += (1.0 / rate) * rng.uniform(0.8, 1.2)
    return out


def mus_hall_reveal() -> tuple[np.ndarray, None]:
    """~12.4 s: oppressive low cluster swelling for 10.8 s, cut off; the hall rings on."""
    T = Track('mus_hall_reveal', bpm=60, beats=12.4, loop=False, seed=53, tail=0.0)
    T.n = secs(12.4)
    rng = np.random.default_rng(53)
    D = 11.2
    # brass cluster (C2 Db2 F2 Gb2 G2) entering in sequence
    for (st, m, v) in [(0.0, 36, 0.36), (0.6, 37, 0.33), (2.5, 43, 0.33), (4.0, 42, 0.32), (5.5, 41, 0.32)]:
        sig = brass_note(m, D - st, vel=v, attack=2.5, release=0.3, seed=int(rng.integers(1 << 30)),
                         bright=0.7, swell=1.6, pan=float(rng.uniform(-0.3, 0.3)))
        T.put('brass', st, sig)
    # low string cluster
    for (st, m, v) in [(0.0, 36, 0.36), (1.0, 43, 0.34), (3.0, 49, 0.32), (4.5, 50, 0.32), (6.0, 48, 0.3)]:
        sig = string_note(m, D - st, vel=v, attack=3.0, release=0.3, seed=int(rng.integers(1 << 30)),
                          bright=0.6, swell=1.4, pan=float(rng.uniform(-0.4, 0.4)), vib=6.0)
        T.put('strings', st, sig)
    # high cold semitone rise
    T.put('strings_hi', 2.0, string_note(79, 5.0, vel=0.12, attack=2.5, release=0.6, harmonic=True,
                                         seed=5301, vib=3.0, swell=0.5))
    T.put('strings_hi', 7.0, string_note(80, D - 7.0, vel=0.14, attack=1.5, release=0.3, harmonic=True,
                                         seed=5302, vib=3.0, swell=0.8))
    # sub (C1) + roll
    n = secs(D + 0.3)
    t = np.arange(n) / SR
    sub = (np.sin(2 * np.pi * 32.70 * t) + 0.25 * np.sin(2 * np.pi * 65.41 * t + 0.5))
    sub *= smoothstep(t / 9.0) ** 1.6
    T.put('sub', 0.0, pan2(sub, 0.0))
    roll = drum_roll(D - 3.0, rng)
    roll *= np.linspace(0.05, 1.0, len(roll)) ** 2.2
    T.put('roll', 3.0, pan2(roll, -0.1))
    ir = hall_ir(505, rt_low=3.4, rt_high=1.6, length=4.0, predelay=0.04)
    mix = {'brass': (0.0, 0.30, BRASS_EQ), 'strings': (-2.0, 0.30, STR_EQ),
           'strings_hi': (-14.0, 0.5, STR_HI_EQ), 'sub': (-9.0, 0.05, (('hp', 24, 2), ('lp', 120, 2))),
           'roll': (-8.0, 0.25, (('hp', 35, 2), ('lp', 900, 2)))}
    out = T.mixdown(mix, ir, target_rms=-14.5, cut=10.8, cut_fade=0.035, end_fade=0.35,
                    rms_from=(8.0, 10.8))
    return out, None


def mus_finale_x1() -> tuple[np.ndarray, None]:
    """20 s: K (piano) and B (celesta) meet; ends on an A/Bb rub inside Bbmaj7/D -- unresolved."""
    T = Track('mus_finale_x1', bpm=60, beats=20, loop=False, seed=61, tail=0.0)
    T.strings(0, 8.5, [38, 45, 50, 53, 64], vel=0.42, attack=2.0)             # Dm(add9)
    T.strings(8, 6.5, [38, 43, 58, 69], vel=0.46, attack=1.5)                  # Gm(add9)/D
    T.strings(14, 4.6, [38, 46, 53, 57], vel=0.44, attack=1.6, release=3.0)    # Bbmaj7/D
    T.strings(14.2, 4.4, [88], vel=0.12, stem='strings_hi', harmonic=True, attack=2.0, release=2.5)
    T.brass(6, 11.5, [38, 45], vel=0.34, attack=2.5, release=2.5, bright=0.25, swell=0.4)
    T.piano(K_A, vel=0.46, beat0=0.5)
    T.celesta(B_1[:7], vel=0.42, beat0=8.0)
    # the meeting: K head on piano + B head on celesta together, then the rub
    T.piano([(0, 1.5, 74), (1.5, 3.0, 69)], vel=0.40, beat0=15.8, pedal=True, max_len=5.0)
    T.celesta([(0, 1, 67), (1, 3, 70)], vel=0.38, beat0=15.8)
    ir = hall_ir(606, rt_low=3.8, rt_high=1.5)
    mix = {'strings': (0.0, 0.32, STR_EQ), 'strings_hi': (-12.0, 0.5, STR_HI_EQ),
           'piano': (-0.5, 0.32, PIANO_EQ), 'celesta': (-2.5, 0.36, CEL_EQ),
           'brass': (-6.0, 0.25, BRASS_EQ)}
    out = T.mixdown(mix, ir, target_rms=-20.0, end_fade=2.5)
    return out, None


TRACKS = {
    'mus_karsk': mus_karsk,
    'mus_berlin': mus_berlin,
    'mus_menu': mus_menu,
    'mus_choice': mus_choice,
    'mus_hall_reveal': mus_hall_reveal,
    'mus_finale_x1': mus_finale_x1,
}
