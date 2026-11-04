"""env_berlin_layout -- single source of truth for M1 'Berliner Bauarchiv' world coordinates.

World 1600 x 360 logical px, Mode A side-on interior.  Feet line y = 300.
Rooms left -> right: drafting office | archive hall | light-table room | Emil's issue counter.
"""

WORLD_W, WORLD_H = 1600, 360
VIEW_W, VIEW_H = 640, 360
FLOOR = 288            # back wall meets floor
WALK_Y = 300           # feet line of walking characters
WALK_BAND = (296, 306)
CEIL = 20              # ceiling/wall junction
HORIZON = 200          # eye level used for floor perspective

# ---------------------------------------------------------------- rooms (x ranges)
OFFICE = (0, 568)
PART1 = (568, 596)     # partition office | archive (poche + arch)
ARCHIVE = (596, 1092)
PART2 = (1092, 1112)   # partition archive | light room
LIGHTROOM = (1112, 1280)
EMIL = (1280, 1600)

# ---------------------------------------------------------------- office
DOOR0 = (22, 70)                      # corridor double door (x0, x1)
DOOR0_TOP = 178
WINDOWS = [(120, 164), (240, 284), (360, 404)]   # glass x ranges
WIN_Y = (84, 236)                     # glass y range
PILASTERS = [(75, 89), (195, 209), (315, 329), (435, 449)]
POSTER = (458, 160, 36, 54)           # x, y, w, h  (reconstruction poster, Reichssiegel)
CLOCK = (536, 166)                    # centre
CABINETS = (506, 562)                 # filing cabinets x range (baked)

# ---------------------------------------------------------------- archive
GALLERY_Y = (138, 148)                # gallery slab
RAIL_Y = 116                          # top rail of the gallery balustrade
PIERS = [600, 716, 832, 948, 1064]    # left x of 12 px piers
PIER_W = 12
LADDER_X = 668

# ---------------------------------------------------------------- light room
DIAZO = (1222, 1274)

# ---------------------------------------------------------------- Emil
NOTICE = (1300, 196, 36, 42)          # notice board x, y, w, h  (obs_notice)
PIGEON = (1350, 150, 128, 112)        # pigeonhole wall x, y, w, h
EXIT_DOOR = (1528, 1576)
EMIL_POS = (1412, 284)                # Emil's feet (behind the counter, sorted behind it)

# ---------------------------------------------------------------- gameplay points
SPAWNS = {'SP_M1_Office': (140, WALK_Y)}
HOTSPOTS = {
    'plan_a': (322, WALK_Y),          # Konrad's drafting board
    'plan_b': (842, WALK_Y),          # flat-file drawer pulled out
    'overlay_table': (1178, WALK_Y),  # light table
    'emil': EMIL_POS,                 # Emil behind the counter
    'obs_window': (262, WALK_Y),      # Great Hall glimpse through the middle window
    'obs_photo': (204, WALK_Y),       # office photo on the covered drafting table
    'obs_notice': (1318, WALK_Y),     # typed list of 'relocated' tenants
}
# where the player should stand / what the prompt should point at (extension data)
FOCUS = {
    'plan_a': (322, 246), 'plan_b': (842, 262), 'overlay_table': (1178, 262), 'emil': (1412, 250),
    'obs_window': (262, 150), 'obs_photo': (206, 250), 'obs_notice': (1318, 214),
}
APPROACH = {
    'plan_a': ((310, WALK_Y), 'right'), 'plan_b': ((826, WALK_Y), 'right'),
    'overlay_table': ((1160, WALK_Y), 'right'), 'emil': ((1376, WALK_Y), 'right'),
    'obs_window': ((262, WALK_Y), 'back'), 'obs_photo': ((190, WALK_Y), 'right'),
    'obs_notice': ((1318, WALK_Y), 'back'),
}

# ---------------------------------------------------------------- parallax
PARALLAX = {'ext_sky': 0.05, 'ext_far': 0.10, 'ext_near': 0.18, 'fg_frame': 1.25}


def layer_width(p: float, margin: int = 16) -> int:
    """Required width for a parallax layer (TECHNICAL_ARCHITECTURE §3.1) + margin, rounded to 16."""
    w = VIEW_W + p * (WORLD_W - VIEW_W) + margin
    return int(-(-w // 16) * 16)
