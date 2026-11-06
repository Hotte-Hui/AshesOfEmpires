"""env_c4p2_berlin_layout -- every coordinate of L_C4P2_Berlin (C4P2_DESIGN.md §4.2) in one place.

World 1920 x 360, side view, feet line y 300, walk band y 296..306 (x 18..1902).  Two places in ONE level file:
    x    0 .. 898   Ostbahnhof, Korridorbahnsteig K       (Story scene L_C4P2_BerlinA, Monday 20.30)
    x  898 .. 938   the end of platform K = the permanent blocker `platform_end`
    x  938 .. 1920  Kolonnenstrasse 14, gate passage + courtyard (Story scene L_C4P2_BerlinB, Tuesday 22.10)
Camera zones A [0, 0, 918, 360] / B [918, 0, 1002, 360]: the station layers cover x 0..918, the courtyard layers
x 918..1920 (the seam is never on screen in either scene).

Story names and positions are the story stream's placeholder (kept); the exploration stream's art contract
(assets/environments/berlin_c4p2/explore_hotspots.json "info") placed its finds -- the art below puts each thing
where that contract says.
"""
from __future__ import annotations

WORLD_W, WORLD_H = 1920, 360
FEET = 300
WALK_BAND = (296, 306)
WALK_X = (18, 1902)
SEAM_A = 918                    # station layers 0..918
SEAM_B = 918                    # courtyard layers 918..1920
SCENE_A, SCENE_B = 'L_C4P2_BerlinA', 'L_C4P2_BerlinB'
CAMERA_ZONES = {SCENE_A: [0, 0, 918, 360], SCENE_B: [918, 0, 1002, 360]}
BLOCKER = {'name': 'platform_end', 'rect': [898, 270, 40, 60],
           'note': 'Ostbahnhof platform K (Monday, scene A) and the courtyard of Kolonnenstraße 14 (Tuesday, '
                   'scene B) are two places in one file; LS_C4P2_Express carries Konrad there. Painted: the '
                   'Corridor fence at the end of platform K (A) / the street door of the gate passage (B).'}
SPAWNS = {'SP_C4P2_Platform': (60, FEET), 'SP_C4P2_Gate': (960, FEET)}
HOTSPOTS = {
    'departure_board': (110, FEET), 'marta_buffet': (300, FEET), 'shadow_kiosk': (410, FEET),
    'courier_car': (500, FEET), 'ekdahl_window': (680, FEET), 'dining_table': (800, FEET),
    'gate_notice': (1000, FEET), 'kuhnert_gate': (1060, FEET), 'wendt_yard': (1110, FEET),
    'hanna_yard': (1250, FEET), 'lodge_window': (1420, FEET), 'yard_pump': (1600, FEET),
}
NPCS = {
    'marta_buffet': {'char': 'marta', 'feet': [318, FEET], 'facing': 'left'},
    'shadow_kiosk': {'char': 'stapo_civil', 'feet': [410, FEET], 'facing': 'left'},
    'ekdahl_window': {'char': 'journalist', 'feet': [698, FEET], 'facing': 'left'},
    'kuhnert_gate': {'char': 'blockwart', 'feet': [1060, FEET], 'facing': 'left'},
    'wendt_yard': {'char': 'wendt', 'feet': [1128, FEET], 'facing': 'left', 'show_after': 'c4h_solve_house'},
    'hanna_yard': {'char': 'hanna', 'feet': [1268, FEET], 'facing': 'left', 'hide_after': 'c4h_solve_house'},
}
ZONES = {'platform_k': [0, 898], 'platform_end': [898, 938], 'gate_passage': [938, 1100], 'courtyard': [1100, 1920]}

# =========================================================================== A: the station (x 0..918)
A_W = SEAM_A
PLAT_EDGE_Y = 266            # far edge of platform K (coping)
PLAT_NEAR_Y = 318            # near edge (foreground from here)
RAIL_K = 262                 # rail top of track K (behind the platform edge: only the wheels' upper halves show)
CAR_TOP = 166                # roof line of the D 303's coaches
CAR_BOT = 252                # bottom of the car bodies (skirts)
VAULT_SPRING = 150           # where the far side of the glass vault meets the far wall (hall layer coordinates)
# the D 303, head to the left (the open end of the hall is left)
LOCO = (254, 392)            # buffer beam .. cab back (drivers at x 310 / 334 / 358, the cab from x 358)
TENDER = (394, 446)
COURIER = (448, 530)         # two-axle windowless courier van; its sliding door with the two seals at x 492..508
COURIER_DOOR = (490, 510)
GAP = (530, 622)             # the coaches are not coupled yet: through the gap the next track and the green car
DINER = (624, 816)           # the dining car; its open door (vestibule) at x 794..814
DINER_DOOR = (794, 814)
SLEEPER = (818, 990)         # the sleeping car runs on behind the Corridor fence
# platform furniture (feet / base on the platform, behind the walk band)
BOOTH = (5, 60)              # the liaison booth at the barrier (exp_liaison_booth 34)
BARRIER = (60, 70)
BOARD = (64, 156)            # the enamel departure board on its two posts (departure_board 110)
BAGGAGE = (146, 200)         # baggage counter window + the decimal scale (exp_luggage_scale 166 / focus 172)
SCALE = (150, 192)
BUFFET = (200, 338)          # the buffet stand, open at the back (marta_buffet 300, Marta 318; exp_corridor_permit 236)
COUNTER_TOP = 262
KIOSK = (380, 440)           # the newspaper kiosk (exp_kiosk 380, the man with the paper 410); between buffet and
                             # kiosk (x 338..380) the engine's drivers and rods show
CARTS = (596, 646)           # two porters' carts (exp_porters 616)
CLOCK = (740, 150)           # the station clock hanging from the vault (exp_station_clock 740 / focus (740, 150))
FENCE = (878, 918)           # the Corridor fence at the end of platform K (blocker platform_end 898..938); its
                             # sign „KEIN DURCHGANG“ wired to its face
TICKET_STUB = (850, 296)     # hidden find exp_ticket_stub: between two platform boards
LAMPS_A = (36, 186, 346, 506, 666, 826)   # sodium lamps hanging from the vault (x)
LAMP_Y = 128

# =========================================================================== B: the courtyard (x 918..1920)
B_X0 = SEAM_B
B_W = WORLD_W - SEAM_B       # 1002
# storey lines shared by the three wings (compressed like every façade of the game)
E_TOP = 230                  # ground floor 300..230 (the passage vault reaches y 214 in the front wing)
FLOORS = {'E': (230, 300), '1': (190, 230), '2': (150, 190), '3': (110, 150), 'D': (86, 110)}
EAVES = 86
RIDGE = 60
# the three wings, unrolled into one courtyard elevation (the puzzle's cutaway: V | S | H, left to right)
WING_V = (918, 1194)         # Vorderhaus (front wing), courtyard face
WING_S = (1194, 1690)        # Seitenfluegel (side wing)
WING_H = (1690, 1920)        # Hinterhaus (back wing)
PASSAGE = (945, 1100)        # the gate passage in the front wing's ground floor
PASSAGE_TOP = 214            # crown of its vault
STREET_DOOR = (918, 945)     # the open street door at the passage's far end
NOTICE = (972, 1028)         # the Blockleitung notice + the pinned site plan (gate_notice 1000)
STAIR_DOOR_V = (1036, 1052)  # the front wing's stair door inside the passage
PASSAGE_LAMP = (1022, 222)
V_AXES = (970, 1024, 1078, 1132)
V_KITCHEN = 1162             # Frau Grabowski's narrow kitchen window (2nd floor); the basket hangs below it
BASKET = (1162, 262)
S_AXES = (1236, 1287, 1340, 1392, 1444, 1496, 1548, 1600, 1652)
S_STAIR = 1287
S_DOOR = (1276, 1298)        # the side wing's stair door (exp_ilse_drawing focus 1286, 250)
COAL = (1306, 1346)          # briquettes delivered today (exp_task_coal 1330 / focus 1336)
HATCH = (1350, 1376)         # the open iron cellar hatch in the pavement (exp_cellar_hatch 1356 / focus 1362)
LODGE = (1402, 1440)         # the lodge window with the card box on the sill (lodge_window 1420)
WASH_DOOR = (1467, 1493)     # the wash-house door
BINS = (1528, 1580)          # four dustbins (exp_dustbins 1550 / focus 1554)
PUMP = (1592, 1610)          # the courtyard pump (yard_pump 1600)
RACK = (1624, 1674)          # the carpet-beating rack (exp_carpet_rack 1640 / focus 1648)
H_AXES = (1712, 1764, 1816, 1868)
H_DOOR = (1702, 1722)        # the back wing's hall door, four steps up
WORKSHOP = (1732, 1884)      # the cobbler's souterrain windows (exp_workshop_window 1760 / focus 1766)
LAUNDRY = (1172, 1246)       # frozen laundry on lines high across the corner (exp_frozen_laundry focus 1204, 128)
# the courtyard floor's two neighbours (life strips, until the house is solved; round-10 lead pass).  No one beats
# a carpet at 22.10: the rack's own enamel plate says 8-12 and 15-18 Uhr.
COAL_MAN = 1389             # up from the cellar with a full coal scuttle, between the open hatch and the lodge
WASH_WOMAN = 1506           # out of the wash-house with the last basket for the attic (Tuesday is washing day)

# households of the house puzzle (C4P2_DESIGN §2.7): wing, floor -> (lit?, window axes, what)
HOUSEHOLDS = {
    'v1': ('V', '1', 'lit', (1024, 1078), 'Schulz: a mother walks the baby'),
    'v2': ('V', '2', 'dark', (V_KITCHEN,), 'Grabowski: the dark kitchen, a basket on a washing line'),
    'v3': ('V', '3', 'lit', (1078, 1132), 'Lenz: desk lamp, the radio dial'),
    'vd': ('V', 'D', 'dark', (), 'Dachboden Vorderhaus: junk'),
    's1': ('S', '1', 'lit', (1444, 1496, 1548), 'Mertens: the tram conductor\'s family at the table'),
    's2': ('S', '2', 'dim', (1340,), 'Pohl: the curtain moves'),
    's3': ('S', '3', 'lit', (1340, 1392), 'Hanna Adler: Ilse draws at the kitchen table'),
    'se': ('S', 'E', 'lit', (1420,), 'Loge Kuhnert: Frau Kuhnert, the radio, the card box on the sill'),
    'sd': ('S', 'D', 'dark', (1444,), 'Trockenboden Seitenflügel: washing day, a hatch ajar'),
    'h1': ('H', '1', 'lit', (1764, 1816), 'Kühn: the card game'),
    'h2': ('H', '2', 'dark', (1764, 1816), 'Brettschneider: night shift at the gasworks'),
    'h3': ('H', '3', 'sealed', (1764, 1816, 1868), 'empty, sealed with paper strips (umgesetzt 10/63)'),
    'hd': ('H', 'D', 'dark', (1816,), 'Trockenboden Hinterhaus: the hatch open (Tuesdays)'),
    'ws': ('H', 'K', 'dim', (1764, 1796, 1828, 1860), 'Schuhmacherei Pietsch: the souterrain'),
}
