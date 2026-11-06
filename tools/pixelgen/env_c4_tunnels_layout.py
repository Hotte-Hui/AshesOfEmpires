"""env_c4_tunnels_layout -- the binding geometry of L_C4_Tunnels (documentation/C4_DESIGN.md 4.1).

Side view like the registry: world 1920 x 360, the back wall meets the floor at y 288, feet line y 300, walk band
y 296-306 (x 18-1902); everything painted stands behind the walk band (base_y <= 294), the foreground frame stays
below y 318.  Rooms left -> right: Archivkeller (scene A, Alexei, ~4.40) | door wall (permanent blocker) |
Dienststollen 3 + Umsetzgleis (scene C, Alexei, ~7.30).  Story hotspot / spawn / NPC names and x positions are the
story stream's (C4_DESIGN 4.1) and must not change.
"""
from __future__ import annotations

WORLD_W, WORLD_H = 1920, 360
FLOOR = 288            # back wall meets floor
WALK_Y = 300
WALK_BAND = (296, 306)
WALK_X = (18, 1902)
HORIZON = 196          # eye level for floor perspective

# ---- rooms
CELLAR = (0, 700)
DOOR_WALL = (700, 720)
TUNNEL = (720, 1240)
SIDING = (1240, 1920)

# ---- cellar (A)
C_SPRING = 112                   # the brick barrel vault springs from the back wall here
C_RIBS = [0, 176, 352, 528, 700]  # transverse arches (centres)
STAIRS = (0, 66)                 # flight from the office door (top left) down to the floor
OFFICE_DOOR = (2, 26)            # door at the stair head (x0, x1), sill y 196
STAIR_TOP_Y = 196
WINDOWS_C = [(248, 280), (424, 456)]   # high barred windows in the lunettes (glass x0, x1), y below
WIN_Y = (82, 106)
SHELVES = (86, 300)              # three bays of freight books
SHELF_TOP = 132
SHELF_BOARDS = [152, 172, 192, 212, 232, 252, 272]
GAP = (176, 193)                 # the three-volume gap (January 1964, decades I-III) on board 232
GAP_BOARD = 232
HANG_LAMP = (196, 150)           # enamel shade over the shelves (bottom centre)
DESK = (342, 456)                # Lev's desk, top y 262
DESK_TOP = 262
GREEN_LAMP = (374, 238)          # shade bottom centre
BOOK = (354, 390)                # the January freight book, open
SIDE_TABLE = (460, 494)          # tea table right of Lev (exp_samovar 474)
SAMOVAR = (463, 479)
GLASSES = (481, 491)
CARD_INDEX = (316, 340)           # personnel card cabinet at the desk's left end (exp_card_index 334)
PLAN_ROLL = (434, 454)           # the 1941 tunnel plan, rolled linen, on the desk (until c4a_talk_tunnel)
CALENDAR = (338, 150)            # 1964 wall calendar (top-left), insignia site
CLOCK = (318, 166)               # wall clock centre (4.40)
PHOTO = (384, 250)               # Lev's photo, leaning against the lamp foot (exp_lev_photo 400)
STAMP_RACK = (300, 228)          # stamp rack right of the shelves (exp_stamps 292)
LIGHTBOX = (500, 542)            # light box made from an old signal lamp
STOVE = (562, 600)
STOVE_PIPE_X = 578
DOOR = (640, 700)                # iron door with the 1941 air-raid sign
DOOR_LEAF = (646, 690)
DOOR_Y = (232, 288)
SIGN_Y = 198

# ---- door wall
# ---- tunnel (C)
T_SHELL = 96                     # top of the concrete shell (section), earth above
T_SOFFIT = (108, 150)            # vault soffit band (section cut at the top -> far springing)
T_LAMPS = [(782, True), (902, True), (1022, False), (1142, True)]   # 1941 cage lamps (x, lit), y 166
T_LAMP_Y = 166
T_NICHE = (774, 810)             # niche with the old field telephone (exp_field_phone 792)
T_LEVER = (1036, 1100)           # lever frame, eight levers (mini-game spot, exp_lever_frame 1064)
T_POINT = (1000, 1030)           # hand-thrown point W2 (lever box + counterweight)
T_BRANCH = (1118, 1200)          # sealed side gallery the W2 branch runs into
T_FLANGE = 1188                  # leaking flange of the heating pipe (steam)
T_DRIPS = [846, 968, 1162]
BENCH_BOARDS = (1202, 1240)      # boards out of a wagon at the tunnel mouth (exp_child_drawing 1222)

# ---- siding (C)
S_SPRING = 116
S_RIBS = [1240, 1352, 1464, 1576, 1688, 1800, 1912]
BOOTH = (1288, 1392)             # the siding office, roof y 196
BOOTH_WIN = (1318, 1368)
BOOTH_COUNTER_Y = 258
CARD_BOX = (1330, 1361)
STAMP = (1364, 1376)
PAINTERS = (1390, 1426)          # crate table, tea glasses, newspaper, roster on the post (exp_painters_corner 1404)
PAINT_STAND = (1442, 1500)
BUCKET = (1478, 1496)
PLATE_HEAP = (1504, 1546)
WAGON = (1550, 1740)             # wagon 24 318 on track 1 (body incl. buffers)
WAGON_BODY = (1556, 1734)
WAGON_DOOR = (1652, 1702)        # sliding door opening (centre ~1677)
WAGON_ROOF = 186
WAGON_FLOOR = 258
NUMBER_FIELD = (1562, 1628)      # the paint layers on the left side panel
BULB = (1646, 150)               # the single bulb over the wagon (bottom)
KIT_PILE = (1244, 1286)          # conversion kit: stove-pipe elbows, small stove, buckets (exp_stovepipes 1262)
BRAZIER = (1816, 1836)           # the workers' brazier, embers
PORTAL = (1866, 1920)            # exit portal to the main line, gate shut
WORK_LAMPS = [(1432, 126), (1812, 126)]

ROOMS = {'cellar': list(CELLAR), 'door': list(DOOR_WALL), 'tunnel': list(TUNNEL), 'siding': list(SIDING)}

# ---- story contract (C4_DESIGN 4.1) -- names and x are binding
HOTSPOTS = {
    'book_shelf': (184, 300), 'desk_book': (372, 300), 'lev_cellar': (428, 300), 'lamp_table': (520, 300),
    'tunnel_door': (664, 300), 'office_desk': (1346, 300), 'paint_stand': (1468, 300), 'wagon_side': (1590, 300),
    'wagon_door': (1680, 300), 'lev_siding': (1772, 300),
}
SPAWNS = {'SP_C4_Stairs': (48, 300), 'SP_C4_Office': (1322, 300)}
NPCS = {
    'lev_cellar': {'char': 'lev', 'feet': [446, 300], 'facing': 'left', 'hide_after': 'c4c_inspect_card'},
    'lev_siding': {'char': 'lev', 'feet': [1790, 300], 'facing': 'left', 'show_after': 'c4a_open_door'},
}
BLOCKERS = [{'name': 'cellar_door', 'rect': [700, 270, 20, 60],
             'note': 'the iron tunnel door wall: always shut for walking; LS_C4_Number carries Alexei through'}]
# walk area per scene (C4_DESIGN 4 / tests/test_c4_routes.gd AREAS) and the camera window the level script uses
AREAS = {'L_C4_TunnelsA': (18, 700), 'L_C4_TunnelsB': (720, 1902)}
CAMERA = {'L_C4_TunnelsA': (0, 720), 'L_C4_TunnelsB': (700, 1920)}

# what each story hotspot stands at (the painted object and its x span)
HOTSPOT_PROPS = {
    'book_shelf': ('shelves of freight books; the three January volumes missing, Lev\'s slip on the empty board',
                   (GAP[0] - 8, GAP[1] + 8)),
    'desk_book': ('Lev\'s desk under the green-shaded lamp: the January book open at the column "Genehmigt"',
                  (BOOK[0] - 4, BOOK[1] + 4)),
    'lev_cellar': ('Lev Sokolov (x 446) at the end of his desk: samovar, two tea glasses, the card index',
                   (DESK[0], DESK[1] + 4)),
    'lamp_table': ('the light box made from an old signal lamp, carbon copies on the frosted glass', LIGHTBOX),
    'tunnel_door': ('the iron door, sign "Бомбоубежище - Служебный тоннель №3" (1941)', (DOOR[0] + 2, DOOR[1] - 4)),
    'office_desk': ('the siding office counter: card box "C-17/45 - принять", the stamp, the kerosene lamp',
                    (BOOTH_WIN[0] - 4, BOOTH_WIN[1] + 6)),
    'paint_stand': ('the paint stand: stencils in two alphabets, C-17/41 .. /45, the bucket of red-brown',
                    PAINT_STAND),
    'wagon_side': ('wagon 24 318, left side: the paint layers, the fresh stencil C-17/45 still taped on',
                   (WAGON_BODY[0], WAGON_DOOR[0])),
    'wagon_door': ('the sliding door of the wagon, half open: benches, the stove hole in the roof inside',
                   (WAGON_DOOR[0], WAGON_DOOR[1] + 4)),
    'lev_siding': ('Lev (x 1790) at the end of the wagon, keeping watch toward the exit portal',
                   (WAGON[1] - 4, WAGON[1] + 60)),
}
# The exploration stream owns the find positions (assets/environments/karsk_tunnels/explore_hotspots.json,
# "info" = its art contract); the painters above put each described object at its focus.
