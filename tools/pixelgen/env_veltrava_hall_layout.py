"""env_veltrava_hall_layout -- single source of truth for L_C3_Hall 'Palais der Kommission' coordinates.

World 1920 x 360 logical px, Mode A side-on interior (like the Berlin archive).  Feet line y = 300.
Rooms left -> right (C3_DESIGN.md 4.2):
    0..420     vestibule      revolving door, snow outside, cloakroom, six flags
    420..1000  foyer          grand staircase, chandelier, buffet, photo wall, tall window, doors to the Saal
    1000..1400 corridor + Protokollbuero   evacuation plan, treaty shelf, typists, carbon basket, big table
    1400..1920 interpreters' corridor     three glass booths, the Grosser Saal seen below through the glass
"""

WORLD_W, WORLD_H = 1920, 360
VIEW_W, VIEW_H = 640, 360
FLOOR = 288            # back wall meets floor
WALK_Y = 300           # feet line of walking characters
WALK_BAND = (296, 306)
WALK_X = (18, 1902)
CEIL = 12              # ceiling / wall junction (ceiling band above)
HORIZON = 196          # eye level used for floor and ceiling perspective
TILE = 36              # marble chequer tile (unprojected px) in the vestibule and foyer

# ---------------------------------------------------------------- rooms (x ranges)
VEST = (0, 410)
ARCH1 = (410, 434)     # arched opening vestibule | foyer (cut wall, poche)
FOYER = (434, 1000)
PART2 = (1000, 1014)   # wall foyer | corridor (doorway)
OFFICE = (1014, 1390)  # corridor + Protokollbuero
PART3 = (1390, 1404)   # wall office | interpreters' corridor (door)
INTERP = (1404, 1920)

# ---------------------------------------------------------------- vestibule
ENTRANCE = (12, 112)                 # glazed entrance screen (x0, x1)
REVOLVING = (36, 88)                 # revolving-door drum
DRUM_TOP = 230                       # canopy underside of the drum
SIDELIGHTS = [(16, 32), (92, 108)]   # glass x ranges beside the drum
SIDE_Y = (150, 284)
FANLIGHT = (16, 108, 104, 146)       # x0, x1, y0, y1 (transom with leaded bars)
ARCHWIN = (22, 102, 38, 98)          # big arched window above (x0, x1, y_top_of_arch, y_bottom)
FLAG_X = [124 + 16 * i for i in range(6)]
FLAG_ORDER = ['commission', 'ussr', 'reich', 'sweden', 'switzerland', 'finland']
FLAG_BASE = 291
CLOAK = (214, 300)                   # cloakroom counter
CLOAK_RAIL_Y = 214                   # hook rail
VEST_LANTERN = (176, 64)             # hanging lantern (x, bottom y)

# ---------------------------------------------------------------- foyer
PHOTO_WALL = (444, 508)
STAIR_FOOT = 520                     # x where the flight starts (floor)
STAIR_TOP = (696, 176)               # x, y of the landing nosing
LANDING = (696, 752)
UPPER_DOOR = (708, 740)              # door on the landing (to the gallery of the Saal)
LUNETTES = [(486, 530), (566, 610), (778, 822)]
LUNETTE_Y = (30, 56)                 # crown .. springing line (semicircle-ish)
CHANDELIER = (648, 112)              # x, lowest point
BUFFET = (768, 832)
WINDOW = (848, 882)                  # tall window glass x range
WIN_Y = (70, 250)                    # glass y range (arched top)
SAAL_DOOR = (952, 994)               # double doors to the Grosser Saal
SAAL_DOOR_TOP = 198
EASEL_X = 930

# ---------------------------------------------------------------- corridor + office
EVAC = (1018, 1054, 204, 234)        # evacuation plan x0, x1, y0, y1
TREATY = (1060, 1100)                # treaty bookcase
OFFICE_DOOR = (1102, 1108)           # glazed partition post (office begins)
OFFICE_WIN = (1176, 1204, 90, 196)   # office window (glass x0, x1, y0, y1)
TYPIST_DESK = (1110, 1166)
BASKET = (1168, 1198)
TABLE = (1214, 1326)
MIMEO = (1330, 1366)

# ---------------------------------------------------------------- interpreters' corridor
HEADSETS = (1494, 1546)              # headset cabinet
BOOTHS = [(1556, 1616), (1622, 1682), (1688, 1748)]
BOOTH_LANG = ['FR', 'RU DE', 'EN']   # (the plate shows RU <-> DE with an arrow glyph)
BOOTH_TOP = 196                      # top of the booth casing (cabin ~2.4 m)
BOOTH_GLASS = (214, 274)             # corridor-side glazing y range (booth interior visible)
BOOTH_WIN = (220, 258)               # far window (to the Saal) y range inside the booth
BOOTH_DESK_Y = 262                   # booth desk top (~1 m)
STAFF_DOOR = (1846, 1882)
FIRE_CAB = (1806, 1830)

# ---------------------------------------------------------------- gameplay points
SPAWNS = {'SP_C3_Vestibule': (70, WALK_Y)}
HOTSPOTS = {
    # story
    'kessler': (300, WALK_Y),
    'seating': (930, WALK_Y),
    'booth_log': (1180, WALK_Y),
    'protocol_table': (1270, WALK_Y),
    'booth_2': (1650, WALK_Y),
    'alexei_meet': (1700, WALK_Y),
    # NPC anchors
    'elena_arrival': (345, WALK_Y),
    'voronova_bg': (700, WALK_Y),
    'typist': (1120, WALK_Y),
    'journalist': (560, WALK_Y),
    # exploration
    'exp_flags': (154, WALK_Y),
    'exp_cloakroom': (240, WALK_Y),
    'exp_photos': (474, WALK_Y),
    'exp_chandelier': (640, WALK_Y),
    'exp_buffet': (792, WALK_Y),
    'exp_window': (866, WALK_Y),
    'exp_evac_plan': (1036, WALK_Y),
    'exp_treaty_shelf': (1080, WALK_Y),
    'exp_mimeograph': (1342, WALK_Y),
    'exp_headsets': (1520, WALK_Y),
}
# what the prompt / camera should point at (extension data) and where the player should stand
FOCUS = {
    'kessler': (316, 256), 'seating': (930, 236), 'booth_log': (1182, 254), 'protocol_table': (1270, 254),
    'booth_2': (1652, 246), 'alexei_meet': (1718, 256), 'elena_arrival': (353, 256), 'voronova_bg': (700, 256),
    'typist': (1134, 256), 'journalist': (574, 256), 'exp_flags': (156, 236), 'exp_cloakroom': (262, 236),
    'exp_photos': (476, 214), 'exp_chandelier': (648, 80), 'exp_buffet': (800, 262), 'exp_window': (865, 150),
    'exp_evac_plan': (1036, 218), 'exp_treaty_shelf': (1080, 200), 'exp_mimeograph': (1348, 262),
    'exp_headsets': (1520, 226),
}
APPROACH_FACING = {
    'kessler': 'right', 'seating': 'back', 'booth_log': 'back', 'protocol_table': 'back', 'booth_2': 'back',
    'alexei_meet': 'right', 'elena_arrival': 'right', 'voronova_bg': 'right', 'typist': 'right',
    'journalist': 'right', 'exp_flags': 'back', 'exp_cloakroom': 'back', 'exp_photos': 'back',
    'exp_chandelier': 'back', 'exp_buffet': 'back', 'exp_window': 'back', 'exp_evac_plan': 'back',
    'exp_treaty_shelf': 'back', 'exp_mimeograph': 'back', 'exp_headsets': 'back',
}
# NPC feet positions = hotspot + hotspot_offset from scenes/levels/L_C3_Hall.tscn (for previews / framing)
NPC_FEET = {'kessler': (316, WALK_Y), 'elena': (353, WALK_Y), 'voronova': (700, WALK_Y),
            'typist': (1134, WALK_Y), 'journalist': (574, WALK_Y), 'alexei': (1718, WALK_Y)}

# ---------------------------------------------------------------- parallax
PARALLAX = {'ext_sky': 0.04, 'ext_square': 0.30, 'ext_town': 0.12, 'ext_river': 0.20,
            'saal_far': 0.46, 'saal_near': 0.66, 'fg_frame': 1.25}


def layer_width(p: float, margin: int = 16) -> int:
    """Required width of a full-coverage parallax layer (TECHNICAL_ARCHITECTURE 3.1) + margin, /16."""
    w = VIEW_W + p * (WORLD_W - VIEW_W) + margin
    return int(-(-w // 16) * 16)


def local_range(p: float, wx0: float, wx1: float, cam0: float = 0.0, cam1: float = WORLD_W - VIEW_W):
    """Layer-local x range seen behind world x in [wx0, wx1] for cameras in [cam0, cam1]
    (layer pos.x = 0):  local = world - cam * (1 - p)."""
    lo = wx0 - cam1 * (1 - p)
    hi = wx1 - cam0 * (1 - p)
    return lo, hi


def visible_cams(wx0: float, wx1: float):
    """Camera x range for which world x in [wx0, wx1] is (at least partly) on screen."""
    return max(0.0, wx0 - VIEW_W), min(float(WORLD_W - VIEW_W), wx1)
