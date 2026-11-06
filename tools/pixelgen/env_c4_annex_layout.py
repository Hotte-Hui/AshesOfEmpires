"""env_c4_annex_layout -- single source of truth for L_C4_Annex (Chapter 4 part 1, documentation/C4_DESIGN.md 4.2).

One level file, two Story scenes in two walk areas that never see each other (each scene starts with a level load):
    0..846     Wendeschleife Sued 8   (L_C4_AnnexA, Konrad, exterior, dawn, snow)
    846..1920  Nebenstelle Sued       (L_C4_AnnexB, Konrad, underground, fluorescent)
The permanent blocker `shaft_wall` (822..846) separates the walk areas; the level script
(scripts/levels/c4/annex_level.gd) clamps the camera to the area of the scene it plays (CAMERA_ZONES), so the
street never shows underground and the annex never shows the sky.  World 1920 x 360 logical px, side view like
the registry (feet line y 300, walk band 296-306, everything painted stands behind it, foreground below y 318).
Every story hotspot, spawn, NPC anchor and the blocker below is the contract of C4_DESIGN 4.2 and must not move.
"""

WORLD_W, WORLD_H = 1920, 360
VIEW_W, VIEW_H = 640, 360
FEET = 300
WALK_BAND = (296, 306)
WALK_X = (18, 1902)
SEAM = 846                         # camera seam between the two scenes (inside the blocker's right edge)
CAMERA_ZONES = {'L_C4_AnnexA': [0, 0, SEAM, WORLD_H], 'L_C4_AnnexB': [SEAM, 0, WORLD_W - SEAM, WORLD_H]}

# =========================================================================== B: Wendeschleife Sued 8 (exterior)
LOOP = (0, SEAM)
BASE_Y = 288                        # facades / track bed meet the pavement
HOUSE11 = (0, 86)                   # still lived in (Marta's window lit, a lamp)
STOREYS_11 = [(240, 288), (194, 240), (150, 194), (106, 150), (64, 106)]   # ground .. 4th floor (y0, y1)
CORNICE_11 = (54, 64)
MARTA_WIN = (52, 202, 16, 26)       # x, y, w, h (1st floor, right window)
HOUSE9 = (86, 208)                  # gutted: ground-floor front + the exposed back wall with three storeys of paper
DOOR9 = (100, 136)                  # boarded, sealed double door (door_9 = 118)
DOOR9_Y = (236, 288)
PAPER_STOREYS = [(198, 240, 'rose'), (152, 198, 'green'), (108, 152, 'blue')]
GAP = (208, 250)                    # rubble edge of the cleared lot, first wire pole
POLES = [228, 612]                  # overhead-wire poles (x centre)
WIRE_Y = 176                        # trolley contact wire
SPAN_Y = 140                        # span wire carrying the loop lamp
SHELTER = (250, 334)                # tram shelter (Wartehalle)
SHELTER_ROOF_Y = (212, 222)
CASE = (280, 304)                   # lit timetable case (timetable_case = 292)
CASE_Y = (230, 262)
STOP_SIGN = 244                     # the H sign on its post
LAMP_LOOP = (344, 152)              # sodium lamp under the span wire (x, bottom of the bowl)
TRAM = (362, 604)                   # tram 74, motor car, standing in the loop
TRAM_Y = (218, 292)                 # roof .. rail head
TRAM_DOOR = (394, 418)              # front platform door (open), Marta beside it at 422
TRAM_WINDOWS = [(424, 444), (448, 468), (472, 492), (496, 516), (520, 540), (544, 562)]
ILSE_WIN = (544, 562)               # the last bench: Ilse (life strip), breath on the glass
COLUMN = (630, 662)                 # advertising column S 2 (column_s2 = 646)
COLUMN_Y = (194, 286)
HATCH = (698, 792)                  # freight hatch of the shaft, hoist frame above
CRATES = (712, 752)                 # stack C-17/45
SPLIT_CRATE = (752, 778)            # the split crate, cards in the snow (loading_hatch = 762)
CARD_0417 = (760, 297)              # the card in the snow (centre)
LORRY = (716, 790)                  # the lorry backed up to the hatch, seen from behind (tail lights)
FENCE = (796, SEAM)                 # site hoarding of the axis: the end of the street
NEAR_RAIL_Y = (326, 335)            # near side of the loop (foreground street)
FAR_RAIL_Y = (289, 294)             # far side: the tram's track

# =========================================================================== D: Nebenstelle Sued (underground)
ANNEX = (SEAM, WORLD_W)
FLOOR = 288                         # back wall meets the floor
CEIL_Y = 26                         # underside of the slab
BEAMS = [960, 1100, 1240, 1380, 1520, 1660, 1800]   # downstand beams (x centre)
DUCT_Y = (30, 52)                   # main air duct from the machine room
TUBES_Y = (56, 62)                  # the two pneumatic tubes under the ceiling
TRAY_Y = (64, 67)                   # cable tray
FIXTURE_Y = 76                      # fluorescent fixtures hang here
FIXTURES = [1000, 1120, 1240, 1360, 1480, 1600, 1720, 1840]
DADO_Y = 226                        # oil-paint dado (Behoerdengruen) top
PIER = (SEAM, 872)                  # cut concrete wall of the shaft (near-black framing pier)
SHAFT = (872, 918)                  # ladder niche; the shaft goes up through the slab
LADDER = (884, 904)                 # SP_C4_Ladder = 902 stands at its foot
MACHINE = (930, 1060)               # machine room behind a mesh grille: two fans
FANS = [(964, 150, 30), (1028, 150, 30)]   # (cx, cy, r) of the two axial fans
CARD_HALL = (1060, 1500)
CABINETS = [(1066, 1324), (1440, 1500)]    # steel card cabinets to the ceiling (x0, x1)
BANK = (1127, 1295)                 # drawer bank "Sued 1 .. Sued 12" at hand height (12 x 14 px)
BANK_Y = (238, 284)
DRAWER_W = 14
DRAWER_S8 = (1225, 1239)            # drawer Sued 8 (drawer_s8 = 1232)
DRAWER_S3 = (1155, 1169)            # drawer Sued 3: a finger's width open, Brandt's card standing up (exp_brandt_card)
LADDERS = [1090, 1300]              # sliding ladders on the cabinet rail (x)
PLAN = (1340, 1412)                 # framed ventilation plan (plan_wall = 1376)
PLAN_Y = (168, 222)
CLOCK = (1376, 128)                 # wall clock above the plan (6.00)
TUBE_ST = (1526, 1570)              # pneumatic-tube station (tube_station = 1548)
TUBE_ST_Y = (150, 280)
BENCH = (1584, 1636)                # waiting bench for the public
COUNTER = (1650, 1772)              # counter "Auskunft . Abgleich" (registrar_counter = 1716, Fengler at 1734)
COUNTER_Y = (250, 288)
GLASS = (1648, 1832)                # glazed partition: the typists' room behind it
GLASS_Y = (150, 250)
TYPISTS = [(1676, 'a'), (1790, 'b')]
STAPO_DOOR = (1850, 1886)           # steel door to the Staatspolizei corridor (guard_annex = 1868)
STAPO_DOOR_Y = (232, 288)

ZONES = {'loop': [0, 820], 'shaft': [820, 880], 'machine_room': [880, 1060], 'card_hall': [1060, 1500],
         'tube': [1500, 1620], 'counter': [1620, 1800], 'corridor': [1800, 1920]}

# =========================================================================== story contract (C4_DESIGN 4.2)
HOTSPOTS = {
    'door_9': (118, 300), 'timetable_case': (292, 300), 'marta_tram': (404, 300), 'column_s2': (646, 300),
    'loading_hatch': (762, 300), 'drawer_s8': (1232, 300), 'plan_wall': (1376, 300), 'tube_station': (1548, 300),
    'registrar_counter': (1716, 300), 'guard_annex': (1868, 300),
}
SPAWNS = {'SP_C4_Shelter': (236, 300), 'SP_C4_Ladder': (902, 300)}
NPCS = {
    'marta_tram': {'char': 'marta', 'feet': [422, 300], 'facing': 'left'},
    'registrar_counter': {'char': 'registrar', 'feet': [1734, 276], 'facing': 'left'},   # behind the counter prop
    'guard_annex': {'char': 'guard', 'feet': [1868, 300], 'facing': 'left'},
}
BLOCKER = {'name': 'shaft_wall', 'rect': [822, 270, 24, 60],
           'note': 'street and annex are two walk areas; LS_C4_Card carries Konrad down the shaft'}
# which painted object each story hotspot belongs to (x range) -- checked by tests/test_c4_annex_art.gd
HOTSPOT_PROPS = {
    'door_9': ('house No. 9: boarded double door, red seal strip, the notice', DOOR9),
    'timetable_case': ("the shelter's lit timetable case (Konrad's light table)", CASE),
    'marta_tram': ('front platform door of tram 74 (Marta beside it, Ilse at the last window)', (TRAM[0], 430)),
    'column_s2': ('advertising column S 2 with the warm-air grate at its foot', COLUMN),
    'loading_hatch': ('freight hatch: crates C-17/45, the split crate, a card in the snow', (CRATES[0], SPLIT_CRATE[1])),
    'drawer_s8': ('drawer bank Sued 1-12: drawer Sued 8 (red tab / pulled out)', DRAWER_S8),
    'plan_wall': ('framed ventilation plan, Blatt 3, gez. K. Adler', PLAN),
    'tube_station': ('pneumatic-tube station, capsule in the tray', TUBE_ST),
    'registrar_counter': ('counter "Auskunft . Abgleich" with stamps, forms, perforator', COUNTER),
    'guard_annex': ('steel door to the Staatspolizei corridor', STAPO_DOOR),
}
SCENE_A, SCENE_B = 'L_C4_AnnexA', 'L_C4_AnnexB'
