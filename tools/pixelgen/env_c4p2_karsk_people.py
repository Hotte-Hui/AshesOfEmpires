"""env_c4p2_karsk_people -- the people of L_C4P2_Karsk as life strips (looping decals, baked in the scene's light).

A small 2D rig in tone space: joints (hip, neck, head, shoulders, elbows, hands, knees, feet) per key pose, eased
between keys; garments as strokes and polygons with their own ramps (quilted cotton with its stitching, plum or brown
Western wool, railway navy, sheepskin, felt boots, rags round the hands), hand-made head patterns per headgear
(ushanka, headscarf, shawl, knit cap, felt hat, beret, flat cap, railway cap, militia cap, bare heads young / old),
a rim-light / dark-outline pass from the main light, then the figure is baked with the scene's light fields at its
world position (env_c4p2_karsk_kit.light_fields) -- so the floodlight, the fire barrel and the windows light the
people as they light the walls.  Heights 42-46 px (adults; the cast sheets are 44-46), children 26-32.

Scene A -- Kolonne 4 (the returnees of wagon 24 318; Western and Soviet clothes mixed, people of every age, no
insignia), the cook in the hatch, a fitter in the stall door.  Scene B -- the railway workers' brass band, children,
the cleaner on the engine's buffer beam, the canteen's waitress and cook, the shovels behind the tarpaulin, the
militia patrol, families at the express, a vendor, a porter, the conductor, passengers in the windows.
Deterministic (fixed seeds), no randomness at run time.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K

# =========================================================================== heads (profile, facing RIGHT)
# r hair  q hair light  S skin  s skin shadow  L nose/skin light  E eye  M mouth  b beard shadow
# H hat  h hat shadow  G hat light  F fur light  f fur dark  B band / brim  X badge   K scarf  k scarf shadow
HEADS = {
    'bare_m': ['..rrrrr..',
               '.rqqrrrr.',
               'rqrrrrSS.',
               'rrrrSSSE.',
               'rrrsSSSSL',
               '.rrsSSSS.',
               '.rsSSSM..',
               '..sSSS...',
               '...ss....'],
    'bare_old': ['..qqqq...',
                 '.qSSSSS..',
                 'qqSSSSSS.',
                 'qqqsSSSE.',
                 'qqqsSSSSL',
                 '.qqsSSSS.',
                 '.qsbbbM..',
                 '..sbbb...',
                 '...ss....'],
    'bun': ['...rrrrr..',
            '..rqqrrrr.',
            '.rrrrrrSS.',
            'rrrrrSSSE.',
            'rqrrsSSSSL',
            '.rrrsSSSS.',
            '...rsSSM..',
            '....sSS...',
            '.....ss...'],
    'ushanka': ['...HHHH...',
                '..fFFFFFf.',
                '.fFFFFFFFF',
                '.fFFfFFFFf',
                'fFFfSSSSE.',
                'fFFfSSSSSL',
                'fFFfSSSS..',
                '.fFsSSM...',
                '..fsSS....',
                '...ss.....'],
    'ushanka_up': ['..fFFFFf..',
                   '.fFFFFFFf.',
                   'fFHHHHHHHf',
                   'fFFFFFFFFf',
                   '.rrrsSSSE.',
                   '.rrrsSSSSL',
                   '.rrsSSSS..',
                   '..rsSSM...',
                   '...sSS....',
                   '...ss.....'],
    'scarf': ['...KKKKK..',
              '..KKKKKKk.',
              '.KKKKKKKSs',
              'KKKKKKSSSE',
              'KKKKKsSSSSL',
              'kKKKKsSSSS.',
              '.kKKKsSSM..',
              '..kKKKSS...',
              '...KKKk....',
              '....kk.....'],
    'shawl': ['...KKKKK...',
              '..KKKKKKKk.',
              '.KKKKKKKKSs',
              'KKKKKKKsSSE',
              'KKKKKKsSSSSL',
              'KKKKKKsSSSS.',
              'kKKKKKKsSM..',
              'kkKKKKKKS...',
              '.kkKKKKKk...',
              '..kkKKKkk...'],
    'knit': ['...HHH...',
             '..HHHHH..',
             '.HhHhHhH.',
             'BBBBBBBB.',
             'rrrrSSSE.',
             'rrrsSSSSL',
             '.rrsSSSS.',
             '.rsSSSM..',
             '..sSSS...',
             '...ss....'],
    'flatcap': ['..HHHHH...',
                '.HGGHHHH..',
                '.HHHHHHHBB',
                'rrrrSSSE..',
                'rrrsSSSSL.',
                '.rrsSSSS..',
                '.rsSSSM...',
                '..sSSS....',
                '...ss.....'],
    'felthat': ['...HHHH...',
                '..HGHHHH..',
                '..hhhhhh..',
                'BBBBBBBBBB',
                '.rrrSSSE..',
                '.rrsSSSSL.',
                '..rsSSSS..',
                '..rsSSM...',
                '...sSS....',
                '...ss.....'],
    'beret': ['..HHHHHH.',
              '.HGGHHHHH',
              '.hhhhhhh.',
              'rrrrSSSE.',
              'rrrsSSSSL',
              '.rrsSSSS.',
              '.rsSSSM..',
              '..sSSS...',
              '...ss....'],
    'railcap': ['..HHHHHH..',
                '.HGGHHHHH.',
                '.HHHHHHHH.',
                '.BBBBBBBBB',
                '.rrSSSSE..',
                '.rrsSSSSL.',
                '..rsSSSS..',
                '..rsSSM...',
                '...sSS....',
                '...ss.....'],
    'militia': ['..HHHHHH..',
                '.HGGHHHHH.',
                '.HHHHHXHH.',
                '.BBBBBBBBh',
                '.rrSSSSE..',
                '.rrsSSSSL.',
                '..rsSSSS..',
                '..rsSSM...',
                '...sSS....',
                '...ss.....'],
    'hood': ['..HHHHH..',
             '.HHHHHHH.',
             'HHHHhSSS.',
             'HHHhSSSE.',
             'HHHhSSSSL',
             'HHHhSSSS.',
             '.HHhSSM..',
             '..hhSS...',
             '...ss....'],
    'back_m': ['..rrrrr..',
               '.rrrrrrr.',
               'rqrrrrrrr',
               'rqrrrrrrr',
               'rrrrrrrrr',
               '.rrrrrrr.',
               '..sSSSs..',
               '..sSSSs..',
               '...sSs...'],
    # ---- round-10 review: faces that are not twins (m = moustache in the hair colour)
    'bare_moust': ['...rrr...',
                   '.qrrrrr..',
                   'qqrrrrSS.',
                   'qrrrSSSE.',
                   'qrrsSSSSL',
                   '.qrsSSSS.',
                   '.qsSmmmm.',
                   '..sSSSS..',
                   '..sbbS...',
                   '...ss....'],
    'railcap_moust': ['..HHHHHH..',
                      '.HGGHHHHH.',
                      '.HHHHHHHH.',
                      '.BBBBBBBBB',
                      '.rrSSSSE..',
                      '.rrsSSSSL.',
                      '..rsSmmmm.',
                      '..rsSSSS..',
                      '...sSS....',
                      '...ss.....'],
    'railcap_young': ['...HHHHH..',
                      '..HGGHHHH.',
                      '.HHHHHHHHB',
                      '.qqBBBBBBB',
                      'rrqqSSSE..',
                      'rrrsSSSSL.',
                      '.rrsSSSS..',
                      '..rsSSM...',
                      '...sSS....',
                      '...ss.....'],
    'furhat_f': ['..fFFFFf..',
                 '.fFFFFFFf.',
                 '.fFGFFFFFf',
                 '.rrrSSSSE.',
                 'rrrrsSSSSL',
                 'rrrrsSSSS.',
                 '.rrrsSSM..',
                 '..rrrsSS..',
                 '...r..ss..'],
    'militia_winter': ['...ffff...',
                       '..fFFFFf..',
                       '.fFFFFXFf.',
                       '.fFFFFFFFf',
                       '.fffSSSSE.',
                       '.ffsSSSSSL',
                       '.ffsSSSS..',
                       '..fsSSM...',
                       '...sSS....',
                       '...ss.....'],
    'militia_winter_m': ['...ffff...',
                         '..fFFFFf..',
                         '.fFFFFXFf.',
                         '.fFFFFFFFf',
                         '.fffSSSSE.',
                         '.ffsSSSSSL',
                         '.ffsSmmmm.',
                         '..fsSSSS..',
                         '...sSS....',
                         '...ss.....'],
    'porter_cap': ['..HHHHH...',
                   '.HGGHHHH..',
                   '.HHHHXHHBB',
                   'rrrrSSSE..',
                   'rrrsSSSSL.',
                   '.rrsSSSS..',
                   '.rsSmmm...',
                   '..sSSS....',
                   '...ss.....'],
}


def head_map(spec):
    hr, ht = spec.get('hair', ('N', 2.2))
    hat = spec.get('hat', ('Q', 2.0))
    sk = spec.get('skin', 2.0)
    sc = spec.get('scarf_head', ('G', 2.4))
    fur = spec.get('fur', ('D', 3.0))
    band = spec.get('band', ('N', 1.4))
    return {'r': (hr, ht), 'q': (hr, ht + 1.2), 'S': ('Y', sk), 's': ('Y', sk - 0.9), 'L': ('Y', sk + 1.0),
            'E': ('N', 0.6), 'M': ('Y', sk - 1.1), 'b': ('Y', sk - 0.7), 'm': (hr, ht + 0.5),
            'H': (hat[0], hat[1]), 'h': (hat[0], hat[1] - 0.8), 'G': (hat[0], hat[1] + 1.0),
            'F': (fur[0], fur[1]), 'f': (fur[0], fur[1] - 1.0), 'B': (band[0], band[1]), 'X': ('L', 4.2),
            'K': (sc[0], sc[1]), 'k': (sc[0], sc[1] - 0.9)}


def blit_pat(lay, x, y, pat, cmap, flip=False, hgt=0.75):
    w = max(len(r) for r in pat)
    for yy, row in enumerate(pat):
        row = row.ljust(w, '.')
        if flip:
            row = row[::-1]
        for xx, ch in enumerate(row):
            if ch in cmap:
                rmp, t = cmap[ch]
                lay.px(x + xx, y + yy, rmp, t, hgt=hgt)
    return w


# =========================================================================== rig
JOINTS = ('hip', 'neck', 'head', 'sh_n', 'el_n', 'ha_n', 'sh_f', 'el_f', 'ha_f', 'kn_n', 'ft_n', 'kn_f', 'ft_f')


def lerp_pose(a: dict, b: dict, u: float) -> dict:
    u = u * u * (3 - 2 * u)                                    # ease in/out
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, b.get(k)), b.get(k, a.get(k))
        if isinstance(va, tuple) and isinstance(vb, tuple) and len(va) == len(vb) and all(
                isinstance(v, (int, float)) for v in va + vb):
            out[k] = tuple(x + (y - x) * u for x, y in zip(va, vb))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out[k] = va + (vb - va) * u
        else:
            out[k] = va if u < 0.5 else vb
    return out


def standing(H=44, lean=0.0, stance=3.0, arms='hang', knee=0.0):
    """A neutral standing pose (relative to the feet centre, y up = negative), facing right."""
    hip_y = -H * 0.48
    neck = (lean * 6, -H + 9.5)
    p = {
        'hip': (0.0, hip_y + knee * 0.6), 'neck': neck, 'head': (neck[0] + 0.5, -H + 4.5),
        'kn_n': (1.0 + knee, -H * 0.24), 'ft_n': (stance * 0.5, 0.0),
        'kn_f': (-0.5 + knee * 0.6, -H * 0.24), 'ft_f': (-stance * 0.5, 0.0),
        'sh_n': (neck[0] + 0.5, neck[1] + 1.5), 'sh_f': (neck[0] - 1.0, neck[1] + 1.5),
    }
    sx, sy = p['sh_n']
    if arms == 'hang':
        p.update({'el_n': (sx + 1.0, sy + 7.5), 'ha_n': (sx + 1.5, sy + 14.0),
                  'el_f': (sx - 2.0, sy + 7.5), 'ha_f': (sx - 2.0, sy + 13.5)})
    elif arms == 'pockets':
        p.update({'el_n': (sx - 1.0, sy + 7.0), 'ha_n': (sx + 1.0, sy + 11.5),
                  'el_f': (sx - 3.0, sy + 7.0), 'ha_f': (sx - 1.5, sy + 11.0)})
    elif arms == 'front':
        p.update({'el_n': (sx + 3.0, sy + 6.0), 'ha_n': (sx + 7.0, sy + 6.0),
                  'el_f': (sx + 1.0, sy + 6.5), 'ha_f': (sx + 5.5, sy + 6.0)})
    return p


class Rig:
    def __init__(self, spec: dict):
        self.s = dict(spec)

    # ---------------------------------------------------------------- primitives
    @staticmethod
    def stroke(lay, pts, r, ramp, t, hgt=0.6):
        m = K.stroke_mask(lay.w, lay.h, [pts], r)
        lay.put(m, 0, 0, ramp, t, hgt=hgt, flat=True)
        return m

    def draw(self, lay, ox, oy, pose: dict, face=1, extra=None):
        """Draw the figure with its feet centre at (ox, oy) of the frame layer."""
        s = self.s
        P = {k: (ox + face * v[0], oy + v[1]) for k, v in pose.items() if k in JOINTS}
        coat_r, coat_t = s.get('coat', ('Q', 2.4))
        tr_r, tr_t = s.get('trousers', ('N', 2.2))
        boots = s.get('boots', 'felt')
        clen = s.get('coat_len', 'short')
        width = s.get('width', 1.0)
        H = s.get('H', 44)
        far = -0.9
        # far leg + boot
        self._leg(lay, P['hip'], P['kn_f'], P['ft_f'], tr_r, tr_t + far, boots, face, far=True)
        # far arm
        sl_r, sl_t = s.get('sleeve', (coat_r, coat_t - 0.3))
        self._arm(lay, P['sh_f'], P['el_f'], P['ha_f'], sl_r, sl_t + far, face, far=True)
        if extra and 'behind' in extra:
            extra['behind'](lay, P, face)
        # torso + coat
        self._torso(lay, P, face, coat_r, coat_t, clen, width, H)
        # near leg (below the coat)
        self._leg(lay, P['hip'], P['kn_n'], P['ft_n'], tr_r, tr_t, boots, face, far=False)
        if clen in ('mid', 'long'):
            self._skirt(lay, P, face, coat_r, coat_t, clen, width, H)
        # head
        self._head(lay, P, face, pose.get('look', 0))
        if extra and 'mid' in extra:
            extra['mid'](lay, P, face)
        # near arm
        self._arm(lay, P['sh_n'], P['el_n'], P['ha_n'], sl_r, sl_t, face, far=False)
        if extra and 'front' in extra:
            extra['front'](lay, P, face)
        return P

    def _leg(self, lay, hip, kn, ft, r, t, boots, face, far):
        hx, hy = hip
        hip_pt = (hx + (-0.8 if far else 0.8) * face * 0.5, hy)
        self.stroke(lay, [hip_pt, kn, ft], 1.25 if self.s.get('legs', 'normal') == 'normal' else 1.0, r, t)
        fx, fy = ft
        fx, fy = int(round(fx)), int(round(fy))
        if boots == 'felt':                                     # valenki: thick, grey-black, to below the knee
            bt = ('C', 1.4 if far else 2.0)
            kx, ky = kn
            self.stroke(lay, [(kx + 0.0, ky + 3.0), ft], 1.7, bt[0], bt[1], hgt=0.7)
            lay.rect(fx - 2 + (1 if face > 0 else 0), fy - 2, 5, 2, bt[0], bt[1] - 0.3, hgt=0.6)
            lay.px(fx + 2 * face, fy - 1, bt[0], bt[1] + 0.6)
        elif boots == 'shoes':                                  # worn Western shoes
            sh = ('K', 1.6 if far else 2.4)
            lay.rect(fx - 1 - (1 if face < 0 else 0), fy - 2, 4, 2, sh[0], sh[1], hgt=0.6)
            lay.px(fx + 2 * face, fy - 1, sh[0], sh[1] + 0.4)
            lay.px(fx - 1 * face, fy - 2, 'N', 1.4)
        elif boots == 'boots':                                  # leather boots (militia, railwaymen)
            bt = ('N', 1.2 if far else 2.0)
            kx, ky = kn
            self.stroke(lay, [(kx, ky + 2.5), ft], 1.4, bt[0], bt[1], hgt=0.7)
            lay.rect(fx - 1 - (1 if face < 0 else 0), fy - 2, 4, 2, bt[0], bt[1], hgt=0.6)
            lay.px(fx + 2 * face, fy - 1, 'I', 3.0)
        else:                                                   # child's boots
            lay.rect(fx - 1, fy - 2, 3, 2, 'K', 1.8 if far else 2.4)

    def _arm(self, lay, sh, el, ha, r, t, face, far):
        rad = self.s.get('arm_r', 1.55)
        if not far:
            # a dark seam under the sleeve separates the arm from the coat behind it
            m0 = K.stroke_mask(lay.w, lay.h, [[(sh[0], sh[1] + 0.8), (el[0], el[1] + 0.8), (ha[0], ha[1] + 0.6)]],
                               rad + 0.5)
            lay.put(m0 & (lay.rid >= 0), 0, 0, r, t - 1.1, hgt=0.5)
        self.stroke(lay, [sh, el, ha], rad, r, t + (0.35 if not far else 0.0), hgt=0.85 if not far else 0.6)
        if not far:
            ex, ey = int(round(el[0])), int(round(el[1]))
            lay.px(ex, ey, r, t - 0.6)
            sx_, sy_ = int(round(sh[0])), int(round(sh[1]))
            lay.px(sx_, sy_ - 1, r, t + 1.0)
            cuff = self.s.get('cuff')
            if cuff:
                cx_ = int(round(ha[0] - (ha[0] - el[0]) * 0.18))
                cy_ = int(round(ha[1] - (ha[1] - el[1]) * 0.18))
                lay.rect(cx_ - 1, cy_ - 1, 2, 2, cuff[0], cuff[1])
        hx, hy = int(round(ha[0])), int(round(ha[1]))
        hands = self.s.get('hands', 'bare')
        if hands == 'rags':
            lay.rect(hx - 1, hy - 1, 3, 3, 'P', 2.0 if far else 2.8, hgt=0.8)
            lay.px(hx, hy - 1, 'P', 3.8 if not far else 2.6)
            lay.px(hx - 1, hy + 1, 'P', 1.6)
        elif hands == 'mittens':
            mt = self.s.get('mitten', ('Q', 2.6))
            lay.rect(hx - 1, hy - 1, 3, 3, mt[0], mt[1] - (0.8 if far else 0), hgt=0.8)
            lay.px(hx + (1 if face > 0 else -1), hy - 2, mt[0], mt[1] - (0.8 if far else 0))
        elif hands == 'gloves':
            lay.rect(hx - 1, hy - 1, 3, 3, 'N', 1.8 if far else 2.4, hgt=0.8)
        else:
            sk = self.s.get('skin', 2.0)
            lay.rect(hx - 1, hy - 1, 3, 2, 'Y', sk - (0.8 if far else 0.0), hgt=0.9)
            lay.px(hx - 1 + (2 if face > 0 else 0), hy + 1, 'Y', sk - 0.6)

    def _torso(self, lay, P, face, r, t, clen, width, H):
        nx, ny = P['neck']
        hx, hy = P['hip']
        bw = 4.3 * width                                         # back half-width
        fw = 3.6 * width                                         # front half-width
        chest = self.s.get('chest', 1.0)
        hem = hy + {'short': 2.0, 'mid': 2.0, 'long': 2.0}[clen]
        pts = [(nx - face * (bw - 0.5), ny - 0.5), (nx + face * (fw - 0.5), ny - 0.5),
               (nx + face * (fw + chest), ny + 5), (hx + face * (fw + 0.4), hem), (hx - face * (bw + 0.6), hem),
               (nx - face * (bw + 0.6), ny + 4)]
        m, mx, my = lay.poly(pts, r, t, hgt=0.7)
        # form shading: back edge darker, chest light, a fold at the waist
        hh = m.shape[0]
        yy = np.linspace(0, 1, hh, dtype=np.float32)[:, None]
        xx = (np.arange(m.shape[1], dtype=np.float32)[None, :] + mx - nx) * face
        dt = 0.6 * np.clip(xx / 4.0, -1, 1) - 0.5 * yy + 0.35 * (1 - yy) * (np.abs(xx) < 2.5)
        sub = lay.tone[my:my + hh, mx:mx + m.shape[1]]
        mm = m[:sub.shape[0], :sub.shape[1]]
        sub[mm] += dt[:sub.shape[0], :sub.shape[1]][mm]
        if self.s.get('quilted'):                                # telogreika: stitched rows
            for yq in range(int(ny) + 3, int(hem), 3):
                row = m[min(hh - 1, max(0, yq - my))]
                xs = np.nonzero(row)[0]
                if xs.size:
                    lay.rect(mx + xs.min() + 1, yq, max(1, xs.size - 2), 1, r, t - 0.7)
        if self.s.get('opening', True):                         # the coat's front edge
            lay.line(int(round(nx + face * (fw - 1.0))), int(round(ny + 2)), int(round(hx + face * (fw - 0.6))),
                     int(round(hem)) - 1, r, t - 0.8)
        belt = self.s.get('belt')
        if belt:
            yb = int(round(hy - 2))
            row = m[min(hh - 1, max(0, yb - my))]
            xs = np.nonzero(row)[0]
            if xs.size:
                lay.rect(mx + xs.min(), yb, xs.size, 1, belt[0], belt[1])
        col = self.s.get('collar')
        if col:
            lay.rect(int(round(nx - face * 2.5)) - (2 if face < 0 else 0), int(round(ny)) - 1, 5, 2, col[0], col[1],
                     hgt=0.8)
        nsc = self.s.get('neck_scarf')
        if nsc:
            lay.rect(int(round(nx - 2)), int(round(ny)) - 1, 5, 2, nsc[0], nsc[1], hgt=0.8)
            if self.s.get('scarf_tail'):
                tx = int(round(nx - face * 3))
                lay.rect(tx, int(round(ny)), 1, 5, nsc[0], nsc[1] - 0.5)
        ap = self.s.get('apron')
        if ap:
            lay.poly([(nx + face * 1.0, ny + 4), (nx + face * (fw + chest), ny + 5), (hx + face * (fw + 1.5), hy + 12),
                      (hx + face * 0.0, hy + 12)], ap[0], ap[1], hgt=0.75)
        for b in self.s.get('buttons', []):
            lay.px(int(round(nx + face * (fw - 0.5))), int(round(ny + b)), 'L', 3.6)
        tie = self.s.get('tie')                                  # shirt collar + tie in the coat's V
        if tie:
            tx_ = int(round(nx + face * (fw - 1.5)))
            lay.rect(tx_ - (1 if face > 0 else 0), int(round(ny)), 2, 1, 'P', 5.6)
            lay.rect(tx_, int(round(ny)) + 1, 1, 4, tie[0], tie[1])
        badge = self.s.get('badge')                              # a brass number badge on the chest
        if badge:
            lay.rect(int(round(nx + face * 1.0)) - 1, int(round(ny + 5)), 2, 2, badge[0], badge[1], hgt=0.9)
        holster = self.s.get('holster')                          # brown leather holster on the belt, behind
        if holster:
            lay.rect(int(round(hx - face * 3.5)) - 1, int(round(hy - 3)), 3, 4, holster[0], holster[1], hgt=0.8)
        patch = self.s.get('patch')
        if patch:
            lay.rect(int(round(hx - face * 2)) - 1, int(round(hy - 6)), 3, 3, patch[0], patch[1])

    def _skirt(self, lay, P, face, r, t, clen, width, H):
        hx, hy = P['hip']
        fx = (P['kn_n'][0] + P['kn_f'][0]) / 2
        bot = hy + (H * 0.27 if clen == 'mid' else H * 0.40)
        flare = 1.6 if clen == 'mid' else 2.8
        pts = [(hx - face * (3.8 * width), hy + 1), (hx + face * (3.8 * width), hy + 1),
               (fx + face * (4.4 * width + flare), bot), (fx - face * (4.4 * width + flare), bot)]
        m, mx, my = lay.poly(pts, r, t - 0.2, hgt=0.65)
        hh = m.shape[0]
        for k in range(2):                                       # folds
            xk = int(round(fx + face * (k * 3 - 1)))
            lay.line(xk, int(hy + 4), xk + face, int(bot - 1), r, t - 0.9)
        lay.rect(int(round(min(pts[2][0], pts[3][0]))), int(round(bot)), int(abs(pts[2][0] - pts[3][0])), 1, r,
                 t - 0.8)
        if self.s.get('hem_patch'):
            lay.rect(int(round(fx - 2)), int(round(bot - 3)), 3, 2, 'P', 2.0)

    def _head(self, lay, P, face, look):
        kind = self.s.get('head', 'bare_m')
        pat = HEADS[kind]
        cm = head_map(self.s)
        nx, ny = P['head']
        w = max(len(rw) for rw in pat)
        hh = len(pat)
        x0 = int(round(nx - (w / 2.0) + (0.5 if face > 0 else -0.5)))
        y0 = int(round(ny - hh / 2.0)) + int(look)
        blit_pat(lay, x0, y0, pat, cm, flip=face < 0)

    # ---------------------------------------------------------------- the whole figure on one frame
    def frame(self, fw, fh, ox, oy, pose, face=1, extra=None):
        lay = K.tlayer(fw, fh, 'fig')
        self.draw(lay, ox, oy, pose, face, extra)
        return lay


def outline_pass(lay, light_dir=(-0.6, -0.8), rim=0.9, dark=0.9):
    """Edge pixels: lit side lighter (rim), the other side darker (an outline in the garment's own ramp)."""
    m = lay.rid >= 0
    if not m.any():
        return
    up = np.roll(m, 1, 0); dn = np.roll(m, -1, 0); lf = np.roll(m, 1, 1); rt = np.roll(m, -1, 1)
    up[0, :] = False; dn[-1, :] = False; lf[:, 0] = False; rt[:, -1] = False
    lx, ly = light_dir
    # outward normal of the edge (sum of the empty directions)
    nxm = (~rt).astype(np.float32) - (~lf).astype(np.float32)
    nym = (~dn).astype(np.float32) - (~up).astype(np.float32)
    edge = m & ((~up) | (~dn) | (~lf) | (~rt))
    d = nxm * lx + nym * ly
    lit = edge & (d > 0.3)
    shade = edge & (d <= 0.3)
    lay.tone[lit] += rim
    lay.tone[shade] -= dark


def rounded(lay, amount=0.9):
    m = lay.rid >= 0
    if m.any():
        h = K.box_blur(m.astype(np.float32), 1)
        lay.hgt[m] = lay.hgt[m] * 0.35 + h[m] * amount


# =========================================================================== strips
class Strip:
    """Frames of one life strip, baked in the scene's light at world `origin` (top-left of a frame)."""

    def __init__(self, name, fw, fh, origin, lights, exposure, light_dir=(-0.6, -0.8)):
        self.name, self.fw, self.fh = name, fw, fh
        self.origin = origin
        self.lights = lights
        self.exposure = exposure
        self.light_dir = light_dir
        self.frames = []

    def add(self, lay):
        outline_pass(lay, self.light_dir)
        rounded(lay)
        F = K.light_fields(lay, self.lights, origin=self.origin)
        K.resolve(lay, F, exposure=self.exposure, band=1.6)
        self.frames.append((lay.c.copy(), lay.normal_map(3.0), lay.em.copy()))

    def arrays(self):
        c = np.concatenate([f[0] for f in self.frames], axis=1)
        n = np.concatenate([f[1] for f in self.frames], axis=1)
        e = np.concatenate([f[2] for f in self.frames], axis=1)
        return c, n, e


def cycle(keys, counts):
    """Key poses + frames per transition -> list of poses (eased)."""
    out = []
    for i, n in enumerate(counts):
        a, b = keys[i], keys[(i + 1) % len(keys)]
        for k in range(n):
            out.append(lerp_pose(a, b, k / float(n)))
    return out


# =========================================================================== tools / props drawn with a figure
def shovel(lay, P, face, load=False, seed=0, ext=11.0):
    """Shovel held in both hands: a straight ash handle from the far hand (D-grip) through the near hand, the
    steel blade `ext` px beyond the near hand -- so the handle never bends whatever the pose."""
    a = np.array(P['ha_f'], float)
    b = np.array(P['ha_n'], float)
    d = b - a
    n = np.linalg.norm(d) + 1e-6
    d /= n
    tip = b + d * ext
    grip = a - d * 2.5
    Rig.stroke(lay, [tuple(grip), tuple(tip)], 0.55, 'D', 3.8, hgt=0.6)
    gx, gy = int(round(grip[0])), int(round(grip[1]))
    lay.rect(gx - 1, gy - 1, 2, 2, 'D', 2.6)
    ux, uy = d
    px_, py_ = -uy, ux
    tx, ty = tip
    L_, Wb = 6.0, 2.2
    pts = [(tx - px_ * Wb, ty - py_ * Wb), (tx + px_ * (Wb - 0.6), ty + py_ * (Wb - 0.6)),
           (tx + px_ * (Wb - 0.8) + ux * L_, ty + py_ * (Wb - 0.8) + uy * L_),
           (tx - px_ * (Wb + 0.2) + ux * L_, ty - py_ * (Wb + 0.2) + uy * L_)]
    lay.poly(pts, 'I', 3.0, hgt=0.8)
    e0, e1 = pts[0], pts[3]
    lay.line(int(round(e0[0])), int(round(e0[1])), int(round(e1[0])), int(round(e1[1])), 'I', 5.2)
    lay.px(int(round(tx)), int(round(ty)), 'I', 2.0)
    if load:
        rng = np.random.default_rng(seed)
        cx, cy = tx + ux * 3.0 - px_ * 1.5, ty + uy * 3.0 - py_ * 1.5
        for k in range(9):
            lay.px(int(round(cx + rng.integers(-2, 3) * 0.8 + ux * rng.integers(-1, 2))),
                   int(round(cy - abs(rng.integers(0, 2)))), 'X', 1.8 + rng.random() * 3.0, hgt=0.9)


def coal_spray(lay, x, y, k, seed, n=9, spread=10.0):
    """Coal lumps flying from a thrown shovel (k = 0..1 along the arc)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        vx = rng.uniform(0.5, 1.0) * spread
        vy = -rng.uniform(4.0, 8.0)
        t = k + rng.uniform(-0.12, 0.12)
        if t < 0:
            continue
        px_ = x + vx * t * 1.6
        py_ = y + vy * t * 1.6 + 14 * t * t
        lay.px(int(round(px_)), int(round(py_)), 'X', 1.6 + rng.random() * 3.0, hgt=0.9)


def basket(lay, x, y, w=8, h=7, load=True, seed=0, ramp='D', tone=3.2):
    lay.rect(x, y, w, h, ramp, tone, hgt=0.7)
    for k in range(0, w, 2):
        lay.rect(x + k, y, 1, h, ramp, tone - 0.9)
    for k in range(1, h, 2):
        lay.rect(x, y + k, w, 1, ramp, tone - 0.5)
    lay.rect(x, y, w, 1, ramp, tone + 0.8)
    if load:
        K.coal_heap(lay, x + w // 2, y + 1, w, 3, seed=seed)


# =========================================================================== the people of scene A (Kolonne 4 ...)
# spec presets (garments: Western coats of Veltrava + issued Soviet quilted vests, felt boots a size too big)
def spec(**kw):
    base = {'coat': ('Q', 2.4), 'trousers': ('N', 2.4), 'boots': 'felt', 'coat_len': 'short', 'head': 'ushanka',
            'hair': ('N', 2.2), 'hat': ('N', 2.6), 'fur': ('D', 3.8), 'skin': 2.0, 'H': 44, 'hands': 'bare'}
    base.update(kw)
    return base


def _pose(H, hip, neck, head, sh_n, el_n, ha_n, sh_f, el_f, ha_f, kn_n, ft_n, kn_f, ft_f):
    k = H / 44.0

    def sc(p):
        return (p[0] * k, p[1] * k)
    return {'hip': sc(hip), 'neck': sc(neck), 'head': sc(head), 'sh_n': sc(sh_n), 'el_n': sc(el_n), 'ha_n': sc(ha_n),
            'sh_f': sc(sh_f), 'el_f': sc(el_f), 'ha_f': sc(ha_f), 'kn_n': sc(kn_n), 'ft_n': sc(ft_n),
            'kn_f': sc(kn_f), 'ft_f': sc(ft_f)}


def shoveller_poses(H=44, reach=1.0):
    """Key poses of one shovelful (facing right): bent over the heap, thrust, lift the load, swing, throw."""
    ready = _pose(H, (-3, -20), (6, -32), (9, -36.5), (6, -30.5), (9, -23), (12, -15), (5, -31), (2, -25), (1, -22),
                  (3, -10), (6, 0), (-4, -11), (-7, 0))
    thrust = _pose(H, (-1, -19), (9, -30), (12.5, -34), (9, -28.5), (12, -21), (16, -13), (8, -29), (5, -24),
                   (5, -20), (5, -9.5), (6, 0), (-3, -10.5), (-7, 0))
    lift = _pose(H, (-3, -21), (4, -35), (6.5, -39.5), (4, -33.5), (8, -27), (12, -23), (3, -34), (0, -28),
                 (1, -25), (2, -11), (6, 0), (-4, -11.5), (-7, 0))
    swing = _pose(H, (-2, -21), (4, -36), (6.5, -40.5), (4, -34.5), (9, -31), (13, -29.5), (3, -35), (1, -30),
                  (3, -27), (2, -11), (6, 0), (-4, -11.5), (-7, 0))
    throw = _pose(H, (-1, -21), (6, -35), (8.5, -39.5), (6, -33.5), (11, -31), (16, -32), (5, -34), (4, -29),
                  (6, -28), (3, -11), (6, 0), (-4, -11.5), (-7, 0))
    return [ready, thrust, thrust, lift, swing, throw, ready], [2, 1, 2, 2, 1, 2, 2]


def make_shoveller(name, sp, origin, lights, exposure, face=1, H=44, seed=0, load_frames=(3, 4, 5, 6, 7, 8),
                   spray=True, fw=48, fh=58):
    keys, counts = shoveller_poses(H)
    poses = cycle(keys, counts)
    rig = Rig(dict(sp, H=H))
    st = Strip(name, fw, fh, origin, lights, exposure)
    ox, oy = fw // 2 - 8 * face, fh - 2
    n = len(poses)
    for i, p in enumerate(poses):
        def front(lay, P, f, i=i):
            shovel(lay, P, f, load=i in load_frames, seed=seed + i)
            if spray and i in (9, 10, 11):
                hx, hy = P['ha_n']
                coal_spray(lay, hx + f * 8, hy - 2, (i - 8) / 3.0, seed + 31, spread=8.0 * f)
        lay = rig.frame(fw, fh, ox, oy, p, face, {'front': front})
        st.add(lay)
    return st


def make_idle(name, sp, origin, lights, exposure, poses, face=1, fw=36, fh=56, extras=None, ox=None):
    rig = Rig(sp)
    st = Strip(name, fw, fh, origin, lights, exposure)
    ox = fw // 2 if ox is None else ox
    oy = fh - 2
    for i, p in enumerate(poses):
        ex = extras(i) if extras else None
        st.add(rig.frame(fw, fh, ox, oy, p, face, ex))
    return st


def breathe(pose, k, amp=0.5):
    """Small breathing / weight shift of a pose at phase k (0..1)."""
    d = math.sin(k * 2 * math.pi) * amp
    out = dict(pose)
    for j in ('neck', 'head', 'sh_n', 'sh_f', 'el_n', 'el_f', 'ha_n', 'ha_f'):
        if j in out:
            x, y = out[j]
            out[j] = (x, y + d * (1.0 if j in ('neck', 'head', 'sh_n', 'sh_f') else 0.6))
    return out
