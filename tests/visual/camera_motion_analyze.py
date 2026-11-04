"""Analyse a camera motion run of tests/visual/camera_motion.gd (owner: render-camera).

usage: py -3 -P tests/visual/camera_motion_analyze.py <out_dir> <tag> [--strips] [--screen-scale=1]

Reports per phase (screen pixels of a 1920x1080 canvas, i.e. physical pixels at 1080p):
  * scroll steps: distribution of the per-frame camera displacement, share of "hold" frames (0 px) while the
    camera is moving, max step, stddev of the step  -> stepping like 0/3/0/3 shows up as many zeros + 3s
  * player-vs-world: reversals of the player's drawn world position while it walks one way (feet sliding back)
  * player-vs-screen: direction reversals of the player's on-screen position (visible vibration)
With --strips the real composed frames are compared: the integer shift that best aligns consecutive strips
(minimum mean absolute difference, player columns masked) is the measured on-screen scroll.
"""
import csv
import os
import sys
from collections import Counter, OrderedDict

try:
    import numpy as np
    from PIL import Image
except ImportError:  # strips analysis optional
    np = None


def load(out_dir, tag):
    with open(os.path.join(out_dir, tag + "_frames.csv"), newline="") as f:
        return list(csv.DictReader(f))


def reversals(values, eps=0.25):
    """Number of times the sign of consecutive non-zero differences flips (values in whole screen px; diffs
    below eps are CSV rounding noise)."""
    last = 0
    n = 0
    for a, b in zip(values, values[1:]):
        d = b - a
        if abs(d) < eps:
            continue
        s = 1 if d > 0 else -1
        if last and s != last:
            n += 1
        last = s
    return n


def strip_shift(a, b, mask_cols, max_shift):
    """Best integer x-shift s such that b[x] ~ a[x + s] (content moved left by s when the camera moves right).
    a, b: 2-D float arrays (rows x cols, grey). Columns in mask_cols (player) are ignored."""
    h, w = a.shape
    best, best_s = None, 0
    valid = ~mask_cols
    for s in range(-max_shift, max_shift + 1):
        x0, x1 = max_shift, w - max_shift
        cols = np.arange(x0, x1)
        cols = cols[valid[cols] & valid[np.clip(cols + s, 0, w - 1)]]
        d = np.abs(b[:, cols] - a[:, cols + s]).mean()
        if best is None or d < best:
            best, best_s = d, s
    return best_s, best


def main():
    out_dir, tag = sys.argv[1], sys.argv[2]
    use_strips = "--strips" in sys.argv
    rows = load(out_dir, tag)
    phases = OrderedDict()
    for r in rows:
        phases.setdefault(r["phase"], []).append(r)
    print(f"== {tag}: {len(rows)} frames, dt={float(rows[1]['dt']):.5f} s, k={rows[0]['k']}")
    for ph, rs in phases.items():
        cam = [float(r["drawn_x"]) * 3.0 for r in rs]          # canvas px (=physical px at 1080p)
        steps = [round(b - a, 3) for a, b in zip(cam, cam[1:])]
        moving = [s for s in steps]
        pd = [float(r["pdraw_x"]) * 3.0 for r in rs]
        scr = [p - c for p, c in zip(pd, cam)]
        cont = [float(r["cam_x"]) * 3.0 for r in rs]
        cont_steps = [b - a for a, b in zip(cont, cont[1:])]
        cam_moving = sum(1 for s in cont_steps if abs(s) > 0.05)
        zero_while_moving = sum(1 for s, c in zip(steps, cont_steps) if abs(c) > 0.05 and abs(s) < 1e-6)
        hist = Counter(steps)
        top = ", ".join(f"{k:g}:{v}" for k, v in sorted(hist.items(), key=lambda kv: -kv[1])[:6])
        err = [abs(c - d) for c, d in zip(cont, cam)]
        sd = (np.std([s for s, c in zip(steps, cont_steps) if abs(c) > 0.05]) if np is not None and cam_moving > 1 else 0.0)
        print(f"  [{ph:8s}] frames {len(rs):4d} | cam moving {cam_moving:4d} | step hist {top} | holds-while-moving "
              f"{zero_while_moving:3d} | step sd {sd:.3f} | max|drawn-cont| {max(err):.3f} px")
        psteps = Counter(round(b - a) for a, b in zip(pd, pd[1:]))
        ptop = ", ".join(f"{k:g}:{v}" for k, v in sorted(psteps.items(), key=lambda kv: -kv[1])[:5])
        print(f"             player world reversals {reversals(pd)} | player screen reversals {reversals(scr)} | "
              f"screen pos range {min(scr):.1f}..{max(scr):.1f} | player world step hist {ptop}")
    if use_strips and np is not None:
        print("  strips (measured on-screen scroll, px per frame):")
        prev = None
        meas = []
        for r in rows:
            f = int(r["frame"])
            path = os.path.join(out_dir, f"{tag}_strip_{f:04d}.png")
            if not os.path.exists(path):
                prev = None
                continue
            img = np.asarray(Image.open(path).convert("L"), dtype=np.float32)[::3, :]
            if prev is not None:
                pr, pimg = prev
                cam_c = (float(pr["drawn_x"]) * 3.0)
                px = float(r["pdraw_x"]) * 3.0 - float(r["drawn_x"]) * 3.0
                scale = img.shape[1] / 1920.0
                mask = np.zeros(img.shape[1], bool)
                lo, hi = int((px - 60) * scale), int((px + 60) * scale)
                mask[max(0, lo):max(0, hi)] = True
                s, d = strip_shift(pimg, img, mask, int(12 * scale))
                exp = (float(r["drawn_x"]) - float(pr["drawn_x"])) * 3.0 * scale
                meas.append((r["phase"], s, exp, d))
            prev = (r, img)
        by = OrderedDict()
        for ph, s, e, d in meas:
            by.setdefault(ph, []).append((s, e, d))
        for ph, v in by.items():
            hs = Counter(s for s, _, _ in v)
            mism = sum(1 for s, e, _ in v if abs(s - e) > 0.51)
            top = ", ".join(f"{k}:{c}" for k, c in sorted(hs.items(), key=lambda kv: -kv[1])[:6])
            print(f"  [{ph:8s}] measured shift hist {top} | frames where image != camera data: {mism}/{len(v)}")


if __name__ == "__main__":
    main()
