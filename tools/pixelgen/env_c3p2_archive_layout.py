"""env_c3p2_archive_layout -- single source of truth for L_C3_Registry (Chapter 3 part 2) coordinates.

The commission's registry in the souterrain of the palais' east wing: the former Kurhaus coal and boiler cellar
(1909), converted 1963.  World 1920 x 360 logical px, side view like the palais (feet line y 300, walk band
296-306).  Every story hotspot, spawn and blocker below is the contract of documentation/C3P2_DESIGN.md
section 5.1 / section 4 and must never move.
Rooms left -> right:
    0..372      Wirtschaftshof (exterior, snow): gate, facade, bracket lamp, handcart with crates, hatch, ramp
    372..404    corner pier with the iron-clad ramp door
    404..680    Annahme: chute door 1909, oak intake desk, fire case, porter's booth (glazed)
    680..1260   Karteisaal: bucket stand, rows of card cabinets, sorting table + green lamp, drawer C-17
    1260..1560  Planarchiv: plan chests, the wall of framed Annex C sheets (Blatt 7)
    1560..1920  Magazin: compact shelving, the C-17 shelf (fire starts here), barred service-stair door
"""

WORLD_W, WORLD_H = 1920, 360
VIEW_W, VIEW_H = 640, 360
FLOOR = 288            # back wall meets floor
WALK_Y = 300
WALK_BAND = (296, 306)
WALK_X = (18, 1902)
HORIZON = 196          # eye level for floor perspective
VAULT_SPRING = 34      # interior: brick cap vaults spring from the steel beams here
WIN_Y = (44, 82)       # high souterrain windows (light wells at yard level)
DADO_Y = 250           # oil-paint dado top
PLINTH_Y = 282

# ---------------------------------------------------------------- yard (exterior)
YARD = (0, 372)
GATE = (8, 56)                  # wrought-iron double gate (x0, x1), posts outside
GATE_Y = (214, 288)
GATE_POSTS = [(0, 9), (55, 66)]
FACADE = (66, 372)
CORNICE_Y = (24, 40)
LAMP_YARD = (184, 170)          # bracket lamp head (x, y)
CART = (194, 276)               # handcart with the emptied crates (prop)
HATCH = (312, 350)              # cast-iron coal-chute hatch in the ground ("1909")
RAMP = (346, 376)               # concrete ramp up to the door sill
PIER = (372, 404)               # corner pier (cut exterior wall)
DOOR = (377, 401)               # ramp door opening
DOOR_Y = (228, 284)             # lintel .. sill
LEAF_OPEN = (348, 372)          # the leaf stands open against the facade (night)

# ---------------------------------------------------------------- Annahme
ANNAHME = (404, 680)
CHUTE = (436, 468)
CHUTE_Y = (252, 288)
DESK = (456, 530)               # oak standing desk ("Pult"); in D it is pushed by DESK_PUSH px
DESK_PUSH = 18
FIRE_CASE = (548, 576)
CASE_Y = (216, 262)
BELL = (604, 150)               # fire bell (centre x, top y)
BOOTH = (588, 680)
CLOCK = (520, 182)              # wall clock centre

# ---------------------------------------------------------------- Karteisaal
PART1 = (680, 700)
KARTEI = (700, 1260)
BUCKETS = (700, 722)
ROWS = [(734, 764), (794, 824), (854, 886)]     # ends of the cabinet rows (aisles between them)
TABLE = (934, 1066)
LAMP_GREEN = (1000, 230)        # shade bottom centre
BANK = (1074, 1240)             # card-cabinet bank against the back wall
DRAWER = (1092, 1118)           # drawer C-17 (half open)
LADDER = (816, 836)             # the rolling ladder on the row-end rail

# ---------------------------------------------------------------- Planarchiv
PART2 = (1260, 1276)
PLAN = (1276, 1560)
BLATT7 = (1328, 1352)
FALLEN_FRAME = (1388, 1430)     # the frame that falls and burns (fire states)

# ---------------------------------------------------------------- Magazin
PART3 = (1560, 1576)
MAGAZIN = (1576, 1920)
C17_SHELF = (1684, 1722)
PLAQUE = (1584, 1616)           # enamel plate of the Kurhaus boiler house (1909)
CASSATION = (1728, 1744)        # the cassation list on the wall
SERVICE_DOOR = (1866, 1904)

ROOMS = {'yard': (0, 380), 'annahme': (380, 680), 'karteisaal': (680, 1260), 'planarchiv': (1260, 1560),
         'magazin': (1560, 1920)}

# ---------------------------------------------------------------- story contract (C3P2_DESIGN 5.1 / 4)
HOTSPOTS = {
    'crates': (232, 300), 'ramp_door': (398, 300), 'alexei_chute': (440, 300), 'chute_door': (476, 300),
    'intake_desk': (505, 300), 'fire_case': (560, 300), 'porter_booth': (612, 300), 'konrad_booth': (640, 300),
    'konrad_cards': (880, 300), 'alexei_table': (950, 300), 'sorting_table': (1012, 300),
    'drawer_c17': (1104, 300), 'plan_wall': (1340, 300),
}
SPAWNS = {
    'SP_C3_Gate': (44, 300), 'SP_C3_KonradCards': (898, 300), 'SP_C3_AlexeiTable': (968, 300),
    'SP_C3_KonradBooth': (658, 300), 'SP_C3_AlexeiChute': (458, 300),
}
BLOCKERS = [
    {'name': 'ramp_bolted', 'rect': [384, 280, 12, 40], 'after': 'c3d_choose'},
    {'name': 'fire_c', 'rect': [1236, 270, 24, 60], 'after': 'c3d_choose'},
    {'name': 'fire_d', 'rect': [690, 270, 24, 60], 'after': 'c3e_reach_konrad'},
]
# which painted object each story hotspot belongs to (x range) -- checked by tests/test_c3p2_archive_art.gd
HOTSPOT_PROPS = {
    'crates': ('handcart with the emptied crates of courier wagon 4', CART),
    'ramp_door': ('iron-clad ramp door', (DOOR[0] - 4, PIER[1])),
    'alexei_chute': ('iron chute door "1909" (Alexei holds it)', CHUTE),
    'chute_door': ('iron chute door "1909" (stand point beside the desk)', (CHUTE[0], DESK[0] + 24)),
    'intake_desk': ('oak intake desk with the intake book', (DESK[0], DESK[1] + DESK_PUSH)),
    'fire_case': ('red fire case with hose and axe', FIRE_CASE),
    'porter_booth': ("porter's booth: night book on the counter", BOOTH),
    'konrad_booth': ("porter's booth: the framed 1909 Kurhaus plan", BOOTH),
    'konrad_cards': ('end of the third cabinet row (Konrad with his torch)', (ROWS[2][0], ROWS[2][1] + 14)),
    'alexei_table': ('sorting table (left end)', TABLE),
    'sorting_table': ('sorting table under the green lamp', TABLE),
    'drawer_c17': ('half-open drawer C-17, chair with the scarf', (DRAWER[0] - 4, DRAWER[1] + 4)),
    'plan_wall': ('Blatt 7 of Annex C on the plan wall', (BLATT7[0] - 4, BLATT7[1] + 4)),
}
